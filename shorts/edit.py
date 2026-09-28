"""구간 하나를 9:16 쇼츠로 렌더링한다.

무음 제거 → 배속 → 세로 화면 → 제목·자막(말하는 단어 강조) → BGM 순서로 ffmpeg 필터 한 번에 처리.
"""
import re
from pathlib import Path

from . import ff
from .transcribe import all_words

PUNCT_END = re.compile(r"[.?!…。？！]$")


# ---------- 무음 제거 구간 계산 ----------

def speech_ranges(words: list[dict], clip: dict, e: dict) -> list[tuple[float, float]]:
    """남길 원본 구간 목록. 단어 사이 공백이 max_gap보다 길면 끊는다."""
    if not e["remove_silence"]:
        return [(clip["start"], clip["end"])]
    ranges: list[list[float]] = []
    for w in words:
        if ranges and w["start"] - ranges[-1][1] <= e["max_gap"]:
            ranges[-1][1] = max(ranges[-1][1], w["end"])
        else:
            ranges.append([w["start"], w["end"]])
    pad = e["pad"]
    merged: list[list[float]] = []
    for a, b in ranges:
        a, b = max(0.0, a - pad), b + pad
        if merged and a <= merged[-1][1]:
            merged[-1][1] = b
        else:
            merged.append([a, b])
    return [(a, b) for a, b in merged]


class Timeline:
    """원본 시각 → 완성본 시각 변환."""

    def __init__(self, ranges: list[tuple[float, float]], speed: float):
        self.ranges, self.speed = ranges, speed
        self.offsets, acc = [], 0.0
        for a, b in ranges:
            self.offsets.append(acc)
            acc += b - a
        self.duration = acc / speed

    def map(self, t: float) -> float:
        for (a, b), off in zip(self.ranges, self.offsets):
            if t <= b:
                return (off + max(0.0, t - a)) / self.speed
        return self.duration


# ---------- ASS 자막 ----------

def ass_color(hex_rgb: str, alpha: float = 0.0) -> str:
    r, g, b = hex_rgb.lstrip("#")[0:2], hex_rgb.lstrip("#")[2:4], hex_rgb.lstrip("#")[4:6]
    return f"&H{int(alpha * 255):02X}{b}{g}{r}".upper()


def ass_time(t: float) -> str:
    cs = max(0, int(round(t * 100)))
    return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"


def ass_escape(s: str) -> str:
    return s.replace("\\", "＼").replace("{", "(").replace("}", ")").replace("\n", " ")


def wrap_title(title: str, limit: int = 12) -> str:
    title = ass_escape(title.strip())
    if len(title) <= limit or " " not in title:
        return title
    mid = len(title) // 2
    spaces = [i for i, ch in enumerate(title) if ch == " "]
    cut = min(spaces, key=lambda i: abs(i - mid))
    return title[:cut] + "\\N" + title[cut + 1:]


def chunk_words(words: list[dict], max_chars: int) -> list[list[dict]]:
    chunks, cur, n = [], [], 0
    for w in words:
        size = len(w["word"])
        gap = w["s"] - cur[-1]["e"] if cur else 0
        if cur and (n + size > max_chars or gap > 0.6):
            chunks.append(cur)
            cur, n = [], 0
        cur.append(w)
        n += size
        if PUNCT_END.search(w["word"]):
            chunks.append(cur)
            cur, n = [], 0
    if cur:
        chunks.append(cur)
    return chunks


def build_ass(clip: dict, words: list[dict], tl: Timeline, cfg: dict) -> str:
    o, t, c = cfg["output"], cfg["title"], cfg["caption"]
    style = "Style: {name},{font},{size},{primary},{primary},{outline},{back},{bold},0,0,0,100,100,0,0,{border},{ow},0,{align},60,60,{mv},1"
    lines = [
        "[Script Info]", "ScriptType: v4.00+", f"PlayResX: {o['width']}", f"PlayResY: {o['height']}",
        "WrapStyle: 0", "ScaledBorderAndShadow: yes", "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, "
        "Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, "
        "MarginL, MarginR, MarginV, Encoding",
        style.format(
            name="Title", font=t["font"], size=t["size"], primary=ass_color(t["color"]),
            outline=ass_color(t["box_color"], t["box_alpha"]), back=ass_color(t["box_color"], t["box_alpha"]),
            bold=-1 if t["bold"] else 0, border=3, ow=18, align=8, mv=t["margin_top"],
        ),
        style.format(
            name="Caption", font=c["font"], size=c["size"], primary=ass_color(c["color"]),
            outline=ass_color(c["outline_color"]), back=ass_color("#000000", 1.0),
            bold=-1 if c["bold"] else 0, border=1, ow=c["outline"], align=2, mv=c["margin_bottom"],
        ),
        "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    if t["enabled"] and clip.get("title"):
        lines.append(f"Dialogue: 1,{ass_time(0)},{ass_time(tl.duration)},Title,,0,0,0,,{wrap_title(clip['title'])}")

    if c["enabled"]:
        timed = [{"word": ass_escape(w["word"]), "s": tl.map(w["start"]), "e": tl.map(w["end"])} for w in words]
        hi = ass_color(c["highlight"])
        for chunk in chunk_words(timed, c["max_chars"]):
            for i, w in enumerate(chunk):
                start = w["s"]
                end = chunk[i + 1]["s"] if i + 1 < len(chunk) else w["e"] + 0.15
                text = " ".join(
                    f"{{\\c{hi}}}{x['word']}{{\\r}}" if j == i else x["word"] for j, x in enumerate(chunk)
                )
                lines.append(f"Dialogue: 0,{ass_time(start)},{ass_time(end)},Caption,,0,0,0,,{text}")
    return "\n".join(lines) + "\n"


# ---------- 렌더링 ----------

def filter_escape(path: Path) -> str:
    return str(path).replace("\\", "/").replace(":", "\\:").replace("'", "\\'")


def render(video: Path, transcript: dict, clip: dict, job_dir: Path, cfg: dict) -> Path:
    e, o, a = cfg["edit"], cfg["output"], cfg["audio"]
    W, H, speed = o["width"], o["height"], float(e["speed"])
    words = [w for w in all_words(transcript) if w["start"] >= clip["start"] - 0.01 and w["end"] <= clip["end"] + 0.01]
    if not words:
        raise RuntimeError(f"{clip['id']}: 구간 안에 단어가 없습니다")

    ranges = speech_ranges(words, clip, e)
    tl = Timeline(ranges, speed)
    work = job_dir / "work"
    work.mkdir(exist_ok=True)
    ass_path = work / f"{clip['id']}.ass"
    ass_path.write_text(build_ass(clip, words, tl, cfg), encoding="utf-8")

    # 입력을 구간 근처에서만 읽도록 -ss/-t로 자르고, 필터 안의 시각은 그 기준으로 옮긴다
    base = ranges[0][0]
    span = ranges[-1][1] - base
    f = []
    for i, (s, t) in enumerate(ranges):
        s, t = s - base, t - base
        f.append(f"[0:v]trim=start={s:.3f}:end={t:.3f},setpts=PTS-STARTPTS[v{i}]")
        fade = min(0.02, (t - s) / 4)
        f.append(
            f"[0:a]atrim=start={s:.3f}:end={t:.3f},asetpts=PTS-STARTPTS,"
            f"afade=t=in:d={fade:.3f},afade=t=out:st={t - s - fade:.3f}:d={fade:.3f}[a{i}]"
        )
    f.append("".join(f"[v{i}][a{i}]" for i in range(len(ranges))) + f"concat=n={len(ranges)}:v=1:a=1[vc][ac]")
    f.append(f"[vc]setpts=PTS/{speed},fps={o['fps']}[vs]")
    f.append(f"[ac]atempo={speed}[as]")

    if e["reframe"] == "crop":
        f.append(f"[vs]scale=-2:{H},crop={W}:{H}:(iw-{W})*{e['crop_x']}:0,setsar=1[vr]")
    else:
        fg_w = int(W * e["zoom"]) // 2 * 2
        f.append("[vs]split[b1][f1]")
        f.append(f"[b1]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=24:2[bg]")
        f.append(f"[f1]scale={fg_w}:-2[fg]")
        f.append("[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1[vr]")

    fonts_dir = (Path(__file__).resolve().parent.parent / o["fonts_dir"]).resolve()
    f.append(f"[vr]ass=filename='{filter_escape(ass_path)}':fontsdir='{filter_escape(fonts_dir)}'[vout]")

    inputs = ["-ss", f"{base:.3f}", "-t", f"{span + 0.5:.3f}", "-i", str(video)]
    bgm = a.get("bgm")
    if bgm:
        bgm_path = Path(bgm) if Path(bgm).is_absolute() else Path(__file__).resolve().parent.parent / bgm
        inputs += ["-stream_loop", "-1", "-i", str(bgm_path)]
        f.append(f"[1:a]volume={a['bgm_volume']}[bgm]")
        if a["duck"]:
            f.append("[as]asplit[as1][as2]")
            f.append("[bgm][as1]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=400[bgd]")
            f.append("[as2][bgd]amix=inputs=2:duration=first:normalize=0[aout]")
        else:
            f.append("[as][bgm]amix=inputs=2:duration=first:normalize=0[aout]")
        audio_label = "[aout]"
    else:
        audio_label = "[as]"

    script = work / f"{clip['id']}.filter"
    script.write_text(";\n".join(f), encoding="utf-8")
    out_dir = job_dir / "out"
    out_dir.mkdir(exist_ok=True)
    out = out_dir / f"{clip['id']}.mp4"
    ff.run([
        *inputs, "-filter_complex_script", str(script), "-map", "[vout]", "-map", audio_label,
        "-c:v", "libx264", "-preset", "medium", "-crf", str(o["crf"]), "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-t", f"{tl.duration:.3f}", str(out),
    ])
    return out

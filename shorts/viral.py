"""터진 쇼츠·채널 분석.

- discover: 키워드로 최근 쇼츠를 모아 성과도·기여도가 비정상적으로 높은 영상과 급성장 채널을 골라낸다.
- channel : 채널 하나의 쇼츠를 전부 모아 '채널 평균 대비 몇 배 터졌나', 업로드 주기, 시간대, 길이, 제목 패턴을 본다.
- video   : 영상마다 첫 화면·컷 속도·대사·다시 본 구간을 모아 Claude가 훅·구성·자막 스타일·터진 이유를 정리한다.
분석 결과의 playbook은 제작 설정(길이, 자막, 제목 틀, 업로드 시간)에 그대로 옮겨 쓸 수 있게 만든다.
"""
import base64
import json
import os
import re
import statistics
import subprocess
import time
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

import anthropic
import requests
from pydantic import BaseModel

from . import ff, trends
from .trends import _get, fetch_channels, fmt_num, grade, iso_seconds

JST = timezone(timedelta(hours=9))
CLIENTS = [None, "web_safari", "mweb", "tv_simply"]
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿]")


# ---------- 채널 ----------

def resolve_channel(ref: str) -> dict:
    """@handle, 채널 URL, UC로 시작하는 ID 모두 받는다."""
    ref = ref.strip().rstrip("/")
    m = re.search(r"/channel/(UC[\w-]{22})", ref) or re.fullmatch(r"(UC[\w-]{22})", ref)
    if m:
        params = {"id": m.group(1)}
    else:
        h = re.search(r"@([\w.\-]+)", ref)
        if not h:
            raise SystemExit(f"채널을 알아볼 수 없습니다: {ref} (@핸들 또는 채널 URL을 넣어 주세요)")
        params = {"forHandle": "@" + h.group(1)}
    res = _get("channels", part="snippet,statistics,contentDetails", **params)
    if not res.get("items"):
        raise SystemExit(f"채널을 찾지 못했습니다: {ref}")
    return res["items"][0]


def channel_videos(channel: dict, limit: int) -> list[dict]:
    """업로드 재생목록(1유닛/50개)으로 최근 영상 ID를 모아 통계를 붙인다. 검색 API보다 훨씬 싸다."""
    playlist = channel["contentDetails"]["relatedPlaylists"]["uploads"]
    ids, token = [], None
    while len(ids) < limit:
        res = _get("playlistItems", part="contentDetails", playlistId=playlist, maxResults=50, pageToken=token)
        ids += [it["contentDetails"]["videoId"] for it in res.get("items", [])]
        token = res.get("nextPageToken")
        if not token:
            break
    rows = []
    now = datetime.now(timezone.utc)
    for i in range(0, min(len(ids), limit), 50):
        res = _get("videos", part="snippet,statistics,contentDetails", id=",".join(ids[i:i + 50]))
        for v in res.get("items", []):
            sec = iso_seconds(v["contentDetails"]["duration"])
            if not sec or sec > trends.MAX_SHORT_SEC:
                continue
            sn, st = v["snippet"], v["statistics"]
            published = datetime.fromisoformat(sn["publishedAt"].replace("Z", "+00:00"))
            views = int(st.get("viewCount", 0))
            rows.append({
                "id": v["id"], "url": f"https://youtube.com/shorts/{v['id']}", "title": sn["title"],
                "published": published.isoformat(), "sec": sec, "views": views,
                "likes": int(st.get("likeCount", 0)), "comments": int(st.get("commentCount", 0)),
                "views_per_day": round(views / max((now - published).total_seconds() / 86400, 0.5)),
                "tags": sn.get("tags", [])[:15], "desc": sn.get("description", "")[:300],
            })
    return rows


def channel_stats(rows: list[dict], subs: int) -> dict:
    """채널 안에서의 패턴. 터진 영상 = 채널 중앙값의 3배 이상."""
    if not rows:
        return {}
    med = statistics.median(r["views"] for r in rows) or 1
    for r in rows:
        r["x_median"] = round(r["views"] / med, 1)
        r["perf"] = round(r["views"] / subs, 2) if subs else None
    times = sorted(datetime.fromisoformat(r["published"]) for r in rows)
    gaps = [(b - a).total_seconds() / 3600 for a, b in zip(times, times[1:])]
    recent = [t for t in times if t > times[-1] - timedelta(days=28)]

    def bucket(sec: int) -> str:
        return "~15초" if sec < 15 else "15~30초" if sec < 30 else "30~45초" if sec < 45 else "45~60초" if sec <= 60 else "60초~"

    by_len: dict[str, list[int]] = {}
    by_hour: dict[int, list[int]] = {}
    for r in rows:
        by_len.setdefault(bucket(r["sec"]), []).append(r["views"])
        by_hour.setdefault(datetime.fromisoformat(r["published"]).astimezone(JST).hour, []).append(r["views"])
    titles = [r["title"] for r in rows]
    return {
        "shorts": len(rows), "median_views": int(med),
        "hit_ratio": round(sum(r["x_median"] >= 3 for r in rows) / len(rows) * 100, 1),
        "uploads_last_28d": len(recent), "median_gap_hours": round(statistics.median(gaps), 1) if gaps else None,
        "first_upload": times[0].date().isoformat(), "last_upload": times[-1].date().isoformat(),
        "length": {k: {"count": len(v), "median_views": int(statistics.median(v))} for k, v in sorted(by_len.items())},
        "hour_jst": {h: {"count": len(v), "median_views": int(statistics.median(v))} for h, v in sorted(by_hour.items())},
        "title_len_median": int(statistics.median(len(t) for t in titles)),
        "title_emoji_ratio": round(sum(bool(EMOJI.search(t)) for t in titles) / len(titles) * 100, 1),
        "title_hashtag_ratio": round(sum("#" in t for t in titles) / len(titles) * 100, 1),
        "top_tags": [t for t, _ in Counter(tag for r in rows for tag in r["tags"]).most_common(15)],
    }


# ---------- 영상 한 개 자료 모으기 ----------

def _ytdlp(args: list[str]) -> bool:
    """yt-dlp 실행. 봇 확인을 피하려면 YTDLP_BROWSER=chrome (로그인된 브라우저 쿠키) 또는 YTDLP_COOKIES=cookies.txt 설정."""
    auth = []
    if os.environ.get("YTDLP_BROWSER"):
        auth = ["--cookies-from-browser", os.environ["YTDLP_BROWSER"]]
    elif os.environ.get("YTDLP_COOKIES"):
        auth = ["--cookies", os.environ["YTDLP_COOKIES"]]
    res = subprocess.run(["yt-dlp", "--no-warnings", *auth, *args], capture_output=True, text=True)
    return res.returncode == 0


def _with_retry(args: list[str], done) -> bool:
    """봇 확인에 걸리면 다른 플레이어 클라이언트로 다시 시도."""
    for client in CLIENTS:
        extra = ["--extractor-args", f"youtube:player_client={client}"] if client else []
        _ytdlp([*extra, *args])
        if done():
            return True
        time.sleep(3)
    return False


def gather(video_id: str, work: Path) -> dict:
    """메타데이터·자막·다시 본 구간·화면 캡처·컷 수를 모은다. 영상 다운로드가 막히면 스토리보드로 대신한다."""
    work.mkdir(parents=True, exist_ok=True)
    url = f"https://www.youtube.com/watch?v={video_id}"
    info_path = work / "v.info.json"
    if not info_path.exists() and not _with_retry(
        ["--skip-download", "--write-info-json", "-o", str(work / "v"), url], info_path.exists
    ):
        raise RuntimeError(f"{video_id}: 영상 정보를 가져오지 못했습니다 (봇 확인 또는 비공개)")
    info = json.loads(info_path.read_text(encoding="utf-8"))

    if not any(work.glob("v.*.json3")):
        _with_retry(["--skip-download", "--write-auto-subs", "--write-subs", "--sub-langs", "ja-orig,ja,ko-orig,ko,en-orig,en",
                     "--sub-format", "json3", "-o", str(work / "v"), url], lambda: any(work.glob("v.*.json3")))

    transcript = ""
    for sub in sorted(work.glob("v.*.json3")):
        events = json.loads(sub.read_text(encoding="utf-8")).get("events", [])
        lines = []
        for e in events:
            t = "".join(s.get("utf8", "") for s in e.get("segs", [])).replace("\n", " ").strip()
            if t:
                lines.append(f"[{e['tStartMs'] / 1000:.1f}] {t}")
        transcript = "\n".join(lines)
        break

    heat = sorted(info.get("heatmap") or [], key=lambda h: -h["value"])[:5]
    data = {
        "id": video_id, "title": info.get("title"), "channel": info.get("channel"),
        "duration": info.get("duration"), "views": info.get("view_count"), "likes": info.get("like_count"),
        "comments": info.get("comment_count"), "upload_date": info.get("upload_date"),
        "description": (info.get("description") or "")[:500], "tags": (info.get("tags") or [])[:15],
        "transcript": transcript[:6000] or "(자막 없음: 대사 없는 영상이거나 자막 미생성)",
        "replay_peaks": [{"start": round(h["start_time"], 1), "end": round(h["end_time"], 1), "value": round(h["value"], 2)} for h in heat],
        "frames": [], "cuts_per_10s": None, "frame_source": None,
    }

    video = next(work.glob("video.*"), None)
    if not video and _ytdlp(["-f", "bv*[height<=720]+ba/b[height<=720]/b", "--merge-output-format", "mp4",
                             "-o", str(work / "video.%(ext)s"), url]):
        video = next(work.glob("video.*"), None)

    if video:
        dur = ff.probe(str(video))["duration"]
        points = [0.1, 1.0, 2.0, 3.0, dur / 2, max(dur - 1.0, 0.2)]
        for i, t in enumerate(points):
            out = work / f"frame_{i}.jpg"
            if not out.exists():
                ff.run(["-ss", f"{t:.2f}", "-i", str(video), "-frames:v", "1", "-vf", "scale=-2:720", str(out)])
            data["frames"].append({"t": round(t, 1), "path": str(out)})
        data["cuts_per_10s"] = round(count_cuts(video) / max(dur, 1) * 10, 1)
        data["frame_source"] = "video"
    else:
        sheet = storyboard(info, work)
        if sheet:
            data["frames"].append({"t": 0.0, "path": str(sheet)})
            data["frame_source"] = "storyboard(저해상도)"
    return data


def count_cuts(video: Path, threshold: float = 0.3) -> int:
    res = subprocess.run(
        [ff.ffmpeg_bin(), "-hide_banner", "-i", str(video), "-vf", f"select='gt(scene,{threshold})',showinfo",
         "-an", "-f", "null", "-"],
        capture_output=True, text=True,
    )
    return res.stderr.count("pts_time:")


def storyboard(info: dict, work: Path) -> Path | None:
    """영상 다운로드가 막혔을 때 쓰는 미리보기 격자 이미지(가장 큰 해상도의 첫 장)."""
    out = work / "storyboard.jpg"
    if out.exists():
        return out
    boards = [f for f in info.get("formats", []) if f.get("format_id", "").startswith("sb") and f.get("fragments")]
    if not boards:
        return None
    best = max(boards, key=lambda f: (f.get("width") or 0))
    try:
        r = requests.get(best["fragments"][0]["url"], timeout=30)
        r.raise_for_status()
    except requests.RequestException:
        return None
    out.write_bytes(r.content)
    return out


# ---------- Claude 분석 ----------

class Breakdown(BaseModel):
    format: str
    hook_text: str
    hook_type: str
    first_frame: str
    structure: list[str]
    caption_style: str
    edit_pace: str
    audio: str
    why_it_worked: list[str]
    reusable_template: str
    source_risk: str


class Playbook(BaseModel):
    summary: str
    patterns: list[str]
    hook_templates: list[str]
    recommended_settings: list[str]
    formats_for_cc_by: list[str]
    avoid: list[str]


def _image_block(path: str) -> dict:
    return {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg",
                                        "data": base64.b64encode(Path(path).read_bytes()).decode()}}


def breakdown(data: dict, model: str) -> Breakdown:
    content: list[dict] = []
    for fr in data["frames"]:
        content.append({"type": "text", "text": f"화면 캡처 ({fr['t']}초)" if data["frame_source"] == "video"
                        else "스토리보드 격자 (왼쪽 위부터 시간순, 저해상도)"})
        content.append(_image_block(fr["path"]))
    meta = {k: v for k, v in data.items() if k not in ("frames", "transcript")}
    content.append({"type": "text", "text": f"<meta>\n{json.dumps(meta, ensure_ascii=False)}\n</meta>\n"
                                            f"<transcript>\n{data['transcript']}\n</transcript>\n\n이 쇼츠를 분석해줘."})
    client = anthropic.Anthropic()
    resp = client.messages.parse(
        model=model, max_tokens=8000, thinking={"type": "adaptive"}, output_config={"effort": "medium"},
        system=(
            "너는 쇼츠 분석가다. 화면 캡처, 대사, 수치, 다시 본 구간(replay_peaks)을 근거로 이 영상이 왜 터졌는지 분해한다.\n"
            "- hook_text: 첫 1~3초의 화면 문구나 첫 대사 (원문 그대로 + 괄호 안에 한국어 뜻)\n"
            "- structure: 시간 순서의 구성 단계 (예: '0~2초 충격 장면', '2~10초 설명')\n"
            "- caption_style: 폰트 굵기, 색, 테두리, 위치, 한 줄 글자 수, 제목 바 유무\n"
            "- edit_pace: cuts_per_10s 수치와 화면으로 본 전환 속도\n"
            "- reusable_template: 다른 소재에 그대로 옮길 수 있는 틀을 한 문단으로\n"
            "- source_risk: 원본이 남의 영상 재업로드·TV·음원 사용으로 보이는지 판단 (저작권·재사용 콘텐츠 위험)\n"
            "화면에서 확인할 수 없는 것은 추측하지 말고 '확인 불가'라고 쓴다. 한국어로 답한다."
        ),
        messages=[{"role": "user", "content": content}],
        output_format=Breakdown,
    )
    if resp.parsed_output is None:
        raise RuntimeError(f"{data['id']}: 분석 응답을 받지 못했습니다 (stop_reason={resp.stop_reason})")
    return resp.parsed_output


def playbook(context: str, items: list[dict], model: str) -> Playbook:
    client = anthropic.Anthropic()
    resp = client.messages.parse(
        model=model, max_tokens=8000, thinking={"type": "adaptive"}, output_config={"effort": "high"},
        system=(
            "너는 쇼츠 채널 전략가다. 여러 터진 영상의 분해 결과와 채널 수치를 종합한다.\n"
            "- patterns: 여러 영상에 반복되는 성공 요인만 (한 영상에만 있는 건 제외)\n"
            "- recommended_settings: 제작 프로그램에 넣을 구체적 값 (길이 초, 자막 스타일, 제목 글자 수, 업로드 시각 JST, 주기)\n"
            "- formats_for_cc_by: CC-BY 롱폼 영상 + 일본어 해설 나레이션으로 재현 가능한 포맷만\n"
            "- avoid: 남의 영상 재업로드, 상업 음원, 번역만 한 영상처럼 수익화·저작권 위험이 있는 요소\n"
            "한국어로 답한다."
        ),
        messages=[{"role": "user", "content": f"{context}\n\n<videos>\n{json.dumps(items, ensure_ascii=False)}\n</videos>"}],
        output_format=Playbook,
    )
    if resp.parsed_output is None:
        raise RuntimeError("종합 분석 응답을 받지 못했습니다")
    return resp.parsed_output


# ---------- 실행 흐름 ----------

def analyze_videos(video_ids: list[str], out_dir: Path, model: str) -> list[dict]:
    results = []
    for vid in video_ids:
        cache = out_dir / "videos" / vid / "breakdown.json"
        if cache.exists():
            results.append(json.loads(cache.read_text(encoding="utf-8")))
            continue
        print(f"  영상 분석: {vid}")
        try:
            data = gather(vid, out_dir / "videos" / vid)
            bd = breakdown(data, model)
        except RuntimeError as e:
            print(f"    건너뜀: {e}")
            continue
        item = {k: v for k, v in data.items() if k not in ("frames", "transcript")} | bd.model_dump()
        cache.write_text(json.dumps(item, ensure_ascii=False, indent=1), encoding="utf-8")
        results.append(item)
    return results


def video_section(items: list[dict]) -> list[str]:
    L = []
    for it in items:
        L += [f"### [{it['title']}](https://youtube.com/shorts/{it['id']})", "",
              f"조회수 {fmt_num(it.get('views'))} · {it.get('duration')}초 · 컷 {it.get('cuts_per_10s') or '-'}회/10초 · "
              f"화면 자료: {it.get('frame_source') or '없음'}", "",
              f"- **포맷:** {it['format']}", f"- **훅:** {it['hook_text']} ({it['hook_type']})",
              f"- **첫 화면:** {it['first_frame']}", "- **구성:**"] + [f"  - {s}" for s in it["structure"]] + [
              f"- **자막:** {it['caption_style']}", f"- **편집 속도:** {it['edit_pace']}", f"- **소리:** {it['audio']}",
              "- **터진 이유:**"] + [f"  - {w}" for w in it["why_it_worked"]] + [
              f"- **재사용 틀:** {it['reusable_template']}", f"- **소스 위험:** {it['source_risk']}", ""]
    return L


def playbook_section(pb: Playbook) -> list[str]:
    return (["## 종합", "", pb.summary, "", "### 반복되는 성공 요인", ""] + [f"- {p}" for p in pb.patterns]
            + ["", "### 훅 템플릿", ""] + [f"- {h}" for h in pb.hook_templates]
            + ["", "### 제작 설정 제안", ""] + [f"- {s}" for s in pb.recommended_settings]
            + ["", "### CC-BY + 일본어 해설로 재현 가능한 포맷", ""] + [f"- {f}" for f in pb.formats_for_cc_by]
            + ["", "### 피할 것", ""] + [f"- {a}" for a in pb.avoid] + [""])


def run_channel(ref: str, out_root: Path, limit: int, top: int, model: str) -> Path:
    ch = resolve_channel(ref)
    name, subs = ch["snippet"]["title"], int(ch["statistics"].get("subscriberCount", 0))
    out = out_root / f"channel_{ch['id']}"
    out.mkdir(parents=True, exist_ok=True)
    print(f"채널: {name} (구독자 {fmt_num(subs)})")
    rows = channel_videos(ch, limit)
    if not rows:
        raise SystemExit("이 채널에서 쇼츠를 찾지 못했습니다.")
    stats = channel_stats(rows, subs)
    (out / "videos.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  쇼츠 {stats['shorts']}개, 중앙값 {fmt_num(stats['median_views'])}회, 터진 비율 {stats['hit_ratio']}%")

    hits = sorted(rows, key=lambda r: -r["x_median"])[:top]
    items = analyze_videos([h["id"] for h in hits], out, model)
    pb = playbook(f"채널: {name}, 구독자 {subs}\n<channel_stats>\n{json.dumps(stats, ensure_ascii=False)}\n</channel_stats>", items, model)

    L = [f"# 채널 분석: {name}", "", f"https://youtube.com/channel/{ch['id']} · 구독자 {fmt_num(subs)} · "
         f"개설 {ch['snippet']['publishedAt'][:10]}", "",
         "## 채널 수치", "",
         f"- 분석한 쇼츠 {stats['shorts']}개 ({stats['first_upload']} ~ {stats['last_upload']})",
         f"- 조회수 중앙값 {fmt_num(stats['median_views'])} · 중앙값 3배 이상 터진 비율 {stats['hit_ratio']}%",
         f"- 최근 28일 업로드 {stats['uploads_last_28d']}개 · 업로드 간격 중앙값 {stats['median_gap_hours']}시간",
         f"- 제목 길이 중앙값 {stats['title_len_median']}자 · 이모지 {stats['title_emoji_ratio']}% · 해시태그 {stats['title_hashtag_ratio']}%",
         f"- 자주 쓰는 태그: {', '.join(stats['top_tags'][:10]) or '-'}", "",
         "| 길이 | 개수 | 조회수 중앙값 |", "|---|---|---|"]
    L += [f"| {k} | {v['count']} | {fmt_num(v['median_views'])} |" for k, v in stats["length"].items()]
    L += ["", "| 업로드 시각(JST) | 개수 | 조회수 중앙값 |", "|---|---|---|"]
    L += [f"| {h}시 | {v['count']} | {fmt_num(v['median_views'])} |" for h, v in stats["hour_jst"].items()]
    L += ["", "## 채널 평균 대비 가장 터진 영상", "", "| 배수 | 조회수 | 성과도 | 길이 | 제목 |", "|---|---|---|---|---|"]
    L += [f"| {h['x_median']}배 | {fmt_num(h['views'])} | {h['perf']} {grade('perf', h['perf'])} | {h['sec']}초 | "
          f"[{h['title'].replace('|', '/')}]({h['url']}) |" for h in hits]
    L += [""] + playbook_section(pb) + ["## 영상별 분해", ""] + video_section(items)
    report = out / "report.md"
    report.write_text("\n".join(L) + "\n", encoding="utf-8")
    return report


def run_discover(keyword: str, out_root: Path, days: int, limit: int, region: str, lang: str, top: int, model: str) -> Path:
    slug = re.sub(r"[^\w가-힣ぁ-んァ-ン一-龥-]+", "_", keyword)[:40]
    out = out_root / f"discover_{slug}"
    out.mkdir(parents=True, exist_ok=True)
    raw = out / "collected.json"
    if raw.exists():
        saved = json.loads(raw.read_text(encoding="utf-8"))
        rows, channels = saved["rows"], saved["channels"]
    else:
        print(f"쇼츠 수집: '{keyword}' {region} 최근 {days}일...")
        rows, channels = trends.collect(keyword, days, limit, region, lang)
        raw.write_text(json.dumps({"rows": rows, "channels": channels}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  쇼츠 {len(rows)}개, 채널 {len(channels)}개")

    # 터진 영상: 성과도(구독자 대비)와 기여도(채널 평균 대비)를 함께 본다. 대형 채널의 평범한 영상은 걸러진다.
    def score(r: dict) -> float:
        return (min(r.get("perf") or 0, 100) / 10) + (min(r.get("contrib") or 0, 30) / 3)

    hits = sorted(rows, key=lambda r: -score(r))[:top]
    hot = sorted((c for c in channels.values() if c["days"] <= 365), key=lambda c: -c["sub_per_day"])[:15]
    items = analyze_videos([h["id"] for h in hits], out, model)
    pb = playbook(f"키워드: {keyword}, 지역: {region}, 최근 {days}일", items, model)

    L = [f"# 터진 쇼츠 찾기: {keyword} ({region}, 최근 {days}일)", "",
         f"수집 {len(rows)}개 중 성과도(구독자 대비)와 기여도(채널 평균 대비)가 함께 높은 영상 {len(hits)}개를 분해했습니다.", "",
         "## 터진 영상", "", "| 성과도 | 기여도 | 조회수 | 구독자 | 길이 | 제목 |", "|---|---|---|---|---|---|"]
    L += [f"| {h['perf']} {grade('perf', h['perf'])} | {h.get('contrib')} {grade('contrib', h.get('contrib'))} | "
          f"{fmt_num(h['views'])} | {fmt_num(h['subs'])} | {h['sec']}초 | [{h['title'].replace('|', '/')}]({h['url']}) |" for h in hits]
    L += ["", "## 급성장 채널 (개설 1년 이내)", "", "| 채널 | 개설 | 구독자 | 일평균 구독 | 영상성과 | 영상 수 |", "|---|---|---|---|---|---|"]
    L += [f"| [{c['name'].replace('|', '/')}]({c['url']}) | {c['created']} | {fmt_num(c['subs'])} | "
          f"{c['sub_per_day']} {grade('sub_per_day', c['sub_per_day'])} | {c['video_perf']} {grade('video_perf', c['video_perf'])} | "
          f"{c['videos']} |" for c in hot]
    L += ["", "채널을 더 깊게 보려면: `python -m shorts viral channel <채널 URL>`", ""]
    L += playbook_section(pb) + ["## 영상별 분해", ""] + video_section(items)
    report = out / "report.md"
    report.write_text("\n".join(L) + "\n", encoding="utf-8")
    return report


def run_videos(refs: list[str], out_root: Path, model: str) -> Path:
    ids = []
    for ref in refs:
        m = re.search(r"(?:v=|youtu\.be/|shorts/)([\w-]{11})", ref) or re.fullmatch(r"([\w-]{11})", ref)
        if not m:
            raise SystemExit(f"영상 주소를 알아볼 수 없습니다: {ref}")
        ids.append(m.group(1))
    out = out_root / f"videos_{datetime.now(JST):%Y%m%d_%H%M}"
    out.mkdir(parents=True, exist_ok=True)
    items = analyze_videos(ids, out, model)
    if not items:
        raise SystemExit("분석한 영상이 없습니다.")
    pb = playbook("사용자가 고른 참고 쇼츠", items, model)
    L = [f"# 쇼츠 분석 ({len(items)}개)", ""] + playbook_section(pb) + ["## 영상별 분해", ""] + video_section(items)
    report = out / "report.md"
    report.write_text("\n".join(L) + "\n", encoding="utf-8")
    return report

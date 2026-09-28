"""Claude가 전사본에서 쇼츠로 쓸 구간을 고른다."""
import json
from pathlib import Path

import anthropic
from pydantic import BaseModel

from .transcribe import all_words

SYSTEM = """너는 유튜브 쇼츠 편집자다. 롱폼 영상 전사본에서 조회수가 잘 나올 쇼츠 구간을 고른다.

규칙:
- 각 구간은 원본에서 연속된 한 덩어리다. start/end는 전사본에 적힌 초 단위 시각을 그대로 쓴다.
- 완성본은 {speed}배속 + 무음 제거를 거친다. 그래서 원본 기준 길이는 약 {raw_min:.0f}~{raw_max:.0f}초로 잡는다.
- 구간끼리 겹치지 않는다. 문장 중간에서 시작하거나 끝내지 않는다.
- title: 화면 상단에 붙을 제목. 15자 안팎, 궁금증을 만드는 한국어.
- hook: 구간 첫 문장이 왜 시청자를 붙잡는지 한 줄.
- score: 1~10, 쇼츠로서의 기대 성과.

선별 기준:
{guide}"""


class Clip(BaseModel):
    start: float
    end: float
    title: str
    hook: str
    score: int


class Selection(BaseModel):
    clips: list[Clip]


def format_transcript(transcript: dict) -> str:
    return "\n".join(f"[{s['start']:.1f}-{s['end']:.1f}] {s['text']}" for s in transcript["segments"])


def select(transcript: dict, out: Path, cfg: dict) -> list[dict]:
    if out.exists():
        return json.loads(out.read_text(encoding="utf-8"))

    s, e = cfg["select"], cfg["edit"]
    # 무음 제거로 대략 15% 줄어든다고 보고 원본 기준 길이를 역산
    shrink = e["speed"] / (0.85 if e["remove_silence"] else 1.0)
    system = SYSTEM.format(
        speed=e["speed"], raw_min=s["min_sec"] * shrink, raw_max=s["max_sec"] * shrink, guide=s["guide"]
    )
    client = anthropic.Anthropic()
    resp = client.messages.parse(
        model=cfg["llm"]["model"],
        max_tokens=16000,
        thinking={"type": "adaptive"},
        output_config={"effort": cfg["llm"]["effort"]},
        system=system,
        messages=[{
            "role": "user",
            "content": f"쇼츠 {s['count']}개를 골라줘.\n\n<transcript>\n{format_transcript(transcript)}\n</transcript>",
        }],
        output_format=Selection,
    )
    if resp.stop_reason == "refusal":
        raise RuntimeError("Claude가 요청을 거절했습니다. 전사본 내용을 확인하세요.")
    if resp.stop_reason == "max_tokens" or resp.parsed_output is None:
        raise RuntimeError("구간 선택 응답이 잘렸습니다. select.count를 줄여 다시 실행하세요.")

    clips = snap(resp.parsed_output.clips, transcript)
    out.write_text(json.dumps(clips, ensure_ascii=False, indent=1), encoding="utf-8")
    return clips


def snap(clips: list[Clip], transcript: dict) -> list[dict]:
    """LLM이 준 시각을 실제 단어 경계에 맞추고, 겹치는 구간은 버린다."""
    words = all_words(transcript)
    result = []
    for c in sorted(clips, key=lambda c: -c.score):
        inside = [w for w in words if w["end"] > c.start and w["start"] < c.end]
        if len(inside) < 3:
            continue
        start, end = inside[0]["start"], inside[-1]["end"]
        if any(start < r["end"] and end > r["start"] for r in result):
            continue
        result.append({"start": start, "end": end, "title": c.title, "hook": c.hook, "score": c.score})
    result.sort(key=lambda r: r["start"])
    for i, r in enumerate(result, 1):
        r["id"] = f"clip_{i:02d}"
    return result

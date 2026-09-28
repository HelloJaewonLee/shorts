"""자연어 수정 지시("목소리 빠르게", "제목 굵게")를 설정 변경으로 바꾼다."""
import json

import yaml
from pydantic import BaseModel

from . import llm

SYSTEM = """너는 쇼츠 편집 프로그램의 설정 담당이다. 사용자의 수정 지시를 설정 변경 목록으로 바꾼다.

- path는 현재 설정에 이미 있는 키만 점 경로로 쓴다 (예: edit.speed, caption.highlight).
- value_json은 새 값을 JSON으로 쓴다 (숫자 1.4, 불리언 true, 문자열 "\\"#FF0000\\"").
- 특정 쇼츠의 제목을 바꾸라는 지시는 title_changes에 clip_id와 새 제목으로 넣는다.
- "조금", "좀"은 기존 값의 10~20% 정도로 해석한다.
- 설정으로 표현할 수 없는 요청은 unsupported에 한 줄로 적고 억지로 바꾸지 않는다."""


class Change(BaseModel):
    path: str
    value_json: str


class TitleChange(BaseModel):
    clip_id: str
    title: str


class Plan(BaseModel):
    changes: list[Change]
    title_changes: list[TitleChange]
    unsupported: list[str]


def plan(instruction: str, cfg: dict, clips: list[dict]) -> Plan:
    shown = {k: v for k, v in cfg.items() if k != "llm"}
    titles = "\n".join(f"{c['id']}: {c['title']}" for c in clips)
    return llm.parse(
        Plan, SYSTEM,
        f"<config>\n{yaml.safe_dump(shown, allow_unicode=True)}</config>\n"
        f"<clips>\n{titles}\n</clips>\n\n수정 지시: {instruction}",
        effort="low", max_tokens=4000,
    )


def parse_value(raw: str):
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw

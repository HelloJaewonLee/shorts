"""Claude 호출 통로. 두 가지 방식 중 하나로 돈다.

- claude-code: 설치된 Claude Code CLI(`claude -p`)를 부른다. Pro/Max 구독 사용량 안에서 처리된다. API 키 불필요.
- api        : Anthropic API를 SDK로 부른다. ANTHROPIC_API_KEY 필요, 사용량만큼 별도 요금.

선택: 환경변수 SHORTS_LLM 또는 config의 llm.backend (auto면 claude CLI가 있으면 claude-code).
"""
import base64
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

from . import config

T = TypeVar("T", bound=BaseModel)


def backend() -> str:
    choice = os.environ.get("SHORTS_LLM") or config.load()["llm"].get("backend", "auto")
    if choice == "auto":
        return "claude-code" if shutil.which("claude") else "api"
    return choice


def parse(schema: type[T], system: str, text: str, images: list[str] | None = None,
          effort: str = "medium", max_tokens: int = 16000) -> T:
    """system 지시 + 본문(+이미지)을 보내고 schema 형태로 검증된 결과를 돌려준다."""
    images = images or []
    if backend() == "claude-code":
        return _via_cli(schema, system, text, images)
    return _via_api(schema, system, text, images, effort, max_tokens)


def _via_cli(schema: type[T], system: str, text: str, images: list[str]) -> T:
    cfg = config.load()["llm"]
    prompt = f"{system}\n\n{text}"
    args = ["claude", "-p", "--output-format", "json", "--json-schema", json.dumps(schema.model_json_schema())]
    if images:
        listing = "\n".join(f"- {p}" for p in images)
        prompt += f"\n\n아래 이미지 파일을 Read 도구로 모두 열어 보고 분석에 반영하라. 다른 도구는 쓰지 않는다.\n{listing}"
        args += ["--allowedTools", "Read"]
        for d in sorted({str(Path(p).resolve().parent) for p in images}):
            args += ["--add-dir", d]
    if cfg.get("cli_model"):
        args += ["--model", cfg["cli_model"]]
    res = subprocess.run(args, input=prompt, capture_output=True, text=True, timeout=900)
    try:
        out = json.loads(res.stdout)
    except json.JSONDecodeError:
        raise RuntimeError(f"claude CLI 응답을 읽지 못했습니다: {(res.stderr or res.stdout)[-500:]}")
    if out.get("is_error") or out.get("structured_output") is None:
        raise RuntimeError(f"claude CLI 오류: {out.get('subtype')} {str(out.get('result'))[:300]}")
    return schema.model_validate(out["structured_output"])


def _via_api(schema: type[T], system: str, text: str, images: list[str], effort: str, max_tokens: int) -> T:
    import anthropic

    content: list[dict] = [
        {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg",
                                     "data": base64.b64encode(Path(p).read_bytes()).decode()}}
        for p in images
    ]
    content.append({"type": "text", "text": text})
    client = anthropic.Anthropic()
    resp = client.messages.parse(
        model=config.load()["llm"]["model"],
        max_tokens=max_tokens,
        thinking={"type": "adaptive"},
        output_config={"effort": effort},
        system=system,
        messages=[{"role": "user", "content": content}],
        output_format=schema,
    )
    if resp.stop_reason == "refusal":
        raise RuntimeError("Claude가 요청을 거절했습니다.")
    if resp.parsed_output is None:
        raise RuntimeError(f"응답이 잘렸거나 형식이 맞지 않습니다 (stop_reason={resp.stop_reason})")
    return resp.parsed_output

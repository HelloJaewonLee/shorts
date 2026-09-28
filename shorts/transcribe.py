"""faster-whisper로 단어 단위 타임스탬프가 있는 전사본을 만든다."""
import json
from pathlib import Path


def transcribe(video: Path, out: Path, cfg: dict) -> dict:
    if out.exists():
        return json.loads(out.read_text(encoding="utf-8"))

    from faster_whisper import WhisperModel

    t = cfg["transcribe"]
    model = WhisperModel(t["model"], device=t["device"], compute_type="auto")
    segments, _ = model.transcribe(
        str(video), language=t["language"] or None, word_timestamps=True, vad_filter=True
    )
    data = {"segments": []}
    for seg in segments:
        words = [
            {"start": round(w.start, 3), "end": round(w.end, 3), "word": w.word.strip()}
            for w in (seg.words or [])
            if w.word.strip()
        ]
        data["segments"].append(
            {"start": round(seg.start, 3), "end": round(seg.end, 3), "text": seg.text.strip(), "words": words}
        )
        print(f"  [{seg.start:7.1f}s] {seg.text.strip()}")
    out.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    return data


def all_words(transcript: dict) -> list[dict]:
    return [w for seg in transcript["segments"] for w in seg["words"]]

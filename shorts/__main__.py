"""사용법:
  python -m shorts trends "키워드" [--days 30] [--limit 200]      # 1단계: 어떤 쇼츠가 많고 잘 되는지
  python -m shorts make  <영상파일|URL> [--trend 키워드] [--count 5]  # 2단계: 롱폼 → 쇼츠
  python -m shorts list  <이름>
  python -m shorts render <이름> [--clip clip_01]
  python -m shorts revise <이름> "목소리 좀 빠르게, 제목 굵게" [--clip clip_01]
"""
import argparse
import re
import json
import shutil
import subprocess
import sys
from pathlib import Path

from . import config, edit, ff, highlights, revise, transcribe, trends

JOBS = config.ROOT / "jobs"
TRENDS = config.ROOT / "trends"


def slug(text: str) -> str:
    return re.sub(r"[^\w가-힣-]+", "_", text).strip("_")[:40] or "trend"


def job_paths(name: str) -> dict:
    d = JOBS / name
    return {
        "dir": d, "config": d / "config.yaml", "transcript": d / "transcript.json",
        "clips": d / "clips.json", "source": next(iter(sorted(d.glob("source.*"))), d / "source.mp4"),
    }


def fetch_source(src: str, job_dir: Path) -> Path:
    if src.startswith(("http://", "https://")):
        print("영상 다운로드 중...")
        subprocess.run(
            ["yt-dlp", "-f", "bv*[height<=1080]+ba/b[height<=1080]", "--merge-output-format", "mp4",
             "-o", str(job_dir / "source.%(ext)s"), src],
            check=True,
        )
        return next(job_dir.glob("source.*"))
    path = Path(src).expanduser().resolve()
    if not path.exists():
        sys.exit(f"파일이 없습니다: {path}")
    dest = job_dir / f"source{path.suffix.lower()}"
    if not dest.exists():
        try:
            dest.symlink_to(path)
        except OSError:
            shutil.copy2(path, dest)
    return dest


def render_clips(p: dict, cfg: dict, only: str | None = None) -> None:
    transcript = json.loads(p["transcript"].read_text(encoding="utf-8"))
    clips = json.loads(p["clips"].read_text(encoding="utf-8"))
    for clip in clips:
        if only and clip["id"] != only:
            continue
        out = edit.render(p["source"], transcript, clip, p["dir"], cfg)
        print(f"  ✔ {out.relative_to(config.ROOT)}  [{clip['title']}]")


def cmd_make(args) -> None:
    name = args.name or Path(args.source.rstrip("/")).stem[:40] or "job"
    p = job_paths(name)
    p["dir"].mkdir(parents=True, exist_ok=True)
    cfg = config.load(p["config"])
    if args.count:
        cfg["select"]["count"] = args.count
    if args.whisper:
        cfg["transcribe"]["model"] = args.whisper
    if args.trend:
        guide = TRENDS / slug(args.trend) / "guide.txt"
        if not guide.exists():
            sys.exit(f"트렌드 분석 결과가 없습니다. 먼저 실행: python -m shorts trends \"{args.trend}\"")
        cfg["select"]["guide"] = guide.read_text(encoding="utf-8")
        print(f"트렌드 기준 적용: {guide.relative_to(config.ROOT)}")
    config.save(cfg, p["config"])

    source = fetch_source(args.source, p["dir"])
    p["source"] = source
    info = ff.probe(str(source))
    if not info["has_audio"]:
        sys.exit("오디오가 없는 영상입니다.")
    print(f"원본 {info['duration'] / 60:.1f}분, {info['width']}x{info['height']}")

    print("1/3 전사 중 (faster-whisper)...")
    transcript = transcribe.transcribe(source, p["transcript"], cfg)
    print("2/3 쇼츠 구간 고르는 중 (Claude)...")
    clips = highlights.select(transcript, p["clips"], cfg)
    for c in clips:
        print(f"  {c['id']}  {c['start']:.0f}s~{c['end']:.0f}s  ★{c['score']}  {c['title']}")
    print("3/3 렌더링 중...")
    render_clips(p, cfg)
    print(f"\n완료. 수정하려면: python -m shorts revise {name} \"제목 더 크게\"")


def cmd_list(args) -> None:
    p = job_paths(args.name)
    for c in json.loads(p["clips"].read_text(encoding="utf-8")):
        print(f"{c['id']}  {c['start']:.0f}s~{c['end']:.0f}s  ★{c['score']}  {c['title']}\n    훅: {c['hook']}")


def cmd_render(args) -> None:
    p = job_paths(args.name)
    render_clips(p, config.load(p["config"]), args.clip)


def cmd_revise(args) -> None:
    p = job_paths(args.name)
    cfg = config.load(p["config"])
    clips = json.loads(p["clips"].read_text(encoding="utf-8"))
    result = revise.plan(args.instruction, cfg, clips)

    for ch in result.changes:
        value = revise.parse_value(ch.value_json)
        try:
            config.set_path(cfg, ch.path, value)
            print(f"  {ch.path} → {value}")
        except KeyError:
            print(f"  (건너뜀) 없는 설정: {ch.path}")
    for tc in result.title_changes:
        for c in clips:
            if c["id"] == tc.clip_id:
                c["title"] = tc.title
                print(f"  {c['id']} 제목 → {tc.title}")
    for u in result.unsupported:
        print(f"  (지원 안 함) {u}")

    config.save(cfg, p["config"])
    p["clips"].write_text(json.dumps(clips, ensure_ascii=False, indent=1), encoding="utf-8")

    paths = [ch.path for ch in result.changes]
    if any(x.startswith("transcribe.") for x in paths):
        p["transcript"].unlink(missing_ok=True)
        p["clips"].unlink(missing_ok=True)
        print("전사 설정이 바뀌어 처음부터 다시 만듭니다: make 명령을 다시 실행하세요.")
        return
    if any(x.startswith("select.") for x in paths):
        p["clips"].unlink(missing_ok=True)
        transcript = json.loads(p["transcript"].read_text(encoding="utf-8"))
        highlights.select(transcript, p["clips"], cfg)
    if result.changes or result.title_changes:
        render_clips(p, cfg, args.clip)


def cmd_trends(args) -> None:
    cfg = config.load()
    report = trends.analyze(
        args.keyword, TRENDS / slug(args.keyword), args.days, args.limit, args.region, args.lang, cfg["llm"]["model"]
    )
    print(f"\n리포트: {report.relative_to(config.ROOT)}")
    print(f"이 기준으로 쇼츠 만들기: python -m shorts make <영상> --trend \"{args.keyword}\"")


def main() -> None:
    ap = argparse.ArgumentParser(prog="shorts", description="롱폼 영상 → 쇼츠 자동 생성")
    sub = ap.add_subparsers(dest="cmd", required=True)

    t = sub.add_parser("trends", help="키워드로 쇼츠 트렌드 분석 (YOUTUBE_API_KEY 필요)")
    t.add_argument("keyword")
    t.add_argument("--days", type=int, default=30, help="최근 며칠 (기본 30)")
    t.add_argument("--limit", type=int, default=200, help="수집할 영상 수 (50개당 검색 100유닛)")
    t.add_argument("--region", default="KR")
    t.add_argument("--lang", default="ko")
    t.set_defaults(func=cmd_trends)

    m = sub.add_parser("make", help="영상 하나로 쇼츠 여러 개 만들기")
    m.add_argument("source", help="영상 파일 경로 또는 URL")
    m.add_argument("--name", help="작업 이름 (jobs/<이름>)")
    m.add_argument("--count", type=int, help="쇼츠 개수")
    m.add_argument("--whisper", help="whisper 모델 (small, medium, large-v3)")
    m.add_argument("--trend", help="trends로 분석한 키워드. 그 결과를 구간 선별 기준으로 사용")
    m.set_defaults(func=cmd_make)

    ls = sub.add_parser("list", help="고른 구간 보기")
    ls.add_argument("name")
    ls.set_defaults(func=cmd_list)

    r = sub.add_parser("render", help="설정대로 다시 렌더링")
    r.add_argument("name")
    r.add_argument("--clip")
    r.set_defaults(func=cmd_render)

    rv = sub.add_parser("revise", help="말로 수정하고 다시 렌더링")
    rv.add_argument("name")
    rv.add_argument("instruction")
    rv.add_argument("--clip", help="이 쇼츠만 다시 렌더링")
    rv.set_defaults(func=cmd_revise)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

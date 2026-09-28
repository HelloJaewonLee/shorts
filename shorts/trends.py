"""유튜브 쇼츠 트렌드 분석.

키워드로 최근 쇼츠를 모아 조회수·일평균 조회수·성과도(조회수 ÷ 구독자, 뷰트랩 방식)를 계산하고,
Claude가 영상마다 포맷·훅 유형을 분류한 뒤 "어떤 쇼츠가 많고, 어떤 쇼츠가 잘 되는지"를 집계한다.
결과의 guide.txt는 make --trend 로 쇼츠 구간 선별 기준에 그대로 들어간다.
"""
import csv
import json
import os
import re
import statistics
from datetime import datetime, timedelta, timezone
from pathlib import Path

import anthropic
import requests
from pydantic import BaseModel

API = "https://www.googleapis.com/youtube/v3"
MAX_SHORT_SEC = 180

FORMATS = [
    "정보·지식 해설", "사건사고·실화", "감동·사연", "랭킹·TOP N", "리뷰·언박싱", "하우투·팁",
    "유머·밈", "인터뷰·토크 클립", "영화·드라마 요약", "브이로그·일상", "동물", "먹방·요리",
    "게임", "스포츠 하이라이트", "음악·챌린지", "뉴스·이슈", "기타",
]


def _get(path: str, **params) -> dict:
    key = os.environ.get("YOUTUBE_API_KEY")
    if not key:
        raise SystemExit("YOUTUBE_API_KEY 환경변수가 없습니다. Google Cloud에서 YouTube Data API v3 키를 발급하세요.")
    r = requests.get(f"{API}/{path}", params={**params, "key": key}, timeout=30)
    if r.status_code != 200:
        raise RuntimeError(f"YouTube API 오류 {r.status_code}: {r.text[:300]}")
    return r.json()


def iso_seconds(d: str) -> int:
    m = re.fullmatch(r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", d or "")
    if not m:
        return 0
    dd, h, mi, s = (int(x or 0) for x in m.groups())
    return dd * 86400 + h * 3600 + mi * 60 + s


def collect(keyword: str, days: int, limit: int, region: str, lang: str) -> tuple[list[dict], dict]:
    """search.list(100 유닛/회)로 후보를 모으고 videos/channels로 통계를 붙인다."""
    after = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    ids, token = [], None
    while len(ids) < limit:
        res = _get(
            "search", part="id", q=keyword, type="video", videoDuration="short", order="viewCount",
            publishedAfter=after, regionCode=region, relevanceLanguage=lang, maxResults=50, pageToken=token,
        )
        ids += [it["id"]["videoId"] for it in res.get("items", [])]
        token = res.get("nextPageToken")
        if not token:
            break
    ids = list(dict.fromkeys(ids))[:limit]

    videos = []
    for i in range(0, len(ids), 50):
        res = _get("videos", part="snippet,statistics,contentDetails", id=",".join(ids[i:i + 50]))
        videos += res.get("items", [])

    ch_ids = list({v["snippet"]["channelId"] for v in videos})
    channels = fetch_channels(ch_ids)

    now = datetime.now(timezone.utc)
    rows = []
    for v in videos:
        sec = iso_seconds(v["contentDetails"]["duration"])
        if not sec or sec > MAX_SHORT_SEC:
            continue
        sn, st = v["snippet"], v["statistics"]
        published = datetime.fromisoformat(sn["publishedAt"].replace("Z", "+00:00"))
        age = max((now - published).total_seconds() / 86400, 0.5)
        views = int(st.get("viewCount", 0))
        ch = channels.get(sn["channelId"], {})
        sub, avg = ch.get("subs", 0), ch.get("avg_views", 0)
        rows.append({
            "id": v["id"], "url": f"https://youtube.com/shorts/{v['id']}", "title": sn["title"],
            "channel": sn["channelTitle"], "channel_id": sn["channelId"], "published": sn["publishedAt"][:10],
            "sec": sec, "views": views, "likes": int(st.get("likeCount", 0)),
            "comments": int(st.get("commentCount", 0)), "subs": sub, "views_per_day": round(views / age),
            "perf": round(views / sub, 2) if sub else None,            # 성과도: 구독자 대비 조회수
            "contrib": round(views / avg, 2) if avg else None,         # 기여도: 채널 평균 대비 조회수
            "desc": sn.get("description", "")[:200], "tags": sn.get("tags", [])[:10],
        })
    return rows, channels


def fetch_channels(ch_ids: list[str]) -> dict[str, dict]:
    """채널 지표 (뷰트랩 채널 분석 항목을 공개 API 값으로 근사)."""
    now = datetime.now(timezone.utc)
    out = {}
    for i in range(0, len(ch_ids), 50):
        res = _get("channels", part="snippet,statistics", id=",".join(ch_ids[i:i + 50]))
        for c in res.get("items", []):
            st, sn = c["statistics"], c["snippet"]
            subs = 0 if st.get("hiddenSubscriberCount") else int(st.get("subscriberCount", 0))
            views, count = int(st.get("viewCount", 0)), int(st.get("videoCount", 0))
            created = datetime.fromisoformat(sn["publishedAt"].replace("Z", "+00:00"))
            days = max((now - created).days, 1)
            avg = views / count if count else 0
            out[c["id"]] = {
                "id": c["id"], "name": sn["title"], "url": f"https://youtube.com/channel/{c['id']}",
                "created": sn["publishedAt"][:10], "days": days, "subs": subs, "views": views,
                "videos": count, "avg_views": round(avg),
                "sub_per_view": round(subs / views * 1000, 2) if views else None,   # 조회수대비 구독전환 (1천 뷰당)
                "sub_per_day": round(subs / days, 1),                                # 일평균 구독전환
                "video_perf": round(avg / subs, 2) if subs else None,                # 영상성과: 평균 조회수 ÷ 구독자
                "views_per_day": round(views / days),
            }
    return out


# 뷰트랩식 5단계 등급. 경계값은 경험치이므로 필요하면 조정.
GRADES = {
    "perf":        [0.3, 1, 3, 10],      # 성과도
    "contrib":     [0.3, 0.7, 1.5, 3],   # 기여도
    "sub_per_view": [0.5, 1, 3, 8],      # 1천 뷰당 구독
    "sub_per_day": [5, 30, 150, 800],    # 일평균 구독
    "video_perf":  [0.1, 0.3, 1, 3],     # 영상성과
}
LABELS = ["Worst", "Bad", "Normal", "Good", "Great"]


def grade(metric: str, value: float | None) -> str:
    if value is None:
        return "-"
    return LABELS[sum(value >= b for b in GRADES[metric])]


# ---------- Claude 분류 ----------

class Tag(BaseModel):
    id: str
    format: str
    hook_type: str
    topic: str


class Tagging(BaseModel):
    videos: list[Tag]


class Insight(BaseModel):
    summary: str
    winning_patterns: list[str]
    hook_templates: list[str]
    guide: str


def classify(rows: list[dict], model: str) -> dict[str, Tag]:
    client = anthropic.Anthropic()
    tags: dict[str, Tag] = {}
    for i in range(0, len(rows), 60):
        batch = rows[i:i + 60]
        lines = "\n".join(
            json.dumps({"id": r["id"], "title": r["title"], "desc": r["desc"][:120], "tags": r["tags"]}, ensure_ascii=False)
            for r in batch
        )
        resp = client.messages.parse(
            model=model, max_tokens=16000, thinking={"type": "adaptive"}, output_config={"effort": "low"},
            system=(
                "유튜브 쇼츠를 제목·설명·태그만 보고 분류한다.\n"
                f"format은 다음 중 하나: {', '.join(FORMATS)}\n"
                "hook_type은 제목이 클릭을 부르는 방식 (질문형, 충격 사실, 숫자·순위, 반전 예고, 공감, 경고, 비밀 공개 등) 중 짧게.\n"
                "topic은 소재를 2~4단어로."
            ),
            messages=[{"role": "user", "content": f"모든 영상을 분류해줘.\n{lines}"}],
            output_format=Tagging,
        )
        if resp.parsed_output:
            tags.update({t.id: t for t in resp.parsed_output.videos})
    return tags


def summarize(stats: list[dict], top: list[dict], keyword: str, model: str) -> Insight:
    client = anthropic.Anthropic()
    resp = client.messages.parse(
        model=model, max_tokens=16000, thinking={"type": "adaptive"}, output_config={"effort": "high"},
        system=(
            "너는 쇼츠 채널 전략가다. 포맷별 통계와 성과 상위 영상을 보고 결론을 낸다.\n"
            "- '많이 올라오는 포맷'(공급)과 '잘 되는 포맷'(성과도·일평균 조회수)을 구분해서 말한다. "
            "공급은 적은데 성과가 높은 포맷이 기회다.\n"
            "- hook_templates: 상위 영상 제목에서 뽑은 재사용 가능한 첫 문장 틀 (예: '___인데 어떻게 ___할까요?').\n"
            "- guide: 롱폼 영상에서 쇼츠 구간을 고를 때 쓸 선별 기준. 5줄 이내 한국어 지시문."
        ),
        messages=[{
            "role": "user",
            "content": f"키워드: {keyword}\n\n<format_stats>\n{json.dumps(stats, ensure_ascii=False)}\n</format_stats>\n"
                       f"<top_videos>\n{json.dumps(top, ensure_ascii=False)}\n</top_videos>",
        }],
        output_format=Insight,
    )
    if resp.parsed_output is None:
        raise RuntimeError("요약 생성 실패")
    return resp.parsed_output


# ---------- 집계·리포트 ----------

def aggregate(rows: list[dict]) -> list[dict]:
    groups: dict[str, list[dict]] = {}
    for r in rows:
        groups.setdefault(r.get("format", "기타"), []).append(r)
    total = len(rows)
    stats = []
    for fmt, rs in groups.items():
        perfs = [r["perf"] for r in rs if r["perf"] is not None]
        stats.append({
            "format": fmt, "count": len(rs), "share": round(len(rs) / total * 100, 1),
            "median_views": int(statistics.median(r["views"] for r in rs)),
            "median_views_per_day": int(statistics.median(r["views_per_day"] for r in rs)),
            "median_perf": round(statistics.median(perfs), 2) if perfs else None,
            "great_ratio": round(sum(p >= 10 for p in perfs) / len(perfs) * 100, 1) if perfs else None,
            "median_sec": int(statistics.median(r["sec"] for r in rs)),
        })
    return sorted(stats, key=lambda s: -s["count"])


def fmt_num(n) -> str:
    if n is None:
        return "-"
    return f"{n / 10000:.1f}만" if n >= 10000 else f"{n:,}"


def write_report(out: Path, keyword: str, days: int, rows: list[dict], channels: dict, stats: list[dict], ins: Insight) -> None:
    L = [f"# 쇼츠 트렌드 리포트: {keyword}", "",
         f"최근 {days}일 · 쇼츠 {len(rows)}개 · 채널 {len(channels)}개", "",
         "- 성과도 = 조회수 ÷ 구독자 수 (채널 규모에 비해 얼마나 터졌나)",
         "- 기여도 = 조회수 ÷ 그 채널 평균 조회수 (그 채널 안에서 얼마나 튀었나)",
         "- 등급 Worst/Bad/Normal/Good/Great 경계값은 trends.GRADES 에서 조정", "",
         "## 결론", "", ins.summary, "", "## 포맷별 통계 (많이 올라오는 순)", "",
         "| 포맷 | 개수 | 비중 | 조회수 중앙값 | 일평균 조회 | 성과도 중앙값 | Great 비율 | 길이 |",
         "|---|---|---|---|---|---|---|---|"]
    for s in stats:
        L.append(f"| {s['format']} | {s['count']} | {s['share']}% | {fmt_num(s['median_views'])} | "
                 f"{fmt_num(s['median_views_per_day'])} | {s['median_perf'] if s['median_perf'] is not None else '-'} | "
                 f"{s['great_ratio'] if s['great_ratio'] is not None else '-'}% | {s['median_sec']}초 |")
    L += ["", "## 잘 되는 패턴", ""] + [f"- {p}" for p in ins.winning_patterns]
    L += ["", "## 훅 템플릿", ""] + [f"- {h}" for h in ins.hook_templates]
    L += ["", "## 쇼츠 선별 기준 (make --trend 에 사용)", "", "```", ins.guide, "```", "",
          "## 성과도 상위 30 영상", "",
          "| 성과도 | 기여도 | 조회수 | 구독자 | 포맷 | 훅 | 제목 |", "|---|---|---|---|---|---|---|"]
    for r in sorted(rows, key=lambda r: -(r["perf"] or 0))[:30]:
        title = r["title"].replace("|", "/")
        L.append(f"| {r['perf']} {grade('perf', r['perf'])} | {r.get('contrib')} {grade('contrib', r.get('contrib'))} | "
                 f"{fmt_num(r['views'])} | {fmt_num(r['subs'])} | {r.get('format', '')} | {r.get('hook_type', '')} | "
                 f"[{title}]({r['url']}) |")
    L += ["", "## 핫 채널 (개설 1년 이내, 일평균 구독 순)", "",
          "| 채널 | 개설일 | 구독자 | 일평균 구독전환 | 조회수대비 구독전환 | 영상성과 | 총 영상 |", "|---|---|---|---|---|---|---|"]
    young = sorted((c for c in channels.values() if c["days"] <= 365), key=lambda c: -c["sub_per_day"])[:20]
    for c in young:
        L.append(f"| [{c['name'].replace('|', '/')}]({c['url']}) | {c['created']} | {fmt_num(c['subs'])} | "
                 f"{c['sub_per_day']} {grade('sub_per_day', c['sub_per_day'])} | "
                 f"{c['sub_per_view']} {grade('sub_per_view', c['sub_per_view'])} | "
                 f"{c['video_perf']} {grade('video_perf', c['video_perf'])} | {c['videos']} |")
    out.write_text("\n".join(L) + "\n", encoding="utf-8")


def analyze(keyword: str, out_dir: Path, days: int, limit: int, region: str, lang: str, model: str) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    raw, raw_ch = out_dir / "videos.json", out_dir / "channels.json"
    if raw.exists() and raw_ch.exists():
        rows = json.loads(raw.read_text(encoding="utf-8"))
        channels = json.loads(raw_ch.read_text(encoding="utf-8"))
    else:
        print(f"쇼츠 수집 중: '{keyword}' 최근 {days}일...")
        rows, channels = collect(keyword, days, limit, region, lang)
        raw.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
        raw_ch.write_text(json.dumps(channels, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  쇼츠 {len(rows)}개, 채널 {len(channels)}개")
    if not rows:
        raise SystemExit("수집된 쇼츠가 없습니다. 키워드나 기간을 바꿔 보세요.")

    if "format" not in rows[0]:
        print("포맷 분류 중 (Claude)...")
        tags = classify(rows, model)
        for r in rows:
            t = tags.get(r["id"])
            r["format"], r["hook_type"], r["topic"] = (t.format, t.hook_type, t.topic) if t else ("기타", "", "")
        raw.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")

    stats = aggregate(rows)
    top = [
        {k: r.get(k) for k in ("title", "format", "hook_type", "topic", "views", "perf", "contrib", "views_per_day", "sec")}
        for r in sorted(rows, key=lambda r: -(r["perf"] or 0))[:40]
    ]
    print("인사이트 정리 중 (Claude)...")
    ins = summarize(stats, top, keyword, model)

    with (out_dir / "videos.csv").open("w", newline="", encoding="utf-8-sig") as f:
        cols = ["perf", "contrib", "views", "views_per_day", "subs", "format", "hook_type", "topic", "sec",
                "published", "channel", "title", "url"]
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(sorted(rows, key=lambda r: -(r["perf"] or 0)))
    with (out_dir / "channels.csv").open("w", newline="", encoding="utf-8-sig") as f:
        cols = ["name", "created", "subs", "videos", "avg_views", "sub_per_day", "sub_per_view", "video_perf", "url"]
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(sorted(channels.values(), key=lambda c: -c["sub_per_day"]))
    (out_dir / "guide.txt").write_text(ins.guide, encoding="utf-8")
    report = out_dir / "report.md"
    write_report(report, keyword, days, rows, channels, stats, ins)
    return report

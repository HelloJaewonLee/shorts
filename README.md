# shorts — 쇼츠 트렌드 분석 + 롱폼→쇼츠 자동 제작

두 단계로 동작합니다.

1. **trends**: 키워드로 최근 유튜브 쇼츠를 모아 **어떤 포맷이 많이 올라오고, 어떤 포맷이 잘 되는지** 분석합니다. 지표는 뷰트랩 방식을 따릅니다.
2. **make**: 롱폼 영상을 넣으면 1단계 분석 결과를 기준으로 쇼츠 구간을 골라 **9:16 쇼츠로 편집**합니다. 편집 방식은 참고 영상(`analysis.md`)의 설정을 따릅니다: 1.3배속, 무음 제거, 굵은 자막, 상단 제목.

```
키워드 ──► trends ──► report.md / videos.csv / channels.csv / guide.txt
                                                           │ (선별 기준)
롱폼 영상 ──► 전사(whisper) ──► 구간 선택(Claude) ──► 편집(ffmpeg) ──► jobs/<이름>/out/clip_XX.mp4
                                                           ▲
                         revise "목소리 빠르게, 제목 굵게" ──┘ (설정만 바꾸고 다시 렌더링)
```

## 설치

```bash
pip install -r requirements.txt
export YOUTUBE_API_KEY=...       # trends / viral (Google Cloud → YouTube Data API v3 사용 설정 → API 키)
```

**Claude 호출 방식** (`config/default.yaml`의 `llm.backend`, 또는 환경변수 `SHORTS_LLM`)
- `claude-code` (기본, Claude Code가 설치돼 있으면 자동 선택): `claude -p`로 호출합니다. **Pro/Max 구독 사용량 안에서** 돌아가고 API 키가 필요 없습니다. 먼저 터미널에서 `claude`로 한 번 로그인해 두세요.
- `api`: Anthropic API를 씁니다. `ANTHROPIC_API_KEY`가 필요하고, 구독과 별도로 사용량만큼 요금이 나옵니다.

ffmpeg는 시스템에 설치된 것을 쓰고, 없으면 `imageio-ffmpeg` 번들을 씁니다. 한글 폰트는 `assets/fonts/`에 Pretendard 같은 `.ttf`/`.otf`를 넣고 `config/default.yaml`의 `font`에 이름을 적으면 됩니다.

## 사용법

```bash
# 1) 트렌드 분석: 최근 30일, 200개
python -m shorts trends "재테크" --days 30 --limit 200
#   → trends/재테크/report.md  (포맷별 개수·성과, 성과도 상위 영상, 핫 채널, 훅 템플릿)

# 2) 롱폼 → 쇼츠 5개 (1단계 결과를 선별 기준으로)
python -m shorts make ~/Videos/podcast_ep12.mp4 --name ep12 --trend "재테크" --count 5
#   → jobs/ep12/out/clip_01.mp4 ...

# 고른 구간 보기 / 말로 수정 / 다시 렌더링
python -m shorts list ep12
python -m shorts revise ep12 "자막 좀 더 크게, 강조색 빨간색으로"
python -m shorts revise ep12 "clip_02 제목을 '월 1억 버는 사람들의 공통점'으로" --clip clip_02
python -m shorts render ep12
```

## 터진 쇼츠·채널 분석 (`viral`)

```bash
# 키워드로 터진 쇼츠와 급성장 채널 찾기 (기본: 일본, 최근 30일)
python -m shorts viral discover "猫 おもしろ" --region JP --lang ja --top 8

# 채널 하나 깊게: 채널 평균 대비 터진 영상, 업로드 주기·시간대(JST), 길이, 제목 패턴
python -m shorts viral channel @채널핸들 --top 8

# 직접 고른 쇼츠 분석
python -m shorts viral video https://youtube.com/shorts/xxxx https://youtube.com/shorts/yyyy
```

영상마다 모으는 자료는 메타데이터, 자막(대사), 가장 많이 다시 본 구간, 첫 0~3초와 중간·끝 화면 캡처, 컷 전환 수입니다. 이 자료로 Claude가 훅, 구성, 자막 스타일, 편집 속도, 터진 이유, 재사용 틀, 소스 위험을 분해합니다. 여러 영상의 공통점은 제작 설정 제안(playbook)으로 묶어 `viral/.../report.md`에 저장합니다.

유튜브가 봇 확인으로 다운로드를 막으면 저해상도 스토리보드로 대신 분석합니다. 이 경우 화면 글씨는 읽기 어렵습니다. 로그인된 브라우저 쿠키를 쓰면 대부분 해결됩니다.
```bash
export YTDLP_BROWSER=chrome        # 또는 export YTDLP_COOKIES=~/cookies.txt
```

## 지표 (뷰트랩 항목 대응)

| 지표 | 계산 | 의미 |
|---|---|---|
| 성과도 | 조회수 ÷ 구독자 | 채널 규모에 비해 얼마나 터졌나 (알고리즘 픽업 신호) |
| 기여도 | 조회수 ÷ 채널 평균 조회수 | 그 채널 안에서 얼마나 튀었나 |
| 조회수대비 구독전환 | 구독자 ÷ 누적 조회수 (1천 뷰당) | 시청이 구독으로 이어지는 정도 |
| 일평균 구독전환 | 구독자 ÷ 채널 나이(일) | 채널 성장 속도 |
| 영상성과 | 채널 평균 조회수 ÷ 구독자 | 채널 전체 영상의 평균 성과 |

등급(Worst/Bad/Normal/Good/Great) 경계값은 `shorts/trends.py`의 `GRADES`에 있습니다. 뷰트랩의 정확한 공식은 공개되어 있지 않아 공개 API 값으로 근사했습니다. 노출확률과 성장속도는 시계열 데이터가 필요해서 아직 넣지 않았습니다.

**API 사용량:** 검색 1회(50개)에 100유닛이 들고, 하루 무료 할당량은 10,000유닛입니다. `--limit 200`이면 한 번에 약 400유닛을 씁니다. 결과는 `trends/<키워드>/`에 캐시되며, 같은 키워드를 다시 수집하려면 그 폴더를 지우면 됩니다.

## 편집 설정 (`config/default.yaml`)

| 설정 | 기본값 | 설명 |
|---|---|---|
| `edit.speed` | 1.3 | 배속 |
| `edit.remove_silence`, `max_gap` | true, 0.35초 | 말 사이 공백이 0.35초보다 길면 잘라냄 (단어 타임스탬프 기준) |
| `edit.reframe` | blur | `blur`: 원본 비율 유지 + 흐린 배경 / `crop`: 가운데를 9:16으로 자름 |
| `title.*` | 상단 박스, 굵게 | Claude가 붙인 궁금증 유발 제목 |
| `caption.*` | 굵은 흰 글씨, 말하는 단어 노란색 | 단어 단위 하이라이트 자막 |
| `audio.bgm` | 없음 | 넣으면 말할 때 BGM 볼륨이 자동으로 줄어듦 |

작업 폴더의 `jobs/<이름>/config.yaml`이 기본값보다 우선합니다. `revise`는 이 파일을 고칩니다.

## 주의

- 롱폼 원본은 **본인 영상이나 사용 허락을 받은 영상**만 쓰세요. 남의 영상을 잘라 올리면 저작권 신고와 재사용 콘텐츠 정책에 걸립니다.
- 업로드 자동화(YouTube Data API `videos.insert`)는 아직 없습니다. 만들어진 mp4를 검수한 뒤 직접 올리세요.

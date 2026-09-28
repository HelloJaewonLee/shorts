# YouTube 쇼츠 추천 시스템과 배포되는 쇼츠 제작법 (2025–2026)

> 조사 기준일: 2026-09-28. 참고: 이번 조사 환경에서는 youtube 공식 블로그, support.google.com, techcrunch, tubefilter, vidiq, opus.pro 본문 fetch가 네트워크에서 차단됐다. 그래서 아래 인용은 대부분 검색 결과 스니펫과 2차 요약에 기대고 있다. 공식 문서 원문 대조는 하지 못했으니, 중요한 규칙은 원문 URL을 직접 열어 재확인하길 권한다.
> 표기: [공식]=YouTube/TeamYouTube/Creator Liaison 발언, [데이터]=표본이 있는 분석, [의견]=크리에이터·툴사 주장, [미검증]=출처가 불명확한 2차 블로그 주장.

## 1. 쇼츠 랭킹 신호에 대한 YouTube 공식 입장과 제도 변화

### Takeaway
공식적으로 확인되는 핵심 신호는 두 가지다. 피드에 노출됐을 때 멈추고 보느냐(viewed vs swiped away)와 시청 뒤 만족도(좋아요·싫어요·설문)다. 평가는 채널 단위가 아니라 영상과 주제 단위로 이뤄진다. 2024년 10월 15일부터 쇼츠는 최대 3분까지 가능해졌다. 2025년 3월 31일부터는 조회수가 재생이나 반복 재생이 시작될 때마다 집계되고, 수익과 YPP 자격은 여전히 '참여 조회수(engaged views)' 기준이다.

### Cited Findings
- [공식/2차 보도] YouTube Growth & Discovery 시니어 디렉터 Todd Beaupré는 알고리즘의 큰 축으로 '만족도(satisfaction)'를 든다. 만족도에는 좋아요, 싫어요, 시청 후 설문이 들어간다. 그래서 시청시간이 많아도 시청자가 즐기지 않았다면 도달이 줄 수 있다. — [Sprout Social](https://sproutsocial.com/insights/youtube-algorithm/), [Metricool](https://metricool.com/youtube-shorts-algorithm/), [OutlierKit](https://outlierkit.com/resources/youtube-viewer-satisfaction-algorithm-2026/)
- [의견/2차] '조회 vs 스와이프(VvSA)'는 쇼츠가 통과해야 하는 첫 관문으로 흔히 설명된다. 피드에 떴을 때 넘기지 않고 본 비율이다. — [ReelRise](https://reelrise.app/guide/viewed-vs-swiped-away-the-only-youtube-shorts-metric-that-matters/), [vidIQ](https://vidiq.com/blog/post/youtube-shorts-algorithm/)
- [데이터] Paddy Galloway와 Chris Gileta는 2023년 4월 쇼츠 조회 33억 회를 분석했다. VvSA가 60% 미만이면 좋은 성과가 드물었고, 최상위 쇼츠는 대체로 70–90%였다. 다만 VvSA가 높다고 성공이 보장되지는 않는다(롱폼 CTR과 같은 성격). — [Paddy Galloway X 스레드](https://x.com/PaddyG96/status/1646898368495382528?lang=en), [스레드 원글](https://x.com/PaddyG96/status/1646898356419981315?lang=en). ※ 2023년 데이터이며 2025년 조회수 집계 변경 이전이다. 방향성 참고용으로만 쓴다.
- [공식] Creator Liaison Rene Ritchie: "채널이나 크리에이터를 보지 않고 영상과 주제를 본다." 쇼츠 하나가 부진해도 다음 롱폼 배포에 영향이 없다는 취지다. — [Tubefilter(Rene Ritchie Shorts FAQ)](https://www.tubefilter.com/2024/08/26/rene-ritchie-shorts-creator-faqs/), [CreatiCalc 정리](https://creaticalc.com/blog/do-youtube-shorts-hurt-long-form)
- [공식 문서 인용(2차)] YouTube 추천 문서에는 "쇼츠·VOD·라이브 같은 새 포맷을 시도해도 알고리즘이 본질적으로 혼동하거나 채널 전체 성과에 악영향을 주지 않는다"는 문장이 있다고 한다. — [Panda Video](https://www.pandavideo.com/blog/shorts-and-long-form-videos-same-channel)
- [공식] 2024-10-15부터 정사각형·세로형 영상은 최대 3분까지 쇼츠로 올릴 수 있다. 그 이전 업로드분에는 소급 적용되지 않는다. YouTube는 이후 몇 달간 긴 쇼츠의 추천을 개선하겠다고 밝혔다. 같은 발표에 'Show fewer Shorts' 기능과 Veo 통합도 포함됐다. — [YouTube Blog "Tall updates coming to Shorts"](https://blog.youtube/news-and-events/tall-updates-coming-to-shorts/), [9to5Google](https://9to5google.com/2024/10/03/youtube-shorts-3-minutes/), [Variety](https://variety.com/2024/digital/news/youtube-shorts-maximum-video-length-three-minutes-1236166349/), [YouTube Help 15424877](https://support.google.com/youtube/answer/15424877?hl=en)
- [공식] 2025-03-31부터 쇼츠 '조회수'는 재생 또는 재재생이 시작될 때마다 집계되고 최소 시청 시간이 없다. TikTok, Reels와 기준을 맞춘 것이다. 기존 방식의 지표는 '참여 조회수(engaged views)'라는 이름으로 남았다. 쇼츠 수익 배분과 YPP 자격은 계속 참여 조회수를 기준으로 한다. Studio > 분석 > 고급 모드에서 두 지표를 비교할 수 있다. — [TechCrunch](https://techcrunch.com/2025/03/26/youtube-is-changing-how-youtube-shorts-views-are-counted), [PPC Land](https://ppc.land/youtube-changes-how-shorts-views-are-counted-from-march-31/), [TubeBuddy](https://www.tubebuddy.com/blog/youtube-shorts-view-count-update-what-creators-need-to-know-about-the-new-metrics/), [Rene Ritchie LinkedIn](https://www.linkedin.com/posts/reneritchie_shorts-creators-youtube-is-making-an-update-activity-7310736092759052288-6xcO)
- [공식] 1–3분 쇼츠에 활성 Content ID 클레임이 있으면 정책과 무관하게 전 세계에서 차단됐다(TeamYouTube). 검색 결과 요약에 따르면 2026-09-24부터는 1–3분 신규 쇼츠에 클레임이 있어도 자동 차단하지 않고 재생 가능하게 바뀌었다고 한다. 단, 이 변경은 Help 원문으로 확인하지 못했다. — [TeamYouTube X](https://x.com/TeamYouTube/status/2000198352625910075), [YouTube Help 15424877](https://support.google.com/youtube/answer/15424877?hl=en)
- [공식] 2025-07-15에 '반복적 콘텐츠(repetitious)' 수익화 정책 이름이 '진정성 없는 콘텐츠(inauthentic)'로 바뀌었다. 대량 생산되거나 반복적인 콘텐츠가 명시적으로 포함됐다. 클립·컴필레이션·리액션을 다루는 '재사용 콘텐츠(reused content)' 정책 자체는 바뀌지 않았고, 의미 있는 변형이 있으면 수익화할 수 있다. — [Social Media Today](https://www.socialmediatoday.com/news/youtube-clarifies-monetization-update-inauthentic-repeated-content/752892/), [YouTube 채널 수익 창출 정책](https://support.google.com/youtube/answer/1311392?hl=en)
- [미검증] "2025년 말 쇼츠와 롱폼 추천 엔진이 완전히 분리됐다", "30초 미만은 약 65%, 30–60초는 약 50% 유지율이 확산 임계값", "첫 30–60분 안에 임계값을 넘지 못하면 푸시가 멈춘다", "2026년 초 검색에 쇼츠 필터 도입" 같은 주장이 떠돈다. 모두 1차 공식 출처를 찾지 못했다. — [OutlierKit](https://outlierkit.com/resources/youtube-algorithm-updates/), [Miraflow](https://miraflow.ai/blog/youtube-shorts-algorithm-update-january-2026)
- [데이터] Metricool 2026 YouTube 연구(71,177개 계정, 영상 799,718개)의 쇼츠 결과: 조회수 +127%, 평균 시청 시간 약 67% 감소해 쇼츠 1개당 약 16초(전년 대비 32초 짧음). 쇼츠 피드가 YouTube 조회의 61%를 차지했다. 광고 노출, 수익 재생, 추정 광고 수익은 50% 넘게 줄었다. 상호작용의 83%가 첫 10일 안에 발생했다. — [Metricool 보도자료](https://metricool.com/press-release-youtube-study-2026/), [Tubefilter](https://www.tubefilter.com/2026/08/03/youtube-shorts-long-form-study-metricool/)

### Inferences
- 조회수 +127%와 평균 시청 시간 급감은 상당 부분 2025-03 집계 방식 변경(스와이프 직전 재생도 조회로 셈)에서 생긴 착시일 가능성이 크다. 따라서 프로그램 성과 평가는 '조회수'가 아니라 참여 조회수, VvSA, 평균 시청 비율로 해야 한다.
- 채널 단위 페널티가 없다는 공식 입장을 보면, 실험적으로 여러 클립을 올려도 채널 전체가 망가질 위험은 낮다. 다만 부진한 쇼츠가 좋은 쇼츠에 줄 노출 기회를 빼앗을 수는 있다.
- 롱폼 클립을 자동으로 잘라 올리는 프로그램은 '재사용·진정성 없는 콘텐츠' 정책 위험이 가장 크다. 자막, 편집, 구조 재배열, 해설 같은 변형 요소를 반드시 넣어야 하고, 같은 템플릿을 기계적으로 반복하지 않게 해야 한다. 특히 타인 원본을 쓴다면 더 그렇다.

### Gaps
- Creator Insider나 Todd Beaupré의 쇼츠 전용 최신(2025–2026) 발언 원문을 fetch로 확인하지 못했다(egress 차단).
- 2026-09-24 Content ID 정책 변경은 검색 요약 한 곳에서만 봤다. Help 원문 확인이 필요하다.
- '추천 엔진 분리', '유지율 임계값' 수치는 공식 근거가 없다.

## 2. 첫 1–3초 훅 기법 (롱폼에서 잘라낸 클립 기준)

### Takeaway
시청자는 첫 1–2초 안에 계속 볼지 넘길지를 정한다. 훅은 곧바로 주제로 들어가야 하고, 호기심 갭이나 열린 고리를 만들며, 화면 텍스트로도 내용을 전해야 한다. 롱폼 클립이라면 인사나 맥락 설명을 잘라내고 결론 직전, 논쟁적 주장, 감정 반응 지점부터 시작하는 것이 일관된 조언이다.

### Cited Findings
- [의견] Jenny Hoyos는 첫 1초에 사로잡지 못하면 끝이라고 본다. 좋은 훅은 짧고 시각적이며 몇 초 안에 이야기의 요지를 전한다. 핵심은 '호기심 갭'과 '열린 고리(open loop)'다(낚시 비유: 먼저 걸고, 나머지로 끌어올린다). — [vidIQ: How Jenny Hoyos Gets 10M Views](https://vidiq.com/blog/post/how-jenny-hoyos-gets-10m-views-per-youtube-short/), [KDCC 블로그](https://blog.kdcc.social/make-anything-go-viral-how-to-hook-and-reel-in-your-viewer/)
- [의견] Hoyos는 "banned", "free", "one dollar", "secret", "cheap" 같은 파워 워드를 쓰고, 목표 유지율을 90% 이상으로 잡는다. — [vidIQ 18 Viral Hooks](https://vidiq.com/blog/post/viral-video-hooks-youtube-shorts/), [Medium 정리](https://medium.com/@10xquality/600m-viral-youtube-shorts-views-in-only-1-year-jenny-cracked-the-code-bcb43708f298)
- [데이터? 출처 불명확] "첫 2초에 즉각적인 훅이 있는 쇼츠는 느리게 시작하는 쇼츠보다 시청자를 19% 더 유지한다"는 수치가 vidIQ 글 요약에 나온다. 원 데이터 출처는 확인하지 못했다. — [vidIQ 18 Viral Hooks](https://vidiq.com/blog/post/viral-video-hooks-youtube-shorts/)
- [데이터] Galloway 연구의 결론은 "첫 1초를 강렬하게 만들라"였다(VvSA 60% 이상 유지). — [BAM 요약](https://nowbam.com/decoding-the-youtube-shorts-algorithm/), [Paddy Galloway X](https://x.com/PaddyG96/status/1646898368495382528?lang=en)
- [의견/툴사] Klap이 꼽는 바이럴 예측 패턴 4가지는 다음과 같다. ① 첫 1–2초에 호기심이나 놀라움을 주는 훅, ② 반직관적·역발상 주장(논쟁 유발), ③ 실시간으로 포착된 감정 반응(웃음·분노·놀람), ④ 마지막 3초의 보상(payoff). — [Klap Viral Clip Generator](https://klap.app/tools/viral-clip-generator)
- [의견] OpusClip의 'Hook' 기준은 도입부가 주의를 끄는지, 그리고 영상의 주제와 직접 관련되는지다. — [OpusClip Help: Virality Score](https://help.opus.pro/docs/article/virality-score)

### Inferences
- 자동 편집 규칙 후보(추론이며 검증된 규칙은 아님):
  1. 클립 시작점을 문장 중간이 아닌 '주장이나 질문 문장의 시작'에 맞춘다. 인사, "자, 오늘은", 맥락 설명은 제거한다.
  2. 0–1초 안에 화면 텍스트 훅(질문형이나 결과 선공개형, 10단어 이내)을 표시한다.
  3. 결과나 반전 장면을 맨 앞에 짧게 보여준 뒤 되감는 '콜드오픈' 구조를 선택지로 둔다.
  4. 첫 프레임은 정지 화면이나 검은 화면이 아니라 움직임이나 인물 표정이 있는 프레임이어야 한다.
- 훅은 반드시 본문 내용과 일치해야 한다. 과장 훅으로 VvSA를 올려도 만족도(싫어요, 설문)에서 깎이면 역효과가 난다는 점은 Beaupré의 만족도 발언과 맞아떨어진다.

### Gaps
- 훅 유형별(질문, 대담한 주장, 패턴 인터럽트) A/B 효과를 비교한 공개 대규모 데이터는 찾지 못했다. 대부분 크리에이터 의견이다.

## 3. 최적 길이, 완주율 대 시청시간, 루프

### Takeaway
출처마다 권장 범위는 조금씩 다르지만 중심은 약 20–45초다. 순수 유지율을 노리면 15–30초, 설명형이나 튜토리얼은 30–60초가 권장된다. 3분까지 올릴 수 있어도 60초가 넘으면 유지율이 떨어지는 경향이 보고된다. 2025-03 이후에는 반복 재생마다 조회수가 올라가므로 루프 구조의 가치가 커졌다.

### Cited Findings
- [데이터] Galloway 연구에서 쇼츠 길이 분포는 대부분 20–40초에 몰려 있었다(2023년). — [Paddy Galloway X](https://twitter.com/PaddyG96/status/1646898359808974851)
- [2차 정리] 여러 분석이 30–60초를 이상적인 길이로 제시한다(Inflow Network, Galloway·Gileta 인용). 유지율 극대화에는 15–30초, 2025–2026 분석들은 20–45초를 강세 구간으로 본다. 코미디와 트렌드 오디오는 15–25초, 튜토리얼과 제품 데모는 30–60초가 권장된다. — [Riverside](https://riverside.com/blog/how-long-can-youtube-shorts-be), [OpusClip 블로그](https://www.opus.pro/blog/ideal-youtube-shorts-length-format-retention), [Piktochart](https://piktochart.com/blog/how-long-youtube-shorts/)
- [2차/미검증] "유지율은 80% 이상이 경험칙", "60초 이하가 유지율이 더 높다", "20초 미만 쇼츠는 42%가 끝까지 본다" 같은 수치가 있다. 원 데이터 출처는 확인하지 못했다. — [Shortimize](https://www.shortimize.com/blog/youtube-shorts-retention-rate), [Joyspace](https://joyspace.ai/looping-hack-trick-algorithm-double-views)
- [데이터] Metricool 2026: 쇼츠 1개당 평균 시청 시간 약 16초. — [Metricool](https://metricool.com/press-release-youtube-study-2026/)
- [공식+해석] 2025-03-31부터 반복 재생도 조회로 집계되므로 매끄러운 루프는 조회수를 직접 늘린다. 반복 재생은 시청시간과 유지율에도 쌓인다고 설명된다. — [PPC Land](https://ppc.land/youtube-changes-how-shorts-views-are-counted-from-march-31/), [Neal Schaffer](https://nealschaffer.com/youtube-shorts-looping/)
- [의견] 루프 기법은 두 가지다. ① 시각적 루프: 마지막 프레임을 첫 프레임과 거의 같게 맞춘다(구도, 움직임 방향, 오디오 비트). ② 서사적 루프: 마지막 문장이 첫 문장으로 자연스럽게 이어지거나 첫 문장의 의미를 다시 해석하게 만든다. — [Virvid](https://virvid.ai/blog/looping-structure-shorts-retention-2026), [Digital Blacksmiths](https://digitalblacksmiths.io/youtube-shorts-algorithm-secret-loopable-videos-increase-watch-time/)
- [의견] Hoyos는 루프하고 싶은 콘텐츠를 만드는 것을 유지율 전략의 핵심으로 본다. — [Medium 정리](https://medium.com/@10xquality/600m-viral-youtube-shorts-views-in-only-1-year-jenny-cracked-the-code-bcb43708f298)

### Inferences
- 트레이드오프: 짧을수록 완주율과 반복 재생률은 오르지만 1회 시청시간은 줄어든다. 길수록 반대다. 만족도가 핵심이라는 공식 입장을 고려하면 '내용이 완결되는 가장 짧은 길이'가 안전한 기본값이다.
- 자동 편집 규칙 후보: 기본 목표 20–45초, 하드 상한 약 60초. 60초를 넘기는 것은 스토리가 끊기지 않을 때만 예외로 허용한다. 60초 초과 클립에 저작권 음원이나 영상이 섞이면 Content ID 차단 위험이 있다(2026-09 정책 변경 여부는 확인 필요).
- 엔딩: "구독하세요" 같은 아웃트로는 빼고 payoff 직후 바로 끊는다. 가능하면 마지막 문장이나 프레임이 첫 훅으로 이어지게 구성한다.

### Gaps
- vidIQ, TubeBuddy, Social Blade, Dash Hudson이 길이별 성과를 정량 비교한 1차 연구는 찾지 못했다(fetch 차단, 검색 노출 없음). OpusClip 글도 본문 표본 규모를 확인하지 못했다.

## 4. 자막(번인 캡션)

### Takeaway
소셜 피드 영상의 상당수가 무음으로 재생되기 시작한다는 통계가 있고, 번인 자막이 유지율을 높인다는 수치도 여러 2차 출처에 나온다. 하지만 쇼츠에 한정한 1차 통제 연구는 찾지 못했다. 업계 사실상 표준은 단어 단위로 강조되는 애니메이션 자막이다.

### Cited Findings
- [2차/출처 불명확] 번인 자막이 유지율을 15–25% 높인다(쇼츠 맥락, OpusClip 블로그 요약). Instagram Reels에서는 자막이 있으면 약 38% 더 오래 시청하고, 완주율이 약 65% 대 37%였다는 수치가 있다. — [OpusClip 블로그](https://www.opus.pro/blog/ideal-youtube-shorts-length-format-retention), [Shortzly](https://shortzly.com/blog/short-form-video-retention-strategies)
- [2차] 소셜 피드 영상의 80–85%는 처음에 무음으로 시청된다. 공공장소에서는 69%가 무음으로 보고, 혼자 있을 때는 25%다. — [Mile High Title Guy](https://www.milehightitleguy.com/post/what-percentage-of-people-watch-videos-with-the-sound-off-and-how-to-fix-your-captions-so-they-actu), [Kapwing Subtitle Stats](https://www.kapwing.com/resources/subtitle-statistics/)
- [2차/미검증] 단어 단위 동적 자막이 정적 자막보다 평균 시청 시간을 40–80% 늘리고, 상위 쇼트클립의 78.6%가 애니메이션 자막을 쓴다(정적 자막은 1.6%). — [KreateFlo](https://kreateflo.com/blog/why-dynamic-text-animations-outperform-static-subtitles)
- [학술] 소리 없이 자막만으로 시청하면 이해도, 인지 부하, 몰입, 즐거움, 시선 패턴에 영향이 있다는 아이트래킹 혼합연구가 있다. — [PMC 11458047](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11458047/)

### Inferences
- 자동 편집 규칙 후보: 모든 쇼츠에 번인 자막을 기본으로 넣는다. 한 번에 1–4단어를 보여주고 현재 단어를 강조한다. 화면 중앙 하단 1/3 위쪽에 두어 YouTube UI(제목, 버튼)와 겹치지 않게 한다. 고대비 외곽선을 쓴다. 일본 현지화라면 일본어 자막 줄바꿈과 가독성을 따로 조정해야 한다.
- 수치(15–25%, 40–80%)는 방법론이 불명확하므로 보고서에서는 "업계 주장"으로 표기해야 한다.

### Gaps
- YouTube 쇼츠 전용으로 자막 유무를 통제한 1차 실험 데이터는 찾지 못했다.

## 5. 업로드 빈도, 일관성, 롱폼 잠식 문제

### Takeaway
공식 입장은 게시 시간과 빈도가 직접적인 랭킹 요인은 아니고 각 영상이 개별로 평가된다는 것이다. 데이터 연구는 '꾸준히 게시하는 것'이 '안 올리는 것'보다 낫다는 쪽이다. 하루 여러 개를 올려도 채널 페널티를 준다는 공식 근거는 없지만, 연속 업로드는 서로 경쟁한다는 의견이 있다. 쇼츠가 롱폼을 해친다는 주장은 공식적으로 부인됐다.

### Cited Findings
- [공식(2차 인용)] YouTube는 "오후 5시에 올리면 도달이 최대" 같은 규칙이 없다고 말한다. 쇼츠는 게시 시점이 아니라 시청자 반응으로 평가된다. — [Shortimize](https://www.shortimize.com/blog/how-does-youtube-shorts-algorithm-work)
- [데이터] Buffer의 빈도 분석(채널-주 관측치 480만 건): 어떤 주에 게시하지 않은 계정은 자기 기준 성장률보다 일관되게 낮은 성과를 냈다. 어떤 게시든 안 하는 것보다 나았고, 모든 플랫폼에서 그랬다. — [Buffer State of Social Media Engagement 2026](https://buffer.com/resources/state-of-social-media-engagement-2026/)
- [데이터] Buffer의 영상 180만 개 분석: 쇼츠는 금요일, 16시·18시·19시 순으로 중앙값 참여가 높았다(시간대 기준 확인 필요). — [Buffer Best Time to Post on YouTube](https://buffer.com/resources/best-time-to-post-on-youtube/)
- [데이터] vidIQ는 1,000만 채널을 분석해 게시 빈도와 성장의 관계를 봤다(세부 수치는 fetch 차단으로 확인 못함). — [vidIQ How Often to Post](https://vidiq.com/blog/post/How-Often-Post-on-Youtube/)
- [의견] 공격적 성장에는 하루 1–3개, 지속 가능한 운영에는 주 3–7개가 권장된다. 하루 여러 개를 올린다면 4–6시간 간격을 두어 각자 평가 창을 확보하라는 조언도 있다. 쇼츠 피드는 같은 채널 영상을 연달아 보여주지 않으려는 경향이 있다. — [Shortimize](https://www.shortimize.com/blog/how-does-youtube-shorts-algorithm-work), [FlowShorts](https://flowshorts.app/blog/how-many-shorts-per-day), [AIR Media-Tech](https://air.io/en/youtube-hacks/the-death-of-daily-uploads-what-cadence-actually-triggers-algorithm-love-in-2025)
- [공식] Rene Ritchie: 채널이 아니라 영상과 주제 단위로 평가하므로, 쇼츠 부진이 롱폼 배포에 영향을 주지 않는다. 알고리즘은 쇼츠 시청자와 롱폼 시청자가 다를 수 있다는 것을 이해한다. — [Tubefilter](https://www.tubefilter.com/2024/08/26/rene-ritchie-shorts-creator-faqs/), [CreatiCalc](https://creaticalc.com/blog/do-youtube-shorts-hurt-long-form), [ytgrowth](https://ytgrowth.io/blog/shorts-vs-long-form)
- [데이터] Metricool: 상호작용의 83%가 게시 후 첫 10일 안에 발생한다. — [Metricool](https://metricool.com/press-release-youtube-study-2026/)
- [공식] 2025-07 '진정성 없는 콘텐츠' 정책은 대량 생산되거나 반복적인 콘텐츠를 수익화 대상에서 뺀다. — [Social Media Today](https://www.socialmediatoday.com/news/youtube-clarifies-monetization-update-inauthentic-repeated-content/752892/)

### Inferences
- 스케줄링 규칙 후보: 하루 1–3개, 업로드 간 최소 4시간 간격, 매주 빠짐없이 게시. 일본 타깃이라면 Buffer의 시간대 결과를 그대로 쓰지 말고 JST 기준 저녁 시간대를 가설로 잡아 자체 A/B로 검증한다.
- 물량을 늘리는 것 자체보다 '같은 템플릿의 기계적 대량 생산'으로 보이는 것이 수익화 위험이다. 하루 업로드 상한을 두고 클립마다 훅, 자막, 구조에 변주를 주는 편이 안전하다.
- 롱폼 잠식에 대한 공식 답은 "해치지 않는다"다. 다만 '쇼츠 시청자가 롱폼 구독자로 전환되느냐'는 별개 문제이며 이번 조사에서는 데이터를 찾지 못했다.

### Gaps
- 하루 5개 이상 게시할 때 쇼츠당 성과가 떨어지는지 정량 분석한 신뢰할 만한 공개 데이터는 찾지 못했다.
- 쇼츠에서 롱폼으로 가는 전환율 데이터(관련 동영상 링크 효과 등)도 확보하지 못했다.

## 6. AI 클리핑 툴(OpusClip, Vizard, Klap, Descript)의 하이라이트 선정 기준

### Takeaway
공개된 기준을 모으면 공통 축이 보인다. 훅 강도, 흐름과 완결성(만족스러운 결론), 가치와 감정 공명, 트렌드 적합성, 역발상 주장, 감정 반응, 끝부분 payoff다. 툴이 매기는 점수는 순위를 매기는 보조 도구일 뿐 성과를 보장하지 않는다.

### Cited Findings
- [툴사 공식] OpusClip Virality Score는 0–99점이다. 4개 축으로 구성된다. Hook: 도입부가 주의를 끌고 주제와 직접 연결되는가. Flow: 논리적으로 이어지고 만족스러운 결론이 있는가. Value: 가치를 주고 감정적으로 공명하며 개인적 연결을 만드는가. Trend: 현재 트렌드나 관심사에 맞는가. — [OpusClip Help](https://help.opus.pro/docs/article/virality-score)
- [리뷰] OpusClip 점수는 훅 강도, 페이싱, 주제 전환을 반영한다. 사용자들은 고득점 클립이 저득점보다 2–3배 낫다고 말하지만 보장은 아니고 순위용이라는 평가가 있다. — [SendShort 리뷰](https://sendshort.ai/guides/opus-review/), [eesel AI](https://www.eesel.ai/blog/opusclip)
- [툴사 공식] Vizard는 음성, 시각, 페이싱을 분석해 Clip Score를 매긴다. — [Vizard Clip Maker](https://vizard.ai/tools/clip-maker)
- [경쟁사 의견, 편향 주의] Klap은 Vizard 점수가 '장식적'이라고 주장한다. 이 평가는 경쟁사 페이지에서 나온 것이다. — [Klap vs Vizard](https://klap.app/alternatives/vizard-ai)
- [툴사 공식] Klap은 바이럴 쇼트폼 데이터로 학습했고, 훅, payoff, 감정 피크를 잡는다고 밝힌다. 점수는 0–100이다. 예측 패턴 4가지는 첫 1–2초 호기심 훅, 역발상 주장, 실시간 감정 반응, 마지막 3초 payoff다. — [Klap Viral Clip Generator](https://klap.app/tools/viral-clip-generator)
- [벤치마크] 클리핑 툴 9개를 비교한 2026 보고서가 있다(세부 확인 못함). — [Reap 보고서](https://reap.video/reports/state-of-top-ai-video-clipping-tools-2026)
- [학술] 루브릭 기반 VLM으로 쇼트폼 에듀테인먼트의 바이럴성을 평가하는 프레임워크 논문이 있다(arXiv 2512.21402). — [arXiv](https://arxiv.org/pdf/2512.21402)

### Inferences
- 프로그램의 LLM 클립 선정 프롬프트에 쓸 수 있는 채점 루브릭(각 0–10점, 가중치는 예시이며 추론):
  1. 훅(25%): 첫 문장만 들어도 호기심이 생기는가. 질문, 대담한 주장, 숫자, 결과 선공개가 있는가.
  2. 독립성과 완결성(20%): 앞뒤 맥락 없이 이해되는가. 지시어("이거", "아까 말한")로 시작하지 않는가.
  3. Payoff(20%): 끝 3초 안에 결론, 반전, 펀치라인이 있는가. 루프로 이어질 수 있는가.
  4. 감정과 에너지(15%): 웃음, 놀람, 분노, 강한 어조 같은 감정 피크가 있는가.
  5. 역발상과 논쟁성(10%): 통념과 다른 주장이 있는가(댓글 유발).
  6. 가치와 트렌드(10%): 실용 정보를 주는가. 타깃 시장(일본)의 현재 관심사와 맞는가.
- Descript의 하이라이트 선정 기준은 공개 자료를 찾지 못했다.

### Gaps
- Descript의 클립 자동 선정 기준은 공개 문서를 확보하지 못했다.
- 툴 점수와 실제 성과의 상관을 독립적으로 검증한 데이터는 없다. 사용자 체감 수준에 그친다.

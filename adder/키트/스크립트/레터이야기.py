# -*- coding: utf-8 -*-
"""레터이야기 — Narrative 를 읽고 쓰는 절 (L2 · 기획/레터_고도화_제안 2 · 5절, 2026-10-09 결정).

`레터.py` · `레터1부.py` 가 부른다. 숫자는 모두 `맥.수` · `맥.식` 으로 찍는다(장부). 저자 글은 `펴기()` 로 싣는다.

가정 파일의 Narrative 키 (모두 선택 — 없으면 그 절 · 문단이 서지 않고 저자에게 알린다)
  Narrative     {"견본": false,
                 "계기", "질문", "한줄", "값으로", "가격",                    ← 1. 요약을 여는 문단(제안 2.1)
                 "정체성", "구성", "우위", "그러나", "값의원천",               ← 3. Narrative 의 첫 문단들(비우면 「서사」를 싣는다)
                 "값밖": [{"글"} …],                                         ← M10 값에 넣지 않은 Narrative(비우면 가격 성립 입력 · 부록 G 에서 짓는다)
                 "틀림": {"가정": ["616"], "길": "…"},                      ← 가장 먼저 틀릴 가정(비우면 민감도의 첫 손잡이)
                 "다음점검": "…",                                            ← 16. 평가자의 자리
                 "지난평가": {"파일": "지난평가/가정_….json", "날짜", "갈래", "까닭"},   ← M8 지난 평가와의 다리
                 "하강": [{"가정": ["6s9"], "자", "출처", "관측": [{"구간", "연수", "폭"}]}]}   ← 판가의 과거 하강(거친 바퀴 도달연도의 기간 · 깊이)
  서사연결      {"<가정 번호> | WACC": "Narrative 한 줄" | {"문장", "열": [기간 ID …]}}   M1 Link to story(근거 넷째 칸과 다른 자리)
  신호          [{"신호", "자료", "기준일값", "문턱", "가정": [번호 …] (또는 「고칠가정」 글), "갈래": "shift|change|break", "시나리오"}]   M3
  3P            {"시나리오": {"비관|기준|낙관": {"판정": "Possible|Plausible|Probable", "근거", "신호"}},
                 "가정": {"<번호>": {"판정", "근거"}}}                       M5 — 기준은 Probable, 비관 · 낙관은 Plausible 이상
  메타.이해관계 {"보유": false | true, "보유내용", "의뢰"}                   M4
  메타.생애주기 {"단계": 창업기 · 초기 성장기 · 고성장기 · 성숙 성장기 · 성숙기 · 쇠퇴기, "덧표지": [경기순환 · 원자재 · 금융],
                 "위치", "가격변수", "값의원천"}                              M6
저자 글 속 숫자는 장부 키로 쓴다 — 「{키|꼴}」(예: {S:616:기준|지수2} · {R:기준:2.DCF:68|주당} · {÷ R:기준:2.DCF:15:1H26A R:기준:2.DCF:11:1H26A|퍼1}).
가격 변수의 기준(`Narrative.독자.눈금` — 「2025년 평균 = 100」)을 따르는 글은 「{눈금:구분 번호}」(→ 「2025년 평균」) · 「{백 구분 번호 지수키|수0}」
(→ 지수 ÷ 기준 × 100)로 쓴다 — 저자가 기준을 바꾸면 글의 숫자도 따라 바뀐다(2026-10-16).
A · S 키는 꼴을 비워도 된다(가정의 꼴). 손으로 적은 숫자 · 눈금 낱말은 게이트 ⑬(M2)이 장부와 맞댄다.
엔진 값은 손으로 적지 않는다 — 이 가격이 전제한 세계는 「{가:역셀:대상:<대상>:2.DCF:42|퍼1}」 · 「{백 구분 번호 민:표4:대상:<대상>:내재값|수0}」(1.1.19 — 표 Ⅳ 줄은 대상으로 부른다 · `표4키`), 자체검사가 재는
고정비 비중 · 영업레버리지도는 「{가:레버리지:몫|퍼1}」 · 「{가:레버리지:DOL|배}」(2026-10-22 — 손으로 적은 값이 가정을 바꾼 뒤 낡았다).

    python 스크립트/레터이야기.py --검사 가정.json        Narrative 키의 꼴(오류 · 경보)
"""
from __future__ import annotations

import importlib
import copy
import io
import json
import os
import re
import sys

여기 = os.path.dirname(os.path.abspath(__file__))
if 여기 not in sys.path:
    sys.path.insert(0, 여기)

시나리오들 = ("비관", "기준", "낙관")
판정들 = ("Possible", "Plausible", "Probable")
판정순 = {"Possible": 1, "Plausible": 2, "Probable": 3}
독자판정 = {"Possible": "산술적으로만 가능한", "Plausible": "역사적 개연성이 있는", "Probable": "현실적 개연성이 가장 높은"}     # 2026-10-27 — 레터에 찍는 이름을 판정 뜻에 맞게
갈래들 = ("shift", "change", "break")
단계들 = ("창업기", "초기 성장기", "고성장기", "성숙 성장기", "성숙기", "쇠퇴기")
덧표지들 = ("경기순환", "원자재", "금융")
Narrative키 = ("견본", "계기", "질문", "한줄", "값으로", "가격", "정체성", "구성", "우위", "그러나", "값의원천", "값밖", "틀림", "다음점검", "지난평가",
              "독자", "정상수준",                           # R1b — 독자(3분 레터) · 정상수준(정상 수준의 세 방법 · 검증 범위, L7)
              "가설", "계기판", "독법",                     # R1c — 4막 퍼즐 판정 · 계기판 · 2막 독법(레터막)
              "절글", "동인", "자료",                       # 저자 덧글(아래 줄에 이어짐)
              "추정구조",                                   # 2026-10-16 — 본편 추정 구조 절(출발값 · 순서 · 정합 · 변수 — `레터본문.구조절`)
              "하강",                                       # 2026-10-26 — 판가의 과거 하강(거친 바퀴 도달연도의 기간 · 깊이 잣대 — `거친바퀴._하강재료`)
              "절결론",                                     # 2026-10-31 요건판 3 L8 — 절 첫 줄의 결론 한 문장({절 키: 글} — `레터본문.절첫줄넣기`)
              "반대논거", "열정의",                          # 1.1.2 요건판 4 — 시장 쪽 논거(`레터1부.반대논거절`) · 실적 · 추정 열의 정의({항목: 글})
              "회사와쟁점")                                 # 1.1.17 — 3분 레터 「회사와 쟁점」 한 단락(`레터3분.회사와쟁점`)
#                                                             저자 덧글(막 · 깊이 층 절에 문단 · 표) · 가치 동인을 같은 잣대로 견준 문장(3분 · 3막 · 민감도 절) ·
                                                            # 저자가 셈해 둔 수(N:자료:… 로 부른다 — 출처는 그 칸의 「근거」)
신호방향 = ("↑", "↓", "↑↓", "↕", "올림", "오름", "내림", "둘 다")      # R1b(L9) — 켜지면 주당가치가 움직이는 쪽
신호상태 = ("켜짐", "다가감", "꺼짐")
신호상태말 = {"켜짐": "경보", "다가감": "임계치 근접", "꺼짐": "경보 없음"}     # 2026-10-27 — 레터에 찍는 말(「경보 없음 · 모니터링」). 가정 파일 값은 그대로
신호머리 = {"신호": "관측 신호", "문턱": "임계치", "켜지면": "경보 시 가치 방향"}       # 2026-10-27 — 레터에 찍는 표 머리(「관측 신호(Signpost) · 임계치 · 경보 시 가치 방향」)
글키 = ("계기", "질문", "한줄", "값으로", "가격", "정체성", "구성", "우위", "그러나", "값의원천", "다음점검")
_자리표 = re.compile(r"\{([^{}|]+?)(?:\|([^{}|]+))?\}")
# 1.1.4 — 자리표시 뒤 조사(「{금액}을」 · 「{값|지수3}으로」)는 편 값의 받침으로 다시 고른다(저자가 값을 모르고 쓴 조사가 게이트 ⑬ 에 걸리던 자리 —
#   회차 다섯이 원고 문장을 고쳐 피했다). 짝 — 앞이 받침 있음 · 뒤가 받침 없음. 「으로」 · 「로」 는 뒤 글자를 가리지 않고(로서 · 로써),
#   나머지는 뒤가 한글이 아닐 때만(「{x}이상」 같은 낱말은 건드리지 않는다)
_조사짝 = (("이었다", "였다", False), ("이었고", "였고", False), ("이라는", "라는", False), ("이라고", "라고", False), ("이다", "다", False),
         ("이고", "고", False), ("이며", "며", False), ("이면", "면", False), ("으로", "로", True), ("을", "를", False), ("은", "는", False),
         ("이", "가", False), ("과", "와", False))

_온꼴유지 = ("이라는", "이라고", "이다", "이고", "이며", "이면")   # 저자가 온꼴로 쓴 서술격 조사는 그대로 둔다(줄인 꼴은 받침 있는 값 뒤에서 온꼴로 늘린다)


def 조사맞춰펴기(글, 바꿈):
    """`_자리표.sub(바꿈, 글)` 과 같되 자리표시 바로 뒤의 조사를 편 값에 맞춘다."""
    import 레터1부 as P                                    # noqa: PLC0415
    낸, i = [], 0
    for m in _자리표.finditer(글):
        낸.append(글[i:m.start()])
        r = 바꿈(m)
        낸.append(r)
        i = m.end()
        if r == m.group(0):
            continue
        뒤 = 글[i:]
        for 있, 없, 아무 in _조사짝:
            for 옛 in (있, 없):
                if not 뒤.startswith(옛):
                    continue
                다음 = 뒤[len(옛):len(옛) + 1]
                if not 아무 and 다음 and "가" <= 다음 <= "힣":
                    continue
                if 옛 == "가" and 있 == "이" and 다음 and "가" <= 다음 <= "힣":
                    continue
                if 옛 == 있 and 있 in _온꼴유지:            # 1.1.20 — 서술격 조사의 온꼴(「{…|배}이고」)은 받침이 없어도 맞다. 줄이면 「1.63배고」 · 「147%고」
                    break
                새 = P._조(r, 있, 없)
                if 새.startswith(" "):                       # 읽는 소리 미정(WACC) — 「 값」 을 끼운 꼴은 저자 글을 그대로 둔다
                    break
                낸.append(새)
                i += len(옛)
                break
            else:
                continue
            break
    낸.append(글[i:])
    return "".join(낸)
_연산 = ("÷", "×", "−", "합", "괴리", "음", "절대", "최대", "최소", "CAGR")   # CAGR — 「{CAGR 끝키 시작키|퍼1}」(연수는 회계연도 차) · 「{CAGR 끝키 시작키 5.5|퍼1}」
#   1.1.19 — 절대 · 최대 · 최소(`레터.식값` 에 있던 연산 — 원고에서 「{절대 키|꼴}」 이 「모르는 키」 로 빈자리가 됐다) · 연산을 겹쳐 쓴다(`식만들기`)
# 단계마다 「이런 회사의 값은 … 에서 나온다」 의 기본 말(값의원천을 비울 때)
_값의원천기본 = {"창업기": "지금의 실적보다 사업이 서는지와 그 뒤의 성장", "초기 성장기": "매출이 얼마나 빨리 커지는지",
              "고성장기": "성장이 이어지는 기간과 그때의 이익률", "성숙 성장기": "남은 성장과 이익률이 지켜지는 정도",
              "성숙기": "지금의 이익과 그 이익을 지키는 데 드는 재투자", "쇠퇴기": "남은 사업에서 나오는 현금과 정리하는 속도"}


def _n(x):
    try:
        if x is None or isinstance(x, bool):
            return None
        return float(x)
    except (TypeError, ValueError):
        return None


def _글(x):
    return ("%s" % x).strip() if isinstance(x, str) else ""


# ══════════════════════════════════════════════════════════════════ 1. 입력 — 꼴 검사

def 입력검사(가정):
    """Narrative 키들의 꼴 → (오류, 경보). 오류면 레터가 rc 2 로 멈춘다(입력의 꼴)."""
    오류, 경보 = [], []
    N = 가정.get("Narrative")
    if N is not None:
        if not isinstance(N, dict):
            오류.append("Narrative 는 객체로 적습니다")
        else:
            for k in N:
                if k not in Narrative키 and not ("%s" % k).startswith("_"):
                    경보.append("Narrative 에 모르는 키 「%s」 (유효: %s)" % (k, " · ".join(Narrative키)))
            for k in 글키:
                if k in N and N[k] is not None and not isinstance(N[k], str):
                    오류.append("Narrative.%s 는 글로 적습니다" % k)
            값밖 = N.get("값밖")
            if 값밖 is not None and not (isinstance(값밖, list) and all(isinstance(x, (str, dict)) for x in 값밖)):
                오류.append("Narrative.값밖 은 글 또는 {\"글\"} 의 목록으로 적습니다")
            틀 = N.get("틀림")
            if 틀 is not None and not (isinstance(틀, dict) and isinstance(틀.get("가정", []), list)):
                오류.append("Narrative.틀림 은 {\"가정\": [번호 …], \"길\": 글} 로 적습니다")
            if 틀 is not None and isinstance(틀, dict) and 틀.get("아래") is not None and not isinstance(틀.get("아래"), str):
                오류.append("Narrative.틀림.아래 는 글로 적습니다(값이 아래로 틀릴 길)")
            독 = N.get("독자")
            if 독 is not None:
                if not isinstance(독, dict):
                    오류.append("Narrative.독자 는 {\"가격말\", \"지수기준\", \"가로선\", \"지난사이클\"} 객체로 적습니다")
                else:
                    for k in ("가격말", "지수기준"):
                        if 독.get(k) is not None and not isinstance(독.get(k), str):
                            오류.append("Narrative.독자.%s 는 글로 적습니다" % k)
                    선 = 독.get("가로선")
                    if 선 is not None and not (isinstance(선, list) and all(
                            isinstance(x, dict) and _글(x.get("이름")) and (_글(x.get("키")) or (isinstance(x.get("키"), dict) and x["키"]
                                                                          and all(_글(v) for v in x["키"].values()))) for x in 선)):
                        오류.append("Narrative.독자.가로선 은 [{\"이름\", \"키\"(장부 키 — 정상 수준과 같은 지수, 또는 {구분 번호: 키})}] 로 적습니다")
                    for k in ("낱말", "제품"):                     # 통독 v3 — 3분 레터의 낱말 풀이 · 2막의 제품마다 값이 움직이는 방식
                        if 독.get(k) is not None and not (isinstance(독[k], list) and all(isinstance(x, str) for x in 독[k])):
                            오류.append("Narrative.독자.%s 는 [글 …] 로 적습니다" % k)
                    if 독.get("보조말") is not None and not (isinstance(독["보조말"], dict) and all(isinstance(v, str) for v in 독["보조말"].values())):
                        오류.append("Narrative.독자.보조말 은 {보조 시나리오 이름: 글} 로 적습니다")
                    지난 = 독.get("지난사이클")
                    if 지난 is not None and not (isinstance(지난, dict) and _글(지난.get("이름")) and _n(지난.get("낙폭")) is not None):
                        오류.append("Narrative.독자.지난사이클 은 {\"이름\", \"낙폭\"(정점에서 줄어든 비율 — 0.6 꼴), \"근거\"} 로 적습니다")
            절 = N.get("절글")
            if 절 is not None and not (isinstance(절, dict) and all(isinstance(v, list) and all(
                    isinstance(x, str) or (isinstance(x, dict) and (_글(x.get("글")) or isinstance(x.get("표"), dict))) for x in v) for v in 절.values())):
                오류.append("Narrative.절글 은 {절 키: [글 · {\"글\", \"뒤\", \"요소\"} · {\"표\": {\"머리\", \"줄\"}, \"뒤\"} …]} 로 적습니다")
            elif 절 is not None:                             # 문단마다 다는 「요소」(그 문단이 쓰는 원고 항목)의 이름
                import 레터원고                              # noqa: PLC0415
                오류 += 레터원고.입력검사(가정)[0]
            동 = N.get("동인")
            if 동 is not None and not (isinstance(동, dict) and all(
                    (k in ("독자", "깊이") and isinstance(v, list) and all(isinstance(x, str) for x in v)) or
                    (k == "표" and isinstance(v, list) and all(isinstance(x, dict) and _글(x.get("이름")) and (_글(x.get("낮음")) or _글(x.get("높음")))
                                                               for x in v))
                    for k, v in 동.items())):
                오류.append("Narrative.동인 은 {\"독자\": [글], \"깊이\": [글], \"표\": [{\"이름\", \"범위\", \"낮음\": 장부 키, \"높음\": 장부 키}]} 로 적습니다")
            정 = N.get("정상수준")
            if 정 is not None:
                if not isinstance(정, dict) or not isinstance(정.get("방법", []), list) or not isinstance(정.get("검증", []), list):
                    오류.append("Narrative.정상수준 은 {\"가정\", \"방법\": [{\"이름\", \"아래\", \"위\", \"가운데\"}], \"채택\", \"검증\": [{\"이름\", \"아래\", \"위\"}]} 로 적습니다")
                else:
                    for k, x in enumerate(정.get("방법") or []):
                        if not (isinstance(x, dict) and _글(x.get("이름")) and _n(x.get("아래")) is not None and _n(x.get("위")) is not None):
                            오류.append("Narrative.정상수준.방법[%d] 에 이름 · 아래 · 위(수)를 적습니다" % k)
                    for k, x in enumerate(정.get("검증") or []):
                        끝들 = [x.get(c) for c in ("아래", "위")] if isinstance(x, dict) else []
                        if not (isinstance(x, dict) and _글(x.get("이름")) and all(_n(v) is not None or (isinstance(v, dict) and _글(v.get("키"))) for v in 끝들)):
                            오류.append("Narrative.정상수준.검증[%d] 에 이름 · 아래 · 위(수 또는 {\"키\"})를 적습니다" % k)
            하 = N.get("하강")
            if 하 is not None:
                블 = 하 if isinstance(하, list) else [하]
                for k, x in enumerate(블):
                    관 = x.get("관측") if isinstance(x, dict) else None
                    if not (isinstance(x, dict) and (x.get("가정") or x.get("구분") is not None) and isinstance(관, list) and 관
                            and all(isinstance(o, dict) and _n(o.get("연수")) is not None and _n(o.get("연수")) > 0
                                    and (o.get("폭") is None or -1 < (_n(o.get("폭")) or 0) < 0) for o in 관)):
                        오류.append("Narrative.하강[%d] 은 {\"가정\": [도달 연도 번호 …], \"자\", \"출처\", \"관측\": [{\"구간\", \"연수\"(> 0), \"폭\"(−1 ~ 0 — 저점 ÷ 고점 − 1)}]} 로 적습니다" % k)
            지 = N.get("지난평가")
            if 지 is not None:
                if not isinstance(지, dict) or not _글(지.get("파일")):
                    오류.append("Narrative.지난평가 는 {\"파일\", \"날짜\", \"갈래\", \"까닭\"} 로 적습니다(파일은 회차 폴더 기준)")
                elif not _글(지.get("날짜")):
                    오류.append("Narrative.지난평가.날짜(지난 평가의 평가기준일 — 2026-03-31 꼴)를 적습니다")
                elif 지.get("갈래") is not None and 지.get("갈래") not in ("유지",) + 갈래들:
                    오류.append("Narrative.지난평가.갈래 는 유지 · %s 가운데 하나입니다" % " · ".join(갈래들))
    S = 가정.get("서사연결")
    if S is not None:
        if not isinstance(S, dict):
            오류.append("서사연결 은 {가정 번호: Narrative 한 줄} 객체로 적습니다")
        else:
            for k, v in S.items():
                if not (("%s" % k).isdigit() or k == "WACC"):
                    오류.append("서사연결 의 키 「%s」 — 가정 번호나 WACC 로 적습니다" % k)
                if not (isinstance(v, str) or (isinstance(v, dict) and isinstance(v.get("문장"), str))):
                    오류.append("서사연결.%s — 글 하나 또는 {\"문장\", \"열\"} 로 적습니다" % k)
                elif isinstance(v, dict) and v.get("열") is not None and not isinstance(v.get("열"), list):
                    오류.append("서사연결.%s.열 은 기간 ID 목록입니다" % k)
    G = 가정.get("신호")
    if G is not None:
        if not isinstance(G, list):
            오류.append("신호 는 목록으로 적습니다")
            G = []
        G = [x for x in G if not (isinstance(x, dict) and not _글(x.get("신호")) and x.get("갈래") is None)]   # 템플릿의 빈 줄
        if isinstance(G, list):
            for i, x in enumerate(G):
                if not isinstance(x, dict) or not _글(x.get("신호")):
                    오류.append("신호[%d] 에 「신호」 글이 없습니다" % i)
                    continue
                if x.get("갈래") not in 갈래들:
                    오류.append("신호[%d].갈래 는 %s 가운데 하나입니다" % (i, " · ".join(갈래들)))
                if not isinstance(x.get("가정", []), list):
                    오류.append("신호[%d].가정 은 가정 번호 목록입니다" % i)
                elif not x.get("가정") and not _글(x.get("고칠가정")):
                    경보.append("신호[%d] 에 고칠 가정(「가정」 번호 목록 또는 「고칠가정」 글)이 없습니다" % i)
                if x.get("시나리오") not in (None,) + 시나리오들:
                    오류.append("신호[%d].시나리오 는 비관 · 기준 · 낙관 가운데 하나입니다" % i)
                for 칸 in ("자료", "기준일값", "문턱"):
                    if not _글(x.get(칸)):
                        경보.append("신호[%d] 의 「%s」 가 비었습니다" % (i, 칸))
                if x.get("방향") is not None and x.get("방향") not in 신호방향:
                    오류.append("신호[%d].방향 은 %s 가운데 하나입니다(켜지면 주당가치가 움직이는 쪽)" % (i, " · ".join(신호방향)))
                if x.get("상태") is not None and x.get("상태") not in 신호상태:
                    오류.append("신호[%d].상태 는 %s 가운데 하나입니다" % (i, " · ".join(신호상태)))
                if x.get("지금") is not None and not isinstance(x.get("지금"), str):
                    오류.append("신호[%d].지금 은 글로 적습니다(평가기준일 뒤의 상태 — 날짜와 함께)" % i)
                if x.get("요약") is not None and not isinstance(x.get("요약"), bool):
                    오류.append("신호[%d].요약 은 true · false 로 적습니다(3분 레터의 신호등에 싣는다)" % i)
    P = 가정.get("3P")
    if P is not None:
        if not isinstance(P, dict):
            오류.append("3P 는 {\"시나리오\": …, \"가정\": …} 객체로 적습니다")
        else:
            for s, x in (P.get("시나리오") or {}).items():
                if isinstance(x, dict) and x.get("판정") is None:
                    continue                                 # 템플릿의 빈 칸 — 채우면 본다
                if s not in 시나리오들 or not isinstance(x, dict) or x.get("판정") not in 판정들:
                    오류.append("3P.시나리오.%s — 판정은 %s 가운데 하나입니다" % (s, " · ".join(판정들)))
                    continue
                if s == "기준" and x["판정"] != "Probable":
                    오류.append("3P.시나리오.기준 — 기준 시나리오는 Probable 이어야 합니다(지금 %s)" % x["판정"])
                if s != "기준" and 판정순[x["판정"]] < 판정순["Plausible"]:
                    오류.append("3P.시나리오.%s — 비관 · 낙관은 Plausible 이상만 싣습니다(지금 %s)" % (s, x["판정"]))
            for k, x in (P.get("가정") or {}).items():
                if isinstance(x, dict) and x.get("판정") is None:
                    continue
                if not ("%s" % k).isdigit() or not isinstance(x, dict) or x.get("판정") not in 판정들:
                    오류.append("3P.가정.%s — {\"판정\": Possible · Plausible · Probable, \"근거\"} 로 적습니다" % k)
    M = 가정.get("메타") or {}
    이 = M.get("이해관계")
    if 이 is not None and not (isinstance(이, dict) and (isinstance(이.get("보유"), bool) or 이.get("보유") is None)):
        오류.append("메타.이해관계 는 {\"보유\": true · false, \"보유내용\", \"의뢰\"} 로 적습니다")
    생 = M.get("생애주기")
    if 생 is not None and not (isinstance(생, dict) and 생.get("단계") is None):
        if not isinstance(생, dict) or 생.get("단계") not in 단계들:
            오류.append("메타.생애주기.단계 는 %s 가운데 하나입니다" % " · ".join(단계들))
        else:
            덧 = 생.get("덧표지") or []
            if not isinstance(덧, list) or any(x not in 덧표지들 for x in 덧):
                오류.append("메타.생애주기.덧표지 는 %s 의 목록입니다" % " · ".join(덧표지들))
            elif any(x in ("경기순환", "원자재") for x in 덧) and not _글(생.get("가격변수")):
                오류.append("메타.생애주기 — 경기순환 · 원자재 기업은 「가격변수」(정상 수준을 보는 가격)를 적습니다")
    return 오류, 경보


# ══════════════════════════════════════════════════════════════════ 2. 저자 글 — 장부 키 펴기

def _키꼴(맥, 키):
    import 레터 as _L                                       # noqa: PLC0415
    부 = 키.split(":")
    if 부[0] in ("A", "S") and len(부) > 1 and 부[1].isdigit():
        return _L.가정꼴(부[1], 맥.구)
    return None


_어림꼴 = {"금액": "어림금액", "주당": "어림주당"}


def 펴기(맥, 글, 자리, 어림=False, 부록=False):
    """저자 글의 「{키|꼴}」 을 장부에 적으며 편다 → 실을 글(검수에 걸리면 빈 글 — 원고글이 알린다).
    어림 = True(3분 레터 — R1b · L16) 면 금액 · 주당 꼴을 반올림 꼴(어림금액 · 어림주당)로 찍는다. 저자의 말은 그대로다.
    부록 = True 면 부록의 규칙으로 잰다(2026-10-26 — 부록 A 의 독자근거가 자리표시를 펴지 않고 찍던 결함)."""
    글 = _글(글)
    if not 글:
        return ""

    def 바꿈(m):
        안, 꼴 = m.group(1).strip(), (m.group(2) or "").strip()
        if not 꼴 and "·" in 안 and ":" not in 안.rsplit("·", 1)[1] and " " not in 안.rsplit("·", 1)[1].strip():
            안, 꼴 = 안.rsplit("·", 1)[0].strip(), 안.rsplit("·", 1)[1].strip()      # 1.1.2(Q31) — 「{키·꼴}」 도 「{키|꼴}」 로 읽는다(원고 두 회차가 이 꼴로 썼다)
        부 = 안.split()
        if 안.startswith("절:") and 맥.절.get(안[2:]):          # 통독 v3 상-10 — 「{절:역산}」 → 「17절」(막이면 「5막」 — 번호를 손으로 적지 않는다)
            import 레터1부 as P                                # noqa: PLC0415
            return P.곳(맥, 맥.절[안[2:]])
        if 안.startswith("눈금:") and 안[3:].strip().isdigit():   # 2026-10-16 — 가격 변수의 기준 이름(「2025년 평균」)
            import 레터1부 as P                                # noqa: PLC0415
            s = int(안[3:].strip())
            x = next((y for y in 맥.구.get("매출구분") or [] if y.get("번호") == s), {})
            return P.눈금이름(맥, x)
        try:
            if 부 and 부[0] == "백" and len(부) == 3 and 부[1].isdigit():   # 「{백 3 키|수0}」 — 지수 ÷ 기준 × 100
                import 레터1부 as P                            # noqa: PLC0415
                return 맥.식(["×", ["÷", 표4키(부[2], 표4줄들(getattr(맥, "민", None))), P.눈금키(맥, int(부[1]))], 100], 꼴 or "수0")
            if 꼴 == "글" and 부 and len(부) == 1:              # 레터 v27 6단계 — 엔진이 낸 글(대조 판정 「안 · 밖」 따위)은 장부에 글로 적는다
                return 맥.엔진글(표4키(안, 표4줄들(getattr(맥, "민", None)))) or "—"
            if 부 and 부[0] in _연산:
                날식 = 식만들기(부)                              # 1.1.19 — 연산을 겹쳐 쓴다(「{÷ 음 A B}」)
                식 = 식키바꿈(날식, 표4줄들(getattr(맥, "민", None)))
                _표4이름맞대기(맥, 글, m, 식, 자리, 막음)
                꼴 = 꼴 or "지수2"
                f = _어림꼴.get(꼴, 꼴) if 어림 else 꼴
                g = 맥.식(식, f)
                if 식 != 날식:                                  # 줄 이름 키 — 원고에 적힌 꼴(이름 키)로도 장부에 적는다(교열이 원고의 자리표시를 장부로 편다)
                    _별칭적기(맥, "식:" + json.dumps(날식, ensure_ascii=False), 식, f, g)
                _배알림(맥, lambda: 맥.식값(식), f, 자리, m)
                return g
            키 = 표4키(안, 표4줄들(getattr(맥, "민", None)))
            _표4이름맞대기(맥, 글, m, [키], 자리, 막음)
            꼴 = 꼴 or _키꼴(맥, 키) or "지수2"
            f = _어림꼴.get(꼴, 꼴) if 어림 else 꼴
            g = 맥.수(키, f)
            if 키 != 안:
                _별칭적기(맥, 안, ["합", 키], f, g)
            _연도알림(맥, 키, f, 자리, m)
            _배알림(맥, lambda: 맥.값(키), f, 자리, m)
            return g
        except Exception as e:                               # noqa: BLE001
            맥.알림.append("저자 글의 장부 키를 못 폈다(%s) — 「%s」: %s" % (자리, m.group(0), e))
            return m.group(0)
    막음 = []
    편 = 판정비문고침(조사맞춰펴기(글, 바꿈))
    if 막음:                                                 # 1.1.19 — 표 Ⅳ 줄을 자리 번호로 불렀는데 문장의 가정 이름이 다른 줄이다(다른 가정의 값이 실린다)
        for x in 막음:
            맥.알림.append("원고를 싣지 않았다(%s) — %s" % (자리, x))
        return ""
    return 맥.원고글(편, 자리, 부록=부록)


_판정비문 = re.compile(r"범위\s*(—|정의 다름)에\s*있(습니다|고|으며|어|는)")
_판정끝말 = {"습니다": "않았습니다", "고": "않았고", "으며": "않았으며", "어": "않아", "는": "않은"}


def 판정비문고침(글):
    """1.1.21 — 원고 「… 그 실적 범위 {…:판정끝|글}에 있습니다」 를 펼 때 판정이 「안 · 밖」 이 아니면(「—」 실적이 한 점 · 「정의 다름」) 그 글자가 문장에 끼어
    비문이 된다(「범위 —에 있습니다」 · 「범위 정의 다름에 있습니다」). 판정하지 않았다는 사실 문장으로 바꾼다 — 숫자는 건드리지 않는다."""
    def 바(m):
        끝 = _판정끝말[m.group(2)]
        return ("범위와 견주지 %s" % 끝) if m.group(1) == "—" else ("범위와 정의가 달라 견주지 %s" % 끝)
    return _판정비문.sub(바, 글 or "")


# ── 1.1.19 자리표시 도움(연산 겹쳐 쓰기 · 표 Ⅳ 줄 이름 키 · 연도 꼴) ────────────────────────────────────────
_항수 = {"÷": 2, "−": 2, "괴리": 2, "음": 1, "절대": 1}       # 나머지 연산(× · 합 · 최대 · 최소 · CAGR)은 남은 항을 모두 받는다


def _항(x):
    return _n(x) if _n(x) is not None and not re.match(r"^[A-Za-z가-힣]", x) else x


def 식만들기(부):
    """자리표시의 낱말들 → 식. 앞에 연산을 둔 꼴(폴란드 꼴)이라 겹쳐 쓸 수 있다 — 「÷ 음 A B」 → [÷, [음, A], B].
    항 수가 정해진 연산(÷ · − · 괴리 = 둘, 음 · 절대 = 하나)은 그만큼만 받고, 나머지 연산은 남은 항을 모두 받는다(그래서 겹친 식 안에서는 끝에 둔다).
    겹치지 않은 옛 꼴(「÷ A B」 · 「합 A B C」 · 「CAGR A B 5.5」)은 종전과 같은 평평한 식이다. 남는 항이 있으면 종전처럼 평평하게 읽는다."""
    def 읽(i):
        op = 부[i]
        i += 1
        n = _항수.get(op)
        항 = []
        while i < len(부) and (n is None or len(항) < n):
            if 부[i] in _연산:
                sub, i = 읽(i)
                항.append(sub)
            else:
                항.append(_항(부[i]))
                i += 1
        if n is not None and len(항) < n:
            raise ValueError("연산 「%s」 의 항이 %d개다(%d개를 받는다)" % (op, len(항), n))
        return [op] + 항, i
    식, i = 읽(0)
    if i != len(부):
        return [부[0]] + [_항(x) for x in 부[1:]]
    return 식


_표4대상키 = re.compile(r"^(민:표4:|가:역셀:)대상:([^:]+)(:.*)?$")
_표4번호키 = re.compile(r"^민:표4:줄:(\d+):(?:내재값|적용값)$")    # 그 줄 가정의 값 칸만(닿는끝 · 내재영구이익률 같은 딸린 칸은 다른 이름을 말한다)


def 표4줄들(민):
    return (((민 or {}).get("표4") or {}).get("줄") or []) if isinstance(민, dict) else []


def 표4대상(줄들, 대상글):
    """표 Ⅳ 의 줄 가운데 대상(가정 번호 · 엔진 손잡이 대상)이 「a+b」 와 같은 줄 → i 또는 None(차례는 보지 않는다)."""
    원 = sorted(x.strip() for x in ("%s" % 대상글).split("+") if x.strip())
    맞 = [i for i, r in enumerate(줄들) if sorted("%s" % x for x in ((r or {}).get("대상") or [])) == 원]
    return 맞[0] if len(맞) == 1 else None


def 표4키(키, 줄들):
    """1.1.19 — 표 Ⅳ 의 줄을 가정 이름(대상)으로 부르는 키 → 지금 표의 줄 번호 키. 줄 차례는 판마다 바뀐다(같은 번호에 다른 가정의 값이 실렸다).
      「민:표4:대상:<a+b>:<칸>」 → 「민:표4:줄:<i>:<칸>」 · 「가:역셀:대상:<a+b>:<시트>:<줄>[:<열>]」 → 「가:역셀:<i>:…」. 이름 키가 아니면 그대로."""
    m = _표4대상키.match(키) if isinstance(키, str) else None
    if not m:
        return 키
    i = 표4대상(줄들, m.group(2))
    if i is None:
        raise KeyError("표 Ⅳ 에 대상 「%s」 인 줄이 없다(있는 줄: %s)" % (
            m.group(2), " · ".join("+".join("%s" % x for x in (r.get("대상") or [])) for r in 줄들) or "없음"))
    return ("민:표4:줄:%d%s" if m.group(1) == "민:표4:" else "가:역셀:%d%s") % (i, m.group(3) or "")


def 식키바꿈(식, 줄들):
    """식 안의 표 Ⅳ 이름 키를 줄 번호 키로(겹친 식까지)."""
    return [식[0]] + [식키바꿈(x, 줄들) if isinstance(x, list) else 표4키(x, 줄들) for x in 식[1:]]


def _식키들(식):
    for x in 식:
        if isinstance(x, list):
            yield from _식키들(x)
        elif isinstance(x, str):
            yield x


def 표4이름들(r, 맥=None):
    """표 Ⅳ 줄의 이름 — 엔진 손잡이 이름 · 레터가 찍는 이름 · 괄호 안 영문 약어(「WACC」 · 「RONIC」). 괄호 덧말은 뗀다."""
    낸 = []
    바탕 = ["%s" % (r.get("이름") or "")]
    if 맥 is not None:
        try:
            import 레터1부 as P                              # noqa: PLC0415
            바탕.append(P.손잡이이름({"이름": r.get("이름"), "대상": r.get("대상")}, 맥))
        except Exception:                                    # noqa: BLE001
            pass
    for b in 바탕:
        for 괄 in re.findall(r"\(([^()]*)\)", b):
            if re.fullmatch(r"[A-Za-z][A-Za-z ]{2,}", 괄.strip()):
                낸.append(괄.strip())
        t = re.sub(r"\s*\([^()]*\)", "", b).strip()
        if len(t) >= 2:
            낸.append(t)
    return list(dict.fromkeys(낸))


_문장끝식 = re.compile(r"[.?!](?=\s|$)|\n")


def _앞마디(글, a):
    """글[a:] 의 자리표시 바로 앞 마디 — 같은 문장 안에서 앞 자리표시의 끝(없으면 문장 머리)부터 a 까지(자리표시 안의 「2.DCF」 를 문장 끝으로 읽지 않는다).
    「A로 풀면 {x}, B로 풀면 {y}」 처럼 한 문장에 여러 줄을 부르면 마디마다 제 이름을 말한다 — 문장 통째로 보면 다른 마디의 이름이 섞인다."""
    가린 = _자리표.sub(lambda x: " " * len(x.group(0)), 글)
    앞 = max([x.end() for x in _문장끝식.finditer(가린, 0, a)] + [x.end() for x in _자리표.finditer(글, 0, a) if x.end() <= a] + [0])
    return 가린[앞:a]


def 표4이름어긋남(줄들, 문장, i, 맥=None):
    """자리 번호로 부른 표 Ⅳ 줄 i 와 그 자리표시 앞 마디(`_앞마디`)의 가정 이름 → 어긋나면 그 말, 아니면 None.
    마디에 줄 i 의 이름이 없고 다른 줄의 이름이 있으면 어긋남이다(같은 번호에 다른 가정의 값이 실린 자리 — 1.1.9 실측). 이름이 없거나 저자가 다른 말로
    불렀으면(「최종 예측 연도 영업이익률」) 판정하지 않는다."""
    if i >= len(줄들):
        return None
    이 = 표4이름들(줄들[i], 맥)
    if any(n in 문장 for n in 이):
        return None
    남 = [(j, n) for j, r in enumerate(줄들) if j != i for n in 표4이름들(r, 맥) if n in 문장]
    if not 남:
        return None
    return "표 Ⅳ 줄 %d 은 「%s」 인데 문장은 「%s」 을 말한다 — 줄을 가정 이름 키 「민:표4:대상:%s:…」 로 부른다" % (
        i, 이[0] if 이 else "?", 남[0][1], "+".join("%s" % x for x in (줄들[남[0][0]].get("대상") or [])))


def _표4이름맞대기(맥, 글, m, 키들, 자리, 막음):
    """펴기 — 자리표시가 표 Ⅳ 줄을 번호로 부르면(이름 키를 거치지 않은 번호) 문장의 가정 이름과 맞댄다. 어긋나면 막음에 적는다."""
    if "표4:대상:" in m.group(0) or "역셀:대상:" in m.group(0):    # 이름 키로 부른 줄 — 줄 차례와 무관하다
        return
    키들 = list(_식키들(키들))
    if not any(_표4번호키.match(k) for k in 키들):
        return
    줄들 = 표4줄들(getattr(맥, "민", None))
    문장 = _앞마디(글, m.start())
    for k in 키들:
        mm = _표4번호키.match(k) if isinstance(k, str) else None
        if mm:
            말 = 표4이름어긋남(줄들, 문장, int(mm.group(1)), 맥)
            if 말 and 말 not in 막음:
                막음.append(말)


def _별칭적기(맥, 키, 식, 꼴, 글):
    """원고에 적힌 키(이름 키 · 겹친 식)로 장부에 한 줄 더 — 값은 식으로(게이트가 식을 다시 셈해 맞댄다)."""
    장 = getattr(맥, "장부", None)
    if 장 is None or not 글 or 글 == "—":
        return
    try:
        v = _n(맥.식값(식))
    except Exception:                                        # noqa: BLE001
        return
    if v is not None:
        장.적기(키, v, 꼴, 글, 식=식)


def _연도알림(맥, 키, 꼴, 자리, m):
    """연도 값(1900~2100 의 정수)을 수 꼴(「수0」)로 부르면 「2,009」 로 찍힌다 — 꼴 「연도」(→ 「2009년」)로 쓰게 알린다."""
    if not re.fullmatch(r"수\d", 꼴 or ""):
        return
    try:
        v = _n(맥.값(키))
    except Exception:                                        # noqa: BLE001
        return
    if v is not None and float(v).is_integer() and 1900 <= v <= 2100:
        맥.알림.append("연도로 보이는 값을 꼴 「%s」 로 불렀다(%s) — 「%s」 가 「%s」 로 찍혔다. 「{%s|연도}」(→ 「%d년」)로 쓴다"
                     % (꼴, 자리, m.group(0), "{:,.0f}".format(v), m.group(1).strip(), int(v)))


def _배알림(맥, 값, 꼴, 자리, m):
    """정수 배수 꼴(「배0」)이 값을 크게 바꾸면(1.825 → 「2배」) 알린다 — 본편은 「|배1」, 3분 레터는 차이를 퍼센트로
    (1.1.19 · 한 레터 안에서 같은 값이 「2배」 · 「1.8배」 로 갈렸다 · 3분 레터는 소수 배수를 쓰지 않는다)."""
    if 꼴 != "배0":
        return
    try:
        v = _n(값())
    except Exception:                                        # noqa: BLE001
        return
    if v is not None and 배어림꼴(v) == "배1":
        import 레터 as _L                                   # noqa: PLC0415
        맥.알림.append("정수 배수가 값을 %s%% 넘게 바꾼다(%s) — 「%s」 가 「%s」 로 찍혔다(값 %.3f). 본편은 「|배1」(→ 「%s」), 3분 레터는 차이를 퍼센트(「{괴리 A B|폭0}」 + 많다 · 적다)로 쓴다"
                     % ("{:g}".format(배어림한도 * 100), 자리, m.group(0), _L.꼴글(v, "배0"), v, _L.꼴글(v, "배1")))


def 키풀어글(원, 글, 메타):
    """게이트용 — 저자 글의 「{키|꼴}」 을 엔진 값으로 편 글(장부에 적지 않는다)."""
    import 레터 as _L                                       # noqa: PLC0415
    줄들 = 표4줄들((원 or {}).get("민"))

    def 바꿈(m):
        안, 꼴 = m.group(1).strip(), (m.group(2) or "").strip()
        부 = 안.split()
        try:
            if 안.startswith("눈금:") and 안[3:].strip().isdigit():
                import 레터1부 as P                            # noqa: PLC0415
                d = P.눈금선언(원["가정"])
                return ("%s" % d["이름"]).strip() if d and _n((d.get("지수") or {}).get(안[3:].strip())) else m.group(0)
            if 부 and 부[0] == "백" and len(부) == 3 and 부[1].isdigit():
                import 레터1부 as P                            # noqa: PLC0415
                return _L.꼴글(_L.식값(["×", ["÷", 표4키(부[2], 줄들), P.눈금키(원["가정"], int(부[1]))], 100], 원), 꼴 or "수0", 메타)
            if 부 and 부[0] in _연산:
                식 = 식키바꿈(식만들기(부), 줄들)                  # 1.1.19 — 겹친 연산 · 표 Ⅳ 줄 이름 키(펴기와 같은 셈)
                return _L.꼴글(_L.식값(식, 원), 꼴 or "지수2", 메타)
            안 = 표4키(안, 줄들)
            if not 꼴:
                부2 = 안.split(":")
                꼴 = _L.가정꼴(부2[1], 원["가정"].get("구조")) if 부2[0] in ("A", "S") and len(부2) > 1 and 부2[1].isdigit() else "지수2"
            if 꼴 == "글" and len(부) == 1:                     # 레터 v27 6단계 — 엔진이 낸 글(대조 판정)
                v = _L.키풀기(안, 원)
                return re.sub(r"\s+", " ", ("%s" % (v or ""))).strip() or "—"
            return _L.꼴글(_L.키풀기(안, 원), 꼴, 메타)
        except Exception:                                    # noqa: BLE001
            return m.group(0)
    return 조사맞춰펴기(_글(글), 바꿈)


# ══════════════════════════════════════════════════════════════════ 3. Narrative 숫자(M2) — 저자 글의 숫자 · 눈금을 장부와 맞댄다

def 글자리들(가정, 가성=None):
    """저자가 쓴 Narrative 글 — [(자리, 글, 시나리오)]. 숫자 대조(M2)의 대상(제안 5절 M2 — 서사 · 서술 · 시나리오이야기 · 조합 근거 + 새 키)."""
    낸 = []
    N = 가정.get("Narrative") or {}
    if isinstance(N, dict):
        for k in 글키:
            if _글(N.get(k)):
                낸.append(("Narrative.%s" % k, N[k], "기준"))
        for i, x in enumerate(N.get("값밖") or []):
            g = x if isinstance(x, str) else (x or {}).get("글")
            if _글(g):
                낸.append(("Narrative.값밖[%d]" % i, g, "기준"))
        if isinstance(N.get("틀림"), dict) and _글(N["틀림"].get("길")):
            낸.append(("Narrative.틀림.길", N["틀림"]["길"], "기준"))
        if isinstance(N.get("틀림"), dict) and _글(N["틀림"].get("아래")):
            낸.append(("Narrative.틀림.아래", N["틀림"]["아래"], "기준"))
        if isinstance(N.get("정상수준"), dict) and _글(N["정상수준"].get("채택")):
            낸.append(("Narrative.정상수준.채택", N["정상수준"]["채택"], "기준"))
        if isinstance(N.get("지난평가"), dict) and _글(N["지난평가"].get("까닭")):
            낸.append(("Narrative.지난평가.까닭", N["지난평가"]["까닭"], "기준"))
    서사 = 가정.get("서사")
    if isinstance(서사, dict):
        for k, v in sorted(서사.items()):
            if _글(v):
                낸.append(("서사.%s" % k, v, "기준"))
    elif _글(서사):
        낸.append(("서사", 서사, "기준"))
    서 = 가정.get("서술") or {}
    for 칸 in ("세계서술",):                                  # 관측근거는 저자 메모(레터 · 워크북에 싣지 않는다) — M2 밖
        for s, v in ((서.get(칸) or {}) if isinstance(서.get(칸), dict) else {}).items():
            if _글(v):
                낸.append(("서술.%s.%s" % (칸, s), v, s if s in 시나리오들 else "기준"))
    for s, v in ((가정.get("시나리오이야기") or {}) if isinstance(가정.get("시나리오이야기"), dict) else {}).items():
        if isinstance(v, dict) and _글(v.get("한줄")):
            낸.append(("시나리오이야기.%s.한줄" % s, v["한줄"], s if s in 시나리오들 else "기준"))
    for k, v in ((가정.get("서사연결") or {}) if isinstance(가정.get("서사연결"), dict) else {}).items():
        g = v if isinstance(v, str) else (v or {}).get("문장")
        if _글(g):
            낸.append(("서사연결.%s" % k, g, "기준"))
    for i, x in enumerate(가정.get("신호") or [] if isinstance(가정.get("신호"), list) else []):
        for 칸 in ("신호", "기준일값", "문턱", "지금"):
            if isinstance(x, dict) and _글(x.get(칸)):
                낸.append(("신호[%d].%s" % (i, 칸), x[칸], x.get("시나리오") or "기준"))
    P = 가정.get("3P") or {}
    for s, x in ((P.get("시나리오") or {}) if isinstance(P, dict) else {}).items():
        for 칸 in ("근거", "신호"):
            if isinstance(x, dict) and _글(x.get(칸)):
                낸.append(("3P.시나리오.%s.%s" % (s, 칸), x[칸], s if s in 시나리오들 else "기준"))
    for k, x in ((P.get("가정") or {}) if isinstance(P, dict) else {}).items():
        if isinstance(x, dict) and _글(x.get("근거")):
            낸.append(("3P.가정.%s.근거" % k, x["근거"], "기준"))
    for i, x in enumerate((가성 or {}).get("조합") or []):
        if isinstance(x, dict) and _글(x.get("근거")):
            낸.append(("가격성립.조합[%d].근거" % i, x["근거"], "조합:%d" % i))
    return 낸


_단위 = r"조 원|억 원|만 원|억 달러|만 달러|억 유로|억 엔|%p|%|배|원|달러|엔|유로"
_수토큰 = re.compile(r"(?<![\w.,])([−\-+]?)(\d[\d,]*(?:\.\d+)?)\s?(%s)(?![가-힣A-Za-z])|(?<![\w.,−\-+])([−\-+]?)(\d+\.\d+)(?![\d.,%%]|\s?(?:%s|[가-힣]))"
                  % (_단위, _단위))


def 수토큰(글):
    """글의 값 꼴 숫자 → [(부호 붙은 수, 단위, 자릿수, 조각, 자리)]. 단위가 없는 소수(지수 따위)는 단위 「」."""
    낸 = []
    for m in _수토큰.finditer(글):
        if m.group(2) is not None:
            부, 수, 단 = m.group(1), m.group(2), m.group(3)
        else:
            부, 수, 단 = m.group(4), m.group(5), ""
        v = float(수.replace(",", ""))
        if 부 in ("−", "-"):
            v = -v
        자 = len(수.split(".")[1]) if "." in 수 else 0
        낸.append((v, 단, 자, m.group(0), m.start()))
    return 낸


def _장부토큰(장부숫자):
    """장부의 글(꼴이 「글」 이 아닌 것)을 토큰으로 → {단위: [수 …]}."""
    낸 = {}
    for x in 장부숫자 or []:
        if x.get("꼴") == "글":
            continue
        for v, 단, _자, _조, _i in 수토큰("%s" % (x.get("글") or "")):
            낸.setdefault(단, []).append(v)
            if 단 in ("%", "%p"):
                낸.setdefault("%·%p", []).append(v)
    return 낸


def _있나(토큰, v, 단, 자):
    허용 = 0.5 * 10 ** (-자) + 1e-9
    for w in 토큰.get(단, []):
        if abs(w - v) <= 허용 or (단 in ("%", "%p") and abs(abs(w) - abs(v)) <= 허용 and w * v >= 0):
            return True
    return False


def _문장들(글):
    return [x.strip() for x in re.split(r"(?<=[.!?])\s+|\n+", 글) if x.strip()]


def _수준구분(원):
    """정상 수준을 쓰는 매출 구분 — [(번호, 이름, 기준 기간 지수 T:6s7:판매단가지수, 기준기간 종류)]."""
    가정 = 원["가정"]
    낸 = []
    for x in (가정.get("구조") or {}).get("매출구분") or []:
        s = x.get("번호")
        if x.get("경로") != "수준" or not isinstance(s, int) or s >= 6 or x.get("단가경로") != "수렴":
            continue
        t = ((가정.get("표") or {}).get("6%d7" % s) or {})
        if isinstance(t.get("기준"), dict):
            t = t["기준"]
        낸.append((s, ("%s" % (x.get("이름") or "")).strip(), _n(t.get("판매단가지수")), x.get("기준기간")))
    return 낸


def _정상값(원, s, 시, 가성=None):
    """시나리오(또는 조합) 의 정상 수준 판매단가 지수 — 조합이면 그 조합 손잡이의 값(그 구분을 겨냥할 때), 없으면 기준."""
    import 레터 as _L                                       # noqa: PLC0415
    if 시.startswith("조합:"):
        i = int(시.split(":")[1])
        for 손 in (((가성 or {}).get("조합") or [])[i].get("손잡이") or []):
            if "6%d6" % s in ["%s" % x for x in 손.get("대상") or []] and 손.get("방식", "가산") == "값":
                return _n(손.get("값"))
        시 = "기준"
    return _n(_L._시점값(원["가정"], "6%d6" % s, 시))


def _근거범위(가정, 번호들):
    """가정의 근거 네 칸 · 서사연결 에 적힌 소수 범위 「a~b」 — [(a, b)]."""
    낸 = []
    for 번 in 번호들:
        글들 = list((가정.get("근거") or {}).get("%s" % 번) or [])
        v = (가정.get("서사연결") or {}).get("%s" % 번)
        글들.append(v if isinstance(v, str) else (v or {}).get("문장") if isinstance(v, dict) else "")
        for g in 글들:
            for m in re.finditer(r"(?<![\d.])(\d+\.\d+)\s*[~∼]\s*(\d+\.\d+)(?!\s?%|\d)", "%s" % (g or "")):
                a, b = float(m.group(1)), float(m.group(2))
                if a <= b:
                    낸.append((a, b))
    return 낸


def 숫자대조(원, 장부숫자, 가성=None):
    """M2 — 저자 Narrative 글의 숫자 · 눈금을 장부와 맞댄다 → [(등급, 자리, 항목, 조각)] (등급 「오류」).
      ① 값 꼴 숫자(원 · % · 배 …) · 단위 없는 소수가 장부에 없다
      ② 정상 수준의 % · 지수가 장부의 눈금(매출 구분의 기준 기간 = 100% · 지수)과 다르다 · 「2분기보다 높게」 처럼 눈금과 반대로 말했다
      ③ 「N분기 대비」 의 분기가 매출 구분의 기준 기간과 다르다
      ④ 「범위의 위 끝 · 아래 끝 · 가운데」 라고 한 값이 그 가정의 근거에 적힌 범위의 그 자리와 다르다
    저자 글의 「{키|꼴}」 은 엔진 값으로 편 뒤에 본다(장부 키로 찍은 숫자는 늘 맞는다)."""
    import 레터 as _L                                       # noqa: PLC0415
    가정 = 원["가정"]
    메타 = 가정.get("메타") or {}
    토큰 = _장부토큰(장부숫자)
    구분 = _수준구분(원)
    # 기준 분기는 재무 자료의 분기(2026-10-25 날짜 둘 — 메타.재무기준일, 없으면 평가기준일 · 옛 판정 그대로)
    m기 = re.match(r"^\s*(\d{4})-(\d{1,2})", "%s" % (메타.get("재무기준일") or 메타.get("평가기준일") or ""))
    기준분기 = (int(m기.group(2)) - 1) // 3 + 1 if m기 else None
    분기쓰나 = any(k == "직전분기" for _s, _이, _t, k in 구분) or any(
        (x.get("기준기간") == "직전분기") for x in (가정.get("구조") or {}).get("매출구분") or [])
    낸 = []
    for 자리, 원글, 시 in 글자리들(가정, 가성):
        글 = 키풀어글(원, 원글, 메타)
        자리표 = [(m.start(), m.end()) for m in _자리표.finditer(원글)]
        # ① 장부에 없는 숫자 — 장부 키로 편 숫자는 늘 장부에 있다(글이 바뀌어 자리를 다시 셀 수 없으니 펴기 전 글에서 「{」 밖만 본다)
        밖글 = _자리표.sub(" ", 원글)
        근거토큰 = {}
        if 시.startswith("조합:"):                          # 조합 근거는 그 손잡이가 겨냥한 가정의 근거 칸에 적힌 숫자도 받는다(범위 「58~67%」 의 양 끝 포함)
            i0 = int(시.split(":")[1])
            for 손 in (((가성 or {}).get("조합") or [])[i0].get("손잡이") or []):
                for 번 in 손.get("대상") or []:
                    for g in (가정.get("근거") or {}).get("%s" % 번) or []:
                        g = "%s" % (g or "")
                        g = re.sub(r"(\d+(?:\.\d+)?)\s*[~∼]\s*(\d+(?:\.\d+)?)\s?%", r"\1% \2%", g)
                        for v0, 단0, _자0, _조0, _i0 in 수토큰(g):
                            근거토큰.setdefault("%·%p" if 단0 in ("%", "%p") else 단0, []).append(v0)
        for v, 단, 자, 조, i in 수토큰(밖글):
            if 단 == "%" and re.match(r"\s?(?:신뢰)?구간|\s?신뢰", 밖글[i + len(조):i + len(조) + 4]):
                continue                                     # 「95% 구간」 — 통계의 수준(값이 아니다)
            if 근거토큰 and _있나(근거토큰, v, "%·%p" if 단 in ("%", "%p") else 단, 자):
                continue
            if not _있나(토큰, v, "%·%p" if 단 in ("%", "%p") else 단, 자):
                낸.append(("오류", 자리, "Narrative 숫자:장부에 없다 「%s」" % 조, 글[:90]))
        for 문 in _문장들(글):
            정상 = "정상 수준" in 문 or "정상 상태" in 문
            # ② 정상 수준의 눈금 — 「정상 수준」 뒤 35자 안(다음 「정상 수준」 앞까지)의 % · 지수
            if 정상 and 구분:
                기대퍼, 기대지수, 비율들 = [], [], []
                import 레터1부 as P                            # noqa: PLC0415
                눈 = P.눈금선언(가정)
                for s, 이, t, _k in 구분:
                    v = _정상값(원, s, 시, 가성)
                    if v is None:
                        continue
                    기대지수.append(v)
                    if t:
                        비율들.append(v / t)
                        기대퍼.append(round(v / t * 100, 1))
                    d = _n(((눈 or {}).get("지수") or {}).get("%d" % s))
                    if d:                                    # 2026-10-16 — 가격 변수의 기준(2025년 평균 = 100)으로 적은 % 도 받는다
                        기대퍼.append(round(v / d * 100, 1))
                자리들 = [m.start() for m in re.finditer(r"정상 (?:수준|상태)", 문)]
                for k, p0 in enumerate(자리들):
                    창 = 문[p0:min(p0 + 35, 자리들[k + 1] if k + 1 < len(자리들) else len(문))].split(",")[0]
                    for v, 단, 자, 조, _i in 수토큰(창):
                        if 단 == "%" and 기대퍼 and not any(abs(v - p) <= 0.5 * 10 ** (-자) + 0.5 for p in 기대퍼):
                            낸.append(("오류", 자리, "Narrative 숫자:정상 수준 「%s」 — 장부의 눈금(기준 기간 = 100%%)으로는 %s" % (
                                조, " · ".join("%.0f%%" % p for p in 기대퍼)), 문[:90]))
                        elif 단 == "" and 기대지수 and not any(abs(v - p) <= 0.5 * 10 ** (-자) + 1e-9 for p in 기대지수) and                                 not re.search(r"범위|끝|가운데|~", 창):
                            낸.append(("오류", 자리, "Narrative 숫자:정상 수준 지수 「%s」 — 장부는 %s" % (
                                조, " · ".join("%.2f" % p for p in 기대지수)), 문[:90]))
                m = re.search(r"정상 (?:수준|상태)[^.]{0,15}?(\d)분기(?:보다|에 비해|대비)[^.]{0,12}?(높|낮|위|아래|웃|밑)", 문)
                if m and 비율들:
                    위 = m.group(2) in ("높", "위", "웃")
                    if (위 and not all(r > 1 for r in 비율들)) or (not 위 and not all(r < 1 for r in 비율들)):
                        낸.append(("오류", 자리, "Narrative 눈금:「%s」 — 장부의 정상 수준은 기준 기간의 %s" % (
                            m.group(0)[m.group(0).find(m.group(1) + "분기"):], " · ".join("%.0f%%" % (r * 100) for r in 비율들)), 문[:90]))
            # ③ 분기 눈금
            if 분기쓰나 and 기준분기:
                for m in re.finditer(r"(?<!\d)(\d)분기\s?(?:대비|보다|의|에 비해)", 문):
                    if int(m.group(1)) != 기준분기:
                        낸.append(("오류", 자리, "Narrative 눈금:「%s」 — 매출 구분의 기준 기간은 %d분기" % (m.group(0), 기준분기), 문[:90]))
            # ④ 범위의 끝 · 가운데
            m = re.search(r"범위의\s?(?:가장\s?)?(위 끝|아래 끝|높은 끝|낮은 끝|윗 끝|가운데|한가운데)", 문)
            if m:
                대상 = []
                if 시.startswith("조합:"):
                    i = int(시.split(":")[1])
                    for 손 in (((가성 or {}).get("조합") or [])[i].get("손잡이") or []):
                        대상 += ["%s" % x for x in 손.get("대상") or []]
                elif 정상:
                    대상 = ["6%d6" % s for s, _이, _t, _k in 구분]
                범위 = _근거범위(가정, 대상)
                수들 = [v for v, 단, _자, _조, _i in 수토큰(문) if 단 == ""]
                자리말 = m.group(1)
                if 범위 and 수들:
                    x = 수들[-1] if not 시.startswith("조합:") else (수들[0])
                    if 자리말 in ("위 끝", "높은 끝", "윗 끝"):
                        맞 = any(abs(x - b) < 0.0051 for _a, b in 범위)
                    elif 자리말 in ("아래 끝", "낮은 끝"):
                        맞 = any(abs(x - a) < 0.0051 for a, _b in 범위)
                    else:
                        맞 = any(abs(x - (a + b) / 2) < 0.0151 for a, b in 범위)
                    if not 맞:
                        낸.append(("오류", 자리, "Narrative 숫자:「%s」 를 범위의 %s 이라 했으나 근거의 범위는 %s" % (
                            ("%g" % x), 자리말, " · ".join("%.2f~%.2f" % ab for ab in sorted(set(범위)))), 문[:90]))
    # 같은 자리 · 같은 숫자를 눈금으로 잡았으면 「장부에 없다」 는 뺀다(한 숫자에 한 번)
    눈금잡은 = {(x[1], re.search(r"「([^」]+)」", x[2]).group(1)) for x in 낸 if "정상 수준 「" in x[2] or "정상 수준 지수 「" in x[2]}
    return [x for x in 낸 if not ("장부에 없다" in x[2] and (x[1], re.search(r"「([^」]+)」", x[2]).group(1)) in 눈금잡은)]


# ══════════════════════════════════════════════════════════════════ 4. 이름 · 값 — 표에 싣는 말

def 가정말(맥, 번):
    import 레터 as _L                                       # noqa: PLC0415
    if 번 == "WACC":
        return "WACC"
    return 이름다듬기(_L.가정이름(번, 맥.구) or "가정 %s" % 번)


def 이름묶기(맥, 이름들):
    """「DRAM 판매단가 누적 변동률 · NAND 판매단가 누적 변동률」 → 「DRAM · NAND 판매단가 누적 변동률」 — 매출 구분 이름만 다른 가정을 묶는다."""
    구분들 = sorted({("%s" % (x.get("이름") or "")).strip() for x in (맥.구.get("매출구분") or [])} - {""}, key=len, reverse=True)
    묶음, 차례 = {}, []
    for 이름 in dict.fromkeys(이름들):
        앞 = next((g for g in 구분들 if 이름.startswith(g + " ")), None)
        열쇠 = 이름[len(앞) + 1:] if 앞 else ("", 이름)
        if 열쇠 not in 묶음:
            묶음[열쇠] = []
            차례.append(열쇠)
        if 앞:
            묶음[열쇠].append(앞)
    낸 = [("%s %s" % (" · ".join(묶음[k]), k)) if isinstance(k, str) else k[1] for k in 차례]
    return (", " if any(" · " in x for x in 낸) else " · ").join(낸)


def 이름다듬기(이름):
    """본문에서 부르는 가정 이름 — 기호 괄호(「영구성장률 (g)」)를 걷는다(제안 1절 — 기호는 표 머리 · 워크북에만)."""
    import 용어                                                # noqa: PLC0415
    for 기 in 용어.기호괄호():
        이름 = 이름.replace(" (%s)" % 기, "").replace("(%s)" % 기, "")
    return 이름


def 채택글(맥, 번, 열들=None):
    """서사연결 줄의 채택 칸 — 기준 시나리오의 값(장부). 한 값 가정은 그 값, 열별 가정은 모든 예측 열이 같으면 그 값,
    아니면 지정 열(없으면 첫 · 끝 예측 열)."""
    import 레터 as _L                                       # noqa: PLC0415
    import 레터1부 as P                                    # noqa: PLC0415
    if 번 == "WACC":
        return 맥.수("R:기준:WACC:예측기간:WACC", "퍼2")
    s = P.정상수준구분(맥, 번) if P.독자층(맥) else None
    if s is not None and _n(_L._시점값(맥.가정, 번, "기준")) is not None:     # 독자 층 — 정상 수준은 기준 기간 = 100 눈금으로
        x0 = next((x for x in 맥.구.get("매출구분") or [] if x.get("번호") == s), {})
        return "%s (%s = 100)" % (P.백글(맥, "S:%s:기준" % 번, s), P.눈금이름(맥, x0))
    if 번 == "219" and _n(_L._시점값(맥.가정, "219", "기준")) is None and _n(맥.값("R:기준:2.DCF:48")) is not None:
        return "영구기간 WACC와 같음(%s)" % 맥.수("R:기준:2.DCF:48", "퍼2")          # R1b(L10) — 「—」 대신 뜻을
    꼴 = _L.가정꼴(번, 맥.구)
    if 번 in (맥.가정.get("시점가정") or {}):
        return 맥.수("S:%s:기준" % 번, 꼴) if _n(_L._시점값(맥.가정, 번, "기준")) is not None else "—"
    if 번 in (맥.가정.get("가정") or {}):
        값들 = [(c, _n(_L._가정값(맥.가정, 번, "기준", c))) for c in 맥.예측열]
        값들 = [(c, v) for c, v in 값들 if v is not None]
        if not 값들:
            return "—"
        if 열들:
            고른 = [(c, v) for c, v in 값들 if c in 열들]
            return " · ".join("%s %s" % (맥.열말(c), 맥.수("A:%s:기준:%s" % (번, c), 꼴)) for c, _v in 고른) or "—"
        if len({round(v, 12) for _c, v in 값들}) == 1:
            return 맥.수("A:%s:기준:%s" % (번, 값들[0][0]), 꼴)
        (c1, _a), (c2, _b) = 값들[0], 값들[-1]
        return "%s %s → %s %s" % (맥.열말(c1), 맥.수("A:%s:기준:%s" % (번, c1), 꼴), 맥.열말(c2), 맥.수("A:%s:기준:%s" % (번, c2), 꼴))
    return "—"


def 연결줄들(맥):
    """서사연결 → 「Narrative와 입력값」 표의 줄 — 같은 문장의 가정을 한 줄로. [{문장, 번호들, 열들}] (가정 파일의 차례).
    가정 파일에 값이 없는 번호(구조가 선언하지 않은 줄 — 옛 판의 서사연결 따위)는 빼고 저자에게 알린다."""
    S = 맥.가정.get("서사연결") or {}
    줄들 = []
    for k, v in S.items():
        if k != "WACC" and "%s" % k not in (맥.가정.get("가정") or {}) and "%s" % k not in (맥.가정.get("시점가정") or {}):
            말 = "서사연결.%s — 가정 파일에 그 번호의 값이 없어 「Narrative와 입력값」 표에서 뺐다" % k
            if 말 not in 맥.알림:
                맥.알림.append(말)
            continue
        문 = v if isinstance(v, str) else (v or {}).get("문장")
        열 = (v or {}).get("열") if isinstance(v, dict) else None
        if not _글(문):
            continue
        같은 = next((x for x in 줄들 if x["문장"] == 문.strip()), None)
        if 같은:
            같은["번호들"].append("%s" % k)
            if 열:
                같은["열들"] = list(dict.fromkeys((같은.get("열들") or []) + list(열)))
        else:
            줄들.append({"문장": 문.strip(), "번호들": ["%s" % k], "열들": list(열) if 열 else None})
    return 줄들


def 신호들(맥):
    return [x for x in (맥.가정.get("신호") or []) if isinstance(x, dict) and _글(x.get("신호"))]


def 신호가정(맥, x):
    """신호 x 가 고치게 할 가정 번호 — 「가정」 번호 목록, 없으면 「고칠가정」 글의 항목(「 · 」 로 나눈 것)을 가정 이름(워크북 이름에서
    매출 구분 이름을 뗀 것)에 맞대어 찾는다(R1b · L9 · L10). WACC 는 「WACC」."""
    import 레터 as _L                                       # noqa: PLC0415
    if x.get("가정"):
        return ["%s" % y for y in x.get("가정") or []]
    글 = _글(x.get("고칠가정"))
    if not 글:
        return []
    항목 = [t.strip() for t in re.split(r"\s·\s|,", 글) if t.strip()]
    구분들 = sorted({("%s" % (y.get("이름") or "")).strip() for y in 맥.구.get("매출구분") or []} - {""}, key=len, reverse=True)
    낸 = []
    번들 = sorted(set(list(맥.가정.get("가정") or {}) + list(맥.가정.get("시점가정") or {})) | {"WACC"}, key=lambda b: (len(b), b))
    for 번 in 번들:
        if 번 != "WACC" and not 번.isdigit():
            continue
        이름 = "WACC" if 번 == "WACC" else (_L.가정이름(번, 맥.구, 원래=True) or "")
        뗀 = next((이름[len(g) + 1:] for g in 구분들 if 이름.startswith(g + " ")), 이름)
        if any(t and (t == 뗀 or t in 이름 or 뗀.endswith(t)) for t in 항목):
            낸.append(번)
    return 낸


def 신호글(맥, 번호들, 고르기=False, 뺄=()):
    """v27 — 번호들(그 신호가 고치게 할 가정 · `신호가정`)에 묶인 첫 신호 → (신호, 「문턱은」, 문턱) 또는 None. 고르기면 번호 대신 3분 레터의
    신호 고르기(`레터3분.신호고르기`)의 첫 신호. 뺄 = 이미 다른 줄이 쓴 신호의 차례(같은 신호를 두 줄에 싣지 않는다)."""
    import 레터3분 as T                                     # noqa: PLC0415
    if 고르기:
        신 = T.신호고르기(맥)[:1]
    else:
        번 = {"%s" % b for b in 번호들 or []}
        신 = [(i, x) for i, x in enumerate(신호들(맥)) if 번 & set(신호가정(맥, x))] if 번 else []
    for i, x in 신:
        if i in 뺄:
            continue
        이 = 펴기(맥, x.get("신호"), "신호[%d].신호" % i, 어림=True)
        문턱 = 펴기(맥, x.get("문턱"), "신호[%d].문턱" % i, 어림=True) if _글(x.get("문턱")) else ""
        if 이:
            맥._신호차례 = i
            return (이.rstrip("."), "문턱은", 문턱.rstrip("."))
    return None


def 틀릴가정(맥):
    """v27 — 「가장 먼저 틀릴 가정」 → (이름, 번호들, 지렛대와 같나). 작성자가 `Narrative.틀림.가정` 으로 선언했고 지렛대(값 폭 1위)가 그 선언이 아니면
    (선언보다 넓은 다른 가정 · 선언을 품은 묶음) 선언한 가정이다 — 「먼저 틀릴 가정」 은 작성자의 판단이고 「값을 가장 크게 가르는 가정」 은 셈이다.
    선언이 없거나 지렛대가 곧 선언이면 지렛대. 지렛대가 없으면 (None, [], True)."""
    d = 지렛대(맥)
    if not d:
        return None, [], True
    s = d.get("선언") or {}
    if s.get("이름"):
        return s["이름"], ["%s" % b for b in s.get("번호들") or []], False
    return d["이름"], ["%s" % b for b in d.get("번호들") or []], True


def _신호이름(맥, 번호들):
    낸 = []
    for i, x in enumerate(신호들(맥)):
        if set(신호가정(맥, x)) & set(번호들):
            낸.append(펴기(맥, x.get("신호"), "신호[%d].신호" % i))
    return [x for x in 낸 if x]


# ══════════════════════════════════════════════════════════════════ 5. 절

def _민감첫(맥):
    """민감도 표 Ⅲ 에서 주당가치를 가장 크게 움직이는 손잡이 → (i, 표3 줄) 또는 None.
    저자가 값을 가르는 축(`Narrative.틀림.가정`)을 선언했고 그 가정이 표 Ⅲ 의 손잡이 대상이면 그 줄을 쓴다 — 결론 · 3분 레터 · 민감도 절의
    「값을 가르는 가정」 이 Narrative ③ 과 같은 말을 하게(견본 실측: ③ 은 정상 수준인데 3분 레터 · 14절은 WACC)."""
    표3 = (맥.민 or {}).get("표3") or []
    틀 = (맥.가정.get("Narrative") or {}).get("틀림") if isinstance(맥.가정.get("Narrative"), dict) else None
    선 = {"%s" % x for x in ((틀 or {}).get("가정") or [])} if isinstance(틀, dict) else set()
    for i, r in enumerate(표3):
        기 = _n(r.get("기준"))
        쪽 = [_n(r.get(k)) for k in ("하", "상") if _n(r.get(k)) is not None]
        if 선 and 기 and 쪽 and set("%s" % t for t in (r.get("대상") or [])) & 선:
            return (i, r, max(abs(v / 기 - 1) for v in 쪽))
    낸 = None
    for i, r in enumerate(표3):
        기 = _n(r.get("기준"))
        쪽 = [_n(r.get(k)) for k in ("하", "상")]
        if not 기 or all(v is None for v in 쪽):
            continue
        크기 = max(abs(v / 기 - 1) for v in 쪽 if v is not None)
        if 낸 is None or 크기 > 낸[2]:
            낸 = (i, r, 크기)
    return 낸


def 민감첫이름(맥):
    """값을 가르는 가정의 이름 — 지렛대(`지렛대` · 2026-10-25 R3). 이름은 결론 · 민감도 · 3분이 같은 말이다."""
    d = 지렛대(맥)
    return d["이름"] if d else None


def _독자드라이버(맥, i, r, h):
    """독자 층(3막)의 Value driver 문장 — 지수 폭 대신 기준 기간 = 100 과 돈(주당가치가 얼마 오르내리나)으로.
    「값을 가르는 Value driver는 웨이퍼 한 장으로 버는 돈의 바닥이다. 바닥(2026년 2분기 = 100)이 범용 DRAM 33 → 31 · NAND 22 → 21로
    내려가면 주당가치는 6.9만 원 내린다. 범용 DRAM 33 → 35 · NAND 22 → 24로 올라가면 6.9만 원 오른다.」 정상 수준이 아닌 손잡이는 폭을
    그대로(%p · % · 년 — 지수 꼴이면 폭 없이 「민감도 절의 폭만큼」) 적는다. WACC 와 견줄 때도 돈으로."""
    import 레터1부 as P                                    # noqa: PLC0415
    기 = "R:기준:2.DCF:68"
    v기 = _n(r.get("기준"))
    백 = P.백폭(맥, i, h)
    이름 = P.독자손잡이이름(맥, h) if 백 else P.손잡이이름(h, 맥)
    쪽들 = []                                               # (k, 돈 글, 동사 끝 「내린다」 · 「오른다」, 크기)
    for k in ("하", "상"):
        v = _n(r.get(k))
        if v is None or v기 is None:
            continue
        내림 = v < v기
        돈 = 맥.식(["−", 기, "민:표3:%d:%s" % (i, k)] if 내림 else ["−", "민:표3:%d:%s" % (i, k), 기], "어림주당")
        쪽들.append((k, 돈, "내립니다" if 내림 else "오릅니다", abs(v - v기)))
    if not 쪽들:
        return []
    L = ["주당가치를 가장 크게 좌우하는 가정은 %s." % P.입니다(이름)]
    if 백:
        for n, (k, 돈, 끝, _크기) in enumerate(쪽들):
            길 = "%s %s" % (P.으로(백[k + "길"]), "내려가면" if k == "하" else "올라가면")
            if n == 0:
                L.append("다른 가정을 그대로 두고 정상 수준(%s = 100)이 %s 주당가치는 %s %s." % (백["기간"], 길, 돈, 끝))
            else:
                L.append("%s %s %s." % (길, 돈, 끝))
    else:
        폭 = ("민감도 절의 폭만큼" if P.지수꼴인가(P.손잡이꼴(h, 맥)) and h.get("방식") != "배율"
             else P.폭말(h, "민:표3:%d:폭" % i, 맥))
        L.append("%s 바꾸면 주당가치는 %s." % (폭, ", ".join("%s %s" % (돈, "내리고" if 끝 == "내립니다" else "오르고") for _k, 돈, 끝, _c in 쪽들[:-1])
                                            + (", " if len(쪽들) > 1 else "") + "%s %s" % (쪽들[-1][1], 쪽들[-1][2])))
    크기 = max(c for _k, _d, _e, c in 쪽들)
    for j, w in enumerate((맥.민 or {}).get("표3") or []):
        if j != i and ["%s" % x for x in w.get("대상") or []] == ["WACC.예측기간", "WACC.영구기간"]:
            if _n(w.get("하")) is not None and _n(w.get("상")) is not None and _n(w.get("기준")) is not None:
                wh = {"이름": w["이름"], "대상": w["대상"], "방식": w.get("방식")}
                w크기 = max(abs(_n(w["하"]) - _n(w["기준"])), abs(_n(w["상"]) - _n(w["기준"])))
                L.append("이 폭은 할인율을 %s 바꿀 때 주당가치가 달라지는 %s · %s보다 %s." % (
                    P.폭말(wh, "민:표3:%d:폭" % j, 맥), 맥.식(["−", "민:표3:%d:하" % j, 기], "어림주당"),
                    맥.식(["−", 기, "민:표3:%d:상" % j], "어림주당"), "큽니다" if 크기 >= w크기 else "작습니다"))
            break
    return L


def 동인글(맥, 층):
    """저자 선언 `Narrative.동인` {"독자": [글], "깊이": [글]} — 가치 동인을 같은 잣대로 견준 문장(통독 v3 상3). 있으면 자동 문장 대신 쓴다."""
    d = (맥.가정.get("Narrative") or {}).get("동인")
    if not isinstance(d, dict) or not isinstance(d.get(층), list):
        return []
    return [x for x in (펴기(맥, g, "Narrative.동인.%s[%d]" % (층, k), 어림=(층 == "독자")) for k, g in enumerate(d[층])) if x]


def Value드라이버문장(맥):
    """민감도 절 머리(· 옛 3막) — 「값을 가르는 가정은 {지렛대}다. 그 가정만 … 옮기면 주당가치는 a에서 b까지 움직인다.」 + 같은 방법으로 WACC 를 옮긴 폭.
    2026-10-25 R3 — 결론 · 3분 레터 · 결합 민감도 · 격자와 같은 가정(`지렛대`)을 쓴다(종전에는 민감도 표 Ⅲ 의 첫 손잡이라 증가율 경로 회사에서 WACC 로 떨어졌다).
    저자가 같은 잣대로 견준 문장(`Narrative.동인`)이 있으면 지렛대 문장 뒤에 그 글을 잇는다."""
    import 레터1부 as P                                    # noqa: PLC0415
    꼴 = "어림주당" if P.독자층(맥) else "주당"
    L = 지렛대문장(맥, 꼴)
    저 = 동인글(맥, "독자" if P.독자층(맥) else "깊이")
    if 저:
        return L + 저
    return L + WACC견줌(맥, 꼴)


def 요약문단(맥):
    """1. 요약을 여는 문단(제안 2.1) — 계기 · 질문 · 기준 시나리오의 Narrative · 값 · Value driver · 비관 · 낙관 · 종가가 담은 Narrative.
    Narrative 의 글이 없으면 빈 목록(요약은 지금 꼴의 첫 문장으로 연다). R1b — 주당가치는 반올림(L16), 종가는 배수 없이 값으로(L12),
    단순 역산은 평가 모델 밖의 셈이라고 문장에 적는다(L17)."""
    import 레터1부 as P                                    # noqa: PLC0415
    N = 맥.가정.get("Narrative") or {}
    if not isinstance(N, dict) or not any(_글(N.get(k)) for k in ("계기", "질문", "한줄")):
        return []
    L = []
    문 = [x for x in (펴기(맥, N.get("계기"), "Narrative.계기"),) if x]
    질 = 펴기(맥, N.get("질문"), "Narrative.질문")
    if 질:
        문.append(질)                                         # v27 — 예고 문장(「이 평가가 묻는 것은 하나다」)은 싣지 않는다
    if 문:
        L += [" ".join(문), ""]
    한 = 펴기(맥, N.get("한줄"), "Narrative.한줄")
    값 = 펴기(맥, N.get("값으로"), "Narrative.값으로")
    주당 = 맥.수("R:기준:2.DCF:68", "어림주당")
    끝 = "기준 시나리오의 주당가치는 약 %s." % P.입니다(주당)
    if 한:
        L += ["이 레터는 %s 기준 시나리오로 삼았습니다.%s %s" % (P.을(한.rstrip(".")), (" " + 값) if 값 else "", 끝), ""]
    else:
        L += [끝, ""]
    v = Value드라이버문장(맥)
    if v:
        L += [" ".join(v), ""]
    이름 = ((맥.가정.get("서술") or {}).get("이름") or {})
    둘 = []
    for s in ("비관", "낙관"):
        나 = 맥.원고글(이름.get(s), "서술.이름.%s" % s) if _글(이름.get(s)) else ""
        둘.append("%s 시나리오%s의 주당가치는 약 %s" % (s, ("(%s)" % 나) if 나 else "", 맥.수("R:%s:2.DCF:68" % s, "어림주당")))
    L += ["같은 회사를 다르게 본 Narrative 둘도 주당가치로 계산했습니다. %s, %s." % (둘[0], P.입니다(둘[1])), ""]
    if 맥.종가키:
        종 = 맥.종가키
        문 = ["%s %s." % (P.은(P.종가말(맥)), P.입니다(맥.수(종, "어림주당")))]
        문 += 역산축문장(맥)
        L += [" ".join(문), ""]
        가 = 펴기(맥, N.get("가격"), "Narrative.가격")
        if 가:
            L += ["이 가격은 %s에 가깝습니다. 이 레터는 그 Narrative가 맞는지 판정하지 않습니다. 그쪽으로 옮겨 가는지 알려 줄 신호를 정리했습니다(%s)." % (
                가.rstrip("."), P.곳(맥, 맥.절.get("이야기점검", 0))) if 맥.절.get("이야기점검") else
                "이 가격은 %s에 가깝습니다. 이 레터는 그 Narrative가 맞는지 판정하지 않습니다." % 가.rstrip("."), ""]
    return L


def 역산축문장(맥):
    """요약의 Reverse DCF 문장 — 선언한 역산 축 하나만 풀었을 때 이 가격에 필요한 값(정상 수준이면 기준 기간 눈으로).
    R1b(L17) — 전사 단순 역산은 평가 모델 밖의 셈이라고 문장에 적는다."""
    import 레터1부 as P                                    # noqa: PLC0415
    줄들 = P._표4줄들(맥)
    if not 줄들:
        return []
    r = 줄들[0]
    if r["내재"] is None:
        return ["다른 가정은 그대로 두고 Reverse DCF로 %s 하나만 풀면 뜻이 있는 범위 안에서 이 가격이 성립하는 값이 없습니다." % r["이름"]]
    L = ["다른 가정은 그대로 두고 Reverse DCF로 %s 하나만 풀었습니다." % r["이름"]]
    눈 = P._정상눈금(맥, r)
    낙 = None
    if r["h"]["대상"] and ("%s" % r["h"]["대상"][0]).isdigit():
        import 레터 as _L                                   # noqa: PLC0415
        번 = "%s" % r["h"]["대상"][0]
        if _n(_L._시점값(맥.가정, 번, "낙관")) is not None:
            낙 = 맥.수("S:%s:낙관" % 번, r["꼴"])
    if 눈:
        L.append("이 가격에 필요한 정상 수준은 %s의 %s 아니라 %s." % (
            눈["기간"], P.이("%s(%s)" % (" · ".join(눈["적용"]), " · ".join(눈["구분"]))), P.입니다(" · ".join(눈["내재"]))))
        if 낙:
            높 = _n(맥.값(r["키"])) > _n(맥.값("S:%s:낙관" % r["h"]["대상"][0]))
            L.append("지수로는 %s%s, 낙관 시나리오의 %s보다도 %s." % (눈["지수"], P._조(눈["지수"], "이고", "고"), 낙, "높습니다" if 높 else "낮습니다"))
        else:
            L.append("지수로는 %s." % P.입니다(눈["지수"]))
    else:
        L.append("이 가격에 필요한 %s %s." % (P.은(r["이름"]), P.입니다(r["내재"])))
    if r["비고"]:
        L.append("%s." % r["비고"])
    if _n(맥.값("가:성장:증가율")) is not None and _n(맥.값("가:성장:모델")) is not None:     # S9-03 — 같은 엔진의 매출성장 역산
        L.append("매출로 보면 예측기간 매출 연평균 증가율이 %s 대신 %s여야 합니다(원가 비율 · 재투자 · Terminal Value의 셈은 모델 그대로)." % (
            맥.수("가:성장:모델", "퍼1"), 맥.수("가:성장:증가율", "퍼1")))
    return L


def 생애주기문단(맥):
    import 레터1부 as P                                    # noqa: PLC0415
    생 = (맥.메타 or {}).get("생애주기")
    if not isinstance(생, dict) or 생.get("단계") not in 단계들:
        return []
    회사 = ("%s" % (맥.메타.get("회사명") or "이 회사")).strip()
    덧 = 생.get("덧표지") or []
    위치 = 맥.원고글(생.get("위치"), "메타.생애주기.위치") if _글(생.get("위치")) else ""
    종류 = "경기순환 기업" if "경기순환" in 덧 else "원자재 기업" if "원자재" in 덧 else "금융 회사" if "금융" in 덧 else "회사"
    글 = "그래서 이 레터는 %s Life cycle로는 %s%s에 있는 %s 봅니다." % (
        P.을(회사), 생["단계"], (", 업황으로는 %s" % 위치) if ("경기순환" in 덧 and 위치) else "", P.으로(종류))
    N = 맥.가정.get("Narrative") if isinstance(맥.가정.get("Narrative"), dict) else {}
    if _글(N.get("값의원천")):
        원천 = 펴기(맥, N.get("값의원천"), "Narrative.값의원천")
    elif _글(생.get("값의원천")):
        원천 = 맥.원고글(생.get("값의원천"), "메타.생애주기.값의원천")
    else:
        원천 = _값의원천기본.get(생["단계"], "")
        # 1.1.21 — 정상 수준으로 값을 낸 회사(경기순환 · 원자재 표지 · 판매단가를 정상 수준으로 되돌리는 매출 구분)에 「지금의 이익」 을 쓰면 레터의 산정 방식과 어긋난다(맥 읽기 삼성전자)
        정상 = any(x in ("경기순환", "원자재") for x in 덧) or any(
            isinstance(x, dict) and x.get("단가경로") == "수렴" for x in ((맥.구 or {}).get("매출구분") or []))
        if 정상 and 원천 and "지금의 이익" in 원천:
            원천 = 원천.replace("지금의 이익", "업황이 정상 수준으로 돌아온 뒤의 이익")
    if 원천:
        글 += " 이런 회사의 값은 %s에서 나옵니다." % 원천.rstrip(".")
    L = [글]
    if any(x in ("경기순환", "원자재") for x in 덧) and _글(생.get("가격변수")):
        변 = 맥.원고글(생.get("가격변수"), "메타.생애주기.가격변수")
        L.append("이 평가에는 %s의 정상 수준을 보는 견해가 들어 있습니다." % 변)
    return [" ".join(L), ""]


def 틀림문장(맥):
    """「이 Narrative가 틀린다면 가장 먼저 틀릴 가정은 {}다.」 + 민감도 범위 한 문장 — (문장들, 가정 이름)."""
    import 레터1부 as P                                    # noqa: PLC0415
    N = 맥.가정.get("Narrative") or {}
    틀 = N.get("틀림") if isinstance(N, dict) else None
    이름 = 틀릴가정(맥)[0]                                 # 1.1.19 — 결론 표 「틀림」 줄과 같은 가정(선언보다 넓은 후보가 지렛대가 되면 지렛대가 아니라 선언)
    if not 이름:
        return [], None
    L = ["이 Narrative가 틀린다면 가장 먼저 틀릴 가정은 %s." % P.입니다(이름)]
    t5 = (맥.민 or {}).get("표5")
    if t5:
        값들 = [(i, j) for i in range(len(t5["세로값"])) for j in range(len(t5["가로값"])) if _n(t5["값"][i][j]) is not None]
        if 값들:
            lo = min(값들, key=lambda ij: t5["값"][ij[0]][ij[1]])
            hi = max(값들, key=lambda ij: t5["값"][ij[0]][ij[1]])
            세, 가 = 표2이름(맥)
            꼴 = "어림주당" if P.독자층(맥) else "주당"
            L.append("%s의 표에서 %s %s 함께 바꾸면 주당가치는 %s에서 %s까지 달라집니다." % (
                ("민감도" if P.독자층(맥) else P.곳(맥, 맥.절["민감도"])) if 맥.절.get("민감도") else "민감도 절", P.과(세), P.을(가), 맥.수("민:표5:값:%d:%d" % lo, 꼴),
                맥.수("민:표5:값:%d:%d" % hi, 꼴)))
    return L, 이름


def 값밖문단(맥):
    """M10 — Narrative에 들었지만 값에는 넣지 않은 것. 저자 글(Narrative.값밖)이 있으면 그것을, 없으면 가격 성립 입력의 증설 ·
    부록 G 의 시나리오 전용 가정에서 짓는다."""
    import 레터1부 as P                                    # noqa: PLC0415
    N = 맥.가정.get("Narrative") or {}
    글들 = []
    for i, x in enumerate((N.get("값밖") or []) if isinstance(N, dict) else []):
        g = 펴기(맥, x if isinstance(x, str) else (x or {}).get("글"), "Narrative.값밖[%d]" % i)
        if g:
            글들.append(g)
    if not 글들:
        증 = [맥.원고글(x.get("이름"), "가격성립.증설.%d.이름" % i) for i, x in enumerate((맥.가성 or {}).get("증설") or [])]
        증 = [x for x in 증 if x]
        if 증 and 맥.절.get("역산"):                         # 부록 G 안내는 빼고(절 안내는 한 절에 둘까지 — 구조검수)
            글들.append("%s 기준 시나리오에서 빼고 따로 계산했습니다(%d절)." % (P.은(P._나열(증)), 맥.절["역산"]))
        뒤 = (맥.부록 or {}).get("기준일뒤자료") if isinstance(맥.부록, dict) else None
        뒤 = [x for x in 뒤 or [] if isinstance(x, dict)]
        if 뒤 and importlib.import_module("기준일").자료경계(맥.가정)["이월"]:
            뒤 = []                                          # 날짜 둘 판 — 재무 자료 기준일과 평가기준일 사이 자료는 값에 쓴 정보라 「값에 넣지 않은 것」 목록에 두지 않는다(부록 G 가 밝힌다)
        if 뒤:                                               # R1b(L13) — 시나리오마다의 건수를 다 적는다(기준 시나리오에 쓴 자료도)
            셈 = [(시, sum(1 for x in 뒤 if 시 in (x.get("시나리오") or []))) for 시 in ("기준", "낙관", "비관")]
            글들.append("평가기준일 뒤에 나온 실적 · 통계 자료는 가정 %d건에 참고했습니다(%s)." % (       # 통독 v3 중-9 — 뺀 증설과 가른다
                len(뒤), " · ".join("%s 시나리오 %d건" % (시, n) for 시, n in 셈 if n)))
    if not 글들:
        return []
    return ["Narrative에는 들어 있지만 주당가치 계산에는 넣지 않은 내용도 있습니다. %s" % " ".join(g if g.endswith(".") else g + "." for g in 글들), ""]


def _연결점수(맥, 번호들):
    """Narrative와 입력값 표의 줄이 값을 얼마나 움직이나 — 민감도 표 Ⅲ 의 손잡이(± 폭)와 시나리오 폭포(가정 묶음의 한 걸음) 가운데 큰 것
    (기준 주당가치 대비). 둘 다 없으면 0 — 본문의 다섯 줄을 고르는 데만 쓴다(R1b · L10)."""
    import 레터 as _L                                       # noqa: PLC0415
    기 = _n(맥.값("R:기준:2.DCF:68")) or 1.0
    점 = 0.0
    for r in (맥.민 or {}).get("표3") or []:
        대 = ["%s" % x for x in r.get("대상") or []]
        묶 = set(번호들) & set(대) or ("WACC" in 번호들 and 대 == ["WACC.예측기간", "WACC.영구기간"])
        if 묶:
            for k in ("하", "상"):
                if _n(r.get(k)) is not None:
                    점 = max(점, abs(_n(r[k]) / 기 - 1))
    걸음 = 폭포걸음(맥)
    for (이름, 번들), 크기 in 걸음.items():
        if set(번들) & set(번호들):
            점 = max(점, 크기 / 기)
    return 점


def 폭포걸음(맥):
    """{(묶음 이름, (번호 …)): 비관 · 낙관 폭포의 그 묶음 걸음 가운데 큰 절댓값} — 값을 움직이는 줄 고르기에 쓴다(장부에 적지 않는다)."""
    if hasattr(맥, "_폭포걸음"):
        return 맥._폭포걸음
    import 레터 as _L                                       # noqa: PLC0415
    낸 = {}
    묶음 = _L.폭포묶음(맥.가정, 맥.구)
    for 시 in ("비관", "낙관"):
        앞 = _n(맥.값("R:기준:2.DCF:68"))
        for k, (이름, 번들) in enumerate(묶음):
            v = _n(맥.값("가:폭포:%s:%d" % (시, k)))
            if v is None or 앞 is None:
                continue
            키 = (이름, tuple(번들))
            낸[키] = max(낸.get(키, 0.0), abs(v - 앞))
            앞 = v
    맥._폭포걸음 = 낸
    return 낸



# ══════════════════════════════════════════════════════════════════ 4-2. 지렛대 — 값을 가장 크게 가르는 가정 하나(2026-10-25 레터 재구성 R3 · 계약 0절 2)
# 결론(1절 「갈림」 줄) · 민감도 절 머리 · 3분 레터 · 결합 민감도 손잡이 · 인터랙티브 격자 손잡이가 모두 이 함수의 답을 쓴다. 게이트 ⑮ 가 자리마다 같은지 센다.
# 잣대 하나 — 「그 가정 하나만 근거 범위의 양 끝으로 옮기고 다른 가정은 기준 그대로 둘 때 주당가치가 움직이는 폭 ÷ 기준 주당가치」(토네이도 · 결합 민감도와 같은 잣대).
#   근거 범위 — 시나리오가 가른 가정은 그 가정의 비관 · 낙관 시나리오 값(저자가 근거로 정한 이야기의 양 끝 · 장부 키 「가:홀로」),
#              민감도 표 Ⅲ 의 손잡이는 선언한 「범위」 가 있을 때만(근거 범위). 관행 폭(±1%p 따위)만 있는 손잡이는 근거 범위 후보가 하나도 없을 때만 쓴다.
# 고르는 차례 — ① 저자가 `Narrative.틀림.가정` 으로 선언한 가정(값을 가르는 축은 저자가 지목한다) ② 근거 범위 후보 가운데 폭이 가장 큰 것
#   ③ 관행 폭 손잡이 가운데 폭이 가장 큰 것. 폭포 걸음(묶음 차례에 따라 값이 달라진다) 대신 「하나만 옮기기」 를 쓴다 — 차례를 타지 않는다.

_보간끝 = {"비관": -1.0, "기준": 0.0, "낙관": 1.0}


def _연도꼴(*vs):
    return all(_n(v) is not None and float(_n(v)).is_integer() and 1900 <= _n(v) <= 2200 for v in vs)


영구시점번호 = ("212", "213", "219")        # 한 값 가정 가운데 영구기간에만 닿는 칸(영구성장률 · Normalization 영업이익률 · 영구기간 ROIC) — 열 거르개 「영구」 에 든다


def _영구열ID():
    try:
        return importlib.import_module("기간축").영구ID
    except Exception:                                        # noqa: BLE001
        return "TV"


def 시나리오보간(가정, 번들, t, 바탕=None, 열=None):
    """번들(가정 · 시점가정 번호)의 기준 시나리오 값을 t 만큼 옮긴 사본 — t = −1 이면 비관 값, +1 이면 낙관 값(그 시나리오의 칸 그대로), 0 이면 기준,
    그 사이 · 바깥은 열마다 선형(연도 칸은 정수로 반올림). 바탕(이미 다른 손잡이를 옮긴 가정)을 주면 그 위에 쓴다. 세 시나리오 값은 원래 가정에서 읽는다.
    세 값 가운데 하나라도 비면 그 칸은 그대로 둔다. 장부 키 「가:홀로」 · 결합 민감도 · 민감도 격자가 같은 함수로 옮긴다(엔진 산식은 그대로 — 기준 칸만 바꾼다).
    v27(R5 P1) — 열 거르개: 열 = None · 「전부」 면 모든 칸, 「예측」 이면 열별 가정의 영구기간 열 밖의 칸만, 「영구」 면 영구기간 열만 옮긴다.
    한 값 가정(시점가정)은 「전부」 에서만 옮기고, 영구기간에만 닿는 칸(`영구시점번호`)은 「영구」 에서도 옮긴다(「예측」 에서는 기준 그대로)."""
    a = copy.deepcopy(바탕 if 바탕 is not None else 가정)
    끝 = {1.0: "낙관", -1.0: "비관"}.get(float(t))
    열 = None if 열 in (None, "", "전부") else 열
    if 열 not in (None, "예측", "영구"):
        raise ValueError("열 거르개는 전부 · 예측 · 영구 가운데 하나입니다: %s" % 열)
    영 = _영구열ID()

    def 든다(c):
        return 열 is None or ((c == 영) if 열 == "영구" else (c != 영))

    def 새(b, lo, hi):
        v = b + t * ((hi - b) if t >= 0 else (b - lo))
        return int(round(v)) if _연도꼴(b, lo, hi) else v
    for 번 in ("%s" % x for x in 번들):
        원벌 = (가정.get("가정") or {}).get(번)
        if isinstance(원벌, dict) and "공통" not in 원벌 and isinstance(원벌.get("기준"), dict):
            벌 = (a.get("가정") or {}).get(번)
            if not isinstance(벌, dict):
                continue
            if 끝 and isinstance(원벌.get(끝), dict):
                if 열 is None:
                    벌["기준"] = copy.deepcopy(원벌[끝])
                elif isinstance(벌.get("기준"), dict):
                    for c, v in 원벌[끝].items():
                        if 든다(c):
                            벌["기준"][c] = copy.deepcopy(v)
                continue
            if not isinstance(벌.get("기준"), dict):
                continue
            for c, b in 원벌["기준"].items():
                if not 든다(c):
                    continue
                lo, hi = (원벌.get("비관") or {}).get(c), (원벌.get("낙관") or {}).get(c)
                if all(_n(v) is not None for v in (b, lo, hi)):
                    벌["기준"][c] = 새(_n(b), _n(lo), _n(hi))
            continue
        원시 = (가정.get("시점가정") or {}).get(번)
        if isinstance(원시, dict) and "공통" not in 원시 and isinstance((a.get("시점가정") or {}).get(번), dict):
            if 열 == "예측" or (열 == "영구" and 번 not in 영구시점번호):
                continue
            if 끝 and 끝 in 원시:
                a["시점가정"][번]["기준"] = copy.deepcopy(원시[끝])
                continue
            b, lo, hi = 원시.get("기준"), 원시.get("비관"), 원시.get("낙관")
            if all(_n(v) is not None for v in (b, lo, hi)):
                a["시점가정"][번]["기준"] = 새(_n(b), _n(lo), _n(hi))
    return a


def 홀로가정(가정, 번들, 시, 열=None):
    """번들만 시나리오 시 의 값으로 둔 기준 가정(다른 가정은 기준 그대로) — 장부 키 「가:홀로:<시>:<번+번>」(레터 · 게이트가 같은 함수로 셈한다).
    열(v27) — 「예측」 · 「영구」 면 그 열만 옮긴다(장부 키 「가:홀로열:<시>:<예측 | 영구>:<번+번>」)."""
    return 시나리오보간(가정, 번들, _보간끝[시], 열=열)


def _번차례(번들):
    return sorted(("%s" % b for b in 번들), key=lambda x: (len(x), x))


def 홀로키(시, 번들):
    return "가:홀로:%s:%s" % (시, "+".join(_번차례(번들)))


def 홀로열키(시, 열, 번들):
    """v27(R5 P1) — 번들의 시나리오 시 값을 예측기간 열(「예측」) 또는 영구기간 열(「영구」)에만 옮긴 주당가치의 장부 키."""
    return "가:홀로열:%s:%s:%s" % (시, 열, "+".join(_번차례(번들)))


def 열갈리나(가정, 번들):
    """번들 가운데 예측 · 영구로 가를 수 있는 가정(열별 가정 · 영구기간에만 닿는 한 값 가정)이 있나 — 없으면 「예측만 · 영구만」 셈을 싣지 않는다."""
    for 번 in ("%s" % b for b in 번들):
        벌 = (가정.get("가정") or {}).get(번)
        if isinstance(벌, dict) and "공통" not in 벌 and isinstance(벌.get("기준"), dict):
            return True
        if 번 in 영구시점번호 and 번 in (가정.get("시점가정") or {}):
            return True
    return False


def 가를수없는한값(가정, 번들):
    """번들 가운데 예측 · 영구로 가르지 못하는 한 값 가정(모든 기간에 같이 닿는 계수 따위) — 「예측만 · 영구만」 셈에서 기준 그대로 둔 번호."""
    시 = 가정.get("시점가정") or {}
    return [b for b in _번차례(번들) if b in 시 and b not in 영구시점번호 and _변동(가정, b)]


# ── v27(R5 P4) — 딸린행: 시나리오 축(driver)이 물고 움직이는 줄(`시나리오이야기.<쪽>.딸린행`). 그 줄만 따로 옮긴 주당가치는 「다른 가정은 기준 그대로」 가
#    성립하지 않는다(매출 경로에서 셈한 칸 · 축과 같이 가는 수준) — 홀로 귀속(절 머리 폭 · 지렛대 후보)에 싣지 않고 축과 묶는다. 선언이 없으면 종전과 같다.

def _선언번호(이야, 키):
    return {("%s" % x).replace("A-", "").strip() for x in (이야.get(키) or []) if ("%s" % x).replace("A-", "").strip()}


def 축딸린(가정):
    """→ (축 번호 합집합, 딸린 번호 합집합) — 비관 · 낙관 시나리오 이야기의 driver · 딸린행(어느 쪽이든 driver 인 번호는 딸린에서 뺀다)."""
    이야 = 가정.get("시나리오이야기") if isinstance(가정.get("시나리오이야기"), dict) else {}
    축, 딸 = set(), set()
    for 시 in ("비관", "낙관"):
        x = 이야.get(시) if isinstance(이야.get(시), dict) else {}
        축 |= _선언번호(x, "driver")
        딸 |= _선언번호(x, "딸린행")
    return 축, 딸 - 축


def 딸림묶음(가정, 번들):
    """번들이 모두 딸린행이고 어느 시나리오의 축(driver)도 들지 않았나 — 참이면 홀로 귀속을 싣지 않는다(축과 묶는다)."""
    축, 딸 = 축딸린(가정)
    번 = {"%s" % b for b in 번들}
    return bool(번) and 번 <= 딸 and not (번 & 축)


def 딸림뺀(가정, 번들):
    """v27(R5 P4) — 홀로 귀속을 셀 번들 → (남은 번호, 뺀 딸린 번호). 번들에 축(driver)이 들면 같은 묶음의 딸린행도 함께 옮긴다(축 + 딸린 — 그대로),
    축이 없으면 딸린행 번호를 뺀다(그 줄만 따로 옮기면 「다른 가정은 기준 그대로」 가 성립하지 않는다). 차례는 그대로."""
    축, 딸 = 축딸린(가정)
    번 = ["%s" % b for b in 번들]
    if set(번) & 축:
        return 번, []
    return [b for b in 번 if b not in 딸], [b for b in 번 if b in 딸]


def 귀속문턱(가정=None):
    """레터 v27 P2 · P5 · P9 — 귀속 상대 문턱(기준 주당가치 대비 몫 · 정합설정 「귀속.상대문턱」 · 기본 0.001)."""
    import 레터 as _L                                       # noqa: PLC0415
    return _L.귀속설정()["상대문턱"]


def 움직임(v, 기, 문=None):
    """기준 기 대비 v 의 쪽 → −1 · 0 · +1(상대 문턱 `귀속문턱` 안이면 0)."""
    v, 기 = _n(v), _n(기)
    if v is None or 기 is None:
        return 0
    문 = 귀속문턱() if 문 is None else 문
    if abs(v - 기) <= 문 * max(abs(기), 1e-12):
        return 0
    return 1 if v > 기 else -1


def _변동(가정, 번):
    import 레터 as _L                                       # noqa: PLC0415
    return ("%s" % 번).isdigit() and _L._변동(가정, "%s" % 번)


def _지렛대설정():
    try:
        return (importlib.import_module("레터정합").설정().get("지렛대")) or {}
    except Exception:                                        # noqa: BLE001
        return {}


_대안이름 = {"βU": "Unlevered Beta 산정 방법", "WACC": "WACC 산정 방법", "영구": "영구기간 자본비용"}     # 1.1.19 — 「사양」 은 도구 안의 말(결론 표 · 본문에 섰다)


def 대안후보(가정, 원=None):
    """1.1.7 — 할인율 대안 사양을 지렛대 후보로(같은 잣대 — 그 사양만 바꾸고 다른 가정은 기준 그대로 둔 주당가치의 폭). → [{"묶음", "꼴", "키들", "대상"}].
      자본비용 대안(가정 「자본비용」 · 없으면 레터부록 — 부록 B 와 같은 읽기): βU 로 댄 대안은 「대안β:<βU>:주당」 · WACC 로 댄 대안은 「대안:<예측>:<영구>」
      영구기간 자본비용 판(`_raw/안정성장.json` 「영구베타.판」 — 업종 성숙 평균 · Levered Beta 1.0 · 수렴 없음): 「파일:안정성장:영구베타:판:i:주당」
    키들의 첫째는 채택(기준 시나리오 주당가치)이다 — 폭은 채택과 대안 가운데 가장 낮은 값 ~ 가장 높은 값. 설정 「지렛대.대안사양」 이 거짓이면 빈 목록."""
    if not _지렛대설정().get("대안사양", True):
        return []
    import 자본비용옮기기 as _자본                               # noqa: PLC0415
    기 = "R:기준:2.DCF:68"
    낸 = []
    try:
        입, _출, _알 = _자본.읽기(가정, (원 or {}).get("부록"))
    except Exception:                                        # noqa: BLE001
        입 = None
    점 = []
    for x in ((입 or {}).get("대안") or []) if isinstance(입, dict) else []:
        if not isinstance(x, dict):
            continue
        if _n(x.get("βU")) is not None and _n(x.get("예측기간WACC")) is None:
            점.append(("대안β:%r:주당" % _n(x["βU"]), "βU"))
        elif _n(x.get("예측기간WACC")) is not None:
            예, 영 = _n(x["예측기간WACC"]), _n(x.get("영구기간WACC"))
            점.append(("대안:%r:%r" % (예, 예 if 영 is None else 영), "WACC"))
    if 점:
        낸.append({"묶음": "할인율 대안 사양", "꼴": "βU" if all(f == "βU" for _k, f in 점) else "WACC",
                  "키들": [기] + list(dict.fromkeys(k for k, _f in 점)), "대상": ["WACC.예측기간", "WACC.영구기간"]})
    판 = (((((원 or {}).get("파일") or {}).get("안정성장") or {}).get("영구베타") or {}).get("판")) or []
    키 = ["파일:안정성장:영구베타:판:%d:주당" % i for i, x in enumerate(판) if isinstance(x, dict) and _n(x.get("주당")) is not None]
    if 키:
        낸.append({"묶음": "영구기간 자본비용", "꼴": "영구", "키들": [기] + 키, "대상": ["WACC.영구기간"]})
    return 낸


def 지렛대셈(가정, 구, 민, 값, 원=None):
    """「값을 가장 크게 가르는 가정」 → {"대상", "번호들", "원천"(선언 · 후보), "잣대"(시나리오 · 범위 · 대안 · 관행 · None), "하키", "상키", "폭", "가장큼",
    "표3"(민감도 표 Ⅲ 의 줄 · 없으면 None), "후보"(근거 범위 후보 — 폭 큰 차례), "선언"(1.1.7 — 선언보다 넓은 후보가 이겼을 때 그 선언)} 또는 None.
    값 = 장부 키 → 값(레터는 `맥.값`, 게이트 · 결합 민감도 · 격자는 `레터.키풀기(키, 원)`). 원 = 부록 입력 · 재료 파일(대안 사양 후보 — `대안후보`).
    장부에 적지 않는다 — 글은 `지렛대문장` 이 적는다. 이름은 `지렛대(맥)`.
    1.1.7 — 대안 사양(자본비용 대안 · 영구기간 자본비용 판)을 같은 잣대(「대안」 — 채택과 대안 가운데 가장 낮은 · 높은 주당가치의 폭)로 후보에 넣고,
    선언한 지렛대보다 폭이 큰 근거 범위 후보(선언과 겹치지 않는)가 있으면 폭 1위를 고른다(설정 「지렛대.선언보다넓으면」 = 1위 · 「선언」 이면 종전)."""
    import 레터 as _L                                       # noqa: PLC0415
    기 = _n(값("R:기준:2.DCF:68"))
    후보 = []
    for c in 대안후보(가정, 원):
        점 = []
        for k in c["키들"]:
            try:
                v = _n(값(k))
            except Exception:                                # noqa: BLE001
                v = None
            if v is not None:
                점.append((v, k))
        if 기 and len(점) >= 2 and max(점)[0] > min(점)[0]:
            후보.append({"잣대": "대안", "묶음": c["묶음"], "번호들": ["WACC"], "대상": list(c["대상"]), "하키": min(점)[1], "상키": max(점)[1],
                       "폭": (max(점)[0] - min(점)[0]) / abs(기), "표3": None, "대안꼴": c["꼴"]})
    for 묶, 번들 in _L.폭포묶음(가정, 구):
        번들, _뺀 = 딸림뺀(가정, 번들)                          # v27(R5 P4) — 축이 물고 가는 딸린행은 홀로 옮긴 폭을 후보에 넣지 않는다(축이 든 묶음은 그대로)
        if not 번들:
            continue
        하키, 상키 = 홀로키("비관", 번들), 홀로키("낙관", 번들)
        lo, hi = _n(값(하키)), _n(값(상키))
        if 기 and lo is not None and hi is not None:
            후보.append({"잣대": "시나리오", "묶음": 묶, "번호들": ["%s" % b for b in 번들], "대상": ["%s" % b for b in 번들], "하키": 하키, "상키": 상키,
                       "폭": abs(hi - lo) / abs(기), "표3": None})
    for i, r in enumerate((민 or {}).get("표3") or []):
        lo, hi = _n(r.get("하")), _n(r.get("상"))
        if not 기 or lo is None or hi is None:
            continue
        대 = ["%s" % x for x in r.get("대상") or []]
        번 = [d for d in 대 if d.isdigit()] or (["WACC"] if 대 and all(d.startswith("WACC") for d in 대) else [])
        후보.append({"잣대": "범위" if r.get("범위") else "관행", "묶음": r.get("이름"), "번호들": 번, "대상": 대, "하키": "민:표3:%d:하" % i,
                   "상키": "민:표3:%d:상" % i, "폭": abs(hi - lo) / abs(기), "표3": i})
    근 = sorted([c for c in 후보 if c["잣대"] in ("시나리오", "범위", "대안")], key=lambda c: -c["폭"])
    관 = sorted([c for c in 후보 if c["잣대"] == "관행"], key=lambda c: -c["폭"])
    N_ = 가정.get("Narrative") if isinstance(가정.get("Narrative"), dict) else {}
    틀 = N_.get("틀림") if isinstance(N_.get("틀림"), dict) else {}
    선 = list(dict.fromkeys("%s" % x for x in (틀.get("가정") or []) if "%s" % x))
    고른 = None
    if 선:
        if any(s.startswith("WACC") for s in 선):
            c = next((c for c in 근 + 관 if c["대상"] and all(d.startswith("WACC") for d in c["대상"])), None)
            고른 = dict(c, 번호들=["WACC"]) if c else {"잣대": None, "번호들": ["WACC"], "대상": ["WACC"], "하키": None, "상키": None, "폭": None, "표3": None}
        else:
            갈 = [s for s in 선 if _변동(가정, s)]
            if 갈:
                하키, 상키 = 홀로키("비관", 갈), 홀로키("낙관", 갈)
                lo, hi = _n(값(하키)), _n(값(상키))
                고른 = {"잣대": "시나리오", "번호들": 선, "대상": 선, "하키": 하키, "상키": 상키, "표3": None,
                       "폭": (abs(hi - lo) / abs(기)) if (기 and lo is not None and hi is not None) else None}
            else:
                c = next((c for c in 근 + 관 if set(c["번호들"]) & set(선)), None)
                고른 = dict(c, 번호들=선) if c else {"잣대": None, "번호들": 선, "대상": 선, "하키": None, "상키": None, "폭": None, "표3": None}
        고른["원천"] = "선언"
        일위 = (_지렛대설정().get("선언보다넓으면") or "1위") == "1위"
        선판 = None
        if 일위 and 고른.get("폭") is not None and 고른.get("잣대") == "시나리오":
            # v27 — 선언한 가정을 품은 더 넓은 시나리오 묶음(같은 뜻의 가정을 매출 구분마다 묶은 것)이 더 넓으면 그 묶음이 지렛대다(선언은 그 일부).
            #   종전에는 「선언과 겹친다」 고 그 묶음을 빼고 선언과 무관한 다음 후보가 지렛대가 됐다
            갈번 = {"%s" % s for s in 선 if _변동(가정, s)}
            품 = [c for c in 근 if c["잣대"] == "시나리오" and 갈번 <= set(c["번호들"]) and set(c["번호들"]) - 갈번]
            if 품 and 품[0]["폭"] > 고른["폭"] + 1e-12:
                선판 = {k: 고른.get(k) for k in ("잣대", "번호들", "대상", "하키", "상키", "폭", "표3")}
                고른 = dict(품[0], 원천="후보", 선언=선판, 품음=True)
        넓 = [c for c in 근 if not (set(c["번호들"]) & set(고른["번호들"]))]       # 선언(또는 선언을 품은 묶음)과 무관한 다른 가정만 견준다
        if 일위 and 고른.get("폭") is not None and 넓 and 넓[0]["폭"] > 고른["폭"] + 1e-12:
            선판 = 선판 or {k: 고른.get(k) for k in ("잣대", "번호들", "대상", "하키", "상키", "폭", "표3")}
            고른 = dict(넓[0], 원천="후보", 선언=선판)              # 1.1.7 — 같은 잣대로 선언보다 넓은 후보(폭 1위)가 첫 장의 지렛대
    elif 근 or 관:
        고른 = dict((근 or 관)[0], 원천="후보")
    if not 고른:
        return None
    남 = [c for c in 근 if not (set(c["번호들"]) & set(고른["번호들"]))]
    고른["가장큼"] = bool(고른.get("폭") is not None and 고른.get("잣대") in ("시나리오", "범위", "대안") and 남
                     and all(고른["폭"] >= c["폭"] - 1e-12 for c in 남))
    고른["후보"] = [{k: c.get(k) for k in ("잣대", "묶음", "번호들", "대상", "하키", "상키", "폭", "표3", "대안꼴")} for c in 근]
    return 고른


def 지렛대(맥):
    """이 레터의 지렛대(`지렛대셈`) + 이름 — 한 번 셈해 맥에 둔다(결론 · 민감도 · 3분이 같은 답을 쓴다). 없으면 None."""
    if hasattr(맥, "_지렛대"):
        return 맥._지렛대
    d = 지렛대셈(맥.가정, 맥.구, 맥.민, 맥.값, 원=getattr(맥, "원", None))
    if d:
        d["이름"] = 지렛대이름(맥, d)
        d["이름들"] = list(dict.fromkeys([d["이름"]] + [가정말(맥, b) for b in d["번호들"] if b != "WACC" and b.isdigit()]))
        if d.get("선언"):
            d["선언"]["이름"] = 지렛대이름(맥, d["선언"])
    맥._지렛대 = d
    return d


def 표3손잡이(가정):
    """엔진 민감도 표 Ⅲ(손잡이 줄만 — 격자는 셈하지 않는다)을 `표다섯` 의 표3 꼴로 — 맥 없이 지렛대를 셈할 때(결합 민감도 · 민감도 격자)."""
    import importlib                                          # noqa: PLC0415
    M = importlib.import_module("엔진.민감도")
    return [{"이름": r["이름"], "폭": r["폭"], "방식": r["손잡이"].get("방식", "가산"), "대상": r["손잡이"]["대상"], "하값": r.get("하값"),
             "기준값": r["기준값"], "상값": r.get("상값"), "하": r.get("하"), "기준": r["기준"], "상": r.get("상"), "범위": r.get("범위")}
            for r in M.민감도(가정, "기준")]


def 지렛대독립(가정, 가정경로=None):
    """맥 없이 지렛대를 셈한다 — 레터 앞 단계 도구(결합 민감도 · 민감도 격자)가 레터와 같은 가정을 손잡이로 넣는다(게이트 ⑮ 가 센다).
    선언(Narrative.틀림.가정)이 시나리오가 가른 가정이고 설정이 종전(「선언」)이면 민감도 표 Ⅲ 을 셈하지 않는다(1.1.7 기본 「1위」 는 선언보다 넓은
    범위 손잡이가 있는지 보아야 하므로 늘 셈한다). 가정경로를 주면 곁의 `_raw/안정성장.json`(영구기간 자본비용 판 — 대안 후보)을 읽는다.
    → 지렛대 dict(+ 이름 · 이름들) 또는 None."""
    import importlib                                          # noqa: PLC0415
    import types                                              # noqa: PLC0415
    import 레터 as _L                                       # noqa: PLC0415
    _오, _경, 구, _축 = importlib.import_module("엔진.스키마").검증전부(가정)
    파일 = {}
    q = os.path.join(os.path.dirname(os.path.abspath(가정경로)), "_raw", "안정성장.json") if 가정경로 else None
    if q and os.path.isfile(q):
        try:
            파일["안정성장"] = json.load(io.open(q, encoding="utf-8"))
        except (OSError, ValueError):
            pass
    원 = _L.원천만들기(가정, 표다섯=False, 파일=파일)
    원["민"] = {"표3": []}
    d = 지렛대셈(가정, 구, 원["민"], lambda k: _L.키풀기(k, 원), 원=원)
    종전 = (_지렛대설정().get("선언보다넓으면") or "1위") != "1위"
    if not (종전 and d and d.get("원천") == "선언" and d.get("잣대") == "시나리오"):
        원["민"] = {"표3": 표3손잡이(가정)}
        원.pop("_가성", None)
        d = 지렛대셈(가정, 구, 원["민"], lambda k: _L.키풀기(k, 원), 원=원)
    if d:
        맥 = types.SimpleNamespace(구=구, 가정=가정, 민=원["민"])
        d["이름"] = 지렛대이름(맥, d)
        d["이름들"] = list(dict.fromkeys([d["이름"]] + [가정말(맥, b) for b in d["번호들"] if b != "WACC" and b.isdigit()]))
    return d


_엔진손잡이말 = {"영구ROIC": "영구기간 ROIC", "매출성장": "예측기간 매출 증가율", "목표마진": "예측 끝 영업이익률", "영구이익률가감": "영구기간 영업이익률",
             "비영업할인": "비영업자산 할인율"}


def 손잡이본편이름(구, 대상, 바탕=None):
    """손잡이 대상 → 본편 가정 표의 이름(결합 민감도 · 격자 손잡이 — 화면 글에 내부 번호 「A-182」 를 내지 않는다 · 2026-10-25 R3).
    가정 번호면 가정 이름(매출 구분 이름만 다른 것은 묶음), WACC 대상이면 「WACC」, 엔진 전용 대상이면 그 뜻의 이름, 모르면 바탕 이름에서 번호를 걷은 것."""
    import types                                              # noqa: PLC0415
    맥 = types.SimpleNamespace(구=구 or {})
    대 = [("%s" % d).replace("A-", "") for d in 대상 or []]
    번 = [d for d in 대 if d.isdigit()]
    if 번:
        return 이름묶기(맥, list(dict.fromkeys(가정말(맥, b) for b in 번)))
    if 대 and all(d.startswith("WACC") for d in 대):
        return "WACC"
    if 대 and 대[0] in _엔진손잡이말:
        return _엔진손잡이말[대[0]]
    글 = re.sub(r"\s*\(A-[\d\s+A-]+\)|A-\d+\s*", "", "%s" % (바탕 or "")).strip()
    return 이름다듬기(글) or " · ".join(대)


def 지렛대이름(맥, d):
    """지렛대의 본편 이름 — 가정 번호면 가정 표의 이름(매출 구분 이름만 다른 것은 묶는다), WACC 면 「WACC」, 엔진 전용 손잡이면 민감도 표의 이름."""
    import 레터1부 as P                                    # noqa: PLC0415
    번 = [b for b in d.get("번호들") or [] if b.isdigit()]
    if d.get("잣대") == "대안":                               # 1.1.7 — 할인율 대안 사양 · 영구기간 자본비용 판
        return _대안이름.get(d.get("대안꼴"), _대안이름["WACC"])
    if "WACC" in (d.get("번호들") or []):
        return "WACC"
    if 번:
        return 이름묶기(맥, [가정말(맥, b) for b in 번])
    if d.get("표3") is not None:
        r = 맥.민["표3"][d["표3"]]
        return 이름다듬기(P.손잡이이름({"이름": r["이름"], "대상": r["대상"], "방식": r.get("방식")}, 맥))
    return 이름다듬기(" · ".join(d.get("대상") or []))


def 가정지시(d):
    """1.1.21 — 지렛대 이름의 가정 수에 맞춘 지시어 「이 가정」 · 「이 두 가정」(이름은 「 · 」 로 묶인다 — `이름묶기`)."""
    n = len([x for x in ("%s" % ((d or {}).get("이름") or "")).split(" · ") if x.strip()])
    return "이 %s가정" % ({2: "두 ", 3: "세 ", 4: "네 "}.get(n, "")) if n >= 2 else "이 가정"


def 지렛대폭글(맥, d, 꼴="주당"):
    """지렛대를 근거 범위 양 끝으로 옮긴 주당가치 「a에서 b까지」(낮은 쪽 먼저 · 장부에 적는다)와 무엇으로 옮겼는지의 말 → (옮김 말, 값 글) 또는 None."""
    import 레터1부 as P                                    # noqa: PLC0415
    if not d or not d.get("하키") or not d.get("상키"):
        return None
    a, b = _n(맥.값(d["하키"])), _n(맥.값(d["상키"]))
    if a is None or b is None:
        return None
    낮, 높 = (d["하키"], d["상키"]) if a <= b else (d["상키"], d["하키"])
    if d.get("잣대") == "시나리오":                            # v27 교열 270 — 「옮기다 · 움직이다」 대신 「바꾸다 · 달라지다」
        말 = "%s만 비관 · 낙관 시나리오의 값으로 바꾸고 다른 가정은 기준 시나리오대로 두면" % 가정지시(d)
    elif d.get("표3") is not None:
        r = 맥.민["표3"][d["표3"]]
        h = {"이름": r["이름"], "대상": r["대상"], "방식": r.get("방식")}
        if d.get("잣대") == "범위":
            말 = "%s만 근거 범위(%s)의 끝 값으로 바꾸고 다른 가정은 기준 시나리오대로 두면" % (가정지시(d), P.폭글(h, "민:표3:%d:폭" % d["표3"], 맥))
        else:
            말 = "%s만 %s 다른 가정은 기준 시나리오대로 두면" % (가정지시(d), 폭바꿈말(P.폭말(h, "민:표3:%d:폭" % d["표3"], 맥), "고"))
    elif d.get("잣대") == "대안":                             # 1.1.7 — 채택 사양과 대안 사양 가운데 가장 낮은 · 높은 주당가치
        말 = ("영구기간 자본비용만 할인율 절에서 비교한 세 가지 값으로 바꾸고 다른 가정은 기준 시나리오대로 두면" if d.get("대안꼴") == "영구"
             else "할인율만 부록 B의 대안 산정 방법으로 바꾸고 다른 가정은 기준 시나리오대로 두면")
    else:
        return None
    return 말, "%s에서 %s까지" % (맥.수(낮, 꼴), 맥.수(높, 꼴))


def 폭바꿈말(폭, 끝="면"):
    """v27 — 폭(「0.50%p」 · 「8.0%~12.0% 사이에서」)만큼 가정을 바꾸는 말 — 「0.50%p 높이거나 낮추면」 · 「8.0%~12.0% 사이에서 바꾸면」(끝 「고」 면 「…낮추고」)."""
    return ("%s 바꾸%s" if 폭.endswith("사이에서") else "%s 높이거나 낮추%s") % (폭, 끝)


def 지렛대문장(맥, 꼴="주당", 앞="주당가치를 좌우하는 가정은"):
    """「주당가치를 좌우하는 가정은 X입니다. 이 가정만 … 바꾸면 주당가치는 a에서 b까지 달라집니다.」 (+ 근거 범위 후보 가운데 가장 큰 때 그 사실) — 문장 목록."""
    import 레터1부 as P                                    # noqa: PLC0415
    d = 지렛대(맥)
    if not d:
        return []
    L = ["%s %s." % (앞, P.입니다(d["이름"]))]
    폭 = 지렛대폭글(맥, d, 꼴)
    if 폭:
        L.append("%s 주당가치는 %s 달라집니다." % 폭)
        if d.get("가장큼"):                                   # v27 교열 172
            대 = any(c.get("잣대") == "대안" for c in d.get("후보") or [])
            L.append("%s은 %s 하나씩 바꿔 본 가정 가운데 주당가치가 가장 크게 달라졌습니다." % (
                가정지시(d), "근거 범위와 대안 산정 방법으로" if 대 else "근거 범위로"))
        L += 선언견줌(맥, d, 꼴)
    return L


def 선언견줌(맥, d, 꼴="주당"):
    """1.1.7 — 같은 잣대로 선언(Narrative.틀림.가정)보다 넓은 후보가 지렛대가 됐을 때, 선언한 가정을 같은 방법으로 옮긴 폭 한 문장 — 없으면 빈 목록."""
    s = (d or {}).get("선언") or {}
    폭 = 지렛대폭글(맥, s, 꼴) if s.get("하키") and s.get("상키") else None
    if not 폭 or not s.get("이름"):
        return []
    말 = {"시나리오": "비관 · 낙관 시나리오의 값으로 바꾸면", "범위": "근거 범위의 끝 값으로 바꾸면"}.get(s.get("잣대"), "같은 방법으로 바꾸면")
    return ["먼저 틀릴 가정으로 본 %s만 %s 주당가치는 %s 달라집니다." % (s["이름"], 말, 폭[1])]


def WACC견줌(맥, 꼴="주당"):
    """지렛대가 WACC 가 아니면 같은 방법으로 WACC 를 옮긴 폭 한 문장(민감도 표 Ⅲ 의 WACC 줄) — 없으면 빈 목록."""
    import 레터1부 as P                                    # noqa: PLC0415
    d = 지렛대(맥)
    if d and "WACC" in (d.get("번호들") or []):
        return []
    for j, w in enumerate((맥.민 or {}).get("표3") or []):
        if ["%s" % x for x in w.get("대상") or []] == ["WACC.예측기간", "WACC.영구기간"] and _n(w.get("하")) is not None and _n(w.get("상")) is not None:
            h = {"이름": w["이름"], "대상": w["대상"], "방식": w.get("방식")}
            a, b = _n(w["하"]), _n(w["상"])
            낮, 높 = ("민:표3:%d:하" % j, "민:표3:%d:상" % j) if a <= b else ("민:표3:%d:상" % j, "민:표3:%d:하" % j)
            return ["다른 가정은 바꾸지 않고 WACC만 %s 주당가치는 %s에서 %s까지 달라집니다." % (      # v27 교열 276
                폭바꿈말(P.폭말(h, "민:표3:%d:폭" % j, 맥)), 맥.수(낮, 꼴), 맥.수(높, 꼴))]
    return []


# ══════════════════════════════════════════════════════════════════ 4-3. 결론 다섯 줄 — 판정 문장의 앞 넷 + 신호와 다음 점검(2026-10-25 레터 재구성 R2 · 계약 0절 3)
# 본편 1절 · 3분 레터 맨 앞 · 인터랙티브 머리가 이 함수의 글을 싣는다(같은 함수 · 같은 장부 키 · 한 번 셈해 맥에 둔다). 다섯째 줄(비싸다 · 싸다 · 판단 보류)의
# 자리에는 신호와 다음 점검이 선다 — 권유어(목표주가 · 저평가 · 고평가 · 매수 · 매도 · 상승 여력 · 적정가치)는 쓰지 않는다. 숫자는 모두 장부 키다.
#   (v27 문장 단계 — 합쇼체 · 교열 3 · 264 · 268 ~ 270 · 본보기 「종가 … 전제한다 → … 같아집니다」)
#   값   기준 시나리오의 주당가치는 약 {기준}입니다. 비관 시나리오에서는 약 {a}, 낙관 시나리오에서는 약 {b}입니다. {범위 밖} {시나리오 한 줄}
#   가격 다른 가정을 그대로 두고 {가정}만 높이면(낮추면), {역산 값}일 때 주당가치가 {날짜} 종가 {P}와 같아집니다.
#        기준 시나리오의 {가정}은 {기준 값}입니다(5단계 — 「{날짜} 종가는 {P}입니다」 를 따로 찍지 않는다 · 3분 레터는 종가를 표에 둔다). 수준 경로면 정상 수준 역산, 증가율 경로면 역산 표 Ⅳ 의 「종가에 맞는 영구기간 영업이익률」 줄
#        (없으면 유형 기본 축 · 풀린 첫 줄). 종가가 세 시나리오 범위 밖이면 「{종가}는 {조건}에 대한 판단입니다」 틀. 종가가 없으면 지운다.
#   갈림 주당가치를 (가장 크게) 좌우하는 가정은 {지렛대}입니다. 이 가정만 … 바꾸고 … 두면 주당가치는 {x}에서 {y}까지 달라집니다
#        (`지렛대` — 결론 · 민감도 · 3분 · 결합 · 격자가 같은 가정).
#   근거 {근거 — 독자근거 → 서사연결 → 절글 「범위」 문단의 첫 문장} 이를 근거로 {지렛대 첫 가정}의 기준 시나리오 값을 정했습니다.
#   틀림 {Narrative.틀림.길} 먼저 확인할 지표는 {신호}이고, 임계치는 {문턱}입니다. 다음 점검은 {다음점검} 뒤입니다.
# 원고가 없어 서지 않는 줄(근거 · 틀림)은 지운다 — 원고 요건(`레터원고` · R1)이 그 자리를 요구한다. 이 함수는 지어내지 않는다.
결론자리 = ("값", "가격", "갈림", "근거", "틀림")
# 레터 v27 5단계(3분 레터) — 결론 줄의 문장은 몫을 가진다(`결론부분`). 본편 1절은 몫과 상관없이 줄의 문장을 모두 싣는다(장부 · 인터랙티브 머리가
# 읽는 글은 그대로). 3분 레터는 「표」 몫을 맨 위 핵심 숫자 표의 칸으로 옮기고(`삼분결론`) 「글」 몫만 문장으로 싣는다.
#   표    어느 회사에나 있는 사실 — 세 시나리오의 주당가치 · 날짜와 종가 · 주당가치를 좌우하는 가정과 그 폭 · 다음 점검
#   글    그 회사의 판단과 까닭 — 시나리오 한 줄 · 범위 밖 · 주가가 뜻하는 조건 · 근거 · 판단이 틀리는 경우 · 먼저 확인할 지표
#   본편  본편 1절에만 싣는 문장 — 표의 숫자를 되풀이하거나(「그 조건이 성립하지 않으면 …」) 근거 뒤의 맺음 · 다른 절을 가리키는 문장
# 핵심 숫자 표의 줄 이름(게이트 ⑯ 이 줄 이름으로 결론 자리를 찾는다 — `결론표자리`)
결론표머리 = {"기준": "주당가치(기준 시나리오)", "범위": "비관 시나리오 · 낙관 시나리오",
           "가정": ("주당가치를 가장 크게 좌우하는 가정", "주당가치를 좌우하는 가정"), "다음": "다음 점검"}
# 3분 레터에 문장으로 싣지 않는 결론 문장의 표지(「표」 · 「본편」 몫) — 게이트 ⑯ 이 본편 1절 줄에서 3분 레터에 와야 할 문장만 가른다
결론삼분밖 = ("기준 시나리오의 주당가치는", "비관 시나리오에서는 약", "좌우하는 가정은", "다른 가정은 기준 시나리오대로 두면 주당가치는",
          "먼저 틀릴 가정으로 본", "다음 점검은", "에 대한 판단입니다", "그 조건이 성립하지 않으면", "기준 시나리오 값을 정했습니다",
          "값을 정한 근거는",
          # 1.1.21 — 종가 위치 · 주가가 뜻하는 조건(역산) · 반대 논거 · 먼저 볼 지표는 3분 레터 결론 표의 줄로 싣는다(`삼분결론`)
          "세 시나리오 범위 밖에 있으며", "세 시나리오 주당가치의 범위(", "일 때 주당가치가", "다른 가정을 그대로 두면 예측기간 매출이", "그 경우 ",
          "시장에서 제시되는 논거", "먼저 확인할 지표는")
# 줄 찾기 머리(게이트 ⑯ `레터문장._결론줄찾기` · 인터랙티브 `레터인터랙티브._결론자르기`) — 앞이 v27 글, 뒤는 옛 판 레터를 읽을 때의 옛 머리
결론머리 = {"값": ("기준 시나리오의 주당가치는", "이 가정들에서 계산한 주당가치는"),
          "가격": ("다른 가정을 그대로 두고", "에 대한 판단입니다", "세 시나리오 주당가치의 범위(", "다른 가정을 그대로 둘 때", "가정 하나만 풀어서는", "에 대한 판단이다"),
          "갈림": ("좌우하는 가정은", "갈리는 지점은", "값을 가르는 가정은"),
          "근거": ("기준 시나리오 값을 정했습니다", "기준 시나리오 값을 정한 근거", "기준 시나리오의 값으로 둔 근거는"),
          "틀림": ("먼저 확인할 지표는", "다음 점검은", "이 판단이 틀린다면")}
판단머리 = "에 대한 판단입니다"                                # 1.1.6 — 종가가 세 시나리오 범위 밖일 때 [가격] 줄의 틀(게이트 ⑯ · 인터랙티브 머리가 이 말로 줄을 찾는다)
_형용줄기 = ("높", "낮", "같", "많", "적", "작", "좁", "넓", "짧", "얕", "깊", "멀", "가깝")     # 「…습니다」 로 끝나는 형용사 줄기 → 「…은」


def _받침(c):
    n = ord(c) - 0xAC00
    return n % 28 if 0 <= n <= 11171 else -1


def _받침뗌(c):
    n = ord(c) - 0xAC00
    return chr(ord(c) - n % 28) if 0 <= n <= 11171 else c


def 경우글(글):
    """v27 — 임계치 · 경보 기준 글을 「…입니다」 의 보어로. 명사구면 그대로, 합쇼체 · 평서체 문장이면 관형형 + 「경우」
    (「출시가 두 분기 넘게 밀립니다」 → 「출시가 두 분기 넘게 밀리는 경우」). 모르는 꼴이면 낫표로 감싼다."""
    g = (글 or "").strip().rstrip(".")
    if not g.endswith("다"):
        return g
    m = re.search(r"(\S+)$", g)
    w, 앞 = m.group(1), g[:m.start()]
    if w.endswith("입니다") and w not in ("보입니다", "줄입니다", "높입니다", "늘입니다"):
        관 = w[:-3] + "인"
    elif w.endswith("습니다"):
        관 = w[:-3] + ("은" if w[:-3].endswith(_형용줄기) else "는")
    elif w.endswith("니다") and len(w) >= 3 and _받침(w[-3]) == 17:            # ㅂ니다 — 밀립니다 → 밀리는 · 하락합니다 → 하락하는
        관 = w[:-3] + _받침뗌(w[-3]) + "는"
    elif w.endswith("는다") and len(w) >= 3:                                   # 넘는다 → 넘는
        관 = w[:-1]
    elif len(w) >= 2 and _받침(w[-2]) == 4:                                    # ㄴ다 — 밀린다 → 밀리는
        관 = w[:-2] + _받침뗌(w[-2]) + "는"
    else:
        return "「%s」" % g
    return "%s%s 경우" % (앞, 관)


def 종가문(맥):
    """v27 — 「{날짜} 종가는 {P}입니다.」(옛 [가격] 줄의 첫 문장 — 5단계부터 결론 줄은 이 문장을 따로 찍지 않고 `종가와` 로 조건 문장 안에 둔다)."""
    import 레터1부 as P                                    # noqa: PLC0415
    return "%s %s." % (P.은(P.종가말(맥)), P.입니다(맥.수(맥.종가키, "어림주당")))


def 종가와(맥):
    """5단계 — 「{날짜} 종가 {P}와」(조건 문장의 비교 대상). 3분 레터는 종가를 표에 두므로 「이 주가」 가 가리킬 앞 문장이 없다 — 날짜와 값을 문장에 넣는다."""
    import 레터1부 as P                                    # noqa: PLC0415
    return "%s %s" % (P.종가말(맥), P.과(맥.수(맥.종가키, "어림주당")))


def 잇기(부분):
    """결론 줄의 부분 [(몫, 글, 이름)] → 본편 1절의 글(몫과 상관없이 모든 문장)."""
    return " ".join(x[1] for x in 부분 if x[1])


def 바꿈쪽(내, 적, 오름="높이면", 내림="낮추면", 같음="바꾸면"):
    """v27 — 역산값(내)이 채택값(적)보다 높으면 「높이면」, 낮으면 「낮추면」(문장 원칙 6 — 방향은 낱말로)."""
    import 어투                                              # noqa: PLC0415
    a, b = _n(내), _n(적)
    return 같음 if a is None or b is None else 어투.방향(a - b, 오름, 내림, 같음)


def _문장끝(g):
    g = (g or "").strip()
    return (g if g.endswith(".") else g + ".") if g else ""


def 결론가격(맥):
    """[가격] 줄의 글(본편 1절) — `결론가격부분` 의 문장을 모두 잇는다. → 글 또는 ""."""
    return 잇기(결론가격부분(맥))


def 결론가격부분(맥):
    """[가격] 줄 → [(몫, 글, 이름)] — 종가가 세 시나리오 범위 밖이면 「이 가격은 ○○ 에 대한 판단이다」 틀(1.1.6 — `결론판단틀부분`), 범위 안이면 종전 틀:
    수준 경로는 정상 수준을 푼 역산, 증가율 경로는 역산 표 Ⅳ 의 영구기간 영업이익률 줄(없으면 유형 기본 · 풀린 첫 줄). 종가가 없으면 []."""
    if not getattr(맥, "종가키", None):
        return []
    import 레터갭 as _갭                                     # noqa: PLC0415
    쪽 = _갭.범위(맥)
    if 쪽 in ("위", "아래"):
        틀 = 결론판단틀부분(맥, 쪽)                            # 쓰지 않을 종전 글을 먼저 짓지 않는다(장부에 실리지 않은 숫자가 남는다 — 게이트 ⑦)
        if 틀:
            return 틀
    return _결론가격옛부분(맥)


배어림한도 = 0.05                                             # 정수 배수가 값을 이만큼 넘게 바꾸면 정수로 찍지 않는다(1.825 → 「2배」 는 9.6% 바꾼다)


def 배어림꼴(v):
    """값 → 「배0」 또는 「배1」 — 정수 반올림이 값을 배어림한도 넘게 바꾸면(또는 0 으로 찍히면) 「배1」(정수로 찍을 수 없는 값).
    독자 층(3분 레터)은 소수 배수를 쓰지 않으므로(레터문장 「독자 층 배수」) 「배1」 이 나오면 배수 대신 차이를 퍼센트로 쓴다(`판단조건.세계`)."""
    v = _n(v)
    if v is None or v == 0:
        return "배0"
    정 = float(int(abs(v) + 0.5))
    return "배1" if (정 == 0 or abs(정 / abs(v) - 1) > 배어림한도) else "배0"


def 함축세계칸(맥, 머, 축들=()):
    """1.1.21 — `함축세계` 의 재료를 3분 레터 결론 표의 줄로 → [(줄 이름, 칸)](같은 장부 키 · 같은 꼴 — 게이트 ⑯ 이 본편 1절 줄의 숫자와 맞댄다)."""
    끝 = getattr(맥, "끝예측", None)
    기끝 = "R:기준:4.Sales:54:%s" % 끝 if 끝 else None
    기영 = _n(맥.값("R:기준:요약:영구기간영업이익률"))
    끝v, 기v = (_n(맥.값(머 + ":끝매출")), _n(맥.값(기끝))) if 기끝 else (None, None)
    낸 = []
    if 끝v is not None and 기v and abs(끝v / 기v - 1) > 0.05:
        if 배어림꼴(끝v / 기v) == "배0":
            덧 = "기준 시나리오의 %s" % 맥.식(["÷", 머 + ":끝매출", 기끝], "배0")
        else:
            덧 = "기준 시나리오보다 %s %s" % (맥.식(["괴리", 머 + ":끝매출", 기끝], "폭0"), "많음" if 끝v > 기v else "적음")
        낸.append(("그때 %s 매출" % 맥.열말(끝), "약 %s(%s)" % (맥.수(머 + ":끝매출", "어림금액"), 덧)))
    영v = _n(맥.값(머 + ":영구이익률"))
    if 영v is not None and "영구이익률가감" not in 축들 and (기영 is None or abs(영v - 기영) > 0.005):
        낸.append(("그때 영구기간 영업이익률", "약 %s" % 맥.수(머 + ":영구이익률", "퍼0")))
    return 낸


def 함축세계(맥, 머, 축들=()):
    """역세 키 머리 → 「{끝 해} 매출은 약 X로 기준 시나리오의 N배가 되고, 영구기간 영업이익률은 약 M가 됩니다」 (값이 없으면 빈 글). 기준과 거의 같은 값
    (매출 배수 ±5% 안 · 영구 영업이익률 ±0.5%p 안)과 푼 축 자신(영구기간 영업이익률 축)은 싣지 않는다. 1.1.19 — 정수 배수가 값을 5% 넘게 바꾸면
    배수 대신 차이를 퍼센트로(「기준 시나리오보다 83% 많아집니다」 — 3분 레터는 소수 배수를 쓰지 않는다 · 본편 「1.8배」 와 어긋나지 않게)."""
    import 레터1부 as P                                    # noqa: PLC0415
    끝 = getattr(맥, "끝예측", None)
    기끝 = "R:기준:4.Sales:54:%s" % 끝 if 끝 else None
    기영 = _n(맥.값("R:기준:요약:영구기간영업이익률"))
    끝v, 기v = (_n(맥.값(머 + ":끝매출")), _n(맥.값(기끝))) if 기끝 else (None, None)
    매 = (끝v is not None and 기v and abs(끝v / 기v - 1) > 0.05)
    영v = _n(맥.값(머 + ":영구이익률"))
    영 = 영v is not None and "영구이익률가감" not in 축들 and (기영 is None or abs(영v - 기영) > 0.005)
    매글, 매고, 매다 = "", "", ""
    if 매:
        머글 = "%s 매출은 약 %s 기준 시나리오" % (맥.열말(끝), P.으로(맥.수(머 + ":끝매출", "어림금액")))
        if 배어림꼴(끝v / 기v) == "배0":                    # 독자 층(3분 레터)은 정수 배수만 쓴다(레터문장 「독자 층 배수」)
            매글, 매고, 매다 = "%s의 %s" % (머글, P.이(맥.식(["÷", 머 + ":끝매출", 기끝], "배0"))), "되고", "됩니다"
        else:                                            # 1.1.19 — 정수로 찍으면 값이 크게 바뀐다(1.825 → 「2배」 대 본편 「1.8배」) — 차이를 퍼센트로
            많 = 끝v > 기v
            매글 = "%s보다 %s" % (머글, 맥.식(["괴리", 머 + ":끝매출", 기끝], "폭0"))
            매고, 매다 = ("많아지고", "많아집니다") if 많 else ("적어지고", "적어집니다")
    영글 = ("영구기간 영업이익률은 약 %s" % P.이(맥.수(머 + ":영구이익률", "퍼0"))) if 영 else ""
    if 매글 and 영글:
        return "%s %s, %s 됩니다" % (매글, 매고, 영글)
    return ("%s %s" % (매글, 매다)) if 매글 else ((영글 + " 됩니다") if 영글 else "")


def 판단조건(맥):
    """1.1.6 — 종가가 범위 밖일 때 「이 가격은 무엇에 대한 판단인가」 의 재료 → {"꼴", "이름", "글"} 또는 None. 차례(앞이 이긴다):
      하나   역산 표 Ⅳ 에서 실적 · 정상화 · 시나리오 범위 안에 풀린 축(종전 [가격] 줄이 고르는 축)
      둘     범위 끝에 한 가정을 두고 둘째 가정을 다시 푼 조합이 범위 안(`레터1부.두변수안`)
      성장   매출성장 축(가감 공간)의 풀이 — 범위 밖 판정이 아니고 성립 조건 밖 비고가 없을 때
    함축하는 세계(끝 해 매출 · 기준 대비 배수 · 영구기간 영업이익률)는 장부 키 「역세:…」 가 엔진으로 다시 셈한다(지어내지 않는다)."""
    import 레터1부 as P                                    # noqa: PLC0415
    import 레터3분 as T                                     # noqa: PLC0415
    if not getattr(맥, "민", None) or not (맥.민.get("표4") or {}).get("종가"):
        return None
    종, 종말 = 맥.종가키, P.종가말(맥)

    def 세계(머, 축들=()):
        return 함축세계(맥, 머, 축들)
    b = T.바닥(맥)
    if b and b["풀이"]:                                       # 수준 경로 — 정상 수준을 푼 역산(종전 글)이 곧 조건이다
        말 = T.가격말(맥, b)
        return {"꼴": "정상", "이름": "%s의 정상 수준" % 말,
                "글": "다른 가정을 그대로 두고 %s의 정상 수준만 바꾸면, %s(%s = 100)일 때 주당가치가 이 주가와 같아집니다. "
                      "기준 시나리오의 정상 수준은 %s." % (
                    말, T._백들(맥, b, {s: T._내(b, s) for s, _x in b["구분"]}), T.기간말(맥, b),
                    P.입니다(T._백들(맥, b, {s: "S:6%d6:기준" % s for s, _x in b["구분"]})))}
    줄들 = (맥.민.get("표4") or {}).get("줄") or []
    표4 = P._표4줄들(맥)
    for i, r in enumerate(줄들):
        if _n(r.get("내재값")) is None or ("%s" % (r.get("비고") or "")).strip():
            continue
        h = {"이름": r["이름"], "대상": r["대상"], "방식": r.get("방식")}
        if P.지수꼴인가(P.손잡이꼴(h, 맥)) or ["%s" % x for x in r.get("대상") or []] in (["매출성장"], ["목표마진"]):
            continue
        if P.역산판정(맥, 표4[i]) == "안":
            꼴 = P.손잡이꼴(h, 맥)
            이름 = 이름다듬기(P.손잡이이름(h, 맥))
            덧 = 세계("역세:%d" % i, ["%s" % x for x in r.get("대상") or []])
            return {"꼴": "하나", "이름": 이름,
                    "글": "다른 가정을 그대로 두고 %s만 %s, %s일 때 주당가치가 이 주가와 같아지며, 기준 시나리오의 값은 %s.%s" % (
                        이름, 바꿈쪽(r.get("내재값"), r.get("적용값")), 맥.수("민:표4:줄:%d:내재값" % i, 꼴),
                        P.입니다(맥.수("민:표4:줄:%d:적용값" % i, 꼴)), (" 그 경우 %s." % 덧) if 덧 else ""),
                    "표": [("이 주가와 같아지는 %s" % 이름, "%s(기준 시나리오 %s)" % (맥.수("민:표4:줄:%d:내재값" % i, 꼴), 맥.수("민:표4:줄:%d:적용값" % i, 꼴)))]
                          + 함축세계칸(맥, "역세:%d" % i, ["%s" % x for x in r.get("대상") or []])}
    안 = P.두변수안(맥)
    if 안:
        머 = "역세:%d:%d:%r" % (안["A"]["i"], 안["B"]["i"], float(안["v1"]))
        덧 = 세계(머, ["%s" % x for x in (안["A"]["h"]["대상"] or []) + (안["B"]["h"]["대상"] or [])])
        이름 = "%s %s" % (P.과(이름다듬기(안["A"]["이름"])), 이름다듬기(안["B"]["이름"]))
        return {"꼴": "둘", "이름": 이름,
                "글": "실적과 세 시나리오의 범위 안에서는 %s %s 두고 %s %s 두어야 주당가치가 이 주가와 같아집니다.%s" % (
                    P.을(이름다듬기(안["A"]["이름"])), P.으로(P._끝글(맥, 안["끝"])), P.을(이름다듬기(안["B"]["이름"])), P.으로(맥.수(안["키"], 안["B"]["꼴"])),
                    (" 그 경우 %s." % 덧) if 덧 else "")}
    for i, r in enumerate(줄들):
        if ["%s" % x for x in r.get("대상") or []] != ["매출성장"] or _n(r.get("내재값")) is None or _n(r.get("손잡이값")) is None:
            continue
        if ("%s" % (r.get("비고") or "")).strip() or P.역산판정(맥, 표4[i]) == "밖":
            continue
        덧 = 세계("역세:%d" % i)
        내키 = "민:표4:줄:%d:내재값" % i
        줄 = _n(r.get("내재값")) < 0                           # v27 — 방향은 낱말로(「−4%씩 늘어야」 대신 「4%씩 줄어야」)
        적키 = "민:표4:줄:%d:적용값" % i
        return {"꼴": "성장", "이름": "매출 성장과 이익률",
                "글": "다른 가정을 그대로 두면 예측기간 매출이 해마다 약 %s씩 %s 주당가치가 이 주가와 같아지며, %s.%s" % (
                    맥.식(["음", 내키], "퍼0") if 줄 else 맥.수(내키, "퍼0"), "줄어야" if 줄 else "늘어야",
                    ("기준 시나리오에서는 해마다 약 %s씩 줄어듭니다" % 맥.식(["음", 적키], "퍼0")) if (_n(맥.값(적키)) or 0) < 0     # 1.1.21 — 방향은 낱말로(원칙 6)
                    else "기준 시나리오의 같은 증가율은 %s" % P.입니다(맥.수(적키, "퍼0")), (" 그 경우 %s." % 덧) if 덧 else ""),
                "표": [("이 주가와 같아지는 예측기간 매출 연 증가율", "%s(기준 시나리오 %s)" % (_증가칸(맥, 내키), _증가칸(맥, 적키)))]
                      + 함축세계칸(맥, "역세:%d" % i)}
    return None


def _증가칸(맥, 키):
    """1.1.21 — 증가율 칸(결론 표) — 음수면 방향 낱말로(「약 4% 감소」 · 문장 원칙 6)."""
    v = _n(맥.값(키))
    return ("약 %s 감소" % 맥.식(["음", 키], "퍼0")) if (v is not None and v < 0) else ("약 %s" % 맥.수(키, "퍼0"))


# ── 1.1.19 반대 논거의 결합 줄 ───────────────────────────────────────────────────────────────────────────
# 원고가 반대 논거 목록에 「세 논거를 함께」 처럼 다른 논거의 바꿈을 묶은 줄을 넣으면 그 줄을 논거 하나로 세고(「논거 네 가지」) 장부 키 「반:합」 이
# 그 줄의 바꿈까지 겹쳐 더했다(가산 바꿈이 두 번 걸린다 — 실측 98,607원 대 바른 합 75,165원). 결합 줄은 낱말이 아니라 바꿈의 구조로 가른다.
# 15절 반대 논거 표(`레터1부`)도 이 함수들을 부른다 — 같은 판정을 두 벌 두지 않는다.

def _바꿈짝(b):
    """바꿈 하나 → 견줄 짝(가정 · 방식 · 값 · 열). 꼴이 어긋나면 None."""
    if not isinstance(b, dict) or b.get("가정") is None or _n(b.get("값")) is None:
        return None
    열 = tuple("%s" % c for c in b["열"]) if isinstance(b.get("열"), list) else None
    return ("%s" % b["가정"]).strip(), ("%s" % (b.get("방식") or "가산")).strip(), round(float(_n(b["값"])), 12), 열


def _바꿈모음(x):
    """반대 논거 한 줄 → 바꿈 짝의 집합(`레터.반대바꿈` 과 같은 읽기 — 「바꿈」 목록이 없으면 줄 자신이 바꿈 하나)."""
    if not isinstance(x, dict):
        return frozenset()
    바 = x.get("바꿈") if isinstance(x.get("바꿈"), list) else [x]
    return frozenset(s for s in (_바꿈짝(b) for b in 바) if s is not None)


def 반대결합줄(목):
    """`Narrative.반대논거` 목록 → 결합 줄의 자리 번호 집합. 결합 줄 = 다른 줄 둘 이상의 바꿈이 모두 그 줄의 바꿈에 들고(그 줄보다 좁게)
    그 줄의 바꿈이 그 줄들의 바꿈을 합친 것과 같은 줄. 번호는 목록 그대로의 차례(장부 키 「반:<i>」 와 같다)."""
    모 = [_바꿈모음(x) for x in (목 or [])]
    낸 = set()
    for i, s in enumerate(모):
        if not s:
            continue
        든 = [t for j, t in enumerate(모) if j != i and t and t < s]
        if len(든) >= 2 and frozenset().union(*든) == s:
            낸.add(i)
    return 낸


def 반대논거들(목):
    """결합 줄을 뺀 반대 논거 → [(자리 번호, 줄)] — 논거 수와 표의 줄은 이것으로 센다(번호는 장부 키 「반:<i>」 의 번호)."""
    결 = 반대결합줄(목)
    return [(i, x) for i, x in enumerate(목 or []) if isinstance(x, dict) and i not in 결]


def 반대함께키(목):
    """「논거가 모두 함께 맞을 때」 의 장부 키 — 늘 「반:합」(논거가 없으면 None). 1.1.19 — 「반:합」(`레터.반대주당`)이 결합 줄의 바꿈을 빼고 더하므로
    결합 줄이 있어도 겹쳐 더하지 않는다. 결합 줄이 나머지 논거의 일부만 묶은 판도 함께 맞을 때의 값을 싣는다(종전에는 결합 줄의 키로 비켜 가거나 싣지 않았다)."""
    return "반:합" if 반대논거들(목) else None


def 결론판단틀(맥, 쪽):
    """1.1.6 — 종가가 세 시나리오 범위 밖일 때의 [가격] 줄의 글(`결론판단틀부분` 을 잇는다). 조건이 없으면 ""(종전 글)."""
    return 잇기(결론판단틀부분(맥, 쪽))


def 결론판단틀부분(맥, 쪽):
    """1.1.6 — 종가가 세 시나리오 범위 밖일 때의 [가격] 줄: 「{종가} 는 {조건 이름}에 대한 판단이다. {조건 · 함축하는 세계} {반대 논거가 함께 맞을 때}
    그 조건이 깨지면 값은 기준 · 비관(종가가 아래면 기준 · 낙관) 시나리오의 값이다.」 숫자는 모두 장부 키. → [(몫, 글, 이름)] — 조건이 없으면 [](종전 글).
    5단계 — 첫 문장(종가 · 조건 이름)과 끝 문장(표의 주당가치를 되풀이)은 본편 1절에만 싣는다. 3분 레터는 조건과 반대 논거를 싣는다(「이 주가」 는
    3분 레터 첫 문단의 범위 밖 문장이 가리킨다 — 이 틀은 범위 밖에서만 선다)."""
    import 레터1부 as P                                    # noqa: PLC0415
    조 = 판단조건(맥)
    if not 조:
        return []
    맥._판단꼴 = 조["꼴"]
    종, 종말 = 맥.종가키, P.종가말(맥)
    맥._가격표 = list(조.get("표") or [])                      # 1.1.21 — 3분 레터는 조건을 결론 표의 줄로(`삼분결론`)
    문 = [("본편", "%s %s %s%s." % (종말, P.은(맥.수(종, "어림주당")), 조["이름"], 판단머리), "판단머리"),
         ("본편" if 맥._가격표 else "글", 조["글"], "조건")]
    전목 = list(((맥.가정.get("Narrative") or {}).get("반대논거")) or [])
    목 = 반대논거들(전목)                                    # 1.1.19 — 결합 줄(「세 논거를 함께」)은 논거로 세지 않는다
    함께 = 반대함께키(전목)                                  # 「반:합」 — 결합 줄의 바꿈은 빼고 더한다(`레터.반대주당`)
    if len(목) >= 2 and 함께 and _n(맥.값(함께)) is not None:
        수 = {2: "두", 3: "세", 4: "네", 5: "다섯"}.get(len(목), "%d" % len(목))
        합, 기v, 종v = _n(맥.값(함께)), _n(맥.값("R:기준:2.DCF:68")), _n(맥.값(종))
        # 1.1.21 — 논거가 모두 맞을 때의 값이 이 주가 쪽인지(못 미침 · 넘음), 기준의 반대쪽인지를 함께 적는다(값만 찍으면 방향을 읽을 수 없다)
        if 기v is None or 종v is None or (합 - 기v) * (종v - 기v) <= 0:
            끝말, 칸끝 = "기준 시나리오보다 %s" % ("낮습니다" if 기v is not None and 합 < 기v else "높습니다"), None
        elif abs(합 - 기v) < abs(종v - 기v):
            끝말, 칸끝 = "이 주가에 못 미칩니다", "이 주가에 못 미침"
        else:
            끝말, 칸끝 = "이 주가를 넘습니다", "이 주가를 넘음"
        문.append(("본편", "시장에서 제시되는 논거 %s 가지가 모두 맞으면 주당가치는 약 %s %s." % (수, P.으로(맥.수(함께, "어림주당")), 끝말), "반대논거"))
        if 칸끝:
            맥._가격표.append(("시장에서 제시되는 논거 %s 가지가 모두 맞을 때" % 수, "약 %s(%s)" % (맥.수(함께, "어림주당"), 칸끝)))
    먼 = "비관" if 쪽 == "위" else "낙관"
    문.append(("본편", "그 조건이 성립하지 않으면 주당가치는 기준 시나리오 약 %s, %s 시나리오 약 %s." % (맥.수("R:기준:2.DCF:68", "어림주당"), 먼,
                                                                            P.입니다(맥.수("R:%s:2.DCF:68" % 먼, "어림주당"))), "깨짐"))
    return [x for x in 문 if x[1]]


def _결론가격옛(맥):
    """종전 [가격] 줄의 글(`_결론가격옛부분` 을 잇는다)."""
    return 잇기(_결론가격옛부분(맥))


def _결론가격옛부분(맥):
    """종전 [가격] 줄(종가가 범위 안이거나 1.1.6 틀의 조건이 없을 때) → [(몫, 글, 이름)]. 5단계 — 「{날짜} 종가는 {P}입니다」 를 따로 찍지 않고
    조건 문장의 비교 대상에 날짜와 값을 넣는다(`종가와` — 3분 레터는 종가를 표에 두므로 「이 주가」 가 가리킬 앞 문장이 없다)."""
    import 레터1부 as P                                    # noqa: PLC0415
    import 레터3분 as T                                     # noqa: PLC0415
    if not getattr(맥, "종가키", None):
        return []
    종, 종말 = 맥.종가키, P.종가말(맥)
    b = T.바닥(맥)
    if b and b["풀이"]:                                       # v27 — 본보기(「종가 … 전제한다」 → 「… 일 때 주당가치가 종가와 같아집니다」)
        말 = T.가격말(맥, b)
        return [("글", "다른 가정을 그대로 두고 %s의 정상 수준만 바꾸면, %s(%s = 100)일 때 주당가치가 %s 같아집니다. 기준 시나리오의 정상 수준은 %s." % (
            말, T._백들(맥, b, {s: T._내(b, s) for s, _x in b["구분"]}), T.기간말(맥, b), 종가와(맥),
            P.입니다(T._백들(맥, b, {s: "S:6%d6:기준" % s for s, _x in b["구분"]}))), "조건")]
    줄들 = ((맥.민 or {}).get("표4") or {}).get("줄") or []
    풀린 = [i for i, r in enumerate(줄들) if _n(r.get("내재값")) is not None
          and not P.지수꼴인가(P.손잡이꼴({"이름": r["이름"], "대상": r["대상"], "방식": r.get("방식")}, 맥))]   # 지수 꼴은 3분 레터에 소수로 나간다
    if not 풀린:
        return [("글", "다른 가정을 그대로 두고 가정 하나만 바꿔서는 주당가치가 %s 같아지지 않습니다." % 종가와(맥), "조건")]
    i = next((i for i in 풀린 if ["%s" % x for x in 줄들[i].get("대상") or []] in (["영구이익률가감"], ["213"])), None)
    if i is None:
        i = next((i for i in 풀린 if 줄들[i].get("유형기본")), 풀린[0])
    # 1.1.2 — 그 단일 역산값이 실적 · 정상화 · 시나리오 범위 밖이면 첫 장에 올리지 않는다. 범위 안에서 풀린 다른 축이 있으면 그 축을, 없으면
    # 「가정 하나로는 성립하지 않는다」 와 범위 안의 두 변수 조합 · 비영업자산 몫(브리지)을 싣는다(게이트 정합 「3분 범위 밖 역산값」)
    표4 = P._표4줄들(맥)
    if P.역산판정(맥, 표4[i]) in ("밖", "범위없음"):          # 1.1.4 — 한 점뿐인 범위(범위 없음)도 첫 장에 단일 역산값으로 올리지 않는다
        안i = next((k for k in 풀린 if P.역산판정(맥, 표4[k]) == "안"), None)
        if 안i is None:
            # 1.1.12 — 「범위 안에서 같아지지 않습니다」 는 범위 밖으로 판정된 역산값이 있고 종가가 세 시나리오 범위 밖일 때만 쓴다.
            #   근거 범위가 없는 값(범위없음)뿐이거나 종가가 비관 ~ 낙관 안이면 그 단정은 사실이 아니다(종가가 낙관 아래인데 「성립하지 않는다」)
            안쪽 = 종가시나리오안(맥)
            if 안쪽:
                return [("본편", 안쪽, "조건")]                # 1.1.21 — 3분 레터는 결론 표 종가 칸에 「비관 · 낙관 시나리오 사이」
            if not any(P.역산판정(맥, 표4[k]) == "밖" for k in 풀린):
                return [("글", "다른 가정을 그대로 두고 가정 하나만 바꿔 주당가치가 %s 같아지는 값은 실적과 시나리오의 근거 범위가 없어 "
                               "견주지 못했습니다." % 종가와(맥), "조건")]
            return 결론가격밖부분(맥, 종, 종말)
        i = 안i
    r = 줄들[i]
    h = {"이름": r["이름"], "대상": r["대상"], "방식": r.get("방식")}
    꼴 = P.손잡이꼴(h, 맥)
    이름 = 이름다듬기(P.손잡이이름(h, 맥))
    맥._가격표 = [("이 주가와 같아지는 %s" % 이름, "%s(기준 시나리오 %s)" % (맥.수("민:표4:줄:%d:내재값" % i, 꼴), 맥.수("민:표4:줄:%d:적용값" % i, 꼴)))]
    return [("본편", "다른 가정을 그대로 두고 %s만 %s, %s일 때 주당가치가 %s 같아지며, 기준 시나리오의 값은 %s." % (
        이름, 바꿈쪽(r.get("내재값"), r.get("적용값")), 맥.수("민:표4:줄:%d:내재값" % i, 꼴), 종가와(맥),
        P.입니다(맥.수("민:표4:줄:%d:적용값" % i, 꼴))), "조건")]


def 종가시나리오안(맥):
    """1.1.12 — 종가가 비관 ~ 낙관 주당가치 사이면 그 사실을 쓰는 [가격] 줄, 아니면 빈 글. 5단계 — 「{날짜} 종가 {P}는 … 범위 안에 있습니다」 한 문장."""
    import 레터1부 as P                                    # noqa: PLC0415
    종 = getattr(맥, "종가키", None)
    v, 비, 낙 = _n(맥.값(종)) if 종 else None, _n(맥.값("R:비관:2.DCF:68")), _n(맥.값("R:낙관:2.DCF:68"))
    if None in (v, 비, 낙) or not (min(비, 낙) <= v <= max(비, 낙)):
        return ""
    return "%s %s 세 시나리오 주당가치의 범위(비관 %s ~ 낙관 %s) 안에 있습니다." % (
        P.종가말(맥), P.은(맥.수(종, "어림주당")), 맥.수("R:비관:2.DCF:68", "주당"), 맥.수("R:낙관:2.DCF:68", "주당"))


def 결론가격밖(맥, 종, 종말):
    """1.1.2 — 단일 역산값이 모두 범위 밖일 때의 [가격] 줄의 글(`결론가격밖부분` 을 잇는다)."""
    return 잇기(결론가격밖부분(맥, 종, 종말))


def 결론가격밖부분(맥, 종, 종말):
    """1.1.2 — 단일 역산값이 모두 범위 밖일 때의 [가격] 줄 → [(몫, 글, 이름)]. 범위 안 두 변수 조합(있으면)과 비영업자산 몫(브리지 역산 문턱을 넘으면)을 붙인다."""
    import 레터1부 as P                                    # noqa: PLC0415
    문 = [("글", "다른 가정을 그대로 두고 가정 하나만 바꿔서는 실적과 시나리오의 범위 안에서 주당가치가 %s 같아지지 않습니다." % 종가와(맥), "조건")]
    안 = P.두변수안(맥)
    if 안:
        문.append(("글", "실적과 세 시나리오의 범위 안에서는 %s %s 두고 %s %s 두어야 주당가치가 이 주가와 같아집니다." % (
            P.을(이름다듬기(안["A"]["이름"])), P.으로(P._끝글(맥, 안["끝"])), P.을(이름다듬기(안["B"]["이름"])), P.으로(맥.수(안["키"], 안["B"]["꼴"]))), "두변수"))
    elif P.두변수(맥):
        문.append(("글", "두 가정을 함께 실적과 세 시나리오의 범위 끝까지 바꿔도 주당가치가 이 주가와 같아지지 않습니다.", "두변수"))
    몫 = 브리지몫글(맥)
    if 몫:
        문.append(("글", 몫, "브리지"))
    return 문


def 브리지몫글(맥):
    """비영업자산(평가조정의 원천 장부 — 투자부동산 · 관계기업 · 기타)이 주주가치의 문턱(정합설정 「브리지역산.문턱」)을 넘으면 그 몫 한 문장. 아니면 ""."""
    import 레터1부 as P                                    # noqa: PLC0415
    try:
        _민 = importlib.import_module("엔진.민감도")          # 엔진 꾸러미의 같은 이름 함수가 모듈을 가린다 — 모듈로 부른다
    except Exception:                                        # noqa: BLE001
        return ""
    if not _민.브리지역산필수(맥.가정):
        return ""
    c = 맥.기준일열
    키들 = ["H:%d:%s" % (r, c) for _n_, r in _민.비영업할인줄 if _n(맥.값("H:%d:%s" % (r, c)))]
    if not c or not 키들:
        return ""
    return "주주가치의 %s는 비영업자산(장부가액)입니다." % 맥.식(["÷", ["합"] + 키들, "R:기준:요약:주주가치"], "퍼0")


def 결론근거(맥):
    """[근거] 줄의 글(본편 1절) — `결론근거부분` 을 잇는다. 없으면 ""."""
    return 잇기(결론근거부분(맥))


def 결론근거부분(맥):
    """[근거] 줄 → [(몫, 글, 이름)] — 지렛대 가정 가운데 근거 글이 있는 첫 가정의 근거(`레터본문.근거한줄` — 독자근거 → 서사연결 → 절글 「범위」 문단의
    첫 문장 · 값은 가정 표에 있다 — 지수 칸은 3분 레터에 소수로 싣지 않는다)와 맺음 한 문장(본편 1절에만). 없으면 []."""
    import 레터본문 as B                                    # noqa: PLC0415
    d = 지렛대(맥)
    if not d:
        return []
    if d.get("잣대") == "대안":                               # 1.1.7 — 할인율 대안 사양의 근거는 부록 B · 영구기간 판은 할인율 절(다른 자리를 가리키는 문장 — 본편 1절에만)
        return [("본편", "영구기간 자본비용의 기준 시나리오 값을 정한 근거는 할인율 절에 있습니다." if d.get("대안꼴") == "영구"
                 else "할인율의 기준 시나리오 값을 정한 근거는 산정 방법별로 부록 B에 있습니다.", "가리킴")]
    for 번 in d.get("번호들") or []:
        if 번 != "WACC" and (not 번.isdigit() or not B.값있나(맥, 번)):
            continue
        근 = B.근거한줄(맥, 번)
        if 근:                                               # v27 — 예고 문장(「… 근거는 이렇다」) 대신 근거 뒤에 사실 한 문장
            return [("글", _문장끝(근), "근거"), ("본편", "이를 근거로 %s의 기준 시나리오 값을 정했습니다." % 가정말(맥, 번), "맺음")]
    return []


def 결론틀림(맥):
    """[틀림] 줄의 글(본편 1절) — `결론틀림부분` 을 잇는다. 셋 다 없으면 ""."""
    return 잇기(결론틀림부분(맥))


def 결론틀림부분(맥):
    """[틀림] 줄 → [(몫, 글, 이름)] — 틀림.길(저자) · 그 가정을 고치게 할 신호(없으면 3분 레터의 신호 · 모니터링 지표) · 다음 점검(3분 레터는 표).
    셋 다 없으면 []. 다음 점검 글은 맥에 둔다(`맥._결론다음` — 3분 레터 표가 같은 글을 싣는다)."""
    import 레터1부 as P                                    # noqa: PLC0415
    N_ = 맥.가정.get("Narrative") if isinstance(맥.가정.get("Narrative"), dict) else {}
    틀 = N_.get("틀림") if isinstance(N_.get("틀림"), dict) else {}
    문 = []
    길 = 펴기(맥, 틀.get("길"), "Narrative.틀림.길", 어림=True) if _글(틀.get("길")) else ""
    if 길:
        문.append(("글", _문장끝(길), "길"))                    # v27 교열 3 — 예고 문장(「이 판단이 틀린다면 … 이렇다」)은 싣지 않는다
    _이름, 틀번, 같 = 틀릴가정(맥)                          # v27 — 신호는 작성자가 정한 「먼저 틀릴 가정」 에 묶는다(지렛대가 다르면 지렛대 신호는 「갈림」 줄에)
    맥._신호차례 = None
    맥._신호표 = []
    신글 = 신호글(맥, 틀번)
    if not 신글 and 같:                                      # 선언이 없을 때만(지렛대 = 틀릴 가정) 일반 신호로 메운다
        신글 = 신호글(맥, None, 고르기=True)
    if not 신글 and not 같:
        맥.알림.append("결론 — 먼저 틀릴 가정(Narrative.틀림.가정)을 고치게 할 신호(신호[].가정)가 없다 — 「틀림」 줄에 신호 문장을 싣지 않았다")
    if not 신글 and 같:
        for k, x in enumerate(((맥.가정.get("관측") or {}).get("모니터링") or [])[:1]):
            if isinstance(x, dict) and _글(x.get("지표")):
                지 = 맥.원고글(x.get("지표"), "관측.모니터링[%d].지표" % k)
                경 = 맥.원고글(x.get("경보"), "관측.모니터링[%d].경보" % k) if _글(x.get("경보")) else ""
                if 지:
                    신글 = (지.rstrip("."), "경보 기준은", 경.rstrip("."))
    if 신글:                                                 # v27 — 지시어(「그것을 먼저 보여 줄 신호」) 없이 · 문턱이 문장이면 「… 경우」 로
        이, 말, 끝 = 신글
        말 = "임계치는" if 말 == "문턱은" else 말
        문.append(("본편", ("먼저 확인할 지표는 %s, %s %s." % (P.이고(이), 말, P.입니다(경우글(끝)))) if 끝 else "먼저 확인할 지표는 %s." % P.입니다(이),
                  "신호"))
        맥._신호표 = [("먼저 볼 지표", 이)] + ([("그 지표의 %s" % ("임계치" if 말 == "임계치는" else "경보 기준"), 경우글(끝))] if 끝 else [])
    다 = 펴기(맥, N_.get("다음점검"), "Narrative.다음점검", 어림=True) if _글(N_.get("다음점검")) else ""
    맥._결론다음 = 다.rstrip(".") if 다 else ""
    if 다:
        문.append(("표", "다음 점검은 %s 뒤입니다." % 다.rstrip("."), "다음"))
    return 문


def 결론부분(맥):
    """결론 다섯 줄의 부분 → [(자리, [(몫, 글, 이름)])](값 · 가격 · 갈림 · 근거 · 틀림 차례 — 비는 줄은 빠진다). 한 번 셈해 맥에 둔다.
    본편 1절은 줄마다 모든 부분을(`결론줄들`), 3분 레터는 「표」 몫을 핵심 숫자 표로 · 「글」 몫을 문장으로 싣는다(`삼분결론`). 장부 키는 같다."""
    import 레터1부 as P                                    # noqa: PLC0415
    if getattr(맥, "_결론부분", None) is not None:
        return 맥._결론부분
    L = []
    기 = "R:기준:2.DCF:68"
    값 = [("표", "기준 시나리오의 주당가치는 약 %s." % P.입니다(맥.수(기, "어림주당")), "기준"),       # v27 교열 268 · 269
         ("표", "비관 시나리오에서는 약 %s, 낙관 시나리오에서는 약 %s." % (맥.수("R:비관:2.DCF:68", "어림주당"), P.입니다(맥.수("R:낙관:2.DCF:68", "어림주당"))),
          "범위")]
    이야 = 맥.가정.get("시나리오이야기") or {}
    한 = 펴기(맥, (이야.get("기준") or {}).get("한줄"), "시나리오이야기.기준.한줄", 어림=True) if _글((이야.get("기준") or {}).get("한줄")) else ""
    이름꼴 = 펴기(맥, _N(맥).get("한줄"), "Narrative.한줄", 어림=True) if (not 한 and _글(_N(맥).get("한줄"))) else ""
    import 레터갭 as _갭                                     # noqa: PLC0415 — 1.1.3(A4) 「범위 밖」 신호(첫 장 · 본편 1절이 같은 줄)
    밖 = _갭.범위밖글(맥)
    if 밖:
        값.append(("본편", 밖, "범위밖"))                      # 1.1.21 — 3분 레터는 결론 표 종가 칸에 「세 시나리오 범위 밖 · …」
    if 한:                                                   # 시나리오 한 줄은 문장이다(「… 늘어납니다」) — v27 교열 264: 앞의 예고 문장은 싣지 않는다
        값.append(("글", _문장끝(한), "한줄"))
    elif 이름꼴:                                             # Narrative.한줄 은 이름 꼴이다(13절 「이 레터는 … 을 기준 시나리오로 삼았다」)
        값.append(("글", "기준 시나리오에서는 %s 가정했습니다." % P.을(이름꼴.rstrip(".")), "한줄"))
    L.append(("값", 값))
    맥._가격표 = []
    가 = 결론가격부분(맥)
    if 가:
        L.append(("가격", 가))
    d = 지렛대(맥)
    if d:                                                    # v27 — 본보기(「두 값이 갈리는 지점은 … 하나다」 → 「주당가치를 가장 크게 좌우하는 가정은 …입니다」)
        앞 = "주당가치를 가장 크게 좌우하는 가정은" if d.get("가장큼") else "주당가치를 좌우하는 가정은"
        문 = [("표", "%s %s." % (앞, P.입니다(d["이름"])), "가정")]
        폭 = 지렛대폭글(맥, d, "어림주당")
        if 폭:
            문.append(("표", "%s 주당가치는 %s 달라집니다." % 폭, "폭"))
            문 += [("표", g, "선언폭") for g in 선언견줌(맥, d, "어림주당")]      # 1.1.7 — 폭 1위가 선언을 이겼으면 선언한 가정의 폭을 나란히
        L.append(("갈림", 문))
    else:
        맥.알림.append("결론 — 값을 가르는 가정(Narrative.틀림.가정 · 시나리오 driver · 민감도 손잡이)이 하나도 없다 — 결론의 「갈림」 줄을 싣지 않았다")
    근 = 결론근거부분(맥)
    if 근:
        L.append(("근거", 근))
    elif d:
        맥.알림.append("결론 — 지렛대(%s)의 근거 글(독자근거 · 서사연결 · 절글 「범위」)이 없다 — 결론의 「근거」 줄을 싣지 않았다" % d["이름"])
    틀 = 결론틀림부분(맥)
    if 틀:
        L.append(("틀림", 틀))
    else:
        맥.알림.append("결론 — Narrative.틀림.길 · 신호 · 다음점검이 모두 없다 — 결론의 「틀림」 줄을 싣지 않았다")
    맥._결론부분 = L
    return L


def 결론줄들(맥):
    """결론 다섯 줄 → [(자리, 글)](값 · 가격 · 갈림 · 근거 · 틀림 차례 — 비는 줄은 빠진다). 한 번 셈해 맥에 둔다. 본편 1절이 싣는 글이고(줄의 모든
    부분 — `결론부분`), 장부 「결론」 에 같은 줄이 남는다(인터랙티브 판 머리가 읽는다). 3분 레터는 같은 부분을 표와 문장으로 나눠 싣는다(`삼분결론`)."""
    if getattr(맥, "_결론줄", None) is not None:
        return 맥._결론줄
    맥._결론줄 = [(자리, 잇기(부)) for 자리, 부 in 결론부분(맥)]
    return 맥._결론줄


def 지렛대폭끝(맥, d, 꼴="주당"):
    """지렛대(또는 선언)를 근거 범위 양 끝으로 옮긴 주당가치 → (낮은 쪽 글, 높은 쪽 글) — `지렛대폭글` 과 같은 키 · 같은 꼴. 없으면 None."""
    if not d or not d.get("하키") or not d.get("상키"):
        return None
    a, b = _n(맥.값(d["하키"])), _n(맥.값(d["상키"]))
    if a is None or b is None:
        return None
    낮, 높 = (d["하키"], d["상키"]) if a <= b else (d["상키"], d["하키"])
    return 맥.수(낮, 꼴), 맥.수(높, 꼴)


def 지렛대폭머리(맥, d):
    """핵심 숫자 표의 폭 줄 이름 — 지렛대를 무엇으로 바꿨나(`지렛대폭글` 의 말과 같은 잣대 · 「…바꿨을 때」 꼴)."""
    import 레터1부 as P                                    # noqa: PLC0415
    if d.get("잣대") == "시나리오":
        return "그 가정만 비관 · 낙관 시나리오의 값으로 바꿨을 때"
    if d.get("잣대") == "대안":
        return ("영구기간 자본비용만 할인율 절에서 비교한 세 가지 값으로 바꿨을 때" if d.get("대안꼴") == "영구"
                else "할인율만 부록 B의 대안 산정 방법으로 바꿨을 때")
    if d.get("표3") is not None:
        r = 맥.민["표3"][d["표3"]]
        h = {"이름": r["이름"], "대상": r["대상"], "방식": r.get("방식")}
        if d.get("잣대") == "범위":
            return "그 가정만 근거 범위(%s)의 끝 값으로 바꿨을 때" % P.폭글(h, "민:표3:%d:폭" % d["표3"], 맥)
        폭 = P.폭말(h, "민:표3:%d:폭" % d["표3"], 맥)
        return ("그 가정만 %s 바꿨을 때" % 폭) if 폭.endswith("사이에서") else ("그 가정만 %s 높이거나 낮췄을 때" % 폭)
    return "그 가정만 바꿨을 때"


def 선언폭머리(s, d=None):
    """핵심 숫자 표의 선언 가정 폭 줄 이름(`선언견줌` 과 같은 잣대). 지렛대(d)와 잣대가 같으면 바꾼 방법은 바로 위 줄이 말한다 — 이름만 둔다."""
    if d is not None and s.get("잣대") == d.get("잣대"):
        return "먼저 틀릴 가정으로 본 %s만 바꿨을 때" % s["이름"]
    말 = {"시나리오": "비관 · 낙관 시나리오의 값으로 바꿨을 때", "범위": "근거 범위의 끝 값으로 바꿨을 때"}.get(s.get("잣대"), "같은 방법으로 바꿨을 때")
    return "먼저 틀릴 가정으로 본 %s만 %s" % (s["이름"], 말)


def 결론표자리(이름):
    """핵심 숫자 표의 줄 이름 → (결론 자리, 대조 꼴) — 「수」(칸의 숫자를 본편 1절 줄의 숫자와) · 「글」(칸의 글이 본편 1절 줄 안에). 모르는 줄은 None.
    게이트 ⑯(`레터문장.결론점검`)이 3분 레터의 표를 본편 1절의 결론 줄과 맞대는 열쇠다."""
    이 = re.sub(r"\s+", " ", "%s" % 이름).strip().strip("*").strip()
    if 이 in (결론표머리["기준"], 결론표머리["범위"]):
        return "값", "수"
    if 이.endswith("종가") or 이.startswith(("이 주가와 같아지는 ", "그때 ", "시장에서 제시되는 논거")):
        return "가격", "수"                                  # 1.1.21 — 주가가 뜻하는 조건 · 반대 논거도 표의 줄로
    if 이 == "먼저 볼 지표" or 이.startswith("그 지표의 "):
        return "틀림", "글"
    if 이 in 결론표머리["가정"]:
        return "갈림", "글"
    if 이.endswith("때") and "만 " in 이:
        return "갈림", "수"
    if 이 == 결론표머리["다음"]:
        return "틀림", "글"
    return None


def 삼분결론(맥):
    """3분 레터 「### 결론」 의 재료(레터 v27 5단계) → {"표": [(줄 이름, 칸)], "글": [[문장 …] …]}. 결론 줄과 같은 부분 · 같은 장부 키다.
    표 = 결론 줄의 「표」 몫(세 시나리오의 주당가치 · 날짜와 종가 · 주당가치를 좌우하는 가정과 그 폭 · 다음 점검) — 어느 회사에나 있는 사실은 문장으로
    쓰지 않는다. 글 = 「글」 몫 — 첫 문단은 시나리오 한 줄 · 범위 밖 · 주가가 뜻하는 조건(「이 주가」 가 바로 앞 범위 밖 문장을 가리키게 이 차례),
    둘째 문단은 근거 · 판단이 틀리는 경우 · 먼저 확인할 지표."""
    import 레터1부 as P                                    # noqa: PLC0415
    부 = dict(결론부분(맥))
    기 = "R:기준:2.DCF:68"
    표 = [(결론표머리["기준"], "약 %s" % 맥.수(기, "어림주당")),
         (결론표머리["범위"], "약 %s · 약 %s" % (맥.수("R:비관:2.DCF:68", "어림주당"), 맥.수("R:낙관:2.DCF:68", "어림주당")))]
    if getattr(맥, "종가키", None) and "가격" in 부:
        import 레터갭 as _갭                                 # noqa: PLC0415
        위치 = {"위": "%s · 낙관 시나리오보다 높음" % _갭.범위밖말, "아래": "%s · 비관 시나리오보다 낮음" % _갭.범위밖말,
              "안": "비관 · 낙관 시나리오 사이"}.get(_갭.범위(맥))
        종칸 = 맥.수(맥.종가키, "어림주당")
        표.append((P.종가말(맥), "%s(%s)" % (종칸, 위치) if 위치 else 종칸))
        표 += list(getattr(맥, "_가격표", None) or [])
    d = 지렛대(맥)
    if d and "갈림" in 부:
        표.append((결론표머리["가정"][0 if d.get("가장큼") else 1], d["이름"]))
        이름들 = [이 for 몫, _g, 이 in 부["갈림"]]
        폭 = 지렛대폭끝(맥, d, "어림주당") if "폭" in 이름들 else None
        if 폭:
            표.append((지렛대폭머리(맥, d), "%s ~ %s" % 폭))
            s = d.get("선언") or {}
            폭2 = 지렛대폭끝(맥, s, "어림주당") if (s.get("이름") and "선언폭" in 이름들) else None
            if 폭2:
                표.append((선언폭머리(s, d), "%s ~ %s" % 폭2))
    if any(이 == "신호" for _m, _g, 이 in 부.get("틀림", [])):
        표 += list(getattr(맥, "_신호표", None) or [])
    if getattr(맥, "_결론다음", "") and any(이 == "다음" for _m, _g, 이 in 부.get("틀림", [])):
        표.append((결론표머리["다음"], "%s 뒤" % 맥._결론다음))

    def 글들(자리, 이름들=None):
        return [g for 몫, g, 이 in 부.get(자리, []) if 몫 == "글" and g and (이름들 is None or 이 in 이름들)]
    첫 = 글들("값", ("한줄",)) + 글들("값", ("범위밖",)) + 글들("가격")
    둘 = 글들("근거") + 글들("틀림")
    return {"표": 표, "글": [x for x in (첫, 둘) if x]}


def _N(맥):
    return 맥.가정.get("Narrative") if isinstance(맥.가정.get("Narrative"), dict) else {}


본문연결줄수 = 5


def 연결표(맥, 전부=False):
    """「Narrative와 입력값」 표 — 전부 = False 면 값을 움직이는 줄 다섯(점수 차례로 고르고 가정 파일의 차례로 싣는다), True 면 모든 줄.
    채택 칸의 「—」 는 뜻을 적고(영구기간 ROIC = WACC 따위), 「고치게 할 신호」 열은 15절의 신호와 잇는다. 이어진 신호가 하나도 없으면
    그 열을 뺀다(L10)."""
    줄들 = 연결줄들(맥)
    if not 줄들:
        return []
    if not 전부:
        줄들 = 본문연결줄(맥, 줄들)
        if not 줄들:
            return []
    표 = []
    P3가 = ((맥.가정.get("3P") or {}).get("가정") or {}) if isinstance(맥.가정.get("3P"), dict) else {}
    for x in 줄들:
        문 = 펴기(맥, x["문장"], "서사연결.%s" % x["번호들"][0])
        if not 문:
            continue
        입 = 이름묶기(맥, [가정말(맥, b) for b in x["번호들"]])
        채 = " · ".join(dict.fromkeys(채택글(맥, b, x.get("열들")) for b in x["번호들"]))
        판 = next((P3가[b]["판정"] for b in x["번호들"] if isinstance(P3가.get(b), dict) and P3가[b].get("판정") in 판정들), None)
        if 판:
            채 += " · %s" % 판                                  # M5 — 핵심 가정의 3P test 판정
        신 = " · ".join(_신호이름(맥, x["번호들"])) or "—"
        표.append([문, 입, 채, 신])
    if not 표:
        return []
    신호열 = any(r[3] != "—" for r in 표)
    머 = ["Narrative", "입력값", "채택"] + (["고치게 할 신호"] if 신호열 else [])
    import 레터1부 as P                                    # noqa: PLC0415
    L = P._표(머, [r if 신호열 else r[:3] for r in 표], ["l"] * len(머))
    L.append("")
    return L


def 주제말있나(글):
    """원고 문장이 제 주제어(「회사의 우위는 …」 · 「원가 구조는 …」)로 여는가 — 그러면 코드가 머리말(「강점은 」)을 잇지 않는다(문장 원칙 13 ·
    구조 지표 ⑧ — 「강점은 회사의 우위는 …」 처럼 주제어가 겹친 비문이 된다). 첫 세 어절 안에 「은 · 는」 으로 끝나는 어절이 있으면 참."""
    return bool(re.match(r"^\s*(?:\S+\s){0,2}\S+[은는]\s", "%s" % (글 or "")))


def Narrative절(맥, 번):
    """3. Narrative — 사업 개요를 흡수한다(제안 2.2). 정체성 · 우위와 「그러나」 · Life cycle · 「Narrative와 입력값」 표(값을 움직이는
    다섯 줄 — 전부는 부록 I, R1b · L10) · 값에 넣지 않은 Narrative · 가장 먼저 틀릴 가정."""
    L = ["## %d. Narrative" % 번, ""]
    N = 맥.가정.get("Narrative") or {}
    N = N if isinstance(N, dict) else {}
    첫 = [x for x in (펴기(맥, N.get("정체성"), "Narrative.정체성"), 펴기(맥, N.get("구성"), "Narrative.구성")) if x]
    둘 = []
    우 = 펴기(맥, N.get("우위"), "Narrative.우위")
    그 = 펴기(맥, N.get("그러나"), "Narrative.그러나")
    if 우:
        둘.append("강점은 %s" % 우 if not (우.startswith("강점") or 주제말있나(우)) else 우)     # v27 구조 ⑧
    if 그:
        둘.append("그러나 %s" % 그 if not 그.startswith("그러나") else 그)
    if 첫 or 둘:
        if 첫:
            L += [" ".join(첫), ""]
        if 둘:
            L += [" ".join(둘), ""]
    else:
        for g in 맥.개요:
            L += [g, ""]
    L += 생애주기문단(맥)
    표 = 연결표(맥)
    if 표:
        전부수 = len(연결줄들(맥))
        표줄수 = sum(1 for x in 표 if x.startswith("| ") and not x.startswith("| Narrative |")) 
        L += ["**표. 주당가치에 영향이 큰 Narrative 문장과 그 문장을 반영한 가정**", ""]     # v27 교열 25 — 표 설명은 표 제목으로 · 26 — 나머지는 표 주석으로
        L += 표
        if 전부수 > 표줄수:
            L += ["나머지 Narrative 문장 %d개는 부록 %s에 있습니다." % (전부수 - 표줄수, 맥.부록글["Narrative"]), ""]
        맥.서술("Narrative.표")
    L += 값밖문단(맥)
    틀, _이름 = 틀림문장(맥)
    if 틀:
        L += [" ".join(틀), ""]
    맥.서술("Narrative")
    return L


def 본문연결줄(맥, 줄들=None):
    """2절 「Narrative와 입력값」 표에 싣는 줄 — 값을 움직이는 줄 다섯(점수 차례로 고르고 가정 파일의 차례로). 나머지는 부록에 있다."""
    줄들 = 연결줄들(맥) if 줄들 is None else 줄들
    import 레터 as _L                                       # noqa: PLC0415
    줄들 = [x for x in 줄들 if not _L.원고검사(x["문장"])]
    import 레터1부 as P                                    # noqa: PLC0415
    if P.독자층(맥):                                         # 독자 층 — 기준 기간 = 100 으로 못 바꾸는 지수 · 배수 칸의 줄은 싣지 않는다(부록에 있다)
        줄들 = [x for x in 줄들 if not any(b != "WACC" and P.정상수준구분(맥, b) is None and P.지수꼴인가(_L.가정꼴(b, 맥.구))
                                        for b in x["번호들"])]
    점 = [(_연결점수(맥, x["번호들"]), k) for k, x in enumerate(줄들)]
    고른 = {k for _p, k in sorted(점, key=lambda t: -t[0])[:본문연결줄수] if _p > 0}
    return [x for k, x in enumerate(줄들) if k in 고른]


def 절머리(맥, 절키, 판정=None):
    """추정 절(매출 · 비용 · 인건비 · 재투자 · 운전자본 · 세금 · 할인율 · Terminal Value · 주주가치) 머리 한 문장 — 「가정에 반영한 Narrative는
    「…」입니다.」 (서사연결 가운데 이 절의 가정을 가리키는 줄 · 부록에만 있으면 끝에 「(부록 X)」 — v27 교열 57 · 77). 없으면 빈 목록.
    판정 — 가정 번호 → 절 키(본편의 `레터본문.항목절` — 인건비 · 운전자본을 따로 가른다). 없으면 `절가정`."""
    판정 = 판정 or 절가정
    줄들 = 연결줄들(맥)
    if not 줄들 or not 맥.절.get("Narrative"):
        return []
    # 2절 표에 실린 줄을 먼저 가리키고, 그 절의 줄이 부록에만 있으면 부록 표를 가리킨다(2026-10-23 W3 — 2절 표에 없는 줄을 「2절 표의 … 줄」 로 적었다)
    본문 = {id(x) for x in 본문연결줄(맥, 줄들)}
    고른 = []
    for x in sorted(줄들, key=lambda x: 0 if id(x) in 본문 else 1):
        if any(판정(b) == 절키 for b in x["번호들"]):
            문 = 펴기(맥, x["문장"], "서사연결.%s" % x["번호들"][0])      # 2026-10-26 — 표(1409행)와 같이 자리표시를 편다
            if 문:
                고른.append(("「%s」" % 문.rstrip("."), id(x) in 본문))
    if not 고른:
        return []
    글, 본 = 고른[0]
    부 = (getattr(맥, "부록글", None) or {}).get("Narrative")
    if 본:
        return ["가정에 반영한 Narrative는 %s입니다." % 글, ""]
    if 부:
        return ["가정에 반영한 Narrative는 %s입니다(부록 %s)." % (글, 부), ""]
    return []


def 절가정(번):
    """가정 번호(또는 WACC) → 그 가정을 숫자로 옮기는 본문 절의 키."""
    if 번 == "WACC":
        return "할인율"
    try:
        n = int(번)
    except (TypeError, ValueError):
        return None
    if n < 80 or 600 <= n < 700 or (270 <= n < 400 and not 394 <= n <= 421):
        return "매출"
    if 80 <= n < 146 or 500 <= n < 530 or 700 <= n < 800:
        return "비용"
    if 146 <= n < 194 or 800 <= n < 940 or 960 <= n < 970 or 394 <= n <= 421:
        return "재투자"
    if 194 <= n < 212 or 940 <= n < 950:
        return "세금"
    if n in (212, 213, 219) or 950 <= n <= 952:
        return "영구"
    if 214 <= n < 270 or 953 <= n < 960:
        return "주주가치"
    return None


def 시나리오3P(맥, s):
    """12절 — 시나리오 s 의 「이 세계로 가고 있다는 신호는 …다. 3P test로는 …이다. {근거}」."""
    import 레터1부 as P                                    # noqa: PLC0415
    P3 = ((맥.가정.get("3P") or {}).get("시나리오") or {}).get(s) if isinstance(맥.가정.get("3P"), dict) else None
    글 = []
    신 = ""
    if isinstance(P3, dict) and _글(P3.get("신호")):
        신 = 펴기(맥, P3.get("신호"), "3P.시나리오.%s.신호" % s)
    if not 신:
        고른 = [x for x in (펴기(맥, x.get("신호"), "신호[%d].신호" % i) for i, x in enumerate(신호들(맥)) if x.get("시나리오") == s) if x]
        신 = P._나열(고른)
        while len(고른) > 1 and len("이 세계로 가고 있다는 신호는 %s." % P.입니다(신.rstrip("."))) > 120:     # 레터 v27 6단계 — 한 문장 120자 안(신호가 많으면 앞에서부터)
            고른 = 고른[:-1]
            신 = P._나열(고른)
    if 신 and s != "기준":                                   # 문장 머리(「이 세계로 가고 있다는 신호는」 · 「3P 기준으로는」 · 「이 길은」)는 인터랙티브 `관측머리` 가 찾는다
        글.append("이 세계로 가고 있다는 신호는 %s." % P.입니다(신.rstrip(".")))
    if isinstance(P3, dict) and P3.get("판정") in 판정들:
        if P.독자층(맥):                                     # 통독 v3 상-9 — 독자 층은 판정 이름 없이 쉬운 말로
            글.append("이 길은 %s 길입니다." % 독자판정[P3["판정"]])
        else:
            글.append("3P 기준으로는 %s." % P.입니다(P3["판정"]))
        근 = 펴기(맥, P3.get("근거"), "3P.시나리오.%s.근거" % s)
        if 근:
            글.append(근 if 근.endswith(".") else 근 + ".")
        맥.서술("3P")
    return " ".join(글)


def 신호지금(맥, i, x, 본편=False):
    """신호의 「지금 상태」 — 저자 글(신호[].지금)이 있으면 그것, 없으면 그 신호가 고치게 할 가정에 닿은 평가기준일 뒤 자료(부록 G)가
    있는지(있으면 공표일과 함께). 둘 다 없으면 빈 글(R1b · L9)."""
    if _글(x.get("지금")):
        return 펴기(맥, x.get("지금"), "신호[%d].지금" % i)
    뒤 = (맥.부록 or {}).get("기준일뒤자료") if isinstance(맥.부록, dict) else None
    번들 = set(신호가정(맥, x))
    if not 뒤 or not 번들:
        return ""
    날 = sorted({("%s" % (y.get("공표일") or "")).strip() for y in 뒤 if isinstance(y, dict) and 번들 & {("%s" % b) for b in y.get("가정") or []}} - {""})
    return ("%s 자료가 있습니다(%s부록 G — %s)" % (importlib.import_module("기준일").자료경계(맥.가정)["말"], "본편 " if 본편 else "", " · ".join(날))) if 날 else ""


def 이야기점검절(맥, 번):
    """15. Narrative 점검(M3) — 신호 · 보는 자료 · 평가기준일의 값 · 문턱 · 켜지면 값(↑ · ↓) · 지금 상태 · 넘으면 고칠 가정 · 변화 유형.
    R1b(L9 · L15) — 「켜지면」 은 저자가 적은 방향, 「지금 상태」 는 저자 글이나 부록 G 의 자료. 둘 다 없는 열은 세우지 않는다.
    변화 유형은 용어표의 쉬운 말과 함께(shift 세부 조정 · change 사업 범위 변경 · break 핵심 전제 훼손 — 2026-10-27)."""
    import 레터1부 as P                                    # noqa: PLC0415
    import 레터3분                                           # noqa: PLC0415
    L = ["## %d. Narrative 점검" % 번, ""]
    if P.독자층(맥):                                         # 통독 v3 중-6 — 독자 층(5막)은 신호 · 문턱 · 켜지면 · 지금 넷만, 전체 표는 부록(신호전체)
        return L + 신호요약표(맥)
    # 1.1.21 — 변화 유형의 정의(서른 곳 같은 네 문장)는 표로(원칙 12 — 정의는 표 · 같은 내용이 되풀이되면 표로)
    L += ["**표. 관측 신호가 임계치를 넘을 때의 변화 유형과 고칠 범위**", ""]
    L += P._표(["변화 유형", "뜻", "고칠 범위"],
               [["세부 조정", "사업 내용이 같고 성장 · 이익률 · 위험의 수준만 바뀜", "해당 가정"],
                ["사업 범위 변경", "사업 영역이 추가되거나 제외됨", "매출 구분과 모델 구조"],
                ["핵심 전제 훼손", "Narrative의 핵심 요소가 더는 성립하지 않음", "모델 전체를 다시 구성"]], ["l", "l", "l"])
    L.append("")
    줄들, 방향들, 지금들 = [], [], []
    for i, x in enumerate(신호들(맥)):
        고칠 = 이름묶기(맥, [가정말(맥, "%s" % b) for b in x.get("가정") or []]) or 맥.원고글(x.get("고칠가정"), "신호[%d].고칠가정" % i) or "—"
        방향들.append(레터3분.방향글(x) or "—")
        지금들.append(신호지금(맥, i, x) or "—")
        줄들.append([펴기(맥, x.get("신호"), "신호[%d].신호" % i) or "—", 맥.원고글(x.get("자료"), "신호[%d].자료" % i) or "—",
                   펴기(맥, x.get("기준일값"), "신호[%d].기준일값" % i) or "—", 펴기(맥, x.get("문턱"), "신호[%d].문턱" % i) or "—",
                   고칠, x.get("갈래") or "—"])
    방향열 = any(v != "—" for v in 방향들)
    지금열 = any(v != "—" for v in 지금들)
    머 = [신호머리["신호"], "보는 자료", "평가기준일의 값", 신호머리["문턱"]] + ([신호머리["켜지면"]] if 방향열 else []) + (["지금 상태"] if 지금열 else []) + ["넘으면 고칠 가정", "변화 유형"]
    낸 = []
    for k, r in enumerate(줄들):
        낸.append(r[:4] + ([방향들[k]] if 방향열 else []) + ([지금들[k]] if 지금열 else []) + r[4:])
    if 방향열:
        L.append("「경보 시 가치 방향」은 관측 신호에 경보가 켜질 때 주당가치가 바뀌는 방향입니다(↑ 오름 · ↓ 내림 · ↑↓ 오를 수도 내릴 수도 있음).")
        L.append("")
    L += P._표(머, 낸, ["l"] * len(머))
    L.append("")
    if not 방향열:
        맥.알림.append("신호에 「방향」(켜지면 주당가치가 오르는지 · 내리는지 — ↑ · ↓ · ↑↓)이 없다 — 15절에 「켜지면」 열을 세우지 않았다")
    맥.서술("Narrative.점검")
    return L


def 신호요약표(맥):
    """5막(독자 층)의 신호 표 — 신호 · 문턱 · 켜지면 · 지금 상태. 보는 자료 · 평가기준일의 값 · 고칠 가정 · 변화 유형은 부록의 신호 전체 표에."""
    import 레터1부 as P                                    # noqa: PLC0415
    import 레터3분                                           # noqa: PLC0415
    줄들 = []
    for i, x in enumerate(신호들(맥)):
        줄들.append([펴기(맥, x.get("신호"), "신호[%d].신호" % i) or "—", 펴기(맥, x.get("문턱"), "신호[%d].문턱" % i) or "—",
                   레터3분.방향글(x) or "—", 신호지금(맥, i, x) or "—"])
    방향열 = any(r[2] != "—" for r in 줄들)
    지금열 = any(r[3] != "—" for r in 줄들)
    머 = [신호머리["신호"], 신호머리["문턱"]] + ([신호머리["켜지면"]] if 방향열 else []) + (["지금 상태"] if 지금열 else [])
    낸 = [r[:2] + ([r[2]] if 방향열 else []) + ([r[3]] if 지금열 else []) for r in 줄들]
    L = []
    if 방향열:                                               # 1.1.21 — 표 설명 한 줄만(「다시 검토합니다」 · 부록 안내는 지움 — 원칙 3 · 12)
        L += ["「경보 시 가치 방향」은 관측 신호에 경보가 켜질 때 주당가치가 바뀌는 방향입니다(↑ 오름 · ↓ 내림 · ↑↓ 오를 수도 내릴 수도 있음).", ""]
    L += P._표(머, 낸, ["l"] * len(머))
    L.append("")
    맥.서술("Narrative.점검")
    return L


def 자리절(맥, 번):
    """16. 평가자의 자리 — 매수 · 매도의 자리를 대신한다(제안 2.7 · 6절): 이해관계 · 틀릴 수 있는 길 · 독자 손잡이 · 다음 점검."""
    import 레터1부 as P                                    # noqa: PLC0415
    L = ["## %d. 평가자의 자리" % 번, ""]
    회사 = ("%s" % (맥.메타.get("회사명") or "평가 대상 회사")).strip()
    이 = (맥.메타 or {}).get("이해관계")
    if isinstance(이, dict) and isinstance(이.get("보유"), bool):
        글 = "이 레터를 쓴 사람은 %s 주식을 %s." % (회사, "보유합니다" if 이.get("보유") else "보유하지 않습니다")     # v27 교열 263
        내 = 맥.원고글(이.get("보유내용"), "메타.이해관계.보유내용") if 이.get("보유") and _글(이.get("보유내용")) else ""
        if 내:
            글 += " " + (내 if 내.endswith(".") else 내 + ".")
        의 = 맥.원고글(이.get("의뢰"), "메타.이해관계.의뢰") if _글(이.get("의뢰")) else ""
        if 의:
            글 += " " + (의 if 의.endswith(".") else 의 + ".")
        L += [글, ""]
    else:
        맥.알림.append("메타.이해관계(보유 여부 · 의뢰 관계)가 없다 — 16절 첫 문단을 싣지 않았다")
    틀, 이름 = 틀림문장(맥)
    if 틀:
        길 = ""
        N = 맥.가정.get("Narrative") or {}
        if isinstance(N, dict) and isinstance(N.get("틀림"), dict):
            길 = 펴기(맥, N["틀림"].get("길"), "Narrative.틀림.길")
        L += ["이 평가가 틀린다면 가장 먼저 틀릴 가정은 %s." % P.입니다(이름), ""]       # 1.1.21 — 길(원고)은 1절 결론이 싣는다(같은 글을 세 자리에 두지 않는다)
    손 = 손잡이목록(맥)
    긴 = len(P._나열(손)) > 70 if 손 else False               # 손잡이가 많으면 한 문장이 140자를 넘는다(⑬ 오류 — 회차 20261023 NAVER) — 수로 부르거나 목록으로
    if P.독자층(맥) and getattr(맥, "종가키", None):          # 통독 v3 하-15 — 엑셀을 다루지 않는 독자에게는 3분 레터 그림 2 가 그 도구다
        L += ["판단이 다른 독자는 3분 레터 그림 2에서 자기가 생각하는 정상 수준에 맞는 주당가치를 읽을 수 있습니다.%s" % (
            (" 평가 모델 파일에서는 %s 바꿔 볼 수 있습니다(%s)." % (("민감도 절의 가정 %d가지를" % len(손)) if 긴 else P.을(P._나열(손)),
                                                       P.곳(맥, 맥.절["파일"])))
             if 손 and 맥.절.get("파일") else ""), ""]
    elif 손 and 긴:                                          # v27 교열 230
        L += ["판단이 다른 독자는 평가 모델 파일에서 다음 가정을 바꿔 주당가치를 직접 계산할 수 있습니다.", ""] + ["- %s" % x for x in 손] + [""]
    elif 손:                                                 # v27 교열 230 · 231
        L += ["판단이 다른 독자는 평가 모델 파일에서 가정을 바꿔 주당가치를 직접 계산할 수 있습니다. 바꿔 볼 가정은 %s." % P.입니다(P._나열(손)), ""]
    N = 맥.가정.get("Narrative") or {}
    다 = 펴기(맥, N.get("다음점검"), "Narrative.다음점검") if isinstance(N, dict) else ""
    # 1.1.21 — 「그때 모니터링 신호를 확인하고 … 판정합니다」(서른 곳 같은 방법 문장)는 지운다 — 변화 유형과 고칠 범위는 모니터링 절의 표가 말한다
    if 다 and not (P.독자층(맥) and 맥.절.get("이야기점검")):    # 통독 v3 하-8 — 독자 층은 막 첫 문단이 점검일을 적었다(한 막에 한 번)
        L += ["다음 점검은 %s 뒤입니다." % 다.rstrip("."), ""]
    맥.서술("평가자의 자리")
    return L


def 손잡이목록(맥):
    """독자가 바꿔 볼 가정 — 지렛대(결론 「주당가치를 좌우하는 가정」 · 1.1.21) · 민감도 손잡이 · 역산 축 · 표2 의 두 축(이름, 차례 그대로 · 겹침 없이).
    1.1.21 — 종전에는 민감도 표 Ⅲ 의 관행 손잡이(영구성장률 · WACC · 영구기간 영업이익률)만 실어 그 회사의 지렛대 가정이 빠졌다(서른 곳 같은 목록)."""
    import 레터1부 as P                                    # noqa: PLC0415
    d = 지렛대(맥)
    낸 = [x.strip() for x in ("%s" % (d.get("이름") or "")).split(" · ") if x.strip()] if d else []
    for r in ((맥.민 or {}).get("표3") or []):
        낸.append(P.손잡이이름({"이름": r["이름"], "대상": r["대상"], "방식": r.get("방식")}, 맥))
    if (맥.민 or {}).get("표5"):
        낸 += list(표2이름(맥))
    return [이름다듬기(x) for x in dict.fromkeys(x for x in 낸 if x)]


def 표2이름(맥):
    """민감도 표2 의 두 축 이름 — 손잡이 이름(판매단가 명칭으로 통일 — R1b · L5)."""
    import 레터1부 as P                                    # noqa: PLC0415
    t5 = (맥.민 or {}).get("표5") or {}
    표2 = (맥.가정.get("민감도") or {}).get("표2") or {}
    h세 = {"이름": t5.get("세로이름"), "대상": (표2.get("세로") or {}).get("대상") or []}
    h가 = {"이름": t5.get("가로이름"), "대상": (표2.get("가로") or {}).get("대상") or []}
    return P.손잡이이름(h세, 맥), P.손잡이이름(h가, 맥)


# ══════════════════════════════════════════════════════════════════ 6. 가격 위치 격자(M7)

격자한도 = 40                         # 세로 축을 넓히는 칸 수의 한도(한 쪽)


def 격자축(원):
    """민감도 표2 의 두 축을 종가가 들어오는 칸과 세 시나리오의 자리까지 넓힌 축 → (h세, 세x, h가, 가x) 또는 None.
    세로 축은 값 목록의 간격으로 넓힌다(종가 칸 + 한 칸, 시나리오 값을 덮는 데까지). 가로 축은 그대로(시나리오 값이 밖이면 더한다)."""
    import 레터 as _L                                       # noqa: PLC0415
    가정 = 원["가정"]
    표2 = (가정.get("민감도") or {}).get("표2")
    t5 = (원.get("민") or {}).get("표5")
    종 = _n(((원.get("민") or {}).get("표4") or {}).get("종가"))
    if not (isinstance(표2, dict) and t5 and 종 and "값" in (표2.get("세로") or {}) and "값" in (표2.get("가로") or {})):
        return None
    세, 가 = 표2["세로"], 표2["가로"]
    h세 = {"이름": 세["이름"], "대상": ["%s" % x for x in 세["대상"]], "방식": "값"}
    h가 = {"이름": 가["이름"], "대상": ["%s" % x for x in 가["대상"]], "방식": "값"}
    세x = [float(x) for x in 세["값"]]
    가x = [float(x) for x in 가["값"]]
    if len(세x) < 2:
        return None
    폭 = round(세x[1] - 세x[0], 10)

    def 시값(h):
        낸 = []
        for s in 시나리오들:
            v = _n(_L._시점값(가정, h["대상"][0], s)) if h["대상"][0] in (가정.get("시점가정") or {}) else None
            if v is not None:
                낸.append(v)
        return 낸
    for v in 시값(h가):
        if all(abs(v - x) > 1e-9 for x in 가x):
            가x.append(v)
    가x = sorted(가x)
    시세 = 시값(h세)
    while 시세 and min(시세) < 세x[0] - 1e-9 and len(세x) < 격자한도:
        세x.insert(0, round(세x[0] - 폭, 10))
    최대 = max(max(r for r in 줄 if _n(r) is not None) for 줄 in t5["값"] if any(_n(r) is not None for r in 줄))
    더 = 0
    while (최대 < 종 or (시세 and max(시세) > 세x[-1] + 1e-9)) and 더 < 격자한도:
        세x.append(round(세x[-1] + 폭, 10))
        더 += 1
        최대 = max(최대, max((_L._계산.계산(_L._민감도.움직이기(_L._민감도.움직이기(가정, h세, 세x[-1], "기준"), h가, xg, "기준"),
                                       "기준")["요약"]["주당가치"]) for xg in 가x))
    if 최대 >= 종:
        세x.append(round(세x[-1] + 폭, 10))                    # 종가 칸 위로 한 칸
    return h세, 세x, h가, 가x


def 격자셈(원):
    """격자 — {"세로": [x], "가로": [x], "값": [[주당]], "자리": {시나리오: (i, j) 또는 None}} (원 「_격자」 에 담아 둔다)."""
    if "_격자" in 원:
        return 원["_격자"]
    import 레터 as _L                                       # noqa: PLC0415
    축 = 격자축(원)
    if 축 is None:
        원["_격자"] = None
        return None
    h세, 세x, h가, 가x = 축
    t = _L._민감도._격자(원["가정"], "기준", (h세, 세x), (h가, 가x))
    자리 = {}
    for s in 시나리오들:
        vs = _n(_L._시점값(원["가정"], h세["대상"][0], s))
        vg = _n(_L._시점값(원["가정"], h가["대상"][0], s))
        i = next((k for k, x in enumerate(세x) if vs is not None and abs(x - vs) < 1e-9), None)
        j = next((k for k, x in enumerate(가x) if vg is not None and abs(x - vg) < 1e-9), None)
        자리[s] = (i, j) if i is not None and j is not None else None
    원["_격자"] = {"세로": 세x, "가로": 가x, "값": [[_n(v) for v in 줄] for 줄 in t["값"]], "자리": 자리,
                "세로이름": h세["이름"], "가로이름": h가["이름"], "h세": h세, "h가": h가}
    return 원["_격자"]


def 격자값(부, 원):
    """장부 키 「가:격자:…」 — 가:격자:값:<i>:<j> · 가:격자:세로:<i> · 가:격자:가로:<j>."""
    g = 격자셈(원)
    if g is None:
        return None
    if 부[0] == "값":
        return g["값"][int(부[1])][int(부[2])]
    if 부[0] == "세로":
        return g["세로"][int(부[1])]
    if 부[0] == "가로":
        return g["가로"][int(부[1])]
    raise KeyError("모르는 격자 키: %s" % ":".join(부))


def 격자줄(맥):
    """14절의 가격 위치 격자 — 13절의 두 축 표를 종가가 들어오는 칸까지 넓히고 세 시나리오의 자리를 적는다(제안 2.5 · M7)."""
    import 레터1부 as P                                    # noqa: PLC0415
    g = 격자셈(맥.원)
    if g is None or not 맥.종가키:
        return []
    h세, h가 = g["h세"], g["h가"]
    세꼴, 가꼴 = P.손잡이꼴(h세, 맥), P.손잡이꼴(h가, 맥)
    세이름, 가이름 = P.손잡이이름(h세, 맥), P.손잡이이름(h가, 맥)
    종 = _n(맥.값(맥.종가키))
    자리 = {}
    for s, ij in g["자리"].items():
        if ij:
            자리.setdefault(ij, []).append(s)
    줄들 = []
    for i in range(len(g["세로"])):
        줄 = [맥.수("가:격자:세로:%d" % i, 세꼴)]
        for j in range(len(g["가로"])):
            v = g["값"][i][j]
            if v is None:
                줄.append("—")
                continue
            글 = 맥.수("가:격자:값:%d:%d" % (i, j), "주당")
            if 종 and v >= 종:
                글 = "**%s**" % 글
            if (i, j) in 자리:
                글 += " (%s 시나리오)" % " · ".join(자리[(i, j)])
            줄.append(글)
        줄들.append(줄)
    L = ["### 가격 위치 격자", ""]
    L.append("%s × %s 표를 %s 들어오는 칸까지 넓혔습니다(%d절). 칸의 값은 기준 시나리오에서 두 가정만 바꾼 주당가치입니다." % (
        세이름, 가이름, P.이(P.종가말(맥)), 맥.절["민감도"]))
    L.append("굵은 칸은 주당가치가 이 가격 이상인 칸입니다. 괄호 안에 시나리오 이름을 적은 칸은 그 시나리오가 두 가정에 적용한 값의 칸입니다.")
    L.append("이 칸의 주당가치는 다른 가정을 기준 시나리오대로 둔 값이라 그 시나리오의 주당가치와 다릅니다.")
    L.append("")
    L += P._표(["%s \\ %s" % (세이름, 가이름)] + [맥.수("가:격자:가로:%d" % j, 가꼴) for j in range(len(g["가로"]))], 줄들)
    L.append("")
    맥.서술("역산.격자")
    return L


# ══════════════════════════════════════════════════════════════════ 7. 지난 평가와의 다리(M8)

def 지난찾기(가정, 경로):
    """지난 회차의 가정 파일 — Narrative.지난평가.파일(회차 폴더 기준) → (가정, 경로) 또는 (None, 까닭)."""
    N = 가정.get("Narrative") or {}
    지 = N.get("지난평가") if isinstance(N, dict) else None
    if not isinstance(지, dict) or not _글(지.get("파일")):
        return None, None
    p = 지["파일"]
    if not os.path.isabs(p) and 경로:
        p = os.path.join(os.path.dirname(os.path.abspath(경로)), p)
    if not os.path.isfile(p):
        return None, "지난 평가의 가정 파일이 없다: %s" % 지["파일"]
    try:
        with io.open(p, encoding="utf-8") as f:
            return json.load(f), p
    except Exception as e:                                   # noqa: BLE001
        return None, "지난 평가의 가정 파일을 못 읽었다(%s)" % e


_실적키 = ("원천", "원천근거", "기간", "일정")
_이야기키 = ("가정", "시점가정", "표", "구조")


def _옮겨심기(지금, 지난, 키들):
    """지금 가정에 지난 가정의 키들(가정 · 시점가정 · 표는 번호 · 시나리오 · 기간 ID 가 같은 칸만)을 심은 사본."""
    a = copy.deepcopy(지금)
    for k in 키들:
        if k not in 지난:
            continue
        if k in ("가정",):
            for 번, 벌 in (지난.get("가정") or {}).items():
                if 번 not in (a.get("가정") or {}) or not isinstance(벌, dict):
                    continue
                for 시, 열들 in 벌.items():
                    if isinstance(열들, dict) and isinstance(a["가정"][번].get(시), dict):
                        for c, v in 열들.items():
                            if c in a["가정"][번][시]:
                                a["가정"][번][시][c] = copy.deepcopy(v)
        elif k in ("시점가정", "표"):
            for 번, v in (지난.get(k) or {}).items():
                if 번 in (a.get(k) or {}):
                    a[k][번] = copy.deepcopy(v)
        elif k == "구조":
            continue                                         # 구조는 옮기지 않는다(축 · 줄이 갈린다 — 값만 옮긴다)
        else:
            a[k] = copy.deepcopy(지난[k])
    return a


def 지난셈(원):
    """→ {"지난": 주당, "실적": 주당, "이야기": 주당, "지금": 주당} — 지난 가정에서 지금 가정으로 한 번에 하나씩(실적 갱신 →
    Narrative → 할인율). 실적 갱신 = 지금 가정에 지난 가정의 가정 값 · WACC 를 심은 판(기간 ID 가 같은 칸만), Narrative = 지난 WACC 만 심은 판."""
    if "_지난" in 원:
        return 원["_지난"]
    import 레터 as _L                                       # noqa: PLC0415
    지난 = 원.get("지난")
    if not isinstance(지난, dict):
        원["_지난"] = None
        return None
    지금 = 원["가정"]
    def 주(a):
        return _L._계산.계산(a, "기준")["요약"]["주당가치"]
    낸 = {"지난": 주(지난)}
    a1 = _옮겨심기(지금, 지난, ("가정", "시점가정", "표"))
    a1["WACC"] = copy.deepcopy(지난.get("WACC") or a1.get("WACC"))
    낸["실적"] = 주(a1)
    a2 = copy.deepcopy(지금)
    a2["WACC"] = copy.deepcopy(지난.get("WACC") or a2.get("WACC"))
    낸["이야기"] = 주(a2)
    낸["지금"] = 원["R"]["기준"]["요약"]["주당가치"]
    원["_지난"] = 낸
    return 낸


def 지난값(부, 원):
    r = 지난셈(원)
    return None if r is None else r.get(부[0])


def 다리절(맥, 번):
    """지난 평가와의 다리(제안 2.8 · M8) — 둘째 회차부터, 지난 회차 파일이 있을 때만."""
    import 레터1부 as P                                    # noqa: PLC0415
    지 = (맥.가정.get("Narrative") or {}).get("지난평가") or {}
    L = ["## %d. 지난 평가와 이번 평가의 값 차이" % 번, ""]
    import 어투                                              # noqa: PLC0415
    날 = 맥.원고글(P.날짜말(지.get("날짜")), "Narrative.지난평가.날짜")
    차 = (_n(맥.값("R:기준:2.DCF:68")) or 0.0) - (_n(맥.값("가:지난:지난")) or 0.0)
    L.append("지난 평가(%s)의 주당가치 %s 이번에 %s %s." % (날, P.은(맥.수("가:지난:지난", "주당")), P.으로(맥.수("R:기준:2.DCF:68", "주당")),
                                                 어투.방향(차, "올랐습니다", "내렸습니다", "같았습니다")))

    def 몫(식):                                              # v27 — 방향은 낱말로(부호 · 「움직였다」 대신 「… 올랐고 · 내렸고」)
        v = _n(맥.식값(식)) or 0.0
        return "%s %s" % (맥.식(식 if v >= 0 else ["음", 식], "주당"), 어투.방향(v, "올랐", "내렸", "같았"))
    L.append("그 차이는 실적 갱신으로 %s고, Narrative 변경으로 %s고, 할인율로 %s습니다." % (
        몫(["−", "가:지난:실적", "가:지난:지난"]), 몫(["−", "가:지난:이야기", "가:지난:실적"]), 몫(["−", "R:기준:2.DCF:68", "가:지난:이야기"])))
    if 지.get("갈래"):
        까 = 펴기(맥, 지.get("까닭"), "Narrative.지난평가.까닭")
        L.append("Narrative 변경은 %s로 판정했습니다.%s" % (지["갈래"], (" " + 까) if 까 else ""))
    L.append("가정을 한 번에 하나씩 바꿔 계산했습니다. 지난 평가의 가정과 WACC 값을 이번 기간에 옮겨 실적 갱신에 따른 차이를 따로 구했고, "
             "이번에 새로 생긴 기간에는 이번 값을 적용했습니다.")
    L.append("")
    맥.서술("지난평가")
    return L


# ══════════════════════════════════════════════════════════════════ CLI

def main():
    sys.stdout.reconfigure(encoding="utf-8")
    인자 = [x for x in sys.argv[1:] if not x.startswith("--")]
    if "--검사" not in sys.argv or len(인자) != 1:
        print(__doc__)
        raise SystemExit(2)
    with io.open(인자[0], encoding="utf-8") as f:
        가정 = json.load(f)
    오류, 경보 = 입력검사(가정)
    for x in 오류:
        print("오류 — %s" % x)
    for x in 경보:
        print("경보 — %s" % x)
    print("Narrative 키 검사 — 오류 %d · 경보 %d" % (len(오류), len(경보)))
    raise SystemExit(2 if 오류 else 0)


if __name__ == "__main__":
    main()

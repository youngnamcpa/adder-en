# -*- coding: utf-8 -*-
"""**스트림 병합** — B1(앞 국면)과 B2(심화 국면)의 웹조사 산출물을 하나로 합친다.

    python 스크립트/스트림병합.py _raw/매출스트림_웹조사.json _raw/매출스트림_심화.json

왜 스크립트가 합치나 — **에이전트가 합치면 고르게 된다.** 두 국면이 같은 것을 다르게 말했을 때
사람이 보기 전에 한쪽이 사라지는 것이 가장 나쁘다. 그래서 합치는 규칙을 코드로 굳힌다.

규칙 셋.
  ① **B1 이 채운 칸은 덮지 않는다.** 멈춤 통지가 그 값으로 나갔기 때문이다.
  ② **B2 는 빈 칸을 채우고 목록에 덧붙인다.** 같은 대상이 아니면 그냥 늘어난다.
  ③ **같은 대상의 같은 칸을 다르게 말하면 고르지 않고 `충돌[]` 에 올린다.** 모순 장부가 M-09 로 읽는다.

B1 원본은 `_raw/매출스트림_웹조사_B1.json` 으로 보존되고 합본이 원래 이름을 차지한다 —
자체검사 ⑰ 과 모순장부가 이미 그 이름을 보고 있어서, **이름을 바꾸면 배선이 끊긴다.**

**같은 대상인지는 출처까지 보고 가린다.** 조사 산출물은 「출처별로 나란히, 평균 없음」이 규약이라
IEA 의 「EV 배터리 deployment」와 SNE 의 같은 이름 항목은 **다른 줄**이다. 항목 이름만으로 묶으면
두 기관의 통계가 한 줄로 뭉개진다.

**값이 어느 칸에 있는지 미리 알 수 없다.** 실측: 능력은 `GWh`, 시장은 `2025`·`2030` 칸에 값이 있었다.
그래서 고정된 「값」 칸을 찾지 않고 **칸마다 견준다** — 같은 대상의 같은 칸이 다르면 그것이 충돌이다.

── 2026-09-13 수리(펄어비스·세일즈포스 회차 실측) ──
  ⓐ **재실행은 언제나 보존된 B1 원본에서 다시 합친다.** 종전에는 합본 위에 B2 를 또 얹어서
     합본이 스스로 만든 `국면` 칸이 B2 의 `국면` 문자열과 「충돌」했고, 충돌 수가 7→1(펄)·3→4(CRM)로
     흔들렸다. 장부의 순번 ID 가 그 흔들림을 따라 밀려 **사람이 적은 처리 문장이 엉뚱한 충돌에 붙었다.**
  ⓑ **에이전트가 스스로 적은 `충돌[]` 도 충돌이다.** B1·B2 가 각자 「값들」로 적은 충돌을 종전에는
     평범한 목록으로 덧붙이거나(펄: 「충돌 +3건」인데 요약은 「충돌: 없음」), 스크립트가 찾은 충돌로
     통째로 덮었다(CRM: B2 가 적은 넷이 합본에서 사라짐). 이제 셋(스크립트 검출·B1 기록·B2 기록)을
     한 형식으로 정리해 합치고 **(칸·대상·값 묶음)으로 중복을 지운다**(펄: 도깨비 시점이 두 번 오름).
     요약은 **합본 전체의 충돌 수**를 센다.
  ⓒ **B2 는 B1 파일을 못 고치므로 처리 결과를 심화 파일의 `심화_큐_처리[]` 에 적는다.**
     병합이 그것을 B1 의 `심화_큐` 줄에 번호·「무엇을」·「어디서」로 대응시켜 센다
     (종전: B1 줄의 `처리` 칸만 봐서 「12줄 중 12줄 미처리」로 잘못 셈).

── 2026-10-07 산식 개편(W7c) — 남기고 줄였다 ──
  가정 파일의 `스트림` · `물리` 블록과 전개 함수는 걷혔지만(설계서 6-2) 조사 두 국면의 산출물은 그대로 나온다 — 합치는 일과
  충돌을 고르지 않고 남기는 일(모순장부 M-09 · 자체검사 ⑰ 이 읽는다)은 새 구조에서도 같다. 엔진 결과를 읽지 않는다.
  줄인 것: 화면의 옛 물리층 안내 — 조사의 `능력` · `market_size` 칸은 이제 4번의 판매량 산정(생산능력 × 가동률 × 수율 —
  `매출구분[].판매량산정 = 능력`)과 시장점유율 대조(`점유율대조 = 예`)의 근거 재료다. 값은 사람이 근거와 함께 가정에 적는다.

── 2026-10-16 수리(S1 리뷰) ──
  ⓓ **근거의 두께는 충돌이 아니라 보강이다.** 축의 `신뢰도` · `신뢰도_까닭` · `독립출처수` · `evidence` · `출처_성격` · `근거범위`(재리뷰에서 더함) 와 묶음
     `축_신뢰도` 는 B2 가 CP2 에서 근거를 채우면 바뀌는 것이 설계다(약 → 문항에 묶인 B2 보강 → `보강_B2` 가 그 문항 문장에). 종전에는 이 칸들이 다르면
     M-09(high) 충돌 여섯 건이 생기고 합본은 「약」 그대로였다. 이제 B1 값은 그대로 두고(규칙 ① — 사람이 본 값) B2 값을
     `보강_B2{}` 에, 신뢰도가 바뀐 자리를 `신뢰도_변경[]`(칸 · 대상 · 옛 · 새 · 근거)에 남긴다 — 충돌로 올리지 않는다.
  ⓓ' **B2 가 신뢰도를 올린 축은 축 칸에 올린다(2026-10-24 W18 · 유니버스 조사 결함 3).** 합본 축이 「약」 그대로라 뒤 도구가 B2 의 보강을 못 썼다.
     올린 축만 신뢰도 · 까닭 · 독립출처수 · 근거범위를 올리고 B1 값은 `…_B1` · `보강_올림` 에 남긴다. 내리거나 같은 등급의 보강은 종전대로 `보강_B2` 에만.
  ⓔ **「F 이관」은 남음이 아니다.** B2 가 능력 · 투자 줄을 「F 의 몫」으로 넘겼으면 그 줄은 B2 미처리가 아니라 F 투자능력이
     가져간 것이다. `심화_큐_셈.이관` 으로 따로 세고 `심화_큐_남음` 에서 뺀다.

── 2026-10-18 수리(S9 재리뷰 S9R1-N1) ──
  ⓕ **근거범위가 빈 축을 경보한다.** 거친 바퀴는 근거 범위가 없는 축을 순위에 넣지 못하고 「범위를 묻는 문항」으로만 올린다. 실제 B1 산출에서 축
     열두 개가 모두 `근거범위` 없이 나온 일이 있다 — 병합(B2 가 없어 그대로 두는 경로도)이 빈 축 이름을 `근거범위_빈축[]` 에 적고 화면에 경보한다.

── 2026-10-25 수리(FX-D · 유니버스 F 물결 결함 R11) ──
  ⓖ **평가기준일은 회차 기준일 하나다.** 갈래 산출이 기준일 뒤 분기 말(「2026-07-26」 · 「2026-09-30」)을 평가기준일로 적어 기준일 꼬리표가 그 날짜로
     돌았다. `--기준일`(없으면 같은 `_raw/` 의 동인원천 · 투자능력 · 외부제약이 적은 평가기준일)을 회차 기준일로 삼아 합본에 강제하고, B1 · B2 가 다르면
     `평가기준일_갈림{회차 · B1 · B2}` 경보 · 옛 값은 `평가기준일_원래`. 기준일 꼬리표도 회차 기준일로 돈다.
  ⓗ **근거범위는 숫자다.** 「+40%」 · 「9.0%」 · 「약 20%」 · 「2배 초과」 처럼 글로 적은 끝을 숫자로 푼다(퍼센트 글은 퍼센트 수 그대로 두고 단위에 「%」 —
     거친 바퀴가 1 넘는 퍼센트를 소수로 바꾼다 · 두 끝이 모두 1 이하 퍼센트 글이면 소수로 바꾸고 단위 「비율」). 범위 사전 안에 원문(`원문`) ·
     「약」 · 「미만」 · 「초과」(`근사[]`) · 못 푼 끝(`못풂[]` — 그 끝은 비워 반쪽 · 빈 축으로 센다)을 남긴다 — 범위와 함께 다녀 B2 보강으로 가도 섞이지 않는다.
  ⓘ **출처마다 공표일.** 출처 목록(리포트 · IR · company_voice · 투자_소식 · 관측치 · market_size · 능력 · 원가_구조 · 제품_로드맵 · 공시먼저)의 항목에
     날짜(공표일 · 발행일 · 날짜 칸 · 글 속 온전한 날짜 · 접수번호)도 기간 표지(분기 · 반기 · 공시 기간)도 없으면 `공표일_빈[]` 에 경로를 적고 경보한다 —
     기준일 꼬리표가 가르지 못하는 출처다.
  ⓙ **첫 공표일.** 같은 계획을 기준일 전에 처음 발표했고 기준일 뒤 콜이 다시 말한 것이면 항목에 `첫공표일` 을 적는다 — `첫공표일 ≤ 기준일` 이고
     `기준일뒤: true` 인 항목은 `기준일뒤: false` · `기준일뒤_첫공표일` 로 바로잡는다(기준일에 알 수 있던 정보). 근거 범위는 자동으로 되돌리지 않고
     `근거범위_첫공표일` 로 「기준일 전 발표로 다시 잡으라」 알린다. 기준일 뒤 표지가 붙은 계획 · 발언(투자_소식 · 능력 · 제품_로드맵 · company_voice)에
     `첫공표일` 이 없으면 `첫공표일_확인[]` 정보 줄.
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

이름칸 = ("항목", "이름", "공장", "설비", "name", "내용", "지표", "제품", "대상", "시장", "보고서",
       "사이클", "전방", "회사")      # 2026-11-01 A13 — 요건판 3 칸(과거 사이클 · 전방 매출 · 경쟁 위치)의 이름. 회사는 맨 뒤(발화 줄은 내용이 이름)
기간칸 = ("연도", "기간", "기준일")    # A2 — 같은 이름 · 출처라도 다른 해 · 다른 기준일의 관측은 다른 줄이다(연도별 반대 대조 · 시점별 지표)
출처칸 = ("출처", "source", "출처_성격")
# 견주지 않는 칸 — 같은 대상이어도 국면마다 달라도 되는 자리
비교제외 = ("메모", "확신도", "비고", "_국면", "note", "coverage",
        "기준일사이", "기준일사이_사유", "기준일뒤_거둠", "기준일뒤_손")      # 2026-10-25 날짜 둘 — 표지 칸은 견주지 않는다
# 보강 칸 — 다르면 충돌이 아니라 B2 의 보강으로 남긴다(근거의 두께 — 값이 아니다)
# 근거범위(관측 최저 · 최고)도 근거의 두께다 — B2 가 CP2 에서 범위를 좁히거나 넓힐 근거를 채우면 그 축 문항의 보강이다(2026-10-16, S1 재리뷰 S1-04)
보강칸 = ("신뢰도", "신뢰도_까닭", "독립출처수", "evidence", "출처_성격", "근거범위")
# 최상위에서 목록 병합·칸 비교를 하지 않고 따로 다루는 열쇠 — 합본이 스스로 쓰는 열쇠도 여기
따로 = ("status", "coverage", "심화_큐", "충돌", "심화_큐_처리", "처리된_큐", "국면", "조사일",
       "_병합", "coverage_B1", "coverage_B2", "심화_큐_남음", "심화_큐_셈", "심화_큐_대응",
       "심화_큐_처리_짝없음", "충돌_셈", "축_신뢰도", "축_신뢰도_B2", "신뢰도_변경", "근거범위_빈축",
       # 2026-10-24 W17 — 국면마다 다른 장부 칸(예산 실측)은 견주지 않는다(LS ELECTRIC · AVGO 조사 — 충돌 3줄로 올라갔다). B2 것은 `예산실측_B2` 에
       "예산실측", "예산실측_B2",
       # 2026-10-24 W18 — 메타 칸(갈래 · 회사 표기 · 도구 · 시각 · 평가기준일)은 견주지 않는다(유니버스 조사 — 「B1」 대 「B2」 · 「Apple Inc. (AAPL)」 대
       # 「Apple Inc.」 가 충돌로 모순 장부에 갔다). 평가기준일이 갈리면 충돌이 아니라 따로 경보한다(`평가기준일_갈림`)
       "갈래", "회사", "회사명", "도구", "작성", "끝난시각", "만든날", "조회일", "평가기준일", "기준일뒤_셈",
       # 2026-10-25 FX-D — 병합 · 마무리가 스스로 쓰는 장부 칸(국면마다 다를 수 있다 — 견주지 않는다)
       "평가기준일_갈림", "평가기준일_원래", "회차기준일_근거", "근거범위_숫자화", "근거범위_밴드변환", "첫공표일_셈", "첫공표일_확인",
       "공표일_셈", "공표일_빈",
       # 2026-10-25 날짜 둘 — 재무기준일(F)과 그 근거도 메타 칸
       "재무기준일", "재무기준일_근거")
보존이름 = "매출스트림_웹조사_B1.json"
등급차례 = {"약": 0, "보통": 1, "강": 2}
# 2026-10-25 FX-D — 회차 기준일을 읽는 다른 갈래 산출(같은 `_raw/`) · 출처 목록 칸(공표일 검사) · 계획 · 발언 칸(첫 공표일 확인)
기준일원천 = ("동인원천.json", "투자능력.json", "외부제약.json")
출처목록칸 = ("리포트", "IR", "company_voice", "투자_소식", "관측치", "market_size", "능력", "원가_구조", "제품_로드맵", "공시먼저",
          "출처목록", "sources",
          "업황_지표", "과거_사이클", "경쟁_위치", "전방_매출", "반대_대조")     # 2026-10-31 레터 원고 요건판 3 — 업황 · 경쟁 · 전방 칸도 공표일을 잰다
계획칸 = ("투자_소식", "능력", "제품_로드맵", "company_voice")


def _n(x):
    if x is None:
        return ""
    if isinstance(x, (list, dict)):
        return json.dumps(x, ensure_ascii=False, sort_keys=True)
    return re.sub(r"\s+", " ", "%s" % x).strip()


def _이름(d):
    if not isinstance(d, dict):
        return _n(d)[:60]
    for k in 이름칸:
        v = d.get(k)
        if isinstance(v, bool):                             # A17 — 참거짓 칸(경쟁 위치의 `대상`)은 이름이 아니다
            continue
        if _n(v):
            return _n(v)[:60]
    return ""


def _기간(d):
    """항목의 기간 표지(연도 · 기간 · 기준일 가운데 처음 있는 것) — 목록 열쇠에 넣는다(A2)."""
    if not isinstance(d, dict):
        return ""
    for k in 기간칸:
        if _n(d.get(k)):
            return _n(d.get(k))[:20]
    return ""


def _출처(d):
    if not isinstance(d, dict):
        return ""
    for k in 출처칸:
        if _n(d.get(k)):
            return _n(d.get(k))[:50]
    return ""


def _키(d):
    """같은 대상인가 — **이름 + 출처**로 가린다. 둘 다 없으면 내용 전체(병합이 붙인 `_국면` 등은 빼고)."""
    if not isinstance(d, dict):
        return _n(d)[:80]
    나, 출, 기 = _이름(d), _출처(d), _기간(d)
    if 나:
        return "%s‖%s‖%s" % (나, 기, 출) if 기 else "%s‖%s" % (나, 출)
    # 2026-10-24 W17 — 이름 칸 없이 출처만 있는 항목(회사 발화 · company_voice)은 한 출처에 여러 줄이다 — 출처만으로 묶으면 서로 다른 발화가
    # 충돌로 올라갔다(AVGO 조사). 이름이 없으면 출처 + 내용으로 가린다
    return "%s‖%s" % (출, json.dumps({k: v for k, v in d.items() if k not in 비교제외},
                                      ensure_ascii=False, sort_keys=True)[:200])


def _대상말(d):
    """사람이 읽는 대상 이름 — 내부 키 구분자(‖)를 쓰지 않는다."""
    나, 출 = _이름(d), _출처(d)
    if 나:
        return 나
    if 출:
        return "%s 의 이름 없는 항목" % 출
    return "이름 없는 항목"


def _비었나(v):
    if v is None:
        return True
    if isinstance(v, str):
        return not v.strip()
    if isinstance(v, (list, dict)):
        return len(v) == 0
    return False


# ── 충돌 정리 ─────────────────────────────────────────────────────────────
_숫자괄호 = re.compile(r"^[+\-−~≈]?\s*[\d.,]+\s*[%배x×]?\s*$")


def 값출처가르기(s):
    """「2028 하반기(인벤·삼성증권)」 → ("2028 하반기", "인벤·삼성증권", 국면표시).
    **맨 끝 괄호만** 출처로 본다. 괄호 안이 숫자뿐이면(「(+7.4%)」) 출처가 아니다.
    괄호 안이 「B1: …」·「B2: …」로 시작하면 국면 표시로 떼어 낸다."""
    s = _n(s)
    국 = ""
    if not s.endswith(")"):
        return s, "", 국
    깊이, i = 0, len(s) - 1
    while i >= 0:
        if s[i] == ")":
            깊이 += 1
        elif s[i] == "(":
            깊이 -= 1
            if 깊이 == 0:
                break
        i -= 1
    if i <= 0:
        return s, "", 국
    값, 안 = s[:i].strip(), s[i + 1:-1].strip()
    if not 값 or not 안 or _숫자괄호.match(안):
        return s, "", 국
    m = re.match(r"^(B1|B2)\s*[:：]\s*(.*)$", 안)
    if m:
        국, 안 = m.group(1), m.group(2).strip()
    return 값, 안, 국


def _정규(s):
    return re.sub(r"[\s\"'`「」『』()（）\[\]·,.:：;/\\\-—–~]+", "", _n(s)).lower()


def 충돌정리(c, 기록):
    """세 모양을 한 모양으로.
      스크립트 검출  {"칸","대상","B1":{"값","출처"},"B2":{"값","출처"}}
      에이전트 기록  {"대상","값들":[문자열…],"비고"}  (펄어비스 B1·B2)
      에이전트 기록  {"대상","B1":문자열,"B2":문자열,"비고"}  (세일즈포스 B2)
    돌려주는 모양 — {"칸","대상","값들":[{"값","출처","국면"}…],"B1","B2","비고","기록","키"}.
    `B1`·`B2` 는 모순장부·자체검사 호환용으로 값들의 앞 둘을 담는다."""
    if not isinstance(c, dict):
        c = {"대상": _n(c)}
    칸 = _n(c.get("칸"))
    대상 = _n(c.get("대상")).lstrip("‖").strip()
    값들 = []
    if isinstance(c.get("값들"), list):
        for v in c["값들"]:
            if isinstance(v, dict):
                값들.append({"값": _n(v.get("값")), "출처": _n(v.get("출처")), "국면": _n(v.get("국면"))})
            else:
                값, 출, 국 = 값출처가르기(v)
                값들.append({"값": 값, "출처": 출, "국면": 국})
    else:
        for 국 in ("B1", "B2"):
            v = c.get(국)
            if isinstance(v, dict):
                값들.append({"값": _n(v.get("값")), "출처": _n(v.get("출처")), "국면": 국})
            elif not _비었나(v):
                값, 출, _ = 값출처가르기(v)
                값들.append({"값": 값, "출처": 출, "국면": 국})
    # 국면 표시가 있으면 B1 을 앞에
    값들.sort(key=lambda v: {"B1": 0, "B2": 1}.get(v["국면"], 2))
    if not 대상 and "‖" in _n(c.get("대상")):
        대상 = _n(c.get("대상")).replace("‖", " ").strip()
    키 = "%s|%s|%s" % (칸, _정규(대상), "|".join(sorted({_정규(v["값"]) for v in 값들})))
    쌍 = {}
    for i, 국 in enumerate(("B1", "B2")):
        if i < len(값들):
            쌍[국] = {"값": 값들[i]["값"], "출처": 값들[i]["출처"]}
    return {"칸": 칸, "대상": 대상, "값들": 값들, "B1": 쌍.get("B1", {"값": "", "출처": ""}),
            "B2": 쌍.get("B2", {"값": "", "출처": ""}), "비고": _n(c.get("비고")),
            "기록": 기록, "키": 키}


def 충돌모으기(묶음):
    """[(기록이름, [충돌…])…] → 정리·중복 제거한 목록과 셈."""
    나온, 셈 = [], {"중복제거": 0}
    표 = {}
    for 기록, 벌 in 묶음:
        셈[기록] = 0
        for c in 벌 or []:
            x = 충돌정리(c, 기록)
            셈[기록] += 1
            if x["키"] in 표:
                옛 = 표[x["키"]]
                셈["중복제거"] += 1
                if 기록 not in 옛["기록"]:
                    옛["기록"] = "%s · %s" % (옛["기록"], 기록)
                # 같은 값의 출처는 합친다 — 한쪽이 원문을 봤으면 그 출처가 남아야 한다
                for v in x["값들"]:
                    짝 = next((w for w in 옛["값들"] if _정규(w["값"]) == _정규(v["값"])), None)
                    if 짝 is not None and v["출처"] and v["출처"] not in 짝["출처"]:
                        짝["출처"] = ("%s · %s" % (짝["출처"], v["출처"])).strip(" ·")
                if x["비고"] and x["비고"] not in 옛["비고"]:
                    옛["비고"] = ("%s · %s" % (옛["비고"], x["비고"])).strip(" ·")
                for i, 국 in enumerate(("B1", "B2")):
                    if i < len(옛["값들"]):
                        옛[국] = {"값": 옛["값들"][i]["값"], "출처": 옛["값들"][i]["출처"]}
                continue
            # 2026-10-24 W18 — 두 국면이 같은 대상을 각자 적으면 칸 글자 · 값 문구가 달라 둘로 셌다(유니버스 조사 — 충돌 3 → 실제 2).
            # 에이전트 기록(B1 기록 · B2 기록)끼리는 대상 이름(정규화)이 같으면 한 줄로 묶고 값을 합친다(스크립트 검출은 칸까지 본다)
            대 = _정규(x["대상"])
            짝 = next((y for y in 나온 if 대 and _정규(y["대상"]) == 대 and y["기록"] != "스트림병합" and 기록 != "스트림병합"
                      and 기록 not in y["기록"].split(" · ")), None)
            if 짝 is not None:
                셈["중복제거"] += 1
                짝["기록"] = "%s · %s" % (짝["기록"], 기록)
                for v in x["값들"]:
                    if not any(_정규(w["값"]) == _정규(v["값"]) for w in 짝["값들"]):
                        짝["값들"].append(v)
                if x["비고"] and x["비고"] not in 짝["비고"]:
                    짝["비고"] = ("%s · %s" % (짝["비고"], x["비고"])).strip(" ·")
                표[x["키"]] = 짝
                continue
            표[x["키"]] = x
            나온.append(x)
    return 나온, 셈


# ── 심화_큐 대응 ──────────────────────────────────────────────────────────
def _구분(글):
    g = _n(글)
    if re.search(r"F\s*(의\s*몫|이관|로\s*넘|에\s*넘)|이관", g):          # F 투자능력이 가져간 줄 — 미처리가 아니다
        return "이관"
    for 머리, 뜻 in (("미처리", "미처리"), ("처리 안", "미처리"), ("부분", "부분"), ("처리", "처리"), ("완료", "처리")):
        if g.startswith(머리):
            return 뜻
    for 말, 뜻 in (("미처리", "미처리"), ("부분", "부분"), ("처리", "처리")):
        if 말 in g:
            return 뜻
    return "불명"


def _조각(s):
    return [t for t in re.split(r"[\s·,/()（）\[\]'\"「」—–\-:：]+", _n(s).lower()) if len(t) >= 2]


def 큐대응(큐, 기록들):
    """B1 `심화_큐` 줄마다 B2 의 `심화_큐_처리` 기록을 짝짓는다.
    짝 찾는 순서 — ① `큐`/`번호` 가 정수면 1부터 센 줄 번호 ② 「무엇을」(또는 문자열 `큐`)이
    줄의 앞머리이거나 서로 포함 ③ 조각 일치율 0.6 이상 중 가장 높은 줄 ④ 「어디서」 일치."""
    짝 = [None] * len(큐)
    짝없음 = []
    무엇 = [_정규((q or {}).get("무엇을") if isinstance(q, dict) else q) for q in 큐]
    어디 = [_정규((q or {}).get("어디서")) if isinstance(q, dict) else "" for q in 큐]
    for p in 기록들 or []:
        if not isinstance(p, dict):
            p = {"무엇을": _n(p), "결과": _n(p)}
        글 = p.get("결과") or p.get("처리") or p.get("상태") or ""
        번 = p.get("번호", p.get("큐"))
        자리 = None
        if isinstance(번, int) or (isinstance(번, str) and 번.strip().isdigit()):
            i = int(번) - 1
            if 0 <= i < len(큐) and 짝[i] is None:
                자리 = i
        글감 = p.get("무엇을") or (번 if isinstance(번, str) and not 번.strip().isdigit() else "")
        if 자리 is None and 글감:
            g = _정규(글감)
            for i, w in enumerate(무엇):
                if 짝[i] is None and g and w and (w.startswith(g) or g in w or w in g):
                    자리 = i
                    break
            if 자리 is None:
                조 = _조각(글감)
                best, bi = 0.0, None
                for i, w in enumerate(무엇):
                    if 짝[i] is not None or not 조:
                        continue
                    r = sum(1 for t in 조 if _정규(t) and _정규(t) in w) / len(조)
                    if r > best:
                        best, bi = r, i
                if best >= 0.6:
                    자리 = bi
        if 자리 is None and p.get("어디서"):
            g = _정규(p.get("어디서"))
            for i, w in enumerate(어디):
                if 짝[i] is None and g and w and (g in w or w in g):
                    자리 = i
                    break
        if 자리 is None:
            짝없음.append(p)
            continue
        짝[자리] = (_구분(글), _n(글))
    셈 = {"전체": len(큐), "처리": 0, "부분": 0, "미처리": 0, "불명": 0, "기록없음": 0, "이관": 0}
    대응 = []
    for i, q in enumerate(큐):
        if 짝[i] is None and isinstance(q, dict) and q.get("처리"):
            짝[i] = (_구분(q.get("처리")) if isinstance(q.get("처리"), str) else "처리", _n(q.get("처리")))
        구, 글 = 짝[i] if 짝[i] else ("기록없음", "")
        셈[구] += 1
        대응.append({"번호": i + 1, "무엇을": _n((q or {}).get("무엇을") if isinstance(q, dict) else q)[:60],
                   "구분": 구, "B2_기록": 글[:160]})
    # **남음 = 미처리 + 기록없음 + 불명.** 「부분」은 B2 가 열어 보고 받을 수 있는 만큼 받은 줄이라
    # 다시 큐에 넣어도 더 나오지 않는다 — 남음에 넣지 않고 따로 센다(무엇이 빠졌는지는 기록 문장에).
    # 「이관」(F 의 몫으로 넘긴 줄)도 남음이 아니다 — F 투자능력이 가져갔다
    남음 = 셈["미처리"] + 셈["기록없음"] + 셈["불명"]
    return 대응, 셈, 남음, 짝없음


# ── 회차 기준일 · 근거범위 숫자 · 공표일 · 첫 공표일(2026-10-25 FX-D — R11) ─────────────────────
def _일(v):
    """'YYYY-MM-DD' · 'YYYY.MM.DD' · 'YYYY/MM/DD'(뒤에 시각이 붙어도) → 'YYYY-MM-DD' | ''."""
    m = re.match(r"^\s*(\d{4})[-./](\d{1,2})[-./](\d{1,2})", "%s" % (v or ""))
    if not m:
        return ""
    y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
    return "%04d-%02d-%02d" % (y, mo, d) if 1 <= mo <= 12 and 1 <= d <= 31 else ""


def _조사상한(*사전들):
    """기준일 뒤 판정의 위 끝(그보다 늦은 날짜는 공표일이 될 수 없다고 본다) — 「조사일」 로 시작하는 맨 위 칸과 항목마다의
    「조회일」 가운데 가장 늦은 날. 1.1.10 — 보충 조사(심화)가 B1 조사일 뒤에 들어오면 B1 조사일을 위 끝으로 써서
    그 사이 공표 줄에 표지가 안 붙었다(보충 회차가 있는 회사 넷 · 조사일 B1 10-24 · 보충 11-05). 날짜가 없으면 None(오늘)."""
    날들 = []

    def 훑기(x):
        if isinstance(x, dict):
            for k, v in x.items():
                if k == "조회일" or ("%s" % k).startswith("조사일"):
                    d = _일(v)
                    if d:
                        날들.append(d)
                훑기(v)
        elif isinstance(x, list):
            for v in x:
                훑기(v)
    for s in 사전들:
        if isinstance(s, dict):
            for k, v in s.items():
                if ("%s" % k).startswith("조사일") and _일(v):
                    날들.append(_일(v))
            훑기(s)
    return max(날들) if 날들 else None


def 정본기준일(raw폴더, 칸="평가기준일"):
    """회차의 정본 날짜 → (값 | None, 근거). `_raw/` 곁의 진행판(`_회차실행/진행판.json` 회사.평가기준일 · 재무기준일)이 먼저, 그다음
    곁의 가정 파일 하나(`가정_*.json` — 예시 · 템플릿 제외 · `기준일.py` 로 푼다). 갈래 산출 머리의 날짜보다 앞선다(A4 · A8 — 두 날짜 회차에서
    갈래 산출 머리가 옛 기준일(재무기준일)을 적어 기준일 뒤 판정이 밀렸다). 재무기준일이 없으면 평가기준일(F = T)."""
    곳 = os.path.dirname(os.path.abspath(raw폴더 or "."))
    try:
        판 = json.load(io.open(os.path.join(곳, "_회차실행", "진행판.json"), encoding="utf-8"))
        회 = (판 or {}).get("회사") or {}
        v = _일(회.get(칸)) or (_일(회.get("평가기준일")) if 칸 == "재무기준일" else "")
        if v:
            return v, [("_회차실행/진행판.json", v)]
    except (OSError, ValueError, AttributeError):
        pass
    import glob as _g                                         # noqa: PLC0415
    가들 = [p for p in _g.glob(os.path.join(곳, "가정_*.json")) if not re.search(r"가정_(예시|템플릿)", os.path.basename(p))]
    if len(가들) == 1:
        try:
            import 기준일 as _기                               # noqa: PLC0415
            g = json.load(io.open(가들[0], encoding="utf-8"))
            d = _기.재무기준일(g) if 칸 == "재무기준일" else _기.평가기준일(g)
            if d:
                return d.isoformat(), [(os.path.basename(가들[0]), d.isoformat())]
        except Exception:                                     # noqa: BLE001
            pass
    return None, []


def 정본결산월(raw폴더):
    """진행판(회사.결산월) → 가정 파일 하나(기간.결산월) 차례로 결산월 → int | None."""
    곳 = os.path.dirname(os.path.abspath(raw폴더 or "."))
    try:
        v = (((json.load(io.open(os.path.join(곳, "_회차실행", "진행판.json"), encoding="utf-8")) or {}).get("회사") or {}).get("결산월"))
        if v:
            return int(v)
    except (OSError, ValueError, AttributeError, TypeError):
        pass
    import glob as _g                                         # noqa: PLC0415
    가들 = [p for p in _g.glob(os.path.join(곳, "가정_*.json")) if not re.search(r"가정_(예시|템플릿)", os.path.basename(p))]
    if len(가들) == 1:
        try:
            v = ((json.load(io.open(가들[0], encoding="utf-8")) or {}).get("기간") or {}).get("결산월")
            return int(v) if v else None
        except (OSError, ValueError, AttributeError, TypeError):
            return None
    return None


def 회차기준일(raw폴더, 칸="평가기준일"):
    """회차 기준일 → (값 | None, [(근거, 값)]). 정본(진행판 · 가정 — `정본기준일`)이 있으면 그것, 없으면 같은 `_raw/` 의 다른 갈래 산출
    (동인원천 · 투자능력 · 외부제약)이 적은 평가기준일 — 갈리면 가장 많은 값.
    `칸="재무기준일"` 이면 같은 차례로 재무기준일(2026-10-25 날짜 둘 — 없으면 None · 그러면 F = T)."""
    v, 근 = 정본기준일(raw폴더, 칸)
    if v:
        return v, 근
    본 = []
    for 이름 in 기준일원천:
        p = os.path.join(raw폴더 or ".", 이름)
        try:
            d = json.load(io.open(p, encoding="utf-8"))
        except (OSError, ValueError):
            continue
        v = _일((d or {}).get(칸)) if isinstance(d, dict) else ""
        if v:
            본.append((이름, v))
    if not 본:
        return None, 본
    셈 = {}
    for _, v in 본:
        셈[v] = 셈.get(v, 0) + 1
    return sorted(셈.items(), key=lambda x: (-x[1], x[0]))[0][0], 본


def 기준일맞춤(합, b1, b2, 기준일=None, 보고=None):
    """합본 평가기준일을 회차 기준일로 강제한다(ⓖ) → 맞춘 기준일 | 합본의 평가기준일. 회차 기준일이 없으면 B1 · B2 갈림만 경보(W18)."""
    보고 = 보고 if 보고 is not None else []
    회 = _일(기준일)
    원 = {k: v for k, v in (("B1", (b1 or {}).get("평가기준일")), ("B2", (b2 or {}).get("평가기준일") if b2 else None)) if v}
    if 회:
        갈 = {k: v for k, v in 원.items() if _일(v) != 회}
        if 갈:
            합["평가기준일_갈림"] = dict({"회차": 회}, **원)
            if 합.get("평가기준일") and _일(합.get("평가기준일")) != 회:
                합["평가기준일_원래"] = 합.get("평가기준일")
            보고.append("**평가기준일을 회차 기준일 %s 로 맞췄다(%s) — 갈래 산출이 다른 날을 적었다**"
                      % (회, " · ".join("%s %s" % (k, v) for k, v in 갈.items())))
        합["평가기준일"] = 회
        return 회
    if len({_일(v) for v in 원.values()}) > 1:
        합["평가기준일_갈림"] = dict(원)
        보고.append("**평가기준일이 갈렸다(%s) — 회차 기준일을 `--기준일` 로 주십시오**" % " · ".join("%s %s" % kv for kv in 원.items()))
    return _일(합.get("평가기준일")) or None


_근사앞 = re.compile(r"^\s*(약|대략|대략적으로|최소|최대|≈|~|〜|about|approx\.?|approximately|circa|c\.)\s*", re.I)
_근사뒤 = re.compile(r"(미만|이하|초과|이상|안팎|내외|정도|수준|under|below|less than|over|above|more than|plus|\+)\s*$", re.I)
_끝수 = re.compile(r"[+\-−–]?\s*\d+(?:\.\d+)?")


def 끝풀기(s):
    """근거범위의 한 끝(글) → (수, {"퍼센트", "퍼센트포인트", "배", "근사"}) | (None, None). 쉼표 천 단위는 지운다."""
    if isinstance(s, bool) or s is None:
        return None, None
    if isinstance(s, (int, float)):
        return float(s), {}
    t = ("%s" % s).strip().replace(",", "")
    if not t:
        return None, None
    근 = []
    m = _근사앞.match(t)
    if m:
        근.append(m.group(1))
        t = t[m.end():]
    t = re.sub(r"[\(（][^)）]*[\)）]", " ", t).strip()
    m = _근사뒤.search(t)
    if m:
        근.append(m.group(1))
        t = t[:m.start()].strip()
    수들 = list(_끝수.finditer(t))
    if not 수들:
        return None, None
    # 수가 여럿이면(「2026년 15%」) 단위(% · 배 · x)가 바로 붙은 수를 고른다 — 없으면 첫 수
    수 = next((m for m in 수들 if re.match(r"\s*(%|배|x\b|×)", t[m.end():], re.I)), 수들[0])
    v = float(re.sub(r"\s+", "", 수.group(0)).replace("−", "-").replace("–", "-"))
    꼬 = t[수.end():].strip().lower()
    표 = {"퍼센트": 꼬.startswith("%") and not re.match(r"%\s*(p|포인트)", 꼬),
         "퍼센트포인트": bool(re.match(r"%\s*(p|포인트)|%p|pp\b", 꼬)) or 꼬.startswith("pp"),
         "배": 꼬.startswith(("배", "x", "×")),
         "근사": " · ".join(근) if 근 else None}
    return v, 표


def 근거범위풀기(r):
    """근거범위(사전 또는 글) → (새 사전 | None, 바뀜). 글로 적힌 끝만 숫자로 바꾸고 원문 · 근사 · 못풂을 사전 안에 남긴다(ⓗ)."""
    if isinstance(r, str):
        t = r.strip()
        if not t:
            return None, False
        조각 = re.split(r"\s*(?:~|〜|∼| to |–|—)\s*", t, maxsplit=1)
        if len(조각) == 2 and 조각[0] and 조각[1]:
            r = {"최저": 조각[0], "최고": 조각[1]}
        else:
            r = {"최저": t, "최고": t}
        r["원문글"] = t
    if not isinstance(r, dict):
        return r, False
    글끝 = [k for k in ("최저", "최고") if isinstance(r.get(k), str)]
    if not 글끝:
        return r, False
    새 = dict(r)
    원문 = {k: r.get(k) for k in 글끝}
    근사, 못, 표들 = [], [], {}
    for k in 글끝:
        v, 표 = 끝풀기(r.get(k))
        if v is None:
            못.append("%s: %s" % (k, r.get(k)))
            새[k] = None
            continue
        새[k] = v
        표들[k] = 표
        if 표.get("근사"):
            근사.append("%s: %s" % (k, r.get(k)))
    단 = "%s" % (새.get("단위") or "")
    퍼 = [k for k, 표 in 표들.items() if 표.get("퍼센트")]
    수끝 = [k for k in ("최저", "최고") if k not in 글끝 and isinstance(새.get(k), (int, float))]
    if 퍼 and not 수끝 and len(퍼) == len([k for k in ("최저", "최고") if isinstance(새.get(k), (int, float))]) \
            and max(abs(새[k]) for k in 퍼) <= 1:
        for k in 퍼:                                       # 두 끝이 모두 1 이하 퍼센트 글 — 소수 비율로(거친 바퀴는 1 이하 값을 비율로 읽는다)
            새[k] = round(새[k] / 100.0, 10)
        새["단위"] = (단 + " — 비율(원문 퍼센트)").strip(" —") if 단 else "비율(원문 퍼센트)"
    elif 퍼 and not re.search(r"%|퍼센트|percent", 단, re.I):
        새["단위"] = (단 + " (%)").strip() if 단 else "%"
    if any(표.get("퍼센트포인트") for 표 in 표들.values()) and not re.search(r"%p|퍼센트포인트|pp", 단, re.I):
        새["단위"] = "%s (%%p)" % 새["단위"] if 새.get("단위") else "%p"
    if any(표.get("배") for 표 in 표들.values()) and "배" not in ("%s" % (새.get("단위") or "")):
        새["단위"] = "%s (배)" % 새["단위"] if 새.get("단위") else "배"
    lo, hi = 새.get("최저"), 새.get("최고")
    if isinstance(lo, (int, float)) and isinstance(hi, (int, float)) and lo > hi:
        새["최저"], 새["최고"] = hi, lo
        근사.append("끝 순서를 바꿈(최저 > 최고)")
    새["원문"] = 원문
    if 근사:
        새["근사"] = 근사
    if 못:
        새["못풂"] = 못
    return 새, True


def 근거범위숫자화(j, 국면="B1"):
    """`scenario_axes[]` 의 `근거범위` · `보강_B2.근거범위` 를 숫자로 푼다(제자리) → [{국면 · 축 · 칸 · 원문 · 최저 · 최고 · 못풂}]."""
    낸 = []
    for ax in ((j or {}).get("scenario_axes") or []):
        if not isinstance(ax, dict):
            continue
        자리들 = [("근거범위", ax)]
        if isinstance(ax.get("보강_B2"), dict):
            자리들.append(("보강_B2.근거범위", ax["보강_B2"]))
        for 칸, 그릇 in 자리들:
            r = 그릇.get("근거범위")
            새, 바뀜 = 근거범위풀기(r)
            if not 바뀜:
                continue
            그릇["근거범위"] = 새
            낸.append({"국면": 국면, "축": "%s" % (ax.get("name") or ax.get("이름") or "(이름 없음)"), "칸": 칸,
                      "원문": (새 or {}).get("원문글") or (새 or {}).get("원문"), "최저": (새 or {}).get("최저"),
                      "최고": (새 or {}).get("최고"), "못풂": list((새 or {}).get("못풂") or [])})
    return 낸


def _출처글(d):
    return " · ".join("%s" % v for k, v in d.items() if isinstance(v, str)
                      and k not in ("기준일뒤_사유", "기준일뒤_첫공표일", "기준일사이_사유", "기준일뒤_거둠"))


def 공표일검사(j):
    """출처 목록 칸의 항목마다 날짜 · 기간 표지가 있는가(ⓘ) → {출처항목 · 공표일 · 기간만 · 빈 · 빈자리[]}. 표지는 달지 않는다(읽기만)."""
    import 기준일뒤 as _뒤                                 # noqa: PLC0415
    날칸 = tuple(_뒤.공표칸) + ("첫공표일",)
    셈 = {"출처항목": 0, "공표일": 0, "기간만": 0, "빈": 0, "빈자리": []}
    for 칸 in 출처목록칸:
        for i, d in enumerate((j or {}).get(칸) or []):
            if not isinstance(d, dict):
                continue
            셈["출처항목"] += 1
            글 = _출처글(d)
            접 = "%s" % (d.get("접수") or d.get("원문접수") or d.get("rcept_no") or "")
            if any(_일(d.get(k)) or _뒤.공표날(d.get(k)) for k in 날칸) or re.match(r"^20\d{6}\d{6}$", 접.strip()) or _뒤.날짜들(글):
                셈["공표일"] += 1
            elif _뒤.기간끝들(글):
                셈["기간만"] += 1
            else:
                셈["빈"] += 1
                if len(셈["빈자리"]) < 40:
                    셈["빈자리"].append("%s[%d] %s" % (칸, i, (_이름(d) or 글)[:40]))
    return 셈


def 첫공표일정정(j, 기준일):
    """`첫공표일 ≤ 기준일` 인데 `기준일뒤: true` 인 항목을 바로잡고 · 근거 범위는 알리기만 · 첫 공표일이 없는 기준일 뒤 계획을 센다(ⓙ)."""
    셈 = {"정정": 0, "축": 0, "확인": []}
    기 = _일(기준일)
    if not 기:
        return 셈

    def 걷기(x):
        if isinstance(x, dict):
            첫 = _일(x.get("첫공표일"))
            if 첫 and 첫 <= 기 and x.get("기준일뒤") is True:
                x["기준일뒤"] = False
                x["기준일뒤_첫공표일"] = "처음 발표 %s ≤ 평가기준일 %s — 기준일 안 정보(기준일 뒤 출처는 다시 말한 것 · 스트림병합)" % (첫, 기)
                셈["정정"] += 1
            for v in x.values():
                걷기(v)
        elif isinstance(x, list):
            for v in x:
                걷기(v)

    걷기(j)
    for ax in ((j or {}).get("scenario_axes") or []):
        if not isinstance(ax, dict):
            continue
        r = ax.get("근거범위_기준일뒤") if isinstance(ax.get("근거범위_기준일뒤"), dict) else {}
        첫 = _일(r.get("첫공표일") or ax.get("첫공표일"))
        if 첫 and 첫 <= 기:
            ax["근거범위_첫공표일"] = ("근거 범위 출처의 계획은 %s 에 처음 발표됐다(평가기준일 전) — 기준일 전 발표 자료를 출처로 근거 범위를 "
                                  "다시 잡는다(자동으로 되돌리지 않는다)" % 첫)
            셈["축"] += 1
    for 칸 in 계획칸:
        for i, d in enumerate((j or {}).get(칸) or []):
            if isinstance(d, dict) and d.get("기준일뒤") is True and not _일(d.get("첫공표일")):
                if len(셈["확인"]) < 40:
                    셈["확인"].append("%s[%d] %s" % (칸, i, (_이름(d) or _출처글(d))[:40]))
    return 셈


def 마무리(합, 기준일, 조사일=None, 재무기준일=None, 결산월=None):
    """병합 뒤(또는 B2 없이) 합본에 차례로 — 기준일 꼬리표(W18) → 첫 공표일(ⓙ) → 밴드 변환(W15) → 빈 축 → 공표일 검사(ⓘ). 셈들을 합본에 적는다.
    `기준일` 은 평가기준일 T(정보 경계) · `재무기준일` 은 F(2026-10-25 날짜 둘 — 주고 T 보다 이르면 (F, T] 출처에 「사이」 표지 · 합본에 `재무기준일`).
    F 가 없으면 지금과 같다."""
    뒤셈 = None
    if 기준일:
        import 기준일뒤 as _뒤                             # noqa: PLC0415
        재 = _일(재무기준일)
        if 재 and 재 < _일(기준일):
            합["재무기준일"] = 재
        else:
            재 = None
        뒤셈 = _뒤.표지(합, 기준일, 조사일, 재, 결산월=결산월)          # 결산월 — 회계 분기 표지를 결산월로 푼다(A18)
        합["기준일뒤_셈"] = {k: v for k, v in 뒤셈.items() if k != "보기"}
    첫셈 = 첫공표일정정(합, 기준일)
    합["첫공표일_셈"] = {"정정": 첫셈["정정"], "축": 첫셈["축"]}
    합["첫공표일_확인"] = 첫셈["확인"]
    잇기 = 밴드잇기(합)                                  # 밴드 표현만 있는 축 → 밴드사전 범위(2026-10-24 W15)
    합["근거범위_밴드변환"] = [{"축": n, "범위": r, "못옮김": m} for n, r, m in 잇기]
    합["근거범위_빈축"] = 근거범위빈축(합)
    공셈 = 공표일검사(합)
    합["공표일_셈"] = {k: v for k, v in 공셈.items() if k != "빈자리"}
    합["공표일_빈"] = 공셈["빈자리"]
    return 뒤셈, 첫셈, 잇기, 공셈


def _마무리말(합, 뒤셈, 첫셈, 공셈, 기준일, 머리="  "):
    if 뒤셈 and (뒤셈["새표지"] or 뒤셈["이미"] or 뒤셈["축옮김"] or 뒤셈["축섞임"] or 뒤셈["밴드옮김"]):
        print("%s평가기준일 뒤 : 출처 표지 %d(새) · %d(이미) · 근거 범위 옮김 %d축 · 섞임 경보 %d축 · 밴드 옮김 %d — 축 근거 범위에 섞지 않는다(부록 G 재료)"
              % (머리, 뒤셈["새표지"], 뒤셈["이미"], 뒤셈["축옮김"], 뒤셈["축섞임"], 뒤셈["밴드옮김"]))
    elif not 기준일:
        print("%s평가기준일 뒤 : 합본에 평가기준일이 없어 가리지 못했다 — B1 산출에 `평가기준일` 을 적거나 `--기준일` 을 준다" % 머리)
    if 뒤셈 and "사이수" in 뒤셈 and (뒤셈["사이수"] or 뒤셈["축사이"] or 뒤셈["거둠"] or 뒤셈["축되돌림"] or 뒤셈["밴드되돌림"]):
        print("%s기준일 사이 : 재무기준일 %s ~ 평가기준일 %s — 출처 표지 %d · 근거 범위에 사이 정보 %d축 · 옛 경계 표지 거둠 %d · 근거 범위 되돌림 %d축 · 밴드 되돌림 %d"
              " — 쓴다(첫 예측 열 추정의 근거 · 실적 열이 아니다)"
              % (머리, 합.get("재무기준일"), 기준일, 뒤셈["사이수"], 뒤셈["축사이"], 뒤셈["거둠"], 뒤셈["축되돌림"], 뒤셈["밴드되돌림"]))
    if 첫셈["정정"] or 첫셈["축"]:
        print("%s첫 공표일   : 기준일 전 처음 발표된 항목 %d건의 기준일뒤 표지를 거뒀다 · 근거 범위 다시 잡을 축 %d(`근거범위_첫공표일`)"
              % (머리, 첫셈["정정"], 첫셈["축"]))
    if 첫셈["확인"]:
        print("%s첫 공표일   : 기준일 뒤 출처로 적힌 계획 · 발언 %d건 — 처음 발표가 기준일 전이면 항목에 `첫공표일` 을 적는다(정보): %s"
              % (머리, len(첫셈["확인"]), " · ".join(첫셈["확인"][:4])))
    if 공셈["빈"]:
        print("%s**경보 — 출처 항목 %d개 가운데 %d개에 공표일 · 기간 표지가 없습니다**(기준일 꼬리표가 가르지 못한다). 항목마다 `공표일`(YYYY-MM-DD)을 적는다: %s"
              % (머리, 공셈["출처항목"], 공셈["빈"], " · ".join(공셈["빈자리"][:5]) + (" …" if 공셈["빈"] > 5 else "")))
    for x in (합.get("근거범위_숫자화") or []):
        if x.get("못풂"):
            print("%s근거범위    : %s(%s) 끝을 숫자로 못 풀었다 — %s(그 끝은 비웠다 · 숫자로 다시 적는다)" % (머리, x["축"][:30], x["국면"], " · ".join(x["못풂"])))


def 병합(b1, b2, 기준일=None):
    """B1 을 바탕으로 B2 를 얹는다. 돌려주는 것은 (합본, 충돌, 보고).
    **b1 은 반드시 B1 원본이어야 한다** — 합본을 넣으면 합본이 스스로 쓴 칸이 충돌로 잡힌다(main 이 막는다).
    `기준일` — 회차 기준일(2026-10-25 FX-D ⓖ). 주면 합본 평가기준일을 그것으로 강제하고 B1 · B2 가 다르면 `평가기준일_갈림` 경보.
    두 국면의 글로 적힌 근거범위 끝은 합치기 전에 숫자로 푼다(ⓗ — B1 · B2 원본 파일은 그대로, 합본에만)."""
    합 = json.loads(json.dumps(b1))
    b2 = json.loads(json.dumps(b2 or {}))
    숫자화 = 근거범위숫자화(합, "B1") + 근거범위숫자화(b2, "B2")
    검출, 보고, 변경 = [], [], []

    def 칸비교(칸이름, 대상, a, b, 앞국면="B1"):
        """같은 대상의 칸마다 견준다 — 빈 칸은 채우고, 다르면 충돌(보강 칸은 보강으로 남긴다)."""
        찬, 났 = 0, 0
        for kk, vv in (b or {}).items():
            if kk in 비교제외 or _비었나(vv):
                continue
            if _비었나(a.get(kk)):
                a[kk] = vv
                찬 += 1
            elif kk in 보강칸 and _n(a.get(kk)) != _n(vv):
                a.setdefault("보강_B2", {})[kk] = vv
                if kk == "신뢰도":
                    변경.append({"칸": "%s.신뢰도" % 칸이름, "대상": 대상, "옛": a.get(kk), "새": vv,
                               "근거": _n((b or {}).get("신뢰도_까닭") or (b or {}).get("evidence"))[:160]})
            elif _n(a.get(kk)) != _n(vv):
                검출.append({"칸": "%s.%s" % (칸이름, kk), "대상": 대상,
                           "값들": [{"값": _n(a.get(kk))[:160], "출처": _출처(a), "국면": 앞국면},
                                  {"값": _n(vv)[:160], "출처": _출처(b), "국면": "B2"}]})
                났 += 1
        return 찬, 났

    for 키, v2 in (b2 or {}).items():
        if 키 in 따로:
            continue                                  # 아래에서 따로 다룬다
        v1 = 합.get(키)

        if isinstance(v2, list):
            벌 = list(v1) if isinstance(v1, list) else []
            있는, 국면표 = {}, {}
            # 축 후보는 **이름이 같으면 같은 축**이다(2026-10-24 W15 · 인텔 시범 — B2 가 같은 이름 축에 신뢰도 · 근거범위를 적었는데 출처가 달라
            # 새 줄로 덧붙어 축이 7 → 9, 같은 이름 두 줄이 됐다). 스킬 B2 절의 「보강으로 얹는다」 와 맞춘다. 다른 목록은 종전대로 이름 + 출처
            열쇠 = (lambda x: "축:" + _이름(x).strip().lower()) if 키 == "scenario_axes" else _키
            for x in 벌:
                있는.setdefault(열쇠(x), x)
                국면표.setdefault(열쇠(x), "B1")
            더함, 채움, 갈림 = 0, 0, 0
            for x in v2:
                k = 열쇠(x)
                if k in 있는 and isinstance(있는[k], dict) and isinstance(x, dict):
                    a, b = 칸비교(키, _대상말(x), 있는[k], x, 국면표.get(k, "B1"))
                    채움 += a
                    갈림 += b
                    continue
                if k in 있는:
                    if _n(있는[k]) != _n(x):
                        검출.append({"칸": 키, "대상": _대상말(x) if isinstance(x, dict) else _n(x)[:60],
                                   "값들": [{"값": _n(있는[k])[:160], "출처": "", "국면": 국면표.get(k, "B1")},
                                          {"값": _n(x)[:160], "출처": "", "국면": "B2"}]})
                        갈림 += 1
                    continue
                x = dict(x) if isinstance(x, dict) else x
                if isinstance(x, dict):
                    x.setdefault("_국면", "B2")
                벌.append(x)
                있는[k] = x
                국면표[k] = "B2"
                더함 += 1
            합[키] = 벌
            말 = []
            if 더함:
                말.append("+%d건" % 더함)
            if 채움:
                말.append("빈칸 %d개" % 채움)
            if 갈림:
                말.append("갈림 %d" % 갈림)
            if 말:
                보고.append("%s %s" % (키, " · ".join(말)))
            continue

        if isinstance(v2, dict) and isinstance(v1, dict):
            찬, 났 = 칸비교(키, 키, v1, v2)
            if 찬 or 났:
                보고.append("%s 빈칸 %d개%s" % (키, 찬, (" · 갈림 %d" % 났) if 났 else ""))
            continue

        if _비었나(v1) and not _비었나(v2):
            합[키] = v2
            보고.append("%s 채움(B1 비어 있었다)" % 키)
        elif not _비었나(v1) and not _비었나(v2) and _n(v1) != _n(v2):
            검출.append({"칸": 키, "대상": 키,
                       "값들": [{"값": _n(v1)[:160], "출처": "", "국면": "B1"},
                              {"값": _n(v2)[:160], "출처": "", "국면": "B2"}]})

    # ── 묶음 신뢰도 — B1 값은 두고 B2 의 등급을 보강으로 ──
    _a, _b = (b1 or {}).get("축_신뢰도"), (b2 or {}).get("축_신뢰도")
    if _b is not None:
        합["축_신뢰도_B2"] = _b
        if _n(_a) != _n(_b):
            변경.append({"칸": "축_신뢰도", "대상": "묶음", "옛": (_a or {}).get("등급") if isinstance(_a, dict) else _a,
                       "새": (_b or {}).get("등급") if isinstance(_b, dict) else _b,
                       "근거": _n((_b or {}).get("까닭") if isinstance(_b, dict) else "")[:160]})
    합["신뢰도_변경"] = 변경
    if 변경:
        보고.append("신뢰도 보강 %d곳(충돌 아님 — `신뢰도_변경`)" % len(변경))
    # 2026-10-24 W18 — B2 가 축의 신뢰도를 **올렸으면**(약 → 보통 · 강) 그 신뢰도와 그때 낸 근거 범위를 축 칸에 올린다(유니버스 조사 — 합본 축이 「약」 그대로라
    # 거친 바퀴가 B2 의 보강을 못 썼다). B1 값은 `신뢰도_B1` · `근거범위_B1` 에 둔다. 내린 보강은 올리지 않는다(규칙 ① — 사람이 본 값)
    올림 = 0
    for ax in 합.get("scenario_axes") or []:
        if not isinstance(ax, dict) or not isinstance(ax.get("보강_B2"), dict):
            continue
        보 = ax["보강_B2"]
        옛, 새 = 등급차례.get(_n(ax.get("신뢰도")).strip()), 등급차례.get(_n(보.get("신뢰도")).strip())
        if 옛 is None or 새 is None or 새 <= 옛:
            continue
        ax["신뢰도_B1"] = ax.get("신뢰도")
        ax["신뢰도"] = 보["신뢰도"]
        for k in ("신뢰도_까닭", "독립출처수"):
            if k in 보:
                ax[k + "_B1"] = ax.get(k)
                ax[k] = 보[k]
        if isinstance(보.get("근거범위"), dict):
            ax["근거범위_B1"] = ax.get("근거범위")
            ax["근거범위"] = 보["근거범위"]
        ax["보강_올림"] = "B2 신뢰도 %s → %s 를 축에 올림(B1 값은 `…_B1`)" % (ax["신뢰도_B1"], ax["신뢰도"])
        올림 += 1
    if 올림:
        보고.append("B2 가 신뢰도를 올린 축 %d개를 축 칸에 올림(`보강_올림`)" % 올림)
    기준일맞춤(합, b1, b2, 기준일, 보고)
    합["근거범위_숫자화"] = 숫자화
    if 숫자화:
        보고.append("글로 적힌 근거범위 끝 %d축을 숫자로 풀었다(`근거범위_숫자화` · 원문은 범위 사전의 `원문`)%s"
                  % (len(숫자화), (" · 못 푼 끝 %d" % sum(len(x["못풂"]) for x in 숫자화)) if any(x["못풂"] for x in 숫자화) else ""))

    # ── 충돌 — 스크립트 검출 + 두 국면이 스스로 적은 것, 한 형식·중복 제거 ──
    충돌, 충셈 = 충돌모으기([("B1 기록", (b1 or {}).get("충돌")),
                          ("B2 기록", (b2 or {}).get("충돌")),
                          ("스트림병합", 검출)])
    합["충돌"] = 충돌
    합["충돌_셈"] = 충셈

    합["coverage_B1"] = (b1 or {}).get("coverage")
    합["coverage_B2"] = (b2 or {}).get("coverage")
    if (b2 or {}).get("예산실측") is not None:
        합["예산실측_B2"] = b2.get("예산실측")
    if (b2 or {}).get("조사일") and (b2 or {}).get("조사일") != (b1 or {}).get("조사일"):
        합["조사일_B2"] = b2.get("조사일")
    cov2 = (b2 or {}).get("coverage")
    cov2 = cov2 if isinstance(cov2, dict) else {}
    체크 = cov2.get("체크포인트") or cov2.get("체크포인트_도달") or (b2 or {}).get("체크포인트")
    합["국면"] = {"B1": (b1 or {}).get("status"), "B2": (b2 or {}).get("status"), "체크포인트": 체크}

    # ── 심화_큐 — B2 가 심화 파일에 적은 처리 기록으로 센다 ──
    큐 = (b1 or {}).get("심화_큐") or []
    기록들 = (b2 or {}).get("심화_큐_처리") or (b2 or {}).get("처리된_큐") or []
    대응, 셈, 남음, 짝없음 = 큐대응(큐, 기록들)
    합["심화_큐"] = 큐
    합["심화_큐_처리"] = 기록들
    합["심화_큐_대응"] = 대응
    합["심화_큐_셈"] = 셈
    합["심화_큐_남음"] = 남음
    if 짝없음:
        합["심화_큐_처리_짝없음"] = 짝없음
    합["_병합"] = {"도구": "스크립트/스트림병합.py", "B1원본": 보존이름,
                 "규약": "재실행은 B1 원본에서 다시 합친다 — 이 파일 위에 B2 를 또 얹지 않는다"}
    return 합, 충돌, 보고


밴드별칭 = {"lsd": "low-single", "msd": "mid-single", "hsd": "high-single", "ldd": "low-teens", "mdd": "mid-teens",
         "hdd": "high-teens", "lowsingledigit": "low-single", "midsingledigit": "mid-single", "highsingledigit": "high-single"}
_내림말 = ("감소", "하락", "축소", "역성장", "decline", "decrease", "down", "lower", "drop")


def 밴드범위(표현들, 사전=None):
    """회사 · 애널리스트가 밴드로만 준 변동률(`근거범위_밴드` — 「+MSD」 · 「HSD 하락」 · 「소폭 증가」 · 「10% 중반」)을 밴드사전(키트 정본 ·
    `표현실현.밴드`)으로 숫자 범위로 잇는다(2026-10-24 W15 · 삼성전기 시범 — 밴드뿐이라 근거범위가 비어 병합이 경보만 냈다).
    → ({"최저", "최고", "단위", "출처", "딱지"}, 못 옮긴 표현[]) · 하나도 못 옮기면 (None, 못 옮긴 표현[]). 방향은 표현의 부호 · 낱말이 정한다(없으면 오름)."""
    import re as _re
    try:
        import 표현실현 as _P                               # noqa: PLC0415
        사전 = 사전 or _P.사전읽기()
    except Exception:                                       # noqa: BLE001
        return None, list(표현들 or [])
    값, 못 = [], []
    for e in ([표현들] if isinstance(표현들, str) else (표현들 or [])):
        s = ("%s" % e).strip()
        if not s:
            continue
        원 = s
        # 2026-10-24 W16 — 괄호 꼬리(「low-10% (2Q26 실적)」)를 떼고 견준다 · 숫자로 적힌 밴드(「+2~3%」 · 「N% 감소」 · 「10~15%」)는 사전 없이 숫자로 ·
        # 「풀가동」 은 가동률 상한 신호라 변동률로 옮기지 않는다 · 전월 대비(MoM)는 분기 축과 단위가 달라 옮기지 않는다(유니버스 조사 물결 실측)
        s = _re.sub(r"[\(（][^)）]*[\)）]", " ", s).strip()
        if _re.search(r"풀\s*가동|full\s*(utili[sz]ation|capacity)", s, _re.I):
            못.append("%s — 가동률 상한 신호(변동률 아님 · 가동률 축에서만)" % 원)
            continue
        if _re.search(r"\bmom\b|전월\s*대비|month[- ]over[- ]month", s, _re.I):
            못.append("%s — 전월 대비(분기 축과 단위가 다르다)" % 원)
            continue
        내림 = s.startswith(("-", "−", "–")) or any(w in s.lower() for w in _내림말)
        수 = _re.search(r"([+\-−–]?\d+(?:\.\d+)?)\s*%?\s*(?:~|〜|to|–|—)\s*([+\-−–]?\d+(?:\.\d+)?)\s*%", s) or             _re.search(r"(?<![\w.])([+\-−–]?\d+(?:\.\d+)?)\s*%(?!\s*(?:p|포인트))", s)
        if 수 and not _re.search(r"(?i)(low|mid|high)[- ]?(single|teens|\d)", s):
            def _f(x):
                return float(x.replace("−", "-").replace("–", "-"))
            a1 = _f(수.group(1))
            a2 = _f(수.group(2)) if 수.lastindex and 수.lastindex >= 2 else a1
            lo, hi = sorted((abs(a1), abs(a2)))
            음 = 내림 or a1 < 0
            값.append(((-hi if 음 else lo) / 100.0, (-lo if 음 else hi) / 100.0, 원))
            continue
        핵 = _re.sub(r"^[+\-−–]\s*", "", s)
        for w in _내림말 + ("증가", "상승", "확대", "성장", "increase", "growth", "up", "higher", "growth", "yoy", "qoq", "전년 대비", "전분기 대비"):
            핵 = 핵.replace(w, " ").replace(w.capitalize(), " ")
        핵 = 핵.strip()
        핵 = 밴드별칭.get(_re.sub(r"[^a-z]", "", 핵.lower()), 핵)
        b = _P.밴드(핵, 사전)
        if not (isinstance(b, tuple) and all(isinstance(x, (int, float)) and x != float("inf") for x in b)):
            못.append(원)
            continue
        lo, hi = (-b[1], -b[0]) if 내림 else (b[0], b[1])
        값.append((lo / 100.0, hi / 100.0, 원))
    if not 값:
        return None, 못
    return ({"최저": min(x[0] for x in 값), "최고": max(x[1] for x in 값), "단위": "전기 대비 변동률(비율)",
             "출처": "밴드사전 — " + " · ".join(x[2] for x in 값), "딱지": "[밴드 변환]"}, 못)


def 밴드잇기(j):
    """`scenario_axes[]` 가운데 근거범위가 비었고 `근거범위_밴드` 가 있는 축에 밴드사전 범위를 채운다 → [(축 이름, 범위 또는 None, 못 옮긴 표현)]."""
    낸 = []
    for ax in ((j or {}).get("scenario_axes") or []):
        if not isinstance(ax, dict) or not ax.get("근거범위_밴드"):
            continue
        r = ax.get("근거범위")
        if isinstance(r, dict) and isinstance(r.get("최저"), (int, float)) and isinstance(r.get("최고"), (int, float)):
            continue
        범, 못 = 밴드범위(ax.get("근거범위_밴드"))
        if 범:
            ax["근거범위"] = 범
        낸.append((ax.get("name") or ax.get("이름") or "(이름 없음)", 범, 못))
    return 낸


def 근거범위빈축(j):
    """S9R2(재리뷰 S9R1-N1 ③) — 축 후보(`scenario_axes[]`) 가운데 `근거범위`(관측 최저 · 최고)가 없는 축 이름. B2 가 채운 보강(`보강_B2.근거범위`)이
    있으면 찬 것으로 본다. 거친 바퀴는 근거 범위가 없는 축을 순위에 넣지 못하고(범위 없음 — 참고) 범위를 묻는 문항으로만 올린다 — 그래서 병합에서 경보한다."""
    낸 = []
    for ax in ((j or {}).get("scenario_axes") or []):
        if not isinstance(ax, dict):
            continue
        범 = ax.get("근거범위")
        보 = (ax.get("보강_B2") or {}).get("근거범위") if isinstance(ax.get("보강_B2"), dict) else None
        찬 = lambda r: isinstance(r, dict) and isinstance(r.get("최저"), (int, float)) and isinstance(r.get("최고"), (int, float))  # noqa: E731
        # 2026-10-24 W17 — 한쪽 끝만 관측된 축(AMD 조사 — 「최저: null · 최고」)은 「범위 없음」 이 아니라 「반쪽 범위」 —
        # 빈 축으로 세지 않고 `근거범위_반쪽` 칸을 단다. 거친 바퀴는 아직 두 끝이 다 있어야 범위로 쓴다(반쪽은 일률 폭) — 그래서 경보는 따로 낸다
        반 = lambda r: isinstance(r, dict) and (isinstance(r.get("최저"), (int, float)) != isinstance(r.get("최고"), (int, float)))  # noqa: E731
        if 찬(범) or 찬(보):
            continue
        if 반(범) or 반(보):
            ax["근거범위_반쪽"] = "최저" if isinstance((범 if 반(범) else 보).get("최저"), (int, float)) else "최고"
            continue
        낸.append("%s" % (ax.get("name") or ax.get("이름") or "(이름 없음)"))
    return 낸


def _빈축경보(j, 머리="  "):
    빈모두 = 근거범위빈축(j)
    축수 = len([x for x in ((j or {}).get("scenario_axes") or []) if isinstance(x, dict)])
    # 2026-10-24 W18 — `근거범위_까닭` 을 적은 축은 「못 채운 까닭이 있다」 — 경보가 아니라 정보 줄(유니버스 조사 실측). 기준일 뒤 출처라 옮긴 축은
    # 기준일 안 출처로 다시 잡아야 하니 경보에 남긴다
    까닭축 = {"%s" % (x.get("name") or x.get("이름") or "(이름 없음)") for x in ((j or {}).get("scenario_axes") or [])
            if isinstance(x, dict) and x.get("근거범위_까닭") and not x.get("근거범위_기준일뒤")}
    빈 = [x for x in 빈모두 if x not in 까닭축]
    까닭있음 = [x for x in 빈모두 if x in 까닭축]
    if 까닭있음:
        print("%s근거범위 없이 까닭을 적은 축 %d개(정보 — 경보 아님): %s" % (머리, len(까닭있음), " · ".join(x[:24] for x in 까닭있음[:8])))
    if 빈:
        print("%s**경보 — 축 후보 %d개 가운데 %d개에 근거범위(관측 최저 · 최고)가 없습니다.** 거친 바퀴는 이 축을 순위에 넣지 못하고"
              % (머리, 축수, len(빈)))
        print("%s  범위를 묻는 문항으로만 올립니다(근거 범위 없음). B1 · B2 가 관측(과거 실적 범위 · 리포트의 과거 칸)으로 채우거나, 못 채우면"
              % 머리)
        print("%s  `근거범위_까닭` 에 왜 못 채웠는지 적습니다: %s" % (머리, " · ".join(x[:24] for x in 빈[:8]) + (" …" if len(빈) > 8 else "")))
    반 = ["%s(%s만)" % (x.get("name") or x.get("이름") or "?", x["근거범위_반쪽"])
         for x in ((j or {}).get("scenario_axes") or []) if isinstance(x, dict) and x.get("근거범위_반쪽")]
    if 반:
        print("%s반쪽 범위 %d축 — 한 끝만 관측됐습니다. 거친 바퀴는 두 끝이 다 있어야 범위로 쓰므로(반쪽은 일률 폭) 다른 끝을 관측으로 채우거나 "
              "`근거범위_까닭` 에 적습니다: %s" % (머리, len(반), " · ".join(반[:8])))
    return 빈


def _합본인가(j):
    return isinstance(j, dict) and (isinstance(j.get("_병합"), dict) or "coverage_B1" in j
                                    or "심화_큐_남음" in j)


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("b1", nargs="?", default=os.path.join("_raw", "매출스트림_웹조사.json"))
    ap.add_argument("b2", nargs="?", default=os.path.join("_raw", "매출스트림_심화.json"))
    ap.add_argument("--기준일", help="회차 평가기준일(YYYY-MM-DD) — 없으면 곁의 진행판(_회차실행/진행판.json) · 가정 파일의 평가기준일, "
                                    "그것도 없으면 같은 _raw/ 의 동인원천 · 투자능력 · 외부제약이 적은 평가기준일")
    ap.add_argument("--결산월", type=int, default=None, help="결산월 1~12 — 회계 분기 표지(「회계 2026 4분기」)를 푼다. 없으면 진행판 · 가정의 결산월")
    ap.add_argument("--재무기준일", help="회차 재무기준일 F(YYYY-MM-DD · 2026-10-25 날짜 둘) — 없으면 같은 _raw/ 의 세 산출이 적은 재무기준일 · "
                                      "그것도 없으면 F = 평가기준일(「사이」 표지 없음 — 지금과 같다)")
    a = ap.parse_args()
    회차, 회차근거 = (_일(a.기준일), [("--기준일", _일(a.기준일))]) if a.기준일 else 회차기준일(os.path.dirname(os.path.abspath(a.b1)))
    if a.기준일 and not 회차:
        sys.exit("--기준일 꼴이 틀렸습니다(%s) — YYYY-MM-DD" % a.기준일)
    재무 = _일(a.재무기준일) if a.재무기준일 else 회차기준일(os.path.dirname(os.path.abspath(a.b1)), "재무기준일")[0]
    if a.재무기준일 and not 재무:
        sys.exit("--재무기준일 꼴이 틀렸습니다(%s) — YYYY-MM-DD" % a.재무기준일)
    결산 = a.결산월 or 정본결산월(os.path.dirname(os.path.abspath(a.b1)))

    if not os.path.exists(a.b1):
        sys.exit("B1 산출물이 없습니다: %s" % a.b1)
    # 2026-10-24 W17 — 인자 순서를 잘못 주어 보존 원본(_B1.json)을 첫 인자로 주면 합본으로 보존 원본을 덮었다(LIG디펜스 조사) — 덮기 전에 멈춘다
    if os.path.basename(a.b1) in (보존이름, "매출스트림_웹조사_B1.이전.json") or os.path.basename(a.b1).endswith("_B1.json"):
        sys.exit("첫 인자가 보존 원본(%s)입니다 — 합본 자리(매출스트림_웹조사.json)를 주십시오. 보존 원본을 덮지 않으려고 멈춥니다" % os.path.basename(a.b1))
    if os.path.abspath(a.b1) == os.path.abspath(a.b2):
        sys.exit("B1 과 B2 가 같은 파일입니다(%s) — 인자를 확인하십시오" % a.b1)
    if not os.path.exists(a.b2):
        print("심화 산출물이 없습니다: %s" % a.b2)
        print("→ B2 가 아직 안 돌았거나 SLA 를 넘겨 열화 경로로 갔습니다. **병합할 것이 없으므로 그대로 둡니다.**")
        print("  판매량을 생산능력으로 세웠거나(매출구분[].판매량산정 = 능력) 시장점유율 대조를 세웠다면(점유율대조 = 예)")
        print("  그 줄의 근거 칸에 「심화 없이 세움」이 적혀 있어야 합니다(자체검사 ⑰ — 조사 배선).")
        try:
            j = json.load(io.open(a.b1, encoding="utf-8"))
        except (OSError, ValueError):
            return
        if not isinstance(j, dict):
            return
        # 2026-10-25 FX-D — B2 가 없어도 회차 기준일 강제(ⓖ) · 근거범위 숫자(ⓗ) · 기준일 꼬리표 · 첫 공표일(ⓙ) · 공표일 검사(ⓘ)는 같게 한다.
        # 합본이 아니므로 B1 자리에 그대로 쓰고(바뀐 것이 있을 때만) 원문은 범위 사전의 `원문` 에 남는다
        전 = json.dumps(j, ensure_ascii=False, sort_keys=True)
        보고 = []
        숫자화 = 근거범위숫자화(j, "B1")
        if 숫자화 or j.get("근거범위_숫자화"):
            j["근거범위_숫자화"] = (j.get("근거범위_숫자화") or []) + 숫자화
        기준일 = 기준일맞춤(j, j, None, 회차, 보고)
        뒤셈, 첫셈, _, 공셈 = 마무리(j, 기준일, _조사상한(j), 재무 or _일(j.get("재무기준일")) or None, 결산)
        for x in 보고:
            print("  %s" % x)
        _마무리말(j, 뒤셈, 첫셈, 공셈, 기준일)
        _빈축경보(j)
        if json.dumps(j, ensure_ascii=False, sort_keys=True) != 전:
            io.open(a.b1, "w", encoding="utf-8").write(json.dumps(j, ensure_ascii=False, indent=1))
            print("  B1 자리에 고친 것을 썼다(근거범위 숫자 · 평가기준일 · 표지 — 원문은 범위 사전의 `원문`)")
        return

    현재 = json.load(io.open(a.b1, encoding="utf-8"))
    b2 = json.load(io.open(a.b2, encoding="utf-8"))
    보존 = os.path.join(os.path.dirname(a.b1), 보존이름)
    알림 = ""

    if _합본인가(현재):
        if not os.path.exists(보존):
            print("**%s 는 이미 합본인데 B1 원본(%s)이 없습니다.**" % (a.b1, 보존))
            print("  합본 위에 B2 를 다시 얹으면 합본이 스스로 쓴 칸이 충돌로 잡히고 충돌 수가 흔들립니다")
            print("  (실측 2026-09-13: 펄어비스 7→1건, 세일즈포스 3→4건). B1 원본을 되살린 뒤 다시 돌리십시오.")
            sys.exit(2)
        b1 = json.load(io.open(보존, encoding="utf-8"))
        알림 = "재실행 — 합본 위가 아니라 보존된 B1 원본에서 다시 합쳤습니다"
    else:
        b1 = 현재
        if os.path.exists(보존):
            옛 = json.load(io.open(보존, encoding="utf-8"))
            if 옛 != 현재:
                이전 = os.path.join(os.path.dirname(a.b1), "매출스트림_웹조사_B1.이전.json")
                io.open(이전, "w", encoding="utf-8").write(json.dumps(옛, ensure_ascii=False, indent=1))
                io.open(보존, "w", encoding="utf-8").write(json.dumps(현재, ensure_ascii=False, indent=1))
                알림 = "B1 이 다시 돌았습니다 — 옛 보존본은 %s 로 옮기고 새 B1 을 보존했습니다" % 이전
        else:
            io.open(보존, "w", encoding="utf-8").write(json.dumps(b1, ensure_ascii=False, indent=1))

    합, 충돌, 보고 = 병합(b1, b2, 회차)
    # 2026-10-24 W18 — 평가기준일 뒤 정보는 축 근거 범위에 섞지 않는다(조사 지시 「평가기준일을 지킨다」). 출처 항목에 `기준일뒤` 표지를 달고,
    # 출처가 기준일 뒤뿐인 근거 범위 · 밴드 표현은 `…_기준일뒤` 로 옮긴다(밴드 변환보다 먼저 — 기준일 뒤 밴드가 범위로 되살아나지 않게).
    # 2026-10-25 FX-D — 기준일은 회차 기준일(병합이 합본에 강제 — ⓖ) · 첫 공표일(ⓙ) · 공표일 검사(ⓘ)를 같은 차례에(`마무리`)
    기준일 = _일(합.get("평가기준일") or b1.get("평가기준일") or b2.get("평가기준일")) or None
    뒤셈, 첫셈, 잇기, 공셈 = 마무리(합, 기준일, _조사상한(합, b1, b2),
                              재무 or _일(b1.get("재무기준일") or b2.get("재무기준일")) or None, 결산)
    if 회차근거 and len({v for _, v in 회차근거}) > 1:
        합["회차기준일_근거"] = [{"파일": f, "평가기준일": v} for f, v in 회차근거]
    io.open(a.b1, "w", encoding="utf-8").write(json.dumps(합, ensure_ascii=False, indent=1))

    셈 = 합["심화_큐_셈"]
    충셈 = 합["충돌_셈"]
    print("── 스트림 병합 ──")
    if 알림:
        print("  %s" % 알림)
    print("  B1 원본 보존 → %s" % 보존)
    print("  합본        → %s" % a.b1)
    print("  더한 것     : %s" % (" · ".join(보고) if 보고 else "없음"))
    print("  심화_큐     : %d줄 — 처리 %d · 부분 %d · 미처리 %d · 기록없음 %d%s → 남음 %d줄"
          % (셈["전체"], 셈["처리"], 셈["부분"], 셈["미처리"], 셈["기록없음"],
             (" · 구분불명 %d" % 셈["불명"]) if 셈["불명"] else "", 합["심화_큐_남음"]))
    if 합.get("심화_큐_처리_짝없음"):
        print("               B2 처리 기록 %d줄은 B1 큐의 어느 줄인지 못 찾았습니다(심화_큐_처리_짝없음)"
              % len(합["심화_큐_처리_짝없음"]))
    if 셈["전체"] and not 합["심화_큐_처리"]:
        print("               B2 가 `심화_큐_처리[]` 를 안 적었습니다 — 셈이 전부 「기록없음」입니다")
    if 충돌:
        print("\n  **충돌 %d건 — 고르지 않았습니다. 모순 장부에 올리십시오.**" % len(충돌))
        print("    (스크립트 검출 %d · B1 기록 %d · B2 기록 %d · 중복 제거 %d)"
              % (충셈.get("스트림병합", 0), 충셈.get("B1 기록", 0), 충셈.get("B2 기록", 0), 충셈.get("중복제거", 0)))
        for c in 충돌[:10]:
            print("    · [%s] %s" % (c["칸"] or c["기록"], c["대상"]))
            for v in c["값들"][:3]:
                print("        %s %s%s" % (v["국면"] or "-", v["값"][:70], (" (%s)" % v["출처"][:40]) if v["출처"] else ""))
        print("    `python 스크립트/모순장부.py 가정_회사.json` 이 이 칸을 M-09 로 읽습니다")
    else:
        print("  충돌        : 없음 (합본 전체 기준)")
    for n, r, m in 잇기:
        print("  밴드 변환   : %s → %s%s" % (n[:30], ("%.1f%% ~ %.1f%%" % (r["최저"] * 100, r["최고"] * 100)) if r else "못 옮김",
                                          (" · 사전에 없는 표현 %s — 밴드사전에 칸을 더하거나 숫자 범위로 적는다" % " · ".join(m)) if m else ""))
    _마무리말(합, 뒤셈, 첫셈, 공셈, 기준일)
    _빈축경보(합)
    # 조사의 두 칸이 닿는 4번 줄 — 판매량 산정(능력 × 가동률 × 수율)과 시장점유율 대조(시장 규모 × 점유율). 설계서 6-2:
    # 전개 함수가 공급 ÷ 수요를 셈하던 길은 걷었고 줄은 남았다 — 값은 사람이 근거와 함께 가정에 적는다
    for 칸, 뜻 in (("능력", "4번 판매량 산정(생산능력 × 가동률 × 수율 — 매출구분[].판매량산정 = 능력)"),
                  ("market_size", "4번 시장점유율 대조(시장 규모 × 점유율 — 매출구분[].점유율대조 = 예)")):
        print("  %-12s %d건 — %s 의 근거 재료입니다" % (칸, len(합.get(칸) or []), 뜻))


if __name__ == "__main__":
    main()

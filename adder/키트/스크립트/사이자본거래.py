# -*- coding: utf-8 -*-
"""사이자본거래 — 재무기준일 F 와 평가기준일 T 사이((F, T])의 자본거래를 공시에서 모아 `_raw/사이자본거래.json`(「사이자본거래/1」)으로 낸다
(2026-10-25 날짜 둘 · K2 · 계약 `연구/평가기준일_날짜둘_20261025/01_계약.md` 0-4).

왜 — 평가기준일이 분석일(T)이고 재무는 최근 공시 분기말(F)이면 주주가치를 F 에서 셈해 T 로 이월한다(엔진 · K1). 그 다리의 둘째 항이
  Σ(F, T] 자본거래 현금(증자 유입 + · 자기주식 취득 − · 배당 지급 − · 전환 · 행사 유입 +)과 주식수 변동이다. F 의 재무상태표에는 그 사이의
  증자 · 자기주식 · 배당이 없다 — 공시를 읽어야 한다. 값은 원문 표에서만 받는다(눈으로 옮기지 않는다 — 키트 `공시표.py` 격자).

국내(OpenDART) — `list.json`(기업 고유번호 · F − 120일 ~ T, 모든 공시 종류)을 한 번 받고(쪽마다 100건), 제목으로 종류를 가른다.
  F 다음 날 ~ T 에 제출된 것   증권발행실적보고서 · 유상증자(주식관련사채) 발행결과 · 자기주식 취득 · 처분 결과보고서 · 신탁계약 해지결과 ·
                               현금 · 현물배당결정 · 전환 · 교환청구권 행사 · 신주인수권 · 주식매수선택권 행사 — 실행이고 값을 읽는다.
                               유상증자 · 자기주식 취득 · 처분 결정 · 주식소각결정 · 무상증자 · 주식분할 · 감자 결정 — 기록(결정은 실행이 아니다)
  F 앞 120일에 제출된 배당결정  결정일 ≤ F 인데 지급이 F 뒤(또는 지급일 미기재)면 **F 재무상태표의 미지급배당금**이다 — 이월 다리에서 빼지 않는다고 표지한다
  원문 — `document.xml`(ZIP) → `_raw/사이자본거래원문/<접수번호>/` · 목록 → `_raw/사이자본거래원문/목록_<고유번호>_<시작>_<끝>.json`. 있으면 다시 받지 않는다
  (두 번째 돌기는 OpenDART 0 콜 · 같은 산출). 일일 한도(status 020)면 그 자리에서 멈추고 `남은받기` 에 적는다(종료 1).
미국(SEC) — 10-Q · 10-K 는 T 뒤에 나오는 일이 많아 8-K(배당 선언 · Item 3.02 미등록 지분 매각)에서 되는 만큼 읽고, 자기주식 매입(10-Q Part II
  Item 2 월별 표) · 주식 보상 행사 · 전환은 「사람이 적는다」 줄로 남긴다. 배당 총액은 8-K 에 없어 주당 × 표지 주식수(참고)다.

판정 규칙(회사 · 업종 이름 없음)
  ① 결과(실행)만 다리에 든다 — 결정은 `반영: false`(참고). 결과가 없는데 결정 기간이 (F, T] 를 걸치면 **확인 불가**(실행분 미공시)로 이름을 남긴다
  ② 자기주식 결과보고서는 일자별 줄을 (F, T] 로 가른다 — F 이하 줄은 F 재무상태표 · T 뒤 줄은 평가기준일 후 사건
  ③ 처분 목적 · 상대방이 보수 · 보상 · 임직원(주식 보상)이면 현금 유입 0(처분가액은 보상 평가액) — 주식수만 늘린다(사람 확인 표지)
  ④ 배당 — 결정일 ≤ F 면 반영 안 함(F 미지급배당금 또는 F 전 지급). F < 결정일 ≤ T 면 지급일이 T 이하(또는 지급일 미기재 · 배당기준일 T 이하 —
     T 주가는 배당락 뒤이고 T 에 미지급배당금이 부채로 선다)면 반영 · 배당기준일이 T 뒤면 반영 안 함(T 주가가 배당 권리를 품는다). 현물배당은 확인 필요
  ⑤ 소각 — 이미 자기주식인 주식(또는 취득 예정 자기주식)의 소각은 유통주식수를 바꾸지 않는다(기록만 · 13번 135 에 넣지 않는다)
  ⑥ 전환 · 교환 — 현금이 아니라 사채가 주식으로 바뀐다. 주식수는 134 로 · 청구금액은 `부채감소` 로 두고 재무기준일 이자부부채에 그 사채가 들었는지
     사람이 보고 131 에 더한다(도구가 더하지 않는다)
  ⑦ 못 읽은 사건은 **0 으로 메우지 않는다** — `확인상태: 확인 불가 — 까닭` · `반영: null` · `확인불가[]` 에 이름
  ⑧ 같은 사건의 정정 · 자율공시 대조는 하나로 — 늦은 정정을 쓰고, 증권발행실적보고서와 발행결과(자율공시)는 수량 · 날짜가 맞으면 「대조 일치」

13번(02_줄번호 3절) — 131 유입 현금(증자 · 행사 · 자기주식 처분) · 132 자기주식 취득 현금 · 133 배당 지급 현금(양수) · 134 주식수 증가 · 135 주식수 감소.
`줄합계(산출)` 가 그 다섯 칸과 사건 목록(`관측.사이자본거래[]` 꼴)을 낸다 — `공시채움.py` ⑦ 이 가정에 옮긴다.

    python 스크립트/사이자본거래.py --회사 00164779 --재무기준일 2026-06-30 --평가기준일 2026-10-23 [--raw _raw]
    python 스크립트/사이자본거래.py --가정 가정.json --회사 00164779                # 날짜는 기준일.py 로(F 가 없으면 F = T — 사건 0)
    python 스크립트/사이자본거래.py --국가 US --ticker NVDA --재무기준일 … --평가기준일 …   # 8-K 에서 되는 만큼 + 사람이 적는다
    python 스크립트/사이자본거래.py … --오프라인                                     # 받아 둔 목록 · 원문만(네트워크 0)

인증키(OPENDART_API_KEY) · 연락처(SEC_CONTACT_EMAIL)는 환경변수에서만 읽고 찍지 않는다. 종료 코드 — 0 통과 · 1 발견(확인 불가 사건 · 한도 초과) · 2 입력오류.
"""
from __future__ import annotations

import argparse
import datetime
import glob
import html as _html
import io
import json
import os
import re
import sys
import time
import zipfile

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:                                                # noqa: BLE001
    pass
여기 = os.path.dirname(os.path.abspath(__file__))
if 여기 not in sys.path:
    sys.path.insert(0, 여기)
from 종료코드 import 통과, 발견, 입력오류                            # noqa: E402
import 공시표                                                    # noqa: E402
import 기준일 as _기                                              # noqa: E402
import 기준일인자 as _기인                                         # noqa: E402

형식 = "사이자본거래/1"
출력파일 = "사이자본거래.json"
원문폴더 = "사이자본거래원문"
앞창일 = 120               # F 앞 배당결정을 훑는 창 — 결정일 ≤ F · 지급 > F(미지급배당금) 판정
쪽상한 = 20                # list.json 쪽(100건) 상한
도구표지 = "사이자본거래.py"

# 13번 칸(02_줄번호 3절) — 종류 → (현금 칸, 주식수 칸)
유입종류 = ("증자", "행사", "자기주식처분")          # 131 · 134
주식만종류 = ("전환", "교환")                       # 134 만(현금 0 — 부채감소는 사람이 131 에)
칸 = {"유입현금": "131", "취득현금": "132", "배당현금": "133", "주식증가": "134", "주식감소": "135"}

# ── 제목 → (종류, 역할). 차례가 중요하다(위가 먼저). None 종류 = 다리 밖(기록도 안 한다)
제목규칙 = [
    (r"종속회사의주요경영사항|\(종속회사", None, None),
    (r"주주명부폐쇄", None, None),
    (r"증권발행실적보고서", "증자", "결과"),
    (r"(유상증자|주식관련사채).*발행결과", "증자", "결과대조"),
    (r"무상증자결정", "무상증자", "결정"),
    (r"유상증자결정", "증자", "결정"),
    (r"자기주식취득신탁계약.*해지결과|신탁계약해지결과보고서", "자기주식취득", "신탁결과"),
    (r"자기주식취득신탁계약.*체결|신탁계약체결결정", "자기주식취득", "신탁결정"),
    (r"자기주식취득결과보고서", "자기주식취득", "결과"),
    (r"자기주식처분결과보고서", "자기주식처분", "결과"),
    (r"자기주식취득결정", "자기주식취득", "결정"),
    (r"자기주식처분결정", "자기주식처분", "결정"),
    (r"현금ㆍ?현물배당결정|현금ㆍ?현물배당결정|현금배당결정|현물배당결정|^배당결정|분기배당결정|중간배당결정", "배당", "결정"),
    (r"전환청구권행사", "전환", "결과"),
    (r"교환청구권행사", "교환", "결과"),
    (r"신주인수권행사", "행사", "결과"),
    (r"주식매수선택권행사", "행사", "결과"),
    (r"주식소각결정", "소각", "결정"),
    (r"(주식분할|주식병합)결정", "주식분할", "결정"),
    (r"감자결정", "감자", "결정"),
]
보상꼴 = re.compile(r"보수|보상|상여|성과|임직원|직원|이사|우리사주|ESOP|주식매수선택권|스톡옵션|양도제한|RSU|PSU|복지")
매도꼴 = re.compile(r"시간외|장내|장외|블록|대량매매|매도|교환사채|해외|예탁")


class 한도초과(Exception):
    """OpenDART 일일 한도(status 020)."""


# ════════════════════════════════════════ 작은 도구
def _표준(s):
    return re.sub(r"[\s 　]+", "", "%s" % (s or ""))


def 제목정리(제목):
    """「[기재정정]주요사항보고서(자기주식 취득 결정)」 → 「주요사항보고서(자기주식취득결정)」(대괄호 머리 · 빈칸 뗌)."""
    return _표준(re.sub(r"\[[^\]]*\]", "", "%s" % (제목 or "")))


def 정정인가(제목):
    return bool(re.search(r"\[(기재정정|첨부정정|첨부추가|발행조건확정|정정)\]", "%s" % (제목 or "")))


def 종류가르기(제목):
    """공시 제목 → (종류, 역할) | (None, None). 규칙표(`제목규칙`) 차례로."""
    t = 제목정리(제목)
    for 꼴, 종, 역 in 제목규칙:
        if re.search(꼴, t):
            return 종, 역
    return None, None


def 날짜(s):
    """「2026-08-31」 · 「2026.08.08」 · 「2026년 08월 20일」 · 「20260831」 → ISO | None."""
    s = "%s" % (s or "")
    m = re.search(r"((?:19|20)\d\d)\s*[.\-/년]\s*(\d{1,2})\s*[.\-/월]\s*(\d{1,2})", s) or re.fullmatch(r"\s*((?:19|20)\d\d)(\d\d)(\d\d)\s*", s)
    if not m:
        return None
    try:
        return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3))).isoformat()
    except ValueError:
        return None


def 수(s):
    """칸 글 → 수(공시표.수 — 쉼표 · 괄호 음수 · 「-」 = 0). 「-」 한 글자는 0 이 아니라 None 으로 읽는다(값 없음 — 0 으로 메우지 않는다)."""
    c = ("%s" % (s or "")).strip()
    if c in ("", "-", "－", "—", "–"):
        return None
    c = re.sub(r"[원주株$₩]|\s", "", c)
    return 공시표.수(c)


def _값꼴(c):
    c = (c or "").strip()
    return c in ("-", "－", "—") or 수(c) is not None or 날짜(c) is not None


def 칸들(문):
    """공시 문서의 표 → 칸 목록 [{"라벨": [...], "라벨글": 붙인 글, "값": [...], "표": 번호, "줄": 줄}] — 「1. 배당구분 | 분기배당」 꼴(열 병합 복사는 한 번).
    값 꼴(수 · 날짜 · 「-」)이 처음 나오는 칸부터가 값, 그 앞이 라벨이다. 값 꼴이 없으면 첫 칸이 라벨 · 나머지가 값."""
    낸 = []
    for 표 in (문 or {}).get("표") or []:
        for i, 줄 in enumerate(표.get("격자") or []):
            d = []
            for c in 줄:
                c = (c or "").strip()
                if c and (not d or d[-1] != c):
                    d.append(c)
            if len(d) < 2:
                continue
            k = next((j for j, c in enumerate(d) if j > 0 and _값꼴(c)), None)
            라, 값 = (d[:1], d[1:]) if k is None else (d[:k], d[k:])
            낸.append({"라벨": 라, "라벨글": _표준(" ".join(라)), "값": 값, "표": 표.get("번호"), "줄": i})
    return 낸


def 값(kv, 라벨꼴, 차례=0, 제외=None):
    """칸 목록에서 라벨이 꼴에 맞는 첫 칸의 값(글) | None."""
    for x in kv:
        if re.search(라벨꼴, x["라벨글"]) and not (제외 and re.search(제외, x["라벨글"])):
            v = x["값"]
            return v[차례] if len(v) > 차례 else None
    return None


def 열(표, 꼴, 제외=None):
    for j, n in enumerate(표.get("열이름") or []):
        t = _표준(n)
        if re.search(꼴, t) and not (제외 and re.search(제외, t)):
            return j
    return None


def 날짜줄들(문, 수량꼴, 총액꼴=None, 단가꼴=None, 대상꼴=None, 일자꼴=r"^일자|일자$|^청구일|청구일자|행사일|처분일|취득일|교환일|^일자"):
    """일자 열이 있는 표의 줄 → [{"일자", "수량", "총액", "단가", "대상", "표", "줄"}] — 「계」 · 날짜가 아닌 줄은 뺀다."""
    낸 = []
    for 표 in (문 or {}).get("표") or []:
        j일 = 열(표, 일자꼴)
        if j일 is None:
            continue
        j수 = 열(표, 수량꼴)
        if j수 is None:
            continue
        j총 = 열(표, 총액꼴) if 총액꼴 else None
        j단 = 열(표, 단가꼴) if 단가꼴 else None
        j대 = 열(표, 대상꼴) if 대상꼴 else None
        for i, 줄 in enumerate((표.get("격자") or [])[표.get("머리줄수") or 0:]):
            d = 날짜(줄[j일] if j일 < len(줄) else "")
            if not d:
                continue
            g = lambda j: (줄[j] if j is not None and j < len(줄) else None)   # noqa: E731
            낸.append({"일자": d, "수량": 수(g(j수)), "총액": 수(g(j총)), "단가": 수(g(j단)), "대상": g(j대), "표": 표.get("번호"), "줄": i})
    return 낸


def 표열값(문, 표꼴, 열꼴, 줄꼴=None, 열제외=None):
    """앞글 · 제목 · 머리에 표꼴이 있는 표에서 열꼴 열의 값(줄꼴이 맞는 줄 · 없으면 머리 아래 첫 줄) → 글 | None."""
    for 표 in (문 or {}).get("표") or []:
        글 = _표준(" ".join(list(표.get("제목경로") or []) + list(표.get("앞글") or []) + list(표.get("열이름") or [])))
        if not re.search(표꼴, 글):
            continue
        j = 열(표, 열꼴, 열제외)
        if j is None:
            continue
        for 줄 in (표.get("격자") or [])[표.get("머리줄수") or 0:]:
            if 줄꼴 and not re.search(줄꼴, _표준(" ".join(줄))):
                continue
            if j < len(줄) and 줄[j].strip() not in ("", "-"):
                return 줄[j]
    return None


def _사이(d, F, T):
    """d ∈ (F, T] — 글 날짜 셋."""
    return bool(d and F < d <= T)


# ════════════════════════════════════════ 판정(순수 — 시험이 직접 부른다)
def 배당판정(결정일, 기준일, 지급일, F, T):
    """→ (반영 True/False/None, 판정 날짜, 표지 글). 모두 ISO 글 · 없으면 None. 규칙 ④."""
    if not 결정일:
        return None, 지급일 or 기준일, "확인 불가 — 이사회결의일(결정일)을 원문에서 못 읽었다"
    if 결정일 <= F:
        if 지급일 and 지급일 <= F:
            return False, 지급일, "재무기준일 전에 지급 — F 현금에 이미 빠져 있다"
        if 지급일:
            return False, 지급일, "결정일 %s ≤ 재무기준일 · 지급 %s 는 F 뒤 — F 재무상태표의 미지급배당금이다(이월 다리에서 빼지 않는다)" % (결정일, 지급일)
        return False, 기준일, ("결정일 %s ≤ 재무기준일 · 지급 예정일 미기재 — 지급이 F 뒤여도 F 재무상태표의 미지급배당금이다(이월 다리에서 빼지 않는다)" % 결정일)
    if 결정일 > T:
        return False, 결정일, "결정이 평가기준일 뒤 — 평가기준일 후 사건"
    if 지급일 and 지급일 <= T:
        return True, 지급일, "(F, T] 결정 · 지급 %s" % 지급일
    if 기준일:
        if 기준일 <= T:
            return True, 기준일, ("(F, T] 결정 · %s · 배당기준일 %s ≤ T — T 주가는 배당락 뒤이고 T 에 미지급배당금이 부채로 선다(뺀다)"
                              % ("지급 %s 는 T 뒤" % 지급일 if 지급일 else "지급 예정일 미기재(배당기준일로 판정)", 기준일))
        return False, 기준일, "배당기준일 %s 이 평가기준일 뒤 — T 주가가 배당 권리를 품는다(빼지 않는다)" % 기준일
    if 지급일:
        return False, 지급일, "지급 %s 이 평가기준일 뒤 · 배당기준일 미기재 — 평가기준일 후 사건" % 지급일
    return None, None, "확인 불가 — 지급 예정일 · 배당기준일을 둘 다 원문에서 못 읽었다"


def 기간가르기(줄들, F, T):
    """일자별 줄 → (안 (F, T], 앞 ≤ F, 뒤 > T)."""
    안 = [x for x in 줄들 if _사이(x["일자"], F, T)]
    앞 = [x for x in 줄들 if x["일자"] <= F]
    뒤 = [x for x in 줄들 if x["일자"] > T]
    return 안, 앞, 뒤


def _합(xs, 키):
    v = [x.get(키) for x in xs]
    return None if (not v or any(a is None for a in v)) else float(sum(v))


def _사건(종류, 역할, 행, **kw):
    s = {"날짜": None, "종류": 종류, "역할": 역할, "현금": None, "주식수": None, "부채감소": None, "반영": None, "확인상태": None,
         "표지": [], "근거": {}, "접수번호": 행.get("rcept_no"), "공시일": 날짜(행.get("rcept_dt")), "제목": (행.get("report_nm") or "").strip(),
         "정정": 정정인가(행.get("report_nm"))}
    s.update(kw)
    return s


# ════════════════════════════════════════ 종류별 읽기(문 = 공시표.읽기 · 행 = list.json 항목)
def 읽기_증자결과(문, 행, F, T):
    kv = 칸들(문)
    주 = 수(값(kv, r"실제발행주식수")) or 수(표열값(문, r"자금조달|실제조달", r"수량", r"총계|^계|합계")) or 수(표열값(문, r"청약및배정|배정현황", r"최종배정.*수량", r"계"))
    금 = 수(값(kv, r"실제발행금액")) or 수(표열값(문, r"자금조달|실제조달", r"발행총액", r"총계|^계|합계")) or 수(표열값(문, r"발행개요", r"발행총액"))
    가 = 수(표열값(문, r"자금조달|실제조달", r"발행가액", r"총계|^계|합계"))
    납 = 날짜(값(kv, r"납입일")) or 날짜(표열값(문, r"납입일정|청약및납입", r"납입기일"))
    근 = {"실제발행주식수": 주, "실제발행금액": 금, "발행가액": 가, "납입일": 납, "발행방법": 값(kv, r"발행방법")}
    s = _사건("증자", "결과" if 행.get("_역할") != "결과대조" else "결과대조", 행, 날짜=납, 근거=근)
    if 주 is None or 금 is None or not 납:
        빠 = [k for k, v in (("주식수", 주), ("발행금액", 금), ("납입일", 납)) if v in (None, "")]
        s["확인상태"] = "확인 불가 — 원문 표에서 %s 을(를) 못 읽었다" % " · ".join(빠)
        return [s]
    s.update(현금=금, 주식수=주)
    if not _사이(납, F, T):
        s.update(반영=False, 확인상태="확인완료(원문 표)")
        s["표지"].append("납입일 %s 이 (F, T] 밖 — %s" % (납, "F 재무상태표에 있다" if 납 <= F else "평가기준일 후 사건"))
        return [s]
    s.update(반영=True, 확인상태="확인완료(원문 표)")
    s["표지"].append("발행 총액(발행비용 차감 전) — 순액은 다음 정기보고서")
    return [s]


def 읽기_자기주식결과(문, 행, F, T, 종류):
    """자기주식 취득 · 처분 결과보고서 — 일자별 줄을 (F, T] 로 가른다."""
    부호 = -1.0 if 종류 == "자기주식취득" else 1.0
    동 = "취득" if 종류 == "자기주식취득" else "처분"
    줄 = 날짜줄들(문, r"%s수량|^수량%s수량" % (동, 동), r"%s가액총액|총액" % 동, r"1주당%s가액|1주당|단가" % 동, r"%s대상|대상|상대방|취득방법|처분방법" % 동)
    if not 줄:
        줄 = 날짜줄들(문, r"수량", r"총액", r"1주당|단가", r"대상|상대방|방법")
    kv = 칸들(문)
    목적 = " ".join(x for x in [값(kv, r"%s목적" % 동), 값(kv, r"%s상대방|%s대상" % (동, 동))] if x) or " ".join(sorted({(x.get("대상") or "") for x in 줄}))
    if not 줄:
        s = _사건(종류, "결과", 행, 확인상태="확인 불가 — 결과보고서에서 일자별 %s 내역 표를 못 읽었다" % 동)
        return [s]
    안, 앞, 뒤 = 기간가르기(줄, F, T)
    낸 = []
    if 안:
        주, 금 = _합(안, "수량"), _합(안, "총액")
        s = _사건(종류, "결과", 행, 날짜=max(x["일자"] for x in 안), 근거={"일자별": [{k: x[k] for k in ("일자", "수량", "단가", "총액", "대상")} for x in 안],
                                                                       "목적 · 상대방": 목적 or None})
        if 주 is None or (금 is None and 종류 == "자기주식취득"):
            s["확인상태"] = "확인 불가 — (F, T] 줄의 %s 을(를) 못 읽었다" % ("수량" if 주 is None else "총액")
        elif 종류 == "자기주식처분" and 보상꼴.search(목적 or "") and not 매도꼴.search(목적 or ""):
            s.update(현금=0.0, 주식수=주, 반영=True, 확인상태="확인완료(원문 표) · 확인 필요 — 보상 지급 처분")
            s["표지"].append("처분 목적 · 상대방이 보수 · 보상(%s) — 현금 유입 없음(처분가액 총액 %s 원은 보상 평가액). 유통주식수만 늘린다"
                           % (목적, "{:,.0f}".format(금) if 금 is not None else "?"))
        elif 금 is None:
            s["확인상태"] = "확인 불가 — (F, T] 처분 줄의 처분가액 총액을 못 읽었다"
        else:
            s.update(현금=부호 * 금, 주식수=부호 * 주, 반영=True, 확인상태="확인완료(원문 표)")
        낸.append(s)
    if 앞:
        s = _사건(종류, "결과", 행, 날짜=max(x["일자"] for x in 앞), 반영=False, 확인상태="확인완료(원문 표)",
                현금=(부호 * _합(앞, "총액")) if _합(앞, "총액") is not None else None, 주식수=(부호 * _합(앞, "수량")) if _합(앞, "수량") is not None else None)
        s["표지"].append("일자 %s ≤ 재무기준일 — F 재무상태표(자기주식)에 있다 · 이월 다리에서 빼지 않는다" % " · ".join(sorted({x["일자"] for x in 앞})))
        낸.append(s)
    if 뒤:
        s = _사건(종류, "결과", 행, 날짜=min(x["일자"] for x in 뒤), 반영=False, 확인상태="확인완료(원문 표)",
                현금=(부호 * _합(뒤, "총액")) if _합(뒤, "총액") is not None else None, 주식수=(부호 * _합(뒤, "수량")) if _합(뒤, "수량") is not None else None)
        s["표지"].append("일자가 평가기준일 뒤 — 평가기준일 후 사건")
        낸.append(s)
    return 낸


def 읽기_자기주식결정(문, 행, F, T, 종류):
    kv = 칸들(문)
    동 = "취득" if 종류 == "자기주식취득" else "처분"
    주 = 수(값(kv, r"%s예정주식.*보통" % 동)) or 수(값(kv, r"%s예정주식" % 동))
    금 = 수(값(kv, r"%s예정금액.*보통" % 동)) or 수(값(kv, r"%s예정금액|계약금액" % 동))
    시 = 날짜(값(kv, r"%s(예상|예정)기간.*시작|계약기간.*시작" % 동))
    끝 = 날짜(값(kv, r"%s(예상|예정)기간.*종료|계약기간.*종료" % 동))
    결 = 날짜(값(kv, r"%s결정일|이사회결의일|결정일" % 동)) or 날짜(행.get("rcept_dt"))
    근 = {"예정주식수": 주, "예정금액": 금, "기간시작": 시, "기간종료": 끝, "결정일": 결, "목적": 값(kv, r"%s목적" % 동),
         "방법": 값(kv, r"%s방법" % 동), "상대방": 값(kv, r"%s상대방" % 동)}
    s = _사건(종류, 행.get("_역할") or "결정", 행, 날짜=결, 반영=False, 확인상태="참고(결정 — 실행 아님)", 근거=근)
    s["표지"].append("결정은 실행이 아니다 — 다리에는 결과보고서의 일자별 실행분만 든다")
    return [s]


def 읽기_배당(문, 행, F, T):
    kv = 칸들(문)
    총 = 수(값(kv, r"배당금총액"))
    주당 = 수(값(kv, r"1주당배당금.*보통")) or 수(값(kv, r"1주당배당금"))
    기 = 날짜(값(kv, r"배당기준일"))
    지 = 날짜(값(kv, r"배당금지급예정일|지급예정일|지급일"))
    결 = 날짜(값(kv, r"이사회결의일|결정일"))
    종 = 값(kv, r"배당종류") or ""
    근 = {"배당구분": 값(kv, r"배당구분"), "배당종류": 종 or None, "1주당배당금(보통)": 주당, "배당금총액": 총, "배당기준일": 기, "지급예정일": 지, "결정일": 결}
    반, 날, 표 = 배당판정(결, 기, 지, F, T)
    s = _사건("배당", "결정", 행, 날짜=날, 근거=근)
    s["표지"].append(표)
    if 반 is None:
        s["확인상태"] = 표
        return [s]
    if "현물" in 종 and "현금" not in 종:
        s.update(확인상태="확인 필요 — 현물배당(현금이 아니다 — 자산 유출을 사람이 적는다)", 반영=None)
        return [s]
    if 총 is None:
        s.update(확인상태="확인 불가 — 배당금총액을 원문 표에서 못 읽었다", 반영=None if 반 else False)
        return [s]
    s.update(현금=-총, 주식수=0.0, 반영=반,
             확인상태="확인완료(원문 표)" + ("" if (지 or not 반) else " · 지급 예정일 미기재(배당기준일로 판정)"))
    return [s]


def 읽기_전환행사(문, 행, F, T, 종류):
    """전환 · 교환청구권 · 신주인수권 · 주식매수선택권 행사 — 일자별 줄(청구일 · 행사일)을 (F, T] 로."""
    if 종류 in ("전환", "교환"):
        줄 = 날짜줄들(문, r"(전환|교환|발행|교부)주식수|주식수", r"청구금액|사채금액|권면", r"(전환|교환)가액|가액")
    else:
        줄 = 날짜줄들(문, r"(행사|발행|교부)주식수|주식수", r"행사금액|납입금액|금액", r"행사가(액|격)|가(액|격)")
    if not 줄:
        return [_사건(종류, "결과", 행, 확인상태="확인 불가 — 일자별 %s 내역 표(청구 · 행사일 · 주식수)를 못 읽었다" % 종류)]
    안, 앞, 뒤 = 기간가르기(줄, F, T)
    낸 = []
    if 안:
        주 = _합(안, "수량")
        금 = _합(안, "총액")
        if 금 is None and all(x.get("단가") is not None and x.get("수량") is not None for x in 안):
            금 = float(sum(x["단가"] * x["수량"] for x in 안))
        s = _사건(종류, "결과", 행, 날짜=max(x["일자"] for x in 안), 근거={"일자별": [{k: x[k] for k in ("일자", "수량", "단가", "총액")} for x in 안]})
        if 주 is None:
            s["확인상태"] = "확인 불가 — (F, T] 줄의 주식수를 못 읽었다"
        elif 종류 in ("전환", "교환"):
            s.update(현금=0.0, 주식수=주, 부채감소=금, 반영=True, 확인상태="확인완료(원문 표) · 확인 필요 — 사채가 주식으로")
            s["표지"].append("현금 유입이 아니다 — 청구금액(%s)은 사채 감소다. 재무기준일 이자부부채에 그 사채가 들었으면 사람이 131 에 더한다"
                           % ("{:,.0f}".format(금) if 금 is not None else "못 읽음"))
        elif 금 is None:
            s["확인상태"] = "확인 불가 — (F, T] 행사 금액(행사가 × 주식수)을 못 읽었다"
        else:
            s.update(현금=금, 주식수=주, 반영=True, 확인상태="확인완료(원문 표)")
            if 종류 == "행사" and re.search(r"자기주식", " ".join(_표준(" ".join(x.get("앞글") or [])) for x in (문 or {}).get("표") or [])):
                s["표지"].append("자기주식 교부 행사일 수 있다 — 유통주식수는 같게 늘고 발행주식수는 그대로")
        낸.append(s)
    for 쪽, 무리 in (("앞", 앞), ("뒤", 뒤)):
        if 무리:
            s = _사건(종류, "결과", 행, 날짜=(max if 쪽 == "앞" else min)(x["일자"] for x in 무리), 반영=False, 확인상태="확인완료(원문 표)",
                    주식수=_합(무리, "수량"))
            s["표지"].append("일자 ≤ 재무기준일 — F 재무상태표에 있다" if 쪽 == "앞" else "일자가 평가기준일 뒤 — 평가기준일 후 사건")
            낸.append(s)
    return 낸


def 읽기_소각(문, 행, F, T):
    kv = 칸들(문)
    주 = 수(값(kv, r"소각할주식의종류와수.*보통")) or 수(값(kv, r"소각할주식"))
    취득연계 = bool(값(kv, r"소각을위한자기주식취득예정기간.*시작|취득예정기간"))
    근 = {"소각주식수": 주, "소각예정일": 날짜(값(kv, r"소각예정일")), "발행주식총수": 수(값(kv, r"발행주식총수.*보통")),
         "결정일": 날짜(값(kv, r"이사회결의일|결정일")), "취득연계": 취득연계}
    s = _사건("소각", "결정", 행, 날짜=근["결정일"] or 날짜(행.get("rcept_dt")), 주식수=0.0, 현금=0.0, 반영=False, 확인상태="확인완료(원문 표)", 근거=근)
    s["표지"].append("자기주식의 소각은 유통주식수를 바꾸지 않는다(발행주식수와 자기주식수가 같이 준다) — 기록만(13번 135 에 넣지 않는다)" +
                   (" · 소각 대상은 같은 결정의 취득 예정 자기주식 — 유통주식수 변동은 그 취득(결과보고서)에서 센다" if 취득연계 else ""))
    return [s]


def 읽기_기타결정(문, 행, F, T, 종류):
    kv = 칸들(문)
    if 종류 == "증자":
        납 = 날짜(값(kv, r"납입일"))
        s = _사건("증자", "결정", 행, 날짜=날짜(값(kv, r"이사회결의일|결정일")) or 날짜(행.get("rcept_dt")), 반영=False, 확인상태="참고(결정 — 실행 아님)",
                근거={"신주의수": 수(값(kv, r"신주의종류와수.*보통")) or 수(값(kv, r"신주의종류와수")), "납입일": 납, "증자방식": 값(kv, r"증자방식")})
        s["표지"].append("유상증자 결정 — 실행은 증권발행실적보고서 · 발행결과에서 센다")
        return [s]
    s = _사건(종류, "결정", 행, 날짜=날짜(값(kv, r"이사회결의일|결정일")) or 날짜(행.get("rcept_dt")), 반영=None,
            확인상태="확인 필요 — %s 은(는) 주식수 기준을 바꾼다(사람이 적는다)" % 종류,
            근거={"신주의수": 수(값(kv, r"신주의종류와수.*보통|신주의수")), "기준일": 날짜(값(kv, r"신주배정기준일|기준일"))})
    return [s]


# ════════════════════════════════════════ 모으기(네트워크 0 — 목록 · 원문 읽기 함수를 받는다)
def 모으기(목록, 원문, F, T, 앞창=앞창일):
    """목록(list.json 항목들) · 원문(접수번호 → 문 | None) · F · T(ISO) → (사건[], 확인불가[], 경보[], 셈{})."""
    시작앞 = (datetime.date.fromisoformat(F) - datetime.timedelta(days=앞창)).isoformat()
    사건, 확인불가, 경보 = [], [], []
    셈 = {"목록": len(목록 or []), "관련": 0, "원문": 0}
    for 행 in sorted(목록 or [], key=lambda x: (x.get("rcept_dt") or "", x.get("rcept_no") or "")):
        종, 역 = 종류가르기(행.get("report_nm"))
        if not 종:
            continue
        접일 = 날짜(행.get("rcept_dt"))
        if not 접일 or 접일 > T:
            continue
        if 접일 <= F and not (종 == "배당" and 접일 >= 시작앞):
            continue                                                  # F 이하 제출 — 배당결정만 미지급 판정용으로 본다
        셈["관련"] += 1
        행 = dict(행, _역할=역)
        문 = 원문(행.get("rcept_no"))
        if 문 is None:
            s = _사건(종, 역, 행, 날짜=접일, 확인상태="확인 불가 — 원문을 받지 못했다(받기 실패 · 오프라인 · 한도)")
            사건.append(s)
            continue
        셈["원문"] += 1
        try:
            if 종 == "증자" and 역 in ("결과", "결과대조"):
                낸 = 읽기_증자결과(문, 행, F, T)
            elif 종 in ("자기주식취득", "자기주식처분") and 역 in ("결과", "신탁결과"):
                낸 = 읽기_자기주식결과(문, 행, F, T, 종)
            elif 종 in ("자기주식취득", "자기주식처분"):
                낸 = 읽기_자기주식결정(문, 행, F, T, 종)
            elif 종 == "배당":
                낸 = 읽기_배당(문, 행, F, T)
            elif 종 in ("전환", "교환", "행사"):
                낸 = 읽기_전환행사(문, 행, F, T, 종)
            elif 종 == "소각":
                낸 = 읽기_소각(문, 행, F, T)
            else:
                낸 = 읽기_기타결정(문, 행, F, T, 종)
        except Exception as e:                                           # noqa: BLE001 — 한 공시를 못 읽어도 나머지는 간다
            낸 = [_사건(종, 역, 행, 날짜=접일, 확인상태="확인 불가 — 원문 읽기 오류 %s: %s" % (type(e).__name__, str(e)[:120]))]
        if 종 == "배당" and 접일 <= F:                                  # F 앞 결정 가운데 F 전에 지급까지 끝난 것은 다리와 무관 — 싣지 않는다
            낸 = [s for s in 낸 if "재무기준일 전에 지급" not in " ".join(s["표지"])]
        사건 += 낸
    사건 = _정정묶기(사건)
    사건 = _대조묶기(사건, 경보)
    _결정잇기(사건, F, T, 확인불가)
    for s in 사건:
        if (s.get("확인상태") or "").startswith("확인 불가") or ((s.get("확인상태") or "").startswith("확인 필요") and s.get("반영") is None):
            확인불가.append({"접수번호": s.get("접수번호"), "제목": s.get("제목"), "종류": s.get("종류"), "까닭": s.get("확인상태")})
    사건.sort(key=lambda s: (s.get("날짜") or "9999", s.get("접수번호") or "", s.get("종류")))
    return 사건, 확인불가, 경보, 셈


def _열쇠(s):
    k = s.get("근거") or {}
    return (s["종류"], s["역할"], k.get("납입일") or k.get("배당기준일") or k.get("기간시작") or k.get("소각주식수") or s.get("날짜"),
            (s.get("표지") or [""])[0][:12] if s["역할"] == "결과" else "")


def _정정묶기(사건):
    """같은 사건(종류 · 역할 · 핵심 날짜)의 원본과 정정 — 늦은 접수번호 하나만 남기고 앞 것은 `정정이력` 에."""
    무리 = {}
    for s in 사건:
        무리.setdefault(_열쇠(s), []).append(s)
    낸 = []
    for k, xs in 무리.items():
        if len(xs) == 1 or not any(x.get("정정") for x in xs):
            낸 += xs
            continue
        xs = sorted(xs, key=lambda x: x.get("접수번호") or "")
        끝 = dict(xs[-1])
        끝["정정이력"] = [x.get("접수번호") for x in xs[:-1]]
        낸.append(끝)
    return 낸


def _대조묶기(사건, 경보):
    """증권발행실적보고서(결과) ↔ 발행결과 자율공시(결과대조) — 납입일 · 주식수가 맞으면 하나로(대조 일치), 다르면 둘 다 두고 경보."""
    주 = [s for s in 사건 if s["종류"] == "증자" and s["역할"] == "결과"]
    대 = [s for s in 사건 if s["종류"] == "증자" and s["역할"] == "결과대조"]
    뺄 = set()
    for d in 대:
        짝 = next((p for p in 주 if p.get("날짜") == d.get("날짜") and p.get("주식수") == d.get("주식수")), None)
        if 짝:
            짝.setdefault("대조", []).append({"접수번호": d.get("접수번호"), "제목": d.get("제목"), "일치": 짝.get("현금") == d.get("현금"),
                                           "현금": d.get("현금")})
            if 짝.get("현금") != d.get("현금"):
                경보.append("증자 %s — 실적보고서 금액 %s ≠ 자율공시 %s(실적보고서 값을 쓴다)" % (짝.get("날짜"), 짝.get("현금"), d.get("현금")))
            뺄.add(id(d))
        elif 주:
            경보.append("증자 발행결과(자율공시 %s)에 짝이 되는 증권발행실적보고서가 없다 — 둘 다 남긴다" % d.get("접수번호"))
        else:
            d["역할"] = "결과"                                         # 실적보고서가 없으면 자율공시가 결과다
    return [s for s in 사건 if id(s) not in 뺄]


def _결정잇기(사건, F, T, 확인불가):
    """자기주식 · 증자 결정이 (F, T] 를 걸치는데 그 기간의 결과가 없으면 확인 불가(실행분 미공시)."""
    for s in 사건:
        if s["역할"] not in ("결정", "신탁결정") or s["종류"] not in ("자기주식취득", "자기주식처분", "증자"):
            continue
        k = s.get("근거") or {}
        if s["종류"] == "증자":
            납 = k.get("납입일")
            결과 = [x for x in 사건 if x["종류"] == "증자" and x["역할"] == "결과" and (not 납 or x.get("날짜") == 납)]
            if 결과:
                s["연결"] = [x.get("접수번호") for x in 결과]
            elif 납 and 납 <= T and 납 > F:
                s["표지"].append("납입일 %s 이 (F, T] 인데 증권발행실적보고서 · 발행결과가 목록에 없다" % 납)
                확인불가.append({"접수번호": s.get("접수번호"), "제목": s.get("제목"), "종류": "증자",
                             "까닭": "확인 불가 — 유상증자 납입(%s)의 결과 공시가 평가기준일까지 없다(사람이 원문으로)" % 납})
            continue
        시, 끝 = k.get("기간시작"), k.get("기간종료")
        if not 시:
            continue
        결과 = [x for x in 사건 if x["종류"] == s["종류"] and x["역할"] in ("결과", "신탁결과") and x.get("날짜") and 시 <= x["날짜"] <= (끝 or "9999")]
        if 결과:
            s["연결"] = sorted({x.get("접수번호") for x in 결과})
            continue
        if 시 <= T and (끝 or 시) > F:
            진행 = bool(끝 and 끝 > T)
            까 = ("확인 불가 — %s 결정(기간 %s ~ %s · 예정 %s주 · %s원)의 (F, T] 실행분이 공시되지 않았다%s" % (
                s["종류"], 시, 끝 or "?", _글수(k.get("예정주식수")), _글수(k.get("예정금액")),
                " — 기간이 평가기준일 뒤에 끝나 결과보고서가 T 뒤에 나온다(사람이 거래소 공시 · 다음 정기보고서로 적는다)" if 진행 else " — 결과보고서가 목록에 없다"))
            s["표지"].append(까)
            확인불가.append({"접수번호": s.get("접수번호"), "제목": s.get("제목"), "종류": s["종류"], "까닭": 까})


def _글수(v):
    return "{:,.0f}".format(v) if isinstance(v, (int, float)) else "?"


# ════════════════════════════════════════ 13번 줄 합계(02_줄번호 3절) — 공시채움 ⑦ 이 부른다
def 줄합계(산출):
    """「사이자본거래/1」 → {"칸": {"131": 원, …, "135": 주}, "건": {칸: 접수번호[]}, "빈칸까닭": {칸: 글}, "관측": [...], "사람확인": [...]}.
    반영 = true 인 사건만 더한다. 칸에 든 사건이 하나도 없는데 그 칸의 확인 불가 사건이 있으면 그 칸은 값 대신 까닭(0 으로 메우지 않는다)."""
    합 = {k: 0.0 for k in 칸.values()}
    건 = {k: [] for k in 칸.values()}
    관측, 사람 = [], []
    for s in (산출 or {}).get("사건") or []:
        if s.get("반영") is not True:
            continue
        종, 현, 주 = s.get("종류"), s.get("현금"), s.get("주식수")
        if 종 in 유입종류:
            if 현:
                합[칸["유입현금"]] += abs(현)
                건[칸["유입현금"]].append(s.get("접수번호"))
            if 주:
                합[칸["주식증가"]] += abs(주)
                건[칸["주식증가"]].append(s.get("접수번호"))
        elif 종 in 주식만종류:
            if 주:
                합[칸["주식증가"]] += abs(주)
                건[칸["주식증가"]].append(s.get("접수번호"))
            if s.get("부채감소"):
                사람.append("%s %s — 사채 %s 원이 주식으로(재무기준일 이자부부채에 들었으면 131 에 더한다)" % (s.get("날짜"), 종, _글수(s.get("부채감소"))))
        elif 종 == "자기주식취득":
            if 현:
                합[칸["취득현금"]] += abs(현)
                건[칸["취득현금"]].append(s.get("접수번호"))
            if 주:
                합[칸["주식감소"]] += abs(주)
                건[칸["주식감소"]].append(s.get("접수번호"))
        elif 종 == "배당":
            if 현:
                합[칸["배당현금"]] += abs(현)
                건[칸["배당현금"]].append(s.get("접수번호"))
        else:
            continue
        관측.append({"날짜": s.get("날짜"), "종류": "전환" if 종 == "교환" else 종,      # 02_줄번호 3절 종류표(교환 = 전환 줄 · 131/134)
                   "현금": abs(현) if 현 else 0.0, "주식수": abs(주) if 주 else 0.0,
                   "출처": "DART %s" % s.get("접수번호") if (산출 or {}).get("국가") != "US" else "SEC %s" % s.get("접수번호"),
                   "설명": "%s" % (s.get("제목") or 종),                   # 2026-10-26 — 독자층(레터 사이 표의 내용 칸) · 확인 상태는 따로
                   "확인상태": s.get("확인상태") or ""})
    빈 = {}
    칸종류 = {"131": 유입종류, "132": ("자기주식취득",), "133": ("배당",), "134": 유입종류 + 주식만종류, "135": ("자기주식취득",)}
    for x in (산출 or {}).get("확인불가") or []:
        for k, 종들 in 칸종류.items():
            if x.get("종류") in 종들:
                빈.setdefault(k, []).append("%s %s" % (x.get("접수번호") or "", x.get("까닭") or ""))
    return {"칸": {k: (v if (건[k] or k not in 빈) else None) for k, v in 합.items()}, "건": 건,
            "빈칸까닭": {k: " / ".join(v) for k, v in 빈.items()}, "관측": 관측, "사람확인": 사람}


# ════════════════════════════════════════ 국내 받기(OpenDART — dart_fetch._get 의 안전 속도 · 재시도)
def _DF():
    import dart_fetch                                                    # noqa: PLC0415
    return dart_fetch


def 목록받기(고유, 시작, 끝, raw, 오프라인=False, 기록=None):
    """list.json(모든 종류 · 쪽마다 100건) → 항목[]. 캐시 `<raw>/사이자본거래원문/목록_<고유>_<시작>_<끝>.json` 이 있으면 그대로."""
    p = os.path.join(raw, 원문폴더, "목록_%s_%s_%s.json" % (고유, 시작.replace("-", ""), 끝.replace("-", "")))
    if os.path.exists(p):
        return json.load(io.open(p, encoding="utf-8")).get("list") or []
    if 오프라인:
        raise FileNotFoundError("목록 캐시가 없다(오프라인) — %s" % os.path.basename(p))
    DF = _DF()
    if not DF.KEY:
        raise RuntimeError("OPENDART_API_KEY 가 환경변수에 없다(값은 화면에 적지 않는다)")
    낸, 쪽수 = [], 1
    for 쪽 in range(1, 쪽상한 + 1):
        j = DF._get("list.json", corp_code=고유, bgn_de=시작.replace("-", ""), end_de=끝.replace("-", ""), page_no=쪽, page_count=100).json()
        if 기록 is not None:
            기록["호출"] = 기록.get("호출", 0) + 1
        st = j.get("status")
        if st == "020":
            raise 한도초과("list.json %s 쪽 %d" % (고유, 쪽))
        if st == "013":
            break
        if st not in (None, "000"):
            raise RuntimeError("OpenDART list.json status %s %s" % (st, j.get("message")))
        낸 += j.get("list") or []
        쪽수 = int(j.get("total_page") or 1)
        if 쪽 >= 쪽수:
            break
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with io.open(p, "w", encoding="utf-8") as f:
        json.dump({"고유번호": 고유, "시작": 시작, "끝": 끝, "조회일": datetime.date.today().isoformat(), "쪽수": 쪽수, "list": 낸}, f, ensure_ascii=False, indent=1)
    return 낸


def 원문받기(접수, raw, 오프라인=False, 기록=None):
    """document.xml(ZIP) → `<raw>/사이자본거래원문/<접수>/` 의 본문 XML 경로 | None. 있으면 다시 받지 않는다."""
    d = os.path.join(raw, 원문폴더, 접수)
    있 = sorted(glob.glob(os.path.join(d, "*.xml")))
    if 있:
        본 = [p for p in 있 if os.path.basename(p).startswith(접수)]
        return (본 or 있)[0]
    if 오프라인:
        return None
    DF = _DF()
    r = DF._get("document.xml", rcept_no=접수)
    if 기록 is not None:
        기록["호출"] = 기록.get("호출", 0) + 1
    if r.content[:2] != b"PK":
        try:
            if (json.loads(r.content.decode("utf-8", "ignore")) or {}).get("status") == "020":
                raise 한도초과("document.xml %s" % 접수)
        except ValueError:
            pass
        return None
    os.makedirs(d, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        for n in z.namelist():
            with open(os.path.join(d, os.path.basename(n)), "wb") as f:
                f.write(z.read(n))
    있 = sorted(glob.glob(os.path.join(d, "*.xml")))
    본 = [p for p in 있 if os.path.basename(p).startswith(접수)]
    return (본 or 있 or [None])[0]


def 국내(고유, F, T, raw, 오프라인=False):
    """→ 산출 dict(「사이자본거래/1」 · 국내). 한도 초과면 그 자리에서 멈추고 `한도초과` · `남은받기` 를 적는다."""
    기록 = {"호출": 0}
    시작 = (datetime.date.fromisoformat(F) - datetime.timedelta(days=앞창일)).isoformat()
    낸 = _머리("KR", {"고유번호": 고유}, F, T)
    낸["창"] = {"목록시작": 시작, "사이시작": (datetime.date.fromisoformat(F) + datetime.timedelta(days=1)).isoformat(), "끝": T,
               "까닭": "F 앞 %d일은 배당결정의 미지급 판정용(결정일 ≤ F) — 그 밖 종류는 F 다음 날부터" % 앞창일}
    try:
        목 = 목록받기(고유, 시작, T, raw, 오프라인, 기록)
    except 한도초과 as e:
        낸.update(한도초과=str(e), 남은받기=["목록 %s ~ %s" % (시작, T)])
        return 낸
    except (FileNotFoundError, RuntimeError) as e:
        낸["경보"].append("목록을 받지 못했다 — %s" % e)
        낸["확인불가"].append({"접수번호": None, "제목": "공시 목록", "종류": None, "까닭": "확인 불가 — %s" % e})
        return 낸
    남은 = []
    문들 = {}

    def 원문(접수):
        if 접수 in 문들:
            return 문들[접수]
        if 남은:
            남은.append(접수)
            return None
        try:
            p = 원문받기(접수, raw, 오프라인, 기록)
        except 한도초과 as e:
            낸["한도초과"] = str(e)
            남은.append(접수)
            return None
        문들[접수] = 공시표.읽기(p) if p else None
        return 문들[접수]
    사건, 확인불가, 경보, 셈 = 모으기(목, 원문, F, T)
    if 남은:
        낸["남은받기"] = ["원문 %s" % x for x in 남은]
    셈["호출"] = 기록["호출"]
    낸.update(사건=사건, 확인불가=확인불가, 셈=셈)
    낸["경보"] += 경보
    return 낸


# ════════════════════════════════════════ 미국(SEC) — 8-K 에서 되는 만큼
_월 = {m: i for i, m in enumerate(["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"], 1)}


def 영문날짜(s):
    m = re.search(r"([A-Za-z]{3,9})\.?\s+(\d{1,2}),?\s+(\d{4})", s or "")
    if not m:
        return None
    mo = next((v for k, v in _월.items() if k.startswith(m.group(1).lower()[:3])), None)
    try:
        return datetime.date(int(m.group(3)), mo, int(m.group(2))).isoformat() if mo else None
    except ValueError:
        return None


def 미국배당읽기(글, 공시일):
    """8-K · EX-99 글 → [{"주당", "지급일", "기준일", "결정일", "문장"}] — 「declared a … dividend of $X per share … payable on D to … of record (on|as of) D」."""
    글 = re.sub(r"\s+", " ", 글 or "")
    낸 = []
    for m in re.finditer(r"([^.]{0,200}?declared[^.]{0,120}?dividends?\s+of\s+\$\s?([0-9]+(?:\.[0-9]+)?)\s+per\s+(?:common\s+|ordinary\s+)?share[^.]{0,300})", 글, re.I):
        문장 = m.group(1)
        # 1.1.10 — 지급일 · 기준일이 다음 문장에 오는 꼴(「… per share of the Company’s common stock. The dividend is payable on …」 ·
        #   「… This dividend will be paid to stockholders of record as of the close of business on D, with a payment date of D」)도 읽는다.
        #   다음 선언(declared) 앞까지 400자만 본다
        뒤 = 글[m.end(1):m.end(1) + 400]
        k = re.search(r"declared", 뒤, re.I)
        볼 = 문장 + (뒤[:k.start()] if k else 뒤)
        _날 = r"([A-Za-z]{3,9}\.?\s+\d{1,2},?\s+\d{4})"
        지 = (re.search(r"payable\s+(?:on\s+)?" + _날, 볼, re.I) or re.search(r"payment\s+date\s+(?:of|is|will\s+be)\s+" + _날, 볼, re.I)
             or re.search(r"(?:will\s+be\s+)?paid\s+on\s+" + _날, 볼, re.I))
        기 = re.search(r"of\s+record\s+(?:(?:at|as\s+of)\s+the\s+close\s+of\s+business\s+)?(?:on|as\s+of)?\s*" + _날, 볼, re.I)
        문장 = 볼.strip()
        # 결정일 — 「On <날짜>, … declared」. 회사 이름의 「Inc.」 · 「Corp.」 마침표가 문장을 끊으므로 선언 앞 300자를 따로 본다
        앞 = 글[max(0, m.start(1) - 300):m.start(1) + max(0, 문장.lower().find("declared"))]
        결 = None
        for 결 in re.finditer(r"\b[Oo]n\s+([A-Za-z]{3,9}\.?\s+\d{1,2},?\s+\d{4})", 앞):
            pass
        낸.append({"주당": float(m.group(2)), "지급일": 영문날짜(지.group(1)) if 지 else None, "기준일": 영문날짜(기.group(1)) if 기 else None,
                  "결정일": (영문날짜(결.group(1)) if 결 else None) or 공시일, "문장": 문장[:300]})
    return 낸


def 표지주식수(cf, T):
    """companyfacts dei:EntityCommonStockSharesOutstanding 가운데 end ≤ T · filed ≤ T 의 가장 늦은 것 → (주식수, end, accn) | (None, …)."""
    u = (((cf or {}).get("facts") or {}).get("dei") or {}).get("EntityCommonStockSharesOutstanding") or {}
    xs = [x for v in (u.get("units") or {}).values() for x in v if (x.get("end") or "") <= T and (x.get("filed") or "") <= T]
    if not xs:
        return None, None, None
    끝 = max(x["end"] for x in xs)
    합 = sum(float(x["val"]) for x in xs if x["end"] == 끝 and x.get("filed") == max(y.get("filed") for y in xs if y["end"] == 끝))
    return 합, 끝, next((x.get("accn") for x in xs if x["end"] == 끝), None)


def 미국모으기(팔K들, F, T, 주식수=None, 앞창=앞창일):
    """팔K들 = [{"accession", "제출일", "글", "항목"}] → (사건[], 확인불가[], 사람이적는다[]). 네트워크 0."""
    시작앞 = (datetime.date.fromisoformat(F) - datetime.timedelta(days=앞창)).isoformat()
    사건, 확인불가 = [], []
    for k in sorted(팔K들 or [], key=lambda x: (x.get("제출일") or "", x.get("accession") or "")):
        제 = k.get("제출일") or ""
        if not 제 or 제 > T or 제 < 시작앞:
            continue
        행 = {"rcept_no": k.get("accession"), "rcept_dt": 제, "report_nm": "8-K %s" % (k.get("항목") or "")}
        for d in 미국배당읽기(k.get("글"), 제):
            if 제 <= F and not (d.get("지급일") and d["지급일"] > F):
                continue
            반, 날, 표 = 배당판정(d.get("결정일"), d.get("기준일"), d.get("지급일"), F, T)
            s = _사건("배당", "결정", 행, 날짜=날, 근거={"주당": d["주당"], "지급일": d.get("지급일"), "기준일": d.get("기준일"),
                                                   "결정일": d.get("결정일"), "문장": d["문장"]})
            s["표지"].append(표)
            if 반 is None:
                s["확인상태"] = 표
            elif 주식수:
                s.update(현금=-d["주당"] * 주식수[0], 주식수=0.0, 반영=반,
                         확인상태="참고(주당 × 표지 주식수 %s · %s — 총액은 다음 10-Q 현금흐름표)" % (_글수(주식수[0]), 주식수[1]))
            else:
                s.update(반영=None if 반 else False, 확인상태="확인 불가 — 주당 %s 달러는 읽었으나 표지 주식수가 없다(총액을 못 셈)" % d["주당"])
            사건.append(s)
        if 제 > F and re.search(r"\b3\.02\b", k.get("항목") or ""):
            s = _사건("증자", "결과", 행, 날짜=제, 확인상태="확인 불가 — 8-K Item 3.02(미등록 지분 매각) — 수량 · 금액을 사람이 원문으로 적는다")
            사건.append(s)
    for s in 사건:
        if (s.get("확인상태") or "").startswith("확인 불가"):
            확인불가.append({"접수번호": s.get("접수번호"), "제목": s.get("제목"), "종류": s.get("종류"), "까닭": s.get("확인상태")})
    사람 = ["자기주식 매입 — (F, T] 분기의 10-Q Part II Item 2 월별 매입 표는 대개 평가기준일 뒤에 제출된다(사람이 회사 발표 · 다음 10-Q 로 132 · 135 를 적는다)",
          "주식 보상 행사 · ESPP · 전환사채 전환 — 8-K 에 수량이 오지 않는다(사람이 Form 4 · 다음 10-Q 로 131 · 134 를 적는다)",
          "등록 공모(424B · S-3) 신주 발행 — 납입이 (F, T] 면 사람이 공모 결과로 131 · 134 를 적는다"]
    사건.sort(key=lambda s: (s.get("날짜") or "9999", s.get("접수번호") or ""))
    return 사건, 확인불가, 사람


def _글로(h):
    h = re.sub(r"(?is)<(script|style|ix:header)[^>]*>.*?</\1>", " ", h or "")
    h = re.sub(r"(?s)<[^>]+>", " ", h)
    return re.sub(r"\s+", " ", _html.unescape(h)).strip()


def 미국(티커, F, T, raw, 오프라인=False):
    낸 = _머리("US", {"티커": (티커 or "").upper()}, F, T)
    sub = None
    p = os.path.join(raw, "submissions.json")
    if os.path.exists(p):
        sub = json.load(io.open(p, encoding="utf-8"))
    연락 = os.environ.get("SEC_CONTACT_EMAIL")
    H = {"User-Agent": "DCF-research %s" % 연락, "Accept-Encoding": "gzip, deflate"} if 연락 else None
    if sub is None and not 오프라인:
        if not H:
            낸["확인불가"].append({"접수번호": None, "제목": "submissions", "종류": None, "까닭": "확인 불가 — SEC_CONTACT_EMAIL 이 없고 _raw/submissions.json 도 없다"})
            return 낸
        import requests                                                   # noqa: PLC0415
        r = requests.get("https://www.sec.gov/files/company_tickers.json", headers=dict(H, Host="www.sec.gov"), timeout=60)
        cik = next((int(v["cik_str"]) for v in r.json().values() if v["ticker"].upper() == 낸["회사"]["티커"]), None) if r.status_code == 200 else None
        if cik:
            r = requests.get("https://data.sec.gov/submissions/CIK%010d.json" % cik, headers=dict(H, Host="data.sec.gov"), timeout=60)
            sub = r.json() if r.status_code == 200 else None
    if sub is None:
        낸["확인불가"].append({"접수번호": None, "제목": "submissions", "종류": None, "까닭": "확인 불가 — submissions 를 못 읽었다"})
        return 낸
    cik = int(sub.get("cik") or 0)
    낸["회사"].update(CIK="%010d" % cik, 이름=sub.get("name"))
    rec = (sub.get("filings") or {}).get("recent") or {}
    시작앞 = (datetime.date.fromisoformat(F) - datetime.timedelta(days=앞창일)).isoformat()
    팔K = []
    for i, f in enumerate(rec.get("form") or []):
        제 = rec["filingDate"][i]
        if f not in ("8-K", "8-K/A") or not (시작앞 <= 제 <= T):
            continue
        acc = rec["accessionNumber"][i]
        d = os.path.join(raw, 원문폴더, "US", acc)
        글들 = []
        for q in sorted(glob.glob(os.path.join(d, "*.htm*"))):
            글들.append(_글로(io.open(q, encoding="utf-8", errors="ignore").read()))
        if not 글들 and not 오프라인 and H:
            import requests                                               # noqa: PLC0415
            기 = "https://www.sec.gov/Archives/edgar/data/%d/%s/" % (cik, acc.replace("-", ""))
            r = requests.get(기 + "index.json", headers=dict(H, Host="www.sec.gov"), timeout=60)
            time.sleep(0.3)
            이름들 = [x.get("name") for x in ((r.json().get("directory") or {}).get("item") or [])] if r.status_code == 200 else []
            고른 = [n for n in 이름들 if n and re.search(r"\.htm", n, re.I) and (n == rec["primaryDocument"][i] or re.search(r"ex-?99|ex99", n, re.I))]
            os.makedirs(d, exist_ok=True)
            for n in 고른[:4]:
                r2 = requests.get(기 + n, headers=dict(H, Host="www.sec.gov"), timeout=60)
                time.sleep(0.3)
                if r2.status_code == 200:
                    io.open(os.path.join(d, n), "w", encoding="utf-8", errors="ignore").write(r2.text)
                    글들.append(_글로(r2.text))
        팔K.append({"accession": acc, "제출일": 제, "항목": (rec.get("items") or [""] * len(rec["form"]))[i], "글": " ".join(글들)})
    cf = None
    cp = os.path.join(raw, "companyfacts.json")
    if os.path.exists(cp):
        cf = json.load(io.open(cp, encoding="utf-8"))
    주, 끝, accn = 표지주식수(cf, T)
    사건, 확인불가, 사람 = 미국모으기(팔K, F, T, (주, 끝) if 주 else None)
    낸.update(사건=사건, 확인불가=확인불가, 사람이적는다=사람, 셈={"8-K": len(팔K)})
    return 낸


# ════════════════════════════════════════ 머리 · 저장 · main
def _머리(국가, 회사, F, T):
    return {"형식": 형식, "국가": 국가, "회사": 회사, "재무기준일": F, "평가기준일": T,
            "이월연수": (datetime.date.fromisoformat(T) - datetime.date.fromisoformat(F)).days / 365.0,
            "조회일": datetime.date.today().isoformat(), "도구": 도구표지, "창": {"끝": T},
            "사건": [], "확인불가": [], "사람이적는다": [], "경보": [], "한도초과": None, "남은받기": [], "셈": {},
            "읽는법": "현금 = 원(달러) · + 유입 · − 유출 / 주식수 = 유통주식 + 증가 · − 감소 / 반영 = 이월 다리에 드는가(true) · 참고(false) · 확인 불가(null). "
                     "13번 131~135 는 `줄합계` 가 반영 사건만 더한다(공시채움 ⑦)"}


def 마무리(낸):
    낸["합계"] = 줄합계(낸)
    낸["합계"]["완전"] = not 낸.get("확인불가") and not 낸.get("한도초과")
    return 낸


def 저장(낸, raw, 출력=None):
    p = 출력 or os.path.join(raw, 출력파일)
    os.makedirs(os.path.dirname(os.path.abspath(p)), exist_ok=True)
    with io.open(p + ".쓰는중", "w", encoding="utf-8") as f:
        json.dump(낸, f, ensure_ascii=False, indent=1)
    os.replace(p + ".쓰는중", p)
    return p


def main(argv=None):
    ap = argparse.ArgumentParser(allow_abbrev=False, description="(F, T] 자본거래 — 공시에서 모아 「사이자본거래/1」")
    ap.add_argument("--국가", default="KR", choices=("KR", "US", "kr", "us"))
    ap.add_argument("--회사", default=None, help="국내 고유번호(8자리)")
    ap.add_argument("--ticker", default=None, help="미국 티커")
    ap.add_argument("--재무기준일", "--기준일", dest="재무기준일", default=None, help=_기인.도움말[_기인.재무])
    ap.add_argument("--평가기준일", default=None, help=_기인.도움말[_기인.평가])
    ap.add_argument("--가정", default=None, help=_기인.가정도움말)
    ap.add_argument("--raw", default=os.path.join(os.path.dirname(여기), "_raw"), help="회차 `_raw`(기본: 키트의 _raw)")
    ap.add_argument("-o", "--출력", default=None, help="기본 <raw>/사이자본거래.json")
    ap.add_argument("--조회일", default=None, help="산출 머리의 조회일(시험 · 재현용)")
    ap.add_argument("--오프라인", action="store_true", help="받아 둔 목록 · 원문만(네트워크 0)")
    a = ap.parse_args(argv)
    F = _기인.풀기(a.재무기준일, a.가정, _기인.재무, 인자="--재무기준일")
    T = _기인.풀기(a.평가기준일, a.가정, _기인.평가, 인자="--평가기준일")
    try:
        F = _기인.꼴(_기인.날짜(F)) if F else None
        T = _기인.꼴(_기인.날짜(T)) if T else None
    except _기.기준일오류 as e:
        print("입력 오류 — %s" % e)
        return 입력오류
    if not F or not T:
        print("입력 오류 — 재무기준일 · 평가기준일(또는 --가정)이 있어야 합니다")
        return 입력오류
    if F > T:
        print("입력 오류 — 재무기준일 %s 이 평가기준일 %s 보다 늦습니다" % (F, T))
        return 입력오류
    국가 = a.국가.upper()
    if 국가 == "KR" and not a.회사:
        print("입력 오류 — 국내는 --회사(고유번호)가 있어야 합니다")
        return 입력오류
    if 국가 == "US" and not a.ticker:
        print("입력 오류 — 미국은 --ticker 가 있어야 합니다")
        return 입력오류
    if F != T and not a.오프라인 and os.path.abspath(a.raw) == os.path.abspath(os.path.join(os.path.dirname(여기), "_raw")):
        import 본체가드                                                  # noqa: PLC0415 — 기본 _raw(키트 뿌리)로 받으려면 본체가 아니어야 한다
        본체가드.본체면멈춘다(os.path.dirname(여기))
    if F == T:
        낸 = _머리(국가, {"고유번호": a.회사} if 국가 == "KR" else {"티커": (a.ticker or "").upper()}, F, T)
        낸["경보"].append("재무기준일 = 평가기준일 — 사이 기간이 없다(옛 판 · 이월 0). 받지 않았다")
    elif 국가 == "KR":
        낸 = 국내(a.회사, F, T, a.raw, a.오프라인)
    else:
        낸 = 미국(a.ticker, F, T, a.raw, a.오프라인)
    if a.조회일:
        낸["조회일"] = a.조회일
    마무리(낸)
    p = 저장(낸, a.raw, a.출력)
    합 = 낸["합계"]["칸"]
    print("사이자본거래 %s — (%s, %s] · 사건 %d(반영 %d) · 확인 불가 %d · 호출 %s → %s" % (
        국가, F, T, len(낸["사건"]), sum(1 for s in 낸["사건"] if s.get("반영") is True), len(낸["확인불가"]), (낸.get("셈") or {}).get("호출", 0), p))
    for s in 낸["사건"]:
        print("  %s %-6s %-6s 현금 %18s · 주식 %14s · 반영 %-5s · %s · %s" % (
            s.get("날짜") or "?", s["종류"], s["역할"], _글수(s.get("현금")) if s.get("현금") is not None else "—",
            _글수(s.get("주식수")) if s.get("주식수") is not None else "—", s.get("반영"), s.get("접수번호"), (s.get("확인상태") or "")[:60]))
    print("  13번 — " + " · ".join("%s %s" % (k, _글수(v) if v is not None else "빈칸(확인 불가)") for k, v in sorted(합.items())))
    for x in 낸["확인불가"]:
        print("  확인 불가 %s — %s" % (x.get("접수번호"), (x.get("까닭") or "")[:150]))
    for x in 낸.get("사람이적는다") or []:
        print("  사람이 적는다 — %s" % x)
    for x in 낸["경보"]:
        print("  경보 — %s" % x)
    if 낸.get("한도초과"):
        print("  [멈춤] 일일 한도 초과(020) — %s · 남은 받기 %d" % (낸["한도초과"], len(낸.get("남은받기") or [])))
        return 발견
    return 발견 if 낸["확인불가"] else 통과


if __name__ == "__main__":
    sys.exit(main())

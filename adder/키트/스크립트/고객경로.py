# -*- coding: utf-8 -*-
"""고객경로 — 매출 구분의 경로를 「고객 수 × 고객당 매출」 로 세운다(1.1.6). 원가는 공시 단위(부문)로 그대로 둔다.

    python 스크립트/고객경로.py <가정.json>                 # 점검만 — 실적 열의 구분 매출 합 = 부문 매출 합(검증행) · 선언 대조
    python 스크립트/고객경로.py <가정.json> --쓰기          # 선언을 엔진 칸으로 옮기고 엔진을 돌려 스스로 대조한다
    python 스크립트/고객경로.py <가정.json> --쓰기 --걷기   # 옮기며 없어지는 줄(증가율 경로 · 합친 구분)을 가리키는 자리를 걷는다(걷은 자리를 적는다)
    python 스크립트/고객경로.py <가정.json> --쓰기 --원가 매출|고객   # 원가 · 인건비 · 투자가 판매량에 연동하면 — 매출에 잇거나(공시 단위) 고객 수를 따르게

**엔진에 새 경로를 박지 않는다** — 매출 구분의 수준 경로(판매량 × 판매단가 지수)가 이미 고객 수(판매량 — 저량 꼴: 기간 길이로 연환산하지 않는다) ×
고객당 매출(판매단가 지수)이다. 이 도구는 선언 블록(최상위 `고객경로` — 엔진은 읽지 않는다)을 그 칸으로 옮긴다(도착점짓기와 같은 꼴).
원가 줄은 연결 한 벌이라 매출 구분이 부문과 달라도 그대로다 — **원가는 공시 단위(부문)로 둔다**. 대신 매출 구분과 부문이 갈리므로
「구분 매출의 합 = 부문 매출의 합」 을 실적 열마다 검증행으로 잰다(차이 0 이어야 함 · 허용 0.5%).

선언 꼴(최상위 `고객경로` — 사업 단위 하나 · 목록이면 여럿)
  {"구분": s(1~5), "이름", "합칠구분"[번호 — 그 구분의 실적 매출을 s 에 더하고 구분을 걷는다(고객 수가 여러 부문에 걸쳐 한 줄로만 공시될 때)],
   "부문"[부문 멤버 — `_raw/부문매출.json` 「멤버」 · 원가 단위 · 검증행의 상대 · 비면 그 구분들의 `_부문멤버`],
   "기준기간"(직전회계연도 — 기본 · 그 해 12개월이 기준 기간),
   "고객수": {"명칭"(고객 수), "단위"(곳), "실적"{FY…A: 값}, "기말"{FY…A: 값 — 비면 실적}, "경로"{시나리오: {열: 값}}, "기말경로"(비면 경로), "출처", "근거"},
   "고객당매출": {"명칭"(고객당 매출), "변동률"{시나리오: {열: 전년 대비 — 첫 예측 열은 기준 기간 대비}}, "출처", "근거"},
   "순매출유지율": {"실적"{FY…A: 값}, "출처"}(선택 — 대조 줄), "잔여이행의무": {"실적"{기간 ID: 금액(금액 단위)}, "출처"}(선택 — 대조 줄),
   "근거"(경로를 고른 까닭)}
옮기는 칸 — 구조.매출구분[s](경로 수준 · 판매량꼴 저량 · 판매량산정 직접 · 판매량공시 예 · 단가경로 직접 · 단가입력 전년대비 · 기준기간 ·
  판매량명칭 · 판매량단위 · 판매단가명칭 · `_부문멤버` 합) · 가정 6s0 · 6s1(고객 수 — 기간 평균 · 기말) · 6s3(고객당 매출 변동률) · 표 6s7(지수 1 · 시점 0) ·
  원천 550+s · 555+s(고객 수 실적 · 기말) · 580+s · 586+s(기준 기간 매출 · 고객 수) · 594(기준 기간 개월 수 12) · 근거 6s0 · 6s1 · 6s3.
  걷는 칸 — 그 구분의 증가율 경로 줄(30 + 8(s−1) · 34 + 8(s−1)) · 합친 구분(구조 · 원천 85 + k · 증가율 줄). 그 줄을 가리키는 자리(시나리오이야기 driver ·
  민감도 손잡이 · 역산 축 · 반대 논거 · 관측.레짐 바꿈)가 있으면 멈추고 알린다 — `--걷기` 를 주면 걷고 걷은 자리를 적는다.
  원가 · 인건비 · 유지 투자가 판매량(물량 지수)에 연동하면(연동기준 판매량 · 물량단위원가 · 지표구분 · 인원 물량연동 · 판매량연동) 고객 수가 그 물량이 된다 —
  멈추고 알린다. `--원가 매출` 은 연동기준 판매량을 매출액으로 바꿔 원가를 공시 단위(매출)에 두고, `--원가 고객` 은 고객 수를 따르게 둔다(걷은 자리에 적는다).
산출 가정 곁 `_raw/고객경로.json` — 「고객경로/1」: 형식 · 만든날 · 가정해시 · 값을바꿈(쓰기 판만 true) · 구분[{번호, 이름, 부문, 검증[{열, 구분매출, 부문매출, 차이, 차이율}],
  실적[{열, 고객수, 고객당매출, 매출}], 예측[{열, 고객수, 고객당매출지수, 엔진매출, 셈매출, 차이}], 대조{순매출유지율 · 잔여이행의무}, 걷은자리[], 까닭}] · 신호[].
종료 코드 — 0 통과 · 1 발견(검증행 차이 · 엔진 대조 어긋남) · 2 입력오류(선언 깨짐 · 가리키는 자리 · 엔진 계산 실패).
회사 · 업종 이름은 이 도구에 없다.
"""
from __future__ import annotations

import argparse
import copy
import datetime
import hashlib
import io
import json
import os
import sys

여기 = os.path.dirname(os.path.abspath(__file__))
if 여기 not in sys.path:
    sys.path.insert(0, 여기)
from 종료코드 import 통과, 발견, 입력오류  # noqa: E402

형식 = "고객경로/1"
산출이름 = "고객경로.json"
허용 = 0.005                      # 검증행 차이율 허용(㉜ 부문 합과 같은 0.5%)
엔진허용 = 1e-6
시나리오들 = ("비관", "기준", "낙관")


class 선언오류(ValueError):
    pass


def _n(x):
    try:
        return None if x is None or isinstance(x, bool) else float(x)
    except (TypeError, ValueError):
        return None


def 선언들(가정):
    v = 가정.get("고객경로") if isinstance(가정, dict) else None
    if isinstance(v, dict):
        v = [v]
    return [x for x in (v or []) if isinstance(x, dict) and x.get("구분") is not None]


def 증가율줄(s):
    return ("%d" % (30 + 8 * (s - 1)), "%d" % (34 + 8 * (s - 1)))


def _FY(k):
    return isinstance(k, str) and k.startswith("FY") and k.endswith("A")


def 부문매출(자리, 배율):
    """`_raw/부문매출.json` → {멤버: {기간 ID: 금액(가정 금액 단위)}}. 없으면 {}."""
    p = os.path.join(자리 or "", "_raw", "부문매출.json")
    if not 자리 or not os.path.exists(p):
        return {}
    try:
        d = json.load(io.open(p, encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    낸 = {}
    for 멤, 칸 in (((d.get("값표") or {}).get("매출")) or {}).items():
        낸[멤] = {k: _n((x or {}).get("값")) / 배율 for k, x in (칸 or {}).items() if isinstance(x, dict) and _n(x.get("값")) is not None}
    return 낸


def _구분(가정, s):
    return next((x for x in (((가정.get("구조") or {}).get("매출구분")) or []) if isinstance(x, dict) and x.get("번호") == s), None)


def _멤버들(가정, 선, 합칠):
    부 = [("%s" % x) for x in (선.get("부문") or [])]
    if 부:
        return 부
    낸 = []
    for k in [int(선["구분"])] + 합칠:
        m = (_구분(가정, k) or {}).get("_부문멤버")
        낸 += ([m] if isinstance(m, str) else list(m or []))
    return list(dict.fromkeys(낸))


def 검증행(가정, 선, 자리, 원천=None):
    """실적 열마다 구분 매출(원천 85 + s, 합칠 구분 포함)과 부문 매출 합(같은 기간에 값이 있는 멤버 — 멤버 이름이 바뀐 판은 같은 부문의 다른 멤버가 채운다)."""
    배 = float(((가정.get("메타") or {}).get("환산배율")) or 1)
    s = int(선["구분"])
    합칠 = [int(k) for k in 선.get("합칠구분") or []]
    원 = 원천 if 원천 is not None else (가정.get("원천") or {})
    부 = 부문매출(자리, 배)
    멤 = _멤버들(가정, 선, 합칠)
    열들 = sorted({k for k in (원.get("%d" % (85 + s)) or {}) if isinstance(k, str) and k[-1:] == "A"})
    줄 = []
    for c in 열들:
        구 = sum(_n((원.get("%d" % (85 + k)) or {}).get(c)) or 0.0 for k in [s] + 합칠)
        값들 = [부[m][c] for m in 멤 if m in 부 and c in 부[m]]
        if not 값들:
            continue
        b = sum(값들)
        줄.append({"열": c, "구분매출": 구, "부문매출": b, "차이": 구 - b, "차이율": ((구 - b) / b) if b else None})
    return 줄, 멤


자료블록 = ("가정", "시점가정", "표", "원천", "근거", "원천근거", "고객경로", "메타", "기간", "스위치", "구조", "WACC", "WACC근거", "일정",
         "소비처", "행이름", "미사용")       # 소비처 · 행이름은 13번 원천 줄 번호로 키를 단다(가정 번호가 아니다)


def _번호(x):
    """가정 번호를 가리키는 글(「30」) — 수(30)는 자료 값일 수 있어 보지 않는다."""
    return x.strip() if isinstance(x, str) else None


def 가리키는자리(가정, 번들):
    """걷는 줄 번호들을 가리키는 자리 → [(자리 글, 값)] — 자료 블록(가정 · 원천 · 근거 …) 밖을 훑는다: 목록의 원소(driver · 딸린행 · 가정 목록) ·
    사전의 키(서사연결 · 방향선언 · 독자근거 …) · 「가정」 · 「대상」 칸(바꿈 · 손잡이 · 신호). 블록 이름을 코드에 박지 않는다(새 블록도 잡힌다)."""
    번들 = {("%s" % b) for b in 번들}
    낸 = []

    def 훑(x, 길):
        if isinstance(x, dict):
            for k, v in x.items():
                if _번호(k) in 번들:
                    낸.append(("%s.%s" % (길, k), k))
                    continue
                if k in ("가정", "대상") and _번호(v) in 번들:
                    낸.append(("%s.%s" % (길, k), v))
                    continue
                훑(v, "%s.%s" % (길, k))
        elif isinstance(x, list):
            for i, v in enumerate(x):
                if _번호(v) in 번들:
                    낸.append(("%s[%d]" % (길, i), v))
                else:
                    훑(v, "%s[%d]" % (길, i))
    for k, v in (가정 or {}).items():
        if k not in 자료블록 and not ("%s" % k).startswith("_"):
            훑(v, k)
    return 낸


def _걷기(가정, 번들):
    """가리키는 자리를 걷는다 — 목록의 원소는 빼고, 사전의 키는 지우고, 「가정」 · 「대상」 이 그 번호인 사전(바꿈 · 손잡이)은 그 목록에서 뺀다."""
    번들 = {("%s" % b) for b in 번들}

    def 걸림(v):
        if not isinstance(v, dict):
            return False
        대 = v.get("대상")
        대들 = 대 if isinstance(대, list) else [대]
        return _번호(v.get("가정")) in 번들 or any(_번호(d) in 번들 for d in 대들)

    def 걷(x):
        if isinstance(x, dict):
            for k in [k for k in x if _번호(k) in 번들]:
                x.pop(k)
            for k, v in list(x.items()):
                if k in ("가정",) and isinstance(v, list):
                    x[k] = [y for y in v if _번호(y) not in 번들]
                elif isinstance(v, dict) and 걸림(v) and k in ("축",):
                    x.pop(k)
                else:
                    걷(v)
        elif isinstance(x, list):
            x[:] = [y for y in x if _번호(y) not in 번들 and not 걸림(y)]
            for y in x:
                걷(y)
    for k, v in list((가정 or {}).items()):
        if k not in 자료블록 and not ("%s" % k).startswith("_"):
            걷(v)


def 물량연동자리(가정, 구분들):
    """원가 · 인건비 · 유지 투자가 매출 구분의 판매량(물량 지수)에 연동하는 자리 → [(자리, 고칠 수 있나 — 연동기준 판매량 → 매출액)].
    고객 수가 판매량이 되면 그 자리는 고객 수를 따른다 — 원가를 공시 단위 그대로 두려면 매출에 연동해야 한다."""
    구 = (가정.get("구조") or {})
    낸 = []
    for x in 구.get("원가줄") or []:
        if not isinstance(x, dict):
            continue
        k = x.get("번호")
        if x.get("연동기준") == "판매량":
            낸.append(("구조.원가줄[%s].연동기준 = 판매량" % k, True))
        if "물량단위원가" in (x.get("산식"), x.get("보조산식")):
            낸.append(("구조.원가줄[%s] 물량단위원가(전사 판매량 지수)" % k, False))
        if x.get("지표") == "구분" and int(x.get("지표구분") or 0) in 구분들:
            낸.append(("구조.원가줄[%s].지표구분 = %s" % (k, x.get("지표구분")), False))
    if ((구.get("인건비") or {}).get("인원경로")) == "물량연동":
        낸.append(("구조.인건비.인원경로 = 물량연동", False))
    if ((구.get("투자") or {}).get("유지규칙")) == "판매량연동":
        낸.append(("구조.투자.유지규칙 = 판매량연동", False))
    return 낸


def 옮기기(가정, 선, 걷기=False, 원가=None):
    """선언 하나를 엔진 칸으로 → (새 가정, 걷은 자리 목록). 선언이 깨졌거나 가리키는 자리가 남으면 선언오류.
    원가 — None(물량에 연동한 원가 자리가 있으면 멈춘다) · 「매출」(연동기준 판매량 → 매출액 · 그 밖의 물량 연동 자리는 멈춘다) ·
    「고객」(그 자리가 고객 수를 따르게 둔다 — 그렇게 정한 것을 산출에 적는다)."""
    g = copy.deepcopy(가정)
    s = int(선["구분"])
    if not 1 <= s <= 5:
        raise 선언오류("고객경로.구분 은 1 ~ 5(기타 6 은 수준 경로가 아니다) — %s" % s)
    x = _구분(g, s)
    if x is None:
        raise 선언오류("구조.매출구분 에 구분 %d 이 없다" % s)
    합칠 = [int(k) for k in 선.get("합칠구분") or []]
    for k in 합칠:
        if k == s or _구분(g, k) is None or k == 6:
            raise 선언오류("합칠구분 %s — 구조.매출구분 에 없거나 같은 구분 · 기타(6)다" % k)
    고 = 선.get("고객수") or {}
    단 = 선.get("고객당매출") or {}
    실 = {k: _n(v) for k, v in (고.get("실적") or {}).items() if _n(v) is not None}
    if not 실:
        raise 선언오류("고객수.실적 이 비었다(공시된 고객 수 — 회계연도 실적 열)")
    기준기간 = 선.get("기준기간") or "직전회계연도"
    if 기준기간 != "직전회계연도":
        raise 선언오류("기준기간 은 지금 「직전회계연도」 만 받는다(고객 수는 대개 회계연도 말 한 번 공시된다)")
    원 = g.setdefault("원천", {})
    FY들 = sorted(k for k in (원.get("62") or {}) if _FY(k))
    끝FY = FY들[-1] if FY들 else None
    if 끝FY not in 실:
        raise 선언오류("고객수.실적 에 직전 회계연도(%s) 값이 없다 — 기준 기간의 고객 수" % 끝FY)
    # 구분 매출 실적(합칠 구분 더함)
    열 = sorted({c for k in [s] + 합칠 for c in (원.get("%d" % (85 + k)) or {}) if isinstance(c, str)})
    새 = {}
    for c in 열:
        vs = [_n((원.get("%d" % (85 + k)) or {}).get(c)) for k in [s] + 합칠]
        if any(v is not None for v in vs):
            새[c] = sum(v or 0.0 for v in vs)
    if _n(새.get(끝FY)) is None:
        raise 선언오류("구분 %d 의 %s 매출 실적(원천 %d)이 없다 — 기준 기간 매출" % (s, 끝FY, 85 + s))
    걷 = [b for k in [s] + 합칠 for b in 증가율줄(k)] + ["%d" % (600 + 10 * k + d) for k in 합칠 for d in range(10)]
    자리 = 가리키는자리(g, 걷)
    if 자리 and not 걷기:
        raise 선언오류("옮기면 없어지는 줄(%s)을 가리키는 자리가 있다 — %s. 손으로 고치거나 --걷기 를 준다"
                     % (" · ".join(sorted(set(걷), key=int)), " · ".join("%s(%s)" % (a, b) for a, b in 자리)))
    if 자리:
        _걷기(g, 걷)
    물 = 물량연동자리(g, [s] + 합칠)
    if 물 and 원가 not in ("매출", "고객"):
        raise 선언오류("원가 · 인건비 · 투자가 판매량에 연동한다(%s) — 고객 수가 판매량이 되면 그 자리가 고객 수를 따른다. 원가를 공시 단위 그대로 두려면 "
                     "--원가 매출(연동기준 판매량 → 매출액), 고객 수를 따르게 두려면 --원가 고객" % " · ".join(a for a, _b in 물))
    if 원가 == "매출":
        못 = [a for a, ok in 물 if not ok]
        if 못:
            raise 선언오류("--원가 매출 로 바꿀 수 없는 물량 연동 자리가 있다(%s) — 손으로 고치거나 --원가 고객" % " · ".join(못))
        for x in ((g.get("구조") or {}).get("원가줄") or []):
            if isinstance(x, dict) and x.get("연동기준") == "판매량":
                x["연동기준"] = "매출액"
    자리 = list(자리) + [("원가 연동 — %s" % a, "매출액으로" if 원가 == "매출" else "고객 수를 따름") for a, _ok in 물]
    # 합칠 구분 걷기
    for k in 합칠:
        g["구조"]["매출구분"] = [y for y in g["구조"]["매출구분"] if not (isinstance(y, dict) and y.get("번호") == k)]
        원.pop("%d" % (85 + k), None)
        for n in (85 + k, 550 + k, 555 + k, 580 + k, 586 + k):                 # 합친 구분의 원천 근거(출처 칸이 남으면 15번이 빈 실적으로 센다)
            (g.get("원천근거") or {}).pop("%d" % n, None)
            if n != 85 + k:
                원.pop("%d" % n, None)
        for b in 증가율줄(k) + tuple("%d" % (600 + 10 * k + d) for d in range(10)):
            (g.get("가정") or {}).pop(b, None)
            (g.get("시점가정") or {}).pop(b, None)
            (g.get("근거") or {}).pop(b, None)
        (g.get("표") or {}).pop("%d" % (600 + 10 * k + 7), None)
    for b in 증가율줄(s):
        (g.get("가정") or {}).pop(b, None)
        (g.get("근거") or {}).pop(b, None)
    원["%d" % (85 + s)] = 새
    x = _구분(g, s)
    멤 = _멤버들(가정, 선, 합칠)
    for k in list(x.keys()):
        if k not in ("번호", "이름", "_부문멤버"):
            x.pop(k)
    x.update({"경로": "수준", "판매량명칭": 고.get("명칭") or "고객 수", "판매량단위": 고.get("단위") or "곳", "판매량꼴": "저량",
              "판매단가명칭": 단.get("명칭") or "고객당 매출", "판매량산정": "직접", "판매량공시": "예", "단가경로": "직접", "단가입력": "전년대비",
              "기준기간": 기준기간})
    if 선.get("이름"):
        x["이름"] = 선["이름"]
    if 멤:
        x["_부문멤버"] = 멤
    말 = {k: _n(v) for k, v in (고.get("기말") or 실).items() if _n(v) is not None}
    원["%d" % (550 + s)] = {k: v for k, v in 실.items()}
    원["%d" % (555 + s)] = {k: v for k, v in 말.items()}
    원["%d" % (580 + s)] = {"기준기간": 새[끝FY]}
    원["%d" % (586 + s)] = {"기준기간": 실[끝FY]}
    옛 = _n((원.get("594") or {}).get("기준기간"))
    if 옛 is not None and abs(옛 - 12) > 1e-9:
        raise 선언오류("원천 594(기준 기간 개월 수)가 이미 %s — 다른 수준 경로 구분과 기준 기간이 갈린다(한 값이다)" % 옛)
    원["594"] = {"기준기간": 12}
    A = g.setdefault("가정", {})
    b = 600 + 10 * s
    경, 말경, 변 = 고.get("경로") or {}, 고.get("기말경로") or 고.get("경로") or {}, 단.get("변동률") or {}
    for 시 in 시나리오들:
        if not isinstance(경.get(시), dict) or not isinstance(변.get(시), dict):
            raise 선언오류("고객수.경로 · 고객당매출.변동률 에 시나리오 「%s」 가 없다" % 시)
    A["%d" % b] = {시: {k: _n(v) for k, v in 경[시].items()} for 시 in 시나리오들}
    A["%d" % (b + 1)] = {시: {k: _n(v) for k, v in (말경.get(시) or 경[시]).items()} for 시 in 시나리오들}
    A["%d" % (b + 3)] = {시: {k: _n(v) for k, v in 변[시].items()} for 시 in 시나리오들}
    g.setdefault("표", {})["%d" % (b + 7)] = {"판매단가지수": 1.0, "판매량지수": 1.0, "시점": 0.0}
    기준일 = (g.get("메타") or {}).get("재무기준일") or (g.get("메타") or {}).get("평가기준일") or ""
    근 = g.setdefault("근거", {})
    근["%d" % b] = ["[판단] %s — 실적 %s(%s)" % (고.get("명칭") or "고객 수", " · ".join("%s %s" % (k[2:6], "{:,.0f}".format(v)) for k, v in sorted(실.items())),
                                          고.get("출처") or "출처 없음"), 기준일,
                   "고객 수 경로(고객경로.py --쓰기) — %s" % (고.get("근거") or 선.get("근거") or "근거 없음"), "확인완료" if 고.get("출처") else "확인필요"]
    근["%d" % (b + 1)] = ["[판단] %s 기말 — 기간 평균과 같은 경로(저량 꼴)" % (고.get("명칭") or "고객 수"), 기준일, "고객경로.py --쓰기", 근["%d" % b][3]]
    근["%d" % (b + 7)] = ["[판단] 기준 기간 지수 — 판매량 · 고객당 매출 지수 1(기준 기간 = %s)" % 끝FY, 기준일,
                         "고객경로.py --쓰기 — 기준 기간 매출 · 고객 수는 13번 %d · %d" % (580 + s, 586 + s), "확인완료"]
    근["%d" % (b + 3)] = ["[판단] %s 변동률(전년 대비) — %s" % (단.get("명칭") or "고객당 매출", 단.get("출처") or "출처 없음"), 기준일,
                         "고객당 매출 경로(고객경로.py --쓰기) — %s" % (단.get("근거") or 선.get("근거") or "근거 없음"), "확인완료" if 단.get("출처") else "확인필요"]
    원근 = g.setdefault("원천근거", {})
    출 = 고.get("출처") or "출처 없음"
    확 = "확인완료" if 고.get("출처") else "확인필요"
    매근 = (원근.get("%d" % (85 + s)) or [None])[0] or "구분 매출 실적"
    for 번, 글 in ((550 + s, "%s — %s(실적)" % (출, 고.get("명칭") or "고객 수")), (555 + s, "%s — %s 기말(실적)" % (출, 고.get("명칭") or "고객 수")),
                 (580 + s, "%s — 기준 기간 %s 매출(합친 구분 포함)" % (매근, 끝FY)), (586 + s, "%s — 기준 기간 %s %s" % (출, 끝FY, 고.get("명칭") or "고객 수")),
                 (594, "기준 기간 개월 수 — %s 12개월(고객경로.py --쓰기)" % 끝FY)):
        원근["%d" % 번] = [글, 기준일, 확, None]
    return g, [{"자리": a, "값": b_} for a, b_ in 자리]


def 엔진대조(가정, 선):
    """엔진 4번의 구분 매출(예측 열)이 「기준 매출 × 고객 수 ÷ 기준 고객 수 × 고객당 매출 지수 × 기간(년)」 과 같은가(도구가 따로 셈한다)."""
    from 엔진.계산 import 계산                               # noqa: PLC0415
    from 엔진.읽개 import 축내기                              # noqa: PLC0415
    s = int(선["구분"])
    b = 600 + 10 * s
    금액줄 = ("13", "21", "27", "33", "39")[s - 1]
    축 = 축내기(가정)
    원 = 가정.get("원천") or {}
    기매, 기고 = _n((원.get("%d" % (580 + s)) or {}).get("기준기간")), _n((원.get("%d" % (586 + s)) or {}).get("기준기간"))
    낸 = []
    for 시 in 시나리오들:
        R = 계산(가정, 시)
        Q = ((가정.get("가정") or {}).get("%d" % b) or {}).get(시) or {}
        u = ((가정.get("가정") or {}).get("%d" % (b + 3)) or {}).get(시) or {}
        P = 1.0
        for i in 축.예측:
            c = 축.ID[i]
            P *= 1 + (_n(u.get(c)) or 0.0)
            년 = 축.열[i].년 or 1.0
            셈 = 기매 * (_n(Q.get(c)) or 0.0) / 기고 * P * 년 if (기매 and 기고) else None
            엔 = _n((R["4.Sales"].get(금액줄) or {}).get(c))
            낸.append({"시나리오": 시, "열": c, "고객수": _n(Q.get(c)), "고객당매출지수": P, "엔진매출": 엔, "셈매출": 셈,
                      "차이": (엔 - 셈) if (엔 is not None and 셈 is not None) else None})
    return 낸


def 대조줄(가정, 선):
    """순매출유지율 · 잔여이행의무(선언에 있을 때만) — 실적의 고객당 매출 증가율 · 다음 해 매출과 나란히(값을 바꾸지 않는다)."""
    s = int(선["구분"])
    원 = 가정.get("원천") or {}
    매 = {}
    for k in [s] + [int(x) for x in 선.get("합칠구분") or []]:        # 옮기기 전이면 합칠 구분의 실적을 더한다(옮긴 뒤에는 그 원천이 없다)
        for c, v in (원.get("%d" % (85 + k)) or {}).items():
            if _FY(c) and _n(v) is not None:
                매[c] = (매.get(c) or 0.0) + _n(v)
    고 = {k: _n(v) for k, v in ((선.get("고객수") or {}).get("실적") or {}).items() if _n(v) is not None}
    낸 = {}
    단가 = {k: 매[k] / 고[k] for k in 매 if 고.get(k)}
    해 = sorted(단가)
    낸["고객당매출"] = [{"열": k, "고객수": 고[k], "매출": 매[k], "고객당매출": 단가[k],
                     "증가율": (단가[k] / 단가[해[j - 1]] - 1) if j else None} for j, k in enumerate(해)]
    n = (선.get("순매출유지율") or {}).get("실적") or {}
    if n:
        낸["순매출유지율"] = [{"열": k, "값": _n(v)} for k, v in sorted(n.items()) if _n(v) is not None]
        낸["순매출유지율출처"] = (선.get("순매출유지율") or {}).get("출처")
    r = (선.get("잔여이행의무") or {}).get("실적") or {}
    if r:
        낸["잔여이행의무"] = [{"열": k, "값": _n(v)} for k, v in sorted(r.items()) if _n(v) is not None]
        낸["잔여이행의무출처"] = (선.get("잔여이행의무") or {}).get("출처")
    return 낸


def 셈(가정, 자리, 쓴판=False):
    낸 = {"형식": 형식, "만든날": datetime.date.today().isoformat(), "평가기준일": (가정.get("메타") or {}).get("평가기준일"),
         "값을바꿈": bool(쓴판), "구분": [], "신호": []}
    for 선 in 선언들(가정):
        s = int(선["구분"])
        줄, 멤 = 검증행(가정, 선, 자리)
        한 = {"번호": s, "이름": 선.get("이름") or (_구분(가정, s) or {}).get("이름"), "부문": 멤, "검증": 줄, "대조": 대조줄(가정, 선)}
        x = _구분(가정, s) or {}
        한["옮김"] = x.get("경로") == "수준" and x.get("판매량꼴") == "저량"
        if 한["옮김"]:
            try:
                한["예측"] = 엔진대조(가정, 선)
            except Exception as e:                           # noqa: BLE001
                한["까닭"] = "엔진 대조 실패 — %s" % e
        밖 = [r for r in 줄 if r["차이율"] is not None and abs(r["차이율"]) > 허용]
        if 밖:
            낸["신호"].append({"출처": "고객경로", "종류": "구분 매출 ≠ 부문 매출", "대상": "구분 %d" % s, "값": 밖[0]["차이율"], "등급": "경보",
                             "글": "구분 %d 매출 합이 부문(%s) 매출 합과 %s 열에서 %.2f%% 갈린다 — 검증행 차이 0 이어야 함" % (
                                 s, " · ".join(멤) or "멤버 없음", 밖[0]["열"], 100 * 밖[0]["차이율"])})
        if not 멤 or not 줄:
            낸["신호"].append({"출처": "고객경로", "종류": "부문 대조 재료 없음", "대상": "구분 %d" % s, "값": None, "등급": "참고",
                             "글": "부문 멤버(고객경로.부문 · _부문멤버)나 `_raw/부문매출.json` 이 없어 검증행을 세우지 못했다"})
        어 = [r for r in 한.get("예측") or [] if r["차이"] is None or abs(r["차이"]) > 엔진허용 * max(1.0, abs(r["셈매출"] or 0))]
        if 어:
            낸["신호"].append({"출처": "고객경로", "종류": "엔진 대조 어긋남", "대상": "구분 %d" % s, "값": len(어), "등급": "경보",
                             "글": "엔진 매출이 고객 수 × 고객당 매출과 %d개 열에서 다르다" % len(어)})
        낸["구분"].append(한)
    if not 낸["구분"]:
        낸["해당없음"] = "최상위 `고객경로` 선언이 없다"
    return 낸


def _가정해시(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def 화면(낸):
    if 낸.get("해당없음"):
        return "고객경로 — 해당 없음: %s" % 낸["해당없음"]
    줄 = []
    for h in 낸["구분"]:
        줄.append("구분 %s %s — 부문 %s · %s" % (h["번호"], h.get("이름") or "", " · ".join(h.get("부문") or []) or "없음",
                                           "수준 경로(고객 수 × 고객당 매출)로 옮겼다" if h.get("옮김") else "아직 옮기지 않았다(--쓰기)"))
        for r in h.get("검증") or []:
            줄.append("  검증 %-7s 구분 매출 %14s · 부문 매출 %14s · 차이 %12s (0 이어야 함)" % (
                r["열"], "{:,.3f}".format(r["구분매출"]), "{:,.3f}".format(r["부문매출"]), "{:,.6f}".format(r["차이"])))
        for r in (h.get("대조") or {}).get("고객당매출") or []:
            줄.append("  실적 %-7s 고객 수 %s · 고객당 매출 %.6g%s" % (r["열"], "{:,.0f}".format(r["고객수"]), r["고객당매출"],
                                                         (" (%+.1f%%)" % (100 * r["증가율"])) if r.get("증가율") is not None else ""))
        if h.get("예측"):
            어 = [r for r in h["예측"] if r["차이"] is None or abs(r["차이"]) > 엔진허용 * max(1.0, abs(r["셈매출"] or 0))]
            줄.append("  엔진 대조 — %d열 · 어긋남 %d" % (len(h["예측"]), len(어)))
        if h.get("까닭"):
            줄.append("  ! %s" % h["까닭"])
    for x in 낸.get("신호") or []:
        줄.append("  [%s] %s" % (x["등급"], x["글"]))
    return "\n".join(줄)


def main(argv=None):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:                                        # noqa: BLE001
        pass
    ap = argparse.ArgumentParser(description="고객 수 × 고객당 매출 경로 — 선언을 엔진 칸으로 옮기고 구분 매출 = 부문 매출을 잰다")
    ap.add_argument("가정")
    ap.add_argument("--쓰기", action="store_true")
    ap.add_argument("--걷기", action="store_true")
    ap.add_argument("--원가", choices=("매출", "고객"), help="원가 · 인건비 · 투자가 판매량에 연동할 때 — 매출(연동기준 매출액으로) · 고객(고객 수를 따르게)")
    ap.add_argument("--낼")
    a = ap.parse_args(argv)
    자리 = os.path.dirname(os.path.abspath(a.가정))
    try:
        가정 = json.load(io.open(a.가정, encoding="utf-8"))
        걷은 = []
        if a.쓰기:
            선들 = 선언들(가정)
            if not 선들:
                raise 선언오류("최상위 `고객경로` 선언이 없다")
            g = 가정
            for 선 in 선들:
                if _구분(g, int(선["구분"])) and _구분(g, int(선["구분"])).get("경로") == "수준" and _구분(g, int(선["구분"])).get("판매량꼴") == "저량":
                    continue                                 # 이미 옮긴 구분(두 번 돌려도 같은 파일)
                g, w = 옮기기(g, 선, a.걷기, a.원가)
                걷은 += w
            from 엔진.계산 import 계산                       # noqa: PLC0415
            for 시 in 시나리오들:
                계산(g, 시)                                  # 엔진이 받는 꼴인지 먼저 본다
            with io.open(a.가정, "w", encoding="utf-8", newline="\n") as f:
                json.dump(g, f, ensure_ascii=False, indent=1)
            가정 = g
            print("고객경로 — 엔진 칸으로 옮겼다 → %s%s" % (a.가정, (" · 걷은 자리 %d" % len(걷은)) if 걷은 else ""))
        낸 = 셈(가정, 자리, a.쓰기)
        if 걷은:
            낸["걷은자리"] = 걷은
    except 선언오류 as e:
        print("입력오류 — %s" % e)
        return 입력오류
    except (OSError, ValueError, KeyError) as e:
        print("입력오류 — %s: %s" % (type(e).__name__, e))
        return 입력오류
    낸["가정해시"] = _가정해시(a.가정)
    p = a.낼 or os.path.join(자리, "_raw", 산출이름)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with io.open(p, "w", encoding="utf-8", newline="\n") as f:
        json.dump(낸, f, ensure_ascii=False, indent=1)
    print(화면(낸))
    print("→ %s" % p)
    return 발견 if any(x["등급"] == "경보" for x in 낸["신호"]) else 통과


if __name__ == "__main__":
    sys.exit(main())

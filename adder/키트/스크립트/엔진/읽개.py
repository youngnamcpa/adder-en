# -*- coding: utf-8 -*-
"""엔진/읽개 — 가정 파일의 값을 읽는 한 곳. 시트 함수는 가정 사전을 직접 뒤지지 않고 읽개로 읽는다.

  읽 = 읽개(가정, 시나리오, 축)
  읽.A(30)          12번 열별 가정의 적용값 — 축 순서의 목록(실적 열은 None). `{"공통": …}` 이면 세 시나리오가 그 한 벌을 읽는다
  읽.S(212)         12번 한 값 가정 — `{비관, 기준, 낙관}` 이면 그 시나리오의 값, 값 하나면 그 값(공통). 없으면 None
  읽.T(617)         12번 표 구획의 줄 — {칸: 값}. 시나리오 겹(`{비관: {칸: 값}, …}` · `{"공통": {…}}`)이 있으면 그 시나리오의 것
  읽.H(62)          13번 원천 — 축 순서의 목록(예측 열은 None).  읽.H(62, 열) 은 그 칸,  읽.H기준일(97) 은 평가기준일 열
  읽.W(구간)        `WACC.<구간>` 사전

없는 값은 None 이다(「해당 없음」). 산술 자리에서만 `_n()` 이 0 으로 읽는다 — 숫자를 지어내지 않는다.
"""

import os as _os
import sys as _sys

_위 = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
if _위 not in _sys.path:
    _sys.path.insert(0, _위)
from 기간축 import 기간축, 기간축오류  # noqa: E402

from .공통 import 가정오류, 공통키, 시나리오목록, _n, _빈칸  # noqa: E402


def 축내기(가정):
    """가정의 기간 축. 못 지으면 가정오류."""
    try:
        return 기간축(가정)
    except 기간축오류 as e:
        raise 가정오류("%s" % e)


def _펴기(v, 축):
    """{기간 ID: 값} → 축 순서의 목록. 이 축에 없는 ID 는 버린다(검증이 이미 오류로 알린 자리다)."""
    out = [None] * 축.n
    if isinstance(v, dict):
        for k, x in v.items():
            if k in 축.ID:
                out[축.ID.index(k)] = x
    return out


def _벌(g, 시나리오):
    """`{비관, 기준, 낙관}` 이나 `{"공통": …}` 에서 그 시나리오가 읽을 한 벌."""
    if not isinstance(g, dict):
        return None
    if 시나리오 in g:
        return g.get(시나리오)
    return g.get(공통키)


def _행(가정, 번호, 시나리오, 축):
    """12번 가정의 「적용값」 = INDEX(세 줄, 시나리오번호). 축 순서의 목록을 낸다(실적 열은 None)."""
    v = _펴기(_벌(가정.get("가정", {}).get(str(번호)), 시나리오), 축)
    for i in 축.실적:
        v[i] = None
    return v


def _시점(가정, 번호, 시나리오):
    """12번 한 값 가정. `{비관, 기준, 낙관}` · `{"공통": 값}` · 값 하나(공통)를 받는다."""
    g = 가정.get("시점가정", {}).get(str(번호))
    if g is None:
        return None
    if isinstance(g, dict):
        return _벌(g, 시나리오)
    return g


def _표(가정, 번호, 시나리오):
    """12번 표 구획의 줄 → {칸: 값} 또는 None. 시나리오 겹이 있으면 그 시나리오의 것을 낸다."""
    g = (가정.get("표") or {}).get(str(번호))
    if not isinstance(g, dict):
        return None
    if any(k in g for k in 시나리오목록) or 공통키 in g:
        g = _벌(g, 시나리오)
    return g if isinstance(g, dict) else None


def _원천(가정, 번호, 축, 열=None):
    """13번 원천의 실적 열 값. 열(자리)을 주면 그 칸, 안 주면 축 순서의 목록(예측 열은 None)."""
    v = _펴기(가정.get("원천", {}).get(str(번호)), 축)
    for i in range(축.n):
        if i not in 축.실적:
            v[i] = None
    return v[열] if 열 is not None else v


def _기준일값(가정, 번호, 축):
    """13번의 평가기준일 열(마지막 실적 열) — 브리지·WACC가 쓰는 자리."""
    return _원천(가정, 번호, 축, 축.기준일)


# ── 날짜 둘(2026-10-25 결정 · 계약 `연구/평가기준일_날짜둘_20261025/01_계약.md` 0절 4) ─────────────────────────
# 재무기준일 F(열이 서는 날) ≠ 평가기준일 T 인 판(이월 판)에서 엔진은 F 에서 셈한 주주가치를 T 로 이월하고 (F, T] 사이 자본거래를
# 더하고 뺀다. 그 거래는 13번 131~135 의 기준일 열(재무기준일 열 — 95 · 96 · 99 와 같은 칸) 한 칸에 적는다(빈칸 = 0).
이월원천 = (("유입", 131), ("취득", 132), ("배당", 133), ("증가", 134), ("감소", 135))
이월원천번호 = tuple(n for _k, n in 이월원천)


def 이월판(축):
    """재무기준일 ≠ 평가기준일인가(이월 연수 > 0). 생성기의 조건식 `기간.이월` 과 같은 판정이다."""
    return (getattr(축, "이월연수", 0.0) or 0.0) > 0


def 사이자본거래(가정, 축):
    """13번 131~135 의 기준일 열 → {유입 · 취득 · 배당 · 증가 · 감소}(빈칸은 0 — 워크북 수식의 빈칸처럼). 금액은 워크북 금액 단위 · 주식수는 주."""
    return {k: _n(_기준일값(가정, n, 축)) for k, n in 이월원천}


class 읽개(object):
    """한 시나리오에서 가정 파일을 읽는 손잡이. 가정을 고치지 않는다."""

    def __init__(self, 가정, 시나리오, 축=None):
        self.가정 = 가정
        self.시나리오 = 시나리오
        self.축 = 축 or 축내기(가정)

    def A(self, 번호):
        return _행(self.가정, 번호, self.시나리오, self.축)

    def A있나(self, 번호):
        return str(번호) in (self.가정.get("가정") or {})

    def S(self, 번호):
        return _시점(self.가정, 번호, self.시나리오)

    def S있나(self, 번호):
        return str(번호) in (self.가정.get("시점가정") or {})

    def T(self, 번호):
        return _표(self.가정, 번호, self.시나리오)

    def H(self, 번호, 열=None):
        return _원천(self.가정, 번호, self.축, 열)

    def H기준일(self, 번호):
        return _기준일값(self.가정, 번호, self.축)

    def W(self, 구간):
        return (self.가정.get("WACC") or {}).get(구간) or {}

    def 메타(self, 키, 기본=None):
        return (self.가정.get("메타") or {}).get(키, 기본)

    def 스위치(self, 키, 기본=None):
        return (self.가정.get("스위치") or {}).get(키, 기본)

    def 관측(self, 키):
        return (self.가정.get("관측") or {}).get(키)

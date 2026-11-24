# -*- coding: utf-8 -*-
"""엔진/공통 — 시트 함수들이 함께 쓰는 보조(빈칸 · 나눗셈 · 줄 묶음 · 열 틀). 산식은 여기 두지 않는다."""

시나리오목록 = ["비관", "기준", "낙관"]
공통키 = "공통"                      # 가정 · 시점가정 · 표에서 세 시나리오가 같은 값 한 벌을 적는 키
스키마버전 = "v13"


class 가정오류(Exception):
    """가정 JSON이 엔진을 돌릴 모양이 아니다 — 맨 KeyError 대신 이것을 낸다."""


def _n(v):
    """수식 안에서 쓰이는 값 — None·문자열은 0으로 읽는다 (엑셀 SUMPRODUCT·SUM 규약)."""
    if v is None:
        return 0.0
    if isinstance(v, str):
        return 0.0
    return float(v)


def _빈칸(v):
    return v is None or (isinstance(v, str) and v.strip() == "")


def _나눔(a, b):
    """IFERROR(a/b, 0)"""
    a, b = _n(a), _n(b)
    if b == 0:
        return 0.0
    try:
        return a / b
    except Exception:
        return 0.0


class 줄묶음(dict):
    """한 시트 함수가 내는 것 — {번호 문자열: 축 순서의 목록(열 줄) 또는 한 값(한 값 줄)}.

    번호는 워크북 계산 줄의 번호이고 결과의 키다(`R["4.Sales"]["54"]`). 다른 시트 함수는 이 번호로 읽는다(`매["54"]`).
    `덤` 은 줄이 아닌 값이다(요약에 실을 값 · 다른 시트 함수가 읽는 중간 값) — 결과의 시트에는 실리지 않는다."""

    def __init__(self, *a, **k):
        dict.__init__(self, *a, **k)
        self.덤 = {}


class 열틀(object):
    """기간 축에서 뽑은 열의 자리와, 시트 함수가 줄을 지을 때 쓰는 작은 도구. 축 하나에 하나를 만들어 시트 함수에 넘긴다."""

    def __init__(self, 축):
        self.축 = 축
        self.n = 축.n
        self.년 = 축.줄("년")                             # 기간(년) = 개월 ÷ 12
        self.실적열, self.예측열, self.영구열 = 축.실적, 축.예측, 축.영구
        self.FY실적 = 축.FY실적
        self.FY끝, self.누계열, self.잔여열 = 축.FY실적[-1], 축.누계, 축.잔여
        self.첫예측, self.끝예측 = 축.첫예측, 축.끝예측
        self.예측영구 = 축.예측 + [축.영구]
        self.전체열 = list(range(축.n))
        self.수렴 = 축.수렴
        self.기준일 = 축.기준일

    def 빈열(self):
        return [None] * self.n

    def 예측만(self, f):
        """예측 열과 영구기간 열에만 f(i) 를 놓은 목록(실적 열은 None)."""
        v = self.빈열()
        for i in self.예측영구:
            v[i] = f(i)
        return v

    def 앞열(self, i):
        """연 단위 사슬에서 i 열의 앞 열 — 영구기간 열은 최종 예측 열, 그 밖은 바로 앞 열."""
        return self.끝예측 if i == self.영구열 else i - 1

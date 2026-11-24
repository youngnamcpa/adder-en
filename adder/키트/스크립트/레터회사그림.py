# -*- coding: utf-8 -*-
"""레터회사그림 — 레터 v27 7단계(다): 이 회사의 구조 · 쟁점 · 대조가 고르는 그림과, 본편 그림을 고르는 조건.

그림 블록(마크다운 — 표지 · 굵은 제목 · 설명 · 출처 · 표. 표의 숫자는 모두 장부 자리표시이고 그리기는 `레터그림` 의 범용 막대 · 선이다)
  남은기간  매출 절 — 첫 예측 기간이 한 해 미만이면 회계연도 매출 막대(그해는 누계 실적 위에 남은 기간 추정을 쌓는다)
  원가두선  영업비용 절 — 판매량을 따르는 매출원가 줄(물량단위원가 · 판매량 연동)이 있고 판매량 · 판매단가를 따로 세운 매출 구분이 있으면
            매출과 매출원가의 두 선(첫 해 = 100 — 두 선의 간격에 판매단가 변동이 드러난다)
  저량      매출 절 — 판매량을 저량 굴림으로 세운 구분마다 유입 · 유출 막대와 기말 저량 선(수주잔고 · 계약 잔액 · 가입자 · 점포)
  결손금    법인세 절 — 예측기간에 이월결손금을 쓰면 해마다 사용액 막대(잔액을 굴리는 판이면 잔액 선)
  범위      3분 레터 결론 — 세 시나리오의 주당가치와 평가기준일 종가(어느 회사에나 넣는 그림)

조건(`레터그림배치.옮기기` 가 `정합설정.json` 「그림.조건」 으로 부른다 — 거짓이면 그 그림은 본편에서 부록으로, 모르면 그대로)
  부록        늘 거짓(세 단계 그림 · 결론에 합쳐진 흐름 그림)
  블록밖      그림이 선 절의 추정 블록 대조 판정에 「밖」 이 있다(실적 범위 · 회사 말 · 바깥 상한 · 안쪽 정합)
  지렛대      주당가치를 가장 크게 좌우하는 가정이 그 절의 가정이다
  영구비중>x  Terminal Value 의 현재가치가 영업가치의 x 를 넘는다
  종가밖      평가기준일 종가가 세 시나리오 주당가치의 범위 밖이다
  수준구분>=n 판매량 · 판매단가를 따로 세운 매출 구분이 n 개 이상이다
회사 · 업종 이름은 이 모듈에 없다.
"""
from __future__ import annotations

import re


def _B():
    import 레터본문 as B                                      # noqa: PLC0415 — 레터본문이 이 모듈을 부른다(늦게 부른다)
    return B


def _n(x):
    try:
        return None if x is None or isinstance(x, bool) else float(x)
    except (TypeError, ValueError):
        return None


def _해(맥, c):
    try:
        return float(맥.년(c) or 0.0)
    except Exception:                                         # noqa: BLE001
        return 0.0


def _온해(맥, c):
    return _해(맥, c) >= 0.999


def _해이름(맥, c):
    """열 → 회계연도 이름(「2027년 하반기」 → 「2027년」)."""
    t = "%s" % 맥.열말(c)
    return re.sub(r"\s*(상반기|하반기|\d\s*분기|\d+\s*개월|\d+월).*$", "", t).strip() or t


# ══════════════════════════════════════════════════════════════════ 남은기간 — 첫 예측 기간이 한 해 미만
def 반기첫열(맥):
    """(누계 실적 열, 남은 기간 열) — 첫 예측 열이 한 해 미만이고 바로 앞 실적 열도 한 해 미만(같은 회계연도의 누계)일 때. 아니면 None."""
    예, 실 = list(맥.예측열 or []), list(맥.실적열 or [])
    if not 예 or not 실:
        return None
    남, 누 = 예[0], 실[-1]
    if _온해(맥, 남) or _온해(맥, 누) or _해(맥, 남) <= 0 or _해(맥, 누) <= 0:
        return None
    return 누, 남


def _당해머리(맥, 남):
    """누계 실적 + 남은 기간 추정을 합친 회계연도의 열 머리 — 다른 열 머리(「2027(추정)」)와 같은 꼴로 「2027(실적 + 추정)」."""
    return "%s(실적 + 추정)" % re.sub(r"년$", "", _해이름(맥, 남))


def 남은기간그림(맥, 실해수=3, 예해수=4):
    r = 반기첫열(맥)
    if not r:
        return []
    B = _B()
    누, 남 = r
    K = "R:기준:4.Sales:54:%s"
    if _n(맥.값(K % 누)) is None or _n(맥.값(K % 남)) is None:
        return []
    실해 = [c for c in 맥.실적열 if c != 누 and _온해(맥, c) and _n(맥.값(K % c)) is not None][-실해수:]
    예해 = [c for c in 맥.예측열[1:] if _온해(맥, c) and _n(맥.값(K % c)) is not None][:예해수]
    당해 = _당해머리(맥, 남)
    with B._키기록(맥) as 키들:
        실줄 = ["누계 실적"] + [맥.수(K % c, "어림금액") for c in 실해] + [맥.수(K % 누, "어림금액")] + ["—" for _c in 예해]
        추줄 = ["남은 기간 추정"] + ["—" for _c in 실해] + [맥.수(K % 남, "어림금액")] + [맥.수(K % c, "어림금액") for c in 예해]
    실줄[0], 추줄[0] = "실적", "추정"
    머 = ["그림의 값"] + [맥.표기(c) for c in 실해] + [당해] + [맥.표기(c) for c in 예해]
    설 = ("막대는 회계연도 매출입니다. %s 막대는 %s 누계 실적 위에 %s 추정을 쌓았습니다. 남은 기간의 추정이 누계 실적에 비해 큰지 작은지가 그해 매출을 좌우합니다."
         % (_해이름(맥, 남), 맥.열말(누), 맥.열말(남)))
    return B._그림블록(맥, "남은기간", "회계연도 매출과 첫 예측 기간의 남은 기간 추정(기준 시나리오)", 설, 머, [실줄, 추줄], 키들=키들)


# ══════════════════════════════════════════════════════════════════ 원가두선 — 매출과 물량을 따르는 매출원가
def 물량연동원가인가(구):
    """매출원가(시트 5)에 판매량을 따르는 줄(산식 · 보조산식 물량단위원가 · 연동기준 판매량)이 있고, 판매량 · 판매단가를 따로 세운 매출 구분(수준 경로)이 있나."""
    구 = 구 or {}
    줄 = [x for x in 구.get("원가줄") or [] if isinstance(x, dict) and x.get("시트") == 5]
    물 = any(x.get("산식") == "물량단위원가" or x.get("보조산식") == "물량단위원가" or x.get("연동기준") == "판매량" for x in 줄)
    수 = any(isinstance(x, dict) and x.get("경로") == "수준" for x in 구.get("매출구분") or [])
    return 물 and 수


def 원가두선그림(맥, 실해수=2):
    if not 물량연동원가인가(맥.구):
        return []
    B = _B()
    S, C = "R:기준:4.Sales:54:%s", "R:기준:5.COGS:17:%s"
    반 = 반기첫열(맥)                                          # 첫 예측 기간이 한 해 미만이면 누계 실적 + 남은 기간을 그 회계연도 한 칸으로(해 간격이 고르게)
    열 = [(c,) for c in 맥.실적열 if _온해(맥, c)][-실해수:] + ([반] if 반 else []) + [(c,) for c in 맥.예측열 if _온해(맥, c)]

    def 다(K, cs):
        return K % cs[0] if len(cs) == 1 else ["합"] + [K % c for c in cs]

    def 값(K, cs):
        vs = [_n(맥.값(K % c)) for c in cs]
        return None if any(v is None for v in vs) else sum(vs)
    열 = [cs for cs in 열 if 값(S, cs) and 값(C, cs)]
    if len(열) < 3 or len(열[0]) != 1:
        return []
    밑 = 열[0]
    밑말 = 맥.열말(밑[0])

    def 지수(K, cs):
        return ["×", ["÷", 다(K, cs), 다(K, 밑)], "상:100"]
    판 = "매출과 매출원가(%s = 100)" % 밑말
    with B._키기록(맥) as 키들:
        줄들 = [["%s · 매출" % 판] + [맥.식(지수(S, cs), "수0") for cs in 열],
              ["%s · 매출원가" % 판] + [맥.식(지수(C, cs), "수0") for cs in 열]]
    import 레터1부 as _P                                     # noqa: PLC0415 — 조사(을 · 를)
    설 = ("두 선은 %s 100으로 둔 매출과 매출원가입니다. 매출은 판매량과 판매단가를 따르고, 매출원가의 큰 줄은 판매량을 따르므로 "
         "두 선의 간격에 판매단가 변동이 드러납니다." % _P.을(밑말))
    머 = ["그림의 값"] + [(맥.표기(cs[0]) if len(cs) == 1 else _당해머리(맥, cs[-1])) for cs in 열]
    return B._그림블록(맥, "원가두선", "매출과 매출원가의 경로(기준 시나리오, %s = 100)" % 밑말, 설, 머, 줄들, 키들=키들)


# ══════════════════════════════════════════════════════════════════ 저량 — 유입 · 유출 · 기말 저량
def 저량구분들(구):
    return [x for x in (구 or {}).get("매출구분") or [] if isinstance(x, dict) and x.get("경로") == "수준" and x.get("판매량산정") == "저량"
            and isinstance(x.get("번호"), int) and 1 <= x["번호"] <= 5]


def 저량그림(맥):
    B = _B()
    L = []
    S = 맥.기.get("4.Sales") or {}
    for x in 저량구분들(맥.구):
        s = x["번호"]
        말행, 출행 = "1%d0" % s, "1%d4" % s
        if not S.get(말행):
            continue
        열 = [c for c in 맥.실적열 + 맥.예측열 if _n((S.get(말행) or {}).get(c)) is not None]
        예 = [c for c in 열 if c in 맥.예측열]
        if len(예) < 2:
            continue
        잔고 = x.get("판매량꼴") != "저량"
        이름 = "%s" % (x.get("이름") or "구분 %d" % s)
        단 = "%s" % (x.get("판매량단위") or "")
        유입말, 유출말, 기말말 = (("신규 유입(수주)", "소진(매출로 인식)", "기말 잔고") if 잔고 else ("유입", "유출", "기말 저량"))
        K말, K출 = "R:기준:4.Sales:%s:%s" % (말행, "%s"), "R:기준:4.Sales:%s:%s" % (출행, "%s")
        with B._키기록(맥) as 키들:
            입줄 = [유입말] + [(맥.수("A:%d:기준:%s" % (570 + s, c), "수1") if c in 예 else
                             (맥.식(["÷", "H:%d:%s" % (605 + s, c), 맥.년(c)], "수1") if _n(맥.값("H:%d:%s" % (605 + s, c))) is not None else "—"))
                            for c in 열]
            출줄 = [유출말] + [(맥.식(["음", K출 % c], "수1") if _n((S.get(출행) or {}).get(c)) is not None else "—") for c in 열]
            말줄 = ["%s (선)" % 기말말] + [맥.수(K말 % c, "수1") for c in 열]
        설 = ("막대는 해마다의 %s(위)과 %s(아래, 연간 기준)이고 선은 %s입니다. 기말 %s = 기초 + %s − %s입니다%s."
              % (유입말, 유출말, 기말말, "잔고" if 잔고 else "저량", 유입말.split("(")[0], 유출말.split("(")[0],
                 " — 소진이 그해 매출의 판매량입니다" if 잔고 else ""))
        제 = "%s의 %s 굴림(기준 시나리오%s)" % (이름, "잔고" if 잔고 else "저량", (", " + 단) if 단 else "")
        L += B._그림블록(맥, "저량", 제, 설, ["그림의 값"] + [맥.표기(c) for c in 열], [입줄, 출줄, 말줄], 키들=키들)
    return L


# ══════════════════════════════════════════════════════════════════ 결손금 — 이월결손금 사용 일정
def 결손금그림(맥):
    B = _B()
    T = 맥.기.get("10.Tax") or {}
    예 = [c for c in 맥.예측열]
    사용 = [c for c in 예 if abs(_n((T.get("35") or {}).get(c)) or 0.0) > 0]
    공제 = [c for c in 예 if abs(_n(맥.값("A:204:기준:%s" % c)) or 0.0) > 0]
    if not 사용 and not 공제:
        return []
    with B._키기록(맥) as 키들:
        줄들 = []
        if 사용:
            줄들.append(["이월결손금 사용액"] + [맥.수("R:기준:10.Tax:35:%s" % c, "어림금액") if c in 사용 else "—" for c in 예])
        elif 공제:
            줄들.append(["이월결손금 공제"] + [맥.수("A:204:기준:%s" % c, "어림금액") if c in 공제 else "—" for c in 예])
        if any(abs(_n((T.get("36") or {}).get(c)) or 0.0) > 0 for c in 예):
            줄들.append(["이월결손금 잔액 (선)"] + [맥.수("R:기준:10.Tax:36:%s" % c, "어림금액") if _n((T.get("36") or {}).get(c)) is not None else "—"
                                              for c in 예])
    설 = "막대는 해마다 과세표준에서 공제한 이월결손금이고, 선이 있으면 그해 말 남은 잔액입니다. 결손금을 다 쓴 해부터 법인세가 온전히 붙습니다."
    return B._그림블록(맥, "결손금", "이월결손금의 사용 일정(기준 시나리오)", 설, ["그림의 값"] + [맥.표기(c) for c in 예], 줄들, 키들=키들)


# ══════════════════════════════════════════════════════════════════ 범위 — 결론(3분 레터)
def 범위그림(맥, 종가이름=None):
    """세 시나리오의 주당가치와 날짜를 붙인 종가 — 3분 레터 결론 표 바로 뒤(어느 회사에나). 숫자는 결론 표와 같은 장부 키 · 꼴(어림주당)."""
    B = _B()
    K = "R:%s:2.DCF:68"
    if any(_n(맥.값(K % s)) is None for s in ("비관", "기준", "낙관")):
        return []
    종말 = None
    with B._키기록(맥) as 키들:
        줄들 = [["%s 시나리오" % s, 맥.수(K % s, "어림주당")] for s in ("비관", "기준", "낙관")]
        종 = getattr(맥, "종가키", None)
        if 종 and _n(맥.값(종)) is not None:
            import 레터1부 as _P                             # noqa: PLC0415 — 「종가」 는 어디서나 날짜와 함께(게이트 ⑫)
            종말 = 종가이름 or _P.종가말(맥)
            줄들.append([종말, 맥.수(종, "어림주당")])                 # 결론 표의 종가와 같은 꼴
    설 = "점은 세 시나리오의 주당가치이고 띠는 비관에서 낙관까지의 범위입니다." + (" 세로선은 %s입니다." % 종말 if 종말 else "")
    제 = "세 시나리오의 주당가치" + ("와 %s" % 종말 if 종말 else "")
    return B._그림블록(맥, "범위", 제, 설, ["구분", "주당가치"], 줄들, ["l", "r"], 키들=키들)


# ══════════════════════════════════════════════════════════════════ 조건 — 본편 그림을 고르는 조건
def 블록밖(맥, 절키):
    """그 절 추정 블록의 대조 판정 가운데 「밖」 이 있으면 참 · 판정이 있는데 모두 「안」 이면 거짓 · 판정이 없으면 None."""
    try:
        import 레터원고 as W                                  # noqa: PLC0415
        근 = W.근거표(맥)
    except Exception:                                        # noqa: BLE001
        return None
    if not 근:
        return None
    블록키들 = W.블록절.get(절키) or ()
    판들 = []
    for b in 근.get("블록") or []:
        if b.get("키") not in 블록키들:
            continue
        for d in list(b.get("대조") or []) + [d for z in b.get("줄") or [] for d in z.get("대조") or []]:
            k = d.get("판정키")
            if k:
                판들.append(W.판정값(맥, k))
    판들 = [p for p in 판들 if p in ("안", "밖")]
    if not 판들:
        return None
    return "밖" in 판들


def 종가밖(맥):
    종 = getattr(맥, "종가키", None)
    v = _n(맥.값(종)) if 종 else None
    a, b = _n(맥.값("R:비관:2.DCF:68")), _n(맥.값("R:낙관:2.DCF:68"))
    if v is None or a is None or b is None:
        return None
    return not (min(a, b) <= v <= max(a, b))


def 조건참(맥, 조건, 절키):
    """조건 글 하나 → 참 · 거짓 · None(모름 — 그림을 그대로 둔다)."""
    c = ("%s" % (조건 or "")).strip()
    if not c or 맥 is None:
        return None
    if c == "부록":
        return False
    if c == "블록밖":
        return 블록밖(맥, 절키)
    if c == "지렛대":
        try:
            import 레터그림배치 as 배                         # noqa: PLC0415
            k = 배.지렛대절(맥)
        except Exception:                                    # noqa: BLE001
            return None
        return None if k is None else (k == 절키)
    m = re.match(r"^영구비중\s*>\s*([\d.]+)$", c)
    if m:
        v = _n(맥.값("R:기준:요약:영구가치비중"))
        return None if v is None else v > float(m.group(1))
    if c == "종가밖":
        return 종가밖(맥)
    m = re.match(r"^수준구분\s*>=\s*(\d+)$", c)
    if m:
        n = sum(1 for x in (맥.구 or {}).get("매출구분") or [] if isinstance(x, dict) and x.get("경로") == "수준" and (x.get("번호") or 9) < 6)
        return n >= int(m.group(1))
    return None

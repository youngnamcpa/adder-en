# -*- coding: utf-8 -*-
"""미사용 — 쓰지 않는 입력 줄을 가린다: 가정 파일의 「미사용」 선언 + 구조가 선언하지 않은 매출 구분 (W6b — 3_점검_마감 4절).

붓기는 그 줄의 출처 칸(12번은 근거 1 · 13번 · 3번은 출처)에 「미사용」을 적는다 — 15번 검증 시트의 완결성 점검(C-02 · C-03 · C-05 · C-06 ·
C-07)은 출처가 「미사용」인 줄의 빈칸을 세지 않는다. 워크북 마감은 같은 줄을 접는다(서식마감의 안쓰는줄).
사용 표지 열(설계 4절)을 세우기 전의 꼴이다 — 표지를 출처 칸에 둔다. 사람이 워크북에서 「미사용」을 손으로 적어 미입력을 가리면
마감이 가정 파일의 선언과 맞대어 잡는다(I-52).

선언의 꼴(가정 파일)
  "미사용": ["매출구분3", "A-084", "H-013", "W-009"]
    매출구분s  매출 구분 s(1~5 · 기타 6) — 12번 그 구분의 증가율 · 단가 가정 · 13번 그 구분의 실적 줄 · 4번 그 구분의 구획
    A-nnn      12번 가정 nnn(머리 줄과 세 시나리오 줄)
    H-nnn      13번 원천 nnn
    W-nnn      3번 WACC 줄 nnn
구조가 정하는 것(선언 없이): 선언하지 않은 매출 구분 · 하위 구분(R1a `매출구분[].상위` > 0)의 13번 실적 줄(85 + s) — 하위 구분의 실적은
상위 구분 한 줄에 있고(공시가 가르지 않는다) 이 줄은 비고다. 15번 C-06 · C-07 이 빈칸으로 세지 않게 출처 칸에 표지를 적는다.
구조.원가줄이 선언하지 않은 원가 번호(1~7)의 12번 비율 가정 줄(80 · 84 · 88 · 92 · 112 · 116 · 120 — W4 2026-10-23). 엔진과 5 · 6번 계산 줄은
구조.원가줄의 번호만 읽는다 — 안 쓰는 「경비 N (매출액 대비)」 줄이 익명으로 보이지 않게 접는다.

`구조접을줄(가정, 결과들)` — 표지 없이 엔진 값으로 접는 줄(W4): 판매량명칭이 매출인 구분의 0 인 판매단가 변동률 줄 · 매출원가 합계가
모든 시나리오 · 모든 열에서 0 인 회사의 5번 몸통 · 0 인 선택 기능 줄(주력 제품 비중 · 재료비 및 경비 소계).
"""
import re

원가줄머리 = {1: 80, 2: 84, 3: 88, 4: 92, 5: 112, 6: 116, 7: 120}      # 구조.원가줄 번호 → 12번 비율 가정 머리 줄(가정이전_v13.원가열쇠 와 같은 표)
_re선언 = re.compile(r"^(?:(매출구분)\s*(\d)|([AHW])-(\d{1,4}))$")
표지 = "미사용"


def 매출구분머리(s):
    """매출 구분 s 의 12번 가정 머리 줄 번호들 — 1~5 는 판매량 증가율 · 판매단가 변동률, 6(기타)은 기타 매출액 증가율."""
    return (70,) if s == 6 else (30 + 8 * (s - 1), 34 + 8 * (s - 1))


def 선언구분(가정):
    """구조가 선언한 매출 구분 번호들(1~6). 구조가 없으면 None(가리지 않는다)."""
    구분 = ((가정.get("구조") or {}).get("매출구분")) if isinstance(가정, dict) else None
    if not isinstance(구분, list):
        return None
    return {int(x.get("번호")) for x in 구분 if isinstance(x, dict) and str(x.get("번호", "")).isdigit()}


def 풀기(가정):
    """→ (자리 목록, 오류 목록). 자리 = [(갈래, 시트 번호, 번호, 까닭)] — 갈래: 「구분」(매출 구분 s) · 「줄」.
    선언이 꼴에 맞지 않으면 오류 글."""
    자리, 오류 = [], []
    선언 = 가정.get(표지) if isinstance(가정, dict) else None
    if 선언 is not None and not isinstance(선언, list):
        return [], ["미사용 — 목록이어야 합니다(보기: [\"매출구분3\", \"A-084\"]): %r" % (선언,)]
    구분들 = set()
    for x in 선언 or ():
        m = _re선언.match(("%s" % x).strip())
        if not m:
            오류.append("미사용 「%s」 — 「매출구분3」 · 「A-084」 · 「H-013」 · 「W-009」 꼴로 적습니다" % x)
            continue
        if m.group(1):
            s = int(m.group(2))
            if not 1 <= s <= 6:
                오류.append("미사용 「%s」 — 매출 구분은 1~6(6 = 기타)입니다" % x)
                continue
            구분들.add((s, "선언"))
        else:
            자리.append(("줄", {"A": "12", "H": "13", "W": "3"}[m.group(3)], int(m.group(4)), "선언"))
    쓰는 = 선언구분(가정)
    if 쓰는 is not None:
        for s in range(1, 7):
            if s not in 쓰는 and (s, "선언") not in 구분들:
                구분들.add((s, "구조"))
    for s, 까닭 in sorted(구분들):
        자리.append(("구분", "구분", s, 까닭))
    있는 = {(시, 번) for 갈래, 시, 번, _까닭 in 자리 if 갈래 == "줄"}
    for x in (((가정.get("구조") or {}).get("매출구분")) or []) if isinstance(가정, dict) else ():
        try:
            s, 상 = int(x.get("번호")), int(x.get("상위") or 0)
        except (TypeError, ValueError, AttributeError):
            continue
        if 1 <= s <= 5 and 상 > 0 and ("13", 85 + s) not in 있는:      # R1a 하위 구분 — 13번 실적 줄은 비고(상위 한 줄)
            자리.append(("줄", "13", 85 + s, "구조"))
            있는.add(("13", 85 + s))
    원 = ((가정.get("구조") or {}).get("원가줄")) if isinstance(가정, dict) else None
    if isinstance(원, list):                                         # W4 — 구조가 선언하지 않은 원가 번호의 12번 비율 가정 줄
        쓰는원가 = {int(x.get("번호")) for x in 원 if isinstance(x, dict) and str(x.get("번호", "")).isdigit()}
        for k, h in sorted(원가줄머리.items()):
            if k not in 쓰는원가 and ("12", h) not in 있는:
                자리.append(("줄", "12", h, "구조"))
                있는.add(("12", h))
    return 자리, 오류


def 표지자리(가정):
    """붓기가 「미사용」을 적을 칸 — [(시트 번호, 번호, 열 ID, 까닭, 선언 글)]."""
    낸 = []
    자리, _ = 풀기(가정)
    for 갈래, 시, 번, 까닭 in 자리:
        if 갈래 == "구분":
            글 = "매출구분%d" % 번
            for h in 매출구분머리(번):
                낸.append(("12", h, "근거1", 까닭, 글))
            낸.append(("13", 85 + 번, "출처", 까닭, 글))
        else:
            낸.append((시, 번, "근거1" if 시 == "12" else "출처", 까닭, "%s-%03d" % ({"12": "A", "13": "H", "3": "W"}[시], 번)))
    return 낸


def 구분줄(s):
    """매출 구분 s 를 쓰지 않을 때 접을 줄의 행 ID — 4번 그 구분의 구획(앞의 빈 줄 포함) · 매출액 합계 구획의 그 줄 · 12번 가정 · 13번 실적."""
    낸 = []
    if s <= 5:
        첫, 끝 = (9, 15) if s == 1 else (6 * s + 5, 6 * s + 9)      # 4번 구획머리 009 · 017 · 023 · 029 · 035 와 그 아래 줄
        낸 += ["S04R%03d" % n for n in range(첫, 끝 + 1)] + ["S04R%03d" % (46 + s)]
        for h in 매출구분머리(s):
            낸 += ["S12R%03d" % n for n in range(h, h + 4)]
        if s <= 2:
            낸 += ["S01R%03d" % (32 + s)] + ["S01R%03d" % (48 + 2 * s - 1 + k) for k in (0, 1)]
    else:
        낸 += ["S04R%03d" % n for n in range(41, 45)] + ["S04R052"] + ["S12R%03d" % n for n in range(70, 74)]
    낸.append("S13R%03d" % (85 + s))
    return 낸


def _영(결과들, 시트, 줄):
    """그 줄의 모든 시나리오 · 모든 열 값이 0 이거나 비었나. 결과들 = [엔진 계산 결과 …]. 줄이 결과에 없으면 None(모른다)."""
    있음 = False
    for R in 결과들:
        v = ((R or {}).get(시트) or {}).get("%s" % 줄)
        if not isinstance(v, dict):
            continue
        있음 = True
        for x in v.values():
            if isinstance(x, (int, float)) and not isinstance(x, bool) and abs(x) > 1e-9:
                return False
    return True if 있음 else None


def _매출명칭인가(x):
    """레터1부.매출명칭인가 와 같은 규칙 — 판매량명칭이 매출 그 자체인가."""
    명 = ("%s" % (x.get("판매량명칭") or "")).strip()
    이 = ("%s" % (x.get("이름") or "")).strip()
    뗀 = 명[len(이):].strip() if 이 and 명.startswith(이) and 명[len(이):len(이) + 1].isspace() else 명      # 「<구분 이름> 매출」
    return bool(명) and (명 in ("매출", "매출액", "영업수익") or 뗀 in ("매출", "매출액", "영업수익") or bool(이 and 명 in 이))


def 구조접을줄(가정, 결과들):
    """표지 없이 엔진 값으로 접는 줄의 행 ID(W4 · 2026-10-23) → [(행 ID, 까닭)]. 좌표 지도에 없는 ID 는 서식마감이 건너뛴다.
      · 판매량명칭이 매출인 구분(매출 증가율 하나로 추정)의 판매단가 변동률 줄 — 그 줄이 모두 0 이면(가격 몫이 없다) 4 · 12 · 1번
      · 5번 몸통 — 매출원가 합계(5번 17)가 모두 0 인 회사(영업비용을 한 줄 · 판관비로만 적는 회사): 머리 구역 아래 줄 전부 · 1번 244(매출원가율)
      · 선택 기능 줄 — 주력 제품 매출 비중(4번 14 · 15 · 12번 74) · 재료비 및 경비 소계(5번 151)가 모두 0 이면"""
    낸 = []
    for x in (((가정.get("구조") or {}).get("매출구분")) or []) if isinstance(가정, dict) else ():
        try:
            s = int(x.get("번호"))
        except (TypeError, ValueError, AttributeError):
            continue
        if not (1 <= s <= 5) or not _매출명칭인가(x):
            continue
        단줄 = 11 if s == 1 else 6 * s + 7
        if _영(결과들, "4.Sales", 단줄):
            h = 매출구분머리(s)[1]
            낸 += [("S04R%03d" % 단줄, "판매단가 0 · 매출명칭")] + [("S12R%03d" % n, "판매단가 0 · 매출명칭") for n in range(h, h + 4)]
            낸 += [("S01R17%d" % s, "판매단가 0 · 매출명칭")] + ([("S01R%03d" % (48 + 2 * s), "판매단가 0 · 매출명칭")] if s <= 2 else [])
    if _영(결과들, "5.COGS", 17):
        낸 += [("S05R%03d" % n, "매출원가 없음") for n in range(9, 26)] + [("S05R151", "매출원가 없음"), ("S05R154", "매출원가 없음")]
        낸.append(("S01R244", "매출원가 없음"))                  # 1번 「이 주당가치가 나오려면」 의 매출원가율 줄(2026-10-24 W11)
    if _영(결과들, "4.Sales", 14) and _영(결과들, "4.Sales", 15):
        낸 += [("S04R014", "선택 기능 0"), ("S04R015", "선택 기능 0")] + [("S12R%03d" % n, "선택 기능 0") for n in range(74, 78)]
    if _영(결과들, "5.COGS", 151):
        낸.append(("S05R151", "선택 기능 0"))
    본 = set()
    return [(i, 까) for i, 까 in 낸 if not (i in 본 or 본.add(i))]


def 접을줄(가정):
    """서식마감에 넘길 안 쓰는 줄의 행 ID(좌표 지도에 없는 ID 는 서식마감이 건너뛴다)."""
    낸 = []
    자리, _ = 풀기(가정)
    for 갈래, 시, 번, _까닭 in 자리:
        if 갈래 == "구분":
            낸 += 구분줄(번)
        elif 시 == "12":
            낸 += ["S12R%03d" % n for n in range(번, 번 + 4)]
        else:
            낸.append("S%02dR%03d" % (int(시), 번))
    return list(dict.fromkeys(낸))

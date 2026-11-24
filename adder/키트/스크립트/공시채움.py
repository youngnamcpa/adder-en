# -*- coding: utf-8 -*-
"""공시채움 — 공시(갈래 산출물)에 있는데 어느 도구도 가정 13번에 옮기지 않던 칸을 규칙으로 채운다(손개입 개선 1 · 2026-10-18).

S10 리뷰 1 의 손 개입 열다섯 가운데 「도구 틈」으로 남은 것(S10 재리뷰 2 4절 8 — 원천 86 = 62 · 77 감가상각비 · 리스 짝 47 · 39 · 220 비지배)은
공시에 값이 있거나 규칙의 기본값이 정해져 있는데도 본선이 손으로 옮겼다. 그 손을 이 도구가 대신한다. **값을 지어내지 않는다** — 공시(A2 · A3) 에서
오는 칸은 `[공시]` 로, 공시가 직접 주지 않아 규칙의 기본으로 둔 칸은 `[기본값]` 딱지로 적어 넘긴 몫 장부가 사람 확인 대기로 센다. 회사 · 업종 이름은 없다.

    python 스크립트/공시채움.py 가정.json            # 보기 — 채울 칸 · 못 채우는 칸과 까닭
    python 스크립트/공시채움.py 가정.json --적기     # 가정 파일에 적고 _raw/공시채움.json 에 기록을 남긴다

채우는 칸(빈칸 · null 만 — 값이 있는 칸은 건드리지 않는다. 0 은 빈칸을 0 으로 채운 흔적일 때만(도구 출처가 0 이 아닌 값을 줄 때) 채운다)
  ① 원천 86(구분 1 매출)  — 구조.매출구분 이 상위 구분 하나뿐이면 손익 매출 62 와 같은 값이다 → 86 = 62 `[공시]`(합류 「매출이 한 줄」 판정의 기계적 귀결)
  ② 원천 77(감가상각비)   — A2 77(현금흐름표 API 감가상각비) → A3 상각유형(유형 몫 상각 — 유형자산 주석) → A3 579 − 78(성격별 상각 합에서 무형 상각을 뗀 것)
                           → A3 자산군 상각 합(사용권 미포함 — `추정`). 미국처럼 A2 77 이 상각 총액(D&A)이고 78 이 비었는데 A3 상각무형이 있으면 78 = 상각무형 ·
                           77 = A2 77 − 78 로 가른다(A2 주의 「77 에 인수무형 상각이 들어 있을 수 있다」의 기계적 처리)
  ③ 원천 47 · 39(리스부채) — 19 사용권자산이 있는데 39 · 47 이 모두 비면(기타금융부채에 묻힌 서식) 47 = 19 · 39 = 0 `[기본값]`(IFRS 16 최초 인식 등식의
                           근사 — 리스부채 ≈ 사용권자산 · 유동 · 비유동 미확인). A2 기타후보 가운데 「금융부채 · 리스」 이름을 메모에 적는다 — 사람이 주석 「리스」
                           표로 고친다. ⑳ 「리스 짝 끊김」 오류가 멈춤 문항(기본값 확인 대기)으로 바뀐다
  ④ 시점가정 220(비지배지분 조정률) — 비면 57 비지배지분 장부가 있을 때 1(100% 장부가 차감) `[기본값]`, 57 이 없거나 0 이면 0 `[공시]`(비지배지분 없음)
  ⑤ 주식수 짝 95 · 96 · 97 — 96 이 비고 95 · 97 이 있으면 96 = 95 − 97, 95 가 비고 97 만 있으면(분기 표지) 95 = 97 · 96 = 0 (13번 97 = 95 − 96 식)
  ⑥ 원천 86 ~ 91(구분 s 매출 = 85 + s) — 사람이 `구조.매출구분[s]._부문멤버` 에 XBRL 부문 멤버(QName · 로컬 이름 · 여럿이면 목록 = 합)를 적은 구분만,
                           `_raw/부문매출.json`(「부문매출/1」 — `sec_부문.py` 가 10-K · 10-Q · 20-F 인스턴스의 부문 축 차원 사실에서 짓는다)의 매출을
                           열의 시작 · 끝 날짜로 맞춰 옮긴다 `[공시]`(2026-10-25 Y3-2 C). 하위 구분 · 멤버 없는 구분 · 0 이 적힌 칸은 옮기지 않고 까닭을 적는다
  ⑦ 원천 131 ~ 135(사이 자본거래 · 기준일 열) · 관측.사이자본거래 — **이월 판(재무기준일 ≠ 평가기준일)에서만**(2026-10-25 날짜 둘 · 02_줄번호 3절).
                           `_raw/사이자본거래.json`(「사이자본거래/1」 — `사이자본거래.py` 가 (F, T] 공시 원문 표에서 짓는다)의 반영 사건 합을 옮긴다 `[공시]`.
                           131 유입 현금 · 132 자기주식 취득 · 133 배당(금액 ÷ 메타.환산배율 · 양수) · 134 · 135 주식수(주). 해당 사건이 없으면 0 · 확인 불가 사건만
                           있는 칸은 비우고 까닭을 적는다(0 으로 메우지 않는다). 날짜가 가정과 다른 파일은 쓰지 않는다. 옛 판(F = T)은 건드리지 않는다
못 채우는 것(까닭을 적는다) — 반기 · 분기 보고서의 현금흐름표에 77 이 없는 누계 열 · 사용권 상각 · 유동 리스부채 몫 · 저량 기준일 값(반기 미공시) · A2 기준일이
가정 재무기준일과 다른 파일(쓰지 않는다 — N6-b).
날짜 둘(2026-10-25 · `기준일.py`) — 13번 원천은 재무 쪽이다. A2 대조 · 근거 둘째 칸은 **재무기준일 F**(메타.재무기준일, 없으면 메타.평가기준일 —
옛 가정은 지금과 같다)로 선다.
종료 코드 — 0 채울 것 없음 · 적었다 / 1 채울 것이 있는데 보기만 했다 / 2 입력 오류
"""
import argparse
import datetime
import glob
import io
import json
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:                                    # noqa: BLE001
    pass
여기 = os.path.dirname(os.path.abspath(__file__))
if 여기 not in sys.path:
    sys.path.insert(0, 여기)
from 종료코드 import 통과, 발견, 입력오류                # noqa: E402

도구표지 = "공시채움.py"


def _수(x):
    return float(x) if isinstance(x, (int, float)) and not isinstance(x, bool) else None


def _읽기(p):
    try:
        return json.load(io.open(p, encoding="utf-8"))
    except (OSError, ValueError):
        return None


def 재무날(가정):
    """가정의 재무기준일 F 글 — `기준일.py`(메타.재무기준일, 없으면 메타.평가기준일). 날이 없거나 꼴이 아니면 메타의 글 그대로(옛 동작)."""
    m = (가정.get("메타") or {}) if isinstance(가정, dict) else {}
    try:
        import 기준일 as _기                                    # noqa: PLC0415
        return _기.재무기준일(가정).isoformat()
    except Exception:                                            # noqa: BLE001
        return ("%s" % (m.get("재무기준일") or m.get("평가기준일") or "")).strip()


def 실적열들(가정):
    from 기간축 import 기간축                                      # noqa: PLC0415
    축 = 기간축(가정)
    실 = [축.ID[i] for i in 축.실적]
    누 = 축.ID[축.누계] if 축.누계 is not None else None
    return 실, 누, {축.ID[i]: 축.열[i] for i in 축.실적}


def A2읽기(가정, 가정경로, 원천폴더=None):
    """가정 곁 `_raw/원천_조립*.json` 가운데 기준일이 가정 재무기준일 F 와 같은 가장 새 것 → (dict, 열 대응 {가정 열: A2 열 번호}, 건너뛴 글). 국내(열이름)와
    미국(잔액일 · 흐름기간)을 같은 꼴로 읽는다. A2 쪽 날은 `재무기준일` → `기준일` → 잔액일 끝 차례(옛 파일은 `기준일` = F)."""
    폴더 = 원천폴더 or os.path.join(os.path.dirname(os.path.abspath(가정경로)), "_raw")
    기준일 = 재무날(가정)
    실, 누, 열들 = 실적열들(가정)
    건너뜀 = []
    for p in sorted(glob.glob(os.path.join(폴더, "원천_조립*.json")), key=lambda q: -os.path.getmtime(q)):
        d = _읽기(p)
        if not isinstance(d, dict) or not isinstance(d.get("원천"), dict):
            continue
        a2기준 = ("%s" % (d.get("재무기준일") or d.get("기준일") or "")).strip()
        if not a2기준 and d.get("잔액일"):
            a2기준 = ("%s" % d["잔액일"][-1]).strip()
        if 기준일 and a2기준 and a2기준 != 기준일:
            건너뜀.append("%s(기준일 %s ≠ 가정 %s)" % (os.path.basename(p), a2기준, 기준일))
            continue
        대응 = {}
        이름들 = d.get("열이름")
        if isinstance(이름들, list):                                  # 국내 — FY2024 · FY2025 · 당기
            for i, 이름 in enumerate(이름들):
                if 이름 == "당기" and 누:
                    대응[누] = i
                elif ("%s" % 이름).startswith("FY") and ("%s" % 이름)[2:6].isdigit():
                    y = ("%s" % 이름)[2:6]
                    for c in 실:
                        if c.startswith("FY") and c[2:6] == y:
                            대응[c] = i
        elif isinstance(d.get("잔액일"), list):                       # 미국 — 잔액일 끝날로 맞춘다
            for i, 날 in enumerate(d["잔액일"]):
                for c, 열 in 열들.items():
                    if 열.종료일 and 열.종료일.isoformat() == "%s" % 날:
                        대응[c] = i
        d["_파일"] = os.path.basename(p)
        return d, 대응, 건너뜀
    return None, {}, 건너뜀


def A2값(a2, 대응, 번호, 열, 배):
    if not a2:
        return None
    v = (a2.get("원천") or {}).get("%d" % 번호)
    i = 대응.get(열)
    if not isinstance(v, list) or i is None or i >= len(v):
        return None
    x = _수(v[i])
    return None if x is None else x / 배


def _빈(가정, 번호, 열):
    d = (가정.get("원천") or {}).get("%d" % 번호)
    return not isinstance(d, dict) or _수(d.get(열)) is None


def _영(가정, 번호, 열):
    d = (가정.get("원천") or {}).get("%d" % 번호)
    return isinstance(d, dict) and _수(d.get(열)) == 0.0


def 채울것(가정, 가정경로, 원천폴더=None):
    """→ (채움 목록, 못채움 목록, 쓰기 함수들). 채움 = {"칸": "원천 86", "열": …, "값": …, "딱지": "[공시]"/"[기본값]", "출처": 글, "근거": 4칸}."""
    실, 누, 열들 = 실적열들(가정)
    배 = _수((가정.get("메타") or {}).get("환산배율")) or 1.0
    기준일 = 재무날(가정)                                          # 근거 둘째 칸 — 값이 그날 것(재무기준일 F)
    폴더 = 원천폴더 or os.path.join(os.path.dirname(os.path.abspath(가정경로)), "_raw")
    a2, 대응, 건너뜀 = A2읽기(가정, 가정경로, 폴더)
    a3 = _읽기(os.path.join(폴더, "동인원천.json")) or {}
    원행 = a3.get("원천행") or {} if isinstance(a3, dict) else {}
    채움, 못 = [], []
    for g in 건너뜀:
        못.append({"칸": "A2", "까닭": "기준일이 다른 A2 는 쓰지 않는다(N6-b) — %s" % g})
    원 = 가정.setdefault("원천", {})
    근 = 가정.setdefault("원천근거", {})

    def 넣기(번호, 열, 값, 딱지, 출처, 메모, 확인="도구 채움"):
        채움.append({"칸": "원천 %d" % 번호, "번호": "%d" % 번호, "열": 열, "값": 값, "딱지": 딱지, "출처": 출처,
                   "근거": ["%s %s — %s" % (딱지, 출처, 도구표지), 기준일, "%s · %s" % (확인, 메모), None]})

    # ① 86 = 62 — 상위 구분이 하나뿐
    구분 = [x for x in ((가정.get("구조") or {}).get("매출구분") or []) if isinstance(x, dict) and x.get("번호") and not (x.get("상위") or 0)]
    if len(구분) == 1 and int(구분[0]["번호"]) == 1:
        for c in 실:
            v62 = _수((원.get("62") or {}).get(c))
            if v62 is None:
                continue
            if _빈(가정, 86, c) or (_영(가정, 86, c) and v62 != 0.0):
                넣기(86, c, v62, "[공시]", "손익계산서 매출액(13번 62)", "매출 구분이 상위 하나(%s)라 구분 1 매출 = 손익 매출(합류 「매출이 한 줄」)" % (구분[0].get("이름") or "구분 1"))
    elif len(구분) > 1 and not all(부문멤버목록(x) for x in 구분):         # 모든 구분에 부문 멤버가 적혔으면 ⑥ 이 옮긴다(이 안내를 내지 않는다)
        for c in 실:
            if _빈(가정, 86, c) and _수((원.get("62") or {}).get(c)) is not None:
                못.append({"칸": "원천 86~%d" % (85 + len(구분)), "까닭": "매출 구분이 %d개 — 부문 주석의 구분별 매출은 본선이 옮긴다(한 줄이 아니다)" % len(구분)})
                break

    # ②-0 78 무형 상각 가르기 — 77 이 상각 총액(현금흐름표 D&A — 태그에 Amortization)이고 78 이 비었는데 A3 상각무형(무형 상각 태그 · 주석)이 그 열에 있으면
    #    78 = 상각무형 · 77 = 77 − 78 (A2 주의 「77 에 인수무형 상각이 들어 있을 수 있다 — 떼어 78 에」의 기계적 처리). 77 이 비어 있으면 아래 ② 가 함께 한다
    a2태그77 = ((a2.get("태그") or {}).get("77") if a2 else None) or []
    a2태그글77 = " · ".join(a2태그77) if isinstance(a2태그77, list) else "%s" % a2태그77
    무형표 = (a3.get("유형자산") or {}).get("상각무형") if isinstance(a3.get("유형자산"), dict) else None
    for c in 실:
        v77 = _수((원.get("77") or {}).get(c))
        무형 = _수(무형표.get(c)) if isinstance(무형표, dict) else None
        if v77 and (_빈(가정, 78, c) or _영(가정, 78, c)) and "Amortization" in a2태그글77 and 무형 and 0 < 무형 < v77                 and A2값(a2, 대응, 77, c, 배) is not None and abs(A2값(a2, 대응, 77, c, 배) - v77) <= abs(v77) * 1e-6:
            넣기(78, c, 무형, "[공시]", "A3 상각무형(companyfacts 무형 상각 태그 · 무형자산 주석)", "A2 77 이 상각 총액(%s)이라 무형 상각을 떼어 78 에 둔다" % a2태그글77)
            넣기(77, c, v77 - 무형, "[공시]", "A2 77(%s) − 78 무형 상각" % a2태그글77, "상각 총액에서 무형 상각(A3 상각무형)을 뺀 유형 · 사용권 몫 — 77 을 고쳐 적는다(원래 %s)" % "{:,.1f}".format(v77))
        elif v77 and (_빈(가정, 78, c) or _영(가정, 78, c)) and "Amortization" in a2태그글77 and not 무형:
            못.append({"칸": "원천 78", "열": c, "까닭": "A2 77 이 상각 총액(%s)인데 무형 상각을 가를 재료가 없다 — companyfacts 무형 상각 태그에 %s 값이 없다(10-K 무형자산 주석의 상각액을 사람이 78 에 옮긴다 — 공시에 있으나 API 에 없음)" % (a2태그글77, c)})
    이미 = {(x["번호"], x["열"]) for x in 채움}
    # ② 77 감가상각비(· 78 무형 상각). 차례는 리스 스위치가 정한다 — 리스부채포함 = 포함(사용권자산이 있으면 그 상각도 77 에 든다)이면
    #    A2 77 → 579 − 78(성격별 상각 합 — 사용권 포함) → 상각유형(사용권 미포함 — 과소 표시) → 자산군 합, 제외(또는 사용권 없음)면 A2 77 → 상각유형 → 579 − 78 → 자산군 합
    포함 = (((가정.get("스위치") or {}).get("리스부채포함")) or "포함") != "제외"
    for c in 실:
        if ("77", c) in 이미 or not (_빈(가정, 77, c) or _영(가정, 77, c)):
            continue
        사용권있음 = bool(_수((원.get("19") or {}).get(c)))
        a2_77 = A2값(a2, 대응, 77, c, 배)
        a2태그 = (a2.get("태그") or {}).get("77") if a2 else None
        a2태그글 = " · ".join(a2태그) if isinstance(a2태그, list) else ("%s" % (a2태그 or ""))
        if a2_77 is not None and a2_77 != 0.0:
            무형 = _수(((a3.get("유형자산") or {}).get("상각무형") or {}).get(c)) if isinstance((a3.get("유형자산") or {}).get("상각무형"), dict) else None
            if _빈(가정, 78, c) and 무형 and "Amortization" in a2태그글 and 무형 < a2_77:
                넣기(78, c, 무형, "[공시]", "A3 상각무형(%s)" % (a3.get("유형자산") or {}).get("상각무형출처", "무형자산 상각 태그 · 주석"),
                    "A2 77 이 상각 총액(%s)이라 무형 상각을 떼어 78 에 둔다" % a2태그글)
                넣기(77, c, a2_77 - 무형, "[공시]", "A2 77(%s) − 78 무형 상각" % a2태그글, "상각 총액에서 무형 상각(A3 상각무형)을 뺀 유형 · 사용권 몫")
            else:
                넣기(77, c, a2_77, "[공시]", "A2 %s 현금흐름표 감가상각비(%s)" % (a2.get("_파일"), a2태그글 or "77"), "현금흐름표 API 값 그대로")
            continue
        상유 = (a3.get("유형자산") or {}).get("상각유형") if isinstance(a3.get("유형자산"), dict) else None
        v상유 = _수(상유.get(c)) if isinstance(상유, dict) else None
        v579 = _수((원행.get("579") or {}).get(c))
        v78 = _수((원.get("78") or {}).get(c)) or 0.0

        def 상유넣기():
            넣기(77, c, v상유, "[공시]", "A3 상각유형(유형자산 주석 종류별 상각 합 — 사용권 · 무형 뺀)",
                "사용권 상각은 들지 않는다%s" % (" — 리스부채포함 = 포함 · 사용권자산 있음이라 과소(579 가 없어 유형 몫만) · 주석 「리스」 사용권 상각을 더한다" if (포함 and 사용권있음) else ""),
                "추정 — 사람 확인")

        def 상579넣기():
            넣기(77, c, v579 - v78, "[공시]", "A3 579 성격별 상각 합%s" % (" − 78 무형 상각" if v78 else ""),
                "유형 · 사용권%s 상각이 섞인 합이다%s" % ("" if v78 else " · 무형(78 이 비면 포함)", " — 리스부채포함 = 포함이라 사용권 상각이 든 이 값이 엔진 77 의 뜻과 맞다" if (포함 and 사용권있음) else ""),
                "추정 — 사람 확인")
        차례 = ((상579넣기, bool(v579)), (상유넣기, bool(v상유))) if (포함 and 사용권있음) else ((상유넣기, bool(v상유)), (상579넣기, bool(v579)))
        됨 = False
        for f, 있 in 차례:
            if 있:
                f()
                됨 = True
                break
        if 됨:
            continue
        합 = 0.0
        군들 = (a3.get("유형자산") or {}).get("자산군") if isinstance(a3.get("유형자산"), dict) else None
        있 = False
        for 군 in 군들 or []:
            x = _수(((군.get("감가상각비") or {}) if isinstance(군, dict) else {}).get(c))
            if x is not None:
                합 += x
                있 = True
        if 있 and 합:
            넣기(77, c, 합, "[공시]", "A3 자산군 상각 합(유형자산 주석)", "사용권 상각 미포함 · 자산군이 합계 줄을 품으면 겹친다", "추정 — 사람 확인")
            continue
        못.append({"칸": "원천 77", "열": c, "까닭": "A2 현금흐름표(API) · A3 상각유형 · 579 · 자산군 상각에 %s 값이 없다%s" % (
            c, " — 반기 · 분기 보고서의 현금흐름표 상각은 API 에 없는 회사가 있다(주석 「유형자산」 반기 상각에서 사람이 옮긴다)" if c == 누 else "")})

    # ③ 리스 짝 — 19 가 있는데 39 · 47 이 모두 비면
    기타 = [x for x in (a2.get("기타후보") or []) if isinstance(x, dict)] if a2 else []
    후보 = [("%s %s" % (x.get("계정명"), "{:,.0f}".format(_수(x.get("금액")) / 배) if _수(x.get("금액")) is not None else "")).strip()
          for x in 기타 if re.search(r"리스|금융부채|기타비유동부채|기타유동부채", "%s" % x.get("계정명"))]
    for c in 실:
        v19 = _수((원.get("19") or {}).get(c))
        if not v19 or v19 <= 0:
            continue
        if (_빈(가정, 39, c) or _영(가정, 39, c)) and (_빈(가정, 47, c) or _영(가정, 47, c)):
            넣기(47, c, v19, "[기본값]", "리스부채(비유동) = 사용권자산 장부(13번 19)", "IFRS 16 최초 인식 등식의 근사(리스부채 ≈ 사용권자산) — 유동 · 비유동 미확인 · 주석 「리스」 표로 고친다%s" % (
                (" · A2 기타 후보: " + " / ".join(후보[:4])) if 후보 else ""), "기본값 — 사람 확인 대기")
            넣기(39, c, 0.0, "[기본값]", "리스부채(유동) 0 — 비유동(47)에 전액", "유동 몫은 주석 「리스」의 만기 표에서 가른다", "기본값 — 사람 확인 대기")

    # ⑤ 주식수 짝 — 97 유통 = 95 발행 − 96 자기주식(워크북 13번 식). 96 이 비고 95 · 97 이 있으면 96 = 95 − 97, 95 가 비고 97 만 있으면(분기 표지 유통주식수) 95 = 97 · 96 = 0
    for c in 실:
        v95, v96, v97 = (_수((원.get(k) or {}).get(c)) for k in ("95", "96", "97"))
        if v95 is not None and v97 is not None and _빈(가정, 96, c) and v95 >= v97:
            넣기(96, c, v95 - v97, "[공시]", "자기주식수 = 발행주식총수(95) − 유통주식수(97)", "13번 97 = 95 − 96 식의 되풀이(A2 가 발행 · 유통을 주고 자기주식 줄이 없는 서식)")
        elif v95 is None and v97 is not None:
            넣기(95, c, v97, "[공시]", "발행주식총수 = 보고서 표지 유통주식수(97)", "그 기준일에는 표지 유통주식수뿐이다(10-Q · 분기 표지) — 자기주식 0 으로(96)")
            if _빈(가정, 96, c):
                넣기(96, c, 0.0, "[공시]", "자기주식수 0 — 표지 유통주식수를 발행으로 둠", "표지에는 자기주식 줄이 없다")
    # ④ 220 비지배지분 조정률
    시점 = 가정.setdefault("시점가정", {})
    v220 = 시점.get("220")
    비었 = v220 is None or (isinstance(v220, dict) and all(_수(x) is None for x in v220.values()))
    if 비었:
        끝열 = 누 or 실[-1]
        v57 = _수((원.get("57") or {}).get(끝열))
        if v57 and v57 > 0:
            채움.append({"칸": "시점가정 220", "번호": "220", "열": "시점", "값": {"비관": 1, "기준": 1, "낙관": 1}, "딱지": "[기본값]",
                       "출처": "비지배지분 장부 %s(13번 57 %s) — 100%% 장부가 차감" % ("{:,.0f}".format(v57), 끝열),
                       "근거": ["[기본값] 비지배지분 조정률 1(100%% 장부가 차감 — 13번 57 %s %s) — %s" % (끝열, "{:,.0f}".format(v57), 도구표지), 기준일,
                              "기본값 — 사람 확인 대기 · 비지배지분의 시가 · 배수가 있으면 조정률을 바꾼다", "세 시나리오 같음"]})
        else:
            채움.append({"칸": "시점가정 220", "번호": "220", "열": "시점", "값": {"비관": 0, "기준": 0, "낙관": 0}, "딱지": "[공시]",
                       "출처": "비지배지분 없음(13번 57 %s)" % ("0" if v57 == 0.0 else "줄 없음"),
                       "근거": ["[공시] 비지배지분 없음(13번 57 %s) — %s" % ("0" if v57 == 0.0 else "줄 없음", 도구표지), 기준일, "빈칸(조정 없음)", "세 시나리오 같음"]})
    # ⑥ 부문 매출 86 ~ 91 — 사람이 구조.매출구분[s]._부문멤버 에 XBRL 부문 멤버를 적은 구분만(2026-10-25 Y3-2 C)
    채움6, 못6 = 부문채울것(가정, 폴더, 실, 열들, 배, {(x["번호"], x["열"]) for x in 채움})
    # ⑦ 사이 자본거래 131 ~ 135 — 이월 판(F ≠ T)에서만(2026-10-25 날짜 둘)
    채움7, 못7 = 사이채울것(가정, 폴더, 배)
    return 채움 + 채움6 + 채움7, 못 + 못6 + 못7


# ════════════════════════════════════════ ⑦ 사이 자본거래 — `_raw/사이자본거래.json`(「사이자본거래/1」 · 사이자본거래.py)
#   02_줄번호 3절 — 13번 131 유입 현금(증자 · 행사 · 자기주식 처분) · 132 자기주식 취득 현금 · 133 배당 지급 현금(양수 — 산식이 뺀다) ·
#   134 주식수 증가 · 135 주식수 감소. 기준일 열 한 칸 + 근거 4칸 [출처(접수번호들) · 기준일(T) · 확인상태 · 소비처]. 합은 사이자본거래.줄합계 한 곳.
#   옛 판(F = T)에서 131 ~ 135 에 값이 있으면 엔진 검증 오류다 — 그래서 옛 판에서는 아무것도 하지 않는다.
사이줄 = {"131": "주식 발행 · 전환 · 행사 · 자기주식 처분 유입 현금", "132": "자기주식 취득 현금", "133": "배당 지급 현금",
         "134": "주식수 증가(발행 · 전환 · 행사 · 자기주식 처분)", "135": "주식수 감소(자기주식 취득)"}


def 사이채울것(가정, 폴더, 배):
    채움, 못 = [], []
    try:
        import 기준일 as _기                                    # noqa: PLC0415
        F, T = _기.재무기준일(가정).isoformat(), _기.평가기준일(가정).isoformat()
    except Exception:                                            # noqa: BLE001
        return 채움, 못
    if F == T:
        return 채움, 못                                          # 옛 판 — 131 ~ 135 를 두지 않는다
    p = os.path.join(폴더, "사이자본거래.json")
    d = _읽기(p)
    if not isinstance(d, dict) or d.get("형식") != "사이자본거래/1":
        못.append({"칸": "원천 131~135", "까닭": "이월 판(재무기준일 %s · 평가기준일 %s)인데 `_raw/사이자본거래.json` 이 없다 — "
                                              "`python 스크립트/사이자본거래.py --가정 <가정> --회사 <고유번호>` 를 먼저" % (F, T)})
        return 채움, 못
    if d.get("재무기준일") != F or d.get("평가기준일") != T:
        못.append({"칸": "원천 131~135", "까닭": "사이자본거래.json 의 날짜(%s · %s)가 가정(%s · %s)과 다르다 — 쓰지 않는다" % (
            d.get("재무기준일"), d.get("평가기준일"), F, T)})
        return 채움, 못
    from 기간축 import 기간축                                    # noqa: PLC0415
    import 사이자본거래 as 사                                     # noqa: PLC0415
    축 = 기간축(가정)
    열 = 축.ID[축.기준일]
    합 = 사.줄합계(d)
    사건 = {s.get("접수번호"): s for s in d.get("사건") or []}
    출처틀 = "DART %s" if d.get("국가") != "US" else "SEC %s"
    for 번호, 이름 in 사이줄.items():
        v = 합["칸"].get(번호)
        if v is None:
            못.append({"칸": "원천 %s" % 번호, "열": 열, "까닭": "%s — (F, T] 사건이 확인 불가라 비운다(0 으로 메우지 않는다): %s" % (이름, 합["빈칸까닭"].get(번호, ""))})
            continue
        if not (_빈(가정, int(번호), 열) or (_영(가정, int(번호), 열) and v != 0.0)):
            continue
        값 = v / 배 if 번호 in ("131", "132", "133") else v
        건 = 합["건"].get(번호) or []
        필요 = [s.get("확인상태") for k in 건 for s in [사건.get(k) or {}] if "확인 필요" in (s.get("확인상태") or "")]
        확인 = "도구 채움 · %s" % ("(F, T] 공시 목록에 해당 사건 없음" if not 건 else "원문 표 %d건" % len(건))
        if 필요:
            확인 += " · 확인 필요 — " + " / ".join(sorted(set(필요)))
        if 합["빈칸까닭"].get(번호):
            확인 += " · 일부 확인 불가 — " + 합["빈칸까닭"][번호][:160]
            못.append({"칸": "원천 %s" % 번호, "열": 열, "까닭": "확인된 사건만 더했다 — 확인 불가 사건이 남았다(사람이 더한다): %s" % 합["빈칸까닭"][번호]})
        출처 = " · ".join(출처틀 % k for k in 건) if 건 else "(F, T] 공시 목록 %s ~ %s" % ((d.get("창") or {}).get("목록시작") or F, T)
        채움.append({"칸": "원천 %s" % 번호, "번호": 번호, "열": 열, "값": 값, "딱지": "[공시]", "출처": "사이자본거래.json %s" % (출처[:80]),
                   "근거": ["[공시] %s — %s · 사이자본거래.py · %s" % (이름, 출처, 도구표지), T, 확인, "2번 165 · 167(이월 다리)"]})
    관 = 가정.get("관측") if isinstance(가정.get("관측"), dict) else {}
    if 합["관측"] and not 관.get("사이자본거래"):
        목록 = [dict(x, 현금=(x["현금"] / 배) if isinstance(x.get("현금"), (int, float)) else x.get("현금")) for x in 합["관측"]]
        채움.append({"칸": "관측 사이자본거래", "번호": "사이자본거래", "열": "목록", "값": 목록, "딱지": "[공시]",
                   "출처": "사이자본거래.json 반영 사건 %d건" % len(목록), "근거": None})
    for x in 합.get("사람확인") or []:
        못.append({"칸": "원천 131", "열": 열, "까닭": x})
    return 채움, 못


# ════════════════════════════════════════ ⑥ 부문 매출 — `_raw/부문매출.json`(「부문매출/1」 · sec_부문.py)
#   사람이 `구조.매출구분[s]._부문멤버`(글 하나 또는 글 목록 — 부문 멤버 QName 「ns:이름Member」 또는 로컬 이름)를 적은 구분만 옮긴다.
#   밑줄 키라 엔진 구조 검증 · 구조 지문 밖이다(주석 키 관례). 멤버가 여럿이면 그 합(같은 기간이 다 있을 때만 — 하나라도 없으면 못 채움).
#   열은 날짜로 맞춘다(시작 · 끝이 양쪽 7일 안 — 52/53주 결산). 값 = 공시 값 합 ÷ 메타.환산배율. 빈칸만 채운다(0 이 적힌 칸도 두고 못 채움에 적는다).
#   하위 구분(상위 > 0)은 실적 줄을 비우는 자리라 옮기지 않는다. 근거 첫 칸이 있으면 그 뒤에 「 / 」 로 잇는다(그 줄의 다른 열 출처를 지우지 않는다).

def 부문멤버목록(x):
    v = x.get("_부문멤버") if isinstance(x, dict) else None
    if isinstance(v, str):
        return [v.strip()] if v.strip() else []
    if isinstance(v, list):
        return [("%s" % m).strip() for m in v if isinstance(m, str) and m.strip()]
    return []


def _멤버찾기(적은, 멤버들):
    """적은 글 → 부문매출의 멤버 QName | None — QName 그대로(대소문자 무시) 먼저, 없으면 로컬 이름이 하나로 맞을 때."""
    a = 적은.lower()
    같음 = [m for m in 멤버들 if m.lower() == a]
    if 같음:
        return 같음[0]
    로컬 = [m for m in 멤버들 if m.split(":", 1)[-1].lower() == a.split(":", 1)[-1]]
    return 로컬[0] if len(로컬) == 1 else None


def _날(s):
    try:
        return datetime.date.fromisoformat(("%s" % s)[:10])
    except (TypeError, ValueError):
        return None


def _기간칸(값들, 열):
    """{기간id: 칸} 가운데 열의 시작일 · 종료일과 양 끝이 7일 안에서 맞는 칸 → (id, 칸) | (None, None)."""
    for k, v in (값들 or {}).items():
        s, e = _날(v.get("시작")), _날(v.get("끝"))
        if s and e and 열.시작일 and 열.종료일 and abs((s - 열.시작일).days) <= 7 and abs((e - 열.종료일).days) <= 7:
            return k, v
    return None, None


def 부문채울것(가정, 폴더, 실, 열들, 배, 이미):
    채움, 못 = [], []
    선언 = [x for x in ((가정.get("구조") or {}).get("매출구분") or []) if isinstance(x, dict) and 부문멤버목록(x)]
    if not 선언:
        return 채움, 못
    p = os.path.join(폴더, "부문매출.json")
    d = _읽기(p)
    if not isinstance(d, dict) or d.get("형식") != "부문매출/1":
        못.append({"칸": "원천 86~91", "까닭": "부문 멤버를 적은 구분이 %d개인데 `_raw/부문매출.json`(부문매출/1)이 없다 — `python 스크립트/sec_부문.py` 를 먼저" % len(선언)})
        return 채움, 못
    표시통화 = ("%s" % ((가정.get("메타") or {}).get("표시통화") or "")).strip().upper()
    통화 = d.get("통화")
    if 표시통화 and isinstance(통화, str) and 통화.upper() != 표시통화:
        못.append({"칸": "원천 86~91", "까닭": "부문매출 통화 %s ≠ 가정 표시통화 %s — 옮기지 않는다" % (통화, 표시통화)})
        return 채움, 못
    값표 = (d.get("값표") or {}).get("매출") or {}
    이름 = {m.get("멤버"): m.get("이름") for m in d.get("멤버") or [] if isinstance(m, dict)}
    검산 = [z for z in d.get("검산") or [] if isinstance(z, dict) and z.get("종류") == "매출"]
    근 = 가정.get("원천근거") or {}
    for x in 선언:
        번 = x.get("번호")
        if not isinstance(번, int) or isinstance(번, bool) or not 1 <= 번 <= 6:
            continue
        번호 = 85 + 번
        if x.get("상위"):
            못.append({"칸": "원천 %d" % 번호, "까닭": "구분 %d 는 하위 구분(상위 %s)이라 실적 줄을 비운다 — 부문 멤버는 상위 구분에 적는다" % (번, x.get("상위"))})
            continue
        적은 = 부문멤버목록(x)
        멤버 = [_멤버찾기(m, list(값표)) for m in 적은]
        if not all(멤버):
            못.append({"칸": "원천 %d" % 번호, "까닭": "구분 %d 의 부문 멤버 %s 가 부문매출.json 에 없다 — 받는 멤버: %s" % (
                번, " · ".join(m for m, q in zip(적은, 멤버) if not q), " · ".join(sorted(값표)) or "없음")})
            continue
        줄 = []                                                       # (열, 값, [칸들])
        for c in 실:
            if ("%d" % 번호, c) in 이미 or c not in 열들:
                continue
            칸들 = [_기간칸(값표.get(m), 열들[c])[1] for m in 멤버]
            if not all(칸들):
                if _빈(가정, 번호, c):
                    못.append({"칸": "원천 %d" % 번호, "열": c, "까닭": "부문매출.json 에 %s 기간(%s ~ %s)의 %s 매출이 없다 — 그 기간을 담은 공시를 sec_부문.py 로 받는다" % (
                        c, 열들[c].시작일, 열들[c].종료일, " · ".join(m for m, v in zip(멤버, 칸들) if not v))})
                continue
            if any(_수(v.get("값")) is None for v in 칸들):
                continue
            값 = sum(_수(v["값"]) for v in 칸들) / 배
            if _빈(가정, 번호, c):
                줄.append((c, 값, 칸들))
            elif _영(가정, 번호, c) and 값 != 0.0:
                못.append({"칸": "원천 %d" % 번호, "열": c, "까닭": "0 이 적혀 있어 두었다 — 부문 차원 사실은 %s(값이 있는 칸은 건드리지 않는다 · 0 이 빈칸 표시면 지우고 다시 돈다)" % "{:,.4f}".format(값)})
        if not 줄:
            continue
        # 그 줄의 근거 하나 — 공시별 열 · 개념 · 멤버(표시 이름) · 검산 판정
        공시 = {}
        for c, _v, 칸들 in 줄:
            공시.setdefault((칸들[0]["양식"], 칸들[0]["접수번호"], 칸들[0]["개념"]), []).append(c)
        조각 = " / ".join("%s %s(%s)" % (양, 접, " · ".join(cs)) for (양, 접, _개), cs in 공시.items())
        개념들 = " · ".join(sorted({k[2] for k in 공시}))
        멤글 = " + ".join("%s%s" % (m, ("(%s)" % 이름[m]) if 이름.get(m) else "") for m in 멤버)
        판정 = []
        for c, _v, 칸들 in 줄:
            z = next((z for z in 검산 if z.get("접수번호") == 칸들[0]["접수번호"] and z.get("시작") == 칸들[0]["시작"] and z.get("끝") == 칸들[0]["끝"]), None)
            판정.append("%s %s" % (c, z["판정"] if z else "검산 없음"))
        감사 = sorted({("감사(연차 보고서)" if 양.split("/")[0] in ("10-K", "20-F", "40-F", "10-KT") else "미감사 중간(분기 보고서)") for (양, _접, _개) in 공시})
        첫 = "[공시] %s XBRL 부문 차원 사실 %s · 부문 = %s — %s" % (조각, 개념들, 멤글, 도구표지)
        끝날 = " · ".join(sorted({칸들[0]["끝"] for _c, _v, 칸들 in 줄}))
        확인 = "도구 채움 · %s · 부문 합 검산 %s" % (" · ".join(감사), " · ".join(판정))
        옛 = list(근.get("%d" % 번호)) if isinstance(근.get("%d" % 번호), list) else []
        옛 = (옛 + [None] * 4)[:4]
        if 옛[0]:
            근거 = ["%s / %s" % (옛[0], 첫), ("%s · %s" % (옛[1], 끝날)) if 옛[1] else 끝날, ("%s · %s" % (옛[2], 확인)) if 옛[2] else 확인, 옛[3]]
        else:
            근거 = [첫, 끝날, 확인, 옛[3]]
        for c, 값, 칸들 in 줄:
            채움.append({"칸": "원천 %d" % 번호, "번호": "%d" % 번호, "열": c, "값": 값, "딱지": "[공시]",
                       "출처": "부문매출.json %s %s %s(%s)" % (칸들[0]["양식"], 칸들[0]["접수번호"], 멤글, 칸들[0]["개념"]), "근거": 근거})
    return 채움, 못


def 적기(가정, 채움):
    원 = 가정.setdefault("원천", {})
    근 = 가정.setdefault("원천근거", {})
    for x in 채움:
        if x["칸"].startswith("원천"):
            if not isinstance(원.get(x["번호"]), dict):             # null 줄(빈 줄 표시) — 객체로 세운다(전에는 여기서 멈췄다)
                원[x["번호"]] = {}
            원[x["번호"]][x["열"]] = x["값"]
            근[x["번호"]] = list(x["근거"])
        elif x["칸"].startswith("시점가정"):
            가정.setdefault("시점가정", {})[x["번호"]] = x["값"]
            가정.setdefault("근거", {})[x["번호"]] = list(x["근거"])
        elif x["칸"] == "관측 사이자본거래":                            # ⑦ 사건 목록(엔진은 읽지 않는다 · 자체검사가 13번 합과 견준다)
            if not isinstance(가정.get("관측"), dict):
                가정["관측"] = {}
            가정["관측"]["사이자본거래"] = list(x["값"])
    return 가정


def main(argv=None):
    ap = argparse.ArgumentParser(allow_abbrev=False, description="공시에 있는데 도구가 안 채우던 13번 칸을 규칙으로 채운다(손개입 개선 1)")
    ap.add_argument("가정")
    ap.add_argument("--원천폴더", default=None, help="갈래 산출물 폴더(기본: 가정 곁 _raw/)")
    ap.add_argument("--적기", action="store_true")
    a = ap.parse_args(argv)
    가정 = _읽기(a.가정)
    if not isinstance(가정, dict):
        sys.stderr.write("가정을 못 읽었습니다 — %s\n" % a.가정)
        return 입력오류
    try:
        채움, 못 = 채울것(가정, a.가정, a.원천폴더)
    except Exception as e:                                   # noqa: BLE001
        sys.stderr.write("채울 것을 재지 못했습니다 — %s: %s\n" % (type(e).__name__, e))
        return 입력오류
    for x in 채움:
        print("  채움 %s %s = %s  %s %s" % (x["칸"], x["열"], ("{:,.4f}".format(x["값"]) if isinstance(x["값"], float) else
                                                         ("%d건" % len(x["값"]) if isinstance(x["값"], list) else x["값"])), x["딱지"], x["출처"]))
    for x in 못:
        print("  못 채움 %s %s — %s" % (x["칸"], x.get("열", ""), x["까닭"]))
    print("공시채움 — 채움 %d · 못 채움 %d" % (len(채움), len(못)))
    기록 = {"도구": 도구표지, "시각": datetime.datetime.now().isoformat(timespec="seconds"), "가정": os.path.basename(a.가정),
          "채움": [{k: v for k, v in x.items() if k != "근거"} | {"근거": x.get("근거")} for x in 채움], "못채움": 못}
    if a.적기:
        적기(가정, 채움)
        io.open(a.가정, "w", encoding="utf-8").write(json.dumps(가정, ensure_ascii=False, indent=1))
        폴더 = a.원천폴더 or os.path.join(os.path.dirname(os.path.abspath(a.가정)), "_raw")
        os.makedirs(폴더, exist_ok=True)
        io.open(os.path.join(폴더, "공시채움.json"), "w", encoding="utf-8").write(json.dumps(기록, ensure_ascii=False, indent=1))
        print("적었습니다 — %s · 기록 %s" % (a.가정, os.path.join(폴더, "공시채움.json")))
        return 통과
    return 발견 if 채움 else 통과


if __name__ == "__main__":
    sys.exit(main())

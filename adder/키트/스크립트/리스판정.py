# -*- coding: utf-8 -*-
"""리스판정 — 회사 회계기준과 리스 구분을 보고 리스를 한 방식으로만 셈하게 한다(1.1.3 · US GAAP 운용리스 이중 차감).

    python 스크립트/리스판정.py <가정.json>                 # 판정 · 값 영향만(가정을 바꾸지 않는다)
    python 스크립트/리스판정.py <가정.json> --고치기        # 이중 차감이면 가정을 고친다(옛 판은 _raw/_리스판정전_<날>.json)

왜 — 키트의 리스 스위치 「포함」(기본)은 리스를 금융으로 본다: 리스부채(원천 39 · 47)를 브리지에서 빼고 사용권자산(19)을 상각 밑값에 더한다.
  K-IFRS · IFRS 16 회사는 리스료가 영업비용에 없어(사용권 상각 + 이자) 짝이 맞는다. **US GAAP 운용리스는 리스료(정액 리스 비용)가 영업비용 안에
  남는다** — 그 회사에 「포함」을 두면 리스료를 영업이익에서 한 번, 리스부채를 브리지에서 또 한 번 뺀다(이중 차감). 둘 중 하나만 한다.

판정 — 회계기준(메타.회계기준 → `_raw/원천_조립.json` 「리스구분.회계기준」 → 원천근거의 us-gaap · ifrs 표지 → 관할 US 면 US GAAP) ·
  리스 구분(원천_조립 「리스구분」 의 운용 · 금융 잔액 → 원천근거 39 · 47 의 OperatingLease 태그) · 스위치(리스부채포함) · 리스 재조정(영업비용에서 리스료를
  뺀 판 — `도착점.조정.리스재조정` 이나 `스위치사유.리스부채포함` 에 「리스료」 · 「재조정」 · 「영업비용에서 뺐」).
    이중 차감   US GAAP · 운용리스가 39 · 47 에 있다 · 스위치 포함 · 리스 재조정 없음
    한 방식     그 밖(IFRS · 제외 · 재조정한 판 · 운용리스 없음)
고치기 — 금융리스(부채 · 사용권)는 금융으로 남긴다: 금융리스부채를 차입 줄(38 유동성장기부채 · 45 사채 · 장기부채)로, 금융 사용권을 유형자산(17)으로 옮기고
  39 · 47 · 19 에는 운용리스만 남긴 뒤 스위치를 「제외」 로 둔다(운용리스 부채는 브리지에서 빼지 않고 사용권은 상각 밑값에서 빠진다 — 리스료가 영업비용에
  이미 있다). 금융 몫 금액을 모르면(원천_조립 리스구분 없음) 스위치만 「제외」 로 두고 금융리스가 함께 빠진 사실 · 그 금액의 한도를 적는다.
값 영향 — 엔진으로 고친 판과 지금 판의 주당가치를 함께 낸다(값을 지어내지 않는다). 회사 · 업종 이름은 이 도구에 없다.
종료 코드 — 0 한 방식 · 1 이중 차감(고치기 전) · 2 입력 오류.
"""
from __future__ import annotations

import argparse
import copy
import datetime
import io
import json
import os
import sys

여기 = os.path.dirname(os.path.abspath(__file__))
if 여기 not in sys.path:
    sys.path.insert(0, 여기)
from 종료코드 import 통과, 발견, 입력오류  # noqa: E402

재조정말 = ("리스료", "재조정", "영업비용에서 뺐", "영업비용에서 제외", "operating lease cost")
운용말 = ("OperatingLease", "Operating lease", "operating lease", "운용리스", "운용 +", "리스 주석 운용")


def _n(x):
    try:
        return None if x is None or isinstance(x, bool) else float(x)
    except (TypeError, ValueError):
        return None


def _조립(가정경로):
    p = os.path.join(os.path.dirname(os.path.abspath(가정경로)), "_raw", "원천_조립.json") if 가정경로 else None
    try:
        return json.load(io.open(p, encoding="utf-8")) if p and os.path.exists(p) else {}
    except (OSError, ValueError):
        return {}


def 회계기준(가정, 조=None):
    m = 가정.get("메타") or {}
    if m.get("회계기준"):
        return "%s" % m["회계기준"], "메타.회계기준"
    리 = ((조 or {}).get("리스구분") or {})
    if 리.get("회계기준"):
        return 리["회계기준"], "원천 조립(리스구분)"
    근 = json.dumps(가정.get("원천근거") or {}, ensure_ascii=False)
    if "us-gaap" in 근 or "OperatingLease" in 근:
        return "US GAAP", "원천근거의 us-gaap 태그"
    if "ifrs-full" in 근:
        return "IFRS", "원천근거의 ifrs-full 태그"
    관 = ("%s" % (m.get("관할") or "")).upper() or {"KRW": "KR", "USD": "US"}.get(("%s" % (m.get("표시통화") or "KRW")).upper(), "")
    if 관 == "KR":
        return "K-IFRS", "관할 KR"
    if 관 == "US":
        return "US GAAP", "관할 US(추정 — 메타.회계기준으로 밝힌다)"
    return None, "모름"


def _열들(가정):
    """원천 39 · 47 의 열(엔진 기간 축 차례) — 잔액일 셋(조립)과 같은 차례다."""
    from 엔진.읽개 import 축내기                              # noqa: PLC0415
    축 = 축내기(가정)
    return [축.ID[i] for i in 축.실적]


def 판정(가정, 가정경로=None):
    조 = _조립(가정경로)
    기준, 출 = 회계기준(가정, 조)
    스 = ((가정.get("스위치") or {}).get("리스부채포함") or "포함")
    사 = "%s" % ((가정.get("스위치사유") or {}).get("리스부채포함") or "")
    재 = bool(((가정.get("도착점") or {}).get("조정") or {}).get("리스재조정")) or any(w in 사 for w in 재조정말)
    리 = 조.get("리스구분") or {}
    근 = json.dumps({k: (가정.get("원천근거") or {}).get(k) for k in ("39", "47")}, ensure_ascii=False)
    태 = json.dumps((리.get("태그") or {}), ensure_ascii=False)
    운용 = (any(_n(v) for v in (리.get("운용부채유동") or []) + (리.get("운용부채비유동") or [])) or any(w in 근 for w in 운용말)
          or ("OperatingLease" in 태))
    원 = 가정.get("원천") or {}
    리합 = {k: (원.get(k) or {}) for k in ("39", "47")}
    out = {"회계기준": 기준, "회계기준출처": 출, "스위치": 스, "재조정": 재, "운용리스": bool(운용), "리스구분": bool(리), "리스행": 리합}
    try:                                                     # 기준일 열의 리스 금액(39 · 47 · 19) — 모두 0 이면 겹칠 것이 없다
        from 엔진.읽개 import _기준일값, 축내기               # noqa: PLC0415
        축 = 축내기(가정)
        금 = sum(abs(_n(_기준일값(가정, r, 축)) or 0.0) for r in (39, 47, 19))
    except Exception:                                        # noqa: BLE001
        금 = None
    out["리스금액"] = 금
    if 기준 == "US GAAP" and 운용 and 스 == "포함" and not 재 and (금 is None or 금 > 0):
        out["판정"] = "이중 차감"
        out["까닭"] = ("US GAAP 운용리스 — 리스료가 영업비용에 남아 있는데 스위치 「포함」 이 리스부채(39 · 47)를 브리지에서 또 뺀다. 금융리스는 차입 줄로 옮기고 "
                     "스위치를 「제외」 로 두거나(운용리스를 영업으로), 영업비용에서 리스료를 뺀 재조정 판이면 그 근거를 스위치사유에 적는다")
    else:
        out["판정"] = "한 방식"
        out["까닭"] = ("회계기준 %s · 스위치 %s%s%s" % (기준 or "모름", 스, " · 리스 재조정" if 재 else "", "" if 운용 else " · 운용리스 없음"))
    return out


def 고친판(가정, 가정경로=None):
    """이중 차감이면 고친 가정 사본과 바꾼 것 목록. 금융 몫을 알면 차입 · 유형으로 옮기고, 모르면 스위치만."""
    조 = _조립(가정경로)
    리 = 조.get("리스구분") or {}
    a = copy.deepcopy(가정)
    원 = a.setdefault("원천", {})
    바꿈 = []
    try:
        열 = _열들(a)
    except Exception:                                        # noqa: BLE001
        열 = []
    n = len(리.get("잔액일") or [])
    if 리 and 열 and n == len(열):
        for 칸, 뺄행, 넣을행 in (("금융부채유동", "39", "38"), ("금융부채비유동", "47", "45"), ("금융사용권", "19", "17")):
            값들 = 리.get(칸) or []
            if 뺄행 == "19" and any("FinanceLeaseRightOfUseAsset" in ("%s" % t) for t in ((리.get("태그") or {}).get("17") or [])):
                continue                                         # 17 이 이미 금융 사용권을 품었다(조립이 19 에서 뺐다)
            if 뺄행 == "19" and not any("FinanceLeaseRightOfUseAsset" in ("%s" % t) for t in ((리.get("태그") or {}).get("19") or [])):
                continue
            운용들 = 리.get({"39": "운용부채유동", "47": "운용부채비유동", "19": "운용사용권"}[뺄행]) or []
            for i, (c, v) in enumerate(zip(열, 값들)):
                v = _n(v)
                if not v:
                    continue
                배 = float(((a.get("메타") or {}).get("환산배율")) or 1)
                v = v / 배
                # 1.1.8 — 그 줄에 금융 몫이 이미 없으면(원천 조립 · A2 가 차입 줄로 갈랐다) 옮기지 않는다. 종전에는 두 번 옮겨 음수가 되거나(금융 > 운용)
                #   운용 몫을 차입으로 옮겼다(금융 < 운용). 그 줄 값이 「운용 + 금융」 보다 「운용만」 에 가까우면 이미 갈라졌다고 본다
                현 = _n((원.get(뺄행) or {}).get(c)) or 0.0
                운 = (_n(운용들[i]) or 0.0) / 배 if i < len(운용들) else None
                if 현 < v - max(1e-9, abs(v) * 1e-9) or (운 is not None and abs(현 - 운) < abs(현 - (운 + v))):
                    바꿈.append("%s 금융 몫 %.6g 은 %s(%s 열 %.6g)에 없어 옮기지 않았다 — 이미 %s 쪽에 갈라져 있다고 본다" % (칸, v, 뺄행, c, 현, 넣을행))
                    continue
                for 행, 부호 in ((뺄행, -1), (넣을행, 1)):
                    줄 = 원.setdefault(행, {})
                    줄[c] = (_n(줄.get(c)) or 0.0) + 부호 * v
                바꿈.append("%s 금융 몫 %.6g 을 %s → %s 로(%s)" % (칸, v, 뺄행, 넣을행, c))
    else:
        바꿈.append("원천 조립의 리스구분이 없거나 열이 맞지 않아 금융리스 몫을 옮기지 못했다 — 스위치만 「제외」(금융리스 부채도 브리지에서 빠진다 · 그 금액만큼 과대 한도)")
    a.setdefault("스위치", {})["리스부채포함"] = "제외"
    a.setdefault("스위치사유", {})["리스부채포함"] = ("US GAAP 운용리스 — 리스료가 영업비용에 있어 운용리스 부채는 브리지에서 빼지 않는다(이중 차감 방지 · 리스판정.py %s). "
                                              "금융리스는 차입 줄(38 · 45) · 유형자산(17)으로 옮겼다" % datetime.date.today().isoformat())
    바꿈.append("스위치 리스부채포함 = 제외")
    # 1.1.4(R3) — 계정 분류도 스위치와 맞춘다: 운용리스만 남은 39 · 47(리스부채) · 19(사용권)는 브리지 · 영업자산 소비처에서 「명시적 제외」
    # (종전에는 소비처가 이자부부채 · 영업자산(사용권) 그대로라 마감 정합성 I-02 · I-03 · I-28 이 오류였다 — 엔진 값은 같다)
    소 = a.get("소비처")
    if isinstance(소, dict):
        for 행 in ("19", "39", "47"):
            if 소.get(행) not in (None, "명시적 제외"):
                바꿈.append("소비처 %s 「%s」 → 「명시적 제외」" % (행, 소.get(행)))
                소[행] = "명시적 제외"
    # 1.1.4(P-01) — 상각률(156)을 「유형 + 사용권」 밑으로 잰 회차(근거 글에 사용권)는 사용권이 밑에서 빠지면 상각비가 줄어든다 — 그 비를 마지막 실적 열의
    # (유형 + 사용권) ÷ 유형 배로 옮겨 유형자산 밑으로 다시 잰다(근거가 유형자산만으로 잰 상각률이면 그대로 — 사용권 상각은 리스료와 겹친 몫이었다)
    import re as _re                                         # noqa: PLC0415
    근 = (a.get("근거") or {}).get("156")
    근글 = ("%s" % (근[0] if isinstance(근, (list, tuple)) and 근 else (근 or "")))
    방 = ((a.get("구조") or {}).get("투자") or {}).get("상각방식") or "상각률"
    벌 = (a.get("가정") or {}).get("156")
    if 방 == "상각률" and isinstance(벌, dict) and _re.search(r"사용권|right[- ]of[- ]use|\bROU\b", 근글, _re.I):
        실 = [c for c in (열 or []) if _n((원.get("17") or {}).get(c)) and _n((원.get("19") or {}).get(c)) is not None]
        if 실:
            c = 실[-1]
            v17, v19 = _n(원["17"][c]), _n(원["19"][c]) or 0.0
            k = (v17 + v19) / v17 if v17 else None
            if k and k > 1.0 + 1e-9:
                for s, 열값 in 벌.items():
                    if isinstance(열값, dict):
                        for cc, v in list(열값.items()):
                            if _n(v) is not None:
                                열값[cc] = _n(v) * k
                바꿈.append("상각률 156 을 %.3f배로(유형 + 사용권 밑 → 유형자산 밑 · %s 열 (%.6g + %.6g) ÷ %.6g)" % (k, c, v17, v19, v17))
                if isinstance(근, list) and 근:
                    근[0] = "%s · [계산] 1.1.4 리스판정 — 사용권을 상각 밑에서 뺀 판: 유형자산 밑으로 %.3f배" % (근[0], k)
    return a, 바꿈


def 값영향(가정, 고친, 가정경로=None):
    """지금 · 고친 판 · 브리지만(운용리스 부채만 39 · 47 에서 뺀 판 — 스위치 그대로)의 기준 주당가치. 고친 판과 브리지만의 차는 사용권 상각
    (영업비용의 리스료와 겹친 8번 상각 · 유지 투자)의 몫이다."""
    from 엔진.계산 import 계산                                # noqa: PLC0415
    지 = 계산(가정, "기준")["요약"]["주당가치"]
    새 = 계산(고친, "기준")["요약"]["주당가치"]
    out = {"지금": 지, "고친판": 새, "변화": ((새 - 지) / 지) if 지 else None}
    리 = (_조립(가정경로).get("리스구분") or {})
    try:
        열 = _열들(가정)
    except Exception:                                        # noqa: BLE001
        열 = []
    if 리 and 열 and len(리.get("잔액일") or []) == len(열):
        b = copy.deepcopy(가정)
        배 = float(((b.get("메타") or {}).get("환산배율")) or 1)
        for 칸, 행 in (("운용부채유동", "39"), ("운용부채비유동", "47")):
            for c, v in zip(열, 리.get(칸) or []):
                if _n(v):
                    줄 = b.setdefault("원천", {}).setdefault(행, {})
                    줄[c] = (_n(줄.get(c)) or 0.0) - _n(v) / 배
        br = 계산(b, "기준")["요약"]["주당가치"]
        out.update({"브리지만": br, "브리지만변화": ((br - 지) / 지) if 지 else None})
    return out


def main(argv=None):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:                                        # noqa: BLE001
        pass
    ap = argparse.ArgumentParser(description="리스를 한 방식으로만 — US GAAP 운용리스 이중 차감 판정 · 고치기")
    ap.add_argument("가정")
    ap.add_argument("--고치기", action="store_true")
    a = ap.parse_args(argv)
    try:
        가정 = json.load(io.open(a.가정, encoding="utf-8"))
        판 = 판정(가정, a.가정)
    except (OSError, ValueError) as e:
        print("입력오류 — %s" % e)
        return 입력오류
    print("리스 판정 — %s (%s) · 회계기준 %s(%s)" % (판["판정"], 판["까닭"], 판["회계기준"], 판["회계기준출처"]))
    if 판["판정"] != "이중 차감":
        return 통과
    고친, 바꿈 = 고친판(가정, a.가정)
    try:
        영 = 값영향(가정, 고친, a.가정)
        print("  값 영향 — 기준 주당가치 %.6g → %.6g (%+.2f%%)%s" % (영["지금"], 영["고친판"], 100 * (영["변화"] or 0),
              (" · 그 가운데 브리지(운용리스 부채만) %+.2f%%" % (100 * 영["브리지만변화"])) if 영.get("브리지만변화") is not None else ""))
    except Exception as e:                                   # noqa: BLE001
        print("  값 영향 — 셈 실패: %s" % e)
    for x in 바꿈:
        print("  · " + x)
    if not a.고치기:
        print("  가정을 바꾸지 않았다 — 고치려면 --고치기")
        return 발견
    백 = os.path.join(os.path.dirname(os.path.abspath(a.가정)), "_raw", "_리스판정전_%s.json" % datetime.date.today().isoformat())
    os.makedirs(os.path.dirname(백), exist_ok=True)
    with io.open(백, "w", encoding="utf-8") as f:
        json.dump(가정, f, ensure_ascii=False, indent=1)
    with io.open(a.가정, "w", encoding="utf-8") as f:
        json.dump(고친, f, ensure_ascii=False, indent=1)
    print("  고쳤다 → %s (옛 판 %s)" % (a.가정, 백))
    return 통과


if __name__ == "__main__":
    sys.exit(main())

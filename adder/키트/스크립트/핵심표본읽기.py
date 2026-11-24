# -*- coding: utf-8 -*-
"""핵심표본읽기 — C1 `핵심표본.json` 을 유사기업 도구들이 한 함수로 읽는다 (2026-10-24 W16 · 유니버스 조사 물결 1 · 2차).

종전에는 도구마다 읽는 칸이 달랐다 — `peer_βU_us` 는 `컷통과전체[].구분` 만 읽어 그 칸이 비거나(C1 이 핵심 · 예비 목록만 채운 꼴)
티커 문자열 목록이면 핵심 묶음이 비어 「본값 0곳 · 산업 βU 선택지 ★」 로 떨어졌고(유니버스 조사 물결 실측), 국내 조립기는
해외 줄(종목코드 없음)을 만나면 멈췄다(유니버스 조사 물결 실측). 운영 단계는 운영 동종이 아니라 컷 통과 전체를 돌았다(유니버스 조사 물결 실측).

정본 차례: `핵심[]` · `예비[]` · `운영동종전용[]`(별칭 넷) 목록이 먼저 · `컷통과전체` / `컷통과_전체` 는 그 밖의 회사에만(문자열이면
구분 「컷통과」). 옛 꼴(티커 문자열 목록)은 전부 핵심.

  구분표(h)                      → {열쇠: {"구분", "슬롯", "목적", "시장", "행"}} · 열쇠 = 미국 티커(대문자) · 국내 종목코드(6자리)
  명단(h, 구분들, 시장=None)      → 행 목록(구분 차례대로 · 중복 없음)
  운영명단(h, 시장=None)          → 운영 동종 행(운영동종전용 + 목적에 「운영」 이 든 핵심 · 예비 · 목적이 하나도 없으면 핵심)
  시장(x)                        → "US" · "KR" · None(모름)
  목록꼴(j)                      → dict 로 감싼 티커 목록(`{"tickers": […]}` · `{"티커들": […]}` · 목록 값이 하나뿐인 dict)을 목록으로(2026-10-24 W17)

같은 회사가 핵심 · 예비(위험 동종)와 운영동종전용에 함께 있으면 위험 동종 쪽 줄을 정본으로 두고 `겸운영` 을 단다 — 운영 동종 전용으로만
읽혀 βU 에서 빠지던 결함(2026-10-24 W17 · META 조사 — AMZN · MSFT 를 예비 + 운영 동종 전용에 두었다). 운영명단은 겸운영도 낸다.
"""
from __future__ import annotations

전용키 = ("운영동종전용", "운영동종_전용", "운영 동종 전용", "운영전용")
컷키 = ("컷통과전체", "컷통과_전체")
_국내시장 = {"KR", "유가", "코스닥", "코넥스", "KOSPI", "KOSDAQ", "유가증권", "유가증권시장", "코스닥시장"}


def 시장(x):
    if not isinstance(x, dict):
        return None
    m = ("%s" % (x.get("시장") or "")).strip()
    if m.upper() in ("US", "NYSE", "NASDAQ", "미국"):
        return "US"
    if m in _국내시장 or m.upper() in _국내시장:
        return "KR"
    if x.get("종목코드"):
        return "KR"
    if x.get("티커") or x.get("ticker") or x.get("cik"):
        return "US"
    return None


def 열쇠(x):
    if isinstance(x, str):
        return x.strip().upper() or None
    if not isinstance(x, dict):
        return None
    c = ("%s" % (x.get("종목코드") or "")).strip()
    if c and c.isdigit():
        return c.zfill(6)
    t = x.get("티커") or x.get("ticker") or x.get("Ticker")
    return ("%s" % t).strip().upper() if t else None


def _목적(x):
    v = x.get("목적") if isinstance(x, dict) else None
    if isinstance(v, str):
        return [s.strip() for s in v.replace("·", ",").split(",") if s.strip()]
    if isinstance(v, list):
        return [("%s" % s).strip() for s in v if s]
    return []


_목록키 = ("tickers", "티커들", "티커목록", "Tickers")


def 목록꼴(j):
    """dict 로 감싼 티커 목록을 목록으로 — 아니면 그대로."""
    if not isinstance(j, dict):
        return j
    if any(k in j for k in ("핵심", "예비", "행", "cands") + 전용키 + 컷키):
        return j
    for k in _목록키:
        if isinstance(j.get(k), list):
            return j[k]
    목록값 = [v for v in j.values() if isinstance(v, list)]
    if len(목록값) == 1:
        return 목록값[0]
    return j


def 구분표(h):
    표 = {}
    h = 목록꼴(h)
    if isinstance(h, list):
        for x in h:
            k = 열쇠(x)
            if k:
                표.setdefault(k, {"구분": "핵심", "슬롯": (x.get("슬롯") if isinstance(x, dict) else "") or "",
                                "목적": _목적(x), "시장": 시장(x) if isinstance(x, dict) else None,
                                "행": x if isinstance(x, dict) else {"티커": k}})
        return 표
    if not isinstance(h, dict):
        return 표
    묶음 = [("핵심", h.get("핵심") or []), ("예비", h.get("예비") or [])] + [("운영동종전용", h.get(k) or []) for k in 전용키]
    for 이름, 목록 in 묶음:
        for x in 목록 if isinstance(목록, list) else []:
            k = 열쇠(x)
            if not k:
                continue
            행 = x if isinstance(x, dict) else {"티커": k}
            if k in 표:                                  # 같은 회사가 두 묶음에 — 위험 동종 줄이 정본, 운영동종전용에도 있으면 겸운영
                if 이름 == "운영동종전용" and 표[k]["구분"] in ("핵심", "예비"):
                    표[k]["겸운영"] = True
                for s in _목적(행):
                    if s not in 표[k]["목적"]:
                        표[k]["목적"].append(s)
                continue
            표[k] = {"구분": 이름, "슬롯": (행.get("슬롯") or ""), "목적": _목적(행), "시장": 시장(행), "행": 행}
    for ck in 컷키:
        for x in h.get(ck) or []:
            k = 열쇠(x)
            if not k or k in 표:
                continue
            행 = x if isinstance(x, dict) else {"티커": k}
            g = 행.get("구분") if isinstance(x, dict) else None
            g = g if g in ("핵심", "예비", "운영동종전용") else "컷통과"
            표[k] = {"구분": g, "슬롯": (행.get("슬롯") or ""), "목적": _목적(행), "시장": 시장(행), "행": 행}
    return 표


def 명단(h, 구분들=("핵심", "예비"), 시장_=None):
    표 = 구분표(h)
    낸 = []
    for g in 구분들:
        for k, v in 표.items():
            if v["구분"] == g and (시장_ is None or v["시장"] == 시장_ or (v["시장"] is None and 시장_ == "US" and not v["행"].get("종목코드"))):
                낸.append(dict(v["행"], **{"구분": g, "_열쇠": k}))
    return 낸


def 운영명단(h, 시장_=None):
    """운영 동종 — 운영동종전용 + 목적에 「운영」 이 든 핵심 · 예비. 목적을 아무도 적지 않았으면 핵심 + 운영동종전용."""
    표 = 구분표(h)
    목적있음 = any(v["목적"] for v in 표.values())
    낸 = []
    for k, v in 표.items():
        if 시장_ is not None and v["시장"] not in (시장_, None):
            continue
        if 시장_ == "US" and v["시장"] is None and v["행"].get("종목코드"):
            continue
        if v["구분"] == "운영동종전용" or v.get("겸운영") or (목적있음 and v["구분"] in ("핵심", "예비") and any("운영" in s for s in v["목적"])) \
                or (not 목적있음 and v["구분"] == "핵심"):
            낸.append(dict(v["행"], **{"구분": v["구분"], "_열쇠": k}))
    return 낸


def 해외더하기(h, 핵심=(), 예비=(), 까닭="", 슬롯="", 목적="위험동종,운영동종", 이름표=None, 일시=None):
    """C1 `핵심표본.json`(사전 꼴)에 해외 동종 줄을 넣는다(2026-10-24 W18 · 유니버스 조사 결함 7 · 10 · 13 — 손 스크립트로 넣었다).
    줄은 `{"티커", "시장": "US", "구분", "슬롯", "목적", "판단"}` — 국내 조립기는 건너뛰고 미국 사슬(`sec_peer_사슬` · `peer_βU_us`)이 핵심 · 예비로 읽는다.
    이미 있는 회사는 그 구분을 바꾸지 않고 「이미」 로 센다(한 회사를 두 묶음에 두지 않는다). → (h, {"더함": [], "이미": []}). 「판단대장」 에 적는다."""
    if not isinstance(h, dict):
        raise ValueError("사전 꼴(핵심 · 예비 목록을 가진) 핵심표본만 고친다 — 옛 티커 목록 꼴은 먼저 C1 꼴로")
    표 = 구분표(h)
    셈 = {"더함": [], "이미": []}
    대장 = h.setdefault("판단대장", [])
    for 구, 목록 in (("핵심", 핵심), ("예비", 예비)):
        for t in 목록:
            t = ("%s" % t).strip().upper()
            if not t:
                continue
            if t in 표:
                셈["이미"].append("%s(%s)" % (t, 표[t]["구분"]))
                continue
            줄 = {"티커": t, "회사명": (이름표 or {}).get(t, ""), "시장": "US", "구분": 구, "슬롯": 슬롯, "목적": 목적,
                 "경로": "판단(해외)", "판단": 까닭 or "판단으로 넣은 해외 동종"}
            h.setdefault(구, []).append(줄)
            표[t] = {"구분": 구}
            대장.append({"자리": "C1 %s" % 구, "티커": t, "판단": "해외 더함", "까닭": 까닭 or "판단으로 넣음", "일시": 일시})
            셈["더함"].append(t)
    return h, 셈


def main(argv=None):
    import argparse                                  # noqa: PLC0415
    import io                                        # noqa: PLC0415
    import json                                      # noqa: PLC0415
    import os                                        # noqa: PLC0415
    import shutil                                    # noqa: PLC0415
    import time                                      # noqa: PLC0415
    ap = argparse.ArgumentParser(description="핵심표본 읽기 · 해외 동종 줄 넣기", allow_abbrev=False)
    sub = ap.add_subparsers(dest="명령", required=True)
    s = sub.add_parser("해외더하기", allow_abbrev=False, help="핵심표본.json 에 해외(미국 상장) 동종을 핵심 · 예비로 넣는다 — 옛 파일은 `.이전.json`")
    s.add_argument("--표본", default=os.path.join("_raw", "peers", "핵심표본.json"))
    s.add_argument("--핵심", default="", help="티커(쉼표)")
    s.add_argument("--예비", default="", help="티커(쉼표)")
    s.add_argument("--까닭", required=True, help="판단대장에 적을 까닭(필수 — 판단으로 넣는 표본이다)")
    s.add_argument("--슬롯", default="")
    s.add_argument("--목적", default="위험동종,운영동종")
    s = sub.add_parser("보기", allow_abbrev=False, help="구분표를 화면에")
    s.add_argument("--표본", default=os.path.join("_raw", "peers", "핵심표본.json"))
    a = ap.parse_args(argv)
    if not os.path.exists(a.표본):
        print("입력 오류 — 핵심표본이 없다(%s)" % a.표본)
        return 2
    h = json.load(io.open(a.표본, encoding="utf-8"))
    if a.명령 == "보기":
        for k, v in 구분표(h).items():
            print("  %-8s %-6s %-3s %s" % (k, v["구분"], v["시장"] or "-", v["슬롯"]))
        return 0
    이름표 = {}
    for x in ((h.get("해외경로") or {}).get("후보") or []) if isinstance(h, dict) else []:
        if isinstance(x, dict) and x.get("티커"):
            이름표[("%s" % x["티커"]).upper()] = x.get("회사명", "")
    try:
        h, 셈 = 해외더하기(h, [x for x in a.핵심.split(",") if x.strip()], [x for x in a.예비.split(",") if x.strip()],
                         a.까닭, a.슬롯, a.목적, 이름표, time.strftime("%Y-%m-%d %H:%M:%S"))
    except ValueError as e:
        print("입력 오류 — %s" % e)
        return 2
    if 셈["더함"]:
        이전 = os.path.splitext(a.표본)[0] + ".이전.json"
        shutil.copy2(a.표본, 이전)
        json.dump(h, io.open(a.표본, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("해외 더함 %d(%s) · 이미 있음 %d(%s)%s" % (len(셈["더함"]), ", ".join(셈["더함"]) or "-", len(셈["이미"]), ", ".join(셈["이미"]) or "-",
                                             " — 옛 파일은 %s" % (os.path.splitext(a.표본)[0] + ".이전.json") if 셈["더함"] else ""))
    return 0 if 셈["더함"] else 1


if __name__ == "__main__":
    import sys
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:                                # noqa: BLE001
        pass
    sys.exit(main())

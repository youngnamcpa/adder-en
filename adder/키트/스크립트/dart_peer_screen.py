# -*- coding: utf-8 -*-
"""DART 상장사 재무 일괄 조회 — 유사기업 후보를 좁히는 1차 재료.

**한 곳씩 부르지 않는다.** 전자공시시스템은 회사를 100곳씩 묶어 받는 창구를
따로 열어 두었고, 이 스크립트가 그 창구를 쓴다.

    GET https://opendart.fss.or.kr/api/fnlttMultiAcnt.json
        corp_code   쉼표로 이어 붙인 고유번호. **한 번에 100곳까지**
        bsns_year   사업연도
        reprt_code  11011 사업보고서 / 11012 반기 / 11013 1분기 / 11014 3분기
        fs_div      CFS 연결 / OFS 별도

    한 곳씩 부르면 상장사 전체가 약 2,500호출이라 중간에 연결이 끊긴다.
    100곳씩 묶으면 26호출이고 30초면 끝난다.

**종목코드가 있다고 상장사가 아니다.** `corpCode.xml`에는 상장이 폐지된 회사도
종목코드를 단 채로 남아 있다. 3,986건 중 약 1,400건이 그렇고, 그 회사들은
조회해도 데이터가 없다.

    **그렇다고 `modify_date` 로 거르지는 않는다 — 기본은 전수다.**
    `modify_date` 는 상장 상태가 아니라 정보 갱신일이다. 2년 필터를 걸었더니
    **대상회사 자신(삼화전자공업 20221103)과 실제 핵심 표본 둘이 사라졌다.**
    대상회사가 자기 유사기업 표에서 빠지면 규모대의 기준값 자체가 안 나오는데
    표는 멀쩡해 보인다. 600곳을 더 받아도 100곳씩 묶으므로 **호출 6회 차이**다.
    거르고 싶으면 `--since` 를 명시적으로 주고, 그때는 `--대상` 도 같이 준다.

주요계정은 열넷뿐이다(매출액·영업이익·자산총계 등). **차입금 명세나 주식수는
여기 없다.** 그것들은 후보를 좁힌 뒤 그 회사들만 따로 받는다 —
**싼 조회로 전수, 비싼 조회는 좁힌 뒤.** 이 스크립트가 **싼 층**이다.

    싼 층    이 스크립트 — 주요계정 일괄            후보 전원       26호출 1분
    중간 층  주식수·자기주식·기업개황·종가 1점       1차 컷 통과분   20곳 안팎
    비싼 층  3년 주간 시세·베타 회귀·잔차상관        핵심 표본+예비  7~12곳

**이 산출로 1차 컷을 건다.** 여기서 나온 매출·자산 규모대와 사업 단계로 후보를
줄이고, 시가총액이 필요한 2차 컷은 중간 층을 받은 뒤에 건다. **후보 전원에
비싼 층을 돌리지 않는다** — 유사기업 재료 수집이 매 회차 최장 작업이고 멈춤이
그 완료를 기다린다(유사기업-선정 스킬 「비싼 조회는 좁힌 뒤」).

인증키는 환경변수 `OPENDART_API_KEY`에서 읽고 화면에 출력하지 않는다.

사용법
    python dart_peer_screen.py                          # 상장사 전체, 직전 사업연도
    python dart_peer_screen.py --year 2025
    python dart_peer_screen.py --year 2025 --half       # 반기보고서
    python dart_peer_screen.py --codes 01032486,00159209   # 후보만 다시
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import io
import os
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
import zipfile

API = "https://opendart.fss.or.kr/api"
BATCH = 100          # 창구가 받는 상한. 넘기면 status 021
PAUSE = 0.5          # 배치 사이 간격. 연속 호출로 끊기는 것을 막는다
CACHE = "_dartcache"

REPRT = {"annual": "11011", "half": "11012", "q1": "11013", "q3": "11014"}

# 주요계정에서 뽑아 쓸 것. 계정명은 회사마다 표기가 갈리므로 부분일치로 찾는다.
WANT = [
    ("매출액", ["매출액", "수익(매출액)", "영업수익", "매출", "수익"]),
    ("영업이익", ["영업이익", "영업이익(손실)", "영업손실", "영업손익"]),  # 「영업손익」 2026-09-13 펄어비스 실측
    # **「당기순이익」만 찾으면 적자 회사가 통째로 빈다.** 손실인 회사는 계정명을
    # 「당기순이익(손실)」로 올린다(실측: 삼화전자공업이 이 이름이라 빈 칸이 나왔다).
    ("당기순이익", ["당기순이익", "당기순이익(손실)", "당기순손실", "분기순이익",
               "반기순이익", "당기순이익(당기순손실)"]),
    ("자산총계", ["자산총계"]),
    ("부채총계", ["부채총계"]),
    ("자본총계", ["자본총계"]),
]


def _key() -> str:
    k = os.environ.get("OPENDART_API_KEY")
    if not k:
        sys.exit("환경변수 OPENDART_API_KEY 가 없습니다. 값은 화면에 적지 마십시오.")
    return k


def _get(url: str, timeout: int = 90, tries: int = 4):
    """끊기면 간격을 늘려 다시 부른다."""
    last = None
    for i in range(tries):
        try:
            return urllib.request.urlopen(url, timeout=timeout).read()
        except Exception as e:                       # noqa: BLE001
            last = e
            time.sleep(1.5 * (i + 1))
    raise last                                        # type: ignore[misc]


def corp_index(refresh: bool = False):
    """고유번호 대조표. 하루에 한 번만 받으면 된다."""
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, "corpCode.xml")
    raw_copy = os.path.join("_raw", "corpCode.xml")   # 본선이 이미 받았으면 다시 안 받는다
    if not refresh and not os.path.exists(path) and os.path.exists(raw_copy):
        path = raw_copy
    if refresh or not os.path.exists(path):
        blob = _get(f"{API}/corpCode.xml?crtfc_key={_key()}")
        with zipfile.ZipFile(io.BytesIO(blob)) as z:
            with open(path, "wb") as f:
                f.write(z.read(z.namelist()[0]))
    root = ET.parse(path).getroot()
    out = []
    for e in root.iter("list"):
        stock = (e.findtext("stock_code") or "").strip()
        if not stock:
            continue
        out.append({
            "corp_code": e.findtext("corp_code"),
            "corp_name": e.findtext("corp_name"),
            "stock_code": stock,
            "modify_date": e.findtext("modify_date") or "",
        })
    return out


def live_only(rows, since: str):
    """상장폐지 추정분을 걷어낸다 — 다만 modify_date 는 정보 갱신일이지 상장 상태가
    아니다. 살아 있는 상장사도 몇 해 갱신이 없으면 걸러질 수 있으므로(실측: 우리로·
    쏠리드·유비쿼스·코위버), 걸러낸 목록을 반드시 함께 돌려주고 호출 쪽이 파일로
    남긴다. 조용히 빼지 않는다."""
    kept = [r for r in rows if r["modify_date"] >= since]
    dropped = [r for r in rows if r["modify_date"] < since]
    return kept, dropped


def 공용C1():
    """공용 캐시의 C1 자리(전 상장사 주요계정 · 상장명부 · 산업분류) — 환경변수 DCF_공용캐시 · DCF_SHARED_CACHE · 없으면 ~/.dcf캐시."""
    return os.path.join(os.environ.get("DCF_공용캐시") or os.environ.get("DCF_SHARED_CACHE")
                        or os.path.join(os.path.expanduser("~"), ".dcf캐시"), "C1")


def fetch(codes, year: int, reprt: str, fs_div: str = "CFS", 진행=None):
    """100곳씩 묶어 주요계정을 받는다. 진행 = 배치마다 받은 것을 적는 파일 — 끊겨도 받은 만큼 남고 다음 실행이 이어받는다(2026-10-24 W15)."""
    import json
    got, misses, 끝난 = {}, [], set()
    if 진행 and os.path.exists(진행):
        try:
            d = json.load(open(진행, encoding="utf-8"))
            got, 끝난 = d.get("got") or {}, set(d.get("끝난배치") or [])
            print(f"  이어받기 — 지난 실행이 받은 배치 {len(끝난)}개 · {len(got)}곳", file=sys.stderr)
        except (OSError, ValueError):
            got, 끝난 = {}, set()
    batches = [codes[i:i + BATCH] for i in range(0, len(codes), BATCH)]
    for n, b in enumerate(batches, 1):
        열쇠 = ",".join(b[:1] + b[-1:]) + ":%d" % len(b)
        if 열쇠 in 끝난:
            continue
        url = (f"{API}/fnlttMultiAcnt.json?crtfc_key={_key()}"
               f"&corp_code={','.join(b)}&bsns_year={year}"
               f"&reprt_code={reprt}&fs_div={fs_div}")
        import json
        try:
            r = json.loads(_get(url).decode("utf-8"))
        except Exception as e:                        # noqa: BLE001
            print(f"  배치 {n}/{len(batches)} 실패 — {e}", file=sys.stderr)
            misses.extend(b)
            continue
        if r.get("status") not in ("000", "013"):
            print(f"  배치 {n}/{len(batches)} status={r.get('status')} {r.get('message')}",
                  file=sys.stderr)
        for item in r.get("list", []):
            got.setdefault(item["corp_code"], []).append(item)
        print(f"  배치 {n}/{len(batches)} — 누적 {len(got)}곳", file=sys.stderr)
        if 진행:
            끝난.add(열쇠)
            os.makedirs(os.path.dirname(진행) or ".", exist_ok=True)
            json.dump({"got": got, "끝난배치": sorted(끝난)}, open(진행, "w", encoding="utf-8"), ensure_ascii=False)
        time.sleep(PAUSE)
    return got, misses


def _num(s):
    try:
        return int(str(s).replace(",", ""))
    except (ValueError, TypeError):
        return None


def pick(items, want_cfs: bool = True, reprt: str = "11011"):
    """주요계정 목록에서 쓸 계정만 골라낸다. 못 찾으면 비운다 — 채우지 않는다.

    걸리는 자리가 셋이다.

    **영. `--half` 로 받으면 손익이 3개월이다. 누계가 아니다.**
    반기·분기 보고서에서 `thstrm_amount` 는 그 분기 3개월치이고 누계는
    `thstrm_add_amount` 에 있다(실측: SGC에너지 2026 반기 수익 5,770억 대 1조 1,884억).
    매출을 규모대 컷의 잣대로 쓰는데 어떤 해는 연간, 어떤 해는 3개월이면
    **규모대가 통째로 어긋난다.** 반기·분기면 누계 칸을 쓴다.

    하나, **`fs_div=CFS` 로 받아도 별도재무제표 행이 섞여 온다.** 회신의 `fs_nm` 이
    「연결재무제표」인지 「재무제표」인지를 보고 골라야 한다. 그냥 첫 행을 집으면
    어떤 회사는 연결, 어떤 회사는 별도가 들어가 표가 조용히 섞인다.

    둘, **표시통화가 회사마다 다르다.** `currency` 가 KRW 가 아닌 회사가 있다
    (두산밥캣은 USD 로 공시한다). 금액을 그대로 나란히 놓으면 자릿수가 어긋난다.
    **여기서 환산하지 않고 통화를 그대로 실어 보낸다** — 환산에는 적용 환율과
    기준일이 붙어야 하고, 그것은 이 스크립트가 정할 일이 아니다.
    """
    fs_want = "연결재무제표" if want_cfs else "재무제표"
    rows = [it for it in items if (it.get("fs_nm") or "").strip() == fs_want] or items
    누계쓴다 = reprt in ("11012", "11013", "11014")
    손익라벨 = ("매출액", "영업이익", "당기순이익")
    row = {}
    for label, names in WANT:
        val = None
        for it in rows:
            nm = (it.get("account_nm") or "").strip()
            if nm in names:
                if 누계쓴다 and label in 손익라벨:
                    val = _num(it.get("thstrm_add_amount"))
                    if val is None:
                        val = _num(it.get("thstrm_amount"))
                else:
                    val = _num(it.get("thstrm_amount"))
                break
        row[label] = val
    row["표시통화"] = (rows[0].get("currency") or "").strip() if rows else ""
    row["재무제표구분"] = (rows[0].get("fs_nm") or "").strip() if rows else ""
    return row


def main() -> None:
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--year", type=int, default=dt.date.today().year - 1)
    ap.add_argument("--half", action="store_true", help="반기보고서로 받는다")
    ap.add_argument("--ofs", action="store_true", help="별도재무제표로 받는다")
    ap.add_argument("--since", default=None,
                    help="이 날짜 뒤에 갱신된 회사만. **기본은 거르지 않는다(전수)** — "
                         "이 필터는 살아 있는 상장사도 떨군다")
    ap.add_argument("--대상", default=None,
                    help="대상회사 고유번호(쉼표). --since 로 이 회사가 걸러지면 죽는다")
    ap.add_argument("--codes", default=None,
                    help="고유번호를 쉼표로. 후보만 다시 받을 때")
    ap.add_argument("--out", default=None)
    ap.add_argument("--refresh", action="store_true", help="고유번호 대조표를 다시 받는다")
    ap.add_argument("--새로", action="store_true",
                    help="공용 캐시에 같은 해 전수 파일이 있어도 다시 받는다(기본은 캐시를 쓴다 — 2026-10-24 W15)")
    a = ap.parse_args()

    reprt = REPRT["half"] if a.half else REPRT["annual"]
    fs_div = "OFS" if a.ofs else "CFS"
    # **기본을 「거르지 않음」으로 둔다.** 예전 기본(2년)은 헛호출을 줄이려던 것인데,
    # 실측에서 대상회사(삼화전자공업 modify_date 20221103)와 실제 핵심 표본 둘이
    # 그 필터에 걸려 사라졌다. 600곳을 더 받아도 100곳씩 묶으므로 호출 6회 차이다.
    # **정확성을 6회에 판 것이라 되돌린다.**
    since = a.since

    전수 = not a.codes and not since and not a.ofs
    전수이름 = f"상장사_주요계정_{a.year}{'_반기' if a.half else ''}.csv"
    # **공용 캐시에 같은 해 전수 파일이 있으면 다시 받지 않는다**(2026-10-24 W15 · 유니버스 조사 시범 — 캐시가 있는데 전 상장사를 새로 받다
    # 400초 제한에서 23/41 배치에 끊겨 C1 상한을 넘겼다). 키트 캐시 규약(찾는 순서 회차 → 공용 캐시 → 네트워크)과 같다. --새로 면 다시 받는다.
    공 = os.path.join(공용C1(), 전수이름)
    if 전수 and not a.새로 and not a.out and os.path.exists(공):
        import shutil
        if os.path.abspath(공) != os.path.abspath(전수이름):
            shutil.copyfile(공, 전수이름)
        print(f"공용 캐시에서 가져왔다 — {공}(만든날 {dt.date.fromtimestamp(os.path.getmtime(공))}) · 다시 받으려면 --새로", file=sys.stderr)
        if a.대상:
            with open(전수이름, encoding="utf-8-sig") as f:
                있는 = {r.get("고유번호", "").zfill(8) for r in csv.DictReader(f)}
            빠진 = [c.strip().zfill(8) for c in a.대상.split(",") if c.strip() and c.strip().zfill(8) not in 있는]
            if 빠진:
                print(f"  대상 {','.join(빠진)} 가 캐시 파일에 없다 — 그것만 받아 덧붙인다", file=sys.stderr)
                by_code = {r["corp_code"]: r for r in corp_index(a.refresh)}
                g2, _m2 = fetch(빠진, a.year, reprt, fs_div)
                cols = (["회사명", "종목코드", "고유번호", "표시통화", "재무제표구분"] + [w[0] for w in WANT] + ["영업이익률", "부채비율"])
                with open(전수이름, "a", newline="", encoding="utf-8-sig") as f:
                    w = csv.DictWriter(f, fieldnames=cols)
                    for code, items in g2.items():
                        row = pick(items, want_cfs=True, reprt=reprt)
                        meta = by_code.get(code, {})
                        rev, op, debt, eq = row.get("매출액"), row.get("영업이익"), row.get("부채총계"), row.get("자본총계")
                        row.update({"회사명": meta.get("corp_name", ""), "종목코드": meta.get("stock_code", ""), "고유번호": code,
                                    "영업이익률": round(op / rev, 4) if rev and op is not None and rev != 0 else "",
                                    "부채비율": round(debt / eq, 4) if eq and debt is not None and eq != 0 else ""})
                        w.writerow(row)
        print(f"→ {전수이름}", file=sys.stderr)
        return


    index = corp_index(a.refresh)
    by_code = {r["corp_code"]: r for r in index}

    if a.codes:
        # 고유번호는 8자리 문자열이다. 어디서 오다 앞자리 0이 떨어졌어도 되살린다
        codes = [c.strip().zfill(8) for c in a.codes.split(",") if c.strip()]
        print(f"지정한 {len(codes)}곳을 받습니다.", file=sys.stderr)
    elif not since:
        codes = [r["corp_code"] for r in index]
        print(f"고유번호 대조표 {len(index)}건 전부를 받습니다(거르지 않음). "
              f"자료가 없는 회사는 미확보_고유번호.csv 로 나옵니다.", file=sys.stderr)
    else:
        rows, dropped = live_only(index, since)
        codes = [r["corp_code"] for r in rows]
        with open("필터제외_고유번호.csv", "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(["고유번호", "회사명", "종목코드", "modify_date"])
            for r in dropped:
                w.writerow([r["corp_code"], r["corp_name"], r["stock_code"], r["modify_date"]])
        # **대상회사가 필터에 걸리면 조용히 가지 않고 죽는다.** 대상회사가 자기 유사기업
        # 표에서 빠지면 매출·시총 규모대의 기준값 자체가 안 나오는데, 표는 멀쩡해 보인다.
        if a.대상:
            잃음 = {c.strip().zfill(8) for c in a.대상.split(",") if c.strip()}
            걸림 = [r for r in dropped if r["corp_code"] in 잃음]
            if 걸림:
                sys.exit("--since %s 가 대상회사를 걸러냈습니다: %s\n"
                         "이대로 가면 대상회사가 자기 유사기업 표에서 빠집니다. "
                         "--since 를 빼고(전수) 다시 돌리십시오."
                         % (since, ", ".join(r["corp_name"] for r in 걸림)))
        print(f"고유번호 대조표 {len(index)}건 중 {since} 이후 갱신 {len(codes)}건. "
              f"나머지 {len(dropped)}건은 상장폐지 추정으로 뺐고 → 필터제외_고유번호.csv. "
              f"**modify_date 는 상장 상태가 아니라 정보 갱신일이라 살아 있는 회사도 섞일 수 "
              f"있습니다** — 유사기업 후보가 이 목록에 있으면 --codes 로 따로 받으십시오.",
              file=sys.stderr)

    t0 = time.time()
    진행 = os.path.join(CACHE, "진행_%d_%s_%s_%s.json" % (a.year, reprt, fs_div, "전수" if 전수 else "일부")) if (전수 or len(codes) > BATCH) else None
    got, misses = fetch(codes, a.year, reprt, fs_div, 진행=진행)
    print(f"{len(got)}곳 확보 · {time.time() - t0:.0f}초 · 호출 {(len(codes) + BATCH - 1) // BATCH}회",
          file=sys.stderr)

    # --codes 보충 실행이 전수 파일을 덮지 않게 이름을 가른다
    if a.out:
        # **--out 이 그 장치를 무력화한다.** 실측: 후보 22곳을 받으면서 --out 으로
        # 전수 파일 이름을 줘 2,789행을 22행으로 덮었다(다시 받아 복구). 거부한다.
        if a.codes and os.path.basename(a.out).startswith("상장사_주요계정"):
            sys.exit("--codes 로 일부만 받으면서 전수 파일 이름(%s)에 쓰려 합니다.\n"
                     "전수 결과를 덮어씁니다. --out 을 빼거나 다른 이름을 주십시오."
                     % os.path.basename(a.out))
        out = a.out
    elif a.codes:
        out = f"보충_주요계정_{a.year}{'_반기' if a.half else ''}.csv"
    else:
        out = f"상장사_주요계정_{a.year}{'_반기' if a.half else ''}.csv"
    if not got:
        print("0곳 확보 — 파일을 쓰지 않습니다. 고유번호·연도·보고서 구분을 확인하십시오.",
              file=sys.stderr)
        if misses:
            with open("미확보_고유번호.csv", "w", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f)
                w.writerow(["고유번호", "회사명", "종목코드", "원인"])
                for c in misses:
                    m = by_code.get(c, {})
                    w.writerow([c, m.get("corp_name", ""), m.get("stock_code", ""), "배치 조회 실패"])
        return
    cols = (["회사명", "종목코드", "고유번호", "표시통화", "재무제표구분"]
            + [w[0] for w in WANT] + ["영업이익률", "부채비율"])
    nonkrw = []
    with open(out, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for code, items in got.items():
            meta = by_code.get(code, {})
            row = pick(items, want_cfs=not a.ofs, reprt=reprt)
            if row.get("표시통화") not in ("KRW", ""):
                nonkrw.append(f"{meta.get('corp_name','')}({row.get('표시통화')})")
            rev, op = row.get("매출액"), row.get("영업이익")
            debt, eq = row.get("부채총계"), row.get("자본총계")
            row.update({
                "회사명": meta.get("corp_name", ""),
                "종목코드": meta.get("stock_code", ""),
                "고유번호": code,
                "영업이익률": round(op / rev, 4) if rev and op is not None and rev != 0 else "",
                "부채비율": round(debt / eq, 4) if eq and debt is not None and eq != 0 else "",
            })
            w.writerow(row)
    print(f"→ {out}", file=sys.stderr)
    if 진행 and os.path.exists(진행) and not misses:
        os.remove(진행)                                   # 다 받았다 — 이어받기 기록을 걷는다
    if 전수 and not a.out and not misses and len(got) > 1000:   # 전수를 받았으면 공용 캐시에도 둔다 — 다음 회사는 받지 않는다
        try:
            import shutil
            os.makedirs(공용C1(), exist_ok=True)
            shutil.copyfile(out, os.path.join(공용C1(), os.path.basename(out)))
            print(f"공용 캐시에도 둠 — {os.path.join(공용C1(), os.path.basename(out))}", file=sys.stderr)
        except OSError as e:
            print(f"공용 캐시에 두지 못함({type(e).__name__})", file=sys.stderr)

    if nonkrw:
        print(f"표시통화가 원화가 아닌 회사 {len(nonkrw)}곳: {', '.join(nonkrw[:12])}"
              f"{' 외' if len(nonkrw) > 12 else ''}\n"
              f"  **금액을 그대로 나란히 놓지 마십시오.** 환산하려면 적용 환율과 "
              f"기준일을 함께 적습니다. 비율(영업이익률·부채비율)은 통화와 무관합니다.",
              file=sys.stderr)

    # 요청했는데 회신에 없는 회사 — 조용히 빼지 않는다. 표본에서 대형 이웃이
    # 소리 없이 빠지면 무차입 베타가 통째로 기운다 (실측: 엔씨소프트가 이렇게 빠졌다)
    absent = [c for c in codes if c not in got and c not in misses]
    if absent or misses:
        with open("미확보_고유번호.csv", "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(["고유번호", "회사명", "종목코드", "원인"])
            for c in misses:
                meta = by_code.get(c, {})
                w.writerow([c, meta.get("corp_name", ""), meta.get("stock_code", ""), "배치 조회 실패"])
            for c in absent:
                meta = by_code.get(c, {})
                w.writerow([c, meta.get("corp_name", ""), meta.get("stock_code", ""),
                            "회신에 없음 (해당 연도 미제출·폐지·데이터 부재)"])
        names = [by_code.get(c, {}).get("corp_name", c) for c in (misses + absent)[:8]]
        print(f"미확보 {len(misses) + len(absent)}건 → 미확보_고유번호.csv "
              f"(예: {', '.join(names)}{' 외' if len(misses) + len(absent) > 8 else ''}) — "
              f"조용히 빼지 말고, 유사기업 후보가 여기 있으면 그 회사만 따로 다시 받으십시오",
              file=sys.stderr)


if __name__ == "__main__":
    main()

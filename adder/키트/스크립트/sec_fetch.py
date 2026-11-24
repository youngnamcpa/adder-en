# -*- coding: utf-8 -*-
"""SEC 원천 조회 — 티커→CIK 역조회, 제출 이력, companyfacts 를 _raw/ 에 저장한다.

규칙: 재무제표 수치는 SEC XBRL 에서만 받는다. 웹 검색값을 쓰지 않는다.
CIK 를 기억으로 적지 않는다 — company_tickers.json 에서 역조회한다.
User-Agent 의 연락처는 환경변수 SEC_CONTACT_EMAIL 에서 읽고 화면에 출력하지 않는다.
SEC 는 브라우저 흉내 없는 요청을 403 으로 막는다. 이 스크립트로만 간다.

사용:  python 스크립트/sec_fetch.py --ticker PLTR --기준일 2026-06-30
       python 스크립트/sec_fetch.py --ticker PLTR --가정 가정.json        # 날짜는 가정에서(재무기준일 F · 평가기준일 T)

**날짜 둘(2026-10-25 · `기준일.py`).** `--기준일`(별칭 `--재무기준일`)은 **재무기준일 F** 다 — 평가기준일 전에 제출된 마지막 정기 보고의
기간 끝. 아래 「기준일」 은 모두 F 다(지금 뜻 그대로). `--평가기준일`(T · 분석일)은 받기를 바꾸지 않고 재무기준일 점검에만 쓴다 —
F 의 보고가 T 뒤에 제출됐거나 T 전에 더 늦은 정기 보고가 제출됐으면 `sec_공시고르기.json` 의 경보에 적는다.

`--기준일` 을 주면(2026-10-25 FX-C · 뿌리 R7) **기준일을 담은 분기 보고**를 반드시 받는다 — 기간 끝 ≤ 기준일 + 7일(52/53주 결산) 가운데
가장 늦은 정기 보고(10-Q · 10-K · 20-F · 40-F — 제출이 기준일 뒤여도 그 기간을 담았으면 첫 출처) + 그 직전 보고 + 기준일 앞 마지막 연차 보고 +
기준일 뒤 첫 정기 보고 하나(「평가기준일 뒤 정보」 — 값 칸에 섞지 않는다). 해외 발행사(20-F · 40-F)는 기준일 분기 실적이 6-K 로 오므로
기준일 − 30일 ~ + 120일에 낸 6-K 의 첨부(EX-99)를 열어 기준일 분기를 담은 것만 남긴다. 무엇을 왜 받았는지 `_raw/sec_공시고르기.json` 에 적는다.
`--기준일` 이 없으면 옛 동작(최신 10-K · 10-Q 하나씩) — 기준일 뒤 10-Q 만 씨앗에 남는 사고(F12 · F24 · F29 · F43 · F44)가 이 자리에서 났다.

`--신고서` 를 주면(2026-10-25 Y1 · 설계 `연구/재무이력없음_20261025/02_설계.md` 2-1) 등록 신고서 하나를 더 받는다 — 정기보고서에 연간 재무가
3해 미만인 회사(상장 직후 · 분할 신설)의 감사받은 연간 재무가 여기 있다. submissions 에서 S-1 · S-1/A · F-1 · F-1/A · 424B1 · 424B4 · 10-12B(· /A)
가운데 제출이 기준일 이하인 것을 찾아, 마지막 공모 회차(가장 늦은 제출에서 180일 안)의 확정 판을 고른다 — 424B4 > 424B1 > 최신 S-1/A · F-1/A
> S-1 · F-1 · 10-12B. DRS(비공개 초안)는 열지 않는다. `_raw/신고서_<양식>_<접수번호>.htm`(양식의 「/」 는 뺀다 — S-1/A → S-1A)으로 두고
`htm2txt.py` 로 글(.txt)을 만든다. 무엇을 왜 골랐는지 `_raw/sec_공시고르기.json` 의 「신고서」 에 덧붙인다. 표 읽기는 `신고서재무.py`.
스위치가 없으면 신고서를 받지 않는다(옛 동작 그대로). 신고서만 있고 XBRL 이 아직 없는 회사는 companyfacts 가 없을 수 있어 그때는 멈추지 않고 적는다.
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys
import time

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "_raw")
# 폴더는 본체 판정 뒤에 만든다(main) — import 때 만들면 멈추기도 전에 본체에 빈 `_raw/` 가 생긴다(S1 리뷰)

HEAD = HEAD_DATA = None
log = []


def _머리():
    """연락처를 환경변수에서 읽어 머리를 짓는다 — 없으면 멈춘다(값은 화면에 적지 않는다). import 때가 아니라 main 에서(시험이 import 할 수 있게)."""
    global HEAD, HEAD_DATA
    contact = os.environ.get("SEC_CONTACT_EMAIL")
    if not contact:
        sys.exit("환경변수 SEC_CONTACT_EMAIL 이 없습니다. 값은 화면에 적지 마십시오.")
    HEAD = {"User-Agent": "DCF-research %s" % contact, "Accept-Encoding": "gzip, deflate", "Host": "www.sec.gov"}
    HEAD_DATA = dict(HEAD)
    HEAD_DATA["Host"] = "data.sec.gov"


def get(url, headers, tries=4):
    import requests                                           # noqa: PLC0415 — 시험은 네트워크 없이 import 한다
    for i in range(tries):
        try:
            r = requests.get(url, headers=headers, timeout=60)
            if r.status_code == 200:
                return r
            log.append("HTTP %d %s" % (r.status_code, url))
        except requests.RequestException as e:
            log.append("ERR %s %s" % (type(e).__name__, url))
        time.sleep(1.5 * (i + 1))
    return None


def _본체면멈춘다(뿌리):
    """**본체에서 원본을 받으면 정본이 더러워진다.** 회차 폴더에서 돌린다 — 판정은 `본체가드.py`
    (폴더 이름 「시작키트」 · 저장소 안의 회귀기준선 본체). 종전에는 이름 하나만 봤다(S1 리뷰)."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import 본체가드                                          # noqa: PLC0415
    본체가드.본체면멈춘다(뿌리)


def _원문받기(cik, 행, 이름, 받은):
    """정기 보고 원문 하나 → `_raw/<이름>` — 이미 있으면 받지 않는다(같은 accession 은 바뀌지 않는다)."""
    p = os.path.join(OUT, 이름)
    if os.path.exists(p) and os.path.getsize(p) > 1000:
        받은.append({"파일": 이름, "받음": "이미 있음"})
        return True
    url = "https://www.sec.gov/Archives/edgar/data/%d/%s/%s" % (cik, 행["accession"].replace("-", ""), 행["문서"])
    r = get(url, HEAD)
    if r is None:
        log.append("%s 원문 다운로드 실패: %s" % (행["양식"], url))
        받은.append({"파일": 이름, "받음": "실패"})
        return False
    with io.open(p, "w", encoding="utf-8", errors="ignore") as f:
        f.write(r.text)
    받은.append({"파일": 이름, "받음": "새로"})
    time.sleep(0.3)
    return True


신고서양식 = ("S-1", "S-1/A", "F-1", "F-1/A", "424B1", "424B4", "10-12B", "10-12B/A")
신고서우선 = {"424B4": 0, "424B1": 1, "S-1/A": 2, "F-1/A": 2, "10-12B/A": 2, "S-1": 3, "F-1": 3, "10-12B": 3}
신고서회차일 = 180                                     # 마지막 제출에서 이만큼 안이면 같은 공모 회차로 본다


def 신고서파일이름(양식, accession):
    """`신고서_424B4_0001628280-26-042639.htm` — 양식의 「/」 는 뺀다(S-1/A → S-1A)."""
    return "신고서_%s_%s.htm" % ((양식 or "").replace("/", ""), accession)


def 신고서고르기(sub, 기준일=None, 회차일=신고서회차일):
    """submissions → {"고른": 행 | None, "후보": [행…], "뒤": [행…], "고른까닭": 글, "경보": […]}. 네트워크 없음(시험이 부른다).
    · 후보 = 신고서 양식 가운데 제출일 ≤ 기준일(기준일이 없으면 전부)
    · 회차 = 가장 늦은 후보 제출일에서 회차일 안 — 몇 해 전 상장 신고서보다 최근 증자 신고서가 앞선다
    · 고른 = 회차 안에서 우선순위(424B4 > 424B1 > S-1/A · F-1/A · 10-12B/A > S-1 · F-1 · 10-12B), 같은 순위면 늦은 제출"""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import 미국원천읽기 as U                                  # noqa: PLC0415
    표 = U.공시표(sub)
    모두 = [r for r in 표 if r["양식"] in 신고서양식 and r.get("제출일")]
    후보 = [r for r in 모두 if not 기준일 or r["제출일"] <= 기준일]
    낸 = {"고른": None, "후보": [], "뒤": [r for r in 모두 if 기준일 and r["제출일"] > 기준일], "고른까닭": None, "경보": []}
    if not 후보:
        낸["경보"].append("기준일(%s) 앞 신고서(%s)가 submissions 에 없다%s" % (
            기준일 or "없음", " · ".join(신고서양식), " — recent 밖의 옛 쪽(filings.files)은 보지 않았다" if ((sub or {}).get("filings") or {}).get("files") else ""))
        return 낸
    최근 = max(U.날(r["제출일"]) for r in 후보)
    회차 = [r for r in 후보 if (최근 - U.날(r["제출일"])).days <= 회차일]
    고른 = min(회차, key=lambda r: (신고서우선.get(r["양식"], 9), -U.날(r["제출일"]).toordinal()))
    낸["후보"] = sorted(후보, key=lambda r: r["제출일"], reverse=True)
    낸["고른"] = dict(고른)
    낸["고른까닭"] = ("기준일(%s) 앞 신고서 %d건 · 마지막 공모 회차(%s ~ %s, %d건)의 확정 판 %s(제출 %s) — 우선 424B4 > 424B1 > 최신 S-1/A · F-1/A > "
                  "S-1 · F-1 · 10-12B · DRS(비공개 초안)는 열지 않는다" % (
                      기준일 or "없음", len(후보), min(r["제출일"] for r in 회차), 최근.isoformat(), len(회차), 고른["양식"], 고른["제출일"]))
    if 낸["뒤"]:
        낸["경보"].append("기준일 뒤 신고서 %d건(%s) — 값 칸에 쓰지 않는다" % (len(낸["뒤"]), " · ".join("%s %s" % (r["양식"], r["제출일"]) for r in 낸["뒤"][:3])))
    return 낸


def _신고서받기(cik, sub, 기준일, 받은):
    """신고서 하나를 받아 글로 바꾼다 → sec_공시고르기.json 의 「신고서」 칸."""
    import subprocess                                         # noqa: PLC0415
    고름 = 신고서고르기(sub, 기준일)
    칸 = {"고른": None, "후보": [{"양식": r["양식"], "제출일": r["제출일"], "accession": r["accession"]} for r in 고름["후보"][:12]],
         "고른까닭": 고름["고른까닭"], "경보": list(고름["경보"])}
    행 = 고름["고른"]
    if not 행:
        return 칸
    이름 = 신고서파일이름(행["양식"], 행["accession"])
    ok = _원문받기(cik, 행, 이름, 받은)
    글 = None
    if ok:
        txt = os.path.join(OUT, 이름[:-4] + ".txt")
        if not (os.path.exists(txt) and os.path.getmtime(txt) >= os.path.getmtime(os.path.join(OUT, 이름))):
            환 = dict(os.environ, PYTHONIOENCODING="utf-8")
            r = subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "htm2txt.py"), 이름[:-4]],
                               capture_output=True, text=True, encoding="utf-8", errors="replace", env=환)
            if r.returncode != 0:
                칸["경보"].append("htm2txt 실패 — %s" % ((r.stderr or r.stdout or "").strip().splitlines() or ["?"])[-1][:200])
        if os.path.exists(txt):
            글 = os.path.basename(txt)
    else:
        칸["경보"].append("신고서 원문 다운로드 실패 — %s %s" % (행["양식"], 행["accession"]))
    칸["고른"] = {"양식": 행["양식"], "제출일": 행["제출일"], "accession": 행["accession"], "문서": 행["문서"],
                "파일": 이름 if ok else None, "글": 글, "고른까닭": 고름["고른까닭"]}
    return 칸


def _6K받기(cik, 후보들, 기준일, 상한, 판):
    """해외 발행사 6-K → 첨부(EX-99 · 본문)를 열어 기준일 분기를 담은 것만 `_raw/6K_<제출일>_<n>.htm` 으로 남긴다."""
    import 미국원천읽기 as U                                  # noqa: PLC0415
    남긴, 본 = [], []
    for 행 in 후보들[:상한]:
        acc = 행["accession"].replace("-", "")
        r = get("https://www.sec.gov/Archives/edgar/data/%d/%s/index.json" % (cik, acc), HEAD)
        time.sleep(0.3)
        if r is None:
            본.append({"accession": 행["accession"], "제출일": 행["제출일"], "결과": "목록 못 받음"})
            continue
        이름들 = [x.get("name") for x in ((r.json().get("directory") or {}).get("item") or [])]
        첨부 = [n for n in 이름들 if n and re.search(r"(?i)\.htm", n) and (re.search(r"(?i)ex[-_]?99", n) or n == 행["문서"])]
        맞음 = False
        for k, n in enumerate(첨부[:4]):
            r2 = get("https://www.sec.gov/Archives/edgar/data/%d/%s/%s" % (cik, acc, n), HEAD)
            time.sleep(0.3)
            if r2 is None:
                continue
            if U.기준일6K인가(U.글로(r2.text)[:200000], 기준일):
                이름 = "6K_%s_%d.htm" % ((행["제출일"] or "").replace("-", ""), k + 1)
                with io.open(os.path.join(OUT, 이름), "w", encoding="utf-8", errors="ignore") as f:
                    f.write(r2.text)
                남긴.append(이름)
                맞음 = True
        본.append({"accession": 행["accession"], "제출일": 행["제출일"], "결과": "기준일 분기 담음" if 맞음 else "기준일 분기 아님"})
    판["6K검사"] = 본
    return 남긴


정기양식 = ("10-K", "10-Q", "20-F", "40-F", "10-K/A", "10-Q/A", "20-F/A", "40-F/A", "10-KT", "10-QT")


def 재무기준일점검(sub, 기준일, 평가기준일):
    """submissions 의 정기 보고(기간 끝 · 제출일)로 재무기준일 F 를 평가기준일 T 와 대 본다 → 경보 글 목록(T 가 없거나 F = T 면 빈 목록).
    규칙은 `기준일인자.재무기준일점검` 하나다."""
    if not 평가기준일 or 평가기준일 == 기준일:
        return []
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import 기준일인자                                         # noqa: PLC0415
    rec = ((sub or {}).get("filings") or {}).get("recent") or {}
    보고들 = []
    for i, f in enumerate(rec.get("form") or []):
        if f not in 정기양식:
            continue
        try:
            보고들.append({"기간끝": rec["reportDate"][i], "제출일": rec["filingDate"][i],
                        "이름": "%s %s" % (f, rec["accessionNumber"][i])})
        except (KeyError, IndexError):
            continue
    return 기준일인자.재무기준일점검(기준일, 평가기준일, 보고들)


def main():
    _본체면멈춘다(os.path.dirname(OUT))
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--ticker", required=True, help="예: PLTR")
    ap.add_argument("--기준일", "--재무기준일", dest="기준일",
                    help="재무기준일 F YYYY-MM-DD — 주면 기준일 분기 보고 · 직전 · 연차 · 뒤 첫 보고를 고른다(없으면 최신 둘). "
                         "평가기준일 전에 제출된 마지막 정기 보고의 기간 끝 · 옛 이름 --기준일 은 지금 뜻 그대로다")
    ap.add_argument("--평가기준일", default=None,
                    help="평가기준일 T YYYY-MM-DD(분석일) — 받기는 바꾸지 않는다. 재무기준일 점검(경보)에만 쓴다")
    ap.add_argument("--가정", default=None, help="가정 파일 — 날짜 인자를 비우면 기준일.py 로 F · T 를 푼다(F 가 없으면 F = T)")
    ap.add_argument("--6K상한", dest="육상한", type=int, default=12, help="해외 발행사 6-K 를 몇 건까지 열어 볼지(기본 12)")
    ap.add_argument("--신고서", action="store_true",
                    help="등록 신고서(S-1 · F-1 · 424B · 10-12B) 확정 판 하나를 더 받는다 — 기준일 앞 마지막 회차 · 표 읽기는 신고서재무.py")
    a = ap.parse_args()
    if a.가정 or a.평가기준일:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import 기준일인자                                     # noqa: PLC0415
        a.기준일 = 기준일인자.풀기(a.기준일, a.가정, 기준일인자.재무, 인자="--기준일")
        a.평가기준일 = 기준일인자.풀기(a.평가기준일, a.가정, 기준일인자.평가, 인자="--평가기준일")
    _머리()
    os.makedirs(OUT, exist_ok=True)
    ticker = a.ticker.upper()

    # 1) 티커 → CIK (기억으로 적지 않는다)
    r = get("https://www.sec.gov/files/company_tickers.json", HEAD)
    if r is None:
        sys.exit("company_tickers.json 조회 실패\n" + "\n".join(log))
    cik = name = None
    for _, v in r.json().items():
        if v["ticker"].upper() == ticker:
            cik = int(v["cik_str"]); name = v["title"]
            break
    if cik is None:
        sys.exit("티커 %s 를 company_tickers.json 에서 못 찾음" % ticker)
    cik10 = "%010d" % cik
    log.append("CIK 확인: %s = %d (%s)" % (ticker, cik, name))
    time.sleep(0.3)

    # 2) submissions — 평가기준일 판정용 (보고서가 실제로 접수됐는지)
    r = get("https://data.sec.gov/submissions/CIK%s.json" % cik10, HEAD_DATA)
    if r is None:
        sys.exit("submissions 조회 실패\n" + "\n".join(log))
    sub = r.json()
    with io.open(os.path.join(OUT, "submissions.json"), "w", encoding="utf-8") as f:
        json.dump(sub, f, ensure_ascii=False)
    rec = sub["filings"]["recent"]
    log.append("")
    log.append("최근 제출 서류 (form / 기준일 / 접수일 / accession / 문서)")
    shown = 0
    for i in range(len(rec["form"])):
        if rec["form"][i] in ("10-K", "10-Q", "8-K", "20-F", "40-F", "6-K", "DEF 14A") and shown < 28:
            log.append("  %-8s %-11s %-11s %-22s %s" % (
                rec["form"][i], rec["reportDate"][i], rec["filingDate"][i],
                rec["accessionNumber"][i], rec["primaryDocument"][i]))
            shown += 1
    time.sleep(0.3)

    # 3) companyfacts — 통째로 한 번만. 유사기업 갈래는 이 파일을 읽기만 한다
    r = get("https://data.sec.gov/api/xbrl/companyfacts/CIK%s.json" % cik10, HEAD_DATA)
    if r is None and not a.신고서:
        sys.exit("companyfacts 조회 실패\n" + "\n".join(log))
    if r is None:
        log.append("※ companyfacts 조회 실패 — XBRL 이 아직 없는 회사일 수 있다(신고서만 받는다)")
    cf = r.json() if r is not None else {"facts": {}}
    p = os.path.join(OUT, "companyfacts.json")
    if r is not None:                                         # 받지 못했으면 빈 파일을 쓰지 않는다(「사실 0건」 으로 읽히지 않게)
        with io.open(p, "w", encoding="utf-8") as f:
            json.dump(cf, f, ensure_ascii=False)
    tags_us = sorted(cf.get("facts", {}).get("us-gaap", {}).keys())
    tags_ifrs = sorted(cf.get("facts", {}).get("ifrs-full", {}).keys())
    tags_dei = sorted(cf.get("facts", {}).get("dei", {}).keys())
    log.append("")
    if r is not None:
        log.append("companyfacts 저장: %s (%.1f MB)" % (p, os.path.getsize(p) / 1e6))
    log.append("us-gaap 태그 수: %d / ifrs-full 태그 수: %d / dei 태그 수: %d — 태그는 가정하지 말고 훑어서 고른다"
               % (len(tags_us), len(tags_ifrs), len(tags_dei)))
    # ── 법인 승계 감지 — 실측(XOM): 2026-07 지주 재편으로 티커가 새 CIK
    # (ExxonMobil Holdings·94태그·제출 이력 두 달)로 넘어가 과거가 통째로 없는
    # 회사처럼 보였다. 신호 둘이 겹치면 구 법인 CIK 를 확인하라고 알린다.
    _신호 = []
    if len(tags_us) + len(tags_ifrs) < 150:
        _신호.append("us-gaap · ifrs-full 태그 %d개(정상 대형주는 수백)" % (len(tags_us) + len(tags_ifrs)))
    _접수일들 = rec.get("filingDate") or []
    if _접수일들 and min(_접수일들) > "2024-01-01":
        _신호.append("제출 이력 시작이 %s(2년 미만)" % min(_접수일들))
    if "8-K12B" in (rec.get("form") or []):
        _신호.append("8-K12B(승계 상장) 존재")
    if len(_신호) >= 2:
        log.append("")
        log.append("※ **법인 승계 의심 — %s.** 티커가 재편된 새 법인을 가리키면 "
                   "과거 재무가 통째로 비어 보입니다. EDGAR 전체회사 검색에서 같은 "
                   "이름의 **구 CIK** 를 찾아 companyfacts 를 별도로 받으십시오"
                   "(sec_원천 `--입력` 으로 결합 — XOM 처방)" % " · ".join(_신호))
    with io.open(os.path.join(OUT, "tags_us_gaap.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(tags_us))
    if tags_ifrs:
        with io.open(os.path.join(OUT, "tags_ifrs_full.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(tags_ifrs))
    with io.open(os.path.join(OUT, "tags_dei.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(tags_dei))

    # 4) 원문 — 서술(부문·리스 주석·유효세율 조정표·약정 · capex 가이던스)은 XBRL 에 없다
    if a.기준일:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import 미국원천읽기 as U                              # noqa: PLC0415
        고름 = U.공시고르기(sub, a.기준일)
        판 = {"형식": "sec공시고르기 1", "티커": ticker, "CIK": cik10, "기준일": a.기준일, "고른": [], "6K검사": [], "경보": list(고름["경보"])}
        if a.평가기준일 and a.평가기준일 != a.기준일:
            판["재무기준일"], 판["평가기준일"] = a.기준일, a.평가기준일
            판["경보"].extend(재무기준일점검(sub, a.기준일, a.평가기준일))
        받은 = []
        본 = set()
        for 역, 행 in [("기준일분기", 고름["기준"]), ("직전", 고름["직전"]), ("연차", 고름["연차"])] + [("뒤", x) for x in 고름["뒤"][:1]]:
            if not 행 or 행["accession"] in 본:
                continue
            본.add(행["accession"])
            이름 = U.파일이름(행["양식"], 행["기간끝"])
            ok = _원문받기(cik, 행, 이름, 받은)
            판["고른"].append({"역할": 역, "양식": 행["양식"], "기간끝": 행["기간끝"], "제출일": 행["제출일"], "accession": 행["accession"],
                             "파일": 이름 if ok else None})
            log.append("%s %-6s 기간 끝 %s · 제출 %s → %s%s" % (역, 행["양식"], 행["기간끝"], 행["제출일"], 이름, "" if ok else "(실패)"))
        if 고름["해외6K후보"]:
            남긴 = _6K받기(cik, 고름["해외6K후보"], a.기준일, a.육상한, 판)
            log.append("6-K %d건 열어 기준일 분기를 담은 첨부 %d개 — %s" % (min(len(고름["해외6K후보"]), a.육상한), len(남긴), " · ".join(남긴) or "없음"))
            if not 남긴:
                판["경보"].append("해외 발행사 — 기준일 분기를 담은 6-K 첨부를 못 찾았다(대만 등 본국 공시로 본선이 메운다)")
        for x in 판["경보"]:
            log.append("※ " + x)
        with io.open(os.path.join(OUT, "sec_공시고르기.json"), "w", encoding="utf-8") as f:
            json.dump(판, f, ensure_ascii=False, indent=1)
    else:
        log.append("※ --기준일 없이 받았다 — 최신 10-K · 10-Q 하나씩. 기준일 분기 보고를 받으려면 --기준일 을 준다")
        got = {}
        for i in range(len(rec["form"])):
            form = rec["form"][i]
            if form in ("10-K", "10-Q", "20-F") and form not in got:
                acc = rec["accessionNumber"][i].replace("-", "")
                doc = rec["primaryDocument"][i]
                url = "https://www.sec.gov/Archives/edgar/data/%d/%s/%s" % (cik, acc, doc)
                r = get(url, HEAD)
                if r is None:
                    log.append("%s 원문 다운로드 실패: %s" % (form, url))
                    continue
                name_out = "%s_%s.htm" % (form.replace("-", ""), rec["reportDate"][i][:7].replace("-", ""))
                with io.open(os.path.join(OUT, name_out), "w", encoding="utf-8",
                             errors="ignore") as f:
                    f.write(r.text)
                got[form] = name_out
                log.append("%s 원문 저장: %s (기준일 %s)" % (form, name_out, rec["reportDate"][i]))
                time.sleep(0.3)
            if len(got) >= 2:
                break

    # 5) 등록 신고서(--신고서) — 정기보고서에 없는 감사 연간 재무. 옛 동작(스위치 없음)은 받지 않는다
    if a.신고서:
        신받은 = []
        칸 = _신고서받기(cik, sub, a.기준일, 신받은)
        g = 칸["고른"]
        if g:
            log.append("신고서 %-8s 제출 %s · %s → %s%s" % (g["양식"], g["제출일"], g["accession"], g["파일"] or "(실패)",
                                                   (" · 글 " + g["글"]) if g.get("글") else ""))
            log.append("  고른 까닭: " + (칸["고른까닭"] or ""))
        for x in 칸["경보"]:
            log.append("※ 신고서 — " + x)
        gp = os.path.join(OUT, "sec_공시고르기.json")
        try:
            with io.open(gp, encoding="utf-8") as f:
                판 = json.load(f)
        except (OSError, ValueError):
            판 = {"형식": "sec공시고르기 1", "티커": ticker, "CIK": cik10, "기준일": a.기준일, "고른": [], "6K검사": [], "경보": []}
        판["신고서"] = 칸
        with io.open(gp, "w", encoding="utf-8") as f:
            json.dump(판, f, ensure_ascii=False, indent=1)

    with io.open(os.path.join(OUT, "_fetch_log.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(log))
    print("\n".join(log))


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""sec_xbrl보충 — SEC companyfacts 가 아직 싣지 않은 정기 공시(XBRL 있음)의 사실을 그 공시의 XBRL 인스턴스에서 읽어 companyfacts 에 보충한다.

**왜 만들었나(2026-10-24 W13 · 유니버스 TSMC 실측).** companyfacts(`data.sec.gov/api/xbrl/companyfacts`)는 SEC 가 공시를 정리해 내는 2차 자료라
늦거나 빠질 때가 있다. 실측(TSM): 2026-04-16 접수 20-F(FY2025 · isXBRL 1)가 2026-10-24 조회한 companyfacts 에 없어 원천 조립(13번)이
FY2024 에서 멈췄다. submissions 의 공시 목록에는 그 20-F 가 XBRL 과 함께 있다 — 그 공시의 인스턴스(`*_htm.xml`)를 직접 읽으면 같은 사실이 나온다.
**회사 · 업종과 무관하다** — 국내 IFRS 외국 발행인(ifrs-full) · 미국 회사(us-gaap) 모두 같은 길이다.

규칙
  · companyfacts 와 같은 꼴로 넣는다 — 차원(축 · 멤버)이 붙은 맥락은 넣지 않는다(companyfacts 도 비차원 사실만 싣는다).
  · 표준 이름공간만(us-gaap · ifrs-full · dei · srt). 회사 확장 태그는 넣지 않는다.
  · 원본은 `companyfacts_원본.json` 으로 한 번 남기고, 보충한 공시는 `_보충` 목록(접수번호 · 양식 · 접수일 · 사실 수 · 주소 · 조회일)에 적는다.
  · 이미 있는 사실(같은 접수번호 · 같은 기간 · 같은 값)은 다시 넣지 않는다. 값을 고치지 않는다 — 더하기만.
  · 연락처는 환경변수 SEC_CONTACT_EMAIL 에서 읽고 찍지 않는다. 초당 열 건 한도 안에서 천천히.

사용:
    python 스크립트/sec_xbrl보충.py                       # _raw/submissions.json · companyfacts.json 을 보고 빠진 정기 공시를 보충
    python 스크립트/sec_xbrl보충.py --최대 2 --확인만       # 무엇이 빠졌는지만
    python 스크립트/sec_xbrl보충.py --인스턴스 파일.xml --접수번호 … --양식 20-F --접수일 2026-04-16   # 받아 둔 인스턴스로(네트워크 없이)
종료 코드 — 0 보충 · 할 일 없음 / 1 받지 못함(까닭 출력) / 2 입력 없음.
"""
from __future__ import annotations

import argparse
import datetime
import io
import json
import os
import re
import shutil
import sys
import time
import xml.etree.ElementTree as ET

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:                                    # noqa: BLE001
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
정기양식 = ("10-K", "10-K/A", "10-Q", "10-Q/A", "20-F", "20-F/A", "40-F", "40-F/A", "10-KT", "20-FR")
연차양식 = ("10-K", "10-K/A", "20-F", "20-F/A", "40-F", "40-F/A", "10-KT", "20-FR")
표준이름공간 = (("fasb.org/us-gaap", "us-gaap"), ("xbrl.ifrs.org", "ifrs-full"), ("xbrl.sec.gov/dei", "dei"), ("fasb.org/srt", "srt"))
_XBRLI = "http://www.xbrl.org/2003/instance"
_XBRLDI = "http://xbrl.org/2006/xbrldi"


def 이름공간(uri):
    for 조각, 이름 in 표준이름공간:
        if 조각 in (uri or ""):
            return 이름
    return None


def _단위글(el):
    """<xbrli:unit> → companyfacts 꼴 단위 이름(TWD · USD · shares · pure · TWD/shares)."""
    def 측(x):
        m = (x.text or "").strip()
        return m.split(":", 1)[1] if ":" in m else m
    분자 = el.find("{%s}divide/{%s}unitNumerator" % (_XBRLI, _XBRLI))
    if 분자 is not None:
        분모 = el.find("{%s}divide/{%s}unitDenominator" % (_XBRLI, _XBRLI))
        a = "*".join(측(x) for x in 분자.findall("{%s}measure" % _XBRLI))
        b = "*".join(측(x) for x in 분모.findall("{%s}measure" % _XBRLI)) if 분모 is not None else ""
        return "%s/%s" % (a, b) if b else a
    return "*".join(측(x) for x in el.findall("{%s}measure" % _XBRLI))


def 파싱(내용):
    """XBRL 인스턴스(바이트) → (사실 [{이름공간, 태그, 단위, start?, end, val}], fy, fp). 차원 맥락 · 확장 태그 · 숫자 아닌 값은 뺀다."""
    뿌리 = ET.fromstring(내용)
    맥락, 단위 = {}, {}
    for c in 뿌리.findall("{%s}context" % _XBRLI):
        차원 = c.find(".//{%s}explicitMember" % _XBRLDI) is not None or c.find(".//{%s}typedMember" % _XBRLDI) is not None \
            or c.find("{%s}scenario" % _XBRLI) is not None
        p = c.find("{%s}period" % _XBRLI)
        if p is None:
            continue
        즉 = p.find("{%s}instant" % _XBRLI)
        if 즉 is not None:
            맥락[c.get("id")] = (None, (즉.text or "").strip()[:10], 차원)
        else:
            s, e = p.find("{%s}startDate" % _XBRLI), p.find("{%s}endDate" % _XBRLI)
            if s is not None and e is not None:
                맥락[c.get("id")] = ((s.text or "").strip()[:10], (e.text or "").strip()[:10], 차원)
    for u in 뿌리.findall("{%s}unit" % _XBRLI):
        단위[u.get("id")] = _단위글(u)
    사실, fy, fp = [], None, None
    for el in 뿌리:
        if not isinstance(el.tag, str) or not el.tag.startswith("{"):
            continue
        uri, 태그 = el.tag[1:].split("}", 1)
        ns = 이름공간(uri)
        if ns is None or el.get("contextRef") is None:
            continue
        글 = (el.text or "").strip()
        if ns == "dei" and 태그 == "DocumentFiscalYearFocus" and 글:
            fy = 글[:4]
        if ns == "dei" and 태그 == "DocumentFiscalPeriodFocus" and 글:
            fp = 글
        if el.get("{http://www.w3.org/2001/XMLSchema-instance}nil") == "true" or el.get("unitRef") is None:
            continue
        m = 맥락.get(el.get("contextRef"))
        if not m or m[2]:
            continue
        try:
            v = float(글)
        except ValueError:
            continue
        if v.is_integer() and abs(v) < 1e18:
            v = int(v)
        한 = {"이름공간": ns, "태그": 태그, "단위": 단위.get(el.get("unitRef")) or el.get("unitRef"), "end": m[1], "val": v}
        if m[0]:
            한["start"] = m[0]
        사실.append(한)
    return 사실, fy, fp


def 합치기(cf, 사실, 접수번호, 양식, 접수일, fy=None, fp=None):
    """companyfacts dict 에 사실을 더한다(같은 접수번호 · 기간 · 값이면 건너뜀) → 더한 수."""
    facts = cf.setdefault("facts", {})
    if not fp:
        fp = "FY" if 양식 in 연차양식 else None
    n = 0
    for x in 사실:
        단 = facts.setdefault(x["이름공간"], {}).setdefault(x["태그"], {"label": x["태그"], "description": "", "units": {}})["units"]
        목 = 단.setdefault(x["단위"], [])
        열쇠 = (x.get("start"), x["end"], x["val"], 접수번호)
        if any((f.get("start"), f.get("end"), f.get("val"), f.get("accn")) == 열쇠 for f in 목):
            continue
        새 = {"end": x["end"], "val": x["val"], "accn": 접수번호, "fy": int(fy) if fy and str(fy).isdigit() else fy,
             "fp": fp, "form": 양식, "filed": 접수일, "보충": x.get("보충글") or "sec_xbrl보충"}
        if x.get("start"):
            새 = dict({"start": x["start"]}, **새)
        목.append(새)
        n += 1
    return n


def 빠진공시(sub, cf, 최대=4, 문턱=10):
    """submissions 의 정기 공시(XBRL 있음) 가운데 companyfacts 가 본문 사실을 싣지 않은 것 → [{접수번호, 양식, 접수일, 문서}].
    표지(dei) 사실 몇 개만 실린 공시는 실린 것으로 치지 않는다(실측 TSM — FY2025 20-F 는 표지 주식 수 하나만 실렸다).
    본문 사실이 「문턱」 개 이상 실린 공시 가운데 가장 늦은 접수일보다 뒤의 공시만 본다(옛 공시를 다시 두드리지 않는다)."""
    import collections                               # noqa: PLC0415
    수 = collections.Counter()
    접 = {}
    for ns, tags in (cf.get("facts") or {}).items():
        if ns == "dei":
            continue
        for t in tags.values():
            for arr in (t.get("units") or {}).values():
                for f in arr:
                    if f.get("accn"):
                        수[f["accn"]] += 1
                        접[f["accn"]] = f.get("filed") or 접.get(f["accn"])
    완비 = max([접[a] or "" for a, n in 수.items() if n >= 문턱] or [""])
    r = ((sub or {}).get("filings") or {}).get("recent") or {}
    낸 = []
    for i, 양식 in enumerate(r.get("form") or []):
        if 양식 not in 정기양식:
            continue
        if not (r.get("isXBRL") or [0] * (i + 1))[i]:
            continue
        acc = r["accessionNumber"][i]
        if 수.get(acc, 0) >= 문턱 or r["filingDate"][i] <= 완비:
            continue
        낸.append({"접수번호": acc, "양식": 양식, "접수일": r["filingDate"][i], "문서": (r.get("primaryDocument") or [""] * (i + 1))[i]})
    낸.sort(key=lambda x: x["접수일"], reverse=True)
    return 낸[:최대]


def _머리():
    연락 = os.environ.get("SEC_CONTACT_EMAIL")
    if not 연락:
        raise SystemExit("환경변수 SEC_CONTACT_EMAIL 이 없습니다(값은 화면에 적지 않는다)")
    return {"User-Agent": "DCF-research %s" % 연락, "Accept-Encoding": "gzip, deflate"}


def 받기(cik, 접수번호, 곳):
    """공시 색인에서 인스턴스(`*_htm.xml` 먼저 · 없으면 확장자 .xml 인스턴스)를 골라 받는다 → (경로, 주소)."""
    import requests                                  # noqa: PLC0415
    h = _머리()
    바탕 = "https://www.sec.gov/Archives/edgar/data/%d/%s/" % (int(cik), 접수번호.replace("-", ""))
    r = requests.get(바탕 + "index.json", headers=h, timeout=60)
    r.raise_for_status()
    이름들 = [x["name"] for x in (r.json().get("directory") or {}).get("item") or []]
    후 = [n for n in 이름들 if n.lower().endswith("_htm.xml")] or \
        [n for n in 이름들 if n.lower().endswith(".xml") and not re.search(r"_(cal|def|lab|pre)\.xml$", n, re.I) and n != "FilingSummary.xml"]
    if not 후:
        raise RuntimeError("인스턴스 파일을 색인에서 못 찾았다")
    time.sleep(0.2)
    주소 = 바탕 + 후[0]
    r = requests.get(주소, headers=h, timeout=180)
    r.raise_for_status()
    os.makedirs(곳, exist_ok=True)
    p = os.path.join(곳, "%s.xml" % 접수번호)
    with open(p, "wb") as f:
        f.write(r.content)
    time.sleep(0.2)
    return p, 주소


def main(argv=None):
    ap = argparse.ArgumentParser(allow_abbrev=False, description="SEC companyfacts 에 빠진 정기 공시를 XBRL 인스턴스에서 보충")
    ap.add_argument("--raw", default=os.path.join(ROOT, "_raw"))
    ap.add_argument("--최대", type=int, default=4)
    ap.add_argument("--확인만", action="store_true")
    ap.add_argument("--인스턴스", help="받아 둔 인스턴스 파일(네트워크 없이) — --접수번호 · --양식 · --접수일 과 함께")
    ap.add_argument("--접수번호")
    ap.add_argument("--양식")
    ap.add_argument("--접수일")
    a = ap.parse_args(argv)
    cfp = os.path.join(a.raw, "companyfacts.json")
    if not os.path.exists(cfp):
        print("companyfacts.json 이 없다(%s) — sec_fetch 를 먼저" % cfp)
        return 2
    cf = json.load(io.open(cfp, encoding="utf-8"))
    할일 = []
    if a.인스턴스:
        if not (a.접수번호 and a.양식 and a.접수일):
            print("--인스턴스 에는 --접수번호 · --양식 · --접수일 을 함께 준다")
            return 2
        할일 = [{"접수번호": a.접수번호, "양식": a.양식, "접수일": a.접수일, "파일": a.인스턴스, "주소": "(받아 둔 파일) %s" % os.path.basename(a.인스턴스)}]
    else:
        sp = os.path.join(a.raw, "submissions.json")
        if not os.path.exists(sp):
            print("submissions.json 이 없다 — sec_fetch 를 먼저")
            return 2
        할일 = 빠진공시(json.load(io.open(sp, encoding="utf-8")), cf, a.최대)
    if not 할일:
        print("보충할 정기 공시 없음 — companyfacts 가 XBRL 정기 공시를 다 싣고 있다")
        return 0
    for x in 할일:
        print("빠짐: %s %s(접수 %s)%s" % (x["양식"], x["접수번호"], x["접수일"], (" · " + x.get("문서")) if x.get("문서") else ""))
    if a.확인만:
        return 0
    원본 = os.path.join(a.raw, "companyfacts_원본.json")
    if not os.path.exists(원본):
        shutil.copyfile(cfp, 원본)
    cik = cf.get("cik")
    오늘 = datetime.date.today().isoformat()
    실패 = 0
    for x in 할일:
        try:
            if x.get("파일"):
                p, 주소 = x["파일"], x["주소"]
            else:
                p, 주소 = 받기(cik, x["접수번호"], os.path.join(a.raw, "xbrl"))
            사실, fy, fp = 파싱(open(p, "rb").read())
            n = 합치기(cf, 사실, x["접수번호"], x["양식"], x["접수일"], fy, fp)
            cf.setdefault("_보충", []).append({"접수번호": x["접수번호"], "양식": x["양식"], "접수일": x["접수일"], "사실수": n,
                                             "fy": fy, "fp": fp, "주소": 주소, "조회일": 오늘})
            print("보충: %s %s — 사실 %d건(fy %s · fp %s)" % (x["양식"], x["접수번호"], n, fy, fp))
        except Exception as e:                       # noqa: BLE001
            실패 += 1
            print("받지 못함: %s %s — %s: %s" % (x["양식"], x["접수번호"], type(e).__name__, str(e)[:160]))
    json.dump(cf, io.open(cfp, "w", encoding="utf-8"), ensure_ascii=False)
    print("저장: %s (원본 %s)" % (cfp, os.path.basename(원본)))
    return 1 if 실패 else 0


if __name__ == "__main__":
    sys.exit(main())

# -*- coding: utf-8 -*-
"""조문 조회 — 국내 법령 조문 원문(법제처 국가법령정보 공동활용 OPEN API · DRF)을 읽어 캐시에 남긴다(S6-08 · D 의 첫 수단).

왜 있는가
    D(외부 제약)가 조세특례제한법 제24조를 「law.go.kr 본문 열람 실패 — 2차 매체」로 남겼다(하이닉스 S6 리뷰). law.go.kr 화면은 동적이라
    읽히지 않지만 DRF 는 정적 JSON 을 준다 — `한계세율.py` 가 이미 그 길로 세율표를 만든다. 그 조회를 세율표 밖의 아무 조문에 쓰게 뗐다.
    **1차 원문이 있으면 2차 매체(기사 · 해설)로 확인상태를 올리지 않는다**(D 규칙).

쓰는 법
    python 스크립트/조문조회.py 조회 조세특례제한법 24 --기준일 2026-06-30            # 제24조 — 평가기준일에 시행 중인 판
    python 스크립트/조문조회.py 조회 조세특례제한법 10 --가지 0 --캐시 _raw            # → _raw/조문_조세특례제한법_010000.json
    python 스크립트/조문조회.py 조회 법인세법 13 --기준일 2026-06-30

    **OC(API 신청 아이디)는 환경변수 `LAW_OC` 에서만 읽는다**(`한계세율.py` 와 같은 규약 — 화면 · 파일에 찍지 않는다. 주소는 `OC={OC}` 로 가려 저장).
    `LAW_OC` 가 없으면 네트워크를 타지 않고 캐시(`--캐시` 폴더의 `조문_{법령명}_{JO}.json`)만 읽고 「OC 없음 — 캐시만」을 알린다.

산출(JSON)  {"법령명", "조문"(제n조[의m]), "JO", "시행일", "공포일", "법령일련번호", "본문"(조 · 항 · 호 · 목을 차례대로 이은 글), "출처URL"(OC 가림),
            "조회일", "확인상태"("확인완료(법령 원문·1차)" | "캐시" | "미확인 — 까닭")}
조문 번호의 시한(일몰 · 적용기한) · 공제율 · 한도는 본문에서 사람이 읽는다 — 이 도구는 원문을 가져올 뿐 해석하지 않는다.
종료 코드 0 = 원문을 얻었다(조회 · 캐시) · 1 = 못 얻었다.
"""
from __future__ import annotations

import argparse
import datetime as dt
import io
import json
import os
import re
import sys
import urllib.parse

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
DRF = "https://www.law.go.kr/DRF/"


def JO(조, 가지=0):
    """제24조 → 002400 · 제103조의20 → 010320."""
    return "%04d%02d" % (int(조), int(가지 or 0))


def _get(url):
    import 한계세율 as _한                                    # noqa: PLC0415 — 같은 요청 함수(재시도 · 머리)
    return _한._get(url)


def 본문잇기(조문json):
    """lawService 응답(JO 지정) → 조 · 항 · 호 · 목 글을 차례대로 이은 글. 표(이미지 alt)는 그대로 둔다."""
    b = 조문json.get("법령", {}) if isinstance(조문json, dict) else {}
    cs = (b.get("조문") or {}).get("조문단위") or []
    if isinstance(cs, dict):
        cs = [cs]
    줄 = []

    def 목록(x):
        return [x] if isinstance(x, dict) else (x or [])
    for c in cs:
        if c.get("조문여부") not in (None, "조문"):
            continue
        줄.append(("%s" % (c.get("조문내용") or "")).strip())
        for 항 in 목록(c.get("항")):
            줄.append(("%s" % (항.get("항내용") or "")).strip())
            for 호 in 목록(항.get("호")):
                줄.append("  " + ("%s" % (호.get("호내용") or "")).strip())
                for 목 in 목록(호.get("목")):
                    줄.append("    " + ("%s" % (목.get("목내용") or "")).strip())
    return "\n".join(x for x in 줄 if x.strip())


def _판고르기(목록, 기준일):
    """기준일에 시행 중이고 기준일까지 공포된 판 — (법령일련번호, 시행일자, 공포일자). 없으면 None."""
    k = (기준일 or dt.date.today().isoformat()).replace("-", "")
    후보 = [x for x in 목록 if (x.get("시행일자") or "") <= k and (x.get("공포일자") or "") <= k]
    if not 후보:
        return None
    x = sorted(후보, key=lambda x: (x.get("시행일자") or "", x.get("공포일자") or ""))[-1]
    return x.get("법령일련번호"), x.get("시행일자"), x.get("공포일자")


def 조회(법령명, 조, 가지=0, 기준일=None, 캐시=None, oc=None):
    oc = oc or os.environ.get("LAW_OC")
    jo = JO(조, 가지)
    곳 = os.path.join(캐시, "조문_%s_%s.json" % (법령명, jo)) if 캐시 else None
    if not oc:
        if 곳 and os.path.exists(곳):
            d = json.load(io.open(곳, encoding="utf-8"))
            d["확인상태"] = "캐시 — " + (d.get("확인상태") or "")
            return d
        return {"법령명": 법령명, "JO": jo, "확인상태": "미확인 — OC 없음 — 캐시만(환경변수 LAW_OC 가 없고 캐시 %s 도 없다)" % (곳 or "(캐시 폴더 미지정)")}
    목록 = []
    for 쪽 in range(1, 9):
        u = DRF + "lawSearch.do?OC=%s&target=eflaw&type=JSON&display=100&page=%d&query=%s" % (oc, 쪽, urllib.parse.quote(법령명))
        j = _get(u).get("LawSearch", {})
        laws = j.get("law") or []
        if isinstance(laws, dict):
            laws = [laws]
        if not laws:
            break
        목록 += [x for x in laws if x.get("법령명한글") == 법령명]
        if 쪽 * 100 >= int(j.get("totalCnt") or 0):
            break
    판 = _판고르기(목록, 기준일)
    if not 판:
        return {"법령명": 법령명, "JO": jo, "확인상태": "미확인 — 기준일(%s)에 시행 중인 판을 목록에서 찾지 못했다" % 기준일}
    mst, 시행, 공포 = 판
    url = DRF + "lawService.do?OC=%s&target=eflaw&MST=%s&efYd=%s&JO=%s&type=JSON" % (oc, mst, 시행, jo)
    본 = 본문잇기(_get(url))
    d = {"법령명": 법령명, "조문": "제%d조%s" % (int(조), ("의%d" % int(가지)) if 가지 else ""), "JO": jo,
         "시행일": "%s-%s-%s" % (시행[:4], 시행[4:6], 시행[6:]), "공포일": "%s-%s-%s" % (공포[:4], 공포[4:6], 공포[6:]), "법령일련번호": mst,
         "본문": 본, "출처URL": url.replace("OC=%s&" % oc, "OC={OC}&"), "조회일": dt.date.today().isoformat(),
         "확인상태": "확인완료(법령 원문·1차)" if 본 else "미확인 — 조문 본문이 비었다"}
    if 곳 and 본:
        os.makedirs(os.path.dirname(os.path.abspath(곳)), exist_ok=True)
        json.dump(d, io.open(곳, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return d


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False, description="조문 조회 — 법제처 DRF 원문(LAW_OC) · 캐시")
    sub = ap.add_subparsers(dest="명령", required=True)
    q = sub.add_parser("조회", allow_abbrev=False)
    q.add_argument("법령명")
    q.add_argument("조", type=int)
    q.add_argument("--가지", type=int, default=0, help="조의 가지 번호(제103조의20 → 20)")
    q.add_argument("--기준일", default=None, help="YYYY-MM-DD — 그날 시행 중이고 그날까지 공포된 판")
    q.add_argument("--캐시", default=None, help="캐시 폴더(예: _raw) — 조회 결과를 남기고, OC 가 없으면 여기서만 읽는다")
    a = ap.parse_args()
    d = 조회(a.법령명, a.조, a.가지, a.기준일, a.캐시)
    print(json.dumps(d, ensure_ascii=False, indent=1))
    return 0 if d.get("본문") else 1


if __name__ == "__main__":
    sys.exit(main())

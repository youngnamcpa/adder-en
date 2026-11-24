# -*- coding: utf-8 -*-
"""IR 묶음 — 재무기준일 분기의 **최신 실적 IR 자료 전문**과 **컨퍼런스콜 전사 전문**을 회차에 받아 두고, 읽었는지를 장부로 남긴다(1.1.11).

왜 있나. 정기보고서(10-Q · 분기보고서)만 받고 실적 발표 묶음(보도자료 · 주주서한 · 실적 발표자료)과 콜 전사를 전문으로 읽지 않은 채
가정을 세운 회차가 나왔다 — 웹조사 갈래가 콜 전사를 「못 봤다」로 넘기고 제3자 요약 몇 줄만 가져왔는데 어느 관문도 막지 않았다.
회사가 다음 분기 가이던스의 구성(유기 · 인수 몫), 매출총이익률이 오른 까닭, 새 투자 계획을 말하는 자리는 그 묶음과 콜이다.
그래서 (1) A1 바로 뒤에 묶음을 받고 (2) 콜 전사가 전문인지 기계로 판정하고 (3) 본선 · B1 이 읽었다는 표지가 없으면 자체검사 63 이 오류로 막는다.

    python 스크립트/IR묶음.py 받기 --가정 가정.json                 # 미국: SEC 8-K Item 2.02 첨부(EX-99) · 국내: DART 잠정실적 · 기업설명회 공시 목록
    python 스크립트/IR묶음.py 전사 --가정 가정.json --파일 <글.txt> --출처 <URL> [--분기 이번|직전]   # 콜 전사 글을 회차에 넣고 전문 · 요약 판정
    python 스크립트/IR묶음.py 전사 --가정 가정.json --출처 <URL> --글자수 N --화자수 K --질의응답 예     # 사본 없이 — 브라우저로 끝까지 읽고 잰 값
    python 스크립트/IR묶음.py 해당없음 --가정 가정.json --까닭 "…" [--분기 이번]                    # 콜이 없는 회사(까닭 10자 이상)
    python 스크립트/IR묶음.py 읽음 --가정 가정.json --누가 본선|B1 --메모 "…"                        # 묶음 · 전사를 처음부터 끝까지 읽었다
    python 스크립트/IR묶음.py 점검 --가정 가정.json                                                    # 종료 0 = 갖춤 · 1 = 모자람(목록)

산출: `_raw/IR묶음.json`(「IR묶음/1」) · 첨부 글은 `_raw/IR/<재무기준일>/`. 콜 전사는 도구가 웹에서 받지 않는다 — 전사 게시처가 자동 요청을
막거나(403) 요약 도구가 전문을 돌려주지 않기 때문이다 — 차단을 우회하는 자동 받기(헤드리스 브라우저 따위)는 쓰지 않는다. 게시처가 일반 받기를
허용하면 글 파일로(`--파일`), 아니면 본선이 브라우저로 전문을 끝까지 읽고 그 자리에서 잰 값으로(`--글자수 · --화자수 · --질의응답`) 넣는다 —
제3자 전사의 사본을 손으로 옮겨 두지 않는다.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import html as _html
import io
import json
import os
import re
import sys
import time

여기 = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, 여기)

형식 = "IR묶음/1"
전문최소글자 = 12000          # 한 시간 남짓한 실적 콜의 전사는 3만 자 안팎 — 1만 2천 자 밑은 요약이나 발췌로 본다
질의표지 = (r"\bOperator\b", r"question[- ]and[- ]answer", r"\bQ&A\b", r"\bAnalyst\b", r"질의응답", r"애널리스트", r"질문")


def _읽기(p):
    try:
        with io.open(p, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def _쓰기(p, d):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with io.open(p, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)


def _글로(htm):
    t = re.sub(r"(?is)<(script|style).*?</\1>", " ", htm)
    t = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</tr>", "\n", t)
    t = re.sub(r"<[^>]+>", " ", t)
    t = _html.unescape(t)
    t = re.sub(r"[ \t\xa0]+", " ", t)
    return re.sub(r"\n\s*\n+", "\n", t).strip()


def _해시(b):
    return hashlib.sha256(b if isinstance(b, bytes) else b.encode("utf-8")).hexdigest()[:16]


def 날짜들(가정경로):
    import 기준일인자                                       # noqa: PLC0415
    F = 기준일인자.풀기(None, 가정경로, 기준일인자.재무, 인자="--기준일")
    T = 기준일인자.풀기(None, 가정경로, 기준일인자.평가, 인자="--평가기준일")
    return F, T or F


def 자리(가정경로):
    회차 = os.path.dirname(os.path.abspath(가정경로))
    return 회차, os.path.join(회차, "_raw", "IR묶음.json")


def 시장(회차):
    raw = os.path.join(회차, "_raw")
    if os.path.exists(os.path.join(raw, "submissions.json")):
        return "US"
    if os.path.exists(os.path.join(raw, "dart_기업개황.json")):
        return "KR"
    return None


def 전사판정(글):
    """콜 전사 글 → {"상태": 전문|요약, "글자수", "질의응답표지", "화자수", "까닭"}. 전문 = 글자 수 문턱 이상 + 질의응답 표지 + 화자 셋 이상."""
    n = len(re.sub(r"\s", "", 글 or ""))
    표지 = any(re.search(p, 글 or "", re.I) for p in 질의표지)
    화자 = len(set(re.findall(r"(?m)^\s*([A-Z][A-Za-z.'\- ]{2,40}|[가-힣]{2,5})\s*[,:(]", 글 or "")))
    까닭 = []
    if n < 전문최소글자:
        까닭.append("글자 %d < %d" % (n, 전문최소글자))
    if not 표지:
        까닭.append("질의응답 표지 없음")
    if 화자 < 3:
        까닭.append("화자 %d < 3" % 화자)
    return {"상태": "전문" if not 까닭 else "요약", "글자수": n, "질의응답표지": 표지, "화자수": 화자, "까닭": " · ".join(까닭) or None}


# ── 미국: SEC 8-K Item 2.02(Results of Operations) 첨부 ─────────────────────────
def 실적8K고르기(sub, F, T):
    """submissions → 재무기준일 분기의 실적 8-K(이번)와 그 앞 분기의 실적 8-K(직전). Item 2.02 가 있는 8-K · 해외 발행사는 6-K(실적 첨부는 sec_fetch 가 고른다).
    이번 = 제출일이 F 뒤 ~ T 이하인 2.02 가운데 가장 늦은 것(없으면 F − 10일 ~ T) · 직전 = 이번보다 앞 2.02 가운데 가장 늦은 것."""
    r = (sub.get("filings") or {}).get("recent") or {}
    행 = []
    for i, form in enumerate(r.get("form") or []):
        items = (r.get("items") or [""] * len(r["form"]))[i] or ""
        if form in ("8-K", "8-K/A") and "2.02" in items:
            행.append({"양식": form, "제출일": r["filingDate"][i], "accession": r["accessionNumber"][i], "items": items,
                      "문서": r["primaryDocument"][i]})
    행.sort(key=lambda x: x["제출일"])
    f, t = datetime.date.fromisoformat(F), datetime.date.fromisoformat(T)
    이번후보 = [x for x in 행 if f < datetime.date.fromisoformat(x["제출일"]) <= t] or \
             [x for x in 행 if f - datetime.timedelta(days=10) <= datetime.date.fromisoformat(x["제출일"]) <= t]
    이번 = 이번후보[-1] if 이번후보 else None
    앞 = [x for x in 행 if (not 이번) or x["제출일"] < 이번["제출일"]]
    return 이번, (앞[-1] if 앞 else None)


def _종류(이름, 글):
    """첨부 이름이 먼저 · 글은 그다음(보도자료가 주주서한을 언급해도 주주서한으로 가르지 않는다)."""
    n = 이름.lower()
    if re.search(r"sharehold|letter", n):
        return "주주서한"
    if re.search(r"present|slide|deck", n):
        return "발표자료"
    s = 글[:4000].lower()
    if "dear fellow shareholders" in s or "dear shareholders" in s:
        return "주주서한"
    if re.search(r"ex\w{0,3}99[-_.]?0?1", n) or re.search(r"reports? .{0,60}(quarter|results)", s):
        return "보도자료"
    return "기타"


def 미국받기(회차, F, T, 판):
    import sec_fetch as S                                     # noqa: PLC0415
    S._머리()
    raw = os.path.join(회차, "_raw")
    sub = _읽기(os.path.join(raw, "submissions.json"))
    if not sub:
        판["경보"].append("submissions.json 이 없다 — sec_fetch.py 를 먼저 돌린다")
        return
    cik = int(sub.get("cik") or 0)
    이번, 직전 = 실적8K고르기(sub, F, T)
    if not 이번:
        판["경보"].append("재무기준일 %s 뒤 ~ 평가기준일 %s 에 Item 2.02(실적) 8-K 가 없다 — 실적 발표가 10-Q 와 함께만 나왔거나 아직 없다. "
                         "회사 IR 사이트의 실적 자료를 본선이 받아 `읽음` 메모에 적는다" % (F, T))
    폴더 = os.path.join(raw, "IR", F)
    os.makedirs(폴더, exist_ok=True)
    for 역, 행 in (("이번", 이번), ("직전", 직전)):
        if not 행:
            continue
        acc = 행["accession"].replace("-", "")
        r = S.get("https://www.sec.gov/Archives/edgar/data/%d/%s/index.json" % (cik, acc), S.HEAD)
        time.sleep(0.3)
        칸 = {"분기": 역, "양식": 행["양식"], "제출일": 행["제출일"], "accession": 행["accession"], "items": 행["items"], "첨부": []}
        if r is None:
            칸["경보"] = "목록 못 받음"
            판["실적묶음"].append(칸)
            continue
        이름들 = [x.get("name") for x in ((r.json().get("directory") or {}).get("item") or [])]
        첨부 = [n for n in 이름들 if n and not re.match(r"\d{10}-\d{2}-\d{6}", n)
                and re.search(r"(?i)ex[\w\-]{0,5}99|sharehold|letter|present|slide|deck", n) and re.search(r"(?i)\.(htm|html|pdf|txt)$", n)]   # 1.1.12 — 「ex-991」 따위 하이픈 이름
        for n in 첨부[:6]:
            r2 = S.get("https://www.sec.gov/Archives/edgar/data/%d/%s/%s" % (cik, acc, n), S.HEAD)
            time.sleep(0.3)
            if r2 is None:
                continue
            저장 = os.path.join(폴더, "%s_%s_%s" % (역, 행["제출일"].replace("-", ""), n))
            with io.open(저장, "wb") as f:
                f.write(r2.content)
            if n.lower().endswith(".pdf"):
                try:
                    import pymupdf                            # noqa: PLC0415
                    글 = "\n".join(p.get_text() for p in pymupdf.open(저장))
                except Exception:                             # noqa: BLE001
                    글 = ""
            else:
                글 = _글로(r2.text)
            with io.open(저장 + ".txt", "w", encoding="utf-8") as f:
                f.write(글)
            웹캐스트 = sorted(set(re.findall(r"https?://(?:ir|investor|investors)\.[A-Za-z0-9.\-/]+", 글)))[:3]
            칸["첨부"].append({"파일": os.path.relpath(저장, 회차).replace("\\", "/"), "종류": _종류(n, 글), "글자수": len(글),
                             "해시": _해시(r2.content), "웹캐스트": 웹캐스트})
        판["실적묶음"].append(칸)


# ── 국내: DART 잠정실적 · 기업설명회 ────────────────────────────────────────
def 국내받기(회차, F, T, 판):
    raw = os.path.join(회차, "_raw")
    개 = _읽기(os.path.join(raw, "dart_기업개황.json")) or {}
    고유 = 개.get("corp_code")
    if not 고유:
        판["경보"].append("dart_기업개황.json 의 고유번호가 없다 — dart_fetch.py 를 먼저 돌린다")
        return
    import dart_fetch as DF                                    # noqa: PLC0415
    시작 = (datetime.date.fromisoformat(F) - datetime.timedelta(days=100)).strftime("%Y%m%d")
    끝 = datetime.date.fromisoformat(T).strftime("%Y%m%d")
    줄 = []
    for 종류 in ("I", "E"):
        try:
            j = DF._get("list.json", corp_code=고유, bgn_de=시작, end_de=끝, pblntf_ty=종류, page_no=1, page_count=100).json()
        except Exception as e:                                # noqa: BLE001
            판["경보"].append("DART list.json(%s) 실패 — %s" % (종류, e))
            continue
        for it in j.get("list") or []:
            nm = it.get("report_nm") or ""
            if re.search(r"잠정\)?실적|기업설명회|IR\)?\s*개최|실적발표", nm):
                줄.append({"보고서": nm.strip(), "접수일": it.get("rcept_dt"), "접수번호": it.get("rcept_no"),
                          "주소": "https://dart.fss.or.kr/dsaf001/main.do?rcpNo=%s" % it.get("rcept_no")})
    줄.sort(key=lambda x: x["접수일"] or "")
    f = F.replace("-", "")
    이번 = [x for x in 줄 if (x["접수일"] or "") > f]
    판["실적묶음"].append({"분기": "이번", "공시": 이번, "첨부": []})
    판["실적묶음"].append({"분기": "직전", "공시": [x for x in 줄 if (x["접수일"] or "") <= f], "첨부": []})
    if not 이번:
        판["경보"].append("재무기준일 뒤 잠정실적 · 기업설명회 공시가 없다 — 회사 IR 페이지 · KIND 의 실적 발표자료를 본선이 받아 `읽음` 메모에 적는다")
    판["안내"].append("국내 실적 발표자료(기업설명회 첨부 PDF)는 KIND · 회사 IR 페이지에 있다 — 받아 `_raw/IR/<재무기준일>/` 에 두고 `읽음` 으로 적는다")


def 받기(가정경로):
    F, T = 날짜들(가정경로)
    회차, p = 자리(가정경로)
    옛 = _읽기(p) or {}
    판 = {"형식": 형식, "시장": 시장(회차), "재무기준일": F, "평가기준일": T, "조회일": datetime.date.today().isoformat(),
         "실적묶음": [], "콜전사": 옛.get("콜전사") or [], "읽음": 옛.get("읽음") or [], "경보": [], "안내": []}
    if 판["시장"] == "US":
        미국받기(회차, F, T, 판)
    elif 판["시장"] == "KR":
        국내받기(회차, F, T, 판)
    else:
        판["경보"].append("시장을 모른다 — sec_fetch.py(미국) · dart_fetch.py(국내)를 먼저 돌린다")
    if not any(c.get("분기") == "이번" for c in 판["콜전사"]):
        판["안내"].append("콜 전사는 도구가 받지 않는다 — 본선이 브라우저로 이번 · 직전 분기 전사 전문을 열어 글로 저장하고 "
                         "`IR묶음.py 전사 --파일 … --출처 …` 로 넣는다(요약 · 기사 · 검색 요약은 전문이 아니다). 콜이 없으면 `해당없음 --까닭`")
    _쓰기(p, 판)
    return 판


def 전사넣기(가정경로, 파일, 출처, 분기="이번"):
    F, _ = 날짜들(가정경로)
    회차, p = 자리(가정경로)
    판 = _읽기(p) or 받기(가정경로)
    with io.open(파일, encoding="utf-8", errors="ignore") as f:
        글 = f.read()
    폴더 = os.path.join(회차, "_raw", "IR", F)
    os.makedirs(폴더, exist_ok=True)
    저장 = os.path.join(폴더, "콜전사_%s.txt" % 분기)
    if os.path.abspath(저장) != os.path.abspath(파일):
        with io.open(저장, "w", encoding="utf-8") as f:
            f.write(글)
    판정 = 전사판정(글)
    칸 = {"분기": 분기, "파일": os.path.relpath(저장, 회차).replace("\\", "/"), "출처": 출처, "넣은날": datetime.date.today().isoformat(),
         "해시": _해시(글), **판정}
    판["콜전사"] = [c for c in 판.get("콜전사") or [] if c.get("분기") != 분기] + [칸]
    _쓰기(p, 판)
    return 칸


def 전사측정넣기(가정경로, 출처, 글자수, 화자수, 질의응답, 분기="이번"):
    """사본을 두지 않는 등록 — 게시처가 자동 받기를 막거나(403) 재배포가 안 되는 전사는 본선이 브라우저로 전문을 끝까지 읽고,
    그 자리에서 잰 값(공백 뺀 글자 수 · 화자 수 · 질의응답 표지)과 주소만 장부에 남긴다. 판정 문턱은 글 파일과 같다."""
    _, p = 자리(가정경로)
    판 = _읽기(p) or 받기(가정경로)
    까닭 = []
    if 글자수 < 전문최소글자:
        까닭.append("글자 %d < %d" % (글자수, 전문최소글자))
    if not 질의응답:
        까닭.append("질의응답 표지 없음")
    if 화자수 < 3:
        까닭.append("화자 %d < 3" % 화자수)
    칸 = {"분기": 분기, "파일": None, "출처": 출처, "넣은날": datetime.date.today().isoformat(), "방식": "브라우저 열람 측정(사본 없음)",
         "상태": "전문" if not 까닭 else "요약", "글자수": 글자수, "질의응답표지": bool(질의응답), "화자수": 화자수, "까닭": " · ".join(까닭) or None}
    판["콜전사"] = [c for c in 판.get("콜전사") or [] if c.get("분기") != 분기] + [칸]
    _쓰기(p, 판)
    return 칸


def 해당없음(가정경로, 까닭, 분기="이번"):
    _, p = 자리(가정경로)
    판 = _읽기(p) or 받기(가정경로)
    if len((까닭 or "").strip()) < 10:
        raise SystemExit("까닭은 10자 이상 — 무엇을 확인했고 왜 콜이 없나(회사 IR 일정 · 공시)")
    판["콜전사"] = [c for c in 판.get("콜전사") or [] if c.get("분기") != 분기] + [{"분기": 분기, "상태": "해당없음", "까닭": 까닭.strip()}]
    _쓰기(p, 판)


def 읽음(가정경로, 누가, 메모):
    _, p = 자리(가정경로)
    판 = _읽기(p) or 받기(가정경로)
    파일들 = [a["파일"] for c in 판.get("실적묶음") or [] for a in c.get("첨부") or []] + \
           [c["파일"] for c in 판.get("콜전사") or [] if c.get("파일")]
    판["읽음"] = [x for x in 판.get("읽음") or [] if x.get("누가") != 누가] + \
               [{"누가": 누가, "날": datetime.date.today().isoformat(), "메모": 메모, "파일": 파일들}]
    _쓰기(p, 판)


def 점검(판):
    """→ (오류 목록, 경보 목록). 자체검사 63 · 회차실행이 같은 함수를 쓴다."""
    오류, 경보 = [], []
    if not 판:
        return ["최신 실적 IR 묶음을 받지 않았다 — `python 스크립트/IR묶음.py 받기 --가정 <가정>`"], []
    이번 = [c for c in 판.get("실적묶음") or [] if c.get("분기") == "이번"]
    if 판.get("시장") == "US":
        if not 이번 or not any(a.get("글자수", 0) > 0 for c in 이번 for a in c.get("첨부") or []):
            (오류 if not any("Item 2.02" in x for x in 판.get("경보") or []) else 경보).append(
                "재무기준일 분기의 실적 발표 묶음(보도자료 · 주주서한 · 발표자료) 원문이 회차에 없다")
    elif 판.get("시장") == "KR" and not (이번 and 이번[0].get("공시")):
        경보.append("재무기준일 뒤 잠정실적 · 기업설명회 공시를 찾지 못했다 — 회사 IR 자료를 받아 `읽음` 메모에 적는다")
    콜 = {c.get("분기"): c for c in 판.get("콜전사") or []}
    c = 콜.get("이번")
    if not c:
        오류.append("이번 분기 컨퍼런스콜 전사가 없다 — 전문을 받아 `IR묶음.py 전사` 로 넣거나, 콜이 없으면 `해당없음 --까닭`")
    elif c.get("상태") == "요약":
        오류.append("이번 분기 콜 전사가 전문이 아니다(%s) — 요약 · 발췌는 「봤다」가 아니다" % (c.get("까닭") or "판정 요약"))
    if "직전" not in 콜:
        경보.append("직전 분기 콜 전사가 없다 — 두 회 사이에 회사가 고쳐 말한 칸(가이던스 표현 · 투자 계획)을 대 보려면 직전도 넣는다")
    elif 콜["직전"].get("상태") == "요약":
        경보.append("직전 분기 콜 전사가 전문이 아니다(%s)" % (콜["직전"].get("까닭") or ""))
    누 = {x.get("누가") for x in 판.get("읽음") or []}
    if "본선" not in 누:
        오류.append("본선이 IR 묶음과 콜 전사를 처음부터 끝까지 읽었다는 표지가 없다 — 읽고 `IR묶음.py 읽음 --누가 본선 --메모 …`(가정에 닿은 것)")
    return 오류, 경보


def main(argv=None):
    ap = argparse.ArgumentParser(description="최신 실적 IR 묶음 · 콜 전사 전문 — 받기 · 전사 · 해당없음 · 읽음 · 점검")
    ap.add_argument("명령", choices=["받기", "전사", "해당없음", "읽음", "점검"])
    ap.add_argument("--가정", required=True)
    ap.add_argument("--파일")
    ap.add_argument("--출처")
    ap.add_argument("--분기", default="이번", choices=["이번", "직전"])
    ap.add_argument("--까닭")
    ap.add_argument("--누가", choices=["본선", "B1", "B2"])
    ap.add_argument("--메모", default="")
    ap.add_argument("--글자수", type=int, help="전사 — 브라우저 열람 측정: 공백 뺀 글자 수(사본 없이 넣을 때)")
    ap.add_argument("--화자수", type=int, default=0)
    ap.add_argument("--질의응답", choices=["예", "아니오"], default="아니오")
    a = ap.parse_args(argv)
    if a.명령 == "받기":
        판 = 받기(a.가정)
        for c in 판["실적묶음"]:
            print("%s %s 제출 %s · 첨부 %d · %s" % (c.get("분기"), c.get("양식", "공시"), c.get("제출일", "-"), len(c.get("첨부") or c.get("공시") or []),
                                              " · ".join("%s(%s %d자)" % (x["파일"].split("/")[-1], x["종류"], x["글자수"]) for x in c.get("첨부") or [])))
        for x in 판["경보"] + 판["안내"]:
            print("※ " + x)
        return 0
    if a.명령 == "전사":
        if not a.출처 or not (a.파일 or a.글자수):
            ap.error("전사 — --출처 와 함께 --파일(글) 또는 --글자수 · --화자수 · --질의응답(브라우저 열람 측정)이 필요하다")
        칸 = 전사넣기(a.가정, a.파일, a.출처, a.분기) if a.파일 else             전사측정넣기(a.가정, a.출처, a.글자수, a.화자수, a.질의응답 == "예", a.분기)
        print("콜 전사 %s — %s · 글자 %d · 질의응답 %s · 화자 %d%s" % (a.분기, 칸["상태"], 칸["글자수"], "있음" if 칸["질의응답표지"] else "없음",
                                                        칸["화자수"], (" · " + 칸["까닭"]) if 칸.get("까닭") else ""))
        return 0 if 칸["상태"] == "전문" else 1
    if a.명령 == "해당없음":
        해당없음(a.가정, a.까닭, a.분기)
        print("콜 전사 %s — 해당없음 적음" % a.분기)
        return 0
    if a.명령 == "읽음":
        if not a.누가 or len(a.메모.strip()) < 10:
            ap.error("읽음 — --누가 와 --메모(10자 이상 — 읽고 가정에 닿은 것)가 필요하다")
        읽음(a.가정, a.누가, a.메모)
        print("읽음 — %s" % a.누가)
        return 0
    _, p = 자리(a.가정)
    오류, 경보 = 점검(_읽기(p))
    for x in 오류:
        print("오류 — " + x)
    for x in 경보:
        print("경보 — " + x)
    if not (오류 or 경보):
        print("IR 묶음 · 콜 전사 · 읽음 — 갖춤")
    return 1 if 오류 else 0


if __name__ == "__main__":
    sys.exit(main())

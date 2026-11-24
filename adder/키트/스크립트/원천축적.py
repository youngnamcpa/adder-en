# -*- coding: utf-8 -*-
"""원천축적 — 회사마다 공시 원천을 공용 캐시에 쌓고, 다음 회차는 「받아 둔 시점 이후」만 받는다 (2026-10-23 밤 신설).

왜 만들었나
  회차마다 A1(원본 확보)이 사업보고서 · 반기보고서 원문 · 재무 API · companyfacts 를 처음부터 다시 받았다(국내 한 종목 수십 MB ·
  수십 번의 왕복). 이미 받아 둔 공시는 바뀌지 않는다. 그래서 **회사마다 받은 원천을 공용 캐시에 쌓고 as-of(마지막으로 반영한 공시)를
  적어 두면**, 다음 사람은 그 as-of 뒤에 나온 공시만 받으면 된다(2026-10-23 결정).

무엇을 쌓나 — **공시 원천만**(공개 공시 · 재무 API 응답 · XBRL)과 그 회사의 시세 파일. 판단(가정 · 표본 선정 · 판정 · 원고)은 쌓지 않는다.
  키트 「공용 캐시」 규칙의 「종목 고유 값은 공용으로 두지 않는다」는 **판단 값**을 말한다 — 공개 공시 원문은 누가 받아도 같은 바이트라
  출처(접수번호 · accession · 조회일)를 붙인 채 공용에 둘 수 있다. 그래도 이 캐시는 「찾는 순서: `_raw/` → 공용 캐시 → 네트워크」의
  둘째 자리일 뿐이고, 씨앗으로 가져다 쓰면 회차 `_raw/원천축적_씨앗.json` 에 어디서 왔는지(as-of · 조회일 · 해시)를 남긴다.

자리 — `<공용>/원천/<KR|US>/<종목코드|티커>/` (공용 = 환경변수 `DCF_공용캐시` · 없으면 `~/.dcf캐시`)
  목록.json        꼴의 판 · 회사 · 식별(고유번호 · CIK) · 조회일 · as-of · 파일마다 {sha256 · 크기 · 분류 · 배포 · 도구 · 받은날} · 이력
  원천/            공시 원천(국내 dart_*.json · 사업YYYY/ · 반기/ · 분기원문/ … · 미국 companyfacts · submissions · 10K/10Q 원문)
  시세/            그 회사의 시세 파일 — **배포 묶음에서 뺀다**(재배포 조건이 시세 제공처마다 다르다)
  `<공용>/원천/종목풀/US/<평가기준일>/` — 유사기업 갈래가 받은 다른 회사 개념 추출(sec_concept.py 의 cc_<티커>.json — 값이 평가기준일에 묶여
                   있어 기준일 칸으로 나눈다) — 같은 기준일 · 같은 티커를 다음 회차가 다시 받지 않게(씨앗 `--종목풀 <평가기준일>`)
  `<공용>/원천/_작업/`  받기 · 이어받기가 수집 도구를 돌리는 작업 폴더(키트 스크립트 사본 — 수집 도구는 `_raw/` 를 스크립트 부모에 잡는다)

명령
  python 스크립트/원천축적.py 넣기 --국가 KR --종목 000660 --raw <회차>/_raw          # 이미 받은 회차 `_raw/` 를 캐시에 쌓는다(네트워크 0)
  python 스크립트/원천축적.py 받기 --국가 KR --종목 000660 --기준일 2026-06-30 [--회사 00164779] [--원문해수 6]
  python 스크립트/원천축적.py 받기 --국가 US --종목 NVDA [--기준일 2026-06-30]        # sec_fetch.py 를 작업 폴더에서 돌리고 쌓는다(기준일 분기 보고를 반드시)
  python 스크립트/원천축적.py 이어받기 --국가 KR --종목 000660 [--기준일 …] [--확인만]   # as-of 뒤 정기공시가 있나 한 번 묻고, 있을 때만 받는다
  python 스크립트/원천축적.py 씨앗 --국가 KR --종목 000660 --raw <회차>/_raw [--덮어쓰기] [--종목풀 2026-06-30] [--기준일 2026-06-30]
  python 스크립트/원천축적.py 상태 [--국가 KR] [--json 경로]                          # 쌓인 회사마다 as-of 표
  python 스크립트/원천축적.py 묶기 --출력 <폴더> --판 1 [--국가 KR]                    # 배포 묶음(공시 원천만 · 시세 뺌) — 목록과 ZIP

이어받기의 규칙
  국내 — OpenDART `list.json`(정기공시 A) 을 as-of 접수일 다음 날부터 한 번 부른다. 0건이면 **받지 않고** 확인일만 고친다.
         있으면 그 가운데 마지막 보고서의 기간 끝을 기준일로(`--기준일` 이 있으면 그 값) `dart_fetch.py --회사 … --기준일 …` 을 돌린다.
         원문은 접수번호로 이름이 붙어 바뀌지 않는다 — 이미 있는 원문 폴더는 작업 폴더에 먼저 씨앗으로 넣어 둔다.
  미국 — `submissions` 를 한 번 받아 마지막 정기 보고(10-K · 10-Q · 20-F · 40-F)의 accession 이 as-of 와 같으면 받지 않는다.
         다르면 `sec_fetch.py --ticker …` 를 돌린다(companyfacts 는 통째로 한 파일이라 통째로 바꾼다).
  병합 — 들어오는 쪽의 as-of 가 캐시보다 늦거나 같으면 바뀐 파일을 바꾸고, 이르면 캐시에 없는 파일만 더한다(옛 회차 `_raw` 를 넣어도
         새 캐시를 덮지 않는다). 바꾼 · 더한 파일 수를 이력에 남긴다.

날짜 둘(2026-10-25 · `기준일.py`)
  씨앗 · 받기 · 이어받기의 `--기준일`(별칭 `--재무기준일`)은 **재무기준일 F** 다 — 평가기준일 전에 제출된 마지막 정기보고서의 기간 끝(지금 뜻 그대로).
  `--종목풀 <평가기준일>` 은 **평가기준일 T** 다(다른 회사 개념 추출은 시장 쪽 날에 묶인다). `--평가기준일`(T)을 주면 이어받기는 T 까지 제출된
  공시만 보고(T 뒤 제출은 정보 집합 밖), 받기 · 이어받기는 받는 도구에 넘겨 재무기준일 점검(경보)을 돈다. `--가정` 을 주면 두 날짜를 가정에서 푼다
  (메타.재무기준일이 없으면 F = T — 옛 가정 파일은 지금과 같다).

씨앗의 기준일 대조(2026-10-25 FX-C · 뿌리 R7 · F12 · F24 · F29 · F43 · F44)
  `--기준일` 을 주면 옮긴 원천의 기간을 회차 기준일과 대 본다 — 기준일을 담은 분기 보고(미국 10-Q · 10-K · 20-F · 국내 반기 · 분기 · 사업)가
  캐시에 없거나 기준일 뒤 보고만 있으면 경보를 내고 받는 명령을 적는다(`_raw/원천축적_씨앗.json` 의 「기준일대조」). 기준일 뒤 파일은 지우지 않고 표지만 한다.

키 · 연락처(OPENDART_API_KEY · SEC_CONTACT_EMAIL)는 환경변수에서만 읽고 화면 · 파일에 찍지 않는다.
회사 · 업종 이름은 이 도구에 없다(범용). 종료 코드 — 0 통과 · 1 발견(받기 실패 · 넣을 것 없음) · 2 입력오류.
"""
from __future__ import annotations

import argparse
import datetime
import glob
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:                                    # noqa: BLE001
    pass

여기 = os.path.dirname(os.path.abspath(__file__))
if 여기 not in sys.path:
    sys.path.insert(0, 여기)
from 종료코드 import 통과, 발견, 입력오류  # noqa: E402

형식 = "원천축적 1"
정기양식 = ("10-K", "10-Q", "20-F", "40-F", "10-K/A", "10-Q/A", "20-F/A")

# ── 무엇이 원천인가(이름 꼴 — 수집 도구의 산출 이름이 정본이다: dart_fetch.py · sec_fetch.py)
원천파일꼴 = {
    "KR": [r"dart_기업개황\.json", r"dart_제출이력\.json", r"dart_정기보고서_목록\.json",
           r"dart_재무_(연결|별도)_\d{4}_\d{5}\.json", r"dart_주요계정_\d{4}_\d{5}\.json", r"dart_앵커시계열\.json",
           r"dart_수시공시목록\.json",                                         # 수시공시.py(B · I · C 목록 — 2026-10-25 FX-C)
           r"dart_신고서고르기\.json", r"dart_공시목록_[AC]_\d{8}\.json", r"신고서재무\.json"],   # dart_fetch.py --신고서 · 신고서재무 (2026-10-25 Y1)
    "US": [r"companyfacts\.json", r"submissions\.json", r"(10K|10Q|20F|40F|10KT)_\d{6}\.htm", r"tags_us_gaap\.txt", r"tags_ifrs_full\.txt",
           r"tags_dei\.txt", r"_fetch_log\.txt", r"sec_공시고르기\.json", r"6K_\d{8}_\d+\.htm",
           r"신고서_[A-Za-z0-9\-]+_[\d\-]+\.(htm|txt)", r"신고서재무\.json",   # sec_fetch.py --신고서 · 신고서재무 (2026-10-25 Y1)
           r"부문매출\.json"],                                                 # sec_부문.py(XBRL 부문 축 차원 사실 — 2026-10-25 Y3-2 C)
}
xbrl폴더 = "xbrl"                                                              # 미국 XBRL 인스턴스 · 라벨 — `xbrl/<접수번호>.xml` · `_lab.xml`(sec_부문.py · 2026-10-25 Y3-2)
xbrl파일꼴 = re.compile(r"^\d{10}-\d{2}-\d{6}(_lab)?\.xml$")
신고서폴더 = "신고서"                                                           # 국내 신고서 원문 — `신고서/<접수번호>/<접수번호…>` 한 단 더 들어간다(2026-10-25 Y1)
원문폴더꼴 = r"(사업\d{4}|반기|분기\d?|분기원문|반기원문|사업원문|원문|수시공시원문)$"     # 국내 원문 폴더 — 안의 파일 이름이 접수번호(14자리)로 시작한다
접수번호꼴 = re.compile(r"^\d{14}")
종목풀꼴 = re.compile(r"^cc_([A-Z0-9.\-]+)\.json$")                        # 유사기업 갈래가 받은 다른 회사 companyfacts


def 공용뿌리():
    return (os.environ.get("DCF_공용캐시") or os.environ.get("DCF_SHARED_CACHE")
            or os.path.join(os.path.expanduser("~"), ".dcf캐시"))


def 원천뿌리():
    return os.path.join(공용뿌리(), "원천")


def 회사자리(국가, 종목):
    return os.path.join(원천뿌리(), 국가.upper(), 종목정리(국가, 종목))


def 종목정리(국가, 종목):
    s = ("%s" % 종목).strip()
    return s.zfill(6) if 국가.upper() == "KR" and s.isdigit() else s.upper()


def _지금():
    return datetime.datetime.now().replace(microsecond=0).isoformat()


def _해시(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for 덩 in iter(lambda: f.read(1 << 20), b""):
            h.update(덩)
    return h.hexdigest()


def _읽기(p, 기본=None):
    try:
        with io.open(p, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return 기본


def _쓰기(p, 것):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    임 = p + ".쓰는중"
    with io.open(임, "w", encoding="utf-8") as f:
        json.dump(것, f, ensure_ascii=False, indent=1)
    os.replace(임, p)


# ══════════════════════════════════════════════════════════ 원천 가르기

def 원천목록(raw, 국가, 종목=None):
    """회차 `_raw/` → [(상대경로, 분류)] — 분류: 원천 · 시세. 판단 산출(가정 · 표본 · 신호 · 원고)은 담지 않는다."""
    국가 = 국가.upper()
    낸 = []
    if not os.path.isdir(raw):
        return 낸
    꼴들 = [re.compile("^%s$" % x) for x in 원천파일꼴.get(국가, [])]
    for 이름 in sorted(os.listdir(raw)):
        p = os.path.join(raw, 이름)
        if os.path.isfile(p) and any(c.match(이름) for c in 꼴들):
            낸.append((이름, "원천"))
        elif os.path.isdir(p) and 국가 == "KR" and re.match(원문폴더꼴, 이름):
            for 안 in sorted(os.listdir(p)):
                if 접수번호꼴.match(안) and os.path.isfile(os.path.join(p, 안)):
                    낸.append(("%s/%s" % (이름, 안), "원천"))
        elif os.path.isdir(p) and 국가 == "US" and 이름 == xbrl폴더:
            for 안 in sorted(os.listdir(p)):
                if xbrl파일꼴.match(안) and os.path.isfile(os.path.join(p, 안)):
                    낸.append(("%s/%s" % (이름, 안), "원천"))
        elif os.path.isdir(p) and 국가 == "KR" and 이름 == 신고서폴더:
            for 묶 in sorted(os.listdir(p)):
                q = os.path.join(p, 묶)
                if not (접수번호꼴.match(묶) and os.path.isdir(q)):
                    continue
                for 안 in sorted(os.listdir(q)):
                    if 접수번호꼴.match(안) and os.path.isfile(os.path.join(q, 안)):
                        낸.append(("%s/%s/%s" % (이름, 묶, 안), "원천"))
    # 그 회사의 시세(유사기업 폴더 안 — 이름에 종목코드 · 티커가 든 파일). 다른 회사 시세는 담지 않는다
    if 종목:
        s = 종목정리(국가, 종목)
        pd = os.path.join(raw, "peers")
        if os.path.isdir(pd):
            for 이름 in sorted(os.listdir(pd)):
                if re.match(r"^(day|wk|week|price|주봉|일봉)_?%s([_.]|$)" % re.escape(s), 이름, re.I):
                    낸.append(("peers/%s" % 이름, "시세"))
    return 낸


def 종목풀목록(raw):
    """회차 `_raw/peers/` 의 다른 회사 companyfacts → [(파일 이름, 티커)]."""
    pd = os.path.join(raw, "peers")
    if not os.path.isdir(pd):
        return []
    return [(n, 종목풀꼴.match(n).group(1)) for n in sorted(os.listdir(pd)) if 종목풀꼴.match(n)]


# ══════════════════════════════════════════════════════════ as-of

def _기간(report_nm):
    m = re.search(r"\((\d{4})\.(\d{2})\)", report_nm or "")
    return "%s-%s" % (m.group(1), m.group(2)) if m else None


def asof읽기(raw, 국가):
    """원천에서 as-of 를 읽는다 — 국내: 정기보고서 목록의 마지막 접수(보고서 · 접수번호 · 접수일 · 기간) ·
    미국: submissions 의 마지막 정기 보고(양식 · accession · 접수일 · 보고 기간). 못 읽으면 None."""
    국가 = 국가.upper()
    if 국가 == "KR":
        목 = _읽기(os.path.join(raw, "dart_정기보고서_목록.json"))
        if not isinstance(목, list):
            목 = (_읽기(os.path.join(raw, "dart_제출이력.json")) or {}).get("list") or []
        정 = [x for x in 목 if isinstance(x, dict) and re.search(r"(사업|반기|분기)보고서", x.get("report_nm") or "")]
        if not 정:
            return None
        x = max(정, key=lambda e: (e.get("rcept_dt") or "", e.get("rcept_no") or ""))
        일 = x.get("rcept_dt") or (x.get("rcept_no") or "")[:8]
        return {"보고서": (x.get("report_nm") or "").strip(), "접수번호": x.get("rcept_no"),
                "접수일": "%s-%s-%s" % (일[:4], 일[4:6], 일[6:8]) if len(일) == 8 else 일, "기간": _기간(x.get("report_nm")),
                "고유번호": x.get("corp_code")}
    sub = _읽기(os.path.join(raw, "submissions.json"))
    if not isinstance(sub, dict):
        return None
    rec = (sub.get("filings") or {}).get("recent") or {}
    양 = rec.get("form") or []
    후 = [i for i, f in enumerate(양) if f in 정기양식]
    if not 후:
        return None
    i = max(후, key=lambda j: ((rec.get("filingDate") or [""])[j] or "", (rec.get("accessionNumber") or [""])[j] or ""))
    return {"보고서": 양[i], "접수번호": rec["accessionNumber"][i], "접수일": rec["filingDate"][i],
            "기간": (rec.get("reportDate") or [None] * len(양))[i], "CIK": sub.get("cik"), "회사명": sub.get("name")}


def _앞서나(a, b):
    """as-of a 가 b 보다 이르면 True(접수일 → 접수번호)."""
    if not a:
        return True
    if not b:
        return False
    return (a.get("접수일") or "", a.get("접수번호") or "") < (b.get("접수일") or "", b.get("접수번호") or "")


# ══════════════════════════════════════════════════════════ 넣기 · 씨앗

def 넣기(국가, 종목, raw, 도구="(회차 _raw)", 종목풀=True, 조용=False):
    """회차 `_raw/` 의 원천을 캐시에 쌓는다 → 요약 dict. 네트워크를 타지 않는다."""
    국가 = 국가.upper()
    자리 = 회사자리(국가, 종목)
    목p = os.path.join(자리, "목록.json")
    목 = _읽기(목p) or {"형식": 형식, "국가": 국가, "종목": 종목정리(국가, 종목), "파일": {}, "이력": []}
    if 목.get("형식") != 형식:
        raise ValueError("캐시 목록의 꼴이 다르다(%s ≠ %s) — 옛 캐시는 지우고 다시 쌓는다" % (목.get("형식"), 형식))
    들어옴 = asof읽기(raw, 국가)
    늦거나같음 = not _앞서나(들어옴, 목.get("asof")) if 목.get("asof") else True
    더, 바, 같, 둠 = 0, 0, 0, 0
    지금 = _지금()
    for 상대, 분류 in 원천목록(raw, 국가, 종목):
        src = os.path.join(raw, 상대.replace("/", os.sep))
        칸 = ("시세/" if 분류 == "시세" else "원천/") + 상대
        dst = os.path.join(자리, 칸.replace("/", os.sep))
        h = _해시(src)
        옛 = 목["파일"].get(칸)
        if 옛 and 옛.get("sha256") == h:
            같 += 1
            continue
        if 옛 and not 늦거나같음:
            둠 += 1                                                  # 들어오는 쪽이 옛 as-of — 캐시의 새것을 덮지 않는다
            continue
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
        받은날 = datetime.datetime.fromtimestamp(os.path.getmtime(src)).replace(microsecond=0).isoformat()
        목["파일"][칸] = {"sha256": h, "크기": os.path.getsize(src), "분류": 분류, "배포": 분류 == "원천",
                         "도구": 도구, "받은날": 받은날, "넣은날": 지금}
        if 옛:
            바 += 1
        else:
            더 += 1
    if 들어옴 and 늦거나같음:
        목["asof"] = 들어옴
        if 들어옴.get("고유번호"):
            목.setdefault("식별", {})["고유번호"] = 들어옴["고유번호"]
        if 들어옴.get("CIK"):
            목.setdefault("식별", {})["CIK"] = 들어옴["CIK"]
        if 들어옴.get("회사명"):
            목["회사명"] = 들어옴["회사명"]
    if not 목.get("회사명"):
        개 = _읽기(os.path.join(raw, "dart_기업개황.json")) or {}
        if 개.get("corp_name"):
            목["회사명"] = 개["corp_name"]
            목.setdefault("식별", {})["고유번호"] = 개.get("corp_code")
    목["조회일"] = max([목.get("조회일") or ""] + [v.get("받은날") or "" for v in 목["파일"].values()])
    목["이력"].append({"일시": 지금, "동작": "넣기", "출처": 도구, "asof": 들어옴, "더함": 더, "바꿈": 바, "같음": 같, "옛것이라둠": 둠})
    _쓰기(목p, 목)
    풀 = 0
    if 종목풀:
        for 이름, 티커 in 종목풀목록(raw):
            풀 += 풀넣기(os.path.join(raw, "peers", 이름), 티커)
    낸 = {"국가": 국가, "종목": 종목정리(국가, 종목), "자리": 자리, "asof": 목.get("asof"), "더함": 더, "바꿈": 바, "같음": 같,
         "옛것이라둠": 둠, "종목풀": 풀, "파일수": len(목["파일"])}
    if not 조용:
        print("넣기 %s %s — 더함 %d · 바꿈 %d · 같음 %d · 옛것이라 둠 %d · 종목풀 %d · as-of %s" % (
            국가, 낸["종목"], 더, 바, 같, 둠, 풀, _asof글(목.get("asof"))))
    return 낸


def 풀넣기(src, 티커):
    """다른 회사의 개념 추출(sec_concept.py 의 `cc_<티커>.json` — **평가기준일마다 값이 다르다**: 파일 안 「기준일」)을 종목풀의
    그 기준일 칸에 — 더 늦게 받은 것만 바꾼다. 기준일이 없는 파일은 넣지 않는다(어느 기준일 값인지 모르면 다른 회차에 잘못 쓰인다). 넣었으면 1."""
    기준일 = (_읽기(src) or {}).get("기준일")
    if not (isinstance(기준일, str) and re.match(r"^\d{4}-\d{2}-\d{2}$", 기준일)):
        return 0
    자리 = os.path.join(원천뿌리(), "종목풀", "US", 기준일)
    os.makedirs(자리, exist_ok=True)
    목p = os.path.join(자리, "목록.json")
    목 = _읽기(목p) or {"형식": 형식, "기준일": 기준일, "파일": {}}
    이름 = "cc_%s.json" % 티커.upper()
    받은날 = datetime.datetime.fromtimestamp(os.path.getmtime(src)).replace(microsecond=0).isoformat()
    옛 = 목["파일"].get(이름)
    if 옛 and (옛.get("받은날") or "") >= 받은날:
        return 0
    shutil.copy2(src, os.path.join(자리, 이름))
    목["파일"][이름] = {"sha256": _해시(src), "크기": os.path.getsize(src), "받은날": 받은날, "배포": True}
    _쓰기(목p, 목)
    return 1


def _기간끝(국가, 이름):
    """원천 파일 이름 → 그 보고의 기간 끝 달(YYYY-MM) | None — 미국 `10Q_202606.htm` · 국내는 정기보고서 목록에서 따로 본다."""
    m = re.match(r"^(10K|10Q|20F|40F|10KT)_(\d{4})(\d{2})\.htm$", 이름)
    return "%s-%s" % (m.group(2), m.group(3)) if m else None


def 기준일대조(raw, 국가, 기준일):
    """씨앗 뒤 `_raw` 의 원천 기간을 회차 기준일과 대 본다 → {"기준일보고": 파일 | None, "기준일뒤파일": [...], "경보": [...], "받기": 명령 | None}.
    미국 — submissions 로 기준일 분기 보고(기간 끝 ≤ 기준일 + 7일 중 가장 늦은 것)를 고르고 그 원문이 있나 · 국내 — 기준일 달 보고서가 목록 · 원문 폴더에 있나."""
    국가 = 국가.upper()
    낸 = {"기준일": 기준일, "기준일보고": None, "기준일뒤파일": [], "경보": [], "받기": None}
    if 국가 == "US":
        import 미국원천읽기 as U                                # noqa: PLC0415
        sub = _읽기(os.path.join(raw, "submissions.json"))
        if not isinstance(sub, dict):
            낸["경보"].append("submissions.json 이 없다 — 기준일 분기 보고를 고를 수 없다")
            return 낸
        고름 = U.공시고르기(sub, 기준일)
        기 = 고름.get("기준")
        한달 = (datetime.date.fromisoformat(기준일) + datetime.timedelta(days=U.허용일)).strftime("%Y-%m")
        for n in sorted(os.listdir(raw)):
            k = _기간끝("US", n)
            if k and k > 한달:
                낸["기준일뒤파일"].append(n)
        if 기:
            이름 = U.파일이름(기["양식"], 기["기간끝"])
            if os.path.exists(os.path.join(raw, 이름)):
                낸["기준일보고"] = 이름
            else:
                낸["경보"].append("기준일 분기 보고(%s · 기간 끝 %s · 제출 %s) 원문 `%s` 가 씨앗에 없다%s" % (
                    기["양식"], 기["기간끝"], 기["제출일"], 이름, " — 기준일 뒤 보고만 있다(%s)" % " · ".join(낸["기준일뒤파일"]) if 낸["기준일뒤파일"] else ""))
                낸["받기"] = "python 스크립트/sec_fetch.py --ticker <티커> --기준일 %s" % 기준일
        낸["경보"] += 고름.get("경보") or []
        return 낸
    목 = _읽기(os.path.join(raw, "dart_정기보고서_목록.json"))
    if not isinstance(목, list):
        목 = (_읽기(os.path.join(raw, "dart_제출이력.json")) or {}).get("list") or []
    달 = 기준일[:7].replace("-", ".")
    후 = [x for x in 목 if isinstance(x, dict) and re.search(r"(사업|반기|분기)보고서\s*\(%s\)" % re.escape(달), x.get("report_nm") or "")]
    if not 후:
        낸["경보"].append("기준일(%s) 보고서가 정기보고서 목록에 없다 — 아직 제출 전이거나 목록이 묵었다(이어받기)" % 달)
        낸["받기"] = "python 스크립트/원천축적.py 이어받기 --국가 KR --종목 <종목> --기준일 %s" % 기준일
        return 낸
    x = max(후, key=lambda e: e.get("rcept_no") or "")
    있음 = [p for p in glob.glob(os.path.join(raw, "*", "%s*" % x.get("rcept_no"))) if os.path.isfile(p)]
    if 있음:
        낸["기준일보고"] = os.path.relpath(있음[0], raw).replace("\\", "/")
    else:
        낸["경보"].append("기준일 보고서(%s · 접수 %s) 원문이 씨앗에 없다 — 주석(성격별 · 약정 · 가동률)이 빈다" % ((x.get("report_nm") or "").strip(), x.get("rcept_no")))
        낸["받기"] = "python 스크립트/dart_fetch.py --회사 <고유번호> --기준일 %s" % 기준일
    return 낸


def 씨앗(국가, 종목, raw, 덮어쓰기=False, 종목풀=None, 조용=False, 기준일=None):
    """캐시의 원천을 회차 `_raw/` 로 — 「찾는 순서: `_raw/` → 공용 캐시 → 네트워크」의 둘째 자리.
    이미 있는 파일은 덮지 않는다(`--덮어쓰기`). 무엇을 어디서 가져왔는지 `_raw/원천축적_씨앗.json` 에 남긴다.
    종목풀 = 평가기준일(YYYY-MM-DD)이면 그 기준일의 다른 회사 개념 추출도 `_raw/peers/` 로 — 기준일이 다른 칸은 쓰지 않는다."""
    국가 = 국가.upper()
    자리 = 회사자리(국가, 종목)
    목 = _읽기(os.path.join(자리, "목록.json"))
    if not 목:
        if not 조용:
            print("씨앗 — 캐시에 %s %s 가 없다(%s)" % (국가, 종목정리(국가, 종목), 자리))
        return None
    os.makedirs(raw, exist_ok=True)
    옮김, 둠 = [], 0
    for 칸, v in sorted(목["파일"].items()):
        상대 = 칸.split("/", 1)[1]
        src = os.path.join(자리, 칸.replace("/", os.sep))
        dst = os.path.join(raw, 상대.replace("/", os.sep))
        if not os.path.exists(src):
            continue
        if os.path.exists(dst) and not 덮어쓰기:
            둠 += 1
            continue
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
        옮김.append({"파일": 상대, "sha256": v.get("sha256"), "받은날": v.get("받은날")})
    풀 = []
    if 종목풀:
        풀자리 = os.path.join(원천뿌리(), "종목풀", "US", 종목풀)
        풀목 = _읽기(os.path.join(풀자리, "목록.json")) or {"파일": {}}
        os.makedirs(os.path.join(raw, "peers"), exist_ok=True)
        for 이름, v in sorted(풀목["파일"].items()):
            dst = os.path.join(raw, "peers", 이름)
            if os.path.exists(dst) and not 덮어쓰기:
                continue
            shutil.copy2(os.path.join(풀자리, 이름), dst)
            풀.append({"파일": "peers/" + 이름, "받은날": v.get("받은날")})
    기록 = {"형식": 형식, "일시": _지금(), "국가": 국가, "종목": 목.get("종목"), "캐시": 자리, "asof": 목.get("asof"),
          "조회일": 목.get("조회일"), "옮김": 옮김, "이미있어둠": 둠, "종목풀": 풀,
          "알림": "공용 캐시에서 가져왔다 — 이 회차 폴더에서 새로 받은 것이 아니다. as-of 뒤의 공시는 `원천축적.py 이어받기` 로"}
    if 기준일:
        대 = 기준일대조(raw, 국가, 기준일)
        if 대.get("받기"):
            대["받기"] = 대["받기"].replace("<티커>", 목.get("종목") or "").replace("<종목>", 목.get("종목") or "").replace(
                "<고유번호>", (목.get("식별") or {}).get("고유번호") or "<고유번호>")
        기록["기준일대조"] = 대
    _쓰기(os.path.join(raw, "원천축적_씨앗.json"), 기록)
    if not 조용:
        print("씨앗 %s %s — 옮김 %d · 이미 있어 둠 %d · 종목풀 %d · as-of %s · 공용 캐시에서 가져왔다(이 폴더에서 새로 받은 것이 아니다)" % (
            국가, 목.get("종목"), len(옮김), 둠, len(풀), _asof글(목.get("asof"))))
        for x in (기록.get("기준일대조") or {}).get("경보") or []:
            print("  경보 — %s" % x)
        if (기록.get("기준일대조") or {}).get("받기"):
            print("  받기 — %s" % 기록["기준일대조"]["받기"])
    return 기록


def _asof글(a):
    if not a:
        return "(없음)"
    return "%s %s(접수 %s · 기간 %s)" % (a.get("보고서") or "", a.get("접수번호") or "", a.get("접수일") or "", a.get("기간") or "?")


# ══════════════════════════════════════════════════════════ 받기 · 이어받기

def _작업폴더():
    """수집 도구를 돌릴 작업 폴더 — 키트 스크립트 사본(도구는 `_raw/` 를 스크립트 부모에 잡는다). 스크립트가 바뀌었으면 다시 복사."""
    뿌 = os.path.join(원천뿌리(), "_작업", "키트")
    지문 = hashlib.sha256()
    for n in sorted(os.listdir(여기)):
        p = os.path.join(여기, n)
        if os.path.isfile(p) and n.endswith(".py"):
            지문.update(n.encode("utf-8"))
            지문.update(str(os.path.getmtime(p)).encode())
    지 = 지문.hexdigest()[:16]
    표 = os.path.join(뿌, ".지문")
    if not (os.path.exists(표) and io.open(표, encoding="utf-8").read().strip() == 지):
        if os.path.isdir(os.path.join(뿌, "스크립트")):
            shutil.rmtree(os.path.join(뿌, "스크립트"))
        shutil.copytree(여기, os.path.join(뿌, "스크립트"), ignore=shutil.ignore_patterns("__pycache__", "_*시험*.py"))
        io.open(표, "w", encoding="utf-8").write(지)
    return 뿌


def _돌기(뿌, args, 기록):
    환 = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1")
    r = subprocess.run([sys.executable, "-X", "utf8"] + args, cwd=뿌, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", env=환, timeout=3600)
    끝 = [x for x in ((r.stdout or "") + (r.stderr or "")).splitlines() if x.strip()]
    기록.append({"명령": " ".join(os.path.basename(a) if i == 0 else a for i, a in enumerate(args)), "rc": r.returncode,
               "끝줄": (끝[-1] if 끝 else "")[:200]})
    return r.returncode


def 미국받기인자(티커, 기준일=None, 평가기준일=None):
    """sec_fetch 명령 — 기준일이 있으면 기준일 분기 보고를 반드시 받게 `--기준일` 을 넘긴다(옛 동작은 최신 둘 — F12 · F24 · F29 · F43 · F44).
    `기준일` 은 재무기준일 F · `평가기준일`(T)이 F 와 다르면 `--평가기준일` 도 넘긴다(재무기준일 점검)."""
    return (["스크립트/sec_fetch.py", "--ticker", 티커] + (["--기준일", 기준일] if 기준일 else [])
            + (["--평가기준일", 평가기준일] if 평가기준일 and 평가기준일 != 기준일 else []))


def 받기(국가, 종목, 기준일=None, 회사=None, 원문해수=6, 조용=False, 평가기준일=None):
    """수집 도구를 작업 폴더에서 돌리고 산출을 캐시에 쌓는다 → 요약 dict(rc 포함)."""
    국가 = 국가.upper()
    뿌 = _작업폴더()
    raw = os.path.join(뿌, "_raw")
    if os.path.isdir(raw):
        shutil.rmtree(raw)
    os.makedirs(raw)
    씨앗(국가, 종목, raw, 조용=True)                                    # 이미 받은 원문을 먼저 — 도구가 다시 받지 않는 파일은 그대로 쓰인다
    기록 = []
    if 국가 == "KR":
        if not 기준일:
            raise ValueError("국내 받기에는 --기준일 이 있어야 한다(dart_fetch.py 가 그 기준일의 직전 보고서를 고른다)")
        회사 = 회사 or ((_읽기(os.path.join(회사자리(국가, 종목), "목록.json")) or {}).get("식별") or {}).get("고유번호")
        if not 회사:
            import dart_fetch                                       # noqa: PLC0415 — 고유번호표(corpCode.xml)는 공용 원천 자리에 한 번만
            회사 = dart_fetch.고유번호풀기([종목정리(국가, 종목)], 캐시=os.path.join(원천뿌리(), "_dartcache")).get(종목정리(국가, 종목))
        if not 회사:
            raise ValueError("고유번호를 못 풀었다(%s) — --회사 로 준다" % 종목)
        rc = _돌기(뿌, ["스크립트/dart_fetch.py", "--회사", 회사, "--기준일", 기준일, "--원문해수", str(원문해수), "--결산월확인"]
                  + (["--평가기준일", 평가기준일] if 평가기준일 and 평가기준일 != 기준일 else []), 기록)
        도구 = "dart_fetch.py"
    else:
        rc = _돌기(뿌, 미국받기인자(종목정리(국가, 종목), 기준일, 평가기준일), 기록)
        도구 = "sec_fetch.py"
    낸 = {"국가": 국가, "종목": 종목정리(국가, 종목), "rc": rc, "기록": 기록}
    if rc == 0:
        낸.update(넣기(국가, 종목, raw, 도구="%s(원천축적 받기 %s)" % (도구, _지금()[:10]), 종목풀=False, 조용=조용))
    elif not 조용:
        print("받기 실패 %s %s — %s" % (국가, 종목, 기록[-1] if 기록 else ""))
    return 낸


def 새공시(국가, 종목, 평가기준일=None):
    """as-of 뒤에 나온 정기 보고 → (목록, 까닭). 네트워크 한 번. 캐시가 없으면 (None, 까닭).
    `평가기준일`(T)을 주면 T 까지 제출된 것만 본다(T 뒤 제출은 그날의 정보 집합 밖) — 없으면 오늘까지(옛 동작)."""
    국가 = 국가.upper()
    목 = _읽기(os.path.join(회사자리(국가, 종목), "목록.json"))
    if not 목 or not 목.get("asof"):
        return None, "캐시가 없거나 as-of 를 못 읽었다 — 받기부터"
    a = 목["asof"]
    if 국가 == "KR":
        import dart_fetch                                           # noqa: PLC0415
        if not dart_fetch.KEY:
            return None, "OPENDART_API_KEY 가 환경변수에 없다"
        시작 = (datetime.date.fromisoformat(a["접수일"]) + datetime.timedelta(days=1)).strftime("%Y%m%d")
        회사 = (목.get("식별") or {}).get("고유번호") or a.get("고유번호")
        끝날 = (평가기준일 or datetime.date.today().isoformat()).replace("-", "")[:8]
        j = dart_fetch._get("list.json", corp_code=회사, bgn_de=시작, end_de=끝날,
                            pblntf_ty="A", page_count=100).json()
        if j.get("status") == "013":
            return [], "정기공시 0건(%s 뒤)" % a["접수일"]
        if j.get("status") not in (None, "000"):
            return None, "OpenDART status %s" % j.get("status")
        새 = [{"보고서": x.get("report_nm"), "접수번호": x.get("rcept_no"), "접수일": x.get("rcept_dt"), "기간": _기간(x.get("report_nm"))}
             for x in j.get("list") or [] if re.search(r"(사업|반기|분기)보고서", x.get("report_nm") or "")]
        return 새, "정기공시 %d건(%s 뒤)" % (len(새), a["접수일"])
    import requests                                                 # noqa: PLC0415
    연락 = os.environ.get("SEC_CONTACT_EMAIL")
    if not 연락:
        return None, "SEC_CONTACT_EMAIL 이 환경변수에 없다"
    cik = (목.get("식별") or {}).get("CIK") or a.get("CIK")
    r = requests.get("https://data.sec.gov/submissions/CIK%010d.json" % int(cik),
                     headers={"User-Agent": "DCF-research %s" % 연락, "Host": "data.sec.gov"}, timeout=60)
    if r.status_code != 200:
        return None, "SEC submissions HTTP %d" % r.status_code
    rec = (r.json().get("filings") or {}).get("recent") or {}
    새 = [{"보고서": f, "접수번호": rec["accessionNumber"][i], "접수일": rec["filingDate"][i], "기간": rec["reportDate"][i]}
         for i, f in enumerate(rec.get("form") or []) if f in 정기양식 and (rec["filingDate"][i], rec["accessionNumber"][i]) > (a["접수일"], a["접수번호"])
         and (not 평가기준일 or rec["filingDate"][i] <= 평가기준일)]
    return 새, "정기 보고 %d건(%s 뒤)" % (len(새), a["접수일"])


def 이어받기(국가, 종목, 기준일=None, 확인만=False, 조용=False, 평가기준일=None):
    """`기준일` = 재무기준일 F(없으면 새 공시의 마지막 기간 끝) · `평가기준일` = T(주면 T 까지 제출된 공시만 · 받는 도구에 넘겨 점검)."""
    새, 까닭 = 새공시(국가, 종목, 평가기준일)
    자리 = 회사자리(국가, 종목)
    목p = os.path.join(자리, "목록.json")
    목 = _읽기(목p)
    if 새 is None:
        if not 조용:
            print("이어받기 %s %s — 확인 못 함: %s" % (국가, 종목, 까닭))
        return {"국가": 국가, "종목": 종목, "rc": 발견, "까닭": 까닭}
    목["확인일"] = _지금()
    목["이력"].append({"일시": 목["확인일"], "동작": "확인", "까닭": 까닭, "새공시": 새})
    _쓰기(목p, 목)
    if not 새:
        if not 조용:
            print("이어받기 %s %s — %s · 받지 않았다(as-of %s)" % (국가, 종목, 까닭, _asof글(목.get("asof"))))
        return {"국가": 국가, "종목": 종목, "rc": 통과, "까닭": 까닭, "받음": False}
    if 확인만:
        if not 조용:
            print("이어받기 %s %s — %s · --확인만 이라 받지 않았다" % (국가, 종목, 까닭))
        return {"국가": 국가, "종목": 종목, "rc": 통과, "까닭": 까닭, "받음": False, "새공시": 새}
    if 국가.upper() == "KR" and not 기준일:
        끝 = max((x.get("기간") or "") for x in 새)
        if 끝:
            y, m = int(끝[:4]), int(끝[5:7])
            기준일 = (datetime.date(y + (m == 12), m % 12 + 1, 1) - datetime.timedelta(days=1)).isoformat()
    if 국가.upper() != "KR" and not 기준일 and 평가기준일:
        기준일 = max((x.get("기간") or "") for x in 새) or None       # T 까지 제출된 마지막 정기 보고의 기간 끝 = F
    낸 = 받기(국가, 종목, 기준일=기준일, 조용=조용, 평가기준일=평가기준일)
    낸.update({"까닭": 까닭, "받음": 낸.get("rc") == 0, "새공시": 새})
    return 낸


# ══════════════════════════════════════════════════════════ 상태 · 묶기

def 상태(국가=None):
    """쌓인 회사마다 [{국가 · 종목 · 회사명 · as-of · 조회일 · 확인일 · 파일수 · 크기}]."""
    낸 = []
    for c in ([국가.upper()] if 국가 else ["KR", "US"]):
        d = os.path.join(원천뿌리(), c)
        if not os.path.isdir(d):
            continue
        for s in sorted(os.listdir(d)):
            목 = _읽기(os.path.join(d, s, "목록.json"))
            if not 목:
                continue
            낸.append({"국가": c, "종목": s, "회사명": 목.get("회사명"), "asof": 목.get("asof"), "조회일": 목.get("조회일"),
                      "확인일": 목.get("확인일"), "파일수": len(목.get("파일") or {}),
                      "크기MB": round(sum(v.get("크기") or 0 for v in (목.get("파일") or {}).values()) / 1e6, 1)})
    return 낸


def 묶기(출력, 판, 국가=None):
    """배포 묶음 — 공시 원천만(시세 뺌) · 회사마다 목록 + ZIP 하나 + 묶음 목록. 키 · 연락처는 원천 파일에 없다(수집 도구가 쓰지 않는다)."""
    os.makedirs(출력, exist_ok=True)
    zp = os.path.join(출력, "원천축적_판%s.zip" % 판)
    목록 = {"형식": 형식, "판": 판, "만든날": _지금(), "회사": []}
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
        for r in 상태(국가):
            자리 = os.path.join(원천뿌리(), r["국가"], r["종목"])
            목 = _읽기(os.path.join(자리, "목록.json"))
            실은 = {k: v for k, v in 목["파일"].items() if v.get("배포")}
            for 칸 in 실은:
                z.write(os.path.join(자리, 칸.replace("/", os.sep)), "%s/%s/%s" % (r["국가"], r["종목"], 칸))
            목2 = dict(목, 파일=실은)
            z.writestr("%s/%s/목록.json" % (r["국가"], r["종목"]), json.dumps(목2, ensure_ascii=False, indent=1))
            목록["회사"].append({"국가": r["국가"], "종목": r["종목"], "asof": 목.get("asof"), "파일수": len(실은),
                              "뺀시세": len(목["파일"]) - len(실은)})
    _쓰기(os.path.join(출력, "원천축적_판%s.목록.json" % 판), 목록)
    return zp, 목록


def main(argv=None):
    ap = argparse.ArgumentParser(allow_abbrev=False, description="원천 축적 — 공시 원천을 공용 캐시에 쌓고 as-of 뒤만 받는다")
    sp = ap.add_subparsers(dest="명령")
    for 이름 in ("넣기", "받기", "이어받기", "씨앗"):
        p = sp.add_parser(이름, allow_abbrev=False)
        p.add_argument("--국가", required=True, choices=["KR", "US", "kr", "us"])
        p.add_argument("--종목", required=True)
        if 이름 in ("넣기", "씨앗"):
            p.add_argument("--raw", required=True, help="회차 `_raw/` 폴더")
        if 이름 in ("받기", "이어받기"):
            p.add_argument("--기준일", "--재무기준일", dest="기준일",
                           help="재무기준일 F YYYY-MM-DD — 받을 정기 보고의 기간 끝(옛 이름 --기준일 은 지금 뜻 그대로)")
        if 이름 in ("받기", "이어받기", "씨앗"):
            p.add_argument("--평가기준일", default=None,
                           help="평가기준일 T YYYY-MM-DD — 이어받기는 T 까지 제출된 공시만 · 받는 도구의 재무기준일 점검")
            p.add_argument("--가정", default=None, help="가정 파일 — 날짜 인자를 비우면 기준일.py 로 F · T 를 푼다(F 가 없으면 F = T)")
        if 이름 == "받기":
            p.add_argument("--회사", help="국내 고유번호(8자리) — 없으면 캐시 · corpCode 에서 푼다")
            p.add_argument("--원문해수", type=int, default=6)
        if 이름 == "이어받기":
            p.add_argument("--확인만", action="store_true")
        if 이름 == "씨앗":
            p.add_argument("--덮어쓰기", action="store_true")
            p.add_argument("--종목풀", metavar="평가기준일",
                           help="그 평가기준일 T 의 다른 회사 개념 추출(cc_<티커>.json)도 `_raw/peers/` 로")
            p.add_argument("--기준일", "--재무기준일", dest="기준일",
                           help="회차 재무기준일 F — 옮긴 원천에 기준일을 담은 분기 보고가 있나 대 보고 없으면 경보 · 받는 명령"
                                "(옛 이름 --기준일 은 지금 뜻 그대로)")
        if 이름 == "넣기":
            p.add_argument("--종목풀없이", action="store_true")
    p = sp.add_parser("상태", allow_abbrev=False)
    p.add_argument("--국가")
    p.add_argument("--json")
    p = sp.add_parser("묶기", allow_abbrev=False)
    p.add_argument("--출력", required=True)
    p.add_argument("--판", required=True)
    p.add_argument("--국가")
    a = ap.parse_args(argv)
    if getattr(a, "가정", None) or getattr(a, "평가기준일", None):
        import 기준일인자                                         # noqa: PLC0415
        a.기준일 = 기준일인자.풀기(a.기준일, a.가정, 기준일인자.재무, 인자="--기준일")
        a.평가기준일 = 기준일인자.풀기(a.평가기준일, a.가정, 기준일인자.평가, 인자="--평가기준일")
    try:
        if a.명령 == "넣기":
            r = 넣기(a.국가, a.종목, a.raw, 종목풀=not a.종목풀없이)
            return 통과 if (r["더함"] + r["바꿈"] + r["같음"]) else 발견
        if a.명령 == "씨앗":
            r = 씨앗(a.국가, a.종목, a.raw, a.덮어쓰기, a.종목풀, 기준일=a.기준일)
            return 통과 if (r and not (r.get("기준일대조") or {}).get("경보")) else 발견
        if a.명령 == "받기":
            return 통과 if 받기(a.국가, a.종목, a.기준일, a.회사, a.원문해수, 평가기준일=a.평가기준일)["rc"] == 0 else 발견
        if a.명령 == "이어받기":
            return 이어받기(a.국가, a.종목, a.기준일, a.확인만, 평가기준일=a.평가기준일)["rc"]
        if a.명령 == "상태":
            표 = 상태(a.국가)
            for r in 표:
                print("%s %-8s %-24s %s · 파일 %d · %.1fMB · 확인 %s" % (r["국가"], r["종목"], (r["회사명"] or "")[:24],
                                                                 _asof글(r["asof"]), r["파일수"], r["크기MB"], r["확인일"] or "—"))
            print("쌓인 회사 %d곳(%s)" % (len(표), 원천뿌리()))
            if a.json:
                _쓰기(a.json, {"형식": 형식, "만든날": _지금(), "회사": 표})
            return 통과
        if a.명령 == "묶기":
            zp, 목 = 묶기(a.출력, a.판, a.국가)
            print("묶기 — %d곳 · %s" % (len(목["회사"]), zp))
            return 통과
    except (ValueError, OSError) as e:
        print("입력 오류 — %s" % e)
        return 입력오류
    ap.print_help()
    return 입력오류


if __name__ == "__main__":
    sys.exit(main())

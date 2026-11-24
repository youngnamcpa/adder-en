# -*- coding: utf-8 -*-
"""국내 법인 한계세율 — 세율표 캐시(JSON)와 조회 함수. 법령 원문(법제처 공개 API)에서 만든다.

왜 있는가 (펄어비스 회차 펄32)
    법인세 규칙: 「한계세율은 법령 원문에서 확인한다. 국내는 법인세법 제55조와 지방세법 제103조의20.
    시행일과 부칙 적용례를 함께 확인하고, 법인지방소득세를 법인세액의 10%로 계산하지 않는다」.
    회차는 law.go.kr 화면이 동적이라 원문을 못 읽었고, 2026년 지방소득세 표를 **로펌 해설로만**
    확인했다. 한계세율 27.5% vs 24.2% 가 멈춤 문항에 올라갈 만큼 값에 닿는 칸이다.

1차 출처 — 법제처 국가법령정보 공동활용 OPEN API (정적 JSON, 실측 2026-09-13)
    목록  https://www.law.go.kr/DRF/lawSearch.do?OC={OC}&target=eflaw&type=JSON&query=법인세법
    조문  https://www.law.go.kr/DRF/lawService.do?OC={OC}&target=eflaw&MST={일련번호}&efYd={시행일}&JO=005500&type=JSON
          (JO 는 조 4자리 + 가지 2자리: 제55조 005500 · 제103조의20 010320)
    부칙  같은 lawService 를 JO 없이 불러 「부칙」 블록에서 그 조문을 언급한 적용례·경과조치를 뽑는다
    **세율표는 조문 안에 이미지로 실리지만 alt 텍스트에 표가 글자로 함께 온다** — 그것을 파싱한다.
    **OC(API 신청 아이디)는 환경변수 `LAW_OC` 에서만 읽는다.** 코드에 기본값을 두지 않고 화면·파일에
    찍지 않는다(주소는 `OC={OC}` 로 가려 저장). 가이드의 예시 아이디를 쓰는 것은 남의 인증값을 쓰는
    것이다(2026-09-13 조정자 지시). **`LAW_OC` 가 없으면 네트워크를 타지 않고 캐시된 세율표만 쓰며
    「OC 없음 — 캐시만」을 알린다.**
    ※ 지금 들어 있는 `한계세율표_KR.json` 은 첫 수리 때 **가이드 예시 OC 로 조회**해 만든 것이다.
      값(조문 표·부칙 원문)은 법령에서 온 그대로 두되, 판마다 `출처주의` 칸에
      「가이드 예시 OC 로 조회 — 저자 OC 로 재확인 필요」를 달았다. 저자 OC 로 `갱신` 하면 사라진다.

세율표 JSON (`스크립트/한계세율표_KR.json`)
    {"법인세": [판, …], "지방소득세": [판, …]}  판마다
        적용시작(사업연도 개시일) · 시행일 · 공포일 · 공포번호 · 조문 · 구간[{초과, 이하, 세율}]
        · 구간_60조의2(있으면) · 출처URL · 부칙(원문 발췌) · 적용근거 · 확인일 · 확인상태
    **확인 못 한 연도·구간은 값을 비운다.** 표가 덮는 가장 이른 판의 시행일보다 앞선 사업연도는
    조회가 「미확인」을 낸다 — 옛 세율을 기억으로 채우지 않는다. 2차 자료(로펌 해설 등)로 넣은
    판이 있으면 확인상태를 「2차」로 적는다(이 도구가 만든 판은 전부 1차).

조회 규칙
    · 날짜 둘(2026-10-25 · `기준일.py`) — `--기준일`(별칭 `--평가기준일`)은 **평가기준일 T**(분석일)다. 법령 시행 · 공포는 T 기준이고
      재무기준일(최근 공시 분기말)로 자르지 않는다 — T 전에 공포된 개정은 쓴다(지금 뜻 그대로)
    · 사업연도 개시일(기본: 평가기준일 해의 1월 1일)에 적용되는 판 = **평가기준일까지 공포된 판** 중
      적용시작 ≤ 개시일인 마지막 판. 평가기준일 뒤에 공포된 개정은 쓰지 않고 비고에 적는다
    · 한계세율 = 과세표준이 속한 구간의 법인세율 + 같은 구간의 지방소득세 표준세율
    · 지방소득세는 **조례로 표준세율의 50% 범위에서 가감**할 수 있다(제103조의20②) — 본점 소재지
      조례 확인은 이 도구 밖이다. 비고에 그 사실을 적는다

사용
    python 스크립트/한계세율.py 갱신                       # API 로 표를 다시 만든다(네트워크)
    python 스크립트/한계세율.py 조회 --기준일 2026-06-30 --과세표준 50000000000
    python 스크립트/한계세율.py 조회 --기준일 2026-06-30 --과세표준 50000000000 --사업연도개시 2027-01-01
"""
from __future__ import annotations

import argparse
import datetime as dt
import io
import json
import os
import re
import sys
import time
import urllib.parse

sys.stdout.reconfigure(encoding="utf-8")
여기 = os.path.dirname(os.path.abspath(__file__))
표경로 = os.path.join(여기, "한계세율표_KR.json")
DRF = "https://www.law.go.kr/DRF/"
H = {"User-Agent": "Mozilla/5.0"}

법령 = {
    "법인세": {"법령명": "법인세법", "JO": "005500", "조문": "법인세법 제55조제1항", "조패턴": r"제55조(?!의)"},
    "지방소득세": {"법령명": "지방세법", "JO": "010320", "조문": "지방세법 제103조의20제1항",
               "조패턴": r"제103조의20(?!\d)"},
}


# ── 금액·표 파싱 ─────────────────────────────────────────────────────────
def 한글금액(s):
    """「3천억원」·「39억8천만원」·「200억」 → 원. 못 읽으면 None."""
    s = s.replace(",", "").replace("원", "").strip()
    if not s:
        return None
    합, 남 = 0, s
    for 단위, 배 in (("조", 10 ** 12), ("억", 10 ** 8), ("만", 10 ** 4)):
        if 단위 in 남:
            앞, 남 = 남.split(단위, 1)
            v = _작은수(앞)
            if v is None:
                return None
            합 += v * 배
    if 남:
        v = _작은수(남)
        if v is None:
            return None
        합 += v
    return 합


def _작은수(s):
    """「3천」·「8천」·「200」·「1천5백」 → 정수(만 미만 자리)."""
    if not s:
        return 1 if s == "" else None
    if re.fullmatch(r"\d+", s):
        return int(s)
    합, 남 = 0, s
    for 단위, 배 in (("천", 1000), ("백", 100), ("십", 10)):
        if 단위 in 남:
            앞, 남 = 남.split(단위, 1)
            합 += (int(앞) if 앞 else 1) * 배
    if 남:
        if not re.fullmatch(r"\d+", 남):
            return None
        합 += int(남)
    return 합


def _평표파싱(글):
    """상자 문자가 없는 판(실측: 지방세법 2021-01-01 시행본)은 칸이 붙어서 온다 —
    「…과세표준의 1천분의 102억원 초과200억원 이하…」. 세율 숫자와 다음 줄 경계 금액이 붙으므로
    **이번 줄의 상한(=다음 줄 하한)과 값이 같아지는 자리**에서 숫자를 가른다."""
    t = re.sub(r"\s+", " ", 글.replace("과세표준세율", " "))
    경계re = re.compile(r"(\d[0-9천백십억조만,]*원)\s*(초과|이하)")
    구간, pos = [], 0
    while True:
        m = 경계re.search(t, pos)
        if not m:
            break
        아래, 위 = 0, None
        while m and m.start() - pos <= 1:
            v = 한글금액(m.group(1))
            if m.group(2) == "초과":
                아래 = v
            else:
                위 = v
            pos = m.end()
            m = 경계re.match(t, pos) or 경계re.match(t, pos + 1)
        r = re.compile(r"(100분의|1천분의|1000분의)\s*(\d+(?:\.\d+)?)([천백십억조만]*원\s*(?:초과|이하))?").search(t, pos)
        if not r:
            break
        분모 = 100.0 if r.group(1) == "100분의" else 1000.0
        숫자, 꼬리 = r.group(2), r.group(3)
        if 꼬리 and 위 is not None:
            단위 = re.match(r"[천백십억조만]*", 꼬리).group(0)
            쪼갬 = [k for k in range(1, len(숫자)) if not 숫자[k:].startswith("0") and 한글금액(숫자[k:] + 단위) == 위]
            if not 쪼갬:
                break
            세율문자, pos = 숫자[:쪼갬[0]], r.start(2) + 쪼갬[0]
        else:
            세율문자, pos = 숫자, r.end(2)
        구간.append({"초과": 아래, "이하": 위, "세율": round(float(세율문자) / 분모, 6)})
    return 구간


def 세율표파싱(글):
    """상자 표 글자 → [{초과, 이하, 세율}]. 표가 아니면 []."""
    if "├" not in 글 and "│" not in 글:
        return _평표파싱(글)
    구간 = []
    for 줄 in re.split(r"[├└]", 글):
        경계 = re.findall(r"([0-9천백십억조만,]+원)\s*(초과|이하)", 줄)
        율 = re.findall(r"(100분의|1천분의|1000분의)\s*(\d+(?:\.\d+)?)", 줄)
        if not 경계 or not 율:
            continue
        분모 = 100.0 if 율[-1][0] == "100분의" else 1000.0
        세율 = round(float(율[-1][1]) / 분모, 6)
        아래, 위 = 0, None
        for 금액, 뜻 in 경계:
            v = 한글금액(금액)
            if 뜻 == "초과":
                아래 = v
            else:
                위 = v
        구간.append({"초과": 아래, "이하": 위, "세율": 세율})
    return 구간


def 조문표들(조문json):
    """lawService JO 응답 → 제1항 안의 표 글자 목록(호 순서)."""
    b = 조문json.get("법령", {})
    cs = (b.get("조문") or {}).get("조문단위") or []
    if isinstance(cs, dict):
        cs = [cs]
    표들, 개정 = [], ""
    for c in cs:
        if c.get("조문여부") != "조문":
            continue
        항들 = c.get("항") or []
        if isinstance(항들, dict):
            항들 = [항들]
        for 항 in 항들:
            if not str(항.get("항번호", "")).startswith("①"):
                continue
            개정 = 항.get("항내용", "")
            조각 = [항.get("항내용", "")]
            호들 = 항.get("호") or []
            if isinstance(호들, dict):
                호들 = [호들]
            조각 += [h.get("호내용", "") for h in 호들]
            for t in 조각:
                for m in re.finditer(r"<img[^>]*>(.*?)</img>", t.replace("<\\/img>", "</img>"), re.S):
                    표들.append(m.group(1))
    m = re.findall(r"(\d{4})\.\s*(\d{1,2})\.\s*(\d{1,2})", 개정.split("<개정")[-1]) if "<개정" in 개정 else []
    마지막개정 = ("%s%02d%02d" % (m[-1][0], int(m[-1][1]), int(m[-1][2]))) if m else None
    return 표들, 마지막개정


def 부칙발췌(전체json, 공포일, 조패턴):
    """공포일이 같은 부칙에서 그 조문을 언급한 조(적용례·경과조치)를 뽑는다."""
    bu = ((전체json.get("법령") or {}).get("부칙") or {}).get("부칙단위") or []
    if isinstance(bu, dict):
        bu = [bu]
    out, 일반 = [], []
    for x in bu:
        if str(x.get("부칙공포일자")) != str(공포일):
            continue
        t = x.get("부칙내용")
        if isinstance(t, list):
            t = " ".join(s if isinstance(s, str) else " ".join(s) for s in t)
        t = re.sub(r"\s+", " ", str(t))
        for 조 in re.split(r"(?=제\d+조(?:의\d+)?\()", t):
            if re.search(조패턴, 조) and re.match(r"제\d+조(?:의\d+)?\((적용례|경과조치|[^)]*적용례|[^)]*경과조치|시행일)", 조):
                out.append(조.strip()[:400])
            elif re.match(r"제\d+조\(일반적 적용례\)", 조):
                일반.append("[일반적 적용례 — 조문 언급 없음] " + 조.strip()[:300])
    return out or 일반


def 적용시작(부칙들, 시행일):
    """부칙 문장 → (사업연도 개시일, 근거). 경과조치 「YYYY년 M월 D일 전에 개시한 사업연도 … 종전」 이
    적용례보다 사업연도 기준을 더 정확히 말한다(지방세법 2023.3.14 실측: 적용례는 「납세의무 성립」,
    경과조치는 「2023년 1월 1일 전에 개시한 사업연도는 종전」)."""
    for s in 부칙들:
        m = re.search(r"(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일\s*이후\s*개시하는\s*사업연도", s)
        if m:
            return "%s-%02d-%02d" % (m.group(1), int(m.group(2)), int(m.group(3))), "부칙 적용례(날짜 명시)"
    for s in 부칙들:
        m = re.search(r"(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일\s*전에\s*개시한[^.]*사업연도[^.]*종전의 규정", s)
        if m:
            return ("%s-%02d-%02d" % (m.group(1), int(m.group(2)), int(m.group(3))),
                    "부칙 경과조치(그 날 전 개시 사업연도는 종전 규정) — 그 날 이후 개시분부터로 읽음")
    for s in 부칙들:
        if re.search(r"이 법 시행 이후 (최초로 )?개시하는 사업연도", s):
            return 시행일, ("부칙 일반적 적용례(이 법 시행 이후 개시하는 사업연도)" if s.startswith("[일반적")
                         else "부칙 적용례(이 법 시행 이후 개시하는 사업연도)")
        if re.search(r"이 법 시행 전에 개시한 사업연도.*종전의 규정", s):
            return 시행일, "부칙 경과조치(시행 전 개시 사업연도는 종전 규정) — 시행 이후 개시분부터로 읽음"
    return 시행일, "부칙 적용례 미확인 — 시행일로 둠"


# ── 갱신(네트워크) ───────────────────────────────────────────────────────
def _get(url):
    import requests
    for i in range(3):
        try:
            r = requests.get(url, headers=H, timeout=120)
            if r.status_code == 200:
                return r.json()
        except Exception:                                   # noqa: BLE001
            pass
        time.sleep(1.5 * (i + 1))
    raise IOError("법제처 API 응답 없음: %s" % url.split("OC=")[0])


def 갱신(부터="20170101", oc=None):
    """법제처 API 로 세율표를 새로 만든다. OC 가 없으면 None — 부르는 쪽이 캐시만 쓴다."""
    oc = oc or os.environ.get("LAW_OC")
    if not oc:
        return None
    오늘 = dt.date.today().isoformat()
    결과 = {"국가": "KR", "만든날": 오늘, "출처": "법제처 국가법령정보 공동활용 OPEN API(DRF · eflaw)",
          "주의": "확인 못 한 연도·구간은 값을 비운다. 표가 덮는 가장 이른 판보다 앞선 사업연도는 미확인",
          "OC": "환경변수 LAW_OC 에서 읽음(값은 기록하지 않음)"}
    for 세목, 정 in 법령.items():
        목록 = []
        for 쪽 in (1, 2, 3, 4, 5, 6, 7, 8):
            u = DRF + "lawSearch.do?OC=%s&target=eflaw&type=JSON&display=100&page=%d&query=%s" % (
                oc, 쪽, urllib.parse.quote(정["법령명"]))
            j = _get(u).get("LawSearch", {})
            laws = j.get("law") or []
            if isinstance(laws, dict):
                laws = [laws]
            if not laws:
                break
            목록 += [x for x in laws if x.get("법령명한글") == 정["법령명"]]
            if 쪽 * 100 >= int(j.get("totalCnt") or 0):
                break
        판들, 앞표 = [], None
        본 = set()
        for x in sorted(목록, key=lambda x: (x["시행일자"], x["공포일자"])):
            k = (x["법령일련번호"], x["시행일자"])
            if k in 본 or x["시행일자"] < 부터 or x["시행일자"] > 오늘.replace("-", ""):
                continue
            본.add(k)
            url = DRF + "lawService.do?OC=%s&target=eflaw&MST=%s&efYd=%s&JO=%s&type=JSON" % (
                oc, x["법령일련번호"], x["시행일자"], 정["JO"])
            try:
                표들, 개정일 = 조문표들(_get(url))
            except IOError:
                continue
            time.sleep(0.3)
            if not 표들:
                continue
            구간 = 세율표파싱(표들[0])
            구간2 = 세율표파싱(표들[1]) if len(표들) > 1 else []
            서명 = json.dumps([구간, 구간2])
            if 서명 == 앞표:
                continue
            앞표 = 서명
            공포일 = 개정일 or x["공포일자"]
            부칙들 = []
            try:
                전체 = _get(DRF + "lawService.do?OC=%s&target=eflaw&MST=%s&efYd=%s&type=JSON" % (
                    oc, x["법령일련번호"], x["시행일자"]))
                부칙들 = 부칙발췌(전체, 공포일, 정["조패턴"])
            except IOError:
                pass
            시행 = "%s-%s-%s" % (x["시행일자"][:4], x["시행일자"][4:6], x["시행일자"][6:])
            시작, 근거 = 적용시작(부칙들, 시행)
            첫판 = not 판들
            판들.append({
                "적용시작": 시작, "시행일": 시행,
                "공포일": "%s-%s-%s" % (공포일[:4], 공포일[4:6], 공포일[6:]),
                "공포번호": x["공포번호"] if 공포일 == x["공포일자"] else "(조문 개정일 %s — 목록 공포번호 %s 와 다름)" % (공포일, x["공포번호"]),
                "조문": 정["조문"], "구간": 구간, "구간_60조의2": 구간2 or None,
                "출처URL": url.replace("OC=%s&" % oc, "OC={OC}&"),
                "출처주의": "",
                "부칙": 부칙들, "적용근거": 근거 + (" · 표가 덮는 가장 이른 판 — 이 시행일 전 사업연도는 미확인" if 첫판 else ""),
                "확인일": 오늘,
                "확인상태": ("확인완료(법령 원문·1차)" if (부칙들 and "미확인" not in 근거)
                         else "확인완료(조문 원문·1차) · 적용례 미확인(적용시작=시행일로 둠)")})
        if 판들:
            판들[0]["덮는시작"] = 판들[0]["시행일"]
        결과[세목] = 판들
    return 결과


# ── 조회 ─────────────────────────────────────────────────────────────────
def 표읽기(p=None):
    return json.load(io.open(p or 표경로, encoding="utf-8"))


def _판고르기(판들, 기준일, 개시일):
    알던 = [p for p in 판들 if p["공포일"] <= 기준일]
    뒤 = [p for p in 판들 if p["공포일"] > 기준일 and p["적용시작"] <= 개시일]
    if not 판들 or 개시일 < 판들[0].get("덮는시작", 판들[0]["적용시작"]):
        return None, "미확인 — 세율표가 덮는 가장 이른 판(%s)보다 앞선 사업연도" % (
            판들[0].get("덮는시작") if 판들 else "없음")
    후보 = [p for p in 알던 if p["적용시작"] <= 개시일]
    if not 후보:
        return None, "미확인 — 평가기준일까지 공포된 판 중 이 사업연도에 적용되는 판이 없음"
    판 = sorted(후보, key=lambda p: (p["적용시작"], p["공포일"]))[-1]
    비고 = ""
    if 뒤:
        비고 = "평가기준일 뒤 공포된 개정(%s)이 이 사업연도에 적용되지만 기준일 당시 법이 아니라 쓰지 않음" % (
            ", ".join(p["공포일"] for p in 뒤))
    return 판, 비고


def _구간율(구간, 과세표준):
    for g in 구간:
        if 과세표준 > (g["초과"] or 0) and (g["이하"] is None or 과세표준 <= g["이하"]):
            return g
    if 과세표준 <= 0 and 구간:
        return 구간[0]
    return None


def 한계세율(기준일, 과세표준, 사업연도개시=None, 구분="일반", 표=None):
    """평가기준일·과세표준(원) → dict(법인세율, 지방소득세율, 한계세율, 근거…). 못 정하면 값 None."""
    표 = 표 or 표읽기()
    개시 = 사업연도개시 or "%s-01-01" % 기준일[:4]
    키 = "구간" if 구분 == "일반" else "구간_60조의2"
    out = {"평가기준일": 기준일, "사업연도개시": 개시, "과세표준": 과세표준, "구분": 구분,
           "법인세율": None, "지방소득세율": None, "한계세율": None, "확인상태": "미확인", "근거": {}}
    율 = {}
    for 세목 in ("법인세", "지방소득세"):
        판, 비고 = _판고르기(표.get(세목) or [], 기준일, 개시)
        if 판 is None:
            out["근거"][세목] = 비고
            continue
        g = _구간율(판.get(키) or [], 과세표준)
        if g is None:
            out["근거"][세목] = "미확인 — %s 구간표에 해당 구간 없음" % 키
            continue
        율[세목] = g["세율"]
        if 판.get("출처주의"):
            out.setdefault("출처주의", []).append("%s %s: %s" % (세목, 판["공포일"], 판["출처주의"]))
        out["근거"][세목] = {"조문": 판["조문"], "공포일": 판["공포일"], "시행일": 판["시행일"], "출처주의": 판.get("출처주의", ""),
                          "적용시작": 판["적용시작"], "구간": g, "출처URL": 판["출처URL"],
                          "확인일": 판["확인일"], "확인상태": 판["확인상태"], "적용근거": 판["적용근거"],
                          "비고": 비고}
    out["법인세율"] = 율.get("법인세")
    out["지방소득세율"] = 율.get("지방소득세")
    if len(율) == 2:
        out["한계세율"] = round(율["법인세"] + 율["지방소득세"], 6)
        상태 = {out["근거"][k]["확인상태"] for k in 율}
        out["확인상태"] = ("2차" if any("2차" in s for s in 상태) else
                        ("확인완료(법령 원문·1차)" if all(s.startswith("확인완료(법령") for s in 상태) else " · ".join(sorted(상태))))
    if out.get("출처주의") and out["한계세율"] is not None:
        out["확인상태"] += " · 출처주의(가이드 예시 OC 로 조회 — 저자 OC 로 재확인 필요)"
    out["비고"] = ("지방소득세는 표준세율이다 — 조례로 50% 범위 가감 가능(지방세법 제103조의20②), 본점 소재지 "
                 "조례 확인은 이 도구 밖. 법인지방소득세를 법인세액의 10%로 계산하지 않았다 — 조문 표를 따로 읽었다")
    return out


# ── 최저한세 · 세액공제 한도율(시점가정 208) — S6-12 ───────────────────────
# 조세특례제한법 제132조①(최저한세) — 과세표준 구간별 최저한세율(중소기업 7%). 법제처 원문(S6 리뷰 조회 2026-10-17)의 구간을 옮겼다 — 구간의 부분마다
# 그 세율을 거는 누진으로 계산한다(원문 재확인 대상).
# 확인상태: 리뷰 조회 1차 · 이 도구가 갱신하지 않는다(DRF 조회 `조문조회.py 조회 조세특례제한법 132` 로 다시 본다). 중소기업의 연구개발 세액공제(제10조)는
# 최저한세 대상이 아니다 — 그 공제는 한도 밖이다(엔진 풀 분리는 S6 미해소 — 판단 칸으로 적는다).
최저한세구간 = {"일반": [{"초과": 0, "이하": 10_000_000_000, "세율": 0.10}, {"초과": 10_000_000_000, "이하": 100_000_000_000, "세율": 0.12},
                    {"초과": 100_000_000_000, "이하": None, "세율": 0.17}],
            "중소기업": [{"초과": 0, "이하": None, "세율": 0.07}],
            "출처": "조세특례제한법 제132조제1항(법제처 원문 — S6 리뷰 조회 2026-10-17)",
            "확인상태": "1차(리뷰 조회 — 구간 세율) · 구간의 「부분」 누진 적용은 원문 재확인 필요(조문조회.py) · 이 도구 미갱신"}


def _누진세액(구간, 과세표준):
    세 = 0.0
    for g in 구간:
        lo, hi = g["초과"] or 0, g["이하"]
        if 과세표준 <= lo:
            break
        세 += ((min(과세표준, hi) if hi is not None else 과세표준) - lo) * g["세율"]
    return 세


def 세액공제한도율(기준일, 과세표준, 중소기업=False, 표=None):
    """시점가정 208(세액공제 한도율 = 과세표준 대비) — (법인세 산출세액 − 최저한세) ÷ 과세표준. 산출세액은 법인세법 제55조 누진(국세만 — 지방소득세는
    최저한세 계산 밖), 최저한세는 조특법 제132조① 구간(부분마다 그 세율 — 누진).
    → dict(한도율, 평균세율, 최저한세율, 근거). 세율표가 그 사업연도를 덮지 못하면 한도율 None."""
    표 = 표 or 표읽기()
    개시 = "%s-01-01" % 기준일[:4]
    판, 비고 = _판고르기(표.get("법인세") or [], 기준일, 개시)
    out = {"평가기준일": 기준일, "과세표준": 과세표준, "중소기업": bool(중소기업), "한도율": None, "근거": {}}
    if 판 is None or 과세표준 <= 0:
        out["근거"]["법인세"] = 비고 or "과세표준 0 이하"
        return out
    산출 = _누진세액(판.get("구간") or [], 과세표준)
    최구 = 최저한세구간["중소기업" if 중소기업 else "일반"]
    최율 = _누진세액(최구, 과세표준) / 과세표준                 # 구간의 「부분」마다 그 세율(누진) — 원문 재확인 대상(확인상태)
    out.update({"평균세율": round(산출 / 과세표준, 6), "최저한세율": round(최율, 6), "한도율": round(max(0.0, 산출 / 과세표준 - 최율), 6),
                "근거": {"법인세": "%s(%s 시행)" % (판["조문"], 판["시행일"]), "최저한세": 최저한세구간["출처"], "확인상태": 최저한세구간["확인상태"]},
                "비고": "한도율 = 평균 법인세율(국세) − 최저한세율. 중소기업의 연구개발 세액공제(조특법 제10조)는 최저한세 대상이 아니다 — 그 공제는 한도 밖에 둔다"})
    return out


# ── 미국 — 일반 사업 세액공제 한도(IRC §38(c)) 근사 (S6 결정 ②, 2026-10-17 S8 개선 1) ────────────
# §38(c)(1): 일반 사업 세액공제는 「순 소득세 − max(잠정 최저세, 순 정규세 중 2만 5천 달러 초과분의 25%)」까지 쓴다. 큰 회사(정규세가 2만 5천 달러를
# 훨씬 넘고 잠정 최저세가 걸리지 않는 회사)는 **정규세의 약 75%** 다. 208 은 과세표준 대비라 208 ≈ 0.75 × 연방 법인세율(21% — IRC §11(b)).
# 주세는 연방 세액공제의 한도 밖이라 넣지 않는다. 근사다 — 잠정 최저세(CAMT · AMT)가 걸리는 회사 · 2만 5천 달러 근처의 작은 회사는 근거에 적고 고친다.
미국연방세율 = 0.21
미국38c몫 = 0.75


def 세액공제한도율_미국(연방세율=미국연방세율):
    """시점가정 208(세액공제 한도율 — 과세표준 대비)의 미국 기본값 = 0.75 × 연방세율. → dict(한도율, 근거, 확인상태)."""
    return {"한도율": round(미국38c몫 * 연방세율, 6), "관할": "US",
            "근거": {"조문": "IRC §38(c)(1) — 일반 사업 세액공제 한도(정규세의 약 75%% — 큰 회사 근사) · 연방세율 IRC §11(b) %.0f%%" % (연방세율 * 100)},
            "확인상태": "근사 — 잠정 최저세(CAMT · AMT)가 걸리거나 정규세가 2만 5천 달러 근처면 원문 계산으로 고친다",
            "비고": "208 = 0.75 × 연방세율. 주세는 연방 세액공제 한도 밖"}


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False, description="국내 법인 한계세율 — 세율표 캐시·조회")
    sub = ap.add_subparsers(dest="명령", required=True)
    g = sub.add_parser("갱신", help="법제처 공개 API 로 세율표를 다시 만든다", allow_abbrev=False)
    g.add_argument("--부터", default="20170101", help="이 시행일 이후 판만 (YYYYMMDD)")
    g.add_argument("--출력", default=표경로)
    q = sub.add_parser("조회", allow_abbrev=False)
    q.add_argument("--기준일", "--평가기준일", dest="기준일", required=True,
                   help="평가기준일 T YYYY-MM-DD — 이 날까지 공포된 판만 쓴다(재무기준일이 아니다)")
    q.add_argument("--과세표준", type=float, required=True, help="원")
    q.add_argument("--사업연도개시", default=None, help="YYYY-MM-DD (기본: 기준일 해 1월 1일)")
    q.add_argument("--구분", default="일반", choices=["일반", "60조의2"])
    q.add_argument("--표", default=None)
    h = sub.add_parser("한도율", help="시점가정 208(세액공제 한도율) — 국내: 평균 법인세율 − 최저한세율(조특법 제132조①) · 미국: §38(c) 근사", allow_abbrev=False)
    h.add_argument("--기준일", "--평가기준일", dest="기준일", default=None,
                   help="평가기준일 T YYYY-MM-DD — 이 날까지 공포된 판만 쓴다(재무기준일이 아니다)")
    h.add_argument("--과세표준", type=float, default=None, help="원")
    h.add_argument("--중소기업", action="store_true")
    h.add_argument("--관할", default="KR", choices=["KR", "US"], help="US 면 IRC §38(c) 근사(0.75 × 연방세율 — S6 결정 ②)")
    a = ap.parse_args()
    if a.명령 == "한도율" and a.관할 == "US":
        r = 세액공제한도율_미국()
        print(json.dumps(r, ensure_ascii=False, indent=1))
        return 0
    if a.명령 == "한도율":
        if not a.기준일 or a.과세표준 is None:
            print("국내 한도율은 --기준일 과 --과세표준 이 있어야 합니다")
            return 2
        r = 세액공제한도율(a.기준일, a.과세표준, a.중소기업)
        print(json.dumps(r, ensure_ascii=False, indent=1))
        return 0 if r["한도율"] is not None else 1
    if a.명령 == "갱신":
        d = 갱신(a.부터)
        if d is None:
            print("OC 없음 — 캐시만: 환경변수 LAW_OC 가 없어 법제처 API 를 부르지 않았다. "
                  "세율표 %s 를 그대로 둔다%s" % (a.출력, "" if os.path.exists(a.출력) else " (캐시 파일도 없다)"))
            return 0
        json.dump(d, io.open(a.출력, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("→ %s" % a.출력)
        for 세목 in ("법인세", "지방소득세"):
            for p in d.get(세목, []):
                print("  %-5s 적용 %s (시행 %s·공포 %s) %s · %s · %s" % (
                    세목, p["적용시작"], p["시행일"], p["공포일"],
                    " / ".join("%s~%s %.3g%%" % ((g["초과"] or 0) / 1e8, (g["이하"] / 1e8) if g["이하"] else "", g["세율"] * 100)
                               for g in p["구간"]), p["적용근거"][:40], p["확인상태"]))
        return 0
    r = 한계세율(a.기준일, a.과세표준, a.사업연도개시, a.구분, 표읽기(a.표) if a.표 else None)
    print(json.dumps(r, ensure_ascii=False, indent=1))
    return 0 if r["한계세율"] is not None else 1


if __name__ == "__main__":
    sys.exit(main())

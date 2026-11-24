# -*- coding: utf-8 -*-
"""kirs_리포트 — 한국IR협의회 기업리서치센터 리서치 보고서(인소싱 · 아웃소싱 · 밸류업)를 종목코드로 찾고, 기준일 앞 보고서만 받아 글을 뽑는다 (2026-10-25 신설).

왜 만들었나(2026-10-25 결정) — 고객이 특정 종목 DCF 를 돌려 달라고 하면 정보 검색 갈래가 이 보고서들도 확인해 끌어와야 한다.
  협의회가 직접 쓰거나(인소싱) 맡겨 쓴(아웃소싱 — 신용평가 · 기술평가 회사) 중립 보고서라 증권사 커버리지가 얇은 중소형주에 특히 쓸모가 있다.
  쓰는 법은 증권사 리포트와 같다 — **모델의 축 · 사업 구조 · 원 출처가 달린 산업 자료 · 리스크 요인은 가져오고, 보고서가 낸 추정치 · 목표가 ·
  적정가치는 가져오지 않는다.** 회사가 공시하지 않는 과거 칸도 추정치로 본다. 기준일 앞 보고서만 근거로 쓰고, 뒤 보고서는 목록에만 `기준일뒤: true`.

사이트 구조(2026-10-25 실측 · 읽기만)
  목록   https://www.kirs.or.kr/research/<게시판>.html?mode=search&area=code2&keyword=<6자리>   (area: code 종목명 · subject 제목 · code2 종목코드 · content 작성자)
         쪽 넘김은 `?dbname=<db>&page=<N>&mode=search&area=…&keyword=…` · 한 쪽 10줄 · 「전체 <span>N</span> 개」
  줄     종목명(코드) · 제목 · 작성자 · 등록일자 · 첨부(PDF 바로 받기 a href) · 게시물 번호는 PDF 아이콘의 `add_hit(<번호>)` — 상세 쪽은 없다
  PDF    https://w4.kirs.or.kr/download/<research|valueup>/<YYMMDD>_<파일이름>.pdf — 로그인 없이 열린다. 여러 종목이 한 파일(산업 묶음)을 가리키기도 한다
  인증서 — 사이트 인증서 사슬을 certifi 묶음이 못 잇는다(실측). `truststore`(운영체제 인증서 저장소)를 쓰고, 없으면 그 사실을 적고 멈춘다(검증을 끄지 않는다).

명령
  python 스크립트/kirs_리포트.py 목록 --종목 <6자리> [--기준일 YYYY-MM-DD] [--게시판 인소싱|아웃소싱|밸류업|모두] [-o 목록.json]
  python 스크립트/kirs_리포트.py 받기 --종목 <6자리> --기준일 YYYY-MM-DD [--최근 1] [--게시판 …] [--raw _raw]
         → `<raw>/리포트/KIRS_<종목>_<YYYYMMDD>.pdf` · 곁에 `.txt`(pdf글.py) · 묶음 `<raw>/리포트/KIRS_<종목>.json`(계약 「KIRS리포트/1」)
  python 스크립트/kirs_리포트.py 목록 --html <목록.html> [--기준일 …]                                      # 네트워크 0 — 받아 둔 목록 쪽을 읽는다

받기 규칙 — 기준일 앞(발행일 ≤ 기준일) 최근 N건만 받는다(대량 내려받기 금지). 같은 파일이 있으면 다시 받지 않는다(캐시 — `캐시: true`).
  요청 사이 간격(기본 1.5초) · 재시도(연결 오류 · 5xx 세 번까지) · 403 · 404 · PDF 가 아닌 응답(로그인 쪽 따위)이면 그 자리에서 멈추고 까닭을 적는다.
출력에 발행기관 「한국IR협의회 기업리서치센터」 · 작성자 · 발행일 · 식별자(`KIRS-<게시판>-<게시물 번호>`)를 남긴다(리포트 기록 규칙 — 발행사 · 작성자 · 발행일 · 식별번호).
보고서 본문 · 추정치 · 목표가는 이 도구의 JSON 에 넣지 않는다 — 글(.txt)은 읽기용으로 곁에 둘 뿐이다.
회사 · 업종 이름은 이 도구에 없다(범용). 종료 코드 — 0 통과 · 1 발견(보고서 없음 · 받기 실패로 멈춤) · 2 입력오류.
"""
from __future__ import annotations

import argparse
import datetime
import io
import json
import os
import re
import sys
import time
from html.parser import HTMLParser
from urllib.parse import parse_qs, urlparse

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:                                    # noqa: BLE001
    pass

여기 = os.path.dirname(os.path.abspath(__file__))
if 여기 not in sys.path:
    sys.path.insert(0, 여기)
from 종료코드 import 통과, 발견, 입력오류  # noqa: E402

형식 = "KIRS리포트/1"
발행기관 = "한국IR협의회 기업리서치센터"
뿌리 = "https://www.kirs.or.kr/research/"
게시판들 = {"인소싱": "research22_1.html", "아웃소싱": "research.html", "밸류업": "valueup.html"}
파일머리 = {"인소싱": "KIRS", "아웃소싱": "KIRS아웃소싱", "밸류업": "KIRS밸류업"}
쪽크기 = 10
기본쪽상한 = 5
기본간격 = 1.5
기본재시도 = 3
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
      "Accept-Language": "ko-KR,ko;q=0.9"}
쓰는법 = ("모델의 축 · 사업 구조 · 원 출처가 달린 산업 자료 · 리스크 요인은 가져오고, 보고서가 낸 추정치 · 목표가 · 적정가치는 가져오지 않는다. "
       "회사가 공시하지 않는 과거 칸도 추정치로 본다. 기준일 앞 보고서만 근거 — 뒤 보고서는 `기준일뒤: true`.")
다루지않음 = {"AI 기업분석 보고서": 뿌리 + "ai_report.html", "기업분석(~2022.5)": 뿌리 + "tech2020_1.html",
           "산업분석(~2022.5)": 뿌리 + "tech2020_2.html", "Research Report(영문)": 뿌리 + "research_eng.html"}


class 멈춤(Exception):
    """받기를 더 이어 갈 수 없다 — 까닭을 적고 멈춘다."""


def _읽기(p, 기본=None):
    try:
        with io.open(p, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return 기본


def _쓰기(p, 것):
    os.makedirs(os.path.dirname(os.path.abspath(p)), exist_ok=True)
    임 = p + ".쓰는중"
    with io.open(임, "w", encoding="utf-8") as f:
        json.dump(것, f, ensure_ascii=False, indent=1)
    os.replace(임, p)


def 날짜(s):
    """「2026-10-21」 · 「2026.10.21」 · 「20261021」 → ISO | None."""
    s = (s or "").strip()
    m = re.search(r"(\d{4})[-.\s/]?(\d{1,2})[-.\s/]?(\d{1,2})", s)
    if not m:
        return None
    try:
        return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3))).isoformat()
    except ValueError:
        return None


def 종목코드인가(s):
    return bool(re.fullmatch(r"[0-9A-Z]{6}", s or ""))


# ═══ 목록 쪽 읽기 — 네트워크 0
class _줄파서(HTMLParser):
    """tbody 의 tr 마다 td 글 · 그 안의 href · onclick 을 모은다."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.본문 = False
        self.줄들 = []
        self.줄 = None
        self.칸 = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "tbody":
            self.본문 = True
        elif not self.본문:
            return
        elif tag == "tr":
            self.줄 = []
        elif tag == "td" and self.줄 is not None:
            self.칸 = {"글": [], "href": [], "onclick": [], "data-url": []}
            self.줄.append(self.칸)
        elif self.칸 is not None:
            for k in ("href", "onclick", "data-url"):
                if a.get(k):
                    self.칸[k].append(a[k])

    def handle_endtag(self, tag):
        if tag == "tbody":
            self.본문 = False
        elif tag == "tr" and self.줄 is not None:
            if self.줄:
                self.줄들.append(self.줄)
            self.줄, self.칸 = None, None
        elif tag == "td":
            self.칸 = None

    def handle_data(self, d):
        if self.칸 is not None:
            self.칸["글"].append(d)


def _글(칸):
    return re.sub(r"\s+", " ", "".join(칸["글"])).strip()


def 종목가르기(s):
    """「종목명 (012345)」 · 「종목명(012345)」 → (이름, 코드|None)."""
    s = re.sub(r"\s+", " ", s or "").strip()
    m = re.match(r"^(.*?)\s*\(\s*([0-9A-Z]{6})\s*\)\s*$", s)
    return (m.group(1).strip(), m.group(2)) if m else (s, None)


def 목록읽기(html, 게시판="인소싱"):
    """목록 쪽 HTML → {"전체": N|None, "db": 쪽 넘김의 dbname|None, "쪽수": N, "줄": [..]}. 줄은 종목 · 제목 · 작성자 · 발행일 · pdf · 번호."""
    p = _줄파서()
    p.feed(html or "")
    줄들 = []
    for 칸들 in p.줄들:
        글들 = [_글(c) for c in 칸들]
        if len(칸들) < 4:
            continue
        이름, 코드 = 종목가르기(글들[0])
        날 = next((날짜(g) for g in reversed(글들) if re.fullmatch(r"\d{4}-\d{2}-\d{2}", g or "")), None)
        if not 날:
            continue
        날자리 = max(i for i, g in enumerate(글들) if 날짜(g) == 날 and re.fullmatch(r"\d{4}-\d{2}-\d{2}", g))
        작성자 = 글들[날자리 - 1] if 날자리 >= 3 else None                  # 종목 · 제목 · (작성자) · 날짜 · 첨부 — AI 보고서처럼 작성자 칸이 없으면 None
        링크들 = [h for c in 칸들 for h in c["href"] + c["data-url"]]
        pdf = next((h for h in 링크들 if h.lower().split("?")[0].endswith(".pdf")), None)
        번호 = None
        for c in 칸들:
            for o in c["onclick"]:
                m = re.search(r"add_hit\(\s*(\d+)", o)
                if m:
                    번호 = int(m.group(1))
        파일이름 = os.path.basename(urlparse(pdf).path) if pdf else None
        줄들.append({"식별자": "KIRS-%s-%s" % (게시판, 번호) if 번호 is not None else None, "게시판": 게시판, "게시물번호": 번호,
                   "종목명": 이름, "종목코드": 코드, "제목": 글들[1], "작성자": 작성자, "발행일": 날, "pdf": pdf,
                   "파일이름에종목명없음": bool(파일이름 and 이름 and re.sub(r"\s", "", 이름) not in re.sub(r"\s", "", 파일이름))})
    m = re.search(r"전체\s*<span>\s*([\d,]+)\s*</span>", html or "")
    전체 = int(m.group(1).replace(",", "")) if m else None
    db = None
    for q in re.findall(r"href=['\"]?\?([^'\" >]+)", html or ""):
        v = parse_qs(q).get("dbname")
        if v:
            db = v[0]
            break
    if 전체:
        쪽수 = max(1, -(-전체 // 쪽크기))
    else:                                                    # 아웃소싱 게시판은 「전체 N 개」 가 없다 — 쪽 넘김 고리의 가장 큰 쪽 번호
        쪽들 = [int(x) for x in re.findall(r"[?&]page=(\d+)", html or "")]
        쪽수 = max([1] + 쪽들)
    return {"전체": 전체, "db": db, "쪽수": 쪽수, "줄": 줄들}


def 기준일가르기(줄들, 기준일):
    """줄마다 `기준일뒤`(발행일 > 기준일) 표지. 기준일이 없으면 None 으로 둔다 → 같은 목록(새 사전)."""
    낸 = []
    for r in 줄들:
        r = dict(r)
        r["기준일뒤"] = (r["발행일"] > 기준일) if (기준일 and r.get("발행일")) else None
        낸.append(r)
    return 낸


def 고르기(줄들, 기준일, 최근=1):
    """기준일 앞(발행일 ≤ 기준일) · pdf 있는 줄 가운데 늦은 것부터 N건."""
    앞 = [r for r in 줄들 if r.get("pdf") and r.get("발행일") and r["발행일"] <= 기준일]
    앞.sort(key=lambda r: (r["발행일"], r.get("게시물번호") or 0), reverse=True)
    return 앞[:max(0, 최근)]


def 파일이름(줄, 종목, 같은날번호=None):
    머 = 파일머리.get(줄.get("게시판"), "KIRS")
    꼬 = ("_%s" % 같은날번호) if 같은날번호 else ""
    return "%s_%s_%s%s.pdf" % (머, 종목, 줄["발행일"].replace("-", ""), 꼬)


# ═══ 네트워크 — 시험에서 `_get` · `_잠` 을 바꿔 끼운다
_세션 = None


def _준비():
    global _세션
    if _세션 is not None:
        return _세션
    try:
        import truststore                                    # noqa: PLC0415
        truststore.inject_into_ssl()
    except ImportError as e:
        raise 멈춤("truststore 가 없다 — 사이트 인증서 사슬을 certifi 묶음이 못 잇는다(pip install truststore). 검증을 끄지 않는다") from e
    import requests                                          # noqa: PLC0415
    _세션 = requests.Session()
    _세션.headers.update(UA)
    return _세션


def _get(url, params=None, timeout=40):
    """→ (상태, 내용 바이트, content-type)."""
    s = _준비()
    r = s.get(url, params=params, timeout=timeout)
    return r.status_code, r.content, r.headers.get("content-type") or ""


def _잠(초):
    time.sleep(초)


def _부르기(url, params=None, 간격=기본간격, 재시도=기본재시도, 셈=None):
    """간격 · 재시도를 두고 부른다 → (상태, 내용, 형식). 재시도 끝에도 안 되면 멈춤."""
    마지막 = None
    for k in range(max(1, 재시도)):
        if 셈 is not None:
            if 셈.get("호출"):
                _잠(간격 * (1 + k))
            셈["호출"] = 셈.get("호출", 0) + 1
        try:
            st, 바, 꼴 = _get(url, params)
        except 멈춤:
            raise
        except Exception as e:                               # noqa: BLE001 — 연결 오류는 재시도
            마지막 = "%s %s" % (type(e).__name__, str(e)[:120])
            continue
        if st >= 500:
            마지막 = "HTTP %s" % st
            continue
        return st, 바, 꼴
    raise 멈춤("%s — 재시도 %d번 끝에 실패(%s)" % (url, 재시도, 마지막))


def 목록받기(종목, 게시판="인소싱", 쪽상한=기본쪽상한, 간격=기본간격, 재시도=기본재시도, 셈=None):
    """종목코드 검색 → 그 게시판의 줄 전부(쪽상한까지) · 종목코드가 같은 줄만(코드를 못 읽은 줄은 `코드확인: false` 로 둔다)."""
    셈 = 셈 if 셈 is not None else {}
    url = 뿌리 + 게시판들[게시판]
    st, 바, _ = _부르기(url, {"mode": "search", "area": "code2", "keyword": 종목}, 간격, 재시도, 셈)
    if st != 200:
        raise 멈춤("목록 %s — HTTP %s" % (게시판, st))
    첫 = 목록읽기(바.decode("utf-8", "replace"), 게시판)
    줄들 = list(첫["줄"])
    for 쪽 in range(2, min(첫["쪽수"], 쪽상한) + 1):
        st, 바, _ = _부르기(url, {"dbname": 첫["db"] or "research", "page": 쪽, "mode": "search", "area": "code2", "keyword": 종목},
                         간격, 재시도, 셈)
        if st != 200:
            raise 멈춤("목록 %s %d쪽 — HTTP %s" % (게시판, 쪽, st))
        줄들 += 목록읽기(바.decode("utf-8", "replace"), 게시판)["줄"]
    낸 = []
    본 = set()
    for r in 줄들:
        if r.get("종목코드") not in (None, 종목):
            continue
        r["코드확인"] = r.get("종목코드") == 종목
        열 = (r.get("식별자"), r.get("pdf"), r.get("발행일"))
        if 열 in 본:
            continue
        본.add(열)
        낸.append(r)
    return {"게시판": 게시판, "주소": url, "전체": 첫["전체"], "쪽수": 첫["쪽수"], "읽은쪽": min(첫["쪽수"], 쪽상한), "줄": 낸}


def pdf받기(url, 낼곳, 간격=기본간격, 재시도=기본재시도, 셈=None):
    """PDF 한 건 → 낼곳. 이미 있으면 받지 않는다 → {"캐시": bool, "크기": n}. PDF 가 아니면 멈춤."""
    if os.path.exists(낼곳) and os.path.getsize(낼곳) > 0:
        with open(낼곳, "rb") as f:
            if f.read(5) == b"%PDF-":
                return {"캐시": True, "크기": os.path.getsize(낼곳)}
    st, 바, 꼴 = _부르기(url, None, 간격, 재시도, 셈)
    if st in (401, 403):
        raise 멈춤("PDF %s — HTTP %s(로그인 · 권한이 필요한 것으로 보인다 — 로그인하지 않는다)" % (os.path.basename(urlparse(url).path), st))
    if st != 200:
        raise 멈춤("PDF %s — HTTP %s" % (os.path.basename(urlparse(url).path), st))
    if 바[:5] != b"%PDF-":
        raise 멈춤("PDF 가 아닌 응답(%s · %d바이트) — 로그인 쪽이거나 주소가 바뀌었다" % (꼴[:40], len(바)))
    os.makedirs(os.path.dirname(os.path.abspath(낼곳)), exist_ok=True)
    임 = 낼곳 + ".받는중"
    with open(임, "wb") as f:
        f.write(바)
    os.replace(임, 낼곳)
    return {"캐시": False, "크기": len(바)}


def 글뽑기(pdf경로):
    """pdf글.py 로 글을 뽑아 곁에 .txt → {"글판정", "방법", "글파일"}."""
    import pdf글                                              # noqa: PLC0415
    txt = pdf경로[:-4] + ".txt"
    if os.path.exists(txt) and os.path.getsize(txt) > 0 and os.path.getmtime(txt) >= os.path.getmtime(pdf경로):
        return {"글판정": "읽힘(캐시)", "방법": None, "글파일": txt}
    r = pdf글.뽑기(pdf경로, True)
    if r["글"]:
        io.open(txt, "w", encoding="utf-8").write(r["글"])
    return {"글판정": r["판정"], "방법": r["방법"], "글파일": txt if r["글"] else None}


def 게시판고르기(s):
    s = (s or "인소싱").strip()
    if s == "모두":
        return list(게시판들)
    낸 = [x.strip() for x in s.split(",") if x.strip()]
    for x in 낸:
        if x not in 게시판들:
            raise ValueError("게시판은 %s · 모두 — 받은 값 %s" % (" · ".join(게시판들), x))
    return 낸


def 목록(종목, 기준일=None, 게시판=("인소싱",), 쪽상한=기본쪽상한, 간격=기본간격, 재시도=기본재시도, 조회일=None):
    """→ 계약 「KIRS리포트/1」 의 목록 부분."""
    if not 종목코드인가(종목):
        raise ValueError("종목은 6자리 코드 — 받은 값 %r" % 종목)
    셈 = {}
    판 = {"형식": 형식, "발행기관": 발행기관, "종목": 종목, "평가기준일": 기준일, "조회일": 조회일 or datetime.date.today().isoformat(),
         "쓰는법": 쓰는법, "게시판": [], "목록": [], "오류": [], "멈춤": None}
    for g in 게시판:
        try:
            r = 목록받기(종목, g, 쪽상한, 간격, 재시도, 셈)
        except 멈춤 as e:
            판["멈춤"] = str(e)
            break
        판["게시판"].append({k: r[k] for k in ("게시판", "주소", "전체", "쪽수", "읽은쪽")})
        if r["읽은쪽"] < r["쪽수"]:
            판["오류"].append("%s — %d쪽 가운데 %d쪽만 읽었다(--쪽상한)" % (g, r["쪽수"], r["읽은쪽"]))
        판["목록"] += 기준일가르기(r["줄"], 기준일)
    판["목록"].sort(key=lambda r: (r["발행일"], r.get("게시물번호") or 0), reverse=True)
    판["호출"] = 셈.get("호출", 0)
    판["커버리지"] = "있음" if 판["목록"] else ("봤고 없었다" if not 판["멈춤"] else "못 봤다")
    return 판


def 받기(종목, 기준일, raw=None, 최근=1, 게시판=("인소싱",), 쪽상한=기본쪽상한, 간격=기본간격, 재시도=기본재시도, 조회일=None, 글=True):
    """기준일 앞 최근 N건을 `<raw>/리포트/` 에 받고 글을 뽑는다 · 묶음 JSON 을 쓴다 → 판."""
    if not 기준일 or not 날짜(기준일) or 날짜(기준일) != 기준일:
        raise ValueError("기준일은 YYYY-MM-DD — 받은 값 %r" % 기준일)
    raw = raw or os.path.join(os.path.dirname(여기), "_raw")
    폴더 = os.path.join(raw, "리포트")
    판 = 목록(종목, 기준일, 게시판, 쪽상한, 간격, 재시도, 조회일)
    판["받음"] = []
    if not 판["멈춤"]:
        고른 = 고르기(판["목록"], 기준일, 최근)
        같은날 = {}
        for r in 고른:
            열 = (r["게시판"], r["발행일"])
            같은날[열] = 같은날.get(열, 0) + 1
            이름 = 파일이름(r, 종목, 같은날[열] if 같은날[열] > 1 else None)
            p = os.path.join(폴더, 이름)
            셈 = {"호출": 1}                                     # 목록을 이미 불렀다 — 첫 PDF 앞에도 간격을 둔다
            try:
                d = pdf받기(r["pdf"], p, 간격, 재시도, 셈)
            except 멈춤 as e:
                판["멈춤"] = str(e)
                break
            한 = {"식별자": r["식별자"], "발행일": r["발행일"], "작성자": r["작성자"], "파일": os.path.relpath(p, raw).replace("\\", "/"),
                 "캐시": d["캐시"], "크기": d["크기"]}
            if 글:
                g = 글뽑기(p)
                한.update({"글판정": g["글판정"], "글방법": g["방법"],
                          "글파일": os.path.relpath(g["글파일"], raw).replace("\\", "/") if g["글파일"] else None})
            판["받음"].append(한)
        if not 고른 and 판["목록"]:
            판["오류"].append("기준일(%s) 앞 보고서가 없다 — 목록의 %d건은 전부 기준일 뒤" % (기준일, len(판["목록"])))
    _쓰기(os.path.join(폴더, "KIRS_%s.json" % 종목), 판)
    return 판


def _요약(판):
    앞 = sum(1 for r in 판["목록"] if r.get("기준일뒤") is False)
    뒤 = sum(1 for r in 판["목록"] if r.get("기준일뒤") is True)
    return "KIRS %s — 보고서 %d건(기준일 앞 %d · 뒤 %d) · 호출 %d%s" % (
        판["종목"], len(판["목록"]), 앞, 뒤, 판.get("호출", 0), (" · 멈춤: %s" % 판["멈춤"]) if 판["멈춤"] else "")


def main(argv=None):
    ap = argparse.ArgumentParser(allow_abbrev=False, description="한국IR협의회 기업리서치센터 리서치 보고서 — 종목코드로 목록 · 기준일 앞 최근 N건 받기")
    sp = ap.add_subparsers(dest="명령")
    for 이름 in ("목록", "받기"):
        p = sp.add_parser(이름, allow_abbrev=False)
        p.add_argument("--종목", help="6자리 종목코드")
        p.add_argument("--기준일", required=(이름 == "받기"))
        p.add_argument("--게시판", default="인소싱", help="인소싱(기본) · 아웃소싱 · 밸류업 · 모두 · 쉼표로 여럿")
        p.add_argument("--쪽상한", type=int, default=기본쪽상한)
        p.add_argument("--간격", type=float, default=기본간격, help="요청 사이 초(기본 1.5)")
        p.add_argument("--재시도", type=int, default=기본재시도)
        p.add_argument("--조회일")
        if 이름 == "목록":
            p.add_argument("--html", help="받아 둔 목록 쪽(네트워크 0)")
            p.add_argument("-o", "--출력")
        else:
            p.add_argument("--최근", type=int, default=1)
            p.add_argument("--raw")
            p.add_argument("--글없이", action="store_true", help="PDF 만 받고 글은 뽑지 않는다")
    a = ap.parse_args(argv)
    try:
        if a.명령 == "목록":
            if a.html:
                g = 게시판고르기(a.게시판)[0]
                r = 목록읽기(io.open(a.html, encoding="utf-8").read(), g)
                판 = {"형식": 형식, "발행기관": 발행기관, "종목": a.종목, "평가기준일": a.기준일, "쓰는법": 쓰는법, "게시판": [{"게시판": g, "전체": r["전체"]}],
                     "목록": 기준일가르기([x for x in r["줄"] if not a.종목 or x.get("종목코드") in (None, a.종목)], a.기준일), "오류": [], "멈춤": None, "호출": 0}
            else:
                if not a.종목:
                    raise ValueError("--종목 또는 --html 이 필요하다")
                판 = 목록(a.종목, a.기준일, 게시판고르기(a.게시판), a.쪽상한, a.간격, a.재시도, a.조회일)
            글 = json.dumps(판, ensure_ascii=False, indent=1)
            if a.출력:
                _쓰기(a.출력, 판)
                print(_요약(판) if 판.get("종목") else "KIRS 목록 %d건 → %s" % (len(판["목록"]), a.출력))
            else:
                print(글)
            return 발견 if (판["멈춤"] or not 판["목록"]) else 통과
        if a.명령 == "받기":
            if not a.종목:
                raise ValueError("--종목 이 필요하다")
            판 = 받기(a.종목, a.기준일, a.raw, a.최근, 게시판고르기(a.게시판), a.쪽상한, a.간격, a.재시도, a.조회일, not a.글없이)
            print(_요약(판))
            for x in 판["받음"]:
                print("  %s %s · %s · %s%s" % (x["식별자"], x["발행일"], x["파일"], x.get("글판정"), " · 캐시" if x["캐시"] else ""))
            for x in 판["오류"]:
                print("  ※ %s" % x)
            return 발견 if (판["멈춤"] or not 판["받음"]) else 통과
    except ValueError as e:
        print("입력 오류 — %s" % e)
        return 입력오류
    ap.print_help()
    return 입력오류


if __name__ == "__main__":
    sys.exit(main())

# -*- coding: utf-8 -*-
"""수시공시 — 국내 주요사항보고(B) · 거래소 공시(I) · 발행공시(C)를 받아 투자 결정 · 자금 사용을 `_raw/수시공시.json` 으로 (2026-10-25 FX-C).

왜 만들었나 — 설계 `연구/F도구수리_20261025/설계.md` 뿌리 R5(32곳)
  `dart_fetch` 의 제출이력은 정기공시(A)뿐이다. 그래서 신규시설투자등 · 유형자산 취득 / 처분 결정 · 타법인주식 취득 · 증자 · 사채의 「자금의 사용목적 —
  시설자금」 · 정기보고서의 「공모자금 사용실적」 · **상장 종속회사의 같은 공시** · 정정(총액 증액 · 완공 연기 — 지연 신호)이 하나도 안 들어왔다.
  유니버스 F 물결의 프로젝트는 거의 전부 회사마다 손으로 연 수시공시였다(한 회사 11건 · 6 · 9 · 4 … — 결함 F9 · F15 · F16 · F25).
  수주 공시(시공사 선정 · 우선협상 · 단일판매 · 공급계약)를 투자로 올리던 결함(R3 — 「VAT」 프로젝트)도 여기서 가른다.

범위(설계 J7 — 2026-10-25 총괄 기본값) — 기준일 앞 5년부터 조회일까지 · 본사와 **상장 종속회사**(정기보고서 「연결대상 종속회사 현황」 이름을
  상장 명부(corpCode)에 대 본다) · 비상장 종속은 본사 공시의 「(종속회사의 주요경영사항)」 제목으로만 들어온다. 기준일 뒤 공시는 버리지 않고 `기준일뒤`.
날짜 둘(2026-10-25) — 수시공시는 정보 경계 도구라 `--기준일` 은 **평가기준일 T** 다(`dart_fetch.py --수시공시` 가 T 를 넘긴다 · T 가 없으면 재무기준일 F = T ·
  옛 동작 그대로). 받기 창은 T 앞 5년 ~ 조회일 · 짓기는 공시일 > T 면 `기준일뒤`(값에 넣지 않는다 · 정정도 T 까지만 현재 값). `짓기 --재무기준일 F` 를 주면
  공시일이 (F, T] 인 결정 · 자금사용 · 정정에 `기준일사이: true`(쓴다 — 첫 예측 열 추정의 근거 · 투자 계획은 T 에 알려진 것)와 산출 머리 `재무기준일`.

명령
  python 스크립트/수시공시.py 받기 --회사 <고유번호> --기준일 2026-06-30 [--해수 5] [--종속없이] [--원문상한 40]   # OpenDART — 목록 · 원문
  python 스크립트/수시공시.py 짓기 --기준일 2026-06-30 [--raw _raw] [--조회일 YYYY-MM-DD]                          # 네트워크 0 — 받아 둔 것으로

받은 것: `_raw/dart_수시공시목록.json`(list.json 응답 묶음 — 원천) · `_raw/수시공시원문/<접수번호>.xml|txt`(원문 — 원천) · 낸 것: `_raw/수시공시.json`
  (계약 「수시공시/1」 — 투자능력(FX-B)이 읽는다). 일일 한도 응답(status 020)이 오면 그 자리에서 멈추고 남은 받기를 `_raw/수시공시_남은받기.json` 에 적는다.
금액은 원 단위 · 통화는 원문 그대로(환산하지 않는다). 회사 · 업종 이름은 이 도구에 없다(범용). 키는 환경변수에서만 읽고 찍지 않는다.
종료 코드 — 0 통과 · 1 발견(한도 초과로 멈춤 · 목록 없음) · 2 입력오류.
"""
from __future__ import annotations

import argparse
import datetime
import glob
import io
import json
import os
import re
import sys
from html.parser import HTMLParser

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:                                    # noqa: BLE001
    pass

여기 = os.path.dirname(os.path.abspath(__file__))
if 여기 not in sys.path:
    sys.path.insert(0, 여기)
from 종료코드 import 통과, 발견, 입력오류  # noqa: E402

형식 = "수시공시/1"
목록파일 = "dart_수시공시목록.json"
원문폴더 = "수시공시원문"
출력파일 = "수시공시.json"
남은파일 = "수시공시_남은받기.json"
기본해수 = 5


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
    """「2023-10-31」 · 「2023.10.31」 · 「2023년 10월 31일」 · 「20231031」 → ISO | None."""
    s = (s or "").strip()
    m = re.search(r"(20\d\d|19\d\d)\s*[.\-/년]\s*(\d{1,2})\s*[.\-/월]\s*(\d{1,2})", s) or re.fullmatch(r"(20\d\d)(\d\d)(\d\d)", s)
    if not m:
        return None
    try:
        return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3))).isoformat()
    except ValueError:
        return None


def 수(s):
    s = (s or "").replace(",", "").replace(" ", "").strip()
    if s in ("", "-", "--", "—", "해당사항없음"):
        return None
    음 = s.startswith("(") and s.endswith(")") or s.startswith("△") or s.startswith("-")
    s = s.strip("()△-")
    try:
        v = float(s)
    except ValueError:
        return None
    return -v if 음 else v


# ══════════════════════════════════════════════════════════ 종류 가르기 (R3 · R5)

_제목꼴 = [
    ("신규시설투자", r"신규시설투자"),
    ("유형자산취득", r"유형자산(?:의)?(?:취득|양수)"),
    ("유형자산처분", r"유형자산(?:의)?(?:처분|양도)"),
    ("타법인주식취득", r"(?:타법인주식및출자증권|출자증권)(?:의)?(?:취득|양수)"),
    ("타법인주식처분", r"(?:타법인주식및출자증권|출자증권)(?:의)?(?:처분|양도)"),
    ("수주", r"수주|시공사선정|우선협상|낙찰"),
    ("공급계약", r"단일판매|공급계약"),
    ("증자", r"유상증자|증권신고서\(지분증권\)|투자설명서|증권발행실적보고서"),
    ("사채", r"전환사채|신주인수권부사채|교환사채|사채권발행|증권신고서\(채무증권\)|조건부자본증권"),
    ("기타", r"투자판단관련주요경영사항|기타경영사항|장래사업|경영계획"),
]
_수주본문 = re.compile(r"시공사\s*(?:로\s*)?선정|수주|공사\s*도급|도급\s*계약|공급\s*계약|낙찰|우선\s*협상|판매\s*계약")
_법인본문 = re.compile(r"(?:신규|현지|해외)?\s*법인\s*(?:설립|신설)|자회사\s*설립|(?:지분|주식)\s*(?:취득|인수|출자)")
_공장본문 = re.compile(r"공장\s*(?:신축|증설|건설|건축)|생산\s*라인\s*(?:증설|신설|구축)|설비\s*(?:투자|증설|구축)")
_시설본문 = re.compile(r"(?:신규|증설|시설|공장|라인|설비|생산\s*능력|캐파|CAPA).{0,40}투자|투자.{0,40}(?:공장|시설|설비|라인|증설|생산\s*능력)")
# 협약 · 의향서 — 「실증 협력의향서(LOI) 체결」 처럼 시설 낱말이 보여도 투자 결정이 아니다(R15 · 2026-10-25). 공장 신축 · 증설 문장이 함께면 시설투자로 둔다
_협약본문 = re.compile(r"협력\s*의향|의향서|\bLOI\b|\bMOU\b|양해\s*각서|업무\s*협약|협약\s*(?:을\s*)?체결|공동\s*개발\s*계약|파트너십")


def 제목정리(제목):
    t = re.sub(r"\s+", "", 제목 or "")
    return re.sub(r"^(?:\[[^\]]*\])+", "", t)


def 정정인가(제목):
    return bool(re.match(r"^\s*\[(?:기재정정|정정|첨부정정)\]", 제목 or ""))


def 종류가르기(제목, 본문=None):
    """→ (종류 | None, 근거 「제목|본문」). None = 이 도구가 다루지 않는 공시(잠정실적 · IR · 주총 · 채무보증 …).
    「투자판단 관련 주요경영사항」 · 「기타경영사항」은 본문으로 가른다 — 수주 문장이면 수주, 시설 투자 문장이면 신규시설투자."""
    t = 제목정리(제목)
    if re.search(r"해지|취소|철회", t) and re.search(r"공급계약|단일판매|수주", t):
        return "기타", "제목"
    for 종류, 꼴 in _제목꼴:
        if re.search(꼴, t):
            if 종류 == "기타" and 본문:
                if _수주본문.search(본문):
                    return "수주", "본문"
                if _법인본문.search(본문) and not _공장본문.search(본문):
                    return "타법인주식취득", "본문"                   # 해외 법인 · 자회사 설립 — 지분 출자(CAPEX 아님)
                if _협약본문.search(본문) and not _공장본문.search(본문):
                    return "기타", "본문"                            # 협약 · 의향서 — 투자 결정이 아니다
                if _시설본문.search(본문):
                    return "신규시설투자", "본문"
            return 종류, "제목"
    return None, "제목"


_우선 = {"신규시설투자": 1, "유형자산취득": 2, "유형자산처분": 2, "기타": 3, "증자": 4, "사채": 4, "타법인주식취득": 6, "타법인주식처분": 6}
# 원문 받기 상한(설정) — 회사(주체)마다 전체 상한과 종류별 상한. 시설투자 · 유형자산 취득 · 처분은 상한 없음(먼저 다 받는다), 「기타」(본문으로
# 시설투자를 가를 공시)가 다음, 자금사용(증자 · 사채)이 그다음, 지분 공시(CAPEX 아님)는 마지막(R16 · 2026-10-25 — 회사당 40 상한으로
# 21곳 원문 940편이 밀렸고 그 940편은 시설투자가 아니라 기타 · 증자 · 사채 · 지분이었다)
원문상한기본 = 120
종류상한기본 = {"신규시설투자": None, "유형자산취득": None, "유형자산처분": None, "기타": 120, "증자": 40, "사채": 30,
           "타법인주식취득": 30, "타법인주식처분": 30}


def 종류상한읽기(글):
    """「기타=60,증자=20」 → 종류상한기본에 덮은 dict(값 「없음」 · 0 은 상한 없음)."""
    d = dict(종류상한기본)
    for 칸 in [x.strip() for x in (글 or "").split(",") if x.strip()]:
        k, _, v = 칸.partition("=")
        k, v = k.strip(), v.strip()
        if k not in d:
            raise ValueError("종류상한 — 모르는 종류 %r(%s)" % (k, " · ".join(d)))
        d[k] = None if v in ("", "없음", "0") else int(v)
    return d


def 결정이름(줄):
    """결정 한 줄의 이름 — 본문의 투자대상 · 시설명 → 목적(짧게) → 「<주체> <종류> <공시일>」. 공시 제목(「기타경영사항(자율공시)」 류)은 이름이
    아니다(유니버스 교차가 회사 사이 같은 제목을 같은 시설로 잡았다 — R15)."""
    for k in ("대상", "목적"):
        v = re.sub(r"\s+", " ", "%s" % (줄.get(k) or "")).strip()
        if v and not re.search(r"자율공시|공정공시|주요경영사항|주요사항보고|^\[", v):
            return v[:80]
    return "%s %s %s" % (줄.get("주체이름") or "", 줄.get("종류") or "", 줄.get("공시일") or "")


def 원문필요(종류, 제목):
    """본문을 받아 읽을 공시인가 — 수주 · 공급계약은 제목으로 족하다(투자가 아니다). 증권신고서 본문은 크다 — 증자 결정의 자금조달 목적이 먼저."""
    if 종류 not in _우선:
        return False
    if 종류 in ("증자", "사채") and re.search(r"투자설명서|발행실적", 제목정리(제목)):
        return False
    return True


# ══════════════════════════════════════════════════════════ 원문 표 → 칸 (TD · TH · TE · TU — DART 의 HTML 양식과 DSD XML 둘 다)

class _격자모음(HTMLParser):
    칸태그 = ("td", "th", "te", "tu")

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.줄들, self._줄, self._칸 = [], None, None

    def handle_starttag(self, tag, attrs):
        t = tag.lower()
        if t == "tr":
            self._줄 = []
        elif t in self.칸태그 and self._줄 is not None:
            a = {k.lower(): (v or "") for k, v in attrs}
            try:
                rs, cs = int(a.get("rowspan") or 1), int(a.get("colspan") or 1)
            except ValueError:
                rs, cs = 1, 1
            self._칸 = {"글": [], "rs": max(1, rs), "cs": max(1, cs), "acode": a.get("acode") or a.get("aunit") or ""}
        elif t == "br" and self._칸 is not None:
            self._칸["글"].append(" ")

    def handle_endtag(self, tag):
        t = tag.lower()
        if t in self.칸태그 and self._칸 is not None and self._줄 is not None:
            self._칸["글"] = re.sub(r"\s+", " ", "".join(self._칸["글"])).strip()
            self._줄.append(self._칸)
            self._칸 = None
        elif t == "tr" and self._줄 is not None:
            self.줄들.append(self._줄)
            self._줄 = None

    def handle_data(self, d):
        if self._칸 is not None:
            self._칸["글"].append(d)


def 격자(표html):
    """표 하나 → 펼친 격자(줄마다 칸 사전 목록 — ROWSPAN · COLSPAN 은 같은 사전을 여러 자리에 둔다)."""
    p = _격자모음()
    try:
        p.feed(표html)
    except Exception:                                # noqa: BLE001
        return []
    격, 남 = [], {}                                   # 남: (줄, 열) → 칸(위 줄의 rowspan)
    for i, 줄 in enumerate(p.줄들):
        행, j = [], 0
        큐 = list(줄)
        while 큐 or (i, j) in 남:
            if (i, j) in 남:
                행.append(남.pop((i, j)))
                j += 1
                continue
            c = 큐.pop(0)
            for dj in range(c["cs"]):
                행.append(c)
                for di in range(1, c["rs"]):
                    남[(i + di, j + dj)] = c
            j += c["cs"]
        격.append(행)
    return 격


def 표들(html):
    """원문 → [(시작 자리, 격자)] — 표는 `<TABLE>` 단위(DART 원문은 겹친 표가 없다)."""
    return [(m.start(), 격자(m.group(0))) for m in re.finditer(r"(?is)<table\b.*?</table>", html or "")]


def 칸값들(격):
    """격자 → [(라벨 경로, 값, acode)] — 줄의 마지막 칸이 값, 앞 칸들이 라벨(같은 칸이 펼쳐져 겹친 것은 한 번)."""
    낸 = []
    for 행 in 격:
        고유 = []
        for c in 행:
            if not 고유 or 고유[-1] is not c:
                고유.append(c)
        if len(고유) < 2:
            continue
        값 = 고유[-1]
        라벨 = [re.sub(r"\s+", " ", c["글"]).strip() for c in 고유[:-1] if c["글"].strip()]
        if not 라벨:
            continue
        낸.append((" > ".join(라벨), 값["글"], 값["acode"]))
    return 낸


def 원문읽기(raw, 접수):
    """접수번호 → (html, txt) — `_raw/수시공시원문/` 먼저, 없으면 `_raw/F_공시/` · `_raw` 아래 아무 곳(이름이 접수번호로 시작하는 .xml · .html)."""
    후 = []
    for d in (os.path.join(raw, 원문폴더), os.path.join(raw, "F_공시"), raw):
        후 += glob.glob(os.path.join(d, "%s*.xml" % 접수)) + glob.glob(os.path.join(d, "%s*.htm*" % 접수))
    if not 후:
        후 = [p for p in glob.glob(os.path.join(raw, "**", "%s*.xml" % 접수), recursive=True)]
    for p in 후:
        b = open(p, "rb").read()
        for 인코딩 in ("utf-8", "cp949", "euc-kr"):
            try:
                h = b.decode(인코딩)
                break
            except UnicodeDecodeError:
                h = None
        if h:
            return h, p
    return None, None


def _글(html):
    h = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", html or "")
    h = re.sub(r"(?i)<br\s*/?>|</(p|div|tr|table|td|th|te|tu)>", "\n", h)
    h = re.sub(r"(?s)<[^>]+>", " ", h)
    for a, b in (("&nbsp;", " "), ("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"), ("&quot;", '"'), ("&#39;", "'")):
        h = h.replace(a, b)
    return re.sub(r"[ \t]+", " ", h)


# ══════════════════════════════════════════════════════════ 결정 · 정정 · 자금사용 읽기

_금액라벨 = {
    "신규시설투자": r"투자금액",
    "유형자산취득": r"취득금액|양수금액|취득가액",
    "유형자산처분": r"처분금액|양도금액|처분가액",
    "타법인주식취득": r"취득금액|취득가액|양수금액",
    "타법인주식처분": r"처분금액|양도금액|처분가액",
    "공급계약": r"확정계약금액|계약금액",
    "수주": r"계약금액|수주금액",
    "기타": r"투자금액|투자총액|총투자|금액",
}


def _찾기(kv, 꼴, 제외=None):
    for 경로, 값, _ in kv:
        if re.search(꼴, 경로) and not (제외 and re.search(제외, 경로)):
            return 경로, 값
    return None, None


def _통화(경로, 값):
    t = "%s %s" % (경로 or "", 값 or "")
    for 코드, 꼴 in (("USD", r"USD|미화|달러|US\$|\$"), ("EUR", r"EUR|유로"), ("JPY", r"JPY|엔화"), ("CNY", r"CNY|위안")):
        if re.search(꼴, t):
            return 코드
    return "KRW"


def 투자범위(*글들):
    t = " ".join(g or "" for g in 글들)
    t = re.sub(r"[가-힣A-Za-z ,·및]{0,24}(?:를|을)\s*제외(?:한|하고|하며)?", " ", t)      # 「토지, 장비를 제외한 건물」 — 뺀 것은 범위가 아니다
    건 = re.search(r"토지|건물|부지|건축|신축|사옥|건설공사", t)
    장 = re.search(r"기계|장비|설비|라인|생산시설|시설증설|증설|양산", t)
    if 건 and 장:
        return "전체"
    if 건:
        return "건물"
    if 장:
        return "장비"
    return "모름"


def _정정표인가(격):
    """정정 공시의 머리 표(정정관련 공시서류 · 정정항목 / 정정전 / 정정후) — 결정 칸을 읽을 때는 뺀다(정정 전 글이 라벨로 섞인다)."""
    글 = "".join(c["글"] for 행 in 격 for c in 행).replace(" ", "")
    return ("정정전" in 글 and "정정후" in 글) or "정정관련공시서류" in 글 or "정정일자" in 글


def 결정읽기(html, 종류):
    """수시공시 본문 → {금액 · 자기자본대비 · 기간 · 목적 · 대상 · 투자범위 · 주체이름 · 이사회결의일} (못 읽은 칸은 None)."""
    kv = [x for _, 격 in 표들(html) if not _정정표인가(격) for x in 칸값들(격)]
    글 = _글(html)
    낸 = {"금액": None, "자기자본대비": None, "기간": {"시작": None, "끝": None}, "목적": None, "대상": None, "투자범위": "모름",
          "주체이름": None, "이사회결의일": None}
    경, 값 = _찾기(kv, _금액라벨.get(종류, r"금액"), 제외=r"자기자본|자산총액|매출액|최근|대비")
    v = 수(값)
    if v is not None:
        낸["금액"] = {"값": v, "통화": _통화(경, 값)}
    for 꼴 in (r"자기자본대비", r"자산총액대비", r"매출액대비"):
        _, 값 = _찾기(kv, 꼴)
        if 수(값) is not None:
            낸["자기자본대비"] = round(수(값) / 100.0, 6)
            break
    _, s = _찾기(kv, r"(?:투자|계약|사업)?기간.*시작|시작일")
    _, e = _찾기(kv, r"(?:투자|계약|사업)?기간.*종료|종료일")
    if not e:
        _, e = _찾기(kv, r"(?:취득|처분|양수|양도)예정일자|예정일자")
    낸["기간"] = {"시작": 날짜(s), "끝": 날짜(e)}
    _, 낸["목적"] = _찾기(kv, r"(?:투자|취득|처분|양수|양도|출자)\s*목적|계약\s*내용|체결계약명|주요\s*내용|^\d+\.\s*제목")
    _, 대상 = _찾기(kv, r"투자대상|자산명|물건명|회사명|계약상대|거래상대|^\d+\.\s*대상")
    낸["대상"] = 대상
    _, 구분 = _찾기(kv, r"투자구분|자산구분|물건\s*구분")
    낸["투자범위"] = 투자범위(구분, 대상, 낸["목적"]) if 종류 in ("신규시설투자", "유형자산취득", "유형자산처분", "기타") else "모름"
    _, 결의 = _찾기(kv, r"이사회\s*결의일")
    낸["이사회결의일"] = 날짜(결의)
    m = re.search(r"종속회사인\s*(.{1,80}?)\s*의\s*주요\s*경영사항", 글)
    if m:
        낸["주체이름"] = re.sub(r"\s+", " ", m.group(1)).strip()
    for k in ("목적", "대상"):
        if 낸[k]:
            낸[k] = re.sub(r"\s+", " ", 낸[k]).strip()[:200]
    return 낸


def 정정읽기(html):
    """정정 공시 → {"원공시일", "정정사유", "바뀐": [(항목, 전, 후)]} | None(정정 표가 없으면)."""
    판들 = 표들(html)
    kv = [x for _, 격 in 판들 for x in 칸값들(격)]
    _, 원 = _찾기(kv, r"정정관련\s*공시서류\s*제출일")
    _, 사유 = _찾기(kv, r"정정사유")
    바뀐 = []
    for _, 격 in 판들:
        머 = None
        for i, 행 in enumerate(격):
            글들 = [c["글"] for c in 행]
            if any("정정전" in g.replace(" ", "") for g in 글들) and any("정정후" in g.replace(" ", "") for g in 글들):
                머 = i
                break
        if 머 is None:
            continue
        for 행 in 격[머 + 1:]:
            고유 = []
            for c in 행:
                if not 고유 or 고유[-1] is not c:
                    고유.append(c)
            if len(고유) >= 3:
                바뀐.append((고유[0]["글"], 고유[-2]["글"], 고유[-1]["글"]))
    if not (원 or 바뀐):
        return None
    return {"원공시일": 날짜(원), "정정사유": (사유 or "").strip()[:200] or None, "바뀐": 바뀐}


def 바뀐칸(바뀐):
    """정정 표 줄 → 계약의 `바뀐칸` — 금액 · 기간.끝 · 기간.시작은 이름을 맞추고, 나머지는 항목 이름 그대로(앞 80자)."""
    낸 = {}
    for 항, 전, 후 in 바뀐:
        h = re.sub(r"\s+", "", 항)
        if re.search(r"금액|가액", h) and not re.search(r"대비|자기자본|자산총액|매출액", h) and 수(전) is not None and 수(후) is not None:
            낸["금액"] = [수(전), 수(후)]
        elif re.search(r"종료|예정일|완료|끝", h) and (날짜(전) or 날짜(후)):
            낸["기간.끝"] = [날짜(전), 날짜(후)]
        elif re.search(r"시작", h) and (날짜(전) or 날짜(후)):
            낸["기간.시작"] = [날짜(전), 날짜(후)]
        else:
            낸[항.strip()[:80]] = [(전 or "").strip()[:80], (후 or "").strip()[:80]]
    return 낸


_목적이름 = [("시설자금", r"시설"), ("채무상환", r"채무상환"), ("타법인증권취득", r"타법인|증권\s*취득"), ("운영자금", r"운영"), ("기타", r"영업양수|기타")]


def _목적(라벨):
    for 이름, 꼴 in _목적이름:
        if re.search(꼴, 라벨 or ""):
            return 이름
    return "기타"


def 자금사용_결정(html):
    """유상증자 · 사채 발행 결정(주요사항보고서) → [{목적 · 세부 · 금액 · 통화}] — 「자금조달의 목적 > 시설자금 (원)」 줄."""
    낸 = []
    for 경로, 값, _ in (x for _, 격 in 표들(html) for x in 칸값들(격)):
        if not re.search(r"자금조달의\s*목적|자금의\s*사용\s*목적", 경로):
            continue
        끝라벨 = 경로.split(" > ")[-1]
        v = 수(값)
        if v is None or not re.search(r"자금", 끝라벨):
            continue
        낸.append({"목적": _목적(끝라벨), "세부": 끝라벨, "금액": v, "통화": _통화(끝라벨, 값), "시기": None, "집행": None, "전용": None})
    return 낸


def 자금사용_신고서(html):
    """증권신고서 · 투자설명서 「자금의 사용목적」 가로 표(시설자금 · 운영자금 … 열) → 항목들."""
    for _, 격 in 표들(html):
        for i, 행 in enumerate(격[:-1]):
            글들 = [c["글"].replace(" ", "") for c in 행]
            if sum(1 for g in 글들 if re.search(r"시설자금|운영자금|채무상환자금|타법인증권취득자금", g)) < 2:
                continue
            for 다음 in 격[i + 1:i + 3]:
                수들 = [(행[j]["글"], 수(c["글"])) for j, c in enumerate(다음) if j < len(행)]
                낸 = [{"목적": _목적(라), "세부": 라, "금액": v, "통화": "KRW", "시기": None, "집행": None, "전용": None}
                     for 라, v in 수들 if v and re.search(r"자금|기타", 라) and not re.search(r"합계|계$", 라.replace(" ", ""))]
                if 낸:
                    return 낸
    return []


def 자금사용_정기(html):
    """정기보고서 「공모 · 사모자금의 사용내역」(DSD 표 — ACODE PLA_USE · PLA_AMT · BRK_CON · BRK_AMT · 차이 사유) → 항목들 + 단위.
    ACODE 가 없으면 머리 이름(사용용도 · 조달금액 · 사용내용 · 사용금액)으로."""
    낸 = []
    for m in re.finditer(r"(공모|사모)자금의\s*사용\s*내역", html or ""):
        뒤 = html[m.end():m.end() + 60000]
        단 = re.search(r"\(\s*단위\s*:\s*(백만원|천원|원|억원)", _글(뒤[:4000]))
        배 = {"백만원": 1e6, "천원": 1e3, "원": 1.0, "억원": 1e8}.get(단.group(1) if 단 else "", 1.0)
        for _, 격 in 표들(뒤)[:3]:
            줄 = [행 for 행 in 격 if any(c.get("acode") in ("PLA_USE", "PLA_AMT", "BRK_AMT") for c in 행)]
            if not 줄:
                continue
            for 행 in 줄:
                a = {c["acode"]: c["글"] for c in 행 if c.get("acode")}
                계획, 금 = a.get("PLA_USE"), 수(a.get("PLA_AMT"))
                if not 계획 and 금 is None:
                    continue
                실, 집 = a.get("BRK_CON"), 수(a.get("BRK_AMT"))
                사유 = " · ".join(x for x in (a.get("PS_USE_PL"), a.get("PS_MNY_PL")) if x and x.strip() not in ("-", ""))
                전용 = None
                if 실 and 계획 and _목적(실) != _목적(계획):
                    전용 = "%s → %s" % (계획.strip(), 실.strip())
                낸.append({"목적": _목적(계획), "세부": "%s(%s)" % ((계획 or "").strip(), m.group(1) + "자금"), "금액": 금 * 배 if 금 is not None else None,
                          "통화": "KRW", "시기": 날짜(a.get("PYM_DT") or "") or None, "집행": 집 * 배 if 집 is not None else None,
                          "전용": 전용 or (사유 or None)})
            break
    return 낸


# ══════════════════════════════════════════════════════════ 목록 · 상장 종속

def 목록읽기(raw):
    """`_raw/dart_수시공시목록.json`(이 도구) → [{"고유번호", "이름", "주체", "목록": [list.json 항목]}].
    없으면 F 물결이 손으로 받아 둔 목록(list.json 항목 꼴의 JSON — `_raw` · `_raw/F_공시`)을 줍는다 — 본사 고유번호(기업개황)가 아니면 상장종속."""
    j = _읽기(os.path.join(raw, 목록파일))
    if isinstance(j, dict) and j.get("회사"):
        return j["회사"], j
    본 = (_읽기(os.path.join(raw, "dart_기업개황.json")) or {}).get("corp_code")
    모 = {}
    for p in glob.glob(os.path.join(raw, "*.json")) + glob.glob(os.path.join(raw, "F_공시", "*.json")):
        x = _읽기(p)
        항목 = x if isinstance(x, list) else (x.get("list") if isinstance(x, dict) else None)
        if not (isinstance(항목, list) and 항목 and isinstance(항목[0], dict) and "rcept_no" in 항목[0] and "report_nm" in 항목[0]):
            continue
        for it in 항목:
            if re.search(r"(사업|반기|분기)보고서", it.get("report_nm") or "") and not 정정인가(it.get("report_nm")):
                continue
            c = it.get("corp_code") or 본
            d = 모.setdefault(c, {"고유번호": c, "이름": it.get("corp_name"), "주체": "본사" if (c == 본 or not 본) else "상장종속", "목록": {}})
            d["목록"][it["rcept_no"]] = it
    회사 = [dict(d, 목록=sorted(d["목록"].values(), key=lambda z: z["rcept_no"])) for d in 모.values()]
    return 회사, {"형식": "수시공시목록 1", "출처": "F 물결 손 목록(대체)"}


def _이름정리(s):
    s = re.sub(r"\(주\)|㈜|주식회사|\(유\)|유한회사|\s+|,|\.", "", s or "")
    return s.lower()


def 상장명부(캐시들=None):
    """corpCode.xml → {정리한 이름: (고유번호, 종목코드, 이름)} — 상장(종목코드 있음)만. 캐시를 찾는 차례: 공용 원천 · 키트 `_dartcache`."""
    import xml.etree.ElementTree as ET                      # noqa: PLC0415
    후 = list(캐시들 or [])
    공용 = os.environ.get("DCF_공용캐시") or os.environ.get("DCF_SHARED_CACHE") or os.path.join(os.path.expanduser("~"), ".dcf캐시")
    후 += [os.path.join(공용, "원천", "_dartcache", "corpCode.xml"), os.path.join(os.path.dirname(여기), "_dartcache", "corpCode.xml")]
    for p in 후:
        if p and os.path.exists(p):
            표 = {}
            for e in ET.parse(p).getroot().iter("list"):
                s = (e.findtext("stock_code") or "").strip()
                if s:
                    n = (e.findtext("corp_name") or "").strip()
                    표[_이름정리(n)] = ((e.findtext("corp_code") or "").strip(), s, n)
            return 표
    return None


def 연결종속이름들(raw):
    """가장 최근 정기보고서(사업 → 반기) 원문의 「연결대상 종속회사 현황(상세)」 표 구간 → (줄 목록, 파일).
    머리(「상호」 · 「회사명」)가 300자 안에 있는 구간만 — 회사 개요의 요약 문단(신용평가 · 주관사 이름이 섞인다)은 쓰지 않는다."""
    후 = sorted(glob.glob(os.path.join(raw, "사업20*", "*.txt")), reverse=True) + sorted(glob.glob(os.path.join(raw, "반기", "*.txt")), reverse=True)
    for p in 후:
        t = io.open(p, encoding="utf-8", errors="ignore").read()
        줄들 = []
        for m in re.finditer(r"연결대상\s*종속회사\s*(?:현황|개황)\s*\((?:상세|요약)\)", t):
            앞 = t[m.end():m.end() + 300]
            if not re.search(r"상\s*호|회\s*사\s*명|법\s*인\s*명", 앞):
                continue
            끝 = re.search(r"\n\s*주\s*\d?\s*\)|계열회사\s*현황|타법인출자\s*현황|나\.\s*연결대상회사의\s*변동", t[m.end():])
            조각 = t[m.end():m.end() + (끝.start() if 끝 else 15000)][:30000]
            줄들 += [x.strip() for x in 조각.split("\n") if x.strip()]
        if 줄들:
            return 줄들, p
    return [], None


def 상장종속찾기(raw, 명부, 본사고유=None):
    """→ [{"고유번호", "종목코드", "이름"}] — 연결대상 종속회사 표의 **한 칸(줄) 전체가** 상장 회사 이름과 같은 것(본사 제외).
    부분 문자열로 대지 않는다(「하이브리드」 속 「하이브」 같은 오탐)."""
    줄들, _ = 연결종속이름들(raw)
    if not 줄들 or not 명부:
        return []
    본사이름 = _이름정리((_읽기(os.path.join(raw, "dart_기업개황.json")) or {}).get("corp_name"))
    낸, 본 = [], set()
    for 줄 in 줄들:
        k = _이름정리(줄)
        if len(k) < 2 or k == 본사이름 or k not in 명부:
            continue
        고유, 종목, 이름 = 명부[k]
        if 고유 == 본사고유 or 고유 in 본:
            continue
        낸.append({"고유번호": 고유, "종목코드": 종목, "이름": 이름})
        본.add(고유)
    return 낸


# ══════════════════════════════════════════════════════════ 짓기 (네트워크 0)

def 짓기(raw, 기준일, 조회일=None, 재무기준일=None):
    """`기준일` = 평가기준일 T(정보 경계 — 공시일 > T 면 `기준일뒤` · 값에 넣지 않는다). `재무기준일` F(2026-10-25 날짜 둘)를 주고 T 보다 이르면
    공시일이 (F, T] 인 결정 · 자금사용 · 정정에 `기준일사이: true`(쓴다 — 첫 예측 열 추정 · 이월 다리 자본거래의 근거)와 산출 머리에 `재무기준일`.
    F 가 없으면 산출이 지금과 같다."""
    낸 = _짓기(raw, 기준일, 조회일)
    재 = (재무기준일 or "")[:10]
    if 재 and 재 < (기준일 or "")[:10]:
        낸["재무기준일"] = 재

        def 사이(z):
            일 = z.get("공시일")
            return bool(일 and 재 < 일 <= 기준일)
        for z in 낸["결정"] + 낸["자금사용"]:
            z["기준일사이"] = 사이(z)
            for 정 in z.get("정정") or []:
                정["기준일사이"] = 사이(정)
    return 낸


def _짓기(raw, 기준일, 조회일=None):
    회사들, 목록원 = 목록읽기(raw)
    if not 회사들:
        raise ValueError("수시공시 목록이 없다 — `수시공시.py 받기` 로 받는다(`%s`)" % os.path.join(raw, 목록파일))
    개 = _읽기(os.path.join(raw, "dart_기업개황.json")) or {}
    기준 = 기준일
    결정, 자금, 확인불가, 원문읽음, 본문없음 = [], [], [], [], []
    for 회사 in 회사들:
        주체기본 = 회사.get("주체") or "본사"
        묶음 = {}                                            # (종류, 주체, 원공시일 | 접수) → 결정
        정정들 = []
        for it in sorted(회사.get("목록") or [], key=lambda z: z.get("rcept_no") or ""):
            제목 = (it.get("report_nm") or "").strip()
            접수 = it.get("rcept_no")
            공시일 = 날짜(it.get("rcept_dt") or (접수 or "")[:8])
            html, 파일 = 원문읽기(raw, 접수) if 접수 else (None, None)
            본문글 = _글(html) if html else None
            종류, 근거 = 종류가르기(제목, 본문글)
            if not 종류:
                continue
            if 종류 == "기타":
                # 「기타경영사항」은 자율공시가 많다 — 본문이 투자 · 출자 · 취득을 말할 때만, 본문이 없으면 투자판단 · 장래사업 제목만 남긴다
                if html and not re.search(r"투자|시설|공장|증설|설비|취득|출자|생산\s*능력", 본문글 or ""):
                    continue
                if not html and not re.search(r"장래사업|경영계획", 제목정리(제목)):
                    # 본문 없이는 투자 · 수주 · 임상 · 소송을 가를 수 없다 — 결정에 넣지 않고 「본문없음」으로 센다(받기가 본문을 받는다)
                    if re.search(r"투자판단", 제목정리(제목)):
                        본문없음.append({"접수번호": 접수, "공시일": 공시일, "제목": 제목, "주체이름": 회사.get("이름")})
                    continue
            if html:
                원문읽음.append({"접수번호": 접수, "파일": os.path.relpath(파일, raw).replace("\\", "/")})
            주체 = 주체기본
            if 주체기본 == "본사" and "종속회사" in 제목정리(제목):
                주체 = "비상장종속"
            if 종류 in ("증자", "사채"):
                if html:
                    항목 = 자금사용_결정(html) or 자금사용_신고서(html)
                    if 항목:
                        자금.append({"문서": "증권신고서" if re.search(r"증권신고서", 제목) else ("투자설명서" if "투자설명서" in 제목 else "주요사항보고서"),
                                   "접수번호": 접수, "공시일": 공시일, "기준일뒤": bool(공시일 and 공시일 > 기준), "주체": 주체,
                                   "주체이름": 회사.get("이름"), "제목": 제목, "항목": 항목})
                elif 원문필요(종류, 제목):
                    확인불가.append({"항목": "%s 자금사용(%s)" % (제목정리(제목)[:30], 접수), "원인": "원문을 받지 않았다"})
            읽 = 결정읽기(html, 종류) if html else None
            주체이름 = ((읽 or {}).get("주체이름") if 주체 != "본사" else None) or 회사.get("이름")
            줄 = {"종류": 종류, "분류근거": 근거, "주체": 주체, "주체이름": 주체이름, "접수번호": 접수,
                 "공시일": 공시일, "제목": 제목, "대상": (읽 or {}).get("대상"), "금액": (읽 or {}).get("금액"),
                 "자기자본대비": (읽 or {}).get("자기자본대비"), "기간": (읽 or {}).get("기간") or {"시작": None, "끝": None},
                 "목적": (읽 or {}).get("목적"), "투자범위": (읽 or {}).get("투자범위") or "모름", "이사회결의일": (읽 or {}).get("이사회결의일"),
                 "정정": [], "기준일뒤": bool(공시일 and 공시일 > 기준), "출처": "DART 접수 %s" % 접수, "원문": bool(html)}
            줄["이름"] = 결정이름(줄)
            if 정정인가(제목):
                정 = 정정읽기(html) if html else None
                정정들.append((줄, 정))
                continue
            if not html and 원문필요(종류, 제목) and 종류 not in ("증자", "사채", "타법인주식취득", "타법인주식처분"):
                확인불가.append({"항목": "%s 본문(%s)" % (제목정리(제목)[:30], 접수), "원인": "원문을 받지 않았다 — 금액 · 기간 · 목적 빈칸"})
            묶음[접수] = 줄
            결정.append(줄)
        # 정정 사슬 — 원공시일 · 종류 · 주체가 맞는 원래 공시 아래로. 기준일 뒤 정정은 값에 반영하지 않고 적기만 한다
        for 줄, 정 in 정정들:
            원일 = (정 or {}).get("원공시일")
            머리 = None
            if 원일:
                머리 = next((d for d in 결정 if d["종류"] == 줄["종류"] and d["공시일"] == 원일 and d["주체"] == 줄["주체"]
                           and (d["주체이름"] == 줄["주체이름"] or not 줄["주체이름"] or not d["주체이름"])), None)
            if not 머리:
                머리 = next((d for d in reversed(결정) if d["종류"] == 줄["종류"] and d["주체"] == 줄["주체"] and d["대상"] and d["대상"] == 줄["대상"]), None)
            if not 머리 and not 정:
                # 정정 원문이 없으면 — 같은 제목(정정 꼬리표를 뗀)의 가장 늦은 앞 공시에 붙인다(근사 — 원공시일을 못 읽었다)
                머리 = next((d for d in reversed(결정) if 제목정리(d["제목"]) == 제목정리(줄["제목"]) and d["주체"] == 줄["주체"]
                           and (d["공시일"] or "") <= (줄["공시일"] or "") and d["공시일"] and 줄["공시일"]
                           and (datetime.date.fromisoformat(줄["공시일"]) - datetime.date.fromisoformat(d["공시일"])).days <= 180), None)
                if 머리:
                    줄["근사연결"] = True
            바 = 바뀐칸((정 or {}).get("바뀐") or [])
            기록 = {"접수번호": 줄["접수번호"], "공시일": 줄["공시일"], "바뀐칸": 바, "정정사유": (정 or {}).get("정정사유"), "기준일뒤": 줄["기준일뒤"],
                  "원문": bool(정), "근사연결": bool(줄.get("근사연결"))}
            if not 머리:
                줄["정정"] = [기록]
                줄["원래공시"] = {"공시일": 원일, "찾음": False}
                결정.append(줄)
                continue
            머리["정정"].append(기록)
            if not 줄["기준일뒤"]:                          # 기준일까지의 정정만 현재 값으로
                if 줄["금액"]:
                    머리["금액"] = 줄["금액"]
                elif "금액" in 바 and 바["금액"][1] is not None:
                    머리["금액"] = {"값": 바["금액"][1], "통화": (머리.get("금액") or {}).get("통화", "KRW")}
                if 줄["기간"].get("끝") or "기간.끝" in 바:
                    머리["기간"] = dict(머리["기간"], 끝=줄["기간"].get("끝") or 바["기간.끝"][1])
                for k in ("자기자본대비", "목적", "투자범위"):
                    if 줄.get(k) and 줄[k] != "모름":
                        머리[k] = 줄[k]
                머리["이름"] = 결정이름(머리)
    # 정기보고서 공모 · 사모자금 사용실적(가장 최근 · 기준일까지의 보고서)
    정기 = sorted(glob.glob(os.path.join(raw, "반기", "*.xml")) + glob.glob(os.path.join(raw, "사업20*", "*.xml")),
                key=lambda p: os.path.basename(p), reverse=True)                # 접수번호(이름) 늦은 것 먼저
    for p in 정기[:2]:
        try:
            h = io.open(p, encoding="utf-8", errors="ignore").read()
        except OSError:
            continue
        항목 = 자금사용_정기(h)
        if 항목:
            접 = re.match(r"(\d{14})", os.path.basename(p))
            자금.append({"문서": "정기보고서 공모자금 사용실적", "접수번호": 접.group(1) if 접 else None, "공시일": 날짜(접.group(1)[:8]) if 접 else None,
                       "기준일뒤": False,
                       "주체": "본사", "주체이름": 개.get("corp_name"), "제목": os.path.relpath(p, raw).replace("\\", "/"), "항목": 항목})
            break
    결정.sort(key=lambda d: (d["공시일"] or "", d["접수번호"] or ""))
    # 자금 사용 — 정정본이 같은 항목을 다시 내면 하나만(늦은 공시 · 기준일 앞뒤는 따로)
    묶 = {}
    for z in sorted(자금, key=lambda z: (z.get("공시일") or "", z.get("접수번호") or "")):
        키 = (z["주체"], z["문서"], z["기준일뒤"], tuple((i["목적"], i["금액"]) for i in z["항목"]))
        묶[키] = z
    자금 = list(묶.values())
    if 본문없음:
        확인불가.append({"항목": "본문 없는 「투자판단 관련 주요경영사항」 %d건" % len(본문없음),
                     "원인": "본문 없이는 투자 · 수주 · 그 밖을 가를 수 없다 — `수시공시.py 받기` 가 본문을 받는다(목록은 `본문없음`)"})
    범위 = (목록원 or {}).get("범위") or {}
    return {"형식": 형식, "회사": 개.get("corp_name"), "고유번호": 개.get("corp_code"), "평가기준일": 기준일,
            "조회일": 조회일 or (목록원 or {}).get("조회일") or datetime.date.today().isoformat(),
            "목록범위": {"시작": 범위.get("시작"), "끝": 범위.get("끝"), "종류": 범위.get("종류") or ["B", "I", "C"],
                       "연결범위": sorted({c.get("주체") or "본사" for c in 회사들}), "출처": (목록원 or {}).get("출처") or 목록파일},
            "결정": 결정, "자금사용": 자금, "확인불가": 확인불가, "원문읽음": 원문읽음, "본문없음": 본문없음}


# ══════════════════════════════════════════════════════════ 받기 (OpenDART)

class 한도초과(Exception):
    pass


def _목록받기(DF, 고유, 시작, 끝, 종류, 셈):
    낸, 쪽 = [], 1
    while True:
        j = DF._get("list.json", corp_code=고유, bgn_de=시작, end_de=끝, pblntf_ty=종류, page_no=쪽, page_count=100).json()
        셈["호출"] += 1
        s = (j or {}).get("status")
        if s == "020":
            raise 한도초과("list.json %s %s" % (고유, 종류))
        if s == "013":
            return 낸
        if s not in (None, "000"):
            셈["오류"].append("list.json %s %s status %s" % (고유, 종류, s))
            return 낸
        낸 += j.get("list") or []
        if 쪽 >= int(j.get("total_page") or 1):
            return 낸
        쪽 += 1


def _원문받기(DF, 접수, 낼곳):
    """document.xml 한 건 → `<낼곳>/<접수번호>*.xml|txt`. zip 이 아니면 — 020 은 한도초과, 그 밖은 None(뷰어 우회는 쓰지 않는다:
    뷰어 도구는 키트 본체 `_raw/` 에 접수번호 없는 이름으로 쓴다). → 쓴 파일 목록 | None."""
    import zipfile                                          # noqa: PLC0415
    r = DF._get("document.xml", rcept_no=접수)
    if r.content[:2] != b"PK":
        try:
            st = (json.loads(r.content.decode("utf-8", "ignore")) or {}).get("status")
        except ValueError:
            st = None
        if st == "020":
            raise DF.한도초과("document.xml %s" % 접수)
        return None
    os.makedirs(낼곳, exist_ok=True)
    낸 = []
    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        for k, n in enumerate(z.namelist()):
            바 = z.read(n)
            이름 = os.path.basename(n)
            if not 이름.startswith(접수):
                이름 = "%s_%d_%s" % (접수, k, 이름)
            p = os.path.join(낼곳, 이름)
            with open(p, "wb") as f:
                f.write(바)
            낸.append(p)
            if 이름.lower().endswith((".xml", ".html", ".htm")):
                for 인코딩 in ("utf-8", "cp949", "euc-kr"):
                    try:
                        글 = 바.decode(인코딩)
                        break
                    except UnicodeDecodeError:
                        글 = None
                if 글:
                    io.open(p.rsplit(".", 1)[0] + ".txt", "w", encoding="utf-8").write(DF._태그벗기기(글))
    return 낸


def 받기(고유, 기준일, raw=None, 해수=기본해수, 종속=True, 원문상한=원문상한기본, 조회일=None, 종류상한=None, 목록재사용=False):
    """OpenDART — 목록(B · I · C) 과 고른 원문을 `_raw` 에 받는다. 한도 초과(020)면 멈추고 남은 받기를 적는다 → 요약 dict.
    원문은 종류 차례(시설투자 → 유형자산 → 기타 → 증자 · 사채 → 지분)로 받고, 회사(주체)마다 전체 상한(`원문상한`)과 종류별 상한(`종류상한`)을 둔다.
    `목록재사용` — 같은 기준일의 목록 파일이 이미 있으면 목록을 다시 부르지 않고 원문만 받는다(남은 원문 이어 받기)."""
    import dart_fetch as DF                                 # noqa: PLC0415
    raw = raw or DF.RAW
    if not DF.KEY:
        raise ValueError("OPENDART_API_KEY 가 환경변수에 없다")
    기 = datetime.date.fromisoformat(기준일)
    시작 = 기.replace(year=기.year - 해수).strftime("%Y%m%d")
    끝 = (조회일 or datetime.date.today().isoformat()).replace("-", "")
    셈 = {"호출": 0, "오류": []}
    개 = _읽기(os.path.join(raw, "dart_기업개황.json")) or {}
    회사들 = [{"고유번호": 고유, "이름": 개.get("corp_name"), "주체": "본사"}]
    if 종속:
        명부 = 상장명부()
        if 명부 is None:
            try:
                DF.고유번호표()
                명부 = 상장명부()
            except Exception as e:                         # noqa: BLE001
                셈["오류"].append("상장 명부(corpCode) 못 받음 — %s" % type(e).__name__)
        for s in 상장종속찾기(raw, 명부 or {}, 고유):
            회사들.append({"고유번호": s["고유번호"], "이름": s["이름"], "주체": "상장종속", "종목코드": s["종목코드"]})
    남은 = {"형식": "수시공시 남은받기 1", "고유번호": 고유, "기준일": 기준일, "목록": [], "원문": []}
    멈춤 = None
    옛목록 = _읽기(os.path.join(raw, 목록파일)) if 목록재사용 else None
    if isinstance(옛목록, dict) and 옛목록.get("평가기준일") == 기준일 and 옛목록.get("회사") and not 옛목록.get("한도초과"):
        회사들 = 옛목록["회사"]                                  # 이어 받기 — 목록은 그대로(조회일 · 범위도 옛 판)
    else:
        for c in 회사들:
            c["목록"] = []
            for 종류 in ("B", "I", "C"):
                if 멈춤:
                    남은["목록"].append({"고유번호": c["고유번호"], "종류": 종류})
                    continue
                try:
                    c["목록"] += _목록받기(DF, c["고유번호"], 시작, 끝, 종류, 셈)
                except 한도초과 as e:
                    멈춤 = str(e)
                    남은["목록"].append({"고유번호": c["고유번호"], "종류": 종류})
        판 = {"형식": "수시공시목록 1", "조회일": 끝[:4] + "-" + 끝[4:6] + "-" + 끝[6:], "평가기준일": 기준일,
             "범위": {"시작": "%s-%s-%s" % (시작[:4], 시작[4:6], 시작[6:]), "끝": "%s-%s-%s" % (끝[:4], 끝[4:6], 끝[6:]), "종류": ["B", "I", "C"]},
             "회사": [{k: v for k, v in c.items()} for c in 회사들], "호출": 셈["호출"], "오류": 셈["오류"], "한도초과": 멈춤}
        _쓰기(os.path.join(raw, 목록파일), 판)
    상한표 = dict(종류상한기본, **(종류상한 or {}))
    # 원문 — 종류의 차례(시설 투자 → 유형자산 → 본문으로 가를 것 → 증자 · 사채 → 지분), 같은 차례면 늦은 것 먼저
    받을 = []
    for c in 회사들:
        for it in c.get("목록") or []:
            종류, _ = 종류가르기(it.get("report_nm"))
            if 종류 and 원문필요(종류, it.get("report_nm")) and not 원문읽기(raw, it["rcept_no"])[0]:
                받을.append((_우선.get(종류, 9), -int(re.sub(r"\D", "", it["rcept_no"]) or 0), it["rcept_no"], c["고유번호"], 종류))   # 같은 차례면 늦은 것 먼저
    받을.sort()
    받은 = 0
    셈회, 셈종 = {}, {}
    for _, _, 접수, 고, 종류 in 받을:
        if 멈춤:
            남은["원문"].append(접수)
            continue
        종상 = 상한표.get(종류)
        if (원문상한 and 셈회.get(고, 0) >= 원문상한) or (종상 is not None and 셈종.get((고, 종류), 0) >= 종상):
            남은["원문"].append(접수)
            continue
        try:
            낸 = _원문받기(DF, 접수, os.path.join(raw, 원문폴더))
            셈["호출"] += 1
            셈회[고] = 셈회.get(고, 0) + 1
            셈종[(고, 종류)] = 셈종.get((고, 종류), 0) + 1
            if 낸:
                받은 += 1
            else:
                셈["오류"].append("원문 %s — zip 이 아니다(받지 못함)" % 접수)
        except DF.한도초과 as e:
            멈춤 = str(e)
            남은["원문"].append(접수)
        except Exception as e:                             # noqa: BLE001
            셈["오류"].append("원문 %s — %s" % (접수, type(e).__name__))
    if 남은["목록"] or 남은["원문"]:
        남은["까닭"] = 멈춤 or "원문 상한(회사 %s · 종류 %s)" % (원문상한 or "없음", " · ".join("%s %s" % (k, v) for k, v in 상한표.items() if v is not None))
        _쓰기(os.path.join(raw, 남은파일), 남은)
    elif os.path.exists(os.path.join(raw, 남은파일)):
        os.remove(os.path.join(raw, 남은파일))                    # 이어 받기로 다 받았다 — 옛 남은 목록을 지운다
    return {"호출": 셈["호출"], "회사수": len(회사들), "상장종속": [c["이름"] for c in 회사들 if c["주체"] == "상장종속"],
            "목록": sum(len(c.get("목록") or []) for c in 회사들), "원문받음": 받은, "남은원문": len(남은["원문"]), "남은목록": len(남은["목록"]),
            "한도초과": 멈춤, "오류": 셈["오류"]}


def main(argv=None):
    ap = argparse.ArgumentParser(allow_abbrev=False, description="국내 수시공시(B · I · C) — 투자 결정 · 자금 사용")
    sp = ap.add_subparsers(dest="명령")
    p = sp.add_parser("받기", allow_abbrev=False)
    p.add_argument("--회사", required=True, help="고유번호(8자리)")
    p.add_argument("--기준일", required=True)
    p.add_argument("--raw")
    p.add_argument("--해수", type=int, default=기본해수)
    p.add_argument("--종속없이", action="store_true")
    p.add_argument("--원문상한", type=int, default=원문상한기본, help="회사(주체)마다 원문 전체 상한(0 = 없음)")
    p.add_argument("--종류상한", default="", help="종류별 상한 덮기 「기타=60,증자=20」(기본: 시설투자 · 유형자산 없음 · 기타 120 · 증자 40 · 사채 30 · 지분 30)")
    p.add_argument("--목록재사용", action="store_true", help="같은 기준일 목록 파일이 있으면 목록을 다시 부르지 않고 남은 원문만 받는다")
    p.add_argument("--조회일")
    p = sp.add_parser("짓기", allow_abbrev=False)
    p.add_argument("--기준일", required=True, help="평가기준일 T(정보 경계)")
    p.add_argument("--재무기준일", default=None, help="재무기준일 F(2026-10-25 날짜 둘 — 주면 (F, T] 공시에 `기준일사이` · 없으면 지금과 같다)")
    p.add_argument("--raw", default="_raw")
    p.add_argument("--조회일")
    p.add_argument("-o", "--출력")
    a = ap.parse_args(argv)
    try:
        if a.명령 == "받기":
            r = 받기(a.회사, a.기준일, a.raw, a.해수, not a.종속없이, a.원문상한, a.조회일, 종류상한읽기(a.종류상한), a.목록재사용)
            print("수시공시 받기 %s — 호출 %d · 회사 %d(상장종속 %s) · 목록 %d · 원문 %d · 남은 원문 %d · 남은 목록 %d%s" % (
                a.회사, r["호출"], r["회사수"], " · ".join(r["상장종속"]) or "없음", r["목록"], r["원문받음"], r["남은원문"], r["남은목록"],
                (" · 한도 초과로 멈춤(%s) — 남은 받기를 %s 에 적었다" % (r["한도초과"], 남은파일)) if r["한도초과"] else ""))
            for x in r["오류"][:10]:
                print("  ※ %s" % x)
            return 발견 if r["한도초과"] else 통과
        if a.명령 == "짓기":
            낸 = 짓기(a.raw, a.기준일, a.조회일, a.재무기준일)
            out = a.출력 or os.path.join(a.raw, 출력파일)
            _쓰기(out, 낸)
            from collections import Counter                 # noqa: PLC0415
            c = Counter(d["종류"] for d in 낸["결정"])
            print("수시공시 %s — 결정 %d(%s) · 정정 묶음 %d · 기준일 뒤 %d%s · 자금사용 %d · 확인불가 %d → %s" % (
                낸["회사"], len(낸["결정"]), " · ".join("%s %d" % kv for kv in c.most_common()), sum(1 for d in 낸["결정"] if d["정정"]),
                sum(1 for d in 낸["결정"] if d["기준일뒤"]),
                (" · 재무기준일과 평가기준일 사이 %d" % sum(1 for d in 낸["결정"] if d.get("기준일사이"))) if 낸.get("재무기준일") else "",
                len(낸["자금사용"]), len(낸["확인불가"]), out))
            return 통과
    except ValueError as e:
        print("입력 오류 — %s" % e)
        return 입력오류
    ap.print_help()
    return 입력오류


if __name__ == "__main__":
    sys.exit(main())

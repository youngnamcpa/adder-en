# -*- coding: utf-8 -*-
"""공시절 — 정기보고서 「II. 사업의 내용」 · 10-K/10-Q Item 을 표준 절로 나누고, 카드 인용이 원천에 글자 그대로 있는지 대조한다
(레터 문체 3단계 B3 · 2026-10-26 · 연구/레터_문체체계_독립설계안_20261026.md 4-4).

왜 있나
    회사 소개의 첫 원천은 레터 본편이 아니라 모든 상장사에 있는 공시의 「사업의 내용」이다(미국은 10-K Item 1 · 1A · 7). 이 서식은 소제목이
    법정 · 표준이라 회사와 상관없이 나눌 수 있다. 이 도구는 **나누기만** 한다 — 무엇을 카드로 지을지는 P 갈래(`.claude/갈래/P_공시카드.md`)가 고른다.
    그리고 카드의 원천 인용이 원천 파일에 글자 그대로 있는지(공백 정규화만 허용) 본다 — 카드 감사(B4)가 `인용대조` 를 불러 쓴다.

읽는 것 (회차 `_raw/` — 읽기만)
    국내  `_raw/**/<접수번호 14자리>.xml`(정기보고서 본문 — 첨부 `_00760` 꼴은 뺀다 · `_raw/peers` 는 보지 않는다). 곁의 같은 이름 `.txt`
          (dart_fetch 가 태그를 벗겨 둔 것)가 **인용 원천**이다. XML 이 없으면 TXT 만으로 나눈다(표 구조는 잃는다).
          기본은 보고 기간 끝이 가장 늦은 보고서 하나(`--기준일` 을 주면 그날까지).
    미국  `_raw/10K_YYYYMM.htm` · `_raw/10Q_YYYYMM.htm`(sec_fetch) — 가장 늦은 10-K 와 10-Q 하나씩. 인용 원천은 htm 이다(조항추출.원문글 과 같은 벗기기).
    `--파일` 로 원문을 직접 줄 수 있다(여러 번 · 회차 폴더 기준 상대 경로 또는 절대 경로).

나누는 것
    국내  II. 사업의 내용 → 큰 절(1 사업의 개요 · 2 주요 제품 및 서비스 · 3 원재료 및 생산설비 · 4 매출 및 수주상황 · 5 위험관리 및 파생거래 ·
          6 주요계약 및 연구개발활동 · 7 기타 참고사항 — 옛 서식의 「4. 매출」 · 「5. 수주상황」 … 도 가장 가까운 이름에) → 그 안의 하위 머리
          (가. · 1. · (1) · (가) · 1) · 가) · ① · [ ])를 표준 하위 이름(산업의 특성 · 경기변동 · 경쟁요소 · 시장점유율 · 영업개황 · 주요 매출처 …)에 댄다.
          연결재무제표 주석(없으면 재무제표 주석)의 영업부문 · 매출(수익) 주석과 「III. 재무에 관한 사항 — 기타 재무에 관한 사항」 의 부문별 · 지역별 정보도 낸다.
    미국  Item 1 Business · 1A Risk Factors · 2 Properties · 5 Market(배당) · 7 MD&A · 7A Market Risk(10-Q 는 Part I Item 2 · 3, Part II Item 1A) ·
          재무제표 주석의 Segment · Revenue · Geographic · Concentration 주석. 목차의 같은 Item 줄은 뒤따르는 글이 가장 긴 것을 본문으로 고른다.
          짧은 머리 줄(뒤에 긴 문단이 오는 열두 낱말 안의 줄)은 표준 하위 이름(주요 고객 · 경쟁요소 · 판매경로 …)에 댄다.
    블록(머리 하나에서 다음 머리까지)이 「절」 하나다. 블록의 `이름` 은 자기 머리의 표준 이름, 없으면 가장 가까운 윗머리의 표준 이름, 없으면 큰 절 이름.

내는 것 — `_raw/공시절.json` (`--낼` 로 바꾼다)
    {"형식": "공시절 1", "평가기준일", "재무기준일", "원천": [{번호 · 파일 · 구조 · 서식 · 문서이름 · 기간 · 접수 · 읽은꼴}], "요약": {…},
     "못찾음": [{이름 · 갈래 · 찾은곳 · 까닭 · 글속}], "찾아둔": [{종류 · 글 · 번호}],
     "차례": ["번호 | 이름 | 제목 | 큰절 | 부문 | 글자수 | 표 수" …](한 줄에 블록 하나 — 앞머리만 읽고 길을 잡게 절 앞에 둔다),
     "절": [{번호 · 파일 · 원천 · 큰절 · 큰절제목 · 이름 · 머리표준 · 머리표준들 · 제목 · 제목경로 · 부문 · 글[문단 …] · 표[…] · 위치 · 글자수}]}
    `글` 은 문단 목록이다(한 줄에 한 문단 — Read 의 offset · limit 과 Grep 이 줄로 닿게). 문단은 원천 글자 그대로다(빈칸만 하나로).
    1,500자 넘는 문단은 문장 경계에서 여러 줄로 나눈다(조각마다 원천의 이어진 일부 — 읽는 쪽 Read 가 긴 줄을 자르지 않게).
    표는 `| 칸 | 칸 |` 줄로 펼친다(병합 칸은 펼친 자리마다 복사 · 80줄 넘으면 자른다). 〔 〕 로 시작하는 줄은 도구가 단 표지이고 원천 글이 아니다.
    표에서 인용할 때는 칸 하나만 인용한다(줄 전체는 원천 txt 에 그 꼴로 없다).
    `부문` 은 가장 가까운 [ ] 머리다 — 사업부문 머리(「[○○ 부문 : ○○]」)일 때가 많지만 소제목(「[제품 A]」 · 환경 절의 [ ] 항목)일 때도 있다.
    `못찾음` 은 서식이 늘 두는 절 · 머리 가운데 이 보고서에서 머리를 못 찾은 것이다 — `글속` 에 그 말이 글 안에 몇 번 나오는지 적는다
    (머리 없이 글 속에 있는 경우가 있다). `찾아둔` 은 카드 짓기의 보조 — 고객 집중 · 출처 표기 · 집계 기준 · 반대 진술 후보(대조 접속사) 줄.

대조 — `인용대조(카드문서, 회차)`
    카드 원천 `{"파일", "인용"}` 마다 원천 파일 글에 인용이 있는가. 규칙은 조항추출의 대조와 같다(`조항추출.정규` — &cr; 지움 · 공백을 한 칸으로).
    그 규칙으로는 없고 빈칸을 모두 지웠을 때만 있으면 「일치(빈칸)」 — 글자는 같고 빈칸 자리만 다르다(통과로 세되 따로 센다).
    원천 글: .htm · .html → 조항추출.원문글 · .xml → 태그 벗기기(dart_fetch txt 와 같은 규칙) · .json → 파일 글 + 문자열 잎 · 그 밖 → 파일 글 그대로.
    등급이 인용을 요구하는데(카드설정 「등급」 의 「원천」 = 인용) 인용이 비면 「인용없음」, 원천이 아예 없으면 「원천없음」.

쓰는 법(회차 폴더 = `_raw/` 의 부모 · 기본은 이 스크립트 폴더의 부모)
    python 스크립트/공시절.py --회차 <폴더>                                  # → <폴더>/_raw/공시절.json
    python 스크립트/공시절.py --회차 <폴더> --낼 <경로> [--평가기준일 YYYY-MM-DD]
    python 스크립트/공시절.py --회차 <폴더> --파일 _raw/사업2025/20260317000635.xml
    python 스크립트/공시절.py 대조 <카드 문서.json> --회차 <폴더> [--낼 <경로>]   # 인용이 원천에 없으면 종료 코드 1

종료 코드 — 0 통과 · 1 발견(대조 불일치 · 파일없음 · 인용없음 / 나누기에서 「사업의 내용」 · Item 1 · MD&A 를 못 찾음) · 2 입력오류(원문 · 카드 파일 없음 · JSON 깨짐).
회사 · 업종 이름은 이 도구에 한 글자도 없다. 서식(법정 소제목 · Item 번호)만 안다.
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

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:                                    # noqa: BLE001
    pass

여기 = os.path.dirname(os.path.abspath(__file__))
if 여기 not in sys.path:
    sys.path.insert(0, 여기)
import 공시표 as G                                   # noqa: E402
import 조항추출 as J                                 # noqa: E402
from 종료코드 import 통과, 발견, 입력오류            # noqa: E402

형식 = "공시절 1"
대조형식 = "인용대조 1"
정규 = J.정규

# ══ 서식 — 국내 「II. 사업의 내용」 (기업공시서식 작성기준의 소제목 · 회사 무관) ═══════════════════════════════════════
국내큰절 = [
    ("사업의 개요", r"사업의\s*개요"),
    ("주요 제품 및 서비스", r"주요\s*(제품|상품|서비스)|제품\s*및\s*서비스"),
    ("원재료 및 생산설비", r"원재료|생산\s*설비|영업\s*설비"),
    ("매출 및 수주상황", r"매출|수주|영업의\s*현황|영업\s*실적"),
    ("위험관리 및 파생거래", r"위험\s*관리|시장\s*위험|파생"),
    ("주요계약 및 연구개발활동", r"주요\s*계약|경영상의\s*주요|연구\s*개발"),
    ("기타 참고사항", r"기타\s*(참고|투자\s*의사\s*결정)|재무\s*건전성"),
]
국내큰절이름 = [x for x, _ in 국내큰절]
# 하위 머리 — 먼저 걸린 것이 이름이다(차례가 뜻이다)
국내하위 = [
    ("업계의 현황", r"업계의\s*현황"),
    ("회사의 현황", r"회사의\s*현황"),
    ("시장점유율", r"시장\s*점유율"),
    ("산업의 특성", r"산업의\s*(특성|개요)|산업\s*특성"),
    ("산업의 성장성", r"성장성"),
    ("경기변동", r"경기\s*변동|계절성"),
    ("경쟁요소", r"경쟁\s*(요소|상황|환경|력|우위|현황)|회사의\s*강점"),
    ("자원조달", r"자원\s*조달"),
    ("관련 법령 · 규제", r"법령|규제|정부\s*정책"),
    ("영업개황", r"영업\s*(의\s*)?개황|영업\s*개요|영업\s*현황"),
    ("시장 여건", r"시장\s*(의\s*)?(특징|특성|여건|현황|규모|전망)"),
    ("신규사업", r"신규\s*사업"),
    ("사업부문 구분", r"사업\s*부문.{0,4}구분|부문의\s*구분"),
    ("주요 제품 현황", r"주요\s*(제품|상품).{0,4}현황|제품\s*등의\s*현황"),
    ("가격변동추이", r"가격\s*변동"),
    ("주요 원재료", r"원재료"),
    ("생산능력 · 실적 · 가동률", r"생산\s*능력|생산\s*실적|가동\s*률|가동\s*율"),
    ("생산설비", r"생산\s*설비|물적\s*자산|설비의\s*현황|영업\s*설비"),
    ("투자계획", r"투자\s*(계획|현황)|설비\s*투자"),
    ("매출실적", r"매출\s*실적|매출\s*현황"),
    ("판매경로 · 전략", r"판매\s*(경로|방법|전략|조직|정책)"),
    ("주요 매출처", r"매출\s*처|주요\s*고객|고객\s*현황"),
    ("수주상황", r"수주"),
    ("위험관리", r"위험\s*관리|시장\s*위험|위험\s*요소"),
    ("파생상품", r"파생|풋\s*옵션|콜\s*옵션|헤지"),
    ("주요계약", r"주요\s*계약|경영상의"),
    ("연구개발", r"연구\s*개발"),
    ("지식재산권", r"지식\s*재산|지적\s*재산|특허"),
    ("환경", r"환경|온실가스"),
    ("조직도", r"조직도"),
]
# 회사 소개 다섯 수에 쓰이는 머리 — 못 찾으면 「못찾음」 에 남긴다
국내핵심하위 = ["주요 제품 현황", "매출실적", "주요 매출처", "판매경로 · 전략", "산업의 특성", "경기변동", "경쟁요소", "시장점유율",
            "영업개황", "가격변동추이", "주요 원재료", "생산능력 · 실적 · 가동률", "수주상황", "연구개발"]
# 주석 — 영업부문 · 매출(수익) 주석만
주석고름 = re.compile(r"영업\s*부문|부문\s*(별\s*)?(정보|보고)|매출|수익")
주석뺌 = re.compile(r"금융\s*(수익|원가)|기타\s*(영업\s*외\s*)?수익|영업\s*외|이자\s*수익|법인세|수익\s*증권|배당금\s*수익|지분법|기타\s*손익"
                 r"|매출\s*채권|매출\s*원가|채권")
주석하위 = [
    ("품목별 수익", r"품목|제품\s*별|서비스\s*별|유형\s*별|수익의\s*구분|구분에\s*대한"),
    ("지역별", r"지역"),
    ("주요 고객", r"주요\s*고객|외부\s*고객|고객에\s*대한\s*정보|고객\s*정보"),
    ("부문 정보", r"부문"),
]

# ══ 서식 — 미국 10-K · 10-Q (Item 번호 · 회사 무관) ═══════════════════════════════════════════════════════════════
미국10K = {"1": "사업(Item 1 Business)", "1A": "위험 요인(Item 1A Risk Factors)", "2": "설비(Item 2 Properties)",
         "5": "주식 · 배당(Item 5 Market)", "7": "경영진 분석(Item 7 MD&A)", "7A": "시장위험(Item 7A Market Risk)"}
미국10K주석 = "8"
미국10Q = {("I", "2"): "경영진 분석(Part I Item 2 MD&A)", ("I", "3"): "시장위험(Part I Item 3 Market Risk)",
         ("II", "1A"): "위험 요인(Part II Item 1A Risk Factors)"}
미국10Q주석 = ("I", "1")
미국핵심 = {"10-K": ["1", "1A", "7"], "10-Q": [("I", "2")]}
미국하위 = [                                       # 차례가 뜻이다 — 먼저 걸린 것이 이름(머리표준들에는 모두)
    ("배당", r"(?i)dividend|repurchase|shareholder return"),
    ("주요 고객", r"(?i)\bcustomers?\b"),
    ("경쟁요소", r"(?i)competition|competitive|competitors?"),
    ("판매경로 · 전략", r"(?i)distribution|marketing|\bsales\b|channels?"),
    ("원재료 · 공급", r"(?i)raw materials?|sourcing|suppl(y|iers?)|procurement|manufactur"),
    ("부문", r"(?i)\bsegments?\b"),
    ("관련 법령 · 규제", r"(?i)regulat|legislat|government|excise|litigation"),
    ("계절성", r"(?i)seasonal"),
    ("지식재산권", r"(?i)intellectual property|patents?|trademarks?"),
    ("인력", r"(?i)human capital|employees|workforce"),
    ("연구개발", r"(?i)research|innovation"),
    ("주요 제품", r"(?i)\bproducts?\b|\bbrands?\b|\bservices\b|\bportfolio\b"),
    ("전략", r"(?i)strategy|vision|mission|ambition"),
    ("영업개황", r"(?i)executive summary|overview|results of operations|business environment"),
    ("시장 여건", r"(?i)\bmarket\b|industry|trends?"),
]
미국주석고름 = re.compile(r"(?i)segment|revenue|disaggregat|geograph|concentrat|customer")
미국주석이름 = [("부문(주석 Segment)", r"(?i)segment"), ("수익(주석 Revenue)", r"(?i)revenue|disaggregat"),
            ("지역(주석 Geographic)", r"(?i)geograph"), ("집중(주석 Concentration)", r"(?i)concentrat|customer")]

# ══ 찾아둔 줄 — 카드 짓기 보조(값을 정하지 않는다) ══════════════════════════════════════════════════════════════
찾아둘 = [
    ("고객 집중", re.compile(r"(단일\s*(의\s*)?외부\s*고객|주요\s*고객|매출처|고객\s*\().{0,120}\d+(\.\d+)?\s*%|10\s*%\s*(를|을|이)?\s*(상회|초과|이상)"
                          r"|(?i:(customer|distributor|wholesaler|retailer)s?\b[^.]{0,200}\b(accounted for|represented|comprised)\b[^.]{0,80}\d+(\.\d+)?\s?%)")),
    ("출처 표기", re.compile(r"출처\s*[:：]|자료\s*[:：]|(?i:\baccording to\b|\bsources?:|\bestimated by\b|\bdata from\b)")),
    ("집계 기준", re.compile(r"법인\s*소재지|소재지\s*기준|고객\s*소재지|인도\s*기준|매출액\s*기준|출하\s*기준"
                          r"|(?i:based on (the )?(location|domicile)|attributed to (countries|geographic)|by geographic)")),
    ("반대 진술 후보", re.compile(r"(다만|그러나|반면|하지만|그럼에도|그렇지만|한편으로)|(?i:^(however|although|while|nevertheless|despite)\b|\bhowever,)")),
]
찾아둘상한 = {"고객 집중": 20, "출처 표기": 40, "집계 기준": 20, "반대 진술 후보": 40}

_머리꼴 = [("가.", re.compile(r"^([가-하])\.\s*")), ("1.", re.compile(r"^(\d{1,2})\.(?!\d)\s*")),
         ("(1)", re.compile(r"^\((\d{1,2})\)\s*")), ("(가)", re.compile(r"^\(([가-하])\)\s*")),
         ("1)", re.compile(r"^(\d{1,2})\)\s*")), ("가)", re.compile(r"^([가-하])\)\s*")), ("①", re.compile(r"^([①-⑳])\s*"))]
_문장끝 = re.compile(r"(다|음|함|임|됨)\s*[.。]?\s*$|다\.\s")          # 「요」 는 넣지 않는다 — 「개요」 · 「주요」 같은 명사 끝이다
_괄호머리 = re.compile(r"^\[\s*([^\[\]]{1,40}?)\s*\]$")
_단위줄 = re.compile(r"^\(?\s*단\s*위\s*[:：]")
_접수 = re.compile(r"^(\d{14})\.(xml|txt)$", re.I)
_미국이름 = re.compile(r"^(10[KQ])_(\d{4,6})\.(htm|html|txt)$", re.I)
_엔티티 = (("&nbsp;", " "), ("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"), ("&quot;", '"'), ("&#39;", "'"))
표줄상한 = 80


def _한줄(조각들):
    """글 조각 → 한 줄. dart_fetch txt 와 같은 규칙(엔티티 여섯만 풀고 &cr; 는 빈칸) — 원천 txt 와 공백 정규화 후 같다."""
    s = "".join(조각들)
    for a, b in _엔티티:
        s = s.replace(a, b)
    return re.sub(r"\s+", " ", s.replace("&cr;", " ")).strip()


def 태그벗기기(h):
    """XML · HTML → 글(dart_fetch._태그벗기기 와 같은 규칙 — 태그는 빈칸, 블록 태그는 줄바꿈, 엔티티 여섯만). 인용대조가 .xml 원천에 쓴다."""
    h = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", h)
    h = re.sub(r"(?i)<br\s*/?>", "\n", h)
    h = re.sub(r"(?i)</(p|div|tr|table|h\d)>", "\n", h)
    h = re.sub(r"(?i)</t[dh]>", "\t", h)
    h = re.sub(r"(?s)<[^>]+>", " ", h)
    for a, b in _엔티티:
        h = h.replace(a, b)
    return h


def _표준(글, 표, 앞만=False, 차례우선=False):
    """머리 글 → (표준 이름, 걸린 자리) — 없으면 (None, None). 앞만 = 글 앞 12자 안에서 시작하는 말만.
    고르는 법 — 가장 앞에서 시작하는 말(같으면 표의 차례). 차례우선 = 표에서 먼저 걸린 말(미국 머리 — 「Market and Dividend」 는 배당)."""
    s = (글 or "")[:30] if not 차례우선 else (글 or "")[:90]
    좋은 = (None, None)
    for 이름, 식 in 표:
        m = re.search(식, s)
        if not m or (앞만 and m.start() > 12):
            continue
        if 차례우선:
            return 이름, m
        if 좋은[1] is None or m.start() < 좋은[1].start():
            좋은 = (이름, m)
    return 좋은


def _표준들(글, 표):
    """머리 글에 걸린 표준 이름 모두(자리 차례) — 「판매경로, 경쟁 및 원재료」 같은 합친 머리가 여러 이름을 덮는다(못찾음 판정에 쓴다)."""
    s = re.sub(r"^\s*(\(?[가-하0-9]{1,2}[.)]|\[|[①-⑳])\s*", "", 글 or "")[:90]
    걸 = []
    for 이름, 식 in 표:
        m = re.search(식, s)
        if m:
            걸.append((m.start(), 이름))
    return [n for _k, n in sorted(걸)]


def _rel(p, 회차):
    try:
        return os.path.relpath(p, 회차).replace("\\", "/")
    except ValueError:
        return p.replace("\\", "/")


# ══ 국내 XML 읽기 — 사건 목록 ══════════════════════════════════════════════════════════════════════════════════
def xml사건(t):
    """XML 글 → 사건 [(종, …, 자리)]. 종: 「절」(깊이) · 「절끝」(깊이) · 「제목」(깊이, 글, 묶음 안인가) · 「묶음끝」 · 「문단」(글) · 「표」(줄들, thead수).
    글 조각은 태그 경계마다 빈칸을 넣어 잇는다 — dart_fetch 가 txt 를 지을 때 태그를 빈칸으로 바꾸는 것과 같은 규칙이라, 여기서 낸 문단은 원천 txt 에
    공백 정규화 후 그대로 있다. 표는 공시표와 같은 규칙으로 「글뿐인 표」(수 칸이 없는 한 열 · 칸 넷 이하 · 단위 줄)를 문단으로 바꾼다."""
    사건 = []
    깊이 = 0
    묶음 = 0
    제목 = None
    문단 = None
    문단자리 = 0
    표쌓 = []
    칸 = None
    # 태그가 아닌 「<…>」(본문의 「<그림 제목>」 같은 것)는 dart_fetch 의 txt 가 태그처럼 지운다 — 같게 지워야 문단이 txt 에 그대로 있다(자리는 지킨다)
    t = re.sub(r"<(?![A-Za-z/!?])[^>]*>", lambda x: " " * len(x.group(0)), t)
    for m in G._토큰.finditer(t):
        닫, 태그, 속, 글 = m.group(1), (m.group(2) or "").upper(), m.group(3) or "", m.group(5)
        if 글 is not None:
            if 칸 is not None:
                칸["글"].append(글)
            elif 제목 is not None:
                제목.append(글)
            elif 문단 is not None:
                문단.append(글)
            continue
        if 칸 is not None:
            칸["글"].append(" ")
        elif 제목 is not None:
            제목.append(" ")
        elif 문단 is not None:
            문단.append(" ")
        if not 닫:
            if 태그.startswith("SECTION-"):
                깊이 += 1
                사건.append(("절", 깊이, m.start()))
            elif 태그 == "TITLE" and 칸 is None:
                제목 = []
            elif 태그 == "TABLE-GROUP":
                묶음 += 1
            elif 태그 == "P" and not 표쌓 and 칸 is None and 제목 is None:
                if 문단 is not None:                          # 닫히지 않은 문단(</P> 가 사라진 원문) — 먼저 낸다
                    s0 = _한줄(문단)
                    if s0:
                        사건.append(("문단", s0, 문단자리))
                문단, 문단자리 = [], m.start()
            elif 태그 == "TABLE":
                if 문단 is not None:                          # 문단 안의 표 — 문단을 먼저 닫는다
                    s = _한줄(문단)
                    if s:
                        사건.append(("문단", s, 문단자리))
                    문단 = None
                표쌓.append({"줄": [], "지금줄": None, "thead": 0, "in_thead": False, "자리": m.start()})
            elif len(표쌓) == 1 and 태그 == "THEAD":
                표쌓[-1]["in_thead"] = True
            elif len(표쌓) == 1 and 태그 == "TR":
                표쌓[-1]["지금줄"] = []
            elif len(표쌓) == 1 and 태그 in G._칸태그:
                a = dict((k.upper(), v) for k, v in G._속성.findall(속))
                try:
                    rs = max(1, int(a.get("ROWSPAN", "1") or 1))
                except ValueError:
                    rs = 1
                try:
                    cs = max(1, int(a.get("COLSPAN", "1") or 1))
                except ValueError:
                    cs = 1
                칸 = {"글": [], "rs": min(rs, 200), "cs": min(cs, 60), "h": 태그 == "TH" or 표쌓[-1]["in_thead"]}
            continue
        if 태그.startswith("SECTION-"):
            사건.append(("절끝", 깊이, m.start()))
            깊이 = max(0, 깊이 - 1)
        elif 태그 == "TABLE-GROUP":
            묶음 = max(0, 묶음 - 1)
            사건.append(("묶음끝", m.start()))
        elif 태그 == "TITLE" and 제목 is not None:
            사건.append(("제목", 깊이, _한줄(제목), 묶음 > 0, m.start()))
            제목 = None
        elif 태그 == "P" and 문단 is not None:
            s = _한줄(문단)
            if s:
                사건.append(("문단", s, 문단자리))
            문단 = None
        elif len(표쌓) == 1 and 태그 in G._칸태그 and 칸 is not None:
            if 표쌓[-1]["지금줄"] is None:
                표쌓[-1]["지금줄"] = []
            표쌓[-1]["지금줄"].append((_한줄(칸["글"]), 칸["rs"], 칸["cs"], 칸["h"]))
            칸 = None
        elif len(표쌓) == 1 and 태그 == "TR":
            if 표쌓[-1]["지금줄"] is not None:
                표쌓[-1]["줄"].append(표쌓[-1]["지금줄"])
                if 표쌓[-1]["in_thead"]:
                    표쌓[-1]["thead"] += 1
            표쌓[-1]["지금줄"] = None
        elif len(표쌓) == 1 and 태그 == "THEAD":
            표쌓[-1]["in_thead"] = False
        elif 태그 == "TABLE" and 표쌓:
            s = 표쌓.pop()
            if 표쌓:
                continue
            줄 = s["줄"]
            if not 줄:
                continue
            셀수 = sum(len(r) for r in 줄)
            열수 = max((sum(c[2] for c in r) for r in 줄), default=0)
            수있음 = any(G._수칸인가(c[0]) for r in 줄 for c in r)
            if not 수있음 and (열수 <= 1 or 셀수 <= 4 or (len(줄) <= 2 and G.단위읽기(" ".join(c[0] for r in 줄 for c in r if c[0])))):
                for r in 줄:
                    글r = " ".join(c[0] for c in r if c[0])
                    if 글r:
                        사건.append(("문단", 글r, s["자리"]))
                continue
            사건.append(("표", 줄, s["thead"], s["자리"]))
    return 사건


def _표짓기(줄, thead, 앞글):
    격, 병합, 머리 = G._격자([[c for c in r] for r in 줄])
    k = G._머리줄수(격, 머리, thead)
    u = None
    for 글 in reversed(앞글[-5:]):
        u = G.단위읽기(글)
        if u:
            break
    if not u:
        for r in 격[:max(1, k)]:
            u = G.단위읽기(" ".join(r))
            if u:
                break
    return {"격자": 격, "머리줄수": k, "열이름": G._열이름(격, k), "단위": u, "줄수": len(격), "열수": len(격[0]) if 격 else 0}


def 표펼침(표, 번호):
    줄 = ["〔표 %d · %d줄 × %d열%s〕" % (번호, 표["줄수"], 표["열수"], (" · 단위 %s" % 표["단위"]) if 표["단위"] else "")]
    for r in 표["격자"][:표줄상한]:
        줄.append("| " + " | ".join(r) + " |")
    if 표["줄수"] > 표줄상한:
        줄.append("〔표 %d — 줄 %d개를 더 두었으나 여기서는 잘랐다. 원천 파일에서 본다〕" % (번호, 표["줄수"] - 표줄상한))
    return 줄


# ══ 머리 판정 ══════════════════════════════════════════════════════════════════════════════════════════════
def 국내머리(s, 다음, 표준표, 주석모드=False):
    """문단 하나가 머리인가 → (종류, 제목, 표준) 또는 None. 짧은 머리(표지 뒤 40자 안 · 문장 끝 없음)와 표준 이름으로 시작하는 붙은 머리
    (「(가) 영업개황 2분기는 …」)를 머리로 본다. 붙은 머리의 제목은 표준 이름이 끝나는 낱말까지다(글에는 문단 전체가 그대로 남는다)."""
    for 종류, 꼴 in _머리꼴:
        m = 꼴.match(s)
        if not m:
            continue
        나 = s[m.end():].strip()
        if not 나 or 나[0] in ")].,":
            return None
        if len(나) <= 40 and not _문장끝.search(나):
            return 종류, s, _표준(나, 표준표)[0]
        이름, mm = _표준(나, 표준표, 앞만=True)
        if 이름:
            k = mm.end()
            while k < len(나) and not 나[k].isspace() and 나[k] not in "(①[":
                k += 1
            return 종류, (s[:m.end()] + 나[:k]).rstrip(",.:·"), 이름
        return None
    m = _괄호머리.match(s)
    if m and 다음 is not None and 다음[0] != "표" and not (다음[0] == "문단" and _단위줄.match(다음[1])):
        return "[]", s, _표준(m.group(1), 표준표)[0]
    if 주석모드 and len(s) <= 70 and re.search(r"(공시|정보|기술|내역|구분)\s*$", s) and not _문장끝.search(s):
        return "주석머리", s, _표준(s, 표준표)[0]
    return None


_미국붙은머리 = re.compile(r"^[▪•·◦■□\-–]?\s*([A-Z][A-Za-z0-9 ,&\-/’'()]{2,70}?):\s+\S")


def 미국머리(s, 다음, 표준표, 주석모드=False):
    """짧은 머리 줄 — 3~90자 · 열두 낱말 안 · 대문자로 시작 · 끝이 마침표 · 쉼표가 아님 · 숫자 · $ · % 가 드묾 · 다음 줄이 120자 넘는 문단.
    붙은 머리 — 「▪ Customers: For a discussion …」 처럼 줄 앞의 여덟 낱말 안 이름 + 쌍점(종류 「h2」 — 짧은 머리 아래에 선다)."""
    t = s.strip()
    m = _미국붙은머리.match(t)
    if m and len(m.group(1).split()) <= 8 and len(t) > len(m.group(0)) + 20 \
            and not re.search(r"(?i)\b(include|includes|including|are|is|were|was|follows|following|as)\s*$", m.group(1)):
        return "h2", m.group(1).strip(), _표준(m.group(1), 표준표, 차례우선=True)[0]
    if not (3 <= len(t) <= 90) or len(t.split()) > 12 or not re.match(r"^[A-Z]", t):
        return None
    if t.endswith((".", ",", ";", ":")) or re.match(r"(?i)^(table of contents|index|page)\b", t):
        return None
    if "$" in t or "%" in t or sum(ch.isdigit() for ch in t) > len(t) * 0.2:
        return None
    if not 다음 or 다음[0] != "문단" or len(다음[1]) < 120:
        return None
    return "h", t, _표준(t, 표준표, 차례우선=True)[0]


# ══ 블록 짓기 — 머리 하나에서 다음 머리까지 ════════════════════════════════════════════════════════════════════
문단상한 = 1500
_문장경계 = re.compile(r"(?<=다\.)|(?<=[.?!])\s+(?=[A-Z가-힣(\[「“\"'※▪•])")


def _쪼개기(s, 상한=None):
    """긴 문단을 문장 경계에서 나눈다 — 조각마다 원천 문단의 이어진 일부라 인용이 그대로 선다(읽는 쪽 Read 가 긴 줄을 자르지 않게).
    상한(기본 1,500자) 안이면 그대로 한 줄. 경계가 없으면 나누지 않는다."""
    상한 = 상한 or 문단상한
    if len(s) <= 상한:
        return [s]
    조각, 지금 = [], ""
    끝 = 0
    for m in _문장경계.finditer(s):
        문장 = s[끝:m.start()]
        끝 = m.end()
        if 지금 and len(지금) + len(문장) > 상한 * 2 // 3:
            조각.append(지금.strip())
            지금 = ""
        지금 += 문장 + s[m.start():m.end()]
    지금 += s[끝:]
    if 지금.strip():
        조각.append(지금.strip())
    return [x for x in 조각 if x] or [s]


class 짓개:
    """원천 하나의 블록을 차례로 쌓는다(번호 · 표 번호를 원천 안에서 이어 단다)."""

    def __init__(self, 원천번호, 파일):
        self.원천번호, self.파일 = 원천번호, 파일
        self.블록 = []
        self.표번호 = 0

    def 새블록(self, 큰절, 큰절제목, 이름, 머리표준, 제목, 경로, 부문, 자리):
        b = {"번호": "%d-%03d" % (self.원천번호, len(self.블록) + 1), "파일": self.파일, "원천": self.원천번호,
             "큰절": 큰절, "큰절제목": 큰절제목, "이름": 이름, "머리표준": 머리표준, "제목": 제목, "제목경로": list(경로),
             "부문": 부문, "글": [], "표": [], "위치": {"자리": [자리, 자리]}}
        self.블록.append(b)
        return b

    def 짓기(self, 사건들, 큰절, 큰절제목, 바탕경로, 표준표, 판정, 주석모드=False, 큰절표준=None):
        """사건들(「문단」 · 「표」 · 「머리」) → 블록들. 첫 블록은 큰 절 자신(머리 앞 글)."""
        시작 = 사건들[0][-1] if 사건들 else 0
        지금 = self.새블록(큰절, 큰절제목, 큰절표준 or 큰절, None, 큰절제목, 바탕경로 + [큰절제목], None, 시작)
        만든 = [지금]
        if 큰절제목:
            지금["글"].append(큰절제목)
        쌓 = []
        앞글 = []
        for i, ev in enumerate(사건들):
            자리 = ev[-1]
            if ev[0] == "표":
                self.표번호 += 1
                표 = _표짓기(ev[1], ev[2], 앞글)
                지금["표"].append({"번호": self.표번호, "단위": 표["단위"], "줄수": 표["줄수"], "열수": 표["열수"], "머리줄수": 표["머리줄수"]})
                지금["글"].extend(표펼침(표, self.표번호))
                지금["위치"]["자리"][1] = 자리
                앞글 = []
                continue
            if ev[0] == "머리":
                종류, 제목, s = ev[1], ev[2], ev[2]
                표준 = _표준(re.sub(r"^\S+\s*", "", 제목) if 종류 == "절3" else 제목, 표준표)[0]
            else:
                s = ev[1]
                다음 = 사건들[i + 1] if i + 1 < len(사건들) else None
                판 = 판정(s, 다음, 표준표, 주석모드)
                if not 판:
                    지금["글"].extend(_쪼개기(s))
                    지금["위치"]["자리"][1] = 자리
                    앞글.append(s)
                    continue
                종류, 제목, 표준 = 판
            if any(x[0] == 종류 for x in 쌓):
                while 쌓:
                    x = 쌓.pop()
                    if x[0] == 종류:
                        break
            쌓.append((종류, 제목, 표준))
            이름 = next((x[2] for x in reversed(쌓) if x[2]), None) or 큰절표준 or 큰절
            부문 = next((x[1] for x in reversed(쌓) if x[0] == "[]"), None)
            지금 = self.새블록(큰절, 큰절제목, 이름, 표준, 제목, 바탕경로 + [큰절제목] + [x[1] for x in 쌓], 부문, 자리)
            지금["머리표준들"] = _표준들(제목, 표준표) if 표준 else []
            if 표준 and 표준 not in 지금["머리표준들"]:
                지금["머리표준들"].insert(0, 표준)
            지금["글"].extend(_쪼개기(s))
            만든.append(지금)
            앞글 = [s]
        return 만든


# ══ 국내 — XML ════════════════════════════════════════════════════════════════════════════════════════════
def _큰절이름(제목):
    s = re.sub(r"^\s*\d{1,2}\s*[.\-]\s*", "", 제목 or "")
    for 이름, 식 in 국내큰절:
        if re.search(식, s):
            return 이름
    return None


def _문서정보(t):
    m = re.search(r"<DOCUMENT-NAME[^>]*>([^<]*)<", t)
    이름 = _한줄([m.group(1)]) if m else None
    시 = re.search(r'AUNIT="PERIODFROM"[^>]*AUNITVALUE="(\d{8})"', t) or re.search(r'AUNITVALUE="(\d{8})"[^>]*AUNIT="PERIODFROM"', t)
    끝 = re.search(r'AUNIT="PERIODTO"[^>]*AUNITVALUE="(\d{8})"', t) or re.search(r'AUNITVALUE="(\d{8})"[^>]*AUNIT="PERIODTO"', t)
    기 = None
    if 시 and 끝:
        f = lambda x: "%s-%s-%s" % (x[:4], x[4:6], x[6:])            # noqa: E731
        기 = {"시작": f(시.group(1)), "끝": f(끝.group(1))}
    return 이름, 기


def xml읽기(경로):
    """원문 XML 글 — 머리는 utf-8 이라 적어도 옛 원문(dart3.xsd)은 cp949 인 일이 있다. dart_fetch 가 txt 를 지을 때와 같은 차례(utf-8 → cp949 → euc-kr)로 푼다."""
    바 = io.open(경로, "rb").read()
    for 인코딩 in ("utf-8", "cp949", "euc-kr"):
        try:
            return 바.decode(인코딩)
        except UnicodeDecodeError:
            continue
    return 바.decode("utf-8", errors="ignore")


def 국내xml나누기(xml경로, 파일, 원천번호):
    """XML → (블록들, 못찾음, 정보). 정보 = {문서이름 · 기간 · 사업의내용 · 큰절수 · 주석수}."""
    t = xml읽기(xml경로)
    문서이름, 기간 = _문서정보(t)
    사건 = xml사건(t)
    짓 = 짓개(원천번호, 파일)
    못 = []
    경로 = {}
    구획 = {"II": [], "주석연결": [], "주석별도": [], "기타재무": []}
    II제목 = None
    for ev in 사건:
        if ev[0] == "제목":
            _종, d, s, 묶, 자리 = ev
            if not 묶:
                경로[d] = s
                for k in [k for k in 경로 if k > d]:
                    del 경로[k]
                if d >= 3 and 경로.get(1) and re.search(r"사업의\s*내용", 경로.get(1, "")):
                    구획["II"].append(("머리절", 경로.get(2), ("머리", "절3", s, 자리)))
                continue
            ev = ("묶음제목", s, 자리)
        elif ev[0] in ("절", "절끝", "묶음끝"):
            if ev[0] == "절끝":
                for k in [k for k in 경로 if k >= ev[1]]:
                    del 경로[k]
            continue
        p1, p2 = 경로.get(1, ""), 경로.get(2, "")
        if re.search(r"사업의\s*내용", p1):
            II제목 = p1
            if ev[0] != "묶음제목":
                구획["II"].append(("내용", p2, ev))
        elif re.search(r"재무에\s*관한", p1) and re.search(r"연결\s*재무\s*제표\s*주석", p2):
            구획["주석연결"].append(ev)
        elif re.search(r"재무에\s*관한", p1) and re.search(r"재무\s*제표\s*주석", p2):
            구획["주석별도"].append(ev)
        elif re.search(r"재무에\s*관한", p1) and re.search(r"기타\s*재무", p2):
            if ev[0] != "묶음제목":
                구획["기타재무"].append(ev)
    정보 = {"문서이름": 문서이름, "기간": 기간, "사업의내용": II제목, "큰절": [], "주석": []}
    # ── II 큰 절 ──
    if not 구획["II"]:
        못.append({"이름": "사업의 내용", "갈래": "큰절", "찾은곳": "문서 전체의 SECTION-1 제목", "까닭": "「사업의 내용」 SECTION-1 이 없다", "글속": 0})
    else:
        묶 = []                                   # [(큰절제목, [사건])]
        섹션2있음 = any(x[1] for x in 구획["II"])
        for 종, p2, ev in 구획["II"]:
            if 섹션2있음:
                if not 묶 or 묶[-1][0] != p2:
                    묶.append((p2, []))
                if 종 == "머리절" or ev[0] in ("문단", "표"):
                    묶[-1][1].append(ev)
            else:                                 # SECTION-2 없이 문단 「1. 사업의 개요」 꼴로 큰 절을 가른 서식
                if ev[0] == "문단" and re.match(r"^\d{1,2}\.(?!\d)\s*\S.{0,30}$", ev[1]) and _큰절이름(ev[1]):
                    묶.append((ev[1], []))
                    continue
                if not 묶:
                    묶.append((II제목, []))
                묶[-1][1].append(ev)
        본이름 = set()
        for 제목, 사건들 in 묶:
            if not 제목:
                continue
            이름 = _큰절이름(제목) or re.sub(r"^\s*\d{1,2}\s*[.\-]\s*", "", 제목)
            본이름.add(이름)
            정보["큰절"].append(제목)
            짓.짓기(사건들, 이름, 제목, [II제목], 국내하위, 국내머리, 큰절표준=이름)
        for 이름 in 국내큰절이름:
            if 이름 not in 본이름:
                못.append({"이름": 이름, "갈래": "큰절", "찾은곳": "II. 사업의 내용의 큰 절 %d개(%s)" % (len(정보["큰절"]), " · ".join(정보["큰절"])[:200]),
                          "까닭": "이 이름에 닿는 큰 절 제목이 없다(서식이 다르거나 합쳐 적었다)", "글속": 0})
    # ── 주석(연결 우선) ──
    주석사건 = 구획["주석연결"] or 구획["주석별도"]
    주석곳 = "연결재무제표 주석" if 구획["주석연결"] else ("재무제표 주석" if 구획["주석별도"] else None)
    for 제목, 사건들 in 주석나누기(주석사건):
        고름 = _주석고름글(제목)
        정보["주석"].append(고름)
        if not 주석고름.search(고름) or 주석뺌.search(고름):
            continue
        이름 = next((n for n, 식 in [("영업부문(주석)", r"부문"), ("매출 · 수익(주석)", r"매출|수익")] if re.search(식, 고름)), "주석")
        짓.짓기(사건들, 이름, 제목, [주석곳], 주석하위 + 국내하위, 국내머리, 주석모드=True, 큰절표준=이름)
    if not 주석곳:
        못.append({"이름": "재무제표 주석", "갈래": "주석", "찾은곳": "III. 재무에 관한 사항", "까닭": "주석 구획(연결 · 별도)이 없다", "글속": 0})
    else:
        if not any(re.search(r"부문", x) for x in 정보["주석"]):
            못.append({"이름": "영업부문(주석)", "갈래": "주석", "찾은곳": "%s 제목 %d개" % (주석곳, len(정보["주석"])),
                      "까닭": "영업부문 주석 제목이 없다", "글속": 0})
        if not any(주석고름.search(x) and not 주석뺌.search(x) and re.search(r"매출|수익", x) for x in 정보["주석"]) \
                and not any(b["머리표준"] == "품목별 수익" for b in 짓.블록):
            못.append({"이름": "매출 · 수익(주석)", "갈래": "주석", "찾은곳": "%s 제목 %d개" % (주석곳, len(정보["주석"])),
                      "까닭": "매출 · 수익 주석 제목이 없다", "글속": 0})
    # ── III 기타 재무 — 부문별 · 지역별 ──
    if 구획["기타재무"]:
        임시 = 짓개(원천번호, 파일)
        임시.표번호 = 짓.표번호
        블 = 임시.짓기(구획["기타재무"], "부문 · 지역 재무정보(III 기타 재무)", "기타 재무에 관한 사항", ["III. 재무에 관한 사항"], 국내하위, 국내머리)
        고른 = [b for b in 블 if any(re.search(r"(부문\s*별|지역\s*별)\s*(연결\s*)?(재무\s*)?정보", x) for x in b["제목경로"][2:])]
        for b in 고른:
            b["번호"] = "%d-%03d" % (원천번호, len(짓.블록) + 1)
            b["이름"] = "부문 · 지역 재무정보(III 기타 재무)" if not b["머리표준"] else b["이름"]
            짓.블록.append(b)
        짓.표번호 = 임시.표번호
    return 짓.블록, 못, 정보


def _주석고름글(제목):
    """주석을 고르는 글 — 제목 앞 서른 자(옛 서식은 문단 전체가 제목이라 본문의 낱말에 걸리지 않게)."""
    return (제목 or "")[:30]


def 주석나누기(사건들):
    """주석 구획 사건 → [(주석 제목, [사건])]. 주석 머리 = 묶음(TABLE-GROUP) 제목 「4. 영업부문」 꼴, 없으면 번호 문단(옛 서식 — 번호가 1 부터 하나씩
    오를 때만 · 주석 안 목록의 「1.」 에 걸리지 않게). 옛 서식은 머리와 본문이 한 문단에 붙어 있다(「1. 일반 사항회사는 …」) — 그때는 문단 전체를
    제목으로 둔다(원천 글 그대로 — 그 주석의 첫 글이 된다). 주석을 고르는 쪽은 제목 앞 서른 자만 본다(`_주석고름글`)."""
    낸 = []
    묶음있음 = any(ev[0] == "묶음제목" and re.match(r"^\d{1,3}\.", ev[1]) for ev in 사건들)
    앞번호 = 0
    for ev in 사건들:
        if ev[0] == "묶음제목":
            if re.match(r"^\d{1,3}\.", ev[1]):
                낸.append((ev[1], []))
            elif 낸:
                낸[-1][1].append(("문단", ev[1], ev[2]))
            continue
        if not 묶음있음 and ev[0] == "문단":
            m = re.match(r"^(\d{1,2})\.(?!\d)\s*([^\d\s].*)$", ev[1])
            if m and 앞번호 < int(m.group(1)) <= 앞번호 + 5:          # 머리 문단이 빠진 원문(「2.1」 부터 적음 · 표 안의 머리)이 있어 네 칸까지 건너뛴다
                앞번호 = int(m.group(1))
                낸.append((ev[1], []))
                continue
        if 낸 and ev[0] in ("문단", "표"):
            낸[-1][1].append(ev)
    return 낸


# ══ 국내 — TXT 만 있을 때 ═════════════════════════════════════════════════════════════════════════════════
def _가장긴구간(줄들, 시작식, 끝식):
    시작들 = [i for i, l in enumerate(줄들) if re.match(시작식, l)]
    끝들 = [i for i, l in enumerate(줄들) if re.match(끝식, l)]
    좋은 = None
    for s in 시작들:
        e = next((x for x in 끝들 if x > s), len(줄들))
        if 좋은 is None or (e - s) > (좋은[1] - 좋은[0]):
            좋은 = (s, e)
    return 좋은


def 국내txt나누기(txt경로, 파일, 원천번호):
    줄들 = [re.sub(r"\s+", " ", l).strip() for l in io.open(txt경로, encoding="utf-8", errors="ignore").read().split("\n")]
    짓 = 짓개(원천번호, 파일)
    못 = []
    정보 = {"문서이름": None, "기간": None, "사업의내용": None, "큰절": [], "주석": []}
    구 = _가장긴구간(줄들, r"^(II|Ⅱ)\.\s*사업의\s*내용$", r"^(III|Ⅲ)\.\s*재무에\s*관한\s*사항$")
    if not 구:
        못.append({"이름": "사업의 내용", "갈래": "큰절", "찾은곳": "txt 줄 전체", "까닭": "「II. 사업의 내용」 줄이 없다", "글속": 0})
    else:
        s, e = 구
        정보["사업의내용"] = 줄들[s]
        묶 = []
        for i in range(s + 1, e):
            l = 줄들[i]
            if not l:
                continue
            if re.match(r"^\d{1,2}\.(?!\d)\s*\S.{0,30}$", l) and _큰절이름(l) and not _문장끝.search(l):
                묶.append((l, i, []))
                continue
            if not 묶:
                묶.append((줄들[s], s, []))
            묶[-1][2].append(("문단", l, i + 1))
        본 = set()
        for 제목, i, 사건들 in 묶:
            이름 = _큰절이름(제목) or 제목
            본.add(이름)
            정보["큰절"].append(제목)
            for b in 짓.짓기(사건들, 이름, 제목, [줄들[s]], 국내하위, 국내머리, 큰절표준=이름):
                b["위치"] = {"txt줄": list(b["위치"]["자리"])}
        for 이름 in 국내큰절이름:
            if 이름 not in 본:
                못.append({"이름": 이름, "갈래": "큰절", "찾은곳": "txt II 구간의 번호 줄 %d개" % len(정보["큰절"]),
                          "까닭": "이 이름에 닿는 큰 절 줄이 없다", "글속": 0})
    구2 = _가장긴구간(줄들, r"^\d{1,2}\.\s*연결\s*재무\s*제표\s*주석$", r"^\d{1,2}\.\s*(재무\s*제표|배당에\s*관한\s*사항)$") \
        or _가장긴구간(줄들, r"^\d{1,2}\.\s*재무\s*제표\s*주석$", r"^\d{1,2}\.\s*배당에\s*관한\s*사항$")
    if 구2:
        사건들 = [("문단", 줄들[i], i + 1) for i in range(구2[0] + 1, 구2[1]) if 줄들[i]]
        for 제목, 사건 in 주석나누기(사건들):
            고름 = _주석고름글(제목)
            정보["주석"].append(고름)
            if not 주석고름.search(고름) or 주석뺌.search(고름):
                continue
            이름 = "영업부문(주석)" if re.search(r"부문", 고름) else "매출 · 수익(주석)"
            for b in 짓.짓기(사건, 이름, 제목, [줄들[구2[0]]], 주석하위 + 국내하위, 국내머리, 주석모드=True, 큰절표준=이름):
                b["위치"] = {"txt줄": list(b["위치"]["자리"])}
    return 짓.블록, 못, 정보


# ══ 미국 ═══════════════════════════════════════════════════════════════════════════════════════════════
def 미국나누기(경로, 파일, 원천번호):
    글 = J.원문글(경로) if 경로.lower().endswith((".htm", ".html")) else io.open(경로, encoding="utf-8", errors="ignore").read()
    줄들 = [re.sub(r"\s+", " ", l).strip() for l in 글.split("\n")]
    이 = os.path.basename(경로)
    m = _미국이름.match(이)
    서식 = ("10-Q" if m.group(1).upper() == "10Q" else "10-K") if m else ("10-Q" if re.search(r"FORM\s+10-Q", 글[:20000]) else "10-K")
    짓 = 짓개(원천번호, 파일)
    못 = []
    머리들 = []
    부 = None
    for i, l in enumerate(줄들):
        if not l:
            continue
        mp = re.match(r"(?i)^part\s+(iv|i{1,3})\b", l)
        if mp and len(l) <= 80:
            부 = mp.group(1).upper()
            머리들.append((i, 부, "PART", l))
            continue
        mi = re.match(r"(?i)^item\s*(\d{1,2}[a-c]?)\s*[.:\-–—]?\s*(.*)$", l)
        if mi and len(l) <= 220:
            제목 = mi.group(2).strip()
            if not 제목:
                제목 = next((줄들[k] for k in range(i + 1, min(i + 4, len(줄들))) if 줄들[k]), "")[:120]
            머리들.append((i, 부, mi.group(1).upper(), 제목))
    고른 = {}
    for n, (i, p, 항, 제목) in enumerate(머리들):
        if 항 == "PART":
            continue
        끝 = 머리들[n + 1][0] if n + 1 < len(머리들) else len(줄들)
        길이 = sum(len(줄들[k]) for k in range(i, 끝))
        열쇠 = 항 if 서식 == "10-K" else (p or "I", 항)
        if 열쇠 not in 고른 or 길이 > 고른[열쇠][2]:
            고른[열쇠] = (i, 끝, 길이, 제목)
    표 = 미국10K if 서식 == "10-K" else 미국10Q
    정보 = {"문서이름": 서식, "기간": None, "항목": sorted("%s" % (k,) for k in 고른)}
    # 표지의 「For the fiscal year ended December 31 , 2025」 — iXBRL 머리 뒤에 있어 앞 20만 자를 본다 · 쉼표 앞 빈칸도 받는다
    mper = re.search(r"(?i)for\s+the\s+(fiscal\s+year|quarterly\s+period)\s+ended\s*:?\s*([A-Z][a-z]+)\s+(\d{1,2})\s*,\s*(\d{4})", 글[:200000])
    if mper:
        try:
            정보["기간"] = {"끝": datetime.datetime.strptime("%s %s %s" % (mper.group(2), mper.group(3), mper.group(4)), "%B %d %Y").date().isoformat()}
        except ValueError:
            pass
    for 열쇠, 이름 in 표.items():
        if 열쇠 not in 고른:
            if 열쇠 in 미국핵심[서식]:
                못.append({"이름": 이름, "갈래": "Item", "찾은곳": "Item 머리 줄 %d개" % len([x for x in 머리들 if x[2] != "PART"]),
                          "까닭": "이 Item 머리 줄이 없다", "글속": 0})
            continue
        i, 끝, _길, 제목 = 고른[열쇠]
        사건들 = [("문단", 줄들[k], k) for k in range(i + 1, 끝) if 줄들[k]]
        큰제목 = 줄들[i]
        for b in 짓.짓기(사건들, 이름, 큰제목, [서식], 미국하위, 미국머리, 큰절표준=이름):
            b["위치"] = {"줄": list(b["위치"]["자리"]), "기준": "원문글(htm 벗김) 줄 번호 — 0 부터"}
    # ── 주석 ──
    열쇠 = 미국10K주석 if 서식 == "10-K" else 미국10Q주석
    주석수 = 0
    if 열쇠 in 고른:
        i, 끝, _길, _제 = 고른[열쇠]
        주석머리 = [(k, 줄들[k]) for k in range(i, 끝) if re.match(r"(?i)^note\s+\d{1,2}\s*[.:\-–—]?\s*\S.{1,150}$", 줄들[k])]
        if not 주석머리:
            주석머리 = [(k, 줄들[k]) for k in range(i, 끝) if re.match(r"^\d{1,2}\.\s+[A-Z][A-Za-z ,&\-–—()/']{2,100}$", 줄들[k])]
        주석수 = len(주석머리)
        정보["주석"] = [x[1][:80] for x in 주석머리]
        for n, (k, 제목) in enumerate(주석머리):
            if not 미국주석고름.search(제목):
                continue
            e = 주석머리[n + 1][0] if n + 1 < len(주석머리) else 끝
            이름 = next((nm for nm, 식 in 미국주석이름 if re.search(식, 제목)), "주석")
            b = 짓.새블록(이름, 제목, 이름, None, 제목, [서식, 제목], None, k)
            b["글"] = [줄들[x] for x in range(k, e) if 줄들[x]]
            b["위치"] = {"줄": [k, e - 1], "기준": "원문글(htm 벗김) 줄 번호 — 0 부터"}
        if not any(re.search(r"(?i)segment", x[1]) for x in 주석머리):
            못.append({"이름": "부문(주석 Segment)", "갈래": "주석", "찾은곳": "재무제표 주석 머리 %d개" % 주석수, "까닭": "Segment 주석 머리가 없다", "글속": 0})
    else:
        못.append({"이름": "재무제표 주석", "갈래": "주석", "찾은곳": "Item %s" % (열쇠,), "까닭": "재무제표 Item 을 못 찾아 주석을 못 봤다", "글속": 0})
    return 짓.블록, 못, 정보, 서식, 줄들


# ══ 원천 고르기 ══════════════════════════════════════════════════════════════════════════════════════════
def 원천고르기(회차, 파일들=None, 기준일=None):
    """→ [(경로, 종류)] — 종류: 국내xml · 국내txt · 미국."""
    raw = os.path.join(회차, "_raw")
    if 파일들:
        낸 = []
        for p in 파일들:
            p = p if os.path.isabs(p) else os.path.join(회차, p)
            if not os.path.exists(p):
                raise FileNotFoundError(p)
            b = os.path.basename(p).lower()
            if _미국이름.match(os.path.basename(p)) or b.endswith((".htm", ".html")):
                낸.append((p, "미국"))
            elif b.endswith(".xml"):
                낸.append((p, "국내xml"))
            else:
                낸.append((p, "국내txt"))
        return 낸
    후 = []
    for p in glob.glob(os.path.join(raw, "**", "*.*"), recursive=True):
        rel = os.path.relpath(p, raw).replace("\\", "/")
        if rel.split("/")[0] == "peers":
            continue
        m = _접수.match(os.path.basename(p))
        if m and m.group(2).lower() == "xml":
            이름, 기 = _문서정보(xml읽기(p)[:400000])
            if not 이름 or "보고서" not in 이름 or "감사" in 이름:
                continue
            끝 = (기 or {}).get("끝") or ""
            if 기준일 and 끝 and 끝 > 기준일:
                continue
            후.append((끝, m.group(1), p, "국내xml"))
    if not 후:
        for p in glob.glob(os.path.join(raw, "**", "*.txt"), recursive=True):
            rel = os.path.relpath(p, raw).replace("\\", "/")
            m = _접수.match(os.path.basename(p))
            if m and rel.split("/")[0] != "peers":
                후.append(("", m.group(1), p, "국내txt"))
    낸 = []
    if 후:
        후.sort(reverse=True)
        낸.append((후[0][2], 후[0][3]))
    미 = {}
    for p in glob.glob(os.path.join(raw, "10*_*.*")):
        m = _미국이름.match(os.path.basename(p))
        if not m:
            continue
        종 = m.group(1).upper()
        if 기준일 and m.group(2)[:6] > 기준일.replace("-", "")[:6]:
            continue
        앞 = 미.get(종)
        좋다 = (m.group(2), 0 if p.lower().endswith(".txt") else 1)
        if 앞 is None or 좋다 > 앞[0]:
            미[종] = (좋다, p)
    for 종 in ("10K", "10Q"):
        if 종 in 미:
            낸.append((미[종][1], "미국"))
    return 낸


# ══ 보조 — 위치 · 대조율 · 찾아둔 · 못찾음 글속 ═══════════════════════════════════════════════════════════════
def _문단줄(l):
    return bool(l) and not l.startswith("〔") and not l.startswith("| ")


def txt줄달기(블록들, txt경로):
    """블록마다 첫 긴 문단이 원천 txt 의 몇째 줄인가(1부터 · 문서 차례로 앞에서부터 찾는다 — 목차 줄에 걸리지 않게)."""
    줄 = [정규(l) for l in io.open(txt경로, encoding="utf-8", errors="ignore").read().split("\n")]
    커 = 0
    for b in 블록들:
        긴 = next((정규(l) for l in b["글"][1:] + b["글"][:1] if _문단줄(l) and len(l) >= 20), None)
        if not 긴:
            continue
        조각 = 긴[:40]
        k = next((i for i in range(커, len(줄)) if 조각 in 줄[i]), None)
        if k is None:
            k = next((i for i in range(0, len(줄)) if 조각 in 줄[i]), None)
        if k is not None:
            b["위치"]["txt줄"] = k + 1
            커 = k


def 글대조율(블록들, 인용경로):
    """블록 문단(표 줄 · 표지 줄 뺌)이 인용 원천 글에 공백 정규화 후 있는가 — 나누기가 글을 바꾸지 않았는지 스스로 본다."""
    원 = _정규원천(인용경로)
    n = 있 = 0
    빠짐 = []
    for b in 블록들:
        for l in b["글"]:
            if not _문단줄(l):
                continue
            n += 1
            if 정규(l) in 원:
                있 += 1
            elif len(빠짐) < 10:
                빠짐.append("%s: %s" % (b["번호"], l[:60]))
    return {"문단": n, "원천에있음": 있, "비율": round(있 / n, 4) if n else None, "없는보기": 빠짐}


def 찾아두기(블록들):
    낸 = []
    셈 = {}
    for b in 블록들:
        for l in b["글"]:
            if not _문단줄(l):
                continue
            for 종류, 식 in 찾아둘:
                if 셈.get(종류, 0) >= 찾아둘상한[종류]:
                    continue
                if 식.search(l):
                    셈[종류] = 셈.get(종류, 0) + 1
                    낸.append({"종류": 종류, "번호": b["번호"], "이름": b["이름"], "글": l})
    return 낸


def 글속셈(블록들, 식):
    셈, 첫 = 0, None
    r = re.compile(식)
    for b in 블록들:
        for l in b["글"]:
            if _문단줄(l) and r.search(l):
                셈 += 1
                첫 = 첫 or b["번호"]
    return 셈, 첫


def 회차날짜(회차):
    """회차 `_raw/` 의 다른 갈래 산출에서 평가기준일 · 재무기준일(없으면 None)."""
    for 이름 in ("매출스트림_웹조사.json", "동인원천.json", "외부제약.json", "투자능력.json"):
        p = os.path.join(회차, "_raw", 이름)
        if os.path.exists(p):
            try:
                d = json.load(io.open(p, encoding="utf-8"))
            except (ValueError, OSError):
                continue
            t, f = d.get("평가기준일"), d.get("재무기준일")
            if t:
                return t, f, "_raw/" + 이름
    return None, None, None


# ══ 나누기 ═══════════════════════════════════════════════════════════════════════════════════════════════
def 나누기(회차, 파일들=None, 기준일=None, 평가기준일=None, 재무기준일=None):
    """회차 → 공시절 문서(dict)와 종료 코드."""
    원천들 = 원천고르기(회차, 파일들, 기준일)
    if not 원천들:
        return None, 입력오류
    문서 = {"형식": 형식, "만든날": datetime.date.today().isoformat(), "도구": "스크립트/공시절.py",
          "읽는법": "절[] 은 머리 하나에서 다음 머리까지의 블록이다. 이름 = 표준 이름(자기 머리 → 윗머리 → 큰 절). 글[] 은 원천 글자 그대로의 문단(빈칸만 하나로) · "
                  "〔 〕 줄은 도구 표지 · | 칸 | 줄은 표(인용은 칸 하나만). 카드 원천의 파일은 절의 「파일」 을 그대로 쓴다.",
          "원천": [], "차례": [], "절": [], "못찾음": [], "찾아둔": [], "요약": {}}
    t, f, 근 = 회차날짜(회차)
    문서["평가기준일"] = 평가기준일 or t
    문서["재무기준일"] = 재무기준일 or f
    if 근 and not 평가기준일:
        문서["기준일_근거"] = 근
    rc = 통과
    대조 = []
    for n, (p, 종류) in enumerate(원천들, 1):
        if 종류 == "국내xml":
            txt = re.sub(r"\.xml$", ".txt", p, flags=re.I)
            인용 = txt if os.path.exists(txt) else p
            파일 = _rel(인용, 회차)
            블, 못, 정보 = 국내xml나누기(p, 파일, n)
            if os.path.exists(txt):
                txt줄달기(블, txt)
            서식 = "국내 정기보고서"
            읽은꼴 = "XML"
            구조 = _rel(p, 회차)
            핵심 = [(nm, 식) for nm, 식 in 국내하위 if nm in 국내핵심하위]
            if not 정보.get("사업의내용"):
                rc = 발견
        elif 종류 == "국내txt":
            인용 = p
            파일 = _rel(p, 회차)
            블, 못, 정보 = 국내txt나누기(p, 파일, n)
            서식, 읽은꼴, 구조 = "국내 정기보고서", "TXT", None
            핵심 = [(nm, 식) for nm, 식 in 국내하위 if nm in 국내핵심하위]
            if not 정보.get("사업의내용"):
                rc = 발견
        else:
            인용 = p
            파일 = _rel(p, 회차)
            블, 못, 정보, 서식0, _줄 = 미국나누기(p, 파일, n)
            서식, 읽은꼴, 구조 = "미국 " + 서식0, "HTM" if p.lower().endswith((".htm", ".html")) else "TXT", None
            핵심 = [(nm, 식) for nm, 식 in 미국하위 if nm in ("주요 고객", "경쟁요소", "부문", "주요 제품")] if 서식0 == "10-K" else []
            if any(x["갈래"] == "Item" for x in 못):
                rc = 발견
        # 핵심 하위 머리 — 머리가 없으면 글 속 셈과 함께 못찾음에
        본표준 = {x for b in 블 for x in ([b.get("머리표준")] + (b.get("머리표준들") or [])) if x}
        for 이름, 식 in 핵심:
            if 이름 in 본표준:
                continue
            셈, 첫 = 글속셈(블, 식)
            못.append({"이름": 이름, "갈래": "하위 머리", "찾은곳": "이 원천의 블록 %d개 머리" % len(블),
                      "까닭": "이 이름의 머리가 없다" + ("" if 셈 else " · 글 속에도 그 말이 없다"),
                      "글속": 셈, "글속첫블록": 첫})
        for x in 못:
            x["원천"] = n
        m = _접수.match(os.path.basename(p))
        문서["원천"].append({"번호": n, "파일": 파일, "구조": 구조, "서식": 서식, "문서이름": 정보.get("문서이름"), "기간": 정보.get("기간"),
                          "접수": m.group(1) if m else os.path.splitext(os.path.basename(p))[0], "읽은꼴": 읽은꼴,
                          "큰절": 정보.get("큰절") or 정보.get("항목"), "주석머리수": len(정보.get("주석") or [])})
        문서["절"].extend(블)
        문서["못찾음"].extend(못)
        문서["찾아둔"].extend(찾아두기(블))
        대조.append(dict(글대조율(블, 인용), 원천=n))
    for b in 문서["절"]:
        b["글자수"] = sum(len(l) for l in b["글"])
        문서["차례"].append("%s | %s | %s | %s | %s | %d자 | 표 %d" % (b["번호"], b["이름"], b["제목"][:60], b["큰절"], b["부문"] or "-",
                                                             b["글자수"], len(b["표"])))
    if not 문서["재무기준일"]:
        끝들 = [((x.get("기간") or {}).get("끝")) for x in 문서["원천"] if (x.get("기간") or {}).get("끝")]
        if 끝들:
            문서["재무기준일"] = max(끝들)
            문서["재무기준일_근거"] = "원천 보고서 기간 끝"
    셈 = {}
    for b in 문서["절"]:
        셈[b["이름"]] = 셈.get(b["이름"], 0) + 1
    문서["요약"] = {"원천수": len(문서["원천"]), "절수": len(문서["절"]), "글자수": sum(b["글자수"] for b in 문서["절"]),
                 "이름별": 셈, "못찾음": len(문서["못찾음"]), "찾아둔": len(문서["찾아둔"]), "글대조": 대조}
    # 칸 차례 — 읽는 쪽(갈래)이 앞머리만 읽고 길을 잡게: 머리 · 원천 · 요약 · 못찾음 · 찾아둔 · 차례(한 줄에 블록 하나) 다음에 절
    차례 = ("형식", "만든날", "도구", "평가기준일", "재무기준일", "기준일_근거", "재무기준일_근거", "읽는법", "원천", "요약", "못찾음", "찾아둔",
          "차례_꼴", "차례", "절")
    문서["차례_꼴"] = "번호 | 이름 | 제목 | 큰절 | 부문 | 글자수 | 표 수 — 블록은 「\"번호\": \"<번호>\"」 를 Grep 해 찾는다"
    문서 = {k: 문서[k] for k in 차례 if k in 문서} | {k: v for k, v in 문서.items() if k not in 차례}
    return 문서, rc


# ══ 인용 대조 ═══════════════════════════════════════════════════════════════════════════════════════════
_원천캐시 = {}


def _잎(x):
    if isinstance(x, str):
        yield x
    elif isinstance(x, (int, float)) and not isinstance(x, bool):
        yield str(x)
    elif isinstance(x, dict):
        for v in x.values():
            yield from _잎(v)
    elif isinstance(x, list):
        for v in x:
            yield from _잎(v)


def 원천글(경로):
    """인용대조가 보는 원천 글 — 확장자마다 하나의 규칙."""
    확 = os.path.splitext(경로)[1].lower()
    if 확 in (".htm", ".html"):
        return J.원문글(경로)
    if 확 == ".xml":
        return 태그벗기기(xml읽기(경로))
    글 = io.open(경로, encoding="utf-8", errors="replace").read()
    if 확 == ".json":
        try:
            return 글 + "\n" + "\n".join(_잎(json.loads(글)))
        except ValueError:
            return 글
    return 글


def _정규원천(경로):
    k = os.path.abspath(경로)
    if k not in _원천캐시:
        n = 정규(원천글(경로))
        _원천캐시[k] = (n, re.sub(r"\s+", "", n))
    return _원천캐시[k][0]


def _빈칸없는원천(경로):
    _정규원천(경로)
    return _원천캐시[os.path.abspath(경로)][1]


def _등급원천():
    try:
        d = json.load(io.open(os.path.join(여기, "카드설정.json"), encoding="utf-8"))
        return {k: v.get("원천", "인용") for k, v in d.get("등급", {}).items()}
    except (OSError, ValueError):
        return {}


def 인용대조(카드문서, 회차):
    """카드 문서(dict 또는 경로)의 원천 인용이 원천 파일에 글자 그대로 있나(공백 정규화만 허용 — 조항추출.정규).
    → {"형식", "회차", "카드수", "인용수", "셈": {판정: 수}, "줄": [{"id", "순번", "파일", "인용", "판정", "까닭"}], "통과"}.
    판정 — 일치 · 일치(빈칸) · 불일치 · 파일없음 · 인용없음 · 원천없음 · 파일만(등급이 파일만 요구 — 계산 카드)."""
    if isinstance(카드문서, str):
        카드문서 = json.load(io.open(카드문서, encoding="utf-8"))
    요구표 = _등급원천()
    줄, 셈 = [], {}

    def 적(d):
        줄.append(d)
        셈[d["판정"]] = 셈.get(d["판정"], 0) + 1

    카드들 = (카드문서 or {}).get("카드") or []
    for c in 카드들:
        if not isinstance(c, dict):
            continue
        요구 = 요구표.get(c.get("등급"), "인용")
        원 = c.get("원천") or []
        if not 원:
            if 요구 in ("인용", "파일"):
                적({"id": c.get("id"), "순번": None, "파일": None, "인용": None, "판정": "원천없음",
                   "까닭": "등급 「%s」는 원천이 있어야 한다" % c.get("등급")})
            continue
        for i, o in enumerate(원):
            o = o if isinstance(o, dict) else {}
            파일 = o.get("파일")
            인 = o.get("인용")
            d = {"id": c.get("id"), "순번": i, "파일": 파일, "인용": 인}
            if not 파일:
                적(dict(d, 판정="파일없음", 까닭="원천에 「파일」 칸이 없다"))
                continue
            p = 파일 if os.path.isabs(파일) else os.path.join(회차, 파일)
            if not os.path.exists(p):
                적(dict(d, 판정="파일없음", 까닭="회차 폴더에 그 파일이 없다"))
                continue
            if not str(인 or "").strip():
                if 요구 == "인용":
                    적(dict(d, 판정="인용없음", 까닭="등급 「%s」는 글자 그대로의 인용이 필요하다" % c.get("등급")))
                else:
                    적(dict(d, 판정="파일만", 까닭="등급이 파일만 요구한다"))
                continue
            q = 정규(str(인))
            if q in _정규원천(p):
                적(dict(d, 판정="일치", 까닭=""))
            elif re.sub(r"\s+", "", q) in _빈칸없는원천(p):
                적(dict(d, 판정="일치(빈칸)", 까닭="글자는 같고 빈칸 자리만 다르다"))
            else:
                적(dict(d, 판정="불일치", 까닭="공백 정규화 후에도 원천 글에 없다 — 지어낸 인용 · 다른 파일의 글 · 여러 조각을 이은 인용(「…」)인지 본다"))
    나쁨 = sum(셈.get(k, 0) for k in ("불일치", "파일없음", "인용없음", "원천없음"))
    return {"형식": 대조형식, "회차": 회차, "카드수": len(카드들), "인용수": len(줄), "셈": 셈, "줄": 줄, "통과": 나쁨 == 0}


# ══ 명령 ═══════════════════════════════════════════════════════════════════════════════════════════════
def _대조main(argv):
    ap = argparse.ArgumentParser(prog="공시절.py 대조", description="카드 원천 인용 대조")
    ap.add_argument("카드")
    ap.add_argument("--회차", default=os.path.dirname(여기))
    ap.add_argument("--낼", default=None)
    a = ap.parse_args(argv)
    if not os.path.exists(a.카드):
        print("카드 파일이 없다: %s" % a.카드)
        return 입력오류
    try:
        결 = 인용대조(a.카드, os.path.abspath(a.회차))
    except ValueError as e:
        print("카드 JSON 이 깨졌다 — %s" % e)
        return 입력오류
    print("인용 대조 — 카드 %d장 · 인용 %d건 · %s" % (결["카드수"], 결["인용수"], " · ".join("%s %d" % kv for kv in sorted(결["셈"].items()))))
    for x in 결["줄"]:
        if x["판정"] not in ("일치", "파일만"):
            print("  %s %s[%s] %s — %s" % (x["판정"], x["id"], x["순번"], x["파일"], str(x["인용"] or "")[:60]))
    if a.낼:
        io.open(a.낼, "w", encoding="utf-8").write(json.dumps(결, ensure_ascii=False, indent=1))
        print("→ %s" % a.낼)
    return 통과 if 결["통과"] else 발견


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "대조":
        return _대조main(argv[1:])
    ap = argparse.ArgumentParser(description="공시 「사업의 내용」 · 10-K Item 을 표준 절로 나눈다")
    ap.add_argument("--회차", default=os.path.dirname(여기), help="_raw/ 의 부모 폴더(기본: 이 스크립트 폴더의 부모)")
    ap.add_argument("--파일", action="append", default=None, help="원문을 직접(여러 번)")
    ap.add_argument("--기준일", default=None, help="이 날짜까지 기간이 끝난 보고서만(YYYY-MM-DD)")
    ap.add_argument("--평가기준일", default=None)
    ap.add_argument("--재무기준일", default=None)
    ap.add_argument("--낼", default=None, help="산출 경로(기본 <회차>/_raw/공시절.json)")
    a = ap.parse_args(argv)
    회차 = os.path.abspath(a.회차)
    try:
        문서, rc = 나누기(회차, a.파일, a.기준일, a.평가기준일, a.재무기준일)
    except FileNotFoundError as e:
        print("원문이 없다: %s" % e)
        return 입력오류
    if 문서 is None:
        print("원문이 없다 — %s/_raw 아래 정기보고서 원문(접수번호 14자리 .xml · .txt)도 미국 원문(10K_ · 10Q_)도 없다" % 회차)
        return 입력오류
    낼 = a.낼 or os.path.join(회차, "_raw", "공시절.json")
    os.makedirs(os.path.dirname(os.path.abspath(낼)), exist_ok=True)
    io.open(낼, "w", encoding="utf-8").write(json.dumps(문서, ensure_ascii=False, indent=1))
    for w in 문서["원천"]:
        print("원천 %d %s — %s · %s · 큰 절 %s" % (w["번호"], w["파일"], w["서식"], w["읽은꼴"], len(w.get("큰절") or [])))
    print("절 %d개 · 글 %d자 · 못찾음 %d · 찾아둔 %d" % (문서["요약"]["절수"], 문서["요약"]["글자수"], 문서["요약"]["못찾음"], 문서["요약"]["찾아둔"]))
    for x in 문서["요약"]["글대조"]:
        print("  원천 %d 글 대조 — 문단 %d · 원천에 있음 %d" % (x["원천"], x["문단"], x["원천에있음"]))
    for x in 문서["못찾음"]:
        print("  못찾음 [%s] %s — %s%s" % (x["갈래"], x["이름"], x["까닭"], (" · 글속 %d" % x["글속"]) if x.get("글속") else ""))
    print("→ %s" % 낼)
    return rc


if __name__ == "__main__":
    sys.exit(main())

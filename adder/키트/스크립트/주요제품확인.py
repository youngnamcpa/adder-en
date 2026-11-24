# -*- coding: utf-8 -*-
"""**주요제품확인** — C1 「같은 사업 확인」: 후보 회사의 기준일 전 최신 사업보고서 「주요 제품 및 서비스」 매출 비중을 읽어
대상의 슬롯(부문)에 들어가는 몫을 재고, `peer_후보조립_국내.py --접점` 입력 꼴로 낸다(2026-10-25 FX3-a).

왜 있는가 (C1 다시 돌리기 26곳 · 2026-10-25)
    C1 은 「위험 동종 = 해당 사업 매출이 그 회사 매출의 절반 이상」(사업 순도)을 원문으로 확인한 뒤 `--접점` 으로 다시 돌린다. 그 원문을 받는
    도구가 키트에 없어 네 조가 회차마다 손 스크립트로 사업보고서를 받고 눈으로 비중을 셌다 — 같은 일을 손으로 다시 짜면 판정 잣대가 조용히
    갈린다. 이 도구가 받고(캐시) · 표를 읽고 · 순도를 재고 · 근거(접수번호 · 제품 · 비중)를 남긴다. 회사 · 업종 이름은 규칙에 없다.

**순도는 대상의 슬롯 합으로 잰다**(`설계/0_결정.md` 2026-10-25 C1 다시 돌리기 검토 ④)
    후보 매출 가운데 대상이 가진 사업(슬롯들)에 들어가는 몫의 합이 `--문턱`(기본 0.5) 이상이면 같은 사업(「유」) — 넣는 슬롯은 몫이 가장 큰
    슬롯 하나(한 회사는 한 슬롯에만 — 다른 슬롯은 「무」). 예: 대상 슬롯이 카메라모듈 · 기판이면 카메라 34% + 기판 20% = 54% → 「유」 · 카메라 슬롯.
    한 슬롯씩 따로 재면 두 사업을 함께 하는 직접 경쟁사가 어느 슬롯에서도 절반이 안 돼 빠진다(실측).
    판정 셋 — 「유」(합 ≥ 문턱) · 「무」(표를 읽었고 덮은 몫 ≥ 0.6 인데 합 < 문턱) · 「미확인」(표를 못 읽음 · 덮은 몫이 작음 — 사람이 원문 확인).

**원문 고르기** — 기준일까지 접수된 정기 사업보고서 가운데 가장 늦은 것. `[첨부정정]` · `[첨부추가]` 는 본문이 없어(정정신고 · 첨부만) 뺀다 —
    기재정정 · 원본 가운데 최신(실측: 첨부정정을 고르면 「주요 제품」 절이 없다). 받은 표는 공용 캐시 `~/.dcf캐시/C1/사업확인/<종목>/<접수번호>.json`
    에 남겨 다른 회차가 DART 0 콜로 쓴다(저자 허락 2026-10-18 — C1 전 상장사 캐시와 같은 자리). 슬롯 판정은 대상마다 달라 캐시에 넣지 않는다.

**표 읽기** — 원문 XML 의 「II. 사업의 내용 — 주요 제품」 절 표 가운데 열 이름에 매출 · 비율(비중)이 있는 표(가격 변동표 · 매출실적 기간표는 뺀다).
    한 절에 표가 여럿이면(종속회사 · 사업마다) 금액으로 합쳐 몫을 다시 잰다. 금액 · 비율이 한 칸(「92,751(78.9%)」)이어도 읽는다.
    합계 · 소계 · 연결조정 · 내부거래 줄과 음수 금액은 몫에서 뺀다. XML 이 없고 옛 산출의 「주요제품절」 글만 있으면 글 조각에서 「이름 금액(비율%)」 을
    읽고 `표출처 = 글 조각(약함)` 으로 적는다.

**슬롯과 낱말** — 슬롯은 후보 조립과 같은 이름 · 낱말을 쓴다: `--슬롯 "이름:비중:낱말,낱말"`(peer_후보조립_국내 와 같은 꼴) · 없으면 `--후보`
    (핵심표본_초안.json)의 `슬롯들` · 그것도 없으면 `--선언`(C1_선언.json)의 `슬롯배분`. 제품 줄의 글(부문 · 품목 · 구체적 용도 · 상표)이 슬롯 낱말과
    맞으면(peer_후보조립_국내.키워드맞나 — 낱말 방식) 그 슬롯 몫. 주요제품 표에는 KIND 주요제품과 다른 말이 나와 `--슬롯낱말 "이름=낱말,낱말"` 로 더한다.

산출
    {폴더}/_raw/peers/C1확인/<종목>.json   옛 꼴(종목코드 · 고유번호 · 회사명 · 접수번호 · 보고서 · 주요제품절) + 제품표 · 표출처 · 덮은몫 · 슬롯몫 ·
                                           순도합 · 판정 · 슬롯 · 문턱 · 근거
    {폴더}/_raw/peers/접점_확인.json        `--접점` 입력 — {"종목": {"슬롯": "유", "*": "무"}}(다슬롯) · "유"(한 슬롯) · "무". 미확인은 싣지 않는다.
                                           있던 파일에 덧쓴다(사람이 고친 값은 `--덮어쓰기` 없이는 바꾸지 않는다)
    {폴더}/_raw/peers/접점_확인_근거.json   종목마다 판정 · 슬롯 · 순도합 · 슬롯몫 · 접수번호 · 큰 제품 셋 · 생산모형
    {폴더}/_raw/peers/생산모형.json         (2026-10-25 FX5-P) 종목마다 생산 모형 — 위탁(회사 주어 팹리스 · 생산설비 없음 · 전량 외주 문장, 또는
                                           유형자산 ÷ 매출 < 0.08 이고 생산능력 표 없음 — 약함) · 설비(유형자산 ÷ 매출 ≥ 0.40, 또는 생산능력 · 가동률 표 +
                                           ≥ 0.20 — 약함) · 미확인. `peer_후보조립_국내.py` 가 대상 생산 모형(A3)과 다르면 핵심에서 예비로 내린다.
                                           사람이 적은 값(「출처」: 「사람」)은 `--덮어쓰기` 없이 바꾸지 않는다

사용(회차 폴더에서 — 본체에서 받으면 멈춘다)
    python 스크립트/주요제품확인.py --기준일 2026-06-30 --후보 _raw/peers/핵심표본_초안.json
    python 스크립트/주요제품확인.py --기준일 2026-06-30 --종목 001820,353200 --슬롯 "수동소자:0.46:MLCC,커패시터" --슬롯 "기판:0.2:기판,PCB"
    python 스크립트/주요제품확인.py ... --받지않음          # 캐시 · 받아 둔 원문만(DART 0 콜)
DART 일일 한도(020)면 멈추고 남은 종목을 `_raw/peers/C1확인/_남은받기.json` 에 적는다(rc 3).
"""
from __future__ import annotations

import argparse
import csv
import glob
import io
import json
import os
import re
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")
여기 = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, 여기)

import 공시표 as G                                              # noqa: E402

# ══ 사업 확인 잣대(2026-10-25 FX4-P) — 낱말은 `유사기업_사업확인설정.json`(코드에 회사 · 업종 이름 없음) ══════════════════════
_설정기본 = {"부품꼴": ["부품", "부분품", "구성품", "기자재", "소재", "원료", "원재료", "자재", "장비"], "유형제외": ["부품", "소재", "상품"],
          "사업모형": ["대행", "위탁생산", "수탁", "임가공", "유통"], "일반머리": ["등", "외", "기타", "제품", "류", "사업", "부문"],
          "넓은낱말": [], "슬롯낱말더함": [], "합계겹침문턱": 1.1}
_설 = None


# ══ 생산 모형(2026-10-25 FX5-P — 총괄 결정 ② 사업 모형 일치) ═══════════════════════════════════════════════
#   후보의 생산 모형 = 위탁(팹리스 · 전량 외주 · 생산 설비 없음) | 설비(자체 생산 — 생산능력 · 가동률 표 + 유형자산 몫) | 미확인.
#   재료는 사업보고서 원문 하나(C1 확인이 이미 받는 것) — 「요약재무정보」 표의 유형자산 ÷ 매출 · 「생산능력 · 가동률」 표의 유무 ·
#   **회사 자신을 주어로 한** 위탁 문장(「당사는 … 팹리스」 · 「연결회사는 생산설비가 없는 …」 — 업계 설명 문장 · 사업부 하나의 문장은 세지 않는다).
#   문턱은 `유사기업_사업확인설정.json` 의 「생산모형」 으로 바꾼다.
모형문턱기본 = {"위탁문장유형자산상한": 0.40, "위탁약함유형자산": 0.08, "설비유형자산": 0.40, "설비능력표유형자산": 0.20}
_자기주어 = re.compile(r"(당사|회사|연결\s*회사|지배\s*(기업|회사)|연결\s*실체|당\s*그룹)\s*(는|은|의|가)")
_부분주어 = re.compile(r"(사업\s*부|사업\s*부문|부문)\s*(는|은|의)")
_위탁낱말 = re.compile(r"(팹리스|[Ff]abless)\s*(\(\s*([Ff]abless|팹리스)\s*\))?\s*(전문\s*)?(반도체\s*)?(설계\s*)?(업체|회사|기업|사업자)\s*(로|로서|이며|이고|입니다|이다|임|에\s*해당)"
                     r"|(생산|제조)\s*(시설|설비|공장|라인)\s*(을|를|이|은)?\s*(보유하고\s*있지\s*않|갖추고\s*있지\s*않|소유하고\s*있지\s*않|없)"
                     r"|(전량|모두|전부)\s*(을\s*|를\s*)?(외주|위탁)\s*(생산|제조|가공)|(생산|제조)\s*(을|를|은)?\s*(전량|모두|전부)\s*(외주|위탁)")
_능력표 = re.compile(r"생산\s*능력|가동\s*률|가동\s*율|생산\s*실적")


def 모형문턱():
    return dict(모형문턱기본, **(설정().get("생산모형") or {}))


def 생산모형읽기(xml경로):
    """원문 XML → {"모형": 위탁 | 설비 | 미확인, "유형자산비", "능력표", "위탁문장", "근거"}. 못 읽으면 None."""
    문 = G.읽기(xml경로) if xml경로 else None
    if not 문:
        return None
    문턱x = 모형문턱()
    유형 = 매출 = None
    for 표 in G.찾기(문, r"요약\s*(연결\s*)?재무"):
        for 이름, 칸, _i in G.줄들(표):
            n = G.표준(이름)
            vals = [G.수(c) for c in 칸 if G.수(c) is not None]
            if not vals:
                continue
            if 유형 is None and n.endswith("유형자산") and "사용권" not in n and "투자" not in n:
                유형 = vals[0]
            if 매출 is None and re.match(r"^(매출(액|수익)?|영업수익|수익\(매출액\))$", n):
                매출 = vals[0]
        if 유형 is not None and 매출:
            break
    비 = (유형 / 매출) if (유형 is not None and 매출 and 매출 > 0) else None
    능 = sum(1 for 표 in 문["표"] if _능력표.search(G.맥락(표)) and any(G.수(c) is not None for r in 표["격자"] for c in r))
    위 = []
    for _경, s in 문["글"]:
        m = _위탁낱말.search(s)
        if not m:
            continue
        앞 = s[max(0, m.start() - 80): m.start()]
        if _자기주어.search(앞) and not _부분주어.search(앞[-40:]):
            위.append(s[max(0, m.start() - 60): m.end() + 20].strip())
    강도 = "강함"
    if 위 and (비 is None or 비 < 문턱x["위탁문장유형자산상한"]):
        모형, 까 = "위탁", "회사 주어 위탁 문장%s" % (" · 유형자산 ÷ 매출 %.3f < %.2f" % (비, 문턱x["위탁문장유형자산상한"]) if 비 is not None else "")
    elif 비 is not None and 비 < 문턱x["위탁약함유형자산"] and not 능:
        모형, 까, 강도 = "위탁", "유형자산 ÷ 매출 %.3f < %.2f · 생산능력 · 가동률 표 없음(문장 없이 숫자로 — 약함)" % (비, 문턱x["위탁약함유형자산"]), "약함"
    elif 비 is not None and (비 >= 문턱x["설비유형자산"] or (능 and 비 >= 문턱x["설비능력표유형자산"])) and not 위:
        모형, 까 = "설비", "유형자산 ÷ 매출 %.3f%s" % (비, " · 생산능력 · 가동률 표 %d" % 능 if 능 else "")
        강도 = "강함" if 비 >= 문턱x["설비유형자산"] else "약함"
    else:
        모형, 까, 강도 = "미확인", "유형자산 ÷ 매출 %s · 생산능력 표 %d · 회사 주어 위탁 문장 %d — 문턱으로 가르지 못함" % (
            ("%.3f" % 비) if 비 is not None else "없음", 능, len(위)), None
    return {"모형": 모형, "강도": 강도, "유형자산비": round(비, 4) if 비 is not None else None, "능력표": 능,
            "위탁문장": [x[:160] for x in 위[:2]], "근거": 까, "원문": os.path.basename(xml경로)}


def 설정():
    global _설
    if _설 is None:
        _설 = dict(_설정기본)
        q = os.path.join(여기, "유사기업_사업확인설정.json")
        if os.path.exists(q):
            try:
                _설.update({k: v for k, v in json.load(io.open(q, encoding="utf-8")).items() if not k.startswith("_")})
            except (OSError, ValueError):
                pass
    return _설

_합계 = re.compile(r"(합\s*계|총\s*계|소\s*계|^계$|연결\s*조정|연결\s*제거|내부\s*거래|내부\s*매출|상계\s*제거|조\s*정\s*액)")
_금비 = re.compile(r"([0-9][0-9,]*(?:\.[0-9]+)?)\s*\(\s*([0-9]{1,3}(?:\.[0-9]+)?)\s*%?\s*\)?")


def _합계줄(이름, 글=""):
    """합계 · 소계 · 「○○ 계」 · 총매출 · 계속사업 매출 · 연결조정 · 내부거래 줄 — 몫에서 뺀다(겹셈 · 음수 조정)."""
    s = G.표준(이름 or "")
    낱 = (이름 or "").split()
    if _합계.search(s) or (글 and _합계.search(G.표준(글))):
        return True
    if 낱 and 낱[-1] == "계":
        return True
    return bool(re.search(r"(제품|상품|부문|사업|매출|용역|기타)계$|총매출|매출총계|계속사업매출", s))
_주요절 = re.compile(r"주요\s*제품|주요\s*상품|제품\s*및\s*서비스|제품별|매출\s*유형")


def _키워드맞나():
    """peer_후보조립_국내 의 낱말 일치를 그대로 쓴다(같은 잣대 — 「마트」 ⊄ 「스마트」)."""
    import importlib.util                                       # noqa: PLC0415
    spec = importlib.util.spec_from_file_location("peer_후보조립_국내_확인", os.path.join(여기, "peer_후보조립_국내.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


_후 = None


def 후보도구():
    global _후
    if _후 is None:
        _후 = _키워드맞나()
    return _후


# ══ 슬롯 ══════════════════════════════════════════════════════════════════
def 슬롯들(a, 폴더):
    """[(이름, 비중, [낱말 …])] — `--슬롯` → `--후보` 의 슬롯들 → `--선언` 의 슬롯배분 순. 이름은 「현재사업-」 을 뗀 맨 이름."""
    후 = 후보도구()
    낸 = []
    if a.슬롯:
        for 이름, w, kw in 후.슬롯읽기(a.슬롯):
            낸.append((후.슬롯맨이름(이름), w, [x.strip() for x in kw.split(",") if x.strip()]))
    else:
        for 키, p in (("후보", a.후보), ("선언", a.선언)):
            if not p:
                continue
            p = p if os.path.isabs(p) else os.path.join(폴더, p)
            if not os.path.exists(p):
                continue
            d = json.load(io.open(p, encoding="utf-8"))
            줄 = d.get("슬롯들") if 키 == "후보" else d.get("슬롯배분")
            if not 줄 and 키 == "후보" and d.get("선언", {}).get("경로2키워드"):     # 한 슬롯 초안
                줄 = [{"이름": (d["선언"].get("슬롯") or "단일").split()[0], "비중": 1.0, "경로2키워드": ",".join(d["선언"]["경로2키워드"])}]
            for s in 줄 or []:
                이름 = s.get("이름") or s.get("슬롯") or ""
                kw = s.get("경로2키워드") or ""
                kw = kw if isinstance(kw, list) else [x for x in str(kw).split(",")]
                낸.append((후.슬롯맨이름(이름), float(s.get("비중") or 0) or 1.0, [x.strip() for x in kw if x.strip()]))
            if 낸:
                break
    for x in a.슬롯낱말 or []:
        이름, _, kw = x.partition("=")
        for i, (n, w, k) in enumerate(낸):
            if n == 후.슬롯맨이름(이름.strip()):
                낸[i] = (n, w, k + [y.strip() for y in kw.split(",") if y.strip()])
    # 2026-10-25 FX4-P — 슬롯 이름 · 낱말이 패턴에 맞으면 주요 제품 표에만 나오는 약어 · 업계 말을 더한다(설정 `슬롯낱말더함` — 3-5)
    for 더 in 설정().get("슬롯낱말더함") or []:
        pat = re.compile(더.get("슬롯패턴") or "^$", re.I)
        for i, (n, w, k) in enumerate(낸):
            if pat.search(n) or any(pat.search(x) for x in k):
                낸[i] = (n, w, k + [x for x in 더.get("낱말") or [] if x not in k])
    합 = sum(w for _, w, _ in 낸) or 1.0
    return [(n, w / 합, k) for n, w, k in 낸]


# ══ 표 읽기 ═══════════════════════════════════════════════════════════════
def _칸금비(c):
    """칸 글 → (금액, 비율%) — 「92,751(78.9%)」 · 「151,694( 98.4%)」 · 「21,050」 · 「8.9%」."""
    c = (c or "").strip()
    m = _금비.search(c.replace(" ", ""))
    if m:
        return G.수(m.group(1)), float(m.group(2))
    if c.endswith("%"):
        v = G.수(c)
        return None, v
    return G.수(c), None


def _매출표인가(표):
    """주요 제품 절의 매출 비중 표 — 열 이름에 매출 · 비율 · 비중 · 금액이 있거나, 「주요 제품」 절 표이고 칸이 「금액(비율%)」 꼴이다
    (열 이름이 기간뿐인 꼴 — 실측: 「제품군 · 2025년(제22기) · …」 에 「459,188(99.85%)」). 가격 변동표 · 원재료 · 생산 표는 아니다."""
    열 = [G.표준(x) for x in 표["열이름"]]
    앞 = G.표준(" ".join(표["앞글"][-2:]))
    if re.search(r"가격변동|원재료|매입|생산능력|생산실적|가동률|가동율", 앞):
        return False
    if any(re.search(r"매출|비율|비중|금액", x) for x in 열):
        return not ((표.get("단위") or "") in ("원",) and not any(re.search(r"비율|비중", x) for x in 열))   # 가격표(단위 원)
    경로 = G.표준(" ".join(표["제목경로"][-2:] + 표["앞글"][-3:]))
    if re.search(r"주요제품|제품및서비스|주요상품", 경로):
        return any(_금비.search((c or "").replace(" ", "")) for 행 in 표["격자"][표["머리줄수"]:] for c in 행)
    return False


def 표읽기(xml경로):
    """원문 XML → (제품표 줄 [{"이름", "글", "금액", "비율", "몫"}], 금액 합) · 못 읽으면 ([], None)."""
    문 = G.읽기(xml경로)
    if not 문:
        return [], None
    표들 = [t for t in G.찾기(문, r"주요\s*제품|제품\s*및\s*서비스|주요\s*상품") if _매출표인가(t)
           and any("사업의내용" in G.표준(x) for x in t["제목경로"])]
    if not 표들:
        표들 = [t for t in G.찾기(문, _주요절.pattern) if _매출표인가(t)][:1]
    줄 = []
    for 표 in 표들:
        배 = G.단위배수(표.get("단위")) or 1.0
        j금 = G.열찾기(표, r"매출액|금액")
        if j금 is None:
            j금 = G.열찾기(표, r"매출(?!유형|처)")                    # 「매출유형」 · 「매출처」 열이 아니라
        j비 = G.열찾기(표, r"비율|비중|구성비")
        if j비 is not None and j비 == j금:                          # 「매출액(비율)」 한 머리 — 칸 글이 %면 비율, 아니면 금액
            j비 = None
        # 용도 · 상표 · 고객 열은 제품이 아니다 — 「MLCC · 용도: IT, 전장」 의 「전장」 이 전장 슬롯에 맞아 버렸다(실측 · 다부문 부품사)
        용도열 = set(G.열들찾기(표, r"용도|상표|고객|거래처|비고|적용|수요처"))
        # 2026-10-25 FX4-P — 사업부문 열(부문 이름)과 매출유형 · 품목구분 열(제품 · 상품 · 부품)은 제품 이름 칸과 가른다 — 머리 맞춤은 제품 칸으로만,
        # 유형 칸이 「부품 · 소재 · 상품」 이면 그 줄은 완제품이 아니다(1조 — 품목 구분 「부품」 의 「경승용차 밋션」 이 완성차로 셌다)
        부문열 = set(G.열들찾기(표, r"사업부문|^부문|사업부|^사업$|^세그먼트"))
        유형열 = set(j for j in G.열들찾기(표, r"매출유형|제품유형|품목구분|^구분$|^유형$|매출구분") if j not in 부문열)
        for _i, (_이름, _칸, i) in enumerate(G.줄들(표)):
            행 = 표["격자"][i]
            글 = " ".join(dict.fromkeys(c for c in 행 if c and G.수(c) is None and not _금비.search(c.replace(" ", ""))))
            제품글 = " ".join(dict.fromkeys(c for j, c in enumerate(행) if j not in 용도열 and c and G.수(c) is None
                                           and not _금비.search(c.replace(" ", ""))))
            if not 글 or _합계줄(제품글 or 글, 글):
                continue
            금, 비 = 줄금비(행, j금, j비)
            if 금 is None and 비 is None:
                continue
            if 금 is None and 줄 and 줄[-1]["표"] == 표["번호"] and 줄[-1]["글"] == 글[:200] and 줄[-1].get("비율") is None:
                # 금액 줄 다음에 같은 이름의 비율 줄이 오는 꼴(실측 — 「1,415,814」 줄 · 「50.73%」 줄) — 앞 줄의 비율로 붙인다
                줄[-1]["비율"] = 비
                continue
            칸 = list(dict.fromkeys(c.strip() for j, c in enumerate(행) if j not in (용도열 | 부문열 | 유형열) and c and G.수(c) is None
                                    and not _금비.search(c.replace(" ", ""))))
            부문칸 = list(dict.fromkeys(c.strip() for j, c in enumerate(행) if j in 부문열 and c and G.수(c) is None))
            유형글 = " ".join(dict.fromkeys(c.strip() for j, c in enumerate(행) if j in 유형열 and c and G.수(c) is None))
            줄.append({"이름": (제품글 or 글)[:80], "글": 글[:200], "제품글": (제품글 or 글)[:200],
                      "금액": (금 * 배) if 금 is not None else None, "비율": 비, "표": 표["번호"],
                      "칸": [c[:120] for c in 칸], "부문칸": [c[:80] for c in 부문칸], "유형글": 유형글[:60]})
    return 몫매기기(줄)


def 줄금비(행, j금, j비):
    """한 줄 → (금액, 비율%). 차례: ① 「금액(비율%)」 한 칸(첫 칸 — 기간 열이면 당기) ② 금액 열 · 비율 열(머리가 한 칸 「매출액(비율)」 이면
    칸 글이 % 로 끝나면 비율, 아니면 금액) ③ 비율이 100 을 넘으면 금액으로 본다(머리와 칸이 어긋난 꼴)."""
    for c in 행:
        m = _금비.search((c or "").replace(" ", ""))
        if m:
            return G.수(m.group(1)), float(m.group(2))
    금, 비 = None, None
    for j in [x for x in (j금, j비) if x is not None and x < len(행)]:
        c = (행[j] or "").strip()
        v = G.수(c)
        if v is None:
            continue
        if c.endswith("%"):
            비 = v if 비 is None else 비
        elif j == j금 and 금 is None:
            금 = v
        elif 비 is None:
            비 = v
    if 금 is None and 비 is None and j금 is None and j비 is None:      # 머리에 매출 · 비율이 없는 기간 열 표 — 첫 수 칸
        수칸 = [c for c in 행 if c and G.수(c) is not None]
        if 수칸:
            c = 수칸[0].strip()
            if c.endswith("%"):
                비 = G.수(c)
            else:
                금 = G.수(c)
    if 비 is not None and 비 > 100.5:
        금, 비 = (금 if 금 is not None else 비), None
    return 금, 비


def 몫매기기(줄):
    """금액이 다 있으면 금액으로(표가 여럿이어도 한 분모), 아니면 비율로 몫(0~1)을 단다. 음수 금액 줄은 뺀다."""
    줄 = [r for r in 줄 if r.get("금액") is None or r["금액"] >= 0]
    if not 줄:
        return [], None
    if all(r.get("금액") is not None for r in 줄):
        합 = sum(r["금액"] for r in 줄)
        for r in 줄:
            r["몫"] = (r["금액"] / 합) if 합 else None
        return 줄, 합
    표수 = len({r.get("표") for r in 줄})
    for r in 줄:
        r["몫"] = (r["비율"] / 100.0) if r.get("비율") is not None else None
    if 표수 > 1:                                                 # 비율만 있는 표가 여럿 — 표마다 100% 라 합치면 부풀다 — 첫 표만
        첫 = 줄[0].get("표")
        줄 = [r for r in 줄 if r.get("표") == 첫]
    return 줄, None


def 글조각읽기(글):
    """옛 산출의 「주요제품절」 글 → 제품 줄(약함 — `약함: True`). 「이름 금액(비율%)」 · 「이름 금액 비율%」 꼴만.
    가격 변동 · 원재료 절 앞에서 끊고, 합계 줄을 만나면 그 표를 끝으로 본다. 비율 합이 100% 를 넘으면(요약표 · 본표가 겹침) 합으로 나눈다."""
    글 = re.split(r"가격\s*변동|원재료|\(2\)\s|2\)\s*주요|나\.\s*주요\s*제품", 글 or "", maxsplit=1)[0]
    줄 = []
    pat = re.compile(r"(\(?-?[0-9][0-9,]{1,}\)?)\s*\(?\s*(-?[0-9]{1,3}(?:\.[0-9]+)?)\s*%\s*\)?")
    끝 = 0
    for m in pat.finditer(글):
        앞 = 글[끝:m.start()]
        끝 = m.end()
        이름 = re.sub(r"\s+", " ", re.sub(r"[0-9][0-9,]*(\.[0-9]+)?", " ", 앞)).strip(" -·,")[-80:]
        if not 이름:
            continue
        if _합계줄(이름[-12:]):
            if 줄:
                break                                            # 첫 표의 합계 — 그 뒤는 다른 표(요약 · 지역별 등)
            continue
        금 = G.수(m.group(1))
        비 = float(m.group(2))
        if (금 is not None and 금 < 0) or 비 < 0:
            continue                                            # 내부거래 제거 · 조정
        줄.append({"이름": 이름[-40:], "글": 이름, "제품글": 이름, "금액": 금, "비율": 비, "표": 0, "약함": True})
    if not 줄:
        return [], None
    합 = sum(r["비율"] for r in 줄)
    for r in 줄:
        r["몫"] = (r["비율"] / 합) if 합 > 100.5 else r["비율"] / 100.0
    return 줄, None


# ══ 순도 ══════════════════════════════════════════════════════════════════
def 제품낱말맞음(글, 낱말들):
    """주요 제품 표의 낱말 일치 — 후보 조립과 같은 잣대(`키워드맞나` — 같거나 앞머리 · 세 글자 이상은 안쪽) 위에, **두 글자 낱말은 네 글자 이상
    합성어의 끝**에도 맞춘다(한국어 합성어는 머리가 끝 — 「반도체패키지기판」 은 「기판」, 「인쇄회로기판」 도). 세 글자 낱말(「스마트」)의 끝은
    보지 않아 「마트」 ⊄ 「스마트」 는 그대로다. 대소문자는 가리지 않는다(영문 약어)."""
    후 = 후보도구()
    맞 = []
    낱 = [w.lower() for w in 후.낱말들(글 or "")]
    for k in 낱말들:
        kl = (k or "").lower()
        if not kl:
            continue
        if 후.키워드맞나((글 or "").lower(), [kl]) or (len(kl) == 2 and any(len(w) >= 4 and w.endswith(kl) for w in 낱)):
            맞.append(k)
    return 맞


def _항목들(글):
    """제품 칸 글 → 항목들 — 괄호 속을 지우고 쉼표 · 가운뎃점 · 빗금 · 「및 · 와 · 과」 로 나눈다."""
    t = re.sub(r"\([^)]*\)|\[[^\]]*\]|<[^>]*>", " ", 글 or "")
    return [x.strip() for x in re.split(r"[,·/;\n]|\s및\s|\s와\s|\s과\s", t) if x.strip()]


def _머리(항목):
    """항목의 머리 — 마지막 낱말(일반 머리 낱말은 건너뛴다 — 「카메라모듈 사업」 의 머리는 카메라모듈). 한국어 명사구는 끝이 머리다."""
    일반 = set(설정().get("일반머리") or [])
    토 = 항목.split()
    while len(토) > 1 and 토[-1] in 일반:
        토.pop()
    return 토[-1] if 토 else ""


def _제외낱말(목록, 슬롯이름, kw):
    """설정 목록 가운데 이 슬롯의 이름 · 낱말에 들어 있지 않은 것(부품 회사가 대상이면 「부품」 은 제외 낱말이 아니다)."""
    슬 = " ".join([슬롯이름 or ""] + list(kw or [])).lower()
    return [w for w in 목록 or [] if w and w.lower() not in 슬]


def 머리맞음(칸들, 슬롯이름, kw):
    """제품 칸들 · 슬롯 → (맞은 낱말 [..], 제외 까닭 | None, 수식만 [..]).

    2026-10-25 FX4-P — 슬롯 낱말이 **제품의 머리**(항목의 마지막 낱말)에 맞아야 그 슬롯 제품이다. 앞 낱말에만 맞으면 수식어다
    (「선박용 크레인」 · 「경승용차 밋션」 · 「카메라모듈에 탑재되는 부품」 — C2 다시 셈 1조 · 2조 · 3-5). 머리가 맞아도
    ① 머리가 부품꼴 낱말로 끝나면(「선박구성부분품」 · 「조선기자재」 · 「건축내외장재」) 부품 · 공급 줄로 빼고(제외 까닭)
    ② 넓은 낱말이 합성어 앞머리로만 맞고 뒤가 슬롯 낱말이 아니면(「광학필름」) ③ 한 낱말 「…용」 이면 수식어로 본다."""
    설 = 설정()
    부품 = _제외낱말(설.get("부품꼴"), 슬롯이름, kw)
    넓은 = set(설.get("넓은낱말") or [])
    맞, 수식, 제외 = [], [], None
    for 칸 in 칸들 or []:
        for 항목 in _항목들(칸):
            머 = _머리(항목)
            for k in kw or []:
                if not k:
                    continue
                if 제품낱말맞음(머, [k]):
                    kl, ml = k.lower(), 머.lower()
                    끝 = next((w for w in 부품 if ml.endswith(w.lower()) and ml != kl and not kl.endswith(w.lower())), None)
                    if 끝:
                        제외 = "머리 「%s」 가 「%s」 로 끝남 — 부품 · 공급 줄" % (머, 끝)
                        continue
                    if k in 넓은 and ml.startswith(kl) and ml != kl:
                        뒤 = 머[len(k):]
                        if not any(제품낱말맞음(뒤, [x]) for x in (kw or []) if x and x != k):
                            수식.append("%s(넓은 낱말 「%s」 가 합성어 앞머리로만)" % (머, k))
                            continue
                    if 머.endswith("용") and len(항목.split()) == 1 and ml != kl:
                        수식.append("%s(「…용」)" % 머)
                        continue
                    맞.append(k)
                elif 제품낱말맞음(항목, [k]):
                    수식.append("%s(머리 「%s」 — 「%s」 는 수식어)" % (항목[:40], 머, k))
    return list(dict.fromkeys(맞)), 제외, 수식


def 순도(줄, 슬롯, 문턱=0.5):
    """제품 줄 · 슬롯 → {"슬롯몫", "순도합", "덮은몫", "제외몫", "판정", "슬롯", "큰제품", "유근거줄"}. 한 줄은 낱말이 가장 많이 맞은 슬롯 하나에만.

    2026-10-25 FX4-P — 맞춤은 제품 칸(사업부문 · 매출유형 · 용도 열을 뺀 칸)의 **머리**로만 하고(`머리맞음`), 유형 칸이 「부품 · 소재 · 상품」 이거나
    줄 글에 사업모형 낱말(대행 · 위탁생산 · 유통 …)이 있거나 머리가 부품꼴이면 그 줄의 몫은 `제외몫` 으로 — 순도에서 뺀다. 슬롯 합이 문턱 밑인데
    제외 몫을 더하면 문턱을 넘으면 「미확인(사업 모형)」 — 사람이 원문으로 가른다(4-1). 제품 칸에서 하나도 안 맞으면 부문 칸으로 한 번 더 본다.
    합계 줄이 겹쳐 덮은 몫이 `합계겹침문턱`(110%) 을 넘으면 몫을 합으로 나눈다(3-5)."""
    설 = 설정()
    몫 = {n: 0.0 for n, _, _ in 슬롯}
    제외몫 = {n: 0.0 for n, _, _ in 슬롯}
    덮은 = 0.0
    맞은줄 = 0
    유근거 = []
    덮은합 = sum(r.get("몫") or 0.0 for r in 줄)
    배 = (1.0 / 덮은합) if 덮은합 > float(설.get("합계겹침문턱") or 1.1) else 1.0
    낱말표 = {n: kw for n, _, kw in 슬롯}
    for r in 줄:
        v = r.get("몫")
        if v is None:
            continue
        v = v * 배
        덮은 += v
        칸들 = r.get("칸") or [r.get("제품글") or r.get("글") or r.get("이름") or ""]
        best, bm, b제외 = None, 0, None
        for 단 in (칸들, r.get("부문칸") or []):                # 제품 칸 → (하나도 안 맞으면) 부문 칸
            for n, _, kw in 슬롯:
                if not kw:
                    continue
                맞, 제, _수 = 머리맞음(단, n, kw)
                if len(맞) > bm:
                    best, bm, b제외 = n, len(맞), None
                elif not 맞 and 제 and best is None:
                    best, b제외 = n, 제
            if bm:
                break
        if best and bm:
            유형 = r.get("유형글") or ""
            유제 = [w for w in _제외낱말(설.get("유형제외"), best, 낱말표.get(best)) if w in 유형.split()]
            글 = (r.get("글") or "").lower().replace(" ", "")
            모형 = [w for w in _제외낱말(설.get("사업모형"), best, 낱말표.get(best)) if w.lower() in 글]
            if 유제:
                b제외 = "유형 칸 「%s」 — 완제품 아님" % " · ".join(유제)
            elif 모형:
                b제외 = "사업 모형 낱말 「%s」 — 대행 · 위탁 · 유통" % " · ".join(모형)
        r["슬롯"] = best if (best and bm and not b제외) else None
        r["제외"] = b제외 if best else None
        if best and b제외:
            제외몫[best] += v
        elif best and bm:
            몫[best] += v
            맞은줄 += 1
            유근거.append((v, best, r.get("이름") or ""))
    합 = sum(몫.values())
    제합 = sum(제외몫.values())
    약함 = bool(줄) and all(r.get("약함") for r in 줄)
    if not 줄:
        판, 까 = "미확인", "주요 제품 표를 못 읽음 — 사람이 원문 확인"
    elif 합 >= 문턱:
        판, 까 = "유", "대상 슬롯 합 %.1f%% ≥ %.0f%%%s" % (합 * 100, 문턱 * 100, " · 글 조각(약함)" if 약함 else "")
    elif 제합 and 합 + 제합 >= 문턱:
        판, 까 = "미확인", ("사업 모형 · 부품 꼴 줄 제외 — 슬롯 합 %.1f%% · 제외 몫 %.1f%%(%s) — 더하면 문턱을 넘는다. 완제품 · 같은 사업 모형인지 "
                          "사람이 원문으로 가른다" % (합 * 100, 제합 * 100, " / ".join(sorted({r["제외"] for r in 줄 if r.get("제외")}))[:160]))
    elif 맞은줄 == 0:
        # 슬롯 낱말이 한 줄도 안 맞으면 「다른 사업」 인지 「낱말이 모자란지」 가를 수 없다 — 「무」 로 자르지 않는다(실측: 액추에이터를
        # 「AFA · OIS」 약어로만 적은 회사가 카메라 슬롯에서 0% 로 「무」 가 될 뻔했다)
        판, 까 = "미확인", "슬롯 낱말이 제품 줄 머리에 한 줄도 안 맞음 — 다른 사업이거나 낱말이 모자람(`--슬롯낱말` 로 더하거나 사람이 원문 확인)"
    elif 약함:
        판, 까 = "미확인", "글 조각(약함)으로는 「무」 로 자르지 않음 — 슬롯 합 %.1f%%(사람이 원문 확인)" % (합 * 100)
    elif 덮은 >= 0.6:
        판, 까 = "무", "대상 슬롯 합 %.1f%% < %.0f%%(표가 매출의 %.0f%% 를 덮음)" % (합 * 100, 문턱 * 100, 덮은 * 100)
    else:
        판, 까 = "미확인", "표가 매출의 %.0f%% 만 덮음 — 슬롯 합 %.1f%%(사람이 원문 확인)" % (덮은 * 100, 합 * 100)
    if 배 != 1.0:
        까 += " · 합계 줄 겹침 의심(덮음 %.0f%% → 합으로 나눔)" % (덮은합 * 100)
    슬 = max(몫, key=lambda n: 몫[n]) if 판 == "유" else None
    큰 = sorted([r for r in 줄 if r.get("몫") is not None], key=lambda r: -r["몫"])[:3]
    return {"슬롯몫": {n: round(v, 4) for n, v in 몫.items()}, "순도합": round(합, 4), "덮은몫": round(덮은, 4),
            "제외몫": {n: round(v, 4) for n, v in 제외몫.items() if v}, "판정": 판, "판정까닭": 까, "슬롯": 슬,
            "큰제품": ["%s %.1f%%%s" % (r["이름"][:30], r["몫"] * 100, (" → " + r["슬롯"]) if r.get("슬롯") else
                                    ((" ✕ " + r["제외"][:30]) if r.get("제외") else "")) for r in 큰],
            "유근거줄": ["%s %.1f%% → %s" % (nm[:40], v * 100, n) for v, n, nm in sorted(유근거, reverse=True)[:3]]}


# ══ 받기 · 캐시 ═══════════════════════════════════════════════════════════
def 공용사업확인():
    d = os.environ.get("DCF_공용캐시") or os.environ.get("DCF_SHARED_CACHE") or os.path.join(os.path.expanduser("~"), ".dcf캐시")
    return os.path.join(d, "C1", "사업확인")


def 보고서고르기(목록, 기준일):
    """list.json 목록 → 기준일까지 접수된 정기 사업보고서 가운데 가장 늦은 것(첨부정정 · 첨부추가 뺌). 없으면 None."""
    기 = 기준일.replace("-", "")
    후 = [x for x in 목록 or [] if "사업보고서" in (x.get("report_nm") or "") and not re.search(r"\[첨부(정정|추가)\]", x.get("report_nm") or "")
         and (x.get("rcept_dt") or "") <= 기]
    if not 후:
        return None

    def 기간(x):
        m = re.search(r"\((\d{4})\.(\d{2})\)", x.get("report_nm") or "")
        return (m.group(1) + m.group(2)) if m else ""
    후.sort(key=lambda x: (기간(x), x.get("rcept_dt") or "", x.get("rcept_no") or ""))
    return 후[-1]


def 캐시읽기(종목, 기준일):
    """공용 캐시 — 기준일까지 접수 · 기준일 15개월 안의 가장 늦은 것."""
    d = os.path.join(공용사업확인(), 종목)
    기 = 기준일.replace("-", "")
    월 = int(기[:4]) * 12 + int(기[4:6]) - 1 - 15                 # 기준일 15개월 전(사업보고서는 해마다 바뀐다)
    하한 = "%04d%02d%s" % (월 // 12, 월 % 12 + 1, 기[6:])
    best = None
    for p in glob.glob(os.path.join(d, "*.json")):
        try:
            x = json.load(io.open(p, encoding="utf-8"))
        except (OSError, ValueError):
            continue
        dt = (x.get("제출일") or x.get("접수번호", "")[:8] or "")
        if dt <= 기 and dt >= 하한 and (best is None or dt > (best.get("제출일") or best.get("접수번호", "")[:8])):
            best = x
    return best


def 캐시쓰기(것):
    if not 것.get("접수번호") or not 것.get("제품표"):
        return
    d = os.path.join(공용사업확인(), 것["종목코드"])
    os.makedirs(d, exist_ok=True)
    keep = {k: 것.get(k) for k in ("종목코드", "고유번호", "회사명", "접수번호", "보고서", "제출일", "제품표", "표출처", "덮은몫", "금액합")}
    json.dump(keep, io.open(os.path.join(d, 것["접수번호"] + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def 고유번호들(폴더, 종목들):
    """종목 → 고유번호 — 상장명부(회차 · 공용) → 싼 층 → corpCode(dart_fetch)."""
    후 = 후보도구()
    낸 = {}
    for 조각 in (("_dartcache", "상장명부_KIND.csv"), ("상장사_주요계정_2025.csv",)):
        p, _w = 후._캐시경로(폴더, *조각)
        표 = 후._표(p) or {}
        for c in 종목들:
            g = (표.get(c) or {}).get("고유번호")
            if g and c not in 낸:
                낸[c] = ("%s" % g).zfill(8)
    return 낸


def 받기(폴더, 종목, 고유, 기준일, D):
    """사업보고서 원문을 받아 XML 경로 · 고른 보고서를 낸다. D = dart_fetch(RAW · CACHE 를 회차로 돌린 것)."""
    기 = 기준일.replace("-", "")
    시작 = "%04d%s" % (int(기[:4]) - 2, 기[4:])
    r = D._get("list.json", corp_code=고유, bgn_de=시작, end_de=기, pblntf_ty="A", page_count=100)
    j = r.json()
    if j.get("status") == "020":
        raise D.한도초과("list.json — 일일 한도(020)")
    고른 = 보고서고르기(j.get("list") or [], 기준일)
    if not 고른:
        return None, None
    파일 = D.원문(고른["rcept_no"], os.path.join("peers", "C1확인", "원문_" + 종목)) or []
    xml = [f for f in 파일 if str(f).lower().endswith(".xml") and re.search(r"[\\/]\d{14}\.xml$", str(f))]
    return (xml[0] if xml else None), 고른


def 한종목(폴더, 종목, 기준일, 슬롯, a, D=None, 고유=None):
    낼곳 = os.path.join(폴더, "_raw", "peers", "C1확인")
    os.makedirs(낼곳, exist_ok=True)
    p = os.path.join(낼곳, 종목 + ".json")
    옛 = json.load(io.open(p, encoding="utf-8")) if os.path.exists(p) else {}
    것 = dict(옛)
    것.update({"종목코드": 종목, "도구": "주요제품확인.py", "기준일": 기준일})
    줄, 금합, 출처 = None, None, None
    if 옛.get("제품표") and 옛.get("기준일") == 기준일 and not a.다시:
        줄, 출처 = 옛["제품표"], 옛.get("표출처")
    if 줄 is None and not a.다시:
        c = 캐시읽기(종목, 기준일)
        if c:
            줄, 출처 = c["제품표"], (c.get("표출처") or "") + " · 공용 캐시"
            for k in ("고유번호", "회사명", "접수번호", "보고서", "제출일", "금액합"):
                if c.get(k):
                    것[k] = c[k]
    if 줄 is None and (not a.다시 or a.받지않음):                     # 받아 둔 원문(옛 회차 · 손 스크립트) — 받지 않으면 --다시 여도 읽는다
        xs = sorted(glob.glob(os.path.join(낼곳, "원문_" + 종목, "*.xml")))
        xs = [x for x in xs if re.search(r"[\\/]\d{14}\.xml$", x)]
        if xs:
            줄, 금합 = 표읽기(xs[-1])
            출처 = "XML 표(받아 둔 원문)"
            것.setdefault("접수번호", os.path.basename(xs[-1])[:14])
    if 줄 is None and not a.받지않음 and D is not None:
        g = (고유 or {}).get(종목) or 것.get("고유번호")
        if not g:
            것["판정"], 것["판정까닭"] = "미확인", "고유번호를 못 풂"
        else:
            xml, 고른 = 받기(폴더, 종목, g, 기준일, D)
            것["고유번호"] = g
            if 고른:
                것.update({"회사명": 고른.get("corp_name"), "접수번호": 고른["rcept_no"], "보고서": 고른.get("report_nm"),
                         "제출일": 고른.get("rcept_dt")})
            if xml:
                줄, 금합 = 표읽기(xml)
                출처 = "XML 표"
                txt = re.sub(r"\.xml$", ".txt", xml)
                if os.path.exists(txt) and not 것.get("주요제품절"):
                    t = io.open(txt, encoding="utf-8", errors="ignore").read()
                    m = re.search(r"주요\s*제품\s*(등의\s*현황|및\s*서비스)", t)
                    if m:
                        것["주요제품절"] = re.sub(r"\s+", " ", t[m.start(): m.start() + 2600]).strip()
            elif 고른 is None:
                것["판정까닭"] = "기준일 전 사업보고서 없음"
    if not 줄 and 옛.get("주요제품절"):                            # 마지막 — 옛 산출의 글 조각
        줄, 금합 = 글조각읽기(옛["주요제품절"])
        출처 = "글 조각(약함 — 표 아님)" if 줄 else 출처
    줄 = 줄 or []
    것["제품표"], 것["표출처"] = 줄, 출처
    if 금합:
        것["금액합"] = 금합
    순 = 순도(줄, 슬롯, a.문턱)
    것.update(순)
    것["문턱"] = a.문턱
    if not 것.get("판정까닭") or 순["판정"] != "미확인" or 줄:
        것["판정까닭"] = 순["판정까닭"]
    # 2026-10-25 FX5-P — 생산 모형(위탁 · 설비 · 미확인) — 받아 둔 원문 XML 에서(같은 원문을 다시 읽지 않는다)
    xs = [x for x in sorted(glob.glob(os.path.join(낼곳, "원문_" + 종목, "*.xml"))) if re.match(r"^\d{14}\.xml$", os.path.basename(x))]
    if xs and (not 것.get("생산모형") or a.다시 or (것.get("생산모형") or {}).get("원문") != os.path.basename(xs[-1])):
        try:
            것["생산모형"] = 생산모형읽기(xs[-1]) or {"모형": "미확인", "근거": "원문을 읽지 못함"}
        except Exception as e:                                   # noqa: BLE001
            것["생산모형"] = {"모형": "미확인", "근거": "원문 읽기 오류(%s)" % type(e).__name__}
    elif not xs and not 것.get("생산모형"):
        것["생산모형"] = {"모형": "미확인", "근거": "받아 둔 원문 없음(공용 캐시의 제품표만)"}
    것["근거"] = "%s %s · %s · 큰 제품 %s%s" % (것.get("보고서") or "사업보고서", 것.get("접수번호") or "(접수번호 없음)", 출처 or "표 없음",
                                            " / ".join(순["큰제품"]) or "-",
                                            (" · 「유」 근거 줄 " + " / ".join(순.get("유근거줄") or [])) if 순.get("판정") == "유" else "")
    json.dump(것, io.open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    if 출처 and "XML" in 출처 and "캐시" not in 출처:
        캐시쓰기(것)
    return 것


def 접점꼴(판정, 슬롯이름, 슬롯수, 약함=False):
    """판정 → `--접점` 값. 글 조각(약함)에서 나온 판정은 싣지 않는다(근거에만 — 용도 칸과 제품 칸을 못 갈라 슬롯이 틀릴 수 있다)."""
    if 약함:
        return None
    if 판정 == "유":
        return {슬롯이름: "유", "*": "무"} if 슬롯수 > 1 else "유"
    if 판정 == "무":
        return "무"
    return None


def 종목고르기(a, 폴더):
    if a.종목:
        return [c.strip().zfill(6) for c in a.종목.split(",") if c.strip()]
    낸 = []
    p = a.후보 if (not a.후보 or os.path.isabs(a.후보)) else os.path.join(폴더, a.후보)
    if p and os.path.exists(p):
        d = json.load(io.open(p, encoding="utf-8"))
        for x in d.get("접점확인대상") or []:
            낸.append(x.get("종목코드"))
        for 묶 in ("핵심", "예비", "내린후보"):
            for r in d.get(묶) or []:
                if r.get("종목코드") and r.get("사업접점") != "유" and r.get("시장") != "US":
                    낸.append(r["종목코드"])
        # 2026-10-25 FX4-P — 판단대장의 「뺌」 가운데 까닭이 순도 · 접점 · 사업인 회사도 다시 본다(순도 잣대가 슬롯 합으로 바뀌면 들어올 수 있다 —
        # C2 다시 셈 3-7: 대상 슬롯 합으로 54% 인 직접 경쟁사가 한 슬롯씩 잰 순도로 뺌 대장에 있었다)
        for x in d.get("판단대장") or []:
            if x.get("판단") == "뺌" and str(x.get("종목코드") or "").isdigit() and re.search(r"순도|접점|사업|같은\s*사업", str(x.get("까닭") or "")):
                낸.append(str(x["종목코드"]))
    return [c.zfill(6) for c in dict.fromkeys(x for x in 낸 if x)]


def main():
    ap = argparse.ArgumentParser(description="C1 같은 사업 확인 — 사업보고서 주요 제품 매출 · 대상 슬롯 합 순도 → --접점 입력", allow_abbrev=False)
    ap.add_argument("--폴더", default=None, help="회차 키트 폴더(기본 스크립트의 부모)")
    ap.add_argument("--기준일", required=True)
    ap.add_argument("--종목", default="", help="종목코드(쉼표). 없으면 --후보 의 접점확인대상 · 미확인 핵심 · 예비 · 내린 후보")
    ap.add_argument("--후보", default="", help="핵심표본_초안.json(종목 · 슬롯들을 읽는다)")
    ap.add_argument("--선언", default="", help="C1_선언.json(슬롯배분 — --슬롯 · --후보 슬롯들이 없을 때)")
    ap.add_argument("--슬롯", action="append", default=[], metavar="이름:비중:낱말", help="peer_후보조립_국내 --슬롯 과 같은 꼴(여럿)")
    ap.add_argument("--슬롯낱말", action="append", default=[], metavar="이름=낱말,낱말", help="주요 제품 표에만 나오는 말을 슬롯에 더한다")
    ap.add_argument("--문턱", type=float, default=0.5, help="대상 슬롯 합 순도 문턱(기본 0.5 — 매출 절반)")
    ap.add_argument("--다시", action="store_true", help="캐시 · 받아 둔 원문을 쓰지 않고 다시 받는다")
    ap.add_argument("--받지않음", action="store_true", help="DART 를 부르지 않는다(캐시 · 받아 둔 원문 · 옛 글만)")
    ap.add_argument("--덮어쓰기", action="store_true", help="접점_확인.json 에 이미 있는 값(사람이 고친 것)도 바꾼다")
    a = ap.parse_args()
    폴더 = os.path.abspath(a.폴더 or os.path.dirname(여기))
    슬롯 = 슬롯들(a, 폴더)
    if not 슬롯:
        raise SystemExit("슬롯이 없습니다 — --슬롯 「이름:비중:낱말」 · --후보(슬롯들) · --선언(슬롯배분) 가운데 하나를 주십시오")
    종목들 = 종목고르기(a, 폴더)
    if not 종목들:
        print("확인할 종목이 없습니다")
        return 0
    import 본체가드                                              # noqa: PLC0415
    본체가드.본체면멈춘다(폴더)                                     # 받든 안 받든 회차 _raw 에 쓴다 — 본체(정본)에 쓰지 않게
    D = None
    if not a.받지않음:
        import dart_fetch as D                                   # noqa: PLC0415
        D.RAW, D.CACHE = os.path.join(폴더, "_raw"), os.path.join(폴더, "_dartcache")
        D._준비()
    고유 = 고유번호들(폴더, 종목들)
    빠진 = [c for c in 종목들 if c not in 고유]
    if 빠진 and D is not None:
        고유.update(D.고유번호풀기(빠진, D.CACHE))
    결과, 남은 = {}, []
    for i, c in enumerate(종목들):
        try:
            결과[c] = 한종목(폴더, c, a.기준일, 슬롯, a, D, 고유)
        except Exception as e:                                   # noqa: BLE001
            if D is not None and isinstance(e, D.한도초과):
                남은 = 종목들[i:]
                print("일일 한도(020) — 멈춤 · 남은 %d" % len(남은))
                break
            raise
    낼 = os.path.join(폴더, "_raw", "peers")
    jp = os.path.join(낼, "접점_확인.json")
    접 = json.load(io.open(jp, encoding="utf-8")) if os.path.exists(jp) else {}
    근p = os.path.join(낼, "접점_확인_근거.json")
    근 = json.load(io.open(근p, encoding="utf-8")) if os.path.exists(근p) else {}
    # 2026-10-25 FX4-P — 값마다 출처(도구 | 사람)를 곁 파일 `접점_확인_출처.json` 에 적는다(파일 꼴은 그대로 — 4-2). 있던 값이 지난 도구값과
    # 다르면 사람이 고친 것이다. 「미확인」 · 빈 값은 사람 판단이 아니므로 도구가 덮는다(3-6)
    출p = os.path.join(낼, "접점_확인_출처.json")
    출 = json.load(io.open(출p, encoding="utf-8")) if os.path.exists(출p) else {}

    def 사람값인가(c):
        v0 = 접.get(c)
        if v0 is None or v0 == "미확인" or (isinstance(v0, dict) and not any(x in ("유", "무") for x in v0.values())):
            return False
        if (출.get(c) or {}).get("출처") == "사람":
            return True
        return 근.get(c, {}).get("도구값") != v0
    for c, x in 결과.items():
        v = 접점꼴(x["판정"], x.get("슬롯"), len(슬롯), "글 조각" in (x.get("표출처") or ""))
        사람 = c in 접 and 사람값인가(c)
        if c in 접 and 사람 and (출.get(c) or {}).get("출처") != "사람":
            출[c] = {"출처": "사람", "값": 접[c], "때": time.strftime("%Y-%m-%d %H:%M"), "근거": "지난 도구값과 다름 — 사람이 고친 값으로 본다"}
        if v is not None and (c not in 접 or a.덮어쓰기 or not 사람):
            접[c] = v
            출[c] = {"출처": "도구", "값": v, "때": time.strftime("%Y-%m-%d %H:%M")}
        근[c] = {"회사명": x.get("회사명"), "판정": x["판정"], "판정까닭": x.get("판정까닭"), "슬롯": x.get("슬롯"), "순도합": x.get("순도합"),
                "슬롯몫": x.get("슬롯몫"), "덮은몫": x.get("덮은몫"), "접수번호": x.get("접수번호"), "보고서": x.get("보고서"),
                "표출처": x.get("표출처"), "큰제품": x.get("큰제품"), "유근거줄": x.get("유근거줄"), "제외몫": x.get("제외몫"),
                "도구값": v, "기준일": a.기준일, "문턱": a.문턱, "생산모형": x.get("생산모형"),
                "때": time.strftime("%Y-%m-%d %H:%M")}
    # 2026-10-25 FX5-P — 생산 모형 모음 `_raw/peers/생산모형.json`(peer_후보조립_국내 가 읽는다) — 사람이 적은 값(「출처」: 「사람」)은 덮지 않는다
    mp = os.path.join(낼, "생산모형.json")
    모 = json.load(io.open(mp, encoding="utf-8")) if os.path.exists(mp) else {}
    for c, x in 결과.items():
        if (모.get(c) or {}).get("출처") == "사람" and not a.덮어쓰기:
            continue
        if x.get("생산모형"):
            모[c] = dict(x["생산모형"], 회사명=x.get("회사명"), 출처="도구", 때=time.strftime("%Y-%m-%d %H:%M"))
    json.dump(모, io.open(mp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(접, io.open(jp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(근, io.open(근p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(출, io.open(출p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    if 남은:
        json.dump({"기준일": a.기준일, "남은": 남은}, io.open(os.path.join(낼, "C1확인", "_남은받기.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
    for c, x in 결과.items():
        print("%s %-14s %-4s 합 %5.1f%% 덮음 %5.1f%% 슬롯 %-10s %s" % (c, (x.get("회사명") or "")[:14], x["판정"], (x.get("순도합") or 0) * 100,
                                                            (x.get("덮은몫") or 0) * 100, x.get("슬롯") or "-", x.get("표출처") or "-"))
        if x["판정"] == "유" and x.get("유근거줄"):
            print("       근거 줄: " + " / ".join(x["유근거줄"]))
        elif x.get("제외몫"):
            print("       제외 몫: " + " · ".join("%s %.1f%%" % (n, v * 100) for n, v in x["제외몫"].items()) + " — " + (x.get("판정까닭") or "")[:120])
        if x.get("생산모형"):
            print("       생산 모형: %s — %s" % (x["생산모형"].get("모형"), (x["생산모형"].get("근거") or "")[:110]))
    print("→ %s (--접점 으로 peer_후보조립_국내 를 다시 돌린다) · 근거 %s" % (jp, 근p))
    if D is not None:
        print("DART 호출 %d" % D.호출수)
    return 3 if 남은 else 0


if __name__ == "__main__":
    sys.exit(main())

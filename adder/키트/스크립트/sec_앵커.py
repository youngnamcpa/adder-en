# -*- coding: utf-8 -*-
"""미국 종목 앵커 시계열 — sec_fetch.py 에 없는 앵커 루프를 대신한다.

이미 받아 둔 `_raw/companyfacts.json` **한 파일만** 읽는다. 추가 조회를 하지 않는다.
매출·매출원가·판관비(총영업비용)·영업이익 네 줄을 사업연도별로 세우고
**영업이익률의 부호 전환을 세면서 스스로 뒤로 늘어난다.**

  python 스크립트/sec_앵커.py                      # 기본 (6월 결산 자동 감지)
  python 스크립트/sec_앵커.py --결산월 12          # 12월 결산
  python 스크립트/sec_앵커.py --최대 12            # 최대 12개 사업연도까지

멈추는 이유 셋을 파일에 적는다 — 전환 2회 도달 / 자료 소진 / 상한.

**서식이 갈리는 회사를 위해 두 체계를 다 훑는다.**
20-F(IFRS·ifrs-full)와 10-K(US GAAP·us-gaap)가 한 companyfacts 안에 따로 들어 있고,
전환기 두어 해는 양쪽에 다 있으면서 값이 다르다. us-gaap 을 먼저 쓰고 없는 해만 ifrs-full 로 메운다.
IFRS 시절 20-F 가 비용을 성격별로만 공시하면 매출원가·판관비 칸은 **비운다 — 지어내지 않는다.**

산출: _raw/앵커_시계열.json
"""
import os, sys, json, io, datetime, argparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "_raw")

# 태그 후보 — 앞에 있는 것부터 쓴다
TAGS = {
    "us-gaap": {
        "매출":     ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax",
                     "RevenueFromContractWithCustomerIncludingAssessedTax", "SalesRevenueNet"],
        # **한 글자가 다르다.** `CostOfGoodsAndService**s**Sold` 와
        # `CostOfGoodsAndService**Excluding**…` 는 다른 태그다. 실측(UBER): 후자를
        # 쓰는데 후보에 없어 매출원가가 통째로 비었다.
        # `Excluding…Amortization` 계열은 **상각이 빠진 원가**다 — 5번 COGS 시트가
        # 재료·외주와 상각을 따로 세우므로 오히려 맞는 재료지만, 그 사실은 밝힌다.
        "매출원가": ["CostOfRevenue", "CostOfGoodsAndServicesSold", "CostOfGoodsSold",
                     "CostOfServices",
                     "CostOfRevenueExcludingDepreciationDepletionAndAmortization",
                     "CostOfGoodsAndServiceExcludingDepreciationDepletionAndAmortization",
                     "CostOfServicesExcludingDepreciationDepletionAndAmortization"],
        "판관비":   ["SellingGeneralAndAdministrativeExpense", "GeneralAndAdministrativeExpense",
                     "OperatingExpenses", "CostsAndExpenses"],
        "영업이익": ["OperatingIncomeLoss"],
        # **총비용** — 「Operating income」 소계를 XBRL 에 안 내는 회사가 미국에는 흔하다.
        # 제약·에너지·리츠·보험이 그렇다(실측: LLY·XOM·O·BRK-B 넷 다 최근 해에 없다).
        # 그때 영업이익은 **매출 − 총비용**으로 구한다. 추정이 아니라 손익계산서의 산술이다.
        # `CostsAndExpenses` 만 쓴다 — 정의상 총비용이다. `OperatingExpenses` 는 회사마다
        # 뜻이 갈려(R&D·마케팅만 담기도 한다) **쓰지 않는다. 지어내는 것이 되기 때문이다.**
        "총비용":   ["CostsAndExpenses", "BenefitsLossesAndExpenses"],
    },
    "ifrs-full": {
        "매출":     ["Revenue", "RevenueFromContractsWithCustomers"],
        "매출원가": ["CostOfSales"],
        "판관비":   ["AdministrativeExpense", "SellingGeneralAndAdministrativeExpense"],
        "영업이익": ["ProfitLossFromOperatingActivities"],
    },
}


def _days(a, b):
    a = datetime.date.fromisoformat(a); b = datetime.date.fromisoformat(b)
    return (b - a).days


def 연간(facts, tax, tag, 결산월, 보고통화="USD"):
    """{'YYYY-MM-DD': (값, 서식)} — 결산월 말일에 끝나는 330~400일 duration 만."""
    G = facts.get(tax, {})
    if tag not in G:
        return {}
    out = {}
    for unit, arr in G[tag]["units"].items():
        # **통화를 고정하지 않는다.** 실측(TSM): TWD·USD 이중 공시에서 USD 고정이
        # 절반만 보고, 원천 조립(보고통화)과 다른 통화를 골라 둘이 어긋났다.
        # `보고통화` 인자를 따른다 — 기본 USD.
        if unit != 보고통화:
            continue
        for f in arr:
            if "start" not in f:
                continue
            e = f["end"]
            if int(e[5:7]) != 결산월:
                # 52 · 53주 결산은 끝날이 다음 달 초(≤ 7일)로 넘어가는 해가 있다 — 그 해를 같은 결산월로 받고 열쇠는 결산월 말일로 맞춘다
                # (결산월 6 인데 7월 초 · 8월 결산인데 9월 초 — 최근 해가 빠져 관문 ② 가 옛 국면으로 판정되던 결함 · 2026-10-23 유니버스 선별)
                다음 = 결산월 % 12 + 1
                if not (int(e[5:7]) == 다음 and int(e[8:10]) <= 7):
                    continue
                if not (330 <= _days(f["start"], e) <= 400):
                    continue
                import calendar                              # noqa: PLC0415
                y = int(e[:4]) - (1 if 결산월 == 12 else 0)
                e = "%04d-%02d-%02d" % (y, 결산월, calendar.monthrange(y, 결산월)[1])
            if not (330 <= _days(f["start"], f["end"]) <= 400):
                continue
            # 나중에 접수된 서류(최신 재작성)를 이긴 것으로 둔다
            prev = out.get(e)
            if prev is None or f.get("accn", "") >= prev[2]:
                out[e] = (f["val"], f.get("form"), f.get("accn", ""))
    return {k: (v[0], v[1]) for k, v in out.items()}


def _가까운월말의달(끝, 기본):
    """1.1.9 — 52/53주 회사의 결산월은 회계연도 말 날짜에 가장 가까운 월말의 달이다. 기간 축 · 원천 조립과 같은 함수
    (`기간축.가까운월말` — ±10일)로 판정한다. 그 폭 밖이거나 못 불러오면 `기본`(종전 ≤4일 규칙의 달)."""
    try:
        import 기간축 as _축                                # noqa: PLC0415
        m = _축.가까운월말(끝)
    except Exception:                                      # noqa: BLE001
        return 기본
    return m[0].month if m else 기본


def 결산월_감지(facts):
    G = facts.get("us-gaap", {}) or facts.get("ifrs-full", {})
    for tag in ("Assets", "StockholdersEquity", "Equity"):
        if tag in G:
            months = {}
            for unit, arr in G[tag]["units"].items():
                for f in arr:
                    if "start" in f:
                        continue
                    if f.get("fp") == "FY":
                        m, d = int(f["end"][5:7]), int(f["end"][8:10])
                        # 52/53주 회계연도는 종료일이 월말 ±며칠을 오간다 —
                        # 실측(DIS): FY 종료가 9-27~10-03 을 오가 10월이 최빈값이
                        # 되면서 결산월을 10월로 오감지, 원천 필수 5행이 통째로
                        # 비었다. 월초(≤4일) 종료는 전월의 주차 결산로 본다.
                        if d <= 4:
                            m = 12 if m == 1 else m - 1
                        m = _가까운월말의달(f["end"], m)
                        months[m] = months.get(m, 0) + 1
            if months:
                return max(months, key=months.get)
    return 12


def 통화감지(facts):
    """가장 흔한 통화 단위 — 이중 통화(TSM: TWD+USD)에선 보고통화가 이긴다."""
    from collections import Counter
    c = Counter()
    for ns in ("us-gaap", "ifrs-full"):
        for v in (facts.get(ns) or {}).values():
            for u in (v.get("units") or {}):
                if u != "shares" and "/" not in u:
                    c[u] += 1
    return c.most_common(1)[0][0] if c else "USD"


def 태그잇기(받은것, 후보, 항목="", 허용=0.005):
    """**태그 사슬 잇기** — 같은 뜻의 후보 태그들을 「최근 해에 닿는 사슬」을 씨앗으로 거꾸로 잇는다(다른 도구도 이 함수를 쓴다 —
    `동인원천.py` 의 미국 판, 2026-10-16 S1 리뷰: 첫 태그에서 끊어 CRM 의 기능별 매출원가가 FY2015~ 통째로 비었다).

    받은것  {태그: {끝날 키: (값, …)}} — 값은 튜플의 첫 칸
    후보    태그 우선순위(같은 조건이면 앞 것)
    → (채움 {키: (태그, 튜플)}, 이은것 [문장], 단절 [{항목 · 태그 · 최신태그 · 겹친해 · 어긋난해 · 차이율 · 끊긴해 · 값}])
    겹치는 해의 값이 `허용`(상대) 안에서 맞을 때만 잇는다. 갈리면 **옛 사슬만 끊고** `단절` 에 남긴다(값은 버리지 않는다).
    겹치는 해가 없으면 안 잇는다(맞는지 잴 수 없다) — 이을수록 겹침이 늘므로 붙을 때까지 돈다."""
    채움, 이은것, 단절 = {}, [], []
    남은 = sorted(받은것, key=lambda t: (-int(max(받은것[t])[:4]), -len(받은것[t]),
                                     후보.index(t) if t in 후보 else 99))
    if 남은:
        씨 = 남은.pop(0)
        채움 = {e: (씨, v) for e, v in 받은것[씨].items()}
    진전 = True
    while 진전 and 남은:
        진전, 보류 = False, []
        for tag in 남은:
            got = 받은것[tag]
            겹 = [e for e in got if e in 채움]
            새해 = [e for e in got if e not in 채움]
            if not 새해:
                continue
            if not 겹:
                보류.append(tag)      # 나중에 겹칠 수 있다. 버리지 않는다
                continue
            어긋 = [e for e in 겹
                    if 채움[e][1][0] and abs(got[e][0] - 채움[e][1][0]) >
                    abs(채움[e][1][0]) * 허용]
            if 어긋:
                차율 = abs(got[어긋[0]][0] - 채움[어긋[0]][1][0]) / abs(채움[어긋[0]][1][0])
                이은것.append("%s/%s — 겹치는 %d해 중 %d해가 어긋나 **옛 사슬을 끊었다** "
                            "(%s: 옛 %s vs 최신 %s, %.2f%%) — 최신 사슬(%s)을 지켰다"
                            % (항목, tag, len(겹), len(어긋), 어긋[0],
                               got[어긋[0]][0], 채움[어긋[0]][1][0], 차율 * 100,
                               채움[어긋[0]][0]))
                단절.append({"항목": 항목, "태그": tag,
                           "최신태그": 채움[어긋[0]][0],
                           "겹친해": sorted(e[:4] for e in 겹),
                           "어긋난해": sorted(e[:4] for e in 어긋),
                           "차이율": round(차율, 4),
                           "끊긴해": sorted(e[:4] for e in 새해),
                           "값": {e: got[e] for e in 새해}})
                continue
            for e in 새해:
                채움[e] = (tag, got[e])
            이은것.append("%s — %s 를 이어 붙였다 (겹치는 %d해가 다 맞아 %d해를 "
                        "더 얻었다)" % (항목, tag, len(겹), len(새해)))
            진전 = True
        남은 = 보류
    for tag in 남은:
        이은것.append("%s/%s — 겹치는 해가 없어 안 이었다 (%s 가 %d해를 "
                    "더 갖고 있다)"
                    % (항목, tag, tag,
                       len([e for e in 받은것[tag] if e not in 채움])))
    return 채움, 이은것, 단절


# **흑자 속 사이클의 문턱** (2026-10-16, S1 재리뷰 N-01) — `dart_fetch.사이클진폭배수` 와 같은 값 · 같은 정의(시험이 둘을 맞춰 본다).
사이클진폭배수 = 2.0


def 사이클진폭(율들, 배수문턱=사이클진폭배수):
    """관측 이익률 목록 → {최저, 최고, 배수, 사이클, 문턱}. 배수 = 최고 ÷ 최저(최저가 0 이하이면 None). 이익률이 둘 미만이면 None."""
    율 = [x for x in (율들 or []) if x is not None]
    if len(율) < 2:
        return None
    lo, hi = min(율), max(율)
    배 = (hi / lo) if lo > 0 else None
    # 모양 — 앞의 고점에서 1/3 넘게 내려간 적과 앞의 저점에서 1.5배 넘게 오른 적이 둘 다 있으면 「오르내림」(사이클),
    # 한쪽만 있으면 「한 방향」(규모의 경제로 이익률이 오르기만 한 회사 · 구조적으로 내리기만 한 회사). 오래된 해부터 준다.
    하락 = any(율[j] <= 율[i] * (2 / 3) for i in range(len(율)) for j in range(i + 1, len(율)) if 율[i] > 0)
    상승 = any(율[j] >= 율[i] * 1.5 for i in range(len(율)) for j in range(i + 1, len(율)) if 율[i] > 0)
    모양 = "오르내림" if (하락 and 상승) else ("한 방향(상승)" if 상승 else ("한 방향(하락)" if 하락 else "고름"))
    return {"최저": round(lo, 4), "최고": round(hi, 4), "배수": (round(배, 2) if 배 is not None else None),
            "사이클": bool(배 is not None and 배 >= 배수문턱), "문턱": 배수문턱, "모양": 모양}


def 진폭문장(진, 꼬리):
    """사이클진폭 결과 → 관문 ② 재료의 진폭 문장(관문 판정과 따로 — 전부 흑자일 때 붙인다)."""
    if 진.get("배수") is None:                                # 최저 이익률 0 — 배수를 잴 수 없다(S2-20 · dart_fetch 와 같은 문장)
        return ("영업이익률 %.1f%%~%.1f%%(최저 이익률 0 — 최고 ÷ 최저 배수를 잴 수 없다). 손익분기 언저리의 해가 있으니 관측 창이 한 국면에만 "
                "걸쳤는지 사람이 보고, %s" % (진["최저"] * 100, 진["최고"] * 100, 꼬리))
    범 = "영업이익률 %.1f%%~%.1f%%(최고 ÷ 최저 %.1f배" % (진["최저"] * 100, 진["최고"] * 100, 진["배수"])
    if not 진["사이클"]:
        return 범 + " < %.0f배) — 평상시 구간이 넓다" % 진["문턱"]
    if 진["모양"] == "오르내림":
        return ("**다만 흑자 속 사이클이다** — %s ≥ %.0f배, 오르내림). 관측 창이 한 국면에만 걸쳤는지 보고(정상 이익률 · 상하한 · "
                "국면 범위가 정점이나 바닥에 묶이지 않게), %s" % (범, 진["문턱"], 꼬리))
    return ("**다만 이익률이 %s으로 크게 옮겨 갔다** — %s ≥ %.0f배). 규모의 경제 · 구조 변화로 옮겨 간 것이면 옛 구간을 평상시에 "
            "섞지 말고 최근 구간이 앞으로의 평상시에 가까운지 본다. 사이클의 한쪽 국면이면 %s" % (진["모양"], 범, 진["문턱"], 꼬리))


def 만들기(cf_path, 결산월=None, 최대=12, 단절이음=False):
    """`단절이음=True` 면 겹치는 해에서 갈려 끊긴 옛 사슬을 **표식(`기준단절`)을 달고** 잇는다.
    기본은 끊는다 — 대신 끊긴 사슬과, 이었다면의 부호 전환을 `단절_옛사슬`·`참고_단절이음` 에 낸다."""
    facts = json.load(io.open(cf_path, encoding="utf-8"))["facts"]
    결산월 = 결산월 or 결산월_감지(facts)
    보고통화 = 통화감지(facts)

    시리즈 = {}   # end -> {항목: (값, 서식)}
    이은것 = []   # 태그를 이어 붙인 자취. 「자료 소진」이 참말인지 여기서 갈린다
    단절 = []     # 겹치는 해에서 갈려 끊은 옛 사슬
    for tax in ("us-gaap", "ifrs-full"):
        for 항목, 후보 in TAGS.get(tax, {}).items():
            # **첫 태그에서 끊지 않는다.** 옛 판은 `if got: break` 였다.
            # 회사가 서식을 갈아타면(예: SalesRevenueNet → RevenueFromContract…)
            # 새 태그가 최근 몇 해만 갖고 옛 태그가 그 앞을 갖는다. 첫 태그에서 끊으면
            # **그 앞이 통째로 사라지고도 「자료 소진」이라고 적힌다.**
            # 실측(MO): FY2016 에서 멈췄는데 뒤 후보에 FY2007~FY2017 이 있었다.
            #
            # **다만 겹치는 해의 값이 맞을 때만 잇는다** — 뜻이 다른 태그가 빈 해를
            # 메우면 시계열이 거짓이 된다. 겹치는 해가 없으면 안 잇는다(맞는지 잴 수 없다).
            #
            # **씨앗은 「목록의 첫 태그」가 아니라 「가장 많은 해를 가진 태그」다
            # (2026-09-08, MSFT 실측).** 옛 판은 후보를 왼쪽에서 오른쪽으로 훑으며
            # **처음 값이 나온 태그**를 씨앗으로 삼았다. 그 태그가 짧으면 긴 태그가
            # 「겹치는 해가 없다」로 거부되고, **거부된 태그는 다시 시도되지 않았다.**
            # 실측(MSFT): 매출 후보가 `Revenues`(FY2008~10, 3해) ·
            # `RevenueFromContractWithCustomerExcludingAssessedTax`(FY2016~26, 11해) ·
            # `SalesRevenueNet`(FY2009~17, 9해) 순이었다. 3해짜리가 씨앗이 되어
            # **11해짜리가 겹침 0 으로 거부**됐고, 그 뒤 SalesRevenueNet 이 붙어
            # 범위가 FY2017 까지 늘었는데도 **11해짜리를 다시 대 보지 않아**
            # 표가 FY2008~FY2017 로 굳었다 — **최근 9개 사업연도가 통째로 사라진 채
            # 「자료 소진」이라고 적혔다.** 상한·하한 대조는 「가장 최근 구조 블록」을
            # 쓰므로 이 결함은 시나리오 범위를 통째로 옛 회사의 것으로 만든다.
            #
            # **그래서 둘을 고친다 — 긴 것을 씨앗으로, 그리고 붙을 때까지 돈다.**
            # 겹침은 이을수록 늘어나므로 「지금 안 겹친다」가 「영영 안 겹친다」가 아니다.
            #
            # **씨앗은 「가장 최근 해에 닿는 사슬」이다 (2026-09-13, CRM 실측).** 「가장 긴 태그」를
            # 씨앗으로 두면, 옛 태그가 더 길고 겹치는 해에서 재작성 때문에 값이 갈릴 때 **최신 사슬이
            # 거부된다.** 실측(CRM): `Revenues`(FY2008~FY2017, 10해)가 씨앗이 되고
            # `RevenueFromContractWithCustomerExcludingAssessedTax`(FY2017~FY2026, ASC 606 소급 재작성)가
            # 겹치는 FY2017 에서 8,391,984 대 8,437,000(0.54%) 로 어긋나 거부됐다 — **최근 9해(FY2018~FY2026)가
            # 통째로 사라진 채 「전환 2회 도달」로 멈췄다.** 상한·하한 대조는 가장 최근 구조 블록을 쓰므로
            # 시나리오 범위가 옛 회사의 것으로 선다.
            # 이제 **최근 해에 닿는 사슬을 먼저 확보하고 거꾸로 잇는다.** 겹치는 해에서 갈리면
            # **옛 사슬만 끊는다** — 끊긴 사슬은 버리지 않고 `단절_옛사슬` 에 적고, `--단절이음` 을 켜면
            # 표식을 달고 잇는다(기준이 바뀐 해를 조용히 섞지 않는다).
            받은것 = {}
            for tag in 후보:
                got = 연간(facts, tax, tag, 결산월, 보고통화)
                if got:
                    받은것[tag] = got
            _채, _이, _단 = 태그잇기(받은것, 후보, 항목)
            채움 = {e: (v[0], v[1], tax, t) for e, (t, v) in _채.items()}
            이은것.extend(_이)
            for b in _단:
                단절.append(dict({"항목": b["항목"], "체계": tax}, **{k: v for k, v in b.items() if k != "항목"}))
            for e, v in 채움.items():
                d = 시리즈.setdefault(e, {})
                if 항목 not in d:          # us-gaap 먼저 돌므로 우선순위 유지
                    d[항목] = v

    # ── 끊긴 옛 사슬을 표식 달고 이은 판(참고 또는 `단절이음`) ──────────────
    단절해 = {}
    시리즈_이음 = {e: dict(d) for e, d in 시리즈.items()}
    for b in 단절:
        for e, v in b["값"].items():
            d = 시리즈_이음.setdefault(e, {})
            if b["항목"] not in d:
                d[b["항목"]] = (v[0], v[1], b["체계"], b["태그"])
                단절해.setdefault(e, []).append(
                    "%s 는 옛 사슬 %s — 최신 %s 와 %s 에서 %.2f%% 갈려 끊겼던 것을 이었다"
                    % (b["항목"], b["태그"], b["최신태그"], "·".join(b["어긋난해"]),
                       b["차이율"] * 100))

    def _표짓기(시리즈, 표식, 자르기=True):
        표 = []
        for e in sorted(시리즈):
            r = 시리즈[e]
            매출 = r.get("매출", (None,))[0]
            영업 = r.get("영업이익", (None,))[0]
            원가 = r.get("매출원가", (None,))[0]
            판관 = r.get("판관비", (None,))[0]
            총비용 = r.get("총비용", (None,))[0]
            # **매출이 없으면 그 해는 없는 것이다.** 영업이익은 없어도 매출만 있으면 남긴다 —
            # 관문 ①(매출이 있나)은 매출만으로 판정하고, 영업이익률만 비게 둔다.
            # 옛 판은 `영업 is None` 이면 그 해를 통째로 버렸다. 그래서 영업이익 태그가 없는
            # 회사는 **표가 통째로 비고도 「자료 소진」이라고 적혔다**(실측: LLY·O·XOM).
            if 매출 is None:
                continue
            영업출처 = "공시"
            # **판관비 칸은 언제나 합산 계열로 잰다 — 단일 태그 선택이 아니다
            # (2026-09-08, MSFT 실측).** 옛 판은 이 합산을 「영업이익 태그가 없을 때」만
            # 돌렸고, 영업이익이 공시된 회사는 `판관비` 칸에 **후보 목록에서 처음 잡힌
            # 태그 하나**를 그대로 실었다. 실측(MSFT): `SellingGeneralAndAdministrative
            # Expense` 가 없어 `GeneralAndAdministrativeExpense` 7,956 하나가 잡혔는데
            # 실제 판관비는 70,228 이다 — **표의 한 칸이 아홉 배 틀린 채 아무 경고도 안
            # 떴다.** 총영업비용(잔여)과 영업이익률은 멀쩡해서 더 안 보인다.
            # **총계 태그가 있으면 그 부분 태그는 안 더한다** — 실측(NKE): SG&A 총계와
            # 그 부분(G&A·S&M)을 함께 태깅한 회사에서 이중계상이 났다(`sec_원천.py` 의
            # `_총계부분` 과 같은 판정이다).
            # **무형자산상각은 이 합에 안 넣는다 (2026-09-08, MSFT 실측).** 대부분의
            # 미국 신고인은 그 상각을 매출원가나 R&D 줄 **안에** 이미 담아 낸다 —
            # 따로 더하면 이중이다. 실측(MSFT FY2026): G&A+R&D+S&M = 70,228 로 잔여와
            # **원 단위까지 맞는데**, 무형상각 4,700 을 얹자 매출 대비 +1.4%p 벌어졌다.
            # 별도 줄로 내는 회사는 아래 잔여 대조가 잡아 준다.
            # 영업이익 태그가 없어 **되살려야 할 때만** 무형상각을 얹어 본다(실측 LLY).
            판관합, 판관수, 쓴태그 = 0.0, 0, []
            for _t in ("SellingGeneralAndAdministrativeExpense",
                      "ResearchAndDevelopmentExpense",
                      "ResearchAndDevelopmentExpenseExcludingAcquiredInProcessCost",
                      "SellingAndMarketingExpense",
                      "GeneralAndAdministrativeExpense"):
                _got = 연간(facts, "us-gaap", _t, 결산월, 보고통화)
                if e in _got:
                    판관합 += _got[e][0]
                    판관수 += 1
                    쓴태그.append(_t)
            for 총, 부분들 in (("SellingGeneralAndAdministrativeExpense",
                              ("GeneralAndAdministrativeExpense",
                               "SellingAndMarketingExpense")),
                             ("ResearchAndDevelopmentExpense",
                              ("ResearchAndDevelopmentExpenseExcludingAcquiredInProcessCost",))):
                if 총 in 쓴태그:
                    for 부분 in 부분들:
                        if 부분 in 쓴태그:
                            _got = 연간(facts, "us-gaap", 부분, 결산월, 보고통화)
                            판관합 -= _got[e][0]
                            판관수 -= 1
                            쓴태그.remove(부분)
            if 판관수:
                판관, 판관출처 = 판관합, "합산(%s)" % " + ".join(쓴태그)
            else:
                판관출처 = "단일 태그" if 판관 is not None else None
            if 영업 is None and 원가 is not None and 판관수:
                # **매출 − 매출원가 − (판관 계열 전부 합).** 제약 대형(PFE·LLY)은
                # OperatingIncomeLoss 도 CostsAndExpenses 도 안 낸다. 단일 선택이면
                # SG&A 만 잡혀 **R&D 가 빠지고 OPM 이 과대**해진다(실측: LLY 66%).
                # 되살릴 때만 무형상각을 얹는다 — 손익에 별도 줄로 서는 회사가 있다.
                _되살= 판관합
                _되살수 = 판관수
                _무형 = 연간(facts, "us-gaap", "AmortizationOfIntangibleAssets",
                           결산월, 보고통화)
                if e in _무형:
                    _되살 += _무형[e][0]
                    _되살수 += 1
                후 = 매출 - 원가 - _되살
                if 매출 and -1.0 <= 후 / 매출 <= 1.0:
                    영업, 영업출처 = 후, "계산(매출−원가−판관%d계열)" % _되살수
            if 영업 is None and 총비용 is not None:
                후 = 매출 - 총비용
                # 계산값이 말이 되는지 본다 — 매출 대비 −100%~+100% 밖이면 그 태그가
                # 총비용이 아니라는 뜻이다. **버린다. 억지로 채우지 않는다.**
                if 매출 and -1.0 <= 후 / 매출 <= 1.0:
                    영업, 영업출처 = 후, "계산(매출−총비용)"
            # 총영업비용 = 매출 − 매출원가 − 영업이익 (매출원가를 알 때만)
            총영업비용 = (매출 - 원가 - 영업) if (원가 is not None and 영업 is not None) else None
            # **판관비 칸과 잔여를 견준다 — 이 대조가 없어서 아홉 배가 지나갔다.**
            # 잔여(총영업비용)는 산술이라 언제나 맞고, 판관비 칸은 태그가 다 잡혔을 때만
            # 맞는다. 둘이 매출의 1% 넘게 벌어지면 **태그가 일부만 잡은 것**이다.
            # **합산이 잔여와 벌어지면 총영업비용 태그 → 합산 + 구조조정비 순으로 닫아 본다**
            # (2026-09-13, CRM 실측 — `sec_원천.py` 65행과 같은 규칙). 합산 계열이 Restructuring
            # 461/586 을 빠뜨려 FY2025·FY2026 이 −1.2%p·−1.4%p 벌어졌다. **잔여와 맞을 때만** 바꾼다.
            if (판관 is not None and 총영업비용 is not None and 매출
                    and abs(판관 - 총영업비용) > abs(매출) * 0.0005):
                _oe = 연간(facts, "us-gaap", "OperatingExpenses", 결산월, 보고통화)
                _rc = {}
                for _r in ("RestructuringCharges", "RestructuringCosts"):
                    _rc = 연간(facts, "us-gaap", _r, 결산월, 보고통화)
                    if e in _rc:
                        break
                if e in _oe and abs(_oe[e][0] - 총영업비용) <= abs(매출) * 0.0005:
                    판관, 판관출처 = _oe[e][0], "OperatingExpenses(잔여와 일치 — 합산 %s 대체)" % (판관출처 or "")
                elif e in _rc and abs(판관 + _rc[e][0] - 총영업비용) <= abs(매출) * 0.0005:
                    판관, 판관출처 = 판관 + _rc[e][0], "%s + 구조조정비(잔여와 일치)" % (판관출처 or "")
            판관갭 = None
            if 판관 is not None and 총영업비용 is not None and 매출:
                판관갭 = round((판관 - 총영업비용) / 매출, 4)
            표.append({
                "사업연도": "FY" + e[:4], "종료일": e,
                "매출": 매출, "매출원가": 원가, "판관비": 판관, "총영업비용": 총영업비용,
                "판관비출처": 판관출처, "판관비_잔여갭": 판관갭,
                "영업이익": 영업,
                "영업이익률": (round(영업 / 매출, 4) if (매출 and 영업 is not None) else None),
                "영업이익출처": 영업출처,
                # **이 원가에 상각이 들어 있나.** 「Excluding…Amortization」 계열로 잡혔으면
                # 상각이 빠진 값이다. 5번 COGS 로 부을 때 상각을 어디서 더하는지 갈린다.
                "매출원가_상각포함": (None if 원가 is None else
                                ("Excluding" not in (r.get("매출원가", (None, None, None, ""))[3]
                                                     if len(r.get("매출원가", ())) > 3 else ""))),
                "서식": r.get("매출", (None, None))[1], "체계": r.get("매출", (None, None, None))[2],
                "기준단절": (단절해.get(e) if 표식 else None),
            })

        표 = 표[-최대:] if 자르기 else 표
        전환 = []
        for i in range(1, len(표)):
            a, b = 표[i - 1]["영업이익"], 표[i]["영업이익"]
            if a is None or b is None:
                continue
            if (a < 0) != (b < 0):
                전환.append(f"{표[i-1]['사업연도']}({'−' if a<0 else '+'})"
                            f"→{표[i]['사업연도']}({'−' if b<0 else '+'})")
        return 표, 전환

    표, 전환 = _표짓기(시리즈_이음 if 단절이음 else 시리즈, 단절이음)
    참고표, 참고전환 = (_표짓기(시리즈_이음, True, False) if (단절 and not 단절이음) else (None, None))

    # **「자료 소진」은 후보 태그를 다 훑은 뒤에야 참말이다.** 옛 판은 첫 태그에서
    # 끊고도 그렇게 적었다.
    # **「자료 소진」과 「연간 자료가 없다」는 다른 말이다.** 표가 통째로 비었을 때
    # 「소진」이라고 적으면 태그 매핑 문제로 읽힌다. 실측(XOM): companyfacts 에 10-Q
    # 만 268건 있고 **10-K 가 하나도 없었다** — 지주회사 재편으로 보고 법인이 바뀌어
    # 새 CIK 가 연간 보고를 낸다. 그때는 태그를 아무리 늘려도 안 나온다.
    서식들 = set()
    for tax in ("us-gaap", "ifrs-full"):
        for 후보 in TAGS.get(tax, {}).values():
            for tag in 후보:
                for _u, arr in (facts.get(tax, {}).get(tag, {}).get("units") or {}).items():
                    for f in arr:
                        서식들.add(f.get("form"))
    이유 = ("전환 2회 도달" if len(전환) >= 2 else
            ("상한" if len(표) >= 최대 else "자료 소진 (후보 태그를 다 훑었다)"))
    if not 표:
        연간서식 = {x for x in 서식들 if x and ("10-K" in x or "20-F" in x)}
        if not 연간서식:
            이유 = ("**연간 보고서가 없다** — companyfacts 에 %s 만 있고 10-K·20-F 가 "
                   "하나도 없다. 태그 문제가 아니다. 이 CIK 가 연간 보고를 안 내는 "
                   "것이니(지주회사 재편·상장 직후·법인 변경) **보고 법인을 다시 "
                   "찾으십시오**" % (" · ".join(sorted(x for x in 서식들 if x)) or "아무 서식도"))
        else:
            이유 = ("**연간 duration 을 못 잡았다** — %s 는 있는데 결산월 %d월 말에 "
                   "끝나는 330~400일 구간이 없다. 결산월 감지가 틀렸을 수 있으니 "
                   "`--결산월` 로 지정해 보십시오"
                   % (" · ".join(sorted(연간서식)), 결산월))
    if 단절 and not 단절이음:
        이유 += (" — **기준 단절로 옛 사슬을 끊었다**(%s). 이었다면 %d해 · 부호 전환 %d회 — "
                 "`--단절이음` 으로 표식을 달고 이을 수 있다(기준이 바뀐 해를 섞는 판단은 사람이 한다)"
                 % (" · ".join("%s/%s %s~%s" % (b["항목"], b["태그"], b["끊긴해"][0], b["끊긴해"][-1])
                               for b in 단절 if b["끊긴해"]),
                    len(참고표 or []), len(참고전환 or [])))
    elif 단절 and 단절이음:
        이유 += " — 끊긴 옛 사슬을 `기준단절` 표식을 달고 이었다(%d건)" % len(단절)
    if len(표) < 6:
        이유 += " — ★6개 사업연도에 못 미친다"
    # **관문 ② 재료** — 자체검사 ⓪ 과 같은 정의(2026-10-16, S1 리뷰). 전환 0 회 + 전부 흑자는 「평상시 구간이 넓다」(안 걸림).
    # 기준 단절로 끊은 옛 사슬이 있으면 **이었다면의 전환 수를 참고로 함께 싣는다** — 기준 개정(ASC 606 · IFRS 15) 차이로
    # 끊으면 관측 해와 전환 수가 줄어 관문 재료가 바뀐다(실측 CRM: 10해 · 0회 ↔ 이었다면 19해 · 2회). 판단은 사람이 한다.
    # **관문 판정과 사이클 진폭은 다른 질문이다**(2026-10-16, S1 재리뷰 N-01) — 전부 흑자여도 이익률이 몇 배로 출렁이면(흑자 속 사이클)
    # 관측 창이 한 국면에만 걸쳤는지를 따로 봐야 한다. 진폭 정의는 `dart_fetch.사이클진폭` 과 같다.
    _부 = [x["영업이익"] for x in 표 if x["영업이익"] is not None]
    진폭 = 사이클진폭([x["영업이익률"] for x in 표 if x["영업이익률"] is not None])
    if not _부:
        관문2 = "재료 없음"
    elif len(전환) == 0 and all(v >= 0 for v in _부):
        if 진폭 is None:
            관문2 = "전부 흑자(전환 0회) — 관문 ② 에 안 걸린다. 사이클 진폭은 이익률 재료가 없어 못 쟀다"
        else:
            관문2 = "전부 흑자(전환 0회) — 관문 ② 에 안 걸린다. " + 진폭문장(진폭, "모자라면 `--최대` 를 늘리거나 기준 단절로 끊은 옛 사슬(`--단절이음`)을 본다")
    elif len(전환) == 0:
        관문2 = "전부 적자(전환 0회) — 최근이 단조 개선이면 T4(전환 미완)의 예고, 아니면 관문 ② 에 걸린다(자체검사 ⓪ 이 이익률로 가른다)"
    else:
        관문2 = "부호 전환 %d회 — 한 번 꺾여 돌아오지 않은 것인지, 진폭이 사이클인지 한 번의 사건인지 관문 ② 를 판정하십시오" % len(전환)
    if 참고표 is not None:
        관문2 += (" (참고: 기준 단절로 끊은 옛 사슬을 이었다면 %d해 · 부호 전환 %d회 — 기준 개정 차이면 그 해들도 관문 ② 의 관측으로 "
                 "볼지 사람이 정한다)" % (len(참고표), len(참고전환 or [])))

    율 = [x["영업이익률"] for x in 표 if x["영업이익률"] is not None]
    # **판관비 칸이 잔여와 벌어진 해를 세어 밖으로 낸다.** 표만 보면 안 보이는 자리다.
    벌어진해 = [(x["사업연도"], x["판관비_잔여갭"]) for x in 표
              if x.get("판관비_잔여갭") is not None and abs(x["판관비_잔여갭"]) > 0.01]
    return {
        "통화": 보고통화, "결산월": 결산월, "사업연도수": len(표), "표": 표, "태그_이음": 이은것,
        "부호_전환_횟수": len(전환), "부호_전환_지점": 전환, "멈춘_이유": 이유, "관문2재료": 관문2, "이익률진폭": 진폭,
        "판관비_잔여와_벌어진_해": 벌어진해,
        # 겹치는 해에서 갈려 끊은 옛 사슬 — 값은 버리지 않고 여기 둔다
        "단절_옛사슬": [{k: v for k, v in x.items() if k != "값"} for x in 단절],
        "단절이음": 단절이음,
        "참고_단절이음": (None if 참고표 is None else {
            "사업연도수": len(참고표), "처음": 참고표[0]["사업연도"] if 참고표 else None,
            "부호_전환_횟수": len(참고전환), "부호_전환_지점": 참고전환,
            "주의": "옛 사슬을 이었다면의 참고값이다(`--최대` 상한 없이 셌다) — 기준(예: ASC 606 소급 재작성)이 바뀐 해가 섞인다. "
                    "앵커 표·범위 대조에는 쓰지 않는다"}),
        "영업이익률": {
            "최저": min(율) if 율 else None,
            "최저_해": 표[율.index(min(율))]["사업연도"] if 율 else None,
            "최고": max(율) if 율 else None,
            "최고_해": 표[율.index(max(율))]["사업연도"] if 율 else None,
            "평균": round(sum(율) / len(율), 4) if 율 else None,
        },
        "주의": "매출원가·판관비가 비어 있는 해는 그 서식(주로 20-F·IFRS 성격별 공시)이 "
                "구분을 주지 않은 해다. 채우지 않는 것이 맞다. "
                "영업이익출처가 「계산(…판관N계열)」이면 N 이 판관 계열을 몇 개 "
                "합쳤는지다 — **N 이 1~2 면 R&D 등 큰 계열이 빠져 OPM 이 과대일 수 "
                "있다**(실측 LLY: R&D 태그가 표준 이름이 아니어서 빠짐). 그 해 "
                "10-K 손익으로 확인하라.",
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--결산월", type=int, default=None)
    ap.add_argument("--최대", type=int, default=12)
    ap.add_argument("--입력", default=os.path.join(RAW, "companyfacts.json"))
    ap.add_argument("--출력", default=os.path.join(RAW, "앵커_시계열.json"))
    ap.add_argument("--단절이음", action="store_true",
                    help="겹치는 해에서 갈려 끊긴 옛 태그 사슬을 `기준단절` 표식을 달고 잇는다(기본: 끊는다)")
    a = ap.parse_args()
    if not os.path.exists(a.입력):
        print("companyfacts.json 이 없습니다. sec_fetch.py 를 먼저 돌리십시오.")
        raise SystemExit(1)
    out = 만들기(a.입력, a.결산월, a.최대, a.단절이음)
    dst = a.출력
    io.open(dst, "w", encoding="utf-8").write(json.dumps(out, ensure_ascii=False, indent=2))
    for r in out["표"]:
        print(f"{r['사업연도']}  매출 {r['매출']:>14,}  매출원가 "
              f"{(format(r['매출원가'],',') if r['매출원가'] is not None else '-'):>14}  "
              f"총영업비용 {(format(r['총영업비용'],',') if r['총영업비용'] is not None else '-'):>14}  "
              f"영업이익 {(format(r['영업이익'],',') if r['영업이익'] is not None else '-'):>14}  "
              f"{'' if r['영업이익률'] is None else format(r['영업이익률']*100, '.1f')+'%':>9}  "
              f"{r['서식']}"
              f"{'' if r['영업이익출처'] == '공시' else '  ← ' + r['영업이익출처']}"
              f"{'  [기준단절]' if r.get('기준단절') else ''}")
    print("부호 전환", out["부호_전환_횟수"], "회:", out["부호_전환_지점"], "| 멈춤:", out["멈춘_이유"])
    print("관문 ② 재료:", out["관문2재료"])
    for b in out.get("단절_옛사슬") or []:
        print("  ※ 옛 사슬을 끊었다 — %s/%s (최신 %s 와 %s 에서 %.2f%% 차) · 끊긴 해 %s"
              % (b["항목"], b["태그"], b["최신태그"], "·".join(b["어긋난해"]), b["차이율"] * 100,
                 ("%s~%s" % (b["끊긴해"][0], b["끊긴해"][-1])) if b["끊긴해"] else "없음"))
    # **판관비 칸이 잔여와 벌어졌으면 화면에 크게 알린다.** 표의 총영업비용과
    # 영업이익률은 잔여라 멀쩡하므로, 알리지 않으면 판관비 한 칸만 조용히 틀린다.
    벌 = out.get("판관비_잔여와_벌어진_해") or []
    if 벌:
        print("\n  ⚠ 판관비 칸이 잔여(총영업비용)와 벌어진 해 %d 개 — "
              "태그가 판관비의 일부만 잡은 것입니다." % len(벌))
        for 해, 갭 in 벌:
            print("      %s  매출 대비 %+.1f%%p" % (해, 갭 * 100))
        print("      **판관비 칸을 그대로 읽지 마십시오. 총영업비용(잔여)이 정본입니다.**")
    print("저장:", dst)

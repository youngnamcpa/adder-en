# -*- coding: utf-8 -*-
"""다모다란 산업 무차입베타 — 유사기업 βU 의 **늘 붙는 대조값**이자, 회귀가 무너졌을 때 내려가는 섹터 사다리.

**되풀이 2회로 만들었다.** SGC에너지·한일시멘트 두 회차가 회귀 βU 를 기각하고
섹터 상향식으로 내려갔는데, 그때마다 **웹 갈래를 띄워 손으로 받아 왔다.**
market_data.py 가 Rf·ERP·회사채·합성등급 스프레드는 받는데 산업 베타표만 없었다.

**2026-10-17(S7-07) — C2 기본 산출에 붙는다.** 종전에는 서열(⑲)이 깨진 뒤에만 부르는 도구라, 유사기업 βU 가 산업 βU 의
4분의 1~3분의 2 인 판(국내 동종이 적은 플랫폼 · 게임 · 유통 실측)이 자동으로 걸리지 않았다. 이제 조립기(`peer_조립.py` ·
`peer_βU_us.py` · `peer_병합.py`)가 `대조값()` 으로 대상회사의 매핑 줄(GLOBAL · 지역) 현금보정 βU 를 표 머리에 싣고,
핵심 중앙값이 그 둘 모두에서 ±30% 넘게 갈리면 ★ 를 단다.

    python 스크립트/산업베타.py --지역 EM --산업 "Construction Supplies" "Engineering/Construction"
    python 스크립트/산업베타.py --회사 "Hanil Cement"        # 매핑표에서 그 회사의 줄을 찾는다
    python 스크립트/산업베타.py --대상 KOSE:A000660 --βU 1.10  # 그 회사 줄 · 지역의 산업 βU 와 대조(±30%)
    python 스크립트/산업베타.py --대상 KOSE:A000660 --해외후보  # 같은 줄의 미국 상장 회사(해외 동종 경로 ⑤)
    python 스크립트/산업베타.py --지역 EM --목록              # 그 지역의 산업 줄 전부

**줄을 이름으로 고르지 않는다** — `--회사` · `--대상` 으로 대상회사 자신이 어느 줄에 배정돼 있는지
먼저 확인한다. 실측(한일시멘트): 이름으로는 「Building Materials」가 맞아 보였는데
매핑표에는 **Construction Supplies(SIC 3241)** 였다. 사명에 Cement 가 든 145곳 중
**135곳**이 그 줄이고, 나머지 10곳은 오탐 5(Commencement·Advancement 등)와
운송·유통·금융 자회사 5다 — **시멘트를 만드는 회사는 예외가 없다.**
Building Materials 469곳에는 **Cement 가 든 회사가 한 곳도 없다**(창호·유리·타일이다).

**지역도 매핑표가 정한다.** 같은 줄이라도 Global 0.9167 · EM 0.9062 · Japan 1.2079 ·
US 1.0468 로 크게 갈린다. 매핑표의 「Broad Group」 이 지역이다(Emerging Markets → EM · United States → US · Japan → JAPAN ·
그 밖은 GLOBAL).

**주소를 박지 않는다(S7-18).** 파일 주소는 `market_data.다모다란주소` 가 자료 페이지(datacurrent.html)의 링크에서 고른다 —
링크가 안 보이면 받지 않고 멈춘다. 받은 것은 `~/.dcf캐시/` 에 두고(회차마다 다시 받지 않는다 — 파일이 크다),
곁에 `{파일}.meta.json`(주소 · 받은 날 · Last-Modified)을 남긴다. 산출에는 **파일 안 갱신일(「Date updated」)** 과
**평가기준일과의 차(일)** 를 싣는다 — 다음 해 평가기준일에도 같은 판을 조용히 쓰지 않게(판이 평가기준일보다 1년 넘게 이르거나
평가기준일 뒤면 경보).
"""
import re
import argparse
import datetime as _dt
import io
import json
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

캐시 = os.environ.get("DCF_공용캐시") or os.environ.get("DCF_SHARED_CACHE") or os.path.join(os.path.expanduser("~"), ".dcf캐시")
지역표 = {"GLOBAL": "betaGlobal.xls", "EM": "betaemerg.xls",
        "JAPAN": "betaJapan.xls", "US": "betas.xls"}
매핑파일 = "indname.xls"
머리 = {"User-Agent": "Mozilla/5.0 (compatible; DCF-research/1.0)"}
지역이름 = {"emerging markets": "EM", "united states": "US", "japan": "JAPAN"}
미국거래소 = ("NYSE:", "NasdaqGS:", "NasdaqGM:", "NasdaqCM:", "NYSEAM:", "NYSEArca:", "BATS:")
대조폭 = 0.30          # 핵심 중앙값이 산업 βU 의 ±30% 밖이면 ★(GLOBAL · 지역 둘 다 밖일 때)


def 받기(이름, 조용=False):
    """캐시에 없으면 자료 페이지의 링크로 내려받는다. 있으면 그대로 쓴다. 받으면 곁에 meta 를 남긴다."""
    os.makedirs(캐시, exist_ok=True)
    p = os.path.join(캐시, 이름)
    if os.path.exists(p) and os.path.getsize(p) > 1000:
        if not 조용:
            print("캐시 사용: %s (%.1f MB)" % (p, os.path.getsize(p) / 1e6))
        return p
    import market_data as md
    주소, 까닭 = md.다모다란주소(이름)
    if not 주소:
        raise SystemExit("다모다란 %s 를 받지 않는다 — %s" % (이름, 까닭))
    import urllib.request
    req = urllib.request.Request(주소, headers=머리)
    with urllib.request.urlopen(req, timeout=180) as r:
        데이터 = r.read()
        lm = r.headers.get("Last-Modified")
    io.open(p, "wb").write(데이터)
    json.dump({"URL": 주소, "받은날": _dt.date.today().isoformat(), "Last-Modified": lm},
              io.open(p + ".meta.json", "w", encoding="utf-8"), ensure_ascii=False)
    print("받음: %s (%.1f MB) · %s" % (p, len(데이터) / 1e6, 주소))
    return p


def _엑셀날짜(v):
    try:
        import xlrd
        return _dt.datetime(*xlrd.xldate_as_tuple(float(v), 0)[:3]).date().isoformat()
    except Exception:                                       # noqa: BLE001
        return None


def 판정보(p, 기준일=None):
    """{파일, 파일갱신일(Date updated), 받은날, 평가기준일차_일, 경보}. 기준일 = 평가기준일 YYYY-MM-DD(선택)."""
    out = {"파일": os.path.basename(p), "파일갱신일": None, "받은날": None, "평가기준일차_일": None, "경보": None}
    try:
        import xlrd
        wb = xlrd.open_workbook(p, on_demand=True)
        for nm in wb.sheet_names():
            sh = wb.sheet_by_name(nm)
            for r in range(min(4, sh.nrows)):
                if str(sh.cell_value(r, 0)).strip().lower().startswith("date updated"):
                    out["파일갱신일"] = _엑셀날짜(sh.cell_value(r, 1))
                    break
            if out["파일갱신일"]:
                break
    except Exception:                                       # noqa: BLE001
        pass
    m = p + ".meta.json"
    if os.path.exists(m):
        try:
            out["받은날"] = json.load(io.open(m, encoding="utf-8")).get("받은날")
        except (ValueError, OSError):
            pass
    if not out["받은날"]:
        out["받은날"] = _dt.date.fromtimestamp(os.path.getmtime(p)).isoformat() + "(파일 시각 — meta 없음)"
    if 기준일 and out["파일갱신일"]:
        차 = (_dt.date.fromisoformat(out["파일갱신일"]) - _dt.date.fromisoformat(기준일[:10])).days
        out["평가기준일차_일"] = 차
        if 차 > 0:
            out["경보"] = "판 갱신일 %s 이 평가기준일 %s 뒤 — 기준일 뒤 정보(대조값으로만 쓴다)" % (out["파일갱신일"], 기준일)
        elif 차 < -365:
            out["경보"] = "판 갱신일 %s 이 평가기준일보다 1년 넘게 이르다 — 새 판을 받는다(캐시 파일을 지우고 다시)" % out["파일갱신일"]
    return out


def 표읽기(p, 시트=None):
    """행 목록. xlrd 가 없으면 pandas 로 떨어진다."""
    try:
        import xlrd
        wb = xlrd.open_workbook(p, on_demand=True)
        sh = None
        if 시트 and 시트 in wb.sheet_names():
            sh = wb.sheet_by_name(시트)
        else:
            for nm in wb.sheet_names():
                if "industry" in nm.lower() and "average" in nm.lower():
                    sh = wb.sheet_by_name(nm)
                    break
        sh = sh or wb.sheet_by_index(0)
        return [[sh.cell_value(r, c) for c in range(sh.ncols)] for r in range(sh.nrows)]
    except ImportError:
        import pandas as pd
        df = pd.read_excel(p, sheet_name=시트 or 0, header=None)
        return df.values.tolist()


def 머리찾기(행들):
    """첫 칸이 정확히 「Industry Name」인 줄을 머리로 본다.

    「Variable definitions:」 같은 안내 줄에도 industry 링크가 들어 있어, 느슨하게
    찾으면 그쪽에 먼저 걸린다(실측: betaemerg.xls 6행 vs 진짜 머리 9행).
    """
    for i, 줄 in enumerate(행들):
        if 줄 and str(줄[0]).strip().lower() in ("industry name", "industry", "company name"):
            return i
    for i, 줄 in enumerate(행들):          # 매핑표는 첫 칸 이름이 다르다
        글 = " ".join(str(x) for x in 줄).lower()
        if "industry group" in 글 or ("company name" in 글 and "industry" in 글):
            return i
    return 0


def _수(v):
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def 산업줄(줄이름, 지역="GLOBAL", 기준일=None):
    """한 지역 표의 한 줄 → dict(지역, 줄, 회사수, βL, DE, 세율, βU, 현금비중, βU현금보정, 판) · 없으면 None."""
    p = 받기(지역표[지역.upper()], 조용=True)
    행들 = 표읽기(p)
    h = 머리찾기(행들)
    머리줄 = [str(x).strip() for x in 행들[h]]

    def 칸(줄, *이름들):
        for 이름 in 이름들:
            for i, k in enumerate(머리줄):
                if k.lower().startswith(이름.lower()) and i < len(줄):
                    return 줄[i]
        return None
    for 줄 in 행들[h + 1:]:
        if 줄 and str(줄[0]).strip().lower() == 줄이름.strip().lower():
            return {"지역": 지역.upper(), "줄": str(줄[0]).strip(), "회사수": _수(칸(줄, "Number of firms")),
                    "βL": _수(칸(줄, "Beta")), "DE": _수(칸(줄, "D/E Ratio")), "세율": _수(칸(줄, "Effective Tax rate")),
                    "βU": _수(칸(줄, "Unlevered beta")), "현금비중": _수(칸(줄, "Cash/Firm value")),
                    "βU현금보정": _수(칸(줄, "Unlevered beta corrected for cash")), "판": 판정보(p, 기준일)}
    return None


def 매핑(찾기=None, 거래소티커=None):
    """매핑표(indname.xls 「By company name」) → 행 dict 목록. 거래소티커(예: KOSE:A000660)는 정확히, 찾기는 이름 부분일치."""
    p = 받기(매핑파일, 조용=True)
    행들 = 표읽기(p, "By company name")
    h = 머리찾기(행들)
    머리줄 = [str(x).strip() for x in 행들[h]]
    out = []
    for 줄 in 행들[h + 1:]:
        d = {머리줄[i]: 줄[i] for i in range(min(len(머리줄), len(줄)))}
        t = str(d.get("Exchange:Ticker") or "").strip()
        if 거래소티커 and t.upper() == 거래소티커.upper():
            out.append(d)
        elif 찾기 and 찾기.lower() in str(d.get("Company Name") or "").lower():
            out.append(d)
    return out


def 거래소티커후보(티커):
    """티커만 알 때(미국 회차) — 매핑표에서 「거래소:티커」 가 그 티커로 끝나는 것. 미국 거래소를 앞에 둔다."""
    p = 받기(매핑파일, 조용=True)
    행들 = 표읽기(p, "By company name")
    h = 머리찾기(행들)
    머리줄 = [str(x).strip() for x in 행들[h]]
    i = 머리줄.index("Exchange:Ticker") if "Exchange:Ticker" in 머리줄 else 1
    끝 = ":" + 티커.upper()
    hits = [str(줄[i]).strip() for 줄 in 행들[h + 1:] if len(줄) > i and str(줄[i]).strip().upper().endswith(끝)]
    return sorted(hits, key=lambda t: (not any(t.startswith(x) for x in 미국거래소), t))


def 국내티커(종목코드, 시장=None):
    """국내 종목코드 → 매핑표의 거래소 티커 후보(KOSE:A000660 · KOSDAQ:A263750)."""
    c = str(종목코드).strip().zfill(6)
    if 시장 and str(시장).upper().startswith("KOSDAQ"):
        return ["KOSDAQ:A%s" % c]
    if 시장 and str(시장).upper() in ("KOSPI", "유가", "유가증권"):
        return ["KOSE:A%s" % c]
    return ["KOSE:A%s" % c, "KOSDAQ:A%s" % c]


_국내꼴 = re.compile(r"^(?:(KRX|KOSE|KOSPI|KS|KOSDAQ|KQ)\s*:\s*)?A?(\d{6})$", re.I)


def 티커정규(t):
    """2026-10-24 W16 — 국내 티커 표기를 매핑표 꼴(KOSE:A000660 · KOSDAQ:A263750)로. `KRX:042700` · `KOSE:012450` · `A086520` ·
    `KOSDAQ:086520` · `012450` 을 모두 받는다(유니버스 조사 물결 실측). 국내 꼴이 아니면 그대로."""
    m = _국내꼴.match(("%s" % t).strip())
    if not m:
        return [t]
    시장 = (m.group(1) or "").upper()
    return 국내티커(m.group(2), "KOSDAQ" if 시장 in ("KOSDAQ", "KQ") else ("KOSPI" if 시장 in ("KOSE", "KOSPI", "KS") else None))


def 대상줄(거래소티커들):
    """대상회사의 매핑 → (줄, 지역, 매핑 행) · 못 찾으면 (None, None, 사유)."""
    후 = []
    for t in ([거래소티커들] if isinstance(거래소티커들, str) else 거래소티커들):
        for x in [t] + [y for y in 티커정규(t) if y != t]:
            if x not in 후:
                후.append(x)
    for t in 후:
        hits = 매핑(거래소티커=t)
        if hits:
            d = hits[0]
            지역 = 지역이름.get(str(d.get("Broad Group") or "").strip().lower(), "GLOBAL")
            return str(d.get("Industry Group") or "").strip(), 지역, d
    return None, None, "매핑표에 %s 가 없다 — `--회사` 로 영문 사명을 찾아 줄을 확인한다" % (거래소티커들,)


# S7R1-N3 — 산업 βU 는 **위험 동종(베타)의 대용**이다. 그 줄은 매핑표가 대상에 배정한 업종 줄 전체(사업 접점을 확인하지 않은 회사 수백 곳)라
# 운영 동종(매출총이익률 · 판관비율 · 회전일수 · 정상 마진 — C2 `운영지표`)의 자가 아니고, C1 핵심 표본도 아니다.
# 산출 · 가정 근거 칸에 이 표지를 함께 싣는다(산업 βU 로 내려간 회차가 그 줄의 마진 · 회전일수를 운영 동종으로 읽지 않게)
대용목적 = "위험동종 대용"
대용표지 = ("산업 βU — 위험 동종(베타)의 대용 · 매핑표 업종 줄 전체(사업 접점 미확인) · 운영 동종 아님(마진 · 회전일수 자로 쓰지 않는다) · "
        "C1 핵심 표본 아님(해외 동종 경로 ⑤ 를 열면 같은 줄의 미국 상장 회사를 SEC 사슬로 표본에 넣는다)")


def 동종줄(동종티커들):
    """동종(핵심 표본) 회사마다 매핑표 업종 줄 → (가장 많은 줄, 그 수, 매핑된 수, {줄: 수}). 동종 하나는 거래소 티커 후보 목록 또는 문자열."""
    import collections as _co
    셈, n = _co.Counter(), 0
    for t in 동종티커들 or []:
        try:
            줄, _지, _행 = 대상줄(t)
        except Exception:                                   # noqa: BLE001
            줄 = None
        if 줄:
            셈[줄] += 1
            n += 1
    if not 셈:
        return None, 0, 0, {}
    줄, 수 = 셈.most_common(1)[0]
    return 줄, 수, n, dict(셈)


def 사명줄(회사명):
    """사명으로 매핑 줄 찾기(2026-10-24 W18 · 결함 18 — 미국 ADR 티커가 매핑표에 없고 본국 상장 줄만 있을 때). 사명 열쇠가 같은 행 →
    (줄, 지역, 행) · 못 찾으면 (None, None, 사유). 여러 행이면 거래소 상장(장외 아님) 줄을 먼저."""
    열 = 사명열쇠(회사명 or "")
    if not 열:
        return None, None, "사명 없음"
    hits = [d for d in 매핑(찾기=(회사명 or "").split()[0]) if 사명열쇠(d.get("Company Name")) == 열]
    hits.sort(key=lambda d: str(d.get("Exchange:Ticker") or "").upper().startswith("OTC"))
    if not hits:
        return None, None, "매핑표에 사명 「%s」 없음" % 회사명
    d = hits[0]
    return str(d.get("Industry Group") or "").strip(), 지역이름.get(str(d.get("Broad Group") or "").strip().lower(), "GLOBAL"), d


def 대조값(거래소티커들, βU=None, 기준일=None, 줄이름=None, 지역=None, 동종=None, 회사명=None):
    """대상회사 매핑 줄의 산업 βU(현금보정) — GLOBAL · 지역 · US 셋과, βU(핵심 중앙값)가 둘(GLOBAL · 지역) 다에서 ±30% 밖인지.

    → dict(줄, 지역, 산업[{지역, βU현금보정, …}], 비교, ★, 문장). 줄이름 · 지역을 주면 매핑 대신 그것을 쓴다(사람이 정한 줄).
    `동종`(핵심 동종의 거래소 티커 목록)을 주면 동종 다수가 속한 매핑 줄이 대상 줄과 다를 때 그 줄로도 견준 `대안줄` 과 `분류경보` 를 단다
    (2026-10-24 W18 · 유니버스 조사 결함 12 — 다모다란이 대상을 사업과 다른 줄에 두어 거짓 ★ 가 섰다. ★ 는 그대로 두고 사람이 줄을 정한다 — `--산업줄`)."""
    if 동종 and βU is not None:
        out = 대조값(거래소티커들, βU, 기준일, 줄이름, 지역)
        if not out.get("줄"):
            return out
        대안, 수, n, 분포 = 동종줄(동종)
        if 대안 and 대안.strip().lower() != out["줄"].strip().lower() and 수 >= 2 and 수 * 2 >= n:
            alt = 대조값(None, βU, 기준일, 대안, out.get("지역"))
            out["대안줄"] = {"줄": 대안, "근거": "핵심 동종 %d곳 가운데 %d곳의 매핑 줄(%s)" % (n, 수, " · ".join("%s %d" % kv for kv in sorted(분포.items(), key=lambda x: -x[1]))),
                          "비교": alt.get("비교"), "★": alt.get("★"), "문장": alt.get("문장")}
            out["분류경보"] = ("대상 매핑 줄 「%s」 과 핵심 동종 다수의 줄 「%s」 이 다르다 — 다모다란 회사 분류가 사업과 다를 수 있다%s. "
                            "어느 줄로 견줄지는 사람이 정한다(`--산업줄 \"%s\"`)" % (out["줄"], 대안,
                                                                       " · 동종 줄로는 ±%d%% 안" % (대조폭 * 100) if out.get("★") and not alt.get("★") else "", 대안))
            out["문장"] = "%s — ※ %s" % (out.get("문장") or "", out["분류경보"])
        return out
    매핑행 = None
    사명으로 = False
    if not 줄이름:
        줄이름, 지역, 매핑행 = 대상줄(거래소티커들) if 거래소티커들 else (None, None, "티커 없음")
        if not 줄이름 and 회사명:                        # ADR 티커 → 본국 상장 줄(사명 대조) — 빈칸 대신
            줄이름, 지역, 행2 = 사명줄(회사명)
            if 줄이름:
                매핑행, 사명으로 = 행2, True
        if not 줄이름:
            return {"줄": None, "지역": None, "산업": [], "★": False, "문장": "산업 βU 대조 불가 — %s" % 매핑행}
    지역 = (지역 or "GLOBAL").upper()
    산업 = []
    for 곳 in dict.fromkeys(["GLOBAL", 지역, "US"]):
        try:
            x = 산업줄(줄이름, 곳, 기준일)
        except SystemExit as e:
            x = {"지역": 곳, "줄": 줄이름, "βU현금보정": None, "오류": str(e)}
        except Exception as e:                              # noqa: BLE001
            x = {"지역": 곳, "줄": 줄이름, "βU현금보정": None, "오류": type(e).__name__}
        if x:
            산업.append(x)
    out = {"줄": 줄이름, "지역": 지역, "매핑": ({k: 매핑행.get(k) for k in ("Company Name", "Exchange:Ticker", "Industry Group",
                                                                    "Country", "Broad Group")} if isinstance(매핑행, dict) else None),
           "산업": 산업, "대조폭": 대조폭, "★": False, "비교": [], "목적": 대용목적, "대용표지": 대용표지}
    if 사명으로:
        out["매핑경로"] = "티커가 매핑표에 없어 사명으로 찾은 줄(%s — ADR · 다른 시장 상장)" % (매핑행 or {}).get("Exchange:Ticker")
    if βU is None:
        out["문장"] = "산업 βU(현금보정) %s — %s" % (" · ".join("%s %s" % (x["지역"], ("%.3f" % x["βU현금보정"]) if x.get("βU현금보정") else "-")
                                                         for x in 산업), 대용목적)
        return out
    기준들 = [x for x in 산업 if x["지역"] in ("GLOBAL", 지역) and x.get("βU현금보정")]
    for x in 기준들:
        out["비교"].append({"지역": x["지역"], "산업βU": x["βU현금보정"], "비": βU / x["βU현금보정"]})
    밖 = [c for c in out["비교"] if abs(c["비"] - 1) > 대조폭]
    out["★"] = bool(기준들) and len(밖) == len(out["비교"])
    out["문장"] = ("핵심 중앙값 βU %.3f 대 다모다란 「%s」 현금보정 βU %s%s" % (
        βU, 줄이름, " · ".join("%s %.3f(%.0f%%)" % (c["지역"], c["산업βU"], c["비"] * 100) for c in out["비교"]) or "없음",
        " — ★ 둘 다 ±%d%% 밖(표본이 업종 위험을 못 담는지 본다 — 해외 동종 경로 · 산업 βU 대안 사양)" % (대조폭 * 100)
        if out["★"] else ""))
    return out


def 해외후보(줄이름, 거래소접두=미국거래소, 제외국가=None):
    """같은 매핑 줄의 미국 상장 회사(해외 동종 경로 ⑤ — SEC 사슬로 재료를 받는다). [{티커, 회사명, 국가, SIC}]."""
    p = 받기(매핑파일, 조용=True)
    행들 = 표읽기(p, "By company name")
    h = 머리찾기(행들)
    머리줄 = [str(x).strip() for x in 행들[h]]
    out = []
    for 줄 in 행들[h + 1:]:
        d = {머리줄[i]: 줄[i] for i in range(min(len(머리줄), len(줄)))}
        if str(d.get("Industry Group") or "").strip().lower() != 줄이름.strip().lower():
            continue
        t = str(d.get("Exchange:Ticker") or "").strip()
        if not any(t.startswith(x) for x in 거래소접두):
            continue
        if 제외국가 and str(d.get("Country") or "").strip() in 제외국가:
            continue
        out.append({"티커": t.split(":", 1)[1], "거래소": t.split(":", 1)[0], "회사명": d.get("Company Name"),
                    "국가": d.get("Country"), "SIC": str(d.get("SIC Code") or "").split(".")[0], "경로": "⑤"})
    return out


_사명꼬리 = {"CO", "COMPANY", "CORP", "CORPORATION", "INC", "INCORPORATED", "LTD", "LIMITED", "PLC", "NV", "SA", "AG", "SE", "KK",
           "HOLDINGS", "HOLDING", "GROUP", "THE", "CO.,LTD", "ADR", "ADS", "SPA", "AB", "ASA", "OYJ", "BHD", "TBK", "PCL",
           # 2026-10-24 W18 — 「S.A.」 · 「N.V.」 · 「S.A.B. de C.V.」 · 「KGaA」 · 「LLC」 꼴(유니버스 조사 — MT 가 SEC 밖으로 갈렸다)
           "SAB", "CV", "KGAA", "LLC", "LP", "BV", "SAS", "SPA", "AS", "NPV"}
미국상장차례 = ("NYSE:", "NasdaqGS:", "NasdaqGM:", "NYSEAM:", "NasdaqCM:", "NYSEArca:", "BATS:")


def 사명열쇠(이름):
    """회사명 → 견줄 열쇠(대문자 · 기호 · 법인 꼬리 뺌). 「Toyota Motor Corporation」 = 「TOYOTA MOTOR CORP」."""
    import re as _re
    s = _re.sub(r"\([^)]*\)", " ", "%s" % 이름)                # 매핑표 사명 끝의 「(NYSE:APH)」 를 뗀다
    s = _re.sub(r"(?<=[A-Za-z])\.(?=[A-Za-z]\.)|(?<=\b[A-Za-z])\.(?=[A-Za-z]\b)|(?<=\b[A-Za-z])\.(?=[\s,]|$)", "", s)   # 「S.A.」 · 「N.V.」 → SA · NV(2026-10-24 W18)
    낱 = [w for w in _re.sub(r"[^A-Z0-9 ]", " ", s.upper().replace("&", " AND ")).split() if w and w not in _사명꼬리]
    return " ".join(낱)


sec명부주소 = "https://www.sec.gov/files/company_tickers_exchange.json"     # {fields: [cik, name, ticker, exchange], data: [...]}


def sec명부읽기(경로들):
    """SEC 명부(사명이 든 꼴 — company_tickers_exchange.json · 원본 company_tickers.json) 있는 첫 자리 → {사명열쇠: SEC 티커}.
    사명이 없는 줄인 꼴({cik: [티커]})은 건너뛴다. 없으면 {}."""
    for p in 경로들:
        if not (p and os.path.exists(p)):
            continue
        try:
            d = json.load(io.open(p, encoding="utf-8"))
        except (OSError, ValueError):
            continue
        낸 = {}
        if isinstance(d, dict) and isinstance(d.get("fields"), list) and isinstance(d.get("data"), list):
            f = d["fields"]
            i이, i티 = f.index("name") if "name" in f else 1, f.index("ticker") if "ticker" in f else 2
            i거 = f.index("exchange") if "exchange" in f else None
            for r in d["data"]:
                if len(r) > max(i이, i티) and r[i이] and r[i티]:
                    거 = (r[i거] if (i거 is not None and len(r) > i거) else None) or ""
                    k = 사명열쇠(r[i이])
                    if k not in 낸 or ((거 in ("NYSE", "Nasdaq")) and 낸[k][1] not in ("NYSE", "Nasdaq")):   # 거래소 상장 줄을 장외 줄보다 앞에
                        낸[k] = (r[i티], 거)
        else:
            for v in (d.values() if isinstance(d, dict) else d):
                if isinstance(v, dict) and v.get("title") and v.get("ticker"):
                    낸.setdefault(사명열쇠(v["title"]), (v["ticker"], ""))
        if 낸:
            return 낸
    return {}


def sec명부받기(자리):
    """SEC company_tickers_exchange.json 을 자리(공용 캐시 파일)에 받는다 — SEC_CONTACT_EMAIL 이 있을 때만(값은 찍지 않는다). → 자리 또는 None."""
    if os.path.exists(자리):
        return 자리
    연락 = os.environ.get("SEC_CONTACT_EMAIL")
    if not 연락:
        return None
    try:
        import requests                                         # noqa: PLC0415
        r = requests.get(sec명부주소, headers={"User-Agent": "DCF-research %s" % 연락}, timeout=60)
        if r.status_code != 200:
            return None
        os.makedirs(os.path.dirname(자리), exist_ok=True)
        io.open(자리, "w", encoding="utf-8").write(r.text)
        return 자리
    except Exception:                                           # noqa: BLE001
        return None


def 세계후보(줄이름, sec명부=None, 언급=None, 장외뺌=True):
    """같은 매핑 줄의 **전 세계** 상장 회사(해외 동종 경로 ⑤ · 2026-10-24 W15 — 종전 `해외후보` 는 미국 거래소 1차 상장만 보아
    동종이 일본 · 대만 · 유럽에 상장된 업종(전자부품 · 완성차 · 파운드리)에서 소형 미국 회사로만 채워졌다).
    회사마다 `SEC` 를 단다 — 「미국 상장」(1차 상장) · 「SEC 신고(ADR · 20-F)」(사명이 SEC 명부와 맞는 외국 회사 — SEC 사슬로 재료를 받는다) ·
    「SEC 밖」(사슬로 못 받는다 — 위험 동종은 다모다란 지역 산업 βU 대용 · 운영 동종은 공시 · IR 에서 손으로).
    차례: B1 이 거론한 회사(`언급` — 사명 열쇠 일치) → SEC 신고 외국 회사 → 미국 상장(거래소 층) → SEC 밖. 장외(OTC*)는 뺀다."""
    p = 받기(매핑파일, 조용=True)
    행들 = 표읽기(p, "By company name")
    h = 머리찾기(행들)
    머리줄 = [str(x).strip() for x in 행들[h]]
    언급열쇠 = {사명열쇠(x) for x in (언급 or []) if x}
    sec명부 = sec명부 or {}
    out = []
    for 줄 in 행들[h + 1:]:
        d = {머리줄[i]: 줄[i] for i in range(min(len(머리줄), len(줄)))}
        if str(d.get("Industry Group") or "").strip().lower() != 줄이름.strip().lower():
            continue
        t = str(d.get("Exchange:Ticker") or "").strip()
        if ":" not in t or (장외뺌 and t.upper().startswith("OTC")):
            continue
        거, 티 = t.split(":", 1)
        열 = 사명열쇠(d.get("Company Name"))
        if any(t.startswith(x) for x in 미국거래소):
            sec, sec티커 = "미국 상장", 티
        elif 열 in sec명부:
            sec티커, sec거 = sec명부[열] if isinstance(sec명부[열], tuple) else (sec명부[열], "")
            sec = "SEC 신고(ADR · 20-F)" if sec거 in ("NYSE", "Nasdaq") else "SEC 명부(장외 — 20-F 신고인이 아닐 수 있다)"
        else:
            sec, sec티커 = "SEC 밖", None
        out.append({"티커": sec티커 or 티, "거래소": 거, "현지티커": 티, "회사명": d.get("Company Name"), "국가": d.get("Country"),
                    "SIC": str(d.get("SIC Code") or "").split(".")[0], "경로": "⑤", "SEC": sec, "B1거론": 열 in 언급열쇠})

    def 차(x):
        층 = next((i for i, 접 in enumerate(미국상장차례) if (x["거래소"] + ":").startswith(접)), len(미국상장차례))
        return (not x["B1거론"], {"SEC 신고(ADR · 20-F)": 0, "미국 상장": 1, "SEC 명부(장외 — 20-F 신고인이 아닐 수 있다)": 2, "SEC 밖": 3}[x["SEC"]],
                층, "%s" % x["회사명"])
    return sorted(out, key=차)


def 산업(a):
    p = 받기(지역표[a.지역.upper()])
    행들 = 표읽기(p)
    h = 머리찾기(행들)
    머리줄 = [str(x).strip() for x in 행들[h]]
    판 = 판정보(p, a.기준일)
    print("파일 %s · 머리행 %d · 파일 갱신일 %s · 받은 날 %s%s" % (os.path.basename(p), h + 1, 판["파일갱신일"], 판["받은날"],
                                                       (" · ⚠ " + 판["경보"]) if 판["경보"] else ""))
    if a.목록:
        for 줄 in 행들[h + 1:]:
            if 줄 and str(줄[0]).strip():
                print("  %s" % str(줄[0]).strip())
        return
    찾을 = [s.lower() for s in a.산업]
    낸것 = []
    for 줄 in 행들[h + 1:]:
        이름 = str(줄[0]).strip()
        if 이름.lower() in 찾을:
            항 = {머리줄[i]: 줄[i] for i in range(min(len(머리줄), len(줄)))}
            낸것.append((이름, 항))
    if not 낸것:
        print("못 찾음 — `--목록` 으로 그 지역의 줄 이름을 먼저 보십시오")
        return
    칸 = [k for k in 머리줄 if k and ("firm" in k.lower() or "beta" in k.lower()
                                     or "d/e" in k.lower() or "tax" in k.lower()
                                     or "cash" in k.lower())]
    for 이름, 항 in 낸것:
        print()
        print("── %s" % 이름)
        for k in 칸:
            v = 항.get(k)
            print("   %-42s %s" % (k[:42], ("%.4f" % v) if isinstance(v, float) else v))
    print()
    print("**쓸 값은 「Unlevered beta corrected for cash」다.** 그 줄이 없으면 "
          "「Unlevered beta」를 쓰고 현금비중을 따로 적는다.")
    print("**이 파일의 무차입베타는 그 지역의 한계세율로 벗긴 값이다** — 한국 세율로 다시 "
          "벗기려면 Beta ÷ (1+(1−t)(D/E)) 뒤 ÷ (1−현금비중) 을 직접 한다.")


def 회사(a):
    낸것 = 매핑(찾기=a.회사)
    if not 낸것:
        print("매핑표에서 「%s」를 못 찾았습니다 — 영문 사명으로 다시 찾아 보십시오" % a.회사)
        return
    print("매핑표에서 %d건" % len(낸것))
    for 항 in 낸것[:12]:
        print("  " + " | ".join("%s=%s" % (k, 항[k]) for k in list(항)[:6] if 항.get(k) != ""))
    print()
    print("**이 줄과 지역을 그대로 쓴다.** 이름이 그럴듯한 다른 줄을 고르지 않는다.")


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--지역", default="GLOBAL", help="GLOBAL / EM / JAPAN / US")
    ap.add_argument("--산업", nargs="*", default=[])
    ap.add_argument("--회사", default=None, help="매핑표에서 그 회사의 산업 줄을 찾는다")
    ap.add_argument("--대상", default=None, help="대상회사 거래소 티커(KOSE:A000660 · NasdaqGS:MU) 또는 국내 종목코드 6자리")
    ap.add_argument("--βU", type=float, default=None, help="--대상 과 함께 — 유사기업 핵심 중앙값 βU 를 산업 βU 와 대조(±30%%)")
    ap.add_argument("--해외후보", action="store_true", help="--대상 의 매핑 줄에서 미국 상장 회사를 낸다(경로 ⑤)")
    ap.add_argument("--기준일", "--평가기준일", dest="기준일", default=None, help="평가기준일 T(분석일 · 시장 쪽 — 종가 · 시가총액 · 주식수 · 베타 창 끝 · 환율 · 법령 시행일) YYYY-MM-DD — 판 갱신일과의 차를 적는다")
    ap.add_argument("--목록", action="store_true")
    a = ap.parse_args()
    if a.대상:
        티커들 = 국내티커(a.대상) if a.대상.isdigit() else [a.대상]
        r = 대조값(티커들, a.βU, a.기준일)
        print(json.dumps({k: v for k, v in r.items()}, ensure_ascii=False, indent=1, default=str))
        if a.해외후보 and r.get("줄"):
            후보 = 해외후보(r["줄"])
            print("── 「%s」 미국 상장 %d곳(경로 ⑤ — SEC 사슬 명단)" % (r["줄"], len(후보)))
            for x in 후보:
                print("  %-8s %-10s %-40s %s" % (x["티커"], x["거래소"], str(x["회사명"])[:40], x["국가"]))
    elif a.회사:
        회사(a)
    elif a.산업 or a.목록:
        산업(a)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()

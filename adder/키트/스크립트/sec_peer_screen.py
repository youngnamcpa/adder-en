# -*- coding: utf-8 -*-
"""미국 유사기업 2차 컷 — 시가총액 조립과 규모대 판정. 캐시 전용, 네트워크 0회.

**이게 미국 경로에 마지막으로 남아 있던 손 글루다(HWO-56).** 사슬(HWO-55)이 수집을
층 단위로 묶은 뒤에도, 「중간 층 캐시 → 후보별 시가총액 → 규모대 컷」 사이를
에이전트가 후보 한 곳씩 손으로 이었다. 실측(릴리 2026-06-30 회차, 후보 59곳):
C 갈래 55분 중 **10초 이상 멈춰 있던 시간이 2,725초(82.7%)** 였고, 가장 긴 멈춤이
시가총액_예비 → 주식수_직접조회 → 시가총액_확정 사이의 약 7분이었다 — 수집(전송)은
전체의 6~11%뿐이다. 마이크론 회차도 70.3%가 같은 자리였다.

**손 조립은 느리기만 한 게 아니라 틀린다.** 마이크론 회차의 손 조립은 TSM 시가총액을
11,017bn 으로 세웠다 — 보통주 25,932,524,521주(ADS 배율 미확정)에 ADS 종가를 그대로
곱한 값으로, 실제(약 1,100bn)의 5배다. 그 회차는 규모대 밖이라 결론이 안 바뀌었지만,
밴드 경계에 걸친 후보였다면 표본이 조용히 어긋났다. **이 스크립트가 나온 뒤로
시가총액을 손으로 곱해 만드는 것을 금지한다**(유사기업-선정 스킬 HWO-52).

**컷의 기준(밴드)은 이 스크립트의 소유가 아니다** — 값을 보기 전에 회차가 선언하고,
여기는 선언된 밴드를 받아 판정만 한다. 밴드 없이 돌리면 조립표만 쓰고 판정은 비운다.

읽는 캐시(전부 `_raw/peers/`, 사슬 싼층·중간이 이미 받아 둔 것):
    sub_<티커>.json               회사명·sic·최근서류(20-F/40-F 로 외국 신고인 판별)
    shares_<티커>.json            dei 표지 유통·us-gaap 발행·자기주식
    frame_dei_shares_<CCP>.json   frames 창구의 표지 유통 전수 — 있으면 더 새 값 채택
    ads_<티커>.json               ADS 배율(외국 신고인)
    종가_<YYYYMMDD>.json          기준일 종가 사전
    주식수_대체.json              사람이 확정한 분모 {티커: [주식수, 기준일, 종류, 비고]}
                                  주식수 null 은 「시가총액을 세우지 않는다」는 확정이다

분모를 고르는 순서 — 값마다 근거 칸(분모종류·주식수기준일·주식수비고)에 남는다:
    ⓪ 주식수_대체.json 이 그 티커를 확정했으면 그 값 (사람의 확정이 항상 이긴다)
    ① frames dei 표지 유통 · shares 의 dei 표지 유통 · us-gaap 발행−자기주식 중
       **기준일이 가장 새 것** (dei 를 골랐는데 자기주식이 따로 보고돼 있으면 비고에 적는다)

자동 확정을 거부하는 세 자리 — 그럴듯해 보이는 틀린 값을 만들지 않는다(HWO-52):
    · 외국 신고인(20-F·40-F)의 ADS 배율 ≠ 1 → **후보 시총 둘(그대로/나눔)을 사유에 적고
      세우지 않는다.** 표지 문장으로 사람이 주식수_대체.json 에 확정한다(TM ÷10 실측)
    · ADS 배율 확인 불가(외국 신고인인데 ads 캐시가 비었거나 없음) → 세우지 않는다
    · 주식수 기준일이 평가기준일에서 **1년 넘게 묵으면** 세우지 않는다 — 묵은 주식수 ×
      오늘 종가는 그럴듯해 보이는 틀린 값이다(HMC 2020년·F 2011년 실측). 주식수_대체로
      확정한 값도 이 문은 못 지난다(사유에 값은 남긴다)

사용법 (사슬의 중간 층과 비싼 층 사이):
    python 스크립트/sec_peer_screen.py --명단 1차통과.json --기준일 2026-06-30 \\
           --대상 LLY --대상주식수 941357065 --밴드배수 5
    python 스크립트/sec_peer_screen.py --명단 1차통과.json --기준일 2026-06-30 \\
           --대상 MU --대상주식수 1129000000 --밴드 208.53,5213.27      # bn USD 직접 선언

산출(캐시 폴더에):
    2차스크린.json        조립표 전체 + 통과/탈락(분류·사유) — 탈락도 조용히 안 뺀다
    2차통과_명단.json     통과분 [{"티커": ...}] — 사슬 비싼 층의 --명단 으로 그대로 쓴다
                          (조립 산출물 2차통과.json 과 이름을 일부러 갈랐다 — 덮임 방지)
"""
from __future__ import annotations

import argparse
import datetime as dt
import glob
import io
import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import 피어경로 as 피경  # noqa: E402 — 명단 경로 · 종가 파일 이름 한 규칙(2026-10-24 W15)

sys.stdout.reconfigure(encoding="utf-8")
여기 = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(여기)


def _읽기(경로):
    with io.open(경로, encoding="utf-8") as f:
        return json.load(f)


def _캐시읽기(캐시, 이름):
    p = os.path.join(캐시, 이름)
    return _읽기(p) if os.path.exists(p) else None


def _날짜(s):
    try:
        return dt.date.fromisoformat(str(s)[:10])
    except (ValueError, TypeError):
        return None


def _bn(값):
    return f"{값 / 1e9:,.2f}"


def frames_색인(캐시):
    """frame_dei_shares_*.json → {cik: (end, val, ccp)} — cik 마다 가장 새 것만."""
    색인 = {}
    for p in sorted(glob.glob(os.path.join(캐시, "frame_dei_shares_*.json"))):
        d = _읽기(p)
        ccp = d.get("ccp", os.path.basename(p))
        for 행 in d.get("data", []):
            cik, end, val = 행.get("cik"), 행.get("end"), 행.get("val")
            if cik is None or not end or not val:
                continue
            기존 = 색인.get(cik)
            if 기존 is None or end > 기존[0]:
                색인[cik] = (end, val, ccp)
    return 색인


def 분모찾기(캐시, 티커, cik, f색인, 기준일=None):
    """대체를 뺀 자동 후보 중 기준일이 가장 새 분모 하나.

    반환: (주식수, 기준일, 분모종류, 비고) — 없으면 (None, None, None, 사유)
    """
    후보 = []                                    # (기준일, 주식수, 종류, 비고)
    sh = _캐시읽기(캐시, f"shares_{티커}.json")
    자기 = (sh or {}).get("자기주식") or None
    if cik is None and sh:
        cik = sh.get("cik")
    if cik is not None and cik in f색인:
        end, val, ccp = f색인[cik]
        후보.append((end, val, f"유통(dei 표지 · frames {ccp})", ""))
    if sh:
        dei = sh.get("유통_dei") or {}
        if dei.get("val") and dei.get("end"):
            후보.append((dei["end"], dei["val"], "유통(dei 표지)", ""))
        발행 = sh.get("발행_usgaap") or {}
        if 발행.get("val") and 발행.get("end"):
            if 자기 and 자기.get("val") and 자기.get("end") == 발행["end"]:
                후보.append((발행["end"], 발행["val"] - 자기["val"],
                           "발행−자기주식(us-gaap)", ""))
            elif not 자기:
                # 자기주식 태그가 아예 없으면 발행=유통일 수도, 미보고일 수도 있다 —
                # 그대로 쓰되 비고에 남긴다. 자기주식이 있는데 기준일이 어긋나면
                # 발행만으로는 유통을 못 만드니 후보에서 뺀다(과대평가 방지).
                후보.append((발행["end"], 발행["val"],
                           "발행(us-gaap · 자기주식 미보고)", "자기주식 태그 없음"))
    # 2026-10-24 W18 — 기준일 뒤 시점의 분모(기준일 뒤에 낸 10-K · 10-Q 표지 · frames 창구)를 기준일 자료로 쓰지 않는다
    if 기준일:
        기준일 = 기준일.isoformat() if hasattr(기준일, "isoformat") else ("%s" % 기준일)
        뒤 = [x for x in 후보 if x[0] > 기준일]
        후보 = [x for x in 후보 if x[0] <= 기준일]
        if not 후보 and 뒤:
            return None, None, None, "유통주식수 확인 불가 — 분모가 기준일 뒤 시점뿐(%s)" % ", ".join("%s %s" % (x[2], x[0]) for x in 뒤[:3])
    if sh:
        for 칸 in ("유통_dei", "발행_usgaap"):
            if (sh.get(칸) or {}).get("기준일뒤"):
                후보 = [(e, v, 종 + " · 기준일 뒤 제출(%s)" % (sh[칸].get("filed") or "?") if e == sh[칸].get("end") and 종.startswith(("유통(dei 표지)", "발행")) else 종, 비)
                      for e, v, 종, 비 in 후보]
    if not 후보:
        return None, None, None, "유통주식수 확인 불가 (shares·frames 캐시에 분모 없음)"
    후보.sort(key=lambda x: x[0], reverse=True)
    기준일, 주식수, 종류, 비고 = 후보[0]
    if 종류.startswith("유통(dei") and 자기 and 자기.get("val"):
        추가 = f"자기주식 {자기['val']:,}주 별도 보고 — dei 표지 값은 유통 기준"
        비고 = f"{비고} · {추가}" if 비고 else 추가
    return 주식수, 기준일, 종류, 비고


def 후보조립(캐시, 티커, 기준일, 종가사전, f색인, 대체, 경로표시):
    """후보 한 곳의 시가총액 행. 세울 수 없으면 사유를 행에 남긴다 — 조용히 안 뺀다."""
    sub = _캐시읽기(캐시, f"sub_{티커}.json") or {}
    최근 = sub.get("최근서류") or {}
    외국 = any(폼 in 최근 for 폼 in ("20-F", "40-F"))
    서식 = next((폼 for 폼 in ("10-K", "10-Q", "20-F", "40-F") if 폼 in 최근), "")
    ads = _캐시읽기(캐시, f"ads_{티커}.json") or {}
    배율 = ads.get("ADS비율")
    행 = {
        "티커": 티커,
        "회사명": sub.get("name"),
        "경로": 경로표시,
        "서식": 서식,
        "sic": sub.get("sic"),
        "sic설명": sub.get("sicDescription"),
        "ADS비율": 배율,
        "주식수": None, "주식수기준일": None, "분모종류": None, "주식수비고": "",
        "종가": None, "종가일": None,
        "시가총액": None,
        "판정": None, "분류": None, "사유": None,
    }

    def 못세움(분류, 사유):
        행["판정"], 행["분류"], 행["사유"] = "탈락", 분류, 사유
        return 행

    종가행 = 종가사전.get(티커) or {}
    종가, 종가일 = 종가행.get("종가"), 종가행.get("일자")
    행["종가"], 행["종가일"] = 종가, 종가일
    if not 종가:
        return 못세움("2. 자료 부재", "기준일 종가 확인 불가 → 시가총액 산출 불가")
    if 종가행.get("일치") is False:
        행["주식수비고"] = f"종가 일자 {종가일} — 기준일 불일치(직전 거래일)"

    확정 = (대체 or {}).get(티커)
    if 확정 is not None:
        주식수, 주식수일, 종류, 비고 = (확정 + [None] * 4)[:4]
        if 주식수 is None:
            return 못세움("2. 자료 부재", f"주식수_대체 확정: 시가총액을 세우지 않는다 — {비고}")
        행["분모종류"] = f"{종류} (주식수_대체)"
        비고합 = f"주식수_대체: {비고}" if 비고 else "주식수_대체 확정"
        행["주식수비고"] = f"{행['주식수비고']} · {비고합}" if 행["주식수비고"] else 비고합
    else:
        주식수, 주식수일, 종류, 비고 = 분모찾기(캐시, 티커, sub.get("cik"), f색인, 기준일)
        if 주식수 is None:
            return 못세움("2. 자료 부재", f"{비고} → 시가총액 산출 불가")
        행["분모종류"] = 종류
        if 비고:
            행["주식수비고"] = f"{행['주식수비고']} · {비고}" if 행["주식수비고"] else 비고
        # ADS 문 — 배율이 1로 확정된 경우에만 자동으로 지나간다.
        # 외국 신고인(20-F/40-F)만이 아니다: **10-K 신고인인데 상장증권이 ADS 인 회사가
        # 있다**(실측: ONC/BeOne — 1 ADS = 보통주 13. 안 나누면 시총 439bn 으로 JNJ 보다
        # 커져 규모대를 통과한다. 실제 32bn). ads 캐시에 1 아닌 배율이 있으면 서식과
        # 무관하게 세운다. ads 캐시가 아예 없는 10-K ADS 상장은 이 문이 못 잡는다 —
        # 시총이 규모대 경계에 걸친 후보는 dei/EntityListingDepositoryReceiptRatio 를
        # 확인하고 주식수_대체.json 으로 확정하라(스킬 HWO-52).
        if 외국 or (배율 is not None and 배율 != 1):
            if 배율 is None:
                return 못세움("2. 자료 부재",
                            "외국 신고인인데 ADS 배율 확인 불가 — 표지 문장으로 확정해 "
                            "주식수_대체.json 에 적기 전에는 시가총액을 세우지 않는다")
            if 배율 != 1:
                그대로 = 주식수 * 종가
                나눔 = 주식수 / 배율 * 종가
                return 못세움("2. 자료 부재",
                            f"ADS 배율 {배율} — 자동 확정 금지. 후보 시총 둘: 그대로 "
                            f"{_bn(그대로)} bn / 배율로 나눔 {_bn(나눔)} bn. 표지 문장으로 "
                            f"확인해 주식수_대체.json 에 확정한다 (분모 {주식수:,} · {주식수일})")

    행["주식수"], 행["주식수기준일"] = 주식수, 주식수일

    # 묵은 주식수 문 — 사람의 확정도 이 문은 못 지난다
    d = _날짜(주식수일)
    if d is None:
        return 못세움("2. 자료 부재", f"주식수 기준일({주식수일})을 날짜로 못 읽음 → 세우지 않는다")
    묵은일수 = (기준일 - d).days
    if 묵은일수 > 365:
        참고 = _bn(주식수 * 종가)
        return 못세움("2. 자료 부재",
                    f"주식수 기준일 {주식수일} 이 평가기준일에서 {묵은일수}일 묵음 — 묵은 "
                    f"주식수 × 오늘 종가({참고} bn)는 그럴듯해 보이는 틀린 값이라 세우지 않는다")

    행["시가총액"] = 주식수 * 종가
    return 행


def main() -> None:
    ap = argparse.ArgumentParser(allow_abbrev=False, description="미국 유사기업 2차 컷 — 캐시 전용 시가총액 조립·판정")
    ap.add_argument("--명단", default="1차통과.json",
                    help="[{'티커': ...}] 꼴 파일 (캐시 폴더 기준 상대경로 허용)")
    ap.add_argument("--tickers", default=None, help="티커를 쉼표로 직접")
    ap.add_argument("--기준일", "--평가기준일", dest="기준일", required=True, help="평가기준일 T(분석일 · 시장 쪽 — 종가 · 시가총액 · 주식수 · 베타 창 끝 · 환율 · 법령 시행일) YYYY-MM-DD")
    ap.add_argument("--대상", required=True, help="대상회사 티커")
    ap.add_argument("--대상주식수", type=float, default=None,
                    help="대상 유통주식수. 없으면 캐시의 대상.json 에서 읽는다")
    ap.add_argument("--밴드", default=None,
                    help="선언한 규모대 하한,상한 (bn USD). 예: 208.53,5213.27")
    ap.add_argument("--밴드배수", type=float, default=None,
                    help="대상시총 ÷N ~ ×N 을 밴드로. --밴드와 같이 주면 죽는다")
    ap.add_argument("--캐시", default=os.path.join(ROOT, "_raw", "peers"))
    ap.add_argument("--출력", default="2차스크린.json")
    ap.add_argument("--통과출력", default="2차통과_명단.json",
                    help="사슬 비싼 층 --명단 용. 조립 산출물(2차통과.json)과 겹치면 죽는다")
    a = ap.parse_args()

    캐시 = a.캐시
    기준일 = dt.date.fromisoformat(a.기준일)
    ymd = a.기준일.replace("-", "")

    종가사전 = 피경.종가읽기(캐시, ymd) or None
    if 종가사전 is None:
        sys.exit(f"종가_{ymd}.json 이 캐시({캐시})에 없습니다. 사슬 중간 층을 먼저 돌리십시오.")

    # 명단
    if a.tickers:
        티커들 = [t.strip().upper() for t in a.tickers.split(",") if t.strip()]
        경로들 = {}
    else:
        p = 피경.명단경로(a.명단, 캐시, ROOT)
        # 2026-10-24 W17 — C1 핵심표본(dict) · {"tickers": […]} 꼴도 `핵심표본읽기` 로 편다(AMD 조사 — 사전 꼴 명단을 목록으로 읽다 AttributeError).
        # 운영 동종 전용(βU 를 안 세우는 회사)은 스크린(시가총액 규모대)에서 뺀다 — 겸운영(위험 동종이기도 한 회사)은 남긴다
        import 핵심표본읽기 as _hr
        원 = _hr.목록꼴(_읽기(p))
        if isinstance(원, dict):
            목록 = _hr.명단(원, ("핵심", "예비"), "US")
        else:
            목록 = [(x if isinstance(x, dict) else {"티커": x}) for x in (원 or [])]
        목록 = [dict(x, 티커=(x.get("티커") or x.get("ticker") or x.get("Ticker"))) for x in 목록 if isinstance(x, dict)]
        티커들 = [("%s" % x["티커"]).upper() for x in 목록 if x.get("티커")]
        경로들 = {("%s" % x["티커"]).upper(): x.get("경로", "") for x in 목록 if x.get("티커")}
    티커들 = [t for t in 티커들 if t != a.대상.upper()]
    if not 티커들:
        sys.exit("명단이 비었습니다.")

    # 대상 시가총액 — 규모대의 기준값. 못 세우면 밴드배수를 못 만든다
    대상 = a.대상.upper()
    대상주식수 = a.대상주식수
    if 대상주식수 is None:
        대상파일 = _캐시읽기(캐시, "대상.json") or {}
        if 대상파일.get("티커", "").upper() == 대상:
            대상주식수 = 대상파일.get("주식수")
    if not 대상주식수:
        # 2026-10-24 W17 — 사슬 중간 단계가 받아 둔 shares_<대상>.json · frames 표지에서 후보와 같은 규칙으로 고른다(AVGO 조사 — 손으로 넘겼다)
        주, 날, 종, _비 = 분모찾기(캐시, 대상, None, frames_색인(캐시), 기준일)
        if 주:
            대상주식수 = 주
            print(f"  대상 주식수 {주:,.0f} — {종} {날} (shares_{대상}.json · frames)")
    if not 대상주식수:
        sys.exit("--대상주식수가 없고 캐시의 대상.json · shares_%s.json · frames 표지에도 없습니다." % 대상)
    대상종가 = (종가사전.get(대상) or {}).get("종가")
    if not 대상종가:
        # 2026-10-24 W17 — 대상 종가가 없으면 멈추지 않고 한 번 받아 온다(AMD · META · RKLB 조사 — 중간 층이 명단 회사만 받았다)
        import subprocess as _sp
        _sp.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "peer_기준일종가.py"),
                 "--기준일", ymd, "--추가", 대상], capture_output=True, text=True, encoding="utf-8",
                env=dict(os.environ, PYTHONIOENCODING="utf-8", DCF_PEER_CACHE=캐시), cwd=ROOT)
        종가사전 = 피경.종가읽기(캐시, ymd) or {}
        대상종가 = (종가사전.get(대상) or {}).get("종가")
    if not 대상종가:
        sys.exit(f"대상({대상})의 기준일 종가가 종가_{ymd}.json 에 없습니다(peer_기준일종가.py --추가 {대상} 도 실패).")
    대상시총 = 대상주식수 * 대상종가

    # 밴드 — 값을 보기 전에 선언된 것을 받기만 한다
    if a.밴드 and a.밴드배수:
        sys.exit("--밴드와 --밴드배수를 같이 줄 수 없습니다. 선언은 하나입니다.")
    밴드 = None
    if a.밴드:
        하한, 상한 = (float(x) * 1e9 for x in a.밴드.split(","))
        밴드 = (하한, 상한, f"직접 선언 {a.밴드} bn")
    elif a.밴드배수:
        밴드 = (대상시총 / a.밴드배수, 대상시총 * a.밴드배수,
              f"대상시총 {_bn(대상시총)} bn 의 ÷{a.밴드배수:g}~×{a.밴드배수:g}")

    f색인 = frames_색인(캐시)
    대체 = _캐시읽기(캐시, "주식수_대체.json") or {}

    행들, 통과, 탈락 = [], [], []
    for t in 티커들:
        행 = 후보조립(캐시, t, 기준일, 종가사전, f색인, 대체, 경로들.get(t, ""))
        if 행["시가총액"] is not None and 밴드 is not None:
            하한, 상한, _ = 밴드
            if 하한 <= 행["시가총액"] <= 상한:
                행["판정"] = "통과"
            else:
                행["판정"], 행["분류"] = "탈락", "4. 목적 불일치"
                행["사유"] = (f"규모대 밖 ({_bn(행['시가총액'])} bn, "
                            f"선언 밴드 {_bn(하한)}~{_bn(상한)} bn)")
        elif 행["시가총액"] is not None:
            행["판정"] = "—"                      # 밴드 미선언 — 조립만
        행들.append(행)
        if 행["판정"] == "통과":
            통과.append(행)
        elif 행["판정"] == "탈락":
            탈락.append({"티커": 행["티커"], "회사명": 행["회사명"], "경로": 행["경로"],
                       "시가총액": 행["시가총액"], "분류": 행["분류"], "사유": 행["사유"]})

    산출 = {
        "기준일": a.기준일,
        "대상": {"티커": 대상, "주식수": 대상주식수, "종가": 대상종가, "시가총액": 대상시총},
        "밴드": None if 밴드 is None else
               {"하한": 밴드[0], "상한": 밴드[1], "선언": 밴드[2]},
        "행": 행들,
        "통과": [행["티커"] for 행 in 통과],
        "탈락": 탈락,
    }
    출력경로 = os.path.join(캐시, a.출력)
    with io.open(출력경로, "w", encoding="utf-8") as f:
        json.dump(산출, f, ensure_ascii=False, indent=1)

    통과경로 = None
    if 밴드 is not None and 통과:
        if os.path.basename(a.통과출력) == "2차통과.json":
            sys.exit("--통과출력을 2차통과.json 으로 주면 조립 산출물을 덮습니다. "
                     "다른 이름을 주십시오(기본 2차통과_명단.json).")
        통과경로 = os.path.join(캐시, a.통과출력)
        with io.open(통과경로, "w", encoding="utf-8") as f:
            json.dump(통과, f, ensure_ascii=False, indent=1)

    # 화면 표 — 근거가 한 줄씩 보이게
    print(f"대상 {대상} 시가총액 {_bn(대상시총)} bn "
          f"(주식수 {대상주식수:,.0f} × 종가 {대상종가:,.2f})")
    if 밴드 is not None:
        print(f"선언 밴드 {_bn(밴드[0])}~{_bn(밴드[1])} bn — {밴드[2]}")
    print()
    for 행 in sorted(행들, key=lambda r: -(r["시가총액"] or 0)):
        시총 = f"{_bn(행['시가총액']):>10} bn" if 행["시가총액"] is not None else f"{'—':>13}"
        표기 = {"통과": "○ 통과", "탈락": "× 탈락", "—": "  (판정 없음)"}.get(행["판정"], "")
        print(f"{행['티커']:<6} {시총}  {표기:<8} {행['분모종류'] or ''} "
              f"{행['주식수기준일'] or ''}")
        if 행["사유"]:
            print(f"       └ [{행['분류']}] {행['사유']}")
    print()
    n불가 = sum(1 for r in 행들 if r["시가총액"] is None)
    print(f"후보 {len(행들)}곳: 통과 {len(통과)} · 탈락 {len(탈락)} "
          f"(그중 시가총액 못 세움 {n불가}) → {출력경로}")
    if 통과경로:
        print(f"통과 명단 → {통과경로} (사슬 비싼 층의 --명단 으로 쓴다)")
    확정필요 = [r["티커"] for r in 행들 if r["사유"] and "주식수_대체.json 에 확정" in r["사유"]]
    if 확정필요:
        print(f"사람 확정 대기 {len(확정필요)}곳: {', '.join(확정필요)} — 표지 문장을 읽고 "
              f"주식수_대체.json 에 적은 뒤 다시 돌리면 그 자리만 바뀝니다.")


if __name__ == "__main__":
    main()

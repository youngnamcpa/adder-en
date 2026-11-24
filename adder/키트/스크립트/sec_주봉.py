# -*- coding: utf-8 -*-
"""미국·해외 주봉을 회귀 창 전체(`--창년`, 기본 5년)로 받는다 (HWO-53) — 110개 상한을 푼다.

**회귀 창 기본 5년 주간(2026-10-16 결정).** 옛 기본은 3년(365×3+14일)이었다. 창년은 인자다.
기대 주 수 = 52 × 창년 + 1(5년이면 261주). 그보다 적으면 상장 이력 · 창구 결손이다 — 표본 수를 그대로 적는다.

**병목 실측:** 종전 창구(naver 해외 주봉)는 **110개 상한**이라 3년(157주)도 못 채웠다.
표본 110이면 잔차상관 잡음 문턱이 2/√110 = 0.191 로 올라가 컷이 무뎌지고,
베타 회귀도 국내(160주)보다 짧은 창에서 돌았다 — 속도가 아니라 **표본의 병목**이다.

**처방:** Yahoo chart API 가 기간을 지정한 주봉을 무인증 1콜(실측 0.4초 — 3년 158개)에 준다.
ADR(VLVLY)·해외 상장(005930.KS)까지 같은 창구다. **가격 수익률이 기본이다(2026-10-17 S7-16 — 「로그 · 가격 수익률로
통일(배당 미포함)」).** 지수(^GSPC · 그 나라 넓은 지수)는 가격 지수라 종목도 가격(분할만 조정된 `close`)으로 맞춘다 — 종목만 배당 포함
수정주가(adjclose)를 쓰면 종목은 총수익 · 지수는 가격이라 베타가 배당만큼 어긋난다. 총수익으로 맞추려면 `--총수익`(종목 adjclose) 과
총수익 지수(예: ^SP500TR)를 함께 쓰고 근거에 적는다. 2026-10-17 전 캐시는 adjclose 다 — 같은 회차에서 섞지 않게 `--새로` 로 다시 받는다.

산출은 `peer_조립_us.py` 가 읽는 `_raw/peers/wk_{티커}.json` 형식 그대로다:
    [["YYYYMMDD", 종가], ...]
평가기준일이 주어지면 그 **당일까지의 주만** 담는다 — 기준일 뒤의 주가 섞이면
회귀 창이 평가기준일을 넘는다.

사용:
    python 스크립트/sec_주봉.py --tickers TSLA,GM,VLVLY --기준일 2026-06-30
    python 스크립트/sec_주봉.py --tickers ^GSPC --키 _INX --기준일 2026-06-30

비공식 창구라 형식 변경·차단 위험이 있다 — 실패하면 그 티커를 실패로 적고,
종전 창구(naver 110개)를 폴백으로 쓰되 **표본 수를 그대로 보고**한다.

**한 회차 안에서 두 창구를 섞지 않는다.** 주 라벨 관행이 다르다 — naver 는 금요일
종료일, Yahoo 는 월요일 시작일. 섞으면 종목·지수의 주 키가 하나도 안 겹쳐 회귀 표본이
0 이 된다(시끄럽게 죽으니 그나마 다행이지만, 지수만 폴백으로 받는 실수가 그 자리다).
품질 대조 실측(GM, ISO 주 기준 101주 겹침): 수익률 부호 일치 100/100 ·
최대 수익률 차 1.4%p — 배당 조정(adjclose) 차이다. 지수와 같은 정의(가격)로 맞추는 것이 먼저다(S7-16).

**캐시는 기준일 창일 때만 재사용한다 (2026-09-13 · 세일즈포스 회차 C2 실측).** 옛 판은 파일이
있으면 창을 안 보고 재사용했다 — 세일즈포스 폴더(기준일 2026-07-31)에 다른 회차의 `wk__INX`
(2026-06-30 창)가 남아 있어 C2 가 `--새로` 로 손으로 갱신했다. 그대로 갔으면 지수 수익률이 한 달
짧은 창으로 회귀에 들어갔다. 이제 캐시가 아래 셋 중 하나면 **다시 받는다**:
  · 마지막 주 라벨이 기준일 뒤다(더 늦은 기준일 창)
  · 마지막 주 라벨이 기준일보다 7일 이상 이르다(기준일이 든 주가 없다 — 옛 기준일 창)
  · 라벨이 월요일이 아니다(naver 금요일 라벨 — 창구가 섞인다)
상장폐지·거래정지로 기준일 주가 원래 없는 종목은 매번 다시 받게 되지만, 받은 결과도 창 밖이면
그 사실을 경보로 적는다(조용히 옛 값을 쓰지 않는다).

**창년이 늘었을 때(3년 → 5년)** 옛 창 캐시는 끝이 맞아도 앞이 짧다. 첫 주가 「기준일 − k년」(k < 창년) 경계 ±21일
안이면 옛 창으로 잘린 캐시로 보고 다시 받는다. 상장이 짧아 앞이 짧은 종목은 경계와 무관하므로 그대로 쓴다
(마침 경계 근처에 상장한 종목은 한 번 더 받을 뿐이다).
"""
from __future__ import annotations

import argparse
import datetime
import io
import json
import os
import sys
import time
import urllib.parse
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
PEER = os.environ.get("DCF_PEER_CACHE") or os.path.join(os.getcwd(), "_raw", "peers")      # main() 이 --캐시 로 바꿀 수 있다 · 사슬은 환경변수로(손개입 개선 1)
머리 = {"User-Agent": "Mozilla/5.0"}
창년 = 5                                                # main() 이 --창년 으로 바꾼다


def 기대주수(n=None):
    return 52 * (n or 창년) + 1


def 캐시창(줄, 기준일, 창=None):
    """(재사용해도 되는가, 사유) — Yahoo 주 라벨(월요일 시작) 기준으로 기준일이 든 주로 끝나는가.
    `창`(해 수)을 주면 앞도 본다 — 첫 주가 더 짧은 옛 창의 경계에서 잘렸으면 다시 받는다."""
    if not 줄:
        return False, "빈 캐시"
    try:
        날들 = [datetime.date(int(d[:4]), int(d[4:6]), int(d[6:8])) for d, _ in 줄]
    except Exception:
        return False, "라벨 읽기 실패"
    끝 = 날들[-1]
    if 끝 > 기준일:
        return False, "마지막 주 %s 가 기준일 %s 뒤 — 다른 기준일 창" % (끝, 기준일)
    if (기준일 - 끝).days >= 7:
        return False, "마지막 주 %s 가 기준일 %s 보다 %d일 이르다 — 옛 기준일 창" % (끝, 기준일, (기준일 - 끝).days)
    뒤 = 날들[-8:]
    if sum(1 for d in 뒤 if d.weekday() == 0) <= len(뒤) / 2:
        return False, "주 라벨이 월요일이 아니다 — naver 창구 캐시(섞으면 표본 0)"
    if 창:
        첫 = 날들[0]
        for k in range(1, 창):
            try:
                경계 = 기준일.replace(year=기준일.year - k)
            except ValueError:                                  # 2월 29일
                경계 = 기준일.replace(year=기준일.year - k, day=28)
            if abs((첫 - 경계).days) <= 21:
                return False, "첫 주 %s 가 %d년 창 경계(%s) — 옛 창 캐시, %d년 창으로 다시 받음" % (첫, k, 경계, 창)
    return True, ""


총수익 = False          # S7-16 — 기본 가격 수익률(close). --총수익 이면 adjclose(배당 포함) — 지수도 총수익 지수로 맞춘다


def 야후주봉(티커, 기준일, 창=None):
    끝 = datetime.datetime.combine(기준일 + datetime.timedelta(days=1), datetime.time())
    시작 = 끝 - datetime.timedelta(days=365 * (창 or 창년) + 14)
    u = ("https://query1.finance.yahoo.com/v8/finance/chart/%s?" % urllib.parse.quote(티커)
         + urllib.parse.urlencode(dict(period1=int(시작.timestamp()), period2=int(끝.timestamp()),
                                       interval="1wk", events="div,splits")))
    d = json.loads(urllib.request.urlopen(urllib.request.Request(u, headers=머리), timeout=30).read().decode())
    r = d["chart"]["result"][0]
    ts = r["timestamp"]
    지표 = r["indicators"]
    수정 = (지표.get("adjclose") or [{}])[0].get("adjclose")
    종가 = 지표["quote"][0]["close"]
    값 = 수정 if (총수익 and 수정 and any(v is not None for v in 수정)) else 종가
    통화 = r.get("meta", {}).get("currency")
    줄 = []
    for t, v in zip(ts, 값):
        if v is None:
            continue
        d8 = time.strftime("%Y%m%d", time.gmtime(t))
        if d8 <= 기준일.strftime("%Y%m%d"):
            줄.append([d8, round(float(v), 6)])
    return 줄, 통화, ("adjclose" if 값 is 수정 else "close")


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False, description="Yahoo 회귀 창(기본 5년) 주봉 → _raw/peers/wk_{키}.json")
    ap.add_argument("--tickers", required=True, help="쉼표 구분 (지수는 ^GSPC 등)")
    ap.add_argument("--기준일", required=True, help="YYYY-MM-DD — 이 날까지의 주만 담는다")
    ap.add_argument("--키", default=None, help="저장 키를 티커 대신 지정 (지수 _INX 등, 티커 1개일 때)")
    ap.add_argument("--새로", action="store_true", help="캐시가 기준일 창이어도 다시 받는다")
    ap.add_argument("--캐시", default=None, help="_raw/peers 대신(시험용)")
    ap.add_argument("--창년", type=int, default=5, help="회귀 창 해 수(기본 5 — 주간)")
    ap.add_argument("--총수익", action="store_true", help="종목을 배당 포함 수정주가(adjclose)로 — 지수도 총수익 지수로 맞춰야 한다(S7-16)")
    a = ap.parse_args()
    global PEER, 창년, 총수익
    창년 = a.창년
    총수익 = a.총수익
    if a.캐시:
        PEER = os.path.abspath(a.캐시)
    os.makedirs(PEER, exist_ok=True)
    기준일 = datetime.date.fromisoformat(a.기준일)
    티커들 = [t.strip() for t in a.tickers.split(",") if t.strip()]
    if a.키 and len(티커들) != 1:
        sys.exit("--키 는 티커가 하나일 때만 씁니다")
    실패 = []
    for i, t in enumerate(티커들):
        키 = a.키 or t.upper().replace("^", "").replace(".", "_")
        경로 = os.path.join(PEER, "wk_%s.json" % 키)
        if os.path.exists(경로) and not a.새로:
            try:
                기존 = json.load(io.open(경로, encoding="utf-8"))
            except Exception:
                기존 = []
            됨, 사유 = 캐시창(기존, 기준일, 창년)
            if 됨:
                print("  %-8s 캐시 %d주(마지막 %s) — 기준일 창이라 재사용" % (t, len(기존), 기존[-1][0]))
                continue
            print("  %-8s 캐시를 버리고 다시 받음 — %s" % (t, 사유))
        if i:
            time.sleep(0.3)
        try:
            줄, 통화, 기준 = 야후주봉(t, 기준일)
        except Exception as e:
            실패.append(t)
            print("  %-8s 실패: %s" % (t, str(e)[:70]))
            continue
        io.open(경로, "w", encoding="utf-8").write(json.dumps(줄, ensure_ascii=False))
        됨, 사유 = 캐시창(줄, 기준일)
        if not 됨:
            print("           경보: 받은 주봉도 기준일 창이 아니다(%s) — 상장폐지·거래정지·창구 결손을 확인하십시오" % 사유)
        print("  %-8s 주봉 %d개 (%s~%s · %s · %s) → wk_%s.json"
              % (t, len(줄), 줄[0][0] if 줄 else "-", 줄[-1][0] if 줄 else "-", 통화, 기준, 키))
        if len(줄) < 기대주수() - 7:
            print("           주의: %d년 %d주를 못 채웠습니다(%d) — 상장 이력이 짧거나 창구 결손. 표본 수를 그대로 적으십시오"
                  % (창년, 기대주수(), len(줄)))
    if 실패:
        print("실패 %d곳: %s — 종전 창구(naver 110개)를 폴백으로 쓰되 표본 수를 그대로 보고하십시오"
              % (len(실패), ",".join(실패)))


if __name__ == "__main__":
    main()

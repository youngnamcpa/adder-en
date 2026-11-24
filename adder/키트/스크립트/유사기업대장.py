# -*- coding: utf-8 -*-
"""유사기업 대장 (HWO-57) — 비싼 층 원재료를 회차 넘어 재사용한다.

**무엇을 쌓는가 — 원재료만.** 시세(sise_·wk_·day_·vol_)·주식수(shares_·주식수.csv)·
재무(전체재무_추출.csv·cc_·fx_)·메타(sub_)·종가(종가_)·환율(환율_)·ADS 배율(ads_)·
표지(표지_)·산업분류(산업분류_전수.csv). **파생값(βU·잔차상관·조립 표)은 안 쌓는다** —
βU 는 세율 위에서 계산된 값이라 대장에 넣으면 낡은 전제가 따라온다(HWO-26).
원재료를 꺼내 조립기가 그 회차의 전제로 다시 계산하면 전제 문제가 구조적으로 사라진다.

**칸은 기준분기다.** 시세 창과 재무 기준이 분기 단위로 같아야 재사용이 성립한다.
ADS 배율·표지·sub 메타는 회사 속성이라 `무기한/` 에 둔다 — 다만 sub 는 꺼낼 때
갱신 여부를 확인하라는 알림을 낸다.

**주봉 창구를 전제로 기록한다.** naver(금요일 종료 라벨)와 Yahoo(월요일 시작 라벨)를
한 회차에 섞으면 주 키가 안 겹쳐 회귀 표본이 0 이 된다(sec_주봉.py 머리말).
꺼낼 때 창구가 섞이면 경고한다.

**기준일 창을 거른다 (2026-09-13 · 세일즈포스 회차 세14).** 회차 폴더의 `_raw/peers` 에는
**다른 회차가 남긴 옛 창**이 섞여 있다 — 세일즈포스(기준일 2026-07-31) 폴더에 기아·TSLA 회차의
`wk__INX`·`wk_F`·`wk_GM`(2026-06-30 창)이 있었고, 옛 판 `넣기` 는 폴더를 통째로 쓸어 담아
2026Q3 칸에 6/30 창을 섞을 뻔했다(C2 가 손으로 오늘 파일만 골라 넣었다). 이제 `--기준일` 을 주면:
  · wk_ 는 마지막 주가 기준일 7일 안이어야, day_(해외) 는 기준일 7일 안의 날이 있어야,
    sise_·vol_·day_(국내 기간형) 는 파일 이름의 끝일이 기준일이어야,
    종가_·환율_ 은 파일 이름의 날짜가 기준일이어야 넣는다. 아니면 **건너뛰고 이름을 적는다.**
  · 기준분기가 기준일의 분기와 다르면 멈춘다. 칸의 전제.json 에 이미 다른 기준일이 있으면 경보.
  · `꺼내기 --기준일` 도 같은 거름을 건다 — 개정 전에 섞여 들어간 칸에서 옛 창을 안 꺼낸다.
  `--기준일` 없이 `넣기` 를 돌리면 옛 동작 그대로 가되 경보를 낸다.

사용:
    python 스크립트/유사기업대장.py 넣기 --회차 "…/한화오션" --기준분기 2026Q2 --시장 kr --기준일 2026-06-30
    python 스크립트/유사기업대장.py 꺼내기 --기준분기 2026Q2 --시장 kr --대상폴더 "…/새회차" --기준일 2026-06-30
    python 스크립트/유사기업대장.py 목록

대장 위치: 저장소/데이터/유사기업대장/{시장}/{기준분기}/ 와 {시장}/무기한/
(이 스크립트가 시작키트 안에 있으므로 저장소 = 시작키트의 부모다. `--대장` 으로 바꿀 수 있다 — 시험용.)
"""
from __future__ import annotations

import argparse
import datetime as dt
import io
import json
import os
import re
import shutil
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")
여기 = os.path.dirname(os.path.abspath(__file__))
시작키트 = os.path.dirname(여기)
_옛뿌리 = os.path.join(os.path.dirname(시작키트), "데이터", "유사기업대장")
# 2026-10-24 W16 — 키트 사본(회사마다의 작업 폴더)에서는 옛 자리(사본 옆 `데이터/`)가 회사 폴더 안이라 쌓인 것이 다음 회사로 안 넘어갔다(유니버스 조사 물결 실측).
# 차례: 환경변수 `DCF_유사기업대장` → 옛 자리가 이미 있으면 그대로(저장소) → 공용 캐시 `<공용>/유사기업대장`
대장뿌리 = (os.environ.get("DCF_유사기업대장")
         or (_옛뿌리 if os.path.isdir(_옛뿌리) else
             os.path.join(os.environ.get("DCF_공용캐시") or os.environ.get("DCF_SHARED_CACHE") or os.path.expanduser("~/.dcf캐시"), "유사기업대장")))

분기접두 = ("sise_", "vol_", "wk_", "day_", "shares_", "cc_", "fx_", "frame_",
           "종가_", "환율_")
병합접두 = ("종가_", "환율_")            # {키: 값} 사전 — 통째로 덮으면 마지막 회차가 이긴다
하위캐시 = ("shares", "fs", "company")   # 국내 회차의 회사별 원문 캐시 폴더
무기한접두 = ("ads_", "표지_", "sub_")
뿌리파일 = ("주식수.csv", "전체재무_추출.csv", "산업분류_전수.csv", "산업분류.csv")


def _날(s):
    s = str(s).replace("-", "")
    return dt.date(int(s[:4]), int(s[4:6]), int(s[6:8]))


def 분기(기준일):
    d = _날(기준일)
    return "%dQ%d" % (d.year, (d.month - 1) // 3 + 1)


def 창판정(경로, 기준일):
    """(넣어도 되는가, 사유) — 기준일 창이 아닌 시세·종가·환율 파일을 거른다."""
    f = os.path.basename(경로)
    기 = _날(기준일)
    기8 = 기.strftime("%Y%m%d")
    try:
        if f.startswith(("종가_", "환율_")):
            m = re.search(r"_(\d{8})\.json$", f)
            if m and m.group(1) != 기8:
                return False, "다른 기준일(%s)" % m.group(1)
            if not m:
                return False, "파일 이름에 기준일이 없음(백업·병합본)"
            return True, ""
        if f.startswith(("sise_", "vol_")) or (f.startswith("day_") and re.search(r"_\d{8}_\d{8}\.json$", f)):
            m = re.search(r"_(\d{8})_(\d{8})\.json$", f)
            if m and m.group(2) != 기8:
                return False, "창 끝일 %s ≠ 기준일" % m.group(2)
            return True, ""
        if f.startswith("wk_"):
            줄 = json.load(io.open(경로, encoding="utf-8"))
            끝 = _날(줄[-1][0])
            if 끝 > 기 or (기 - 끝).days > 7:
                return False, "주봉 마지막 주 %s — 기준일 창 아님" % 끝
            return True, ""
        if f.startswith("day_"):
            줄 = json.load(io.open(경로, encoding="utf-8"))
            날들 = [_날(x[0]) for x in 줄]
            if not any(0 <= (기 - d).days <= 7 for d in 날들):
                return False, "일봉에 기준일 7일 안의 날이 없음(%s~%s)" % (min(날들), max(날들))
            return True, ""
        if f.startswith("shares_"):
            d = json.load(io.open(경로, encoding="utf-8"))
            ends = [v.get("end") for v in d.values() if isinstance(v, dict) and v.get("end")]
            if ends and (기 - _날(max(ends))).days > 200:
                return True, "경보: 주식수 최신 끝일 %s — 기준일보다 200일 넘게 이르다" % max(ends)
    except Exception as e:  # noqa
        return False, "읽기 실패 %r" % e
    return True, ""


def _주봉창구(peer, 기준일=None):
    """주봉 라벨의 **요일**로 창구를 가른다 — 접두(wk_)는 두 창구가 같이 쓴다.

    Yahoo 는 월요일 시작 라벨, naver 는 금요일 종료 라벨이다(sec_주봉.py 머리말 실측)."""
    창구 = set()
    for f in os.listdir(peer):
        경로 = os.path.join(peer, f)
        if not os.path.isfile(경로):
            continue
        if 기준일 and f.startswith(("wk_", "sise_")) and not 창판정(경로, 기준일)[0]:
            continue
        if f.startswith("wk_"):
            try:
                줄 = json.load(io.open(경로, encoding="utf-8"))
                요일 = [_날(d).weekday() for d, _ in 줄[:8]]
                if 요일 and sum(1 for x in 요일 if x == 0) > len(요일) / 2:
                    창구.add("yahoo주봉(월요일라벨)")
                elif 요일:
                    창구.add("naver주봉(금요일라벨)")
            except Exception:
                pass
        if f.startswith("sise_") and "_week_" in f:
            창구.add("naver주봉(금요일라벨)")
    return sorted(창구)


def _병합사전(원, 갈곳):
    """{키: 값} 사전 파일은 합친다 — 원 쪽이 새 키를 더하고, 겹치는 키는 원 쪽이 이긴다."""
    a = json.load(io.open(갈곳, encoding="utf-8"))
    b = json.load(io.open(원, encoding="utf-8"))
    if isinstance(a, dict) and isinstance(b, dict):
        a.update(b)
        io.open(갈곳, "w", encoding="utf-8").write(json.dumps(a, ensure_ascii=False, indent=1))
    else:
        shutil.copy2(원, 갈곳)


def 넣기(a):
    회차 = os.path.abspath(a.회차)
    peer = os.path.join(회차, "_raw", "peers")
    if not os.path.isdir(peer):
        sys.exit("회차에 _raw/peers 가 없습니다: %s" % peer)
    if a.기준일:
        if 분기(a.기준일) != a.기준분기:
            sys.exit("기준일 %s 은 %s 인데 --기준분기 %s 입니다 — 칸이 어긋납니다" % (a.기준일, 분기(a.기준일), a.기준분기))
    else:
        print("★ --기준일 없이 넣습니다 — 다른 회차의 옛 창(wk_·종가_)이 섞여도 거르지 못합니다(옛 동작)")
    분기칸 = os.path.join(대장뿌리, a.시장, a.기준분기)
    무기한칸 = os.path.join(대장뿌리, a.시장, "무기한")
    os.makedirs(분기칸, exist_ok=True)
    os.makedirs(무기한칸, exist_ok=True)
    전제경로 = os.path.join(분기칸, "전제.json")
    전제 = {"수집": []}
    if os.path.exists(전제경로):
        전제 = json.load(io.open(전제경로, encoding="utf-8"))
    옛기준일 = sorted({x.get("기준일") for x in 전제.get("수집", []) if x.get("기준일")})
    if a.기준일 and 옛기준일 and 옛기준일 != [a.기준일]:
        print("★ 이 칸에는 다른 기준일(%s)의 수집이 이미 있습니다 — 시세 창이 다를 수 있습니다" % ",".join(옛기준일))
    센 = {"분기": 0, "무기한": 0, "뿌리": 0, "건너뜀": 0, "창밖": 0}
    창밖 = []
    for f in sorted(os.listdir(peer)):
        원 = os.path.join(peer, f)
        if not os.path.isfile(원):
            continue
        if f.startswith(무기한접두):
            갈곳 = os.path.join(무기한칸, f)
            칸 = "무기한"
        elif f.startswith(분기접두):
            갈곳 = os.path.join(분기칸, f)
            칸 = "분기"
        else:
            센["건너뜀"] += 1
            continue
        if a.기준일 and 칸 == "분기":
            됨, 사유 = 창판정(원, a.기준일)
            if not 됨:
                센["창밖"] += 1
                창밖.append("%s(%s)" % (f, 사유))
                continue
            if 사유:
                print("  %s — %s" % (f, 사유))
        if f.startswith(병합접두) and os.path.exists(갈곳):
            _병합사전(원, 갈곳)
            센[칸] += 1
            continue
        if os.path.exists(갈곳) and os.path.getsize(갈곳) == os.path.getsize(원):
            continue
        shutil.copy2(원, 갈곳)
        센[칸] += 1
    for 폴더 in 하위캐시:
        원폴더 = os.path.join(peer, 폴더)
        if os.path.isdir(원폴더):
            갈폴더 = os.path.join(분기칸, 폴더)
            os.makedirs(갈폴더, exist_ok=True)
            for f in os.listdir(원폴더):
                원 = os.path.join(원폴더, f)
                갈곳 = os.path.join(갈폴더, f)
                if os.path.isfile(원) and not os.path.exists(갈곳):
                    shutil.copy2(원, 갈곳)
                    센["분기"] += 1
    for f in 뿌리파일:
        원 = os.path.join(회차, f)
        if os.path.exists(원):
            shutil.copy2(원, os.path.join(분기칸, f))
            센["뿌리"] += 1
    전제["수집"].append({"회차": os.path.basename(os.path.normpath(회차)), "넣은날": time.strftime("%Y-%m-%d %H:%M"), "기준일": a.기준일,
                       "주봉창구": _주봉창구(peer, a.기준일), "창밖_건너뜀": len(창밖)})
    io.open(전제경로, "w", encoding="utf-8").write(json.dumps(전제, ensure_ascii=False, indent=1))
    print("넣기 완료 — 분기 %d · 무기한 %d · 뿌리표 %d · 대상 밖 %d · 기준일 창 밖 %d → %s"
          % (센["분기"], 센["무기한"], 센["뿌리"], 센["건너뜀"], 센["창밖"], 분기칸))
    if 창밖:
        print("  기준일 창 밖이라 안 넣은 파일(다른 회차 잔재로 봄): " + " · ".join(창밖[:30])
              + (" …외 %d" % (len(창밖) - 30) if len(창밖) > 30 else ""))
    print("전제 기록: 기준일 %s · 주봉창구 %s ｜ βU·조립 표는 넣지 않았다 — 꺼낸 회차가 제 세율로 다시 계산한다"
          % (a.기준일 or "미기재", _주봉창구(peer, a.기준일) or "없음"))
    return 센, 창밖


def 꺼내기(a):
    분기칸 = os.path.join(대장뿌리, a.시장, a.기준분기)
    무기한칸 = os.path.join(대장뿌리, a.시장, "무기한")
    if not os.path.isdir(분기칸):
        sys.exit("대장에 %s/%s 칸이 없습니다 — `목록` 으로 확인하십시오" % (a.시장, a.기준분기))
    if a.기준일 and 분기(a.기준일) != a.기준분기:
        sys.exit("기준일 %s 은 %s 인데 --기준분기 %s 입니다" % (a.기준일, 분기(a.기준일), a.기준분기))
    대상 = os.path.abspath(a.대상폴더)
    peer = os.path.join(대상, "_raw", "peers")
    os.makedirs(peer, exist_ok=True)
    센 = {"분기": 0, "무기한": 0, "뿌리": 0, "이미": 0, "창밖": 0}
    창밖 = []
    for 칸이름, 칸 in (("분기", 분기칸), ("무기한", 무기한칸)):
        if not os.path.isdir(칸):
            continue
        for f in sorted(os.listdir(칸)):
            원 = os.path.join(칸, f)
            if not os.path.isfile(원) or f == "전제.json":
                continue
            if f in 뿌리파일:
                갈곳 = os.path.join(대상, f)
                키 = "뿌리"
            else:
                갈곳 = os.path.join(peer, f)
                키 = 칸이름
            if a.기준일 and 칸이름 == "분기" and f not in 뿌리파일:
                됨, 사유 = 창판정(원, a.기준일)
                if not 됨:
                    센["창밖"] += 1
                    창밖.append("%s(%s)" % (f, 사유))
                    continue
            if f.startswith(병합접두) and os.path.exists(갈곳):
                _병합사전(원, 갈곳)
                센[키] += 1
                continue
            if os.path.exists(갈곳):
                센["이미"] += 1
                continue
            shutil.copy2(원, 갈곳)
            센[키] += 1
        for 폴더 in 하위캐시:
            원폴더 = os.path.join(칸, 폴더)
            if os.path.isdir(원폴더):
                갈폴더 = os.path.join(peer, 폴더)
                os.makedirs(갈폴더, exist_ok=True)
                for f2 in os.listdir(원폴더):
                    원2 = os.path.join(원폴더, f2)
                    갈2 = os.path.join(갈폴더, f2)
                    if os.path.isfile(원2) and not os.path.exists(갈2):
                        shutil.copy2(원2, 갈2)
                        센[칸이름] += 1
    print("꺼내기 완료 — 분기 %d · 무기한 %d · 뿌리표 %d · 이미 있어 건너뜀 %d · 기준일 창 밖 %d → %s"
          % (센["분기"], 센["무기한"], 센["뿌리"], 센["이미"], 센["창밖"], 대상))
    if 창밖:
        print("  기준일 창 밖이라 안 꺼낸 파일: " + " · ".join(창밖[:30]))
    전제경로 = os.path.join(분기칸, "전제.json")
    if os.path.exists(전제경로):
        전제 = json.load(io.open(전제경로, encoding="utf-8"))
        창구들 = set()
        for x in 전제.get("수집", []):
            창구들 |= set(x.get("주봉창구") or [])
        기준일들 = sorted({x.get("기준일") or "미기재" for x in 전제.get("수집", [])})
        print("전제 — 주봉창구 %s · 수집 이력 %d건 · 기준일 %s"
              % (sorted(창구들) or "기록 없음", len(전제.get("수집", [])), ",".join(기준일들)))
        if len(창구들) > 1:
            print("★ 주봉 창구가 섞여 있습니다(naver 금요일 라벨 vs Yahoo 월요일 라벨) — "
                  "한 회귀에 섞으면 주 키가 안 겹쳐 표본이 0 이 됩니다. 한 창구만 쓰십시오.")
        if not a.기준일 and (len(기준일들) > 1 or "미기재" in 기준일들):
            print("★ 이 칸에는 기준일이 다르거나 미기재인 수집이 있습니다 — --기준일 을 주면 옛 창을 거릅니다")
    print("주의 — sub_ 메타는 무기한 칸에서 왔습니다. 기준일이 대장 수집 시점보다 뒤면 "
          "sec_peer_meta 를 다시 돌려 최근 제출을 갱신하십시오. "
          "βU·조립 표는 대장에 없습니다 — 이 회차의 세율로 조립기를 돌리십시오(HWO-26).")
    return 센, 창밖


def 목록(a):
    if not os.path.isdir(대장뿌리):
        print("대장이 비어 있습니다:", 대장뿌리)
        return
    for 시장 in sorted(os.listdir(대장뿌리)):
        for 칸 in sorted(os.listdir(os.path.join(대장뿌리, 시장))):
            p = os.path.join(대장뿌리, 시장, 칸)
            n = sum(1 for f in os.listdir(p) if os.path.isfile(os.path.join(p, f)))
            크기 = sum(os.path.getsize(os.path.join(p, f)) for f in os.listdir(p)
                     if os.path.isfile(os.path.join(p, f)))
            print("  %s/%-10s %4d개 %7.1fMB" % (시장, 칸, n, 크기 / 1e6))


def main():
    global 대장뿌리
    ap = argparse.ArgumentParser(allow_abbrev=False, description="유사기업 대장 — 원재료의 회차 간 재사용")
    ap.add_argument("--대장", default=None, help="대장 뿌리 폴더(시험용 — 기본은 저장소/데이터/유사기업대장)")
    sub = ap.add_subparsers(dest="일", required=True)
    p1 = sub.add_parser("넣기", allow_abbrev=False)
    p1.add_argument("--회차", required=True, help="회차 폴더 (…/_raw/peers 를 가진)")
    p1.add_argument("--기준분기", required=True, help="예: 2026Q2")
    p1.add_argument("--시장", required=True, type=str.lower, choices=["kr", "us"])   # 대소문자 무시(2026-10-24 W15)
    p1.add_argument("--기준일", default=None, help="YYYY-MM-DD — 주면 기준일 창이 아닌 시세·종가·환율을 거른다")
    p2 = sub.add_parser("꺼내기", allow_abbrev=False)
    p2.add_argument("--기준분기", required=True)
    p2.add_argument("--시장", required=True, type=str.lower, choices=["kr", "us"])   # 대소문자 무시(2026-10-24 W15)
    p2.add_argument("--대상폴더", default=시작키트, help="꺼낼 회차(키트) 폴더 — 기본은 이 키트(2026-10-24 W16 — 문서 예시와 맞춤)")
    p2.add_argument("--기준일", default=None, help="YYYY-MM-DD — 주면 옛 창을 안 꺼낸다")
    sub.add_parser("목록", allow_abbrev=False)
    a = ap.parse_args()
    if a.대장:
        대장뿌리 = os.path.abspath(a.대장)
    {"넣기": 넣기, "꺼내기": 꺼내기, "목록": 목록}[a.일](a)


if __name__ == "__main__":
    main()

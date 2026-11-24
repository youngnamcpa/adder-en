# -*- coding: utf-8 -*-
"""**이례 표시** — 회사의 과거 해 · 유사기업 값에서 튀는 점을 Modified Z 로 **표시만** 한다(지우지 않는다).

    python 스크립트/이례표시.py 가정.json                                   # → 가정 곁 _raw/이례표시.json · 표를 찍는다
    python 스크립트/이례표시.py 가정.json --자리 앵커,운전자본               # 재는 자리를 고른다(앵커 · 운전자본 · 성격별 · 유사기업)
    python 스크립트/이례표시.py 가정.json --낼 경로.json --설정 다른설정.json

무엇 — Modified Z = 0.6745 × (x − 중앙값) ÷ MAD(중앙값 절대편차). |Z| 가 문턱(설정 3.5)을 넘는 점을 표시한다.
  평균 · 표준편차로 재면 튀는 점이 기준 자체를 끌어당겨 제 자신을 가린다. 중앙값 · MAD 는 그 영향을 거의 안 받는다 —
  키트가 무차입 베타를 개별 βU 의 **중앙값**으로 잡는 것과 같은 강건 통계 계열이다.
왜 — 규칙 셋을 사람 손이 아니라 같은 자로 실행한다.
  · 「평균을 내기 전에 튀는 해가 있는지 먼저 보고한다」 — 운전자본 회전일수 · 성격별 비용 비율
  · 「일회성 판정 기준은 반복되면 일회성이 아니다 — 최근 4개 기간에 두 번 이상 나온 항목은 사이클의 일부」 — 표시된 해를 품는
    연속 4개 기간에 같은 쪽 표시가 두 번 이상이면 「반복」, 한 번이면 「일회성 후보」
  · 「벌어짐을 만드는 회사를 위 · 아래 각 둘씩 지목한다」 — 유사기업 βU · 현금보정 βU · PER · PBR
**표시는 「틀렸다」가 아니라 「틀릴 수도 있다」다.** 실험(전 상장사 11년 패널)에서 연도별 영업이익률의 12% 가 문턱에 걸렸고 대부분
  실제 극단이었다. 그래서 값을 지우거나 고치지 않고, 어느 점이 튀었는지와 근거 칸에 무엇을 적어야 하는지만 낸다. 고르는 것은 사람이다.
  MAD 가 0 이면(값이 거의 다 같으면) 그 계열은 「잴 수 없음」, 관측이 최소(설정 — 시계열 6 · 유사기업 5)보다 적으면 「표본 부족」으로
  적고 표시하지 않는다. 시계열은 사업연도 열만 쓴다(반기 · 분기 열은 기간 길이가 달라 섞지 않는다).

읽는 것 — 네트워크 0. 가정 곁 `_raw/`(없으면 가정 폴더 · 위 폴더 `_raw/` · 작업 폴더 `_raw/` — `정상화.파일찾기` 와 같은 차례)
  앵커       `_raw/dart_앵커시계열.json`(국내 — `dart_fetch.py` 앵커받기: {"해": [{"사업연도", "list": fnlttSinglAcntAll 행}]}) ·
             `_raw/앵커_시계열.json`(미국 — `sec_앵커.py`: {"표": [{"사업연도": "FY2024", "매출", "매출원가", "판관비", "영업이익"}]})
             → 영업이익률 · 매출성장률 · 매출원가율 · 판관비율. 계정은 `앵커읽기.py` 의 같은 읽기(이름 맞춤 → 표준계정코드)
  운전자본   `_raw/동인원천.json` 의 `운전자본`(A3 — `가정_스키마.md` 「`_raw/동인원천.json`」 절) — 「…회전일수」 · 「…비율」 칸 전부
  성격별     같은 파일의 `성격별비용.항목` ÷ 매출(`재무시계열.매출` → `운전자본.매출연`). 「해당 없음」이면 `기능별비용.항목` 으로
  유사기업   `_raw/peers/βU_{표본}.json`(`peer_조립.py` · `peer_βU_us.py` 의 「표」) · `유사기업_재료_{표본}.csv`(`peer_조립.py` — 대상 참고행은 뺀다)
             → βU · βU_현금보정 · PER · PBR. 표본마다 따로 잰다
내는 것 — `_raw/이례표시.json`
  {"형식": "이례표시 1", "만든날", "설정", "입력", "계열": [자리 · 항목 · 표본 · 관측수 · 중앙값 · MAD · 상태 · 위아래],
   "표시": [자리 · 항목 · 표본 · 대상 · 값 · MZ · 중앙값 · MAD · 표시 · 쪽 · 반복 · 최근4표시 · 판정], "건너뜀": [자리 · 까닭], "신호": […]}
  신호 종류 — 「일회성 후보」(경보) · 「유사기업 극단」(경보) · 「반복 — 사이클」(참고) · 「잴 수 없음」(참고) · 「표본 부족」(참고)
종료 코드 — 0 통과(경보 신호 없음) · 1 발견(경보 신호 있음) · 2 입력오류(가정 파일 없음 · JSON 파손 · 설정 없음 · 모르는 자리).
회사 · 업종 이름은 이 도구에 한 글자도 없다.
"""
from __future__ import annotations

import argparse
import csv
import datetime
import glob
import io
import json
import os
import re
import statistics
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:                                    # noqa: BLE001
    pass
여기 = os.path.dirname(os.path.abspath(__file__))
if 여기 not in sys.path:
    sys.path.insert(0, 여기)
from 종료코드 import 통과, 발견, 입력오류              # noqa: E402

설정경로 = os.path.join(여기, "이례표시설정.json")
자리들 = ("앵커", "운전자본", "성격별", "유사기업")
_FY = re.compile(r"^FY(\d{4})A?$")


def _수(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _float(v):
    if _수(v):
        return float(v)
    if isinstance(v, str):
        s = v.replace(",", "").strip()
        if not s or s in ("-", "None", "nan"):
            return None
        try:
            return float(s)
        except ValueError:
            return None
    return None


def 설정읽기(p=None):
    return json.load(io.open(p or 설정경로, encoding="utf-8"))


def 파일찾기(이름, 가정경로=None):
    """`정상화.파일찾기` 와 같은 차례 — 가정 곁 `_raw/` → 가정 폴더 → 위 폴더 `_raw/` → 작업 폴더 `_raw/`. (내용, 경로)."""
    try:
        import 정상화                                    # noqa: PLC0415
        return 정상화.파일찾기(이름, 가정경로)
    except Exception:                                    # noqa: BLE001
        pass
    후보 = []
    if 가정경로:
        d = os.path.dirname(os.path.abspath(가정경로))
        후보 += [os.path.join(d, "_raw", 이름), os.path.join(d, 이름), os.path.join(os.path.dirname(d), "_raw", 이름)]
    후보.append(os.path.join(os.getcwd(), "_raw", 이름))
    for p in 후보:
        if os.path.exists(p):
            try:
                return json.load(io.open(p, encoding="utf-8")), p
            except (OSError, ValueError):
                return None, p
    return None, None


def _raw폴더(가정경로):
    """유사기업 파일을 찾을 `_raw/` 후보 — 가정 곁 → 위 폴더 → 작업 폴더."""
    d = os.path.dirname(os.path.abspath(가정경로)) if 가정경로 else os.getcwd()
    낸 = []
    for p in (os.path.join(d, "_raw"), os.path.join(os.path.dirname(d), "_raw"), os.path.join(os.getcwd(), "_raw")):
        if os.path.isdir(p) and p not in 낸:
            낸.append(p)
    return 낸


# ────────────────────────────────────────────────────────────── Modified Z

def 재기(값들, 계수=0.6745):
    """[x] → (중앙값, MAD, [Z] 또는 None — MAD 0)."""
    med = statistics.median(값들)
    mad = statistics.median([abs(x - med) for x in 값들])
    if mad == 0:
        return med, 0.0, None
    return med, mad, [계수 * (x - med) / mad for x in 값들]


def 계열재기(자리, 항목, 점들, 설정, 종류="시계열", 표본=None):
    """점들 = [(대상, 값)] (시계열이면 해 순서). → (계열 요약, [표시 줄])."""
    점들 = [(t, float(v)) for t, v in 점들 if _수(v)]
    최소 = (설정.get("최소관측") or {}).get(종류, 6 if 종류 == "시계열" else 5)
    요 = {"자리": 자리, "항목": 항목, "표본": 표본, "관측수": len(점들), "중앙값": None, "MAD": None, "상태": "잼"}
    if len(점들) < 최소:
        요["상태"] = "표본 부족"
        요["까닭"] = "관측 %d개 < 최소 %d" % (len(점들), 최소)
        return 요, []
    med, mad, zs = 재기([v for _, v in 점들], 설정.get("계수", 0.6745))
    요.update(중앙값=round(med, 6), MAD=round(mad, 6))
    if zs is None:
        요["상태"] = "잴 수 없음"
        요["까닭"] = "MAD 0 — 값이 거의 다 같아 퍼짐을 잴 수 없다"
        return 요, []
    문턱 = 설정.get("문턱", 3.5)
    줄 = []
    for (t, v), z in zip(점들, zs):
        표 = abs(z) > 문턱
        줄.append({"자리": 자리, "항목": 항목, "표본": 표본, "대상": t, "값": round(v, 6), "MZ": round(z, 3),
                  "중앙값": round(med, 6), "MAD": round(mad, 6), "표시": 표,
                  "쪽": ("위" if z > 0 else "아래") if 표 else None, "반복": None, "최근4표시": None, "판정": ""})
    if 종류 == "시계열":
        _반복(줄, 설정)
    else:
        n = 설정.get("위아래지목", 2)
        정렬 = sorted(줄, key=lambda x: x["값"])
        요["위아래"] = {"위": [{"대상": x["대상"], "값": x["값"], "MZ": x["MZ"]} for x in 정렬[::-1][:n]],
                     "아래": [{"대상": x["대상"], "값": x["값"], "MZ": x["MZ"]} for x in 정렬[:n]]}
        for x in 줄:
            if x["표시"]:
                x["판정"] = "극단 — 벌어짐을 만드는 회사. 표본에서 뺄지는 사람이 정한다"
    return 요, 줄


def _반복(줄, 설정):
    """표시된 해를 품는 연속 `반복창` 개 기간 가운데 같은 쪽 표시가 `반복최소` 번 이상이면 반복."""
    창, 최소 = 설정.get("반복창", 4), 설정.get("반복최소", 2)
    n = len(줄)
    최근 = 줄[-창:] if n >= 창 else 줄
    for i, x in enumerate(줄):
        if not x["표시"]:
            continue
        반복 = False
        for s in range(max(0, i - 창 + 1), min(i, n - 창) + 1 if n >= 창 else 1):
            묶음 = 줄[s:s + 창]
            if sum(1 for y in 묶음 if y["표시"] and y["쪽"] == x["쪽"]) >= 최소:
                반복 = True
                break
        x["반복"] = 반복
        x["최근4표시"] = sum(1 for y in 최근 if y["표시"] and y["쪽"] == x["쪽"])
        x["판정"] = ("반복 — 일회성 후보 아님(사이클의 일부). 걷어내지 않는다" if 반복 else
                   "일회성 후보 — 원인(충당금 환입 · 구조조정 · 일회성 손익 등)을 확인해 정상화에서 걷어낼지 근거 칸에 적는다")


# ────────────────────────────────────────────────────────────── 읽기

def _해(글):
    m = _FY.match("%s" % 글)
    if m:
        return int(m.group(1))
    m = re.search(r"(19|20)\d{2}", "%s" % (글 or ""))
    return int(m.group(0)) if m else None


def 앵커읽기_(가정경로, 설정):
    """→ ({해: {매출 · 영업이익 · 매출원가 · 판관비}}, 출처 경로, 까닭)."""
    j, p = 파일찾기("dart_앵커시계열.json", 가정경로)
    if isinstance(j, dict) and isinstance(j.get("해"), list):
        import 앵커읽기                                       # noqa: PLC0415
        낸 = {}
        for h in j["해"]:
            items = h.get("list") or []
            y = h.get("사업연도")
            try:
                y = int(y)
            except (TypeError, ValueError):
                continue
            매, _무, 금융 = 앵커읽기.매출한해(items)
            영, _w = 앵커읽기.영업한해(items)
            원가, _ = 앵커읽기.이름값(items, tuple(설정.get("매출원가이름") or ("매출원가",)))
            판관, _ = 앵커읽기.이름값(items, tuple(설정.get("판관비이름") or ("판매비와관리비",)))
            낸[y] = {"매출": 매, "영업이익": 영, "매출원가": 원가, "판관비": 판관, "금융업계정": bool(금융)}
        return 낸, p, None
    j, p = 파일찾기("앵커_시계열.json", 가정경로)
    if isinstance(j, dict) and isinstance(j.get("표"), list):
        낸 = {}
        for r in j["표"]:
            y = _해(r.get("사업연도"))
            if y is None:
                continue
            낸[y] = {"매출": _float(r.get("매출")), "영업이익": _float(r.get("영업이익")),
                    "매출원가": _float(r.get("매출원가")), "판관비": _float(r.get("판관비")), "금융업계정": False}
        return 낸, p, None
    return {}, None, "앵커 파일이 없다(`_raw/dart_앵커시계열.json` · `_raw/앵커_시계열.json`) — 2단계 앵커를 받은 뒤 다시 돈다"


def 앵커계열(가정경로, 설정):
    해들, p, 까 = 앵커읽기_(가정경로, 설정)
    if 까:
        return [], p, 까
    ys = sorted(해들)
    계 = {"영업이익률": [], "매출성장률": [], "매출원가율": [], "판관비율": []}
    for y in ys:
        r = 해들[y]
        매 = r.get("매출")
        if _수(매) and 매:
            if _수(r.get("영업이익")):
                계["영업이익률"].append((str(y), r["영업이익"] / 매))
            if _수(r.get("매출원가")):
                계["매출원가율"].append((str(y), r["매출원가"] / 매))
            if _수(r.get("판관비")):
                계["판관비율"].append((str(y), r["판관비"] / 매))
            앞 = 해들.get(y - 1)
            if 앞 and _수(앞.get("매출")) and 앞["매출"] > 0:
                계["매출성장률"].append((str(y), 매 / 앞["매출"] - 1))
    금융 = [y for y in ys if 해들[y].get("금융업계정")]
    return [(k, v) for k, v in 계.items()], p, ("매출을 금융업 계정으로 잡은 해 %s — 값은 재되 FCFF 매출과 성질이 다르다" % 금융) if 금융 else None


def _FY열(d):
    """{기간 ID: 값} → [(해 글, 값)] — 사업연도 열만, 해 순서."""
    낸 = []
    if not isinstance(d, dict):
        return 낸
    for k, v in d.items():
        m = _FY.match("%s" % k)
        if m and _수(v):
            낸.append((int(m.group(1)), float(v)))
    return [(str(y), v) for y, v in sorted(낸)]


def 운전자본계열(가정경로):
    j, p = 파일찾기("동인원천.json", 가정경로)
    if not isinstance(j, dict):
        return [], p, "A3 `_raw/동인원천.json` 이 없다 — A3 를 돈 뒤 다시 돈다"
    운 = j.get("운전자본")
    if not isinstance(운, dict):
        return [], p, "`동인원천.json` 에 `운전자본` 이 없다(%s)" % ("「%s」" % 운 if isinstance(운, str) else "칸 없음")
    낸 = []
    for k, v in 운.items():
        if (k.endswith("회전일수") or k.endswith("비율")) and isinstance(v, dict):
            열 = _FY열(v)
            if 열:
                낸.append((k, 열))
    return 낸, p, (None if 낸 else "`운전자본` 에 사업연도 열의 회전일수 · 비율이 없다")


def 성격별계열(가정경로):
    j, p = 파일찾기("동인원천.json", 가정경로)
    if not isinstance(j, dict):
        return [], p, "A3 `_raw/동인원천.json` 이 없다 — A3 를 돈 뒤 다시 돈다"
    매 = {}
    for k, r in (j.get("재무시계열") or {}).items():
        m = _FY.match("%s" % k)
        if m and isinstance(r, dict) and _수(r.get("매출")) and r["매출"]:
            매[int(m.group(1))] = float(r["매출"])
    for y, v in _FY열((j.get("운전자본") or {}).get("매출연") if isinstance(j.get("운전자본"), dict) else {}):
        if v:
            매.setdefault(int(y), v)
    표 = j.get("성격별비용")
    출처 = "성격별비용"
    if not isinstance(표, dict) or not isinstance(표.get("항목"), dict):
        표 = j.get("기능별비용")
        출처 = "기능별비용"
    if not isinstance(표, dict) or not isinstance(표.get("항목"), dict):
        return [], p, "`성격별비용` · `기능별비용` 둘 다 표가 없다(%s)" % (j.get("성격별비용") if isinstance(j.get("성격별비용"), str) else "칸 없음")
    if not 매:
        return [], p, "비율의 분모(`재무시계열.매출` · `운전자본.매출연`)가 없다"
    낸 = []
    for 이름, 열 in 표["항목"].items():
        점 = [(y, v / 매[int(y)]) for y, v in _FY열(열) if int(y) in 매]
        if 점:
            낸.append(("%s ÷ 매출(%s)" % (이름, 출처), 점))
    return 낸, p, (None if 낸 else "%s 항목에 사업연도 열이 없다" % 출처)


def _대상행인가(r):
    nm = ("%s" % (r.get("회사명") or r.get("티커") or "")).strip()
    return nm.endswith("(대상)") or (r.get("경로") or "").strip() == "-" or "대상회사 참고행" in ("%s" % r.get("왜", ""))


def 유사기업계열(가정경로, 설정):
    """표본마다 [(항목, [(회사, 값)])]. → ([(표본, 항목, 점들)], [경로], 까닭)."""
    항목들 = 설정.get("유사기업항목") or ["βU", "βU_현금보정", "PER", "PBR"]
    표본 = {}
    json표본 = set()      # βU 산출(json)이 있는 표본은 βU 를 json 에서만 — csv 와 회사 키가 달라도 두 번 세지 않는다
    경로 = []
    import 피어경로                                         # noqa: PLC0415
    try:
        가정 = json.load(io.open(가정경로, encoding="utf-8")) if 가정경로 else None
    except (OSError, ValueError):
        가정 = None
    for raw in _raw폴더(가정경로):
        peer = os.path.join(raw, "peers")
        # 1.1.4 — 레터 · 갭해석과 같은 βU 재료 하나(창 끝 날짜로 고른 판)와 그 짝 csv 만 본다. 종전에는 폴더의 βU 산출 · csv 를 다 읽어
        # 옛 창 · 오염 판 표본(「핵심예비_T」)의 중앙값으로 경보했다(1.1.3 재실행 회차)
        고 = 피어경로.βU재료고르기(os.path.dirname(raw), 가정)
        jsons = [고["경로"]] if 고 else []
        짝 = 피어경로.βU짝csv(os.path.dirname(raw), 고["경로"]) if 고 else None
        for p in jsons:
            이름 = os.path.basename(p)[len("βU_"):-len(".json")]
            try:
                j = json.load(io.open(p, encoding="utf-8"))
            except (OSError, ValueError):
                continue
            for r in j.get("표") or []:
                if not isinstance(r, dict) or _대상행인가(r):
                    continue
                키 = r.get("종목코드") or r.get("티커")
                칸 = 표본.setdefault(이름, {}).setdefault(키, {"회사": r.get("티커") or 키})
                for h in ("βU", "βU_현금보정"):
                    if _float(r.get(h)) is not None:
                        칸[h] = _float(r.get(h))
            json표본.add(이름)
            경로.append(p)
        csvs = ([짝] if 짝 else []) if 고 else sorted(glob.glob(os.path.join(peer, "유사기업_재료*.csv")) + glob.glob(os.path.join(raw, "..", "유사기업_재료*.csv")))
        for p in csvs:
            b = os.path.basename(p)[:-len(".csv")]
            이름 = b[len("유사기업_재료_"):] if b.startswith("유사기업_재료_") else "기본"
            try:
                rows = list(csv.DictReader(io.open(p, encoding="utf-8-sig")))
            except (OSError, UnicodeDecodeError, csv.Error):
                continue
            for r in rows:
                if _대상행인가(r):
                    continue
                키 = r.get("종목코드") or r.get("티커") or r.get("회사명")
                칸 = 표본.setdefault(이름, {}).setdefault(키, {"회사": r.get("회사명") or r.get("티커") or 키})
                for h in 항목들:
                    if h.startswith("βU") and 이름 in json표본:
                        continue
                    v = _float(r.get(h))
                    if v is not None and h not in 칸:
                        칸[h] = v
            경로.append(os.path.normpath(p))
    if not 표본:
        return [], 경로, "유사기업 산출이 없다(`_raw/peers/βU_*.json` · `유사기업_재료_*.csv`) — C2 를 돈 뒤 다시 돈다"
    낸 = []
    for 이름, 회사들 in sorted(표본.items()):
        for h in 항목들:
            점 = [(c["회사"], c[h]) for c in 회사들.values() if _수(c.get(h))]
            낸.append((이름, h, 점))
    return 낸, sorted(set(경로)), None


# ────────────────────────────────────────────────────────────── 실행

def _퍼(x, 항목):
    if not _수(x):
        return "%s" % x
    if "회전일수" in 항목:
        return "%.1f일" % x
    if 항목 in ("βU", "βU_현금보정", "PER", "PBR") or "β" in 항목:
        return "%.3f" % x
    return "%.1f%%" % (x * 100)


def 돌기(가정경로, 설정, 고른=None):
    고른 = list(고른 or 설정.get("자리") or 자리들)
    문턱 = 설정.get("문턱", 3.5)
    계열, 표시, 건너뜀, 신호 = [], [], [], []
    입력 = {"가정": os.path.abspath(가정경로)}

    def 담기(자리, 묶음, 종류, 표본=None):
        for 항목, 점 in 묶음:
            요, 줄 = 계열재기(자리, 항목, 점, 설정, 종류, 표본)
            계열.append(요)
            표시.extend(줄)
            if 요["상태"] in ("잴 수 없음", "표본 부족"):
                신호.append({"출처": "이례표시", "종류": 요["상태"], "대상": "%s %s%s" % (자리, 항목, (" · " + 표본) if 표본 else ""),
                           "값": 요["관측수"], "문턱": (설정.get("최소관측") or {}).get(종류) if 요["상태"] == "표본 부족" else "MAD > 0",
                           "글": "%s %s 은(는) %s — %s. 이 자리의 튀는 점은 사람이 원문으로 본다"
                                % (자리, 항목, 요["상태"], 요.get("까닭", "")), "등급": "참고"})
            for x in 줄:
                if not x["표시"]:
                    continue
                if 종류 == "시계열":
                    신호.append({"출처": "이례표시", "종류": "반복 — 사이클" if x["반복"] else "일회성 후보",
                               "대상": "%s %s %s" % (자리, 항목, x["대상"]), "값": x["값"], "문턱": 문턱,
                               "글": "%s %s %s년 %s 이(가) 중앙값 %s 에서 벗어났다(MZ %+.1f) — %s"
                                    % (자리, 항목, x["대상"], _퍼(x["값"], 항목), _퍼(x["중앙값"], 항목), x["MZ"], x["판정"]),
                               "등급": "참고" if x["반복"] else "경보"})
                else:
                    신호.append({"출처": "이례표시", "종류": "유사기업 극단", "대상": "%s %s · %s" % (항목, x["대상"], 표본),
                               "값": x["값"], "문턱": 문턱,
                               "글": "유사기업 %s 에서 %s 의 %s 가 표본(%s) 중앙값 %s 에서 벗어났다(MZ %+.1f) — βU 세 방식 · 배수의 폭을 "
                                    "보고할 때 이 회사를 이름으로 적는다. 표본에서 뺄지는 사람이 정한다"
                                    % (항목, x["대상"], _퍼(x["값"], 항목), 표본, _퍼(x["중앙값"], 항목), x["MZ"]),
                               "등급": "경보"})

    for 자리 in 고른:
        if 자리 == "앵커":
            묶음, p, 까 = 앵커계열(가정경로, 설정)
            입력["앵커"] = p
            if not 묶음:
                건너뜀.append({"자리": 자리, "까닭": 까})
                continue
            if 까:
                건너뜀.append({"자리": 자리, "까닭": 까, "진행": True})
            담기(자리, 묶음, "시계열")
        elif 자리 == "운전자본":
            묶음, p, 까 = 운전자본계열(가정경로)
            입력["동인원천"] = p
            if not 묶음:
                건너뜀.append({"자리": 자리, "까닭": 까})
                continue
            담기(자리, 묶음, "시계열")
        elif 자리 == "성격별":
            묶음, p, 까 = 성격별계열(가정경로)
            입력["동인원천"] = p
            if not 묶음:
                건너뜀.append({"자리": 자리, "까닭": 까})
                continue
            담기(자리, 묶음, "시계열")
        elif 자리 == "유사기업":
            묶음, ps, 까 = 유사기업계열(가정경로, 설정)
            입력["유사기업"] = ps
            if not 묶음:
                건너뜀.append({"자리": 자리, "까닭": 까})
                continue
            for 표본, 항목, 점 in 묶음:
                담기(자리, [(항목, 점)], "유사기업", 표본)
    공개설정 = {k: v for k, v in 설정.items() if not k.startswith("_")}
    return {"형식": "이례표시 1", "만든날": datetime.date.today().isoformat(), "설정": 공개설정, "입력": 입력,
            "계열": 계열, "표시": 표시, "건너뜀": 건너뜀, "신호": 신호}


def 찍기(결과):
    print("이례 표시 — Modified Z 문턱 %s · 표시만 한다(지우지 않는다)" % 결과["설정"].get("문턱"))
    for 요 in 결과["계열"]:
        n표 = sum(1 for x in 결과["표시"] if x["자리"] == 요["자리"] and x["항목"] == 요["항목"]
                 and x.get("표본") == 요.get("표본") and x["표시"])
        print("  %-6s %-34s %s 관측 %2d · %s%s" % (요["자리"], (요["항목"] + (" · " + 요["표본"] if 요.get("표본") else ""))[:34],
                                           "" if 요["상태"] == "잼" else "[%s]" % 요["상태"], 요["관측수"],
                                           "표시 %d" % n표 if 요["상태"] == "잼" else 요.get("까닭", ""),
                                           ("  위 %s · 아래 %s" % (", ".join("%s" % w["대상"] for w in 요["위아래"]["위"]),
                                                                ", ".join("%s" % w["대상"] for w in 요["위아래"]["아래"])))
                                           if 요.get("위아래") else ""))
    for b in 결과["건너뜀"]:
        print("  건너뜀 %s — %s" % (b["자리"], b["까닭"]))
    경 = [s for s in 결과["신호"] if s["등급"] == "경보"]
    print("신호 %d개 — 경보 %d · 참고 %d" % (len(결과["신호"]), len(경), len(결과["신호"]) - len(경)))
    for s in 경[:20]:
        print("  [경보] " + s["글"])


def main(argv=None):
    ap = argparse.ArgumentParser(allow_abbrev=False, description="회사의 과거 해 · 유사기업 값의 튀는 점을 Modified Z 로 표시한다(지우지 않는다)")
    ap.add_argument("가정")
    ap.add_argument("--자리", default=None, help="쉼표로 — 앵커 · 운전자본 · 성격별 · 유사기업 (기본: 설정의 자리 전부)")
    ap.add_argument("--낼", default=None, help="산출 경로(기본: 가정 곁 _raw/이례표시.json)")
    ap.add_argument("--설정", default=None, help="설정 파일(기본: 스크립트 곁 이례표시설정.json)")
    a = ap.parse_args(argv)
    if not os.path.exists(a.가정):
        print("가정 파일이 없습니다: %s" % a.가정)
        return 입력오류
    try:
        json.load(io.open(a.가정, encoding="utf-8"))
    except (OSError, ValueError) as e:
        print("가정 파일을 읽지 못했습니다: %s" % e)
        return 입력오류
    try:
        설정 = 설정읽기(a.설정)
    except (OSError, ValueError) as e:
        print("설정 파일을 읽지 못했습니다: %s" % e)
        return 입력오류
    고른 = [x.strip() for x in a.자리.split(",") if x.strip()] if a.자리 else None
    if 고른 and any(x not in 자리들 for x in 고른):
        print("모르는 자리: %s (앵커 · 운전자본 · 성격별 · 유사기업)" % ", ".join(x for x in 고른 if x not in 자리들))
        return 입력오류
    결과 = 돌기(a.가정, 설정, 고른)
    밖 = a.낼 or os.path.join(os.path.dirname(os.path.abspath(a.가정)), "_raw", "이례표시.json")
    os.makedirs(os.path.dirname(밖), exist_ok=True)
    io.open(밖, "w", encoding="utf-8").write(json.dumps(결과, ensure_ascii=False, indent=1))
    찍기(결과)
    print("→ %s" % 밖)
    return 발견 if any(s["등급"] == "경보" for s in 결과["신호"]) else 통과


if __name__ == "__main__":
    sys.exit(main())

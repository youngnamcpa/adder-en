# -*- coding: utf-8 -*-
"""신호돌리기 — 신호 · 통계 도구를 집대성 단계 표(`신호단계.json`)의 차례대로 돌린다 (2026-10-23 밤 · 연구/레터워크북_최적화_20261023/05 W1).

    python 스크립트/신호돌리기.py 가정.json                      # 앞 · 뒤 · 끝 전부(거친 바퀴는 돌리지 않는다 — 있으면 뒤 단계가 읽는다)
    python 스크립트/신호돌리기.py 가정.json --단계 앞             # 거친 바퀴 앞 — 관측 · 시계열 · 구조 · 패널 도구
    python 스크립트/신호돌리기.py 가정.json --거친바퀴            # 앞 → 거친 바퀴(`--json _raw/거친바퀴.json`) → 뒤 → 끝
    python 스크립트/신호돌리기.py 가정.json --만 기저율,지속성     # 그 도구만(도구글 머리 · 산출 이름 어느 쪽이든)
    python 스크립트/신호돌리기.py 가정.json --건너뛰기 조합이례도 --받기   # 네트워크 도구(주석태그 · kam추출 …)까지
    python 스크립트/신호돌리기.py 가정.json --보기                # 돌리지 않고 차례 · 재료 판정만 찍는다

왜 — 도구 31종 가운데 10-23 회차에서 값이 흐른 것은 결합민감도 · 민감도격자 둘이었다. 단계 표는 집대성 문서에 있었지만 그 표대로 돌리는
  실행기가 없었고, 거친 바퀴의 통계범위(코호트 · 수축 · 국면 · 상태공간 · 계절추세 · 계수사전)와 기저율 자리는 그 산출이 **먼저** 있어야 실리는데
  차례가 어긋났다. 이 실행기가 그 차례를 박는다 — 앞(관측 · 시계열 · 구조 · 패널) → [거친 바퀴] → 뒤(정보가치 · 결합민감도 · 민감도격자 · 닫힘검사) → 끝(변수카드).
무엇을 하나 — 도구마다 ① 재료 판정(「패널」 = 공용 패널이 이 가정의 국가에 있음 · 「파일:…」 = `_raw` 에 있음) — 없으면 건너뛰고 까닭을 적는다 ·
  ② 네트워크 도구는 `--받기` 일 때만 · 가정 밖 인자가 있어야 하는 도구는 건너뛴다 ③ `python -X utf8 -B 도구.py …` 를 돌려 rc 를 판정한다 —
  0 돎 · 1 돎(경보) · 2 건너뜀(그 도구가 입력이 없다고 했다 — 마지막 줄이 까닭) · 그 밖 실패 ④ `_raw/신호돌리기.json` 에 요약을 쓴다.
값을 정하지 않는다 — 도구가 낸 신호 · 근거범위 · 제안은 거친 바퀴 · 자체검사 51 · 모순장부 M-10 · 변수카드 · 레터 · 워크북이 읽는다.
회사 · 업종 이름이 이 도구에 없다. 종료 코드 — 0(실패 0) · 1(실패 있음) · 2 입력 오류.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import io
import json
import os
import subprocess
import sys
import time

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:                                    # noqa: BLE001
    pass
여기 = os.path.dirname(os.path.abspath(__file__))
if 여기 not in sys.path:
    sys.path.insert(0, 여기)
from 종료코드 import 통과, 발견, 입력오류           # noqa: E402
import 신호파일                                       # noqa: E402

형식 = "신호돌리기 1"
단계차례 = ("앞", "뒤", "끝")


def _해시(p):
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()[:12]


def 이름(x):
    """도구 줄의 짧은 이름 — 산출 파일 이름(확장자 · 폴더 뺌)."""
    return os.path.splitext(os.path.basename(x["산출"]))[0]


def 패널있음(가정):
    """공용 패널이 이 가정의 국가(표시통화)에 있나 → (참 · 거짓, 글)."""
    try:
        import 기저율 as 기                                   # noqa: PLC0415
        s = 기.설정읽기()
        국, s, _ = 기.국가맞춤(가정, s)
        if not 국:
            return False, "표시통화가 패널 국가(KR · US)가 아니다"
        자리 = 기.패널자리(s)
        if 기.패널파일들(자리):
            return True, "%s 패널(%s)" % (국, 자리)
        return False, "%s 공용 패널이 비었다 — `기저율.py --받기%s`(네트워크 · 한 번만)" % (국, " --국가 US" if 국 == "US" else "")
    except Exception as e:                           # noqa: BLE001
        return False, "패널을 확인하지 못했다(%s)" % type(e).__name__


def _가정값(가정, 길):
    """가정 dict 에서 「도착점.켜기」 꼴 점 경로의 값(없으면 None)."""
    v = 가정
    for k in 길.split("."):
        if not isinstance(v, dict):
            return None
        v = v.get(k)
    return v


def 재료판정(x, raw, 패널, 가정=None):
    """→ (돌릴까, 까닭). 패널 = (있음, 글). 「가정:점.경로」 재료는 가정 파일의 그 칸이 참일 때만 돈다(2026-10-25 Y3 — `도착점` 블록이
    있는 회사에서만 도는 도구가 블록 없는 회사에서 「산출 없음 = 실패」 로 서지 않게)."""
    for r in x.get("재료") or []:
        if r == "패널":
            if not 패널[0]:
                return False, "재료 없음 — %s" % 패널[1]
        elif r.startswith("파일:"):
            후보 = r[3:].split("|")
            if not any(os.path.exists(os.path.join(raw, *c.split("/"))) for c in 후보):
                return False, "재료 없음 — _raw/%s" % " 또는 ".join(후보)
        elif r.startswith("가정:"):
            if not _가정값(가정 or {}, r[3:]):
                return False, "해당 없음 — 가정의 `%s` 가 없거나 꺼져 있다" % r[3:]
    return True, ""


def 계획(단, 가정, 가정경로, a, 고른=None, 패널=None):
    """→ ([{도구 줄 + 판정}], 패널) — 고른 단계의 도구를 차례대로. 재료는 부를 때마다 다시 본다(앞 단계 · 거친 바퀴가 방금 쓴 산출)."""
    raw = os.path.join(os.path.dirname(os.path.abspath(가정경로)), "_raw")
    패널 = 패널 or 패널있음(가정)
    만 = {s.strip() for s in (a.만 or "").split(",") if s.strip()}
    뺄 = {s.strip() for s in (a.건너뛰기 or "").split(",") if s.strip()}
    고른 = 고른 or (단계차례 if a.단계 == "전부" else (a.단계,))
    줄들 = sorted([x for x in 단["도구"] if x.get("단계") in 고른 and x.get("명령")],
                key=lambda x: (단계차례.index(x["단계"]), x.get("차례", 0)))
    낸 = []
    for x in 줄들:
        n = 이름(x)
        머 = x["도구글"].split()[0].replace(".py", "")
        한 = {"이름": n, "도구글": x["도구글"], "단계": x["단계"], "차례": x.get("차례"), "산출": x["산출"], "집대성": x.get("집대성")}
        if 만 and not ({n, 머, x["도구글"]} & 만):
            continue
        if {n, 머, x["도구글"]} & 뺄:
            한.update(판정="건너뜀", 까닭="--건너뛰기")
        elif x.get("받기") and not a.받기:
            한.update(판정="건너뜀", 까닭="네트워크 도구 — `--받기` 일 때만")
        elif x.get("인자필요"):
            한.update(판정="건너뜀", 까닭="인자 필요 — %s" % x["인자필요"])
        else:
            ok, 까 = 재료판정(x, raw, 패널, 가정)
            if not ok:
                한.update(판정="건너뜀", 까닭=까)
            else:
                명 = [("%s" % c).replace("{가정}", os.path.abspath(가정경로)).replace("{raw}", raw) for c in x["명령"]]
                if 패널[0] and x.get("패널있으면"):
                    명 += list(x["패널있으면"])
                한.update(판정="돌림", 명령=명)
        낸.append(한)
    return 낸, 패널


def 하나(한, 시간):
    """도구 하나를 돈다 — 한 줄에 rc · 초 · 판정 · 끝줄을 채운다."""
    시 = time.time()
    환 = dict(os.environ, PYTHONIOENCODING="utf-8")
    명 = [sys.executable, "-X", "utf8", "-B", os.path.join(여기, 한["명령"][0])] + 한["명령"][1:]
    try:
        r = subprocess.run(명, capture_output=True, text=True, encoding="utf-8", errors="replace", env=환, timeout=시간,
                           cwd=os.path.dirname(여기))
        rc, 글 = r.returncode, (r.stdout or "") + (r.stderr or "")
    except subprocess.TimeoutExpired:
        rc, 글 = "시간초과", ""
    끝 = [l for l in 글.strip().splitlines() if l.strip()]
    한["rc"] = rc
    한["초"] = round(time.time() - 시, 1)
    말 = [l for l in 끝 if not l.lstrip().startswith("→ ")]                 # 산출 경로 줄(「→ …」)보다 도구의 마지막 말을 남긴다
    한["끝줄"] = ((말 or 끝)[-1] if 끝 else "").strip()[:240]
    if rc == 통과:
        한["판정"] = "돎"
    elif rc == 발견:
        한["판정"] = "돎(경보)"
    elif rc == 입력오류:
        한["판정"] = "건너뜀"
        한["까닭"] = "도구가 입력이 없다고 했다 — %s" % 한["끝줄"]
    else:
        한["판정"] = "실패"
        한["까닭"] = 한["끝줄"] or "rc %s" % rc
        한["글끝"] = 끝[-12:]
    return 한


def 실행(가정경로, a):
    try:
        가정 = json.load(io.open(가정경로, encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise ValueError("가정을 못 읽었다 — %s" % e)
    단 = 신호파일.단계읽기()
    raw = os.path.join(os.path.dirname(os.path.abspath(가정경로)), "_raw")
    os.makedirs(raw, exist_ok=True)
    고른 = 단계차례 if a.단계 == "전부" else (a.단계,)
    계, 패널 = 계획(단, 가정, 가정경로, a, 고른)
    결과 = {"형식": 형식, "만든날": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "가정": os.path.abspath(가정경로),
          "가정해시": _해시(가정경로), "단계": a.단계, "받기": bool(a.받기), "패널": {"있음": 패널[0], "글": 패널[1]}, "도구": [], "거친바퀴": None, "신호": []}
    if a.보기:
        결과["도구"] = 계
        return 결과
    for 한 in [x for x in 계 if x["단계"] == "앞"]:
        결과["도구"].append(하나(한, a.시간) if 한["판정"] == "돌림" else 한)
    if a.거친바퀴 and a.단계 in ("전부", "앞", "뒤"):
        명 = [("%s" % c).replace("{가정}", os.path.abspath(가정경로)).replace("{raw}", raw) for c in 단["거친바퀴"]["명령"]]
        결과["거친바퀴"] = 하나({"이름": "거친바퀴", "도구글": "거친바퀴.py", "단계": "거친바퀴", "산출": "거친바퀴.json", "명령": 명}, a.시간)
    뒤고른 = tuple(d for d in ("뒤", "끝") if d in 고른)
    if 뒤고른:                                        # 앞 단계 · 거친 바퀴가 쓴 산출로 재료를 다시 본다
        계2, _ = 계획(단, 가정, 가정경로, a, 뒤고른, 패널)
        for 한 in 계2:
            결과["도구"].append(하나(한, a.시간) if 한["판정"] == "돌림" else 한)
    # 산출 확인 · 낡음
    for 한 in 결과["도구"]:
        p = os.path.join(raw, *한["산출"].split("/"))
        한["산출있음"] = os.path.exists(p)
        if 한["판정"].startswith("돎") and not 한["산출있음"]:
            한["판정"] = "실패"
            한["까닭"] = "rc %s 인데 산출 파일이 없다" % 한.get("rc")
        elif 한["판정"].startswith("돎") and 한["산출"] in 신호파일.엔진값파일:
            신호파일.값해시찍기(p, 가정경로)          # G2 — 원고 넣기처럼 글만 바뀐 가정이 이 신호를 낡게 하지 않게(자체검사 51 이 값 해시로 본다)
    for 한 in 결과["도구"]:
        if 한["판정"] == "실패":
            결과["신호"].append({"출처": "신호돌리기", "종류": "도구 실패", "대상": 한["도구글"], "값": 한.get("rc"), "문턱": None,
                             "글": "%s 가 돌다 멈췄다 — %s. 그 도구의 신호 없이 진행된다(다시 돌린다)" % (한["도구글"], 한.get("까닭")), "등급": "참고"})
    결과["요약"] = {k: sum(1 for x in 결과["도구"] if x["판정"] == k) for k in ("돎", "돎(경보)", "건너뜀", "실패")}
    return 결과


def 쓰기(결과, 가정경로, 낼=None):
    p = 낼 or os.path.join(os.path.dirname(os.path.abspath(가정경로)), "_raw", "신호돌리기.json")
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
    with io.open(p, "w", encoding="utf-8") as f:
        json.dump(결과, f, ensure_ascii=False, indent=1)
    return p


def 표찍기(결과):
    print("신호돌리기 — 단계 %s · 패널 %s%s" % (결과["단계"], "있음" if 결과["패널"]["있음"] else "없음", "" if 결과["패널"]["있음"] else "(%s)" % 결과["패널"]["글"]))
    줄들 = list(결과["도구"])
    if 결과.get("거친바퀴"):
        i = next((k for k, x in enumerate(줄들) if x["단계"] != "앞"), len(줄들))
        줄들.insert(i, 결과["거친바퀴"])
    for x in 줄들:
        print("  %-4s %-16s %-8s %6s  %s" % (x["단계"][:4], x["이름"][:16], x["판정"], ("%.1f초" % x["초"]) if x.get("초") is not None else "",
                                           (x.get("까닭") or x.get("끝줄") or "")[:110]))
    if 결과.get("요약"):
        print("  요약 — %s" % " · ".join("%s %d" % kv for kv in 결과["요약"].items()))


def main(argv=None):
    ap = argparse.ArgumentParser(allow_abbrev=False, description=__doc__.split("\n")[0])
    ap.add_argument("가정")
    ap.add_argument("--단계", default="전부", choices=("전부", "앞", "뒤", "끝"))
    ap.add_argument("--만", help="쉼표로 — 이 도구만(산출 이름 · 도구 이름)")
    ap.add_argument("--건너뛰기", help="쉼표로 — 이 도구는 건너뛴다")
    ap.add_argument("--받기", action="store_true", help="네트워크 도구까지(주석태그 · kam추출 …)")
    ap.add_argument("--거친바퀴", action="store_true", help="앞 단계 뒤에 거친 바퀴를 돌려 _raw/거친바퀴.json 을 쓴다")
    ap.add_argument("--시간", type=int, default=900, help="도구 하나의 시간 한도(초)")
    ap.add_argument("--보기", action="store_true", help="돌리지 않고 차례 · 재료 판정만")
    ap.add_argument("--낼")
    a = ap.parse_args(argv)
    if not os.path.exists(a.가정):
        print("가정 파일이 없다: %s" % a.가정)
        return 입력오류
    try:
        결과 = 실행(a.가정, a)
    except ValueError as e:
        print("입력 오류 — %s" % e)
        return 입력오류
    if not a.보기:
        print("→ %s" % 쓰기(결과, a.가정, a.낼))
    표찍기(결과)
    return 발견 if (결과.get("요약") or {}).get("실패") else 통과


if __name__ == "__main__":
    sys.exit(main())

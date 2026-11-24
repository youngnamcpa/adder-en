# -*- coding: utf-8 -*-
"""레터모션 — 레터의 모션 장면(A · B · C)의 시간표(한 출처)와 영상(MP4 · GIF · 포스터)을 낸다 (R1c · v4d · v4e — 2026-10-16 디자이너 리뷰 반영 ·
v4f — 2026-10-22 리뷰 두 편의 남은 항목: 단계 경계 프레임의 「읽히는가」 검사(⑤ 라벨과 마크 겹침 포함) · 단추 자리 고정 · C 「한 달」 · 자 눈금).

    python 스크립트/레터모션.py <레터.md> [--장부 <장부.json>] [-o <곳>] [--fps 30] [--장면 A,B,C] [--밝은것만] [--경계 <폴더>]
        [--배율 2] [--경계만]      # 정지 그림(프레임 내보내기): --경계 <폴더> --경계만 --배율 3.4(넓은 판 560 × 3.4 = 1,904px — 300dpi 16cm 폭)

두 매체, 한 시간표(v4e)
  · 웹(레터 HTML) — 영상을 쓰지 않는다. 레터 안의 정적 SVG(정적 그림과 같은 함수가 낸 것)를 브라우저가 움직인다(`레터HTML.모션JS` — Anime.js).
    처음에는 완성된 정적 그림이고 「순서대로 보기」 를 눌러야 움직인다(자동 재생 없음 · 한 번에 한 장면 · 줄인 움직임 · 인쇄 · 스크립트 꺼짐은 정적).
    시간표는 `웹계획` 이 이 파일의 단계 목록에서 내고(JSON), 영상도 같은 단계 목록으로 굽는다 — 웹과 영상이 같은 시간표다.
  · 영상(mp4 · gif · 포스터) — 스크립트가 돌지 않는 곳(네이버 프리미엄 콘텐츠 · 메일 · SNS)에 붙이는 파일이다. 넓은 판(viewBox 560)을
    2배(1120px)로 굽는다 — 표시 폭 560px 에서 주 글 14px · 보조 12.5px · 축 12px(원본 28 · 25 · 24px). 어두운 화면용(.dark)도 따로 굽는다.

모션이 필요한가(v4e 판정 질문) — 「시작과 끝 사이에 정적 그림에 없는 사건이 있는가」. 예 → 시간 재생(C: 가격이 옮겨 가면 전제가 따라온다).
  아니오지만 공개 순서가 내용이면 → 독자가 넘기는 단계형 또는 재생 단추(A: 계산 순서 · B: 맥락 다음 초점). 둘 다 아니면 → 정적(D 토네이도 — 폐기).
규칙(자료/모션그래픽_연구.md · 모션그래픽_깃허브연구.md · 기획/통독_모션_디자이너_v4d.md)
  · 마지막 프레임 = 짝이 되는 정적 그림 — 프레임은 정적 그림 글 + 진행 값(`레터그림판.진행적용` — 움직이는 요소의 data-m 주석). 진행이 다 1 이면
    정적 그림과 같은 글이다. 단계 경계의 프레임도 「그 단계까지 다 된」 상태다(경계검사). 숫자는 장부의 숫자뿐(사이 값의 숫자를 찍지 않는다 — 숫자글검사).
  · 이징: 위치 · 길이는 cubic in-out(「삼차」), 시계열 선은 x(시간) 몫으로 등속(「선형」), 글 · 색은 0.2초 등속, 멈춤 없이 붙은 두 움직임만
    in-cubic + out-cubic. 넘치는 이징은 없다(이징검사). 웹은 같은 이름의 Anime.js 이징(inOutCubic · linear · inCubic · outCubic)을 쓴다.
  · 리듬(v4e 리뷰 5순위): 글이 새로 선 뒤의 멈춤 = 0.6초 + 새 글자 수 ÷ 12(한국어 묵독 분당 약 700자), 아래 끝 1.0초(`멈춤`). 같은 종류 조작이
    이어지는 곳은 단계마다 제 글만큼 멈추고, 종류가 바뀌는 자리(마디)에서 독자가 넘긴다(웹 단계형). 장면 상한 24초(멈춤을 깎아 맞추지 않는다 —
    리뷰 4-2: 읽을 시간을 깎지 말고 단계를 독자에게 넘긴다. 넘으면 그 장면을 싣지 않는다).
  · 시간표: 단계 목록(몫 키 · 초 · 뒤멈춤 · 이징 · 자리 · 마디) — 자리 「<」 앞 단계와 동시 · 「-=x」 겹침 · 「+=x」 빈틈 · 없으면 앞 단계 끝 + 멈춤.
    시각은 정수 프레임으로 셈한다. 길이 0 단계 = 컷. 「마디」 가 붙은 단계의 끝이 웹 단계형의 한 걸음 끝이다.
장면(제목은 「대상 + 무엇」 평서 · 그림 표지 「<!-- 그림:종류 · 모션:A -->」 의 그림이 짝)
  A 매출에서 주당가치까지(그림 「가치」) — 단계형 넷: 빠지는 몫 셋 → Terminal Value 와 영업가치 → 비영업자산 · 차감과 주주가치 → 주식 수로 나누기(컷).
  B 경로와 기준선(그림 「길」) — 재생형: 실적(회색)은 처음부터 → 경로(x 등속) → 경로 끝 이름 → 맥락 가로선 함께 → 주가의 전제(--flag) → 「약 N배」 괄호.
  C 주가별로 전제된 정상 수준(그림 「자」) — 종가 표시 → 앞 글을 흐린 글로 → 표시가 트랙을 따라 옮겨 감(꼬리선 · 흔적 원) → 새 글 · 화살촉 · 변화율.
    정지점(종가 줄)이 둘이면 재생형(움직임 하나 = 사건 하나), 셋 이상이면 움직임마다 한 걸음인 단계형(2026-10-27 — 주가 경로의 꺾임
    · 평가기준일: 오르내림이 섞여 그림은 한 줄 트랙 대신 꺾은선 경로 — `레터그림판.자`). 정지점은 `레터궤적.앞꺾임` 이 고른다.
  장면이 서지 않으면 **조용히 빠지지 않는다**(2026-10-27 — 날짜 둘 판에서 C 가 소리 없이 빠진 사고): `서나` 가 까닭을 내고, 초안은 그림
  표지에 모션을 달지 않은 채 알림을 남기며(`표지달기`), 게이트 ⑬ 은 모션 표지가 있는데 장면이 서지 않으면 오류 · 장부에 적힌 장면의 표지가
  없으면 경보로 적는다(`점검`). 다른 회사에서도 같은 코드다.
산출: <곳>/motion_spec.json(장면마다 짝 그림 · 제목 · 단계 · 웹계획 · 길이 · 검사 · 설계 조항과 구현 여부) · A.mp4 · A.gif · A.png(포스터 = 마지막 프레임) ·
      A.dark.mp4 · A.dark.png … · --경계 <폴더> 면 장면마다 처음 · 단계 경계 · 끝 프레임 PNG.
"""
from __future__ import annotations

import argparse
import html as _html
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

여기 = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, 여기)
import 레터그림  # noqa: E402
import 레터그림판  # noqa: E402
import 레터HTML  # noqa: E402

최대초 = 24.0
기본fps = 30
칸폭 = 1120                      # 프레임 폭(px) — 넓은 판(viewBox 560)의 두 배(표시 폭 560px · 2배 해상도)
한장 = 60                        # 한 번에 찍는 프레임 수(격자 페이지 높이가 브라우저 한도를 넘지 않게)
쪽한도 = 16000                    # 격자 페이지 한 변의 상한(px) — 칸이 크면(배율을 올리면) 열 · 장 수를 줄인다(2026-10-27)
후보 = [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe", r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
      r"C:\Program Files\Google\Chrome\Application\chrome.exe"]

_쓸 = None


def 쓸브라우저(다시=False):
    """후보 가운데 헤드리스로 실제 파일을 쓰는 첫 브라우저(한 번 재고 기억한다). Edge 가 업데이트를 기다리는 동안에는 곧바로 끝나고
    아무것도 쓰지 않는 일이 있다(2026-10-16 실측 — rc 0 · 0.2초) — 그때 다음 후보(Chrome)로 간다. 띄운 시험 프로필의 프로세스만 끝낸다."""
    global _쓸
    if _쓸 and not 다시:
        return _쓸
    _쓸 = None
    for exe in [p for p in 후보 if os.path.isfile(p)]:
        d = tempfile.mkdtemp(prefix="브라우저시험_")
        h = os.path.join(d, "a.html")
        io.open(h, "w", encoding="utf-8").write("<html><body>test</body></html>")
        png = os.path.join(d, "a.png")
        try:
            subprocess.run([exe, "--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check", "--user-data-dir=" + os.path.join(d, "p"),
                            "--window-size=200,100", "--screenshot=" + png, "file:///" + h.replace("\\", "/")], capture_output=True, timeout=60)
        except subprocess.TimeoutExpired:
            pass
        됨 = os.path.exists(png)
        subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command",
                        "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -and $_.CommandLine.Contains('%s') } "
                        "| ForEach-Object { Stop-Process -Id $_.ProcessId -Force }" % os.path.basename(d)], capture_output=True)
        shutil.rmtree(d, ignore_errors=True)
        if 됨:
            _쓸 = exe
            return exe
    return None



# ══════════════════════════════════════════════════════════════════ 1. 이징 — 넘치지 않는 것만

def 선형(t):
    return t


def 삼차(t):                       # cubic in-out — d3 easeCubicInOut · Manim ease_in_out_cubic
    t *= 2
    return (t * t * t if t <= 1 else (t - 2) ** 3 + 2) / 2


def 삼차_들어감(t):                 # cubic in — 멈춤 없이 이어진 두 움직임의 앞쪽(Vizzu planner)
    return t * t * t


def 삼차_나감(t):                   # cubic out — 그 뒤쪽(경계에서 속도가 이어진다: 앞 끝 기울기 3 = 뒤 시작 기울기 3)
    return 1 - (1 - t) ** 3


이징들 = {"선형": 선형, "삼차": 삼차, "삼차_들어감": 삼차_들어감, "삼차_나감": 삼차_나감}


def 맞춤(이징, u):
    """[0,1] 밖은 자르고 끝은 정확히 0 · 1(d3 schedule tick — 끝나면 이징을 거치지 않는다)."""
    if u <= 0:
        return 0.0
    if u >= 1:
        return 1.0
    return 이징(u)


def 이징검사(n=1000):
    """이징마다 f(0)=0 · f(1)=1 · [0,1] 안 · 단조(넘침 없음). → 문제 목록."""
    낸 = []
    for 이름, f in 이징들.items():
        앞 = f(0.0)
        if abs(앞) > 1e-12 or abs(f(1.0) - 1) > 1e-12:
            낸.append("%s — 끝값이 0 · 1 이 아니다" % 이름)
        for k in range(1, n + 1):
            v = f(k / n)
            if v < -1e-12 or v > 1 + 1e-12 or v < 앞 - 1e-12:
                낸.append("%s — %.3f 에서 넘침 또는 되돌아감(%.4f)" % (이름, k / n, v))
                break
            앞 = v
    return 낸


# ══════════════════════════════════════════════════════════════════ 2. 시간표 — 단계 목록 → (키, 시작 프레임, 끝 프레임, 이징)

def 단계(몫=None, 초=0.0, 뒤=0.0, 이징="삼차", 자리=None, 마디=False):
    """단계 하나. 몫 = 진행 키(없으면 멈춤만) · 초 = 움직임 길이(0 이면 컷) · 뒤 = 그 뒤 멈춤 · 자리 = None | "<" | "+=x" | "-=x" ·
    마디 = 이 단계의 끝이 웹 단계형의 한 걸음 끝(v4e)."""
    return {"몫": 몫, "초": float(초), "뒤": float(뒤), "이징": 이징, "자리": 자리, "마디": bool(마디)}


def _펼치기(단계들, fps):
    """→ [(단계, 시작 프레임, 끝 프레임)], 전체 프레임 수. 초를 먼저 정수 프레임으로 바꾸고 프레임으로 더한다(누적 오차 없음)."""
    낸, 커서, 앞시작, 앞끝, 끝 = [], 0, 0, 0, 0
    for s in 단계들:
        길이 = int(round(s.get("초", 0.0) * fps))
        뒤 = int(round(s.get("뒤", 0.0) * fps))
        자리 = s.get("자리")
        if 자리 == "<":
            시작 = 앞시작
        elif 자리 and 자리[:2] in ("+=", "-="):
            d = int(round(float(자리[2:]) * fps))
            시작 = 앞끝 + (d if 자리[0] == "+" else -d)
        else:
            시작 = 커서
        시작 = max(0, 시작)
        e = 시작 + 길이
        낸.append((s, 시작, e))
        앞시작, 앞끝 = 시작, e
        커서 = max(커서, e + 뒤)
        끝 = max(끝, 커서)
    return 낸, max(끝, 1)


def 시간표(단계들, fps):
    """→ ([(키, 시작 프레임, 끝 프레임, 이징 이름)], 전체 프레임 수). 전체 프레임 수 = 마지막 멈춤까지 — 마지막 프레임(전체 − 1)에서 모든 키가 1 이다."""
    펼, 전체 = _펼치기(단계들, fps)
    낸 = []
    for s, a, e in 펼:
        if s.get("몫"):
            if s.get("이징") not in 이징들:
                raise ValueError("모르는 이징: %s" % s.get("이징"))
            낸.append((s["몫"], a, e, s.get("이징", "삼차")))
    return 낸, 전체


def 마디들(단계들, fps):
    """웹 단계형의 걸음 → [(시작 프레임, 끝 프레임)] — 걸음의 시작 = 앞 걸음 끝 뒤의 첫 움직임, 끝 = 「마디」 단계의 끝."""
    펼, _전체 = _펼치기(단계들, fps)
    낸, 시작 = [], None
    for s, a, e in 펼:
        if s.get("몫") and 시작 is None:
            시작 = a
        if s.get("마디") and 시작 is not None:
            낸.append((시작, e))
            시작 = None
    return 낸


def 상태(표, k):
    """프레임 k → {키: 0~1}. 아직 안 온 키 0, 지난 키 1. 길이 0 단계(컷)는 시작 프레임부터 1."""
    낸 = {}
    for 키, a, b, 이 in 표:
        u = (1.0 if k >= a else 0.0) if b <= a else (k - a) / float(b - a)
        낸[키] = round(맞춤(이징들[이], u), 6)
    return 낸


def 프레임들(표, 전체):
    """→ [[상태, 머묾]] — 같은 상태가 이어지면 한 장으로 묶는다(멈춤 구간은 SVG 한 장)."""
    낸 = []
    for k in range(전체):
        st = 상태(표, k)
        if 낸 and 낸[-1][0] == st:
            낸[-1][1] += 1
        else:
            낸.append([st, 1])
    return 낸


def 경계들(표, 전체):
    """처음 · 단계 경계(키마다 끝 프레임) · 끝 프레임 번호."""
    return sorted({0, 전체 - 1} | {min(b, 전체 - 1) for _k, _a, b, _e in 표})


def 맞추기(단계들, fps, 최대=최대초):
    """상한(24초) 안이면 그대로, 넘으면 None(장면을 싣지 않는다). v4e — 멈춤(읽을 시간)을 깎아 맞추지 않는다(리뷰 4-2)."""
    _표, n = 시간표(단계들, fps)
    return 단계들 if n / float(fps) <= 최대 + 1e-9 else None


# ══════════════════════════════════════════════════════════════════ 3. 장면 — 짝 그림 종류마다 단계 목록

글초 = 0.2          # 글 · 색 — 등속 0.2초
움직임 = 0.7        # 위치 · 길이 — cubic in-out


def 멈춤(*글들, 아래=1.0):
    """새로 선 글을 읽는 멈춤(초) = 0.6 + 글자 수 ÷ 12 — 빈칸은 세지 않는다. 아래 끝 1.0초(리뷰 5순위)."""
    n = sum(len(re.sub(r"\s", "", "%s" % g)) for g in 글들 if g)
    return round(max(아래, 0.6 + n / 12.0), 2)


def _짧(글):
    return re.sub(r"\s*(조 원|억 원|만 원|원)$", "", re.sub(r"\*", "", "%s" % 글).strip())


def 장면_가치(표들, 제목="", 빠르게=False):
    """A — 매출에서 주당가치까지(단계형 넷). 줄여 가는 줄은 줄마다 막대(0.7초) → 글(0.2초) → 제 글만큼 멈춤, 더하고 빼는 다리와 그 합계는 한 걸음,
    주식 수로 나누기는 컷. 걸음(마디) = 종류가 바뀌는 자리.
    빠르게(1.1.10) — 상한을 넘을 때 한 번 더 짓는 판: 막대가 움직이는 시간만 줄인다(막대마다 0.3초 — 다리 둘 짝도 0.3초씩).
    멈춤(읽을 시간)은 그대로다(v4e) — 날짜 둘 이월 · 자본거래 줄 · 브리지 조정 줄이 많은 회사가 24.1 ~ 25.0초로 장면을 잃었다."""
    움 = 0.3 if 빠르게 else 움직임
    항 = 레터그림.가치항(표들)
    if not 항:
        return None
    단 = [단계(뒤=1.2)]
    k, n = 1, len(항)
    while k < n:
        d = 항[k]
        if d["a"] is None:                               # 주식 수로 나누기 — 단위가 바뀌므로 컷(그 뒤 글만 있는 줄도 함께) · 식 한 줄
            글 = [x["금액"] for x in 항[k:]] + [항[k - 1]["금액"]]
            for j in range(k, n):
                단.append(단계("글:%d" % j, 0.0, max(2.0, 멈춤(*글)) if j == n - 1 else 0.0, "선형", 자리="<" if j > k else None, 마디=j == n - 1))
            k = n
            break
        if d["셈"] == "":                                # 줄여 감 — 같은 종류가 이어지는 동안은 줄마다 제 글만큼 멈추고, 끝 줄이 마디
            묶 = [k]
            while 묶[-1] + 1 < n and 항[묶[-1] + 1]["셈"] == "" and 항[묶[-1] + 1]["a"] is not None:
                묶.append(묶[-1] + 1)
            for t, j in enumerate(묶):
                x = 항[j]
                단 += [단계("막대:%d" % j, 움), 단계("글:%d" % j, 글초, 멈춤(_짧(x["금액"]), x["빠짐"], x.get("주석")), "선형", 마디=t == len(묶) - 1)]
            k = 묶[-1] + 1
            continue
        if d["셈"] in ("+", "−"):                        # 더하고 빼는 다리 — 붙은 줄을 모아 이어진 움직임으로, 합계(= 줄)와 한 걸음
            묶 = [k]
            while 묶[-1] + 1 < n and 항[묶[-1] + 1]["셈"] in ("+", "−") and 항[묶[-1] + 1]["a"] is not None:
                묶.append(묶[-1] + 1)
            if len(묶) == 2:
                반 = 0.3 if 빠르게 else 0.5
                단 += [단계("막대:%d" % 묶[0], 반, 이징="삼차_들어감"), 단계("막대:%d" % 묶[1], 반, 이징="삼차_나감")]
            else:
                단 += [단계("막대:%d" % j, 움) for j in 묶]
            합 = 묶[-1] + 1 if 묶[-1] + 1 < n and 항[묶[-1] + 1]["셈"] == "=" else None
            글키 = 묶 + ([합] if 합 is not None else [])
            글 = [항[j]["셈"] + _짧(항[j]["금액"]) for j in 묶] + [항[j].get("주석") for j in 글키] + ([_짧(항[합]["금액"])] if 합 is not None else [])
            for t, j in enumerate(글키):
                끝 = t == len(글키) - 1
                단.append(단계("글:%d" % j, 글초, 멈춤(*글) if 끝 else 0.0, "선형", 자리="<" if t else None, 마디=끝))
            k = (합 + 1) if 합 is not None else 묶[-1] + 1
            continue
        단.append(단계("글:%d" % k, 글초, 멈춤(_짧(d["금액"]), d.get("주석")), "선형", 마디=True))      # = 줄(앞이 다리가 아닌 합계) · 그 밖
        k += 1
    단.append(단계(뒤=1.0))
    return 단


def 장면_길(표들, 제목=""):
    """B — 경로와 기준선(재생형): 실적(회색)은 처음부터 → 경로(x 등속 2초) → 경로 끝 이름 → 맥락 가로선(함께) → 주가의 전제(--flag) → 「약 N배」 괄호.
    공개 단계는 넷(경로 · 맥락 · 초점 · 주석 — 리뷰 B)."""
    z = 레터그림판.길자료(표들, 제목)
    if not z or len(z["경로"]) < 2:
        return None
    차 = 레터그림판.길차례(표들, 제목)
    선 = {d["i"]: d for d in z["선"]}
    단 = [단계(뒤=1.2), 단계("선", 2.0, 0.0, "선형")]
    if 차["경로글"] is not None:
        d = 선[차["경로글"]]
        단.append(단계("선글", 글초, 멈춤(d["값글"], d["이름"]), "선형"))
    for 무리 in (차["맥락"], 차["강조"]):
        if not 무리:
            continue
        for t, i in enumerate(무리):
            단.append(단계("가로:%d" % i, 0.6, 자리="<" if t else None))
        for t, i in enumerate(무리):
            단.append(단계("가로글:%d" % i, 글초, 멈춤(*[x for j in 무리 for x in (선[j]["값글"], 선[j]["이름"])]) if t == len(무리) - 1 else 0.0,
                         "선형", 자리="<" if t else None))
    if 차["주석"]:
        단.append(단계("주석", 0.4, max(2.0, 멈춤("약 " + z["주석"]["글"])), "선형"))
    else:
        단.append(단계(뒤=2.0))
    return 단


def 장면_자(표들, 제목=""):
    """C — 주가별로 전제된 정상 수준(재생형): 첫 종가 표시 · 글 → (앞 글을 흐린 글로 → 표시가 트랙을 따라 다음 종가로(꼬리선 · 흔적 원) → 새 글 ·
    화살촉 · 변화율) × 정지점. 끝 멈춤 3초 이상."""
    종 = 레터그림.자종가(표들)
    if len(종) < 2:
        return None
    줄들 = 표들[0][1]
    여러 = len(종) >= 3                                  # 2026-10-27 — 움직임이 둘 이상이면 움직임마다 한 걸음(웹 단계형 — 독자가 그 정지점의 글을 읽고 넘긴다)

    def 글(k):
        return [c for c in 줄들[k] if c and c.strip() not in ("—", "-")]
    단 = [단계(뒤=1.2), 단계("점0", 글초, 멈춤(*글(종[0])), "선형", 마디=여러)]
    for j in range(1, len(종)):
        끝 = j == len(종) - 1
        단 += [단계("내림:%d" % j, 글초, 0.0, "선형"), 단계("옮김:%d" % j, 1.0),
              단계("글:%d" % j, 글초, max(3.0 if 끝 else 1.0, 멈춤(*글(종[j]))), "선형", 마디=여러)]
    return 단


장면틀 = {"가치": 장면_가치, "길": 장면_길, "자": 장면_자}      # v4e — D(토네이도)는 모션 폐기: 시작과 끝 사이에 정적 그림에 없는 사건이 없다


def 서나(종류, 표들, 제목="", fps=기본fps):
    """그림 종류 · 표로 모션 장면이 서는가 → (단계 목록, None) 또는 (None, 까닭 글). 까닭은 알림 · 게이트가 그대로 적는다(2026-10-27 —
    장면이 조용히 빠지지 않게). 판정은 장면 함수 하나가 한다 — 여기는 까닭만 붙인다."""
    if 종류 not in 장면틀:
        return None, "그림 「%s」 에는 모션 장면이 없다(장면이 있는 그림: %s)" % (종류, " · ".join(장면틀))
    단 = 장면틀[종류](표들, 제목)
    if not 단:
        if 종류 == "자":
            n = len(레터그림.자종가(표들))
            return None, ("종가 줄이 %d개다 — 정지점이 둘 이상이어야 주가 표시가 옮겨 간다(평가기준일 앞 주가 경로에 확정된 꺾임이 없고 "
                          "평가기준일 뒤 자료도 없으면 하나다)" % n)
        if 종류 == "길":
            return None, "경로의 점이 둘 미만이다(그림 표의 기준 시나리오 줄 · 연도 머리를 못 읽었다)"
        if 종류 == "가치":
            return None, "가치 표의 계산 단계를 못 읽었다(매출 · 영업이익 · FCFF … 주당가치 줄)"
        return None, "장면의 단계를 세우지 못했다"
    if not 맞추기(단, fps) and 종류 == "가치":                    # 1.1.10 — 막대 움직임만 줄인 판으로 한 번 더(멈춤은 그대로)
        빠른 = 장면_가치(표들, 제목, 빠르게=True)
        if 빠른 and 맞추기(빠른, fps):
            return 빠른, None
    if not 맞추기(단, fps):
        _표, n = 시간표(단, fps)
        return None, "%.1f초 — 상한 %d초를 넘는다(멈춤을 깎지 않는다 — 정지점 · 단계를 줄인다)" % (n / float(fps), 최대초)
    return 단, None


def 표지달기(L, 모, 맥=None):
    """그림 블록 줄 L(첫 줄 「<!-- 그림:종류 -->」)에 모션 표지(「<!-- 그림:종류 · 모션:모 -->」)를 단다 — 그 블록의 표로 장면이 서면 달고,
    안 서면 정적 표지 그대로 두고 까닭을 맥.알림에 적는다(2026-10-27 — 조용한 탈락을 막는다 · 같은 알림은 한 번). → L(고친 목록)."""
    if not L:
        return L
    m = _표지.match(L[0].strip())
    if not m:
        return L
    블 = _블록들("\n".join([("<!-- 그림:%s -->" % m.group(1))] + list(L[1:])))
    if not 블:
        return L
    종, _모, 제목, 표들 = 블[0]
    단, 까닭 = 서나(종, 표들, 제목)
    if 단:
        L[0] = "<!-- 그림:%s · 모션:%s -->" % (종, 모)
        if 맥 is not None and isinstance(getattr(맥, "모션", None), dict):
            맥.모션.setdefault(모, {})                     # 표지를 단 장면은 장부에 적는다(제목 · 메시지는 그 장면의 자리 — 레터막 — 가 채운다)
    elif 맥 is not None:
        말 = "모션 %s(그림 「%s」 — %s) 을 싣지 않았다 — %s" % (모, 종, _그림제목(제목) or 제목[:30], 까닭)
        if 말 not in 맥.알림:
            맥.알림.append(말)
    return L


def 점검(글, 장부, fps=기본fps):
    """레터(마크다운) · 장부 → (오류, 경보, 선 장면) — 오류: 모션 표지가 있는데 장면이 서지 않는다(까닭과 함께) · 장부 「모션」 에 없는 표지.
    경보: 장부 「모션」 에 적힌 장면인데 그 표지를 단 그림이 없다(초안이 장면을 세우지 못해 표지를 달지 않은 자리 — 알림과 같은 까닭).
    선 장면: [(모션, 그림 종류, 방식, 초)] — 게이트 기록에 남긴다."""
    모 = (장부 or {}).get("모션") or {}
    오, 경, 선 = [], [], []
    본 = set()
    for 종, 이, 제목, 표들 in _블록들(글):
        if not 이:
            continue
        본.add(이)
        이름 = _그림제목(제목) or 제목[:30]
        if 장부 is not None and 이 not in 모:
            오.append("모션 %s(그림 「%s」 — %s) — 장부 「모션」 에 없는 장면이다" % (이, 종, 이름))
            continue
        단, 까닭 = 서나(종, 표들, 제목, fps)
        if not 단:
            오.append("모션 %s(그림 「%s」 — %s) — 표지가 있는데 장면이 서지 않는다: %s" % (이, 종, 이름, 까닭))
            continue
        계 = 웹계획(종, 표들, 제목, fps)
        선.append((이, 종, (계 or {}).get("방식"), (계 or {}).get("초")))
    for 이 in 모:
        if 이 not in 본:
            경.append("모션 %s — 장부에 적힌 장면인데 표지를 단 그림이 없다(초안 알림에 까닭)" % 이)
    return 오, 경, 선


def 서지않는표지걷기(글, fps=기본fps):
    """1.1.8 — 모션 표지가 붙었는데 장면이 서지 않는 그림(`서나` 가 까닭을 내는 그림 — 단계가 많아 상한 초를 넘는 따위)의 표지에서 모션만 걷는다.
    그림은 정지 그림으로 남는다. 종전에는 초안이 표지를 그대로 달아 게이트 ⑬ 이 막았고 손 편집으로 걷었다. → (새 글, [(모션, 까닭)])."""
    걷은 = []
    for 종, 이, 제목, 표들 in _블록들(글):
        if not 이:
            continue
        단, 까닭 = 서나(종, 표들, 제목, fps)
        if not 단:
            걷은.append((이, 까닭))
    for 이, _까 in 걷은:
        글 = re.sub(r"(<!--\s*그림:\S+?)\s*·\s*모션:%s(\s*-->)" % re.escape(이), lambda m: m.group(1) + m.group(2), 글)
    return 글, 걷은


def 웹계획(종류, 표들, 제목="", fps=기본fps):
    """웹 모션의 시간표(JSON 으로 레터 HTML 에 싣는다) — 영상과 같은 단계 목록 · 같은 정수 프레임에서 낸다(한 출처).
    → {"종류", "방식"(단계 · 재생), "초", "키": [{"k", "s", "e", "이징"}], "마디": [[시작초, 끝초]]} 또는 None(장면이 서지 않는다 — 까닭은 `서나`)."""
    단, _까닭 = 서나(종류, 표들, 제목, fps)
    if not 단:
        return None
    표, 전체 = 시간표(단, fps)
    마 = 마디들(단, fps)
    f = float(fps)
    return {"종류": 종류, "방식": "단계" if len(마) >= 2 else "재생", "초": round(전체 / f, 3),
            "키": [{"k": k, "s": round(a / f, 3), "e": round(b / f, 3), "이징": e} for k, a, b, e in 표],
            "마디": [[round(a / f, 3), round(b / f, 3)] for a, b in 마]}


# ══════════════════════════════════════════════════════════════════ 4. 레터에서 짝 그림 찾기 · 명세

_표지 = re.compile(r"^<!--\s*그림:(\S+)(?:\s*·\s*모션:([A-Z][A-Za-z0-9]*))?\s*-->$")


def _블록들(글):
    """마크다운 → [(종류, 모션 또는 None, 제목, [(머리, 줄들)])] — 그림 표지 뒤의 굵은 제목과 표들."""
    줄 = 글.split("\n")
    낸 = []
    i = 0
    while i < len(줄):
        m = _표지.match(줄[i].strip())
        if not m:
            i += 1
            continue
        i += 1
        제목 = ""
        if i < len(줄) and 줄[i].strip() and not 줄[i].strip().startswith("|"):
            제목 = re.sub(r"\*", "", 줄[i].strip())
            i += 1
        표들, i = 레터HTML._표줄들(줄, i)
        낸.append((m.group(1), m.group(2), 제목, [(머, 행) for 머, 행, _b in 표들]))
    return 낸


def 그림블록들(글):
    """마크다운 → {종류: (제목, [(머리, 줄들)])} — 같은 종류는 첫 블록."""
    낸 = {}
    for 종, _모, 제목, 표들 in _블록들(글):
        낸.setdefault(종, (제목, 표들))
    return 낸


def 모션블록들(글):
    """마크다운 → {모션: (종류, 제목, 표들)} — 표지에 모션이 붙은 그림만(같은 모션은 첫 블록)."""
    낸 = {}
    for 종, 모, 제목, 표들 in _블록들(글):
        if 모:
            낸.setdefault(모, (종, 제목, 표들))
    return 낸


def _그림제목(제목):
    """「그림 13. 매출에서 … — 설명」 → 「매출에서 …」(번호 · 설명을 뗀 이름)."""
    t = re.split(r"\s—\s", 제목)[0]
    return re.sub(r"^그림\s*\d*\.\s*", "", t).strip()


def 명세(글, 장부, fps=기본fps):
    """→ {"판", "fps", "장면": {모션: {"그림", "제목", "메시지", "단계", "초", "_표", "_전체"}}, "블": {모션: (제목, 표들)}}.
    장부의 「모션」 에 없거나 짝 그림의 표가 장면을 못 세우면 빠진다."""
    모 = (장부 or {}).get("모션") or {}
    블 = 모션블록들(글)
    장면, 쓴블, 빠짐 = {}, {}, {}
    for 이, (종, 제목, 표들) in 블.items():
        if 이 not in 모:
            빠짐[이] = "장부 「모션」 에 없는 장면이다"
            continue
        단, 까닭 = 서나(종, 표들, 제목, fps)
        if not 단:
            빠짐[이] = 까닭
            print("모션 %s — 싣지 않는다: %s" % (이, 까닭))
            continue
        표, 전체 = 시간표(단, fps)
        장면[이] = {"그림": 종, "제목": (모[이].get("제목") or _그림제목(제목)), "메시지": 모[이].get("메시지", ""),
                  "단계": [{"키": k, "시작초": round(a / float(fps), 3), "끝초": round(b / float(fps), 3), "이징": e} for k, a, b, e in 표],
                  "초": round(전체 / float(fps), 2), "웹계획": 웹계획(종, 표들, 제목, fps), "_표": 표, "_전체": 전체}
        쓴블[이] = (제목, 표들)
    for 이 in 모:
        if 이 not in 블:
            빠짐.setdefault(이, "장부에 적힌 장면인데 표지를 단 그림이 없다")
    return {"판": 판, "fps": fps, "장면": 장면, "블": 쓴블, "영상": 영상설명, "설계조항": 설계조항, "빠짐": 빠짐}


판 = "v4g"
영상설명 = ("mp4 · gif · 포스터는 스크립트가 돌지 않는 곳(네이버 프리미엄 콘텐츠 · 메일 · SNS)에 붙이는 파일이다. 웹 레터는 영상을 쓰지 않고 레터 안의 "
         "SVG 를 같은 시간표(웹계획)로 움직인다. 영상은 넓은 판(viewBox 560)을 2배(1120px)로 구웠다 — 표시 폭 560px 에서 주 글 14px · 보조 12.5px · 축 12px. "
         "GIF 는 한 번만 재생한다(반복 표지 없음). 메일 본문에는 GIF 대신 포스터(PNG — 마지막 프레임 = 정적 그림)와 웹 레터 링크를 붙인다(모션 리뷰 중-8).")
설계조항 = [      # 리뷰 4-5 — 「설계 조항 : 구현 여부」(다음 판부터 대조)
    ["정적 그림 먼저 · 「순서대로 보기」 로만 시작(자동 재생 없음)", "구현 — 레터HTML.모션JS"],
    ["한 번에 한 장면(다른 장면을 시작하면 재생 중이던 장면은 완성 그림으로)", "구현"],
    ["A 단계형(「다음 ▸ 1/4」 · 이전 · ← → · Esc)", "구현 — 마디"],
    ["줄인 움직임 · 인쇄 · 스크립트 꺼짐 = 정적 그림", "구현 — 단추를 달지 않음 · 인쇄 전 완성 그림"],
    ["본문 토큰 팔레트(--accent · --flag · 맥락선 · 면 맥락 + 테두리)", "구현 — 그림 열아홉"],
    ["글자 크기(표시 기준 주 14 · 보조 12.5 · 하한 12px) · 휴대폰은 좁은 판", "구현 — 레터그림검사 ① · v4f 390px 보다 좁은 화면(375 · 360)은 그림이 "
     "본문 여백 쪽으로 나와 358px(360 은 352px)를 쓴다(레터그림.CSS)"],
    ["그림마다 핵심 비교 주석 하나 · 출처 줄", "구현 — A 비율 · B 약 N배 · C 「한 달, 변화율」 · D 변화율(정적) · 계단 「증가율 하락 시작」"],
    ["멈춤 = 0.6 + 글자 수 ÷ 12(아래 끝 1.0초)", "구현 — 멈춤()"],
    ["검사: 글자 12px · 라벨 겹침 0 · 대비 3:1 · 4.5:1 · 가려진 점 0", "구현 — 레터그림검사(게이트 ⑬ · 꼴 시험)"],
    ["검사: 라벨과 마크(막대 · 점 · 선) 겹침 0", "구현 — 레터그림검사 ⑤(v4f · `마크=True` — 게이트 ⑬ 배선 대기)"],
    ["D 모션 폐기(정적 토네이도)", "구현"],
    ["단추 자리 고정(주 단추가 늘 오른쪽 끝 — 「완성 그림」 이 나타나도 움직이지 않음)", "구현 — v4f"],
    ["C 자에 고른 간격 눈금(선형인지 보이게 — 글 없음)", "구현 — v4f"],
    ["M1 궤적: 세로선 머리에 이름과 날짜 · 값 글은 제 점 곁(남의 점 · 기준선 위에 서지 않음)", "구현 — v4f(정적)"],
    ["M5 계단: 실적 + 추정 해 막대 쌓기(「그중 실적」 줄) · 0 아래 증가율 눈금 · 「증가율 하락 시작」", "구현 — v4f(정적 · 「그중 실적」 줄은 레터 생성기 배선 대기)"],
    ["B 길: 잔여 기간 「N개월」 머리를 달력 자리로(평가기준일이 3월 말 · 9월 말인 회사)", "구현 — v4f"],
    ["GIF 한 번 재생 · 메일은 포스터 PNG + 웹 링크", "구현 — 엮기 · 영상설명"],
    ["웹 SVG 직접 애니메이션의 시계", "Anime.js v4.5.0(인라인 · MIT) — 리뷰가 권한 WAAPI 대신(자료/모션그래픽_연구.md (아)의 결정)"],
    ["C 정지점 = 평가기준일 앞 주가 경로의 확정된 꺾임(가장 늦은 것부터) · 평가기준일 · 뒤 저점 — 넷까지", "구현 — v4g(레터궤적.앞꺾임 · 카드_계산 과 같은 규칙)"],
    ["C 정지점 셋 이상 = 꺾은선 주가 경로 · 움직임마다 한 걸음(단계형)", "구현 — v4g(레터그림판.자 길모드 · 장면_자 마디)"],
    ["첫 화면(3분 레터) 그림 1 · 2 에도 모션 B · C(본편 15절 짝 그림과 같은 표)", "구현 — v4g(레터3분 · 표지달기)"],
    ["장면이 서지 않으면 조용히 빠지지 않는다 — 초안 알림 · 게이트 ⑬(표지 있는데 장면 없음 = 오류 · 장부만 = 경보)", "구현 — v4g(서나 · 표지달기 · 점검)"],
]


def 프레임그림(spec, 이, 진행):
    """영상의 한 프레임 = 넓은 판 정적 그림 + 진행(웹과 같은 규칙 — `레터그림판.진행적용`)."""
    return 레터그림판.진행적용(정적그림(spec, 이), 진행)


def 정적그림(spec, 이, 판="넓은"):
    """짝 그림의 정적 그림 — 두 판 그림은 판(넓은 · 좁은)을 고른다(영상은 넓은 판, 웹은 둘 다 움직인다)."""
    x = spec["장면"][이]
    제목, 표들 = spec["블"][이]
    f = 레터그림.그림들[x["그림"]]
    return f(표들, 제목, 판=판) if x["그림"] in 레터그림.두판 else f(표들, 제목)


def 경계읽힘(spec, 이):
    """v4f — 단계 경계(다 된 단계까지 그린 순수 프레임)마다 「읽히는가」(`레터그림검사.그림검사` ①~⑤ — 글자 · 겹침 · 대비 · 가려진 점 ·
    라벨과 마크)를 두 판 다 잰다. 웹 단계형은 독자가 그 자리에서 멈춰 읽고, 영상은 그 자리에서 멈춘다 — 끝 그림만 재면 중간의 겹침을 못 본다.
    → [(판, 프레임, 번호, 내용)]."""
    import 레터그림검사                                      # noqa: PLC0415 — 레터그림검사가 레터모션을 부른다(늦게 부른다)
    x = spec["장면"][이]
    표, 전체 = x["_표"], x["_전체"]
    낸 = []
    for 판 in (("넓은", "좁은") if x["그림"] in 레터그림.두판 else ("한판",)):
        정 = 정적그림(spec, 이, "넓은" if 판 == "한판" else 판)
        본 = set()
        for k in 경계들(표, 전체):
            st = 상태(표, k)
            if not all(v in (0.0, 1.0) for v in st.values()):
                continue
            for 번, 말 in 레터그림검사.그림검사(레터그림판.진행적용(정, st), None if 판 == "한판" else 판, 마크=True):
                if (번, 말) not in 본:
                    본.add((번, 말))
                    낸.append((판, k, 번, 말))
    return 낸


# ══════════════════════════════════════════════════════════════════ 5. 검사 — 끝 = 정적 · 경계 = 다 된 단계 · 숫자는 장부 글만

_글뽑기 = re.compile(r"<(text|title)\b[^>]*>(.*?)</\1>", re.S)
숫자꼴 = re.compile(r"\d[\d,]*(?:\.\d+)?")


def 글들(svg):
    return [_html.unescape(re.sub(r"<[^>]+>", "", m.group(2))) for m in _글뽑기.finditer(svg)]


def 숫자글검사(프레임svgs, 허용글들):
    """프레임에 찍힌 숫자가 허용 글(그림 표의 칸 · 정적 그림의 글)의 숫자에 다 있는가 — 사이 값의 숫자(카운트업)가 새면 그 숫자를 돌려준다."""
    허용 = {m for g in 허용글들 for m in 숫자꼴.findall("%s" % g)}
    샌 = []
    for svg in 프레임svgs:
        for g in 글들(svg):
            for m in 숫자꼴.findall(g):
                if m not in 허용:
                    샌.append(m)
    return sorted(set(샌))


def 검사(spec, 이):
    """→ {"짝같음", "경계": [(프레임, 순수, 같음)], "샌숫자", "초", "고유"} — 문제가 있으면 "문제" 목록."""
    x = spec["장면"][이]
    표, 전체 = x["_표"], x["_전체"]
    정 = 정적그림(spec, 이)
    문제 = []
    끝상태 = 상태(표, 전체 - 1)
    if any(v != 1.0 for v in 끝상태.values()):
        문제.append("마지막 프레임에 1 이 아닌 키가 있다")
    짝 = 프레임그림(spec, 이, 끝상태) == 정
    if not 짝:
        문제.append("마지막 프레임 ≠ 정적 그림")
    경 = []
    for k in 경계들(표, 전체):
        st = 상태(표, k)
        순수 = all(v in (0.0, 1.0) for v in st.values())
        정준 = {키: (1.0 if b <= k and (b > a or k >= a) else 0.0) for 키, a, b, _e in 표}
        같음 = (프레임그림(spec, 이, st) == 프레임그림(spec, 이, 정준)) if 순수 else None
        경.append((k, 순수, 같음))
        if 순수 and not 같음:
            문제.append("경계 프레임 %d 이 다 된 단계의 그림과 다르다" % k)
    제목, 표들 = spec["블"][이]
    허용 = [c for _m, 행 in 표들 for r in 행 for c in r] + [c for 머, _행 in 표들 for c in 머] + 글들(정) + [제목]
    프 = 프레임들(표, 전체)
    샌 = 숫자글검사([프레임그림(spec, 이, st) for st, _n in 프], 허용)
    if 샌:
        문제.append("프레임에 장부 글이 아닌 숫자 — %s" % ", ".join(샌[:10]))
    if 전체 / float(spec["fps"]) > 최대초 + 1e-9:
        문제.append("%.2f초 — %d초를 넘는다" % (전체 / float(spec["fps"]), 최대초))
    읽 = 경계읽힘(spec, 이)
    for 판, k, 번, 말 in 읽[:6]:
        문제.append("경계 프레임 %d(%s 판) 읽힘 %s %s" % (k, 판, 번, 말))
    return {"짝같음": 짝, "경계": 경, "샌숫자": 샌, "초": round(전체 / float(spec["fps"]), 2), "고유": len(프), "읽힘": len(읽), "문제": 문제}


# ══════════════════════════════════════════════════════════════════ 6. 찍기 · 엮기

def _브라우저(덧, 주소):
    exe = 쓸브라우저()
    if not exe:
        raise SystemExit("헤드리스로 그림을 쓰는 Edge · Chrome 을 못 찾았다 — 모션을 찍지 못한다")
    프로필 = tempfile.mkdtemp(prefix="레터모션_")
    표지 = os.path.basename(프로필)
    p = subprocess.Popen([exe, "--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check", "--disable-extensions",
                          "--user-data-dir=" + 프로필, "--hide-scrollbars", "--force-device-scale-factor=1"] + 덧 + [주소],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        _o, 오류 = p.communicate(timeout=180)
        if os.environ.get("LETTER_MOTION_DEBUG"):
            print("브라우저 rc %s — %s" % (p.returncode, (오류 or b"")[-600:].decode("utf-8", "replace")))
    except subprocess.TimeoutExpired:
        p.kill()
    명령 = ("Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -and $_.CommandLine.Contains('%s') } "
          "| ForEach-Object { Stop-Process -Id $_.ProcessId -Force }") % 표지                # 이 프로필로 띄운 것만 끝낸다
    subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", 명령], capture_output=True)
    shutil.rmtree(프로필, ignore_errors=True)


def _id따로(svg, k):
    """격자 한 장의 칸 k 의 SVG — 안의 id(잘라 보이는 사각형 · 그러데이션 …)와 그 id 를 부르는 url(#…) · href="#…" 에 칸 꼬리를 단다.
    같은 그림의 프레임 여럿이 한 페이지에 들어가면 id 가 겹쳐 모든 칸이 첫 칸(움직이기 전)의 정의를 읽는다(2026-10-27 — 장면 B 의 경로가
    잘라 보이는 사각형 폭 6 인 첫 프레임의 정의를 읽어 모든 프레임에서 사라진 결함 · 웹 레터는 그림마다 id 가 달라 걸리지 않았다)."""
    for i in sorted(set(re.findall(r'\bid="([^"]+)"', svg)), key=len, reverse=True):
        새 = "%s-k%d" % (i, k)
        svg = re.sub(r'\bid="%s"' % re.escape(i), 'id="%s"' % 새, svg)
        svg = svg.replace("url(#%s)" % i, "url(#%s)" % 새).replace('href="#%s"' % i, 'href="#%s"' % 새)
    return svg


def 픽셀같음(a, b, 문턱=16, 몫=0.001):
    """두 PIL 그림이 픽셀로 같은가 — 크기가 같고, 채널 차가 문턱을 넘는 픽셀이 몫 이하(글꼴 안티에일리어싱의 흔들림만 허용). → (같음, 다른 몫)."""
    from PIL import ImageChops
    if a.size != b.size:
        return False, 1.0
    d = ImageChops.difference(a.convert("RGB"), b.convert("RGB")).convert("L").point(lambda v: 255 if v > 문턱 else 0)
    n = d.histogram()[255]
    r = n / float(a.size[0] * a.size[1])
    return r <= 몫, r


def _한판(svgs, 높이, 임시, 어둠, 번):
    from PIL import Image
    열 = max(1, min(6, 쪽한도 // 칸폭, len(svgs)))
    줄수 = (len(svgs) + 열 - 1) // 열
    머 = 레터HTML.머리.replace("{{제목}}", "모션").replace("</style>", 레터그림.CSS + "</style>", 1)
    머 = re.sub(r'<link[^>]+fonts\.g[^>]+>\s*', "", 머)              # 바깥 글꼴을 부르지 않는다(헤드리스 · 오프라인) — 페이지와 같은 대체 글꼴
    if 어둠:
        머 = 머.replace('<html lang="ko">', '<html lang="ko" data-theme="dark">', 1)
    칸 = "".join('<div class="f" style="left:%dpx;top:%dpx">%s</div>' % ((k % 열) * 칸폭, (k // 열) * 높이, _id따로(s, k)) for k, s in enumerate(svgs))
    page = 머 + ('<body style="margin:0;background:var(--paper)"><style>.f{position:absolute;width:%dpx;height:%dpx;overflow:hidden;'
                 'background:var(--paper)} .f svg.viz{width:%dpx;height:auto;display:block;max-width:none;margin:0}</style>%s</body></html>'
                 % (칸폭, 높이, 칸폭, 칸))
    h = os.path.join(임시, "격자%d.html" % 번)
    io.open(h, "w", encoding="utf-8").write(page)
    png = os.path.join(임시, "격자%d.png" % 번)
    if os.path.exists(png):
        os.remove(png)
    for 번째 in range(3):                                   # 여러 장면을 함께 찍을 때 브라우저가 늦게 뜨거나 그림을 못 쓰는 일이 있다 — 세 번까지 다시
        _브라우저(["--window-size=%d,%d" % (열 * 칸폭, 줄수 * 높이), "--virtual-time-budget=5000", "--screenshot=" + png],
               "file:///" + h.replace("\\", "/"))
        시작 = time.time()
        while not os.path.exists(png) and time.time() - 시작 < 30:
            time.sleep(0.5)
        if os.path.exists(png):
            break
        print("찍기 다시(%d) — %s" % (번째 + 1, os.path.basename(h)))
        쓸브라우저(다시=True)                                 # 쓰던 브라우저가 멈췄으면 다시 고른다
    if not os.path.exists(png):
        raise SystemExit("모션 프레임을 찍지 못했다 — %s" % h)
    time.sleep(0.3)                                          # 파일을 다 쓴 뒤 연다
    Image.MAX_IMAGE_PIXELS = None                            # 이 함수가 찍은 격자 한 장(프레임 60개 × 2배) — 바깥 파일이 아니다(큰 그림 경고 · 오류를 끈다)
    im = Image.open(png).convert("RGB")
    return [im.crop(((k % 열) * 칸폭, (k // 열) * 높이, (k % 열 + 1) * 칸폭, (k // 열 + 1) * 높이)) for k in range(len(svgs))]


def 찍기(svgs, 높이, 임시, 어둠=False):
    """SVG 프레임들 → PIL 그림 목록. 60프레임씩 나눠 한 장의 격자 페이지로 찍고 자른다. 어둠 = 어두운 화면(data-theme="dark")."""
    낸 = []
    n = max(1, min(한장, max(1, min(6, 쪽한도 // 칸폭)) * max(1, 쪽한도 // max(1, 높이))))     # 격자 페이지가 쪽한도 안에 들게
    for 번, k in enumerate(range(0, len(svgs), n)):
        낸 += _한판(svgs[k:k + n], 높이, 임시, 어둠, 번)
    return 낸


def _ffmpeg():
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    p = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "WinGet", "Links", "ffmpeg.exe")
    return p if os.path.isfile(p) else None


def 엮기(이, 그림들, 머묾, fps, 곳, 임시, 덧="", gif=True):
    """→ {"mp4", "gif", "png"} — 고유 프레임 그림 · 머묾(프레임 수). GIF 는 한 번 재생(loop 없음)."""
    낸 = {}
    포 = os.path.join(곳, "%s%s.png" % (이, 덧))
    그림들[-1].save(포)
    낸["png"] = 포
    차례 = [i for i, n in enumerate(머묾) for _ in range(max(1, n))]
    if gif:                                                  # 15fps — 둘에 하나(마지막 프레임은 반드시)
        뽑 = 차례[::2]
        if 뽑[-1] != 차례[-1]:
            뽑.append(차례[-1])
        묶 = []
        for i in 뽑:
            if 묶 and 묶[-1][0] == i:
                묶[-1][1] += 1
            else:
                묶.append([i, 1])
        g = os.path.join(곳, "%s%s.gif" % (이, 덧))
        자 = [그림들[i].quantize(colors=256, method=2, dither=0) for i, _n in 묶]
        자[0].save(g, save_all=True, append_images=자[1:], duration=[int(round(1000.0 * 2 * n / fps)) for _i, n in 묶], optimize=False, disposal=1)
        낸["gif"] = g
    ff = _ffmpeg()
    if not ff:
        print("ffmpeg 를 못 찾았다 — MP4 없이 GIF · 포스터만")
        return 낸
    d = os.path.join(임시, 이 + 덧)
    os.makedirs(d, exist_ok=True)
    k = 0                                                    # 프레임 차례 그대로(머묾만큼 — 같은 그림은 하드링크로 한 번만 쓴다)
    for i, (im, n) in enumerate(zip(그림들, 머묾)):
        p0 = os.path.join(d, "%05d.png" % k)
        im.save(p0)
        k += 1
        for _ in range(max(1, n) - 1):
            p = os.path.join(d, "%05d.png" % k)
            try:
                os.link(p0, p)
            except OSError:
                shutil.copyfile(p0, p)
            k += 1
    mp4 = os.path.join(곳, "%s%s.mp4" % (이, 덧))
    r = subprocess.run([ff, "-y", "-loglevel", "error", "-framerate", str(fps), "-i", os.path.join(d, "%05d.png"),
                        "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2", "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(fps),
                        "-movflags", "+faststart", "-an", mp4], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode == 0:
        낸["mp4"] = mp4
    else:
        print("ffmpeg 실패(%s) — MP4 없이" % (r.stderr or "")[-300:])
    return 낸


def 영상프레임수(mp4):
    """ffprobe 로 센 MP4 의 프레임 수(못 세면 None) — 시간표의 전체 프레임 수와 같아야 한다."""
    ff = _ffmpeg()
    if not ff:
        return None
    fp = os.path.join(os.path.dirname(ff), "ffprobe.exe" if os.name == "nt" else "ffprobe")
    fp = fp if os.path.isfile(fp) else shutil.which("ffprobe")
    if not fp:
        return None
    r = subprocess.run([fp, "-v", "error", "-select_streams", "v:0", "-count_frames", "-show_entries", "stream=nb_read_frames", "-of", "csv=p=0", mp4],
                       capture_output=True, text=True)
    try:
        return int((r.stdout or "").strip().split(",")[0])
    except ValueError:
        return None


def main():
    global 칸폭
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(allow_abbrev=False, description="레터 모션(A~D) — MP4 · GIF · 포스터")
    ap.add_argument("레터")
    ap.add_argument("--장부", default=None, help="숫자 장부(기본: 레터 이름의 .장부.json · 없으면 같은 폴더의 레터_초안.장부.json)")
    ap.add_argument("-o", "--곳", default=None, help="낼 폴더(기본: 레터 옆 「모션」 — 레터 HTML 이 이 폴더를 읽는다)")
    ap.add_argument("--fps", type=int, default=기본fps)
    ap.add_argument("--장면", default=None, help="고를 장면(쉼표) — 비우면 전부")
    ap.add_argument("--밝은것만", action="store_true", help="어두운 화면용 MP4 · 포스터를 굽지 않는다(웹은 어두운 화면에서 정적 그림)")
    ap.add_argument("--경계", default=None, help="장면마다 처음 · 단계 경계 · 끝 프레임 PNG 를 낼 폴더(검토용)")
    ap.add_argument("--배율", type=float, default=칸폭 / 560.0, help="프레임 폭 = 넓은 판 560 × 배율(기본 2 = 1,120px)")
    ap.add_argument("--경계만", action="store_true", help="영상 · 명세 없이 --경계 폴더에 처음 · 단계 경계 · 끝 프레임 PNG(밝은 화면)만 — 정지 그림 · 프레임 내보내기")
    a = ap.parse_args()
    칸폭 = int(round(560 * a.배율))
    문 = 이징검사()
    if 문:
        raise SystemExit("이징 검사 실패 — %s" % "; ".join(문))
    글 = io.open(a.레터, encoding="utf-8").read()
    d = os.path.dirname(os.path.abspath(a.레터))
    후 = [a.장부] if a.장부 else [os.path.splitext(a.레터)[0] + ".장부.json", os.path.join(d, "레터_초안.장부.json")]
    장부 = next((json.load(io.open(p, encoding="utf-8")) for p in 후 if p and os.path.isfile(p)), None)
    if not 장부:
        raise SystemExit("숫자 장부를 못 찾았다 — --장부 로 준다")
    곳 = os.path.abspath(a.곳 or os.path.join(d, 레터HTML.모션폴더))
    spec = 명세(글, 장부, a.fps)
    고른 = [x for x in spec["장면"] if not a.장면 or x in [y.strip() for y in a.장면.split(",")]]
    if a.경계만:                                             # 2026-10-27 — 정지 그림 · 프레임 내보내기: 경계 프레임만 높은 배율로(영상 프레임 전부를 굽지 않는다)
        if not a.경계:
            raise SystemExit("--경계만 은 --경계 <폴더> 와 함께 준다")
        os.makedirs(a.경계, exist_ok=True)
        임시 = tempfile.mkdtemp(prefix="레터모션경계_")
        실패 = []
        try:
            for 이 in 고른:
                x = spec["장면"][이]
                검 = 검사(spec, 이)
                if 검["문제"]:
                    실패.append("%s — %s" % (이, "; ".join(검["문제"])))
                ks = [k for k, _p, _s in 검["경계"]]
                svgs = [프레임그림(spec, 이, 상태(x["_표"], k)) for k in ks]
                vb = re.search(r'viewBox="0 0 (\d+(?:\.\d+)?) (\d+(?:\.\d+)?)"', svgs[-1])
                높이 = int(칸폭 * float(vb.group(2)) / float(vb.group(1))) if vb else 칸폭
                자 = os.path.join(임시, 이)
                os.makedirs(자, exist_ok=True)
                ims = 찍기(svgs, 높이, 자)
                for k, im in zip(ks, ims):
                    im.save(os.path.join(a.경계, "%s_%03d_%05.2f초.png" % (이, k, k / float(a.fps))))
                # 2026-10-27 — 끝 프레임 = 정지 그림을 픽셀로도 본다(SVG 글이 같아도 찍는 쪽에서 어긋날 수 있다 — id 겹침으로 B 경로가 사라진 결함)
                os.makedirs(os.path.join(자, "정지"), exist_ok=True)
                정 = 찍기([정적그림(spec, 이)], 높이, os.path.join(자, "정지"))[0]
                같, 몫 = 픽셀같음(ims[-1], 정)
                if not 같:
                    실패.append("%s — 끝 프레임이 정지 그림과 픽셀로 다르다(다른 픽셀 %.2f%%)" % (이, 100 * 몫))
                print("%s — %s · 경계 프레임 %d장 · %d×%dpx · 마지막 = 짝 %s" % (이, x["제목"], len(ks), 칸폭, 높이, "예" if 검["짝같음"] else "아니오"))
        finally:
            shutil.rmtree(임시, ignore_errors=True)
        if 실패:
            raise SystemExit("모션 검사 실패\n  " + "\n  ".join(실패))
        return
    os.makedirs(곳, exist_ok=True)
    임시 = tempfile.mkdtemp(prefix="레터모션프레임_")
    실패 = []
    t0 = time.time()
    일 = []                                                  # (장면, 어둠, svgs, 높이, 머묾)
    준 = {}
    for 이 in 고른:
        x = spec["장면"][이]
        검 = 검사(spec, 이)
        x["검사"] = {k: v for k, v in 검.items() if k != "경계"}
        x["검사"]["경계"] = [{"프레임": k, "초": round(k / float(a.fps), 3), "순수": p, "같음": s} for k, p, s in 검["경계"]]
        if 검["문제"]:
            실패.append("%s — %s" % (이, "; ".join(검["문제"])))
        프 = 프레임들(x["_표"], x["_전체"])
        svgs = [프레임그림(spec, 이, st) for st, _n in 프]
        vb = re.search(r'viewBox="0 0 (\d+(?:\.\d+)?) (\d+(?:\.\d+)?)"', svgs[-1])
        높이 = int(칸폭 * float(vb.group(2)) / float(vb.group(1))) if vb else 칸폭
        준[이] = (검, 프)
        x["파일"] = {}
        for 어둠 in ((False, True) if not a.밝은것만 else (False,)):
            일.append((이, 어둠, svgs, 높이, [n for _st, n in 프]))

    def 한일(w):                                             # 장면 · 테마 하나 — 제 임시 폴더 · 제 브라우저 프로필(서로 섞이지 않는다)
        이, 어둠, svgs, 높이, 머묾 = w
        자 = os.path.join(임시, "%s%s" % (이, "_dark" if 어둠 else ""))
        os.makedirs(자, exist_ok=True)
        그림 = 찍기(svgs, 높이, 자, 어둠)
        낸 = 엮기(이, 그림, 머묾, a.fps, 곳, 자, ".dark" if 어둠 else "", gif=not 어둠)
        return 이, 어둠, 그림, 낸
    from concurrent.futures import ThreadPoolExecutor
    try:
        with ThreadPoolExecutor(max_workers=3) as 풀:
            결과 = list(풀.map(한일, 일))
        for 이, 어둠, 그림, 낸 in 결과:
            x = spec["장면"][이]
            검, 프 = 준[이]
            if 낸.get("mp4"):
                nf = 영상프레임수(낸["mp4"])
                x["검사"]["영상프레임" + (".dark" if 어둠 else "")] = nf
                if nf is not None and nf != x["_전체"]:
                    실패.append("%s — %s 의 프레임 %d ≠ 시간표 %d" % (이, os.path.basename(낸["mp4"]), nf, x["_전체"]))
            x["파일"].update({(k + "_dark") if 어둠 else k: os.path.basename(v) for k, v in 낸.items()})
            if a.경계 and not 어둠:                            # 처음 · 경계 · 끝 프레임(검토용)
                os.makedirs(a.경계, exist_ok=True)
                시작프, s0 = [], 0
                for _st, n in 프:
                    시작프.append(s0)
                    s0 += n
                for k, _p, _s in 검["경계"]:
                    j = max(i for i, s in enumerate(시작프) if s <= k)
                    그림[j].save(os.path.join(a.경계, "%s_%03d_%05.2f초.png" % (이, k, k / float(a.fps))))
        for 이 in 고른:
            x = spec["장면"][이]
            검, _프 = 준[이]
            x["짝같음"] = 검["짝같음"]
            print("%s — %s · %.2f초 · 고유 프레임 %d · 마지막 = 짝 %s · 경계 %d곳(순수 %d · 같음 %d) · 샌 숫자 %d · 경계 읽힘 %d · %s" % (
                이, x["제목"], x["초"], 검["고유"], "예" if 검["짝같음"] else "아니오", len(검["경계"]),
                sum(1 for _k, p, _s in 검["경계"] if p), sum(1 for _k, _p, s in 검["경계"] if s), len(검["샌숫자"]), 검.get("읽힘", 0),
                " · ".join(sorted(x["파일"].values()))))
        print("찍기 · 엮기 %.0f초(장면 · 테마 %d개를 셋씩 함께)" % (time.time() - t0, len(일)))
    finally:
        shutil.rmtree(임시, ignore_errors=True)
    for x in spec["장면"].values():
        x.pop("_표", None)
        x.pop("_전체", None)
    spec["블"] = {k: {"제목": v[0], "표": v[1]} for k, v in spec["블"].items()}
    io.open(os.path.join(곳, "motion_spec.json"), "w", encoding="utf-8").write(json.dumps(spec, ensure_ascii=False, indent=1))
    print("모션 — %s (motion_spec.json)" % 곳)
    if 실패:
        raise SystemExit("모션 검사 실패\n  " + "\n  ".join(실패))


if __name__ == "__main__":
    main()

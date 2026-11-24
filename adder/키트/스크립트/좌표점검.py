# -*- coding: utf-8 -*-
"""좌표점검 — 코드는 판올림을 따라왔는데 **글이 뒤처진 자리**를 잡는다.

## 왜 있는가
판올림(v10→v11→v12) 때 `행이전_vN.py` 은 JSON 의 행 키를 옮기는데, **문구와 문서는
아무도 안 옮겼다.** 실측(2026-08-28, v12 정비): 코드끼리는 전부 맞았는데 사람이 읽는
자리 **63곳**이 옛 판이었다 — 가정_스키마.md 가 시점가정을 옛 범위로 안내했고,
엔진 화면 문구가 「189행에 직접 적으십시오」라 말했다(코드는 213 을 읽는다).
시키는 대로 하면 값이 **엔진이 안 읽는 칸**에 들어가는, 조용히 틀리는 종류다.

## 옛 좌표를 손으로 적지 않는다 — 행이전에서 계산한다
첫 판은 옛 좌표 짝을 이 파일에 손으로 적었다. 그러면 v13 때 또 사람이 짝을 추가해야
하고, **빼먹으면 도구가 눈을 잃는다.** 그래서 지금 판은 이렇게 돈다.

    이름표      「의미 ↔ v12 좌표」만 적는다. 좌표의 **뜻**은 판이 바뀌어도 안 변한다
    행이전_v*  `_시트지도` 를 전부 읽어 온다 (파일 이름에서 판 번호를 스스로 찾는다)
    옛 좌표    이동 함수를 **역산**해서 얻는다 — 손으로 적은 사전이 없다
    현행 좌표  v12 보다 새 판의 지도가 있으면 그만큼 밀어서 얻는다

**그래서 v13 때 사람이 할 일은 `행이전_v13.py` 하나다** (`_시트지도` 를 노출할 것 —
v11·v12 와 같은 규약). 그것만 있으면 이 도구는 새로 밀린 좌표를 스스로 안다.
어느 한쪽만 하면 `--자기확증` 이 운다:
    행이전_v13 만 만들고 코드를 안 옮김  → 계산된 현행 좌표와 코드가 어긋난다 — 운다
    코드만 옮기고 행이전_v13 을 안 만듦  → 계산된 현행 좌표가 v12 에 머문다 — 운다

## 무엇을 잡는가 — 옛 좌표 숫자와 의미어의 짝
숫자만 찾으면 안 된다. 옛 번호와 새 번호는 겹친다(252 는 v11 정상마진이었다가 v12 에서
T2 매출 기여로 **재사용**됐다). 그래서 ① 줄의 숫자가 이름표 항목의 **옛 좌표**이고
② 그 항목의 의미어가 같은 줄에 있을 때만 잡는다. ③ 그 숫자가 다른 항목의 **현행**
좌표이기도 하고 그쪽 의미어가 줄에 있으면 정당한 현행 서술로 보고 넘어간다.
줄에 「옛」「이전:」「v10」「v11」「→」이 있으면 역사 서술로 보고 건너뛴다.

    python 스크립트/좌표점검.py            # 본체 전체 점검 (0건이어야 한다)
    python 스크립트/좌표점검.py --자기확증   # 계산된 현행 좌표가 코드와 같은지
    python 스크립트/좌표점검.py --지도       # 스크립트가 부르는 번호가 지금 좌표 지도에 다 있는지

## 2026-10-01 — 번호는 좌표가 아니라 ID 다
워크북의 자리는 이제 생성기가 낸 **좌표 지도**(`DCF_워크북_좌표지도.json`)가 정하고, 스크립트는 `좌표.py` 로
번호를 지금 자리로 바꾼다. 그래서 이 파일의 「v12 좌표」는 **가정 번호(ID)** 로 읽는다 — 배치를 옮겨도 번호는
안 바뀌고, 배치를 옮겼다고 `행이전_vN.py` 를 새로 만들 일도 없다. 이 도구에 남은 일은 셋이다.
    ① 글에 남은 **v12 이전의 옛 번호**를 잡는다 (위의 원래 일 — 이름표는 그 번호 31개의 뜻이다)
    ② 가정_템플릿 ↔ 엔진 가정머리행 · 레터.행이름 ↔ 스캐폴드 줄 이름 (번호가 같은 뜻을 가리키는가)
    ③ `--지도` — 붓기·대조·엔진이 부르는 번호가 지금 배치에 있는가 (배치에서 줄을 빼면 여기서 운다) ·
       스캐폴드와 좌표 지도가 지문으로 짝인가 · **지문을 남긴 뒤에 고친 스캐폴드가 아닌가**(값 있는 칸의 자리 · 줄 이름) ·
       지도가 가정묶음·단위 종류·이름 칸·기간 열·줄 이름 지문을 실었는가 · 기간 열(열 ID · 구분 · 순서)이 지도의 축과 같은가 ·
       이름 칸의 틀이 스캐폴드의 줄 이름과 맞는가 · 종류를 모르는 단위 낱말이 가정 머리 줄에 있는가 ·
       스크립트가 좌표 지도를 안 거치고 워크북을 만지지 않는가 (시트 이름 글자 · 시트 이름 머리 글자 · 시트를 순서로 잡기 ·
       칸 주소 글자 · 셈한 칸 주소 · 좌표.py 없이 load_workbook) · 지침 파일의 덤프 명령이 시트 이름 글자가 아닌가
       ④ 의 헛울음은 그 줄에 `# 지도밖: 까닭` 을 적어 푼다(이 지도의 워크북이 아닌 파일을 만지는 줄)
이 파일이 워크북을 읽는 자리(②의 줄 이름, 스캐폴드 글 훑기)는 `좌표.py` 를 거친다.

## 2026-10-07 (W7c) — 스키마 v13 · 납품 배치
엔진의 가정 머리 행 · 시점가정행은 옛꼴다리가 아니라 엔진의 얼굴(`dcf엔진` — 스키마의 표)에서 읽는다. `연장` 블록의 키는 없어졌다.
`--지도` 는 납품 배치도 본다 — 엔진의 시트인데 시간축이 아닌 1번 요약 · 3번 · 11번의 대조 칸(값1~값3 · 예측값 · 영구값)과
붓기가 엔진 값을 적는 1번(시나리오별 결과 · 역산 DCF 분석) · 14번(민감도 표 다섯) 칸(`납품산출칸`)이 이 배치에 있는가.
이름표에서 걷은 항목(221 영구 매출 기준)을 뺐고, v12 이후 세액공제율 자리인 200 을 재사용 가드로 더했다(옛 200 은 최저한세 — 지금 208).
"""
from __future__ import annotations

import argparse
import glob
import importlib
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "스크립트"))
import 좌표  # noqa: E402

역사패턴 = re.compile(r"옛|이전:|v10|v11|→")
기준판 = 12                     # 이름표의 좌표가 이 판 기준이다

# ── 이름표 — 「의미 ↔ v12 좌표」. 좌표의 뜻은 판이 바뀌어도 안 변한다 ─────────
# 이름의 낱말들이 곧 의미어다 — 그 낱말이 같은 줄에 있어야 잡는다.
이름표 = [
    ("12", 124, "연구개발"),
    ("12", 148, "자본적지출 CapEx 유지 전략"),
    ("12", 200, "세액공제율 세액공제 공제"),      # 재사용 가드 — v12 이후 200 은 세액공제율(옛 200 은 최저한세 · 지금 208)
    ("12", 208, "최저한세 스위치 유효값"),
    ("12", 209, "결손금"),
    ("12", 212, "영구성장률"),
    ("12", 213, "정규화 종착 마진 영업이익률"),
    ("12", 219, "ROIC 초과수익"),
    ("12", 220, "비지배"),
    ("12", 244, "연장여부"),
    ("12", 245, "트리거"),
    ("12", 246, "근거자료"),
    ("12", 248, "WACC로드맵"),
    ("12", 252, "T2 매출 기여 회수 램프업"),
    ("12", 256, "전략 투자 CAPEX CapEx 증설CapEx"),
    ("12", 260, "정상마진 신제품"),
    ("12", 264, "완공 리드타임"),
    ("12", 46,  "제품군3 물량"),
    ("12", 62,  "제품군5 물량"),
    ("12", 70,  "기타 성장률"),
    ("4",  53,  "증설 신제품 매출"),
    ("4",  54,  "합계 기저"),
    ("13", 90,  "제품군5 매출"),
    ("13", 92,  "부문 합계 매출액"),
    ("13", 95,  "발행주식총수 발행총수"),
    ("13", 96,  "자기주식"),
    ("13", 97,  "유통주식수"),
    ("13", 98,  "우선주"),
    ("13", 99,  "종가"),
    ("13", 100, "시가총액"),
]
# 범위 표기(「204~212」)는 블록으로 잡는다 — (시트, 의미어, v12 시작, v12 끝)
범위표 = [
    ("12", "시점 K블록", 212, 220),
    ("12", "L절", 243, 259),
]

# ── 행이전 지도를 전부 읽는다 — 파일 이름에서 판 번호를 스스로 찾는다 ────────
def _지도들():
    낸것 = []
    for p in glob.glob(os.path.join(ROOT, "스크립트", "행이전_v*.py")):
        m = re.search(r"행이전_v(\d+)\.py$", p)
        if not m:
            continue
        판 = int(m.group(1))
        mod = importlib.import_module("행이전_v%d" % 판)
        지도 = getattr(mod, "_시트지도", None)
        if 지도 is None:
            sys.stderr.write("⚠ 행이전_v%d 에 _시트지도 가 없다 — v11·v12 규약대로 "
                             "노출해야 이 도구가 그 판의 이동을 안다\n" % 판)
            continue
        낸것.append((판, 지도))
    return sorted(낸것)


def _민다(지도목록, 시트, x):
    for _, 지도 in 지도목록:
        fn = 지도.get(시트)
        if fn:
            x = fn(x)
    return x


def 좌표계산():
    """이름표(v12 기준)에서 (현행 좌표, 옛 좌표 집합)을 **계산**한다."""
    전부 = _지도들()
    이후 = [(판, z) for 판, z in 전부 if 판 > 기준판]      # v13, v14, …
    항목들 = []
    for 시트, v12값, 이름 in 이름표:
        현행 = _민다(이후, 시트, v12값)
        옛 = set()
        # 어느 판의 좌표가 적혀 있는지 모르므로 모든 시작판에서 역산해 합친다
        for i in range(len(전부)):
            꼬리 = 전부[i:]
            for x in range(1, 601):
                if _민다(꼬리, 시트, x) == 현행 and x != 현행:
                    옛.add(x)
        토큰 = [t for t in 이름.split() if len(t) >= 2]
        항목들.append({"시트": 시트, "현행": 현행, "옛": 옛, "이름": 이름, "토큰": 토큰})
    범위들 = []
    for 시트, 의미, 첫, 끝 in 범위표:
        옛범위 = set()
        for i in range(len(전부)):
            꼬리 = 전부[i:]
            a = [x for x in range(1, 601) if _민다(꼬리, 시트, x) == _민다(이후, 시트, 첫)]
            b = [x for x in range(1, 601) if _민다(꼬리, 시트, x) == _민다(이후, 시트, 끝)]
            for xa in a:
                for xb in b:
                    if (xa, xb) != (_민다(이후, 시트, 첫), _민다(이후, 시트, 끝)):
                        옛범위.add("%d~%d" % (xa, xb))
        범위들.append({"시트": 시트, "의미": [t for t in 의미.split() if len(t) >= 2],
                      "옛범위": 옛범위,
                      "현행": "%d~%d" % (_민다(이후, 시트, 첫), _민다(이후, 시트, 끝))})
    return 항목들, 범위들


# ── 점검 대상 ─────────────────────────────────────────────────────────────
# `_스캐폴드_*.py` 는 스캐폴드 패치 스크립트 — 「옛 글 → 새 글」 짝을 적는 것이 본업이라 옛 번호가 정당하다
제외파일 = re.compile(r"좌표점검\.py$|행이전_v\d+\.py$|_스캐폴드_[^\/]*\.py$")
이력머리 = "## v10 → v11 좌표 변경 지도"        # 스캐폴드_구조.md 개정 이력 절 — 신설 당시 번호가 정당


def _대상파일():
    for 뿌리, 폴더들, 파일들 in os.walk(ROOT):
        # 백업 폴더는 **옛 판을 일부러 얼려 둔 자리**다 — 거기서 울면 소음이다
        # (실측 L5 수리 2026-09-13: 수리 전 사본 두 벌을 `_스캐폴드_백업` 에 뜨자 21건이 울었다)
        # `보관` 은 버린 도구(옛 좌표를 글로 박은 스크립트)를 얼려 둔 자리다 — 같은 까닭으로 뺀다
        폴더들[:] = [d for d in 폴더들 if d not in ("__pycache__", "_raw", "_dartcache", "회귀기준선",
                                                  "_스캐폴드_백업", "보관")]
        for f in 파일들:
            if f.endswith((".md", ".py")) and not 제외파일.search(f):
                yield os.path.join(뿌리, f)


행표기 = re.compile(r"(\d{2,3})\s*행")
# ⚠ 알려진 사각: 한글 조사가 붙으면(「D185가」) `\b` 가 경계를 못 봐 안 걸린다(L5 2026-09-13 실측 —
# 스캐폴드 10!B29). 넓힌 정규식 `(?<![A-Za-z0-9$])D(\d{2,3})(?![0-9])` 는 자체검사.py:358 docstring
# 「D200을」 을 새로 잡아 좌표점검이 rc=1 이 되므로, 그 줄이 고쳐진 뒤에 바꾼다(L5 보고 ③)
셀표기 = re.compile(r"\bD(\d{2,3})\b")
키표기 = re.compile(r'"(\d{3})"')
# **백틱 표기를 놓쳤다** — 문서는 행을 「`94`(발행총수)」처럼 적는 자리가 많은데
# 「94행」도 아니고 큰따옴표 키도 아니라 셋 다 안 잡혔다. 실측(씨젠 회차):
# 가정_스키마.md 가 주식수 행을 v11 번호(94·95·96·98·99)로 안내하고 있었고
# 좌표점검은 0건이라 말했다. **눈이 없던 표기법이 있었던 것이다.**
백틱표기 = re.compile(r"`(\d{2,3})`")


def _토큰있음(토큰들, 줄):
    return any(t in 줄 for t in 토큰들)


def _줄검사(줄, 항목들, 범위들, 현행별, 파이썬=False):
    """한 줄에서 옛 좌표를 찾는다. 돌려주는 것: [(이름, 현행), …]."""
    걸림 = []
    if 역사패턴.search(줄):
        return 걸림
    # ① 범위 표기 (「204~212」)
    for 범 in 범위들:
        for 옛 in 범["옛범위"]:
            if 옛 in 줄 and _토큰있음(범["의미"], 줄):
                걸림.append(("범위 " + 옛, 범["현행"]))
    # ② 숫자 표기 — 줄에서 후보를 모은다
    후보 = set()
    for m in 행표기.finditer(줄):
        n = int(m.group(1))
        시트들 = ["12"]                     # 시트 무표기는 12번으로 본다
        if "4번" in 줄:
            시트들.append("4")
        if "13번" in 줄:
            시트들.append("13")
        for s in 시트들:
            후보.add((s, n))
    for m in 셀표기.finditer(줄):
        후보.add(("12", int(m.group(1))))
    키검사줄 = 줄
    if 파이썬:
        # 코드 줄의 "252" 같은 리터럴은 현행 코드다 — 주석(#) 뒤만 본다
        키검사줄 = 줄.split("#", 1)[1] if "#" in 줄 else ""
    for m in 키표기.finditer(키검사줄):
        후보.add(("12", int(m.group(1))))
    for m in 백틱표기.finditer(줄):
        n = int(m.group(1))
        for s in ("12", "13", "4"):
            후보.add((s, n))
    for 시트, n in 후보:
        for 항 in 항목들:
            if 항["시트"] != 시트 or n not in 항["옛"]:
                continue
            if not _토큰있음(항["토큰"], 줄):
                continue
            # 재사용 가드 — n 이 **어느 시트에서든** 현행 좌표이고 그쪽 의미어가
            # 줄에 있으면 정당하다. 백틱 숫자는 시트를 못 가려 12·13·4 로 다
            # 시험하는데, 같은 시트만 보면 「12번 46(제품군3 물량)」이
            # 「4번 옛 46(증설)」로 오인된다 — 실측: 스키마 행 목록 개정에서 헛울음
            if any(자 is not None and _토큰있음(자["토큰"], 줄)
                   for 자 in (현행별.get((s2, n)) for s2 in ("12", "13", "4"))):
                continue
            걸림.append(("%s번 %d (%s)" % (시트, n, 항["이름"].split()[0]),
                        "%s번 %d" % (시트, 항["현행"])))
    return 걸림


def 점검(항목들, 범위들):
    걸린것 = []
    현행별 = {}                                   # (시트, 좌표) → 항목 (재사용 가드용)
    for 항 in 항목들:
        현행별[(항["시트"], 항["현행"])] = 항

    for p in _대상파일():
        try:
            글 = io.open(p, encoding="utf-8").read()
        except Exception:                          # noqa: BLE001
            continue
        if os.path.basename(p) == "스캐폴드_구조.md" and 이력머리 in 글:
            글 = 글.split(이력머리)[0]
        for 번호, 줄 in enumerate(글.split("\n"), 1):
            for 이름, 현행 in _줄검사(줄, 항목들, 범위들, 현행별, p.endswith(".py")):
                걸린것.append((os.path.relpath(p, ROOT), 번호, 이름, 현행, 줄.strip()[:70]))
    걸린것.extend(스캐폴드라벨점검(항목들, 범위들, 현행별))
    return 걸린것


# ── 스캐폴드 라벨 층 — 워크북 안의 글도 사람이 읽는 자리다 ─────────────────
# **.md·.py 만 보던 눈이 워크북 안의 글을 못 봤다.** 실측(펄어비스 2026-09-13 검증 V2):
# 2번 시트 라벨·판정 문구가 「12번 D196」(현행 D221)·「189행·236행」(현행 213·260)·
# 「12번 D221」(현행 D245)·「232·228행」(현행 256·252)으로 **옛 판 번호를 안내**하고 있었고
# 좌표점검은 0건이라 말했다. 검증행 문구는 「어디를 고치라」고 시키는 글이라 틀리면
# 사람이 엔진이 안 읽는 칸을 고친다. 그래서 B열 라벨과 **판정 수식 속 따옴표 글**을
# 한 칸 = 한 줄로 보고 같은 규칙(옛 좌표 숫자 + 의미어)으로 훑는다.
_따옴표글 = re.compile(r'"((?:[^"]|"")*)"')


def _스캐폴드글줄들(경로):
    try:
        import openpyxl                                   # noqa: PLC0415
        wb = openpyxl.load_workbook(경로)
    except Exception as e:                                # noqa: BLE001
        sys.stderr.write("⚠ 스캐폴드 라벨 층을 못 읽었다 — %s\n" % e)
        return
    for ws in wb.worksheets:
        for 행 in ws.iter_rows():
            for 칸 in 행:
                v = 칸.value
                if not isinstance(v, str) or not v.strip():
                    continue
                if v.startswith("="):
                    글 = " ".join(m.group(1) for m in _따옴표글.finditer(v))
                else:
                    글 = v
                if 글.strip():
                    yield "%s!%s" % (ws.title, 칸.coordinate), 글


def 스캐폴드라벨점검(항목들, 범위들, 현행별):
    경로 = 좌표.스캐폴드경로(ROOT)
    if not os.path.exists(경로):
        return []
    걸림 = []
    for 자리, 줄 in _스캐폴드글줄들(경로):
        for 이름, 현행 in _줄검사(줄, 항목들, 범위들, 현행별):
            걸림.append(("%s[%s]" % (좌표.스캐폴드이름, 자리), 0, 이름, 현행, 줄.strip()[:70]))
    return 걸림


def 자기확증(항목들):
    """계산된 현행 좌표가 **코드**와 같은지 — 행이전과 코드 중 한쪽만 옮기면 여기서 운다."""
    좌 = {(항["시트"], 항["이름"].split()[0]): 항["현행"] for 항 in 항목들}
    좋다 = True

    def 어긋남(글):
        nonlocal 좋다
        print("  ✗ " + 글)
        좋다 = False

    # ① 엔진 — 시점가정행 아홉 칸(스키마의 표 — 얼굴 `dcf엔진` 이 내놓는다)
    import dcf엔진 as E                             # noqa: PLC0415
    g, 끝 = 좌[("12", "영구성장률")], 좌[("12", "비지배")]
    if tuple(E.시점가정행) != tuple(str(r) for r in range(g, 끝 + 1)):
        어긋남("엔진 시점가정행 %s ≠ 계산된 현행 %d~%d — 행이전과 코드가 어긋났다"
             % (E.시점가정행, g, 끝))
    # ② 붓기 — 스위치·연장 셀 짝
    붓기 = io.open(os.path.join(ROOT, "스크립트", "붓기.py"), encoding="utf-8").read()
    for 의미 in ("최저한세한도율", "결손금처리", "연장여부"):       # 붓기가 쓰는 스위치 · 연장 칸(W6b: 12번 D124 연구개발 경로 칸은 걷었다)
        키 = 의미 if ("12", 의미) in 좌 else 의미[:3]
        칸 = {"최저한세한도율": "최저한세",
             "결손금처리": "결손금", "연구개발경로": "연구개발", "연장여부": "연장여부"}[의미]
        행 = next(항["현행"] for 항 in 항목들 if 항["시트"] == "12" and 칸 in 항["이름"])
        if '("D%d", "%s")' % (행, 의미) not in 붓기:
            어긋남('붓기에 ("D%d", "%s") 짝이 없다 — 행이전과 코드가 어긋났다' % (행, 의미))
    # ③ (걷음 — W7c) 엔진의 전개 함수가 굳히던 줄의 번호가 엔진 코드에 있는지 보던 문단. 그 함수가 엔진에 없다(설계서 6-2)
    # ④ 자체검사 — 시점행이름 사전의 키
    import 자체검사 as C                            # noqa: PLC0415
    if set(C.시점행이름.keys()) != {str(r) for r in range(g, 끝 + 1)}:
        어긋남("자체검사 시점행이름 키가 계산된 현행 %d~%d 과 다르다" % (g, 끝))

    print("  자기확증 %s — 행이전으로 계산한 현행 좌표가 코드와 %s"
          % ("통과" if 좋다 else "실패", "같다" if 좋다 else "다르다"))
    return 좋다


# ── 가정_템플릿 ↔ 엔진 가정머리행 대조 ──────────────────────────────
# **머리 행이 템플릿에 「없는」 것과 「비어 있는」 것은 다르다.** 실측(현대차 2026-09-11):
# 제품군 3·4·5 의 물량·단가(46·50·54·58·62·66)가 엔진 `가정머리행` 에는 있는데
# 템플릿에만 없었다. 그러면 세 가지가 조용히 어긋난다.
#   ① 붓기가 「빠짐」으로 울고 스캐폴드 안내문이 그 행 근거 칸에 그대로 남는다
#   ② 자체검사 ㉚(가정 전달)이 **없는 행을 만들며 한 시나리오만 채워** 스키마 오류로 죽고,
#      검사가 「재료 없음」으로 비켜 간다 — 감시가 통째로 사라지는데 아무도 안 운다
#   ③ 다음 회차가 템플릿을 보고 「이 회사는 스트림이 둘뿐이구나」로 읽는다
# **안 쓰는 행도 세 시나리오 빈 벌로 있어야 한다**(「0과 빈칸을 가른다」의 스키마 판).
# v13(W8a) — 템플릿은 구조 묶음 셋(기본형 · 물량·단가형 · 설비 동인형)이고 구조가 줄을 정한다. 그래서 「늘 서는」 머리 행만 요구한다:
# 매출 구분 3~5 의 증가율 줄(46~66)은 선언하지 않으면 붓기가 비운 채 두고, 인건비 줄(126~142)은 구조.인건비 가 정한다 —
# 구조가 짓지 않는 인건비 줄에 키가 있으면 붓기가 「남음」으로 멈추므로 그 키는 **없어야** 한다. 조건은 줄 명세 S12_인건비.jsonl 의 조건과 같다
템플릿파일 = ("가정_템플릿_기본형.json", "가정_템플릿_물량단가형.json", "가정_템플릿_설비동인형.json")
_선언따라서는줄 = {"46", "50", "54", "58", "62", "66"}
_인건비줄 = ("126", "130", "134", "138", "142")


def _서는인건비줄(구):
    """구조.인건비 → 짓는 인건비 머리 줄(줄 명세 S12_인건비.jsonl 의 조건)."""
    인 = (구 or {}).get("인건비") or {}
    방식, 경로 = 인.get("산정방식", "인원"), 인.get("인원경로", "증가율")
    낸 = set()
    if (방식 != "매출액비율" and 경로 == "수준") or (방식 == "인원" and 경로 == "증가율"):
        낸.add("126")
    if 방식 != "매출액비율" and 경로 == "수준":
        낸.add("130")
    if 방식 != "미분리" or 경로 == "수준":
        낸 |= {"134", "138", "142"}
    return 낸


def 템플릿대조():
    """가정 템플릿 셋(`가정_템플릿_*.json`)이 그 구조가 짓는 엔진 `가정머리행` 을 빠짐없이 갖고 있는지 본다."""
    걸림 = []
    try:
        엔 = importlib.import_module("dcf엔진")             # 스키마의 가정 머리 행(늘 서는 옛 번호의 줄 — 엔진의 얼굴이 내놓는다)
        머리 = [str(r) for r in getattr(엔, "가정머리행", ())]
    except Exception as e:                                   # pragma: no cover
        return ["  가정머리행을 못 읽었습니다(%s) — 대조를 건너뜁니다" % type(e).__name__]
    if not 머리:
        return []
    for 파일 in 템플릿파일:
        경로 = os.path.join(ROOT, 파일)
        if not os.path.exists(경로):
            걸림.append("  %s 가 없습니다 — 구조 묶음의 템플릿은 셋이다(%s)" % (파일, " · ".join(템플릿파일)))
            continue
        try:
            t = json.load(io.open(경로, encoding="utf-8"))
        except Exception as e:                               # pragma: no cover
            걸림.append("  %s 을 못 읽었습니다(%s)" % (파일, type(e).__name__))
            continue
        서는 = _서는인건비줄(t.get("구조"))
        필수 = [r for r in 머리 if r not in _선언따라서는줄 and (r not in _인건비줄 or r in 서는)]
        for 칸 in ("가정", "근거"):
            있 = set((t.get(칸) or {}).keys())
            빠진 = [r for r in 필수 if r not in 있]
            if 빠진:
                걸림.append("  %s 의 `%s` 에 머리 행 %d개가 **없습니다** — %s" % (파일, 칸, len(빠진), " · ".join(빠진)))
        남는 = [r for r in _인건비줄 if r not in 서는 and r in (t.get("가정") or {})]
        if 남는:
            걸림.append("  %s 의 `가정` 에 구조가 짓지 않는 인건비 줄의 키가 있습니다 — %s (붓기가 「남음」으로 멈춘다)" % (파일, " · ".join(남는)))
        # 있기는 한데 세 시나리오를 다 안 갖춘 행도 같은 사고를 낸다(시나리오 공통 줄은 「공통」 한 벌)
        모자란 = []
        for r in 필수:
            벌 = (t.get("가정") or {}).get(r)
            if isinstance(벌, dict) and "공통" not in 벌 and any(s not in 벌 for s in ("비관", "기준", "낙관")):
                모자란.append(r)
        if 모자란:
            걸림.append("  %s 의 `가정` 에 세 시나리오를 다 안 갖춘 행 — %s" % (파일, " · ".join(모자란)))
    return 걸림


# ── 행이름 ↔ 스캐폴드 라벨 대조 ─────────────────────────────────────
# **좌표가 맞아도 이름이 반대면 사람이 거꾸로 채운다.** 실측(SK하이닉스, 2026-09-10):
# 스캐폴드 12번은 138=연구개발·142=판매관리인데 레터.행이름 사전이 반대로 적혀 있었고,
# 저자가 그 사전을 믿고 JSON 을 거꾸로 채웠다 — 영업이익은 안 틀려서(둘 다 판관비 합계)
# 대조 0곳으로 통과했고, 레터의 항목 라벨만 조용히 틀렸다. 좌표점검이 이제 이 층을 본다.
_의미어군 = [("제조", ("제조",)), ("연구개발", ("연구개발", "R&D")), ("판관", ("판관", "판매관리", "판매비")),
          ("유형", ("유형",)), ("무형", ("무형",))]


def 행이름대조():
    """레터.행이름 의 각 항목이 스캐폴드 12번 같은 행 라벨과 **의미어가 충돌하지 않는지** 본다."""
    try:
        레 = importlib.import_module("레터")
        import openpyxl
    except Exception as e:
        return ["행이름대조를 못 돌았다 — %s" % e]
    경로 = 좌표.스캐폴드경로(ROOT)
    if not os.path.exists(경로):
        return ["행이름대조를 못 돌았다 — 스캐폴드가 없다: %s" % 경로]
    try:
        지 = 좌표.지도찾기(경로)
        wb = openpyxl.load_workbook(경로)
        지.확인(wb)
        장 = 지.장(wb, "12")
    except 좌표.좌표오류 as e:
        return ["행이름대조를 못 돌았다 — 좌표 오류: %s" % e]
    라벨들 = {}                                  # 가정 번호 → 줄 이름 (자리는 좌표 지도가 찾는다)
    for 번, _n in 장.줄들():
        v = 장.값("B", 번)
        if v:
            라벨들[str(번)] = "%s" % v
    걸림 = []
    for 행, 이름 in (getattr(레, "행이름", {}) or {}).items():
        라벨 = 라벨들.get(str(행))
        if not 라벨:
            continue
        for _군, 말들 in _의미어군:
            이쪽 = any(m in 이름 for m in 말들)
            저쪽 = any(m in 라벨 for m in 말들)
            if 이쪽 != 저쪽:
                # 한쪽에만 의미어가 있으면, 반대 군의 의미어가 다른 쪽에 있는지 본다 — 그때만 충돌
                for _군2, 말들2 in _의미어군:
                    if _군2 == _군:
                        continue
                    if (이쪽 and any(m in 라벨 for m in 말들2) and not any(m in 이름 for m in 말들2)) or                        (저쪽 and any(m in 이름 for m in 말들2) and not any(m in 라벨 for m in 말들2)):
                        걸림.append("  %s행 — 행이름 「%s」 vs 스캐폴드 「%s」: 의미어 「%s」/「%s」 가 갈린다"
                                   % (행, 이름, 라벨.strip()[:40], _군, _군2))
                        break
                break
    return 걸림


# ── 규칙 문서의 배분 번호 ↔ 스캐폴드 라벨 (S4-07 · 2026-10-17) ──────────────────────────
# 행이름 사전만 보면 규칙 문서(CLAUDE.md 매출원가·판관비 규칙 「134 제조 + 138 판관 + 142 개발」)에 남은 같은 뒤바뀜은 못 잡는다 — 에이전트는 규칙 문서를 믿고 채운다.
# 배분율 줄(합이 1 이라 값이 틀려도 영업이익이 안 틀린다 — 라벨만 조용히 틀린다)의 「번호 + 의미어」를 문서에서 찾아 스캐폴드 12번 라벨의 의미어와 견준다.
_배분번호 = ("134", "138", "142", "168", "172")
_배분의미 = [("매출원가", ("제조", "매출원가")), ("연구개발", ("연구개발", "개발")), ("판관", ("판관", "판매관리", "판매비"))]
_배분말 = "제조|매출원가|판관|판매관리|판매비와관리비|판매비|연구개발|개발"
_배분re = (re.compile(r"(?<!\d)(%s)\s*(?:행)?\s*\(?\s*(%s)" % ("|".join(_배분번호), _배분말)),
          re.compile(r"(%s)\s*(?:배분)?\s*(%s)\s*행" % (_배분말, "|".join(_배분번호))))


def _배분군(글):
    for 군, 말들 in _배분의미:
        if any(m in 글 for m in 말들):
            return 군
    return None


def 규칙문서배분대조():
    """키트 문서(.md — 뿌리 · .claude/갈래)의 「배분 번호 + 의미어」가 스캐폴드 12번 라벨과 같은 뜻인가 → 걸린 줄 목록."""
    try:
        import openpyxl
        경로 = 좌표.스캐폴드경로(ROOT)
        지 = 좌표.지도찾기(경로)
        wb = openpyxl.load_workbook(경로)
        장 = 지.장(wb, "12")
    except Exception as e:                                  # noqa: BLE001
        return ["규칙문서배분대조를 못 돌았다 — %s" % e]
    라벨 = {}
    for 번, _n in 장.줄들():
        if str(번) in _배분번호:
            라벨[str(번)] = "%s" % (장.값("B", 번) or "")
    파일들 = [os.path.join(ROOT, f) for f in os.listdir(ROOT) if f.endswith(".md")]
    갈 = os.path.join(ROOT, ".claude", "갈래")
    if os.path.isdir(갈):
        파일들 += [os.path.join(갈, f) for f in os.listdir(갈) if f.endswith(".md")]
    걸림 = []
    for f in sorted(파일들):
        for k, 줄 in enumerate(io.open(f, encoding="utf-8", errors="ignore").read().splitlines(), start=1):
            for 식 in _배분re:
                for m in 식.finditer(줄):
                    번, 말 = (m.group(1), m.group(2)) if m.group(1) in _배분번호 else (m.group(2), m.group(1))
                    문, 표 = _배분군(말), _배분군(라벨.get(번, ""))
                    if 문 and 표 and 문 != 표:
                        걸림.append("  %s:%d — 문서 「%s %s」 vs 스캐폴드 12번 %s 「%s」" % (os.path.relpath(f, ROOT), k, 번, 말, 번, 라벨.get(번)))
    return 걸림


# ── 시트 이름 글자 — 워크북을 만지는 길은 `좌표.py` 하나여야 한다 ──────────────
# 스크립트가 시트 이름("12. 가정_시나리오")을 글자로 들고 있으면 좌표 지도를 안 거치고 칸을 만질 수 있다.
# 그러면 배치(또는 시트 이름)가 바뀔 때 그 자리만 조용히 옛 칸을 읽는다. 주석과 설명글(docstring)은 뺀다.
시트글자제외 = re.compile(r"은행워크북\.py$")          # 은행형 워크북은 제 손으로 짓는다 — 이 지도의 워크북이 아니다


def 시트이름글자(지):
    import ast                                            # noqa: PLC0415
    이름들 = 지.시트이름들()                              # 생성기가 새로 세운 시트는 옛 이름이 없다(None 을 넣지 않는다)
    걸림 = []
    for p in sorted(glob.glob(os.path.join(ROOT, "스크립트", "*.py"))):
        if 시트글자제외.search(p):
            continue
        try:
            나무 = ast.parse(io.open(p, encoding="utf-8").read())
        except SyntaxError:
            continue
        설명글 = set()
        for 마디 in ast.walk(나무):
            if isinstance(마디, (ast.Module, ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)) and 마디.body:
                첫 = 마디.body[0]
                if isinstance(첫, ast.Expr) and isinstance(getattr(첫, "value", None), ast.Constant):
                    설명글.add(id(첫.value))
        for 마디 in ast.walk(나무):
            if isinstance(마디, ast.Constant) and isinstance(마디.value, str) and id(마디) not in 설명글:
                든 = [n for n in 이름들 if n in 마디.value]
                if 든:
                    걸림.append("  %s:%d 에 시트 이름 「%s」 이 글자로 있다 — 좌표.py 의 시트 번호로 부를 것"
                                % (os.path.basename(p), 마디.lineno, 든[0]))
    return 걸림


# ── 워크북을 직접 만지는 꼴 — 시트 이름 글자가 없어도 좌표 지도를 안 거칠 수 있다 ──────────────
# 실측(검증 2026-10-01): 시트를 순서로 잡고(`wb.worksheets[11]`) `ws["D221"]`·`cell(row=30, …)` 로 만지는 파일을 심자
# 시트 이름 글자만 보던 점검이 통과시켰다. 그래서 꼴을 본다.
#   ① load_workbook 을 부르는데 좌표.py 를 안 들인다      ② 시트를 순서로 잡는다 — `….worksheets[정수]` · `….sheetnames[정수]`
#   ③ 시트에 칸 주소 글자로 첨자한다 — `ws["D221"]`        ④ 행을 상수로 준 `ws.cell(row=30, …)` · 열을 상수로 준 `ws.cell(r, 7)`
#   ⑤ 시트 이름 머리 글자로 시트를 고른다 — `w.title.startswith("12.")` · `"12." in w.title` · `w.title[:3] == "12."`
#   ⑥ 시트에 셈한 칸 주소로 첨자한다 — `ws["D%d" % r]` · `ws[f"D{r}"]` · `ws["D" + str(r)]`
# ③·④·⑥은 「시트」로 보이는 것에만 건다(load_workbook 이 낸 워크북에서 꺼낸 것, 그리고 **그것을 인자로 받은 함수의 매개변수**) —
# 엔진 결과 사전의 `E["2.DCF"]["D68"]` 은 번호다.
# (재검증 2026-10-02: 좌표.py 를 들이고도 함수 인자로 받은 시트 · 셈한 주소 · 시트 이름 머리로 만지는 파일 셋을 못 잡았다)
# **꼴을 보는 점검이다.** `getattr` 로 돌아가는 코드, 다른 파일의 함수로 시트를 넘기는 코드는 여전히 못 잡는다.
# **헛울음은 그 줄에 표시를 적어 푼다** — `# 지도밖: 까닭`. 이 지도의 워크북이 아닌 파일(남의 xlsx)을 만지는 줄이다.
# 까닭을 안 적은 표시는 그 자체가 걸린다. 파일을 통째로 빼는 목록(아래)은 늘리지 않는다 — 제 워크북을 짓는 은행형과
# 남의 파일만 읽는 다모다란 도구 둘뿐이다.
워크북도구제외 = re.compile(r"은행워크북\.py$|market_data\.py$")      # 제 워크북을 짓는다(은행형) · 남의 파일을 읽는다(다모다란 xlsx)
_칸주소글 = re.compile(r"^\$?[A-Za-z]{1,3}\$?[0-9]{1,7}(:\$?[A-Za-z]{1,3}\$?[0-9]{1,7})?$")
_칸주소틀 = re.compile(r"^\$?[A-Za-z]{1,3}\$?(%[ds]|\{\})?$")     # 셈한 칸 주소의 앞머리 — "D%d" · "D" · "D{}"
_시트머리글 = re.compile(r"^\d{1,2}\.\s?$|^\d{1,2}\.\s?\S")    # 시트 이름 머리 — "12." · "12. " · "12. 가정"
지도밖표시 = re.compile(r"#\s*지도밖\s*[:：]\s*(.*)$")


def 워크북직접만짐():
    import ast                                            # noqa: PLC0415
    import tokenize                                       # noqa: PLC0415

    def 끝이름(f):
        return f.attr if isinstance(f, ast.Attribute) else (f.id if isinstance(f, ast.Name) else None)

    def 상수(x, 종류):
        return isinstance(x, ast.Constant) and isinstance(x.value, 종류) and not isinstance(x.value, bool)

    걸림 = []
    for p in sorted(glob.glob(os.path.join(ROOT, "스크립트", "*.py"))):
        if 워크북도구제외.search(p):
            continue
        try:
            원글 = io.open(p, encoding="utf-8").read()
            나무 = ast.parse(원글)
        except SyntaxError:
            continue
        파일 = os.path.basename(p)
        마디들 = list(ast.walk(나무))
        표시 = {}                                         # 줄 번호 → `# 지도밖:` 뒤의 까닭(주석만 본다 — 글 속의 같은 글자는 표시가 아니다)
        try:
            for 토 in tokenize.generate_tokens(io.StringIO(원글).readline):
                m2 = 지도밖표시.search(토.string) if 토.type == tokenize.COMMENT else None
                if m2:
                    표시[토.start[0]] = m2.group(1).strip()
        except (tokenize.TokenError, IndentationError):
            pass

        def 푼줄(m):
            """그 마디의 줄(여러 줄에 걸친 문이면 그 가운데 어느 줄)에 `# 지도밖: 까닭` 이 있는가 → 까닭(없으면 None)."""
            for n in range(m.lineno, (getattr(m, "end_lineno", None) or m.lineno) + 1):
                if n in 표시:
                    return 표시[n]
            return None

        def 건다(m, 말):
            # 까닭이 든 표시가 있으면 그 줄은 이 지도의 워크북을 만지는 줄이 아니다. 까닭 없는 표시는 풀어 주지 않는다(아래에서 따로도 건다)
            if not 푼줄(m):
                걸림.append("  %s:%d %s" % (파일, m.lineno, 말))
        연다 = [m for m in 마디들 if isinstance(m, ast.Call) and 끝이름(m.func) == "load_workbook"]
        들인다 = any((isinstance(m, ast.Import) and any(a.name == "좌표" for a in m.names))
                  or (isinstance(m, ast.ImportFrom) and m.module == "좌표")
                  or (isinstance(m, ast.Call) and 끝이름(m.func) == "import_module" and m.args and 상수(m.args[0], str)
                      and m.args[0].value == "좌표")
                  for m in 마디들)
        if 연다 and not 들인다 and 파일 != "좌표.py":
            건다(연다[0], "가 load_workbook 으로 워크북을 여는데 좌표.py 를 안 들인다 — 칸은 좌표 지도를 거쳐 만질 것")
        # 워크북·시트로 보이는 이름 — load_workbook 이 낸 것과 거기서 꺼낸 것
        워크북들, 시트 = set(), set()

        def 책인가(x):
            return (isinstance(x, ast.Name) and x.id in 워크북들) or (isinstance(x, ast.Call) and 끝이름(x.func) in ("load_workbook", "Workbook"))

        def 시트인가(x):
            if isinstance(x, ast.Name):
                return x.id in 시트
            if isinstance(x, ast.Subscript):
                if isinstance(x.value, (ast.ListComp, ast.GeneratorExp)):      # [w for w in wb if …][0]
                    return any(책인가(g.iter) or (isinstance(g.iter, ast.Attribute) and g.iter.attr == "worksheets")
                               for g in x.value.generators)
                return 책인가(x.value) or (isinstance(x.value, ast.Attribute) and x.value.attr == "worksheets")
            if isinstance(x, ast.Attribute):
                return x.attr in ("active", "ws") and (x.attr == "ws" or 책인가(x.value))
            return False

        함수들 = {m.name: m for m in 마디들 if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))}
        for _돌 in range(3):                              # 이름이 이름으로 넘어가는 것을 두어 번 따라간다
            for m in 마디들:
                if isinstance(m, ast.Assign):
                    for t in m.targets:
                        if isinstance(t, ast.Name):
                            if 책인가(m.value):
                                워크북들.add(t.id)
                            elif 시트인가(m.value):
                                시트.add(t.id)
                elif isinstance(m, ast.For) and isinstance(m.target, ast.Name):
                    it = m.iter
                    if 책인가(it) or (isinstance(it, ast.Attribute) and it.attr == "worksheets"):
                        시트.add(m.target.id)
                elif isinstance(m, ast.comprehension) and isinstance(m.target, ast.Name):
                    if 책인가(m.iter) or (isinstance(m.iter, ast.Attribute) and m.iter.attr == "worksheets"):
                        시트.add(m.target.id)
                elif isinstance(m, ast.Call) and isinstance(m.func, ast.Name) and m.func.id in 함수들:
                    # 시트(또는 워크북)를 인자로 받은 이 파일의 함수 — 그 매개변수도 시트(워크북)다
                    매개 = [a.arg for a in 함수들[m.func.id].args.args]
                    for i, 인자 in enumerate(m.args):
                        if i < len(매개):
                            if 시트인가(인자):
                                시트.add(매개[i])
                            elif 책인가(인자):
                                워크북들.add(매개[i])
                    for k in m.keywords:
                        if k.arg in 매개:
                            if 시트인가(k.value):
                                시트.add(k.arg)
                            elif 책인가(k.value):
                                워크북들.add(k.arg)

        def 제목인가(x):
            """시트 이름을 읽는 꼴인가 — `….title` · `….title[:3]` · `….sheetnames` 의 낱낱."""
            if isinstance(x, ast.Subscript):
                x = x.value
            return isinstance(x, ast.Attribute) and x.attr in ("title", "sheetnames")

        def 셈한주소(x):
            """칸 주소를 셈해 만든 글인가 — "D%d" % r · f"D{r}" · "D" + str(r) · "D{}".format(r). → 앞머리 글 또는 None."""
            if isinstance(x, ast.BinOp) and isinstance(x.op, (ast.Mod, ast.Add)) and 상수(x.left, str) and _칸주소틀.match(x.left.value):
                return x.left.value
            if isinstance(x, ast.JoinedStr) and x.values and 상수(x.values[0], str) and _칸주소틀.match(x.values[0].value) \
                    and any(isinstance(v, ast.FormattedValue) for v in x.values):
                return x.values[0].value + "{…}"
            if isinstance(x, ast.Call) and isinstance(x.func, ast.Attribute) and x.func.attr == "format" and 상수(x.func.value, str) \
                    and _칸주소틀.match(x.func.value.value):
                return x.func.value.value
            return None
        for m in 마디들:
            if isinstance(m, ast.Subscript):
                첨자 = m.slice
                if isinstance(m.value, ast.Attribute) and m.value.attr in ("worksheets", "sheetnames") and 상수(첨자, int):
                    건다(m, "가 시트를 순서로 잡는다(%s[%d]) — 시트는 좌표.py 의 시트 번호로 부를 것" % (m.value.attr, 첨자.value))
                elif 시트인가(m.value) and 상수(첨자, str) and _칸주소글.match(첨자.value):
                    건다(m, "가 시트에 칸 주소 글자로 첨자한다(「%s」) — 칸은 좌표.py 의 칸 번호로 부를 것" % 첨자.value)
                elif 시트인가(m.value) and 셈한주소(첨자) is not None:
                    건다(m, "가 시트에 셈한 칸 주소로 첨자한다(「%s…」) — 칸은 좌표.py 의 (열 ID, 번호)로 부를 것" % 셈한주소(첨자))
            elif isinstance(m, ast.Call) and isinstance(m.func, ast.Attribute) and m.func.attr == "cell" and 시트인가(m.func.value):
                행 = next((k.value for k in m.keywords if k.arg == "row"), m.args[0] if m.args else None)
                열 = next((k.value for k in m.keywords if k.arg == "column"), m.args[1] if len(m.args) > 1 else None)
                if 상수(행, int):
                    건다(m, "가 행을 상수로 준 cell(row=%d) 로 칸을 만진다 — 줄은 좌표.py 의 가정 번호로 부를 것" % 행.value)
                elif 상수(열, int):
                    건다(m, "가 열을 상수로 준 cell(column=%d) 로 칸을 만진다 — 열은 좌표.py 의 열 ID 로 부를 것" % 열.value)
            elif isinstance(m, ast.Call) and isinstance(m.func, ast.Attribute) and m.func.attr == "startswith" \
                    and 제목인가(m.func.value) and m.args and 상수(m.args[0], str) and _시트머리글.match(m.args[0].value):
                건다(m, "가 시트 이름 머리 글자로 시트를 고른다(startswith(「%s」)) — 시트는 좌표.py 의 시트 번호로 부를 것" % m.args[0].value)
            elif isinstance(m, ast.Compare) and len(m.comparators) == 1:
                왼, 오 = m.left, m.comparators[0]
                for 글쪽, 제목쪽 in ((왼, 오), (오, 왼)):
                    if 상수(글쪽, str) and _시트머리글.match(글쪽.value) and 제목인가(제목쪽):
                        건다(m, "가 시트 이름 머리 글자로 시트를 고른다(「%s」) — 시트는 좌표.py 의 시트 번호로 부를 것" % 글쪽.value)
                        break
        for n in sorted(n for n, 까닭 in 표시.items() if not 까닭):
            걸림.append("  %s:%d 의 `# 지도밖:` 표시에 까닭이 없다 — 왜 좌표 지도를 안 거쳐도 되는 줄인지 적을 것" % (파일, n))
    return 걸림


# ── 지침 파일의 덤프 명령 — 시트 이름 글자로 주면 시트 이름이 바뀐 배치에서 덤프가 안 나온다 ──────────
def 지침덤프명령(지):
    이름들 = 지.시트이름들()
    대상 = [os.path.join(ROOT, f) for f in os.listdir(ROOT) if f.endswith(".md")]
    for 뿌리, 폴더들, 파일들 in os.walk(os.path.join(ROOT, ".claude")):
        대상.extend(os.path.join(뿌리, f) for f in 파일들 if f.endswith(".md"))
    걸림 = []
    for p in sorted(대상):
        try:
            줄들 = io.open(p, encoding="utf-8").read().split("\n")
        except Exception:                                  # noqa: BLE001
            continue
        for 번, 줄 in enumerate(줄들, 1):
            if "--시트" not in 줄:
                continue
            뒤 = 줄.split("--시트", 1)[1]
            든 = [n for n in 이름들 if n in 뒤]
            if 든:
                걸림.append("  %s:%d 의 덤프 명령이 시트 이름 글자다(「%s」) — 번호로 줄 것(--시트 %s)"
                            % (os.path.relpath(p, ROOT), 번, 든[0], 지.시트번호(든[0])))
    return 걸림


# ── 납품 배치의 산출 칸 — 붓기 `_산출붓기`(W6a)가 엔진 값을 값으로 적는 1번 · 14번 칸 ─────────────
def 납품산출칸(지):
    """[(시트 번호, (열 ID, 번호))] — 1번 시나리오별 결과 61~63(값1~값3) · 역산 DCF 분석 136~138(값2 시장 내재 가정 · 값3 비고),
    14번 민감도 표 다섯(Ⅰ 11~16 · Ⅱ 21~26 · Ⅲ 31~40 · Ⅳ 46~50 · Ⅴ 56~62 — W1~W6). 14번이 없는 배치면 1번만(붓기도 건너뛴다).
    매출 구분별 역산 줄(1번 23s)은 수준 경로를 선언할 때만 서는 줄이라 넣지 않는다(견본 지도에는 없다)."""
    낸 = [("1", (열, 번)) for 번 in (61, 62, 63) for 열 in ("값1", "값2", "값3")]
    낸 += [("1", (열, 번)) for 번 in (136, 137, 138) for 열 in ("값2", "값3")]
    try:
        지.sid("14")
    except 좌표.좌표오류:
        return 낸
    W = ["W%d" % i for i in range(1, 7)]
    for 첫 in (11, 21):                               # 표 Ⅰ · Ⅱ — 머리 줄(가로 칸 값 W2~W6) + 다섯 줄(W1 세로 값 · W2~W6 주당가치)
        낸 += [("14", (w, 첫)) for w in W[1:]] + [("14", (w, 번)) for 번 in range(첫 + 1, 첫 + 6) for w in W]
    낸 += [("14", (w, 번)) for 번 in range(31, 41) for w in W]                 # Ⅲ 주요 가정 변동(손잡이 여섯까지)
    낸 += [("14", ("W1", 47))] + [("14", (w, 번)) for 번 in (46, 48, 49, 50) for w in W]   # Ⅳ 역산(47 = 종가)
    낸 += [("14", (w, 번)) for 번 in range(56, 63) for w in W]                 # Ⅴ 동인 2축(선언했을 때만 값이 선다)
    return 낸


# ── 지도확증 — 스크립트가 부르는 번호가 지금 배치에 있는가 ─────────────────
# 배치는 생성기가 바꾼다. 줄을 빼거나 묶음을 풀면 번호는 남아 있는데 자리가 없어진다 — 붓기는 「남음」으로,
# 대조는 좌표 오류로 멈추지만 그것은 회차 도중이다. 여기서는 키트를 고친 자리에서 미리 본다.
def 지도확증():
    걸림 = []
    경로 = 좌표.스캐폴드경로(ROOT)
    try:
        import openpyxl                                   # noqa: PLC0415
        지 = 좌표.지도찾기(경로)
        wb = openpyxl.load_workbook(경로)
        찍혀있다 = 지.확인(wb)
    except Exception as e:                                # noqa: BLE001
        걸림.append("  좌표 지도를 못 읽었다 — %s" % e)
        print("  지도확증 실패 — 좌표 지도(또는 스캐폴드)를 못 읽어 아무것도 보지 못했다")
        for t in 걸림:                                    # 예전에는 이 글을 돌려주기만 하고 안 찍어, 지도가 없으면 글 없이 rc 1 이었다
            print(t)
        return 걸림
    # ⓪ 스캐폴드와 좌표 지도가 지문으로 짝인가 — 지문이 없는 스캐폴드에는 붓기가 멈춘다
    if not 찍혀있다:
        걸림.append("  스캐폴드에 배치 지문이 없다 — 좌표 지도와 짝인지 확인할 수 없고 붓기가 멈춘다"
                    "(생성기가 지은 스캐폴드에는 지문이 있다. 지문이 없으면 스캐폴드짓기.py 로 다시 짓는다)")
    # **지문은 꼬리표다** — 지문을 남긴 뒤에 엑셀로 줄을 끼운 스캐폴드도 지문은 그대로다. 구조(값 있는 칸의 자리 · 줄 이름)를 견준다.
    # 실측(재검증 2026-10-02): 지문 있는 스캐폴드에 줄 하나를 끼웠더니 이 점검 · 붓기 · 엑셀 · 대조가 전부 맞는 짝으로 봤다
    구조걸림, 구조본 = 지.구조견줌(wb, 부은=False)
    for x in 구조걸림:
        걸림.append("  스캐폴드의 구조가 좌표 지도와 다르다 — %s. %s — 붓기가 멈춘다"
                    % (x, "지문은 같으니 지문을 남긴 뒤에 줄·열을 고친 스캐폴드다" if 찍혀있다 else "이 지도의 스캐폴드가 아니다"))

    def 있나(시트, 칸번호, 누가):
        # 열 ID 가 글자가 아닌 칸(값1 · W3 · FY2027E)은 「열 ID@번호」로 적는다(좌표.자리풀기 의 꼴 — 「값161」 처럼 붙지 않게)
        뜻열 = isinstance(칸번호, tuple) and not re.fullmatch(r"[A-Za-z]{1,3}", "%s" % 칸번호[0])
        글 = ("%s@%d" % 칸번호) if 뜻열 else 좌표.칸글(칸번호)
        try:
            if 지.칸(시트, 칸번호) is None:
                걸림.append("  %s 가 부르는 %s번 %s 가 이 배치에 없다(뺀 줄·열)" % (누가, 시트, 글))
        except 좌표.좌표오류 as e:
            걸림.append("  %s 가 부르는 %s번 %s — %s" % (누가, 시트, 글, e))

    # ① 대조 — 대조표·스칼라표. W3c: 대조할 줄은 지도의 「대조줄」(생성기가 줄 명세에서 낸 등록부)에서 온다 — 없으면 대조가 멈춘다
    대 = importlib.import_module("대조")
    if 대.대조줄(지) is None:
        걸림.append("  좌표 지도에 「대조줄」이 없다 — 대조할 줄의 등록부를 싣기 전에 지은 스캐폴드다. 대조가 멈춘다(다시 짓는다)")
    for _키, _행키, 시트, 번 in 대.대조표(지):
        for c in 지.기간열():
            있나(시트, (c, 번), "대조표")
    for _키, 시트, 칸 in 대.스칼라표(지):
        있나(시트, 칸, "스칼라표")
    있나(대.적용시나리오칸[0], 대.적용시나리오칸[1], "대조(적용 시나리오)")
    # ② 엔진이 아는 가정 머리 행이 지도의 가정묶음에 있는가 (붓기는 이 묶음으로만 붓는다). 늘 서는 줄만 — 구조가 짓는 줄
    #    (수준 경로 · 인건비 · 원가 줄 …)은 견본 지도에 없어도 된다(회차의 스캐폴드가 그 구조로 짓는다)
    엔 = importlib.import_module("dcf엔진")
    try:
        묶음 = {번 for 번, _줄 in 지.가정묶음("12", 지.장(wb, "12"))}
    except 좌표.좌표오류 as e:
        묶음 = set()
        걸림.append("  가정묶음을 못 읽었다 — %s" % e)
    for r in tuple(엔.가정머리행):
        if int(r) not in 묶음:
            걸림.append("  엔진의 가정 머리 행 %s 이 좌표 지도의 가정묶음에 없다 — 붓기가 그 줄을 못 붓는다" % r)
    for r in 엔.시점가정행:
        for c in ("D", "E", "F"):
            있나("12", "%s%s" % (c, r), "시점가정")
    # ②-덧 납품 배치(W6a) — 엔진의 시트인데 시간축이 아닌 시트(1번 요약 · 3번 · 11번)의 대조 칸(값1~값3 · 예측값 · 영구값 …)이
    #    이 배치에 있는가, 붓기 `_산출붓기` 가 엔진 값을 적는 1번 · 14번 칸이 있는가(없으면 대조가 칸을 못 찾고 붓기가 값을 버린다)
    for 시, 키 in sorted(대.엔진시트().items()):
        줄들 = (대.대조줄(지) or {}).get(시)
        if not 줄들 or all(c in (지.자료["시트"][지.sid(시)].get("열ID") or {}) for c in 지.기간열()):
            continue                                       # 시간축 시트는 ① 이 기간 열마다 보았다
        for 번, 속 in 줄들.items():
            for 열 in (list((속.get("칸") or {}).values()) if 속.get("쓰임") else list(속.get("열") or ())):
                있나(시, (열, int(번)), "대조(엔진의 시트 %s)" % 키)
    for 시, 칸 in 납품산출칸(지):
        있나(시, 칸, "붓기(모델 산출값 — 1번 · 14번)")
    # ③ 지도가 키트 스크립트가 읽는 표를 실었는가 — 없으면 워크북의 글을 열쇠로 읽게 된다
    if 지.단위("12") is None:
        걸림.append("  좌표 지도에 「단위」가 없다 — 자체검사가 워크북의 단위 칸 글을 읽게 된다(스캐폴드짓기.py 로 다시 짓는다)")
    if 지.묶음출처 != "좌표 지도":
        걸림.append("  좌표 지도에 「가정묶음」이 없다 — 붓기가 줄 이름 글자(· 비관/· 기준/· 낙관)로 머리 행을 찾게 된다"
                    "(스캐폴드짓기.py 로 다시 짓는다)")
    if "S12" not in (지.자료.get("단위종류") or {}):
        걸림.append("  좌표 지도에 「단위종류」가 없다 — 자체검사 ⑫ 가 단위 낱말(「%」「명」「일」)을 종류로 옮겨 읽게 된다"
                    "(생성기가 명세에서 낸다 — 스캐폴드짓기.py 로 다시 짓는다)")
    if 지.자료.get("이름칸") is None:
        걸림.append("  좌표 지도에 「이름칸」이 없다 — 붓기가 줄 이름 속의 자리표시 글자(「제품군 N」「원가 항목 N」)로 이름 칸을 찾게 된다"
                    "(생성기가 명세에서 낸다 — 스캐폴드짓기.py 로 다시 짓는다)")
    elif not any(칸들 for 열쇠들 in 지.이름칸().values() for 칸들 in 열쇠들.values()):
        걸림.append("  좌표 지도의 「이름칸」에 이 배치의 칸이 하나도 없다 — 메타.스트림이름·원가이름 이 워크북에 안 들어간다")
    if not all(isinstance(한, dict) and 한.get("구분") for 한 in (지.자료.get("기간열") or [None])):
        걸림.append("  좌표 지도의 「기간열」에 구분(실적·예측·영구)이 없다 — 붓기가 어느 열이 실적 · 예측 · 영구인지 모른다"
                    "([{\"id\": …, \"구분\": …}] 꼴 — 생성기가 낸다 — 다시 짓는다)")
    # 기간 열이 지도의 축(「기간」)과 같은가 — 열 ID · 구분 · 순서. 축이 없는 지도(기간 없이 지은 것)에는 붓기·대조가 멈춘다.
    # 키트 뿌리의 스캐폴드는 기본 기간으로 지은 견본이다 — 회차의 가정과 같은 기간인지는 붓기 · 대조가 그 가정으로 본다
    try:
        지.기간열확인()
    except 좌표.좌표오류 as e:
        걸림.append("  %s" % e)
    # 이름 칸의 틀이 스캐폴드의 그 칸의 글과 맞는가 — 줄 이름을 고쳤는데 틀이 옛 글이면 붓기가 그 칸에 이름을 안 쓴다
    if 지.자료.get("이름칸") is not None:
        틀다른 = 지.이름틀견줌(wb)
        if 틀다른:
            걸림.append("  좌표 지도의 「이름칸」 틀이 스캐폴드의 줄 이름과 안 맞는 칸 %d곳(%s) — 붓기가 그 칸에 이름을 쓰지 않는다(「이름 미전파」). "
                        "줄 이름을 고쳤으면 지도의 틀도 함께 낼 것(줄 명세를 고쳐 다시 짓는다)"
                        % (len(틀다른), " / ".join(틀다른[:3])))
    if 구조본["줄이름"] is None:
        걸림.append("  좌표 지도에 「줄이름지문」이 없다 — 꼴이 같은 줄끼리 자리를 바꾼 스캐폴드를 못 가린다(자리만 견준다)"
                    "(생성기가 명세에서 낸다 — 스캐폴드짓기.py 로 다시 짓는다)")
    # 종류를 모르는 단위 낱말이 가정 머리 줄에 있는가 — 있으면 자체검사 ⑫ 가 그 줄을 못 잰다
    _종류, 모름 = 지.단위종류("12")
    모르는 = sorted((번, 낱) for 번, 낱 in 모름.items() if 번 in 묶음)
    if 모르는:
        걸림.append("  종류를 모르는 단위 낱말이 가정 머리 줄 %d곳에 있다(%s) — 자체검사 ⑫ 가 그 줄을 못 잰다. "
                    "지도의 「단위종류」에 종류(비율·수준·그밖)를 싣거나 좌표.py 의 단위종류표에 낱말을 더할 것"
                    % (len(모르는), " · ".join("%d 「%s」" % x for x in 모르는[:6])))
    # ④ 스크립트가 좌표 지도를 안 거치고 워크북을 만지지 않는가 — 시트 이름 글자 · 순서로 잡은 시트 · 칸 주소 글자
    걸림.extend(시트이름글자(지))
    걸림.extend(워크북직접만짐())
    # ⑤ 지침 파일의 덤프 명령이 시트 이름 글자가 아닌가
    걸림.extend(지침덤프명령(지))
    print("  지도확증 %s — 좌표 지도 %s (지문 %s · 가정묶음 %d개)"
          % ("통과" if not 걸림 else "실패 %d건" % len(걸림), 지.경로, 지.지문(), len(묶음)))
    for t in 걸림:
        print(t)
    return 걸림


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--자기확증", action="store_true")
    ap.add_argument("--지도", action="store_true", help="스크립트가 부르는 번호가 지금 좌표 지도에 다 있는지")
    ap.add_argument("--사전", action="store_true", help="계산된 옛↔현행 좌표를 보여 준다")
    a = ap.parse_args()
    항목들, 범위들 = 좌표계산()
    if a.사전:
        for 항 in 항목들:
            print("  %2s번 %-4d ← 옛 %-12s %s"
                  % (항["시트"], 항["현행"], ",".join(str(x) for x in sorted(항["옛"])), 항["이름"]))
        for 범 in 범위들:
            print("  %2s번 %-9s ← 옛 %s" % (범["시트"], 범["현행"], ", ".join(sorted(범["옛범위"]))))
        return 0
    if a.자기확증:
        return 0 if 자기확증(항목들) else 1
    if a.지도:
        return 1 if 지도확증() else 0
    if 지도확증():                       # 스크립트가 부르는 번호가 지금 배치에 있는가 — 없으면 나머지를 볼 것도 없다
        return 1
    걸린것 = 점검(항목들, 범위들)
    템플릿걸림 = 템플릿대조()
    if 템플릿걸림:
        print("가정_템플릿 ↔ 엔진 가정머리행 대조 — %d건. "
              "**「없는 행」은 「빈 행」이 아니다 — 붓기가 빠짐으로 울고 검사 ㉚ 이 눈을 잃는다**"
              % len(템플릿걸림))
        for t in 템플릿걸림:
            print(t)
        return 1
    이름걸림 = 행이름대조() + 규칙문서배분대조()
    if 이름걸림:
        print("행이름 ↔ 스캐폴드 라벨 대조 — %d건. **좌표는 맞는데 이름이 갈린다 — 사람이 거꾸로 채우게 만드는 종류다**" % len(이름걸림))
        for t in 이름걸림:
            print(t)
        return 1
    if not 걸린것:
        print("좌표점검 — 0건. 문서·문구가 현행 좌표를 쓴다 (행이름↔스캐폴드 라벨 · 가정_템플릿↔가정머리행 대조 포함)")
        return 0
    print("좌표점검 — 옛 좌표 잔존 %d건. 코드는 현행인데 글이 옛 판이다\n" % len(걸린것))
    for 경로, 번호, 이름, 현행, 줄 in 걸린것:
        print("  %s  [%s → 현행 %s]" % (("%s:%d" % (경로, 번호)) if 번호 else 경로, 이름, 현행))
        print("      %s" % 줄)
    print("\n**이 줄들을 시키는 대로 따라 하면 조용히 틀린다** — 값이 엔진이 안 읽는 칸에 들어간다.")
    return 1


if __name__ == "__main__":
    sys.exit(main())

# -*- coding: utf-8 -*-
"""키트에넣기 — 정본(줄명세/)으로 스캐폴드와 좌표 지도를 지어 키트 사본에 넣는다.

정본이 명세가 된 뒤로(산식 개편 W1) 키트 사본의 스캐폴드는 정본의 산출물이다. 정본이나 생성기를 고치면 다시 지어 넣어야
엔진 · 붓기 · 대조가 읽는 스캐폴드가 명세와 같다(시험 1 ⑩ 이 이것을 본다).

하는 일
  1. 정본을 같은 배치로 짓는다(산출/키트넣기/ 에 — 짓기의 오류 · 위험한 경고가 있으면 멈춘다). `--납품` 이면 납품 배치(배치_납품.py —
     시트 15장 · 번호 열 · 표준 서식 길)로 짓고 좌표 지도에 「배치: 납품」을 적는다(시험 1 ⑩ 이 이 표지를 보고 같은 배치로 지어 견준다).
     좌표 지도의 「이름칸」·「단위종류」·「줄이름지문」·「명세지문」·「구조지문」은 짓기가 바로 싣는다(W3a — 짓기._지도덧).
  2. 지은 것이 키트 사본의 것과 같은지 본다(수식 · 상수 · 글 · 병합 · 유효성 · 지도의 열쇠). 같으면 아무것도 안 바꾼다.
  3. 다르면 — `--보관 <이름>` 을 줬으면 지금 것을 `키트/보관/스캐폴드_<오늘>_<이름>/` 에 옮겨 두고 —
     지은 스캐폴드 · 지도를 키트 뿌리에 놓는다(지도의 표는 짓기가 다 실었다 — 키트의 `좌표지도보강.py` 는 걷었다. W3 맞물림).
  4. `키트/스크립트/좌표.py --확인` 으로 짝(지문 · 구조)을 확인한다.

쓰기:  python 키트에넣기.py --보기                 바뀌는지만 본다(키트를 안 건드린다)
       python 키트에넣기.py                        바뀌었으면 바꿔 넣는다(옛 것은 git 이력에만 남는다)
       python 키트에넣기.py --보관 걷기전           바꿔 넣기 전에 지금 것을 키트/보관/ 에 옮겨 둔다
       python 키트에넣기.py --납품 [--보관 이름]    납품 배치 · 표준 서식 길로 지어 넣는다(L1 묶기)
       덧붙임: --키트 <폴더>  구현/키트 대신 그 키트 사본에 넣는다(시험용 사본에서 먼저 돌려 볼 때)
               --기간 <가정.json | 기본>  시간축 열을 그 가정의 기간(평가기준일 · 결산월 · 실적연도수 · 상세추정연수 · 수렴연수)으로 짓는다
                      (열 ID = 기간 ID. 「기본」은 줄명세/책.json 의 「기본기간」). 안 주면 명세의 틀(열 ID H1 … E11 · TV)로 짓는다 —
                      기간 ID 로 붓는 키트(W2 통합 뒤)에는 --기간 을 주어 넣는다. 좌표 지도에 「기간」(축)이 실리고 시험 1 ⑩ 이 그것으로 다시 지어 견준다.
               --곳 <폴더>   키트 뿌리가 아니라 그 폴더에 스캐폴드 · 좌표 지도를 낸다(회차 폴더 — 그 회차의 가정으로 지을 때).
                      견주지 않고 늘 새로 지어 놓는다. 짝 확인은 --키트(기본 구현/키트)의 스크립트로 그 폴더의 파일에 돌린다.
                      키트의 `스크립트/스캐폴드짓기.py <가정.json> <폴더>` 가 이 길을 부른다(W2 통합 — 「짓고 나서 붓는다」).

납품 배치로 지은 스캐폴드를 쓰는 키트는 붓기 뒤 · 엑셀 재계산 앞에 `python 생성기/서식마감.py <부은 xlsx> <좌표 지도> <낼 xlsx>` 를 부른다
(안 쓰는 예측 열 접기 · 시나리오 세 줄 접기 · 바닥글 — 값을 보아야 정해지는 서식).
그 밖의 배치(시트를 옮기거나 열을 바꾸는)는 이 도구가 아니라 그 배치로 짓는 길을 따로 세운다.
"""
import sys
import os
import json
import shutil
import subprocess
import datetime

import openpyxl

import 줄무늬
import 짓기 as 짓기모듈
from 공통 import 배치오류

여기 = os.path.dirname(os.path.abspath(__file__))
정본 = os.path.join(여기, "줄명세")
키트 = os.path.normpath(os.path.join(여기, "..", "키트"))
틀이름, 지도이름 = "DCF_워크북_스캐폴드.xlsx", "DCF_워크북_좌표지도.json"
작업 = os.path.join(여기, "산출", "키트넣기")


def 칸들(경로):
    """xlsx 의 칸 값(수식 글 · 상수 · 글) · 병합 · 유효성 — 견줄 꼴로."""
    wb = openpyxl.load_workbook(경로)
    칸 = {(ws.title, c.coordinate): getattr(c.value, "text", c.value) for ws in wb for c in ws._cells.values() if c.value is not None}
    덧 = {"시트": wb.sheetnames,
         "병합": {ws.title: sorted(str(m) for m in ws.merged_cells.ranges) for ws in wb},
         "유효성": {ws.title: sorted((str(d.sqref), d.formula1) for d in ws.data_validations.dataValidation) for ws in wb}}
    return 칸, 덧


def 견줌(새틀, 새지도, 옛틀, 옛지도):
    """지은 것과 키트 사본의 것을 견준다 → 다른 점의 목록(비면 같다)."""
    if not (os.path.exists(옛틀) and os.path.exists(옛지도)):
        return ["키트 사본에 스캐폴드나 좌표 지도가 없다"]
    다른 = []
    가, 가덧 = 칸들(새틀)
    나, 나덧 = 칸들(옛틀)
    칸다름 = sorted(k for k in set(가) | set(나) if 가.get(k) != 나.get(k))
    if 칸다름:
        다른.append("칸 %d곳 (%s …)" % (len(칸다름), " · ".join("%s!%s" % k for k in 칸다름[:4])))
    다른 += ["%s" % 키 for 키 in 가덧 if 가덧[키] != 나덧[키]]
    with open(새지도, encoding="utf-8") as f:
        새 = json.load(f)
    with open(옛지도, encoding="utf-8") as f:
        옛 = json.load(f)
    # 지도의 열쇠는 전부 생성기가 낸다(키트의 좌표지도보강.py 는 걷었다) — 키트 사본에만 있는 열쇠(옛 「보강」 기록)도 다른 것으로 본다
    다른 += ["좌표 지도의 「%s」" % k for k in sorted(새) if (k != "기간열" or 새.get("기간")) and 새[k] != 옛.get(k)]
    다른 += ["좌표 지도의 「%s」(키트 사본에만 있다)" % k for k in sorted(옛) if k not in 새]
    return 다른


def 명세지문적기(키트, 지도경로):
    """키트의 `스크립트/명세지문.json` 에 그 지도의 「명세지문」을 적는다(같으면 그대로 둔다) → 적은 글자.

    구조 지문은 지도 자신의 명세 지문으로 센다 — 명세를 고쳐 지은 스캐폴드도 제 지도와는 맞는다. 키트가 「지금의 명세」를 따로 알아야
    다른 판의 명세로 지은 스캐폴드를 붓기 · 대조가 가린다(`좌표.본체명세지문`)."""
    with open(지도경로, encoding="utf-8") as f:
        지문 = json.load(f).get("명세지문")
    곳 = os.path.join(키트, "스크립트", "명세지문.json")
    try:
        with open(곳, encoding="utf-8") as f:
            옛 = json.load(f).get("명세지문")
    except (OSError, ValueError):
        옛 = None
    if 지문 and 지문 != 옛:
        with open(곳, "w", encoding="utf-8", newline="\n") as f:
            json.dump({"명세지문": 지문, "적은곳": "생성기/키트에넣기.py"}, f, ensure_ascii=False, indent=1)
            f.write("\n")
        print("키트의 명세 지문을 적었다: %s (%s → %s)" % (곳, 옛 or "없음", 지문))
    return 지문


def main(인자, 키트=키트):
    깃발 = {a for a in 인자 if a.startswith("--")}
    if 깃발 - {"--보기", "--보관", "--납품", "--키트", "--기간", "--곳"}:
        raise SystemExit(__doc__)
    곳 = None
    if "--곳" in 인자:
        i = 인자.index("--곳")
        if i + 1 >= len(인자) or 인자[i + 1].startswith("--"):
            raise SystemExit("--곳 뒤에 스캐폴드 · 좌표 지도를 낼 폴더를 적는다")
        곳 = os.path.abspath(인자[i + 1])
    기간 = None
    if "--기간" in 인자:
        i = 인자.index("--기간")
        if i + 1 >= len(인자) or 인자[i + 1].startswith("--"):
            raise SystemExit("--기간 뒤에 가정 파일(.json)이나 「기본」을 적는다")
        기간 = 인자[i + 1]
        if 기간 == "기본":
            with open(os.path.join(정본, "책.json"), encoding="utf-8") as f:
                기간 = json.load(f).get("기본기간")
            if not 기간:
                raise SystemExit("줄명세/책.json 에 「기본기간」이 없다")
        elif not os.path.exists(기간):
            raise SystemExit("가정 파일이 없다: %s" % 기간)
    보관이름 = None
    if "--보관" in 인자:
        i = 인자.index("--보관")
        if i + 1 >= len(인자) or 인자[i + 1].startswith("--"):
            raise SystemExit("--보관 뒤에 이름을 적는다(키트/보관/스캐폴드_<오늘>_<이름>/)")
        보관이름 = 인자[i + 1]
    if "--키트" in 인자:
        i = 인자.index("--키트")
        if i + 1 >= len(인자) or 인자[i + 1].startswith("--") or not os.path.isdir(os.path.join(인자[i + 1], "스크립트")):
            raise SystemExit("--키트 뒤에 키트 폴더를 적는다(그 안에 스크립트/ 가 있어야 한다)")
        키트 = os.path.abspath(인자[i + 1])
    납품 = "--납품" in 깃발
    지을곳 = 작업
    if 곳:      # 회차 폴더에 낼 때는 제 임시 폴더에서 짓는다(여러 회차를 함께 지어도 산출/키트넣기/ 를 다투지 않는다)
        import tempfile
        지을곳 = tempfile.mkdtemp(prefix="스캐폴드짓기_")
    os.makedirs(지을곳, exist_ok=True)
    새틀, 새지도 = os.path.join(지을곳, 틀이름), os.path.join(지을곳, 지도이름)
    try:
        if 납품:
            import 배치_납품
            명, _덧 = 배치_납품.명세읽기(정본, 기간=기간)
            지은 = 짓기모듈.짓기(명, 배치_납품.납품배치(명), 새틀, 새지도)
        else:
            명 = 줄무늬.읽기(정본, 기간=기간)
            지은 = 짓기모듈.짓기(명, 짓기모듈.같은배치(명), 새틀, 새지도)
    except 배치오류 as e:
        for o in e.오류목록[:20]:
            print("[%s] %s" % (o["종류"], o["설명"][:300]))
        print("정본이 지어지지 않는다 — 오류 %d건. 키트 사본은 그대로다" % len(e.오류목록))
        return 1
    위험 = [w for w in 지은["경고"] if w["종류"] in 짓기모듈.위험경고]
    print("지었다: %s · 경고 %d건(위험 %d건)" % (새틀, len(지은["경고"]), len(위험)))
    if 위험:
        for w in 위험[:10]:
            print("  [%s] %s" % (w["종류"], w["설명"][:300]))
        print("위험한 경고가 있다 — 키트 사본은 그대로다")
        return 2
    # 가정 파일의 이름이 들어갈 칸(이름칸) · 12번 줄의 단위 종류 · 줄 이름 지문 · 명세 지문 · 구조 지문은 짓기가 지도에 바로 싣는다(W3a —
    # 짓기._지도덧). 여기서는 ① 짓기가 적은 「명세」「원본」의 절대 경로를 파일 이름만 남기고(키트에는 이 컴퓨터의 경로를 싣지 않는다 —
    # 키트의 좌표지도보강.py 가 하던 일이다. 그 도구는 걷었다 — W3 맞물림) ② 납품 배치면 그 표지를 적는다(시험 1 ⑩ 이 같은 배치로 지어 견준다)
    with open(새지도, encoding="utf-8") as f:
        자료 = json.load(f)
    for 키 in ("명세", "원본"):
        if isinstance(자료.get(키), str):
            자료[키] = os.path.basename(자료[키].replace("\\", "/").rstrip("/"))
    if 납품:
        자료["배치"] = "납품"
    with open(새지도, "w", encoding="utf-8", newline="\n") as f:
        json.dump(자료, f, ensure_ascii=False, separators=(",", ":"))
        f.write("\n")
    with open(새지도, encoding="utf-8") as f:
        새지문 = json.load(f).get("지문")
    if 곳:      # 회차 폴더 — 견주지 않고 놓는다
        os.makedirs(곳, exist_ok=True)
        옛틀, 옛지도 = os.path.join(곳, 틀이름), os.path.join(곳, 지도이름)
        shutil.copy(새틀, 옛틀)
        shutil.copy(새지도, 옛지도)
        shutil.rmtree(지을곳, ignore_errors=True)
        if 보강확인(키트, 옛틀, 옛지도):
            return 1
        print("지어 놓았다: %s — 지문 %s" % (곳, 새지문))
        return 0
    옛틀, 옛지도 = os.path.join(키트, 틀이름), os.path.join(키트, 지도이름)
    다른 = 견줌(새틀, 새지도, 옛틀, 옛지도)
    if "--보기" not in 깃발:
        명세지문적기(키트, 새지도)       # 키트가 아는 줄 명세의 판 — 붓기 · 대조가 회차 지도의 명세 지문을 이것과 견준다(다르면 멈춘다)
    if not 다른:
        print("키트 사본의 스캐폴드 · 좌표 지도가 정본으로 지은 것과 같다(지문 %s) — 바꾸지 않았다" % 새지문)
        return 0
    print("키트 사본과 다르다: %s" % " / ".join(다른))
    if "--보기" in 깃발:
        print("--보기 — 키트 사본은 그대로다")
        return 1
    if 보관이름 and os.path.exists(옛틀):
        보관곳 = os.path.join(키트, "보관", "스캐폴드_%s_%s" % (datetime.date.today().strftime("%Y%m%d"), 보관이름))
        if os.path.exists(보관곳):
            raise SystemExit("보관할 곳이 이미 있다: %s" % 보관곳)
        os.makedirs(보관곳)
        for 이름 in (틀이름, 지도이름):
            if os.path.exists(os.path.join(키트, 이름)):
                shutil.move(os.path.join(키트, 이름), os.path.join(보관곳, 이름))
        print("지금 것을 옮겨 두었다: %s (키트/보관/읽어두기.md 에 한 줄 적는다)" % 보관곳)
    shutil.copy(새틀, 옛틀)
    shutil.copy(새지도, 옛지도)
    if 보강확인(키트, 옛틀, 옛지도):
        return 1
    print("키트 사본에 넣었다 — 지문 %s. 키트의 시험(_좌표시험 · _v14시험 · 회귀)과 생성기 시험 1 을 다시 돌린다" % 새지문)
    return 0


def 보강확인(키트, 틀, 지도):
    """놓은 스캐폴드 · 좌표 지도에 키트의 `좌표.py --확인`(짝 — 지문 · 구조 · 줄 이름)을 돌린다 → 0(통과) · 1."""
    환경 = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1")
    환경.pop("DCF_좌표지도", None)      # 지도는 그 스캐폴드 곁의 것을 읽는다
    환경.pop("DCF_MAP", None)
    for 명령 in (["좌표.py", "--확인", 틀],):
        r = subprocess.run([sys.executable, os.path.join(키트, "스크립트", 명령[0])] + 명령[1:], cwd=키트, capture_output=True,
                           text=True, encoding="utf-8", errors="replace", env=환경)
        print("%s → 종료 코드 %d · %s" % (명령[0], r.returncode, " / ".join(x.strip() for x in (r.stdout + r.stderr).strip().split("\n")[-3:])[:600]))
        if r.returncode:
            print("스캐폴드 · 좌표 지도를 놓았으나 %s 가 통과하지 못했다 — 위의 글을 본다" % 명령[0])
            return 1
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv[1:]))

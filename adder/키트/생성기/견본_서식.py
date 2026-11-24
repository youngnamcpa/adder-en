# -*- coding: utf-8 -*-
"""견본_서식 — 납품 배치 · 표준 서식 길로 지은 워크북에 닻 하나를 부어 「값이 든 모양」의 견본을 낸다.

쓰기:  python 견본_서식.py <낼 xlsx> [--명세 <폴더>] [--닻 예시] [--pdf]

  1. 납품 배치(배치_납품.py)로 짓는다 — 서식길 「표준」.
  2. 얼려 둔 닻의 값(서식재료/부음_<닻>.json)을 좌표 지도 거쳐 붓는다(시험 11 과 같은 재료).
  3. 서식마감(안 쓰는 예측 열 접기 · 시나리오 세 줄 접기 · 바닥글).
  4. 따로 띄운 엑셀로 재계산하고 쪽 나눔을 맞춰(쪽나눔.py) 저장한다(캐시 값 · 줄바꿈한 줄의 높이가 파일에 남는다).
     --pdf 면 같은 이름의 pdf 도 낸다(쪽 배치 확인용).
  5. 서식 점검(서식점검.py)을 돌려 갈래별 수를 찍고 <낼 xlsx 이름>_점검.json 으로 낸다.
곁에 <이름>_빈틀.xlsx(값을 붓기 전) · <이름>_지도.json(좌표 지도)도 둔다.
엑셀은 DispatchEx 로 따로 띄운 것만 쓰고, 이 스크립트가 띄운 것만 끝낸다.
"""
import os
import sys
import json

import 짓기 as 짓기모듈
import 배치_납품
import 서식마감
import 서식점검
import 쪽나눔
from 공통 import 배치오류
from 엑셀재계산 import 거듭

여기 = os.path.dirname(os.path.abspath(__file__))


def 엑셀로내기(읽을, 낼, pdf=None, 나눔=None):
    """따로 띄운 엑셀로 다시 계산해 저장한다. pdf 를 주면 통합 문서 전체를 pdf 로도 낸다. → 쪽 수(시트마다) | None

    저장하기 전에 쪽 나눔을 맞춘다(쪽나눔.py — 구획이 쪽 사이에서 갈리지 않게 구획머리 앞으로 당긴다).
    나눔 에 dict 를 주면 넣은 쪽 나눔({시트 이름: [행 번호 …]})을 거기에 담는다."""
    import win32com.client
    읽을, 낼 = os.path.abspath(읽을), os.path.abspath(낼)
    쪽 = None
    엑셀 = win32com.client.DispatchEx("Excel.Application")      # 따로 띄운 엑셀
    try:
        엑셀.Visible = False
        엑셀.DisplayAlerts = False
        엑셀.AskToUpdateLinks = False
        엑셀.EnableEvents = False
        책 = 거듭(lambda: 엑셀.Workbooks.Open(읽을, UpdateLinks=0, ReadOnly=True))
        try:
            거듭(엑셀.CalculateFullRebuild)
            넣은 = 쪽나눔.맞추기(엑셀, 책)
            if 나눔 is not None:
                나눔.update(넣은)
            if os.path.exists(낼):
                os.remove(낼)
            책.SaveAs(낼, FileFormat=51)
            if pdf:
                pdf = os.path.abspath(pdf)
                if os.path.exists(pdf):
                    os.remove(pdf)
                책.ExportAsFixedFormat(0, pdf)                 # 0 = pdf
                쪽 = {}
                for i in range(1, 책.Worksheets.Count + 1):   # 쪽 수는 내보낸 뒤에, 시트를 앞에 세워 놓고 읽는다(앞에 서 보지 않은 시트는 쪽 나눔이 덜 세어진다)
                    ws = 책.Worksheets(i)
                    try:
                        ws.Activate()
                        쪽[ws.Name] = int(ws.PageSetup.Pages.Count)
                    except Exception:                          # noqa: BLE001 — 프린터가 없으면 쪽 수를 못 읽는다
                        쪽[ws.Name] = None
        finally:
            책.Close(SaveChanges=False)                         # 내가 연 것만 닫는다
    finally:
        엑셀.Quit()                                             # 내가 띄운 엑셀만 끝낸다
        del 엑셀
    return 쪽


def main(인자):
    def 뒤(깃발, 기본):
        return 인자[인자.index(깃발) + 1] if 깃발 in 인자 else 기본
    자리 = [a for i, a in enumerate(인자) if not a.startswith("--") and (i == 0 or 인자[i - 1] not in ("--명세", "--닻"))]
    if len(자리) != 1:
        raise SystemExit(__doc__)
    낼 = os.path.abspath(자리[0])
    명세곳 = 뒤("--명세", os.path.join(여기, "줄명세"))
    닻 = 뒤("--닻", "예시")
    재료 = os.path.join(여기, "서식재료", "부음_%s.json" % 닻)
    if not os.path.exists(재료):
        print("얼려 둔 재료가 없다: %s (python 시험_11_서식길.py --재료뜨기 <키트 폴더> --닻 %s)" % (재료, 닻))
        return 2
    os.makedirs(os.path.dirname(낼), exist_ok=True)
    머리 = os.path.splitext(낼)[0]
    빈틀, 지도, 부은, 마감본 = 머리 + "_빈틀.xlsx", 머리 + "_지도.json", 머리 + "_부음_임시.xlsx", 머리 + "_마감_임시.xlsx"
    try:
        명, 덧 = 배치_납품.명세읽기(명세곳)
        배 = 배치_납품.납품배치(명)
        지은 = 짓기모듈.짓기(명, 배, 빈틀, 지도)
    except 배치오류 as e:
        짓기모듈.알림찍기(e.오류목록, "오류", 보기=8)
        return 1
    위험 = [w for w in 지은["경고"] if w["종류"] in 짓기모듈.위험경고]
    print("지었다: %s — 시트 %d장 · 서식길 %s · 경고 %d건(위험 %d건)" % (빈틀, len(배["시트"]), 배["서식길"], len(지은["경고"]), len(위험)))
    from 시험_11_서식길 import 재료붓기
    쓴, 건너뜀 = 재료붓기(빈틀, 지도, 재료, 부은)
    print("부었다: 닻 「%s」 — 쓴 칸 %d · 건너뛴 칸 %d" % (닻, 쓴, len(건너뜀)))
    마 = 서식마감.마감(부은, 지도, 마감본)
    print("서식마감: 서식 없는 칸 %d · 날짜 서식을 맞춘 칸 %d · 접은 예측 열 %s · 시나리오 세 줄 접음 %d / 폄 %d · 연도별 WACC 줄 %s · 바닥글 「%s」" % (
        len(마["서식 없는 칸"]), len(마["날짜 서식을 맞춘 칸"]), next(iter(마["접은 열"].values()), "없음"), 마["접은 묶음"], 마["편 묶음"],
        마["연도별 WACC 줄"] or "묶음 없음", 마["바닥글"]))
    나눔 = {}
    쪽 = 엑셀로내기(마감본, 낼, 머리 + ".pdf" if "--pdf" in 인자 else None, 나눔)
    for p in (부은, 마감본):
        os.remove(p)
    print("엑셀로 재계산해 냈다: %s%s" % (낼, " · pdf 쪽 수 %s" % (쪽,) if 쪽 else ""))
    print("쪽 나눔을 넣은 곳(그 행 앞): %s" % (" · ".join("%s %s" % (k, ",".join(map(str, v))) for k, v in 나눔.items()) or "없음"))
    결 = 서식점검.점검(낼)
    서식점검.찍기(결, 보기=3)
    with open(머리 + "_점검.json", "w", encoding="utf-8", newline="\n") as f:
        json.dump(결, f, ensure_ascii=False, indent=1)
        f.write("\n")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv[1:]))

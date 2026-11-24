# -*- coding: utf-8 -*-
"""시험공통 — 시험이 함께 쓰는 경로와 길(xlsx → 칸 단위 명세 → 열 ID 명세 → 줄 무늬 명세 → 읽기).

시험은 늘 산출/ 아래에 뽑는다. 정본(줄명세/)은 건드리지 않는다 — 줄명세/ 를 스캐폴드에서 새로 뽑는 일은
「python 줄명세뽑기.py」 로만 한다.
"""
import os
import json
import shutil

import openpyxl

import 명세추출
import 열표
import 줄무늬
import 짓기 as 짓기모듈
from 대조도구 import 값대조, 시나리오바꾸기, 시나리오들

여기 = os.path.dirname(os.path.abspath(__file__))
산출 = os.path.join(여기, "산출")
정본 = os.path.join(여기, "줄명세")                      # 정본 — 시험은 읽기만 한다
스캐폴드명세 = os.path.join(산출, "줄명세_스캐폴드")       # 시험 1 이 스캐폴드에서 뽑아 두는 줄 무늬 명세(시험 3·4·5·7·8 이 쓴다)
스캐폴드칸명세 = os.path.join(산출, "명세_스캐폴드")
키트 = os.path.normpath(os.path.join(여기, "..", "키트"))
# 시험이 「옛 스캐폴드」로 읽는 것은 걷기 전(v12 배치)의 스캐폴드다. 산식 개편 W1 에서 줄을 지운 뒤로 키트 사본의 스캐폴드는
# 정본(줄명세/)으로 지은 것이라 거기서 명세를 뽑을 수 없다(행 ID 가 자리 순서로 다시 매겨진다). 옛 스캐폴드와 그 좌표 지도는
# 키트의 보관/ 에, 걷기 전 키트가 그 스캐폴드에 부어 둔 예시 두 벌은 옛판/ 에 얼려 두었다 — 시험의 기대값이 정본을 고쳐도 흔들리지 않는다
옛배치 = os.path.join(키트, "보관", "스캐폴드_20261002_걷기전")
스캐폴드 = os.path.join(옛배치, "DCF_워크북_스캐폴드.xlsx")
옛지도 = os.path.join(옛배치, "DCF_워크북_좌표지도.json")
키트스캐폴드 = os.path.join(키트, "DCF_워크북_스캐폴드.xlsx")      # 정본(줄명세/)으로 지어 키트 사본에 넣은 것 — 시험 1 ⑩ 이 정본과 견준다
키트지도 = os.path.join(키트, "DCF_워크북_좌표지도.json")
옛판 = os.path.join(여기, "옛판")
# 새 시트 두 장(14 · 15번)의 명세도 옛 스캐폴드와 짝인 것을 얼려 두었다(옛판/새시트/ — 이름을 입히기 전의 새시트/). 정본의 줄 이름을
# 고치면(L1 이름 입히기) 새시트/ 의 덧붙인 이름이 새 이름이 되어 옛 스캐폴드에서 뽑은 명세(옛 이름)와 맞지 않는다.
# 옛 스캐폴드의 명세로 짓는 시험(2 · 3 · 5 · 8 · 9 · 10)은 이것을 읽고, 정본과 짝인 새시트/ 는 시험 1 ⑧ 만 읽는다
얼린새시트 = [os.path.join(옛판, "새시트", "S14.jsonl"), os.path.join(옛판, "새시트", "S15.jsonl")]
하이닉스 =r"C:\Users\Public\제출작업\패키지\김영남_DCF원고_검토자료\03_실습파일\SK하이닉스_DCF.xlsx"
가정_하이닉스 = os.path.normpath(os.path.join(여기, "..", "회차_하이닉스", "가정_하이닉스.json"))
예시들 = ["가정_예시", "가정_예시_v14"]


def 부은예시(이름, 다시=False):
    """키트 예시 가정을 부은 워크북(옛판/부은_<이름>.xlsx) — 걷기 전 키트의 붓기가 걷기 전 스캐폴드에 부어 둔 것을 얼려 둔 시험 재료다.

    예전에는 없으면 지금 키트의 붓기로 부었다. 지금 키트의 엔진은 키트 뿌리의 예시 가정(증설 블록 · 물리층 스트림)을 오류로 멈추고
    지금 붓기는 옛 배치의 줄 일부를 붓지 않는다 — 그래서 다시 붓지 않는다(`다시` 는 쓰지 않는다)."""
    낼 = os.path.join(옛판, "부은_%s.xlsx" % 이름)
    if not os.path.exists(낼):
        raise SystemExit("얼려 둔 부은 예시가 없다: %s (옛판/읽어두기.md)" % 낼)
    return 낼


def 대상들():
    """시험 2·4 의 대상 워크북: (이름, 경로)."""
    return [("하이닉스", 하이닉스)] + [(이름.replace("가정_", ""), 부은예시(이름)) for 이름 in 예시들]


def 명세만들기(xlsx, 이름, 시트표=None):
    """xlsx → 칸 단위 명세 → 열 ID 명세 → 줄 무늬 명세. → {"칸폴더","줄폴더","요약","줄요약","칸명세"(열 ID)}

    늘 산출/ 아래(명세_<이름> · 줄명세_<이름>)에 낸다. 정본(줄명세/)은 덮어쓰지 않는다.
    """
    칸폴더 = os.path.join(산출, "명세_" + 이름)
    줄폴더 = os.path.join(산출, "줄명세_" + 이름)
    if os.path.abspath(줄폴더) == os.path.abspath(정본):
        raise SystemExit("시험은 정본(줄명세/)에 쓰지 않는다")
    요약 = 명세추출.추출(xlsx, 칸폴더)
    칸 = 열표.적용(짓기모듈.칸명세읽기(칸폴더), 시트표)
    if os.path.isdir(줄폴더):
        shutil.rmtree(줄폴더)
    줄요약 = 줄무늬.쓰기(칸, 줄폴더)
    return {"칸폴더": 칸폴더, "줄폴더": 줄폴더, "요약": 요약, "줄요약": 줄요약, "칸명세": 칸}


def 스캐폴드명세확인():
    """시험 1 이 뽑아 둔 스캐폴드의 줄 무늬 명세 폴더. 없으면 멈춘다."""
    if not os.path.exists(os.path.join(스캐폴드명세, "책.json")):
        raise SystemExit("시험 1 을 먼저 돌려 둔다(산출/줄명세_스캐폴드 가 없다)")
    return 스캐폴드명세


def 구조수(경로):
    """수식 칸 · 병합 · 목록 유효성의 수 — 엑셀이 파일을 고쳐 열지 않았는지 보는 용도."""
    wb = openpyxl.load_workbook(경로)
    return {"수식": sum(1 for ws in wb for c in ws._cells.values() if c.data_type == "f"),
            "병합": sum(len(ws.merged_cells.ranges) for ws in wb),
            "유효성": sum(len(ws.data_validations.dataValidation) for ws in wb)}


def 시나리오짝(옛사본, 새, 지도, 이름):
    """시나리오 선택을 비관·낙관으로 바꾼 사본 짝 — 엑셀로 재계산할 목록과 값 대조에 쓸 경로를 돌려준다.

    → (재계산할 짝 [(읽을, 낼)], {시나리오: (옛 값 파일, 새 값 파일, 옛 수식 파일)})
    기준(파일에 든 선택)은 부르는 쪽이 이미 재계산한다. 여기서는 나머지 둘을 만든다.
    """
    os.makedirs(산출, exist_ok=True)
    wb = openpyxl.load_workbook(옛사본, read_only=True)
    지금 = wb["12. 가정_시나리오"]["D12"].value
    wb.close()
    짝, 길 = [], {}
    for 시 in 시나리오들:
        if 시 == 지금:
            continue
        옛 = os.path.join(산출, "_시나_%s_%s_옛.xlsx" % (이름, 시))
        새것 = os.path.join(산출, "_시나_%s_%s_새.xlsx" % (이름, 시))
        시나리오바꾸기(옛사본, 옛, 시)
        시나리오바꾸기(새, 새것, 시, 지도)
        옛값, 새값 = 옛.replace(".xlsx", "_재계산.xlsx"), 새것.replace(".xlsx", "_재계산.xlsx")
        짝 += [(옛, 옛값), (새것, 새값)]
        길[시] = (옛값, 새값, 옛)
    return 짝, 길, 지금


def 시나리오대조(길, 지도, 제외=(), 허용=1e-9):
    """시나리오마다 값 대조 → {시나리오: {"판정에 든 칸", "다른 칸", "글을 내는 수식 칸", "주당가치", "보기"}}"""
    결 = {}
    for 시, (옛값, 새값, 옛식) in 길.items():
        값 = 값대조(옛값, 새값, 옛식, 지도, 허용=허용, 제외=set(제외))
        wv = openpyxl.load_workbook(옛값, data_only=True)
        결[시] = {"판정에 든 칸": 값["수"].get("판정에 든 칸", 0), "견준 칸": 값["수"].get("견준 칸", 0),
                 "다른 칸": 값["수"].get("다른 칸", 0), "글을 내는 수식 칸": 값["수"].get("글을 내는 수식 칸", 0),
                 "글이 다른 칸": 값["수"].get("글을 내는 수식 칸 — 글이 다름", 0),
                 "시나리오 번호(옛 12!D13)": wv["12. 가정_시나리오"]["D13"].value,
                 "주당가치(옛 2!D68)": wv["2. DCF"]["D68"].value, "보기": (값["다른칸"] + 값["글다른칸"])[:5]}
    return 결


def 결과쓰기(이름, 결과):
    os.makedirs(산출, exist_ok=True)
    with open(os.path.join(산출, 이름), "w", encoding="utf-8") as f:
        json.dump(결과, f, ensure_ascii=False, indent=1, default=str)

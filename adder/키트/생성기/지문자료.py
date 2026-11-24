# -*- coding: utf-8 -*-
"""지문자료 — 값 대조의 판별력을 높이는 자료를 만든다(0_결정.md 합격 기준 ④).

값이 부어진 워크북은 숫자 수식의 60%가 0 이다(안 쓰는 예측 열 · 안 쓰는 제품군 · 꺼진 기능). 값이 0 인 칸의 틀린 참조는
값 대조로 안 잡힌다(원형 검증 5절). 그래서 **입력 칸마다 서로 다른 0 아닌 값**을 넣고 **예측 열을 모두 켠** 워크북을 만들어
한 번 더 대조한다. 옛 배치의 워크북과 새 배치의 워크북을 같은 자료에서 재계산해 견주므로, 값이 그럴듯할 필요는 없다 —
서로 달라서 한 칸 어긋난 참조가 값의 차이로 드러나면 된다.

  · 숫자를 받는 입력 칸(줄의 「입력」 구간 가운데 실적·예측·영구·값 열)에 값을 넣는다. 줄의 「서식」으로 크기를 고른다:
      비율·비율2·포인트   옛 값(없거나 0 이면 0.01) + 0.00001 × 순번
      금액·금액1·주당·인원·주식수   옛 값(없거나 0 이면 1,000) + 순번
      베타·계수·연수·일수·배수     옛 값(없거나 0 이면 1) + 0.0001 × 순번
    서식이 없는 시나리오 줄(가정 머리 줄 아래 세 줄)은 머리 줄의 서식을 따른다. 글·날짜·참거짓·수식이 든 입력 칸과
    서식이 「개월」·「날짜」·없음인 줄은 건드리지 않는다(선택 칸 · 열 위치 따위).
  · 기간 종료일 줄(12번 22번 줄)의 빈 예측 열에 다음 해 말일을 이어 넣고, 그 위아래 구분 줄(21·23번 줄)도 채운다.

쓰기:  python 지문자료.py <값이 부어진 옛 xlsx> <그 워크북의 줄 무늬 명세 폴더> <낼 xlsx>
"""
import sys
import os
import json
import datetime
from collections import Counter

import openpyxl

import 범위지문

_크기 = {"비율": ("비율", 0.01, 0.00001), "비율2": ("비율", 0.01, 0.00001), "포인트": ("비율", 0.01, 0.00001),
       "금액": ("금액", 1000, 1), "금액1": ("금액", 1000, 1), "주당": ("금액", 1000, 1), "인원": ("금액", 1000, 1),
       "주식수": ("금액", 1000, 1),
       "베타": ("계수", 1, 0.0001), "계수": ("계수", 1, 0.0001), "연수": ("계수", 1, 0.0001), "일수": ("계수", 1, 0.0001),
       "배수": ("계수", 1, 0.0001)}
_숫자열 = ("실적", "예측", "영구", "값")
기간시트, 종료일줄, 구분줄위, 구분줄아래 = "S12", "S12R022", "S12R021", "S12R023"


def 만들기(옛xlsx, 명세, 낼):
    """옛 배치의 워크북(값이 부어진 것)에 지문 값을 넣어 낼 에 저장한다. → 요약(수)"""
    wb = openpyxl.load_workbook(옛xlsx)
    수, k = Counter(), 0
    for sid, s in 명세["시트"].items():
        if not s.get("옛이름") or s["옛이름"] not in wb.sheetnames:
            continue
        ws = wb[s["옛이름"]]
        열글 = {c["id"]: c.get("옛") for c in s["열"]}
        종 = {c["id"]: c.get("종류") for c in s["열"]}
        줄표 = {r["id"]: r for r in s["행"]}
        머리서식 = {아래: 줄표[머리].get("서식") for 머리, 세 in 범위지문.가정묶음(s) for 아래 in 세}
        for 줄 in s["행"]:
            크기 = _크기.get(줄.get("서식") or 머리서식.get(줄["id"]))
            if 크기 is None or "옛행" not in 줄:
                continue
            갈래, 기본, 걸음 = 크기
            for cid in 줄.get("입력") or ():
                if 종.get(cid) not in _숫자열 or not 열글.get(cid):
                    continue
                한 = 줄["칸"].get(cid, {})
                v = 한.get("v")
                if "f" in 한 or 한.get("t") or isinstance(v, (str, bool)):
                    수["둔 칸(수식·글·날짜)"] += 1
                    continue
                k += 1
                옛값 = v if isinstance(v, (int, float)) and v != 0 else 기본
                ws["%s%d" % (열글[cid], 줄["옛행"])].value = 옛값 + 걸음 * k
                수["값을 넣은 입력 칸"] += 1
                수["  그 가운데 비어 있었거나 0 이던 칸"] += 0 if (isinstance(v, (int, float)) and v != 0) else 1
                수["  " + 갈래] += 1
    # 예측 열을 모두 켠다 — 기간 종료일의 빈 예측 열에 다음 해 말일을 이어 넣는다
    s = 명세["시트"].get(기간시트)
    if s and s.get("옛이름") in wb.sheetnames:
        ws = wb[s["옛이름"]]
        줄표 = {r["id"]: r for r in s["행"]}
        예측열 = [c for c in s["열"] if c.get("종류") == "예측" and c.get("옛")]
        행 = 줄표[종료일줄]["옛행"]
        앞 = None
        for c in 예측열:
            칸 = ws["%s%d" % (c["옛"], 행)]
            v = 칸.value
            if v not in (None, ""):
                앞 = v
                continue
            if 앞 is None:
                continue
            날 = datetime.date.fromisoformat(str(앞)[:10]) if not isinstance(앞, (datetime.date, datetime.datetime)) else 앞
            다음 = datetime.date(날.year + 1, 12, 31)
            새 = 다음.isoformat() if isinstance(앞, str) else datetime.datetime(다음.year, 12, 31)
            칸.value = 새
            앞 = 새
            for rid, 글 in ((구분줄위, "%dE" % 다음.year), (구분줄아래, "예측")):
                if rid in 줄표 and ws["%s%d" % (c["옛"], 줄표[rid]["옛행"])].value in (None, ""):
                    ws["%s%d" % (c["옛"], 줄표[rid]["옛행"])].value = 글
            수["켠 예측 열"] += 1
    wb.save(낼)
    return dict(수)


def 판별력(값xlsx, 수식xlsx):
    """재계산한 워크북에서 숫자를 내는 수식 칸의 값 분포 — 0 인 칸이 적고 서로 다른 값이 많을수록 틀린 참조가 값으로 드러난다."""
    값 = openpyxl.load_workbook(값xlsx, data_only=True)
    식 = openpyxl.load_workbook(수식xlsx)
    수, 본 = Counter(), set()
    for ws in 식.worksheets:
        wv = 값[ws.title]
        for (r, c), 칸 in ws._cells.items():
            if 칸.data_type != "f":
                continue
            v = wv.cell(r, c).value
            수["수식 칸"] += 1
            if isinstance(v, bool):
                수["참거짓"] += 1
            elif isinstance(v, (int, float)):
                수["숫자를 내는 수식 칸"] += 1
                수["  값이 0"] += 1 if v == 0 else 0
                본.add(round(v, 9))
            elif isinstance(v, str) and v.startswith("#"):
                수["오류값을 내는 수식 칸"] += 1
            elif v in (None, ""):
                수["빈 결과"] += 1
            elif isinstance(v, str):
                수["글을 내는 수식 칸"] += 1
            else:
                수["날짜 따위"] += 1
    수["  서로 다른 숫자 값"] = len(본)
    return dict(수)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) != 4:
        raise SystemExit(__doc__)
    import 짓기
    print(json.dumps(만들기(sys.argv[1], 짓기.명세읽기(sys.argv[2]), sys.argv[3]), ensure_ascii=False, indent=1))

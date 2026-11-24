# -*- coding: utf-8 -*-
"""쪽나눔 — 구획이 쪽 사이에서 갈리지 않게 구획머리 앞에 쪽 나눔을 넣는다 (엑셀로 연 통합 문서에서 — 재계산해 저장하는 단계가 부른다).

  from 쪽나눔 import 맞추기, 구획머리줄
  머리 = 구획머리줄(xlsx 경로)       # {시트 이름: [구획머리의 행 번호 …]} — 파일에서(openpyxl) 한 번에 읽는다
  넣은 = 맞추기(엑셀, 책, 머리)      # 엑셀 = 따로 띄운 Excel.Application, 책 = 그 안에서 연 Workbook(COM). → {시트 이름: [넣은 행 번호 …]}

한 쪽에 드는 줄 수는 값을 부은 뒤에야 정해진다 — 접은 예측 열에 따라 폭 1쪽 맞춤의 배율이 달라지고, 접은 줄과 줄바꿈한 긴 글의 줄 높이가
쪽마다 드는 줄 수를 바꾼다. 줄 높이는 엑셀이 열 때 정하는 값이라 파일만 보고는 쪽을 셈할 수 없다. 그래서 엑셀이 스스로 나눈 자리(자동 쪽 나눔)를 읽어,
그 자리가 구획 한가운데면 그 구획의 구획머리 앞으로 당긴다.

  · 자동 쪽 나눔이 구획머리(명명 스타일 「글_구획」)에서 떨어지면 그대로 둔다.
  · 구획 한가운데에서 떨어지고 그 구획이 그 쪽의 중간에서 시작했으면 — 구획이 한 쪽에 드는 높이이거나, 그 쪽에 남은 줄이 머리 몇 줄뿐이면 —
    구획머리 앞에 손 쪽 나눔을 넣는다(구획이 다음 쪽의 처음부터 놓인다).
  · 한 쪽보다 긴 구획이 쪽의 처음에서 시작했으면 그대로 흘려 보낸다.
  · 손 쪽 나눔(배치가 준 것)은 건드리지 않는다.

빠르게(W6d — W8a 차: 쪽 나눔이 마감 시간의 대부분이었다. 시간의 거의 다는 구획머리를 찾느라 인쇄 영역의 줄마다 세 칸씩 COM 으로 스타일을
묻는 데 들었다 — 설비동인형 예시 1,600줄 × 3칸)
  ① 구획머리는 파일에서 한 번에 읽는다(구획머리줄 — openpyxl, 몇 초)
  ② 쪽 나눔을 넣는 동안 Application.PrintCommunication = False(프린터 드라이버와 주고받지 않는다 — 끝에 True)
  줄 높이로 쪽을 흉내 내 한꺼번에 넣는 길도 재 보았으나 줄 높이를 줄마다 COM 으로 묻는 것이 더 느렸다(줄당 10~40ms) — 넣을 자리가 있을 때만
  한 번에 하나씩 넣고 다시 읽는 옛 길을 그대로 쓴다
수식과 값은 건드리지 않는다. 엑셀을 띄우거나 닫지 않는다(부른 쪽의 것을 쓴다).
"""
구획스타일 = "글_구획"
자동, 손 = -4105, -4135            # xlPageBreakAutomatic · xlPageBreakManual
머리줄수 = 4                       # 구획머리 + 머리 줄 + 두 줄 — 쪽 끝에 이만큼도 못 남으면 구획을 다음 쪽으로 넘긴다
되풀이한도 = 60


def 구획머리줄(경로):
    """xlsx 파일의 시트마다 구획머리(A~C 열 가운데 명명 스타일 「글_구획」인 칸이 있는 행) — {시트 이름: [행 번호 …]}."""
    import openpyxl                                   # noqa: PLC0415
    wb = openpyxl.load_workbook(경로)
    낸 = {}
    for ws in wb.worksheets:
        줄 = set()
        for row in ws.iter_rows(min_col=1, max_col=3):
            for c in row:
                if c.style == 구획스타일:
                    줄.add(c.row)
                    break
        낸[ws.title] = sorted(줄)
    return 낸


def _구획머리인가(ws, r):
    for c in (1, 2, 3):
        try:
            if ws.Cells(r, c).Style.Name == 구획스타일:
                return True
        except Exception:                          # noqa: BLE001 — 병합 칸 따위
            continue
    return False


def _나눔들(ws):
    """[(그 줄에서 새 쪽이 시작하는 행 번호, 손인가)] — 위에서부터."""
    낸 = []
    for k in range(1, ws.HPageBreaks.Count + 1):
        b = ws.HPageBreaks(k)
        낸.append((int(b.Location.Row), int(b.Type) == 손))
    return sorted(낸)


def _높이(ws, a, z):
    return float(ws.Range(ws.Rows(a), ws.Rows(z)).Height) if z >= a else 0.0


def 시트맞추기(엑셀, ws, 머리줄=None):
    """한 시트 — 넣은 쪽 나눔(구획머리의 행 번호) 목록. 머리줄: 구획머리의 행 번호(없으면 칸마다 스타일을 묻는다 — 느리다)."""
    영역 = ws.PageSetup.PrintArea
    if not 영역:
        return []
    범 = ws.Range(영역)
    첫, 끝 = int(범.Row), int(범.Row + 범.Rows.Count - 1)
    제목 = ws.PageSetup.PrintTitleRows
    몸첫 = (int(ws.Range(제목).Row + ws.Range(제목).Rows.Count) if 제목 else 첫)
    if 머리줄 is None:
        머리 = [r for r in range(몸첫, 끝 + 1) if _구획머리인가(ws, r)]
    else:
        머리 = sorted(r for r in 머리줄 if 몸첫 <= r <= 끝)
    if not 머리:
        return []
    ws.Activate()
    창 = 엑셀.ActiveWindow
    옛보기 = 창.View
    창.View = 2                                    # 쪽 나눔 미리 보기 — 자동 쪽 나눔을 끝 줄까지 읽으려면 이 보기여야 한다
    넣은 = []
    try:
        for _ in range(되풀이한도):
            나눔 = _나눔들(ws)
            바뀜 = False
            for i, (r, 손인가) in enumerate(나눔):
                if 손인가 or r in 머리 or r > 끝:
                    continue
                위 = [s for s in 머리 if s < r]
                if not 위:
                    continue
                s = 위[-1]                                       # 이 쪽 나눔이 가르는 구획의 구획머리
                쪽첫 = 나눔[i - 1][0] if i > 0 else 몸첫         # 이 쪽이 시작한 줄
                if s <= 쪽첫:
                    continue                                    # 구획이 쪽의 처음에서 시작했다 — 한 쪽보다 긴 구획이다
                다음 = next((x for x in 머리 if x > s), 끝 + 1)
                구획높이, 쪽높이, 남은 = _높이(ws, s, 다음 - 1), _높이(ws, 쪽첫, r - 1), _높이(ws, s, r - 1)
                if 구획높이 <= 쪽높이 or 남은 <= _높이(ws, s, min(s + 머리줄수 - 1, 다음 - 1)):
                    ws.HPageBreaks.Add(Before=ws.Rows(s))
                    넣은.append(s)
                    바뀜 = True
                    break                                       # 뒤의 자동 쪽 나눔이 다시 셈해진다 — 처음부터 다시 본다
            if not 바뀜:
                break
    finally:
        창.View = 옛보기
    return sorted(set(넣은))


def 맞추기(엑셀, 책, 머리줄=None):
    """통합 문서의 시트 전부 — {시트 이름: [구획머리의 행 번호 …]} (넣은 것이 없는 시트는 싣지 않는다).
    머리줄: {시트 이름: [구획머리 행 …]}(구획머리줄 — 주면 칸마다 스타일을 묻지 않는다)."""
    앞시트 = 책.ActiveSheet
    결 = {}
    try:
        엑셀.PrintCommunication = False            # 쪽 설정을 프린터 드라이버와 주고받지 않는다(끝에 되돌린다)
    except Exception:                              # noqa: BLE001 — 옛 엑셀
        pass
    try:
        for i in range(1, 책.Worksheets.Count + 1):
            ws = 책.Worksheets(i)
            넣은 = 시트맞추기(엑셀, ws, None if 머리줄 is None else 머리줄.get(ws.Name, []))
            if 넣은:
                결[ws.Name] = 넣은
    finally:
        try:
            엑셀.PrintCommunication = True
        except Exception:                          # noqa: BLE001
            pass
    앞시트.Activate()
    return 결

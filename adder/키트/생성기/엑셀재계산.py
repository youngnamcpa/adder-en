# -*- coding: utf-8 -*-
"""엑셀재계산 — 엑셀을 따로 띄워 파일을 다시 계산하고 다른 이름으로 저장한다.

DispatchEx 로 새 엑셀을 띄운다. 사용자가 쓰고 있는 엑셀에는 닿지 않는다.
이 스크립트가 연 통합문서만 닫고, 이 스크립트가 띄운 엑셀만 끝낸다. 프로세스를 죽이지 않는다.
엑셀이 바빠 호출을 거부하면(RPC_E_CALL_REJECTED) 잠깐 쉬고 다시 부른다 — 열기 · 재계산 · 시트 수 읽기 · 저장 · 닫기 · 끝내기 모두
(W1 검증의 작은 결함 10: 시험 묶음을 잇달아 돌리면 감싸지 않은 호출에서 한 번의 거부로 시험이 죽었다).

쓰기:  python 엑셀재계산.py <읽을 xlsx> <낼 xlsx> [<읽을 xlsx> <낼 xlsx> ...]
"""
import sys
import os


호출거부 = -2147418111        # RPC_E_CALL_REJECTED — 「피호출자가 호출을 거부했습니다」. 엑셀이 바쁠 때 난다(잠깐 뒤에 다시 부르면 된다)


def 거듭(부름, 번=5, 쉼=2.0):
    """엑셀이 바빠 호출을 거부하면(RPC_E_CALL_REJECTED) 잠깐 쉬고 다시 부른다. 다른 오류는 그대로 올린다."""
    import time
    for k in range(번):
        try:
            return 부름()
        except Exception as e:                                # noqa: BLE001 — pywintypes.com_error 는 엑셀이 있어야 들인다
            if getattr(e, "hresult", None) != 호출거부 or k == 번 - 1:
                raise
            time.sleep(쉼)


def 재계산(짝들):
    """짝들 = [(읽을 경로, 낼 경로), …]. 읽을 파일은 고치지 않는다(다른 이름으로 저장)."""
    import win32com.client
    결과 = []
    엑셀 = win32com.client.DispatchEx("Excel.Application")   # 따로 띄운 엑셀
    try:
        엑셀.Visible = False
        엑셀.DisplayAlerts = False
        엑셀.AskToUpdateLinks = False
        엑셀.EnableEvents = False
        for 읽, 낼 in 짝들:
            읽, 낼 = os.path.abspath(읽), os.path.abspath(낼)
            if os.path.exists(낼):
                os.remove(낼)
            책 = 거듭(lambda: 엑셀.Workbooks.Open(읽, UpdateLinks=0, ReadOnly=True))
            try:
                거듭(엑셀.CalculateFullRebuild)
                한 = {"읽은": 읽, "낸": 낼, "시트 수": 거듭(lambda: 책.Worksheets.Count)}
                거듭(lambda: 책.SaveAs(낼, FileFormat=51))      # 51 = xlsx
                결과.append(한)
            finally:
                거듭(lambda: 책.Close(SaveChanges=False))       # 내가 연 것만 닫는다
    finally:
        try:
            거듭(엑셀.Quit)                           # 내가 띄운 엑셀만 끝낸다
        finally:
            del 엑셀
    return 결과


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    인자 = sys.argv[1:]
    if not 인자 or len(인자) % 2:
        raise SystemExit(__doc__)
    for 한 in 재계산(list(zip(인자[0::2], 인자[1::2]))):
        print(한)

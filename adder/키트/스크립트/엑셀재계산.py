# -*- coding: utf-8 -*-
"""엑셀로 재계산하고 오류 칸을 훑는다.

`formulas` 라이브러리는 워크북을 통째로 다시 써서 **수식이 망가지고 시트명이 대문자로 바뀌고
서식을 잃는다.** 스캐폴드의 8,192자 초과 수식을 고친 뒤로는 엑셀이 파일을 열 수 있으므로
엑셀에게 직접 시킨다 — 수식·서식·시트명이 그대로 남는다.

같이 하는 일: 재계산 뒤 **오류 값이 든 칸**(#REF!·#NAME?·#VALUE!·#DIV/0!·#N/A 등)을 세어 낸다.
"""
import sys, os, time
sys.stdout.reconfigure(encoding='utf-8')
import win32com.client as win32
import pythoncom

경로 = os.path.abspath(sys.argv[1])
낼곳 = os.path.abspath(sys.argv[2]) if len(sys.argv) > 2 else None

# 새로 띄운 엑셀이 아직 시작 중이거나 바쁘면 첫 호출을 「피호출자가 호출을 거부했습니다」로 튕긴다(RPC_E_CALL_REJECTED ·
# RPC_E_SERVERCALL_RETRYLATER). 오래 쉬었다 띄울 때 매번 났다 — 실측 2026-10-26 v14 시험: 같은 파일을 곧이어 다시 돌리면 오류 칸 0.
# 이 두 응답만 잠깐 쉬었다 다시 부른다. DispatchEx 로 띄운 이 도구의 인스턴스에만 닿는다(사용자가 연 엑셀은 건드리지 않는다)
바쁨 = (-2147418111, -2147417846)


def 부르기(일, 몇=40, 쉼=0.5):
    for i in range(몇):
        try:
            return 일()
        except pythoncom.com_error as e:
            if e.args and e.args[0] in 바쁨 and i < 몇 - 1:
                time.sleep(쉼)
                continue
            raise


pythoncom.CoInitialize()
엑셀 = None
try:
    엑셀 = win32.DispatchEx('Excel.Application')
    부르기(lambda: setattr(엑셀, 'Visible', False))
    부르기(lambda: setattr(엑셀, 'DisplayAlerts', False))
    부르기(lambda: setattr(엑셀, 'AskToUpdateLinks', False))
    wb = 부르기(lambda: 엑셀.Workbooks.Open(경로, UpdateLinks=0))
    부르기(lambda: 엑셀.CalculateFullRebuild())

    오류표 = {}
    총 = 0
    for ws in wb.Worksheets:
        쓴범위 = ws.UsedRange
        try:
            칸들 = 쓴범위.SpecialCells(-4123, 16)      # xlCellTypeFormulas, xlErrors
        except Exception:
            continue                                   # 오류 칸 없음
        수 = 칸들.Count
        총 += 수
        보기 = []
        for c in 칸들:
            # **`Address` 는 바인딩에 따라 메서드이기도 하고 속성이기도 하다.**
            # 늦은 바인딩(DispatchEx)에서는 속성으로 와서 `c.Address(False, False)` 가
            # 「'str' object is not callable」로 죽는다 — **오류 칸이 있을 때만** 이 줄에
            # 닿으므로, 정작 오류를 보고해야 할 때 도구가 먼저 죽었다(실측 한화오션 3차:
            # v14 시험이 「엑셀 오류 칸」이라고만 하고 어느 칸인지 못 냈다).
            try:
                주소 = c.Address(False, False)
            except TypeError:
                주소 = str(c.Address).replace('$', '')
            보기.append('%s=%s' % (주소, c.Text))
            if len(보기) >= 6:
                break
        오류표[ws.Name] = (수, 보기)

    if 낼곳 and 낼곳 != 경로:
        wb.SaveAs(낼곳)
    else:
        wb.Save()
    wb.Close(SaveChanges=False)
    print('재계산 완료 — %s' % os.path.basename(낼곳 or 경로))
    print('오류 칸 총 %d개' % 총)
    for 시트, (수, 보기) in sorted(오류표.items(), key=lambda x: -x[1][0]):
        print('  %-24s %4d개   %s' % (시트, 수, ' · '.join(보기)))
except Exception as e:
    print('실패 — %s' % e)
    sys.exit(1)
finally:
    try:
        if 엑셀 is not None:
            엑셀.Quit()
    except Exception:
        pass
    pythoncom.CoUninitialize()

# -*- coding: utf-8 -*-
"""워크북을 텍스트로 뜬다. 셀 좌표·수식·캐시값을 한 줄씩.

사용:
  python 덤프.py 워크북.xlsx 출력.txt [--시트 "1,2"] [--수식길이 200] [--범위 A1:Z50]
  python 덤프.py 워크북.xlsx 출력.txt --검증용     # 검증 에이전트용: 수식 전문 + 캐시값 + 배경색 + 노트

`--시트` 는 **시트 번호(「12」)로 준다** — 좌표 지도(`좌표.py`)에서 지금 시트 이름을 찾는다. 이름을 그대로 줘도 되지만
시트 이름은 배치가 바뀌면 달라진다(지침과 스크립트에는 번호로 적는다).
**없는 시트를 주면 빈 파일을 내지 않고 종료 코드 2 로 멈춘다** — 예전에는 0줄 파일에 rc 0 이라 그 시트의 검증이 조용히 빠졌다.
`--범위` 는 지금 워크북의 칸 주소다 — 번호로 부르려면 `python 스크립트/좌표.py 5!B17 5!R18` 로 지금 자리를 먼저 얻는다.

**줄마다 머리에 줄 ID · 줄 이름 · 단위를 붙인다**(W7c) — `<줄 S05R011 노무비 · 백만원> B17=… | C17=…`. 줄 ID 는 좌표 지도가
그 행에 놓은 줄의 번호(시트 · 번호 — 배치가 줄을 옮겨도 번호는 그대로)이고, 이름은 그 행의 줄 이름 칸, 단위는 단위 칸의 글이다
(단위 칸이 12번 금액 단위를 부르는 수식인데 재계산 값이 없으면 12번 금액 단위 칸의 글을 쓴다). 번호 없는 행(머리 · 빈 줄)과
지도가 없는 워크북에는 머리를 붙이지 않는다. `--줄머리없이` 로 옛 꼴(칸만)을 낸다.
"""
import argparse, io, os, sys
import openpyxl

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import 산출물  # noqa: E402
from 종료코드 import 입력오류  # noqa: E402


def 줄머리표(지, wbf, wbv):
    """(시트 이름, 행) → 「<줄 S05R011 노무비 · 백만원>」 또는 None. 좌표 지도가 그 행에 놓은 줄의 번호 · 줄 이름 칸 · 단위 칸의 글."""
    import 좌표  # noqa: E402,PLC0415
    금액단위 = None
    try:                                                     # 12번 금액 단위 칸(설정 줄 6 — 단위 칸의 수식이 부르는 자리)
        금 = 지.장(wbv, "12").값("G6")
        금액단위 = ("%s" % 금).strip() if 금 not in (None, "") else None
    except (좌표.좌표오류, KeyError, ValueError):
        pass
    열표 = {}

    def 열(시번, 뜻, 기본):
        """그 시트의 이름 · 단위 열 글자 — 생성기 시트는 열ID(이름 · 단위), 옛 시트는 B · C."""
        if (시번, 뜻) not in 열표:
            열표[(시번, 뜻)] = (지.자료["시트"][지.sid(시번)].get("열ID") or {}).get(뜻) or 기본
        return 열표[(시번, 뜻)]

    def 머리(시트이름, 행):
        try:
            시번 = 지.시트번호(시트이름)
            놓 = 지.놓인줄(시번, 행)
        except (좌표.좌표오류, KeyError, ValueError):
            return None
        if not 놓:
            return None
        본, 번 = 놓
        이름칸 = "%s%d" % (열(시번, "이름", "B"), 행)
        이름 = wbv[시트이름][이름칸].value
        if 이름 is None:
            이름 = wbf[시트이름][이름칸].value
        이름 = "" if (이름 is None or ("%s" % 이름).startswith("=")) else ("%s" % 이름).strip()
        단위칸 = "%s%d" % (열(시번, "단위", "C"), 행)
        단위 = wbv[시트이름][단위칸].value
        if 단위 in (None, ""):
            식 = wbf[시트이름][단위칸].value
            if isinstance(식, str) and 식.startswith("="):     # 재계산 값이 없는 단위 수식 — 지도의 단위(「금액」이면 12번 금액 단위)
                표 = 지.단위(본) or {}
                단위 = 금액단위 if 표.get(int(번)) == "금액" else 표.get(int(번))
            else:
                단위 = 식
        단위 = ("%s" % 단위).strip() if 단위 not in (None, "") else ""
        return "<줄 S%02dR%03d%s%s>" % (int(본), int(번), (" " + 이름) if 이름 else "", (" · " + 단위) if 단위 else "")
    return 머리


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("wb")
    ap.add_argument("out")
    ap.add_argument("--시트", default=None, help="쉼표로 구분한 시트 번호(「2,9」) 또는 시트 이름 (기본: 전부)")
    ap.add_argument("--수식길이", type=int, default=0, help="수식을 N자에서 자른다 (0=자르지 않음)")
    ap.add_argument("--범위", default=None, help="예: A1:Z50 — 이 범위만 뜬다")
    ap.add_argument("--검증용", action="store_true",
                    help="수식 전문 + 배경색 + 셀 노트까지 — 검증 에이전트에게 주는 덤프")
    ap.add_argument("--줄머리없이", action="store_true", help="줄마다 붙이는 <줄 ID 이름 · 단위> 머리를 뺀다(옛 꼴)")
    a = ap.parse_args()

    try:
        wbf = openpyxl.load_workbook(a.wb)
        wbv = openpyxl.load_workbook(a.wb, data_only=True)
    except Exception as e:                                   # noqa: BLE001 — 없는 파일 · xlsx 가 아닌 파일
        sys.stderr.write("입력 오류 — 워크북을 못 열었습니다: %s (%s: %s)\n" % (a.wb, type(e).__name__, e))
        return 입력오류
    sheets = [s.strip() for s in a.시트.split(",") if s.strip()] if a.시트 else None
    import 좌표  # noqa: E402
    지 = None
    try:
        지 = 좌표.지도찾기(a.wb)
    except 좌표.좌표오류 as e:
        if sheets and any(s.isdigit() for s in sheets):      # 번호로 부르면 지도가 있어야 한다
            sys.stderr.write("좌표 오류 — %s\n" % e)
            return 입력오류
    if sheets and any(s.isdigit() for s in sheets):          # 시트 번호 → 지금 시트 이름 (좌표 지도)
        try:
            sheets = [지.시트(s) if s.isdigit() else s for s in sheets]
        except 좌표.좌표오류 as e:
            sys.stderr.write("좌표 오류 — %s\n" % e)
            return 입력오류
    줄머리 = 줄머리표(지, wbf, wbv) if (지 is not None and not a.줄머리없이) else (lambda _시트이름, _행: None)
    없는 = [s for s in (sheets or []) if s not in wbf.sheetnames]
    if 없는:                                                 # 빈 파일을 내고 rc 0 으로 끝나면 그 시트의 검증이 조용히 빠진다
        sys.stderr.write("입력 오류 — 이 워크북에 없는 시트입니다: %s (있는 시트: %s). 시트는 번호로 주십시오(--시트 9)\n"
                         % (" · ".join("「%s」" % s for s in 없는), " · ".join(wbf.sheetnames)))
        return 입력오류
    L = []
    for ws in wbf.worksheets:
        if sheets and ws.title not in sheets:
            continue
        wsv = wbv[ws.title]
        L.append("")
        L.append("################ %s  (rows=%d cols=%d) ################" % (ws.title, ws.max_row, ws.max_column))
        if a.범위:
            from openpyxl.utils import range_boundaries
            c1, r1, c2, r2 = range_boundaries(a.범위)
        else:
            c1, r1, c2, r2 = 1, 1, ws.max_column, ws.max_row
        for r in range(r1, r2 + 1):
            cells = []
            for c in range(c1, c2 + 1):
                cell = ws.cell(row=r, column=c)
                v = cell.value
                if v is None:
                    continue
                s = "%s" % v
                if a.검증용:
                    pass  # 검증용은 수식을 자르지 않는다
                elif a.수식길이 and len(s) > a.수식길이:
                    s = s[:a.수식길이] + "…(%d자)" % len(s)
                cv = wsv.cell(row=r, column=c).value
                out = "%s=%s" % (cell.coordinate, s)
                if isinstance(v, str) and v.startswith("=") and cv is not None:
                    cs = "%s" % cv
                    if len(cs) > 60:
                        cs = cs[:60] + "…"
                    out += " {%s}" % cs
                if a.검증용:
                    fill = cell.fill
                    if (fill is not None and fill.patternType and fill.fgColor is not None
                            and fill.fgColor.rgb and str(fill.fgColor.rgb) not in ("00000000",)):
                        out += " <색:%s>" % str(fill.fgColor.rgb)[-6:]
                    if cell.comment is not None:
                        note = (cell.comment.text or "").replace("\n", " ")[:80]
                        out += " <노트:%s>" % note
                cells.append(out)
            if cells:
                머리 = 줄머리(ws.title, r)
                L.append(("%s " % 머리 if 머리 else "") + " | ".join(cells))
    경로, 말 = 산출물.안전쓰기(a.out, "\n".join(L))   # 회차 규약 — 남의 덤프를 안 덮는다
    for x in 말:
        print(x)
    print("저장: %s (%d줄, 회차 「%s」)" % (경로, len(L), 산출물.회차()))
    return 0


if __name__ == "__main__":
    sys.exit(main())

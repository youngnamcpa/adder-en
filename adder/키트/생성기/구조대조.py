# -*- coding: utf-8 -*-
"""구조대조 — 지은 xlsx 의 수식이 「같은 줄 · 같은 열」을 가리키는지, 값과 무관하게 본다.

값 대조는 값이 0 이거나 빈 칸의 틀린 참조를 못 잡는다(원형 검증 5절 — 참조를 한 칸 어긋나게 한 387건 가운데
208건이 값으로는 안 잡혔다). 이 대조는 수식의 참조를 하나씩 (시트 ID, 행 ID, 열 ID, 절대 표시)로 풀어 차례대로 견준다.

  구조대조(옛 xlsx, 새 xlsx, 지도)   옛 파일의 수식 ↔ 새 파일의 수식. 참조를 뺀 나머지 글(함수 · 연산자 · 숫자 · 문자열)도 글자 그대로 같아야 한다.
  명세대조(명세, 새 xlsx, 지도)      명세의 틀 ↔ 새 파일의 수식. 옛 파일이 없는 수식(새 시트 · 명세에서 새로 적은 줄)도 본다.

범위는 두 끝만이 아니라 **범위 안의 줄 ID 목록**까지 견준다(좌표가 작은 쪽부터). 명세에서 범위의 줄을 맞바꾸거나
사이에 줄을 끼우면 두 끝의 ID 는 그대로여도 목록이 달라진다.

짓기와 다른 코드로 읽는다 — 수식은 openpyxl Tokenizer 가 아니라 정규식으로 나누고, 틀(공통.수식틀)을 쓰지 않는다.
새 좌표 → ID 는 좌표 지도의 「행」·「열ID」·「행시트」·「열맞춤」 표를 거꾸로 읽는다.

  옛 수식  '4. Sales_working'!G54      → (S04, S04R054, E1, 상대·상대)   옛 행 번호가 곧 행 ID, 옛 열 글자 → 지도의 「옛열ID」
  새 수식  '4. Sales_working'!G55      → (S04, S04R054, E1, 상대·상대)   새 행 번호 → 지도의 「행」을 거꾸로, 새 열 글자 → 「열ID」를 거꾸로
  줄이 다른 시트로 옮겨졌으면 새 수식의 시트는 놓인 시트다. 그 줄의 본 시트와 본 열 ID 로 되돌려 견준다.
  시트 머리는 「가리키는 줄이 놓인 시트가 수식이 놓인 시트와 다른가」로 견준다(같은 시트인데 일부러 붙인 머리는 그대로 있어야 한다).

범위가 일부러 넓어진 배치(범위허용 · 범위에넣기 · 틈허용 · 묶음에 열을 더함)에서는 그 범위가 「다름」으로 나온다 — 그런 배치에는 쓰지 않는다.
열 전체 · 행 전체 참조는 풀지 않는다(나머지 글로 남아 글자 그대로 견줘진다. 스캐폴드에는 없다).
"""
import re
import json
from collections import Counter

import openpyxl
from openpyxl.cell.cell import MergedCell
from openpyxl.worksheet.formula import ArrayFormula

_문자열 = re.compile(r'"(?:[^"]|"")*"')
_칸 = r"(\$?)([A-Z]{1,3})(\$?)(\d{1,7})"
_참 = re.compile(r"(?<![A-Za-z0-9_.])(?:(?:'((?:[^']|'')+)'|([A-Za-z_가-힣][A-Za-z0-9_.가-힣]*))!)?" +
                _칸 + "(?::" + _칸 + ")?" + r"(?![A-Za-z0-9_(])")
_자리 = ""
_열번호 = openpyxl.utils.column_index_from_string
_열글자 = openpyxl.utils.get_column_letter


def 수식풀기(수식):
    """수식 글 → (참조를 뺀 나머지 글, [참조 …]). 참조 = (시트 이름|None, [(열 절대, 열 글자, 행 절대, 행 번호), …])."""
    글들 = []

    def 글빼기(m):
        글들.append(m.group(0))
        return "%d" % (len(글들) - 1)

    몸 = _문자열.sub(글빼기, 수식)
    참조 = []

    def 참빼기(m):
        이름 = m.group(1).replace("''", "'") if m.group(1) is not None else m.group(2)
        끝 = [(bool(m.group(3)), m.group(4), bool(m.group(5)), int(m.group(6)))]
        if m.group(8) is not None:
            끝.append((bool(m.group(7)), m.group(8), bool(m.group(9)), int(m.group(10))))
        참조.append((이름, 끝))
        return _자리

    몸 = _참.sub(참빼기, 몸)
    몸 = re.sub("(\\d+)", lambda m: 글들[int(m.group(1))], 몸)
    return 몸, 참조


class _거꾸로:
    """좌표 지도를 거꾸로 읽는 표."""

    def __init__(self, 지도):
        self.시트 = 지도["시트"]
        self.옛이름 = 지도["옛이름"]
        self.새이름 = {s["새이름"]: sid for sid, s in self.시트.items() if s.get("새이름")}
        self.행시트 = 지도.get("행시트", {})
        self.새줄 = 지도.get("새줄", {})
        self.뺀줄 = set(지도.get("뺀줄", ()))
        self.행 = {}                        # (놓인 시트 ID, 새 행 번호) → 행 ID
        self.자리 = {}                      # 행 ID → (놓인 시트 ID, 새 행 번호)
        for rid, n in 지도["행"].items():
            놓 = self.놓인(rid)
            self.행[(놓, n)] = rid
            self.자리[rid] = (놓, n)
        self.열 = {sid: {v: k for k, v in s.get("열ID", {}).items()} for sid, s in self.시트.items()}
        self.옛열 = {sid: dict(s.get("옛열ID", {})) for sid, s in self.시트.items()}
        self.역맞춤 = {놓: {본: {v: k for k, v in 표.items()} for 본, 표 in 한.items()}
                    for 놓, 한 in (지도.get("열맞춤") or {}).items()}

    def 본(self, rid):
        """행 ID → 본 시트 ID."""
        if rid in self.새줄:
            return self.새줄[rid][0]
        m = re.match(r"([SX]\d+)R", rid)
        return m.group(1) if m else None

    def 놓인(self, rid):
        return self.행시트.get(rid) or self.본(rid)

    def 옛(self, sid, 글자, 행):
        return "%sR%03d" % (sid, 행), self.옛열[sid].get(글자, "?" + 글자)

    def 새줄ID(self, 놓, 행):
        rid = self.행.get((놓, 행))
        if rid is None:
            s = self.시트[놓]
            rid = "%sR%03d" % (놓, s["옛끝행"] + 행 - s["새끝행"]) if 행 > s["새끝행"] else "?%d" % 행
        return rid

    def 새(self, 놓, 글자, 행):
        """새 좌표(놓인 시트 · 열 글자 · 행 번호) → (행 ID, 본 시트의 열 ID)."""
        rid = self.새줄ID(놓, 행)
        cid = self.열[놓].get(글자, "?" + 글자)
        본 = self.본(rid) if not rid.startswith("?") else 놓
        if 본 is not None and 본 != 놓:
            cid = self.역맞춤.get(놓, {}).get(본, {}).get(cid, cid)
        return rid, cid


def _옛ID(참조, 현재sid, 거):
    """옛 수식의 참조 → [(본 시트 ID, 같은 시트인데 머리를 붙였나, 끝점들, 범위 안 줄 목록)]"""
    낸 = []
    for 이름, 끝 in 참조:
        sid = 거.옛이름.get(이름) if 이름 is not None else 현재sid
        if sid is None:
            낸.append(("?" + str(이름), None, tuple(끝), ()))
            continue
        끝점 = tuple(거.옛(sid, 글자, 행) + (열절, 행절) for 열절, 글자, 행절, 행 in 끝)
        줄 = ()
        if len(끝) == 2 and 끝[0][3] != 끝[1][3]:
            lo, hi = sorted((끝[0][3], 끝[1][3]))
            줄 = tuple(r for r in ("%sR%03d" % (sid, n) for n in range(lo, hi + 1)) if r not in 거.뺀줄)
        낸.append((sid, 이름 is not None and sid == 현재sid, 끝점, 줄))
    return 낸


def _새ID(참조, 놓인sid, 거, 명시=None):
    """새 수식의 참조 → 같은 꼴. 시트 머리가 기대와 다르면(붙어야 할 곳에 없거나 까닭 없이 붙었으면) 둘째 자리에 "머리 다름"."""
    낸 = []
    for i, (이름, 끝) in enumerate(참조):
        놓 = 거.새이름.get(이름) if 이름 is not None else 놓인sid
        if 놓 is None:
            낸.append(("?" + str(이름), None, tuple(끝), ()))
            continue
        끝점 = tuple(거.새(놓, 글자, 행) + (열절, 행절) for 열절, 글자, 행절, 행 in 끝)
        본 = 거.본(끝점[0][0]) if not 끝점[0][0].startswith("?") else 놓
        줄 = ()
        if len(끝) == 2 and 끝[0][3] != 끝[1][3]:
            lo, hi = sorted((끝[0][3], 끝[1][3]))
            줄 = tuple(거.새줄ID(놓, n) for n in range(lo, hi + 1))
        # 시트 머리: 다른 시트를 가리키면 붙고(이름이 곧 그 시트다), 같은 시트면 「일부러 붙인 것」일 때만 붙는다
        일부러 = 명시[i] if 명시 is not None and i < len(명시) else None
        if 이름 is not None and 놓 == 놓인sid:
            표시 = True if 일부러 else "머리 다름"       # 같은 시트인데 머리가 붙었다 — 옛 수식에서 일부러 붙인 것이어야 한다
        else:
            표시 = "머리 다름" if (일부러 and 놓 == 놓인sid) else bool(일부러)
        낸.append((본, 표시, 끝점, 줄))
    return 낸


def 구조대조(옛경로, 새경로, 지도경로, 보기수=40):
    """옛 파일과 새 파일의 수식 칸을 좌표 지도로 짝지어 참조의 ID 를 견준다. → {"수": …, "다른칸": […]}

    옛 파일에 있던 수식 칸만 본다 — 배치가 더한 새 줄·새 시트의 수식(손 수식)은 견줄 옛 수식이 없다(명세대조가 본다).
    """
    import 좌표지도
    지 = 좌표지도.읽기(지도경로)
    with open(지도경로, encoding="utf-8") as f:
        거 = _거꾸로(json.load(f))
    옛, 새 = openpyxl.load_workbook(옛경로), openpyxl.load_workbook(새경로)
    수, 다른칸 = Counter(), []
    for ws in 옛.worksheets:
        sid = 지.sid(ws.title)
        for (r, c), 칸 in ws._cells.items():
            if isinstance(칸, MergedCell) or 칸.data_type != "f":
                continue
            옛주소 = "%s%d" % (_열글자(c), r)
            새시트, 주소 = 지.새주소(ws.title, 옛주소)
            if 주소 is None:
                수["뺀 줄·열의 수식 칸"] += 1
                continue
            a, b = 칸.value, 새[새시트][주소].value
            a = a.text if isinstance(a, ArrayFormula) else a
            b = b.text if isinstance(b, ArrayFormula) else b
            수["견준 수식 칸"] += 1
            if not isinstance(b, str) or not b.startswith("="):
                수["다른 칸"] += 1
                수["다름 — 새 칸이 수식이 아니다"] += 1
                다른칸.append({"시트": ws.title, "옛칸": 옛주소, "새칸": 주소, "새시트": 새시트, "까닭": "새 칸이 수식이 아니다"})
                continue
            몸a, 참a = 수식풀기(a)
            몸b, 참b = 수식풀기(b)
            가 = _옛ID(참a, sid, 거)
            나 = _새ID(참b, 거.새이름[새시트], 거, 명시=[x[1] for x in 가])
            수["견준 참조"] += len(가)
            수["견준 범위(줄 목록)"] += sum(1 for x in 가 if x[3])
            까닭 = None
            if 몸a != 몸b:
                까닭 = "참조를 뺀 글이 다르다"
            elif [(x[0], x[2]) for x in 가] != [(x[0], x[2]) for x in 나]:
                까닭 = "참조가 가리키는 줄·열이 다르다"
            elif [x[3] for x in 가] != [x[3] for x in 나]:
                까닭 = "범위 안의 줄 목록이 다르다"
            elif any(x[1] == "머리 다름" for x in 나):
                까닭 = "시트 머리가 기대와 다르다"
            if 까닭:
                수["다른 칸"] += 1
                수["다름 — " + 까닭] += 1
                if len(다른칸) < 보기수:
                    i = next((k for k, (x, y) in enumerate(zip(가, 나)) if (x[0], x[2], x[3]) != (y[0], y[2], y[3]) or y[1] == "머리 다름"), None)
                    다른칸.append({"시트": ws.title, "옛칸": 옛주소, "새칸": 주소, "새시트": 새시트, "까닭": 까닭,
                                 "옛": str(가[i])[:300] if i is not None else a[:100],
                                 "새": str(나[i])[:300] if i is not None else b[:100]})
    수.setdefault("다른 칸", 0)
    return {"수": dict(수), "다른칸": 다른칸}


def _자리푼열(자료, 주인, rid, c):
    """명세의 틀에 자리 이름(실적.끝 · 예측.첫 · 시간.4 …)으로 적힌 열 → 좌표 지도의 묶음에서 푼 열 ID. 풀 수 없으면 None(열은 안 본다)."""
    from 공통 import 자리풀기, 자리열
    자 = 자리풀기(c)
    if not 자:
        return c
    sid = 주인.get(rid)
    if sid is None or rid in (자료.get("행시트") or {}):
        return None
    return 자리열((자료["시트"].get(sid) or {}).get("묶음", {}).get(자[0]) or [], 자[1])


def 명세대조(명세, 새경로, 지도경로, 보기수=40):
    """명세의 틀과 지은 파일의 수식을 견준다 — 수식 칸마다 참조의 (행 ID, 열 ID)와 범위 안의 줄 목록이 같은가.

    옛 파일 없이 본다. 명세로 새로 지은 시트(14·15번)와 명세에서 새로 적은 줄의 수식도 든다.
    배치가 끼운 새 줄(명세에 없는 줄)의 손 수식 · 열 전체/행 전체 참조 · 못 바꾸는 참조가 든 수식은 건너뛴다.
    묶음으로 적은 범위는 줄만 견준다(열은 새 배치의 묶음에서 정해진다). 자리 이름(「묶음.첫/끝/k」)은 좌표 지도의 묶음에서 열을 풀어 견준다.
    """
    import 좌표지도
    지 = 좌표지도.읽기(지도경로)
    with open(지도경로, encoding="utf-8") as f:
        자료 = json.load(f)
    거 = _거꾸로(자료)
    새 = openpyxl.load_workbook(새경로)
    순 = {sid: [r["id"] for r in s["행"]] for sid, s in 명세["시트"].items()}
    자리표 = {sid: {rid: i for i, rid in enumerate(줄)} for sid, 줄 in 순.items()}
    주인 = {rid: sid for sid, 줄 in 순.items() for rid in 줄}
    수, 다른칸 = Counter(), []
    for sid, s in 명세["시트"].items():
        if sid not in 자료["시트"]:
            continue
        for 줄 in s["행"]:
            rid = 줄["id"]
            if rid not in 자료["행"]:
                continue
            for cid, 한 in 줄["칸"].items():
                if "f" not in 한:
                    continue
                try:
                    새시트, 주소 = 지.주소(sid, rid, cid)
                except KeyError:
                    주소 = None
                if 주소 is None:
                    수["뺀 열·자리 없는 열의 수식 칸"] += 1
                    continue
                틀 = 한["f"]
                참 = [p for p in 틀 if isinstance(p, dict)]
                if any(p["k"] in ("C", "R", "x") for p in 참):
                    수["건너뛴 칸(열 전체·행 전체·못 바꾸는 참조)"] += 1
                    continue
                참 = [p for p in 참 if p["k"] in ("c", "r")]
                b = 새[새시트][주소].value
                b = b.text if isinstance(b, ArrayFormula) else b
                수["견준 수식 칸"] += 1
                if not isinstance(b, str) or not b.startswith("="):
                    수["다른 칸"] += 1
                    다른칸.append({"줄": rid, "열": cid, "새칸": "%s!%s" % (새시트, 주소), "까닭": "새 칸이 수식이 아니다"})
                    continue
                _, 참b = 수식풀기(b)
                놓 = 거.새이름[새시트]
                나 = _새ID(참b, 놓, 거)
                까닭 = None
                if len(참) != len(나):
                    까닭 = "참조의 수가 다르다(명세 %d · 지은 수식 %d)" % (len(참), len(나))
                else:
                    for p, y in zip(참, 나):
                        끝 = [(p["r"], p["c"])] + ([(p["r2"], p["c2"])] if p["k"] == "r" else [])
                        if p["k"] == "r" and p["r"] == p["r2"] and len(y[2]) == 1:
                            끝 = 끝[:1]             # 묶음에 열이 하나뿐이면 범위가 칸 하나로 적힌다
                        끝 = [(r, _자리푼열(자료, 주인, r, c)) for r, c in 끝]
                        열안봄 = bool(p.get("g")) or any(c is None for _, c in 끝)
                        if len(끝) != len(y[2]) or any(a[0] != b2[0] or (not 열안봄 and a[1] != b2[1]) for a, b2 in zip(끝, y[2])):
                            까닭 = "참조가 가리키는 줄·열이 다르다: 명세 %s ↔ 지은 수식 %s" % (끝, [x[:2] for x in y[2]])
                            break
                        if p["k"] == "r" and p["r"] != p["r2"]:
                            본 = 주인.get(p["r"])
                            if 본 is None or 주인.get(p["r2"]) != 본:
                                continue
                            lo, hi = sorted((자리표[본][p["r"]], 자리표[본][p["r2"]]))
                            기대 = tuple(r for r in 순[본][lo:hi + 1] if r not in 거.뺀줄)
                            수["견준 범위(줄 목록)"] += 1
                            if 기대 != y[3]:
                                까닭 = "범위 안의 줄 목록이 다르다: 명세 %s… ↔ 지은 수식 %s…" % (list(기대[:6]), list(y[3][:6]))
                                break
                수["견준 참조"] += len(참)
                if 까닭:
                    수["다른 칸"] += 1
                    if len(다른칸) < 보기수:
                        다른칸.append({"줄": rid, "열": cid, "새칸": "%s!%s" % (새시트, 주소), "까닭": 까닭, "수식": b[:120]})
    수.setdefault("다른 칸", 0)
    return {"수": dict(수), "다른칸": 다른칸}


def _어긋내기(수식, 방향):
    """수식의 첫 참조(문자열 상수 밖)를 한 줄 아래("줄") 또는 한 열 오른쪽("열")으로 민 수식. 참조가 없으면 None."""
    글들 = []

    def 글빼기(m):
        글들.append(m.group(0))
        return "%d" % (len(글들) - 1)      # 문자열 상수의 자리표시(사용자 영역 글자로 싼 번호)

    몸 = _문자열.sub(글빼기, 수식)
    m = _참.search(몸)
    if not m:
        return None
    열, 행 = m.group(4), int(m.group(6))
    if 방향 == "줄":
        행 += 1
    else:
        열 = _열글자(_열번호(열) + 1)
    a, b = m.span(4)[0], m.span(6)[1]
    몸 = 몸[:a] + "%s%s%d" % (열, m.group(5), 행) + 몸[b:]
    return re.sub("(\\d+)", lambda x: 글들[int(x.group(1))], 몸)


def 돌연변이시험(옛경로, 새경로, 지도경로, 임시경로, 건수=40):
    """구조대조가 눈을 뜨고 있는가 — 새 파일의 수식 칸 몇 곳에서 참조 하나를 한 줄·한 열 어긋나게 고친 뒤 견준다.

    옛 파일의 수식 칸에 대응하는 새 칸 가운데 고른다(고른 차례는 늘 같다). 고친 칸은 값이 0 이거나 빈 칸이어도
    모두 「다름」으로 나와야 한다. → {"고친 칸", "잡은 칸", "놓친 칸": […]}
    """
    import 좌표지도
    지 = 좌표지도.읽기(지도경로)
    옛 = openpyxl.load_workbook(옛경로)
    wb = openpyxl.load_workbook(새경로)
    후보 = []
    for ws in 옛.worksheets:
        for (r, c), 칸 in sorted(ws._cells.items()):
            if 칸.data_type == "f" and isinstance(칸.value, str):
                새시트, 주소 = 지.새주소(ws.title, "%s%d" % (_열글자(c), r))
                if 주소 is not None:
                    후보.append((새시트, 주소))
    걸음 = max(1, len(후보) // 건수)
    고친 = {}
    for i, (시트, 주소) in enumerate(후보[::걸음][:건수]):
        칸 = wb[시트][주소]
        새 = _어긋내기(칸.value, "줄" if i % 2 == 0 else "열") if isinstance(칸.value, str) else None
        if 새 and 새 != 칸.value:
            고친[(시트, 주소)] = (칸.value, 새)
            칸.value = 새
    wb.save(임시경로)
    결 = 구조대조(옛경로, 임시경로, 지도경로, 보기수=10 ** 9)
    잡은 = {(d["새시트"], d["새칸"]) for d in 결["다른칸"]}
    놓친 = [{"시트": k[0], "칸": k[1], "원래": v[0][:80], "고친": v[1][:80]} for k, v in 고친.items() if k not in 잡은]
    return {"고친 칸": len(고친), "잡은 칸": len(잡은 & set(고친)), "고치지 않았는데 다르다고 한 칸": len(잡은 - set(고친)),
            "놓친 칸": 놓친[:10]}


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) != 4:
        raise SystemExit("쓰기:  python 구조대조.py <옛 xlsx> <새 xlsx> <좌표지도 json>")
    결 = 구조대조(*sys.argv[1:])
    print(json.dumps(결["수"], ensure_ascii=False, indent=1))
    for d in 결["다른칸"][:20]:
        print("  다름", d)
    sys.exit(1 if 결["수"]["다른 칸"] else 0)

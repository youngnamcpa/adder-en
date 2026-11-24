# -*- coding: utf-8 -*-
"""좌표지도 — 짓기가 낸 좌표 지도를 읽어 「옛 주소 → 새 주소」 · 「ID → 새 주소」를 답한다.

붓기·대조·자체검사처럼 워크북 파일을 직접 만지는 코드는 좌표를 글로 박지 않고 이 지도를 거친다.

  지 = 좌표지도.읽기("좌표지도.json")

  옛 주소로 부르기(원형과 같다 — 2단계 값 불변 대조 동안 쓴다)
    지.새주소("12. 가정_시나리오", "D221")   → ("12. 가정_시나리오", "E222")
    지.행("S12R030")                          → 31
    지.가정행("12", 30)                        → ("12. 가정_시나리오", 31)
    지.열("12", "D")                           → "E"
    지.수식옮기기("='4. Sales_working'!G54", "5. COGS_working")   → 새 좌표의 수식 글

  ID 로 부르기(3단계부터 쓴다 — 시트 ID · 가정 번호 · 열 ID)
    지.주소("S12", 30, "E1")                   → ("12. 가정_시나리오", "H31")
    지.주소("S12", 212, "기준")                → 시점 가정 줄의 「기준」 칸(그 줄 쓰임의 별칭)
    지.주소("S10", 28, "사유")                 → 검증 줄의 사유 칸
    지.열자리("S12", "E1")                     → "H"          지.묶음("S12", "예측") → ["H", "I", …]
    지.열ID("12", "D")                         → "H1"         (옛 열 글자 → 열 ID)
    지.번호표시("S12", 30)                     → "A-030"      (0_결정.md 2절의 접두)

  줄이 다른 시트로 옮겨진 배치
    행 ID 는 이름일 뿐이고 놓이는 시트는 배치가 정한다. 옮긴 줄은 지도의 「행시트」에 놓인 시트가 실리고,
    그 줄의 열은 「열맞춤」을 거쳐 놓인 시트의 열에 놓인다. 새주소 · 주소 · 가정행 은 **놓인 시트의 이름**을 돌려준다.
    지.놓인시트("S04R064")                     → "S15"        (옮기지 않은 줄은 본 시트)
    지.새주소("4. Sales_working", "D64")       → ("15. 검증", "D31")

지도 JSON 의 열쇠
  원형의 것(그대로 둔다): 명세 · 원본(파일 이름만) · 시트{옛이름·새이름·열·뺀열·옛끝행·새끝행·옛끝열} · 옛이름 · 행 · 뺀줄 · 새줄 · 칸
  넓힌 것: 형식(2) · 시트{열ID·옛열ID·뺀열ID·열종류·묶음·쓰임} · 행쓰임
           행시트{행 ID: 놓인 시트 ID} · 열맞춤{놓인 시트: {본 시트: {본 열 ID: 놓인 열 ID}}} — 줄을 옮긴 배치에만 있다
           가정묶음{시트 ID: [[머리 번호, [비관·기준·낙관 번호]]]} · 단위{시트 ID: {번호: 단위 글}} · 기간열[열 ID …] · 지문
           (가정묶음·단위·기간열·지문은 키트 스크립트/좌표.py 가 읽는 이름 그대로다)
  기간으로 지은 것(W2 — 짓기에 기간을 줬을 때): 열 ID 가 기간 ID 다.
           기간열[{id: 기간 ID, 구분: 실적|예측|영구, 열: 열 글자} …] · 기간{평가기준일·결산월·실적연도수·상세추정연수·수렴연수·열·묶음·자리·속성}
           시트{틀: {옛열ID: {옛 열 글자: 틀의 열 ID}, 쓰임: {쓰임: {별칭: 틀의 열 ID}}}} — 시간축 시트에만. 뺀열에 틀의 옛 열 글자(D~R)가 들어 있다
           (옛 열 글자로 부른 시간축 칸은 그 줄 쓰임의 별칭 자리로만 풀린다 — 시간축 값은 기간 ID 로 부른다)
"""
import json
import re
import hashlib

from openpyxl.utils import get_column_letter, column_index_from_string

from 공통 import 수식틀, 시트이름쓰기, 행ID, 행ID풀기, 자리풀기, 자리열

번호머리 = {"S12": "A", "S13": "H", "S03": "W"}     # 가정 · 과거 재무제표 · WACC (0_결정.md 2절)
지문이름 = "DCF_좌표지도_지문"                       # 워크북의 사용자 지정 속성 이름(키트 스크립트/좌표.py 와 같다)


def 지문(자료):
    """배치의 지문 — 시트 이름·열 자리·줄 자리가 같으면 같은 글자가 나온다.

    키트 스크립트/좌표.py 의 `지도.지문()` 과 같은 셈이다(시험 5 가 두 값을 견준다). 짓기가 워크북에 남기고,
    키트의 붓기·대조는 워크북의 지문이 곁의 좌표 지도와 다르면 멈춘다.
    줄을 다른 시트로 옮긴 배치는 「행시트」도 셈에 넣는다(옮기지 않은 배치의 지문은 전과 같다).
    """
    몸 = {"시트": {sid: [s["새이름"], sorted(s["열"].items())] for sid, s in 자료["시트"].items()},
         "행": sorted(자료["행"].items())}
    if 자료.get("행시트"):
        몸["행시트"] = sorted(자료["행시트"].items())
        몸["열맞춤"] = 자료.get("열맞춤") or {}
    글 = json.dumps(몸, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha1(글.encode("utf-8")).hexdigest()[:16]


기간지문키 = ("평가기준일", "결산월", "실적연도수", "상세추정연수", "수렴연수")
구조이름 = "_구조지문"                               # 12번 시트의 숨은 정의된 이름 — 값은 구조 지문 글(설계/6_산식_설계.md 9-5)


def 구조지문(기간, 구조, 판, 덧=None):
    """구조 지문 — 그 워크북을 지은 「기간 · 구조 · 명세의 판」이 같으면 같은 글자가 나온다(9-5).

    기간 : {평가기준일, 결산월, 실적연도수, 상세추정연수, 수렴연수} — `기간축.사전()` 의 그 다섯 값(가정 파일의 `기간` 을 기간축이 다듬은 것)
    구조 : 가정 파일의 `구조` 에 키트의 구조틀로 기본값을 채운 것(`구조펴기.키트채움` — 없으면 빈 사전. 키트의 틀로 못 읽는 구조는 적힌 그대로).
           기본값을 적든 안 적든 같은 글자가 난다. 책.json 의 「구조기본」(합성 명세의 것)은 판에 든다
    판   : 명세 지문(좌표 지도의 「명세지문」 — 축 · 구조와 무관한 명세의 지문)
    덧   : 명세의 되풀이 정의가 가정 파일에서 읽은 값({"시점가정.857": 12} — 좌표 지도의 「구조지문재료」에 경로가 실린다). 없으면 뺀다
    셈   : 위 넷을 열쇠 차례로 늘어놓은 JSON(ensure_ascii=False · 구분자 「,」「:」)의 sha1 앞 16자.
    붓기 · 대조 · 마감은 가정 파일에서 이 글자를 다시 내어 좌표 지도의 「구조지문」과 견준다 — 다르면 「구조가 바뀌었으니 다시 지으라」.
    """
    몸 = {"기간": {k: (기간 or {}).get(k) for k in 기간지문키}, "구조": 구조 or {}, "판": 판}
    if (기간 or {}).get("재무기준일") not in (None, "", (기간 or {}).get("평가기준일")):
        몸["기간"]["재무기준일"] = 기간["재무기준일"]        # 날짜 둘(2026-10-25) — 이월 판만(옛 판 지문 그대로). 키트 좌표.가정구조지문 과 같은 셈
    if 덧:
        몸["덧"] = dict(덧)
    글 = json.dumps(몸, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha1(글.encode("utf-8")).hexdigest()[:16]


def 가정구조지문(가정, 지도자료):
    """가정 사전(또는 파일 경로)에서 구조 지문을 다시 낸다 — 좌표 지도(자료)의 「명세지문」 · 「구조지문재료」를 판과 덧 경로로 쓴다.

    키트의 붓기 · 대조 · 마감이 `가정구조지문(가정, 지도) == 지도["구조지문"]` 로 견준다(기간은 기간축으로 다듬는다)."""
    import 기간열
    if isinstance(가정, str):
        with open(가정, encoding="utf-8") as f:
            가정 = json.load(f)
    축 = 기간열.축사전(가정)
    덧 = {}
    for 길 in 지도자료.get("구조지문재료") or ():
        v = 가정
        for 키 in 길.split("."):
            v = v.get(키) if isinstance(v, dict) else None
        if isinstance(v, dict) and "기준" in v:
            v = v["기준"]
        if isinstance(v, float) and float(v) == int(v):
            v = int(v)
        덧[길] = v
    import 구조펴기
    준 = 구조펴기.키트채움(가정.get("구조")) if isinstance(가정.get("구조"), dict) else {}      # 짓기가 지문에 넣는 것과 같은 사전(선언.준구조)
    return 구조지문(축, 준, 지도자료.get("명세지문"), 덧)


class 지도:
    def __init__(self, 자료):
        self.자료 = 자료
        self.시트 = 자료["시트"]
        self.옛이름 = 자료["옛이름"]          # 옛 시트 이름 → 시트 ID
        self.행자리 = 자료["행"]
        self.뺀줄 = set(자료.get("뺀줄", []))
        self.행쓰임 = 자료.get("행쓰임", {})
        self.행시트 = 자료.get("행시트", {})  # 다른 시트로 옮긴 줄 → 놓인 시트 ID
        self.열맞춤 = 자료.get("열맞춤", {})  # 놓인 시트 → {본 시트 → {본 열 ID: 놓인 열 ID}}
        self._새줄 = 자료.get("새줄", {})

    def sid(self, 시트):
        """옛 시트 이름 · 새 시트 이름 · 시트 ID · 번호('12') 어느 것으로 불러도 시트 ID 를 준다."""
        if 시트 in self.시트:
            return 시트
        if 시트 in self.옛이름:
            return self.옛이름[시트]
        if re.fullmatch(r"\d+", str(시트)) and "S%02d" % int(시트) in self.시트:
            return "S%02d" % int(시트)
        for sid, s in self.시트.items():
            if s["새이름"] == 시트:
                return sid
        raise KeyError("모르는 시트: %r" % (시트,))

    def 새시트(self, 시트):
        return self.시트[self.sid(시트)]["새이름"]

    def 본시트(self, rid):
        """행 ID → 본 시트 ID(명세에서 그 줄이 적힌 시트). 새 줄은 배치가 놓은 시트."""
        if rid in self._새줄:
            return self._새줄[rid][0]
        return 행ID풀기(rid)[0]

    def 놓인시트(self, rid):
        """행 ID → 지금 놓인 시트 ID. 옮기지 않은 줄은 본 시트."""
        return self.행시트.get(rid) or self.본시트(rid)

    def 행(self, rid):
        """행 ID → 새 행 번호(뺀 줄이면 None). 번호는 그 줄이 놓인 시트에서의 것이다."""
        if rid in self.행자리:
            return self.행자리[rid]
        if rid in self.뺀줄:
            return None
        sid, 옛 = 행ID풀기(rid)
        s = self.시트[sid]
        if 옛 > s["옛끝행"]:
            return s["새끝행"] + (옛 - s["옛끝행"])   # 등록부 밖의 줄은 끝에서 떨어진 만큼
        raise KeyError(rid)

    def 열(self, 시트, 옛열):
        """옛 열 글자 → 새 열 글자(뺀 열이면 None). 그 시트에 그대로 있는 줄의 것이다 — 옮긴 줄은 새주소 를 쓴다."""
        s = self.시트[self.sid(시트)]
        if 옛열 in s["열"]:
            return s["열"][옛열]
        if 옛열 in s["뺀열"]:
            return None
        새끝 = max(column_index_from_string(v) for v in s["열"].values())
        return get_column_letter(새끝 + column_index_from_string(옛열) - s["옛끝열"])

    def _줄열(self, rid, 본sid, 옛열=None, 열id=None):
        """줄 rid 의 열(옛 열 글자 또는 본 시트의 열 ID) → 놓인 시트에서의 새 열 글자(없으면 None)."""
        놓 = self.놓인시트(rid) if rid else 본sid
        틀 = self.시트[본sid].get("틀")
        if 옛열 is not None and 틀 and rid and 옛열 in 틀.get("옛열ID", {}):
            # 회차의 기간으로 지은 시트 — 틀의 시간축 열(옛 D~R)은 없다. 그 줄 쓰임이 그 열에 별칭을 줬으면(값 · 판정 · 비관 …) 별칭으로 푼다.
            # 별칭이 없는 줄(시간축 줄)의 옛 열 글자는 풀지 않는다 — 기간 ID 로 불러야 한다
            쓰 = self.행쓰임.get(rid)
            별 = {v: k for k, v in (틀.get("쓰임", {}).get(쓰) or {}).items()}.get(틀["옛열ID"][옛열]) if 쓰 else None
            if 별 is None:
                return None
            옛열, 열id = None, self.시트[본sid].get("쓰임", {}).get(쓰, {}).get(별)
        if 놓 == 본sid:
            return self.열(본sid, 옛열) if 옛열 is not None else self.열자리(본sid, 열id, rid)
        if 열id is None:
            열id = self.시트[본sid].get("옛열ID", {}).get(옛열)
            if 열id is None:
                return None
        else:
            열id = self._별칭풀기(본sid, 열id, rid)
        열id = self.열맞춤.get(놓, {}).get(본sid, {}).get(열id, 열id)
        return self.시트[놓].get("열ID", {}).get(열id)

    def 가정행(self, 시트, 번호):
        """가정 번호(옛 행 번호) → (그 줄이 놓인 시트의 이름, 새 행 번호)."""
        sid = self.sid(시트)
        rid = 행ID(sid, int(번호))
        return self.시트[self.놓인시트(rid)]["새이름"], self.행(rid)

    def 새주소(self, 시트, 옛칸):
        """옛 시트·옛 칸 주소 → (그 칸이 놓인 시트의 이름, 새 칸 주소). 뺀 줄·열이면 주소가 None."""
        sid = self.sid(시트)
        m = re.fullmatch(r"\$?([A-Za-z]{1,3})\$?(\d+)", 옛칸)
        rid = 행ID(sid, int(m.group(2)))
        n = self.행(rid)
        놓 = self.놓인시트(rid) if rid in self.행자리 else sid
        if n is None:
            return self.시트[놓]["새이름"], None
        g = self._줄열(rid if rid in self.행자리 else None, sid, 옛열=m.group(1).upper())
        return self.시트[놓]["새이름"], (None if g is None else "%s%d" % (g, n))

    # ── ID 로 부르기 ──
    def _별칭풀기(self, sid, 열id, 행id=None):
        """그 줄 쓰임의 별칭 → 열 ID(본 시트의 것). 열 ID 면 그대로."""
        s = self.시트[sid]
        if 열id in s.get("열ID", {}) or 열id in s.get("옛열ID", {}).values() or 열id in s.get("뺀열ID", ()):
            return 열id
        쓰임 = s.get("쓰임", {})
        쓰 = self.행쓰임.get(행id) if 행id else None
        if 쓰 and 열id in 쓰임.get(쓰, {}):
            return 쓰임[쓰][열id]
        if 행id is None:
            후보 = {m[열id] for m in 쓰임.values() if 열id in m}
            if len(후보) == 1:
                return 후보.pop()
        return 열id

    def 열자리(self, 시트, 열id, 행id=None):
        """열 ID(또는 그 줄 쓰임의 별칭 · 자리 이름 묶음.첫/끝/k) → 새 열 글자(뺀 열이면 None).

        별칭은 그 줄의 쓰임에서만 찾는다(행id 를 줬는데 그 줄의 쓰임에 없는 별칭이면 KeyError — 다른 쓰임에서 빌려 풀지 않는다).
        """
        s = self.시트[self.sid(시트)]
        표 = s.get("열ID", {})
        if 열id in 표:
            return 표[열id]
        if 열id in s.get("뺀열ID", ()):
            return None
        쓰임 = s.get("쓰임", {})
        쓰 = self.행쓰임.get(행id) if 행id else None
        if 쓰 and 열id in 쓰임.get(쓰, {}):
            return self.열자리(시트, 쓰임[쓰][열id])
        if 행id is None:
            후보 = {m[열id] for m in 쓰임.values() if 열id in m}
            if len(후보) == 1:
                return self.열자리(시트, 후보.pop())
        자 = 자리풀기(열id)      # 자리 이름 — 묶음의 몇째 열(예측.첫 · 실적.끝 · 시간.4 · 예측.끝2)
        if 자 and 자리열(s.get("묶음", {}).get(자[0]) or [], 자[1]) is not None:
            return 표[자리열(s["묶음"][자[0]], 자[1])]
        raise KeyError("모르는 열 ID: %s 의 %s%s" % (self.sid(시트), 열id, " (줄 %s 의 쓰임 %s 에 없는 별칭)" % (행id, 쓰) if 행id else ""))

    def 묶음(self, 시트, 이름):
        """묶음 이름 → 새 열 글자 목록(새 배치의 순서)."""
        s = self.시트[self.sid(시트)]
        return [s["열ID"][c] for c in s.get("묶음", {})[이름]]

    def 열ID(self, 시트, 옛열):
        """옛 열 글자 → 열 ID."""
        return self.시트[self.sid(시트)].get("옛열ID", {}).get(옛열)

    def 주소(self, 시트, 번호, 열id):
        """시트 ID(또는 이름·번호) + 가정 번호(또는 행 ID) + 열 ID → (그 줄이 놓인 시트의 이름, 새 칸 주소). 뺀 줄·열이면 None.

        시트 는 그 줄의 본 시트(명세에서 그 줄이 적힌 시트)다. 열 ID 도 본 시트의 것(또는 그 줄 쓰임의 별칭)으로 부른다.
        """
        sid = self.sid(시트)
        rid = 번호 if isinstance(번호, str) and not 번호.isdigit() else 행ID(sid, int(번호))
        n = self.행(rid)
        놓 = self.놓인시트(rid) if rid in self.행자리 else sid
        if 놓 == sid:
            g = self.열자리(sid, 열id, rid)
        else:
            g = self._줄열(rid, sid, 열id=열id)
            if g is None:
                raise KeyError("옮긴 줄 %s 의 열 %s 가 놓인 시트(%s)에 없다" % (rid, 열id, 놓))
        return self.시트[놓]["새이름"], (None if n is None or g is None else "%s%d" % (g, n))

    def 지문(self):
        return 지문(self.자료)

    def 가정묶음(self, 시트="S12"):
        """[(머리 번호, (비관 번호, 기준 번호, 낙관 번호))] — 세 시나리오 줄을 가진 가정 머리 줄(뺀 줄은 빠진다)."""
        sid = self.sid(시트)
        return [(머리, tuple(줄)) for 머리, 줄 in self.자료.get("가정묶음", {}).get(sid, [])
                if all(self.행(행ID(sid, x)) is not None for x in [머리] + list(줄))]

    def 단위(self, 시트, 번호):
        """그 줄의 단위 글(금액 단위 칸을 읽는 줄은 「금액」). 없으면 None."""
        return self.자료.get("단위", {}).get(self.sid(시트), {}).get("%d" % int(번호))

    def 번호표시(self, 시트, 번호):
        """가정 번호의 표시 글. 12번 A-030 · 13번 H-062 · 3번 W-014. 그 밖의 시트는 시트 번호를 머리로."""
        sid = self.sid(시트)
        return "%s-%03d" % (번호머리.get(sid, sid), int(번호))

    def 수식옮기기(self, 수식, 시트, 옛칸=None):
        """옛 좌표로 쓴 수식 글을 새 좌표로 옮긴다(붓기의 「수식덮기」용).

        시트 : 그 수식이 있던 옛 시트.  옛칸 : 그 수식이 있던 옛 칸 주소(줄이 다른 시트로 옮겨졌을 수 있으면 준다 —
        시트 머리를 붙일지는 수식이 지금 놓인 시트와 가리키는 줄이 놓인 시트가 같은가로 정한다).
        범위 점검은 하지 않는다 — 양 끝만 옮긴다. 뺀 줄을 가리키면 ValueError.
        """
        본 = self.sid(시트)
        현재 = 본
        if 옛칸 is not None:
            m = re.fullmatch(r"\$?([A-Za-z]{1,3})\$?(\d+)", 옛칸)
            현재 = self.놓인시트(행ID(본, int(m.group(2)))) if 행ID(본, int(m.group(2))) in self.행자리 else 본
        이름sid = dict(self.옛이름)
        글 = []
        for p in 수식틀(수식, 본, 이름sid):
            if isinstance(p, str):
                글.append(p)
                continue
            k = p["k"]
            if k in ("x", "n"):
                글.append(p.get("t") or p.get("name"))
                continue
            sid = p["s"] if k == "C" else 행ID풀기(p["r"])[0]
            if k in ("c", "r"):
                놓 = self.놓인시트(p["r"]) if p["r"] in self.행자리 else sid
                머리 = 시트이름쓰기(self.시트[놓]["새이름"]) + "!" if ((p.get("x") and sid == 본) or 놓 != 현재) else ""
                낱 = []
                for rid, cid, a in [(p["r"], p["c"], p["a"])] + ([(p["r2"], p["c2"], p["a2"])] if k == "r" else []):
                    n = self.행(rid)
                    g = self._줄열(rid if rid in self.행자리 else None, sid, 옛열=cid)
                    if n is None or g is None:
                        raise ValueError("뺀 줄·열을 가리키는 수식: %s" % 수식)
                    낱.append("%s%s%s%s" % ("$" if a[0] == "$" else "", g, "$" if a[1] == "$" else "", n))
                글.append(머리 + ":".join(낱))
                continue
            머리 = 시트이름쓰기(self.시트[sid]["새이름"]) + "!" if (p.get("x") or sid != 현재) else ""
            if k == "C":
                글.append("%s%s%s:%s%s" % (머리, "$" if p["a"] == "$" else "", self.열(sid, p["c"]),
                                         "$" if p["a2"] == "$" else "", self.열(sid, p["c2"])))
            elif k == "R":
                글.append("%s%s%s:%s%s" % (머리, "$" if p["a"] == "$" else "", self.행(p["r"]),
                                         "$" if p["a2"] == "$" else "", self.행(p["r2"])))
        return "".join(글)


def 읽기(경로):
    with open(경로, encoding="utf-8") as f:
        return 지도(json.load(f))

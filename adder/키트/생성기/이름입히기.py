# -*- coding: utf-8 -*-
"""이름입히기 — 이름표(옛 칸마다의 조치)를 줄 무늬 명세에 입힌다 (L1-가). 값은 변하지 않는다 — 글 칸과 글만 내는 띠 수식만 바꾼다.

  python 이름입히기.py                        줄명세/ 를 고친다. 다시 돌려도 같다(바뀔 것이 없으면 아무것도 쓰지 않는다)
  python 이름입히기.py --보기                 무엇을 할지만 낸다(쓰지 않는다)
  python 이름입히기.py --지도 <좌표지도.json>  지은 좌표 지도에 「이름칸」·「단위종류」를 싣는다(키트의 좌표지도보강.py 보다 먼저)
  python 이름입히기.py --대응표               선택지 대응표(../L1/선택지_대응표.json)만 다시 낸다
  덧붙임: --명세 <폴더>(기본 줄명세) · --기록 <폴더>(기본 ../L1)

읽는 것 (이름표/)
  이름표.json     옛 스캐폴드의 글 칸 3,856개마다 조치(rename · keep · drop · merge · move_to_note)와 새 이름. 준비/W0d 가 낸 것
  추가결정.json   0_결정 「추가 결정 — 이름과 표기」가 이름표보다 앞서는 이름(새 이름을 읽을 때 바꿔 읽는다)
  덧이름.json     이름표에 없거나 이름표대로 둘 수 없는 칸에 지어 준 이름 · 주석 글 · 빼는 줄 · 보류. 칸마다 까닭을 적는다.
                  「수식글」은 수식 속의 글 상수 하나를 바꾼다(그 칸의 셈은 그대로다 — 요약 시트에 보이던 안내 글 「스위치를 돌려 보십시오」)
  걷은줄.json     W1 이 지운 줄 — 이름표에 남아 있어도 건너뛴다
  단위종류.json   12번 줄의 단위 종류(비율 · 수준 · 그밖) — 단위 글을 바꾸기 전에 굳힌 것

옛 칸 → 명세의 칸
  이름표의 old_sheet · old_cell 은 걷기 전(v12) 스캐폴드의 좌표다. 행 ID 의 숫자가 그 행 번호이고(S12R030 = 12번 30행),
  열은 시트 머리의 열 등록부 「옛」(열 글자)으로 찾는다.

조치 (역할 × action)
  제목 · 구획 · 소구획 · 행이름 · 열머리 · 시나리오줄 · 점검항목 · 약어 · 약어명칭 · 범례 · 시트이름 · 총괄(이름 칸)
      rename · keep · merge 는 새 이름을 적는다(추가결정을 먼저 읽는다). drop 은 칸을 비운다.
  안내      drop 은 비운다(글도, 글만 내는 띠 수식도). move_to_note 는 덧이름의 「주석」에 적은 글을 그 칸(비고 · 설명 열)에 적는다.
            「주석」에 글이 없으면 칸을 비우고 기록의 「주석 보류」에 싣는다(표 아래 주석 줄 · 비고 자리를 세우는 묶음이 가져간다).
  단위      고정 글만 고친다(금액 단위 칸을 읽는 수식은 둔다). 「배」→ 빈칸(계수) · drop → 빈칸.
            뜻이 바뀌는 단위(년 → 개월 · 배 → %)는 값 · 서식과 함께 바꿔야 하므로 두고 보류에 적는다.
  빈값      고정 글 「n/a」는 비운다. 수식이 내는 글은 수식이라 둔다.
  근거글    스캐폴드의 안내문(「(」로 시작하는 고정 글)은 비운다.
  이번에 하지 않는 것 — 까닭과 함께 센다
      시점머리 · 머리줄이름      기간 머리 줄(W2)
      값글 · 수식속글 · 판정표시 · 보조 · 총괄(판정 칸)의 수식      글을 내는 수식은 수식이라 둔다(W6b 가 다시 짠다).
                                 다만 이름 칸의 수식(이름을 수식으로 만든 줄)은 새 이름이 있으면 고정 글로 바꾼다
      선택지                     선택 칸의 값 글자는 코드와 수식이 읽는다 — 대응표만 낸다
      검토의견                   빈 입력 칸
      「신설」                   새 줄은 뒤 묶음이 만든다
  이름표와 무관하게 거는 규칙
      안내문    12번 근거 네 열 · 시나리오 정의 줄 · 설정 값 칸의 「(…)」 꼴 고정 글은 비운다
      부제      시트마다 2행(행 ID …R002)의 이름 칸은 「대상회사 | 평가기준일 | 적용 시나리오 | (단위)」 한 줄 수식이다(배치 명세 1-2).
                이름표가 그 칸에 적은 조치(안내 drop 등)는 건너뛴다 — 규칙이 정한다
      들여      이름 앞의 빈칸 · 「· 」 머리는 떼고 줄의 「들여」(1 · 2)로 적는다
  줄 빼기   덧이름의 「뺄줄」에 적은 줄만 뺀다. 그 줄을 낱칸으로 읽는 수식이 남아 있으면 멈춘다. 범위의 끝 줄이면 범위 끝을
            안쪽의 남는 줄로 옮긴다(범위 지문은 「python 범위지문.py 승인 줄명세 --위치범위」 로 따로 승인한다).

다시 돌려도 같다 — 같은 칸을 두 번 고친 것은 처음과 끝만 견준다(순바꿈). 바뀐 칸이 없으면 명세도 기록도 쓰지 않는다.

쓰고 난 뒤
  python 줄무늬.py --다시쓰기 줄명세 --덧명세 새시트/S14.jsonl 새시트/S15.jsonl     새 시트 파일의 덧붙인 이름을 새 줄 이름으로
  python 범위지문.py 보기 줄명세 --덧명세 …  →  승인 … --위치범위                  줄을 빼서 바뀐 범위를 읽고 승인
  python 짓기.py 줄명세 같은배치 <낼 xlsx> <지도 json>  →  python 이름입히기.py --지도 <지도 json>
      지은 좌표 지도에 「이름칸」(가정 파일의 이름이 들어갈 칸과 틀) · 「단위종류」를 싣는다. **키트에 넣기 전에(좌표지도보강.py 보다 먼저)** 돌린다 —
      안 돌리면 보강이 옛 자리표시 글(제품군 N)을 찾다가 이름 칸 0곳인 지도를 만든다(붓기가 이름을 못 넣는다)
"""
import sys
import os
import re
import io
import json
from collections import OrderedDict, Counter

import 줄무늬
from 공통 import 손수식틀, 손수식쓰기, 배치오류

여기 = os.path.dirname(os.path.abspath(__file__))
정본 = os.path.join(여기, "줄명세")
표곳 = os.path.join(여기, "이름표")
기록곳 = os.path.normpath(os.path.join(여기, "..", "L1"))

탭이름 = {"S08": "8. CAPEX_working", "S09": "9. NWC_working"}      # 0_결정 3절 — 바꾸는 탭은 둘뿐이다
이름역할 = {"제목", "구획", "소구획", "행이름", "열머리", "시나리오줄", "점검항목", "약어", "약어명칭", "범례", "시트이름",
        "주석", "총괄"}
기간역할 = {"시점머리", "머리줄이름"}                                # 기간 머리 줄 — W2 가 고친다
수식역할 = {"값글", "수식속글", "판정표시", "보조", "총괄", "빈값", "점검항목"}      # 그 칸이 수식이면 두는 역할
뜻바뀌는단위 = {("년", "개월"), ("배", "%")}                         # 값 · 서식과 함께 바꿔야 하는 단위
부제줄 = "R002"
# 가정 파일의 이름(메타.스트림이름 · 원가이름)이 들어가는 줄 이름 칸 — 키트 좌표.py 의 이름자리표와 같은 자리에 1번 시트를 더했다
# (1번의 「매출 구분 N」「경비 1」 줄은 옛 스캐폴드에서 이름이 안 들어가 납품본에 자리표시가 남던 줄이다).
# (블록, 열쇠, 기본 이름 속의 자리 글, ((시트 번호, 가정 번호들), …))
# W5a — 수준 경로의 새 줄(4번 068~092 · 101~169 · 12번 273~392 · 610~659 · 13번 551~560 · 581~591)도 「매출 구분 N」 을 이름 자리로 받는다
이름자리 = tuple(
    [("스트림이름", "제품군%d" % i, "매출 구분 %d" % i,
      (("12", tuple(range(29, 78)) + tuple(range(273, 393)) + tuple(range(610, 660))),
       ("4", tuple(range(9, 53)) + tuple(range(68, 93)) + tuple(range(101, 160))),
       ("13", tuple(range(85, 92)) + tuple(range(551, 561)) + tuple(range(581, 592))),
       ("1", tuple(range(32, 60)) + (135, 150 + i, 160 + i, 170 + i, 200 + 10 * i + 6, 230 + i))))     # W6a — 1번 주요 가정 요약 · 시나리오별 · 역산의 구분 줄
     for i in range(1, 6)]
    + [("스트림이름", "기타", "기타", (("12", (70, 664, 665, 667)), ("4", (41, 42, 43, 44, 52, 90, 167)), ("13", (91,)), ("1", (156, 166))))]
    + [("원가이름", "원가항목%d" % i, "경비 %d" % i, (("12", (80, 84, 88)), ("5", (10, 13, 14)), ("1", (53, 190 + i)))) for i in range(1, 4)]
    + [("원가이름", "기타원가", "경비 4", (("12", (92,)), ("5", (15,)), ("1", (194,))))]
    # W4(2026-10-23) — 판관 원가 줄 5 · 6 · 7 의 12번 머리 줄도 이름 칸이다(구조.원가줄[5~7].이름 → 메타.원가이름 의 연구개발 · 판촉물류 ·
    # 기타판관). 예전에는 레터만 읽어 12번이 「경비 6 (매출액 대비)」 로 남았다 — 6번 계산 줄은 구조 이름인데 12번 가정 줄은 익명이라 잇지 못했다
    + [("원가이름", 열쇠, "경비 %d" % k, (("12", (번,)),)) for k, 열쇠, 번 in ((5, "연구개발", 112), (6, "판촉물류", 116), (7, "기타판관", 120))])


class 어긋남(Exception):
    pass


def _json(경로):
    with io.open(경로, encoding="utf-8") as f:
        return json.load(f, object_pairs_hook=OrderedDict)


def _json쓰기(경로, 자료, **덧):
    with io.open(경로, "w", encoding="utf-8", newline="\n") as f:
        json.dump(자료, f, ensure_ascii=False, **(덧 or {"indent": 1}))
        f.write("\n")


def _열수(글자):
    n = 0
    for ch in 글자:
        n = n * 26 + ord(ch) - 64
    return n


def _열글자(n):
    s = ""
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


def 옛칸들(글):
    """이름표의 old_cell → [(열 글자, 행 번호)]. 「신설(…)」처럼 칸이 아닌 글이면 None."""
    글 = re.sub(r"\([^()]*\)$", "", (글 or "").strip())
    낸 = []
    for 조각 in 글.split(","):
        m = re.fullmatch(r"([A-Z]{1,3})(\d+)(?::([A-Z]{1,3})(\d+))?", 조각.strip())
        if not m:
            return None
        c1, r1 = _열수(m.group(1)), int(m.group(2))
        c2, r2 = _열수(m.group(3) or m.group(1)), int(m.group(4) or m.group(2))
        낸 += [(_열글자(c), r) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)]
    return 낸


# ───────────────────────── 명세 위의 손 ─────────────────────────
class 판:
    """편 명세(줄무늬.읽기)와 그 위에서 칸을 고치는 손. 고친 것은 「바꿈」에 쌓인다."""

    def __init__(self, 폴더):
        self.폴더 = 폴더
        self.명 = 줄무늬.읽기(폴더)
        self.문 = 줄무늬.문맥만들기(self.명)
        self.시트 = self.명["시트"]
        self.탭2sid = {}
        self.옛열, self.이름열, self.단위열 = {}, {}, {}
        for sid, t in self.시트.items():
            self.탭2sid[t["이름"]] = sid
            self.옛열[sid] = {c["옛"]: c["id"] for c in t["열"] if c.get("옛")}
            self.이름열[sid] = next((c["id"] for c in t["열"] if c["종류"] == "이름"), None)
            self.단위열[sid] = next((c["id"] for c in t["열"] if c["종류"] == "단위"), None)
        for 옛, sid in (("8. CapEx_working", "S08"), ("9. WC_working", "S09")):
            self.탭2sid.setdefault(옛, sid)
        self.줄 = {줄["id"]: (sid, 줄) for sid, t in self.시트.items() for 줄 in t["행"]}
        self.바꿈 = []          # [{줄, 열, 옛, 새, 출처, 까닭}]
        self.뺀줄 = []          # [{줄, 이름, 까닭}]
        self.고친범위 = []
        self.들여고침 = []

    # 읽기
    def 지금(self, rid, cid):
        """그 칸의 지금 내용 → (갈래, 글).  갈래: 수식 · 글 · 값 · 빈."""
        sid, 줄 = self.줄[rid]
        한 = 줄["칸"].get(cid)
        if not 한 or ("f" not in 한 and "v" not in 한 and "x" not in 한):
            return "빈", None
        if "f" in 한:
            return "수식", 손수식쓰기(한["f"], cid, sid, self.문, None, False)
        if isinstance(한.get("v"), str) and "t" not in 한:
            return "글", 한["v"]
        return "값", 한.get("v")

    # 쓰기
    def _놓기(self, rid, cid, 갈래, 새, 출처, 까닭):
        sid, 줄 = self.줄[rid]
        if 줄["칸"].get(cid, {}).get("갈") == "축값":
            return False      # 생성기가 기간 축에서 적는 칸(12번의 기간 표기 · 종료일 …) — 이름표의 옛 칸(틀의 열)과 무관하다
        옛갈래, 옛 = self.지금(rid, cid)
        if (옛갈래, 옛) == (갈래, 새):
            return False
        한 = 줄["칸"].setdefault(cid, {})
        for 키 in ("f", "v", "x", "t", "배열", "열쇠"):
            한.pop(키, None)
        if 갈래 == "글":
            한["v"] = 새
        elif 갈래 == "수식":
            한["f"] = 손수식틀(새, cid, sid, self.문)
        if not 한:
            del 줄["칸"][cid]
        if cid == self.이름열[sid]:
            if 갈래 == "글":
                줄["이름"] = 새
            else:
                줄.pop("이름", None)
            self.문.행이름.pop(rid, None)
            if 갈래 == "글":
                self.문.행이름[rid] = [새]
        self.바꿈.append(OrderedDict([("줄", rid), ("열", cid), ("옛", ("=" if 옛갈래 == "수식" and not str(옛).startswith("=") else "") + ("" if 옛 is None else "%s" % 옛)),
                                    ("새", "" if 새 is None else 새), ("출처", 출처), ("까닭", 까닭)]))
        return True

    def 글(self, rid, cid, 새, 출처, 까닭=""):
        return self._놓기(rid, cid, "글", 새, 출처, 까닭)

    def 비움(self, rid, cid, 출처, 까닭=""):
        return self._놓기(rid, cid, "빈", None, 출처, 까닭)

    def 수식(self, rid, cid, 새, 출처, 까닭=""):
        return self._놓기(rid, cid, "수식", 새, 출처, 까닭)

    # 줄 빼기
    def 틀들(self):
        for sid, t in self.시트.items():
            for 줄 in t["행"]:
                for cid, 한 in 줄["칸"].items():
                    for 키 in ("f", "배열"):
                        if 키 in 한:
                            yield sid, 줄["id"], cid, 한[키]
            for v in t.get("유효성") or ():
                for 키 in ("formula1", "formula2"):
                    if 키 in v:
                        yield sid, "(유효성)", None, v[키]
            for c in t.get("조건부서식") or ():
                for f in c.get("수식") or ():
                    yield sid, "(조건부서식)", None, f

    def 줄빼기(self, 뺄):
        """뺄 = {행 ID: 까닭}. 낱칸으로 읽는 수식이 남는 줄이면 멈춘다. 범위의 끝 줄이면 범위 끝을 안쪽의 남는 줄로 옮긴다."""
        뺄 = OrderedDict((rid, 왜) for rid, 왜 in 뺄.items() if rid in self.줄)
        if not 뺄:
            return
        자리 = {}
        for sid, t in self.시트.items():
            for i, 줄 in enumerate(t["행"]):
                자리[줄["id"]] = (sid, i)

        def 안쪽(a, b):
            """범위 a:b 에서 빼는 줄을 덜어낸 새 끝 (a2, b2). 남는 줄이 없으면 None."""
            sid, i = 자리[a]
            _s, j = 자리[b]
            남는 = [줄["id"] for 줄 in self.시트[sid]["행"][i:j + 1] if 줄["id"] not in 뺄]
            return (남는[0], 남는[-1]) if 남는 else None

        걸림 = []
        for sid, 읽는줄, cid, 틀 in self.틀들():
            if 읽는줄 in 뺄:
                continue
            for x in 틀:
                if not isinstance(x, dict):
                    continue
                if x.get("k") == "c" and x["r"] in 뺄:
                    걸림.append("%s 의 %s 가 %s 를 읽는다" % (읽는줄, cid, x["r"]))
                elif x.get("k") == "r" and (x["r"] in 뺄 or x["r2"] in 뺄):
                    if x["r"] not in 자리 or x["r2"] not in 자리:
                        continue
                    새끝 = 안쪽(x["r"], x["r2"])
                    if 새끝 is None:
                        걸림.append("%s 의 %s 가 읽는 범위 %s:%s 가 통째로 빠진다" % (읽는줄, cid, x["r"], x["r2"]))
                        continue
                    if (x["r"], x["r2"]) != 새끝:
                        self.고친범위.append(OrderedDict([("읽는 줄", 읽는줄), ("열", cid), ("옛", "%s:%s" % (x["r"], x["r2"])), ("새", "%s:%s" % 새끝)]))
                        x["r"], x["r2"] = 새끝
                elif x.get("k") == "R" and (x["r"] in 뺄 or x.get("r2") in 뺄):
                    걸림.append("%s 의 %s 가 %s 행 전체를 읽는다" % (읽는줄, cid, x["r"]))
        if 걸림:
            raise 어긋남("뺄 수 없는 줄 — 그 줄을 읽는 수식이 남는다:\n  " + "\n  ".join(sorted(set(걸림))[:40]))
        for sid, t in self.시트.items():
            for 묶 in ("병합",):
                남 = []
                for g in t.get(묶) or ():
                    if g["r"] in 뺄 or g["r2"] in 뺄:
                        if g["r"] != g["r2"]:
                            # 여러 줄 병합의 끝 줄을 뺀다 — 병합을 남는 줄로 줄인다. 한 칸만 남으면 병합이 아니다
                            새끝 = 안쪽(g["r"], g["r2"]) if g["r"] in 자리 and g["r2"] in 자리 else None
                            if 새끝 is not None and not (새끝[0] == 새끝[1] and g["c"] == g["c2"]):
                                g["r"], g["r2"] = 새끝
                                남.append(g)
                        continue
                    남.append(g)
                t[묶] = 남
            for 묶 in ("유효성", "조건부서식"):
                for v in t.get(묶) or ():
                    남 = []
                    for g in v["범위"]:
                        if g["r"] in 뺄 or g["r2"] in 뺄:
                            새끝 = 안쪽(g["r"], g["r2"]) if g["r"] in 자리 and g["r2"] in 자리 else None
                            if 새끝 is None:
                                continue
                            g["r"], g["r2"] = 새끝
                        남.append(g)
                    v["범위"] = 남
                t[묶] = [v for v in (t.get(묶) or ()) if v["범위"]]
            고정 = (t.get("속성") or {}).get("틀고정") or {}
            if 고정.get("행") in 뺄:
                raise 어긋남("뺄 줄이 틀 고정의 줄이다: %s" % 고정["행"])
            for 줄 in list(t["행"]):
                if 줄["id"] in 뺄:
                    self.뺀줄.append(OrderedDict([("줄", 줄["id"]), ("이름", 줄.get("이름") or self.지금(줄["id"], self.이름열[sid])[1] or ""),
                                                ("까닭", 뺄[줄["id"]])]))
            t["행"] = [줄 for 줄 in t["행"] if 줄["id"] not in 뺄]
        for rid in 뺄:
            self.줄.pop(rid, None)
            self.문.행이름.pop(rid, None)

    def 쓰기(self):
        for t in self.시트.values():
            for 줄 in t["행"]:
                줄.pop("무늬원", None)
        return 줄무늬.쓰기(self.명, self.폴더, 지문쓰기=False)


# ───────────────────────── 이름표 읽기 ─────────────────────────
class 표:
    def __init__(self):
        self.이름표 = _json(os.path.join(표곳, "이름표.json"))
        추가 = _json(os.path.join(표곳, "추가결정.json"))
        self.추가이름 = {x["옛"]: x["새"] for x in 추가["이름"]}
        self.추가낱말 = [(x["옛"], x["새"]) for x in 추가["낱말"]]
        self.판정표시 = {k: v for k, v in 추가["판정 표시"].items() if k != "근거"}
        self.걷은 = _json(os.path.join(표곳, "걷은줄.json"))["줄"]
        덧곳 = os.path.join(표곳, "덧이름.json")
        self.덧 = _json(덧곳) if os.path.exists(덧곳) else OrderedDict()
        self.덧칸 = OrderedDict(((x["줄"], x["열"]), x) for x in self.덧.get("칸") or ())
        self.주석 = {x["uid"]: x for x in self.덧.get("주석") or ()}
        self.뺄줄 = OrderedDict((x["줄"], x["까닭"]) for x in self.덧.get("뺄줄") or ())
        self.보류 = {x["uid"]: x["까닭"] for x in self.덧.get("보류") or ()}
        self.남길글 = {(x["줄"], x["열"]): x["까닭"] for x in self.덧.get("남길 글") or ()}
        self.수식글 = list(self.덧.get("수식글") or ())

    def 새이름(self, 글):
        """이름표의 새 이름 → 추가 결정을 거친 이름."""
        if 글 in self.추가이름:
            return 글 and self.추가이름[글]
        for 옛, 새 in self.추가낱말:
            글 = 글.replace(옛, 새)
        return 글


def _안내문인가(글):
    return isinstance(글, str) and 글.strip().startswith("(") and 글.strip().endswith(")")


def 부제글(sid):
    """2행의 한 줄 — 대상회사 | 평가기준일 | 적용 시나리오 | (단위). 12번의 평가 전제와 시나리오 선택 칸을 읽는다(배치 명세 1-2)."""
    return ('=[$S12R005]@$값&" | 평가기준일 "&TEXT([$S12R006]@$값,"yyyy-mm-dd")&" | 적용 시나리오: "&[$S12R012]@$값'
            '&" | (단위: "&[$S12R006]@$값2&", 주당 금액은 "&[$S12R007]@$값2&")"')


# ───────────────────────── 입히기 ─────────────────────────
def 입히기(폴더, 낼=print):
    """→ (판, 셈, 항목별 결과). 명세는 아직 쓰지 않는다."""
    p, t = 판(폴더), 표()
    셈 = Counter()
    결과 = []          # [(uid, 줄, 열, 처리, 덧말)]
    걷은, 뺄줄 = t.걷은, t.뺄줄
    주석보류 = []      # [(항목, 줄, 열, 옛 글, 덧이름의 주석)] — 칸은 비우고 글은 주석 줄을 세우는 묶음에 넘긴다

    def 적기(it, rid, cid, 처리, 덧말=""):
        셈[처리] += 1
        결과.append((it["uid"] if it else "", rid, cid, 처리, 덧말))

    # 1. 탭 이름
    탭바꿈 = []
    for sid, 새 in 탭이름.items():
        s = p.시트[sid]
        if s["이름"] != 새:
            탭바꿈.append((sid, s["이름"], 새))
            s["이름"] = 새
            if s.get("옛이름"):
                s["옛이름"] = 새

    # 2. 이름표의 항목
    for it in t.이름표["항목"]:
        역할, 조치 = it["role"], it["action"]
        sid = p.탭2sid.get(it["old_sheet"])
        칸들 = 옛칸들(it["old_cell"])
        if 칸들 is None or sid is None:
            적기(it, "", "", "새 줄(뒤 묶음)", it["old_cell"])
            continue
        if it["uid"] in t.보류:
            for 열글자, 행 in 칸들:
                적기(it, "%sR%03d" % (sid, 행), p.옛열[sid].get(열글자, 열글자), "보류", t.보류[it["uid"]])
            continue
        새이름 = t.새이름(it.get("new_label") or "")
        for 열글자, 행 in 칸들:
            rid = "%sR%03d" % (sid, 행)
            cid = p.옛열[sid].get(열글자)
            if rid not in p.줄:
                if rid in 걷은:
                    적기(it, rid, cid or 열글자, "걷은 줄(W1)")
                elif rid in 뺄줄:
                    적기(it, rid, cid or 열글자, "뺀 줄")
                else:
                    적기(it, rid, cid or 열글자, "명세에 없는 줄")
                continue
            if cid is None:
                적기(it, rid, 열글자, "명세에 없는 열")
                continue
            if rid in 뺄줄:
                적기(it, rid, cid, "뺀 줄")
                continue
            if (rid, cid) in t.덧칸:
                적기(it, rid, cid, "덧이름이 정함")
                continue
            갈래, 지금 = p.지금(rid, cid)
            출처 = it["uid"]
            if rid.endswith(부제줄) and cid == p.이름열[sid]:
                if 역할 == "안내" and 조치 not in ("drop",) and it["uid"] not in t.주석:
                    적기(it, rid, cid, "주석 미정", "덧이름의 「주석」에 없다")
                else:
                    if it["uid"] in t.주석:
                        주석보류.append((it, rid, cid, 지금, t.주석[it["uid"]]))
                    적기(it, rid, cid, "부제(규칙)")
            elif 역할 in 기간역할:
                적기(it, rid, cid, "기간 머리 줄(W2)")
            elif 역할 in ("선택지",):
                적기(it, rid, cid, "선택지(대응표)")
            elif 역할 == "검토의견":
                적기(it, rid, cid, "검토 의견 칸(빈 입력 칸)")
            elif 역할 == "부제":
                적기(it, rid, cid, "부제(규칙)")
            elif 역할 == "안내":
                if 조치 == "drop":
                    적기(it, rid, cid, "비움" if p.비움(rid, cid, 출처, "안내 글") else "이미 같음")
                else:                                   # move_to_note · merge — 덧이름의 「주석」이 글과 자리를 정한다
                    주 = t.주석.get(it["uid"])
                    if 주 is None:
                        적기(it, rid, cid, "주석 미정", "덧이름의 「주석」에 없다")
                    else:
                        놓을열 = 주.get("열") or cid
                        바뀜 = False
                        if not 주.get("글"):
                            주석보류.append((it, rid, cid, 지금, 주))
                        if 놓을열 != cid:
                            바뀜 |= p.비움(rid, cid, 출처, "주석으로 옮김")
                        if 주.get("글"):
                            바뀜 |= p.글(rid, 놓을열, 주["글"], 출처, "주석")
                        else:
                            바뀜 |= p.비움(rid, 놓을열, 출처, 주.get("까닭", "주석 자리 없음"))
                        적기(it, rid, cid, ("주석" if 주.get("글") else "주석 보류") if 바뀜 else "이미 같음", 주.get("까닭", ""))
            elif 역할 == "단위":
                if 조치 == "keep":
                    적기(it, rid, cid, "그대로(keep)")
                elif 갈래 == "수식":
                    적기(it, rid, cid, "수식이라 둠", "금액 단위 칸을 읽는 수식")
                elif 갈래 == "빈":
                    적기(it, rid, cid, "이미 같음")
                elif 조치 == "drop" or not 새이름:
                    적기(it, rid, cid, "비움" if p.비움(rid, cid, 출처, "단위") else "이미 같음")
                elif (지금, 새이름) in 뜻바뀌는단위:
                    적기(it, rid, cid, "보류", "뜻이 바뀌는 단위(%s → %s) — 값 · 서식과 함께 바꾼다" % (지금, 새이름))
                else:
                    적기(it, rid, cid, "입힘" if p.글(rid, cid, 새이름, 출처, "단위") else "이미 같음")
            elif 역할 == "근거글":
                if 갈래 == "글" and _안내문인가(지금):
                    적기(it, rid, cid, "비움" if p.비움(rid, cid, 출처, "근거 안내문") else "이미 같음")
                else:
                    적기(it, rid, cid, "근거 칸(가정 파일이 채운다)" if 갈래 == "빈" else "둠(%s)" % 갈래)
            elif 역할 == "빈값":
                if 갈래 == "글":
                    적기(it, rid, cid, "비움" if p.비움(rid, cid, 출처, "빈 값의 글") else "이미 같음")
                else:
                    적기(it, rid, cid, "수식이라 둠" if 갈래 == "수식" else "이미 같음")
            elif 갈래 == "수식" and 역할 in 수식역할 and not (cid == p.이름열[sid] and 역할 in 이름역할 and 새이름 and 조치 != "drop"):
                적기(it, rid, cid, "수식이라 둠")
            elif 역할 in 이름역할:
                if 조치 == "drop":
                    적기(it, rid, cid, "비움" if p.비움(rid, cid, 출처, "이름표 drop") else "이미 같음")
                elif 새이름:
                    if 갈래 == "빈" and rid not in 걷은 and not p.지금(rid, cid)[1]:
                        # 빈 칸에는 새 이름을 얹지 않는다 — 이름표를 쓴 뒤에 W1 이 비운 이름 칸(4번 66행)이거나, 옛 글이 없는 칸에
                        # 이름표가 지어 둔 이름(한시적 현금흐름 머리 줄의 빈 입력 칸 · 새 열의 머리)이다. 뒤의 것은 줄 · 열을 세우는 묶음이 놓는다
                        적기(it, rid, cid, "빈 칸(새 이름을 얹지 않음)",
                           "W1 이 비운 칸" if (it.get("old") or "").strip() else "옛 글이 없는 칸 — 줄 · 열을 세우는 묶음이 이름을 놓는다")
                    else:
                        적기(it, rid, cid, "입힘" if p.글(rid, cid, 새이름, 출처, 조치) else "이미 같음")
                else:
                    적기(it, rid, cid, "새 이름 없음", 조치)
            elif 역할 in ("값글", "수식속글", "판정표시", "보조"):
                if 갈래 == "글" and 조치 == "drop":
                    적기(it, rid, cid, "비움" if p.비움(rid, cid, 출처, "이름표 drop") else "이미 같음")
                elif 갈래 == "글" and _안내문인가(지금):
                    적기(it, rid, cid, "비움" if p.비움(rid, cid, 출처, "안내문") else "이미 같음")
                else:
                    적기(it, rid, cid, "둠(%s)" % 갈래, 조치)
            else:
                적기(it, rid, cid, "모르는 역할", 역할)

    # 3. 이름표와 무관하게 거는 규칙
    for sid, s in p.시트.items():
        이름열 = p.이름열[sid]
        for 줄 in list(s["행"]):
            rid = 줄["id"]
            if rid in 뺄줄:
                continue
            # 부제 — 2행의 이름 칸
            if rid.endswith(부제줄) and (rid, 이름열) not in t.덧칸:
                if p.수식(rid, 이름열, 부제글(sid), "규칙:부제", "배치 명세 1-2"):
                    셈["부제(규칙)로 고침"] += 1
            for cid in list(줄["칸"]):
                if (rid, cid) in t.덧칸 or (rid, cid) in t.남길글:
                    continue
                갈래, 지금 = p.지금(rid, cid)
                if 갈래 != "글":
                    continue
                종 = p.문.열종류[sid].get(cid)
                if 지금 == "n/a":
                    if p.비움(rid, cid, "규칙:n/a", "고정 글 n/a"):
                        셈["n/a(규칙)로 비움"] += 1
                elif _안내문인가(지금) and cid not in (이름열, p.단위열[sid]) and (종 == "근거" or 줄.get("입력") and cid in 줄["입력"]):
                    if p.비움(rid, cid, "규칙:안내문", "입력 칸의 안내문"):
                        셈["안내문(규칙)으로 비움"] += 1
                elif cid == 이름열:
                    m = re.match(r"^(\s+|·\s*)", 지금)
                    if m:
                        깊이 = 2 if 지금.lstrip().startswith("·") else 1
                        if p.글(rid, cid, 지금[m.end():].strip(), "규칙:들여", "앞의 빈칸 · 가운뎃점 머리를 뗀다"):
                            줄["들여"] = 깊이
                            p.들여고침.append((rid, 깊이))

    # 4. 덧이름 — 이름표에 없거나 이름표대로 둘 수 없는 칸
    for (rid, cid), x in t.덧칸.items():
        if rid not in p.줄:
            셈["덧이름: 없는 줄(%s)" % ("걷은 줄" if rid in 걷은 else "뺀 줄" if rid in 뺄줄 else "모름")] += 1
            continue
        if rid in 뺄줄:
            continue
        sid = p.줄[rid][0]
        열 = {"이름": p.이름열[sid], "단위": p.단위열[sid]}.get(cid, cid)
        if x.get("수식"):
            바뀜 = p.수식(rid, 열, x["수식"], "덧이름", x.get("까닭", ""))
        elif x.get("새"):
            바뀜 = p.글(rid, 열, x["새"], "덧이름", x.get("까닭", ""))
        else:
            바뀜 = p.비움(rid, 열, "덧이름", x.get("까닭", ""))
        셈["덧이름으로 고침" if 바뀜 else "덧이름: 이미 같음"] += 1
        if x.get("들여") is not None and p.줄[rid][1].get("들여") != x["들여"]:
            p.줄[rid][1]["들여"] = x["들여"]
            p.들여고침.append((rid, x["들여"]))
    # 4-나. 덧이름의 「수식글」 — 그 칸의 수식에 든 글 상수 하나를 바꾼다. 수식의 셈은 그대로이고 글만 내는 가지의 글이 바뀐다
    #        (이름표가 「글만 뺌」으로 적은 수식 속 안내 글 가운데 덧이름이 고른 칸만 — 나머지는 판정 수식을 다시 짜는 묶음의 일이다)
    for x in t.수식글:
        for cid in x["열"]:
            rid = x["줄"]
            if rid not in p.줄 or rid in 뺄줄:
                셈["수식글: 없는 줄"] += 1
                continue
            갈래, 지금 = p.지금(rid, cid)
            옛, 새 = '"%s"' % x["옛"], '"%s"' % x["새"]
            if 갈래 != "수식" or 옛 not in 지금:
                셈["수식글: 이미 같음"] += 1
                continue
            p.수식(rid, cid, 지금.replace(옛, 새), "덧이름:수식글", x.get("까닭", ""))
            셈["수식글로 고침"] += 1
    # 이름표가 들여쓰기를 준 줄(이름 앞의 빈칸 · 가운뎃점 머리를 새 이름이 이미 뗀 줄)
    for it in t.이름표["항목"]:
        if it["role"] in ("행이름", "시나리오줄") and it["action"] != "drop" and re.match(r"^(\s+|·)", it.get("old") or ""):
            sid, 칸들 = p.탭2sid.get(it["old_sheet"]), 옛칸들(it["old_cell"])
            for 열글자, 행 in 칸들 or ():
                rid = "%sR%03d" % (sid, 행)
                if rid in p.줄 and rid not in 뺄줄:
                    깊이 = 2 if it["old"].lstrip().startswith("·") else 1
                    if p.줄[rid][1].get("들여") != 깊이:
                        p.줄[rid][1]["들여"] = 깊이
                        p.들여고침.append((rid, 깊이))

    # 5. 줄 빼기
    p.줄빼기(뺄줄)
    p.주석보류 = [OrderedDict([("uid", it["uid"]), ("줄", rid), ("열", cid), ("옛 글", "" if 옛 is None else "%s" % 옛),
                              ("이름표의 주석", (it.get("note") or "").strip()), ("까닭", 주.get("까닭", ""))])
                 for it, rid, cid, 옛, 주 in 주석보류]
    p.바꿈 = 순바꿈(p.바꿈)
    return p, t, 셈, 결과, 탭바꿈


def 순바꿈(바꿈):
    """같은 칸을 두 번 고친 것을 하나로 — 첫 「옛」과 끝 「새」. 끝이 처음과 같으면 바뀐 것이 아니다(다시 돌려도 같게)."""
    칸 = OrderedDict()
    for b in 바꿈:
        열쇠 = (b["줄"], b["열"])
        if 열쇠 in 칸:
            칸[열쇠]["새"], 칸[열쇠]["출처"], 칸[열쇠]["까닭"] = b["새"], b["출처"], b["까닭"]
        else:
            칸[열쇠] = OrderedDict(b)
    return [b for b in 칸.values() if b["옛"] != b["새"]]


# ───────────────────────── 좌표 지도에 싣는 표 ─────────────────────────
def 이름칸(p):
    """가정 파일의 이름이 들어갈 칸과 그 칸에 쓸 글의 틀 — {블록: {열쇠: [[시트 ID, 칸 번호, 틀, "채움"]]}}.

    줄 이름 속의 기본 이름(「매출 구분 1」「경비 1」「기타」)을 「{이름}」 자리로 바꾼 글이 틀이다. 기본 이름이 없는 줄은 이름 칸이 아니다."""
    번호2sid = {s["이름"].split(".")[0].strip(): sid for sid, s in p.시트.items()}
    낸 = OrderedDict()
    for 블록, 열쇠, 자리글, 곳들 in 이름자리:
        칸들 = 낸.setdefault(블록, OrderedDict()).setdefault(열쇠, [])
        for 시, 번들 in 곳들:
            sid = 번호2sid[시]
            열글자 = next(옛 for 옛, cid in p.옛열[sid].items() if cid == p.이름열[sid])
            for 번 in 번들:
                rid = "%sR%03d" % (sid, 번)
                if rid not in p.줄:
                    continue
                갈래, 글 = p.지금(rid, p.이름열[sid])
                if 갈래 != "글":
                    continue
                if 자리글 == "기타":
                    if not 글.startswith("기타"):
                        continue
                    틀 = "{이름}" + 글[len("기타"):]
                elif 자리글 in 글:
                    틀 = 글.replace(자리글, "{이름}")
                else:
                    continue
                칸들.append([sid, "%s%d" % (열글자, 번), 틀, "채움"])
    return 낸


def 이름칸_명세(명세):
    """편 명세(줄무늬.읽기가 준 것)에서 바로 낸 「이름칸」 — `이름칸(판)` 과 같은 표다. 짓기가 좌표 지도에 싣는다(W3a)."""
    시트 = 명세["시트"]
    번호2sid = {s["이름"].split(".")[0].strip(): sid for sid, s in 시트.items() if s.get("이름")}
    줄 = {r["id"]: r for s in 시트.values() for r in s["행"]}
    낸 = OrderedDict()
    for 블록, 열쇠, 자리글, 곳들 in 이름자리:
        칸들 = 낸.setdefault(블록, OrderedDict()).setdefault(열쇠, [])
        for 시, 번들 in 곳들:
            sid = 번호2sid.get(시)
            이름열 = next((c for c in 시트[sid]["열"] if c["종류"] == "이름"), None) if sid else None
            if not 이름열 or not 이름열.get("옛"):
                continue
            for 번 in 번들:
                한 = (줄.get("%sR%03d" % (sid, 번)) or {}).get("칸", {}).get(이름열["id"])
                if not 한 or "f" in 한 or "t" in 한 or not isinstance(한.get("v"), str):
                    continue
                글 = 한["v"]
                if 자리글 == "기타":
                    if not 글.startswith("기타"):
                        continue
                    틀 = "{이름}" + 글[len("기타"):]
                elif 자리글 in 글:
                    틀 = 글.replace(자리글, "{이름}")
                else:
                    continue
                칸들.append([sid, "%s%d" % (이름열["옛"], 번), 틀, "채움"])
    return 낸


def 명세에싣기(자료, 명세):
    """좌표 지도(자료)에 「이름칸」·「단위종류」와 표지(「이름입히기」)를 싣는다 — 짓기가 지도를 낼 때 부른다(`지도싣기` 와 같은 표)."""
    자료["이름칸"] = 이름칸_명세(명세)
    있는줄 = {r["id"] for s in 명세["시트"].values() for r in s["행"]}
    for sid, 줄들 in _json(os.path.join(표곳, "단위종류.json")).items():
        if sid == "설명":
            continue
        자료.setdefault("단위종류", OrderedDict())[sid] = OrderedDict(
            (k, v) for k, v in 줄들.items() if "%sR%03d" % (sid, int(k)) in 있는줄)
    자료["이름입히기"] = {"도구": "이름입히기.py --지도", "이름칸": "줄 이름 속의 기본 이름(매출 구분 N · 경비 N · 기타)을 이름 자리로 바꾼 틀",
                     "단위종류": "이름표/단위종류.json — 단위 글을 바꾸기 전에 굳힌 12번 줄의 종류"}
    return 자료


def 지도싣기(지도곳, 폴더=정본, 낼=print):
    """지은 좌표 지도에 「이름칸」·「단위종류」를 싣는다. 키트의 좌표지도보강.py 는 지도에 이미 있는 표를 그대로 둔다."""
    p = 판(폴더)
    자료 = _json(지도곳)
    자료["이름칸"] = 이름칸(p)
    종류 = _json(os.path.join(표곳, "단위종류.json"))
    for sid, 줄들 in 종류.items():
        if sid == "설명":
            continue
        있는 = OrderedDict((k, v) for k, v in 줄들.items() if "%sR%03d" % (sid, int(k)) in p.줄)
        자료.setdefault("단위종류", OrderedDict())[sid] = 있는
    자료["이름입히기"] = {"도구": "이름입히기.py --지도", "이름칸": "줄 이름 속의 기본 이름(매출 구분 N · 경비 N · 기타)을 이름 자리로 바꾼 틀",
                     "단위종류": "이름표/단위종류.json — 단위 글을 바꾸기 전에 굳힌 12번 줄의 종류"}
    _json쓰기(지도곳, 자료, separators=(",", ":"))
    n = sum(len(v) for 열쇠들 in 자료["이름칸"].values() for v in 열쇠들.values())
    낼("좌표 지도에 실었다: %s — 이름 칸 %d곳 · 단위종류 %s" % (
        지도곳, n, " · ".join("%s %d줄" % (k, len(v)) for k, v in 자료["단위종류"].items())))
    return 자료


# ───────────────────────── 선택지 대응표 ─────────────────────────
_re견줌앞 = re.compile(r'\[\$?(S\d\dR\d+)\]@\$?([^\s=<>,()&+\-*/"]+)\s*(=|<>)\s*"((?:[^"]|"")*)"')
_re견줌뒤 = re.compile(r'"((?:[^"]|"")*)"\s*(=|<>)\s*\[\$?(S\d\dR\d+)\]@\$?([^\s=<>,()&+\-*/"]+)')


def 대응표(낼=print):
    """선택 칸의 값 글자는 코드와 수식이 읽으므로 이번에 바꾸지 않는다. 「옛 값 → 새 표시 글」만 적어 둔다."""
    t = 표()
    p = 판(정본)
    칸들, 판정 = [], Counter()
    for it in t.이름표["항목"]:
        if it["role"] == "선택지":
            sid = p.탭2sid.get(it["old_sheet"])
            풀 = 옛칸들(it["old_cell"]) or []
            자리 = ["%sR%03d@%s" % (sid, 행, p.옛열[sid].get(열, 열)) for 열, 행 in 풀]
            남은 = [x for x in 자리 if x.split("@")[0] in p.줄]
            칸들.append(OrderedDict([
                ("uid", it["uid"]), ("옛 시트", it["old_sheet"]), ("옛 칸", it["old_cell"]), ("명세의 칸", 자리),
                ("조치", it["action"]), ("옛 값", it["old"]), ("새 표시 글", re.sub(r"\s*\(하이닉스[^)]*\)$", "", it.get("new_value") or "")),
                ("새 선택지 목록", [x.strip() for x in (it.get("options") or "").split(" / ") if x.strip()]),
                ("지금 명세에 있는가", "있다" if 남은 and len(남은) == len(자리) else ("일부" if 남은 else "없다(걷은 줄)")),
                ("읽는 곳", it.get("code_coupled") or ""), ("비고", it.get("note") or "")]))
        elif it["role"] in ("판정표시", "총괄") and it.get("options"):
            판정[it["options"]] += 1
    덧 = t.덧.get("선택지 값 대응") or OrderedDict()
    # 수식이 글 상수와 견주는 칸 — [행]@열="글" · "글"=[행]@열 꼴(<> 도). 표시 글을 바꾸려면 이 수식들이 먼저 번호나 대응표를 읽어야 한다
    견줌 = OrderedDict()
    for sid, t2 in p.시트.items():
        for 줄 in t2["행"]:
            for cid, 한 in 줄["칸"].items():
                if "f" not in 한:
                    continue
                글 = 손수식쓰기(한["f"], cid, sid, p.문, None, False)
                for m in _re견줌앞.finditer(글):
                    if m.group(4):                      # 빈 글과 견주는 것(빈칸 확인)은 선택 값이 아니다
                        견줌.setdefault("%s@%s" % (m.group(1), m.group(2)), Counter())[m.group(4)] += 1
                for m in _re견줌뒤.finditer(글):
                    if m.group(1):
                        견줌.setdefault("%s@%s" % (m.group(3), m.group(4)), Counter())[m.group(1)] += 1
    견줌 = OrderedDict((k, OrderedDict(sorted(v.items()))) for k, v in sorted(견줌.items()))
    낸 = OrderedDict([
        ("설명", "선택 칸의 값 글자는 엔진 · 붓기 · 자체검사와 워크북의 수식이 읽는다. L1-가 는 값 글자를 바꾸지 않았다. "
               "표시 글을 바꾸는 묶음은 이 표로 수식과 코드를 선택 번호나 대응표를 읽게 고친 뒤에 바꾼다(0_결정 추가 결정 — 서식과 점검)."),
        ("값 대응", 덧),
        ("수식이 견주는 글 상수", OrderedDict([
            ("설명", "「행 ID@수식에 적힌 열」마다 그 칸과 견주는 글 상수와 그 수(수식 칸 수). 선택 칸의 값 글자를 바꾸면 이 수식들이 깨진다."),
            ("칸", 견줌)])),
        ("판정 표시", OrderedDict([
            ("설명", "판정 칸은 숫자(0 = 이상 없음, 1 = 이상)와 표시 글로 가른다(W6b). 지금 판정 수식이 내는 머리 글과 새 표시 글."),
            ("옛 머리 글 → 새 표시 글", OrderedDict([("OK", "OK"), ("확인 필요", "Error (정합성 · 완결성) / Review (검토사항)"), ("신호", "Review"),
                                            ("확인 불가", "Error (완결성 — 값 · 출처 미기재)"), ("해당 없음", "N/A"), ("검사 아님", "N/A"),
                                            ("미사용", "N/A")])),
            ("이름표가 판정 칸마다 적은 새 표시 글 묶음(칸 수)", OrderedDict((k.replace("n/a", t.판정표시.get("n/a", "n/a")), v) for k, v in 판정.most_common()))])),
        ("선택 칸", 칸들)])
    os.makedirs(기록곳, exist_ok=True)
    _json쓰기(os.path.join(기록곳, "선택지_대응표.json"), 낸)
    낼("선택지 대응표: %s — 선택 칸 항목 %d · 값 대응 %d묶음" % (os.path.join(기록곳, "선택지_대응표.json"), len(칸들), len(덧)))
    return 낸


# ───────────────────────── 명령줄 ─────────────────────────
def main(인자):
    sys.stdout.reconfigure(encoding="utf-8")
    global 기록곳
    폴더 = 정본
    if "--명세" in 인자:
        폴더 = 인자[인자.index("--명세") + 1]
    if "--기록" in 인자:
        기록곳 = 인자[인자.index("--기록") + 1]
    if "--지도" in 인자:
        지도싣기(인자[인자.index("--지도") + 1], 폴더)
        return 0
    if "--대응표" in 인자:
        대응표()
        return 0
    보기만 = "--보기" in 인자
    try:
        p, t, 셈, 결과, 탭바꿈 = 입히기(폴더)
    except (어긋남, 배치오류) as e:
        print("멈춤 — %s" % (e if isinstance(e, 어긋남) else "\n".join(o["설명"] for o in e.오류목록[:20])))
        return 1
    print("이름표 항목 %d개 → 칸 %d곳" % (len(t.이름표["항목"]), len(결과)))
    for 처리, n in sorted(셈.items(), key=lambda kv: -kv[1]):
        print("  %-28s %d" % (처리, n))
    print("바꾼 칸 %d · 뺀 줄 %d · 끝을 옮긴 범위 %d · 들여쓰기 %d줄 · 탭 이름 %d" % (
        len(p.바꿈), len(p.뺀줄), len(p.고친범위), len(p.들여고침), len(탭바꿈)))
    바뀜 = bool(p.바꿈 or p.뺀줄 or p.들여고침 or 탭바꿈)
    if 보기만 or not 바뀜:
        if not 바뀜:
            print("바뀔 것이 없다 — 명세는 이미 입힌 상태다. 아무것도 쓰지 않았다")
        if 보기만 and 바뀜:
            os.makedirs(기록곳, exist_ok=True)
            _기록쓰기(os.path.join(기록곳, "이름입히기_보기.json"), p, 셈, 결과, 탭바꿈)
            print("보기만 했다. 할 일의 목록: %s" % os.path.join(기록곳, "이름입히기_보기.json"))
        return 0
    수 = p.쓰기()
    os.makedirs(기록곳, exist_ok=True)
    _기록쓰기(os.path.join(기록곳, "이름입히기_기록.json"), p, 셈, 결과, 탭바꿈)
    print("줄명세에 적었다(%s). 기록: %s" % (" · ".join("%s %s" % kv for kv in 수.items() if kv[0] in ("시트", "행")),
                                    os.path.join(기록곳, "이름입히기_기록.json")))
    print("다음: python 줄무늬.py --다시쓰기 줄명세 --덧명세 새시트/S14.jsonl 새시트/S15.jsonl  →  python 범위지문.py 보기 줄명세 --덧명세 …")
    return 0


def _기록쓰기(경로, p, 셈, 결과, 탭바꿈):
    _json쓰기(경로, OrderedDict([
        ("셈", OrderedDict(sorted(셈.items(), key=lambda kv: -kv[1]))),
        ("탭 이름", [{"시트": a, "옛": b, "새": c} for a, b, c in 탭바꿈]),
        ("뺀 줄", p.뺀줄), ("끝을 옮긴 범위", p.고친범위), ("주석 보류", getattr(p, "주석보류", [])),
        ("들여쓰기", [{"줄": a, "들여": b} for a, b in p.들여고침]),
        ("바꾼 칸", p.바꿈),
        ("항목별", [{"uid": a, "줄": b, "열": c, "처리": d, "덧말": e} for a, b, c, d, e in 결과])]))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

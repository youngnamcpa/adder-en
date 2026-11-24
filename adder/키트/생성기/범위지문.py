# -*- coding: utf-8 -*-
"""범위지문 — 명세를 손으로 고친 뒤에도 범위의 뜻이 그대로인지 본다.

짓기의 범위 점검은 「명세의 순서 대 배치의 순서」를 견준다. 명세 자체에서 줄을 옮기거나 끼우면 그 순서가 곧 기준이 되므로
아무것도 안 걸린다(검증 3-1 가·나·다). 그래서 범위마다 「구성 줄 ID 목록」을 명세 폴더의 범위지문.json 에 적어 두고,
짓기가 지금 명세와 견준다.

  · 위치·빈 칸으로 읽는 범위(INDEX · MATCH · 짝 범위 · COUNTBLANK · COUNTIF …)의 구성·순서가 바뀌면 → 오류
  · 합계 범위(SUM · MAX · MIN · COUNT · AVERAGE …)가 바뀌면 → 바뀐 목록을 내고, 승인 표시가 있어야 짓는다
    (짓기의 합계범위승인=True / 명령줄 --합계범위승인, 또는 아래 「승인」 명령으로 지문을 고친다)
  · 가정묶음(머리 줄 + 세 시나리오 줄)이 기준에서 빠지거나 바뀌면, 서로 짝인 범위의 수가 기준보다 줄면 → 오류
  · 시트 머리(열 차례 · 축의 열 · 묶음마다 열 ID 목록 · 쓰임의 별칭)가 바뀌면 → 오류(위치로 읽는 범위와 같게 다룬다 —
    열의 종류나 묶음 표를 고치면 묶음으로 적은 범위·무늬가 말없이 줄거나 는다. 승인은 --위치범위 로만)
  · 범위의 끝 줄 바로 곁(또는 끝 줄과 그 범위를 읽는 줄 사이)에 지문에 없던 줄이 생기면 → 위험한 경고 한 번
    (새 줄이 합계에 들지 않는다. 범위 끝을 고치거나, 뜻한 것이면 승인한다)

지문과 무관하게 명세만 보고 잡는 것(승인으로 못 푼다)
  · 범위의 두 끝이 명세 순서로 뒤집혔다          · 수식이 놓인 칸이 제 범위 안에 있다(순환)
  · 지문에 가정묶음으로 적힌 머리 줄의 INDEX 가 「바로 아래 세 줄」이 아닌 범위를 읽는다(세 줄 사이에 줄을 끼웠거나 뺐다)
  · 서로 짝인 범위(한 함수가 자리끼리 읽는 범위들 · INDEX 범위 ↔ 그 위치를 낸 MATCH 범위)의 크기가 다르다

가정묶음은 시트 머리에 「가정묶음」 표시가 있는 시트(12번)에서만 찾는다 — 다른 시트의 「INDEX 줄 + 바로 아래 세 줄」은
그냥 표다(좌표 지도의 가정묶음에 싣지 않는다). 줄 수가 셋이 아닌 표도 승인(--위치범위)으로 받는다.

범위 지문은 손으로 고치지 않는다. 범위를 일부러 바꿨으면 바뀐 목록을 확인하고 승인한다.

쓰기:  python 범위지문.py 보기 <줄 무늬 명세 폴더> [--덧명세 파일.jsonl …]            바뀐 범위를 보인다(바뀐 것이 있으면 종료 코드 1)
       python 범위지문.py 승인 <줄 무늬 명세 폴더> [--덧명세 파일.jsonl …] [--위치범위]   지금 명세로 지문을 고쳐 적는다
           --위치범위 : 위치로 읽는 범위 · 가정묶음 · 짝 수가 바뀐 것까지 승인한다(안 주면 합계 범위만 바뀌었을 때에만 적는다)
  덧명세(새 시트)의 지문은 그 파일이 있는 폴더의 범위지문.json 에 적힌다.
"""
import sys
import os
import json
from collections import OrderedDict

from 공통 import 위치로읽나, 호출구조, 좌표의존함수, 짝범위함수, 합계함수, 행ID풀기, 배치오류, 자리풀기, 자리열

형식 = "범위지문 2"      # 1 → 2: 시트 머리(열 차례 · 축 · 묶음 · 쓰임)와 줄 목록을 함께 적는다
곁한도 = 5               # 범위 끝에서 이 줄 수 안에 그 범위를 읽는 줄이 있으면, 그 사이에 생긴 새 줄을 모두 알린다
파일이름 = "범위지문.json"
짝갈래 = ("한 함수 안의 짝", "INDEX↔MATCH 짝")


# ───────────────────────── 명세 훑기 ─────────────────────────
def 수식들(명세, 배열범위=True):
    """명세의 모든 수식 틀 — (시트 ID, 행 ID | None, 열 ID | None, 틀).

    배열범위=False 면 배열 수식이 놓이는 범위(「배열」)는 내지 않는다 — 읽는 범위가 아니라 수식이 차지하는 자리다.
    """
    for sid, s in 명세["시트"].items():
        for 줄 in s["행"]:
            for cid, 한 in (줄.get("칸") or {}).items():
                for 키 in ("f", "배열") if 배열범위 else ("f",):
                    if 키 in 한:
                        yield sid, 줄["id"], cid, 한[키]
        for v in s.get("유효성") or ():
            for 키 in ("formula1", "formula2"):
                if 키 in v:
                    yield sid, None, None, v[키]
        for c in s.get("조건부서식") or ():
            for f in c.get("수식") or ():
                yield sid, None, None, f
        for d in s.get("정의된이름") or ():
            if d.get("틀"):
                yield sid, None, None, d["틀"]
    for d in 명세["책"].get("정의된이름") or ():
        if d.get("틀"):
            yield None, None, None, d["틀"]


def 칸틀표(명세):
    """(행 ID, 열 ID) → 틀. 짝 범위를 찾을 때 위치 칸의 수식을 따라가는 데 쓴다."""
    return {(줄["id"], cid): 한["f"] for s in 명세["시트"].values() for 줄 in s["행"]
            for cid, 한 in (줄.get("칸") or {}).items() if "f" in 한}


def 짝볼틀인가(틀):
    return any(isinstance(p, dict) and (p.get("fn") in ("INDEX", "MATCH", "LOOKUP", "XLOOKUP") or p.get("fn") in 짝범위함수)
               for p in 틀)


def 짝찾기(틀, 칸틀):
    """틀 안에서 서로 짝인 범위를 찾는다 → (가, 나, 갈래, 긴쪽만) 을 차례로 낸다.

    ① 한 함수가 자리끼리 짝지어 읽는 범위들(SUMPRODUCT · COUNTIFS · SUMIF · LOOKUP …)
    ② INDEX 의 범위 ↔ 그 위치를 낸 MATCH 의 범위. 위치 인자가 다른 칸을 가리키면 그 칸의 수식(MATCH)을 따라간다.
    긴쪽만 = 한 줄(또는 한 열)짜리끼리 길이만 견준다(INDEX ↔ MATCH).
    """
    참 = [p for p in 틀 if isinstance(p, dict)]
    호출, 길 = 호출구조(틀)

    def 가까운(i):      # 참조 i 를 감싼 가장 가까운 「좌표 의존·짝 범위」 함수 호출
        return next((c for c, _ in reversed(길.get(i, ())) if 호출[c]["fn"] in 좌표의존함수 or 호출[c]["fn"] in 짝범위함수), None)

    def 매치범위(틀2, 깊이=0):
        """틀 안의 MATCH 가 찾는 범위들. 틀이 다른 칸 하나만 가리키면 그 칸을 따라간다."""
        참2 = [p for p in 틀2 if isinstance(p, dict)]
        범위 = [p for p in 참2 if p["k"] == "r" and p.get("fn") in ("MATCH", "XMATCH") and p.get("arg") == 1]
        if not 범위 and 깊이 < 3:
            for p in 참2:
                if p["k"] == "c" and (p["r"], p["c"]) in 칸틀:
                    범위 += 매치범위(칸틀[(p["r"], p["c"])], 깊이 + 1)
        return 범위

    for ci, 한 in enumerate(호출):
        든 = [i for i in range(len(참)) if any(c == ci for c, _ in 길.get(i, []))]     # 이 호출 안의 모든 참조
        if 한["fn"] in 짝범위함수 or 한["fn"] in ("LOOKUP", "XLOOKUP"):
            범위 = [참[i] for i in 든 if 참[i]["k"] == "r" and 가까운(i) == ci]
            for a in range(len(범위)):
                for b in range(a + 1, len(범위)):
                    yield 범위[a], 범위[b], "한 함수 안의 짝", False
        elif 한["fn"] == "INDEX":
            읽는 = [참[i] for i in 한["인자"][0] if 참[i]["k"] == "r"]
            if not 읽는:
                continue
            위치 = [i for i in 든 if any(c == ci and a >= 1 for c, a in 길[i])]
            찾는 = []
            for i in 위치:
                p = 참[i]
                if p["k"] == "r" and p.get("fn") in ("MATCH", "XMATCH") and p.get("arg") == 1:
                    찾는.append(p)
                elif p["k"] == "c" and (p["r"], p["c"]) in 칸틀:
                    찾는 += 매치범위(칸틀[(p["r"], p["c"])])
            for 가 in 읽는:
                for 나 in 찾는:
                    yield 가, 나, "INDEX↔MATCH 짝", True


def 범위이름(p):
    return "%s:%s@%s~%s" % (p["r"], p["r2"], p.get("g") or p["c"], p.get("g") or p["c2"])


def 가정묶음(명):
    """세 시나리오 줄을 가진 가정 머리 줄: [[머리 행 ID, [비관 · 기준 · 낙관 행 ID]], …]

    줄 이름(· 비관 따위)이 아니라 수식 구조로 찾는다 — 머리 줄의 수식이 바로 아래 세 줄을 INDEX 로 읽는다.
    시트 머리에 「가정묶음」 표시가 있는 시트에서만 찾는다(다른 시트의 세 줄짜리 선택 표는 시나리오 가정이 아니다).
    """
    if not 명.get("가정묶음"):
        return []
    줄, 묶음 = 명["행"], []
    for i, r in enumerate(줄):
        아래 = [x["id"] for x in 줄[i + 1:i + 4]]
        if len(아래) < 3:
            continue
        if any(isinstance(p, dict) and p["k"] == "r" and p.get("fn") == "INDEX" and p.get("arg") == 0
               and p["r"] == 아래[0] and p["r2"] == 아래[2]
               for 한 in (r.get("칸") or {}).values() for p in 한.get("f", ())):
            묶음.append([r["id"], 아래])
    return 묶음


def 머리지문(명):
    """시트 머리의 지문 — 열 차례 · 축을 이루는 열 · 묶음마다 열 ID 목록 · 쓰임의 별칭(→ 열 ID).

    열의 「종류」나 묶음 표를 고치면 여기가 달라진다(종류 그 자체가 아니라 그 결과 — 어느 열이 어느 묶음에 드는가를 적는다).
    """
    열 = [c["id"] for c in 명["열"]]
    종 = {c["id"]: c.get("종류", "기타") for c in 명["열"]}
    # 기간 축의 갈래(FY실적 · 누계실적 · 잔여예측 · 연간예측 · 상세 · 수렴 · 달아님) — 묶음 표가 갈래로도 묶는다
    덧 = {c["id"]: {x for x in (c.get("갈래"), c.get("구간"), "달아님" if c.get("달아님") else None) if x} for c in 명["열"]}
    축 = set(명.get("축") or ())
    return OrderedDict([
        ("열", 열),
        ("축", [c for c in 열 if 종[c] in 축]),
        ("묶음", OrderedDict((이름, [c for c in 열 if 종[c] in 종류들 or 덧[c] & set(종류들)])
                           for 이름, 종류들 in (명.get("묶음") or {}).items())),
        ("쓰임", OrderedDict((이름, OrderedDict(표)) for 이름, 표 in (명.get("쓰임") or {}).items()))])


def _목록다름(옛, 새):
    """두 목록이 어떻게 다른가 — 글."""
    든, 빠진 = [x for x in 새 if x not in 옛], [x for x in 옛 if x not in 새]
    낱 = []
    if 든:
        낱.append("든 열 %s" % ", ".join(든[:8]))
    if 빠진:
        낱.append("빠진 열 %s" % ", ".join(빠진[:8]))
    if not 든 and not 빠진:
        i = next(k for k, (a, b) in enumerate(zip(옛, 새)) if a != b)
        낱.append("차례가 바뀌었다(%s ↔ %s)" % (옛[i], 새[i]))
    return " · ".join(낱)


def 머리다름(옛, 새):
    """적어 둔 시트 머리의 지문과 지금 것이 다른 곳 → 글 목록."""
    낸 = []
    if (옛.get("열") or []) != 새["열"]:
        낸.append("열 등록부: %s" % _목록다름(옛.get("열") or [], 새["열"]))
    if (옛.get("축") or []) != 새["축"]:
        낸.append("축(직전·다음 열을 세는 열들): %s" % _목록다름(옛.get("축") or [], 새["축"]))
    옛묶, 새묶 = 옛.get("묶음") or {}, 새["묶음"]
    for 이름 in list(옛묶) + [x for x in 새묶 if x not in 옛묶]:
        if 이름 not in 새묶:
            낸.append("묶음 「%s」 가 없어졌다" % 이름)
        elif 이름 not in 옛묶:
            낸.append("새 묶음 「%s」 (%s)" % (이름, ", ".join(새묶[이름][:8])))
        elif list(옛묶[이름]) != list(새묶[이름]):
            낸.append("묶음 「%s」 의 열: %s — 이 묶음으로 적은 범위·무늬가 그만큼 달라진다" % (이름, _목록다름(list(옛묶[이름]), list(새묶[이름]))))
    옛쓰, 새쓰 = 옛.get("쓰임") or {}, 새["쓰임"]
    for 이름 in list(옛쓰) + [x for x in 새쓰 if x not in 옛쓰]:
        가, 나 = 옛쓰.get(이름), 새쓰.get(이름)
        if 가 is None or 나 is None:
            낸.append("쓰임 「%s」 가 %s" % (이름, "없어졌다" if 나 is None else "새로 생겼다"))
        elif dict(가) != dict(나):
            낸.append("쓰임 「%s」 의 별칭: %s" % (이름, " · ".join(
                "%s %s → %s" % (k, 가.get(k, "없음"), 나.get(k, "없음")) for k in list(가) + [x for x in 나 if x not in 가] if 가.get(k) != 나.get(k))))
    return 낸


def 기준들(명세):
    """시트마다 적어 둔 지문 → {sid: (그 시트의 기준 | {}, 지문 파일이 없나, 파일 이름, 파일 경로)}"""
    기억, 낸 = {}, {}
    for sid in 명세["시트"]:
        곳 = _지문곳(명세, sid)
        if 곳 not in 기억:
            기억[곳] = 읽기(곳)
        낸[sid] = (기억[곳]["시트"].get(sid) or {}, bool(기억[곳].get("없음")), os.path.basename(곳) if 곳 else 파일이름, 곳)
    return 낸


class _훑음:
    """명세를 한 번 훑어 범위 · 구조 오류 · 짝 수를 모은다."""

    def __init__(self, 명세):
        self.명세 = 명세
        시트 = 명세["시트"]
        self.주인 = {줄["id"]: sid for sid, s in 시트.items() for 줄 in s["행"]}
        self.순 = {sid: {줄["id"]: i for i, 줄 in enumerate(s["행"])} for sid, s in 시트.items()}
        self.줄 = {sid: [줄["id"] for 줄 in s["행"]] for sid, s in 시트.items()}
        self.열순 = {sid: {c["id"]: i for i, c in enumerate(s["열"])} for sid, s in 시트.items()}
        self.묶음열 = {sid: 머리지문(s)["묶음"] for sid, s in 시트.items()}      # 자리 이름(실적.끝 · 시간.4 …)을 열로 풀 때 쓴다
        self.줄번호 = {줄["id"]: 줄.get("줄번호") for s in 시트.values() for 줄 in s["행"]}
        self.범위 = {sid: OrderedDict() for sid in 시트}      # sid → {"r1:r2": [행 ID …]}
        self.읽기 = {}                                        # "r1:r2" → "위치" | "합계"
        self.쓰는곳 = {}                                      # "r1:r2" → [(행 ID, 열 ID) …] (보기용, 몇 곳만)
        self.범위열 = {}                                      # "r1:r2" → 그 범위가 읽는 열 ID 들
        self.읽는줄 = {}                                      # "r1:r2" → 같은 시트에서 그 범위를 읽는 줄들
        self.기준 = 기준들(명세)
        # 지문에 가정묶음으로 적힌 머리 줄 — 「바로 아래 세 줄」 점검은 이 줄들에만 건다(다른 줄의 INDEX 표는 몇 줄이든 된다)
        self.기준머리 = {머리 for 기준, _, _, _ in self.기준.values() for 머리 in (기준.get("가정묶음") or {})}
        self.짝 = {sid: {k: set() for k in 짝갈래} for sid in 시트}
        self.오류 = []
        self._본오류 = set()
        self._훑기()

    def _틀림(self, 종류, sid, rid, cid, 설명, 한번키=None):
        if 한번키 is not None:
            if 한번키 in self._본오류:
                return
            self._본오류.add(한번키)
        파일 = self.명세["시트"][sid].get("파일") if sid in self.명세["시트"] else None
        줄 = self.줄번호.get(rid)
        머리 = ("%s %s째 줄 — " % (파일, 줄)) if 파일 and 줄 else ""
        self.오류.append({"종류": 종류, "시트": sid, "자리": [rid, cid], "설명": 머리 + 설명, "파일": 파일, "줄": 줄})

    def _크기(self, p):
        """범위의 (줄 수, 열 수) — 명세의 순서로. 모르는 줄·열이 끼면 None."""
        home = self.주인.get(p["r"])
        if home is None or self.주인.get(p["r2"]) != home:
            return None
        순, 열순 = self.순[home], self.열순[home]

        def 푼(c):      # 자리 이름으로 적은 열 — 이 명세의 열 등록부에서 푼다
            if c in 열순:
                return c
            자 = 자리풀기(c)
            return 자리열(self.묶음열[home].get(자[0]) or [], 자[1]) if 자 else None

        c1, c2 = 푼(p["c"]), 푼(p["c2"])
        if c1 is None or c2 is None:
            return None
        return (abs(순[p["r"]] - 순[p["r2"]]) + 1, abs(열순[c1] - 열순[c2]) + 1)

    def _훑기(self):
        칸틀 = 칸틀표(self.명세)
        for sid, rid, cid, 틀 in 수식들(self.명세, 배열범위=False):
            참 = [p for p in 틀 if isinstance(p, dict)]
            여러 = [i for i, p in enumerate(참) if p["k"] in ("r", "R") and p["r"] != p["r2"]]
            구조 = 호출구조(틀) if 여러 else None
            for i, p in enumerate(참):
                if p["k"] not in ("r", "R"):
                    continue
                home = self.주인.get(p["r"])
                if home is None or self.주인.get(p["r2"]) != home:
                    continue                    # 등록부 밖의 줄(옛 xlsx 에서 뽑은 명세만) — 지문을 못 낸다
                순 = self.순[home]
                i1, i2 = 순[p["r"]], 순[p["r2"]]
                lo, hi = min(i1, i2), max(i1, i2)
                # 수식이 놓인 칸이 제 범위 안인가(순환)
                if p["k"] == "r" and rid is not None and home == sid and lo <= self.순[sid][rid] <= hi:
                    열순 = self.열순[home]
                    if p["c"] in 열순 and p["c2"] in 열순 and cid in 열순 and \
                            min(열순[p["c"]], 열순[p["c2"]]) <= 열순[cid] <= max(열순[p["c"]], 열순[p["c2"]]):
                        self._틀림("범위 순환", sid, rid, cid,
                                 "%s 의 수식이 제가 놓인 칸을 범위(%s:%s)로 읽는다 — 순환 참조" % (rid, p["r"], p["r2"]),
                                 ("순환", rid, p["r"], p["r2"]))
                if p["r"] == p["r2"]:
                    continue
                키 = "%s:%s" % (p["r"], p["r2"])
                if i1 > i2:
                    self._틀림("범위 뒤집힘", sid, rid, cid,
                             "범위 %s 의 두 끝이 명세 순서로 뒤집혔다(%s 이 %s 보다 아래에 있다) — 줄을 옮겼으면 범위의 끝을 고쳐 적는다"
                             % (키, p["r"], p["r2"]), ("뒤집힘", 키))
                호출, 길 = 구조
                감싼 = 호출[길[i][-1][0]]["fn"] if 길.get(i) else None
                엄한 = 위치로읽나(p) or 감싼 not in 합계함수
                self.범위[home].setdefault(키, self.줄[home][lo:hi + 1])
                if 엄한 or 키 not in self.읽기:
                    self.읽기[키] = "위치" if 엄한 else "합계"
                곳 = self.쓰는곳.setdefault(키, [])
                if len(곳) < 3 and rid:
                    곳.append((rid, cid))
                if p["k"] == "r":
                    열순, 열들 = self.열순[home], [c["id"] for c in self.명세["시트"][home]["열"]]
                    if p["c"] in 열순 and p["c2"] in 열순:
                        a, b = sorted((열순[p["c"]], 열순[p["c2"]]))
                        self.범위열.setdefault(키, set()).update(열들[a:b + 1])
                if rid is not None and home == sid:
                    self.읽는줄.setdefault(키, set()).add(rid)
                # 지문에 가정묶음으로 적힌 머리 줄 — 그 줄의 INDEX 는 바로 아래 세 줄을 읽어야 한다
                if p["k"] == "r" and p.get("fn") == "INDEX" and p.get("arg") == 0 and rid is not None and home == sid \
                        and rid in self.기준머리:
                    나 = self.순[sid][rid]
                    if lo <= 나 + 1 <= hi and (lo, hi) != (나 + 1, 나 + 3):
                        self._틀림("가정 머리 줄", sid, rid, cid,
                                 "%s 의 INDEX 가 바로 아래 세 줄(비관·기준·낙관)이 아니라 %s:%s (%d줄)을 읽는다 — 가정 머리 줄의 세 줄 사이에 줄을 끼웠거나 뺐다"
                                 % (rid, p["r"], p["r2"], hi - lo + 1), ("머리", rid, 키))
            # 서로 짝인 범위 — 명세 안에서 크기가 같아야 한다
            if sid is not None and 짝볼틀인가(틀):
                for 가, 나, 갈래, 긴쪽만 in 짝찾기(틀, 칸틀):
                    옛가, 옛나 = self._크기(가), self._크기(나)
                    if 옛가 is None or 옛나 is None:
                        continue
                    if 긴쪽만:
                        if 1 not in 옛가 or 1 not in 옛나:
                            continue
                        다름 = max(옛가) != max(옛나)
                    else:
                        다름 = 옛가 != 옛나
                    짝키 = (범위이름(가), 범위이름(나), 갈래)
                    if 다름:
                        self._틀림("짝 범위 (명세)", sid, rid, cid,
                                 "명세에서 서로 짝인 범위의 크기가 다르다(%s): %s (%s) ↔ %s (%s) — 한 시트의 열 등록부만 고쳤거나 범위의 끝이 어긋났다"
                                 % (갈래, 범위이름(가), "×".join(map(str, 옛가)), 범위이름(나), "×".join(map(str, 옛나))), ("짝",) + 짝키)
                    else:
                        self.짝[sid][갈래].add(짝키)


def 곁새줄(훑, sid, 키, 기준줄):
    """범위의 끝 줄 곁에 생긴 새 줄(지문에 없던 줄) — 범위의 열에 값·수식·입력 칸이 있는 줄만. → [(행 ID, "아래" | "위", 읽는 줄 | None)]

    끝 줄에 바로 붙어 이어진 새 줄은 늘 알린다. 그 범위를 읽는 줄이 끝에서 가까이(옛 줄 곁한도 안) 있으면 그 사이의 새 줄을 모두 알린다.
    새 줄은 범위에 들지 않으므로 합계에 더해지지 않고 점검 수에 세어지지 않는다.
    """
    줄 = 훑.줄[sid]
    순 = 훑.순[sid]
    든 = 훑.범위[sid][키]
    lo, hi = 순[든[0]], 순[든[-1]]
    열 = 훑.범위열.get(키) or set()
    읽는 = 훑.읽는줄.get(키) or set()
    표 = {r["id"]: r for r in 훑.명세["시트"][sid]["행"]}

    def 찬(rid):
        한 = 표[rid]
        칸 = 한.get("칸") or {}
        return any(c in 열 and ("f" in h or "v" in h) for c, h in 칸.items()) or bool(set(한.get("입력") or ()) & 열)

    낸 = []
    for 방향, 이름 in ((1, "아래"), (-1, "위")):
        i, 붙은, 옛수, 후보 = (hi if 방향 == 1 else lo) + 방향, True, 0, []
        찾은 = None
        while 0 <= i < len(줄):
            rid = 줄[i]
            if rid in 읽는:
                찾은 = rid
                break
            if rid not in 기준줄:
                if 찬(rid):
                    후보.append((rid, 붙은))
            else:
                붙은 = False
                옛수 += 1
                if 옛수 > 곁한도:
                    break
            i += 방향
        낸 += [(rid, 이름, 찾은) for rid, 붙 in 후보 if 붙 or 찾은]
    return 낸


def 만들기(명세, 덧시트=True, 훑음=None):
    """지금 명세의 범위 지문. → {"형식", "시트": {sid: {"머리", "짝", "가정묶음", "범위", "줄"}}}"""
    훑 = 훑음 or _훑음(명세)
    시트 = OrderedDict()
    for sid, s in 명세["시트"].items():
        if s.get("덧파일") and not 덧시트:
            continue
        시트[sid] = OrderedDict([
            ("머리", 머리지문(s)),
            ("가정묶음", OrderedDict((머리, 세) for 머리, 세 in 가정묶음(s))),
            ("짝", OrderedDict((k, len(훑.짝[sid][k])) for k in 짝갈래)),
            ("범위", OrderedDict(훑.범위[sid])),
            ("줄", list(훑.줄[sid]))])
    return {"형식": 형식, "시트": 시트}


def 쓰기(경로, 지문):
    """범위 지문을 파일에 적는다 — 범위 하나에 한 줄(diff 로 읽히게)."""
    def 한줄(v):
        return json.dumps(v, ensure_ascii=False, separators=(",", ":"))
    줄 = ['{', ' "형식": %s,' % 한줄(지문["형식"]),
         ' "설명": "시트 머리(열 차례 · 축 · 묶음 · 쓰임)와 범위마다 구성 줄 ID 목록. 손으로 고치지 않는다 — 일부러 바꿨으면 python 범위지문.py 승인 <명세 폴더> 로 고친다.",',
         ' "시트": {']
    시트글 = []
    for sid, 한 in 지문["시트"].items():
        몸 = ['  %s: {' % 한줄(sid)]
        머리 = 한.get("머리")
        if 머리 is not None:
            몸 += ['   "머리": {', '    "열": %s,' % 한줄(머리.get("열", [])), '    "축": %s,' % 한줄(머리.get("축", [])), '    "묶음": {']
            몸.append(",\n".join('     %s: %s' % (한줄(k), 한줄(v)) for k, v in (머리.get("묶음") or {}).items()))
            몸 += ['    },', '    "쓰임": {']
            몸.append(",\n".join('     %s: %s' % (한줄(k), 한줄(v)) for k, v in (머리.get("쓰임") or {}).items()))
            몸 += ['    }', '   },']
        몸 += ['   "짝": %s,' % 한줄(한.get("짝", {})), '   "가정묶음": {']
        몸.append(",\n".join('    %s: %s' % (한줄(k), 한줄(v)) for k, v in 한.get("가정묶음", {}).items()))
        몸 += ['   },', '   "범위": {']
        몸.append(",\n".join('    %s: %s' % (한줄(k), 한줄(v)) for k, v in 한.get("범위", {}).items()))
        if 한.get("줄") is not None:
            낱 = 한["줄"]
            몸 += ['   },', '   "줄": [']
            몸.append(",\n".join('    ' + ",".join(한줄(x) for x in 낱[i:i + 12]) for i in range(0, len(낱), 12)))
            몸 += ['   ]', '  }']
        else:
            몸 += ['   }', '  }']
        시트글.append("\n".join(x for x in 몸 if x != ""))
    줄.append(",\n".join(시트글))
    줄 += [' }', '}']
    os.makedirs(os.path.dirname(os.path.abspath(경로)), exist_ok=True)
    with open(경로, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(줄) + "\n")


def 읽기(경로):
    """범위 지문 파일 → dict. 없으면 빈 지문."""
    if not 경로 or not os.path.exists(경로):
        return {"형식": 형식, "시트": {}, "없음": True}
    with open(경로, encoding="utf-8") as f:
        return json.load(f)


def _지문곳(명세, sid):
    곳 = (명세.get("지문곳") or {}).get(sid)
    if 곳:
        return 곳
    return os.path.join(명세["폴더"], 파일이름) if 명세.get("폴더") else None


def 견주기(명세, 훑음=None):
    """지금 명세의 지문을 적어 둔 지문과 견준다. → 바뀐 것 목록

    한 건 = {"갈래": "위치" | "합계" | "곁" | "없어짐", "시트", "범위", "설명", "쓰는곳"}
      위치   : 위치·빈 칸으로 읽는 범위 · 가정묶음 · 짝 수 · 시트 머리 — 짓기가 오류로 올린다
      합계   : 합계 범위의 구성 — 승인 표시가 있어야 짓는다
      곁     : 범위의 끝 줄 곁에 생긴 새 줄 — 위험한 경고(범위 끝을 고치거나 승인한다)
      없어짐 : 지문에 있던 범위를 이제 아무 수식도 안 읽는다 — 경고
    """
    훑 = 훑음 or _훑음(명세)
    지금 = 만들기(명세, 훑음=훑)
    바뀐 = []
    for sid, 한 in 지금["시트"].items():
        기준, 없음, 파일, 곳 = 훑.기준[sid]
        if 없음:
            바뀐.append({"갈래": "위치", "시트": sid, "범위": None,
                       "설명": "%s 시트의 범위 지문 파일이 없다(%s) — 범위 %d개 · 가정묶음 %d개 · 시트 머리. 「python 범위지문.py 승인 … --위치범위」 로 만든다"
                       % (sid, 곳, len(한["범위"]), len(한["가정묶음"]))})
            continue
        # 시트 머리 — 열 차례 · 축 · 묶음 · 쓰임
        if 기준.get("머리") is None:
            바뀐.append({"갈래": "위치", "시트": sid, "범위": None,
                       "설명": "%s 시트의 머리(열 차례 · 축 · 묶음 · 쓰임)가 지문에 없다(%s — 옛 형식의 지문이거나 새 시트다). "
                               "「python 범위지문.py 승인 … --위치범위」 로 적는다" % (sid, 파일)})
        else:
            for 글 in 머리다름(기준["머리"], 한["머리"]):
                바뀐.append({"갈래": "위치", "시트": sid, "범위": None,
                           "설명": "%s 시트의 머리가 지문과 다르다 — %s (%s)" % (sid, 글, 파일)})
        옛범위 = 기준.get("범위") or {}
        for 키, 줄 in 한["범위"].items():
            옛 = 옛범위.get(키)
            if 옛 == 줄:
                continue
            갈래 = 훑.읽기.get(키, "위치")
            쓰는 = ", ".join("%s %s" % x for x in 훑.쓰는곳.get(키, ())[:2])
            if 옛 is None:
                설명 = "새 범위 %s (%d줄) — 지문에 없다" % (키, len(줄))
            else:
                더한, 뺀 = [x for x in 줄 if x not in 옛], [x for x in 옛 if x not in 줄]
                낱 = []
                if 더한:
                    낱.append("든 줄 %s" % ", ".join(더한[:6]))
                if 뺀:
                    낱.append("빠진 줄 %s" % ", ".join(뺀[:6]))
                if not 더한 and not 뺀:
                    낱.append("줄의 순서가 바뀌었다")
                설명 = "범위 %s 의 구성이 바뀌었다(%d줄 → %d줄): %s" % (키, len(옛), len(줄), " · ".join(낱))
            바뀐.append({"갈래": 갈래, "시트": sid, "범위": 키, "쓰는곳": 쓰는,
                       "설명": "%s — %s (%s 읽는 곳: %s)" % (
                           설명, "위치·빈 칸으로 읽는 범위" if 갈래 == "위치" else "합계 범위", 파일, 쓰는 or "?")})
        for 키 in 옛범위:
            if 키 not in 한["범위"]:
                바뀐.append({"갈래": "없어짐", "시트": sid, "범위": 키, "설명": "지문에 있던 범위 %s 를 이제 아무 수식도 안 읽는다" % 키})
        # 범위의 끝 줄 곁에 생긴 새 줄 — 구성이 그대로인 범위에서만 본다(구성이 바뀐 범위는 위에서 이미 알렸다)
        if 기준.get("줄") is not None:
            기준줄 = set(기준["줄"])
            for 키, 줄 in 한["범위"].items():
                if 옛범위.get(키) != 줄:
                    continue
                for rid, 쪽, 읽는 in 곁새줄(훑, sid, 키, 기준줄):
                    바뀐.append({"갈래": "곁", "시트": sid, "범위": 키, "줄": rid,
                               "설명": "범위 %s 의 %s 지문에 없던 줄 %s 이 생겼다 — 범위에 들지 않는다(%s)" % (
                                   키, "끝 줄 아래에" if 쪽 == "아래" else "첫 줄 위에", rid,
                                   "그 범위를 읽는 줄 %s 과의 사이" % 읽는 if 읽는 else "범위 끝에 바로 붙은 줄")})
        for 머리, 세 in (기준.get("가정묶음") or {}).items():
            if 한["가정묶음"].get(머리) != 세:
                바뀐.append({"갈래": "위치", "시트": sid, "범위": 머리,
                           "설명": "가정묶음이 기준에서 빠지거나 바뀌었다: %s → %s (지금 %s)" % (머리, "·".join(세), "·".join(한["가정묶음"].get(머리) or ["없음"]))})
        for 갈래 in 짝갈래:
            옛수, 새수 = (기준.get("짝") or {}).get(갈래, 0), 한["짝"].get(갈래, 0)
            if 새수 < 옛수:
                바뀐.append({"갈래": "위치", "시트": sid, "범위": None,
                           "설명": "%s 시트의 수식에서 서로 짝인 범위(%s)의 수가 기준보다 줄었다: %d → %d" % (sid, 갈래, 옛수, 새수)})
    return 바뀐


def 점검(명세, 합계승인=False):
    """짓기가 부른다. → (오류 목록, 경고 목록)

    구조 오류(뒤집힘 · 순환 · 가정 머리 줄 · 짝 크기)는 늘 오류다. 지문과 다른 범위는 위치로 읽는 것이면 오류,
    합계 범위면 합계승인=True 일 때만 경고로 낮춘다. 결과는 명세에 기억해 둔다(같은 명세로 여러 번 지을 때).
    """
    기억 = 명세.setdefault("_범위점검", {})
    if 합계승인 not in 기억:
        훑 = 기억.get("훑음") or _훑음(명세)
        기억["훑음"] = 훑
        오류, 경고 = list(훑.오류), []
        바뀐 = 견주기(명세, 훑)
        없어진 = [b for b in 바뀐 if b["갈래"] == "없어짐"]
        for b in 바뀐:
            if b["갈래"] == "위치":
                오류.append({"종류": "범위 지문 (위치로 읽는 범위)", "시트": b["시트"], "자리": None,
                           "설명": b["설명"] + " — 일부러 바꿨으면 「python 범위지문.py 승인 <명세 폴더> --위치범위」"})
            elif b["갈래"] == "합계":
                (경고 if 합계승인 else 오류).append({
                    "종류": "범위 지문 (합계 범위)", "시트": b["시트"], "자리": None,
                    "설명": b["설명"] + ("" if 합계승인 else " — 일부러 바꿨으면 승인한다(짓기 --합계범위승인 또는 「python 범위지문.py 승인 <명세 폴더>」)")})
        곁 = [b for b in 바뀐 if b["갈래"] == "곁"]
        if 곁:      # 한 번 알린다 — 새 줄이 합계에 안 들고 점검 수에 안 세어진다
            줄들 = sorted({b["줄"] for b in 곁})
            경고.append({"종류": "범위 끝의 새 줄", "시트": 곁[0]["시트"], "자리": [곁[0]["줄"], None],
                       "설명": "범위의 끝 줄 곁에 지문에 없던 줄이 %d줄 생겼다(%s) — 그 범위(합계 · 점검 수 따위)에 들지 않는다. "
                               "넣을 줄이면 범위의 끝 ID 를 고치고, 뜻한 것이면 승인한다(「python 범위지문.py 승인 <명세 폴더>」). 보기: %s"
                               % (len(줄들), ", ".join(줄들[:6]), 곁[0]["설명"]),
                       "목록": [b["설명"] for b in 곁]})
        if 없어진:
            경고.append({"종류": "범위 지문 (없어진 범위)", "시트": None, "자리": None,
                       "설명": "지문에 있던 범위 %d개를 이제 아무 수식도 안 읽는다(보기: %s) — 「python 범위지문.py 승인」 으로 지문을 정리한다"
                       % (len(없어진), ", ".join(b["범위"] for b in 없어진[:3]))})
        기억[합계승인] = (오류, 경고)
    오류, 경고 = 기억[합계승인]
    return list(오류), list(경고)


def 승인(명세, 위치범위=False):
    """지금 명세로 범위 지문을 고쳐 적는다. → (적었나, 바뀐 것 목록, 구조 오류 목록)

    구조 오류가 있으면 적지 않는다. 위치로 읽는 범위가 바뀌었으면 위치범위=True 일 때만 적는다.
    """
    훑 = _훑음(명세)
    바뀐 = 견주기(명세, 훑)
    if 훑.오류 or (not 위치범위 and any(b["갈래"] == "위치" for b in 바뀐)):
        return False, 바뀐, 훑.오류
    지금 = 만들기(명세, 훑음=훑)
    곳별 = OrderedDict()
    for sid, 한 in 지금["시트"].items():
        곳별.setdefault(_지문곳(명세, sid), OrderedDict())[sid] = 한
    for 곳, 시트 in 곳별.items():
        옛 = 읽기(곳)
        남길 = OrderedDict((sid, 한) for sid, 한 in (옛.get("시트") or {}).items() if sid not in 명세["시트"])
        남길.update(시트)             # 이번에 읽지 않은 시트(다른 덧명세)의 지문은 그대로 둔다
        쓰기(곳, {"형식": 형식, "시트": 남길})
    명세.pop("_범위점검", None)
    return True, 바뀐, []


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    인자 = list(sys.argv[1:])
    위치 = "--위치범위" in 인자
    인자 = [a for a in 인자 if a != "--위치범위"]
    덧 = []
    if "--덧명세" in 인자:
        i = 인자.index("--덧명세")
        덧 = [a for a in 인자[i + 1:] if not a.startswith("--")]
        인자 = 인자[:i] + [a for a in 인자[i + 1:] if a.startswith("--")]
    if len(인자) != 2 or 인자[0] not in ("보기", "승인"):
        raise SystemExit(__doc__)
    import 줄무늬
    try:
        명 = 줄무늬.읽기(인자[1], 옛서식=False, 덧파일=덧)
    except 배치오류 as e:
        print("명세를 읽지 못했다 — 오류 %d건" % len(e.오류목록))
        for o in e.오류목록[:40]:
            print("  [%s] %s" % (o["종류"], o["설명"]))
        sys.exit(1)

    def 찍기(바뀐, 구조):
        for o in 구조:
            print("  [구조 오류 · %s] %s" % (o["종류"], o["설명"]))
        for 갈래, 머리 in (("위치", "위치·빈 칸으로 읽는 범위 · 가정묶음 · 짝 수 · 시트 머리"), ("합계", "합계 범위"),
                         ("곁", "범위 끝의 새 줄(범위에 들지 않는다)"), ("없어짐", "없어진 범위")):
            낱 = [b for b in 바뀐 if b["갈래"] == 갈래]
            if 낱:
                print("  %s — %d건" % (머리, len(낱)))
                for b in 낱[:60]:
                    print("    %s" % b["설명"])
                if len(낱) > 60:
                    print("    … 그 밖 %d건" % (len(낱) - 60))

    if 인자[0] == "보기":
        훑 = _훑음(명)
        바뀐 = 견주기(명, 훑)
        지금 = 만들기(명, 훑음=훑)
        print("범위 %d개(위치 %d · 합계 %d) · 가정묶음 %d개 · 짝 %s" % (
            sum(len(s["범위"]) for s in 지금["시트"].values()), sum(1 for v in 훑.읽기.values() if v == "위치"),
            sum(1 for v in 훑.읽기.values() if v == "합계"), sum(len(s["가정묶음"]) for s in 지금["시트"].values()),
            json.dumps({k: sum(s["짝"][k] for s in 지금["시트"].values()) for k in 짝갈래}, ensure_ascii=False)))
        if not 바뀐 and not 훑.오류:
            print("범위 지문과 같다")
            sys.exit(0)
        print("범위 지문과 다르다:")
        찍기(바뀐, 훑.오류)
        sys.exit(1)
    됨, 바뀐, 구조 = 승인(명, 위치)
    찍기(바뀐, 구조)
    if 됨:
        print("범위 지문을 고쳐 적었다 — 바뀐 것 %d건" % len(바뀐))
        sys.exit(0)
    print("범위 지문을 적지 않았다 — " + ("구조 오류부터 고친다" if 구조 else "위치로 읽는 범위가 바뀌었다. 확인했으면 --위치범위 를 붙인다"))
    sys.exit(1)

# -*- coding: utf-8 -*-
"""카드 — 사실 카드의 꼴 · 검사 · 합치기 (레터 문체 3단계 B1 · 2026-10-26).

왜 있나
    레터 문장이 원천과 뜻이 어긋나는 일은 문장이 사실을 다시 말하는 순간 생긴다(연구/레터_문체체계_독립설계안_20261026.md 2절).
    그래서 사실을 문장 밖에 먼저 적는다 — 주장 · 등급 · 값(장부 키) · 날짜 · 필수 한정 · 원천 인용 · 계산식. 글은 이 카드를 옮긴 것이고,
    검사기(문체검사)는 문장을 꼬리표의 카드와만 맞댄다. 이 파일은 그 카드의 꼴을 정하고 꼴이 맞는지 본다.
    무엇이 참인지(인용이 원천에 글자 그대로 있나 · 계산이 맞나)는 카드 감사(B4)가 본다. 여기서는 꼴만 본다.

카드 문서 꼴
    {"판": "카드 v1", "회사": …, "평가기준일": "YYYY-MM-DD", "재무기준일": "YYYY-MM-DD", "카드": [카드…],
     "함정_메모": [글…], "결론에_나오는_용어": [말…]}
카드 꼴(칸 — ✔ 는 반드시)
    ✔ id        접두 한 글자(만든 곳 — 카드설정.json 「만든곳」) + 두세 자리 숫자 + 덧글자 하나까지(k01 · p12 · p12b)
    ✔ 주장      카드가 말하는 사실 한두 문장
    ✔ 등급      카드설정.json 「등급」의 닫힌 목록 하나
      값        [{"글": 레터에 찍히는 꼴, "장부": 장부 키(선택), "단위": 금액 · 비율 · 지수 · 물량 · 배수 · 일수(선택)}]
      날짜      [레터에 찍히는 날짜 꼴 …]  — 문장에 나온 날짜가 이 목록 안에 있어야 한다(검사기 F2)
      공표일    "YYYY-MM-DD" — 그 사실이 공표된 날. 등급이 요구하면 반드시(회사 발화 · 발표 · 조사기관 · 보도)
      사건일    "YYYY-MM-DD" — 사실이 가리키는 날이 공표일과 다를 때
      기간      "2026년 상반기" 같은 말
      계산      [{"이름", "식", "글", "자리"}] — 식은 숫자 · 사칙 · 비교와 카드설정 「식.이름」의 함수만
      필수      [{"종류": 카드설정 「한정」 하나, "정규식": 문장에 남아야 할 말, "설명"}]
      권장      필수와 같은 꼴(빠지면 경고)
      원천      [{"파일": 회차 폴더 기준 경로, "인용": 원천에 글자 그대로 있는 말}] — 등급의 「원천」 칸이 요구하는 만큼
      고유명사  [{"이름", "소개"}] · 풀이용어 [이 카드가 풀이하는 말 …] · 함정 [글] · 고침 [글] · 층제한 ["3분" …](그 층에 쓰지 않음)
    값 · 원천 항목의 덧칸(B2 제안 · 2026-10-26 받음): 값.본편 = 본편 꼴(「291만 9,000원」 — 글은 3분 레터 꼴) · 원천.자리 = 파일 안의 위치
    B3 제안(같은 날 받음): 원천.세부 = 공시가 인용한 조사기관 · 기준 같은 출처의 세부 · 고유명사[].소개원천 = 소개의 근거(공시 · 일반설명)
      · 수 = 회사 소개의 몇째 수에 쓰려는 카드인지(1~5) · **접두는 만든 곳, 등급은 사실의 성격**이다 — 공시 갈래(p)가 공시 표로 셈한
      비중 카드는 등급 「계산」 · 접두 p 다. 둘을 묶지 않는다(「옮기기」만 옛 실험 카드의 계산 등급을 k 로 바꾼다 — 옛 카드에 만든 곳 기록이 없어서)
    밑줄 칸(_경로 · _창 · _날 · _무엇 …)은 만든 곳이 다시 셈하려고 남기는 기록이다. 꼴 검사는 보지 않는다
    판정으로 붙는 칸(검사가 채움): 평가기준일뒤(참 · 거짓)
    문서의 「못지음」: [{"무엇", "까닭"}] — 지으려 했는데 못 지은 카드와 그 까닭(합치기가 조각마다 모은다)

쓰는 법
    python 스크립트/카드.py 검사 <카드 문서.json>                 # 꼴 검사 — 오류가 있으면 종료 코드 1
    python 스크립트/카드.py 합치기 <회차 폴더> [-o 경로]           # _raw/카드/*.json → _raw/사실카드.json(id 겹침 · 기준일 어긋남은 오류)
    python 스크립트/카드.py 옮기기 <옛 카드.json> -o <새 카드.json>  # 독립 설계 실험 카드(등급 열일곱 · 한정 열넷)를 닫힌 목록으로

회사 · 업종 이름은 이 파일에 없다.
"""
from __future__ import annotations

import argparse
import ast
import copy
import datetime as _dt
import glob
import io
import json
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:                                    # noqa: BLE001
    pass

여기 = os.path.dirname(os.path.abspath(__file__))
설정 = json.load(io.open(os.path.join(여기, "카드설정.json"), encoding="utf-8"))
판 = 설정["판"]
등급표 = 설정["등급"]
한정표 = 설정["한정"]
만든곳 = 설정["만든곳"]
식이름 = set(설정["식"]["이름"])
옛한정 = {옛: 새 for 새, v in 한정표.items() for 옛 in v.get("옛이름", [])}

id꼴 = re.compile(r"^([a-z])(\d{2,3})([a-z]?)$")
날꼴 = re.compile(r"^\d{4}-\d{2}-\d{2}$")
알칸 = {"id", "주장", "등급", "값", "날짜", "공표일", "사건일", "기간", "계산", "필수", "권장", "원천", "고유명사", "풀이용어",
       "함정", "고침", "층제한", "평가기준일뒤", "수"}


def _날(s):
    try:
        return _dt.date.fromisoformat(s)
    except (TypeError, ValueError):
        return None


def 식검사(식):
    """식이 숫자 · 사칙 · 비교 · 허용 함수만 쓰는지. 문제가 있으면 그 말을, 없으면 None."""
    try:
        나무 = ast.parse(식, mode="eval")
    except SyntaxError as e:
        return "식을 읽지 못함 — %s" % e.msg
    허용 = (ast.Expression, ast.BinOp, ast.UnaryOp, ast.Compare, ast.BoolOp, ast.Constant, ast.Call, ast.Name, ast.Load,
          ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow, ast.USub, ast.UAdd, ast.Eq, ast.NotEq,
          ast.Lt, ast.LtE, ast.Gt, ast.GtE, ast.And, ast.Or, ast.Not, ast.Attribute, ast.Tuple, ast.List)
    for n in ast.walk(나무):
        if not isinstance(n, 허용):
            return "식에 쓸 수 없는 꼴 %s" % type(n).__name__
        if isinstance(n, ast.Name) and n.id not in 식이름:
            return "식에 쓸 수 없는 이름 %s" % n.id
        if isinstance(n, ast.Attribute) and not (n.attr == "days" and isinstance(n.value, ast.BinOp)):
            return "식에 쓸 수 없는 속성 %s" % n.attr
        if isinstance(n, ast.Constant) and not isinstance(n.value, (int, float, str, bool)):
            return "식에 쓸 수 없는 값"
    return None


def 카드검사(c, 문서=None):
    """카드 하나의 꼴. [(등급, 말)] — 등급은 오류 · 경고."""
    밖 = []

    def 오(말):
        밖.append(("오류", 말))

    def 경(말):
        밖.append(("경고", 말))

    if not isinstance(c, dict):
        return [("오류", "카드가 사전이 아님")]
    m = id꼴.match(str(c.get("id", "")))
    if not m:
        오("id 꼴이 아님 — 「%s」(접두 한 글자 + 두세 자리 숫자 + 덧글자)" % c.get("id"))
    elif m.group(1) not in 만든곳:
        오("id 접두 「%s」가 카드설정 「만든곳」에 없음" % m.group(1))
    for k in c:
        if k not in 알칸 and not k.startswith("_"):
            경("모르는 칸 「%s」" % k)
    if not str(c.get("주장", "")).strip():
        오("주장이 비었음")
    등 = c.get("등급")
    if 등 not in 등급표:
        오("등급 「%s」가 닫힌 목록에 없음" % 등)
        등정 = {}
    else:
        등정 = 등급표[등]
    for v in c.get("값", []) or []:
        if not isinstance(v, dict) or not str(v.get("글", "")).strip():
            오("값에 「글」이 없음")
    if 등 == "일반설명" and c.get("값"):
        오("일반설명 카드에 숫자 값")
    계 = c.get("계산", []) or []
    for k in 계:
        if not isinstance(k, dict) or not k.get("식") or "글" not in k:
            오("계산에 「식」 · 「글」이 없음")
            continue
        문 = 식검사(k["식"])
        if 문:
            오("계산 「%s」 — %s" % (k.get("이름", "?"), 문))
    if 등 == "계산" and not 계 and not any((v or {}).get("장부") for v in c.get("값", []) or []):
        오("계산 카드인데 계산식도 장부 키도 없음")
    for 칸 in ("필수", "권장"):
        for f in c.get(칸, []) or []:
            if not isinstance(f, dict):
                오("%s 항목이 사전이 아님" % 칸)
                continue
            if f.get("종류") not in 한정표:
                오("%s 종류 「%s」가 닫힌 목록에 없음" % (칸, f.get("종류")))
            try:
                re.compile(f.get("정규식") or "")
            except re.error as e:
                오("%s 정규식이 깨짐 — %s" % (칸, e))
            if not f.get("정규식"):
                오("%s 정규식이 비었음" % 칸)
    원 = c.get("원천", []) or []
    요구 = 등정.get("원천", "인용")
    if 요구 in ("인용", "파일") and not 원:
        오("등급 「%s」인데 원천이 없음" % 등)
    for o in 원:
        if not isinstance(o, dict) or not o.get("파일"):
            오("원천에 「파일」이 없음")
        elif 요구 == "인용" and not str(o.get("인용", "")).strip():
            오("원천 「%s」에 인용이 없음(등급 「%s」는 글자 그대로의 인용이 필요)" % (o.get("파일"), 등))
    if 등정.get("공표일") and not c.get("공표일"):
        오("등급 「%s」인데 공표일이 없음" % 등)
    for 칸 in ("공표일", "사건일"):
        if c.get(칸) and not (날꼴.match(str(c[칸])) and _날(c[칸])):
            오("%s 꼴이 YYYY-MM-DD 가 아님 — 「%s」" % (칸, c[칸]))
    for g in c.get("고유명사", []) or []:
        if not isinstance(g, dict) or not g.get("이름") or not g.get("소개"):
            오("고유명사에 이름 · 소개가 없음")
    for 칸 in ("날짜", "풀이용어", "함정", "고침", "층제한"):
        if 칸 in c and not isinstance(c[칸], list):
            오("「%s」는 목록이어야 함" % 칸)
    return 밖


def 기준일뒤(c, 문서):
    """카드가 가리키는 사실이 평가기준일 뒤인가 — 사건일이 있으면 사건일, 없으면 공표일로 본다."""
    t = _날((문서 or {}).get("평가기준일"))
    날 = _날(c.get("사건일")) or _날(c.get("공표일"))
    if not t or not 날:
        return None
    return 날 > t


def 문서검사(문서):
    """카드 문서 전체 — (오류 목록, 경고 목록, 고친 문서). 고친 문서에는 「평가기준일뒤」가 붙는다."""
    오, 경 = [], []
    if not isinstance(문서, dict) or not isinstance(문서.get("카드"), list):
        return ["카드 문서 꼴이 아님(「카드」 목록이 없음)"], [], 문서
    if 문서.get("판") != 판:
        경.append("판이 「%s」가 아님 — 「%s」" % (판, 문서.get("판")))
    for 칸 in ("평가기준일", "재무기준일"):
        if not (날꼴.match(str(문서.get(칸, ""))) and _날(문서.get(칸))):
            오.append("문서 %s 꼴이 YYYY-MM-DD 가 아님" % 칸)
    t, f = _날(문서.get("평가기준일")), _날(문서.get("재무기준일"))
    if t and f and f > t:
        오.append("재무기준일이 평가기준일보다 늦음")
    본 = {}
    새 = copy.deepcopy(문서)
    for c in 새["카드"]:
        cid = (c or {}).get("id")
        if cid in 본:
            오.append("id 겹침 — %s" % cid)
        본[cid] = c
        for 등, 말 in 카드검사(c, 문서):
            (오 if 등 == "오류" else 경).append("%s: %s" % (cid, 말))
        뒤 = 기준일뒤(c, 문서)
        if 뒤 is not None:
            c["평가기준일뒤"] = 뒤
    for k in ("함정_메모", "결론에_나오는_용어"):
        if k in 문서 and not isinstance(문서[k], list):
            오.append("「%s」는 목록이어야 함" % k)
    return 오, 경, 새


def 합치기(회차, 낼=None):
    """_raw/카드/*.json 을 한 문서로. 기준일 · 회사가 어긋나거나 id 가 겹치면 오류."""
    조각들 = sorted(glob.glob(os.path.join(회차, "_raw", "카드", "*.json")))
    if not 조각들:
        return ["_raw/카드/ 에 조각이 없음"], [], None
    밖 = None
    오, 경 = [], []
    for p in 조각들:
        d = json.load(io.open(p, encoding="utf-8"))
        if 밖 is None:
            밖 = {k: v for k, v in d.items() if k != "카드"}
            밖["판"] = 판
            밖["카드"], 밖["함정_메모"], 밖["결론에_나오는_용어"], 밖["못지음"] = [], [], [], []
            밖["_조각"] = []
        for k in ("회사", "평가기준일", "재무기준일"):
            if d.get(k) != 밖.get(k):
                오.append("%s 의 %s 「%s」가 다른 조각 「%s」와 다름" % (os.path.basename(p), k, d.get(k), 밖.get(k)))
        밖["카드"].extend(d.get("카드", []))
        for k in ("함정_메모", "결론에_나오는_용어"):
            for x in d.get(k, []) or []:
                if x not in 밖[k]:
                    밖[k].append(x)
        for x in d.get("못지음", []) or []:
            밖["못지음"].append(dict(x, 조각=os.path.basename(p)) if isinstance(x, dict) else {"무엇": str(x), "조각": os.path.basename(p)})
        밖["_조각"].append(os.path.relpath(p, 회차).replace("\\", "/"))
    o2, g2, 밖 = 문서검사(밖)
    오 += o2
    경 += g2
    낼 = 낼 or os.path.join(회차, "_raw", "사실카드.json")
    if not 오:
        io.open(낼, "w", encoding="utf-8").write(json.dumps(밖, ensure_ascii=False, indent=1))
    return 오, 경, 밖


_월일 = re.compile(r"(?:(\d{4})년\s*)?(\d{1,2})월\s*(\d{1,2})일")


def 옮기기(옛):
    """독립 설계 실험 카드 → 카드 v1. 등급 · 한정 이름을 닫힌 목록으로, 「용어」 → 「풀이용어」, 「사용」 → 「층제한」,
    공표일이 필요한 등급은 날짜 꼴에서 찾는다(연도가 없으면 평가기준일의 해 — 「_공표일추정」 표시)."""
    새 = {k: v for k, v in 옛.items() if k not in ("카드", "_판")}
    새["판"] = 판
    새["_옮김"] = "독립 설계 실험 카드(%s)에서 옮김" % 옛.get("_판", "?")[:40]
    if "재무기준일" not in 새 and "재무 자료 기준일" in 새:
        새["재무기준일"] = 새.pop("재무 자료 기준일")
    해 = str(옛.get("평가기준일", ""))[:4]
    접두 = {"c": "p", "g": "g"}
    새["카드"] = []
    for c in 옛.get("카드", []):
        d = {k: v for k, v in c.items() if k not in ("용어", "사용")}
        d["_옛id"] = c.get("id")
        m = id꼴.match(str(c.get("id", "")))
        if m:
            d["id"] = 접두.get(m.group(1), m.group(1)) + m.group(2) + m.group(3)
        d["등급"] = 설정["옛등급"].get(c.get("등급"), c.get("등급"))
        if d["등급"] == "계산" or "계산" in str(c.get("등급", "")):
            d["id"] = "k" + d["id"][1:]
        for 칸 in ("필수", "권장"):
            d[칸] = [dict(f, 종류=옛한정.get(f.get("종류"), f.get("종류"))) for f in c.get(칸, []) or []]
        for 칸 in ("함정", "고침"):
            if isinstance(d.get(칸), str):
                d[칸] = [d[칸]]
        if c.get("용어"):
            d["풀이용어"] = list(c["용어"])
        if c.get("사용"):
            d["층제한"] = ["3분"] if "3분" in str(c["사용"]) else []
        if 등급표.get(d["등급"], {}).get("공표일") and not d.get("공표일"):
            for s in c.get("날짜", []) or []:
                mm = _월일.search(s)
                if mm:
                    y = mm.group(1) or 해
                    d["공표일"] = "%s-%02d-%02d" % (y, int(mm.group(2)), int(mm.group(3)))
                    if not mm.group(1):
                        d["_공표일추정"] = "연도 없음 — 평가기준일의 해로 둠"
                    break
        새["카드"].append(d)
    return 새


def _보고(오, 경):
    for x in 오:
        print("오류 " + x)
    for x in 경:
        print("경고 " + x)
    print("카드 검사 — 오류 %d · 경고 %d" % (len(오), len(경)))


def main(argv=None):
    ap = argparse.ArgumentParser(description="사실 카드 — 꼴 검사 · 합치기 · 옛 카드 옮기기")
    sub = ap.add_subparsers(dest="일", required=True)
    a = sub.add_parser("검사")
    a.add_argument("파일")
    b = sub.add_parser("합치기")
    b.add_argument("회차")
    b.add_argument("-o", dest="낼")
    c = sub.add_parser("옮기기")
    c.add_argument("파일")
    c.add_argument("-o", dest="낼", required=True)
    인 = ap.parse_args(argv)
    if 인.일 == "검사":
        오, 경, _ = 문서검사(json.load(io.open(인.파일, encoding="utf-8")))
        _보고(오, 경)
        return 1 if 오 else 0
    if 인.일 == "합치기":
        오, 경, _ = 합치기(인.회차, 인.낼)
        _보고(오, 경)
        return 1 if 오 else 0
    새 = 옮기기(json.load(io.open(인.파일, encoding="utf-8")))
    io.open(인.낼, "w", encoding="utf-8").write(json.dumps(새, ensure_ascii=False, indent=1))
    오, 경, _ = 문서검사(새)
    _보고(오, 경)
    return 1 if 오 else 0


if __name__ == "__main__":
    sys.exit(main())

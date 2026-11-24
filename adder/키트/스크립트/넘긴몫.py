# -*- coding: utf-8 -*-
"""넘긴몫 — 판정을 다른 자리(15번 워크북 · 사람 · 검증 갈래)로 넘긴 몫을 한 장부에 모은다(S10-02 · 2026-10-18).

넘긴 몫이 흩어져 있으면 막는 길에 닿지 않는다 — 자체검사의 「→ 15번 … 가 판정」 줄은 목록(rc 무영향)이고, 거친 바퀴의 문항 · 범위 문항이
답을 받았는지, V1~V4 의 「사람이 볼 것」이 닫혔는지, 기본값으로 둔 판단이 사람 확인을 받았는지 읽는 기계가 없었다(S10 리뷰 실측: 예측 매출 0 ·
인건비 0 이 목록으로만 지나갔다). 이 장부가 그 정본이고 **레터 게이트 ⑤ 와 8단계 「넘기기 전 점검」이 미결 0(또는 사유 적힘)을 요구한다.**

    python 스크립트/넘긴몫.py 가정.json                      # _raw/넘긴몫.json 을 (다시) 쓰고 요약을 찍는다 — 미결이 있으면 rc 1
    python 스크립트/넘긴몫.py 가정.json --사유 <키> "<사유>"   # 그 줄을 사유와 함께 닫는다(사람이 적는다 — 다시 써도 사유는 남는다)
    python 스크립트/넘긴몫.py 가정.json --보기                # 쓰지 않고 보기만

모으는 것(있는 것만 — 회사 · 업종 이름은 어디에도 없다)
  15번      자체검사의 「→ 15번 X-n 가 판정」 줄 — 워크북 마감 기록(「마감」이고 그 번호가 미완목록에 없음)이 있으면 닫힘, 없으면 미결
  검토      자체검사의 검토 경보(「검토 R-n — `검토의견.R-n` 로 닫는다」) — 닫히지 않은 것
  멈춤      `_raw/멈춤기록.json` 의 마지막 멈춤 문항(값 문항 · 범위 문항) — 같은 대상 · 노드의 답(`답[]`)이 멈춤 시각 뒤에 없으면 미결
  지도      동인진단이 돈 회차인데 동인 지도가 없음 · 원가 노드의 성격확정(사람)이 없음
  기본값    가정의 근거 칸(근거 · 원천근거 · WACC근거)에 「[기본값]」 · 「[판단] 기본값」 딱지 — 사람 답 대신 둔 기본값(사람 확인 대기).
            `[기본값]` 은 정식 출처 딱지다(가정_스키마 「출처 딱지」 · S10R1-N3) — 답이 없어 규칙의 기본으로 둔 칸은 근거 첫 칸을 `[기본값]` 으로 시작한다
  기본값 의심  판단 칸(동인 지도 · 거친 바퀴의 판단칸) · 멈춤 문항 대상인데 근거 첫 칸이 `[판단]` 이고 멈춤기록에 그 대상의 답이 없는 칸 —
            사람 답 없이 기본값을 두고 `[판단]` 으로 적었을 수 있다(`기본값의심` — 자체검사 ⑯ 도 같은 함수로 목록을 낸다)
  검증      `_raw/검증_V1~V4.md` 의 「사람이 볼 것」 절의 항목
  critical  `_raw/모순장부.json` 의 critical 가운데 해소 · 승격이 없는 것
닫는 법 — 원인을 고치고 다시 돌리거나(그 줄이 사라진다), 고치지 않을 까닭이 있으면 `--사유` 로 적는다(사유가 있는 줄은 미결로 세지 않는다).
종료 코드 — 0 미결 0 · 1 미결 있음 · 2 입력 오류
"""
import argparse
import datetime
import glob
import hashlib
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
if 여기 not in sys.path:
    sys.path.insert(0, 여기)
from 종료코드 import 통과, 발견, 입력오류                # noqa: E402

파일이름 = "넘긴몫.json"
기본값딱지 = re.compile(r"\[기본값\]|\[Default\]|\[판단\]\s*기본값|\[Judgment\]\s*default", re.I)
_15번 = re.compile(r"→\s*((?:15번\s+[ICR]-\d+\S*\s*(?:·\s*)?)+)\s*가 판정")
_번호들 = re.compile(r"([ICR]-\d+)")
_검토 = re.compile(r"\(검토 (R-\d+)")


def _읽기(p):
    try:
        return json.load(io.open(p, encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _키(*조각):
    return hashlib.md5("|".join("%s" % x for x in 조각).encode("utf-8")).hexdigest()[:10]


def _첫줄(글):
    return re.sub(r"\*\*", "", ("%s" % 글).strip().split("\n")[0]).strip()[:240]


def 마감기록(회차):
    # 회차 바로 아래 · _raw · 한 단계 아래 폴더(워크북을 짓는 폴더에 마감 기록을 두는 회차 — 회차 20261023 `짓기/`)
    후보 = sorted(set(glob.glob(os.path.join(회차, "*마감*.json")) + glob.glob(os.path.join(회차, "_raw", "*마감*.json"))
                    + glob.glob(os.path.join(회차, "*", "*마감*.json"))),
                key=lambda p: -os.path.getmtime(p))
    for p in 후보:
        d = _읽기(p)
        if isinstance(d, dict) and "판정" in d and "가정" in d:
            return d, p
    return None, None


def _멈춤답대상(기록):
    """멈춤기록의 답[] 이 가리킨 대상 번호 · 이름 집합(시각 무관 — 한 번이라도 답한 칸)."""
    낸 = set()
    for a in ((기록 or {}).get("답") or []) if isinstance(기록, dict) else []:
        if not isinstance(a, dict):
            continue
        대 = a.get("대상")
        for y in (대 if isinstance(대, list) else ("%s" % 대).split("+")) if 대 else ():
            낸.add(("%s" % y).replace("A-", "").strip())
        if a.get("노드"):
            낸.add(("%s" % a["노드"]).strip())
    return 낸


def 기본값의심(가정, 가정경로, 원천폴더=None):
    """S10R1-N3 — 판단 칸(동인 지도 노드의 판단칸 · 거친 바퀴의 판단칸) · 멈춤 문항 대상(거친 바퀴 표의 문항)인데 근거 첫 칸이 `[판단]` 이고
    (「기본값」 낱말 없음) 멈춤기록에 그 대상의 답이 없으면 「기본값 의심」 → [(번호, 근거 첫 칸, 출처)]. 본선이 답 없이 기본값을 두고 `[판단]` 으로
    적으면 기본값 딱지 장부가 0 건이 되던 틈(리뷰 대행의 딱지에만 기대던 틈)을 메운다. 숫자 번호(가정 칸)만 본다 — 구조 선택 칸은 근거 칸이 없다."""
    회차 = os.path.dirname(os.path.abspath(가정경로)) if 가정경로 else os.getcwd()
    폴더 = 원천폴더 or os.path.join(회차, "_raw")
    대상 = {}
    거 = _읽기(os.path.join(폴더, "거친바퀴.json"))
    if isinstance(거, dict):
        for x in 거.get("판단칸") or []:
            if isinstance(x, dict) and ("%s" % x.get("번호", "")).isdigit():
                대상.setdefault("%s" % x["번호"], "판단 칸(%s)" % (x.get("노드") or "-"))
        for r in 거.get("표") or []:
            if isinstance(r, dict) and r.get("문항"):
                for y in r.get("대상") or []:
                    y = ("%s" % y).replace("A-", "").strip()
                    if y.isdigit():
                        대상.setdefault(y, "멈춤 문항(%s)" % (r.get("이름") or y)[:30])
    지도 = _읽기(os.path.join(폴더, "동인지도.json"))
    if isinstance(지도, dict):
        for n in 지도.get("노드") or []:
            for 칸 in (n.get("판단칸") or []) if isinstance(n, dict) else []:
                if isinstance(칸, dict) and ("%s" % 칸.get("번호", "")).isdigit():
                    대상.setdefault("%s" % 칸["번호"], "판단 칸(%s)" % (n.get("노드") or "-"))
    답 = _멈춤답대상(_읽기(os.path.join(폴더, "멈춤기록.json")))
    낸 = []
    근거 = 가정.get("근거") if isinstance(가정.get("근거"), dict) else {}
    for 번 in sorted(대상, key=int):
        넷 = 근거.get(번)
        첫 = ("%s" % (넷[0] if isinstance(넷, list) and 넷 else (넷 or ""))).strip()
        if ((첫.startswith("[판단]") or 첫.lower().startswith("[judgment]")) or 첫.lower().startswith("[judgment]")) and not 기본값딱지.search(첫) and 번 not in 답:
            낸.append((번, 첫, 대상[번]))
    return 낸


def _자체검사(가정, 가정경로):
    import 자체검사 as _자                                 # noqa: PLC0415
    return _자.검사결과(가정, 복사=True, 가정경로=가정경로)


def 모으기(가정, 가정경로, 원천폴더=None, 자체검사포함=True):
    """→ [{"키", "출처", "종류", "글", "번호", "상태"("미결" · "닫힘"), "닫힘까닭"}].
    `자체검사포함=False` 면 자체검사 몫(15번 판정 · 검토 경보)을 빼고 모은다 — 레터 게이트는 그 둘을 ⑤(자체검사 결과 파일 · 검토 의견)와
    ⑥(워크북 마감)에서 이미 보므로 같은 것을 다시 돌려 세지 않는다."""
    회차 = os.path.dirname(os.path.abspath(가정경로))
    폴더 = 원천폴더 or os.path.join(회차, "_raw")
    줄 = []

    def 넣기(출처, 종류, 글, 번호=None, 닫힘=None):
        줄.append({"키": _키(출처, 종류, 번호, _첫줄(글)[:80]), "출처": 출처, "종류": 종류, "번호": 번호, "글": _첫줄(글),
                  "상태": "닫힘" if 닫힘 else "미결", "닫힘까닭": 닫힘})

    # ── 자체검사 — 15번으로 넘긴 줄 · 닫히지 않은 검토 경보
    마, 마곳 = 마감기록(회차)
    미완 = {("%s" % (x.get("번호") or "")) for x in ((마 or {}).get("미완목록") or []) if isinstance(x, dict)}
    결 = None
    try:
        if 자체검사포함:
            결 = _자체검사(가정, 가정경로)
    except Exception as e:                                  # noqa: BLE001
        넣기("자체검사", "검사 못 돎", "자체검사를 돌리지 못했다 — %s: %s" % (type(e).__name__, e))
    for 검 in ((결 or {}).get("검사") or []):
        기호 = 검.get("기호") or ""
        for x in 검.get("목록") or []:
            m = _15번.search("%s" % x)
            if not m:
                continue
            번호들 = _번호들.findall(m.group(1))
            닫 = None
            if isinstance(마, dict) and 마.get("판정") == "마감" and not (set(번호들) & 미완):
                닫 = "워크북 마감(%s) — 15번 %s 통과" % (os.path.basename(마곳), " · ".join(번호들))
            넣기("자체검사 %s" % 기호, "15번 판정", x, " · ".join(번호들), 닫)
        for x in 검.get("경보") or []:
            m = _검토.search("%s" % x)
            if m:
                넣기("자체검사 %s" % 기호, "검토 의견", x, m.group(1))

    # ── 멈춤 — 마지막 멈춤의 문항(값 · 범위)과 답
    기록 = _읽기(os.path.join(폴더, "멈춤기록.json"))
    if isinstance(기록, dict):
        멈 = [x for x in (기록.get("멈춤") or []) if isinstance(x, dict)]
        답들 = [x for x in (기록.get("답") or []) if isinstance(x, dict)]
        if 멈:
            끝 = 멈[-1]
            시각 = "%s" % 끝.get("시각", "")

            def 답있나(문):
                대 = {("%s" % y).replace("A-", "").strip() for y in (문.get("대상") or [])} if isinstance(문.get("대상"), list) else set()
                이름 = ("%s" % (문.get("이름") or "")).strip()
                for a in 답들:
                    if ("%s" % a.get("시각", "")) < 시각:
                        continue
                    a대 = a.get("대상")
                    a대 = {("%s" % y).replace("A-", "").strip() for y in (a대 if isinstance(a대, list) else ("%s" % a대).split("+"))} if a대 else set()
                    if (대 and a대 and 대 & a대) or (이름 and ("%s" % a.get("노드", "")).strip() == 이름) or (이름 and 이름 in ("%s" % a.get("물음", ""))):
                        return a
                return None
            for 문 in 끝.get("문항") or []:
                if not isinstance(문, dict):
                    continue
                a = 답있나(문)
                종류 = "범위 문항" if (문.get("종류") == "범위" or 문.get("범위") is None and 문.get("참고범위")) else "멈춤 문항"
                넣기("멈춤기록", 종류, "%s — %s" % (문.get("이름") or 문.get("대상"), (문.get("뼈대") or {}).get("원인") or ""),
                    "+".join("%s" % y for y in (문.get("대상") or [])) if isinstance(문.get("대상"), list) else None,
                    ("답(%s) — %s" % (a.get("시각"), ("%s" % a.get("답"))[:60])) if a else None)

    # ── 동인 지도
    지도 = _읽기(os.path.join(폴더, "동인지도.json"))
    진단 = _읽기(os.path.join(폴더, "동인진단.json"))
    if 지도 is None and isinstance(진단, dict):
        넣기("동인 지도", "지도 없음", "동인진단이 돈 회차인데 동인 지도(_raw/동인지도.json)가 없다 — `동인지도짓기.py` 로 v0 를 짓는다")
    elif isinstance(지도, dict):
        for x in 지도.get("노드") or []:
            if isinstance(x, dict) and ("%s" % x.get("노드", "")).startswith("원가줄") and x.get("선택") != "해당 없음":
                확 = x.get("성격확정") if isinstance(x.get("성격확정"), dict) else {}
                넣기("동인 지도", "성격 확정 대기", "%s — 성격(변동 · 고정 · 준변동) 판정을 사람이 확정하지 않았다" % x.get("노드"),
                    x.get("노드"), ("%s(%s)" % (확.get("방식"), 확.get("시각"))) if 확.get("누가") == "사람" else None)

    # ── 기본값 딱지 — 사람 답 대신 둔 기본값
    for 블록 in ("근거", "원천근거", "WACC근거"):
        for 번, v in ((가정.get(블록) or {}).items() if isinstance(가정.get(블록), dict) else ()):
            글 = json.dumps(v, ensure_ascii=False)
            if 기본값딱지.search(글):
                넣기("가정 %s" % 블록, "기본값 확인 대기", "%s.%s — 사람 답 대신 기본값을 두었다: %s" % (블록, 번, 글[:120]), "%s" % 번)

    # ── 기본값 의심 — 판단 칸 · 문항 대상인데 근거가 [판단] 이고 답이 없다(S10R1-N3 — 자체검사 몫이 아니다: 게이트 ⑤ 도 센다)
    for 번, 첫, 출 in 기본값의심(가정, 가정경로, 원천폴더):
        넣기("가정 근거", "기본값 의심", "근거.%s — %s인데 근거가 [판단] 이고 멈춤 답이 없다(사람 답 없이 둔 값이면 근거 첫 칸을 [기본값] 으로): %s"
            % (번, 출, 첫[:80]), 번)

    # ── 검증 갈래 V1~V4 — 「사람이 볼 것」
    for n in (1, 2, 3, 4):
        p = os.path.join(폴더, "검증_V%d.md" % n)
        if not os.path.exists(p):
            continue
        글 = io.open(p, encoding="utf-8", errors="replace").read()
        m = re.search(r"#+\s*사람이 볼 것[^\n]*\n(.*?)(?=\n#+\s|\Z)", 글, re.S)
        if not m:
            continue
        for l in m.group(1).split("\n"):
            l = l.strip()
            if re.match(r"^([-*]|\d+[.)])\s+", l):
                넣기("검증 V%d" % n, "사람이 볼 것", re.sub(r"^([-*]|\d+[.)])\s+", "", l))

    # ── 모순 장부 critical
    장 = _읽기(os.path.join(폴더, "모순장부.json"))
    if isinstance(장, dict):
        for x in 장.get("항목") or []:
            if isinstance(x, dict) and ("%s" % x.get("등급", "")).lower() == "critical" and x.get("상태") != "해소" and not x.get("승격"):
                넣기("모순 장부", "critical", "%s — %s" % (x.get("ID") or x.get("id") or "?", x.get("내용") or x.get("요약") or ""), x.get("ID") or x.get("id"))
    return 줄


def 장부쓰기(줄, 낼, 가정경로):
    옛 = _읽기(낼) if os.path.exists(낼) else None
    사유 = {x["키"]: x.get("사유") for x in ((옛 or {}).get("줄") or []) if isinstance(x, dict) and x.get("사유")}
    for x in 줄:
        if 사유.get(x["키"]):
            x["사유"] = 사유[x["키"]]
    미결 = [x for x in 줄 if x["상태"] == "미결" and not x.get("사유")]
    장부 = {"판": "넘긴몫-1", "작성": datetime.datetime.now().isoformat(timespec="seconds"), "가정": os.path.basename(가정경로),
          "요약": {"전체": len(줄), "미결": len(미결), "사유로닫힘": sum(1 for x in 줄 if x["상태"] == "미결" and x.get("사유")),
                 "닫힘": sum(1 for x in 줄 if x["상태"] == "닫힘"),
                 "종류별미결": {k: sum(1 for x in 미결 if x["종류"] == k) for k in sorted({x["종류"] for x in 미결})}},
          "줄": 줄}
    os.makedirs(os.path.dirname(os.path.abspath(낼)), exist_ok=True)
    io.open(낼, "w", encoding="utf-8").write(json.dumps(장부, ensure_ascii=False, indent=1))
    return 장부


def 미결수(가정, 가정경로, 원천폴더=None, 자체검사포함=True):
    """레터 게이트 ⑤ · 8단계가 부른다 — (미결 수, 미결 줄 목록). 장부 파일의 사유를 읽어 닫는다(쓰지 않는다)."""
    줄 = 모으기(가정, 가정경로, 원천폴더, 자체검사포함)
    낼 = os.path.join(원천폴더 or os.path.join(os.path.dirname(os.path.abspath(가정경로)), "_raw"), 파일이름)
    사유 = {x["키"]: x.get("사유") for x in (((_읽기(낼) or {}).get("줄")) or []) if isinstance(x, dict) and x.get("사유")}
    미결 = [x for x in 줄 if x["상태"] == "미결" and not 사유.get(x["키"])]
    return len(미결), 미결


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False, description="넘긴 몫 장부(S10-02)")
    ap.add_argument("가정")
    ap.add_argument("--원천폴더", default=None)
    ap.add_argument("--보기", action="store_true", help="쓰지 않고 보기만")
    ap.add_argument("--사유", nargs=2, metavar=("키", "사유"), help="그 줄을 사유와 함께 닫는다")
    a = ap.parse_args()
    try:
        가정 = json.load(io.open(a.가정, encoding="utf-8"))
    except (OSError, ValueError) as e:
        sys.stderr.write("가정을 못 읽었습니다: %s\n" % e)
        sys.exit(입력오류)
    낼 = os.path.join(a.원천폴더 or os.path.join(os.path.dirname(os.path.abspath(a.가정)), "_raw"), 파일이름)
    줄 = 모으기(가정, a.가정, a.원천폴더)
    if a.사유:
        k, 글 = a.사유
        if not any(x["키"] == k for x in 줄):
            sys.stderr.write("키 %s 인 줄이 지금 장부에 없습니다\n" % k)
            sys.exit(입력오류)
        옛 = _읽기(낼) or {"줄": []}
        for x in 줄:
            if x["키"] == k:
                x["사유"] = "%s (%s)" % (글, datetime.date.today().isoformat())
        사유 = {x["키"]: x.get("사유") for x in (옛.get("줄") or []) if isinstance(x, dict) and x.get("사유")}
        for x in 줄:
            if x["키"] != k and 사유.get(x["키"]):
                x["사유"] = 사유[x["키"]]
        io.open(낼, "w", encoding="utf-8").write(json.dumps({"줄": 줄}, ensure_ascii=False))
    if a.보기:                                       # S10R1-N3 — 보기도 장부의 사유를 읽어 닫힌 줄을 미결로 세지 않는다
        옛사유 = {x["키"]: x.get("사유") for x in (((_읽기(낼) or {}).get("줄")) or []) if isinstance(x, dict) and x.get("사유")}
        for x in 줄:
            if 옛사유.get(x["키"]):
                x["사유"] = 옛사유[x["키"]]
        미 = [x for x in 줄 if x["상태"] == "미결" and not x.get("사유")]
        장부 = {"요약": {"전체": len(줄), "미결": len(미), "사유로닫힘": sum(1 for x in 줄 if x["상태"] == "미결" and x.get("사유")),
                       "종류별미결": {k: sum(1 for x in 미 if x["종류"] == k) for k in sorted({x["종류"] for x in 미})}}, "줄": 줄}
    else:
        장부 = 장부쓰기(줄, 낼, a.가정)
    요 = 장부["요약"]
    print("넘긴 몫 — 전체 %d · 미결 %d%s%s" % (요["전체"], 요["미결"], (" · 사유로 닫힘 %d" % 요["사유로닫힘"]) if 요.get("사유로닫힘") else "",
                                        ("  → %s" % 낼) if not a.보기 else ""))
    for 종류, n in (요.get("종류별미결") or {}).items():
        print("  %s %d" % (종류, n))
    for x in [x for x in 장부["줄"] if x["상태"] == "미결" and not x.get("사유")][:40]:
        print("  [%s] %s · %s — %s" % (x["키"], x["출처"], x["종류"], x["글"][:150]))
    sys.exit(통과 if 요["미결"] == 0 else 발견)


if __name__ == "__main__":
    main()

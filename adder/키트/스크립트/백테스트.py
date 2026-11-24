# -*- coding: utf-8 -*-
"""백테스트 — 여러 회사의 레터를 한 번에 재는 묶음 측정(구조 검사 · 닮음 · 교열 지적 · 지적 대장 회귀).

평가는 다시 돌리지 않고 레터 단계만 새 판으로 다시 지은 뒤, 그 묶음을 그때까지 지은 레터 전체와 맞대어 잰다.
값이 그대로이므로 지표의 변화는 문장의 변화다.

  명부(JSON) — {"회사": [줄, …]} 또는 [줄, …]. 줄 = {
      "이름"      표에 쓰는 이름(줄마다 달라야 한다 — 같은 회사의 옛 판 · 새 판이면 「이름@판」 처럼)
      "회사"      같은 회사를 묶는 열쇠(비우면 이름). 같은 회사의 다른 판 레터는 닮음을 잴 때 서로 맞대지 않는다
      "레터"      최종 레터 .md(상대 경로는 명부 파일 기준)
      "폴더"      회사 폴더(교열 대장을 찾는다 · 비우면 레터 곁)
      "업종" · "관할" · "매출방식" · "판" · "묶음"   표에 싣고 닮음 · 고르기에 쓴다
      "말뭉치"    거짓이면 재기만 하고 다른 레터의 말뭉치에는 넣지 않는다(옛 꼴 · 같은 회사의 다른 회차)
  }

  재는 것(레터마다)
    구조 검사       `레터구조.지표` 의 항목 값(① ~ ⑬)
    닮음            말뭉치 = 명부의 다른 회사 레터(--말뭉치 같은판 이면 판이 같은 레터만)
                    본편 · 본편 다른 업종 · 3분 · 3분 다른 업종 · 절 첫 문장(본편 「## n.」 절의 첫 산문 문장이 다른 레터의 절 첫 문장과 구조가 같은 비율)
                    — 같은 업종끼리는 쟁점과 논리가 같아 닮음이 높으므로 기준은 다른 업종 값으로 본다
    교열 지적       회사 폴더 `_기록/교열대장.json` 의 마지막 묶음 — 1회 표시 · 만 자당 · 유형 분포 / 두 번 고친 뒤 남은 수
                    (`_raw/교열/남은목록.json` 이 있으면 그 셈 · 없으면 대장 마지막 회의 「남은」)
    대장 회귀       지적 대장(사람이 레터를 읽고 고친 문장 · 6칸 표: 날짜 · 회사 · 절 · 원문 · 고친 문장 · 유형)의 원문과 구조가 같은 문장
  기준(잠정 · 첫 묶음 뒤 확정)  `기준` — 막음 지표 · 본편 닮음 · 3분 닮음(다른 업종) · 교열 남은. 넘은 칸은 표에 「!」
  낸 것          표(마크다운) · JSON. `--기록 <파일>` 이면 묶음 한 줄을 더한다(판 · 묶음 · 회사 · 지표 요약 · 기준 넘은 레터 수)
  고르기         사람이 읽을 두 편 — 지표가 가장 나쁜 레터 하나와 나머지 가운데 하나(이름 · 묶음의 해시 — 무작위와 같되 다시 돌려도 같다)

    python 스크립트/백테스트.py 명부.json [--묶음 1] [--말뭉치 전체|같은판] [--대장 지적대장.md] [-o 결과.json] [--표 결과.md] [--기록 묶음기록.md] [--판 1.1.18]
    종료 코드 0 잼(판정은 사람 몫 — 기준 숫자는 잠정) · 2 명부 오류(이름이 겹치거나 레터가 없다)

회사 · 업종 이름은 이 모듈에 없다(명부가 준다).
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:                                            # noqa: BLE001
    pass
여기 = os.path.dirname(os.path.abspath(__file__))
if 여기 not in sys.path:
    sys.path.insert(0, 여기)
import 레터구조 as R  # noqa: E402

막음키 = ("②", "③", "⑧", "⑨")                               # 확정본 5절 — 막음 지표(잠정) · ④3분 은 닮음 칸에서 본다
보일키 = ("①", "②", "③", "④본편", "④3분", "⑤", "⑥", "⑦", "⑧", "⑨", "⑩", "⑪", "⑫", "⑬")
기준 = {"막음": 0, "본편": 15, "삼분다른": 20, "교열남은": 0}       # 잠정 기준 — 첫 묶음 뒤 확정한다


class 명부오류(Exception):
    pass


def 명부읽기(p):
    """명부 JSON → [줄](경로는 절대 경로로 · 회사 · 폴더를 채운다). 이름이 겹치면 명부오류."""
    d = json.load(io.open(p, encoding="utf-8"))
    뿌 = os.path.dirname(os.path.abspath(p))
    낸, 본 = [], set()
    for x in (d.get("회사") if isinstance(d, dict) else d) or []:
        x = dict(x)
        if not x.get("이름"):
            raise 명부오류("이름이 없는 줄: %s" % json.dumps(x, ensure_ascii=False)[:120])
        if x["이름"] in 본:
            raise 명부오류("이름이 겹친다: %s" % x["이름"])
        본.add(x["이름"])
        for k in ("레터", "폴더"):
            if x.get(k) and not os.path.isabs(x[k]):
                x[k] = os.path.normpath(os.path.join(뿌, x[k]))
        if not x.get("폴더") and x.get("레터"):
            x["폴더"] = os.path.dirname(x["레터"])
        x.setdefault("회사", x["이름"])
        낸.append(x)
    return 낸


def 절첫문장(d):
    """레터구조.읽기 결과 → [(줄, 문장)] — 본편 「## n.」 절마다 첫 산문 문장 하나."""
    줄들 = d["줄들"]
    머 = [i for i, x in enumerate(줄들, 1) if re.match(r"^## \d+\. ", x)]
    문 = R.문장들(d["본편"])
    낸 = []
    for k, h in enumerate(머):
        끝 = 머[k + 1] if k + 1 < len(머) else len(줄들) + 1
        첫 = next(((n, s) for n, s in 문 if h < n < 끝), None)
        if 첫:
            낸.append(첫)
    return 낸


def 교열(폴더):
    """회사 폴더 → {"표시1", "만자당1", "유형1", "남은2", "남은구조", "회수", "출처"} — 교열 대장의 마지막 묶음(같은 회사의 마지막 레터).
    대장이 없으면 {}(교열 단계 전의 판)."""
    p = os.path.join(폴더 or "", "_기록", "교열대장.json")
    if not os.path.isfile(p):
        return {}
    try:
        회 = (json.load(io.open(p, encoding="utf-8")).get("회차") or [])
    except Exception:                                        # noqa: BLE001
        return {}
    if not 회:
        return {}
    시 = len(회) - 1
    while 시 > 0 and (회[시].get("회") or 1) > 1 and (회[시 - 1].get("회") or 1) < (회[시].get("회") or 1):
        시 -= 1                                               # 마지막 묶음의 1회 자리
    첫, 끝 = 회[시], 회[-1]
    낸 = {"표시1": 첫.get("표시"), "만자당1": 첫.get("만자당"), "유형1": 첫.get("유형") or {}, "회수": 끝.get("회"),
          "남은2": 끝.get("남은"), "출처": "대장"}
    남p = os.path.join(폴더, "_raw", "교열", "남은목록.json")
    if os.path.isfile(남p):
        try:
            셈 = json.load(io.open(남p, encoding="utf-8")).get("셈") or {}
            낸.update({"남은2": 셈.get("표시"), "남은구조": 셈.get("구조"), "출처": "남은목록"})
        except Exception:                                    # noqa: BLE001
            pass
    return 낸


def 대장읽기(p):
    """지적 대장(마크다운 6칸 표) → [{"날짜", "회사", "절", "원문", "고친", "유형"}]. 머리 · 가름 줄과 원문이 빈 줄은 뺀다."""
    if not p or not os.path.isfile(p):
        return []
    낸 = []
    for t in io.open(p, encoding="utf-8").read().split("\n"):
        t = t.strip()
        if not t.startswith("|"):
            continue
        c = [x.strip() for x in re.split(r"(?<!\\)\|", t.strip("|"))]
        if len(c) < 6 or c[0] == "날짜" or re.match(r"^:?-+:?$", c[0]) or not c[3]:
            continue
        낸.append({"날짜": c[0], "회사": c[1], "절": c[2], "원문": c[3].replace("\\|", "|"), "고친": c[4].replace("\\|", "|"), "유형": c[5]})
    return 낸


def _중앙(xs):
    xs = sorted(v for v in xs if isinstance(v, (int, float)))
    return None if not xs else xs[len(xs) // 2]


def _닮음비(문, 남구):
    if not 문:
        return None
    return round(sum(1 for _n, s in 문 if R.구조(s) in 남구) * 100 / len(문))


def 재기(명부, 묶음=None, 대장=(), 말뭉치="전체"):
    """→ [{"이름", "회사", "묶음", "업종", "관할", "매출방식", "판", "지표": {키: 값}, "비율": {키: %}, "닮음": {…}, "교열": {…},
    "대장회귀", "넘음": [기준 키], "말뭉치"}]. 말뭉치 — 「전체」(명부의 다른 회사 레터 모두) · 「같은판」(판이 같은 레터만)."""
    줄 = {x["이름"]: x for x in 명부}
    글, 읽 = {}, {}
    for x in 명부:
        if x.get("레터") and os.path.isfile(x["레터"]):
            글[x["이름"]] = io.open(x["레터"], encoding="utf-8").read()
            읽[x["이름"]] = R.읽기(글[x["이름"]])
    첫 = {k: 절첫문장(d) for k, d in 읽.items()}
    대장구 = {R.구조(t) for r in 대장 if r.get("원문") for _n, t in R.문장들([(0, r["원문"])])}   # 원문을 레터와 같은 셈으로 문장마다
    낸 = []
    for x in 명부:
        k = x["이름"]
        if k not in 글 or (묶음 is not None and "%s" % x.get("묶음") != "%s" % 묶음):
            continue

        def 넣나(n):
            y = 줄[n]
            return (n != k and y.get("회사") != x.get("회사") and y.get("말뭉치", True) is not False
                    and (말뭉치 != "같은판" or y.get("판") == x.get("판")))
        남 = [n for n in 글 if 넣나(n)]
        다른 = [n for n in 남 if (줄[n].get("업종") or "?") != (x.get("업종") or "!")]
        값 = R.지표(글[k], 말뭉치=[(n, 읽[n]) for n in 남])
        항 = 값["항목"]
        지 = {키: (항[키].get("값") if 키 in 항 else None) for 키 in 보일키}
        비 = {키: 항[키].get("비율") for 키 in 보일키 if 키 in 항 and 항[키].get("비율") is not None}
        다른본 = 다른삼 = None
        if 다른:
            v2 = R.지표(글[k], 말뭉치=[(n, 읽[n]) for n in 다른])["항목"]
            다른본 = (v2.get("④본편") or {}).get("비율")
            다른삼 = (v2.get("④3분") or {}).get("비율")
        남첫 = {R.구조(s) for n in 남 for _l, s in 첫[n]}
        회귀 = [s for _n, s in R.문장들(읽[k]["본편"]) if R.구조(s) in 대장구]
        교 = 교열(x.get("폴더"))
        r = {"이름": k, "회사": x.get("회사"), "묶음": x.get("묶음"), "업종": x.get("업종"), "관할": x.get("관할"),
             "매출방식": x.get("매출방식"), "판": x.get("판"), "산문글자": 값.get("산문글자"), "문장": 값.get("문장"), "지표": 지, "비율": 비,
             "닮음": {"본편": 비.get("④본편"), "본편표설명포함": (항.get("④본편") or {}).get("표설명포함비율"), "본편다른업종": 다른본, "삼분": 비.get("④3분"), "삼분다른업종": 다른삼,
                      "절첫": _닮음비(첫[k], 남첫) if 남 else None, "절첫수": len(첫[k])},
             "교열": 교, "대장회귀": len(회귀), "대장회귀글": [s[:120] for s in 회귀[:5]], "말뭉치": len(남), "다른업종": len(다른)}
        r["넘음"] = 넘은기준(r)
        낸.append(r)
    return 낸


def 넘은기준(r):
    """잠정 기준을 넘은 칸의 이름 — 막음 지표(값 > 0) · 본편 닮음 · 3분 닮음(다른 업종) · 교열 남은."""
    넘 = [k for k in 막음키 if (r["지표"].get(k) or 0) > 기준["막음"]]
    if (r["닮음"].get("본편") or 0) > 기준["본편"]:
        넘.append("닮음본편")
    if (r["닮음"].get("삼분다른업종") or 0) > 기준["삼분다른"]:
        넘.append("닮음3분")
    if (r["교열"].get("남은2") or 0) > 기준["교열남은"]:
        넘.append("교열남은")
    return 넘


def _칸(v, 넘=False):
    s = "-" if v is None else ("%s" % v)
    return s + "!" if 넘 and v is not None else s


표머리 = ["회사", "판", "업종", "관할", "매출", "산문 글자", "②", "③", "⑧", "⑨", "닮음 본편%", "본편(표 설명 포함)%", "본편 다른 업종%", "3분%", "3분 다른 업종%",
        "절 첫 문장%", "교열 1회 만 자당", "교열 남은", "대장 회귀"]


def 표(결과):
    줄 = ["| %s |" % " | ".join(표머리), "|%s" % ("---|" * len(표머리))]
    for r in 결과:
        지, 닮, 교, 넘 = r["지표"], r["닮음"], r["교열"], set(r["넘음"])
        줄.append("| %s |" % " | ".join([
            _칸(r["이름"]), _칸(r.get("판")), _칸(r.get("업종")), _칸(r.get("관할")), _칸(r.get("매출방식")), _칸(r.get("산문글자"))]
            + [_칸(지.get(k), k in 넘) for k in 막음키]
            + [_칸(닮.get("본편"), "닮음본편" in 넘), _칸(닮.get("본편표설명포함")), _칸(닮.get("본편다른업종")), _칸(닮.get("삼분")), _칸(닮.get("삼분다른업종"), "닮음3분" in 넘),
               _칸(닮.get("절첫")), _칸(교.get("만자당1")), _칸(교.get("남은2"), "교열남은" in 넘), _칸(r["대장회귀"])]))
    if 결과:
        뽑 = ([lambda r: r.get("산문글자")] + [(lambda k: lambda r: r["지표"].get(k))(k) for k in 막음키]
             + [(lambda k: lambda r: r["닮음"].get(k))(k) for k in ("본편", "본편표설명포함", "본편다른업종", "삼분", "삼분다른업종", "절첫")]
             + [lambda r: r["교열"].get("만자당1"), lambda r: r["교열"].get("남은2"), lambda r: r["대장회귀"]])
        줄.append("| **중앙값** | | | | | %s |" % " | ".join(_칸(_중앙([f(r) for r in 결과])) for f in 뽑))
    return 줄


def 요약(결과):
    """묶음 한 줄의 재료 — 합 · 중앙값 · 기준을 넘은 레터 수."""
    return {"회사": [r["이름"] for r in 결과],
            "막음합": {k: sum(r["지표"].get(k) or 0 for r in 결과) for k in 막음키},
            "닮음본편중앙": _중앙([r["닮음"].get("본편") for r in 결과]),
            "본편다른업종중앙": _중앙([r["닮음"].get("본편다른업종") for r in 결과]),
            "삼분다른업종중앙": _중앙([r["닮음"].get("삼분다른업종") for r in 결과]),
            "절첫중앙": _중앙([r["닮음"].get("절첫") for r in 결과]),
            "교열남은합": sum(r["교열"].get("남은2") or 0 for r in 결과),
            "대장회귀합": sum(r["대장회귀"] for r in 결과),
            "기준넘은레터": sum(1 for r in 결과 if r["넘음"])}


def 고르기(결과, 씨=""):
    """사람이 읽을 두 편 → [무작위, 최악] — 최악은 막음 지표 합 · 3분 닮음(다른 업종) · 본편 닮음 · 교열 남은의 점수가 가장 큰 레터,
    무작위는 나머지 가운데 (씨 + 이름) 해시가 가장 작은 레터(다시 돌려도 같다 · 씨에 묶음 번호를 주면 묶음마다 달라진다)."""
    if not 결과:
        return []

    def 나쁨(r):
        return (sum(r["지표"].get(k) or 0 for k in 막음키) + (r["닮음"].get("삼분다른업종") or 0) / 10.0
                + (r["닮음"].get("본편") or 0) / 5.0 + (r["교열"].get("남은2") or 0))
    최악 = max(결과, key=lambda r: (나쁨(r), r["이름"]))
    남 = [r for r in 결과 if r is not 최악]
    무 = min(남, key=lambda r: hashlib.sha256(("%s|%s" % (씨, r["이름"])).encode("utf-8")).hexdigest()) if 남 else None
    return [x for x in (무, 최악) if x]


def 기록줄(판, 묶음, 결과):
    s = 요약(결과)
    return "| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
        판 or "-", 묶음 or "전체", " · ".join(s["회사"]), " · ".join("%s %s" % kv for kv in s["막음합"].items()),
        _칸(s["닮음본편중앙"]), _칸(s["본편다른업종중앙"]), _칸(s["삼분다른업종중앙"]), _칸(s["절첫중앙"]), s["교열남은합"], s["대장회귀합"],
        "%d / %d" % (s["기준넘은레터"], len(결과)))


기록머리 = ("| 판 | 묶음 | 회사 | 막음 지표 합 | 닮음 본편 중앙% | 본편 다른 업종 중앙% | 3분 다른 업종 중앙% | 절 첫 문장 중앙% | 교열 남은 합 | 대장 회귀 합 | 기준 넘은 레터 |\n"
          "|---|---|---|---|---|---|---|---|---|---|---|\n")


def main(argv=None):
    ap = argparse.ArgumentParser(description="백테스트 — 레터 묶음 측정")
    ap.add_argument("명부")
    ap.add_argument("--묶음", default=None, help="이 묶음의 회사만 잰다(말뭉치는 명부 전체)")
    ap.add_argument("--말뭉치", default="전체", choices=("전체", "같은판"))
    ap.add_argument("--대장", default=None, help="지적 대장(.md · 6칸 표 — 사람이 고친 문장)")
    ap.add_argument("-o", "--출력", default=None)
    ap.add_argument("--표", default=None)
    ap.add_argument("--기록", default=None, help="묶음 기록(.md)에 한 줄을 더한다")
    ap.add_argument("--판", default=None)
    a = ap.parse_args(argv)
    try:
        명 = 명부읽기(a.명부)
    except 명부오류 as e:
        print("명부 오류 — %s" % e)
        return 2
    없 = [x["이름"] for x in 명 if (a.묶음 is None or "%s" % x.get("묶음") == "%s" % a.묶음) and not (x.get("레터") and os.path.isfile(x["레터"]))]
    if 없:
        print("명부 오류 — 레터 파일이 없다: %s" % " · ".join(없))
        return 2
    결과 = 재기(명, a.묶음, 대장읽기(a.대장), a.말뭉치)
    줄 = 표(결과)
    고 = 고르기(결과, a.묶음 or "")
    줄 += ["", "말뭉치 %s · 잠정 기준 막음 %d · 본편 닮음 %d%% · 3분 닮음(다른 업종) %d%% · 교열 남은 %d — 넘은 칸 「!」"
           % (a.말뭉치, 기준["막음"], 기준["본편"], 기준["삼분다른"], 기준["교열남은"]),
           "사람이 읽을 두 편 — 무작위 %s · 지표가 가장 나쁜 %s" % (고[0]["이름"] if 고 else "-", 고[-1]["이름"] if len(고) > 1 else "-")]
    print("\n".join(줄))
    if a.출력:
        json.dump({"판": a.판, "묶음": a.묶음, "말뭉치": a.말뭉치, "기준": 기준, "요약": 요약(결과), "결과": 결과,
                   "읽을": [r["이름"] for r in 고]}, io.open(a.출력, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    if a.표:
        io.open(a.표, "w", encoding="utf-8").write("\n".join(줄) + "\n")
    if a.기록:
        새 = not os.path.isfile(a.기록) or not io.open(a.기록, encoding="utf-8").read().strip()
        with io.open(a.기록, "a", encoding="utf-8") as f:
            if 새:
                f.write(기록머리)
            f.write(기록줄(a.판, a.묶음, 결과) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())

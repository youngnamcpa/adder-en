# -*- coding: utf-8 -*-
"""분석_열쓰임 — 줄 무늬 명세가 시간축 열을 어떻게 부르는지 센다(기간 열을 가정 파일이 정하게 될 때 고칠 곳의 수).

  · 무늬·글·값의 열 구간 열쇠(시간축이 있는 시트): 묶음 이름(늘고 준다) / 묶음 끝에 닿는 구간(E2~예측) / 열 ID 를 못 박은 것
  · 수식 속 참조의 열(모든 시트의 수식 — 가리키는 줄의 시트를 기준으로 가른다):
      같은 열(@.) · 이웃 열(@<-1>·@<+1>) · 묶음(@예측 · @예측.끝) — 열 수가 바뀌어도 따라간다
      쓰임의 별칭(@판정 · @값 · @기준 …) — 시간축이 아니다
      시간축 열 ID 를 못 박은 것(@H3 · @E1 · @TV …) — 기간 열 수가 바뀔 때 손볼 자리

쓰기:  python 분석_열쓰임.py [줄 무늬 명세 폴더]
"""
import sys
import os
import re
import json
from collections import Counter, OrderedDict

import 줄무늬

_re참 = re.compile(r"\[\$?([^\]\[\s*]+)(?:[ \t]+[^\]\[]*)?\]@!?\$?(\.(?![첫끝])|<[+-]\d+>|[A-Za-z가-힣_][A-Za-z0-9가-힣_]*(?:\.[첫끝])?)")
_re글 = re.compile(r'"(?:[^"]|"")*"')


def 세기(폴더):
    with open(os.path.join(폴더, "책.json"), encoding="utf-8") as f:
        책 = json.load(f)
    시트 = OrderedDict((sid, 줄무늬.시트읽기(os.path.join(폴더, sid + ".jsonl"))) for sid in 책["시트순서"])
    시간열, 묶음, 쓰임표, 줄쓰임, 줄시트 = {}, {}, {}, {}, {}
    for sid, (머리, 줄들) in 시트.items():
        축 = set(머리.get("축", []))
        시간열[sid] = {c["id"] for c in 머리["열"] if c.get("종류") in 축}
        묶음[sid] = set(머리.get("묶음", {}))
        쓰임표[sid] = 머리.get("쓰임", {})
        for 줄 in 줄들:
            줄시트[줄["id"]] = sid
            줄쓰임[줄["id"]] = set(쓰임표[sid].get(줄.get("쓰임"), {}))
    열쇠수, 참조수, 못박은, 못박은곳 = Counter(), Counter(), Counter(), OrderedDict()
    for sid, (머리, 줄들) in 시트.items():
        for 줄 in 줄들:
            if 시간열[sid]:
                for 갈래 in ("무늬", "글", "값"):
                    for 키 in (줄.get(갈래) or {}):
                        낱 = 키.split("~")
                        if any(x in 줄쓰임[줄["id"]] for x in 낱):
                            열쇠수["쓰임의 별칭"] += 1
                        elif len(낱) == 1 and 낱[0] in 묶음[sid]:
                            열쇠수["묶음 이름(늘고 준다)"] += 1
                        elif len(낱) == 2 and 낱[1] in 묶음[sid] and 낱[0] in 시간열[sid]:
                            열쇠수["시간축 열 ID ~ 묶음 끝(끝은 는다)"] += 1
                        elif any(x in 시간열[sid] for x in 낱):
                            열쇠수["시간축 열 ID 를 못 박음"] += 1
                            못박은["열쇠 " + 키] += 1
                        else:
                            열쇠수["시간축 아닌 열"] += 1
            글들 = list((줄.get("무늬") or {}).values())
            글들 += [줄[k] for k in ("이름", "단위") if isinstance(줄.get(k), str) and 줄[k].startswith("=")]
            for 글 in 글들:
                for m in _re참.finditer(_re글.sub('""', 글)):
                    rid, 낱 = m.group(1), m.group(2)
                    대상 = 줄시트.get(rid) or sid
                    if 낱 == ".":
                        참조수["같은 열 @."] += 1
                    elif 낱[0] == "<":
                        참조수["이웃 열 @<-1> · @<+1>"] += 1
                    elif 낱 in 묶음[대상] or 낱[:-2] in 묶음[대상]:
                        참조수["묶음(@예측 · @예측.끝 …)"] += 1
                    elif 낱 in 줄쓰임.get(rid, ()) or (낱 not in 시간열[대상] and any(낱 in m2 for m2 in 쓰임표[대상].values())):
                        참조수["쓰임의 별칭(@판정 · @값 · @기준 …)"] += 1
                    elif 낱 in 시간열[대상]:
                        참조수["시간축 열 ID 를 못 박음"] += 1
                        못박은["참조 @" + 낱] += 1
                        못박은곳.setdefault(낱, Counter())["%s → %s" % (sid, 대상)] += 1
                    else:
                        참조수["시간축 아닌 열 ID"] += 1
    return {"열 구간 열쇠": dict(열쇠수), "수식 속 참조의 열": dict(참조수),
            "못 박은 열 ID 별": dict(못박은.most_common()),
            "못 박은 참조 — 수식의 시트 → 가리키는 시트": {k: dict(v.most_common()) for k, v in 못박은곳.items()}}


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    여기 = os.path.dirname(os.path.abspath(__file__))
    print(json.dumps(세기(sys.argv[1] if len(sys.argv) > 1 else os.path.join(여기, "줄명세")), ensure_ascii=False, indent=1))

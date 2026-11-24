# -*- coding: utf-8 -*-
"""**키 이름 점검(㊽)** — 키트 문서에 엔진 v13 에서 없어진 키가 「키 꼴」로 남았나 본다. 가정이 아니라 키트를 보는 점검이다.

    python 스크립트/키이름점검.py            # 걸린 곳 목록 · 걸리면 종료 코드 1
    python 스크립트/키이름점검.py --뿌리 키트   # 다른 키트 사본

없어진 키의 정본은 `엔진/스키마.py` 의 표(없어진최상위 · 없어진메타 · 없어진스위치)다 — 이 파일에 키 이름을 적지 않는다.
「키 꼴」 = JSON 키(`"<키>":`) · 백틱 한 덩이(`` `<키>` ``) · 점 경로(`스위치.<키>` · `메타.<키>` · 최상위 키 + 「.」 + 번호나 하위 키).
문장 속의 보통 낱말(최상위 키와 글자가 같은 일반 명사)은 걸지 않는다. 그 줄에 「없어진」 · 「옛 키」 · 「옛 판」 · 「v12」 · 「이전 도구」가 있으면 옛 키를 설명하는
줄로 보고 건너뛴다(이전 · 대응표). 줄 머리가 다른 자리를 선언하면(`관측.과거사이클` 같은 점 경로 · `과거_사이클[]` 같은 목록 선언) 그 줄의 키 꼴은
그 자리의 하위 칸이라 없어진 최상위 키와 글자가 같아도 걸지 않는다 — 머리가 없어진 키 자신(옛 블록의 하위 경로)이면 건다.

읽는 문서 — CLAUDE.md · 모델링_프롬프트_집대성.md · 가정_스키마.md · 스캐폴드_구조.md · .claude/갈래 · .claude/skills · .claude/agents · .claude/commands 의 .md.
"""
from __future__ import annotations

import argparse
import glob
import io
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

설명줄re = re.compile(r"없어진|옛\s*키|옛\s*판|옛\s*꼴|v12|이전\s*도구|걷었|걷은|대신하는\s*자리|가정이전")


def 키표():
    """[(키, 무리, 대신)] — 엔진/스키마.py 의 없어진 키 표에서."""
    from 엔진 import 스키마 as S                          # noqa: PLC0415
    낸 = []
    for 무리, 표 in (("최상위", S.없어진최상위), ("메타", S.없어진메타), ("스위치", S.없어진스위치)):
        for k, v in 표.items():
            낸.append((k, 무리, v))
    return 낸


def 문서들(뿌리):
    낸 = [os.path.join(뿌리, n) for n in ("CLAUDE.md", "모델링_프롬프트_집대성.md", "가정_스키마.md", "스캐폴드_구조.md")]
    for 아래 in ("갈래", "skills", "agents", "commands"):
        낸 += glob.glob(os.path.join(뿌리, ".claude", 아래, "**", "*.md"), recursive=True)
    return [p for p in 낸 if os.path.exists(p)]


def 패턴(키, 무리):
    k = re.escape(키)
    꼴 = [r'"%s"\s*:' % k, r"`%s`" % k]
    if 무리 == "스위치":
        꼴.append(r"스위치\.%s(?![가-힣A-Za-z0-9])" % k)
    elif 무리 == "메타":
        꼴.append(r"메타\.%s(?![가-힣A-Za-z0-9])" % k)
    else:
        # 파일 이름(`연장.py` · `스크립트/정상화.json` …)은 키가 아니다 — 확장자로 끝나는 자리와 경로 안의 이름은 뺀다(S8 개선 1 — `연장.py` 가 옛 키 「연장」으로 걸렸다)
        꼴.append(r"(?<![가-힣A-Za-z0-9./])%s\.(?!(?:py|json|md|txt|csv|xlsx|html)(?![A-Za-z0-9]))(?:[0-9]+|[가-힣A-Za-z]+)(?![가-힣])" % k)
    return re.compile("|".join(꼴))


# 줄 머리가 다른 자리를 선언하는 꼴 — 표 칸 첫머리의 백틱 점 경로(`관측.과거사이클`) · 목록 선언(과거_사이클[]). 그 줄의 키 꼴은 그 자리의
# 하위 칸(목록 한 줄의 칸)이라, 가정 최상위에서 없어진 키와 글자가 같아도 그 키가 아니다(요건판 3 의 관측 칸 「증설」이 그 예)
_자리머리re = re.compile(r"^\s*(?:\|\s*)?(?:`([가-힣A-Za-z_]+)\.[^`\s]+`|([가-힣A-Za-z_][가-힣A-Za-z_0-9]*)\[\])")


def 하위칸줄(줄, 없는키=()):
    """줄이 다른 자리의 하위 칸을 선언하는가 — 머리 자리가 없어진 최상위 키 자신(옛 블록의 하위 경로)이면 아니다."""
    m = _자리머리re.match(줄)
    if not m:
        return False
    머리 = m.group(1) or m.group(2)
    return 머리 not in 없는키


def 점검(뿌리=None):
    """→ (걸린 곳 [{파일, 줄, 키, 대신}], 본 문서 수)."""
    뿌리 = 뿌리 or os.path.dirname(여기)
    표 = [(k, 무리, v, 패턴(k, 무리)) for k, 무리, v in 키표()]
    없는키 = {k for k, 무리, _v in 키표() if 무리 == "최상위"}
    걸린, 파일들 = [], 문서들(뿌리)
    for p in 파일들:
        try:
            줄들 = io.open(p, encoding="utf-8", errors="replace").read().split("\n")
        except OSError:
            continue
        for n, 줄 in enumerate(줄들, start=1):
            if 설명줄re.search(줄):
                continue
            하위 = 하위칸줄(줄, 없는키)
            for k, 무리, v, r in 표:
                if 무리 == "최상위" and 하위:                 # 다른 자리의 하위 칸을 선언하는 줄 — 같은 글자라도 가정 최상위 키가 아니다
                    continue
                if r.search(줄):
                    걸린.append({"파일": os.path.relpath(p, 뿌리).replace("\\", "/"), "줄": n, "키": "%s.%s" % (무리, k) if 무리 != "최상위" else k,
                               "대신": v, "글": 줄.strip()[:160]})
    return 걸린, len(파일들)


_값머리 = re.compile(r'"([^"\n]{1,30})"\s*:\s*(\{|\[|"(?:…|해당 없음|확인 불가)?|true|false|null|-?[0-9])')


def _꼴(c):
    if c.startswith('"') and len(c) > 1:           # 「"…"」 자리표시 · 「"해당 없음"」 · 「"확인 불가"」 — 어느 꼴과도 맞는다(스키마 — 값 자리에 둘을 적을 수 있다)
        return "null"
    return {"{": "사전", "[": "목록", '"': "글", "t": "참거짓", "f": "참거짓", "n": "null"}.get(c[0], "수")


def _블록키꼴(글):
    """```json 블록 안의 「"키": 값」 → {키: {꼴}} (값의 첫 글자로 꼴을 가린다 — 사전 · 목록 · 글 · 참거짓 · 수 · null)."""
    낸 = {}
    for 블 in re.findall(r"```json\n(.*?)```", 글, re.S):
        for m in _값머리.finditer(블):
            낸.setdefault(m.group(1), set()).add(_꼴(m.group(2)))
    return 낸


def 꼴점검(뿌리=None):
    """S5-21 — 갈래 지시서(.claude/갈래/*.md)의 산출 예시가 가정_스키마.md 「갈래 산출물」 절의 값 꼴과 같은가. 스키마에서 한 꼴로만 쓰인 키를
    지시서가 다른 꼴(사전 ↔ 목록 · 글 ↔ 참거짓 …)로 쓰면 걸린다(null 은 어느 꼴과도 맞는다). → [{파일, 키, 스키마, 지시서}]"""
    뿌리 = 뿌리 or os.path.dirname(여기)
    try:
        스 = io.open(os.path.join(뿌리, "가정_스키마.md"), encoding="utf-8").read().replace("\r\n", "\n")
    except OSError:
        return []
    s = 스.find("## 갈래 산출물")
    e = 스.find("\n## ", s + 10)
    절 = 스[s: e if e > 0 else None] if s >= 0 else ""
    # 절을 「### 」 꼭지로 나눈다 — 꼭지마다 산출 파일 이름(`_raw/….json` · `제약.원가[]`)과 그 꼭지의 값 꼴
    꼭지 = []
    조각들 = re.split(r"\n(?=### )", 절)
    머리꼴 = _블록키꼴(조각들[0]) if 조각들 else {}            # 공통 머리(모든 갈래 산출물 — 유형 · 확인불가 · 해당없음 …)
    for 조각 in 조각들[1:]:
        이름들 = set(re.findall(r"`(_raw/[^`]+?\.json|[가-힣A-Za-z]+\.[가-힣A-Za-z]+\[\])`", 조각.split("\n", 1)[0]))
        if 이름들:
            꼭지.append((이름들, _블록키꼴(조각)))
    걸린 = []
    for p in sorted(glob.glob(os.path.join(뿌리, ".claude", "갈래", "*.md"))):
        try:
            지글 = io.open(p, encoding="utf-8").read().replace("\r\n", "\n")
        except OSError:
            continue
        지 = _블록키꼴(지글)
        # 이 지시서의 산출 파일 = 지시서에 이름이 가장 자주 나오는 꼭지(읽기만 하는 다른 파일의 같은 키 이름과 섞지 않는다) + 공통 머리
        수들 = [(sum(지글.count(n) for n in 이름들), 이름들, 표) for 이름들, 표 in 꼭지]
        최다 = max((x[0] for x in 수들), default=0)
        정 = {k: set(v) for k, v in 머리꼴.items()}
        for 수, 이름들, 표 in 수들:
            if 최다 and 수 == 최다:
                for k, v in 표.items():
                    정.setdefault(k, set()).update(v)
        for k, 꼴들 in 지.items():
            정꼴 = 정.get(k, set()) - {"null"}
            쓴 = 꼴들 - {"null"}
            if len(정꼴) == 1 and 쓴 and not (쓴 & 정꼴):
                걸린.append({"파일": os.path.relpath(p, 뿌리).replace("\\", "/"), "키": k, "스키마": "·".join(sorted(정꼴)), "지시서": "·".join(sorted(쓴))})
    return 걸린


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False, description="㊽ 키트 문서의 없어진 키 점검")
    ap.add_argument("--뿌리", default=None, help="키트 폴더(기본: 이 스크립트의 위 폴더)")
    a = ap.parse_args()
    걸린, 본 = 점검(a.뿌리)
    for x in 걸린:
        print("%s:%d  %s → %s\n    %s" % (x["파일"], x["줄"], x["키"], x["대신"][:80], x["글"]))
    꼴 = 꼴점검(a.뿌리)
    for x in 꼴:
        print("%s  「%s」 — 스키마는 %s, 지시서 예시는 %s(갈래 산출물 값 꼴 — S5-21)" % (x["파일"], x["키"], x["스키마"], x["지시서"]))
    print("키 이름 점검 — 문서 %d개 · 걸린 곳 %d · 갈래 산출 꼴 어긋남 %d" % (본, len(걸린), len(꼴)))
    sys.exit(1 if (걸린 or 꼴) else 0)


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""원고어투 — 지난 회차의 레터 원고(평서체 ~다)를 합쇼체(~습니다)로 바꾸고, 레터의 평서체 끝을 찾는다(레터 v27 문장 단계 · 2026-11-11).

레터 독자층은 2026-11-11 부터 합쇼체로 쓴다. 그 전에 쓴 원고 묶음 · 편집 목록 · 가정 파일의 글 블록은 평서체라, 다시 돌리면
넣기 검수와 게이트 ③(「평서체 끝」)에 걸린다. 이 도구는 문장 끝맺음만 바꾼다 — 숫자 · 장부 자리표시 { } · 낫표 「」 인용 · 코드 · 표 · 제목은 그대로다.

    python 스크립트/원고어투.py 바꾸기 <파일> [<파일> …] [--보기] [--목록 <바꾼목록.txt>]
    python 스크립트/원고어투.py 검사 <레터.md> [--목록 <파일>]          # 줄글의 평서체 끝(게이트 ③ 과 같은 판정)

바꾸기가 받는 파일(꼴은 안을 보고 가른다)
  - 원고 묶음 `_raw/레터원고/<묶음>.json` — 모든 글 값(「뒤」 앵커 포함). 「_」 로 시작하는 파일(`_넣은판.json`)은 건너뛴다
  - 편집 목록 `_raw/편집목록.json` — [{원문, 새글, …}] 의 원문 · 새글(초안이 합쇼체로 나오므로 원문도 같은 꼴로 맞춘다)
  - 가정 파일 `가정_<회사>.json` — 레터가 싣는 글 블록만: Narrative · 서사 · 서사연결 · 독자근거 · 시나리오이야기 · 자본비용 · 관측의 글 칸
    (`가정해시.관측글`) · 검토의견(레터 부록에 실린다) · 서술 · 신호 · 3P · 메타.이해관계 · WACC근거의 글 칸(첫 칸 · 넷째 칸부터 — 레터 부록
    「기준일 뒤 자료」 가 싣는다 · 1.1.20). 근거 칸(저자층) · 구조 · 가정 값 · WACC근거의 날짜 · 상태 칸은 건드리지 않는다
  - 모순 장부 `_raw/모순장부.json` — 항목의 「독자」 문장만(레터 부록 H 가 싣는다)
  - 마크다운(.md) — 줄글만(표 · 제목 · 코드 · 「> 원문:」 은 그대로)
  건너뛰는 키: 「_」 로 시작하는 메모 키 · 근거대장 · 옛글처리 · 요소 · 갈래 · 태그(값이 낱말 이름표다)

알아 둘 것
  - **가정 파일의 서술 · 신호 · 3P · 메타.이해관계 · WACC근거는 값 해시 안이다**(`가정해시.글블록` 밖 — 붓기가 워크북 12번에 옮긴다). 이 블록이 바뀌면
    워크북 마감 기록의 값 해시와 어긋나 게이트 ⑥ 이 막는다 — 붓기 → 워크북 마감을 한 번 더 돈다. 바꾸기가 이 경우를 알린다
  - 원고 묶음과 가정 파일을 함께 바꾸면 다음 넣기에서 두 글이 같아 「가정 쪽에서 고친 자리」 로 멈추지 않는다. 묶음만 바꿨으면
    넣기에 `--묶음우선` 을 준다
  - 바꾸지 못한 낱말(서술어인지 모르는 「~다」)과 물음 꼴(「~는가」 · 「~인가」)은 목록으로 낸다 — 사람이 고친다
  - JSON 은 원래 들여쓰기 · 줄 끝 문자로 다시 쓴다(같은 꼴로 되돌려 쓸 수 없으면 들여쓰기 1 로 쓰고 알린다)
  - **숫자 바로 뒤의 한 글자 + 「다」 는 명사(수 단위)다**(1.1.19) — 「779주다」 · 「52주다」 의 「주」 는 주식 · 주(週)이지 동사 「주다」 가 아니다.
    숫자(또는 숫자를 내는 자리표시 `}`)에 붙은 한 글자 낱말은 서술격으로 바꾼다(「779주입니다」). 지난 바꾸기가 이미 「779줍니다」 로 만든
    글은 같은 판정으로 되돌린다(「779주입니다」). 둘 다 `--목록` 과 화면에 「숫자 뒤 명사」 로 알린다. 검사도 이 꼴(「779줍니다」)을 센다
종료 코드 — 0 바꿈(또는 바꿀 것 없음) · 1 검사에서 평서체 끝이 있음 · 2 입력 오류
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys

여기 = os.path.dirname(os.path.abspath(__file__))
if 여기 not in sys.path:
    sys.path.insert(0, 여기)

import 어투  # noqa: E402
import 가정해시  # noqa: E402

건너키 = ("근거대장", "옛글처리", "요소", "갈래", "태그")
가정블록 = tuple(가정해시.글블록) + ("서술", "신호", "3P")
_물음 = re.compile(r"(?:는가|인가|은가|던가|할까|일까|는지)[.?]?\s*$")


class 기록:
    def __init__(self):
        self.수 = 0
        self.못 = []
        self.물음 = []
        self.줄 = []
        self.자리 = set()
        self.남음 = []                    # 1.1.19 — 바꾼 뒤에도 남은 숫자 뒤 용언(표 줄 · 건너뛴 칸 — 사람 몫)
        self.명사 = []                    # 1.1.19 — 숫자 뒤 명사로 읽은 자리 · 되돌린 자리(「779주다」 → 「779주입니다」 · 「779줍니다」 → 「779주입니다」)


# ── 숫자 뒤 명사(1.1.19) ──────────────────────────────────────────────────────
# 숫자에 붙은 한글은 용언이 아니다(용언은 숫자에 붙여 쓰지 않는다) — 「779주다」 · 「52주다」 · 「3자다」 의 한 글자는 수 단위 · 명사다.
# `어투.합쇼` 는 낱말만 보고 「주다 · 자다 · 가다」 를 용언으로 읽어 「줍니다」 로 바꿨다(1.1.18 회차 셋). 판정은 낱말 목록이 아니라 앞 글자다.
# 판정은 `어투.숫자뒤명사` 한 곳(앞 글자 꼴 `어투._수앞`)이다 — 이 파일은 그 판정을 부르고 알림 목록(명)만 더 센다(1.1.19).
_ㅂ받침 = 17


def _되돌릴꼴(글):
    """이미 용언으로 바뀐 숫자 뒤 명사 — 「779줍니다」 · 「52줍니다」 → [(시작, 끝, 옛, 새)]. 「10입니다」(서술격)는 그대로 둔다."""
    낸 = []
    for m in re.finditer(r"(?<=%s)([가-힣])니다" % 어투._수앞.pattern, 글):
        c = m.group(1)
        n = ord(c) - 0xAC00
        if n % 28 != _ㅂ받침:
            continue
        밑 = chr(0xAC00 + n - _ㅂ받침)                     # 받침 ㅂ 을 뗀 글자(「줍」 → 「주」)
        if 밑 == "이" or 어투.합쇼(밑 + "다") != c + "니다":
            continue
        낸.append((m.start(), m.end(), m.group(0), 밑 + "입니다"))
    return 낸


def _조각바꾸기(글):
    """`어투._조각바꾸기` 와 같은 바꿈(숫자 뒤 명사도 같은 판정 — `어투.숫자뒤명사`)에 명사로 읽은 자리를 센다
    → (새 글, 바꾼 수, 못 바꾼 것, 명사로 읽은 것[(옛 둘레, 새)])."""
    자리 = 어투.끝찾기(글)
    밖, 앞, 수, 못, 명 = [], 0, 0, [], []
    for a, b, w, 새 in sorted(자리):
        if a < 앞:
            continue
        if 어투.숫자뒤명사(글, a, w):                       # 「주다」 · 「자다」 … 앞이 숫자면 한 글자 명사 + 서술격(「10이다」 는 서술격 그대로)
            옛 = 새
            새 = w[0] + "입니다"
            if 옛 != 새:
                명.append((글[max(0, a - 12):b], 새))
        if 새 is None:
            못.append((w, 글[max(0, a - 20):b + 5]))
            continue
        밖.append(글[앞:a])
        밖.append(새)
        앞 = b
        수 += 1
    밖.append(글[앞:])
    return "".join(밖), 수, 못, 명


def 합쇼체로(글):
    """`어투.합쇼체로` 와 같은 줄 판정(표 · 제목 · 코드 블록 줄은 그대로) + 숫자 뒤 명사 → (새 글, 바꾼 수, 못 바꾼 것, 명사[(옛 둘레, 새)])."""
    밖, 수, 못, 명 = [], 0, [], []
    블록 = False
    for 줄 in 글.split("\n"):
        t = 줄.strip()
        if t.startswith("```"):
            블록 = not 블록
            밖.append(줄)
            continue
        if 블록 or not 어투._줄글인가(t):
            밖.append(줄)
            continue
        새, k, 남, 명사 = _조각바꾸기(줄)
        for a, b, 옛, 고친 in reversed(_되돌릴꼴(새)):
            새 = 새[:a] + 고친 + 새[b:]
            명사.append((옛, 고친))
            k += 1
        밖.append(새)
        수 += k
        못 += 남
        명 += 명사
    return "\n".join(밖), 수, 못, 명


def 숫자뒤용언(글):
    """레터 · 원고 글에서 숫자 뒤 명사가 용언으로 바뀐 자리(「779줍니다」) → [(줄 번호, 조각)]. 검사 · 바꾸기의 뒤 확인이 쓴다."""
    낸 = []
    for n, 줄 in enumerate(글.split("\n"), 1):
        for a, b, _옛, _새 in _되돌릴꼴(줄):
            낸.append((n, 줄[max(0, a - 12):b]))
    return 낸


def WACC근거글칸(v):
    """WACC근거 한 줄 [자료 · 판단 글, 기준일, 상태, 까닭 …] 에서 글 칸의 차례 — 첫 칸과 넷째 칸부터. 둘째(날짜) · 셋째(상태) 칸은 값 칸이다."""
    return {i for i in range(len(v)) if i == 0 or i >= 3}


def _글바꾸기(s, 자리, 록):
    새, k, 못, 명 = 합쇼체로(s)
    for 옛, 고친 in 명:
        록.명사.append("%s — 「%s」 → 「%s」" % (자리, 옛, 고친))
    if k:
        록.수 += k
        록.줄.append("%s\n  - %s\n  + %s" % (자리, s, 새))
        록.자리.add(re.match(r"[^.\[]*", 자리).group(0))
    for w, 둘레 in 못:
        록.못.append("%s — 「%s」 (%s)" % (자리, w, 둘레))
    for 줄 in 새.split("\n"):
        if _물음.search(re.sub(r"「[^」]*」", "", 줄)):
            록.물음.append("%s — %s" % (자리, 줄.strip()[:120]))
    return 새


def _걷기(x, 자리, 록):
    if isinstance(x, str):
        return _글바꾸기(x, 자리, 록)
    if isinstance(x, list):
        return [_걷기(v, "%s[%d]" % (자리, i), 록) for i, v in enumerate(x)]
    if isinstance(x, dict):
        밖 = {}
        for k, v in x.items():
            if isinstance(k, str) and (k.startswith("_") or k in 건너키):
                밖[k] = v
            else:
                밖[k] = _걷기(v, "%s.%s" % (자리, k) if 자리 else k, 록)
        return 밖
    return x


def _꼴찾기(원):
    d = json.loads(원)
    본 = 원.replace("\r\n", "\n")
    for ind in (1, 2, 4, None, "\t"):
        for sep in ((",", ": "), (", ", ": "), (",", ":")):
            if ind is None and sep == (",", ": "):
                continue
            s = json.dumps(d, ensure_ascii=False, indent=ind, separators=sep)
            if s.rstrip("\n") == 본.rstrip("\n"):
                return d, ind, sep, 본.endswith("\n")
    return d, None, None, True


def _쓰기(경로, 글, crlf):
    if crlf:
        글 = 글.replace("\r\n", "\n").replace("\n", "\r\n")
    io.open(경로, "w", encoding="utf-8", newline="").write(글)


def 꼴(d, 경로):
    if 경로.lower().endswith(".md"):
        return "글"
    if isinstance(d, dict) and isinstance(d.get("항목"), list) and any(isinstance(x, dict) and "독자" in x for x in d["항목"]):
        return "모순장부"
    if isinstance(d, list):
        return "편집목록" if all(isinstance(x, dict) and "원문" in x for x in d) else None
    if isinstance(d, dict):
        if "스키마버전" in d or ("가정" in d and "구조" in d):
            return "가정"
        return "묶음"
    return None


def 바꾸기(경로, 보기=False):
    """파일 하나 → (꼴, 기록, 알림[])."""
    원 = io.open(경로, encoding="utf-8", newline="").read()
    crlf = "\r\n" in 원
    록, 알림 = 기록(), []
    if 경로.lower().endswith(".md"):
        새, 록.수, 못, 명 = 합쇼체로(원.replace("\r\n", "\n"))
        록.못 = ["%s — 「%s」 (%s)" % (os.path.basename(경로), w, 둘) for w, 둘 in 못]
        록.명사 = ["%s — 「%s」 → 「%s」" % (os.path.basename(경로), 옛, 고친) for 옛, 고친 in 명]
        록.남음 = ["%s:%d — 「%s」" % (os.path.basename(경로), n, t) for n, t in 숫자뒤용언(새)]
        if 록.수 and not 보기:
            _쓰기(경로, 새, crlf)
        return "글", 록, 알림
    d, ind, sep, 끝줄 = _꼴찾기(원)
    종 = 꼴(d, 경로)
    if 종 is None:
        raise ValueError("원고 묶음 · 편집 목록 · 가정 파일 · 마크다운이 아니다: %s" % 경로)
    if 종 == "편집목록":
        새d = []
        for i, x in enumerate(d):
            y = dict(x)
            for k in ("원문", "새글"):
                if isinstance(y.get(k), str):
                    y[k] = _글바꾸기(y[k], "[%d].%s" % (i, k), 록)
            새d.append(y)
    elif 종 == "모순장부":                                 # 레터 부록 H 가 싣는 「독자」 문장만(나머지 칸은 저자층)
        새d = dict(d)
        새d["항목"] = [dict(x, 독자=_글바꾸기(x["독자"], "항목[%d].독자" % i, 록)) if isinstance(x, dict) and isinstance(x.get("독자"), str) else x
                     for i, x in enumerate(d["항목"])]
    elif 종 == "가정":
        새d = dict(d)
        for k in 가정블록:
            if k in 새d:
                새d[k] = _걷기(새d[k], k, 록)
        관 = 새d.get("관측")
        if isinstance(관, dict):
            관 = dict(관)
            for k in 가정해시.관측글:
                if k in 관:
                    관[k] = _걷기(관[k], "관측." + k, 록)
            새d["관측"] = 관
        w = 새d.get("WACC근거")                          # 1.1.20 — 할인율 입력의 근거 칸 글(첫 칸 · 넷째 칸 뒤)은 레터 부록(기준일 뒤 자료)에 실린다. 날짜 · 상태 칸은 그대로
        if isinstance(w, dict):
            새w = {}
            for k, v in w.items():
                if isinstance(v, list):
                    새w[k] = [_글바꾸기(x, "WACC근거.%s[%d]" % (k, i), 록) if (isinstance(x, str) and i in WACC근거글칸(v)) else x
                             for i, x in enumerate(v)]
                else:
                    새w[k] = v
            새d["WACC근거"] = 새w
        메 = 새d.get("메타")
        if isinstance(메, dict) and "이해관계" in 메:
            메 = dict(메)
            메["이해관계"] = _걷기(메["이해관계"], "메타.이해관계", 록)
            새d["메타"] = 메
        바뀐값 = [k for k in ("서술", "신호", "3P", "WACC근거") if k in 록.자리] + (["메타.이해관계"] if "메타" in 록.자리 else [])
        if 바뀐값:
            알림.append("값 해시 안의 글 블록(%s)이 바뀌었다 — 붓기 → 워크북 마감을 한 번 더 돈다(게이트 ⑥)" % " · ".join(바뀐값))
    else:
        새d = _걷기(d, "", 록)
    록.남음 = ["%s — 「%s」" % (자리, t) for 자리, 글 in _글들(새d, "") for _n, t in 숫자뒤용언(글)]     # 바꾼 뒤에도 남은 숫자 뒤 용언(표 줄 · 건너뛴 칸)
    if 록.수 and not 보기:
        if ind is None and sep is None:
            ind, sep = 1, (",", ": ")
            알림.append("JSON 꼴을 되돌려 쓸 수 없어 들여쓰기 1 로 썼다")
        글 = json.dumps(새d, ensure_ascii=False, indent=ind, separators=sep) + ("\n" if 끝줄 else "")
        json.loads(글)
        _쓰기(경로, 글, crlf)
    return 종, 록, 알림


def _글들(x, 자리):
    """JSON 값 안의 글 → [(자리, 글)]."""
    if isinstance(x, str):
        return [(자리, x)]
    if isinstance(x, list):
        return [y for i, v in enumerate(x) for y in _글들(v, "%s[%d]" % (자리, i))]
    if isinstance(x, dict):
        return [y for k, v in x.items() for y in _글들(v, "%s.%s" % (자리, k) if 자리 else "%s" % k)]
    return []


def 검사(경로):
    글 = io.open(경로, encoding="utf-8").read()
    return 어투.평서체끝(글)


def 검사명사(경로):
    """1.1.19 — 숫자 뒤 명사가 용언으로 바뀐 자리(「779줍니다」) → [(줄 번호, 조각)]. 평서체 끝과 함께 검사가 센다."""
    return 숫자뒤용언(io.open(경로, encoding="utf-8").read())


def main(argv=None):
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="레터 원고의 평서체 끝을 합쇼체로 바꾸고, 레터의 평서체 끝을 찾는다")
    ap.add_argument("일", choices=("바꾸기", "검사"))
    ap.add_argument("파일", nargs="+")
    ap.add_argument("--보기", action="store_true", help="파일을 쓰지 않고 바꿀 수만 보인다")
    ap.add_argument("--목록", default=None, help="바꾼 글(옛 → 새) · 못 바꾼 낱말 · 물음 꼴을 적을 파일")
    a = ap.parse_args(argv)
    if a.일 == "검사":
        걸, 줄들, 명 = 0, [], 0
        for f in a.파일:
            for n, w, t in 검사(f):
                걸 += 1
                줄들.append("%s:%d 「%s」 %s" % (os.path.basename(f), n, w, t[:110]))
            for n, t in 검사명사(f):
                명 += 1
                줄들.append("%s:%d 숫자 뒤 명사가 용언으로 바뀜 「%s」 — 「~주입니다」 처럼 서술격으로 쓴다" % (os.path.basename(f), n, t))
        print("평서체 끝 %d곳 · 숫자 뒤 용언 %d곳" % (걸, 명))
        걸 += 명
        for x in 줄들[:40]:
            print("  " + x)
        if a.목록:
            io.open(a.목록, "w", encoding="utf-8").write("\n".join(줄들) + "\n")
        return 1 if 걸 else 0
    밖 = []
    합 = 0
    for f in a.파일:
        if os.path.basename(f).startswith("_") and f.lower().endswith(".json"):
            print("%s — 건너뜀(「_」 로 시작하는 파일은 묶음이 아니다)" % f)
            continue
        try:
            종, 록, 알림 = 바꾸기(f, a.보기)
        except (ValueError, json.JSONDecodeError, OSError) as e:
            print("못 읽었다 — %s: %s" % (f, e))
            return 2
        합 += 록.수
        print("%s — %s · 바꾼 끝맺음 %d · 못 바꾼 낱말 %d · 물음 꼴 %d · 숫자 뒤 명사 %d%s%s" % (
            f, 종, 록.수, len(록.못), len(록.물음), len(록.명사), (" · 남은 숫자 뒤 용언 %d" % len(록.남음)) if 록.남음 else "",
            " (보기만)" if a.보기 else ""))
        for x in 알림:
            print("  알림 — " + x)
        for x in 록.못[:10]:
            print("  못 바꿈 — " + x)
        for x in 록.물음[:10]:
            print("  물음 꼴 — " + x)
        for x in 록.명사[:10]:
            print("  숫자 뒤 명사 — " + x)
        for x in 록.남음[:10]:
            print("  남은 숫자 뒤 용언(사람이 고친다) — " + x)
        밖.append("#### %s (%s)" % (f, 종))
        밖 += 록.줄
        밖 += ["못 바꿈 — " + x for x in 록.못] + ["물음 꼴 — " + x for x in 록.물음] + ["숫자 뒤 명사 — " + x for x in 록.명사]
        밖 += ["남은 숫자 뒤 용언 — " + x for x in 록.남음]
    print("합계 — 바꾼 끝맺음 %d" % 합)
    if a.목록:
        io.open(a.목록, "w", encoding="utf-8").write("\n".join(밖) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

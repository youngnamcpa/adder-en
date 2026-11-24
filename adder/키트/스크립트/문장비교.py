# -*- coding: utf-8 -*-
"""문장비교 — 같은 회사의 두 보고서에서 같은 절을 골라 **무엇을 새로 쓰고 · 지우고 · 고쳐 썼나**를 문장 단위로 견준다 (NLP ①).

왜 있나
  · 「앵커 표를 구조 블록으로 끊는다」 · 「과거 평균을 쓰기 전에 사업의 구조가 달라졌는지 확인한다」 — 제품 구성 · 값이
    정해지는 방식 · 경쟁 구도가 바뀐 해를 찾는 재료가 회사의 자기 서술이다. 사람이 두 해 보고서를 나란히 읽으면 놓친다
  · 리포트 커버리지가 없는 회사의 「IR 자료의 연도별 자기 서술 비교」(축 후보 — 키트 CLAUDE.md 매출 분해 규칙) 도 같은 일이다
  **고르지 않는다.** 문장 목록과 후보 신호만 낸다 — 블록을 어디서 끊을지, 축으로 삼을지는 사람이 정한다.

사용
    python 스크립트/문장비교.py 가정.json                       # 가정 곁 _raw 에서 사업보고서 원문 둘(최근 둘)을 찾아 견준다
    python 스크립트/문장비교.py 가정.json --받기                 # 제출이력의 최근 사업보고서 둘 중 없는 원문을 받는다(본체에서는 멈춘다)
    python 스크립트/문장비교.py --앞 <txt|접수번호> --뒤 <txt|접수번호> [--낼 경로.json]
    python 스크립트/문장비교.py 가정.json --절 "사업의 개요,매출 및 수주상황"
  밖에서 쓰기 — `비교(앞글, 뒤글, 설정=None, 앞이름="앞", 뒤이름="뒤")` → {"절": [...], "신호": [...], "요약": {...}}
    (Narrative 점검 초안 · 분기 대 분기 비교에 쓴다. 파일을 읽거나 쓰지 않는다)

읽는 것
    원문 텍스트 — dart_fetch `원문` 이 `_raw/{딱지}/{접수}.txt` 에 남긴 꼴(가정 곁 `_raw/` 와 dart_fetch 의 `_raw/` 를 함께 찾는다)
    _raw/dart_제출이력.json — 최근 사업보고서 둘을 고를 때(정정본이 있으면 늦게 낸 것)
    문장비교설정.json — 큰절 · 절 이름 · 문턱 · 구조 낱말 · 축 낱말(결과를 보기 전에 정한 값)
내는 것
    _raw/문장비교.json — {"형식": "문장비교 1", 만든날, 설정, 입력{앞, 뒤}, 절[], 요약, 신호[]}
      절[] = {"절", "찾음": {"앞": bool, "뒤": bool}, "앞문장수", "뒤문장수", "같음": n,
              "바뀜": [{"앞": 글, "뒤": 글, "유사도", "앞번호", "뒤번호", "숫자": {"앞": [...], "뒤": [...]} | null}],
              "새": [{"문장", "번호"}], "빠짐": [{"문장", "번호"}]}
    신호 종류: 구조 변화 후보 · 축 후보 · 절 찾지 못함 · 신호 줄임
종료 코드 — 0 통과 · 1 발견(절을 찾지 못한 쪽이 있다) · 2 입력오류(원문 없음)
회사 · 업종 · 제품 이름은 이 도구에 한 글자도 없다.
"""
from __future__ import annotations

import argparse
import datetime
import glob
import io
import json
import math
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:                                            # noqa: BLE001
    pass

여기 = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, 여기)
from 종료코드 import 통과, 발견, 입력오류  # noqa: E402

설정경로 = os.path.join(여기, "문장비교설정.json")
기본설정 = {
    "큰절": {"머리": "II. 사업의 내용", "끝": "III. 재무에 관한 사항"},
    "절": ["사업의 개요", "주요 제품 및 서비스", "원재료 및 생산설비", "매출 및 수주상황", "위험관리 및 파생거래",
          "주요계약 및 연구개발활동", "기타 참고사항"],
    "같음문턱": 0.92, "바뀜문턱": 0.45, "최소한글": 10, "숫자비중상한": 0.5,
    "구조낱말": ["신규 사업", "진출", "양수", "양도", "인수", "합병", "분할", "매각", "중단", "철수", "제품 구성", "비중",
              "경쟁", "점유율", "고객", "규제", "가격 결정", "장기공급계약", "생산능력", "증설", "구조조정", "연결 범위"],
    "축낱말": ["가격", "단가", "ASP", "물량", "출하", "판매량", "가동률", "수주", "계약", "시장 규모", "수요", "공급"],
    "최대신호": 25,
}


def 설정읽기(경로=None):
    p = 경로 or 설정경로
    s = dict(기본설정)
    if os.path.exists(p):
        try:
            s.update(json.load(io.open(p, encoding="utf-8")))
        except ValueError:
            pass
    return s


# ═════════════════════════════════════ 글 다루기

def _틀(이름):
    """절 이름 → 빈칸이 있어도 없어도 걸리는 정규식."""
    return r"\s*".join(re.escape(ch) for ch in re.sub(r"\s+", "", 이름))


def 큰절(글, 설정):
    """「II. 사업의 내용」 ~ 「III. 재무에 관한 사항」 — 목차 자리도 걸리므로 가장 긴 구간을 고른다. 못 찾으면 None."""
    머, 끝 = 설정["큰절"]["머리"], 설정["큰절"]["끝"]
    시작들 = [m.start() for m in re.finditer(_틀(머), 글)]
    끝들 = [m.start() for m in re.finditer(_틀(끝), 글)]
    최, 낸 = 0, None
    for s in 시작들:
        e = next((x for x in 끝들 if x > s), None)
        if e is not None and e - s > 최:
            최, 낸 = e - s, 글[s:e]
    return 낸


def 절나누기(큰글, 절이름들):
    """{절 이름: 글} — 줄 첫머리의 「n. 이름」 머리말로 가른다. 못 찾은 절은 빠진다."""
    자리 = []
    for 이름 in 절이름들:
        m = None
        for m0 in re.finditer(r"(?m)^[ \t]*(?:\d{1,2}\s*\.\s*)?" + _틀(이름), 큰글):
            m = m0
            break
        if m:
            자리.append((m.start(), 이름))
    자리.sort()
    낸 = {}
    for i, (s, 이름) in enumerate(자리):
        e = 자리[i + 1][0] if i + 1 < len(자리) else len(큰글)
        낸[이름] = 큰글[s:e]
    return 낸


_문장끝 = re.compile(r"(?<=[다요음함됨임니까])\.")


def 문장들(글, 설정):
    """단락(빈 줄로 가른 덩이) 안의 줄바꿈은 이어 붙이고(옛 보고서는 한 문장을 여러 줄로 감는다), 「…다.」 에서 자른다
    (새 보고서는 「…있습니다.1990년…」 처럼 빈칸 없이 붙여 쓴다). 끝맺음이 없는 조각은 한글이 두 배 넘게 길 때만 문장으로 본다 —
    표 칸을 이은 줄을 문장으로 세지 않으려는 것이다."""
    낸 = []
    for 단락 in re.split(r"\n\s*\n", (글 or "").replace("&cr;", " ")):
        단락 = re.sub(r"\s+", " ", 단락).strip()
        조각 = _문장끝.split(단락)
        for i, s in enumerate(조각):
            s = s.strip(" \t·-•")
            if not s:
                continue
            끝남 = i < len(조각) - 1
            한글 = len(re.findall(r"[가-힣]", s))
            숫자 = len(re.findall(r"[\d,.%()]", s))
            if 한글 < 설정["최소한글"] * (1 if 끝남 else 2) or 숫자 > 설정["숫자비중상한"] * max(1, len(s.replace(" ", ""))):
                continue
            낸.append(s + "." if 끝남 else s)
    return 낸


_숫자꼴 = re.compile(r"\d[\d,]*(?:\.\d+)?\s*(?:%p|%|조\s?원|억\s?원|만\s?원|백만\s?원|천\s?원|원|년|분기|배|개|명|대|톤|GB|Gb|TB)?")


def 숫자들(s):
    """문장 속 숫자(단위째) — 앞머리 번호(「(3)」 「가.」 「2.」)는 뺀다."""
    s = re.sub(r"^\s*(?:\(\d{1,2}\)|\d{1,2}\)|[가-하]\.|\d{1,2}\.)\s*", "", s or "")
    return sorted(re.sub(r"\s+", "", x) for x in _숫자꼴.findall(s))


def _그램(s):
    t = re.sub(r"\s+", "", s)
    g = {}
    for n in (2, 3):
        for i in range(len(t) - n + 1):
            k = t[i:i + n]
            g[k] = g.get(k, 0) + 1
    return g


def _벡터들(문장목록):
    그램 = [_그램(s) for s in 문장목록]
    df = {}
    for g in 그램:
        for k in g:
            df[k] = df.get(k, 0) + 1
    N = len(그램)
    idf = {k: math.log((N + 1) / (v + 1)) + 1 for k, v in df.items()}
    벡 = []
    for g in 그램:
        v = {k: c * idf[k] for k, c in g.items()}
        n = math.sqrt(sum(x * x for x in v.values())) or 1.0
        벡.append({k: x / n for k, x in v.items()})
    return 벡


def 짝짓기(앞, 뒤, 설정):
    """한 대 한 — 코사인이 큰 짝부터 고른다. (같음 수, 바뀜[], 새[], 빠짐[])."""
    벡 = _벡터들(앞 + 뒤)
    A, B = 벡[:len(앞)], 벡[len(앞):]
    색 = {}
    for i, v in enumerate(A):
        for k in v:
            색.setdefault(k, []).append(i)
    쌍 = []
    for j, w in enumerate(B):
        점 = {}
        for k, x in w.items():
            for i in 색.get(k, ()):
                점[i] = 점.get(i, 0.0) + A[i][k] * x
        for i, c in 점.items():
            if c >= 설정["바뀜문턱"]:
                쌍.append((c, i, j))
    쌍.sort(reverse=True)
    쓴앞, 쓴뒤, 같음, 바뀜 = set(), set(), 0, []
    for c, i, j in 쌍:
        if i in 쓴앞 or j in 쓴뒤:
            continue
        쓴앞.add(i)
        쓴뒤.add(j)
        na, nb = 숫자들(앞[i]), 숫자들(뒤[j])
        if 앞[i] == 뒤[j] or (c >= 설정["같음문턱"] and na == nb):
            같음 += 1
            continue
        바뀜.append({"앞": 앞[i], "뒤": 뒤[j], "유사도": round(c, 3), "앞번호": i + 1, "뒤번호": j + 1,
                   "숫자": None if na == nb else {"앞": na, "뒤": nb}})
    새 = [{"문장": 뒤[j], "번호": j + 1} for j in range(len(뒤)) if j not in 쓴뒤]
    빠짐 = [{"문장": 앞[i], "번호": i + 1} for i in range(len(앞)) if i not in 쓴앞]
    바뀜.sort(key=lambda x: x["뒤번호"])
    return 같음, 바뀜, 새, 빠짐


def _걸린낱말(s, 낱말들):
    t = re.sub(r"\s+", "", s)
    return [w for w in 낱말들 if re.sub(r"\s+", "", w) in t]


def 비교(앞글, 뒤글, 설정=None, 앞이름="앞", 뒤이름="뒤", 절이름들=None):
    """두 원문 텍스트의 같은 절을 견준다 — 파일을 읽거나 쓰지 않는다. {"절": [...], "신호": [...], "요약": {...}}."""
    설정 = 설정 or 설정읽기()
    절이름들 = 절이름들 or 설정["절"]
    큰앞, 큰뒤 = 큰절(앞글 or "", 설정), 큰절(뒤글 or "", 설정)
    나앞 = 절나누기(큰앞, 절이름들) if 큰앞 else {}
    나뒤 = 절나누기(큰뒤, 절이름들) if 큰뒤 else {}
    절결과, 신호, 줄임 = [], [], {}
    최대 = int(설정.get("최대신호", 25))

    def 알림(종류, 대상, 값, 문턱, 글, 등급="참고"):
        if sum(1 for s in 신호 if s["종류"] == 종류) >= 최대:
            줄임[종류] = 줄임.get(종류, 0) + 1
            return
        신호.append({"출처": "문장비교", "종류": 종류, "대상": 대상, "값": 값, "문턱": 문턱, "글": 글, "등급": 등급})

    if not 큰앞 or not 큰뒤:
        없 = [n for n, t in ((앞이름, 큰앞), (뒤이름, 큰뒤)) if not t]
        알림("절 찾지 못함", 설정["큰절"]["머리"], " · ".join(없), "머리말", "「%s」 ~ 「%s」 구간을 %s 원문에서 찾지 못했다 — 전체를 견주지 않았다. "
           "보고서 꼴이 다르면 문장비교설정.json 의 큰절 머리말을 고친다" % (설정["큰절"]["머리"], 설정["큰절"]["끝"], " · ".join(없)), "경보")
    for 이름 in 절이름들:
        찾 = {"앞": 이름 in 나앞, "뒤": 이름 in 나뒤}
        rec = {"절": 이름, "찾음": 찾}
        if not (찾["앞"] and 찾["뒤"]):
            if 큰앞 and 큰뒤:
                알림("절 찾지 못함", 이름, " · ".join(k for k, v in 찾.items() if not v), "머리말",
                   "절 「%s」 을 %s 원문에서 찾지 못했다 — 이 절은 견주지 않았다(조용히 다른 절과 섞지 않는다)"
                   % (이름, " · ".join({"앞": 앞이름, "뒤": 뒤이름}[k] for k, v in 찾.items() if not v)), "경보")
            절결과.append(rec)
            continue
        앞 = 문장들(나앞[이름], 설정)
        뒤 = 문장들(나뒤[이름], 설정)
        같음, 바뀜, 새, 빠짐 = 짝짓기(앞, 뒤, 설정)
        rec.update({"앞문장수": len(앞), "뒤문장수": len(뒤), "같음": 같음, "바뀜": 바뀜, "새": 새, "빠짐": 빠짐})
        절결과.append(rec)
        for 무엇, 목록, 글꼴 in (("새", 새, "새로 쓴 문장"), ("빠짐", 빠짐, "지운 문장"), ("바뀜", 바뀜, "고쳐 쓴 문장")):
            for x in 목록:
                s = x["뒤"] if 무엇 == "바뀜" else x["문장"]
                번 = x["뒤번호"] if 무엇 == "바뀜" else x["번호"]
                쪽 = 앞이름 if 무엇 == "빠짐" else 뒤이름
                구 = _걸린낱말(s if 무엇 != "바뀜" else s + " " + x["앞"], 설정["구조낱말"])
                if 구:
                    알림("구조 변화 후보", "%s · %s %d" % (이름, 쪽, 번), " · ".join(구), "구조 낱말",
                       "%s(%s 문장 %d): 「%s」 — 제품 구성 · 값이 정해지는 방식 · 경쟁 구도 · 연결 범위가 바뀐 해인지 보고, 그렇다면 "
                       "앵커 표를 이 해에서 끊는 근거로 적는다" % (글꼴, 쪽, 번, s[:160]))
                    continue
                축 = _걸린낱말(s, 설정["축낱말"])
                if 축 and (x.get("숫자") if 무엇 == "바뀜" else 숫자들(s)):
                    알림("축 후보", "%s · %s %d" % (이름, 쪽, 번), " · ".join(축), "축 낱말",
                       "%s(%s 문장 %d): 「%s」 — 회사가 해마다 고쳐 말한 자리는 시나리오 축 후보다(리포트가 없는 회사의 자기 서술 비교)"
                       % (글꼴, 쪽, 번, s[:160]))
    for 종류, n in 줄임.items():
        신호.append({"출처": "문장비교", "종류": "신호 줄임", "대상": 종류, "값": n, "문턱": 최대,
                   "글": "「%s」 신호가 %d개 더 있다 — 문장비교.json 의 절[] 에서 전부 본다" % (종류, n), "등급": "참고"})
    요약 = {"절수": len(절이름들), "견준절": sum(1 for r in 절결과 if "같음" in r),
          "같음": sum(r.get("같음", 0) for r in 절결과), "바뀜": sum(len(r.get("바뀜", [])) for r in 절결과),
          "새": sum(len(r.get("새", [])) for r in 절결과), "빠짐": sum(len(r.get("빠짐", [])) for r in 절결과),
          "숫자바뀜": sum(1 for r in 절결과 for x in r.get("바뀜", []) if x.get("숫자"))}
    return {"절": 절결과, "신호": 신호, "요약": 요약}


# ═════════════════════════════════════ 원문 찾기 · 받기

def _뿌리들(뿌리):
    낸 = [os.path.join(뿌리, "_raw")] if 뿌리 else []
    try:
        import dart_fetch                                    # noqa: PLC0415
        낸.append(dart_fetch.RAW)
    except Exception:                                        # noqa: BLE001
        pass
    return 낸


def 원문찾기(접수, 뿌리들):
    for r in 뿌리들:
        if not r or not os.path.isdir(r):
            continue
        p = glob.glob(os.path.join(r, "**", "%s.txt" % 접수), recursive=True) or \
            glob.glob(os.path.join(r, "**", "%s*.txt" % 접수), recursive=True)
        if p:
            return max(p, key=os.path.getsize)
    return None


def 원문받기(접수, 딱지="문장비교"):
    import dart_fetch                                        # noqa: PLC0415
    import 본체가드                                          # noqa: PLC0415
    본체가드.본체면멈춘다(dart_fetch.ROOT)
    dart_fetch._준비()
    dart_fetch.원문(접수, 딱지)


def 최근사업보고서(raw, n=2):
    """제출이력에서 최근 사업보고서 n개 — [(접수, 보고서명)] 오래된 것부터. 같은 해에 정정본이 있으면 늦게 낸 것."""
    try:
        j = json.load(io.open(os.path.join(raw, "dart_제출이력.json"), encoding="utf-8"))
    except (IOError, OSError, ValueError):
        return []
    해별 = {}
    for r in (j.get("list") if isinstance(j, dict) else j) or []:
        m = re.search(r"사업보고서\s*\((\d{4})\.\d{2}\)", r.get("report_nm") or "")
        if not m:
            continue
        y = int(m.group(1))
        if y not in 해별 or r.get("rcept_no", "") > 해별[y].get("rcept_no", ""):
            해별[y] = r
    return [(해별[y]["rcept_no"], 해별[y]["report_nm"]) for y in sorted(해별)[-n:]]


def _해딱지(p):
    m = re.search(r"사업(\d{4})", p)
    return int(m.group(1)) if m else -1


def 입력정하기(가정경로, 앞, 뒤, 받기):
    뿌리 = os.path.dirname(os.path.abspath(가정경로)) if 가정경로 else os.getcwd()
    뿌 = _뿌리들(뿌리)

    def 풀기(x):
        if x and os.path.exists(x):
            return x, None
        if x and re.fullmatch(r"\d{14}", x):
            p = 원문찾기(x, 뿌)
            if p is None and 받기:
                원문받기(x)
                p = 원문찾기(x, 뿌)
            return p, x
        return None, x

    if 앞 or 뒤:
        (pa, na), (pb, nb) = 풀기(앞), 풀기(뒤)
        return 뿌리, (pa, na, None), (pb, nb, None)
    raw = os.path.join(뿌리, "_raw")
    고른 = 최근사업보고서(raw)
    if len(고른) == 2:
        낸 = []
        for 접수, 이름 in 고른:
            p, _ = 풀기(접수)
            낸.append((p, 접수, 이름))
        if all(x[0] for x in 낸):
            return 뿌리, 낸[0], 낸[1]
    # 제출이력이 없거나 원문이 모자라면 _raw 의 사업{해} 원문 중 최근 둘
    있는 = sorted({p for r in 뿌 if r and os.path.isdir(r)
                 for p in glob.glob(os.path.join(r, "사업*", "*.txt"))
                 if re.fullmatch(r"\d{14}\.txt", os.path.basename(p))}, key=_해딱지)
    if len(있는) >= 2:
        a, b = 있는[-2], 있는[-1]
        return 뿌리, (a, os.path.basename(a)[:14], None), (b, os.path.basename(b)[:14], None)
    return 뿌리, (None, None, None), (None, None, None)


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False, description="같은 회사 두 보고서의 같은 절을 문장 단위로 견준다")
    ap.add_argument("가정", nargs="?")
    ap.add_argument("--앞")
    ap.add_argument("--뒤")
    ap.add_argument("--절", help="쉼표로 가른 절 이름(기본: 문장비교설정.json)")
    ap.add_argument("--받기", action="store_true")
    ap.add_argument("--낼")
    a = ap.parse_args()
    if not a.가정 and not (a.앞 and a.뒤):
        ap.print_help()
        return 입력오류
    if a.가정 and not os.path.exists(a.가정):
        print("가정 파일이 없습니다: %s" % a.가정)
        return 입력오류
    설정 = 설정읽기()
    뿌리, 앞, 뒤 = 입력정하기(a.가정, a.앞, a.뒤, a.받기)
    if not 앞[0] or not 뒤[0]:
        print("원문을 찾지 못했습니다 — 앞 %s · 뒤 %s. 접수번호를 주고 --받기 로 받거나 원문 txt 경로를 준다" % (앞[1], 뒤[1]))
        return 입력오류
    글앞 = io.open(앞[0], encoding="utf-8", errors="replace").read()
    글뒤 = io.open(뒤[0], encoding="utf-8", errors="replace").read()
    절들 = [x.strip() for x in a.절.split(",")] if a.절 else None
    결과 = 비교(글앞, 글뒤, 설정, "앞(%s)" % (앞[1] or os.path.basename(앞[0])), "뒤(%s)" % (뒤[1] or os.path.basename(뒤[0])), 절들)
    낸 = {"형식": "문장비교 1", "만든날": datetime.date.today().isoformat(),
         "설정": dict({k: 설정[k] for k in ("큰절", "같음문턱", "바뀜문턱", "최소한글", "숫자비중상한", "최대신호")}, 절=절들 or 설정["절"]),
         "입력": {"앞": {"경로": 앞[0], "접수": 앞[1], "보고서": 앞[2]}, "뒤": {"경로": 뒤[0], "접수": 뒤[1], "보고서": 뒤[2]}},
         **결과}
    p = a.낼 or os.path.join(뿌리, "_raw", "문장비교.json")
    os.makedirs(os.path.dirname(os.path.abspath(p)), exist_ok=True)
    io.open(p, "w", encoding="utf-8").write(json.dumps(낸, ensure_ascii=False, indent=1))
    s = 결과["요약"]
    print("절 %d 중 %d 견줌 · 같음 %d · 바뀜 %d(숫자 %d) · 새 %d · 빠짐 %d · 신호 %d"
          % (s["절수"], s["견준절"], s["같음"], s["바뀜"], s["숫자바뀜"], s["새"], s["빠짐"], len(결과["신호"])))
    print("→ %s" % p)
    return 발견 if any(x["종류"] == "절 찾지 못함" for x in 결과["신호"]) else 통과


if __name__ == "__main__":
    sys.exit(main())

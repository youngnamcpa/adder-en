# -*- coding: utf-8 -*-
"""신호 파일 — 기저율 · 이례 신호를 내는 갈래 산출물의 목록과 읽기를 한 곳에 둔다 (2026-10-21).

자체검사 51(R-167) · 모순장부 M-10 · 거친바퀴의 「기저율 자리」가 **같은 목록**을 읽는다(두 벌 두지 않는다 —
목록이 갈라지면 한쪽만 새 도구를 안다).

신호 꼴 — 도구마다 산출 JSON 의 최상위 `신호` 목록:
    {"출처": 도구 이름, "종류": 짧은 이름, "대상": 시나리오 · 연도 · 항목 · 회사, "값": 수 또는 글,
     "문턱": 수 또는 글, "글": 한 문장, "등급": "경보" | "참고"}
값을 바꾸는 도구는 없다. 신호는 「이 가정이 같은 집단 · 자기 과거 · 말과 실현에서 어디에 서는가」의 관측이고,
경보는 그 위치를 근거 칸에 적었는지 사람이 답할 자리다(검토의견 R-167 · 모순장부 「해소」).
"""
import io
import json
import os

# (가정 곁 `_raw/` 아래 이름, 그 파일을 내는 도구) — 2026-10-23 밤부터 `신호단계.json` 이 정본이다(실행기 `신호돌리기.py` 와 같은 표 —
# 목록과 실행 차례가 두 벌이면 한쪽만 새 도구를 안다). 배열 차례가 이 목록의 차례다. 「신호파일」: false 인 줄(민감도격자 — 신호 목록 없는 산출)은 뺀다
단계경로 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "신호단계.json")


def 단계읽기(p=None):
    """신호단계.json → dict. 깨졌으면 예외를 그대로 낸다(목록이 조용히 비면 자체검사 51 이 신호를 못 본다)."""
    with io.open(p or 단계경로, encoding="utf-8") as f:
        return json.load(f)


목록 = tuple((x["산출"].replace("/", os.sep), x["도구글"]) for x in 단계읽기()["도구"] if x.get("신호파일", True))
# 엔진 값(시나리오 경로)을 읽는 신호 — 가정 파일보다 오래되면 낡은 것이다(자체검사 51 이 다시 돌리라고 운다)
엔진값파일 = ("기저율.json", "조합이례도.json", "DCF적합성.json", "도착점가드.json", "확률가중.json",   # 둘은 2026-10-25 Y3(엔진을 돌린다)
         "모델밖가치.json",                                                                       # 2026-10-27 — 공시 밖 사업의 값(엔진 결과를 읽는다)
         "갭해석.json",                                                                           # 1.1.3 — 범위 밖 · 시장 변동 · 지주 · 배수 · 시나리오 폭(엔진 결과를 읽는다)
         "안정성장.json",                                                                         # 1.1.5 — (아래)
         "레짐.json",                                                                             # 1.1.6 — (아래)
         "고객경로.json")                                                                         # 1.1.6 — 레짐 기대값(레짐 묶음을 엔진으로) · 고객 경로 검증행(엔진 대조) — 레짐 기대값(레짐 묶음을 엔진으로 셈한다)
#                                                                                                   1.1.5 — 영구 자본비용 수렴 · 재투자 방향 · 적자 부문 · 연장 · 주식보상(엔진을 돌린다)
# 다른 갈래 산출을 읽어 낸 신호 — 그 입력(`_raw/` 아래 이름)이 신호 파일보다 새것이면 신호가 낡았다(2026-10-23 실측: 외부 제약의 재무약정 블록을
# 채운 뒤에도 조항후보의 「블록 빔」 신호가 남아 경보였다). 자체검사 51 은 낡은 파일의 신호를 싣지 않고 「다시 돌린다」 한 줄로 바꾼다
입력파일 = {"조항후보.json": ("외부제약.json",), "조항대조.json": ("외부제약.json",)}
값해시키 = "가정값해시"            # 엔진 값 신호에 찍는 가정의 값 해시(`가정해시.값` — 글 블록을 뺀 것). 신호돌리기가 도구를 돌린 뒤 찍는다


def 값해시(가정경로):
    """가정 파일의 값 해시(글 블록 · 원고 넣기가 채우는 관측 글을 뺀 것). 못 읽으면 None."""
    try:
        import 가정해시                                         # noqa: PLC0415
        with io.open(가정경로, encoding="utf-8") as f:
            return 가정해시.값(json.load(f))
    except Exception:                                          # noqa: BLE001
        return None


def 값해시찍기(신호경로, 가정경로):
    """신호 파일(최상위가 사전인 JSON)에 지금 가정의 값 해시를 찍는다 → 찍었나."""
    h = 값해시(가정경로)
    try:
        with io.open(신호경로, encoding="utf-8") as f:
            d = json.load(f)
    except (OSError, ValueError):
        return False
    if not isinstance(d, dict) or h is None:
        return False
    if d.get(값해시키) == h:
        return True
    d[값해시키] = h
    with io.open(신호경로, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)
    return True


def 낡음(신호경로, 가정경로, 내용=None):
    """엔진 값 신호가 지금 가정보다 낡았나(G2).

    신호에 값 해시가 찍혔으면 그것으로 본다 — 원고 넣기 · 검토 의견처럼 엔진이 읽지 않는 글만 바뀐 가정은 신호를 낡게 하지 않는다.
    값 해시가 없는 옛 신호는 종전처럼 파일 시각으로 본다(가정 파일이 신호보다 새것이면 낡음)."""
    if not (신호경로 and 가정경로 and os.path.exists(신호경로) and os.path.exists(가정경로)):
        return False
    if 내용 is None:
        try:
            with io.open(신호경로, encoding="utf-8") as f:
                내용 = json.load(f)
        except (OSError, ValueError):
            내용 = None
    찍힌 = 내용.get(값해시키) if isinstance(내용, dict) else None
    if 찍힌:
        return 찍힌 != 값해시(가정경로)
    return os.path.getmtime(신호경로) < os.path.getmtime(가정경로)


def 읽기(raw):
    """`raw` 폴더(가정 곁 `_raw/`)의 신호 파일 → [{이름, 도구, 경로, 내용, 신호, 문제}] — 있는 파일만.
    문제 = None(정상) · "JSON 깨짐" · "신호 목록 없음". 신호 = 꼴이 dict 인 것만."""
    낸 = []
    if not raw or not os.path.isdir(raw):
        return 낸
    for 이름, 도구 in 목록:
        p = os.path.join(raw, 이름)
        if not os.path.exists(p):
            continue
        한 = {"이름": 이름.replace(os.sep, "/"), "도구": 도구, "경로": p, "내용": None, "신호": [], "문제": None}
        try:
            내용 = json.load(io.open(p, encoding="utf-8"))
        except (OSError, ValueError) as e:
            한["문제"] = "JSON 깨짐 — %s" % e
            낸.append(한)
            continue
        한["내용"] = 내용
        신 = 내용.get("신호") if isinstance(내용, dict) else None
        if not isinstance(신, list):
            한["문제"] = "신호 목록 없음(형식 %s)" % ((내용 or {}).get("형식") if isinstance(내용, dict) else type(내용).__name__)
        else:
            한["신호"] = [s for s in 신 if isinstance(s, dict)]
        낸.append(한)
    return 낸


def 한줄(s, 도구=""):
    """신호 하나를 한 줄 글로."""
    return "[%s] %s — %s: %s" % (s.get("출처") or 도구, s.get("종류") or "-", s.get("대상") or "-", s.get("글") or "")

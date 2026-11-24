# -*- coding: utf-8 -*-
"""βU다시셈 — 이미 낸 유사기업 βU 산출을 **표본 그대로** 단일 출처 세율로 다시 벗긴다(2026-10-24 W18 · 유니버스 조사 물결 실측).

왜 있는가
    조립기(`peer_조립.py` · `peer_βU_us.py`)가 `--세율` 을 사람이 적게 해서 같은 유니버스의 공통 세율이 0.21 · 0.25 · 0.264 · 0.275 로 갈렸다
    (`무차입세율.py` 머리). 조립기는 이제 단일 출처를 쓰지만, 이미 공용 캐시(`조사/<국가>/<코드>/C2/peers/βU_*.json`)에 쌓인 산출은
    옛 세율로 벗긴 그대로다. 시세 · 재무를 다시 받지 않고 그 산출의 행만으로 다시 셈한다 — **결과만 바꾸고 표본은 그대로.**

하는 일
    · 단일 시장 산출(국내 조립 · 미국 조립): 회사별 세율이 **법령 세율표(국내) · `--세율표`(미국 — 소재국)** 에서 온 행은 그대로 두고,
      공통 세율로 벗긴 행만 단일 출처 공통 세율로 바꾼다. βU · 현금보정 βU · 담보부 제외 βU · 본값 칸(`βU본값.본값행`)을 다시 셈하고,
      요약(세 방식 · 미래사업 슬롯 · 담보부 제외 대조 · 본값 규칙 · 상장시장 지수 대안)과 산업 βU 대조의 비율(저장된 산업 βU 로)을 다시 낸다
    · 병합 산출(`peer_병합.py`): 같은 폴더의 입력 산출을 다시 셈한 뒤 `peer_병합.병합` 으로 다시 합친다
    · 같은 세율로 돌리면 저장된 값이 그대로 나와야 한다(`항등점검` — 다시 셈 식이 조립기와 갈리지 않았는지 보는 시험)
    · 1.1.4 — 축소를 다시 낸다(`축소` 명령): 병합 산출도 산업 βU 대조를 살려 축소한다(종전 `병합다시` 가 대상 없이 불러 「업종 βU 가 없다 — w = 1」) ·
      `--비교 <다른 창 산출>` 이면 창 이동 폭(같은 표본 · 두 창 끝의 차)을 불확실성에 · `--사전지역` · `--산업줄` 로 사전값 업종 줄을 본선 판단과 맞춤 ·
      `--가정` 이면 대상 자체가 없는 미국 산출에 주봉 캐시로 대상 자체 회귀를 더하고(R4) 축소 결과의 서열 하한(Ke ≥ 세전 Kd + 문턱)을 적는다

    python 스크립트/βU다시셈.py 축소 _raw/peers/βU_<표본>.json [--비교 _raw/peers/βU_<F 창 표본>.json] [--사전지역 GLOBAL] [--산업줄 "<다모다란 줄>"]
                                [--가정 가정.json] [-o _raw/peers/βU_<새 이름>.json]
회사 · 업종 이름은 이 도구에 없다(범용).
"""
from __future__ import annotations

import copy
import io
import json
import math
import os
import statistics
import sys

여기 = os.path.dirname(os.path.abspath(__file__))
if 여기 not in sys.path:
    sys.path.insert(0, 여기)

import βU본값 as 본  # noqa: E402
import 무차입세율 as 무세  # noqa: E402
from peer_βU_us import 세방식 as 조립세방식  # noqa: E402  — 두 조립기의 보정전 · 현금보정 요약이 쓰는 식(본값 규칙은 βU본값.세방식)

허용 = 1e-9


def 종류(d):
    """산출 꼴 → 'KR'(국내 조립) · 'US'(미국 조립) · '병합' · None."""
    if not isinstance(d, dict) or not isinstance(d.get("표"), list):
        return None
    머 = d.get("머리") or {}
    if isinstance(머.get("입력"), list):
        return "병합"
    if "조립csv" in d:
        return "US"
    if "표본" in 머 or any("종목코드" in z for z in d["표"]):
        return "KR"
    return None


def _보정(βU, 비중):
    if βU is None or 비중 is None or 비중 >= 1:
        return None
    return βU / (1 - 비중)


def _행세율고정(z, 꼴):
    """그 행의 세율이 회사별 출처(법령 세율표 · --세율표)에서 왔나."""
    if 꼴 == "KR":
        return ("%s" % (z.get("세율근거") or "")).startswith("법령 세율표")
    return z.get("세율출처") == "--세율표"


def _행다시(z, 꼴, 공통, 출처, ERP):
    """행 하나 — 공통 세율 행이면 세율을 바꾸고 βU 칸을 다시 셈한다. 바꿨으면 True."""
    바꿈 = False
    if not _행세율고정(z, 꼴) and 공통 is not None:
        옛 = z.get("세율")
        if 옛 is None or abs(옛 - 공통) > 허용:
            바꿈 = True
        if 꼴 == "KR":
            덧 = (z.get("세율근거") or "")
            꼬 = (" — " + 덧.split(" — ", 1)[1]) if " — " in 덧 and "영업이익" in 덧 else ""
            z["세율근거"] = "단일 출처 공통(%s)%s" % (출처, 꼬)
        else:
            z["세율출처"] = "단일 출처 공통(%s)" % 출처
        # 담보부 제외 βU(미국)는 옛 세율로 x = D2/E 를 되짚어 다시 벗긴다
        if z.get("βU_담보부제외") and z.get("βL") is not None and 옛 is not None and 옛 < 1:
            x = (z["βL"] / z["βU_담보부제외"] - 1) / (1 - 옛)
            z["βU_담보부제외"] = z["βL"] / (1 + (1 - 공통) * x)
        z["세율"] = 공통
    t = z.get("세율")
    if z.get("βL") is not None and z.get("DE") is not None and t is not None:
        z["βU"] = z["βL"] / (1 + (1 - t) * z["DE"])
    if z.get("βU") is not None and z.get("현금비중") is not None:
        z["βU_현금보정"] = _보정(z["βU"], z["현금비중"])
    본.본값행(z, ERP)
    return 바꿈


def _핵(표):
    return [z for z in 표 if z.get("핵심")] if any(z.get("구분") for z in 표) else 표


def _산업다시(산업, b):
    """저장된 산업 βU 로 비교 · ★ 만 다시(다모다란 표를 다시 읽지 않는다)."""
    if not isinstance(산업, dict) or not 산업.get("줄") or b is None:
        return 산업
    s = copy.deepcopy(산업)
    폭 = s.get("대조폭") or 0.30
    지 = s.get("지역") or "GLOBAL"
    기준들 = [x for x in s.get("산업") or [] if x.get("지역") in ("GLOBAL", 지) and x.get("βU현금보정")]
    s["비교"] = [{"지역": x["지역"], "산업βU": x["βU현금보정"], "비": b / x["βU현금보정"]} for x in 기준들]
    밖 = [c for c in s["비교"] if abs(c["비"] - 1) > 폭]
    s["★"] = bool(기준들) and len(밖) == len(s["비교"])
    s["문장"] = ("핵심 중앙값 βU %.3f 대 다모다란 「%s」 현금보정 βU %s%s" % (
        b, s["줄"], " · ".join("%s %.3f(%.0f%%)" % (c["지역"], c["산업βU"], c["비"] * 100) for c in s["비교"]) or "없음",
        " — ★ 둘 다 ±%d%% 밖(표본이 업종 위험을 못 담는지 본다 — 해외 동종 경로 · 산업 βU 대안 사양)" % (폭 * 100)
        if s["★"] else ""))
    return s


def _요약(d, 꼴, 공통, ERP):
    """조립기의 요약 블록을 그대로 다시 낸다(peer_조립.βU요약 · peer_βU_us.main 과 같은 차례)."""
    표 = d["표"]
    핵 = _핵(표)
    옛 = d.get("요약") or {}
    요 = {}
    for 이름, 묶음 in (("핵심", 핵), ("전체", 표)):
        요[이름] = {"보정전": 조립세방식([z for z in 묶음 if z.get("βU") is not None], 공통),
                  "현금보정": 조립세방식([z for z in 묶음 if z.get("βU_현금보정") is not None], 공통, "βU_현금보정", "현금비중")}
        ok = [z for z in 묶음 if z.get("βU_현금보정") is not None]
        if ok:
            요[이름]["참고_중앙값βU÷(1−중앙값현금비중)"] = (statistics.median(z["βU"] for z in ok)
                                                    / (1 - statistics.median(z["현금비중"] for z in ok)))
        요[이름]["현금보정_제외"] = [(z["티커"], z.get("현금보정_확인불가")) for z in 묶음
                                 if z.get("βU") is not None and z.get("βU_현금보정") is None]
        for k in ("지수혼합",):
            if k in (옛.get(이름) or {}):
                요[이름][k] = 옛[이름][k]
    if any(z.get("미래사업슬롯") for z in 핵):
        포함 = 조립세방식([z for z in 핵 if z.get("βU_현금보정") is not None], 공통, "βU_현금보정", "현금비중")
        제외 = 조립세방식([z for z in 핵 if z.get("βU_현금보정") is not None and not z.get("미래사업슬롯")], 공통, "βU_현금보정", "현금비중")
        요["미래사업슬롯"] = {"포함": 포함, "제외": 제외}
        if 포함.get("표본수") and 제외.get("표본수"):
            차 = abs(포함["(b)개별중앙값_기본"] - 제외["(b)개별중앙값_기본"])
            요["미래사업슬롯"].update({"중앙값차": 차, "경보": 차 > 0.15})
    if 꼴 == "US" and any(z.get("βU_담보부제외") for z in 핵):
        대조 = [dict(z, βU=(z.get("βU_담보부제외") or z.get("βU"))) for z in 핵]
        for z in 대조:
            if z.get("βU_담보부제외") and z.get("현금비중") is not None:
                z["βU_현금보정"] = _보정(z["βU"], z["현금비중"])
        요["핵심_담보부제외대조"] = 조립세방식([z for z in 대조 if z.get("βU_현금보정") is not None], 공통, "βU_현금보정", "현금비중")
    for 이름, 묶음 in (("핵심", 핵), ("전체", 표)):
        요[이름]["본값규칙"] = 본.요약(묶음, 공통, ERP)
        if 꼴 == "KR":
            상장 = [dict(z, βL=z["βL_상장지수"]) for z in 묶음 if not z.get("본값제외") and z.get("βL_상장지수") is not None]
            for z in 상장:
                bu = 본.무차입(z["βL"], z.get("DE_본"), z.get("세율"), z.get("부채베타"))
                z["βU_상장"] = _보정(bu, z.get("현금비중_본")) if bu is not None else None
            요[이름]["본값규칙"]["대안_상장지수"] = 본.세방식([z for z in 상장 if z.get("βU_상장") is not None], 공통, "βU_상장", "현금비중_본")
    return 요


def 기본값(d):
    b = ((d.get("본값") or {}).get("핵심") or {})
    return {"기본값": (b.get("기본값") or {}).get("값"), "기본값출처": (b.get("기본값") or {}).get("출처"),
            "본값b": (b.get("본값") or {}).get("(b)개별중앙값_기본"), "본값n": (b.get("본값") or {}).get("표본수", 0),
            "포함b": (b.get("포함") or {}).get("(b)개별중앙값_기본")}


def 다시셈(d, 기준일=None, 세율=None, 출처=None):
    """단일 시장 산출 → (새 산출, 바꾼 행 수). 세율을 주면 그 값(항등점검용), 아니면 무차입세율 단일 출처."""
    꼴 = 종류(d)
    if 꼴 not in ("KR", "US"):
        raise ValueError("단일 시장 산출이 아니다(%s)" % 꼴)
    d = copy.deepcopy(d)
    기 = 기준일 or d.get("기준일") or (d.get("머리") or {}).get("기준일")
    if 세율 is None:
        r = 무세.공통세율(꼴, 기)
        세율, 출처 = r["값"], r["출처"]
    if 세율 is None:
        raise ValueError("단일 출처 세율을 정하지 못했다(%s)" % 출처)
    ERP = (d.get("본값") or {}).get("ERP")
    n = sum(1 for z in d["표"] if _행다시(z, 꼴, 세율, 출처 or "지정", ERP))
    요 = _요약(d, 꼴, 세율, ERP)
    d["요약"] = 요
    d["세율"] = 세율
    if 꼴 == "KR":
        d.setdefault("머리", {})["세율"] = 세율
        d["머리"]["세율출처"] = 출처
    else:
        d["세율출처"] = 출처
    bv = d.setdefault("본값", {})
    bv["핵심"] = 요["핵심"]["본값규칙"]
    bv["판정"] = bv["핵심"].get("판정")
    bv["기본값"] = bv["핵심"].get("기본값")
    bv["산업대조"] = _산업다시(bv.get("산업대조"), (bv["핵심"].get("본값") or {}).get("(b)개별중앙값_기본"))
    # 1.1.3(B1) — 그날의 βU 규칙 전체: 정밀도 가중 축소(조립기와 같은 함수). 세 겹의 ② 는 다시 셈한 본값 (b)(표본 셋 이상)로 바꿔 넣는다
    b = bv["핵심"].get("본값") or {}
    겹 = copy.deepcopy(bv.get("세겹")) if isinstance(bv.get("세겹"), dict) else None
    if 겹 is not None:
        겹["전체중앙값"] = b.get("(b)개별중앙값_기본") if b.get("표본수", 0) >= 본.기본값최소표본 else None
    축소다시(d, 겹=겹)
    return d, n


def 축소다시(d, 이동=None, 사전지역=None, 서열W=None, 겹=None):
    """산출 하나(단일 · 병합)의 본값 · 산업대조 · 대상자체로 정밀도 가중 축소를 다시 내고 기본값을 덮는다(기본값 규칙 「축소」 일 때). → 축소 블록.
    1.1.4 — 이동(창 이동 폭) · 사전지역 · 서열W(엔진 3번 WACC 예측기간 — 있으면 서열 하한)를 받는다."""
    bv = d.setdefault("본값", {})
    핵 = bv.get("핵심") or {}
    if 겹 is None:
        겹 = bv.get("세겹") if isinstance(bv.get("세겹"), dict) else None
    if 겹 is None and 종류(d) == "병합":
        겹 = {}
    축 = 본.축소규칙(_핵(d["표"]), 겹, bv.get("산업대조"), bv.get("대상자체"), bv.get("대상자체판정"), 핵.get("구간95"), None, 이동, 사전지역)
    if isinstance(서열W, dict) and 축.get("적용"):
        s = 본._축소설정()
        서 = 본.서열하한(축["사후"], 서열W, float(s.get("서열문턱", 0.01)))
        if 서:
            축["서열"] = 서
            if 서.get("경보"):
                축["★"] = True
                축["까닭"] = 축.get("까닭", "") + " · 서열 — Ke %.2f%% < 세전 Kd %.2f%% + %.1f%%p(문턱까지 올린 βU %.3f)" % (
                    서["Ke"] * 100, 서["Kd"] * 100, 서["문턱"] * 100, 서["하한βU"])
    if 종류(d) == "병합" and isinstance(bv.get("세겹"), dict):
        bv["세겹"]["축소규칙"] = 축
    bv["축소"] = 축
    if (bv.get("기본값규칙") or "축소") == "축소" and 축.get("적용") and isinstance(핵, dict) and 핵:
        if "기본값_옛규칙" not in 핵:
            핵["기본값_옛규칙"] = 핵.get("기본값")
        핵["기본값"] = 본.축소기본값(핵.get("기본값_옛규칙") or 핵.get("기본값"), 축)
        bv["기본값"] = 핵["기본값"]
    return 축


def 병합다시(d, 폴더, 대체=None):
    """병합 산출 → 새 병합. 입력은 폴더의 같은 이름 파일, `대체`{파일이름: 새 산출} 가 있으면 그것(쓰기 전 보기)."""
    import contextlib                                   # noqa: PLC0415
    import tempfile                                     # noqa: PLC0415
    import peer_병합 as 병                             # noqa: PLC0415
    머 = d.get("머리") or {}
    with tempfile.TemporaryDirectory() as 임:
        입력 = []
        for o in 머.get("입력") or []:
            p = os.path.join(폴더, o["파일"])
            if 대체 and o["파일"] in 대체:
                p = os.path.join(임, o["파일"])
                json.dump(대체[o["파일"]], io.open(p, "w", encoding="utf-8"), ensure_ascii=False, default=str)
            if not os.path.exists(p):
                raise ValueError("병합 입력이 없다 — %s" % o["파일"])
            입력.append((p, bool(o.get("전부핵심"))))
        with contextlib.redirect_stdout(io.StringIO()):          # 병합 경보는 산출의 `병합경보` 칸에 남는다
            새 = 병.병합(입력, None, 머.get("기준일"), None)
    b = (새["본값"]["핵심"].get("본값") or {}).get("(b)개별중앙값_기본")
    새["본값"]["산업대조"] = _산업다시((d.get("본값") or {}).get("산업대조"), b)
    for k in ("쓰는법",):
        if k in (d.get("본값") or {}):
            새["본값"][k] = d["본값"][k]
    # 1.1.4 — 병합은 대상 티커 없이 불러 축소가 산업 βU 없이(w = 1) 돌았다. 살린 산업대조로 축소를 다시 낸다(옛 산출의 대상 자체 · 판정도 이어받는다)
    for k in ("대상자체", "대상자체판정"):
        if 새["본값"].get(k) is None and (d.get("본값") or {}).get(k) is not None:
            새["본값"][k] = d["본값"][k]
    축소다시(새)
    return 새


def _같다(a, b, 경로="", 틀린=None):
    틀린 = [] if 틀린 is None else 틀린
    if isinstance(a, dict) and isinstance(b, dict):
        for k in set(a) | set(b):
            _같다(a.get(k), b.get(k), "%s.%s" % (경로, k), 틀린)
    elif isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        if len(a) != len(b):
            틀린.append("%s 길이 %d≠%d" % (경로, len(a), len(b)))
        for i, (x, y) in enumerate(zip(a, b)):
            _같다(x, y, "%s[%d]" % (경로, i), 틀린)
    elif isinstance(a, float) or isinstance(b, float):
        if a is None or b is None or isinstance(a, str) or isinstance(b, str) or not (
                (math.isnan(a) and math.isnan(b)) or abs(a - b) <= 1e-9 * max(1.0, abs(a), abs(b))):
            틀린.append("%s %r≠%r" % (경로, a, b))
    elif a != b:
        틀린.append("%s %r≠%r" % (경로, a, b) if not isinstance(a, str) or len("%s" % a) < 80 else "%s 글 다름" % 경로)
    return 틀린


def 항등점검(d):
    """저장된 세율 그대로 다시 셈 → 저장된 요약 · 본값과 같은가. → 틀린 경로 목록(비면 같다)."""
    꼴 = 종류(d)
    공통 = d.get("세율") if d.get("세율") is not None else (d.get("머리") or {}).get("세율")
    새, _ = 다시셈(d, 세율=공통, 출처="항등점검")
    # 세율 출처 글 · 행 근거 글은 다시 셈이 바꾸는 칸이라 빼고 수치 칸만 본다
    비교칸 = ["요약", "본값"]
    틀린 = []
    for k in 비교칸:
        a, b = d.get(k) or {}, 새.get(k) or {}
        if k == "본값":
            a = {x: a.get(x) for x in ("핵심", "판정", "기본값")}
            b = {x: b.get(x) for x in ("핵심", "판정", "기본값")}
        _같다(json.loads(json.dumps(a, default=str)), json.loads(json.dumps(b, default=str)), k, 틀린)
    for i, (z, y) in enumerate(zip(d["표"], 새["표"])):
        for c in ("βU", "βU_현금보정", "βU_본", "βU_본전"):
            _같다(z.get(c), y.get(c), "표[%d].%s" % (i, c), 틀린)
    return [x for x in 틀린 if 꼴]


def 파일다시셈(p, 쓰기=False, 대체=None, 새것=None):
    """파일 하나 → 표 한 줄 dict. 쓰기면 덮어쓴다(옛 파일 보관은 부르는 쪽 몫).

    기본값을 셋 적는다 — 저장(그 산출을 낸 판) · 옛 세율 그대로 지금 규칙(규칙판 차이만) · 단일 출처 세율(세율 차이까지).
    둘째와 셋째의 차가 세율 효과다(첫째와 둘째의 차는 βU본값 규칙이 그 뒤 바뀐 몫)."""
    d = json.load(io.open(p, encoding="utf-8"))
    꼴 = 종류(d)
    전 = 기본값(d)
    항 = None
    if 꼴 == "병합":
        새 = 병합다시(d, os.path.dirname(p), 대체)
        n, 옛세, 새세 = None, None, None
    elif 꼴 in ("KR", "US"):
        옛세 = d.get("세율") if d.get("세율") is not None else (d.get("머리") or {}).get("세율")
        if 옛세 is not None:
            항 = 기본값(다시셈(d, 세율=옛세, 출처="옛 세율")[0])
        새, n = 다시셈(d)
        새세 = 새["세율"]
    else:
        return {"파일": os.path.basename(p), "꼴": None, "까닭": "βU 산출 꼴이 아니다"}
    후 = 기본값(새)
    if 새것 is not None:
        새것[os.path.basename(p)] = 새
    if 쓰기:
        임 = p + ".쓰는중"
        json.dump(새, io.open(임, "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
        os.replace(임, p)
    return {"파일": os.path.basename(p), "꼴": 꼴, "세율전": 옛세, "세율후": 새세, "바꾼행": n,
            "기본값저장": 전["기본값"], "기본값옛세율": (항 or {}).get("기본값"), "기본값후": 후["기본값"],
            "본값b저장": 전["본값b"], "본값b옛세율": (항 or {}).get("본값b"), "본값b후": 후["본값b"],
            "본값n저장": 전["본값n"], "본값n후": 후["본값n"], "기본값출처": 후["기본값출처"],
            "병합경보": ((새.get("본값") or {}).get("핵심") or {}).get("병합경보") if 꼴 == "병합" else None}


def 폴더다시셈(폴더, 쓰기=False):
    """peers 폴더 하나의 βU_*.json — 단일 시장 먼저, 병합은 뒤에. → [표 줄]."""
    if not os.path.isdir(폴더):
        return []
    파일 = sorted(f for f in os.listdir(폴더) if f.startswith("βU_") and f.endswith(".json"))
    꼴들 = {}
    for f in 파일:
        try:
            꼴들[f] = 종류(json.load(io.open(os.path.join(폴더, f), encoding="utf-8")))
        except (OSError, ValueError):
            꼴들[f] = None
    차례 = [f for f in 파일 if 꼴들[f] in ("KR", "US")] + [f for f in 파일 if 꼴들[f] == "병합"]
    낸, 새것 = [], {}
    for f in 차례:
        try:
            낸.append(파일다시셈(os.path.join(폴더, f), 쓰기, None if 쓰기 else 새것, 새것))
        except ValueError as e:
            낸.append({"파일": f, "꼴": 꼴들[f], "까닭": "%s" % e})
    return 낸


# ────────────────────────────────────────────────────────────── 1.1.4 축소 명령

def 축소명령(경로, 비교=None, 사전지역=None, 산업줄=None, 가정경로=None, 출력=None, 이동개월=None, 다시병합=False, 티커=None, 주봉폴더=None):
    """산출 하나를 읽어 축소를 다시 낸다(위 머리 「축소」). → (새 산출, 출력 경로, 알림 []). 주봉폴더 · 티커 — 산출을 옮겨 셈할 때 캐시 자리(기본은 산출 곁)."""
    알 = []
    d = json.load(io.open(경로, encoding="utf-8"))
    폴더 = 주봉폴더 or os.path.dirname(os.path.abspath(경로))
    꼴 = 종류(d)
    if 꼴 is None:
        raise ValueError("βU 산출 꼴이 아니다 — %s" % 경로)
    if 꼴 == "병합" and 다시병합:                            # 입력 산출로 다시 합친다(입력이 바뀌었을 때) — 기본은 이 산출의 표본 그대로 축소만
        d = 병합다시(d, 폴더)
    bv = d.setdefault("본값", {})
    W = None
    if 가정경로:
        from 엔진.계산 import 계산                            # noqa: PLC0415
        가정 = json.load(io.open(가정경로, encoding="utf-8"))
        W = (계산(가정, "기준").get("WACC") or {}).get("예측기간")
        if 꼴 == "US" and not bv.get("대상자체"):
            t = ("%s" % (티커 or ((가정.get("메타") or {}).get("티커")) or _대상티커(폴더) or ((bv.get("산업대조") or {}).get("대상")) or "")).strip().upper()
            s = 본._축소설정()
            if t:
                대, 까 = 본.대상자체주봉(폴더, t, "_INX", d.get("기준일") or (가정.get("메타") or {}).get("평가기준일"), W,
                                    이동개월=이동개월 if 이동개월 is not None else s.get("창이동개월"), 세율=d.get("세율"))
                if 대:
                    bv["대상자체"] = 대
                    bv["대상자체판정"] = 본.대상자체판정(대, {})
                    알.append("대상 자체 회귀를 더했다 — βL %.3f · R² %.3f · %d주 → βU %.3f" % (대["βL"], 대["R2"], 대["표본주"], 대["βU_본"]))
                else:
                    알.append("대상 자체 회귀를 못 더했다 — %s" % 까)
            else:
                알.append("대상 티커를 몰라 자체 회귀를 더하지 못했다(가정 메타.티커)")
    if 산업줄:
        import 산업베타 as _ib                                # noqa: PLC0415
        b = ((bv.get("핵심") or {}).get("본값") or {}).get("(b)개별중앙값_기본")
        옛 = bv.get("산업대조")
        새 = _ib.대조값(None, b, d.get("기준일") or (d.get("머리") or {}).get("기준일"), 산업줄, 사전지역 or (옛 or {}).get("지역"))
        if not 새.get("산업"):
            raise ValueError("산업 줄 「%s」 을 못 읽었다 — %s" % (산업줄, 새.get("문장")))
        새["선택"] = "사람(--산업줄)"
        bv["산업대조_이전"] = 옛
        bv["산업대조"] = 새
    이동 = None
    if 비교:
        F = json.load(io.open(비교, encoding="utf-8"))
        이동 = 본.창이동폭(d, F)
        이동["비교"] = os.path.basename(비교)
        알.append("창 이동 폭 — %s" % (이동.get("근거") or "짝 없음"))
    elif isinstance((bv.get("대상자체") or {}).get("창이동"), dict):
        이동 = {"대상 자체": bv["대상자체"]["창이동"]["차"], "근거": bv["대상자체"]["창이동"]["글"]}
    축 = 축소다시(d, 이동, 사전지역, W)
    if 사전지역:
        bv["축소"]["사전지역"] = 사전지역
    출 = 출력 or 경로
    임 = 출 + ".쓰는중"
    json.dump(d, io.open(임, "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
    os.replace(임, 출)
    return d, 출, 알


def main(argv=None):
    import argparse                                         # noqa: PLC0415
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:                                        # noqa: BLE001
        pass
    ap = argparse.ArgumentParser(allow_abbrev=False, description="βU 산출 다시 셈 — 축소(1.1.4)")
    sub = ap.add_subparsers(dest="명령", required=True)
    a1 = sub.add_parser("축소", help="정밀도 가중 축소를 다시 낸다(창 이동 폭 · 사전지역 · 산업줄 · 대상 자체 · 서열 하한)")
    a1.add_argument("산출")
    a1.add_argument("--비교", default=None, help="같은 표본을 다른 창 끝으로 셈한 산출(F 창 · 끝을 옮긴 창) — 두 판의 차를 창 이동 폭으로")
    a1.add_argument("--사전지역", default=None, help="사전값 업종 βU 의 지역 줄(GLOBAL · EM · US …) — 본선이 고른 줄과 맞춘다")
    a1.add_argument("--산업줄", default=None, help="사전값 업종 줄 이름(다모다란 Industry Group) — 본선이 판단으로 고른 줄")
    a1.add_argument("--가정", default=None, help="가정 파일 — 서열 하한(엔진 3번 WACC) · 미국 산출의 대상 자체 회귀(주봉 캐시)")
    a1.add_argument("--이동개월", type=int, default=None, help="대상 자체 창 이동 폭의 개월(기본 설정 「창이동개월」)")
    a1.add_argument("--다시병합", action="store_true", help="병합 산출을 입력 산출로 다시 합친 뒤 축소(기본은 표본 그대로)")
    a1.add_argument("--티커", default=None, help="대상 티커(비우면 가정 메타 · peers/대상.json · 진행판 · SEC 제출 목록)")
    a1.add_argument("--주봉폴더", default=None, help="주봉 캐시 폴더(비우면 산출 곁)")
    a1.add_argument("-o", "--출력", default=None, help="새 산출 경로(비우면 덮는다 — 옛 판 보관은 부르는 쪽 몫)")
    a = ap.parse_args(argv)
    try:
        d, 출, 알 = 축소명령(a.산출, a.비교, a.사전지역, a.산업줄, a.가정, a.출력, a.이동개월, a.다시병합, a.티커, a.주봉폴더)
    except (OSError, ValueError) as e:
        print("멈춤 — %s" % e)
        return 2
    축 = (d.get("본값") or {}).get("축소") or {}
    for x in 알:
        print("  " + x)
    print("축소 — %s" % 축.get("까닭"))
    if 축.get("적용"):
        print("  사후 %.4f · w %.3f%s" % (축["사후"], 축["w"], " · ★" if 축.get("★") else ""))
    if 축.get("서열"):
        s = 축["서열"]
        print("  서열 — Ke %.2f%% · 세전 Kd %.2f%% · 차 %.2f%%p%s" % (s["Ke"] * 100, s["Kd"] * 100, s["차"] * 100,
                                                            (" — 경보 · 문턱까지 올린 βU %.4f" % s["하한βU"]) if s["경보"] else ""))
    print("→ %s" % 출)
    return 0



def _대상티커(폴더):
    """대상 티커 — peers 폴더의 `대상.json`(미국 조립기가 읽는 자리) → 회차 진행판(`진행판.json` 회사.종목) → SEC 제출 목록(`_raw/submissions.json`). 없으면 None."""
    회차 = os.path.dirname(os.path.dirname(os.path.abspath(폴더)))
    for p, 꺼냄 in ((os.path.join(폴더, "대상.json"), lambda j: j.get("티커")),
                  (os.path.join(회차, "진행판.json"), lambda j: (j.get("회사") or {}).get("종목")),
                  (os.path.join(회차, "_raw", "submissions.json"), lambda j: (j.get("tickers") or [None])[0])):
        try:
            if os.path.exists(p):
                v = 꺼냄(json.load(io.open(p, encoding="utf-8")) or {})
                if v:
                    return "%s" % v
        except (OSError, ValueError):
            continue
    return None


if __name__ == "__main__":
    sys.exit(main())

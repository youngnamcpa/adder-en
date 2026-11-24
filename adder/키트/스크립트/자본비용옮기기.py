# -*- coding: utf-8 -*-
"""자본비용옮기기 — 할인율(WACC) 대안 사양을 레터부록에서 가정 파일의 `자본비용` 블록으로 옮긴다(2026-10-24 결정 · W12).

    python 스크립트/자본비용옮기기.py <가정.json> [--레터부록 레터부록.json]     # 옮긴다(덮지 않는다 · 다르면 멈춘다)
    python 스크립트/자본비용옮기기.py <가정.json> --검사                       # 블록 꼴만 본다
    python 스크립트/자본비용옮기기.py <가정.json> --짓기 대안.json               # 레터부록이 없는 회사 — 대안 사양을 엔진으로 셈해 적는다

`--짓기` 의 대안.json 꼴: [{"사양": "3년 주간 회귀", "근거": "베타회귀.py 3년 창", "덮어쓰기": {"예측기간.베타u": 1.05, "영구기간.베타u": 1.05}}, …]
— 덮어쓰기 열쇠는 가정 `WACC` 블록 안의 자리(「구간.칸」)다. 엔진이 그 입력으로 WACC 를 다시 셈해 예측기간WACC · 영구기간WACC 를 적는다(값을 손으로
적지 않는다). `구조.할인.베타출처 = 유사기업표` 인 회사는 예측기간 칸에 `베타u` 가 없다(그 칸은 유사기업 표의 대표값 — 엔진 `wacc` 머리 · 구조확인).
그래서 덮어쓰기에 `예측기간.베타u` 가 오면 **그 대안의 사본에서만** 베타출처를 「직접」 으로 바꾸고 βu 를 넣는다(2026-10-26 W — 3년 창 · 월간 ·
업종 베타처럼 예측기간 βu 를 바꾼 대안). 가정 파일의 선언은 그대로이고, 바꾼 사실은 대안 줄의 「사본바꿈」 에 남는다.
같은 까닭으로 엔진이 읽는 선택 칸(엔진 `wacc` 의 WACC항목 · WACC새항목 — 규모프리미엄 · DE 등)은 가정에 비어 있어도 덮어쓰기로 받는다
(한국공인회계사회 가이던스 방식의 규모위험처럼 가정에 없는 칸을 더하는 대안). 엔진이 모르는 이름은 종전대로 걸린다.
대안의 재료는 키트 CLAUDE.md 가 「대안 사양으로 병기」 하라는 자리들이다 — 베타 회귀 3년 창(`베타회귀.py` 「대안」 줄) · 상장시장 지수
(`peer_조립` `대안_상장지수`) · 영구 βu 1 쪽 수렴 · 사업 지역 가중 CRP · 결손금 소진 전 한계세율 · 한 사이클 창 βL(C2) · 업종 βU(`산업베타.py`).

왜: 대안 사양(유사기업 묶음 · 베타 회귀 창 · 영구기간 베타 따위를 바꾼 WACC)은 할인율의 근거 범위다. 종전에는 레터 부록 B 를 쓸 때만 만드는
`레터부록.json` 에 있어서, 레터부록이 없는 회사는 결합 민감도 분포에 할인율이 빠졌다. 가정 파일에 두면 결합민감도 · 레터 · 워크북이
같은 자리에서 읽는다. **값은 바뀌지 않는다** — 엔진은 이 블록을 읽지 않는다(채택 WACC 는 종전대로 `WACC` · `스위치` 에서 엔진이 낸다).

블록 꼴(레터부록의 「자본비용」 그대로):
    "자본비용": {"방법": "채택 사양의 방법과 근거(문단)",
              "채택": {"사양": "…", "근거": "…"},
              "대안": [{"사양": "…", "예측기간WACC": 0.1276, "영구기간WACC": 0.1276, "근거": "…"}],
              "교차확인": [{"항목": "…", "값": "…", "근거": "…"}]}

읽는 차례(`읽기`): 가정 `자본비용` → 레터부록 `자본비용`(옛 회차 호환). 둘 다 있고 대안이 다르면 가정을 쓰고 알린다.
종료 코드 — 0 옮김 · 같음 · 꼴 통과 · 짓기 / 1 가정과 레터부록이 다름(멈춤) · 꼴 걸림 · 대안 셈 걸림 / 2 입력 오류(파일 없음 · 레터부록에 자본비용 없음).
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:                                    # noqa: BLE001
    pass

블록키 = "자본비용"


def _n(v):
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def 꼴검사(블):
    """블록 꼴 → 걸린 것 목록(빈 목록이면 통과)."""
    걸 = []
    if not isinstance(블, dict):
        return ["「자본비용」 은 객체여야 한다"]
    대 = 블.get("대안")
    if 대 is not None and not isinstance(대, list):
        걸.append("「자본비용.대안」 은 목록이어야 한다")
    for i, x in enumerate(대 or []):
        if not isinstance(x, dict):
            걸.append("「자본비용.대안[%d]」 은 객체여야 한다" % i)
            continue
        if _n(x.get("예측기간WACC")) is None and _n(x.get("βU")) is None:
            걸.append("「자본비용.대안[%d]」 에 예측기간WACC(숫자) 또는 βU(숫자 — 엔진이 WACC 를 다시 셈한다)가 없다" % i)
        if x.get("영구기간WACC") is not None and _n(x.get("영구기간WACC")) is None:
            걸.append("「자본비용.대안[%d].영구기간WACC」 는 숫자여야 한다" % i)
    if 블.get("채택") is not None and not isinstance(블.get("채택"), dict):
        걸.append("「자본비용.채택」 은 객체여야 한다")
    if 블.get("교차확인") is not None and not isinstance(블.get("교차확인"), list):
        걸.append("「자본비용.교차확인」 은 목록이어야 한다")
    return 걸


def 대안WACC(가정, x):
    """1.1.2(P21) — 대안 사양 한 줄의 (예측기간 WACC, 영구기간 WACC). WACC 를 적었으면 그 값, βU 로 댔으면 두 구간의 `WACC.<구간>.베타u` 를
    바꿔 엔진이 셈한 값(레터 부록 B 의 장부 키 「대안β」 와 같은 셈). 못 내면 (None, None)."""
    예, 영 = _n((x or {}).get("예측기간WACC")), _n((x or {}).get("영구기간WACC"))
    if 예 is not None:
        return 예, (영 if 영 is not None else 예)
    b = _n((x or {}).get("βU"))
    if b is None or not isinstance(가정, dict):
        return None, None
    try:
        import copy as _c                                    # noqa: PLC0415
        import importlib as _i                               # noqa: PLC0415
        a = _c.deepcopy(가정)
        if isinstance(((a.get("구조") or {}).get("할인")), dict) and a["구조"]["할인"].get("베타출처") == "유사기업표":
            a["구조"]["할인"]["베타출처"] = "직접"
        for 구간 in ("예측기간", "영구기간"):
            if isinstance((a.get("WACC") or {}).get(구간), dict):
                a["WACC"][구간]["베타u"] = b
        R = _i.import_module("엔진.계산").계산(a, "기준")
        return R["요약"]["예측기간WACC"], R["요약"]["영구기간WACC"]
    except Exception:                                        # noqa: BLE001
        return None, None


def _대안열쇠(블):
    return [(_n(x.get("예측기간WACC")), _n(x.get("영구기간WACC"))) for x in ((블 or {}).get("대안") or []) if isinstance(x, dict)]


def 읽기(가정, 부록=None):
    """→ (자본비용 블록 또는 None, 출처 「가정」 · 「레터부록」 · None, [알림]). 가정이 먼저, 없으면 레터부록(옛 회차)."""
    알림 = []
    가블 = (가정 or {}).get(블록키) if isinstance(가정, dict) else None
    부블 = (부록 or {}).get(블록키) if isinstance(부록, dict) else None
    if isinstance(가블, dict):
        if isinstance(부블, dict) and _대안열쇠(부블) != _대안열쇠(가블):
            알림.append("자본비용 대안 사양이 가정과 레터부록에서 다르다 — 가정을 썼다(레터부록의 「자본비용」 은 지우거나 맞춘다)")
        return 가블, "가정", 알림
    if isinstance(부블, dict):
        알림.append("자본비용 대안 사양을 레터부록에서 읽었다 — 가정 파일로 옮긴다(`자본비용옮기기.py`)")
        return 부블, "레터부록", 알림
    return None, None, 알림


def _부록경로(가정경로, 지정=None):
    return 지정 or os.path.join(os.path.dirname(os.path.abspath(가정경로)), "레터부록.json")


def 부록읽기(가정경로, 지정=None):
    p = _부록경로(가정경로, 지정) if 가정경로 else 지정
    if not p or not os.path.exists(p):
        return {}
    try:
        d = json.load(io.open(p, encoding="utf-8"))
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def _들여쓰기(글):
    """원래 파일의 들여쓰기 칸 수(둘째 줄의 앞 공백) — 다시 쓸 때 꼴을 지킨다."""
    for 줄 in 글.replace("\r\n", "\n").split("\n")[1:]:
        if 줄.strip():
            return len(줄) - len(줄.lstrip(" ")) or 1
    return 1


def _엔진칸():
    """엔진이 `WACC.<구간>` 에서 읽는 칸 이름(엔진/wacc.py 의 WACC항목 + WACC새항목) — 가정 사본에 없어도 덮어쓰기로 더할 수 있는 칸이다
    (규모프리미엄 · DE 처럼 비워 두는 선택 칸). 이름을 여기 다시 적지 않고 엔진에서 읽는다 — 오타(「없는칸」)는 종전대로 걸린다."""
    import importlib                                                  # noqa: PLC0415
    w = importlib.import_module("엔진.wacc")
    return tuple(w.WACC항목) + tuple(w.WACC새항목)


def _표베타를직접으로(g, 구, 칸, v):
    """덮어쓰기 `예측기간.베타u` + `구조.할인.베타출처 = 유사기업표` → 사본 g 의 베타출처를 「직접」 으로 바꾸고 True(βu 는 부르는 쪽이 넣는다).

    엔진 규칙(`엔진/wacc.py` 머리 · 구조확인): 유사기업표면 예측기간 무차입 베타는 표의 대표값이고, 예측기간 `베타u` 를 표와 다른 값으로 적으면
    구조확인이 막는다(「직접 주려면 직접으로 선언」). 대안은 그 선언을 사본에서만 따른다 — 영구기간 칸은 두 갈래 모두 `베타u` 라 손대지 않는다.
    `영구WACC = 예측과같음` 인데 영구기간 βu 를 함께 덮지 않으면 엔진 구조확인이 걸림으로 알린다(두 구간이 같아야 한다)."""
    할 = (g.get("구조") or {}).get("할인") if isinstance(g.get("구조"), dict) else None
    w = g.get("WACC")
    if not (구 == "예측기간" and 칸 == "베타u" and _n(v) is not None and isinstance(할, dict) and 할.get("베타출처") == "유사기업표"
            and isinstance(w, dict) and isinstance(w.get(구), dict)):
        return False
    할["베타출처"] = "직접"
    return True


def 대안셈(가정, 대안목록):
    """대안마다 가정 사본의 WACC 블록 칸을 덮어쓰고 엔진으로 예측기간 · 영구기간 WACC 를 셈한다 → ([대안 줄], [걸림])."""
    import copy                                                       # noqa: PLC0415
    import importlib                                                  # noqa: PLC0415
    E = importlib.import_module("dcf엔진")
    낸, 걸 = [], []
    for i, x in enumerate(대안목록 or []):
        덮 = (x or {}).get("덮어쓰기") or {}
        if not isinstance(덮, dict) or not 덮:
            걸.append("대안[%d] 「%s」 — 덮어쓰기가 없다" % (i, (x or {}).get("사양")))
            continue
        g = copy.deepcopy(가정)
        w = g.get("WACC")
        잘못, 바꿈 = [], {}
        for 열쇠, v in 덮.items():
            구, _, 칸 = ("%s" % 열쇠).partition(".")
            if _표베타를직접으로(g, 구, 칸, v):
                바꿈["구조.할인.베타출처"] = "직접"
            elif not (isinstance(w, dict) and isinstance(w.get(구), dict) and (칸 in w[구] or 칸 in _엔진칸())) or _n(v) is None:
                잘못.append(열쇠)
                continue
            w[구][칸] = float(v)
        if 잘못:
            걸.append("대안[%d] 「%s」 — WACC 블록에 없는 자리이거나 숫자가 아니다: %s" % (i, x.get("사양"), " · ".join(잘못)))
            continue
        try:
            R = E.계산(g, "기준")["요약"]
        except Exception as e:                                       # noqa: BLE001
            속 = [l.strip(" -") for l in ("%s" % e).splitlines() if l.strip()]
            걸.append("대안[%d] 「%s」 — 엔진 계산이 막혔다(%s: %s)" % (i, x.get("사양"), type(e).__name__, (속[-1] if 속 else "")[:160]))
            continue
        줄 = {"사양": x.get("사양") or "대안 %d" % (i + 1), "예측기간WACC": R.get("예측기간WACC"), "영구기간WACC": R.get("영구기간WACC"),
              "근거": x.get("근거") or "", "덮어쓰기": 덮}
        if 바꿈:
            줄["사본바꿈"] = 바꿈
        낸.append(줄)
    return 낸, 걸


def 짓기(가정경로, 대안경로):
    """→ (rc, 글). 대안을 엔진으로 셈해 가정 「자본비용.대안」 에 더한다(같은 사양 이름은 값이 같으면 둔다 · 다르면 멈춘다)."""
    원 = open(가정경로, "rb").read()
    crlf = b"\r\n" in 원
    글 = 원.decode("utf-8-sig")
    가정 = json.loads(글)
    try:
        목록 = json.load(io.open(대안경로, encoding="utf-8-sig"))
    except (OSError, ValueError) as e:
        return 2, "대안 파일을 못 읽었다(%s)" % e
    새대안, 걸 = 대안셈(가정, 목록 if isinstance(목록, list) else [])
    if 걸:
        return 1, "대안 셈 걸림 — " + " · ".join(걸)
    블 = 가정.get(블록키) if isinstance(가정.get(블록키), dict) else {"채택": {"사양": "채택 사양(가정 WACC 블록)", "근거": ""}, "대안": []}
    있 = {x.get("사양"): x for x in 블.get("대안") or [] if isinstance(x, dict)}
    더, 같 = 0, 0
    for x in 새대안:
        y = 있.get(x["사양"])
        if y is None:
            블.setdefault("대안", []).append(x)
            더 += 1
        elif abs((_n(y.get("예측기간WACC")) or 0) - x["예측기간WACC"]) < 1e-12 and abs((_n(y.get("영구기간WACC")) or 0) - x["영구기간WACC"]) < 1e-12:
            같 += 1
        else:
            return 1, "같은 사양 이름 「%s」 이 다른 값으로 이미 있다 — 덮지 않는다" % x["사양"]
    가정[블록키] = 블
    새 = json.dumps(가정, ensure_ascii=False, indent=_들여쓰기(글)) + ("\n" if 글.endswith(("\n", "\r\n")) else "")
    if crlf:
        새 = 새.replace("\r\n", "\n").replace("\n", "\r\n")
    open(가정경로, "wb").write(새.encode("utf-8"))
    return 0, "짓기 — 더함 %d · 같아 둠 %d(대안 %d개 · 엔진으로 셈한 WACC)" % (더, 같, len(블.get("대안") or []))


def 옮기기(가정경로, 부록경로=None):
    """→ (rc, 글). 레터부록의 「자본비용」 을 가정 파일 끝에 더한다 — 이미 같으면 둔다 · 다르면 멈춘다. 줄끝 · 들여쓰기를 지킨다."""
    if not os.path.exists(가정경로):
        return 2, "가정 파일이 없다: %s" % 가정경로
    원 = open(가정경로, "rb").read()
    crlf = b"\r\n" in 원
    글 = 원.decode("utf-8-sig")
    try:
        가정 = json.loads(글)
    except ValueError as e:
        return 2, "가정 파일을 못 읽었다(%s)" % e
    부록 = 부록읽기(가정경로, 부록경로)
    부블 = 부록.get(블록키) if isinstance(부록, dict) else None
    가블 = 가정.get(블록키)
    if not isinstance(부블, dict):
        if isinstance(가블, dict):
            걸 = 꼴검사(가블)
            return (1, "가정의 자본비용 블록 꼴 — " + " · ".join(걸)) if 걸 else (0, "가정에 자본비용 블록이 이미 있다(레터부록에는 없음) — 할 일 없음")
        return 2, "레터부록(%s)에 「자본비용」 이 없다 — 옮길 것이 없다" % _부록경로(가정경로, 부록경로)
    걸 = 꼴검사(부블)
    if 걸:
        return 1, "레터부록의 자본비용 블록 꼴 — " + " · ".join(걸)
    if isinstance(가블, dict):
        if json.dumps(가블, sort_keys=True, ensure_ascii=False) == json.dumps(부블, sort_keys=True, ensure_ascii=False):
            return 0, "가정과 레터부록의 자본비용이 같다 — 할 일 없음"
        return 1, ("가정에 이미 다른 자본비용 블록이 있다 — 덮지 않는다(대안 가정 %s · 레터부록 %s). 어느 쪽이 맞는지 보고 한쪽을 고친다"
                   % (_대안열쇠(가블), _대안열쇠(부블)))
    가정[블록키] = 부블
    새 = json.dumps(가정, ensure_ascii=False, indent=_들여쓰기(글)) + ("\n" if 글.endswith(("\n", "\r\n")) else "")
    if crlf:
        새 = 새.replace("\r\n", "\n").replace("\n", "\r\n")
    open(가정경로, "wb").write(새.encode("utf-8"))
    return 0, "옮김 — 대안 사양 %d개 · 채택 「%s」 → %s 의 「자본비용」(값은 바뀌지 않는다 · 레터부록의 같은 블록은 두어도 된다 — 가정이 먼저 읽힌다)" % (
        len(부블.get("대안") or []), ((부블.get("채택") or {}).get("사양") or "—"), os.path.basename(가정경로))


def main(argv=None):
    ap = argparse.ArgumentParser(allow_abbrev=False, description="할인율 대안 사양을 가정 파일로 옮긴다(W12)")
    ap.add_argument("가정")
    ap.add_argument("--레터부록", default=None)
    ap.add_argument("--검사", action="store_true", help="가정의 자본비용 블록 꼴만 본다")
    ap.add_argument("--짓기", default=None, help="대안.json — 덮어쓴 WACC 입력으로 엔진이 셈한 대안을 적는다(레터부록이 없는 회사)")
    a = ap.parse_args(argv)
    if a.짓기:
        if not os.path.exists(a.가정):
            print("입력 오류 — 가정 파일이 없다: %s" % a.가정)
            return 2
        rc, 글 = 짓기(a.가정, a.짓기)
        print(글)
        return rc
    if a.검사:
        try:
            가정 = json.load(io.open(a.가정, encoding="utf-8-sig"))
        except (OSError, ValueError) as e:
            print("입력 오류 — %s" % e)
            return 2
        블 = 가정.get(블록키)
        if 블 is None:
            print("가정에 자본비용 블록이 없다 — 결합 분포에 할인율이 들어가지 않는다(대안 사양을 세우면 이 블록에)")
            return 0
        걸 = 꼴검사(블)
        for x in 걸:
            print("  걸림 — %s" % x)
        print("자본비용 블록 — %s" % ("걸림 %d" % len(걸) if 걸 else "통과(대안 %d개)" % len(블.get("대안") or [])))
        return 1 if 걸 else 0
    rc, 글 = 옮기기(a.가정, a.레터부록)
    print(글)
    return rc


if __name__ == "__main__":
    sys.exit(main())

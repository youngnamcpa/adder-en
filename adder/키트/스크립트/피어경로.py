# -*- coding: utf-8 -*-
"""피어경로 — 유사기업 도구들이 같이 쓰는 경로 · 파일 이름 규칙 (2026-10-24 W15 · 유니버스 조사 시범).

  명단경로(인자, 폴더, 뿌리)  명단 인자를 한 규칙으로 푼다 — 절대 경로 · 작업 폴더 기준 상대 경로(`_raw/peers/x.json`) ·
                             폴더 안 이름(`x.json`) 셋 다 받는다. 종전에는 도구마다 달라 `peer_조립_us` 는 `_raw/peers/` 를 한 번 더
                             붙였고(`_raw/peers/_raw/peers/x.json`) `peer_기준일종가` 는 이름만 받았다(현대차 · 인텔 · 마이크론 시범).
  종가파일(폴더, 기준일)      기준일 종가 캐시의 정본 이름 `종가_YYYYMMDD.json` — 기준일을 어느 꼴(2026-06-30 · 20260630)로 줘도 같다.
  종가읽기(폴더, 기준일)      정본과 옛 꼴(`종가_YYYY-MM-DD.json`)을 함께 읽어 합친다(정본이 이긴다) — 두 파일이 따로 쌓여 한쪽만
                             갱신되던 결함(마이크론 시범).
  피어폴더(뿌리)             `DCF_PEER_CACHE`(사슬 `--캐시` 가 하위 도구에 넘기는 환경변수)가 있으면 그것, 없으면 `<뿌리>/_raw/peers`.
  βU재료고르기(회차, 가정)   1.1.4 — 레터 · 갭해석 · 모델밖가치 · 이례표시가 같이 쓰는 βU 재료(`_raw/peers/βU_*.json`) 고르기. 가정 `구조.할인.유사기업파일` 이
                             먼저, 없으면 **창 끝 날짜**(산출의 `기준일` · 병합은 `머리.기준일`)가 평가기준일 이하 가운데 가장 늦은 판 → 가정 βU 근거 글이
                             이름을 댄 판 → 축소 블록이 있는 판 → 가장 늦게 쓴 판. 종전 규칙(이름이 가장 짧은 판)은 재실행 · 날짜 둘 회차에서 재무 자료
                             기준일 창의 옛 판을 집었다(회차 넷 · 레터 Peer 표가 옛 표본). 고른 파일 · 창 끝 · 까닭을 돌려준다 — 부르는 쪽이 산출에 찍는다.
  βU짝csv(회차, βU경로)      그 βU 재료와 짝인 `유사기업_재료_<표본>.csv`(없으면 None — 다른 표본의 csv 를 섞지 않는다).
"""
from __future__ import annotations

import io
import json
import os


def 피어폴더(뿌리):
    return os.environ.get("DCF_PEER_CACHE") or os.path.join(뿌리, "_raw", "peers")


def 명단경로(인자, 폴더, 뿌리=None):
    """명단 인자 → 실제 파일 경로. 있는 첫 자리를 낸다(폴더 안 → 작업 폴더 기준 → 뿌리 기준 → 폴더 안 같은 이름).
    어디에도 없으면 폴더 안 같은 이름의 자리(새로 쓸 자리)."""
    if not 인자:
        return None
    if os.path.isabs(인자):
        return 인자
    후보 = [os.path.join(폴더, 인자), os.path.abspath(인자)]
    if 뿌리:
        후보.append(os.path.join(뿌리, 인자))
    후보.append(os.path.join(폴더, os.path.basename(인자)))
    for p in 후보:
        if os.path.exists(p):
            return os.path.abspath(p)
    return os.path.abspath(os.path.join(폴더, os.path.basename(인자)))


def 날8(기준일):
    return ("%s" % 기준일).replace("-", "")[:8]


def 종가파일(폴더, 기준일):
    return os.path.join(폴더, "종가_%s.json" % 날8(기준일))


def 종가읽기(폴더, 기준일):
    d8 = 날8(기준일)
    옛 = "%s-%s-%s" % (d8[:4], d8[4:6], d8[6:8])
    낸 = {}
    for 이름 in ("종가_%s.json" % 옛, "종가_%s.json" % d8):
        p = os.path.join(폴더, 이름)
        if os.path.exists(p):
            try:
                낸.update(json.load(io.open(p, encoding="utf-8")) or {})
            except (OSError, ValueError):
                pass
    return 낸


def 날10(v):
    """「20260630」 · 「2026-06-30」 · 「2026-06-30T…」 → 「2026-06-30」(못 읽으면 None)."""
    t = ("%s" % (v or "")).strip().replace("-", "")[:8]
    return "%s-%s-%s" % (t[:4], t[4:6], t[6:8]) if len(t) == 8 and t.isdigit() else None


def βU창끝(d):
    """βU 산출 dict → 회귀 창 끝(평가기준일 쪽 · 「YYYY-MM-DD」). 단일 시장 산출은 `기준일`, 병합은 `머리.기준일`."""
    if not isinstance(d, dict):
        return None
    return 날10(d.get("기준일") or (d.get("머리") or {}).get("기준일") or ((d.get("머리") or {}).get("창") or {}).get("끝"))


def _βU근거글(가정):
    근 = (가정 or {}).get("WACC근거") or {}
    낸 = []
    for k in ("10", "11", "12"):
        v = 근.get(k)
        낸 += [("%s" % x) for x in (v if isinstance(v, (list, tuple)) else [v]) if x]
    return " ".join(낸)


def _βU재료값들(d):
    """βU 재료 산출이 내는 대표 값들(기본값 · 축소 사후 · 핵심 본값의 개별 중앙값) — 채택 βU 와 견줄 값."""
    bv = (d or {}).get("본값") or {}
    낸 = []
    for v in ((bv.get("기본값") or {}).get("값"), ((bv.get("축소") or {}).get("사후") or {}).get("값") if isinstance((bv.get("축소") or {}).get("사후"), dict)
              else (bv.get("축소") or {}).get("사후"),
              ((bv.get("핵심") or {}).get("본값") or {}).get("(b)개별중앙값_기본"), ((bv.get("핵심") or {}).get("기본값") or {}).get("값")):
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            낸.append(float(v))
    return 낸


def βU재료고르기(회차, 가정=None):
    """→ {"경로"(절대), "상대"(회차 기준), "창끝", "까닭", "후보수"} 또는 None."""
    import glob as _glob                                    # noqa: PLC0415
    가정 = 가정 if isinstance(가정, dict) else {}
    선 = (((가정.get("구조") or {}).get("할인") or {}).get("유사기업파일"))
    if isinstance(선, str) and 선.strip() and os.path.exists(os.path.join(회차, 선.strip())):
        p = os.path.join(회차, 선.strip())
        try:
            끝 = βU창끝(json.load(io.open(p, encoding="utf-8")))
        except (OSError, ValueError):
            끝 = None
        return {"경로": os.path.abspath(p), "상대": 선.strip().replace(os.sep, "/"), "창끝": 끝, "까닭": "가정 구조.할인.유사기업파일", "후보수": 1}
    T = 날10((가정.get("메타") or {}).get("평가기준일"))
    근글 = _βU근거글(가정)
    채 = (((가정.get("WACC") or {}).get("예측기간") or {}).get("베타u"))          # 1.1.9 — 가정이 채택한 βU(예측기간)
    채 = float(채) if isinstance(채, (int, float)) and not isinstance(채, bool) else None
    후 = []
    for p in _glob.glob(os.path.join(회차, "_raw", "peers", "βU_*.json")):
        try:
            d = json.load(io.open(p, encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if not isinstance(d, dict) or not isinstance(d.get("표"), list):
            continue
        끝 = βU창끝(d)
        이름 = os.path.basename(p)
        축 = isinstance((d.get("본값") or {}).get("축소"), dict) and bool(d["본값"]["축소"].get("적용"))
        차 = min((abs(v - 채) for v in _βU재료값들(d)), default=None) if 채 is not None else None
        맞 = bool(차 is not None and 차 <= 0.005)
        후.append({"p": p, "이름": 이름, "끝": 끝, "축": 축, "근": bool(근글 and 이름 in 근글), "때": os.path.getmtime(p), "맞": 맞,
                  "차": round(차, 4) if 맞 else 9.0})
    if not 후:
        return None
    안 = [x for x in 후 if x["끝"] and (T is None or x["끝"] <= T)] or 후
    if any(x["맞"] for x in 안):                            # 1.1.9 — 채택 βU 와 같은 값을 내는 재료가 있으면 그 가운데서 고른다(참고판이 정본을 이기던 자리 —
        안 = [x for x in 안 if x["맞"]]                     #   유니버스 다섯 회사 · 레터 Peer 표의 동종 중앙값이 채택값과 어긋났다)
    늦 = max((x["끝"] or "") for x in 안)
    같 = [x for x in 안 if (x["끝"] or "") == 늦]
    # 1.1.10 — 맞는 판이 여럿이면 채택 βU 에 가장 가까운 판(업종 줄 감도판 1.038 이 정본 1.0354 를 이기던 자리 — 다섯째 회사)
    같.sort(key=lambda x: (x["차"], not x["근"], not x["축"], -x["때"], len(x["이름"]), x["이름"]))
    고 = 같[0]
    까 = ["창 끝 %s" % (고["끝"] or "모름") + (" ≤ 평가기준일 %s" % T if T and 고["끝"] else "")] + (["채택 βU %.4f 와 같은 값을 내는 판" % 채] if 고.get("맞") else [])
    if len(같) > 1:
        까.append("같은 창 끝 %d판 가운데 %s" % (len(같), "가정 βU 근거가 이름을 댄 판" if 고["근"] else ("축소 블록이 있는 판" if 고["축"] else "가장 늦게 쓴 판")))
    return {"경로": os.path.abspath(고["p"]), "상대": os.path.relpath(고["p"], 회차).replace(os.sep, "/"), "창끝": 고["끝"],
            "까닭": " · ".join(까), "후보수": len(후)}


def βU짝csv(회차, βU경로):
    """βU 재료 이름과 짝인 `유사기업_재료_<표본>.csv`(βU_핵심예비_T ↔ 유사기업_재료_핵심예비_T) — 없으면 None."""
    꼬 = os.path.splitext(os.path.basename(βU경로 or ""))[0].replace("βU_", "", 1)
    for p in (os.path.join(회차, "_raw", "peers", "유사기업_재료_%s.csv" % 꼬), os.path.join(회차, "유사기업_재료_%s.csv" % 꼬)):
        if os.path.exists(p):
            return p
    return None

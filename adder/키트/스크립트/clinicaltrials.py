# -*- coding: utf-8 -*-
"""ClinicalTrials.gov — 스폰서별 임상 파이프라인(단계 × 상태)을 키 없이 받아 바이오 · 제약의 「능력(파이프라인)」 노드 원천으로 낸다 (제안 D-미국 · 2026-10-22 신설).

무엇을 하나
  `clinicaltrials.gov/api/v2/studies?query.lead=<스폰서>` 는 그 스폰서가 주관하는 임상 건을 단계(PHASE1~4 · EARLY_PHASE1 · NA) · 상태(RECRUITING ·
  COMPLETED · TERMINATED …) · 시작일과 함께 준다(키 없음 · 2026-10-22 실측 — 스폰서 하나 1,430건 · 100건씩 페이지). 동인 지도의 「능력」 노드가 바이오 · 제약에서
  파이프라인(임상 단계별 과제 수)인데(동인 지도 규칙), 그 원천을 공시 밖에서 기계로 센다. 평가기준일까지 시작한 건만 센다(기준일 뒤 정보 금지).
  확인상태 「참고(공개 등록 — 미국 등록 기준 · 미국 밖 임상은 일부만)」. 회사 이름은 인자다 — 도구에 박지 않는다.

사용
  python 스크립트/clinicaltrials.py --스폰서 "<회사 영문명>" --기준일 2026-06-30 [--낼 _raw/파이프라인.json]
내는 것 — {형식 · 만든날 · 입력 · 출처 · 확인상태 · 총건수 · 단계별{단계: {진행 · 완료 · 중단 · 기타}} · 연도별시작{연도: 건수} · 진행중[{nct · 단계 · 상태 · 시작}] · 신호[]}
종료 코드 — 0 통과 · 2 입력오류(응답 깨짐).
"""
from __future__ import annotations

import argparse
import datetime
import io
import json
import os
import sys
import time

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:                                    # noqa: BLE001
    pass
여기 = os.path.dirname(os.path.abspath(__file__))
if 여기 not in sys.path:
    sys.path.insert(0, 여기)
from 종료코드 import 통과, 입력오류  # noqa: E402

주소 = "https://clinicaltrials.gov/api/v2/studies"
진행상태 = {"RECRUITING", "ACTIVE_NOT_RECRUITING", "NOT_YET_RECRUITING", "ENROLLING_BY_INVITATION"}
중단상태 = {"TERMINATED", "WITHDRAWN", "SUSPENDED"}


def 받기(스폰서, 기준일):
    import requests                                      # noqa: PLC0415
    낸, 토큰 = [], None
    for _ in range(100):
        p = {"query.lead": 스폰서, "pageSize": 1000, "countTotal": "true",
             "fields": "NCTId,Phase,OverallStatus,LeadSponsorName,StartDate,PrimaryCompletionDate"}
        if 토큰:
            p["pageToken"] = 토큰
        r = requests.get(주소, params=p, timeout=120)
        if r.status_code != 200:
            return None, None
        j = r.json()
        for s in j.get("studies", []):
            ps = s.get("protocolSection") or {}
            시작 = ((ps.get("statusModule") or {}).get("startDateStruct") or {}).get("date") or ""
            if 시작 and 시작[:7] > 기준일[:7]:
                continue                                 # 기준일 뒤 시작 — 넣지 않는다
            낸.append({"nct": (ps.get("identificationModule") or {}).get("nctId"),
                      "단계": " · ".join((ps.get("designModule") or {}).get("phases") or ["NA"]),
                      "상태": (ps.get("statusModule") or {}).get("overallStatus"), "시작": 시작,
                      "스폰서": ((ps.get("sponsorCollaboratorsModule") or {}).get("leadSponsor") or {}).get("name")})
        토큰 = j.get("nextPageToken")
        총 = j.get("totalCount")
        if not 토큰:
            return 낸, 총
        time.sleep(0.3)
    return 낸, None


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False, description="ClinicalTrials.gov — 스폰서의 임상 파이프라인(단계 × 상태)")
    ap.add_argument("--스폰서", required=True, help="주관 스폰서 이름(영문 — 등록된 표기)")
    ap.add_argument("--기준일", default=datetime.date.today().isoformat(), help="평가기준일 — 그 뒤에 시작한 건은 세지 않는다")
    ap.add_argument("--낼", help="산출 경로(기본: ./_raw/파이프라인.json)")
    a = ap.parse_args()
    건들, 총 = 받기(a.스폰서, a.기준일)
    if 건들 is None:
        print("입력오류 — ClinicalTrials.gov 응답을 받지 못했다")
        return 입력오류
    단계별 = {}
    연도별 = {}
    for x in 건들:
        d = 단계별.setdefault(x["단계"], {"진행": 0, "완료": 0, "중단": 0, "기타": 0})
        if x["상태"] in 진행상태:
            d["진행"] += 1
        elif x["상태"] == "COMPLETED":
            d["완료"] += 1
        elif x["상태"] in 중단상태:
            d["중단"] += 1
        else:
            d["기타"] += 1
        if x["시작"]:
            연도별[x["시작"][:4]] = 연도별.get(x["시작"][:4], 0) + 1
    진행 = [x for x in 건들 if x["상태"] in 진행상태]
    후기 = sum(1 for x in 진행 if "PHASE3" in x["단계"])
    낸 = {"형식": "파이프라인 1", "만든날": datetime.date.today().isoformat(), "입력": {"스폰서": a.스폰서, "기준일": a.기준일}, "출처": 주소,
         "확인상태": "참고(공개 등록 — ClinicalTrials.gov · 미국 등록 기준 · 스폰서 표기가 갈리면 빠진다)", "총건수_등록": 총, "기준일까지_건수": len(건들),
         "단계별": 단계별, "연도별시작": dict(sorted(연도별.items())), "진행중": 진행[:200],
         "신호": [{"출처": "clinicaltrials", "종류": "파이프라인 — 진행 중 임상", "대상": a.스폰서, "값": len(진행), "문턱": None,
                 "글": "기준일 %s 까지 시작한 임상 %d건 가운데 진행 중 %d건(3상 %d) — 동인 지도 「능력(파이프라인)」 노드의 원천. 회사 공시의 파이프라인 표와 대 본다" % (a.기준일, len(건들), len(진행), 후기), "등급": "참고"}]}
    if 총 and 총 > len(건들) + 50:
        낸["신호"].append({"출처": "clinicaltrials", "종류": "스폰서 표기 확인", "대상": a.스폰서, "값": 총, "문턱": None,
                        "글": "등록 총 %d건 가운데 기준일까지 %d건만 셌다 — 스폰서 표기(옛 이름 · 자회사)가 갈리면 빠진 건이 있을 수 있다" % (총, len(건들)), "등급": "참고"})
    p = a.낼 or os.path.join(os.getcwd(), "_raw", "파이프라인.json")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    io.open(p, "w", encoding="utf-8").write(json.dumps(낸, ensure_ascii=False, indent=1))
    print("파이프라인 — %s · 기준일까지 %d건 · 진행 %d(3상 %d) · 단계 %s → %s" % (a.스폰서, len(건들), len(진행), 후기, {k: v["진행"] for k, v in 단계별.items()}, p))
    return 통과


if __name__ == "__main__":
    sys.exit(main())

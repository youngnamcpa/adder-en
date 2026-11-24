# -*- coding: utf-8 -*-
"""KAM 추출 — 감사보고서의 「핵심감사사항」을 뽑아 동인 지도의 노드에 「회계 추정 위험」 표시로 붙인다 (제안 F · 2026-10-22 신설).

무엇을 하나
  감사인이 핵심감사사항(Key Audit Matters)으로 적은 항목(수익인식 · 진행률 · 재고 평가 · 손상 · 충당부채 · 개발비 자본화 …)은 **그 회사의 역사 숫자 자체가 경영진의
  추정에 얹혀 있다**는 공개 신호다. 키트의 출처 딱지는 「값이 어디서 왔나」만 적고 「그 공시 값이 추정에 얼마나 기대나」는 적지 않았다(연구/변수분류_한발자국_연구.md 2-6).
  OpenDART `document.xml`(접수번호 → 원문 ZIP)은 사업보고서 본문과 **첨부(감사보고서 · 연결감사보고서)**를 함께 준다(2026-10-22 실측 — 첨부 XML 에 「핵심감사사항」 절,
  본문에는 당기 · 전기 KAM 요약 표). 이 도구는 첨부에서 「(n) 제목 … 가. 핵심감사사항으로 결정된 이유 … 나. 해당사항이 감사에서 다루어진 방법」 꼴을 뽑아
  항목마다 제목 · 이유(원문 인용) · 절차 · 닿는 노드(낱말 사전)를 `_raw/핵심감사사항.json` 에 낸다. **값 · 근거 강도를 바꾸지 않는다** — 신호(참고)만 낸다.
  근거 강도에 닿게 할지는 사람이 정한다(「실측」 상한을 「유추」로 — 연구 보고서 제안 F).

사용
  python 스크립트/kam추출.py 가정.json [--접수번호 20260316001594] [--낼 _raw/핵심감사사항.json]
  접수번호를 안 주면 가정 곁 `_raw/dart_기업개황.json` 의 corp_code 와 재무기준일(메타.재무기준일 · 없으면 메타.평가기준일 — `기준일.py`)로
  그 해(또는 직전 해) 사업보고서를 list API 로 찾는다.
읽는 것 — OPENDART_API_KEY(환경변수 — 화면 · 파일에 쓰지 않는다) · 원문 ZIP 은 가정 곁 `_raw/원문/{접수번호}.zip` 에 캐시(이미 있으면 받지 않는다)
내는 것 — {형식 · 만든날 · 입력 · 출처 · 확인상태 「확인완료(감사보고서 원문)」 · 보고서[{첨부 · 연결여부 · 감사인 · 의견 · 항목[{번호 · 제목 · 이유(인용) · 절차(인용) · 닿는노드 · 낱말}]}] ·
          요약표(본문의 당기 · 전기 KAM 표 글) · 신호[]}. 신호는 참고 — 「핵심감사사항 — <제목> → <노드>」 항목마다 한 줄.
종료 코드 — 0 통과 · 2 입력오류(키 없음 · 접수번호 못 찾음 · 원문 깨짐). 핵심감사사항 절이 없으면(소규모 · 비적용) 「해당 없음」 참고 한 줄 · rc 0.
회사 · 업종 이름은 이 도구에 없다(범용). 낱말 사전은 회계 항목 낱말이다.
"""
from __future__ import annotations

import argparse
import datetime
import html
import io
import json
import os
import re
import sys
import zipfile

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:                                    # noqa: BLE001
    pass
여기 = os.path.dirname(os.path.abspath(__file__))
if 여기 not in sys.path:
    sys.path.insert(0, 여기)
from 종료코드 import 통과, 입력오류  # noqa: E402

# 낱말 → 동인 지도 노드(업종 중립 — 회계 항목 낱말)
노드사전 = [
    (("수익인식", "수익 인식", "매출의 기간귀속", "매출 인식", "진행률", "진행기준", "투입법", "수행의무", "변동대가", "반품", "리베이트"), "매출 구분 Q · P(수익 인식)"),
    (("재고자산", "재고 평가", "순실현가능가치", "평가충당금"), "운전자본(재고) · 원가 줄"),
    (("매출채권", "대손", "기대신용손실", "손실충당금"), "운전자본(매출채권)"),
    (("영업권", "손상", "회수가능액", "사용가치", "현금창출단위"), "영구(초과수익 · 영구가치) · 성장 CAPEX"),
    (("유형자산", "내용연수", "감가상각", "잔존가치"), "감가상각 · 유지 CAPEX"),
    (("개발비", "자본화", "무형자산"), "연구개발"),
    (("충당부채", "소송", "보증", "복구", "우발"), "한시적 현금흐름 · 시나리오 밖 위험"),
    (("이연법인세", "법인세", "세무"), "법인세"),
    (("종속기업", "관계기업", "투자주식", "지분법", "연결범위", "사업결합", "공정가치"), "가치 브리지(비영업자산 · 비지배지분)"),
    (("퇴직급여", "확정급여", "계리"), "인건비"),
    (("파생", "금융상품", "전환사채", "신주인수권"), "주당가치(희석) · 순부채"),
    (("계속기업", "존속"), "계속기업(관문 ⓪)"),
]


def 노드찾기(글):
    낱, 노 = [], []
    for 낱말들, 노드 in 노드사전:
        걸 = [w for w in 낱말들 if w in 글]
        if 걸:
            낱 += 걸
            노.append(노드)
    return 노 or ["모름 — 사람이 노드를 적는다"], 낱


def 벗기기(x):
    x = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", x)
    x = re.sub(r"<[^>]+>", " ", x)
    x = html.unescape(x)
    return re.sub(r"\s+", " ", x).strip()


def 원문받기(접수번호, 곁, key):
    import requests                                      # noqa: PLC0415
    d = os.path.join(곁, "_raw", "원문")
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, "%s.zip" % 접수번호)
    if os.path.exists(p) and os.path.getsize(p) > 100:
        return p, "캐시"
    r = requests.get("https://opendart.fss.or.kr/api/document.xml", params={"crtfc_key": key, "rcept_no": 접수번호}, timeout=180)
    if r.status_code != 200 or r.content[:2] != b"PK":
        return None, "document.xml 응답 %s — %s" % (r.status_code, r.text[:120] if r.content[:2] != b"PK" else "")
    io.open(p, "wb").write(r.content)
    return p, "받음"


def 접수번호찾기(corp_code, 기준일, key):
    """평가기준일이 속한 해(없으면 직전 해)의 사업보고서 접수번호 — list API(A001 정기공시)."""
    import requests                                      # noqa: PLC0415
    y = int(기준일[:4])
    for 해 in (y, y - 1):
        r = requests.get("https://opendart.fss.or.kr/api/list.json", params={"crtfc_key": key, "corp_code": corp_code, "bgn_de": "%d0101" % (해 + 1), "end_de": "%d1231" % (해 + 1),
                                                                            "pblntf_detail_ty": "A001", "page_count": 50}, timeout=60)
        j = r.json() if r.status_code == 200 else {}
        후 = [x for x in j.get("list", []) if "사업보고서" in x.get("report_nm", "")]
        if 후:
            후.sort(key=lambda x: x["rcept_dt"])
            return 후[-1]["rcept_no"], 후[-1]["report_nm"]
    return None, None


def 항목뽑기(글):
    """「(1) 제목 가. 핵심감사사항으로 결정된 이유 … 나. 해당사항이 감사에서 다루어진 방법 …」 → [{번호 · 제목 · 이유 · 절차}]."""
    i = 글.find("핵심감사사항으로 결정하였습니다")
    if i < 0:
        i = 글.find("핵심감사사항")
    끝 = None
    for 표 in ("기타사항", "재무제표에 대한 경영진과 지배기구의 책임", "연결재무제표에 대한 경영진과 지배기구의 책임", "강조사항"):
        j = 글.find(표, i + 20)
        if j > 0 and (끝 is None or j < 끝):
            끝 = j
    본 = 글[i:끝] if 끝 else 글[i:i + 20000]
    조각 = re.split(r"\((\d{1,2})\)\s*", 본)
    낸 = []
    for k in range(1, len(조각) - 1, 2):
        번호, 몸 = 조각[k], 조각[k + 1]
        m = re.match(r"(.+?)\s*가\.\s*핵심감사사항으로\s*결정된\s*이유\s*(.*?)(?:나\.\s*해당\s*사항이\s*감사에서\s*다루어진\s*방법\s*(.*))?$", 몸, re.S)
        if not m:
            제목, 이유, 절차 = 몸[:80], 몸[80:1200], ""
        else:
            제목, 이유, 절차 = m.group(1).strip(), (m.group(2) or "").strip(), (m.group(3) or "").strip()
        노, 낱 = 노드찾기(제목 + " " + 이유[:400])
        낸.append({"번호": int(번호), "제목": 제목[:200], "이유": 이유[:1500], "절차": 절차[:1500], "닿는노드": 노, "낱말": 낱})
    return 낸


def 분석(가정, 가정경로, 접수번호=None):
    key = os.environ.get("OPENDART_API_KEY")
    if not key:
        return None, "환경변수 OPENDART_API_KEY 가 없다"
    곁 = os.path.dirname(os.path.abspath(가정경로))
    보고서명 = None
    if not 접수번호:
        corp = None
        p = os.path.join(곁, "_raw", "dart_기업개황.json")
        if os.path.exists(p):
            try:
                corp = (json.load(io.open(p, encoding="utf-8")).get("corp_code") or "").strip()
            except (OSError, ValueError):
                corp = None
        # 2026-10-25 날짜 둘 — 감사보고서는 재무 자료라 재무기준일 F 의 해로 찾는다(`기준일.py` · F 가 없으면 평가기준일 = 지금과 같다)
        try:
            import 기준일 as _기                                  # noqa: PLC0415
            기준일 = _기.재무기준일(가정).isoformat()
        except Exception:                                        # noqa: BLE001 — 평가기준일 없음 · 꼴 틀림 → 옛 길(오늘)
            기준일 = datetime.date.today().isoformat()
        if not corp:
            return None, "접수번호도 없고 가정 곁 _raw/dart_기업개황.json(corp_code)도 없다 — --접수번호 를 준다"
        접수번호, 보고서명 = 접수번호찾기(corp, 기준일, key)
        if not 접수번호:
            return None, "사업보고서 접수번호를 list API 로 못 찾았다(corp %s · %s)" % (corp, 기준일)
    zp, 어떻게 = 원문받기(접수번호, 곁, key)
    if not zp:
        return None, 어떻게
    낸 = {"형식": "핵심감사사항 1", "만든날": datetime.date.today().isoformat(), "입력": {"가정": os.path.abspath(가정경로), "접수번호": 접수번호, "보고서": 보고서명, "원문": zp, "받기": 어떻게},
         "출처": "OpenDART document.xml(접수번호 %s) — 첨부 감사보고서" % 접수번호, "확인상태": "확인완료(감사보고서 원문 — 인용은 원문 글자)", "보고서": [], "요약표": None, "신호": []}
    with zipfile.ZipFile(zp) as z:
        for n in z.namelist():
            raw = z.read(n)
            x = None
            for enc in ("utf-8", "cp949"):
                try:
                    x = raw.decode(enc)
                    break
                except UnicodeDecodeError:
                    continue
            if x is None or "핵심감사사항" not in x:
                continue
            글 = 벗기기(x)
            if "핵심감사사항으로 결정" not in 글 and "핵심감사사항은 우리의 전문가적 판단" not in 글:
                # 본문의 요약 표
                i = 글.find("핵심감사사항")
                낸["요약표"] = 글[max(0, i - 100):i + 800]
                continue
            연결 = "연결" in 글[:3000] and "연결재무제표" in 글
            감사인 = (re.search(r"([가-힣A-Za-z]+회계법인)", 글) or [None, None])[1]
            의견 = "적정" if "적정하게 표시" in 글 or "적정의견" in 글 else ("한정" if "한정의견" in 글 else ("부적정" if "부적정" in 글 else ("의견거절" if "의견거절" in 글 else "모름")))
            항 = 항목뽑기(글)
            낸["보고서"].append({"첨부": n, "연결": 연결, "감사인": 감사인, "의견": 의견, "항목수": len(항), "항목": 항})
    if not 낸["보고서"]:
        낸["신호"].append({"출처": "kam추출", "종류": "해당 없음", "대상": 접수번호, "값": None, "문턱": None,
                        "글": "원문 묶음에 핵심감사사항 절이 없다 — 미적용 회사(자산 1천억 미만 등)거나 첨부가 다른 접수번호다", "등급": "참고"})
        return 낸, ""
    주 = next((b for b in 낸["보고서"] if b["연결"]), 낸["보고서"][0])
    for a in 주["항목"]:
        낸["신호"].append({"출처": "kam추출", "종류": "핵심감사사항 — 회계 추정 위험", "대상": " · ".join(a["닿는노드"]), "값": a["제목"], "문턱": None,
                        "글": "감사인이 「%s」을 핵심감사사항으로 적었다(%s · %s) — 이 노드의 역사 입력은 경영진 추정에 기댄다. 정규화 · 근거 강도에서 그 사실을 적는다(값은 바꾸지 않는다). 이유: %s"
                             % (a["제목"], 주["감사인"] or "감사인 모름", "연결" if 주["연결"] else "별도", a["이유"][:160]), "등급": "참고"})
    return 낸, ""


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False, description="핵심감사사항(KAM) 추출 — 동인 지도 노드의 회계 추정 위험 표시")
    ap.add_argument("가정")
    ap.add_argument("--접수번호")
    ap.add_argument("--낼")
    a = ap.parse_args()
    try:
        가정 = json.load(io.open(a.가정, encoding="utf-8"))
    except (OSError, ValueError) as e:
        print("가정 파일을 못 읽었다 — %s" % e)
        return 입력오류
    낸, 까 = 분석(가정, a.가정, a.접수번호)
    if 낸 is None:
        print("입력오류 — %s" % 까)
        return 입력오류
    p = a.낼 or os.path.join(os.path.dirname(os.path.abspath(a.가정)), "_raw", "핵심감사사항.json")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    io.open(p, "w", encoding="utf-8").write(json.dumps(낸, ensure_ascii=False, indent=1))
    print("핵심감사사항 — 접수 %s · 보고서 %d · 항목 %s" % (낸["입력"]["접수번호"], len(낸["보고서"]), [b["항목수"] for b in 낸["보고서"]]))
    for s in 낸["신호"]:
        print("   · [%s] %s — %s: %s" % (s["등급"], s["종류"], s["대상"], s["글"][:170]))
    print("→ %s" % p)
    return 통과


if __name__ == "__main__":
    sys.exit(main())

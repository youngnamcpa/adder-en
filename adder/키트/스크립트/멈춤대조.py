# -*- coding: utf-8 -*-
"""멈춤대조 — 멈춤 문항의 선택지 값과 지문을 기록하고(--적기), 다음 실행마다 같은 덧으로 다시 셈해 통지 정정 문안을 낸다(S9-10 · 집대성 3-1).

  python 스크립트/멈춤대조.py 가정.json --적기          # 거친 바퀴 한 표의 문항(결정 3)을 _raw/멈춤기록.json 의 「문항」 에 적는다(선택지 · 지문)
  python 스크립트/멈춤대조.py 가정.json                 # 마지막 멈춤의 문항을 같은 덧으로 다시 셈해 견준다 — 통지 정정 · 멈춤 다시

왜 — 멈춤 문항은 「선택지마다 결과를 숫자로」 묻는다(집대성 3-1 ③). 멈춤을 낸 뒤 엔진이 고쳐지거나 갈래가 표 · 축 · 동인 지도를 바꾸면
사람은 틀린 숫자를 보고 고른다(펄어비스 — 32,483원이라 물었는데 엔진 결함을 고치니 26,479원). 그때 「통지 정정」 을 내야 하는데, 무엇을 물었는지
(선택지의 덧 · 주당가치)와 무엇을 보고 물었는지(지문)가 기록에 없으면 잴 수 없다.

기록(문항[] — 멈춤마다 한 묶음 「멈춤」: {시각, 지문, 문항})
  문항   {대상(가정 번호 · 이름 손잡이), 이름, 잠정값, 범위, 범위출처, 선택지[{이름, 값, 덧: {대상, 방식, x}, 주당}], 안고르면, 뼈대(① ~ ④)}
  지문   {엔진(엔진 소스의 md5) · 명세(명세지문.json) · 가정 · 동인지도 · 축배선 · 핵심표본 · 웹조사(파일 md5 — 없으면 null)}
대조
  선택지 주당가치가 0.5% 넘게 바뀌었거나 선택지의 순위(주당가치 차례)가 바뀌면 → 통지 정정 문안(① 무엇이 바뀌었나 — 바뀐 지문 ② 선택지별 옛 · 새 값
  ③ 순위가 바뀌었나). 순위가 안 바뀌어도 알린다(집대성 3단계)
  지문 가운데 가정 · 동인지도 · 축배선 · 핵심표본 · 웹조사가 다르면 → 「멈춤 다시」(사람이 본 표 · 축 · 동인 지도와 저장 파일이 같아야 한다 — 불변식).
  엔진 · 명세만 다르면 값만 다시 견준다(통지 정정)
종료 코드: 0 같음 · 기록함 / 1 정정 · 멈춤 다시가 필요함 / 2 입력오류. 회사 · 업종 이름은 이 도구에 한 글자도 없다.
"""
import argparse
import datetime
import glob
import hashlib
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:                                      # noqa: BLE001
    pass
from 종료코드 import 통과, 발견, 입력오류  # noqa: E402

여기 = os.path.dirname(os.path.abspath(__file__))
변문턱 = 0.005                                         # 선택지 주당가치 0.5% — 통지 정정
멈춤지문 = ("가정", "동인지도", "축배선", "핵심표본", "웹조사")       # 다르면 멈춤 다시(불변식)


def _md5(경로):
    if not 경로 or not os.path.exists(경로):
        return None
    with open(경로, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def 엔진지문():
    h = hashlib.md5()
    for p in sorted(glob.glob(os.path.join(여기, "엔진", "*.py"))):
        with open(p, "rb") as f:
            h.update(f.read().replace(b"\r\n", b"\n"))
    return h.hexdigest()


def 지문(가정경로):
    곁 = os.path.join(os.path.dirname(os.path.abspath(가정경로)), "_raw")
    명 = os.path.join(여기, "명세지문.json")
    return {"엔진": 엔진지문(), "명세": _md5(명), "가정": _md5(가정경로), "동인지도": _md5(os.path.join(곁, "동인지도.json")),
            "축배선": _md5(os.path.join(곁, "축배선.json")), "핵심표본": _md5(os.path.join(곁, "peers", "핵심표본.json")),
            "웹조사": _md5(os.path.join(곁, "매출스트림_웹조사.json"))}


def _읽기(곳):
    if not os.path.exists(곳):
        return {}
    try:
        return json.load(io.open(곳, encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _쓰기(곳, j):
    os.makedirs(os.path.dirname(os.path.abspath(곳)) or ".", exist_ok=True)
    with io.open(곳, "w", encoding="utf-8", newline="\n") as f:
        json.dump(j, f, ensure_ascii=False, indent=1, default=str)
        f.write("\n")


def _손잡이(r):
    """한 표의 줄 → 선택지 덧의 손잡이(대상 · 방식 · 열). 이름 손잡이(영구ROIC 따위)도 대상으로 다시 선다.
    S9R2 — 한 표가 실제로 민 꼴(`손잡이` — 증가율 줄은 예측 열만 · 수준 물량 줄은 누적 · 정상 수준 묶음은 배율)이 있으면 그것."""
    m = r.get("손잡이") if isinstance(r.get("손잡이"), dict) else {}
    h = {"이름": r.get("이름"), "대상": list(m.get("대상") or r.get("대상") or []), "방식": m.get("방식") or "가산"}
    if m.get("열"):
        h["열"] = list(m["열"])
    return h


def 문항모으기(가정경로, 가정, 시나리오="기준"):
    """거친 바퀴 한 표(같은 _raw 재료)의 문항 → 기록할 꼴."""
    import 거친바퀴 as B                                  # noqa: PLC0415
    곁 = os.path.join(os.path.dirname(os.path.abspath(가정경로)), "_raw")
    지도 = _읽기(os.path.join(곁, "동인지도.json")) or None
    진단 = None if 지도 else (_읽기(os.path.join(곁, "동인진단.json")) or None)
    F = _읽기(os.path.join(곁, "투자능력.json")) or None
    웹 = _읽기(os.path.join(곁, "매출스트림_웹조사.json")) or None
    배선 = B.축배선읽기(os.path.join(곁, "축배선.json"))
    결 = B.한표(가정, 시나리오, 지도=지도, 진단=진단, 웹조사=웹, 배선=배선, F=F, 가정경로=가정경로)
    낸 = []
    for r in 결["표"] + 결.get("범위없음", []):                # S9R2 — 범위 문항(범위 없이 ±5% 넘는 손잡이 — 범위를 묻는다)도 같은 꼴로 기록한다
        if not (r.get("문항") or r.get("범위문항")):
            continue
        m = r.get("문항재료") or {}
        h = _손잡이(r)
        방식 = r.get("손잡이방식", "가산")                  # 프로젝트 총액 = 배율(예측 열 합의 비례) · 구조 판(리드타임 · 구조변경) = 덧으로 못 세움
        선택 = []
        for s in (m.get("선택지") or []):
            v, 지 = s.get("값"), r.get("지금")
            if 방식 == "구조" or not (isinstance(v, (int, float)) and isinstance(지, (int, float))):
                덧 = None
            elif 방식 == "배율":
                덧 = dict(h, 방식="배율", x=(v / 지 - 1) if 지 else 0.0)
            else:
                덧 = dict(h, x=v - 지)
            선택.append({"이름": s.get("이름"), "값": v, "덧": 덧, "주당": s.get("주당")})
        낸.append({"대상": r.get("대상"), "이름": r.get("이름"), "잠정값": r.get("지금"), "범위": r.get("범위"), "범위출처": r.get("범위출처"),
                  "선택지": 선택, "안고르면": m.get("안고르면"), "뼈대": m.get("뼈대"), "종류": m.get("종류") or "값"})
    잔 = 결.get("잔여기간문항")                              # S10R1-N1 — 잔여 기간 매출을 어떻게 잡나(순위 밖 — 값을 무의미하게 하는 자리)
    if isinstance(잔, dict) and 잔.get("선택지"):
        낸.append({"대상": 잔.get("대상"), "이름": 잔.get("이름"), "잠정값": 잔.get("잠정값"), "범위": None, "범위출처": 잔.get("범위출처"),
                  "선택지": [{"이름": s.get("이름"), "값": s.get("값"), "덧": None, "주당": s.get("주당")} for s in 잔["선택지"]],
                  "안고르면": 잔.get("안고르면"), "뼈대": 잔.get("뼈대"), "종류": "잔여기간", "답틀": 잔.get("답틀")})
    return 낸, 결


def 다시셈(가정, 문항, 시나리오="기준"):
    import importlib                                     # noqa: PLC0415
    민 = importlib.import_module("엔진.민감도")
    계 = importlib.import_module("엔진.계산")
    낸 = []
    for s in 문항.get("선택지") or []:
        d = s.get("덧")
        if d is None:                                     # 구조 판의 선택지 — 덧으로 다시 세울 수 없어 옛 값을 그대로 둔다(정정 판정에서 뺀다)
            낸.append(dict(s, 새주당=s.get("주당"), 구조판=True))
            continue
        try:
            h = {"이름": d.get("이름"), "대상": d.get("대상") or [], "방식": d.get("방식", "가산")}
            if d.get("열"):
                h["열"] = d["열"]
            a = 민.움직이기(가정, h, d.get("x") or 0.0, 시나리오)
            v = 계.계산(a, 시나리오)["요약"]["주당가치"]
        except Exception as e:                            # noqa: BLE001
            v = None
            s = dict(s, 오류="%s" % e)
        낸.append(dict(s, 새주당=v))
    return 낸


def 대조(가정경로, 가정, 기록, 시나리오="기준"):
    """→ (판정 글 목록, 정정이 필요한가)."""
    멈춤들 = [x for x in (기록.get("멈춤") or []) if isinstance(x, dict)]
    if not 멈춤들:
        return ["멈춤 기록에 문항이 없다 — `--적기` 로 멈춤을 낼 때 기록한다"], False
    끝 = 멈춤들[-1]
    옛지, 새지 = 끝.get("지문") or {}, 지문(가정경로)
    바뀐 = [k for k in 새지 if 옛지.get(k) != 새지.get(k)]
    글, 필요 = [], False
    if not (끝.get("문항") or []):
        글.append("마지막 멈춤(%s)에 문항이 없다 — 견줄 선택지 값이 없다" % 끝.get("시각"))
    다시 = [k for k in 바뀐 if k in 멈춤지문]
    # S9R1-N7 — 문항마다 멈춤 시각 뒤의 답(`답[]` — 대상 · 노드 · 물음)이 다 왔으면 가정 지문이 바뀐 것은 답을 옮긴 것이다 — 멈춤 다시가 아니라 정정만 본다
    답들 = [x for x in (기록.get("답") or []) if isinstance(x, dict) and ("%s" % x.get("시각", "")) >= ("%s" % 끝.get("시각", ""))]

    def _답있나(q):
        대 = {("%s" % y).replace("A-", "").strip() for y in (q.get("대상") or [])} if isinstance(q.get("대상"), list) else set()
        for x in 답들:
            a대 = x.get("대상")
            a대 = {("%s" % y).replace("A-", "").strip() for y in (a대 if isinstance(a대, list) else ("%s" % a대).split("+"))} if a대 else set()
            if (대 and 대 & a대) or (q.get("이름") and (q.get("이름") == x.get("노드") or q.get("이름") in ("%s" % x.get("물음", "")))):
                return True
        return False
    답완료 = bool(끝.get("문항")) and all(_답있나(q) for q in 끝.get("문항") or [])
    if 답완료 and "가정" in 다시:
        다시.remove("가정")
        글.append("답 도착 — 마지막 멈춤의 문항 %d개에 답이 다 왔다. 가정 지문이 바뀐 것은 답을 옮긴 것으로 보고 선택지 값만 다시 견준다(S9R1-N7)" % len(끝.get("문항") or []))
    if 다시:
        글.append("멈춤 다시 — 사람이 본 %s 가 저장 파일과 다르다(불변식 — 멈춤 %s). 문항을 다시 낸다(집대성 3단계)" % (" · ".join(다시), 끝.get("시각")))
        필요 = True
    for q in 끝.get("문항") or []:
        새 = 다시셈(가정, q, 시나리오)
        옛순 = [s.get("이름") for s in sorted(새, key=lambda s: -(s.get("주당") or 0))]
        새순 = [s.get("이름") for s in sorted(새, key=lambda s: -(s.get("새주당") or 0))]
        변 = [s for s in 새 if isinstance(s.get("주당"), (int, float)) and isinstance(s.get("새주당"), (int, float)) and s["주당"]
             and abs(s["새주당"] / s["주당"] - 1) > 변문턱]
        if 변 or 옛순 != 새순 or any(s.get("새주당") is None and s.get("주당") is not None for s in 새):   # 주당이 처음부터 없는 선택지(사람 입력)는 빼고
            필요 = True
            글.append("통지 정정 — 「%s」" % q.get("이름"))
            글.append("  ① 무엇이 바뀌었나: %s" % ((" · ".join(바뀐) + " 이(가) 멈춤 때와 다르다") if 바뀐 else "지문은 같다 — 같은 덧의 값이 다르다(계산 경로 확인)"))
            글.append("  ② 선택지별 옛 값 → 새 값: %s" % " · ".join("%s %s → %s" % (s.get("이름"), "{:,.0f}".format(s["주당"]) if isinstance(s.get("주당"), (int, float)) else "-",
                                                                           "{:,.0f}".format(s["새주당"]) if isinstance(s.get("새주당"), (int, float)) else "셈 못 함")
                                                         for s in 새))
            글.append("  ③ 선택의 순위: %s" % ("바뀌었다(%s → %s)" % (" > ".join(옛순), " > ".join(새순)) if 옛순 != 새순 else "그대로다 — 그래도 알린다"))
        else:
            글.append("「%s」 — 선택지 값이 0.5%% 안에서 같다(%s)" % (q.get("이름"), " · ".join(
                "%s %s" % (s.get("이름"), "{:,.0f}".format(s["새주당"])) for s in 새 if isinstance(s.get("새주당"), (int, float)))))
    if 바뀐 and not 다시:
        글.append("지문 — %s 만 바뀌었다(엔진 · 명세 — 값만 다시 견줬다)" % " · ".join(바뀐))
    return 글, 필요


def main(argv=None):
    ap = argparse.ArgumentParser(allow_abbrev=False, description="멈춤 문항 기록 · 통지 정정 대조")
    ap.add_argument("가정")
    ap.add_argument("--적기", action="store_true", help="거친 바퀴 한 표의 문항과 지문을 _raw/멈춤기록.json 에 적는다")
    ap.add_argument("--시나리오", default="기준", choices=("비관", "기준", "낙관"))
    ap.add_argument("--기록", default=None, help="멈춤 기록 파일(기본: 가정 곁 _raw/멈춤기록.json)")
    a = ap.parse_args(argv)
    try:
        가정 = json.load(io.open(a.가정, encoding="utf-8"))
    except (OSError, ValueError) as e:
        sys.stderr.write("멈춤대조 입력 오류 — %s\n" % e)
        return 입력오류
    곳 = a.기록 or os.path.join(os.path.dirname(os.path.abspath(a.가정)), "_raw", "멈춤기록.json")
    기록 = _읽기(곳)
    if a.적기:
        try:
            문항, _결 = 문항모으기(a.가정, 가정, a.시나리오)
        except Exception as e:                            # noqa: BLE001
            sys.stderr.write("멈춤대조 입력 오류 — 거친 바퀴를 돌리지 못했다: %s\n" % e)
            return 입력오류
        시 = datetime.datetime.now().isoformat(timespec="minutes")
        기록.setdefault("멈춤", []).append({"시각": 시, "시나리오": a.시나리오, "지문": 지문(a.가정), "문항": 문항})
        기록.setdefault("문항", [])
        기록["문항"] = [x for x in 기록["문항"] if isinstance(x, dict)] + [{"시각": 시, "대상": " + ".join("%s" % y for y in (q.get("대상") or [])),
                                                                          "이름": q.get("이름")} for q in 문항]
        _쓰기(곳, 기록)
        print("멈춤 기록 — 문항 %d개 · 지문 일곱을 적었다: %s" % (len(문항), 곳))
        for q in 문항:
            print("  %s — %s" % (q["이름"], " · ".join("%s %s" % (s["이름"], "{:,.0f}".format(s["주당"]) if isinstance(s.get("주당"), (int, float)) else "-")
                                                for s in q["선택지"])))
        return 통과
    글, 필요 = 대조(a.가정, 가정, 기록, a.시나리오)
    print("\n".join(글))
    return 발견 if 필요 else 통과


if __name__ == "__main__":
    sys.exit(main())

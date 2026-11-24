# -*- coding: utf-8 -*-
"""레터그림배치 — 본편 그림 상한(1.1.7). 본편 그림이 상한(`정합설정.json` 「그림.본편상한」)을 넘으면 우선순위가 낮은 그림부터 부록으로 옮기고
본편의 그 자리에는 가리킴 줄만 남긴다. 레터.py 가 그림 번호를 붙이기 전에 부른다(번호는 옮긴 뒤 한 체계로 이어진다 — 본편 1 ~ 상한, 부록은 그 다음).

우선순위(그림마다 점수 — 높은 것부터 본편에 남긴다 · 같으면 앞의 그림)
  판단  — 그림 종류가 그 절의 판단에 닿는 정도(설정 「그림.판단무게」 · 없으면 「기본무게」) + 그 절에 선 상황 규칙(`그림규칙.json`)이 요구하는 그림이면 「상황무게」
  값 폭 — 그 절의 가정이 결합 민감도에서 주당가치 흔들림에 낸 몫(`_raw/결합민감도.json` 분해 · 주효과) × 「값폭무게」 + 지렛대(값을 가르는 가정)의 절이면 「지렛대무게」
  지킴  — 변수 절마다 점수가 가장 높은 그림 하나 · 모션 표지가 붙은 그림은 「지킴무게」 를 더한다(변수 절에 그림이 남고 · 모션 짝 그림이 본편에 선다)
레터 v27 7단계(디자인 결정 2 · 3 — 설정 키가 있을 때만): 「조건」 — 그림 종류마다 본편에 둘 조건(블록밖 · 지렛대 · 영구비중>x · 종가밖 ·
  수준구분>=n · 부록 — `레터회사그림.조건참`, 거짓이면 부록 · 모르면 그대로) · 「같은종류상한」 — 같은 종류의 그림은 본편에 그 수까지 · 「공통」 — 어느 회사에나 넣는
  그림 종류(결론의 범위 · 주당가치를 좌우하는 가정 · 영업가치에서 주당가치까지)는 지킨다 · 「작은블록문턱」 — 추정 블록의 어느 줄도 주당가치를 그 몫
  넘게 움직이지 않으면(추정 근거표의 무게) 그 블록의 그림을 모두 부록으로(상한 안이어도 — 「가정과 결과」 표의 범위 칸이 그 구실을 한다).
옮긴 그림의 블록(그림 표지 · 굵은 제목 · 표)은 글자 그대로 새 부록 「본편에서 옮긴 그림」 에 절 차례로 싣는다. 본편의 자리에는
「<!-- 그림옮김:종류 -->」 표지만 남는다(`레터그림검사.절검사` 가 이 표지를 그 절의 그림으로 센다 · 1.1.20 — 「「제목」 그림은 부록 X에 있습니다」
가리킴 문장은 문서 안내라 두지 않는다 · `가리킴글` 은 옛 시험이 부른다).
회사 · 업종 이름은 이 모듈에 없다.
"""
from __future__ import annotations

import re

_표지 = re.compile(r"^<!--\s*그림:(\S+?)(?:\s*·\s*모션:([A-Za-z0-9]+))?\s*-->$")
_제목 = re.compile(r"^\*\*그림(?: \d+)?\.\s*(.+?)\*\*")
_절머리 = re.compile(r"^##\s+(\d+)\.\s+(.+?)\s*$")
옮김표지 = "<!-- 그림옮김:%s -->"
_옮김표지식 = re.compile(r"^<!--\s*그림옮김:(\S+)\s*-->$")


def 설정():
    import 레터정합                                         # noqa: PLC0415
    return (레터정합.설정().get("그림")) or {}


def _표끝(줄, i):
    """i 부터 빈 줄을 건너 이어지는 마크다운 표들의 끝 다음 줄 — 표가 없으면 i(`레터HTML._표줄들` 과 같은 읽기)."""
    끝 = i
    while True:
        j = 끝
        while j < len(줄) and not 줄[j].strip():
            j += 1
        if j + 1 < len(줄) and re.match(r"^\|.*\|\s*$", 줄[j].strip()) and re.match(r"^\|[\s\-:|]+\|\s*$", 줄[j + 1].strip()):
            j += 2
            while j < len(줄) and re.match(r"^\|.*\|\s*$", 줄[j].strip()):
                j += 1
            끝 = j
            continue
        return 끝


def 블록들(글):
    """글 → (줄 목록, 본편 시작 · 끝 줄, [{"시작", "끝", "종류", "모션", "제목", "절번호", "절제목", "절키", "차례"}]) — 본편(「# 본편」 아래 · 「# 부록」 앞)의
    그림 블록. 블록 = 그림 표지 줄 → 굵은 제목 줄 → 이어지는 표들(빈 줄 포함). 표지가 없는 굵은 제목 줄도 그림 하나로 센다(그 줄 → 표들)."""
    import 레터그림검사 as V                                 # noqa: PLC0415
    줄 = 글.split("\n")
    처 = next((i for i, t in enumerate(줄) if t.strip() == "# 본편"), None)
    if 처 is None:
        return 줄, None, None, []
    끝 = next((i for i in range(처 + 1, len(줄)) if 줄[i].strip().startswith("# 부록") or 줄[i].strip().startswith("# Part II")), len(줄))
    낸, 절 = [], (None, "", None)
    i = 처 + 1
    while i < 끝:
        t = 줄[i].strip()
        m = _절머리.match(t)
        if m:
            앞 = m.group(2).split(" : ")[0].strip()
            키 = V._절말.get(앞) or next((v for k, v in V._절말.items() if 앞.startswith(k)), None)
            절 = (int(m.group(1)), m.group(2), 키)
            i += 1
            continue
        표 = _표지.match(t)
        if 표 or _제목.match(t):
            시 = i
            종, 모 = (표.group(1), 표.group(2)) if 표 else ("", None)
            j = i + 1 if 표 else i
            while 표 and j < 끝 and not 줄[j].strip():
                j += 1
            제 = _제목.match(줄[j].strip()) if j < 끝 else None
            if 표 and not 제:                                # 제목 없는 표지(띠 · 신호 카드 따위) — 본편 그림 수에 들지 않는다
                i += 1
                continue
            k = _표끝(줄, j + 1)
            낸.append({"시작": 시, "끝": min(k, 끝), "종류": 종, "모션": 모, "제목": 제.group(1).strip() if 제 else "", "절번호": 절[0],
                      "절제목": 절[1], "절키": 절[2], "차례": len(낸)})
            i = max(k, i + 1)
            continue
        i += 1
    return 줄, 처, 끝, 낸


def 절몫(맥):
    """{절 키: 결합 민감도에서 그 절 가정이 낸 몫(0 ~ 1)} — `레터본문.결합몫글` 과 같은 재료 · 같은 절 판정. 재료가 없으면 빈 사전."""
    import 레터본문 as B                                      # noqa: PLC0415
    결 = ((getattr(맥, "원", None) or {}).get("파일") or {}).get("결합민감도") or {}
    주 = (결.get("분해") or {}).get("주효과") or []
    손 = {h.get("이름"): h for h in 결.get("손잡이") or [] if isinstance(h, dict)}
    낸 = {}
    for x in 주:
        if not isinstance(x, dict):
            continue
        try:
            v = float(x.get("몫"))
        except (TypeError, ValueError):
            continue
        k = B._손잡이절(맥, (손.get(x.get("이름")) or {}).get("대상") or [])
        if k:
            낸[k] = 낸.get(k, 0.0) + max(0.0, v)
    return 낸


def 지렛대절(맥):
    """지렛대(값을 가르는 가정)가 서는 항목 절 키 — 없으면 None."""
    try:
        import 레터이야기 as N                                # noqa: PLC0415
        import 레터본문 as B                                  # noqa: PLC0415
        d = N.지렛대(맥) or {}
    except Exception:                                        # noqa: BLE001
        return None
    for b in d.get("번호들") or []:
        if b == "WACC":
            return "할인율"
        k = B.항목절(맥, b) if ("%s" % b).isdigit() else None
        if k:
            return k
    return None


_재는말 = {"매출", "증가율", "변동률", "성장률", "비율", "이익률", "영업이익률", "판가", "판매가격", "가격", "단가", "물량", "출하", "증가", "변동",
          "원가율", "마진", "점유율"}


def 지렛대줄기(맥):
    """1.1.8 — 지렛대(값을 가르는 가정) 이름의 줄기 — 끝의 재는 말을 걷은 앞말(「Intelligent Cloud 매출 증가율」 → 「Intelligent Cloud」 ·
    「메모리 판매가격 변동률」 → 「메모리」). 두 글자 미만은 뺀다. 지렛대 절에서 제목에 이 줄기가 든 그림은 지킨다(그 가정의 경로 · 근거 범위 그림)."""
    try:
        import 레터이야기 as N                                # noqa: PLC0415
        d = N.지렛대(맥) or {}
    except Exception:                                        # noqa: BLE001
        return []
    낸 = []
    for 이 in (d.get("이름들") or [d.get("이름")]):
        말 = ("%s" % (이 or "")).split()
        while 말 and 말[-1] in _재는말:
            말.pop()
        x = " ".join(말).strip()
        if len(x) >= 2 and x not in 낸:
            낸.append(x)
    # 1.1.9 — 지렛대 가정이 속한 매출 구분의 이름도 줄기로(가정 이름은 제품 · 그림 제목은 부문 이름인 회사 — 「카메라모듈 판매가격」 ↔ 「광학솔루션의 매출」)
    #   매출 드라이버 번호: 30 · 34 → 구분 1 · 38 · 42 → 2 · … (8칸씩) · 설비동인 6s0 ~ 6s9 → 구분 s
    구분들 = ((getattr(맥, "구", None) or {}).get("매출구분") or []) if 맥 is not None else []
    for b in d.get("번호들") or []:
        try:
            n = int(b)
        except (TypeError, ValueError):
            continue
        s = (n - 30) // 8 + 1 if 30 <= n < 70 else ((n - 600) // 10 if 610 <= n < 700 else None)
        구 = next((x for x in 구분들 if isinstance(x, dict) and x.get("번호") == s), None) if s else None
        x = ("%s" % ((구 or {}).get("이름") or "")).strip()
        if len(x) >= 2 and x not in 낸:
            낸.append(x)
    return 낸


def _상황그림(맥, 글):
    """{절 키: {그 절에 선 상황 규칙이 요구하는 그림 종류}} — `레터그림검사._상황자리` · `그림규칙.json`(「*」 자리는 모든 절)."""
    import 레터그림검사 as V                                 # noqa: PLC0415
    try:
        규 = V.규칙읽기()
        자리 = V._상황자리(getattr(맥, "가정", None), (getattr(맥, "원", None) or {}).get("파일"), V.본편절들(글))
    except Exception:                                        # noqa: BLE001
        return {}
    낸 = {}
    for r in 규.get("규칙") or []:
        상 = r.get("상황")
        if 상 not in 자리:
            continue
        그림 = r.get("그림")
        for k in 자리[상]:
            키 = r.get("절") if (k == "*" and r.get("절")) else k
            낸.setdefault(키, set()).update([그림] if isinstance(그림, str) else list(그림 or []))
    return 낸


def 점수들(맥, 글, 블, 설=None):
    """그림마다 (점수, 까닭 글) — 모듈 머리의 우선순위."""
    설 = 설 if 설 is not None else 설정()
    import 레터그림검사 as V                                 # noqa: PLC0415
    무게 = 설.get("판단무게") or {}
    기본 = float(설.get("기본무게", 1.0))
    상무 = float(설.get("상황무게", 2.0))
    값무 = float(설.get("값폭무게", 3.0))
    지무 = float(설.get("지렛대무게", 1.0))
    킴 = float(설.get("지킴무게", 10.0))
    변수절 = set(((V.규칙읽기().get("절규칙") or {}).get("변수절")) or ())
    몫 = 절몫(맥) if 맥 is not None else {}
    if not 몫:                                                # v27 7단계 — 결합 민감도가 없으면 추정 근거표의 블록 무게(그 블록 가정이 움직이는 주당가치 몫)
        몫 = 블록무게들(맥)
    지 = 지렛대절(맥) if 맥 is not None else None
    줄기 = 지렛대줄기(맥) if 지 else []
    상 = _상황그림(맥, 글) if 맥 is not None else {}
    낸 = []
    for b in 블:
        s = float(무게.get(b["종류"], 기본))
        까 = ["판단 %.1f(%s)" % (s, b["종류"] or "표지 없음")]
        if b["종류"] and (b["종류"] in 상.get(b["절키"], set()) or b["종류"] in 상.get("*", set())):
            s += 상무
            까.append("상황 규칙 +%.1f" % 상무)
        v = 몫.get(b["절키"], 0.0) * 값무
        if v:
            s += v
            까.append("값 폭 +%.2f" % v)
        if 지 and b["절키"] == 지:
            s += 지무
            까.append("지렛대 절 +%.1f" % 지무)
            if 줄기 and any(x in (b.get("제목") or "") for x in 줄기):   # 1.1.8 — 지렛대 가정의 그림은 지킨다(종전에는 부록으로 밀렸다)
                s += 킴
                까.append("지렛대 그림 +%.0f" % 킴)
        if b["모션"]:
            s += 킴
            까.append("모션 짝 +%.0f" % 킴)
        낸.append([s, 까])
    대표 = {}
    for b, (s, _까) in zip(블, 낸):
        if b["절키"] in 변수절 and (b["절키"] not in 대표 or s > 낸[대표[b["절키"]]][0]):
            대표[b["절키"]] = b["차례"]
    for k, i in 대표.items():
        낸[i][0] += 킴
        낸[i][1].append("변수 절 대표 +%.0f" % 킴)
    return [(s, " · ".join(까)) for s, 까 in 낸]


def 블록무게들(맥):
    """{절 키: 그 절 추정 블록의 줄 무게 가운데 가장 큰 것(몫)} — 추정 근거표(레터 v27 6단계)에서. 결합 민감도 재료가 없을 때 「값 폭」 점수로 쓴다
    (설계의 점수 — 주당가치 민감도 × 값폭무게). 근거표가 없으면 빈 사전."""
    if 맥 is None:
        return {}
    try:
        import 레터원고 as W                                  # noqa: PLC0415
        근 = W.근거표(맥)
    except Exception:                                        # noqa: BLE001
        return {}
    낸 = {}
    for 절키, 블록키들 in (W.블록절.items() if 근 else ()):
        값 = [abs(v) for b in 근.get("블록") or [] if b.get("키") in 블록키들 for z in b.get("줄") or []
             for v in [(z.get("무게") or {}).get("값")] if isinstance(v, (int, float))]
        if 값:
            낸[절키] = min(1.0, max(값))
    return 낸


def 작은블록절(맥, 문턱):
    """레터 v27 7단계(디자인 결정 3) — 추정 블록(블록의 꼴로 선 절)의 어느 줄도 주당가치를 문턱(몫 · 0.01 = 1%) 넘게 움직이지 않는 절 키들.
    무게는 추정 근거표(`레터원고.근거표` — 줄마다 그 줄 가정을 비관 · 낙관 값으로 옮긴 주당가치 변화의 큰 쪽). 무게를 못 잰 줄이 하나라도 있는 블록은 넣지 않는다."""
    if not 문턱 or 맥 is None:
        return set()
    try:
        import 레터원고 as W                                  # noqa: PLC0415
        근 = W.근거표(맥)
    except Exception:                                        # noqa: BLE001
        return set()
    if not 근:
        return set()
    낸 = set()
    for 절키, 블록키들 in W.블록절.items():
        if 절키 not in (getattr(맥, "블록절들", None) or ()):
            continue
        값 = [(z.get("무게") or {}).get("값") for b in 근.get("블록") or [] if b.get("키") in 블록키들 for z in b.get("줄") or []]
        if not 값 or any(not isinstance(v, (int, float)) for v in 값):
            continue                                          # 무게를 못 잰 줄이 하나라도 있으면 작다고 보지 않는다(잰 줄만으로 가르지 않는다)
        if max(abs(v) for v in 값) < 문턱:
            낸.add(절키)
    return 낸


def 그림이름(제목):
    """굵은 제목 → 가리킴에 쓸 그림 이름(「 — 」 앞 · 끝의 괄호 단위 표기를 걷는다)."""
    t = re.split(r"\s—\s", 제목 or "")[0].strip()
    return re.sub(r"\s*\([^()]*\)\s*$", "", t).strip() or t


def 가리킴글(그림들, 글자, 상=110):
    """한 절의 옮긴 그림 → 가리킴 문장(한 문장이 「상」 자를 넘지 않게 이름을 나눠 싣는다 — 문장 길이 검수).
    v27 — 「이 절의 그림 가운데 … 본편 그림 상한에 따라 부록 X로 옮겼다」(작업 과정 설명)를 「「…」 그림은 부록 X에 있습니다」 로."""
    이름 = ["「%s」" % 그림이름(x["제목"]) for x in 그림들]
    머, 이음 = "%s 그림은 부록 %s에 있습니다.", "%s도 같은 부록에 있습니다."
    문, 묶음 = [], []
    for x in 이름:
        시험 = " · ".join(묶음 + [x])
        if 묶음 and len((머 % (시험, 글자)) if not 문 else (이음 % 시험)) > 상:
            문.append((머 % (" · ".join(묶음), 글자)) if not 문 else 이음 % " · ".join(묶음))
            묶음 = [x]
        else:
            묶음.append(x)
    if 묶음:
        문.append((머 % (" · ".join(묶음), 글자)) if not 문 else 이음 % " · ".join(묶음))
    return " ".join(문)


def _은는(글):
    """닫는 괄호 · 낫표를 건너 마지막 글자의 받침으로 「은 · 는」 을 고른다(숫자는 읽는 소리로)."""
    t = re.sub(r"[\s」』)\]\"'.]+$", "", 글)
    c = t[-1:] if t else ""
    if "가" <= c <= "힣":
        받침 = (ord(c) - 0xAC00) % 28 != 0
    elif c.isdigit():
        받침 = c in "013678"
    else:
        받침 = c.lower() in "lmnr"
    return 글 + ("은" if 받침 else "는")


def 다음부록글자(줄):
    있 = [m.group(1) for m in (re.match(r"^## 부록 ([A-Z])\. ", t) for t in 줄) if m]
    return chr(max(ord(x) for x in 있) + 1) if 있 else "A"


def 옮기기(글, 맥=None, 설=None):
    """본편 그림이 상한을 넘으면 옮긴 글을 낸다 → (글, 기록 {"상한", "본편", "옮김": [{"제목", "종류", "절번호", "점수", "까닭"}], "부록"}).
    상한 0 · 「옮기기」 거짓 · 넘지 않으면 글 그대로(기록의 옮김은 빈 목록)."""
    설 = 설 if 설 is not None else 설정()
    상한 = int(설.get("본편상한") or 0)
    같은 = int(설.get("같은종류상한") or 0)                       # v27 7단계 — 같은 종류의 그림은 본편에 이 수까지(0 이면 보지 않는다)
    공통 = set(설.get("공통") or ())                              # v27 7단계 — 어느 회사에나 넣는 그림 종류(지킨다 · 같은 종류 상한 밖)
    줄, 처, 끝, 블 = 블록들(글)
    기록 = {"상한": 상한, "본편": len(블), "옮김": [], "부록": None}
    작은 = 작은블록절(맥, float(설.get("작은블록문턱") or 0)) if 처 is not None else set()
    강제 = {b["차례"] for b in 블 if b["절키"] in 작은 and b["종류"] not in 공통}
    # v27 7단계(다) — 그림 종류마다 본편에 둘 조건(설정 「조건」 · `레터회사그림.조건참`). 거짓이면 부록 · 모르면(None) 그대로 둔다
    조건 = 설.get("조건") or {}
    조건밖 = {}
    if 조건 and 맥 is not None and 처 is not None:
        try:
            import 레터회사그림 as _회                         # noqa: PLC0415
        except Exception:                                    # noqa: BLE001
            _회 = None
        for b in 블:
            c = 조건.get(b["종류"])
            if _회 is None or not c or b["종류"] in 공통 or b["차례"] in 강제:
                continue
            try:
                참 = _회.조건참(맥, c, b["절키"])
            except Exception:                                # noqa: BLE001
                참 = None
            if 참 is False:
                조건밖[b["차례"]] = c
    강제 |= set(조건밖)
    import collections                                       # noqa: PLC0415
    셈0 = collections.Counter(b["종류"] for b in 블 if b["종류"] and b["종류"] not in 공통)
    넘침 = bool(같은 and 셈0 and max(셈0.values()) > 같은)
    if not 상한 or not 설.get("옮기기", True) or 처 is None or not (len(블) > 상한 or 강제 or 넘침):
        return 글, 기록
    점 = 점수들(맥, 글, 블, 설)
    # 1.1.9 — 변수 절 대표 · 모션 짝을 먼저 남기고 남은 자리를 점수 순으로(지렛대 그림이 여럿이면 점수만으로는 변수 절 대표를 밀어냈다 — 시험 G2)
    # v27 7단계 — 공통 그림도 먼저 · 작은 블록의 그림은 후보에서 뺀다 · 같은 종류는 「같은종류상한」 까지
    후보 = [i for i in range(len(블)) if i not in 강제]
    공통들 = sorted((i for i in 후보 if 블[i]["종류"] in 공통), key=lambda i: (-점[i][0], i))      # 어느 회사에나 넣는 그림이 맨 앞(상한에는 든다)
    지킴 = 공통들 + sorted((i for i in 후보 if i not in 공통들 and ("변수 절 대표" in 점[i][1] or "모션 짝" in 점[i][1])), key=lambda i: (-점[i][0], i))
    나머지 = sorted((i for i in 후보 if i not in 지킴), key=lambda i: (-점[i][0], i))
    남김, 셈 = set(), collections.Counter()
    for i in 지킴 + 나머지:
        if len(남김) >= 상한:
            break
        종 = 블[i]["종류"]
        if 같은 and 종 and 종 not in 공통 and 셈[종] >= 같은:
            continue
        남김.add(i)
        셈[종] += 1
    옮 = [b for b in 블 if b["차례"] not in 남김]
    글자 = 다음부록글자(줄[끝:])
    기록["부록"] = 글자
    절별 = {}
    for b in 옮:
        절별.setdefault(b["절번호"], []).append(b)
    새 = []
    앞 = 0
    for b in 옮:
        새 += 줄[앞:b["시작"]]
        같은절 = 절별[b["절번호"]]
        if b is 같은절[0]:                                     # 절마다 가리킴 한 줄(그 절의 첫 옮긴 그림 자리) — 절 안내 · 같은 문형이 쌓이지 않게
            새 += [옮김표지 % (x["종류"] or "제목") for x in 같은절]
            # 1.1.20 — 가리킴 문장(「「…」 그림은 부록 X에 있습니다」 — 문서 안내 · 원칙 3 · 서른 곳 같은 글 · 한 레터에 네 번까지)은 어느 절에도 두지 않는다.
            # 표지만 남는다(그림 검사가 그 절의 그림으로 센다) — 부록의 「N절 「…」에서 옮긴 그림」 머리가 자리를 말한다(종전 추정 블록과 같은 꼴)
            새 += [""]
        앞 = b["끝"]
        while 앞 < len(줄) and 앞 < 끝 and not 줄[앞].strip() and 새 and not 새[-1].strip():
            앞 += 1                                           # 빈 줄 겹침을 줄인다
        까 = 점[b["차례"]][1] + (" · 조건 %s 아님" % 조건밖[b["차례"]] if b["차례"] in 조건밖
                                 else " · 작은 블록(주당가치를 문턱 넘게 움직이는 줄 없음)" if b["차례"] in 강제 else "")
        기록["옮김"].append({"제목": b["제목"], "종류": b["종류"], "절번호": b["절번호"], "점수": 점[b["차례"]][0], "까닭": 까})
    새 += 줄[앞:]
    부 = ["## 부록 %s. 본편에서 옮긴 그림" % 글자, "",
         "본편의 그림 수에 상한을 두어, 각 절의 판단과 관련이 적고 주당가치에 미치는 영향이 작은 그림을 이 부록에 실었습니다.", ""]
    지금절 = None
    for b in 옮:
        if b["절번호"] != 지금절:
            지금절 = b["절번호"]
            부 += ["### %d절 「%s」에서 옮긴 그림" % (b["절번호"], (b["절제목"] or "").split(" : ")[0]), ""]
        블글 = 줄[b["시작"]:b["끝"]]
        while 블글 and not 블글[-1].strip():
            블글 = 블글[:-1]
        부 += 블글 + [""]
    while 새 and not 새[-1].strip():
        새.pop()
    return "\n".join(새 + [""] + 부), 기록


def 옮긴종류(줄들):
    """절 줄들 → 그 절에서 부록으로 옮긴 그림 종류의 모음(가리킴 표지)."""
    return {m.group(1) for m in (_옮김표지식.match(t.strip()) for t in 줄들) if m}

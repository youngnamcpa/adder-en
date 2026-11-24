# -*- coding: utf-8 -*-
"""가정열맞춤 — 템플릿에서 출발한 가정 파일의 열 ID(기간 ID)를 그 파일의 재무기준일 · 기간에 다시 단다 (W8a).

날짜 둘(2026-10-25) — 열은 재무기준일(메타.재무기준일 · 없으면 평가기준일 — `기준일.py`)로 선다. 평가기준일만 옮기고 재무기준일이 같으면
열 ID 는 그대로다.

  python 스크립트/가정열맞춤.py <가정.json> [--낼 <새 파일>] [--버림]

가정 템플릿은 보기 평가기준일로 열 ID 를 달아 두었다(`_열맞춤` 에 그 평가기준일 · 기간이 있다). 메타.평가기준일 과 기간(결산월 ·
실적연도수 · 상세추정연수 · 수렴연수)을 회사에 맞게 고친 뒤 이 도구를 돌리면, 열별 값의 키(`가정.<번호>.<시나리오 · 공통>` ·
`원천.<번호>`)를 새 축의 열 ID 로 옮기고 `_열맞춤` 을 새 축으로 고친다.

옮기는 법 — 같은 ID 는 그대로 둔다. 남은 열은 갈래(실적 · 예측 · TV)마다 자리로 맞춘다: 실적 열은 끝(평가기준일 열)에서부터, 예측 열은
첫 예측 열부터. 새 축에만 있는 열은 빈칸(null)으로 더한다. 옛 축에만 있던 열에 값이 있으면 멈춘다(--버림 이면 버리고 알린다).
값을 이미 채운 파일보다 빈 템플릿에 쓰는 도구다 — 값을 채운 뒤 평가기준일을 바꾸면 자리로 옮긴 값이 뜻에 맞는지 사람이 본다.
Narrative 글(L2)의 장부 키 「{A:613:기준:2H26E|퍼1}」 · 「{R:기준:2.DCF:11:FY2027E|금액}」 의 열 ID 와 `서사연결.<번호>.열` 도 같은 짝으로 옮긴다
(옛 축에만 있던 열을 가리키면 남은 값으로 알린다).
종료 코드: 0 옮김 · 1 옛 열의 값이 남아 멈춤 · 2 입력오류.

  python 스크립트/가정열맞춤.py <가정.json> --옛ID      52/53주(1.1.9) — 템플릿 틀(`_열맞춤`) 없이, 1.1.8 축의 소수 개월 열 키
                                                        (재무기준일 2026-06-27 의 8.9M26A · 3.1M26E)를 월말로 선 새 열(9M26A · 4Q26E)로만 옮긴다
                                                        (`기간축.옛ID` 짝 · 값 · 장부 키 · 서사연결 · 기간.표기). 다른 열은 손대지 않는다.

열을 옮긴 뒤의 재료(1.1.20) — 저자가 엔진으로 셈해 둔 수(`Narrative.자료` — 장부 키 「N:자료:…」)와 원고가 부르는 가정 곁 재료
(`_raw/<이름>.json` — 장부 키 「파일:<이름>:…」)는 옮기기 전 열 · 엔진으로 셈한 값이다. 열을 옮기면(바뀐 열이 하나라도 있으면) 그 재료의
내용 해시를 `_raw/열옮김.json` 에 적어 둔다(낡음 표시). 내용이 그대로인 재료를 원고가 부르면 자체검사 65 가 오류로 알리고 `회차실행.py 재실행`
이 「이 폴더에서 볼 것」 에 적는다 — 재료를 지금 가정으로 다시 셈해 넣으면(내용이 바뀌면) 저절로 풀린다. 열 · 엔진에 기대지 않는 재료면
  python 스크립트/가정열맞춤.py <가정.json> --재료확인 <키 …>     (키 = 「N:자료:<이름>」 · 「파일:<이름>」 · 「모두」)
로 닫는다(실측: 옛 엔진으로 셈한 대안 주당가치가 부록 표에 남아 같은 대안이 본문 · 부록에서 두 값으로 섰다).
"""
import argparse
import datetime
import hashlib
import io
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 기간축 import 기간축, 기간축오류  # noqa: E402
from 종료코드 import 통과, 발견, 입력오류  # noqa: E402

틀키 = "_열맞춤"
시나리오들 = ("비관", "기준", "낙관", "공통")


def _축(평가기준일, 기간, 재무기준일=None):
    """재무기준일을 주면 날짜 둘로 짓는다 — 52/53주 재무기준일은 가장 가까운 월말로 열이 선다(1.1.9 · 엔진 축과 같다)."""
    return 기간축.만들기(평가기준일, 결산월=int(기간.get("결산월") or 12), 실적연도수=int(기간["실적연도수"]),
                      상세추정연수=int(기간["상세추정연수"]), 수렴연수=int(기간.get("수렴연수") or 0),
                      재무기준일=재무기준일)


def _갈래(축):
    return {"실적": [축.ID[i] for i in 축.실적], "예측": [축.ID[i] for i in 축.예측], "TV": [축.ID[축.영구]]}


def 짝(옛축, 새축):
    """옛 ID → 새 ID. 같은 ID 는 그대로, 나머지는 갈래마다 자리로(실적은 끝에서, 예측은 처음부터)."""
    옛, 새 = _갈래(옛축), _갈래(새축)
    낸 = {}
    for 갈 in ("실적", "예측", "TV"):
        a, b = 옛[갈], 새[갈]
        같은 = [x for x in a if x in b]
        for x in 같은:
            낸[x] = x
        남a = [x for x in a if x not in 같은]
        남b = [x for x in b if x not in 같은]
        if 갈 == "실적":
            남a, 남b = 남a[::-1], 남b[::-1]
        for x, y in zip(남a, 남b):
            낸[x] = y
    return 낸, 새


def _옮기기(d, 대응, 새, 이름, 남은값, 버림):
    """{기간 ID: 값} 하나를 옮긴다."""
    if not isinstance(d, dict):
        return d
    갈래들 = set()
    새d = {}
    for k, v in d.items():
        if k in 대응:
            새d[대응[k]] = v
            for 갈, ids in 새.items():
                if 대응[k] in ids:
                    갈래들.add(갈)
        elif k == "기준기간":
            새d[k] = v
        else:
            if v is not None:
                남은값.append("%s.%s = %r" % (이름, k, v))
                if not 버림:
                    새d[k] = v
    for 갈 in 갈래들:
        for c in 새[갈]:
            새d.setdefault(c, None)
    순 = [c for 갈 in ("실적", "예측", "TV") for c in 새[갈]]
    return {k: 새d[k] for k in sorted(새d, key=lambda c: 순.index(c) if c in 순 else -1)}


def 열맞춤(g, 버림=False):
    """(새 가정, 남은 값 목록, 대응). 남은 값이 있고 버림이 아니면 그 열을 그대로 둔다(부르는 쪽이 멈춘다)."""
    틀 = g.get(틀키)
    if not isinstance(틀, dict) or not 틀.get("평가기준일") or not isinstance(틀.get("기간"), dict):
        raise 기간축오류("%s 가 없습니다 — 템플릿에서 출발한 파일만 다시 답니다({평가기준일, 기간})" % 틀키)
    옛축 = _축(틀["평가기준일"], 틀["기간"], 틀.get("재무기준일"))
    import 기준일 as _기준일                                  # noqa: PLC0415 — 날짜 둘: 열은 재무기준일로 선다(없으면 평가기준일)
    try:
        새날 = _기준일.재무기준일(g).isoformat()
        새T = _기준일.평가기준일(g).isoformat()
    except _기준일.기준일오류 as e:
        raise 기간축오류("%s" % e)
    새축 = _축(새T, g.get("기간") or {}, 새날)
    대응, 새 = 짝(옛축, 새축)
    for a, b in (getattr(새축, "옛ID", None) or {}).items():
        대응.setdefault(a, b)                                  # 52/53주(1.1.9) — 1.1.8 축의 소수 개월 열(8.9M26A) → 월말로 선 열(9M26A)
    남은 = []
    for 블록 in ("가정",):
        for n, 벌 in (g.get(블록) or {}).items():
            if isinstance(벌, dict):
                for 시 in list(벌):
                    if 시 in 시나리오들:
                        벌[시] = _옮기기(벌[시], 대응, 새, "%s.%s.%s" % (블록, n, 시), 남은, 버림)
    for n, d in list((g.get("원천") or {}).items()):
        g["원천"][n] = _옮기기(d, 대응, 새, "원천.%s" % n, 남은, 버림)
    _이야기옮기기(g, 대응, 남은)
    g[틀키] = {"평가기준일": (g.get("메타") or {}).get("평가기준일"),
              "기간": {k: (g.get("기간") or {}).get(k) for k in ("결산월", "실적연도수", "상세추정연수", "수렴연수")},
              "열": list(새축.ID)}
    if 새날 != ("%s" % ((g.get("메타") or {}).get("평가기준일") or ""))[:10]:
        g[틀키]["재무기준일"] = 새날                          # 날짜 둘 — 열이 선 날(평가기준일과 다를 때만 적는다)
    return g, 남은, 대응


_장부키 = re.compile(r"\{([^{}|]+?)(\|[^{}|]+)?\}")


def _키옮기기(글, 대응, 이름, 남은):
    """저자 글 속 장부 키의 열 ID(A:<번호>:<시>:<ID> · R:<시>:<시트>:<줄>:<ID> · H:<번호>:<ID>)를 새 ID 로."""
    def 바꿈(m):
        부 = m.group(1).split(":")
        if 부[0] in ("A", "R", "H") and len(부) >= 3 and 부[-1] in 대응:
            부[-1] = 대응[부[-1]]
        elif 부[0] in ("A", "R", "H") and len(부) >= 3 and re.match(r"^(?:FY\d{4}[AE]|\dH\d\d[AE]|\dQ\d\d[AE]|9M\d\d[AE]|TV)$", 부[-1]):
            남은.append("%s 의 장부 키 %s — 새 축에 없는 열" % (이름, m.group(0)))
        return "{%s%s}" % (":".join(부), m.group(2) or "")
    글 = _장부키.sub(바꿈, 글)
    # 1.1.9 — 식 자리표시(「{÷ R:…:8.9M26A R:…|꼴}」 · 「{CAGR …}」 · 「{합 …}」) 안의 키도 옮긴다(종전에는 단순 자리표시만 — 카나리에서 찾음)
    def 식안(m):
        return re.sub(r"((?:A|R|H):[^\s|{}]*:)([^\s|{}:]+)(?=[\s|}])",
                      lambda k: k.group(1) + 대응.get(k.group(2), k.group(2)), m.group(0))
    return re.sub(r"\{[^{}]*\}", 식안, 글)


def _이야기옮기기(g, 대응, 남은):
    """Narrative 글(Narrative · 서사 · 서술 · 시나리오이야기 · 서사연결 · 신호 · 3P)의 장부 키와 서사연결.<번호>.열 을 옮긴다(L2)."""
    def 걷기(v, 이름):
        if isinstance(v, str):
            return _키옮기기(v, 대응, 이름, 남은) if "{" in v else v
        if isinstance(v, dict):
            return {k: 걷기(x, "%s.%s" % (이름, k)) for k, x in v.items()}
        if isinstance(v, list):
            return [걷기(x, "%s[%d]" % (이름, i)) for i, x in enumerate(v)]
        return v
    for 키 in ("Narrative", "서사", "서술", "시나리오이야기", "서사연결", "신호", "3P",
              "관측", "독자근거", "자본비용"):                  # 1.1.9 — 원고 넣기가 채우는 관측 표 · 독자근거 · 자본비용 글의 장부 키도(글만 바꾼다 — 「{」 가 든 글)
        if 키 in g:
            g[키] = 걷기(g[키], 키)
    for n, v in ((g.get("서사연결") or {}) if isinstance(g.get("서사연결"), dict) else {}).items():
        if isinstance(v, dict) and isinstance(v.get("열"), list):
            옛 = v["열"]
            v["열"] = [대응.get(c, c) for c in 옛]
            for c in 옛:
                if c not in 대응:
                    남은.append("서사연결.%s.열 의 %s — 새 축에 없는 열" % (n, c))


def 원고옮기기(가정경로, 대응, 남은):
    """1.1.9 — 같은 회차의 원고 묶음(`_raw/레터원고/*.json`) · 편집 목록(`_raw/편집목록.json`)에 든 장부 키도 새 열 ID 로 옮긴다 → 고친 파일 목록.
    가정만 옮기면 원고 묶음이 옛 키를 쥐고 있어 넣기가 「가정 쪽에서 고친 원고」 로 멈췄다(카나리에서 찾음). 넣은판(`_넣은판*.json`)은 건드리지 않는다."""
    import glob as _glob                                     # noqa: PLC0415
    곳 = os.path.dirname(os.path.abspath(가정경로))
    파일들 = sorted(_glob.glob(os.path.join(곳, "_raw", "레터원고", "*.json"))) + [os.path.join(곳, "_raw", "편집목록.json")]
    고친 = []

    def 걷기(v, 이름):
        if isinstance(v, str):
            return _키옮기기(v, 대응, 이름, 남은) if "{" in v else v
        if isinstance(v, dict):
            return {k: 걷기(x, "%s.%s" % (이름, k)) for k, x in v.items()}
        if isinstance(v, list):
            return [걷기(x, "%s[%d]" % (이름, i)) for i, x in enumerate(v)]
        return v
    for p in 파일들:
        if not os.path.exists(p) or os.path.basename(p).startswith("_넣은판"):
            continue
        try:
            with io.open(p, encoding="utf-8") as f:
                옛 = json.load(f)
        except (OSError, ValueError):
            continue
        새 = 걷기(옛, os.path.basename(p))
        if 새 != 옛:
            with io.open(p, "w", encoding="utf-8", newline="\n") as f:
                json.dump(새, f, ensure_ascii=False, indent=1)
                f.write("\n")
            고친.append(os.path.relpath(p, 곳))
    return 고친


def 옛ID옮기기(g):
    """52/53주(1.1.9) — 1.1.8 축의 소수 개월 열 키(`기간축.옛ID`)만 새 열로 옮긴다 → (새 가정, 남은 값, 대응). 다른 열 · 순서는 그대로다.
    옛 키와 새 키가 한 사전에 함께 있으면 옮기지 않고 남은 값으로 알린다(어느 값이 맞는지 사람이 본다)."""
    축 = 기간축(g)
    옛ID = dict(getattr(축, "옛ID", None) or {})
    남은 = []

    def 바꿈(d, 이름):
        if not isinstance(d, dict) or not any(k in 옛ID for k in d):
            return d
        겹 = [k for k in d if k in 옛ID and 옛ID[k] in d]
        if 겹:
            남은.extend("%s 에 %s 와 %s 가 함께 있다" % (이름, k, 옛ID[k]) for k in 겹)
            return d
        return {옛ID.get(k, k): v for k, v in d.items()}

    for n, 벌 in (g.get("가정") or {}).items():
        if isinstance(벌, dict):
            for 시 in list(벌):
                if 시 in 시나리오들:
                    벌[시] = 바꿈(벌[시], "가정.%s.%s" % (n, 시))
    for n, d in list((g.get("원천") or {}).items()):
        g["원천"][n] = 바꿈(d, "원천.%s" % n)
    기 = g.get("기간") if isinstance(g.get("기간"), dict) else {}
    if isinstance(기.get("표기"), dict):
        기["표기"] = 바꿈(기["표기"], "기간.표기")
    대응 = {c: c for c in 축.ID}
    대응.update(옛ID)
    _이야기옮기기(g, 대응, 남은)
    return g, 남은, 대응


# ══ 열을 옮긴 뒤의 재료(1.1.20) — 낡음 표시 · 낡은 재료 · 확인

열옮김파일 = os.path.join("_raw", "열옮김.json")
열옮김형식 = "열옮김 1"
_재료부름틀 = re.compile(r"(?<![0-9A-Za-z가-힣_])(N:자료|파일):([^\s:|{}\[\]\"',]+)")


def _내용해시(v):
    """JSON 값의 내용 해시(키 차례 · 띄어쓰기와 무관)."""
    return hashlib.sha256(json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
                          .encode("utf-8")).hexdigest()[:16]


def _원고글들(곳, g):
    """재료를 부르는 글 — 가정 전체 · 같은 회차의 원고 묶음(`_raw/레터원고/*.json` — 「_」 로 시작하는 파일은 뺀다) · 편집 목록."""
    import glob as _glob                                     # noqa: PLC0415
    글 = [json.dumps(g, ensure_ascii=False)] if isinstance(g, dict) else []
    if 곳:
        for p in sorted(_glob.glob(os.path.join(곳, "_raw", "레터원고", "*.json"))) + [os.path.join(곳, "_raw", "편집목록.json")]:
            if os.path.basename(p).startswith("_") or not os.path.exists(p):
                continue
            try:
                글.append(io.open(p, encoding="utf-8").read())
            except OSError:
                continue
    return 글


def 재료부름(글들):
    """글 속 장부 키가 부르는 재료 → {「N:자료:<이름>」 · 「파일:<이름>」} (자리표시 · 식 안 어디든)."""
    낸 = set()
    for 글 in 글들:
        for m in _재료부름틀.finditer(글 or ""):
            낸.add("%s:%s" % (m.group(1), m.group(2)))
    return 낸


def 재료해시(g, 곳, 키):
    """재료 하나의 지금 내용 해시 — 「N:자료:<이름>」 은 가정 `Narrative.자료.<이름>`, 「파일:<이름>」 은 `<곳>/_raw/<이름>.json`. 없으면 None."""
    if 키.startswith("N:자료:"):
        z = ((g or {}).get("Narrative") or {}).get("자료") if isinstance(g, dict) else None
        이름 = 키[len("N:자료:"):]
        return _내용해시(z[이름]) if isinstance(z, dict) and 이름 in z else None
    if 키.startswith("파일:") and 곳:
        p = os.path.join(곳, "_raw", 키[len("파일:"):] + ".json")
        if not os.path.exists(p):
            return None
        try:
            return _내용해시(json.load(io.open(p, encoding="utf-8")))
        except (OSError, ValueError):
            try:
                with open(p, "rb") as f:
                    return hashlib.sha256(f.read()).hexdigest()[:16]
            except OSError:
                return None
    return None


def _열옮김읽기(곳):
    p = os.path.join(곳 or ".", 열옮김파일)
    try:
        d = json.load(io.open(p, encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(d, dict):
        return None
    if not isinstance(d.get("기록"), list):
        d["기록"] = []
    if not isinstance(d.get("확인"), dict):
        d["확인"] = {}
    return d


def _열옮김쓰기(곳, d):
    p = os.path.join(곳 or ".", 열옮김파일)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with io.open(p, "w", encoding="utf-8", newline="\n") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)
        f.write("\n")
    return p


def 재료도장(g, 곳, 바뀐, 도구="가정열맞춤"):
    """열을 옮긴 뒤(바뀐 = {옛 ID: 새 ID} 가 비지 않을 때) 재료의 지금 내용 해시를 `_raw/열옮김.json` 에 적는다 → 적은 재료 키 목록.
    적는 재료 — `Narrative.자료` 의 칸 모두(「_」 로 시작하는 칸은 뺀다)와 가정 · 원고 묶음 · 편집 목록이 「파일:<이름>」 으로 부르는
    `_raw/<이름>.json`. 같은 키를 다시 옮기면 앞의 확인(--재료확인)을 지운다(다시 셈할 자리가 새로 생겼다). 바뀐 열이 없거나 재료가 없으면
    적지 않는다."""
    if not 바뀐:
        return []
    z = ((g or {}).get("Narrative") or {}).get("자료") if isinstance(g, dict) else None
    키들 = {"N:자료:%s" % k for k in z if not ("%s" % k).startswith("_")} if isinstance(z, dict) else set()
    키들 |= {k for k in 재료부름(_원고글들(곳, g)) if k.startswith("파일:")}
    재료 = {}
    for k in sorted(키들):
        h = 재료해시(g, 곳, k)
        if h is not None:
            재료[k] = h
    if not 재료:                                              # 셈해 둔 재료가 없는 회차(빈 템플릿에서 출발) — 파일을 만들지 않는다
        return []
    d = _열옮김읽기(곳) or {"형식": 열옮김형식, "기록": [], "확인": {}}
    d["기록"].append({"일시": datetime.datetime.now().replace(microsecond=0).isoformat(), "도구": 도구,
                     "열": dict(바뀐), "재료": 재료})
    for k in 재료:
        d["확인"].pop(k, None)
    _열옮김쓰기(곳, d)
    return sorted(재료)


def 낡은재료(g, 곳):
    """열을 옮긴 뒤 내용이 그대로인데(다시 셈하지 않았는데) 가정 · 원고 묶음 · 편집 목록이 부르는 재료 → [{"키", "일시", "열"}]
    (확인한 키는 뺀다). `_raw/열옮김.json` 이 없으면 빈 목록. 자체검사 65 · 회차실행 재실행 안내가 이 함수를 쓴다."""
    d = _열옮김읽기(곳)
    if not d:
        return []
    최신 = {}
    for r in d["기록"]:
        if isinstance(r, dict) and isinstance(r.get("재료"), dict):
            for k, h in r["재료"].items():
                최신[k] = (h, r.get("일시"), r.get("열") or {})
    if not 최신:
        return []
    부른 = 재료부름(_원고글들(곳, g))
    낸 = []
    for k, (h, 일시, 열) in sorted(최신.items()):
        if k in d["확인"] or k not in 부른:
            continue
        if 재료해시(g, 곳, k) == h:
            낸.append({"키": k, "일시": 일시, "열": 열})
    return 낸


def 재료확인(곳, 키들):
    """--재료확인 — 열 · 엔진에 기대지 않는 재료(또는 다시 셈했더니 내용이 같게 나온 재료)를 닫는다 → (닫은 키, 모르는 키)."""
    d = _열옮김읽기(곳)
    if not d:
        return [], [k for k in 키들 if k != "모두"]
    있는 = {k for r in d["기록"] if isinstance(r, dict) for k in (r.get("재료") or {})}
    고른 = sorted(있는) if "모두" in 키들 else [k for k in 키들 if k in 있는]
    모름 = [k for k in 키들 if k != "모두" and k not in 있는]
    지금 = datetime.datetime.now().replace(microsecond=0).isoformat()
    for k in 고른:
        d["확인"][k] = 지금
    if 고른:
        _열옮김쓰기(곳, d)
    return 고른, 모름


def _열밖글(g):
    """열 옮김이 실제로 무엇을 바꿨는지 재는 글 — 틀(`_열맞춤`)을 뺀 가정 전체."""
    if not isinstance(g, dict):
        return ""
    return json.dumps({k: v for k, v in g.items() if k != 틀키}, ensure_ascii=False, sort_keys=True, default=str)


def _도장알림(가정경로, g, 바뀐, 도구):
    키 = 재료도장(g, os.path.dirname(os.path.abspath(가정경로)), 바뀐, 도구)
    if 키:
        print("  재료 낡음 표시 %d개 → %s — 옮기기 전 열 · 엔진으로 셈한 값이다: %s%s" % (
            len(키), 열옮김파일, " · ".join(키[:12]), " …" if len(키) > 12 else ""))
        print("    원고가 부르는 재료는 지금 가정으로 다시 셈해 넣는다(내용이 바뀌면 저절로 풀린다 · 그대로 두면 자체검사 65 가 막는다). "
              "열 · 엔진에 기대지 않는 재료면 `가정열맞춤.py <가정> --재료확인 <키 …>`")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(allow_abbrev=False, description="가정 파일의 열 ID 를 평가기준일 · 기간에 다시 단다")
    ap.add_argument("가정")
    ap.add_argument("--낼", default=None, help="새 파일(없으면 그 파일을 고친다)")
    ap.add_argument("--버림", action="store_true", help="옛 축에만 있던 열의 값을 버린다")
    ap.add_argument("--옛ID", action="store_true",
                    help="52/53주(1.1.9) — 템플릿 틀 없이 1.1.8 축의 소수 개월 열 키만 월말로 선 새 열로 옮긴다")
    ap.add_argument("--재료확인", nargs="+", default=None, metavar="키",
                    help="1.1.20 — 열을 옮긴 뒤 낡음 표시한 재료(「N:자료:<이름>」 · 「파일:<이름>」 · 「모두」)를 닫는다(열은 옮기지 않는다)")
    a = ap.parse_args()
    if a.재료확인:
        곳 = os.path.dirname(os.path.abspath(a.가정))
        고른, 모름 = 재료확인(곳, a.재료확인)
        print("가정열맞춤 --재료확인 — 닫은 재료 %d개%s" % (len(고른), (": " + " · ".join(고른)) if 고른 else ""))
        if 모름:
            print("  낡음 표시에 없는 키: %s" % " · ".join(모름))
        try:
            g0 = json.load(io.open(a.가정, encoding="utf-8"))
        except (OSError, ValueError):
            g0 = None
        남 = 낡은재료(g0, 곳)
        if 남:
            print("  아직 낡은 재료 %d개: %s" % (len(남), " · ".join(x["키"] for x in 남)))
        return 입력오류 if (모름 and not 고른) else 통과
    try:
        with io.open(a.가정, encoding="utf-8") as f:
            g = json.load(f)
        옛글 = _열밖글(g)
        g, 남은, 대응 = 옛ID옮기기(g) if a.옛ID else 열맞춤(g, a.버림)
    except (OSError, ValueError, KeyError, 기간축오류) as e:
        print("가정열맞춤 — 입력오류: %s" % e)
        return 입력오류
    바뀐 = {k: v for k, v in 대응.items() if k != v}
    if a.옛ID:
        print("가정열맞춤 --옛ID — 옮긴 열: %s" % (" · ".join("%s → %s" % kv for kv in 바뀐.items()) or "없음(52/53주 옛 열 없음)"))
        if 남은:
            print("  옮기지 못한 자리 %d개:" % len(남은))
            for x in 남은[:20]:
                print("    " + x)
            return 발견
        곳 = a.낼 or a.가정
        with io.open(곳, "w", encoding="utf-8", newline="\n") as f:
            json.dump(g, f, ensure_ascii=False, indent=1)
            f.write("\n")
        print("  → %s" % 곳)
        if 바뀐 and not a.낼:                                 # 1.1.9 — 같은 회차의 원고 묶음 · 편집 목록의 장부 키도
            원 = 원고옮기기(a.가정, 대응, 남은)
            print("  원고 묶음 · 편집 목록 %d개도 옮겼다%s" % (len(원), (" — " + " · ".join(원)) if 원 else ""))
        else:
            원 = []
        if 원 or _열밖글(g) != 옛글:                             # 1.1.20 — 실제로 옮긴 키가 있을 때만 옮기기 전 열 · 엔진으로 셈한 재료에 낡음 표시
            _도장알림(곳, g, 바뀐, "가정열맞춤 --옛ID")
        return 통과
    print("가정열맞춤 — 새 열: %s" % " · ".join(g[틀키]["열"]))
    print("  옮긴 열: %s" % (" · ".join("%s → %s" % kv for kv in 바뀐.items()) or "없음(같은 축)"))
    if 남은:
        print("  옛 축에만 있던 열의 값 %d개%s:" % (len(남은), " — 버렸다" if a.버림 else " — 그대로 두고 멈춘다(--버림 으로 버린다)"))
        for x in 남은[:20]:
            print("    " + x)
        if not a.버림:
            return 발견
    곳 = a.낼 or a.가정
    with io.open(곳, "w", encoding="utf-8", newline="\n") as f:
        json.dump(g, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print("  → %s" % 곳)
    if _열밖글(g) != 옛글:                                    # 1.1.20 — 실제로 옮긴 키가 있을 때만 옮기기 전 열 · 엔진으로 셈한 재료에 낡음 표시
        _도장알림(곳, g, 바뀐, "가정열맞춤")
    return 통과


if __name__ == "__main__":
    sys.exit(main())

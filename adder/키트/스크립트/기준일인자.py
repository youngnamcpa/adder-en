# -*- coding: utf-8 -*-
"""기준일인자 — 날짜 인자로 도는 도구가 두 기준일(재무기준일 F · 평가기준일 T)을 한 규칙으로 푼다(2026-10-25 날짜 둘 · K2).

날짜의 정본은 `기준일.py` 다(가정 파일의 메타 두 칸). 이 모듈은 **가정 파일 없이 날짜 인자로 도는 도구**가 그 정본을 같은 규칙으로
부르게 하는 얇은 다리다 — 도구마다 따로 읽지 않는다.

도구는 두 쪽으로 갈린다.
  재무 쪽  재무 원천을 받는 · 읽는 도구(dart_fetch · sec_fetch · 원천축적 씨앗 · 받기 · 신고서재무 · 이력판정 · dart_원천 · sec_원천 ·
           미국원천읽기 · 동인원천 · 투자능력 · 공시채움 · tw_원천 재무). `--기준일` = 재무기준일 F — **지금 뜻 그대로**(별칭 `--재무기준일`)
  평가 쪽  시장 자료를 받는 도구(market_data · kofia_bond_yield · naver_price · peer_* · sec_peer_* · 산업베타 · 무차입세율 · 한계세율 ·
           tw_원천 종가). `--date` · `--기준일` = 평가기준일 T — **지금 뜻 그대로**(별칭 `--평가기준일`)

`--가정 가정.json` 을 주면 날짜 인자를 비워도 그 쪽 날짜를 `기준일.py` 로 푼다(메타.재무기준일이 없으면 F = T — 옛 가정 파일은 지금과 같다).
날짜 인자와 가정이 둘 다 있고 서로 다르면 **인자를 그대로 쓰되(옛 뜻) 경보**를 낸다 — 재무 도구에 평가기준일(분석일)을 넣거나 시장 도구에
재무기준일(분기말)을 넣은 실수를 잡는다.

재무기준일점검 — T 를 알면 받은 정기보고서 목록으로 F 를 대 본다(계약 0-5): F 의 보고가 T 뒤에 제출됐으면 F 가 T 의 정보 집합 밖이고,
F 보다 늦은 기간의 정기 보고가 T 이전에 제출됐으면 F 를 그 기간 끝으로 옮긴다.

표준 라이브러리만 쓴다. 회사 · 업종 이름은 없다.
"""
import datetime
import io
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import 기준일 as _기                                          # noqa: E402

재무, 평가 = "재무", "평가"
이름 = {재무: "재무기준일", 평가: "평가기준일"}
도움말 = {
    재무: "재무기준일 F YYYY-MM-DD — 재무 원천을 받는 날(평가기준일 전에 제출된 마지막 정기보고서의 기간 끝 · 회사 분기말). "
          "가정의 메타.재무기준일(없으면 메타.평가기준일). 옛 이름 --기준일 은 지금 뜻 그대로 재무기준일이다",
    평가: "평가기준일 T YYYY-MM-DD — 시장 자료(금리 · ERP · CRP · 스프레드 · 종가 · 시가총액 · 주식수 · 베타 창 끝 · 법령 시행일)를 받는 날 = "
          "분석일(가정의 메타.평가기준일)",
}
가정도움말 = ("가정 파일 — 날짜 인자를 비우면 기준일.py 로 이 도구 쪽 날짜(재무 쪽 F · 평가 쪽 T)를 푼다. "
          "둘 다 주고 다르면 인자를 그대로 쓰고 경보한다(옛 가정 파일은 F = T)")
제출허용일 = 7          # 52 · 53주 결산 — 기간 끝이 분기말과 며칠 어긋나는 회사


def 날짜(v):
    """'YYYY-MM-DD' · 'YYYYMMDD' · date → date (꼴이 아니면 기준일.기준일오류)."""
    if isinstance(v, str):
        s = v.strip()
        if re.match(r"^\d{8}$", s):
            s = "%s-%s-%s" % (s[:4], s[4:6], s[6:8])
        return _기.날짜(s)
    return _기.날짜(v)


def 가정읽기(가정):
    """경로 · dict · None → dict | None."""
    if isinstance(가정, dict):
        return 가정
    if not 가정:
        return None
    with io.open(가정, encoding="utf-8") as f:
        return json.load(f)


def 가정날짜(가정, 쪽):
    """가정(경로 · dict)의 그 쪽 날짜 → date | None. 재무 쪽은 기준일.재무기준일(없으면 평가기준일) · 평가 쪽은 기준일.평가기준일."""
    g = 가정읽기(가정)
    if g is None:
        return None
    return _기.재무기준일(g) if 쪽 == 재무 else _기.평가기준일(g)


def 꼴(d, 모양="iso"):
    """date → 'YYYY-MM-DD'(iso) · 'YYYYMMDD'(ymd)."""
    return d.strftime("%Y%m%d") if 모양 == "ymd" else d.isoformat()


def 풀기(주어진, 가정, 쪽, 모양="iso", 인자="--기준일", 경보=None, 출력=True):
    """날짜 인자와 가정에서 그 쪽 날짜를 푼다 → 글 | None.

    주어진 값이 있으면 **그대로 돌려준다**(옛 뜻 · 꼴도 바꾸지 않는다). 가정도 있고 날이 다르면 경보(목록 `경보` 에 더하고 표준오류에 한 줄).
    주어진 값이 없고 가정이 있으면 그 쪽 날짜를 `모양` 꼴로. 둘 다 없으면 None(부르는 쪽이 지금처럼 다룬다)."""
    if 주어진 not in (None, ""):
        if 가정:
            try:
                g날 = 가정날짜(가정, 쪽)
                if g날 is not None and 날짜(주어진) != g날:
                    _경보(경보, 출력, "%s %s 이(가) 가정의 %s %s 와 다릅니다 — %s 은(는) %s 입니다. 인자 값을 그대로 씁니다"
                        % (인자, 주어진, 이름[쪽], g날.isoformat(), 인자, 이름[쪽]))
            except (_기.기준일오류, OSError, ValueError) as e:
                _경보(경보, 출력, "가정의 날짜를 읽지 못했습니다 — %s" % e)
        return 주어진
    if 가정:
        try:
            g날 = 가정날짜(가정, 쪽)
        except (_기.기준일오류, OSError, ValueError) as e:
            sys.stderr.write("입력 오류 — 가정에서 %s 을(를) 풀지 못했습니다: %s\n" % (이름[쪽], e))
            raise SystemExit(2)                                        # 종료코드 입력오류 — 명령에서만 부른다
        return 꼴(g날, 모양) if g날 is not None else None
    return None


def 두날짜(가정=None, 재무주어진=None, 평가주어진=None):
    """(F 글 | None, T 글 | None) — 가정이 있으면 기준일.py 로, 없으면 주어진 값. 재무만 주고 평가가 없으면 T = None(부르는 쪽이 F = T 로 읽는다)."""
    F = 풀기(재무주어진, 가정, 재무, 출력=False)
    T = 풀기(평가주어진, 가정, 평가, 출력=False)
    return (꼴(날짜(F)) if F else None), (꼴(날짜(T)) if T else None)


def _경보(목록, 출력, 글):
    if isinstance(목록, list):
        목록.append(글)
    if 출력:
        try:
            sys.stderr.write("경보 — %s\n" % 글)
        except (OSError, ValueError):
            pass


def 머리(낸, 재무기준일=None, 평가기준일=None):
    """산출 머리에 두 날짜를 적는다 — `재무기준일` = F(값이 그날 것) · `평가기준일` = T(알면 · 모르면 지금 값 그대로 둔다). dict 를 고쳐 돌려준다.
    읽는 쪽이 재무 날짜가 필요하면 `재무기준일` 을 먼저, 없으면(옛 파일) `평가기준일` 을 본다."""
    if not isinstance(낸, dict):
        return 낸
    if 재무기준일:
        낸["재무기준일"] = _안전꼴(재무기준일)
    if 평가기준일:
        낸["평가기준일"] = _안전꼴(평가기준일)
    return 낸


def _안전꼴(v):
    """날짜로 읽히면 'YYYY-MM-DD', 아니면 받은 글 그대로(머리 칸에 적을 때 — 꼴 검사는 도구 본문이 한다)."""
    try:
        return 꼴(날짜(v))
    except (_기.기준일오류, TypeError, ValueError):
        return "%s" % v


def 재무날짜읽기(d):
    """도구 산출 머리에서 재무 날짜 → 글 | ''. `재무기준일` 먼저, 없으면(옛 파일 — F = T) `평가기준일`."""
    if not isinstance(d, dict):
        return ""
    return ("%s" % (d.get("재무기준일") or d.get("평가기준일") or "")).strip()


def 재무기준일점검(재무기준일, 평가기준일, 보고들, 허용=제출허용일):
    """T 를 알 때 정기보고서 목록으로 F 를 대 본다 → 경보 글 목록(계약 0-5).

    보고들 = [{"기간끝": 'YYYY-MM-DD', "제출일": 'YYYY-MM-DD' | 'YYYYMMDD', "이름": 글}] — 정기보고서(사업 · 반기 · 분기 · 10-K · 10-Q · 20-F …)만.
      ① F 를 기간 끝(± 허용일)으로 하는 보고가 있는데 모두 T 뒤에 제출됐다 — F 가 T 의 정보 집합 밖이다
      ② F 보다 늦은 기간 끝(허용일 넘게)의 보고가 T 이전(같은 날 포함)에 제출됐다 — F 를 그 기간 끝으로 옮긴다
    F · T 가 같거나 둘 중 하나가 없으면 빈 목록(옛 판 그대로)."""
    if not 재무기준일 or not 평가기준일:
        return []
    F, T = 날짜(재무기준일), 날짜(평가기준일)
    if F == T:
        return []
    경보 = []
    맞는 = []
    늦은 = []
    for b in 보고들 or []:
        try:
            끝 = 날짜(b.get("기간끝"))
            제 = 날짜(b.get("제출일"))
        except (_기.기준일오류, TypeError, AttributeError):
            continue
        if abs((끝 - F).days) <= 허용:
            맞는.append((제, b))
        elif 끝 > F + datetime.timedelta(days=허용) and 제 <= T:
            늦은.append((끝, 제, b))
    if 맞는 and all(제 > T for 제, _ in 맞는):
        제, b = min(맞는, key=lambda x: x[0])
        경보.append("재무기준일 %s 의 보고(%s · 제출 %s)가 평가기준일 %s 뒤에 제출됐습니다 — 평가기준일에 알 수 없던 재무입니다. "
                  "재무기준일을 그 앞 분기말로 물립니다" % (F.isoformat(), b.get("이름") or "", 제.isoformat(), T.isoformat()))
    if 늦은:
        끝, 제, b = max(늦은, key=lambda x: (x[0], x[1]))
        경보.append("평가기준일 %s 전에 더 늦은 기간(%s)의 정기 보고 %s 가 %s 에 제출됐습니다 — 재무기준일 %s 를 %s 로 옮깁니다"
                  % (T.isoformat(), 끝.isoformat(), b.get("이름") or "", 제.isoformat(), F.isoformat(), 끝.isoformat()))
    return 경보

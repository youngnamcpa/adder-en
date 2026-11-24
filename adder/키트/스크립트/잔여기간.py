# -*- coding: utf-8 -*-
"""잔여기간 — 반기 · 분기 기준일 회차의 잔여 기간 열(2H26E 꼴) 매출을 어느 길로 잡을지 환산한다(S10R1-N1 · 2026-10-18).

엔진의 잔여 기간 열 매출 = 연간 기준 금액 − 누계 실적이다(가정_스키마 「증가율은 전년 대비(회계연도 기준)」). 잔여 열에 적는 증가율은
**그 회계연도 전체의 전년 대비**라, 누계 실적이 이미 「전년 × (1 + 증가율)」을 넘은 회사(신작 출시 · 수주 몰림 · 계절성 · 고성장)는
잔여 열 매출이 0 이하가 된다 — 절대 성립할 수 없는 수치다(자체검사 ⑮ 가 오류로 막는다). 이 도구는 사람이 고른 길을 그 회계연도의
전년 대비 율로 환산해 12번 잔여 열에 넣는다. **엔진 · 워크북의 식은 그대로다** — 12번 칸의 뜻(회계연도 전년 대비)이 바뀌지 않는다.

    python 스크립트/잔여기간.py 가정.json                                    # 보기 — 누계 · 전년 · 연간 기준 · 잔여 열 매출 · 세 길의 환산
    python 스크립트/잔여기간.py 가정.json --경로 전년동기 --율 0.10 --적기     # 잔여 = 전년 같은 기간 × (1 + g) — 세 시나리오 같은 g
    python 스크립트/잔여기간.py 가정.json --경로 전년동기 --율 "비관=0,기준=0.1,낙관=0.2" --적기
    python 스크립트/잔여기간.py 가정.json --경로 누계연장 --율 0 --적기       # 잔여 = 누계 실적의 기간 비례 × (1 + g) — 누계 추세 연장
    python 스크립트/잔여기간.py 가정.json --경로 금액 --금액 "기준=150000" --적기   # 잔여 = 사람이 적은 금액(가정의 금액 단위)
    python 스크립트/잔여기간.py 가정.json --경로 연간 --적기                  # 스위치 끔 — 12번 잔여 열을 환산 전 율(원래율)로 되돌리고 관측.잔여기간 을 지운다
    python 스크립트/잔여기간.py 가정.json --구분 "2=전년동기:비관=0.1,기준=0.15,낙관=0.2" --적기   # 구분 2 만 그 길 · 율로(다른 구분은 그대로)
    python 스크립트/잔여기간.py 가정.json --경로 누계연장 --율 0 --구분 1 --구분 "3=금액:기준=20000" --적기   # 구분마다 길이 다를 때

길 셋(회사 · 업종 이름은 어디에도 없다 — 어느 길이 맞는지는 사람이 정한다)
  전년동기  잔여 = (전년 회계연도 − 전년 동기 누계) × (1 + g)      — 계절성이 해마다 같은 회사 · 반기 대 반기로 말하는 회사
  누계연장  잔여 = 누계 실적 × (잔여 개월 ÷ 누계 개월) × (1 + g)  — 누계 기간의 수준이 이어진다고 보는 회사(출시 직후 꺾임은 g < 0)
  금액      잔여 = 사람이 적은 금액                                — 가이던스 · 수주 일정 · 출시 일정으로 금액을 정한 회사
  환산 율 G = (누계 + 잔여) ÷ 전년 회계연도 − 1 → 증가율 경로 구분마다 판매량 증가율 = (1 + G) ÷ (1 + 판매단가 변동률) − 1
  길 ④(2026-10-21 — 통계 기법 8) — 가정 곁 `_raw/계절추세.json`(계절추세.py — 국소 추세 + 분기 계절 + 선행지표 모형 평균)이 있으면 그 잔여 기간
           금액 후보(비관 5% · 기준 중앙값 · 낙관 95%)를 보기와 문항에 「금액」 길의 후보로 나란히 적는다. **값을 정하지 않는다** — 고르는 것은
           사람이고 적는 길은 `--경로 금액 --금액 …` 그대로다. 파일이 없거나 폴백이면 옛 보기 그대로(길 ① ② ③)

구분별(S10R2-N2 · 2026-10-18) — 엔진이 구분별 누계(13번 86~91 의 누계 열)를 받는 회차는 구분마다 「연간 기준 − 그 구분 누계」를 빼므로 한 G 를
모든 구분에 주면 출시 · 수주가 몰린 구분만 음수로 남는다(픽스처 실측: 건강한 구분의 잔여까지 움직이고 몰린 구분은 그대로 음수). 그래서
  · 구분별 누계가 있으면 **구분마다** G_k = (N_k + 잔여_k) ÷ F_k − 1 을 적는다. `--구분 "s=경로:율"` 로 구분마다 길 · 율을 달리 주고, `--구분` 이 없으면
    `--경로 --율` 이 증가율 구분 전부에 간다. `--구분` 을 하나라도 주면 적지 않은 구분은 그대로 둔다
  · 구분별 전년 동기(A2 `전년동기.원천.86~91`)가 없으면 합계 전년 동기 × 그 구분의 전년 매출 비중(F_k ÷ ΣF)으로 가르고 그 사실을 `관측.잔여기간.구분[s].출처` 에 적는다
  · 수준 · 합계 경로 구분이 섞인 회차는 증가율 구분만 환산하고 나머지는 `건너뜀` 에 까닭을 적는다(그 구분의 잔여 기간은 수준 값이 정한다 — rc 2 로 멈추지 않는다)
  · 구분별 누계가 없는 회차(손익 매출 한 줄로 잔여 비율 ρ 를 모든 구분에 곱하는 회차)는 옛 그대로 한 G 다 — 이때 `--구분` 은 받지 않는다(가를 재료가 없다)
기준일 대조(N6-b) — A2 `원천_조립*.json` 의 `기준일` 이 가정의 재무기준일(2026-10-25 날짜 둘 — `메타.재무기준일`, 없으면 `메타.평가기준일`)과
다르면 그 파일의 전년 동기는 쓰지 않는다. 계절추세 산출도 평가기준일 · 재무기준일 둘 다 가정과 같아야 쓴다(낡음). 맞는 파일이 없으면 rc 2 로 멈춘다
(다른 기준일의 반기 응답으로 환산하면 뜻이 틀린 값이 조용히 들어간다). `관측.잔여기간.전년동기누계` 에 사람이 적은 값은 대조 없이 먼저다.

스위치(가정 `관측.잔여기간` — 엔진은 읽지 않는다 · 자체검사 ⑮ 가 12번 잔여 열과 맞는지 본다)
  {"경로": "전년동기" | "누계연장" | "금액", "율": {시나리오: g} | "금액": {시나리오: 금액}, "전년동기누계": 값, "출처": 글, "환산": {시나리오: G}, "시각": …,
   "잔여열": 열 ID, "원래율": {구분: {"판매량": 번호, "꼴": 공통 · 시나리오 · 없음, "값": {시나리오: 환산 전 율}, "없던": [시나리오]}},
   "원래근거": {판매량 번호: 환산 전 근거 · null}, "원래지금율": {시나리오: 환산 전 회계연도 율(엔진 4번 56)}, "환산일": 날짜,
   "원래관측": 환산 전 관측.잔여기간(스위치 끈 채 적어 둔 전년동기누계 등 · 없으면 null), "원래없던블록": [환산 전에 없던 가정 · 근거 · 관측 블록],
   "구분": {s: {"경로", "율" | "금액", "전년동기누계", "출처", "환산": {시나리오: G_k}}}(구분별 누계 회차만), "건너뜀": {s: 까닭}(수준 · 합계 구분 · 적지 않은 구분)}
  없거나 「연간」이면 옛 동작 그대로다(12번 잔여 열 율이 곧 회계연도 전년 대비 — 새 기능 끔 = 옛 값). `--적기` 는 12번을 고치기 전에 환산 전 율을
  `원래율` 에 담고(다시 적을 때는 처음 담은 것을 그대로 잇는다), `--경로 연간 --적기` 가 그것으로 12번 잔여 열과 근거를 되돌린다(S10R2-N3). 원래율이 없는
  옛 기록(S10 개선 3 전)은 되돌릴 재료가 없어 파일을 고치지 않고 rc 1 로 알린다.
  보기 · 문항의 「전년 동기 대비」 길의 g 기본값은 스위치가 꺼져 있으면 지금 율(회계연도 전년 대비)이다. 켜져 있으면 지금 율은 환산 율이라 쓰지 않는다 —
  전년동기 길이면 `율`(사람이 고른 반기 대 반기 g), 아니면 `원래지금율`(환산 전 회계연도 율)이다.
  전년동기누계는 관측에 적은 값이 먼저, 없으면 A2 `_raw/원천_조립*.json` 의 `전년동기.원천.62`(반기보고서 frmtrm_add_amount) ÷ 메타.환산배율.
  `--적기` 는 `_raw/멈춤기록.json` 이 있으면 그 `답[]` 에 「잔여기간」 문항의 답을 남긴다(넘긴 몫 장부가 거친 바퀴 · 멈춤의 잔여 기간 문항을 닫는다).

범위 — 증가율 경로 구분만 환산한다. 수준 · 합계 경로 구분은 건드리지 않고 `건너뜀` 에 까닭을 적는다(그 구분의 잔여 기간은 수준 값이 정한다).
종료 코드 — 0 잔여 열 매출 > 0(보기) · 적었다 · 1 잔여 열 매출 ≤ 0 이 남았다 · 2 입력 오류(기준일이 결산일 · 재료 없음 · A2 기준일 불일치 · 증가율 구분 없음)
"""
import argparse
import copy
import datetime
import glob
import io
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:                                    # noqa: BLE001
    pass
여기 = os.path.dirname(os.path.abspath(__file__))
if 여기 not in sys.path:
    sys.path.insert(0, 여기)
from 종료코드 import 통과, 발견, 입력오류                # noqa: E402

경로목록 = ("연간", "전년동기", "누계연장", "금액")
시나리오목록 = ("비관", "기준", "낙관")
잔여연환산폭 = (0.5, 2.0)        # 엔진 `부수.잔여연환산폭` 과 같은 자 — 잔여 연환산 ÷ 누계 연환산(전년 동기가 없을 때의 자)
전년비율폭 = 0.5                 # N6-f(2026-10-18 결정) — 전년 동기가 있으면 올해 연환산비를 작년 같은 비율 ±50% 와 견준다(계절성이 회사마다 다르다)


def 연환산자(d, 전년동기):
    """N6-f — 잔여 기간 연환산비(잔여 연환산 ÷ 누계 연환산)의 자 → (밖, (lo, hi), 글). A2 전년 동기가 있으면 작년 같은 비율((전년 − 전년 동기) ÷ 잔여 개월 ÷
    (전년 동기 ÷ 누계 개월)) ± `전년비율폭`, 없으면 유형 무관 `잔여연환산폭`(0.5~2.0). 연환산비가 없으면 (False, None, "")."""
    비 = d.get("연환산비")
    if 비 is None:
        return False, None, ""
    F, 잔개, 누개 = d.get("전년"), d.get("잔여개월"), d.get("누계개월")
    if 전년동기 and F and F > 전년동기 and 잔개 and 누개:
        작년 = ((F - 전년동기) / float(잔개)) / (전년동기 / float(누개))
        lo, hi = 작년 * (1 - 전년비율폭), 작년 * (1 + 전년비율폭)
        return not lo <= 비 <= hi, (lo, hi), "작년 같은 비율 %.2f ± %.0f%% = [%.2f, %.2f](A2 전년 동기)" % (작년, 전년비율폭 * 100, lo, hi)
    lo, hi = 잔여연환산폭
    return not lo <= 비 <= hi, (lo, hi), "유형 무관 %.1f~%.1f(전년 동기 없음)" % (lo, hi)
환산허용 = 1e-6                  # 관측.잔여기간 의 환산 율과 엔진 4번 56(잔여 열) 이 이만큼 갈리면 「낡은 환산」


def _수(x):
    return float(x) if isinstance(x, (int, float)) and not isinstance(x, bool) else None


def _엔진():
    import dcf엔진 as E                                       # noqa: PLC0415
    return E


def _축(가정):
    from 엔진.읽개 import 축내기                                  # noqa: PLC0415
    return 축내기(가정)


def _매출표():
    from 엔진 import 매출 as M                                   # noqa: PLC0415
    return M.매출구분


def 구분들(가정):
    """구조.매출구분 → [(번호, 경로, 판매량 번호, 판매단가 번호)] (하위 구분 빼고 — 상위가 담는다)."""
    표 = _매출표()
    낸 = []
    for x in ((가정.get("구조") or {}).get("매출구분") or []):
        if not isinstance(x, dict) or not x.get("번호"):
            continue
        s = int(x["번호"])
        if (x.get("상위") or 0) > 0 or not 1 <= s <= 6:
            continue
        _원, 량, 가, _연, _금 = 표[s - 1]
        낸.append((s, x.get("경로") or "증가율", 량, 가))
    return 낸


def 구분원천(s):
    """구분 s 의 13번 매출 원천 번호(86~91)."""
    return _매출표()[s - 1][0]


def _재무기준일글(가정):
    """재무기준일 F 글(`기준일.py` — 메타.재무기준일, 없으면 평가기준일). 날짜를 못 풀면 None(옛 길 — 메타.평가기준일 글을 그대로 쓴다)."""
    try:
        import 기준일 as _기                                  # noqa: PLC0415
        return _기.재무기준일(가정).isoformat()
    except Exception:                                        # noqa: BLE001
        return None


def 전년동기재료(가정, 가정경로=None):
    """S10R2-N2 · N6-b — 전년 같은 기간 누계의 재료 → {"합계": 값 · None, "구분": {s: 값}, "출처": 글, "기준일": A2 기준일 · None,
    "불일치": [(파일, A2 기준일)], "멈춤": 참이면 A2 가 있는데 기준일이 모두 가정 평가기준일과 다르다}.
    관측.잔여기간.전년동기누계(· 전년동기구분)에 사람이 적은 값이 먼저(대조 없음). 없으면 가정 곁 A2 `_raw/원천_조립*.json` 가운데 `기준일` 이 가정
    `메타.평가기준일` 과 같은 가장 새 파일의 `전년동기.원천.62`(합계) · `86~91`(구분별) ÷ 환산배율. 기준일이 다른 파일은 쓰지 않는다(N6-b)."""
    관 = ((가정.get("관측") or {}).get("잔여기간") or {})
    낸 = {"합계": None, "구분": {}, "출처": "", "기준일": None, "불일치": [], "멈춤": False}
    if isinstance(관, dict) and _수(관.get("전년동기누계")) is not None:
        낸["합계"] = 관["전년동기누계"]
        낸["구분"] = {int(k): v for k, v in (관.get("전년동기구분") or {}).items() if "%s" % k in "123456" and _수(v) is not None}
        낸["출처"] = "관측.잔여기간.전년동기누계(%s)" % (관.get("출처") or "사람")
        return 낸
    if not 가정경로:
        낸["출처"] = "관측.잔여기간.전년동기누계 없음 · 가정 경로 없음(A2 파일을 못 찾는다)"
        return 낸
    곁 = os.path.join(os.path.dirname(os.path.abspath(가정경로)), "_raw")
    배 = _수((가정.get("메타") or {}).get("환산배율")) or 1.0
    기준일 = ("%s" % ((가정.get("메타") or {}).get("평가기준일") or "")).strip()
    재무 = _재무기준일글(가정)                                 # 2026-10-25 날짜 둘 — A2 원천의 기준일은 재무 자료의 날(F)이다
    날말 = "가정 평가기준일"
    if 재무 and 재무 != 기준일:
        기준일, 날말 = 재무, "가정 재무기준일"
    for p in sorted(glob.glob(os.path.join(곁, "원천_조립*.json")), key=lambda q: -os.path.getmtime(q)):
        try:
            d = json.load(io.open(p, encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if not isinstance(d, dict):
            continue
        a2기준 = ("%s" % (d.get("기준일") or "")).strip()
        if 기준일 and a2기준 and a2기준 != 기준일:
            낸["불일치"].append((os.path.basename(p), a2기준))
            continue
        원 = ((d.get("전년동기") or {}).get("원천")) or {}
        v = _수(원.get("62"))
        if v is not None:
            낸["합계"] = v / 배
            낸["기준일"] = a2기준 or None
            낸["구분"] = {s: _수(원.get("%d" % 구분원천(s))) / 배 for s in range(1, 7) if _수(원.get("%d" % 구분원천(s))) is not None}
            낸["출처"] = "A2 %s 전년동기.원천.62(반기보고서 frmtrm_add_amount) ÷ 환산배율 %g%s" % (
                os.path.basename(p), 배, (" · 기준일 %s = %s" % (a2기준, 날말)) if a2기준 else "")
            if 낸["구분"]:
                낸["출처"] += " · 구분별 %s" % " · ".join("%d" % s for s in sorted(낸["구분"]))
            return 낸
    if 낸["불일치"]:
        낸["멈춤"] = True
        낸["출처"] = ("A2 원천_조립의 기준일이 %s %s 과 다르다 — %s. 다른 기준일의 반기 응답으로는 환산하지 않는다(N6-b). "
                   "`dart_원천.py --기준일 %s` 를 다시 돌리거나 관측.잔여기간.전년동기누계 에 적는다" % (
                       날말, 기준일, " · ".join("%s(%s)" % x for x in 낸["불일치"]), 기준일))
        return 낸
    낸["출처"] = "A2 원천_조립에 전년동기 칸이 없다(옛 A2 판이거나 기준일 열이 누계가 아니다) — 관측.잔여기간.전년동기누계 에 적는다"
    return 낸


def 전년동기누계(가정, 가정경로=None):
    """→ (합계 값 · None, 출처 글). `전년동기재료` 의 합계(옛 호출 꼴 — 자체검사 · 시험)."""
    재 = 전년동기재료(가정, 가정경로)
    return 재["합계"], 재["출처"]


def 상황(가정, 가정경로=None, R들=None):
    """시나리오마다 잔여 기간 열의 매출 사정 → {"잔여": ID, "누계": ID, "FY끝": ID, "시나리오": {시: {...}}} 또는 None(잔여 열 없음).
    {...} = 누계 · 전년 · 연간기준 · 잔여매출 · 잔여구분{번호: 값} · 배수(누계 ÷ 전년) · 손익분기율(잔여 = 0 인 회계연도 증가율) · 연환산비 · 지금율(4번 56)."""
    축 = _축(가정)
    if 축.잔여 is None or 축.누계 is None:
        return None
    잔, 누, 끝 = 축.ID[축.잔여], 축.ID[축.누계], 축.ID[축.FY실적[-1]]
    잔년, 누년 = 축.열[축.잔여].년, 축.열[축.누계].년
    표 = _매출표()
    원천 = 가정.get("원천") or {}

    def 원(번호, 열):
        d = 원천.get("%d" % 번호)
        return _수(d.get(열)) if isinstance(d, dict) else None

    # S10R2-N2 — 엔진과 같은 판정: 13번 86~91 의 누계 열에 값이 하나라도 있으면 「구분별차감」(구분마다 연간 기준 − 그 구분 누계)
    구분별누계 = any(원(표[k][0], 누) is not None for k in range(6))
    낸 = {"잔여": 잔, "누계": 누, "FY끝": 끝, "잔여개월": 축.열[축.잔여].개월, "누계개월": 축.열[축.누계].개월, "시나리오": {},
         "구분별누계": 구분별누계, "구분": {s: {"경로": 경, "원천": 표[s - 1][0], "판매량": 량, "판가": 가} for s, 경, 량, 가 in 구분들(가정)}}
    for 시 in 시나리오목록:
        R = (R들 or {}).get(시) or _엔진().계산(가정, 시)
        S = R.get("4.Sales") or {}
        m = S.get("54") or {}
        N, F, 잔매 = _수(m.get(누)), _수(m.get(끝)), _수(m.get(잔))
        구, 구사정 = {}, {}
        for s, 경, _량, _가 in 구분들(가정):
            줄 = S.get(표[s - 1][4]) or {}
            v = _수(줄.get(잔))
            if v is not None and any(_수(x) for c, x in 줄.items() if c != 잔):
                구[s] = v
            Nk = 원(표[s - 1][0], 누)
            Fk = 원(표[s - 1][0], 끝) if 원(표[s - 1][0], 끝) is not None else _수(줄.get(끝))
            구사정[s] = {"경로": 경, "누계": Nk, "전년": Fk, "잔여매출": v, "잔여개월": 낸["잔여개월"], "누계개월": 낸["누계개월"],
                      "배수": (Nk / Fk) if (Nk is not None and Fk) else None,
                      "손익분기율": (Nk / Fk - 1) if (Nk is not None and Fk) else None,
                      "지금율": ((Nk + v) / Fk - 1) if (Nk is not None and v is not None and Fk) else None}
        연기 = (N or 0.0) + (잔매 or 0.0)
        연환산 = (잔매 / 잔년) / (N / 누년) if (N and 잔매 is not None and 잔년 and 누년) else None
        낸["시나리오"][시] = {"누계": N, "전년": F, "연간기준": 연기, "잔여매출": 잔매, "잔여구분": 구, "구분사정": 구사정,
                          "배수": (N / F) if (N is not None and F) else None,
                          "손익분기율": (N / F - 1) if (N is not None and F) else None,
                          "연환산비": 연환산, "지금율": _수((S.get("56") or {}).get(잔)),
                          "잔여개월": 낸["잔여개월"], "누계개월": 낸["누계개월"]}
    return 낸


def 환산(경로, 사정, 값, 전년동기):
    """한 시나리오 — (잔여 매출, 환산 율 G) 또는 (None, 까닭)."""
    N, F = 사정["누계"], 사정["전년"]
    if N is None or not F:
        return None, "누계 · 전년 매출이 없다"
    if 경로 == "전년동기":
        if 전년동기 is None:
            return None, "전년 동기 누계가 없다"
        잔 = (F - 전년동기) * (1 + 값)
    elif 경로 == "누계연장":
        잔 = N * (사정["잔여개월"] / float(사정["누계개월"])) * (1 + 값)
    elif 경로 == "금액":
        잔 = 값
    else:
        return None, "모르는 경로 %s" % 경로
    return 잔, (N + 잔) / F - 1


def 계절추세후보(가정, 가정경로=None):
    """길 ④ — `_raw/계절추세.json` 의 잔여 기간 금액 후보. 파일이 없으면 None.
    {"금액": {시: 금액}(가정의 금액 단위), "구간": [lo, hi], "기준분기", "잔여분기", "경로", "낡음", "명령", "명령까닭", "폴백"} — 폴백이면 금액이 비고 까닭만 있다.
    낡음 = 그 파일의 평가기준일이 가정과 다르다(다른 회차의 모형 — 다시 돌린다).
    명령 = 계절추세가 이 도구가 받는 꼴일 때만 적은 `--경로 금액` 명령 — None 이면(구분별 누계 회차 · 증가율 구분 없음) 금액은 대조값일 뿐 선택지가 아니다."""
    if not 가정경로:
        return None
    try:
        import 정상화                                       # noqa: WPS433 — 쓸 때만(정상화는 이 파일을 부르지 않는다)
        내용, p = 정상화.파일찾기("계절추세.json", 가정경로)
    except Exception:                                     # noqa: BLE001
        p = os.path.join(os.path.dirname(os.path.abspath(가정경로)), "_raw", "계절추세.json")
        try:
            내용 = json.load(io.open(p, encoding="utf-8")) if os.path.exists(p) else None
        except (OSError, ValueError):
            내용 = None
        if not os.path.exists(p):
            p = None
    if not p:
        return None
    if not isinstance(내용, dict):
        return {"금액": {}, "경로": p, "폴백": "계절추세.json 을 못 읽었다"}
    잔 = 내용.get("잔여기간") if isinstance(내용.get("잔여기간"), dict) else {}
    금 = 잔.get("금액길") if isinstance(잔.get("금액길"), dict) else {}
    금 = {시: float(금[시]) for 시 in 시나리오목록 if isinstance(금.get(시), (int, float))}
    기준일 = (내용.get("입력") or {}).get("평가기준일") if isinstance(내용.get("입력"), dict) else None
    가기 = (가정.get("메타") or {}).get("평가기준일")
    낡음 = bool(기준일 and 가기 and str(기준일)[:10] != str(가기)[:10])
    무엇 = "평가기준일"
    if not 낡음 and 기준일:                                   # 2026-10-25 날짜 둘 — 모형의 재무 관측 끝(F)도 가정과 같아야 한다(F 가 없으면 T — 옛 판정 그대로)
        입 = 내용.get("입력") if isinstance(내용.get("입력"), dict) else {}
        파재, 가재 = str(입.get("재무기준일") or 기준일)[:10], _재무기준일글(가정)
        if 가재 and 파재 != 가재:
            낡음, 무엇 = True, "재무기준일"
            기준일, 가기 = 파재, 가재
    return {"금액": {} if 낡음 else 금, "구간": 잔.get("90%"), "기준분기": 잔.get("기준분기"), "잔여분기": 잔.get("잔여분기"),
            "경로": p, "낡음": 낡음, "명령": 잔.get("명령"), "명령까닭": 잔.get("명령까닭"),
            "폴백": ("%s이 다르다(%s ↔ 가정 %s) — 계절추세.py 를 다시 돌린다" % (무엇, 기준일, 가기)) if 낡음
            else (내용.get("폴백") if not 금 else None) or (None if 금 else "금액 후보 없음")}


def _율읽기(글, 이름):
    """「0.1」 · 「비관=0,기준=0.1,낙관=0.2」 → {시: 값}."""
    if 글 is None:
        return None
    글 = ("%s" % 글).strip()
    if "=" not in 글:
        v = float(글)
        return {시: v for 시 in 시나리오목록}
    낸 = {}
    for 조각 in 글.split(","):
        k, v = 조각.split("=")
        k = k.strip()
        if k not in 시나리오목록:
            raise ValueError("%s 의 시나리오 이름은 비관 · 기준 · 낙관 — 「%s」" % (이름, k))
        낸[k] = float(v)
    return 낸


def _구분읽기(목록, 기본경로, 기본값들):
    """`--구분` 들 — 「2」 · 「2=전년동기:비관=0.1,기준=0.2,낙관=0.3」 · 「3=금액:기준=20000」 → {s: (경로, {시: 값})}. 「2」 만이면 기본 경로 · 값."""
    낸 = {}
    for 글 in 목록 or []:
        글 = ("%s" % 글).strip()
        if not 글:
            continue
        if "=" not in 글:
            if not 글.isdigit():
                raise ValueError("--구분 「%s」 — 구분 번호(1~6)로 시작해야 한다" % 글)
            s = int(글)
            if 기본경로 is None or not 기본값들:
                raise ValueError("--구분 %d 에 길 · 율이 없다 — 「%d=경로:율」 로 적거나 --경로 --율 을 함께 준다" % (s, s))
            낸[s] = (기본경로, dict(기본값들))
            continue
        머리, 나머지 = 글.split("=", 1)
        if not 머리.strip().isdigit():
            raise ValueError("--구분 「%s」 — 구분 번호(1~6)로 시작해야 한다" % 글)
        s = int(머리)
        if ":" not in 나머지:
            raise ValueError("--구분 %d — 「경로:율」 꼴이어야 한다(예: 2=전년동기:기준=0.1)" % s)
        경, 값글 = 나머지.split(":", 1)
        경 = 경.strip()
        if 경 not in ("전년동기", "누계연장", "금액"):
            raise ValueError("--구분 %d 의 길은 전년동기 · 누계연장 · 금액 — 「%s」" % (s, 경))
        낸[s] = (경, _율읽기(값글, "--구분 %d" % s))
    return 낸


원래근거머리 = "[판단] 잔여 기간 열 — 관측.잔여기간"       # 적기가 근거 칸을 새로 세울 때의 첫 칸 — 되돌릴 때 그 칸이면 지운다
_원래키 = ("잔여열", "원래율", "원래근거", "원래지금율", "환산일", "원래관측", "원래없던블록")


def _켜짐(가정):
    관 = ((가정.get("관측") or {}).get("잔여기간") or {})
    return 관 if isinstance(관, dict) and 관.get("경로") not in (None, "연간") else None


def 원래담기(가정, 잔, 사정들=None):
    """S10R2-N3 — 환산 전 12번 잔여 열(증가율 경로 구분의 판매량 줄) · 그 근거 · 엔진 4번 56(환산 전 회계연도 율)을 담는다 → {원래 키: 값}."""
    A = 가정.get("가정") or {}
    근 = 가정.get("근거") or {}
    원, 원근 = {}, {}
    for s, _경, 량, _가 in 구분들(가정):
        벌 = A.get("%d" % 량)
        rec = {"판매량": 량, "꼴": "없음", "값": {}, "없던": []}
        if isinstance(벌, dict) and "공통" in 벌 and not any(k in 벌 for k in 시나리오목록):
            rec["꼴"] = "공통"
            한 = 벌.get("공통")
            if isinstance(한, dict) and 잔 in 한:
                rec["값"]["공통"] = 한[잔]
        elif isinstance(벌, dict):
            rec["꼴"] = "시나리오"
            for 시 in 시나리오목록:
                한 = 벌.get(시)
                if isinstance(한, dict):
                    if 잔 in 한:
                        rec["값"][시] = 한[잔]
                else:
                    rec["없던"].append(시)
        원["%d" % s] = rec
        원근["%d" % 량] = copy.deepcopy(근.get("%d" % 량)) if "%d" % 량 in 근 else None
    지 = {시: d.get("지금율") for 시, d in ((사정들 or {}).get("시나리오") or {}).items()}
    옛관 = (가정.get("관측") or {}).get("잔여기간")
    return {"잔여열": 잔, "원래율": 원, "원래근거": 원근, "원래지금율": 지, "환산일": datetime.date.today().isoformat(),
            "원래관측": copy.deepcopy(옛관) if isinstance(옛관, dict) else None,
            "원래없던블록": [k for k in ("가정", "근거", "관측") if k not in 가정]}


def 되돌리기(가정):
    """S10R2-N3 — 스위치 끔(`--경로 연간`). `관측.잔여기간.원래율` 로 12번 잔여 열과 근거를 환산 전으로 되돌리고 관측.잔여기간 을 지운다
    → (새 가정, 글 목록, 됨). 됨 = 거짓이면 되돌릴 재료가 없다(원래율 없는 옛 기록) — 새 가정은 손대지 않은 사본이다."""
    a = copy.deepcopy(가정)
    관 = ((a.get("관측") or {}).get("잔여기간"))
    if not isinstance(관, dict) or not 관:
        return a, ["관측.잔여기간 이 없습니다 — 스위치가 이미 꺼져 있습니다(12번 잔여 열 율이 곧 회계연도 전년 대비)"], True
    if 관.get("경로") in (None, "연간"):
        a["관측"].pop("잔여기간", None)
        return a, ["관측.잔여기간(경로 %s)을 지웠습니다 — 환산한 적이 없어 12번은 그대로입니다" % (관.get("경로") or "없음")], True
    원, 잔 = 관.get("원래율"), 관.get("잔여열")
    if not isinstance(원, dict) or not 원 or not 잔:
        return copy.deepcopy(가정), ["관측.잔여기간 에 원래율이 없습니다(S10 개선 3 전에 적은 기록) — 12번 잔여 열은 환산 율이고 환산 전 율은 어디에도 없습니다. "
                                 "파일을 고치지 않았습니다 — 12번 잔여 열을 손으로 되돌린 뒤 관측.잔여기간 을 지웁니다"], False
    A = a.setdefault("가정", {})
    글 = []
    for s, rec in sorted(원.items()):
        량 = "%d" % rec["판매량"]
        값 = rec.get("값") or {}
        벌 = A.get(량)
        if rec.get("꼴") == "없음":
            if isinstance(벌, dict):
                for 시 in list(벌):
                    한 = 벌.get(시)
                    if isinstance(한, dict):
                        한.pop(잔, None)
                        if not 한:
                            벌.pop(시)
                if not 벌:
                    A.pop(량, None)
            글.append("구분 %s · A-%s — 환산 전에 줄이 없었다 → 적기가 넣은 잔여 열 칸을 걷었다" % (s, 량))
            continue
        if not isinstance(벌, dict):
            벌 = A[량] = {}
        if rec.get("꼴") == "공통":
            세 = [벌.get(시) for 시 in 시나리오목록]

            def 밖(d):
                return {k: v for k, v in d.items() if k != 잔}
            if all(isinstance(x, dict) for x in 세) and all(밖(x) == 밖(세[0]) for x in 세):
                공 = 밖(세[0])
                if "공통" in 값:
                    공[잔] = 값["공통"]
                for 시 in 시나리오목록:
                    벌.pop(시, None)
                벌["공통"] = 공
                글.append("구분 %s · A-%s — 공통 벌로 되돌렸다(잔여 열 %s)" % (s, 량, 값.get("공통")))
            else:
                for 시 in 시나리오목록:
                    한 = 벌.setdefault(시, {})
                    if "공통" in 값:
                        한[잔] = 값["공통"]
                    else:
                        한.pop(잔, None)
                글.append("구분 %s · A-%s — 환산 뒤 시나리오마다 다른 열을 고쳐 공통 벌로 접지 못했다 · 세 벌의 잔여 열을 환산 전 %s 로" % (s, 량, 값.get("공통")))
            continue
        for 시 in 시나리오목록:
            한 = 벌.get(시)
            if 시 in 값:
                if not isinstance(한, dict):
                    한 = 벌[시] = {}
                한[잔] = 값[시]
            elif isinstance(한, dict):
                한.pop(잔, None)
                if not 한 and 시 in (rec.get("없던") or []):
                    벌.pop(시)
        글.append("구분 %s · A-%s — 잔여 열을 환산 전 율로(%s)" % (s, 량, " · ".join("%s %s" % (시, 값[시]) for 시 in 시나리오목록 if 시 in 값)))
    근 = a.get("근거") or {}
    for 량, 옛 in ((관.get("원래근거") or {}).items()):
        e = 근.get(량)
        if not isinstance(e, list):
            continue
        if 옛 is None:
            if e and e[0] == 원래근거머리:
                근.pop(량)
                continue
        if len(e) > 2 and isinstance(e[2], str):
            e[2] = " · ".join(x for x in e[2].split(" · ") if not (x.startswith("잔여 기간 열(") and "관측.잔여기간(" in x))
        if isinstance(옛, list) and e[:len(옛)] == 옛 and all(x == "" for x in e[len(옛):]):
            근[량] = copy.deepcopy(옛)
    if isinstance(관.get("원래관측"), dict):                 # 스위치 끈 채 적어 둔 관측(전년동기누계 등)은 그대로 둔다
        a["관측"]["잔여기간"] = copy.deepcopy(관["원래관측"])
        글.append("관측.잔여기간 을 환산 전 기록으로 되돌렸습니다(환산 %s · 경로 %s — 스위치 끔)" % (관.get("환산일") or 관.get("시각") or "-", 관.get("경로")))
    else:
        a["관측"].pop("잔여기간", None)
        글.append("관측.잔여기간 을 지웠습니다(환산 %s · 경로 %s)" % (관.get("환산일") or 관.get("시각") or "-", 관.get("경로")))
    for k in (관.get("원래없던블록") or []):
        if k in a and not a[k]:
            a.pop(k)
    return a, 글, True


def 기본g(가정, 사정, 시):
    """S10R2-N3 — 보기 · 문항의 「전년 동기 대비」 길 g 기본값 → (g, 글). 스위치가 켜져 있으면 지금 율(4번 56)은 환산 율이라 쓰지 않는다 —
    전년동기 길이면 관측.잔여기간.율(사람이 고른 반기 대 반기 g), 아니면 원래지금율(환산 전 회계연도 율). 둘 다 없으면 (None, 까닭)."""
    관 = _켜짐(가정)
    if 관 is None:
        return 사정.get("지금율"), "지금 율"
    if 관.get("경로") == "전년동기" and _수((관.get("율") or {}).get(시)) is not None:
        return 관["율"][시], "관측.잔여기간.율(고른 g)"
    if _수((관.get("원래지금율") or {}).get(시)) is not None:
        return 관["원래지금율"][시], "환산 전 회계연도 율"
    return None, "스위치가 켜졌는데 환산 전 율 기록이 없다(지금 율은 환산 율이라 g 로 쓰지 않는다)"


def _판매량적기(A, 량, 가, 잔, 시, G):
    """증가율 경로 구분의 12번 잔여 열 — 판매량 증가율 = (1 + G) ÷ (1 + 판매단가 변동률) − 1."""
    p = 0.0
    if 가 is not None:
        벌p = A.get("%d" % 가)
        한p = (벌p.get(시, 벌p.get("공통")) if isinstance(벌p, dict) else None) or {}
        p = _수(한p.get(잔)) or 0.0
    v = (1 + G) / (1 + p) - 1
    벌 = A.get("%d" % 량)
    if not isinstance(벌, dict):
        벌 = A["%d" % 량] = {}
    if "공통" in 벌 and not any(k in 벌 for k in 시나리오목록):       # 공통 벌은 세 벌로 편다(잔여 열만 시나리오마다 다르다)
        공 = 벌.pop("공통")
        for k in 시나리오목록:
            벌[k] = dict(공 or {})
    벌.setdefault(시, {})[잔] = v
    return v


def _근거덧(a, 량, 잔, 경로, 구분=None):
    근 = a.setdefault("근거", {}).setdefault("%d" % 량, [원래근거머리, "", "", ""])
    덧 = "잔여 기간 열(%s)은 관측.잔여기간(%s%s — 잔여기간.py)으로 환산한 회계연도 전년 대비 율" % (잔, 경로, (", 구분 %d" % 구분) if 구분 else "")   # 「 · 」 금지 — 되돌리기가 그 글자로 쪼갠다
    if isinstance(근, list):
        while len(근) < 3:
            근.append("")
        if 덧 not in ("%s" % 근[2]):
            근[2] = ("%s · %s" % (근[2], 덧)).strip(" ·")


def 적기(가정, 경로, 값들, 전년동기, 출처, 사정들, 구분지정=None, 전년동기구분=None):
    """가정 사본에 관측.잔여기간 과 12번 잔여 열(판매량 증가율 = (1 + G) ÷ (1 + 판매단가) − 1)을 적는다 → (새 가정, 환산 {시: G}, 글 목록).
    S10R2-N3 — 고치기 전에 환산 전 율을 `원래율` 에 담는다. 스위치가 이미 켜져 있으면(다시 적기) 처음 담은 원래율을 그대로 잇는다.
    S10R2-N2 — 구분별 누계 회차(`사정들["구분별누계"]`)는 증가율 구분마다 G_k = (N_k + 잔여_k) ÷ F_k − 1 을 적는다. `구분지정` = {s: (경로, {시: 값})} 이
    있으면 그 구분만 그 길로(적지 않은 구분은 그대로), 없으면 `경로 · 값들` 이 증가율 구분 전부에 간다. 구분별 전년 동기(`전년동기구분` {s: 값})가 없으면
    합계 전년 동기 × 전년 매출 비중으로 가른다. 수준 · 합계 구분은 건드리지 않고 `건너뜀` 에 적는다. 구분별 누계가 없는 회차는 옛대로 한 G 다."""
    a = copy.deepcopy(가정)
    잔 = 사정들["잔여"]
    옛관 = _켜짐(가정)
    if 옛관 is None:
        원래 = 원래담기(가정, 잔, 사정들)
    elif 옛관.get("원래율"):
        원래 = {k: copy.deepcopy(옛관[k]) for k in _원래키 if k in 옛관}
    else:
        원래 = {}                                    # 원래율 없는 옛 기록 — 지금 12번은 이미 환산 율이라 원래로 담지 않는다(되돌리기가 알린다)
    A = a.setdefault("가정", {})
    글, 건너뜀, 구분기록 = [], {}, {}
    구분목록 = 구분들(a)
    증가율구분 = [(s, 경, 량, 가) for s, 경, 량, 가 in 구분목록 if 경 == "증가율"]
    for s, 경, _량, _가 in 구분목록:
        if 경 != "증가율":
            건너뜀[s] = "%s 경로 — 잔여 기간은 수준 값이 정한다(환산하지 않음)" % 경
    if not 증가율구분:
        raise ValueError("증가율 경로 구분이 없다 — 환산할 줄이 없다(%s)" % " · ".join("%d %s" % (s, 경) for s, 경, *_ in 구분목록))
    if 사정들.get("구분별누계"):
        if 구분지정:
            모름 = [s for s in 구분지정 if s not in {x[0] for x in 증가율구분}]
            if 모름:
                raise ValueError("--구분 %s 은 증가율 경로 구분이 아니다(증가율 구분: %s)" % (
                    " · ".join("%d" % x for x in 모름), " · ".join("%d" % x[0] for x in 증가율구분)))
        합F = sum((사정들["시나리오"]["기준"]["구분사정"].get(s) or {}).get("전년") or 0.0 for s, *_ in 구분목록)
        G합 = {}
        for 시 in 시나리오목록:
            ΣN = Σ잔 = ΣF = 0.0
            for s, 경, 량, 가 in 증가율구분:
                사 = 사정들["시나리오"][시]["구분사정"][s]
                if 구분지정 and s not in 구분지정:
                    if 시 == "기준":
                        건너뜀[s] = "--구분 에 없어 그대로 둠(지금 회계연도 율 %s)" % (("%.1f%%" % (사["지금율"] * 100)) if 사.get("지금율") is not None else "-")
                    continue
                경_s, 값_s = 구분지정[s] if 구분지정 else (경로, 값들)
                if 시 not in 값_s:
                    continue
                Fk = 사.get("전년")
                if (전년동기구분 or {}).get(s) is not None:
                    전동, 전출 = 전년동기구분[s], "A2 구분별 전년 동기(원천 %d)" % 구분원천(s)
                elif 전년동기 is not None and Fk and 합F:
                    전동, 전출 = 전년동기 * Fk / 합F, "합계 전년 동기 %s × 전년 매출 비중 %.1f%%(구분별 전년 동기 없음 — 매출 비중으로 가름)" % (
                        "{:,.0f}".format(전년동기), Fk / 합F * 100)
                else:
                    전동, 전출 = None, "전년 동기 없음"
                r, G = 환산(경_s, 사, 값_s[시], 전동)
                if r is None:
                    raise ValueError("구분 %d · %s — %s" % (s, 시, G))
                _판매량적기(A, 량, 가, 잔, 시, G)
                기 = 구분기록.setdefault(s, {"경로": 경_s, ("금액" if 경_s == "금액" else "율"): 값_s, "전년동기누계": 전동, "출처": 전출, "환산": {}})
                기["환산"][시] = G
                ΣN += 사.get("누계") or 0.0
                Σ잔 += r
                ΣF += Fk or 0.0
            if ΣF:
                G합[시] = (ΣN + Σ잔) / ΣF - 1
        for s, 경, 량, 가 in 증가율구분:
            if s in 구분기록:
                _근거덧(a, 량, 잔, 구분기록[s]["경로"], s)
        G들 = G합
        for s, 기 in sorted(구분기록.items()):
            글.append("구분 %d — 경로 %s · 전년 동기 %s(%s) · 환산 %s" % (
                s, 기["경로"], "{:,.0f}".format(기["전년동기누계"]) if 기["전년동기누계"] is not None else "-", 기["출처"],
                " · ".join("%s %.2f%%" % (시, G * 100) for 시, G in 기["환산"].items())))
    else:
        if 구분지정:
            raise ValueError("구분별 누계(13번 86~91 의 누계 열)가 없는 회차다 — 엔진이 손익 매출 한 줄로 잔여 비율을 모든 구분에 곱하므로 구분별로 가를 수 없다. --구분 없이 --경로 --율 로 적는다")
        G들 = {}
        for 시 in 시나리오목록:
            if 시 not in 값들:
                continue
            r, G = 환산(경로, 사정들["시나리오"][시], 값들[시], 전년동기)
            if r is None:
                raise ValueError("%s — %s" % (시, G))
            G들[시] = G
        for s, 경, 량, 가 in 증가율구분:
            for 시, G in G들.items():
                _판매량적기(A, 량, 가, 잔, 시, G)
            _근거덧(a, 량, 잔, 경로)
    관 = a.setdefault("관측", {})
    길들 = {v["경로"] for v in 구분기록.values()}
    if 구분기록 and (len(길들) > 1 or (경로 and 길들 != {경로})):
        경로글 = "구분별"
    else:
        경로글 = 경로 or (next(iter(길들)) if 길들 else None)
    새 = {"경로": 경로글, "전년동기누계": 전년동기, "출처": 출처,
         "환산": G들, "시각": datetime.datetime.now().isoformat(timespec="seconds"),
         "뜻": "잔여 기간 열 매출을 어느 길로 잡았나(S10R1-N1). 12번 잔여 열은 이 환산의 회계연도 전년 대비 율이다 — 자체검사 ⑮ 가 맞는지 본다. "
               "원래율은 환산 전 율이다 — `--경로 연간 --적기` 가 그것으로 되돌린다(S10R2-N3). 구분별 누계 회차는 구분마다 환산했다(S10R2-N2 — `구분`)"}
    if 값들:
        새[("금액" if 경로 == "금액" else "율")] = 값들
    if 구분기록:
        옛구분 = copy.deepcopy((옛관 or {}).get("구분") or {}) if isinstance(옛관, dict) else {}
        옛구분 = {int(k): v for k, v in 옛구분.items() if "%s" % k in "123456"}
        옛구분.update(구분기록)
        새["구분"] = {"%d" % k: v for k, v in sorted(옛구분.items())}
        if 전년동기구분:
            새["전년동기구분"] = {"%d" % k: v for k, v in sorted(전년동기구분.items())}
    if 건너뜀:
        새["건너뜀"] = {"%d" % k: v for k, v in sorted(건너뜀.items())}
    관["잔여기간"] = 새
    관["잔여기간"].update(원래)
    if 출처 is None:
        관["잔여기간"].pop("출처")
    글.append("관측.잔여기간 — 경로 %s · 환산 %s%s" % (경로글, " · ".join("%s %.2f%%" % (시, G * 100) for 시, G in G들.items()),
                                              (" · 건너뜀 %s" % " · ".join("%d(%s)" % (k, v.split(" — ")[0]) for k, v in sorted(건너뜀.items()))) if 건너뜀 else ""))
    return a, G들, 글


def 점검(가정, 가정경로=None, R들=None):
    """자체검사 ⑮ 가 부른다 — 관측.잔여기간 의 환산이 지금 12번 잔여 열(엔진 4번 56)과 맞는가 → [(시, 기대 G, 지금 G)] 갈린 것만. 스위치가 꺼졌으면 []."""
    관 = ((가정.get("관측") or {}).get("잔여기간") or {})
    if not isinstance(관, dict) or 관.get("경로") in (None, "연간"):
        return []
    사정들 = 상황(가정, 가정경로, R들)
    if not 사정들:
        return []
    갈림 = []
    구 = 관.get("구분") if isinstance(관.get("구분"), dict) else None
    if 구 and 사정들.get("구분별누계"):                        # S10R2-N2 — 구분마다 기대 G_k 와 지금 구분 율
        for k, 기 in 구.items():
            if not ("%s" % k).isdigit() or not isinstance(기, dict):
                continue
            s = int(k)
            값들 = 기.get("금액" if 기.get("경로") == "금액" else "율") or {}
            for 시, 값 in 값들.items():
                사 = (사정들["시나리오"].get(시) or {}).get("구분사정", {}).get(s)
                if not 사 or _수(값) is None:
                    continue
                r, G = 환산(기.get("경로"), 사, 값, 기.get("전년동기누계"))
                지 = 사.get("지금율")
                if r is None or 지 is None or abs(G - 지) > 환산허용:
                    갈림.append(("%s(구분 %d)" % (시, s), G if r is not None else None, 지))
        return 갈림
    전, _출 = 전년동기누계(가정, 가정경로)
    값들 = 관.get("금액" if 관.get("경로") == "금액" else "율") or {}
    for 시, 값 in 값들.items():
        if 시 not in 사정들["시나리오"] or _수(값) is None:
            continue
        r, G = 환산(관["경로"], 사정들["시나리오"][시], 값, 전)
        지 = 사정들["시나리오"][시]["지금율"]
        if r is None or 지 is None or abs(G - 지) > 환산허용:
            갈림.append((시, G if r is not None else None, 지))
    return 갈림


def 문항(가정, 가정경로=None, R들=None, 기준주당=None):
    """거친 바퀴 · 멈춤이 싣는 「잔여 기간 매출을 어떻게 잡나」 문항 재료 — 잔여 열 매출 ≤ 0 이거나 연환산비가 0.5~2.0 밖인 시나리오가 있을 때만.
    선택지 = 세 길(전년동기 — 지금 율 그대로 g 로 · 누계연장 g 0 · 금액 — 사람 입력)의 환산 율 · 잔여 매출 · 기준 주당가치. 없으면 None."""
    사정들 = 상황(가정, 가정경로, R들)
    if not 사정들:
        return None
    재 = 전년동기재료(가정, 가정경로)
    전, 전출 = 재["합계"], 재["출처"]
    걸린 = {시: d for 시, d in 사정들["시나리오"].items()
          if (d["잔여매출"] is not None and d["잔여매출"] <= 0) or any(v <= 0 for v in d["잔여구분"].values())
          or 연환산자(d, 전)[0]}
    if not 걸린:
        return None
    기 = 사정들["시나리오"]["기준"]
    선택 = []
    g기, g글 = 기본g(가정, 기, "기준")                      # S10R2-N3 — 스위치가 켜져 있으면 환산 율을 g 로 되쓰지 않는다
    전년동기이름 = "전년 동기 대비 — 지금 율을 반기 대 반기로" if g글 == "지금 율" else "전년 동기 대비 — %s 을 반기 대 반기로" % g글
    for 이름, 경, g in ((전년동기이름, "전년동기", g기 or 0.0), ("누계 추세 연장 — g 0", "누계연장", 0.0)):
        r, G = 환산(경, 기, g, 전)
        if r is None:
            선택.append({"이름": 이름, "경로": 경, "율": g, "값": None, "까닭": G})
            continue
        주 = None
        try:
            a, _G, _글 = 적기(가정, 경, {"기준": g}, 전, 전출, 사정들, 전년동기구분=재.get("구분") or None)
            주 = _엔진().계산(a, "기준")["요약"]["주당가치"]
        except Exception:                                     # noqa: BLE001
            주 = None
        선택.append({"이름": 이름, "경로": 경, "율": g, "값": G, "잔여매출": r, "주당": 주})
    넷 = 계절추세후보(가정, 가정경로)                          # 길 ④ — 파일 · 금액 후보 · 명령(이 도구가 받는 꼴)이 다 있을 때만 선택지 하나를 더한다
    if 넷 and 넷["금액"].get("기준") is not None and 넷.get("명령"):
        금기 = 넷["금액"]["기준"]
        r, G = 환산("금액", 기, 금기, 전)
        주 = None
        if r is not None:
            try:
                a, _G, _글 = 적기(가정, "금액", {"기준": 금기}, 전, 전출, 사정들, 전년동기구분=재.get("구분") or None)
                주 = _엔진().계산(a, "기준")["요약"]["주당가치"]
            except Exception:                                 # noqa: BLE001
                주 = None
        선택.append({"이름": "계절 · 추세 모형(길 ④ — 계절추세.json 중앙값)", "경로": "금액", "율": None, "값": G if r is not None else None,
                   "잔여매출": r, "주당": 주, "금액": 넷["금액"], "구간": 넷.get("구간")})
    선택.append({"이름": "금액 직접 — 사람 입력(가이던스 · 출시 · 수주 일정)", "경로": "금액", "값": None})
    시들 = sorted(걸린, key=시나리오목록.index)
    원인 = ("%s 의 잔여 기간 열(%s) 매출이 %s — 누계 실적 %s(%s)이 전년 회계연도 %s(%s)의 %.2f배다. 잔여 열 증가율은 그 회계연도 전체의 "
          "전년 대비라 회계연도 증가율이 %.1f%% 를 넘어야 잔여 매출이 0 보다 크다(지금 %s)" % (
              " · ".join(시들), 사정들["잔여"],
              " · ".join("%s %s" % (시, "{:,.0f}".format(걸린[시]["잔여매출"])) for 시 in 시들 if 걸린[시]["잔여매출"] is not None),
              "{:,.0f}".format(기["누계"] or 0), 사정들["누계"], "{:,.0f}".format(기["전년"] or 0), 사정들["FY끝"], 기["배수"] or 0,
              (기["손익분기율"] or 0) * 100,
              " · ".join("%s %.1f%%" % (시, (사정들["시나리오"][시]["지금율"] or 0) * 100) for 시 in 시나리오목록)))
    if 사정들.get("구분별누계"):                               # S10R2-N2 — 구분별 누계 회차는 구분마다 사정이 다르다
        조각 = []
        for s, 사 in sorted((기.get("구분사정") or {}).items()):
            if 사.get("경로") != "증가율":
                continue
            조각.append("구분 %d 누계 ÷ 전년 %s · 잔여 %s" % (s, ("%.2f배" % 사["배수"]) if 사.get("배수") is not None else "-",
                                                     "{:,.0f}".format(사["잔여매출"]) if 사.get("잔여매출") is not None else "-"))
        if 조각:
            원인 += ". 구분별 누계 회차라 구분마다 환산한다(%s) — `--구분 \"s=경로:율\"` 로 구분마다 길을 달리 줄 수 있다" % " · ".join(조각)
    return {"대상": ["잔여기간"], "이름": "잔여 기간(%s) 매출을 어떻게 잡나" % 사정들["잔여"], "종류": "잔여기간",
            "잠정값": 기["지금율"], "범위": None, "범위출처": "누계 실적 · 전년 회계연도 · 전년 동기(%s)" % 전출,
            "선택지": 선택, "안고르면": "답이 없으면 지금 율(회계연도 전년 대비) 그대로 간다 — 잔여 열 매출이 0 이하이면 자체검사 ⑮ 가 오류로 막는다",
            "뼈대": {"원인": 원인,
                   "문제여부": "잔여 열 매출 ≤ 0 은 절대 성립할 수 없는 수치다(값 전체가 무의미) · 연환산비가 자(%s) 밖이면 반기 수준이 잔여 기간에 꺾이거나 치솟는다는 가정이다" % 연환산자(기, 전)[2],
                   "선택지값": " · ".join("%s → 회계연도 %s · 잔여 %s · 기준 주당 %s" % (
                       x["이름"], ("%.1f%%" % (x["값"] * 100)) if x.get("값") is not None else "사람 입력",
                       "{:,.0f}".format(x["잔여매출"]) if x.get("잔여매출") is not None else "-",
                       "{:,.0f}".format(x["주당"]) if x.get("주당") is not None else "-") for x in 선택),
                   "안고르면": "지금 율 그대로 — 잔여 열 매출 ≤ 0 이면 자체검사 ⑮ 오류"},
            "답틀": {"명령": "python 스크립트/잔여기간.py 가정.json --경로 <전년동기|누계연장|금액> --율 \"비관=…,기준=…,낙관=…\" --적기" +
                           (" [--구분 \"s=경로:율\" …]" if 사정들.get("구분별누계") else "")}}


def 답적기(가정경로, 경로, 값들):
    """멈춤기록(`_raw/멈춤기록.json`)이 있으면 「잔여 기간」 문항의 답을 `답[]` 에 남긴다 — 넘긴 몫 장부가 그 문항을 닫는다(멈춤기록이 없으면 하지 않는다)."""
    p = os.path.join(os.path.dirname(os.path.abspath(가정경로)), "_raw", "멈춤기록.json")
    if not os.path.exists(p):
        return
    try:
        기록 = json.load(io.open(p, encoding="utf-8"))
    except (OSError, ValueError):
        return
    if not isinstance(기록, dict):
        return
    기록.setdefault("답", []).append({"시각": datetime.datetime.now().isoformat(timespec="seconds"), "대상": ["잔여기간"], "누가": "사람(잔여기간.py --적기)",
                                  "답": "경로 %s · %s" % (경로, " · ".join("%s %s" % kv for kv in sorted(값들.items())))})
    io.open(p, "w", encoding="utf-8").write(json.dumps(기록, ensure_ascii=False, indent=1))
    print("  멈춤기록에 잔여 기간 문항의 답을 남겼습니다 — %s" % p)


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False, description="잔여 기간 열 매출의 길을 환산한다(S10R1-N1)")
    ap.add_argument("가정")
    ap.add_argument("--경로", choices=경로목록, default=None)
    ap.add_argument("--율", default=None, help="전년동기 · 누계연장의 g — 「0.1」 또는 「비관=0,기준=0.1,낙관=0.2」")
    ap.add_argument("--금액", default=None, help="금액 길의 잔여 기간 매출(가정의 금액 단위) — 「기준=150000」 꼴")
    ap.add_argument("--구분", action="append", default=None, metavar="s[=경로:율]",
                    help="구분별 누계 회차에서 구분마다 길 · 율 — 「2」(--경로 --율 을 구분 2 에만) · 「2=전년동기:비관=0.1,기준=0.2,낙관=0.3」 · 「3=금액:기준=20000」. 여럿이면 되풀이(S10R2-N2)")
    ap.add_argument("--적기", action="store_true", help="가정 파일에 적는다(없으면 보기만)")
    a = ap.parse_args()
    try:
        가정 = json.load(io.open(a.가정, encoding="utf-8"))
    except (OSError, ValueError) as e:
        sys.stderr.write("가정을 못 읽었습니다: %s\n" % e)
        sys.exit(입력오류)
    사정들 = 상황(가정, a.가정)
    if not 사정들:
        print("잔여 기간 열이 없습니다(평가기준일 = 결산일) — 이 도구가 할 일이 없습니다")
        sys.exit(입력오류)
    밖 = [(s, 경) for s, 경, _l, _g in 구분들(가정) if 경 != "증가율"]
    재 = 전년동기재료(가정, a.가정)
    전, 전출 = 재["합계"], 재["출처"]
    if 재.get("멈춤") and a.경로 != "연간":                   # N6-b — A2 응답의 기준일이 가정 평가기준일과 다르면 멈춘다
        sys.stderr.write("%s\n" % 전출)
        sys.exit(입력오류)
    print("잔여 기간 %s · 누계 %s(%d개월) · 전년 회계연도 %s · 전년 동기 누계 %s(%s)" % (
        사정들["잔여"], 사정들["누계"], 사정들["누계개월"], 사정들["FY끝"], "{:,.0f}".format(전) if 전 is not None else "없음", 전출))
    if 사정들.get("구분별누계"):
        print("  구분별 누계 회차 — 엔진이 구분마다 「연간 기준 − 그 구분 누계」를 뺀다 · 환산도 구분마다(S10R2-N2). 구분별 전년 동기 %s" % (
            ("A2 원천 %s" % " · ".join("%d" % s for s in sorted(재["구분"]))) if 재.get("구분") else "없음 — 합계 × 전년 매출 비중으로 가른다"))
    if 밖:
        print("  수준 · 합계 경로 구분 %s — 잔여 기간은 수준 값이 정한다(환산하지 않고 건너뛴다)" % " · ".join("%d(%s)" % x for x in 밖))
    음 = False
    for 시 in 시나리오목록:
        d = 사정들["시나리오"][시]
        음 = 음 or (d["잔여매출"] is not None and d["잔여매출"] <= 0) or any(v <= 0 for v in d["잔여구분"].values())
        _밖, _자, _자글 = 연환산자(d, 전)
        print("  %s  누계 %s · 전년 %s(누계 ÷ 전년 %.2f배) · 회계연도 율 %s → 연간 기준 %s · 잔여 매출 %s%s · 연환산비 %s%s" % (
            시, "{:,.0f}".format(d["누계"] or 0), "{:,.0f}".format(d["전년"] or 0), d["배수"] or 0,
            "%.1f%%" % ((d["지금율"] or 0) * 100), "{:,.0f}".format(d["연간기준"]), "{:,.0f}".format(d["잔여매출"] or 0),
            "  ← 0 이하(손익분기 율 %.1f%%)" % ((d["손익분기율"] or 0) * 100) if (d["잔여매출"] or 0) <= 0 else "",
            "%.2f" % d["연환산비"] if d["연환산비"] is not None else "-", ("  ← 자 밖(%s)" % _자글) if _밖 else ""))
        if 사정들.get("구분별누계"):
            for s, 사 in sorted((d.get("구분사정") or {}).items()):
                if 사.get("경로") != "증가율" or 사.get("누계") is None:
                    continue
                print("      구분 %d  누계 %s · 전년 %s(%s) · 지금 율 %s · 잔여 %s%s" % (
                    s, "{:,.0f}".format(사["누계"] or 0), "{:,.0f}".format(사["전년"] or 0),
                    ("%.2f배" % 사["배수"]) if 사.get("배수") is not None else "-",
                    ("%.1f%%" % (사["지금율"] * 100)) if 사.get("지금율") is not None else "-",
                    "{:,.0f}".format(사["잔여매출"]) if 사.get("잔여매출") is not None else "-",
                    "  ← 0 이하(손익분기 율 %.1f%%)" % ((사.get("손익분기율") or 0) * 100) if (사.get("잔여매출") is not None and 사["잔여매출"] <= 0) else ""))
    if a.경로 is None and not a.구분:
        for 경, g in (("전년동기", None), ("누계연장", 0.0)):
            줄 = []
            for 시 in 시나리오목록:
                d = 사정들["시나리오"][시]
                gg = 기본g(가정, d, 시)[0] if g is None else g          # S10R2-N3 — 켜진 스위치의 환산 율을 g 로 되쓰지 않는다
                r, G = 환산(경, d, gg or 0.0, 전)
                줄.append("%s %s" % (시, ("잔여 %s → 회계연도 %.1f%%" % ("{:,.0f}".format(r), G * 100)) if r is not None else G))
            print("  길 %s(g = %s) — %s" % (경, 기본g(가정, 사정들["시나리오"]["기준"], "기준")[1] if g is None else g, " · ".join(줄)))
        넷 = 계절추세후보(가정, a.가정)                          # 길 ④ — 계절추세.json 이 있을 때만 한 줄
        if 넷 and 넷["금액"]:
            줄 = []
            for 시 in 시나리오목록:
                if 시 not in 넷["금액"]:
                    continue
                r, G = 환산("금액", 사정들["시나리오"][시], 넷["금액"][시], 전)
                줄.append("%s %s" % (시, ("잔여 %s → 회계연도 %.1f%%" % ("{:,.0f}".format(r), G * 100)) if r is not None else G))
            print("  길 ④ 계절추세(%s) — %s%s%s" % (
                "후보 — 고르는 것은 사람" if 넷.get("명령") else "대조값 — 이 회차는 금액 길로 못 적는다",
                " · ".join(줄), ("  90%% [%s]" % ", ".join("{:,.0f}".format(x) for x in 넷["구간"])) if isinstance(넷.get("구간"), list) and len(넷["구간"]) == 2 else "",
                (" · --경로 금액 --금액 \"%s\"" % ",".join("%s=%.0f" % (시, 넷["금액"][시]) for 시 in 시나리오목록 if 시 in 넷["금액"]))
                if 넷.get("명령") else " · %s" % (넷.get("명령까닭") or "명령 없음")))
        elif 넷:
            print("  길 ④ 계절추세 — 후보 없음: %s" % 넷.get("폴백"))
        켜 = _켜짐(가정)
        if 켜:
            print("  스위치 켜짐 — 관측.잔여기간(경로 %s · 환산 %s) · 지금 율은 환산 율이다. 끄기: --경로 연간 --적기(원래율 %s)" % (
                켜.get("경로"), 켜.get("환산일") or 켜.get("시각") or "-", "있음" if 켜.get("원래율") else "없음 — 되돌릴 재료가 없다"))
        print("  고르는 법 — --경로 전년동기 | 누계연장 | 금액 · --율 / --금액 · --적기(가정_스키마 「잔여 기간 열」)")
        sys.exit(발견 if 음 else 통과)
    if a.경로 == "연간":                                    # S10R2-N3 — 스위치 끔 = 환산 전 율로 되돌린다(새 기능 끔 = 옛 값)
        새, 글, 됨 = 되돌리기(가정)
        for x in 글:
            print("  " + x)
        if not 됨:
            sys.exit(발견)
        if 새 != 가정:
            뒤 = 상황(새, a.가정)
            for 시 in 시나리오목록:
                d = 뒤["시나리오"][시]
                print("  → %s 잔여 매출 %s · 회계연도 %.1f%%%s" % (시, "{:,.0f}".format(d["잔여매출"] or 0), (d["지금율"] or 0) * 100,
                                                     "  ← 0 이하(자체검사 ⑮ 오류 — 옛 판 그대로)" if (d["잔여매출"] or 0) <= 0 else ""))
            if a.적기:
                io.open(a.가정, "w", encoding="utf-8").write(json.dumps(새, ensure_ascii=False, indent=1))
                print("적었습니다 — %s" % a.가정)
            else:
                print("보기만 했습니다(--적기 로 적는다)")
        sys.exit(통과)
    try:
        값들 = _율읽기(a.금액 if a.경로 == "금액" else a.율, "--금액" if a.경로 == "금액" else "--율") if a.경로 else None
        구분지정 = _구분읽기(a.구분, a.경로, 값들) if a.구분 else None
    except ValueError as e:
        sys.stderr.write("%s\n" % e)
        sys.exit(입력오류)
    if not 값들 and not 구분지정:
        sys.stderr.write("--%s 가 없습니다\n" % ("금액" if a.경로 == "금액" else "율"))
        sys.exit(입력오류)
    try:
        새, G들, 글 = 적기(가정, a.경로, 값들 or {}, 전, 전출 if 전 is not None else None, 사정들,
                        구분지정=구분지정, 전년동기구분=재.get("구분") or None)
    except ValueError as e:
        sys.stderr.write("환산 못 함 — %s\n" % e)
        sys.exit(입력오류)
    for x in 글:
        print("  " + x)
    뒤 = 상황(새, a.가정)
    남 = [시 for 시, d in 뒤["시나리오"].items() if (d["잔여매출"] or 0) <= 0 or any(v <= 0 for v in d["잔여구분"].values())]
    for 시 in 시나리오목록:
        d = 뒤["시나리오"][시]
        print("  → %s 잔여 매출 %s · 회계연도 %.1f%% · 연환산비 %s" % (시, "{:,.0f}".format(d["잔여매출"] or 0), (d["지금율"] or 0) * 100,
                                                       "%.2f" % d["연환산비"] if d["연환산비"] is not None else "-"))
    if a.적기:
        io.open(a.가정, "w", encoding="utf-8").write(json.dumps(새, ensure_ascii=False, indent=1))
        print("적었습니다 — %s" % a.가정)
        답적기(a.가정, (새.get("관측") or {}).get("잔여기간", {}).get("경로") or a.경로,
            값들 or {("구분 %d" % k): "%s:%s" % (v[0], v[1]) for k, v in sorted((구분지정 or {}).items())})
    else:
        print("보기만 했습니다(--적기 로 적는다)")
    sys.exit(발견 if 남 else 통과)


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""**외부 제약 형식 검증** — D 갈래 산출물과 가정 `제약` 블록이 받는 쪽이 읽을 수 있는 모양인지 본다.

    python 스크립트/외부제약검증.py                                  # _raw/외부제약.json
    python 스크립트/외부제약검증.py _raw/외부제약.json 가정_회사.json   # 둘 다(가정은 `제약` 블록만)

종료코드 — 0 통과(경고는 있어도 됨) · 1 형식 위반 · 2 파일 없음·JSON 깨짐.

왜 있나 — **형식이 틀린 제약은 조용히 죽는다.** 모순장부 M-08 은 `경로` 의 마지막 값이 0 인지로
법령의 끝을 알고, 자체검사 ㉟ 는 `영구화금지` 가 참인지로 영구 열을 잰다. 그런데 D 갈래가
`경로` 를 문장으로(「확인 불가 — 요약상 일몰일 기재 없음」), `영구화금지` 를 「미확정 — …」 문자열로
적어도 아무것도 울지 않았다. 문자열은 참(truthy)이라 어느 자리는 참으로, 어느 자리는 거짓으로
읽혔고, 레터 부록 I 는 dict 를 기대하다 죽었다(세일즈포스 2026-09-13 실측).
펄어비스 회차는 본선이 붓다가 `경로` 를 `{"비고": "…"}` 로 바꿔 넣었는데 이것도 연도 키가 아니라
받는 쪽에는 똑같이 빈 경로다.

형식 — 위반(rc 1)
  제약                    dict. 블록 `법령`·`산업상한`·`규제가격`·`재무약정`·`원가` 는 list[dict]
  법령[].영구화금지         **true/false 만.** 모르면 문자열로 적지 않는다 — 갈래 프롬프트의 기본값을 따른다
  법령[].경로              **{연도: 잔존비율} dict 만.** 연도는 네 자리, 잔존비율은 0~1 숫자.
                          경로가 없는 규칙(상시 행위 규제 등)은 `{}` 로 두고 사유는 `경로_비고` 에 쓴다
  영구화금지 true          경로가 비면 안 된다(끝이 어디인지가 그 판정의 근거다) —
                          단 `영구화금지_근거`(미확정 기본값)가 있으면 경고로 내린다
  산업상한[].전망           있으면 {연도: 숫자} dict
  원가[](2026-10-16 — 원가 · 투자 쪽 울타리: 전기요금 · 배출권 · 최저임금 · 근로시간 · 설비 의무 투자 · 상각 한도)
                          `경로` {연도: 숫자}(비율이나 금액 — 0~1 로 묶지 않는다) · `영구화금지` true/false **필수** ·
                          true 면 경로가 비면 안 된다(`영구화금지_근거` 가 없으면) ·
                          `닿는_원가줄` 은 원가줄1~7 · 인건비 · 투자 · 법인세 가운데 하나
                          (손으로 JSON 을 쓰지 말고 `외부제약작성.py` 로 블록마다 넣는다 — 검증을 통과해야 쓴다)
  [].원문인용 · [].원문접수(2026-10-21 — 선택 칸, 다섯 블록 모두) 원문인용은 원문을 글자 그대로 옮긴 글(1,200자 안) ·
                          원문접수는 DART 접수번호 14자리 · SEC accession · 미국 원문 이름(10K_YYYYMM). 인용이 원문에 정말 있는지는 원문이 있어야 보므로
                          `조항추출.py --대조` 가 본다(여기서는 꼴만)
형식 — 경고(rc 0)
  영구화금지 true 인데 경로 마지막 값이 0 이 아님 · 적용행이 비었는데 반영 표시가 없음 ·
  산업상한[].값 이 문자열 · 재무약정[].닿는_행 이 list 가 아님 · 모르는 블록 이름 ·
  재무약정[] 항목에 원문인용이 없음(2026-10-21 — 조항은 원문 문단을 옮겨 단다)
"""
from __future__ import annotations

import io
import json
import os
import re
import sys
from json.decoder import scanstring

sys.stdout.reconfigure(encoding="utf-8")

블록 = ("법령", "산업상한", "규제가격", "재무약정", "원가")
닿는자리 = re.compile(r"원가줄[1-7]|인건비|투자|법인세")
_수 = re.compile(r"-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][-+]?\d+)?")
_공백 = re.compile(r"[ \t\n\r]*")


# ── 줄 번호를 아는 JSON 읽기 — 경로(키 사슬) → 줄 번호 ─────────────────────
def 줄표(글):
    """값은 json.loads 로 따로 읽고, 여기서는 **키 사슬마다 그 키가 시작하는 줄**만 모은다."""
    표 = {}
    줄시작 = [0]
    for m in re.finditer("\n", 글):
        줄시작.append(m.end())

    def 줄(pos):
        lo, hi = 0, len(줄시작) - 1
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if 줄시작[mid] <= pos:
                lo = mid
            else:
                hi = mid - 1
        return lo + 1

    def ws(i):
        return _공백.match(글, i).end()

    def 값(i, 사슬):
        i = ws(i)
        표.setdefault(사슬, 줄(i))
        c = 글[i]
        if c == "{":
            i = ws(i + 1)
            if 글[i] == "}":
                return i + 1
            while True:
                i = ws(i)
                k, j = scanstring(글, i + 1)
                키줄 = 줄(i)
                i = ws(j)
                i = ws(i + 1)                                  # ':'
                하위 = "%s.%s" % (사슬, k) if 사슬 else k
                표[하위] = 키줄
                i = 값(i, 하위)
                표[하위] = 키줄
                i = ws(i)
                if 글[i] == ",":
                    i += 1
                    continue
                return i + 1                                   # '}'
        if c == "[":
            i = ws(i + 1)
            if 글[i] == "]":
                return i + 1
            n = 0
            while True:
                i = 값(i, "%s[%d]" % (사슬, n))
                n += 1
                i = ws(i)
                if 글[i] == ",":
                    i += 1
                    continue
                return i + 1
        if c == '"':
            return scanstring(글, i + 1)[1]
        for lit in ("true", "false", "null"):
            if 글.startswith(lit, i):
                return i + len(lit)
        m = _수.match(글, i)
        return m.end()

    try:
        값(0, "")
    except Exception:                                            # noqa: BLE001 — 줄 번호는 보조다
        pass
    return 표


def _숫자(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _짧게(v, n=60):
    s = json.dumps(v, ensure_ascii=False) if not isinstance(v, str) else v
    return s if len(s) <= n else s[:n] + "…"


def 검사(제약, 머리="제약"):
    """(위반[], 경고[]) — 각 원소는 (키 사슬, 문장)."""
    위반, 경고 = [], []
    if not isinstance(제약, dict):
        위반.append((머리, "`제약` 이 dict 가 아니다 (받은 값: %s)" % _짧게(제약)))
        return 위반, 경고
    for k, v in 제약.items():
        if k in 블록:
            continue
        if k.endswith("_비고") or k in ("비고",):
            continue
        경고.append(("%s.%s" % (머리, k), "모르는 블록 이름 — 받는 쪽은 %s 만 읽는다" % "·".join(블록)))
    for b in 블록:
        벌 = 제약.get(b)
        사 = "%s.%s" % (머리, b)
        if 벌 is None:
            continue
        if not isinstance(벌, list):
            위반.append((사, "list 여야 한다. 해당 없음이면 `[]` 로 두고 사유는 `%s_비고` 에 쓴다 (받은 값: %s)"
                        % (b, _짧게(벌))))
            continue
        for i, x in enumerate(벌):
            s = "%s[%d]" % (사, i)
            if not isinstance(x, dict):
                위반.append((s, "항목이 dict 가 아니다 (받은 값: %s)" % _짧게(x)))
                continue
            _인용(x, s, b, 위반, 경고)
            if b == "법령":
                _법령(x, s, 위반, 경고)
            elif b == "산업상한":
                전 = x.get("전망")
                if 전 is not None and not isinstance(전, dict):
                    위반.append((s + ".전망", "{연도: 숫자} dict 여야 한다 (받은 값: %s)" % _짧게(전)))
                elif isinstance(전, dict):
                    for yk, yv in 전.items():
                        if not re.fullmatch(r"\d{4}", str(yk)) or not (_숫자(yv) or yv is None):
                            위반.append((s + ".전망.%s" % yk, "연도 네 자리 키와 숫자 값이어야 한다 (받은 값: %s)" % _짧게(yv)))
                if isinstance(x.get("값"), str):
                    경고.append((s + ".값", "숫자가 아니라 문자열이다 — ⑨ 가 상한으로 못 잰다 (받은 값: %s)" % _짧게(x["값"])))
            elif b == "원가":
                _원가(x, s, 위반, 경고)
            elif b == "재무약정":
                if "닿는_행" in x and not isinstance(x.get("닿는_행"), list):
                    경고.append((s + ".닿는_행", "list 가 아니다 (받은 값: %s)" % _짧게(x.get("닿는_행"))))
    return 위반, 경고


def _인용(x, s, b, 위반, 경고):
    """선택 칸 `원문인용` · `원문접수`(2026-10-21 — `조항추출.py` 가 후보로 낸 원문 문단을 D 가 옮겨 단 것). 꼴만 본다 —
    인용이 원문에 글자 그대로 있는지는 원문이 있어야 볼 수 있어 `조항추출.py --대조` 가 본다."""
    인 = x.get("원문인용")
    if 인 is not None and (not isinstance(인, str) or not 인.strip() or len(인) > 1200):
        위반.append((s + ".원문인용", "원문을 글자 그대로 옮긴 글(1,200자 안)이어야 한다 (받은 값: %s)" % _짧게(인)))
    접 = x.get("원문접수")
    # DART 접수번호 14자리 · SEC accession(0000764180-26-000012 · 대시 없는 18자리) · 미국 원문 이름(10K_YYYYMM) — 2026-10-23(미국 회사의 재무약정 인용)
    if 접 is not None and not re.fullmatch(r"\d{14}|\d{10}-\d{2}-\d{6}|\d{18}|10[KQ]_\d{4,6}", str(접)):
        위반.append((s + ".원문접수", "DART 접수번호 14자리 · SEC accession(0000000000-00-000000) · 미국 원문 이름(10K_YYYYMM)이어야 한다 (받은 값: %s)" % _짧게(접)))
    if b == "재무약정" and 인 is None:
        경고.append((s, "`원문인용` 이 없다 — 재무약정은 원문 조항을 옮겨 단다(`조항추출.py` 후보 → `--대조`)"))


def _원가(x, s, 위반, 경고):
    """제약.원가[] — 원가 · 투자 쪽 울타리. 경로 값은 비율이나 금액이라 0~1 로 묶지 않는다.
    **`영구화금지` 는 법령과 같이 필수다**(2026-10-16, S1 리뷰 — 종전에는 빠져도 위반이 아니라 기한이 정해진 의무 투자가 영구 열에
    남아도 ㉟ · M-08 이 재지 못했다). true 면 끝나는 해가 경로에 있어야 하고(또는 `영구화금지_근거`), 적용행이 있어야 영구 열을 잰다."""
    영 = x.get("영구화금지", "__없음__")
    if 영 == "__없음__":
        위반.append((s, "`영구화금지` 가 없다 — true/false 로 적는다(기한이 있는 돈이면 true)"))
    elif not isinstance(영, bool):
        위반.append((s + ".영구화금지", "true/false 가 아니다 (받은 값: %s)" % _짧게(영)))
    경 = x.get("경로", "__없음__")
    if 영 is True and isinstance(경, dict):
        if not 경 and not str(x.get("영구화금지_근거") or "").strip():
            위반.append((s + ".경로", "`영구화금지: true` 인데 경로가 비었다 — 끝나는 해가 그 판정의 근거다. 일정을 확정 못 했으면 "
                                     "`영구화금지_근거` 에 그렇게 적는다"))
        if not str(x.get("적용행") or "").strip():
            경고.append((s + ".적용행", "`영구화금지: true` 인데 적용행이 없다 — ㉟ · M-08 이 영구 열을 재지 못한다(가정 번호나 "
                                       "「한시적현금흐름」을 적는다)"))
    if 경 == "__없음__":
        위반.append((s, "`경로` 가 없다 — {연도: 비율 또는 금액} dict, 경로 없는 규칙이면 `{}` + `경로_비고`"))
    elif not isinstance(경, dict):
        위반.append((s + ".경로", "{연도: 숫자} dict 가 아니다 (받은 값: %s)" % _짧게(경)))
    else:
        for yk, yv in 경.items():
            if not re.fullmatch(r"\d{4}", str(yk)):
                위반.append((s + ".경로.%s" % yk, "연도 네 자리 키가 아니다 (받은 값: %s)" % _짧게(yv)))
            elif not _숫자(yv):
                위반.append((s + ".경로.%s" % yk, "숫자가 아니다 (받은 값: %s)" % _짧게(yv)))
    닿 = x.get("닿는_원가줄")
    if not isinstance(닿, str) or not 닿는자리.fullmatch(닿.strip()):
        위반.append((s + ".닿는_원가줄", "원가줄1~7 · 인건비 · 투자 · 법인세 가운데 하나여야 한다 (받은 값: %s)" % _짧게(닿)))
    if not str(x.get("조문") or x.get("출처") or "").strip():
        경고.append((s, "조문 · 출처가 비었다 — 울타리의 근거를 되짚을 수 없다"))


def _법령(x, s, 위반, 경고):
    영 = x.get("영구화금지", "__없음__")
    if 영 == "__없음__":
        위반.append((s, "`영구화금지` 가 없다 — true/false 로 적는다"))
        영 = None
    elif not isinstance(영, bool):
        위반.append((s + ".영구화금지",
                    "true/false 가 아니다 (받은 값: %s). 문자열은 받는 쪽에서 참으로도 거짓으로도 읽힌다 — "
                    "확정 못 하면 D 갈래 규약의 기본값(true + `영구화금지_근거`)으로 적는다" % _짧게(영)))
        영 = None
    경 = x.get("경로", "__없음__")
    if 경 == "__없음__":
        위반.append((s, "`경로` 가 없다 — {연도: 잔존비율} dict, 경로 없는 규칙이면 `{}` + `경로_비고`"))
        return
    if not isinstance(경, dict):
        위반.append((s + ".경로",
                    "{연도: 잔존비율(0~1 숫자)} dict 가 아니다 (받은 값: %s). 문장은 `경로_비고` 로 옮기고 "
                    "경로 없는 규칙이면 `{}` 로 둔다" % _짧게(경)))
        return
    해들 = []
    for yk, yv in 경.items():
        if not re.fullmatch(r"\d{4}", str(yk)):
            위반.append((s + ".경로.%s" % yk,
                        "연도 네 자리 키가 아니다 — 설명은 `경로_비고` 로 옮긴다 (받은 값: %s)" % _짧게(yv)))
            continue
        if not _숫자(yv):
            위반.append((s + ".경로.%s" % yk,
                        "잔존비율이 숫자가 아니다 (받은 값: %s) — 75%% 는 0.75 로" % _짧게(yv)))
            continue
        if not (0.0 <= float(yv) <= 1.0):
            위반.append((s + ".경로.%s" % yk, "잔존비율은 0~1 이다 (받은 값: %s)" % yv))
            continue
        해들.append((int(yk), float(yv)))
    if 영 is True:
        if not 경 and str(x.get("영구화금지_근거") or "").strip():
            경고.append((s + ".경로", "`영구화금지: true`(미확정 기본값)인데 경로가 비었다 — M-08 은 이 법령의 영구 열을 "
                                     "못 잰다. 자체검사 ㉟ 가 적용행 영구 열을 직접 잰다"))
        elif not 경:
            위반.append((s + ".경로", "`영구화금지: true` 인데 경로가 비었다 — 끝나는 해가 어디인지가 그 판정의 근거다. "
                                     "일정을 확정 못 했으면 `영구화금지_근거` 에 그렇게 적는다"))
        elif 해들 and sorted(해들)[-1][1] != 0.0:
            경고.append((s + ".경로", "`영구화금지: true` 인데 마지막 해(%d)의 잔존비율이 %s — 0 이 아니면 "
                                     "모순장부 M-08 이 영구 열을 재지 않는다" % sorted(해들)[-1]))
        if not str(x.get("적용행") or "").strip() and x.get("반영") is not False:
            경고.append((s + ".적용행", "적용행이 비었다 — 값에 안 실은 제약이면 `반영: false` 와 사유를 적는다"))


def 파일검사(p):
    """(위반[], 경고[], 줄표) — 파일이 외부제약.json 이든 가정 JSON 이든 최상위 `제약` 을 본다."""
    글 = io.open(p, encoding="utf-8-sig").read()
    j = json.loads(글)
    표 = 줄표(글)
    if not isinstance(j, dict):
        return [("", "최상위가 dict 가 아니다")], [], 표
    if "제약" not in j:
        if os.path.basename(p).startswith("외부제약"):
            return [("제약", "`제약` 블록이 없다 — 해당 없음이어도 블록들을 `[]` 로 두고 `_비고` 에 사유를 쓴다")], [], 표
        return [], [("제약", "가정에 `제약` 블록이 없다(선택 칸) — 외부 제약이 없는 회사면 괜찮다")], 표
    위, 경 = 검사(j["제약"])
    return 위, 경, 표


def main(argv=None):
    인자 = list(sys.argv[1:] if argv is None else argv)
    if not 인자:
        인자 = [os.path.join("_raw", "외부제약.json")]
    rc = 0
    for p in 인자:
        print("── 외부 제약 형식 검증 — %s ──" % p)
        if not os.path.exists(p):
            print("  파일이 없습니다")
            rc = max(rc, 2)
            continue
        try:
            위, 경, 표 = 파일검사(p)
        except ValueError as e:
            print("  JSON 을 읽지 못했습니다: %s" % e)
            rc = max(rc, 2)
            continue

        def 찍(쌍, 딱지):
            사슬, 말 = 쌍
            줄 = 표.get(사슬)
            while 줄 is None and 사슬:
                사슬 = re.sub(r"(\.[^.\[]+|\[\d+\])$", "", 사슬) if re.search(r"(\.[^.\[]+|\[\d+\])$", 사슬) else ""
                줄 = 표.get(사슬)
            print("  %s L%-5s %s — %s" % (딱지, 줄 if 줄 else "?", 쌍[0], 말))

        for x in 위:
            찍(x, "위반")
        for x in 경:
            찍(x, "경고")
        print("  → 위반 %d · 경고 %d%s" % (len(위), len(경), "" if 위 else " · 통과"))
        if 위:
            rc = max(rc, 1)
    if rc == 1:
        print("\n**형식 위반이 있습니다.** 붓기·레터가 받기 전에 고치십시오 — 규약은 .claude/갈래/D_외부제약.md 「산출물」 절")
    return rc


if __name__ == "__main__":
    sys.exit(main())

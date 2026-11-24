# -*- coding: utf-8 -*-
"""회차실행 — 회사 폴더 하나에서 결정적 사슬(도구만 도는 단계)을 단계 이름으로 고르거나 차례로 돈다.

판단 구간(A2 보정 · 조사 갈래 · 가정 판단 · 레터 원고 · 교열 검토 · 편집 · 검토 의견)은 사람 · 에이전트가 한다. 이 실행기는 그 사이를 잇는 도구 단계만
돌리고, 단계마다 무엇을 넣어 무엇이 나왔는지를 회사 폴더의 `진행판.json` 에 적는다. 이 실행기는 값을 정하지 않는다 — 키트 도구를 부를 뿐이다.

    python -X utf8 스크립트/회차실행.py                       # 기본 사슬을 차례로(끝난 단계는 건너뛴다)
    python -X utf8 스크립트/회차실행.py --단계 엔진,짓기,붓기   # 고른 단계만(사슬 차례로)
    python -X utf8 스크립트/회차실행.py --부터 마감 --까지 게이트
    python -X utf8 스크립트/회차실행.py --다시 원천             # 판단 산출(A2 보정본 따위)을 알고 덮는다 — 이 이름을 준 단계만
    python -X utf8 스크립트/회차실행.py --새로                  # 같은 입력이어도 다시 돈다(판단 산출은 여전히 덮지 않는다)
    python -X utf8 스크립트/회차실행.py --보기                  # 돌지 않고 무엇을 할지만
    python -X utf8 스크립트/회차실행.py 목록 | 상태
    python -X utf8 스크립트/회차실행.py 기록 --단계 가정 --토큰 120000 --호출 4 --초 900 --기록자 본선
    python -X utf8 스크립트/회차실행.py --기록 레터원고 --토큰 … --호출 … --초 … --기록자 …   # 같은 일(깃발 꼴)
    python -X utf8 스크립트/회차실행.py --꾸러미                # 꾸러미 내보내기 자리(미구현 — 종료 코드 3)

인자 — 날짜는 박지 않는다. 평가기준일 T · 재무기준일 F · 결산월은 `--평가기준일` · `--재무기준일` · `--결산월` 이 먼저이고, 없으면 가정 파일
(`기준일.py` — 메타.평가기준일 · 메타.재무기준일(없으면 F = T) · 기간.결산월)에서 읽는다. 인자와 가정이 다르면 인자를 쓰고 경보한다.
관할은 `--국가 KR|US`(또는 `--미국`)가 먼저이고, 없으면 가정의 메타.표시통화(KRW → KR · USD → US), 그다음 `_raw/companyfacts.json` 유무.
가정 파일은 `--가정` 이 먼저이고, 없으면 폴더의 `가정_*.json` 하나(예시 · 템플릿은 뺀다). 여럿이면 `--가정` 을 묻는다.

규칙
  · 건너뛰기 — 같은 입력 해시로 끝난(통과 · 허용된 발견) 단계는 산출이 남아 있으면 다시 돌지 않는다. 입력 해시는 입력 파일 · 도구 파일 ·
    키트 판(`버전.json`) · 명령 인자를 묶는다. 가정 파일은 단계마다 「값」(엔진이 읽는 값만 — `가정해시.값`) 또는 「전체」로 잰다.
    `_raw/` 를 통째로 읽는 단계는 `_raw/` 맨 위 파일을 모두 재되, 이 단계와 뒤 단계가 쓰는 파일(선언 · 지난 실행에서 실측한 부산출)은 뺀다.
  · 멈춤 — 단계의 종료 코드가 허용 밖이면 그 자리에서 멈추고 그 코드를 돌려준다. 검사 도구의 「발견」(1)은 단계마다 허용을 정했다
    (자체검사 · 대조 · 넘긴 몫처럼 게이트가 다시 보는 것). `--엄격` 이면 0 만 허용한다.
  · 덮기 금지 — 판단 산출(A2 보정본 · 동인 원천 · 매출 구분 판정 · 동인 진단 · 레터 편집본)은 이 실행기가 지은 그대로가 아니면
    (기록이 없거나 해시가 바뀌었으면) 돌지 않고 「보호」로 적는다. 덮으려면 `--다시 <단계>` 를 준다. 가정 파일 · 레터 원고 묶음 ·
    편집 목록은 어느 단계의 산출도 아니다(시작할 때 점검한다).
  · 잠금 — 엑셀 · 워크북 파일을 쓰는 단계(짓기 · 붓기 · 마감 · 대조)는 기계 하나에서 한 번에 하나만 돈다(잠금 파일 — `DCF_회차잠금` 폴더 ·
    없으면 공용 캐시 · 없으면 사용자 임시 폴더). 같은 회사 폴더에서 실행기 둘이 함께 돌지 않는다.
  · 생성기 판 — 짓기를 고르면 먼저 생성기를 본다(`생성기점검`). 생성기 폴더의 표지 `_본체판.json`(본체에서 갈아 끼운 도구가 남김)의
    본체와 코드 지문이 다르거나, 생성기와 키트가 이 가정에서 낸 구조 지문이 다르면 경보한다(짓기가 rc 1 로 멈출 자리를 미리 알린다).
  · 판단 구간 계측 —`진행판.json` 의 `판단구간[]` 에 단계 · 토큰 · 호출 · 초 · 기록자를 바깥(본선 · 워크플로)이 `기록` 으로 적는다.

종료 코드 — 0 통과 · 1 발견(허용 밖) · 2 입력 오류 · 3 미구현. 멈춘 단계의 종료 코드를 그대로 돌려준다.
회사 · 업종 이름은 이 도구에 없다(범용).
"""
from __future__ import annotations

import argparse
import datetime
import glob
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import time

try:
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)   # 1.1.10 — 줄마다 내보낸다(백그라운드 로그가 버퍼에 쌓여 사슬이 멈춘 듯 보였다)
    sys.stderr.reconfigure(encoding="utf-8", line_buffering=True)
except Exception:                                    # noqa: BLE001
    pass

여기 = os.path.dirname(os.path.abspath(__file__))
if 여기 not in sys.path:
    sys.path.insert(0, 여기)

형식 = "회차실행 진행판 1"
판이름 = "진행판.json"
작업곳 = "_회차실행"
통과, 발견, 입력오류, 미구현 = 0, 1, 2, 3
끝난상태 = ("통과", "발견")
이력상한 = 500
잠금파일 = "ADDER_엑셀.lock"


# ══════════════════════════════════════════════════════════ 작은 도구

def _지금():
    return datetime.datetime.now().replace(microsecond=0).isoformat()


def _쓰기(p, d):
    """JSON 을 임시 파일에 쓴 뒤 바꿔 넣는다(반쯤 쓴 파일이 남지 않게)."""
    os.makedirs(os.path.dirname(os.path.abspath(p)), exist_ok=True)
    t = p + ".쓰는중"
    with io.open(t, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1, default=str)
    os.replace(t, p)


def _읽기(p, 기본=None):
    try:
        with io.open(p, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return 기본


def _sha(b):
    return hashlib.sha256(b).hexdigest()


_해시기억 = {}


def 파일해시(p):
    """파일 sha256(없으면 None). 폴더면 그 안 파일(상대 경로 · 해시)의 해시. 같은 실행 안에서는 (크기 · 시각)이 같으면 다시 재지 않는다."""
    if os.path.isdir(p):
        줄 = []
        for 뿌리, _d, fs in os.walk(p):
            for f in sorted(fs):
                q = os.path.join(뿌리, f)
                줄.append("%s=%s" % (os.path.relpath(q, p).replace("\\", "/"), 파일해시(q)))
        return _sha("\n".join(sorted(줄)).encode("utf-8"))
    try:
        st = os.stat(p)
    except OSError:
        return None
    열쇠 = (os.path.abspath(p), st.st_size, st.st_mtime_ns)
    if 열쇠 in _해시기억:
        return _해시기억[열쇠]
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for 조각 in iter(lambda: f.read(1 << 20), b""):
            h.update(조각)
    _해시기억[열쇠] = h.hexdigest()
    return _해시기억[열쇠]


def 가정해시(p, 모드):
    """가정 파일 해시 — 「값」 은 엔진이 읽지 않는 글 블록을 뺀 해시(`가정해시.값`), 「전체」 는 파일 전부."""
    g = _읽기(p)
    if g is None:
        return 파일해시(p)
    if 모드 in ("값", "값검토"):
        try:
            import 가정해시 as _가                                     # noqa: PLC0415
            h = "값:" + _가.값(g)
            if 모드 == "값검토":                                       # 1.1.4(P-08) — 붓기 · 마감은 검토의견을 15번에 싣는다: 의견만 고쳐도 다시 돈다
                h += "|검토:" + _sha(json.dumps(g.get("검토의견"), sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
            return h
        except ImportError:                                            # 옛 키트 사본 — 값 해시가 없으면 전체로(더 자주 돌 뿐 틀리지 않는다)
            pass
    return "전체:" + _sha(json.dumps(g, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))


def 끝줄(글):
    줄 = [x for x in 글.splitlines() if x.strip()]
    return (줄[-1].strip() if 줄 else "")[:220]


def 안전이름(s):
    return re.sub(r'[\\/:*?"<>|\s]+', "_", ("%s" % s).strip()) or "회사"


# ══════════════════════════════════════════════════════════ 잠금

class 잠금시간초과(Exception):
    pass


class 잠금:
    """파일 잠금 — 운영체제의 바이트 잠금이라 잡은 프로세스가 죽으면 저절로 풀린다(낡은 잠금 파일을 지울 일이 없다).
    잡은 쪽의 설명은 곁의 `.누구` 파일에 적는다(기다리는 쪽이 누구를 기다리는지 알린다)."""

    def __init__(self, 경로, 대기초=3600.0, 누구="", 쉼=0.25):
        self.경로, self.대기초, self.누구, self.쉼 = 경로, float(대기초), 누구, 쉼
        self.fd = None

    def _잡기(self):
        if os.name == "nt":
            import msvcrt                                               # noqa: PLC0415
            os.lseek(self.fd, 0, 0)
            msvcrt.locking(self.fd, msvcrt.LK_NBLCK, 1)
        else:
            import fcntl                                                # noqa: PLC0415
            fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)

    def _풀기(self):
        if os.name == "nt":
            import msvcrt                                               # noqa: PLC0415
            os.lseek(self.fd, 0, 0)
            msvcrt.locking(self.fd, msvcrt.LK_UNLCK, 1)
        else:
            import fcntl                                                # noqa: PLC0415
            fcntl.flock(self.fd, fcntl.LOCK_UN)

    def __enter__(self):
        os.makedirs(os.path.dirname(os.path.abspath(self.경로)), exist_ok=True)
        self.fd = os.open(self.경로, os.O_RDWR | os.O_CREAT)
        끝 = time.time() + self.대기초
        알림 = False
        while True:
            try:
                self._잡기()
                break
            except OSError:
                if time.time() >= 끝:
                    os.close(self.fd)
                    self.fd = None
                    raise 잠금시간초과("%s — %.0f초 기다렸다(잡은 쪽: %s)" % (self.경로, self.대기초, self.잡은쪽()))
                if not 알림 and self.대기초 > 1:
                    print("  잠금 기다림 — %s" % self.잡은쪽(), flush=True)
                    알림 = True
                time.sleep(self.쉼)
        try:
            with io.open(self.경로 + ".누구", "w", encoding="utf-8") as f:
                f.write("%s · pid %d · %s" % (self.누구, os.getpid(), _지금()))
        except OSError:
            pass
        return self

    def 잡은쪽(self):
        try:
            return io.open(self.경로 + ".누구", encoding="utf-8").read().strip() or "?"
        except OSError:
            return "?"

    def __exit__(self, *e):
        if self.fd is not None:
            try:
                self._풀기()
            except OSError:
                pass
            os.close(self.fd)
            self.fd = None
        return False


def 엑셀잠금곳(지정=None):
    """엑셀 잠금 파일 — 지정 > 환경변수 DCF_회차잠금(폴더) > 공용 캐시(DCF_공용캐시 · DCF_SHARED_CACHE · 있으면 ~/.dcf캐시) > 사용자 임시 폴더."""
    for d in (지정, os.environ.get("DCF_회차잠금"), os.environ.get("DCF_공용캐시"), os.environ.get("DCF_SHARED_CACHE")):
        if d:
            return os.path.join(d, 잠금파일)
    집 = os.path.join(os.path.expanduser("~"), ".dcf캐시")
    if os.path.isdir(집):
        return os.path.join(집, 잠금파일)
    return os.path.join(tempfile.gettempdir(), 잠금파일)


# ══════════════════════════════════════════════════════════ 판(이 회차의 맥락)

class 판:
    """회사 폴더 하나의 맥락 — 경로 · 관할 · 날짜 둘 · 결산월 · 표기 · 옵션."""

    def __init__(self, 폴더, 가정=None, 국가=None, 평가기준일=None, 재무기준일=None, 결산월=None, 표기=None, 종목=None, 종가=None,
                 해수=None, 도구=None, **옵션):
        self.폴더 = os.path.abspath(폴더)
        self.도구 = os.path.abspath(도구) if 도구 else os.path.join(self.폴더, "스크립트")
        self.경보 = []
        self.가정 = 가정찾기(self.폴더, 가정)
        self.가정자료 = _읽기(self.상(self.가정), {}) if self.가정 else {}
        메타 = self.가정자료.get("메타") if isinstance(self.가정자료.get("메타"), dict) else {}
        기간 = self.가정자료.get("기간") if isinstance(self.가정자료.get("기간"), dict) else {}
        self.국가 = (국가 or "").upper() or None
        if not self.국가:
            통화 = (메타.get("표시통화") or "").upper()
            self.국가 = {"KRW": "KR", "USD": "US"}.get(통화)
        if not self.국가 and os.path.isfile(self.상("_raw/companyfacts.json")):
            self.국가 = "US"
        gT = gF = None
        if self.가정자료:
            try:
                import 기준일 as _기                                    # noqa: PLC0415 — 날짜의 정본
                gT = _기.평가기준일(self.가정자료).isoformat()
                gF = _기.재무기준일(self.가정자료).isoformat()
            except ImportError:                                        # 날짜 둘 이전의 옛 키트 사본 — 메타 두 칸을 그대로(F 가 없으면 F = T)
                gT = 메타.get("평가기준일") or None
                gF = 메타.get("재무기준일") or gT
                self.경보.append("기준일.py 가 없는 옛 키트다 — 메타의 날짜 칸을 그대로 읽었다")
            except Exception:                                          # noqa: BLE001
                gT = gF = None
        self.T = 평가기준일 or gT
        self.F = 재무기준일 or gF or self.T
        for 이름, 인, 가 in (("평가기준일", 평가기준일, gT), ("재무기준일", 재무기준일, gF)):
            if 인 and 가 and 인 != 가:
                self.경보.append("--%s %s 이(가) 가정의 %s 와 다르다 — 인자를 쓴다" % (이름, 인, 가))
        g결산 = 기간.get("결산월")
        self.결산월 = int(결산월) if 결산월 else (int(g결산) if g결산 else None)
        if 결산월 and g결산 and int(결산월) != int(g결산):
            self.경보.append("--결산월 %s 이(가) 가정의 기간.결산월 %s 와 다르다 — 인자를 쓴다" % (결산월, g결산))
        self.해수 = int(해수) if 해수 else (int(기간["실적연도수"]) if 기간.get("실적연도수") else None)
        self.표기 = 안전이름(표기 or 메타.get("회사명") or os.path.basename(self.폴더))
        self.금액단위 = 메타.get("금액단위")
        self.종목 = 종목
        self.종가 = 종가
        self.옵션 = 옵션

    def 상(self, p):
        return p if os.path.isabs(p) else os.path.join(self.폴더, p)

    def 있나(self, p):
        return os.path.exists(self.상(p))

    @property
    def 워크북(self):
        return "짓기/%s_DCF.xlsx" % self.표기

    @property
    def 레터(self):
        return "레터_%s.md" % self.표기

    @property
    def 판html(self):
        return "레터_%s_interactive.html" % self.표기

    def 키트판(self):
        v = _읽기(os.path.join(self.폴더, "버전.json")) or _읽기(os.path.join(os.path.dirname(self.도구), "버전.json")) or {}
        return {k: v[k] for k in sorted(v) if not k.startswith("_")}


def 가정찾기(폴더, 지정=None):
    """가정 파일(폴더 상대) — 지정이 먼저, 없으면 `가정_*.json` 하나(예시 · 템플릿 · 스키마는 뺀다). 여럿이면 입력 오류."""
    if 지정:
        return os.path.relpath(os.path.abspath(지정), 폴더) if os.path.isabs(지정) else 지정
    후보 = [os.path.basename(p) for p in glob.glob(os.path.join(폴더, "가정_*.json"))
          if not re.match(r"가정_(예시|템플릿|스키마)", os.path.basename(p))]
    if len(후보) > 1:
        raise 입력문제("가정 파일이 여럿이다(%s) — --가정 으로 하나를 고른다" % " · ".join(sorted(후보)))
    return 후보[0] if 후보 else None


class 입력문제(Exception):
    pass


# ══════════════════════════════════════════════════════════ 단계

class 단계:
    """단계 하나의 선언.

    명령(판) → [도구 파일 이름, 인자 …](도구 폴더 상대) | None        내부(판, 쓰기) → rc  — 명령 대신 실행기 안에서 하는 일
    입력(판) → [(경로, 모드, 필수)]  모드: 파일 · 값 · 전체(가정 파일)   산출 · 보호 · 부산출(판) → [경로]
    해당(판) → None | 까닭(해당없음)   다시필요(판) → None | 까닭(--다시 를 줘야 돈다)   보호표지(판, 경로) → 까닭 | None
    앞(판) — 돌기 직전(지난 산출 치우기)   뒤(판, rc, 쓰기) → rc — 돈 뒤(짝 파일 · 요건 대조)
    """

    def __init__(self, 이름, 설명, 명령=None, 내부=None, 입력=None, 산출=None, 보호=None, 부산출=None, 허용=(0,), 엑셀=False,
                 raw전체=False, 해당=None, 다시필요=None, 보호표지=None, 앞=None, 뒤=None, 기본=True, 별명=()):
        self.이름, self.설명 = 이름, 설명
        self._명령, self._내부 = 명령, 내부
        self._입력 = 입력 or (lambda 판: [])
        self._산출 = 산출 or (lambda 판: [])
        self._보호 = 보호 or (lambda 판: [])
        self._부산출 = 부산출 or (lambda 판: [])
        self.허용 = tuple(허용)
        self.엑셀, self.raw전체, self.기본, self.별명 = 엑셀, raw전체, 기본, tuple(별명)
        self._해당, self._다시필요, self._보호표지 = 해당, 다시필요, 보호표지
        self._앞, self._뒤 = 앞, 뒤

    def 명령(self, 판):
        return self._명령(판) if self._명령 else None

    def 입력(self, 판):
        return list(self._입력(판))

    def 산출(self, 판):
        return list(self._산출(판))

    def 보호(self, 판):
        return list(self._보호(판))

    def 부산출(self, 판):
        return list(self._부산출(판))

    def 해당(self, 판):
        return self._해당(판) if self._해당 else None

    def 다시필요(self, 판):
        return self._다시필요(판) if self._다시필요 else None

    def 보호표지(self, 판, p):
        return self._보호표지(판, p) if self._보호표지 else None


def _가(판, 모드="전체"):
    return [(판.가정, 모드, True)] if 판.가정 else [("가정 파일", 모드, True)]


def _A2보정표지(판, p):
    d = _읽기(판.상(p))
    if isinstance(d, dict) and (d.get("갈래") == "A2" or "보정" in d or "원천근거" in d):
        return "A2 보정본(갈래 · 보정 칸)"
    if 판.있나("_raw/도구원본/원천_조립.json"):
        return "도구 원본을 `_raw/도구원본/` 으로 옮긴 보정본"
    return None


def _원천명령(판):
    if 판.국가 == "US":
        a = ["sec_원천.py", "--기준일", 판.F, "--평가기준일", 판.T, "--출력", "_raw/원천_조립.json"]
        if 판.결산월:
            a += ["--결산월", "%d" % 판.결산월]
            if int(판.F[5:7]) != 판.결산월:
                a += ["--반기"]
        return a
    a = ["dart_원천.py", "--기준일", 판.F, "--평가기준일", 판.T, "--출력", "_raw/원천_조립.json"]
    if 판.해수:
        a += ["--해수", "%d" % 판.해수]
    return a


def _원천해당(판):
    if 판.국가 not in ("KR", "US"):
        return "관할을 모른다 — --국가 KR|US"
    if not (판.F and 판.T):
        return "날짜를 모른다 — 가정 파일 또는 --평가기준일 · --재무기준일"
    return None


def _동인원천명령(판):
    if 판.국가 == "US":
        a = ["동인원천.py", "--미국", "_raw/companyfacts.json", "--가정", 판.가정]
        if 판.금액단위 in ("달러", "천달러", "백만달러"):
            a += ["--원천통화단위", 판.금액단위]
        return a
    return ["동인원천.py", "--가정", 판.가정]


def _마감앞(판):
    for p in ("짓기/워크북마감.json", "짓기/워크북마감.txt", 판.워크북, 판.워크북 + ".좌표지도.json"):   # 짝 지도도 — 구조를 바꾼 뒤 옛 지도가 남지 않게(N5)
        if 판.있나(p):
            os.remove(판.상(p))


def _마감뒤(판, rc, 쓰기):
    짝 = 판.상(판.워크북 + ".좌표지도.json")
    원 = 판.상("짓기/부음.xlsx.좌표지도.json")
    if 판.있나(판.워크북) and not os.path.exists(짝) and os.path.exists(원):
        with open(원, "rb") as f:
            b = f.read()
        with open(짝, "wb") as f:
            f.write(b)
        쓰기("짝 좌표 지도를 워크북 곁에 두었다 — %s" % os.path.basename(짝))
    return rc


_넣기방식 = {"거꾸로": "--거꾸로", "가정우선": "--가정우선", "묶음우선": "--묶음우선"}


def _넣기명령(판):
    a = ["레터원고.py", "넣기", 판.가정, "--덮어쓰기"]
    m = 판.옵션.get("넣기방식")
    if m in _넣기방식:
        a.append(_넣기방식[m])
    return a


def _넣기다시(판):
    """판단 산출(레터 원고 묶음)을 덮는 넣기만 `--다시 넣기` 를 요구한다. 1.1.3(H29) — `--옵션 넣기방식=묶음우선` 은 그 옵션이 곧 「묶음 글로 가정 쪽 원고를
    덮는다」 는 뜻이라 매 실행 `--다시 넣기` 를 다시 묻지 않는다(사슬이 넣기 · 엔진 · 게이트 세 번으로 갈리던 자리). 거꾸로(가정 → 묶음)는 그대로 묻는다."""
    m = 판.옵션.get("넣기방식")
    if m == "거꾸로":
        return "넣기 --거꾸로 는 가정 쪽 글을 레터 원고 묶음에 옮겨 쓴다(원고 묶음을 덮는다)"
    return None


def _넣기뒤(판, rc, 쓰기):
    if rc != 0:
        return rc
    r = 도구돌기(판, ["레터.py", 판.가정, "--원고요건", "--json"], 담기=True)
    try:
        d = json.loads(r["글"][r["글"].index("{"):])
    except ValueError:
        쓰기("원고 요건을 읽지 못했다 — %s" % 끝줄(r["글"]))
        return 입력오류
    _쓰기(판.상("_raw/원고요건.json"), d)
    누락 = d.get("누락") or []
    쓰기("원고 요건 %d · 누락 %d" % (len(d.get("요건") or []), len(누락)))
    if 누락:
        쓰기("원고 누락 %d곳 — 판단 구간(레터 원고)으로 돌아간다: %s" % (
            len(누락), " · ".join("%s" % (x.get("자리") if isinstance(x, dict) else x) for x in 누락)[:400]))
        return 발견
    return 통과


def _게이트명령(판):
    a = ["레터게이트.py", "레터_초안.md", "레터_편집.md", "-o", 판.레터, "--가정", 판.가정, "--마감", "짓기/워크북마감.json"]
    if 인터랙티브새것(판):
        a += ["--인터랙티브", 판.판html]
    return a


def 인터랙티브새것(판):
    """1.1.2(P20) — 인터랙티브 판이 지금 초안의 장부보다 늦게 지어졌을 때만 게이트가 그 판을 맞댄다. 초안을 다시 지으면 옛 판이 남아
    ⑦-2(장부 해시)에서 멈췄고, 사슬 차례(게이트 → 인터랙티브)로는 스스로 풀지 못했다. 옛 판이면 이 게이트는 판을 보지 않고,
    인터랙티브 단계가 새 판을 지은 뒤 다시 돈 게이트가 맞댄다."""
    if not 판.있나(판.판html):
        return False
    장 = 판.상("레터_초안.장부.json")
    try:
        return not os.path.exists(장) or os.path.getmtime(판.상(판.판html)) >= os.path.getmtime(장)
    except OSError:
        return False


def _인터랙티브명령(판):
    a = ["레터인터랙티브.py", "--장부", "레터_초안.장부.json", "--레터", 판.레터, "-o", 판.판html]
    if 판.있나("레터_주가.csv"):
        a += ["--주가", "레터_주가.csv"]
    return a


# ── 내부 단계

합본머리, 합본끝 = "<!-- 합본:3분과같음 -->", "<!-- /합본:3분과같음 -->"


def _합본짝(글, 원):
    """1.1.3(CT25) — 원문이 두 번 나오고 그 가운데 꼭 하나가 본편 1절의 「합본:3분과같음」 블록 안이면 참(3분 레터와 1절은 같은 글로 둔 자리 —
    둘을 함께 고쳐야 같게 남는다)."""
    자리 = []
    i = 글.find(원)
    while i >= 0:
        자리.append(i)
        i = 글.find(원, i + 1)
    if len(자리) != 2:
        return False
    블 = []
    a = 글.find(합본머리)
    while a >= 0:
        b = 글.find(합본끝, a)
        if b < 0:
            break
        블.append((a, b))
        a = 글.find(합본머리, b)
    안 = [any(a <= j < b for a, b in 블) for j in 자리]
    return 안.count(True) == 1


def 편집적용(초안글, 목록, 장부=None, 기록=None):
    """편집 목록([{원문, 새글, 모두?}])을 초안 본문에 적용 → (새 글, 적용 수, 안 된 것[]). 원문이 본문에서 꼭 한 번 나와야 적용한다 —
    1.1.3(CT25) 두 예외: `모두: true` 면 본문의 그 원문을 모두 고치고, 원문이 3분 레터와 본편 1절의 같은 글(「합본:3분과같음」 블록과 그 짝)에만
    두 번 나오면 둘을 함께 고친다(같은 글로 남게). 부록(「# 부록」 줄 아래)은 건드리지 않는다 — 부록이 달라지면 ValueError.
    v27 교열 — `종류: 다시쓰기` 항목(교열 검토가 표시한 문장만 다시 쓴다 · `레터교열.py`)은 새 글의 장부 자리표시를 장부(키 · 꼴)로 펴고,
    숫자가 원문의 숫자 안에서만 나오고 열쇠 말이 남을 때만 적용한다(`레터교열.다시쓰기펴기`). 그 원문은 지금 글(앞 항목을 적용한 뒤)의
    본문에서 찾는다 — 둘째 회의 다시 쓰기가 첫 회에 고친 문장을 다시 고친다. 기록(목록)을 주면 적용한 항목마다 {원문, 새글(편 글)} 을 더한다
    (`_raw/편집적용.json` — 게이트가 문장 단위로 숫자를 맞댈 재료 · `레터교열.문장대조`)."""
    표 = "\n# 부록\n"
    부록 = 초안글.find(표)
    본문끝 = 부록 if 부록 >= 0 else len(초안글)
    본문 = 초안글[:본문끝]
    글, 됨, 안됨 = 초안글, 0, []
    for k, x in enumerate(목록, 1):
        if not (isinstance(x, dict) and isinstance(x.get("원문"), str) and isinstance(x.get("새글"), str) and x["원문"]):
            안됨.append("%d — 꼴이 아니다({원문, 새글})" % k)
            continue
        원, 새 = x["원문"], x["새글"]
        if x.get("종류") == "다시쓰기":
            import 레터교열 as _교                            # noqa: PLC0415
            새, 걸 = _교.다시쓰기펴기(원, 새, 장부)
            if 걸:
                안됨.append("%d — 다시 쓰기 조건(%s): %s" % (k, " · ".join(걸[:3]), 원[:60]))
                continue
            끝 = 글.find(표) if 표 in 글 else len(글)
            지금 = 글[:끝]
            n = 지금.count(원)
            if n == 0:
                안됨.append("%d — 다시 쓸 원문이 지금 글의 본문에 없다(초안이 바뀌었거나 부록 안이다): %s" % (k, 원[:60]))
                continue
            if n != 1 and not (x.get("모두") is True or _합본짝(지금, 원)):
                안됨.append("%d — 지금 글에서 %d번 나온다(「모두」: true 로 모두 고친다): %s" % (k, n, 원[:60]))
                continue
            글 = 지금.replace(원, 새) + 글[끝:]
            됨 += 1
            if 기록 is not None:
                기록.append({"종류": "다시쓰기", "원문": 원, "새글": 새, "회": x.get("회")})
            continue
        n, n전 = 본문.count(원), 초안글.count(원)
        if n == 0 and n전 == 1 and 0 <= 초안글.find(원) < 본문끝:       # 본문에서 시작해 부록으로 넘어가는 원문 — 고치면 부록이 달라진다(아래에서 막는다)
            글 = 글.replace(원, 새, 1)
            됨 += 1
            continue
        여럿 = x.get("모두") is True or _합본짝(본문, 원)
        if n == 0 and n전:
            안됨.append("%d — 부록 안이다: %s" % (k, 원[:60]))
            continue
        if n != 1 and not (여럿 and n >= 1):
            안됨.append("%d — 초안에서 %d번 나온다%s: %s" % (k, n, "(3분 레터 · 1절의 같은 글이 아니면 「모두」: true 로 모두 고친다)" if n > 1 else "", 원[:60]))
            continue
        if n전 != n and not 여럿:
            안됨.append("%d — 부록 안에도 있다: %s" % (k, 원[:60]))
            continue
        끝 = 글.find(표) if 표 in 글 else len(글)
        if 글[:끝].count(원) != n:
            안됨.append("%d — 앞 항목을 적용한 뒤 %d번 나온다(겹침): %s" % (k, 글[:끝].count(원), 원[:60]))
            continue
        글 = 글[:끝].replace(원, 새) + 글[끝:]
        됨 += 1
        if 기록 is not None:
            기록.append({"원문": 원, "새글": 새})
    if 부록 >= 0 and 초안글.split(표, 1)[1] != (글.split(표, 1)[1] if 표 in 글 else None):
        raise ValueError("부록이 달라졌다 — 쓰지 않는다")
    return 글, 됨, 안됨


def _편집내부(판, 쓰기):
    초p, 목p, 출p = 판.상("레터_초안.md"), 판.상("_raw/편집목록.json"), 판.상("레터_편집.md")
    목록 = _읽기(목p)
    if not isinstance(목록, list):
        쓰기("편집 목록(_raw/편집목록.json)이 목록 꼴이 아니다")
        return 입력오류
    원바이트 = open(초p, "rb").read()
    crlf = b"\r\n" in 원바이트
    초 = 원바이트.decode("utf-8").replace("\r\n", "\n")
    장부 = _읽기(판.상("레터_초안.장부.json"))                  # v27 교열 — 「다시쓰기」 항목의 자리표시를 펴는 장부
    적용 = []
    try:
        글, 됨, 안됨 = 편집적용(초, 목록, 장부 if isinstance(장부, dict) else None, 적용)
    except ValueError as e:
        쓰기("%s" % e)
        return 발견
    if crlf:
        글 = 글.replace("\n", "\r\n")
    with open(출p, "wb") as f:
        f.write(글.encode("utf-8"))
    _쓰기(판.상("_raw/편집적용.json"), {"형식": "편집적용/1", "초안해시": hashlib.sha256(초.encode("utf-8")).hexdigest(), "항목": 적용})
    for x in 안됨:
        쓰기("  ! " + x)
    다 = sum(1 for x in 목록 if isinstance(x, dict) and x.get("종류") == "다시쓰기")
    쓰기("적용 %d / %d(다시 쓰기 %d) · 안 됨 %d → 레터_편집.md (%s)" % (됨, len(목록), 다, len(안됨), "CRLF" if crlf else "LF"))
    return 발견 if 안됨 else 통과


def _교열내부(판, 쓰기):
    """v27 교열 — 교열 검토는 판단 구간(교열자 · `.claude/갈래/L2_레터교열.md`)이다. 이 단계는 기록만 확인한다(`레터교열.확인`):
    표시 · 다시 쓰기 고리 두 회 · 남은 목록 · 교열 대장이 섰나. 덜 섰으면 발견(허용 — 진행판에 남고 사슬은 간다 · `--엄격` 이면 멈춘다)."""
    try:
        import 레터교열 as _교                                # noqa: PLC0415
        rc, 줄 = _교.확인(판.상("."))
    except Exception as e:                                       # noqa: BLE001
        쓰기("교열 기록을 읽지 못했다 — %s: %s" % (type(e).__name__, e))
        return 발견
    if rc and 교열남은차례(판, _교):                                # 1.1.19 — 고리 두 회 뒤 · 남은 목록 전은 정상 흐름(남은 목록은 편집본을 읽는다)
        줄 = [x for x in 줄 if not x.startswith("남은 목록이 없다")] + [
            "다시 쓰기 %d회가 섰다 — 다음은 편집 단계 뒤 `레터교열.py 남은`(남은 목록은 편집본 레터_편집.md 를 읽는다 · 정상 흐름)" % _교.회상한]
        rc = 0
    for x in 줄:
        쓰기(x)
    _쓰기(판.상("_raw/교열/확인.json"), {"rc": rc, "줄": 줄})
    return 발견 if rc else 통과


def 교열남은차례(판, 교=None):
    """다시 쓰기 고리가 두 회(`레터교열.회상한`) 섰고 교열 대장이 있는데 남은 목록만 없는가 — 사슬 차례(초안 → 교열 → 편집) 위에서 남은 목록은
    편집 뒤에 낸다(`레터교열.py 남은` 은 레터_편집.md 를 읽는다). 그 사이의 교열 단계는 실패가 아니다."""
    if 교 is None:
        import 레터교열 as 교                                  # noqa: PLC0415
    회차 = 판.상(".")
    return (len(교.고리들(회차)) >= 교.회상한 and not os.path.isfile(os.path.join(회차, 교.곳, "남은목록.json"))
            and bool(_읽기(os.path.join(회차, 교.대장곳 + ".json"))))


def _편집해당(판):
    if not 판.있나("_raw/편집목록.json"):
        if 판.있나("레터_편집.md"):
            return "편집 목록 없음 — 손으로 쓴 레터_편집.md 를 그대로 쓴다"
        return None                                     # 입력 점검에서 멈춘다(판단 구간 대기)
    return None


def _편집입력(판):
    if not 판.있나("_raw/편집목록.json") and not 판.있나("레터_편집.md"):
        return [("레터_초안.md", "파일", True), ("_raw/편집목록.json 또는 레터_편집.md (판단 구간 — 편집)", "파일", True)]
    return [("레터_초안.md", "파일", True), ("_raw/편집목록.json", "파일", True)]


def _PDF도구(판):
    return 판.옵션.get("PDF도구") or os.environ.get("DCF_PDF도구") or os.environ.get("DCF_PDF_TOOL")


def _PDF해당(판):
    if not _PDF도구(판):
        return "PDF 도구가 없다 — --PDF도구 또는 환경변수 DCF_PDF도구(레터 HTML → PDF 를 찍는 도구)"
    if not os.path.isfile(_PDF도구(판)):
        return "PDF 도구 파일이 없다 — %s" % os.path.basename(_PDF도구(판))
    return None


def _PDF쌍(판):
    밑 = 판.레터[:-3]
    return [(h, h[:-5] + ".pdf") for h in (밑 + ".html", 밑 + "_3분.html") if 판.있나(h)]


def _PDF내부(판, 쓰기):
    rc = 통과
    for h, p in _PDF쌍(판):
        r = 바깥돌기(판, [sys.executable, "-X", "utf8", os.path.abspath(_PDF도구(판)), 판.상(h), 판.상(p)])
        쓰기(r["글"].rstrip())
        쓰기("PDF %s → %s · rc %s" % (h, p, r["rc"]))
        if r["rc"] != 0:
            rc = r["rc"] if isinstance(r["rc"], int) else 발견
    return rc


def _주가내부(판, 쓰기):
    if 판.국가 == "US":
        return _미국주가(판, 쓰기)
    if 판.국가 != "KR":
        쓰기("미구현 — 관할 %s 의 일봉을 받는 길이 없다. 레터_주가.csv(「#」 주석 · date,close)를 따로 둔다" % 판.국가)
        return 미구현
    if not 판.종목:
        쓰기("--종목(국내 6자리)이 없다")
        return 입력오류
    기 = datetime.date.fromisoformat(판.T)
    시작 = (기 - datetime.timedelta(days=int(판.옵션.get("주가일수") or 430))).strftime("%Y%m%d")
    # 1.1.2(P5) — 창 끝은 평가기준일(T)이다. 오늘로 받으면 T 뒤 거래일이 레터_주가.csv 에 섞여 평가기준일 뒤 정보가 레터에 든다.
    #   T 뒤 주가가 필요한 회차(평가기준일 뒤의 주가 경로를 일부러 싣는 판)만 `--옵션 주가뒤포함=1`
    뒤포함 = ("%s" % (판.옵션.get("주가뒤포함") or "")).strip() not in ("", "0", "아니오", "false")
    끝 = (datetime.date.today() if 뒤포함 else min(datetime.date.today(), 기)).strftime("%Y%m%d")
    r = 도구돌기(판, ["naver_price.py", "--ticker", 판.종목, "--domestic", "--일봉", "--부터", 시작, "--까지", 끝], 담기=True)
    쓰기(r["글"].rstrip()[-400:])
    p = 판.상(os.path.join("_raw", "peers", "sise_%s_day_%s_%s.json" % (판.종목, 시작, 끝)))
    줄 = _읽기(p)
    if 줄 and not 뒤포함:
        T8 = 기.strftime("%Y%m%d")
        줄 = [x for x in 줄 if ("%s" % x[0]).replace("-", "")[:8] <= T8]
    if not 줄:
        쓰기("주가를 받지 못했다 — 비슷한 값으로 메우지 않는다")
        return 발견
    with io.open(판.상("레터_주가.csv"), "w", encoding="utf-8-sig") as f:
        f.write("# %s 일별 시세. 출처 api.finance.naver.com/siseJson.naver?symbol=%s (일봉 · 수정주가). 조회일 %s\n"
                % (판.종목, 판.종목, datetime.date.today().isoformat()))
        f.write("date,close\n")
        for d, c in 줄:
            f.write("%s,%s\n" % (d, c))
    쓰기("레터_주가.csv — %d일 (%s ~ %s)" % (len(줄), 줄[0][0], 줄[-1][0]))
    return 통과


def _지수해당(판):
    if not (판.F and 판.T) or 판.F >= 판.T:
        return "날짜 하나 판(재무기준일 = 평가기준일) — 시장 변동을 견줄 사이 기간이 없다"
    if 판.국가 not in ("KR", "US"):
        return "관할을 모른다 — --국가 KR|US"
    return None


def _미국주가(판, 쓰기):
    """1.1.11 — 미국 종목 일봉(야후 차트 창구 — 대표 지수와 같은 창구 · `갭해석.지수받기`)을 레터_주가.csv 에. 창은 평가기준일 앞 430일 ~ 평가기준일
    (T 뒤 거래일은 싣지 않는다 — `주가뒤포함=1` 이면 오늘까지). 레터는 이 파일로 평가 종가가 평가기준일 앞 마지막 거래일의 값인지 보고 그 날을 적는다
    (실측: 실적 발표 다음 날을 평가기준일로 둔 회차가 전날 종가를 「평가기준일 종가」로 찍었다). 받지 못하면 발견(비슷한 값으로 메우지 않는다)."""
    import urllib.parse                                         # noqa: PLC0415
    import urllib.request                                       # noqa: PLC0415
    if not 판.종목:
        쓰기("--종목(미국 티커)이 없다")
        return 입력오류
    기 = datetime.date.fromisoformat(판.T)
    시작 = 기 - datetime.timedelta(days=int(판.옵션.get("주가일수") or 430))
    뒤포함 = ("%s" % (판.옵션.get("주가뒤포함") or "")).strip() not in ("", "0", "아니오", "false")
    끝 = datetime.date.today() if 뒤포함 else min(datetime.date.today(), 기)
    p1 = int(datetime.datetime(시작.year, 시작.month, 시작.day, tzinfo=datetime.timezone.utc).timestamp())
    p2 = int(datetime.datetime(끝.year, 끝.month, 끝.day, tzinfo=datetime.timezone.utc).timestamp()) + 86400
    u = "https://query1.finance.yahoo.com/v8/finance/chart/%s?period1=%d&period2=%d&interval=1d" % (urllib.parse.quote(판.종목), p1, p2)
    try:
        d = json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=30).read().decode("utf-8"))
    except Exception as e:                                       # noqa: BLE001
        쓰기("주가를 받지 못했다 — %s (비슷한 값으로 메우지 않는다)" % e)
        return 발견
    r = ((d.get("chart") or {}).get("result") or [None])[0] or {}
    ts, cl = r.get("timestamp") or [], (((r.get("indicators") or {}).get("quote") or [{}])[0].get("close") or [])
    줄 = sorted((datetime.datetime.fromtimestamp(t, datetime.timezone.utc).date().isoformat(), float(c)) for t, c in zip(ts, cl) if c is not None)
    줄 = [x for x in 줄 if x[0] <= 끝.isoformat()]
    if not 줄:
        쓰기("주가를 받지 못했다 — 빈 응답(비슷한 값으로 메우지 않는다)")
        return 발견
    with io.open(판.상("레터_주가.csv"), "w", encoding="utf-8-sig", newline="\n") as f:
        f.write("# %s 일별 시세. 출처 query1.finance.yahoo.com/v8/finance/chart/%s (일봉 · 장 마감 값). 조회일 %s\n"
                % (판.종목, 판.종목, datetime.date.today().isoformat()))
        f.write("date,close\n")
        for 날, 값 in 줄:
            f.write("%s,%s\n" % (날, 값))
    쓰기("레터_주가.csv — %d일 · 마지막 %s %s" % (len(줄), 줄[-1][0], 줄[-1][1]))
    return 통과


def _지수내부(판, 쓰기):
    """1.1.3(A1) — 표시통화 시장의 대표 지수 일봉(국내 KOSPI · 미국 S&P 500 — 갭해석설정.json)을 회사 폴더의 레터_지수.csv 에. 받지 못하면 발견(비슷한 값으로 메우지 않는다)."""
    try:
        import 갭해석 as _G                                     # noqa: PLC0415
        with io.open(판.상(판.가정), encoding="utf-8") as f:
            가 = json.load(f)
        p, n = _G.지수받기(가, 판.상("."))
    except Exception as e:                                       # noqa: BLE001
        쓰기("지수를 받지 못했다 — %s" % e)
        return 발견
    쓰기("레터_지수.csv — %d일 → %s" % (n, p))
    return 통과


def _꾸러미내부(판, 쓰기):
    쓰기("지금 쓸 수 있는 것: 원천넣기(원천축적.py 넣기) · 조사넣기(조사축적.py 넣기) 단계가 공용 캐시에 쌓는다.")
    쓰기("미구현 — 꾸러미 내보내기(회사 × 기준일 단위 · 원천 · 조사 갈래 산출 · 시장 자료 · 매크로 · 리포트 축 · 목록.json)는 규격 v0 만 섰다(종료 코드 3)")
    return 미구현


def _종목필요(판):
    if not 판.종목:
        return "--종목(국내 6자리 · 미국 티커)이 없다"
    if 판.국가 not in ("KR", "US"):
        return "관할을 모른다 — --국가 KR|US"
    return None


def 단계표():
    """사슬의 단계 — 이 차례가 정본이다(고른 단계도 이 차례로 돈다)."""
    W = lambda 판: 판.워크북                                            # noqa: E731
    return [
        단계("원천", "A2 원천 조립 도구(dart_원천 · sec_원천) — 보정본이 있으면 보호",
             명령=_원천명령, 해당=_원천해당, raw전체=True,
             입력=lambda 판: ([("_raw/companyfacts.json", "파일", True)] if 판.국가 == "US" else []),
             산출=lambda 판: ["_raw/원천_조립.json"], 보호=lambda 판: ["_raw/원천_조립.json"], 보호표지=_A2보정표지, 별명=("A2",)),
        단계("IR", "최신 실적 IR 묶음 받기(IR묶음 — 미국 8-K 2.02 첨부 · 국내 잠정실적 · 기업설명회) — 콜 전사 · 읽음 표지는 이어 적는다(1.1.11)",
             명령=lambda 판: ["IR묶음.py", "받기", "--가정", 판.가정], raw전체=True, 입력=lambda 판: _가(판),
             산출=lambda 판: ["_raw/IR묶음.json"], 별명=("IR묶음",)),
        단계("동인원천", "A3 동인 원천 도구 — 갈래가 고친 산출이면 보호",
             명령=_동인원천명령, 해당=_원천해당, raw전체=True, 입력=lambda 판: _가(판),
             산출=lambda 판: ["_raw/동인원천.json"], 보호=lambda 판: ["_raw/동인원천.json"], 별명=("A3",)),
        단계("합류", "매출 구분 판정 초안(매출구분초안) — 본선이 고쳤으면 보호",
             명령=lambda 판: ["매출구분초안.py", "--가정", 판.가정], raw전체=True, 입력=lambda 판: _가(판),
             산출=lambda 판: ["_raw/매출구분판정.json"], 보호=lambda 판: ["_raw/매출구분판정.json"]),
        단계("동인진단", "E 동인 진단 도구 — 갈래가 고친 산출이면 보호",
             명령=lambda 판: ["동인진단.py", "--가정", 판.가정, "--매출구분판정", "_raw/매출구분판정.json"], raw전체=True,
             입력=lambda 판: _가(판), 산출=lambda 판: ["_raw/동인진단.json"], 보호=lambda 판: ["_raw/동인진단.json"], 별명=("E",)),
        단계("동인지도", "동인 지도 짓기(--덮기 — 정정 · 멈춤 · 성격 확정은 잇는다)",
             명령=lambda 판: ["동인지도짓기.py", 판.가정, "--덮기"], raw전체=True, 입력=lambda 판: _가(판),
             산출=lambda 판: ["_raw/동인지도.json"]),
        단계("엔진", "계산 엔진(dcf엔진) — 가정 값만 읽는다",
             명령=lambda 판: ["dcf엔진.py", 판.가정, "_raw/엔진_결과.json"], 입력=lambda 판: _가(판, "값"),
             산출=lambda 판: ["_raw/엔진_결과.json"]),
        단계("짓기", "스캐폴드 짓기(생성기) — 가정의 기간 · 구조로", 엑셀=True,
             명령=lambda 판: ["스캐폴드짓기.py", 판.가정, "짓기"], 입력=lambda 판: _가(판, "값"),
             산출=lambda 판: ["짓기/DCF_워크북_스캐폴드.xlsx", "짓기/DCF_워크북_좌표지도.json"]),
        단계("붓기", "가정을 스캐폴드에 붓기", 엑셀=True, 허용=(0, 1),
             명령=lambda 판: ["붓기.py", "짓기/DCF_워크북_스캐폴드.xlsx", 판.가정, "짓기/부음.xlsx"]
             + (["--경보무시"] if 판.옵션.get("붓기경보무시") else []),
             입력=lambda 판: _가(판, "값검토") + [("짓기/DCF_워크북_스캐폴드.xlsx", "파일", True), ("짓기/DCF_워크북_좌표지도.json", "파일", True)],
             산출=lambda 판: ["짓기/부음.xlsx"], 부산출=lambda 판: ["짓기/부음.xlsx.좌표지도.json"]),
        단계("마감", "워크북 마감(재계산 · 판정 · 도구 기입 · 서식) → 평가 모델 파일", 엑셀=True, 허용=(0, 1), 별명=("재계산",),
             명령=lambda 판: ["워크북마감.py", "짓기/부음.xlsx", 판.가정, "--낼", W(판), "--출력", "짓기/워크북마감.txt"],
             입력=lambda 판: _가(판, "값검토") + [("짓기/부음.xlsx", "파일", True)],
             산출=lambda 판: [W(판), "짓기/워크북마감.json", "짓기/워크북마감.txt"], 부산출=lambda 판: [W(판) + ".좌표지도.json"],
             앞=_마감앞, 뒤=_마감뒤),
        단계("모순앞", "모순 장부(자체검사가 지금 장부를 읽게 먼저)", 허용=(0, 1), raw전체=True,
             명령=lambda 판: ["모순장부.py", 판.가정], 입력=lambda 판: _가(판), 산출=lambda 판: ["_raw/모순장부.json"]),
        단계("자체검사", "자체 검사", 허용=(0, 1), raw전체=True,
             명령=lambda 판: ["자체검사.py", 판.가정, "--출력", "_raw/자체검사.txt"], 입력=lambda 판: _가(판),
             산출=lambda 판: ["_raw/자체검사.txt"]),
        단계("대조", "워크북 ↔ 엔진 대조", 엑셀=True, 허용=(0, 1), raw전체=True,
             명령=lambda 판: ["대조.py", W(판), 판.가정, "--출력", "_raw/대조.txt"],
             입력=lambda 판: _가(판) + [(W(판), "파일", True)], 산출=lambda 판: ["_raw/대조.txt"]),
        단계("모순장부", "모순 장부(대조 뒤 다시)", 허용=(0, 1), raw전체=True,
             명령=lambda 판: ["모순장부.py", 판.가정], 입력=lambda 판: _가(판), 산출=lambda 판: ["_raw/모순장부.json"]),
        단계("넘긴몫", "넘긴 몫 장부(미결이 있으면 발견 — 게이트 ⑤ 가 다시 본다)", 허용=(0, 1), raw전체=True,
             명령=lambda 판: ["넘긴몫.py", 판.가정], 입력=lambda 판: _가(판), 산출=lambda 판: ["_raw/넘긴몫.json"]),
        단계("거친바퀴", "거친 바퀴(민감도 순위 — 동인 지도에 되적는다)", 허용=(0, 1), raw전체=True,
             명령=lambda 판: ["거친바퀴.py", 판.가정, "--json", "_raw/거친바퀴.json"], 입력=lambda 판: _가(판),
             산출=lambda 판: ["_raw/거친바퀴.json"], 부산출=lambda 판: ["_raw/동인지도.json"]),
        단계("역산", "역산(그 가격이 성립하려면) — --종가 를 줄 때만", 기본=False, raw전체=True,
             명령=lambda 판: ["역산.py", 판.가정, "--주가", "%s" % 판.종가, "--날짜", 판.T],
             해당=lambda 판: None if 판.종가 else "--종가 가 없다", 입력=lambda 판: _가(판),
             산출=lambda 판: ["_raw/역산_독자.json"]),
        단계("넣기", "레터 원고 넣기 → 원고 요건 대조(누락이면 멈춘다)",
             명령=_넣기명령, 다시필요=_넣기다시, 뒤=_넣기뒤,
             입력=lambda 판: _가(판) + [("_raw/레터원고", "파일", False)], 산출=lambda 판: ["_raw/원고요건.json"]),
        단계("지수", "대표 지수 일봉(레터_지수.csv — 날짜 둘 회차의 시장 변동 · 1.1.3)", 내부=_지수내부, 해당=_지수해당, 허용=(0, 1),
             입력=lambda 판: _가(판, "값"), 산출=lambda 판: ["레터_지수.csv"]),
        단계("신호", "신호 · 통계 도구 앞 · 뒤 · 끝(신호돌리기 — 넣기 뒤 · 초안 앞. 격자 · 결합은 따로 선 단계)", 허용=(0, 1), raw전체=True,
             명령=lambda 판: ["신호돌리기.py", 판.가정, "--건너뛰기", "결합민감도,민감도격자"],
             입력=lambda 판: _가(판, "값") + [("레터_주가.csv", "파일", False), ("레터_지수.csv", "파일", False)],
             산출=lambda 판: ["_raw/신호돌리기.json"]),
        단계("격자", "민감도 격자(레터 재료)", raw전체=True, 별명=("재료",),
             명령=lambda 판: ["민감도격자.py", 판.가정], 입력=lambda 판: _가(판), 산출=lambda 판: ["_raw/민감도격자.json"]),
        단계("결합", "결합 민감도(레터 재료)", 허용=(0, 1), raw전체=True, 별명=("재료",),
             명령=lambda 판: ["결합민감도.py", 판.가정], 입력=lambda 판: _가(판), 산출=lambda 판: ["_raw/결합민감도.json"]),
        단계("초안", "레터 초안 · 숫자 장부", 허용=(0, 1), raw전체=True,
             명령=lambda 판: ["레터.py", 판.가정, "--엑셀", W(판), "--마감", "짓기/워크북마감.json", "-o", "레터_초안.md"],
             입력=lambda 판: _가(판) + [(W(판), "파일", True), ("짓기/워크북마감.json", "파일", True)],
             산출=lambda 판: ["레터_초안.md", "레터_초안.장부.json"]),
        단계("교열", "교열 검토 기록 확인(판단 구간 — 교열자 표시 · 다시 쓰기 고리 두 회 · 남은 목록 · 교열 대장 · `레터교열.py`)", 허용=(0, 1),
             내부=_교열내부, 입력=lambda 판: [("레터_초안.md", "파일", True), ("_raw/편집목록.json", "파일", False)]
             + [("_raw/교열/%s.json" % x, "파일", False) for x in ("고리_1", "고리_2", "남은목록")],
             산출=lambda 판: ["_raw/교열/확인.json"]),
        단계("편집", "편집 목록 적용(_raw/편집목록.json → 레터_편집.md · 「다시쓰기」 항목은 장부로 편다) — 손으로 쓴 편집본이면 보호",
             내부=_편집내부, 해당=_편집해당, 입력=lambda 판: _편집입력(판) + [("레터_초안.장부.json", "파일", False)],
             산출=lambda 판: ["레터_편집.md"], 보호=lambda 판: ["레터_편집.md"], 부산출=lambda 판: ["_raw/편집적용.json"]),
        단계("게이트", "레터 게이트(배포 조건 판정 · 최종 레터)", raw전체=True,
             명령=_게이트명령,
             입력=lambda 판: _가(판) + [("레터_초안.md", "파일", True), ("레터_편집.md", "파일", True),
                                       ("레터_초안.장부.json", "파일", True), ("짓기/워크북마감.json", "파일", True)],
             산출=lambda 판: [판.레터, 판.레터[:-3] + ".html"]),
        단계("주가", "레터 주가 파일(레터_주가.csv — 국내 · 미국 일봉 · 1.1.11)", 기본=False, 내부=_주가내부, 해당=_종목필요,
             입력=lambda 판: [], 산출=lambda 판: ["레터_주가.csv"]),
        단계("인터랙티브", "인터랙티브 판", 명령=_인터랙티브명령,
             입력=lambda 판: [("레터_초안.장부.json", "파일", True), (판.레터, "파일", True), ("레터_주가.csv", "파일", False),
                             ("_raw/민감도격자.json", "파일", False), ("_raw/결합민감도.json", "파일", False)],
             산출=lambda 판: [판.판html]),
        단계("모션", "레터 모션(영상 · 포스터 — 블로그 · SNS 배포물 · 기본 꺼짐: `--단계 모션` 으로 켠다 · v27 7단계)", 기본=False, 허용=(0, 1),
             명령=lambda 판: ["레터모션.py", 판.레터, "--장부", "레터_초안.장부.json"],
             입력=lambda 판: [(판.레터, "파일", True), ("레터_초안.장부.json", "파일", True)], 산출=lambda 판: ["모션"]),
        단계("PDF", "레터 PDF(바깥 PDF 도구 — 없으면 해당없음)", 내부=_PDF내부, 해당=_PDF해당, 허용=(0, 1),
             입력=lambda 판: [(h, "파일", True) for h, _p in _PDF쌍(판)] or [(판.레터[:-3] + ".html", "파일", True)],
             산출=lambda 판: [p for _h, p in _PDF쌍(판)]),
        단계("원천넣기", "공시 원천을 공용 캐시에(원천축적 넣기)", 기본=False, 해당=_종목필요, raw전체=True, 허용=(0, 1),
             명령=lambda 판: ["원천축적.py", "넣기", "--국가", 판.국가, "--종목", 판.종목, "--raw", "_raw"]),
        단계("조사넣기", "조사 갈래 산출을 공용 캐시에(조사축적 넣기)", 기본=False, 해당=_종목필요, raw전체=True, 허용=(0, 1),
             명령=lambda 판: ["조사축적.py", "넣기", "--국가", 판.국가, "--종목", 판.종목, "--raw", "_raw"]),
        단계("꾸러미", "분기 데이터 꾸러미 내보내기(미구현 — 종료 코드 3)", 기본=False, 내부=_꾸러미내부),
    ]


def 판단산출(판):
    """어느 단계도 산출로 쓰면 안 되는 판단 파일(보호로 선언한 자리는 예외)."""
    낸 = ["_raw/레터원고", "_raw/편집목록.json"]
    if 판.가정:
        낸.append(판.가정)
    return 낸


def 산출점검(단계들, 판):
    """단계 선언이 판단 파일을 산출로 적지 않았나 → 걸린 것[]."""
    금 = [os.path.normcase(os.path.normpath(판.상(p))) for p in 판단산출(판)]
    걸림 = []
    for s in 단계들:
        try:
            쓰는 = s.산출(판) + s.부산출(판)
        except Exception:                                              # noqa: BLE001 — 맥락이 모자라 선언을 못 푸는 단계는 넘긴다
            continue
        for p in 쓰는:
            q = os.path.normcase(os.path.normpath(판.상(p)))
            if any(q == g or q.startswith(g + os.sep) for g in 금):
                걸림.append("%s — %s" % (s.이름, p))
    return 걸림


def 고르기(단계들, 이름들=None, 부터=None, 까지=None):
    """이름(별명 포함) → 사슬 차례의 단계 목록. 모르는 이름은 입력문제."""
    색 = {}
    for s in 단계들:
        색.setdefault(s.이름, []).append(s)
        for b in s.별명:
            색.setdefault(b, []).append(s)
    def 찾(n):
        if n not in 색:
            raise 입력문제("모르는 단계: %s (있는 단계: %s)" % (n, " · ".join(s.이름 for s in 단계들)))
        return 색[n]
    if 이름들:
        고른 = set()
        for n in 이름들:
            고른.update(id(s) for s in 찾(n))
        return [s for s in 단계들 if id(s) in 고른]
    차례 = [s for s in 단계들 if s.기본]
    for n in (부터, 까지):
        if n and not any(x in 차례 for x in 찾(n)):
            raise 입력문제("--부터 · --까지 는 기본 사슬의 단계만 받는다: %s" % n)
    i = min(차례.index(x) for x in 찾(부터) if x in 차례) if 부터 else 0
    j = max(차례.index(x) for x in 찾(까지) if x in 차례) if 까지 else len(차례) - 1
    if i > j:
        raise 입력문제("--부터 %s 가 --까지 %s 보다 뒤다" % (부터, 까지))
    return 차례[i:j + 1]


# ══════════════════════════════════════════════════════════ 진행판

def 판경로(판):
    return os.path.join(판.폴더, 판이름)


def 판읽기(판):
    d = _읽기(판경로(판))
    if not isinstance(d, dict):
        d = {"형식": 형식, "만든때": _지금()}
    d.setdefault("단계", {})
    d.setdefault("이력", [])
    d.setdefault("판단구간", [])
    return d


def 판고치기(판, 고침):
    """진행판을 잠그고 다시 읽어 고친 뒤 쓴다(바깥의 `기록` 과 함께 돌아도 서로 덮지 않는다)."""
    with 잠금(os.path.join(판.폴더, 작업곳, "진행판.lock"), 대기초=120, 누구="진행판"):
        d = 판읽기(판)
        고침(d)
        d["형식"] = 형식
        d["고친때"] = _지금()
        d["회사"] = {"표기": 판.표기, "국가": 판.국가, "평가기준일": 판.T, "재무기준일": 판.F, "결산월": 판.결산월,
                   "가정": 판.가정, "종목": 판.종목}
        d["이력"] = d["이력"][-이력상한:]
        _쓰기(판경로(판), d)
        return d


# ══════════════════════════════════════════════════════════ 돌기

def 바깥돌기(판, 명령, 로그=None, 담기=False, 상한초=None):
    """명령을 회사 폴더에서 돌린다 → {rc, 글}. 로그가 있으면 출력 전문을 거기에."""
    환 = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1")
    if 판.옵션.get("생성기"):
        환["DCF_GENERATOR"] = os.path.abspath(판.옵션["생성기"])
    상한 = 상한초 or float(판.옵션.get("상한초") or 3600)
    try:
        r = subprocess.run(명령, cwd=판.폴더, capture_output=True, text=True, encoding="utf-8", errors="replace", env=환, timeout=상한)
        rc, 글 = r.returncode, (r.stdout or "") + (r.stderr or "")
    except subprocess.TimeoutExpired as e:
        앞글 = e.stdout or ""
        if isinstance(앞글, bytes):
            앞글 = 앞글.decode("utf-8", "replace")
        rc, 글 = "시간초과", 앞글 + "\n시간초과 — %.0f초" % 상한
    if 로그:
        with io.open(로그, "a", encoding="utf-8") as f:
            f.write(글)
    return {"rc": rc, "글": 글}


def 도구돌기(판, 인자, 로그=None, 담기=False):
    도 = os.path.join(판.도구, 인자[0])
    return 바깥돌기(판, [sys.executable, "-X", "utf8", 도] + list(인자[1:]), 로그=로그, 담기=담기)


def _raw목록(판):
    """_raw 맨 위 파일 → {상대 경로: (크기, 시각)}."""
    d = 판.상("_raw")
    낸 = {}
    if os.path.isdir(d):
        for f in os.listdir(d):
            p = os.path.join(d, f)
            if os.path.isfile(p) and not f.endswith(".쓰는중"):
                st = os.stat(p)
                낸["_raw/" + f] = (st.st_size, st.st_mtime_ns)
    return 낸


def _norm(p):
    return p.replace("\\", "/").lstrip("./")


def 입력해시(판, s, 단계들, 기록판, 명령, 덤뺄=()):
    """→ (해시, {경로: 해시}, raw 파일 수, 빠진 필수[]). 덤뺄 — 방금 돈 단계가 새로 쓴 부산출(기록 전이라 기록판에 아직 없다)."""
    줄, 쪽, 빠짐 = [], {}, []
    for p, 모드, 필수 in s.입력(판):
        if not 판.있나(p):
            if 필수:
                빠짐.append(p)
            쪽[_norm(p)] = None
            continue
        h = 가정해시(판.상(p), 모드) if 모드 in ("값", "값검토", "전체") else 파일해시(판.상(p))
        쪽[_norm(p)] = h
    nraw = 0
    if s.raw전체:
        뺄 = set()
        i = [x.이름 for x in 단계들].index(s.이름)
        for x in 단계들[i:]:
            try:
                뺄.update(_norm(p) for p in x.산출(판) + x.부산출(판))
            except Exception:                                          # noqa: BLE001
                pass
            뺄.update(_norm(p) for p in ((기록판.get("단계") or {}).get(x.이름) or {}).get("자동산출") or [])
        뺄.update(_norm(p) for p, _m, _f in s.입력(판))
        뺄.update(_norm(p) for p in 덤뺄)
        raw줄 = []
        for p in sorted(_raw목록(판)):
            if p in 뺄:
                continue
            raw줄.append("%s=%s" % (p, 파일해시(판.상(p))))
        nraw = len(raw줄)
        쪽["_raw/*"] = _sha("\n".join(raw줄).encode("utf-8"))
    도구파일 = os.path.join(판.도구, 명령[0]) if 명령 else None
    줄.append("도구=%s" % (파일해시(도구파일) if 도구파일 else "내부:%s" % s.이름))
    줄.append("명령=%s" % json.dumps(명령 or [], ensure_ascii=False))
    줄.append("판=%s" % json.dumps(판.키트판(), sort_keys=True, ensure_ascii=False))
    for k in sorted(쪽):
        줄.append("%s=%s" % (k, 쪽[k]))
    return _sha("\n".join(줄).encode("utf-8")), 쪽, nraw, 빠짐


def 산출해시(판, s):
    return {_norm(p): 파일해시(판.상(p)) for p in s.산출(판)}


# ══════════════════════════════════════════════════════════ 생성기 판

생성기표지 = "_본체판.json"          # 생성기를 본체에서 갈아 끼운 도구가 남기는 표지 — {"본체": 경로, "지문": 코드 지문, "적은때"}
_생성기뺄곳 = ("산출", "__pycache__")


def 생성기지문(곳):
    """생성기 폴더의 코드 지문 — 산출 · 캐시 · 표지를 뺀 모든 파일(상대 경로 + 내용)의 sha1 앞 16자. 폴더가 없으면 None."""
    if not 곳 or not os.path.isdir(곳):
        return None
    h = hashlib.sha1()
    for 뿌, 폴더들, 파일들 in os.walk(곳):
        폴더들[:] = sorted(d for d in 폴더들 if d not in _생성기뺄곳)
        for f in sorted(파일들):
            if f == 생성기표지 or f.endswith(".pyc"):
                continue
            p = os.path.join(뿌, f)
            h.update(os.path.relpath(p, 곳).replace("\\", "/").encode("utf-8") + b"\x00")
            with open(p, "rb") as g:
                h.update(hashlib.sha1(g.read()).digest())
    return h.hexdigest()[:16]


def 생성기곳(판):
    """짓기가 쓸 생성기 폴더 — 스캐폴드짓기와 같은 차례(--생성기 · 환경 변수 · 키트 안 · 키트 곁). 못 찾으면 None."""
    후보 = [판.옵션.get("생성기"), os.environ.get("DCF_생성기"), os.environ.get("DCF_GENERATOR"),
          os.path.join(판.폴더, "생성기"), os.path.join(os.path.dirname(판.폴더), "생성기")]
    for c in 후보:
        if c and os.path.isfile(os.path.join(c, "키트에넣기.py")):
            return os.path.abspath(c)
    return None


def 생성기점검(판):
    """짓기 앞 — 생성기 판을 본다 → 경보 글 목록(막지 않는다 · 짓기가 구조 지문으로 다시 막는다).

    ① 표지(`_본체판.json`)가 있으면 지금 코드 지문을 본체의 지금 지문(본체 폴더가 있을 때)이나 적힌 지문과 견준다 — 다르면 판이 다르다.
    ② 생성기와 키트가 이 가정에서 낸 구조 지문을 견준다 — 다르면 짓기가 「두 쪽의 셈이 갈렸습니다」(rc 1)로 멈춘다."""
    곳 = 생성기곳(판)
    if not 곳:
        return []
    경 = []
    표 = _읽기(os.path.join(곳, 생성기표지)) or {}
    지금 = 생성기지문(곳)
    본체 = 표.get("본체")
    if 본체 and os.path.isfile(os.path.join(본체, "키트에넣기.py")) and os.path.abspath(본체) != 곳:
        본지문 = 생성기지문(본체)
        if 본지문 != 지금:
            경.append("생성기 판이 본체와 다르다 — %s(%s) ≠ 본체 %s(%s) · 본체에서 다시 갈아 끼우거나 --생성기 로 본체를 준다"
                     % (곳, 지금, 본체, 본지문))
    elif 표.get("지문") and 표["지문"] != 지금:
        경.append("생성기가 본체에서 갈아 끼운 뒤 고쳐졌다 — %s(%s ≠ 적힌 %s)" % (곳, 지금, 표["지문"]))
    if 판.가정자료:
        경 += _구조지문견주기(판, 곳)
    return 경


def _구조지문견주기(판, 곳):
    """생성기의 `좌표지도.가정구조지문` 과 키트의 `좌표.가정구조지문` 을 같은 가정 · 같은 좌표 지도 자료로 견준다 → 경보 목록."""
    지도p = os.path.join(판.폴더, "DCF_워크북_좌표지도.json")
    if not os.path.isfile(지도p) or not os.path.isfile(os.path.join(곳, "좌표지도.py")):
        return []
    sys.path.insert(0, 판.도구)
    try:
        import 좌표 as _좌                                              # noqa: PLC0415
        import 스캐폴드짓기 as _짓                                       # noqa: PLC0415
        온 = _짓._새꼴(판.가정자료)
        if 온 is None:
            return []
        키트쪽 = _좌.가정구조지문(온, _읽기(지도p) or {})
    except Exception as e:                                             # noqa: BLE001 — 점검은 막지 않는다
        return ["생성기 구조 지문 점검을 못 했다(키트 쪽) — %s: %s" % (type(e).__name__, str(e)[:120])]
    finally:
        try:
            sys.path.remove(판.도구)
        except ValueError:
            pass
    with tempfile.TemporaryDirectory() as d:
        gp = os.path.join(d, "가정.json")
        with io.open(gp, "w", encoding="utf-8") as f:
            json.dump(온, f, ensure_ascii=False)
        코드 = ("import json,sys; sys.path.insert(0, sys.argv[1]); import 좌표지도; "
              "print(좌표지도.가정구조지문(json.load(open(sys.argv[2], encoding='utf-8')), json.load(open(sys.argv[3], encoding='utf-8'))))")
        환 = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1")
        if not 환.get("기간축곳") and os.path.isfile(os.path.join(판.도구, "기간축.py")):
            환["기간축곳"] = os.path.abspath(os.path.join(판.도구, "기간축.py"))   # 생성기가 이 키트의 기간축으로 열을 짓게
        try:
            r = subprocess.run([sys.executable, "-X", "utf8", "-c", 코드, 곳, gp, 지도p], cwd=곳, capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=120, env=환)
        except subprocess.TimeoutExpired:
            return ["생성기 구조 지문 점검이 120초 안에 끝나지 않았다"]
    낸 = (r.stdout or "").strip().splitlines()
    if r.returncode != 0 or not 낸:
        return ["생성기가 구조 지문을 내지 못했다(옛 판일 수 있다) — %s" % 끝줄((r.stderr or r.stdout or "").strip())[:160]]
    if 낸[-1].strip() != 키트쪽:
        return ["생성기와 키트의 구조 지문 셈이 갈린다 — 생성기 %s ≠ 키트 %s · 이대로 짓기는 rc 1 로 멈춘다(생성기 판이 키트와 다르다)"
                % (낸[-1].strip(), 키트쪽)]
    return []


def 실행(판, 단계들, 고른, 다시=(), 새로=False, 엄격=False, 보기=False, 잠금곳=None, 잠금대기=3600.0, 알림=print):
    """고른 단계를 사슬 차례로 돈다 → 종료 코드(멈춘 단계의 코드 · 다 돌았으면 0)."""
    다시 = set(다시 or ())
    if any(s.이름 == "짓기" for s in 고른) and not 판.옵션.get("생성기점검끔"):
        판.경보 += [w for w in 생성기점검(판) if w not in 판.경보]
    for w in 판.경보:
        알림("경보 — " + w)
    걸림 = 산출점검(단계들, 판)
    if 걸림:
        알림("입력 오류 — 판단 파일을 산출로 적은 단계 선언: " + " · ".join(걸림))
        return 입력오류
    로그곳 = os.path.join(판.폴더, 작업곳, "로그")
    if 보기:                                                          # 보기는 회사 폴더에 아무것도 쓰지 않는다
        return _실행(판, 단계들, 고른, 다시, 새로, 엄격, 보기, 잠금곳, 잠금대기, 알림, 로그곳)
    os.makedirs(로그곳, exist_ok=True)
    try:
        폴더잠금 = 잠금(os.path.join(판.폴더, 작업곳, "실행.lock"), 대기초=0, 누구="회차실행 %s" % 판.표기)
        폴더잠금.__enter__()
    except 잠금시간초과 as e:
        알림("입력 오류 — 이 회사 폴더에서 다른 회차실행이 돈다(%s)" % e)
        return 입력오류
    try:
        남 = 남의표식(판, 고른)                                       # 1.1.15 — 폴더 잠금을 잡은 뒤라 같은 폴더의 다른 회차실행은 없다
        if 남 and not 판.옵션.get("표식인수"):
            알림("입력 오류 — 돌 단계의 산출에 다른 회차의 표식이 있다(%s). 도구는 그 파일을 피해 다른 이름으로 쓰고 사슬은 옛 파일을 읽게 된다. "
                 "다른 폴더에서 복사해 온 회차면 `--표식인수` 로 이 회차의 산출로 받고, 아니면 그 파일을 `_기록/` 로 옮긴 뒤 돈다"
                 % " · ".join("%s(회차 %s)" % (p, r) for p, r in 남[:6]))
            return 입력오류
        if 남:
            표식인수(판, 남)
            알림("표식 인수 — %d개를 이 회차(%s)의 산출로 받았다: %s" % (len(남), 이회차(판), " · ".join(p for p, _r in 남[:6])))
        return _실행(판, 단계들, 고른, 다시, 새로, 엄격, 보기, 잠금곳, 잠금대기, 알림, 로그곳)
    finally:
        폴더잠금.__exit__()


def 이회차(판):
    """하위 도구가 보는 회차 이름 — 도구는 회차 폴더에서 돌므로 `DCF_회차`(`DCF_ROUND`)가 없으면 회차 폴더 이름(`산출물.회차`)."""
    import 산출물                                              # noqa: PLC0415
    v = (os.environ.get("DCF_회차") or os.environ.get("DCF_ROUND") or "").strip()
    return 산출물._안전한이름(v or os.path.basename(os.path.abspath(판.폴더)) or "기본")


def 남의표식(판, 고른):
    """1.1.15 — 고른 단계의 산출 · 부산출 가운데 다른 회차의 표식(`<파일>.표식.json` — `산출물` 규약)이 붙은 파일 → [(상대 경로, 표식의 회차)].
    다른 폴더에서 복사해 온 회차에서 생긴다(실측: 붓기가 옛 표식을 보고 `부음__<회차>.xlsx` 로 피해 썼는데 마감은 옛 `짓기/부음.xlsx` 를 읽었다)."""
    import 산출물                                              # noqa: PLC0415
    나 = 이회차(판)
    낸, 본 = [], set()
    for s in 고른:
        for p in list(s.산출(판)) + list(s.부산출(판)):
            k = _norm(p)
            if k in 본 or not 판.있나(p):
                continue
            본.add(k)
            m = 산출물._표식읽기(판.상(p))
            if isinstance(m, dict) and m.get("회차") and m.get("회차") != 나:
                낸.append((p, m.get("회차")))
    return 낸


def 표식인수(판, 남):
    """다른 회차 표식을 이 회차 것으로 고쳐 쓴다(쓴 시각은 지금 — 이어 도는 도구 프로세스가 시작하기 전이라 그 도구의 것으로 읽힌다)."""
    import 산출물                                              # noqa: PLC0415
    for p, _r in 남:
        m = dict(산출물.나의표식(), 회차=이회차(판), 폴더=판.폴더, 인수=_r)
        with io.open(판.상(p) + 산출물.표식꼬리, "w", encoding="utf-8") as f:
            f.write(json.dumps(m, ensure_ascii=False))


def _실행(판, 단계들, 고른, 다시, 새로, 엄격, 보기, 잠금곳, 잠금대기, 알림, 로그곳):
    발견수 = 0
    첫문제 = []                                                       # 보기 — 문제를 적고 끝까지 훑은 뒤 첫 코드를 돌려준다

    def 멈(s, rc, 글):
        if 보기:
            알림("%-10s 문제 rc=%s — %s" % (s.이름, rc, 글))
            첫문제.append(rc)
            return None
        return _멈춤(판, s, rc, 글, 알림)

    for s in 고른:
        기록판 = 판읽기(판)
        rec = (기록판.get("단계") or {}).get(s.이름)
        시작 = time.time()
        해당 = s.해당(판)
        if 해당:
            알림("%-10s 해당없음 — %s" % (s.이름, 해당))
            if not 보기:
                _기록(판, s, {"상태": "해당없음", "rc": 0, "끝줄": 해당, "시작": _지금(), "끝": _지금(), "초": 0.0})
            continue
        if s._명령 is None and s._내부 is None:
            알림("%-10s 해당없음 — 명령이 없다" % s.이름)
            continue
        try:
            명령 = s.명령(판)
        except Exception as e:                                         # noqa: BLE001
            명령, 문제 = None, "명령을 짓지 못했다: %s" % e
        else:
            문제 = None
            if 명령 and any(a is None for a in 명령):
                문제 = "명령에 빈 자리가 있다(가정 · 날짜 · 관할) — %s" % 명령
            elif 명령 and not os.path.isfile(os.path.join(판.도구, 명령[0])):
                문제 = "도구가 없다 — %s/%s" % (os.path.basename(판.도구), 명령[0])
            elif s.다시필요(판) and s.이름 not in 다시:
                문제 = "%s — 알고 덮으려면 --다시 %s" % (s.다시필요(판), s.이름)
        if 문제:
            r = 멈(s, 입력오류, 문제)
            if r is None:
                continue
            return r
        h, 쪽, nraw, 빠짐 = 입력해시(판, s, 단계들, 기록판, 명령)
        if 빠짐:
            r = 멈(s, 입력오류, "입력이 없다 — %s" % " · ".join(빠짐))
            if r is None:
                continue
            return r
        # 덮기 금지 — 판단 산출
        if s.이름 not in 다시:
            막 = []
            for p in s.보호(판):
                if not 판.있나(p):
                    continue
                표지 = s.보호표지(판, p)
                지난 = ((rec or {}).get("산출") or {}).get(_norm(p))
                if 표지:
                    막.append("%s(%s)" % (p, 표지))
                elif 지난 is None:
                    막.append("%s(이 실행기가 지은 기록이 없다)" % p)
                elif 지난 != 파일해시(판.상(p)):
                    막.append("%s(지은 뒤 고쳐졌다)" % p)
            if 막:
                글 = "판단 산출이 있다 — 덮지 않는다: %s · 덮으려면 --다시 %s" % (" · ".join(막), s.이름)
                알림("%-10s 보호 — %s" % (s.이름, 글))
                if not 보기:
                    _기록(판, s, {"상태": "보호", "rc": 0, "끝줄": 글[:220], "시작": _지금(), "끝": _지금(), "초": 0.0,
                                "입력해시": h, "보호산출": 산출해시(판, s)})
                continue
        # 건너뛰기 — 같은 입력으로 끝났고 산출이 남아 있다
        if (not 새로 and s.이름 not in 다시 and rec and rec.get("상태") in 끝난상태
                and not (엄격 and rec.get("rc") != 0)
                and h in (rec.get("입력해시"), rec.get("끝입력해시"))
                and all(판.있나(p) for p in s.산출(판))):
            알림("%-10s 건너뜀 — 같은 입력(%s · %s)" % (s.이름, h[:10], rec.get("끝")))
            continue
        if 보기:
            알림("%-10s 돈다 — %s%s" % (s.이름, " ".join(명령) if 명령 else "(내부)", " [엑셀 잠금]" if s.엑셀 else ""))
            continue
        # 돈다
        로그 = os.path.join(로그곳, "%s.txt" % s.이름)
        io.open(로그, "w", encoding="utf-8").write("# %s · %s · %s\n" % (s.이름, _지금(), " ".join(명령) if 명령 else "(내부)"))
        def 쓰기(t, 로그=로그):
            with io.open(로그, "a", encoding="utf-8") as f:
                f.write(t + "\n")
        시작때 = _지금()
        앞목록 = _raw목록(판)
        기다림 = 0.0
        try:
            잠 = 잠금(엑셀잠금곳(잠금곳), 대기초=잠금대기, 누구="%s · %s" % (판.표기, s.이름)) if s.엑셀 else None
            if 잠:
                기 = time.time()
                잠.__enter__()
                기다림 = time.time() - 기
            try:
                시작 = time.time()
                if s._앞:
                    s._앞(판)
                if s._내부:
                    rc = s._내부(판, 쓰기)
                else:
                    rc = 도구돌기(판, 명령, 로그=로그)["rc"]
                if s._뒤 and isinstance(rc, int):
                    rc = s._뒤(판, rc, 쓰기)
            finally:
                if 잠:
                    잠.__exit__()
        except 잠금시간초과 as e:
            return _멈춤(판, s, 입력오류, "엑셀 잠금을 잡지 못했다 — %s" % e, 알림)
        except KeyboardInterrupt:
            _멈춤(판, s, 입력오류, "중단(사용자)", 알림)
            raise
        except Exception as e:                                         # noqa: BLE001 — 실행기 안 단계(내부 · 앞 · 뒤)의 오류도 기록하고 멈춘다
            쓰기("%s: %s" % (type(e).__name__, e))
            return _멈춤(판, s, 입력오류, "단계 안에서 오류 — %s: %s" % (type(e).__name__, str(e)[:160]), 알림)
        초 = time.time() - 시작
        뒤목록 = _raw목록(판)
        자동 = sorted(p for p, v in 뒤목록.items() if 앞목록.get(p) != v and _norm(p) not in {_norm(x) for x in s.산출(판)})
        _해시기억.clear()
        h끝, _쪽2, _n2, _b2 = 입력해시(판, s, 단계들, 판읽기(판), 명령, 덤뺄=자동)
        글 = io.open(로그, encoding="utf-8", errors="replace").read()
        허용 = (0,) if 엄격 else s.허용
        상태 = ("통과" if rc == 0 else "발견") if rc in 허용 else ("시간초과" if rc == "시간초과" else ("미구현" if rc == 미구현 else "실패"))
        rec새 = {"상태": 상태, "rc": rc, "시작": 시작때, "끝": _지금(), "초": round(초, 1), "잠금기다림초": round(기다림, 1), "판": 판.키트판(),
                "입력해시": h, "끝입력해시": h끝, "입력": 쪽, "raw파일수": nraw, "산출": 산출해시(판, s),
                "산출해시": _sha(json.dumps(산출해시(판, s), sort_keys=True).encode("utf-8")), "자동산출": 자동,
                "끝줄": 끝줄(글), "로그": os.path.relpath(로그, 판.폴더).replace("\\", "/"), "명령": 명령 or ["(내부)"]}
        _기록(판, s, rec새)
        알림("%-10s %s rc=%s %6.1f초  %s" % (s.이름, 상태, rc, 초, rec새["끝줄"]))
        if rc not in 허용:
            알림("멈춤 — %s (rc %s) · 로그 %s" % (s.이름, rc, rec새["로그"]))
            return rc if isinstance(rc, int) else 발견
        if rc != 0:
            발견수 += 1
    if 첫문제:
        return 첫문제[0]
    if 발견수:
        알림("다 돌았다 — 허용된 발견 %d단계(게이트가 다시 본다)" % 발견수)
    return 통과


def _기록(판, s, rec):
    def 고침(d):
        지난 = d["단계"].get(s.이름) or {}
        if rec.get("상태") in ("보호", "해당없음") and 지난.get("상태") in 끝난상태:
            지난 = dict(지난, 마지막판정=rec)                          # 끝난 기록은 두고 판정만 덧붙인다
            d["단계"][s.이름] = 지난
        else:
            d["단계"][s.이름] = rec
        d["이력"].append({"단계": s.이름, "상태": rec.get("상태"), "rc": rec.get("rc"), "시작": rec.get("시작"),
                        "초": rec.get("초"), "입력해시": (rec.get("입력해시") or "")[:16]})
    판고치기(판, 고침)


def _멈춤(판, s, rc, 글, 알림):
    알림("%-10s 실패 rc=%s — %s" % (s.이름, rc, 글))
    _기록(판, s, {"상태": "실패", "rc": rc, "끝줄": 글[:220], "시작": _지금(), "끝": _지금(), "초": 0.0})
    알림("멈춤 — %s (rc %s)" % (s.이름, rc))
    return rc


# ══════════════════════════════════════════════════════════ 기록 · 상태 · 목록

def 판단기록(판, 단계이름, 토큰, 호출, 초, 기록자, 모델=None, 메모=None):
    """판단 구간 한 줄을 진행판 `판단구간[]` 에 더한다 → 그 줄."""
    for 이름, v in (("토큰", 토큰), ("호출", 호출)):
        if v is None or int(v) < 0:
            raise 입력문제("%s 은(는) 0 이상의 정수다" % 이름)
    if 초 is None or float(초) < 0:
        raise 입력문제("초 는 0 이상의 수다")
    if not 단계이름 or not 기록자:
        raise 입력문제("단계 · 기록자 가 있어야 한다")
    줄 = {"단계": 단계이름, "토큰": int(토큰), "호출": int(호출), "초": round(float(초), 1), "기록자": 기록자, "때": _지금(),
         "키트판": 판.키트판().get("ADDER")}
    if 모델:
        줄["모델"] = 모델
    if 메모:
        줄["메모"] = 메모
    판고치기(판, lambda d: d["판단구간"].append(줄))
    return 줄


def 상태글(판, 단계들):
    d = 판읽기(판)
    L = ["진행판 — %s · %s · T %s · F %s · 결산월 %s" % (판.표기, 판.국가, 판.T, 판.F, 판.결산월)]
    for s in 단계들:
        r = d["단계"].get(s.이름)
        if not r:
            if s.기본:
                L.append("  %-10s -" % s.이름)
            continue
        L.append("  %-10s %-6s rc=%-4s %7s초  %s  %s" % (s.이름, r.get("상태"), r.get("rc"), r.get("초"), r.get("끝") or "", r.get("끝줄") or ""))
    합 = {}
    for x in d["판단구간"]:
        a = 합.setdefault(x["단계"], [0, 0, 0.0, 0])
        a[0] += x["토큰"]; a[1] += x["호출"]; a[2] += x["초"]; a[3] += 1
    if 합:
        L.append("판단 구간")
        for k, (t, c, sec, n) in 합.items():
            L.append("  %-10s 토큰 %s · 호출 %d · %.0f초 · %d줄" % (k, format(t, ","), c, sec, n))
    기 = sum(r.get("초") or 0 for r in d["단계"].values() if isinstance(r, dict))
    L.append("도구 구간 합 %.0f초 · 판단 구간 합 %.0f초" % (기, sum(x["초"] for x in d["판단구간"])))
    return "\n".join(L)


재실행차례 = (
    ("판 올리기", "`/adder:키트갱신`(또는 키트 사본 갈기) — 스크립트 · 생성기를 새 판으로. 회사 폴더의 가정 · 원고 · _raw 는 그대로"),
    ("원천 리스구분(미국 · US GAAP)", "A2 보정본이 보호돼 원천 단계가 다시 돌지 않는다 — `sec_원천.py` 를 다른 출력으로 돌려 「리스구분」 칸만 보정본에 옮긴 뒤 `리스판정.py <가정> --고치기`"),
    ("βU 재료", "`βU다시셈.py 축소 <T 창 산출> --비교 <F 창 산출> --가정 <가정>`(창 이동 폭 · 서열 하한 · 미국 대상 자체) — 판단으로 받으면 가정 3번 10 · 근거에. "
               "βU 재료가 여럿이면 `구조.할인.유사기업파일` 에 쓴 판을 적는다(없으면 창 끝 날짜로 고른다)"),
    ("영구기간 자본비용 · 안정 성장 정합(1.1.5)", "`안정성장.py <가정>` 으로 영구기간 βU · D/E 세 판(업종 성숙 평균 · Levered Beta 1.0 · 수렴 없음)을 보고, 기본 규칙을 받으면 "
                                         "`--쓰기 업종성숙`(WACC 부터 전면 — 자체검사 54). 재투자 방향 요건이 서면 판단대장에 「재투자 방향」 줄(55), 연장 트리거 · 주식보상 · "
                                         "적자 부문 경보는 원고 관측 또는 검토의견 R-171 ~ R-173(56 ~ 58)"),
    ("RONIC 정의 · 레짐 · 고객 경로(1.1.6)", "`안정성장.py <가정>` 의 ⑦ RONIC 정합이 경보면 판단대장에 「RONIC 기준」 줄(어느 투하자본 기준으로 정했나 — 60). "
                                        "레짐 기대값을 실을 회차는 원고 `관측.레짐`(묶음 · 확률 규칙) → `레짐.py <가정>`(61). 고객 수 · 고객당 매출이 공시된 회차는 최상위 "
                                        "`고객경로` → `고객경로.py <가정> --쓰기`(원가가 판매량에 연동하면 `--원가 매출` · 가리키는 자리는 `--걷기` — 62) → 짓기부터"),
    ("레짐 기저율 밖 · 첫 장 지렛대 · 그림 상한(1.1.7)", "레짐 표를 실은 회차는 `레짐.py <가정>` 을 다시(기저율 밖이면 확률 · 기대값 줄이 빠지고 사실만 · 구간 · 넓힌 집단). "
                                              "격자 · 결합 재료를 다시 지은 뒤 초안 — 첫 장 「갈림」 줄이 대안 사양까지 같은 잣대로 잰 폭 1위를 고르고(선언이 좁으면 선언한 가정의 폭을 나란히), "
                                              "본편 그림이 상한(정합설정 「그림.본편상한」)을 넘으면 부록으로 옮긴다. 손 편집본이 옛 결론 · 그림 자리를 쥐고 있으면 `--다시 편집`"),
    ("원천 조립 태그 · 넣기 · 지렛대 그림(1.1.8)", "원천 조립(국내 `dart_원천` · 미국 `sec_원천`)이 흔한 계정 태그 · 회계연도 말 재무기준일을 새로 안다 — A2 보정본은 보호되니 "
                                             "그대로 두고, 원천부터 다시 도는 회차만 새 조립을 본다(미국 Other current assets 는 13 → 15 · 값 영향). 원고 묶음에 "
                                             "`자본비용` · `관측.실측분포` 를 썼으면 `--다시 넣기`(종전에는 넣기가 버렸다). 초안을 다시 지으면 지렛대 그림이 본편에 남는다"),
    ("52/53주 회계연도 · βU 재료(1.1.9)", "재무기준일이 월말이 아닌 52/53주 회사는 기간 축이 가장 가까운 월말로 선다 — 가정의 소수 개월 열 키(8.9M26A 따위)를 "
                                     "`가정열맞춤.py <가정> --옛ID` 로 새 ID(9M26A · 4Q26E)로 옮긴 뒤 `--새로 --부터 짓기`(결산월이 어긋나면 기간 축이 오류로 바른 결산월을 알린다). "
                                     "월말 재무기준일 회사는 축 · 값이 그대로다. 레터 Peer 표는 채택 βU 와 같은 값을 내는 재료를 고른다(초안부터). "
                                     "1.1.20 — 열을 옮기면 엔진으로 셈해 둔 재료(`Narrative.자료` · 원고가 「파일:」 로 부르는 `_raw/<이름>.json` — 대안 · 반대 논거의 "
                                     "주당가치 따위)는 옛 열 · 옛 엔진 값이다. 도구가 `_raw/열옮김.json` 에 낡음을 표시하니 지금 가정으로 다시 셈해 넣는다"
                                     "(그대로 두면 자체검사 65 가 막는다 · 열 · 엔진과 무관한 재료는 `--재료확인 <키>`)"),
    ("추정 블록의 꼴(1.1.14)", "`추정근거.py <가정>` → 원고 갈래가 블록 원고를 다시 쓴다(요건판 5 — 옛 꼴 원고는 넣기가 누락으로 멈춘다) → 넣기 → 초안 → 교열 두 회. "
                              "앞 판의 편집 목록(`_raw/편집목록.json`)은 옛 꼴 초안의 조립 문장을 가리켜 새 초안에서 「안 됨」 으로 편집을 멈춘다 — "
                              "`_기록/` 로 옮겨 두고 빈 목록(`[]`)에서 교열을 다시 돈다"),
    ("옛 판 빈 자리(1.1.19)", "앞 판 회차는 새 판이 읽는 칸이 비어 있을 수 있다 — 부록 B 「채택」 줄의 근거 · `관측.외부범위` 줄의 「독립」 · "
                          "`WACC근거` 의 템플릿 자리표시 · 원고 요건이 까닭을 묻는 줄의 근거 셋째 칸. 아래 「할 일」 이 자리만 알린다(값 · 글은 짓지 않는다 — "
                          "판단대장 · 조사 산출의 글을 옮겨 채운다). 교열 단계는 고리 두 회 뒤 남은 목록 전이면 통과다(남은 목록은 편집 뒤)"),
    ("넣기 차례", "앞 판에서 게이트를 맞추며 가정 쪽에서 고친 원고가 있으면 `레터원고.py 넣기 --거꾸로` 로 묶음에 먼저 옮기고 묶음을 고친 뒤 `--넣기방식 묶음우선`"),
    ("주가 · 지수", "날짜 둘 회차는 `--단계 주가,지수` 를 신호 앞에 — 주가를 다시 받았으면 초안 · 인터랙티브 · 게이트를 그 뒤에 다시"),
    ("짓기부터", "생성기 · 명세 지문이 바뀐 판이면 `--새로` 로 짓기부터(붓기 · 마감은 검토의견만 고쳐도 다시 돈다 — 1.1.4)"),
    ("편집", "앞 판의 손 편집본(`레터_편집.md`)은 판단 산출로 보호된다 — 새 초안에 편집 목록을 다시 대려면 `--다시 편집`(옛 편집본은 따로 둔다)"),
    ("게이트", "판단 변경 전파 관문 — 앞 판 장부(`레터_초안.장부.옛.json` · 레터.py 가 남긴다)의 바뀐 값이 원고 · 검토의견에 남았으면 막는다. "
             "원고의 글자 숫자는 「{키|꼴}」 자리표시로 바꾼다. 버린 판단의 글은 `관측.판단변경[].옛` 에 적어 두면 같은 관문이 본다"),
)


def 재실행안내(폴더, 가정경로=None):
    """1.1.4(R2 · R20 · P-08 · P-11) — 앞 판으로 완주한 회차를 새 판으로 다시 돌 때의 차례와, 이 폴더에서 걸릴 자리 → 글 줄 목록."""
    줄 = ["재실행 차례 — 앞 판으로 완주한 회차(판단 산출 · 손 편집이 있는 폴더)"]
    for i, (이름, 글) in enumerate(재실행차례, 1):
        줄.append("  %d. %s — %s" % (i, 이름, 글))
    본 = []
    if os.path.exists(os.path.join(폴더, "레터_편집.md")):
        본.append("레터_편집.md 가 있다 — 새 초안에는 `--다시 편집`(편집 목록 `_raw/편집목록.json` 이 있으면 그것으로)")
    피 = glob.glob(os.path.join(폴더, "_raw", "peers", "βU_*.json"))
    if len(피) > 1:
        try:
            import 피어경로                                     # noqa: PLC0415
            g = _읽기(가정경로) if 가정경로 else None
            r = 피어경로.βU재료고르기(폴더, g if isinstance(g, dict) else None)
            본.append("βU 재료 %d판 — 레터 · 갭해석이 고르는 판: %s(%s)" % (len(피), r["상대"] if r else "없음", r["까닭"] if r else "-"))
        except Exception:                                    # noqa: BLE001
            pass
    try:
        g = _읽기(가정경로) if 가정경로 else None
        if isinstance(g, dict) and (((g.get("구조") or {}).get("할인") or {}).get("영구WACC") or "예측과같음") == "예측과같음":
            본.append("영구기간 자본비용이 예측기간과 같다(수렴 없음) — 1.1.5 기본 규칙은 업종 성숙 평균(`안정성장.py <가정> --쓰기 업종성숙` · 자체검사 54)")
    except Exception:                                        # noqa: BLE001
        pass
    try:
        g = _읽기(가정경로) if 가정경로 else None
        if isinstance(g, dict):
            a = _읽기(os.path.join(폴더, "_raw", "안정성장.json")) or {}
            if (a.get("RONIC정합") or {}).get("경보"):
                본.append("영구 RONIC 과 예측기간의 투하자본 정의가 갈린다 — 판단대장 「RONIC 기준」 줄(1.1.6 · 자체검사 60)")
            import 고객경로 as _고                             # noqa: PLC0415
            for 선 in _고.선언들(g):
                x = _고._구분(g, int(선["구분"])) or {}
                if not (x.get("경로") == "수준" and x.get("판매량꼴") == "저량"):
                    본.append("고객경로 구분 %s 선언이 있는데 엔진 칸에 옮기지 않았다 — `고객경로.py <가정> --쓰기`(1.1.6 · 자체검사 62)" % 선["구분"])
    except Exception:                                        # noqa: BLE001
        pass
    if glob.glob(os.path.join(폴더, "*.장부.옛.json")):
        본.append("옛 장부가 있다 — 게이트 ⑳ 판단 변경 전파 관문이 원고 · 검토의견의 옛 값을 본다")
    try:                                                     # 1.1.20 — 열을 옮긴 뒤 다시 셈하지 않은 재료(`가정열맞춤` 의 낡음 표시)
        g = _읽기(가정경로) if 가정경로 else None
        import 가정열맞춤 as _열                               # noqa: PLC0415
        낡 = _열.낡은재료(g if isinstance(g, dict) else None, 폴더)
        if 낡:
            본.append("열을 옮긴 뒤 다시 셈하지 않은 재료 %d개를 원고가 부른다 — %s. 옛 열 · 옛 엔진 값이니 지금 가정으로 다시 셈해 넣는다"
                      "(재료를 지은 스크립트를 다시 돈 뒤 `--다시 넣기` · 초안부터). 열 · 엔진과 무관하면 "
                      "`가정열맞춤.py <가정> --재료확인 <키>`(자체검사 65)" % (len(낡), " · ".join(x["키"] for x in 낡[:8])))
    except Exception:                                        # noqa: BLE001
        pass
    try:
        g = _읽기(가정경로) if 가정경로 else None
        if isinstance(g, dict) and ((g.get("메타") or {}).get("재무기준일") not in (None, "", (g.get("메타") or {}).get("평가기준일"))) \
                and not os.path.exists(os.path.join(폴더, "레터_주가.csv")):
            본.append("날짜 둘 회차인데 레터_주가.csv 가 없다 — `--단계 주가` 를 신호 앞에")
    except Exception:                                        # noqa: BLE001
        pass
    if 본:
        줄.append("이 폴더에서 볼 것")
        줄 += ["  · " + x for x in 본]
    try:
        할 = 빈자리할일(폴더, 가정경로)
    except Exception as e:                                   # noqa: BLE001
        할 = ["빈 자리를 다 보지 못했다 — %s: %s" % (type(e).__name__, ("%s" % e)[:120])]
    if 할:
        줄.append("할 일 — 옛 판 회차의 빈 자리(값 · 글은 짓지 않는다 — 자리만 알린다)")
        줄 += ["  · " + x for x in 할]
    return 줄


# 자체검사 할인율 ⑬(1.1.15)과 같은 꼴 — 템플릿의 「(출처 — …)」 · 「(기준일 — …)」 · 「(비고)」
_틀자리꼴 = re.compile(r"\((?:출처|기준일)\s*—[^)]*\)|^\(비고(?:\s*—[^)]*)?\)$")


def _묶음들(폴더):
    """원고 묶음(`_raw/레터원고/*.json` — 「_」 로 시작하는 파일은 뺀다 · 넣기와 같은 고르기) → [(파일 이름, dict)]."""
    낸 = []
    for p in sorted(glob.glob(os.path.join(폴더, "_raw", "레터원고", "*.json"))):
        if os.path.basename(p).startswith("_"):
            continue
        d = _읽기(p)
        if isinstance(d, dict):
            낸.append((os.path.basename(p), d))
    return 낸


def 빈자리할일(폴더, 가정경로=None):
    """1.1.19 — 앞 판으로 완주한 회차에서 새 판이 읽는 칸이 빈 자리 → [글]. 값 · 글을 짓지 않고 자리만 알린다.
      ① 부록 B 「채택」 줄의 근거(가정 · 원고 묶음 · 레터부록의 `자본비용` — 대안이 있는데 `채택.근거` 가 비면 게이트 ⑱ 이 막는다)
      ② `관측.외부범위` 줄의 「독립」(비우면 추정 근거표가 독립 대조로 센다 — 가정 · 원고 묶음)
      ③ `WACC근거` 의 템플릿 자리표시(Unlevered Beta 10 은 언제나 · 다른 줄은 사실 글과 섞였을 때 — 자체검사 ⑬ 과 같은 꼴)
      ④ 추정 근거표(`_raw/추정근거.json` — 지금 가정과 해시가 같을 때)의 원고 요건 줄(무게 한 문단 이상) 가운데 까닭이 빈 줄 ·
         근거 칸이 없는 규칙 줄 · 범위 판정을 하지 않은 줄(정의 다름 · 한 점) · 근거 칸 글 안의 숫자 알림. 해시가 다르거나 없으면 다시 지으라고 알린다"""
    g = _읽기(가정경로) if 가정경로 else None
    if not isinstance(g, dict):
        return []
    낸 = []
    묶 = _묶음들(폴더)
    # ① 자본비용 「채택」 근거 — 묶음에 자본비용이 있으면 넣기가 그것을 가정으로 옮긴다
    자 = next(((n, d["자본비용"]) for n, d in 묶 if isinstance(d.get("자본비용"), dict)), None)
    if 자 is None and isinstance(g.get("자본비용"), dict):
        자 = (os.path.basename(가정경로), g["자본비용"])
    if 자 is None:
        try:
            import 자본비용옮기기 as _자                        # noqa: PLC0415
            부 = _자.부록읽기(가정경로).get("자본비용")
            if isinstance(부, dict):
                자 = ("레터부록.json", 부)
        except Exception:                                    # noqa: BLE001
            pass
    if 자 is not None:
        채 = 자[1].get("채택")
        if not (isinstance(채, dict) and ("%s" % (채.get("근거") or "")).strip()):
            낸.append("부록 B 「채택」 줄 근거가 비었다(%s `자본비용.채택` %s) — 채택 사양 · 근거 글(판단대장의 자본비용 판단)을 적는다(게이트 ⑱)"
                     % (자[0], "없음" if not isinstance(채, dict) else "의 근거 빔"))
    # ② 외부 범위 「독립」
    없는 = []
    for n, d in [(os.path.basename(가정경로), g)] + 묶:
        for i, x in enumerate(((d.get("관측") or {}) if isinstance(d.get("관측"), dict) else {}).get("외부범위") or []):
            if isinstance(x, dict) and not isinstance(x.get("독립"), bool):
                없는.append("%s 관측.외부범위[%d] %s" % (n, i, ("%s" % (x.get("항목") or x.get("이름") or ""))[:30]))
    if 없는:
        낸.append("`관측.외부범위` 줄에 「독립」 이 없다 — 그 범위를 가정을 정하는 데 썼으면 거짓 · 따로 잰 대조면 참(%s)" % " · ".join(없는[:4]))
    # ③ WACC근거 템플릿 자리표시
    for 번, v in sorted(((g.get("WACC근거") or {}) if isinstance(g.get("WACC근거"), dict) else {}).items(), key=lambda kv: "%s" % kv[0]):
        칸 = [("%s" % x).strip() for x in (v if isinstance(v, (list, tuple)) else [v]) if x]
        걸 = [c for c in 칸 if _틀자리꼴.search(c)]
        섞임 = [c for c in 걸 if len(_틀자리꼴.sub("", c).strip(" /—-·")) > 0]
        if 걸 and ("%s" % 번 == "10" or 섞임):
            넷 = list(v) if isinstance(v, (list, tuple)) else [v]
            빈칸 = "" if len(넷) >= 3 and ("%s" % (넷[2] or "")).strip() else " · 셋째 칸(까닭) 빔"
            낸.append("`WACC근거.%s` 에 템플릿 자리표시 「%s」%s — 판단대장 · `자본비용.채택.근거` 의 글을 옮겨 근거 넷(관측 · 기준일 · 까닭 · 비고)을 "
                     "사실로 채운다(채우는 도구 없음 · 값은 그대로)" % (번, _틀자리꼴.search((섞임 or 걸)[0]).group(0)[:30], 빈칸))
    # ④ 추정 근거표
    낸 += _근거표할일(폴더, 가정경로, g)
    return 낸


def _근거표할일(폴더, 가정경로, g):
    p = os.path.join(os.path.dirname(os.path.abspath(가정경로)), "_raw", "추정근거.json")
    근 = _읽기(p)
    다시 = "`추정근거.py %s` 를 다시 돌려 근거표의 빈 까닭 · 범위 판정 · 근거 칸 숫자 알림을 본다" % os.path.basename(가정경로)
    if not isinstance(근, dict):
        return ["추정 근거표(_raw/추정근거.json)가 없다 — " + 다시]
    try:
        import 레터 as _L                                     # noqa: PLC0415
        if 근.get("가정해시") != _L._해시(g):
            return ["추정 근거표가 지금 가정과 다르다(가정 해시) — " + 다시]
    except Exception:                                        # noqa: BLE001
        pass
    낸 = []
    빔, 규칙 = [], []
    for b in 근.get("블록") or []:
        for z in b.get("줄") or []:
            if (z.get("무게") or {}).get("표지") not in ("두문단", "한문단"):
                continue
            출 = z.get("까닭출처")
            if 출 is None:                                    # 1.1.19 전 근거표 — 빈자리 · 가정 종류로 가른다
                if z.get("까닭"):
                    출 = "근거 칸"
                else:
                    출 = "빔" if any(x.get("번호") and x.get("종류") != "규칙" for x in z.get("가정") or []) else "근거 칸 없음"
            if 출 == "빔":
                빔.append(z.get("id"))
            elif 출 == "근거 칸 없음":
                규칙.append(z.get("id"))
    if 빔:
        낸.append("원고 요건 줄의 근거 셋째 칸(까닭)이 비었다 — %s(근거 칸에 까닭 글을 옮긴다 · 넣기가 누락으로 멈춘다)" % " · ".join(빔[:8]))
    if 규칙:
        낸.append("근거 칸이 없는 규칙 · 장부 줄이 원고 요건에 선다 — %s(문단이 규칙을 쓴 까닭을 적는다 · 근거 칸 글이 없다)" % " · ".join(규칙[:8]))
    없음 = 근.get("범위판정없음") or []
    if 없음:
        낸.append("실적 범위를 판정하지 않은 줄 %d(정의 다름 · 한 점 — 「범위 밖」 을 쓰지 않는다): %s" % (
            len(없음), " · ".join("%s %s" % (x.get("줄"), x.get("대조")) for x in 없음[:6])))
    알 = 근.get("알림") or []
    if 알:
        낸.append("근거 칸 글 안의 숫자가 지금 값과 다른 자리 %d(값은 그대로 · 원고는 장부 키로 부른다 — 근거 글을 고칠지 본다): %s" % (
            len(알), " / ".join(알[:3])))
    return 낸


def 목록글(단계들):
    L = []
    for s in 단계들:
        L.append("%-10s %s%s%s%s" % (s.이름, "" if s.기본 else "[고를 때만] ", "[엑셀 잠금] " if s.엑셀 else "",
                                    ("[별명 %s] " % "·".join(s.별명)) if s.별명 else "", s.설명))
    return "\n".join(L)


# ══════════════════════════════════════════════════════════ 명령줄

def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--기록" in argv:                                               # 깃발 꼴 — `--기록 <단계>` = `기록 --단계 <단계>`
        i = argv.index("--기록")
        if i + 1 >= len(argv):
            print("입력 오류 — --기록 뒤에 단계 이름")
            return 입력오류
        argv = ["기록", "--단계", argv[i + 1]] + argv[:i] + argv[i + 2:]
    if "--꾸러미" in argv:
        argv = [x for x in argv if x != "--꾸러미"] + ["--단계", "꾸러미"]
    ap = argparse.ArgumentParser(allow_abbrev=False, description="회차실행 — 결정적 사슬을 단계 이름으로 고르거나 차례로 돈다")
    ap.add_argument("명령", nargs="?", default="돌기", choices=("돌기", "목록", "상태", "기록", "재실행"))
    ap.add_argument("--폴더", default=".", help="회사 폴더(키트가 펴진 곳 · 기본 지금 폴더)")
    ap.add_argument("--가정", default=None)
    ap.add_argument("--국가", default=None, type=str.upper, choices=("KR", "US"))
    ap.add_argument("--미국", action="store_true", help="--국가 US 와 같다")
    ap.add_argument("--평가기준일", default=None, help="평가기준일 T YYYY-MM-DD — 비우면 가정")
    ap.add_argument("--재무기준일", default=None, help="재무기준일 F YYYY-MM-DD — 비우면 가정(없으면 F = T)")
    ap.add_argument("--결산월", type=int, default=None)
    ap.add_argument("--해수", type=int, default=None, help="A2 실적 회계연도 열 수 — 비우면 가정의 기간.실적연도수")
    ap.add_argument("--표기", default=None, help="파일 이름의 회사 표기 — 비우면 가정의 메타.회사명")
    ap.add_argument("--종목", default=None, help="국내 6자리 · 미국 티커(주가 · 캐시 넣기)")
    ap.add_argument("--종가", type=float, default=None, help="역산 단계의 가격")
    ap.add_argument("--단계", default=None, help="쉼표 — 고른 단계만(사슬 차례로)")
    ap.add_argument("--부터", default=None)
    ap.add_argument("--까지", default=None)
    ap.add_argument("--다시", nargs="+", default=[], help="판단 산출을 알고 덮는다 — 이 단계들만(같은 입력이어도 돈다)")
    ap.add_argument("--새로", action="store_true", help="같은 입력이어도 다시 돈다(판단 산출은 덮지 않는다)")
    ap.add_argument("--엄격", action="store_true", help="발견(1)도 멈춘다")
    ap.add_argument("--보기", action="store_true", help="돌지 않고 할 일만")
    ap.add_argument("--넣기방식", default=None, choices=("기본", "거꾸로", "가정우선", "묶음우선"))
    ap.add_argument("--붓기경보무시", action="store_true")
    ap.add_argument("--생성기", default=None, help="스캐폴드 생성기 폴더(환경변수 DCF_GENERATOR 로 넘긴다)")
    ap.add_argument("--표식인수", action="store_true",
                    help="돌 단계의 산출에 다른 회차의 표식이 있으면(다른 폴더에서 복사해 온 회차) 그 표식을 이 회차 것으로 고쳐 쓰고 돈다")
    ap.add_argument("--PDF도구", default=None, help="레터 HTML → PDF 도구(.py) — 비우면 환경변수 DCF_PDF도구")
    ap.add_argument("--잠금곳", default=None, help="엑셀 잠금 파일 폴더")
    ap.add_argument("--잠금대기", type=float, default=3600.0, help="엑셀 잠금 기다림(초)")
    ap.add_argument("--상한분", type=float, default=60.0, help="단계 하나의 벽시계 상한(분)")
    ap.add_argument("--도구", default=None, help="도구 폴더(기본 <폴더>/스크립트)")
    ap.add_argument("--토큰", type=int, default=None)
    ap.add_argument("--호출", type=int, default=None)
    ap.add_argument("--초", type=float, default=None)
    ap.add_argument("--기록자", default=None)
    ap.add_argument("--모델", default=None)
    ap.add_argument("--메모", default=None)
    a = ap.parse_args(argv)
    단계들 = 단계표()
    if a.명령 == "목록":
        print(목록글(단계들))
        return 통과
    폴더 = os.path.abspath(a.폴더)
    if a.명령 == "재실행":                                    # 1.1.4 — 앞 판 회차를 새 판으로 다시 돌 때의 차례(돌지 않는다)
        가 = a.가정 or next((p for p in sorted(glob.glob(os.path.join(폴더, "가정_*.json"))) if not re.search(r"예시|템플릿", os.path.basename(p))), None)
        print("\n".join(재실행안내(폴더, 가)))
        return 통과
    if os.path.isdir(os.path.join(폴더, "배포틀")) and os.path.isdir(os.path.join(폴더, "회귀기준선")):
        print("입력 오류 — 키트 본체에서는 돌지 않는다(회사 폴더에 키트를 펴고 거기서 돈다)")
        return 입력오류
    try:
        p = 판(폴더, 가정=a.가정, 국가=("US" if a.미국 else a.국가), 평가기준일=a.평가기준일, 재무기준일=a.재무기준일, 결산월=a.결산월,
              표기=a.표기, 종목=a.종목, 종가=a.종가, 해수=a.해수, 도구=a.도구,
              넣기방식=a.넣기방식, 붓기경보무시=a.붓기경보무시, 생성기=a.생성기, PDF도구=a.PDF도구, 상한초=a.상한분 * 60,
              표식인수=a.표식인수)
    except 입력문제 as e:
        print("입력 오류 — %s" % e)
        return 입력오류
    if a.명령 == "기록":
        try:
            줄 = 판단기록(p, a.단계, a.토큰, a.호출, a.초, a.기록자, a.모델, a.메모)
        except (입력문제, ValueError, TypeError) as e:
            print("입력 오류 — %s" % e)
            return 입력오류
        print("기록했다 — 판단구간 %s" % json.dumps(줄, ensure_ascii=False))
        return 통과
    if a.명령 == "상태":
        print(상태글(p, 단계들))
        return 통과
    if not os.path.isdir(p.도구):
        print("입력 오류 — 도구 폴더가 없다(회사 폴더에 키트가 펴져 있나): %s" % os.path.basename(p.도구))
        return 입력오류
    try:
        고른 = 고르기(단계들, [x.strip() for x in a.단계.split(",") if x.strip()] if a.단계 else None, a.부터, a.까지)
        모르는다시 = [x for x in a.다시 if x not in {s.이름 for s in 단계들}]
        if 모르는다시:
            raise 입력문제("--다시 의 모르는 단계: %s" % " · ".join(모르는다시))
    except 입력문제 as e:
        print("입력 오류 — %s" % e)
        return 입력오류
    for x in a.다시:                                                  # --다시 준 단계는 고른 것에 든다
        if x not in {s.이름 for s in 고른}:
            고른 = [s for s in 단계들 if s in 고른 or s.이름 == x]
    print("회차실행 — %s · %s · T %s · F %s · 결산월 %s · 단계 %d%s" % (p.표기, p.국가, p.T, p.F, p.결산월, len(고른), " (보기)" if a.보기 else ""))
    return 실행(p, 단계들, 고른, 다시=a.다시, 새로=a.새로, 엄격=a.엄격, 보기=a.보기, 잠금곳=a.잠금곳, 잠금대기=a.잠금대기)


if __name__ == "__main__":
    sys.exit(main())

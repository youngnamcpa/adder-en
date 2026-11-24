# -*- coding: utf-8 -*-
"""준비점검 — 이 컴퓨터에서 키트(ADDER)를 돌릴 준비가 됐는지 한 번에 본다(설계: 연구/준비점검_mcp_설계_20261023.md 3절).

    python -X utf8 스크립트/준비점검.py                       # 열일곱 항목을 끝까지 보고 표 한 장
    python -X utf8 스크립트/준비점검.py --언어 en             # 영문 표 · 안내(templates/en)
    python -X utf8 스크립트/준비점검.py --설치                # 미비한 키(DART · SEC · 선택 셋)를 하나씩 묻고 저장(터미널에서만 — 화면에 보이지 않는다)
    python -X utf8 스크립트/준비점검.py --저장 OPENDART_API_KEY   # 값 하나를 받아 저장(표준 입력 · getpass — 인자로 받지 않는다)
                                                              # 받는 이름: OPENDART_API_KEY · SEC_CONTACT_EMAIL · LAW_OC · ECOS_API_KEY · KOSIS_API_KEY
    python -X utf8 스크립트/준비점검.py --망없이 --엑셀안봄    # 접속 시험 · 엑셀 띄우기 없이(시험용)

점검 열일곱(멈추지 않고 끝까지 돈 뒤 표 한 장)
  ① 파이썬 ≥ 3.11(필수)  ② requests · openpyxl(필수)  ③ 엑셀 계산 — Excel + pywin32 또는 formulas(선택)  ④ Excel 프로그램(선택 · Windows 에서
  따로 띄운 인스턴스만 열고 닫는다 — 열어 둔 엑셀에 붙지 않는다)  ⑤ Edge · Chrome · ffmpeg(선택)  ⑥ OPENDART_API_KEY(한국 회사면 필요)
  ⑦ SEC_CONTACT_EMAIL(미국 회사면 필요)  ⑧ DART 접속 1회(⑥ 이 있을 때)  ⑨ SEC 접속 1회(⑦ 이 있을 때)  ⑩ DART MCP(한국 회사면 필요) — `.mcp.json` 의 `dart`
  서버로 initialize · tools/list 한 번(주소가 없으면 「주소 없음」)  ⑪ 기저율 패널(KR · US 가공 CSV)  ⑫ 버전(`버전.json` ↔ 저장소 최신 tag)
  ⑬ 쓰기 자리(이 폴더의 `_raw` · 공용 캐시 — 필수)  ⑭ 법령 조회 — LAW_OC(법제처 DRF 인증값) 있음 · 접속 1회(선택 — 없으면 D 갈래가
  조문 원문을 못 연다)  ⑮ 갈래 권한 — 클로드 설정의 허용 규칙(permissions.allow · defaultMode)에 python 실행 · WebSearch · WebFetch 가
  있는지 읽기만 한다(선택 — 없으면 갈래 서브에이전트가 권한 거부로 멈출 수 있다. 실측 2026-10-23: B1 · C1 이 그 자리에서 멈췄다)
  ⑯ ECOS_API_KEY · ⑰ KOSIS_API_KEY(선택 — 있음 · 꼴만 본다. 키트 지금 판은 두 키 없이 돈다)
  ⑥ · ⑦ 은 하나만 있어도 통과다 — 다른 나라 회사는 처음 부를 때 다시 묻는다(「나중에」 는 `보류` 로 적는다).
  첫 시작 안내(2026-10-25 결정) — ⑥ · ⑦ 이 둘 다 없고 둘 다 「나중에」도 아니면 표 앞에 첫 시작 안내(대본 `첫시작`)를 띄우고
  종료 1(발견)로 멈춘다. 발급 · 설치 절차는 키트 폴더의 `시작하기_인증키.md`. 배포본에는 어떤 키도 넣지 않는다.

값을 적지 않는다 — 키 · 연락처의 값은 화면 · 로그 · `준비점검.json` 어디에도 쓰지 않는다(있음 · 길이 · 저장한 곳만). 접속 시험이 실패해도
예외 글(키가 든 주소를 담을 수 있다)을 찍지 않고 예외의 종류만 적는다.
네트워크는 ⑧ ⑨ ⑩ ⑫ 에서만 쓴다. 서버 주소는 코드가 아니라 `.mcp.json` 에서 읽는다. 회사 · 업종 이름은 이 도구에 없다.

내는 것 — 지금 폴더의 `_raw/준비점검.json`(`--곳` 으로 바꾼다): {형식 · 만든날 · 키트버전 · 언어 · 항목[{번호 · 이름 · 필수 · 상태 · 말}] · 보류 · 신호}.
  신호파일 목록(`신호파일.py`)에 들어 있어 자체검사 51 이 읽는다 — 신호 등급은 늘 「참고」(닫힘 판정을 막지 않는다). 날짜 키는 `만든날` 뿐이다.
종료 코드(키트 규약) — 0 통과 · 1 발견(필수 항목 미비) · 2 입력 오류.
"""
from __future__ import annotations

import argparse
import datetime
import getpass
import glob
import importlib.util
import json
import os
import re
import shutil
import sys
import tempfile

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:                                    # noqa: BLE001
    pass
여기 = os.path.dirname(os.path.abspath(__file__))
키트 = os.path.dirname(여기)
if 여기 not in sys.path:
    sys.path.insert(0, 여기)
from 종료코드 import 통과, 발견, 입력오류  # noqa: E402

형식 = "준비점검/1"
번호글 = {1: "①", 2: "②", 3: "③", 4: "④", 5: "⑤", 6: "⑥", 7: "⑦", 8: "⑧", 9: "⑨", 10: "⑩", 11: "⑪", 12: "⑫", 13: "⑬", 14: "⑭", 15: "⑮",
         16: "⑯", 17: "⑰"}
필수번호 = (1, 2, 13)
키이름 = {6: "OPENDART_API_KEY", 7: "SEC_CONTACT_EMAIL", 14: "LAW_OC", 16: "ECOS_API_KEY", 17: "KOSIS_API_KEY"}
선택키빠짐 = {16: "ECOS 경제통계를 키트가 직접 받지 않는다(지금 판은 이 키 없이 돈다)",
          17: "KOSIS 국가통계를 키트가 직접 받지 않는다(지금 판은 이 키 없이 돈다)"}
안내문서 = "시작하기_인증키.md"
DART주소 = "https://opendart.fss.or.kr/api/company.json"
DART시험회사 = "00126380"                             # 접속 시험용 고유번호 한 건(값을 쓰지 않는다 — 응답의 status 만 본다)
SEC주소 = "https://data.sec.gov/submissions/CIK0000320193.json"   # 접속 시험 한 건(본문은 읽지 않는다 — 상태 코드만)
GITHUB태그 = "https://api.github.com/repos/%s/tags"
LAW주소 = "https://www.law.go.kr/DRF/lawSearch.do"   # 접속 시험 한 건(target=law · query 하나 — 응답 꼴만 본다)


# ────────────────────────────────────────────────── 글

def 대본(언어="ko"):
    for l in (언어, "ko"):
        p = os.path.join(키트, "templates", l, "준비점검.json")
        if os.path.exists(p):
            with open(p, encoding="utf-8") as f:
                return json.load(f)
    raise FileNotFoundError("templates/%s/준비점검.json 이 없다" % 언어)


def 버전읽기():
    p = os.path.join(키트, "버전.json")
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except Exception:                                # noqa: BLE001
        return {}


def _항목(번호, 상태, 말="", 다음=None):
    return {"번호": 번호, "필수": 번호 in 필수번호, "상태": 상태, "말": 말, "다음": 다음}


# ────────────────────────────────────────────────── 점검 하나씩

def 점검_파이썬():
    v = sys.version_info
    글 = "%d.%d.%d" % (v[0], v[1], v[2])
    return _항목(1, "통과" if v >= (3, 11) else "미비", 글)


def _있나(모듈):
    try:
        return importlib.util.find_spec(모듈) is not None
    except Exception:                                # noqa: BLE001
        return False


def 점검_패키지():
    없음 = [m for m in ("requests", "openpyxl") if not _있나(m)]
    return _항목(2, "미비" if 없음 else "통과", ("없음: " + " · ".join(없음)) if 없음 else "")


def 엑셀있나(띄우기=True):
    """Windows 에서 Excel 을 **따로 띄운 인스턴스(DispatchEx)** 로 열었다 바로 닫는다 — 사용자가 열어 둔 엑셀에 붙지 않는다.
    → '있음' · '없음' · 'Windows 아님' · '보지 않음'."""
    if os.name != "nt":
        return "Windows 아님"
    if not 띄우기:
        return "보지 않음"
    if not (_있나("win32com") and _있나("pythoncom")):
        return "없음"
    try:
        import pythoncom                             # noqa: PLC0415
        import win32com.client                       # noqa: PLC0415
        pythoncom.CoInitialize()
        try:
            app = win32com.client.DispatchEx("Excel.Application")
            app.Visible = False
            app.Quit()
            return "있음"
        finally:
            pythoncom.CoUninitialize()
    except Exception:                                # noqa: BLE001
        return "없음"


def 점검_엑셀(띄우기=True):
    """④ Excel 프로그램 · ③ 엑셀 계산(Excel + pywin32 이면 그것, 아니면 formulas)."""
    엑 = 엑셀있나(띄우기)
    py = _있나("win32com") and _있나("pythoncom")
    fo = _있나("formulas")
    if 엑 == "있음" and py:
        셋 = _항목(3, "통과", "Excel · pywin32")
    elif fo:
        셋 = _항목(3, "통과", "formulas" + ("(Excel 은 보지 않음)" if 엑 == "보지 않음" else ""))
    else:
        셋 = _항목(3, "선택없음", "Excel 도 formulas 도 없다 — 워크북은 값만 붓고 수식 재계산은 건너뛴다", 다음=3)
    넷 = _항목(4, "통과" if 엑 == "있음" else ("건너뜀" if 엑 in ("보지 않음", "Windows 아님") else "선택없음"), 엑)
    return 셋, 넷


def _브라우저():
    for 이 in ("msedge", "chrome", "google-chrome", "chromium", "chromium-browser"):
        p = shutil.which(이)
        if p:
            return 이
    if os.name == "nt":
        for 뿌리 in (os.environ.get("ProgramFiles(x86)"), os.environ.get("ProgramFiles"), os.environ.get("LOCALAPPDATA")):
            if not 뿌리:
                continue
            for 꼬 in (r"Microsoft\Edge\Application\msedge.exe", r"Google\Chrome\Application\chrome.exe"):
                if os.path.exists(os.path.join(뿌리, 꼬)):
                    return "msedge" if "Edge" in 꼬 else "chrome"
    if os.path.exists("/Applications/Google Chrome.app") or os.path.exists("/Applications/Microsoft Edge.app"):
        return "chrome" if os.path.exists("/Applications/Google Chrome.app") else "msedge"
    return None


def 점검_영상():
    b, f = _브라우저(), shutil.which("ffmpeg")
    if b and f:
        return _항목(5, "통과", "%s · ffmpeg" % b)
    없음 = [x for x, y in (("Edge/Chrome", b), ("ffmpeg", f)) if not y]
    return _항목(5, "선택없음", "없음: " + " · ".join(없음) + " — 영상은 건너뛴다", 다음=5)


def 키꼴(번호, 값):
    """키 · 연락처 꼴 — (맞나, 까닭). 값은 돌려주지 않는다."""
    if 번호 == 6:
        if len(값) != 40:
            return False, "길이 %d자 — 40자여야 한다" % len(값)
        if not re.fullmatch(r"[0-9A-Za-z]{40}", 값):
            return False, "영문 · 숫자 40자가 아니다"
        return True, ""
    if 번호 == 7:
        if "@" not in 값 or len(값) < 5 or " " in 값.strip():
            return False, "이메일 꼴이 아니다"
        return True, ""
    if 번호 in (14, 16, 17):                            # 꼴이 공개되지 않은 값 — 빈칸 · 공백 · 지나친 길이만 막는다
        if not 값 or re.search(r"\s", 값):
            return False, "빈칸이나 공백이 들어 있다"
        if len(값) > 200:
            return False, "길이 %d자 — 너무 길다" % len(값)
        return True, ""
    return True, ""


def 점검_키(번호, 보류=()):
    이 = 키이름[번호]
    v = os.environ.get(이) or ""
    if not v:
        if 이 in 보류:
            return _항목(번호, "보류", "없음 — 나중에 하기로 했다", 다음=번호)
        return _항목(번호, "선택없음", "없음 — %s 회사를 볼 때 필요하다" % ("한국" if 번호 == 6 else "미국"), 다음=번호)
    ok, 까닭 = 키꼴(번호, v.strip())
    if not ok:
        return _항목(번호, "미비", "저장돼 있으나 꼴이 틀렸다(%s)" % 까닭, 다음=번호)
    return _항목(번호, "통과", "저장됨(%d자)" % len(v.strip()))


def 점검_선택키(번호, 보류=()):
    """⑯ ECOS · ⑰ KOSIS — 있음 · 꼴만(값 · 접속은 보지 않는다). 없으면 「없음(선택)」 + 빠지는 것."""
    이 = 키이름[번호]
    v = (os.environ.get(이) or "").strip()
    if not v:
        if 이 in 보류:
            return _항목(번호, "보류", "없음 — 나중에 하기로 했다", 다음=번호)
        return _항목(번호, "선택없음", "없음 — %s" % 선택키빠짐[번호], 다음=번호)
    ok, 까닭 = 키꼴(번호, v)
    if not ok:
        return _항목(번호, "미비", "저장돼 있으나 꼴이 틀렸다(%s)" % 까닭, 다음=번호)
    return _항목(번호, "통과", "저장됨(%d자)" % len(v))


def 첫시작막힘(항목들, 보류=()):
    """⑥ · ⑦ 이 둘 다 없고 둘 다 「나중에」 도 아니면 참 — 첫 시작 안내를 띄우고 종료 1 로 멈춘다(어느 나라 회사도 받을 수 없다)."""
    상 = {h["번호"]: h["상태"] for h in 항목들}
    return (상.get(6) == "선택없음" and 상.get(7) == "선택없음"
            and 키이름[6] not in 보류 and 키이름[7] not in 보류)


def DART분류(status):
    """DART 응답 status → (통과?, 글). 000 정상 · 013 자료 없음(접속은 됨) · 010/011/901 키 오류 · 012 IP · 020/021 한도 · 800 점검."""
    s = "%s" % (status or "")
    if s in ("000", "013"):
        return True, "연결됨"
    if s in ("010", "011", "901"):
        return False, "키 오류(상태 %s — 등록되지 않았거나 쓸 수 없는 키)" % s
    if s == "012":
        return False, "접근할 수 없는 IP(상태 012)"
    if s in ("020", "021"):
        return False, "요청 한도 초과(상태 %s — 내일 다시)" % s
    if s == "800":
        return False, "DART 시스템 점검 중(상태 800)"
    return False, "응답 상태 %s" % (s or "없음")


def 점검_DART(망=True, 받기=None):
    키 = (os.environ.get(키이름[6]) or "").strip()
    if not 키:
        return _항목(8, "건너뜀", "⑥ 이 없어 보지 않았다")
    if not 망:
        return _항목(8, "건너뜀", "망 없이(--망없이)")
    받기 = 받기 or _requests_get
    try:
        r = 받기(DART주소, params={"crtfc_key": 키, "corp_code": DART시험회사}, timeout=15)
        if getattr(r, "status_code", 200) != 200:
            return _항목(8, "미비", "HTTP %s" % r.status_code, 다음=8)
        try:
            상 = (r.json() or {}).get("status")
        except Exception:                            # noqa: BLE001
            return _항목(8, "미비", "응답을 읽지 못했다(JSON 아님)", 다음=8)
        ok, 글 = DART분류(상)
        return _항목(8, "통과" if ok else "미비", 글, 다음=None if ok else 8)
    except Exception as e:                           # noqa: BLE001 — 예외 글에는 키가 든 주소가 있을 수 있다 → 종류만
        return _항목(8, "미비", "망 오류(%s)" % type(e).__name__, 다음=8)


def 점검_SEC(망=True, 받기=None):
    연 = (os.environ.get(키이름[7]) or "").strip()
    if not 연:
        return _항목(9, "건너뜀", "⑦ 이 없어 보지 않았다")
    if not 망:
        return _항목(9, "건너뜀", "망 없이(--망없이)")
    받기 = 받기 or _requests_get
    try:
        r = 받기(SEC주소, headers={"User-Agent": "DCF-research %s" % 연, "Accept-Encoding": "gzip, deflate"}, timeout=15, stream=True)
        코 = getattr(r, "status_code", 0)
        try:
            r.close()
        except Exception:                            # noqa: BLE001
            pass
        if 코 == 200:
            return _항목(9, "통과", "연결됨")
        if 코 == 403:
            return _항목(9, "미비", "403 — 연락처 꼴(User-Agent) 또는 요청 빈도를 SEC 가 막았다", 다음=9)
        return _항목(9, "미비", "HTTP %s" % 코, 다음=9)
    except Exception as e:                           # noqa: BLE001
        return _항목(9, "미비", "망 오류(%s)" % type(e).__name__, 다음=9)


def _requests_get(url, **k):
    import requests                                  # noqa: PLC0415
    return requests.get(url, **k)


def _requests_post(url, **k):
    import requests                                  # noqa: PLC0415
    return requests.post(url, **k)


# ── ⑩ MCP

def 펼치기(글, 환경=None):
    """`${VAR}` · `${VAR:-기본}` 을 환경 변수로 편다(Claude Code 의 .mcp.json 확장과 같은 꼴). 없는 VAR(기본 없음)은 빈 글."""
    환경 = os.environ if 환경 is None else 환경

    def 하나(m):
        이, 기 = m.group(1), m.group(3)
        v = 환경.get(이)
        return v if v else (기 if 기 is not None else "")
    return re.sub(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(:-([^}]*))?\}", 하나, 글 or "")


def MCP설정(뿌리=None):
    """`.mcp.json` 의 `dart` 서버 → {url, headers} (펴기 전 글 그대로) 또는 None(파일 · 서버 · 주소 없음)."""
    p = os.path.join(뿌리 or 키트, ".mcp.json")
    try:
        with open(p, encoding="utf-8") as f:
            d = json.load(f)
    except Exception:                                # noqa: BLE001
        return None
    s = ((d.get("mcpServers") if "mcpServers" in d else d) or {}).get("dart")
    if not isinstance(s, dict) or not s.get("url"):
        return None
    return {"url": s["url"], "headers": dict(s.get("headers") or {})}


def _MCP읽기(r):
    """Streamable HTTP 응답 — JSON 이거나 SSE(data: {...}) — 에서 JSON-RPC 결과 하나."""
    ct = (getattr(r, "headers", {}) or {}).get("Content-Type", "") or ""
    글 = r.text if hasattr(r, "text") else ""
    if "text/event-stream" in ct or 글.lstrip().startswith("event:") or 글.lstrip().startswith("data:"):
        for 줄 in 글.splitlines():
            if 줄.startswith("data:"):
                try:
                    return json.loads(줄[5:].strip())
                except Exception:                    # noqa: BLE001
                    continue
        return None
    try:
        return r.json()
    except Exception:                                # noqa: BLE001
        return None


def 점검_MCP(망=True, 보내기=None, 뿌리=None):
    설 = MCP설정(뿌리)
    if not 설:
        return _항목(10, "선택없음", "주소 없음 — 한국 회사를 볼 때 필요하다(.mcp.json 에 dart 서버를 넣는다)", 다음=10)
    if not 망:
        return _항목(10, "건너뜀", "망 없이(--망없이)")
    보내기 = 보내기 or _requests_post
    url = 펼치기(설["url"])
    머리 = {k: 펼치기(v) for k, v in 설["headers"].items()}
    머리 = {k: v for k, v in 머리.items() if v}       # 빈 헤더는 보내지 않는다(키 없음 = 캐시 도구만)
    머리.update({"Content-Type": "application/json", "Accept": "application/json, text/event-stream"})
    키있음 = bool((os.environ.get(키이름[6]) or "").strip())
    try:
        r = 보내기(url, json={"jsonrpc": "2.0", "id": 1, "method": "initialize",
                           "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                                      "clientInfo": {"name": "adder-preflight", "version": 버전읽기().get("ADDER", "")}}},
                headers=머리, timeout=20)
        if getattr(r, "status_code", 200) not in (200, 202):
            return _항목(10, "미비", "initialize HTTP %s" % r.status_code, 다음=10)
        세션 = ((getattr(r, "headers", {}) or {}).get("Mcp-Session-Id") or (getattr(r, "headers", {}) or {}).get("mcp-session-id"))
        if 세션:
            머리["Mcp-Session-Id"] = 세션
        try:
            보내기(url, json={"jsonrpc": "2.0", "method": "notifications/initialized"}, headers=머리, timeout=20)
        except Exception:                            # noqa: BLE001
            pass
        r2 = 보내기(url, json={"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}, headers=머리, timeout=20)
        답 = _MCP읽기(r2) or {}
        도구 = ((답.get("result") or {}).get("tools")) or []
        if not 도구:
            return _항목(10, "미비", "연결은 됐으나 도구 목록이 비었다", 다음=10)
        return _항목(10, "통과", "연결됨 · 도구 %d%s" % (len(도구), "" if 키있음 else "(키 없음 — 캐시 도구만)"))
    except Exception as e:                           # noqa: BLE001
        return _항목(10, "미비", "망 오류(%s)" % type(e).__name__, 다음=10)


def 공용캐시():
    return os.environ.get("DCF_공용캐시") or os.environ.get("DCF_SHARED_CACHE") or os.path.join(os.path.expanduser("~"), ".dcf캐시")


def 점검_패널():
    뿌리 = os.path.join(공용캐시(), "기저율")
    글 = []
    for 나, 자 in (("KR", 뿌리), ("US", os.path.join(뿌리, "US"))):
        해 = sorted(int(m.group(1)) for p in glob.glob(os.path.join(자, "*주요계정_*.csv"))
                   for m in [re.search(r"주요계정_(\d{4})\.csv$", p)] if m)
        판 = None
        for 판파일 in ("패널판.json", "판.json"):
            pp = os.path.join(자, 판파일)
            if os.path.exists(pp):
                try:
                    with open(pp, encoding="utf-8") as f:
                        판 = (json.load(f) or {}).get("판")
                except Exception:                    # noqa: BLE001
                    판 = None
        if 해:
            글.append("%s %d~%d(%d해)%s" % (나, 해[0], 해[-1], len(해), (" · 판 %s" % 판) if 판 else ""))
        else:
            글.append("%s 없음" % 나)
    있음 = any("없음" not in g for g in 글)
    return _항목(11, "통과" if 있음 else "선택없음", " · ".join(글), 다음=None if 있음 else 11)


def _버전수(v):
    return tuple(int(x) for x in re.findall(r"\d+", "%s" % v)[:3]) or (0,)


def 점검_버전(망=True, 받기=None):
    v = 버전읽기()
    지금 = v.get("ADDER")
    if not 지금:
        return _항목(12, "미비", "버전.json 이 없다")
    저 = v.get("저장소")
    if not 저:
        return _항목(12, "통과", "v%s · 최신 조회 불가(저장소 주소 없음)" % 지금)
    if not 망:
        return _항목(12, "통과", "v%s · 망 없이" % 지금)
    받기 = 받기 or _requests_get
    try:
        r = 받기(GITHUB태그 % 저, headers={"Accept": "application/vnd.github+json"}, timeout=15)
        태그 = [t.get("name", "") for t in (r.json() or []) if isinstance(t, dict)]
        태그 = [t for t in 태그 if re.search(r"\d", t)]
        if not 태그:
            return _항목(12, "통과", "v%s · 저장소에 tag 없음" % 지금)
        최신 = max(태그, key=_버전수)
        if _버전수(최신) > _버전수(지금):
            return _항목(12, "미비", "v%s → %s" % (지금, 최신), 다음=12)
        return _항목(12, "통과", "v%s = 최신" % 지금)
    except Exception as e:                           # noqa: BLE001
        return _항목(12, "통과", "v%s · 최신 조회 불가(%s)" % (지금, type(e).__name__))


def 점검_쓰기(곳):
    안됨 = []
    for 자리 in (os.path.join(곳, "_raw"), 공용캐시()):
        try:
            os.makedirs(자리, exist_ok=True)
            fd, p = tempfile.mkstemp(prefix="준비점검_", dir=자리)
            os.close(fd)
            os.remove(p)
        except Exception:                            # noqa: BLE001
            안됨.append(자리)
    return _항목(13, "미비" if 안됨 else "통과", ("쓸 수 없음: " + " · ".join(안됨)) if 안됨 else "", 다음=13 if 안됨 else None)


# ────────────────────────────────────────────────── 저장(값은 어디에도 찍지 않는다)

def rc줄바꾸기(경로, 이름, 값):
    """Mac/Linux — 셸 시작 파일 끝에 `export 이름='값'`(이미 있으면 그 줄만 바꾼다). 값 안의 작은따옴표는 '\\'' 로."""
    줄 = "export %s='%s'\n" % (이름, 값.replace("'", "'\\''"))
    글 = ""
    if os.path.exists(경로):
        with open(경로, encoding="utf-8", errors="replace") as f:
            글 = f.read()
    줄들 = 글.splitlines(keepends=True)
    바꿈 = False
    for i, x in enumerate(줄들):
        if re.match(r"\s*export\s+%s=" % re.escape(이름), x):
            줄들[i] = 줄
            바꿈 = True
    if not 바꿈:
        if 줄들 and not 줄들[-1].endswith("\n"):
            줄들[-1] += "\n"
        줄들.append(줄)
    with open(경로, "w", encoding="utf-8") as f:
        f.write("".join(줄들))
    return 경로


def _윈도우저장(이름, 값):
    """Windows — 사용자 환경 변수(HKCU\\Environment)에 쓰고 설정 바뀜을 알린다(setx 처럼, 값을 명령줄에 싣지 않는다)."""
    import winreg                                    # noqa: PLC0415
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_SET_VALUE) as k:
        winreg.SetValueEx(k, 이름, 0, winreg.REG_SZ, 값)
    try:
        import ctypes                                # noqa: PLC0415
        결 = ctypes.c_ulong()
        ctypes.windll.user32.SendMessageTimeoutW(0xFFFF, 0x001A, 0, "Environment", 0x0002, 5000, ctypes.byref(결))
    except Exception:                                # noqa: BLE001
        pass
    return "사용자 환경 변수"


def 저장(이름, 값, rc경로=None):
    """값을 사용자 환경에 저장하고 지금 프로세스에도 넣는다 → 저장한 곳(글). 값은 돌려주지 않는다."""
    if os.name == "nt" and rc경로 is None:
        곳 = _윈도우저장(이름, 값)
    else:
        rc = rc경로 or os.path.join(os.path.expanduser("~"), ".zshrc" if (os.environ.get("SHELL") or "").endswith("zsh") else ".bashrc")
        곳 = rc줄바꾸기(rc, 이름, 값)
    os.environ[이름] = 값
    return 곳


def 값받기(물음):
    if sys.stdin.isatty():
        return getpass.getpass(물음)
    return (sys.stdin.readline() or "").strip()


# ────────────────────────────────────────────────── 기록 · 표

def 이전보류(곳):
    p = os.path.join(곳, "_raw", "준비점검.json")
    try:
        with open(p, encoding="utf-8") as f:
            return list((json.load(f) or {}).get("보류") or [])
    except Exception:                                # noqa: BLE001
        return []


def 기록(곳, 항목들, 언어, 보류, 첫시작=False):
    글 = 대본(언어)
    신호 = []
    for h in 항목들:
        if h["상태"] in ("미비", "보류") or (h["상태"] == "선택없음" and h["번호"] in (6, 7, 10, 11)):
            신호.append({"출처": "준비점검", "종류": "준비", "대상": 글["항목"]["%d" % h["번호"]], "값": None, "문턱": None,
                       "글": "%s %s — %s" % (번호글[h["번호"]], 글["항목"]["%d" % h["번호"]], h["말"] or h["상태"]), "등급": "참고"})
    d = {"형식": 형식, "만든날": datetime.date.today().isoformat(), "키트버전": 버전읽기().get("ADDER"), "언어": 언어,
         "항목": [{"번호": h["번호"], "이름": 글["항목"]["%d" % h["번호"]], "필수": h["필수"], "상태": h["상태"], "말": h["말"]} for h in 항목들],
         "보류": sorted(set(보류)), "첫시작": bool(첫시작), "신호": 신호}
    p = os.path.join(곳, "_raw", "준비점검.json")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    return p, d


def _폭(글):
    import unicodedata                               # noqa: PLC0415
    return sum(2 if unicodedata.east_asian_width(c) in ("W", "F") else 1 for c in 글)


def _채움(글, 폭):
    return 글 + " " * max(1, 폭 - _폭(글))


def 표(항목들, 언어, 첫시작=False):
    글 = 대본(언어)
    v = 버전읽기().get("ADDER", "?")
    필 = [h for h in 항목들 if h["필수"]]
    선 = [h for h in 항목들 if not h["필수"]]
    줄 = ["%s  %s  ADDER v%s            %s %d/%d · %s %d/%d" % (
        글["제목"], datetime.date.today().isoformat(), v, "필수" if 언어 == "ko" else "required", sum(h["상태"] == "통과" for h in 필), len(필),
        "선택" if 언어 == "ko" else "optional", sum(h["상태"] == "통과" for h in 선), len(선))]
    if 첫시작:
        줄 += list(글.get("첫시작") or [])
    for h in 항목들:
        이 = 글["항목"]["%d" % h["번호"]]
        상 = 글["상태말"].get(h["상태"], h["상태"])
        줄.append("%s %s%s%s" % (번호글[h["번호"]], _채움(이, 30), 상, (" — " + h["말"]) if h["말"] else ""))
    다음 = [h for h in 항목들 if h.get("다음") and h["상태"] in ("미비", "보류", "선택없음") and (h["필수"] or h["번호"] in (3, 6, 7, 10, 12, 14, 15, 16, 17))]
    if not 다음:
        줄.append(글["다음"]["없음"])
    else:
        줄.append(글["다음"]["있음"])
        for h in 다음:
            줄.append("  %s %s" % (번호글[h["번호"]], 글["안내"].get("%d" % h["다음"], "")))
    return "\n".join(줄)


def 점검_법령(망=True, 받기=None):
    """⑭ — LAW_OC 있음(값은 적지 않는다) · 법제처 DRF 접속 1회. 없으면 「없음(선택)」 — D 갈래 · 조문조회.py 가 캐시만 본다."""
    v = os.environ.get("LAW_OC") or ""
    if not v.strip():
        return _항목(14, "선택없음", "LAW_OC 없음 — 조문 원문 조회(조문조회.py · D 갈래)가 캐시만 본다", 다음=14)
    if not 망:
        return _항목(14, "건너뜀", "망 없이(--망없이)")
    받기 = 받기 or _requests_get
    try:
        r = 받기(LAW주소, params={"OC": v.strip(), "target": "law", "type": "JSON", "query": "법인세법"}, timeout=15)
        if getattr(r, "status_code", 0) != 200:
            return _항목(14, "미비", "HTTP %s" % getattr(r, "status_code", "?"), 다음=14)
        try:
            d = r.json()
        except Exception:                            # noqa: BLE001
            return _항목(14, "미비", "응답을 읽지 못했다(JSON 아님 — 인증값 · 등록 IP 를 본다)", 다음=14)
        ok = isinstance(d, dict) and any(k for k in d if "Law" in k or "law" in k)
        return _항목(14, "통과" if ok else "미비", "연결됨" if ok else "응답 꼴이 다르다", 다음=None if ok else 14)
    except Exception as e:                           # noqa: BLE001
        return _항목(14, "미비", "망 오류(%s)" % type(e).__name__, 다음=14)


def 설정파일들(곳="."):
    """⑮ 이 읽는 클로드 설정 — 사용자(~/.claude) · 이 폴더(.claude). 고치지 않는다."""
    집 = os.path.join(os.path.expanduser("~"), ".claude")
    return [os.path.join(d, n) for d in (집, os.path.join(os.path.abspath(곳), ".claude")) for n in ("settings.json", "settings.local.json")]


def 점검_갈래권한(곳=".", 파일들=None):
    """⑮ — 갈래 서브에이전트가 쓸 권한(python 실행 · WebSearch · WebFetch)이 허용 규칙에 있나. 설정을 읽기만 한다.
    defaultMode 가 bypassPermissions 면 셋 다 있는 것으로 본다. 없으면 「없음(선택)」 + 안내(사람이 설정에서 연다)."""
    허용, 모드 = [], set()
    for p in (파일들 if 파일들 is not None else 설정파일들(곳)):
        try:
            with open(p, encoding="utf-8") as f:
                d = json.load(f)
        except Exception:                            # noqa: BLE001
            continue
        권 = d.get("permissions") or {}
        허용 += ["%s" % x for x in (권.get("allow") or [])]
        if 권.get("defaultMode"):
            모드.add("%s" % 권["defaultMode"])
    if "bypassPermissions" in 모드:
        return _항목(15, "통과", "defaultMode bypassPermissions")
    있 = {"python": any(x in ("Bash", "Bash(*)") or x.startswith("Bash(python") for x in 허용),
          "WebSearch": any(x == "WebSearch" or x.startswith("WebSearch(") for x in 허용),
          "WebFetch": any(x == "WebFetch" or x.startswith("WebFetch(") for x in 허용)}
    없 = [k for k, v in 있.items() if not v]
    if not 없:
        return _항목(15, "통과", "허용 규칙 — python 실행 · WebSearch · WebFetch")
    return _항목(15, "선택없음", "허용 규칙에 없음: %s — 갈래가 권한 거부로 멈출 수 있다" % " · ".join(없), 다음=15)


def 점검(곳=".", 망=True, 엑셀띄우기=True, 보류=()):
    셋, 넷 = 점검_엑셀(엑셀띄우기)
    return [점검_파이썬(), 점검_패키지(), 셋, 넷, 점검_영상(), 점검_키(6, 보류), 점검_키(7, 보류), 점검_DART(망), 점검_SEC(망),
            점검_MCP(망), 점검_패널(), 점검_버전(망), 점검_쓰기(곳), 점검_법령(망), 점검_갈래권한(곳),
            점검_선택키(16, 보류), 점검_선택키(17, 보류)]


def main(argv=None):
    ap = argparse.ArgumentParser(allow_abbrev=False, description="키트(ADDER) 준비 점검 — 열일곱 항목 · 값은 적지 않는다(발급 안내: 시작하기_인증키.md)")
    ap.add_argument("--언어", default="ko", choices=("ko", "en"))
    ap.add_argument("--조용히", action="store_true", help="표 대신 한 줄 요약")
    ap.add_argument("--설치", action="store_true", help="미비한 키를 하나씩 묻고 저장(터미널에서만)")
    ap.add_argument("--저장", choices=sorted(키이름.values()), help="값 하나를 표준 입력으로 받아 저장")
    ap.add_argument("--곳", default=".", help="`_raw/준비점검.json` 을 둘 폴더(기본 지금 폴더)")
    ap.add_argument("--망없이", action="store_true", help="접속 시험 ⑧ ⑨ ⑩ ⑫ ⑭ 를 건너뛴다")
    ap.add_argument("--엑셀안봄", action="store_true", help="Excel 을 띄워 보지 않는다")
    ap.add_argument("--json", action="store_true", help="표 대신 준비점검.json 내용을 찍는다")
    a = ap.parse_args(argv)
    try:
        글 = 대본(a.언어)
    except Exception as e:                           # noqa: BLE001
        print("입력 오류 — %s" % e)
        return 입력오류
    곳 = os.path.abspath(a.곳)
    보류 = 이전보류(곳)

    if a.저장:
        번 = [k for k, v in 키이름.items() if v == a.저장][0]
        값 = 값받기(글["저장"]["물음"]).strip()
        if not 값:
            보류.append(a.저장)
            print(글["저장"]["보류"])
        else:
            ok, 까닭 = 키꼴(번, 값)
            if not ok:
                print(글["저장"]["꼴틀림"].format(까닭=까닭))
                return 입력오류
            곳글 = 저장(a.저장, 값)
            보류 = [x for x in 보류 if x != a.저장]
            print(글["저장"]["됨"].format(곳=곳글 if 곳글 == "사용자 환경 변수" else os.path.basename(곳글)))
        값 = None

    항목들 = 점검(곳, 망=not a.망없이, 엑셀띄우기=not a.엑셀안봄, 보류=보류)
    if a.설치 and sys.stdin.isatty():
        for 번 in (6, 7, 14, 16, 17):
            h = 항목들[번 - 1]
            if h["상태"] in ("통과",):
                continue
            print("\n" + 글["안내"]["%d" % 번])
            값 = getpass.getpass(글["저장"]["물음"]).strip()
            if not 값:
                if 번 in (6, 7):                     # 선택 키는 빈 값이면 그냥 넘어간다(「나중에」 로 적지 않는다)
                    보류.append(키이름[번])
                    print(글["저장"]["보류"])
                continue
            ok, 까닭 = 키꼴(번, 값)
            if not ok:
                print(글["저장"]["꼴틀림"].format(까닭=까닭))
                continue
            곳글 = 저장(키이름[번], 값)
            보류 = [x for x in 보류 if x != 키이름[번]]
            print(글["저장"]["됨"].format(곳=곳글 if 곳글 == "사용자 환경 변수" else os.path.basename(곳글)))
            값 = None
        항목들 = 점검(곳, 망=not a.망없이, 엑셀띄우기=False, 보류=보류) if True else 항목들
    막힘 = 첫시작막힘(항목들, 보류)
    p, d = 기록(곳, 항목들, a.언어, 보류, 첫시작=막힘)
    if a.json:
        print(json.dumps(d, ensure_ascii=False, indent=2))
    elif a.조용히:
        필 = [h for h in 항목들 if h["필수"]]
        print("준비점검 — 필수 %d/%d · 선택 %d/%d · %s%s" % (sum(h["상태"] == "통과" for h in 필), len(필),
              sum(h["상태"] == "통과" for h in 항목들 if not h["필수"]), sum(1 for h in 항목들 if not h["필수"]), p,
              (" · 첫 시작 — 인증키가 하나도 없다(%s)" % 안내문서) if 막힘 else ""))
    else:
        print(표(항목들, a.언어, 첫시작=막힘))
    return 발견 if (막힘 or any(h["필수"] and h["상태"] != "통과" for h in 항목들)) else 통과


if __name__ == "__main__":
    sys.exit(main())

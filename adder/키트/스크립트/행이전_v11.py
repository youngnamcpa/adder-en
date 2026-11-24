# -*- coding: utf-8 -*-
"""가정 JSON 을 v10(제품군 2) → v11(제품군 4) 로 옮긴다.

왜 필요한가
    이 프로젝트의 가정 JSON 은 **워크북 행 번호를 그대로 키로 쓴다**(`"172"` = 법정세율).
    v11 에서 12번 시트 46행 아래가 16행, 13번 시트 88행 아래가 2행 밀렸다.
    옛 파일을 그대로 읽으면 `"172"` 가 여전히 **유효한 키**라서 오류도 안 나고
    **딴 값을 조용히 읽는다.** 그래서 옮기고, 안 옮긴 것은 엔진이 거부한다.

행 지도
    12번 가정_시나리오   46 이상 → +16      (제품군 3·4 물량·단가 16행이 끼어들었다)
    13번 원천_재무제표    88 이상 → +2       (제품군 3·4 실적 매출 2행)

옮기는 블록
    가정 · 근거 · 방향선언 · 시점가정 · 행이름      12번 행이 키
    원천 · 원천근거 · 소비처                        13번 행이 키
    연장의 "228"·"232"                             12번 행이 키

**값은 하나도 안 건드린다. 키 이름만 바꾼다.**

사용
    python 스크립트/행이전_v11.py 가정_NVDA.json                # 제자리에서 (백업 남김)
    python 스크립트/행이전_v11.py 가정_NVDA.json --출력 새.json
    python 스크립트/행이전_v11.py --폴더 . --살펴만
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import os
import shutil
import sys

버전 = "v11"
가정블록 = ("가정", "근거", "방향선언", "시점가정", "행이름")
원천블록 = ("원천", "원천근거", "소비처")


def 가정12(r: int) -> int:
    return r if r <= 45 else r + 16


def 원천13(r: int) -> int:
    return r if r <= 87 else r + 2


def _옮긴키(블록, 지도):
    """행 번호 키만 옮긴다. 숫자가 아닌 키(예: 'WACC근거')는 그대로 둔다."""
    if not isinstance(블록, dict):
        return 블록, 0
    새, 셈 = {}, 0
    for k, v in 블록.items():
        if str(k).isdigit():
            새키 = str(지도(int(k)))
            if 새키 != str(k):
                셈 += 1
            새[새키] = v
        else:
            새[k] = v
    return 새, 셈


def 사이즈4(r: int) -> int:
    """4번 Sales_working — 제품군 3·4 블록 12행 + 합계 2행이 끼어들었다."""
    표 = {23: 35, 24: 36, 25: 37, 26: 38, 27: 39,
          28: 40, 29: 41, 30: 42, 31: 45, 32: 46, 33: 47, 34: 48, 35: 49,
          37: 51, 38: 52, 39: 53, 40: 54, 41: 55, 42: 56, 43: 57}
    return 표.get(r, r)


_시트지도 = {"4": 사이즈4, "12": 가정12, "13": 원천13}
_주소 = __import__("re").compile(r"^(\d+)!([A-Z]{0,2})(\d+)$")


def 주소옮기기(s):
    """「12!167」·「12!E209」 같은 시트!셀 문자열을 옮긴다.

    **이 자리를 빠뜨리면 조용히 틀린다.** `수식덮기` 는 「이 칸의 스캐폴드 수식을
    덮어써도 된다」는 선언이라, 안 옮기면 붓기가 **엉뚱한 행의 수식을 지키고**
    정작 값을 넣어야 할 행에는 제안 수식이 남는다. 실측에서 기타 순운전자본이
    0.02(내 값) 대신 0.138(제안 수식)로 계산돼 주당가치가 13% 틀렸다.
    """
    m = _주소.match(str(s))
    if not m:
        return s, False
    시트, 열, 행 = m.group(1), m.group(2), int(m.group(3))
    지도 = _시트지도.get(시트)
    if 지도 is None:
        return s, False
    새행 = 지도(행)
    if 새행 == 행:
        return s, False
    return "%s!%s%d" % (시트, 열, 새행), True


def 옮기기(j: dict):
    """(옮긴 것, 바뀐 키 수, 보고 줄)"""
    보고, 총 = [], 0
    j = dict(j)
    for 이름 in 가정블록:
        if 이름 in j:
            j[이름], n = _옮긴키(j[이름], 가정12)
            총 += n
            if n:
                보고.append("  %-8s 12번 행 %d개" % (이름, n))
    for 이름 in 원천블록:
        if 이름 in j:
            j[이름], n = _옮긴키(j[이름], 원천13)
            총 += n
            if n:
                보고.append("  %-8s 13번 행 %d개" % (이름, n))
    # ── 시트!셀 주소를 쓰는 블록 ──────────────────────────────────────
    덮기 = j.get("수식덮기")
    if isinstance(덮기, list):
        새목록, n = [], 0
        for x in 덮기:
            새것, 바뀜 = 주소옮기기(x)
            새목록.append(새것)
            n += 1 if 바뀜 else 0
        j["수식덮기"] = 새목록
        총 += n
        if n:
            보고.append("  수식덮기 %d개  (%s → %s)"
                        % (n, 덮기[0], 새목록[0]))
    사유 = j.get("사유")
    if isinstance(사유, dict):
        새것, n = {}, 0
        for k, v in 사유.items():
            새키, 바뀜 = 주소옮기기(k)
            새것[새키] = v
            n += 1 if 바뀜 else 0
        j["사유"] = 새것
        총 += n
        if n:
            보고.append("  사유     주소 %d개" % n)

    연장 = j.get("연장")
    if isinstance(연장, dict):
        새 = {}
        for k, v in 연장.items():
            새키 = {"228": "244", "232": "248"}.get(str(k), k)
            if 새키 != k:
                총 += 1
                보고.append("  연장     %s → %s" % (k, 새키))
            새[새키] = v
        j["연장"] = 새
    j["스키마버전"] = 버전
    return j, 총, 보고


def 이미옮겼나(j: dict) -> bool:
    return str(j.get("스키마버전") or "") == 버전


def main() -> int:
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("파일", nargs="*", help="가정 JSON")
    ap.add_argument("--폴더", default=None, help="이 폴더 아래 가정 JSON 을 모두")
    ap.add_argument("--출력", default=None, help="한 파일일 때만")
    ap.add_argument("--살펴만", action="store_true", help="바꾸지 않고 무엇이 바뀔지만")
    a = ap.parse_args()

    목록 = list(a.파일)
    if a.폴더:
        목록 += [p for p in glob.glob(os.path.join(a.폴더, "**", "*.json"), recursive=True)
                if "_raw" not in p and "peers" not in p and "_dartcache" not in p]
    if not 목록:
        ap.print_help()
        return 2

    한것 = 건너뛴것 = 아닌것 = 0
    for p in 목록:
        try:
            j = json.load(io.open(p, encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(j, dict) or not isinstance(j.get("가정"), dict):
            아닌것 += 1
            continue
        이름 = os.path.join(os.path.basename(os.path.dirname(p)), os.path.basename(p))
        if 이미옮겼나(j):
            print("이미 v11 — %s" % 이름)
            건너뛴것 += 1
            continue
        새, n, 보고 = 옮기기(j)
        print("%s %s — 키 %d개" % ("[살펴만]" if a.살펴만 else "옮김", 이름, n))
        for 줄 in 보고:
            print(줄)
        if a.살펴만:
            continue
        나갈곳 = a.출력 if (a.출력 and len(목록) == 1) else p
        if 나갈곳 == p:
            shutil.copy(p, p + ".v10백업")
        io.open(나갈곳, "w", encoding="utf-8").write(
            json.dumps(새, ensure_ascii=False, indent=2))
        한것 += 1

    print("\n옮긴 파일 %d개 · 이미 v11 %d개 · 가정 JSON 아님 %d개"
          % (한것, 건너뛴것, 아닌것))
    return 0


if __name__ == "__main__":
    sys.exit(main())

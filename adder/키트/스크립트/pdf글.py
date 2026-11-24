# -*- coding: utf-8 -*-
"""pdf글 — 내려받은 PDF(증권사 리포트 · IR 자료 · 기술분석보고서)의 본문 글을 뽑는다. 처방 순서는 한 곳(2026-10-24 W15 · 유니버스 조사 시범).

    python 스크립트/pdf글.py <파일.pdf> [-o 글.txt] [--json]

차례 — PyMuPDF(`pymupdf` · 옛 이름 `fitz`) 먼저 → `pdftotext -layout` 다음. 뽑은 글이 **깨졌는지** 잰다: 한국어 문서인데 한글이 거의 없고
(한글 글꼴에 유니코드 표가 없어 숫자 · 기호만 남는 꼴 — 네이버 리서치 PDF 실측) · 대체 문자(�) · 사적 영역 문자가 많으면 「깨짐」.
둘 다 깨지거나 비면 「본문 못 읽음」 을 내고 끝낸다 — 그때는 같은 리포트의 요약(리서치 페이지 본문 · 기사)에서 축만 가져오고 출처 성격을 「요약기사」 로
적는다(OCR 은 이 도구가 하지 않는다). 리포트 원문을 길게 옮겨 적지 않는다 — 이 도구는 읽기용 글을 낼 뿐이다.
종료 코드 — 0 읽힘 · 1 깨짐/빔(본문 못 읽음) · 2 입력 오류.
"""
from __future__ import annotations

import argparse
import io
import json
import os
import shutil
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:                                    # noqa: BLE001
    pass


def 한글수(글):
    return sum(1 for c in 글 if "가" <= c <= "힣")


def 판정(글, 한국어=None):
    """→ (판정, 지표). 판정: 읽힘 · 깨짐 · 빔. 한국어 = None 이면 글에서 짐작(한글이 조금이라도 있으면 한국어 문서)."""
    글 = 글 or ""
    n = len(글.strip())
    if n < 200:
        return "빔", {"글자": n}
    한 = 한글수(글)
    대체 = 글.count("�") + sum(1 for c in 글 if "" <= c <= "")
    영 = sum(1 for c in 글 if c.isascii() and c.isalpha())
    지표 = {"글자": n, "한글": 한, "영문": 영, "대체문자": 대체}
    if 대체 > 0.05 * n:
        return "깨짐", 지표
    if 한국어 is True and 한 < 0.02 * n:
        return "깨짐", 지표
    if 한국어 is None and 0 < 한 < 0.005 * n and 영 < 0.2 * n:   # 한글이 아주 조금 · 영문도 적음 — 글꼴 표 없는 한국어 PDF 의 꼴
        return "깨짐", 지표
    return "읽힘", 지표


def 뮤(p):
    try:
        try:
            import pymupdf as m                          # noqa: PLC0415
        except ImportError:
            import fitz as m                             # noqa: PLC0415
    except ImportError:
        return None
    try:
        with m.open(p) as d:
            return "\n".join(쪽.get_text() for 쪽 in d)
    except Exception:                                    # noqa: BLE001
        return None


def 피디(p):
    exe = shutil.which("pdftotext")
    if not exe:
        return None
    try:
        r = subprocess.run([exe, "-layout", "-enc", "UTF-8", p, "-"], capture_output=True, timeout=120)
        return r.stdout.decode("utf-8", errors="replace") if r.returncode == 0 else None
    except Exception:                                    # noqa: BLE001
        return None


def 뽑기(p, 한국어=None):
    """→ {"방법", "판정", "지표", "글", "시도"[]}. 첫 「읽힘」 을 낸다 — 없으면 가장 나은 것(깨짐)과 「본문 못 읽음」."""
    시도 = []
    for 이름, f in (("PyMuPDF", 뮤), ("pdftotext", 피디)):
        글 = f(p)
        if 글 is None:
            시도.append({"방법": 이름, "판정": "도구 없음 또는 실패"})
            continue
        판, 지 = 판정(글, 한국어)
        시도.append({"방법": 이름, "판정": 판, "지표": 지})
        if 판 == "읽힘":
            return {"방법": 이름, "판정": 판, "지표": 지, "글": 글, "시도": 시도}
    return {"방법": None, "판정": "본문 못 읽음", "지표": None, "글": "", "시도": 시도,
            "다음": "같은 리포트의 요약(리서치 페이지 본문 · 기사)에서 축만 — 출처_성격 「요약기사」 · 확신도 한 칸 낮춤"}


def main(argv=None):
    ap = argparse.ArgumentParser(allow_abbrev=False, description="PDF 본문 글 — PyMuPDF → pdftotext · 깨짐 판정")
    ap.add_argument("파일")
    ap.add_argument("-o", "--출력")
    ap.add_argument("--한국어", action="store_true", help="한국어 문서라고 알려 준다(한글이 2%% 미만이면 깨짐)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    if not os.path.exists(a.파일):
        print("파일이 없다 — %s" % a.파일)
        return 2
    r = 뽑기(a.파일, True if a.한국어 else None)
    if a.출력 and r["글"]:
        io.open(a.출력, "w", encoding="utf-8").write(r["글"])
    요 = {k: v for k, v in r.items() if k != "글"}
    if a.json:
        print(json.dumps(요, ensure_ascii=False))
    else:
        print("pdf글 — %s · %s%s" % (os.path.basename(a.파일), r["판정"], (" (%s)" % r["방법"]) if r["방법"] else ""))
        for x in r["시도"]:
            print("  %s: %s %s" % (x["방법"], x["판정"], x.get("지표") or ""))
        if r.get("다음"):
            print("  다음 — %s" % r["다음"])
    return 0 if r["판정"] == "읽힘" else 1


if __name__ == "__main__":
    sys.exit(main())

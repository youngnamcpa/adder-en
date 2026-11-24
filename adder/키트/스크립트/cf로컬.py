# -*- coding: utf-8 -*-
"""cf로컬 — SEC companyfacts 를 공용 캐시에서 먼저 읽는다 (2026-10-24 W17 · 유니버스 조사 물결 3차).

유사기업 사슬의 개념 보충(`sec_concept`) · 외화 개념(`sec_외화개념`) · 주식수(`sec_shares_us`)는 회사마다 개념 하나에 요청 하나
(companyconcept)를 보내 곳당 20번 안팎을 불렀다 — 외국 소형 신고인 여덟 곳에 509초(META 조사 실측), 해외 후보 60곳에 600초 타임아웃
(LIG디펜스앤에어로스페이스 조사 실측). 같은 사실은 패널 도구(`sec_상세변수.py 받기`)가 공용 캐시에 받아 둔 `companyfacts_<날>.zip`
(전 제출인 · 비차원 사실 전부)과 회사별 새 판(`companyfacts/회사/CIK##########.json`)에 이미 있다. 그래서 먼저 거기서 읽고,
없을 때만 네트워크로 간다.

  로컬(기준일)                     공용 캐시 자리를 찾는다(없으면 쓰지 않는다)
  로컬.개념(cik, tax, tag)        → (있음, j) — 있음 False 면 그 회사가 로컬에 없다(네트워크로) · 있음 True · j None 이면 그 태그가 없다
                                  (네트워크로 다시 묻지 않는다 — companyfacts 와 companyconcept 는 같은 사실이다)
  로컬.판                         zip 날짜(YYYYMMDD) · 회사 파일만 있으면 그 파일 날짜

쓸 수 있나 — zip 이 기준일보다 75일 넘게 늦게 지어졌을 때만(기준일이 끝인 분기 · 연차 보고서가 늦게 들어온다: 10-Q 40~45일 · 10-K 60~90일).
그보다 이르면 로컬을 쓰지 않는다(`쓸수있음` False · 까닭). 회사 파일(`회사/`)은 그 파일의 수정 시각으로 같은 잣대를 건다.
"""
from __future__ import annotations

import datetime as _dt
import glob
import io
import json
import os
import re
import threading
import zipfile

여유일 = 75


def 공용뿌리():
    return os.environ.get("DCF_공용캐시") or os.environ.get("DCF_SHARED_CACHE") or os.path.expanduser("~/.dcf캐시")


class 로컬:
    def __init__(self, 기준일=None, 자리=None):
        self.자리 = 자리 or os.path.join(공용뿌리(), "기저율", "US", "companyfacts")
        self.기준일 = 기준일
        self._zip = None
        self._zp = None
        self._잠금 = threading.Lock()
        self._캐시 = {}
        self.판 = None
        self.쓸수있음 = False
        self.까닭 = ""
        zs = sorted(glob.glob(os.path.join(self.자리, "companyfacts_*.zip")))
        if zs:
            self._zp = zs[-1]
            m = re.search(r"companyfacts_(\d{8})\.zip$", self._zp)
            self.판 = m.group(1) if m else None
        if not (self._zp or os.path.isdir(os.path.join(self.자리, "회사"))):
            self.까닭 = "공용 캐시에 companyfacts 가 없다(%s)" % self.자리
            return
        if self.판 and 기준일 and not self._신선(self.판):
            self.까닭 = "companyfacts 판 %s 이 기준일 %s 뒤 %d일 안이라 늦게 들어온 보고서가 빠질 수 있다 — 네트워크로" % (self.판, 기준일, 여유일)
            self._zp = None
        self.쓸수있음 = bool(self._zp or os.path.isdir(os.path.join(self.자리, "회사")))

    def _신선(self, 날8):
        if not self.기준일:
            return True
        try:
            판 = _dt.date(int(날8[:4]), int(날8[4:6]), int(날8[6:8]))
            기 = _dt.date.fromisoformat(self.기준일[:10])
        except ValueError:
            return False
        return (판 - 기).days >= 여유일

    def 회사(self, cik):
        """→ companyfacts dict 또는 None(로컬에 없다)."""
        if not self.쓸수있음:
            return None
        cik = int(cik)
        with self._잠금:
            if cik in self._캐시:
                return self._캐시[cik]
            이름 = "CIK%010d.json" % cik
            j = None
            p = os.path.join(self.자리, "회사", 이름)
            if os.path.exists(p):
                날 = _dt.date.fromtimestamp(os.path.getmtime(p)).strftime("%Y%m%d")
                if self._신선(날):
                    try:
                        j = json.load(io.open(p, encoding="utf-8"))
                    except (OSError, ValueError):
                        j = None
            if j is None and self._zp:
                try:
                    if self._zip is None:
                        self._zip = zipfile.ZipFile(self._zp)
                    with self._zip.open(이름) as f:
                        j = json.loads(f.read().decode("utf-8"))
                except KeyError:
                    j = None
                except (OSError, ValueError, zipfile.BadZipFile):
                    j = None
            self._캐시[cik] = j
            return j

    def 개념(self, cik, tax, tag):
        """→ (있음, {"units": …} 또는 None) — companyconcept 응답과 같은 꼴."""
        cf = self.회사(cik)
        if cf is None:
            return False, None
        d = ((cf.get("facts") or {}).get(tax) or {}).get(tag)
        if not d:
            return True, None
        return True, {"cik": int(cik), "taxonomy": tax, "tag": tag, "units": d.get("units") or {}, "출처": "로컬 companyfacts(%s)" % (self.판 or "회사 파일")}

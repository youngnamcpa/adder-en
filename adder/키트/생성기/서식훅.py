# -*- coding: utf-8 -*-
"""서식훅 — 표준 서식 길: 「칸 종류 → 명명 스타일」과 시트 공통 서식.

짓기가 서식길="표준" 일 때 칸마다 · 줄마다 · 시트마다 부른다. 스타일 표 자체는 같은 폴더의 서식표준.py 가 갖고 있다
(명명 스타일 한 벌 · 숫자 서식 표 · 열 폭 · 시트 사양). 그 파일이 없으면 칸 종류만 가리고 서식은 입히지 않는다.

칸 종류는 네 가지에서 정해진다: 줄의 종류(줄 무늬 명세의 「종류」 — 배치의 「줄서식」이 덮을 수 있다) · 열의 종류(열 등록부) ·
칸의 내용(입력 칸인가 · 수식인가 · 글인가) · **수식이 다른 시트를 읽는가**(수식 틀의 참조가 놓인 시트로 판정한다 — 짓기가 넘겨준다).

  칸 종류      명명 스타일(서식표준)     언제
  제목         글_제목                  제목 줄의 이름 칸
  부제         글_부제                  머리 구역(틀 고정 위)의 글 줄 · 시점 머리 아랫줄의 이름 칸
  구획머리     글_구획                  구획머리 줄 — 이름 열부터 표의 끝 열까지 띠로
  소구획       글_소구획                구획 안의 작은 머리 줄(배치의 「줄서식」이 종류를 「소구획」으로 덮은 줄) — 굵은 글 + 아래 가는 선.
                                        번호를 매기지 않는다. 그 줄의 입력 칸은 입력 칸으로 선다
  머리         머리_띠                  머리 줄(표 머리 · 시점 머리 첫 줄) — 이름 열부터 글이 있는 마지막 열까지 띠로
  머리보조     머리_보조                시점 머리 아랫줄(실적/예측 · 기간 종료일 · 기간)의 값 칸
  행이름       글_행이름                이름 열
  곁이름       글_곁이름                값 열에 놓인 둘째 이름(「이름 · 값 · 둘째 이름 · 값」 줄) — 줄바꿈
  주석         글_주석                  글 줄의 이름 칸 · 줄바꿈하지 않는 글 열의 글
  단위         글_단위                  단위 열 · 값 열의 짧은 글(n/a 따위)
  번호         글_번호                  번호 열
  근거         글_출처                  근거 · 비고 · 풀이 열의 글(생성기가 적은 글)
  입력         값_입력                  입력 칸(숫자 · 날짜 · 빈칸)
  입력글       값_입력글                입력 칸(짧은 글) · 사유 칸
  입력긴글     값_입력긴글              근거 · 비고 · 풀이 열의 입력 칸(줄바꿈)
  선택         값_선택                  목록 유효성이 걸린 칸
  계산         값_계산                  같은 시트 안의 계산(숫자)
  연결         값_연결                  다른 시트를 읽는 수식(숫자)
  산출         값_산출                  도구가 값으로 적는 모델 산출값(시나리오별 결과 · 민감도)
  글값         값_글                    숫자 서식이 없는 줄의 계산 · 긴 글 값
  연결글       값_연결글                숫자 서식이 없는 줄에서 다른 시트를 읽는 수식
  판정         점검_표시                점검 줄의 판정 칸(조건부 서식: Error 빨강 · Review 주황)
  결과         점검_결과                판정 숫자(0/1) · 건수

숫자 서식은 줄의 「서식」(서식표의 키)으로 덧씌운다. 「서식」이 없는 줄의 값 칸은 일반(General)이다 — 스타일의 기본 금액 서식이
말없이 남지 않게 한다. 소계 · 합계 줄에는 줄선을 긋는다. 이름 칸의 들여쓰기 · 굵기는 줄의 덧 속성으로 덧씌운다.
"""
import os
import datetime
import importlib.util
from copy import copy
from collections import Counter

from openpyxl.styles import Alignment, Font

표준경로 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "서식표준.py")     # 생성기의 정본(설계/서식표준.py 를 옮겨 온 것)

훅표 = {
    "제목": "글_제목", "부제": "글_부제", "구획머리": "글_구획", "소구획": "글_소구획", "머리": "머리_띠", "머리보조": "머리_보조",
    "행이름": "글_행이름", "곁이름": "글_곁이름", "주석": "글_주석", "단위": "글_단위", "번호": "글_번호", "근거": "글_출처",
    "입력": "값_입력", "입력글": "값_입력글", "입력긴글": "값_입력긴글", "선택": "값_선택",
    "계산": "값_계산", "연결": "값_연결", "산출": "값_산출", "글값": "값_글", "연결글": "값_연결글",
    "판정": "점검_표시", "결과": "점검_결과",
}
칸종류들 = tuple(훅표)
_숫자서식입는 = {"입력", "계산", "연결", "산출", "결과", "머리보조", "글값", "연결글"}
_일반으로 = {"글값", "연결글", "머리보조"}        # 줄에 「서식」이 없으면 스타일 기본 서식 그대로 두는 종류(General)
_글열 = {"근거", "비고", "풀이", "소비처", "방향", "방향점검", "역산", "보조"}
_긴글열 = {"근거", "비고", "풀이"}
_값열 = {"실적", "예측", "영구", "값", "점검칸", "기타"}
# 열 종류가 줄의 숫자 서식을 덮는 곳 — 그 열의 칸은 줄의 값과 단위가 다르다.
# 12번의 방향점검 열은 「시나리오 대소 관계 불일치 수」(건수)다 — 줄의 서식(비율 · 일수 …)을 입으면 2 가 「200.0%」로 보인다
열서식 = {"방향점검": "건수"}
# 줄 종류 — 줄 무늬 명세의 종류에 서식만의 종류를 더한다(배치의 「줄서식」에서만 쓴다)
덧줄종류 = ("머리보조", "산출", "부제", "소구획")
짧은글한도 = 12      # 값 열의 글이 이 환산 폭 안이면 가운데 회색(글_단위), 넘으면 왼쪽 검정(값_글)


def _표준읽기(경로):
    if not os.path.exists(경로):
        return None
    spec = importlib.util.spec_from_file_location("서식표준", 경로)
    모듈 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(모듈)
    return 모듈


def 다른시트읽나(틀, 현재sid, 놓인시트):
    """수식 틀이 다른 시트의 칸을 읽는가. 놓인시트 = 행 ID → 그 줄이 놓인 시트 ID(배치가 정한 것).

    참조가 가리키는 줄이 놓인 시트가 수식이 놓인 시트와 다르면 다른 시트 참조다 — 원문에 시트 머리가 붙어 있었는지(x)가 아니라
    새 배치에서 판정한다(검증 줄을 15번으로 옮기면 같은 수식이 다른 시트 참조가 된다)."""
    if not 틀:
        return False
    for p in 틀:
        if isinstance(p, str):
            continue
        k = p.get("k")
        if k in ("c", "r", "R"):
            for rid in (p.get("r"), p.get("r2")):
                if rid is not None:
                    try:
                        놓 = 놓인시트(rid)
                    except KeyError:
                        놓 = None
                    if 놓 is not None and 놓 != 현재sid:
                        return True
        elif k == "C":
            if p.get("s") and p["s"] != 현재sid:
                return True
        elif k == "n":
            if p.get("s") and p["s"] != 현재sid:
                return True
        elif k == "x":
            if "!" in str(p.get("t", "")):
                return True
    return False


class 훅:
    def __init__(self, 경로=None):
        self.표준 = _표준읽기(경로 or 표준경로)
        self.쓸수있나 = self.표준 is not None
        self.수 = Counter()

    def 책준비(self, wb, 기본글꼴=True):
        """명명 스타일을 통합문서에 싣는다. 기본글꼴=False 면 통합문서의 기본 글꼴은 건드리지 않는다(옛 서식과 섞어 쓸 때)."""
        if self.쓸수있나:
            if 기본글꼴:
                self.표준.기본글꼴(wb)
            self.표준.스타일등록(wb)

    # ── 칸 ──
    def 칸종류(self, 줄종류, 열종류, 한, 입력인가, 틀, sid, 별칭, 다른시트=None, 선택=False, 서식이름=None, 머리구역=False):
        """칸 하나의 종류. 서식을 입히지 않을 칸이면 None.

        다른시트 : 이 칸의 수식이 다른 시트를 읽는가(짓기가 새 배치에서 판정해 넘긴다). None 이면 옛 판정(다른 시트의 칸 하나를
                   그대로 읽는 수식만 연결)으로 가린다.
        선택     : 이 칸에 목록 유효성이 걸려 있는가.    머리구역 : 이 줄이 시트의 머리 구역(틀 고정 위)에 있는가.
        """
        글값 = isinstance(한.get("v"), str) and 한.get("t") not in ("dt", "d", "tm")     # 날짜·시각은 글이 아니다
        있음 = "v" in 한 or 틀 is not None
        if 다른시트 is None and 틀 is not None:
            참 = [p for p in 틀 if not isinstance(p, str)]
            다른시트 = len(참) == 1 and len(틀) == 2 and 틀[0] == "=" and bool(참[0].get("x"))
        if 열종류 == "여백":
            return None
        if 줄종류 == "제목":      # 제목 글은 이름 열에 둔다. 이름 열이 안쪽에 있는 시트(15번)는 글이 있는 칸이 제목이다
            return "제목" if (열종류 == "이름" or 글값) else None
        if 줄종류 == "구획머리":
            return "구획머리"
        if 줄종류 == "머리":
            return "머리"
        if 줄종류 == "소구획" and (열종류 == "이름" or not 있음):      # 이름 칸과 빈 칸은 띠 — 값이 있는 칸은 아래 규칙으로 간다
            return "소구획" if 열종류 == "이름" else None
        if 열종류 == "이름":
            if 줄종류 in ("머리보조", "부제") or (줄종류 == "글" and 머리구역):
                return "부제"
            return "주석" if 줄종류 == "글" else "행이름"
        if 열종류 == "단위":
            return "단위"
        if 열종류 == "번호":
            return "번호"
        if 줄종류 == "머리보조":
            return "머리보조" if 있음 else None
        if 별칭 and not 입력인가 and 틀 is None and 열종류 not in _글열:
            # 한 줄에 「이름 · 값 · 둘째 이름 · 값 · 설명」을 나란히 둔 줄(12번 기준 정보)의 둘째 이름 칸과 설명 칸
            if str(별칭).startswith("이름") and 글값:
                return "곁이름"
            if 별칭 == "설명" and 글값:
                return "주석"
        if 줄종류 == "점검" and 별칭 == "판정":
            return "판정"
        if 줄종류 == "점검" and 별칭 == "사유" and 틀 is None:      # 사유 자리에 보조 계산 수식을 둔 줄은 아래 규칙으로 간다
            return "입력글"
        if 선택:
            return "선택"
        숫자줄 = bool(서식이름) and 서식이름 not in ("글", "일반")
        if 열종류 in _글열:
            if 입력인가:
                return "입력긴글" if 열종류 in _긴글열 else "입력글"
            if 틀 is not None:
                return "연결글" if 다른시트 else "글값"
            if not 있음:
                return None
            return "근거" if 열종류 in _긴글열 else "주석"
        if 입력인가:      # 숫자 서식이 없는 줄(대상회사 · 시나리오 명칭 · 주요 전제 …)의 입력 칸은 비어 있어도 글 입력 칸이다
            return "입력글" if (글값 or not 숫자줄) else "입력"
        if 줄종류 == "산출":
            return "산출" if (있음 or 열종류 in _값열) else None
        if 틀 is not None:
            if 다른시트:
                return "연결" if 숫자줄 else "연결글"
            return "계산" if 숫자줄 else "글값"
        if 글값:
            if 줄종류 == "글":      # 글 줄(약어 · 범례 · 주석 표)의 값 열 글은 길이와 상관없이 같은 모양이다
                return "글값"
            짧은 = self.표준.환산폭(한["v"]) <= 짧은글한도 if self.쓸수있나 else len(한["v"]) <= 6
            return "단위" if 짧은 else "글값"
        return ("계산" if 숫자줄 else "글값") if 있음 else None

    def 입히기(self, 칸, 종류, 서식이름=None):
        if 종류 is None:
            return
        self.수[종류] += 1
        if not self.쓸수있나:
            return
        칸.style = 훅표[종류]
        표 = self.표준.서식표
        if 종류 in _숫자서식입는:
            if 서식이름 and 서식이름 in 표:
                칸.number_format = 표[서식이름]
            elif 종류 not in _일반으로:
                칸.number_format = 표["일반"]      # 「서식」이 없는 줄 — 스타일의 기본 금액 서식을 남기지 않는다
        if isinstance(칸.value, (datetime.date, datetime.datetime)):
            칸.number_format = 표["날짜"]           # 날짜 값은 어느 칸에서든 날짜로 보인다(글 서식이면 일련번호가 된다)
        elif 종류 in ("입력", "선택") and 서식이름 == "날짜":
            칸.number_format = 표["날짜"]

    def 줄덧(self, 칸, 열종류, 줄):
        """줄의 덧 속성을 칸에 덧씌운다 — 「들여」(이름 칸 들여쓰기 0·1·2) · 「굵게」. 스타일 이름은 남는다."""
        if not self.쓸수있나:
            return
        if 줄.get("들여") and 열종류 == "이름":
            a = copy(칸.alignment)
            칸.alignment = Alignment(horizontal=a.horizontal or "left", vertical=a.vertical, wrap_text=a.wrap_text,
                                    indent=int(줄["들여"]))
        if 줄.get("굵게"):
            f = copy(칸.font)
            칸.font = Font(name=f.name, sz=f.sz, b=True, i=f.i, color=f.color, u=f.u, strike=f.strike, vertAlign=f.vertAlign)

    def 줄선(self, ws, 행, 열1, 열2, 종류):
        if self.쓸수있나:
            self.표준.줄선(ws, 행, 열1, 열2, 종류)

    def 띠(self, ws, 행, 열1, 열2, 종류):
        """구획머리 · 머리 줄의 띠 — 열1~열2 의 빈 칸에도 같은 스타일을 준다(병합 대신)."""
        if not self.쓸수있나:
            return
        for k in range(열1, 열2 + 1):
            칸 = ws.cell(행, k)
            if 칸.style == "Normal":
                칸.style = 훅표[종류]
                self.수[종류] += 1

    # ── 시트 ──
    def 사양(self, sid):
        return self.표준.시트사양(sid) if self.쓸수있나 else {}

    def 열폭(self, sid, 열종류, 머리글=None):
        """표준 열 폭 — 글 열은 머리 글(출처 · 기준일 · 산정 근거 · 비고 …)로 먼저 가리고, 그다음 시트의 예외, 열 종류."""
        if not self.쓸수있나:
            return None
        if 열종류 in _글열 or 열종류 == "점검칸":
            w = self.표준.글열폭찾기(머리글)
            if w:
                return w
        return (self.표준.시트폭.get(sid) or {}).get(열종류) or self.표준.폭.get(열종류) or self.표준.폭["기타"]

    def 줄높이(self, 줄종류):
        if not self.쓸수있나:
            return None
        return {"제목": self.표준.높이["제목"], "구획머리": self.표준.높이["구획"], "머리": self.표준.높이["머리"]}.get(줄종류)

    def 보기(self, ws, sid, 덮음=None):
        """눈금선 · 확대 · 탭 색 · 그룹 요약의 자리. 덮음 = 배치의 「보기」({"확대", "눈금선", "탭색"})."""
        if not self.쓸수있나:
            return
        사 = self.사양(sid)
        덮음 = 덮음 or {}
        ws.sheet_view.showGridLines = bool(덮음.get("눈금선", False))
        ws.sheet_view.zoomScale = 덮음.get("확대") or 사.get("확대") or 100
        ws.sheet_properties.tabColor = 덮음.get("탭색") or self.표준.탭색[사.get("묶음") or "계산"]
        ws.sheet_properties.outlinePr.summaryBelow = False      # 접는 줄의 요약 줄은 묶음 위, 요약 열은 묶음 왼쪽
        ws.sheet_properties.outlinePr.summaryRight = False

    def 판정서식(self, ws, 범위글들):
        """판정 칸의 조건부 서식 — 이어진 범위마다 규칙 둘(Error 빨강 · Review 주황)."""
        if not self.쓸수있나:
            return 0
        n = 0
        for 글 in 범위글들:
            첫 = 글.split(":")[0]
            for 규칙 in self.표준.판정규칙(첫):
                ws.conditional_formatting.add(글, 규칙)
                n += 1
        return n

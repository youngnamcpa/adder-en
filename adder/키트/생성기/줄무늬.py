# -*- coding: utf-8 -*-
"""줄무늬 — 열 ID 명세(칸 단위) ↔ 줄 무늬 명세(시트마다 한 파일, 행 하나가 JSON 객체 하나).

쓰기:  python 줄무늬.py <칸 단위 명세 폴더> <줄 무늬 명세 폴더>     (열표를 입혀 묶어 쓴다 — 새 폴더에만. 범위 지문 · 줄 이름표도 새로 낸다)
       python 줄무늬.py --다시쓰기 <줄 무늬 명세 폴더> [--덧명세 파일.jsonl …] [--이름덮기]
           읽어서 표준 꼴로 다시 쓴다. 줄 이름을 고친 줄에 한해 수식에 덧붙인 이름을 새 이름으로 맞추고, 무엇을 고쳤는지 낸다
           (행 ID · 옛 덧붙인 이름 → 새 이름 · 곳 수). 덧붙인 이름이 그 줄의 옛 이름(줄이름.json 에 적어 둔 것)과도 지금 이름과도
           다르면 행 ID 를 틀리게 적은 것일 수 있으므로 고치지 않고 멈춘다(--이름덮기 로만 덮는다). 범위 지문은 안 건드린다.
       python 줄무늬.py --옛꼴고치기 <줄 무늬 명세 폴더> [--덧명세 파일.jsonl …]
           옛 형식(줄무늬 2)의 명세를 지금 형식으로 옮긴다 — 이웃 열 표기 @-1 → @<-1> · 「가정묶음」 표시 · 줄 이름표.
           그 뒤 「python 범위지문.py 승인 <폴더> --위치범위」 로 범위 지문을 새 형식으로 적는다.
       python 줄무늬.py --함수목록 <줄 무늬 명세 폴더>
           목록_좌표의존함수.json(좌표에 기대는 함수가 쓰인 곳)을 지금 명세에서 다시 낸다 — 줄을 더하거나 지운 뒤에 한 번.

줄 무늬 명세 폴더
  책.json        형식 · 시트 순서 · 통합문서의 정의된 이름 (원본은 파일 이름만 싣는다)
  S04.jsonl      첫 객체 = 시트 머리(탭 이름 · 열 등록부 · 묶음 · 축 · 쓰임 · 틀 고정 · 유효성 …), 둘째부터 행 하나씩
  범위지문.json  범위마다 구성 줄 ID 목록 · 가정묶음 · 짝 범위 수 · 시트 머리(열 차례 · 축 · 묶음 · 쓰임)
                 (범위지문.py — 손으로 고치지 않고 「승인」 명령으로 고친다)
  줄이름.json    줄마다 이름과 옛 이름 몇 개(수식에 덧붙인 이름이 「줄 이름을 고쳐서」 달라진 것인지 가리는 데 쓴다. 「다시쓰기」가 고쳐 적는다)
  옛서식/        옛 서식을 있는 그대로 옮기는 길의 재료(서식 표 · 칸별 서식 번호 · 행 높이 · 기본 글꼴). 지워도 줄 무늬 명세는 읽힌다
  테마.xml

행 하나
  {"id":"S05R017","이름":"매출원가 합계","단위":"=[$S12R006 금액 단위 라벨]@$값2","종류":"합계","서식":"금액",
   "무늬":{"실적":"=[S13R063 매출원가]@.","예측영구":"=SUM([S05R010 원가 항목 1]@.:[S05R016 신제품·증설 원가]@.)"},
   "글":{"근거1":"…"},"값":{"H1":1},"입력":["예측영구"],"병합":["이름~TV"],"쓰임":"점검","메모":"왜 이렇게 했는지"}
  · 이름 · 단위 : 이름 열 · 단위 열의 글. 「=」로 시작하면 손 수식이다. 숫자를 적으면 오류다.
  · 종류       : 제목 / 구획머리 / 머리 / 입력 / 계산 / 소계 / 합계 / 비율 / 점검 / 글 / 빈줄
  · 서식       : 숫자 서식 이름(서식표준.서식표의 키 — 금액 · 비율 · 일수 …). 명명 스타일은 칸 종류가 정한다(서식훅.py)
  · 무늬       : 열 구간 → 손 수식(수식문법.md).  글 : 열 구간 → 글.  값 : 열 구간 → 숫자·참거짓(날짜는 {"v": …, "t": "d"})
                 「글」에 숫자를, 「값」에 글("1000")을 적으면 오류다.
  · 축값       : 열 구간 → 기간 축의 속성 이름(표기 · 구분 · 종료일 · 시작일 · 개월 · 구간 · 회계연도 …). 생성기가 그 열의 속성 값을 적는다
                 (12번 기간 구획의 표기 · 종료일 따위 — 가정 파일의 `기간` 에서 온다). 같은 칸에 무늬가 있으면 축값이 덮는다
  · 덧         : 열 ID → {"메모": …, "링크": …}. 그 밖의 열쇠(값 · 수식)는 받지 않는다 — 값은 「글」·「값」에, 수식은 「무늬」에
  · 입력       : 입력 칸인 열 구간.  병합 : 이 줄 안의 병합.  쓰임 : 이 줄의 열 별칭 묶음(시트 머리의 「쓰임」 표에 있는 이름)
  · 선 · 들여 · 굵게 : (있을 때만) 소계/합계 줄선 · 이름 칸 들여쓰기(0·1·2) · 굵은 글씨 — 표준 서식 길에서 쓴다
  · 높이       : (있을 때만) 줄 높이. 옛서식/ 의 높이보다 앞선다 — 새로 적는 줄은 이것으로 준다
  · 메모       : 사람이 적는 풀이(왜 이렇게 했는지). 짓기는 안 읽고 「다시쓰기」가 지킨다. 시트 머리에도 적을 수 있다

  · 되풀이 · 묶음끝 · 조건 · 갈래 · 시나리오 · 적용열 · 빈칸허용 · 표 · 표머리 · 칸서식 : 구조에 따라 펴는 줄(틀)의 열쇠 — 구조펴기.py · 수식문법.md 15절.
                 가정 파일의 `구조` 선언대로 줄이 되풀이되고 갈리고 빠진다(읽기(…, 구조=가정)). 틀인 줄은 다시쓰기가 적힌 그대로 둔다
  조각 파일     책.json 의 「조각」({"S12": ["S12_매출.jsonl", …]})에 적힌 파일 — 첫 객체 {"조각": "S12"}, 둘째부터 행. 시트 파일 뒤에 이어 읽는다

적는 꼴
  · 열쇠의 차례는 정해져 있다(id · 이름 · 단위 · 종류 · 서식 · 쓰임 · 선 · 들여 · 굵게 · 높이 · 입력 · 무늬 · 글 · 값 · 병합 · 덧 · 메모).
  · 긴 행(400자 넘음)은 여러 줄에 걸쳐 적는다 — 열쇠마다 한 줄, 긴 수식·글은 조각의 목록으로(읽을 때 이어 붙인다).
        "무늬": {
         "판정": [
          "=IF([S04R054 매출액 합계]@$E1>0,",
          "\"OK\",\"확인 필요\")"]}
    손으로 고칠 때는 한 줄로 적어도 되고 조각을 달리 나눠도 된다. 「다시쓰기」가 표준 꼴로 되돌린다.
  · 모르는 열쇠 · 같은 열쇠 두 번 · 종류/서식/쓰임의 오타 · 「=」로 시작하는 글 · 열 등록부의 모르는 열 종류 ·
    줄 안에서 겹치는 병합은 오류다(파일 이름과 줄 번호를 알린다).

열 구간(무늬 · 글 · 값 · 입력 · 병합의 열쇠)
  E1            열 하나(열 ID 또는 그 줄 쓰임의 별칭)
  E2~E7         열 ID 구간
  예측          묶음 전부(그 종류의 열이 늘면 따라 는다)
  E2~예측       E2 부터 예측 묶음의 끝 열까지     실적~E3  실적 묶음의 첫 열부터 E3 까지
  예측.첫       예측 묶음의 첫 열 하나            예측.끝  예측 묶음의 끝 열 하나(열이 늘면 따라간다 — 「E11」로 못 박지 않는다)
  예측.2        예측 묶음의 둘째 열               예측.끝2 예측 묶음의 뒤에서 둘째 열          예측.2~예측  둘째 예측 열부터 끝까지

시간축 열을 기간 축에서 받는 시트 (열 등록부에 「갈래」가 있는 시트 — 정본의 2 · 4~10 · 12 · 13번)
  열 등록부의 시간축 열은 **틀**이다(지금의 15열 구성 — H1~H3 · E1~E11 · TV). 열마다 「갈래」(FY실적 · 누계실적 · 잔여예측 · 연간예측 · 영구)와
  「구간」(상세 · 수렴)이 있고, 묶음 표는 갈래로도 묶는다(FY실적 · 누계 · 잔여 · 연간 · 상세 · 수렴 · 달아님).
  읽기(폴더, 기간=…) 에 가정 파일의 기간을 주면 틀의 시간축 열이 그 회차의 열(열 ID = 기간 ID)로 바뀐다(기간열.py).
  안 주면 틀 그대로 읽는다 — 열의 기간 속성은 책.json 의 「기본기간」에서 자리대로 받는다. 명세를 고치는 도구(범위 지문 · 다시쓰기 · 이름입히기)는 틀로 읽는다.
  이런 시트의 무늬 · 글 · 값 · 입력 · 병합의 열쇠와 수식 속 열 낱말은 시간축 열 ID(H1 · E1 …)를 못 박아 적지 않는다 —
  묶음 · 자리 이름(실적.끝 · 예측.첫 · 시간.4) · 그 줄 쓰임의 별칭 · @. · @<-1> · @TV 로 적는다. 다시쓰기는 적은 열쇠와 낱말을 그대로 지킨다.
  이 회차의 축에 없는 갈래의 묶음(누계 · 잔여 · 수렴 · 달아님)으로 적은 열쇠는 놓이는 칸이 없다(오류가 아니다).
"""
import sys
import os
import re
import json
import shutil
from collections import OrderedDict

from 공통 import (문맥, 손수식틀, 손수식쓰기, 틀같나, 배치오류, 손오류, 안견줌, 틀의함수, 모르는함수, 옛이웃열고치기,
                _이름맞나, 자리풀기, 자리열, 축갈래)
import 구조펴기

형식 = "줄무늬 3"       # 2 → 3: 이웃 열 표기가 @-1 에서 @<-1> 로 바뀌었다 · 시트 머리의 「가정묶음」 표시 · 줄이름.json
옛형식 = ("줄무늬 2",)   # 「python 줄무늬.py --옛꼴고치기」 로 옮길 수 있는 형식
줄덧속성 = ("선", "들여", "굵게")       # 표준 서식 길에서 쓰는 줄의 덧 속성(설계/2_배치_서식.md 7-1) — 없으면 안 적는다
줄종류들 = ("제목", "구획머리", "머리", "입력", "계산", "소계", "합계", "비율", "점검", "글", "빈줄")
# 열쇠 등록부 — 적는 차례이기도 하다. 여기 없는 열쇠는 오타로 보고 오류로 올린다
행열쇠 = ("id", "되풀이", "묶음끝", "조건", "이름", "단위", "종류", "서식", "쓰임", "표", "표머리", "시나리오", "적용열", "빈칸허용",
       "대조", "대조열",
       "선", "들여", "굵게", "높이", "입력", "무늬", "글", "값", "축값", "칸서식", "병합", "갈래", "덧", "메모")
머리열쇠 = ("시트", "이름", "열", "축", "묶음", "쓰임", "표", "덧이름", "가정묶음", "속성", "병합", "유효성", "조건부서식", "정의된이름", "메모")
열열쇠 = ("id", "옛", "종류", "갈래", "구간", "폭", "숨김", "수준", "접힘", "메모")
책열쇠 = ("형식", "원본", "시트순서", "조각", "기본기간", "되풀이", "구조기본", "기본구조", "시나리오칸", "정의된이름", "계산", "등록부밖허용",
        "허용함수", "메모")
조각열쇠 = ("조각", "이름", "메모")       # 조각 파일의 첫 객체(조각 머리) — 어느 시트의 조각인지와 풀이
_서식기본 = {"금액", "금액1", "비율", "비율2", "포인트", "배수", "일수", "인원", "주당", "주식수", "계수", "베타", "연수",
         "개월", "날짜", "판정", "글", "일반"}
줄길이한도, 조각한도 = 400, 110        # 이보다 긴 행은 여러 줄로, 이보다 긴 글은 조각으로 나눠 적는다
지문파일 = "범위지문.json"
이름파일 = "줄이름.json"
옛이름한도 = 4            # 줄 이름표에 줄마다 남겨 두는 옛 이름의 수(지금 이름 뒤에)
# 열 종류 등록부 — 열 등록부의 「종류」와 배치 새 열의 「종류」는 여기 있거나 그 시트의 묶음·축에 나오는 종류여야 한다(오타가 묶음에서 말없이 빠지지 않게)
열종류들 = ("여백", "이름", "단위", "번호", "실적", "예측", "영구", "값", "풀이", "근거", "보조", "비고", "방향", "방향점검", "역산",
        "소비처", "점검칸", "기타")
덧열쇠 = ("메모", "링크")                              # 줄의 「덧」 안쪽 열쇠
칸열쇠 = ("v", "t", "손수식", "메모", "링크")          # 배치 새 줄의 「칸」 · 배치 「덧칸」 안쪽 열쇠
값칸열쇠 = ("v", "t", "x", "배열수식", "배열범위")      # 「글」·「값」에 { } 로 적은 칸의 열쇠


def 아는열종류(머리):
    """그 시트에서 쓸 수 있는 열 종류 — 등록부 + 그 시트의 묶음·축에 나오는 종류."""
    안 = set(열종류들) | {k for k in (머리.get("축") or ()) if isinstance(k, str)}
    if any(isinstance(c, dict) and c.get("갈래") for c in 머리.get("열") or ()):
        안 |= set(축갈래)      # 기간 축의 열 갈래 — 시간축 열을 기간 축에서 받는 시트의 묶음 표에 적을 수 있다
    for 종류들 in (머리.get("묶음") or {}).values():
        안 |= {k for k in (종류들 if isinstance(종류들, list) else ()) if isinstance(k, str)}
    return 안


_서식기억 = []


def 서식이름들():
    """줄의 「서식」에 쓸 수 있는 이름 — 서식표준.서식표의 키(파일이 있으면) + 옛 서식에서 가늠해 붙이는 이름."""
    if not _서식기억:
        이름 = set(_서식기본)
        try:
            import 서식훅
            표준 = 서식훅._표준읽기(서식훅.표준경로)
            if 표준 is not None:
                이름 |= set(표준.서식표)
        except Exception:
            pass
        _서식기억.append(이름)
    return _서식기억[0]


# ───────────────────────── 문맥 ─────────────────────────
def 문맥만들기(명세):
    """열 ID 명세에서 손 수식 문맥을 만든다."""
    문 = 문맥()
    책 = 명세.get("책", {})
    문.엄한행 = bool(책.get("줄무늬")) and not 책.get("등록부밖허용")
    if "허용함수" not in 책 and not 책.get("줄무늬"):
        # 옛 xlsx 에서 뽑은 명세 — 엑셀 함수 목록에 없는 함수가 옛 수식에 있으면(스캐폴드의 _xlfn._LONGTEXT 따위) 받아 둔다.
        # 줄 무늬 명세로 쓸 때 책.json 의 「허용함수」에 실린다. 손으로 새로 적는 수식의 오타(SUMM)는 이 목록에 없으므로 오류로 걸린다
        import 범위지문
        책["허용함수"] = sorted({이름 for _, _, _, 틀 in 범위지문.수식들(명세) for 이름 in 틀의함수(틀) if 모르는함수(이름)})
    문.허용함수 = set(책.get("허용함수") or ())
    for sid, s in 명세["시트"].items():
        문.열순서[sid] = [c["id"] for c in s["열"]]
        문.열종류[sid] = {c["id"]: c.get("종류", "기타") for c in s["열"]}
        if any(c.get("갈래") for c in s["열"]):      # 시간축 열을 기간 축에서 받는 시트
            문.기간틀.add(sid)
            문.열덧[sid] = {c["id"]: {x for x in (c.get("갈래"), c.get("구간"), "달아님" if c.get("달아님") else None) if x}
                          for c in s["열"]}
            문.열기간[sid] = {c["id"]: c["기간"] for c in s["열"] if c.get("기간")}
        문.축[sid] = list(s.get("축", []))
        문.묶음[sid] = OrderedDict(s.get("묶음", {}))
        문.쓰임[sid] = s.get("쓰임", {})
        덧이름 = s.get("덧이름", {})
        for 줄 in s["행"]:
            문.행소속[줄["id"]] = sid
            if 줄.get("이름"):
                문.행이름[줄["id"]] = [줄["이름"]]
            if 줄.get("쓰임"):
                문.행쓰임[줄["id"]] = 줄["쓰임"]
        for 줄 in s["행"]:
            for 값열, 이름열 in 덧이름.get(줄.get("쓰임"), {}).items():      # 둘째 이름표가 있는 칸
                글 = _칸글(줄, 이름열, 문, sid)
                if 글:
                    문.칸이름[(줄["id"], 값열)] = 글
                    문.줄덧이름.setdefault(줄["id"], []).append(글)
    문.정의된이름 = {d["이름"] for d in 책.get("정의된이름", [])}
    for s in 명세["시트"].values():
        문.정의된이름 |= {d["이름"] for d in s.get("정의된이름", [])}
    return 문


def _칸글(줄, cid, 문, sid):
    """줄의 한 칸에 적힌 글(편 줄이면 칸에서, 날것이면 「글」에서 찾는다)."""
    if "칸" in 줄:
        v = 줄["칸"].get(cid, {}).get("v")
        return v if isinstance(v, str) else None
    for 키, v in (줄.get("무늬원") or {}).get("글", {}).items():
        if "~" not in 키 and 문.별칭풀기(sid, 줄["id"], 키) == cid and isinstance(v, str):
            return v
    return None


# ───────────────────────── 열 구간 ─────────────────────────
def 구간키(문, sid, rid, 열들):
    """이어진 열 ID 목록 → 열 구간 열쇠.

    그 줄의 쓰임이 별칭을 준 열이 끼어 있으면 묶음 이름을 쓰지 않는다(시점 가정의 비관~낙관은 「실적」이 아니다).
    """
    if sid in 문.기간틀:
        return _틀구간키(문, sid, rid, 열들)
    if len(열들) == 1:
        return 문.별칭쓰기(sid, rid, 열들[0])
    끝 = 문.별칭쓰기(sid, rid, 열들[-1])
    if not any(문.별칭쓰기(sid, rid, c) != c for c in 열들):
        for 이름 in 문.묶음.get(sid, {}):
            if 문.묶음열(sid, 이름) == 열들:
                return 이름
        for 이름 in 문.묶음.get(sid, {}):
            m = 문.묶음열(sid, 이름)
            if len(m) >= 2 and m[-1] == 열들[-1]:
                끝 = 이름
                break
    return "%s~%s" % (문.별칭쓰기(sid, rid, 열들[0]), 끝)


def _틀구간키(문, sid, rid, 열들):
    """시간축 열을 기간 축에서 받는 시트의 열 구간 열쇠 — 시간축 열은 열 ID 로 못 박지 않는다.

    그 줄 쓰임의 별칭이 있으면 별칭, 묶음 전체면 묶음 이름, 그 밖의 시간축 열은 「시간.k」(시간축의 k째 열 — 자리 그대로)로 적는다.
    적어 둔 열쇠가 남아 있는 칸은 이 길로 오지 않는다(_줄쓰기가 적은 열쇠를 그대로 낸다) — 낱칸을 코드로 고친 뒤의 길이다.
    """
    축 = 문.축열(sid)
    시간묶음 = "시간" if 문.묶음열(sid, "시간") else "실적"
    시간 = 문.묶음열(sid, 시간묶음) or []

    def 한(c):
        별 = 문.별칭쓰기(sid, rid, c)
        if 별 != c or c not in 축 or c not in 시간 or c == "TV":
            return 별
        return "%s.%d" % (시간묶음, 시간.index(c) + 1)

    if len(열들) == 1:
        return 한(열들[0])
    if not any(문.별칭쓰기(sid, rid, c) != c for c in 열들):
        for 이름 in 문.묶음.get(sid, {}):
            if 문.묶음열(sid, 이름) == 열들:
                return 이름
    return "%s~%s" % (한(열들[0]), 한(열들[-1]))


def 빈묶음되나(문, sid, 이름):
    """그 묶음은 비어 있어도 되는가 — 기간 축의 갈래만으로 된 묶음(누계 · 잔여 · 수렴 · 달아님 …)은 회차의 축에 따라 열이 없을 수 있다."""
    종류들 = 문.묶음.get(sid, {}).get(이름)
    return sid in 문.기간틀 and bool(종류들) and all(k in 축갈래 for k in 종류들)


def 구간풀기(문, sid, rid, 키, 순서=None):
    """열 구간 열쇠 → 열 ID 목록. 순서 = 열 순서(안 주면 명세의 열 순서. 짓기는 새 배치의 순서를 준다).

    기간 축의 갈래로 된 묶음(누계 · 잔여 · 수렴 …)이 이 회차에 비어 있으면, 그 묶음 하나(또는 그 묶음의 자리 하나)로 적은 열쇠는 빈 목록이다.
    """
    순 = 순서 if 순서 is not None else 문.열순서[sid]

    def 묶음(이름):
        return 문.묶음열(sid, 이름) if 순서 is None else \
            ([c for c in 순 if 문.든다(sid, c, 문.묶음[sid][이름])] if 이름 in 문.묶음.get(sid, {}) else None)

    def 끝점(낱, 첫):
        m = 묶음(낱)
        if m is not None:
            if not m:
                raise 손오류("빈 열 묶음: %s 의 %s" % (sid, 낱))
            return m[0] if 첫 else m[-1]
        자 = 자리풀기(낱)
        if 자 and 묶음(자[0]) is not None:      # 묶음의 몇째 열 하나(열이 늘면 따라간다)
            c = 자리열(묶음(자[0]), 자[1])
            if c is None:
                raise 손오류("%s 의 열 구간 「%s」 — 묶음 「%s」 에 그 자리가 없다(열 %d개)" % (rid or sid, 키, 자[0], len(묶음(자[0]))),
                           종류="자리 없음")
            return c
        cid = 문.별칭풀기(sid, rid, 낱)
        if cid is None or cid not in 순:
            raise 손오류("%s 의 열 구간 「%s」 — %s" % (rid or sid, 키, 문.별칭까닭(sid, rid, 낱)))
        return cid

    if not isinstance(키, str):
        raise 손오류("열 구간은 글로 적는다: %r" % (키,))
    낱들 = 키.split("~")
    if len(낱들) == 1:
        자 = 자리풀기(낱들[0])
        이름 = 낱들[0] if 낱들[0] in 문.묶음.get(sid, {}) else (자[0] if 자 and 자[0] in 문.묶음.get(sid, {}) else None)
        if 이름 is not None and not 묶음(이름) and 빈묶음되나(문, sid, 이름):
            return []
        if 낱들[0] in 문.묶음.get(sid, {}):
            a, b = 끝점(낱들[0], True), 끝점(낱들[0], False)
        else:
            a = b = 끝점(낱들[0], True)
    elif len(낱들) == 2:
        a, b = 끝점(낱들[0], True), 끝점(낱들[1], False)
    else:
        raise 손오류("열 구간을 읽을 수 없다: %s" % 키)
    i, j = 순.index(a), 순.index(b)
    if i > j:
        raise 손오류("열 구간의 두 끝이 뒤집혔다: %s" % 키)
    return 순[i:j + 1]


def _이어묶기(순서자리, 열값):
    """[(열 ID, 값)] → 이웃한 열(명세 순서로 바로 옆)이 같은 값이면 한 묶음으로. → [([열 ID …], 값)]"""
    묶음 = []
    for cid, v in sorted(열값, key=lambda kv: 순서자리[kv[0]]):
        if 묶음 and 묶음[-1][1] == v and type(묶음[-1][1]) is type(v) and \
                순서자리[묶음[-1][0][-1]] + 1 == 순서자리[cid]:
            묶음[-1][0].append(cid)
        else:
            묶음.append(([cid], v))
    return 묶음


_re묶음앞글 = re.compile(r"\]@!?\$?[A-Za-z가-힣_][A-Za-z0-9가-힣_]*<-\d+>")      # 손 수식 글 속의 「[행]@묶음<-k>」


# ───────────────────────── 범위 글(병합 · 유효성 · 조건부 서식) ─────────────────────────
_re범위글 = re.compile(r"^\[([^\]\[\s]+)\]@([^:\s]+)(?::\[([^\]\[\s]+)\]@([^:\s]+))?$")


def 범위쓰기(g):
    c, c2 = g.get("적은") or (g["c"], g["c2"])
    return "[%s]@%s:[%s]@%s" % (g["r"], c, g["r2"], c2)


def 범위읽기(글, 문, 엄한=False):
    """범위 글 → {"r","c","r2","c2"}. 엄한=True(배치가 준 범위)면 명세에 없는 행 ID 를 받지 않는다."""
    m = _re범위글.match(글.strip())
    if not m:
        raise 손오류("범위를 읽을 수 없다: %s" % 글)
    r1, c1, r2, c2 = m.group(1), m.group(2), m.group(3) or m.group(1), m.group(4) or m.group(2)
    for rid in (r1, r2):
        if 문.소속(rid) is None or ((엄한 or 문.엄한행) and rid not in 문.행소속):
            raise 손오류("범위의 행 ID 를 모른다: %s" % rid)
    sid = 문.소속(r1)
    if 문.소속(r2) != sid:
        raise 손오류("범위의 두 끝이 다른 시트다: %s" % 글)
    적은 = (c1, c2)
    c1, c2 = 문.별칭풀기(sid, r1, c1), 문.별칭풀기(sid, r2, c2)
    if c1 is None or c2 is None:
        raise 손오류("범위의 열을 모른다: %s" % 글)
    if sid in 문.기간틀 and 적은 != (c1, c2):      # 별칭으로 적은 범위 — 다시 쓸 때 열 ID 로 되돌리지 않는다
        return {"r": r1, "c": c1, "r2": r2, "c2": c2, "적은": list(적은)}
    return {"r": r1, "c": c1, "r2": r2, "c2": c2}


# ───────────────────────── 무늬 묶기(쓰기) ─────────────────────────
def _뼈대(틀):
    """열을 뺀 틀의 모양 — 같은 줄의 이웃 칸이 같은 무늬인지 견주는 데 쓴다."""
    낱 = []
    for p in 틀:
        if isinstance(p, str):
            낱.append(p)
        else:
            q = {k: v for k, v in p.items() if k not in 안견줌}
            if p["k"] in ("c", "r") and not p.get("g"):
                q.pop("c", None)
                q.pop("c2", None)
            낱.append(tuple(sorted(q.items())))
    return tuple(낱)


def _끝점들(틀, sid, cid, 문):
    """참조의 열 끝점마다 (절대인가, 열 ID, 이 칸에서의 간격)."""
    끝 = []
    for p in 틀:
        if isinstance(p, dict) and p["k"] in ("c", "r"):
            if p.get("g"):
                끝 += [("묶", None, None), ("묶", None, None)]
                continue
            for c, a in ((p["c"], p["a"]),) + (((p["c2"], p["a2"]),) if p["k"] == "r" else ()):
                끝.append(("절", c, None) if a[0] == "$" else ("상", c, 문.간격(sid, cid, c)))
    return 끝


def 무늬묶기(sid, rid, 수식칸, 문, 이름붙이기=True):
    """한 줄의 수식 칸 [(열 ID, 틀)] → [([열 ID …], 손 수식 글)].

    이웃한 칸의 수식이 「같은 열 · 직전 열 · 고정 열」로 적으면 같은 글이 되는 동안 한 묶음으로 잇는다.
    묶은 글을 칸마다 다시 틀로 읽어 원래 틀과 같은지 확인하고, 다르면 그 칸을 따로 적는다.
    """
    자리 = {c: i for i, c in enumerate(문.열순서[sid])}
    묶음 = []     # [열들, 틀들, 뼈대, 끝점 상태]
    for cid, 틀 in sorted(수식칸, key=lambda kv: 자리[kv[0]]):
        뼈, 끝 = _뼈대(틀), _끝점들(틀, sid, cid, 문)
        if 묶음:
            열들, 틀들, 앞뼈, 상태 = 묶음[-1]
            if 앞뼈 == 뼈 and 자리[열들[-1]] + 1 == 자리[cid] and len(상태) == len(끝):
                새상태, 된다 = [], True
                for (갈, c0, 간0, 가능), (갈2, c, 간) in zip(상태, 끝):
                    if 갈 != 갈2:
                        된다 = False
                        break
                    if 갈 == "묶":
                        새상태.append((갈, c0, 간0, 가능))
                        continue
                    새가능 = set()
                    if "고정" in 가능 and c == c0:
                        새가능.add("고정")
                    if 갈 == "상" and "상대" in 가능 and 간 is not None and 간 == 간0:
                        새가능.add("상대")
                    if not 새가능:
                        된다 = False
                        break
                    새상태.append((갈, c0, 간0, 새가능))
                if 된다:
                    열들.append(cid)
                    틀들.append(틀)
                    묶음[-1][3] = 새상태
                    continue
        묶음.append([[cid], [틀], 뼈,
                    [(갈, c, 간, {"고정"} | ({"상대"} if 갈 == "상" and 간 is not None else set())) for 갈, c, 간 in 끝]])
    결과 = []
    for 열들, 틀들, _, 상태 in 묶음:
        꼴 = None
        if len(열들) > 1:
            꼴 = [("상대" if "상대" in 가능 else "고정") if 갈 == "상" else None for 갈, _, _, 가능 in 상태]
        글 = 손수식쓰기(틀들[0], 열들[0], sid, 문, 꼴, 이름붙이기)
        # 되읽어 확인 — 묶은 글이 칸마다 원래 틀을 그대로 내는가
        좋은, 나쁜 = [], []
        for cid, 틀 in zip(열들, 틀들):
            try:
                같 = 틀같나(손수식틀(글, cid, sid, 문), 틀)
            except 배치오류:
                같 = False
            (좋은 if 같 else 나쁜).append((cid, 틀))
        if 나쁜:
            좋은, 나쁜 = [], list(zip(열들, 틀들))        # 한 칸이라도 어긋나면 묶음을 풀어 칸마다 적는다
        if 좋은:
            결과.append((열들, 글))
        for cid, 틀 in 나쁜:
            글1 = 손수식쓰기(틀, cid, sid, 문, None, 이름붙이기)
            try:
                같 = 틀같나(손수식틀(글1, cid, sid, 문), 틀)
            except 배치오류 as e:
                raise 손오류("틀을 손 수식으로 적었다가 되읽지 못했다: %s %s — %s (%s)" % (rid, cid, 글1[:160], e.오류목록[0]["설명"][:120]))
            if not 같:
                raise 손오류("틀을 손 수식으로 적었다가 되읽으니 달라졌다: %s %s — %s" % (rid, cid, 글1[:200]))
            결과.append(([cid], 글1))
    return 결과


# ───────────────────────── 적는 꼴(차례 · 여러 줄 · 조각) ─────────────────────────
def _차례(d, 열쇠):
    """dict 를 등록부의 차례로(등록부에 없는 열쇠는 뒤에 그대로)."""
    낸 = OrderedDict((k, d[k]) for k in 열쇠 if k in d)
    for k in d:
        if k not in 낸:
            낸[k] = d[k]
    return 낸


_re끊을곳 = re.compile(r'"(?:[^"]|"")*"|\[[^\]\[]*\]@[^,&;)(+\-*/<>=\s]*|[,&;]')


def _조각내기(글):
    """긴 글 → 조각 목록(이어 붙이면 원문). 수식은 쉼표·&·; 뒤에서(문자열 상수와 참조 안은 안 끊는다), 글은 빈칸 뒤에서 끊는다."""
    if len(글) <= 조각한도:
        return 글
    곳 = []
    if 글.startswith("="):
        for m in _re끊을곳.finditer(글):
            if m.group(0) in ",&;":
                곳.append(m.end())
            elif m.group(0)[0] == '"' and len(m.group(0)) > 조각한도:        # 긴 문자열 상수 안 — 빈칸 뒤
                곳 += [m.start() + k + 1 for k, ch in enumerate(m.group(0)) if ch == " " and 0 < k < len(m.group(0)) - 1]
    else:
        곳 = [k + 1 for k, ch in enumerate(글) if ch == " "]
    낸, 앞 = [], 0
    for i in 곳:
        if i - 앞 >= 조각한도 * 2 // 3 and len(글) - i > 12:
            낸.append(글[앞:i])
            앞 = i
    낸.append(글[앞:])
    while any(len(x) > 조각한도 * 3 for x in 낸):       # 끊을 곳이 없는 긴 조각 — 글자 수로 끊는다
        낸 = [y for x in 낸 for y in ([x[k:k + 조각한도 * 2] for k in range(0, len(x), 조각한도 * 2)] if len(x) > 조각한도 * 3 else [x])]
    return 낸 if len(낸) > 1 else 글


def _잇기(v):
    """조각 목록으로 적은 글 → 글 하나."""
    if isinstance(v, list) and v and all(isinstance(x, str) for x in v):
        return "".join(v)
    return v


def _값글(v, 들여):
    """값 하나를 JSON 글로 — 긴 글은 조각 목록을 한 줄에 하나씩."""
    if isinstance(v, str):
        조각 = _조각내기(v)
        if isinstance(조각, list):
            틈 = "\n" + " " * (들여 + 1)
            return "[" + 틈 + ("," + 틈).join(json.dumps(x, ensure_ascii=False) for x in 조각) + "]"
    return json.dumps(v, ensure_ascii=False)


def 줄글(낸):
    """행 한 줄(dict) → 파일에 적을 글. 짧으면 한 줄, 길면 열쇠마다 한 줄."""
    한줄 = json.dumps(낸, ensure_ascii=False)
    if len(한줄) <= 줄길이한도:
        return 한줄
    짧은, 긴 = [], []
    for 키, v in 낸.items():
        if 키 in ("무늬", "글", "값") and isinstance(v, dict):
            안 = ["  %s: %s" % (json.dumps(k, ensure_ascii=False), _값글(x, 2)) for k, x in v.items()]
            긴.append(" %s: {\n%s}" % (json.dumps(키, ensure_ascii=False), ",\n".join(안)))
        elif 키 in ("이름", "단위", "메모") and isinstance(v, str) and len(v) > 조각한도:
            긴.append(" %s: %s" % (json.dumps(키, ensure_ascii=False), _값글(v, 1)))
        elif 키 in ("입력", "병합", "덧"):
            긴.append(" %s: %s" % (json.dumps(키, ensure_ascii=False), json.dumps(v, ensure_ascii=False)))
        else:
            (짧은 if not 긴 else 긴).append(("%s: %s" if not 긴 else " %s: %s") % (
                json.dumps(키, ensure_ascii=False), json.dumps(v, ensure_ascii=False)))
    return "{" + ", ".join(짧은) + (",\n" if 긴 and 짧은 else "") + ",\n".join(긴) + "}"


def 머리글(머리):
    """시트 머리(dict) → 파일에 적을 글. 열쇠마다 한 줄, 열 등록부는 열마다 한 줄."""
    줄 = []
    for 키, v in 머리.items():
        이름 = json.dumps(키, ensure_ascii=False)
        if 키 == "열":
            줄.append(" %s: [\n%s]" % (이름, ",\n".join("  " + json.dumps(c, ensure_ascii=False) for c in v)))
        elif 키 in ("유효성", "조건부서식", "정의된이름", "병합") and isinstance(v, list) and v:
            줄.append(" %s: [\n%s]" % (이름, ",\n".join("  " + json.dumps(c, ensure_ascii=False) for c in v)))
        else:
            줄.append(("%s: %s" if not 줄 else " %s: %s") % (이름, json.dumps(v, ensure_ascii=False)))
    return "{" + ",\n".join(줄) + "}"


def 시트쓰기(경로, 머리, 줄들):
    """날것(시트읽기가 준 것과 같은 꼴)을 표준 꼴로 파일에 적는다 — 명세를 코드로 고칠 때 쓴다.

    열쇠의 차례를 맞추고 긴 행을 여러 줄로 적는다. 수식에 덧붙인 이름을 지금 이름에 맞추는 일은 「다시쓰기」가 한다.
    조각 파일로 가른 시트(책.json 의 「조각」)는 줄마다 온 파일(날줄.파일)에 되돌려 적는다 — 코드로 끼운 줄(파일 표시가 없는 줄)은
    바로 앞 줄의 파일에 든다. 한 파일의 줄은 한데 붙어 있어야 한다(조각을 이어 읽은 차례가 곧 줄 차례다).
    """
    본 = os.path.basename(경로)
    조각머리 = getattr(머리, "조각머리", None) or {}
    묶음, 앞 = OrderedDict([(본, [])]), 본
    for x in 줄들:
        파일 = getattr(x, "파일", None) or 앞
        if 파일 not in 묶음:
            if 파일 not in 조각머리:
                raise SystemExit("%s — 줄 %s 이 온 파일 「%s」 이 이 시트의 조각이 아니다" % (본, x.get("id"), 파일))
            묶음[파일] = []
        elif 파일 != 앞:
            raise SystemExit("%s — 조각 「%s」 의 줄이 한데 붙어 있지 않다(줄 %s). 조각을 이어 읽은 차례가 줄 차례다" % (본, 파일, x.get("id")))
        묶음[파일].append(x)
        앞 = 파일
    for 파일 in 조각머리:
        묶음.setdefault(파일, [])
    for 파일, 든 in 묶음.items():
        첫 = 머리글(_차례(머리, 머리열쇠)) if 파일 == 본 else json.dumps(_차례(조각머리[파일], 조각열쇠), ensure_ascii=False)
        with open(os.path.join(os.path.dirname(경로), 파일), "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join([첫] + [줄글(_차례(x, 행열쇠)) for x in 든]) + "\n")


# ───────────────────────── 쓰기 ─────────────────────────
def _값쓰기(한):
    """상수 칸 → 줄 무늬의 값. 글은 str, 숫자·참거짓은 그대로, 그 밖은 {"v","t"}."""
    if "t" in 한:
        return {"v": 한["v"], "t": 한["t"]}
    return 한["v"]


def _줄쓰기(시트, 줄, 문, 이름붙이기):
    sid, rid = 시트["id"], 줄["id"]
    순 = 문.열순서[sid]
    자리 = {c: i for i, c in enumerate(순)}
    종 = 문.열종류[sid]
    이름열 = next((c for c in 순 if 종[c] == "이름"), None)
    단위열 = next((c for c in 순 if 종[c] == "단위"), None)
    낸 = OrderedDict(id=rid)
    수식칸, 글칸, 값칸, 덧 = [], [], [], OrderedDict()
    # 시간축 열을 기간 축에서 받는 시트 — 적어 둔 열쇠가 온전한 칸(그 열쇠가 놓은 칸이 그대로 다 남았다)은 그 열쇠로 다시 적는다
    적힌 = OrderedDict()      # (갈래, 열쇠) → [열 ID …]
    열쇠순 = 줄.get("열쇠순") if sid in 문.기간틀 else None
    if 열쇠순:
        for 갈, 키0 in 열쇠순:
            if 갈 == "축값":
                continue
            try:
                기대 = [c for c in 구간풀기(문, sid, rid, 키0) if 줄["칸"].get(c, {}).get("갈") != "축값"]
            except 배치오류:
                continue
            if 기대 and all(줄["칸"].get(c, {}).get("열쇠") == 키0 and 줄["칸"][c].get("갈") == 갈 for c in 기대):
                적힌[(갈, 키0)] = 기대
    든칸 = {c for 열들 in 적힌.values() for c in 열들}
    for cid, 한 in 줄["칸"].items():
        if cid in 든칸 or 한.get("갈") == "축값":
            for 키 in ("메모", "링크"):
                if 키 in 한:
                    덧.setdefault(cid, OrderedDict())[키] = 한[키]
            continue
        if "배열" in 한:
            값칸.append((cid, {"배열수식": 손수식쓰기(한["f"], cid, sid, 문, None, 이름붙이기),
                             "배열범위": 손수식쓰기(한["배열"], cid, sid, 문, None, False)}))
        elif "f" in 한:
            수식칸.append((cid, 한["f"]))
        elif "x" in 한:
            값칸.append((cid, {"x": 한["x"]}))
        elif "v" in 한:
            v = _값쓰기(한)
            (글칸 if isinstance(v, str) else 값칸).append((cid, v))
        for 키 in ("메모", "링크"):
            if 키 in 한:
                덧.setdefault(cid, OrderedDict())[키] = 한[키]
    def 키(열들):
        # 「예측.끝」처럼 묶음의 첫·끝 열로 적은 열쇠는 그대로 지킨다(열 ID 로 되돌리면 그 열에 못 박힌다)
        적은 = 줄["칸"][열들[0]].get("열쇠") if len(열들) == 1 else None
        if 적은:
            try:
                if 구간풀기(문, sid, rid, 적은) == 열들:
                    return 적은
            except 배치오류:
                pass
        return 구간키(문, sid, rid, 열들)

    무늬, 글, 값, 축값 = OrderedDict(), OrderedDict(), OrderedDict(), OrderedDict()
    for 갈, 키0 in 열쇠순 or ():
        if 갈 == "축값":
            축값[키0] = (줄.get("축값") or {}).get(키0)
            continue
        열들 = 적힌.get((갈, 키0))
        if not 열들:
            if (갈, 키0) in (줄.get("열쇠원") or {}):      # 틀에 그 갈래의 열이 없는 묶음으로 적은 것 — 적어 둔 글 그대로
                {"무늬": 무늬, "글": 글, "값": 값}[갈][키0] = 줄["열쇠원"][(갈, 키0)]
            continue
        첫 = 줄["칸"][열들[0]]
        원글 = (줄.get("열쇠원") or {}).get((갈, 키0))
        if "f" in 첫 and 갈 == "무늬" and isinstance(원글, str) and _re묶음앞글.search(원글):
            무늬[키0] = 원글      # 「@묶음<-k>」 를 쓴 무늬 — 묶음을 벗어난 열에서는 숫자 0 이라 틀이 열마다 다르다. 적힌 그대로 둔다
            continue
        if "f" in 첫:
            한글 = 손수식쓰기(첫["f"], 열들[0], sid, 문, None, 이름붙이기, 적은대로=True)
            for c in 열들:      # 되읽어 확인 — 그 열쇠의 칸마다 같은 틀이 나오는가
                try:
                    같 = 틀같나(손수식틀(한글, c, sid, 문), 줄["칸"][c]["f"])
                except 배치오류 as e:
                    raise 손오류("적어 둔 열쇠로 다시 적은 수식을 되읽지 못했다: %s 의 「%s」 열 %s — %s (%s)" % (
                        rid, 키0, c, 한글[:120], e.오류목록[0]["설명"][:120]))
                if not 같:
                    raise 손오류("적어 둔 열쇠로 다시 적은 수식이 그 칸의 틀과 다르다: %s 의 「%s」 열 %s — %s" % (rid, 키0, c, 한글[:160]))
            if "배열" in 첫:
                값[키0] = {"배열수식": 한글, "배열범위": 손수식쓰기(첫["배열"], 열들[0], sid, 문, None, False, 적은대로=True)}
            else:
                무늬[키0] = 한글
        elif "x" in 첫:
            값[키0] = {"x": 첫["x"]}
        elif "v" in 첫:
            {"글": 글, "값": 값}.get(갈, 값)[키0] = _값쓰기(첫)
    for 열들, 한글 in 무늬묶기(sid, rid, 수식칸, 문, 이름붙이기):
        if 열들 == [이름열]:
            낸["이름"] = 한글
        elif 열들 == [단위열]:
            낸["단위"] = 한글
        else:
            무늬[키(열들)] = 한글
    for 열들, v in _이어묶기(자리, 글칸):
        if 열들 == [이름열]:
            낸["이름"] = v
        elif 열들 == [단위열]:
            낸["단위"] = v
        else:
            글[키(열들)] = v
    for 열들, v in _이어묶기(자리, 값칸):
        값[키(열들)] = v
    for 키 in ("종류", "서식", "쓰임") + 줄덧속성 + ("높이",):
        if 줄.get(키):
            낸[키] = 줄[키]
    if 줄.get("입력"):
        입력원 = 줄.get("입력원") if sid in 문.기간틀 else None
        try:
            같은 = 입력원 is not None and [c for 키1 in 입력원 for c in 구간풀기(문, sid, rid, 키1)] == list(줄["입력"])
        except 배치오류:
            같은 = False
        낸["입력"] = list(입력원) if 같은 else \
            [구간키(문, sid, rid, 열들) for 열들, _ in _이어묶기(자리, [(c, 1) for c in 줄["입력"]])]
    if 무늬:
        낸["무늬"] = 무늬
    if 글:
        낸["글"] = 글
    if 값:
        낸["값"] = 값
    if 축값:
        낸["축값"] = 축값
    병합 = [g for g in 시트["병합"] if g["r"] == rid and g["r2"] == rid]
    if 병합:
        def 병합키(g):
            열들 = 순[자리[g["c"]]:자리[g["c2"]] + 1]
            if sid in 문.기간틀 and g.get("키"):      # 적어 둔 열쇠가 같은 열들을 가리키면 그대로
                try:
                    if 구간풀기(문, sid, rid, g["키"]) == 열들:
                        return g["키"]
                except 배치오류:
                    pass
            return 구간키(문, sid, rid, 열들)
        낸["병합"] = [병합키(g) for g in 병합]
    if 덧:
        낸["덧"] = 덧
    if 줄.get("메모"):
        낸["메모"] = 줄["메모"]
    # 옛 서식 — 칸별 서식 번호(이어진 열은 묶어서) · 행 높이 · 숨김 · 묶음 수준
    옛 = OrderedDict()
    s칸 = [(cid, 한["s"]) for cid, 한 in 줄["칸"].items() if "s" in 한]
    if s칸:
        옛["s"] = OrderedDict(("%s~%s" % (열들[0], 열들[-1]) if len(열들) > 1 else 열들[0], n)
                             for 열들, n in _이어묶기(자리, s칸))
    속 = [cid for cid, 한 in 줄["칸"].items() if 한.get("병합속")]
    if 속:
        옛["병합속"] = 속
    for 키 in ("height", "hidden", "outlineLevel", "collapsed"):
        if 줄.get(키):
            옛[키] = 줄[키]
    return _차례(낸, 행열쇠), 옛


def _등록부밖있나(명세, 문):
    """명세의 수식이 등록부에 없는 행 ID 를 가리키는 곳이 있는가(옛 xlsx 가 끝 줄 아래의 빈 줄을 읽던 것)."""
    for s in 명세["시트"].values():
        for 줄 in s["행"]:
            for 한 in 줄["칸"].values():
                for 키 in ("f", "배열"):
                    for p in 한.get(키) or ():
                        if isinstance(p, dict) and p["k"] in ("c", "r", "R") and \
                                any(rid not in 문.행소속 for rid in (p["r"], p.get("r2", p["r"]))):
                            return True
    return False


def 쓰기(명세, 폴더, 이름붙이기=True, 지문쓰기=True, 덧시트쓰기=False):
    """열 ID 명세 → 줄 무늬 명세 폴더. → 요약(수)

    지문쓰기   : 범위 지문(범위지문.json)을 이 명세에서 새로 낸다 — xlsx 에서 새로 뽑을 때만 참.
                 「다시쓰기」는 거짓으로 부른다(범위 지문은 승인 명령으로만 고친다).
    덧시트쓰기 : 폴더 밖의 파일로 읽은 시트(새 시트)를 제 파일에 다시 쓴다(「다시쓰기」의 --덧명세).
    줄 이름표(줄이름.json)는 늘 지금 이름으로 고쳐 적는다.
    """
    if not 명세["책"].get("열ID"):
        raise SystemExit("열 ID 명세가 아니다 — 열표.적용 을 먼저 거친다")
    if 명세.get("기간"):
        raise SystemExit("회차의 기간으로 편 명세는 줄 무늬 명세로 쓰지 않는다 — 명세는 틀로 읽어(기간을 주지 않고) 고친다")
    os.makedirs(os.path.join(폴더, "옛서식"), exist_ok=True)
    문 = 문맥만들기(명세)
    문.엄한행 = False             # 적은 글을 되읽어 확인할 때는 등록부 밖의 줄도 받는다(아래에서 따로 센다)
    수 = {"시트": 0, "행": 0, "수식 칸": 0, "무늬(이어진 구간)": 0, "글 칸": 0, "글 구간": 0, "값 칸": 0}
    for sid, s in 명세["시트"].items():
        if s.get("덧파일") and not (덧시트쓰기 and s.get("경로")):     # 폴더 밖의 파일로 읽은 시트(새 시트)는 이 폴더에 쓰지 않는다
            continue
        머리 = OrderedDict(시트=sid, 이름=s.get("옛이름") or s.get("이름"))
        머리["열"] = []
        머리원 = s.get("머리원")
        for c in s["열"]:
            한 = OrderedDict(id=c["id"])
            if c.get("옛"):
                한["옛"] = c["옛"]
            한["종류"] = c.get("종류", "기타")
            for 영, 한글 in (("width", "폭"), ("hidden", "숨김"), ("outlineLevel", "수준"), ("collapsed", "접힘")):
                if c.get(영):
                    한[한글] = c[영]
            if c.get("메모"):
                한["메모"] = c["메모"]
            머리["열"].append(한)
        for 키 in ("축", "묶음", "쓰임", "덧이름", "가정묶음"):
            if s.get(키):
                머리[키] = s[키]
        머리["속성"] = s.get("속성", {})
        if 머리원 is not None:      # 시간축 열을 기간 축에서 받는 시트 — 열 등록부(틀)와 자리 이름으로 적은 것(쓰임 · 덧이름 · 틀 고정)은 적은 그대로
            for 키 in ("열", "쓰임", "덧이름", "속성"):
                if 키 in 머리원:
                    머리[키] = 머리원[키]
        if s.get("표원"):      # 표 구획이 선 시트 — 묶음 「표칸」 · 표의 별칭 · 덧 열은 생성기가 더한 것이다. 적힌 그대로 되돌린다
            for 키, v in s["표원"].items():
                머리[키] = v
        if s.get("표정의"):
            머리["표"] = s["표정의"]
        여러줄 = [g for g in s["병합"] if g["r"] != g["r2"]]
        if 여러줄:
            머리["병합"] = [범위쓰기(g) for g in 여러줄]
        첫열 = s["열"][0]["id"] if s["열"] else None
        if s.get("유효성"):
            머리["유효성"] = []
            for v in s["유효성"]:
                한 = OrderedDict((k, x) for k, x in v.items() if k not in ("범위", "formula1", "formula2"))
                한["범위"] = [범위쓰기(g) for g in v["범위"]]
                for 키 in ("formula1", "formula2"):
                    if 키 in v:
                        한[키] = 손수식쓰기(v[키], v["범위"][0]["c"], sid, 문, None, False)
                머리["유효성"].append(한)
        if s.get("조건부서식"):
            머리["조건부서식"] = [OrderedDict(범위=[범위쓰기(g) for g in c["범위"]], 규칙=c["규칙"],
                                         수식=[손수식쓰기(f, c["범위"][0]["c"], sid, 문, None, False) for f in c["수식"]],
                                         서식=c.get("서식")) for c in s["조건부서식"]]
        if s.get("정의된이름"):
            머리["정의된이름"] = [{"이름": d["이름"], "수식": 손수식쓰기(d["틀"], 첫열, sid, 문, None, False)}
                             for d in s["정의된이름"]]
        if s.get("메모"):
            머리["메모"] = s["메모"]
        본파일 = os.path.basename(s["경로"]) if s.get("덧파일") and s.get("경로") else sid + ".jsonl"
        조각머리 = s.get("조각머리") or {}
        줄들, 옛서식 = [머리글(_차례(머리, 머리열쇠))], OrderedDict()
        조각줄 = OrderedDict((이름, [json.dumps(_차례(한, 조각열쇠), ensure_ascii=False)]) for 이름, 한 in 조각머리.items())
        앞조각, 끝난 = 본파일, set()
        틀표 = OrderedDict()      # 바로 앞의 보통 줄 ID → [틀의 날것 …] — 틀인 줄(구조펴기)은 적힌 그대로 되돌려 적는다
        for 앞줄, 틀낸 in s.get("틀줄들") or ():
            틀표.setdefault(앞줄, []).append(틀낸)

        def 틀적기(앞줄):
            for 틀낸 in 틀표.pop(앞줄, ()):
                곳 = getattr(틀낸, "파일", None)
                (조각줄[곳] if 곳 in 조각줄 else 줄들).append(줄글(_차례(틀낸, 행열쇠)))
                수["틀인 줄"] = 수.get("틀인 줄", 0) + 1

        틀적기(None)
        for 줄 in s["행"]:
            if 줄.get("틀줄"):      # 틀을 펴서 나온 줄 — 틀을 적는다
                continue
            낸, 옛 = _줄쓰기(s, 줄, 문, 이름붙이기)
            이조각 = 줄.get("조각") if 줄.get("조각") in 조각줄 or 줄.get("조각") == 본파일 else 앞조각      # 코드로 끼운 줄은 앞 줄의 파일에
            if 이조각 != 앞조각:
                끝난.add(앞조각)
                if 이조각 in 끝난:
                    raise SystemExit("%s — 조각 「%s」 의 줄이 한데 붙어 있지 않다(줄 %s)" % (sid, 이조각, 줄["id"]))
                앞조각 = 이조각
            (줄들 if 이조각 == 본파일 else 조각줄[이조각]).append(줄글(낸))
            if 옛:
                옛서식[줄["id"]] = 옛
            수["행"] += 1
            수["수식 칸"] += sum(1 for 한 in 줄["칸"].values() if "f" in 한)
            수["무늬(이어진 구간)"] += len(낸.get("무늬", {})) + sum(
                1 for 키 in ("이름", "단위") if str(낸.get(키, "")).startswith("=") and
                "f" in 줄["칸"].get(next((c["id"] for c in s["열"] if c["종류"] == 키), ""), {}))
            수["글 칸"] += sum(1 for 한 in 줄["칸"].values() if isinstance(한.get("v"), str) and "t" not in 한)
            수["글 구간"] += len(낸.get("글", {})) + sum(1 for 키 in ("이름", "단위") if 키 in 낸 and not str(낸[키]).startswith("="))
            수["값 칸"] += len(낸.get("값", {}))
            틀적기(줄["id"])
        for 앞줄 in list(틀표):      # 앞의 보통 줄이 없어진 틀 — 끝에 적는다
            틀적기(앞줄)
        if s.get("덧파일"):
            with open(s["경로"], "w", encoding="utf-8", newline="\n") as f:
                f.write("\n".join(줄들) + "\n")
            수["덧명세 시트"] = 수.get("덧명세 시트", 0) + 1
            continue
        with open(os.path.join(폴더, sid + ".jsonl"), "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(줄들) + "\n")
        for 이름, 든 in 조각줄.items():
            with open(os.path.join(폴더, 이름), "w", encoding="utf-8", newline="\n") as f:
                f.write("\n".join(든) + "\n")
        with open(os.path.join(폴더, "옛서식", sid + ".json"), "w", encoding="utf-8") as f:
            json.dump(옛서식, f, ensure_ascii=False, separators=(",", ":"))
        수["시트"] += 1
    책 = 명세["책"]
    낼책 = OrderedDict(형식=형식, 원본=os.path.basename(책["원본"]) if 책.get("원본") else None,       # 절대 경로는 싣지 않는다
                    시트순서=[sid for sid, s in 명세["시트"].items() if not s.get("덧파일")],
                    정의된이름=[{"이름": d["이름"], "수식": 손수식쓰기(d["틀"], None, None, 문, None, False)}
                            for d in 책.get("정의된이름", [])],
                    계산=책.get("계산", {"fullCalcOnLoad": True}))
    for 키 in ("조각", "기본기간", "되풀이", "구조기본", "기본구조", "시나리오칸"):
        if 책.get(키):
            낼책[키] = 책[키]
    if 책.get("등록부밖허용") or _등록부밖있나(명세, 문):
        낼책["등록부밖허용"] = True      # 옛 xlsx 가 끝 줄 아래의 빈 줄을 읽는다 — 읽을 때 오류로 올리지 않는다
    if 문.허용함수:
        낼책["허용함수"] = sorted(문.허용함수)
    if 책.get("메모"):
        낼책["메모"] = 책["메모"]
    with open(os.path.join(폴더, "책.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(_차례(낼책, 책열쇠), f, ensure_ascii=False, indent=1)
        f.write("\n")
    with open(os.path.join(폴더, "옛서식", "책.json"), "w", encoding="utf-8") as f:
        json.dump({"서식표": 책.get("서식표"), "서식조합": 책.get("서식조합"), "기본글꼴": 책.get("기본글꼴")},
                  f, ensure_ascii=False, separators=(",", ":"))
    if 명세.get("테마"):
        with open(os.path.join(폴더, "테마.xml"), "wb") as f:
            f.write(명세["테마"])
    for 이름 in ("목록_좌표의존함수.json",):       # 못 바꾸는 함수 목록은 그대로 옮겨 둔다(짓기가 알린다)
        원 = os.path.join(명세.get("폴더") or "", 이름)
        if os.path.exists(원) and os.path.abspath(원) != os.path.abspath(os.path.join(폴더, 이름)):
            shutil.copyfile(원, os.path.join(폴더, 이름))
    if 지문쓰기:
        import 범위지문
        범위지문.쓰기(os.path.join(폴더, 지문파일), 범위지문.만들기(명세, 덧시트=False))
    이름표쓰기(명세, 폴더, 문, 덧시트=덧시트쓰기)
    수["덧붙인 이름 경고"] = sum(문.이름경고.values())
    return 수


# ───────────────────────── 줄 이름표(줄이름.json) ─────────────────────────
# 수식에 덧붙인 이름이 지금 줄 이름과 다를 때, 「줄 이름을 고쳐서」 달라진 것인지 「행 ID 를 틀리게 적어서」 달라진 것인지를
# 가리는 기준이다. 줄마다 마지막으로 맞춰 둔 이름(과 그 줄의 칸 이름)을 적는다. 「다시쓰기」와 xlsx 에서 새로 뽑기가 고쳐 적는다.
# 이름을 고치면 옛 이름을 몇 개(옛이름한도) 뒤에 남긴다 — 다시쓰기를 덧명세 없이 먼저 돌려 이름표가 새 이름으로 바뀐 뒤에도,
# 덧명세(새 시트 파일)에 남은 옛 덧붙인 이름이 「줄 이름을 고친 것」으로 가려진다(「행 ID 를 본다」는 헛알림이 안 난다).
def _이름표곳(명세, sid, 폴더=None):
    s = 명세["시트"][sid]
    if s.get("덧파일") and s.get("경로"):
        return os.path.join(os.path.dirname(s["경로"]), 이름파일)
    return os.path.join(폴더 or 명세["폴더"], 이름파일)


def 줄이름들(문, rid):
    """그 줄을 부를 수 있는 이름들 — 줄 이름 + 그 줄의 칸 이름(둘째 이름표)."""
    return [x for x in list(문.행이름.get(rid) or ()) + list(문.줄덧이름.get(rid) or ()) if isinstance(x, str) and x]


def 이름표읽기(명세, 폴더=None):
    """적어 둔 줄 이름표 → {행 ID: [이름 …]}. 파일이 없는 시트의 줄은 들어 있지 않다. 둘째 값 = 이름표 파일이 없는 시트들."""
    표, 기억, 없는 = {}, {}, []
    for sid in 명세["시트"]:
        곳 = _이름표곳(명세, sid, 폴더)
        if 곳 not in 기억:
            try:
                with open(곳, encoding="utf-8") as f:
                    기억[곳] = json.load(f).get("시트") or {}
            except (OSError, ValueError):
                기억[곳] = None
        if 기억[곳] is None or sid not in 기억[곳]:
            없는.append(sid)
            continue
        for rid, v in 기억[곳][sid].items():
            표[rid] = [v] if isinstance(v, str) else list(v)
    return 표, 없는


def 이름표쓰기(명세, 폴더, 문, 덧시트=False):
    """지금 줄 이름으로 줄 이름표를 고쳐 적는다 — 줄 하나에 한 줄(diff 로 읽히게)."""
    곳별 = OrderedDict()
    for sid, s in 명세["시트"].items():
        if s.get("덧파일") and not (덧시트 and s.get("경로")):
            continue
        곳별.setdefault(_이름표곳(명세, sid, 폴더), OrderedDict())[sid] = s

    def 한줄(v):
        return json.dumps(v, ensure_ascii=False, separators=(",", ":"))

    for 곳, 시트들 in 곳별.items():
        try:
            with open(곳, encoding="utf-8") as f:
                있던 = json.load(f, object_pairs_hook=OrderedDict).get("시트") or {}
        except (OSError, ValueError):
            있던 = {}
        남길 = OrderedDict((k, v) for k, v in 있던.items() if k not in 명세["시트"])      # 이번에 읽지 않은 시트(다른 덧명세)의 것은 그대로 둔다
        글 = ['{', ' "형식": "줄이름 1",',
             ' "설명": "줄마다 마지막으로 맞춰 둔 이름. 손으로 고치지 않는다 — python 줄무늬.py --다시쓰기 가 고쳐 적는다.",', ' "시트": {']
        몸 = []
        for sid, v in 남길.items():
            몸.append("  %s: {\n%s\n  }" % (한줄(sid), ",\n".join("   %s: %s" % (한줄(k), 한줄(x)) for k, x in v.items())))
        for sid, s in 시트들.items():
            낱 = []
            for 줄 in s["행"]:
                이름 = 줄이름들(문, 줄["id"])
                옛 = (있던.get(sid) or {}).get(줄["id"])
                옛 = [옛] if isinstance(옛, str) else list(옛 or ())
                이름 = 이름 + [x for x in 옛 if x not in 이름][:옛이름한도]      # 지금 이름(과 칸 이름)이 앞, 옛 이름이 뒤
                if 이름:
                    낱.append("   %s: %s" % (한줄(줄["id"]), 한줄(이름[0] if len(이름) == 1 else 이름)))
            몸.append("  %s: {\n%s\n  }" % (한줄(sid), ",\n".join(낱)))
        글 += [",\n".join(몸), ' }', '}']
        with open(곳, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(글) + "\n")


# ───────────────────────── 읽기 ─────────────────────────
class 날줄(OrderedDict):
    """명세 파일의 객체 하나(날것). 어느 파일 몇째 줄에서 왔는지 달고 다닌다."""
    파일 = None
    줄번호 = None


class _겹친열쇠(Exception):
    pass


def _짝훅(짝들):
    d = 날줄()
    for k, v in 짝들:
        if k in d:
            raise _겹친열쇠(k)
        d[k] = v
    return d


def _읽기오류(경로, 줄, 설명, 종류="명세 읽기", 시트=None, 자리=None):
    이름 = os.path.basename(경로) if 경로 else None
    머리 = ("%s %s째 줄 — " % (이름, 줄)) if 줄 else (("%s — " % 이름) if 이름 else "")
    return {"종류": 종류, "시트": 시트, "자리": 자리, "설명": 머리 + 설명, "파일": 이름, "줄": 줄}


def _객체들(경로):
    """파일 → [날줄 …]. 행 하나가 여러 줄에 걸쳐 적혀 있어도 된다(JSON 객체가 이어진 꼴). 문법 오류면 배치오류."""
    try:
        with open(경로, encoding="utf-8") as f:
            글 = f.read()
    except OSError as e:
        raise 배치오류([_읽기오류(경로, None, "파일을 읽을 수 없다: %s" % e)])
    if 글.startswith("﻿"):
        글 = 글[1:]
    해독 = json.JSONDecoder(object_pairs_hook=_짝훅)
    i, n, 낸 = 0, len(글), []
    while True:
        while i < n and 글[i] in " \t\r\n":
            i += 1
        if i >= n:
            break
        줄 = 글.count("\n", 0, i) + 1
        try:
            객, j = 해독.raw_decode(글, i)
        except _겹친열쇠 as e:
            raise 배치오류([_읽기오류(경로, 줄, "같은 열쇠가 두 번 적혔다: 「%s」 (뒤엣것만 남으므로 받지 않는다)" % e.args[0])])
        except json.JSONDecodeError as e:
            # 줄 번호는 그 행이 시작한 줄이다(닫는 괄호가 빠지면 틀린 곳은 다음 행의 첫 글자로 잡힌다)
            raise 배치오류([_읽기오류(경로, 줄, "JSON 문법 오류: %s (틀린 곳은 %d째 줄 %d번째 글자 근처). 주석 줄(//)은 못 쓴다 — 풀이는 「메모」 열쇠에 적는다"
                                 % (e.msg, e.lineno, e.colno))])
        if not isinstance(객, dict):
            raise 배치오류([_읽기오류(경로, 줄, "행은 { } 로 적는다")])
        객.파일, 객.줄번호 = os.path.basename(경로), 줄
        낸.append(객)
        i = j
    return 낸


def 조각파일들(경로, sid=None):
    """시트 파일 곁의 책.json 이 그 시트를 조각 파일로 갈랐으면 조각 파일 이름 목록(이어 읽는 차례). 없으면 []."""
    책곳 = os.path.join(os.path.dirname(os.path.abspath(경로)), "책.json")
    sid = sid or os.path.splitext(os.path.basename(경로))[0]
    try:
        with open(책곳, encoding="utf-8") as f:
            표 = json.load(f).get("조각") or {}
    except (OSError, ValueError):
        return []
    목록 = 표.get(sid) if isinstance(표, dict) else None
    return [x for x in 목록 if isinstance(x, str)] if isinstance(목록, list) else []


def 시트읽기(경로, 오류=None, 조각=None):
    """줄 무늬 명세 파일 하나 → (머리, 행 줄 목록) — 아직 펴지 않은 날것(조각으로 적은 글은 이어 붙인다).

    열쇠와 값의 꼴을 등록부와 맞댄다: 모르는 열쇠 · 종류/서식/쓰임의 오타 · 시트 머리가 다른 행 ID.
    오류 : 목록을 주면 거기에 모으고, 안 주면 배치오류로 던진다. JSON 문법 오류·겹친 열쇠는 늘 던진다.
    조각 : 그 시트의 조각 파일 이름 목록(같은 폴더). 안 주면 곁의 책.json 의 「조각」에서 읽는다. 조각 파일은 첫 객체가
           {"조각": 시트 ID} 이고 둘째부터 행이다 — 시트 파일의 줄 뒤에 적힌 차례로 이어 붙는다. 줄마다 온 파일(날줄.파일)이 달린다.
    """
    모음 = [] if 오류 is None else 오류
    객 = _객체들(경로)

    def 틀림(줄, 설명, 자리=None):
        곳 = os.path.join(os.path.dirname(경로), 줄.파일) if 줄 is not None and getattr(줄, "파일", None) else 경로
        모음.append(_읽기오류(곳, 줄.줄번호 if 줄 is not None else None, 설명, 시트=sid, 자리=자리))

    sid = None
    if not 객 or "시트" not in 객[0]:
        raise 배치오류([_읽기오류(경로, 1, "첫 객체는 시트 머리여야 한다(「시트」 열쇠가 없다)")])
    머리, 줄들 = 객[0], 객[1:]
    sid = 머리["시트"]
    머리.조각머리 = OrderedDict()
    for 이름 in (조각파일들(경로, sid if isinstance(sid, str) else None) if 조각 is None else 조각):
        곳 = os.path.join(os.path.dirname(경로), 이름)
        덧객 = _객체들(곳)
        if not 덧객 or 덧객[0].get("조각") != sid or [k for k in 덧객[0] if k not in 조각열쇠]:
            raise 배치오류([_읽기오류(곳, 1, "조각 파일의 첫 객체는 {\"조각\": \"%s\"} 여야 한다(쓸 수 있는 열쇠: %s)" % (sid, " · ".join(조각열쇠)))])
        if 이름 in 머리.조각머리 or 이름 == os.path.basename(경로):
            raise 배치오류([_읽기오류(곳, 1, "같은 조각 파일이 두 번 적혔다: %s" % 이름)])
        머리.조각머리[이름] = 덧객[0]
        줄들 = 줄들 + 덧객[1:]
    for 키 in 머리:
        if 키 not in 머리열쇠:
            틀림(머리, "시트 머리의 모르는 열쇠: 「%s」" % 키)
    # 머리의 뼈대가 틀리면 더 읽을 수 없다 — 바로 던진다(트레이스백 대신 파일 이름과 줄 번호)
    뼈대 = []
    if not isinstance(sid, str) or not sid:
        뼈대.append("시트 머리의 「시트」 는 시트 ID 글이어야 한다: %r" % (sid,))
    if not isinstance(머리.get("열") or [], list):
        뼈대.append("시트 머리의 「열」 은 열 등록부의 목록이어야 한다")
    else:
        for i, c in enumerate(머리.get("열") or (), 1):
            if not isinstance(c, dict) or not isinstance(c.get("id"), str) or not c.get("id"):
                뼈대.append("열 등록부의 %d번째 열에 「id」 가 없다: %s" % (i, json.dumps(c, ensure_ascii=False)[:80]))
    for 키, 꼴 in (("축", list), ("묶음", dict), ("쓰임", dict), ("덧이름", dict), ("속성", dict)):
        if 머리.get(키) is not None and not isinstance(머리[키], 꼴):
            뼈대.append("시트 머리의 「%s」 꼴이 틀렸다" % 키)
    if isinstance(머리.get("묶음"), dict):
        for 이름, 종류들 in 머리["묶음"].items():
            if not (isinstance(종류들, list) and all(isinstance(x, str) for x in 종류들)):
                뼈대.append("시트 머리의 묶음 「%s」 는 열 종류의 목록으로 적는다" % 이름)
    if 뼈대:
        raise 배치오류([_읽기오류(경로, 머리.줄번호, x, 시트=sid if isinstance(sid, str) else None) for x in 뼈대])
    본열, 안종류, 쓴종류 = set(), 아는열종류(머리), set()
    for c in 머리.get("열") or ():
        for 키 in c:
            if 키 not in 열열쇠:
                틀림(머리, "열 등록부의 모르는 열쇠: %s 의 「%s」" % (c.get("id"), 키))
        if c.get("id") in 본열:
            틀림(머리, "열 ID 가 겹친다: %s" % c.get("id"))
        본열.add(c.get("id"))
        종류 = c.get("종류", "기타")
        쓴종류.add(종류)
        쓴종류 |= {x for x in (c.get("갈래"), c.get("구간")) if isinstance(x, str)}
        if c.get("갈래") is not None and (c["갈래"] not in 축갈래 or 종류 not in ("실적", "예측", "영구")):
            틀림(머리, "열 등록부의 %s — 갈래 「%s」 는 종류가 실적 · 예측 · 영구인 열에 FY실적 · 누계실적 · 잔여예측 · 연간예측 · 영구 로 적는다" % (
                c.get("id"), c["갈래"]))
        if c.get("구간") is not None and c["구간"] not in ("상세", "수렴"):
            틀림(머리, "열 등록부의 %s — 구간 「%s」 를 모른다 (상세 · 수렴)" % (c.get("id"), c["구간"]))
        if 종류 not in 안종류:      # 종류의 오타는 그 열을 묶음에서 말없이 뺀다(COUNTBLANK(근거) 가 한 칸 준다)
            틀림(머리, "열 등록부의 모르는 열 종류: %s 의 「%s」 (등록된 종류: %s · 이 시트의 묶음·축: %s)" % (
                c.get("id"), 종류, " · ".join(열종류들), " · ".join(sorted(안종류 - set(열종류들))) or "없음"))
    틀시트 = any(c.get("갈래") for c in 머리.get("열") or ())
    for 이름, 종류들 in (머리.get("묶음") or {}).items():
        for k in 종류들:
            if k not in 쓴종류 and not (틀시트 and k in 축갈래):      # 기간 축의 갈래는 회차에 따라 열이 없을 수 있다(달아님 · 수렴 …)
                틀림(머리, "묶음 「%s」 에 적힌 열 종류 「%s」 인 열이 열 등록부에 없다(종류 이름의 오타인지 본다)" % (이름, k))
    for k in 머리.get("축") or ():
        if k not in 쓴종류:
            틀림(머리, "축에 적힌 열 종류 「%s」 인 열이 열 등록부에 없다" % (k,))
    if 머리.get("가정묶음") is not None and not isinstance(머리["가정묶음"], bool):
        틀림(머리, "시트 머리의 「가정묶음」 은 true / false 로 적는다")
    for 키 in ("메모",):
        if 키 in 머리:
            머리[키] = _잇기(머리[키])
    for v in 머리.get("유효성") or ():
        for 키 in ("formula1", "formula2"):
            if 키 in v:
                v[키] = _잇기(v[키])
    for d in 머리.get("정의된이름") or ():
        if "수식" in d:
            d["수식"] = _잇기(d["수식"])
    쓰임표, 서식들 = 머리.get("쓰임") or {}, 서식이름들()
    for 줄 in 줄들:
        rid = 줄.get("id")
        if not isinstance(rid, str) or not rid:
            틀림(줄, "행에 「id」 가 없다")
            continue
        for 키 in 줄:
            if 키 not in 행열쇠:
                틀림(줄, "모르는 열쇠: %s 의 「%s」 (쓸 수 있는 열쇠: %s)" % (rid, 키, " · ".join(행열쇠)), [rid, None])
        if "대조" in 줄 and 줄["대조"] is not False:
            틀림(줄, "%s 의 「대조」 는 false 만 적는다(엔진 = 워크북 대조에서 뺀다 — 까닭은 「메모」에). 적지 않으면 계산 · 소계 · 합계 · 비율 줄은 전부 대조한다" % rid,
               [rid, None])
        m = re.fullmatch(r"([SX]\d+)R\d+", rid)
        if m and m.group(1) != sid:
            틀림(줄, "행 ID 의 시트 머리가 이 파일의 시트(%s)와 다르다: %s" % (sid, rid), [rid, None])
        for 키 in ("이름", "단위", "메모"):
            if 키 in 줄:
                줄[키] = _잇기(줄[키])
                if not isinstance(줄[키], str):
                    틀림(줄, "%s 의 「%s」 는 글(또는 글 조각의 목록)로 적는다: %s" % (rid, 키, json.dumps(줄[키], ensure_ascii=False)[:60]), [rid, None])
                    del 줄[키]
        for 키 in ("무늬", "글", "값"):
            if 키 in 줄:
                if not isinstance(줄[키], dict):
                    틀림(줄, "%s 의 「%s」 는 {열 구간: …} 로 적는다" % (rid, 키), [rid, None])
                    줄[키] = {}
                    continue
                for 구간 in list(줄[키]):
                    줄[키][구간] = _잇기(줄[키][구간])
                    v = 줄[키][구간]
                    if isinstance(v, dict):
                        for 속 in ("배열수식", "배열범위"):
                            if 속 in v:
                                v[속] = _잇기(v[속])
                    문제 = 칸값문제(키, v)
                    if 문제:
                        틀림(줄, "%s 의 %s 「%s」 — %s" % (rid, 키, 구간, 문제), [rid, None])
                        del 줄[키][구간]
        if "축값" in 줄:
            if not (isinstance(줄["축값"], dict) and all(isinstance(v, str) for v in 줄["축값"].values())):
                틀림(줄, "%s 의 「축값」 은 {열 구간: 기간 속성 이름} 으로 적는다" % rid, [rid, None])
                줄["축값"] = {}
            elif not 틀시트:
                틀림(줄, "%s 의 「축값」 — 시간축 열을 기간 축에서 받는 시트(열 등록부에 「갈래」가 있는 시트)에서만 쓴다" % rid, [rid, None])
                줄["축값"] = {}
            else:
                from 기간열 import 축값속성
                for 구간, 속 in list(줄["축값"].items()):
                    if 속 not in 축값속성:
                        틀림(줄, "%s 의 축값 「%s」 — 기간 속성 「%s」 를 모른다 (%s)" % (rid, 구간, 속, " · ".join(축값속성)), [rid, None])
                        del 줄["축값"][구간]
        if "덧" in 줄:
            if not isinstance(줄["덧"], dict):
                틀림(줄, "%s 의 「덧」 은 {열 ID: {메모 · 링크}} 로 적는다" % rid, [rid, None])
                줄["덧"] = {}
            for cid, 한 in list(줄["덧"].items()):
                문제 = 덧문제(한, 덧열쇠)
                if cid not in 본열:
                    문제 = "열 등록부에 없는 열 ID 다(「덧」은 별칭이 아니라 열 ID 로 적는다)"
                if 문제:
                    틀림(줄, "%s 의 덧 「%s」 — %s" % (rid, cid, 문제), [rid, None])
                    del 줄["덧"][cid]
        for 키 in ("입력", "병합"):
            if 키 in 줄 and not (isinstance(줄[키], list) and all(isinstance(x, str) for x in 줄[키])):
                틀림(줄, "%s 의 「%s」 는 열 구간의 목록으로 적는다" % (rid, 키), [rid, None])
                줄[키] = []
        if 줄.get("종류") is not None and 줄["종류"] not in 줄종류들:
            틀림(줄, "%s 의 종류 「%s」 를 모른다 (%s)" % (rid, 줄["종류"], " / ".join(줄종류들)), [rid, None])
        if 줄.get("서식") is not None and 줄["서식"] not in 서식들:
            틀림(줄, "%s 의 서식 「%s」 를 모른다 (%s)" % (rid, 줄["서식"], " · ".join(sorted(서식들))), [rid, None])
        if 줄.get("쓰임") is not None and 줄["쓰임"] not in 쓰임표:
            틀림(줄, "%s 의 쓰임 「%s」 가 이 시트의 쓰임 표에 없다 (%s)" % (
                rid, 줄["쓰임"], " · ".join(쓰임표) or "쓰임 표가 비었다"), [rid, None])
        if 줄.get("선") is not None and 줄["선"] not in ("소계", "합계"):
            틀림(줄, "%s 의 선 「%s」 를 모른다 (소계 / 합계)" % (rid, 줄["선"]), [rid, None])
        if 줄.get("들여") is not None and 줄["들여"] not in (0, 1, 2):
            틀림(줄, "%s 의 들여 「%s」 를 모른다 (0 · 1 · 2)" % (rid, 줄["들여"]), [rid, None])
        if 줄.get("높이") is not None and not (isinstance(줄["높이"], (int, float)) and not isinstance(줄["높이"], bool) and 줄["높이"] > 0):
            틀림(줄, "%s 의 높이는 0 보다 큰 숫자로 적는다: %r" % (rid, 줄["높이"]), [rid, None])
    if 오류 is None and 모음:
        raise 배치오류(모음)
    return 머리, [줄 for 줄 in 줄들 if isinstance(줄.get("id"), str) and 줄.get("id")]


def 칸값문제(키, v):
    """「무늬」·「글」·「값」에 적은 값의 꼴이 틀렸으면 까닭, 맞으면 None."""
    if 키 == "무늬":
        return None if isinstance(v, str) else "손 수식 글(또는 글 조각의 목록)로 적는다"
    if isinstance(v, dict):
        모름 = [k for k in v if k not in 값칸열쇠]
        if 모름:
            return "모르는 열쇠 「%s」 (쓸 수 있는 열쇠: %s)" % (모름[0], " · ".join(값칸열쇠))
        if "v" in v and not (v["v"] is None or isinstance(v["v"], (str, int, float, bool))):
            return "「v」 는 글 · 숫자 · 참거짓 하나로 적는다: %s" % json.dumps(v["v"], ensure_ascii=False)[:40]
        if v.get("t") is not None and v["t"] not in ("s", "e", "dt", "d", "tm", "?"):      # ? = 명세추출이 종류를 모르고 글로 옮긴 값
            return "「t」(값의 종류) 「%s」 를 모른다 (s 글 · e 오류값 · d 날짜 · dt 날짜와 시각 · tm 시각)" % (v["t"],)
        return None
    if 키 == "글" and not isinstance(v, str):
        return "글(또는 글 조각의 목록)로 적는다: %s — 숫자는 「값」에 적는다" % json.dumps(v, ensure_ascii=False)[:40]
    if 키 == "값" and isinstance(v, str):
        return '글이 적혔다: "%s" — 숫자는 따옴표 없이, 글은 「글」에, 날짜는 {"v": "2026-06-30", "t": "d"} 로 적는다' % v[:30]
    if 키 == "값" and not isinstance(v, (int, float, bool)):
        return "숫자 · 참거짓 · { } 로 적는다: %s" % json.dumps(v, ensure_ascii=False)[:40]
    return None


def 덧문제(한, 열쇠):
    """줄의 「덧」 · 배치의 「칸」·「덧칸」 한 칸의 꼴이 틀렸으면 까닭, 맞으면 None. 열쇠 = 쓸 수 있는 안쪽 열쇠."""
    if not isinstance(한, dict):
        return "{ } 로 적는다"
    for k in 한:
        if k in ("f", "배열"):
            return "수식의 틀(「%s」)은 받지 않는다 — 문법을 거치지 않은 수식이 된다. 수식은 손 수식으로 적는다(줄의 「무늬」 · 배치의 「손수식」)" % k
        if k not in 열쇠:
            return "모르는 열쇠 「%s」 (쓸 수 있는 열쇠: %s)" % (k, " · ".join(열쇠))
    return None


def _칸값(v, rid, cid):
    if isinstance(v, dict):
        return dict(v)
    if isinstance(v, str) and v.startswith("="):
        # 「=」로 시작하는 글을 그대로 칸에 넣으면 문법을 거치지 않은 수식이 된다
        raise 손오류('%s 의 열 %s — 「=」로 시작하는 글은 {"v": "…", "t": "s"} 로 적는다(수식이면 「무늬」에 손 수식으로)' % (rid, cid),
                   종류="「=」 글")
    return {"v": v}


def 줄펴기(sid, 낸, 문, 순서=None, 열만=None):
    """행 한 줄(날것) → 칸 dict {열 ID: 칸}. 순서·열만 은 짓기가 새 열을 채울 때 쓴다(그 열만 편다)."""
    rid = 낸["id"]
    종 = 문.열종류[sid]
    순 = 순서 if 순서 is not None else 문.열순서[sid]
    칸 = OrderedDict()

    def 놓기(cid, 한):
        if 열만 is not None and cid not in 열만:
            return
        if cid in 칸 and ("f" in 칸[cid] or "v" in 칸[cid]):
            raise 손오류("%s 의 열 %s 에 값이 두 번 적혔다" % (rid, cid))
        칸[cid] = 한

    for 키, 종류 in (("이름", "이름"), ("단위", "단위")):
        if 키 in 낸:
            cid = next((c for c in 순 if 종.get(c) == 종류), None)
            if cid is None:
                raise 손오류("%s 에 %s 열이 없는데 %s 가 적혔다" % (sid, 종류, rid))
            v = _잇기(낸[키])
            if 열만 is None or cid in 열만:
                놓기(cid, {"f": 손수식틀(v, cid, sid, 문)} if isinstance(v, str) and v.startswith("=") else {"v": v})

    def 구간(키):
        try:
            return 구간풀기(문, sid, rid, 키, 순서)
        except 배치오류:
            if 열만 is not None:      # 새 열만 채울 때는 못 푸는 구간(뺀 열을 가리키는 것 따위)을 건너뛴다
                return []
            raise

    틀시트 = sid in 문.기간틀

    def 적은(키, 한, 갈="무늬"):
        # 「예측.끝」처럼 묶음의 몇째 열로 적은 열쇠는 칸에 적어 둔다 — 다시 쓸 때 열 ID 로 되돌리지 않는다.
        # 시간축 열을 기간 축에서 받는 시트는 모든 열쇠를 적어 둔다(다시쓰기가 적은 열쇠를 그대로 낸다)
        if 틀시트:
            한["열쇠"], 한["갈"] = 키, 갈
        elif 자리풀기(키):
            한["열쇠"] = 키
        return 한

    for 키, 글 in (낸.get("무늬") or {}).items():
        글 = _잇기(글)
        if not isinstance(글, str):
            raise 손오류("%s 의 무늬 「%s」 는 손 수식 글로 적는다" % (rid, 키), 종류="수식 꼴")
        for cid in 구간(키):
            if 열만 is None or cid in 열만:
                놓기(cid, 적은(키, {"f": 손수식틀(글, cid, sid, 문)}))
    for 키, v in (낸.get("글") or {}).items():
        v = _잇기(v)
        문제 = 칸값문제("글", v)
        if 문제:
            raise 손오류("%s 의 글 「%s」 — %s" % (rid, 키, 문제), 종류="명세 읽기")
        for cid in 구간(키):
            놓기(cid, 적은(키, _칸값(v, rid, cid), "글"))
    for 키, v in (낸.get("값") or {}).items():
        문제 = 칸값문제("값", v)
        if 문제:
            raise 손오류("%s 의 값 「%s」 — %s" % (rid, 키, 문제), 종류="명세 읽기")
        for cid in 구간(키):
            if isinstance(v, dict) and "배열수식" in v:
                놓기(cid, 적은(키, {"f": 손수식틀(_잇기(v["배열수식"]), cid, sid, 문), "배열": 손수식틀(_잇기(v["배열범위"]), cid, sid, 문)}, "값")
                    if 틀시트 else {"f": 손수식틀(_잇기(v["배열수식"]), cid, sid, 문), "배열": 손수식틀(_잇기(v["배열범위"]), cid, sid, 문)})
            else:
                놓기(cid, 적은(키, _칸값(v, rid, cid), "값"))
    # 축값 — 생성기가 그 열의 기간 속성을 적는다. 같은 칸의 무늬 · 글 · 값을 덮는다(달 단위가 아닌 누계 · 잔여 열의 개월 수 따위)
    for 키, 속 in (낸.get("축값") or {}).items():
        from 기간열 import 날짜속성
        for cid in 구간(키):
            if 열만 is not None and cid not in 열만:
                continue
            v = ((문.열기간.get(sid) or {}).get(cid) or {}).get(속)
            if v is None:
                continue
            한 = {"v": v, "t": "d"} if 속 in 날짜속성 else {"v": v}
            한["열쇠"], 한["갈"] = 키, "축값"
            if cid in 칸:
                한.update({k: x for k, x in 칸[cid].items() if k in ("메모", "링크")})
            칸[cid] = 한
    for cid, 한 in (낸.get("덧") or {}).items():
        문제 = 덧문제(한, 덧열쇠)
        if cid not in 순 and 열만 is None:
            문제 = "이 시트에 없는 열 ID 다"
        if 문제:
            raise 손오류("%s 의 덧 「%s」 — %s" % (rid, cid, 문제), 종류="명세 읽기")
        if 열만 is None or cid in 열만:
            칸.setdefault(cid, {}).update(한)
    return 칸


def _책읽기(폴더, 옛꼴도=False):
    경로 = os.path.join(폴더, "책.json")
    try:
        with open(경로, encoding="utf-8") as f:
            책글 = json.load(f, object_pairs_hook=_짝훅)
    except _겹친열쇠 as e:
        raise 배치오류([_읽기오류(경로, None, "같은 열쇠가 두 번 적혔다: 「%s」" % e.args[0])])
    except json.JSONDecodeError as e:
        raise 배치오류([_읽기오류(경로, e.lineno, "JSON 문법 오류: %s" % e.msg)])
    except OSError as e:
        raise 배치오류([_읽기오류(경로, None, "파일을 읽을 수 없다: %s" % e)])
    오류 = [_읽기오류(경로, None, "책.json 의 모르는 열쇠: 「%s」" % 키) for 키 in 책글 if 키 not in 책열쇠]
    if not isinstance(책글.get("시트순서"), list):
        오류.append(_읽기오류(경로, None, "책.json 에 「시트순서」 가 없다"))
    if 책글.get("형식") in 옛형식 and not 옛꼴도:
        # 옛 형식은 이웃 열을 @-1 로 적는다 — 그대로 읽으면 수식마다 오류가 난다. 한 번에 옮기는 길을 알린다
        raise 배치오류([_읽기오류(경로, None, "옛 형식(%s)의 명세다 — 「python 줄무늬.py --옛꼴고치기 %s」 로 지금 형식(%s)으로 옮긴 뒤 "
                                 "「python 범위지문.py 승인 %s --위치범위」 로 범위 지문을 새로 적는다" % (책글.get("형식"), 폴더, 형식, 폴더))])
    if 책글.get("형식") != 형식 and not (옛꼴도 and 책글.get("형식") in 옛형식):
        오류.append(_읽기오류(경로, None, "책.json 의 「형식」 을 모른다: %r (지금 형식은 %s)" % (책글.get("형식"), 형식)))
    if 오류:
        raise 배치오류(오류)
    return 책글


def _머리자리풀기(머리):
    """시트 머리에 자리 이름으로 적은 열(쓰임의 별칭 · 덧이름 · 틀 고정의 「시간.1」 따위)을 지금 열 등록부의 열 ID 로 푼다."""
    열 = 머리.get("열") or []
    묶음표 = 머리.get("묶음") or {}

    def 묶음열(이름):
        종류들 = 묶음표.get(이름)
        if 종류들 is None:
            return None
        return [c["id"] for c in 열 if c.get("종류", "기타") in 종류들 or c.get("갈래") in 종류들 or c.get("구간") in 종류들
                or ("달아님" in 종류들 and c.get("달아님"))]

    def 풀기(낱):
        자 = 자리풀기(낱) if isinstance(낱, str) else None
        if not 자 or 묶음열(자[0]) is None:
            return 낱
        c = 자리열(묶음열(자[0]), 자[1])
        if c is None:
            raise 손오류("시트 머리의 자리 이름 「%s」 — 묶음 「%s」 에 그 자리가 없다(열 %d개. 값 칸이 놓일 시간축 열이 모자란다)" % (
                낱, 자[0], len(묶음열(자[0]))), 종류="자리 없음")
        return c

    if isinstance(머리.get("쓰임"), dict):
        머리["쓰임"] = OrderedDict((쓰, OrderedDict((별, 풀기(c)) for 별, c in 표.items()) if isinstance(표, dict) else 표)
                               for 쓰, 표 in 머리["쓰임"].items())
    if isinstance(머리.get("덧이름"), dict):
        머리["덧이름"] = OrderedDict((쓰, OrderedDict((풀기(a), 풀기(b)) for a, b in 표.items()) if isinstance(표, dict) else 표)
                                for 쓰, 표 in 머리["덧이름"].items())
    틀 = (머리.get("속성") or {}).get("틀고정")
    if isinstance(틀, dict) and 틀.get("열"):
        틀["열"] = 풀기(틀["열"])


def _명세지문(책글, 날것):
    """축 · 구조와 무관한 명세의 지문 — 책.json(원본 · 메모 빼고)과 시트 파일(조각 · 덧파일 포함)의 날것 내용을 열쇠 차례로 늘어놓은 글의 sha1 앞 16자.

    파일의 띄어쓰기 · 줄 나눔 · 「메모」 · 조각을 가른 자리는 지문을 바꾸지 않는다. 줄 · 열 · 수식 · 이름 · 서식 속성 가운데 하나라도 고치면 바뀐다.
    축이 다른 회차끼리도 같은 명세로 지었는지를 이 글자로 가린다(좌표 지도의 「명세지문」).
    """
    import hashlib

    def 다듬(v):
        if isinstance(v, dict):
            return {k: 다듬(x) for k, x in v.items() if k != "메모"}
        if isinstance(v, list):
            return [다듬(x) for x in v]
        return v

    몸 = {"책": 다듬({k: v for k, v in 책글.items() if k not in ("원본", "조각")}),
         "시트": {sid: [다듬(머리), [다듬(줄) for 줄 in 줄들]] for sid, (머리, 줄들) in 날것.items()}}
    글 = json.dumps(몸, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha1(글.encode("utf-8")).hexdigest()[:16]


def 읽기(폴더, 옛서식=True, 덧파일=(), 기간=None, 구조=None):
    """줄 무늬 명세 폴더 → 열 ID 명세(칸 단위로 편 것). 짓기가 이것을 받는다.

    옛서식 : 옛서식/ 의 칸별 서식 번호 · 행 높이를 입힌다(없으면 서식 없이 편다).
    덧파일 : 폴더 밖의 줄 무늬 명세 파일(새 시트 따위)을 더 읽는다.
    기간   : 가정 사전 · 가정 파일 경로 · {평가기준일, 결산월, 실적연도수, 상세추정연수, 수렴연수} · 기간축 객체(기간열.축사전 이 받는 것).
             주면 시간축 틀 열을 그 회차의 열(열 ID = 기간 ID)로 바꿔 편다 — 워크북은 이 꼴로 짓는다. 명세["기간"] 에 축이 실린다.
             안 주면 틀 그대로 편다(열의 기간 속성은 책.json 의 「기본기간」에서) — 명세를 고치는 도구가 읽는 꼴이다.
    구조   : 가정 사전 · 가정 파일 경로(그 「구조」를 쓴다) · 구조 사전. 안 주면 「기간」으로 준 가정의 「구조」, 그것도 없으면 책.json 의
             「기본구조」(없으면 빈 구조)로 줄을 편다 — 되풀이 줄 · 갈래 무늬 · 조건 · 시나리오 세 줄 · 표 구획(구조펴기.py). 명세["구조"] 에 실린다.
    읽다가 틀린 곳을 만나면 모아서 배치오류로 던진다(오류마다 파일 이름과 줄 번호가 붙는다).
    """
    책글 = _책읽기(폴더)
    오류 = []
    날것, 파일 = OrderedDict(), {}
    조각표 = 책글.get("조각") or {}
    if not (isinstance(조각표, dict) and all(isinstance(v, list) and all(isinstance(x, str) for x in v) for v in 조각표.values())):
        raise 배치오류([_읽기오류(os.path.join(폴더, "책.json"), None, "책.json 의 「조각」 은 {시트 ID: [조각 파일 이름 …]} 으로 적는다")])
    for sid in 조각표:
        if sid not in 책글["시트순서"]:
            오류.append(_읽기오류(os.path.join(폴더, "책.json"), None, "「조각」 에 적힌 시트 %s 가 「시트순서」 에 없다" % sid))
    for sid in 책글["시트순서"]:
        경로 = os.path.join(폴더, sid + ".jsonl")
        머리, 줄들 = 시트읽기(경로, 오류, 조각=조각표.get(sid) or [])
        if 머리["시트"] != sid:
            오류.append(_읽기오류(경로, 1, "시트 머리의 「시트」(%s)가 파일 이름(%s)과 다르다" % (머리["시트"], sid)))
        if sid in 날것:
            오류.append(_읽기오류(os.path.join(폴더, "책.json"), None, "「시트순서」에 같은 시트가 두 번 있다: %s" % sid))
        날것[sid], 파일[sid] = (머리, 줄들), 경로
    for 경로 in 덧파일:
        머리, 줄들 = 시트읽기(경로, 오류)
        if 머리["시트"] in 날것:
            오류.append(_읽기오류(경로, 1, "덧파일의 시트 ID 가 이미 있다: %s" % 머리["시트"]))
            continue
        날것[머리["시트"]], 파일[머리["시트"]] = (머리, 줄들), 경로
    덧시트 = {s for s, p in 파일.items() if os.path.abspath(os.path.dirname(p)) != os.path.abspath(폴더)}
    # 시간축 열을 기간 축에서 받는 시트 — 틀의 열을 축에 맞춘다(기간을 줬으면 그 회차의 열로, 안 줬으면 틀 그대로 + 기본기간의 속성)
    명세지문 = _명세지문(책글, 날것)      # 축 · 구조와 무관한 명세의 지문 — 읽은 파일의 내용(메모 빼고)에서 낸다
    머리원, 틀쓰임, 축, 기간적용 = {}, {}, None, False
    틀시트있나 = any(any(isinstance(c, dict) and c.get("갈래") for c in 머리.get("열") or ()) for 머리, _ in 날것.values())
    if 틀시트있나 and not 오류:
        import 기간열
        try:
            if 기간 is not None:
                축, 기간적용 = 기간열.축사전(기간), True
            elif 책글.get("기본기간"):
                축 = 기간열.축사전(책글["기본기간"])
        except 배치오류 as e:
            for o in e.오류목록:
                오류.append(dict(o, 파일="책.json" if o.get("종류") == "기간" else None))
    elif 기간 is not None and not 오류:
        오류.append(_읽기오류(os.path.join(폴더, "책.json"), None, "기간을 줬는데 이 명세에는 시간축 틀 열(열 등록부의 「갈래」)이 없다 — "
                                                              "옛 스캐폴드에서 뽑은 명세는 열이 못 박혀 있다", 종류="기간"))
    # 구조 — 가정 파일의 「구조」 선언대로 줄을 편다(되풀이 · 갈래 · 조건 · 시나리오 세 줄 · 표 구획). 안 줬으면 책의 「기본구조」(없으면 빈 구조)
    구조정보, 표원, 선 = OrderedDict(), {}, None
    원줄 = {sid: 줄들 for sid, (_, 줄들) in 날것.items()}      # 펴기 전의 줄(날것) — 다시 쓸 때 틀인 줄의 자리를 찾는다
    if not 오류:
        가정 = 구조펴기.가정읽기(구조 if 구조 is not None else 기간)
        if 가정 is None and isinstance(구조, dict):
            가정 = {"구조": 구조}
        try:
            선 = 구조펴기.선언(책글, 가정, 축)
        except 배치오류 as e:
            for o in e.오류목록:
                오류.append(dict(o, 파일="책.json", 설명="책.json — " + o["설명"]))
    if 선 is not None:
        for sid, (머리, 줄들) in list(날것.items()):
            def 한오류(낸, 설명, _경로=파일[sid], _sid=sid):
                곳 = os.path.join(os.path.dirname(_경로), 낸.파일) if getattr(낸, "파일", None) else _경로
                return _읽기오류(곳, getattr(낸, "줄번호", None), 설명, 종류="구조", 시트=_sid,
                              자리=[낸.get("id"), None] if 낸.get("id") else None)
            편줄, 정보 = 구조펴기.시트펴기(머리, 줄들, 선, 오류, 한오류)
            날것[sid] = (머리, 편줄)
            구조정보[sid] = 정보
    if 틀시트있나 and not 오류:
        import 기간열
    for sid, (머리, 줄들) in list(날것.items()) if not 오류 else ():
        표칸 = (구조정보.get(sid) or {}).get("표칸") or {}
        try:
            if 틀시트있나 and 기간열.틀인가(머리):
                머리원[sid] = 머리
                새 = 기간열.입히기(머리, 축, 기간적용)
                if 표칸:
                    표원[sid] = OrderedDict((키, 머리[키]) for 키 in ("묶음", "표") if 키 in 머리)
                    구조펴기.표입히기(새, 표칸)
                _머리자리풀기(새)
                날것[sid] = (새, 줄들)
                틀푼 = 기간열.입히기(머리, None, False)      # 틀의 별칭 표(별칭 → 틀의 열 ID) — 좌표 지도가 옛 열 글자를 별칭으로 풀 때 쓴다
                _머리자리풀기(틀푼)
                틀쓰임[sid] = 틀푼.get("쓰임") or {}
            elif 표칸:
                from copy import deepcopy
                표원[sid] = OrderedDict((키, 머리[키]) for 키 in ("열", "묶음", "쓰임", "표") if 키 in 머리)
                새 = 구조펴기.표입히기(deepcopy(머리), 표칸)
                _머리자리풀기(새)
                날것[sid] = (새, 줄들)
        except 배치오류 as e:
            for o in e.오류목록:
                오류.append(dict(o, 시트=sid, 파일="책.json" if o.get("종류") == "기간" else os.path.basename(파일[sid])))
    옛책 = None
    옛곳 = os.path.join(폴더, "옛서식")
    if 옛서식 and os.path.exists(os.path.join(옛곳, "책.json")):
        with open(os.path.join(옛곳, "책.json"), encoding="utf-8") as f:
            옛책 = json.load(f)

    # 1. 뼈대(열 · 행 ID · 이름 · 쓰임)부터 세워 문맥을 만든다
    명세 = {"책": OrderedDict(원본=책글.get("원본"), 시트순서=list(날것), 열ID=True, 줄무늬=True,
                           계산=책글.get("계산", {"fullCalcOnLoad": True}),
                           서식표=(옛책 or {}).get("서식표"), 서식조합=(옛책 or {}).get("서식조합"),
                           기본글꼴=(옛책 or {}).get("기본글꼴")),
          "시트": OrderedDict(), "테마": None, "폴더": os.path.abspath(폴더),
          "지문곳": {sid: os.path.join(os.path.dirname(os.path.abspath(p)), 지문파일) for sid, p in 파일.items()}}
    명세["명세지문"] = 명세지문
    if 기간적용:
        명세["기간"] = 축          # 이 회차의 축(기간축.사전()) — 짓기가 좌표 지도에 싣는다
        명세["덧파일"] = [os.path.abspath(p) for p in 덧파일]
    if 선 is not None:
        명세["구조"] = OrderedDict([
            ("선언", 선.구조), ("준것", 선.준구조), ("틀읽기", 선.틀읽기), ("가정", 선.가정 if not 선.틀읽기 else None), ("쓴경로", 선.쓴경로),
            ("안지은", OrderedDict((rid, 까닭) for 정보 in 구조정보.values() for rid, 까닭 in 정보["안지은"].items())),
            ("틀", [dict(한, 시트=sid) for sid, 정보 in 구조정보.items() for 한 in 정보["틀"]])])
    for 키 in ("등록부밖허용", "허용함수", "메모", "기본기간", "조각", "되풀이", "구조기본", "기본구조", "시나리오칸"):
        if 책글.get(키):
            명세["책"][키] = 책글[키]
    주인 = {}
    for sid, (머리, 줄들) in 날것.items():
        명 = OrderedDict(id=sid, 옛이름=머리.get("이름") if any(c.get("옛") for c in 머리.get("열") or ()) else None,
                        이름=머리.get("이름"))
        명["파일"] = os.path.basename(파일[sid])
        명["경로"] = os.path.abspath(파일[sid])
        if getattr(머리, "조각머리", None) or getattr(머리원.get(sid), "조각머리", None):      # 조각 파일로 가른 시트 — 다시 쓸 때 조각마다 되돌려 적는다
            명["조각머리"] = OrderedDict(getattr(머리원.get(sid), "조각머리", None) or getattr(머리, "조각머리", None))
        if sid in 덧시트:
            명["덧파일"] = True
        if 머리.get("가정묶음"):
            명["가정묶음"] = True
        if sid in 머리원:
            명["기간틀"] = True
            명["머리원"] = 머리원[sid]
            명["틀쓰임"] = 틀쓰임.get(sid) or {}
        if 머리.get("표"):      # 시트 머리의 표 정의(날것) — 다시 쓸 때 그대로 되돌린다
            명["표정의"] = 머리["표"]
        if sid in 표원:      # 표 구획이 선 시트 — 다시 쓸 때 머리의 묶음 · 쓰임 · 열은 적힌 그대로(표의 별칭 · 묶음 「표칸」 · 덧 열은 생성기가 더한 것이다)
            명["표원"] = 표원[sid]
        if (구조정보.get(sid) or {}).get("표칸"):
            명["표"] = OrderedDict((이름, {"칸": 칸, "줄": list(구조정보[sid]["표줄"].get(이름, ()))})
                                  for 이름, 칸 in 구조정보[sid]["표칸"].items())
        틀줄들, 앞줄 = [], None      # 다시 쓸 때 틀인 줄(구조펴기)을 적힌 그대로 되돌릴 자리 — (바로 앞의 보통 줄 ID, 틀의 날것)
        for 낸 in 원줄.get(sid) or ():
            if 선 is not None and 구조펴기.틀인가(낸, 선.괄호푼다):
                틀줄들.append((앞줄, 낸))
            else:
                앞줄 = 낸.get("id")
        if 틀줄들:
            명["틀줄들"] = 틀줄들
        명["속성"] = 머리.get("속성", {})
        명["열"] = []
        for c in 머리.get("열") or ():
            한 = {"id": c["id"], "옛": c.get("옛"), "종류": c.get("종류", "기타")}
            for 키 in ("갈래", "구간", "기간", "달아님", "틀열"):
                if c.get(키):
                    한[키] = c[키]
            for 영, 한글 in (("width", "폭"), ("hidden", "숨김"), ("outlineLevel", "수준"), ("collapsed", "접힘")):
                if c.get(한글):
                    한[영] = c[한글]
            if c.get("메모"):
                한["메모"] = c["메모"]
            명["열"].append(한)
        for 키, 기본 in (("축", []), ("묶음", OrderedDict()), ("쓰임", {}), ("덧이름", {})):
            명[키] = 머리.get(키, 기본)
        if 머리.get("메모"):
            명["메모"] = 머리["메모"]
        명["행"] = []
        for 낸 in 줄들:
            if 낸["id"] in 주인:
                오류.append(_읽기오류(getattr(낸, "파일", None) or 파일[sid], 낸.줄번호, "행 ID 가 겹친다: %s (%s 에도 있다)" % (낸["id"], 주인[낸["id"]]),
                                  시트=sid, 자리=[낸["id"], None]))
                continue
            주인[낸["id"]] = getattr(낸, "파일", None) or 명["파일"]
            줄 = OrderedDict(id=낸["id"])
            줄["조각"] = getattr(낸, "파일", None) or 명["파일"]      # 그 줄이 적힌 파일(시트 파일이나 조각 파일)
            m = re.fullmatch(r"[SX]\d+R(\d+)", 낸["id"])
            if m and 명["옛이름"]:
                줄["옛행"] = int(m.group(1))
            if isinstance(낸.get("이름"), str) and not 낸["이름"].startswith("="):
                줄["이름"] = 낸["이름"]
            for 키 in ("종류", "서식", "쓰임") + 줄덧속성 + ("높이", "메모", "시나리오", "빈칸허용", "표", "표머리", "칸서식"):
                if 낸.get(키):
                    줄[키] = 낸[키]
            if 낸.get("대조") is False:                    # 엔진 = 워크북 대조에서 빼는 줄(글 · 날짜를 내는 줄 · 도구 기입 칸) — 지도의 「견주지않는줄」
                줄["대조"] = False
            if 낸.get("대조열"):                           # 대조할 열의 묶음(「예측영구」 …) — 적지 않으면 수식이 선 시간축 열 전부
                줄["대조열"] = 낸["대조열"]
            if getattr(낸, "틀줄", None) is not None:      # 틀을 펴서 나온 줄 — 다시 쓸 때 이 줄은 건너뛰고 틀을 적힌 그대로 적는다
                줄["틀줄"] = True
            줄["무늬원"] = 낸
            줄["줄번호"] = 낸.줄번호
            if sid in 머리원:      # 다시 쓸 때 적은 열쇠를 그대로 내려고 적어 둔다
                줄["열쇠순"] = [(갈, 키) for 갈 in ("무늬", "글", "값", "축값") for 키 in (낸.get(갈) or {})]
                줄["열쇠원"] = {(갈, 키): _잇기(v) for 갈 in ("무늬", "글", "값") for 키, v in (낸.get(갈) or {}).items()}
                if 낸.get("축값"):
                    줄["축값"] = dict(낸["축값"])
                if 낸.get("입력"):
                    줄["입력원"] = list(낸["입력"])
            명["행"].append(줄)
        명세["시트"][sid] = 명
    명세["책"]["정의된이름"] = [{"이름": d["이름"]} for d in 책글.get("정의된이름", [])]
    for sid, (머리, _) in 날것.items():
        명세["시트"][sid]["정의된이름"] = [{"이름": d["이름"]} for d in 머리.get("정의된이름", [])]
    if 오류:              # 뼈대가 틀리면 수식을 펴 봐야 헛 오류만 는다
        raise 배치오류(오류)
    문 = 문맥만들기(명세)

    def 모으기(e, sid, rid, 줄번호, 파일이름=None):
        파일이름 = 파일이름 or 명세["시트"][sid]["파일"]
        for o in e.오류목록:
            오류.append(dict(o, 시트=sid, 자리=[rid, None], 파일=파일이름, 줄=줄번호,
                           설명="%s %s째 줄 — %s" % (파일이름, 줄번호, o["설명"])))

    # 2. 줄을 편다
    for sid, (머리, 줄들) in 날것.items():
        명 = 명세["시트"][sid]
        순 = 문.열순서[sid]
        옛 = {}
        if 옛책 and os.path.exists(os.path.join(옛곳, sid + ".json")):
            with open(os.path.join(옛곳, sid + ".json"), encoding="utf-8") as f:
                옛 = json.load(f)
        병합 = []
        # 축으로 읽은 시트 — 옛 서식은 틀의 열 ID 로 적혀 있다. 틀의 열 순서로 편 뒤, 새 열마다 폭을 받은 틀 열(「틀열」)의 서식을 입힌다
        틀순 = [c["id"] for c in 머리원[sid]["열"]] if 기간적용 and sid in 머리원 else None
        틀열 = {c["id"]: c.get("틀열") or c["id"] for c in 명["열"]} if 틀순 else None
        for 줄 in 명["행"]:
            낸, rid = 줄["무늬원"], 줄["id"]
            try:
                줄["칸"] = 줄펴기(sid, 낸, 문)
                if 낸.get("입력"):
                    줄["입력"] = [c for 키 in 낸["입력"] for c in 구간풀기(문, sid, rid, 키)]
                if 낸.get("칸서식"):      # 그 칸만 다른 숫자 서식(표 구획의 칸) — 열 구간을 열 ID 로 푼다
                    for 키, 이름 in 낸["칸서식"].items():
                        if 이름 not in 서식이름들():
                            raise 손오류("%s 의 칸서식 「%s」 — 서식 「%s」 를 모른다" % (rid, 키, 이름), 종류="명세 읽기")
                    줄["칸서식"] = OrderedDict((c, 이름) for 키, 이름 in 낸["칸서식"].items() for c in 구간풀기(문, sid, rid, 키))
                든 = set()
                for 키 in 낸.get("병합", []):
                    열들 = 구간풀기(문, sid, rid, 키)
                    if 든 & set(열들):      # 겹친 병합이 든 파일은 엑셀이 열지 못한다
                        raise 손오류("%s 의 병합 구간이 서로 겹친다: %s (겹친 열 %s)" % (
                            rid, " · ".join(낸["병합"]), ", ".join(c for c in 열들 if c in 든)), 종류="병합")
                    든 |= set(열들)
                    병합.append({"r": rid, "c": 열들[0], "r2": rid, "c2": 열들[-1], "키": 키})
            except 배치오류 as e:
                모으기(e, sid, rid, 줄["줄번호"], 줄.get("조각"))
                줄.setdefault("칸", OrderedDict())
                continue
            한옛 = 옛.get(rid, {})
            if 틀순:
                틀서식 = {}
                for 키, n in 한옛.get("s", {}).items():
                    a, _, b = 키.partition("~")
                    if a not in 틀순 or (b and b not in 틀순):
                        continue
                    for cid in 틀순[틀순.index(a):틀순.index(b or a) + 1]:
                        틀서식[cid] = n
                for cid in 순:
                    if 틀열[cid] in 틀서식:
                        줄["칸"].setdefault(cid, {})["s"] = 틀서식[틀열[cid]]
                속 = set(한옛.get("병합속", []))
                for cid in 순:
                    # 새 열이 받은 틀 열이 병합 안쪽이었어도, 그 칸에 내용이 있으면 안쪽으로 치지 않는다(병합 안쪽 칸은 쓰지 않는다)
                    if 틀열[cid] in 속 and (cid == 틀열[cid] or not ({"손수식", "f", "v"} & set(줄["칸"].get(cid, {})))):
                        줄["칸"].setdefault(cid, {})["병합속"] = 1
            else:
                for 키, n in 한옛.get("s", {}).items():
                    a, _, b = 키.partition("~")
                    if a not in 순 or (b and b not in 순):      # 줄 무늬 명세에서 열을 고친 뒤 남은 옛 서식 — 건너뛴다
                        continue
                    for cid in 순[순.index(a):순.index(b or a) + 1]:
                        줄["칸"].setdefault(cid, {})["s"] = n
                for cid in 한옛.get("병합속", []):
                    if cid in 순:
                        줄["칸"].setdefault(cid, {})["병합속"] = 1
            for 키 in ("height", "hidden", "outlineLevel", "collapsed"):
                if 키 in 한옛:
                    줄[키] = 한옛[키]
            # 명세의 열 순서대로 칸을 늘어놓는다
            줄["칸"] = OrderedDict(sorted(줄["칸"].items(), key=lambda kv: 순.index(kv[0])))
        첫열 = 순[0] if 순 else None
        명["병합"], 명["유효성"], 명["조건부서식"], 명["정의된이름"] = 병합, [], [], []
        try:
            명["병합"] = 병합 + [범위읽기(g, 문) for g in 머리.get("병합", [])]
            for v in 머리.get("유효성", []):
                한 = dict((k, x) for k, x in v.items() if k not in ("범위", "formula1", "formula2"))
                한["범위"] = [범위읽기(g, 문) for g in v["범위"]]
                for 키 in ("formula1", "formula2"):
                    if 키 in v:
                        한[키] = 손수식틀(v[키], 한["범위"][0]["c"], sid, 문)
                명["유효성"].append(한)
            for c in 머리.get("조건부서식", []):
                범위 = [범위읽기(g, 문) for g in c["범위"]]
                명["조건부서식"].append({"범위": 범위, "규칙": c["규칙"], "서식": c.get("서식"),
                                     "수식": [손수식틀(f, 범위[0]["c"], sid, 문) for f in c.get("수식", [])]})
            명["정의된이름"] = [{"이름": d["이름"], "틀": 손수식틀(d["수식"], 첫열, sid, 문)} for d in 머리.get("정의된이름", [])]
        except 배치오류 as e:
            모으기(e, sid, None, 머리.줄번호)
    try:
        명세["책"]["정의된이름"] = [{"이름": d["이름"], "틀": 손수식틀(d["수식"], None, None, 문)}
                             for d in 책글.get("정의된이름", [])]
    except 배치오류 as e:
        for o in e.오류목록:
            오류.append(dict(o, 파일="책.json", 설명="책.json — " + o["설명"]))
    if 오류:
        raise 배치오류(오류)
    if os.path.exists(os.path.join(폴더, "테마.xml")):
        with open(os.path.join(폴더, "테마.xml"), "rb") as f:
            명세["테마"] = f.read()
    명세["이름경고"] = [{"행": rid, "덧붙인 이름": 덧, "지금 이름": (문.행이름.get(rid) or [None])[0], "횟수": n}
                    for (rid, 덧), n in 문.이름경고.items()]
    # 덧붙인 이름이 다른 까닭을 가른다 — 적어 둔 옛 이름과 같으면 「줄 이름을 고친 것」, 옛 이름과도 다르면 「행 ID 를 틀리게 적었을 수 있다」
    if 명세["이름경고"]:
        옛이름, 없는 = 이름표읽기(명세)
        for 한 in 명세["이름경고"]:
            옛 = 옛이름.get(한["행"])
            한["옛 이름"] = 옛
            if 옛 is None and 문.행소속.get(한["행"]) in 없는:
                한["갈래"] = "이름표 없음"
            else:
                한["갈래"] = "이름고침" if 옛 and _이름맞나(한["덧붙인 이름"], 옛) else "모름"
    return 명세


def 이름알림글(한):
    """덧붙인 이름이 다른 곳 한 건 → 사람에게 보일 글(짓기 · 다시쓰기가 함께 쓴다)."""
    머리 = "%s 를 가리키는 수식에 덧붙인 이름 「%s」 이 지금 이름 「%s」 과 다르다(%d곳)" % (
        한["행"], 한["덧붙인 이름"], 한["지금 이름"], 한["횟수"])
    갈래 = 한.get("갈래")
    if 갈래 == "이름고침":
        return 머리 + " — 이 줄의 옛 이름과 같다: 줄 이름을 고친 것이다. 「python 줄무늬.py --다시쓰기 <명세 폴더>」 로 맞춘다"
    if 갈래 == "이름표 없음":
        return 머리 + (" — 줄 이름표(줄이름.json)가 없어 줄 이름을 고친 것인지 행 ID 를 틀리게 적은 것인지 가릴 수 없다. "
                     "행 ID 가 맞는지 본다(맞으면 덧붙인 이름을 손으로 고치거나 「다시쓰기 --이름덮기」)")
    return 머리 + (" — 이 줄의 옛 이름(%s)과도 다르다: **행 ID 를 틀리게 적었는지 본다.** 「다시쓰기」로는 고쳐지지 않는다"
                 "(행 ID 가 맞고 이름만 틀리게 적은 것이면 덧붙인 이름을 손으로 고친다)" % (
                     " / ".join("「%s」" % x for x in (한.get("옛 이름") or [])) or "적어 둔 것 없음"))


def 다시쓰기(폴더, 덧파일=(), 이름덮기=False):
    """줄 무늬 명세를 읽어 표준 꼴로 다시 쓴다 — 줄 이름을 고친 뒤 수식에 덧붙인 이름을 한 번에 맞춘다. → 요약(수 · 「고친 이름」 목록)

    덧붙인 이름은 **줄 이름을 고친 줄**에 한해 고친다: 덧붙인 이름이 적어 둔 옛 이름(줄이름.json)과 같을 때만 새 이름으로 바꾼다.
    옛 이름과도 지금 이름과도 다르면 행 ID 를 틀리게 적은 것일 수 있으므로 아무것도 쓰지 않고 배치오류로 멈춘다
    (이름덮기=True 면 그것까지 지금 이름으로 덮는다 — 행 ID 가 맞는 것을 확인한 뒤에만).
    덧파일 : 폴더 밖의 줄 무늬 명세 파일(새 시트)도 함께 읽어 제 파일에 다시 쓴다.
    「메모」· 「높이」· 열쇠의 차례를 지킨다. 범위 지문(범위지문.json)은 건드리지 않는다 — 승인 명령으로만 고친다.
    """
    명 = 읽기(폴더, 덧파일=덧파일)
    경고 = 명.get("이름경고") or []
    못 = [한 for 한 in 경고 if 한.get("갈래") != "이름고침"]
    if 못 and not 이름덮기:
        주인 = {줄["id"]: sid for sid, t in 명["시트"].items() for 줄 in t["행"]}
        raise 배치오류([{"종류": "덧붙인 이름", "시트": 주인.get(한["행"]), "자리": [한["행"], None], "설명": 이름알림글(한)} for 한 in 못])
    for t in 명["시트"].values():
        for 줄 in t["행"]:
            줄.pop("무늬원", None)
    수 = 쓰기(명, 폴더, 지문쓰기=False, 덧시트쓰기=bool(덧파일))
    수["고친 이름"] = [{"행": 한["행"], "옛 덧붙인 이름": 한["덧붙인 이름"], "새 이름": 한["지금 이름"], "곳": 한["횟수"],
                    "갈래": 한.get("갈래")} for 한 in 경고]
    return 수


_re함수 = re.compile(r'"(?:[^"]|"")*"|([A-Za-z_][A-Za-z0-9_.]*)\(')


def 옛꼴고치기(폴더, 덧파일=()):
    """옛 형식(줄무늬 1 · 2)의 명세를 지금 형식으로 옮긴다. → 요약

      · 이웃 열 표기 @-1 · @+1 → @<-1> · @<+1> (문자열 상수 안은 건드리지 않는다)
      · 세 시나리오 줄을 가진 가정 시트의 머리에 「가정묶음」 표시(적어 둔 범위 지문에 가정묶음이 있는 시트. 지문이 없으면 S12)
      · 책.json 의 「형식」 · 「원본」(파일 이름만) · 옛 수식에 있던 낯선 함수(「허용함수」 — 줄무늬 1 에만)
      · 줄 이름표(줄이름.json)를 지금 이름으로 적는다
    범위 지문은 건드리지 않는다 — 그 뒤 「python 범위지문.py 승인 <폴더> --위치범위」 로 새 형식의 지문을 적는다.
    """
    책경로 = os.path.join(폴더, "책.json")
    책글 = _책읽기(폴더, 옛꼴도=True)
    if 책글.get("형식") == 형식:
        raise 배치오류([_읽기오류(책경로, None, "이미 지금 형식(%s)이다 — 옮길 것이 없다" % 형식)])
    옛 = 책글.get("형식")
    try:
        with open(os.path.join(폴더, 지문파일), encoding="utf-8") as f:
            기준 = json.load(f).get("시트") or {}
    except (OSError, ValueError):
        기준 = None
    수 = OrderedDict([("옛 형식", 옛), ("새 형식", 형식), ("시트", 0), ("이웃 열 표기를 고친 곳", 0), ("가정묶음 표시를 단 시트", [])])
    낯선 = set()

    def 고침(v):
        v = _잇기(v)
        if isinstance(v, str) and v.startswith("="):
            v, n = 옛이웃열고치기(v)
            수["이웃 열 표기를 고친 곳"] += n
            if 옛 == "줄무늬 1":      # 함수 이름을 보기 전의 형식 — 옛 수식에 있던 낯선 함수를 모은다(참조의 대괄호 안은 빼고)
                for m in _re함수.finditer(re.sub(r"\[[^\]\[]*\]", "", v)):
                    if m.group(1) and 모르는함수(m.group(1)):
                        낯선.add(m.group(1))
        return v

    for sid, 경로 in [(x, os.path.join(폴더, x + ".jsonl")) for x in 책글["시트순서"]] + [(None, x) for x in 덧파일]:
        객 = _객체들(경로)
        if not 객 or "시트" not in 객[0]:
            raise 배치오류([_읽기오류(경로, 1, "첫 객체는 시트 머리여야 한다(「시트」 열쇠가 없다)")])
        머리, 줄들 = 객[0], 객[1:]
        for 줄 in 줄들:
            for 키 in ("이름", "단위", "메모"):
                if 키 in 줄:
                    줄[키] = 고침(줄[키])
            for 키 in ("무늬", "글", "값"):
                if isinstance(줄.get(키), dict):
                    for 구간, v in list(줄[키].items()):
                        if isinstance(v, dict):
                            for 속 in ("배열수식", "배열범위"):
                                if 속 in v:
                                    v[속] = 고침(v[속])
                        else:
                            줄[키][구간] = 고침(v) if 키 == "무늬" else _잇기(v)
        for v in 머리.get("유효성") or ():
            for 키 in ("formula1", "formula2"):
                if 키 in v:
                    v[키] = 고침(v[키])
        for c in 머리.get("조건부서식") or ():
            if isinstance(c.get("수식"), list):
                c["수식"] = [고침(x) for x in c["수식"]]
        for d in 머리.get("정의된이름") or ():
            if "수식" in d:
                d["수식"] = 고침(d["수식"])
        if "메모" in 머리:
            머리["메모"] = _잇기(머리["메모"])
        if sid is not None and "가정묶음" not in 머리 and (
                ((기준 or {}).get(sid) or {}).get("가정묶음") if 기준 is not None else sid == "S12"):
            머리["가정묶음"] = True
            수["가정묶음 표시를 단 시트"].append(sid)
        시트쓰기(경로, 머리, 줄들)
        수["시트"] += 1
    for d in 책글.get("정의된이름") or ():
        if "수식" in d:
            d["수식"] = 고침(d["수식"])
    책글["형식"] = 형식
    if 책글.get("원본"):
        책글["원본"] = os.path.basename(책글["원본"])
    if 낯선 and "허용함수" not in 책글:      # 옛 xlsx 에 있던 낯선 함수(스캐폴드의 _xlfn._LONGTEXT) — 받아 둔다
        책글["허용함수"] = sorted(낯선)
        수["허용함수에 적은 낯선 함수"] = sorted(낯선)
    with open(책경로, "w", encoding="utf-8", newline="\n") as f:
        json.dump(_차례(책글, 책열쇠), f, ensure_ascii=False, indent=1)
        f.write("\n")
    명 = 읽기(폴더, 덧파일=덧파일)       # 옮긴 것이 읽히는지 본다(틀린 곳이 있으면 배치오류)
    이름표쓰기(명, 폴더, 문맥만들기(명), 덧시트=bool(덧파일))
    수["덧붙인 이름이 지금 이름과 다른 곳"] = sum(한["횟수"] for 한 in 명.get("이름경고") or ())
    return 수


함수목록파일 = "목록_좌표의존함수.json"


def 함수목록(명세):
    """편 명세(틀 읽기)의 수식에서 좌표에 기대는 함수(공통.좌표의존함수)가 쓰인 곳을 센다 → 목록_좌표의존함수.json 의 내용.

    {"함수별": {이름: {수, 설명, 틀로못바꿈}}, "쓰인곳": [{"자리": [시트 ID, 행 ID, 열 ID], "함수": 이름} …], "낸곳": …}
    옛 목록은 옛 xlsx 에서 명세추출이 낸 것이라 명세에서 줄을 지운 뒤로 낡았다(W1 검증의 작은 결함 6) — 정본에서 다시 낸다.
    덧명세(폴더 밖의 시트 파일)의 수식은 세지 않는다. 짓기는 「틀로못바꿈」인 함수가 있으면 한 번 알린다.
    """
    from collections import Counter
    from openpyxl.formula import Tokenizer
    from 공통 import 좌표의존함수, 못바꾸는함수, _맨이름
    쓰임 = []
    for sid, t in 명세["시트"].items():
        if t.get("덧파일"):
            continue
        for 줄 in t["행"]:
            for cid, 한 in (줄.get("칸") or {}).items():
                for 키 in ("f", "배열"):
                    if 키 not in 한:
                        continue
                    글 = "".join(p if isinstance(p, str) else "A1" for p in 한[키])
                    try:
                        낱들 = Tokenizer(글).items
                    except Exception:      # noqa: BLE001
                        continue
                    for 낱 in 낱들:
                        if 낱.type == "FUNC" and 낱.subtype == "OPEN" and _맨이름(낱.value[:-1]) in 좌표의존함수:
                            쓰임.append(OrderedDict([("자리", [sid, 줄["id"], cid]), ("함수", _맨이름(낱.value[:-1]))]))
    수 = Counter(u["함수"] for u in 쓰임)
    return OrderedDict([
        ("함수별", OrderedDict((k, OrderedDict([("수", n), ("설명", 좌표의존함수[k]), ("틀로못바꿈", k in 못바꾸는함수)])) for k, n in 수.most_common())),
        ("쓰인곳", 쓰임),
        ("낸곳", "줄 무늬 명세(틀 읽기)에서 낸 것 — python 줄무늬.py --함수목록 <명세 폴더>. 자리 = [시트 ID, 행 ID, 열 ID]")])


def 함수목록쓰기(폴더):
    """명세 폴더의 목록_좌표의존함수.json 을 지금 명세에서 다시 낸다. → 함수별 수."""
    목록 = 함수목록(읽기(폴더, 옛서식=False))
    with open(os.path.join(폴더, 함수목록파일), "w", encoding="utf-8", newline="\n") as f:
        json.dump(목록, f, ensure_ascii=False, separators=(",", ":"))
        f.write("\n")
    return OrderedDict((k, v["수"]) for k, v in 목록["함수별"].items())


def _오류찍기(e, 머리="명세를 읽지 못했다"):
    print("%s — 오류 %d건" % (머리, len(e.오류목록)))
    for o in e.오류목록[:40]:
        print("  [%s] %s" % (o["종류"], o["설명"]))
    if len(e.오류목록) > 40:
        print("  … 그 밖 %d건" % (len(e.오류목록) - 40))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    인자 = list(sys.argv[1:])
    덧 = []
    if "--덧명세" in 인자:
        i = 인자.index("--덧명세")
        덧 = [a for a in 인자[i + 1:] if not a.startswith("--")]
        인자 = 인자[:i] + [a for a in 인자[i + 1:] if a.startswith("--")]
    덮기 = "--이름덮기" in 인자
    인자 = [a for a in 인자 if a != "--이름덮기"]
    try:
        if len(인자) == 2 and 인자[0] == "--다시쓰기":
            try:
                수 = 다시쓰기(인자[1], 덧파일=덧, 이름덮기=덮기)
            except 배치오류 as e:
                if e.오류목록 and all(o["종류"] == "덧붙인 이름" for o in e.오류목록):
                    _오류찍기(e, "다시 쓰지 않았다 — 줄 이름을 고친 것으로 볼 수 없는 덧붙인 이름이 있다")
                    sys.exit(1)
                raise
            고친 = 수.pop("고친 이름")
            print(json.dumps(수, ensure_ascii=False, indent=1))
            if 고친:
                print("덧붙인 이름을 고쳤다 — %d건 · %d곳 (행 ID · 옛 덧붙인 이름 → 새 이름 · 곳 수)" % (len(고친), sum(x["곳"] for x in 고친)))
                for x in 고친:
                    print("  %s  「%s」 → 「%s」  %d곳%s" % (x["행"], x["옛 덧붙인 이름"], x["새 이름"], x["곳"],
                                                   "" if x["갈래"] == "이름고침" else "  ※ 옛 이름과 다른 것을 덮었다(--이름덮기)"))
            else:
                print("덧붙인 이름을 고친 곳 없음")
        elif len(인자) == 2 and 인자[0] == "--함수목록":
            print("목록_좌표의존함수.json 을 다시 냈다 — %s" % json.dumps(함수목록쓰기(인자[1]), ensure_ascii=False))
        elif len(인자) == 2 and 인자[0] == "--옛꼴고치기":
            print(json.dumps(옛꼴고치기(인자[1], 덧파일=덧), ensure_ascii=False, indent=1))
            print("범위 지문을 새 형식으로 적는다: python 범위지문.py 승인 %s%s --위치범위" % (
                인자[1], (" --덧명세 " + " ".join(덧)) if 덧 else ""))
        elif len(인자) == 2 and not 인자[0].startswith("--") and not 덧:
            import 짓기
            import 열표
            if os.path.exists(os.path.join(인자[1], "책.json")):
                raise SystemExit("이미 줄 무늬 명세가 있는 폴더다: %s — 덮어쓰지 않는다. 정본(줄명세/)을 스캐폴드에서 새로 뽑으려면 "
                                 "「python 줄명세뽑기.py --덮어쓰기」 를 쓴다" % 인자[1])
            print(json.dumps(쓰기(열표.적용(짓기.칸명세읽기(인자[0])), 인자[1]), ensure_ascii=False, indent=1))
        else:
            raise SystemExit(__doc__)
    except 배치오류 as e:
        _오류찍기(e)
        sys.exit(1)

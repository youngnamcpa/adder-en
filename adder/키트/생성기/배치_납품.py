# -*- coding: utf-8 -*-
"""배치_납품 — 납품 워크북의 배치(시트 순서 · 탭 이름 · 줄의 자리 · 서식 속성)를 명세에서 낸다.

쓰기:  python 배치_납품.py <명세 폴더> <낼 배치.json>                          배치를 JSON 으로 낸다(사람이 읽고 짓기에 넘긴다)
       python 배치_납품.py <명세 폴더> --짓기 <낼 xlsx> [<낼 좌표지도.json>]    배치를 내어 바로 짓는다(표준 서식 길)
       [--기간 <가정.json>]  그 가정 파일의 기간(평가기준일 · 결산월 · 실적연도수 · 상세추정연수 · 수렴연수)으로 시간축 열을 짓는다 —
                            회차의 워크북은 이렇게 짓는다(열 ID = 기간 ID). 안 주면 명세의 틀(책.json 의 기본기간 — 15열)로 낸다
       python 배치_납품.py --새시트지문 [<명세 폴더>]                          납품시트/ 의 범위 지문 · 줄 이름표를 다시 적는다
                                                                              (14 · 15번 뼈대 파일을 고친 뒤에 한 번)
       [--경고허용] 위험한 경고가 있어도 종료 코드 0

납품 배치는 **규칙으로 낸다** — 줄 ID 를 하나하나 적어 두지 않는다. 줄 명세(줄명세/*.jsonl)의 줄을 더하거나 빼거나 이름을 고쳐도
이 파일은 안 고친다. 명세의 「종류」「서식」이 모자란 줄만 아래 표(선고침 · 종류고침)로 덮는다(명세는 건드리지 않는다).

배치가 정하는 것 (0_결정.md 3절 · 5절 · 「추가 결정 — 서식과 점검」 · 설계/2_배치_서식.md)
  1. 시트 15장의 순서와 탭 이름 — 1~13번은 원래 이름, 8번만 「8. CAPEX_working」 · 9번만 「9. NWC_working」.
     14. 민감도 · 15. 검증은 납품시트/ 의 뼈대(제목과 머리 줄)를 덧명세로 읽는다.
  2. 서식길 「표준」 — 이 배치로 지으면 명명 스타일과 시트 공통 서식이 선다(짓기 · 서식훅 · 서식표준).
  3. 번호 열 — 가정(A) · 과거 재무제표(H) · WACC(W) · 법인세(T) · 비영업자산(N) · 인건비(L) 시트의 여백 열(A)을 번호 열로 바꾸고
     입력 줄에 「A-030」 꼴의 번호를 싣는다(번호 = 행 ID 의 숫자 = 가정 번호). 계산 줄에는 싣지 않는다.
  4. 틀 고정 — 머리 구역(첫 구획머리 앞의 줄) 아래 · 첫 값 열 왼쪽. 요약 · 민감도는 행만.
  5. 머리 구역의 시점 머리 아랫줄(기간 종료일 · 구분 · 기간 길이 …)은 머리보조로 입힌다.
  6. 소계선 · 합계선 — 명세의 줄 종류를 따르되, 옛 서식에서 가늠한 「합계」가 맞지 않는 줄은 선고침 표로 고친다.
     「서식」이 빠진 줄은 줄 종류(점검 = 건수)와 단위 칸의 글(% · 배 · 일 · 명 …)로 숫자 서식을 가늠해 준다.
     「서식」이 단위 칸의 글과 어긋난 줄(단위 「일」에 금액 서식 따위)은 단위를 따른다. 시나리오 세 줄은 머리 줄을 따른다.
  7. 들여쓰기 — 시나리오 세 줄 2단, 계산 시트의 비율 줄 1단.
     머리 구역(첫 구획 앞)의 끝에 빈 줄이 겹친 시트(1번 — 안내 띠를 비운 3행 + 빈줄)는 빈줄 하나를 뺀다.
  8. 접기 — 12번의 시나리오 세 줄(가정마다 묶음. 펴 둔다 — 값을 부은 뒤 세 값이 같은 묶음을 접는다: 서식마감.py) ·
     보조 계산 구획(접음) · 점검 보조 열(접음) · 2번의 연도별 WACC 산정 줄(접음 — 연도별 WACC 를 쓰는 회차에는 서식마감이 편다) ·
     12번의 점검 보조 계산 줄(접음) · 보이는 열에 아무것도 없는 줄(점검 보조 열에만 값이 있는 줄 — 접음) ·
     확인상태 열(3 · 13번 — 접음. 머리 글이 빠진 열이다: 0_결정 「확인상태는 워크북에 싣지 않는다」. 열과 값은 옛 점검 수식이 읽어 남아 있다).
  9. 목록 유효성 — 명세의 유효성에 더해, **수식이 글 상수와 견주는 입력 칸**(="기중" · <>"미사용" …. 범위째 견주는 것도)을 찾아
     목록을 건다. 선택지는 수식에서 가늠한 것이라 목록 밖 값은 막지 않고 경고만 한다(「경고」).
     명세의 목록 유효성이 건너뛴 입력 칸(옛 파일의 범위 밀림)에는 같은 목록을 건다.
 10. 1번 시트 — 색 범례 구획과 약어 구획을 맨 아래로 보내고 인쇄 영역에서 뺀다. 도구가 적는 시나리오별 결과 줄은 산출 칸으로 입힌다.
 11. 인쇄 — 짓기의 표준 서식 길이 시트 사양으로 채운다(가로 · 폭 1쪽 · 제목 행/열 반복 · 인쇄 영역 · 바닥글). 여기서는 1번의 끝 줄과
     제목 행은 머리 구역 바로 아래의 빈 줄까지다(둘째 쪽부터 머리 줄 바로 아래에 표가 붙지 않게). 제목 열은 주지 않는다(짓기._표준인쇄).
     쪽 나눔은 못 박지 않는다 — 구획이 쪽 사이에서 갈리지 않게 하는 일은 값을 부은 뒤 엑셀로 재계산해 저장하는 단계가 한다(쪽나눔.py).
 12. 구획 머리의 번호 — 로마 숫자 한 체계로, 그 시트에 놓인 구획에 차례로 매긴다(「I. 평가 전제」). 줄 명세는 번호 없는 이름만 준다.
     이름이 이미 번호 머리(「I.」 「A.」 「1.」)로 시작하는 구획과 보조 계산 구획, 소구획(종류고침)에는 매기지 않는다.
 13. 구획 사이의 빈 줄 — 구획머리 앞에 빈 줄이 없으면 한 줄 넣는다(줄을 빼서 합계 줄 바로 아래에 다음 구획이 붙은 곳 · 옛 양식에서
     붙어 있던 곳). 그 틈을 범위 참조가 가로지르면 넣지 않는다(범위 안에 빈 줄이 생긴다). 구획머리 바로 아래의 소구획 앞에는 넣지 않는다.
 14. 번호 열의 머리 「No.」 — 번호를 실은 줄을 거느린 머리 줄마다 싣는다(점검 구획의 머리 줄에는 싣지 않는다).
 15. 붓기가 글을 적는 칸은 입력 칸으로 선다 — 명세의 「입력」에 빠진 칸을 덮는다.
     · 점검 줄의 사유 칸: 판정 수식이 제 줄의 빈 칸을 읽으면(사유가 적혔는지 본다) 그 칸은 사람이 적는 칸이다(사유칸찾기 — 규칙).
     · 근거 칸: 12번 한시적 현금흐름의 금액 · 잔여액 줄의 근거 네 칸, 3번의 비고 칸과 신용스프레드 줄의 근거 칸(칸꼴고침 — 표).
     키트의 가정 틀이 열쇠를 대는 자리가 전부 입력 칸으로 서는지는 L1/묶기/붓는자리.py 가 본다.
 16. 기간 축 (W2) — 시간축 열은 읽은 명세의 열 그대로다(기간을 줬으면 그 회차의 열). 이 표들의 열 구간은 열 ID 를 못 박지 않고
     묶음 · 자리 이름(시간.k) · 그 줄 쓰임의 별칭으로 적는다. 12번의 시점 머리 네 줄(기간 · 실적/예측 · 기간 종료일 · 기간 (개월))은
     명세에서 머리 구역(첫 구획 앞)에 있다 — 규칙 4 · 5 · 11 이 틀 고정 · 머리보조 · 인쇄 제목 행에 싣는다. 생성기가 적는 줄이라 입력 칸이 아니다.
 17. 예측 열이 많은 회차의 용지 (W2 통합 — 0_결정 「L1 뒤」 3) — 예측 열(잔여 기간 열 · 연간 예측 열 · 수렴 구간 열)이 여덟 개 이상이면
     계산 시트(2 · 4~10번 — 시트 사양의 뼈대가 「시간축」인 시트)도 A3 가로로 낸다. 폭 1쪽 맞춤이라 열이 늘면 배율이 떨어진다 —
     A4 로는 본문 10pt 가 6pt 아래로 찍힌다(L1 묶기에서 잰 것: 예측 11열에 57~58%). 12번은 사양이 이미 A3 다.
     이 회차의 축에 잔여 기간 열이 없으면 「잔여 기간 비율」 줄(4번)은 뺀다(놓일 칸이 없다).
"""
import os
import re
import sys
import json
from collections import OrderedDict

여기 = os.path.dirname(os.path.abspath(__file__))
새시트파일 = [os.path.join(여기, "납품시트", "S14.jsonl"), os.path.join(여기, "납품시트", "S15.jsonl"),
          os.path.join(여기, "납품시트", "S16.jsonl"),          # L2(M11) — 16. Narrative와 숫자
          os.path.join(여기, "납품시트", "S17.jsonl")]          # W4(2026-10-23) — 17. 동인 지도와 근거
기본낼곳 = os.path.join(여기, "배치_납품.json")
값열종류 = ("실적", "예측", "영구", "값")
보조열종류 = ("보조", "방향점검", "역산")      # 점검 보조 열 — 접어 두고 인쇄 영역에서 뺀다
큰용지예측열 = 8                               # 예측 열이 이만큼 이상이면 계산 시트(뼈대 「시간축」)도 큰 용지로 낸다(규칙 17)
큰용지 = 8                                     # 엑셀의 용지 번호 — 8 = A3 (9 = A4)
글열종류 = ("근거", "비고", "풀이", "방향", "소비처")
긴글열종류 = ("근거", "비고", "풀이")
비율들이는시트 = ("S02", "S04", "S05", "S06", "S07", "S08", "S09", "S10")

# 소계선 · 합계선을 고치는 표 — 행 ID → "소계" | "합계" | None(선 없음. 줄 종류가 합계여도 긋지 않는다).
# 명세의 「종류」는 옛 서식(굵은 글 · 바탕색)에서 가늠한 것이라 2번 시트처럼 굵게 칠해 둔 계산 줄이 모두 「합계」로 적혀 있다.
# 한 구획에 합계는 하나다(설계/2_배치_서식.md 1-3 · 5-2). 명세에 없는 행 ID 는 건너뛴다.
선고침 = {
    # 2. DCF — I. FCFF
    "S02R013": "소계", "S02R015": "소계", "S02R017": None, "S02R019": "소계", "S02R023": "합계",
    # II. 현재가치 — 연도별 WACC 구성 줄은 계산 줄이다
    "S02R026": None, "S02R027": None, "S02R028": None, "S02R029": None, "S02R030": None, "S02R031": None, "S02R032": None,
    "S02R033": None, "S02R034": None, "S02R035": None, "S02R036": "소계",
    # III. 영구가치
    "S02R040": None, "S02R050": None, "S02R051": "소계", "S02R054": "합계", "S02R055": None,
    # IV. 주주가치 산정
    "S02R058": "소계", "S02R066": "소계", "S02R068": "합계",
    # V. 최종 예측 연도 지표 — 표시 줄이다
    "S02R082": None, "S02R083": None, "S02R084": None, "S02R085": None, "S02R086": None, "S02R087": None, "S02R088": None,
    "S02R089": None,
    # 1. 주당가치
    "S01R018": "소계", "S01R026": "소계", "S01R028": "합계", "S01R029": None, "S01R041": None,
    # 그 밖
    "S04R055": None, "S06R022": "소계", "S07R022": None, "S08R036": None, "S08R041": None,
    "S10R034": None, "S10R035": None, "S10R036": None,
    "S13R016": "소계", "S13R032": "소계", "S13R044": "소계", "S13R054": "소계",
    # 13. 과거 재무제표 — 총계와 손익의 단계 이익(명세에는 계산 줄로 적혀 있다): 자산총계 · 부채와자본총계는 합계선, 나머지는 소계선
    "S13R033": "합계", "S13R055": "소계", "S13R058": "소계", "S13R059": "합계",
    "S13R064": "소계", "S13R066": "소계", "S13R073": "소계",
}
# 줄 종류를 고치는 표 — 행 ID → 종류(서식만의 종류 「산출」「머리보조」「부제」도 쓸 수 있다). 명세에 없는 행 ID 는 건너뛴다.
종류고침 = {
    "S01R061": "산출", "S01R062": "산출", "S01R063": "산출",      # 시나리오별 결과 — 도구가 값으로 적는다
    "S12R249": "입력", "S12R250": "입력",      # 12번 예측기간 연장의 기록 줄(연장 전 · 후 주당가치) — 같은 까닭(붓기가 「연장」 블록의 값을 적는다)
    # 12번 한시적 현금흐름 1 · 2 · 3 — 명세에는 구획머리지만 「한시적 현금흐름」 구획 안의 작은 머리 줄이다(번호를 매기지 않는다)
    "S12R394": "소구획", "S12R403": "소구획", "S12R412": "소구획",
}
# 칸 종류를 못 박는 표 — 행 ID → {열 구간: 칸 종류}. 붓기가 값을 적는데 명세의 「입력」에 없는 칸들이다(12번 기간 정의의 종료일 · 구분)
# 열쇠는 열 구간이다(열 ID · 묶음 · 그 줄의 쓰임이 준 별칭 · 「비관~낙관」 꼴)
칸꼴고침 = {
    # 12번 시나리오 정의의 주요 전제 · 설정 근거 — 값 열 세 칸에 긴 글을 받는다. 줄바꿈하는 긴 글 입력 칸으로 입힌다(잘리지 않게)
    "S12R018": {"비관~낙관": "입력긴글"}, "S12R019": {"비관~낙관": "입력긴글"},
    # 12번 「명시적 예측기간」의 값 칸 — 숫자 서식이 있는 줄(둘째 값이 환산계수)이지만 이 칸은 글을 내는 수식이다
    "S12R008": {"값": "글값"},
    # 1번 색 범례 — 뜻을 적은 칸이 곧 견본 칸이다(입력 = 파랑 글자 + 연노랑 바탕 · 다른 시트 참조 = 초록 · 계산 = 검정)
    "S01R116": {"값1": "입력글"}, "S01R118": {"값1": "연결글"}, "S01R119": {"값1": "글값"},
    # 12번 예측기간 연장의 기록 줄 — 값 칸 하나(붓기가 적는다)
    "S12R249": {"시간.1": "입력"}, "S12R250": {"시간.1": "입력"},
    # 12번 한시적 현금흐름의 머리 줄 — 붓기가 명칭 · 합산할 줄 · 세후 여부 · 구분을 적는 네 칸(명세의 「입력」에 없다)
    "S12R394": {"시간.1~시간.4": "입력글", "시간.3": "선택"}, "S12R403": {"시간.1~시간.4": "입력글", "시간.3": "선택"},
    "S12R412": {"시간.1~시간.4": "입력글", "시간.3": "선택"},
    # 15번의 부제(2행) — 제목과 같은 「구분」 열에 놓인다(이름 열이 셋째 열인 시트). 다른 시트를 읽는 수식이지만 부제로 입힌다
    "S15R002": {"구분": "부제"},
}
# W6a — 14. 민감도의 표 다섯(엔진 산출값 — 붓기가 적는다)과 1번 역산 DCF 분석의 시장 내재 가정 · 비고 칸. 축 이름 줄은 머리보조, 값 줄은 산출
종류고침.update((rid, "산출") for rid in ["S14R%03d" % n for n in ([3] + list(range(11, 17)) + list(range(21, 27)) + list(range(32, 41))
                                                               + list(range(47, 51)) + list(range(58, 63)))])
종류고침.update((rid, "머리보조") for rid in ("S14R031", "S14R046", "S14R056", "S14R057"))
# L2(M11) — 16. Narrative와 숫자: 붓기가 적는 글 · 값 칸은 산출, 칸 머리 줄은 머리보조
종류고침.update((rid, "산출") for rid in ["S16R%03d" % n for n in (list(range(11, 17)) + list(range(22, 28)) + [32, 33])])
종류고침.update((rid, "머리보조") for rid in ("S16R021", "S16R031"))
# W4(2026-10-23) — 14번 결합 민감도 구획 · 17. 동인 지도와 근거: 붓기가 적는 칸은 산출, 가정 이름 줄은 머리보조
종류고침.update((rid, "산출") for rid in ["S14R%03d" % n for n in (152, 153, 154, 155, 157, 158, 161, 162, 163)])
종류고침.update((rid, "머리보조") for rid in ("S14R151",))
종류고침.update((rid, "산출") for rid in ["S17R%03d" % n for n in [6] + list(range(101, 181)) + [191, 196]])
칸꼴고침.update((rid, {"값2~값3": "산출"}) for rid in ["S01R136", "S01R137", "S01R138"] + ["S01R23%d" % s for s in range(1, 6)])
# 붓기가 근거를 적는데 명세의 「입력」에 없는 칸 — 키트의 가정 틀(가정_템플릿.json)이 열쇠를 대는 자리다(L1/묶기/붓는자리.py 가 본다)
#   · 12번 한시적 현금흐름의 금액 · 잔여액 줄 — 근거 네 칸(다른 가정 머리 줄은 근거 네 칸이 입력 칸이다)
칸꼴고침.update((rid, {"근거1~근거4": "입력긴글"}) for rid in ("S12R395", "S12R399", "S12R404", "S12R408", "S12R413", "S12R417"))
#   · 3번의 비고 칸 — 넷째 근거 칸이다(0_결정: 출처 · 기준일 · 산정 근거 · 비고). 명세의 「입력」에는 출처 · 기준일 · 확인상태뿐이다.
#     14번 줄(목표 자본구조)의 비고에는 생성기가 적은 글이 있어 둔다
칸꼴고침.update((rid, {"비고": "입력긴글"}) for rid in ("S03R007", "S03R008", "S03R009", "S03R010", "S03R011", "S03R013"))
#   · 3번 신용스프레드(21번 줄) — 근거 칸이 입력으로 서 있지 않고 두 줄 위의 계산 줄 「세전 타인자본비용」(19번 줄)에 서 있다(목록 유효성도
#     19번 줄에 걸려 있다 — 옛 양식의 범위 밀림). 가정 틀(WACC근거 7 · 8 · 9 · 10 · 11 · 13 · 14 · 21)과 점검 수식(출처 · 기준일 미기재 수)이
#     세는 줄은 21번이다. 21번 줄에 세우고 19번 줄의 출처 · 기준일은 푼다(19번 줄의 확인상태 칸은 목록이 걸린 채 둔다 — 접어 둔 열이다)
칸꼴고침["S03R021"] = {"출처": "입력긴글", "기준일": "입력긴글", "확인상태": "선택", "비고": "입력긴글"}
칸꼴고침["S03R019"] = {"출처": "근거", "기준일": "근거"}
# 목록을 거는 칸 — 명세의 「입력」에 없어 선택칸찾기가 못 찾는 선택 칸(붓기가 값을 적는다). 시트 ID → [(행 ID 들, 열 ID, 목록)]
# 12번 한시적 현금흐름의 세후 여부 칸: 2번의 FCFF 수식이 「아니오」와 견준다(붓기는 「예」「아니오」를 적는다)
# 3번 신용스프레드의 확인상태 칸: 같은 열의 다른 근거 줄과 같은 목록(명세의 목록 유효성은 19번 줄에 걸려 있다)
선택고침 = {"S12": [(("S12R394", "S12R403", "S12R412"), "시간.3", ["예", "아니오"])],
        "S03": [(("S03R021",), "확인상태", ["확인완료", "검토중", "미확인"])]}
# 1번 「모델 점검 총괄」 표의 시트 줄 — 표시 칸은 다른 시트의 판정을 읽는 수식이지만 판정 칸으로 입힌다(조건부 서식이 걸린다)
칸꼴고침.update(("S01R%03d" % n, {"값1": "판정"}) for n in range(75, 87))
# 숫자 서식을 못 박는 표 — 행 ID → 서식 이름. 「서식」이 빠졌는데 단위 칸이 비어 가늠할 수 없는 줄, 옛 서식에서 잘못 가늠된 줄.
# 명세에 「서식」이 있어도 이 표가 앞선다. 명세에 없는 행 ID 는 건너뛴다
서식고침 = {
    # 한시적 현금흐름 — 금액 줄인데 옛 서식에서 비율로 가늠됐다(시나리오 세 줄은 머리 줄을 따른다)
    "S12R395": "금액", "S12R399": "금액", "S12R404": "금액", "S12R408": "금액", "S12R413": "금액", "S12R417": "금액",
    "S12R421": "금액",
    # 예측기간 연장의 기록 줄 — 주당 금액인데 옛 서식에서 연수(0.00)로 가늠됐다
    "S12R249": "주당", "S12R250": "주당",
}
# 단위 칸의 글 → 서식 이름(「서식」이 빠진 줄에만 쓴다). 단위 칸이 금액 단위를 읽는 수식이면 「금액」
단위서식 = {"%": "비율", "%p": "포인트", "배": "배수", "일": "일수", "명": "인원", "주": "주식수", "원": "주당", "년": "연수",
        "개월": "개월", "건": "건수", "개": "건수"}
# 단위 칸의 글과 어울리는 서식들 — 명세의 「서식」이 여기에 없으면 단위를 따른다(한 줄은 한 서식 · 단위와 서식이 어긋나지 않게:
# 설계/2_배치_서식.md 3-3). 옛 서식에서 가늠한 「금액」이 일수 · 인원 · 주식수 줄에 남아 있다
단위가족 = {"%": ("비율", "비율2"), "%p": ("포인트",), "배": ("배수", "연수", "베타", "계수"), "일": ("일수",), "명": ("인원",),
        "주": ("주식수",), "원": ("주당", "금액", "금액1"), "년": ("연수", "개월"), "개월": ("개월",), "건": ("건수",), "개": ("건수",)}
# 맨 아래로 보내는 1번 시트의 구획(인쇄 영역 밖) — 구획머리의 행 ID 또는 이름의 낱말로 찾는다. 적은 순서대로 놓는다
아래로 = (("S01R115", ("범례", "색상")), ("S01R088", ("약어", "쉬운 뜻")))
_re보조구획 = re.compile(r"^\s*(\((계산|보조)\)|보조 계산)")
보조구획줄 = ("S10R033",)      # 이름이 바뀌어도 보조 계산 구획으로 보는 구획머리(10번의 예측기간 발생 이월결손금 계산)
# 묶어 접어 두는 줄 — 시트 ID → (첫 줄 · 끝 줄의 행 ID) 들. 명세에 없는 행 ID 는 건너뛴다.
# 2번의 연도별 WACC 산정 줄(수렴 진행률 ~ 세후 타인자본비용): 0_결정 「추가 결정 — 서식과 점검」 「연도별 WACC 산정 줄은 2번 시트에
# 그룹으로 접어 둔다」. WACC 줄은 묶음 밖에 남는다. 연도별 WACC 를 쓰는 회차에는 값을 부은 뒤 서식마감.py 가 편다
# 12번의 가정 미입력 수 줄(S12R266): 15번 C-02 가 읽는 기간별 보조 계산이다 — 「예측기간 연장」 구획 아래에 이름만 보이는 줄로 남아 있었다
# (W6b: 265 는 15번이 읽지 않아 걷었다)
접는줄 = {"S02": (("S02R026", "S02R032"),), "S12": (("S12R266", "S12R266"),)}
# 묶어 접어 두는 열 — 시트 ID → 열 ID 들. 확인상태 열: 0_결정 「확인상태는 가정 파일에는 남기고 워크북에는 싣지 않는다」. 이름표가 머리 글을
# 뺐지만 열과 값은 옛 점검 수식(확인 여부 미기재 수 …)이 읽어 남아 있다 — 머리 없는 열이 보이지 않게 접어 둔다(W6b 가 점검과 함께 뺀다)
접는열 = {"S03": ("확인상태",), "S13": ("확인상태",)}
# 열 폭을 못 박는 표 — 시트 ID → {열 ID: 폭}. 머리 글이 빠져 표준 폭을 가릴 수 없는 열 ·
# 1번 값3 — 역산 DCF 분석 표의 「비고」 칸(W6c 결정 8 의 글 「무위험이자율 3.68%보다 낮음」 — 환산폭 27~28. 값 칸은 오른쪽 맞춤이라 옆으로
# 흐르지 못한다 — W6e: 글은 두고 칸을 맞춘다)
열폭고침 = {"S01": {"값3": 30}, "S03": {"확인상태": 11}, "S13": {"확인상태": 11}}
# 이 회차의 축에 그 묶음의 열이 없으면 빼는 줄 — 시트 ID → [(묶음 이름, 행 ID)]. 그 묶음의 열에만 놓이는 줄이다(이름만 남는다)
없으면빼는줄 = {"S04": [("잔여", "S04R195")]}
# 쪽 나눔을 못 박는 구획머리 — 그 줄 앞에서 쪽을 나눈다(설계/2_배치_서식.md 4-6). 명세에 없는 행 ID 는 건너뛴다.
# 비워 둔다: 한 쪽에 드는 줄 수는 값을 부은 뒤에야 정해진다(접은 예측 열에 따라 폭 1쪽 맞춤의 배율이 달라진다). 못 박아 두면
# 한 쪽에 들 구획을 억지로 넘기거나(1번 「모델 점검 총괄」 앞 — 시장가격 대비 다섯 줄만 둘째 쪽에 남았다) 쪽이 덜 찬다.
# 구획이 쪽 사이에서 갈리지 않게 하는 일은 엑셀로 재계산해 저장하는 단계가 한다(쪽나눔.py)
쪽나눔줄 = {}
# 18. 배치가 끼우는 새 줄 — 정본의 줄은 새 시트(14 · 15번 — 납품시트/ 의 덧명세)를 읽지 못한다(정본만 읽는 도구가 그 행 ID 를 모른다).
#     새 시트를 읽는 요약 줄은 배치의 새 줄로 끼운다. 시트 ID → [(이 줄 바로 뒤, 새줄 항목)]. 그 새 시트가 명세에 없으면 끼우지 않는다.
#     1번의 「모델 점검 총괄」(W6b): 15번 검증 시트의 총괄 표시(미결 0 이면 OK)를 읽는 한 줄 — 옛 「모델 점검 총괄」 · 「모델 점검」 두 구획 자리다
끼울새줄 = {"S01": [("S01R013", "S15", OrderedDict([("새줄", "S01R140"), ("이름", "모델 점검 총괄"), ("종류", "점검"), ("쓰임", "점검"),
                                                ("무늬", OrderedDict([("판정", "=[$S15R008 모델 점검 총괄]@$판정")]))]))]}
_re번호머리 = re.compile(r"^\s*([IVXLC]+|[A-Z](-\d+)?|\d+)\.\s")
_로마표 = ((100, "C"), (90, "XC"), (50, "L"), (40, "XL"), (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I"))


def 로마(n):
    글 = ""
    for 값, 자 in _로마표:
        while n >= 값:
            글, n = 글 + 자, n - 값
    return 글
_re앞 = re.compile(r'^(=|<>)"((?:[^"]|"")*)"')
_re뒤 = re.compile(r'"((?:[^"]|"")*)"(=|<>)$')
선택아닌글 = {"", "n/a", "-"}
표지글 = {"미사용"}          # W6b: 출처 · 근거 칸의 「미사용」 표지와 견주는 식(15번 완결성 점검)은 그 칸을 선택 칸으로 만들지 않는다 — 출처는 글 칸이다


def _번호(rid):
    m = re.fullmatch(r"[SX]\d+R(\d+)", rid)
    return int(m.group(1)) if m else None


def 이름열of(명):
    """그 시트의 이름 열 ID(종류가 「이름」인 첫 열)."""
    return next((c["id"] for c in 명["열"] if c.get("종류") == "이름"), "이름")


def 구획들(줄들):
    """줄 목록 → [(구획머리 줄 | None, [그 구획의 줄 …])]. 첫 구획머리 앞의 줄은 머리 구역(구획머리 None)이다."""
    묶, 지금 = [], (None, [])
    for r in 줄들:
        if r.get("종류") == "구획머리":
            묶.append(지금)
            지금 = (r, [r])
        else:
            지금[1].append(r)
    묶.append(지금)
    return 묶


def 가로지르는범위(명세):
    """명세의 범위 참조(수식 · 유효성 · 조건부서식 · 병합) — [(첫 줄 ID, 끝 줄 ID)]. 그 사이에 빈 줄을 넣으면 범위 안에 빈 줄이 생긴다."""
    import 범위지문
    낸 = []
    for _sid, _rid, _cid, 틀 in 범위지문.수식들(명세):
        for p in 틀:
            if isinstance(p, dict) and p.get("k") in ("r", "R") and p.get("r") and p.get("r2") and p["r"] != p["r2"]:
                낸.append((p["r"], p["r2"]))
    for s in 명세["시트"].values():
        for 묶 in ("유효성", "조건부서식"):
            for v in s.get(묶) or ():
                낸 += [(g["r"], g["r2"]) for g in v.get("범위") or () if g.get("r") != g.get("r2")]
        낸 += [(g["r"], g["r2"]) for g in s.get("병합") or () if g.get("r") != g.get("r2")]
    return 낸


def 사유칸찾기(명세):
    """점검 줄의 판정 수식이 읽는 제 줄의 빈 칸 — {행 ID: [열 ID …]}. 사람이 사유를 적는 칸이다(수식이 그 칸이 찼는지 본다).

    명세의 「입력」에 적힌 칸은 뺀다(이미 입력 칸으로 선다). 붓기는 가정 파일의 `사유` 를 이 칸들에 적는다."""
    import 범위지문
    줄 = {r["id"]: r for s in 명세["시트"].values() for r in s["행"]}
    결 = OrderedDict()
    for _sid, rid, _cid, 틀 in 범위지문.수식들(명세):
        r = 줄.get(rid)
        if r is None or r.get("종류") != "점검":
            continue
        for p in 틀:
            if isinstance(p, dict) and p.get("k") == "c" and p.get("r") == rid:
                cid = p.get("c")
                한 = (r.get("칸") or {}).get(cid)
                찬 = 한 is not None and ("f" in 한 or 한.get("v") not in (None, ""))
                if not 찬 and cid not in (r.get("입력") or ()) and cid not in 결.setdefault(rid, []):
                    결[rid].append(cid)
    return OrderedDict((k, v) for k, v in 결.items() if v)


def 선택칸찾기(명세):
    """수식이 글 상수와 견주는 입력 칸 — {(행 ID, 열 ID): [선택지 …]}. 명세의 목록 유효성이 이미 걸린 칸은 뺀다.

    =IF([S12R010]@E1="미사용", …) 같은 수식의 참조와 글 상수를 모은다. 선택지 = 견준 글들 + 그 칸의 지금 값.
    범위째 견주는 수식(SUMPRODUCT(([S13R007]@소비처:[S13R015]@소비처="명시적 제외")*…))은 그 범위의 입력 칸 전부가 선택 칸이다.
    같은 열에서 선택지가 겹치는 칸들은 선택지를 합쳐 같게 한다(방향 선언처럼 줄마다 견주는 글이 조금씩 다른 열)."""
    import 범위지문
    줄순 = {sid: [r["id"] for r in s["행"]] for sid, s in 명세["시트"].items()}
    열순 = {sid: [c["id"] for c in s["열"]] for sid, s in 명세["시트"].items()}
    본 = {rid: sid for sid, 줄 in 줄순.items() for rid in 줄}

    def 가리키는칸(p):
        """참조 하나가 가리키는 칸들 — 칸 하나(c) 또는 범위(r)."""
        if p.get("k") == "c":
            return [(p["r"], p["c"])]
        if p.get("k") != "r" or p.get("r") not in 본 or 본.get(p.get("r2")) != 본[p["r"]]:
            return []
        줄, 열 = 줄순[본[p["r"]]], 열순[본[p["r"]]]
        c1, c2 = p.get("c"), p.get("c2") or p.get("c")
        if c1 not in 열 or c2 not in 열:
            return []
        i, j = sorted((줄.index(p["r"]), 줄.index(p["r2"])))
        k, l = sorted((열.index(c1), 열.index(c2)))
        return [(rid, cid) for rid in 줄[i:j + 1] for cid in 열[k:l + 1]]

    칸, 입력 = {}, set()
    for s in 명세["시트"].values():
        for r in s["행"]:
            for cid, 한 in r["칸"].items():
                칸[(r["id"], cid)] = 한
            for cid in r.get("입력") or ():
                입력.add((r["id"], cid))
    걸린 = set()
    for s in 명세["시트"].values():
        for v in s.get("유효성") or ():
            if v.get("type") != "list":
                continue
            for g in v["범위"]:
                줄 = [r["id"] for r in 명세["시트"][s["id"]]["행"]]
                열 = [c["id"] for c in 명세["시트"][s["id"]]["열"]]
                if g["r"] in 줄 and g["r2"] in 줄 and g["c"] in 열 and g["c2"] in 열:
                    for rid in 줄[줄.index(g["r"]):줄.index(g["r2"]) + 1]:
                        for cid in 열[열.index(g["c"]):열.index(g["c2"]) + 1]:
                            걸린.add((rid, cid))
    찾 = OrderedDict()
    for _sid, _rid, _cid, 틀 in 범위지문.수식들(명세):
        for i, p in enumerate(틀):
            if not isinstance(p, dict) or p.get("k") not in ("c", "r"):
                continue
            뒤 = 틀[i + 1] if i + 1 < len(틀) and isinstance(틀[i + 1], str) else ""
            앞 = 틀[i - 1] if i > 0 and isinstance(틀[i - 1], str) else ""
            글들 = [m.group(k) for m, k in ((_re앞.match(뒤), 2), (_re뒤.search(앞), 1)) if m and m.group(k) not in 선택아닌글
                  and m.group(k) not in 표지글]
            if not 글들:
                continue
            for 자리 in 가리키는칸(p):
                if 자리 not in 입력 or 자리 in 걸린 or "f" in 칸.get(자리, {}):
                    continue
                낱 = 찾.setdefault(자리, [])
                for 글 in 글들:
                    if 글 not in 낱:
                        낱.append(글)
    for 자리, 낱 in 찾.items():      # 지금 값도 선택지다
        v = 칸.get(자리, {}).get("v")
        if isinstance(v, str) and v not in 선택아닌글 and v not in 낱:
            낱.insert(0, v)
    # 같은 열에서 선택지가 겹치는 칸들은 합친다
    열별 = OrderedDict()
    for (rid, cid), 낱 in 찾.items():
        열별.setdefault((rid.split("R")[0], cid), []).append((rid, 낱))
    for (_s, cid), 줄들 in 열별.items():
        바뀜 = True
        while 바뀜:
            바뀜 = False
            for i, (_, 가) in enumerate(줄들):
                for _, 나 in 줄들[i + 1:]:
                    if 가 is not 나 and set(가) & set(나) and set(가) != set(나):
                        합 = 가 + [x for x in 나 if x not in 가]
                        가[:], 나[:] = 합, 합
                        바뀜 = True
    return 찾


def 건너뛴칸찾기(명세):
    """명세의 목록 유효성이 건너뛴 입력 칸 — {시트 ID: [(목록, [(행 ID, 열 ID) …]) …]}.

    옛 파일의 유효성 범위는 줄이 끼고 빠지면서 밀려 있다(13번 확인상태 열 — 0_결정 9절). 같은 열에서 그 유효성이 걸린 첫 줄과 끝 줄 사이에 있는
    입력 칸인데 어느 목록 유효성에도 안 든 칸을 찾아 같은 목록을 건다. 목록이 글 상수("가,나,다")로 적힌 유효성만 본다."""
    결 = OrderedDict()
    for sid, s in 명세["시트"].items():
        줄 = [r["id"] for r in s["행"]]
        열 = [c["id"] for c in s["열"]]
        입력 = {(r["id"], cid) for r in s["행"] for cid in (r.get("입력") or ())}
        덮인, 후보 = set(), []
        for v in s.get("유효성") or ():
            if v.get("type") != "list":
                continue
            열별 = OrderedDict()
            for g in v["범위"]:
                if not (g["r"] in 줄 and g["r2"] in 줄 and g["c"] in 열 and g["c2"] in 열):
                    continue
                i, j = sorted((줄.index(g["r"]), 줄.index(g["r2"])))
                k, l = sorted((열.index(g["c"]), 열.index(g["c2"])))
                for cid in 열[k:l + 1]:
                    열별.setdefault(cid, []).extend(range(i, j + 1))
                    덮인.update((줄[n], cid) for n in range(i, j + 1))
            틀 = v.get("formula1")
            글 = 틀[0] if isinstance(틀, list) and len(틀) == 1 and isinstance(틀[0], str) else (틀 if isinstance(틀, str) else None)
            if 글 and 글.startswith("=") :
                글 = 글[1:]
            if not (글 and len(글) > 2 and 글[0] == '"' and 글[-1] == '"'):
                continue
            후보.append(([x.strip() for x in 글[1:-1].split(",")], 열별))
        for 목록, 열별 in 후보:
            빠진 = [(줄[n], cid) for cid, 자리 in 열별.items() if len(자리) > 1
                   for n in range(min(자리), max(자리) + 1) if (줄[n], cid) in 입력 and (줄[n], cid) not in 덮인]
            if 빠진:
                결.setdefault(sid, []).append((목록, 빠진))
                덮인.update(빠진)
    return 결


def 납품배치(명세):
    """명세(14 · 15번 뼈대를 덧명세로 읽은 것) → 납품 배치. 명세의 시트 가운데 서식표준의 시트 사양에 있는 것을 그 순서로 놓는다."""
    import 서식훅
    import 범위지문
    import 줄무늬
    from 공통 import 배치오류
    표준 = 서식훅._표준읽기(서식훅.표준경로)
    if 표준 is None:
        raise SystemExit("서식표준.py 가 없다: %s" % 서식훅.표준경로)
    선택 = 선택칸찾기(명세)
    건너뛴 = 건너뛴칸찾기(명세)
    범위들 = 가로지르는범위(명세)
    사유칸 = 사유칸찾기(명세)
    문 = 줄무늬.문맥만들기(명세)
    배치 = OrderedDict([("설명", "납품 배치 — 배치_납품.py 가 명세에서 낸 것이다. 손으로 고치지 않는다(규칙은 배치_납품.py 에)."),
                      ("서식길", "표준"), ("시트", [])])
    순서 = [s["id"] for s in 표준.시트표 if s["id"] in 명세["시트"]] + [sid for sid in 명세["시트"] if sid not in 표준.사양]
    for sid in 순서:
        명 = 명세["시트"][sid]
        사 = 표준.시트사양(sid)
        줄들 = list(명["행"])
        종 = {c["id"]: c.get("종류") for c in 명["열"]}
        열 = [c["id"] for c in 명["열"]]
        b = OrderedDict([("id", sid), ("이름", 사.get("탭") or 명.get("옛이름") or 명.get("이름"))])
        줄서식, 덧칸, 묶음, 열묶음 = OrderedDict(), OrderedDict(), [], []

        # 10. 1번 시트 — 색 범례 · 약어 구획을 맨 아래로(인쇄 영역 밖)
        인쇄끝줄 = None
        if sid == "S01":
            묶 = 구획들(줄들)
            보낼 = []
            for rid, 낱말들 in 아래로:
                for 머리, 안 in 묶:
                    if 머리 is not None and 안 not in 보낼 and (
                            머리["id"] == rid or any(w in (머리.get("이름") or "") for w in 낱말들)):
                        보낼.append(안)
                        break
            if 보낼:
                뺄 = {r["id"] for 안 in 보낼 for r in 안}
                남은 = [r for r in 줄들 if r["id"] not in 뺄]
                인쇄끝줄 = next((r["id"] for r in reversed(남은) if r.get("종류") != "빈줄"), None)      # 인쇄 영역은 여기까지
                줄들 = 남은 + [r for 안 in 보낼 for r in 안]
        # 머리 구역(첫 구획머리 앞)의 끝에 빈 줄이 겹치면 뒤의 빈줄을 뺀다 — 안내 띠를 비운 줄(3행) 아래에 빈줄이 또 있는 시트(1번).
        # 범위 참조가 그 줄에 걸쳐 있으면 두고 간다
        첫구획 = next((i for i, r in enumerate(줄들) if r.get("종류") == "구획머리"), None)
        if 첫구획 and 첫구획 >= 2 and not 명.get("덧파일"):
            가, 나 = 줄들[첫구획 - 2], 줄들[첫구획 - 1]
            가빈 = 가.get("종류") in ("빈줄", "글") and not any("f" in 한 or 한.get("v") not in (None, "") for 한 in (가.get("칸") or {}).values())
            곳 = {r["id"]: i for i, r in enumerate(줄들)}
            걸친 = any(min(곳[x], 곳[z]) <= 첫구획 - 1 <= max(곳[x], 곳[z]) for x, z in 범위들 if x in 곳 and z in 곳)
            if 가빈 and 나.get("종류") == "빈줄" and not (나.get("칸") or {}) and not 걸친:
                줄들.remove(나)
                b["뺄줄"] = [나["id"]]
        for 묶이름, rid in 없으면빼는줄.get(sid, ()):      # 16. 이 회차의 축에 그 묶음의 열이 없다 — 놓일 칸이 없는 줄을 뺀다
            r = next((x for x in 줄들 if x["id"] == rid), None)
            if r is not None and 묶이름 in 문.묶음.get(sid, {}) and not 문.묶음열(sid, 묶이름):
                줄들.remove(r)
                b.setdefault("뺄줄", []).append(rid)
        b["행"] = [r["id"] for r in 줄들]

        # 3. 번호 열 — 여백 열을 번호 열로 바꾼다(새 시트는 제 번호 열을 명세에 갖고 있다)
        번호머리 = 사.get("번호")
        번호열 = False
        if 번호머리 and not 명.get("덧파일") and "번호" not in 열 and 열 and 종.get(열[0]) == "여백":
            b["열"] = [{"새열": "번호", "폭": 표준.폭["번호"], "종류": "번호"}] + 열[1:]
            b["뺄열"] = [열[0]]
            번호열 = True
        else:
            b["열"] = list(열)
        세줄 = {}
        if 명.get("가정묶음"):
            for 머리, 세 in 범위지문.가정묶음(명):
                for x in 세:
                    세줄[x] = 머리
        값열 = [c for c in 열 if 종.get(c) in 값열종류]
        첫값열 = 값열[0] if 값열 else None

        # 4 · 5. 머리 구역과 틀 고정
        묶 = 구획들(줄들)
        머리구역 = 묶[0][1] if 묶[0][0] is None else []
        while 머리구역 and 머리구역[-1].get("종류") == "빈줄":
            머리구역 = 머리구역[:-1]
        머리줄본 = False
        for r in 머리구역:
            if r.get("종류") == "머리":
                머리줄본 = True
            elif 머리줄본 and r.get("종류") in ("계산", "비율", "입력", "소계", "합계"):
                줄서식.setdefault(r["id"], OrderedDict())["종류"] = "머리보조"
        if 머리구역 and not 명.get("덧파일"):
            i = 줄들.index(머리구역[-1])
            if i + 1 < len(줄들):
                b["틀고정"] = {"행": 줄들[i + 1]["id"], "열": (첫값열 if 사.get("틀열") and 첫값열 else b["열"][0] if isinstance(b["열"][0], str) else "번호")}
                # 인쇄의 제목 행 — 머리 구역 바로 아래가 빈 줄이면 그 줄까지 되풀이한다(둘째 쪽부터 머리 줄 바로 아래에 표가 붙지 않게)
                if 줄들[i + 1].get("종류") == "빈줄" and i + 2 < len(줄들):
                    b.setdefault("인쇄", OrderedDict())["제목행"] = [줄들[0]["id"], 줄들[i + 1]["id"]]

        # 번호 — 입력 줄(값 열에 입력 칸이 있는 줄)과 가정 머리 줄. 시나리오 세 줄 · 점검 줄 · 머리 구역에는 싣지 않는다
        if 번호열:
            for r in 줄들:
                rid, n = r["id"], _번호(r["id"])
                if n is None or rid in 세줄 or r.get("종류") in ("점검", "제목", "구획머리", "머리", "글", "빈줄") or r in 머리구역:
                    continue
                if rid in 세줄.values() or any(종.get(c) in 값열종류 for c in (r.get("입력") or ())):
                    덧칸.setdefault(rid, OrderedDict())["번호"] = {"v": "%s-%03d" % (번호머리, n)}
            # 「No.」 — 번호를 실은 줄을 거느린 머리 줄마다(그 머리 줄부터 다음 머리 줄 앞까지에 번호 줄이 있다). 점검 구획의 머리 줄에는 싣지 않는다
            실은 = set(덧칸)
            머리자리 = [i for i, r in enumerate(줄들) if r.get("종류") == "머리"]
            for k, i in enumerate(머리자리):
                끝 = 머리자리[k + 1] if k + 1 < len(머리자리) else len(줄들)
                제구획 = next((안 for _머, 안 in 구획들(줄들) if 줄들[i] in 안), [])
                값줄 = [r for r in 제구획 if r.get("종류") not in ("빈줄", "머리", "구획머리", "제목")]
                if 값줄 and all(r.get("종류") == "점검" for r in 값줄):
                    continue
                if any(줄들[j]["id"] in 실은 for j in range(i + 1, 끝)):
                    덧칸.setdefault(줄들[i]["id"], OrderedDict())["번호"] = {"v": "No."}

        # 6. 소계선 · 합계선 · 줄 종류 고침
        있는 = {r["id"]: r for r in 줄들}
        for rid, 선 in 선고침.items():
            if rid not in 있는:
                continue
            한 = 줄서식.setdefault(rid, OrderedDict())
            if 선 is None:
                if 있는[rid].get("종류") in ("소계", "합계"):
                    한["종류"] = "비율" if (있는[rid].get("서식") or "").startswith("비율") else "계산"
                else:
                    줄서식.pop(rid) if not 한 else None
            else:
                한["선"] = 선
                if 있는[rid].get("종류") in ("소계", "합계") and 있는[rid]["종류"] != 선:
                    한["종류"] = 선
        for rid, 종류 in 종류고침.items():
            if rid in 있는:
                한 = 줄서식.setdefault(rid, OrderedDict())
                한["종류"] = 종류
                if 종류 == "산출":      # 값 칸이 비어 있어도 산출 칸으로 입힌다
                    한["칸꼴"] = OrderedDict((c, "산출") for c in 값열)

        for rid, 꼴 in 칸꼴고침.items():      # 열 구간(열 ID · 묶음 · 그 줄의 별칭)을 열 ID 로 풀어 적는다. 풀리지 않는 구간은 건너뛴다
            if rid not in 있는:
                continue
            for 키, 종류 in 꼴.items():
                try:
                    풀린 = 줄무늬.구간풀기(문, sid, rid, 키)
                except 배치오류:
                    continue
                줄서식.setdefault(rid, OrderedDict()).setdefault("칸꼴", OrderedDict()).update((c, 종류) for c in 풀린)
        for rid, 칸들 in 사유칸.items():      # 15. 점검 줄의 사유 칸 — 명세의 「입력」에 빠진 줄에도 입력 칸으로 세운다
            if rid in 있는:
                꼴 = 줄서식.setdefault(rid, OrderedDict()).setdefault("칸꼴", OrderedDict())
                for c in 칸들:
                    if c in 열:
                        꼴.setdefault(c, "입력글")

        # 6-나. 「서식」이 빠진 줄 — 숫자가 일반 서식으로 보이지 않게 가늠해 준다(명세는 안 고친다).
        #   점검 줄 = 건수 · 단위 칸의 글(% · 배 · 일 · 명 …) · 단위 칸이 수식이면 금액 · 그래도 모르면 서식고침 표
        단위열 = next((c for c in 열 if 종.get(c) == "단위"), None)
        for r in 줄들:
            rid = r["id"]
            if rid in 서식고침:
                줄서식.setdefault(rid, OrderedDict())["서식"] = 서식고침[rid]
                continue
            if rid in 세줄 and "서식" in 줄서식.get(세줄[rid], {}):      # 머리 줄의 서식을 고쳤으면 시나리오 세 줄도 따른다
                줄서식.setdefault(rid, OrderedDict())["서식"] = 줄서식[세줄[rid]]["서식"]
                continue
            if r.get("서식") and 단위열:      # 단위 칸의 글과 어긋난 서식 — 단위를 따른다
                단 = (r.get("칸") or {}).get(단위열) or {}
                단글 = str(단.get("v") or "").strip() if "f" not in 단 else ""
                if 단글 in 단위가족 and r["서식"] not in 단위가족[단글]:
                    줄서식.setdefault(rid, OrderedDict())["서식"] = 단위서식[단글]
                    continue
            if r.get("서식") or "서식" in 줄서식.get(rid, {}):
                continue
            종류 = 줄서식.get(rid, {}).get("종류") or r.get("종류")
            서 = None
            if rid in 세줄:      # 시나리오 세 줄은 머리 줄의 서식을 따른다
                서 = 줄서식.get(세줄[rid], {}).get("서식") or (있는.get(세줄[rid]) or {}).get("서식")
            if 서 is None and 종류 == "점검":
                서 = "건수"
            if 서 is None and 종류 in ("계산", "입력", "소계", "합계", "비율") and 단위열:
                단 = (r.get("칸") or {}).get(단위열) or {}
                서 = "금액" if "f" in 단 else 단위서식.get(str(단.get("v") or "").strip())
            if 서:
                줄서식.setdefault(rid, OrderedDict())["서식"] = 서

        # 7. 들여쓰기
        for r in 줄들:
            if r["id"] in 세줄:
                줄서식.setdefault(r["id"], OrderedDict())["들여"] = 2
            elif sid in 비율들이는시트 and r.get("종류") == "비율" and r not in 머리구역 and "들여" not in r:
                줄서식.setdefault(r["id"], OrderedDict())["들여"] = 1

        # 8. 접기 — 시나리오 세 줄(펴 둔다) · 보조 계산 구획(접는다) · 접는줄 표의 줄(접는다) · 점검 보조 열(접는다)
        자리 = {r["id"]: i for i, r in enumerate(줄들)}
        머리별 = OrderedDict()
        for x, 머리 in 세줄.items():
            if x in 자리:
                머리별.setdefault(머리, []).append(x)
        for 머리, 세 in 머리별.items():
            세.sort(key=자리.get)
            if 머리 in 자리 and [자리[x] for x in 세] == list(range(자리[머리] + 1, 자리[머리] + 1 + len(세))):
                묶음.append({"줄": [세[0], 세[-1]], "수준": 1})
        for 머리, 안 in 묶:
            if 머리 is None or not (머리["id"] in 보조구획줄 or _re보조구획.match(머리.get("이름") or "")):
                continue
            몸 = [r for r in 안[1:]]
            while 몸 and 몸[-1].get("종류") == "빈줄":
                몸.pop()
            if 몸:
                묶음.append({"줄": [몸[0]["id"], 몸[-1]["id"]], "수준": 1, "숨김": True})
        for 첫, 끝 in 접는줄.get(sid, ()):
            if 첫 in 자리 and 끝 in 자리 and 자리[첫] <= 자리[끝]:
                묶음.append({"줄": [첫, 끝], "수준": 1, "숨김": True})
        # 보이는 열에 아무것도 없는 줄 — 점검 보조 열에만 값이 있는 줄(4번 점검 구획의 보조 계산 줄)을 이어진 것끼리 묶어 접는다
        이미 = {x for 묶 in 묶음 for x in (r["id"] for r in 줄들[자리[묶["줄"][0]]:자리[묶["줄"][1]] + 1])}
        달 = []
        for r in 줄들 + [None]:
            찬 = [c for c, 한 in ((r or {}).get("칸") or {}).items() if "f" in 한 or 한.get("v") not in (None, "")]
            if r is not None and r["id"] not in 이미 and 찬 and all(종.get(c) in 보조열종류 for c in 찬):
                달.append(r["id"])
            elif 달:
                묶음.append({"줄": [달[0], 달[-1]], "수준": 1, "숨김": True})
                달 = []
        새열순 = [c if isinstance(c, str) else c["새열"] for c in b["열"]]
        달 = []
        for c in 새열순 + [None]:
            if c is not None and (종.get(c) in 보조열종류 or c in 접는열.get(sid, ())):
                if 달 and (종.get(c) in 보조열종류) != (종.get(달[-1]) in 보조열종류):      # 보조 열과 접는 열은 따로 묶는다
                    열묶음.append({"열": [달[0], 달[-1]], "수준": 1, "숨김": True})
                    달 = []
                달.append(c)
            elif 달:
                열묶음.append({"열": [달[0], 달[-1]], "수준": 1, "숨김": True})
                달 = []
        폭 = {c: w for c, w in 열폭고침.get(sid, {}).items() if c in 새열순}
        if 폭:
            b["열폭"] = 폭

        # 9-가. 글 열의 입력 칸 넓히기 — 붓기가 값을 적는데 명세의 「입력」에 빠진 칸(12번 시점 가정의 방향 · 13번 손익 줄의 소비처).
        #   한 구획의 입력 줄은 같은 글 열을 입력 칸으로 갖는다. 근거 칸이 입력인 줄은 소비처 칸도 입력이다.
        #   같은 구획 · 같은 열의 다른 칸이 선택 칸이면 같은 목록을 걸고, 아니면 글 입력 칸으로 입힌다.
        for 머리, 안 in 묶:
            입줄 = [r for r in 안 if r.get("종류") == "입력" and r["id"] not in 세줄]
            글입 = OrderedDict((r["id"], [c for c in (r.get("입력") or ()) if 종.get(c) in 글열종류]) for r in 입줄)
            합 = [c for c in 열 if any(c in v for v in 글입.values())]
            합 += [c for c in 열 if 종.get(c) == "소비처" and c not in 합]
            for rid, 가진 in 글입.items():
                if not 가진:
                    continue
                for c in 합:
                    if c in 가진:
                        continue
                    짝 = next(((x, c) for x in 글입 if (x, c) in 선택), None)
                    if 짝 is not None:
                        선택[(rid, c)] = 선택[짝]
                        줄서식.setdefault(rid, OrderedDict()).setdefault("칸꼴", OrderedDict())[c] = "선택"
                    else:
                        줄서식.setdefault(rid, OrderedDict()).setdefault("칸꼴", OrderedDict())[c] = (
                            "입력긴글" if 종.get(c) in 긴글열종류 else "입력글")

        # 9. 목록 유효성 — 수식이 글 상수와 견주는 입력 칸
        목록별 = OrderedDict()
        for (rid, cid), 낱 in 선택.items():
            if rid in 자리:
                목록별.setdefault(tuple(낱), []).append("[%s]@%s" % (rid, cid))
        if 목록별:
            b["유효성"] = [{"범위": 범위, "목록": list(낱), "빈칸허용": True, "경고": True} for 낱, 범위 in 목록별.items()]
        for 줄ids, cid, 목록 in 선택고침.get(sid, ()):      # 명세의 「입력」에 없는 선택 칸 — 목록 밖 값은 막지 않고 경고만 한다
            범위 = []
            for rid in 줄ids:      # 열은 열 구간으로 적혀 있다(자리 이름 · 별칭) — 열 ID 로 푼다
                try:
                    범위 += ["[%s]@%s" % (rid, c) for c in (줄무늬.구간풀기(문, sid, rid, cid) if rid in 자리 else ())]
                except 배치오류:
                    continue
            if 범위:
                b.setdefault("유효성", []).append({"범위": 범위, "목록": list(목록), "빈칸허용": True, "경고": True})
        for 목록, 빠진 in 건너뛴.get(sid, ()):      # 명세의 목록 유효성이 건너뛴 입력 칸 — 같은 목록을 건다(목록 밖 값은 막는다)
            범위 = ["[%s]@%s" % (rid, cid) for rid, cid in 빠진 if rid in 자리]
            if 범위:
                b.setdefault("유효성", []).append({"범위": 범위, "목록": 목록, "빈칸허용": True})

        # 12. 구획 머리의 번호 — 로마 숫자를 차례로(이름 칸이 글 상수인 구획만. 이미 번호가 붙은 이름 · 보조 계산 구획은 그대로)
        새이름, 차례 = OrderedDict(), 0
        for 머리, 안 in 묶:
            if 머리 is None or 명.get("덧파일"):
                continue
            이름 = (머리.get("칸") or {}).get(이름열of(명), {}).get("v")
            if not isinstance(이름, str) or 머리["id"] in 보조구획줄 or _re보조구획.match(이름) or _re번호머리.match(이름):
                continue
            if 종류고침.get(머리["id"]) == "소구획":
                continue
            차례 += 1
            새이름[머리["id"]] = "%s. %s" % (로마(차례), 이름.strip())
        if 새이름:
            b["새이름"] = 새이름
        쪽 = [rid for rid in 쪽나눔줄.get(sid, ()) if rid in 자리 and 자리[rid] > 0]

        # 13. 구획 사이의 빈 줄 — 구획머리(소구획 포함) 앞에 빈 줄이 없으면 한 줄 넣는다. 범위 참조가 그 틈을 가로지르면 넣지 않는다
        if not 명.get("덧파일"):
            가른 = [tuple(sorted((자리[a], 자리[z]))) for a, z in 범위들 if a in 자리 and z in 자리]
            넣을, 못넣은 = set(), []
            for i, r in enumerate(줄들):
                if i == 0 or r.get("종류") != "구획머리":
                    continue
                앞 = 줄들[i - 1]
                앞빈 = 앞.get("종류") == "빈줄" or not any("f" in 한 or 한.get("v") not in (None, "") for 한 in (앞.get("칸") or {}).values())
                if 앞빈 or 앞 in 머리구역 or 앞.get("종류") in ("구획머리", "제목"):
                    continue
                if any(lo < i <= hi for lo, hi in 가른):
                    못넣은.append(r["id"])
                    continue
                넣을.add(r["id"])
            if 넣을:
                b["행"] = [x for r in 줄들 for x in (([{"빈줄": 1}] if r["id"] in 넣을 else []) + [r["id"]])]
            if 못넣은:
                b["설명"] = "구획머리 앞에 빈 줄을 넣지 못한 곳(범위가 가로지른다): %s" % " · ".join(못넣은)

        # 18. 배치가 끼우는 새 줄 — 그 줄이 읽는 새 시트가 명세에 있을 때만
        for 뒤, 읽는시트, 항 in 끼울새줄.get(sid, ()):
            if 읽는시트 in 명세["시트"] and 뒤 in b["행"]:
                b["행"].insert(b["행"].index(뒤) + 1, OrderedDict(항))
        if 줄서식:
            b["줄서식"] = OrderedDict((k, v) for k, v in 줄서식.items() if v)
        if 덧칸:
            b["덧칸"] = 덧칸
        if 묶음:
            b["묶음"] = 묶음
        if 열묶음:
            b["열묶음"] = 열묶음
        if 인쇄끝줄:
            b.setdefault("인쇄", OrderedDict())["영역"] = {"끝행": 인쇄끝줄, "끝열": 값열[-1] if 값열 else 새열순[-1]}
        # 17. 예측 열이 여덟 개 이상인 회차 — 계산 시트(뼈대 「시간축」)도 A3 가로로
        if 사.get("뼈대") == "시간축" and sum(1 for c in 명["열"] if c.get("종류") == "예측") >= 큰용지예측열:
            b.setdefault("인쇄", OrderedDict()).update(방향="landscape", 용지=큰용지)
        if 쪽:
            b.setdefault("인쇄", {})["쪽나눔"] = 쪽
        배치["시트"].append(b)
    return 배치


def 명세읽기(폴더, 기간=None):
    """납품 명세 — 정본 폴더 + 14 · 15번 뼈대(납품시트/). 정본이 이미 14 · 15번을 갖고 있으면 뼈대는 읽지 않는다.

    기간 : 가정 사전 · 가정 파일 경로 따위(줄무늬.읽기). 주면 시간축 열을 그 회차의 열로 편다 — 회차의 워크북은 이렇게 짓는다."""
    import 짓기
    with open(os.path.join(폴더, "책.json"), encoding="utf-8") as f:
        있는 = set(json.load(f).get("시트순서") or ())
    덧 = [p for p in 새시트파일 if os.path.splitext(os.path.basename(p))[0] not in 있는]
    return 짓기.명세읽기(폴더, 옛서식=False, 덧파일=덧, 기간=기간), 덧


def 새시트지문(폴더=None):
    """납품시트/ 의 범위 지문과 줄 이름표를 지금 뼈대 파일로 다시 적는다(정본 폴더의 것은 건드리지 않는다)."""
    import 줄무늬
    import 범위지문
    명, _ = 명세읽기(폴더 or os.path.join(여기, "줄명세"))
    지문 = 범위지문.만들기(명)
    새 = OrderedDict((sid, 한) for sid, 한 in 지문["시트"].items() if 명["시트"][sid].get("덧파일"))
    곳 = os.path.join(여기, "납품시트", 범위지문.파일이름)
    범위지문.쓰기(곳, {"형식": 범위지문.형식, "시트": 새})
    문 = 줄무늬.문맥만들기(명)
    글 = OrderedDict([("형식", "줄이름 1"),
                     ("설명", "줄마다 마지막으로 맞춰 둔 이름. 손으로 고치지 않는다 — python 배치_납품.py --새시트지문 이 고쳐 적는다."),
                     ("시트", OrderedDict())])
    for sid in 새:
        낱 = OrderedDict()
        for 줄 in 명["시트"][sid]["행"]:
            이름 = 줄무늬.줄이름들(문, 줄["id"])
            if 이름:
                낱[줄["id"]] = 이름[0] if len(이름) == 1 else 이름
        글["시트"][sid] = 낱
    with open(os.path.join(여기, "납품시트", 줄무늬.이름파일), "w", encoding="utf-8", newline="\n") as f:
        json.dump(글, f, ensure_ascii=False, indent=1)
        f.write("\n")
    return 곳, list(새)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.path.insert(0, 여기)
    인자 = [a for a in sys.argv[1:] if a not in ("--경고허용",)]
    기간 = None
    if "--기간" in 인자:
        i = 인자.index("--기간")
        if i + 1 >= len(인자):
            raise SystemExit("--기간 뒤에 가정 파일(또는 기간 json)이 없다")
        기간 = 인자[i + 1]
        del 인자[i:i + 2]
    if 인자 and 인자[0] == "--새시트지문":
        곳, 시트 = 새시트지문(인자[1] if len(인자) > 1 else None)
        print("범위 지문 · 줄 이름표를 적었다: %s (%s)" % (os.path.dirname(곳), " · ".join(시트)))
        sys.exit(0)
    if not 인자:
        raise SystemExit(__doc__)
    import 짓기
    from 공통 import 배치오류
    try:
        명, 덧 = 명세읽기(인자[0], 기간=기간)
        배 = 납품배치(명)
    except 배치오류 as e:
        짓기.알림찍기(e.오류목록, "오류", 보기=8)
        sys.exit(1)
    if "--짓기" in 인자:
        i = 인자.index("--짓기")
        낼 = 인자[i + 1:]
        if not 1 <= len(낼) <= 2:
            raise SystemExit(__doc__)
        try:
            결 = 짓기.짓기(명, 배, 낼[0], 낼[1] if len(낼) > 1 else None)
        except 배치오류 as e:
            짓기.알림찍기(e.오류목록, "오류", 보기=8)
            print("파일을 내지 않았다")
            sys.exit(1)
        위험 = [w for w in 결["경고"] if w["종류"] in 짓기.위험경고]
        print("지었다: %s · 서식길 %s · 경고 %d건(위험 %d건)" % (낼[0], 배["서식길"], len(결["경고"]), len(위험)))
        if 결["경고"]:
            짓기.알림찍기(결["경고"], "경고")
        sys.exit(2 if 위험 and "--경고허용" not in sys.argv else 0)
    낼곳 = 인자[1] if len(인자) > 1 else 기본낼곳
    with open(낼곳, "w", encoding="utf-8", newline="\n") as f:
        json.dump(배, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print("배치를 냈다: %s — 시트 %d장 · 서식길 %s · 덧명세 %s" % (
        낼곳, len(배["시트"]), 배["서식길"], " ".join(os.path.relpath(p, 여기) for p in 덧) or "없음"))

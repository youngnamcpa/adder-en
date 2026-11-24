# -*- coding: utf-8 -*-
"""잔차상관을 계산한다.

왜 필요한가
    고성장 기술주는 시장이 오르면 다 같이 오른다. 서로 아무 관계가 없어도
    단순 상관이 높게 나온다. 각 종목을 시장 지수에 회귀해 시장 효과를 걷어내고
    남은 고유 변동끼리 비교해야 실제로 같이 움직이는지가 보인다.

사양 (종목마다 흔들리지 않게 고정한다)
    3년, 주간 로그수익률, 시장지수는 상장 시장에 맞춘다.
    한국 KOSPI / 미국 S&P 500 / 일본 닛케이 225.

쓰는 법
    python 잔차상관.py 가격.csv --대상 TSLA --시장 ^GSPC
    가격.csv 는 첫 열이 날짜이고 나머지 열이 종목별 종가인 표다.
    (시세를 어디서 받아올지는 이 스크립트가 정하지 않는다. 표를 만들어 넘긴다.)
"""
import argparse, csv, math, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


def 로그수익률(값들):
    결과 = []
    for 앞, 뒤 in zip(값들, 값들[1:]):
        if 앞 and 뒤 and 앞 > 0 and 뒤 > 0:
            결과.append(math.log(뒤 / 앞))
        else:
            결과.append(None)
    return 결과


def 상관(a, b):
    쌍 = [(x, y) for x, y in zip(a, b) if x is not None and y is not None]
    n = len(쌍)
    if n < 3:
        return None, n
    ax = sum(x for x, _ in 쌍) / n
    ay = sum(y for _, y in 쌍) / n
    분자 = sum((x - ax) * (y - ay) for x, y in 쌍)
    좌 = math.sqrt(sum((x - ax) ** 2 for x, _ in 쌍))
    우 = math.sqrt(sum((y - ay) ** 2 for _, y in 쌍))
    if 좌 == 0 or 우 == 0:
        return None, n
    return 분자 / (좌 * 우), n


def 회귀잔차(y, x):
    """y 를 x 에 회귀하고 잔차를 돌려준다. 시장 효과를 걷어내는 자리다."""
    쌍 = [(a, b) for a, b in zip(x, y) if a is not None and b is not None]
    n = len(쌍)
    if n < 3:
        return [None] * len(y)
    ax = sum(a for a, _ in 쌍) / n
    ay = sum(b for _, b in 쌍) / n
    분모 = sum((a - ax) ** 2 for a, _ in 쌍)
    기울기 = sum((a - ax) * (b - ay) for a, b in 쌍) / 분모 if 분모 else 0.0
    절편 = ay - 기울기 * ax
    return [None if (a is None or b is None) else b - (절편 + 기울기 * a)
            for a, b in zip(x, y)]


def 읽기(경로):
    with io.open(경로, encoding="utf-8-sig") as f:
        행 = list(csv.reader(f))
    머리, 몸 = 행[0], 행[1:]
    표 = {이름: [] for 이름 in 머리[1:]}
    for r in 몸:
        for 이름, 값 in zip(머리[1:], r[1:]):
            try:
                표[이름].append(float(값.replace(",", "")) if 값.strip() else None)
            except ValueError:
                표[이름].append(None)
    return 표


def main():
    p = argparse.ArgumentParser()
    p.add_argument("가격표")
    p.add_argument("--대상", required=True)
    p.add_argument("--시장", required=True)
    a = p.parse_args()

    표 = 읽기(a.가격표)
    for 필요 in (a.대상, a.시장):
        if 필요 not in 표:
            print("열이 없다: %s" % 필요); sys.exit(1)

    수익 = {이름: 로그수익률(값) for 이름, 값 in 표.items()}
    시장 = 수익[a.시장]
    대상잔차 = 회귀잔차(수익[a.대상], 시장)

    print("%-10s %10s %10s %6s" % ("종목", "단순상관", "잔차상관", "표본"))
    결과 = []
    for 이름, 값 in 수익.items():
        if 이름 in (a.대상, a.시장):
            continue
        단순, n1 = 상관(값, 수익[a.대상])
        잔차, n2 = 상관(회귀잔차(값, 시장), 대상잔차)
        결과.append((이름, 단순, 잔차, n2))
    결과.sort(key=lambda r: (r[2] is None, -(r[2] or 0)))
    for 이름, 단순, 잔차, n in 결과:
        print("%-10s %10s %10s %6d" % (
            이름,
            "확인 불가" if 단순 is None else "%.3f" % 단순,
            "확인 불가" if 잔차 is None else "%.3f" % 잔차, n))

    if 결과 and 결과[0][3]:
        표준오차 = 1 / math.sqrt(결과[0][3])
        print("\n표본 %d주 기준 상관계수 표준오차 약 %.3f." % (결과[0][3], 표준오차))
        print("잔차상관이 %.2f 를 밑돌면 0과 구별되지 않는다." % (1.96 * 표준오차))


if __name__ == "__main__":
    main()

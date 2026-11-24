# -*- coding: utf-8 -*-
"""서술유사도 — 대상회사와 유사기업 후보의 최신 사업보고서 「II. 사업의 내용」 글이 얼마나 닮았는지 문자 n-gram TF-IDF 코사인으로 잰다
(NLP ④ · 2026-10-21). C 갈래가 경로 ②(사업부문 대응)를 보강할 재료 열 하나를 낸다.

    python 스크립트/서술유사도.py 가정.json                       # 후보 = 가정 곁 _raw/peers/핵심표본.json(없으면 핵심표본_초안.json)
    python 스크립트/서술유사도.py 가정.json --명단 후보.txt        # 고유번호 한 줄씩(쉼표 뒤 회사명 · 구분은 선택)
    python 스크립트/서술유사도.py 가정.json --받기                 # 공용 캐시에 없는 후보의 최신 사업보고서를 받는다(사람 허락 뒤에만)

왜 있나
    경로 ② 는 KIND 주요제품 낱말로 후보를 모은다. 낱말 하나가 우연히 겹친 회사(실측 — 「마트」 가 「스마트」 에 걸렸다)와 사업이
    정말 닮은 회사를 그 단계에서는 가를 재료가 없다. 사업보고서의 사업 서술 전체를 견주면 「접점 미확인」 후보에 재료가 하나 생긴다.
    **결과와 무관한 기준(사업 서술)이라 「베타 · 상관 · 수익률로 자르지 않는다」와 부딪히지 않는다.** 그래도 **선정하지 않는다** —
    유사도 · 순위 · 겹친 낱말을 재료 열로 낼 뿐이고, 몇 등까지 담을지는 사람이 정한다. 유사도가 낮다는 것은 「사업 접점의 근거를
    적으라」는 신호이지 빼라는 뜻이 아니다.

읽는 것
    절            「II. 사업의 내용」 전체가 기본(설정 `절범위` — 「개요와제품」 이면 사업의 개요 · 주요 제품 및 서비스만)
    대상회사 원문  가정 곁 `_raw/사업{연도}/{접수번호}.txt` 가운데 가장 최근 연도(dart_fetch 원문 꼴). 없으면 `_raw/**/{접수번호}.txt` 중
                  「사업의 내용」 을 가진 가장 큰 본문
    후보 명단      `_raw/peers/핵심표본.json`(C1 — `가정_스키마.md` 정본 꼴 · 「핵심」 · 「예비」의 `고유번호` · `회사명`) 또는 `--명단`
    후보 원문      공용 캐시 `{공용}/원문/{고유번호}/{접수번호}.txt` — 공용 = 환경변수 `DCF_공용캐시` 또는 `DCF_SHARED_CACHE` 또는 `~/.dcf캐시`
    설정           `조항설정.json` 「서술유사도」 — n-gram 길이 · 겹친 낱말 수 · 하위 분위 문턱(결과를 보기 전에 정했다)

받기 (`--받기` 를 줄 때만)
    공시 원문 대량 수집이라 사람 허락이 먼저다. `--받기` 없이 돌면 원문이 빈 후보 수와 받을 명령만 찍는다(네트워크를 타지 않는다).
    받을 때는 `list.json` 으로 최근 `목록최근년수` 해의 정기공시에서 가장 늦은 사업보고서 접수번호를 찾고, `dart_fetch.원문` 과 같은 길
    (document.xml → 막히면 뷰어 우회)로 `{공용}/원문/{고유번호}/` 에 받는다. 안전 속도 0.6초 · 인증키는 환경변수 `OPENDART_API_KEY` 에서만.
    회차 폴더가 본체(정본 키트)면 `본체가드` 가 멈춘다.

내는 것
    `_raw/peers/서술유사도.json`  {"형식": "서술유사도 1", "만든날", "설정", "입력", "대상": {"원문", "글자수"},
                                  "후보": [{"고유번호", "회사명", "구분", "유사도", "순위", "겹친낱말", "원문", "상태"}], "신호": [...]}
    `_raw/peers/서술유사도.csv`   고유번호 · 회사명 · 구분 · 유사도 · 순위 · 겹친낱말(상위 10) · 원문 · 상태
    신호 종류 — 「원문 없음」(참고) · 「서술 유사도 하위 핵심 후보」(참고)

종료 코드 — 0 통과 · 1 발견(원문이 빈 후보가 있다) · 2 입력오류(가정 · 대상 원문 · 명단 없음).
회사 · 업종 이름은 이 도구에 한 글자도 없다.
"""
from __future__ import annotations

import argparse
import csv
import datetime
import glob
import io
import json
import math
import os
import re
import sys
from collections import Counter

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:                                            # noqa: BLE001
    pass

여기 = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, 여기)
from 종료코드 import 통과, 발견, 입력오류  # noqa: E402

기본설정 = os.path.join(여기, "조항설정.json")
_본문이름 = re.compile(r"^(\d{14})\.txt$")



def _평가기준일(가정):
    """메타 날짜를 `기준일.py` 로 푼다(날짜 둘 — 2026-10-25). 못 풀면 None."""
    try:
        import 기준일 as _B                                   # noqa: PLC0415
        return _B.평가기준일(가정).isoformat()
    except Exception:                                         # noqa: BLE001
        return None

def 공용캐시():
    d = os.environ.get("DCF_공용캐시") or os.environ.get("DCF_SHARED_CACHE")
    return d or os.path.join(os.path.expanduser("~"), ".dcf캐시")


def 설정읽기(p=None):
    return json.load(io.open(p or 기본설정, encoding="utf-8"))["서술유사도"]


# ── 절 고르기 ──────────────────────────────────────────────────────────────
_II = re.compile(r"(?:II|Ⅱ)\s*\.\s*사업의\s*내용")
_III = re.compile(r"(?:III|Ⅲ)\s*\.\s*재무에\s*관한\s*사항")
_개요 = re.compile(r"(?m)^\s*1\s*\.\s*사업의\s*개요")
_원재료 = re.compile(r"(?m)^\s*3\s*\.\s*원재료")


def 사업의내용(글, 절범위="전체"):
    """「II. 사업의 내용」 ~ 「III. 재무에 관한 사항」 가운데 가장 긴 구간(목차의 같은 제목을 건너뛴다). 없으면 None.
    절범위 「전체」(기본 — 최근 서식의 「1. 사업의 개요」 는 요약이라 짧고 사업 서술은 「7. 기타 참고사항」 까지 이어진다) ·
    「개요와제품」 이면 그 안의 「1. 사업의 개요」 ~ 「3. 원재료」 앞(사업의 개요 · 주요 제품 및 서비스)만."""
    if not 글:
        return None
    시작 = [m.start() for m in _II.finditer(글)]
    끝 = [m.start() for m in _III.finditer(글)]
    best = None
    for s in 시작:
        e = next((x for x in 끝 if x > s), len(글))
        if best is None or (e - s) > (best[1] - best[0]):
            best = (s, e)
    if not best:
        return None
    구 = 글[best[0]:best[1]]
    if 절범위 != "개요와제품":
        return 구
    a = _개요.search(구)
    b = _원재료.search(구, a.end()) if a else None
    if a and b and (b.start() - a.start()) > 200:
        return 구[a.start():b.start()]
    return 구


def _본문고르기(파일들):
    """접수번호 14자리 그 자체가 이름인 본문 가운데 가장 늦은 접수(같으면 큰 것)."""
    본 = [p for p in 파일들 if _본문이름.match(os.path.basename(p))]
    if not 본:
        return None
    return max(본, key=lambda p: (os.path.basename(p), os.path.getsize(p)))


def 대상원문(raw):
    폴더 = []
    for d in glob.glob(os.path.join(raw, "사업*")):
        m = re.fullmatch(r"사업(\d{4})", os.path.basename(d))
        if m and os.path.isdir(d):
            폴더.append((int(m.group(1)), d))
    for _연, d in sorted(폴더, reverse=True):
        p = _본문고르기(glob.glob(os.path.join(d, "*.txt")))
        if p:
            return p
    후 = []
    for p in glob.glob(os.path.join(raw, "**", "*.txt"), recursive=True):
        if os.path.relpath(p, raw).replace("\\", "/").startswith("peers/") or not _본문이름.match(os.path.basename(p)):
            continue
        try:
            t = io.open(p, encoding="utf-8").read()
        except (IOError, OSError, UnicodeDecodeError):
            continue
        if _II.search(t):
            후.append((len(t), p))
    return max(후)[1] if 후 else None


def 후보원문(공용, 고유):
    d = os.path.join(공용, "원문", 고유)
    return _본문고르기(glob.glob(os.path.join(d, "*.txt"))) if os.path.isdir(d) else None


def 명단읽기(raw, 명단파일=None):
    if 명단파일:
        out = []
        for 줄 in io.open(명단파일, encoding="utf-8-sig"):
            쪽 = [x.strip() for x in 줄.strip().split(",")]
            if not 쪽 or not 쪽[0]:
                continue
            out.append({"고유번호": 쪽[0].zfill(8), "회사명": 쪽[1] if len(쪽) > 1 else "",
                        "구분": 쪽[2] if len(쪽) > 2 else "명단"})
        return out, os.path.basename(명단파일)
    for 이름 in ("핵심표본.json", "핵심표본_초안.json"):
        p = os.path.join(raw, "peers", 이름)
        if os.path.exists(p):
            d = json.load(io.open(p, encoding="utf-8"))
            out = []
            for 구분 in ("핵심", "예비"):
                for c in d.get(구분) or []:
                    고 = str(c.get("고유번호") or "").strip()
                    if 고:
                        out.append({"고유번호": 고.zfill(8), "회사명": c.get("회사명") or "", "구분": 구분})
            return out, 이름
    return None, None


# ── TF-IDF ────────────────────────────────────────────────────────────────
def _다듬기(글):
    글 = (글 or "").replace("&cr;", " ").lower()
    글 = re.sub(r"[^가-힣a-z ]+", " ", 글)
    return re.sub(r"\s+", " ", 글).strip()


def 문자그램(글, n들):
    t = _다듬기(글)
    c = Counter()
    for n in range(n들[0], n들[1] + 1):
        for i in range(len(t) - n + 1):
            g = t[i:i + n]
            if g.strip():
                c[g] += 1
    return c


def 낱말(글, 꼬리):
    out = Counter()
    for w in re.findall(r"[가-힣A-Za-z]{2,}", (글 or "").replace("&cr;", " ")):
        for k in 꼬리:
            if len(w) > len(k) + 1 and w.endswith(k):
                w = w[:-len(k)]
                break
        if len(w) >= 2:
            out[w.lower()] += 1
    return out


def tfidf(문서들):
    """[Counter] → [dict(단위벡터)]. tf = 1 + log(빈도), idf = log((1 + N) / (1 + df)) + 1."""
    N = len(문서들)
    df = Counter()
    for c in 문서들:
        df.update(c.keys())
    out = []
    for c in 문서들:
        v = {g: (1 + math.log(f)) * (math.log((1 + N) / (1 + df[g])) + 1) for g, f in c.items()}
        nrm = math.sqrt(sum(x * x for x in v.values())) or 1.0
        out.append({g: x / nrm for g, x in v.items()})
    return out


def 코사인(a, b):
    if len(a) > len(b):
        a, b = b, a
    return sum(x * b.get(g, 0.0) for g, x in a.items())


# ── 받기 ──────────────────────────────────────────────────────────────────
def 받기(빈것, 공용, 기준일, 년수, 방):
    sys.path.insert(0, 여기)
    import 본체가드                                          # noqa: PLC0415
    본체가드.본체면멈춘다(방)
    if not os.environ.get("OPENDART_API_KEY"):
        print("환경변수 OPENDART_API_KEY 가 없다 — 키를 화면에 적지 말고 환경변수로 넣는다")
        return []
    import dart_fetch as F                                   # noqa: PLC0415
    F.RAW = os.path.join(공용, "원문")
    try:
        import dart_뷰어원문 as V                             # noqa: PLC0415
        V.RAW = F.RAW
    except Exception:                                        # noqa: BLE001
        pass
    끝 = (기준일 or datetime.date.today().isoformat()).replace("-", "")
    시작 = "%d0101" % (int(끝[:4]) - 년수)
    받은 = []
    for c in 빈것:
        try:
            j = F._get("list.json", corp_code=c["고유번호"], bgn_de=시작, end_de=끝, pblntf_ty="A", page_count=100).json()
        except Exception as e:                               # noqa: BLE001
            print("  %s 목록 실패 — %s" % (c["고유번호"], type(e).__name__))
            continue
        후 = [x for x in (j.get("list") or []) if re.search(r"사업보고서", x.get("report_nm") or "")]
        if not 후:
            print("  %s — 최근 %d년 사업보고서 없음" % (c["고유번호"], 년수))
            continue
        x = max(후, key=lambda r: r.get("rcept_no") or "")
        try:
            F.원문(x["rcept_no"], c["고유번호"])
            받은.append((c["고유번호"], x["rcept_no"]))
        except (Exception, SystemExit) as e:                 # noqa: BLE001
            print("  %s 원문 실패 — %s" % (c["고유번호"], e))
    return 받은


def main(argv=None):
    ap = argparse.ArgumentParser(allow_abbrev=False, description="사업 서술 유사도(문자 n-gram TF-IDF 코사인) — 선정하지 않는다")
    ap.add_argument("가정")
    ap.add_argument("--명단", default=None)
    ap.add_argument("--받기", action="store_true", help="공용 캐시에 없는 후보 원문을 받는다(공시 원문 대량 수집 — 사람 허락 뒤에만)")
    ap.add_argument("--설정", default=None)
    a = ap.parse_args(argv)
    if not os.path.exists(a.가정):
        print("가정 파일이 없다: %s" % a.가정)
        return 입력오류
    try:
        가정 = json.load(io.open(a.가정, encoding="utf-8"))
        S = 설정읽기(a.설정)
    except (ValueError, IOError, OSError, KeyError) as e:
        print("JSON 을 못 읽었다 — %s" % e)
        return 입력오류
    방 = os.path.dirname(os.path.abspath(a.가정))
    raw = os.path.join(방, "_raw")
    공용 = 공용캐시()
    t원 = 대상원문(raw)
    t글 = 사업의내용(io.open(t원, encoding="utf-8").read(), S.get("절범위", "전체")) if t원 else None
    if not t글 or len(t글) < S["최소글자"]:
        print("대상회사의 「II. 사업의 내용」 을 원문에서 못 찾았다 — %s 아래 사업보고서 원문(dart_fetch) 이 필요하다" % raw)
        return 입력오류
    명단, 명단출처 = 명단읽기(raw, a.명단)
    if not 명단:
        print("후보 명단이 없다 — _raw/peers/핵심표본.json(C1) 이나 --명단 파일을 준다")
        return 입력오류

    빈것 = [c for c in 명단 if not 후보원문(공용, c["고유번호"])]
    받은 = []
    if 빈것 and a.받기:
        print("공용 캐시에 원문이 없는 후보 %d곳을 받는다 → %s" % (len(빈것), os.path.join(공용, "원문")))
        받은 = 받기(빈것, 공용, _평가기준일(가정), S["목록최근년수"], 방)   # 공시 목록 경계 — 평가기준일(T · 2026-10-25 날짜 둘)

    줄, 글들, 낱말들 = [], [t글], [낱말(t글, S["조사꼬리"])]
    for c in 명단:
        p = 후보원문(공용, c["고유번호"])
        글 = 사업의내용(io.open(p, encoding="utf-8").read(), S.get("절범위", "전체")) if p else None
        r = dict(c, 원문=os.path.basename(p) if p else None, 유사도=None, 순위=None, 겹친낱말="")
        if not p:
            r["상태"] = "원문 없음"
        elif not 글 or len(글) < S["최소글자"]:
            r["상태"] = "사업의 내용 못 찾음"
        else:
            r["상태"] = "잰"
            r["_i"] = len(글들)
            글들.append(글)
            낱말들.append(낱말(글, S["조사꼬리"]))
        줄.append(r)

    n들 = tuple(S["n그램"])
    벡 = tfidf([문자그램(g, n들) for g in 글들])
    낱벡 = tfidf(낱말들)
    for r in 줄:
        i = r.pop("_i", None)
        if i is None:
            continue
        r["유사도"] = round(코사인(벡[0], 벡[i]), 4)
        겹 = sorted(((낱벡[0][w] * 낱벡[i][w], w) for w in set(낱벡[0]) & set(낱벡[i])), reverse=True)[:S["겹친낱말수"]]
        r["겹친낱말"] = " · ".join(w for _, w in 겹)
    잰 = sorted([r for r in 줄 if r["유사도"] is not None], key=lambda r: -r["유사도"])
    for k, r in enumerate(잰, 1):
        r["순위"] = k

    신호 = []
    if 빈것 and not a.받기:
        신호.append({"출처": "서술유사도", "종류": "원문 없음", "대상": "후보 %d곳" % len(빈것), "값": len(빈것),
                   "문턱": "공용 캐시 {공용}/원문/{고유번호}/",
                   "글": "후보 %d곳의 사업보고서 원문이 공용 캐시에 없어 서술 유사도를 못 쟀다 — 공시 원문 대량 수집이라 사람 허락을 받은 뒤 "
                         "`python 스크립트/서술유사도.py %s --받기` 로 받는다" % (len(빈것), os.path.basename(a.가정)),
                   "등급": "참고"})
    if len(잰) >= 4:
        값들 = sorted(r["유사도"] for r in 잰)
        위치 = S["하위분위_참고"] * (len(값들) - 1)                 # 선형 보간 분위
        lo = int(math.floor(위치))
        hi = min(lo + 1, len(값들) - 1)
        문턱 = 값들[lo] + (위치 - lo) * (값들[hi] - 값들[lo])
        for r in 잰:
            if r["구분"] == "핵심" and r["유사도"] <= 문턱:
                신호.append({"출처": "서술유사도", "종류": "서술 유사도 하위 핵심 후보", "대상": r["회사명"] or r["고유번호"],
                           "값": r["유사도"], "문턱": round(문턱, 4),
                           "글": "핵심 후보 %s 의 사업 서술 유사도 %.3f 가 잰 후보 %d곳의 하위 %d%% 안이다 — 빼라는 뜻이 아니다. "
                                 "핵심표본의 `사업접점` 근거(어느 사업부문이 닿는지)를 적는다"
                                 % (r["회사명"] or r["고유번호"], r["유사도"], len(잰), int(S["하위분위_참고"] * 100)),
                           "등급": "참고"})

    out = {"형식": "서술유사도 1", "만든날": datetime.date.today().isoformat(), "설정": S,
           "입력": {"대상원문": os.path.relpath(t원, raw).replace("\\", "/"), "명단": 명단출처,
                  "공용원문": os.path.join(공용, "원문"), "받은것": 받은},
           "대상": {"원문": os.path.basename(t원), "글자수": len(t글)},
           "후보": 줄, "신호": 신호}
    peers = os.path.join(raw, "peers")
    os.makedirs(peers, exist_ok=True)
    io.open(os.path.join(peers, "서술유사도.json"), "w", encoding="utf-8").write(json.dumps(out, ensure_ascii=False, indent=1))
    cols = ["고유번호", "회사명", "구분", "유사도", "순위", "겹친낱말", "원문", "상태"]
    with io.open(os.path.join(peers, "서술유사도.csv"), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in sorted(줄, key=lambda r: (r["순위"] is None, r["순위"] or 0)):
            w.writerow(r)
    print("후보 %d곳 — 잰 것 %d · 원문 없음 %d · 사업의 내용 못 찾음 %d (선정하지 않는다)"
          % (len(줄), len(잰), sum(1 for r in 줄 if r["상태"] == "원문 없음"),
             sum(1 for r in 줄 if r["상태"] == "사업의 내용 못 찾음")))
    for r in 잰[:10]:
        print("  %2d %-20s %.3f  %s" % (r["순위"], (r["회사명"] or r["고유번호"])[:20], r["유사도"], r["겹친낱말"][:40]))
    if 빈것 and not a.받기:
        print("원문이 빈 후보 %d곳 — 사람 허락 뒤 `python 스크립트/서술유사도.py %s --받기`" % (len(빈것), a.가정))
    print("→ %s" % os.path.join(peers, "서술유사도.json"))
    남은빈 = [r for r in 줄 if r["상태"] == "원문 없음"]
    return 발견 if 남은빈 else 통과


if __name__ == "__main__":
    sys.exit(main())

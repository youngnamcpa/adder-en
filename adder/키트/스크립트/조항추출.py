# -*- coding: utf-8 -*-
"""조항추출 — 대상회사 공시 원문에서 약정 조항 후보(재무약정 · 담보 · 지급보증 · 약정사항 · 장기공급계약 · 판매계약 · 우발부채)를
문단째 뽑고, D 갈래가 외부 제약에 적은 원문 인용이 원문에 글자 그대로 있는지 대조한다 (NLP ③ · 2026-10-21).

    python 스크립트/조항추출.py 가정.json                         # → 가정 곁 _raw/조항후보.json
    python 스크립트/조항추출.py 가정.json --대조                  # _raw/외부제약.json(+ 가정의 `제약` 블록) 의 원문인용 대조 → _raw/조항대조.json
    python 스크립트/조항추출.py 가정.json --대조 다른/외부제약.json
    python 스크립트/조항추출.py 가정.json --설정 조항설정.json

왜 있나
    재무약정(부채비율 유지 · 기한의 이익 상실) · 담보 · 지급보증 · 장기공급계약은 주석 깊숙이 문장으로만 있다. D 갈래가 그 문단을
    찾느라 원문을 처음부터 다시 읽으면 놓치고, 찾았어도 「어디서 읽었는지」가 남지 않으면 나중에 되짚을 수 없다.
    이 도구는 **후보 문단과 그 위치(접수번호 · 파일 · 절 · 문단 번호)만** 낸다. 값을 정하지 않고 외부 제약에 넣지도 않는다 —
    D 갈래가 읽고 판단해 `외부제약작성.py` 로 넣는다(블록 이름은 `조항설정.json` 의 「닿는블록」 — 재무약정 · 담보 · 지급보증 ·
    약정사항은 `재무약정` 블록, 장기공급계약 · 판매계약은 매출 축(B 갈래 참고), 우발부채는 가치 브리지(주당가치 규칙 참고)).
    **원문 인용이 없으면 버린다** — LLM 이 옮겨 적은 조항은 후보일 뿐이다. `--대조` 는 외부 제약 항목의 `원문인용`(선택 칸) ·
    `원문접수`(선택 칸 — 있으면 그 접수번호의 원문에서만 찾는다)가 원문에 공백 정규화 후 글자 그대로 있는지 본다.

읽는 것
    가정 곁 `_raw/**/*.txt` 가운데 이름이 접수번호(14자리)로 시작하는 파일 — `dart_fetch.py` 의 `원문(접수번호, 딱지)` 이
    `_raw/{딱지}/{접수번호}.txt`(본문) · `{접수번호}_{첨부}.txt`(첨부 감사보고서 등)로 남긴다. `_raw/peers/` 는 보지 않는다.
    낱말 목록 · 문턱은 `조항설정.json` 「조항추출」 · 「조항대조」 (결과를 보기 전에 정했다).

내는 것
    `_raw/조항후보.json`  {"형식": "조항추출 1", "만든날", "설정", "입력": {"원문파일": [...]}, "후보": [{"번호", "종류", "닿는블록",
                          "접수번호", "파일", "파일들", "절", "문단", "인용", "인용_잘림", "숫자": [{"글", "종류"}], "낱말"}],
                          "종류별": {종류: 개수}, "신호": [...]}
    `_raw/조항대조.json`  (`--대조`) {"형식": "조항대조 1", ..., "대조": [{"블록", "순번", "이름", "원문인용", "원문접수", "판정", "찾은파일"}],
                          "신호": [...]}
    신호 종류 — 「재무약정 후보 · 블록 빔」(경보) · 「장기공급계약 후보」(참고) · 「원문인용 불일치」(경보) · 「원문인용 없음」(경보)

종료 코드 — 0 통과 · 1 발견(`--대조` 에서 원문에 없는 인용) · 2 입력오류(가정 · 원문 · 외부제약 파일 없음 · JSON 깨짐).
회사 · 업종 이름은 이 도구에 한 글자도 없다.
"""
from __future__ import annotations

import argparse
import datetime
import glob
import io
import json
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:                                            # noqa: BLE001
    pass

여기 = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, 여기)
from 종료코드 import 통과, 발견, 입력오류  # noqa: E402

기본설정 = os.path.join(여기, "조항설정.json")
_접수 = re.compile(r"^(\d{14})")
_미국원문 = re.compile(r"^(10[KQ]_\d{4,6})\.(txt|htm|html)$", re.I)          # sec_fetch 원문 꼴(10K_YYYYMM · 10Q_YYYYMM) — 2026-10-23
_SEC접수 = re.compile(r"^(?:\d{10}-\d{2}-\d{6}|\d{18})$")                    # SEC accession(0000764180-26-000012 · 대시 없는 18자리)
_머리말 = re.compile(r"^\s*(?:[IVXⅠ-Ⅹ]{1,4}\.|\d{1,2}\.(?!\d)|\(\d{1,2}\)|[가-하]\.|[①-⑳]|\d{1,2}\))\s*[^\d\s.,]")
_큰머리말 = re.compile(r"^\s*(?:[IVXⅠ-Ⅹ]{1,4}\.|\d{1,2}\.(?!\d))")


def 설정읽기(p=None):
    return json.load(io.open(p or 기본설정, encoding="utf-8"))


def 정규(s):
    """대조용 공백 정규화 — `&cr;` 를 지우고 모든 공백을 한 칸으로."""
    return re.sub(r"\s+", " ", (s or "").replace("&cr;", " ")).strip()


def 원문파일들(raw):
    """`_raw/**/<접수번호 14자리>*.txt` — `_raw/peers` 아래는 뺀다. 미국 원문(`_raw/10K_YYYYMM` · `10Q_YYYYMM` 의 .txt · .htm — 같은 이름이면 .txt)도
    읽는다(2026-10-23 — 종전에는 국내 원문만 읽어 미국 회사의 재무약정 원문 인용을 대조하지 못했다)."""
    out = []
    for p in sorted(glob.glob(os.path.join(raw, "**", "*.txt"), recursive=True)):
        rel = os.path.relpath(p, raw).replace("\\", "/")
        if rel.split("/")[0] == "peers":
            continue
        if _접수.match(os.path.basename(p)):
            out.append(p)
    미국 = {}
    for p in sorted(glob.glob(os.path.join(raw, "10*_*.*"))):
        m = _미국원문.match(os.path.basename(p))
        if m and (m.group(1) not in 미국 or p.lower().endswith(".txt")):
            미국[m.group(1)] = p
    return out + [미국[k] for k in sorted(미국)]


def 원문표지(p):
    """파일의 접수 표지 — 국내는 접수번호 14자리, 미국은 원문 이름(10K_YYYYMM)."""
    b = os.path.basename(p)
    m = _접수.match(b) or _미국원문.match(b)
    return m.group(1) if m else b


def 원문글(p):
    """원문 글 — .htm · .html 은 문단 · 줄 단위로 벗긴다(블록 태그 → 줄바꿈 · 나머지 태그 지움 · 개체 풀기)."""
    import html as _html                                     # noqa: PLC0415
    글 = io.open(p, encoding="utf-8", errors="replace").read()
    if p.lower().endswith((".htm", ".html")):
        글 = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", 글)
        글 = re.sub(r"(?i)<\s*(?:br|/p|/div|/tr|/li|/h\d|/table)\s*/?>", "\n", 글)
        글 = re.sub(r"<[^>]+>", " ", 글)
        글 = "\n".join(re.sub(r"[ \t\xa0]+", " ", x).strip() for x in _html.unescape(글).split("\n"))
    return 글


def _낱말식(낱말):
    """ASCII 낱말은 글자 경계를 건다(「LTA」 가 다른 영어 낱말 속에 걸리지 않게). 한글은 그대로."""
    if re.fullmatch(r"[A-Za-z\- ]+", 낱말):
        return re.compile(r"(?<![A-Za-z])%s(?![A-Za-z])" % re.escape(낱말))
    return re.compile(re.escape(낱말))


_날짜 = re.compile(r"\d{4}\s*년\s*\d{1,2}\s*월(?:\s*\d{1,2}\s*일)?|\d{4}[.\-/]\d{1,2}[.\-/]\d{1,2}")
_금액 = re.compile(r"(?:(?:USD|US\$|EUR|JPY|CNY|\$)\s*\d[\d,]*(?:\.\d+)?(?:\s*(?:백만|천만|억|천|만|million|billion))?)"
                  r"|(?:\d[\d,]*(?:\.\d+)?\s*(?:조\s*원|억\s*원|백만\s*원|천\s*원|만\s*원|원|백만\s*달러|천\s*달러|달러|"
                  r"백만\s*USD|USD|EUR|JPY|CNY|엔|위안))")
_비율 = re.compile(r"\d[\d,]*(?:\.\d+)?\s*(?:%|퍼센트|배)")
_기간 = re.compile(r"\d[\d,]*(?:\.\d+)?\s*(?:년|개월|일)(?!\s*\d)")


def 숫자뽑기(글):
    """금액 · 비율 · 기간 · 날짜를 원문 조각 그대로 뽑는다(값을 해석하지 않는다)."""
    out, 남 = [], 글
    for 종류, 식 in (("날짜", _날짜), ("금액", _금액), ("비율", _비율), ("기간", _기간)):
        for m in 식.finditer(남):
            out.append({"글": re.sub(r"\s+", " ", m.group(0)).strip(), "종류": 종류})
        남 = 식.sub(" ", 남)
    return out


def 뽑기(파일들, 설정):
    S = 설정["조항추출"]
    종류식 = {k: [(w, _낱말식(w)) for w in v["낱말"]] for k, v in S["종류"].items()}
    함께식 = {k: [[(w, _낱말식(w)) for w in 목록] for 목록 in v.get("함께") or []] for k, v in S["종류"].items()}
    # 2026-10-24 W18 — 종류마다 「제외」 글귀(영문 면책 · 약정 없음 문장)를 지운 뒤 낱말을 댄다(조항설정.json 「제외_뜻」)
    제외식 = {k: (re.compile("|".join(re.escape(x) for x in v["제외"]), re.I) if v.get("제외") else None) for k, v in S["종류"].items()}
    최대, 최소, 머리최대 = S["인용최대글자"], S["문단최소글자"], S["머리말최대글자"]
    묶음 = {}                       # 정규 인용 → 후보
    for p in 파일들:
        접수 = 원문표지(p)
        try:
            글 = 원문글(p)
        except (IOError, OSError, UnicodeDecodeError):
            continue
        큰, 작은 = "", ""
        for i, 줄 in enumerate(글.split("\n")):
            s = 줄.strip()
            if not s:
                continue
            if len(s) <= 머리최대 and _머리말.match(s):
                if _큰머리말.match(s):
                    큰, 작은 = s, ""
                else:
                    작은 = s
                continue
            if len(s) < 최소:
                continue
            걸린 = []
            for 종류, 식들 in 종류식.items():
                sk = 제외식[종류].sub(" ", s) if 제외식[종류] else s
                낱 = [w for w, 식 in 식들 if 식.search(sk)]
                if not 낱 and 함께식[종류]:
                    짝 = [[w for w, 식 in 목록 if 식.search(sk)] for 목록 in 함께식[종류]]
                    if all(짝):
                        낱 = [w for 목록 in 짝 for w in 목록]
                if 낱:
                    걸린.append((종류, 낱))
            if not 걸린:
                continue
            인용 = s
            잘림 = False
            if len(인용) > 최대:
                cut = 인용[:최대]
                k = max(cut.rfind("다."), cut.rfind(". "))
                인용 = cut[:k + 2] if k > 최대 // 3 else cut
                잘림 = True
            키 = 정규(인용)
            if 키 in 묶음:
                c = 묶음[키]
                rel = os.path.basename(p)
                if rel not in c["파일들"]:
                    c["파일들"].append(rel)
                continue
            절 = " › ".join(x for x in (큰, 작은) if x)
            묶음[키] ={"종류": 걸린[0][0], "종류들": [k for k, _ in 걸린], "낱말": sorted({w for _, ws in 걸린 for w in ws}),
                      "닿는블록": S["종류"][걸린[0][0]]["닿는블록"], "접수번호": 접수, "파일": os.path.basename(p),
                      "파일들": [os.path.basename(p)], "절": 절, "문단": i + 1, "인용": 인용, "인용_잘림": 잘림,
                      "숫자": 숫자뽑기(인용)}
    후보 = list(묶음.values())
    for n, c in enumerate(후보, 1):
        c["번호"] = n
    return 후보


def _블록들(제약):
    """외부제약.json 의 `제약` dict · 가정의 `제약` dict → {블록: list}. 블록 밖 키(`_비고`)는 따로."""
    if not isinstance(제약, dict):
        return {}, {}
    블, 비 = {}, {}
    for k, v in 제약.items():
        if k.endswith("_비고"):
            비[k[:-3]] = v
        elif isinstance(v, list):
            블[k] = v
    return 블, 비


def 신호_후보(후보, 외부):
    신호 = []
    재 = [c for c in 후보 if c["닿는블록"] == "재무약정"]
    if 재 and 외부 is not None:
        블, 비 = _블록들(외부.get("제약") if isinstance(외부, dict) else None)
        if not 블.get("재무약정"):
            신호.append({"출처": "조항추출", "종류": "재무약정 후보 · 블록 빔", "대상": "외부제약 재무약정",
                       "값": len(재), "문턱": "후보 1개 이상인데 블록 빔",
                       "글": "원문에 재무약정 · 담보 · 지급보증 · 약정사항 후보 문단이 %d개 있는데 외부 제약 `재무약정` 블록이 비었다%s — "
                             "후보를 읽고 닿는 것은 `외부제약작성.py` 로 원문인용과 함께 넣고, 닿지 않으면 `재무약정_비고` 에 까닭을 적는다"
                             % (len(재), "(비고: %s)" % str(비.get("재무약정"))[:60] if 비.get("재무약정") else ""),
                       "등급": "경보"})
    공 = [c for c in 후보 if "장기공급계약" in c["종류들"] or "판매계약" in c["종류들"]]
    if 공:
        신호.append({"출처": "조항추출", "종류": "장기공급계약 후보", "대상": "매출 축(B 갈래)", "값": len(공), "문턱": "후보 1개 이상",
                   "글": "원문에 장기공급계약 · 판매계약 후보 문단이 %d개 있다(첫째: 문단 %d — %s) — 물량 · 단가 · 기간이 매출 축에 닿는지 "
                         "B 갈래가 보고 닿으면 근거 칸에 접수번호와 인용을 적는다" % (len(공), 공[0]["문단"], 공[0]["인용"][:40]),
                   "등급": "참고"})
    return 신호


_법령꼴 = re.compile(r"법\s*개정|법률|시행령|시행규칙|고시|보도자료|감독규정|규제|법령|\bAct\b|\bRegulation\b|\bRule\b")


def 대조(외부들, 파일들, 설정):
    """외부 제약 항목의 원문인용을 원문과 견준다 → (대조 줄들, 신호, 불일치 수)."""
    원 = {}
    for p in 파일들:
        try:
            원[p] = 정규(원문글(p))
        except (IOError, OSError, UnicodeDecodeError):
            continue
    필수 = set(설정["조항대조"]["원문인용_필수블록"])
    줄, 신호, 틀림 = [], [], 0
    for 출처이름, 제약 in 외부들:
        블, _비 = _블록들(제약)
        for 블록, 항목들 in 블.items():
            for i, it in enumerate(항목들):
                if not isinstance(it, dict):
                    continue
                q = it.get("원문인용")
                접 = str(it.get("원문접수") or "").strip()
                이름 = it.get("이름") or it.get("지표") or ""
                if not q:
                    # 2026-10-24 W10(회차 20261024) — 출처가 법령 · 규제 · 보도자료인 항목은 공시 조항이 아니라 원문인용이 있을 수 없다.
                    # 재무약정 블록에 들었으면 경보가 아니라 「블록 옮김」 참고(법령 블록으로)
                    if 블록 in 필수 and not 접 and _법령꼴.search("%s %s" % (이름, it.get("출처") or "")):
                        줄.append({"출처": 출처이름, "블록": 블록, "순번": i, "이름": 이름, "원문인용": None, "원문접수": None,
                                  "판정": "법령 꼴 — 블록 옮김", "찾은파일": []})
                        신호.append({"출처": "조항추출", "종류": "법령 꼴 항목이 재무약정 블록에", "대상": "%s[%d] %s" % (블록, i, 이름),
                                   "값": None, "문턱": "출처가 법령 · 규제 · 보도자료",
                                   "글": "%s %s 블록 %d번째 항목(%s)은 출처가 법령 · 규제라 공시 원문인용이 있을 수 없다 — 「법령」 블록으로 옮긴다" % (출처이름, 블록, i, 이름 or "이름 없음"),
                                   "등급": "참고"})
                        continue
                    if 블록 in 필수:
                        줄.append({"출처": 출처이름, "블록": 블록, "순번": i, "이름": 이름, "원문인용": None, "원문접수": 접 or None,
                                  "판정": "원문인용 없음", "찾은파일": []})
                        신호.append({"출처": "조항추출", "종류": "원문인용 없음", "대상": "%s[%d] %s" % (블록, i, 이름),
                                   "값": None, "문턱": "%s 블록은 원문인용 필수" % 블록,
                                   "글": "%s %s 블록 %d번째 항목(%s)에 `원문인용` 이 없다 — 조항후보.json 에서 그 문단을 찾아 글자 그대로 옮기고 "
                                         "`원문접수` 를 함께 적는다(원문 인용이 없으면 되짚을 수 없다)" % (출처이름, 블록, i, 이름 or "이름 없음"),
                                   "등급": "경보"})
                    continue
                qn = 정규(q)
                # 접수 표지로 좁힌다 — 국내 접수번호 14자리 · 미국 원문 이름(10K_YYYYMM)이면 그 파일만. SEC accession 은 파일 이름에 없어 미국 원문 전부에서 찾는다
                if 접 and _SEC접수.match(접):
                    후 = [p for p in 원 if _미국원문.match(os.path.basename(p))]
                else:
                    후 = [p for p in 원 if (not 접 or os.path.basename(p).startswith(접))]
                찾은 = [os.path.basename(p) for p in 후 if qn and qn in 원[p]]
                ok = bool(찾은)
                줄.append({"출처": 출처이름, "블록": 블록, "순번": i, "이름": 이름, "원문인용": q, "원문접수": 접 or None,
                          "판정": "일치" if ok else "불일치", "찾은파일": 찾은})
                if not ok:
                    틀림 += 1
                    신호.append({"출처": "조항추출", "종류": "원문인용 불일치", "대상": "%s[%d] %s" % (블록, i, 이름),
                               "값": q[:80], "문턱": "공백 정규화 후 글자 그대로",
                               "글": "%s %s 블록 %d번째 항목의 원문인용이 %s원문에 글자 그대로 없다 — 지어낸 인용이거나 다른 보고서의 문단이다. "
                                     "조항후보.json 의 인용을 그대로 옮긴다" % (출처이름, 블록, i, ("접수 %s " % 접) if 접 else ""),
                               "등급": "경보"})
    return 줄, 신호, 틀림


def main(argv=None):
    ap = argparse.ArgumentParser(allow_abbrev=False, description="약정 조항 후보 추출 · 외부 제약 원문인용 대조")
    ap.add_argument("가정", nargs="?", default=None)
    ap.add_argument("--raw", default=None,
                    help="가정 없이 회차 `_raw` 폴더로 돈다(조사 단계 · D 갈래 — 2026-10-24 W17). 외부 제약은 그 안의 외부제약.json")
    ap.add_argument("--대조", nargs="?", const="", default=None,
                    help="외부 제약 파일(기본 가정 곁 _raw/외부제약.json). 가정 파일의 `제약` 블록도 함께 본다")
    ap.add_argument("--설정", default=None)
    a = ap.parse_args(argv)
    if a.raw:
        # 2026-10-24 W17 — 조사 단계에는 가정이 없다(LS ELECTRIC 조사 — 빈 JSON 을 키트 뿌리에 두고 돌렸다)
        if not os.path.isdir(a.raw):
            print("_raw 폴더가 없다: %s" % a.raw)
            return 입력오류
        raw, 가정 = os.path.abspath(a.raw), {}
    elif not a.가정 or not os.path.exists(a.가정):
        print("가정 파일이 없다: %s — 조사 단계면 `--raw <회차>/_raw`" % a.가정)
        return 입력오류
    try:
        if not a.raw:
            가정 = json.load(io.open(a.가정, encoding="utf-8"))
        설정 = 설정읽기(a.설정)
    except (ValueError, IOError, OSError) as e:
        print("JSON 을 못 읽었다 — %s" % e)
        return 입력오류
    if not a.raw:
        raw = os.path.join(os.path.dirname(os.path.abspath(a.가정)), "_raw")
    파일들 = 원문파일들(raw)
    if not 파일들:
        print("원문이 없다 — %s 아래 접수번호(14자리) 이름의 .txt 도 미국 원문(10K_YYYYMM · 10Q_YYYYMM)도 없다. dart_fetch.py · sec_fetch.py 로 원문을 먼저 받는다" % raw)
        return 입력오류
    오늘 = datetime.date.today().isoformat()
    외부p = os.path.join(raw, "외부제약.json")

    if a.대조 is not None:
        p = a.대조 or 외부p
        외부들 = []
        if os.path.exists(p):
            try:
                외부들.append((os.path.basename(p), (json.load(io.open(p, encoding="utf-8")) or {}).get("제약")))
            except ValueError as e:
                print("외부 제약 JSON 이 깨졌다 — %s" % e)
                return 입력오류
        if isinstance(가정.get("제약"), dict):
            외부들.append(("가정.제약", 가정["제약"]))
        if not 외부들:
            print("외부 제약이 없다 — %s 도 가정의 `제약` 블록도 없다" % p)
            return 입력오류
        줄, 신호, 틀림 = 대조(외부들, 파일들, 설정)
        out = {"형식": "조항대조 1", "만든날": 오늘, "설정": 설정["조항대조"],
               "입력": {"외부제약": [n for n, _ in 외부들], "원문파일": [os.path.relpath(x, raw).replace("\\", "/") for x in 파일들]},
               "대조": 줄, "신호": 신호}
        os.makedirs(raw, exist_ok=True)
        io.open(os.path.join(raw, "조항대조.json"), "w", encoding="utf-8").write(json.dumps(out, ensure_ascii=False, indent=1))
        일치 = sum(1 for x in 줄 if x["판정"] == "일치")
        print("원문인용 대조 %d건 — 일치 %d · 불일치 %d · 원문인용 없음(필수 블록) %d"
              % (len(줄), 일치, 틀림, sum(1 for x in 줄 if x["판정"] == "원문인용 없음")))
        for x in 줄:
            if x["판정"] != "일치":
                print("  %s %s[%d] %s — %s" % (x["판정"], x["블록"], x["순번"], x["이름"], (x["원문인용"] or "")[:50]))
        print("→ %s" % os.path.join(raw, "조항대조.json"))
        return 발견 if 틀림 else 통과

    후보 = 뽑기(파일들, 설정)
    외부 = None
    if os.path.exists(외부p):
        try:
            외부 = json.load(io.open(외부p, encoding="utf-8"))
        except ValueError:
            외부 = None
    elif isinstance(가정.get("제약"), dict):
        외부 = {"제약": 가정["제약"]}
    종류별 = {}
    for c in 후보:
        종류별[c["종류"]] = 종류별.get(c["종류"], 0) + 1
    out = {"형식": "조항추출 1", "만든날": 오늘, "설정": 설정["조항추출"],
           "입력": {"원문파일": [os.path.relpath(x, raw).replace("\\", "/") for x in 파일들],
                  "외부제약": os.path.basename(외부p) if os.path.exists(외부p) else None},
           "후보": 후보, "종류별": 종류별, "신호": 신호_후보(후보, 외부)}
    os.makedirs(raw, exist_ok=True)
    io.open(os.path.join(raw, "조항후보.json"), "w", encoding="utf-8").write(json.dumps(out, ensure_ascii=False, indent=1))
    print("원문 %d개에서 약정 조항 후보 %d개 — %s" % (len(파일들), len(후보), " · ".join("%s %d" % kv for kv in 종류별.items()) or "없음"))
    for s in out["신호"]:
        print("  [%s] %s — %s" % (s["등급"], s["종류"], s["글"][:90]))
    print("→ %s" % os.path.join(raw, "조항후보.json"))
    return 통과


if __name__ == "__main__":
    sys.exit(main())

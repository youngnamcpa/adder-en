# -*- coding: utf-8 -*-
"""DART 공시 뷰어(dart.fss.or.kr)에서 공시 원문 절을 받는다.
OpenDART document.xml 이 점검(status 800)일 때의 우회 경로. 같은 공시 원문이다."""
import io, os, re, sys, time, json, html
import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "_raw")
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
     "Referer": "https://dart.fss.or.kr/dsaf001/main.do"}


def 본문받기(접수번호, tag):
    """뷰어의 `_main.html`(목차 스크립트가 든 뼈대)을 받아 둔다.

    **이것이 없으면 목차를 못 읽는다.** 옛 판은 누가 미리 받아 둔 것을 전제했는데,
    `dart_fetch.원문()` 이 우회로 부를 때는 아무도 안 받아 둬서 **항상 실패했다**
    (한화오션 회차에서 잡혔다). 이제 없으면 스스로 받는다.
    """
    낼곳 = os.path.join(RAW, tag)
    os.makedirs(낼곳, exist_ok=True)
    p = os.path.join(낼곳, "_main.html")
    if os.path.exists(p) and os.path.getsize(p) > 1000:
        return p
    r = requests.get("https://dart.fss.or.kr/dsaf001/main.do",
                     params={"rcpNo": 접수번호}, timeout=40,
                     headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    io.open(p, "w", encoding="utf-8").write(r.text)
    return p


def 목차(tag, 접수번호=None):
    p = os.path.join(RAW, tag, "_main.html")
    if 접수번호 and not (os.path.exists(p) and os.path.getsize(p) > 1000):
        본문받기(접수번호, tag)
    s = io.open(p, encoding="utf-8").read()
    blocks = re.split(r"var node\d+ = \{\};", s)[1:]
    out = []
    for b in blocks:
        d = {}
        for k in ("text", "rcpNo", "dcmNo", "eleId", "offset", "length", "dtd"):
            m = re.search(r"\['%s'\]\s*=\s*\"(.*?)\"" % k, b)
            if m:
                d[k] = m.group(1)
        if d.get("dcmNo") and d.get("text"):
            out.append(d)
    # 중복 제거
    seen, uniq = set(), []
    for d in out:
        key = (d["dcmNo"], d["eleId"], d["offset"])
        if key in seen:
            continue
        seen.add(key)
        uniq.append(d)
    return uniq


def 벗기기(h):
    h = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", h)
    h = re.sub(r"(?i)<br\s*/?>", "\n", h)
    h = re.sub(r"(?i)</t[dh]>", "\t", h)
    h = re.sub(r"(?i)</tr>", "\n", h)
    h = re.sub(r"(?i)</(p|div|table|h\d|title)>", "\n", h)
    h = re.sub(r"(?s)<[^>]+>", " ", h)
    h = html.unescape(h)
    lines = []
    for ln in h.split("\n"):
        cells = [re.sub(r"[ \u00a0]+", " ", c).strip() for c in ln.split("\t")]
        cells = [c for c in cells if c]
        if cells:
            lines.append(" | ".join(cells))
    t = "\n".join(lines)
    return re.sub(r"\n{3,}", "\n\n", t)


def 받기(tag, 골라=None, 접수번호=None):
    """`tag` 는 **폴더 이름(딱지)** 이다. 접수번호를 주면 `_main.html` 을 스스로 받는다."""
    toc = 목차(tag, 접수번호)
    낼곳 = os.path.join(RAW, tag)
    os.makedirs(낼곳, exist_ok=True)
    io.open(os.path.join(낼곳, "_목차.json"), "w", encoding="utf-8").write(
        json.dumps([{"i": i, "text": d["text"], "len": d.get("length")}
                    for i, d in enumerate(toc)], ensure_ascii=False, indent=1))
    낸것 = []
    for i, d in enumerate(toc):
        if 골라 is not None and i not in 골라:
            continue
        if d.get("length", "0") in ("0", ""):
            continue
        p = {"rcpNo": d["rcpNo"], "dcmNo": d["dcmNo"], "eleId": d["eleId"],
             "offset": d["offset"], "length": d["length"], "dtd": d.get("dtd", "dart4.xsd")}
        for 시도 in range(4):
            try:
                r = requests.get("https://dart.fss.or.kr/report/viewer.do",
                                 params=p, headers=H, timeout=60)
                if r.status_code == 200 and len(r.content) > 100:
                    break
            except Exception:
                pass
            time.sleep(1.0 + 시도)
        else:
            sys.stderr.write("실패 %d %s\n" % (i, d["text"][:20]))
            continue
        r.encoding = "utf-8"
        txt = r.text
        if "\ufffd" in txt[:2000] or txt.count("?") > len(txt) / 20:
            r.encoding = "cp949"
            txt = r.text
        nm = "%03d_%s" % (i, re.sub(r"[^0-9A-Za-z가-힣]+", "_", d["text"])[:40])
        io.open(os.path.join(낼곳, nm + ".txt"), "w", encoding="utf-8").write(벗기기(txt))
        낸것.append(nm)
        time.sleep(0.4)
    print("받음 %d개 → %s" % (len(낸것), 낼곳))
    return 낸것


if __name__ == "__main__":
    tag = sys.argv[1]
    골라 = None
    if len(sys.argv) > 2:
        골라 = set(int(x) for x in sys.argv[2].split(","))
    받기(tag, 골라)

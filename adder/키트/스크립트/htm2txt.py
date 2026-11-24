# -*- coding: utf-8 -*-
"""SEC htm 원문을 표 구조가 남는 텍스트로 바꾼다. 뒤 단계는 이 txt 를 읽는다."""
import re, io, os, sys, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "_raw")


def convert(src, dst):
    s = io.open(src, encoding="utf-8", errors="ignore").read()
    s = re.sub(r"(?is)<(script|style|ix:header)[^>]*>.*?</\1>", " ", s)
    # 표 구조 보존
    s = re.sub(r"(?i)</t[dh]>", "\t", s)
    s = re.sub(r"(?i)</tr>", "\n", s)
    s = re.sub(r"(?i)</(table|p|div|br|h\d)>", "\n", s)
    s = re.sub(r"(?i)<br[^>]*/?>", "\n", s)
    s = re.sub(r"(?s)<[^>]+>", "", s)
    s = html.unescape(s)
    s = s.replace(" ", " ").replace("’", "'").replace("—", "-")
    # 셀 정리
    out = []
    for line in s.split("\n"):
        cells = [re.sub(r"[ ]+", " ", c).strip() for c in line.split("\t")]
        cells = [c for c in cells if c not in ("", "$", ")", "(", "%")]
        if not cells:
            continue
        out.append(" | ".join(cells))
    txt = "\n".join(out)
    txt = re.sub(r"\n{3,}", "\n\n", txt)
    io.open(dst, "w", encoding="utf-8").write(txt)
    return len(txt)


def main():
    names = sys.argv[1:]
    if not names:
        import glob as _g
        names = [os.path.splitext(os.path.basename(f))[0]
                 for f in _g.glob(os.path.join(RAW, "*.htm"))]
        if not names:
            print("_raw/ 에 htm 파일이 없습니다. sec_fetch.py 를 먼저 돌리십시오."); raise SystemExit(1)
    for name in names:
        src = os.path.join(RAW, name + ".htm")
        dst = os.path.join(RAW, name + ".txt")
        n = convert(src, dst)
        print("%s -> %s (%d chars)" % (name + ".htm", name + ".txt", n))


if __name__ == "__main__":      # A20 — import 만으로 _raw 에 파일을 쓰지 않는다
    main()

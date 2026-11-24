# -*- coding: utf-8 -*-
"""레터(마크다운)를 읽는 사람에게 보낼 HTML 한 장으로 만든다 (W7b).

    python 스크립트/레터HTML.py 레터.md -o 레터.html [--제목 …] [--견본]

계산하지 않는다 — `레터.py` 가 낸 마크다운의 꼴만 바꾼다. 숫자를 다시 만들지 않으므로 평가 모델 · 레터 · HTML 이 갈릴 자리가 없다.
꼴을 정할 때 지킨 것
  · 본문은 읽는 글, 부록(`# 부록` 아래)은 검증용 자료다. 부록은 조금 더 조여 성격을 눈으로 가르고, 부록마다 접는다(요약줄에 표 · 행 수)
  · 숫자 열은 `tabular-nums` 로 자리를 맞추고 오른쪽에 붙인다. 넘치는 표는 데스크톱에서 본문 폭 밖으로 넓히고(필요할 때만),
    휴대폰에서 글이 많은 좁은 표는 줄마다 카드로 쌓는다. 넘친다는 것은 가장자리 그림자로 알린다
  · 행마다 같은 돈 단위(조 원 · 억 원 · 만 원 · 원)는 셀에서 떼어 첫 칸에 한 번 적는다(마크다운은 그대로 — 게이트가 셀 글을 장부와 맞댄다)
  · 밝은 화면 · 어두운 화면 둘 다에서 선다(어두운 화면에서는 밝게 구운 모션 대신 정적 그림). 인쇄(A4)에서는 스크롤을 풀고 머리행을
    쪽마다 되풀이하며, 쪽 아래에 「회사 · 평가기준일 · 쪽 / 쪽수」 를 찍는다
  · 견본은 머리에 띠를 두르고 쪽마다 「견본」을 찍는다
  · R1b — 그림 표지(`<!-- 그림:길 · 자 · 신호 · 폭포 · 띠 … -->`) 뒤의 굵은 제목과 표를 `레터그림` 으로 그린다(표는 「그림의 숫자」로 접힌다 —
    띠는 첫 화면의 요약 숫자라 접지 않는다).
    절 머리에 바로가기 이름(「N. …」 → #sN · 「3분 레터」 → #삼분 · 「본편」 · 「부록」)을 달고, 링크만 든 목록은 목차로 꾸민다.
    본문의 「N막」 · 「N절」 · 「부록 X」 · 「3분 레터」 는 그 자리가 문서에 있을 때만 링크로 잇는다. 날짜는 줄 끝에서 쪼개지 않는다.
    `삼분=True` 는 3분 레터만 떼어 낸 파일(휴대폰 폭 · A4 두 쪽 — 참조는 본편 파일로 잇는다)
외부에서 읽는 것은 Google Fonts 의 글꼴뿐이다(없으면 시스템 글꼴로 선다).
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys

여기 = os.path.dirname(os.path.abspath(__file__))
if 여기 not in sys.path:
    sys.path.insert(0, 여기)
import 레터그림  # noqa: E402

# CSS 안에 `%` 가 많아 `%` 포맷을 쓰지 않는다 — 자리표시자를 바꿔 넣는다.
머리 = """<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{제목}}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+KR:wght@300;400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
/* 레터 v27 7단계 — 화면 시안 3C: 옅은 회색 바탕 위의 흰 종이 · IBM Plex Sans KR(숫자만 든 표 칸은 IBM Plex Mono) · 청색 강조.
   색 하나에 뜻 하나 — 청색: 가정 값 · 지금 보는 자리 · 보라 · 청록: 그림의 계열 · 빨강: 범위 밖 · 회색: 실적 · 회사가 공시한 값 */
:root{
  --canvas:#F4F4F4; --paper:#FFFFFF; --paper-2:#F4F4F4; --ink:#161616; --ink-2:#393939;
  --muted:#6F6F6F; --rule:#E0E0E0; --rule-2:#A8A8A8;
  --accent:#0F62FE; --accent-soft:#EDF5FF; --flag:#DA1E28; --flag-soft:#FFF1F1;
  --band:#E0E0E0; --on-band:#161616; --est:#F4F4F4; --assume:#0043CE;
  --s1:#6929C4; --s1-soft:#E8DAFF; --s2:#009D9A; --ctx:#8D8D8D;
  --shadow:rgba(22,22,22,.18);
  --measure:46rem; --sheet:58.75rem;
  --sans:"IBM Plex Sans KR","IBM Plex Sans","Malgun Gothic","Apple SD Gothic Neo",system-ui,sans-serif;
  --mono:"IBM Plex Mono","IBM Plex Sans KR",ui-monospace,monospace;
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --canvas:#161616; --paper:#262626; --paper-2:#2E2E2E; --ink:#F4F4F4; --ink-2:#C6C6C6;
    --muted:#A8A8A8; --rule:#393939; --rule-2:#6F6F6F;
    --accent:#78A9FF; --accent-soft:#1C2A44; --flag:#FF8389; --flag-soft:#3A1F21;
    --band:#393939; --on-band:#F4F4F4; --est:#2E2E2E; --assume:#A6C8FF;
    --s1:#A56EFF; --s1-soft:#491D8B; --s2:#009D9A; --ctx:#8D8D8D;
    --shadow:rgba(244,244,244,.18);
  }
}
:root[data-theme="dark"]{
  --canvas:#161616; --paper:#262626; --paper-2:#2E2E2E; --ink:#F4F4F4; --ink-2:#C6C6C6;
  --muted:#A8A8A8; --rule:#393939; --rule-2:#6F6F6F;
  --accent:#78A9FF; --accent-soft:#1C2A44; --flag:#FF8389; --flag-soft:#3A1F21;
  --band:#393939; --on-band:#F4F4F4; --est:#2E2E2E; --assume:#A6C8FF;
  --s1:#A56EFF; --s1-soft:#491D8B; --s2:#009D9A; --ctx:#8D8D8D;
  --shadow:rgba(244,244,244,.18);
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{
  margin:0; background:var(--canvas); color:var(--ink);
  font-family:var(--sans); font-size:15px; line-height:1.72; word-break:keep-all; overflow-wrap:break-word;
  font-variant-numeric:tabular-nums;
}
.wrap{max-width:var(--sheet); margin:28px auto; padding:40px 48px 48px; background:var(--paper)}
main{display:block}
h1,h2,h3{font-family:var(--sans); text-wrap:balance; margin:0}
h1{font-size:42px; line-height:1.2; font-weight:300; letter-spacing:0}
h2{font-size:26px; line-height:1.35; font-weight:400; margin:44px 0 6px; padding-top:14px; border-top:1px solid var(--ink)}
h3{font-size:17px; line-height:1.5; font-weight:600; margin:30px 0 4px; color:var(--ink)}
p,ul,ol,blockquote{max-width:var(--measure)}
p{margin:10px 0}
ul{margin:10px 0; padding-left:1.2rem}
li{margin:.3rem 0}
strong{font-weight:600}
em{font-style:normal; color:var(--muted); font-size:.93em}
code{font-family:var(--mono); font-size:.9em}
hr{border:0; border-top:1px solid var(--rule); margin:2.4rem 0}
.nb{white-space:nowrap}
blockquote{margin:14px 0; padding:2px 0 2px 16px; border-left:2px solid var(--rule-2); color:var(--ink-2)}
blockquote p{margin:.3rem 0}
blockquote.flag{border-left-color:var(--flag)}
div.sample{margin:0 0 2rem; padding:.6rem 0; border-top:1px solid var(--flag); border-bottom:1px solid var(--flag); color:var(--flag);
  font-size:.86rem; letter-spacing:.02em}
.scroll{overflow-x:auto; margin:16px 0; position:relative}
.scroll.more-right{background:radial-gradient(farthest-side at 100% 50%, var(--shadow), transparent) right / .8rem 100% no-repeat}
table{border-collapse:collapse; width:100%; font-size:12.5px; line-height:1.45; font-variant-numeric:tabular-nums}
th,td{padding:5px 8px; border-bottom:1px solid var(--rule); text-align:left; white-space:nowrap; vertical-align:top}
td.text,th.text{white-space:normal; min-width:14rem}
thead th{background:var(--band); color:var(--on-band); font-weight:600; font-size:12px; border-bottom:0}
td.num,th.num{text-align:right}
td.mono{font-family:var(--mono); font-size:.94em}
td.unit{color:var(--muted); font-size:.92em}
tbody tr:last-child td{border-bottom:1px solid var(--rule-2)}
td.k{color:var(--muted); font-size:11.5px}
tr.as td.k{color:var(--assume); font-weight:600}
tr.as td.e{color:var(--assume)}
tr.tot td{font-weight:600; border-top:1px solid var(--rule-2); border-bottom:1px solid var(--rule-2)}
td.e,tr.er td:not(:first-child){background:var(--est)}
td.b,th.b{border-left:1px solid var(--rule-2)}
.vd{font-weight:600; white-space:nowrap}
.vd.out{color:var(--flag)} .vd.taken,.vd.na{color:var(--muted)}
table.many{font-size:11.5px}
table.stick tr > :first-child{position:sticky; left:0; z-index:1; background:var(--paper)}
table.stick thead tr > :first-child{background:var(--band)}
.scroll.scrolled table.stick tr > :first-child{box-shadow:6px 0 6px -5px var(--shadow)}
@media (min-width:900px){
  .scroll.wide th:not(.num), .scroll.wide td:not(.num){white-space:normal}
  .scroll.wide td.text, .scroll.wide th.text{min-width:8rem}
  .scroll.wide td.nw, .scroll.wide th.nw{white-space:nowrap}
}
.lede{color:var(--muted); font-size:13px; margin-top:6px}
.part{margin:56px 0 0; padding:14px 0 0; border-top:1px solid var(--ink)}
.part h1{font-size:26px; font-weight:400}
#appendix{--measure:48rem}
#appendix h2{font-size:20px}
#appendix h3{font-size:15px}
#appendix p{font-size:14px; margin:8px 0}
#appendix table{font-size:11.5px}
details.app{margin:18px 0 0; border-top:1px solid var(--rule)}
details.app > summary{cursor:pointer; list-style:none; padding:.9rem 0 .5rem; display:flex; flex-wrap:wrap; align-items:baseline; gap:.2rem .9rem}
details.app > summary::-webkit-details-marker{display:none}
details.app > summary::before{content:"+"; font:500 1rem/1 var(--mono); color:var(--muted); width:1rem}
details.app[open] > summary::before{content:"−"}
details.app > summary h2{margin:0; padding:0; border:0; display:inline}
details.app > summary .app-meta{font-size:12px; color:var(--muted)}
a{color:var(--accent)}
:focus-visible{outline:2px solid var(--accent); outline-offset:2px}
.skip{position:absolute; left:.5rem; top:-3rem; z-index:20; background:var(--paper); color:var(--accent); padding:.4rem .8rem;
  border:1px solid var(--accent); font-size:.9rem}
.skip:focus{top:.5rem}
ul.toc{list-style:none; padding:0; margin:1rem 0 2rem; columns:2 15rem; column-gap:2rem; font-size:14px; max-width:none}
ul.toc li{margin:.15rem 0; break-inside:avoid}
ul.toc a{text-decoration:none}
h2[id],h1[id],div[id],details[id]{scroll-margin-top:1rem}
#삼분 + p{color:var(--muted)}
.three h3{color:var(--ink); font-size:17px; margin-top:26px}
.progress{position:fixed; left:0; top:0; height:2px; width:100%; z-index:15; pointer-events:none}
.progress span{display:block; height:100%; width:100%; background:var(--accent); transform-origin:0 50%; transform:scaleX(0)}
.to-top{position:fixed; right:1rem; bottom:1rem; z-index:15; font-size:12px; text-decoration:none; color:var(--ink-2); background:var(--paper);
  border:1px solid var(--rule-2); padding:.35rem .7rem; opacity:0; pointer-events:none; transition:opacity .2s}
.to-top.on{opacity:1; pointer-events:auto}
nav.side-toc{display:none}
@media (min-width:1440px){
  nav.side-toc{display:block; position:fixed; top:3.5rem; left:1rem; width:calc(50vw - var(--sheet) / 2 - 2rem);
    max-height:calc(100vh - 5rem); overflow:auto; font-size:12px; line-height:1.45; z-index:5}
  nav.side-toc ol{list-style:none; margin:0; padding:0}
  nav.side-toc li{margin:0}
  nav.side-toc a{display:block; padding:.18rem .5rem; color:var(--muted); text-decoration:none; border-left:2px solid transparent}
  nav.side-toc li.toc-part > a{color:var(--ink-2); font-weight:600; margin-top:.6rem}
  nav.side-toc a:hover{color:var(--ink)}
  nav.side-toc a[aria-current="true"]{color:var(--ink); border-left-color:var(--accent); font-weight:600}
}
@media (max-width:940px){
  body{background:var(--paper)} .wrap{margin:0; padding:24px 16px 40px}
  h1{font-size:32px}
}
@media (max-width:640px){
  body{font-size:15px} h2{font-size:22px}
  table.stick tr > :first-child{white-space:normal; min-width:6rem; max-width:9rem}
  table.cards, table.cards tbody, table.cards tr{display:block; width:100%}
  table.cards thead{position:absolute; width:1px; height:1px; overflow:hidden; clip-path:inset(50%); white-space:nowrap}
  table.cards tr{padding:.55rem .25rem; border-bottom:1px solid var(--rule)}
  table.cards tbody tr:last-child{border-bottom:0}
  table.cards td{display:grid; grid-template-columns:minmax(5rem,32%) 1fr; gap:.7rem; border:0; padding:.12rem .45rem;
    white-space:normal; min-width:0; text-align:left}
  table.cards td::before{content:attr(data-label); color:var(--muted); font-size:.74rem; padding-top:.1rem}
  table.cards td:first-child{display:block; font-weight:600; color:var(--ink); padding-bottom:.25rem}
  table.cards td:first-child::before{content:none}
  table.cards td.empty{display:none}
}
@media print{
  :root, :root:not([data-theme="light"]), :root[data-theme="dark"]{
    --canvas:#FFFFFF; --paper:#FFFFFF; --paper-2:#F4F4F4; --ink:#161616; --ink-2:#393939; --muted:#6F6F6F; --rule:#E0E0E0; --rule-2:#A8A8A8;
    --accent:#0F62FE; --accent-soft:#EDF5FF; --flag:#DA1E28; --flag-soft:#FFF1F1;
    --band:#E0E0E0; --on-band:#161616; --est:#F4F4F4; --assume:#0043CE;
    --s1:#6929C4; --s1-soft:#E8DAFF; --s2:#009D9A; --ctx:#8D8D8D;
    --vz-ctx:#8D8D8D; --vz-grid:#E8E8E8; --vz-c2:#1192E8; --vz-c4:#9F1853; --vz-c5:#6F6F6F; --vz-c6:#B28600; --viz-warn:#B7791F}
  @page{size:A4; margin:14mm 15mm 16mm}
  body{background:#fff; color:#000; font-size:9.5pt}
  .wrap{max-width:none; margin:0; padding:0}
  .skip, .progress, .to-top, nav.side-toc{display:none !important}
  h2,h3{break-after:avoid}
  .scroll{overflow:visible; background:none !important}
  th,td{white-space:normal; word-break:keep-all; overflow-wrap:break-word}
  td.num,th.num,td.nw,th.nw{white-space:nowrap}
  td.text,th.text{min-width:0}
  table{max-width:100%; font-size:8pt}
  td.num,th.num{white-space:normal; word-break:keep-all}      /* 2026-10-16 — 가정 표의 「2026년 하반기 0.0% · 2027년 51.4%」 따위가 쪽 밖으로 잘리지 않게(숫자 하나는 그대로 한 줄) */
  table.many{font-size:7.5pt} table.many th, table.many td{padding:.2rem .3rem}
  table.stick tr > :first-child{position:static; box-shadow:none !important}
  table{break-inside:auto} tr{break-inside:avoid} thead{display:table-header-group}
  thead th, td.e, tr.er td, tr.tot td{-webkit-print-color-adjust:exact; print-color-adjust:exact}
  .part{break-before:page}
  ul.toc{columns:2}
  a{color:inherit; text-decoration:none}
  details.app{border-top:0}
  details.app > summary::before, details.app > summary .app-meta{display:none}
  details.app::details-content{content-visibility:visible; display:block}
  .viz-fig details{display:none} .viz-fig .print-only{display:block}
  .print-only .scroll{margin:.2rem 0}
  .print-only table{table-layout:fixed; width:100%; font-size:7pt; line-height:1.15}
  .print-only thead th{font-size:6.5pt}
  .print-only th,.print-only td{padding:.05rem .2rem; white-space:normal; overflow-wrap:anywhere; word-break:normal}
  .print-only td.num,.print-only th.num{white-space:normal}
  .print-only th:first-child,.print-only td:first-child{width:30%}
  .viz-fig.has-print{display:grid; grid-template-columns:minmax(0,54%) minmax(0,1fr); column-gap:4mm; align-items:start}
  .viz-fig.has-print > figcaption{grid-column:1 / -1}
  .viz-fig.has-print > svg.viz{grid-column:1; max-height:62mm}
  .viz-fig.has-print > .print-only{grid-column:2; grid-row:2 / span 2}
  .sig-key-col{white-space:nowrap}
  p,ul,ol,blockquote{max-width:none}
}
/* 추정 단계 표시 — 블록 차례 한 줄 · 지금 블록만 청색 윗선과 굵은 글자(시안 3C) */
ol.steps{display:flex; flex-wrap:wrap; gap:0 4px; list-style:none; padding:0; margin:4px 0 14px; font-size:11.5px; line-height:1.3; max-width:none}
ol.steps li{flex:1 1 0; min-width:4.6rem; margin:0; padding:6px 6px 2px; border-top:2px solid var(--rule); color:var(--muted); white-space:nowrap}
ol.steps li.cur{border-top-color:var(--accent); color:var(--ink); font-weight:600}
ol.steps a{color:inherit; text-decoration:none}
@media (max-width:640px){ ol.steps li{flex:0 0 calc(25% - 3px); min-width:0} }
@media print{ ol.steps{break-after:avoid} ol.steps li.cur{-webkit-print-color-adjust:exact; print-color-adjust:exact} }
/* 「가정과 결과」 표의 실적 범위 칸 — 회색 띠(실적 범위) · 점(마지막 예측 해 · 범위 밖이면 빨강) · 판정 낱말 */
.rstrip{display:inline-flex; align-items:center; gap:6px; white-space:nowrap}
.rstrip svg.rs{flex:none} .rs .rs-ax{stroke:var(--rule-2); stroke-width:1} .rs .rs-band{fill:var(--ctx); opacity:.35}
.rs .rs-dot{fill:var(--s1); stroke:var(--paper); stroke-width:1.2} .rs .rs-dot.out{fill:var(--flag)}
.rstrip .rs-txt{font-family:var(--mono); font-size:.92em; color:var(--muted)}
.rstrip .vd.in{color:var(--muted); font-weight:400}
.rnd .rs-txt{font-family:var(--mono); font-size:.92em; color:var(--muted)} .rnd .rnd-why{color:var(--muted); font-size:.92em}
@media print{ .rs .rs-band, .rs .rs-dot{-webkit-print-color-adjust:exact; print-color-adjust:exact} }
/* 그림 · 표 제목 — 위에 진한 괘선 한 줄(시안 3C) */
.wrap .viz-fig > figcaption{border-top:1px solid var(--ink); padding-top:6px; font-size:13.5px; line-height:1.5; color:var(--ink-2)}
.wrap .viz-fig > figcaption strong{font-weight:600; color:var(--ink)}
@media (max-width:940px){ .scroll.wide td:first-child, .scroll.wide th:first-child{min-width:7.5rem} }
@media (min-width:900px){ .scroll.wide td:first-child, .scroll.wide th:first-child{min-width:10rem} }
.print-only{display:none}
</style>
</head>
"""


def 이스케이프(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def 인라인(s):
    """굵게 · 기울임 · 코드 · 링크(문서 안 「#…」 과 같은 폴더의 「….html」 만 — R1b)를 옮긴다."""
    s = 이스케이프(s)
    s = re.sub(r"\[([^\]]+)\]\((#[^)\s]+|[^)\s/:#]+\.html(?:#[^)\s]+)?)\)", r'<a href="\2">\1</a>', s)     # 통독 v3 — 「….html#막」 도
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\*\w])\*([^*\n]+)\*(?!\*)", r"<em>\1</em>", s)
    return s.replace("**", "")


def 숫자칸(t):
    t = re.sub(r"<[^>]+>", "", t).replace("*", "").strip()
    if not t or t in ("—", "-"):
        return True
    m = re.match(r"^[\(\-−+±]?[\d,.]+", t)
    if not m:
        return False
    # 통독 v4 — 숫자로 시작해도 뒤가 문장이면(「2030년이 오기 전에 …」) 숫자 칸이 아니다. 단위 · 기호를 걷고 두 글자 넘게 남으면 글
    남 = re.sub(r"[\d,.\s%~·()\-−+±×/=:]|조|억|만|천|원|배|주|년|월|개|일|건|달러|bp|pt|x", "", t[m.end():])
    return len(남) <= 2


def _맨글(c):
    """셀의 마크다운을 걷어 낸 글(카드의 칸 이름 · 길이 재기)."""
    return re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", re.sub(r"[*`]", "", "%s" % c)).strip()


돈단위 = ("조 원", "억 원", "만 원", "원")                  # 긴 것부터 — 「조 원」 을 「원」 으로 읽지 않는다


def _셀단위(c):
    """숫자 셀이 끝나는 돈 단위(없으면 None). 「134만 원」 → 「만 원」 · 「**70만 원**」 → 「만 원」 · 「−9.7만 원」 → 「만 원」."""
    t = _맨글(c)
    if not t or t in ("—", "-") or not 숫자칸(t) or "%" in t:
        return None
    for 단 in 돈단위:
        if t.endswith(단) and re.match(r"^[\(\-−+±]?[\d,.]+\s*$", t[:-len(단)]):
            return 단
    return None


def 단위올리기(행들):
    """행마다 — 첫 칸 밖의 숫자 셀이 모두 같은 돈 단위로 끝나면(빈 칸 · 「—」 은 건너뜀, 다른 글이 하나라도 있으면 그 행은 그대로)
    단위를 셀에서 떼어 첫 칸 끝에 「 (조 원)」 으로 한 번 적는다(통독 v4 중-7). 마크다운은 그대로 둔다 — HTML 표에서만."""
    낸 = []
    for r in 행들:
        단들 = set()
        된다 = len(r) > 1
        for c in r[1:]:
            t = _맨글(c)
            if not t or t in ("—", "-"):
                continue
            단 = _셀단위(c)
            if 단 is None:
                된다 = False
                break
            단들.add(단)
        if not 된다 or len(단들) != 1:
            낸.append(r)
            continue
        단 = 단들.pop()
        새 = [r[0] if _맨글(r[0]).replace(" ", " ").endswith("(%s)" % 단) else "%s (%s)" % (r[0], 단.replace(" ", " "))]     # 단위 안은 줄을 바꾸지 않는다
        for c in r[1:]:
            새.append(re.sub(r"\s*%s(\**)\s*$" % re.escape(단), r"\1", c) if _셀단위(c) else c)
        낸.append(새)
    return 낸


_구분꼴 = {"가정": "as", "결과": "", "합계": "tot", "밑": "", "규칙": ""}     # 「가정과 결과」 표의 구분 칸 → 줄의 꼴(가정 값은 파란 글자 · 합계는 굵게)
_판정꼴 = {"범위 안": "in", "범위 밖": "out", "가정에 쓴 값": "taken", "확인하지 못함": "na"}
_판정짧은꼴 = {"안": "in", "밖": "out"}                                       # 머리가 「판정」 인 칸에서만
_고정폭꼴 = re.compile(r"^[−\-+±]?(?:[\d,]*\.)?\d+(?:%p|%|배|x|bp)?$")       # 숫자만 든 칸(단위가 붙는 돈 · 낱말은 고정폭을 쓰지 않는다)


def _열지위(머):
    """표 머리 → 「a」(실적 열) · 「e」(추정 · 예측 · 영구 열) · None. 기간을 가리키는 머리만 가른다(「추정 방법」 따위 글 열은 None)."""
    t = _맨글(머)
    if not re.search(r"\d{4}|\d{2}[AFE]|예측기간|영구기간|^영구|년~|~$", t):
        return None
    if re.search(r"추정|예측|영구|\d[FE]|[FE]$|~$", t):
        return "e"
    if re.search(r"실적|\d{2,4}\s?A|A$", t):
        return "a"
    return None


def _표꼴(머리줄, 행들):
    """레터 v27 7단계(시안 3C) — 표의 뜻을 꼴로: 구분 칸(가정 · 결과 · 합계)의 열 · 열마다 지위(실적 · 추정) · 실적과 추정의 경계 열 ·
    판정 열 · 줄 머리가 기간인 표 → dict. 마크다운은 그대로다(게이트는 마크다운을 본다)."""
    n = len(머리줄)
    구분 = next((i for i, c in enumerate(머리줄) if _맨글(c) == "구분"
               and all(_맨글(r[i]) in _구분꼴 or not _맨글(r[i]) for r in 행들 if i < len(r))
               and any(_맨글(r[i]) == "가정" for r in 행들 if i < len(r))), None)
    지위 = [None] + [_열지위(c) for c in 머리줄[1:]]
    e들 = [i for i in range(n) if 지위[i] == "e"]
    경계 = next((i for i in e들 if any(지위[j] == "a" for j in range(i))), None) if e들 else None
    판정 = {i for i, c in enumerate(머리줄) if _맨글(c) in ("판정", "대조 판정")}
    범위 = {i for i, c in enumerate(머리줄) if _맨글(c) == "실적 범위"}
    줄머리기간 = bool(n and re.search(r"회계연도|연도|기간", _맨글(머리줄[0])))
    return {"구분": 구분, "지위": 지위, "경계": 경계, "판정": 판정, "범위": 범위, "줄머리기간": 줄머리기간}


_범위칸꼴 = re.compile(r"^\s*([−\-+]?[\d,]*\.?\d+)\s*(%p|%|배)?\s*~\s*([−\-+]?[\d,]*\.?\d+)\s*(%p|%|배)?\s*·\s*끝\s*([−\-+]?[\d,]*\.?\d+)\s*(%p|%|배)?\s*·\s*범위\s*(안|밖)\s*$")


_정의다름칸꼴 = re.compile(r"^\s*([−\-+]?[\d,]*\.?\d+\s*(?:%p|%|배)?)\s*~\s*([−\-+]?[\d,]*\.?\d+\s*(?:%p|%|배)?)\s*·\s*정의 다름\s*(?:—\s*(.*?))?\s*$")


def _수(s):
    return float(s.replace(",", "").replace("−", "-"))


def _정의다름칸(글):
    """1.1.19 — 실적 범위 칸의 판정이 「정의 다름」(`레터추정표._범위칸` — 「최저 ~ 최고 · 정의 다름 — 까닭」)이면 띠를 그리지 않는다:
    실적 범위 글 · 판정 낱말 「정의 다름」 · 까닭 글(줄을 바꿀 수 있게 nowrap 을 걸지 않는다). 읽지 못하면 None(글 그대로)."""
    m = _정의다름칸꼴.match(_맨글(글))
    if not m:
        return None
    lo, hi = m.group(1).replace(" ", ""), m.group(2).replace(" ", "")
    범 = lo if lo == hi else "%s~%s" % (lo, hi)
    까 = (m.group(3) or "").strip()
    return ('<span class="rnd"><span class="rs-txt">%s</span> <span class="vd na">정의 다름</span>%s</span>'
            % (이스케이프(범), (' <span class="rnd-why">— %s</span>' % 이스케이프(까)) if 까 else ""))


def _범위띠칸(글):
    """레터 v27 7단계(디자인 결정 2) — 「가정과 결과」 표의 「실적 범위」 칸(「최저 ~ 최고 · 끝 값 · 범위 안/밖」)을 띠 그래프로: 실적 범위는 회색 띠,
    마지막 예측 해의 값은 점(범위 밖이면 빨강), 그 옆에 범위 글과 판정 낱말. 읽지 못하면 None(글 그대로)."""
    m = _범위칸꼴.match(_맨글(글))
    if not m:
        return None
    lo, hi, v = _수(m.group(1)), _수(m.group(3)), _수(m.group(5))
    단 = m.group(2) or m.group(4) or m.group(6) or ""
    a, z = min(lo, hi, v), max(lo, hi, v)
    if z - a < 1e-12:
        a, z = a - 1, z + 1
    여 = (z - a) * 0.08
    a, z = a - 여, z + 여
    W, H = 84.0, 12.0
    x = lambda q: 2 + (q - a) / (z - a) * (W - 4)
    밖 = m.group(7) == "밖"
    svg = ('<svg class="rs" width="%d" height="%d" viewBox="0 0 %d %d" aria-hidden="true"><line class="rs-ax" x1="2" x2="%.1f" y1="6" y2="6"/>'
           '<rect class="rs-band" x="%.1f" y="2" width="%.1f" height="8"/><circle class="rs-dot%s" cx="%.1f" cy="6" r="3.6"/></svg>') % (
        W, H, W, H, W - 2, x(min(lo, hi)), max(1.5, abs(x(hi) - x(lo))), " out" if 밖 else "", x(v))
    범 = ("%s%s" % (m.group(1), 단)) if abs(hi - lo) < 1e-12 else "%s~%s%s" % (m.group(1), m.group(3), 단)     # 실적이 한 해면 값 하나
    return ('<span class="rstrip" title="%s">%s<span class="rs-txt">%s · 끝 %s%s</span> <span class="vd %s">범위 %s</span></span>'
            % (이스케이프(_맨글(글)), svg, 이스케이프(범), 이스케이프(m.group(5)), 이스케이프(단), "out" if 밖 else "in", m.group(7)))


def _판정칸(글, 판정열):
    """판정 낱말 넷(범위 안 · 범위 밖 · 가정에 쓴 값 · 확인하지 못함 — 머리가 판정인 칸은 안 · 밖도)을 표시로 감싼다. 뜻은 낱말이 싣고 색은 덧붙인다."""
    t = _맨글(글)
    꼴 = _판정꼴.get(t) or (_판정짧은꼴.get(t) if 판정열 else None)
    return ('<span class="vd %s">%s</span>' % (꼴, 인라인(글))) if 꼴 else None


def _표HTML(머리줄, 정렬줄, 행들, 단위=True, 전치=False):
    오른쪽 = set(i for i, c in enumerate(정렬줄) if c.endswith(":"))
    글칸 = set()
    for i in range(len(머리줄)):
        칸들 = [_맨글(r[i]) for r in 행들 if i < len(r)]
        if i and 칸들 and all(숫자칸(c) for c in 칸들):
            오른쪽.add(i)
        if i not in 오른쪽 and 칸들 and (max(len(c) for c in 칸들) >= 22 or any(c.count(" ") >= 4 for c in 칸들)):
            글칸.add(i)                                   # 통독 v4 상-2 — 문장이 드는 열은 줄을 바꾼다
    짧은칸 = set(i for i in range(len(머리줄)) if i not in 글칸 and i not in 오른쪽
              and all(len(_맨글(r[i])) <= 6 for r in 행들 if i < len(r)))      # 「값 ↑↓」 같은 짧은 칸은 쪼개지 않는다
    if 단위:
        행들 = 단위올리기(행들)
    n = len(머리줄)
    갈 = []
    카드 = (n <= 6 and bool(글칸) or len(글칸) * 2 >= n) and not 전치       # 글이 많은 표 — 휴대폰에서 줄마다 카드
    if 카드:
        갈.append("cards")                                # 휴대폰에서 줄마다 카드
    if n >= 3 and 0 not in 글칸 and not 카드:
        갈.append("stick")                                # 첫 열 고정(넘칠 때)
    if n >= 9:
        갈.append("many")

    표꼴 = _표꼴(머리줄, 행들)

    def 꼴들(i, 머리=False):
        c = ["num"] if i in 오른쪽 else (["text"] if i in 글칸 else (["nw"] if i in 짧은칸 else []))
        if i < len(표꼴["지위"]) and 표꼴["지위"][i] == "e" and not 머리:
            c.append("e")                                 # 시안 3C — 추정 열은 옅은 바탕
        if i == 표꼴["경계"]:
            c.append("b")                                 # 실적과 추정 사이 세로줄
        if i == 표꼴["구분"] and not 머리:
            c.append("k")
        return c

    def 꼴(c):
        return (' class="%s"' % " ".join(c)) if c else ""
    낸다 = ['<div class="scroll"><table%s>' % ((' class="%s"' % " ".join(갈)) if 갈 else ""), "<thead><tr>"]
    for i, c in enumerate(머리줄):
        낸다.append("<th%s>%s</th>" % (꼴(꼴들(i, 머리=True)), 인라인(c)))
    낸다.append("</tr></thead><tbody>")
    for r in 행들:
        칸 = []
        줄꼴 = []
        if 표꼴["구분"] is not None and 표꼴["구분"] < len(r):
            g = _구분꼴.get(_맨글(r[표꼴["구분"]]), "")
            if g:
                줄꼴.append(g)
        if 표꼴["줄머리기간"] and r and re.search(r"추정|영구", _맨글(r[0])) and "실적" not in _맨글(r[0]):
            줄꼴.append("er")                                  # 줄 머리가 기간인 표의 추정 줄(연도별 손익 요약 따위)
        for i, c in enumerate(r):
            덧 = ""
            if 카드 and i < n:
                덧 = ' data-label="%s"' % 이스케이프(_맨글(머리줄[i])).replace('"', "&quot;")
                if _맨글(c) in ("", "—", "-") and i:
                    덧 += ' data-empty="1"'
            cs = 꼴들(i)
            if i and _고정폭꼴.match(_맨글(c).replace(" ", "")):
                cs.append("mono")                             # 숫자만 든 칸은 고정폭(단위가 붙는 값은 비례 글꼴 그대로)
            if 'data-empty' in 덧:
                cs = ["empty"] + cs
            판 = ((_범위띠칸(c) or _정의다름칸(c)) if i in 표꼴["범위"] else None) or (_판정칸(c, i in 표꼴["판정"]) if i else None)
            안 = 판 or 인라인(c)
            칸.append("<td%s%s>%s</td>" % (꼴(cs), 덧, ('<span class="cv">%s</span>' % 안) if 카드 else 안))
        낸다.append("<tr%s>" % 꼴(줄꼴) + "".join(칸) + "</tr>")
    낸다.append("</tbody></table></div>")
    return "".join(낸다)


def _표나누기(줄들):
    머리줄 = [c.strip() for c in 줄들[0].strip().strip("|").split("|")]
    정렬줄 = [c.strip() for c in 줄들[1].strip().strip("|").split("|")]
    행들 = [[c.strip() for c in l.strip().strip("|").split("|")] for l in 줄들[2:]]
    return 머리줄, 정렬줄, 행들


def 표만들기(줄들, 단위=True):
    """마크다운 표 줄 → HTML 표(넘치면 가로로 흐르는 상자 안)."""
    머리줄, 정렬줄, 행들 = _표나누기(줄들)
    return _표HTML(머리줄, 정렬줄, 행들, 단위=단위)


def 전치표만들기(줄들):
    """열이 많은 표를 돌려 세운다(인쇄용 — 연도가 행으로 간다). 첫 칸 머리는 그대로, 원래 첫 열의 이름이 새 머리가 된다."""
    머리줄, _정렬, 행들 = _표나누기(줄들)
    새머리 = [머리줄[0]] + [r[0] if r else "" for r in 행들]
    새행 = [[머리줄[j]] + [r[j] if j < len(r) else "" for r in 행들] for j in range(1, len(머리줄))]
    return _표HTML(새머리, ["---"] + ["---:"] * len(행들), 새행, 단위=True, 전치=True)


def _표줄들(줄, i):
    """i 부터 빈 줄을 건너 이어지는 마크다운 표들 → ([(머리, 행들)], 다음 i). 표가 아닌 줄을 만나면 멈춘다."""
    표들 = []
    while True:
        j = i
        while j < len(줄) and not 줄[j].strip():
            j += 1
        if j + 1 < len(줄) and re.match(r"^\|.*\|\s*$", 줄[j].strip()) and re.match(r"^\|[\s\-:|]+\|\s*$", 줄[j + 1].strip()):
            블 = [줄[j], 줄[j + 1]]
            j += 2
            while j < len(줄) and re.match(r"^\|.*\|\s*$", 줄[j].strip()):
                블.append(줄[j])
                j += 1
            머 = [c.strip() for c in 블[0].strip().strip("|").split("|")]
            행 = [[c.strip() for c in l.strip().strip("|").split("|")] for l in 블[2:]]
            표들.append((머, 행, 블))
            i = j
            continue
        return 표들, i


모션폴더 = "모션"                 # 레터모션.py 가 영상(mp4 · gif · 포스터)을 내는 레터 곁 폴더 — 네이버 · 메일 · SNS 용. 웹 레터는 영상을 쓰지 않는다(v4e)
자산 = os.path.join(여기, "자산")
애니메 = "anime-4.5.0.umd.min.js"        # Anime.js v4.5.0(MIT, 2026-06-22) — 받은 배포 파일 그대로(머리말에 라이선스). 레터는 한 장으로 서야 해 인라인으로 싣는다


def 모션만(아이디):
    """옛 표지(「<!-- 모션:X -->」 — 그림 없이 따로 서는 모션). v4e 부터 웹은 영상을 쓰지 않아 아무것도 내지 않는다."""
    return ""


웹모션 = False                    # 레터 v27 7단계(디자인 결정 1) — 웹 레터 본편에서 「순서대로 보기」 · 장면 재생 · 「주가」 슬라이더를 뺀다(영상은 `레터모션.py`)
인쇄표한도 = 12                   # 그림의 숫자표가 이 줄 수 이하면 인쇄본에 펼쳐 싣는다(1막 궤적처럼 긴 표는 접힌 채)
인쇄표종류 = ("길", "계단")         # 그림에 숫자가 다 찍히지 않는 그림만(그림 2 「자」 · 시계 · 신호는 그림의 글에 값이 있다)
전치열 = 6                        # 인쇄용 숫자표의 열이 이보다 많으면 돌려 세운다(용지 밖으로 잘리지 않게 · 그림 곁 단에 들게)


def _출처줄(종류, 표들, 출처, 제목=""):
    """그림 아래 출처 한 줄(리뷰 4순위) — 「자료: 이 평가의 계산(평가기준일 …)」, 주가가 든 그림(머리 · 줄 이름에 종가 · 주가)은 문서의 「주가 자료:」 줄.
    2026-10-25 R5 — 캡션에 그림마다의 「출처:」 문장(그 그림이 찍은 장부 키에서 지은 글 · `레터본문.출처글`)이 있으면 「자료: 이 평가의 계산」 을 되풀이하지
    않고 평가기준일(과 주가 자료)만 남긴다. 둘 다 없으면 줄을 세우지 않는다."""
    if 종류 in ("띠", "신호", "연결") or not 출처:
        return ""
    캡션출처 = bool(re.search(r"(?:출처|자료):\s*\S", re.sub(r"\*", "", 제목 or "")))      # `레터그림검사.출처있나` 와 같은 판정
    글들 = [c for m, r, _b in 표들 for c in list(m) + [x for 줄 in r for x in 줄[:1]]]
    주가 = 출처.get("주가") and any(("종가" in c or c.strip() == "주가" or c.strip().startswith("주가")) for c in 글들)
    if 캡션출처:
        조각 = (["평가기준일 %s" % 출처["기준일"]] if 출처.get("기준일") else []) + (["주가: %s" % 출처["주가"]] if 주가 else [])
        return ('<p class="viz-src">%s</p>' % 이스케이프(" · ".join(조각))) if 조각 else ""
    말 = "자료: 이 평가의 계산" + (("(평가기준일 %s)" % 출처["기준일"]) if 출처.get("기준일") else "")
    if 주가:
        말 += " · 주가: %s" % 출처["주가"]
    return '<p class="viz-src">%s</p>' % 이스케이프(말)


def 그림(종류, 제목, 표들, 모션=None, 출처=None, 부록=False):
    """그림 표지 블록 → HTML(figure). 그림이 못 서면 표만.
    v4e — 두 판 그림(레터그림.두판: 가치 · 길 · 자 · 토네이도)은 넓은 판(데스크톱 560px)과 좁은 판(휴대폰)을 함께 싣고 화면 폭으로 고른다(인쇄는 넓은 판).
    모션 표지가 있고 `레터모션.웹계획` 이 장면을 세우면 시간표(영상과 같은 단계 목록 — 한 출처)를 JSON 으로 싣는다. 처음엔 완성된 정적 그림이고,
    「순서대로 보기」 를 눌렀을 때만 스크립트(Anime.js)가 같은 SVG 의 속성을 움직인다. 스크립트가 없거나 줄인 움직임 · 인쇄면 정적 그림 그대로.
    레터 v27 7단계(디자인 결정 1 · 4) — 본편 그림은 누르지 않고 다 보인다: 「그림의 숫자」 접힘 · 인쇄 단 · 모션 시간표를 싣지 않는다(그 숫자는 같은
    블록의 「가정과 결과」 표에 있다). 부록 그림은 검증 자료라 접힌 숫자표를 둔다(모션은 없다). 영상은 `레터모션.py` 가 따로 굽는다."""
    f = 레터그림.그림들.get(종류)
    표2 = [(m, r) for m, r, _b in 표들]
    제 = re.sub(r"\*", "", 제목)
    if f and 종류 in getattr(레터그림, "두판", ()):
        넓 = f(표2, 제, 판="넓은")
        그 = (넓 + f(표2, 제, 판="좁은")) if 넓 else ""
    else:
        그 = f(표2, 제) if f else ""
    if 종류 == "띠" and 그:                               # 통독 v4 상-3 — 첫 화면의 요약 띠(그림의 숫자를 따로 달지 않는다)
        return ("<p>%s</p>" % 인라인(제목) if 제목 else "") + 그
    표 = "".join(표만들기(b) for _m, _r, b in 표들)
    if not 그:
        return ("<p>%s</p>" % 인라인(제목) if 제목 else "") + 표
    접힘 = "" if (종류 in ("신호", "연결") or not 부록) else '<details><summary>그림의 숫자</summary>%s</details>' % 표     # 연결도는 상자가 곧 글(2026-10-16) · 본편은 접힘 없음(v27 7단계)
    인쇄 = False
    if 접힘 and 종류 in 인쇄표종류 and sum(len(r) for _m, r, _b in 표들) <= 인쇄표한도:     # 통독 v3 — 작은 숫자표는 인쇄(PDF)에서 펼쳐 싣는다
        접힘 += '<div class="print-only">%s</div>' % "".join(                 # 그림 안 주석의 표(「그림 1의 주석」)는 그림이 이미 보인다 — 인쇄 단에서 뺀다
            (전치표만들기(b) if len(m) > 전치열 else 표만들기(b)) for m, _r, b in 표들 if not m[0].strip().endswith("주석"))
        인쇄 = True
    갈 = "viz-fig viz-%s%s" % (종류, " has-print" if 인쇄 else "")
    줄 = _출처줄(종류, 표들, 출처, 제목)
    계획 = None
    if 모션 and 웹모션:                                     # v27 7단계 — 웹 레터는 움직이지 않는다(웹모션 거짓). 표지는 영상용으로 남는다
        import 레터모션                                    # noqa: PLC0415 — 레터모션이 이 모듈을 부른다(늦게 부른다)
        계획 = 레터모션.웹계획(종류, 표2, 제)
    if 계획:
        계획 = dict(계획, 장면=모션)
        js = json.dumps(계획, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
        return ('<figure class="%s motion-fig" data-motion="%s"><figcaption>%s</figcaption>%s%s<script type="application/json" class="motion-plan">%s</script>'
                '%s</figure>') % (갈, 이스케이프(모션), 인라인(제목), 그, 줄, js, 접힘)
    return '<figure class="%s"><figcaption>%s</figcaption>%s%s%s</figure>' % (갈, 인라인(제목), 그, 줄, 접힘)


def 모션JS():
    """웹 모션 — Anime.js(인라인) 의 타임라인을 시계로 쓰고, 그 순간의 키 진행(시간표 · 이징 = 영상과 같은 단계 목록)으로 data-m 주석을 칠한다.
    규칙(디자이너 리뷰 3 · 7순위): 자동 재생 없음 · 처음엔 완성 그림 · 「순서대로 보기」 를 누를 때만 · 한 번에 한 장면(다른 장면을 시작하면
    재생 중이던 장면은 완성 그림으로) · 단계형(가치 — 「다음 ▸ 1/4」 · 이전 · 키보드 ← → · Esc) · 재생형(멈춤 · 이어 보기 · 다시 보기 · Esc).
    줄인 움직임이면 단추를 달지 않는다(바뀌면 완성 그림으로 걷는다). 인쇄 직전에는 완성 그림으로. 그림이 화면에 있으면 「맨 위로」 를 숨긴다.
    v4f(리뷰 7순위 「자리 고정」) — 주 단추(순서대로 보기 · 다음 · 멈춤 · 다시 보기)는 늘 줄의 오른쪽 끝이다. 「완성 그림」 · 「이전」 · 단계 점은
    그 왼쪽에 서고 사라져도 주 단추가 움직이지 않는다."""
    try:
        라 = io.open(os.path.join(자산, 애니메), encoding="utf-8").read()
    except OSError:
        return ""
    if "</script" in 라.lower():
        raise SystemExit("라이브러리 글에 </script 가 있어 인라인으로 실을 수 없다")
    return "<script>\n" + 라.strip() + "\n</script>\n" + 모션제어
# 모션 제어(레터 자체 스크립트) — 진행 적용 규칙은 `레터그림판.진행적용` 과 같다(같은 속성의 주석은 차례대로, 시작한 마지막 주석의 값, 다 끝나면 원래 속성).
모션제어 = """<script>(function(){
var A=window.anime,F=[].slice.call(document.querySelectorAll('figure.motion-fig'));
if(!F.length||!A||!A.createTimeline||!A.eases)return;
var RM=window.matchMedia?matchMedia('(prefers-reduced-motion: reduce)'):null;
if(RM&&RM.matches)return;
var EZ={'삼차':A.eases.inOutCubic,'선형':A.eases.linear,'삼차_들어감':A.eases.inCubic,'삼차_나감':A.eases.outCubic};
var IC={play:'M1.5 .5 9.5 5 1.5 9.5Z',pause:'M1 .5h3v9H1zM6 .5h3v9H6z',next:'M1.5 .5 9.5 5 1.5 9.5Z',prev:'M8.5 .5.5 5 8.5 9.5Z',
 again:'M5 .6a4.4 4.4 0 1 0 4.4 4.4H8a3 3 0 1 1-1-2.2L5.6 4.2H9.6V.2L8 1.8A4.4 4.4 0 0 0 5 .6Z',end:'M.5 .5h9v9h-9z'};
function ic(n){return '<svg viewBox="0 0 10 10" aria-hidden="true"><path d="'+IC[n]+'"/></svg>';}
var live=null,all=[];
function grab(f){return [].slice.call(f.querySelectorAll('[data-m]')).map(function(el){var g={},o=[];
 JSON.parse(el.getAttribute('data-m')).forEach(function(w){if(!g[w[1]]){g[w[1]]=[];o.push(w[1]);}g[w[1]].push(w);});
 return {el:el,g:o.map(function(a){return {a:a,t:g[a],o:el.getAttribute(a)};})};});}
function paint(E,P){E.forEach(function(x){x.g.forEach(function(r){var v=r.t[0][2],d=true;
 r.t.forEach(function(w){var p=P[w[0]];if(p==null)p=1;if(p>0)v=w[2]+(w[3]-w[2])*p;if(p<1)d=false;});
 if(d){if(r.o===null)x.el.removeAttribute(r.a);else x.el.setAttribute(r.a,r.o);}else x.el.setAttribute(r.a,String(Math.round(v*1000)/1000));});});}
function prog(plan,t){var P={};plan.키.forEach(function(k){var u;if(k.e<=k.s)u=t>=k.s?1:0;else u=(t-k.s)/(k.e-k.s);
 P[k.k]=u<=0?0:(u>=1?1:(EZ[k.이징]||EZ['선형'])(u));});return P;}
function Ctl(f){
 var me=this,plan=JSON.parse(f.querySelector('script.motion-plan').textContent),E=grab(f),T=plan.초,M=plan.마디||[],step=plan.방식==='단계'&&M.length>1;
 var head={t:T},stopAt=null,at=0,st='idle',played=false;
 var tl=A.createTimeline({autoplay:false,onUpdate:function(){draw(head.t);},onComplete:function(){if(st==='play'){played=true;me.finish();}}});
 tl.add(head,{t:[0,T],duration:T*1000,ease:'linear'},0);
 var bar=document.createElement('div');bar.className='motion-ctl';bar.setAttribute('role','group');bar.setAttribute('aria-label','그림 순서대로 보기');
 var bPrev=btn('prev'),bMain=btn('main'),bEnd=btn('end'),dots=document.createElement('span'),say=document.createElement('span');
 dots.className='m-dots';dots.setAttribute('aria-hidden','true');say.className='m-say';say.setAttribute('aria-live','polite');
 if(step){for(var i=0;i<M.length;i++)dots.appendChild(document.createElement('i'));bar.appendChild(bPrev);bar.appendChild(dots);}
 bar.appendChild(bEnd);bar.appendChild(bMain);bar.appendChild(say);
 var svgs=f.querySelectorAll('svg.viz');svgs[svgs.length-1].insertAdjacentElement('afterend',bar);
 function btn(n){var b=document.createElement('button');b.type='button';b.className='m-'+n;return b;}
 function set(b,i,t,al){b.innerHTML=ic(i)+'<span>'+t+'</span>';if(al)b.setAttribute('aria-label',al);else b.removeAttribute('aria-label');}
 function ui(){
  var n=M.length;
  if(st==='idle'){set(bMain,played?'again':'play',(played?'다시 보기':'순서대로 보기')+' · '+(step?(n+'단계'):(Math.round(T)+'초')));bEnd.hidden=true;bPrev.hidden=true;dots.hidden=true;}
  else if(step){bPrev.hidden=false;dots.hidden=false;bEnd.hidden=false;set(bPrev,'prev','이전','이전 단계');bPrev.disabled=at<=0&&st!=='play';
   if(at>=n&&st!=='play')set(bMain,'again','처음부터');else set(bMain,'next','다음 '+Math.min(at+1,n)+'/'+n,'다음 단계 '+Math.min(at+1,n)+' / '+n);
   set(bEnd,'end','완성 그림');[].forEach.call(dots.children,function(d,i){d.className=i<at?'on':'';});}
  else{bEnd.hidden=false;set(bEnd,'end','완성 그림');if(st==='play')set(bMain,'pause','멈춤');else set(bMain,'play','이어 보기');}
 }
 function draw(t){if(st==='idle')return;paint(E,prog(plan,t));if(stopAt!=null&&t>=stopAt-1e-6){var s=stopAt;stopAt=null;tl.pause();head.t=s;paint(E,prog(plan,s));st='step';ui();}}
 function take(){if(live&&live!==me)live.finish();live=me;}
 function go(from,to){take();stopAt=to;st='play';head.t=from;paint(E,prog(plan,from));tl.seek(from*1000);ui();tl.play();}
 me.finish=function(){st='idle';tl.pause();stopAt=null;head.t=T;paint(E,{});at=0;if(live===me)live=null;ui();};
 function next(){if(!step)return;if(st==='play')return;if(at>=M.length){at=0;say.textContent='처음 상태';enter();return;}
  var k=at;at+=1;say.textContent=at+'/'+M.length+' 단계';go(M[k][0],M[k][1]);}
 function enter(){take();st='step';at=0;stopAt=null;tl.pause();head.t=M[0][0];paint(E,prog(plan,M[0][0]));ui();}
 function prev(){if(!step)return;tl.pause();stopAt=null;at=Math.max(0,at-1);var t=at>0?M[at-1][1]:M[0][0];head.t=t;paint(E,prog(plan,t));st='step';ui();
  say.textContent=at>0?(at+'/'+M.length+' 단계'):'처음 상태';}
 bMain.addEventListener('click',function(){
  if(step){if(st==='idle'){enter();say.textContent='처음 상태 — 다음 단추로 넘긴다';}else next();return;}
  if(st==='idle'){take();go(0,null);}else if(st==='play'){tl.pause();st='pause';ui();}else{take();st='play';ui();tl.play();}});
 bPrev.addEventListener('click',prev);bEnd.addEventListener('click',function(){me.finish();bMain.focus();});
 bar.addEventListener('keydown',function(e){if(e.key==='Escape'){me.finish();bMain.focus();e.preventDefault();}
  else if(step&&st!=='idle'&&e.key==='ArrowRight'){next();e.preventDefault();}else if(step&&st!=='idle'&&e.key==='ArrowLeft'){prev();e.preventDefault();}});
 me.drop=function(){me.finish();bar.remove();};
 paint(E,{});ui();
}
F.forEach(function(f){try{all.push(new Ctl(f));}catch(e){}});
window.addEventListener('beforeprint',function(){if(live)live.finish();});
if(RM&&RM.addEventListener)RM.addEventListener('change',function(e){if(e.matches)all.forEach(function(c){c.drop();});});
var top=document.querySelector('.to-top');
if(top&&'IntersectionObserver' in window){var on=new Set();var io=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting)on.add(e.target);else on.delete(e.target);});
 top.classList.toggle('motion-near',on.size>0);});F.forEach(function(f){io.observe(f);});}
})();</script>"""

# 단계 — 격자 칸에서만 서는 주가 단계(v4f · 모션 리뷰 하-12 「웹판 2단계」): svg[data-steps](`레터그림본편.곡선`)마다 범위 단추 하나 · 칸을 옮기면
# 세로 표시선과 구분마다의 점이 그 칸으로 가고 그 칸의 글(표의 칸 그대로 — 보간 없음)을 읽어 준다. 움직임이 없어 줄인 움직임에서도 쓴다.
# 읽어 주는 말은 data-steps 의 「말」(2026-10-25 R5 — 곡선의 세로축이 무엇인가: 증가율 경로 판은 「전제한 영구기간 영업이익률」)이고, 없으면
# 「전제한 정상 수준」(수준 경로 판). 「말」 이 있고 계열이 하나면 계열 이름을 되풀이하지 않는다.
# 스크립트가 없거나 인쇄면 정적 그림 그대로(CSS 가 단추와 표시를 숨긴다).
단계JS = """<script>(function(){
var NS='http://www.w3.org/2000/svg';
[].slice.call(document.querySelectorAll('svg.viz[data-steps]')).forEach(function(svg,j){try{
 var d=JSON.parse(svg.getAttribute('data-steps')),n=d.x.length;if(n<2)return;
 var g=document.createElementNS(NS,'g');g.setAttribute('class','vz-step-mark');g.setAttribute('aria-hidden','true');
 var ln=document.createElementNS(NS,'line');ln.setAttribute('class','vz-step-line');ln.setAttribute('y1',d['위']);ln.setAttribute('y2',d['아래']);g.appendChild(ln);
 var dots=d['구분'].map(function(_n,k){var c=document.createElementNS(NS,'circle');c.setAttribute('r','4.5');c.setAttribute('class','vz-step-dot vz-step-dot'+(k%3+1));g.appendChild(c);return c;});
 svg.appendChild(g);
 var box=document.createElement('div');box.className='step-ctl';
 var lab=document.createElement('label'),inp=document.createElement('input'),out=document.createElement('output');
 inp.type='range';inp.min='0';inp.max=String(n-1);inp.step='1';inp.id='step-'+j;out.setAttribute('for',inp.id);out.setAttribute('aria-live','polite');
 lab.appendChild(document.createTextNode('주가'));lab.appendChild(inp);box.appendChild(lab);box.appendChild(out);
 svg.insertAdjacentElement('afterend',box);
 function set(i){var x=d.x[i];ln.setAttribute('x1',x);ln.setAttribute('x2',x);
  dots.forEach(function(c,k){var y=d.y[i][k];if(y==null){c.setAttribute('visibility','hidden');}else{c.removeAttribute('visibility');c.setAttribute('cx',x);c.setAttribute('cy',y);}});
  var t='주가 '+d['가격'][i]+'일 때 '+(d['말']||'전제한 정상 수준')+': '+d['구분'].map(function(nm,k){return (d['말']&&d['구분'].length<2)?d['값'][i][k]:nm+' '+d['값'][i][k];}).join(' · ');
  out.textContent=t;inp.setAttribute('aria-valuetext',t);}
 inp.value=String(d['처음']||0);set(+inp.value);inp.addEventListener('input',function(){set(+inp.value);});
}catch(e){}});
})();</script>"""

# 화면 — 넘치는 표 넓히기 · 넘침 그림자, 읽은 만큼 막대, 맨 위로, 옆 목차의 지금 자리, 부록 펼치기(바로가기 · 인쇄)
화면JS = """<script>(function(){
var mm=function(q){return window.matchMedia&&matchMedia(q).matches;};
var S=[].slice.call(document.querySelectorAll('.scroll'));
function shade(s){var m=s.scrollWidth-s.clientWidth;s.classList.toggle('more-right',m>1&&s.scrollLeft<m-1);s.classList.toggle('scrolled',s.scrollLeft>1);}
function widen(){var big=mm('(min-width:900px)');S.forEach(function(s){s.classList.remove('wide');});
 S.forEach(function(s){if(big&&s.scrollWidth>s.clientWidth+1&&!s.closest('details:not([open])'))s.classList.add('wide');});S.forEach(shade);}
S.forEach(function(s){s.addEventListener('scroll',function(){shade(s);},{passive:true});});
var bar=document.querySelector('.progress span'),top=document.querySelector('.to-top');
var links=[].slice.call(document.querySelectorAll('nav.side-toc a[href^="#"]'));
var marks=links.map(function(a){return document.getElementById(decodeURIComponent(a.getAttribute('href').slice(1)));});
var tick=false;
function onScroll(){tick=false;var h=document.documentElement,y=window.scrollY||h.scrollTop,max=h.scrollHeight-innerHeight;
 if(bar)bar.style.transform='scaleX('+(max>0?Math.min(1,y/max):0)+')';
 if(top)top.classList.toggle('on',y>innerHeight*1.2);
 if(links.length){var k=-1;for(var i=0;i<marks.length;i++){if(marks[i]&&marks[i].getBoundingClientRect().top<innerHeight*.3)k=i;}
  links.forEach(function(a,i){if(i===k)a.setAttribute('aria-current','true');else a.removeAttribute('aria-current');});}}
window.addEventListener('scroll',function(){if(!tick){tick=true;requestAnimationFrame(onScroll);}},{passive:true});
var rt;window.addEventListener('resize',function(){clearTimeout(rt);rt=setTimeout(function(){widen();onScroll();},150);});
function openTo(id){var e=id&&document.getElementById(id);if(!e)return;var d=e.closest('details');if(d&&!d.open){d.open=true;widen();}}
function hash(){openTo(decodeURIComponent(location.hash.slice(1)));}
window.addEventListener('hashchange',hash);
document.addEventListener('click',function(ev){var a=ev.target.closest&&ev.target.closest('a[href^="#"]');if(a)openTo(decodeURIComponent(a.getAttribute('href').slice(1)));});
document.querySelectorAll('details').forEach(function(d){d.addEventListener('toggle',widen);});
window.addEventListener('beforeprint',function(){document.querySelectorAll('details.app').forEach(function(d){d.open=true;});});
widen();hash();onScroll();window.addEventListener('load',function(){widen();onScroll();});
if(document.fonts&&document.fonts.ready)document.fonts.ready.then(function(){widen();onScroll();});
})();</script>"""


def 머리id(깊이, 글):
    """절 머리의 바로가기 이름 — 「5. 매출 추정」 → s5 · 「3분 레터」 → 삼분 · 「부록 C. …」 → 부록C · 「본편」 · 「부록」(첫째 단)."""
    t = re.sub(r"<[^>]+>|\*", "", 글).strip()
    m = re.match(r"^(\d+)\.\s", t)
    if 깊이 == 2 and m:
        return "s%s" % m.group(1)
    m = re.match(r"^부록\s?([A-Z])\.", t)
    if 깊이 == 2 and m:
        return "부록%s" % m.group(1)
    if 깊이 == 2 and t.startswith("3분 레터"):
        return "삼분"
    if 깊이 == 1 and t in ("본편", "부록"):
        return t
    if 깊이 == 1 and t == "다섯 막":                          # R1c(L-D)
        return "막"
    if 깊이 == 1 and t.startswith("깊이 층"):
        return "깊이"
    return None


블록머리말 = (("매출 추정", "매출"), ("영업비용 추정", "영업비용"), ("인건비 추정", "인건비"), ("설비투자와 감가상각", "설비투자"),
            ("운전자본 추정", "운전자본"), ("법인세와 FCFF", "법인세"), ("할인율", "할인율"), ("Terminal Value", "영구가치"),
            ("가치 브리지", "가치 브리지"))           # 추정 블록 절(「N. 이름 : 하는 일」 의 이름) → 추정 단계 표시의 짧은 이름


def 추정단계들(원문):
    """레터 v27 7단계(시안 3C) — 본편의 추정 블록 절 → [(절 번호, 짧은 이름)] (문서에 선 차례대로). 부록 앞까지만 본다."""
    낸 = []
    for L in 원문.split("\n"):
        if L.startswith("# ") and L[2:].strip().startswith("부록"):
            break
        m = re.match(r"^##\s+(\d+)\.\s+(.+?)(?:\s+:\s+.*)?$", L.strip())
        if m:
            앞 = m.group(2).strip()
            짧 = next((s for 이, s in 블록머리말 if 앞 == 이), None)
            if 짧:
                낸.append((m.group(1), 짧))
    return 낸


def 단계표시(단계들, 번):
    """추정 단계 표시 — 블록 차례 한 줄(지금 블록만 청색 윗선 · 굵은 글자). 단계가 둘 이상일 때만."""
    if len(단계들) < 2:
        return ""
    항 = "".join('<li%s><a href="#s%s">%s</a></li>' % (' class="cur" aria-current="step"' if n == 번 else "", n, 이스케이프(s)) for n, s in 단계들)
    return '<ol class="steps" aria-label="추정 단계">%s</ol>' % 항


def 변환(원문, 정보=None):
    """마크다운 → 본문 HTML. 정보(dict)를 주면 머리 목록(옆 목차) · 막의 절 · 3분 자리를 채운다."""
    정보 = {} if 정보 is None else 정보
    머리들 = 정보.setdefault("머리", [])                      # [(깊이, id, 글, 단)]
    줄 = 원문.split("\n")
    나 = []
    i = 0
    첫제목 = True
    지금단 = None
    부록 = False                                             # v27 7단계 — 「# 부록」 아래의 그림만 숫자표를 접어 둔다
    단계들 = 추정단계들(원문)                                 # v27 7단계 — 추정 블록 절 머리 아래 추정 단계 표시
    while i < len(줄):
        L = 줄[i]
        S = L.strip()
        m = re.match(r"^<!--\s*모션:([A-Z][A-Za-z0-9]*)\s*-->$", S)
        if m:                                                # R1c 옛 표지 — v4e 부터 아무것도 내지 않는다
            i += 1
            continue
        m = re.match(r"^<!--\s*그림:(\S+)(?:\s*·\s*모션:([A-Z][A-Za-z0-9]*))?\s*-->$", S)
        if m:                                                # R1b — 그림 표지: 굵은 제목 한 줄 + 표들(R1c — 짝 모션)
            i += 1
            제목 = ""
            if i < len(줄) and 줄[i].strip() and not 줄[i].strip().startswith("|"):
                제목 = 줄[i].strip()
                i += 1
            표들, i = _표줄들(줄, i)
            나.append(그림(m.group(1), 제목, 표들, m.group(2), 정보.get("출처"), 부록=부록))
            continue
        if re.match(r"^<!--.*-->$", S):                       # 2026-10-26 — 그 밖의 표지(합본:3분과같음 따위)는 주석 그대로(글로 찍지 않는다)
            나.append(S)
            i += 1
            continue
        if re.match(r"^\|.*\|\s*$", S) and i + 1 < len(줄) and re.match(r"^\|[\s\-:|]+\|\s*$", 줄[i + 1].strip()):
            블 = [줄[i], 줄[i + 1]]
            i += 2
            while i < len(줄) and re.match(r"^\|.*\|\s*$", 줄[i].strip()):
                블.append(줄[i])
                i += 1
            나.append(표만들기(블))
            continue
        if S.startswith("> "):
            안 = []
            견본 = S[2:].startswith("견본")
            깃발 = False
            while i < len(줄) and 줄[i].strip().startswith(">"):
                t = 줄[i].strip().lstrip(">").strip()
                if t:
                    if "확인하지 않았" in t or "한계" in t:
                        깃발 = True
                    안.append("<p>%s</p>" % 인라인(t))
                i += 1
            if 견본:
                나.append('<div class="sample">%s</div>' % "".join(안))
            else:
                나.append('<blockquote%s>%s</blockquote>' % (' class="flag"' if 깃발 else "", "".join(안)))
            continue
        if S.startswith("- "):
            항, 원항 = [], []
            while i < len(줄) and 줄[i].strip().startswith("- "):
                원항.append(줄[i].strip()[2:])
                항.append("<li>%s</li>" % 인라인(줄[i].strip()[2:]))
                i += 1
            목차 = all(re.match(r"^\[[^\]]+\]\(#[^)]+\)$", x) for x in 원항)
            나.append('<ul%s>%s</ul>' % (' class="toc"' if 목차 else "", "".join(항)))
            continue
        m = re.match(r"^(#{1,3})\s+(.*)$", S)
        if m:
            깊이, 글 = len(m.group(1)), m.group(2)
            if 깊이 == 1 and 첫제목:
                나.append("<h1>%s</h1>" % 인라인(글))
                정보["제목"] = re.sub(r"[*`]", "", 글).strip()
                첫제목 = False
                i += 1
                if i < len(줄) and not 줄[i].strip():
                    i += 1
                if i < len(줄) and 줄[i].strip() and not 줄[i].strip().startswith(("#", "|", ">", "-", "<!--")):
                    정보["머리줄"] = 줄[i].strip()
                    나.append('<p class="lede">%s</p>' % 인라인(줄[i].strip()))
                    i += 1
                정보["첫"] = len(나)
                continue
            if 깊이 == 1 and re.match(r"^(부록|2부|Part\s*II)\b", 글):
                나.append('</div><div class="wrap" id="appendix">')
                부록 = True
            아 = 머리id(깊이, 글)
            if 깊이 == 1:
                정보.setdefault("첫단", len(나))
                지금단 = 아
                나.append('<div class="part"%s><h1>%s</h1></div>' % ((' id="%s"' % 아) if 아 else "", 인라인(글)))
                if 아:
                    머리들.append((1, 아, re.sub(r"[*`]", "", 글).strip(), 아))
            else:
                q = re.match(r"^(\d+\.\s.+?\?)\s·\s(.+)$", 글) if 깊이 == 2 else None     # R1c — 질문형 제목 + 기존 이름(작게)
                안 = ("%s <small class=\"old\">%s</small>" % (인라인(q.group(1)), 인라인(q.group(2)))) if q else 인라인(글)
                나.append("<h%d%s>%s</h%d>" % (깊이, (' id="%s"' % 아) if 아 else "", 안, 깊이))
                if 깊이 == 2 and not 부록 and 아 and re.match(r"^s\d+$", 아) and any(n == 아[1:] for n, _s in 단계들):
                    나.append(단계표시(단계들, 아[1:]))
                if 아 and 깊이 == 2 and re.match(r"^s\d+$", 아) and "첫단" not in 정보:
                    정보["앞절"] = True                     # 첫 단 앞에 번호 절이 있다 — 3분 레터 자리가 아니다(옛 꼴 레터)
                if 아 and 깊이 == 2:
                    머리들.append((2, 아, re.sub(r"[*`]", "", q.group(1) if q else 글).strip(), 지금단))
            i += 1
            continue
        if re.match(r"^-{3,}$", S):
            나.append("<hr>")
            i += 1
            continue
        if not S:
            i += 1
            continue
        문단 = [L]
        i += 1
        while i < len(줄) and 줄[i].strip() and not re.match(r"^(#{1,3}\s|\||>|- |-{3,}$|<!--)", 줄[i].strip()):
            문단.append(줄[i])
            i += 1
        나.append("<p>%s</p>" % 인라인(" ".join(x.strip() for x in 문단)))
    _부록접기(나)
    return "\n".join(나)


def _부록접기(나):
    """부록마다(「## 부록 X.」 에서 다음 부록 · 다음 단까지) <details> 로 접는다. 요약줄에 표 수 · 행 수(통독 v4 중-1). 인쇄에서는 펼친다."""
    k = 0
    while k < len(나):
        m = re.match(r'^<h2 id="(부록[A-Z])">(.*)</h2>$', 나[k], re.S)
        if not m:
            k += 1
            continue
        j = k + 1
        while j < len(나) and not re.match(r'^(<h2 id="부록[A-Z]">|<div class="part"|</div><div class="wrap")', 나[j]):
            j += 1
        안 = "\n".join(나[k + 1:j])
        표수 = 안.count("<table")
        행수 = max(0, 안.count("</tr>") - 표수)
        말 = "표 %d개 · 행 %d개" % (표수, 행수) if 표수 else "표 없음"
        나[k] = '<details class="app"><summary><h2 id="%s">%s</h2><span class="app-meta">%s</span></summary>' % (m.group(1), m.group(2), 말)
        나.insert(j, "</details>")
        k = j + 1


# ── 본문 글 다듬기(통독 v4 중-2 · 중-11) — 태그 밖의 글에만. 제목 · 표 머리 · 링크 · 그림(SVG) 안은 건드리지 않는다
_막는태그 = {"a", "h1", "h2", "h3", "th", "svg", "title", "script", "style", "code", "summary", "button", "nav"}
_날짜 = re.compile(r"(\d{4}-\d{2}-\d{2}|\d{4}년 \d{1,2}월 \d{1,2}일|\d{4}년 \d{1,2}월|\d{4}년 \d분기|\d{1,2}월 \d{1,2}일)")
_참조 = re.compile(r"(3분 레터(?: 그림 \d+)?)|(?<![\d.~])(\d{1,2})(막|절)|(부록 ?([A-Z]))(?![A-Za-z])")


def 글다듬기(본문, 있는id, 막id=(), 본편파일=None, 삼분=False):
    """참조 글을 링크로 잇고(자리가 문서에 있을 때만 — 3분 파일은 본편 파일로), 날짜를 줄 끝에서 쪼개지 않게 묶는다."""
    조각 = re.split(r"(<[^>]+>)", 본문)
    막는 = 0
    낸 = []

    def 주소(아):
        if 삼분:
            return ("%s#%s" % (본편파일, 아)) if 본편파일 else None
        return ("#" + 아) if 아 in 있는id else None

    def 이어(mt):
        if mt.group(1):
            if 삼분 or "삼분" not in 있는id:
                return mt.group(0)
            return '<a href="#삼분">%s</a>' % mt.group(1)
        if mt.group(2):
            n, 말 = mt.group(2), mt.group(3)
            아 = "s%s" % n
            if 말 == "막" and not 삼분 and 아 not in 막id:
                return mt.group(0)
            u = 주소(아)
            return '<a href="%s">%s%s</a>' % (u, n, 말) if u else mt.group(0)
        아 = "부록%s" % mt.group(5)
        u = 주소(아)
        return '<a href="%s">%s</a>' % (u, mt.group(4)) if u else mt.group(0)
    for c in 조각:
        if c.startswith("<"):
            m = re.match(r"^<(/?)([a-zA-Z0-9]+)", c)
            if m and m.group(2).lower() in _막는태그 and not c.endswith("/>"):
                막는 += -1 if m.group(1) else 1
                막는 = max(막는, 0)
            낸.append(c)
            continue
        if not c:
            continue
        if 막는 == 0:
            c = _참조.sub(이어, c)
            부 = re.split(r"(<[^>]+>)", c)
            c = "".join(x if x.startswith("<") else _날짜.sub(r'<span class="nb">\1</span>', x) for x in 부)
        낸.append(c)
    return "".join(낸)


def 출처찾기(원문):
    """그림 출처 줄의 재료 — 머리 줄의 평가기준일, 문서의 「주가 자료: …」 줄(첫 마침표까지 · 「조회일」 앞까지)."""
    m = re.search(r"평가기준일\s*(\d{4}-\d{2}-\d{2})", 원문)
    주 = re.search(r"^주가 자료:\s*(.+?)(?:\.\s|\.$|\s조회일)", 원문, re.M)
    return {"기준일": m.group(1) if m else "", "주가": 주.group(1).strip().rstrip(".") if 주 else ""}


def 제목찾기(원문):
    for L in 원문.split("\n"):
        if L.startswith("# "):
            return L[2:].strip()
    return "가치평가"


삼분인쇄 = """@media print{
  @page{margin:11mm 12mm 13mm}
  body{font-size:8.7pt; line-height:1.4}
  h1{font-size:1.3rem}
  .lede{margin:.2rem 0 .4rem}
  div.sample{padding:.25rem .6rem; font-size:.74rem; margin:0 0 .5rem}
  h2{margin:.5rem 0 0; padding-top:.3rem; font-size:1.05rem}
  .three h3{margin:.65rem 0 .05rem; font-size:.98rem}
  p{margin:.3rem 0}
  ul{margin:.25rem 0} li{margin:.1rem 0}
  .viz-fig{margin:.4rem 0}
  .viz-fig figcaption{font-size:.82rem; margin:.1rem 0}
  .viz-fig .viz, .viz-fig .viz.viz-wide{max-width:20.5rem; max-height:44mm; margin:.15rem 0}
  .viz-src{font-size:6.5pt; line-height:1.25; margin:0}
  .three .viz-fig{break-inside:auto} .three .viz-fig > figcaption{break-after:avoid} .three .viz-fig > svg.viz{break-inside:avoid}
  .three .viz-fig.has-print{break-inside:avoid} .three .viz-fig.has-print > svg.viz{max-height:45mm}
  .three .viz-fig.has-print > .viz-src{grid-column:1; grid-row:3}
  .three .print-only table{font-size:6.5pt; line-height:1.08} .three .print-only thead th{font-size:6pt} .three .print-only .scroll{margin:.1rem 0}
  .viz-signals{columns:2; column-gap:1.4rem; margin:.3rem 0}
  .viz-signals li{padding:.3rem 0; border-top:1px solid var(--rule)}
  .viz-sig-row{font-size:.82rem}
}"""


def _css글(s):
    return '"%s"' % ("%s" % s).replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")


def 쪽꼬리(정보):
    """인쇄 쪽 아래 — 「회사(제목) · 평가기준일 YYYY-MM-DD · 쪽 / 쪽수」 (문서의 h1 · 머리줄에서 · 통독 v4 상-5)."""
    제 = re.sub(r"\s*—\s*3분 레터\s*$", "", 정보.get("제목") or "").strip()
    m = re.search(r"평가기준일\s*(\d{4}-\d{2}-\d{2})", 정보.get("머리줄") or "")
    앞 = " · ".join(x for x in (제, ("평가기준일 " + m.group(1)) if m else "") if x)
    내용 = (_css글(앞 + " · ") + " ") if 앞 else ""
    return ('@media print{@page{@bottom-center{content:%scounter(page) " / " counter(pages); font-family:"IBM Plex Sans KR","Malgun Gothic",sans-serif; '
            'font-size:8pt; color:#6F6F6F}}}' % 내용)


def _옆목차(머리들):
    if len(머리들) < 4:
        return ""
    항 = []
    for 깊이, 아, 글, _단 in 머리들:
        항.append('<li class="%s"><a href="#%s">%s</a></li>' % ("toc-part" if 깊이 == 1 else "toc-sec", 아, 이스케이프(글)))
    return '<nav class="side-toc" aria-label="목차"><ol>%s</ol></nav>\n' % "".join(항)


def 문서(원문, 제목=None, 견본=False, 삼분=False):
    """마크다운 → HTML 한 장. 삼분 = 3분 레터만 떼어 낸 파일(R1b — 머리 띠 · 두 쪽 인쇄 꼴)."""
    제목 = 제목 or 제목찾기(원문)
    if 견본 and not 제목.startswith("견본"):
        제목 = "견본 — " + 제목
    갈 = " ".join(x for x in ("sample" if 견본 else "", "three" if 삼분 else "") if x)
    정보 = {"출처": 출처찾기(원문)}
    본문 = 변환(원문, 정보)
    if 'id="삼분"' not in 본문 and "<h1>" in 본문:            # 통독 v4 상-3 — 「## 3분 레터」 머리가 없어도 3분 레터 자리(#삼분)는 선다
        첫단 = 정보.get("첫단")
        if 삼분 or (첫단 is not None and 첫단 > 정보.get("첫", 0) and not 정보.get("앞절")):
            본문 = 본문.replace("<h1>", '<h1 id="삼분">', 1)
    있는id = set(re.findall(r'\sid="([^"]+)"', 본문))
    막id = {아 for 깊이, 아, _g, 단 in 정보.get("머리", []) if 깊이 == 2 and 단 == "막"}
    본편파일 = None
    if 삼분:
        m = re.search(r"\]\(([^)\s/:#]+\.html)(?:#[^)\s]*)?\)", 원문)
        본편파일 = m.group(1) if m else None
    본문 = 글다듬기(본문, 있는id, 막id, 본편파일, 삼분)
    머리들 = [] if 삼분 else 정보.get("머리", [])
    if 머리들 and "삼분" in 있는id and not any(아 == "삼분" for _k, 아, _g, _d in 머리들):
        머리들 = [(1, "삼분", "3분 레터", None)] + 머리들
    옆 = _옆목차(머리들)
    m요 = None if (삼분 or "\n## 3분 레터" in 원문) else re.search(r"\[3분 레터\]\(([^)\s/:#]+\.html)\)", 원문)
    if m요:                                                  # 2026-10-16 — 본편만 낸 파일: 옆 목차의 「3분 레터」 는 따로 낸 요약본 파일로
        옆 = 옆.replace('<a href="#삼분">3분 레터</a>', '<a href="%s">3분 레터(요약본)</a>' % m요.group(1), 1)
    # v27 7단계(디자인 결정 1) — 본편에 누르는 요소를 두지 않는다: 모션 재생 · 「주가」 슬라이더(곡선 그림은 정적 눈금 그림이 완성본) 스크립트를 싣지 않는다
    스 = (모션JS() if 'class="motion-plan"' in 본문 else "") + ((단계JS if " data-steps=" in 본문 else "") if 웹모션 else "") + 화면JS + "\n"
    몸 = ('<body%s>\n<a class="skip" href="#본문">본문으로 건너뛰기</a>\n<div class="progress" aria-hidden="true"><span></span></div>\n%s'
          '<main id="본문" tabindex="-1">\n<div class="wrap%s">\n%s\n</div>\n</main>\n<a class="to-top" href="#본문">맨 위로</a>\n%s</body>\n</html>\n') % (
        (' class="%s"' % 갈) if 갈 else "", 옆, " three" if 삼분 else "", 본문, 스)
    머 = 머리.replace("{{제목}}", 이스케이프(제목)).replace("</style>", 레터그림.CSS + "</style>", 1)
    머 = 머.replace("</head>", "<style>" + 쪽꼬리(정보) + "</style>\n</head>", 1)
    if 삼분:                                             # 3분 레터 — A4 두 쪽에 들게 조인다(그림은 줄이고 신호 카드는 두 단)
        머 = 머.replace("</head>", "<style>" + 삼분인쇄 + "</style>\n</head>", 1)
    if 견본:                                             # 인쇄본은 쪽마다 위 여백 오른쪽에 「견본」(본문과 겹치지 않게 여백 상자에)
        머 = 머.replace("</head>", '<style>@media print{@page{@top-right{content:"견본"; color:#9A3B2E; font-size:9pt; '
                                  'letter-spacing:.2em}}}</style>\n</head>', 1)
    return 머 + 몸


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False, description="레터(마크다운)를 HTML 한 장으로")
    ap.add_argument("마크다운")
    ap.add_argument("-o", "--출력", default=None)
    ap.add_argument("--제목", default=None)
    ap.add_argument("--견본", action="store_true")
    ap.add_argument("--삼분", action="store_true", help="3분 레터만 떼어 낸 파일의 꼴(R1b)")
    a = ap.parse_args()
    원문 = io.open(a.마크다운, encoding="utf-8").read()
    출 = a.출력 or (os.path.splitext(a.마크다운)[0] + ".html")
    글 = 문서(원문, a.제목, 견본=a.견본 or ("\n> 견본 —" in 원문), 삼분=a.삼분)
    io.open(출, "w", encoding="utf-8").write(글)
    sys.stdout.reconfigure(encoding="utf-8")
    print("HTML 로 냈다: %s (%d자)" % (os.path.basename(출), len(글)))


if __name__ == "__main__":
    main()

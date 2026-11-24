# -*- coding: utf-8 -*-
"""공통 — 수식 틀 · 참조 풀기 · 손 수식 문법 · 서식 직렬화.

명세추출·열표·줄무늬·짓기·좌표지도가 함께 쓴다. 손 수식 문법의 설명은 수식문법.md 에 있다.

용어
  시트 ID : 옛 시트 이름 머리의 번호로 만든다. '12. 가정_시나리오' → S12
  행 ID   : 시트 ID + 번호. S12R030. 한 번 정하면 배치를 바꿔도 안 바뀐다(= 가정 번호 A-030).
  열 ID   : 뜻으로 부르는 이름(H1 · E1 · TV · 이름 · 단위 · 근거1 …). 열표.py 가 시트마다 정한다.
            명세추출이 갓 뽑은 칸 단위 명세는 아직 옛 열 글자다 — 열표.적용 이 열 ID 로 바꾼다.
  틀      : 수식을 조각 목록으로 나눈 것. 글 조각(str)과 참조(dict)가 섞여 있다.

참조(dict)의 모양
  {"k":"c","x":0,"r":"S12R030","c":"E1","a":"$$"}                     칸 하나
  {"k":"r","x":1,"r":..,"c":..,"a":..,"r2":..,"c2":..,"a2":..}        범위
  {"k":"r",…,"g":"예측"}                                              열 묶음으로 적은 범위(묶음이 늘면 따라 는다)
  {"k":"C","x":0,"s":"S12","c":"여백","a":"$","c2":"단위","a2":"."}   열 전체
  {"k":"R","x":0,"r":"S12R003","a":"$","r2":"S12R007","a2":"$"}       행 전체
  {"k":"n","name":"세율"}                                             정의된 이름
  {"k":"x","t":"원문","why":"사유"}                                   못 바꾸는 것(원문 그대로)
  x = 원문에 시트 이름이 붙어 있었는가(1/0).
  a = 절대 표시 두 글자(열, 행). "$" 절대 · "." 상대.
  fn/arg = 이 참조를 감싼 가장 가까운 「좌표 의존·짝 범위」 함수와 몇 번째 인자인가(위치 의존 판정용).
  w/w2 = 손 수식에서 열을 어떻게 적었나(끝점마다): "." 같은 열 · "n" 이웃 열(@<-1>) · "i" 열 ID 를 못 박음 · "a" 쓰임의 별칭 ·
         "e" 묶음의 첫·끝. 옛 xlsx 에서 뽑은 틀에는 없다. 틀을 견줄 때는 보지 않는다(짓기가 「못 박은 열」을 셀 때만 쓴다).
"""
import re
from copy import copy

from openpyxl.formula import Tokenizer
from openpyxl.utils import get_column_letter, column_index_from_string

최대행 = 1048576
최대열 = 16384

# 좌표에 기대는 함수. 값 = 설명.
좌표의존함수 = {
    "INDIRECT": "글로 주소를 만든다 — 틀로 못 바꾼다(인자가 상수 글이어도 글 속 주소는 안 옮긴다)",
    "OFFSET": "기준 칸에서 몇 줄·몇 칸 떨어진 곳 — 숫자 간격은 배치를 바꾸면 틀린다",
    "ADDRESS": "행·열 번호로 주소 글을 만든다 — 틀로 못 바꾼다",
    "ROW": "행 번호를 돌려준다 — 값이 배치에 따라 달라진다",
    "COLUMN": "열 번호를 돌려준다 — 값이 배치에 따라 달라진다",
    "ROWS": "범위의 줄 수 — 범위 안 줄 수가 바뀌면 달라진다",
    "COLUMNS": "범위의 열 수 — 범위 안 열 수가 바뀌면 달라진다",
    "CELL": "칸 정보(주소 등) — 배치에 따라 달라질 수 있다",
    "INDEX": "범위 안의 몇 번째 — 범위 안 순서·개수가 같아야 한다(짓기가 점검)",
    "MATCH": "범위 안의 위치를 돌려준다 — 짝이 되는 INDEX 범위와 순서·개수가 같아야 한다(짓기가 점검)",
    "CHOOSE": "인자를 번호로 고른다 — 인자가 칸 참조라 틀로 바뀐다(위치 의존 아님)",
    "LOOKUP": "범위 안 위치로 찾는다 — 순서·개수가 같아야 한다",
    "VLOOKUP": "표의 몇 번째 열 — 열 번호 숫자는 열 배치가 바뀌면 틀린다",
    "HLOOKUP": "표의 몇 번째 행 — 행 번호 숫자는 행 배치가 바뀌면 틀린다",
    "XLOOKUP": "범위 안 위치로 찾는다 — 두 범위의 순서·개수가 같아야 한다",
}
# 틀로 못 바꾸는 것(쓰이면 짓기가 경고한다)
못바꾸는함수 = {"INDIRECT", "OFFSET", "ADDRESS", "ROW", "COLUMN", "CELL", "VLOOKUP", "HLOOKUP"}
# 범위 인자의 순서·개수에 값이 달린 것: (함수, 인자 번호)
위치의존 = {("INDEX", 0), ("MATCH", 1), ("LOOKUP", 1), ("LOOKUP", 2), ("VLOOKUP", 1),
        ("HLOOKUP", 1), ("XLOOKUP", 1), ("XLOOKUP", 2), ("OFFSET", 0), ("ROWS", 0), ("COLUMNS", 0)}
# 여러 범위를 자리끼리 짝지어 읽는 함수 — 범위 가운데 줄을 빼면 짝이 어긋나므로 위치 의존으로 다룬다
짝범위함수 = {"SUMPRODUCT", "SUMIFS", "COUNTIFS", "AVERAGEIFS", "SUMIF", "AVERAGEIF", "MAXIFS", "MINIFS",
          "SUMXMY2", "SUMX2MY2", "SUMX2PY2", "CORREL", "SLOPE", "INTERCEPT", "MMULT", "TREND", "FORECAST"}


def 위치로읽나(p):
    """이 참조(범위)는 범위 안의 순서·개수에 값이 달려 있는가."""
    return (p.get("fn"), p.get("arg")) in 위치의존 or p.get("fn") in 짝범위함수


class 배치오류(Exception):
    """배치(또는 손 수식)가 명세의 참조를 깨뜨릴 때."""

    def __init__(self, 오류목록):
        self.오류목록 = 오류목록
        super().__init__("배치 오류 %d건 — 첫 건: %s" % (len(오류목록), 오류목록[0] if 오류목록 else ""))


def 손오류(설명, 종류="손 수식", **덧):
    return 배치오류([dict({"종류": 종류, "시트": None, "자리": None, "설명": 설명}, **덧)])


# 범위 안에 빈 줄·낯선 줄이 생겨도 값의 뜻이 그대로인 함수(빈 칸을 세지 않고 자리로 읽지 않는다) — 「합계 범위」.
# 그 밖의 함수가 읽는 여러 줄 범위는 위치·빈 칸으로 읽는 범위로 다룬다(COUNTBLANK · COUNTIF · INDEX …)
합계함수 = {"SUM", "MAX", "MIN", "COUNT", "COUNTA", "AVERAGE", "PRODUCT", "SUMSQ"}

# ───────────────────────── 함수 이름 ─────────────────────────
# 손 수식에 쓸 수 있는 함수 이름 = 2007년 파일 형식 표준의 함수(openpyxl 의 FORMULAE) + 그 뒤에 나온 함수(새함수).
# 뒤에 나온 함수는 xlsx 에 「_xlfn.」 접두와 함께 적혀야 엑셀이 안다(접두 없이 적히면 엑셀이 _xludf. 를 붙이고 #NAME? 이 된다).
# 손 수식에는 접두 없이 적고(=IFNA(…)), 짓기가 수식 글을 낼 때 붙인다(새함수접두). 이미 붙여 적은 것은 그대로 둔다.
# 이 표는 엑셀 16.0(빌드 20430)에 수식을 적어 저장한 파일에서 확인한 것이다 — 「python 함수표확인.py」 로 다시 확인한다.
from openpyxl.utils import FORMULAE as _엑셀함수  # noqa: E402
새함수 = frozenset("""
ACOT ACOTH AGGREGATE ARABIC ARRAYTOTEXT BASE BETA.DIST BETA.INV BINOM.DIST BINOM.DIST.RANGE BINOM.INV BITAND BITLSHIFT BITOR
BITRSHIFT BITXOR CEILING.MATH CEILING.PRECISE CHISQ.DIST CHISQ.DIST.RT CHISQ.INV CHISQ.INV.RT CHISQ.TEST CHOOSECOLS CHOOSEROWS
COMBINA CONCAT CONFIDENCE.NORM CONFIDENCE.T COT COTH COVARIANCE.P COVARIANCE.S CSC CSCH DAYS DECIMAL DETECTLANGUAGE DROP
ENCODEURL ERF.PRECISE ERFC.PRECISE EXPAND EXPON.DIST F.DIST F.DIST.RT F.INV F.INV.RT F.TEST FILTER FILTERXML FLOOR.MATH
FLOOR.PRECISE FORECAST.ETS FORECAST.ETS.CONFINT FORECAST.ETS.SEASONALITY FORECAST.ETS.STAT FORECAST.LINEAR FORMULATEXT GAMMA
GAMMA.DIST GAMMA.INV GAMMALN.PRECISE GAUSS GROUPBY HSTACK HYPGEOM.DIST IFNA IFS IMAGE IMCOSH IMCOT IMCSC IMCSCH IMSEC IMSECH
IMSINH IMTAN ISFORMULA ISOWEEKNUM LOGNORM.DIST LOGNORM.INV MAXIFS MINIFS MODE.MULT MODE.SNGL MUNIT NEGBINOM.DIST NORM.DIST
NORM.INV NORM.S.DIST NORM.S.INV NUMBERVALUE PDURATION PERCENTILE.EXC PERCENTILE.INC PERCENTOF PERCENTRANK.EXC PERCENTRANK.INC
PERMUTATIONA PHI PIVOTBY POISSON.DIST QUARTILE.EXC QUARTILE.INC RANDARRAY RANK.AVG RANK.EQ REGEXEXTRACT REGEXREPLACE REGEXTEST
RRI SEC SECH SEQUENCE SHEET SHEETS SKEW.P SORT SORTBY STDEV.P STDEV.S STOCKHISTORY SWITCH T.DIST T.DIST.2T T.DIST.RT T.INV
T.INV.2T T.TEST TAKE TEXTAFTER TEXTBEFORE TEXTJOIN TEXTSPLIT TOCOL TOROW TRANSLATE TRIMRANGE UNICHAR UNICODE UNIQUE VALUETOTEXT
VAR.P VAR.S VSTACK WEBSERVICE WEIBULL.DIST WRAPCOLS WRAPROWS XLOOKUP XMATCH XOR Z.TEST
""".split())
_시트접두함수 = frozenset({"SORT", "FILTER"})      # 엑셀은 이 둘을 「_xlfn._xlws.」 로 적는다
# 이름 인자에 「_xlpm.」 접두가 붙어야 하는 함수(LET · LAMBDA 와 LAMBDA 를 인자로 받는 함수) — 손 수식으로는 적지 못한다
못쓰는함수 = {"LET", "LAMBDA", "BYROW", "BYCOL", "MAP", "REDUCE", "SCAN", "MAKEARRAY", "ISOMITTED"}
# 값을 여러 칸에 펼쳐 내는 함수 — 생성기는 수식을 칸마다 적으므로 펼쳐지지 않는다(그 칸에는 첫 값만 나온다. SUM 따위로 감싼 값은 맞다)
펼침함수 = {"UNIQUE", "SORT", "SORTBY", "FILTER", "SEQUENCE", "RANDARRAY", "VSTACK", "HSTACK", "TOCOL", "TOROW", "WRAPROWS",
        "WRAPCOLS", "TAKE", "DROP", "CHOOSEROWS", "CHOOSECOLS", "EXPAND", "TEXTSPLIT", "GROUPBY", "PIVOTBY", "TRIMRANGE"}
함수이름 = set(_엑셀함수) | 새함수

# 자주 쓰는 함수의 인자 수(가장 적게, 가장 많이). 빈 인자(IF(a,1,))도 하나로 센다. 표에 없는 함수는 보지 않는다.
# 닫는 괄호를 한 칸 앞에 적은 겹친 IF(=IF(a,1,IF(b,2,3),4))처럼 괄호 수는 맞는데 엑셀이 못 여는 수식을 잡는다
인자수표 = {
    "IF": (2, 3), "IFERROR": (2, 2), "IFNA": (2, 2), "AND": (1, 255), "OR": (1, 255), "NOT": (1, 1), "XOR": (1, 254),
    "TRUE": (0, 0), "FALSE": (0, 0), "IFS": (2, 254), "SWITCH": (3, 254),
    "INDEX": (2, 4), "MATCH": (2, 3), "VLOOKUP": (3, 4), "HLOOKUP": (3, 4), "LOOKUP": (2, 3), "XLOOKUP": (3, 6), "XMATCH": (2, 4),
    "CHOOSE": (2, 255), "OFFSET": (3, 5), "INDIRECT": (1, 2), "ROW": (0, 1), "COLUMN": (0, 1), "ROWS": (1, 1), "COLUMNS": (1, 1),
    "ADDRESS": (2, 5), "TRANSPOSE": (1, 1),
    "SUM": (1, 255), "SUMIF": (2, 3), "SUMIFS": (3, 255), "SUMPRODUCT": (1, 255), "PRODUCT": (1, 255), "SUMSQ": (1, 255),
    "ROUND": (2, 2), "ROUNDUP": (2, 2), "ROUNDDOWN": (2, 2), "INT": (1, 1), "ABS": (1, 1), "SQRT": (1, 1), "POWER": (2, 2),
    "EXP": (1, 1), "LN": (1, 1), "LOG": (1, 2), "LOG10": (1, 1), "MOD": (2, 2), "SIGN": (1, 1), "TRUNC": (1, 2), "MROUND": (2, 2),
    "CEILING": (2, 2), "FLOOR": (2, 2), "QUOTIENT": (2, 2), "PI": (0, 0), "RAND": (0, 0), "SUBTOTAL": (2, 255), "AGGREGATE": (3, 253),
    "AVERAGE": (1, 255), "AVERAGEIF": (2, 3), "AVERAGEIFS": (3, 255), "COUNT": (1, 255), "COUNTA": (1, 255), "COUNTBLANK": (1, 1),
    "COUNTIF": (2, 2), "COUNTIFS": (2, 254), "MAX": (1, 255), "MIN": (1, 255), "MAXIFS": (3, 253), "MINIFS": (3, 253),
    "MEDIAN": (1, 255), "LARGE": (2, 2), "SMALL": (2, 2), "RANK": (2, 3), "STDEV": (1, 255), "VAR": (1, 255), "PERCENTILE": (2, 2),
    "QUARTILE": (2, 2), "SLOPE": (2, 2), "INTERCEPT": (2, 2), "CORREL": (2, 2),
    "TEXT": (2, 2), "LEN": (1, 1), "LEFT": (1, 2), "RIGHT": (1, 2), "MID": (3, 3), "TRIM": (1, 1), "UPPER": (1, 1), "LOWER": (1, 1),
    "CONCATENATE": (1, 255), "CONCAT": (1, 254), "TEXTJOIN": (3, 254), "SEARCH": (2, 3), "FIND": (2, 3), "SUBSTITUTE": (3, 4),
    "REPLACE": (4, 4), "VALUE": (1, 1), "REPT": (2, 2), "EXACT": (2, 2), "CHAR": (1, 1), "T": (1, 1), "N": (1, 1),
    "ISNUMBER": (1, 1), "ISBLANK": (1, 1), "ISTEXT": (1, 1), "ISERROR": (1, 1), "ISERR": (1, 1), "ISNA": (1, 1), "ISLOGICAL": (1, 1),
    "ISNONTEXT": (1, 1), "ISFORMULA": (1, 1), "NA": (0, 0),
    "DATE": (3, 3), "YEAR": (1, 1), "MONTH": (1, 1), "DAY": (1, 1), "EOMONTH": (2, 2), "EDATE": (2, 2), "TODAY": (0, 0), "NOW": (0, 0),
    "YEARFRAC": (2, 3), "DATEDIF": (3, 3), "DAYS": (2, 2), "DATEVALUE": (1, 1), "WEEKDAY": (1, 2), "NETWORKDAYS": (2, 3),
    "NPV": (2, 255), "IRR": (1, 2), "XNPV": (3, 3), "XIRR": (2, 3), "PV": (3, 5), "FV": (3, 5), "PMT": (3, 5), "RATE": (3, 6), "NPER": (3, 5),
}
_re사용자영역 = re.compile("[\\ue000-\\uf8ff]")


def 남은자리표시(글):
    """낸 수식 글에 안에서 쓰는 자리표시 글자(사용자 영역 글자)가 남았는가."""
    return bool(_re사용자영역.search(글)) if isinstance(글, str) else False


# ───────────────────────── ID ─────────────────────────
def 시트ID(이름, 순번):
    """'12. 가정_시나리오' → 'S12'. 번호 머리가 없으면 순번으로 'X03'."""
    m = re.match(r"\s*(\d+)\s*\.", 이름)
    return "S%02d" % int(m.group(1)) if m else "X%02d" % 순번


def 행ID(sid, 행):
    return "%sR%03d" % (sid, 행)


def 행ID풀기(rid):
    """'S12R030' → ('S12', 30). 번호 꼴이 아닌 줄 ID(배치가 끼운 새 줄 따위)는 (None, None)."""
    m = re.fullmatch(r"([SX]\d+)R(\d+)", rid)
    return (m.group(1), int(m.group(2))) if m else (None, None)


def 열번호(글자):
    return column_index_from_string(글자)


def 열글자(번호):
    return get_column_letter(번호)


def 시트이름쓰기(이름):
    """수식에 쓸 시트 이름. 필요하면 작은따옴표로 싼다."""
    if re.fullmatch(r"[A-Za-z_¡-￿][A-Za-z0-9_.¡-￿]*", 이름) and \
            not re.fullmatch(r"[A-Za-z]{1,3}\d+", 이름) and not re.fullmatch(r"[Rr]\d*[Cc]\d*", 이름):
        return 이름
    return "'" + 이름.replace("'", "''") + "'"


def 짧은이름(이름, 길이=24):
    """줄 이름 → 수식에 덧붙이는 짧은 이름. 줄표·괄호·쌍점 앞에서 끊고 대괄호는 소괄호로 바꾼다."""
    글 = " ".join(str(이름 or "").split())
    m = re.match(r"^((?:\([^)]{0,8}\)\s*)?)(.*)$", 글)
    머리, 몸 = m.group(1), m.group(2)
    몸 = re.split(r"\s+[—–\-]\s+|\s*[(（:：=]|\s+—|—", 몸, 1)[0]
    글 = (머리 + 몸).strip() or 글
    return _덧글(글)[:길이].strip()


def _덧글(글):
    """대괄호 안에 덧붙일 수 있는 글로 — 대괄호는 소괄호로, 큰따옴표는 작은따옴표로."""
    return 글.replace("[", "(").replace("]", ")").replace('"', "'")


def _이름맞나(덧이름, 지금이름):
    """수식에 덧붙인 이름이 지금 줄 이름(전체 또는 짧은 이름)과 같은가."""
    덧 = " ".join(덧이름.split())
    for 이름 in 지금이름:
        if not 이름:
            continue
        온 = _덧글(" ".join(str(이름).split()))
        if 덧 == 온 or 덧 == 짧은이름(이름):
            return True
    return False


# ───────────────────────── 참조 풀기(A1 글 → 참조) ─────────────────────────
_칸 = r"(\$?)([A-Za-z]{1,3})(\$?)([0-9]{1,7})"
_re칸 = re.compile("^" + _칸 + "$")
_re범위 = re.compile("^" + _칸 + ":" + _칸 + "$")
_re열 = re.compile(r"^(\$?)([A-Za-z]{1,3}):(\$?)([A-Za-z]{1,3})$")
_re행 = re.compile(r"^(\$?)([0-9]{1,7}):(\$?)([0-9]{1,7})$")
_re시트 = re.compile(r"^(?:'((?:[^']|'')*)'|([^'!\[\]:\s]+))!(.*)$", re.S)


def _표시(열절대, 행절대):
    return ("$" if 열절대 else ".") + ("$" if 행절대 else ".")


def _유효(열, 행=None):
    try:
        if 열번호(열.upper()) > 최대열:
            return False
    except ValueError:
        return False
    return 행 is None or 1 <= int(행) <= 최대행


def 참조풀기(원문, 현재sid, 이름sid, 정의된이름=()):
    """수식의 참조 토큰 하나(예: '12. 가정_시나리오'!$G$30:$Q$30)를 참조 dict 로 바꾼다(열은 옛 열 글자)."""
    x, sid, 몸 = 0, 현재sid, 원문
    if "!" in 원문:
        m = _re시트.match(원문)
        if not m:
            return {"k": "x", "t": 원문, "why": "여러 시트에 걸친 참조 또는 다른 파일 참조"}
        이름 = m.group(1).replace("''", "'") if m.group(1) is not None else m.group(2)
        if 이름 not in 이름sid:
            return {"k": "x", "t": 원문, "why": "통합문서에 없는 시트 이름(여러 시트·다른 파일 참조 포함)"}
        x, sid, 몸 = 1, 이름sid[이름], m.group(3)
    m = _re칸.match(몸)
    if m and _유효(m.group(2), m.group(4)):
        return {"k": "c", "x": x, "r": 행ID(sid, int(m.group(4))), "c": m.group(2).upper(),
                "a": _표시(m.group(1), m.group(3))}
    m = _re범위.match(몸)
    if m and _유효(m.group(2), m.group(4)) and _유효(m.group(6), m.group(8)):
        return {"k": "r", "x": x,
                "r": 행ID(sid, int(m.group(4))), "c": m.group(2).upper(), "a": _표시(m.group(1), m.group(3)),
                "r2": 행ID(sid, int(m.group(8))), "c2": m.group(6).upper(), "a2": _표시(m.group(5), m.group(7))}
    m = _re열.match(몸)
    if m and _유효(m.group(2)) and _유효(m.group(4)):
        return {"k": "C", "x": x, "s": sid, "c": m.group(2).upper(), "a": "$" if m.group(1) else ".",
                "c2": m.group(4).upper(), "a2": "$" if m.group(3) else "."}
    m = _re행.match(몸)
    if m and 1 <= int(m.group(2)) <= 최대행 and 1 <= int(m.group(4)) <= 최대행:
        return {"k": "R", "x": x, "r": 행ID(sid, int(m.group(2))), "a": "$" if m.group(1) else ".",
                "r2": 행ID(sid, int(m.group(4))), "a2": "$" if m.group(3) else "."}
    if x == 0 and 몸 in 정의된이름:
        return {"k": "n", "name": 몸}
    if x == 1 and 몸 in 정의된이름:
        return {"k": "n", "name": 몸, "s": sid}
    return {"k": "x", "t": 원문, "why": "칸 주소도 정의된 이름도 아닌 피연산자(표 참조·모르는 이름 등)"}


_re글속좌표 = re.compile(
    r"(?<![A-Za-z0-9_$])\$?[A-Z]{1,2}\$?\d{1,4}(?![A-Za-z0-9_])|\d{1,4}\s*(?:~\s*\d{1,4}\s*)?행|\d{1,2}\s*번|[A-Z]{1,2}\s*열")


def 글속좌표(글):
    """글 안에서 좌표처럼 보이는 낱말을 찾는다(근사). 틀은 이런 글을 바꾸지 않는다."""
    return _re글속좌표.findall(글) if isinstance(글, str) else []


def _함수이름(토큰값):
    return 토큰값[:-1].upper().replace("_XLFN.", "")


def _틀짜기(수식, 풀기, 쓰임=None, 자리=None):
    """수식 글을 토큰으로 나눠 틀을 만든다. 풀기(피연산자 글) → 참조 dict.

    문자열 상수(TEXT)는 한 글자도 안 건드린다. 참조마다 감싼 함수(fn/arg)를 적는다.
    """
    조각, 글 = [], ["="]
    쌓임 = []  # [함수 이름('' = 괄호), 인자 번호]
    for t in Tokenizer(수식).items:
        if t.type == "FUNC" and t.subtype == "OPEN":
            쌓임.append([_함수이름(t.value), 0])
            if 쓰임 is not None and 쌓임[-1][0] in 좌표의존함수:
                쓰임.append({"자리": 자리, "함수": 쌓임[-1][0]})
        elif t.type == "PAREN" and t.subtype == "OPEN":
            쌓임.append(["", 0])
        elif t.type in ("FUNC", "PAREN") and t.subtype == "CLOSE":
            if 쌓임:
                쌓임.pop()
        elif t.type == "SEP" and t.subtype == "ARG" and 쌓임:
            쌓임[-1][1] += 1
        if t.type == "OPERAND" and t.subtype == "RANGE":
            참 = 풀기(t.value)
            # 감싼 함수 가운데 가장 가까운 「좌표 의존 함수·짝 범위 함수」를 적는다(IF 따위는 건너뛴다 — 엄한 쪽)
            for 함수, 인자 in reversed(쌓임):
                if 함수 in 좌표의존함수 or 함수 in 짝범위함수:
                    참["fn"], 참["arg"] = 함수, 인자
                    break
            if "".join(글):
                조각.append("".join(글))
            글 = []
            조각.append(참)
        else:
            글.append(t.value)
    if "".join(글):
        조각.append("".join(글))
    return 조각


def 수식틀(수식, 현재sid, 이름sid, 정의된이름=(), 쓰임=None, 자리=None):
    """A1 수식 글 → 틀(조각 목록). 열은 옛 열 글자 그대로다.

    쓰임 : 좌표 의존 함수가 쓰인 곳을 덧붙일 목록(없으면 안 모은다).
    자리 : 쓰임에 적을 (시트 ID, 행 ID, 열).
    """
    return _틀짜기(수식, lambda v: 참조풀기(v, 현재sid, 이름sid, 정의된이름), 쓰임, 자리)


_자리머리, _자리꼬리 = "", ""      # 토큰 나누기에 쓰는 자리표시(사용자 영역 글자)


def 호출구조(조각):
    """틀 → (호출 목록, 참조마다 감싼 호출의 길).

    호출 = {"fn": 함수 이름, "부모": 호출 번호|None, "부모인자": n, "인자": [그 인자에 바로 든 참조 번호들, …]}
    길[i] = 참조 i(조각 가운데 dict 만 센 순번)를 감싼 (호출 번호, 인자 번호) 목록 — 바깥부터.
    서로 짝인 범위(MATCH ↔ INDEX, SUMPRODUCT 의 범위들)를 찾는 데 쓴다.
    """
    글, n = [], 0
    for p in 조각:
        if isinstance(p, str):
            글.append(p)
        else:
            글.append("%s%d%s" % (_자리머리, n, _자리꼬리))
            n += 1
    호출, 길, 쌓임 = [], {}, []      # 쌓임: [호출 번호(-1 = 괄호), 인자 번호]
    for t in Tokenizer("".join(글)).items:
        if t.type == "FUNC" and t.subtype == "OPEN":
            부모 = next(((c, a) for c, a in reversed(쌓임) if c >= 0), (None, 0))
            호출.append({"fn": _함수이름(t.value), "부모": 부모[0], "부모인자": 부모[1], "인자": [[]]})
            쌓임.append([len(호출) - 1, 0])
        elif t.type == "PAREN" and t.subtype == "OPEN":
            쌓임.append([-1, 0])
        elif t.type in ("FUNC", "PAREN") and t.subtype == "CLOSE":
            if 쌓임:
                쌓임.pop()
        elif t.type == "SEP" and t.subtype == "ARG" and 쌓임:
            쌓임[-1][1] += 1
            if 쌓임[-1][0] >= 0:
                호출[쌓임[-1][0]]["인자"].append([])
        elif t.type == "OPERAND" and t.value.startswith(_자리머리):
            i = int(t.value[1:-1])
            길[i] = [(c, a) for c, a in 쌓임 if c >= 0]
            if 길[i]:
                c, a = 길[i][-1]
                호출[c]["인자"][a].append(i)
    return 호출, 길


# ───────────────────────── 손으로 쓰는 수식 문법 ─────────────────────────
# 설명은 수식문법.md. 요약:
#   [S04R054 매출액 합계]@.        같은 열            @<-1> 직전 열 · @<+1> 다음 열(꺾쇠로 싼다 — 연산자와 안 겹치게)
#   [S12R024]@$E1                  고정 열(열 ID). $ 는 절대 표시         [$S12R013]@$H1  행도 절대 표시
#   [S05R010]@.:[S05R016]@.        범위               [S04R054]@$예측    열 묶음(같은 줄의 묶음 전부)
#   [S12R031]@예측영구:[S12R033]@예측영구             여러 줄 × 열 묶음
#   [S12R005]@!$H1                 같은 시트라도 시트 이름을 붙여 쓴다
#   [S12*]@$여백:[S12*]@$단위      열 전체            [$S12R003]@*:[$S12R007]@*   행 전체
#   [S12*]!세율                    시트 안에서만 쓰는 정의된 이름         ⟦원문⟧  못 바꾸는 참조(원문 그대로)
#   [S08R141]@예측<-2>             묶음 안에서 k칸 앞 열 — 그 열이 묶음(예측)을 벗어나면 그 참조는 숫자 0 이 된다(W3a. 설계의 「@예측-k」)
_열낱 = r"(?:\.(?![첫끝])|<[+-]\d+>|\*|[A-Za-z가-힣_][A-Za-z0-9가-힣_]*<-\d+>|[A-Za-z가-힣_][A-Za-z0-9가-힣_]*(?:\.(?:첫|끝\d*|\d+))?)"
_re묶음앞 = re.compile(r"^([A-Za-z가-힣_][A-Za-z0-9가-힣_]*)<-(\d+)>$")
_낱 = r"\[(\$?)([^\]\[\s*]+)(\*?)(?:[ \t]+([^\]\[]*))?\]@(!?)(\$?)(" + _열낱 + ")"
_re손 = re.compile(_낱 + "(?::" + _낱 + ")?" +
                  r"|\[([^\]\[\s*]+)\*\]!([A-Za-z가-힣_\\][A-Za-z0-9가-힣_.\\]*)" +
                  r"|⟦([^⟧]*)⟧")
_re문자열 = re.compile(r'"(?:[^"]|"")*"')
# 옛 이웃 열 표기(@-1 · @+1) — 받지 않는다. 「[행]@.-1」(같은 열에서 1을 뺀다)과 점 하나 차이라 꺾쇠 꼴(@<-1>)로 바꿨다
_re옛이웃 = re.compile(r"(\][ \t]*@!?\$?)([+-]\d+)")


def 옛이웃열고치기(글):
    """손 수식 글의 옛 이웃 열 표기(@-1 · @+1)를 꺾쇠 꼴(@<-1> · @<+1>)로 고친 글. 문자열 상수 안은 건드리지 않는다.

    → (고친 글, 고친 곳 수). 옛 형식의 명세를 옮길 때만 쓴다(줄무늬.옛꼴고치기).
    """
    if not isinstance(글, str) or not 글.startswith("="):
        return 글, 0
    낱, 앞, 수 = [], 0, 0
    for m in list(_re문자열.finditer(글)) + [None]:
        끝 = m.start() if m else len(글)
        덩이, n = _re옛이웃.subn(lambda x: "%s<%s>" % (x.group(1), x.group(2)), 글[앞:끝])
        낱.append(덩이)
        수 += n
        if m:
            낱.append(m.group(0))
            앞 = m.end()
    return "".join(낱), 수


# ───────────────────────── 자리 이름(묶음의 몇째 열) ─────────────────────────
# 「묶음.첫」 · 「묶음.끝」 · 「묶음.k」(앞에서 k째, 1부터) · 「묶음.끝k」(뒤에서 k째 — 끝 = 끝1).
# 기간 열을 가정 파일이 정하므로 시간축 열을 열 ID 로 못 박아 적지 않는다 — 평가기준일 열은 「실적.끝」, 첫 예측 열은 「예측.첫」,
# 최종 예측 열은 「예측.끝」, 열 별칭이 놓이는 값 칸은 「시간.1」~「시간.5」. 틀에는 낱말 그대로 싣고 짓기가 새 배치에서 푼다.
_re자리 = re.compile(r"^(.+)\.(?:(첫)|끝(\d*)|(\d+))$")
# 기간 축의 열 갈래 — 열 등록부의 「갈래」·「구간」에 적는다(「종류」는 실적 · 예측 · 영구 그대로다). 묶음 표에 종류처럼 적을 수 있고,
# 회차의 축에 그 갈래의 열이 없으면 그 묶음은 비어 있다(누계 실적 · 잔여 기간 열은 평가기준일이 결산일이 아닐 때만, 수렴 열은 수렴연수가 있을 때만 선다)
축갈래 = ("FY실적", "누계실적", "잔여예측", "연간예측", "영구", "상세", "수렴", "달아님")


def 자리풀기(낱):
    """「묶음.첫」「묶음.끝2」「묶음.3」 → (묶음 이름, k). k > 0 = 앞에서 k째, k < 0 = 뒤에서 |k|째. 자리 이름이 아니면 None."""
    m = _re자리.match(낱) if isinstance(낱, str) else None
    if not m:
        return None
    if m.group(2):
        return m.group(1), 1
    if m.group(4):
        return (m.group(1), int(m.group(4))) if int(m.group(4)) >= 1 else None
    k = int(m.group(3)) if m.group(3) else 1
    return (m.group(1), -k) if k >= 1 else None


def 자리열(열들, k):
    """묶음의 열 목록에서 k째(k > 0 앞에서, k < 0 뒤에서) 열 ID. 없으면 None."""
    if not 열들 or k == 0 or abs(k) > len(열들):
        return None
    return 열들[k - 1] if k > 0 else 열들[k]


class 문맥:
    """손 수식을 읽고 쓰는 데 필요한 표. 줄무늬·짓기가 명세에서 만든다.

    행소속   : 행 ID → 시트 ID
    행이름   : 행 ID → 지금 이름(덧붙인 이름 견주기용. 여러 이름이면 목록)
    행쓰임   : 행 ID → 쓰임 이름(그 줄의 열 별칭 묶음. 없으면 기본)
    열순서   : 시트 ID → [열 ID …](명세의 열 순서)
    새순서   : 시트 ID → [열 ID …](배치가 놓은 새 열 순서 — 짓기만 준다. 배치가 더한 새 열이 들어 있다)
    열종류   : 시트 ID → {열 ID: 종류}
    축       : 시트 ID → [시간축을 이루는 열 종류 …]
    묶음     : 시트 ID → {묶음 이름: [열 종류 …]}
    쓰임     : 시트 ID → {쓰임 이름: {별칭: 열 ID}}
    정의된이름: 통합문서의 정의된 이름
    """

    def __init__(self):
        self.행소속, self.행이름, self.행쓰임 = {}, {}, {}
        self.열순서, self.열종류, self.축, self.묶음, self.쓰임 = {}, {}, {}, {}, {}
        self.새순서 = {}
        self.열덧 = {}            # 시트 ID → {열 ID: {갈래 · 구간 …}} — 기간 축의 열 갈래(FY실적 · 누계실적 · 잔여예측 · 연간예측 · 상세 · 수렴 · 달아님)
        self.열기간 = {}          # 시트 ID → {열 ID: 그 열의 기간 속성(표기 · 구분 · 종료일 · 시작일 · 개월 · 구간 · 회계연도 …)} — 「축값」이 읽는다
        self.기간틀 = set()       # 시간축 열을 기간 축에서 받는 시트(열 등록부에 「갈래」가 있는 시트) — 열쇠와 자리 이름을 적은 대로 지킨다
        self.칸이름 = {}          # (행 ID, 열 ID) → 그 칸에 덧붙일 이름(줄 이름과 다른 둘째 이름표가 있는 칸)
        self.줄덧이름 = {}        # 행 ID → [그 줄의 칸 이름들]
        self.정의된이름 = set()
        self.별칭 = {}            # 배치의 「별칭」 표: 이름 → 행 ID
        self.이름경고 = {}        # (행 ID, 덧붙인 이름) → 횟수
        self.엄한행 = False       # 참 = 등록부에 없는 행 ID 를 오류로(줄 무늬 명세). 거짓 = 그 시트의 번호 꼴이면 받는다(옛 xlsx 에서 뽑은 것)
        self.허용함수 = set()     # 엑셀 함수 목록에 없지만 받는 함수 이름(옛 xlsx 에 있던 것 — 책.json 의 「허용함수」)
        self._기억 = {}

    def 소속(self, rid):
        """행 ID → 시트 ID. 등록부 밖의 줄(그 시트의 번호 꼴이지만 명세에 없는 줄)도 시트는 안다. 모르면 None."""
        sid = self.행소속.get(rid)
        if sid is None:
            sid = 행ID풀기(rid)[0]
            if sid not in self.열순서:
                return None
        return sid

    # ── 열 ──
    def 묶음열(self, sid, 이름):
        """묶음 이름 → 그 묶음의 열 ID 목록(명세의 열 순서). 없으면 None."""
        종류들 = self.묶음.get(sid, {}).get(이름)
        if 종류들 is None:
            return None
        키 = ("묶", sid, 이름)
        if 키 not in self._기억:
            self._기억[키] = [c for c in self.열순서.get(sid, []) if self.든다(sid, c, 종류들)]
        return self._기억[키]

    def 든다(self, sid, cid, 종류들):
        """그 열이 종류들(묶음 표의 한 줄) 가운데 하나에 드는가 — 열의 「종류」 또는 기간 축의 갈래(「갈래」·「구간」)로 본다."""
        return self.열종류.get(sid, {}).get(cid) in 종류들 or bool(self.열덧.get(sid, {}).get(cid, ()) and
                                                                  set(종류들) & self.열덧[sid][cid])

    def 축열(self, sid):
        키 = ("축", sid)
        if 키 not in self._기억:
            종, 축 = self.열종류.get(sid, {}), set(self.축.get(sid, ()))
            순 = self.새순서.get(sid) or self.열순서.get(sid, [])
            self._기억[키] = [c for c in 순 if 종.get(c) in 축]
        return self._기억[키]

    def 차례(self, sid, cid):
        """직전·다음 열을 셀 때 쓰는 열 차례.

        시간축 열이면 (새 배치의) 시간축 열끼리 · 명세에 있던 다른 열이면 명세의 열 순서 ·
        배치가 더한 새 열(시간축 아님)이면 새 배치의 열 순서.
        """
        축 = self.축열(sid)
        if cid in 축:
            return 축
        if cid in self.열순서.get(sid, ()):
            return self.열순서[sid]
        return self.새순서.get(sid, [])

    def 이웃열(self, sid, cid, k):
        차 = self.차례(sid, cid)
        if cid not in 차:
            raise 손오류("이웃 열을 셀 수 없다: %s 의 %s" % (sid, cid))
        n = 차.index(cid) + k
        if not 0 <= n < len(차):
            raise 손오류("이웃 열이 없다: %s 의 %s%+d" % (sid, cid, k))
        return 차[n]

    def 간격(self, sid, 이칸열, 대상열):
        """이 칸의 열에서 대상 열 ID 까지 몇 칸인가(같은 차례 안에서). 못 세면 None."""
        차 = self.차례(sid, 이칸열)
        if 이칸열 in 차 and 대상열 in 차:
            return 차.index(대상열) - 차.index(이칸열)
        return None

    def 별칭풀기(self, sid, rid, 낱):
        """열 낱말(열 ID · 그 줄 쓰임의 별칭 · 묶음.첫/끝) → 열 ID. 모르면 None.

        별칭은 그 줄의 쓰임에서만 찾는다. 다른 쓰임에서 빌려 풀지 않는다 — 시점 줄의 「@값」이 비관 칸이 되는 일이 없게.
        """
        if 낱 in self.열종류.get(sid, {}):
            return 낱
        표 = self.쓰임.get(sid, {})
        쓰 = self.행쓰임.get(rid) if rid else None
        if 쓰 and 낱 in 표.get(쓰, {}):
            return 표[쓰][낱]
        자 = 자리풀기(낱)
        if 자 and (self.묶음열(sid, 자[0]) or (sid in self.기간틀 and 자[0] in self.묶음.get(sid, {}))):
            return 낱                     # 묶음의 몇째 열(자리 이름) — 짓기가 새 배치에서 푼다
        return None

    def 별칭까닭(self, sid, rid, 낱):
        """별칭풀기가 None 일 때 사람에게 보일 까닭."""
        표 = self.쓰임.get(sid, {})
        쓰 = self.행쓰임.get(rid) if rid else None
        가진 = sorted(이름 for 이름, m in 표.items() if 낱 in m)
        if 가진:
            return "%s 의 쓰임(%s)에 없는 별칭 「%s」 — 이 별칭은 쓰임 %s 의 것이다" % (
                rid or sid, 쓰 or "없음", 낱, "·".join(가진))
        return "%s 의 열 「%s」 를 모른다(열 ID·그 줄 쓰임의 별칭·묶음 이름이 아니다)" % (rid or sid, 낱)

    def 별칭쓰기(self, sid, rid, cid):
        """열 ID → 그 줄의 쓰임에 맞는 별칭(없으면 열 ID 그대로)."""
        쓰 = self.행쓰임.get(rid)
        if 쓰:
            키 = ("역", sid, 쓰)
            if 키 not in self._기억:
                self._기억[키] = {v: k for k, v in self.쓰임.get(sid, {}).get(쓰, {}).items()}
            return self._기억[키].get(cid, cid)
        return cid

    def 묶음찾기(self, sid, c, c2):
        """열 ID 두 끝이 어떤 묶음(열 둘 이상)의 첫·끝과 같으면 그 묶음 이름."""
        for 이름 in self.묶음.get(sid, {}):
            열 = self.묶음열(sid, 이름)
            if len(열) >= 2 and 열[0] == c and 열[-1] == c2:
                return 이름
        return None

    def 이름적기(self, rid, 덧이름):
        if 덧이름 and not _이름맞나(덧이름, list(self.행이름.get(rid) or ()) + list(self.줄덧이름.get(rid) or ())):
            키 = (rid, " ".join(덧이름.split()))
            self.이름경고[키] = self.이름경고.get(키, 0) + 1


def 손수식틀(글, 이칸열, 현재sid, 문):
    """손 수식 글 → 틀. 이칸열 = 이 수식이 놓이는 칸의 열 ID. 문 = 문맥.

    문자열 상수 안은 건드리지 않는다. 좌표(G54 따위)를 그대로 쓰면 오류다.
    """
    자리표, 낱, 끝 = {}, [], 0
    if not isinstance(글, str) or not 글.startswith("="):
        raise 손오류("수식 글이 「=」로 시작하지 않는다: %s" % str(글)[:80], 종류="수식 꼴")

    def 행(절대, 이름, 덧):
        rid = 문.별칭.get(이름, 이름)
        if 문.소속(rid) is None:
            raise 손오류("[%s] 를 행 ID 로 풀 수 없다" % 이름)
        if 문.엄한행 and rid not in 문.행소속:
            raise 손오류("명세에 없는 행 ID 를 가리킨다: %s" % rid, 종류="모르는 행·열")
        문.이름적기(rid, 덧)
        return rid

    def 열(sid, rid, 낱말):
        if 낱말 == "." or 낱말[0] == "<":
            cid = 이칸열 if 낱말 == "." else 문.이웃열(현재sid, 이칸열, int(낱말[1:-1]))
            if cid not in 문.열종류.get(sid, {}):
                raise 손오류("%s 에는 열 %s 가 없다(@%s 로 부른 열)" % (sid, cid, 낱말))
            return cid
        cid = 문.별칭풀기(sid, rid, 낱말)
        if cid is None:
            raise 손오류(문.별칭까닭(sid, rid, 낱말))
        return cid

    def 적은법(sid, 낱말):
        if 낱말 == ".":
            return "."
        if 낱말[0] == "<":
            return "n"
        if 낱말 in 문.열종류.get(sid, {}):
            return "i"
        return "e" if 자리풀기(낱말) else "a"

    def 한낱(m, i):
        """정규식 묶음 i~i+6 → (행 절대, 행|시트, 별표, 덧이름, 시트붙임, 열 절대, 열 낱말)"""
        return m.group(i), m.group(i + 1), m.group(i + 2), m.group(i + 3), m.group(i + 4), m.group(i + 5), m.group(i + 6)

    def 참조(m):
        if m.group(17) is not None:
            return {"k": "x", "t": m.group(17), "why": "손 수식에 원문 그대로 적은 참조"}
        if m.group(15) is not None:
            if m.group(16) not in 문.정의된이름:
                raise 손오류("정의된 이름이 아니다: %s" % m.group(16))
            return {"k": "n", "name": m.group(16), "s": m.group(15)}
        행절, 이름, 별, 덧, 붙임, 열절, 열낱 = 한낱(m, 1)
        둘 = 한낱(m, 8) if m.group(9) is not None else None
        if 별:                                   # 열 전체: [S12*]@$여백:[S12*]@$단위
            sid = 이름
            if sid not in 문.열순서 or 둘 is None or not 둘[2] or 둘[1] != sid:
                raise 손오류("열 전체는 [시트*]@열:[시트*]@열 로 적는다: %s" % m.group(0))
            return {"k": "C", "x": 1 if (붙임 or sid != 현재sid) else 0, "s": sid,
                    "c": 열(sid, None, 열낱), "a": "$" if 열절 else ".",
                    "c2": 열(sid, None, 둘[6]), "a2": "$" if 둘[5] else "."}
        r1 = 행(행절, 이름, 덧)
        sid = 문.소속(r1)
        x = 1 if (붙임 or sid != 현재sid) else 0
        앞 = _re묶음앞.match(열낱)
        if 앞:                                   # 묶음 안에서 k칸 앞 열: [S08R141]@예측<-2> — 묶음을 벗어나면 숫자 0
            if 둘 is not None:
                raise 손오류("「@묶음<-k>」 는 범위의 끝으로 못 쓴다: %s" % m.group(0))
            묶 = 문.묶음열(sid, 앞.group(1))
            if 묶 is None:
                raise 손오류("%s 에 묶음 「%s」 이 없다(@%s 로 부른 열)" % (sid, 앞.group(1), 열낱))
            차 = 문.차례(현재sid, 이칸열)
            if 이칸열 not in 차:
                raise 손오류("이웃 열을 셀 수 없다: %s 의 %s (@%s)" % (현재sid, 이칸열, 열낱))
            n = 차.index(이칸열) - int(앞.group(2))
            if n < 0 or 차[n] not in 묶:
                return None
            return {"k": "c", "x": x, "r": r1, "c": 차[n], "a": _표시(열절, 행절), "w": "n"}
        if 열낱 == "*":                           # 행 전체: [$S12R003]@*:[$S12R007]@*
            if 둘 is None or 둘[6] != "*":
                raise 손오류("행 전체는 [행]@*:[행]@* 로 적는다: %s" % m.group(0))
            return {"k": "R", "x": x, "r": r1, "a": "$" if 행절 else ".",
                    "r2": 행(둘[0], 둘[1], 둘[3]), "a2": "$" if 둘[0] else "."}
        묶 = 문.묶음열(sid, 열낱)
        if 묶 is not None:                        # 열 묶음: 같은 줄, 또는 여러 줄 × 묶음
            if not 묶:
                raise 손오류("빈 열 묶음: %s 의 %s%s" % (sid, 열낱, " — 이 회차의 기간 축에 그 갈래의 열이 없다. 그 열이 있을 때만 놓이는 "
                                                    "무늬(열쇠가 같은 갈래인 무늬)에서만 읽는다" if sid in 문.기간틀 else ""))
            r2, a2 = r1, _표시(열절, 행절)
            if 둘 is not None:
                if 둘[6] != 열낱:
                    raise 손오류("범위의 두 끝이 같은 묶음이어야 한다: %s" % m.group(0))
                r2, a2 = 행(둘[0], 둘[1], 둘[3]), _표시(둘[5], 둘[0])
            return {"k": "r", "x": x, "r": r1, "c": 묶[0], "a": _표시(열절, 행절),
                    "r2": r2, "c2": 묶[-1], "a2": a2, "g": 열낱}
        if 둘 is None:
            return {"k": "c", "x": x, "r": r1, "c": 열(sid, r1, 열낱), "a": _표시(열절, 행절), "w": 적은법(sid, 열낱)}
        r2 = 행(둘[0], 둘[1], 둘[3])
        if 문.소속(r2) != sid:
            raise 손오류("범위의 두 끝이 다른 시트다: %s" % m.group(0))
        return {"k": "r", "x": x, "r": r1, "c": 열(sid, r1, 열낱), "a": _표시(열절, 행절),
                "r2": r2, "c2": 열(sid, r2, 둘[6]), "a2": _표시(둘[5], 둘[0]),
                "w": 적은법(sid, 열낱), "w2": 적은법(sid, 둘[6])}

    # 문자열 상수 밖에서만 참조를 찾아 자리표시로 바꾼다
    구간, 앞 = [], 0
    for m in _re문자열.finditer(글):
        구간.append((앞, m.start(), True))
        구간.append((m.start(), m.end(), False))
        앞 = m.end()
    구간.append((앞, len(글), True))
    for 시작, 마침, 찾기 in 구간:
        덩이 = 글[시작:마침]
        if not 찾기:
            낱.append(덩이)
            continue
        m = _re옛이웃.search(덩이)
        if m:       # 「[행]@-1」 — 옛 표기. 「[행]@.-1」 의 점을 빠뜨린 것일 수도 있다. 어느 쪽인지는 적는 사람이 정한다
            raise 손오류("이웃 열을 옛 표기로 적었다(「%s」): 직전 열은 @<-1> · 다음 열은 @<+1> 로 적는다. 같은 열에서 숫자를 빼는 것이면 「@.%s」 — %s"
                       % (덩이[max(0, m.start() - 12):m.end()], m.group(2), 글[:100]), 종류="수식 꼴")
        끝 = 0
        for m in _re손.finditer(덩이):
            낱.append(덩이[끝:m.start()])
            한참 = 참조(m)
            if 한참 is None:      # 묶음을 벗어난 「@묶음<-k>」 — 그 참조 자리에 숫자 0 을 적는다(틀에는 글 「0」으로 남는다)
                낱.append("0")
            else:
                키 = "%s%d%s" % (_자리머리, len(자리표), _자리꼬리)
                자리표[키] = 한참
                낱.append(키)
            끝 = m.end()
        낱.append(덩이[끝:])

    def 풀기(값):
        if 값 in 자리표:
            return 자리표[값]
        if 값 in 문.정의된이름:
            return {"k": "n", "name": 값}
        raise 손오류("손 수식에 풀 수 없는 피연산자가 있다(좌표를 그대로 썼거나 모르는 이름): %s" % 값)

    몸 = "".join(낱)
    수식꼴점검(몸, 글, 문.허용함수)
    return _틀짜기(몸, 풀기)


def 틀의함수(조각):
    """틀에 쓰인 함수 이름들(수식에 적힌 그대로)."""
    글 = "".join(p if isinstance(p, str) else "A1" for p in 조각)
    try:
        return {t.value[:-1] for t in Tokenizer(글).items if t.type == "FUNC" and t.subtype == "OPEN"}
    except Exception:
        return set()


def _맨이름(이름):
    """수식에 적힌 함수 이름 → 접두(_xlfn. · _xlws.)를 뗀 대문자 이름."""
    return _함수이름(이름 + "(").replace("_XLWS.", "")


def 모르는함수(이름, 허용=()):
    """수식에 적힌 함수 이름이 엑셀 함수 목록에도 허용 목록에도 없는가."""
    return _맨이름(이름) not in 함수이름 and 이름.upper() not in {x.upper() for x in 허용}


_re새함수 = re.compile(r"(?<![A-Za-z0-9_.])(?:%s)\(" % "|".join(
    re.escape(x) for x in sorted(새함수, key=len, reverse=True)), re.I)


def 새함수접두(글):
    """낸 수식 글에서 2007년 표준 뒤에 나온 함수 이름 앞에 「_xlfn.」(SORT · FILTER 는 「_xlfn._xlws.」)을 붙인다.

    이미 접두가 붙은 것 · 문자열 상수 안의 글은 그대로 둔다. 그런 함수가 없으면 글을 건드리지 않는다. → (글, 붙인 함수 이름들)
    """
    if not _re새함수.search(글):
        return 글, []
    낱, 붙인 = ["="], []
    for t in Tokenizer(글).items:
        v = t.value
        if t.type == "FUNC" and t.subtype == "OPEN":
            이름 = v[:-1].upper()
            if 이름 in 새함수:           # 접두가 붙어 있으면 이름이 _XLFN.… 이라 여기 안 걸린다
                v = ("_xlfn._xlws." if 이름 in _시트접두함수 else "_xlfn.") + v
                붙인.append(이름)
        낱.append(v)
    return "".join(낱), 붙인


def 수식꼴점검(몸, 원문=None, 허용함수=()):
    """손 수식 글의 꼴 — 토큰의 차례 · 괄호 짝 · 함수 이름과 인자 수 · #REF!. 어긋나면 배치오류(종류 「수식 꼴」).

    엑셀은 이런 수식이 든 파일을 열지 못하거나(괄호 · 연산자 둘 · 빈 괄호 · 인자 수 · 모르는 함수), 오류값을 내거나
    (연산자 빠짐 → #NULL! · 함수 밖의 쉼표 → #VALUE!), 깨진 참조를 그대로 싣는다(#REF!). 어느 수식인지 엑셀은 알려 주지 않는다.
    보는 것: 값(피연산자 · 닫는 괄호) 뒤에는 연산자 · 쉼표 · 닫는 괄호가 온다 · 연산자 뒤에는 값이 온다(머리의 + − 는 된다) ·
    빈 괄호 · 함수 밖의 쉼표 · 자주 쓰는 함수의 인자 수(인자수표) · 함수 이름. 빈 인자(IF(a,1,))와 퍼센트(A%)는 엑셀이 받으므로 둔다.
    몸 = 참조를 자리표시로 바꾼 글(문자열 상수는 그대로).
    """
    보일 = (원문 if 원문 is not None else 몸)[:120]

    def 틀림(설명):
        raise 손오류("%s: %s" % (설명, 보일), 종류="수식 꼴")

    def 보임(값):
        return "참조" if _자리머리 in 값 else 값[:20]

    try:
        토큰 = Tokenizer(몸).items
    except Exception as e:      # 닫지 않은 큰따옴표 · 남는 닫는 괄호
        raise 손오류("수식 글을 읽을 수 없다(따옴표·괄호 짝): %s — %s" % (보일, str(e)[:60]), 종류="수식 꼴")
    허용 = {x.upper() for x in 허용함수}
    쌓임 = []        # 열린 괄호: [갈래(FUNC · PAREN · ARRAY), 함수 이름, 쉼표 수]
    있음 = False     # 바로 앞에 값(피연산자 · 닫는 괄호 · %)이 있다 — 다음에는 연산자 · 쉼표 · 닫는 괄호가 와야 한다
    앞 = None        # 바로 앞의 토큰(빈칸은 건너뛴다)
    for t in 토큰:
        종, 갈 = t.type, t.subtype
        if 종 == "WHITE-SPACE":
            continue
        if 종 == "OPERAND":
            if 있음:
                틀림("연산자가 빠졌다(「%s」 앞 — 두 값이 연산자 없이 이어진다)" % 보임(t.value))
            if 갈 == "ERROR" and t.value.upper() == "#REF!":
                틀림("수식에 #REF! 가 적혀 있다(깨진 참조)")
            있음 = True
        elif 종 in ("FUNC", "PAREN", "ARRAY") and 갈 == "OPEN":
            if 있음:
                틀림("연산자가 빠졌다(여는 괄호 「%s」 앞)" % 보임(t.value))
            이름 = t.value[:-1] if 종 == "FUNC" else ""
            if 종 == "FUNC":
                if _자리머리 in 이름:
                    틀림("참조 바로 뒤에 여는 괄호가 온다(연산자가 빠졌다)")
                if _맨이름(이름) in 못쓰는함수 and 이름.upper() not in 허용:
                    틀림("%s 는 손 수식으로 적지 못한다(이름 인자에 _xlpm. 접두가 필요한 함수다)" % _맨이름(이름))
                if 모르는함수(이름, 허용함수):
                    틀림("모르는 함수 이름 「%s」" % 이름)
            쌓임.append([종, 이름, 0])
            있음 = False
        elif 종 in ("FUNC", "PAREN", "ARRAY") and 갈 == "CLOSE":
            if not 쌓임:
                틀림("괄호 짝이 안 맞는다(남는 닫는 괄호)")
            갈래, 이름, 쉼표 = 쌓임.pop()
            바로연 = 앞 is not None and 앞.type == 갈래 and 앞.subtype == "OPEN"
            if not 있음:
                if 바로연 and 갈래 != "FUNC":
                    틀림("빈 괄호" if 갈래 == "PAREN" else "빈 배열 상수")
                elif not 바로연 and not (갈래 == "FUNC" and 앞.type == "SEP"):
                    틀림("연산자 뒤에 값이 없다(「%s」 뒤에 바로 닫는 괄호)" % 앞.value)
            if 갈래 == "FUNC":
                수 = 0 if 바로연 else 쉼표 + 1
                범위 = 인자수표.get(_맨이름(이름))
                if 범위 and not 범위[0] <= 수 <= 범위[1]:
                    틀림("%s 의 인자 수가 맞지 않는다(%d개 — %s). 닫는 괄호의 자리를 본다" % (
                        _맨이름(이름), 수, "%d개여야 한다" % 범위[0] if 범위[0] == 범위[1] else "%d~%d개여야 한다" % 범위))
            있음 = True
        elif 종 == "SEP":
            if not 쌓임 or 쌓임[-1][0] == "PAREN":
                틀림("함수 밖에 쉼표가 있다")
            if not 있음 and not (쌓임[-1][0] == "FUNC" and (앞.type == "SEP" or (앞.type == "FUNC" and 앞.subtype == "OPEN"))):
                틀림("연산자 뒤에 값이 없다(「%s」 뒤에 바로 쉼표)" % 앞.value)
            if 갈 == "ARG":
                쌓임[-1][2] += 1
            있음 = False
        elif 종 == "OPERATOR-INFIX":
            if t.value == ",":
                틀림("함수 밖에 쉼표가 있다(여러 범위를 쉼표로 잇는 합집합 참조는 받지 않는다)")
            if not 있음:
                틀림("연산자가 둘 이어졌다(「%s%s」)" % (앞.value, t.value) if 앞 is not None and 앞.type.startswith("OPERATOR")
                    else "값 없이 연산자 「%s」 가 온다(수식의 머리 · 여는 괄호 · 쉼표 바로 뒤)" % t.value)
            있음 = False
        elif 종 == "OPERATOR-POSTFIX":
            if not 있음:
                틀림("값 없이 「%s」 가 온다" % t.value)
        elif 종 == "OPERATOR-PREFIX":
            if 있음:
                틀림("연산자가 빠졌다(「%s」 앞)" % t.value)
        앞 = t
    if 쌓임:
        틀림("괄호 짝이 안 맞는다(안 닫은 괄호 %d개)" % len(쌓임))
    if 앞 is None:
        틀림("빈 수식이다")
    if not 있음:
        틀림("수식이 연산자·쉼표로 끝난다(「%s」)" % 앞.value)


def 손수식쓰기(조각, 이칸열, 현재sid, 문, 꼴=None, 이름붙이기=True, 적은대로=False):
    """틀 → 손 수식 글.

    꼴 : 참조의 열 끝점마다 적는 법 — "상대"(@. · @<-1> · @<+1>) 또는 "고정"(열 ID). 끝점 순서대로의 목록.
         안 주면 스스로 고른다(같은 열은 @. , 시간축에서 바로 옆이면 @<-1>·@<+1> , 그 밖은 열 ID).
    적은대로 : 손 수식에서 읽은 틀을 그 칸에서 다시 적을 때 — 참조마다 적혀 있던 법(틀의 w · w2)을 지킨다.
         같은 열 · 이웃 열로 적은 것은 간격이 몇 칸이든 그대로 상대로, 자리 이름 · 별칭 · 열 ID 로 적은 것은 그대로 적는다.
    """
    글, 끝점 = [], [0]
    본이름 = set()
    법기억 = [None]

    def 행(rid, 절대, cid=None):
        덧 = ""
        if 이름붙이기:                                # 한 수식에서 같은 줄(같은 이름)은 처음 한 번만 이름을 붙인다
            이름 = 문.칸이름.get((rid, cid)) or 문.행이름.get(rid)
            이름 = 이름[0] if isinstance(이름, (list, tuple)) and 이름 else 이름
            짧 = 짧은이름(이름) if 이름 and not str(이름).startswith("=") else ""
            if 짧 and (rid, 짧) not in 본이름:
                덧 = " " + 짧
                본이름.add((rid, 짧))
        return "[%s%s%s]" % ("$" if 절대 else "", rid, 덧)

    def 열(sid, rid, cid, 절대):
        n = 끝점[0]
        끝점[0] += 1
        적힌 = 법기억[0]
        if 적은대로 and 적힌 in (".", "n"):
            간 = 문.간격(현재sid, 이칸열, cid)
            if 간 is not None and (간 == 0) == (적힌 == "."):
                return ("$" if 절대 else "") + ("." if 간 == 0 else "<%+d>" % 간)
        if 절대 or (적은대로 and 적힌 in ("i", "a", "e")):
            return ("$" if 절대 else "") + 문.별칭쓰기(sid, rid, cid)
        법 = 꼴[n] if 꼴 is not None else None
        간 = 문.간격(현재sid, 이칸열, cid)
        if 법 is None:
            축 = 문.축열(현재sid)
            법 = "상대" if 간 == 0 or (간 in (-1, 1) and 이칸열 in 축 and cid in 축) else "고정"
        if 법 == "상대" and 간 is not None:
            return "." if 간 == 0 else "<%+d>" % 간
        return 문.별칭쓰기(sid, rid, cid)

    for p in 조각:
        if isinstance(p, str):
            글.append(p)
            continue
        k = p["k"]
        if k == "x":
            글.append("⟦%s⟧" % p["t"])
        elif k == "n":
            글.append(("[%s*]!" % p["s"] if p.get("s") else "") + p["name"])
        elif k == "C":
            붙 = "!" if (p.get("x") and p["s"] == 현재sid) else ""
            글.append("[%s*]@%s%s%s:[%s*]@%s%s" % (p["s"], 붙, "$" if p["a"] == "$" else "", p["c"],
                                                 p["s"], "$" if p["a2"] == "$" else "", p["c2"]))
        elif k == "R":
            sid = 문.소속(p["r"])
            붙 = "!" if (p.get("x") and sid == 현재sid) else ""
            글.append("%s@%s*:%s@*" % (행(p["r"], p["a"] == "$"), 붙, 행(p["r2"], p["a2"] == "$")))
        else:
            sid = 문.소속(p["r"])
            붙 = "!" if (p.get("x") and sid == 현재sid) else ""
            if p.get("g"):
                한 = "%s@%s%s%s" % (행(p["r"], p["a"][1] == "$", p["c"]), 붙, "$" if p["a"][0] == "$" else "", p["g"])
                if p["r2"] != p["r"] or p["a2"] != p["a"]:
                    한 += ":%s@%s%s" % (행(p["r2"], p["a2"][1] == "$", p["c2"]), "$" if p["a2"][0] == "$" else "", p["g"])
                끝점[0] += 2
                글.append(한)
                continue
            법기억[0] = p.get("w")
            한 = "%s@%s%s" % (행(p["r"], p["a"][1] == "$", p["c"]), 붙, 열(sid, p["r"], p["c"], p["a"][0] == "$"))
            if k == "r":
                법기억[0] = p.get("w2")
                한 += ":%s@%s" % (행(p["r2"], p["a2"][1] == "$", p["c2"]), 열(sid, p["r2"], p["c2"], p["a2"][0] == "$"))
            글.append(한)
    return "".join(글)


def 틀같나(가, 나):
    """두 틀이 같은가(「why」 설명 글은 견주지 않는다)."""
    if len(가) != len(나):
        return False
    for a, b in zip(가, 나):
        if isinstance(a, str) or isinstance(b, str):
            if a != b:
                return False
        elif {k: v for k, v in a.items() if k not in 안견줌} != {k: v for k, v in b.items() if k not in 안견줌}:
            return False
    return True


안견줌 = ("why", "w", "w2")      # 틀을 견줄 때 보지 않는 열쇠(설명 글 · 열을 적은 법)


# ───────────────────────── 서식 직렬화 ─────────────────────────
from openpyxl.styles import Font, Border, Alignment, Protection  # noqa: E402
from openpyxl.styles.fills import Fill  # noqa: E402
from openpyxl.xml.functions import tostring, fromstring  # noqa: E402


def 서식글(칸):
    """칸의 서식을 XML 글 다섯 개 + 숫자 서식으로 낸다(옛 서식을 있는 그대로 옮기는 길)."""
    return {
        "글꼴": tostring(copy(칸.font).to_tree("font")).decode("utf-8"),
        "채움": tostring(copy(칸.fill).to_tree()).decode("utf-8"),
        "테두리": tostring(copy(칸.border).to_tree("border")).decode("utf-8"),
        "맞춤": tostring(copy(칸.alignment).to_tree("alignment")).decode("utf-8"),
        "보호": tostring(copy(칸.protection).to_tree("protection")).decode("utf-8"),
        "숫자서식": 칸.number_format,
        "따옴표머리": bool(칸.quotePrefix),
    }


def 서식객체(글):
    return {
        "font": Font.from_tree(fromstring(글["글꼴"])),
        "fill": Fill.from_tree(fromstring(글["채움"])),
        "border": Border.from_tree(fromstring(글["테두리"])),
        "alignment": Alignment.from_tree(fromstring(글["맞춤"])),
        "protection": Protection.from_tree(fromstring(글["보호"])),
        "number_format": 글["숫자서식"],
    }

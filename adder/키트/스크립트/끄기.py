# -*- coding: utf-8 -*-
"""끄기 — 이 판에서 쓰지 않는 점검 · 문단 · 도구를 끈다.

산식 개편에서 엔진이 옛 경로(전개 함수와 그 함수가 채우던 블록 · 스위치)를 걷었다. 그 경로를 읽던 점검과
레터 문단, 도구는 새 구조에 맞춰 다시 쓰거나 지워야 한다. 그 일이 끝날 때까지 여기의 두 도구로 꺼 둔다.

  @이판에서안씀("까닭", 값=…)     함수를 끈다. 불려도 몸을 돌리지 않고 `값` 을 돌려준다
                                  (값이 함수면 받은 인자로 불러 그 결과를 돌려준다)
  @이판에서안씀("까닭", 꼴="점검")  자체검사의 점검 함수를 끈다 — (오류 없음, 경보 없음, 목록 한 줄)을 돌려준다
  if 이판에서쓰나("까닭"):         문단을 끈다. 늘 거짓이라 그 아래 줄이 돌지 않는다

끈 자리의 옛 코드는 그대로 둔다. 다시 쓰는 묶음이 그 코드를 보고 고친다.

  python 스크립트/끄기.py          # 이 폴더의 스크립트에서 꺼진 함수와 문단을 찾아 찍는다(코드를 돌리지 않고 읽기만 한다)
"""
import copy
import functools

안씀글 = "이 판에서는 쓰지 않습니다"
꺼진목록 = []          # [(모듈 이름, 함수 이름, 까닭)] — 불러온 모듈에서 꺼진 함수


def 이판에서안씀(까닭, 값=None, 꼴=None):
    """함수를 끄는 장식. 까닭은 한 줄로 적는다(무엇을 읽던 함수인지)."""
    def 장식(fn):
        @functools.wraps(fn)
        def 꺼진(*a, **k):
            if 꼴 == "점검":
                return [], [], ["  %s — %s" % (안씀글, 까닭)]
            if callable(값):
                return 값(*a, **k)
            return copy.deepcopy(값)
        꺼진.꺼짐 = 까닭
        꺼진.원래 = fn
        꺼진목록.append((fn.__module__, fn.__qualname__, 까닭))
        return 꺼진
    return 장식


def 이판에서쓰나(까닭):
    """문단을 끄는 조건 — 늘 거짓이다. `if 이판에서쓰나("까닭"):` 아래의 줄은 돌지 않는다."""
    return False


def 꺼졌나(fn):
    """그 함수가 꺼진 함수인가."""
    return bool(getattr(fn, "꺼짐", None))


def 꺼진자리(폴더):
    """폴더의 스크립트를 읽어 꺼진 함수와 문단을 찾는다 → [(파일, 줄, 종류, 이름, 까닭)]. 코드를 돌리지 않는다."""
    import ast
    import io
    import os

    def _부른이름(마디):
        f = 마디.func if isinstance(마디, ast.Call) else 마디
        return getattr(f, "id", None) or getattr(f, "attr", None)

    낸 = []
    for 파일 in sorted(x for x in os.listdir(폴더) if x.endswith(".py")):
        try:
            나무 = ast.parse(io.open(os.path.join(폴더, 파일), "r", encoding="utf-8").read())
        except SyntaxError:
            continue
        # 까닭을 이름으로 넘긴 자리(`끈까닭`)는 모듈의 글 상수에서 찾는다
        상수 = {t.id: 마디.value.value for 마디 in 나무.body if isinstance(마디, ast.Assign)
              and isinstance(마디.value, ast.Constant) and isinstance(마디.value.value, str)
              for t in 마디.targets if isinstance(t, ast.Name)}

        def _까닭(부름):
            if not 부름.args:
                return ""
            a = 부름.args[0]
            if isinstance(a, ast.Constant):
                return "%s" % a.value
            return 상수.get(getattr(a, "id", None), "")

        for 마디 in ast.walk(나무):
            if isinstance(마디, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for d in 마디.decorator_list:
                    if isinstance(d, ast.Call) and _부른이름(d) == "이판에서안씀":
                        낸.append((파일, 마디.lineno, "함수", 마디.name, _까닭(d)))
            elif isinstance(마디, ast.If):
                for x in ast.walk(마디.test):
                    if isinstance(x, ast.Call) and _부른이름(x) == "이판에서쓰나":
                        낸.append((파일, 마디.lineno, "문단", "%d~%d행" % (마디.lineno, 마디.body[-1].end_lineno), _까닭(x)))
    return 낸


if __name__ == "__main__":
    import os
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    자리 = 꺼진자리(os.path.dirname(os.path.abspath(__file__)))
    for 파일, 줄, 종류, 이름, 까닭 in 자리:
        print("%s:%d  %s %s — %s" % (파일, 줄, 종류, 이름, 까닭))
    print("꺼진 함수 %d개 · 꺼진 문단 %d곳" % (sum(1 for x in 자리 if x[2] == "함수"), sum(1 for x in 자리 if x[2] == "문단")))

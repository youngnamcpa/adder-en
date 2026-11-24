# -*- coding: utf-8 -*-
"""스캐폴드짓기 — 가정 파일의 기간으로 스캐폴드와 좌표 지도를 짓는다. **회차마다 붓기 앞에 한 번 돌린다.**

시간축 열(회계연도 실적 · 누계 실적 · 잔여 기간 · 연간 예측 · 수렴 구간 · 영구기간)은 가정 파일의 `기간`
(결산월 · 실적연도수 · 상세추정연수 · 수렴연수)과 `메타.평가기준일` 이 정한다(`기간축.py`). 스캐폴드는 정해진 파일이 아니라
그 가정으로 **짓는** 것이다 — 열 ID 가 기간 ID(FY2025A · 1H26A · 2H26E · FY2027E · TV)이고 안 쓰는 열이 없다.
붓기 · 대조는 가정의 기간으로 지은 스캐폴드(좌표 지도의 「기간」 = `기간축(가정)`)에서만 돈다.

  python 스크립트/스캐폴드짓기.py 가정.json [낼 폴더]
      낼 폴더(안 주면 가정 파일이 있는 폴더)에 `DCF_워크북_스캐폴드.xlsx` · `DCF_워크북_좌표지도.json` 을 낸다(있으면 덮는다)
  python 스크립트/붓기.py <낼 폴더>/DCF_워크북_스캐폴드.xlsx 가정.json 출력.xlsx      # 그 다음

하는 일 — 생성기(`키트에넣기.py --납품 --기간 … --곳 <낼 폴더>`)를 부른다: 줄 명세를 납품 배치 · 표준 서식으로 짓고, 좌표 지도에
이름칸 · 단위종류 · 줄이름지문 · 명세 지문 · 구조 지문 · 배치 표지를 싣고(짓기가 바로 낸다), 키트의 `좌표.py --확인`(짝)을 돌린다.
생성기는 ① 환경 변수 `DCF_생성기` ② 키트 안의 `생성기/` ③ 키트 곁의 `생성기/` 차례로 찾는다.

**기간과 구조를 넘긴다** (W3b) — 생성기에 스키마 v13 의 가정을 통째로 넘긴다. 생성기는 `기간` 으로 열을, `구조` 로 줄을 짓고
(구조에 따라 갈리는 줄이 명세에 설 때부터 — W5a~), 좌표 지도에 **구조 지문**(기간 · 구조 · 명세 지문의 해시)을 싣는다. 붓기 · 대조는
가정에서 그 지문을 다시 내어 견준다(`좌표.가정구조지문` — 생성기 `좌표지도.가정구조지문` 과 같은 셈). 가정의 `구조` 가 바뀌면 다시 짓는다.
옛 판(v12 — 15칸 배열) · 기간 부분만 옮긴 v13 은 다리(`옛꼴다리.새꼴가정`)가 옮긴 가정으로 짓는다. 다리가 못 옮기는 조각(시험용)은 기간만 넘긴다.
키트 뿌리의 기본 스캐폴드는 줄 명세의 기본 기간(생성기 줄 명세의 「기본기간」)으로 지은 견본이다 — 회차의 가정에 붓는 것이 아니다.

종료 코드 — 0 지었다 · 2 입력 오류(가정을 못 읽음 · 기간에서 열을 못 지음 · 생성기를 못 찾음) · 1 생성기가 짓지 못했거나 짝 확인이 통과하지 못함
"""
import io
import json
import os
import subprocess
import sys
import tempfile

_여기 = os.path.dirname(os.path.abspath(__file__))
if _여기 not in sys.path:
    sys.path.insert(0, _여기)
import 좌표  # noqa: E402
from 기간축 import 기간축, 기간축오류  # noqa: E402

환경변수 = "DCF_생성기"
환경변수_영문 = "DCF_GENERATOR"            # S10-20 — bash 는 한글 이름의 환경 변수를 export 하지 못한다
넘기는키 = ("결산월", "실적연도수", "상세추정연수", "수렴연수", "표기")      # 생성기(기간열.기간키)가 받는 것 — 평가기준일은 따로


class 짓기오류(Exception):
    """스캐폴드를 짓지 못했다. `rc` 는 종료 코드(2 입력 오류 · 1 생성기 쪽)."""

    def __init__(self, 글, rc=1):
        Exception.__init__(self, 글)
        self.rc = rc


def 생성기곳():
    """생성기 폴더(`키트에넣기.py` 가 있는 곳). 못 찾으면 짓기오류."""
    뿌리 = 좌표.키트뿌리()
    후보 = [os.environ.get(환경변수), os.environ.get(환경변수_영문), os.path.join(뿌리, "생성기"), os.path.join(os.path.dirname(뿌리), "생성기")]
    for 곳 in 후보:
        if 곳 and os.path.isfile(os.path.join(곳, "키트에넣기.py")):
            return os.path.abspath(곳)
    raise 짓기오류("생성기를 못 찾았습니다 — 환경 변수 %s, 키트 안의 생성기/, 키트 곁의 생성기/ 어디에도 키트에넣기.py 가 없습니다" % 환경변수, 2)


def 가정의기간(가정):
    """가정(v13 · 옛꼴가정 · 옛 판 v12) → 생성기에 넘길 기간({평가기준일, 결산월, 실적연도수, 상세추정연수, 수렴연수[, 표기]})과 축."""
    if not isinstance(가정, dict):
        raise 짓기오류("가정이 객체가 아닙니다", 2)
    기 = 가정.get("기간") if isinstance(가정.get("기간"), dict) else {}
    if any(k in 기 for k in ("라벨", "종료일", "구분")) or "_옛꼴" in 가정:      # 옛 판 · 다리가 편 옛꼴가정 — 다리가 새 꼴로 돌려준다
        import 옛꼴다리                                                       # noqa: PLC0415
        try:
            가정 = 옛꼴다리.새꼴가정(가정)
        except (옛꼴다리.가정오류, 옛꼴다리.다리오류) as e:
            raise 짓기오류("가정의 기간을 기간 축의 꼴로 옮기지 못했습니다 — %s" % e, 2)
    try:
        축 = 기간축(가정)
    except 기간축오류 as e:
        raise 짓기오류("가정의 기간에서 열을 짓지 못했습니다 — %s" % e, 2)
    기 = 가정.get("기간") or {}
    넘길 = {"평가기준일": 축.평가기준일.isoformat()}
    if 축.재무기준일 != 축.평가기준일:                      # 날짜 둘(2026-10-25) — 열은 재무기준일로 선다(옛 판은 넘기지 않는다 — 넘길 것이 같다)
        넘길["재무기준일"] = 축.재무기준일.isoformat()
    넘길.update((k, 기[k]) for k in 넘기는키 if 기.get(k) is not None)
    return 넘길, 축


def 짓기(가정, 곳, 조용히=True):
    """그 가정의 기간으로 `곳` 에 스캐폴드와 좌표 지도를 짓는다 → (스캐폴드 경로, 좌표 지도 경로, 생성기가 낸 글). 못 지으면 짓기오류.

    `가정` 은 가정 사전이나 가정 파일 경로다."""
    if isinstance(가정, str):
        try:
            with io.open(가정, "r", encoding="utf-8") as f:
                가정 = json.load(f)
        except (OSError, ValueError) as e:
            raise 짓기오류("가정 JSON 을 읽지 못했습니다: %s" % e, 2)
    넘길, 축 = 가정의기간(가정)
    온가정 = _새꼴(가정)                      # 구조를 가진 v13 — 생성기가 기간과 구조를 함께 읽는다. 못 만들면 None(기간만 넘긴다)
    생성기 = 생성기곳()
    곳 = os.path.abspath(곳)
    기간파일 = tempfile.NamedTemporaryFile("w", suffix=".json", prefix="기간_", delete=False, encoding="utf-8")
    try:
        json.dump(온가정 if 온가정 is not None else 넘길, 기간파일, ensure_ascii=False)
        기간파일.close()
        환경 = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1")
        r = subprocess.run([sys.executable, os.path.join(생성기, "키트에넣기.py"), "--납품", "--기간", 기간파일.name,
                            "--키트", 좌표.키트뿌리(), "--곳", 곳],
                           cwd=생성기, capture_output=True, text=True, encoding="utf-8", errors="replace", env=환경)
    finally:
        try:
            os.remove(기간파일.name)
        except OSError:
            pass
    글 = (r.stdout or "") + (r.stderr or "")
    if not 조용히:
        print(글.rstrip())
    틀, 지도 = os.path.join(곳, 좌표.스캐폴드이름), os.path.join(곳, 좌표.지도이름)
    if r.returncode or not (os.path.isfile(틀) and os.path.isfile(지도)):
        raise 짓기오류("생성기가 스캐폴드를 짓지 못했습니다(종료 코드 %d):\n%s" % (r.returncode, 글.strip()[-1500:]), 1)
    좌표.읽기(지도).기간열확인(축)            # 지은 지도의 축이 이 가정의 기간과 같은가 — 다르면 좌표오류
    if 온가정 is not None:
        구조지문맞추기(지도, 온가정)          # 지도에 실린 구조 지문 = 이 가정에서 다시 낸 것 — 다르면 짓기오류(두 쪽의 셈이 갈렸다)
    return 틀, 지도, 글


def _새꼴(가정):
    """가정(v13 · 옛꼴가정 · 옛 판 · 기간 부분만 옮긴 v13) → 구조를 가진 v13 가정. 다리가 못 옮기면 None."""
    if isinstance(가정, dict) and isinstance(가정.get("구조"), dict) and "_옛꼴" not in 가정:
        return 가정
    import 옛꼴다리                                                     # noqa: PLC0415
    try:
        새 = 옛꼴다리.새꼴가정(가정)
    except (옛꼴다리.가정오류, 옛꼴다리.다리오류):
        return None
    return 새 if isinstance(새, dict) and isinstance(새.get("구조"), dict) else None


def 구조지문맞추기(지도경로, 가정):
    """지은 좌표 지도의 구조 지문이 이 가정에서 다시 낸 것과 같은지 본다 → 그 지문. 다르면 짓기오류.

    구조 지문은 생성기가 싣는다(`짓기._지도덧` — 기간 · 구조 · 명세 지문의 해시). 구조 지문을 싣지 않는 옛 생성기로 지은 지도면
    같은 셈(`좌표.가정구조지문`)으로 여기서 싣는다. 지도의 배치 지문은 바뀌지 않는다(배치 지문은 시트 · 열 · 줄 자리로 낸다)."""
    with io.open(지도경로, "r", encoding="utf-8") as f:
        자료 = json.load(f)
    낸 = 좌표.가정구조지문(가정, 자료)
    실린 = 자료.get(좌표.구조지문키)
    if 실린 in (None, ""):
        자료[좌표.구조지문키] = 낸
        with io.open(지도경로, "w", encoding="utf-8") as f:
            json.dump(자료, f, ensure_ascii=False, separators=(",", ":"))      # 생성기와 같은 꼴로 쓴다
    elif 실린 != 낸:
        raise 짓기오류("생성기가 좌표 지도에 실은 구조 지문(%s)이 키트가 가정에서 다시 낸 것(%s)과 다릅니다 — 두 쪽의 셈이 갈렸습니다"
                    "(생성기 `좌표지도.가정구조지문` ↔ 키트 `좌표.가정구조지문`)" % (실린, 낸), 1)
    return 낸


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    인자 = [x for x in sys.argv[1:] if not x.startswith("-")]
    if any(x in ("-h", "--help", "--도움") for x in sys.argv[1:]):
        print(__doc__)
        return 0
    if not 1 <= len(인자) <= 2:
        sys.stderr.write("인자 오류 — python 스크립트/스캐폴드짓기.py 가정.json [낼 폴더]\n")
        return 2
    가정경로 = 인자[0]
    곳 = 인자[1] if len(인자) > 1 else os.path.dirname(os.path.abspath(가정경로))
    try:
        틀, 지도, 글 = 짓기(가정경로, 곳)
    except 짓기오류 as e:
        sys.stderr.write("스캐폴드짓기 — %s\n" % e)
        return e.rc
    except 좌표.좌표오류 as e:
        sys.stderr.write("좌표 오류 — %s\n" % e)
        return 1
    지 = 좌표.읽기(지도)
    열 = 지.기간열()
    print("지었습니다: %s (좌표 지도 %s · 지문 %s)" % (틀, os.path.basename(지도), 지.지문()))
    print("  시간축 %d열 — %s" % (len(열), " · ".join(열)))
    for 줄 in [x for x in 글.split("\n") if x.startswith(("지었다", "좌표.py"))]:
        print("  " + 줄.strip()[:300])
    print("다음: python 스크립트/붓기.py \"%s\" %s <출력.xlsx>" % (틀, 가정경로))
    return 0


if __name__ == "__main__":
    sys.exit(main())

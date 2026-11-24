# -*- coding: utf-8 -*-
"""English CLI wrapper for unpacking and updating the ADDER kit in a working folder."""
from __future__ import annotations
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.dirname(HERE)
KO_SCRIPTS = os.path.join(KIT, "스크립트")
if KO_SCRIPTS not in sys.path:
    sys.path.insert(0, KO_SCRIPTS)

import 키트펴기 as unpacker  # noqa: E402


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="Unpack or update the ADDER valuation kit in a working folder.")
    ap.add_argument("--target", default=".", help="Target working folder (created if missing)")
    ap.add_argument("--update", action="store_true", help="Update an existing unpacked kit in place")
    ap.add_argument("--dry-run", action="store_true", help="Preview changes without writing files")
    args = ap.parse_args(argv)

    os.makedirs(args.target, exist_ok=True)
    rc, rep = unpacker.펴기(args.target, 갱신=args.update, 보기=args.dry_run, 원본=KIT)
    if "까닭" in rep:
        old_v, new_v = rep.get("옛판"), rep.get("새판")
        if old_v and not args.update:
            print(f"ADDER init — stopped: ADDER kit (v{old_v}) is already unpacked in this folder. Run `/adder:update` (or pass --update) to upgrade to v{new_v}.")
        elif not old_v and args.update:
            print("ADDER update — stopped: No unpacked ADDER kit found in this folder. Run `/adder:init` first.")
        else:
            print("ADDER init — stopped: Target folder cannot be the kit source folder itself. Choose a separate working folder.")
        return rc

    mode = "Dry run (preview)" if args.dry_run else ("Updated kit" if args.update else "Unpacked kit")
    old_note = f" (from v{rep['옛판']})" if rep.get("옛판") else ""
    print(f"ADDER — {mode} · v{rep['판']}{old_note} · folder: {rep['작업폴더']}")
    backup_note = f" · backed up {rep['옮긴옛판']} modified file(s) to {rep['백업']}" if rep.get("백업") else ""
    print(f"  Written: {rep['쓴수']} · Unchanged: {rep['같은수']} · Skipped: {len(rep['건너뛴'])}{backup_note}")
    for skipped in rep["건너뛴"][:20]:
        print(f"  Skipped (existing user file preserved): {skipped}")
    if not args.dry_run and not args.update:
        print("Next — Reopen Claude Code in this folder (so CLAUDE.md loads), then run `/preflight`.")
    return rc


if __name__ == "__main__":
    sys.exit(main())

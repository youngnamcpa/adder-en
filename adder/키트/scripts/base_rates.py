# -*- coding: utf-8 -*-
"""English CLI wrapper for downloading & building the US SEC FSDS base-rate panel."""
from __future__ import annotations
import argparse
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.dirname(HERE)
KO_SCRIPT = os.path.join(KIT, "스크립트", "기저율.py")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Download and build the SEC Financial Statement Data Sets base-rate panel.")
    ap.add_argument("--download", action="store_true", help="Download quarterly SEC FSDS archives and build the panel")
    ap.add_argument("--country", default="US", choices=["US", "KR"], help="Market panel to build (default: US)")
    args, extra = ap.parse_known_args(argv)

    cmd = [sys.executable, "-X", "utf8", KO_SCRIPT]
    if args.download:
        cmd.append("--받기")
    cmd += ["--국가", args.country] + extra
    return subprocess.call(cmd)


if __name__ == "__main__":
    sys.exit(main())

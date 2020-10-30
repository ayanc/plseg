#!/usr/bin/env python3
# - Ayan Chakrabarti <ayan.chakrabarti@gmail.com>
"""Run flask app to annotate ROIs."""

import argparse
import plseg.roi as roi


def getargopts():
    """Parse command line arguments."""
    opts = argparse.ArgumentParser()
    opts.add_argument('--port', type=int,
                      help="Port to listen to (default 8888)",
                      default=8888)
    opts.add_argument('srcbase', help="Base source directory.")
    opts.add_argument('targetbase', help="Base target directory.")
    args = opts.parse_args()
    return args.srcbase, args.targetbase, args.port


if __name__ == "__main__":
    roi.main(*getargopts())

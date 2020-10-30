#!/usr/bin/env python3
# - Ayan Chakrabarti <ayan.chakrabarti@gmail.com>
"""Run flask app to clean segmentation."""

import argparse
import plseg.clean as clean


def getargopts():
    """Parse command line arguments."""
    opts = argparse.ArgumentParser()
    opts.add_argument('--port', type=int,
                      help="Port to listen to (default 8888)",
                      default=8888)
    opts.add_argument('basedir', help="Base (target) directory.")
    args = opts.parse_args()
    return args.basedir, args.port


if __name__ == "__main__":
    clean.main(*getargopts())

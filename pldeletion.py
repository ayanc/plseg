#!/usr/bin/env python3
# - Ayan Chakrabarti <ayan.chakrabarti@gmail.com>
"""Run flask app to clean segmentation."""

import argparse
import plseg.deletion as deletion


def getargopts():
    """Parse command line arguments."""
    opts = argparse.ArgumentParser()
    opts.add_argument('--port', type=int,
                      help="Port to listen to (default 8888)",
                      default=8888)
    opts.add_argument('--name', type=str,
                      help='Name of the label (default "bloom-time")',
                      default="bloom-time")
    opts.add_argument('--type', type=str,
                      help='Type of the label: Options are (1) "deletion-onwards", (2) "deletion-upto", (3) "deletion-single" (default "deletion-onwards")',
                      default="deletion-onwards")
    opts.add_argument('--input', type=str, 
                      help='Input file name (Default "clean.npz")',
                      default="clean.npz")
    opts.add_argument('basedir', help="Base (target) directory.")
    args = opts.parse_args()

    if args.type == "1":
        args.type = "deletion-onwards"
    elif args.type == "2":
        args.type = "deletion-upto"
    elif args.type == "3":
        args.type = "deletion-single"
    
    if args.input[0] != '/':
        args.input = '/' + args.input
    if args.input[-4:] != '.npz':
        args.input = args.input + ".npz"

    print(args.basedir, "  ", args.input)

    return args.basedir, args.port, args.name, args.type, args.input 


if __name__ == "__main__":
    deletion.main(*getargopts())

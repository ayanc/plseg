#!/usr/bin/env python3
# - Ayan Chakrabarti <ayan.chakrabarti@gmail.com>
"""Create visualiations of cleaned up segmentations."""

import sys
from glob import glob
from tqdm import tqdm
import numpy as np
from skimage.io import imread, imsave
import plseg.utils as ut


def getargopts():
    """Get directory list base on command line."""

    if len(sys.argv) != 2:
        sys.stderr.write(f'USAGE: {sys.argv[0]} base_target_dir\n')
        sys.stderr.write('Generate visualizations of '
                         + 'cleaned up segmentations.\n')
        sys.stderr.write('See README.md for instructions.\n')
        sys.exit(255)

    tgtdir = sys.argv[1].rstrip('/')
    dlist = sorted(glob(tgtdir+'/*/clean.npz'))
    dlist = ['/'.join(d.split('/')[:-1]) for d in dlist]

    return dlist


def vizcseg(dlist):
    """Main visualize loop."""

    for _d in tqdm(dlist):
        cropfs = sorted(glob(_d + '/*-crop.*'))
        outfs = [fn.replace("-crop", "-cseg") for fn in cropfs]

        origl = np.load(_d+'/labels.npz')['labels']
        cnpz = np.load(_d+'/clean.npz')
        newl = cnpz['labels']
        removed = cnpz['removed']

        for _j in range(newl.shape[-1]):
            base = imread(cropfs[_j])
            viz = ut.visualize(base, newl[:, :, _j])
            for _k in removed:
                viz[origl[:, :, _j] == _k, :] = 0
            imsave(outfs[_j], viz, check_contrast=False)


if __name__ == "__main__":
    vizcseg(getargopts())

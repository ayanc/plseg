#!/usr/bin/env python3
# - Ayan Chakrabarti <ayan.chakrabarti@gmail.com>
"""Crop and segment sequence of plant images."""

import sys
import os
import json
from tqdm import tqdm
import numpy as np
from skimage.io import imsave
import plseg.label as plbl
import plseg.utils as ut


def getargopts():
    """Get directory from command line and load config files."""

    if len(sys.argv) != 2:
        sys.stderr.write(f'USAGE: {sys.argv[0]} targetdir\n')
        sys.stderr.write(f'Crop and segment sequence of plant images.\n')
        sys.stderr.write('See README.md for instructions.\n')
        sys.exit(255)

    tgtdir = sys.argv[1].rstrip('/')

    if not os.path.isfile(tgtdir+'/caopt.json'):
        sys.stderr.write(f'{tgtdir}/caopt.json does not exist.\n')
        sys.stderr.write('See README.md for instructions.\n')
        sys.exit(255)

    with open(tgtdir+'/caopt.json', 'r') as _f:
        caopt = json.load(_f)
    srcdir = caopt['source']
    scale, skip = caopt['scale'], caopt['skip']
    xlim, ylim = caopt['xlim'], caopt['ylim']

    if os.path.isfile(tgtdir+'/segopt.json'):
        with open(tgtdir+'/segopt.json', 'r') as _f:
            sopt = json.load(_f)
        opt = plbl.Options(**sopt)
    else:
        opt = plbl.Options()

    return srcdir, tgtdir, scale, skip, (ylim, xlim), opt


def dosegment(srcdir, tgtdir, scale, skip, alims, opt):
    """Main segment function."""

    flist = ut.getimglist(srcdir)
    if skip > 0:
        flist = flist[skip:]
    nfiles = len(flist)

    labels, seg, imgc = None, None, None
    for i in tqdm(range(nfiles)):
        fname = flist[i]
        img = ut.imread(fname, scale)
        ofname = (fname.split('/')[-1]).split('.')
        ofn, oext = '.'.join(ofname[:-1]), ofname[-1]

        if i == 0:
            imgc = img[alims[0][0]:alims[0][1], alims[1][0]:alims[1][1], :]
            labels = np.zeros([imgc.shape[0], imgc.shape[1], len(flist)],
                              dtype=np.int32)
        else:
            imgc = ut.crop_align(img, imgc)
        imsave(f'{tgtdir}/{ofn}-crop.{oext}', imgc)

        seg = plbl.label(imgc, seg, opt)
        labels[:, :, i] = seg
        imsave(f'{tgtdir}/{ofn}-seg.{oext}', ut.visualize(imgc, seg),
               check_contrast=False)

    if(np.amax(labels) <= 255):
        labels = labels.astype(np.uint8)
    else:
        labels = labels.astype(np.int16)
    np.savez_compressed(f'{tgtdir}/labels.npz', labels=labels)


if __name__ == "__main__":
    dosegment(*getargopts())

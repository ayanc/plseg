# - Ayan Chakrabarti <ayan.chakrabarti@gmail.com>
"""Sequentially segment and label individual plants"""

from dataclasses import dataclass
import numpy as np
import scipy.ndimage as ndi
from skimage.morphology import convex_hull_image as chi
import gco
from .costs import unary, pairwise


@dataclass
class Options:
    """Options class for individual plant segmentation"""
    grthresh: int = 8  # Negative of a value threshold
    grsensitivity: int = 4  # Controls how fast unary cost saturates
    fsz: int = 8  # Derivative filter size
    fsgm: int = 2  # Sigma^2 of derivative filter Gaussian
    fsensitivity: int = 4  # How fast derivative magnitude saturates
    uwt: int = 10000  # Relative weight of unary cost
    ewt: int = 5000  # Relative weight of spatial edge costs
    zwt: int = 2500  # Relative weight of edge to same pixel in previous frame
    ccnbd: int = 10  # Two pixels in same connected component if < ccnbd apart
    joinit: int = 50  # Number of join iterations for disconnected plant parts
    joininc: int = 100  # Amount to increment score by


_PLOPT = Options()


def joincc(lmap, prev, ucost0, ewts, opt):
    """Create joins to ensure each plant is one connected component."""

    pwcost = 1-np.eye(2, dtype=np.int32)
    for lbl in range(1, np.amax(lmap)+1):
        ncc = ndi.label(lmap == lbl)[1]
        if ncc <= 1:
            continue

        # Crop out portions just including that component
        _y, _x = np.where(lmap == lbl)
        _y1, _y2 = np.amin(_y), np.amax(_y)+1
        _x1, _x2 = np.amin(_x), np.amax(_x)+1

        lmxy = lmap[_y1:_y2, _x1:_x2]
        uc0 = (ucost0[_y1:_y2, _x1:_x2]).copy()
        if prev is not None:
            uc0[prev[_y1:_y2, _x1:_x2] == lbl] = \
                uc0[prev[_y1:_y2, _x1:_x2] == lbl] + opt.zwt

        chull = np.logical_and(chi(lmxy == lbl), lmxy == 0)
        ucost = np.zeros([lmxy.shape[0], lmxy.shape[1], 2], np.int32)
        ucost[:, :, 0] = -opt.uwt
        ucost[lmxy == lbl, 0] = opt.uwt
        ucost[chull, 0] = uc0[chull]

        ew0 = [ewts[0][_y1:(_y2-1), _x1:_x2],
               ewts[1][_y1:_y2, _x1:(_x2-1)],
               ewts[2][_y1:(_y2-1), _x1:(_x2-1)],
               ewts[3][_y1:(_y2-1), _x1:(_x2-1)]]

        joined = False
        for _ in range(opt.joinit):
            # Do a graph cut after biasing the background
            ucost[chull, 0] = ucost[chull, 0] + opt.joininc
            lmxy2 = gco.cut_grid_graph(ucost, pwcost, *ew0).reshape(lmxy.shape)

            if ndi.label(lmxy2 == 1)[1] == 1:
                # Now, see if we can remove some of the added components
                newcomps, nnc = ndi.label(np.logical_and(lmxy2 == 1,
                                                         lmxy == 0))
                if nnc > 1:
                    scores = np.bincount(newcomps.flatten(), uc0.flatten())
                    cidx = np.argsort(scores[1:]) + 1
                    for ncidx in cidx:
                        lmxy2b = lmxy2.copy()
                        lmxy2b[newcomps == ncidx] = 0
                        if ndi.label(lmxy2b)[1] == 1:
                            lmxy2 = lmxy2b

                # Patch things back in
                lmxy[lmxy2 == 1] = lbl
                lmap[_y1:_y2, _x1:_x2] = lmxy
                joined = True
                break

        if not joined:
            ccxy = ndi.label(lmxy == lbl)[0]
            ccount = np.bincount(ccxy.flatten())
            ccsort = np.argsort(-ccount[1:])
            for idx in range(1, len(ccsort)):
                lmxy[ccxy == (ccsort[idx]+1)] = 0
            lmap[_y1:_y2, _x1:_x2] = lmxy

    return lmap


def splitlabel(lmap, mask, prev, slbls, ucost0, ewts, opt):
    """Split a new connected component that overlaps multiple components"""

    _ys, _xs = np.where(mask)
    _y1, _y2, _x1, _x2 = np.amin(_ys), np.amax(_ys), np.amin(_xs), np.amax(_xs)

    prev = prev[_y1:(_y2+1), _x1:(_x2+1)]
    ucost0 = ucost0[_y1:(_y2+1), _x1:(_x2+1)]
    ucost = np.zeros(np.shape(ucost0) + (len(slbls)+1,), np.int32)
    ucost[:, :, 0] = ucost0

    ewts = [ewts[0][_y1:_y2, _x1:(_x2+1)],
            ewts[1][_y1:(_y2+1), _x1:_x2],
            ewts[2][_y1:_y2, _x1:_x2],
            ewts[3][_y1:_y2, _x1:_x2]]

    ucost[prev > 0, :] = ucost[prev > 0, :] + opt.zwt
    for i, lbl in enumerate(slbls):
        ucost[prev == lbl, i+1] = 0

    pwcost = 1 - np.eye(len(slbls)+1, dtype=np.int32)

    mcut0 = gco.cut_grid_graph(ucost, pwcost, *ewts).reshape(ucost0.shape)
    mcut = np.zeros_like(lmap)
    mcut[_y1:(_y2+1), _x1:(_x2+1)] = mcut0
    for i, lbl in enumerate(slbls):
        lmap[np.logical_and(mask, mcut == (i+1))] = lbl


def separateconnect(binary, prev, ucost0, ewts, opt):
    """Convert binary to individual plant segmentations."""

    ccs, nfound = ndi.label(ndi.binary_dilation(binary,
                                                np.ones((2*opt.ccnbd+1,)*2)))
    ccs[binary == 0] = 0
    if prev is None:
        lbl2 = 1
        for lbl in range(1, nfound+1):
            if len(np.where(ccs == lbl)[0]) < opt.ccnbd:
                ccs[ccs == lbl] = 0
            else:
                ccs[ccs == lbl] = lbl2
                lbl2 = lbl2 + 1
        if opt.joinit > 0:
            ccs = joincc(ccs, prev, ucost0, ewts, opt)
        return ccs

    nexist, nnew = np.amax(prev), 0
    newmeans = []  # Store mean pos of new labels to match to missing from prev

    lmap = np.zeros_like(ccs)
    for lbl in range(1, nfound+1):
        olbls = np.unique(prev[np.logical_and(prev > 0, ccs == lbl)])
        if len(olbls) == 0:
            if len(np.where(ccs == lbl)[0]) < opt.ccnbd:
                continue
            nnew = nnew+1
            lmap[ccs == lbl] = -nnew
            _lpos = np.where(ccs == lbl)
            newmeans.append([np.mean(np.float64(_lpos[0])),
                             np.mean(np.float64(_lpos[1]))])

        elif len(olbls) == 1:
            lmap[ccs == lbl] = olbls[0]
        else:
            splitlabel(lmap, ccs == lbl, prev, olbls, ucost0, ewts, opt)

    # Map missing old to new found labels
    newmeans = np.asarray(newmeans, np.float64)
    missing = np.bincount(np.maximum(0, lmap.flatten()), minlength=(nexist+1))
    missing = list(np.where(missing[1:] == 0)[0] + 1)
    for mlbl in missing:
        if nnew == 0:
            if np.all(lmap[prev == mlbl] == 0):
                lmap[prev == mlbl] = mlbl
            continue

        _lpos = np.where(prev == mlbl)
        if len(_lpos[0]) == 0:
            continue
        mlmean = np.asarray([np.mean(np.float64(_lpos[0])),
                             np.mean(np.float64(_lpos[1]))], np.float64)
        dists = np.sum(np.square(mlmean-newmeans), -1)
        if np.nanmin(dists) < np.square(opt.ccnbd*8):
            idx = np.nanargmin(dists)
            lmap[lmap == -(idx+1)] = mlbl
            newmeans[idx, :] = np.NAN
            nnew = nnew - 1
        else:  # Too far
            if np.all(lmap[prev == mlbl] == 0):
                lmap[prev == mlbl] = mlbl

    # Create new labels out of any left
    idx = np.where(np.bincount(
        np.maximum(0, -lmap.flatten()))[1:] >= opt.ccnbd)[0] + 1
    for _i in idx:
        nexist = nexist+1
        lmap[lmap == (-_i)] = nexist

    if opt.joinit > 0:
        lmap = joincc(lmap, prev, ucost0, ewts, opt)

    return lmap


def label(img, prev, opt=_PLOPT):
    """Label all plants in an image, using previous labels as guide."""

    # Do a binary segmentation first
    ucost = np.zeros([img.shape[0], img.shape[1], 2], np.int32)
    ucost0 = ((unary(img, opt)-0.5)*opt.uwt).astype(np.int32)
    ucost[:, :, 0] = ucost0
    pwcost = 1 - np.eye(2, dtype=np.int32)
    if prev is not None:
        ucost[prev > 0, 0] = ucost[prev > 0, 0] + opt.zwt

    ewts = pairwise(img, opt)
    ewts = [(f*opt.ewt).astype(np.int32) for f in ewts]

    binary = gco.cut_grid_graph(ucost, pwcost, *ewts).reshape(img.shape[:2])

    # Then label individual plants
    plants = separateconnect(binary, prev, ucost0, ewts, opt)

    return plants

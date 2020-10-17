# - Ayan Chakrabarti <ayan.chakrabarti@gmail.com>
"""Miscellaneous Utility functions."""

from glob import glob
import numpy as np
from scipy.signal import correlate as corr
from skimage.io import imread as skimread
from skimage.transform import resize as imresize


def imread(fname, factor=100):
    """Read possibly scaled version of image"""
    img = skimread(fname)
    if factor < 100:
        img = imresize(img, [int(img.shape[0]*factor/100),
                             int(img.shape[1]*factor/100)], order=3)
        img = (img*255).astype(np.uint8)
    return img


def getimglist(sdir):
    """Get list of images."""
    jpgs = sorted(glob(sdir+'/*.jpg'))
    jpegs = sorted(glob(sdir+'/*.jpeg'))
    pngs = sorted(glob(sdir+'/*.png'))
    if len(jpgs) >= len(jpegs) and len(jpgs) >= len(pngs):
        return jpgs
    if len(jpegs) >= len(pngs):
        return jpegs
    return pngs


def visualize(img, mask):
    """Produce a visualization of the segmentation."""
    out = np.float32(img)/255
    msk = CMAP[mask % CMAP.shape[0], :]
    msk[mask == 0, :] = 0.
    out = out*0.5 + msk*0.5
    return (out*255).astype(np.uint8)


def crop_align(img, imgc):
    """Find crop in img aligned to imgc."""

    if np.amax(img) < np.amax(imgc)//2:
        return imgc

    _py, _px = int(0.05*imgc.shape[0]), int(0.05*imgc.shape[1])
    imgp = np.pad(img, [[_py], [_px], [0]])

    imgpg = np.mean(imgp.astype(np.float32), -1)
    imgc = np.mean(imgc.astype(np.float32), -1)

    imgpc = np.sum(imgc**2) - 2*corr(imgpg, imgc, 'valid')
    imgpc = imgpc + corr(imgpg**2, np.ones_like(imgc), 'valid')

    amin = np.unravel_index(np.argmin(imgpc), imgpc.shape)
    return imgp[amin[0]:(amin[0]+imgc.shape[0]),
                amin[1]:(amin[1]+imgc.shape[1]), :]


# Hardcoded colormap to avoid dependency on matplotlib
CMAP = np.reshape([0.12156, 0.4666, 0.7058, 0.6823, 0.7803, 0.9098,
                   1.0, 0.4980, 0.054901, 1.0, 0.7333, 0.47058, 0.17254,
                   0.6274, 0.17254, 0.596, 0.8745, 0.5411, 0.8392, 0.15294,
                   0.1568, 1.0, 0.596, 0.5882, 0.5803, 0.403, 0.7411, 0.7725,
                   0.6901, 0.8352, 0.5490, 0.33725, 0.29411, 0.7686, 0.611,
                   0.5803, 0.8901, 0.4666, 0.7607, 0.9686, 0.7137, 0.8235,
                   0.4980, 0.4980, 0.4980, 0.7803, 0.7803, 0.7803, 0.7372,
                   0.7411, 0.13333, 0.8588, 0.8588, 0.5529, 0.09019, 0.7450,
                   0.8117, 0.6196, 0.8549, 0.8980, 0.4019, 0.6235, 0.807,
                   0.8411, 0.6392, 0.4823, 1.0, 0.615, 0.2627, 0.5862,
                   0.6803, 0.32156, 0.38431, 0.7509, 0.35686, 0.7176, 0.5137,
                   0.34901, 0.919, 0.37450, 0.37254, 0.7901, 0.5, 0.6647,
                   0.6764, 0.5470, 0.7882, 0.6607, 0.5137, 0.5647, 0.6588,
                   0.47450, 0.4372, 0.8294, 0.5392, 0.6705, 0.9294, 0.5901,
                   0.792, 0.7333, 0.6058, 0.6607, 0.6392, 0.6392, 0.6392,
                   0.7588, 0.7607, 0.4568, 0.7980, 0.8, 0.3431, 0.4745, 0.8019,
                   0.6823, 0.35490, 0.8, 0.8549019607843138], [39, 3])

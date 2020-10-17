# - Ayan Chakrabarti <ayan.chakrabarti@gmail.com>
"""Define unary and pairwise costs."""

import numpy as np
from scipy.signal import convolve2d as conv2
from skimage.color import rgb2lab


def unary(img, opt):
    """Get per-pixel likelihood of it being foreground."""

    aimg = (rgb2lab(img)[:, :, 1]).astype(np.float32)
    aimg = np.exp((-aimg-opt.grthresh)/opt.grsensitivity)
    aimg = aimg / (1+aimg)
    return aimg


def pairwise(img, opt):
    """Get edge weightings for LR-UD-DR-DL pairs"""

    img = np.mean(img.astype(np.float32), -1)
    img = np.pad(img, [[opt.fsz//2-1, opt.fsz//2],
                       [opt.fsz//2-1, opt.fsz//2]],
                 'symmetric')
    _x = np.arange(opt.fsz, dtype=np.float32) - (opt.fsz-1)/2
    _x, _y = np.meshgrid(_x, _x)

    gfx = _x*np.exp(-(_x**2+_y**2)/2/opt.fsgm)
    gfy = np.transpose(gfx)

    imx = conv2(img, gfx, 'valid')
    imy = conv2(img, gfy, 'valid')
    imdr, imdl = (imx+imy)**2, (imx-imy)**2
    imx, imy = imx**2, imy**2

    means = [np.mean(imx), np.mean(imy), np.mean(imdr), np.mean(imdl)]
    imx = np.exp(-imx / means[0] / opt.fsensitivity)
    imy = np.exp(-imy / means[1] / opt.fsensitivity)
    imdr = 0.5*np.exp(-imdr / means[2] / opt.fsensitivity)
    imdl = 0.5*np.exp(-imdl / means[3] / opt.fsensitivity)

    return imy[:-1, :], imx[:, :-1], imdr[:-1, :-1], imdl[:-1, 1:]

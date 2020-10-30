# - Ayan Chakrabarti <ayan.chakrabarti@gmail.com>
"""Flask app for marking up incorrect segmentations."""

import os
import io
from glob import glob
import flask
import numpy as np
from imageio import imwrite
from . import utils as ut


APP = flask.Flask("plseg-clean")
APP.targetid = None
APP.flist = []
APP.lbls = []
APP.dlist = []


# Commented out code to enable selection based on where plant appeared,
# rather than label in current image.
# APP.lbl_f = []
# def findfirst():
#     """Label pixels by where a label first appeared."""
#     APP.lbl_f = np.zeros_like(APP.lbls[:, :, 0])
#     fidx = np.ones((np.amax(APP.lbls),), np.int16)*APP.lbls.shape[2]
#     for i in range(APP.lbls.shape[2]):
#         exist = np.bincount(APP.lbls[:, :, i].flatten())
#         exist = np.where(exist[1:] > 0)[0]
#         fidx[exist] = np.minimum(fidx[exist], i)
#         if np.all(fidx < APP.lbls.shape[2]):
#             break
#     for i, j in enumerate(list(fidx)):
#         APP.lbl_f[APP.lbls[:, :, j] == (i+1)] = i+1


@APP.route("/", methods=["GET"])
def index():
    """Return html file."""
    return flask.send_file(APP.ldir+"/clean.html", cache_timeout=0)


@APP.route("/clean.js", methods=["GET"])
def cleanjs():
    """Return javascript file."""
    return flask.send_file(APP.ldir+"/clean.js", cache_timeout=0)


@APP.route("/img/<imid>", methods=["GET"])
def getimg(imid):
    """Return base image of current sequence."""
    imid = int(imid.split(":")[1])
    return flask.send_file(APP.flist[imid], cache_timeout=0)


@APP.route("/getlabel/<data>", methods=["GET"])
def getlabel(data):
    """Get the label of a specific pixel in the current image."""
    imid, _yl, _yr, _xl, _xr = [int(f) for f in data.split(':')]
    exists = np.bincount(APP.lbls[_yl:_yr, _xl:_xr, imid].flatten())
    labels = np.where(exists[1:] > 0)[0] + 1
    labels = [int(f) for f in list(labels)]
    return flask.jsonify({'label': labels})


@APP.route("/seg/<data>", methods=["GET"])
def getseg(data):
    """Return segmentation mask as PNG with alpha channel."""
    data = [int(f) for f in data.split(':')][1:]
    imid = data[0]
    if len(data) > 1:
        removed = data[1:]

    img = np.ones((APP.lbls.shape[0], APP.lbls.shape[1], 4), np.float32)
    img[:, :, -1] = 0.5
    img[:, :, :3] = ut.CMAP[APP.lbls[:, :, imid] % ut.CMAP.shape[0], :]
    img[APP.lbls[:, :, imid] == 0, :3] = 0
    if len(data) > 1:
        for j in removed:
            img[APP.lbls[:, :, imid] == j, :] = 1.0

    mem = io.BytesIO()
    imwrite(mem, (img*255).astype(np.uint8), format="png")
    mem.seek(0)
    return flask.send_file(mem, mimetype="image/png", cache_timeout=0)


@APP.route("/save/<data>", methods=["GET"])
def save(data):
    """Save cleanup annotations."""
    if len(data) == 1:
        removed = []
    else:
        removed = [int(f) for f in data[1:].split(':')]
    fname = APP.basedir + '/' + APP.dlist[APP.targetid] + '/clean.npz'

    if len(removed) == 0:
        idx = np.zeros((np.amax(APP.lbls) + 1,), APP.lbls.dtype)
        _id = 1
        for i in range(1, len(idx)):
            if i not in removed:
                idx[i] = _id
                _id = _id + 1
        lbls = idx[APP.lbls]
    else:
        lbls = APP.lbls

    npz = {'removed': np.asarray(removed, np.int16), 'labels': lbls}
    np.savez_compressed(fname, **npz)
    return ' '


@APP.route("/load/<int:targetid>", methods=["GET"])
def load(targetid):
    """Switch to different directory and return info."""
    APP.targetid = targetid
    tdir = APP.basedir + '/' + APP.dlist[targetid]
    APP.flist = sorted(glob(tdir+'/*-crop.*'))
    APP.lbls = np.load(tdir+'/labels.npz')['labels']
    # findfirst()
    resp = {'numi': len(APP.flist)}
    if os.path.isfile(tdir+'/clean.npz'):
        resp['saved'] = True
        resp['removed'] = [int(f)
                           for f in np.load(tdir+'/clean.npz')['removed']]
    else:
        resp['saved'] = False
    return flask.jsonify(resp)


@APP.route("/dlist", methods=["GET"])
def getdlist():
    """Get list of target sub-directories."""
    return flask.jsonify(APP.dlist)


def main(basedir, port=8888):
    """Run server"""
    APP.ldir = "/".join(__file__.split('/')[:-1]) + '/jshtml'
    APP.basedir = basedir.rstrip("/")
    APP.dlist = sorted([f.split('/')[-2]
                        for f in glob(basedir+'/*/labels.npz')])

    APP.run(port=port)

# From starting point `clean.py`, used to obtain different subsets of the segmentation


# - Ayan Chakrabarti <ayan.chakrabarti@gmail.com>
"""Flask app for marking up incorrect segmentations."""

import os
import io
from glob import glob
import flask
import numpy as np
from imageio import imwrite
from . import utils as ut


APP = flask.Flask("plseg-deletion")#APP = flask.Flask("plseg-clean")
APP.targetid = None
APP.flist = []
APP.lbls = []
APP.dlist = []
APP.tag_name = ""
APP.tag_type = ""
APP.input_name = ""


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
    return flask.send_file(APP.ldir+"/deletion.html", cache_timeout=0)


@APP.route("/deletion.js", methods=["GET"])
def planttagjs():
    """Return javascript file."""
    return flask.send_file(APP.ldir+"/deletion.js", cache_timeout=0)


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
    data_and_frames = data.split("_")
    data = data_and_frames[0]
    frames = data_and_frames[1]
    data = [int(f) for f in data.split(':')][1:]
    
    imid = data[0]
    if len(data) > 1:
        removed = data[1:]
        frames = [int(f) for f in frames.split(':')]

    img = np.ones((APP.lbls.shape[0], APP.lbls.shape[1], 4), np.float32)
    img[:, :, -1] = 0.5
    img[:, :, :3] = ut.CMAP[APP.lbls[:, :, imid] % ut.CMAP.shape[0], :]
    img[APP.lbls[:, :, imid] == 0, :3] = 0
    if len(data) > 1:
        for j in range(len(removed)):
            rem = removed[j]
            rem_frame = frames[j]
            if APP.tag_type == "deletion-onwards" and imid >= rem_frame:
                img[APP.lbls[:, :, imid] == rem, :] = 1.0
            elif APP.tag_type == "deletion-upto" and imid <= rem_frame:
                img[APP.lbls[:, :, imid] == rem, :] = 1.0
            elif APP.tag_type == "deletion-single" and imid == rem_frame:
                img[APP.lbls[:, :, imid] == rem, :] = 1.0

    mem = io.BytesIO()
    imwrite(mem, (img*255).astype(np.uint8), format="png")
    mem.seek(0)
    return flask.send_file(mem, mimetype="image/png", cache_timeout=0)


@APP.route("/save/<data>", methods=["GET"])
def save(data):
    """Save cleanup annotations."""
    data_and_frames = data.split("_")
    data = data_and_frames[0]
    frames = data_and_frames[1]
    if len(data) == 1:
        removed = []
    else:
        removed = [int(f) for f in data[1:].split(':')]
        frames = [int(f) for f in frames[:].split(':')]
    #fname = APP.basedir + '/' + APP.dlist[APP.targetid] + '/planttag.npz'
    fname = APP.basedir + '/' + APP.dlist[APP.targetid] + '/' + APP.tag_name + '.npz'

    if len(removed) == 0:  # Before: if len(removed) == 0
        idx = np.zeros((np.amax(APP.lbls) + 1,), APP.lbls.dtype)
        _id = 1
        for i in range(1, len(idx)):
            if i not in removed:
                idx[i] = _id
                _id = _id + 1
        lbls = idx[APP.lbls]
    else:
        lbls = APP.lbls

    for j in range(len(removed)):
        rem = removed[j]
        frame = frames[j]
        # Remove that label from the frame onwards:
        if APP.tag_type == "deletion-onwards":
            lbls[:,:,frame:][lbls[:,:,frame:] == rem] = 0
        elif APP.tag_type == "deletion-upto":
            lbls[:,:,:frame][lbls[:,:,:frame] == rem] = 0
        elif APP.tag_type == "deletion-single":
            lbls[:,:,frame][lbls[:,:,frame] == rem] = 0
    
    # 
    tag = [-1]*lbls.max()
    for i in range(len(removed)):
        tag[removed[i]] = frames[i]

    npz = {'removed': np.asarray(removed, np.int16), 'labels': lbls, "frames": np.asarray(frames, np.int16), \
        APP.tag_name: tag}
    np.savez_compressed(fname, **npz)
    return ' '


@APP.route("/load/<int:targetid>", methods=["GET"])
def load(targetid):
    """Switch to different directory and return info."""
    APP.targetid = targetid
    tdir = APP.basedir + '/' + APP.dlist[targetid]
    APP.flist = sorted(glob(tdir+'/*-crop.*'))

    load_file = np.load(tdir+APP.input_name)

    #APP.lbls = np.load(tdir+'/labels.npz')['labels']
    APP.lbls = load_file['labels']
    # findfirst()
    resp = {'numi': len(APP.flist)}
    # if os.path.isfile(tdir+'/planttag.npz'):
    if os.path.isfile(tdir + "/" + APP.tag_name + '.npz'):
        #load_planttag = np.load(tdir+'/planttag.npz')
        load_planttag = np.load(tdir + "/" + APP.tag_name + '.npz')

        resp['saved'] = True
        # resp['removed'] = [int(f)
        #                    for f in np.load(tdir+'/planttag.npz')['removed']]
        # resp['frames'] = [int(f)
        #                    for f in np.load(tdir+'/planttag.npz')['frames']]
        resp['removed'] = [int(f)
                           for f in load_planttag['removed']]
        if 'frames' in load_planttag:
            resp['frames'] = [int(f)
                            for f in load_planttag['frames']]
        else:
            resp['frames'] = [0 for f in load_planttag['removed']]
    else:
        resp['saved'] = False
    return flask.jsonify(resp)


@APP.route("/dlist", methods=["GET"])
def getdlist():
    """Get list of target sub-directories and your labeling type."""
    resp = dict()
    resp["dlist"] = APP.dlist
    resp["type"] = APP.tag_type
    return flask.jsonify(resp)#flask.jsonify(APP.dlist)


def main(basedir, port=8888, name="bloom-time", ttype="deletion-onwards", input_name="/clean.npz"):
    """Run server"""
    APP.ldir = "/".join(__file__.split('/')[:-1]) + '/jshtml'
    APP.basedir = basedir.rstrip("/")
    APP.dlist = sorted([f.split('/')[-2]
                        for f in glob(basedir+'/*' + input_name)])
    
    APP.tag_name = name
    APP.tag_type = ttype
    APP.input_name = input_name

    APP.run(port=port)
    

# - Ayan Chakrabarti <ayan.chakrabarti@gmail.com>
"""Flask app for annotating ROIs."""

import os
import json
from glob import glob
import flask
import numpy as np
from . import utils as ut


APP = flask.Flask("plseg-roi")


@APP.route("/", methods=["GET"])
def index():
    """Return html file."""
    return flask.send_file(APP.ldir+"/cset.html", cache_timeout=0)


@APP.route("/cset.js", methods=["GET"])
def csetjs():
    """Return javascript file."""
    return flask.send_file(APP.ldir+"/cset.js", cache_timeout=0)


@APP.route("/img/<imid>", methods=["GET"])
def getimg(imid):
    """Return image given directory id + skip."""
    imid = [int(f) for f in imid.split(":")]
    flist = ut.getimglist(APP.srcdir+"/"+APP.flist[imid[0]])
    return flask.send_file(flist[imid[1]], cache_timeout=0)


@APP.route("/save/<int:seqid>", methods=["POST"])
def saveinfo(seqid):
    """Save to json."""
    flask.request.get_data()
    data = json.loads(flask.request.data)

    info = {'source': APP.srcdir+"/"+APP.flist[seqid]}
    destdir = APP.destdir+"/"+APP.flist[seqid]
    info['skip'], info['scale'] = data['skip'], data['scale']

    xlim, ylim = data['xlim'], data['ylim']
    if xlim[0] > xlim[1]:
        xlim = [xlim[1], xlim[0]]
    if ylim[0] > ylim[1]:
        ylim = [ylim[1], ylim[0]]

    flist = ut.getimglist(info['source'])
    img = ut.imread(flist[info['skip']])
    shape = [int(img.shape[0]*info['scale']/100),
             int(img.shape[1]*info['scale']/100)]
    xls = np.asarray(xlim, dtype=np.float64) * shape[1]
    yls = np.asarray(ylim, dtype=np.float64) * shape[0]
    info['xlim'] = [int(xls[0]), int(xls[1])]
    info['ylim'] = [int(yls[0]), int(yls[1])]

    print(json.dumps(info))
    if not os.path.isdir(destdir):
        try:
            os.mkdir(destdir)
        except Exception:
            return flask.json.jsonify("Could not create "+destdir)

    try:
        _f = open(destdir+"/caopt.json", "w")
        _f.write(json.dumps(info))
        _f.close()
        return flask.json.jsonify("Saved to "+destdir+"/caopt.json")
    except Exception:
        return flask.json.jsonify("Error writing to "+destdir+"/caopt.json")


@APP.route("/info/<int:seqid>", methods=["GET"])
def getinfo(seqid):
    """Get information about specific sequence directory."""
    flist = ut.getimglist(APP.srcdir+"/"+APP.flist[seqid])
    info = {'smax': len(flist)}
    info['saved'] = False

    if os.path.isfile(APP.destdir+"/"+APP.flist[seqid]+'/caopt.json'):
        try:
            with open(APP.destdir+"/"+APP.flist[seqid]
                      + '/caopt.json', 'r') as _f:
                data = json.load(_f)
            info['scale'] = data['scale']
            info['skip'] = data['skip']
            img = ut.imread(flist[info['skip']])
            shape = [int(img.shape[0]*info['scale']/100),
                     int(img.shape[1]*info['scale']/100)]
            xls = np.asarray(data['xlim'], dtype=np.float64) / shape[1]
            yls = np.asarray(data['ylim'], dtype=np.float64) / shape[0]
            info['xlim'], info['ylim'] = list(xls), list(yls)
            info['saved'] = True
        except Exception:
            info['saved'] = False

    return flask.json.jsonify(info)


@APP.route("/dlist", methods=["GET"])
def dlist():
    """Return list of sequence sub-directories"""
    return flask.json.jsonify(APP.flist)


def main(srcdir, destdir, port=8888):
    """Run server"""
    APP.ldir = "/".join(__file__.split('/')[:-1]) + '/jshtml'
    APP.srcdir = srcdir.rstrip("/")
    APP.destdir = destdir.rstrip("/")

    APP.flist = sorted([f.split('/')[-1] for f in glob(srcdir+'/*')
                        if os.path.isdir(f)])

    APP.run(port=port)

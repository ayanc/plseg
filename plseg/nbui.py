# - Ayan Chakrabarti <ayan.chakrabarti@gmail.com>
"""UI functions for use in jupyter notebooks."""

import os
import json
from glob import glob
import ipywidgets as widgets
import matplotlib.pyplot as plt
from . import utils as ut


def getfigure():
    """Create a matplotlib figure inside a widget output."""
    output = widgets.Output()
    with output:
        fig, axes = plt.subplots(constrained_layout=True)
        fig.canvas.resizable = False
        fig.canvas.header_visible = False
        fig.canvas.toolbar_visible = False

    return output, fig, axes


class CropSetUI:
    """UI for interactively specifying crops."""

    def __init__(self):
        """Setup all UI elements."""

        title = widgets.HTML(value="<h1>Set Image Crops</h1>",
                             layout={'margin': '10px 0px 20px'})

        self.srcdir = widgets.Text(placeholder='/path/to/source/directory')
        self.destdir = widgets.Text(placeholder='/path/to/dest/directory')
        self.rescan = widgets.Button(description="Set",
                                     button_style="primary",
                                     layout={'margin': '10px auto 25px',
                                             'width': 'max-content'})

        self.dsel = widgets.Dropdown(Options=[], value=None)

        self.scale = widgets.IntSlider(50, min=25, max=100, step=25,
                                       description="Scale",
                                       continuous_update=False)
        self.skip = widgets.IntSlider(0, min=0, max=0, step=1,
                                      description="Skip",
                                      continuous_update=False)
        self.xlims = widgets.IntRangeSlider(value=[0, 0],
                                            min=0, max=0, step=1,
                                            description="X",
                                            layout={"width": "90%"},
                                            continuous_update=True)
        self.ylims = widgets.IntRangeSlider(value=[0, 0],
                                            min=0, max=0, step=1,
                                            description="Y",
                                            layout={"width": "90%"},
                                            continuous_update=True)

        self.save = widgets.Button(description="Save", button_style="danger",
                                   layout={'margin': '10px auto 25px',
                                           'width': 'max-content'})
        self.display = widgets.Textarea(value="", rows=6, disabled=True)
        output, self.fig, self.axes = getfigure()
        self.output = widgets.VBox([self.xlims, self.ylims, output])
        self.vb1 = widgets.VBox([title, self.srcdir, self.destdir, self.rescan,
                                 self.dsel, self.scale, self.skip,
                                 self.save,
                                 self.display])
        self.out = widgets.HBox([self.vb1, self.output])

        self.rescan.on_click(self.rsclick)
        self.save.on_click(self.dosave)
        self.dsel.observe(self.dupdate, 'value')
        self.scale.observe(self.imgchange, 'value')
        self.skip.observe(self.imgchange, 'value')
        self.xlims.observe(self.limchange, 'value')
        self.ylims.observe(self.limchange, 'value')

        self.srcdir_ = None
        self.destdir_ = None
        self.srcsubdir_ = None
        self.destsubdir_ = None
        self.imglist = None
        self.img = None
        self.lines = None

    def rsclick(self, _a):
        """Click on rescan button."""
        self.srcdir_ = self.srcdir.value.rstrip('/')
        self.destdir_ = self.destdir.value.rstrip('/')
        flist = [f.split('/')[-1]
                 for f in glob(self.srcdir_+'/*') if os.path.isdir(f)]
        self.dsel.options = sorted(flist)
        self.dupdate(_a)

    def getjson(self):
        """Get json of data to save."""
        data = {'source': self.srcsubdir_,
                'scale': self.scale.value,
                'skip': self.skip.value,
                'xlim': self.xlims.value,
                'ylim': self.ylims.value}
        return json.dumps(data)

    def tryload(self):
        """Try to load a json file for the current path."""
        try:
            _f = open(self.destsubdir_+'/caopt.json', 'r')
            js_ = json.load(_f)
            _f.close()
            return js_
        except Exception:
            return None

    def dosave(self, _a):
        """Create output directory and do save."""
        if self.img is None:
            self.display.value = "Nothing to save."
            return
        if not os.path.isdir(self.destsubdir_):
            try:
                os.mkdir(self.destsubdir_)
            except Exception:
                self.display.value = "Could not create output directory."
                return
        try:
            _f = open(self.destsubdir_+'/caopt.json', 'w')
            _f.write(self.getjson())
            _f.close()
            self.display.value = "Saved!"
        except Exception:
            self.display.value = "Error writing to file."

    def updatedisplay(self):
        """Let user know what will be saved."""
        js_ = self.getjson().replace(', "', ',\n "')
        outfile = self.destsubdir_[(-10):] + '/caopt.json'
        self.display.value = f'Save to ...{outfile}:\n\n{js_}'

    def limchange(self, _a):
        """Changes to limits slider"""
        _ax = self.axes
        if self.img is not None:
            if self.lines is None:
                _ax.clear()
                _ax.imshow(self.img)
                self.lines = [_ax.plot(self.xlims.value,
                                       [self.ylims.value[0]]*2, '-oC1')[0],
                              _ax.plot(self.xlims.value,
                                       [self.ylims.value[1]]*2, '-oC1')[0],
                              _ax.plot([self.xlims.value[0]]*2,
                                       self.ylims.value, '-oC1')[0],
                              _ax.plot([self.xlims.value[1]]*2,
                                       self.ylims.value, '-oC1')[0]]
            else:
                self.lines[0].set_data(self.xlims.value,
                                       [self.ylims.value[0]]*2)
                self.lines[1].set_data(self.xlims.value,
                                       [self.ylims.value[1]]*2)
                self.lines[2].set_data([self.xlims.value[0]]*2,
                                       self.ylims.value)
                self.lines[3].set_data([self.xlims.value[1]]*2,
                                       self.ylims.value)
                self.fig.canvas.draw()
        self.updatedisplay()

    def imgchange(self, _a):
        "Once skip changes"
        self.img = ut.imread(self.imglist[self.skip.value], self.scale.value)
        self.xlims.max = self.img.shape[1]-1
        self.ylims.max = self.img.shape[0]-1
        self.lines = None
        self.limchange(_a)

    def dupdate(self, _a):
        """Changed subdir selection."""
        self.srcsubdir_ = self.srcdir_+'/'+self.dsel.value
        self.destsubdir_ = self.destdir_+'/'+self.dsel.value
        self.imglist = ut.getimglist(self.srcsubdir_)
        if len(self.imglist) == 0:
            self.skip.max = 0
            self.xlims.max = 0
            self.ylims.max = 0
            self.img = None
            self.axes.clear()
            self.lines = None
            self.display.value = ""
        else:
            self.skip.max = len(self.imglist)-1
            data = self.tryload()
            if data is not None:
                self.scale.value = data['scale']
                self.skip.value = data['skip']
            self.img = ut.imread(self.imglist[self.skip.value],
                                 self.scale.value)
            self.xlims.max = self.img.shape[1]-1
            self.ylims.max = self.img.shape[0]-1
            if data is not None:
                self.xlims.value = data['xlim']
                self.ylims.value = data['ylim']
            elif self.xlims.value[1] == 0:
                self.xlims.value = [int(0.33*self.img.shape[1]),
                                    int(0.67*self.img.shape[1])]
                self.ylims.value = [int(0.33*self.img.shape[0]),
                                    int(0.67*self.img.shape[0])]
            self.lines = None
            self.limchange(_a)
            if data is not None:
                self.display.value = "Loaded saved json data."

    def show(self):
        """Call to redirect output to notebook"""
        return self.out

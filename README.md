# Plant Segmentation with Graph Cuts

![](images/results.gif)

This package implements a graph-cuts based algorithm to segment overhead image sequences of plants, producing a distinct label for each plant that is consistent across the various frames. The package asks users to select a region of interest within which to segment plants—this region is annotated in the first image of the sequence and subsequent images are automatically aligned. Then, the algorithm uses local and pairwise edge-based evidence to perform a segmentation, matching connected components across frames, separating merged components from overlapping plants, and enforcing connectivity within each segmented plant in each frame.

## Setup

We recommend using [Conda](https://www.anaconda.com/download) to setup the environment for this package, using the provided environment setup files to install all required dependencies. Create the `plseg` environment by running:
```
conda env create -f plseg/environment.yml
```

Once the environment is created, remember to "activate" it with:
```
conda activate plseg
```

Note that this environment will include all required dependencies for both components of the workflow described below: (1) the UI to specify regions of interest; and (2) the script to perform actual segmentation. In case you plan to run these on separate machines, we also provide separate environment files `plseg/env-ui.yml` and `plseg/env-lbl.yml` for these two components respectively, which create environments named `plseg-ui` and `plseg-lbl`. You can create and activate only the environment you need on each machine.

## Workflow

We assume that every image sequence is stored in its own sub-directory as PNG or JPEG files (with extensions `.png`, `.jpg`, or `.jpeg`), with the sorted order of filenames indicating sequence position. All frames are assumed to be taken by the same camera at the same resolution with at most some camera translation between frames.

The first step of the workflow is interactive and involves specifying an initial number of images to skip before starting segmentation (e.g., to skip over setup images), a region of interest (ROI) in the first image of the sequence, and the resolution at which to carry out the segmentation (as a downscale factor). These parameters will be saved as a JSON file in a target directory, along with the path of the corresponding source directory. 

The second part of the workflow involves calling a script to carry out the sequential segmentation, which will store cropped and aligned images of the ROI in each frame, a visualization of the corresponding segmentation, and an `.npz` file with the label matrix in the target directory. This second step is not interactive, and if needed can be run by submitting the script as a job to a scheduler.

### Specify ROI and Parameters Interactively

![](images/uidemo.gif)

Our UI for specifying ROIs, scale, skip, etc. is a Jupyter notebook run using [Voila](https://github.com/voila-dashboards/voila):
``` shell
conda activate plseg  # or conda activate plseg-ui
voila ./cropset.ipynb
```
This should open the UI in your browser. If your data is stored on a remote machine, you can also access this UI remotely with SSH port-forwarding. For example:
``` shell
ssh -L 8888:localhost:8888 username@server.edu
cd /path/to/code
conda activate plseg  # or conda activate plseg-ui
voila --port 8888 --no-browser ./cropset.ipynb 
```
You can then access the UI on your local machine by just going to `http://127.0.0.1:8888/` in your browser on your local machine.

In the UI, begin by specifying base source and target directories---image sequence directories are assumed to be sub-directories of the base source directories, and segmentation outputs will be stored in sub-directories of the base target directory, i.e., segmentation outputs of a source sequence stored in `/basedir/seqname` will be stored in the target `/targetdir/seqname` sub-directory. Enter paths to these base directories in the text-box, and click on __Set__. 

From the drop-down, pick a source sequence sub-directory, specify the number of frames to __skip__ at the beginning of each sequence (recall, image files are sorted by filename) and a __scale__ factor that is a percentage of the original size,  and use the `X` and `Y` sliders to specify a bounding box for the ROI on the shown first image of the sequence (after any skips). Once you're done, click on **Save** to store these parameters as a JSON file in the corresponding target sub-directory (which will be created if necessary). Repeat this process for different sequence sub-directories.

**Important:** If you plan on running the UI on a different machine than the one in which you will run the segmentation script in the next step below, it is important that the full path to the source base directory be the same on both machines  (if you are running the UI through SSH forwarding, paths on the server you are SSH-ing into should be the same as those on which the segmentation script will be run).

### Run Segmentation Script

![](images/lbldemo.gif)

Once you have created the parameter JSON files for a sequence, you can use the `plabel.py` script to do the actual segmentation. Activate the `plseg` (or `plseg-lbl`) conda environment, and then call the `plabel.py` script with the target directory path of that sequence (which should already have the parameter JSON file stored inside). You can execute `plabel.py` from a job script as well (remember to activate the right conda environment inside the job script).

For every image in the source sequence (after the skipped initial frames), the script will generate two corresponding image files: with a modified name of `-crop` showing the cropped ROI (as tracked across frames), and of `-seg` showing a visualization of the segmentation. It will also create a file called `labels.npz` that can be loaded in python using `labels = numpy.load('labels.npz')['labels']`. This will be a `H x W x N` integer matrix, where `H` and `W` are the height and width of the image, and `N` the number of frames. Each segmented plant in the sequence will have a positive integer ID, with values in `labels` set to that ID for identified pixels across all frames. Background pixels will be set to zero.

**[Optional] Specify Segmentation Parameters:** The segmentation method uses a number of internal parameters (related to the graph-cuts objective, criteria for merging, etc.) which will typically be run with their default values. If you do want to use different values, you will need to specify these in JSON format by placing it as a `segopt.json` file in the target directory. The full list of possible parameters, their default values, and description are below:


| Parameter Name  | Default | Description                                                                    |
|-----------------|---------|--------------------------------------------------------------------------------|
| `grthresh`      | 8       | Unary cost = Sigmoid(-(a+grthresh) / grsensitivity) (a is 2nd channel in Lab). |
| `grsensitivity` | 4       | See above.                                                                     |
| `fsz`           | 8       | Derivative filter size to compute edge weights.                                |
| `fsgm`          | 2       | Sigma^2 used to define Gaussian for DoG edge filters.                          |
| `fsensitivity`  | 4       | Edge weight exp(-grad^2 / mean(grad^2) / fsensitivity).                        |
| `uwt`           | 10000   | Weight on unary cost (after weighting, will be rounded to int32).              |
| `ewt`           | 5000    | Weight on edge cost (after weighting, will be converted to int32).             |
| `zwt`           | 2500    | Relative weight on edge from same pixel in previous frame.                     |
| `ccnbd`         | 10      | Distance when merging connected components to identify as same plant.          |
| `joinit`        | 25      | Number of iterations to connect disconnected components of same plant.         |
| `joininc`       | 100     | Amount by which to change unary in each iteration of joining components.       |


 Note that you only need to include parameters that you want to set to a value different from the default. For example, a JSON file to reduce the `ewt` and `zwt` parameters would look like:
``` json
{ "ewt": 4000, "zwt": 3000 }
```

## LICENSE

[MIT License](LICENSE)

## Acknowledgments

This work was supported by the National Science Foundation under award no. [EF-1921728](https://nsf.gov/awardsearch/showAward?AWD_ID=1921728). Any opinions, findings, and conclusions or recommendations expressed in this material are those of the authors, and do not necessarily reflect the views of the National Science Foundation.

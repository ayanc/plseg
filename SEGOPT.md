# Specify Segmentation Parameters

The segmentation method uses a number of internal parameters (related to the graph-cuts objective, criteria for merging, etc.) which will typically be run with their default values. If you do want to use different values, you will need to specify these in JSON format by placing it as a `segopt.json` file in the target directory. The full list of possible parameters, their default values, and description are below:


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


 Note that you only need to include parameters that you want to set to a value different from the default. For example, a JSON file to change only the `ewt` and `zwt` parameters would look like:
``` json
{ "ewt": 4000, "zwt": 3000 }
```

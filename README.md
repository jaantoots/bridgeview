# Generate synthetic data with semantic labels

Bridgeview provides scripts to render visual, semantic and depth
images using [Blender]. It was developed to generate synthetic data
for training neural networks on images of bridges (but could probably
be extended to other types of models) for semantic segmentation.

- Generate data with `generate.py` (requires configuration files)
- Add trees randomly or from a file using `treegrow.py`

The `render` package provides the plumbing methods using Blender. Main
functionality is rendering the visual, semantic and depth data.
Additional useful modules for quickly defining labels and multiple
textures for objects and procedural modifications are provided.

## Overview

`generate.py` takes a suitable Blender model file and configuration
files to render visual, semantic and depth images.

The model file should have correctly named *Objects* as these are the
basis for texturing and labelling. Objects with the same name (with
instances distinguished by optional dot-separated counters as usual,
i.e. "box", "box.001", etc.) are interpreted as a class and also
textured using the same material. If a different behaviour is desired,
the labels can be parsed accordingly later.

`generate.py` needs to be provided with a meta-configuration file
pointing to other files. Of these, `render` for render parameters,
`labels` for defining colours to use for labels, `textures` for
defining the appropriate textures for different objects and `out` as
an empty placeholder need to be provided. Trees (or any other objects
to be placed repeatedly on the landscape) can be placed at run-time if
at least one instance of the objects is present in the file and
`trees` file is provided (also see [treegrow](#placing-trees)). The
format of these files is discussed (with example configurations) in
[examples](examples/).

### Examples

Generate all images using the GPU when possible (for visual and depth
rendering using Cycles Render, no effect on semantic rendering):

```
./generate.py path/to/model.blend --conf path/to/model-conf.json \
    --name 2016-09-09-some-descriptive-folder-name --size 128 --gpu
```

Generate only points (and then use multiple instances to render
different types of images):

```
./generate.py path/to/model.blend --conf path/to/model-conf.json \
    --name 2016-09-09-model-commitinfo --size 128 --render
```

Generate visual and depth images using a specific GPU (if the folder
and configuration files exist, the previously generated points are
used automatically, and there is no need to specify the number of
images):

```
./generate.py path/to/model.blend --conf path/to/model-conf.json \
    --name 2016-09-09-model-commitinfo --render visual depth --gpu CUDA_1
```

### Placing trees

`treegrow.py` can be used to place objects randomly in a scene
starting from a list of seed objects to use. This is useful for
creating trees and other vegetation in the model quickly and hopefully
without collisions with other objects. Trees are grown in a chain
around the starting point such that on average a small cluster is
formed.

If this is run from the command-line, it is possible to output the
coordinates of placed objects to a file. This file can then be used by
`generate.py` to place them at run-time only.

### Render package

The main functionality interfacing with the Blender API is implemented
in the `render` package.

- `render.render` provides the actual rendering methods. However,
  results can be unexpected if one tries to call methods in an order
  that does not satisfy visual > semantic > depth; this is by design
  as the semantic and depth rendering methods need to be destructive
  with respect to some configuration settings.
- `render.labels` and `render.textures` are used for labelling and
  texturing respectively. Both also contain methods to help set up the
  configuration.
- `render.helpers` contains (among other things) the `BoundingSphere`
  and `CameraLine` classes. These are very useful for writing the
  configuration, to visualise the spheres and lines being defined.

## Usage

[Blender] must be installed and it is
recommended to have it in `PATH`.

Install dependencies (`exrconvert.py` needs Python2):

```
pip3 install -r requirements.txt
pip install -r requirements2.txt
```

Assuming `blender` is in `PATH`, scripts can be run
normally. Otherwise, if for some reason having `blender` in `PATH` is
not possible, provide the executable as an environment variable
`BLENDER=/path/to/blender` (conversely, this should normally be
unset).

Help is available for the scripts (a model file needs to be given):

```
./generate.py MODEL --help
./treegrow.py MODEL --help
```

Blender normally uses its internal Python but this does not find
packages in the working directory nor custom dependencies. For this
reason, use the local script for launching Blender when working on
model files or debugging: `./blender ...`.

For example, help for modules is then also available as:

```
./blender --background --python FILE -- --help
```

Further documentation of methods can be accessed using Blender
interactively.

## License

Copyright (C) 2016  Jaan Toots

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

[Blender]: https://www.blender.org/

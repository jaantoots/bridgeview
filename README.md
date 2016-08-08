# Generate labelled data of bridges

Package provides methods to generate the data using Blender. Main functionality
is rendering the visual, semantic and depth scenes implemented in `render.py`.
Additional useful methods for quickly defining labels and multiple textures for
objects are provided.

# Usage

Similar to the usage of `bridge-render` which provides high-level functionality
using this package.

Install all necessary packages:

```
$ pip3 install -r requirements.txt
```

Blender needs to be told to use system Python and find modules in the working
directory (`path-to-blender` only needs to be provided if `blender` is not in
`$PATH`):

```
$ source set-blender.sh [path-to-blender]
```

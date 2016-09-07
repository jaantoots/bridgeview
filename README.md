# Rendering and data generation

This contains the methods for data generation.

- `generate.py` is used for all data generation
- Configuration files (in JSON) are required for data generation (see
  `render` package help and examples in `models`)
- It is possible to add trees randomly or from a file using
  `treegrow.py`
- `exrconvert.py` can be used for converting depth images from OpenEXR
  to plain text (needs Python2 due to dependencies)

The `render` package provides the plumbing methods using Blender. Main
functionality is rendering the visual, semantic and depth scenes as
implemented in `render/render.py`.  Additional useful modules for
quickly defining labels and multiple textures for objects and
procedural modifications are provided.

## Usage

Install all necessary packages:

```
pip3 install -r requirements.txt
pip install -r requirements2.txt
```

Assuming `blender` is in `$PATH`, scripts can be run as is (a model
file needs to be given):

```
./generate.py MODEL --help
./treegrow.py MODEL --help
```

Otherwise, as Blender needs to be told to look for modules in the
working directory (`path-to-blender` needs to be provided if `blender`
is not in `$PATH`):

```
source set-blender.(sh|zsh) [path-to-blender]
```

Help for modules is then available as:

```
blender --background --python FILE -- --help
```

Sourcing the files to alias `blender` is also useful for using the
`bridge` package when setting up the model files.

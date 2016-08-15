# Rendering and data generation

This contains the porcelain methods for data generation and links to
other necessary directories.

- Configuration files (in JSON) are required for data generation (see
  `bridge` package and examples in `models`)
- It is possible to add trees randomly or from a file using `treegrow`
- `exrconvert` is useful for converting depth images from OpenEXR to
  plain text (needs Python2 due to libraries)

## Usage

Install all necessary packages:

```
pip3 install -r requirements.txt
pip install -r requirements2.txt
```

Blender needs to be told to find modules in the working directory
(`path-to-blender` only needs to be provided if `blender` is not in
`$PATH`):

```
source set-blender.sh [path-to-blender]
```

Help for modules is available:

```
blender --background --python FILE -- --help
```

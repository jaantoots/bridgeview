# Rendering and data generation

This contains the specific files for data generation.

- JSON files contain the configurations for different methods
- `modify` is currently for use in interactive Blender sessions
- `exrconvert` is Python 2, everything else is Python 3

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

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

[Blender](https://www.blender.org/) must be installed and it is
recommended to have it in `PATH`.

Install dependencies:

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

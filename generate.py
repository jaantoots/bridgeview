"""Run Blender in background mode with model and this script to generate data.

For help: blender --background --python generate.py -- --help

"""
import sys
import os
import shutil
import datetime
import json
import argparse
import bpy  # pylint: disable=import-error
import bridge
import treegrow


class Generate():
    """Generate random views of the model with textures and labels.

    Configurations for bridge package objects loaded from files
    specified in the argument configuration file. Data is generated
    with independently random sun and camera positions (and textures).

    """

    def __init__(self, path: str, files: dict):
        """Initialise with specified configuration files and output to path."""
        clean_scene()
        self.objects = bpy.data.objects[:]
        self.path = path
        self.files = files

        # Initialise objects with configurations from files
        self.labels = bridge.labels.Labels(self.objects)
        self.labels.read(self.files['labels'])
        self.textures = bridge.textures.Textures(self.objects)
        self.textures.read(self.files['textures'])
        # Render file can be created automatically but probably not
        # when running, spheres file is optional and defaults to None
        self.render = bridge.render.Render(self.objects, self.files['render'],
                                           self.files.get('spheres'))

    def grow_trees(self):
        """Grow trees according to the coordinates specified in file."""
        with open(self.files['trees']) as file:
            trees = json.load(file)
            grower = treegrow.TreeGrow(self.render.landscape, trees)
            grower.grow_all()

    def point(self):
        """Return a random sun and camera setup."""
        sun_rotation = self.render.random_sun()
        lens, location, rotation = self.render.random_camera()
        return {'sun_rotation': sun_rotation, 'camera_lens': lens,
                'camera_location': location, 'camera_rotation': rotation}

    def run(self, size: int=1, all_levels: bool=False):
        """Generate the data, `size` sets of visual images and labels.

        If data output file already exists, only create missing images
        (`size` is ignored). Otherwise, generate points to file and
        create images.

        """
        # If output file is not empty, load points, otherwise generate points
        out_path = self.files['out']
        if os.path.getsize(out_path):
            print("==Load points from file==")
            with open(out_path) as file:
                data = json.load(file)
        else:
            print("==Generate points==")
            data = {"{:03d}".format(i): self.point() for i in range(size)}
            with open(out_path, 'w') as file:
                json.dump(data, file)

        print("==Render visual images==")
        for seq, point in data.items():
            path = os.path.join(self.path, "{:s}.vis.png".format(seq))
            if os.path.isfile(path):
                continue
            self.textures.texture()
            self.render.displace_landscape()
            self.render.place_sun(point['sun_rotation'])
            self.render.place_camera(point['camera_lens'],
                                     point['camera_location'],
                                     point['camera_rotation'])
            self.render.render(path)

        print("==Render semantic labels==")
        levels = range(3) if all_levels else [2]
        for level in levels:
            # Only change materials once per level for efficiency
            self.labels.color_level(level)
            for seq, point in data.items():
                path = os.path.join(self.path,
                                    "{:s}.sem.{:d}.png".format(seq, level))
                if os.path.isfile(path):
                    continue
                self.render.place_camera(point['camera_lens'],
                                         point['camera_location'],
                                         point['camera_rotation'])
                self.render.render_semantic(path)

        print("==Render depth==")
        for seq, point in data.items():
            path = os.path.join(self.path, "{:s}.dep.exr".format(seq))
            if os.path.isfile(path):
                continue
            self.render.place_camera(point['camera_lens'],
                                     point['camera_location'],
                                     point['camera_rotation'])
            self.render.render_depth(path)


def clean_scene():
    """Clear all cameras and lamps (suns) from the model."""
    for obj in [obj for obj in bpy.data.objects
                if obj.type == 'CAMERA' or obj.type == 'LAMP']:
        bpy.ops.object.select_all(action='DESELECT')
        obj.select = True
        bpy.ops.object.delete(use_global=False)


def main():
    """Parse the arguments and generate data."""
    print("\n==> {:s}".format(__file__))
    # Get all arguments after '--'
    try:
        argv = sys.argv[sys.argv.index('--') + 1:]
    except ValueError:
        argv = []

    # Parse arguments
    prog_text = "blender MODEL --background --factory-startup" \
                " --python {:s} --".format(os.path.relpath(__file__))
    parser = argparse.ArgumentParser(
        prog=prog_text, formatter_class=argparse.RawDescriptionHelpFormatter,
        description=__doc__, epilog="===")
    parser.add_argument("-n", "--name", type=str,
                        help="Name of the generation run (optional)")
    parser.add_argument("-c", "--conf", metavar="FILE", default="conf.json",
                        help="Configuration file (default: conf.json)")
    parser.add_argument("-s", "--size", metavar="N", type=int, default=4,
                        help="Number of images to generate (default: 4)")
    parser.add_argument(
        "-l", "--all-levels", action='store_true',
        help="Generate all levels of semantic labels (default only level 2).")
    parser.add_argument(
        "-t", "--grow-trees", action="store_true",
        help="Place trees to specified coordinates, requires existing file.")
    args = parser.parse_args(argv)

    # Paths
    subpath = 'data/'
    if args.name is None:
        subpath += datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
    else:
        subpath += datetime.date.today().strftime('%Y-%m-%d-') + args.name
    path = os.path.abspath(subpath)

    # Copy files into path
    with open(args.conf) as file:
        files = json.load(file)
    os.makedirs(path, exist_ok=True)
    for filepath in files.values():
        filepath = os.path.join(os.path.dirname(args.conf), filepath)
        if not os.path.isfile(os.path.join(path, os.path.basename(filepath))):
            shutil.copy(filepath, path)
    # And make files dict point to the new files
    for key in files:
        files[key] = os.path.join(path, os.path.basename(files[key]))

    gen = Generate(path, files)
    if args.grow_trees:
        gen.grow_trees()
    gen.run(args.size, args.all_levels)
    print()

if __name__ == "__main__":
    main()

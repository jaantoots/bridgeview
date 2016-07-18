"""Run Blender in background mode with model and this script to
generate the data.

For help: blender --background --python generate.py -- --help

"""
import sys
import os
import shutil
import datetime
import json
import argparse
import bpy # pylint: disable=import-error
import bridge

class Generate():
    """Generate random views of the model with textures and labels

    Configurations for bridge package objects loaded from files
    specified in the argument configuration file. Data is generated
    with independently random sun and camera positions (and textures).

    """

    def __init__(self, path: str, files: dict):
        self.objects = bpy.data.objects[:]
        self.path = path
        self.files = files
        self._load()

    def _load(self):
        """Initialise objects with configurations from files"""
        # Labels file needs to be manually created
        labels_path = os.path.join(self.path, self.files['labels'])
        self.labels = bridge.labels.Labels(self.objects)
        self.labels.read(labels_path)

        # Textures file needs to be manually created
        textures_path = os.path.join(self.path, self.files['textures'])
        self.textures = bridge.textures.Textures(self.objects)
        self.textures.read(textures_path)

        # Render configuration can reasonably be expected to vary between different iterations
        render_path = os.path.join(self.path, self.files['render'])
        if os.path.isfile(render_path):
            self.render = bridge.render.Render(self.objects, render_path)
        else:
            self.render = bridge.render.Render(self.objects)
            self.render.write_conf(render_path)

    def point(self):
        """Return a random sun and camera setup"""
        sun_rotation = self.render.random_sun()
        camera_lens, camera_location, camera_rotation = self.render.random_camera()
        return {'sun_rotation': sun_rotation, 'camera_lens': camera_lens,
                'camera_location': camera_location, 'camera_rotation': camera_rotation}

    def run(self, size: int=1):
        """Generate the data, `size` sets of visual images and labels

        If data output file already exists, only create missing images
        (`size` is ignored). Otherwise, generate points to file and
        create images.

        """
        # Check if output file is not empty, load points from file, or generate points
        out_path = os.path.join(self.path, self.files['out'])
        if os.path.getsize(out_path):
            with open(out_path) as file:
                data = json.load(file)
        else:
            data = {"{:03d}".format(i): self.point() for i in range(size)}
            with open(out_path, 'w') as file:
                json.dump(data, file)

        # Render the visual images
        for seq, point in data.items():
            path = os.path.join(self.path, "{:s}.vis.png".format(seq))
            if os.path.isfile(path):
                continue
            self.render.place_sun(point['sun_rotation'])
            self.render.place_camera(
                point['camera_lens'], point['camera_location'], point['camera_rotation'])
            self.textures.texture() # Texture randomly if more than one texture provided for group
            self.render.render(path)

        # Render semantic labels
        for level in range(3):
            self.labels.color_level(level) # Only change materials once per level for efficiency
            for seq, point in data.items():
                path = os.path.join(self.path, "{:s}.sem.{:d}.png".format(seq, level))
                if os.path.isfile(path):
                    continue
                self.render.place_camera(
                    point['camera_lens'], point['camera_location'], point['camera_rotation'])
                self.render.render_semantic(path)

def main():
    """Parse the arguments and generate data"""
    print("\n==> {:s}".format(__file__))
    # Get all arguments after '--'
    try:
        argv = sys.argv[sys.argv.index('--') + 1:]
    except ValueError:
        argv = []

    # Parse arguments
    prog_text = "blender MODEL --background --factory-startup --python {:s} --".format(__file__)
    parser = argparse.ArgumentParser(prog=prog_text,
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description=__doc__, epilog="===")
    parser.add_argument("-n", "--name", type=str, help="Name of the generation run (optional)")
    parser.add_argument("-c", "--conf", metavar="FILE", default="conf.json",
                        help="Configuration file (default: conf.json)")
    parser.add_argument("-s", "--size", metavar="N", type=int, default=4,
                        help="Number of images to generate")
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
    for file in files.values():
        if not os.path.isfile(os.path.join(path, file)):
            shutil.copy(file, path)

    gen = Generate(path, files)
    gen.run(args.size)
    print()

if __name__ == "__main__":
    main()

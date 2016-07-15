"""Generate the data

This should be called as a Blender script:

blender MODEL --background --factory-startup --python generate.py -- \
[OPTIONS]

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
        camera_location, camera_rotation = self.render.random_camera()
        return {'sun_rotation': sun_rotation,
                'camera_location': camera_location, 'camera_rotation': camera_rotation}

    def run(self, size: int=1):
        """Generate the data, `size` sets of visual images and labels"""
        # Get the points and write them to the output file
        data = {"{:03d}".format(i): self.point() for i in range(size)}
        out_path = os.path.join(self.path, self.files['out'])
        with open(out_path, 'w') as file:
            json.dump(data, file)

        # Render the visual images
        for seq, point in data.items():
            self.render.place_sun(point['sun_rotation'])
            self.render.place_camera(point['camera_location'], point['camera_rotation'])
            self.textures.texture() # Texture randomly if more than one texture provided for group
            self.render.render(self.path, seq)

        # Render semantic labels
        for level in range(3):
            self.labels.color_level(level) # Only change materials once per level for efficiency
            for seq, point in data.items():
                self.render.place_camera(point['camera_location'], point['camera_rotation'])
                self.render.render_semantic(level, self.path, seq)

def main():
    """Parse the arguments and generate data"""
    # Get all arguments after '--'
    try:
        argv = sys.argv[sys.argv.index('--') + 1:]
    except ValueError:
        argv = []

    # Parse arguments
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", "--name", type=str, help="Name of the generation run (optional)")
    parser.add_argument("-c", "--conf", metavar="FILE", default="conf.json",
                        help="Configuration file")
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
        files = json.load(args.conf)
    os.makedirs(path)
    for file in files:
        shutil.copy(file, path)

    gen = Generate(path, files)
    gen.run(args.size)

if __name__ == "__main__":
    main()

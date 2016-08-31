"""Provides methods for rendering the labelled model."""
import json
import os
import hashlib
import glob
import numpy as np
import bpy  # pylint: disable=import-error
from . import helpers


def new_camera(resolution: list):
    """Add a camera to the scene and set the resolution for rendering."""
    bpy.ops.object.camera_add()
    camera = bpy.context.object
    bpy.data.scenes[0].camera = camera
    bpy.data.scenes[0].render.resolution_x = resolution[0]
    bpy.data.scenes[0].render.resolution_y = resolution[1]
    bpy.data.scenes[0].render.resolution_percentage = 100
    camera.data.clip_end = 1e5  # Maybe set dynamically if ground plane larger
    return camera


class Render():
    """Configure and render the scene.

    Parameters are read from conf_file. During testing and setup one
    can be generated with the default parameters. It is possible to
    place the sun and the camera randomly and create the
    renders. However, generating the sun and camera positions
    beforehand allows doing all the visual renders first and the
    semantic renders only afterwards (recommended, as semantic and
    depth renders may break visual rendering setup).

    Blender file should be set up with the correct settings: sky,
    clouds, mist and Cycles parameters. Only Cycles samples and film
    exposure are set from the configuration file with the expectation
    that these might be necessary for finetuning the quality.

    Configuration options:

    landscape (list): List of object names that are not part of the
        bridge. The first item is used for choosing the camera
        position. Additional elements are excluded when calculating
        the bounding sphere automatically. If spheres are provided in
        a file, additional elements are optional.

    sun_theta (list): Range of sun's polar angle.

    sun_size (float): Size of the sun (sharpness of shadows).

    sun_strength (float): Strength of sunlight (balance with exposure
        determines relative brightness of sky.

    sun_color (list): RGBA of the color of sunlight (#FFFFF8 seems
        good and the scene is also influenced by the sky texture which
        means there is no need to worry about the color too much).

    camera_distance_factor (dict: mean, sigma): Relative camera
        distance (in terms of bounding sphere radius) is from a
        Gaussian distribution with given mean and sigma.

    camera_clearance (list or float): Camera clearance above
        landscape. List is used as a uniform range. Float is used as a
        lower limit and camera_theta is used otherwise.

    camera_floor (float): Absolute floor (Z position) for the camera
        position. It might be useful to set this to the water level if
        applicable.

    camera_lens (dict: mean, log_sigma): Camera lens focal length is
        drawn from lognormal distribution with the given mean (in mm)
        and log_sigma.

    camera_theta (list): Range of camera's polar angle. This is only
        looked at if camera_clearance is not provided or is a float.

    camera_noise (float): Noise to add to the camera angle to increase
        viewpoint variety.

    resolution (list: x, y): Resolution of rendered images.

    film_exposure (float): Film exposure for visual renders (see note
        at sun_strength).

    cycles_samples (int): Number of samples to render, higher numbers
        decrease noise but take longer.

    sky (dict): Sky configuration (see help for set_sky).

    """

    def __init__(self, objects: list, conf_file=None, spheres_file=None,
                 lines_file=None):
        """Create Render object for specified Blender objects."""
        # Load configuration
        if conf_file is None:
            self._default()
        else:
            with open(conf_file) as file:
                self.opts = json.load(file)

        # Initialise objects, terrain should be the first item in landscape
        self.objects = objects[:]
        self.landscape = helpers.all_instances(
            self.opts['landscape'][0], self.objects)[0]
        self.landscape_tree = helpers.landscape_tree(self.landscape)

        # Remove landscape for bounding sphere calculation
        for obj_name in self.opts['landscape']:
            for obj in helpers.all_instances(obj_name, self.objects):
                self.objects.remove(obj)

        # Initialise bounding spheres for camera views
        if spheres_file is None:
            sphere = helpers.BoundingSphere()
            self.spheres = {}
            self.spheres['default'] = sphere.find(self.objects)
        else:
            with open(spheres_file) as file:
                self.spheres = json.load(file)

        # Load camera lines if provided
        self.camera_lines = None
        if lines_file is not None:
            with open(lines_file) as file:
                camera_lines = json.load(file)
                # Convert points to np.array
                self.camera_lines = {name: {point: np.array(loc)
                                            for point, loc in line.items()}
                                     for name, line in camera_lines}

        self.sun = None
        self.camera = new_camera(self.opts['resolution'])

    def _default(self):
        """Default configuration parameters."""
        self.opts = {}
        self.opts['landscape'] = ["Landscape"]  # Parts not part of the bridge
        self.opts['sun_theta'] = [0, 17/18 * np.pi/2]  # Higher than 5 deg
        self.opts['sun_size'] = 0.02  # Realistic sun is smaller than default
        self.opts['sun_strength'] = 8  # Good starting point
        self.opts['sun_color'] = [1.0, 1.0, 251/255, 1.0]  # High noon sun
        self.opts['camera_distance_factor'] = {"mean": 4/12, "sigma": 1/12}
        self.opts['camera_clearance'] = [1.5, 2.3]  # Distance above landscape
        self.opts['camera_lens'] = {"mean": 16, "log_sigma": 1/4}
        self.opts['camera_theta'] = [np.pi/3, 17/18 * np.pi/2]  # Not too high
        self.opts['camera_noise'] = 0.01  # Rotation sigma [x, y, z] or float
        self.opts['resolution'] = [512, 512]  # [x, y] pixels
        self.opts['film_exposure'] = 2  # Balances with sun strength and sky
        self.opts['cycles_samples'] = 64  # Increase to reduce noise
        self.opts['sky'] = {}  # Several possibilities here, see set_sky(

    def write_conf(self, conf_file: str):
        """Write current configuration to conf_file."""
        with open(conf_file, 'w') as file:
            json.dump(self.opts, file)

    def random_sun(self):
        """Generate a random rotation for the sun."""
        theta = np.random.uniform(self.opts['sun_theta'][0],
                                  self.opts['sun_theta'][1])
        phi = np.random.uniform(0, 2*np.pi)
        return [theta, 0, phi]

    def place_sun(self, rotation=None):
        """Delete previous sun and create new at specified angle."""
        bpy.ops.object.select_all(action='DESELECT')
        if self.sun is not None:
            self.sun.select = True
            bpy.ops.object.delete()

        if rotation is None:
            rotation = self.random_sun()
        bpy.ops.object.lamp_add(type='SUN', location=(0, 0, 20),
                                rotation=rotation)
        self.sun = bpy.context.object

        # Set size, strength and sky
        self.sun.data.shadow_soft_size = self.opts['sun_size']
        emission = self.sun.data.node_tree.nodes['Emission']
        emission.inputs['Strength'].default_value = self.opts['sun_strength']
        emission.inputs['Color'].default_value = self.opts['sun_color']
        self.set_sky()  # Set sun direction and random clouds
        return self.sun

    def random_camera(self):
        """Generate a random camera position with the objects in view."""
        # Random focal length (approx median, relative sigma)
        focal_length = np.random.lognormal(
            np.log(self.opts['camera_lens']['mean']),
            self.opts['camera_lens']['log_sigma'])
        self.camera.data.lens = focal_length

        if self.camera_lines is not None:
            return self.random_camera_line(focal_length)
        else:
            return self.random_camera_sphere(focal_length)

    def random_camera_sphere(self, focal_length):
        """Choose a camera position around a bounding sphere."""
        # Choose a sphere to render
        sphere = np.random.choice(list(self.spheres.values()))

        # Spherical coordinates of the camera position
        min_distance = sphere['radius'] / np.tan(self.camera.data.angle_y/2)
        while True:
            distance = min_distance * np.random.normal(
                self.opts['camera_distance_factor']['mean'],
                self.opts['camera_distance_factor']['sigma'])
            if (isinstance(self.opts.get('camera_clearance'), list)
                    or self.opts.get('camera_theta') is None):
                theta = np.pi/2
            else:
                theta = np.random.uniform(self.opts['camera_theta'][0],
                                          self.opts['camera_theta'][1])
            phi = np.random.uniform(0, 2*np.pi)
            # Location axes rotated due to default camera orientation
            location = sphere['centre'] + distance * np.array(
                [np.sin(theta)*np.sin(-phi),
                 np.sin(theta)*np.cos(phi),
                 np.cos(theta)])
            # Check if above landscape by at least specified amount
            if isinstance(self.opts.get('camera_clearance'), list):
                location = self._choose_height(location)
                break
            else:
                if self._check_height(location):
                    break

        # Set the camera to face near sphere centre
        rotation = np.array([theta, 0, np.pi + phi])
        rotation += np.random.randn(3) * self.opts['camera_noise']
        return focal_length, location.tolist(), rotation.tolist()

    def random_camera_line(self, focal_length):
        """Choose a camera position randomly on a line."""
        # Choose a location
        line = np.random.choice(list(self.camera_lines.values()))
        location = ((line['end'] - line['start']) * np.random.random()
                    + line['start'])

        while True:
            # Choose a rotation
            theta = np.pi/2 + np.random.normal(0, self.opts['camera_sigma'])
            phi = np.random.uniform(0, 2*np.pi)
            # Adjust rotation for non-standard axis
            rotation = np.array([theta, 0, phi - np.pi/2])
            # Check rotation
            direction = np.array([np.sin(theta)*np.cos(phi),
                                  np.sin(theta)*np.sin(phi),
                                  np.cos(theta)])
            # Have at least one bounding sphere centre in view
            for sphere in self.spheres.values():
                to_centre = sphere['centre'] - location
                cos_angle = (np.dot(direction, to_centre)
                             / np.linalg.norm(to_centre))
                if np.arccos(cos_angle) < self.camera.data.angle_y/2:
                    break

        rotation += np.random.randn(3) * self.opts['camera_noise']
        return focal_length, location.tolist(), rotation.tolist()

    def _choose_height(self, location):
        """Choose height for camera above ground."""
        clearance = self.opts['camera_clearance']
        closest_vertex, _, _ = self.landscape_tree.find(location)
        floor = closest_vertex[2]
        # Optionally, have a set absolute floor configured (e.g. water level)
        camera_floor = self.opts.get('camera_floor')
        if camera_floor is not None and camera_floor > floor:
            floor = camera_floor
        # Check clearance
        if (location[2] > floor + clearance[0]
                and location[2] < floor + clearance[1]):
            return location
        # Set and check new height
        location[2] = floor + np.random.uniform(clearance[0], clearance[1])
        return self._choose_height(location)

    def _check_height(self, location):
        """Check that camera is above ground and not too high."""
        closest_vertex, _, _ = self.landscape_tree.find(location)
        # Not breaking backwards compatibility when no clearance given
        if (self.opts.get('camera_clearance') is not None and
                location[2] > closest_vertex[2]
                + self.opts['camera_clearance']):
            return True
        return False

    def place_camera(self, focal_length=None, location=None, rotation=None):
        """Place the camera at specified location and rotation."""
        if focal_length is None:
            focal_length, location, rotation = self.random_camera()

        # Position and face centre
        self.camera.data.lens = focal_length
        self.camera.location = np.zeros(3)
        self.camera.rotation_euler[:] = rotation
        self.camera.location = location
        return self.camera

    def render(self, path: str):
        """Render the visual scene.

        Should be run before other types of rendering as some detailed
        settings (e.g. mist, indirect clamping, multiple importance)
        are only set in the Blend file. These settings are not
        guaranteed to be stable after semantic rendering that uses
        Blender Render and scene node tree will be cleared for depth
        rendering.

        """
        # Render with Cycles engine
        bpy.data.scenes[0].render.engine = 'CYCLES'
        bpy.data.scenes[0].cycles.film_exposure = self.opts['film_exposure']
        bpy.data.scenes[0].cycles.samples = self.opts['cycles_samples']
        bpy.data.scenes[0].render.filepath = path
        bpy.ops.render.render(write_still=True)

    def render_semantic(self, path: str):
        """Render the semantic labels.

        WARNING: This will probably screw up any careful configuration
        for visual renders.

        """
        # Render with Blender engine, disable node tree and anti-aliasing
        bpy.data.scenes[0].render.engine = 'BLENDER_RENDER'
        bpy.data.scenes[0].use_nodes = False
        bpy.data.scenes[0].render.use_antialiasing = False
        bpy.data.scenes[0].world.horizon_color = (0, 0, 0)
        bpy.data.scenes[0].render.filepath = path
        bpy.ops.render.render(write_still=True)

    def render_depth(self, path: str):
        """Render depth.

        WARNING: This will clear the scene node tree. Any custom
        configuration will be lost and other types of rendering will
        not work afterwards.

        """
        bpy.data.scenes[0].render.engine = 'CYCLES'
        # Use Compositing nodes for Scene
        bpy.data.scenes[0].use_nodes = True
        tree = bpy.data.scenes[0].node_tree

        # Clear the tree and create nodes
        tree.nodes.clear()
        render_layers = tree.nodes.new('CompositorNodeRLayers')
        file_output = tree.nodes.new('CompositorNodeOutputFile')
        file_output.format.file_format = 'OPEN_EXR'
        file_output.base_path = os.path.dirname(path)

        # Generate random collisionless filename
        sha = hashlib.sha1()
        sha.update(np.array(self.camera.location))  # Different for every image
        digest = sha.hexdigest()
        file_output.file_slots[0].path = digest + '_'
        bpy.data.scenes[0].render.filepath = os.path.join('/tmp',
                                                          digest + '.png')

        # Connect depth rendering to outputs
        tree.links.clear()
        tree.links.new(render_layers.outputs['Z'], file_output.inputs[0])

        # Write the render and rename
        bpy.ops.render.render(write_still=True)
        os.rename(
            glob.glob(os.path.join(os.path.dirname(path), digest + '*'))[0],
            path)

    def set_sky(self):
        """Set sun direction consistent with the sun and randomise clouds.

        Configuration options (optional):

        noise_scale (dict: mean, log_sigma): Noise scale for
            generating clouds is drawn from a lognormal distribution
            with given mean and log_sigma.

        cloud_ramp (dict: min, max, diff): Clouds are created by
            ramping the noise: black is drawn between min and max and
            white is diff away.

        translate (list): Translate the cloud texture randomly within
            given limits.

        """
        tree = bpy.data.worlds['World'].node_tree

        # Set sun direction in sky (angles seem to be correct from testing)
        theta = self.sun.rotation_euler[0]
        phi = self.sun.rotation_euler[2]
        tree.nodes['Sky Texture'].sun_direction = [np.sin(theta)*np.sin(phi),
                                                   -np.sin(theta)*np.cos(phi),
                                                   np.cos(theta)]

        # Randomise clouds
        sky = self.opts['sky']
        if 'noise_scale' in sky:
            tree.nodes['Noise Texture'].inputs['Scale'].default_value \
                = np.random.lognormal(np.log(sky['noise_scale']['mean']),
                                      sky['noise_scale']['log_sigma'])
        if 'cloud_ramp' in sky:
            ramp = tree.nodes['ColorRamp'].color_ramp
            ramp.elements[0].position = np.random.uniform(
                sky['cloud_ramp']['min'], sky['cloud_ramp']['max'])
            ramp.elements[1].position = ramp.elements[0].position \
                + sky['cloud_ramp']['diff']
        if 'translate' in sky:
            tree.nodes['Mapping'].translation[0] = np.random.uniform(
                sky['translate'][0], sky['translate'][1])

    def displace_landscape(self):
        """Randomise the location mapping for landscape variety."""
        tree = self.landscape.data.materials[0].node_tree
        mapping = tree.nodes.get('Mapping')
        if mapping is not None:
            mapping.translation = np.random.uniform(0, 1000, 3)

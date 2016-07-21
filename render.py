"""Provides methods for rendering the labelled model"""
import json
import os
import hashlib
import glob
import numpy as np
import bpy # pylint: disable=import-error
import mathutils # pylint: disable=import-error
from . import helpers

def new_camera(resolution: list):
    """Add a camera to the scene and set the resolution for rendering"""
    bpy.ops.object.camera_add()
    camera = bpy.context.object
    bpy.data.scenes[0].camera = camera
    bpy.data.scenes[0].render.resolution_x = resolution[0]
    bpy.data.scenes[0].render.resolution_y = resolution[1]
    bpy.data.scenes[0].render.resolution_percentage = 100
    camera.data.clip_end = 2000 # Maybe set dynamically if ground plane larger
    return camera

def landscape_tree(landscape):
    """Return a balanced tree of landscape vertices for find operations"""
    tree = mathutils.kdtree.KDTree(len(landscape.data.vertices))
    for i, vertex in enumerate(landscape.data.vertices):
        tree.insert(landscape.matrix_world * vertex.co, i)
    tree.balance()
    return tree

# TODO: Test BoundingSphere (returns too large spheres and bounding box is not always correct)
class BoundingSphere():
    """Return a sphere surrounding the objects

    Unfortunately this seems to return slightly weird stuff
    occasionally

    """

    def __init__(self, objects: list, centre=None):
        def minmax(index, axis):
            """Choose min or max depending on axis at bounding box corner index"""
            is_max = (index >> axis) % 2 # Control bit in index corresponding to axis
            if axis == 0:
                is_max ^= (index >> 1) % 2 # Cyclic index: 0 -> 00, 1 -> 01, 2 -> 11, 3 -> 10
            return max if is_max else min

        # For every corner i of bounding box, for axis j, choose min/max of all objects along axis
        box = np.array([[minmax(i, j)([(x.matrix_world * mathutils.Vector(x.bound_box[i]))[j]
                                       for x in objects]) for j in range(3)] for i in range(8)])
        self.centre = np.sum(box, axis=0)/8 if centre is None else centre
        self.radius = np.max(np.linalg.norm(box - self.centre, axis=1))

class Render():
    """Configure and render the scene

    Parameters are read from conf_file. During testing and setup one
    can be generated with the default parameters. It is possible to
    place the sun and the camera randomly and create the
    renders. However, generating the sun and camera positions
    beforehand allows doing all the visual renders first and the
    semantic renders only afterwards (recommended).

    """

    def __init__(self, objects: list, conf_file=None):
        # Load configuration
        if conf_file is None:
            self._default()
        else:
            with open(conf_file) as file:
                self.opts = json.load(file)

        # Initialise objects
        self.objects = objects[:]
        self.landscape = helpers.all_instances(self.opts['landscape'][0], self.objects)[0]
        self.landscape_tree = landscape_tree(self.landscape)

        # Remove landscape
        for obj_name in self.opts['landscape']:
            for obj in helpers.all_instances(obj_name, self.objects):
                self.objects.remove(obj)

        self.sphere = BoundingSphere(self.objects)
        self.sun = None
        self.camera = new_camera(self.opts['resolution'])

    def _default(self):
        """Default configuration parameters"""
        self.opts = {}
        self.opts['landscape'] = ["Landscape"] # Parts not part of the bridge
        self.opts['sun_theta'] = [0, 17/18 * np.pi/2] # Not lower than 5 deg from horizon
        self.opts['sun_size'] = 0.02 # Realistic sun is smaller than the default value
        self.opts['sun_strength'] = 2
        self.opts['sun_color'] = [1.0, 1.0, 251/255, 1.0] # High noon sun color
        self.opts['camera_distance_factor'] = {"mean": 4/12, "sigma": 1/12} # factor * min_distance
        self.opts['camera_lens'] = {"mean": 16, "log_sigma": 1/4} # Focal length lognormal dist
        self.opts['camera_theta'] = [np.pi/3, 17/18 * np.pi/2] # Not too high but above ground
        self.opts['camera_noise'] = 0.01 # Random rotation sigma [x, y, z] or float
        self.opts['resolution'] = [512, 512] # [x, y] pixels
        self.opts['film_exposure'] = 2 # Balances with sun strength and sky
        self.opts['cycles_samples'] = 64 # Increase to reduce noise
        self.opts['sky'] = {} # Several optional possibilities here, see set_sky(

    def write_conf(self, conf_file: str):
        """Write current configuration to conf_file"""
        with open(conf_file, 'w') as file:
            json.dump(self.opts, file)

    def random_sun(self):
        """Generate a random rotation for the sun"""
        theta = np.random.uniform(self.opts['sun_theta'][0], self.opts['sun_theta'][1])
        phi = np.random.uniform(0, 2*np.pi)
        return [theta, 0, phi]

    def place_sun(self, rotation=None):
        """Delete a previous sun (if exists) and create a new one at specified angle"""
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
        self.sun.data.node_tree.nodes['Emission'].inputs['Strength'].default_value \
            = self.opts['sun_strength']
        self.sun.data.node_tree.nodes['Emission'].inputs['Color'].default_value \
            = self.opts['sun_color']
        self.set_sky() # Set sun direction and random clouds
        return self.sun

    def random_camera(self):
        """Generate a random camera position with the objects in view"""

        # Random focal length (approx median, relative sigma)
        focal_length = np.random.lognormal(np.log(self.opts['camera_lens']['mean']),
                                           self.opts['camera_lens']['log_sigma'])
        self.camera.data.lens = focal_length

        # Spherical coordinates of the camera position
        min_distance = self.sphere.radius / np.tan(self.camera.data.angle_y/2) # Height < width
        while True:
            distance = min_distance * np.random.normal(self.opts['camera_distance_factor']['mean'],
                                                       self.opts['camera_distance_factor']['sigma'])
            theta = np.random.uniform(self.opts['camera_theta'][0], self.opts['camera_theta'][1])
            phi = np.random.uniform(0, 2*np.pi)
            # Location axes rotated due to default camera orientation
            location = self.sphere.centre + distance * np.array(
                [np.sin(theta)*np.sin(-phi), np.sin(theta)*np.cos(phi), np.cos(theta)])
            # Check if above landscape
            closest_vertex = self.landscape_tree.find(location)
            if location[2] > closest_vertex[2]:
                break

        rotation = np.array([theta, 0, np.pi + phi])
        rotation += np.random.randn(3) * self.opts['camera_noise']
        return focal_length, location.tolist(), rotation.tolist()

    def place_camera(self, focal_length=None, location=None, rotation=None):
        """Place the camera at specified location and rotation"""
        if focal_length is None:
            focal_length, location, rotation = self.random_camera()

        # Position and face centre
        self.camera.data.lens = focal_length
        self.camera.location = np.zeros(3)
        self.camera.rotation_euler[:] = rotation
        self.camera.location = location
        return self.camera

    def render(self, path: str):
        """Render the visual scene"""
        # Render with Cycles engine
        bpy.data.scenes[0].render.engine = 'CYCLES'
        bpy.data.scenes[0].cycles.film_exposure = self.opts['film_exposure']
        bpy.data.scenes[0].cycles.samples = self.opts['cycles_samples']
        bpy.data.scenes[0].render.filepath = path
        bpy.ops.render.render(write_still=True)

    def render_semantic(self, path: str):
        """Render the semantic labels"""
        # Render with Blender engine and no anti-aliasing
        bpy.data.scenes[0].render.engine = 'BLENDER_RENDER'
        bpy.data.scenes[0].render.use_antialiasing = False
        bpy.data.scenes[0].world.horizon_color = (0, 0, 0)
        bpy.data.scenes[0].render.filepath = path
        bpy.ops.render.render(write_still=True)
        # Switch back to Cycles to have correct properties (for visual renders)
        bpy.data.scenes[0].render.engine = 'CYCLES'

    def render_depth(self, path: str):
        """Render depth"""
        # Use Compositing nodes for Scene
        bpy.data.scenes[0].use_nodes = True
        tree = bpy.data.scenes[0].node_tree

        # Configure File Output node
        if tree.nodes.get('File Output') is None:
            file_output = tree.nodes.new('CompositorNodeOutputFile')
        else:
            file_output = tree.nodes['File Output']
        file_output.format.file_format = 'OPEN_EXR'
        file_output.base_path = os.path.dirname(path)

        # Generate random collisionless filename
        sha = hashlib.sha1()
        sha.update(np.array(self.camera.location)) # Different for every image
        digest = sha.hexdigest()
        file_output.file_slots[0].path = digest + '_'

        # Connect depth rendering to outputs
        tree.links.clear()
        tree.links.new(tree.nodes['Render Layers'].outputs['Z'],
                       tree.nodes['Composite'].inputs['Image'])
        tree.links.new(tree.nodes['Render Layers'].outputs['Z'],
                       file_output.inputs[0])

        # Write the render and rename
        bpy.ops.render.render(write_still=True)
        os.rename(glob.glob(os.path.join(os.path.dirname(path), digest + '*'))[0], path)

    def set_sky(self):
        """Set sun direction consistent with the rotation of sun and randomise clouds"""
        # Initialise node tree
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
            ramp.elements[0].position = np.random.uniform(sky['cloud_ramp']['min'],
                                                          sky['cloud_ramp']['max'])
            ramp.elements[1].position = ramp.elements[0].position + sky['cloud_ramp']['diff']
        if 'translate' in sky:
            tree.nodes['Mapping'].translation[0] = np.random.uniform(sky['translate'][0],
                                                                     sky['translate'][1])

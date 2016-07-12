"""Provides methods for rendering the labelled model"""
import os
import json
import numpy as np
import bpy # pylint: disable=import-error
from mathutils import Vector # pylint: disable=import-error

# TODO: Remove ground plane function, belongs with terrain
def add_ground_plane():
    """Add a large ground plane"""
    bpy.ops.mesh.primitive_plane_add(location=(0, 0, 0), radius=1000)
    return bpy.context.object

def new_camera(resolution):
    """Add a camera to the scene and set the resolution for rendering"""
    bpy.ops.object.camera_add()
    camera = bpy.context.object
    bpy.data.scenes[0].camera = camera
    bpy.data.scenes[0].render.resolution_x = resolution[0]
    bpy.data.scenes[0].render.resolution_y = resolution[1]
    bpy.data.scenes[0].render.resolution_percentage = 100
    camera.data.clip_end = 2000 # Maybe set dynamically if ground plane larger
    return camera

class BoundingSphere():
    """Return a sphere surrounding the objects"""

    def __init__(self, objects, centre=None):
        def minmax(index, axis):
            """Choose min or max depending on axis at bounding box corner index"""
            is_max = (index >> axis) % 2 # Control bit in index corresponding to axis
            if axis == 0:
                is_max ^= (index >> 1) % 2 # Cyclic index: 0 -> 00, 1 -> 01, 2 -> 11, 3 -> 10
            return max if is_max else min

        # For every corner i of bounding box, for axis j, choose min/max of all objects along axis
        box = np.array([[minmax(i, j)([(x.matrix_world * Vector(x.bound_box[i]))[j]
                                       for x in objects]) for j in range(3)] for i in range(8)])
        self.centre = np.sum(box, axis=0)/8 if centre is None else centre
        self.radius = np.max(np.linalg.norm(box - self.centre, axis=1))

class Render():
    """Configure and render the scene"""

    def __init__(self, objects, conf_file=None):
        self.objects = objects
        self.sphere = BoundingSphere(self.objects)
        self.sun = None
        self.camera = None

        if conf_file is None:
            self._default()
        else:
            with open(conf_file) as file:
                self.opts = json.load(file)

    def _default(self):
        self.opts = {}
        self.opts['sun_theta'] = [0, 17/18 * np.pi/2] # Not lower than 5 deg from horizon
        self.opts['sun_size'] = 0.02 # Realistic sun is smaller than the default value
        self.opts['sun_strength'] = 2
        self.opts['camera_distance_factor'] = [6/12, 1/12] # [mu, sigma] = factor * min_distance
        self.opts['camera_theta'] = [np.pi/6, np.pi/2] # Maybe restrict further. Allow views from below?
        self.opts['camera_noise'] = 0.01 # Random rotation sigma [x, y, z] or float
        self.opts['resolution'] = [512, 512] # [x, y] pixels
        self.opts['cycles_samples'] = 64 # Increase to reduce noise

    def write_conf(self, conf_file):
        """Write current configuration to conf_file"""
        with open(conf_file, 'w') as file:
            json.dump(self.opts, file)

    def randomise_sun(self):
        """Delete a previous sun (if exists) and create a new one at a random angle"""
        bpy.ops.object.select_all(action='DESELECT')
        if self.sun is not None:
            self.sun.select = True
            bpy.ops.object.delete()

        theta = np.random.uniform(self.opts['sun_theta'][0], self.opts['sun_theta'][1])
        bpy.ops.object.lamp_add(type='SUN', location=(0, 0, 20),
                                rotation=(theta, 0, np.random.uniform(0, 2*np.pi)))
        self.sun = bpy.context.object

        # Set size and strength
        self.sun.data.shadow_soft_size = self.opts['sun_size']
        self.sun.data.node_tree.nodes['Emission'].inputs['Strength'].default_value \
            = self.opts['sun_strength']
        return self.sun

    def randomise_camera(self):
        """Randomise the camera position with the objects in view"""
        if self.camera is None:
            self.camera = new_camera(self.opts['resolution'])

        # Position and face centre
        min_distance = self.sphere.radius / np.tan(self.camera.data.angle_y/2) # Height < width
        distance = np.random.normal(min_distance * self.opts['camera_distance_factor'][0],
                                    min_distance * self.opts['camera_distance_factor'][1])
        theta = np.random.uniform(self.opts['camera_theta'][0], self.opts['camera_theta'][1])
        phi = np.random.uniform(0, 2*np.pi)

        # Location axes rotated due to default camera position
        location = self.sphere.centre + distance * np.array(
            [np.sin(theta)*np.sin(-phi), np.sin(theta)*np.cos(phi), np.cos(theta)])
        rotation = np.array([theta, 0, np.pi + phi])
        rotation += np.random.randn(3) * self.opts['camera_noise']

        self.camera.location = np.zeros(3)
        self.camera.rotation_euler[:] = rotation
        self.camera.location = location
        return self.camera

    def render(self, path, seq=0):
        """Render the scene; should have seq < 999 to avoid non-canonical naming"""
        if not os.path.exists(path):
            os.makedirs(path)

        # Render with Cycles engine
        bpy.data.scenes[0]render.engine = 'CYCLES'
#        bpy.data.scenes[0].display_settings.display_device = 'None' # Avoid gamma correction
        bpy.data.scenes[0].cycles.samples = self.opts['cycles_samples']
        bpy.data.scenes[0].render.filepath = os.path.join(path, "{:03d}.vis.png".format(seq))
        bpy.ops.render.render(write_still=True)

    def render_semantic(self, level, path, seq=0):
        """Render the semantic labels; should have seq < 999 to avoid non-canonical naming"""
        if not os.path.exists(path):
            os.makedirs(path)

        # Render with Blender engine and no anti-aliasing
        bpy.data.scenes[0]render.engine = 'BLENDER_RENDER'
        bpy.data.scenes[0].render.use_antialiasing = False
        bpy.data.scenes[0].display_settings.display_device = 'None' # Avoid gamma correction
        bpy.data.scenes[0].render.filepath = os.path.join(
            path, "{:03d}.sem.{:d}.png".format(seq, level))
        bpy.ops.render.render(write_still=True)

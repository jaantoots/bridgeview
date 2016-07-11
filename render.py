"""Provides methods for rendering the labelled model"""
import os
import numpy as np
import bpy # pylint: disable=import-error
from mathutils import Vector # pylint: disable=import-error

def add_ground_plane():
    """Add a large ground plane"""
    bpy.ops.mesh.primitive_plane_add(radius=1000)
    return bpy.context.object

def randomise_sun(sun=None):
    """Delete a previous sun (if given) and create a new one at a random angle"""
    bpy.ops.object.select_all(action='DESELECT')
    if sun is not None:
        sun.select = True
        bpy.ops.object.delete()

    theta = np.random.uniform(0, 17/18 * np.pi/2) # Not lower than 5 deg from horizon
    bpy.ops.object.lamp_add(type='SUN', location=(0, 0, 20),
                            rotation=(theta, 0, np.random.uniform(0, 2*np.pi)))
    sun = bpy.context.object

    # TODO: check results and modify sun size
    sun.data.shadow_soft_size = 0.01 # Realistic sun is smaller than the defaul
    return sun

def new_camera():
    """Add a camera to the scene"""
    bpy.ops.object.camera_add()
    camera = bpy.context.object
    bpy.data.scenes[0].camera = camera
    return camera

def randomise_camera(objects, camera=None):
    """Randomise the camera position with the objects in view"""
    camera = new_camera() if camera is None else camera

    # Position and face centre
    sphere = BoundingSphere(objects)
    min_distance = sphere.radius / np.tan(camera.angle_y/2) # Height smaller than width
    distance = np.random.normal(min_distance * 5/3, min_distance/2) # Arbitrary parameters here
    theta = np.random.uniform(np.pi/6, np.pi/2) # Maybe need to limit this further
    phi = np.random.uniform(0, 2*np.pi)

    # Location axes rotated due to default camera position
    location = sphere.centre + distance * np.array(
        [np.sin(theta)*np.sin(-phi), np.sin(theta)*np.cos(phi), np.cos(theta)])
    rotation = np.array([theta, 0, phi])
    rotation += np.random.randn(3) * 0.1 # Arbitrary parameter

    camera.location = location
    camera.rotation_euler[:] = rotation

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
        self.radius = np.max(np.linalg.norm(box - centre, axis=1))

def render(path, seq=0):
    """Render the scene"""
    if not os.path.exists(path):
        os.makedirs(path)
    bpy.data.scenes[0].render.filepath = os.path.join(path, "{:03d}.png".format(seq)) # limit 999

    bpy.ops.render.render()

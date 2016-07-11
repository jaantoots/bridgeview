"""Provides methods for rendering the labelled model"""
import numpy as np
import bpy # pylint: disable=import-error

def add_ground_plane():
    """Add a large ground plane"""
    bpy.ops.mesh.primitive_plane_add(radius=1000)
    return bpy.context.object

def randomize_sun(sun=None):
    """Delete a previous sun (if given) and create a new one at a random angle"""
    bpy.ops.object.select_all(action='DESELECT')
    if sun is not None:
        sun.select = True
        bpy.ops.object.delete()

    polar = np.random.uniform(0, 17/18 * np.pi/2) # Not lower than 5 deg from horizon
    bpy.ops.object.lamp_add(type='SUN', location=(0, 0, 20),
                            rotation=(0, polar, np.random.uniform(0, 2*np.pi)))
    sun = bpy.context.object

    # TODO: check results and modify sun size
    sun.data.shadow_soft_size = 0.01 # Realistic sun is smaller than the defaul
    return sun

def add_camera(camera=None):
    """Add a camera to the scene"""
    bpy.ops.object.camera_add()
    camera = bpy.context.object
    bpy.data.scenes[0].camera = camera
    return camera

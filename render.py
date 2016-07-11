"""Provides methods for rendering the labelled model"""
import numpy as np
import bpy # pylint: disable=import-error

def add_ground_plane():
    """Add a large ground plane"""
    bpy.ops.mesh.primitive_plane_add(radius=1000)
    return bpy.context.object

def randomize_sun(sun=None):
    """Deletes a previous sun (if given) and creates a new one at a random angle"""
    bpy.ops.object.select_all(action='DESELECT')
    if sun is not None:
        sun.select = True
        bpy.ops.object.delete()

    polar = np.random.uniform(0, 17/18 * np.pi/2) # Not lower than 5 deg from horizon
    bpy.ops.object.lamp_add(type='SUN', location=(0, 0, 20),
                            rotation=(0, polar, np.random.uniform(0, 2*np.pi)))
    return bpy.context.object

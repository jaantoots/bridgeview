"""Modify bridge structure according to user-defined groups"""
import numpy as np
import bpy # pylint: disable=import-error
import bridge.helpers

def translate_group(group, translate):
    """Translate all objects in group list by translate"""
    bpy.ops.object.select_all(action='DESELECT')
    for name in group:
        bpy.data.objects[name].select = True
    bpy.ops.transform.translate(value=translate)

class Scale():
    """Scaling operations"""

    def __init__(self, groups: dict):
        self.groups = groups

    def scale(self, value, axis_index, reference):
        """Scale the defined group by value along axis and translate other groups accordingly"""
        # Set axis
        axis = np.zeros(3, dtype=bool)
        axis[axis_index] = True

        # Resize the scale group and get translation values
        start_box = bridge.helpers.bounding_box(reference)

        bpy.ops.object.select_all(action='DESELECT')
        for name in self.groups['scale']:
            bpy.data.scenes[0].objects.active = bpy.data.objects[name]
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.transform.resize(value=(axis*(value - 1) + np.ones(3)))
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.data.scenes[0].objects.active = None

        end_box = bridge.helpers.bounding_box(reference)
        translate = end_box - start_box

        # Translate the min and max groups
        translate_group(self.groups['min'], translate[0] * axis)
        translate_group(self.groups['max'], translate[1] * axis)
        bpy.ops.object.select_all(action='DESELECT')

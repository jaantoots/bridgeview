"""Modify bridge structure according to user-defined groups."""
import json
import numpy as np
import bpy # pylint: disable=import-error
import bridge.helpers as helpers

def translate_group(group, translate):
    """Translate all objects in group list by translate."""
    bpy.ops.object.select_all(action='DESELECT')
    for name in group:
        bpy.data.objects[name].select = True
    bpy.ops.transform.translate(value=translate)

def scale_object(obj, value: float, axis):
    """Scale an object by value along axis."""
    bpy.ops.object.select_all(action='DESELECT')
    bpy.data.scenes[0].objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.transform.resize(value=(axis*(value - 1) + np.ones(3)))
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.data.scenes[0].objects.active = None

class Scale():
    """Scaling operations."""

    def __init__(self, groups: dict=None):
        """Scaling class with groups scale, min, max defined in groups."""
        self.groups = groups

    def load_groups(self, filename: str, name: str):
        """Load groups definition from file by name."""
        with open(filename) as file:
            data = json.load(file)
            self.groups = data[name]

    def write_groups(self, filename: str, name: str, overwrite=True):
        """Write groups definition to file, update an existing definition if overwrite is True."""
        with open(filename) as file:
            data = json.load(file)
        with open(filename, 'w') as file:
            if name not in data or overwrite:
                data[name] = self.groups
                json.dump(data, file)
            else:
                raise ValueError("Name already exists, specify overwrite to write anyway")

    def scale(self, value: float, axis_index: int, reference: str):
        """Scale the defined group by value along axis and translate other groups accordingly."""
        assert self.groups is not None, "Groups not defined."
        # Set axis
        axis = np.zeros(3, dtype=bool)
        axis[axis_index] = True

        # Scale the reference object
        start_ref = helpers.bounding_box(bpy.data.objects[reference])
        scale_object(bpy.data.objects[reference], value, axis)
        end_ref = helpers.bounding_box(bpy.data.objects[reference])

        # Resize scale group using offsets as end structures should be translated without scaling
        for name in self.groups['scale']:
            if name == reference:
                continue
            start_box = helpers.bounding_box(bpy.data.objects[name])
            start_length = start_box[1] - start_box[0]
            end_box = start_box - start_ref + end_ref
            end_length = end_box[1] - end_box[0]
            scale_object(bpy.data.objects[name], end_length/start_length, axis)

        # Translate the min and max groups
        translate = end_ref - start_ref
        translate_group(self.groups['min'], translate[0] * axis)
        translate_group(self.groups['max'], translate[1] * axis)
        bpy.ops.object.select_all(action='DESELECT')

"""Provides methods for labelling the model correctly for rendering"""
import bpy

class _LabelDict(dict):
    def __missing__(self, key):
        return []

class Labels():
    """Label all parts"""

    def __init__(self):
        self.labels = _LabelDict()

    def _read(self, label_file):
        with open(label_file) as file:
            pass

    def add_label(self, label, color):
        self.labels[label] +=  color

def objects_with(color):
    """Return all objects with a specified color"""

    # Materials with a given diffuse_color
    materials = [material for material in bpy.data.materials if material.diffuse_color == color]

    return [obj for obj in bpy.data.objects if obj.material_slots[0].material in materials]

def rename_instances(instances, name):
    """Rename all instances of a part sequentially"""
    for i, obj in enumerate(instances):
        obj.name = "{:s}.{:03d}".format(name, i)
        if i > 999:
            print("Warning: labels: rename_instances:"\
                  "{:s} non-canonical name (> 999)".format(obj.name))


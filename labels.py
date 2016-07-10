"""Provides methods for labelling the model before rendering"""
import bpy # pylint: disable=import-error

class _LabelDict(dict):
    """Overload the missing method of builtin dict for brevity"""
    def __missing__(self, key):
        return []

# At some point have to do this to get rid of gamma correction:
# bpy.data.scenes[0].display_settings.display_device = 'None'

class Parts():
    """Class for identifying and labelling parts

    Parts are identified by original color and then given semantic,
    geometric and instance labels.

    """

    def __init__(self):
        self.colors = _LabelDict()
        self.parts = _LabelDict()

    def _read(self, label_file):
        with open(label_file) as file:
            pass

    def add_label(self, label, color):
        """Identify original color as part label"""
        self.colors[label] += color
        self.parts[label] += objects_with(color)

def objects_with(color):
    """Return all objects with a material of specified diffuse_color"""
    materials = [material for material in bpy.data.materials if material.diffuse_color == color]
    return [obj for obj in bpy.data.objects if obj.material_slots[0].material in materials]

def rename_instances(instances, name): # Should be merged with coloring (for clarity)
    """Rename all instances of a part sequentially"""
    for i, obj in enumerate(instances):
        obj.name = "{:s}.{:03d}".format(name, i)
        if i > 999: # Perhaps another limit depending on the labelling scheme
            print("Warning: labels: rename_instances:"\
                  "{:s} non-canonical name (> 999)".format(obj.name))

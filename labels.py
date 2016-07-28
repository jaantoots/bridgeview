"""Provides methods for labelling the model before rendering."""
import json
import randomcolor
import bpy # pylint: disable=import-error
from . import helpers

class Labels():
    """Identify parts by name and assign semantic labels as colors."""

    def __init__(self, objects: list):
        """Create Labels for given list of Blender objects."""
        self.objects = objects[:]
        self.levels = []
        self.levels += [dict()] # 0: feature -> color
        self.levels += [dict()] # 1: structure -> color
        self.levels += [dict()] # 2: part -> color
        self.parts = helpers.Dict() # structure -> parts

    def read(self, label_file: str):
        """Read labelling from file."""
        with open(label_file) as file:
            data = json.load(file)
            self.levels = data['levels']
            self.parts = helpers.Dict(data['parts'])

    def write(self, label_file: str):
        """Write labelling to file."""
        with open(label_file, 'w') as file:
            data = {'levels': self.levels, 'parts': self.parts}
            json.dump(data, file)

    def def_structure(self, structure: str, parts: list):
        """Define parts in a structure and color the structure and parts.

        Assign parts to be members of a structure. Every structure is
        assigned a hue; the level 1 structure is assigned a color and
        all level 2 parts are assigned a color, all in the same hue
        for clarity. Should have # of structures <= 7 to avoid reusing
        hues.

        """
        index = len(self.parts) # Number of structures defined previously
        rand_color = randomcolor.RandomColor()
        hues = ['red', 'green', 'blue', 'purple', 'yellow', 'orange', 'pink']
        if index >= len(hues):
            index %= len(hues)
            print("labels: WARNING: reusing hue '{:s}'".format(hues[index]))

        self.parts[structure] += parts
        self.levels[1][structure] = rand_color.generate(hue=hues[index], luminosity='bright')[0]
        for part, color in zip(parts, rand_color.generate(
                hue=hues[index], count=len(parts), luminosity='bright')):
            self.levels[2][part] = color

    def structure_from_dict(self, parts_dict: dict):
        """Define all structures in parts_dict.

        Convenience method for defining parts in structures and having them colored

        """
        for structure, parts in parts_dict.items():
            self.def_structure(structure, parts)

    def def_features(self, features: list):
        """Define all non-bridge features.

        Features that are not part of the bridge have the same label
        on level 0 and level 1. All colors are available on level 0,
        while non-bridge features are constrained to monochrome color
        labels on level 1.

        """
        rand_color = randomcolor.RandomColor()
        self.levels[0] = {feature: rand_color.generate(luminosity='bright')[0]
                          for feature in features}
        self.levels[0]['bridge'] = '#ffffff' # Bridge is white on level 0

        # Monochrome colors for non-bridge structures on level 1
        for feature, color in zip(features, rand_color.generate(
                hue='monochrome', count=len(features), luminosity='bright')):
            self.levels[1][feature] = color

    def color_level(self, level: int):
        """Color all objects according to level.

        Apply the colors corresponding to `level`. Using too many
        if-branches adding an annoying amount of cyclomatic
        complexity.

        """
        # Switch off color management
        bpy.context.scene.display_settings.display_device = 'None'
        bpy.context.scene.sequencer_colorspace_settings.name = 'Raw'

        # Start with all objects black
        self._color_parts(None, '#000000')
        # Level 2: parts
        if level == 2:
            for part, color in self.levels[2].items():
                self._color_parts(part, color)
        # Level 1: structures
        elif level == 1:
            for structure, color in self.levels[1].items():
                # If in self.parts, object names start with labels on level 2
                if structure in self.parts:
                    for part in self.parts[structure]:
                        self._color_parts(part, color)
                # Non-bridge structures/features are directly named
                else:
                    self._color_parts(structure, color)
        # Level 0: features
        elif level == 0:
            for feature, color in self.levels[0].items():
                # Non-bridge features/structures are directly named
                if feature != 'bridge':
                    self._color_parts(feature, color)
                # Bridge object names start with labels on level 2
                else:
                    for part in [part for structure in self.parts
                                 for part in self.parts[structure]]:
                        self._color_parts(part, self.levels[0]['bridge'])

    def _color_parts(self, part: str, color: str):
        """Color all instances of a part, or all objects if part is ''."""
        instances = helpers.all_instances(part, self.objects)
        for obj in instances:
            color_object(obj, color)

def color_object(obj, color: str):
    """Color an object with color.

    Find or create a material with the specified color and make this
    the active material of the object

    """
    material_name = "shadeless.{:s}".format(color)

    # Create a shadeless diffuse material with the right color if it does not exist
    if material_name in [material.name for material in bpy.data.materials]:
        material = bpy.data.materials[material_name]
    else:
        material = bpy.data.materials.new(material_name)
        material.use_shadeless = True
        material.diffuse_color = hex_to_rgb(color)

    # Assign the material to object
    for _ in range(len(obj.material_slots)):
        bpy.ops.object.material_slot_remove({'object': obj})
    obj.data.materials.clear()
    obj.active_material = material

def hex_to_rgb(color: str):
    """Convert a hex color code into rgb 3-tuple."""
    rgb = int(color[1:], 16)
    r = ((rgb >> 16) & 255)/255 # pylint: disable=invalid-name
    g = ((rgb >> 8) & 255)/255 # pylint: disable=invalid-name
    b = ((rgb >> 0) & 255)/255 # pylint: disable=invalid-name
    return r, g, b

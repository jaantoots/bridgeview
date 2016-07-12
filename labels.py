"""Provides methods for labelling the model before rendering"""
import json
import randomcolor
import bpy # pylint: disable=import-error

class _LabelDict(dict):
    """Overload the missing method of builtin dict for brevity"""
    def __missing__(self, key):
        return []

# At some point have to get rid of gamma correction:
# bpy.data.scenes[0].display_settings.display_device = 'None'

class Parts():
    """Class for identifying and labelling parts

    Parts are identified by name and then given semantic labels.

    """

    def __init__(self, bridge):
        self.bridge = bridge
        self.levels = []
        self.levels += [dict()] # 0: feature -> color
        self.levels += [dict()] # 1: structure -> color
        self.levels += [dict()] # 2: part -> color
        self.parts = _LabelDict() # structure -> parts

    def read(self, label_file):
        """Read labelling from file"""
        with open(label_file) as file:
            data = json.load(file)
            self.levels = data['levels']
            self.parts = _LabelDict(data['parts'])

    def write(self, label_file):
        """Write labelling to file"""
        with open(label_file, 'w') as file:
            data = {'levels': self.levels, 'parts': self.parts}
            json.dump(data, file)

    def def_structure(self, structure, parts):
        """Define parts in a structure and color the structure and parts"""
        index = len(self.parts) # Number of structures defined previously
        rand_color = randomcolor.RandomColor()
        hues = ['blue', 'red', 'purple', 'yellow', 'orange', 'green', 'pink']
        if index >= len(hues):
            index %= len(hues)
            print("labels: WARNING: reusing hue '{:s}'".format(hues[index]))

        self.parts[structure] += parts
        self.levels[1][structure] = rand_color.generate(hue=hues[index])[0]
        for part, color in zip(parts, rand_color.generate(hue=hues[index], count=len(parts))):
            self.levels[2][part] = color

    def def_features(self, features):
        """Define non-bridge features"""
        rand_color = randomcolor.RandomColor()
        self.levels[0] = {feature: rand_color.generate()[0] for feature in features}
        self.levels[0]['bridge'] = '#ffffff' # Bridge is white on level 0

        # Monochrome colors for non-bridge structures on level 1
        for feature, color in zip(features, generate(hue='monochrome', count=len(features))):
            self.levels[1][feature] = color

    def color_level(self, level):
        """Color all objects according to level"""
        # Start with all objects black
        _color_parts('', '#000000')
        # Level 2: parts
        if level == 2:
            for part, color in self.levels[2].items():
                _color_parts(part, color)
        # Level 1: structures
        elif level == 1:
            for structure, color in self.levels[1].items():
                # If in self.parts, object names start with labels on level 2
                if structure in self.parts:
                    for part in self.parts[structure]:
                        _color_parts(part, color)
                # Non-bridge structures/features are directly named
                else:
                    _color_parts(structure, color)
        # Level 0: features
        elif level == 0:
            for feature, color in self.levels[0].items():
                # Non-bridge features/structures are directly named
                if feature != 'bridge':
                    _color_parts(feature, color)
                # Bridge object names start with labels on level 2
                else:
                    for part in self.levels[2]:
                        _color_parts(part, self.levels[0]['bridge'])

def _color_parts(part, color):
    """Color all instances of a part, or all objects if part is ''"""
    instances = [obj for obj in bpy.data.objects if obj.name.startswith(part)]
    for obj in instances:
        _color_object(obj, color)

def _color_object(obj, color):
    """Color an object with color"""
    material_name = "{:s}.{:s}".format(obj.name, color)

    # Create a shadeless diffuse material with the right color if it does not exist
    if material_name in [material.name for material in bpy.data.materials]:
        material = bpy.data.materials[material_name]
    else:
        material = bpy.data.materials.new(material_name)
        material.use_shadeless = True
        material.diffuse_color = hex_to_rgb(color)

def hex_to_rgb(color):
    """Convert a hex color code into rgb 3-tuple"""
    rgb = int(color[1:], 16)
    r = ((rgb >> 16) & 255)/255
    g = ((rgb >> 8) & 255)/255
    b = ((rgb >> 0) & 255)/255
    return r, g, b

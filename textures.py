"""Provides methods for texturing the scene for rendering"""
import json
import numpy as np
import bpy # pylint: disable=import-error
from . import helpers

class Textures():
    """Identify parts by name, organise into texturing groups and texture

    Initialise with list of objects to be textured.

    Run: read groups and textures from JSON file & call `texture` to
    assign (random) textures to objects

    Test or setup: group parts to always have the same texture, add
    available textures to groups (or ungrouped parts) & write groups
    and textures to JSON file

    """

    def __init__(self, objects: list):
        self.objects = objects
        self.textures = helpers.Dict()
        self.groups = helpers.Dict()

    def read(self, texture_file: str):
        """Read texturing from file"""
        with open(texture_file) as file:
            data = json.load(file)
            self.textures = helpers.Dict(data['textures'])
            self.groups = helpers.Dict(data['groups'])

    def write(self, texture_file: str):
        """Write texturing to file"""
        with open(texture_file, 'w') as file:
            data = {'textures': self.textures, 'groups': self.groups}
            json.dump(data, file)

    def smart_project_all(self):
        """Initialize objects for texturing using UV smart project (for testing only)

        Usually need to prepare the model by choosing the best
        projection for each part manually. Cube projection seems to
        work well most of the time.

        """
        for obj in self.objects:
            bpy.data.scenes[0].objects.active = obj
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.uv.smart_project()
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.data.scenes[0].objects.active = None

    def add_textures(self, group: str, textures: list):
        """Add available textures to group (or part if no group)

        It is possible to add multiple textures per group to have one
        chosen randomly when textures are applied to objects.

        """
        self.textures[group] += textures

    def add_parts_to_group(self, group: str, parts: list):
        """Assign parts to belong in a group that gets textured with the same material"""
        self.groups[group] += parts

    def texture(self):
        """Texture all objects (assumes all parts have been UV projected)"""
        for group, textures in self.textures.items():
            texture = np.random.choice(textures)
            if group in self.groups:
                for part in self.groups[group]:
                    self._texture_parts(part, texture)
            else:
                self._texture_parts(group, texture)

    def _texture_parts(self, part: str, texture: str):
        """Texture all instances of a part, or all objects if part is ''"""
        instances = helpers.all_instances(part, self.objects)
        for obj in instances:
            texture_object(obj, texture)

def texture_object(obj, texture: str):
    """Texture an object with texture

    Find a material with the name `texture` and make this the active
    material of the object

    """
    material = bpy.data.materials[texture]
    # Assign the material to object
    for _ in range(len(obj.material_slots)):
        bpy.ops.object.material_slot_remove({'object': obj})
    obj.data.materials.clear()
    obj.active_material = material

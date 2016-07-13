"""Provides methods for texturing the scene for rendering"""
import json
import numpy as np
import bpy # pylint: disable=import-error
from . import helpers

class Textures():
    """Textures"""

    def __init__(self, objects: list):
        self.objects = objects
        self.textures = helpers.Dict()
        self.parts = helpers.Dict()

    def add_textures(self, group: str, textures: list):
        """Add textures to group (or part if no group)"""
        self.textures[group] += textures

    def add_parts_to_group(self, group: str, parts: list):
        """Assign parts to belong in a group that gets textured with the same material"""
        self.parts[group] += parts

    def texture(self):
        """Texture all objects (assumes all parts have been UV smart projected)"""
        for group, textures in self.textures.items():
            texture = np.random.choice(textures)
            def texture_func(obj, tex=texture):
                texture_object(obj, tex)
            if group in self.parts:
                for part in self.parts[group]:
                    helpers.apply_to_instances(texture_func, part, self.objects)
            else:
                helpers.apply_to_instances(texture_func, group, self.objects)

def texture_object(obj, texture: str):
    """Texture an object with texture"""
    pass

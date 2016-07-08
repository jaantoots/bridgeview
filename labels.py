"""Provides methods for labelling the model correctly for rendering"""
import bpy

def objects_with(color):
    """Returns all objects with a specified color"""

    # Materials with a given diffuse_color
    materials = [material for material in bpy.data.materials if material.diffuse_color == color]

    return [obj for obj in bpy.data.objects if obj.material_slots[0].material in materials]


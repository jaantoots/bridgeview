"""Provides methods for labelling the model correctly for rendering"""
import bpy

def materials_with(color):
    """Returns all materials with a given diffuse_color"""
    return [material for material in bpy.data.materials if material.diffuse_color == color]

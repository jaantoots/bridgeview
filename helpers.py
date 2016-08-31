"""Objects used by multiple modules."""
import json
import numpy as np
import bpy  # pylint: disable=import-error
import mathutils  # pylint: disable=import-error


class Dict(dict):
    """Overload the missing method of builtin dict for brevity."""

    def __missing__(self, key):
        """Return an empty list if missing element: append to dict[key]."""
        return []


def all_instances(part: str, objects):
    """Return all objects with a given name or all if part is None."""
    if part is None:
        return objects
    else:
        return [obj for obj in objects if part in obj.name.split('.')]


def landscape_tree(landscape):
    """Return a balanced tree of landscape vertices for find operations."""
    tree = mathutils.kdtree.KDTree(len(landscape.data.vertices))
    for i, vertex in enumerate(landscape.data.vertices):
        tree.insert(landscape.matrix_world * vertex.co, i)
    tree.balance()
    return tree


def avoid_tree(objects):
    """Return a balanced tree of vertices for find operations."""
    vertices = [(obj, vert) for obj in objects for vert in obj.data.vertices]
    tree = mathutils.kdtree.KDTree(len(vertices))
    for i, vertex in enumerate(vertices):
        tree.insert(vertex[0].matrix_world * vertex[1].co, i)
    tree.balance()
    return tree


def bounding_box(obj):
    """Return a bounding box for an object aligned with the global axes."""
    vertices = [obj.matrix_world * vertex.co for vertex in obj.data.vertices]
    box = np.zeros((2, 3))
    box[0] = np.min(vertices, axis=0)
    box[1] = np.max(vertices, axis=0)
    return box


class BoundingSphere():
    """Sphere surrounding the objects.

    Specify a bounding sphere manually or find it based on the objects.

    """

    def __init__(self, centre=None, radius=None):
        """Initialise a bounding sphere with centre and radius (if given)."""
        self.centre = centre
        self.radius = radius
        self.vis = None

    def visualise(self, centre=None, radius=None):
        """Visualise the bounding sphere by creating a sphere in the scene."""
        if centre is not None:
            self.centre = centre
        if radius is not None:
            self.radius = radius
        if self.centre is None or self.radius is None:
            raise ValueError("Centre and radius must be defined")
        # Delete previous sphere (if exists) and create new
        bpy.ops.object.select_all(action='DESELECT')
        if self.vis is not None:
            self.vis.select = True
            bpy.ops.object.delete()
        bpy.ops.mesh.primitive_ico_sphere_add(
            subdivisions=4, size=self.radius, location=self.centre)
        self.vis = bpy.context.object
        # Print info for adding to conf files
        print(json.dumps({"centre": self.centre, "radius": self.radius}))
        return self.vis

    def clean(self):
        """Remove the visualisation sphere from the scene."""
        bpy.ops.object.select_all(action='DESELECT')
        if self.vis is not None:
            self.vis.select = True
            bpy.ops.object.delete()
            self.vis = None

    def find(self, objects: list, centre=None):
        """Return a bounding sphere for objects with optional centre."""
        # TODO: Spheres are too large and bounding box is not always correct.
        def minmax(index, axis):
            """Choose min or max depending on axis at box corner index."""
            is_max = (index >> axis) % 2  # Control bit in index for axis
            if axis == 0:
                # Cyclic index: 0 -> 00, 1 -> 01, 2 -> 11, 3 -> 10
                is_max ^= (index >> 1) % 2
            return max if is_max else min

        # For corner i of box, for axis j, choose min/max of objects along axis
        box = np.array([
            [minmax(i, j)(
                [(x.matrix_world * mathutils.Vector(x.bound_box[i]))[j]
                 for x in objects]
            ) for j in range(3)] for i in range(8)])
        self.centre = np.sum(box, axis=0)/8 if centre is None else centre
        self.radius = np.max(np.linalg.norm(box - self.centre, axis=1))
        return {"centre": self.centre, "radius": self.radius}


class CameraLine():
    """Create camera lines for choosing position."""

    def __init__(self, start=None, end=None):
        """Initialise a line with start and end points (if given)."""
        self.start = start
        self.end = end
        self.name = "CameraLine." + np.random.bytes(4).hex()
        self.vis = None

    def visualise(self, start=None, end=None):
        """Visualise theline  by creating it in the scene."""
        if start is not None:
            self.start = start
        if end is not None:
            self.end = end
        if self.start is None or self.end is None:
            raise ValueError("Start and end must be defined")
        # Delete previous (if exists) and create new
        bpy.ops.object.select_all(action='DESELECT')
        if self.vis is not None:
            self.vis.select = True
            bpy.ops.object.delete()
        bpy.ops.mesh.primitive_mesh_add()
        self.vis = bpy.context.object
        # Print info for adding to conf files
        self.vis.name = self.name
        vert = self.vis.data.vertices
        vert[0].co = self.start
        vert[1].co = self.start + np.array([0, 0, 1])
        vert[2].co = self.end
        vert[3].co = self.end + np.array([0, 0, 1])
        print(json.dumps({"start": self.start, "end": self.end}))
        return self.vis

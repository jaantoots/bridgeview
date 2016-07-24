"""Objects used by multiple modules."""
import numpy as np
import mathutils # pylint: disable=import-error

class Dict(dict):
    """Overload the missing method of builtin dict for brevity."""

    def __missing__(self, key):
        """Return an empty list if missing element: can always append to dict[key]."""
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

def bounding_box(obj):
    """Return a bounding box for a single object aligned with the global axes."""
    vertices = [obj.matrix_world * vertex.co for vertex in obj.data.vertices]
    box = np.zeros((2, 3))
    box[0] = np.min(vertices, axis=0)
    box[1] = np.max(vertices, axis=0)
    return box

# TODO: Test BoundingSphere (returns too large spheres and bounding box is not always correct)
class BoundingSphere():
    """Sphere surrounding the objects.

    Unfortunately this seems to return slightly weird stuff occasionally.

    """

    def __init__(self, objects: list, centre=None):
        """Return a bounding sphere for the objects with optionally specified centre."""
        def minmax(index, axis):
            """Choose min or max depending on axis at bounding box corner index."""
            is_max = (index >> axis) % 2 # Control bit in index corresponding to axis
            if axis == 0:
                is_max ^= (index >> 1) % 2 # Cyclic index: 0 -> 00, 1 -> 01, 2 -> 11, 3 -> 10
            return max if is_max else min

        # For every corner i of bounding box, for axis j, choose min/max of all objects along axis
        box = np.array([[minmax(i, j)([(x.matrix_world * mathutils.Vector(x.bound_box[i]))[j]
                                       for x in objects]) for j in range(3)] for i in range(8)])
        self.centre = np.sum(box, axis=0)/8 if centre is None else centre
        self.radius = np.max(np.linalg.norm(box - self.centre, axis=1))

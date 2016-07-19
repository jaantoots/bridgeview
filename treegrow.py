"""Place trees randomly across scene"""
import numpy as np
import scipy.optimize
import bpy # pylint: disable=import-error
import mathutils # pylint: disable=import-error

class TreeGrow():
    """Grow trees on landscape with a specified group scale and hard clearance"""

    def __init__(self, landscape, other_trees: set, scale: float=8., clearance: float=8.):
        self.landscape = landscape
        self.scale = scale
        self.clearance = clearance
        self.trees = [obj for obj in bpy.data.objects if obj.name.split('.')[0] in other_trees]

        # Create landscape tree for fast closest point lookup
        self.landscape_tree = mathutils.kdtree.KDTree(len(landscape.data.vertices))
        for i, vertex in enumerate(landscape.data.vertices):
            self.landscape_tree.insert(landscape.matrix_world * vertex.co, i)
        self.landscape_tree.balance()

        # Set some default values
        self._dig = [0., 0.000001]
        self._init_height = 15

    def grow_trees(self, number: int, seed_tree: list):
        """Grow N trees using the last element of seed_tree as a starting point"""
        if number == 0:
            return seed_tree
        print("==> Still growing {:d} tree(s)".format(number))
        seed_tree.append(self.grow_tree(seed_tree[-1]))
        return self.grow_trees(number - 1, seed_tree)

    def grow_tree(self, parent_tree):
        """Grow a tree near parent_tree and return it"""
        # Find an empty area for the tree with a preference for close placement
        print("Find location...")
        while True:
            dist = np.random.exponential(self.scale)
            angle = np.random.uniform(0, 2*np.pi)
            translate = np.array([np.cos(angle), np.sin(angle), 0]) * dist
            location = translate + parent_tree.location
            if self._found_clearing(location):
                break

        # Find appropriate z coordinate at x, y position
        print("Optimise height...")
        location[2] = self._find_height(location)
        location[2] -= np.random.normal(self._dig[0], self._dig[1]) # Slightly into the ground
        translate = location - parent_tree.location

        # Duplicate parent tree with translation and add a random rotation
        print("Place tree...")
        bpy.ops.object.select_all(action='DESELECT')
        parent_tree.select = True
        bpy.ops.object.duplicate_move_linked(
            OBJECT_OT_duplicate={"linked": True, "mode": 'TRANSLATION'},
            TRANSFORM_OT_translate={"value": translate})
        bpy.ops.transform.rotate(value=np.random.uniform(0, 2*np.pi), axis=(0, 0, 1))

        # Add tree to list
        tree = bpy.context.selected_objects[0]
        self.trees.append(tree)
        return tree

    def _found_clearing(self, location):
        """Check whether any other trees are too close (beware the quadratic scaling)"""
        for tree in self.trees:
            if np.linalg.norm(location - tree.location) < self.clearance:
                return False
        return True

    def _find_height(self, location):
        """Use scipy.optimize to find ground height"""
        def height(point_z):
            """Return distance to landscape"""
            point = location[:]
            point[2] = point_z
            _, _, dist = self.landscape_tree.find(point)
            return dist
        res = scipy.optimize.minimize(height, self._init_height)
        return res.x

def main():
    """Grow trees in model where a seed tree has already been placed"""
    # TODO: parse command line arguments (seed trees) and run TreeGrow
    pass

if __name__ == "__main__":
    main()
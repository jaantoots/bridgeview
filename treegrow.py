"""Place trees randomly across scene."""
import sys
import argparse
import itertools
import numpy as np
import scipy.optimize
import bpy  # pylint: disable=import-error
import bridge.helpers


class BaseTreeGrow():
    """Grow trees! Base class for the novice landscape architect."""

    def __init__(self, landscape):
        """Create the landscape tree and set some default values."""
        self.landscape = landscape
        # Create landscape tree for fast closest point lookup
        self.landscape_tree = bridge.helpers.landscape_tree(landscape)
        # Set some default values
        self._dig = [0., 0.000001]
        self._init_height = 15

    def _find_height(self, location):
        """Use scipy.optimize to find ground height."""
        def height(point_z):
            """Return distance to landscape."""
            point = location[:]
            point[2] = point_z
            _, _, dist = self.landscape_tree.find(point)
            return dist
        res = scipy.optimize.minimize(height, self._init_height)
        return res.x


class TreeGrow(BaseTreeGrow):
    """Grow trees at specified locations."""

    def __init__(self, landscape, trees: dict):
        """Create trees on `landscape` as specified by `trees`.

        Dictionary `trees` should have existing object names as keys
        and corresponding lists of coordinate values. Already existing
        objects will be moved to specified coordinates and new trees
        will be grown as necessary.

        """
        BaseTreeGrow.__init__(self, landscape)
        self.trees = trees

    def grow_trees(self, key: str):
        """Grow trees with the specified key."""
        locations = self.trees[key]
        previous_trees = [obj for obj in bpy.data.objects
                          if obj.name.split('.')[0] == key]
        self._init_height = previous_trees[0].location[2]
        for location, tree in itertools.zip_longest(locations, previous_trees):
            if location is None:
                break
            if tree is None:
                # Duplicate last tree and add a random rotation
                bpy.ops.object.select_all(action='DESELECT')
                previous_trees[-1].select = True
                bpy.ops.object.duplicate_linked(
                    OBJECT_OT_duplicate={"linked": True})
                bpy.ops.transform.rotate(value=np.random.uniform(0, 2*np.pi),
                                         axis=(0, 0, 1))
                tree = bpy.context.selected_objects[0]
            # Find appropriate z coordinate at x, y position
            location[2] = self._find_height(location)
            # Dig the tree slightly into the ground
            location[2] -= np.random.normal(self._dig[0], self._dig[1])
            tree.location = location

    def grow_all(self):
        """Grow all trees."""
        for key in self.trees:
            self.grow_trees(key)


class TreeGrowRandom(BaseTreeGrow):
    """Grow random trees  with a specified scale and hard clearance."""

    def __init__(self, landscape, other_trees: set,
                 scale: float=8., clearance: float=8.):
        """Create object on landscape with other trees to avoid."""
        BaseTreeGrow.__init__(self, landscape)
        self.scale = scale
        self.clearance = clearance
        self.trees = [obj for obj in bpy.data.objects
                      if obj.name.split('.')[0] in other_trees]

    def grow_trees(self, number: int, seed_tree: list):
        """Grow trees using last element of seed_tree as a starting point."""
        if number == 0:
            return seed_tree
        print("==> Still growing {:d} tree(s)".format(number))
        seed_tree.append(self.grow_tree(seed_tree[-1]))
        return self.grow_trees(number - 1, seed_tree)

    def grow_tree(self, parent_tree):
        """Grow a tree near parent_tree and return it."""
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
        # Dig the tree slightly into the ground
        location[2] -= np.random.normal(self._dig[0], self._dig[1])
        translate = location - parent_tree.location

        # Duplicate parent tree with translation and add a random rotation
        print("Place tree...")
        bpy.ops.object.select_all(action='DESELECT')
        parent_tree.select = True
        bpy.ops.object.duplicate_move_linked(
            OBJECT_OT_duplicate={"linked": True, "mode": 'TRANSLATION'},
            TRANSFORM_OT_translate={"value": translate})
        bpy.ops.transform.rotate(value=np.random.uniform(0, 2*np.pi),
                                 axis=(0, 0, 1))

        # Add tree to list
        tree = bpy.context.selected_objects[0]
        self.trees.append(tree)
        return tree

    def _found_clearing(self, location):
        """Check if any other trees are too close (FU quadratic scaling)."""
        for tree in self.trees:
            if np.linalg.norm(location - tree.location) < self.clearance:
                return False
        return True


def segment(number: int, pieces: int, res: list=None):
    """Segment a number into pieces using a binomial distribution."""
    if res is None:
        res = []
    if pieces == 0:
        return res
    piece = np.random.binomial(number, 1/pieces)
    return segment(number - piece, pieces - 1, res + [piece])


def main():
    """Grow trees in model where a seed tree has already been placed."""
    print("\n==> {:s}".format(__file__))
    # Get all arguments after '--'
    try:
        argv = sys.argv[sys.argv.index('--') + 1:]
    except ValueError:
        argv = []

    # Parse arguments
    prog_text = "blender MODEL --python {:s} --".format(__file__)
    parser = argparse.ArgumentParser(
        prog=prog_text, formatter_class=argparse.RawDescriptionHelpFormatter,
        description=__doc__, epilog="===")
    parser.add_argument("-n", "--number", metavar="N", type=int, default=32,
                        help="Number of trees to grow")
    parser.add_argument("-t", "--trees", metavar="TREE", type=str, nargs='*',
                        help="Names of the seed trees")
    parser.add_argument(
        "-l", "--landscape", metavar="NAME", type=str, default="Landscape",
        help="Name of landscape object in model (default: 'Landscape')")
    parser.add_argument(
        "-s", "--scale", metavar="DIST", type=float, default=8.,
        help="Scale of intertree distance (default: 8.0)")
    parser.add_argument(
        "-c", "--clearance", metavar="DIST", type=float, default=8.,
        help="Clearance between trees (default: 8.0)")
    args = parser.parse_args(argv)

    # Grow the trees
    grow = TreeGrowRandom(bpy.data.objects[args.landscape], set(args.trees),
                          args.scale, args.clearance)
    numbers = segment(args.number, len(args.trees))
    for tree, number in zip(args.trees, numbers):
        grow.grow_trees(number, [bpy.data.objects[tree]])

if __name__ == "__main__":
    main()

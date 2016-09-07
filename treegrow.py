#!/bin/bash
"true" '''\'
[ -z "$(which blender)" ] \
    && echo "blender not found: run the script manually" && exit 1

PYTHONPATH=$(python3 -c 'import sys; print(*sys.path, sep=":")')

model=$1
shift

if [ "$(uname)" == "Darwin" ]; then
    # Verbose env for Mac OS X
    exec $(which env) -v PYTHONPATH=":$PYTHONPATH" blender "$model" \
        --python "$0" -- "$@"
else
    # Unfortunately Linux doesn't have this flag
    exec $(which env) PYTHONPATH=":$PYTHONPATH" blender "$model" \
        --python "$0" -- "$@"
fi

exit 127
'''
import sys
import os
import json
import argparse
import itertools
import numpy as np
import bpy  # pylint: disable=import-error
import render.helpers as helpers

__doc__ = """Place trees randomly across scene."""


class BaseTreeGrow():
    """Grow trees! Base class for the novice landscape architect."""

    def __init__(self, landscape):
        """Create the landscape tree and set some default values."""
        # Create landscape tree for fast closest point lookup
        self.landscape = landscape
        self.landscape_tree = helpers.landscape_tree(landscape)

        # Set some default values
        self._dig = 0.1
        self._init_height = 15

    def _find_height(self, location):
        """Find the correct height for the tree."""
        closest_vertex, _, _ = self.landscape_tree.find(location)
        if (location[2] > closest_vertex[2] - self._dig
                and location[2] < closest_vertex[2]):
            return np.array(location)
        location[2] = closest_vertex[2] - np.random.uniform(0, self._dig)
        return self._find_height(location)


class TreeGrow(BaseTreeGrow):
    """Grow trees at specified locations."""

    def __init__(self, landscape, locations: dict):
        """Create trees on `landscape` as specified by `trees`.

        Dictionary `trees` should have existing object names as keys
        and corresponding lists of coordinate values. Already existing
        objects will be moved to specified coordinates and new trees
        will be grown as necessary.

        """
        BaseTreeGrow.__init__(self, landscape)
        self.locations = locations

    def grow_trees(self, key: str):
        """Grow trees with the specified key."""
        locations = self.locations[key]
        previous_trees = helpers.all_instances(key, bpy.data.objects)
        self._init_height = previous_trees[0].location[2]
        for location, tree in itertools.zip_longest(locations, previous_trees):
            if location is None:
                break
            if tree is None:
                # Duplicate last tree
                bpy.ops.object.select_all(action='DESELECT')
                previous_trees[-1].select = True
                bpy.ops.object.duplicate_move_linked(
                    OBJECT_OT_duplicate={"linked": True})
                tree = bpy.context.selected_objects[0]
            if not location.get("fixed"):
                # Find appropriate z coordinate at x, y position
                location["location"][2] = self._init_height
                location["location"] = \
                    self._find_height(location["location"]).tolist()
                location["rotation"] = [0, 0, np.random.uniform(0, 2*np.pi)]
                location["fixed"] = True
            tree.location = location["location"]
            tree.rotation_euler = location["rotation"]
        return locations

    def grow_all(self):
        """Grow all trees."""
        for key in self.locations:
            self.grow_trees(key)
        return self.locations


class TreeGrowRandom(BaseTreeGrow):
    """Grow random trees  with a specified scale and hard clearance."""

    def __init__(self, landscape, other_trees: set,
                 scale: float=8., clearance: float=8.):
        """Create object on landscape with other trees to avoid."""
        BaseTreeGrow.__init__(self, landscape)
        self.scale = scale
        self.clearance = clearance
        # Find existing trees
        self.trees = [obj for tree in other_trees
                      for obj in helpers.all_instances(tree, bpy.data.objects)]

        # Avoid other objects in the scene
        avoid_objects = [obj for obj in bpy.data.objects
                         if obj.type == "MESH"
                         and obj.name.split('.')[0] not in other_trees]
        avoid_objects.remove(self.landscape)
        self.avoid_tree = helpers.avoid_tree(avoid_objects)

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
        location[2] = self._init_height
        location = self._find_height(location)
        self._init_height = location[2]
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
        """Check if any other objects or trees are too close."""
        # Check with avoid tree
        closest_landscape, _, _ = self.landscape_tree.find(location)
        closest_avoid, _, _ = self.avoid_tree.find(location)
        if (closest_avoid[2] > closest_landscape[2]
                and np.linalg.norm(np.array(location[:2]) - closest_avoid[:2])
                < self.clearance):
            return False

        # Yes, I know... This scales quadratically.
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
    prog_text = "( {0:s} MODEL | blender MODEL --python {0:s} -- )".format(
        os.path.relpath(__file__))
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
    parser.add_argument("-o", "--out", metavar="FILE", type=str,
                        help="Write generated tree locations to file")
    args = parser.parse_args(argv)

    # Grow the trees
    grow = TreeGrowRandom(bpy.data.objects[args.landscape], set(args.trees),
                          args.scale, args.clearance)
    numbers = segment(args.number, len(args.trees))
    tree_types = []
    for tree, number in zip(args.trees, numbers):
        tree_types.append(grow.grow_trees(number, [bpy.data.objects[tree]]))
    if args.out is not None:
        out = {}
        for trees in tree_types:
            key = trees[0].name.split('.')[0]
            locations = [{"location": np.array(x.location).tolist(),
                          "rotation": np.array(x.rotation_euler).tolist(),
                          "fixed": True} for x in trees]
            out[key] = locations
        with open(args.out, 'w') as file:
            json.dump(out, file)

if __name__ == "__main__":
    main()

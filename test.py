"""Test the bridge package using model.blend"""
import sys
sys.path.append('/Users/jaantoots/mil')
import os
import json
import bpy
import bridge.render
import bridge.labels
import bridge.textures

objects = bpy.data.objects[:]
path = '/Users/jaantoots/mil/bridge_test'
render_file = 'render.json'
labels_file = 'labels.json'
textures_file = 'textures.json'
out_file = 'out.json'

rpath = os.path.join(path, render_file)
lpath = os.path.join(path, labels_file)
tpath = os.path.join(path, textures_file)
opath = os.path.join(path, out_file)

if os.path.isfile(lpath):
    labels = bridge.labels.Labels(objects)
    labels.read(lpath)
else:
    sys.exit("ERROR: Labels file not found: {:s}".format(lpath))

if os.path.isfile(tpath):
    textures = bridge.textures.Textures(objects)
    textures.read(tpath)
else:
    sys.exit("ERROR: Textures file not found: {:s}".format(tpath))

no_plane = objects[:]
no_plane.remove(bpy.data.objects['Landscape']) # Hack to get rid of Landscape 
if os.path.isfile(rpath):
    render = bridge.render.Render(no_plane, rpath)
else:
    render = bridge.render.Render(no_plane)
    render.write_conf(rpath)

def point():
    sun_rotation = render.random_sun()
    camera_location, camera_rotation = render.random_camera()
    return {'sun_rotation': sun_rotation,
            'camera_location': camera_location, 'camera_rotation': camera_rotation}

data = {"{:03d}".format(i): point() for i in range(4)}

for seq, point in data.items():
    render.place_sun(point['sun_rotation'])
    render.place_camera(point['camera_location'], point['camera_rotation'])
    textures.texture()
    render.render(path, seq)

for seq, point in data.items():
    render.place_camera(point['camera_location'], point['camera_rotation'])
    for level in range(3):
        labels.color_level(level)
        render.render_semantic(level, path, seq)

with open(opath, 'w') as file:
    json.dump(data, file)

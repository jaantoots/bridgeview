"""Print compute devices available to Blender."""
import bpy  # pylint: disable=import-error
import _cycles  # pylint: disable=import-error

print("Available devices:")
print(_cycles.available_devices())

syspref = bpy.context.user_preferences.system
print("Device types:")
try:
    syspref.compute_device_type = 'CAUSE_TYPEERROR'
except TypeError as err:
    text = err.args[0]
    print(text[text.find('('):])

syspref.compute_device_type = 'CUDA'
print("CUDA devices:")
try:
    syspref.compute_device = 'CAUSE_TYPEERROR'
except TypeError as err:
    text = err.args[0]
    print(text[text.find('('):])

print("Default CUDA device:")
print(syspref.compute_device)

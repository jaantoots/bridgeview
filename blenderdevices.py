"""Print compute devices available to Blender."""
import bpy # pylint: disable=import-error
import _cycles # pylint: disable=import-error

print(_cycles.available_devices())
bpy.context.user_preferences.system.compute_device = 'CAUSE_TYPEERROR'

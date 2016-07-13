"""Objects used by multiple modules"""

class Dict(dict):
    """Overload the missing method of builtin dict for brevity"""
    def __missing__(self, key):
        return []

def all_instances(part: str, objects):
    """Return all objects with a given name"""
    return [obj for obj in objects if part in obj.name.split('.')]

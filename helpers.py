"""Objects used by multiple modules"""

class Dict(dict):
    """Overload the missing method of builtin dict for brevity"""
    def __missing__(self, key):
        return []

def apply_to_instances(func, part, objects):
    """Apply a function to objects with a given name

    Execute func(obj) where `func` takes a single object as an argument,
    for all objects named `part` with optional suffixes separated by `.`

    """
    for obj in [obj for obj in objects if part in obj.name.split('.')]:
        func(obj)


import json
from .is_a import isAlias, isValue, isFile, isDir, isSymLink, isEntry


def json_type(node):
    if isSymLink(node):
        return "S"
    elif isFile(node):
        return "F"
    elif isDir(node):
        return "D"
    elif isAlias(node):
        return "A"
    elif isValue(node):
        return "V"
    elif isEntry(node):
        return "E"


def make_node(json_node, env):
    name = json_node["name"]
    string_type = json_node["type"]
    if string_type == "S":
        return env.FileSymbolicLink(name)
    elif string_type == "F":
        return env.File(name)
    elif string_type == "D":
        return env.Dir(name)
    elif string_type == "A":
        return env.Alias(name)
    elif string_type == "V":
        return env.Value(name)
    elif string_type == "E":
        return env.Entry(name)


class SetNodeEncode(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        # This should be a node
        try:
            return obj.ID
        except:
            return json.JSONEncoder.default(self, obj)

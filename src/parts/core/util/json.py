from __future__ import absolute_import, division, print_function
import json

class SetNodeEncode(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        # This should be a node
        try:
            return obj.ID
        except:
            return json.JSONEncoder.default(self, obj)


import parts.api as api
import parts.common as common
import parts.core as core
# This is what we want to be setup in parts
from SCons.Script.SConscript import SConsEnvironment


def MetaTag(nodes, ns='meta', **metakv):
    # make sure the nodes are in a list
    nodes = common.make_list(nodes)
    # for each node add the meta values
    for node in nodes:
        try:
            namespace = getattr(node.attributes, ns)
        except AttributeError:
            namespace = common.namespace()
            setattr(node.attributes, ns, namespace)

        for item in metakv.items():
            setattr(namespace, *item)

    return nodes


def MetaTagValue(node, key, ns='meta', default=None):
    try:
        return getattr(getattr(node.attributes, ns), key)
    except AttributeError:
        return default


def hasMetaTag(node, key, ns='meta'):
    try:
        return hasattr(getattr(node.attributes, ns), key)
    except AttributeError:
        return False


def MetaTag_method(env, nodes, ns='meta', **metakv):
    return MetaTag(nodes, ns, **metakv)


def MetaTagValue_method(env, node, key, ns='meta', default=None):
    return MetaTagValue(node, key, ns, default)


def hasMetaTag_method(env, node, key, ns='meta'):
    return hasMetaTag(node, key, ns)


def Tag_wrapper(env, nodes, ns='meta', **metakv):
    api.output.warning_msg("Please use MetaTag instead")
    return MetaTag(nodes, ns, **metakv)


# adding logic to Scons Environment object
api.register.add_method(MetaTag_method, 'MetaTag')
api.register.add_method(Tag_wrapper, 'Tag')  # to work around existing tag usage
api.register.add_method(MetaTagValue_method, 'MetaTagValue')
api.register.add_method(hasMetaTag_method, 'hasMetaTag')

api.register.add_global_parts_object('MetaTag', MetaTag)
api.register.add_global_parts_object('MetaTagValue', MetaTagValue)
api.register.add_global_parts_object('hasMetaTag', hasMetaTag)

api.register.add_global_object('MetaTag', MetaTag)
api.register.add_global_object('MetaTagValue', MetaTagValue)
api.register.add_global_object('hasMetaTag', hasMetaTag)

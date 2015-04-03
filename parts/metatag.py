import common
import core.util
import api.output

def MetaTag(nodes,ns='meta',**metakv):
    #make sure the nodes are in a list
    nodes=common.make_list(nodes)
    #for each node add the meta values
    for node in nodes:
        try:
            namespace = getattr(node.attributes, ns)
        except AttributeError:
            namespace = common.namespace()
            setattr(node.attributes, ns, namespace)

        for item in metakv.iteritems():
            setattr(namespace, *item)

def MetaTagValue(node,key,ns='meta',default=None):
    try:
        return getattr(getattr(node.attributes, ns), key)
    except AttributeError:
        return default

def hasMetaTag(node,key,ns='meta'):
    try:
        return hasattr(getattr(node.attributes, ns), key)
    except AttributeError:
        return False


def MetaTag_method(env,nodes,ns='meta',**metakv):
    return MetaTag(nodes,ns,**metakv)
def MetaTagValue_method(env,node,key,ns='meta',default=None):
    return MetaTagValue(node,key,ns,default)
def hasMetaTag_method(env,node,key,ns='meta'):
    return hasMetaTag(node,key,ns)

def Tag_wrapper(env,nodes,ns='meta',**metakv):
    api.output.warning_msg("Please use MetaTag instead")
    return MetaTag(nodes,ns,**metakv)


# This is what we want to be setup in parts
from SCons.Script.SConscript import SConsEnvironment

# adding logic to Scons Enviroment object
SConsEnvironment.MetaTag=MetaTag_method
SConsEnvironment.Tag=Tag_wrapper # to work around existing tag usage
SConsEnvironment.MetaTagValue=MetaTagValue_method
SConsEnvironment.hasMetaTag=hasMetaTag_method

api.register.add_global_parts_object('MetaTag',MetaTag)
api.register.add_global_parts_object('MetaTagValue',MetaTagValue)
api.register.add_global_parts_object('hasMetaTag',hasMetaTag)

api.register.add_global_object('MetaTag',MetaTag)
api.register.add_global_object('MetaTagValue',MetaTagValue)
api.register.add_global_object('hasMetaTag',hasMetaTag)



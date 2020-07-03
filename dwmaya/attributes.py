__author__ = 'Olivier Evers'
__copyright__ = 'DreamWall'
__license__ = 'MIT'


import maya.cmds as mc
import pymel.core as pm


def get_attr(node, attr):
    return mc.getAttr('%s.%s' % (node, attr))


def set_attr(node, attr, value):
    if isinstance(value, list):
        mc.setAttr('%s.%s' % (node, attr), *value)
    elif isinstance(value, basestring):
        mc.setAttr('%s.%s' % (node, attr), value, type='string')
    else:
        mc.setAttr('%s.%s' % (node, attr), value)


def lock_attr(node, attr):
    mc.setAttr('%s.%s' % (node, attr), lock=True)


def unlock_attr(node, attr):
    mc.setAttr('%s.%s' % (node, attr), lock=False)


def set_default_attribute_value(node, attr):
    default_value = mc.attributeQuery(attr, node=node, listDefault=True)[0]
    pm.Attribute('%s.%s' % (node, attr)).set(default_value)


def reset_animation_attributes(node):
    for attr in mc.listAnimatable(node):
        try:
            set_default_attribute_value(node, attr)
        except RuntimeError:
            print 'Skipped %s' % attr
            continue


def get_path_attributes(node):
    return mc.listAttr(node, usedAsFilename=True) or []

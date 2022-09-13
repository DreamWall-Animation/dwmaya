__author__ = 'Olivier Evers'
__copyright__ = 'DreamWall'
__license__ = 'MIT'


import itertools
import maya.cmds as mc
import pymel.core as pm


def lock_xform(node, keyable=None):
    tsr = ('t', 's', 'r')
    xyz = ('x', 'y', 'z')
    for op, axe in itertools.product(tsr, xyz):
        if keyable is not None:
            mc.setAttr(node + '.' + op + axe, keyable=keyable)
        lock_attr(node, op + axe)
        mc.setAttr(node + '.' + op + axe, lock=True)


def connect_attr(source, destination):
    node, attr = destination.split('.')
    if mc.attributeQuery(attr, node=node, multi=True):
        i = 0
        sub_destination = '{}[{}]'.format(destination, i)
        while mc.listConnections(sub_destination):
            sub_destination = '{}[{}]'.format(destination, i)
            i += 1
        destination = sub_destination
    mc.connectAttr(source, destination)


def get_attr(node, attr):
    return mc.getAttr('%s.%s' % (node, attr))


def set_attr(node, attr, value, skip_locked_connected=False):
    attribute = '%s.%s' % (node, attr)
    if skip_locked_connected:
        if mc.getAttr(attribute, locked=True) or mc.listConnections(attribute):
            return
    if isinstance(value, list):
        mc.setAttr(attribute, *value)
    elif isinstance(value, str):
        mc.setAttr(attribute, value, type='string')
    else:
        mc.setAttr(attribute, value)


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
            print('Skipped %s' % attr)
            continue


def get_path_attributes(node):
    return mc.listAttr(node, usedAsFilename=True) or []


def attribute_name(node):
    node, *attributes = node.split('.')
    return '.'.join(attributes)

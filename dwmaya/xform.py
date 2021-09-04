__author__ = 'Lionel Brouyere, Olivier Evers'
__copyright__ = 'DreamWall'
__license__ = 'MIT'


import maya.cmds as mc
from dwmaya.hierarchy import get_parents


def copy_position_rotation_scale(source, target):
    rot = mc.getAttr(source + '.rotate')[0]
    pos = mc.getAttr(source + '.translate')[0]
    scale = mc.getAttr(source + '.scale')[0]
    mc.setAttr(target + '.rotate', *rot)
    mc.setAttr(target + '.translate', *pos)
    mc.setAttr(target + '.scale', *scale)


def points_distance(p1, p2):
    x1, y1, z1 = p1
    x2, y2, z2 = p2
    return ((x2 - x1)**2 + (y2 - y1)**2 + (z2 - z1)**2) ** .5


def get_distance(transform1, transform2):
    p1 = mc.xform(transform1, query=True, translation=True, worldSpace=True)
    p2 = mc.xform(transform2, query=True, translation=True, worldSpace=True)
    return points_distance(p1, p2)


def has_rotated_parent_or_animated_parents(node):
    parents = get_parents(mc.ls(node, long=True))
    parents = sorted(list(parents), key=lambda n: n.count('|'))
    if not parents:
        return False
    # check parent world rotation
    parent_world_rotation = mc.xform(
        parents[-1], query=True, rotation=True, worldSpace=True)
    if parent_world_rotation != [0, 0, 0]:
        return True
    if mc.keyframe(parents, query=True):
        return True
    return any(
        'constrain' in mc.nodeType(connection).lower()
        for connection in mc.listConnections(parents) or [])
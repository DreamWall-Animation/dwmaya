__author__ = 'Olivier Evers'
__copyright__ = 'DreamWall'
__license__ = 'MIT'


import maya.cmds as mc


def get_shape_and_transform(shape_or_transform):
    if mc.ls(shape_or_transform, shapes=True):
        shape = shape_or_transform
        transform = mc.listRelatives(shape, parent=True, path=True)[0]
    else:
        transform = shape_or_transform
        transform = mc.listRelatives(transform, children=True, path=True)[0]
    return shape, transform

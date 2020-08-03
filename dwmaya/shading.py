__author__ = 'Olivier Evers'
__copyright__ = 'DreamWall'
__license__ = 'MIT'


import maya.cmds as mc


def get_shading_assignments():
    assignments = {}
    for sg in mc.ls(type='shadingEngine'):
        assignments[sg] = mc.sets(sg, query=True)
    return assignments

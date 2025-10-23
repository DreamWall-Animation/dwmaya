
__author__ = 'Lionel Brouyere'
__copyright__ = 'DreamWall'
__license__ = 'MIT'


import maya.cmds as mc
from dwmaya.deformer.tweak import ensure_deformation_tweak_creation


@ensure_deformation_tweak_creation
def create_multitarget_blendshape(bases, targets):
    blendshape = None
    blendshape_set = None
    for i, (base, target) in enumerate(zip(bases, targets)):
        if blendshape is None:
            blendshape = mc.blendShape(target, base, origin='world')[0]
            connections = mc.listConnections(blendshape)
            blendshape_set = mc.ls(connections, type='objectSet')[0]
        else:
            parent = mc.listRelatives(base, parent=True, fullPath=True)
            types = ("nurbsCurve", "mesh")
            neightbourgs = mc.listRelatives(parent, type=types, fullPath=True)
            mc.sets(neightbourgs, add=blendshape_set)
            mc.blendShape(
                blendshape,
                edit=True,
                before=True,
                target=(base, i, target, 1.0))
        mc.blendShape(blendshape, edit=True, weight=(i, 1.0))
    return blendshape


__author__ = 'Lionel Brouyere'
__copyright__ = 'DreamWall'
__license__ = 'MIT'


import maya.cmds as mc
from dwmaya.deformer.tag import force_deformation_component_tags_var


@force_deformation_component_tags_var(state=False)
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


@force_deformation_component_tags_var(False)
def create_transform_children_blendshapes(base_transform, target_transform):
    base_transform = mc.ls(base_transform, long=True, noIntermediate=True)[0]
    target_transform = mc.ls(target_transform, long=True, noIntermediate=1)[0]
    types = ("nurbsCurve", "mesh")
    bases = mc.listRelatives(
        base_transform,
        fullPath=True,
        type=types,
        allDescendents=True)
    blendshape = None
    blendshape_set = None
    i = 0
    for base in bases:
        target = f'{target_transform}|{base[len(base_transform):]}'
        if not mc.objExists(target):
            print(f'Missing target: {target}')
            continue
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
        i += 1
    return blendshape


if __name__ == "__main__":
    create_transform_children_blendshapes("Rocky_grooming_main_default|rocky_main_wires", "|rocky_main_wires")

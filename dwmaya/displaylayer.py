import maya.cmds as mc


def clear_display_layers():
    layers = mc.ls(type='displayLayer')
    layers.remove('defaultLayer')
    layers = [l for l in layers if not mc.referenceQuery(isNodeReferenced=l)]
    if not layers:
        return
    for layer in layers:
        mc.lockNode(layer, lock=False)
    mc.delete(layers)

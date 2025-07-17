import maya.cmds as mc


def clear_display_layers():
    layers = mc.ls(type='displayLayer')
    layers.remove('defaultLayer')
    layers = [
        layer for layer in layers
        if not mc.referenceQuery(layer, isNodeReferenced=True)]
    if not layers:
        return
    for layer in layers:
        mc.lockNode(layer, lock=False)
    mc.delete(layers)
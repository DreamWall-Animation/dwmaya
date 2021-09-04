__author__ = 'Lionel Brouyere, Olivier Evers'
__copyright__ = 'DreamWall'
__license__ = 'MIT'


import maya.cmds as mc
from dwmaya.animation.curve import delete_connected_curves, ANIMATION_CURVE_TYPES
from dwmaya.attributes import attr_name, set_default_attribute_value, node_name


EXCLUDE_FOR_ZERO_OUT = [
    "s", "sx", "sy", "sz", "scale", "scaleX", "scaleY", "scaleZ", "v",
    "visibility"]


def transfer_animation_curves(src, dst, reset_source=True):
    """
    Transfer animation curve found on source to corresponding attribute on
    destination.
    """
    # Clean existing animation on destination.
    delete_connected_curves(dst)

    connections = [
        c for ct in ANIMATION_CURVE_TYPES for c in
        mc.listConnections(src, connections=True, plugs=True, type=ct) or []]
    outputs = [c for i, c in enumerate(connections) if i %2 == 1]
    src_inputs = [c for i, c in enumerate(connections) if i %2 == 0]
    dst_inputs = [dst + "." + attr_name(input_)for input_ in src_inputs]

    for src_input, dst_input, output in zip(src_inputs, dst_inputs, outputs):
        if not mc.objExists(dst_input):
            continue
        mc.connectAttr(output, dst_input)
        if not reset_source:
            continue
        mc.disconnectAttr(output, src_input)
        set_default_attribute_value(node_name(src_input), attr_name(src_input))


def copy_animation(source, destination, offset=0):
    """
    Copy animation from source to destination
    :param str source: Transform node name.
    :param str destination: Transform node name.
    :param int offset: Time offset.
    """
    if not mc.objExists(source) or not mc.objExists(destination):
        return
    mc.copyKey(source)
    delete_connected_curves(destination)
    mc.pasteKey(destination, option='replaceCompletely', timeOffset=offset)


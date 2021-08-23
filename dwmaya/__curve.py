from maya import cmds
import maya.api.OpenMaya as om2
import maya.api.OpenMayaAnim as oma2
from logging import getlogger

from __namespace import strip_namespaces
from __attributes import attribute_name

logger = getlogger()


ANIMATION_CURVES_TYPES = (
    "animCurveTA", "animCurveTL", "animCurveTT", "animCurveTU")


def list_curves_with_infinite_set(
        curves=None, pre=True, post=False, types=None):
    """ List the animtion curves which has post or pre virtual animation set on.
    :param curves: list() of str. Name of the animation curves. If it is
    set to none, function will check all the scene anim curves.
    :param pre: bool list curve with pre infinite set
    :param post: bool list curve with post infinite set
    :param types: str or tuple() of str. Type of animation curves animCurveTU,
    TT, TA, TL
    :rtype: list() of str
    """
    curves = curves or cmds.ls(type=types or ANIMATION_CURVES_TYPES)
    if pre:
        curves = [c for c in curves if cmds.getAttr(c + ".preInfinity")]
    if post:
        curves = [c for c in curves if cmds.getAttr(c + ".postInfinity")]
    return curves


def list_curves_with_namespace(
        curves=None, exclude_references=True, types=None):
    """ List curves which are under a namspace.
    :param curves: list() of str. Name of the animation curves. If it is
    set to none, function will check all the scene anim curves.
    :param exclude_references: bool, do not return curves in reference.
    :param types: str or tuple() of str. Type of animation curves animCurveTU,
    TT, TA, TL
    :rtype: list() of str
    """
    curves = curves or cmds.ls(type=types or ANIMATION_CURVES_TYPES)
    if exclude_references:
        curves = [
            curve for curve in curves
            if not cmds.referenceQuery(curve, isNodeReferenced=True)]
    return [curve for curve in curves if ":" in curve]


def strip_curves_namespaces(curves=None, types=None):
    """ Strip namespace on each curve given.
    :param curves: list() of str. Name of the animation curves. If it is
    set to none, function will check all the scene anim curves.
    :param types: str or tuple() of str. Type of animation curves animCurveTU,
    TT, TA, TL
    """
    curves = list_curves_with_namespace(curves, exclude_references=True, types=types)
    for curve in curves:
        cmds.rename(curve, strip_namespaces(curve))


def node_names_to_mfn_anim_curves(nodes):
    """ Convert an anim curve name to a maya.OpenMayaAnim.MFnAnimCurve object
    :param node: str or list() of string
    :param types: str or tuple() of str. Type of animation curves animCurveTU,
    TT, TA, TL
    :rtype: maya.OpenMayaAnim.MFnAnimCurve
    """
    if isinstance(nodes, basestring):
        nodes = [nodes]

    sel = om2.MSelectionList()
    mfn_anim_curves = []
    for i, node in enumerate(nodes):
        sel.add(node)
        mfn_anim_curves.append(oma2.MFnAnimCurve(sel.getDependNode(i)))
    return mfn_anim_curves


def list_non_static_anim_curves(curves=None, types=None):
    """
    List all static curves in the scene or in the given curves. A static curve,
    is a curve where all the keys are the same value.
    :param types: str or tuple() of str. Type of animation curves animCurveTU,
    TT, TA, TL
    :rtype: list() of str
    """
    anim_curves = curves or cmds.ls(type=types or ANIMATION_CURVES_TYPES)
    anim_curves = node_names_to_mfn_anim_curves(anim_curves)
    return [c.name() for c in anim_curves if not c.isStatic]


def delete_unconnected_anim_curves(types=None):
    """
    Delete all the unused animation curves found in the current maya scene.
    :param types: str or tuple() of str. Type of animation curves animCurveTU,
    TT, TA, TL
    """
    cmds.delete([
        curve for curve in cmds.ls(type=types or ANIMATION_CURVES_TYPES)
        if not cmds.listConnections(curve)])


def find_anim_curve_source(plug):
    """
    This function goes up the connections stream to reach out the anim curve
    node providing animation.
    :param str plug: Maya plug path as string.
    :rtype: str Maya anim curve node name.
    """
    source = cmds.connectionInfo(plug, sourceFromDestination=True)
    while source:
        if cmds.nodeType(source) in ANIMATION_CURVES_TYPES:
            return source.split(".")[0]
        source = cmds.connectionInfo(source, sourceFromDestination=True)


def delete_connected_curves(node):
    """
    delete animation curves connected to given node.
    :param str node: Maya node name.
    """
    for type_ in ANIMATION_CURVES_TYPES:
        anim_curves = list({
            curve.split(".")[0] for curve in
            cmds.listConnections(node, type=type_, plugs=True, source=True)
            or []})
        if not anim_curves:
            continue
        cmds.delete(anim_curves)


def copy_animation(source, destination, offset=0):
    """
    Copy animation from source to destination
    :param str source: Transform node name.
    :param str destination: Transform node name.
    :param int offset: Time offset.
    """
    if not cmds.objExists(source) or not cmds.objExists(destination):
        return
    cmds.copyKey(source)
    delete_connected_curves(destination)
    cmds.pasteKey(destination, option='replaceCompletely', timeOffset=offset)


EXCLUDE_FOR_ZERO_OUT = [
    "s", "sx", "sy", "sz", "scale", "scaleX", "scaleY", "scaleZ", "v",
    "visibility"]


def transfer_animation_curves(src, dst, zero_out_source=True):
    """
    Transfer animation curve found on source to corresponding attribute on
    destination.
    :param str src: Maya node name.
    :param str dst: Maya node name.
    :param bool zero_out_source: Zero out the source attribute
    """

    # Clean existing animation on destination.
    delete_connected_curves(dst)

    connections = [
        c for ct in ANIMATION_CURVES_TYPES for c in
        cmds.listConnections(src, connections=True, plugs=True, type=ct) or []]
    outputs = [c for i, c in enumerate(connections) if i %2 == 1]
    src_inputs = [c for i, c in enumerate(connections) if i %2 == 0]
    dst_inputs = [dst + "." + attribute_name(input_)for input_ in src_inputs]

    failures = []
    for src_input, dst_input, output in zip(src_inputs, dst_inputs, outputs):
        if not cmds.objExists(dst_input):
            failures.append("\b{} ==> {}\n".format(src_input, dst_input))
            continue

        cmds.connectAttr(output, dst_input)
        if not zero_out_source:
            continue
        cmds.disconnectAttr(output, src_input)
        if attribute_name(src_input) in EXCLUDE_FOR_ZERO_OUT:
            continue
        cmds.setAttr(src_input, 0.0)

    if failures:
        logger.info(
            "Impossible to transfer those attribute, "
            "destination doesn't exists.\n" + "".join(failures))

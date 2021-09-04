__author__ = 'Lionel Brouyere, Olivier Evers'
__copyright__ = 'DreamWall'
__license__ = 'MIT'


import maya.cmds as mc
import maya.api.OpenMaya as om2
import maya.api.OpenMayaAnim as oma2

from dwmaya.namespace import strip_namespaces


ANIMATION_CURVE_TYPES = (
    "animCurveTA", "animCurveTL", "animCurveTT", "animCurveTU")


def get_animated_nodes():
    return mc.listConnections(get_anim_curves()) or []


def get_anim_curves():
    return mc.ls(type=ANIMATION_CURVE_TYPES)


def get_selected_curves():
    return mc.keyframe(query=True, selected=True, name=True)


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
    curves = curves or mc.ls(type=types or ANIMATION_CURVE_TYPES)
    if pre:
        curves = [c for c in curves if mc.getAttr(c + ".preInfinity")]
    if post:
        curves = [c for c in curves if mc.getAttr(c + ".postInfinity")]
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
    curves = curves or mc.ls(type=types or ANIMATION_CURVE_TYPES)
    if exclude_references:
        curves = [
            curve for curve in curves
            if not mc.referenceQuery(curve, isNodeReferenced=True)]
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
        mc.rename(curve, strip_namespaces(curve))


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
    anim_curves = curves or mc.ls(type=types or ANIMATION_CURVE_TYPES)
    anim_curves = node_names_to_mfn_anim_curves(anim_curves)
    return [c.name() for c in anim_curves if not c.isStatic]


def delete_unconnected_anim_curves(types=None):
    """
    Delete all the unused animation curves found in the current maya scene.
    :param types: str or tuple() of str. Type of animation curves animCurveTU,
    TT, TA, TL
    """
    mc.delete([
        curve for curve in mc.ls(type=types or ANIMATION_CURVE_TYPES)
        if not mc.listConnections(curve)])


def find_anim_curve_source(plug):
    """
    This function goes up the connections stream to reach out the anim curve
    node providing animation.
    :param str plug: Maya plug path as string.
    :rtype: str Maya anim curve node name.
    """
    source = mc.connectionInfo(plug, sourceFromDestination=True)
    while source:
        if mc.nodeType(source) in ANIMATION_CURVE_TYPES:
            return source.split(".")[0]
        source = mc.connectionInfo(source, sourceFromDestination=True)


def delete_connected_curves(node):
    """
    delete animation curves connected to given node.
    :param str node: Maya node name.
    """
    for type_ in ANIMATION_CURVE_TYPES:
        anim_curves = list({
            curve.split(".")[0] for curve in
            mc.listConnections(node, type=type_, plugs=True, source=True)
            or []})
        if not anim_curves:
            continue
        mc.delete(anim_curves)

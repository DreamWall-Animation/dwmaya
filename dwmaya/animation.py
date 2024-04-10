__author__ = 'Olivier Evers'
__copyright__ = 'DreamWall'
__license__ = 'MIT'


import json
import math
from functools import partial
from contextlib import contextmanager

import maya.mel as mm
import maya.cmds as mc
import maya.OpenMaya as om
import maya.OpenMayaAnim as oma
import maya.api.OpenMaya as om2
import maya.api.OpenMayaAnim as oma2

from dwmaya.attributes import attribute_name
from dwmaya.hierarchy import get_parents
from dwmaya.namespace import get_non_existing_namespace, strip_namespaces


ANIMATION_CURVE_TYPES = (
    'animCurveTA', 'animCurveTL', 'animCurveTT', 'animCurveTU')


ANIMATION_NODE_TYPES = (
    'animBlend',
    'animBlendInOut',
    'animBlendNodeAdditive',
    'animBlendNodeAdditiveDA',
    'animBlendNodeAdditiveDL',
    'animBlendNodeAdditiveF',
    'animBlendNodeAdditiveFA',
    'animBlendNodeAdditiveFL',
    'animBlendNodeAdditiveI16',
    'animBlendNodeAdditiveI32',
    'animBlendNodeAdditiveRotation',
    'animBlendNodeAdditiveScale',
    'animBlendNodeBoolean',
    'animBlendNodeEnum',
    'animBlendNodeTime',
    'animClip',
    'animCurveTA',
    'animCurveTL',
    'animCurveTT',
    'animCurveTU',
    'animCurveUA',
    'animCurveUL',
    'animCurveUT',
    'animCurveUU',
    'animLayer')


OPEN_MAYA_TANGENT_TYPES = {
    'global': oma2.MFnAnimCurve.kTangentGlobal,
    'fixed': oma2.MFnAnimCurve.kTangentFixed,
    'linear': oma2.MFnAnimCurve.kTangentLinear,
    'flat': oma2.MFnAnimCurve.kTangentFlat,
    'smooth': oma2.MFnAnimCurve.kTangentSmooth,
    'step': oma2.MFnAnimCurve.kTangentStep,
    'slow': oma2.MFnAnimCurve.kTangentSlow,
    'fast': oma2.MFnAnimCurve.kTangentFast,
    'clamped': oma2.MFnAnimCurve.kTangentClamped,
    'plateau': oma2.MFnAnimCurve.kTangentPlateau,
    'stepnext': oma2.MFnAnimCurve.kTangentStepNext,
}


def get_scene_frames():
    return list(range(
        int(mc.playbackOptions(query=True, animationStartTime=True)),
        int(mc.playbackOptions(query=True, animationEndTime=True) + 1)))


def get_anim_curves():
    return mc.ls(type=ANIMATION_CURVE_TYPES)


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
    curves = list_curves_with_namespace(
        curves, exclude_references=True, types=types)
    for curve in curves:
        mc.rename(curve, strip_namespaces(curve))


def node_names_to_mfn_anim_curves(nodes):
    """ Convert an anim curve name to a maya.OpenMayaAnim.MFnAnimCurve object
    :param node: str or list() of string
    :param types: str or tuple() of str. Type of animation curves animCurveTU,
    TT, TA, TL
    :rtype: maya.OpenMayaAnim.MFnAnimCurve
    """
    if isinstance(nodes, str):
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
        c for ct in ANIMATION_CURVE_TYPES for c in
        mc.listConnections(src, connections=True, plugs=True, type=ct) or []]
    outputs = [c for i, c in enumerate(connections) if i % 2 == 1]
    src_inputs = [c for i, c in enumerate(connections) if i % 2 == 0]
    dst_inputs = [dst + "." + attribute_name(input_)for input_ in src_inputs]

    failures = []
    for src_input, dst_input, output in zip(src_inputs, dst_inputs, outputs):
        if not mc.objExists(dst_input):
            failures.append("\b{} ==> {}\n".format(src_input, dst_input))
            continue

        mc.connectAttr(output, dst_input)
        if not zero_out_source:
            continue
        mc.disconnectAttr(output, src_input)
        if attribute_name(src_input) in EXCLUDE_FOR_ZERO_OUT:
            continue
        mc.setAttr(src_input, 0.0)

    if failures:
        print(
            "Impossible to transfer those attribute, "
            "destination doesn't exists.\n" + "".join(failures))


def list_connected_curves(node):
    curves = []
    for type_ in ANIMATION_CURVE_TYPES:
        curves.extend(list({
            curve.split(".")[0] for curve in
            mc.listConnections(node, type=type_, plugs=True, source=True)
            or []}))
    return curves


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


def get_animated_nodes():
    return mc.listConnections(get_anim_curves()) or []


def copy_position_rotation_scale(source, target):
    rot = mc.getAttr(source + '.rotate')[0]
    pos = mc.getAttr(source + '.translate')[0]
    scale = mc.getAttr(source + '.scale')[0]
    mc.setAttr(target + '.rotate', *rot)
    mc.setAttr(target + '.translate', *pos)
    mc.setAttr(target + '.scale', *scale)


def motion_to_curve(transform):
    start = mc.playbackOptions(query=True, min=True)
    end = mc.playbackOptions(query=True, max=True)
    mel_command = 'curve -d 1'
    for frame in range(int(start), int(end) + 1):
        mc.currentTime(frame)
        x, y, z = mc.getAttr(transform + '.translate')[0]
        mel_command += ' -p %f %f %f' % (x, y, z)
    mm.eval(mel_command)


def _get_distance(p1, p2):
    x1, y1, z1 = p1
    x2, y2, z2 = p2
    return ((x2 - x1)**2 + (y2 - y1)**2 + (z2 - z1)**2) ** .5


def get_distance(transform1, transform2):
    p1 = mc.xform(transform1, query=True, translation=True, worldSpace=True)
    p2 = mc.xform(transform2, query=True, translation=True, worldSpace=True)
    return _get_distance(p1, p2)


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
    for connection in mc.listConnections(parents) or []:
        if 'constrain' in mc.nodeType(connection).lower():
            return True
    return False


@contextmanager
def temp_DG_evaluation():
    initial_mode = mc.evaluationManager(query=True, mode=True)[0]
    mc.evaluationManager(mode='off')
    try:
        yield
    finally:
        mc.evaluationManager(mode=initial_mode)


@contextmanager
def temp_autokey_off():
    initial_mode = mc.autoKeyframe(query=True, state=True)
    mc.autoKeyframe(state=False)
    try:
        yield
    finally:
        mc.autoKeyframe(state=initial_mode)


def toggle_parallel_evaluation():
    current_mode = mc.evaluationManager(query=True, mode=True)[0]
    if current_mode == 'off':
        new_name = new_mode = 'parallel'
    else:
        new_mode = 'off'
        new_name = 'DG'
    mc.warning('Switched evaluation manager to "%s"' % new_name.upper())
    mc.evaluationManager(mode=new_mode)


def get_selected_curves():
    return mc.keyframe(query=True, selected=True, name=True)


def delete_non_integer_keys():
    anim_curves = mc.keyframe(query=True, selected=True, name=True)
    if not anim_curves:
        times = mc.keyframe(query=True, timeChange=True)
        non_integer = list(set([t for t in times if t != int(t)]))
        for time in non_integer:
            mc.cutKey(time=(time, time))
    else:
        curves_keyframes = {
            curve: mc.keyframe(curve, query=True, selected=True) for
            curve in anim_curves}
        for curve, times in curves_keyframes.items():
            non_integer = list(set([t for t in times if t != int(t)]))
            for time in non_integer:
                mc.cutKey(curve, time=(time, time))


def retime(
        animation_curves,
        start_frame, end_frame,
        new_start_frame, new_end_frame,
        offset_contiguous_animation=True, snap_keys=True):
    """Scale time range but also offset what's contiguous to keep continuity"""
    # Define offsets happening before and after:
    end_offset = new_end_frame - end_frame
    start_offset = new_start_frame - start_frame

    # Define offset functions:
    keys = mc.keyframe(animation_curves, query=True)
    max_keyframe = max(keys) + start_offset + end_offset
    offset_after_function = partial(
        mc.keyframe, animation_curves, edit=True,
        t=(end_frame + 1, max_keyframe), relative=True,
        timeChange=end_offset, option='over')
    min_keyframe = min(keys) - end_offset - start_offset
    offset_before_function = partial(
        mc.keyframe, animation_curves, edit=True,
        t=(min_keyframe, start_frame - 1), relative=True,
        timeChange=start_offset, option='over')

    # Offsets in case of expansion:
    if offset_contiguous_animation and end_offset > 0:
        offset_after_function()
    if offset_contiguous_animation and start_offset < 0:
        offset_before_function()

    # Retime/scale animation:
    mc.scaleKey(
        animation_curves, time=(start_frame, end_frame),
        newStartTime=new_start_frame, newEndTime=new_end_frame)
    if snap_keys:
        mc.snapKey(animation_curves, t=(new_start_frame, new_end_frame))

    # Offsets in case of shrinking:
    if offset_contiguous_animation and end_offset < 0:
        offset_after_function()
    if offset_contiguous_animation and start_offset > 0:
        offset_before_function()


def get_current_time_range():
    if not mc.about(batch=True):
        start, end = mc.timeControl(
            'timeControl1', query=True, rangeArray=True)
    if mc.about(batch=True) or end - start == 1:
        start = mc.playbackOptions(query=True, animationStartTime=True)
        end = mc.playbackOptions(query=True, animationEndTime=True)
    return start, end


def export_animation(export_path):
    if not export_path.endswith('.ma'):
        export_path += '.ma'
    # 1: export maya file with anim layers, curves, and blend nodes:
    blend_types = [
        t for t in mc.listNodeTypes('animation') if t.startswith('animBlend')]
    blenders = mc.ls(type=blend_types)
    curves = get_anim_curves()
    layers = mc.ls(type='animLayer')
    mc.select(blenders + curves + layers)
    mc.file(
        export_path, typ='mayaAscii', force=True, prompt=False,
        exportSelectedStrict=True, constructionHistory=False)
    # 2: export list of connections to recover
    source_nodes = curves + blenders
    connections = []
    targets = set(
        mc.listConnections(source_nodes, destination=True, plugs=True))
    for target in targets:
        target_node = target.split('.')[0]
        if target_node in source_nodes:
            # Connections between each other are already in export maya file
            continue
        node_type = mc.nodeType(target_node)
        if node_type == 'animLayer' or 'EditorInfo' in node_type:
            continue
        for source in mc.listConnections(target, source=True, plugs=True):
            source_node = source.split('.')[0]
            if source_node not in source_nodes:
                continue
            connection = (source, target)
            if connection not in connections:
                connections.append(connection)
    with open(export_path + '.json', 'w') as f:
        json.dump(connections, f, indent=4)


def import_animation(import_path):
    if not import_path.endswith('.ma'):
        import_path += '.ma'
    # Remove pre-existing layers if any
    layers = mc.ls(type='animLayer')
    if layers:
        mc.delete(layers)
    # Import Maya file with layers and curves
    namespace = get_non_existing_namespace()
    mc.file(import_path, i=True, namespace=namespace)
    # Reconnect nodes
    with open(import_path + '.json', 'r') as f:
        connections = json.load(f)
    failed_reconnections = []
    for source, target in connections:
        try:
            mc.connectAttr(namespace + ':' + source, target, force=True)
        except RuntimeError:
            failed_reconnections.append((source, target))
    # Remove namespace for animLayers
    for layer in mc.ls(namespace + ':*', type='animLayer'):
        mc.rename(layer, layer.split(':')[-1])
    return failed_reconnections


def delete_animation_for_selected_references(exclude_selected_nodes=True):
    """Delete animation on selected namespaces"""
    selected_nodes = mc.ls(selection=True)
    namespaces = set([n.split(':')[0] for n in selected_nodes])
    nodes = mc.ls([n + ':*' for n in namespaces])
    if exclude_selected_nodes:
        nodes = list(set(nodes) - set(selected_nodes))
    anim_nodes = []
    connections = mc.listConnections(nodes, source=True) or []
    anim_nodes.extend(mc.ls(connections, type=ANIMATION_NODE_TYPES))
    if anim_nodes:
        mc.delete(anim_nodes)
    else:
        mc.warning('No animation curve found.')


def select_constraints_on_selected_references():
    """Select constraints without namespaces on selected namespaces"""
    selected_nodes = mc.ls(selection=True)
    namespaces = set([n.split(':')[0] for n in selected_nodes])
    nodes = mc.ls([n + ':*' for n in namespaces])
    constraints = [
        n for n in mc.listConnections(nodes) or [] if
        'constr' in mc.nodeType(n).lower() and ':' not in n]
    if not constraints:
        mc.warning('Nothing to select')
    else:
        mc.warning('%i constraints found' % len(constraints))
        mc.select(constraints)


def get_openmaya_curve(curve_name):
    sel = om.MSelectionList()
    sel.add(curve_name)
    mobj = om.MObject()
    sel.getDependNode(0, mobj)
    return oma.MFnAnimCurve(mobj)


def bake_animation(
        anim_curves, frames, skip_static_curves=True,
        tangent_in='stepnext', tangent_out='step'):
    """
    This is faster than using maya.cmds.setKeyframes().

    If a script needs to unlock animation layers, this will have to be placed
    in an evalDeferred() call :(
    """
    tangent_in = OPEN_MAYA_TANGENT_TYPES[tangent_in]
    tangent_out = OPEN_MAYA_TANGENT_TYPES[tangent_out]
    time_unit = om.MTime.uiUnit()
    for curve_name in anim_curves:
        om_curve = get_openmaya_curve(curve_name)
        if om_curve.isStatic() and skip_static_curves:
            continue
        time_array = om.MTimeArray()
        value_array = om.MDoubleArray()
        for frame in frames:
            mtime = om.MTime(frame, time_unit)
            time_array.append(mtime)
            value_array.append(om_curve.evaluate(mtime))
        om_curve.addKeys(
            time_array,
            value_array,
            oma.MFnAnimCurve.kTangentStepNext,
            oma.MFnAnimCurve.kTangentStep,
            False)


def add_pre_post_roll(
        anim_curves=None, start=None, end=None, pre_frames=10, post_frames=10):
    """
    On each curve, add a key at the the preroll and post roll frames.
    Set their value to follow the tangent of the first/last key.
    """
    anim_curves = anim_curves or get_anim_curves()
    start = start or mc.playbackOptions(query=True, animationStartTime=True)
    pre_frame = start - pre_frames
    end = end or mc.playbackOptions(query=True, animationEndTime=True)
    post_frame = end + post_frames
    time_unit = om.MTime.uiUnit()
    for i, curve_name in enumerate(anim_curves):
        om_curve = get_openmaya_curve(curve_name)
        om2_curve = node_names_to_mfn_anim_curves([curve_name])[0]
        if om_curve.isStatic():
            continue
        # Pre-roll:
        first_frame = om_curve.time(0).value()
        delta = first_frame - pre_frame
        if delta > 0:
            value = om_curve.value(0)
            angle = om2_curve.getTangentAngleWeight(0, False)[0].value
            if angle != 0:
                offset = math.sin(angle) / math.cos(angle) * delta
                om_curve.addKey(
                    om.MTime(pre_frame, time_unit),
                    value - offset,
                    oma2.MFnAnimCurve.kTangentLinear,
                    oma2.MFnAnimCurve.kTangentLinear)
        # Post-roll:
        i = om_curve.numKeys() - 1
        last_frame = om_curve.time(i).value()
        delta = post_frame - last_frame
        if delta > 0:
            value = om_curve.value(i)
            om2_curve = node_names_to_mfn_anim_curves([curve_name])[0]
            angle = om2_curve.getTangentAngleWeight(i, True)[0].value
            if angle != 0:
                offset = math.sin(angle) / math.cos(angle) * delta
                om_curve.addKey(
                    om.MTime(post_frame, time_unit),
                    value + offset,
                    oma2.MFnAnimCurve.kTangentLinear,
                    oma2.MFnAnimCurve.kTangentLinear)

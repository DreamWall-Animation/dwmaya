__author__ = 'Olivier Evers'
__copyright__ = 'DreamWall'
__license__ = 'MIT'


import json
from functools import partial
from contextlib import contextmanager

import maya.mel as mm
import maya.cmds as mc

from dwmaya.hierarchy import get_parents
from dwmaya.namespace import get_non_existing_namespace


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


def get_anim_curves():
    return mc.ls(type=ANIMATION_CURVE_TYPES)


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
        yield None
    finally:
        mc.evaluationManager(mode=initial_mode)


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

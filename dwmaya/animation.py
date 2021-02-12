__author__ = 'Olivier Evers'
__copyright__ = 'DreamWall'
__license__ = 'MIT'


from functools import partial
from contextlib import contextmanager

import maya.mel as mm
import maya.cmds as mc

from dwmaya.hierarchy import get_parents


ANIMATION_CURVE_TYPES = (
    'animCurveTA', 'animCurveTL', 'animCurveTT', 'animCurveTU')


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
        mc.snapKey(animation_curves, t=(start_frame, new_end_frame))

    # Offsets in case of shrinking:
    if offset_contiguous_animation and end_offset < 0:
        offset_after_function()
    if offset_contiguous_animation and start_offset > 0:
        offset_before_function()

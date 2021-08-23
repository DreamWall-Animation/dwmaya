from functools import partial
from maya import cmds
import pymel.core as pm
import maya.api.OpenMaya as om2
import maya.api.OpenMayaAnim as oma2
from logging import getlogger
from __curve import (
    list_non_static_anim_curves, node_names_to_mfn_anim_curves)


logger = getlogger()


def add_keyframe(frame, anim_curve, attribute):
    """
    Used to add a Keyframe and set Tangent Type
    after the last Keyframe and
    before the first Keyframe.

    :param int frame:
    :param pm.nodetypes.AnimCurve anim_curve:
    :param pm.general.Attribute attribute:
    :return:
    """
    # Skip Animation Curves that has no Keyframe.
    if anim_curve.numKeys() < 1:
        return

    # Get Animation Curve's start and end frame.
    curve_start_frame = anim_curve.getTime(0)
    curve_end_frame = anim_curve.getTime(anim_curve.numKeys() - 1)

    # Need to insert a key within the current range of the anim curve
    if curve_start_frame < frame < curve_end_frame:
        attribute.setKey(time=frame, insert=True)
        return
    # Need to add a key after the current last key in the anim curve
    elif frame > curve_end_frame:
        in_tangent_type = anim_curve.getInTangentType(anim_curve.numKeys() - 1)
        out_tangent_type = anim_curve.getOutTangentType(anim_curve.numKeys() - 1)

        # Set the new key and the same tangents as the curve's last key
        attribute.setKey(time=frame, insert=True)
        anim_curve.setTangentTypes(
            [anim_curve.numKeys() - 1],
            inTangentType=in_tangent_type,
            outTangentType=out_tangent_type)

        # Put back the tangents to the previously last key, as these may have changed after adding the new key
        last_key = anim_curve.numKeys() - 2 if anim_curve.numKeys() > 1 else anim_curve.numKeys() - 1
        anim_curve.setTangentTypes(
            [last_key],
            inTangentType=in_tangent_type,
            outTangentType=out_tangent_type)
    # Need to add a key before the current first key in the anim curve
    elif frame < curve_start_frame:
        in_tangent_type = anim_curve.getInTangentType(0)
        out_tangent_type = anim_curve.getOutTangentType(0)

        # Set the new key and the same tangents as the curve's first key
        attribute.setKey(time=frame, insert=True)
        anim_curve.setTangentTypes(
            [0],
            inTangentType=in_tangent_type,
            outTangentType=out_tangent_type)

        # Put back the tangents to the previously first key, as these may have changed after adding the new key
        anim_curve.setTangentTypes(
            [1],
            inTangentType=in_tangent_type,
            outTangentType=out_tangent_type)


def remove_out_of_range_keys(start_frame, end_frame, anim_curves=None):
    """ Remove all the keyframes found on the given anim curves in the given
    time range.
    """
    anim_curves = anim_curves or pm.ls(type='animCurve')

    animated_attributes = {}
    for anim_curve in anim_curves:
        outputs = anim_curve.attr('output').outputs(plugs=True)
        if not outputs:
            continue
        animated_attributes.setdefault(anim_curve, outputs[0])

    # Set keyframes on first and end frames for every animated attribute
    for anim_curve, animated_attr in animated_attributes.items():
        if anim_curve.isReferenced():
            continue

        is_locked = animated_attr.isLocked()
        if is_locked:
            animated_attr.unlock()
        # It's quite important to the end frame first, because in the cases
        # where the key uses a stepped tangent, inserting a frame will
        # interpolate between the inserted frame's outTangent and the last
        # frame's inTangent.
        try:
            add_keyframe(end_frame, anim_curve, animated_attr)
            add_keyframe(start_frame, anim_curve, animated_attr)
        except Exception as e:
            logger.error('Failed to add key for anim_curve: %s attribute: %s' % (anim_curve, animated_attr))
            logger.error(e.message)
        if is_locked:
            animated_attr.lock()

    # Delete all keyframes out of frame range (these must belong to other shots)
    for anim_curve in anim_curves:
        # Detect which keys are outside of the frame range
        num_keys = anim_curve.numKeys()
        keys_to_remove = []

        for index in range(num_keys - 1, -1, -1):
            key_time = anim_curve.getTime(index)
            if start_frame <= key_time <= end_frame:
                # Set weights on the tangents to avoid having the curves c
                # hange once the other keys are deleted
                if key_time == start_frame:
                    anim_curve.setTangentsLocked(index, False)
                    anim_curve.setWeightsLocked(index, False)
                    anim_curve.setWeight(index, 1, True)
                elif key_time == end_frame:
                    anim_curve.setTangentsLocked(index, False)
                    anim_curve.setWeightsLocked(index, False)
                    anim_curve.setWeight(index, 1, False)
                continue
            keys_to_remove.append(index)

        # Delete the keys (key indexes will be deleted in reversed order to
        # avoid having the indexes changing)
        for index in keys_to_remove:
            anim_curve.remove(index)


def offset_keyframes(frame_offset, anim_curves=None):
    """
    Move the keyframes according to the animation offset to match the editorial
    cutin/cutout frame range

    :param int frame_offset:
    """
    # for human ik effectors, we found that the rotateX, Y, Z are bounded
    # together when we set keyframes on one of the animcurve, it would set the
    # other two as well so in the next process, we only have to shift keyframes
    # on one of them, or it would shift three times.
    bound_together_anim_curves = list()
    hik_nodes = cmds.ls(type='hikIKEffector')
    for hik_node in hik_nodes:
        curves = cmds.listConnections(hik_node, type='animCurve') or []
        bound_together_curves = [ac for ac in curves if 'rotate' in ac]
        bound_together_anim_curves.extend(bound_together_curves)

    # Move the keyframes according to the animation offset to match the
    # editorial cutin/cutout frame range
    anim_curves = anim_curves or [
        crv for crv in list_non_static_anim_curves()
        if not cmds.referenceQuery(crv, isNodeReferenced=True)]

    logger.info("Offsetting animation keys from %i animation curves..." % len(anim_curves))
    anim_curves_failed_on_moving = list()
    for anim_curve in anim_curves:
        if anim_curve in bound_together_anim_curves and 'rotateX' not in anim_curve:
            continue
        attribute = anim_curve + ".keyTimeValue"
        if cmds.getAttr(attribute, lock=True):
            cmds.setAttr(attribute, lock=False)
        try:
            cmds.keyframe(
                anim_curve, edit=True, relative=True, option='over',
                timeChange=frame_offset)
        except RuntimeError:
            anim_curves_failed_on_moving.append(anim_curve)

    if anim_curves_failed_on_moving:
        msg = "Failed to move animation curves: {}".format(anim_curves_failed_on_moving)
        logger.error(msg)
        raise RuntimeError

    logger.info("Offsetting animation keys from %i animation curves..." % len(anim_curves))


def find_last_keyframe_time(anim_curves=None):
    """
    Get the time of the last keyframe set in the scene.
    :param list[str]|None anim_curves:
    :rtype: int|None
    """
    anim_curves = anim_curves or list_non_static_anim_curves()
    keyframes = cmds.keyframe(anim_curves, query=True)
    if not keyframes:
        return
    return max(keyframes)


def remove_keys_before(anim_curves, time, to_preserve=None):
    """
    Removes keys on given anim curves which precede given time threshold.
    :param list[str] anim_curves: Maya animCurves node names.
    :param int|float time: Time limit to remove keys before.
    :param list[int|float]|None to_preserve: A list of time to not delete frames on.
    """
    to_preserve = to_preserve or []
    # convert to maya API object.
    anim_curves = node_names_to_mfn_anim_curves(anim_curves)
    for anim_curve in anim_curves:
        for i in range(anim_curve.numKeys - 1, -1, -1):
            key_time = anim_curve.input(i).value
            if key_time >= time or key_time in to_preserve:
                continue
            anim_curve.remove(i)


def trim_animation_curves(animation_curves, start_frame, end_frame):
    """
    Trim animation from given range.
    :param list[str] animation_curves: animation curves names
    :param float start_frame:
    :param float end_frame:
    """
    # Key handle boundaries.
    cmds.setKeyframe(
        animation_curves,
        time=start_frame,
        insert=True,
        inTangentType="linear",
        outTangentType="linear")
    cmds.setKeyframe(
        animation_curves,
        time=end_frame,
        insert=True,
        inTangentType="linear",
        outTangentType="linear")
    # Clear keyframes in range.
    time_range = start_frame + 1, end_frame - 1
    cmds.cutKey(animation_curves, clear=True, time=time_range)
    # Adapt animation.
    last_key = max(cmds.keyframe(animation_curves, query=True))
    offset = end_frame - start_frame - 1
    cmds.keyframe(
        animation_curves,
        edit=True,
        time=(end_frame, last_key),
        relative=True,
        timeChange=-offset,
        option='over')


def hold_animation_curves(
        animation_curves, frame, duration, offset_contiguous_animation=True):
    """
    Hold animation for a given duration.
    :param list[str] animation_curves: animation curves names
    :param float frame:
    :param float duration:
    :param bool offset_contiguous_animation:
        shift the animation before and after the scale to match the new timing.
    """
    # Keyframe and copy at given time to hold.
    cmds.setKeyframe(
        animation_curves,
        time=frame,
        inTangentType="linear",
        outTangentType="linear")
    cmds.copyKey(animation_curves, time=(frame, frame))

    if offset_contiguous_animation:
        # Shift the animation set after the held frame beyond the hold duration.
        last_key = max(cmds.keyframe(animation_curves, query=True))
        time_range = (frame + 1, last_key + 1)
        cmds.keyframe(
            animation_curves,
            edit=True,
            time=time_range,
            relative=True,
            timeChange=duration,
            option='over')
    else:
        # Clear the range to hold the animation.
        time_range = (frame + 1, frame + duration)
        cmds.cutKey(animation_curves, clear=True, time=time_range)

    time_range = (frame + duration, frame + duration)
    cmds.pasteKey(animation_curves, time=time_range)
    # flat the held animation.
    cmds.keyTangent(animation_curves, time=time_range, inTangentType='linear')
    time_range = (frame, frame)
    cmds.keyTangent(animation_curves, time=time_range, outTangentType='linear')


def retime_animation_curves(
        animation_curves, start_frame, end_frame, new_start_frame,
        new_end_frame, add_boundary_keyframes=False,
        offset_contiguous_animation=True, snap_keys=True):
    """
    Scale time range but also offset what's contiguous to keep continuity.
    :param list[str] animation_curves: animation curves names
    :param float start_frame:
    :param float end_frame:
    :param float new_start_frame:
    :param float new_end_frame:
    :param bool add_boundary_keyframes:
        add keyframes before and after retime to ensure de animation will not
        change out of the scaled range.
    :param bool offset_contiguous_animation:
        shift the animation before and after the scale to match the new timing.
    :param bool snap_key: round the new key frame time to the closest int.
    """
    # Define offsets happening before and after:
    end_offset = new_end_frame - end_frame
    start_offset = new_start_frame - start_frame

    # Define offset functions:
    keys = cmds.keyframe(animation_curves, query=True)
    max_keyframe = max(keys) + start_offset + end_offset
    offset_after_function = partial(
        cmds.keyframe, animation_curves, edit=True,
        t=(end_frame + 1, max_keyframe), relative=True,
        timeChange=end_offset, option='over')
    min_keyframe = min(keys) - end_offset - start_offset
    offset_before_function = partial(
        cmds.keyframe, animation_curves, edit=True,
        t=(min_keyframe, start_frame - 1), relative=True,
        timeChange=start_offset, option='over')

    if add_boundary_keyframes:
        cmds.setKeyframe(
            animation_curves, time=start_frame, inTangentType="linear",
            outTangentType="linear")
        cmds.setKeyframe(
            animation_curves, time=end_frame, inTangentType="linear",
            outTangentType="linear")

    # Offsets in case of expansion:
    if offset_contiguous_animation and end_offset > 0:
        offset_after_function()
    if offset_contiguous_animation and start_offset < 0:
        offset_before_function()

    # Retime/scale animation:
    cmds.scaleKey(
        animation_curves, time=(start_frame, end_frame),
        newStartTime=new_start_frame, newEndTime=new_end_frame)
    if snap_keys:
        cmds.snapKey(animation_curves, t=(new_start_frame, new_end_frame))

    # Offsets in case of shrinking:
    if offset_contiguous_animation and end_offset < 0:
        offset_after_function()
    if offset_contiguous_animation and start_offset > 0:
        offset_before_function()

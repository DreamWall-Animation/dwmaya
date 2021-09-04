__author__ = 'Lionel Brouyere, Olivier Evers'
__copyright__ = 'DreamWall'
__license__ = 'MIT'


from functools import partial
import maya.cmds as mc
import pymel.core as pm
import maya.api.OpenMaya as om2
import maya.api.OpenMayaAnim as oma2

from dwmaya.animation.curve import (
    list_non_static_anim_curves, node_names_to_mfn_anim_curves)


def delete_non_integer_keys():
    anim_curves = mc.keyframe(query=True, selected=True, name=True)
    if not anim_curves:
        times = mc.keyframe(query=True, timeChange=True)
        non_integer = list({t for t in times if t != int(t)})
        for time in non_integer:
            mc.cutKey(time=(time, time))
    else:
        curves_keyframes = {
            curve: mc.keyframe(curve, query=True, selected=True) for
            curve in anim_curves}
        for curve, times in curves_keyframes.items():
            non_integer = list({t for t in times if t != int(t)})
            for time in non_integer:
                mc.cutKey(curve, time=(time, time))


def find_last_keyframe_time(anim_curves=None):
    """
    Get the time of the last keyframe set in the scene.
    :param list[str]|None anim_curves:
    :rtype: int|None
    """
    anim_curves = anim_curves or list_non_static_anim_curves()
    keyframes = mc.keyframe(anim_curves, query=True)
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
    mc.setKeyframe(
        animation_curves,
        time=start_frame,
        insert=True,
        inTangentType="linear",
        outTangentType="linear")
    mc.setKeyframe(
        animation_curves,
        time=end_frame,
        insert=True,
        inTangentType="linear",
        outTangentType="linear")
    # Clear keyframes in range.
    time_range = start_frame + 1, end_frame - 1
    mc.cutKey(animation_curves, clear=True, time=time_range)
    # Adapt animation.
    last_key = max(mc.keyframe(animation_curves, query=True))
    offset = end_frame - start_frame - 1
    mc.keyframe(
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
    mc.setKeyframe(
        animation_curves,
        time=frame,
        inTangentType="linear",
        outTangentType="linear")
    mc.copyKey(animation_curves, time=(frame, frame))

    if offset_contiguous_animation:
        # Shift the animation set after the held frame beyond the hold duration.
        last_key = max(mc.keyframe(animation_curves, query=True))
        time_range = (frame + 1, last_key + 1)
        mc.keyframe(
            animation_curves,
            edit=True,
            time=time_range,
            relative=True,
            timeChange=duration,
            option='over')
    else:
        # Clear the range to hold the animation.
        time_range = (frame + 1, frame + duration)
        mc.cutKey(animation_curves, clear=True, time=time_range)

    time_range = (frame + duration, frame + duration)
    mc.pasteKey(animation_curves, time=time_range)
    # flat the held animation.
    mc.keyTangent(animation_curves, time=time_range, inTangentType='linear')
    time_range = (frame, frame)
    mc.keyTangent(animation_curves, time=time_range, outTangentType='linear')


def retime_animation_curves(
        animation_curves, start_frame, end_frame, new_start_frame,
        new_end_frame, add_boundary_keyframes=False,
        offset_contiguous_animation=True, snap_keys=True):
    """
    Scale time range but also offset what's contiguous to keep continuity.
    animation_curves: list[str]
    add_boundary_keyframes:
        add keyframes before and after retime to ensure de animation will not
        change out of the scaled range.
    :param bool offset_contiguous_animation:
        shift the animation before and after the scale to match the new timing.
    """
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

    if add_boundary_keyframes:
        mc.setKeyframe(
            animation_curves, time=start_frame, inTangentType="linear",
            outTangentType="linear")
        mc.setKeyframe(
            animation_curves, time=end_frame, inTangentType="linear",
            outTangentType="linear")

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

"""
This module contains a bunch of maya utils. Please do not make any pipeline
related business here. This area is pymel free. The functions are only using
the Maya node names as argument.
"""

import maya.cmds as mc
from dwmaya.__curve import ANIMATION_CURVE_TYPES, list_non_static_anim_curves
from dwmaya.keyframe import (
    retime_animation_curves, hold_animation_curves, trim_animation_curves)


def shift_shots(shots, offset, before=None, after=None):
    """
    Shift given shot in the maya timeline by the offset.
    :param list|str shots: representing maya shot nodes.
    :param float offset:
    :param float before:
        filter shots set before given time in the maya timeline.
    :param float after: filter shots set after given time in the maya timeline.
    """
    if not offset:
        return
    if before:
        shots = [s for s in shots if mc.getAttr(s + ".startFrame") < before]
    if after:
        shots = [s for s in shots if mc.getAttr(s + ".endFrame") > after]
    if offset > 0:
        shots = reversed(shots)

    for shot in shots:
        start_frame = mc.getAttr(shot + ".startFrame") + offset
        end_frame = mc.getAttr(shot + ".endFrame") + offset
        mc.shot(shot, edit=True, startTime=start_frame, endTime=end_frame)


def shift_shots_in_sequencer(shots, offset, before=None, after=None):
    """
    Shift given shot in the camera sequencer timeline by the offset.
    :param list|str shots: representing maya shot nodes.
    :param float offset:
    :param float before:
        filter shots set before given time in the sequencer timeline.
    :param float after:
        filter shots set after given time in the sequencer timeline.
    """
    if before:
        attr = ".sequenceStartFrame"
        shots = [s for s in shots if mc.getAttr(s + attr) < before]
    if after:
        attr = ".sequenceStartFrame"
        shots = [s for s in shots if mc.getAttr(s + attr) > after]
    if offset > 0:
        shots = reversed(shots)

    for shot in shots:
        value = mc.getAttr(shot + ".sequenceStartFrame") + offset
        mc.setAttr(shot + ".sequenceStartFrame", value)


def filter_locked_shots(shots):
    """
    Filter out all shots locked.
    :param list[str] shots: Maya shot nodes.
    :rtype: list[str]
    :return: Maya shot nodes.
    """
    return [s for s in shots if not mc.shot(s, query=True, lock=True)]


def filter_shots_from_time(shots=None, time=None, sequence_time=False):
    """
    Filter shots if their range contains the given time
    :param list[str] shots: Maya shot nodes. Use all shot if None.
    :param float time: Time to filter. Current time is used if None.
    :param bool sequence_time: Check camera sequencer time instead of timeline.
    :rtype: list[str]
    :return: Maya shot nodes.
    """
    time = time or mc.currentTime(query=True)
    shots = shots or mc.ls(type="shot")
    start_attribute = "sequenceStartFrame" if sequence_time else "startFrame"
    end_attribute = "sequenceEndFrame" if sequence_time else "endFrame"
    return [
        shot for shot in shots
        if mc.getAttr(shot + "." + start_attribute) < time <
        mc.getAttr(shot + "." + end_attribute)]


def filter_shots_from_range(
        shots=None, start_frame=None, end_frame=None, sequence_time=False):
    """
    Filter shots if their range contains any frame in the given one.
    :param list[str] shots: Maya shot nodes. Use all shot if None.
    :param float start_frame:
    :param float end_frame:
    :param bool sequence_time: Check camera sequencer time instead of timeline.
    :rtype: list[str]
    :return: Maya shot nodes.
    """
    start_frame = start_frame or mc.playbackOptions(min=True, query=True)
    end_frame = end_frame or mc.playbackOptions(max=True, query=True)
    shots = shots or mc.ls(type="shot")
    return list(set(
        shot for frame in range(int(start_frame), int(end_frame))
        for shot in filter_shots_from_time(shots, frame, sequence_time)))


def retime_shot(
        shot, new_start_frame, new_end_frame, scale_animation=True,
        snap_keys=True):
    """
    Retime the shot with given range and adapts all the shots around through
    the camera sequencer. If "scale_animtion" is true, animation will match the
    change.
    :param str shot: Representing maya shot node.
    :param float new_start_frame:
    :param float new_end_frame:
    :param bool scale_animation: Scale anim along the shot.
    :param bool snap_keys: Snap scaled keyframes during animation retime.
    """
    curves = mc.ls(type=ANIMATION_CURVE_TYPES)
    start_frame = mc.getAttr(shot + ".startFrame")
    end_frame = mc.getAttr(shot + ".endFrame")

    if scale_animation:
        retime_animation_curves(
            animation_curves=curves,
            start_frame=start_frame,
            end_frame=end_frame,
            new_start_frame=new_start_frame,
            new_end_frame=new_end_frame,
            add_boundary_keyframes=True,
            offset_contiguous_animation=True,
            snap_keys=snap_keys)

    sequencers = mc.listConnections(shot, type="sequencer")
    shots = [
        s for s in mc.listConnections(sequencers, type="shot") if s != shot]
    shots = filter_locked_shots(shots)
    # Maya automatically move shot's when two shot sequencer time ranges
    # overlaps. To avoids this issue, depend if the offset is positive or
    # negative we change the order of calls.
    sequencer_start = mc.getAttr(shot + ".sequenceStartFrame")
    offset = new_start_frame - start_frame
    # Shift the shots set before the retimed one.
    if offset > 0:
        mc.setAttr(shot + ".startFrame", new_start_frame)
        mc.setAttr(shot + ".sequenceStartFrame", sequencer_start + offset)
        shift_shots(shots, offset, before=start_frame)
        shift_shots_in_sequencer(shots, offset, before=sequencer_start)
    if offset < 0:
        shift_shots_in_sequencer(shots, offset, before=sequencer_start)
        shift_shots(shots, offset, before=start_frame)
        mc.setAttr(shot + ".sequenceStartFrame", sequencer_start + offset)
        mc.setAttr(shot + ".startFrame", new_start_frame)
    # Shit the shots set after the retimed one.
    offset = new_end_frame - end_frame
    if offset < 0:
        mc.setAttr(shot + ".endFrame", new_end_frame)
        shift_shots_in_sequencer(shots, offset, after=sequencer_start)
        shift_shots(shots, offset, after=end_frame)
    if offset > 0:
        shift_shots_in_sequencer(shots, offset, after=sequencer_start)
        shift_shots(shots, offset, after=end_frame)
        mc.setAttr(shot + ".endFrame", new_end_frame)


def retime_animation_in_shot_timerange(
        start_frame, end_frame, new_start_frame, new_end_frame,
        snap_keys=True):
    """
    Retime animation in a partial shot range and adapts the editing through the
    camera sequencer with those changes.
    :param float start_frame:
    :param float end_frame:
    :param float new_start_frame:
    :param float new_end_frame:
    :param bool snap_keys: snap scaled keyframes during animation retime.
    """
    shots = filter_shots_from_range(
        start_frame=start_frame, end_frame=end_frame)

    shots = filter_locked_shots(shots)
    if len(shots) > 1:
        message = (
            "{0} are detected during the range {1}, {2}.\n"
            "Retime through multiple shots not supported.".format(
                shots, start_frame, end_frame))
        raise ValueError(message)

    curves = mc.ls(type=ANIMATION_CURVE_TYPES)
    if curves:
        retime_animation_curves(
            animation_curves=curves,
            start_frame=start_frame,
            end_frame=end_frame,
            new_start_frame=new_start_frame,
            new_end_frame=new_end_frame,
            add_boundary_keyframes=True,
            offset_contiguous_animation=True,
            snap_keys=snap_keys)

    shot_start_frame = mc.getAttr(shots[0] + ".startFrame")
    shot_end_frame = mc.getAttr(shots[0] + ".endFrame")
    new_shot_start_frame = shot_start_frame + new_start_frame - start_frame
    new_shot_end_frame = shot_end_frame + new_end_frame - end_frame
    retime_shot(
        shots[0],
        new_shot_start_frame,
        new_shot_end_frame,
        scale_animation=False)


def split_shot(shot, frame, padding=0, name=None):
    """
    Split shot at given frame. Adapt animation and other shot
    if padding is set.
    :param str shot: representing maya shot node.
    :param float frame: split time.
    :param float padding: time range to add between the split in maya timeline.
    :rtype: str representing the maya shot node created.
    """
    start_frame = mc.getAttr(shot + ".startFrame")
    end_frame = mc.getAttr(shot + ".endFrame")
    if not start_frame < frame < end_frame:
        raise ValueError(f"{frame} not in shot {shot}")
    old_sequence_end_frame = mc.getAttr(shot + ".sequenceEndFrame")
    mc.setAttr(shot + ".endFrame", frame - 1)
    sequence_end_frame = mc.getAttr(shot + ".sequenceEndFrame")
    new_shot = mc.shot(
        name,
        shotName=mc.getAttr(shot + ".shotName"),
        startTime=frame + 1,
        endTime=end_frame + 1,
        sequenceStartTime=sequence_end_frame + 1,
        sequenceEndTime=old_sequence_end_frame)

    if not padding:
        return new_shot
    curves = mc.ls(type=ANIMATION_CURVE_TYPES)
    if curves:
        hold_animation_curves(curves, frame, padding)
    to_shift = filter_locked_shots(mc.ls(type="shot"))
    shift_shots(to_shift, padding, after=frame)
    return new_shot


def validate_frame_range(shots, start_time, end_time, sequence_time=False):
    """
    Verify if the given frame range is overlapping existing shots timeline
    range. If it is overlapping any shot tail, it redefine the start frame at
    the end of it. If it is overlapping any shot head, it will push back all
    shots (and animation) behind the range to ensure the space is free to
    insert new shot.
    :param list[str] shots: Maya shot node names.
    :param int start_time:
    :param int end_time:
    :param bool sequence_time:
        Operate on Camera Sequencer's timeline instead of Maya timeline.
    :rtype: tuple[int, int]
    :return: Free range.
    """
    start_attribute = "sequenceStartFrame" if sequence_time else "startFrame"
    end_attribute = "sequenceEndFrame" if sequence_time else "endFrame"
    length = end_time - start_time
    # Offset start_time to ensure it is not overlapping any shot tail.
    for shot in shots:
        shot_start = mc.getAttr(shot + "." + start_attribute)
        shot_end = mc.getAttr(shot + "." + end_attribute)
        # Ensure the time is not in the middle of a shot.
        if shot_start <= start_time <= shot_end:
            start_time = shot_end + 1
            break
    # Detect overlapping shots from heads.
    end_time = start_time + length
    overlapping_shots = filter_shots_from_range(
        shots=shots,
        start_frame=start_time,
        end_frame=end_time,
        sequence_time=sequence_time)
    if not overlapping_shots:
        return start_time, end_time
    # Push back overlapping shots.
    offset = max(
        end_time - mc.getAttr(shot + "." + start_attribute) + 1
        for shot in overlapping_shots)

    if sequence_time:
        # Operating on the camera sequencer timeline don't need to adapt
        # animation.
        shift_shots_in_sequencer(shots, offset, after=end_time - offset)
        return start_time, end_time

    shift_shots(shots, offset, after=end_time - offset)
    curves = mc.ls(type=ANIMATION_CURVE_TYPES)
    if curves:
        hold_animation_curves(curves, end_time - offset, offset)

    return start_time, end_time


def delete_shot_and_animation(
        shot, trim_shot_animation=True, shift_sequencer_times=False):
    """
    Delete a shot, trim his animation and shift the rest of the shots through
    the new timeline.
    :param str shot: Maya shot node name.
    :param bool trim_shot_animation:
        Remove and trim the maya timeline animation.
    :param bool shift_sequencer_times:
        Remove the gap let byt the removed shot in
        the camera sequencer.
    """
    start_frame = mc.getAttr(shot + ".startFrame")
    end_frame = mc.getAttr(shot + ".endFrame")
    sequencer_start_frame = mc.getAttr(shot + ".sequenceStartFrame")
    # Verifiy than any other shot is sharing the same maya timeline range.
    overlapping_shots = filter_shots_from_range(
        start_frame=start_frame, end_frame=end_frame)
    overlapping_shots = filter_locked_shots(overlapping_shots)
    if len(overlapping_shots) > 1 and trim_shot_animation:
        message = (
            "{0} are detected in the range {1}, {2}.\n"
            "Impossible to trim animation from deleted shot if other shots "
            "existing on the same frame range.".format(
                overlapping_shots, start_frame, end_frame))
        mc.warning(message)
        trim_shot_animation = False

    sequencers = mc.listConnections(shot, type="sequencer")
    shots = [
        s for s in mc.listConnections(sequencers, type="shot") if s != shot]
    shots = filter_locked_shots(shots)
    mc.delete(shot)

    if trim_shot_animation:
        trim_animation_curves(
            animation_curves=list_non_static_anim_curves(),
            start_frame=start_frame,
            end_frame=end_frame)

    offset = - (end_frame - start_frame + 1)
    if shift_sequencer_times:
        shift_shots_in_sequencer(shots, offset, after=sequencer_start_frame)
    if trim_shot_animation:
        shift_shots(shots, offset, after=end_frame)

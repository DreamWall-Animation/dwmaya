"""
Utils module about the camera sequencer tracks.
"""

import re
import maya.cmds as mc


def list_track_shots(track):
    """
    List all Maya shot node belonging to a sequencer track.
    :param int track:
    :rtype: list[str]
    """
    return [
        shot for shot in mc.ls(type="shot")
        if mc.getAttr(shot + ".track") == track]


def tracks_to_lists():
    """
    Convert tracks to lists of shot. Create a shot list by track.
    :rtype: list[list[str]]
    """
    shots = mc.ls(type="shot")
    tracks = [[]] * mc.shotTrack(query=True, numTracks=True)
    for shot in shots:
        # Tracks count start at 1 instead of 0.
        track = mc.getAttr(shot + ".track") - 1
        tracks[track].append(shot)
    return tracks


def find_track_with_free_range(start_frame, end_frame):
    """
    Find a track which doesn't contain any shot in the given frame range.
    If no track found, None is returned.
    :param float start_frame: Sequence start time.
    :param float end_frame: Sequence end time.
    :rtype: int|None
    """
    # Verifying shot range track by track.
    for i, track in enumerate(tracks_to_lists()):
        for shot in track:
            shot_start_frame = mc.getAttr(shot + ".sequenceStartFrame")
            shot_end_frame = mc.getAttr(shot + ".sequenceEndFrame")
            overlaps = (
                start_frame <= shot_start_frame <= end_frame or
                start_frame <= shot_end_frame <= end_frame)
            if overlaps:
                break
        # If the shot loop didn't detected a shot overlapping the given range,
        # the code will hit the "else" statement. 1 is add to the result to
        # compensate track count start at 1 instead of 0.
        else:
            return i + 1


def list_track_titles():
    """
    List all the track titles sorted by index.
    :rtype: list[str]
    """
    tracks = mc.shotTrack(query=True, numTracks=True)
    return [
        mc.shotTrack(track=i, query=True, title=True)
        for i in range(1, tracks + 1)]


def list_used_sequencer_track_indexes():
    """
    List all the camera sequencer tracks indexes containing at least one shot.
    :rtype: list[int]
    """
    return list(set(
        mc.shot(shot, track=True, query=True)
        for shot in mc.ls(type="shot")))


def remove_unused_sequencer_tracks():
    """
    For some reasons, mc.shotTrack(removeEmptyTracks=True) doesn't remove any
    track. This function do that.
    """
    used_tracks_indexes = list_used_sequencer_track_indexes()
    for i in range(mc.shotTrack(numTracks=True, query=True), 0, -1):
        if i in used_tracks_indexes:
            continue
        mc.shotTrack(removeTrack=i)


def append_sequencer_track(title=""):
    """
    Append a track at the end of the camera sequencer.
    :param str title: Name of the track.
    :rtype: int
    :return: Index of the created track.
    """
    index = mc.shotTrack(numTracks=True, query=True) + 1
    mc.shotTrack(insertTrack=index, title=title)
    return index


def list_shots_on_sequencer_track(index):
    """
    List the shots on a set on a given track index.
    :param int index: track index
    :rtype: list[str]
    :return: Maya shot node names.
    """
    shots = mc.ls(type="shot")
    return [shot for shot in shots if mc.getAttr(shot + ".track") == index]


def find_track_index(track_title):
    """
    Find the first track holding the given title.
    :param str track_title:
    :rtype: int
    """
    for i in range(mc.shotTrack(numTracks=True, query=True), 0, -1):
        if mc.shotTrack(track=i, query=True, title=True) == track_title:
            return i


def list_track_indexes_with_matching_title(regex):
    """
    List the existing tracks with a name matching to the given regex
    """
    return [
        i for i in range(mc.shotTrack(numTracks=True, query=True), 0, -1)
        if re.findall(regex, mc.shotTrack(track=i, query=True, title=True))]


def clear_sequencer_track_shots(index):
    """
    Remove all shots found on the corresponding to the given index
    :param int index:
    """
    shots = [
        shot for shot in mc.ls(type="shot")
        if mc.getAttr(shot + ".track") == index]
    for shot in shots:
        mc.shot(shot, edit=True, lock=False)
    mc.delete(shots)
    mc.shotTrack(removeTrack=index)

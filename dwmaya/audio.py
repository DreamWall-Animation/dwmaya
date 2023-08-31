import maya.cmds as mc
import maya.mel as mm


def get_playback_audio():
    time_slider = mm.eval('$tmpVar=$gPlayBackSlider')
    return mc.timeControl(time_slider, query=True, sound=True)


def set_playback_audio(audio_node):
    time_slider = mm.eval('$tmpVar=$gPlayBackSlider')
    mc.timeControl(time_slider, edit=True, sound=audio_node, displaySound=True)
    mc.timeControl(time_slider, edit=True, forceRefresh=True)

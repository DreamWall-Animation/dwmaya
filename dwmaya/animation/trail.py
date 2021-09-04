__author__ = 'Lionel Brouyere, Olivier Evers'
__copyright__ = 'DreamWall'
__license__ = 'MIT'


import maya.cmds as mc


def motion_to_nurbscurve(transform):
    start = mc.playbackOptions(query=True, min=True)
    end = mc.playbackOptions(query=True, max=True)
    points = []
    for frame in range(int(start), int(end) + 1):
        mc.currentTime(frame)
        points.append(mc.getAttr(transform + '.translate')[0])
    mc.curve(point=points)

__author__ = 'Olivier Evers'
__copyright__ = 'DreamWall'
__license__ = 'MIT'


import os
import maya.cmds as mc


def get_scene_path(shortName=False):
    path = mc.file(query=True, sceneName=True, shortName=shortName)
    if not path:
        # This is slower but sometimes path is empty for some reason.
        path = mc.file(query=True, list=True)[0]
        if shortName:
            path = os.path.basename(path)
    return path

__author__ = 'Olivier Evers'
__copyright__ = 'DreamWall'
__license__ = 'MIT'


import os
import platform
import subprocess
import maya.cmds as mc


def get_scene_path(shortName=False):
    path = mc.file(query=True, sceneName=True, shortName=shortName)
    if not path:
        # This is slower but sometimes path is empty for some reason.
        path = mc.file(query=True, list=True)[0]
        if shortName:
            path = os.path.basename(path)
    return path


def open_file_with_default_app(path):
    system = platform.system()
    if system == 'Windows':
        os.startfile(path.replace('/', '\\'))
    elif system == 'Linux':
        subprocess.Popen(['xdg-open', path])
    elif system == 'Mac':
        subprocess.Popen(['open', path])


def save_if_modified_prompt(dont_save_returns=True):
    if not mc.file(query=True, modified=True):
        return True

    current_scene_path = get_scene_path()
    save, dont_save, cancel = 'Save', "Don't save", 'Cancel'
    choice = mc.confirmDialog(
        title='Save changes',
        message='Save changes to %s ?' % current_scene_path,
        button=[save, dont_save, cancel])

    if choice == cancel:
        return False
    elif choice == dont_save:
        return dont_save_returns
    elif choice == save:
        mc.file(save=True)
        return True

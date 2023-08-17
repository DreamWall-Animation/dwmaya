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


def open_directory(path):
    system = platform.system()
    if system == 'Windows':
        if os.path.isdir(path):
            subprocess.Popen(["explorer", os.path.normpath(path)])
        else:
            subprocess.Popen(["explorer", "/select,", os.path.normpath(path)])
    else:
        if not os.path.isdir(path):
            path = os.path.dirname(path)
        subprocess.Popen(['xdg-open', os.path.normpath(path)])


def open_file_with_default_app(path):
    if os.path.isdir(path):
        open_directory(path)
    system = platform.system()
    if system == 'Windows':
        os.startfile(path.replace('/', '\\'))
    elif system == 'Linux':
        subprocess.Popen(['xdg-open', path])
    elif system == 'Mac':
        subprocess.Popen(['open', path])


def save_as():
    name = mc.fileDialog2(dialogStyle=2, fileFilter='Maya Ascii (*.ma)')
    if not name:
        return False
    mc.file(rename=name)
    mc.file(save=True, type='mayaAscii')
    return True


def save_if_modified_prompt(dont_save_returns=True):
    if not mc.file(query=True, modified=True):
        return True

    current_scene_path = mc.file(query=True, sceneName=True, shortName=False)
    save, dont_save, cancel = 'Save', "Don't save", 'Cancel'
    choice = mc.confirmDialog(
        title='Save changes',
        message='Save changes to %s ?' % get_scene_path(),
        button=[save, dont_save, cancel])

    if choice == cancel:
        return False
    elif choice == dont_save:
        return dont_save_returns
    elif choice == save:
        if not current_scene_path:
            return save_as()
        mc.file(save=True)
        return True

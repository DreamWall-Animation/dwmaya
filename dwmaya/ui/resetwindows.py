import maya.cmds as mc


def reset_windows_positions():
    for window in mc.lsUI(windows=True):
        mc.window(window, edit=True, topLeftCorner=[0, 0])

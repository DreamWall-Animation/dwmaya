import maya.cmds as mc


def reset_windows_positions(skip=None):
    skip = skip or ['MayaWindow']
    for window in mc.lsUI(windows=True):
        if window in skip:
            continue
        mc.window(window, edit=True, topLeftCorner=[0, 0])

__author__ = 'Olivier Evers'
__copyright__ = 'DreamWall'
__license__ = 'MIT'


from contextlib import contextmanager

import maya.OpenMaya as om
import maya.OpenMayaUI as omui
import maya.cmds as mc

from dwmaya.attributes import get_attr, set_attr, unlock_attr
from dwmaya.hierarchy import get_shape_and_transform


def find_active_camera():
    view = omui.M3dView.active3dView()
    camera = om.MDagPath()
    view.getCamera(camera)
    return camera.partialPathName()


def set_all_cameras_not_renderable():
    for cam in mc.ls(type='camera'):
        if get_attr(cam, 'renderable') is False:
            continue
        try:
            unlock_attr(cam, 'renderable')
            set_attr(cam, 'renderable', False)
        except BaseException:
            print('Could not set %s.renderable to False' % cam)


def transfer_camera_framing(source_cam, target_cam, fov=True):
    source_cam, source_transform = get_shape_and_transform(source_cam)
    target_cam, target_transform = get_shape_and_transform(target_cam)
    # Copy transform:
    world_matrix = mc.xform(
        source_transform, query=True, matrix=True, worldSpace=True)
    mc.xform(target_transform, matrix=world_matrix)
    # Copy camera stuff:
    if fov:
        attributes = [
            'horizontalFilmAperture',
            'verticalFilmAperture',
            'focalLength',
            'filmFit',
        ]
        for attr in attributes:
            value = get_attr(source_cam, attr)
            set_attr(target_cam, attr, value)


def set_single_camera_renderable(cam):
    set_all_cameras_not_renderable()
    mc.setAttr(cam + '.renderable', True)
    # test
    renderable_cameras = [
        c for c in mc.ls(type='camera', recursive=True) if
        mc.getAttr(c + '.renderable')]
    if len(renderable_cameras) != 1 or renderable_cameras[0] != cam:
        print(renderable_cameras)
        raise ValueError(f'{cam} should be renderable and no other camera.')


def reset_pan_and_zoom(camera):
    mc.setAttr(f'{camera}.verticalPan', 0)
    mc.setAttr(f'{camera}.horizontalPan', 0)
    mc.setAttr(f'{camera}.zoom', 1)


@contextmanager
def disable_panzoom_ctx(camera):
    initial_panzoom_state = mc.getAttr(f'{camera}.panZoomEnabled')
    mc.setAttr(f'{camera}.panZoomEnabled', False)
    try:
        yield
    finally:
        mc.setAttr(f'{camera}.panZoomEnabled', initial_panzoom_state)

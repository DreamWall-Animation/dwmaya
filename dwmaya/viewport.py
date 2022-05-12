__author__ = 'Olivier Evers'
__copyright__ = 'DreamWall'
__license__ = 'MIT'


import time
from functools import partial
from contextlib import contextmanager

import maya.cmds as mc

from dwmaya.ui.qt import get_screen_size
from dwmaya.attributes import get_attr, set_attr


DEFAULT_MODEL_EDITOR_KWARGS = dict(
    displayAppearance='smoothShaded',
    shadows=False,
    displayTextures=True,

    fogging=False,
    fogColor=[1, 1, 1, 1],
    fogDensity=1,
    fogStart=0,
    fogEnd=100,
    fogMode='linear',
    fogSource='fragment',

    useDefaultMaterial=False,
    nurbsSurfaces=True,
    subdivSurfaces=True,
    polymeshes=True,
    planes=True,
    imagePlane=True,
    textures=True,
    pluginShapes=True,
    selectionHiliteDisplay=False,
    nurbsCurves=False,
    controlVertices=False,
    hulls=False,
    lights=False,
    cameras=False,
    ikHandles=False,
    deformers=False,
    dynamics=False,
    particleInstancers=False,
    fluids=False,
    hairSystems=False,
    follicles=False,
    nCloths=False,
    nParticles=False,
    nRigids=False,
    dynamicConstraints=False,
    locators=False,
    dimensions=False,
    pivots=False,
    handles=False,
    strokes=False,
    motionTrails=False,
    clipGhosts=False,
    greasePencils=False,
    joints=False,
    wireframeOnShaded=False)

AO_SETTINGS = dict(
    ssaoRadius=24,
    ssaoFilterRadius=24,
    ssaoAmount=1.1,
    ssaoEnable=1,
    ssaoSamples=32,
    multiSampleEnable=1)


def create_tearoff_viewport(
        camera, title=None, size=None, model_editor_kwargs=None, position=None):
    tearoff_window = mc.window(title=title)

    _model_editor_kwargs = model_editor_kwargs or dict()
    model_editor_kwargs = DEFAULT_MODEL_EDITOR_KWARGS.copy()
    model_editor_kwargs.update(_model_editor_kwargs)
    model_editor_kwargs['camera'] = camera

    if size is None:
        try:
            w, h = get_screen_size()
            size = w * .6, h * .6
        except BaseException:
            size = [1280, 720]
    mc.window(tearoff_window, edit=True, widthHeight=size)

    if position is None:
        position = [w / 10, h / 10]
    mc.window(tearoff_window, edit=True, topLeftCorner=position)

    mc.paneLayout()
    panel = mc.modelPanel()
    mc.timePort(height=30, snap=True)
    mc.showWindow(tearoff_window)
    editor = mc.modelPanel(panel, query=True, modelEditor=True)
    mc.modelEditor(editor, edit=True, **model_editor_kwargs)
    mc.refresh()
    mc.modelEditor(editor, edit=True, activeView=True)
    return editor, panel, tearoff_window


def delete_tearoff_viewport(window):
    if mc.window(window, query=True, exists=True):
        mc.evalDeferred(partial(mc.deleteUI, window))


@contextmanager
def temp_tearoff_viewport(camera, model_editor_kwargs=None, size=None):
    editor, panel, window = create_tearoff_viewport(
        camera, title='%s_tearoff' % camera,
        model_editor_kwargs=model_editor_kwargs)
    try:
        yield editor, panel, window
    finally:
        delete_tearoff_viewport(window)


@contextmanager
def temp_ambient_occlusion(occlusion_settings=None):
    occlusion_settings = occlusion_settings or AO_SETTINGS
    # Setup VP2 settings
    old_values = dict()
    vp_node = 'hardwareRenderingGlobals'
    for attr, value in occlusion_settings.items():
        old_values[attr] = get_attr(vp_node, attr)
        set_attr(vp_node, attr, value)
    try:
        yield None
    finally:
        # Reset VP2
        for attr, value in occlusion_settings.items():
            value = old_values[attr]
            set_attr(vp_node, attr, value)


if __name__ == '__main__':
    model_editor_kwargs = dict(useDefaultMaterial=True, displayLights='all')
    with temp_tearoff_viewport(
            'persp', model_editor_kwargs=model_editor_kwargs) as (
            editor, panel, window):
        print(editor)
        time.sleep(1)

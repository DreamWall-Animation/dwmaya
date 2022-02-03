__author__ = 'Olivier Evers'
__copyright__ = 'DreamWall'
__license__ = 'MIT'


import os
import time
import glob
import shutil
import tempfile
import subprocess

import maya.cmds as mc
import maya.mel as mm
import maya.OpenMaya as om

from dwmaya.attributes import set_attr
from dwmaya.camera import set_single_camera_renderable
from dwmaya.viewport import (
    DEFAULT_MODEL_EDITOR_KWARGS, temp_tearoff_viewport, temp_ambient_occlusion,
    dummy_context)


def get_sound_node():
    sound_node = mc.timeControl('timeControl1', query=True, sound=True)
    if not sound_node:
        sound_nodes = mc.ls(type='audio')
        if len(sound_nodes) != 1:
            return
        sound_node = sound_nodes[0]
    return sound_node


def get_sound_path():
    sound_node = get_sound_node()
    if not sound_node:
        return
    path = os.path.expandvars(mc.getAttr(sound_node + '.filename'))
    if os.path.exists(path):
        return path
    else:
        mc.warning('Sound path does not exist !')


def get_sound_offset():
    sound_node = get_sound_node()
    if not sound_node:
        return
    return mc.getAttr(sound_node + '.offset')


def playblast(
        camera, maya_playblast_kwargs, model_editor_kwargs=None,
        ambient_occlusion=True, generate_uvtiles_previews=False):
    """
    @maya_playblast_kwargs: maya.cmds.playblast kwargs

    @model_editor_kwargs: maya.cmds.modelEditor kwargs

    @ambient_occlusion can be True for default settings OR it can be passed a
        dict with the attributes values for the "hardwareRenderingGlobals" node
            - ssaoRadius
            - ssaoFilterRadius
            - ssaoAmount
            - ssaoEnable
            - ssaoSamples
            - multiSampleEnable
    """
    model_editor_kwargs = model_editor_kwargs or dict()
    try:
        start = maya_playblast_kwargs['startTime']
        end = maya_playblast_kwargs['endTime']
        frames_str = '%i -> %i' % (start, end)
    except KeyError:
        frames_str = str(maya_playblast_kwargs['frame'])

    if mc.about(batch=True):
        # BATCH
        set_single_camera_renderable(camera)
        set_attr('hardwareRenderingGlobals', 'textureMaxResolution', 256)
        mc.colorManagementPrefs(edit=True, outputTransformEnabled=True)
        lights_display_layer = mc.createDisplayLayer(mc.ls(lights=True))
        set_attr(lights_display_layer, 'visibility', False)
        result = None
        try:
            # # disable textures (default = 4):
            # set_attr('hardwareRenderingGlobals', 'renderMode', 1)
            t1 = time.time()

            def force_eval(mtime, _):
                # Without dgdirty some animation were not updated in mayapy
                mc.dgdirty(allPlugs=True)

            callback = om.MDGMessage.addTimeChangeCallback(force_eval)
            try:
                mc.evaluationManager(mode='off')
                result = mc.playblast(**maya_playblast_kwargs)
            finally:
                om.MEventMessage.removeCallback(callback)
            t2 = time.time()
            print('Playblast took %.2f seconds to render' % (t2 - t1))
        finally:
            print(lights_display_layer)
            mc.delete(lights_display_layer)
            mc.colorManagementPrefs(
                edit=True, outputTransformEnabled=False)
        return result
    else:
        # GUI
        full_model_editor_kwargs = DEFAULT_MODEL_EDITOR_KWARGS.copy()
        full_model_editor_kwargs.update(model_editor_kwargs)
        if ambient_occlusion:
            occlusion_manager = temp_ambient_occlusion
            if isinstance(ambient_occlusion, dict):
                occlusion_settings = ambient_occlusion
            else:
                occlusion_settings = None
        else:
            occlusion_manager = dummy_context
        with temp_tearoff_viewport(camera, full_model_editor_kwargs):
            with occlusion_manager(occlusion_settings):
                print('Playblasting %s.' % frames_str)
                if generate_uvtiles_previews:
                    # reset needed when opening + playblasting multiple scenes:
                    mc.ogs(reset=True)
                    mm.eval('generateAllUvTilePreviews;')
                return mc.playblast(**maya_playblast_kwargs)


def _preroll_postroll_checker(
        output_path, first_frame, last_frame, width, height, camera,
        temp_directory):
    # Playblast the four images:
    frames = [first_frame - 1, first_frame, last_frame, last_frame + 1]
    maya_playblast_kwargs = dict(
        format='image', viewer=False, compression='jpg', forceOverwrite=True,
        quality=100, showOrnaments=False, percent=100,
        width=width, height=height, frame=frames)
    path = playblast(camera, maya_playblast_kwargs)
    images = sorted(glob.glob(path.replace('####', '*')))
    # Compose single image:
    # blend two images:
    average_image = temp_directory + '/average.png'
    image_format = '%ix%i' % (width * 2, height)
    subprocess.call([
        'oiiotool',
        images[0], '--mulc', '0.5',
        images[1], '--mulc', '0.5', '--add',
        images[2], '--mulc', '0.5', '--origin', '+%s+0' % width, '--add',
        images[3], '--mulc', '0.5', '--origin', '+%s+0' % width, '--add',
        '--fullsize', image_format, '-o', average_image])
    # highlight extra frame in red:
    substraction_image = temp_directory + '/substraction.exr'
    subprocess.call([
        'oiiotool',
        images[0],
        images[1], '--sub',
        images[2], '--origin', '+%s+0' % width, '--add',
        images[3], '--origin', '+%s+0' % width, '--sub',
        '--fullsize', image_format, '-o', substraction_image])
    # add red highlight to average:
    cmd = ' '.join([
        'oiiotool',
        substraction_image, '--clamp:max=0', '--mulc', '-1,-1,-1',
        '--chsum:weight=.3,.3,.3', '--ch', '0,0,0', '--mulc', '1,0,0',
        average_image, '--add',
        '-o', output_path])
    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc.communicate()
    if proc.returncode != 0:
        print(out)
        raise Exception(err)


def preroll_postroll_checker(
        output_path, first_frame, last_frame, width, height, camera,
        remove_tmp_images=True):
    temp_directory = (
        tempfile.gettempdir().replace('\\', '/') + '/dw_prepostroll')
    if os.path.exists(temp_directory):
        shutil.rmtree(temp_directory)
    os.makedirs(temp_directory)
    try:
        _preroll_postroll_checker(
            output_path, first_frame, last_frame, width, height, camera,
            temp_directory)
    finally:
        if remove_tmp_images:
            if os.path.exists(temp_directory):
                shutil.rmtree(temp_directory)

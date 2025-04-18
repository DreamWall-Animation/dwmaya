__author__ = 'Olivier Evers'
__copyright__ = 'DreamWall'
__license__ = 'MIT'


import os
import re
import glob
from contextlib import contextmanager

import maya.cmds as mc
import maya.mel as mm

from dwmaya.history import list_full_history
from dwmaya.namespace import strip_namespaces


UDIM_EXTENSION_PATTERN = r'^.*\.\d{4}\.\w{2,4}$'
UDIM_UV_PATTERN = r'_u<u>_v<v>'
UDIM_UV_RE_PATTERN = r'_u\d_v\d'
EXCLUDES_FROM_SHADING_HISTORY = [
    'defaultColorMgtGlobals'
]


def get_materials_assignments():
    """
    Build a dictionnary listing the object by shading engine.
    """
    assignments = {
        sg: mc.ls(mc.sets(sg, query=True), long=True)
        for sg in mc.ls(type='shadingEngine')}
    return {sg: nodes for sg, nodes in assignments.items() if nodes}


def get_shape_shading_engine(shape):
    shading_engines = mc.listConnections(shape, type='shadingEngine')
    if not shading_engines:
        return None
    return shading_engines[0]


def list_shape_textures(shape):
    shading_engine = get_shape_shading_engine(shape)
    if not shading_engine:
        return []
    return list_texture_filepaths([shading_engine])


def get_transform_childs_materials_assignments(
        transform, relative_path=False, preserve_namespaces=False,
        component_assignments=False):
    """
    Build a dictionnary listing the objects by shading engine. Objects are
    filtered from a transform parent. The path are stored relatively from that
    parent.

    This outliner state:
        group1|group2|group3|mesh1  --> connected to --> shadingEngine1
        group1|group2|mesh2  --> connected to --> shadingEngine1
        mesh3  --> connected to --> shadingEngine1

    This command
        get_transform_childs_materials_assignments('group2', relative_path=True)

    Should result this:
        {shadingEngine1: ["group3|mesh1", "mesh2"]}
    Note that "mesh3" is stripped out the result.
    """
    content = mc.listRelatives(
        transform,
        allDescendents=True,
        type='mesh',
        fullPath=True)

    if content is None:
        return {}

    def _mesh_or_parent(mesh):
        if not component_assignments or not re.search(r'.*\..*\[.*\]', mesh):
            return mesh
        return mc.listRelatives(mesh, parent=True, fullPath=True)[0]

    assignments = {
        sg: [mesh for mesh in meshes if _mesh_or_parent(mesh) in content]
        for sg, meshes in get_materials_assignments().items()}

    if relative_path:
        assignments = {
            sg: [m.split(transform)[-1] for m in meshes if m in content]
            for sg, meshes in assignments.items()}

    if not preserve_namespaces:
        assignments = {
            strip_namespaces(sg): [strip_namespaces(m) for m in meshes]
            for sg, meshes in assignments.items()}

    return {k: v for k, v in assignments.items() if v}


def apply_materials_assignment_to_transfom_childs(
        assignments, transform, skip_missing_objects=True,
        geometry_namespace=None, materials_namespace=None):
    """
    Apply a shading assignment generated from function
    get_transform_childs_materials_assignments()
    """
    for shading_engine, meshes in assignments.items():
        if geometry_namespace:
            meshes = ['|'.join([
                ':'.join(
                    (geometry_namespace.strip(':'), element.split(':')[-1]))
                for element in mesh.split('|')][1:])
                for mesh in meshes]
        if materials_namespace:
            shading_engine = f'{materials_namespace}:{shading_engine}'
        if not mc.objExists(shading_engine):
            print(f'Warning: Missing shading engine: {shading_engine}')
            continue
        meshes = [
            '|{0}|{1}'.format(transform.strip('|'), m.strip('|'))
            for m in meshes]
        if skip_missing_objects:
            meshes = [m for m in meshes if mc.objExists(m)]
        assign_material(shading_engine, meshes)


def assign_material(shading_engine, objects):
    mc.sets(objects, forceElement=shading_engine)


def create_material(shader_type):
    shader = mc.shadingNode(shader_type, asShader=True)
    shadingEngine = shader + 'SG'
    shadingEngine = mc.sets(
        name=shadingEngine, renderable=True, noSurfaceShader=True, empty=True)
    mc.connectAttr(shader + '.outColor', shadingEngine + '.surfaceShader')
    return shader, shadingEngine


def clear_materials_assignments(shading_engines):
    for shading_engine in shading_engines:
        assigned_objects = mc.sets(shading_engine, query=True)
        mc.sets(assigned_objects, remove=shading_engine)


@contextmanager
def temp_default_material():
    """Does not work for objects without any material"""
    assignments = get_materials_assignments()
    try:
        for shading_engine, nodes in assignments.items():
            assign_material('initialShadingGroup', nodes)
        yield
    finally:
        for shading_engine, nodes in assignments.items():
            assign_material(shading_engine, nodes)


def set_texture(attribute, texture_path, file_output='outColor'):
    file_node = mc.shadingNode('file', asTexture=True, isColorManaged=True)
    p2t_node = mc.shadingNode('place2dTexture', asUtility=True)
    mm.eval('''
        connectAttr -f {p2t}.coverage {fn}.coverage;
        connectAttr -f {p2t}.translateFrame {fn}.translateFrame;
        connectAttr -f {p2t}.rotateFrame {fn}.rotateFrame;
        connectAttr -f {p2t}.mirrorU {fn}.mirrorU;
        connectAttr -f {p2t}.mirrorV {fn}.mirrorV;
        connectAttr -f {p2t}.stagger {fn}.stagger;
        connectAttr -f {p2t}.wrapU {fn}.wrapU;
        connectAttr -f {p2t}.wrapV {fn}.wrapV;
        connectAttr -f {p2t}.repeatUV {fn}.repeatUV;
        connectAttr -f {p2t}.offset {fn}.offset;
        connectAttr -f {p2t}.rotateUV {fn}.rotateUV;
        connectAttr -f {p2t}.noiseUV {fn}.noiseUV;
        connectAttr -f {p2t}.vertexUvOne {fn}.vertexUvOne;
        connectAttr -f {p2t}.vertexUvTwo {fn}.vertexUvTwo;
        connectAttr -f {p2t}.vertexUvThree {fn}.vertexUvThree;
        connectAttr -f {p2t}.vertexCameraOne {fn}.vertexCameraOne;
        connectAttr {p2t}.outUV {fn}.uv;
        connectAttr {p2t}.outUvFilterSize {fn}.uvFilterSize;
        connectAttr -force {fn}.{output} {attribute};'''.format(
            p2t=p2t_node, fn=file_node, attribute=attribute,
            output=file_output))
    mc.setAttr(file_node + '.fileTextureName', texture_path, type='string')
    return file_node, p2t_node


def list_texture_attributes(shading_engines):
    inputs = mc.listConnections(shading_engines, destination=False)
    shaders = mc.ls(inputs, materials=True)
    history = [
        n for n in list_full_history(shaders)
        if n not in EXCLUDES_FROM_SHADING_HISTORY]
    texture_attributes = []
    for node in history:
        texture_attributes.extend([
            '{0}.{1}'.format(node, a)
            for a in mc.listAttr(node, usedAsFilename=True) or []])
    return texture_attributes


def get_udim_filepaths(path):
    """
    If filepath looks like UDIM pattern, return all paths matching this
    pattern.
    """
    udim_paths = []
    extension = os.path.splitext(path)[-1]
    path_start_length = None
    if re.compile(UDIM_EXTENSION_PATTERN).match(path):
        path_start_length = len(path) - len(
            re.match(r'^(.*?)(\d{4})', path[::-1]).group(0)[::-1])
    elif UDIM_UV_PATTERN in path.lower():
        path_start_length = path.lower().index(UDIM_UV_PATTERN)
    elif re.compile('.*' + UDIM_UV_RE_PATTERN + '.*').match(path):
        path_start_length = len(re.split(UDIM_UV_RE_PATTERN, path)[0])
    if path_start_length:
        pattern = path[:path_start_length] + '*' + extension
        for match_file in glob.glob(os.path.expandvars(pattern)):
            # We preserve original folder name to keep environment variables in
            # the path.
            match_file = (
                f'{os.path.dirname(path)}/{os.path.basename(match_file)}')
            udim_paths.append(match_file.replace('\\', '/'))
    return udim_paths


def list_texture_filepaths(shading_engines):
    textures = []
    for attribute in list_texture_attributes(shading_engines):
        try:
            filepath = mc.getAttr(attribute)
            if filepath:
                udim_paths = get_udim_filepaths(filepath)
                if udim_paths:
                    textures.extend(udim_paths)
                else:
                    textures.append(filepath)
        except ValueError:
            if '.' not in attribute:
                raise
            # This attribute is ghost and does not exists. Skip it.
    return sorted(list(set(textures)))


def replace_textures_root_directory(shading_engines, root):
    for attribute in list_texture_attributes(shading_engines):
        try:
            filepath = mc.getAttr(attribute)
            if not filepath:
                continue
            new_filepath = (
                '{0}/{1}'.format(root, os.path.basename(filepath)))
            mc.setAttr(attribute, new_filepath, type='string')
        except ValueError:
            if '.' not in attribute:
                raise
            # This attribute is ghost and does not exists. Skip it.


def replace_texture(src, dst, shading_engines):
    for attribute in list_texture_attributes(shading_engines):
        try:
            filepath = mc.getAttr(attribute)
            if not filepath:
                continue
            if filepath == src:
                mc.setAttr(attribute, dst, type='string')
        except ValueError:
            if '.' not in attribute:
                raise
            # This attribute is ghost and does not exists. Skip it.


def project_texture(file_node, camera=None):
    target_attr = mc.listConnections(file_node + '.outColor', plugs=True)[0]
    projection = mc.shadingNode('projection', asTexture=True)
    mc.connectAttr(file_node + '.outColor', projection + '.image')
    mc.connectAttr(projection + '.outColor', target_attr, force=True)
    if camera:
        mc.setAttr(projection + '.projType', 8)  # camera projection
        mc.connectAttr(camera + '.message', projection + '.linkedCamera')
    else:
        place3d_texture = mc.shadingNode('place3dTexture', asUtility=True)
        mc.connectAttr(place3d_texture + '.wim[0]', projection + '.pm')
    return projection


def assign_shading_per_faces(shading_engine, mesh_transform):
    mc.sets(mesh_transform, remove=shading_engine)
    face_count = mc.polyEvaluate(mesh_transform, face=True)
    faces = f'{mesh_transform}.f[0:{face_count - 1}]'
    mc.sets(faces, forceElement=shading_engine)

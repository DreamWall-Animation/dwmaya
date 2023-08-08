__author__ = 'Olivier Evers'
__copyright__ = 'DreamWall'
__license__ = 'MIT'


import maya.cmds as mc
import maya.mel as mm
from dwmaya.namespace import strip_namespaces


def get_shading_assignments():
    """
    Build a dictionnary listing the object by shading engine.
    """
    assignments = {
        sg: mc.ls(mc.sets(sg, query=True), long=True)
        for sg in mc.ls(type='shadingEngine')}
    return {sg: nodes for sg, nodes in assignments.items() if nodes}


def get_transform_childs_shading_assignment(
        transform, relative_path=False, preserve_namespaces=False):
    """
    Build a dictionnary listing the objects by shading engine. Objects are
    filtered from a transform parent. The path are stored relatively from that
    parent.

    This outliner state:
        group1|group2|group3|mesh1  --> connected to --> shadingEngine1
        group1|group2|mesh2  --> connected to --> shadingEngine1
        mesh3  --> connected to --> shadingEngine1

    This command
        get_transform_childs_shading_assignment('group2', relative_path=True)

    Should result this:
        {shadingEngine1: ["group3|mesh1", "mesh2"]}
    Note that "mesh3" is stripped out the result.
    """
    content = mc.listRelatives(
        transform,
        allDescendents=True,
        type='mesh',
        fullPath=True)

    assignments = {
        sg: [mesh for mesh in meshes if mesh in content]
        for sg, meshes in get_shading_assignments().items()}

    if relative_path:
        assignments = {
            sg: [m.split(transform)[-1] for m in meshes if m in content]
            for sg, meshes in assignments.items()}

    if not preserve_namespaces:
        assignments = {
            sg: [strip_namespaces(m) for m in meshes]
            for sg, meshes in assignments.items()}

    return {k: v for k, v in assignments.items() if v}


def apply_shading_assignment_to_transfom_childs(
        assignments, transform, namespace=None):
    """
    Apply a shading assignment generated from function
    get_transform_childs_shading_assignment()
    """
    for shading_engine, meshes in assignments.items():
        if namespace:
            meshes = ['|'.join([
                ':'.join((namespace.strip(':'), element.split(':')[-1]))
                for element in mesh.split('|')])
                for mesh in meshes]

        meshes = [
            '|{0}|{1}'.format(transform.strip('|'), m.strip('|'))
            for m in meshes]
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


def set_texture(attribute, texture_path):
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
        connectAttr -force {fn}.outColor {attribute};'''.format(
            p2t=p2t_node, fn=file_node, attribute=attribute))
    mc.setAttr(file_node + '.fileTextureName', texture_path, type='string')
    return file_node


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

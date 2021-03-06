__author__ = 'Olivier Evers'
__copyright__ = 'DreamWall'
__license__ = 'MIT'


import maya.cmds as mc
import maya.mel as mm


def get_shading_assignments():
    assignments = {}
    for sg in mc.ls(type='shadingEngine'):
        assignments[sg] = mc.sets(sg, query=True)
    return assignments


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

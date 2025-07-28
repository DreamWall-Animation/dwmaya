import os
import maya.cmds as mc
import maya.mel as mm
from dwmaya.plugins import ensure_plugin_loaded
from dwmaya.shading import assign_material
from functools import partial


@ensure_plugin_loaded('pgYetiMaya')
def import_texture_to_yeti_node(filepath, yeti_node):
    existing_textures = list_yeti_node_all_texture_files(yeti_node)
    if filepath in existing_textures:
        return mc.warning('Texture already existing in yeti node network')

    texture_node = mc.pgYetiGraph(yeti_node, create=True, type='texture')
    mc.pgYetiGraph(
        yeti_node,
        node=texture_node,
        param='file_name',
        setParamValueString=filepath)
    mc.pgYetiGraph(
        yeti_node,
        node=texture_node,
        param='vCoord',
        setParamValueExpr="floor($t)+1-($t-floor($t))")
    mc.pgYetiGraph(
        yeti_node,
        node=texture_node,
        rename=os.path.splitext(os.path.basename(filepath))[0])


@ensure_plugin_loaded('pgYetiMaya')
def list_yeti_node_all_texture_files(yeti_node):
    texture_nodes = mc.pgYetiGraph(yeti_node, listNodes=True, type='texture')
    filepaths = set()
    for texture_node in texture_nodes:
        filepath = mc.pgYetiGraph(
            yeti_node,
            node=texture_node,
            param='file_name',
            getParamValue=True)
        if not filepath:
            continue
        filepaths.add(filepath)
    return filepaths


@ensure_plugin_loaded('pgYetiMaya')
def replace_yeti_node_texture(src, dst, yeti_node):
    texture_nodes = mc.pgYetiGraph(yeti_node, listNodes=True, type='texture')
    for texture_node in texture_nodes:
        filepath = mc.pgYetiGraph(
            yeti_node,
            node=texture_node,
            param='file_name',
            getParamValue=True)
        if filepath == src:
            filepath = mc.pgYetiGraph(
                yeti_node,
                node=texture_node,
                param='file_name',
                setParamValueString=dst)


@ensure_plugin_loaded('pgYetiMaya')
def create_yeti_node(name=None):
    """
    Reimplementation of pgYetiCreate to be able to set a name
    """
    name = name or "pgYetiMaya"
    transform = mc.createNode('transform', name=name)
    yeti_node = mc.createNode('pgYetiMaya', name=name + 'Shape', parent=transform)
    mc.connectAttr('time1.outTime', f'{yeti_node}.currentTime')
    mc.setAttr(f'{yeti_node}.visibleInReflections', True)
    mc.setAttr(f'{yeti_node}.visibleInRefractions', True)
    assign_material('initialShadingGroup', yeti_node)
    return transform, yeti_node


@ensure_plugin_loaded('pgYetiMaya')
def create_yeti_on_meshes(meshes=None):
    """
    Need to reimplement pgYetiCreateOnMesh to be able to get the result

    """
    meshes = meshes or mc.ls(
        selection=True, dag=True, noIntermediate=True, type='mesh')
    meshes = mc.ls(meshes, noIntermediate=True, type='mesh', shortNames=True)
    if not meshes:
        return mc.error('No mesh selected or specified')
    yeti_nodes = []
    parents = []
    for mesh in meshes:
        name = mc.listRelatives(mesh, parent=True)[0]
        name = f'pgYeti_{name}'
        transform, yeti_node = create_yeti_node(name=name)
        yeti_nodes.append(yeti_node)
        parents.append(transform)
        mm.eval(f'pgYetiAddGeometry("{mesh}", "{yeti_node}")')
        mc.evalDeferred(partial(import_mesh_to_yeti_graph, yeti_node, mesh))
    return parents, yeti_nodes


def import_mesh_to_yeti_graph(yeti_node, mesh):
    import_node = mc.pgYetiGraph(yeti_node, create=True, type='import')
    mc.pgYetiGraph(
        yeti_node, node=import_node,
        param='geometry',
        setParamValueString=mesh)
    mc.pgYetiGraph(
        yeti_node,
        node=import_node,
        rename=f'imp_{mesh}')


def list_all_yeti_nodes_children(parent):
    yeti_nodes = mc.listRelatives(
        parent, allDescendents=True, type='pgYetiMaya', fullPath=True) or []
    grooms = mc.listRelatives(
        parent, allDescendents=True, type='pgYetiGroom', fullPath=True) or []
    yeti_nodes.extend(grooms)
    return yeti_nodes


if __name__ == '__main__':
    nodes = create_yeti_on_meshes()
    print(nodes)

import maya.cmds as mc
import maya.mel as mm
from dwmaya.plugins import ensure_plugin_loaded
from dwmaya.shading import assign_material
from functools import partial


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
        mc.evalDeferred(partial(create_import_node, yeti_node, mesh))
    return parents, yeti_nodes


def create_import_node(yeti_node, mesh):
    import_node = mc.pgYetiGraph(yeti_node, create=True, type='import')
    mc.pgYetiGraph(
        yeti_node, node=import_node,
        param='geometry',
        setParamValueString=mesh)
    mc.pgYetiGraph(
        yeti_node,
        node=import_node,
        rename=f'imp_{mesh}')


if __name__ == '__main__':
    nodes = create_yeti_on_meshes()
    print(nodes)

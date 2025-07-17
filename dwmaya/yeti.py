import maya.cmds as mc
import maya.mel as mm
from dwmaya.plugins import ensure_plugin_loaded
from dwmaya.shading import assign_material


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
    return yeti_node


@ensure_plugin_loaded('pgYetiMaya')
def create_yeti_on_meshes(meshes=None):
    """
    Need to reimplement pgYetiCreateOnMesh to be able to get the result

    """
    meshes = meshes or mc.ls(
        selection=True, dag=True, noIntermediate=True, type='mesh')
    meshes = mc.ls(meshes, noIntermediate=True, type='mesh')
    if not meshes:
        return mc.error('No mesh selected or specified')
    yeti_nodes = []
    for mesh in meshes:
        name = mc.listRelatives(mesh, parent=True)[0]
        name = f'pgYeti_{name}'
        yeti_node = create_yeti_node(name=name)
        yeti_nodes.append(yeti_node)
        mm.eval(f'pgYetiAddGeometry("{mesh}", "{yeti_node}")')
    return yeti_nodes


if __name__ == '__main__':
    nodes = create_yeti_on_meshes()
    print(nodes)

__author__ = 'Lionel Brouyere'
__copyright__ = not 'DreamWall'
__license__ = 'MIT'


import re
import maya.cmds as mc
import maya.api.OpenMaya as om2
import maya.OpenMaya as om
from dwmaya.undo import single_undo_chunk


FINALING_MESH_NAME = '{transform}_finaling_copy_{id}'
STATIC_COPY_NAME = '{transform}_static_copy_{id}'
INMESH_COPY_NAME = '{transform}_inmesh_copy_{id}'
OUTMESH_COPY_NAME = '{transform}_outmesh_copy_{id}'
OUTMESH_PARTIAL_COPY_NAME = '{transform}_outmesh_partial_copy_{id}'


def selected_meshes():
    return mc.ls(
        selection=True,
        type='mesh',
        dag=True,
        shapes=True,
        noIntermediate=True)


def rename_mesh(mesh, template, reference_name=None):
    transform = mc.listRelatives(mesh, parent=True)[0]
    dependnode = om2.MSelectionList().add(mesh).getDependNode(0)
    dagnode = om2.MFnDagNode(dependnode)
    reference_name = reference_name or transform

    id_ = 0
    name = template.format(transform=reference_name, id=str(id_).zfill(3))
    if not mc.objExists(name):
        mc.rename(transform, name)
        return dagnode.name()

    if '{id}' not in template:
        template += '_{id}'

    while mc.objExists(name):
        mc.refresh()
        id_ += 1
        name = template.format(transform=reference_name, id=str(id_).zfill(3))

    dependnode = om2.MSelectionList().add(mesh).getDependNode(0)
    dagnode = om2.MFnDagNode(dependnode)
    mc.rename(transform, name)
    return dagnode.name()


def create_finalling_intermediate(mesh):
    input_connections = mc.listConnections(mesh + '.inMesh', plugs=True)
    if not input_connections:
        msg = (
            'the given mesh doesn\'t have input connection and can\'t'
            ' be used to create finalling intermediate')
        return mc.warning(msg)
    intermediate_mesh = mc.createNode('mesh')
    mc.connectAttr(input_connections[0], intermediate_mesh + '.inMesh')
    blendshape = mc.blendShape(intermediate_mesh, mesh)
    mc.blendShape(blendshape, edit=True, weight=(0, 1.0))
    original_transform = mc.listRelatives(mesh, parent=True)[0]
    intermediate_mesh = rename_mesh(
        intermediate_mesh, FINALING_MESH_NAME,
        reference_name=original_transform)
    return intermediate_mesh


def create_finalling_copies(meshes=None):
    meshes = meshes or selected_meshes()
    copies = []
    for mesh in meshes:
        copy = create_finalling_intermediate(mesh)
        copies.append(copy)
    return copies


def create_inmesh_copies(meshes=None):
    meshes = meshes or selected_meshes()
    copies = []
    for mesh in meshes:
        copy = mc.createNode('mesh')
        outs = mc.listConnections(mesh + '.inMesh', plugs=True)
        if not outs:
            continue
        mc.connectAttr(outs[0], copy + '.inMesh')
        transform = mc.listRelatives(mesh, parent=True)[0]
        copy = rename_mesh(copy, INMESH_COPY_NAME, reference_name=transform)
        copies.append(copy)
    return copies


def create_outmesh_copies(meshes=None):
    meshes = meshes or selected_meshes()
    copies = []
    for mesh in meshes:
        copy = mc.createNode('mesh')
        mc.connectAttr(mesh + '.outMesh', copy + '.inMesh')
        transform = mc.listRelatives(mesh, parent=True)[0]
        copy = rename_mesh(copy, OUTMESH_COPY_NAME, reference_name=transform)
        copies.append(copy)
    return copies


def create_clean_copies(meshes=None, suffix=STATIC_COPY_NAME):
    meshes = meshes or selected_meshes()
    copies = []
    for mesh in meshes:
        copy = mc.createNode('mesh')
        mc.connectAttr(mesh + '.outMesh', copy + '.inMesh')
        mc.refresh()
        mc.disconnectAttr(mesh + '.outMesh', copy + '.inMesh')
        transform = mc.listRelatives(mesh, parent=True)[0]
        copy = rename_mesh(copy, suffix, reference_name=transform)
        copies.append(copy)
    return copies


def create_intermediate_after(mesh):
    output_connections = mc.connectionInfo(mesh + ".worldMesh[0]", dfs=True)
    if not output_connections:
        msg = (
            'the given mesh doesn\'t have input connection and can\'t'
            ' be used to create finalling intermediate')
        return mc.warning(msg)
    intermediate_mesh = create_clean_copies([mesh])[0]
    blendshape = mc.blendShape(mesh, intermediate_mesh)
    mc.blendShape(blendshape, edit=True, weight=(0, 1.0))
    mc.connectAttr(intermediate_mesh + ".outMesh", output_connections[0], f=True)
    original_transform = mc.listRelatives(mesh, parent=True)[0]
    intermediate_mesh = rename_mesh(
        intermediate_mesh,
        FINALING_MESH_NAME,
        reference_name=original_transform)
    return intermediate_mesh


def create_partial_outmesh_copy():
    faces = mc.filterExpand(selectionMask=34)
    if not is_faces_from_unique_mesh(faces):
        raise ValueError('Please, select faces from unique mesh !')
    mesh = faces[0].split('.')[0]
    selected_ids = list_faces_ids(faces)
    copy = create_outmesh_copies(meshes=[mesh])
    copy_transform = mc.listRelatives(copy, parent=True)[0]
    copy_faces = ["{}.f[{}]".format(copy_transform, id) for id in selected_ids]
    mc.select(copy_faces)
    mc.InvertSelection()
    mc.delete()
    return copy


def list_faces_ids(faces):
    """
    This function analyse the faces name and extract the id.
    e.i. for and element as "polyMesh.f[35]", it extract 35.
    This return a list of int.
    """
    ids = []
    for face in faces:
        facename = re.findall(".f\[\d*\]", face)[0]
        id_ = int([elt for elt in re.findall(r"\d*", facename) if elt][0])
        ids.append(int(id_))
    return ids


def is_faces_from_unique_mesh(faces):
    if not faces:
        return False
    return len(set([face.split('.')[-2] for face in faces])) == 1


def mesh_has_ngones(mesh):
    selection_list = om.MSelectionList()
    selection_list.add(mesh)
    dagpath = om.MDagPath()
    selection_list.getDagPath(0, dagpath)

    meshIt = om.MItMeshPolygon(dagpath)
    while not meshIt.isDone():
        if meshIt.polygonVertexCount() > 4:
            return True
        meshIt.next()
    return False


def mesh_has_triangle(mesh):
    selection_list = om.MSelectionList()
    selection_list.add(mesh)
    dagpath = om.MDagPath()
    selection_list.getDagPath(0, dagpath)

    meshIt = om.MItMeshPolygon(dagpath)
    while not meshIt.isDone():
        if meshIt.polygonVertexCount() < 4:
            return True
        meshIt.next()
    return False


def detect_triangles(mesh):
    selection_list = om.MSelectionList()
    selection_list.add(mesh)
    dagpath = om.MDagPath()
    selection_list.getDagPath(0, dagpath)

    poly_it = om.MItMeshPolygon(dagpath)
    triangles = []
    while not poly_it.isDone():
        if poly_it.polygonVertexCount() < 4:
            return triangles.append(poly_it.index())
        poly_it.next()
    return triangles


def reset_mesh_vertices(mesh):
    for i in range(mc.polyEvaluate(mesh, vertex=True)):
        mc.setAttr(f'{mesh}.pnts[{i}]', 0, 0, 0)


def check_vertices_are_freezed(meshes, treshold=0):
    for mesh in meshes:
        for i in range(mc.polyEvaluate(mesh, vertex=True)):
            attr = f'{mesh}.pnts[{i}]'
            if max(mc.getAttr(attr)[0]) > treshold:
                return False
    return True


@single_undo_chunk()
def reset_meshes_vertices(meshes, treshold=0.0001):
    # Check if any vertex is above treshold first:
    if not check_vertices_are_freezed(meshes, treshold):
        return False
    # Set values to 0
    for mesh in meshes:
        reset_mesh_vertices(mesh)
    return True


def create_uv_mesh(mesh):
    """
    Create a physical mesh with vertex positions corresponding to UV
    cordinates.
    """
    dagpath = om2.MSelectionList().add(mesh).getDagPath(0)
    mesh_it = om2.MItMeshVertex(dagpath)

    copy = create_clean_copies([mesh])[0]
    dagpath = om2.MSelectionList().add(copy).getDagPath(0)
    mfn_mesh = om2.MFnMesh(dagpath)

    while not mesh_it.isDone():
        u, v = mesh_it.getUV()
        point = om2.MPoint(u, 0, v)
        mfn_mesh.setPoint(mesh_it.index(), point)
        mesh_it.next()
    return copy

__author__ = 'Olivier Evers'
__copyright__ = 'DreamWall'
__license__ = 'MIT'


import os
import tempfile
import subprocess

from pxr import Usd, UsdGeom, Gf
import maya.cmds as mc


CREATE_NO_WINDOW = 0x08000000
USDVIEW_PATH = os.path.join(os.environ['USD_LOCATION'], 'bin', 'usdview')


def export_geo_usd(path):
    mc.loadPlugin('mayaUsdPlugin', quiet=True)
    options = [
        'exportUVs=1',
        'exportSkels=none',
        'exportSkin=none',
        'exportBlendShapes=0',
        'exportColorSets=1',
        'defaultMeshScheme=none',
        'defaultUSDFormat=usdc',
        'eulerFilter=0',
        'staticSingleSample=0',
        'parentScope=',
        'exportDisplayColor=1',
        'shadingMode=useRegistry',
        'convertMaterialsTo=UsdPreviewSurface',
        'exportInstances=0',
        'exportVisibility=0',
        'mergeTransformAndShape=0',
        'stripNamespaces=1',
    ]
    options = ';'.join(options)
    mc.file(
        path, typ='USD Export', force=True, exportSelected=True,
        options=options)


def set_transform(prim, position, rotation, scale):
    UsdGeom.XformCommonAPI(prim).SetTranslate(position)
    UsdGeom.XformCommonAPI(prim).SetRotate(rotation)
    UsdGeom.XformCommonAPI(prim).SetScale(scale)


def set_matrix(prim, matrix):
    matrix = Gf.Matrix4d(*matrix)
    xform = UsdGeom.Xformable(prim)
    transform = xform.MakeMatrixXform()
    transform.Set(matrix)


def reference_usd(
        stage, usd_path, scene_path, instancable=True,
        transform=None, matrix=None):
    prim = stage.DefinePrim(scene_path)
    prim.SetInstanceable(instancable)
    prim.GetReferences().AddReference(usd_path)
    if matrix:
        set_matrix(prim, matrix)
    if transform:
        set_transform(prim, *transform)
    return prim


def create_usd_hierarchy(stage, parent_path, data):
    for ref in data:
        scene_path = f'{parent_path}/{ref["name"]}'
        reference_usd(
            stage=stage,
            usd_path=ref['path'],
            scene_path=scene_path,
            instancable=not ref.get('children'),
            transform=ref.get('transform'),
            matrix=ref.get('matrix'),
        )
        children = ref.get('children', [])
        if children:
            create_usd_hierarchy(stage, scene_path, children)


def create_assembly(hierarchy, assembly_path=None):
    """
    @hierarchy:
        [dict(name, usd, transform, children=...), dict(...)]
    """
    if assembly_path is None:
        assembly_path = f'{tempfile.gettempdir()}/temp.usdc'
        if os.path.exists(assembly_path):
            os.remove(assembly_path)

    stage = Usd.Stage.CreateInMemory()
    create_usd_hierarchy(stage, '', hierarchy)
    stage.GetRootLayer().Export(assembly_path)
    return assembly_path


def create_maya_usd_proxy(usd_path):
    # Create node to display it in Maya:
    import maya.cmds as mc
    proxy_shape = mc.createNode('mayaUsdProxyShape')
    mc.setAttr(proxy_shape + '.filePath', usd_path, type='string')
    mc.connectAttr('time1.outTime', proxy_shape + '.time')


def show_in_usdview(usd_path):
    python37_path = 'C:/Program Files/Python37'
    if python37_path not in os.environ['PATH']:
        os.environ['PATH'] += f';{python37_path}'
    subprocess.Popen(
        ['mayapy', USDVIEW_PATH, usd_path],
        creationflags=CREATE_NO_WINDOW)


if __name__ == '__main__':
    hierarchy = [
        dict(
            name='hello',
            path='cube.usdc',
            matrix=[
                1.0, 0.0, 0.0, 0.0, 0.0, 0.7071067811865475,
                0.7071067811865476, 0.0, 0.0, -0.7071067811865476,
                0.7071067811865475, 0.0, 2.0, 0.0, -1.0, 1.0],
        ),
        dict(
            name='hello2',
            path='cube.usdc',
            children=[
                dict(
                    name='hello3',
                    path='cube.usdc',
                    transform=[[4, 5, 6], [40, 5, -20], [1, 2, 0.5]],
                ),
            ],
        ),
    ]
    path = create_assembly(hierarchy, 'test.usda')
    show_in_usdview(path)

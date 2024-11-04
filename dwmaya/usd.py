__author__ = 'Olivier Evers'
__copyright__ = 'DreamWall'
__license__ = 'MIT'


import os
import tempfile
import subprocess

from pxr import Usd, UsdGeom, Gf, Sdf
import maya.cmds as mc
from dwmaya.plugins import ensure_plugin_loaded
from dwmaya.selection import preserve_selection

CREATE_NO_WINDOW = 0x08000000
USDVIEW_PATH = os.path.join(os.environ['USD_LOCATION'], 'bin', 'usdview')


@preserve_selection
@ensure_plugin_loaded('mayaUsdPlugin')
def export_geo_usd(path, roots=None):
    """
    roots: list of nodes, if None, the entire scene is exported.
    """
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
    kwargs = dict(
        defaultExtensions=False,
        typ='USD Export',
        force=True,
        options=options)
    if roots:
        mc.select(roots)
        kwargs['exportSelected'] = True
    mc.file(path, **kwargs)


@ensure_plugin_loaded('mayaUsdPlugin')
def import_geo_usd(usd_path, parent):
    content = mc.file(
        usd_path, type="USD Import", i=True, returnNewNodes=True)
    transforms = mc.ls(content, type='transform')
    roots = [t for t in transforms if not mc.listRelatives(t, parent=True)]
    if not roots:
        raise ValueError(f'Usd file is empty: {usd_path}')
    return mc.parent(roots, parent)


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
        transform=None, matrix=None, custom_attributes=None):
    prim = stage.DefinePrim(scene_path, 'Xform')
    prim.SetInstanceable(instancable)
    if usd_path:
        prim.GetReferences().AddReference(usd_path)
    if matrix:
        set_matrix(prim, matrix)
    if transform:
        set_transform(prim, *transform)
    if custom_attributes:
        for attribute_name, (data_type, value) in custom_attributes.items():
            attribute = prim.CreateAttribute(attribute_name, data_type)
            attribute.Set(value)
    return prim


def create_usd_hierarchy(stage, parent_path, data):
    for ref in data:
        scene_path = f'{parent_path}/{ref["name"]}'
        reference_usd(
            stage=stage,
            usd_path=ref.get('path'),
            scene_path=scene_path,
            instancable=not ref.get('children'),
            transform=ref.get('transform'),
            matrix=ref.get('matrix'),
            custom_attributes=ref.get('custom_attributes'),
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


@ensure_plugin_loaded('mayaUsdPlugin')
def create_maya_usd_proxy(usd_path, parent=None):
    """Create node to display it in Maya."""
    proxy_shape = mc.createNode('mayaUsdProxyShape')
    mc.setAttr(proxy_shape + '.filePath', usd_path, type='string')
    mc.connectAttr('time1.outTime', proxy_shape + '.time')
    if parent:
        usd_proxy_transform = mc.listRelatives(proxy_shape, parent=True)[0]
        mc.parent(usd_proxy_transform, parent)
    return proxy_shape


def show_in_usdview(usd_path):
    python37_path = 'C:/Program Files/Python37'
    if python37_path not in os.environ['PATH']:
        os.environ['PATH'] += f';{python37_path}'
    subprocess.Popen(
        ['mayapy', USDVIEW_PATH, usd_path],
        creationflags=CREATE_NO_WINDOW)


if __name__ == '__main__':
    test_dir = f'{os.environ["USERPROFILE"]}'
    cube_path = f'{test_dir}/cube.usdc'
    hierarchy = [
        dict(
            name='hello',
            path=cube_path,
            matrix=[
                1.0, 0.0, 0.0, 0.0, 0.0, 0.7071067811865475,
                0.7071067811865476, 0.0, 0.0, -0.7071067811865476,
                0.7071067811865475, 0.0, 2.0, 0.0, -1.0, 1.0],
        ),
        dict(
            name='hello2',
            # path=cube_path,
            transform=[[4, 5, 6], [40, 5, -20], [1, 2, 0.5]],
            children=[
                dict(
                    name='hello3',
                    path=cube_path,
                    transform=[[4, 5, 6], [40, 5, -20], [1, 2, 0.5]],
                    custom_attributes=dict(
                        my_float_attr=(Sdf.ValueTypeNames.Float, 3.141592),
                        me_string_attr=(Sdf.ValueTypeNames.String, ':)'),
                    )
                ),
            ],
        ),
    ]
    path = create_assembly(hierarchy, f'{test_dir}/test.usda')
    show_in_usdview(path)

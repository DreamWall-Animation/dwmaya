import os
from pathlib import Path

import maya.cmds as mc
import maya.mel as mm


IDENTITY = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]


def export_nodes_to_alembic(start, end, roots, filepath, frame_sample=1):
    mc.loadPlugin('AbcExport', quiet=True)
    # Seems that alembic command does not support windows-like paths. Need to
    # ensure the path is unix-like.
    filepath = filepath.replace('\\', '/')
    roots = ' '.join([f'-root {root}' for root in roots])
    command = (
        f'AbcExport -j "-frameRange {start} {end}'
        f' -frameRelativeSample -{frame_sample} '
        '-frameRelativeSample 0 -worldSpace -ro'
        ' -uvWrite -writeColorSets -writeFaceSets -writeUVSets'
        f' -dataFormat ogawa {roots} -file {filepath}";')
    mm.eval(command)


def convert_gpu_caches_to_meshes(delete_caches=True):
    """
    Replace gpuCache nodes by importing the alembic files.
    When same file is used multiple times OR instanced, it will instance the
    same shape.
    """
    mc.loadPlugin('AbcImport', quiet=True)
    paths = {os.path.basename(p): p for p in mc.file(query=True, list=True)}
    gpu_caches = mc.ls(type='gpuCache')
    for gpu_cache in gpu_caches:
        # Find path (also finds paths resolved by Maya)
        alembic_path = paths[
            os.path.basename(mc.getAttr(f'{gpu_cache}.cacheFileName'))]
        # Import
        group = Path(alembic_path).stem
        if not mc.ls(group):  # check if alembic was not imported yet
            nodes = mc.file(alembic_path, i=True, returnNewNodes=True)
            nodes = mc.ls(nodes, long=True, dag=True)
            # Group
            top_level = min(n.count('|') for n in nodes)
            top_nodes = [n for n in nodes if n.count('|') == top_level]
            group = mc.group(top_nodes, name=group)
        # Instance
        transforms = mc.listRelatives(gpu_cache, allParents=True, path=True)
        for i, transform in enumerate(transforms):
            instance = group if i == 0 else mc.instance(group, lf=True)
            mc.parent(instance, transform)
            mc.xform(instance, m=IDENTITY)
        # Delete gpu cache shape
        if delete_caches:
            mc.delete(gpu_cache)

import maya.mel as mm
from dwmaya.plugins import ensure_plugin_loaded


@ensure_plugin_loaded('AbcExport')
def export_nodes_to_alembic(start, end, roots, filepath, frame_sample=1):
    roots = ' '.join([f'-root {root}' for root in roots])
    command = (
        f'AbcExport -j "-frameRange {start} {end}'
        f' -frameRelativeSample -{frame_sample} '
        '-frameRelativeSample 0 -worldSpace -ro'
        ' -uvWrite -writeColorSets -writeFaceSets -writeUVSets -autoSubd'
        f' -dataFormat ogawa {roots} -file {filepath}";')
    mm.eval(command)

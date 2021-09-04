__author__ = 'Lionel Brouyere, Olivier Evers'
__copyright__ = 'DreamWall'
__license__ = 'MIT'


import json
import maya.cmds as mc

from dwmaya.namespace import build_versioned_namespace
from dwmaya.animation.curve import get_anim_curves


def export_animation(export_path):
    if not export_path.endswith('.ma'):
        export_path += '.ma'
    # 1: export maya file with anim layers, curves, and blend nodes:
    blend_types = [
        t for t in mc.listNodeTypes('animation') if t.startswith('animBlend')]
    blenders = mc.ls(type=blend_types)
    curves = get_anim_curves()
    layers = mc.ls(type='animLayer')
    mc.select(blenders + curves + layers)
    mc.file(
        export_path, typ='mayaAscii', force=True, prompt=False,
        exportSelectedStrict=True, constructionHistory=False)
    # 2: export list of connections to recover
    source_nodes = curves + blenders
    connections = []
    targets = set(
        mc.listConnections(source_nodes, destination=True, plugs=True))
    for target in targets:
        target_node = target.split('.')[0]
        if target_node in source_nodes:
            # Connections between each other are already in export maya file
            continue
        node_type = mc.nodeType(target_node)
        if node_type == 'animLayer' or 'EditorInfo' in node_type:
            continue
        for source in mc.listConnections(target, source=True, plugs=True):
            source_node = source.split('.')[0]
            if source_node not in source_nodes:
                continue
            connection = (source, target)
            if connection not in connections:
                connections.append(connection)
    with open(export_path + '.json', 'w') as f:
        json.dump(connections, f, indent=4)


def import_animation(import_path):
    if not import_path.endswith('.ma'):
        import_path += '.ma'
    # Remove pre-existing layers if any
    layers = mc.ls(type='animLayer')
    if layers:
        mc.delete(layers)
    # Import Maya file with layers and curves
    namespace = build_versioned_namespace()
    mc.file(import_path, i=True, namespace=namespace)
    # Reconnect nodes
    with open(import_path + '.json', 'r') as f:
        connections = json.load(f)
    failed_reconnections = []
    for source, target in connections:
        try:
            mc.connectAttr(namespace + ':' + source, target, force=True)
        except RuntimeError:
            failed_reconnections.append((source, target))
    # Remove namespace for animLayers
    for layer in mc.ls(namespace + ':*', type='animLayer'):
        mc.rename(layer, layer.split(':')[-1])
    return failed_reconnections

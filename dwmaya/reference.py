__author__ = 'Olivier Evers'
__copyright__ = 'DreamWall'
__license__ = 'MIT'


import maya.cmds as mc
from dwmaya.hierarchy import get_closest_to_root


def add_reference(path, namespace, parent=None):
    mc.file(path, reference=True, prompt=False, namespace=namespace)


def remove_reference(refnode):
    path = mc.referenceQuery(refnode, filename=True)
    mc.file(path, removeReference=True, force=True)


def import_reference(refnode):
    path = mc.referenceQuery(refnode, filename=True)
    mc.file(path, importReference=True, force=True)


def get_reference_root_nodes(refnode):
    try:
        nodes = mc.referenceQuery(refnode, nodes=True)
    except RuntimeError:
        return []
    return get_closest_to_root(nodes)


def get_references():
    refs = []
    for ref in mc.ls(type="reference"):
        if "sharedReferenceNode" in ref or "_UNKNOWN_REF_NODE_" in ref:
            continue
        try:
            mc.referenceQuery(ref, filename=True)
        except RuntimeError:
            continue
        refs.append(ref)
    return refs


def remove_reference_number(path):
    if path.endswith('}'):
        path = path.split('{')[:-1]
        path = '{'.join(path)
    return path


def get_reference_path(ref):
    path = mc.referenceQuery(ref, filename=True, unresolvedName=True)
    return remove_reference_number(path)


def list_references_paths():
    return [mc.referenceQuery(ref, filename=True) for ref in get_references()]

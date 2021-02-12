__author__ = 'Olivier Evers'
__copyright__ = 'DreamWall'
__license__ = 'MIT'


import os
import glob

import maya.cmds as mc

from dwmaya.hierarchy import get_closest_to_root
from dwmaya.qt import chose_from_list_prompt


def add_reference(path, namespace, parent=None):
    mc.file(path, reference=True, prompt=False, namespace=namespace)


def remove_reference(refnode):
    path = mc.referenceQuery(refnode, filename=True)
    mc.file(path, removeReference=True, force=True)


def import_reference(refnode):
    path = mc.referenceQuery(refnode, filename=True)
    mc.file(path, importReference=True, force=True)


def get_reference_nodes(refnode):
    try:
        return mc.referenceQuery(refnode, nodes=True, dagPath=True)
    except RuntimeError:
        return []


def get_reference_root_nodes(refnode):
    return get_closest_to_root(get_reference_nodes(refnode))


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


def chose_reference_from_scene_prompt():
    choices = []
    for ref in get_references():
        path = mc.referenceQuery(ref, filename=True)
        namespace = mc.file(path, query=True, namespace=True)
        name = os.path.basename(remove_reference_number(path))
        label = '%s: %s' % (namespace, name)
        choices.append((label, ref))
    return chose_from_list_prompt(choices)


def change_reference_path_prompt():
    """
    This will only look for files in the same directory as current file but
    is easily modified.
    """
    ref_node = chose_reference_from_scene_prompt()
    if not ref_node:
        return
    ref_path = mc.referenceQuery(ref_node, filename=True, unresolvedName=True)
    ref_path = remove_reference_number(ref_path)
    resolved_path = os.path.expandvars(ref_path)
    directory = os.path.dirname(resolved_path)
    name = os.path.basename(resolved_path)
    name_start, extension = os.path.splitext(name)
    name_start = name_start.split('_')[0].split('.')[0]
    name_pattern = name_start + '*' + extension
    matching_files = glob.glob(os.path.join(directory, name_pattern))
    matching_files = [os.path.basename(p) for p in matching_files]
    new_version = chose_from_list_prompt(matching_files)
    if not new_version:
        return
    new_unresolved_path = os.path.join(os.path.dirname(ref_path), new_version)
    new_unresolved_path = new_unresolved_path.replace('\\', '/')
    if new_unresolved_path == ref_path:
        mc.warning('Skipping, no reference path change (%s).' % ref_path)
        return
    mc.file(new_unresolved_path, loadReference=ref_node, prompt=False)

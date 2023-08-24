import os
import re
import shutil
import codecs
import tempfile
import maya.cmds as mc
from dwmaya.hierarchy import temporarily_reparent_transform_children
from dwmaya.node import temporary_nodename
from dwmaya.selection import preserve_selection


def import_maya_file(filepath, parent=None, namespace=None):

    tmp = temporary_nodename(namespace)
    if namespace:
        content = mc.file(
            filepath, i=True, prompt=False, groupReference=True, groupName=tmp,
            returnNewNodes=True, namespace=namespace)
    else:
        content = mc.file(
            filepath, i=True, prompt=False, groupReference=True, groupName=tmp,
            returnNewNodes=True)

    if mc.objExists(tmp):
        ref_content = mc.listRelatives(tmp, fullPath=True)
        if ref_content and parent:
            mc.parent(ref_content, parent)
        mc.delete(tmp)

    non_dag = list(set(content) - set(mc.ls(content, dagObjects=True)))
    return parent, non_dag


def preserve_maya_scenename(func):
    """
    Decorator to preserve to set back maya scene name at the beginning of the
    function.
    """
    def decorator(*args, **kwargs):
        scene_name = mc.file(query=True, sceneName=True)
        try:
            return func(*args, **kwargs)
        finally:
            if scene_name:
                mc.file(rename=scene_name)
    return decorator


@preserve_selection
@preserve_maya_scenename
def export_node_content(
        node, filepath, binary=False, parent_name=None, force=True,
        additional_non_dag_nodes=None):
    """
    Export a node content in given filepath.
    node -> str: transform node name to extract content.
    filepath -> str: output filepath.
    binary -> bool: Use maya binary file format instead of maya ascii.
    parent_name -> None|str: is value set, place the content in a group.
    force -> bool: do not show dialog if overwritting existing file.
    """
    if parent_name:
        parent = mc.group(
            world=True, empty=True, relative=True, name=parent_name)
    else:
        parent = None

    with temporarily_reparent_transform_children(node, parent) as content:
        if additional_non_dag_nodes:
            content.extend(additional_non_dag_nodes)
        mc.select(content, noExpand=True)
        type_ = 'mayaBinary' if binary else 'mayaAscii'
        filepath = mc.file(
            filepath, exportSelected=True, type=type_, force=force)

    if parent:
        mc.delete(parent)


def detect_filepaths_in_maya_file(maya_file_path, root):
    pattern = rf'"{ root}(.*?)"'
    detected = []
    with codecs.open(maya_file_path, 'r', encoding='iso-8859-1') as mayascii:
        for line in mayascii:
            detected.extend(root + m for m in re.findall(pattern, line))
    return detected


def switch_filepaths_in_maya_file(
        maya_file_path, sources_destinations, overwrite_file=False):
    filename = os.path.basename(maya_file_path)
    directory = tempfile.gettempdir()
    clean = f'{directory}/{os.path.splitext(filename)[0]}_clean.ma'
    with open(clean, 'w') as f:
        with codecs.open(maya_file_path, 'r', encoding='iso-8859-1') as mayascii:
            for line in mayascii:
                for source, destination in sources_destinations:
                    line = line.replace(source, destination)
                f.write(line)
    if not overwrite_file:
        return clean
    shutil.copy(clean, maya_file_path)
    return maya_file_path


@preserve_maya_scenename
def save_temporary_scene_copy():
    scene_name = f'{tempfile.NamedTemporaryFile().name}.ma'
    save_scene_copy(scene_name)
    return scene_name


@preserve_maya_scenename
def save_scene_copy(path):
    mc.file(rename=path)
    mc.file(save=True, force=True, type='mayaAscii')

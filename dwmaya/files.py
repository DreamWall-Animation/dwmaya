import os
import re
from sys import version_info as sys_version_info
from zipfile import ZIP_DEFLATED, ZipFile

import maya.cmds as mc


def is_in_install_path(filepath):
    maya_location = os.path.realpath(
        os.getenv('MAYA_LOCATION')).replace('\\', '/')
    file_location = os.path.realpath(filepath).replace('\\', '/')
    return re.match(f'{maya_location}/*', file_location)


def material_files():
    files = []
    for material in mc.ls(materials=True):
        for attribute in mc.listAttr(material, usedAsFilename=True) or []:
            path = mc.getAttr(f'{material}.{attribute}')
            if not is_in_install_path(path):
                files.append(path)
    return files


def files_in_the_scene():
    return [
        f for f in mc.file(query=True, list=True, withoutCopyNumber=True)
        if not is_in_install_path(f)]


def get_all_file_paths(
        include_unloaded_references=False, include_workspace=False):
    if not mc.file(q=True, sceneName=True):
        raise ValueError('Please save file first')
    if not mc.file(q=True, exists=True):
        raise FileNotFoundError('Scene does not exist')

    files = files_in_the_scene()
    files.extend(material_files())
    if include_workspace:
        files.append(mc.workspace(q=True, fullName=True) + '/workspace.mel')

    if not include_unloaded_references:
        return files

    for ref_node in mc.ls(type='reference'):
        if ref_node.find('sharedReferenceNode') != -1:
            continue
        was_loaded = mc.referenceQuery(ref_node, isLoaded=True)
        if was_loaded is False:
            # load ref if needed
            mc.file(loadReference=ref_node, loadReferenceDepth='all')
        files.extend(mc.file(
            query=True, list=True, withoutCopyNumber=True) or [])
        files.extend(material_files())
        if was_loaded is False:
            mc.file(unloadReference=ref_node)  # restore unloaded state

    return list(set(files))  # remove duplicates


def zip_files(files_paths, zip_path):
    locale = mc.about(codeset=True)
    with ZipFile(zip_path, 'w', ZIP_DEFLATED, allowZip64=True) as zip:
        skipped_files = []
        for i, filepath in enumerate(files_paths):
            if not os.path.isfile(filepath):
                skipped_files.append(filepath)
                print(f'WARNING: skipping non-existing file {filepath}')
                continue
            if sys_version_info[0] < 3:
                filepath = filepath.encode(locale)
            print(f'{i + 1}/{len(files_paths)}: {os.path.basename(filepath)}')
            zip.write(filepath)
    return skipped_files


def zip_scene_files(zip_path=None, include_unloaded_references=False):
    files_paths = get_all_file_paths(include_unloaded_references)
    if not files_paths:
        return
    scene_path = files_paths[0]
    if zip_path is None:
        zip_path = f'{scene_path}.zip'
    zip_files(files_paths, zip_path)
    return zip_path

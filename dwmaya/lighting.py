__author__ = 'Olivier Evers'
__copyright__ = 'DreamWall'
__license__ = 'MIT'


import os
import json

import maya.cmds as mc


def get_lights():
    return mc.ls(type=mc.listNodeTypes('light'))


def copy_asset_lightlinking(source_namespace, target_namespace):
    for light in get_lights():
        target_nodes = mc.ls(target_namespace + ':*', type='mesh')
        for shadow in [False, True]:
            mc.lightlink(
                light=light, object=target_nodes, b=True, shadow=shadow)
            for node in mc.lightlink(query=True, light=light, shadow=shadow):
                if mc.nodeType(node) != 'mesh':
                    continue
                if source_namespace not in node:
                    continue
                target_node = node.replace(source_namespace, target_namespace)
                if not mc.objExists(target_node):
                    continue
                print(node, target_node)
                mc.lightlink(
                    make=True, light=light, object=target_node, shadow=shadow)


def get_lightlinking_as_dict():
    lightlinking = {}
    for light in get_lights():
        light_ll = {}
        for shadow in [False, True]:
            light_ll[shadow] = mc.lightlink(
                query=True, light=light, shadow=shadow)
        lightlinking[light] = light_ll
    return lightlinking


def save_lightlinking_to_json(json_path):
    if os.path.exist(json_path):
        raise Exception('json path already exists.')
    with open(json_path, 'w') as f:
        json.dump(get_lightlinking_as_dict(), f, indent=4, sort_keys=True)


def remove_all_lightlinking():
    all_objects = mc.ls(type='transform')
    all_lights = get_lights()
    for shadow in [True, False]:
        mc.lightlink(
            light=all_lights, object=all_objects, b=True, shadow=shadow)


def set_lightlinking_from_dict(lightlinking):
    remove_all_lightlinking()
    for light in lightlinking:
        print(light)
        for shadow in lightlinking[light]:
            objects = lightlinking[light][shadow]
            count = len(objects)
            objects = mc.ls(objects)
            if len(objects) != count:
                print 'Missing %i objects' % (count - len(objects))
            mc.lightlink(make=True, light=light, object=objects, shadow=shadow)


def set_lightlinking_from_json(json_path):
    with open(json_path, 'r') as f:
        set_lightlinking_from_dict(json.load(f))

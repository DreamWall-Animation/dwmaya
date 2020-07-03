__author__ = 'Olivier Evers'
__copyright__ = 'DreamWall'
__license__ = 'MIT'


import maya.cmds as mc


def get_shape_and_transform(shape_or_transform):
    if mc.ls(shape_or_transform, shapes=True):
        shape = shape_or_transform
        transform = mc.listRelatives(shape, parent=True, path=True)[0]
    else:
        transform = shape_or_transform
        transform = mc.listRelatives(transform, children=True, path=True)[0]
    return shape, transform


def get_selected_shapes():
    nodes = mc.ls(selection=True)
    transforms = mc.ls(nodes, transforms=True)
    transforms_children = mc.listRelatives(transforms, children=True) or []
    transforms_shapes = mc.ls(transforms_children, shapes=True)
    return transforms_shapes


def extend_selection_to_shapes():
    "Selection extended to transform's shapes"
    mc.select(get_selected_shapes(), add=True)


def get_parents(nodes, sep='|'):
    parents = set()
    for node in nodes:
        if sep not in node:
            raise Exception('"nodes" arg should be passed full node paths.')
        parts = node.split(sep)[1:]
        while parts:
            parts.pop()
            if not parts:
                break
            parents.add(sep + sep.join(parts))
    return parents


def is_parent_of(parent, node):
    if not parent:
        raise Exception('"parent" arg is mandatory.')
    if not node:
        raise Exception('"node" arg is mandatory.')
    return mc.ls(node, long=True)[0].startswith(mc.ls(parent, long=True)[0])


def remove_overlapping_nodes(nodes):
    """
    If a parent of a node in in the nodes list, remove it from the list.
    """
    to_remove = []
    for node in nodes:
        for parent in get_parents([node]):
            if parent in nodes:
                to_remove.append(node)
                break
    return list(set(nodes) - set(to_remove))


def get_closest_to_root(nodes):
    nodes = mc.ls(nodes, long=True, dag=True)
    if not nodes:
        return []
    nodes = sorted(nodes, key=lambda n: n.count('|'))
    roots_pipes_count = nodes[0].count('|')
    return [n for n in nodes if n.count('|') == roots_pipes_count]

__author__ = 'Olivier Evers'
__copyright__ = 'DreamWall'
__license__ = 'MIT'

from contextlib import contextmanager
import maya.cmds as mc


def get_shape_and_transform(shape_or_transform):
    if mc.ls(shape_or_transform, shapes=True):
        shape = shape_or_transform
        transform = mc.listRelatives(shape, parent=True, path=True)[0]
    else:
        transform = shape_or_transform
        shape = mc.listRelatives(transform, children=True, path=True)[0]
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


def find_root(node):
    parent = mc.listRelatives(node, parent=True)
    while parent:
        node = parent
        parent = mc.listRelatives(node, parent=True)
    return node


def is_parent_of(parent, node):
    if not parent:
        raise Exception('"parent" arg is mandatory.')
    if not node:
        raise Exception('"node" arg is mandatory.')
    return mc.ls(node, long=True)[0].startswith(mc.ls(parent, long=True)[0])


def is_visible(node):
    attrs = mc.listAttr(node)
    if 'visibility' in attrs and not mc.getAttr(node + '.visibility'):
        return False
    if 'lodVisibility' in attrs and not mc.getAttr(node + '.lodVisibility'):
        return False
    if ('intermediateObject' in attrs and
            mc.getAttr(node + '.intermediateObject')):
        return False
    return True


def get_visible_children_shapes(node):
    nodes = mc.listRelatives(node, path=True, children=True) or []
    visible_shapes = []
    while nodes:
        node = nodes.pop()
        if not is_visible(node):
            continue
        nodes.extend(mc.listRelatives(node, path=True, children=True) or [])
        if not mc.ls(node, shapes=True):
            continue
        visible_shapes.append(node)
    return visible_shapes


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


@contextmanager
def temporarily_reparent_transform_children(transform, parent=None):
    """
    Set the children of a node to scene root.
    usage:
    with temporarily_extracted_node_children(node) as content:
        mc.select(content)
        mc.file(exportSelected=True)
    """
    try:
        content = mc.listRelatives(transform, fullPath=True)
        if parent is not None:
            result = mc.parent(content, parent)
        else:
            result = mc.parent(content, world=True)
        yield result

    finally:
        mc.parent(result, transform)

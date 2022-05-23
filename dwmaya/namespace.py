__author__ = 'Lionel Brouyere, Olivier Evers'
__copyright__ = 'DreamWall'
__license__ = 'MIT'


import re
from contextlib import contextmanager

import maya.cmds as mc


def get_non_existing_namespace(prefix='dw'):
    i = 0
    namespace = '%s%i' % (prefix, i)
    while namespace in mc.namespaceInfo(listNamespace=True):
        i += 1
        namespace = '%s%i' % (prefix, i)
    return namespace


def node_namespace(node):
    """
    Return the namespace of the given node
    Example:
        input: "namespace:nodename"  | output: "namespace"
        input: "|parent|nodemane"    | output: None
        intput "|parent|ns:nodename" | output: "ns"
    :param str node: Maya node name
    :rtype: str|None
    """
    basename = node.split("|")[-1]
    if ":" not in node:
        return None
    return basename.split(":")[0]


def shortname_without_namespace(node):
    """
    Returns the node name with neither hierarchy nor namespace.
    Example:
        input: "namespace:nodename"  | output: "nodename"
        input: "|parent|nodemane"    | output: "nodename"
        intput "|parent|ns:nodename" | output: "nodename"
    :rtype: str
    """
    basename = node.split("|")[-1]
    if ":" not in node:
        return basename
    return basename.split(":")[-1]


def strip_namespaces(node):
    """
    This function stip all the namespaces found in a maya node path.
    Examples:
        input: "|nodename"                 | output: "|nodename"
        input: "namespace:commander"       | output: "commander"
        input: "|ns:parent|ns:child"       | output: "|parent|child"
        input: "|nonamespace|nonamespace|" | output: "|nonamespace|nonamespace"
    :param str node: Maya node name or fullpath
    :rtype: str
    """
    return re.sub('\w+:', '', node)


@contextmanager
def maya_namespace(
        namespace='', create_if_missing=True, restore_current_namespace=True):
    """Context manager to temporarily set a namespace"""
    initial_namespace = ':' + mc.namespaceInfo(currentNamespace=True)
    if not namespace.startswith(':'):
        namespace = ':' + namespace
    try:
        if not mc.namespace(absoluteName=True, exists=namespace):
            if create_if_missing:
                mc.namespace(setNamespace=':')
                namespace = mc.namespace(addNamespace=namespace)
            else:
                mc.namespace(initial_namespace)
                raise ValueError(namespace + " doesn't exist.")
        mc.namespace(setNamespace=namespace)
        yield namespace
    finally:
        if restore_current_namespace:
            mc.namespace(setNamespace=initial_namespace)

"""
Collection of utils related to maya namespace.
"""

import re
from maya import cmds


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


class MayaNamespace():
    """
    Context manager to set temporarily a namespace.
    """
    def __init__(self, namespace="", create_if_missing=True, leave_on_exit=True):
        self.original_namespace = ":" + cmds.namespaceInfo(currentNamespace=True)
        self.create_if_missing = create_if_missing
        self.namespace = ":" + namespace
        self.leave_on_exit = leave_on_exit

    def __enter__(self):
        if not cmds.namespace(absoluteName=True, exists=self.namespace):
            if self.create_if_missing:
                cmds.namespace(setNamespace=":")
                self.namespace = cmds.namespace(addNamespace=self.namespace)
            else:
                cmds.namespace(self.original_namespace)
                raise ValueError(self.namespace + " doesn't exists.")
        cmds.namespace(setNamespace=self.namespace)
        return self.namespace

    def __exit__(self, type, value, traceback):
        if not self.leave_on_exit:
            return True
        cmds.namespace(setNamespace=self.original_namespace)
        return True

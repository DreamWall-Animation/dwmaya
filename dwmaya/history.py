import maya.cmds as mc


def _recursive_add_input_nodes(node: str, history: set):
    connections = mc.listConnections(
        node, source=True, destination=False, plugs=True)
    if not connections:
        return
    for input_node in mc.ls(connections, long=True, objectsOnly=True):
        if input_node not in history:
            history.add(input_node)
            _recursive_add_input_nodes(input_node, history)


def list_full_history(nodes):
    history = set()
    for node in mc.ls(nodes, long=True):
        _recursive_add_input_nodes(node, history)
    return list(history)

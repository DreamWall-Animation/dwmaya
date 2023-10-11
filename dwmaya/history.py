import maya.cmds as mc


def find_input_nodes(node, depth=0, max_depth=10):
    input_nodes = []

    if depth >= max_depth:
        return input_nodes

    connections = mc.listConnections(
        node, source=True, destination=False, plugs=True)

    if connections:
        for connection in connections:
            input_node = connection.split('.')[0]
            input_nodes.append(input_node)
            input_nodes += find_input_nodes(
                input_node, depth=depth + 1, max_depth=max_depth)

    return input_nodes


def list_full_history(nodes):
    history = []
    for node in nodes:
        history.expand(find_input_nodes(node, max_depth=100))
    return list(set(history))


from contextlib import contextmanager
import maya.cmds as mc


@contextmanager
def unlocked_nodes(nodes):
    if isinstance(nodes, (str, unicode)):
        nodes = [nodes]
    states = [mc.lockNode(node, query=True)[0] for node in nodes]
    try:
        for node in nodes:
            mc.lockNode(node, lock=False)
        yield
    finally:
        for state, node in zip(states, nodes):
            mc.lockNode(node, lock=state)

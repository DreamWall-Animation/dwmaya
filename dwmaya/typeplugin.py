import json
import maya.cmds as mc


def create_type():
    mc.loadPlugin('Type', quiet=True)
    mc.CreatePolygonType()
    type_node = mc.ls(type='type')[-1]
    transform = mc.listConnections(f'{type_node}.transformMessage')[0]
    return transform, type_node


def format_text(text):
    return ' '.join(['%02X' % ord(x) for x in text])


def set_animated_type(type_node, frames_text):
    """
    `frames_text` example: [(1, 'frame 1'), (2, 'frame 2')]
    """
    data = json.dumps([
        dict(hex=format_text(t), frame=f) for f, t in frames_text])
    mc.setAttr(f'{type_node}.generator', 8)
    mc.setAttr(f'{type_node}.animatedType', data, type='string')

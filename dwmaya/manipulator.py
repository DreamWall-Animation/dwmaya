import math
import maya.cmds as mc


def average(values):
    return sum(values) / len(values)


def get_selection_center(selection=None):
    """Bounding box center that is."""
    selection = selection or mc.ls(selection=True, flatten=True)
    if not selection:
        raise Exception('Nothing is selected.')
    if len(selection) == 1:
        return mc.xform(
            selection[0], query=True, translation=True, worldSpace=True)
    minx = miny = minz = float('inf')
    maxx = maxy = maxz = -float('inf')
    for item in selection:
        if '.' in item:
            # Components (vertex, edge, ...)
            x1, y1, z1 = mc.xform(
                item, query=True, translation=True, worldSpace=True)
            x2, y2, z2 = x1, y1, z1
        else:
            # Geo/transform
            x1, y1, z1, x2, y2, z2 = mc.exactWorldBoundingBox(item)
        minx = min(x1, minx)
        maxx = max(x2, maxx)
        miny = min(y1, miny)
        maxy = max(y2, maxy)
        minz = min(z1, minz)
        maxz = max(z2, maxz)
    return average([minx, maxx]), average([miny, maxy]), average([minz, maxz])


def dotproduct(v1, v2):
    return sum((a * b) for a, b in zip(v1, v2))


def length(v):
    return math.sqrt(dotproduct(v, v))


def angle(v1, v2):
    return math.acos(dotproduct(v1, v2) / (length(v1) * length(v2)))


def vector_to_xy_euler_angles(vx, vy, vz):
    rx = angle([vx, vy, vz], [vx, 0, vz])
    ry = angle([vx, 0, vz], [0, 0, 1])
    if vy > 0:
        rx = -rx
    if vx < 0:
        ry = -ry
    return rx, ry


def set_movetool_direction(vx, vy, vz, horizontal=False):
    """Set moveTool's axes to match given vector"""
    rx, ry = vector_to_xy_euler_angles(vx, vy, vz)
    rz = 0
    if horizontal:
        rx = 0
    mc.manipMoveContext(
        'Move', edit=True, mode=6, orientAxes=[rx, ry, rz], activeHandle=2)


def set_movetool_towards_target(target_transform, horizontal=False):
    """Set moveTool's axes to aim at target"""
    x1, y1, z1 = mc.xform(
        target_transform, query=True, worldSpace=True, scalePivot=True)
    x2, y2, z2 = get_selection_center()
    x, y, z = x1 - x2, y1 - y2, z1 - z2
    set_movetool_direction(x, y, z, horizontal=horizontal)

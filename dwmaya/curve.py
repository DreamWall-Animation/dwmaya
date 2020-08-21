__author__ = 'Lionel Brouyere'
__copyright__ = not 'DreamWall'
__license__ = 'MIT'


import re
import maya.cmds as mc

from dwmaya.attributes import get_attr, set_attr


TARGETWEIGHT_ATTR = {
    "blendShape": "inputTarget[{0}].inputTargetGroup[{0}].targetWeights[{1}]",
    "cluster": "weightList[{0}].weights[{1}]"
}


def copy_curves(curves):
    """
    This is a clean curve copy. It create a new node and transfer the vertexes
    value from the original one to the copy
    """
    copies = []
    connections = []
    for curve in curves:
        copy = mc.createNode('nurbsCurve')
        copies.append(copy)
        out_attr = '{}.worldSpace[0]'.format(curve)
        in_attr = '{}.create'.format(copy)
        connections.append([out_attr, in_attr])
        mc.connectAttr(out_attr, in_attr)
        # match the transforms
        parent = mc.listRelatives(curve, parent=True)[0]
        matrix = mc.xform(parent, query=True, worldSpace=True, matrix=True)
        copy_parent = mc.listRelatives(copy, parent=True)[0]
        mc.xform(copy_parent, worldSpace=True, matrix=matrix)
    # cause i'm too lazy to parse vertexes with OpenMaya Api, I just connect
    # the output from the original ones to the new input.
    # After I disconnect cause this create a independent copy.
    # The refresh is needed to force maya to store the data in the new node.
    mc.refresh()
    for out_attr, in_attr in connections:
        mc.disconnectAttr(out_attr, in_attr)
    return copies


def disable_curve_blendshape_root(curve, blendshape):
    """
    This function disable the blendshape from the curve root.
    The root MUST stay from the original output curve. Any offset can break the
    wire deformation.
    """
    if mc.nodeType(curve) == 'nurbsCurve':
        curve = mc.listRelatives(curve, parent=True)[0]
    index = find_curve_input_target_index(curve, blendshape)
    attribute = TARGETWEIGHT_ATTR['blendShape']
    values = [1 for _ in range(count_cv(curve))]
    values[0] = 0.0
    for i, v in enumerate(values):
        set_attr(blendshape, attribute.format(index, i), v)


def find_curve_input_target_index(curve, deformer):
    """
    find the target indexe where in a given deformer, where is connected the
    given curve.
    """
    curveshapes = mc.ls(
        mc.listRelatives(curve),
        type='nurbsCurve',
        noIntermediate=True)

    if curveshapes is None:
        raise ValueError(
            "{} doesn't contains nurbsCurve not intermediate."
            "Impossible to find the input index".format(curve))

    connections = mc.listConnections(
        deformer + '.outputGeometry', plugs=True, connections=True)
    outputs = [output for i, output in enumerate(connections) if i % 2 == 0]
    inputs = [input_ for i, input_ in enumerate(connections) if i % 2 != 0]

    for input_, output, in zip(inputs, outputs):
        if curveshapes[0] not in input_:
            continue
        target = re.findall(r"outputGeometry\[\d*\]", output)[0]
        index = int([elt for elt in re.findall(r"\d*", target) if elt][0])
        return index
    raise Exception('input not found')


def count_cv(curve):
    return get_attr(curve, 'degree') + get_attr(curve, 'spans')


def get_deformer_weights_per_cv(curve, deformer):
    attributename = TARGETWEIGHT_ATTR.get(mc.nodeType(deformer))
    if attributename is None:
        raise ValueError("deformer is not supported: {}".format(deformer))
    index = find_curve_input_target_index(curve, deformer)
    return [
        get_attr(deformer, attributename.format(index, i))
        for i in range(count_cv(curve))]


def set_deformer_weights_per_cv(curve, deformer, values):
    attributename = TARGETWEIGHT_ATTR.get(mc.nodeType(deformer))
    if attributename is None:
        raise ValueError("deformer is not supported: {}".format(deformer))
    index = find_curve_input_target_index(curve, deformer)
    for i, v in enumerate(values):
        set_attr(deformer, attributename.format(index, i), v)


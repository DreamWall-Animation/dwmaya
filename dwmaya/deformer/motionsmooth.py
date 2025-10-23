import maya.cmds as mc
import maya.api.OpenMaya as om2
from dwmaya.deformer.tag import force_deformation_component_tags_var


MOTION_SMOOTH_CACHE_BLENDSHAPE_NAME = '{}_motion_smooth_cache_BS'
LINEAR_INTERPOLATION_CACHE_BLENDSHAPE_NAME = '{}_linear_interpolation_cache_BS'
DELTA_OFFSET_CACHE_BLENDSHAPE_NAME = '{}_delta_offset_cache_BS'


def copy_mesh(mesh):
    copy = mc.createNode('mesh')
    mc.connectAttr(mesh + '.worldMesh', copy + '.inMesh')
    mc.refresh()
    mc.disconnectAttr(mesh + '.worldMesh', copy + '.inMesh')
    return copy


def input_mesh_copy(mesh):
    copy = mc.createNode('mesh')
    input_connections = mc.listConnections(mesh + '.inMesh', plugs=True)
    mc.connectAttr(input_connections[0], copy + '.inMesh')
    return copy


def get_frame_samples(aperture, samples):
    iterations = (samples * 2) + 1
    start_frame = mc.currentTime(query=True) - aperture
    sampling_lengh = aperture / samples
    return [start_frame + (i * sampling_lengh) for i in range(iterations)]


def create_motionblend_mesh(base, aperture=1, samples=1, skip_center=False):
    """ function to duplicate an animated mesh with a motion smooth.
    Motion smooth is a average geometry with point positions on timings around
    the current frames.

    :aperture: is the timing where start the sampling and when it stop. e.i. If
    the value is one and the current frame is 255, the algorytm will start at
    254 and finish at 256.
    :samples: is the number (only integers) of samples taken. e.i. If the
    aperture is 1, sample 2 and current frame is 255, the algorytm will blend
    the geo with those timings: 254, 254.5, 255, 255.5 and 256
    :skip_center: if this option is true, the current frame vetexes positions
    aren't used at all to create the motion blend mesh.
    """
    motion_blend = copy_mesh(base)
    selection_list = om2.MSelectionList()
    selection_list.add(base)
    selection_list.add(motion_blend)

    current_time = mc.currentTime(query=True)
    base_fn_mesh = om2.MFnMesh(selection_list.getDagPath(0))
    points = []
    for frame in get_frame_samples(aperture, samples):
        if skip_center is True and frame == current_time:
            continue
        mc.currentTime(frame, edit=True)
        points.append(base_fn_mesh.getPoints())
    mc.currentTime(current_time, edit=True)

    motion_blend_points = []
    for i in range(len(points[0])):
        x = sum(p[i][0] for p in points) / len(points)
        y = sum(p[i][1] for p in points) / len(points)
        z = sum(p[i][2] for p in points) / len(points)
        position = om2.MPoint(x, y, z)
        motion_blend_points.append(position)
    motion_blend_fn_mesh = om2.MFnMesh(selection_list.getDagPath(1))
    motion_blend_fn_mesh.setPoints(motion_blend_points)
    motion_blend_fn_mesh.updateSurface()
    return motion_blend


@force_deformation_component_tags_var(state=False)
def bake_motion_smooth_cache(
        mesh, startframe=None, endframe=None, aperture=1, samples=1):
    """ function which bake the given range.
    That create a blendshape and apply a motion blend on every frame.
    """

    frames = range(int(startframe), int(endframe) + 1)
    blendshape = None
    reference_mesh = input_mesh_copy(mesh)
    for i, frame in enumerate(frames):
        mc.refresh()
        mc.currentTime(frame, edit=True)
        blend_mesh = create_motionblend_mesh(
            reference_mesh,
            aperture=aperture,
            samples=samples,
            skip_center=True)

        if blendshape is None:
            mesh_nicename = mesh.split("|")[-1]
            blendshape = mc.blendShape(
                blend_mesh,
                mesh,
                name=MOTION_SMOOTH_CACHE_BLENDSHAPE_NAME.format(mesh_nicename),
                origin='world',
                weight=(0, 1))[0]
        else:
            mc.blendShape(
                blendshape, edit=True, before=True,
                target=(mesh, i, blend_mesh, 1.0))
        # set animation on new target
        attribute = '{}.weight[{}]'.format(blendshape, i)
        mc.setKeyframe(attribute, time=frame - 1, value=0.0)
        mc.setKeyframe(attribute, time=frame, value=1.0)
        mc.setKeyframe(attribute, time=frame + 1, value=0.0)
        mc.refresh()
        # delete the target to store the delta directly inside the blendshape
        motionblend_parent = mc.listRelatives(blend_mesh, parent=True)
        mc.delete(motionblend_parent)

    reference_parent = mc.listRelatives(reference_mesh, parent=True)
    mc.delete(reference_parent)
    return blendshape


def create_linear_interpolation_mesh(base, target, weight=0.5):
    """ This function create an inbetween mesh between the base and the target.
    The weight define the weight of the target. 1 means 100% target, 0 means
    100% base.
    """
    copy = copy_mesh(base)
    selection_list = om2.MSelectionList()
    selection_list.add(base)
    selection_list.add(target)
    selection_list.add(copy)
    fn_base_mesh = om2.MFnMesh(selection_list.getDagPath(0))
    fn_target_mesh = om2.MFnMesh(selection_list.getDagPath(1))
    fn_mesh_copy = om2.MFnMesh(selection_list.getDagPath(2))
    base_points = fn_base_mesh.getPoints()
    target_points = fn_target_mesh.getPoints()
    blended_points = []
    rweight = 1 - weight
    for i in range(len(base_points)):
        x = (target_points[i][0] * weight) + (base_points[i][0] * rweight)
        y = (target_points[i][1] * weight) + (base_points[i][1] * rweight)
        z = (target_points[i][2] * weight) + (base_points[i][2] * rweight)
        position = om2.MPoint(x, y, z)
        blended_points.append(position)
    fn_mesh_copy.setPoints(blended_points)
    fn_mesh_copy.updateSurface()
    return copy


def bake_linear_interpolation_blendshape(mesh, startframe, endframe):
    """Function which create an blendshape of deltas and create a linear
    geometry interpolation for the given mesh"""
    frames = range(int(startframe), int(endframe) + 1)
    blendshape = None
    mc.currentTime(startframe, edit=True)
    base = copy_mesh(mesh)
    mc.currentTime(endframe, edit=True)
    target = copy_mesh(mesh)

    for i, frame in enumerate(frames):
        mc.refresh()
        mc.currentTime(frame, edit=True)
        weight = float(frame - startframe) / (endframe - startframe)
        blend_mesh = create_linear_interpolation_mesh(base, target, weight=weight)

        if blendshape is None:
            mesh_nicename = mesh.split("|")[-1]
            blendshape = mc.blendShape(
                blend_mesh,
                mesh,
                name=LINEAR_INTERPOLATION_CACHE_BLENDSHAPE_NAME.format(mesh_nicename),
                origin='world',
                weight=(0, 1))[0]
        else:
            mc.blendShape(
                blendshape, edit=True, before=True,
                target=(mesh, i, blend_mesh, 1.0))
        # set animation on new target
        attribute = '{}.weight[{}]'.format(blendshape, i)
        mc.setKeyframe(attribute, time=frame - 1, value=0.0)
        mc.setKeyframe(attribute, time=frame, value=1.0)
        mc.setKeyframe(attribute, time=frame + 1, value=0.0)
        mc.refresh()
        # delete the target to store the delta directly inside the blendshape
        motionblend_parent = mc.listRelatives(blend_mesh, parent=True)
        mc.delete(motionblend_parent)

    parents = mc.listRelatives([base, target], parent=True)
    mc.delete(parents)
    return blendshape


def create_delta_offest_mesh(mesh_base, mesh_offset, mesh_target):
    mesh_result = copy_mesh(mesh_target)
    selection_list = om2.MSelectionList()
    selection_list.add(mesh_base)
    selection_list.add(mesh_offset)
    selection_list.add(mesh_target)
    selection_list.add(mesh_result)

    mesh_base_fn_mesh = om2.MFnMesh(selection_list.getDagPath(0))
    mesh_offset_fn_mesh = om2.MFnMesh(selection_list.getDagPath(1))
    mesh_target_fn_mesh = om2.MFnMesh(selection_list.getDagPath(2))
    mesh_result_fn_mesh = om2.MFnMesh(selection_list.getDagPath(3))

    mesh_base_points = mesh_base_fn_mesh.getPoints()
    mesh_offset_points = mesh_offset_fn_mesh.getPoints()
    mesh_target_points = mesh_target_fn_mesh.getPoints()
    mesh_result_points = []

    for i in range(len(mesh_base_points)):
        offset = mesh_base_points[i] - mesh_offset_points[i]
        mesh_result_points.append(mesh_target_points[i] - offset)

    mesh_result_fn_mesh.setPoints(mesh_result_points)
    mesh_result_fn_mesh.updateSurface()

    return mesh_result


def bake_delta_animation_blendshape(
        mesh_base, mesh_offset, mesh_target, startframe, endframe):
    frames = range(int(startframe), int(endframe) + 1)
    blendshape = None
    reference_mesh = input_mesh_copy(mesh_target)
    for i, frame in enumerate(frames):
        mc.refresh()
        mc.currentTime(frame, edit=True)
        delta_mesh = create_delta_offest_mesh(
            mesh_base=mesh_base,
            mesh_offset=mesh_offset,
            mesh_target=mesh_target)

        if blendshape is None:
            mesh_nicename = mesh_target.split("|")[-1]
            blendshape = mc.blendShape(
                delta_mesh,
                mesh_target,
                name=DELTA_OFFSET_CACHE_BLENDSHAPE_NAME.format(mesh_nicename),
                origin='world',
                weight=(0, 1))[0]
        else:
            mc.blendShape(
                blendshape, edit=True, before=True,
                target=(mesh_target, i, delta_mesh, 1.0))
        # set animation on new target
        attribute = '{}.weight[{}]'.format(blendshape, i)
        mc.setKeyframe(attribute, time=frame - 1, value=0.0)
        mc.setKeyframe(attribute, time=frame, value=1.0)
        mc.setKeyframe(attribute, time=frame + 1, value=0.0)
        mc.refresh()
        # delete the target to store the delta directly inside the blendshape
        delta_parent = mc.listRelatives(delta_mesh, parent=True)
        mc.delete(delta_parent)

    reference_parent = mc.listRelatives(reference_mesh, parent=True)
    mc.delete(reference_parent)
    return blendshape



if __name__ == "__main__":
    # startframe = mc.playbackOptions(query=True, min=True)
    # endframe = mc.playbackOptions(query=True, max=True)
    # mesh = mc.ls(selection=True, type='mesh', dag=True, noIntermediate=True)
    # bake_motion_smooth_cache(mesh[0], startframe, endframe, aperture=2, samples=2)

    # mesh = "blueFalcon:cape_INPUT_alternate_inputshape_001"
    # frame_in = 208
    # frame_out = 215
    # bake_linear_interpolation_blendshape(mesh, frame_in, frame_out)

    frame_in = 89
    frame_out = 168
    bake_delta_animation_blendshape(
        'winnie_hoodie2:longSleeveShirt_REN',
        'winnie_hoodie3:longSleeveShirt_REN',
        'winnie_hoodie:longSleeveShirt_REN',
        frame_in, frame_out)
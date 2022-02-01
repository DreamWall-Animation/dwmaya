import maya.cmds as mc
import maya.mel as mm
from dwmaya.plugins import ensure_plugin_loaded
from dwmaya.mesh import create_finalling_intermediate, selected_meshes


@ensure_plugin_loaded('MayaMuscle')
def maya_muscle_smooth():
    meshes = selected_meshes()
    for mesh in meshes:
        intermediate_mesh = create_finalling_intermediate(mesh)
        if not intermediate_mesh:
            continue
        mc.select(intermediate_mesh)
        mm.eval("cMuscle_makeMuscleSystem(1)")
        mc.setAttr(intermediate_mesh + '.lodVisibility', False)
        transform = mc.listRelatives(intermediate_mesh)
        mc.rename(transform, mesh + "_muscleSmoothProxy")
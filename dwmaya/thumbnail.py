import maya.cmds as mc
import maya.OpenMayaUI as omui
from dwmaya.selection import preserve_selection


@preserve_selection
def create_node_thumbnail(node, size):
    active_view = omui.M3dView.active3dView().widget()
    panel = omui.MQtUtil.fullName(int(active_view)).strip('|').split('|')[-1]
    vp_state = mc.isolateSelect(panel, state=True, query=True)
    mc.isolateSelect(panel, state=True)
    mc.select(mc.ls())
    mc.isolateSelect(panel, removeSelected=True)
    mc.isolateSelect(panel, addDagObject=node)
    mc.viewFit(node)
    mc.isolateSelect(panel, state=vp_state)
    return _render_thumbnail(size)


def _render_thumbnail(size):
    for cam in mc.ls(type="camera"):
        mc.setAttr(cam + '.renderable', cam == 'perspShape')
    attribute = "perspShape.backgroundColor"
    mc.setAttr(attribute, 0.375, 0.375, 0.375, type="double3")
    frame = mc.currentTime(query=True)
    mc.setAttr("defaultRenderGlobals.startFrame", frame)
    mc.setAttr("defaultRenderGlobals.endFrame", frame)
    mc.setAttr("defaultRenderGlobals.extensionPadding", 6)
    attribute = "defaultRenderGlobals.currentRenderer"
    mc.setAttr(attribute, "mayaHardware2", type="string")
    mc.setAttr("defaultRenderGlobals.imageFormat", 8)
    attribute = "defaultRenderGlobals.imageFilePrefix"
    mc.setAttr(attribute, 'temp_render', type="string")
    mc.setAttr("defaultRenderGlobals.animation", True)
    mc.setAttr("defaultRenderGlobals.putFrameBeforeExt", True)
    mc.setAttr("defaultRenderGlobals.outFormatControl", 0)
    return mc.ogsRender(width=size[0], height=size[1])

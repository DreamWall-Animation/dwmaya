import maya.cmds as mc


def copy_asset_lightlinking(source_namespace, target_namespace):
    for light in mc.ls(type=mc.listNodeTypes('light')):
        target_nodes = mc.ls(target_namespace + ':*', type='mesh')
        for shadow in [False, True]:
            mc.lightlink(
                light=light, object=target_nodes, b=True, shadow=shadow)
            for node in mc.lightlink(query=True, light=light, shadow=shadow):
                if mc.nodeType(node) != 'mesh':
                    continue
                if source_namespace not in node:
                    continue
                target_node = node.replace(source_namespace, target_namespace)
                if not mc.objExists(target_node):
                    continue
                print(node, target_node)
                mc.lightlink(
                    make=True, light=light, object=target_node, shadow=shadow)

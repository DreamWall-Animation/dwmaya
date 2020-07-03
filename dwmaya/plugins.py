__author__ = 'Olivier Evers'
__copyright__ = 'DreamWall'
__license__ = 'MIT'


import maya.cmds as mc


def load_plugin(plugin_name):
    mc.loadPlugin(plugin_name, quiet=True)


def remove_autoloads():
    for plugin in mc.pluginInfo(query=True, listPluginsPath=True):
        if 'autoLoader' in plugin:
            continue
        mc.pluginInfo(plugin, edit=True, autoload=False)
    mc.pluginInfo(savePluginPrefs=True)


def remove_unknown_plugins():
    for node in mc.ls(type='unknown'):
        mc.lockNode(node, lock=False)
        print('Deleting unknown node "%s"' % node)
        mc.delete(node)

    for plugin in mc.unknownPlugin(query=True, list=True):
        print('Removing unknown plugin "%s"' % plugin)
        mc.unknownPlugin(plugin, remove=True)


def print_plugin_nodes():
    for plugin in mc.pluginInfo(query=True, listPlugins=True):
        print plugin
        nodes = mc.pluginInfo(plugin, query=True, dependNode=True)
        if not nodes:
            print('No nodes with this plugin\n')
            break
        for node in nodes:
            print('    ' + node)
        print('')


def find_nodetype_plugin(node_type):
    for plugin in mc.pluginInfo(query=True, listPlugins=True):
        if node_type in mc.pluginInfo(plugin, q=True, dependNode=True) or []:
            return plugin

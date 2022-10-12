__author__ = 'Olivier Evers'
__copyright__ = 'DreamWall'
__license__ = 'MIT'


import maya.cmds as mc


def load_plugin(plugin_name):
    mc.loadPlugin(plugin_name, quiet=True)


def remove_autoloads(excludes=None):
    if excludes is None:
        excludes = ['autoLoader']
    for plugin in mc.pluginInfo(query=True, listPluginsPath=True):
        if plugin in excludes:
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
        print(plugin)
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


def ensure_plugin_loaded(*plugin_names):
    """
    Decorator which ensure the given plugins are
    loaded on the function execution.
    usage:
    @ensure_plugin_loaded('AbcImport', 'AbcExport')
    def export_wire_alembic():
        blablabla ...
    """
    def wrap(func):
        def decorator(*args, **kwargs):
            for plugin_name in plugin_names:
                if not mc.pluginInfo(plugin_name, query=True, loaded=True):
                    load_plugin(plugin_name)
            return func(*args, **kwargs)
        return decorator
    return wrap
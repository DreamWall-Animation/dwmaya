__author__ = 'Olivier Evers'
__copyright__ = 'DreamWall'
__license__ = 'MIT'


import maya.cmds as mc

MAYA_WINDOW = 'MayaWindow'

SEPARATOR = None


def add_menu_item(item_dict, parent):
    if item_dict is SEPARATOR:
        mc.menuItem(divider=True, parent=parent)
    elif isinstance(item_dict['command'], list):
        submenu = mc.menuItem(
            subMenu=True, label=item_dict['label'], tearOff=True,
            parent=parent)
        for sub_item_dict in item_dict['command']:
            add_menu_item(sub_item_dict, submenu)
    else:
        mc.menuItem(
            label=item_dict['label'],
            command=item_dict['command'],
            parent=parent,
            echoCommand=True)


def get_menu_with_label(label, window=MAYA_WINDOW):
    labels_menus = {
        mc.menu(m, query=True, label=True): m for m in
        mc.window(MAYA_WINDOW, query=True, menuArray=True)}
    try:
        return labels_menus[label]
    except KeyError:
        return ''


def delete_menu_with_label(label, window=MAYA_WINDOW):
    menu = get_menu_with_label(label)
    while menu:
        mc.deleteUI(menu)
        menu = get_menu_with_label(label)


def create_dw_maya_menu(name, items):
    if mc.about(batch=True):
        return
    delete_menu_with_label(name, MAYA_WINDOW)
    dw_menu = mc.menu(
        'dwmenu', label=name, parent=MAYA_WINDOW, tearOff=True)
    for menu_item in items:
        add_menu_item(menu_item, dw_menu)

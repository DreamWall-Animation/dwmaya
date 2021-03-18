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
        return None


def delete_menu_with_label(label, window=MAYA_WINDOW):
    menu = get_menu_with_label(label)
    while menu:
        mc.deleteUI(menu)
        menu = get_menu_with_label(label)


def create(name, items, append=True):
    if mc.about(batch=True):
        return
    menu = None
    if append:
        menu = get_menu_with_label(name)
    else:
        delete_menu_with_label(name, MAYA_WINDOW)
    if not menu:
        menu = mc.menu(label=name, parent=MAYA_WINDOW, tearOff=True)
    for menu_item in items:
        add_menu_item(menu_item, menu)


create_maya_menu = create  # for backwards compatibility


if __name__ == '__main__':
    def create_cube(maya_useless_ui_arg=None):
        mc.polyCube()

    EXAMPLE_MENU = [
        dict(
            label="farm_launcher",
            icon="shelves/farm_launcher.png",
            command='print "test"'),
        dict(
            label="asset_getter",
            icon="shelves/asset_getter.png",
            command=create_cube),
        dict(
            label="asset_committer",
            icon="shelves/asset_committer.png",
            command='print "test"'),
        SEPARATOR,
        dict(
            label="create cube",
            icon="cube.png",
            command=create_cube),
        dict(
            label="submenu",
            icon="shelves/playblast2.png",
            command=[
                dict(label='first menu item',
                     command='import maya.cmds as mc;mc.polyCube()'),
                SEPARATOR,
                dict(label='mc.polyCube',
                     command=create_cube)]),
        dict(
            label="submenu 2",
            icon="shelves/arnoldLightRig.png",
            command=[
                dict(label='first menu item',
                     command=create_cube),
                dict(label='another menu item',
                     command=create_cube)])]

    create('Example menu', EXAMPLE_MENU, append=False)

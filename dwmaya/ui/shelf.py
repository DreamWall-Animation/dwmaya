"""
Module to create and delete shelf tabs.

See the create_shelf doctstring and EXAMPLE_SHELF below for how to use.
Features:
    - Python and mel commands.
    - Python commands can be strings or executable objects.
    - Left and right mouse button menus.
    - Register multiple shelves at same time and manage visibilities
"""

__author__ = 'Olivier Evers', 'Lionel Brouyere'
__copyright__ = 'DreamWall'
__license__ = 'MIT'


from collections import OrderedDict
from copy import deepcopy
import maya.cmds as mc
import maya.mel as mm


DEFAULT_SHELF = 'dwmaya_shelf_default'
SHELVES_TO_LOAD = 'dwmaya_shelves_to_load'
SHELF_LAYOUT = 'ShelfLayout'
SEPARATOR = 'shelf_separator'
LEFT_BUTTON = 1  # LMB = left mouse button
RIGHT_BUTTON = 3  # RMB = right mouse button
KWARGS_MATCHES = {
    'command': 'command',
    'double_click': 'doubleClickCommand',
    'source_type': 'sourceType',
    'tooltip': 'annotation',
    'label': 'imageOverlayLabel',
    'repeatable': 'commandRepeatable',
    'color': 'backgroundColor'
}


_shelves = OrderedDict()


# Modified version of deleteShelfTab to delete without confirmDialog:
mm.eval('''
global proc int deleteShelfTabNoUI(string $shelfName)
{
    if (!`layout -q -exists $shelfName`) return 0;

    global string $gShelfForm;
    global string $gShelfTopLevel;

    setParent $gShelfTopLevel;
    string $shelves[] = `tabLayout -q -ca $gShelfTopLevel`;
    int $numShelves = size($shelves);

    int $indexArr[];
    int $index = 0;
    int $nItems = 0;

    if ($numShelves <= 0) return 0;

    if(!`exists shelfLabel_melToUI` ){
        source "shelfLabel.mel";
    }

    int $i = 0;
    int $nShelves = 0;
    int $shelfNum = 0;

    $nShelves = `shelfTabLayout -q -numberOfChildren $gShelfTopLevel`;
    for ($shelfNum = 1; $shelfNum <= $nShelves; $shelfNum++) {
        if ($shelfName == `optionVar -q ("shelfName" + $shelfNum)`) {
            break;
        }
    }
    for ($i = $shelfNum; $i <= $nShelves; $i++) {
        string $align = "left";
        if ( `optionVar -ex ("shelfAlign" + ($i+1))` )
            $align = `optionVar -q ("shelfAlign" + ($i+1))`;
        optionVar
            -iv ("shelfLoad" + $i) `optionVar -q ("shelfLoad" + ($i+1))`
            -sv ("shelfName" + $i) `optionVar -q ("shelfName" + ($i+1))`
            -sv ("shelfAlign" + $i) $align
            -sv ("shelfFile" + $i) `optionVar -q ("shelfFile" + ($i+1))`;
    }
    optionVar -remove ("shelfLoad" + $nShelves)
        -remove ("shelfName" + $nShelves)
        -remove ("shelfAlign" + $nShelves)
        -remove ("shelfFile" + $nShelves);

    deleteUI -layout ($gShelfTopLevel + "|" + $shelfName);

    string $shelfDirs = `internalVar -userShelfDir`;
    string $shelfArray[];
    string $PATH_SEPARATOR = `about -win`? ";" : ":";
    tokenize($shelfDirs, $PATH_SEPARATOR, $shelfArray);
    for( $i = 0; $i < size($shelfArray); $i++ ) {
        $fileName = ($shelfArray[$i] + "shelf_" + $shelfName + ".mel");
        string $deletedFileName = $fileName + ".deleted";

        if (`filetest -r $deletedFileName`) {
            sysFile -delete $deletedFileName;
        }

        //if (`file -q -exists $fileName`) {
        //    sysFile -rename $deletedFileName $fileName;
        //    break;
        //}
    }

    shelfTabChange();
    return 1;
}''')

# Modified version of addNewShelfTab to avoid extra shelf file:
mm.eval('''
global proc string addNewShelfTab2(string $newName) {
    global string $gShelfForm;
    global string $gShelfTopLevel;

    string $shelfName;
    string $shelves[];
    int $shelfHeight, $nShelves;

    setParent $gShelfTopLevel;
    $shelfHeight = `tabLayout -q -h $gShelfTopLevel`;
    tabLayout -e -visible false $gShelfTopLevel;

    setParent $gShelfForm;
    separator -h $shelfHeight -style "single" spacingSeparator;

    formLayout -e
        -af spacingSeparator top 0
        -af spacingSeparator left 0
        -af spacingSeparator bottom 0
        -af spacingSeparator right 0
        $gShelfForm;

    tabLayout -e -manage false $gShelfTopLevel;
    setParent $gShelfTopLevel;

    string $newShelfName;
    if ($newName == "") {
        $newShelfName = `shelfLayout`;
    } else {
        $newShelfName = `shelfLayout $newName`;
    }

    // Match the style of the other tabs
    string $style = `getShelfStyle($gShelfTopLevel)`;
    shelfStyle $style "Small" $newShelfName;

    tabLayout -e -manage true -visible true $gShelfTopLevel;

    $shelves = `tabLayout -q -ca $gShelfTopLevel`;
    $shelfName = $shelves[size($shelves)-1];

    if(!`exists shelfLabel_melToUI` ){
        source "shelfLabel.mel";
    }

    // If the user has created a new shelf with the same name as the
    // default shelves like Animation, Curves, Surfaces, Polygons ...,
    // edit the tab label to set the localized name in the UI
    shelfTabLayout -edit
        -tabLabel $shelfName (shelfLabel_melToUI($shelfName)) $gShelfTopLevel;

    deleteUI spacingSeparator;

    $nShelves = `shelfTabLayout -q -numberOfChildren $gShelfTopLevel`;
    optionVar -iv ("shelfLoad" + $nShelves) 0;
    optionVar -sv ("shelfName" + $nShelves) $shelfName;
    optionVar -sv ("shelfFile" + $nShelves) ("shelf_" + $shelfName);
    optionVar -sv ("shelfAlign" + $nShelves) "left";

    tabLayout -e -selectTab $shelfName $gShelfTopLevel;

    // Set the current shelf option var
    int $shelfNum = `tabLayout -q -sti $gShelfTopLevel`;
    optionVar -iv selectedShelf $shelfNum;

    return $shelfName;
}
''')


def delete(shelf_name):
    mm.eval('deleteShelfTabNoUI("%s")' % shelf_name)


def get_existing_shelf_tabs():
    return mc.shelfTabLayout(SHELF_LAYOUT, query=True, childArray=True) or []


def set_current_tab(tab, ignore_case=True):
    if ignore_case:
        tab = [
            t for t in get_existing_shelf_tabs() if t.lower() == tab.lower()]
        if not tab:
            return
        tab = tab[0]
    mc.shelfTabLayout(SHELF_LAYOUT, edit=True, selectTab=tab)


def create(name, shelf_buttons):
    """
    shelf_buttons: list of dicts with following keys:
        - icon: icon path
        - command: command to run. Optional if there is a menu on LMB.
        - double_click: command run on double click.
        - separator: optional, will ignore all other arguments and add a |.
        - label: optional, add a label to the shelf button.
        - source_type: optional, will be python by default
        - tooltip: optional tooltip string
        - repeatable: command repeatable (default Maya "G" hotkey).
        - menu: optional. Will create a right click menu.
            List of dict with: label, command, source_type, tooltip.
    """
    # Delete and re-create
    delete(name)
    # mm.eval('addNewShelfTab2("%s")' % name)
    mc.shelfLayout(name, parent=SHELF_LAYOUT)

    # Fill the shelf
    for btn in shelf_buttons:
        if btn == SEPARATOR:
            mc.shelfButton(
                parent=name, image='shelf_separator.png', width=13)
            continue

        # Create the shelf button
        kwargs = dict(parent=name, image=btn['icon'])
        for kwarg, maya_kwarg in KWARGS_MATCHES.items():
            if kwarg in btn:
                kwargs[maya_kwarg] = btn[kwarg]
        shelf_button = mc.shelfButton(**kwargs)

        # Create menu if there is one
        if 'menu' in btn:
            menu = btn['menu']
            mouse_button = btn.get('menu_button') or 3
            create_menu(menu, mouse_button, btn.get('command'), shelf_button)

    # Adapt shelves optionVar's
    shelf_index = mc.shelfTabLayout(
        SHELF_LAYOUT, query=True, numberOfChildren=True) + 1
    mc.optionVar(stringValue=('shelfName%i' % shelf_index, name))
    mc.optionVar(stringValue=('shelfFile%i' % shelf_index, 'shelf_' + name))
    mc.optionVar(intValue=('shelfLoad%i' % shelf_index, 1))
    mc.optionVar(intValue=('numShelves', shelf_index))

    # Switch to shelf
    mc.shelfTabLayout('ShelfLayout', edit=True, selectTab=name)


def create_menu(menu, mouse_button, command, shelf_button):
    """
    - menu: optional. Will create a right click menu.
        List of dict with: label, command, source_type, tooltip.
    """
    if mouse_button == 1 and command:
        raise ValueError(
            'You cannot have both a left mouse button menu and a '
            'shelf button command.')

    # HACK: the command menuItem's flag -sourceType is fucked up.
    # It will always evaluate in Mel whatever the option set.
    # This will will embed the given command in a python() proc.
    menu = deepcopy(menu)
    for item in menu:
        if item.get('source_type') == 'python':
            item['command'] = 'python("{}")'.format(item['command'])

    if mouse_button == 1:
        popup_menu = mc.popupMenu(
            button=1, itemArray=True, parent=shelf_button)

        for item in menu:
            if item == SEPARATOR:
                mc.menuItem(divider=True)
                continue
            kwargs = dict(
                parent=popup_menu,
                label=item['label'],
                command=item['command'])
            mc.menuItem(**kwargs)

    elif mouse_button == 3:
        if SEPARATOR in menu:
            msg = 'You cannot add separator in right button shelf menu.'
            raise ValueError(msg)
        items = [(i['label'], i['command']) for i in menu]
        python_items = [int(i.get('source_type') != 'mel') for i in menu]
        mc.shelfButton(shelf_button, edit=True, menuItem=items)
        # menuItemPython cannot be set at the same time as menuItem.
        mc.shelfButton(shelf_button, edit=True, menuItemPython=python_items)


def register(name, shelf):
    _shelves[name] = shelf


def registered_shelves():
    return _shelves


def update():
    if mc.optionVar(exists=SHELVES_TO_LOAD):
        shelves_to_load = mc.optionVar(query=SHELVES_TO_LOAD).split(',')
    else:
        shelves_to_load = None

    for name, shelf in _shelves.items():
        if shelves_to_load is None or name in shelves_to_load:
            create(name, shelf)
        else:
            delete(name)

    if mc.optionVar(exists=DEFAULT_SHELF):
        set_current_tab(mc.optionVar(query=DEFAULT_SHELF))


if __name__ == '__main__':

    def create_cube(maya_useless_ui_arg=None):
        mc.polyCube()

    EXAMPLE_SHELF = [
        dict(
            tooltip="farm_launcher",
            icon="shelves/farm_launcher.png",
            command='print "test"'),
        dict(
            tooltip="asset_getter",
            icon="shelves/asset_getter.png",
            command=create_cube),  # example of python executable
        dict(
            tooltip="asset_committer",
            icon="shelves/asset_committer.png",
            command='print "test"'),
        SEPARATOR,
        dict(
            tooltip="create cube",
            icon="cube.png",
            command='polyCube',  # example of mel command
            source_type='mel'),
        dict(
            tooltip="left click menu",
            icon="shelves/playblast2.png",
            menu_button=LEFT_BUTTON,  # example of left click menu
            menu=[
                dict(label='first menu item',
                     command='import maya.cmds as mc;mc.polyCube()'),
                SEPARATOR,
                dict(label='mc.polyCube',
                     command=create_cube)]),
        dict(
            tooltip="left click menu",
            icon="shelves/arnoldLightRig.png",
            command='print "test"',
            menu_button=RIGHT_BUTTON,  # example of right click menu
            menu=[
                dict(label='first menu item',
                     command='polyCube',
                     source_type='mel'),
                dict(label='another menu item',
                     command='polyCube',
                     source_type='mel')])]

    create('Example', EXAMPLE_SHELF)

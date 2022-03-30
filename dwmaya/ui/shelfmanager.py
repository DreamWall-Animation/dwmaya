"""
Ui to manage custom shelves registered.
"""

__author__ = 'Olivier Evers', 'Lionel Brouyere'
__copyright__ = 'DreamWall'
__license__ = 'MIT'


import maya.cmds as mc
from PySide2 import QtWidgets, QtCore
from dwmaya.ui.qt import get_maya_window
from dwmaya.ui.shelf import (
    registered_shelves, update, DEFAULT_SHELF, SHELVES_TO_LOAD)


class ShelfUi(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(ShelfUi, self).__init__(parent, QtCore.Qt.Tool)
        self.setWindowTitle('Shelf Manager')
        self.checkboxes = []
        self.radiobuttons = []
        self.buttongroup = QtWidgets.QButtonGroup()
        self.buttongroup.buttonReleased.connect(self.value_changed)

        self.items_layout = QtWidgets.QGridLayout()
        self.items_layout.addWidget(QtWidgets.QLabel('Default'), 0, 0)
        self.items_layout.addWidget(QtWidgets.QLabel('Loaded'), 0, 1)
        self.items_layout.addWidget(QtWidgets.QLabel('Shelf'), 0, 2)

        for i, name in enumerate(registered_shelves().keys()):
            radio = QtWidgets.QRadioButton('')
            checkbox = QtWidgets.QCheckBox('')
            checkbox.released.connect(self.value_changed)
            self.radiobuttons.append(radio)
            self.checkboxes.append(checkbox)
            self.buttongroup.addButton(radio, i)
            self.items_layout.addWidget(radio, i + 1, 0)
            self.items_layout.addWidget(checkbox, i + 1, 1)
            self.items_layout.addWidget(QtWidgets.QLabel(name), i + 1, 2)

        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.addLayout(self.items_layout)
        self.set_ui_states()

    def set_ui_states(self):
        if mc.optionVar(exists=DEFAULT_SHELF):
            default = mc.optionVar(query=DEFAULT_SHELF)
            try:
                shelves = registered_shelves()
                index = [str(k) for k in shelves.keys()].index(default)
                self.buttongroup.button(index).setChecked(True)
            except ValueError:
                msg = 'Default shelf: "{}" is not registered'.format(default)
                mc.warning(msg)
                mc.optionVar(remove=DEFAULT_SHELF)
        if mc.optionVar(exists=SHELVES_TO_LOAD):
            shelves_to_load = mc.optionVar(query=SHELVES_TO_LOAD).split(',')
            for i, name in enumerate(registered_shelves()):
                if name in shelves_to_load:
                    self.checkboxes[i].setChecked(True)

    def value_changed(self, *_):
        shelves_to_load = []
        for i, name in enumerate(registered_shelves().keys()):
            if self.buttongroup.checkedId() == i:
                mc.optionVar(stringValue=[DEFAULT_SHELF, name])
            if self.checkboxes[i].isChecked():
                shelves_to_load.append(name)
        mc.optionVar(stringValue=[SHELVES_TO_LOAD, ','.join(shelves_to_load)])
        update()


_shelf_ui = None


def show_shelf_ui():
    global _shelf_ui
    if _shelf_ui is None:
        _shelf_ui = ShelfUi(parent=get_maya_window())
    _shelf_ui.show()


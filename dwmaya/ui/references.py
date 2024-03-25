import os
from functools import partial

from PySide2 import QtWidgets, QtCore, QtGui
from PySide2.QtGui import QShowEvent

import maya.cmds as mc

from dwmaya.reference import get_references, get_reference_path
from dwmaya.ui.qt import get_maya_window


class ReferencesLister(QtWidgets.QTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent or get_maya_window())
        self.setWindowFlags(QtCore.Qt.Window)

        self.setWindowTitle('References lister')
        self.setSortingEnabled(True)
        self.setSelectionBehavior(self.SelectRows)
        self.setMinimumWidth(800)
        self.setVerticalScrollMode(self.ScrollPerPixel)
        self.setHorizontalScrollMode(self.ScrollPerPixel)

        self.menu = QtWidgets.QMenu()
        load_action = QtWidgets.QAction(
            'Load selected references', self.menu)
        load_action.triggered.connect(self.load_selection)
        self.menu.addAction(load_action)
        unload_action = QtWidgets.QAction(
            'Unload selected references', self.menu)
        unload_action.triggered.connect(self.unload_selection)
        self.menu.addAction(unload_action)


    def fill(self):
        self.clear()
        reference_nodes = get_references()
        self.setRowCount(len(reference_nodes))
        self.setColumnCount(5)
        self.setHorizontalHeaderLabels([
            '', 'namespace', 'node', 'file name', 'file path'])
        for i, ref_node in enumerate(reference_nodes):
            loaded = mc.referenceQuery(ref_node, isLoaded=True)
            cb = QtWidgets.QCheckBox(
                checked=loaded, styleSheet='margin-left: 10px')
            cb.stateChanged.connect(partial(self.set_load_state, ref_node))
            self.setCellWidget(i, 0, cb)

            try:
                namespace = mc.referenceQuery(ref_node, namespace=True)
            except RuntimeError:
                namespace = ' - '
            item = QtWidgets.QTableWidgetItem(f' {namespace[1:]} ')
            self.setItem(i, 1, item)

            item = QtWidgets.QTableWidgetItem(f' {ref_node} ')
            self.setItem(i, 2, item)
            path = get_reference_path(ref_node)
            item = QtWidgets.QTableWidgetItem(f' {os.path.basename(path)} ')
            self.setItem(i, 3, item)
            item = QtWidgets.QTableWidgetItem(f' {path} ')
            self.setItem(i, 4, item)

        self.resizeColumnsToContents()

    def set_load_state(self, refnode, load):
        load = bool(load)
        if load:
            mc.file(loadReference=refnode)
        else:
            mc.file(unloadReference=refnode, force=True)

    def set_selection_load_state(self, load):
        rows = {i.row() for i in self.selectedIndexes()}
        for row in rows:
            refnode = self.item(row, 2).text().strip()
            print(refnode, load)
            self.set_load_state(refnode, load)
        self.fill()

    def load_selection(self):
        self.set_selection_load_state(load=True)

    def unload_selection(self):
        self.set_selection_load_state(load=False)

    def mousePressEvent(self, event):
        if event.type() == QtCore.QEvent.MouseButtonPress:
            if event.button() == QtCore.Qt.RightButton:
                self.menu.popup(QtGui.QCursor.pos())
        return super().mousePressEvent(event)

    def showEvent(self, event: QShowEvent) -> None:
        self.fill()
        return super().showEvent(event)


if __name__ == '__main__':
    widget = ReferencesLister()
    widget.show()

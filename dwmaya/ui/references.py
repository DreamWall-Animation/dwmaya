import os
from functools import partial

from PySide2 import QtWidgets, QtCore
from PySide2.QtGui import QShowEvent

import maya.cmds as mc

from dwmaya.reference import get_references, get_reference_path
from dwmaya.ui.qt import get_maya_window


class ReferencesLister(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent or get_maya_window())
        self.setWindowFlags(QtCore.Qt.Window)

        self.setWindowTitle('References lister')
        self.table = QtWidgets.QTableWidget(sortingEnabled=True)
        self.setMinimumWidth(800)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.table)

    def fill(self):
        self.table.clear()
        reference_nodes = get_references()
        self.table.setRowCount(len(reference_nodes))
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            '', 'namespace', 'node', 'file name', 'file path'])
        for i, ref_node in enumerate(reference_nodes):
            loaded = mc.referenceQuery(ref_node, isLoaded=True)
            cb = QtWidgets.QCheckBox(checked=loaded)
            cb.stateChanged.connect(partial(self.set_load_state, ref_node))
            self.table.setCellWidget(i, 0, cb)

            try:
                namespace = mc.referenceQuery(ref_node, namespace=True)
            except RuntimeError:
                namespace = ' - '
            item = QtWidgets.QTableWidgetItem(f' {namespace[1:]} ')
            self.table.setItem(i, 1, item)

            item = QtWidgets.QTableWidgetItem(f' {ref_node} ')
            self.table.setItem(i, 2, item)
            path = get_reference_path(ref_node)
            item = QtWidgets.QTableWidgetItem(f' {os.path.basename(path)} ')
            self.table.setItem(i, 3, item)
            item = QtWidgets.QTableWidgetItem(f' {path} ')
            self.table.setItem(i, 4, item)

        self.table.resizeColumnsToContents()

    def set_load_state(self, refnode, load):
        load = bool(load)
        if load:
            mc.file(loadReference=refnode)
        else:
            mc.file(unloadReference=refnode, force=True)

    def showEvent(self, event: QShowEvent) -> None:
        self.fill()
        return super().showEvent(event)


if __name__ == '__main__':
    widget = ReferencesLister()
    widget.show()
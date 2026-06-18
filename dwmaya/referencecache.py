import os
from functools import lru_cache
from datetime import datetime
from PySide2 import QtWidgets, QtCore, QtGui
import maya.cmds as mc

from dwmaya.ui.qt import get_maya_window
from dwmaya.plugins import ensure_plugin_loaded
from dwmaya.reference import get_reference_root_nodes


@lru_cache()
def get_color_icon(color, size=None, as_pixmap=False):
    px = QtGui.QPixmap(QtCore.QSize(*(size if size else (60, 60))))
    px.fill(QtCore.Qt.transparent)
    painter = QtGui.QPainter(px)
    painter.setPen(QtCore.Qt.NoPen)
    painter.setBrush(QtGui.QColor(color))
    painter.drawEllipse(0, 0, px.size().width(), px.size().height())
    painter.end()
    if as_pixmap:
        return px
    return QtGui.QIcon(px)


def cache_to_reference(node: str):
    is_locked = mc.lockNode(node, query=True, lock=True)[0]
    if is_locked:
        mc.lockNode(node, lock=False)

    mc.delete(mc.getAttr(f'{node}.gpuCache'))
    mc.deleteAttr(f'{node}.gpuCache')
    mc.file(mc.referenceQuery(
        node, filename=True), loadReference=True)

    if is_locked:
        mc.lockNode(node, lock=True)


@ensure_plugin_loaded('gpuCache')
def reference_to_cache(ref_nodes: list, force=False):
    scene_file = mc.file(query=True, sceneName=True)
    scene_path = os.path.dirname(scene_file)
    cache_dir = os.path.join(scene_path, 'cache')
    os.makedirs(cache_dir, exist_ok=True)

    # Create a dictionnary that links reference nodes with actual exports node
    refs_nodes_filepaths = {}
    export_nodes = []
    existing_cache_files = os.listdir(os.path.join(scene_path, 'cache'))
    for ref_node in ref_nodes:
        for export_node in get_reference_root_nodes(ref_node):
            export_node_sn = export_node.split('|')[-1]
            file_name = export_node_sn.replace(':', '_') + '.abc'
            refs_nodes_filepaths[ref_node] = export_node_sn, file_name
            # Skip if cache exists
            if force or file_name not in existing_cache_files:
                export_nodes.append(export_node)

    # Export cache
    if export_nodes:
        playback_start = mc.playbackOptions(
            query=True, animationStartTime=True)
        playback_end = mc.playbackOptions(
            query=True, animationEndTime=True)
        mc.gpuCache(
            export_nodes,
            startTime=playback_start,
            endTime=playback_end,
            optimize=True,
            writeUVs=True,
            writeMaterials=True,
            directory=cache_dir,
            saveMultipleFiles=True)

    # Create attribute linking things and cache object, then unload reference
    for ref_node, (parent, filename) in refs_nodes_filepaths.items():
        is_locked = mc.lockNode(ref_node, query=True, lock=True)[0]
        if is_locked:
            mc.lockNode(ref_node, lock=False)
        mc.addAttr(ref_node, longName='gpuCache', dataType="string")
        mc.setAttr(
            f'{ref_node}.gpuCache', str(f'{parent}Cache'), type="string")
        if is_locked:
            mc.lockNode(ref_node, lock=True)

        transform_cache_node = mc.createNode(
            'transform', name=f'{parent}Cache', parent=None)
        cache_node = mc.createNode(
            'gpuCache', name=f'{parent}CacheShape',
            parent=transform_cache_node)
        mc.setAttr(
            f'{cache_node}.cacheFileName',
            os.path.join(scene_path, 'cache', filename),
            type="string")

        try:
            mc.file(
            mc.referenceQuery(ref_node, filename=True), unloadReference=True)
        except:
            mc.warning(f"Could not unload reference {ref_node}")


class TableWidget(QtWidgets.QTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.menu = None
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.horizontalHeader().setStretchLastSection(True)

        self.setColumnCount(3)
        self.setColumnWidth(0, 225)

    def get_context_menu_position(self, index):
        header = self.horizontalHeader()
        x = header.sectionViewportPosition(index.column())
        x = header.mapToGlobal(QtCore.QPoint(x, 0)).x()

        if index.row() + 1 == self.rowCount():
            last_row = self.rowCount() - 1
            y = self.rowViewportPosition(last_row) + self.rowHeight(last_row)
        else:
            y = self.verticalHeader().sectionViewportPosition(index.row() + 1)

        y = self.verticalHeader().mapToGlobal(QtCore.QPoint(0, y)).y()
        return QtCore.QPoint(x, y)

    def exec_context_menu(self, pos):
        selected_indexes = self.selectionModel().selectedRows()
        if not selected_indexes:
            return

        selected_asset_names = [
            self.item(idx.row(), 0).text() for idx in selected_indexes]
        last_asset_name = selected_asset_names[-1]

        self.menu = QtWidgets.QMenu(self)

        action_to_cache = QtWidgets.QAction("Convert Selection to Cache", self)
        action_to_cache.triggered.connect(
            lambda: reference_to_cache(selected_asset_names, force=False))
        self.menu.addAction(action_to_cache)

        action_to_force_cache = QtWidgets.QAction(
            "Convert Selection to Cache and Force Recache", self)
        action_to_force_cache.triggered.connect(
            lambda: reference_to_cache(selected_asset_names, force=True))
        self.menu.addAction(action_to_force_cache)

        action_to_ref = QtWidgets.QAction(
            f"Convert '{last_asset_name}' to Reference", self)
        action_to_ref.triggered.connect(
            lambda: cache_to_reference(last_asset_name))
        self.menu.addAction(action_to_ref)

        if isinstance(self.window(), ReferenceCacherWidget):
            action_to_cache.triggered.connect(self.window().refresh_model)
            action_to_ref.triggered.connect(self.window().refresh_model)
            action_to_force_cache.triggered.connect(
                self.window().refresh_model)

        self.menu.exec_(pos)

    def selected_row_index(self):
        selected = self.selectionModel().selectedRows()
        return selected[-1] if selected else None

    def mousePressEvent(self, event):
        if event.button() != QtCore.Qt.RightButton:
            return super().mousePressEvent(event)

        idx = self.selected_row_index()
        if idx:
            pos = self.get_context_menu_position(idx)
            self.exec_context_menu(pos)


class ReferenceCacherWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QtWidgets.QVBoxLayout(self)
        self.view = TableWidget()
        layout.addWidget(self.view)

        self.refresh_model()

        self.setWindowTitle('Cache Switch')
        self.setWindowFlags(QtCore.Qt.Tool)

    def sizeHint(self):
        return QtCore.QSize(560, 300)

    def get_selected_nodes(self):
        sl = self.view.selectionModel().selectedRows()
        return [(idx.row(), self.view.item(idx.row(), 0).text()) for idx in sl]

    def on_cache_clicked(self):
        nodes = []
        for row, node in self.get_selected_nodes():
            if not self.view.item(row, 1).text() == 'GPU Cache':
                nodes.append(node)
        reference_to_cache(sorted(nodes))
        self.refresh_model()

    def on_reference_clicked(self):
        for row, node in self.get_selected_nodes():
            if not self.view.item(row, 1).text() == 'Reference':
                cache_to_reference(node)
        self.refresh_model()

    def refresh_model(self):
        headers = ['Asset Name', 'Status', 'Last Cache Date']
        scene_path = os.path.dirname(mc.file(query=True, sceneName=True))
        assets = [[r, 'Reference'] for r in sorted(mc.ls(references=True))]
        cached_files = os.listdir(os.path.join(scene_path, 'cache'))

        for asset in assets:
            ref_node = asset[0]
            if mc.attributeQuery('gpuCache', node=ref_node, exists=True):
                asset[1] = 'GPU Cache'
                cache_node = mc.getAttr(f'{ref_node}.gpuCache') + 'Shape'
                cache_path = mc.getAttr(f'{cache_node}.cacheFileName')
                cache_file = cache_path.split('/')[-1]

            else:
                for i in get_reference_root_nodes(ref_node):
                    long_name_cache_file = f"{i.replace(':','_')}.abc"
                    cache_file = long_name_cache_file.split('|')[-1]

            if cache_file in cached_files:
                file_path = os.path.join(scene_path, 'cache', cache_file)
                date = os.stat(file_path).st_mtime
                asset.append(str(datetime.fromtimestamp(date))[:-4])

            else:
                asset.append('Not cached yet')

        self.view.setRowCount(0)
        self.view.setHorizontalHeaderLabels(headers)
        self.view.setRowCount(len(assets))

        for row_idx, (asset, status, date) in enumerate(assets):
            item = QtWidgets.QTableWidgetItem(asset)
            item.setFlags(item.flags() ^ QtCore.Qt.ItemIsEditable)
            self.view.setItem(row_idx, 0, item)

            item = QtWidgets.QTableWidgetItem(status)
            item.setFlags(item.flags() ^ QtCore.Qt.ItemIsEditable)
            self.view.setItem(row_idx, 1, item)

            item = QtWidgets.QTableWidgetItem(date)
            item.setIcon(get_color_icon(
                'green' if date != 'Not cached yet' else 'gray'))
            item.setFlags(item.flags() ^ QtCore.Qt.ItemIsEditable)
            self.view.setItem(row_idx, 2, item)

            self.view.setVerticalHeaderItem(
                row_idx, QtWidgets.QTableWidgetItem(str(row_idx + 1)))

        self.update()


_cache_manager_window = None


def show_cache_manager():
    global _cache_manager_window
    if _cache_manager_window is not None:
        _cache_manager_window.close()
    _cache_manager_window = ReferenceCacherWidget(get_maya_window())
    _cache_manager_window.show()


if __name__ == '__main__':
    show_cache_manager()

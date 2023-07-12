__author__ = 'Olivier Evers'
__copyright__ = 'DreamWall'
__license__ = 'MIT'


import os
import shiboken2
from functools import partial
from contextlib import contextmanager

from PySide2 import QtWidgets, QtCore, QtGui

import maya.cmds as mc
import maya.OpenMayaUI as omui


POPUP_STYLESHEET = 'QMessageBox{font: 15px;} QLabel{min-width: 500px;}'


def _warn_popup(title, text):
    mc.warning('[dw] %s: %s' % (title, text))
    QtWidgets.QMessageBox(
        text=text, windowTitle=title,
        standardButtons=QtWidgets.QMessageBox.Ok,
        styleSheet=POPUP_STYLESHEET).exec_()


def warn_popup(title, text):
    # USD were prevented to load at scene opening before use of evalDeferred:
    cmd = partial(_warn_popup, title, text)
    mc.evalDeferred(cmd, lowestPriority=True)


def input_popup(text, value=''):
    prompt = QtWidgets.QInputDialog(
        labelText=text, styleSheet='QLabel{font: 15px;}', textValue=value)
    prompt.exec_()
    return prompt.textValue()


def choice_prompt(text, title='', batch=None):
    if mc.about(batch=True) and batch is not None:
        return batch
    prompt = QtWidgets.QMessageBox(
        windowTitle=title, text=text, standardButtons=(
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No),
        styleSheet=POPUP_STYLESHEET)
    prompt.setDefaultButton(QtWidgets.QMessageBox.No)
    if prompt.exec_() == QtWidgets.QMessageBox.No:
        return False
    else:
        return True


def chose_from_list_prompt(choices, text='', position=None, buttons_height=21):
    dialog = QtWidgets.QDialog()
    dialog.setWindowFlags(QtCore.Qt.CustomizeWindowHint)
    dialog.setMaximumWidth(1500)

    scroll_panel = QtWidgets.QWidget()
    scroll_panel.setMaximumWidth(1500)
    scroll_panel_layout = QtWidgets.QVBoxLayout(scroll_panel)
    scroll_panel_layout.setContentsMargins(0, 0, 0, 0)
    scroll_panel_layout.setSpacing(0)
    scroll_area = QtWidgets.QScrollArea()
    scroll_area.setWidgetResizable(True)
    scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
    scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
    scroll_area.setWidget(scroll_panel)
    scroll_area.setMaximumWidth(2000)

    layout = QtWidgets.QVBoxLayout()
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)
    dialog.setLayout(layout)
    if text:
        layout.addWidget(QtWidgets.QLabel(text))
    layout.addWidget(scroll_area)

    chosen_value = []
    for choice in choices:
        if isinstance(choice, tuple):
            label, value = choice
        else:
            label, value = choice, choice
        button = QtWidgets.QPushButton(label)
        button.clicked.connect(dialog.accept)
        button.clicked.connect(partial(chosen_value.append, value))
        button.setMaximumHeight(buttons_height)
        scroll_panel_layout.addWidget(button)

    button = QtWidgets.QPushButton(
        'Cancel', styleSheet='background-color:#373737')
    button.setMaximumHeight(buttons_height)
    button.clicked.connect(dialog.accept)
    scroll_panel_layout.addWidget(button)
    scroll_panel_layout.addStretch()

    if not position:
        position = QtGui.QCursor.pos()
    dialog.move(position)
    dialog.exec_()
    if chosen_value:
        return chosen_value[0]


def get_maya_window():
    """
    Get the main Maya window as a QtGui.QMainWindow instance
    @return: QtGui.QMainWindow instance of the top level Maya windows
    """
    if os.name == 'posix':
        return None
    ptr = omui.MQtUtil.mainWindow()
    if ptr is not None:
        return shiboken2.wrapInstance(int(ptr), QtWidgets.QWidget)


def center_on_maya_window(widget):
    offset_x = widget.rect().width() / 2
    offset_y = widget.rect().height() / 2
    window = get_maya_window()
    center = window.mapToGlobal(window.rect().center())
    widget.move(center.x() - offset_x, center.y() - offset_y)


def get_screen_size():
    rect = QtWidgets.QDesktopWidget().screenGeometry(-1)
    scale = 96 / QtWidgets.QApplication.primaryScreen().logicalDotsPerInch()
    return [int(rect.width() * scale), int(rect.height() * scale)]


def restore_windows_positions():
    windows = [
        'outlinerPanel1Window', 'hyperGraphPanel1Window', 'graphEditor1Window',
        'timeEditorPanel1Window', 'dopeSheetPanel1Window',
        'nodeEditorPanel1Window', 'shapePanel1Window', 'posePanel1Window',
        'clipEditorPanel1Window', 'devicePanel1Window',
        'hyperShadePanel1Window', 'dynPaintScriptedPanelWindow',
        'blindDataEditor1Window', 'polyTexturePlacementPanel1Window',
        'contentBrowserPanel1Window', 'NewFeatureHighlightWnd', 'shelfEditor',
        'PreferencesWindow', 'panelArrangementWin', 'pluginManagerWindow',
        'Viewport20OptionsWindow', 'OptionBoxWindow']
    for window in windows:
        if not mc.window(window, query=True, exists=True):
            continue
        mc.window(window, edit=True, tlc=(100, 100))


@contextmanager
def waitcursor_ctx():
    QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
    try:
        yield None
    finally:
        QtWidgets.QApplication.restoreOverrideCursor()


STATIC_TEXT_TPL = (
    '<div style="font-size: {size}pt; color: #858585"><b>No Image</b></div>')


def no_image_pixmap(size):
    try:
        pixmap = QtGui.QPixmap(*size)
        painter = QtGui.QPainter(pixmap)
        pixmap.fill(QtGui.QColor(30, 30, 30, 255))

        pen = QtGui.QPen(QtGui.QColor(50, 50, 50, 255))
        painter.setPen(pen)
        offset_x, offset_y = size[0] / 10, size[1] / 10

        painter.drawLine(
            offset_x, offset_y, size[0] - offset_x, size[1] - offset_y)
        painter.drawLine(
            size[0] - offset_x, offset_y, offset_x, size[1] - offset_y)

        tsize = int(min([size[0] / size[1], size[1] / size[0]]) * 18)
        text = STATIC_TEXT_TPL.format(size=tsize)
        statictext = QtGui.QStaticText(text)
        x = (size[0] / 2) - (statictext.size().width() / 2)
        y = (size[1] / 2) - (statictext.size().height() / 2)

        painter.setPen(QtCore.Qt.transparent)
        painter.setBrush(QtGui.QColor(30, 30, 30, 255))
        painter.drawRect(
            int(size[0] / 2 - statictext.size().width() / 2),
            int(size[1] / 2 - statictext.size().height() / 2),
            statictext.size().width(),
            statictext.size().height())

        painter.drawStaticText(int(x), int(y), statictext)
    finally:
        painter.end()
    return pixmap

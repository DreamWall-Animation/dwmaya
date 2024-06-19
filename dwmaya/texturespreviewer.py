import os
from PySide2 import QtWidgets, QtCore
import maya.cmds as mc
from dwmaya.attributes import set_attr
from dwmaya.shading import (
    assign_material,
    create_material,
    get_shape_shading_engine,
    set_texture,
    list_texture_filepaths)
from dwmaya.ui.qt import get_maya_window
from dwmaya.mesh import create_clean_copies, selected_meshes
from dwmaya.selection import (
    preserve_selection,
    selection_contains_at_least,
    select_transform_shapes)
from dwmaya.viewport import isolate_nodes, unisolate_active_view


DEFAULT_EXPOSURE = 'texture_previewer_default_exposure'


@preserve_selection
@select_transform_shapes
@selection_contains_at_least(1, 'mesh')
def create_texture_preview_setup(meshes):
    original_shading_engines = set()
    copies = []
    for mesh in meshes:
        original_shading_engines.add(get_shape_shading_engine(mesh))
        mesh_copy = create_clean_copies([mesh])[0]
        mesh_parent = mc.listRelatives(mesh_copy, parent=True)[0]
        copies.append(mesh_copy)
        add_shading_tag(mesh_copy)
        add_shading_tag(mesh_parent)
    preview_shader, preview_shading_engine = create_material('lambert')
    assign_material(preview_shading_engine, copies)
    add_shading_tag(preview_shading_engine)
    add_shading_tag(preview_shader)
    textures = list_texture_filepaths(original_shading_engines)
    return copies, preview_shader, textures


def add_shading_tag(node):
    mc.addAttr(
        node,
        longName='_for_shading_preview',
        attributeType='message')


def clean_preview_shading_mesh():
    nodes_to_clean = [n.split('.')[0] for n in mc.ls('*._for_shading_preview')]
    if nodes_to_clean:
        mc.delete(nodes_to_clean)
    unisolate_active_view()


def get_default_exposure():
    if not mc.optionVar(exists=DEFAULT_EXPOSURE):
        return 0.0
    return mc.optionVar(query=DEFAULT_EXPOSURE)


def set_default_exposure(value):
    exposure = round((value / 10) - 5, 2)
    mc.optionVar(floatValue=[DEFAULT_EXPOSURE, exposure])
    nodes = [n.split('.')[0] for n in mc.ls('*._for_shading_preview')]
    nodes = mc.ls(nodes, type='file')
    for node in nodes:
        set_attr(node, 'exposure', exposure)


class TexturePreviewer(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent, QtCore.Qt.Tool)
        self.setWindowTitle('Texture Previewer')
        self.preview_shader = None

        self.create_preview = QtWidgets.QPushButton('Create Preview')
        self.create_preview.released.connect(self.call_create_preview)
        self.textures = QtWidgets.QListWidget()
        self.apply_texture = QtWidgets.QPushButton('Apply Texture')
        self.apply_texture.released.connect(self.call_apply_texture)
        self.clean_scene = QtWidgets.QPushButton('Clean Scene')
        self.clean_scene.released.connect(clean_preview_shading_mesh)
        self.clean_scene.released.connect(self.textures.clear)
        self.default_exposure = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.default_exposure.setValue(int((get_default_exposure() + 5) * 10))
        self.default_exposure.valueChanged.connect(self.set_default_exposure)
        self.exposure_label = QtWidgets.QLabel(self.get_exposure_label())
        self.exposure_label.setFixedWidth(150)

        buttons = QtWidgets.QHBoxLayout()
        buttons.addWidget(self.apply_texture)
        buttons.addWidget(self.clean_scene)

        exposure = QtWidgets.QHBoxLayout()
        exposure.addWidget(self.exposure_label)
        exposure.addWidget(self.default_exposure)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.create_preview)
        layout.addWidget(self.textures)
        layout.addLayout(exposure)
        layout.addLayout(buttons)

    def get_exposure_label(self):
        return f'Default exposure ({get_default_exposure()}):'

    def set_default_exposure(self, value):
        set_default_exposure(value)
        self.exposure_label.setText(self.get_exposure_label())

    def call_create_preview(self):
        clean_preview_shading_mesh()
        meshes = selected_meshes()
        meshes, shader, textures = create_texture_preview_setup(meshes)
        self.preview_shader = shader
        self.set_textures(sorted(set(textures)))
        isolate_nodes(meshes)

    def set_textures(self, textures):
        self.textures.clear()
        for texture in textures:
            item = QtWidgets.QListWidgetItem()
            item.setText(os.path.basename(texture))
            item.setData(QtCore.Qt.UserRole, os.path.expandvars(texture))
            self.textures.addItem(item)

    def call_apply_texture(self):
        items = self.textures.selectedItems()
        if not items:
            return
        path = items[0].data(QtCore.Qt.UserRole)
        file_node, p2t_node = set_texture(f'{self.preview_shader}.color', path)
        set_attr(file_node, 'exposure', get_default_exposure())
        add_shading_tag(file_node)
        add_shading_tag(p2t_node)
        mc.select(file_node)


_texture_previewer = None


def show_texture_previewer():
    global _texture_previewer
    if _texture_previewer is not None:
        _texture_previewer.close()
    _texture_previewer = TexturePreviewer(get_maya_window())
    _texture_previewer.show()
    return _texture_previewer


if __name__ == '__main__':
    window = TexturePreviewer(get_maya_window())
    window.show()

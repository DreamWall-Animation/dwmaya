from contextlib import contextmanager
import maya.cmds as mc


@contextmanager
def maya_namespace(
        namespace='', create_if_missing=True, restore_current_namespace=True):
    """Context manager to temporarily set a namespace"""
    initial_namespace = ':' + mc.namespaceInfo(currentNamespace=True)
    if not namespace.startswith(':'):
        namespace = ':' + namespace
    try:
        if not mc.namespace(absoluteName=True, exists=namespace):
            if create_if_missing:
                mc.namespace(setNamespace=':')
                namespace = mc.namespace(addNamespace=namespace)
            else:
                mc.namespace(initial_namespace)
                raise ValueError(namespace + " doesn't exists.")
        mc.namespace(setNamespace=namespace)
        yield namespace
    finally:
        if restore_current_namespace:
            mc.namespace(setNamespace=initial_namespace)

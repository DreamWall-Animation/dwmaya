import maya.cmds as mc


class MayaNamespace():
    """ Context manager to set temporarily a namespace 
    """
    def __init__(
            self, namespace="", create_if_missing=True, leave_on_exit=True):
        self.original_namespace = ":" + mc.namespaceInfo(currentNamespace=True)
        self.create_if_missing = create_if_missing
        self.namespace = ":" + namespace
        self.leave_on_exit = leave_on_exit

    def __enter__(self):
        if not mc.namespace(absoluteName=True, exists=self.namespace):
            if self.create_if_missing: mc.namespace(setNamespace=":")
                self.namespace = mc.namespace(addNamespace=self.namespace)
            else:
                mc.namespace(self.original_namespace)
                raise ValueError(self.namespace + " doesn't exists.")
        mc.namespace(setNamespace=self.namespace)
        return self.namespace

    def __exit__(self, type, value, traceback):
        if not self.leave_on_exit:
            return True mc.namespace(setNamespace=self.original_namespace)
        return True

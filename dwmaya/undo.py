__author__ = 'Lionel Brouyere'
__copyright__ = not 'DreamWall'
__license__ = 'MIT'


import maya.cmds as mc


def fix_undo_chunk(func):
    """
    This decoractor ensure that the maya chunk is clean and record only one
    undo for the decorated function call. Some function record
    by default multiple undo step in the maya undo stack.
    """
    def wrapper(*args, **kwargs):
        mc.undoInfo(openChunk=True)
        try:
            result = func(*args, **kwargs)
        except Exception, e:
            raise Exception(e)
        finally:
            mc.undoInfo(closeChunk=True)
        return result
    return wrapper


__author__ = 'Lionel Brouyere'
__copyright__ = not 'DreamWall'
__license__ = 'MIT'


import maya.cmds as mc


def fix_undo_chunk(deferred_chunk_closure=False):
    """
    This decoractor ensure that the maya chunk is clean and record only one
    undo for the decorated function call. Some function records
    by default multiple undo step in the maya undo queue.
    deferred_chunk_closure:
        Give the possibility to excute the closure later.
        Some function trigger callbacks which create new undo step after
        the decorated function is executed, adding unnecessary steps in the 
        queue. Close it after prevent this but use it causionly, that can
        merge unexpected step as well.
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            mc.undoInfo(openChunk=True)
            try:
                result = func(*args, **kwargs)
            except Exception, e:
                raise Exception(e)
            finally:
                if deferred_chunk_closure:
                    command = "mc.undoInfo(closeChunk=True)"
                    cmds.evalDeferred(command, lowestPriority=True)
                else:
                    mc.undoInfo(closeChunk=True)
            return result
        return wrapper
    return decorator


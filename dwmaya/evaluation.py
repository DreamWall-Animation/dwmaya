from contextlib import contextmanager
import maya.cmds as mc


@contextmanager
def evluation_mode(mode):
    initial_mode = mc.evaluationManager(query=True, mode=True)[0]
    mc.evaluationManager(mode=mode)
    try:
        yield None
    finally:
        mc.evaluationManager(mode=initial_mode)

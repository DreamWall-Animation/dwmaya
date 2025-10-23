import maya.cmds as mc


VAR = 'deformationCreateTweak'


def ensure_deformation_tweak_creation(func):
    """
    Since Maya implemented the rigging tags, that simplified deformer node
    graph. That's does not rely on objectSets, objectIds anymoyre.
    I guess this is cool, but at some point, those nodes remains necessary for
    some scripts :|. Holy shit !! That option var is litterally affecting how
    code behave... Need to decorate my function to ensure a blendShape or a
    cluster is going to be created as I want :(
    """
    def wrapper(*args, **kwargs):
        value = mc.optionVar(query=VAR)
        result = func(*args, **kwargs)
        mc.optionVar(intValue=[VAR, value])
        return result
    return wrapper

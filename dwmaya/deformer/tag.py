import maya.cmds as mc


VAR = 'deformationUseComponentTags'


def force_deformation_component_tags_var(state=False):
    """
    Since Maya implemented the rigging component tags,
    that simplified deformer node connection.
    That's does not rely on objectSets, objectIds etc..
    I guess this is cool, but at some point, those nodes remains necessary for
    some scripts :|. Holy shit !! That option var is litterally affecting how
    code behave... Need to decorate my function to ensure a blendShape or a
    cluster is going to be created as I want :(
    """
    def function(func):
        def wrapper(*args, **kwargs):
            value = mc.optionVar(query=VAR)
            mc.optionVar(intValue=[VAR, int(state)])
            result = func(*args, **kwargs)
            mc.optionVar(intValue=[VAR, value])
            return result
        return wrapper
    return function

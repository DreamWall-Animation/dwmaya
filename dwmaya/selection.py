'''
This Module contain a collection of decorator to manage maya selection.
The goal is to externalize all selection checks during procedure like:
def generic_method_creating_a_deformer_from_selection():
    selection = cmds.ls(selection=True)
    if len(selection) == 0:
        return cmds.warning('Please select at least one node')
    if cmds.nodeType(selection[0]) != 'mesh':
        return cmds.warning('Please select a mesh first')
    # all your process ...
    # and finally reselect to get back your selection
    cmds.select(selection)
    return
These kind of lines pollute all procedures changing, checking selection
and it can be cleaner to externalize them like this:
@preserve_selection
@filter_node_type_in_selection(node_type=('transform, mesh'))
@selection_contains_at_least(2, 'transform')
@selection_required
def generic_method_creating_a_deformer_from_selection():
    # all your process ...
    return
careful, the used order is really important. A bad wrapper managment can
create issue.
'''

__author__ = 'Lionel Brouyere'
__copyright__ = not 'DreamWall'
__license__ = 'MIT'


from functools import wraps
import maya.cmds as mc


def preserve_selection(func):
    '''
    this decorator save your maya selection before execute the
    decorated function. And reselect it when it's executed.
    '''
    @wraps(func)
    def wrapper(*args, **kwargs):
        selection = mc.ls(sl=True)
        result = func(*args, **kwargs)
        mc.select(selection)
        return result
    return wrapper


def selection_required(func):
    '''
    this decorator check check if node is selected and return a mc.error
    if nothing is selected
    '''
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not mc.ls(selection=True):
            return mc.warning('Select at least one node')
        else:
            return func(*args, **kwargs)
    return wrapper


def filter_selection(**ls_kwargs):
    '''
    this decorator filter the current selection and keep only the node_types
    in the node_type list
    @node_type string or tuple of string
    '''
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            mc.select(mc.ls(selection=True, **ls_kwargs))
            result = func(*args, **kwargs)
            return result
        return wrapper
    return decorator


def filter_transforms_by_children_types(*nodetypes):
    '''
    this decorators remove from the current selection the transforms
    who not contains at least a specified nodetype shape.
    The shapes in selection are kept.
    '''
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            not_transforms_selected = [
                n for n in mc.ls(selection=True)
                if mc.nodeType(n) != 'transform']
            filtered_transforms = []
            for transform in mc.ls(selection=True, type='transform'):
                for node in mc.listRelatives(transform):
                    if not mc.getAttr(node + '.intermediateObject'):
                        if mc.nodeType(node) in nodetypes:
                            filtered_transforms.append(transform)
                            continue
            mc.select(not_transforms_selected + filtered_transforms)
            return func(*args, **kwargs)
        return wrapper
    return decorator


def select_shape_transforms(func):
    '''
    this decorator select all transforms instead of shapes
    '''
    @wraps(func)
    def wrapper(*args, **kwargs):
        nodes = [
            n if mc.nodeType(n) == 'transform'
            else mc.listRelatives(n, parent=True)[0]
            for n in mc.ls(sl=True)]
        mc.select(nodes)
        result = func(*args, **kwargs)
        return result
    return wrapper


def selection_contains_at_least(number, node_type):
    '''
    this decorqtor check if a maya selection contain at least the number of
    nodes with nodetype specified.
    :number int
    :node_type string
    '''
    assert isinstance(node_type, str)  # node_type argument must be a string
    assert isinstance(number, int)  # number argument must be an int

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            typed_node_in_selection = mc.ls(selection=True, type=node_type)
            if len(typed_node_in_selection) < number:
                return mc.warning(
                    'The selection must contains at least {} nodes {} '
                    'and it contains {}'.format(
                        number, node_type, len(typed_node_in_selection)))
            return func(*args, **kwargs)
        return wrapper
    return decorator


def selection_contains_exactly(number, node_type):
    '''
    this decorator check if a maya selection contains exactly the number of
    nodes with nodetype specified.
    :number int
    :node_type string
    '''
    assert isinstance(node_type, str)  # node_type argument must be a string
    assert isinstance(number, int)  # number argument must be an int

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            typed_node_in_selection = mc.ls(selection=True, type=node_type)
            if len(typed_node_in_selection) != number:
                return mc.warning(
                    'The selection must contains exactly {} node(s) {} '
                    'and it contains {}'.format(
                        number, node_type, len(typed_node_in_selection)))
            return func(*args, **kwargs)
        return wrapper
    return decorator

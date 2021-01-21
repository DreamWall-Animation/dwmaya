"""
Copied from https://gizmosandgames.com/2017/05/21/frustum-culling-in-maya/
    from MatthewRickShaw
"""

import maya.api.OpenMaya as om


def get_bounding_box(shape_name):
    # maya.cmds.exactWorldBoundingBox
    selection_list = om.MSelectionList()
    selection_list.add(shape_name)
    obj_dag_path = selection_list.getDagPath(0)
    obj_dag_node = om.MFnDagNode(obj_dag_path)
    matrix = obj_dag_path.exclusiveMatrix()
    bbox = obj_dag_node.boundingBox.transformUsing(matrix)
    return bbox


class Plane(object):
    def __init__(self, a, b, c, d):
        self.normal = om.MVector(a, b, c)
        self.distance = d

    def normalise(self):
        length = self.normal.length()
        self.normal /= length
        self.distance /= length

    def is_in_front(self, point):
        return point * self.normal + self.distance > 0


class Frustum(object):
    def __init__(self, camera_name):
        selection_list = om.MSelectionList()
        selection_list.add(camera_name)
        cam_dag_path = selection_list.getDagPath(0)
        self.camera = om.MFnCamera(cam_dag_path)

        world_to_cam = om.MFloatMatrix(cam_dag_path.inclusiveMatrixInverse())
        projection = self.camera.projectionMatrix()
        post_projection = self.camera.postProjectionMatrix()

        # MFloatMatrix = [x-axis, y-axis, z-axis, translate]
        view_projection = world_to_cam * projection * post_projection

        # Right = translate - x-axis
        self.right = Plane(
            view_projection[3] - view_projection[0],
            view_projection[7] - view_projection[4],
            view_projection[11] - view_projection[8],
            view_projection[15] - view_projection[12],
        )

        # Left = translate + x-axis
        self.left = Plane(
            view_projection[3] + view_projection[0],
            view_projection[7] + view_projection[4],
            view_projection[11] + view_projection[8],
            view_projection[15] + view_projection[12],
        )

        # Bottom = translate + y-axis
        self.bottom = Plane(
            view_projection[3] + view_projection[1],
            view_projection[7] + view_projection[5],
            view_projection[11] + view_projection[9],
            view_projection[15] + view_projection[13],
        )

        # Top = translate - y-axis
        self.top = Plane(
            view_projection[3] - view_projection[1],
            view_projection[7] - view_projection[5],
            view_projection[11] - view_projection[9],
            view_projection[15] - view_projection[13],
        )

        # Far = translate + z-axis
        self.far = Plane(
            view_projection[3] + view_projection[2],
            view_projection[7] + view_projection[6],
            view_projection[11] + view_projection[10],
            view_projection[15] + view_projection[14],
        )

        # Near = translate - z-axis
        self.near = Plane(
            view_projection[3] - view_projection[2],
            view_projection[7] - view_projection[6],
            view_projection[11] - view_projection[10],
            view_projection[15] - view_projection[14],
        )

        self.planes = [self.right, self.left, self.bottom, self.top, self.far, self.near]

    def intersects(self, shape_name):
        bbox = get_bounding_box(shape_name)
        limits = [bbox.min, bbox.max]

        for plane in self.planes:
            # The corner furthest in normal direction of plane
            index_x = int(plane.normal.x > 0)
            index_y = int(plane.normal.y > 0)
            index_z = int(plane.normal.z > 0)
            point = om.MVector(limits[index_x].x, limits[index_y].y, limits[index_z].z)

            # If this corner is not in front, none are, bbox is out of view
            if not plane.is_in_front(point):
                return False

        return True

if __name__ == '__main__':
    import maya.cmds as mc
    frustum = Frustum('perspShape')
    shape = mc.ls(selection=True, shapes=True, dag=True, long=True)[0]
    print(frustum.intersects(shape))

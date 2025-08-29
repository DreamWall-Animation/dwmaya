import maya.cmds as mc


def create_bbox_curve(transform, color=None):
    xmin, ymin, zmin, xmax, ymax, zmax = mc.exactWorldBoundingBox(transform)

    p000 = (xmin, ymin, zmin)
    p100 = (xmax, ymin, zmin)
    p110 = (xmax, ymax, zmin)
    p010 = (xmin, ymax, zmin)
    p001 = (xmin, ymin, zmax)
    p101 = (xmax, ymin, zmax)
    p111 = (xmax, ymax, zmax)
    p011 = (xmin, ymax, zmax)

    edges = [
        (p000, p100), (p100, p110), (p110, p010), (p010, p000),
        (p001, p101), (p101, p111), (p111, p011), (p011, p001),
        (p000, p001), (p100, p101), (p110, p111), (p010, p011)]

    shapes = []
    for i, (a, b) in enumerate(edges):
        name = f'{transform}_bbox_{i}'
        crv = mc.curve(d=1, p=[a, b], name=name)
        shp = mc.listRelatives(crv, type='nurbsCurve')[0]
        mc.parent(shp, transform, shape=True, relative=True)
        mc.delete(crv)
        shapes.append(shp)
        if color:
            mc.setAttr(shp + ".overrideEnabled", 1)
            mc.setAttr(shp + ".overrideRGBColors", 1)
            mc.setAttr(shp + ".overrideColorRGB", *color)

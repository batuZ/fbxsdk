from FbxCommon import *
from utils import *

import FbxHelper
import cv2
import numpy as np
import math

# polygong lib pyclipper
# CNdoc:https://www.cnblogs.com/zhigu/p/11943118.html
# EX:https://blog.csdn.net/weixin_43624833/article/details/112919141
import pyclipper

lSdkManager = None
lScene = None
MAX_SIZE = 0
TAG_SIZE = 512


def showImage(img, points):
    cv2.polylines(img, np.array(points, np.int32), True, (0, 255, 255), 2)
    cv2.namedWindow('pic', cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)
    cv2.imshow('pic', img)


def buffer_contour(contour, margin):
    """
    等距离缩放多边形轮廓点
    :param contour: 一个图形的轮廓格式[[x1, x2],...],shape是(n, 2)
    :param margin: 轮廓外扩的像素距离,margin正数是外扩,负数是缩小
    :return: 外扩后的轮廓点
    """
    pco = pyclipper.PyclipperOffset()
    pco.AddPath(contour, pyclipper.JT_MITER, pyclipper.ET_CLOSEDPOLYGON)
    solution = pco.Execute(margin)
    return solution


def ParseMeshUV(iMesh):
    '''解析MeshUV, 得到UVPolygons,UVEdges'''
    layerUV = iMesh.GetElementUV()
    # uv坐标集
    vuPoint = layerUV.GetDirectArray()
    # uv索引集
    uvIndex = layerUV.GetIndexArray()
    # 多边形数，uv与mesh的多边形一定是一一对应的
    polygonCount = iMesh.GetPolygonCount()
    # 存放uv多边型坐标索引（n,pSize）
    uvPolygons = []
    # 存放uv多边型边索引（n,pSize）
    uvPolyEdges = []
    # uvEdge集
    uvEdges = []
    # 依据polygon遍历uv索引集
    for i in range(polygonCount):
        polySize = iMesh.GetPolygonSize(i)

        # 解析uv多边形
        poly = []
        for j in range(polySize):
            uv = uvIndex[i*polySize + j]
            poly.append(uv)
        uvPolygons.append(poly)

        # 解析uv边，edgeSize == polySize
        ed = []
        for k in range(polySize):
            start = poly[k]
            end = poly[(k+1) % polySize]
            # 每个edge在创建之前都要找一下是不是其它面的共边，如果是则直接引用
            currusEdge = None
            edgeId = uvEdgeCount = len(uvEdges)
            for l in range(uvEdgeCount):
                edge = uvEdges[l]
                # 一个edge最多被两个三角面引用，而且方向相反
                if edge == [end, start]:
                    currusEdge = edge
                    edgeId = l
                    break

            ed.append(edgeId)
            if currusEdge == None:
                uvEdges.append([start, end])

        uvPolyEdges.append(ed)
    return len(uvPolygons)


if __name__ == "__main__":

    lSdkManager, lScene = InitializeSdkObjects()

    if not(LoadScene(lSdkManager, lScene, 'D:\\test.FBX')):
        print('load scene faild!!')

    # The coordinate system's original Up Axis when the scene is created. 0 is X, 1 is Y, 2 is Z axis.
    # upAxis = lScene.GetGlobalSettings().GetOriginalUpAxis()  # Z-UP
    # print('upAxis:', upAxis)

    # 1、找到所有超尺寸贴图
    for i in range(lScene.GetTextureCount()):
        tex = lScene.GetTexture(i)
        fileName = tex.GetFileName()
        img = cv2Reader(fileName)
        height, width, channel = img.shape
        if width > MAX_SIZE or height > MAX_SIZE:
            # 2、处理使用大贴图的模型
            DiffuseLayer = tex.GetDstProperty()
            materail = DiffuseLayer.GetParent()
            iNode = materail.GetDstObject(1)
            iMesh = iNode.GetMesh()
            # 3、解析UV集
            done, tUVs = iMesh.GetTextureUV()
            uvGroups = iMesh.BGetUVGroups()
            for grp in uvGroups:
                points = iMesh.BGetContourWithUVGroup(grp)
                uvPoints = ID2UV(tUVs, points, width, height)
                imgPoints = UV2IMG(height, uvPoints)
                # showImage(img, [imgPoints])  # unbuffer
                buffer = buffer_contour(imgPoints, 6)
                showImage(img, buffer)

            # 5、创建空画布，填充uv多边形，填满则创建新多边形

    # 6、创建materail，引用贴图，设置mesh材质id

    # 7、清除未引用materail，导出新fbx
    cv2.waitKey(0)
    lSdkManager.Destroy()
    sys.exit(0)

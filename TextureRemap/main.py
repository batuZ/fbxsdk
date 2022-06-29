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
            # 4、求面积，排序
            areaPercen = 0
            areas = []
            for grp in uvGroups:
                vuIds = iMesh.BGetContourWithUVGroup(grp)  # [1, 2, 3, ...]
                uvPercen = ID2UVP(tUVs, vuIds)  # [[0.1, 0.1], [0.2, 0.2], ...]
                area = polygongArea(uvPercen)
                areaPercen += area  # 0 ~ 1
                areas.append(area)

            # 获取当前UV面积比,用于判断是否需要处理
            if areaPercen > 0.99:
                continue

            # 按面积对uvGroups排序
            uvGroupIds = sorted(range(len(areas)),
                                key=lambda k: areas[k], reverse=True)

            # 5、把uv集排进画布
            container = [[0, 0]]
            containerSize = 1024
            for g in uvGroupIds:
                gid = uvGroupIds[g]
                grp = uvGroups[gid]
                vuIds = iMesh.BGetContourWithUVGroup(grp)
                uvPercen = ID2UVP(tUVs, vuIds)
                _min, _max = getBoundingBox(uvPercen)
                _range = (np.array(_max) - np.array(_min)) * \
                    np.array([width, height])
                ses = []
                for startPoint in container:
                    res = np.array(startPoint) + _range
                    se = res / np.array([1024, 1024])
                    ses.append(se)

                selectStart = 0
                for s in ses:
                    if(s[0] > 1 or s[1] > 1):
                        continue

            contours = []
            for grp in uvGroups:
                vuIds = iMesh.BGetContourWithUVGroup(grp)  # [1, 2, 3, ...]
                # 获取当前UV面积比,用于判断是否需要处理
                uvPercen = ID2UVP(tUVs, vuIds)  # [[0.1, 0.1], [0.2, 0.2], ...]
                areaPercen += polygongArea(uvPercen)  # 0 ~ 1
                # [[12.3, 12.3], [24.6, 24.6], ...]
                uvPoints = ID2UV(tUVs, points, width, height)
                contours.append(uvPoints)
                # imgPoints = UV2IMG(height, uvPoints)
                # # showImage(img, [imgPoints])  # unbuffer
                # buffer = buffer_contour(imgPoints, 5)
                # showImage(img, buffer)
            pass
            # 5、创建空画布，填充uv多边形，填满则创建新多边形

    # 6、创建materail，引用贴图，设置mesh材质id

    # 7、清除未引用materail，导出新fbx
    cv2.waitKey(0)
    lSdkManager.Destroy()
    sys.exit(0)

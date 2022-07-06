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

from ParseUVs import parseUV
from ReArrange import rearrange
from Split2PowN import split2powN


lSdkManager = None
lScene = None
MAX_SIZE = 0
TAG_SIZE = 1024


def showImage(img, points):
    cv2.polylines(img, np.array(points, np.int32), True, (0, 255, 255), 2)
    cv2.namedWindow('pic', cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)
    cv2.imshow('pic', img)

 # imgPoints = UV2IMG(height, uvPoints)
# # showImage(img, [imgPoints])  # unbuffer
# buffer = buffer_contour(imgPoints, 5)
# showImage(img, buffer)


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


def d_showOri(img, title):
    scale = _debug / height
    oriImg = cv2.resize(img, None, fx=scale, fy=scale)
    cvUpdate = cvShow(oriImg, '{}-{}x{}'.format(title, width, height))
    next(cvUpdate)
    return oriImg, cvUpdate


def d_updateOri(oriImg, oriUpdate, ranges):
    scale = _debug / height

    # h, w, _ = img.shape
    auv = [0, _debug] - np.array(ranges)*[-scale, scale]
    auv = np.array(auv, dtype=np.int32)
    cv2.polylines(oriImg, auv, True, (152, 255, 255), 1)
    next(oriUpdate)


if __name__ == "__main__":
    import time
    _debug = 0  # 700.0

    lSdkManager, lScene = InitializeSdkObjects()

    if not(LoadScene(lSdkManager, lScene, 'D:\\test.FBX')):
        print('load scene faild!!')

    # The coordinate system's original Up Axis when the scene is created. 0 is X, 1 is Y, 2 is Z axis.
    # upAxis = lScene.GetGlobalSettings().GetOriginalUpAxis()  # Z-UP
    # print('upAxis:', upAxis)

    # 1、找到需要处理的贴图
    for i in range(lScene.GetTextureCount()):
        tex = lScene.GetTexture(i)
        fileName = tex.GetFileName()

        img = cv2Reader(fileName)
        height, width, channel = img.shape

        if _debug:
            oriImg, oriUpdate = d_showOri(img, os.path.basename(fileName))

        if width > MAX_SIZE or height > MAX_SIZE:
            print('>> 开始处理{}'.format(os.path.basename(fileName)))
            # 2、找到对应的mesh
            DiffuseLayer = tex.GetDstProperty()
            materail = DiffuseLayer.GetParent()
            iNode = materail.GetDstObject(1)
            iMesh = iNode.GetMesh()
            # 3、解析UV集
            uvGroups = iMesh.BGetUVGroups()
            rects = []
            bboxes = []
            for g in uvGroups:
                uvPercenContour = iMesh.BGetContourWithUVGroup(g)
                uvContour = np.array(uvPercenContour)*[width, height]
                # TODO buffer 是根据数据实际情况确定
                # polygon的buffer一定小于外接矩形，buffer越大误差越大
                # 为了减少计算量直接用rect+buffer，优化后可以直接用polygongBuffer
                rect = getRect(uvContour, buffer=5)
                rects.append(rect)
                if _debug:
                    b = getBoundingBox(uvContour, buffer=5)
                    bbox = [b[0], [b[1][0], b[0][1]], b[1], [b[0][0], b[1][1]]]
                    bboxes.append(bbox)
            if _debug:
                d_updateOri(oriImg, oriUpdate, bboxes)

            # 4、拆分贴图
            print('>> 拆分贴图:')
            stime = time.process_time()
            fileCount = 0
            while len(rects):
                fileCount += 1
                cliped = []
                rectsArea = sum([r[2][0]*r[2][1] for r in rects])
                maxW, maxH = [
                    np.array(rects)[:, 2, 0].max(),
                    np.array(rects)[:, 2, 1].max()
                ]
                maxSize = max([maxW, maxH, TAG_SIZE])
                rects = split2powN(rectsArea, 256, maxSize, [maxW, maxH])
                r = rects[0]
                boxes = [[0, 0], [r[0], 0], r, [0, r[1]]]
                rects = rearrange([boxes], [rects])
                print('file-{}:{}'.format(fileCount, r))
            etime = time.process_time()
            print('{}秒'.format(etime - stime))
    # 6、创建materail，引用贴图，设置mesh材质id

    # 7、清除未引用materail，导出新fbx
    cv2.waitKey(0)
    lSdkManager.Destroy()
    sys.exit(0)

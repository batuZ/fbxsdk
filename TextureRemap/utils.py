import os
import cv2
import numpy as np

output_log = True


def printInLine(*msg) -> None:
    '''单行输出'''
    if output_log:
        print('\b'*1000, end='')
        print(*msg, ' '*20, end='')


def cv2Reader(path, flag=None):
    '''解决中文路径问题'''
    # region flag
    # cv2.IMREAD_COLOR：指定加载彩色图像。 图像的任何透明度都将被忽略。 它是默认标志。 或者，我们可以为此标志传递整数值 1。
    # cv2.IMREAD_GRAYSCALE：指定以灰度模式加载图像。 或者，我们可以为此标志传递整数值 0。
    # cv2.IMREAD_UNCHANGED：它指定加载图像，包括 alpha 通道。 或者，我们可以为此标志传递整数值 -1。
    # endregion
    if os.path.exists(path):
        res = cv2.imread(path, flag)
        if res is None:
            res = cv2.imdecode(np.fromfile(path), flag)
        return res


def ID2UV(UVs, ids,  imgX, imgY):
    '''模型轮廓线转纹理图像坐标轮廓线'''
    res = []
    for p in ids:
        x = UVs[p][0] * imgX
        y = (UVs[p][1]) * imgY
        res.append([x, y])
    return res


def ID2UVP(UVs, ids):
    res = []
    for p in ids:
        res.append([UVs[p][0], UVs[p][1]])
    return res


def UV2IMG(height, points):
    '''uv坐标转图像坐标, 图像坐标向下为Y增'''
    res = []
    for i in points:
        res.append([i[0], height-i[1]])
    return res


def polygongArea(poly):
    '''多边形面积，(n,2)不闭合顶点集
    np.array([[0.1, 0.1], [0.9, 0.1], [0.9, 0.9], [0.1, 0.9]])
    '''
    poly = np.array(poly)
    x = poly[:, 0]
    y = poly[:, 1]
    return 0.5*np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))


def getBoundingBox(points):
    '''获取polygon包围盒'''
    minx = miny = float('inf')
    maxx = maxy = float('-inf')
    for poi in points:
        minx = poi[0] if poi[0] < minx else minx
        maxx = poi[0] if poi[0] > maxx else maxx
        miny = poi[1] if poi[1] < miny else miny
        maxy = poi[1] if poi[1] > maxy else maxy
    return (minx,  miny), (maxx, maxy)


def cvShow(data):
    while 1:
        #cv2.namedWindow('pic', cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)
        cv2.imshow('pic', data)
        cv2.waitKey(1)
        tag = yield


def _cross(p1, p2, p3):  # 叉积判定
    x1 = p2[0]-p1[0]
    y1 = p2[1]-p1[1]
    x2 = p3[0]-p1[0]
    y2 = p3[1]-p1[1]
    return x1*y2-x2*y1


def segment(p1, p2, p3, p4):  # 判断两线段是否相交
    # 矩形判定，以l1、l2为对角线的矩形必相交，否则两线段不相交
    if(max(p1[0], p2[0]) >= min(p3[0], p4[0])  # 矩形1最右端大于矩形2最左端
       and max(p3[0], p4[0]) >= min(p1[0], p2[0])  # 矩形2最右端大于矩形1最左端
       and max(p1[1], p2[1]) >= min(p3[1], p4[1])  # 矩形1最高端大于矩形2最低端
       and max(p3[1], p4[1]) >= min(p1[1], p2[1])):  # 矩形2最高端大于矩形1最低端
        if(_cross(p1, p2, p3)*_cross(p1, p2, p4) < 0
                and _cross(p3, p4, p1)*_cross(p3, p4, p2) < 0):
            D = 1
        else:
            D = 0
    else:
        D = 0
    return D


def isIntersect(poly1, poly2):
    '''两多边形是否相交'''
    p1Size = len(poly1)
    p2Size = len(poly2)
    for i in range(p1Size):
        lineAStart = poly1[i]
        lineAEnd = poly1[(i+1) % p1Size]
        for j in range(p2Size):
            lineBStart = poly2[j]
            lineBEnd = poly2[(j+1) % p2Size]
            if segment(lineAStart, lineAEnd, lineBStart, lineBEnd):
                return True
    return False


''' 化简多边形,以去重,去自交
import pyclipper
import numpy as np
path = [[1.2, 1.5], [5.5, 1], [5, 5], [1, 5]]
path1 = np.array(path)
path2 = path1*100
result = pyclipper.SimplifyPolygon(
    path2, pyclipper.PFT_EVENODD)  # pyclipper.PFT_NONZERO
res = np.array(result)/100.0
print(123)
'''

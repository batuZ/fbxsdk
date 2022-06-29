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


def getRange(points):
    (minx,  miny), (maxx, maxy) = getBoundingBox(points)
    return maxx - minx, maxy - miny


def cvShow(data):
    while 1:
        #cv2.namedWindow('pic', cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)
        cv2.imshow('pic', data)
        cv2.waitKey(100)
        tag = yield


def find2n(num):
    '''找到最接近num的2n次幂,返回n,四舍五入原则'''
    n = 0
    while num > 2**(n+0.44444444444444):
        n += 1
    return n

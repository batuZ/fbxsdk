import numpy as np
import pyclipper
import cv2
import os
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


def getBoundingBox(points, buffer=0):
    '''获取polygon包围盒'''
    minx = miny = float('inf')
    maxx = maxy = float('-inf')
    for poi in points:
        minx = poi[0] if poi[0] < minx else minx
        maxx = poi[0] if poi[0] > maxx else maxx
        miny = poi[1] if poi[1] < miny else miny
        maxy = poi[1] if poi[1] > maxy else maxy
    return (minx-buffer,  miny-buffer), (maxx+buffer, maxy+buffer)


def getRect(points, buffer=0):
    '''获取多边形外接矩形'''
    (minx,  miny), (maxx, maxy) = getBoundingBox(points)
    w, h = maxx - minx + buffer*2, maxy - miny + buffer*2
    return [[0, 0], [w, 0], [w, h], [0, h]]


def cvShow(data, title='pic'):
    while 1:
        #cv2.namedWindow('pic', cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)
        cv2.imshow(title, data)
        cv2.waitKey(100)
        tag = yield


def find2n(num):
    '''找到最接近num的2n次幂,返回n,四舍五入原则'''
    n = 0
    while num > 2**(n+0.44444444444444):
        n += 1
    return n


_pc = pyclipper.Pyclipper()


def isAIncludeB(A, B, scale=1e4):
    '''判断多边形A是否完整包含多边形B'''
    A = np.array(A)*scale
    B = np.array(B)*scale
    _pc.Clear()
    _pc.AddPath(A, pyclipper.PT_SUBJECT, True)
    _pc.AddPath(B, pyclipper.PT_CLIP, True)
    sumPolys = _pc.Execute(pyclipper.CT_UNION,
                           pyclipper.PFT_POSITIVE, pyclipper.PFT_POSITIVE)
    return pyclipper.Area(sumPolys[0]) == pyclipper.Area(A)


def isX(A, B):
    A = np.array(A)[:2, :2]
    B = np.array(B)[:2, :2]
    return (A[:, 0].min() < B[:, 0].min() < A[:, 0].max() and B[:, 1].min() < A[:, 1].min() < B[:, 1].max()) \
        or (B[:, 0].min() < A[:, 0].min() < B[:, 0].max() and A[:, 1].min() < B[:, 1].min() < A[:, 1].max())


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
            if isX([lineAStart, lineAEnd], [lineBStart, lineBEnd]):
                return True
    return False


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

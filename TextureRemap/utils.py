import os
import cv2


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

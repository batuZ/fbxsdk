# polygong lib pyclipper
# CNdoc:https://www.cnblogs.com/zhigu/p/11943118.html
# https://blog.csdn.net/weixin_43624833/article/details/112919141

import numpy as np
import pyclipper

# 忽略小结构
IGNORE = 20
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


def cvShow(data):
    while 1:
        cv2.imshow('pic', data)
        cv2.waitKey(100)
        tag = yield


def _showBoxId(img, offset, polygongs):
    # 显示容器顶点索引
    for polygong in polygongs:
        for i in range(len(polygong)):
            cv2.putText(
                img,
                str(i),
                offset[0] + polygong[i],
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                1)


def _clearBox(boxes):
    # 清理容器中的小结构
    for box in boxes:
        boxSize = len(box)
        for box in boxes:
            boxSize = len(box)
            for b in range(boxSize):
                perv = box[(b-1) % boxSize]
                cur = box[b]
                nex = box[(b+1) % boxSize]
                nexx = box[(b+2) % boxSize]

                #  |         4
                # 3 ¯¯¯¯¯¯¯¯¯|________ 6
                #           5         |
                # 5 = [6.x,4.y]
                if 0 < cur[1]-nex[1] < IGNORE:
                    nex[0], nex[1] = nexx[0], cur[1]

                #   |        5          6
                #   |________|¯¯¯¯¯¯¯¯¯|
                #  3         4         |
                # 4 = [3.x,5.y]
                elif 0 < nex[1]-cur[1] < IGNORE:
                    cur[0], cur[1] = perv[0], nex[1]

                #       3
                # ¯¯¯¯¯|
                #      | 5
                #     4¯|
                #       |_____
                #       6
                # 4 = [5.x,3.y]
                if 0 < nex[0]-cur[0] < IGNORE:
                    cur[0], cur[1] = nex[0], perv[1]

                #        3
                # ¯¯¯¯¯¯|
                #     5 |
                #     |¯ 4
                #     |_____
                #     6
                # 5 = [4.x, 6.y]
                elif 0 < cur[0]-nex[0] < IGNORE:
                    nex[0], nex[1] = cur[0], nexx[1]

    return pyclipper.CleanPolygons(boxes)


def rearrange(boxes, clips):
    # 验证数据结构
    boxes = np.array(boxes)[:, :, :2].tolist()
    clips = np.array(clips)[:, :4, :2].tolist()
    pc = pyclipper.Pyclipper()
    last_clips_len = -1
    while last_clips_len != len(clips):
        last_clips_len = len(clips)
        for clip in clips:
            for box in boxes:
                boxSize = len(box)
                # 在容器中找到可用的参考点
                flag = False
                for b in range(boxSize):
                    cur = np.array(box[b])   # 当前顶点，与下个顶点构成边
                    nex = box[(b+1) % boxSize]  # 下一个顶点，可循环的索引
                    sub = nex - cur  # 两顶点的差
                    tmp = clip + cur  # 使用当前顶点的临时结果
                    # 找到横向边，容器完成包含临时结果
                    if sub[0] > 0 and sub[1] == 0 and isAIncludeB(box, tmp):
                        pc.AddPath(tmp, pyclipper.PT_CLIP, True)  # 裁剪多边型
                        cliped.append(tmp)
                        clips.remove(clip)
                        flag = True
                        break  # 过程断点
                if flag:
                    break

            # 被裁多边型
            pc.AddPaths(boxes, pyclipper.PT_SUBJECT, True)
            # 裁剪动作 2:pyclipper.CT_DIFFERENCE, 0:pyclipper.PFT_EVENODD
            boxes = pc.Execute(2, 0, 0)

            # 清理过程
            pc.Clear()
            boxes = _clearBox(boxes)
            for box in boxes:
                if len(box) == 0:
                    boxes.remove(box)
            if len(boxes) == 0:
                last_clips_len = len(clips)
                break

            # 渲染结果
            if len(img):
                img[:, :, :] = [9*16, 8*16, 5*16]
                for b in boxes:
                    cv2.polylines(img, [np.array(b)]+offset, True, color1, 2)
                cv2.polylines(img, np.array(cliped)+offset, True, color2, 1)
                _showBoxId(img, offset, boxes)
                next(cvUpdate)


if __name__ == "__main__":
    import cv2
    import time
    # 模拟画布
    img = np.zeros((700, 800, 3), dtype=np.uint8)
    # 模拟容器
    boxes = [[[0, 0], [600, 0], [600, 600], [0, 600]]]

    # 模拟数据
    his = 0
    if his:
        # 上一次的模拟数据,用于复现问题
        rands = np.loadtxt('testData', dtype=np.uint32).tolist()
    else:
        rands = np.random.randint(
            low=15,
            high=150,
            size=(63, 2),
            dtype=np.uint32).tolist()
        np.savetxt('testData', rands)

    rands.sort(key=lambda k: k[1], reverse=True)  # 按高排序
    # rands.sort(key=lambda k: k[0]*k[1], reverse=True) # 面积排序
    clips = [[[0, 0], [r[0], 0], r, [0, r[1]]] for r in rands]  # 转为轮廓线
    # 绘制偏移，方便观察
    cliped = []
    offset = np.array([[20, 20]])
    cvUpdate = cvShow(img)
    color1 = (152, 255, 255)
    color2 = (0, 125, 255)

    stime = time.process_time()
    rearrange(boxes, clips)
    etime = time.process_time()
    print('>>>', etime - stime)

    cv2.waitKey(0)


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

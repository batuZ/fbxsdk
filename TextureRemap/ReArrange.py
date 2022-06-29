# polygong lib pyclipper
# CNdoc:https://www.cnblogs.com/zhigu/p/11943118.html
# https://blog.csdn.net/weixin_43624833/article/details/112919141

import numpy as np
import pyclipper

# 忽略小结构
IGNORE = 20
img = []
cvUpdate = None


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


def rearrange(boxes, clips):
    # 验证数据结构
    boxes = np.array(boxes)[:, :, :2]
    clips = np.array(clips)[:, :4, :2]
    pc = pyclipper.Pyclipper()
    cliped = []
    for clip in clips:
        pc.Clear()
        for box in boxes:
            boxSize = len(box)
            box = np.array(box)
            # 在容器中找到可用的参考点
            flag = False
            for b in range(boxSize):
                cur = box[b]  # 当前顶点，与下个顶点构成边
                nex = box[(b+1) % boxSize]  # 下一个顶点，可循环的索引
                sub = nex - cur  # 两顶点的差
                tmp = clip + cur  # 使用当前顶点的临时结果
                # 差大于0时边可用，临时结果与容器不相交
                if sub[0] > 0 and not isIntersect(tmp, box):
                    pc.AddPath(tmp, pyclipper.PT_CLIP, True)  # 裁剪多边型
                    cliped.append(tmp)
                    flag = True
                    break
            if flag:
                break

        pc.AddPath(box, pyclipper.PT_SUBJECT, True)  # 被裁多边型
        # 裁剪动作 2:pyclipper.CT_DIFFERENCE, 0:pyclipper.PFT_EVENODD
        boxes = pc.Execute(2, 0, 0)  # TODO 有可能产生多个box，需要处理一下

        # 清理小边
        for box in boxes:
            boxSize = len(box)
            for b in range(boxSize):
                perv = box[(b-1) % boxSize]
                cur = box[b]
                nex = box[(b+1) % boxSize]
                nexx = box[(b+2) % boxSize]
                if 0 < cur[1]-nex[1] < IGNORE:
                    nex[0], nex[1] = nexx[0], cur[1]
                # elif 0 > cur[1]-nex[1] > -IGNORE:
                #     cur[0], cur[1] = perv[0], nex[1]
                # if 0 < cur[0]-nex[0] < IGNORE:
                #     cur[0], cur[1] = nex[0], perv[1]
                # elif 0 > cur[0]-nex[0] > -IGNORE:
                #     nex[0] = cur[0]
                #     nexx[0] = cur[0]
        boxes = pyclipper.CleanPolygons(boxes)

        # 渲染结果
        if len(img):
            img[:, :, :] = [9*16, 8*16, 5*16]
            cv2.polylines(img, np.array(boxes)+offset,
                          True, (152, 255, 255), 2)
            cv2.polylines(img, np.array(cliped) +
                          offset, True, (0, 125, 255), 1)
            _showBoxId(img, offset, boxes)
            next(cvUpdate)
            pass  # 过程断点
    pass  # 完成断点


if __name__ == "__main__":
    import cv2

    # 模拟画布
    img = np.zeros((700, 800, 3), dtype=np.uint8)
    # 模拟容器
    boxes = [[[0, 0], [600, 0], [600, 600], [0, 600]]]
    # 模拟数据
    rands = np.random.randint(
        low=15,
        high=150,
        size=(63, 2),
        dtype=np.uint32).tolist()
    rands.sort(key=lambda k: k[1], reverse=True)  # 按高排序
    # rands.sort(key=lambda k: k[0]*k[1], reverse=True) # 面积排序
    clips = [[[0, 0], [r[0], 0], r, [0, r[1]]] for r in rands]  # 转为轮廓线
    # 绘制偏移，方便观察
    offset = np.array([[20, 20]])
    cvUpdate = cvShow(img)

    rearrange(boxes, clips)
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

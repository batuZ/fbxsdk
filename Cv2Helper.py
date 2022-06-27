from TextureRemap.utils import *
import numpy as np
import pyclipper
import cv2
# polygong lib pyclipper
# CNdoc:https://www.cnblogs.com/zhigu/p/11943118.html
# https://blog.csdn.net/weixin_43624833/article/details/112919141

# height, width, channel
img = np.zeros((700, 800, 3), dtype=np.uint8)
# 模拟画布
box = [[0, 0], [600, 0], [600, 600], [0, 600]]
bCpy = [[0, 0], [600, 0], [600, 600], [0, 600]]


def resetMap():
    img[:, :, :] = [9*16, 8*16, 5*16]
    subject = np.array(bCpy)+[10, 10]
    cv2.polylines(img, [subject], True, (0, 255, 255), 1)


def cvShow(data):
    while 1:
        cv2.imshow('pic', data)
        cv2.waitKey(1)
        tag = yield


resetMap()
cvUpdate = cvShow(img)


# 模拟vu集
rands = np.random.randint(15, high=300, size=(22, 2), dtype=np.uint32).tolist()
# 按高排序
rands.sort(key=lambda k: k[1], reverse=True)
clips = []
# 转为轮廓线
for r in rands:
    clips.append(np.array([[0, 0], [r[0], 0], r, [0, r[1]]], dtype=np.uint32))

# 重排逻辑
pc = pyclipper.Pyclipper()
for clip in clips:
    resetMap()
    boxSize = len(box)
    box = np.array(box)
    flite = []
    for b in range(boxSize):
        cur = box[b]
        nex = box[(b+1) % boxSize]
        sub = nex - cur
        tmp = clip + cur
        if sub[0] > 0 and not isIntersect(tmp, box):  # 在容器中找到基础，且与box不相交
            # 裁剪多边型
            pc.AddPath(tmp, pyclipper.PT_CLIP, True)
            cv2.polylines(img, [np.array(tmp)+[10, 10]],
                          True, (0, 125, 255), 1)
            break
    # 被裁多边型
    pc.AddPath(box, pyclipper.PT_SUBJECT, True)
    # 裁剪动作
    [box] = pc.Execute(pyclipper.CT_DIFFERENCE, pyclipper.PFT_EVENODD,
                       pyclipper.PFT_EVENODD)
    pc.Clear()
    # 清理box中的小边

    # 渲染结果
    cv2.polylines(img, [np.array(box)+[10, 10]], True, (152, 255, 255), 2)
    next(cvUpdate)
    pass  # 这里的断点可以查看重排过程

cv2.waitKey(0)

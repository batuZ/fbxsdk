import numpy as np
import pyclipper
import cv2

# polygong lib pyclipper
# CNdoc:https://www.cnblogs.com/zhigu/p/11943118.html
# https://blog.csdn.net/weixin_43624833/article/details/112919141


def cvShow(data):
    while 1:
        cv2.imshow('pic', data)
        cv2.waitKey(1)
        tag = yield


# height, width, channel
img = np.zeros((700, 800, 3), dtype=np.uint8)
img[:, :, :] = [9*16, 8*16, 5*16]
cvUpdate = cvShow(img)
pc = pyclipper.Pyclipper()

box = [[[0, 0], [600, 0], [600, 600], [0, 600]]]
subject = np.array(box)+[10, 10]
cv2.polylines(img, [subject], True, (0, 255, 255), 1)

# clip = np.array([[1, 1], [4, 1], [4, 4], [1, 4]])*10
# cv2.polylines(img, [clip], True, (0, 255, 255), 1)

rands = np.random.randint(15, high=300, size=(2, 2), dtype=np.uint32).tolist()
rands.sort(key=lambda k: k[1], reverse=True)
clips = []
x = 0
for r in rands:
    item = np.array([[0, 0], [r[0], 0], r, [0, r[1]]], dtype=np.uint32)
    clips.append(item)
    # cv2.polylines(img, [item+[10+x, 10]], True, (0, 255, 255), 1)
    # x += r[0]

for c in clips:
    pc.AddPath(box[0], pyclipper.PT_SUBJECT, True)
    pc.AddPath(c, pyclipper.PT_CLIP, True)
    box = pc.Execute(pyclipper.CT_XOR,
                     pyclipper.PFT_EVENODD, pyclipper.PFT_EVENODD)
    cv2.polylines(img, [np.array(box)+[10, 10]], True, (152, 255, 255), 2)
    next(cvUpdate)
#cv2.namedWindow('pic', cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)
cv2.imshow('pic', img)
cv2.waitKey(0)

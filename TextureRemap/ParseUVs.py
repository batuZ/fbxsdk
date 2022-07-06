from FbxCommon import *
import FbxHelper
import numpy as np
from utils import *

img = []
cvUpdate = None


def parseUV(texture, width, height, buffer=0):
    diffuseLayer = texture.GetDstProperty()
    materail = diffuseLayer.GetParent()
    iNode = materail.GetDstObject(1)
    iMesh = iNode.GetMesh()
    # 3、解析UV集
    uvGroups = iMesh.BGetUVGroups()
    ranges = []
    for grp in uvGroups:
        uvPercenContour = iMesh.BGetContourWithUVGroup(
            grp)  # ex: [[0.1, 0.1], [0.2, 0.2], ...]
        uvContour = np.array(uvPercenContour)*[width, height]
        rect = getRect(uv, buffer)
        ranges.append(rect)
        if len(img):
            h, w, _ = img.shape
            auv = [0, h] - np.array(uvPercen) * [-w, h]
            auv = np.array(auv, dtype=np.int32)
            cv2.polylines(img, ranges, True, (152, 255, 255), 1)
            next(cvUpdate)

    # 获取uv中最大宽高
    # resx = sorted(range(len(ranges)), key=lambda i: ranges[i][0], reverse=True)
    # maxx = ranges[resx[0]]
    # resy = sorted(range(len(ranges)), key=lambda i: ranges[i][1], reverse=True)
    # maxy = ranges[resy[0]]
    return ranges


if __name__ == "__main__":

    lSdkManager, lScene = InitializeSdkObjects()

    if not(LoadScene(lSdkManager, lScene, 'D:\\test.FBX')):
        print('load scene faild!!')

    for i in range(lScene.GetTextureCount()):
        tex = lScene.GetTexture(i)
        fileName = tex.GetFileName()
        img = cv2Reader(fileName)
        height, width, channel = img.shape
        scale = 600.0 / height
        img = cv2.resize(img, None, fx=scale, fy=scale)
        cvUpdate = cvShow(img, 'ori')

        groupRects = parseUV(tex, width, height)

    cv2.waitKey(0)

from FbxCommon import *
import FbxHelper
import numpy as np
from utils import *

img = []
cvUpdate = None
scale = 1
height, width, channel = 0, 0, 0
MIN_SIZE = 512
TAG_SIZE = 1024


def parseUV(texture):
    diffuseLayer = texture.GetDstProperty()
    materail = diffuseLayer.GetParent()
    iNode = materail.GetDstObject(1)
    iMesh = iNode.GetMesh()
    # 3、解析UV集
    done, tUVs = iMesh.GetTextureUV()
    uvGroups = iMesh.BGetUVGroups()
    uvs = []
    ranges = []
    area = 0  # 获取uv覆盖面积
    for grp in uvGroups:
        # TODO 这里可以尝试直接使用uv顶点，而不是轮廓线，对比下效率
        vuIds = iMesh.BGetContourWithUVGroup(grp)
        uvPercen = ID2UVP(tUVs, vuIds)
        uv = np.array(uvPercen)*[width, height]
        uvs.append(uv)
        ranges.append(getRange(uv))
        area += polygongArea(uv)
        if len(img):
            h, w, _ = img.shape
            auv = [0, h] - np.array(uvPercen) * [-w, h]
            auv = np.array(auv, dtype=np.int32)
            cv2.polylines(img, [auv], True, (152, 255, 255), 1)
            next(cvUpdate)

    # 获取uv中最大宽高
    resx = sorted(range(len(ranges)), key=lambda i: ranges[i][0], reverse=True)
    maxx = ranges[resx[0]]
    resy = sorted(range(len(ranges)), key=lambda i: ranges[i][1], reverse=True)
    maxy = ranges[resy[0]]

    # 贴图拆分创建策略：
    # 1、判断uv中最大长宽值，此值为不可拆分值，如果此值大于tag_size, 则判断最接近的2n:
    #       如果2n==tag_size, 则使用这个最大值创建新贴图，另一个边长需要通过面积确定
    #       如果2n>tag_size, 则使用2n创建新贴图, 另一个边长需要通过面积确定
    #       如果最大长宽是同一个uv, 则同时使用上面两个判定
    # 2、uv中最大长宽值都未超过tag_size，则需要通过面积策略确定使用多大的贴图，使用几个：
    #       将uv覆盖面积开平方，用此值找到最接近的2n
    # 3、uv覆盖面积开平方，小于tag_size时，
    pass


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
        cvUpdate = cvShow(img)

        parseUV(tex)
    cv2.waitKey(0)

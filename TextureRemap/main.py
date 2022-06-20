from FbxCommon import *
import cv2
import numpy as np
import math
import os

lSdkManager = None
lScene = None
MAX_SIZE = 0
TAG_SIZE = 512
output_log = True


def BFindBigTextureIds() -> [int]:
    '''在场景中找到过大贴图,返回Textue索引'''
    ids = []
    for i in range(lScene.GetTextureCount()):
        tex = lScene.GetTexture(i)
        fileName = tex.GetFileName()
        height, width = cv2Reader(fileName, cv2.IMREAD_GRAYSCALE).shape
        if width > MAX_SIZE or height > MAX_SIZE:
            ids.append(i)
    return ids


def BCheckMeshWithTextures(tIds) -> [FbxMesh]:
    '''通过纹理查找到Mesh'''
    meshes = []
    for i in tIds:
        tex = lScene.GetTexture(i)
        DiffuseLayer = tex.GetDstProperty()
        materail = DiffuseLayer.GetParent()
        iNode = materail.GetDstObject(1)
        iMesh = iNode.GetMesh()
        meshes.append(iMesh)
    return meshes


def BGetPolygonGroupCount(iMesh) -> int:
    '''创建polygonGroup并返回分组数'''
    # 记录一下已经被用过polyID
    checked = []
    polyCount = iMesh.GetPolygonCount()
    ctrlPoints = iMesh.GetPolygonVertices()
    groupId = 0
    while(len(checked) < polyCount):
        # 当前组中poly的顶点ID
        cIds = []
        last_cIds_len = -1
        # 当某个循环完成后多边形数量没有增加，则认为没有更多的同组成员了
        while(last_cIds_len != len(cIds)):
            last_cIds_len = len(cIds)
            for i in range(polyCount):
                # 跳过已经处理过的poly
                if i not in checked:
                    # 获取当前polygon的启始点在VerIndexes集合中的索引
                    pStartIndex = iMesh.GetPolygonVertexIndex(i)
                    pSize = iMesh.GetPolygonSize(i)
                    for j in range(pStartIndex, pStartIndex + pSize):
                        iVerIndex = ctrlPoints[j]
                        # 判断这个polygon上的顶点是否在当前组的顶点集合中
                        # 如果在则是同组，如果此集合中还没有成员，则直接塞入
                        if(iVerIndex in cIds or len(cIds) == 0):
                            # 设置分组编号
                            iMesh.SetPolygonGroup(i, groupId)
                            # 把已经处理的多边形塞进组，后面不会再处理这个多边形
                            checked.append(i)
                            # 相同组中的多边形都有共用的顶点，通过判断当前多边形中是否用了点集合中的顶点，来判断是否在当前组中
                            # 把当前多边形上的顶点塞进点集合，后面参考这里的顶点来判断是否在同一组中
                            cIds += BGetPolyPointIds(iMesh, pStartIndex, pSize)
                            break

        groupId += 1
        # progress report
        printInLine('>> check polygon group:', groupId, ' checkPoly:',
                    len(checked), "/", polyCount)
    return groupId


def BGetPolyPointIds(iMesh, lStartIndex, pSize) -> [int]:
    '''获取指定多边型的顶点索引'''
    res = []
    for j in range(pSize):
        iVerIndex = iMesh.GetPolygonVertices()[lStartIndex + j]
        res.append(iVerIndex)
    return res


def BGetPolygonsWithGroup(iMesh, gIndex) -> [int]:
    '''获取指定polygon组中的面'''
    grps = []
    for i in range(iMesh.GetPolygonCount()):
        if(iMesh.GetPolygonGroup(i) == gIndex):
            grps.append(i)
    return grps


def BGetOutlineWithGroup(iMesh, groupId=-1) -> [int]:
    '''找出mesh(polygonGroup)的外轮廓线'''
    edges = []
    polygons = range(iMesh.GetPolygonCount())

    if(groupId > -1):
        polygons = BGetPolygonsWithGroup(iMesh, groupId)

    for i in polygons:
        # 遍历当前polygon的edge，塞进一个集合（顶点数与边数相同）
        # 最后集合中的edges都是外轮廓线的一部份，但顺序不一定正确
        for j in range(iMesh.GetPolygonSize(i)):
            ed = iMesh.GetMeshEdgeIndexForPolygon(i, j)
            if(ed in edges):
                #### 判断集合中是否已存在，如果存在，说明此边为内部边线 ###
                # 把存在的remove掉，当前这个也不再塞入
                edges.remove(ed)
            else:
                ### 剩下的就是轮廓线的一部份 ###
                edges.append(ed)
        # progress report
        printInLine('>> check group outline', groupId, ': edge', len(edges))

    points = []
    # 相邻的edge一定有一个共用的顶点，前面的end与后面的start相同
    if(len(edges)):
        # 边集合中的第一个成员作为起点，把这个成员的两个点先塞进点集合
        # 同时把这个边成员从边集合中移除
        points += iMesh.GetMeshEdgeVertices(edges.pop(0))

    # region
    # 如果边线集合中所有的成员都被移除，则停止。
    # 此时闭合轮廓线最后一个顶点id应与第一个顶点id相同，如果不相同，则轮廓线不闭合。
    # 如果edges集合中还有成员，但最后一个顶点id已经与第一个顶点id相同，则停止。
    # 此时轮廓线提前闭合，只返回第一个轮廓线。
    # 说明1、模型中有相邻的面但法线相反，2、输入了一个以上的polygonGroup
    # endregion
    while(len(edges) and points[0] != points[-1]):
        # 从剩余的边成员中找出一个edge,与顶点集合最后一个元素比较
        for i in edges:
            s, e = iMesh.GetMeshEdgeVertices(i)
            # 顶点集合最后一个元素就是前一个边的end,如果当前边的start与end相同，则是邻边
            if s == points[-1]:
                # 将当前edge的顶点索引取出塞进点集合，同时从边集合中移除
                points.append(e)
                edges.remove(i)
                break

        # progress report
        printInLine('>> check group outline', groupId, ': edge', len(edges))
    return points


def BGetImagePolygon(iMesh, imgX, imgY, points=[]) -> [[float, float], [float, float], ...]:
    '''模型轮廓线转纹理图像坐标轮廓线'''
    res = []
    done, tUVs = iMesh.GetTextureUV()
    if(done):
        for p in points:
            x = tUVs[p][0] * imgX
            y = (tUVs[p][1]) * imgY
            res.append([x, y])
    return res


def UV2IMG(points):
    res = []
    for i in points:
        x = round(i[0], 0)
        y = round(2048-i[1], 0)
        res.append([x, y])
    return res


def test(points):
    img = cv2Reader('D:\\datas\\SINGLE_MODEL_ID.fbm\\SB0661.jpg')
    imgPoints = UV2IMG(points)
    cv2.polylines(img, [np.array(imgPoints, np.int32)],
                  False, (0, 255, 255), 2)
    cv2.namedWindow('pic', cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)
    cv2.imshow('pic', img)
    cv2.waitKey(0)


def readImage(filePath):
    # tt = cv2.imread(filePath)C:\Users\30470\Pictures
    tt = cv2Reader('C:\\Users\\30470\\Pictures\\微信图片_20220425105356.jpg')
    # cv2.imshow('IMREAD_UNCHANGED+Color', tt)
    # cv2.waitKey()
    imgZero = np.zeros((100, 200, 3), np.uint8)
    showImage(imgZero)
    pass


def writeImage(outPath):
    newImg = np.zeros((100, 200, 3), np.uint8)
    cv2.imwrite(outPath, newImg)


def showImage(img):
    cv2.imshow('image', img)
    cv2.waitKey()


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


def printInLine(*msg) -> None:
    '''单行输出'''
    if output_log:
        print('\b'*1000, end='')
        print(*msg, ' '*20, end='')


def is_equal(p1, p2):
    '''判断两点是否重合'''
    count1 = len(p1)
    count2 = len(p2)
    # 判断维度
    if count1 != count2:
        return False
    # 判断值
    sum = 0
    for i in range(count1):
        sum += abs(p1[i] - p2[1])
    return sum < 1e-4


def getIntersection(p1, p2, p3, p4) -> (float, float):
    '''两直线求交点'''
    if abs(p1[0] - p2[0]) > 1e-3:
        X1, Y1 = p1
        X2, Y2 = p2
        X3, Y3 = p3
        X4, Y4 = p4
    elif abs(p3[0] - p4[0]) > 1e-3:
        X1, Y1 = p3
        X2, Y2 = p4
        X3, Y3 = p1
        X4, Y4 = p2
    else:
        # 必须有一条线不是垂直的
        return None

    # line1
    A1 = Y2 - Y1
    B1 = X1 - X2
    C1 = X2 * Y1 - X1 * Y2

    # line2
    A2 = Y4 - Y3
    B2 = X3 - X4
    C2 = X4 * Y3 - X3 * Y4

    # TODO 判断是否为平行线

    X = (B2 * (C1 / B1) - C2) / (A2 - B2 * (A1 / B1)+1e-3)
    Y = -X * A1 / B1 - C1 / B1
    return (X, Y)


def getOffset(start_point, end_point, distance):
    '''获取edge在指定距离上的平行线, 平行线方向由edge的方向决定'''
    p1x = start_point[0]
    p1y = start_point[1]
    p2x = end_point[0]
    p2y = end_point[1]
    u = math.atan2(abs(p1x-p2x), abs(p1y-p2y))*180/math.pi
    x_direction = -1 if p1y > p2y else 1
    y_direction = -1 if p1x < p2x else 1
    x_offset = distance * math.cos(u * math.pi / 180) * x_direction
    y_offset = distance * math.sin(u * math.pi / 180) * y_direction
    return (x_offset, y_offset)

# TODO 需要重写buffer算法
# 参考 https://blog.csdn.net/qq_41655524/article/details/105384777


def createBuffer(polygon, distance):
    '''创建闭合多边形Buffer'''
    bufPolygon = []
    # region 因为是轮廓线，暂时不考虑不闭合逻辑
    # 如果线不闭合，先把第一个点塞进去，不需要求交
    # isRingPolygon = is_equal(polygon[0], polygon[-1])
    # if not isRingPolygon:
    #     x_offset, y_offset = getBufOffset(polygon[0], polygon[1], distance)
    #     newPolygon.append([polygon[0][0] + x_offset, polygon[0][1] + y_offset])
    # endregion
    edgeCount = len(polygon)-1
    for i in range(edgeCount):
        # 循环索引
        i_p1 = i
        i_p2 = (i+1) % edgeCount
        i_p3 = (i+2) % edgeCount
        l1s = polygon[i_p1]  # line1start
        l1e = polygon[i_p2]  # line1end
        l2s = polygon[i_p2]  # line2start
        l2e = polygon[i_p3]  # line2end
        offset_x1, offset_y1 = getOffset(l1s, l1e, distance)
        offset_x2, offset_y2 = getOffset(l2s, l2e, distance)
        p1 = [l1s[0] + offset_x1, l1s[1] + offset_y1]
        p2 = [l1e[0] + offset_x1, l1e[1] + offset_y1]
        p3 = [l2s[0] + offset_x2, l2s[1] + offset_y2]
        p4 = [l2e[0] + offset_x2, l2e[1] + offset_y2]
        x, y = getIntersection(p1, p2, p3, p4)
        bufPolygon.append([x, y])
    # 一定闭合的前提下，把最后一个点的副本放在数组前，完成buffer的闭合
    return [bufPolygon[-1]] + bufPolygon


def getBoundingBox(polygong):
    '''获取polygon包围盒'''
    minx = miny = float('inf')
    maxx = maxy = float('-inf')
    for poi in polygong:
        minx = poi[0] if poi[0] < minx else minx
        maxx = poi[0] if poi[0] > maxx else maxx
        miny = poi[1] if poi[1] < miny else miny
        maxy = poi[1] if poi[1] > maxy else maxy
    return minx, maxx, miny, maxy


def SortPolygonsBySize(iMesh):
    pass


def SortPolygonsByArea(iMesh):
    pass


if __name__ == "__main__":

    lSdkManager, lScene = InitializeSdkObjects()

    if not(LoadScene(lSdkManager, lScene, 'D:\\test.FBX')):
        print('load scene faild!!')

    # The coordinate system's original Up Axis when the scene is created. 0 is X, 1 is Y, 2 is Z axis.
    upAxis = lScene.GetGlobalSettings().GetOriginalUpAxis()  # Z-UP
    print('upAxis:', upAxis)

    # 1、找到所有超尺寸贴图
    targetTextures = BFindBigTextureIds()

    # 2、处理使用大贴图的模型
    meshes = BCheckMeshWithTextures(targetTextures)

    # 3、找出每个mesh的多边形组
    for iMesh in meshes:
        print('\n----- Mesh: %s / %s -----' %
              (meshes.index(iMesh)+1, len(meshes)))
        groupCount = BGetPolygonGroupCount(iMesh)
        for g in range(groupCount):
            pointIds = BGetOutlineWithGroup(iMesh, g)
            # 4、通过UV获得贴图坐标的多边形数组
            imgPoints = BGetImagePolygon(iMesh, 2048, 2048, pointIds)
            bufPoints = createBuffer(imgPoints, 8)
            # 5、创建512空画布，填充uv多边形，填满则创建新多边形
            test(bufPoints)
    # 6、创建materail，引用512贴图，设置mesh材质id

    # 7、清除未引用materail，导出新fbx

    lSdkManager.Destroy()
    sys.exit(0)

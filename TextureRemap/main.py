from FbxCommon import *
import cv2
import numpy as np
import math
import os

# polygong lib pyclipper
# CNdoc:https://www.cnblogs.com/zhigu/p/11943118.html
# EX:https://blog.csdn.net/weixin_43624833/article/details/112919141
import pyclipper

lSdkManager = None
lScene = None
MAX_SIZE = 0
TAG_SIZE = 512
output_log = True


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


def BGetContourWithGroup(iMesh, groupId=-1) -> [int]:
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
        printInLine('>> check group contour', groupId, ': edge', len(edges))

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
        printInLine('>> check group contour', groupId, ': edge', len(edges))
    return points


def ID2UV(iMesh, imgX, imgY, points):
    '''模型轮廓线转纹理图像坐标轮廓线'''
    res = []
    done, tUVs = iMesh.GetTextureUV()
    if(done):
        for p in points:
            x = tUVs[p][0] * imgX
            y = (tUVs[p][1]) * imgY
            res.append([x, y])
    return res


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


def UV2IMG(height, points):
    '''uv坐标转图像坐标, 图像坐标向下为Y增'''
    res = []
    for i in points:
        res.append([i[0], height-i[1]])
    return res


def showImage(img, points):
    cv2.polylines(img, np.array(points, np.int32), True, (0, 255, 255), 2)
    cv2.namedWindow('pic', cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)
    cv2.imshow('pic', img)


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


def GetUVGroupCount(iMesh):
    layerUV = iMesh.GetElementUV()
    # uv坐标集
    vuPoint = layerUV.GetDirectArray()
    # uv索引集
    uvIndex = layerUV.GetIndexArray()
    # 多边形数，uv与mesh的多边形一定是一一对应的
    polygonCount = iMesh.GetPolygonCount()
    # 存放uv多边型坐标索引（n,pSize）
    uvPolygons = []
    # 存放uv多边型边索引（n,pSize）
    uvPolyEdges = []
    # uvEdge集
    uvEdges = []
    # 依据polygon遍历uv索引集
    for i in range(polygonCount):
        polySize = iMesh.GetPolygonSize(i)

        # 解析uv多边形
        poly = []
        for j in range(polySize):
            uv = uvIndex[i*polySize + j]
            poly.append(vu)
        uvPolygons.append(poly)

        # 解析uv边，edgeSize == polySize
        for k in range(polySize):
            start = poly[k]
            end = poly[k+1]
            # 每个edge在创建之前都要找一下是不是其它面的共边，如果是则直接引用
            currusEdge = None
            edgeId = uvEdgeCount = len(uvEdges)
            for l in range(uvEdgeCount):
                edge = uvEdgeCount[l]
                # 一个edge最多被两个三角面引用，而方向相反
                if edge == [end, start]:
                    currusEdge = edge
                    break

            uvEdges.append([start, end])


def test(iMesh):
    layerUV = iMesh.GetElementUV()
    vuPoint = layerUV.GetDirectArray()
    uvIndex = layerUV.GetIndexArray()
    ctrlPoints = iMesh.GetPolygonVertices()
    polygonCount = iMesh.GetPolygonCount()
    for i in range(polygonCount):
        polySize = iMesh.GetPolygonSize(i)
        for j in range(polySize):
            ver = iMesh.GetPolygonVertex(i, j)
            uv = uvIndex[i*polySize + j]
            vec4 = iMesh.GetControlPointAt(ver)
            print('poly: %s, num: %s, vertex: %s, uv: %s, vec2: %s' %
                  (i, j, ver, uv, vec4))
            edge = iMesh.GetMeshEdgeIndexForPolygon(i, j)
            start, end = iMesh.GetMeshEdgeVertices(edge)
            print('poly: %s, num: %s, edge: %s, start: %s, end: %s' %
                  (i, j, edge, start, end))
        print('------------------')
    pass


if __name__ == "__main__":

    lSdkManager, lScene = InitializeSdkObjects()

    if not(LoadScene(lSdkManager, lScene, 'D:\\test2.FBX')):
        print('load scene faild!!')

    # The coordinate system's original Up Axis when the scene is created. 0 is X, 1 is Y, 2 is Z axis.
    upAxis = lScene.GetGlobalSettings().GetOriginalUpAxis()  # Z-UP
    print('upAxis:', upAxis)

    # 1、找到所有超尺寸贴图
    for i in range(lScene.GetTextureCount()):
        tex = lScene.GetTexture(i)
        fileName = tex.GetFileName()
        img = cv2Reader(fileName)
        height, width, channel = img.shape
        if width > MAX_SIZE or height > MAX_SIZE:
            # 2、处理使用大贴图的模型
            DiffuseLayer = tex.GetDstProperty()
            materail = DiffuseLayer.GetParent()
            iNode = materail.GetDstObject(1)
            iMesh = iNode.GetMesh()
            test(iMesh)
            # 3、找出每个mesh的多边形组
            groupCount = BGetPolygonGroupCount(iMesh)
            # 4、通过UV映射找到纹理多边形
            for g in range(groupCount):
                idPoints = BGetContourWithGroup(iMesh, g)
                uvPoints = ID2UV(iMesh, width, height, idPoints)
                imgPoints = UV2IMG(height, uvPoints)
                # showImage(img, [imgPoints])# unbuffer
                buffer = buffer_contour(imgPoints, 6)
                showImage(img, buffer)

                # 5、创建空画布，填充uv多边形，填满则创建新多边形

    # 6、创建materail，引用贴图，设置mesh材质id

    # 7、清除未引用materail，导出新fbx
    cv2.waitKey(0)
    lSdkManager.Destroy()
    sys.exit(0)

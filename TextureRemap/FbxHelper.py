from FbxCommon import *
from utils import *


def _getPointIds(iMesh, lStartIndex, pSize) -> [int]:
    '''获取指定多边型的顶点索引'''
    res = []
    for j in range(pSize):
        iVerIndex = iMesh.GetPolygonVertices()[lStartIndex + j]
        res.append(iVerIndex)
    return res


def GetPolygonGroupCount(self: FbxMesh):
    '''创建polygonGroup并返回分组数'''
    if not hasattr(self, 'PolygonGroupCount'):
        # 记录一下已经被用过polyID
        checked = []
        polyCount = self.GetPolygonCount()
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
                        pStartIndex = self.GetPolygonVertexIndex(i)
                        pSize = self.GetPolygonSize(i)
                        for j in range(pStartIndex, pStartIndex + pSize):
                            # TODO 当前为共点分组，应该使用共边分组，在使用此函数前要参考vu分组修改为共边逻辑
                            iVerIndex = self.GetPolygonVertices()[j]
                            # 判断这个polygon上的顶点是否在当前组的顶点集合中
                            # 如果在则是同组，如果此集合中还没有成员，则直接塞入
                            if(iVerIndex in cIds or len(cIds) == 0):
                                # 设置分组编号
                                self.SetPolygonGroup(i, groupId)
                                # 把已经处理的多边形塞进组，后面不会再处理这个多边形
                                checked.append(i)
                                # 相同组中的多边形都有共用的顶点，通过判断当前多边形中是否用了点集合中的顶点，来判断是否在当前组中
                                # 把当前多边形上的顶点塞进点集合，后面参考这里的顶点来判断是否在同一组中
                                cIds += _getPointIds(self, pStartIndex, pSize)
                                break
            groupId += 1
            # progress report
            printInLine('>> check polygon group:', groupId, ' checkPoly:',
                        len(checked), "/", polyCount)
        self.PolygonGroupCount = groupId

    return self.PolygonGroupCount


def GetPolygonsWithGroup(self, gIndex) -> [int]:
    '''获取指定polygon组中的面索引'''
    grps = []
    for i in range(self.GetPolygonCount()):
        if(self.GetPolygonGroup(i) == gIndex):
            grps.append(i)
    return grps


def GetContourWithGroup(self, groupId=-1) -> [int]:
    '''找出mesh(polygonGroup)的外轮廓线上的顶点索引'''
    edges = []
    polygons = range(self.GetPolygonCount())

    if(groupId > -1):
        polygons = self.BGetPolygonsWithGroup(groupId)

    for i in polygons:
        # 遍历当前polygon的edge，塞进一个集合（顶点数与边数相同）
        # 最后集合中的edges都是外轮廓线的一部份，但顺序不一定正确
        for j in range(self.GetPolygonSize(i)):
            ed = self.GetMeshEdgeIndexForPolygon(i, j)
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
        points += self.GetMeshEdgeVertices(edges.pop(0))

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
            s, e = self.GetMeshEdgeVertices(i)
            # 顶点集合最后一个元素就是前一个边的end,如果当前边的start与end相同，则是邻边
            if s == points[-1]:
                # 将当前edge的顶点索引取出塞进点集合，同时从边集合中移除
                points.append(e)
                edges.remove(i)
                break

        # progress report
        printInLine('>> check group contour', groupId, ': edge', len(edges))
    return points


def GetContourWithUVGroup(self, uvPolygons):
    edges = []
    for poly in uvPolygons:
        polyEdges = self.BGetUVPolygongEdges(poly)
        for ed in polyEdges:
            if ed in edges:
                edges.remove(ed)
            else:
                edges.append(ed)
    points = []
    if(len(edges)):
        points += self.BGetUVEdge(edges.pop(0))

    # TODO 这个条件判断会忽略holes，如果需要hole，这里要重写
    while(len(edges) and points[0] != points[-1]):
        for i in edges:
            s, e = self.BGetUVEdge(i)
            if s == points[-1]:
                points.append(e)
                edges.remove(i)
                break
    return points


def _parseMeshUV(iMesh):
    '''解析MeshUV, 得到UVPolygons,UVEdges'''
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
            poly.append(uv)
        uvPolygons.append(poly)

        # 解析uv边，edgeSize == polySize
        ed = []
        for k in range(polySize):
            start = poly[k]
            end = poly[(k+1) % polySize]
            # 每个edge在创建之前都要找一下是不是其它面的共边，如果是则直接引用
            currusEdge = None
            edgeId = uvEdgeCount = len(uvEdges)
            for l in range(uvEdgeCount):
                edge = uvEdges[l]
                # 一个edge最多被两个三角面引用，而且方向相反
                if edge == [end, start]:
                    currusEdge = edge
                    edgeId = l
                    break

            ed.append(edgeId)
            if currusEdge == None:
                uvEdges.append([start, end])

        uvPolyEdges.append(ed)

    iMesh.UVPolygons = uvPolygons
    iMesh.UVEdges = uvEdges
    iMesh.UVPolygongEdges = uvPolyEdges


def GetUVPolygons(self):
    '''获取全部UV多边形'''
    if not hasattr(self, 'UVPolygons'):
        _parseMeshUV(self)
    return self.UVPolygons


def GetUVPolygongEdges(self, uvPolyIndex):
    if not hasattr(self, 'UVPolygongEdges'):
        _parseMeshUV(self)
    return self.UVPolygongEdges[uvPolyIndex]


def GetUVEdge(self, uvEdgeIndex):
    if not hasattr(self, 'UVEdges'):
        _parseMeshUV(self)
    return self.UVEdges[uvEdgeIndex]


def GetUVGroups(self):
    if not hasattr(self, 'UVGroups'):
        self.UVGroups = []
        checked = []
        uvPolygons = self.BGetUVPolygons()
        while(len(checked) < len(uvPolygons)):
            cIds = []
            grp = []
            last_cIds_len = -1
            while(last_cIds_len != len(cIds)):
                last_cIds_len = len(cIds)
                for i in range(len(uvPolygons)):
                    if i not in checked:
                        edges = self.BGetUVPolygongEdges(i)
                        for edge in edges:
                            if(edge in cIds or len(cIds) == 0):
                                cIds += edges
                                checked.append(i)
                                grp.append(i)
                                break
            self.UVGroups.append(grp)
    return self.UVGroups


FbxMesh.BGetPolygonGroupCount = GetPolygonGroupCount
FbxMesh.BGetPolygonsWithGroup = GetPolygonsWithGroup
FbxMesh.BGetContourWithGroup = GetContourWithGroup

FbxMesh.BGetUVPolygons = GetUVPolygons
FbxMesh.BGetUVPolygongEdges = GetUVPolygongEdges
FbxMesh.BGetUVEdge = GetUVEdge
FbxMesh.BGetUVGroups = GetUVGroups
FbxMesh.BGetContourWithUVGroup = GetContourWithUVGroup

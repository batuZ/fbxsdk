#
#   把一个面积值拆分成多个以2的n次幂为边长的矩形
#   用于UV重映射时，创建需要的贴图文件
#

import numpy as np


def _findMin2n(num):
    n = 0
    while num >= 2**n:
        n += 1
    return n-1


def _split(area, min, max, maxItem=[0, 0]):
    t = 2**_findMin2n(area**0.5)
    t = t if area >= min*min else min
    t = t if t <= max else max
    tw = t if t > maxItem[0] else maxItem[0]
    th = t if t > maxItem[1] else maxItem[1]
    maxItem = [0, 0]
    if area > tw*th:
        res = [tw, th] + _split(area-tw*th, min, max)
    else:
        res = [tw, th]

    return res


def _mergeResults(arr, max):
    # 合并尺寸相同的块，可降低损耗
    res = []
    stop = len(arr)
    while len(arr):
        tag = arr.pop(0)
        for rec in arr:
            if tag == rec:
                if tag[0] == tag[1] < max:
                    tag[0] *= 2
                elif tag[1] < max:
                    tag[1] *= 2
                arr.remove(rec)
                break
        res.append(tag)
    if len(res) == stop:
        return res
    else:
        return _mergeResults(res, max)


def split2powN(area, min=128, max=1024, maxItem=[0, 0]):
    '''split_2powN_withArea'''
    splitRes = _split(area, min, max, maxItem)
    formatRes = np.array(splitRes).reshape(-1, 2).tolist()
    # print('beforMerge:', formatRes)
    mergeRes = _mergeResults(formatRes, max)
    # print('afterMerge:', mergeRes)
    return mergeRes


if __name__ == "__main__":
    import random
    # 随机测试数据
    testArea = random.randint(0, 2999**2)
    # 测试数据
    #testArea = 2314**2 + 2321**2

    # 一次性获取
    res = split2powN(testArea, 128, 2048)
    resArea = sum([g[0]*g[1] for g in res])
    print(res)
    print('resArea - testArea:', resArea-testArea)

    # 递进获取
    tRes = []
    while testArea > 0:
        nex = split2powN(testArea, 128, 2048, [522, 0])
        testArea -= nex[0][0]*nex[0][1]
        print(nex[0])

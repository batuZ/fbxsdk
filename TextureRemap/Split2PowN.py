#
#   把一个面积值拆分成多个以2的n次幂为边长的矩形
#   用于UV重映射时，创建需要的贴图文件
#

def findMin2n(num):
    n = 0
    while num >= 2**n:
        n += 1
    return n-1


def split2powN(area, min=128, max=1024):
    '''split_2powN_withArea'''
    t = 2**findMin2n(area**0.5)  # ex: 1024
    t = t if area >= min*min else min  # 限制最小size
    t = t if t <= max else max
    # 4*t**2 == 2**(n+1), 不会出现area >= 4*t**2
    # 2**n 一定小于area, 极小可能等于area

    #  _____    _____
    # |_____|  |  |__|
    # |__| ..  |__| ..
    # if area > 3*t*t:
    #     cur = [t*2, t*2]
    #     last = split2powN(area-3*t*t)
    #     res = cur + last

    #  _____    __
    # |_____|  |  |
    #  ..      |__| ..
    if area > 2*t*t:
        cur = [t*2, t]
        last = split2powN(area-2*t*t)
        if cur == last:
            res = [t*2, t*2]  # 当递归值等于当前值时，合并结果
        else:
            res = cur + last

    #  __
    # |__| ..
    elif area > t*t:
        cur = [t, t]
        last = split2powN(area-t*t)
        if cur == last:
            res = [t*2, t]  # 当递归值等于当前值时，合并结果
        else:
            res = cur + last

    #  __
    # |__|
    else:  # area <= t*t
        res = [t, t]

    return res


if __name__ == "__main__":
    import numpy as np
    testArea = 2048**2 + 1233**2 + 1233**2
    res = np.array(split2powN(testArea, 128, 2048)).reshape(-1, 2)
    print(res)
    resArea = sum([g[0]*g[1] for g in res])
    print('resArea - testArea:', resArea-testArea)

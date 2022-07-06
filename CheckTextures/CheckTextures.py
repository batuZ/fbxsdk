import os
import json
from FbxCommon import *
from PIL import Image  # 安装图像库 pip install pillow


def SearchFiles(path, fileType):
    # 递归找文件
    fileList = []
    for root, subDirs, files in os.walk(path):
        for fileName in files:
            if fileName.lower().endswith(fileType.lower()):
                fileList.append(os.path.join(root, fileName))
    return fileList


def is2n(num):
    # 判断是否2的N次幂
    for n in range(20):
        if num == 2**n:
            return True
    return False


if __name__ == "__main__":

    # 阈值
    maxSize = 4096

    # 根目录
    root_dir = "D:\\datas"

    res = {}
    texCount = 0
    pobTexCount = 0

    fileList = SearchFiles(root_dir, '.fbx')

    for p in fileList:
        # 读fbx
        lSdkManager, lScene = InitializeSdkObjects()
        if not(LoadScene(lSdkManager, lScene, p)):
            continue

        meshes = {}
        texCount += lScene.GetTextureCount()
        checked = []

        for i in range(lScene.GetTextureCount()):
            tex = lScene.GetTexture(i)
            fileName = tex.GetFileName()

            # 不存在的和已经检查过的，跳过
            if not os.path.exists(fileName) or fileName in checked:
                continue

            # 读贴图
            img = Image.open(fileName)
            width = img.width
            height = img.height

            # 检查过大的，不是2n的
            if max(height, width) > maxSize or not (is2n(height) and is2n(width)):
                pobTexCount += 1

                # 纹理 >> 图层 >> 材质 >> 节点
                iNode = tex.GetDstProperty().GetParent().GetDstObject(1)

                # 写进报告
                if not meshes.__contains__(iNode.GetName()):
                    meshes[iNode.GetName()] = []

                meshes[iNode.GetName()].append(
                    {fileName: '{}x{}'.format(width, height)})

                # 标记为已检查，避免复用的贴图被重复检查
                checked.append(fileName)

        # 写进报告
        if len(meshes):
            res[p] = meshes

        print('{}/{}:{}'.format(fileList.index(p), len(fileList), p))

    # 写出文件
    with open('report.json', 'w') as write_f:
        json.dump(res, write_f, indent=4)

    print('---------------------------------------')
    print(' FBX: {}/{}'.format(len(res), len(fileList)))
    print(' Texture: {}/{}'.format(pobTexCount, texCount))
    print('---------------------------------------')

import gdal

ds = None
iBand = None
geotransform = None
minValue = -11034.0  # 可用的最小值，马里亚纳海沟
maxValue = 8848.86  # 可用的最大值，珠峰
unCheckValue = 0    # 未能正常获取高度值时，使用此值

input_file = 'D:\\datas\\ast\\390610.FBX'
output_file = 'D:\\datas\\ast\\390610_1.FBX'
dem_tiff_file = 'D:\\datas\\suzhou_data\\gusu_dem\\DEM\\GS_DEM.tif'


def check_mesh(lScene):
    ''' 遍历场景中的mesh,修改node高度值 '''
    geomCount = lScene.GetGeometryCount()
    for i in range(geomCount):
        iMesh = lScene.GetGeometry(i)
        iNode = iMesh.GetNode()
        x, y, z = iNode.LclTranslation.Get()  # 取坐标时需要留意是Y-Up还是Z-Up
        double3 = FbxDouble3(x, y + getHeight(x, -z), z)
        iNode.LclTranslation.Set(double3)


def getHeight(x, y):
    '''根据坐标获取高度值'''
    res = unCheckValue
    line, column = world2Pixel(geotransform, x, y)
    if 0 < line < ds.RasterXSize and 0 < column < ds.RasterYSize:
        res = iBand.ReadAsArray(line, column, 1, 1)[0][0]
    if not minValue < res < maxValue:
        res = unCheckValue
    return res


def Pixel2world(geotransform, line, column):
    '''像素坐标转地理坐标'''
    originX = geotransform[0]
    originY = geotransform[3]
    pixelWidth = geotransform[1]
    pixelHeight = geotransform[5]
    x = column*pixelWidth + originX - pixelWidth/2
    y = line*pixelHeight + originY - pixelHeight/2
    return(x, y)


def world2Pixel(geotransform, x, y):
    '''地理坐标转像素坐标'''
    originX = geotransform[0]
    originY = geotransform[3]
    pixelWidth = geotransform[1]
    pixelHeight = geotransform[5]
    line = int((y-originY)/pixelHeight)+1
    column = int((x-originX)/pixelWidth)+1
    return(line, column)


if __name__ == "__main__":
    try:
        from FbxCommon import *
    except ImportError:
        print('load sdklibs faild!!')
        sys.exit(1)

    # 加载gdal
    ds = gdal.Open(dem_tiff_file)
    if not ds:
        print('load dem faild!!')
        sys.exit(1)

    iBand = ds.GetRasterBand(1)
    geotransform = ds.GetGeoTransform()

    # 加载fbx场景
    lSdkManager, lScene = InitializeSdkObjects()

    if not(LoadScene(lSdkManager, lScene, input_file)):
        print('load scene faild!!')
        lSdkManager.Destroy()
        sys.exit(0)

    # 处理单位
    if lScene.GetGlobalSettings().GetSystemUnit() != FbxSystemUnit.m:
        FbxSystemUnit.m.ConvertScene(lScene)

    # 处理轴类型
    # The coordinate system's original Up Axis when the scene is created. 0 is X, 1 is Y, 2 is Z axis.
    # upAxis = lScene.GetGlobalSettings().GetOriginalUpAxis()  # Z-UP

    # 处理场景
    check_mesh(lScene)

    # 保存
    SaveScene(
        lSdkManager,    # pSdkManager
        lScene,         # pScene
        output_file,    # pFilename
        3,              # pFileFormat
        True            # pEmbedMedia
    )

    lSdkManager.Destroy()
    sys.exit(0)

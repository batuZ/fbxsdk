### 运行环境
1. python-3.7.9-x64
2. fbxsdk202021, 参考install Python FBX文档配置fbxsdk开发环境


### 运行脚本
1. 安装GDAL的python库，`pip install gdal`
2. 配置main.py里的输入参数
3. python main.py


### install Python FBX

install Python FBX:
Go to http://www.autodesk.com/fbx.

Navigate to the Downloads page.

Find the version of Python Binding for your development platform.

Download the file and install the Python Binding.

Let’s call the directory where you installed the Python Binding for FBX as <yourFBXPythonSDKpath>.

Determine the directory name (<Python*xxxxxx>) of the version of Python FBX that you wish to install (see Platforms supported).

Copy the contents of <yourFBXPythonSDKpath>\<version>\lib\<Pythonxxxxx>\ into:

Windows: yourPythonPath\Lib\site-packages\
Mac OSX: /Library/Python/x.x/site-packages/
Linux: /usr/local/lib/pythonx.x/site-packages/
Optional: Copy the sample programs for Python FBX to a suitable location. The samples are in <yourFBXPythonSDKpath>\<version>.
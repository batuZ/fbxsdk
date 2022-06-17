#include <iostream>
#include <string>

#include "Common.h"
#include "FromTextures.h"


//static const char* sInputFile = "sadface.fbx";
static const char* sInputFile = "D:\\gs.FBX";

//output file path
static const char* sOutputFile = "happyface.fbx";

int main()
{

	//FBX SDK Default Manager
	FbxManager* lSdkManager = NULL;

	//Scene to load from file
	FbxScene* lScene = NULL;

	// Prepare the FBX SDK.
	InitializeSdkObjects(lSdkManager, lScene);

	// Load the scene.
	bool lResult = LoadScene(lSdkManager, lScene, sInputFile);

	if (lResult == false)
	{
		FBXSDK_printf("\n\nAn error occurred while loading the scene...");
	}
	else
	{
		check_textures(lScene);
	}

	// Destroy all objects created by the FBX SDK.
	DestroySdkObjects(lSdkManager, lResult);
	return 0;
}


// 获取mesh三角面的贴图索引
//FbxMesh* iMesh = iNode->GetMesh();
//const char* meshName = iMesh->GetName();
//int elementMaterilCount = iMesh->GetElementMaterialCount();
//FbxLayerElementArrayTemplate<int>* pMaterialIndices = &iMesh->GetElementMaterial()->GetIndexArray();
//int getCount = pMaterialIndices->GetCount();
//int materialIndex = pMaterialIndices->GetAt(10000);
//
//FbxGeometryElement::EMappingMode materialMappingMode = FbxGeometryElement::eNone;
//materialMappingMode = iMesh->GetElementMaterial()->GetMappingMode();


// 获取尺寸
//unsigned int unWidth = 0, unHeight = 0;
//GetPicWidthHeight(lTexPath.c_str(), &unWidth, &unHeight);
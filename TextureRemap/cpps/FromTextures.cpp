#include <iostream>
#include "FromTextures.h"
#include "ImgSize.h"



// 通过lScene->GetTextureCount检索
void check_textures(FbxScene* lScene)
{
	int texCount = lScene->GetTextureCount();
	unsigned int unWidth = 0, unHeight = 0;
	const int maxSize = 256;
	std::cout << "-------------- " << texCount << "-------------- " << std::endl;
	for (int i = 0; i < texCount; i++)
	{
		FbxTexture* txe = lScene->GetTexture(i);
		FbxFileTexture* fTex = FbxCast<FbxFileTexture>(txe);
		std::string fileName = fTex->GetFileName();
		GetPicWidthHeight(fileName.c_str(), &unWidth, &unHeight);
		std::cout << "  name: --> " << i << "  " << fileName ;
		std::cout << "  width:" << unWidth << "  height:" << unHeight << std::endl;
		auto aaa = txe->GetSrcObject();
		std::cout << "-------------- " << aaa << "-------------- " << std::endl;
	}
}




// 获取尺寸
//unsigned int unWidth = 0, unHeight = 0;
//GetPicWidthHeight(lTexPath.c_str(), &unWidth, &unHeight)


// node -> maiterial -> texture -> UV
void check_uv(FbxMesh* pMesh) {
	FbxStringList lUVSetNameList;
	pMesh->GetUVSetNames(lUVSetNameList);
	int uvNameCount = lUVSetNameList.GetCount();
	char* lUVSetName = lUVSetNameList.GetStringAt(0);

	const FbxGeometryElementUV* lUVElement = pMesh->GetElementUV(lUVSetName);

	if (lUVElement->GetMappingMode() != FbxGeometryElement::eByPolygonVertex &&
		lUVElement->GetMappingMode() != FbxGeometryElement::eByControlPoint)
		return;

	//index array, where holds the index referenced to the uv data
	const bool lUseIndex = lUVElement->GetReferenceMode() != FbxGeometryElement::eDirect;
	const int lIndexCount = (lUseIndex) ? lUVElement->GetIndexArray().GetCount() : 0;

	const int lPolyCount = pMesh->GetPolygonCount();

	if (lUVElement->GetMappingMode() == FbxGeometryElement::eByControlPoint)
	{
		for (int lPolyIndex = 0; lPolyIndex < lPolyCount; ++lPolyIndex)
		{
			// build the max index array that we need to pass into MakePoly
			const int lPolySize = pMesh->GetPolygonSize(lPolyIndex);
			for (int lVertIndex = 0; lVertIndex < lPolySize; ++lVertIndex)
			{
				FbxVector2 lUVValue;

				//get the index of the current vertex in control points array
				int lPolyVertIndex = pMesh->GetPolygonVertex(lPolyIndex, lVertIndex);

				//the UV index depends on the reference mode
				int lUVIndex = lUseIndex ? lUVElement->GetIndexArray().GetAt(lPolyVertIndex) : lPolyVertIndex;

				lUVValue = lUVElement->GetDirectArray().GetAt(lUVIndex);

				//User TODO:
				//Print out the value of UV(lUVValue) or log it to a file
			}
		}
	}
	else if (lUVElement->GetMappingMode() == FbxGeometryElement::eByPolygonVertex)
	{
		int lPolyIndexCounter = 0;
		for (int lPolyIndex = 0; lPolyIndex < lPolyCount; ++lPolyIndex)
		{
			// build the max index array that we need to pass into MakePoly
			const int lPolySize = pMesh->GetPolygonSize(lPolyIndex);
			for (int lPolyIndex = 0; lPolyIndex < lPolyCount; ++lPolyIndex)
			{
				// build the max index array that we need to pass into MakePoly
				const int lPolySize = pMesh->GetPolygonSize(lPolyIndex);
				for (int lVertIndex = 0; lVertIndex < lPolySize; ++lVertIndex)
				{
					if (lPolyIndexCounter < lIndexCount)
					{
						FbxVector2 lUVValue;

						//the UV index depends on the reference mode
						int lUVIndex = lUseIndex ? lUVElement->GetIndexArray().GetAt(lPolyIndexCounter) : lPolyIndexCounter;

						lUVValue = lUVElement->GetDirectArray().GetAt(lUVIndex);

						//User TODO:
						//Print out the value of UV(lUVValue) or log it to a file

						lPolyIndexCounter++;
					}
				}
			}
		}
	}
	std::cout << lUVSetName << std::endl;
}
void check_node(FbxScene* lScene)
{
	FbxNode* rNode = lScene->GetRootNode();

	// 通过rNode->GetChildCount()检索material,会出现重复的materal
	int childCount = rNode->GetChildCount();
	std::cout << "nodeCount: " << childCount << std::endl;

	int texLayerCount = ::FbxLayerElement::sTypeTextureCount;
	auto texLayerNames = ::FbxLayerElement::sTextureChannelNames;
	unsigned int unWidth = 0, unHeight = 0;

	for (int i = 0; i < childCount; i++) {
		FbxNode* iNode = rNode->GetChild(i);
		FbxNodeAttribute* iAttri = iNode->GetNodeAttribute();
		std::cout << "----------" << iAttri->GetTypeName() << ":" << iNode->GetName() << std::endl;

		if (iAttri->GetAttributeType() == FbxNodeAttribute::EType::eMesh)
		{
			int materialCount = iNode->GetMaterialCount();
			for (int m = 0; m < materialCount; m++)
			{
				FbxSurfaceMaterial* material = iNode->GetMaterial(m);
				std::cout << "  " << m << " : " << material->GetName() << std::endl;

				for (size_t t = 0; t < texLayerCount; t++)
				{

					FbxProperty pProperty = material->FindProperty(texLayerNames[t]);
					if (pProperty.IsValid()) {
						int textureCount = pProperty.GetSrcObjectCount();
						for (int j = 0; j < textureCount; ++j)
						{
							FbxFileTexture* pTexture = FbxCast<FbxFileTexture>(pProperty.GetSrcObject(j));
							std::string name = pTexture->GetFileName();
							std::cout << "  /-->" << texLayerNames[t] << ":" << name << std::endl;
							GetPicWidthHeight(name.c_str(), &unWidth, &unHeight);
							std::cout << "     w:" << unWidth << " h:" << unHeight << std::endl;

							check_uv(iNode->GetMesh());
						}
					}
					std::cout << std::endl;
				}
			}
		}
	}
}













// lScene->GetMaterialCount() -> texture
void check_materials(FbxScene* lScene)
{
	std::cout << "materCount: " << lScene->GetMaterialCount() << std::endl;
	for (size_t i = 0; i < lScene->GetMaterialCount(); i++)
	{
		::FbxSurfaceMaterial* material = lScene->GetMaterial(i);
		std::cout << i << " : " << material->GetName() << std::endl;
		int objCount = material->GetSrcObjectCount();
		std::cout << "SrcPropertyCount : " << objCount << std::endl;
		int tCount = ::FbxLayerElement::sTypeTextureCount;
		auto names = ::FbxLayerElement::sTextureChannelNames;
		std::cout << "TextureLayerCount  --> " << tCount << std::endl;
		tCount = 0;
		for (size_t m = 0; m < tCount; m++)
		{
			std::cout << "  /-->" << names[m] << ":";
			fbxsdk::FbxProperty pProperty = material->FindProperty(names[m]);
			if (pProperty.IsValid()) {
				int textureCount = pProperty.GetSrcObjectCount();
				for (int j = 0; j < textureCount; ++j)
				{
					FbxFileTexture* pTexture = FbxCast<FbxFileTexture>(pProperty.GetSrcObject(j));
					std::string name = pTexture->GetFileName();
					std::cout << name;
				}
			}
			std::cout << std::endl;
		}
	}
}
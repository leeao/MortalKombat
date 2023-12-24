# Mortal Kombat RenderWare PS2 / PSP DFF Models Noesis Importer
# By Allen(Leeao)
'''
Support games:
    Mortal Kombat Deadly Alliance [PS2]
    Mortal Kombat Deception [PS2]
    Mortal Kombat Armageddon [PS2]
    Mortal Kombat Unchained [PSP]
Support format:
    DFF Model
    MKA Animation
'''

LoadMKAnimation = True      # Load MKA Animation

from inc_noesis import *
import struct
import os


def registerNoesisTypes():
    handle = noesis.register("Mortal Kombat PS2 PSP DFF Models", ".dff")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadModel(handle, dffLoadModel)
    return 1

isMKPS2 = 0
isMKPSP = 0    

def noepyCheckType(data):
    bs = NoeBitStream(data)
    bs.seek(8)
    idstring = bs.readUInt()
    if idstring != 0x10 :
        return 0
    else:
        global isMKPS2
        global isMKPSP
        fileSize = bs.tell() + bs.readUInt() + 8
        version = bs.readUInt()
        if version == 0x1C020064:
            isMKPSP = 1
            isMKPS2 = 0
        else:
            isMKPS2 = 1
            isMKPSP = 0 
    return 1

def dffLoadModel(data, mdlList):
    global isMKPS2
    global isMKPSP
    bs = NoeBitStream(data)
    ctx = rapi.rpgCreateContext()
    fileSize = len(data)
    bs.seek(8)
    checkMK = bs.readUInt()
    if checkMK == 0x10:
        fileSize = bs.tell() + bs.readUInt() + 8
        version = bs.readUInt()
        if version == 0x1C020064:
            isMKPSP = 1
            isMKPS2 = 0
        else:
            isMKPS2 = 1
            isMKPSP = 0
        bs.seek(8)
    while bs.tell() < fileSize:
        chunk = rwChunk(bs)
        if chunk.chunkID == 0x10:
            #datas = bs.readBytes(chunk.chunkSize)
            #clump = rClump(datas)
            clump = rClump(bs)
            clump.readClump()
            if len(clump.mdlList) > 0:
                mdlList.append(clump.mdlList[0])
        else:
            bs.seek(chunk.chunkSize,1)
    return 1
class rwChunk(object):   
    def __init__(self,bs):
        self.chunkID,self.chunkSize,self.chunkVersion = struct.unpack("3I", bs.readBytes(12))
        self.version = libraryIDUnpackVersion(self.chunkVersion)
def libraryIDUnpackVersion( libid):

    if libid & 0xFFFF0000:
        return (libid>>14 & 0x3FF00) + 0x30000 |(libid>>16 & 0x3F)
    return libid<<8

def readRWString(bs):
    rwStrChunk = rwChunk(bs)
    endOfs = bs.tell() + rwStrChunk.chunkSize
    string = bs.readString()
    bs.seek(endOfs)
    return string

def get_ext_file(dir_path,extension):
    file_list = []
    for root, dirs, files in os.walk(dir_path):
        for file in files:
            if file.endswith(extension): # ext "mka"
                file_list.append(os.path.join(root, file))
    return file_list

# Create kf Bone
def createKfBone(boneIndex, posKfs, rotKfs):
    kfBone = NoeKeyFramedBone(boneIndex)
    if rotKfs:
        kfBone.setRotation(rotKfs, noesis.NOEKF_ROTATION_QUATERNION_4,noesis.NOEKF_INTERPOLATE_LINEAR)
    if posKfs:
        kfBone.setTranslation(posKfs, noesis.NOEKF_TRANSLATION_VECTOR_3,noesis.NOEKF_INTERPOLATE_LINEAR)
    return kfBone

def getAnimBoneMap(hAnimBoneIDList,hSkinBoneIDList):
    boneMap = []
    for i in range(26):
        animBoneID = 4096 + i
        for j in range(len(hAnimBoneIDList)):
            if hAnimBoneIDList[j] & 0xFFFF == animBoneID:
                boneMap.append(hSkinBoneIDList[j])
                break
    return boneMap

def LoadAnims(data, animName, bones,hAnimBoneIDList,hSkinBoneIDList):
    boneMap = getAnimBoneMap(hAnimBoneIDList,hSkinBoneIDList)
    #print(boneMap)
    bs = NoeBitStream(data)
    magic = bs.readBytes(3)
    version = bs.readByte()
    if magic == b'MKA':
        animNameBytes = bs.readBytes(20)
        frames = bs.readInt()
        numBones = bs.readInt()
        if version != 0x31:
            unk = bs.readInt()
            bs.seek(12,NOESEEK_REL)

        transOffset = NoeVec3([bs.readInt()/32768.0,bs.readInt()/32768.0,bs.readInt()/32768.0])

        kfBones = []
        frameRate = 60
        keyFrameHeaderList = []
        for i in range(numBones+1):
            headerInfo = []
            keyFrameType = bs.readInt()
            boneIndex = bs.readInt()
            offset = bs.readInt()
            headerInfo.append(keyFrameType)
            headerInfo.append(boneIndex&0xFFF)
            headerInfo.append(offset)
            headerInfo.append(boneIndex)
            keyFrameHeaderList.append(headerInfo)
        for i in range(numBones):

            keyFrameType = keyFrameHeaderList[i][0]
            boneIndex = keyFrameHeaderList[i][1]
            offset = keyFrameHeaderList[i][2]
            size = keyFrameHeaderList[i+1][2] - keyFrameHeaderList[i][2]
            numFrames = 0
            if keyFrameType == 1 or keyFrameType == 4:
                numFrames = size // 8
            bs.seek(offset)

            posKfs, rotKfs = [], []
            curRotKeyFrameList = []
            for j in range(numFrames):
                if keyFrameType == 1:
                    frameID = bs.readShort()
                    tx = bs.readShort() / 1024.0 + transOffset[0]
                    ty = bs.readShort() / 1024.0 + transOffset[1]
                    tz = bs.readShort() / 1024.0 + transOffset[2]
                    #keyFrame = rwKeyFrame()
                    #keyFrame.time = frameID / frameRate
                    #keyFrame.trans = NoeVec3([tx,ty,tz])
                    #curKeyFrameList.append(keyFrame)
                    posKfs.append(NoeKeyFramedValue(frameID / frameRate, NoeVec3([tx,ty,tz])))
                elif keyFrameType == 4:
                    frameID = bs.readShort()
                    RotCompressed1 = bs.readShort()
                    byte1 = bs.readByte()
                    bs.seek(-1,NOESEEK_REL)
                    RotCompressed2 = bs.readInt()
                    qx =((RotCompressed1 & 0xFFF ^ 0x800) - 2048) * 0.00048828125
                    qy = ((byte1 * 16) + ((RotCompressed1 & 0xf000) >> 12)) * 0.00048828125 #* -1.0
                    qz = (0.00048828125 * ((((RotCompressed2 & 0xFFF00) >> 8) ^ 0x800) - 2048)) #* -1.0
                    qw = 0.00048828125 * ((RotCompressed2 & 0xFFF00000) >> 20)
                    #conjugate -qx -qy -qz qw
                    quat = NoeQuat([-qx,-qy,-qz,qw]) 
                    #quat = NoeQuat([qx,qy,qz,qw])
                    #quat = quat.transpose()
                    #quat = NoeQuat([qx,qy,qz,qw]).transpose()
                    #print(qx,qy,qz,qw)

                    keyFrame = rwKeyFrame()
                    keyFrame.time = frameID / frameRate
                    keyFrame.quat = NoeQuat([qx,qy,qz,qw])   
                    curRotKeyFrameList.append(keyFrame)              
                    rotKfs.append(NoeKeyFramedValue(frameID / frameRate, quat))

            if boneIndex < 0xffff and boneIndex < len(boneMap):
                kfBones.append(createKfBone(boneMap[boneIndex], posKfs, rotKfs))

        return NoeKeyFramedAnim(animName, bones, kfBones, frameRate)

class rwKeyFrame(object):
    def __init__(self):
        self.prevFrame = 0
        self.prevFrameHdrOfs = 0
        self.prevFrameID = 0
        self.time = 0.0
        self.currentFrameHdrOfs = 0
        self.currentID = 0
        self.nodeID = 0
        self.nextFrameID = -1
        self.quat = NoeQuat()
        self.trans = NoeVec3()

class rClump(object):
    #def __init__(self,datas):
    def __init__(self,bs):
        #self.bs = NoeBitStream(datas)
        self.bs = bs
        self.mdlList = []
    def readClump(self):
        rapi.rpgReset()
        clumpStructHeader = rClumpStruct(self.bs)            
        frameListHeader = rwChunk(self.bs)

        datas = self.bs.readBytes(frameListHeader.chunkSize)
        frameList = rFrameList(datas)
        #frameList = rFrameList(self.bs)

        bones = frameList.readBoneList()

        #if clumpStructHeader.version > 0x33000:
        #skinBones = bones
        #skinBones = frameList.getMKSkinBones()
        skinBones = frameList.getSkinBones()

        geometryListHeader = rwChunk(self.bs)
        geometryListStructHeader = rwChunk(self.bs)
        geometryCount = self.bs.readUInt()
        geoListOfs = self.bs.tell()
        if geometryCount:
            #datas = self.bs.readBytes(geometryListHeader.chunkSize-16)
            self.bs.seek(geometryListHeader.chunkSize-16,NOESEEK_REL)
        vertMatList=[0]*clumpStructHeader.numAtomics
        if clumpStructHeader.numAtomics:
            atomicData = bytes()
            for i in range(clumpStructHeader.numAtomics):
                atomicHeader = rwChunk(self.bs)
                atomicData += self.bs.readBytes(atomicHeader.chunkSize)
            atomicList = rAtomicList(atomicData,clumpStructHeader.numAtomics).rAtomicStuct()
            for j in range(clumpStructHeader.numAtomics):
                vertMatList[atomicList[j].geometryIndex]= \
                    bones[atomicList[j].frameIndex].getMatrix()
        endOfs = self.bs.tell()
        self.bs.seek(geoListOfs)

        if geometryCount:

            geometryList = rGeometryList(self.bs,geometryCount,vertMatList,\
                frameList.hAnimBoneMap)      # Does not contain duplicate bones
            # geometryList = rGeometryList(self.bs,geometryCount,\
            # vertMatList,frameList.hSkinBoneIDList)  # Contains duplicate bones
            geometryList.readGeometry()
            mdl = rapi.rpgConstructModel()
            #try:
            #    mdl = rapi.rpgConstructModel()
            #except :
            #    mdl = NoeModel()

            texList = []
            texNameList = []
            existTexNameList = []
            path = rapi.getDirForFilePath(rapi.getInputName())
            for m in range(len(geometryList.matList)):
                texName = geometryList.matList[m].name
                if texName not in texNameList:
                    texNameList.append(texName)                        
                    fullTexName = path+texName+".png"
                    if rapi.checkFileExists(fullTexName):
                        texture = noesis.loadImageRGBA(fullTexName)
                        texList.append(texture)
                        existTexNameList.append(texName)

            matList = []
            for i in range(len(texList)):
                matName = existTexNameList[i]
                material = NoeMaterial(matName, texList[i].name)
                #material.setDefaultBlend(0)
                matList.append(material)
            mdl.setModelMaterials(NoeModelMaterials(texList,matList))
            mdl.setBones(skinBones)

            anims = []
            if LoadMKAnimation:
                path = os.path.dirname(rapi.getInputName())
                mkaFiles = get_ext_file(path,"mka")
                for mkaFile in mkaFiles:
                    mkaName = os.path.basename(mkaFile)[:-4] # Filename without extension
                    animData = rapi.loadIntoByteArray(mkaFile)
                    if animData:                        
                        anims.append(LoadAnims(animData, mkaName, \
                        skinBones,frameList.hAnimBoneIDList,frameList.hSkinBoneIDList))
                if anims:
                    mdl.setAnims(anims)
            self.mdlList.append(mdl)
            #rapi.rpgReset()
        else:
            mdl = NoeModel()
            mdl.setBones(bones)
            self.mdlList.append(mdl)
        self.bs.seek(endOfs)

class rClumpStruct(object):
    def __init__(self,bs):
        self.chunkID,self.chunkSize,self.chunkVersion = struct.unpack("3I", bs.readBytes(12))
        self.numAtomics = bs.readUInt()
        self.version = libraryIDUnpackVersion(self.chunkVersion)
        if self.version >= 0x33000:
            self.numLights = bs.readUInt()
            self.numCameras = bs.readUInt()

GlobalBoneNames = {
    '4096': "Bip01",
    '4097': "Bip01_L_Thigh",
    '4100': "Bip01_L_Calf",
    '4103': "Bip01_L_Foot",
    '4106': "Bip01_L_Toe0",
    '4098': "Bip01_R_Thigh",
    '4101': "Bip01_R_Calf",
    '4104': "Bip01_R_Foot",
    '4107': "Bip01_R_Toe0",
    '4099': "Bip01_Spine",
    '4102': "Bip01_Spine1",
    '4105': "Bip01_Spine2",
    '4110': "Bip01_R_Clavicle",
    '4113': "Bip01_R_UpperArm",
    '4115': "Bip01_R_UpperArm2",
    '4117': "Bip01_R_Forearm",
    '4119': "Bip01_R_Forearm2",
    '4121': "Bip01_R_Hand",
    '4123': "Bip01_R_Finger0",
    '4133': "Bip01_R_Finger01",

    '4127': "Bip01_R_Finger2",
    '4137': "Bip01_R_Finger21",
    '4129': "Bip01_R_Finger3",
    '4139': "Bip01_R_Finger31",

    '4131': "Bip01_R_Finger1",
    '4141': "Bip01_R_Finger11",
    '4151': "Bip01_R_Finger111",
    '4109': "Bip01_Neck",
    '4112': "Bip01_Head",
    '4108': "Bip01_L_Clavicle",
    '4111': "Bip01_L_UpperArm",
    '4114': "Bip01_L_UpperArm2",
    '4116': "Bip01_L_Forearm",
    '4118': "Bip01_L_Forearm2",
    '4120': "Bip01_L_Hand",
    '4122': "Bip01_L_Finger0",
    '4132': "Bip01_L_Finger01",

    '4126': "Bip01_L_Finger2",
    '4136': "Bip01_L_Finger21",
    '4128': "Bip01_L_Finger3",
    '4138': "Bip01_L_Finger31",

    '4130': "Bip01_L_Finger1",
    '4140': "Bip01_L_Finger11",
    '4150': "Bip01_L_Finger111",

    '36864': "Bip01_copy",
    '36865': "Bip01_L_Thigh_copy",
    '36866': "Bip01_R_Thigh_copy",
    '36869': "Bip01_R_Calf_copy",
    '36872': "Bip01_R_Foot_copy",
    '36875': "Bip01_R_Toe0_copy",
    '36868': "Bip01_L_Calf_copy",
    '36871': "Bip01_L_Foot_copy",
    '36874': "Bip01_L_Toe0_copy",
    '36867': "Bip01_Spine_copy",
    '36870': "Bip01_Spine1_copy",
    '36873': "Bip01_Spine2_copy",
    '36878': "Bip01_R_Clavicle_copy",
    '36877': "Bip01_Neck_copy",
    '36880': "Bip01_Head_copy",
    '36876': "Bip01_L_Clavicle_copy",
    '36881': "Bip01_R_UpperArm_copy",
    '36883': "Bip01_R_UpperArm2_copy",
    '36885': "Bip01_R_Forearm_copy",
    '36887': "Bip01_R_Forearm2_copy",
    '36889': "Bip01_R_Hand_copy",
    '36891': "Bip01_R_Finger0_copy",
    '36899': "Bip01_R_Finger1_copy",
    '36879': "Bip01_L_UpperArm_copy",
    '36882': "Bip01_L_UpperArm2_copy",
    '36884': "Bip01_L_Forearm_copy",
    '36886': "Bip01_L_Forearm2_copy",
    '36888': "Bip01_L_Hand_copy",
    '36890': "Bip01_L_Finger0_copy",
    '36898': "Bip01_L_Finger1_copy",
}

class rFrameList(object):
    def __init__(self,datas):
        self.bs = NoeBitStream(datas)
        #self.bs = bs          
        self.frameCount = 0
        self.boneMatList=[]
        self.bonePrtIdList=[]
        self.boneIndexList=[]
        self.animBoneIDList=[]
        self.boneNameList=[]                
        self.hAnimBoneIDList =[]
        self.hSkinBoneIDList=[]     #boneMap1 包含重复骨头，没有实体的骨头
        self.hAnimBoneMap=[]        #boneMap2 不包含没有实体的骨头
        self.bones = []
        self.skinBones=[]
        self.hasHAnim = 0
        self.hasBoneName = 0
        self.boneInfoList = []
    def rFrameListStruct(self):
        header = rwChunk(self.bs)
        frameCount = self.bs.readUInt()
        self.frameCount = frameCount
        if frameCount:
            for i in range(frameCount):
                boneMat = NoeMat43.fromBytes(self.bs.readBytes(48)).transpose()
                bonePrtId = self.bs.readInt()
                self.bs.readInt()
                self.boneMatList.append(boneMat)
                self.bonePrtIdList.append(bonePrtId)
                self.boneIndexList.append(i)

                skinBne = skinBone()
                skinBne.boneName = "bone"
                skinBne.listID = i
                skinBne.listParentID = bonePrtId
                skinBne.matrix = boneMat
                skinBne.animBoneID = -1
                skinBne.skinBoneID = -1
                skinBne.skinBoneParentID = -1
                self.boneInfoList.append(skinBne)

    def rHAnimPLG(self,index):
        hAnimVersion = self.bs.readInt()
        animBoneID = self.bs.readInt()
        self.animBoneIDList.append(animBoneID)
        self.boneInfoList[index].animBoneID = animBoneID
        boneCount = self.bs.readUInt()
        if boneCount:
            self.hasHAnim = 1
            flags = self.bs.readInt()
            keyFrameSize = self.bs.readInt()
            for i in range(boneCount):
                if not isMKPS2:
                    self.hAnimBoneIDList.append(self.bs.readInt())
                else:
                    #value = self.bs.readShort()
                    #value2 = self.bs.readShort()
                    #self.hAnimBoneIDList.append(value & 0x7fff)
                    self.hAnimBoneIDList.append(self.bs.readUInt())
                self.hSkinBoneIDList.append(self.bs.readInt())
                boneType = self.bs.readInt()
    def rUserDataPLG(self,index):
        numSet = self.bs.readInt()
        boneName = "Bone"+str(index)
        for i in range(numSet):
            typeNameLen = self.bs.readInt()
            self.bs.seek(typeNameLen,1)
            userDataType = self.bs.readInt()
            numberObjects = self.bs.readInt()
            boneNameLen = self.bs.readInt()
            if boneNameLen>1:
                boneName = self.bs.readString()
                if self.hasBoneName != 1:
                    self.hasBoneName = 1
        self.boneNameList.append(boneName)
        self.boneInfoList[index].boneName = boneName
    def rFrameName(self,nameLength):
        boneName = ""
        boneNameBytes = self.bs.readBytes(nameLength)
        boneName = str(boneNameBytes, encoding = "utf-8")
        return boneName
    def rFrameExt(self,index):
        header = rwChunk(self.bs)
        endOfs = self.bs.tell() + header.chunkSize
        hasName = 0
        if header.chunkSize:
            while self.bs.tell() < endOfs:
                chunk = rwChunk(self.bs)                                
                if chunk.chunkID == 0x11e:
                    self.rHAnimPLG(index)
                elif chunk.chunkID == 0x253F2FE:  
                    hasName = 1
                    self.boneNameList.append(self.rFrameName(chunk.chunkSize))
                    self.boneInfoList[index].boneName = self.boneNameList[index]
                    if self.hasBoneName != 1:
                        self.hasBoneName = 1
                elif chunk.chunkID == 0x11f:
                    hasName = 1
                    self.rUserDataPLG(index)
                else:
                    self.bs.seek(chunk.chunkSize,1)
        if hasName == 0:
            if index==0:
                self.boneNameList.append("RootBone")
            else:
                self.boneNameList.append("Bone"+str(index))
            self.boneInfoList[index].boneName = self.boneNameList[index]                                
    def rFrameExtList(self):
        for i in range(self.frameCount):
            self.rFrameExt(i)

    def readBoneList(self):
        self.rFrameListStruct()
        self.rFrameExtList()
        #Just list order
        bones=[]
        for i in range(self.frameCount):
            boneIndex = i
            boneName = self.boneNameList[i]
            boneMat = self.boneMatList[i]
            bonePIndex = self.bonePrtIdList[i]
            bone = NoeBone(boneIndex, boneName, boneMat, None, bonePIndex)
            bones.append(bone)

        for i in range(self.frameCount):
            bonePIndex = self.bonePrtIdList[i]
            if bonePIndex > -1:
                prtMat=bones[bonePIndex].getMatrix()
                boneMat = bones[i].getMatrix()                             
                bones[i].setMatrix(boneMat * prtMat)
        self.bones = bones
        return bones
    def getMKSkinBones(self):
        if self.hasHAnim > 0:
            # 针对披风等小组件的骨骼
            # 因为骨骼蒙皮使用的骨骼ID不是连续中间有缺少的ID
            # 所以针对蒙皮骨骼ID列表重新排序，修复链接
            tempHSkinBoneIdList = copy.deepcopy(self.hSkinBoneIDList)
            tempHSkinBoneIdList.sort()
            newSkinBoneIdList = copy.deepcopy(self.hSkinBoneIDList)
            for i in range(len(self.hSkinBoneIDList)):
                tempSkinBoneId = tempHSkinBoneIdList[i]
                for j in range(len(self.hSkinBoneIDList)):
                    skinBoneId = self.hSkinBoneIDList[j]
                    if tempSkinBoneId == skinBoneId:
                        newSkinBoneIdList[j] = i
                        break                                
            self.hSkinBoneIDList = copy.deepcopy(newSkinBoneIdList)

            index1 = 0
            skinBoneInfoList = [skinBone()] * len(self.hSkinBoneIDList)

            # just find source bone list skin bone index
            for i in range(len(self.boneInfoList)):
                animBoneID = self.boneInfoList[i].animBoneID    
                for j in range(len(self.hSkinBoneIDList)):
                    hAnimBoneID = self.hAnimBoneIDList[j] & 0xffff
                    SkinBoneID = self.hSkinBoneIDList[j]
                    if hAnimBoneID == animBoneID:
                        self.boneInfoList[i].skinBoneID = SkinBoneID
                        break

            index1 = 0
            for SkinBoneID in self.hSkinBoneIDList:
                hAnimBoneID = self.hAnimBoneIDList[index1] & 0x7fff
                for j in range(len(self.boneInfoList)):
                    animBoneID = self.boneInfoList[j].animBoneID
                    if hAnimBoneID == animBoneID:
                        newSknBone = skinBone()
                        newSknBone.skinBoneID = SkinBoneID                                
                        sknBne = self.boneInfoList[j]
                        if self.hasBoneName == 1:
                            newSknBone.boneName = self.boneNameList[sknBne.listID]
                        else:
                            #newSknBone.boneName = "Bone" + str(SkinBoneID)
                            bname = ""
                            if GlobalBoneNames.get(str(self.hAnimBoneIDList[index1]& 0xffff)  ):
                                bname = "_" + \
                                GlobalBoneNames[str(self.hAnimBoneIDList[index1] & 0xffff) ]
                            #if (self.hAnimBoneIDList[index1] & 0xffff) != hAnimBoneID:
                            #    if GlobalBoneNames.get(str(hAnimBoneID)  ):
                            #        print("'%d':\"%s_copy\"," %\
                            #     ((self.hAnimBoneIDList[index1] & 0xffff),\
                            #    (GlobalBoneNames[str(hAnimBoneID)]))  )
                            newSknBone.boneName = "Bone" \
                                + str(SkinBoneID)+"_"+ str(index1) +"_"+\
                                str(hAnimBoneID)+ "_" +\
                                str(self.hAnimBoneIDList[index1]&0xffff)+\
                                "_" + str(self.hAnimBoneIDList[index1] >> 16)+ bname
                        newSknBone.listParentID = sknBne.listParentID
                        newSknBone.matrix = sknBne.matrix
                        newSknBone.animBoneID = hAnimBoneID
                        newSknBone.listID = sknBne.listID
                        skinBoneInfoList[SkinBoneID] = newSknBone
                        self.hAnimBoneMap.append(self.boneInfoList[j].skinBoneID)
                        break
                index1 += 1

            # find parent bone index   
            for i in range(len(skinBoneInfoList)):
                sknBne = skinBoneInfoList[i]
                if sknBne.listParentID != -1:
                    skinBoneInfoList[i].skinBoneParentID =\
                        self.boneInfoList[sknBne.listParentID].skinBoneID

            #build skeleton
            skinBones = []
            for j in range(len(skinBoneInfoList)):   
                sknBne = skinBoneInfoList[j]    
                boneIndex = skinBoneInfoList[j].skinBoneID
                boneName =  skinBoneInfoList[j].boneName
                boneMat = self.bones[sknBne.listID].getMatrix()
                bonePIndex = skinBoneInfoList[j].skinBoneParentID
                bone = NoeBone(boneIndex, boneName, boneMat, None,bonePIndex)
                skinBones.append(bone) 
                #print(boneIndex, boneName, bonePIndex)

            self.skinBones = skinBones
            #print("new bone count2:",len(skinBones))
        else:
            self.skinBones = self.bones
        return self.skinBones
    def getSkinBones(self):
        #编程思路
        #通过比较每个骨骼的AnimBoneID 和 hAnimBoneIDList 里面的 AnimBoneID 是否相同. AnimBoneID需要大于>0.
        #然后得到一个存在的AnimBoneID数组，SkinBoneID数组（未从0排序），frameListID数组（数组存储顺序ID，方便访问父级和名称，矩阵），父级骨骼ListID数组
        #通过遍历父级骨骼ListID数组，查看是否和frameListID数组相同，然后得到父级的SkinBoneID。链接父级。
        #根据skinBoneID从0开始重新排序. 本步骤不是必做，因为Noesis自动矫正列表,不过还是做了。
        #Programming ideas
        #By comparing the AnimBoneID of each bone and the AnimBoneID in hAnimBoneIDList are the same. AnimBoneID needs to be greater than >0.
        #Then get an existing AnimBoneID array, SkinBoneID array (not sorted from 0), frameListID array (array storage order ID, easy to access parent and name, matrix), parent bone ListID array
        #By traversing the parent bone ListID array, check whether it is the same as the frameListID array, and then get the parent's SkinBoneID. Link to the parent.
        #Re-sort from 0 according to skinBoneID. This step is not necessary, because Noesis automatically corrects the list, but it is still done.                
        if self.hasHAnim > 0: 
            #print(self.hSkinBoneIDList)
            #print(self.hAnimBoneIDList)
            # 针对披风等小组件的骨骼
            # 因为骨骼蒙皮使用的骨骼ID不是连续中间有缺少的ID
            # 所以针对蒙皮骨骼ID列表重新排序，修复链接
            tempHSkinBoneIdList = copy.deepcopy(self.hSkinBoneIDList)
            tempHSkinBoneIdList.sort()
            newSkinBoneIdList = copy.deepcopy(self.hSkinBoneIDList)
            for i in range(len(self.hSkinBoneIDList)):
                tempSkinBoneId = tempHSkinBoneIdList[i]
                for j in range(len(self.hSkinBoneIDList)):
                    skinBoneId = self.hSkinBoneIDList[j]
                    if tempSkinBoneId == skinBoneId:
                        newSkinBoneIdList[j] = i
                        break
            self.hSkinBoneIDList = copy.deepcopy(newSkinBoneIdList)
            #print(newSkinBoneIdList)
            #print(tempHSkinBoneIdList)

            # just find source bone list skin bone index
            for i in range(len(self.boneInfoList)):
                animBoneID = self.boneInfoList[i].animBoneID
                for j in range(len(self.hSkinBoneIDList)):
                    hAnimBoneID = self.hAnimBoneIDList[j] & 0xffff
                    SkinBoneID = self.hSkinBoneIDList[j]
                    if hAnimBoneID == animBoneID:
                        self.boneInfoList[i].skinBoneID = SkinBoneID
                        break
            #boneMap
            index1 = 0
            for SkinBoneID in self.hSkinBoneIDList:
                hAnimBoneID = self.hAnimBoneIDList[index1] & 0x7fff
                for j in range(len(self.boneInfoList)):
                    animBoneID = self.boneInfoList[j].animBoneID
                    if hAnimBoneID == animBoneID:
                        self.hAnimBoneMap.append(self.boneInfoList[j].skinBoneID)
                        break
                index1 += 1

            boneDataList = []
            for i in range(len(self.animBoneIDList)):
                index = i
                if len(self.animBoneIDList) == (self.frameCount - 1):
                    index = i + 1
                elif len(self.animBoneIDList) == self.frameCount:
                    index = i
                curBoneAnimBoneID = self.animBoneIDList[i]
                if curBoneAnimBoneID > -1:
                    for j in range(len(self.hAnimBoneIDList)):
                        if curBoneAnimBoneID == self.hAnimBoneIDList[j] & 0xffff:
                            boneData = skinBone()
                            if self.hasBoneName == 1:
                                boneData.boneName = self.boneNameList[index]
                            else:                           
                                #boneData.boneName = "Bone" + str(curBoneAnimBoneID)
                                if GlobalBoneNames.get(str(curBoneAnimBoneID)  ):
                                    boneData.boneName = "Bone" +\
                                        str(curBoneAnimBoneID)+ "_" + \
                                        GlobalBoneNames[str(curBoneAnimBoneID) ]
                                else:
                                    boneData.boneName = "Bone" + str(curBoneAnimBoneID)
                            boneData.matrix = self.bones[index].getMatrix()
                            boneData.skinBoneID = self.hSkinBoneIDList[j]
                            boneData.animBoneID = curBoneAnimBoneID
                            boneData.listID = index
                            boneData.listParentID = self.bonePrtIdList[index]
                            boneDataList.append(boneData)
            #find parent skin bone id
            for i in range(len(boneDataList)):
                for j in range(len(boneDataList)):
                    if boneDataList[i].listParentID == boneDataList[j].listID:
                        boneDataList[i].skinBoneParentID = boneDataList[j].skinBoneID
                    if len(self.animBoneIDList) == (self.frameCount - 1):
                        if boneDataList[i].listParentID == 0 :
                            boneDataList[i].skinBoneParentID = -1

            #build skeleton
            tempBones = []
            for j in range(len(boneDataList)):                
                boneIndex = boneDataList[j].skinBoneID
                boneName =  boneDataList[j].boneName
                boneMat = boneDataList[j].matrix
                bonePIndex = boneDataList[j].skinBoneParentID
                bone = NoeBone(boneIndex, boneName, boneMat, None,bonePIndex)
                tempBones.append(bone)

            #Re-sort from 0 according to skinBoneID.
            bones = []
            for i in range(len(boneDataList)): 
                for j in range(len(boneDataList)):
                    if tempBones[j].index == i:
                        bones.append(tempBones[j])
            self.skinBones = bones
        else:
            bones = self.bones
        return bones
class skinBone(object):
    def __init__(self):
        #self.bone = 0
        self.boneName = 0
        self.matrix = 0
        self.skinBoneID = 0
        self.animBoneID = 0
        self.skinBoneParentID = -1
        self.listID = 0
        self.listParentID = -1

class Atomic(object):
    def __init__(self):
        self.frameIndex = 0
        self.geometryIndex = 0
class rAtomicList(object):
    def __init__(self,datas,numAtomics):
        self.bs = NoeBitStream(datas)
        self.numAtomics = numAtomics
    def rAtomicStuct(self):
        atomicList=[]
        for i in range(self.numAtomics):
            header = rwChunk(self.bs)
            atomic = Atomic()
            atomic.frameIndex = self.bs.readUInt()
            atomic.geometryIndex = self.bs.readUInt()
            flags = self.bs.readUInt()
            unused = self.bs.readUInt()
            extHeader = rwChunk(self.bs)
            self.bs.seek(extHeader.chunkSize,1)
            atomicList.append(atomic)
        return atomicList

class rMatrial(object):
    def __init__(self,datas):
        self.bs = NoeBitStream(datas)
        #self.bs =  bs
        self.MKMaterialSkinBonePalette = []
        self.diffuseColor = NoeVec4([1.0, 1.0, 1.0, 1.0])
        self.useBonePalette = True
        self.meshTypeFlag = None
        self.unk2 = None
    def rMaterialStruct(self):
        header = rwChunk(self.bs)
        unused = self.bs.readInt()
        colorR = self.bs.readUByte()
        colorG = self.bs.readUByte() 
        colorB = self.bs.readUByte()
        colorA = self.bs.readUByte()
        self.diffuseColor = NoeVec4([colorR, colorG, colorB, colorA])
        unused2 = self.bs.readInt()
        hasTexture = self.bs.readInt()
        ambient = self.bs.readFloat()
        specular = self.bs.readFloat()
        diffuse = self.bs.readFloat()
        texName = ""
        if hasTexture:
            texHeader = rwChunk(self.bs)
            texStructHeader = rwChunk(self.bs)
            textureFilter = self.bs.readByte()
            UVAddressing = self.bs.readByte()
            useMipLevelFlag = self.bs.readShort()
            texName = noeStrFromBytes(self.bs.readBytes(rwChunk(self.bs).chunkSize))
            #alphaTexName = noeStrFromBytes(self.bs.readBytes(rwChunk(self.bs).chunkSize))
            self.bs.seek(rwChunk(self.bs).chunkSize,1)
            texExtHeader = rwChunk(self.bs)
            self.bs.seek(texExtHeader.chunkSize,1)
        matExtHeader = rwChunk(self.bs)
        #self.bs.seek(matExtHeader.chunkSize,1)
        matExtEndOfs = self.bs.tell() + matExtHeader.chunkSize
        if matExtHeader.chunkSize > 0:
            while self.bs.tell() < matExtEndOfs:
                chunk = rwChunk(self.bs)
                if chunk.chunkID == 0x895303:
                    self.ReadMKMaterial()
                else:
                    self.bs.seek(chunk.chunkSize,NOESEEK_REL)
        return texName
    def ReadMKMaterial(self):
        flag  = self.bs.readInt()
        #0xE000 0x6000 use for skin model , 0x0 is no skin.
        first = flag & 0xffff
        second = flag >> 16
        unk2  = self.bs.readInt()
        self.unk2 = unk2
        unk3  = self.bs.readFloat()
        if first >= 2:
            if flag & 0x40000000: # &后为真的话，代表是带蒙皮0x71区块的模型
                numBoneIDs = self.bs.readInt()
                for i in range(numBoneIDs):
                    self.MKMaterialSkinBonePalette.append(self.bs.readInt())
                #print(self.MKMaterialSkinUsedBoneIDList)
            else:
                self.useBonePalette = False
                self.MKMaterialSkinBonePalette.append(0)
                self.MKMaterialSkinBonePalette.append(0)
                self.MKMaterialSkinBonePalette.append(0)

        if first >= 3:
            unk =  self.bs.readInt()
        if  first >= 4:
            unk4 = self.bs.readInt()
            unk5 = self.bs.readFloat()
            if second & 0x8000:
                self.bs.seek(16,NOESEEK_REL) #4 floats
        if  first >= 5:
            meshType = self.bs.readInt()
            self.meshTypeFlag = meshType

class rMaterialList(object):
    def __init__(self,datas):
        self.bs = NoeBitStream(datas)
        #self.bs = bs
        self.matCount = 0
        self.matList = []
        self.texList = []
        self.MKMaterialList = []
        self.MKMaterialSkinBonePalette = []
        self.useBonePalette = True
    def rMaterialListStruct(self):
        header = rwChunk(self.bs)
        self.matCount = self.bs.readUInt()
        self.bs.seek(self.matCount*4,1)
    def getMaterial(self):
        self.rMaterialListStruct()
        for i in range(self.matCount):
            matData = self.bs.readBytes(rwChunk(self.bs).chunkSize)
            mat = rMatrial(matData)
            #mat = rMatrial(self.bs)
            texName = mat.rMaterialStruct()
            self.texList.append(texName)
            self.MKMaterialList.append(mat)
            if texName != "":
                #matName = "material[%d]" %len(self.matList)
                matName = texName
                #matName = "mtl"+str(i)
                material = NoeMaterial(matName, texName)
                material.setDefaultBlend(0)
                self.matList.append(material)
            else:
                matName = "mtl"+str(i)
                material = NoeMaterial(matName, None)
                material.setDiffuseColor(mat.diffuseColor)
                self.matList.append(material)
            #texture = NoeTexture()
            if len(mat.MKMaterialSkinBonePalette) > 0:
                self.MKMaterialSkinBonePalette.append(mat.MKMaterialSkinBonePalette)
                self.useBonePalette = mat.useBonePalette
            #pstr = "MatID:%d " %(i)
            #print(pstr,mat.MKMaterialSkinUsedBoneIDList)
        #return self.matList
class rGeometryList(object):
    def __init__(self,bs:NoeBitStream,geometryCount,vertMatList,hSkinBoneIDList):
        #self.bs = NoeBitStream(datas)
        self.bs = bs
        self.geometryCount = geometryCount
        self.vertMatList = vertMatList
        self.matList =[]
        self.hSkinBoneIDList = hSkinBoneIDList
    def readGeometry(self):
        for i in range(self.geometryCount):
            #print("GEOID:",i)
            vertMat = self.vertMatList[i]
            geometryHeader = rwChunk(self.bs)
            #datas = self.bs.readBytes(geometryHeader.chunkSize)
            #geo = rGeomtry(datas,vertMat,self.hSkinBoneIDList)
            geo = rGeomtry(self.bs,vertMat,self.hSkinBoneIDList)
            geo.rGeometryStruct()
            for m in range(len(geo.matList)):
                self.matList.append(geo.matList[m])


class rSkin(object):
    def __init__(self,datas,numVert,nativeFlag,version,matList):
        self.bs = NoeBitStream(datas)
        self.numVert = numVert
        self.nativeFlag = nativeFlag
        self.boneIndexs = bytes()
        self.boneWeights = bytes()
        self.usedBoneIndexList = []
        self.version = version
        self.pspBonePalettes = []
        self.matList = matList
        self.maxNumWeights = 0
    def readSkin(self):
        if self.nativeFlag == 0:
            boneCount = self.bs.readByte()
            usedBoneIDCount=self.bs.readByte()
            self.maxNumWeights = self.bs.readByte()
            unk2 = self.bs.readByte()
            self.bs.seek(usedBoneIDCount,1)

            self.boneIndexs = self.bs.readBytes(self.numVert*4)
            self.boneWeights= self.bs.readBytes(self.numVert*16)
            inverseBoneMats=[]
            self.usedBoneIndexList=[]
            for i in range(boneCount):
                if self.version < 0x34000 and self.maxNumWeights == 0:
                    flag = self.bs.readInt()
                    self.usedBoneIndexList.append(flag >> 24)
                inverseBoneMats.append(NoeMat44.fromBytes(self.bs.readBytes(64)))
            '''
            newBids = bytes()
            for w in range(self.numVert):
                weights = noeUnpack('4f',self.boneWeights[w*16:w*16+16] )
                b1,b2,b3,b4=(0,0,0,0)
                if weights[0] > 0:
                    b1 = noeUnpack('B',self.boneIndexs[w*4:w*4+1])[0]
                    # b1 = self.usedBoneIndexList[b1]
                if weights[1] > 0:
                    b2 = noeUnpack('B',self.boneIndexs[w*4+1:w*4+2])[0]
                    # b2 = self.usedBoneIndexList[b2]
                if weights[2] > 0:
                    b3 = noeUnpack('B',self.boneIndexs[w*4+2:w*4+3])[0]
                    # b3 = self.usedBoneIndexList[b3]
                if weights[3] > 0:
                    b4 = noeUnpack('B',self.boneIndexs[w*4+3:w*4+4])[0]
                    # b4 = self.usedBoneIndexList[b4]
                newBids += noePack("4B",b1,b2,b3,b4)
            rapi.rpgBindBoneIndexBuffer(newBids, noesis.RPGEODATA_UBYTE, 4 , 4)
            #rapi.rpgBindBoneIndexBuffer(self.boneIndexs, noesis.RPGEODATA_UBYTE, 4 , 4)
            rapi.rpgBindBoneWeightBuffer(self.boneWeights, noesis.RPGEODATA_FLOAT, 16, 4)
            '''
            #if not isMKPS2:
            #    self.bs.read('3f')

        else:   #nativeFlag == 1
            skinStruct = rwChunk(self.bs)
            platform = self.bs.readUInt()
            boneCount = self.bs.readUByte()
            numUsedBone = self.bs.readUByte()
            maxWeightsPerVertex = self.bs.readUByte()
            padding = self.bs.readUByte()

            #if isMKPS2:
            if platform == 4:
                self.usedBoneIndexList=[]
                for i in range(numUsedBone):                            
                    self.usedBoneIndexList.append(self.bs.readUByte())      
                inverseBoneMats=[]
                for i in range(boneCount):
                    inverseBoneMats.append(NoeMat44.fromBytes(self.bs.readBytes(64)))
            #if isMKPSP:
            if platform == 10:
                inverseBoneMats=[]
                for i in range(boneCount):
                    inverseBoneMats.append(NoeMat44.fromBytes(self.bs.readBytes(64)))
                self.bs.seek(20,NOESEEK_REL)
                boneLimit = self.bs.readInt()
                numSplit = self.bs.readInt()
                numBonePalette = self.bs.readInt()
                self.usedBoneIndexList=[]
                if numSplit:
                    for i in range(boneCount):
                        self.usedBoneIndexList.append(self.bs.readUByte())

                table1Offset = self.bs.tell()
                table2Offset = self.bs.tell() + numSplit * 2

                for i in range(numSplit):
                    self.bs.seek(table1Offset + i * 2)
                    table2ID = self.bs.readUByte()
                    numID = self.bs.readUByte()
                    boneIDs = []
                    self.bs.seek(table2Offset + table2ID * 2)
                    for b in range(numID):
                        boneID = self.bs.readUByte()
                        boneCount = self.bs.readUByte()
                        for bi in range(boneCount):
                            boneIDs.append(boneID + bi)
                    self.pspBonePalettes.append(boneIDs)


            #self.bs.read('7i') #for ps2 dff
            #self.bs.seek(16,1) #for Mortal Kombat PS2
class rBinMeshPLG(object):
    def __init__(self,datas,matList,nativeFlag):
        self.bs = NoeBitStream(datas)
        #self.bs = bs
        self.matList = matList
        self.nativeFlag = nativeFlag
        self.matIdList = []
        self.matIdNumFaceList = []
        self.indicesMatIDs = []
        self.faceIndices = []
        self.faceStrips = []
        self.numSplitMatID = 0
        self.faceType = 0
        self.indicesCount = 0
    def readFace(self):
        self.faceType = self.bs.readInt() # 1 = triangle strip
        self.numSplitMatID = self.bs.readUInt()
        self.indicesCount = self.bs.readUInt()
        for i in range(self.numSplitMatID):
            numFaceIndices = self.bs.readUInt()
            matID = self.bs.readUInt()
            self.matIdList.append(matID)
            self.matIdNumFaceList.append(numFaceIndices)
            if self.nativeFlag != 1:
                # matName = self.matList[matID].name
                # rapi.rpgSetMaterial(matName)
                tristrips = self.bs.readBytes(numFaceIndices*4)
                self.faceStrips.append(tristrips)
                # rapi.rpgCommitTriangles(tristrips, noesis.RPGEODATA_UINT, numFaceIndices, noesis.RPGEO_TRIANGLE_STRIP, 1)
                indices = struct.unpack(numFaceIndices * "I", tristrips)
                for vertID in indices:
                    self.indicesMatIDs.append(matID)
                    self.faceIndices.append(vertID)

class materialTristripsInfo(object):
    def __init__(self,vertexCountStart,vertexCountEnd,tristripsCount,unknownCount):
        self.vertexCountStart = vertexCountStart
        self.vertexCountEnd = vertexCountEnd
        self.tristripsCount = tristripsCount
        self.unknownCount = unknownCount
class rMKPS2NativeDataPLG(object):
    def __init__(self,bs:NoeBitStream,matList,binMeshPLG,vertMat,MKMaterialSkinBonePalette,skinFlag,HAnimSkinBoneIDList,useBonePalette,skinPlgBoneMap,MKMaterialList):
        #self.bs = NoeBitStream(natvieDatas)
        self.bs = bs
        self.matList = matList
        self.matIdList = binMeshPLG.matIdList
        self.matIdNumFaceList = binMeshPLG.matIdNumFaceList
        self.vertMat = vertMat  
        self.MKMaterialSkinBonePalette = MKMaterialSkinBonePalette
        self.skinFlag = skinFlag
        self.HAnimSkinBoneIDList = HAnimSkinBoneIDList
        self.useBonePalette = useBonePalette
        self.skinPlgBoneMap = skinPlgBoneMap
        self.MKMaterialList = MKMaterialList
    def readMesh(self):
        splitCount = len(self.matIdList)
        for i in range(splitCount):
            dataSize = self.bs.readUInt()
            meshType = self.bs.readUInt()
            endOfs = self.bs.tell() + dataSize
            
            padLen1 = ((self.bs.tell() + 127) & 0xFFFFFF80) - self.bs.tell()
            padLen2 = 128 - padLen1
            self.bs.seek(padLen1,NOESEEK_REL)
            vifSize = dataSize - 128
            vifData =  self.bs.readBytes(vifSize)
            unpackData = rapi.unpackPS2VIF(vifData) 
            paddingLength = endOfs - self.bs.tell() 
            self.bs.seek(paddingLength,NOESEEK_REL) 

            vertDatas = []
            UVDatas =[]
            normalDatas = [] 
            colorDatas = []
            faceDatas = []    
            skinBoneIDs = []
            skinWeights = []
            realNumVertsList = []
            prevStripIDList = []
            vertIDList1Array = []
            vertIDList2Array = []
            sharedVertexIDList = []   
            MKPS2SkinDatas = []


            count0x71 = 4
            SkinUVMeshInfoList = []

            # MKA 单骨头武器模型带SKIN PLG模型，但没有权重0x71区块。MK材质里没有骨头调色板列表，标志0x00000005。
            # MKD 单骨头武器模型带SKIN PLG模型，但有权重0x71区块。MK材质有骨头调色板列表，标志0x60000005。

            # Mesh Type 128 Player COSTUME / Weapon skined model. 0x6000 flag. 
            # MKMaterial has bone palette, has 0x71 weights chunk.
            if self.MKMaterialList[self.matIdList[i]].meshTypeFlag == 128:
                count0x71 = 4
                self.skinFlag = True
                BonePalette = self.MKMaterialSkinBonePalette[self.matIdList[i]]

            # Mesh Type 129 Weapon skined model. 
            # 0xE000 & 0x8000 special data flag. 
            # MKMaterial has bone palette, has 0x71 weights chunk.                
            elif self.MKMaterialList[self.matIdList[i]].meshTypeFlag == 129:
                count0x71 = 4
                self.skinFlag = True
                BonePalette = self.MKMaterialSkinBonePalette[self.matIdList[i]]

            # Mesh Type 130 Player Reflect / WEAPON_RF No UV skined model. 
            # MKMaterial has bone palette, has 0x6E single weight chunk.
            # no 0x71 index/weights chunk.
            elif self.MKMaterialList[self.matIdList[i]].meshTypeFlag == 130:
                self.skinFlag = True
                BonePalette = self.MKMaterialSkinBonePalette[self.matIdList[i]]

            # Mesh Type 131 NPC / Player DECOY skined model. 
            # MKMaterial no bone palette, has 0x71 weights chunk.  
            # BonePalette in HAnimSkinBoneIDList (HAnim list id).               
            elif self.MKMaterialList[self.matIdList[i]].meshTypeFlag == 131:
                self.skinFlag = True
                count0x71 = 4
                BonePalette = self.HAnimSkinBoneIDList

            # Mesh Type 137 MKA Weapon / Stage model.
            # MKMaterial no bone palette , no 0x71 weights chunk.
            # Whether there is a SKIN PLG section depends on GEO.SkinFlag = True.
            elif self.MKMaterialList[self.matIdList[i]].meshTypeFlag == 137:
                count0x71 = 2
                self.skinFlag = False

            vertStripIndex = -1

            # Mesh Type 128, 129 Player COSTUME / Weapon skined model.
            # Has UV Player SkinedModel , need reorder vertex list and copy new vertex to new list.
            # Bonemap in MKMaterial bones list(id is haim list id).
            # BoneID1 = vx & 0xff / 4 - 1
            # BoneID2 = vy & 0xff / 4 - 1
            # BoneID3 = vz & 0xff / 4 - 1
            # 0x68 - vertex
            # 0x6A - normal
            # 0x65 - uv
            # 0x6E - 8bytes. vertex info section. byte4 = real numVert.
            # 0x6D - Vertex shared list (the vertex ID of the previous strip to the next strip). The first triangle strip does not contain this data.
            # 0x6D - if current strip missing some vertex id then will have this section.
            # 0x71 chunk 1 = vertList 1 USHORT value; unkFlag = value & 0x2; vertID = value & 0x7FFC. skipFlag = value & 0x8000
            # 0x71 chunk 4 = vertList 2
            # 0x71 chunk 2 = skin/vertex weights chunk, UBYTE weight1/255; UBYTE weight1 & 0xf; if weight1 and weight 2 == 0 , is only boneid1 used. weight = 1.0;
            # 0x72 chunk 3 = skin/vertex weights chunk, UBYTE weight2/255; UBYTE weight2 & 0xf;
            
            # 0x71 boneID is HAnimListID real bone id = HAimSkinIDList[HAnimListID].skinBoneID
            # 0x71 weight 16 + 0 is 1.0 weight. 8+8 is 0.5 + 0.5 12+4 = 12/1 + 4/16
            # 0x71 weight A + B = 15. 2 weights. weight /= 255.0. wa+wb=255.
            # 0x71 weight A + b < 15. 3 weights.

            # Mesh Type 131 NPC / Player DECOY skined model. 
            # Has UV NPC SkinedModel 
            # BonePalette in HAnimSkinBoneIDList (HAnim list id).
            # MKMaterial no bone palette.
            # 0x68 vertex, 0x6A normal, 0x65 uv, 0x6D vertex shared list.
            # 0x71 chunk x 4. same as Mesh Type 128.

            # Mesh Type 130 Player REFLECT / WEAPON_RF no UV skined model. 
            # No UV SkinedModel
            # 0x68 Vertex float[3]
            # 0x6A Normals byte[3]            
            # 0x6E 4bytes. UBYTE1 boneid/4 - 1 ; UBYTE2 and UBYTE3 is zero; UBYTE4 skipFlag;
            
            # Mesh Type 137 MKA Weapon / Stage model.
            # Has UV Non-SkinedModel MapMesh
            # 0x64 UV float[2]
            # 0x68 Vertex float[3]
            # 0x6A Normals byte[3]
            # 0x6C UV1+UV2 float[4]
            # 0x6A byte[3] unknown
            # 0x6E Colors RGBA ubyte[4] 
            # 0x71 chunk1 and chunk2 short;
            
            mapVertIdInterval = 0
            for up in unpackData:
                if up.numElems == 3 and up.elemBits == 32:      #0x68000000
                    vertStripIndex += 1
                    #print("read vertex...",vertStripIndex,"numVert:",len(up.data)//12)
                    vertDatas.append(up.data)
                elif up.numElems == 2 and up.elemBits == 16:    #0x65000000
                    UVDatas.append(getUV(up.data))
                elif up.numElems == 2 and up.elemBits == 32:    #0x64000000
                    UVDatas.append(up.data)
                elif up.numElems == 4 and up.elemBits == 32:    #0x6C000000
                    if len(up.data) > 16 :
                        numV = len(up.data) // 16
                        uv1 = bytearray(numV*8)
                        for u in range(numV):
                            uv1[u*8:u*8+8] = up.data[u*16:u*16+8]
                        UVDatas.append(uv1)
                elif up.numElems == 3 and up.elemBits == 8:     #0x6A000000
                    if len(normalDatas) < len(vertDatas):       #skip second 0x6A
                        normals = getNormal(up.data)
                        normalDatas.append(normals)
                elif up.numElems == 1 and up.elemBits == 16:    #0x71000000 (0x61000000)
                    if self.skinFlag:
                        if count0x71 % 4 == 0:
                            vertIDList1 = getVertexIDListSkinMesh(up.data,self.useBonePalette)
                            vertIDList1Array.append(vertIDList1)
                        if count0x71 % 4 == 3:
                            vertIDList2 = getVertexIDListSkinMesh(up.data,self.useBonePalette)
                            vertIDList2Array.append(vertIDList2)
                        if count0x71 % 4 == 1:
                            MKPS2SkinDatas.append(up.data)
                        if count0x71 % 4 == 2:
                            MKPS2SkinDatas.append(up.data)
                    else:
                        if count0x71 % 2 == 0:
                            vertIDList1 = getVertexIDListMapMesh(up.data)
                            vertIDList1Array.append(vertIDList1)
                            mapVertIdInterval = vertIDList1[5]
                        if count0x71 % 2 == 1:
                            vertIDList2 = getVertexIDListMapMesh(up.data)
                            vertIDList2Array.append(vertIDList2)
                            mapVertIdInterval = vertIDList2[5]
                    count0x71 += 1                        
                elif up.numElems == 4 and up.elemBits == 8:     #0x6E000000
                    if self.skinFlag:
                        if len(up.data) > 8: #skip has uv skined model header data
                            faceAndSkinData = createTriListNoUVMesh(up.data,BonePalette)
                            faceDatas.append(faceAndSkinData[0])
                            skinBoneIDs.append(faceAndSkinData[1])
                            skinWeights.append(faceAndSkinData[2])
                        else:
                            realNumVertsList.append(noeUnpack("B",up.data[3:4])[0])
                            SkinUVMeshInfoList.append(up.data)
                            #first8ByteStr = "%d,%d,%d,%d,%d,%d,%d,%d\n" %(up.data[0],up.data[1],up.data[2],up.data[3],up.data[4],up.data[5],up.data[6],up.data[7])
                            #print(first8ByteStr)
                    elif len(up.data) > 4 :
                        colorDatas.append(up.data)
                    elif len(up.data) == 4:
                        realNumVertsList.append(noeUnpack("B",up.data[3:4])[0])
                        first4ByteStr = "%d,%d,%d,%d\n" %(up.data[0],up.data[1],up.data[2],up.data[3])
                        #print(first4ByteStr)
                elif up.numElems == 4 and up.elemBits == 16:    #0x6D000000
                    if self.skinFlag:
                        sharedIDList = getsharedVertexIDListSkinMesh(up.data,self.useBonePalette)
                        sharedVertexIDList.append([(vertStripIndex+1),sharedIDList])
                    else:
                        sharedIDList = getsharedVertexIDListMapMesh(up.data,mapVertIdInterval)
                        sharedVertexIDList.append([(vertStripIndex+1),sharedIDList])
  
            newVertDatas = []
            newUVDatas = []
            newNormalDatas = []
            newColorDatas = []
            newSkipListDatas = []
            newSkinBoneIDs = []
            newSkinWeights = []
            if len(vertIDList1Array) and self.skinFlag:
                skinWeights = getMKPS2VertexWeights(MKPS2SkinDatas)
                skinBoneIDs = getMKPS2VertexBoneIDs(vertDatas,BonePalette,self.HAnimSkinBoneIDList,self.skinPlgBoneMap,self.useBonePalette)              
            numVertBlock = len(vertDatas)
            totalVertCount = 0   
            # 根据现有数据填充生成顶点列表
            for v in range(numVertBlock):   
                tempFaceDatas = []
                #rapi.rpgSetName("mesh"+str(i) + "_" + str(v))
                #print("mesh"+str(i) + "_" + str(v))
                #print("vert buffer strip id:",v)
                vertBuffer = vertDatas[v]
                numVert = len(vertBuffer) // 12 
                normalData = normalDatas[v]   
                if len(UVDatas):
                    UVData = UVDatas[v]
                if len(colorDatas):
                    colorData = colorDatas[v]
                if len(skinBoneIDs):
                    #print("boneid size:",len(skinBoneIDs[v]))   
                    boneIDs = skinBoneIDs[v]
                    weights = skinWeights[v]  
                              
                if len(vertIDList1Array) and numVert > 2:# and self.skinFlag:
                    # print(vertIDList1Array[v][0])
                    vertCount = realNumVertsList[v]
                    if not self.skinFlag:
                        maxVertID = 0
                        if maxVertID < vertIDList1Array[v][3]:
                            maxVertID =  vertIDList1Array[v][3]
                        if maxVertID < vertIDList2Array[v][3]:
                            maxVertID =  vertIDList2Array[v][3]                        
                        if v > 0:
                            for j in range(len(sharedVertexIDList)):                            
                                if sharedVertexIDList[j][0] == v:
                                    for s in range(len(sharedVertexIDList[j][1][0])):                                            
                                        curStripVertID = sharedVertexIDList[j][1][1][s]        
                                        if maxVertID < curStripVertID:
                                            maxVertID = curStripVertID
                        vertCount = maxVertID + 1
                    #print("vertCount:",vertCount)
                    totalVertCount += vertCount
                    padVec3 = NoeVec3.fromBytes(vertBuffer[0:12])
                    padNomral = NoeVec3.fromBytes(normalData[0:12])                    
                    padUV = noeUnpack('2f',UVData[0:8])

                    vertList = [padVec3] * vertCount
                    normalList = [padNomral] * vertCount
                    uvList = [padUV] * vertCount
                    colorList = [[0,0,0,0]] * vertCount
                    boneIDList = [[0,0,0]] * vertCount
                    weightList = [[0.0,0.0,0.0]]* vertCount
                    
                    if len(skinBoneIDs):
                        padBoneID = noeUnpack('3B',boneIDs[0:3])
                        padWeight = noeUnpack('3f',weights[0:12])    
                        boneIDList = [padBoneID] * vertCount
                        weightList = [padWeight]* vertCount
                    if len(colorDatas):
                        padColor = noeUnpack('4B',colorData[0:4])
                        colorList = [padColor] * vertCount
                    skipList = [True] * vertCount
                    vertIDList = [False] * vertCount
                    vertIDList2 = ["missing"] * vertCount
                    for j in range(len(vertIDList1Array[v][0])):
                        vertID = vertIDList1Array[v][0][j]                        
                        vertList[vertID] = NoeVec3.fromBytes(vertBuffer[j*12:j*12+12])
                        normalList[vertID] = NoeVec3.fromBytes(normalData[j*12:j*12+12])
                        uvList[vertID] = noeUnpack('2f',UVData[j*8:j*8+8])
                        skipList[vertID] = vertIDList1Array[v][2][j]
                        vertIDList[vertID] = True
                        vertIDList2[vertID] = 1
                        if len(skinBoneIDs):
                            #print(len(vertIDList1Array[v][0]),j,boneIDs[j*3:j*3+3])
                            boneIDList[vertID] = noeUnpack('3B',boneIDs[j*3:j*3+3])
                            weightList[vertID] = noeUnpack('3f',weights[j*12:j*12+12])
                        if len(colorDatas):
                            colorList[vertID] = noeUnpack('4B',colorData[j*4:j*4+4])
                    for j in range(len(vertIDList2Array[v][0])):
                        vertID = vertIDList2Array[v][0][j]
                        #print(vertID,len(vertBuffer)//12)
                        vertList[vertID] = NoeVec3.fromBytes(vertBuffer[j*12:j*12+12])
                        normalList[vertID] = NoeVec3.fromBytes(normalData[j*12:j*12+12])
                        uvList[vertID] = noeUnpack('2f',UVData[j*8:j*8+8])
                        skipList[vertID] = vertIDList2Array[v][2][j]
                        vertIDList[vertID] = True
                        vertIDList2[vertID] = 1
                        if len(colorDatas):
                            colorList[vertID] = noeUnpack('4B',colorData[j*4:j*4+4])  
                        if len(skinBoneIDs):
                            boneIDList[vertID] = noeUnpack('3B',boneIDs[j*3:j*3+3])
                            weightList[vertID] = noeUnpack('3f',weights[j*12:j*12+12])                            
                    #print("mesh" + str(i) + "_" + str(v))
                    #print(vertIDList2)
                    #print("ori:",(len(vertBuffer) // 12 ),"new:",vertCount)
                    if v > 0:
                        for j in range(len(sharedVertexIDList)):                            
                            if sharedVertexIDList[j][0] == v:
                                #print(sharedVertexIDList[j][1][0])
                                #print(sharedVertexIDList[j][1][1])
                                for s in range(len(sharedVertexIDList[j][1][0])):
                                    prevStripVertID = sharedVertexIDList[j][1][0][s]
                                    curStripVertID = sharedVertexIDList[j][1][1][s]
                                    vid = prevStripVertID                                    
                                    prevStripID = v - 1
                                    #print(curStripVertID,vid)
                                    vertList[curStripVertID] = NoeVec3.fromBytes(newVertDatas[prevStripID][vid*12:vid*12+12])
                                    normalList[curStripVertID] = NoeVec3.fromBytes(newNormalDatas[prevStripID][vid*12:vid*12+12])
                                    uvList[curStripVertID] = noeUnpack('2f',newUVDatas[prevStripID][vid*8:vid*8+8])
                                    skipList[curStripVertID] = sharedVertexIDList[j][1][2][s]                                                                         
                                    if len(skinBoneIDs):
                                        boneIDList[curStripVertID] = noeUnpack('3B', newSkinBoneIDs[prevStripID][vid*3:vid*3+3])
                                        weightList[curStripVertID] = noeUnpack('3f',newSkinWeights[prevStripID][vid*12:vid*12+12])
                                    vertIDList2[curStripVertID] = "prev" + str(vid) 
                    #print(vertIDList2)
                    newVertBuffer = bytes()
                    newNormalBuffer = bytes()
                    newUVBuffer = bytes()
                    newColorBuffer = bytes()
                    newBoneIDBuffer = bytes()
                    newWeightBuffer = bytes()
                    for j in range(vertCount):
                        vert = vertList[j]
                        newVertBuffer += vert.toBytes()
                        normal = normalList[j]
                        newNormalBuffer += normal.toBytes()
                        uv = uvList[j]
                        newUVBuffer += noePack('2f',uv[0],uv[1])
                        if len(colorDatas):   
                            color = colorList[j]
                            newColorBuffer += noePack('4B',color[0],color[1],color[2],color[3])
                        if len(skinBoneIDs):
                            tempBoneIDs = boneIDList[j]
                            tempWeights = weightList[j]
                            newBoneIDBuffer += noePack('3B',tempBoneIDs[0],tempBoneIDs[1],tempBoneIDs[2])
                            newWeightBuffer += noePack('3f',tempWeights[0],tempWeights[1],tempWeights[2])                            
                    vertBuffer = newVertBuffer
                    newVertDatas.append(newVertBuffer)
                    normalData = newNormalBuffer
                    newNormalDatas.append(newNormalBuffer)
                    UVData = newUVBuffer
                    newUVDatas.append(newUVBuffer)
                    newSkipListDatas.append(skipList)
                    faceBuffer = createTriList(skipList)   
                    #faceBuffer = getTriangleList(vertBuffer,1)                
                    tempFaceDatas.append(faceBuffer)
                    if len(colorDatas): 
                        colorData = newColorBuffer
                        newColorDatas.append(newColorBuffer)
                    if len(skinBoneIDs):
                        boneIDs = newBoneIDBuffer
                        weights = newWeightBuffer
                        newSkinBoneIDs.append(newBoneIDBuffer)
                        newSkinWeights.append(newWeightBuffer)

                    
                vertBuffer = getTransformVertex(vertBuffer,self.vertMat)       
                rapi.rpgBindPositionBuffer(vertBuffer, noesis.RPGEODATA_FLOAT, 12) 
                numVert = len(vertBuffer) // 12 
                #print("numVert:",numVert)               
                normalData = getTransformNormal(normalData,self.vertMat)
                rapi.rpgBindNormalBuffer(normalData, noesis.RPGEODATA_FLOAT, 12)
                if len(UVDatas):
                    rapi.rpgBindUV1Buffer(UVData, noesis.RPGEODATA_FLOAT, 8)                      
                if len(colorDatas) and len(vertIDList1Array) > 0:  
                #if len(colorDatas):            
                    rapi.rpgBindColorBuffer(colorData, noesis.RPGEODATA_UBYTE, 4, 4)                   
                
                matID = self.matIdList[i]
                matName = self.matList[matID].name
                #rapi.rpgSetName(matName)
                rapi.rpgSetMaterial(matName)
                '''

                matName = "mtl" + str(i) + "_" + str(v)
                rapi.rpgSetName(matName)
                rapi.rpgSetMaterial(matName)
                '''
                if len(skinBoneIDs):
                    if len(skinBoneIDs[v]) // numVert == 4:          #for no uv skined model                     
                        rapi.rpgBindBoneIndexBuffer(skinBoneIDs[v], noesis.RPGEODATA_INT, 4, 1)
                        rapi.rpgBindBoneWeightBuffer(skinWeights[v], noesis.RPGEODATA_FLOAT, 4, 1)  
                    else:                                            #for has uv skined model
                        rapi.rpgBindBoneIndexBuffer(boneIDs, noesis.RPGEODATA_UBYTE, 3, 3)
                        rapi.rpgBindBoneWeightBuffer(weights, noesis.RPGEODATA_FLOAT, 12, 3) 
                if len(faceDatas):
                    if numVert > 2 : 
                        #print("NO UV SKIN MESH")
                        faceBuffer = faceDatas[v] 
                        rapi.rpgCommitTriangles(faceBuffer, noesis.RPGEODATA_INT, len(faceBuffer)//4, noesis.RPGEO_TRIANGLE, 1)  
                elif len(tempFaceDatas) > 0:
                    #print("UV SKIN MESH and Map MESH")
                    faceBuffer = tempFaceDatas[0] 
                    rapi.rpgCommitTriangles(faceBuffer, noesis.RPGEODATA_INT, len(faceBuffer)//4, noesis.RPGEO_TRIANGLE, 1)
                elif len(vertIDList1Array) == 0: #NO vertex indices map mesh
                    faceBuffer = getTriangleList(vertBuffer,1)
                    rapi.rpgCommitTriangles(faceBuffer, noesis.RPGEODATA_INT, len(faceBuffer)//4, noesis.RPGEO_TRIANGLE, 1)
                rapi.rpgClearBufferBinds()
def getMKPS2VertexBoneIDs(flagData,MKMaterialUsedBoneIDList,hanimSkinBoneIDList,skinPlgBoneMap,useBonePalette):
    numBlock = len(flagData)
    boneIDsList = []
    bonePalette = []
    if useBonePalette:  # player mesh
        for i in range(len(MKMaterialUsedBoneIDList)):
            bonePalette.append(hanimSkinBoneIDList[MKMaterialUsedBoneIDList[i]])
    else:               # npc mesh
        bonePalette = hanimSkinBoneIDList   
    for i in range(numBlock):
        boneIDs = bytes()
        numVert = len(flagData[i]) // 12
        for j in range(numVert):            
            boneID1 = flagData[i][j*12+0]
            boneID2 = flagData[i][j*12+4]
            boneID3 = flagData[i][j*12+8]
            if boneID1 > 0:
                boneID1 = boneID1 // 4 - 1
                boneID1 = bonePalette[boneID1]
            if boneID2 > 0:
                boneID2 = boneID2 // 4 - 1
                boneID2 = bonePalette[boneID2]
            if boneID3 > 0:
                boneID3 = boneID3 // 4 - 1  
                boneID3 = bonePalette[boneID3]
            boneIDs += noePack('3B',boneID1,boneID2,boneID3)    
        boneIDsList.append(boneIDs)
    return boneIDsList                          
def getMKPS2VertexWeights(flagData):      
    numBlock = len(flagData) // 2

    weightsList = []


    for i in range(numBlock):
        bin1 = NoeBitStream(flagData[i*2])
        bin2 = NoeBitStream(flagData[i*2+1])
        boneIDs = bytes()
        weights = bytes()
        numVert = len(flagData[i*2]) // 2
        
        for j in range(numVert):
            weight1 = bin1.readUByte()
            boneID1 = bin1.readUByte() 
            weight2 = bin2.readUByte()
            boneID2 = bin2.readUByte()

            if (boneID1 + boneID2) == 16:
                if boneID1 == 16:                         
                    weights += noePack('3f',1.0,0,0)
                elif boneID2 == 16:                    
                    weights += noePack('3f',0,1.0,0)
                else:                          
                    weights += noePack('3f',boneID1/16,boneID2/16,0)
            elif (boneID1 + boneID2) == 15:

                weights += noePack('3f',boneID1/15,boneID2/15,0)
            elif (boneID1 + boneID2) < 15:
                       
                weights += noePack('3f',boneID1/15,boneID2/15,(15-boneID1-boneID2)/15)

        weightsList.append(weights)
    return weightsList
            
        
        
def getsharedVertexIDListSkinMesh(flagData,useBonePalette):  
    vin = NoeBitStream(flagData)
    numVerts = len(flagData) // 2
    prevStripVertexIDList = []
    curStripVertexIDList = []
    skipList1 = []
    skipList2 = []
    for i in range (numVerts):     
        value = vin.readUShort()
        unkFlag = value & 0x2
        skipFlag = (value & 0x8000) == 0x8000  
        if useBonePalette:
            if (value & 0x7FFF) < 488:
                vertID = ((value & 0x7FFF) - 130) // 4
            else:
                vertID = ((value & 0x7FFF) - 488) // 4                
        else:
            if (value & 0x7FFF) < 634:
                vertID = ((value & 0x7FFF) - 191) // 3
            else:
                vertID = ((value & 0x7FFF) - 634) // 3
        if i % 2 == 0:
            prevStripVertexIDList.append(vertID)
            skipList1.append(skipFlag)
        elif i % 2 == 1:
            curStripVertexIDList.append(vertID)
            skipList2.append(skipFlag)
    return [prevStripVertexIDList,curStripVertexIDList,skipList1,skipList2]
  
def getVertexIDListSkinMesh(flagData,useBonePalette):
    vin = NoeBitStream(flagData)
    numVerts = len(flagData) // 2  
    vertIDList = []
    unkFlagList = []
    skipFlagList = []
    # base index 4 type: 130 488 191 634

    testList = []
    for i in range (numVerts): 
        value = vin.readUShort()
        unkFlag = value & 0x2
        if useBonePalette:
            if (value & 0x7FFF) < 488:
                vertID = ((value & 0x7FFF) - 130) // 4
            else:
                vertID = ((value & 0x7FFF) - 488) // 4
        else:            
            if (value & 0x7FFF) < 634:
                vertID = ((value & 0x7FFF) - 191) // 3
            else:
                vertID = ((value & 0x7FFF) - 634) // 3
        skipFlag = (value & 0x8000) == 0x8000             
        if (value & 0x7FFC) >= 0:
            vertIDList.append(vertID)
            unkFlagList.append(unkFlag)
            skipFlagList.append(skipFlag)
        testList.append(value&0x7fff)
    #print("Ori:",testList)
    #print("sort:",sorted(testList))
    #print("real ori:",vertIDList)
    #print("real sort:",sorted(vertIDList))
    return [vertIDList,unkFlagList,skipFlagList]

def getsharedVertexIDListMapMesh(flagData,mapVertIdInterval):
    vin = NoeBitStream(flagData)
    numVerts = len(flagData) // 2
    prevStripVertexIDList = []
    curStripVertexIDList = []
    skipList1 = []
    skipList2 = []
    vertStorageIDList = []
    #print("shared map interval:",mapVertIdInterval)
    for i in range (numVerts):    
        value = vin.readUShort()
        value1 = value & 0x7fff
        if mapVertIdInterval % 3 == 0:
            if value1 >= 147 and value1 < 622:
                if (value1 - 147) % 3 > 0:
                    vertID = (value1 - 238) // 3
                else:
                    vertID = (value1 - 147) // 3
            elif value1 >= 622:
                if (value1 - 622) % 3 > 0:
                    vertID = (value1 - 723) // 3
                else:
                    vertID = (value1 - 622) // 3
        elif mapVertIdInterval % 5 == 0:
            if value1 >= 193 and value1 < 671:
                if (value1 - 193) % 5 > 0:
                    vertID = (value1 - 201) // 5
                else:
                    vertID = (value1 - 193) // 5
            elif value1 >= 671:
                if (value1 - 671) % 5 > 0:
                    vertID = (value1 - 679) // 5
                else:
                    vertID = (value1 - 671) // 5
        skipFlag = (value & 0x8000) == 0x8000  
        if i % 2 == 0:       
            prevStripVertexIDList.append(vertID)
            skipList1.append(skipFlag)
        elif i % 2 == 1:
            curStripVertexIDList.append(vertID)
            skipList2.append(skipFlag)     
        vertStorageIDList.append(value&0x7fff)
    #print("Shared ID LIST:")
    #print(vertStorageIDList)
    #print(prevStripVertexIDList)   
    #print(curStripVertexIDList)
    
    return [prevStripVertexIDList,curStripVertexIDList,skipList1,skipList2]  
def getVertexIDListMapMesh(flagData):
    vin = NoeBitStream(flagData)
    numVerts = len(flagData) // 2  
    vertIDList = []
    unkFlagList = []
    skipFlagList = []
    
    maxVertID = 0 
    vertStorageIDList = []
    test = []
    for i in range (numVerts): 
        value = vin.readUShort()
        unkFlag = value & 0x3    
        skipFlag = (value & 0x8000) == 0x8000              
        unkFlagList.append(unkFlag)
        skipFlagList.append(skipFlag)
        vertStorageIDList.append(value&0x7fff)
        test.append(value&0x7fff)

    test.sort()
    intervalList = []
    for i in range (numVerts): 
        if i > 0:
            intervalValue = test[i] - test[i-1] 
            intervalList.append(intervalValue)
    intervalList.sort()
    #print(intervalList)
    #print("ID LIST:")
    #print(test) 

    firstID = vertStorageIDList[0]
    secondID = vertStorageIDList[1]
    interval = intervalList[0]

    # Base index values
    # MKD 193-5 671-5 
    # MKA 201-5 679-5
    # MKD 1-3
    # MKA 147-3 622-3 
    # MKA MKD 238-3 723-3
    for i in range (numVerts): 
        value = vertStorageIDList[i]
        if  (interval % 3) == 0:
            if value < 622 and value >= 1:
                if value % 3 == 1:
                    if value >= 238:
                        vertID = (value - 238) // 3
                    else:
                        vertID = (value - 1) // 3
                elif value % 3 == 0 :
                    vertID = (value - 147) // 3
               
            elif value >= 622:
                if (value - 622) % 3 > 0:
                    vertID = (value - 723) // 3
                else:
                    vertID = (value - 622) // 3
        elif (interval % 5) == 0:
            if value < 671 and value >= 193:
                if (value - 193) % 5 > 0:
                    vertID = (value - 201) // 5
                else:
                    vertID = (value - 193) // 5
            elif value >= 671:
                if (value - 671) % 5 > 0:
                    vertID = (value - 679) // 5
                else:
                    vertID = (value - 671) // 5
        vertIDList.append(vertID)
        if maxVertID < vertID:
            maxVertID = vertID
    vertStorageIDList.sort()       
    #print("v count: ",len(vertIDList),numVerts)
    #print("v List:",vertIDList)
    return [vertIDList,unkFlagList,skipFlagList,maxVertID,vertStorageIDList,interval]    
def createTriList(skipList):   
    out = NoeBitStream()
    numVerts = len(skipList)
    startDir = -1
    faceDir = startDir
    f1 = 0
    f2 = 1
    for i in range (numVerts):        
        f3 = i
        skipFlag = skipList[i] #skip Isolated vertex
        faceDir *= -1 
        if skipFlag != True:
            if faceDir > 0:
                out.writeInt(f1)
                out.writeInt(f2)
                out.writeInt(f3)
            else:
                out.writeInt(f2)
                out.writeInt(f1)
                out.writeInt(f3)            
        f1 = f2
        f2 = f3         
    return out.getBuffer()  
def createTriListNoUVMesh(flagData,usedBoneIDList):
    vin = NoeBitStream(flagData)
    out = NoeBitStream()
    numVerts = len(flagData)//4
    faceDir = 1
    f1 = 0
    f2 = 1
    boneIDs = bytes()
    weights = bytes()  
    
    for i in range (numVerts):   
        boneID1 = vin.readUByte() // 4 #always only use boneID1
        weight1 = vin.readUByte() #always 0
        boneID2 = vin.readUByte() #always 0
        bitFlag = vin.readUByte() #weight2 always 0
        weight2 = bitFlag & 0xFE

        weights += noePack("f",1.0)
        boneIDs += noePack("i",usedBoneIDList[boneID1-1])
        f3 = i
        skipFlag = bitFlag & 0x1 #skip Isolated vertex
        if skipFlag != 1:
            if f1 != f2 and f2 != f3 and f3 != f1:
                if faceDir > 0:
                    out.writeInt(f1)
                    out.writeInt(f2)
                    out.writeInt(f3)
                else:
                    out.writeInt(f2)
                    out.writeInt(f1)
                    out.writeInt(f3)
        faceDir *= -1
        f1 = f2
        f2 = f3
    #print("end")
    return [out.getBuffer(),boneIDs,weights]    

def getTriangleList(vertBuffer,startDir):
    triangleList = []
    triangleDir = startDir                        
    for j in range(len(vertBuffer)//12-2):
        v1 = noeUnpack('3f',vertBuffer[j*12:j*12+12])
        v2 = noeUnpack('3f',vertBuffer[(j+1)*12:(j+1)*12+12])
        v3 = noeUnpack('3f',vertBuffer[(j+2)*12:(j+2)*12+12])
        f1 = j
        f2 = j + 1
        f3 = j + 2
        if v1 != v2 and v2 != v3 and v1 != v3:
            if triangleDir > 0:
                triangleList.append((f1,f2,f3))
            else:
                triangleList.append((f2,f1,f3))
        triangleDir *= -1
    faceBuffer = bytes()
    for j in range(len(triangleList)):
        faceBuffer += noePack('3I',triangleList[j][0],triangleList[j][1],triangleList[j][2])    
    return faceBuffer
def getTransformVertex(vertBuffer,parentBoneMatrix):
    vin = NoeBitStream(vertBuffer)
    out = NoeBitStream()
    numVerts = len(vertBuffer) // 12
    for i in range(numVerts):
        vert = NoeVec3.fromBytes(vin.readBytes(12))
        vert *= parentBoneMatrix        
        out.writeBytes(vert.toBytes())
    return out.getBuffer()
def getUV(uvdata):
    uvin = NoeBitStream(uvdata)
    out = NoeBitStream()
    numVerts = len(uvdata) // 4
    for i in range(numVerts):
        u = uvin.readShort() / 4096.0
        v = uvin.readShort() / 4096.0
        out.writeFloat(u)
        out.writeFloat(v)
    return out.getBuffer()  
def getTransformNormal(normalData,parentBoneMatrix):
    nin = NoeBitStream(normalData)
    out = NoeBitStream()
    numVerts = len(normalData) // 12
    for i in range(numVerts):
        normal = NoeVec3.fromBytes(nin.readBytes(12))
        normal *= parentBoneMatrix
        normal.normalize()
        out.writeBytes(normal.toBytes())
    return out.getBuffer()
    
def getNormal(normalData):
    nin = NoeBitStream(normalData)
    out = NoeBitStream()
    numVerts = len(normalData) // 3
    for i in range(numVerts):
        nx = nin.readByte() / 128.0
        ny = nin.readByte() / 128.0
        nz = nin.readByte() / 128.0
        out.writeFloat(nx)
        out.writeFloat(ny)
        out.writeFloat(nz)        
    return out.getBuffer()

class decodeVTypePSP(object):
    def __init__(self,VTYPE:int):
        self.UVFormat = VTYPE & 3
        self.ColorFormat = (VTYPE >> 2) & 7 
        self.NormalFormat = (VTYPE >> 5) & 3
        self.PositionFormat = (VTYPE >> 7) & 3
        self.WeightFormat = (VTYPE >> 9) & 3
        self.IndexFormat = (VTYPE >> 11) & 3
        self.numWeights = ((VTYPE >> 14) & 7) + 1 # Number of weights (Skinning)
        self.numVertices =((VTYPE >> 18) & 7) + 1 # Number of vertices (Morphing)
        self.coordType = (VTYPE >> 23) & 1 # Bypass Transform Pipeline. 1 -Transformed Coordinates . 0-Raw Coordinates.
        

class rMKPSPNativeDataPLG(object):
    def __init__(self,bs:NoeBitStream,matList,binMeshPLG:rBinMeshPLG,vertMat,skinFlag,hSkinBoneIDList,sphereXYZ,skin):
        #self.bs = NoeBitStream(natvieDatas)
        self.bs = bs
        self.matList = matList
        self.matIdList = binMeshPLG.matIdList
        self.matIdNumFaceList = binMeshPLG.matIdNumFaceList
        self.vertMat = vertMat  
        self.skinFlag = skinFlag
        self.hSkinBoneIDList = hSkinBoneIDList
        self.posOffset = sphereXYZ
        self.skin = skin
    def readMesh(self):    
        nativeHeader = rwChunk(self.bs)
        endOfs = self.bs.tell() + nativeHeader.chunkSize

        platformID = self.bs.readInt()
        curOfs = self.bs.tell()
        padLen = 0
        if (curOfs - 24) % 16:
            padLen = 16 - ((curOfs - 24) % 16)
        self.bs.seek(padLen,NOESEEK_REL)


        baseOffset = self.bs.tell()
        chunkSize = self.bs.readInt()
        numStrip = self.bs.readShort()
        splitCount = self.bs.readShort()
        #splitCount = len(self.matIdList)



        self.bs.seek(splitCount * 32,NOESEEK_REL) # skip first list
        self.bs.seek(16,NOESEEK_REL)    # skip 4 ints


        for i in range(splitCount):
            
            self.bs.seek(16,NOESEEK_REL)
            format = self.bs.readInt()
            unk = self.bs.readInt()
            numIndices = self.bs.readInt()
            offset = self.bs.readInt()
            self.bs.seek(16,NOESEEK_REL)
            infoOffset = self.bs.readInt()
            stride = self.bs.readInt()
            matrixOffset = self.bs.readInt()
            unk = self.bs.readInt()


            nextOfs = self.bs.tell()
            self.bs.seek(baseOffset + matrixOffset)
            #scaleMatrix = NoeMat44.fromBytes(self.bs.readBytes(64)).toMat43()
            scaleMatrix = struct.unpack('16f',self.bs.readBytes(64))
            
            vertFormat = decodeVTypePSP(format)
            self.bs.seek(baseOffset + offset)
            
            vertBuffer = bytes()
            normalBuffer = bytes()
            uvBuffer = bytes()
            boneIDBuffer = bytes()
            weightBuffer = bytes()
            colorBuffer = bytes()
            
            for v in range(numIndices):
                for w in range(vertFormat.numWeights):
                    if vertFormat.WeightFormat == 1:
                        weight = self.bs.readUByte()
                        if weight == 128:
                            weight = 1.0
                        elif weight < 127:
                            weight /= 127.0
                        weightBuffer += struct.pack('f',weight)
                        
                        if weight != 0.0:
                            boneIDBuffer += struct.pack('B',self.hSkinBoneIDList[self.skin.pspBonePalettes[i][w]] )                               
                        else:
                            boneIDBuffer += struct.pack('B',0)


                if vertFormat.UVFormat == 1:
                    tu = self.bs.readByte() / 127.0
                    tv = self.bs.readByte() / 127.0
                    uvBuffer += struct.pack('2f',tu,tv)
                if vertFormat.ColorFormat > 3:
                    if vertFormat.ColorFormat == 6:
                        color = self.bs.readShort()
                        cr = (color << 4) & 0xF0
                        cg = (color & 0xF0)
                        cb = (color >> 4 ) & 0xF0
                        ca = (color >> 8 ) & 0xF0                        
                        colorBuffer += struct.pack('4B',cr,cg,cb,ca)
                if vertFormat.NormalFormat == 1:
                    nx = self.bs.readByte() / 127.0
                    ny = self.bs.readByte() / 127.0
                    nz = self.bs.readByte() / 127.0
                    normalBuffer += struct.pack('3f',nx,ny,nz)
                if vertFormat.PositionFormat == 1:
                    x = self.bs.readByte()
                    y = self.bs.readByte()
                    z = self.bs.readByte()
                    vx = ( x / 127.0) * scaleMatrix[0] + self.posOffset.vec3[0]
                    vy = ( y / 127.0) * scaleMatrix[5] + self.posOffset.vec3[1]
                    vz = ( z / 127.0) * scaleMatrix[10] + self.posOffset.vec3[2]

                    vertBuffer += struct.pack('3f',vx,vy,vz)
                elif vertFormat.PositionFormat == 2:
                    x = self.bs.readShort()
                    y = self.bs.readShort()
                    z = self.bs.readShort()
                    vx = ( x / 32767.0) * scaleMatrix[0] + self.posOffset.vec3[0]
                    vy = ( y / 32767.0) * scaleMatrix[5] + self.posOffset.vec3[1]
                    vz = ( z / 32767.0) * scaleMatrix[10] + self.posOffset.vec3[2]
                    vertBuffer += struct.pack('3f',vx,vy,vz)
            faceBuffer = getTriangleList(vertBuffer,1)
            #vertBuffer = getTransformVertex(vertBuffer,scaleMatrix)

            if self.skinFlag and len(self.skin.pspBonePalettes):
                rapi.rpgBindBoneIndexBuffer(boneIDBuffer, noesis.RPGEODATA_UBYTE, vertFormat.numWeights, vertFormat.numWeights)
                rapi.rpgBindBoneWeightBuffer(weightBuffer, noesis.RPGEODATA_FLOAT, vertFormat.numWeights * 4, vertFormat.numWeights) 
            else:
                vertBuffer = getTransformVertex(vertBuffer,self.vertMat)
            rapi.rpgBindPositionBuffer(vertBuffer, noesis.RPGEODATA_FLOAT, 12) 
            if vertFormat.NormalFormat > 0:
                rapi.rpgBindNormalBuffer(normalBuffer, noesis.RPGEODATA_FLOAT, 12)
            if vertFormat.UVFormat > 0:
                rapi.rpgBindUV1Buffer(uvBuffer, noesis.RPGEODATA_FLOAT, 8)  
            if vertFormat.ColorFormat > 3:
                rapi.rpgBindColorBuffer(colorBuffer, noesis.RPGEODATA_UBYTE, 4, 4)   

            
            matID = self.matIdList[i]
            matName = self.matList[matID].name
            rapi.rpgSetMaterial(matName)     
            '''        
            matName = "mtl" + str(i)
            rapi.rpgSetName(matName)
            rapi.rpgSetMaterial(matName)  
            '''          
            rapi.rpgCommitTriangles(faceBuffer, noesis.RPGEODATA_INT, len(faceBuffer)//4, noesis.RPGEO_TRIANGLE, 1)
            rapi.rpgClearBufferBinds()
            
            
            self.bs.seek(nextOfs)
        self.bs.seek(endOfs)

class rGeomtry(object):
    def __init__(self,bs:NoeBitStream,vertMat,hSkinBoneIDList):
        #self.bs = NoeBitStream(datas)
        self.bs = bs
        self.vertMat = vertMat
        self.matList = []
        self.hSkinBoneIDList = hSkinBoneIDList
    def rGeometryStruct(self):
        geoStruct = rwChunk(self.bs)
        FormatFlags = self.bs.readUShort()
        numUV = self.bs.readByte()
        nativeFlags = self.bs.readByte()
        numFace = self.bs.readUInt()
        numVert = self.bs.readUInt()
        numMorphTargets = self.bs.readUInt()
        Tristrip = FormatFlags % 2
        Meshes = (FormatFlags & 3) >> 1
        Textured = (FormatFlags & 7) >> 2
        Prelit = (FormatFlags & 0xF) >> 3
        Normals = (FormatFlags & 0x1F) >> 4
        Light = (FormatFlags & 0x3F) >> 5
        ModulateMaterialColor = (FormatFlags & 0x7F) >> 6
        Textured_2 = (FormatFlags & 0xFF) >> 7
        MKSkinFlag = (FormatFlags & 0x100) == 0x100
        MtlIDList = []
        faceBuff = bytes()
        if nativeFlags != 1:
            if geoStruct.version < 0x34000:
                self.bs.seek(12,NOESEEK_REL) #skip surfaceProperties
            if Prelit == 1:
                self.bs.seek(numVert*4,1)
            if Textured == 1:
                uvs = self.bs.readBytes(numVert * 8)
                rapi.rpgBindUV1Buffer(uvs, noesis.RPGEODATA_FLOAT, 8)
            if Textured_2 == 1:
                uvs = self.bs.readBytes(numVert * 8)
                self.bs.seek(numVert*8,1)
                rapi.rpgBindUV1Buffer(uvs, noesis.RPGEODATA_FLOAT, 8)
            if Meshes == 1:
                for i in range(numFace):
                    f1 = self.bs.readBytes(2)
                    f2 = self.bs.readBytes(2)
                    f3 = self.bs.readBytes(2)
                    MtlIDList.append(self.bs.readUShort())
                    faceBuff+=f1
                    faceBuff+=f2
                    faceBuff+=f3
        for m in range(numMorphTargets):
            vertBuff = bytes()
            normBuff = bytes()
            sphereXYZ = NoeVec3.fromBytes(self.bs.readBytes(12))
            sphereRadius = self.bs.readFloat()
            positionFlag = self.bs.readUInt()
            normalFlag = self.bs.readUInt()
            if nativeFlags != 1:
                if positionFlag == 1:
                    # strout = "current offset:0x%x" % self.bs.tell()
                    # print(strout)
                    if geoStruct.version >= 0x34000:
                        pad16Len1 = ((self.bs.tell() + 15) & 0xFFFFFFF0) - self.bs.tell()
                        padl6Len2 = 16 - pad16Len1
                        self.bs.seek(pad16Len1, NOESEEK_REL)
                    for i in range(numVert):
                        vert = NoeVec3.fromBytes(self.bs.readBytes(12))
                        vert *= self.vertMat
                        vertBuff+=vert.toBytes()
                    if m == 0:
                        # print("Commit vertex")
                        rapi.rpgBindPositionBuffer(vertBuff, noesis.RPGEODATA_FLOAT, 12)
                    else:
                        rapi.rpgFeedMorphTargetPositions(vertBuff, noesis.RPGEODATA_FLOAT, 12)

                    if geoStruct.version >= 0x34000:self.bs.seek(padl6Len2, NOESEEK_REL)
                if normalFlag == 1:
                    if geoStruct.version >= 0x34000:
                        pad16Len1 = ((self.bs.tell() + 15) & 0xFFFFFFF0) - self.bs.tell()
                        padl6Len2 = 16 - pad16Len1
                        self.bs.seek(pad16Len1, NOESEEK_REL)
                    for i in range(numVert):
                        normal = NoeVec3.fromBytes(self.bs.readBytes(12))
                        normal *= self.vertMat
                        normBuff+=normal.toBytes()
                    if m == 0:
                        # print("Commit normal")
                        rapi.rpgBindNormalBuffer(normBuff, noesis.RPGEODATA_FLOAT, 12)
                    else:
                        rapi.rpgFeedMorphTargetNormals(normBuff, noesis.RPGEODATA_FLOAT, 12)
                    if geoStruct.version >= 0x34000:self.bs.seek(padl6Len2, NOESEEK_REL)
                if positionFlag and m > 0:
                    rapi.rpgCommitMorphFrame(numVert)
        if numMorphTargets:
            rapi.rpgCommitMorphFrameSet()

        matrialListHeader = rwChunk(self.bs)
        matDatas = self.bs.readBytes(matrialListHeader.chunkSize)
        rMatList = rMaterialList(matDatas)
        #rMatList = rMaterialList(self.bs)
        rMatList.getMaterial()
        matList = rMatList.matList
        texList = rMatList.texList
        for m in range(len(matList)):
            self.matList.append(matList[m])
        geoExtHeader = rwChunk(self.bs)
        geoExtEndOfs = self.bs.tell()+geoExtHeader.chunkSize

        haveSkin = 0
        haveBinMesh = 0
        while self.bs.tell()<geoExtEndOfs:
            header = rwChunk(self.bs)
            if header.chunkID == 0x50e:
                haveBinMesh = 1
                binMeshDatas = self.bs.readBytes(header.chunkSize)
            elif header.chunkID == 0x116:
                haveSkin = 1
                skinDatas = self.bs.readBytes(header.chunkSize)
            else:
                self.bs.seek(header.chunkSize,1)
        if haveSkin:
            skin = rSkin(skinDatas,numVert,nativeFlags,geoStruct.version,rMatList)
            skin.readSkin()
        if haveBinMesh:
            binMeshPLG = rBinMeshPLG(binMeshDatas,matList,nativeFlags)
            binMeshPLG.readFace()
        if haveSkin and nativeFlags == 0:
            # MKDA PS2
            if geoStruct.version < 0x34000 and skin.maxNumWeights == 0:
                newBids = bytes()
                for w in range(numVert):
                    weights = struct.unpack('4f',skin.boneWeights[w*16:w*16+16] )
                    b1,b2,b3,b4=(0,0,0,0)
                    if weights[0] > 0:
                        b1 = struct.unpack('B',skin.boneIndexs[w*4:w*4+1])[0]
                        b1 = skin.usedBoneIndexList[b1]
                    if weights[1] > 0:
                        b2 = struct.unpack('B',skin.boneIndexs[w*4+1:w*4+2])[0]
                        b2 = skin.usedBoneIndexList[b2]
                    if weights[2] > 0:
                        b3 = struct.unpack('B',skin.boneIndexs[w*4+2:w*4+3])[0]
                        b3 = skin.usedBoneIndexList[b3]
                    if weights[3] > 0:
                        b4 = struct.unpack('B',skin.boneIndexs[w*4+3:w*4+4])[0]
                        b4 = skin.usedBoneIndexList[b4]
                    newBids += noePack("4B",b1,b2,b3,b4)
                rapi.rpgBindBoneIndexBuffer(newBids, noesis.RPGEODATA_UBYTE, 4 , 4)
                rapi.rpgBindBoneWeightBuffer(skin.boneWeights, noesis.RPGEODATA_FLOAT, 16, 4)
            # MKA Morph targets
            elif haveBinMesh and rMatList.useBonePalette:
                vertMatIDs = [0] * numVert
                for vertID,matID in zip(binMeshPLG.faceIndices,binMeshPLG.indicesMatIDs):
                    vertMatIDs[vertID] = matID
                # print(vertMatIDs)
                newBids = bytes()
                for w in range(numVert):
                    weights = struct.unpack('4f',skin.boneWeights[w*16:w*16+16] )
                    matID = vertMatIDs[w]
                    b1,b2,b3,b4=(0,0,0,0)
                    if weights[0] > 0:
                        b1 = struct.unpack('B',skin.boneIndexs[w*4:w*4+1])[0]
                        b1 = rMatList.MKMaterialSkinBonePalette[matID][b1]
                    if weights[1] > 0:
                        b2 = struct.unpack('B',skin.boneIndexs[w*4+1:w*4+2])[0]
                        b2 = rMatList.MKMaterialSkinBonePalette[matID][b2]
                    if weights[2] > 0:
                        b3 = struct.unpack('B',skin.boneIndexs[w*4+2:w*4+3])[0]
                        b3 = rMatList.MKMaterialSkinBonePalette[matID][b3]
                    if weights[3] > 0:
                        b4 = struct.unpack('B',skin.boneIndexs[w*4+3:w*4+4])[0]
                        b4 = rMatList.MKMaterialSkinBonePalette[matID][b4]
                    newBids += noePack("4B",b1,b2,b3,b4)
                rapi.rpgBindBoneIndexBuffer(newBids, noesis.RPGEODATA_UBYTE, 4 , 4)
                rapi.rpgBindBoneWeightBuffer(skin.boneWeights, noesis.RPGEODATA_FLOAT, 16, 4)
        if haveBinMesh and nativeFlags == 0:
            for i in range(binMeshPLG.numSplitMatID):
                matID = binMeshPLG.matIdList[i]
                numFaceIndices = binMeshPLG.matIdNumFaceList[i]
                tristrips = binMeshPLG.faceStrips[i]
                matName = self.matList[matID].name
                if binMeshPLG.faceType == 1:
                    rapi.rpgSetMaterial(matName)
                    rapi.rpgCommitTriangles(tristrips, noesis.RPGEODATA_UINT, \
                                            numFaceIndices, noesis.RPGEO_TRIANGLE_STRIP, 1)
        if nativeFlags == 1 and geoStruct.chunkSize > 40:
            if isMKPS2:
                splitCount = len(binMeshPLG.matIdList)
                nativeChunkStartOffset = self.bs.tell()
                nativeChunkSize = 0
                for i in range(splitCount):
                    dataSize = self.bs.readUInt()
                    meshType = self.bs.readUInt()
                    endOfs = self.bs.tell() + dataSize
                    self.bs.seek(endOfs)
                    nativeChunkSize += (dataSize + 8)
                skinPlgBoneMap = []
                if MKSkinFlag:
                    skinDataSize = geoStruct.chunkSize - 40 - nativeChunkSize
                    skinDatas = self.bs.readBytes(skinDataSize)
                    skin = rSkin(skinDatas,numVert,nativeFlags,geoStruct.version,rMatList)
                    skin.readSkin()
                    skinPlgBoneMap = skin.usedBoneIndexList
                skinPlgEndOffset = self.bs.tell()
                self.bs.seek(nativeChunkStartOffset)                        
                #natvieDatas = self.bs.readBytes(nativeChunkSize)      
                MKPS2NativeDataPLG = rMKPS2NativeDataPLG(self.bs,matList,\
                    binMeshPLG,self.vertMat,rMatList.MKMaterialSkinBonePalette,\
                    MKSkinFlag,self.hSkinBoneIDList,rMatList.useBonePalette,\
                    skinPlgBoneMap,rMatList.MKMaterialList)
                MKPS2NativeDataPLG.readMesh()
                self.bs.seek(skinPlgEndOffset)


            if isMKPSP:
                baseOffset = self.bs.tell()
                nativeHeader = rwChunk(self.bs)
                self.bs.seek(nativeHeader.chunkSize,NOESEEK_REL)
                #natvieDatas = self.bs.readBytes(nativeHeader.chunkSize)
                baseOffset2 = self.bs.tell()
                if MKSkinFlag:
                    skinHeader = rwChunk(self.bs)
                    self.bs.seek(-12,NOESEEK_REL)
                    skinDatas = self.bs.readBytes(skinHeader.chunkSize + 12)
                    skin = rSkin(skinDatas,numVert,nativeFlags,geoStruct.version,matList)
                    skin.readSkin()
                    baseOffset2 = self.bs.tell()
                else:
                    skin = -1
                self.bs.seek(baseOffset)
                MKPSPNativeDataPLG = rMKPSPNativeDataPLG(self.bs,matList,\
                    binMeshPLG,self.vertMat,MKSkinFlag,self.hSkinBoneIDList,sphereXYZ,skin)
                MKPSPNativeDataPLG.readMesh()
                self.bs.seek(baseOffset2)
        # print("Commit face")
        # rapi.rpgCommitTriangles(faceBuff, \
        #    noesis.RPGEODATA_USHORT, (numFace * 3), noesis.RPGEO_TRIANGLE, 1)
        rapi.rpgClearBufferBinds()

from math import degrees, radians, pi, ceil, floor
import numpy as np
import threading
from time import sleep, perf_counter as Tcounter
from queue import Queue

# Blender Imports :
import bpy
import mathutils
from mathutils import Matrix, Vector, Euler, kdtree

import SimpleITK as sitk

# Global Variables :

#######################################################################################
# Popup message box function :
#######################################################################################


def ShowMessageBox(message=[], title="INFO", icon="INFO"):
    def draw(self, context):
        for txtLine in message:
            self.layout.label(text=txtLine)

    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)


##############################################################
# Align utils :
##############################################################
def MoveToCollection(obj, CollName):

    OldColl = obj.users_collection  # list of all collection the obj is in
    NewColl = bpy.data.collections.get(CollName)
    if not NewColl:
        NewColl = bpy.data.collections.new(CollName)
        bpy.context.scene.collection.children.link(NewColl)
    if not obj in NewColl.objects[:]:
        NewColl.objects.link(obj)  # link obj to scene
    if OldColl:
        for Coll in OldColl:  # unlink from all  precedent obj collections
            if Coll is not NewColl:
                Coll.objects.unlink(obj)


def AddRefPoint(name, color, CollName=None):

    loc = bpy.context.scene.cursor.location
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1.2, location=loc)
    RefP = bpy.context.object
    RefP.name = name
    RefP.data.name = name + "_mesh"
    if CollName:
        MoveToCollection(RefP, CollName)
    if name.startswith("B"):
        matName = "TargetRefMat"
    if name.startswith("M"):
        matName = "SourceRefMat"

    mat = bpy.data.materials.get(matName) or bpy.data.materials.new(matName)
    mat.use_nodes = False
    mat.diffuse_color = color
    RefP.active_material = mat
    RefP.show_name = True
    return RefP


def RefPointsToTransformMatrix(TargetRefPoints, SourceRefPoints):
    # TransformMatrix = Matrix()  # identity Matrix (4x4)

    # make 2 arrays of coordinates :
    TargetArray = np.array(
        [obj.location for obj in TargetRefPoints], dtype=np.float64
    ).T
    SourceArray = np.array(
        [obj.location for obj in SourceRefPoints], dtype=np.float64
    ).T

    # Calculate centers of Target and Source RefPoints :
    TargetCenter, SourceCenter = np.mean(TargetArray, axis=1), np.mean(
        SourceArray, axis=1
    )

    # Calculate Translation :
    ###################################

    # TransMatrix_1 : Matrix(4x4) will translate center of SourceRefPoints...
    # to origine (0,0,0) location.
    TransMatrix_1 = Matrix.Translation(Vector(-SourceCenter))

    # TransMatrix_2 : Matrix(4x4) will translate center of SourceRefPoints...
    #  to the center of TargetRefPoints location.
    TransMatrix_2 = Matrix.Translation(Vector(TargetCenter))

    # Calculate Rotation :
    ###################################

    # Home Arrays will get the Centered Target and Source RefPoints around origin (0,0,0).
    HomeTargetArray, HomeSourceArray = (
        TargetArray - TargetCenter.reshape(3, 1),
        SourceArray - SourceCenter.reshape(3, 1),
    )
    # Rigid transformation via SVD of covariance matrix :
    U, S, Vt = np.linalg.svd(np.dot(HomeTargetArray, HomeSourceArray.T))

    # rotation matrix from SVD orthonormal bases and check,
    # if it is a Reflection matrix :
    R = np.dot(U, Vt)
    if np.linalg.det(R) < 0.0:
        Vt[2, :] *= -1
        R = np.dot(U, Vt)
        print(" Reflection matrix fixed ")

    RotationMatrix = Matrix(R).to_4x4()
    TransformMatrix = TransMatrix_2 @ RotationMatrix @ TransMatrix_1

    return TransformMatrix


def KdIcpPairs(SourceVcoList, TargetVcolist, VertsLimite=5000):
    start = Tcounter()
    # print("KD processing start...")
    SourceKdList, TargetKdList, DistList, SourceIndexList, TargetIndexList = (
        [],
        [],
        [],
        [],
        [],
    )
    size = len(TargetVcolist)
    kd = kdtree.KDTree(size)

    for i, Vco in enumerate(TargetVcolist):
        kd.insert(Vco, i)

    kd.balance()

    n = len(SourceVcoList)
    if n > VertsLimite:
        step = ceil(n / VertsLimite)
        SourceVcoList = SourceVcoList[::step]

    for SourceIndex, Sco in enumerate(SourceVcoList):

        Tco, TargetIndex, dist = kd.find(Sco)
        if Tco:
            if not TargetIndex in TargetIndexList:
                TargetIndexList.append(TargetIndex)
                SourceIndexList.append(SourceIndex)
                TargetKdList.append(Tco)
                SourceKdList.append(Sco)
                DistList.append(dist)
    finish = Tcounter()
    # print(f"KD total iterations : {len(SourceVcoList)}")
    # print(f"KD Index List : {len(IndexList)}")

    # print(f"KD finshed in {finish-start} secondes")
    return SourceKdList, TargetKdList, DistList, SourceIndexList, TargetIndexList


def KdRadiusVerts(obj, RefCo, radius):

    RadiusVertsIds = []
    RadiusVertsCo = []
    RadiusVertsDistance = []
    verts = obj.data.vertices
    Vcolist = [obj.matrix_world @ v.co for v in verts]
    size = len(Vcolist)
    kd = kdtree.KDTree(size)

    for i, Vco in enumerate(Vcolist):
        kd.insert(Vco, i)

    kd.balance()

    for (co, index, dist) in kd.find_range(RefCo, radius):

        RadiusVertsIds.append(index)
        RadiusVertsCo.append(co)
        RadiusVertsDistance.append(dist)

    return RadiusVertsIds, RadiusVertsCo, RadiusVertsDistance


def VidDictFromPoints(TargetRefPoints, SourceRefPoints, TargetObj, SourceObj, radius):
    IcpVidDict = {TargetObj: [], SourceObj: []}

    for obj in [TargetObj, SourceObj]:
        if obj == TargetObj:
            for RefTargetP in TargetRefPoints:
                RefCo = RefTargetP.location
                RadiusVertsIds, RadiusVertsCo, RadiusVertsDistance = KdRadiusVerts(
                    TargetObj, RefCo, radius
                )
                IcpVidDict[TargetObj].extend(RadiusVertsIds)
                for idx in RadiusVertsIds:
                    obj.data.vertices[idx].select = True
        if obj == SourceObj:
            for RefSourceP in SourceRefPoints:
                RefCo = RefSourceP.location
                RadiusVertsIds, RadiusVertsCo, RadiusVertsDistance = KdRadiusVerts(
                    SourceObj, RefCo, radius
                )
                IcpVidDict[SourceObj].extend(RadiusVertsIds)
                for idx in RadiusVertsIds:
                    obj.data.vertices[idx].select = True

    bpy.ops.object.select_all(action="DESELECT")
    for obj in [TargetObj, SourceObj]:
        obj.select_set(True)
        bpy.context.view_layer.objects.active = TargetObj

    return IcpVidDict


def KdIcpPairsToTransformMatrix(TargetKdList, SourceKdList):
    # make 2 arrays of coordinates :
    TargetArray = np.array(TargetKdList, dtype=np.float64).T
    SourceArray = np.array(SourceKdList, dtype=np.float64).T

    # Calculate centers of Target and Source RefPoints :
    TargetCenter, SourceCenter = np.mean(TargetArray, axis=1), np.mean(
        SourceArray, axis=1
    )

    # Calculate Translation :
    ###################################

    # TransMatrix_1 : Matrix(4x4) will translate center of SourceRefPoints...
    # to origine (0,0,0) location.
    TransMatrix_1 = Matrix.Translation(Vector(-SourceCenter))

    # TransMatrix_2 : Matrix(4x4) will translate center of SourceRefPoints...
    #  to the center of TargetRefPoints location.
    TransMatrix_2 = Matrix.Translation(Vector(TargetCenter))

    # Calculate Rotation :
    ###################################

    # Home Arrays will get the Centered Target and Source RefPoints around origin (0,0,0).
    HomeTargetArray, HomeSourceArray = (
        TargetArray - TargetCenter.reshape(3, 1),
        SourceArray - SourceCenter.reshape(3, 1),
    )
    # Rigid transformation via SVD of covariance matrix :
    U, S, Vt = np.linalg.svd(np.dot(HomeTargetArray, HomeSourceArray.T))

    # rotation matrix from SVD orthonormal bases :
    R = np.dot(U, Vt)
    if np.linalg.det(R) < 0.0:
        Vt[2, :] *= -1
        R = np.dot(U, Vt)
        print(" Reflection fixed ")

    RotationMatrix = Matrix(R).to_4x4()
    TransformMatrix = TransMatrix_2 @ RotationMatrix @ TransMatrix_1

    return TransformMatrix

def CtxOverride(context):
    Override = context.copy()
    area3D = [area for area in context.screen.areas if area.type == "VIEW_3D"][0]
    space3D = [space for space in area3D.spaces if space.type == "VIEW_3D"][0]
    region3D = [reg for reg in area3D.regions if reg.type == "WINDOW"][0]
    Override["area"], Override["space_data"], Override["region"] = (
        area3D,
        space3D,
        region3D,
    )
    return Override, area3D, space3D 

def AddVoxelPoint(Name="Voxel Anatomical Point", Color=(1.0,0.0,0.0,1.0), Location=(0,0,0), Radius=1.2):
    Active_Obj = bpy.context.view_layer.objects.active
    bpy.ops.mesh.primitive_uv_sphere_add(radius=Radius, location=Location)
    Sphere = bpy.context.object
    Sphere.name = Name
    Sphere.data.name = Name


    MoveToCollection(Sphere, "VOXELS Points")

    matName = f"VOXEL_Points_Mat"
    mat = bpy.data.materials.get(matName) or bpy.data.materials.new(matName)
    mat.diffuse_color = Color
    mat.use_nodes = False
    Sphere.active_material = mat
    Sphere.show_name = True
    bpy.ops.object.select_all(action='DESELECT')
    Active_Obj.select_set(True)
    bpy.context.view_layer.objects.active = Active_Obj
    
def MoveToCollection(obj, CollName):

    OldColl = obj.users_collection  # list of all collection the obj is in
    NewColl = bpy.data.collections.get(CollName)
    if not NewColl:
        NewColl = bpy.data.collections.new(CollName)
        bpy.context.scene.collection.children.link(NewColl)
    if not obj in NewColl.objects[:]:
        NewColl.objects.link(obj)  # link obj to scene
    if OldColl:
        for Coll in OldColl:  # unlink from all  precedent obj collections
            if Coll is not NewColl:
                Coll.objects.unlink(obj)
                
    
def CursorToVoxelPoint(Preffix, CursorMove=False):

    VoxelPointCo = 0
         
    BDENTAL_Props = bpy.context.scene.BDENTAL_Props
    DcmInfoDict = eval(BDENTAL_Props.DcmInfo)
    DcmInfo = DcmInfoDict[Preffix]
    ImageData = bpy.path.abspath(DcmInfo["Nrrd255Path"])
    Treshold=BDENTAL_Props.Treshold
    Wmin, Wmax = DcmInfo['Wmin'], DcmInfo['Wmax']
    TransformMatrix = DcmInfo["TransformMatrix"]
    VtkTransform_4x4 = DcmInfo["VtkTransform_4x4"]
    
    Cursor = bpy.context.scene.cursor
    CursorInitMtx = Cursor.matrix.copy()
    
    
    # Get ImageData Infos :
    Image3D_255 = sitk.ReadImage(ImageData)
    Sp = Spacing = Image3D_255.GetSpacing()
    Sz = Size = Image3D_255.GetSize()
    Ortho_Origin = -0.5 * np.array(Sp) * (np.array(Sz) - np.array((1, 1, 1)))
    Image3D_255.SetOrigin(Ortho_Origin)
    Image3D_255.SetDirection(np.identity(3).flatten())
    
    
    #Cursor shift :
    Cursor_Z = Vector((CursorInitMtx[0][2], CursorInitMtx[1][2], CursorInitMtx[2][2]))
    CT = CursorTrans = -1*(Sz[2]-1)*Sp[2] * Cursor_Z
    CursorTransMatrix = mathutils.Matrix(
    (
        (1.0, 0.0, 0.0, CT[0]),
        (0.0, 1.0, 0.0, CT[1]),
        (0.0, 0.0, 1.0, CT[2]),
        (0.0, 0.0, 0.0, 1.0),
    )
    )
    
    
    # Output Parameters :
    Out_Origin = [Ortho_Origin[0], Ortho_Origin[1], 0]
    Out_Direction = Vector(np.identity(3).flatten())
    Out_Size = Sz
    Out_Spacing = Sp
    
    # Get Plane Orientation and location :
    Matrix =  TransformMatrix.inverted() @ CursorTransMatrix @ CursorInitMtx
    Rot = Matrix.to_euler()
    Rvec = (Rot.x, Rot.y, Rot.z)
    Tvec = Matrix.translation

    # Euler3DTransform :
    Euler3D = sitk.Euler3DTransform()
    Euler3D.SetCenter((0, 0, 0))
    Euler3D.SetRotation(Rvec[0], Rvec[1], Rvec[2])
    Euler3D.SetTranslation(Tvec)
    Euler3D.ComputeZYXOn()
    
    #########################################

    Image3D = sitk.Resample(
        Image3D_255,
        Out_Size,
        Euler3D,
        sitk.sitkLinear,
        Out_Origin,
        Out_Spacing,
        Out_Direction,
        0,
    )
    
    
    
    #  # Write Image :
    # Array = sitk.GetArrayFromImage(Image3D[:,:,Sz[2]-1])#Sz[2]-1
    # Flipped_Array = np.flipud(Array.reshape(Array.shape[0], Array.shape[1]))
    # cv2.imwrite(ImagePath, Flipped_Array)
    
    ImgArray = sitk.GetArrayFromImage(Image3D)
    Treshold255 = int(((Treshold -Wmin) / (Wmax-Wmin)) * 255)
    
    RayPixels = ImgArray[:,int(Sz[1]/2),int(Sz[0]/2)]
    ReversedRayPixels = list(reversed(list(RayPixels)))
    
    for i,P in enumerate(ReversedRayPixels) :
        if P >= Treshold255:
            VoxelPointCo = Cursor.location - i*Sp[2]*Cursor_Z
            break
    
    if CursorMove and VoxelPointCo :
        bpy.context.scene.cursor.location = VoxelPointCo
    #############################################
    
    return(VoxelPointCo)

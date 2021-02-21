from math import degrees, radians, pi, ceil, floor
import numpy as np
import threading
from time import sleep, perf_counter as Tcounter
from queue import Queue

# Blender Imports :
import bpy
from mathutils import Matrix, Vector, Euler, kdtree

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
    mat.diffuse_color = color
    mat.use_nodes = True
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

def AdjustRefPoints(TargetRefPoints, SourceRefPoints):

    for i in range(len(TargetRefPoints)):

        SP = SourceRefPoints[i]
        TP = TargetRefPoints[i]

        Mid_Location = (SP.location + TP.location)/2
        SP.location = TP.location = Mid_Location

        SP.update_tag()
        TP.update_tag()
                
    bpy.context.view_layer.update()


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
            # if not TargetIndex in TargetIndexList:
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
    # IcpVidDict = {TargetObj: [], SourceObj: []}
    IcpVidDict = {TargetObj: {}, SourceObj: {}}


    for obj in [TargetObj, SourceObj]:
        if obj == TargetObj:
            for i, RefTargetP in enumerate(TargetRefPoints):
                RefCo = RefTargetP.location
                RadiusVertsIds, RadiusVertsCo, RadiusVertsDistance = KdRadiusVerts(
                    TargetObj, RefCo, radius
                )
                IcpVidDict[TargetObj][i] = RadiusVertsIds
                # [ IcpVidDict[TargetObj].append(idx) for idx in RadiusVertsIds if not idx in IcpVidDict[TargetObj] ]
                # IcpVidDict[TargetObj].extend(RadiusVertsIds)
                for idx in RadiusVertsIds:
                    obj.data.vertices[idx].select = True
        if obj == SourceObj:
            for i, RefSourceP in enumerate(SourceRefPoints):
                RefCo = RefSourceP.location
                RadiusVertsIds, RadiusVertsCo, RadiusVertsDistance = KdRadiusVerts(
                    SourceObj, RefCo, radius
                )

                IcpVidDict[SourceObj][i] = RadiusVertsIds

                # [ IcpVidDict[SourceObj].append(idx) for idx in RadiusVertsIds if not idx in IcpVidDict[SourceObj] ]

                # IcpVidDict[SourceObj].extend(RadiusVertsIds)
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

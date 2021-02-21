from math import degrees, radians, pi, ceil, floor
import numpy as np
import threading
from time import sleep, perf_counter as Tcounter
from queue import Queue

# Blender Imports :
import bpy
from mathutils import Matrix, Vector, Euler, kdtree

# Global Variables :

from .BDENTAL_ALIGN_Utils import *

############################################################################
class BDENTAL_ALIGN_OT_AlignPoints(bpy.types.Operator):
    """ Add Align Refference points """

    bl_idname = "bdental_align.alignpoints"
    bl_label = "ALIGN POINTS"
    bl_options = {"REGISTER", "UNDO"}

    TargetColor = (0, 1, 0, 1)  # Green
    SourceColor = (1, 0, 0, 1)  # Red
    CollName = "ALIGN POINTS"
    TargetChar = "B"
    SourceChar = "A"

    def IcpPipline(
        self,
        context,
        SourceObj,
        TargetObj,
        SourceVidDict,
        TargetVidDict,
        VertsLimite,
        Iterations,
        Precision,
    ):

        MaxDist = 0.0
        for i in range(Iterations):

            SourceKdList, TargetKdList, DistList = [], [], []

            for n in range(len(self.SourceRefPoints)) :

                SourceVcoList = [
                    SourceObj.matrix_world @ SourceObj.data.vertices[idx].co
                    for idx in SourceVidDict[n]
                ]
                TargetVcoList = [
                    TargetObj.matrix_world @ TargetObj.data.vertices[idx].co
                    for idx in TargetVidDict[n]
                ]

                (
                    RefSourceKdList,
                    RefTargetKdList,
                    RefDistList,
                    SourceIndexList,
                    TargetIndexList,
                ) = KdIcpPairs(SourceVcoList, TargetVcoList, VertsLimite=VertsLimite)

                SourceKdList.extend(RefSourceKdList)
                TargetKdList.extend(RefTargetKdList)
                DistList.extend(RefDistList)

            MeanDist = np.mean(DistList)
            print(f"Number of iterations = {i}")
            print(f"Mean Distance = {round(MeanDist, 6)} mm")

            if MeanDist <= Precision:
                self.ResultMessage = [
                    "Allignement Done !",
                    f"Mean Distance < or = {Precision} mm",
                ]
                
                print(f"Precision of {Precision} mm reached.")
                break

            if MeanDist > Precision:
                
                TransformMatrix = KdIcpPairsToTransformMatrix(
                    TargetKdList=TargetKdList, SourceKdList=SourceKdList
                )
                SourceObj.matrix_world = TransformMatrix @ SourceObj.matrix_world

                for RefP in self.SourceRefPoints :
                    RefP.matrix_world = TransformMatrix @ RefP.matrix_world
                # Update scene :
                SourceObj.update_tag()
                bpy.context.view_layer.update()
                
                # bpy.ops.wm.redraw_timer(context, type='DRAW_SWAP')

            # SourceObj = self.SourceObject

        #     SourceVcoList = [
        #         SourceObj.matrix_world @ SourceObj.data.vertices[idx].co
        #         for idx in SourceVidList
        #     ]
        #     _, _, DistList, _, _ = KdIcpPairs(
        #         SourceVcoList, TargetVcoList, VertsLimite=VertsLimite
        #     )
        #     MaxDist = max(DistList)
        #     MeanDist = np.mean(DistList)
        #     print(f"Number of iterations = {i}")
        #     print(f"Mean Distance = {round(MeanDist, 4)} mm")
        #     bpy.ops.wm.redraw_timer(context,type='DRAW_SWAP')
        #     #######################################################
        #     if MeanDist <= Precision:
        #         self.ResultMessage = [
        #             "Allignement Done !",
        #             f"Mean Distance < or = {Precision} mm",
        #         ]
        #         print(f"Number of iterations = {i}")
        #         print(f"Precision of {Precision} mm reached.")
        #         print(f"Mean Distance = {round(MeanDist, 4)} mm")
        #         break

        # if MeanDist > Precision:
        #     print(f"Number of iterations = {i}")
        print(f"FINISHED : Mean Distance = ({round(MeanDist, 6)} mm)")
        self.ResultMessage = [
            "Allignement Done !",
            f"Mean Distance = {round(MeanDist, 6)} mm",
        ]

    def modal(self, context, event):

        ############################################
        # undo = (event.ctrl == True and event.type == 'Z')
        if not event.type in {
            self.TargetChar,
            self.SourceChar,
            "DEL",
            "RET",
            "ESC",
        }:
            # allow navigation

            return {"PASS_THROUGH"}


                
        #########################################
        if event.type == self.TargetChar:
            # Add Target Refference point :
            if event.value == ("PRESS"):
                color = self.TargetColor
                CollName = self.CollName
                self.TargetCounter += 1
                name = f"B{self.TargetCounter}"
                RefP = AddRefPoint(name, color, CollName)
                self.TargetRefPoints.append(RefP)
                self.TotalRefPoints.append(RefP)
                bpy.ops.object.select_all(action="DESELECT")

        #########################################
        if event.type == self.SourceChar:
            # Add Source Refference point :
            if event.value == ("PRESS"):
                color = self.SourceColor
                CollName = self.CollName
                self.SourceCounter += 1
                name = f"M{self.SourceCounter}"
                RefP = AddRefPoint(name, color, CollName)
                self.SourceRefPoints.append(RefP)
                self.TotalRefPoints.append(RefP)
                bpy.ops.object.select_all(action="DESELECT")

        ###########################################
        elif event.type == ("DEL"):
            if event.value == ("PRESS"):
                if self.TotalRefPoints:
                    obj = self.TotalRefPoints.pop()
                    name = obj.name
                    if name.startswith("B"):
                        self.TargetCounter -= 1
                        self.TargetRefPoints.pop()
                    if name.startswith("M"):
                        self.SourceCounter -= 1
                        self.SourceRefPoints.pop()
                    bpy.data.objects.remove(obj)
                    bpy.ops.object.select_all(action="DESELECT")

        ###########################################
        elif event.type == "RET":

            if event.value == ("PRESS"):

                start = Tcounter()

                TargetObj = self.TargetObject
                SourceObj = self.SourceObject
                Override, area3D, space3D = CtxOverride(context)
                #############################################
                condition = (
                    len(self.TargetRefPoints) == len(self.SourceRefPoints)
                    and len(self.TargetRefPoints) >= 3
                )
                if not condition:
                    message = [
                        "          Please check the following :",
                        "   - The number of Base Refference points and,",
                        "       Align Refference points should match!",
                        "   - The number of Base Refference points ,",
                        "         and Align Refference points,",
                        "       should be superior or equal to 3",
                        "        <<Please check and retry !>>",
                    ]
                    ShowMessageBox(message=message, icon="COLORSET_02_VEC")

                else:

                    TransformMatrix = RefPointsToTransformMatrix(
                        self.TargetRefPoints, self.SourceRefPoints
                    )

                    SourceObj.matrix_world = TransformMatrix @ SourceObj.matrix_world
                    for SourceRefP in self.SourceRefPoints:
                        SourceRefP.matrix_world = (
                            TransformMatrix @ SourceRefP.matrix_world
                        )
                        SourceRefP.update_tag()

                    
                    for obj in [TargetObj, SourceObj]:
                        obj.update_tag()
                    # Update scene :
                    context.view_layer.update()

                    AdjustRefPoints(self.TargetRefPoints, self.SourceRefPoints)

                    # Update scene :
                    context.view_layer.update()

                    bpy.ops.wm.redraw_timer(Override,type='DRAW_SWAP')
                    #########################################################
                    # ICP alignement :
                    print("ICP Align processing...")
                    IcpVidDict = VidDictFromPoints(
                        TargetRefPoints=self.TargetRefPoints,
                        SourceRefPoints=self.SourceRefPoints,
                        TargetObj=TargetObj,
                        SourceObj=SourceObj,
                        radius=2,
                    )
                    BDENTAL_ALIGN_Props = bpy.context.scene.BDENTAL_ALIGN_Props
                    BDENTAL_ALIGN_Props.IcpVidDict = str(IcpVidDict)

                    SourceVidDict, TargetVidDict = (
                        IcpVidDict[SourceObj],
                        IcpVidDict[TargetObj],
                    )


                    # SourceVidList, TargetVidList = (
                    #     IcpVidDict[SourceObj],
                    #     IcpVidDict[TargetObj],
                    # )

                    self.IcpPipline(
                        context=Override,
                        SourceObj=SourceObj,
                        TargetObj=TargetObj,
                        SourceVidDict=SourceVidDict,
                        TargetVidDict=TargetVidDict,
                        VertsLimite=10000,
                        Iterations=20,
                        Precision=0.0001,
                    )

                    for obj in self.TotalRefPoints:
                        bpy.data.objects.remove(obj)

                    AlignColl = bpy.data.collections.get('ALIGN POINTS')
                    if AlignColl :
                        bpy.data.collections.remove(AlignColl)

                    Override, area3D, space3D = CtxOverride(context)
                    ##########################################################
                    space3D.overlay.show_outline_selected = True
                    space3D.overlay.show_object_origins = True
                    space3D.overlay.show_annotation = True
                    space3D.overlay.show_text = True
                    space3D.overlay.show_extras = True
                    space3D.overlay.show_floor = True
                    space3D.overlay.show_axis_x = True
                    space3D.overlay.show_axis_y = True
                    ###########################################################

                    bpy.ops.object.hide_view_clear(Override)
                    bpy.ops.object.select_all(Override, action="DESELECT")
                    for obj in self.visibleObjects:
                        obj.select_set(True)
                        bpy.context.view_layer.objects.active = obj
                    bpy.ops.object.hide_view_set(Override, unselected=True)
                    bpy.ops.object.select_all(Override, action="DESELECT")
                    bpy.ops.wm.tool_set_by_id(Override, name="builtin.select")
                    bpy.context.scene.tool_settings.use_snap = False
                    space3D.shading.background_color = self.background_color
                    space3D.shading.background_type = self.background_type
                    BDENTAL_ALIGN_Props = context.scene.BDENTAL_ALIGN_Props
                    BDENTAL_ALIGN_Props.AlignModalState = False
                    bpy.context.scene.cursor.location = (0, 0, 0)

                    for obj in [TargetObj, SourceObj]:
                        obj.select_set(True)
                        bpy.context.view_layer.objects.active = TargetObj

                    bpy.ops.screen.screen_full_area(Override)

                    ShowMessageBox(message=self.ResultMessage, icon="COLORSET_03_VEC")
                    ##########################################################

                    finish = Tcounter()
                    print(f"Alignement finshed in {finish-start} secondes")

                    return {"FINISHED"}

        ###########################################
        elif event.type == ("ESC"):

            if event.value == ("PRESS"):

                TargetObj = self.TargetObject
                SourceObj = self.SourceObject
                
                if self.TargetRefPoints :
                    for RefP in self.TotalRefPoints:
                        bpy.data.objects.remove(RefP)

                AlignColl = bpy.data.collections.get('ALIGN POINTS')
                if AlignColl :
                    bpy.data.collections.remove(AlignColl)

                Override, area3D, space3D = CtxOverride(context)
                ##########################################################
                space3D.overlay.show_outline_selected = True
                space3D.overlay.show_object_origins = True
                space3D.overlay.show_annotation = True
                space3D.overlay.show_text = True
                space3D.overlay.show_extras = True
                space3D.overlay.show_floor = True
                space3D.overlay.show_axis_x = True
                space3D.overlay.show_axis_y = True
                ###########################################################

                bpy.ops.object.hide_view_clear(Override)
                bpy.ops.object.select_all(Override, action="DESELECT")
                for obj in self.visibleObjects:
                    obj.select_set(True)
                    bpy.context.view_layer.objects.active = obj
                bpy.ops.object.hide_view_set(Override, unselected=True)
                bpy.ops.object.select_all(Override, action="DESELECT")
                bpy.ops.wm.tool_set_by_id(Override, name="builtin.select")
                bpy.context.scene.tool_settings.use_snap = False
                space3D.shading.background_color = self.background_color
                space3D.shading.background_type = self.background_type
                BDENTAL_ALIGN_Props = context.scene.BDENTAL_ALIGN_Props
                BDENTAL_ALIGN_Props.AlignModalState = False
                bpy.context.scene.cursor.location = (0, 0, 0)

                for obj in [TargetObj, SourceObj]:
                    obj.select_set(True)
                    bpy.context.view_layer.objects.active = TargetObj

                bpy.ops.screen.screen_full_area(Override)

                message = [
                    " The Align Operation was Cancelled!",
                ]

                ShowMessageBox(message=message, icon="COLORSET_03_VEC")

                return {"CANCELLED"}

        return {"RUNNING_MODAL"}

    def invoke(self, context, event):
        Condition_1 = len(bpy.context.selected_objects) != 2
        Condition_2 = bpy.context.selected_objects and not bpy.context.active_object
        Condition_3 = bpy.context.selected_objects and not (
            bpy.context.active_object in bpy.context.selected_objects
        )

        if Condition_1 or Condition_2 or Condition_3:

            message = [
                "Selection is invalid !",
                "Please Deselect all objects,",
                "Select the Object to Align and ,",
                "<SHIFT + Select> the Base Object.",
                "Click info button for more info.",
            ]
            ShowMessageBox(message=message, icon="COLORSET_02_VEC")

            return {"CANCELLED"}

        else:

            if context.space_data.type == "VIEW_3D":
                BDENTAL_ALIGN_Props = context.scene.BDENTAL_ALIGN_Props
                BDENTAL_ALIGN_Props.AlignModalState = True
                # Prepare scene  :
                ##########################################################

                bpy.context.space_data.overlay.show_outline_selected = False
                bpy.context.space_data.overlay.show_object_origins = False
                bpy.context.space_data.overlay.show_annotation = False
                bpy.context.space_data.overlay.show_text = False
                bpy.context.space_data.overlay.show_extras = False
                bpy.context.space_data.overlay.show_floor = False
                bpy.context.space_data.overlay.show_axis_x = False
                bpy.context.space_data.overlay.show_axis_y = False
                bpy.context.scene.tool_settings.use_snap = True
                bpy.context.scene.tool_settings.snap_elements = {"FACE"}
                bpy.context.scene.tool_settings.transform_pivot_point = (
                    "INDIVIDUAL_ORIGINS"
                )
                bpy.ops.wm.tool_set_by_id(name="builtin.cursor")
                bpy.ops.object.hide_view_set(unselected=True)

                ###########################################################
                self.TargetObject = bpy.context.active_object
                self.SourceObject = [
                    obj
                    for obj in bpy.context.selected_objects
                    if not obj is self.TargetObject
                ][0]

                self.TargetRefPoints = []
                self.SourceRefPoints = []
                self.TotalRefPoints = []

                self.TargetCounter = 0
                self.SourceCounter = 0
                self.visibleObjects = bpy.context.visible_objects.copy()
                self.background_type = bpy.context.space_data.shading.background_type
                bpy.context.space_data.shading.background_type = "VIEWPORT"
                self.background_color = tuple(
                    bpy.context.space_data.shading.background_color
                )
                bpy.context.space_data.shading.background_color = (0.0, 0.0, 0.0)

                bpy.ops.screen.screen_full_area()
                Override, area3D, space3D = CtxOverride(context)
                # bpy.ops.object.select_all(action="DESELECT")
                context.window_manager.modal_handler_add(self)

                return {"RUNNING_MODAL"}

            else:

                self.report({"WARNING"}, "Active space must be a View3d")

                return {"CANCELLED"}


############################################################################
class BDENTAL_ALIGN_OT_AlignPointsInfo(bpy.types.Operator):
    """ Add Align Refference points """

    bl_idname = "bdental_align.alignpointsinfo"
    bl_label = "INFO"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):

        message = [
            "\u2588 Deselect all objects,",
            "\u2588 Select the Object to Align,",
            "\u2588 Press <SHIFT + Click> to select the Base Object,",
            "\u2588 Click <ALIGN> button,",
            f"      Press <Left Click> to Place Cursor,",
            f"      Press <'B'> to Add Green Point (Base),",
            f"      Press <'A'> to Add Red Point (Align),",
            f"      Press <'DEL'> to delete Point,",
            f"      Press <'ESC'> to Cancel Operation,",
            f"      Press <'ENTER'> to execute Alignement.",
            "\u2588 NOTE :",
            "3 Green Points and 3 Red Points,",
            "are the minimum required for Alignement!",
        ]
        ShowMessageBox(message=message, title="INFO", icon="INFO")

        return {"FINISHED"}


#############################################################################
classes = [
    BDENTAL_ALIGN_OT_AlignPoints,
    BDENTAL_ALIGN_OT_AlignPointsInfo,
]


def register():

    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

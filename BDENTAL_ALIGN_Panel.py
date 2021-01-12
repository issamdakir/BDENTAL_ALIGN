import bpy

# Selected icons :
red_icon = "COLORSET_01_VEC"
orange_icon = "COLORSET_02_VEC"
green_icon = "COLORSET_03_VEC"
blue_icon = "COLORSET_04_VEC"
violet_icon = "COLORSET_06_VEC"
yellow_icon = "COLORSET_09_VEC"
yellow_point = "KEYTYPE_KEYFRAME_VEC"
blue_point = "KEYTYPE_BREAKDOWN_VEC"

####################################################################
class BDENTAL_ALIGN_PT_Main(bpy.types.Panel):
    """ BDENTAL ALIGN Main Panel"""

    bl_idname = "BDENTAL_ALIGN_PT_Main"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"  # blender 2.7 and lower = TOOLS
    bl_category = "BDENT-ALIGN"
    bl_label = "BDENTAL ALIGN"
    # bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):

        # Model operation property group :
        BDENTAL_ALIGN_Props = context.scene.BDENTAL_ALIGN_Props
        GroupNodeName = BDENTAL_ALIGN_Props.GroupNodeName
        VGS = bpy.data.node_groups.get(GroupNodeName)
        Wmin, Wmax = BDENTAL_ALIGN_Props.Wmin, BDENTAL_ALIGN_Props.Wmax

        # Draw Addon UI :

        layout = self.layout
        # row = layout.row()
        # row.operator("bdental_align.addplanes", icon="COLORSET_03_VEC")
        row = layout.row()
        row.prop(BDENTAL_ALIGN_Props, "UserProjectDir", text="Project Directory")

        if BDENTAL_ALIGN_Props.UserProjectDir:
            row = layout.row()
            row.prop(BDENTAL_ALIGN_Props, "DataType")

            if BDENTAL_ALIGN_Props.DataType == "DICOM Series":
                # row = layout.row()
                # row.label(text="DICOM Series Folder :")
                row = layout.row()
                row.prop(BDENTAL_ALIGN_Props, "UserDcmDir", text="DICOM Folder")
                if BDENTAL_ALIGN_Props.UserDcmDir:

                    if BDENTAL_ALIGN_Props.PngDir:
                        row = layout.row()
                        row.operator(
                            "bdental_align.load_dicom_series", icon="COLORSET_03_VEC"
                        )
                        if BDENTAL_ALIGN_Props.CT_Rendered:
                            row = layout.row()
                            row.operator(
                                "bdental_align.volume_render", icon="COLORSET_03_VEC"
                            )

                            row = layout.row()
                            row.label(text=f"Threshold {Wmin} to {Wmax} HU:")
                            row = layout.row()
                            row.prop(
                                BDENTAL_ALIGN_Props,
                                "Treshold",
                                text="TRESHOLD",
                                slider=True,
                            )
                            row = layout.row()
                            row.operator("bdental_align.addslices", icon="EMPTY_AXIS")

                            if (
                                context.active_object
                                and context.active_object.type == "MESH"
                            ):
                                obj = context.active_object
                                if "_SLICE" in obj.name:
                                    split = layout.split(align=True)
                                    col = split.column()
                                    col.label(text=f" {obj.name} location:")
                                    row = col.row(align=True)
                                    row.prop(
                                        obj,
                                        "location",
                                        index=0,
                                        text="Location X :",
                                    )
                                    row = col.row(align=True)
                                    row.prop(
                                        obj,
                                        "location",
                                        index=1,
                                        text="Location Y :",
                                    )
                                    row = col.row(align=True)
                                    row.prop(
                                        obj,
                                        "location",
                                        index=2,
                                        text="Location Z :",
                                    )

                                    col = split.column()
                                    col.label(text=f" {obj.name} rotation:")
                                    row = col.row(align=True)
                                    row.prop(
                                        obj,
                                        "rotation_euler",
                                        index=0,
                                        text="Angle X :",
                                    )
                                    row = col.row(align=True)
                                    row.prop(
                                        obj,
                                        "rotation_euler",
                                        index=1,
                                        text="Angle Y :",
                                    )
                                    row = col.row(align=True)
                                    row.prop(
                                        obj,
                                        "rotation_euler",
                                        index=2,
                                        text="Angle Z :",
                                    )
                            row = layout.row()
                            row.operator("bdental_align.tresh_segment")

                        else:
                            row = layout.row()
                            row.operator(
                                "bdental_align.volume_render", icon="COLORSET_01_VEC"
                            )

                    if not BDENTAL_ALIGN_Props.PngDir:
                        row = layout.row()
                        row.operator(
                            "bdental_align.load_dicom_series", icon="COLORSET_01_VEC"
                        )

            if BDENTAL_ALIGN_Props.DataType == "3D Image File":

                row = layout.row()
                row.prop(BDENTAL_ALIGN_Props, "UserImageFile", text="File Path")

                if BDENTAL_ALIGN_Props.UserImageFile:
                    if BDENTAL_ALIGN_Props.PngDir:
                        row = layout.row()
                        row.operator(
                            "bdental_align.load_3dimage_file", icon="COLORSET_03_VEC"
                        )
                        if BDENTAL_ALIGN_Props.CT_Rendered:
                            row = layout.row()
                            row.operator(
                                "bdental_align.volume_render", icon="COLORSET_03_VEC"
                            )
                            row = layout.row()
                            row.label(text=f"TRESHOLD {Wmin}/{Wmax} :")
                            row = layout.row()
                            row.prop(
                                BDENTAL_ALIGN_Props,
                                "Treshold",
                                text="TRESHOLD",
                                slider=True,
                            )
                            row = layout.row()
                            row.operator("bdental_align.addslices", icon="EMPTY_AXIS")

                            if (
                                context.active_object
                                and context.active_object.type == "MESH"
                            ):
                                obj = context.active_object
                                if "_SLICE" in obj.name:
                                    split = layout.split(align=True)
                                    col = split.column()
                                    col.label(text=f" {obj.name} location:")
                                    row = col.row(align=True)
                                    row.prop(
                                        obj, "location", index=0, text="Location X :"
                                    )
                                    row = col.row(align=True)
                                    row.prop(
                                        obj, "location", index=1, text="Location Y :"
                                    )
                                    row = col.row(align=True)
                                    row.prop(
                                        obj, "location", index=2, text="Location Z :"
                                    )

                                    col = split.column()
                                    col.label(text=f" {obj.name} rotation:")
                                    row = col.row(align=True)
                                    row.prop(
                                        obj, "rotation_euler", index=0, text="Angle X :"
                                    )
                                    row = col.row(align=True)
                                    row.prop(
                                        obj, "rotation_euler", index=1, text="Angle Y :"
                                    )
                                    row = col.row(align=True)
                                    row.prop(
                                        obj, "rotation_euler", index=2, text="Angle Z :"
                                    )

                            row = layout.row()
                            row.operator("bdental_align.tresh_segment")
                        else:
                            row = layout.row()
                            row.operator(
                                "bdental_align.volume_render", icon="COLORSET_01_VEC"
                            )

                    if not BDENTAL_ALIGN_Props.PngDir:
                        row = layout.row()
                        row.operator(
                            "bdental_align.load_3dimage_file", icon="COLORSET_01_VEC"
                        )


class BDENTAL_ALIGN_PT_Main(bpy.types.Panel):
    """ BDENTAL ALIGN Main Panel"""

    bl_idname = "BDENTAL_ALIGN_PT_Main"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"  # blender 2.7 and lower = TOOLS
    bl_category = "BDENT-ALIGN"
    bl_label = "BDENTAL ALIGN"
    # bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        BDENTAL_ALIGN_Props = context.scene.BDENTAL_ALIGN_Props
        AlignModalState = BDENTAL_ALIGN_Props.AlignModalState
        layout = self.layout
        split = layout.split(factor=2 / 3, align=False)
        col = split.column()
        row = col.row()
        row.operator("bdental_align.alignpoints", text="ALIGN")
        col = split.column()
        row = col.row()
        row.alert = True
        row.operator("bdental_align.alignpointsinfo", text="INFO", icon="INFO")

        # # conditions :
        # ###################################
        # if not bpy.context.selected_objects:
        #     self.AlignLabels = "NOTREADY"
        #     TargetObjectLabel = " Empty !"
        #     TargetObjectIcon = red_icon
        #     SourceObjectLabel = " Empty !"
        #     SourceObjectIcon = red_icon

        # if len(bpy.context.selected_objects) == 1:
        #     self.AlignLabels = "NOTREADY"
        #     TargetObject = bpy.context.selected_objects[0]
        #     TargetObjectLabel = f" {TargetObject.name}"
        #     TargetObjectIcon = green_icon
        #     SourceObjectLabel = " Empty ! "
        #     SourceObjectIcon = red_icon

        # if len(bpy.context.selected_objects) == 2:
        #     self.AlignLabels = "GOOD"
        #     TargetObject = bpy.context.active_object
        #     SourceObject = [
        #         obj
        #         for obj in bpy.context.selected_objects
        #         if not obj is bpy.context.active_object
        #     ][0]
        #     TargetObjectLabel = f" {TargetObject.name}"
        #     TargetObjectIcon = green_icon
        #     SourceObjectLabel = f" {SourceObject.name}"
        #     SourceObjectIcon = orange_icon

        Condition_1 = len(bpy.context.selected_objects) != 2
        Condition_2 = bpy.context.selected_objects and not bpy.context.active_object
        Condition_3 = bpy.context.selected_objects and not (
            bpy.context.active_object in bpy.context.selected_objects
        )
        Condition_4 = not bpy.context.active_object in bpy.context.visible_objects

        Conditions = Condition_1 or Condition_2 or Condition_3 or Condition_4
        if AlignModalState:
            self.AlignLabels = "MODAL"
        else:
            if Conditions:
                self.AlignLabels = "INVALID"

            else:
                self.AlignLabels = "READY"

        #########################################

        if self.AlignLabels == "READY":
            TargetObjectName = context.active_object.name
            SourceObjectName = [
                obj
                for obj in bpy.context.selected_objects
                if not obj is bpy.context.active_object
            ][0].name

            box = layout.box()

            row = box.row()
            row.alert = True
            row.alignment = "CENTER"
            row.label(text="READY FOR ALIGNEMENT.")

            row = box.row()
            row.alignment = "CENTER"
            row.label(text=f"{SourceObjectName} will be aligned to, {TargetObjectName}")

            # row = box.row()
            # row.label(text="will be aligned to,")

            # row = box.row()
            # row.label(text=f"{SourceObjectName}")

        if self.AlignLabels == "INVALID" or self.AlignLabels == "NOTREADY":
            box = layout.box()
            row = box.row(align=True)
            row.alert = True
            row.alignment = "CENTER"
            row.label(text="STANDBY MODE", icon="ERROR")

        if self.AlignLabels == "MODAL":
            box = layout.box()
            row = box.row()
            row.alert = True
            row.alignment = "CENTER"
            row.label(text="WAITING FOR ALIGNEMENT...")


#################################################################################################
# Registration :
#################################################################################################

classes = [
    BDENTAL_ALIGN_PT_Main,
]


def register():

    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


##########################################################
# TreshRamp = VGS.nodes.get("TresholdRamp")
# ColorPresetRamp = VGS.nodes.get("ColorPresetRamp")
# row = layout.row()
# row.label(
#     text=f"Volume Treshold ({BDENTAL_ALIGN_Props.Wmin}/{BDENTAL_ALIGN_Props.Wmax} HU) :"
# )
# row.template_color_ramp(
#     TreshRamp,
#     "color_ramp",
#     expand=True,
# )
# row = layout.row()
# row.prop(BDENTAL_ALIGN_Props, "Axial_Loc", text="AXIAL Location :")
# row = layout.row()
# row.prop(BDENTAL_ALIGN_Props, "Axial_Rot", text="AXIAL Rotation :")
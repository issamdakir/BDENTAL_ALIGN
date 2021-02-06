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

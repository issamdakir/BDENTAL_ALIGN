import bpy

from bpy.props import (
    StringProperty,
    IntProperty,
    FloatProperty,
    EnumProperty,
    FloatVectorProperty,
    BoolProperty,
)


class BDENTAL_ALIGN_Props(bpy.types.PropertyGroup):

    #############################################################################################
    # BDENTAL_ALIGN Properties :
    #############################################################################################
    IcpVidDict: StringProperty(
        name="IcpVidDict",
        default="None",
        description="ICP Vertices Pairs str(Dict)",
    )

    #######################
    Progress_Bar: FloatProperty(
        name="Progress_Bar",
        description="Progress_Bar",
        subtype="PERCENTAGE",
        default=0.0,
        min=0.0,
        max=100.0,
        soft_min=0.0,
        soft_max=100.0,
        step=1,
        precision=1,
    )

    #######################
    AlignModalState : BoolProperty(description="Align Modal state ", default=False)
    useICP : BoolProperty(description="use ICP mode ", default=True) 


#################################################################################################
# Registration :
#################################################################################################

classes = [
    BDENTAL_ALIGN_Props,
]


def register():

    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.BDENTAL_ALIGN_Props = bpy.props.PointerProperty(
        type=BDENTAL_ALIGN_Props
    )


def unregister():

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.BDENTAL_ALIGN_Props


#####################################

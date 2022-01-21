# ----------------------------------------------------------
# File __init__.py
# ----------------------------------------------------------

#    Addon info
# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####
##############################################################################################
bl_info = {
    "name": "BDENTAL ALIGN",
    "author": "Essaid Issam Dakir DMD",
    "version": (1, 0, 0),
    "blender": (3, 0, 0),
    "location": "3D View -> UI SIDE PANEL ",
    "description": "Align Tools for Digital Dentistry",
    "warning": "",
    "doc_url": "",
    "tracker_url": "",
    "category": "Dental",
}
#############################################################################################
# IMPORTS :
#############################################################################################
# Python imports :
import sys, bpy

# activate unicode characters in windows CLI :
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="cp65001")

#############################################################
# Addon modules imports :
from . import BDENTAL_ALIGN_Props, BDENTAL_ALIGN_Panel
from .Operators import BDENTAL_ALIGN_Operators

############################################################################################
# Registration :
############################################################################################
addon_modules = [
    BDENTAL_ALIGN_Props,
    BDENTAL_ALIGN_Panel,
    BDENTAL_ALIGN_Operators,
]
init_classes = []


def register():

    for module in addon_modules:
        module.register()
    for cl in init_classes:
        bpy.utils.register_class(cl)


def unregister():
    for cl in init_classes:
        bpy.utils.unregister_class(cl)
    for module in reversed(addon_modules):
        module.unregister()


if __name__ == "__main__":
    register()

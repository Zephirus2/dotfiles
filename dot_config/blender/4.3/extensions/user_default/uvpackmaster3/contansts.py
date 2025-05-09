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

from .enums import UvpmAxis, UvpmScaleMode
from .labels import *

from .app_iface import *


class PropConstants:

    ROTATION_ENABLE_DEFAULT = True
    PRE_ROTATION_DISABLE_DEFAULT = False

    ROTATION_STEP_MIN = 1
    ROTATION_STEP_MAX = 180
    ROTATION_STEP_DEFAULT = 90

    FLIPPING_ENABLE_DEFAULT = False

    PIXEL_MARGIN_MIN = 1
    PIXEL_MARGIN_MAX = 256
    PIXEL_MARGIN_DEFAULT = 5

    PIXEL_BORDER_MARGIN_MIN = 0
    PIXEL_BORDER_MARGIN_MAX = 256
    PIXEL_BORDER_MARGIN_DEFAULT = 0

    EXTRA_PIXEL_MARGIN_TO_OTHERS_MIN = 0
    EXTRA_PIXEL_MARGIN_TO_OTHERS_MAX = 128
    EXTRA_PIXEL_MARGIN_TO_OTHERS_DEFAULT = 0

    PIXEL_MARGIN_TEX_SIZE_MIN = 16
    PIXEL_MARGIN_TEX_SIZE_MAX = 32768	
    PIXEL_MARGIN_TEX_SIZE_DEFAULT = 1024

    TILE_COUNT_XY_DEFAULT = 1
    TILE_COUNT_XY_MIN = 1
    TILE_COUNT_XY_MAX = 100

    TILES_IN_ROW_DEFAULT = 10
    TILE_COUNT_PER_GROUP_DEFAULT = 1
    LAST_GROUP_COMPLEMENTARY_DEFAULT = False
    GROUPS_TOGETHER_DEFAULT = False
    GROUP_COMPACTNESS_DEFAULT = 0.0
    PACK_TO_SINGLE_BOX_DEFAULT = False
    
    ORIENT_PRIM_3D_AXIS_DEFAULT = UvpmAxis.Z.code
    ORIENT_PRIM_UV_AXIS_DEFAULT = UvpmAxis.Y.code
    ORIENT_SEC_3D_AXIS_DEFAULT = UvpmAxis.X.code
    ORIENT_SEC_UV_AXIS_DEFAULT = UvpmAxis.X.code

    ORIENT_PRIM_SEC_BIAS_DEFAULT = 80


def def_prop__scale_mode():
    return EnumProperty(
        name=Labels.SCALE_MODE_NAME,
        description=Labels.SCALE_MODE_DESC,
        items=UvpmScaleMode.to_blend_items())

def def_prop__pixel_margin():
    return IntProperty(
        name=Labels.PIXEL_MARGIN_NAME,
        description=Labels.PIXEL_MARGIN_DESC,
        min=PropConstants.PIXEL_MARGIN_MIN,
        max=PropConstants.PIXEL_MARGIN_MAX,
        default=PropConstants.PIXEL_MARGIN_DEFAULT)

def def_prop__pixel_border_margin():
    return IntProperty(
        name=Labels.PIXEL_BORDER_MARGIN_NAME,
        description=Labels.PIXEL_BORDER_MARGIN_DESC,
        min=PropConstants.PIXEL_BORDER_MARGIN_MIN,
        max=PropConstants.PIXEL_BORDER_MARGIN_MAX,
        default=PropConstants.PIXEL_BORDER_MARGIN_DEFAULT)

def def_prop__extra_pixel_margin_to_others():
    return IntProperty(
        name=Labels.EXTRA_PIXEL_MARGIN_TO_OTHERS_NAME,
        description=Labels.EXTRA_PIXEL_MARGIN_TO_OTHERS_DESC,
        min=PropConstants.EXTRA_PIXEL_MARGIN_TO_OTHERS_MIN,
        max=PropConstants.EXTRA_PIXEL_MARGIN_TO_OTHERS_MAX,
        default=PropConstants.EXTRA_PIXEL_MARGIN_TO_OTHERS_DEFAULT)

def def_prop__pixel_margin_tex_size():
    return IntProperty(
        name=Labels.PIXEL_MARGIN_TEX_SIZE_NAME,
        description=Labels.PIXEL_MARGIN_TEX_SIZE_DESC,
        min=PropConstants.PIXEL_MARGIN_TEX_SIZE_MIN,
        max=PropConstants.PIXEL_MARGIN_TEX_SIZE_MAX,
        default=PropConstants.PIXEL_MARGIN_TEX_SIZE_DEFAULT)

def def_prop__pixel_perfect_align():
    return BoolProperty(
        name=Labels.PIXEL_PERFECT_ALIGN_NAME,
        description=Labels.PIXEL_PERFECT_ALIGN_DESC,
        default=False)

def def_prop__groups_together():
    return BoolProperty(
        name=Labels.GROUPS_TOGETHER_NAME,
        description=Labels.GROUPS_TOGETHER_DESC,
        default=PropConstants.GROUPS_TOGETHER_DEFAULT)

def def_prop__group_compactness():
    return FloatProperty(
        name=Labels.GROUP_COMPACTNESS_NAME,
        description=Labels.GROUP_COMPACTNESS_DESC,
        default=PropConstants.GROUP_COMPACTNESS_DEFAULT,
        min=0.0,
        max=1.0,
        precision=2,
        step=10.0)

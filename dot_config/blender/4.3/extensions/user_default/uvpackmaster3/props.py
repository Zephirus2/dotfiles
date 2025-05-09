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


from .enums import *
from .utils import PanelUtilsMixin
from .labels import Labels
from .pgroup import standalone_property_group
from .app_iface import *


class UVPM3_TrackGroupsProps(PropertyGroup):

    require_match_for_all : BoolProperty(
        name=Labels.TRACK_GROUPS_REQUIRE_MATCH_FOR_ALL_NAME,
        description=Labels.TRACK_GROUPS_REQUIRE_MATCH_FOR_ALL_DESC,
        default=True
    )

    matching_mode : EnumProperty(
        items=UvpmSimilarityMode.to_blend_items(),
        name=Labels.TRACK_GROUPS_MATCHING_MODE_NAME,
        description=Labels.TRACK_GROUPS_MATCHING_MODE_DESC)


@standalone_property_group
class UVPM3_PackStrategyProps(PanelUtilsMixin):

    HELP_URL_SUFFIX = '20-packing-functionalities/45-advanced-packing-options/#pack-strategy'

    strategy : EnumProperty(
        items=UvpmPackStrategy.to_blend_items(),
        name=Labels.PACK_STRATEGY_NAME,
        description=Labels.PACK_STRATEGY_DESC)
    
    start_corner : EnumProperty(
        items=UvpmBoxCorner.to_blend_items(),
        name=Labels.PACK_STRATEGY_START_CORNER_NAME,
        description=Labels.PACK_STRATEGY_START_CORNER_DESC)
    

    def __init__(self):
        self.strategy = UvpmPackStrategy.AUTOMATIC.code
        self.start_corner = UvpmBoxCorner.BOTTOM_LEFT.code

    def copy_from(self, other):
        self.strategy = str(other.strategy)
        self.start_corner = str(other.start_corner)

    def draw(self, layout):
        col = layout.column(align=True)
        inner_col = self.draw_enum_in_box(self, "strategy", col, help_url_suffix=self.HELP_URL_SUFFIX)

        if self.strategy != UvpmPackStrategy.AUTOMATIC.code:
            self.draw_enum_in_box(self, "start_corner", inner_col, expand=True)

    def to_script_param(self):
        return {
            'strategy': int(self.strategy),
            'start_corner': int(self.start_corner)
        }

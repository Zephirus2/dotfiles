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

from ...panel_islands import UVPM3_PT_StackGroups
from ...panel_align import UVPM3_PT_SubPanelAlign, UVPM3_PT_IParamEditAlign
from ...enums import UvpmSimilarityMode, UvpmAxis
from ...labels import Labels
from ...operator_islands import IParamEditUI
from ..operators.align_operator import UVPM3_OT_SplitOverlapping, UVPM3_OT_UndoIslandSplit


class UVPM3_PT_SimilarityOptions(UVPM3_PT_SubPanelAlign):

    bl_idname = 'UVPM3_PT_SimilarityOptions'
    bl_label = 'Similarity Options'
    # bl_options = {}

    PANEL_PRIORITY = 2000


    def draw_impl(self, context):

        layout = self.layout
        col = layout.column(align=True)

        mode_col = self.draw_enum_in_box(self.scene_props, "simi_mode", col)

        if UvpmSimilarityMode.is_vertex_based(self.scene_props.simi_mode):
            box = mode_col.box()
            row = box.row()
            row.prop(self.scene_props, 'simi_correct_vertices')

            row = mode_col.row(align=True)
            row.prop(self.scene_props, 'simi_vertex_threshold')

        else:
            mode_col.prop(self.scene_props, "precision")

            row = mode_col.row(align=True)
            row.prop(self.scene_props, 'simi_threshold')

            box = mode_col.box()
            row = box.row(align=True)
            row.prop(self.scene_props, 'simi_check_holes')


        box = col.box()
        row = box.row(align=True)
        row.prop(self.scene_props, 'flipping_enable')

        box = col.box()
        row = box.row(align=True)
        row.prop(self.scene_props, 'simi_adjust_scale')

        if self.scene_props.simi_adjust_scale:
            row = col.row(align=True)
            row.prop(self.scene_props, 'simi_non_uniform_scaling_tolerance')

        match_col = self.draw_enum_in_box(self.scene_props, "simi_match_3d_axis", col, expand=True)
        match_space_col = self.draw_enum_in_box(self.scene_props, "simi_match_3d_axis_space", match_col, prop_name='', expand=True)
        match_space_col.enabled = self.scene_props.simi_match_3d_axis != UvpmAxis.NONE.code

        # col.separator()


class UVPM3_PT_AlignPriority(UVPM3_PT_IParamEditAlign):

    bl_idname = 'UVPM3_PT_AlignPriority'
    bl_label = 'Align Priority'
    # bl_options = {'DEFAULT_CLOSED'}

    PANEL_PRIORITY = 3000
    IPARAM_INFO_TYPE = 'AlignPriorityIParamInfo'
    HELP_URL_SUFFIX = '35-aligning-functionalities#align-priority'


class UVPM3_PT_StackGroupsAlign(UVPM3_PT_StackGroups, UVPM3_PT_SubPanelAlign):

    bl_idname = 'UVPM3_PT_StackGroupsAlign'
    PANEL_PRIORITY = 4700


class UVPM3_PT_SplitOverlapping(UVPM3_PT_SubPanelAlign):

    bl_idname = 'UVPM3_PT_SplitOverlapping'
    bl_label = 'Split Overlapping'

    PANEL_PRIORITY = 6000


    def draw_impl(self, context):

        layout = self.layout
        col = layout.column(align=True)

        self.draw_enum_in_box(self.scene_props, "split_overlap_detection_mode", col)

        row = col.row(align=True)
        row.prop(self.scene_props, 'split_overlap_max_tile_x')

        col.separator()

        row = col.row(align=True)
        row.operator(UVPM3_OT_SplitOverlapping.bl_idname)

        row = col.row(align=True)
        row.operator(UVPM3_OT_UndoIslandSplit.bl_idname)

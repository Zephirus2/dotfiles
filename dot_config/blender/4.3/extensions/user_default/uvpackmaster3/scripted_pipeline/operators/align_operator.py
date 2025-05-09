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


from ...operator import UVPM3_OT_Engine
from ...operator_islands import UVPM3_OT_ShowManualGroupIParamBase, NumberedGroupsAccess
from ...grouping_scheme import TargetGroupingSchemeMixin
from ...enums import GroupingMethod, UvpmIParamFlags, UvpmLogType, UvpmSimilarityMode, UvpmAxis, UvpmCoordSpace
from ...group import UVPM3_GroupInfo
from ...grouping_scheme_access import GroupingSchemeAccess
from ...utils import redraw_ui
from .grouping_editor_operator import UVPM3_OT_EditGroupingSchemeInEditor
from ...prefs_scripted_utils import ScriptParams
from ...island_params import AlignPriorityIParamInfo, SplitOffsetXIParamInfo, SplitOffsetYIParamInfo, VColorIParamSerializer
from ...app_iface import *


class SimilarityDriver:

    VERTEX_BASED_MODE_PRECISION = 500
    VERTEX_BASED_MODE_THRESHOLD = 1.0

    def __init__(self, context):
        self.scene_props = get_scene_props(context)
        self.stack_groups_access = NumberedGroupsAccess(context, desc_id='stack_group')

    def setup_script_params(self):
        script_params = ScriptParams()

        if UvpmSimilarityMode.is_vertex_based(self.scene_props.simi_mode):
            precision = self.VERTEX_BASED_MODE_PRECISION
            threshold = self.VERTEX_BASED_MODE_THRESHOLD
            check_holes = False
        else:
            precision = self.scene_props.precision
            threshold = self.scene_props.simi_threshold
            check_holes = self.scene_props.simi_check_holes

        simi_params = dict()
        simi_params['mode'] = self.scene_props.simi_mode
        simi_params['precision'] = precision
        simi_params['threshold'] = threshold
        simi_params['check_holes'] = check_holes
        simi_params['flipping_enable'] = self.scene_props.flipping_enable
        simi_params['adjust_scale'] = self.scene_props.simi_adjust_scale
        simi_params['non_uniform_scaling_tolerance'] = self.scene_props.simi_non_uniform_scaling_tolerance
        simi_params['match_3d_axis'] = self.scene_props.simi_match_3d_axis
        simi_params['match_3d_axis_space'] = self.scene_props.simi_match_3d_axis_space
        simi_params['correct_vertices'] = self.scene_props.simi_correct_vertices
        simi_params['vertex_threshold'] = self.scene_props.simi_vertex_threshold

        if self.stack_groups_enabled():
            simi_params['stack_group_iparam_name'] = self.stack_groups_access.get_iparam_info().script_name

        if self.align_priority_enabled():
            simi_params['align_priority_iparam_name'] = AlignPriorityIParamInfo.SCRIPT_NAME

        script_params.add_param('simi_params', simi_params)
        return script_params

    def get_iparam_serializers(self):
        output = []

        if self.stack_groups_enabled():
            output.append(self.stack_groups_access.get_iparam_serializer())

        if self.align_priority_enabled():
            output.append(VColorIParamSerializer(AlignPriorityIParamInfo()))

        return output

    def send_verts_3d(self):
        return self.scene_props.simi_match_3d_axis != UvpmAxis.NONE.code and self.scene_props.simi_match_3d_axis_space == UvpmCoordSpace.LOCAL.code

    def send_verts_3d_global(self):
        return self.scene_props.simi_match_3d_axis != UvpmAxis.NONE.code and self.scene_props.simi_match_3d_axis_space == UvpmCoordSpace.GLOBAL.code

    def align_priority_enabled(self):
        return self.scene_props.align_priority_enable

    def stack_groups_enabled(self):
        return self.stack_groups_access.groups_enabled()
    

class UVPM3_OT_AlignGeneric(UVPM3_OT_Engine):

    def execute_internal(self, context):
        self.simi_driver = SimilarityDriver(context)
        return super().execute_internal(context)

    def split_offset_enabled(self):
        return False
    
    def setup_script_params(self):

        script_params = ScriptParams()
        script_params += self.simi_driver.setup_script_params()

        if self.split_offset_enabled():
            script_params.add_param('split_overlap_detection_mode', self.scene_props.split_overlap_detection_mode)
            script_params.add_param('split_overlap_max_tile_x', self.scene_props.split_overlap_max_tile_x)
            script_params.add_param('split_offset_x_iparam_name', SplitOffsetXIParamInfo.SCRIPT_NAME)
            script_params.add_param('split_offset_y_iparam_name', SplitOffsetYIParamInfo.SCRIPT_NAME)

        return script_params

    def send_verts_3d(self):
        return self.simi_driver.send_verts_3d()

    def send_verts_3d_global(self):
        return self.simi_driver.send_verts_3d_global()

    def get_iparam_serializers(self):
        output = []
        output += self.simi_driver.get_iparam_serializers()

        if self.split_offset_enabled():
            serializer = VColorIParamSerializer(SplitOffsetXIParamInfo())
            serializer.flags |= self.split_offset_iparam_flags()
            output.append(serializer)

            serializer = VColorIParamSerializer(SplitOffsetYIParamInfo())
            serializer.flags |= self.split_offset_iparam_flags()
            output.append(serializer)

        return output


class UVPM3_OT_SelectSimilar(UVPM3_OT_AlignGeneric):

    bl_idname = 'uvpackmaster3.select_similar'
    bl_label = 'Select Similar'
    bl_description = "From all unselected islands, selects all islands which have similar shape to at least one island which is currently selected. For more info regarding similarity detection click the help button"

    SCENARIO_ID = 'align.select_similar'

    def send_unselected_islands(self):
        return True


class UVPM3_OT_AlignSimilar(UVPM3_OT_AlignGeneric):

    bl_idname = 'uvpackmaster3.align_similar'
    bl_label = 'Align Similar (Stack)'
    bl_description = "Align the selected islands, so islands which are similar are stacked on the top of each other. For more info regarding similarity detection click the help button"

    SCENARIO_ID = 'align.align_similar'



def _simi_group_name(group_num):
    return 'S{}'.format(group_num)


class UVPM3_OT_GroupBySimilarity(TargetGroupingSchemeMixin, UVPM3_OT_ShowManualGroupIParamBase, UVPM3_OT_AlignGeneric):

    bl_idname = 'uvpackmaster3.group_by_similarity'
    bl_label = 'Group By Similarity'
    bl_description = 'Group all selected islands by similarity and save generated groups in a grouping scheme'

    SCENARIO_ID = 'align.split_by_similarity'
    ACCESS_DESC_ID = 'editor'

    min_group_size : IntProperty(
        name='Minimum Group Size',
        description='All similarity groups of size lower than the value of this parameter will be ignored and their islands will be reassigned to the default group ({}). If the functionality is not used (value set to 1), the default group will be empty'.format(_simi_group_name(UVPM3_GroupInfo.DEFAULT_GROUP_NUM)),
        min=1,
        max=100,
        default=1)

    def target_scheme_name_impl(self, context):
        return "Scheme 'Similarity'"
    
    def draw_impl(self, context, layout):

        if (not self.create_new_g_scheme()) and (len(self.get_g_schemes()) > 0):
            box = layout.box()
            row = box.row()
            row.label(text='WARNING: operation will overwrite all groups in the existing scheme.')

        row = layout.row(align=True)
        row.prop(self, 'min_group_size')

    def use_default_operation_done_status(self):
        return False

    def pre_operation(self):
        target_g_scheme = self.get_target_g_scheme()

        idx = 0
        while idx < len(target_g_scheme.groups):
            group = target_g_scheme.groups[idx]

            if not group.is_default():
                target_g_scheme.remove_group(idx)
            else:
                idx = idx + 1

        assert len(target_g_scheme.groups) == 1
        def_group = target_g_scheme.groups[0]
        def_group.name = _simi_group_name(def_group.num)
        
        super().pre_operation()

    def post_operation(self):

        self.init_access(self.context, self.get_desc_id_from_obj(self))
        UVPM3_OT_EditGroupingSchemeInEditor.execute_impl(self.context, self.get_active_g_scheme_uuid(), select_editor_with_shift=True)
        self.log_manager.log(UvpmLogType.STATUS, UVPM3_OT_EditGroupingSchemeInEditor.CONFIRMATION_MSG)
        super().post_operation()

    def get_save_iparam_handler(self):

        def save_iparam_handler(iparam_info, g_num):
            group = self.active_g_scheme.get_group_by_num(g_num)
            if not group:
                self.active_g_scheme.add_group_with_target_box(_simi_group_name(g_num), g_num)

        return save_iparam_handler
    
    def setup_script_params(self):
        script_params = super().setup_script_params()
        script_params.add_param('target_iparam_name', self.active_g_scheme.get_iparam_info().script_name)
        script_params.add_param('min_group_size', self.min_group_size)
        return script_params


class UVPM3_OT_SplitOverlappingGeneric(UVPM3_OT_AlignGeneric):

    def split_offset_enabled(self):
        return True
    
    def split_offset_iparam_flags(self):
        return 0

    def operation_done_hint(self):
        return ''


class UVPM3_OT_SplitOverlapping(UVPM3_OT_SplitOverlappingGeneric):

    bl_idname = 'uvpackmaster3.split_overlapping'
    bl_label = 'Split Overlapping Islands'
    bl_description = 'Methodically move overlapping islands to adjacent tiles (in the +X axis direction), so that no selected islands are overlapping each other after the operation is done'

    SCENARIO_ID = 'align.split_overlapping'

    def split_offset_iparam_flags(self):
        return UvpmIParamFlags.CONSISTENCY_CHECK_DISABLE


class UVPM3_OT_UndoIslandSplit(UVPM3_OT_SplitOverlappingGeneric):

    bl_idname = 'uvpackmaster3.undo_island_split'
    bl_label = 'Undo Island Split'
    bl_description = 'Undo the last island split operation - move all selected islands to their original locations before split. WARNING: the operation only process currently selected islands so in order to move an island to its original location, you have to make sure the island is selected when an Undo operation is run'

    SCENARIO_ID = 'align.undo_island_split'

    def skip_topology_parsing(self):
        return True

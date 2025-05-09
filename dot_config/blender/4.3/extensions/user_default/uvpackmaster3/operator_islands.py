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

from .grouping_scheme_access import GroupingSchemeAccess, GroupByNameAccess, AccessDescIdAttrMixin
from .grouping_scheme import TargetGroupingSchemeMixin
from .utils import *
from .pack_context import *
# from .prefs import *
from .island_params import *
from .operator import UVPM3_OT_Engine, ModeIdAttrMixin
from .overlay import TextOverlay
from .event import key_release_event
from .group_map import GroupMapManual
from .help import UVPM3_OT_Help
from .panel import PanelUtilsMixin
from .app_iface import *


class UVPM3_OT_IParamGeneric(UVPM3_OT_Engine):

    SCENARIO_ID = 'util.get_iparam_values'

    def __init__(self):
        super().__init__()
        
        self.iparam_info = None
        self.iparam_value = None
        self.overlay_count = 0
        self.font_size_uv_overlay = int(self.prefs.font_size_uv_overlay)

    def skip_topology_parsing(self):
        return True

    def pre_operation(self):
        self.iparam_info = self.get_iparam_info()
        # self.p_context.register_iparam(self.iparam_info)
        self.iparam_value = self.get_iparam_value()

    def operation_done_finish_condition(self, event):
        return key_release_event(event)

    def operation_done_hint(self):
        if self.log_manager.engine_retcode == UvpmRetCode.SUCCESS:
            return "press any key to hide '{}' values".format(self.iparam_info.label)
        
        return super().operation_done_hint()

    def get_iparam_serializers(self):
        return [VColorIParamSerializer(self.iparam_info)]

    def iparam_to_text(self, iparam_value):
        return self.iparam_info.param_to_text(iparam_value)

    def iparam_to_color(self, iparam_value):
        return self.iparam_info.param_to_color(iparam_value)

    def create_param_overlay(self, p_island):
        self.overlay_count += 1
        iparam_value = p_island.iparam_value(self.iparam_info)
        return TextOverlay(self.iparam_to_text(iparam_value), self.iparam_to_color(iparam_value), font_size=self.font_size_uv_overlay)

    def get_iparam_value(self):
        value_prop_obj = self.iparam_info.value_prop_obj if self.iparam_info.value_prop_obj is not None else self.scene_props
        return getattr(value_prop_obj, self.iparam_info.VALUE_PROP_ID)
    
    def use_default_operation_done_status(self):
        return True

    def post_operation(self):

        for p_island in self.p_context.p_islands:

            if p_island.iparam_values is None:
                continue

            if self.process_island(p_island):
                p_island.register_overlay(self.create_param_overlay(p_island), self.ov_manager)

        if self.overlay_count > 0:
            self.update_context_meshes()


class UVPM3_OT_ShowIParam(UVPM3_OT_IParamGeneric):

    def process_island(self, p_island):

        return True


class UVPM3_OT_SelectIParam(UVPM3_OT_IParamGeneric):

    def pre_operation(self):
        super().pre_operation()

    def require_selection(self):

        return False
        
    def send_unselected_islands(self):

        return True

    def process_island(self, p_island):

        if p_island.iparam_value(self.iparam_info) != self.iparam_value:
            return False

        p_island.select(bool(self.select))
        return True


class UVPM3_OT_SelectNonDefaultIParam(UVPM3_OT_IParamGeneric):

    def require_selection(self):

        return False
        
    def send_unselected_islands(self):

        return True

    def process_island(self, p_island):
        
        if p_island.iparam_value(self.iparam_info) == self.iparam_info.default_value:
            return False

        p_island.select(bool(self.select))
        return True


class UVPM3_OT_SetIParam(UVPM3_OT_ShowIParam):

    bl_options = {'UNDO'}

    def pre_operation(self):
        super().pre_operation()

        self.p_context.save_iparam(
            self.iparam_info,
            self.iparam_value)
        
        self.update_context_meshes()


class UVPM3_OT_SetFreeIParam(UVPM3_OT_ShowIParam):

    bl_options = {'UNDO'}

    def pre_operation(self):
        super().pre_operation()

        self.p_context.save_iparam(
            self.iparam_info,
            self.iparam_value)
        
        self.update_context_meshes()

    def get_iparam_value(self):

        param_values = self.p_context.load_all_iparam_values(self.iparam_info)
        param_values.sort()

        def assign_new_value(new_value):
            return new_value if new_value != self.iparam_info.DEFAULT_VALUE else new_value + 1

        free_value = assign_new_value(self.iparam_info.min_value)

        for iparam_value in param_values:

            if free_value == iparam_value:
                free_value = assign_new_value(free_value + 1)

            elif free_value < iparam_value:
                break

        if free_value > self.iparam_info.max_value:
            raise RuntimeError('Free value not found')

        return free_value


class UVPM3_OT_ResetIParam(UVPM3_OT_SetIParam):

    def get_iparam_value(self):

        return self.iparam_info.default_value



# STD OPERATORS

class IParamInfoTypeAttrMixin:

    iparam_info_type : StringProperty(name='', default='')


class UVPM3_OT_StdIParamGeneric:

    @staticmethod
    def get_iparam_info_impl(iparam_info_type):
        return globals()[iparam_info_type]()
        
    def get_iparam_info(self):
        return self.get_iparam_info_impl(self.iparam_info_type)
    

class UVPM3_OT_StdShowIParam(UVPM3_OT_StdIParamGeneric, UVPM3_OT_ShowIParam, IParamInfoTypeAttrMixin):

    bl_idname = 'uvpackmaster3.std_show_iparam'
    bl_label = 'Show Island Parameter'
    bl_description = "Show island parameter values assigned to the selected islands"


class UVPM3_OT_StdSetIParam(UVPM3_OT_StdIParamGeneric, UVPM3_OT_SetIParam, IParamInfoTypeAttrMixin):

    bl_idname = 'uvpackmaster3.std_set_iparam'
    bl_label = 'Set Island Parameter'

    @classmethod
    def description(cls, context, properties):
        iparam_info = cls.get_iparam_info_impl(properties.iparam_info_type)
        return "Set the island parameter value for the selected islands. The value to be set is determined by the '{}' parameter"\
            .format(iparam_info.get_value_property(context).get_name())


class UVPM3_OT_StdResetIParam(UVPM3_OT_StdIParamGeneric, UVPM3_OT_ResetIParam, IParamInfoTypeAttrMixin):

    bl_idname = 'uvpackmaster3.std_reset_iparam'
    bl_label = 'Reset Island Parameter'
    bl_description = "Reset the island parameter to the default value for the selected islands"


# MANUAL GROUP

class UVPM3_OT_ManualGroupIParamGeneric(GroupingSchemeAccess):

    def get_iparam_info(self):
        if self.active_g_scheme is None or self.active_group is None:
            raise RuntimeError('No active grouping scheme or group')

        return self.active_g_scheme.get_iparam_info()

    def get_iparam_value(self):
        return self.active_group.num

    def iparam_to_text(self, iparam_value):
        return self.active_g_scheme.group_to_text(iparam_value)

    def iparam_to_color(self, iparam_value):
        return rgb_to_rgba(self.active_g_scheme.group_to_color(iparam_value))

    def get_iparam_serializers(self):
        return [self.active_g_scheme.get_iparam_serializer()]


class UVPM3_OT_ShowManualGroupIParamBase(UVPM3_OT_ManualGroupIParamGeneric, UVPM3_OT_ShowIParam):
    pass

class UVPM3_OT_ShowManualGroupIParam(UVPM3_OT_ShowManualGroupIParamBase, AccessDescIdAttrMixin):

    bl_idname = 'uvpackmaster3.uv_show_manual_group_iparam'
    bl_label = 'Show Group Assignment'
    bl_description = "Show the names of all groups the selected islands are assigned to"


class UVPM3_OT_SetManualGroupIParam(UVPM3_OT_ManualGroupIParamGeneric, UVPM3_OT_SetIParam, AccessDescIdAttrMixin):

    bl_idname = 'uvpackmaster3.set_island_manual_group'
    bl_label = 'Assign Islands To The Group'
    bl_description = "Assign the selected islands to the active group"

class UVPM3_OT_ResetManualGroupIParam(UVPM3_OT_ManualGroupIParamGeneric, UVPM3_OT_ResetIParam, AccessDescIdAttrMixin):

    bl_idname = 'uvpackmaster3.reset_island_manual_group'
    bl_label = 'Reset Groups'
    bl_description = "Reset the group assignment for the selected islands"


class UVPM3_OT_SelectManualGroupIParam(UVPM3_OT_ManualGroupIParamGeneric, UVPM3_OT_SelectIParam, AccessDescIdAttrMixin):

    select : BoolProperty(name='', default=True)
    
    bl_idname = 'uvpackmaster3.select_island_manual_group'
    bl_label = 'Select Islands Assigned To Group'
    bl_description = "Select / deselect all islands which are assigned to the active group"


class UVPM3_OT_ApplyGroupingToScheme(TargetGroupingSchemeMixin, UVPM3_OT_ShowManualGroupIParamBase, ModeIdAttrMixin):

    bl_idname = 'uvpackmaster3.apply_grouping_to_scheme'
    bl_label = 'Apply Grouping To Scheme'
    bl_description = "Create or extend a manual grouping scheme using the currently selected automatic grouping method"

    skip_default_group : BoolProperty(name='Skip Default Group', description='Do not assign faces to the default group when applying grouping to a new scheme', default=False)

    pack_op_type = PackOpType.PACK.code

    def send_unselected_islands(self):
        return False
    
    def get_script_container_id(self):
        return None

    def use_similarity_driver(self):
        return False

    def send_verts_3d(self):
        return False

    def send_verts_3d_global(self):
        return False

    def pre_operation(self):
        generated_g_scheme = self.init_g_scheme(self.grouping_config.group_method_prop.get(), self.skip_default_group)
        target_g_scheme = self.get_target_g_scheme()

        if self.create_new_g_scheme():
            target_g_scheme.copy_from(generated_g_scheme)
            target_g_scheme.name = self.target_scheme_name
            target_group_map = generated_g_scheme.group_map
            self.set_active_g_scheme_uuid(target_g_scheme.uuid)
        else:
            target_group_map = self.extend_g_scheme(target_g_scheme, generated_g_scheme)

        target_iparam_info = target_g_scheme.get_iparam_info()

        for target_group in target_g_scheme.groups:
            for p_obj in self.p_context.p_objects:
                p_obj_face_indcies = [f_idx for f_idx in p_obj.selected_faces_stored_indices if target_group_map.get_map(p_obj, f_idx) == target_group.num]
                p_obj.save_iparam(target_iparam_info, target_group.num, face_indicies=p_obj_face_indcies)

        self.grouping_config.group_method_prop.set(GroupingMethod.MANUAL.code)
        super().pre_operation()

    def extend_g_scheme(self, target_g_scheme, generated_g_scheme):
        groups_num_map = {}
        target_g_scheme.init_defaults()
        target_group_map = GroupMapManual(target_g_scheme, self.p_context)

        target_group_name_access = GroupByNameAccess(target_g_scheme)
        for generated_group in generated_g_scheme.groups:
            target_group = target_group_name_access.get(generated_group.name)
            groups_num_map[generated_group.num] = target_group.num

        generated_group_map = generated_g_scheme.group_map
        
        for face_idx, generated_group_num in enumerate(generated_group_map.map):
            if generated_group_num in groups_num_map:
                target_group_map.map[face_idx] = groups_num_map[generated_group_num]
                
        return target_group_map
    
    def target_scheme_name_impl(self, context):
        self.context = context
        grouping_config = self.get_mode().grouping_config
        group_method_label = grouping_config.group_method_prop.property_data().enum_items[grouping_config.group_method_prop.get()].name
        return "Scheme '{}'".format(group_method_label)
                
    def draw_impl(self, context, layout):
        if self.create_new_g_scheme():
            box = layout.box()
            row = box.row(align=True)
            row.prop(self, 'skip_default_group')

    def get_box_renderer(self):
        return None


# NUMBERED GROUP

class NumberedGroupsAccess:

    def __init__(self, context, desc_id):
        self.context = context
        self.desc_id = desc_id
        self.desc = getattr(get_scene_props(context).numbered_groups_descriptors, desc_id)
        self.g_scheme = None

    def get_g_scheme(self):
        assert (self.desc.use_g_scheme)
        if self.g_scheme is not None:
            return self.g_scheme
        
        g_scheme_access = GroupingSchemeAccess()
        g_scheme_access.init_access(self.context, desc_id=self.desc_id)
        self.g_scheme = g_scheme_access.get_active_g_scheme_safe()
        return self.g_scheme

    def groups_enabled(self):
        return self.get_enable_property().get()

    def get_iparam_info(self):
        if self.desc.use_g_scheme:
            return self.get_g_scheme().get_iparam_info()
        
        iparam_info = NumberedGroupIParamInfo()
        iparam_info.script_name = self.desc_id
        iparam_info.label = self.desc_id.replace('_', ' ').title()
        iparam_info.value_prop_obj = self.desc
        return iparam_info
    
    def get_iparam_serializer(self):
        if self.desc.use_g_scheme:
            return self.get_g_scheme().get_iparam_serializer()
        
        return VColorIParamSerializer(self.get_iparam_info())
    
    def get_enable_property(self):
        return PropertyWrapper(self.desc, 'enable')
        

class NumberedGroupsDescIdMixin:

    groups_desc_id : StringProperty(name='', default='')


class UVPM3_OT_NumberedGroupIParamGeneric:

    def execute_internal(self, context):
        self.groups_access = NumberedGroupsAccess(context, desc_id=self.groups_desc_id)
        return super().execute_internal(context)
    
    def get_iparam_info(self):
         return self.groups_access.get_iparam_info()


class UVPM3_OT_NumberedGroupShowIParam(UVPM3_OT_NumberedGroupIParamGeneric, UVPM3_OT_ShowIParam, NumberedGroupsDescIdMixin):

    bl_idname = 'uvpackmaster3.numbered_group_show_iparam'
    bl_label = 'Show Group Assignment'
    bl_description = "Show group numbers the selected islands are assigned to"


class UVPM3_OT_NumberedGroupSetIParam(UVPM3_OT_NumberedGroupIParamGeneric, UVPM3_OT_SetIParam, NumberedGroupsDescIdMixin):

    bl_idname = 'uvpackmaster3.numbered_group_set_iparam'
    bl_label = 'Assign Islands To Group'
    bl_description = "Assign the selected islands to the group determined by the 'Group Number' parameter"


class UVPM3_OT_NumberedGroupSetFreeIParam(UVPM3_OT_NumberedGroupIParamGeneric, UVPM3_OT_SetFreeIParam, NumberedGroupsDescIdMixin):

    bl_idname = 'uvpackmaster3.numbered_group_set_free_iparam'
    bl_label = 'Assign Islands To Free Group'
    bl_description = "Assign the selected islands to the first free group (the lowest group not currently used by faces in the UV map)"


class UVPM3_OT_NumberedGroupResetIParam(UVPM3_OT_NumberedGroupIParamGeneric, UVPM3_OT_ResetIParam, NumberedGroupsDescIdMixin):

    bl_idname = 'uvpackmaster3.numbered_group_reset_iparam'
    bl_label = 'Unset Groups'
    bl_description = "Unset the group assignment for the selected islands (the islands will not belong to any group)"


class UVPM3_OT_NumberedGroupSelectIParam(UVPM3_OT_NumberedGroupIParamGeneric, UVPM3_OT_SelectIParam, NumberedGroupsDescIdMixin):

    select : BoolProperty(name='', default=True)
    
    bl_idname = 'uvpackmaster3.numbered_group_select_iparam'
    bl_label = 'Select Islands Assigned To Group'
    bl_description = "Select / deselect all islands which are assigned to the group determined by the 'Group Number' parameter"


class UVPM3_OT_NumberedGroupSelectNonDefaultIParam(UVPM3_OT_NumberedGroupIParamGeneric, UVPM3_OT_SelectNonDefaultIParam, NumberedGroupsDescIdMixin):

    select : BoolProperty(name='', default=True)
    
    bl_idname = 'uvpackmaster3.numbered_group_select_non_default_iparam'
    bl_label = 'Select All Groups'
    bl_description = "Select all islands which are assigned to any group"


class IParamEditUI(PanelUtilsMixin):

    def __init__(self, context, scene_props, iparam_info_type, help_url_suffix=None):

        self.context = context
        self.scene_props = scene_props
        self.iparam_info_type = iparam_info_type
        self.help_url_suffix = help_url_suffix

        self.iparam_info = UVPM3_OT_StdIParamGeneric.get_iparam_info_impl(self.iparam_info_type)

    def draw(self, layout):

        col = layout.column(align=True)
        col.enabled = True

        row = col.row(align=True)
        row.prop(self.scene_props, self.iparam_info.VALUE_PROP_ID)

        if self.help_url_suffix is not None:
            self._draw_help_operator(row, self.help_url_suffix)

        op_name_suffix = '' if get_prefs().short_island_operator_names else ' ' + self.iparam_info.LABEL

        row = col.row(align=True)
        op = row.operator(UVPM3_OT_StdSetIParam.bl_idname, text='Set' + op_name_suffix)
        op.iparam_info_type = self.iparam_info_type

        col.separator()
        row = col.row(align=True)
        op = row.operator(UVPM3_OT_StdResetIParam.bl_idname, text='Reset' + op_name_suffix)
        op.iparam_info_type = self.iparam_info_type

        row = col.row(align=True)
        op = row.operator(UVPM3_OT_StdShowIParam.bl_idname, text='Show' + op_name_suffix)
        op.iparam_info_type = self.iparam_info_type

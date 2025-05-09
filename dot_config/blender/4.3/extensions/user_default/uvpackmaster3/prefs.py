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

import os
import multiprocessing
from pathlib import Path
from collections import namedtuple

from .enums import *
from .utils import get_active_image_size, PanelUtilsMixin
from .prefs_scripted_utils import scripted_pipeline_property_group
from .labels import Labels
from .contansts import *
from .mode import ModeType
from .grouping_scheme import UVPM3_GroupingScheme, UVPM3_GroupingSchemeAccessDescriptorContainer
from .box import UVPM3_Box
from .box_utils import disable_box_rendering
from .island_params import AlignPriorityIParamInfo, NormalizeMultiplierIParamInfo
from .register_utils import UVPM3_OT_SetEnginePath
from .grouping import UVPM3_AutoGroupingOptions
from .operator_islands import NumberedGroupIParamInfo
from .multi_panel import UVPM3_SavedMultiPanelSettings
from .multi_panel_manager import UVPM3_SavedPanelSettings
from .scripting import UVPM3_Scripting
from . import module_loader
from .props import UVPM3_TrackGroupsProps, UVPM3_PackStrategyProps
from .app_iface import *
from .pgroup import standalone_property_group
from .panel import PanelUtilsMixin

from .scripted_pipeline import properties
scripted_properties_modules = module_loader.import_submodules(properties)
scripted_properties_classes = module_loader.get_registrable_classes(scripted_properties_modules,
                                                                    sub_class=PropertyGroup,
                                                                    required_vars=("SCRIPTED_PROP_GROUP_ID",))

@standalone_property_group
class UVPM3_DeviceSettings:

    enabled : BoolProperty(name='enabled', default=True)


DeviceMetadata = namedtuple('DeviceMetadata', ('enabled_default', 'help_url_suffix'), defaults=(None, None))


@standalone_property_group
class UVPM3_SavedDeviceSettings:

    DEVICE_METADATA = [
        ('vulkan_', DeviceMetadata(
                        enabled_default=False,
                        help_url_suffix='48-other-topics/20-vulkan-gpu-acceleration')
        )
    ]

    dev_id : StringProperty(name="", default="")
    settings : PointerProperty(type=UVPM3_DeviceSettings)
    
    def get_metadata(self):
        for id_prefix, metadata in self.DEVICE_METADATA:
            if self.dev_id.startswith(id_prefix):
                return metadata
            
        return DeviceMetadata()

    def init(self, dev_id):
        self.dev_id = dev_id
        metadata = self.get_metadata()

        if metadata.enabled_default is not None:
            self.settings.enabled = metadata.enabled_default


def _update_active_main_mode_id(self, context):

    disable_box_rendering(None, context)


def _update_orient_3d_axes(self, context):
    if self.orient_prim_3d_axis == self.orient_sec_3d_axis:
        enum_values = AppInterface.object_property_data(self)["orient_sec_3d_axis"].enum_items_static.keys()
        value_index = enum_values.index(self.orient_sec_3d_axis)
        self.orient_sec_3d_axis = enum_values[(value_index+1) % len(enum_values)]


class UVPM3_NumberedGroupsDescriptor(PropertyGroup):

    enable : BoolProperty(
        name=Labels.GROUPS_ENABLE_NAME,
        description=Labels.GROUPS_ENABLE_DESC,
        default=False)

    group_num : IntProperty(
        name=Labels.GROUP_NUM_NAME,
        description=Labels.GROUP_NUM_DESC,
        default=NumberedGroupIParamInfo.MIN_VALUE+1,
        min=NumberedGroupIParamInfo.MIN_VALUE+1,
        max=NumberedGroupIParamInfo.MAX_VALUE)

    use_g_scheme : BoolProperty(
        name='Use Grouping Scheme',
        description='Use a grouping scheme to define groups',
        default=False
    )


class UVPM3_NumberedGroupsDescriptorContainer(PropertyGroup):

    lock_group : PointerProperty(type=UVPM3_NumberedGroupsDescriptor)
    stack_group : PointerProperty(type=UVPM3_NumberedGroupsDescriptor)
    track_group : PointerProperty(type=UVPM3_NumberedGroupsDescriptor)
    

class UVPM3_SceneProps(PropertyGroup):

    saved_m_panel_settings : CollectionProperty(type=UVPM3_SavedMultiPanelSettings)
    saved_panel_settings : CollectionProperty(type=UVPM3_SavedPanelSettings)
    grouping_schemes : CollectionProperty(name="Grouping Schemes", type=UVPM3_GroupingScheme)
    grouping_scheme_access_descriptors : PointerProperty(type=UVPM3_GroupingSchemeAccessDescriptorContainer)

    numbered_groups_descriptors : PointerProperty(type=UVPM3_NumberedGroupsDescriptorContainer)

    track_groups_props : PointerProperty(type=UVPM3_TrackGroupsProps)
    scripting : PointerProperty(type=UVPM3_Scripting)

    pack_strategy_props : PointerProperty(type=UVPM3_PackStrategyProps)

    precision : IntProperty(
        name=Labels.PRECISION_NAME,
        description=Labels.PRECISION_DESC,
        default=500,
        min=10,
        max=10000)

    margin : FloatProperty(
        name=Labels.MARGIN_NAME,
        description=Labels.MARGIN_DESC,
        min=0.0,
        max=0.2,
        default=0.003,
        precision=3,
        step=0.1)

    pixel_margin_enable : BoolProperty(
        name=Labels.PIXEL_MARGIN_ENABLE_NAME,
        description=Labels.PIXEL_MARGIN_ENABLE_DESC,
        default=False)

    pixel_margin : def_prop__pixel_margin()
    pixel_border_margin : def_prop__pixel_border_margin()
    extra_pixel_margin_to_others : def_prop__extra_pixel_margin_to_others()
    pixel_margin_tex_size : def_prop__pixel_margin_tex_size()
    pixel_perfect_align : def_prop__pixel_perfect_align()
    pixel_perfect_vert_align_mode : EnumProperty(
        items=UvpmPixelPerfectVertAlignMode.to_blend_items(),
        name=Labels.PIXEL_PERFECT_VERT_ALIGN_MODE_NAME,
        description=Labels.PIXEL_PERFECT_VERT_ALIGN_MODE_DESC)

    rotation_enable : BoolProperty(
        name=Labels.ROTATION_ENABLE_NAME,
        description=Labels.ROTATION_ENABLE_DESC,
        default=PropConstants.ROTATION_ENABLE_DEFAULT)

    pre_rotation_disable : BoolProperty(
        name=Labels.PRE_ROTATION_DISABLE_NAME,
        description=Labels.PRE_ROTATION_DISABLE_DESC,
        default=PropConstants.PRE_ROTATION_DISABLE_DEFAULT)

    flipping_enable : BoolProperty(
        name=Labels.FLIPPING_ENABLE_NAME,
        description=Labels.FLIPPING_ENABLE_DESC,
        default=PropConstants.FLIPPING_ENABLE_DEFAULT)

    normalize_scale : BoolProperty(
        name=Labels.NORMALIZE_SCALE_NAME,
        description=Labels.NORMALIZE_SCALE_DESC,
        default=False)
    
    normalize_space : EnumProperty(
        items=UvpmCoordSpace.to_blend_items(),
        name=Labels.NORMALIZE_SPACE_NAME,
        description=Labels.NORMALIZE_SPACE_DESC)
    
    island_normalize_multiplier_enable : BoolProperty(
        name=Labels.ISLAND_NORMALIZE_MULTIPLIER_ENABLE_NAME,
        description=Labels.ISLAND_NORMALIZE_MULTIPLIER_ENABLE_DESC,
        default=False)
    
    island_normalize_multiplier : IntProperty(
        name=Labels.ISLAND_NORMALIZE_MULTIPLIER_NAME,
        description=Labels.ISLAND_NORMALIZE_MULTIPLIER_DESC,
        default=NormalizeMultiplierIParamInfo.DEFAULT_VALUE,
        min=NormalizeMultiplierIParamInfo.MIN_VALUE,
        max=NormalizeMultiplierIParamInfo.MAX_VALUE)

    scale_mode : def_prop__scale_mode()

    rotation_step : IntProperty(
        name=Labels.ROTATION_STEP_NAME,
        description=Labels.ROTATION_STEP_DESC,
        default=PropConstants.ROTATION_STEP_DEFAULT,
        min=PropConstants.ROTATION_STEP_MIN,
        max=PropConstants.ROTATION_STEP_MAX)

    island_rot_step_enable : BoolProperty(
        name=Labels.ISLAND_ROT_STEP_ENABLE_NAME,
        description=Labels.ISLAND_ROT_STEP_ENABLE_DESC,
        default=False)

    island_rot_step : IntProperty(
        name=Labels.ISLAND_ROT_STEP_NAME,
        description=Labels.ISLAND_ROT_STEP_DESC,
        default=90,
        min=0,
        max=180)

    tex_ratio : BoolProperty(
        name=Labels.TEX_RATIO_NAME,
        description=Labels.TEX_RATIO_DESC,
        default=False)


    def get_main_mode_blend_enums(scene, context):
        prefs = get_prefs()
        modes_info = prefs.get_modes(ModeType.MAIN)

        return [(mode_id, mode_cls.enum_name(), "") for mode_id, mode_cls in modes_info]

    active_main_mode_id : EnumProperty(
        items=get_main_mode_blend_enums,
        update=_update_active_main_mode_id,
        name=Labels.PACK_MODE_NAME,
        description=Labels.PACK_MODE_DESC)

    group_method : EnumProperty(
        items=GroupingMethod.to_blend_items(),
        name=Labels.GROUP_METHOD_NAME,
        description=Labels.GROUP_METHOD_DESC,
        update=disable_box_rendering)

    auto_group_options : PointerProperty(type=UVPM3_AutoGroupingOptions)

    editor_group_method : EnumProperty(
        items=GroupingMethod.to_blend_items(),
        name="{} (Editor)".format(Labels.GROUP_METHOD_NAME),
        description=Labels.GROUP_METHOD_DESC,
        default=GroupingMethod.MANUAL.code,
        update=disable_box_rendering)

    use_blender_tile_grid : BoolProperty(
        name=Labels.USE_BLENDER_TILE_GRID_NAME,
        description=Labels.USE_BLENDER_TILE_GRID_DESC,
        default=False)

    lock_overlapping_enable : BoolProperty(
        name=Labels.LOCK_OVERLAPPING_ENABLE_NAME,
        description=Labels.LOCK_OVERLAPPING_ENABLE_DESC,
        default=False)

    lock_overlapping_mode : EnumProperty(
        items=UvpmOverlapDetectionMode.to_blend_items(),
        name=Labels.LOCK_OVERLAPPING_MODE_NAME,
        description=Labels.LOCK_OVERLAPPING_MODE_DESC)

    heuristic_enable : BoolProperty(
        name=Labels.HEURISTIC_ENABLE_NAME,
        description=Labels.HEURISTIC_ENABLE_DESC,
        default=False)

    heuristic_search_time : IntProperty(
        name=Labels.HEURISTIC_SEARCH_TIME_NAME,
        description=Labels.HEURISTIC_SEARCH_TIME_DESC,
        default=0,
        min=0,
        max=3600)

    heuristic_max_wait_time : IntProperty(
        name=Labels.HEURISTIC_MAX_WAIT_TIME_NAME,
        description=Labels.HEURISTIC_MAX_WAIT_TIME_DESC,
        default=0,
        min=0,
        max=300)
        
    heuristic_allow_mixed_scales : BoolProperty(
        name=Labels.HEURISTIC_ALLOW_MIXED_SCALES_NAME,
        description=Labels.HEURISTIC_ALLOW_MIXED_SCALES_DESC,
        default=False)
    
    advanced_heuristic : BoolProperty(
        name=Labels.ADVANCED_HEURISTIC_NAME,
        description=Labels.ADVANCED_HEURISTIC_DESC,
        default=False)

    fully_inside : BoolProperty(
        name=Labels.FULLY_INSIDE_NAME,
        description=Labels.FULLY_INSIDE_DESC,
        default=True)

    custom_target_box_enable : BoolProperty(
        name=Labels.CUSTOM_TARGET_BOX_ENABLE_NAME,
        description=Labels.CUSTOM_TARGET_BOX_ENABLE_DESC,
        default=False,
        update=disable_box_rendering)

    custom_target_box : PointerProperty(type=UVPM3_Box)

    tile_count_x : IntProperty(
        name=Labels.TILE_COUNT_X_NAME,
        description=Labels.TILE_COUNT_X_DESC,
        default=PropConstants.TILE_COUNT_XY_DEFAULT,
        min=PropConstants.TILE_COUNT_XY_MIN,
        max=PropConstants.TILE_COUNT_XY_MAX)

    tile_count_y : IntProperty(
        name=Labels.TILE_COUNT_Y_NAME,
        description=Labels.TILE_COUNT_Y_DESC,
        default=PropConstants.TILE_COUNT_XY_DEFAULT,
        min=PropConstants.TILE_COUNT_XY_MIN,
        max=PropConstants.TILE_COUNT_XY_MAX)
    
    tile_filling_method : EnumProperty(
        items=UvpmTileFillingMethod.to_blend_items(),
        name=Labels.TILE_FILLING_METHOD_NAME,
        description=Labels.TILE_FILLING_METHOD_DESC)


    # ------ Aligning properties ------ #

    simi_mode : EnumProperty(
        items=UvpmSimilarityMode.to_blend_items(),
        name=Labels.SIMI_MODE_NAME,
        description=Labels.SIMI_MODE_DESC)

    simi_threshold : FloatProperty(
        name=Labels.SIMI_THRESHOLD_NAME,
        description=Labels.SIMI_THRESHOLD_DESC,
        default=0.1,
        min=0.0,
        precision=2,
        step=5.0)
    
    simi_check_holes : BoolProperty(
        name=Labels.SIMI_CHECK_HOLES_NAME,
        description=Labels.SIMI_CHECK_HOLES_DESC,
        default=False)

    simi_adjust_scale : BoolProperty(
        name=Labels.SIMI_ADJUST_SCALE_NAME,
        description=Labels.SIMI_ADJUST_SCALE_DESC,
        default=False)
    
    simi_non_uniform_scaling_tolerance : FloatProperty(
        name=Labels.SIMI_NON_UNIFORM_SCALING_TOLERANCE_NAME,
        description=Labels.SIMI_NON_UNIFORM_SCALING_TOLERANCE_DESC,
        default=0.0,
        min=0.0,
        max=1.0,
        precision=2,
        step=2.0)

    simi_match_3d_axis : EnumProperty(
        items=UvpmAxis.to_blend_items(include_none=True, only_positive=True),
        name=Labels.SIMI_MATCH_3D_AXIS_NAME,
        description=Labels.SIMI_MATCH_3D_AXIS_DESC)

    simi_match_3d_axis_space : EnumProperty(
        items=UvpmCoordSpace.to_blend_items(),
        name=Labels.SIMI_MATCH_3D_AXIS_SPACE_NAME,
        description=Labels.SIMI_MATCH_3D_AXIS_SPACE_DESC)

    simi_correct_vertices : BoolProperty(
        name=Labels.SIMI_CORRECT_VERTICES_NAME,
        description=Labels.SIMI_CORRECT_VERTICES_DESC,
        default=False)

    simi_vertex_threshold : FloatProperty(
        name=Labels.SIMI_VERTEX_THRESHOLD_NAME,
        description=Labels.SIMI_VERTEX_THRESHOLD_DESC,
        default=0.01,
        min=0.0,
        max=0.05,
        precision=4,
        step=1.0e-1)

    align_priority_enable : BoolProperty(
        name=Labels.ALIGN_PRIORITY_ENABLE_NAME,
        description=Labels.ALIGN_PRIORITY_ENABLE_DESC,
        default=False)

    align_priority : IntProperty(
        name=Labels.ALIGN_PRIORITY_NAME,
        description=Labels.ALIGN_PRIORITY_DESC,
        default=int(AlignPriorityIParamInfo.DEFAULT_VALUE),
        min=int(AlignPriorityIParamInfo.MIN_VALUE),
        max=int(AlignPriorityIParamInfo.MAX_VALUE))

    split_overlap_detection_mode : EnumProperty(
        items=UvpmOverlapDetectionMode.to_blend_items(),
        name=Labels.SPLIT_OVERLAP_DETECTION_MODE_NAME,
        description=Labels.SPLIT_OVERLAP_DETECTION_MODE_DESC)
    
    split_overlap_max_tile_x : IntProperty(
        name=Labels.SPLIT_OVERLAP_MAX_TILE_X_NAME,
        description=Labels.SPLIT_OVERLAP_MAX_TILE_X_DESC,
        default = 0,
        min = 0)

    orient_prim_3d_axis : EnumProperty(
        items=UvpmAxis.to_blend_items(include_none=False, only_positive=True),
        default=PropConstants.ORIENT_PRIM_3D_AXIS_DEFAULT,
        update=_update_orient_3d_axes,
        name=Labels.ORIENT_PRIM_3D_AXIS_NAME,
        description=Labels.ORIENT_PRIM_3D_AXIS_DESC)

    orient_prim_uv_axis : EnumProperty(
        items=UvpmAxis.to_blend_items(include_none=False, only_2d=True),
        default=PropConstants.ORIENT_PRIM_UV_AXIS_DEFAULT,
        name=Labels.ORIENT_PRIM_UV_AXIS_NAME,
        description=Labels.ORIENT_PRIM_UV_AXIS_DESC)

    orient_sec_3d_axis : EnumProperty(
        items=UvpmAxis.to_blend_items(include_none=False, only_positive=True),
        default=PropConstants.ORIENT_SEC_3D_AXIS_DEFAULT,
        update=_update_orient_3d_axes,
        name=Labels.ORIENT_SEC_3D_AXIS_NAME,
        description=Labels.ORIENT_SEC_3D_AXIS_DESC)

    orient_sec_uv_axis : EnumProperty(
        items=UvpmAxis.to_blend_items(include_none=False, only_2d=True),
        default=PropConstants.ORIENT_SEC_UV_AXIS_DEFAULT,
        name=Labels.ORIENT_SEC_UV_AXIS_NAME,
        description=Labels.ORIENT_SEC_UV_AXIS_DESC)

    orient_to_3d_axes_space : EnumProperty(
        items=UvpmCoordSpace.to_blend_items(),
        name=Labels.ORIENT_TO_3D_AXES_SPACE_NAME,
        description=Labels.ORIENT_TO_3D_AXES_SPACE_DESC)

    orient_prim_sec_bias : IntProperty(
        name=Labels.ORIENT_PRIM_SEC_BIAS_NAME,
        description=Labels.ORIENT_PRIM_SEC_BIAS_DESC,
        default=PropConstants.ORIENT_PRIM_SEC_BIAS_DEFAULT,
        min=0,
        max=90)


@addon_preferences
class UVPM3_Preferences(PanelUtilsMixin):
    bl_idname = __package__

    MAX_TILES_IN_ROW = 1000
    INCONSISTENT_ISLANDS_HELP_URL_SUFFIX = '/48-other-topics/5-inconsistent-islands-error-handling/'

    modes_dict = None

    def pixel_margin_enabled(self, scene_props):
        return scene_props.pixel_margin_enable

    def extra_pixel_margin_to_others_enabled(self, scene_props):
        return scene_props.extra_pixel_margin_to_others > 0

    def pixel_border_margin_enabled(self, scene_props):
        return scene_props.pixel_border_margin > 0

    def heuristic_enabled(self, scene_props):
        return scene_props.heuristic_enable

    def heuristic_timeout_enabled(self, scene_props):
        return self.heuristic_enabled(scene_props) and scene_props.heuristic_search_time > 0

    def advanced_heuristic_available(self, scene_props):
        return self.FEATURE_advanced_heuristic and self.heuristic_enabled(scene_props)

    def pack_ratio_supported(self):
        return self.FEATURE_pack_ratio and self.FEATURE_target_box

    def pack_ratio_enabled(self, scene_props):
        return self.pack_ratio_supported() and scene_props.tex_ratio

    def pixel_margin_tex_size(self, scene_props, context):
        if self.pack_ratio_enabled(scene_props):
            img_size = get_active_image_size(context)
            tex_size = img_size[1]
        else:
            tex_size = scene_props.pixel_margin_tex_size

        return tex_size

    def fixed_scale_enabled(self, scene_props):
        return UvpmScaleMode.fixed_scale_enabled(scene_props.scale_mode)

    def normalize_scale_not_supported_msg(self, scene_props):
        return None
    
    def heuristic_allow_mixed_scales_not_supported_msg(self, scene_props):
        return None
    
    def tile_filling_method_not_supported_msg(self, scene_props):      
        return None

    def reset_box_params(self):
        self.box_rendering = False
        self.group_scheme_boxes_editing = False
        self.custom_target_box_editing = False
        self.boxes_dirty = False

    def reset_feature_codes(self):
        self.FEATURE_demo = False
        self.FEATURE_island_rotation = True
        self.FEATURE_overlap_check = True
        self.FEATURE_packing_depth = True
        self.FEATURE_heuristic_search = True
        self.FEATURE_pack_ratio = True
        self.FEATURE_pack_to_others = True
        self.FEATURE_grouping = True
        self.FEATURE_lock_overlapping = True
        self.FEATURE_advanced_heuristic = True
        self.FEATURE_self_intersect_processing = True
        self.FEATURE_validation = True
        self.FEATURE_multi_device_pack = True
        self.FEATURE_target_box = True
        self.FEATURE_island_rotation_step = True
        self.FEATURE_pack_to_tiles = True

    def reset_stats(self):

        for dev in self.device_array():
            dev.reset()

    def reset(self):
        self.engine_path = ''
        self.enabled = True
        self.engine_initialized = False
        self.engine_status_msg = ''
        self.thread_count = multiprocessing.cpu_count()
        self.operation_counter = -1
        self.write_to_file = False
        self.seed = 0

        self.enable_vulkan_saved = self.enable_vulkan

        self.reset_stats()
        self.reset_device_array()
        self.reset_box_params()
        self.reset_feature_codes()

    def draw_engine_status(self, layout):
        row = layout.row(align=True)
        self.draw_engine_status_message(row, icon_only=False)
        self.draw_engine_status_help_button(row)

    def draw_engine_status_message(self, layout, icon_only):
        icon = 'ERROR' if not self.engine_initialized else 'NONE'
        layout.label(text="" if icon_only else self.engine_status_msg, icon=icon)

    def draw_engine_status_help_button(self, layout):
        if not self.engine_initialized:
            from .help import UVPM3_OT_SetupHelp
            layout.operator(UVPM3_OT_SetupHelp.bl_idname, icon='QUESTION', text='')

    def draw_addon_preferences(self, layout):
        col = layout.column(align=True)
        col.label(text='General options:')

        row = col.row(align=True)
        row.prop(self, "thread_count")

        box = col.box()
        row = box.row(align=True)
        row.prop(self, 'orient_aware_uv_islands')

        from .panel import UVPM3_PT_Generic
        box = col.box()
        UVPM3_PT_Generic.prop_with_help(self, 'allow_inconsistent_islands', box, help_url_suffix=self.INCONSISTENT_ISLANDS_HELP_URL_SUFFIX)

        box = col.box()
        row = box.row(align=True)
        row.prop(self, 'dont_transform_pinned_uvs')

        if self.dont_transform_pinned_uvs:
            box = col.box()
            row = box.row(align=True)
            row.prop(self, 'pinned_uvs_as_others')
        
        col.separator()
        col.label(text='UI options:')

        box = col.box()
        row = box.row(align=True)
        row.prop(self, 'hori_multi_panel_toggles')

        box = col.box()
        row = box.row(align=True)
        row.prop(self, 'append_mode_name_to_op_label')

        box = col.box()
        row = box.row(align=True)
        row.prop(self, "disable_tips")

        row = col.row(align=True)
        row.prop(self, "font_size_text_output")

        row = col.row(align=True)
        row.prop(self, "font_size_uv_overlay")

        row = col.row(align=True)
        row.prop(self, "box_render_line_width")
        
        box = col.box()
        row = box.row(align=True)
        row.prop(self, "short_island_operator_names")

        self.draw_prop_saved_state(self, 'enable_vulkan', col.box())

        # adv_op_box = col.box()
        adv_op_layout = col # adv_op_box.column(align=True)
        adv_op_layout.separator()
        adv_op_layout.label(text='Expert options:')

        UVPM3_OT_ShowHideAdvancedOptions.draw_operator(adv_op_layout)
        if self.show_expert_options:
            box = adv_op_layout.box()
            box.label(text='Change expert options only if you really know what you are doing.', icon='ERROR')

            box = adv_op_layout.box()
            row = box.row(align=True)
            row.prop(self, 'disable_immediate_uv_update')

        col.separator()
        col.separator()

        col.label(text='Packing devices:')
        dev_main = col.column(align=True)

        dev_factors = (0.8,)
        dev_cols = self.create_split_columns(dev_main.box(), factors=dev_factors)

        dev_cols[0].label(text='Name')
        dev_cols[1].label(text='Enabled')

        dev_cols = self.create_split_columns(dev_main.box(), factors=dev_factors)

        for dev in self.device_array():
            settings = dev.settings
            row = dev_cols[0].row()
            row.label(text=dev.name)

            row = dev_cols[1].row()
            row.prop(settings, 'enabled', text='')

            help_url_suffix = dev.help_url_suffix()

            if help_url_suffix is not None:
                self._draw_help_operator(row, help_url_suffix)

        save_operator = AppInterface.save_preferences_operator()
        if save_operator:
            col.separator()
            col.operator(save_operator.bl_idname)

    def draw(self, context):
        layout = self.layout

        # main_box = layout.box()
        main_col = layout.column(align=True)
        main_col.label(text='Engine status:')
        box = main_col.box()
        self.draw_engine_status(box)

        col = box.column(align=True)
        row = col.row(align=True)
        row.label(text="Path to the UVPM engine:")
        row = col.row(align=True)
        row.enabled = False
        row.prop(self, 'engine_path')

        row = col.row(align=True)
        row.operator(UVPM3_OT_SetEnginePath.bl_idname)

        main_col.separator()
        main_col.separator()

        self.draw_addon_preferences(main_col)

    def get_engine_args(self):
        args = []

        if self.enable_vulkan:
            args.append('-v')

        return args

    def get_mode(self, mode_id, context):
        if self.modes_dict is None:
            raise RuntimeError("Mods are not initialized.")
        try:
            return next(m(context) for m_list in self.modes_dict.values() for (m_id, m) in m_list if m_id == mode_id)
        except StopIteration:
            raise KeyError("The '{}' mode not found".format(mode_id))

    def get_modes(self, mode_type):
        return self.modes_dict[mode_type]

    def get_active_main_mode(self, context):
        try:
            return self.get_mode(get_scene_props(context).active_main_mode_id, context)
        except KeyError:
            pass

        from .scripted_pipeline.modes.pack_modes import UVPM3_Mode_SingleTile
        return self.get_mode(UVPM3_Mode_SingleTile.MODE_ID, context)

    def set_active_main_mode(self, context, mode_id):
        get_scene_props(context).active_main_mode_id = mode_id

    # Supporeted features
    FEATURE_demo : BoolProperty(
        name='',
        description='',
        default=False)

    FEATURE_island_rotation : BoolProperty(
        name='',
        description='',
        default=False)

    FEATURE_overlap_check : BoolProperty(
        name='',
        description='',
        default=False)

    FEATURE_packing_depth : BoolProperty(
        name='',
        description='',
        default=False)

    FEATURE_heuristic_search : BoolProperty(
        name='',
        description='',
        default=False)

    FEATURE_advanced_heuristic : BoolProperty(
        name='',
        description='',
        default=False)

    FEATURE_pack_ratio : BoolProperty(
        name='',
        description='',
        default=False)

    FEATURE_pack_to_others : BoolProperty(
        name='',
        description='',
        default=False)

    FEATURE_grouping : BoolProperty(
        name='',
        description='',
        default=False)

    FEATURE_lock_overlapping : BoolProperty(
        name='',
        description='',
        default=False)

    FEATURE_self_intersect_processing : BoolProperty(
        name='',
        description='',
        default=False)

    FEATURE_validation : BoolProperty(
        name='',
        description='',
        default=False)

    FEATURE_multi_device_pack : BoolProperty(
        name='',
        description='',
        default=False)

    FEATURE_target_box : BoolProperty(
        name='',
        description='',
        default=False)

    FEATURE_island_rotation_step : BoolProperty(
        name='',
        description='',
        default=False)

    FEATURE_pack_to_tiles : BoolProperty(
        name='',
        description='',
        default=False)

    operation_counter : IntProperty(
        name='',
        description='',
        default=-1)

    box_rendering : BoolProperty(
        name='',
        description='',
        default=False)

    boxes_dirty : BoolProperty(
        name='',
        description='',
        default=False)

    group_scheme_boxes_editing : BoolProperty(
        name='',
        description='',
        default=False)

    custom_target_box_editing : BoolProperty(
        name='',
        description='',
        default=False)

    engine_retcode : IntProperty(
        name='',
        description='',
        default=0)

    engine_path : StringProperty(
        name='',
        description='',
        default='')

    engine_initialized : BoolProperty(
        name='',
        description='',
        default=False)

    engine_status_msg : StringProperty(
        name='',
        description='',
        default='')
        # update=_update_engine_status_msg)

    thread_count : IntProperty(
        name=Labels.THREAD_COUNT_NAME,
        description=Labels.THREAD_COUNT_DESC,
        default=multiprocessing.cpu_count(),
        min=1,
        max=multiprocessing.cpu_count())

    seed : IntProperty(
        name=Labels.SEED_NAME,
        description='',
        default=0,
        min=0,
        max=10000)

    test_param : IntProperty(
        name=Labels.TEST_PARAM_NAME,
        description='',
        default=0,
        min=0,
        max=10000)

    write_to_file : BoolProperty(
        name=Labels.WRITE_TO_FILE_NAME,
        description='',
        default=False)

    wait_for_debugger : BoolProperty(
        name=Labels.WAIT_FOR_DEBUGGER_NAME,
        description='',
        default=False)
    
    hori_multi_panel_toggles : BoolProperty(
        name=Labels.HORI_MULTI_PANEL_TOGGLES_NAME,
        description=Labels.HORI_MULTI_PANEL_TOGGLES_DESC,
        default=False)

    append_mode_name_to_op_label : BoolProperty(
        name=Labels.APPEND_MODE_NAME_TO_OP_LABEL_NAME,
        description=Labels.APPEND_MODE_NAME_TO_OP_LABEL_DESC,
        default=False)

    orient_aware_uv_islands : BoolProperty(
        name=Labels.ORIENT_AWARE_UV_ISLANDS_NAME,
        description=Labels.ORIENT_AWARE_UV_ISLANDS_DESC,
        default=False)

    allow_inconsistent_islands : BoolProperty(
        name=Labels.ALLOW_INCONSISTENT_ISLANDS_NAME,
        description=Labels.ALLOW_INCONSISTENT_ISLANDS_DESC,
        default=False)
    
    dont_transform_pinned_uvs : BoolProperty(
        name=Labels.DONT_TRANSFORM_PINNED_UVS_NAME,
        description=Labels.DONT_TRANSFORM_PINNED_UVS_DESC,
        default=True)
    
    pinned_uvs_as_others : BoolProperty(
        name=Labels.PINNED_UVS_AS_OTHERS_NAME,
        description=Labels.PINNED_UVS_AS_OTHERS_DESC,
        default=True)
    
    enable_vulkan : BoolProperty(
        name='Enable Vulkan',
        description='Enable Vulkan devices for packing (if available in the system)',
        default=True
    )

    enable_vulkan_saved : BoolProperty(
        name='',
        default=True
    )

    # UI options
    disable_tips : BoolProperty(
        name=Labels.DISABLE_TIPS_NAME,
        description=Labels.DISABLE_TIPS_DESC,
        default=False)

    font_size_text_output : IntProperty(
        name=Labels.FONT_SIZE_TEXT_OUTPUT_NAME,
        description=Labels.FONT_SIZE_TEXT_OUTPUT_DESC,
        default=15,
        min=5,
        max=100)

    font_size_uv_overlay : IntProperty(
        name=Labels.FONT_SIZE_UV_OVERLAY_NAME,
        description=Labels.FONT_SIZE_UV_OVERLAY_DESC,
        default=20,
        min=5,
        max=100)

    box_render_line_width : FloatProperty(
        name=Labels.BOX_RENDER_LINE_WIDTH_NAME,
        description=Labels.BOX_RENDER_LINE_WIDTH_DESC,
        default=4.0,
        min=1.0,
        max=10.0,
        step=5.0)
    
    short_island_operator_names : BoolProperty(
        name=Labels.SHORT_ISLAND_OPERATOR_NAMES_NAME,
        description=Labels.SHORT_ISLAND_OPERATOR_NAMES_DESC,
        default=False)

    # Expert options
    show_expert_options : BoolProperty(
        name=Labels.SHOW_EXPERT_OPTIONS_NAME,
        description=Labels.SHOW_EXPERT_OPTIONS_DESC,
        default=False
    )

    disable_immediate_uv_update : BoolProperty(
        name=Labels.DISABLE_IMMEDIATE_UV_UPDATE_NAME,
        description=Labels.DISABLE_IMMEDIATE_UV_UPDATE_DESC,
        default=False
    )

    # Dismissed warnings options

    pixel_margin_warn_dismissed : BoolProperty(
        name='Pixel Margin Warning Dismissed',
        default=False
    )

    multi_panel_manager = None

    script_allow_execution : BoolProperty(name='Allow Script Execution', default=False)

    def get_multi_panel_manager(self, context):
        if type(self).multi_panel_manager is None:
            from .multi_panel_manager import MultiPanelManager
            type(self).multi_panel_manager = MultiPanelManager()

        mp_manager = type(self).multi_panel_manager
        mp_manager.update_settings(get_scene_props(context))
        return mp_manager

    dev_array = []
    saved_dev_settings : CollectionProperty(type=UVPM3_SavedDeviceSettings)

    def device_array(self):
        return type(self).dev_array

    def reset_device_array(self):
        type(self).dev_array = []

    @classmethod
    def get_userdata_path(cls):
        from .os_iface import os_get_userdata_path
        os_userdata_path = os_get_userdata_path()
        path = os.path.join(os_userdata_path, AppInterface.APP_ID, 'engine3')
        Path(path).mkdir(parents=True, exist_ok=True)
        return path

    @classmethod
    def get_main_preset_path(cls):
        preset_path = os.path.join(cls.get_userdata_path(), 'presets')
        Path(preset_path).mkdir(parents=True, exist_ok=True)
        return preset_path

    @classmethod
    def get_g_schemes_preset_path(cls):
        preset_path = os.path.join(cls.get_userdata_path(), 'grouping_schemes')
        Path(preset_path).mkdir(parents=True, exist_ok=True)
        return preset_path

    @classmethod
    def get_preferences_filepath(cls):
        return os.path.join(cls.get_userdata_path(), 'prefs.json')
    

@scripted_pipeline_property_group("scripted_props",
                                  UVPM3_SceneProps, scripted_properties_classes,
                                  (UVPM3_SceneProps, UVPM3_Preferences))
class UVPM3_ScriptedPipelineProperties(PropertyGroup):
    pass


class UVPM3_OT_ShowHideAdvancedOptions(Operator):

    bl_label = 'Show Expert Options'
    bl_idname = 'uvpackmaster3.show_hide_expert_options'

    @staticmethod
    def get_label():
        prefs = get_prefs()
        return 'Hide Expert Options' if prefs.show_expert_options else 'Show Expert Options'

    @classmethod
    def draw_operator(cls, layout):
        layout.operator(cls.bl_idname, text=cls.get_label())

    def draw(self, context):
        layout = self.layout
        col = layout.column()

        for label in self.confirmation_labels:
            col.label(text=label)

    def execute(self, context):
        prefs = get_prefs()
        prefs.show_expert_options = not prefs.show_expert_options

        from .utils import redraw_ui
        redraw_ui(context)

        return {'FINISHED'}

    def invoke(self, context, event):
        prefs = get_prefs()

        if not prefs.show_expert_options:
            self.confirmation_labels =\
                [ 'WARNING: expert options should NEVER be changed under the standard packer usage.',
                  'You should only change them if you really know what you are doing.',
                  'Are you sure you want to show the expert options?' ]

            wm = context.window_manager
            return wm.invoke_props_dialog(self, width=700)

        return self.execute(context)

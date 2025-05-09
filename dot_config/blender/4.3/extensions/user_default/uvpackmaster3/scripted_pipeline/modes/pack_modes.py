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

from ...operator_box import GroupingSchemeRenderAccess
from ...prefs_scripted_utils import ScriptParams
from ...mode import UVPM3_Mode_Main, UVPM3_ModeCategory_Packing, OperatorMetadata
from ..operators.pack_operator import UVPM3_OT_Pack
from ...box import UVPM3_Box, DEFAULT_TARGET_BOX
from ...box_utils import BoxRenderer, BoxArrayRenderAccess, CustomTargetBoxAccess
from ...island_params import NormalizeMultiplierIParamInfo, VColorIParamSerializer, RotStepIParamInfo
from ...utils import get_active_image_ratio, in_debug_mode, PropertyWrapper
from ...enums import TexelDensityGroupPolicy, GroupLayoutMode, UvpmCoordSpace, PackOpType
from ...panel import UVPM3_PT_Generic, PanelUtilsMixin
from ...operator_misc import UVPM3_MT_SetRotStepGroup, UVPM3_MT_SetPixelMarginTexSizeGroup
from ...operator_islands import NumberedGroupsAccess
from ..operators.align_operator import SimilarityDriver
from ...app_iface import *

from ..panels.pack_panels import (
        UVPM3_PT_TileSetup,
        UVPM3_PT_PackOptions,
        UVPM3_PT_NormalizeScale,
        UVPM3_PT_PixelMargin,
        UVPM3_PT_Heuristic,
        UVPM3_PT_NonSquarePacking,
        UVPM3_PT_TargetBox,
        UVPM3_PT_IslandRotStep,
        UVPM3_PT_LockOverlapping,
        UVPM3_PT_LockGroups,
        UVPM3_PT_StackGroupsPack,
        UVPM3_PT_TrackGroups,
        UVPM3_PT_ScriptingPack
    )



class UVPM3_Mode_Pack(UVPM3_Mode_Main):
    
    MODE_CATEGORY = UVPM3_ModeCategory_Packing
    OPERATOR_IDNAME = UVPM3_OT_Pack.bl_idname

    def __init__(self, context):
        super().__init__(context)
        self.simi_driver = SimilarityDriver(context)
        self.lock_groups_access = NumberedGroupsAccess(context, desc_id='lock_group')
        self.track_groups_access = NumberedGroupsAccess(context, desc_id='track_group')

    def operators(self):

        return [
            OperatorMetadata(self.OPERATOR_IDNAME, properties=[('pack_op_type', PackOpType.PACK.code)], scale_y=1.4),
            OperatorMetadata(self.OPERATOR_IDNAME, label='Pack To Others', properties=[('pack_op_type', PackOpType.PACK_TO_OTHERS.code)]),
            OperatorMetadata(self.OPERATOR_IDNAME, label='Repack With Others', properties=[('pack_op_type', PackOpType.REPACK_WITH_OTHERS.code)])
        ]

    def subpanels(self):

        output = []
        output.append(UVPM3_PT_TileSetup.bl_idname)
        output.append(UVPM3_PT_PackOptions.bl_idname)
        output.append(UVPM3_PT_NormalizeScale.bl_idname)
        output.append(UVPM3_PT_PixelMargin.bl_idname)
        output.append(UVPM3_PT_Heuristic.bl_idname)
        output.append(UVPM3_PT_LockOverlapping.bl_idname)
        output.append(UVPM3_PT_LockGroups.bl_idname)
        output.append(UVPM3_PT_StackGroupsPack.bl_idname)
        output.append(UVPM3_PT_TrackGroups.bl_idname)
        output.append(UVPM3_PT_NonSquarePacking.bl_idname)

        if self.use_main_target_box():
            output.append(UVPM3_PT_TargetBox.bl_idname)

        output.append(UVPM3_PT_IslandRotStep.bl_idname)
        output.append(UVPM3_PT_ScriptingPack.bl_idname)
        # output.append(UVPM3_PT_Help.bl_idname)

        return output

    def pre_operation(self):
        
        self.target_boxes = self.get_target_boxes()

    def append_mode_name_to_op_label(self):
        return True

    def use_main_target_box(self):

        return True

    def get_main_target_box(self):

        if not self.use_main_target_box():
            return None

        if self.scene_props.custom_target_box_enable:
            return self.scene_props.custom_target_box

        return DEFAULT_TARGET_BOX

    def get_target_boxes(self):

        main_box = self.get_main_target_box()

        if main_box is None:
            return None

        return [main_box]
    
    def send_unselected_islands(self):

        return PackOpType.send_unselected_islands(self.op.pack_op_type) or self.track_groups_enabled()
    
    def get_script_container_id(self):
        
        return 'packing'

    def get_box_renderer(self):

        if self.target_boxes is None:
            return None

        box_access = BoxArrayRenderAccess()
        if not box_access.init_access(self.target_boxes, CustomTargetBoxAccess.MAIN_TARGET_BOX_COLOR):
            raise RuntimeError('Count not init box renderer')

        return BoxRenderer(self.context, box_access)

    def validate_params(self):
        pass

    def use_similarity_driver(self):
        return self.simi_driver.stack_groups_enabled()

    def send_verts_3d(self):
        ret = self.normalize_scale_enabled() and (self.scene_props.normalize_space == UvpmCoordSpace.LOCAL.code)

        if self.use_similarity_driver():
            ret |= self.simi_driver.send_verts_3d()

        return ret

    def send_verts_3d_global(self):
        ret = self.normalize_scale_enabled() and (self.scene_props.normalize_space == UvpmCoordSpace.GLOBAL.code)

        if self.use_similarity_driver():
            ret |= self.simi_driver.send_verts_3d_global()

        return ret

    def setup_script_params(self):

        self.validate_params()

        script_params = ScriptParams()
        script_params.add_param('pack_op_type', int(self.op.pack_op_type))

        if self.use_similarity_driver():
            script_params += self.simi_driver.setup_script_params()

        script_params.add_param('pinned_as_others', self.prefs.pinned_uvs_as_others)

        script_params.add_param('precision', self.scene_props.precision)
        script_params.add_param('margin', self.scene_props.margin)

        if self.prefs.pixel_margin_enabled(self.scene_props):
            script_params.add_param('pixel_margin', self.scene_props.pixel_margin)
            script_params.add_param('pixel_margin_tex_size', self.prefs.pixel_margin_tex_size(self.scene_props, self.context))

            if self.prefs.extra_pixel_margin_to_others_enabled(self.scene_props):
                script_params.add_param('extra_pixel_margin_to_others', self.scene_props.extra_pixel_margin_to_others)

            if self.prefs.pixel_border_margin_enabled(self.scene_props):
                script_params.add_param('pixel_border_margin', self.scene_props.pixel_border_margin)

            script_params.add_param('pixel_perfect_align', self.scene_props.pixel_perfect_align)
            if self.scene_props.pixel_perfect_align:
                script_params.add_param('pixel_perfect_vert_align_mode', int(self.scene_props.pixel_perfect_vert_align_mode))
            
        script_params.add_param('scale_mode', int(self.scene_props.scale_mode))
        script_params.add_param('pack_strategy', self.scene_props.pack_strategy_props.to_script_param())

        if self.prefs.FEATURE_island_rotation:
            script_params.add_param('rotation_enable', self.scene_props.rotation_enable)
            script_params.add_param('pre_rotation_disable', self.scene_props.pre_rotation_disable)
            script_params.add_param('rotation_step', self.scene_props.rotation_step)

        script_params.add_param('flipping_enable', self.scene_props.flipping_enable)

        if self.prefs.heuristic_enabled(self.scene_props):
            script_params.add_param('heuristic_search_time', self.scene_props.heuristic_search_time)
            script_params.add_param('heuristic_max_wait_time', self.scene_props.heuristic_max_wait_time)
            
            if self.prefs.heuristic_allow_mixed_scales_not_supported_msg(self.scene_props) is None:
                script_params.add_param('heuristic_allow_mixed_scales', self.scene_props.heuristic_allow_mixed_scales)

            if self.prefs.FEATURE_advanced_heuristic and self.scene_props.advanced_heuristic:
                script_params.add_param('advanced_heuristic', self.scene_props.advanced_heuristic)

        if self.scene_props.lock_overlapping_enable:
            script_params.add_param('lock_overlapping_mode', int(self.scene_props.lock_overlapping_mode))

        if self.normalize_scale_enabled():
            script_params.add_param('normalize_scale', True)
            script_params.add_param('normalize_space', int(self.scene_props.normalize_space))

        if self.island_normalize_multiplier_enabled():
            script_params.add_param('normalize_multiplier_iparam_name', NormalizeMultiplierIParamInfo.SCRIPT_NAME)

        if self.island_rot_step_enabled():
            script_params.add_param('rotation_step_iparam_name', RotStepIParamInfo.SCRIPT_NAME)

        if self.lock_groups_enabled():
            script_params.add_param('lock_group_iparam_name', self.lock_groups_access.get_iparam_info().script_name)

        if self.track_groups_enabled():
            script_params.add_param('track_group_iparam_name', self.track_groups_access.get_iparam_info().script_name)

            track_groups_props = self.scene_props.track_groups_props
            track_groups_props_param = {
                'require_match_for_all' : track_groups_props.require_match_for_all,
                'matching_mode' : int(track_groups_props.matching_mode)
            }

            script_params.add_param('track_groups_props', track_groups_props_param)

        if self.supports_tile_filling_method() and (self.prefs.tile_filling_method_not_supported_msg(self.scene_props) is None):
            script_params.add_param('tile_filling_method', int(self.scene_props.tile_filling_method))
        
        if self.prefs.pack_ratio_enabled(self.scene_props):
            pack_ratio = get_active_image_ratio(self.context)
            script_params.add_param('__pack_ratio', pack_ratio)

        if self.target_boxes is not None:
            script_params.add_param('target_boxes', [box.coords_tuple() for box in self.target_boxes])

        return script_params
    
    def normalize_scale_enabled(self):
        return (self.prefs.normalize_scale_not_supported_msg(self.scene_props) is None) and self.scene_props.normalize_scale
    
    def island_normalize_multiplier_enabled(self):
        return self.normalize_scale_enabled() and self.scene_props.island_normalize_multiplier_enable

    def island_rot_step_enabled(self):
        return self.scene_props.rotation_enable and self.scene_props.island_rot_step_enable

    def lock_groups_enabled(self):
        return self.lock_groups_access.groups_enabled()
    
    def track_groups_enabled(self):
        return self.track_groups_access.groups_enabled()

    def get_iparam_serializers(self):

        output = []

        if self.use_similarity_driver():
            output += self.simi_driver.get_iparam_serializers()

        if self.island_normalize_multiplier_enabled():
            output.append(VColorIParamSerializer(NormalizeMultiplierIParamInfo()))

        if self.island_rot_step_enabled():
            output.append(VColorIParamSerializer(RotStepIParamInfo()))

        if self.lock_groups_enabled():
            output.append(self.lock_groups_access.get_iparam_serializer())

        if self.track_groups_enabled():
            output.append(self.track_groups_access.get_iparam_serializer())

        return output
    
    def supports_pack_to_tiles(self):
        return False
    
    def supports_tile_grid(self):
        return False
    
    def supports_tile_filling_method(self):
        return False


class UVPM3_Mode_SingleTile(UVPM3_Mode_Pack):

    MODE_ID = 'pack.single_tile'
    MODE_NAME = 'Single Tile'
    MODE_PRIORITY = 1000
    MODE_HELP_URL_SUFFIX = "30-packing-modes/10-single-tile"

    SCENARIO_ID = 'pack.general'

class UVPM3_Mode_Tiles(UVPM3_Mode_Pack):

    MODE_ID = 'pack.tiles'
    MODE_NAME = 'Tiles'
    MODE_PRIORITY = 2000
    MODE_HELP_URL_SUFFIX = "30-packing-modes/20-tiles"

    SCENARIO_ID = 'pack.general'

    def get_target_boxes(self):

        tile_grid_shape = None
        if self.scene_props.use_blender_tile_grid:
            try:
                tile_grid_shape = self.context.space_data.uv_editor.tile_grid_shape
            except:
                pass

        if tile_grid_shape is None:
            tile_count_x = self.scene_props.tile_count_x
            tile_count_y = self.scene_props.tile_count_y
        else:
            tile_count_x = tile_grid_shape[0]
            tile_count_y = tile_grid_shape[1]

        main_box = self.get_main_target_box()
        return UVPM3_Box.tile_grid_boxes(main_box, tile_count_x, tile_count_y)

    def supports_pack_to_tiles(self):
        return True
    
    def supports_tile_grid(self):
        return True
    
    def supports_tile_filling_method(self):
        return True
    

class UVPM3_PT_OverrideGlobalOptionsPopover(Panel, PanelUtilsMixin, PresetPanel):

    bl_label = 'Override Global Options'

    @classmethod
    def get_active_mode(cls, context):
        return get_prefs().get_active_main_mode(context)

    def draw(self, context):
        self.init_draw(context)

        if not self.active_mode:
            return

        g_scheme_access = self.active_mode.grouping_config.get_scheme_access(ui_drawing=True)
        active_group = g_scheme_access.active_group

        if not active_group:
            return
        
        overrides = active_group.overrides

        ow_layout = self.layout
        ow_col = ow_layout.column(align=True)

        # ow_col.label(text='(Enable checkboxes on the left to override particular options)')
        # ow_col.separator()
        ow_col.label(text='Group - Override Global Options')
        ow_col.separator()
        ow_col.label(text='Packing Options:')

        def draw_prop_override(prop_name, layout_creator=None, prop_drawer=None):
            if layout_creator is None:
                if type(getattr(overrides, prop_name)) == bool:
                    layout_creator = lambda l: l.box()
                else:
                    layout_creator = lambda l: l.column(align=True)

            if prop_drawer is None:
                prop_drawer = lambda l, o, p: l.prop(o, p)

            row = ow_col.row(align=True)
            override_prop_name = 'override_' + prop_name
            row.prop(overrides, override_prop_name, text='')

            prop_layout = layout_creator(row)
            prop_drawer(prop_layout, overrides, prop_name)
            prop_layout.enabled = getattr(overrides, override_prop_name)

        draw_prop_override('rotation_enable')
        draw_prop_override('pre_rotation_disable')
        draw_prop_override('rotation_step',
                           layout_creator=lambda l: l.box(),
                           prop_drawer=lambda l, o, p: self.draw_prop_with_set_menu(o, p, l, UVPM3_MT_SetRotStepGroup))

        draw_prop_override('scale_mode', prop_drawer=lambda l, o, p: self.draw_enum_in_box(o, p, l))

        ow_col.separator()
        ow_col.label(text='Pixel Margin:')
        pixel_margin_override_enabled = hasattr(self.active_mode, 'group_pixel_margin_override_enabled') and self.active_mode.group_pixel_margin_override_enabled()
        if pixel_margin_override_enabled:
            draw_prop_override('pixel_margin')
            draw_prop_override('pixel_border_margin')
            draw_prop_override('extra_pixel_margin_to_others')

            draw_prop_override('pixel_margin_tex_size',
                               prop_drawer=lambda l, o, p: self.draw_prop_with_set_menu(o, p, l, UVPM3_MT_SetPixelMarginTexSizeGroup))
            
        else:
            row = ow_col.box()
            row.label(text='Enable Pixel Margin globally')
            row.label(text='to enable overriding')

        ow_col.separator()
        ow_col.label(text='Other Options:')

        draw_prop_override('groups_together')
        draw_prop_override('group_compactness', layout_creator=lambda l: l.box())
        draw_prop_override('pack_to_single_box')

        draw_prop_override('pack_strategy', prop_drawer=lambda l, o, p: getattr(o, p).draw(l))


class UVPM3_Mode_GroupsToTiles(UVPM3_Mode_Pack):

    MODE_ID = 'pack.groups_to_tiles'
    MODE_NAME = 'Groups To Tiles'
    MODE_PRIORITY = 3000
    MODE_HELP_URL_SUFFIX = "30-packing-modes/30-groups-to-tiles"
    TEXEL_DENSITY_POLICY_URL_SUFFIX = MODE_HELP_URL_SUFFIX + '#texel-density-policy'
    GROUP_LAYOUT_MODE_URL_SUFFIX = MODE_HELP_URL_SUFFIX + '#group-layout-mode'

    SCENARIO_ID = 'pack.groups_to_tiles'

    def get_grouping_config(self):
        config = super().get_grouping_config()
        config.grouping_enabled = True
        config.target_box_editing = config.active_g_scheme_target_box_editing()
        return config

    def group_pixel_margin_override_enabled(self):
        return self.prefs.pixel_margin_enabled(self.scene_props)

    def get_group_script_param_handler(self):

        def sparam_handler(group, out_group):
            overrides = group.overrides
            out_group['tdensity_cluster'] = group.tdensity_cluster

            out_overrides = {}
            out_group['overrides'] = out_overrides

            def handle_ow_prop(prop_name, cond=True):
                out_overrides[prop_name] = PropertyWrapper(overrides, prop_name).to_script_param()\
                    if cond and overrides.override_global_options and getattr(overrides, 'override_' + prop_name) else None

            handle_ow_prop('rotation_enable')
            handle_ow_prop('pre_rotation_disable')
            handle_ow_prop('rotation_step')
            handle_ow_prop('scale_mode')

            pm_override_enabled = self.group_pixel_margin_override_enabled()
        
            handle_ow_prop('pixel_margin', pm_override_enabled)
            handle_ow_prop('pixel_border_margin', pm_override_enabled)
            handle_ow_prop('extra_pixel_margin_to_others', pm_override_enabled)
            handle_ow_prop('pixel_margin_tex_size', pm_override_enabled)

            handle_ow_prop('groups_together')
            handle_ow_prop('group_compactness')
            handle_ow_prop('pack_to_single_box')
            handle_ow_prop('pack_strategy')

        return sparam_handler

    def draw_grouping_options(self, g_scheme, g_options, layout):

        col = layout
        UVPM3_PT_Generic.draw_enum_in_box(g_options, 'tdensity_policy', col, self.TEXEL_DENSITY_POLICY_URL_SUFFIX)

        if not g_options.automatic:
            box = col.box()
            UVPM3_PT_Generic.handle_prop(g_options.base,
                                         'last_group_complementary',
                                         box,
                                         not_supported_msg=g_scheme.complementary_group_not_supported_msg())

        mode_layout = UVPM3_PT_Generic.draw_enum_in_box(g_options, 'group_layout_mode', col, self.GROUP_LAYOUT_MODE_URL_SUFFIX)

        if g_options.automatic and GroupLayoutMode.supports_tile_count(g_options.group_layout_mode):
            row = mode_layout.row(align=True)
            row.prop(g_options.base, "tile_count_per_group")

        if GroupLayoutMode.supports_tiles_in_row(g_options.group_layout_mode):
            row = mode_layout.row(align=True)
            row.prop(g_options.base, "tiles_in_row")

        if GroupLayoutMode.supports_tile_count_xy(g_options.group_layout_mode):
            row = mode_layout.row(align=True)
            row.prop(g_options.base, "tile_count_x")

            row = mode_layout.row(align=True)
            row.prop(g_options.base, "tile_count_y")

        box = col.box()
        row = box.row(align=True)
        row.prop(g_options.base, "groups_together")

        if g_options.base.groups_together:
            box = col.box()
            row = box.row(align=True)
            row.prop(g_options.base, "group_compactness")

        box = col.box()
        row = box.row(align=True)
        row.prop(g_options.base, "pack_to_single_box")

    def draw_group_options(self, g_scheme, group, layout):
        props_count = 0

        if in_debug_mode():
            row = layout.row(align=True)
            row.enabled = False
            row.prop(group, "num")
            props_count += 1

        if g_scheme.options.tdensity_policy == TexelDensityGroupPolicy.CUSTOM.code:
            row = layout.row(align=True)
            row.enabled = g_scheme.options.tdensity_policy == TexelDensityGroupPolicy.CUSTOM.code
            row.prop(group, "tdensity_cluster")
            props_count += 1

        if GroupLayoutMode.supports_tile_count(g_scheme.options.group_layout_mode):
            row = layout.row(align=True)
            # row.enabled = g_scheme.options.group_layout_mode == GroupLayoutMode.AUTOMATIC.code
            row.prop(group, "tile_count")
            props_count += 1

        overrides = group.overrides
        box = layout.box()
        row = box.row(align=True)
        row.prop(overrides, "override_global_options")
        props_count += 1
        
        if overrides.override_global_options:
            row.popover(panel=UVPM3_PT_OverrideGlobalOptionsPopover.__name__, text='', icon='SETTINGS')

        return props_count

    def use_main_target_box(self):

        return False

    def get_box_renderer(self):
        
        box_access = GroupingSchemeRenderAccess()
        box_access.init_access(self.op.g_scheme)

        return BoxRenderer(self.context, box_access)
    
    def supports_pack_to_tiles(self):
        return True
    
    def supports_tile_filling_method(self):
        return True


class UVPM3_Mode_GroupsTogether(UVPM3_Mode_Tiles):

    MODE_ID = 'pack.groups_together'
    MODE_NAME = 'Groups Together'
    MODE_PRIORITY = 4000
    MODE_HELP_URL_SUFFIX = "30-packing-modes/40-groups-together"

    SCENARIO_ID = 'pack.groups_together'

    def get_grouping_config(self):
        config = super().get_grouping_config()
        config.grouping_enabled = True
        return config

    def draw_grouping_options(self, g_scheme, g_options, layout):

        col = layout
        row = col.row(align=True)
        row.prop(g_options.base, "group_compactness")

    def supports_tile_filling_method(self):
        return False


class UVPM3_Mode_GroupsIndependently(UVPM3_Mode_Tiles):

    MODE_ID = 'pack.groups_independently'
    MODE_NAME = 'Groups Independently'
    MODE_PRIORITY = 5000
    MODE_HELP_URL_SUFFIX = "30-packing-modes/50-groups-independently"

    SCENARIO_ID = 'pack.groups_independently'

    def get_grouping_config(self):
        config = super().get_grouping_config()
        config.grouping_enabled = True
        return config

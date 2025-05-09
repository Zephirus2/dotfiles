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

from ...panel_islands import UVPM3_PT_NumberedGroups, UVPM3_PT_StackGroups
from ...panel_grouping_editor import UVPM3_PT_GroupTargetBoxes, UVPM3_PT_Grouping, UVPM3_PT_SchemeGroups
from ...panel import *
from ...labels import Labels

from ...box_ui import CustomTargetBoxEditUI
from ...operator_misc import UVPM3_MT_SetRotStepScene, UVPM3_MT_SetPixelMarginTexSizeScene
from ...operator_islands import *


import multiprocessing


class UVPM3_PT_TileSetup(UVPM3_PT_SubPanelPack):

    bl_idname = 'UVPM3_PT_TileSetup'
    bl_label = 'Tile Setup'

    PANEL_PRIORITY = 500

    @classmethod
    def poll_impl(cls, context):
        return super().poll_impl(context) and cls.active_mode.supports_pack_to_tiles()

    def draw_impl(self, context):
        layout = self.layout
        col = layout.column(align=True)

        if self.active_mode.supports_tile_grid():
            box = col.box()
            box.prop(self.scene_props, "use_blender_tile_grid")

            col2 = col.column(align=True)
            col2.enabled = not self.scene_props.use_blender_tile_grid
            col2.prop(self.scene_props, "tile_count_x")
            col2.prop(self.scene_props, "tile_count_y")

        if self.active_mode.supports_tile_filling_method():
            filling_method_warning_msg = "The '{}' method is always used for islands packed with fixed scale".format(Labels.TILE_FILLING_METHOD_ONE_BY_ONE_NAME)\
                if self.prefs.fixed_scale_enabled(self.scene_props) else None
    
            self.draw_enum_in_box(
                self.scene_props,
                "tile_filling_method",
                col,
                warning_msg=filling_method_warning_msg)


class UVPM3_PT_PackOptions(UVPM3_PT_GenericPack):

    bl_idname = 'UVPM3_PT_PackOptions'
    bl_label = 'Packing Options'

    PANEL_PRIORITY = 1000
    HELP_URL_SUFFIX = '20-packing-functionalities/15-basic-packing-and-options'

    def draw_impl(self, context):
        layout = self.layout
        col = layout.column(align=True)

        self.prop_with_help(self.scene_props, "precision", col, self.HELP_URL_SUFFIX if self.props_with_help else None)

        row = col.row(align=True)
        margin_supported = not self.prefs.pixel_margin_enabled(self.scene_props)
        margin_not_supported_msg = 'The Margin option is ignored when Pixel Margin is enabled'
        self.handle_prop(self.scene_props, "margin", row, not_supported_msg=None if margin_supported else margin_not_supported_msg)

        # Rotation Resolution
        box = col.box()
        box.enabled = self.prefs.FEATURE_island_rotation

        row = box.row()
        # TODO: missing feature check
        row.prop(self.scene_props, "rotation_enable")

        box = col.box()
        row = box.row()
        row.enabled = self.scene_props.rotation_enable
        row.prop(self.scene_props, "pre_rotation_disable")

        row = col.row(align=True)
        row.enabled = self.scene_props.rotation_enable
        self.draw_prop_with_set_menu(self.scene_props, "rotation_step", row, UVPM3_MT_SetRotStepScene)

        # Flipping enable
        box = col.box()
        row = box.row()
        row.prop(self.scene_props, "flipping_enable")

        # Scale mode
        self.draw_enum_in_box(self.scene_props, "scale_mode", col)


class UVPM3_PT_SubPanelPackOptions(UVPM3_PT_SubPanelPack):
    
    bl_parent_id = UVPM3_PT_PackOptions.bl_idname


class UVPM3_PT_SubPanelAdvancedPackOptions(UVPM3_PT_SubPanelPack):
    
    bl_parent_id = UVPM3_PT_AdvancedPackOptions.bl_idname


class UVPM3_PT_NormalizeScale(UVPM3_PT_SubPanelPackOptions):

    bl_idname = 'UVPM3_PT_NormalizeScale'
    bl_label = 'Normalize Scale'
    bl_options = {'DEFAULT_CLOSED'}

    PANEL_PRIORITY = 1500
    HELP_URL_SUFFIX = '20-packing-functionalities/25-normalize-scale'

    def get_main_property(self):
        return PropertyWrapper(get_scene_props(self.context), 'normalize_scale')
    
    def not_supported_msg(self, context):
        return get_prefs().normalize_scale_not_supported_msg(get_scene_props(context))
    
    def warning_msg(self, context):
        if get_prefs().fixed_scale_enabled(get_scene_props(context)):
            return "Islands packed with fixed scale will not be normalized"
        
        return None

    def draw_impl(self, context):
        layout = self.layout
        col = layout.column(align=True)

        self.draw_enum_in_box(self.scene_props, "normalize_space", col, expand=True)

        box = col.box()
        row = box.row()
        row.prop(self.scene_props, "island_normalize_multiplier_enable")

        if self.scene_props.island_normalize_multiplier_enable:
            multiplier_col = col.column(align=True)
            IParamEditUI(self.context, self.scene_props, 'NormalizeMultiplierIParamInfo').draw(multiplier_col)


class UVPM3_PT_PixelMargin(UVPM3_PT_SubPanelPackOptions):

    bl_idname = 'UVPM3_PT_PixelMargin'
    bl_label = 'Pixel Margin'
    bl_options = {'DEFAULT_CLOSED'}

    PANEL_PRIORITY = 3000
    HELP_URL_SUFFIX = '20-packing-functionalities/30-pixel-margin'
    PIXEL_PERFECT_ALIGN_URL_SUFFIX = HELP_URL_SUFFIX + '#pixel-perfect-alignment'

    WARNING_MSG_ARRAY = [
        'The following options may have different meaning than in other 3D tools.',
        'Check the option hints or documentation before using them.'
    ]

    def get_main_property(self):
        return PropertyWrapper(get_scene_props(self.context), 'pixel_margin_enable')

    def draw_impl(self, context):
        layout = self.layout
        col = layout.column(align=True)

        self.draw_dismissable_warning('pixel_margin_warn_dismissed', self.WARNING_MSG_ARRAY, col)

        # Pixel margin
        self.prop_with_help(self.scene_props, "pixel_margin", col, self.HELP_URL_SUFFIX if self.props_with_help else None)

        # Pixel padding
        row = col.row(align=True)
        row.prop(self.scene_props, "pixel_border_margin")

        # Pixel margin to others
        row = col.row(align=True)
        row.prop(self.scene_props, "extra_pixel_margin_to_others")

        # Pixel Margin Tex Size
        tex_size_not_supported_msg = 'When Non-Square Packing is enabled, active texture dimensions are used to calculate pixel margin'\
            if self.prefs.pack_ratio_enabled(self.scene_props) else None
        row = col.row(align=True)
        self.draw_prop_with_set_menu(
            self.scene_props,
            "pixel_margin_tex_size",
            row,
            UVPM3_MT_SetPixelMarginTexSizeScene,
            not_supported_msg=tex_size_not_supported_msg)

        box = col.box()
        self.prop_with_help(self.scene_props, 'pixel_perfect_align', box, self.PIXEL_PERFECT_ALIGN_URL_SUFFIX)

        if self.scene_props.pixel_perfect_align:
            self.draw_enum_in_box(self.scene_props, 'pixel_perfect_vert_align_mode', box)


class UVPM3_PT_Heuristic(UVPM3_PT_SubPanelPackOptions):

    bl_idname = 'UVPM3_PT_Heuristic'
    bl_label = 'Heuristic Search'
    bl_options = {'DEFAULT_CLOSED'}

    PANEL_PRIORITY = 4000
    HELP_URL_SUFFIX = '20-packing-functionalities/40-heuristic-search'

    def get_main_property(self):
        return PropertyWrapper(get_scene_props(self.context), 'heuristic_enable')

    def draw_impl(self, context):
        layout = self.layout

        col = layout.column(align=True)

        self.prop_with_help(self.scene_props, "heuristic_search_time", col, self.HELP_URL_SUFFIX if self.props_with_help else None)
        row = col.row(align=True)
        row.prop(self.scene_props, "heuristic_max_wait_time")

        box = col.box()
        row = box.row()

        allow_mixed_scales_warning_msg = "Islands packed with fixed scale won't be affected by this option"\
            if self.prefs.fixed_scale_enabled(self.scene_props) else None

        self.handle_prop(self.scene_props, "heuristic_allow_mixed_scales", row, warning_msg=allow_mixed_scales_warning_msg)

        # Advanced Heuristic
        box = col.box()
        box.enabled = self.prefs.advanced_heuristic_available(self.scene_props)
        row = box.row()
        self.handle_prop(self.scene_props, "advanced_heuristic", row, None if self.prefs.FEATURE_advanced_heuristic else Labels.FEATURE_NOT_SUPPORTED_MSG)
        

class UVPM3_PT_LockOverlapping(UVPM3_PT_SubPanelAdvancedPackOptions):

    bl_idname = 'UVPM3_PT_LockOverlapping'
    bl_label = 'Lock Overlapping'
    bl_options = {'DEFAULT_CLOSED'}

    PANEL_PRIORITY = 4400
    HELP_URL_SUFFIX = '20-packing-functionalities/50-lock-overlapping'

    def get_main_property(self):
        return PropertyWrapper(get_scene_props(self.context), 'lock_overlapping_enable')

    def draw_impl(self, context):
        layout = self.layout
        col = layout.column(align=True)

        # Lock overlapping
        self.draw_enum_in_box(self.scene_props, "lock_overlapping_mode", col, self.HELP_URL_SUFFIX)
        


class UVPM3_PT_LockGroups(UVPM3_PT_NumberedGroups, UVPM3_PT_SubPanelAdvancedPackOptions):

    bl_idname = 'UVPM3_PT_LockGroups'
    bl_label = 'Lock Groups'
    bl_options = {'DEFAULT_CLOSED'}

    PANEL_PRIORITY = 4500

    DESC_ID = 'lock_group'
    HELP_URL_SUFFIX = '20-packing-functionalities/50-lock-overlapping#lock-groups'


class UVPM3_PT_StackGroupsPack(UVPM3_PT_StackGroups, UVPM3_PT_SubPanelAdvancedPackOptions):

    bl_idname = 'UVPM3_PT_StackGroupsPack'
    PANEL_PRIORITY = 4700


class UVPM3_PT_TrackGroups(UVPM3_PT_NumberedGroups, UVPM3_PT_SubPanelAdvancedPackOptions):

    bl_idname = 'UVPM3_PT_TrackGroups'
    bl_label = 'Track Groups'
    bl_options = {'DEFAULT_CLOSED'}

    PANEL_PRIORITY = 4800

    DESC_ID = 'track_group'
    HELP_URL_SUFFIX = '20-packing-functionalities/57-track-groups'

    def post_draw(self, layout):
        track_groups_props = self.scene_props.track_groups_props

        self.draw_enum_in_box(track_groups_props, 'matching_mode', layout)

        box = layout.box()
        box.prop(track_groups_props, 'require_match_for_all')


class UVPM3_PT_NonSquarePacking(UVPM3_PT_SubPanelAdvancedPackOptions):

    bl_idname = 'UVPM3_PT_NonSquarePacking'
    bl_label = 'Non-Square Packing'
    bl_options = {'DEFAULT_CLOSED'}

    PANEL_PRIORITY = 5000
    HELP_URL_SUFFIX = '20-packing-functionalities/60-non-square-packing'

    def get_main_property(self):
        return PropertyWrapper(get_scene_props(self.context), 'tex_ratio')

    def draw_impl(self, context):
        layout = self.layout
        col = layout.column(align=True)

        self.operator_with_help(UVPM3_OT_AdjustIslandsToTexture.bl_idname, col, help_url_suffix=self.HELP_URL_SUFFIX if self.props_with_help else None)

        row = col.row(align=True)
        row.operator(UVPM3_OT_UndoIslandsAdjustemntToTexture.bl_idname)


class UVPM3_PT_TargetBox(UVPM3_PT_SubPanelAdvancedPackOptions):

    bl_idname = 'UVPM3_PT_TargetBox'
    bl_label = 'Custom Target Box'
    bl_options = {'DEFAULT_CLOSED'}

    PRESET_PANEL = UVPM3_PT_PresetsCustomTargetBox
    PANEL_PRIORITY = 6000
    HELP_URL_SUFFIX = '20-packing-functionalities/70-custom-target-box/'

    def get_main_property(self):
        return PropertyWrapper(get_scene_props(self.context), 'custom_target_box_enable')

    def draw_header_preset(self, _context):
        UVPM3_PT_PresetsCustomTargetBox.draw_panel_header(self.layout)

    def draw_impl(self, context):
        layout = self.layout

        col = layout.column(align=True)

        box_edit_UI = CustomTargetBoxEditUI(context, self.scene_props)
        box_edit_UI.draw(col)


class UVPM3_PT_IslandRotStep(UVPM3_PT_IParamEditMixin, UVPM3_PT_SubPanelAdvancedPackOptions):

    bl_idname = 'UVPM3_PT_IslandRotStep'
    bl_label = 'Island Rotation Step'
    bl_options = {'DEFAULT_CLOSED'}

    HELP_URL_SUFFIX = '20-packing-functionalities/80-island-rotation-step'

    PANEL_PRIORITY = 7000
    IPARAM_INFO_TYPE = 'RotStepIParamInfo'


from ...scripting import UVPM3_PT_ScriptingBase

class UVPM3_PT_ScriptingPack(UVPM3_PT_ScriptingBase, UVPM3_PT_SubPanelAdvancedPackOptions):

    bl_idname = 'UVPM3_PT_ScriptingPack'
    bl_label = 'Scripting'
    bl_options = {'DEFAULT_CLOSED'}

    HELP_URL_SUFFIX = '20-packing-functionalities/95-scripting'
    PANEL_PRIORITY = 9000
    SCRIPT_CONTAINER_ID = 'packing'



class UVPM3_PT_Help(UVPM3_PT_SubPanelPack):

    bl_idname = 'UVPM3_PT_Help'
    bl_label = 'Hints / Help'
    bl_options = {'DEFAULT_CLOSED'}

    PANEL_PRIORITY = 12000

    def draw_impl(self, context):
        layout = self.layout
        col = layout.column(align=True)

        hints = []

        if self.prefs.thread_count < multiprocessing.cpu_count():
            hints.append("'Thread Count' value is lower than the number of cores in your system - consider increasing that parameter in order to increase the packer speed.")

        if self.scene_props.precision < 200:
            hints.append("Setting 'Precision' to a value lower than 200 is not recommended.")

        if self.scene_props.precision > 1000:
            hints.append("Setting 'Precision' to a value greater than 1000 is usually need only if you want to achieve very small margin between islands - increase the 'Precision' value with care as it may significantly increase packing time.")

        if not self.scene_props.rotation_enable:
            hints.append('Packing will not be optimal with island rotations disabled. Disabling rotations might be reasonable only if you really need to improve the packing speed.')
        else:
            if self.scene_props.rotation_step not in UVPM3_MT_SetRotStepScene.VALUES:
                hints.append("It is usually recommended that the Rotation Step value is a divisor of 90 (or 180 at rare cases). You can use the 'Set' menu, next to the 'Rotation Step' parameter, to choose a step from the set of all recommended values.")

        if self.prefs.FEATURE_island_rotation and self.scene_props.pre_rotation_disable:
            hints.append('Pre-rotation usually optimizes packing, disable it only if you have a good reason.')

        if self.prefs.pack_ratio_supported():
            try:
                ratio = get_active_image_ratio(context)

                if not self.scene_props.tex_ratio and ratio != 1.0:
                    hints.append("The active texture is non-square, but the 'Use Texture Ratio' option is disabled. Did you forget to enable it?")
            except:
                pass

        if self.prefs.advanced_heuristic_available(self.scene_props) and self.scene_props.advanced_heuristic:
            hints.append("'Advanced Hueristic' is useful only for UV maps containing a small number of islands. Read the option description to learn more.")

        if len(hints) == 0:
            hints.append('No hints for the currently selected parameters')

        col.label(text='Parameter hints:')
        self.messages_in_boxes(col, hints)



class UVPM3_PT_GroupingPack(UVPM3_PT_Grouping, UVPM3_PT_GenericPack):

    bl_idname = 'UVPM3_PT_GroupingPack'


class UVPM3_PT_SchemeGroupsPack(UVPM3_PT_SchemeGroups, UVPM3_PT_GenericPack):

    bl_idname = 'UVPM3_PT_SchemeGroupsPack'
    bl_parent_id = UVPM3_PT_GroupingPack.bl_idname


class UVPM3_PT_GroupTargetBoxesPack(UVPM3_PT_GroupTargetBoxes, UVPM3_PT_GenericPack):

    bl_idname = 'UVPM3_PT_GroupTargetBoxesPack'
    bl_parent_id = UVPM3_PT_GroupingPack.bl_idname


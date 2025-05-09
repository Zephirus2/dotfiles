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


from .multi_panel import MULTI_PANEL_ID_GROUPING_EDITOR
from .grouping_scheme_access import GroupingSchemeAccess
from .utils import get_prefs, snake_to_camel_case
from .panel import UVPM3_PT_Generic, UVPM3_PT_Registerable
from .operator_islands import UVPM3_OT_SetManualGroupIParam, UVPM3_OT_SelectManualGroupIParam, UVPM3_OT_ShowManualGroupIParam, UVPM3_OT_ApplyGroupingToScheme
from .app_iface import get_scene_props
from .scripted_pipeline.modes.grouping_editor_mode import UVPM3_Mode_GroupingEditor
from .scripted_pipeline.operators.grouping_editor_operator import UVPM3_OT_EditGroupingSchemeInEditor


from .grouping_scheme import\
    (UVPM3_OT_NewGroupingScheme,
     UVPM3_OT_RemoveGroupingScheme,
     UVPM3_OT_NewGroupInfo,
     UVPM3_OT_RemoveGroupInfo,
     UVPM3_OT_NewTargetBox,
     UVPM3_OT_RemoveTargetBox,
     UVPM3_OT_MoveGroupInfo,
     UVPM3_OT_MoveTargetBox)

from .grouping_scheme_ui import UVPM3_UL_GroupInfo, UVPM3_UL_TargetBoxes

from .box_ui import GroupingSchemeBoxesEditUI


class GroupingSchemeDrawer(GroupingSchemeAccess):

    def __init__(self,
                 context,
                 active_mode,
                 access_desc_id=None,
                 access_desc=None,
                 should_draw_grouping_options=False,
                 preset_panel_t=None,
                 draw_edit_g_scheme_button=False):
        
        # if context_access_desc_id:
        #     access_desc_id = str(context_access_desc_id)

        self.init_access(context, desc_id=access_desc_id, desc=access_desc, ui_drawing=True)
        self.scene_props = get_scene_props(context)
        self.active_mode = active_mode
        self.should_draw_grouping_options = should_draw_grouping_options
        self.preset_panel_t = preset_panel_t
        self.use_context_access_desc = self.desc_id is None
        self.draw_edit_g_scheme_button = draw_edit_g_scheme_button

    def draw_g_schemes_presets(self, layout):
        layout.emboss = 'NONE'
        layout.popover(panel=self.preset_panel_t.__name__, icon='PRESET', text="")

    def op_init(self, op, layout):
        if self.use_context_access_desc:
            layout.context_pointer_set('uvpm3_access_desc', self.desc)
        else:
            op.access_desc_id = self.desc_id

    def draw_g_schemes(self, layout):

        main_col = layout.column(align=True)
        main_col.label(text='Select a grouping scheme:')

        row = main_col.row(align=True)

        if self.use_context_access_desc:
            menu_class_idname = 'UVPM3_MT_BrowseGroupingSchemesContext'
            row.context_pointer_set('uvpm3_access_desc', self.desc)
        else:
            menu_class_idname = 'UVPM3_MT_BrowseGroupingSchemes' + snake_to_camel_case(self.desc_id)

        row.menu(menu_class_idname, text="", icon='GROUP_UVS')

        g_scheme_available = len(self.g_schemes) > 0

        if self.active_g_scheme is not None:
            row.prop(self.active_g_scheme, "name", text="")
        elif g_scheme_available:
            box = row.box()
            box.scale_y = 0.5
            box.enabled = False
            box.label(text='← Select a grouping scheme')

        op = row.operator(UVPM3_OT_NewGroupingScheme.bl_idname, icon='ADD', text='' if g_scheme_available else UVPM3_OT_NewGroupingScheme.bl_label)
        self.op_init(op, row)

        if self.active_g_scheme is not None:
            op = row.operator(UVPM3_OT_RemoveGroupingScheme.bl_idname, icon='REMOVE', text='')
            self.op_init(op, row)

        if self.preset_panel_t is not None:
            box = row.box()
            box.scale_y = 0.5
            self.draw_g_schemes_presets(box)

        if self.draw_edit_g_scheme_button:
            main_col.separator()
            row = main_col.row(align=True)
            op = row.operator(UVPM3_OT_EditGroupingSchemeInEditor.bl_idname)
            if self.active_g_scheme is None:
                row.enabled = False
            else:
                op.g_scheme_uuid = self.get_active_g_scheme_uuid()

        if self.active_g_scheme is None:
            return None

        if self.should_draw_grouping_options:
            main_col.separator()
            main_col.separator()
            main_col.label(text='Scheme options:')
            self.draw_grouping_options(self.active_g_scheme.options, main_col, self.active_g_scheme)


    def draw_grouping_options(self, g_options, layout, g_scheme=None):
        self.active_mode.draw_grouping_options(g_scheme, g_options, layout)


    def draw_groups(self, layout):
        if self.active_g_scheme is None:
            return

        main_col = layout.column(align=True)

        groups_layout = main_col # .box()

        show_more = self.active_g_scheme is not None and len(self.active_g_scheme.groups) > 1

        row = groups_layout.row()
        row.template_list(UVPM3_UL_GroupInfo.bl_idname, "", self.active_g_scheme, "groups",
                            self.active_g_scheme,
                            "active_group_idx", rows=4 if show_more else 2)

        col = row.column(align=True)
        op = col.operator(UVPM3_OT_NewGroupInfo.bl_idname, icon='ADD', text="")
        self.op_init(op, col)

        op = col.operator(UVPM3_OT_RemoveGroupInfo.bl_idname, icon='REMOVE', text="")
        self.op_init(op, col)

        if show_more:
            col.separator()
            op = col.operator(UVPM3_OT_MoveGroupInfo.bl_idname, icon='TRIA_UP', text="")
            self.op_init(op, col)
            op.direction = 'UP'

            op = col.operator(UVPM3_OT_MoveGroupInfo.bl_idname, icon='TRIA_DOWN', text="")
            self.op_init(op, col)
            op.direction = 'DOWN'

        if self.active_group is None:
            return
            
        col = groups_layout.column(align=True)
        col.separator()

        if hasattr(self.active_mode, 'draw_group_options'):
            col.label(text='Group options:')
            col2 = col.column(align=True)

            props_count = self.active_mode.draw_group_options(self.active_g_scheme, self.active_group, col2)

            if props_count == 0:
                box = col2.box()
                box.label(text='No group options available the for currently selected modes')

        col.separator()
        col.separator()
        row = col.row(align=True)
        op = row.operator(UVPM3_OT_SetManualGroupIParam.bl_idname)
        self.op_init(op, row)
        col.separator()

        col.label(text="Select islands assigned to the group:")
        row = col.row(align=True)

        op = row.operator(UVPM3_OT_SelectManualGroupIParam.bl_idname, text="Select")
        self.op_init(op, row)
        op.select = True

        op = row.operator(UVPM3_OT_SelectManualGroupIParam.bl_idname, text="Deselect")
        self.op_init(op, row)
        op.select = False

        row = col.row(align=True)
        op = row.operator(UVPM3_OT_ShowManualGroupIParam.bl_idname)
        self.op_init(op, row)

    def draw_target_boxes(self, layout):
        if self.active_g_scheme is None:
            return

        complementary_group_is_active = self.active_g_scheme.complementary_group_is_active()

        target_boxes_col = layout.column(align=True)
        target_boxes_col.enabled = not complementary_group_is_active

        if complementary_group_is_active:
            target_boxes_text='Group Target Boxes: (target boxes of the complementary group cannot be edited)'
            target_boxes_icon='ERROR'
            row = target_boxes_col.row()
            row.label(text=target_boxes_text, icon=target_boxes_icon)


        show_more = self.active_group is not None and len(self.active_group.target_boxes) > 1

        row = target_boxes_col.row()
        row.template_list(UVPM3_UL_TargetBoxes.bl_idname, "", self.active_group, "target_boxes",
                          self.active_group,
                          "active_target_box_idx", rows=4 if show_more else 2)
        col = row.column(align=True)
        op = col.operator(UVPM3_OT_NewTargetBox.bl_idname, icon='ADD', text="")
        self.op_init(op, col)

        op = col.operator(UVPM3_OT_RemoveTargetBox.bl_idname, icon='REMOVE', text="")
        self.op_init(op, col)

        if show_more:
            col.separator()
            op = col.operator(UVPM3_OT_MoveTargetBox.bl_idname, icon='TRIA_UP', text="")
            self.op_init(op, col)
            op.direction = 'UP'

            op = col.operator(UVPM3_OT_MoveTargetBox.bl_idname, icon='TRIA_DOWN', text="")
            self.op_init(op, col)
            op.direction = 'DOWN'

        # col = groups_layout.column(align=True)

        target_boxes_col.separator()
        box_edit_UI = GroupingSchemeBoxesEditUI(self.context, self.scene_props, access_desc_id=self.desc_id)
        box_edit_UI.draw(target_boxes_col)


class UVPM3_PT_GroupingBase(UVPM3_PT_Registerable):

    @classmethod
    def poll_impl(cls, context):
        return cls.active_mode.grouping_config.grouping_enabled

    def draw_impl(self, context):

        self.g_scheme_drawer = GroupingSchemeDrawer(context,
                                                    self.active_mode,
                                                    self.active_mode.grouping_config.g_scheme_access_desc_id,
                                                    should_draw_grouping_options=hasattr(self.active_mode, 'draw_grouping_options'),
                                                    preset_panel_t=self.active_mode.grouping_config.g_scheme_preset_panel_t)
        
        self.draw_impl2(context)


class UVPM3_PT_Grouping(UVPM3_PT_GroupingBase):

    bl_label = 'Island Grouping'

    PANEL_PRIORITY = 800
    APPLY_GROUPING_TO_SCHEME_HELP_URL_SUFFIX = '30-packing-modes/30-groups-to-tiles/#apply-automatic-grouping-to-a-grouping-scheme'
            
    def draw_impl2(self, context):

        layout = self.layout

        col = layout.column(align=True)
        box = col.box()
        col2 = box.column(align=True)
        self.active_mode.grouping_config.draw_group_method(col2)

        if self.active_mode.grouping_config.auto_grouping_enabled():
            if self.g_scheme_drawer.should_draw_grouping_options:
                options_box = col.box()
                options_col = options_box.column(align=True)
                options_col.label(text='Grouping options:')
                # options_box = options_col.box()

                self.g_scheme_drawer.draw_grouping_options(self.scene_props.auto_group_options, options_col)
            
            box = col.box()
            self.operator_attach_mode(UVPM3_OT_ApplyGroupingToScheme.bl_idname, self.active_mode.MODE_ID, box, help_url_suffix=self.APPLY_GROUPING_TO_SCHEME_HELP_URL_SUFFIX)

        else:
            # col.separator()
            box = col.box()
            self.g_scheme_drawer.draw_g_schemes(box)


class UVPM3_PT_RequireGroupingScheme(UVPM3_PT_GroupingBase):

    @classmethod
    def poll_impl(cls, context):
        return super().poll_impl(context) and cls.active_mode.grouping_config.get_active_g_scheme(ui_drawing=True) is not None
    

class UVPM3_PT_SchemeGroups(UVPM3_PT_RequireGroupingScheme):

    bl_label = 'Scheme Groups'

    PANEL_PRIORITY = 810

    def draw_impl2(self, context):

        self.g_scheme_drawer.draw_groups(self.layout)


class UVPM3_PT_GroupTargetBoxes(UVPM3_PT_RequireGroupingScheme):

    bl_label = 'Group Target Boxes'

    PANEL_PRIORITY = 820

    @classmethod
    def poll_impl(cls, context):
        return super().poll_impl(context) and cls.active_mode.grouping_config.target_box_editing

    def draw_impl2(self, context):

        self.g_scheme_drawer.draw_target_boxes(self.layout)


class UVPM3_PT_GenericGroupingEditor(UVPM3_PT_Generic):

    bl_category = 'UVPM3 - Grouping Editor'

    MULTI_PANEL_ID = MULTI_PANEL_ID_GROUPING_EDITOR

    @classmethod
    def get_active_mode(cls, context):
        return UVPM3_Mode_GroupingEditor(context)
    
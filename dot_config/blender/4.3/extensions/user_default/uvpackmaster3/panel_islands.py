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


from .operator_islands import NumberedGroupsAccess, UVPM3_OT_NumberedGroupResetIParam, UVPM3_OT_NumberedGroupSelectIParam, UVPM3_OT_NumberedGroupSetFreeIParam, UVPM3_OT_NumberedGroupShowIParam
from .panel_grouping_editor import GroupingSchemeDrawer
from .operator_islands import UVPM3_OT_NumberedGroupSetIParam


class UVPM3_PT_NumberedGroups:

    def get_main_property(self):
        return NumberedGroupsAccess(self.context, desc_id=self.DESC_ID).get_enable_property()
    
    def post_draw(self, layout):
        pass

    def draw_impl(self, context):

        groups_access = NumberedGroupsAccess(self.context, desc_id=self.DESC_ID)
        layout = self.layout
        col = layout.column(align=True)

        box = col.box()
        box.prop(groups_access.desc, 'use_g_scheme')

        if groups_access.desc.use_g_scheme:
            g_scheme_drawer = GroupingSchemeDrawer(self.context, self.active_mode, groups_access.desc_id, draw_edit_g_scheme_button=True)

            box = col.box()
            g_scheme_drawer.draw_g_schemes(box)

        else:
            row = col.row(align=True)
            row.prop(groups_access.desc, 'group_num')

            if self.props_with_help and self.HELP_URL_SUFFIX is not None:
                self._draw_help_operator(row, self.HELP_URL_SUFFIX)

            row = col.row(align=True)
            op = row.operator(UVPM3_OT_NumberedGroupSetIParam.bl_idname)
            op.groups_desc_id = groups_access.desc_id

            row = col.row(align=True)
            op = row.operator(UVPM3_OT_NumberedGroupSetFreeIParam.bl_idname)
            op.groups_desc_id = groups_access.desc_id
            
            col.separator()

            col.label(text="Select islands assigned to the group:")
            row = col.row(align=True)

            op = row.operator(UVPM3_OT_NumberedGroupSelectIParam.bl_idname, text="Select")
            op.groups_desc_id = groups_access.desc_id
            op.select = True
            op = row.operator(UVPM3_OT_NumberedGroupSelectIParam.bl_idname, text="Deselect")
            op.groups_desc_id = groups_access.desc_id
            op.select = False

            row = col.row(align=True)
            op = row.operator(UVPM3_OT_NumberedGroupResetIParam.bl_idname)
            op.groups_desc_id = groups_access.desc_id

            row = col.row(align=True)
            op = row.operator(UVPM3_OT_NumberedGroupShowIParam.bl_idname)
            op.groups_desc_id = groups_access.desc_id

        self.post_draw(col)


class UVPM3_PT_StackGroups(UVPM3_PT_NumberedGroups):

    bl_label = 'Stack Groups'
    bl_options = {'DEFAULT_CLOSED'}

    DESC_ID = 'stack_group'
    HELP_URL_SUFFIX = '20-packing-functionalities/55-stack-groups'
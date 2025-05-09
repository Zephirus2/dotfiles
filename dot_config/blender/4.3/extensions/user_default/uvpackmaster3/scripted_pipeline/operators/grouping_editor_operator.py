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

from ...multi_panel import MULTI_PANEL_ID_GROUPING_EDITOR
from ...operator import UVPM3_OT_Generic
from ...enums import GroupingMethod
from ..modes.grouping_editor_mode import UVPM3_Mode_GroupingEditor
from ...app_iface import *


class UVPM3_OT_EditGroupingSchemeInEditor(UVPM3_OT_Generic):

    bl_options = {'INTERNAL'}
    bl_idname = 'uvpackmaster3.edit_scheme_in_editor'
    bl_label = 'Edit Scheme In Editor'
    bl_description = "Edit the scheme in the Editor"

    g_scheme_uuid : StringProperty(name='', description='', default='')

    CONFIRMATION_MSG = 'The scheme was selected in the editor'

    @staticmethod
    def execute_impl(context, g_scheme_uuid, select_editor_with_shift=False):
        editor_mode = UVPM3_Mode_GroupingEditor(context)
        editor_mode.grouping_config.group_method_prop.set(GroupingMethod.MANUAL.code)
        editor_mode.grouping_config.get_scheme_access().set_active_g_scheme_uuid(g_scheme_uuid)

        bpy.ops.uvpackmaster3.select_multi_panel(panel_id=MULTI_PANEL_ID_GROUPING_EDITOR, shift=select_editor_with_shift, force_select=True)


    def execute(self, context):
        self.execute_impl(context, self.g_scheme_uuid)
        self.report({'INFO'}, self.CONFIRMATION_MSG)

        return {'FINISHED'}

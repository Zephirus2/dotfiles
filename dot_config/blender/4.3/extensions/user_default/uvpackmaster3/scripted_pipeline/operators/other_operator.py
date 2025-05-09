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


from ...enums import UvpmCoordSpace
from ...operator import UVPM3_OT_Generic, UVPM3_OT_Engine, OpConfirmationMsgMixin
from ...prefs_scripted_utils import ScriptParams
from ...utils import redraw_ui
from ...island_params import IParamInfo
from ...app_iface import *

class UVPM3_OT_OrientTo3dSpace(UVPM3_OT_Engine):

    bl_idname = 'uvpackmaster3.orient_to_3d_space'
    bl_label = 'Orient UVs'
    bl_description = "Rotate every selected UV island so that the resulting mapping transforms a given 3D axis to a given UV axis. Click the help button for more info"

    SCENARIO_ID = 'other.orient_to_3d_space'

    def skip_topology_parsing(self):
        return True
    
    def send_verts_3d(self):
        return self.scene_props.orient_to_3d_axes_space == UvpmCoordSpace.LOCAL.code

    def send_verts_3d_global(self):
        return self.scene_props.orient_to_3d_axes_space == UvpmCoordSpace.GLOBAL.code

    def setup_script_params(self):

        script_params = ScriptParams()

        script_params.add_param('prim_3d_axis', self.scene_props.orient_prim_3d_axis)
        script_params.add_param('prim_uv_axis', self.scene_props.orient_prim_uv_axis)
        script_params.add_param('sec_3d_axis', self.scene_props.orient_sec_3d_axis)
        script_params.add_param('sec_uv_axis', self.scene_props.orient_sec_uv_axis)
        script_params.add_param('axes_space', self.scene_props.orient_to_3d_axes_space)
        
        script_params.add_param('prim_sec_bias', self.scene_props.orient_prim_sec_bias)

        return script_params


class UVPM3_OT_RemoveDataFromObjects(UVPM3_OT_Generic, OpConfirmationMsgMixin):
    bl_idname = "uvpackmaster3.remove_data_from_objects"
    bl_label = "Remove UVPM Data From Objects"
    bl_description = "Remove UVPM data from selected objects (UVPM color attributes)"

    VCOLOR_CHANNEL_NAME_PREFIX = IParamInfo.VCOLOR_CHANNEL_NAME_PREFIX_BASE
    CONFIRMATION_MSG = 'The operation is going to remove all per-island assignments from the selected objects e.g. groups, island rotation step etc. Are you sure you want to continue?'

    def remove_color_attributes(self, obj):
        if obj.type != "MESH":
            return

        is_in_edit_mode = obj.mode == 'EDIT'

        if is_in_edit_mode:
            bm = bmesh.from_edit_mesh(obj.data)
        else:
            bm = bmesh.new()
            bm.from_mesh(obj.data)

        # Use bm loops layers instead color_attributes to keep compatibility with Blender 2.8-3.1
        color_attributes = bm.loops.layers.color
        for color_attribute_name in color_attributes.keys():
            if color_attribute_name.startswith(self.VCOLOR_CHANNEL_NAME_PREFIX):
                color_attributes.remove(color_attributes[color_attribute_name])

        int_attributes = bm.faces.layers.int
        for int_attribute_name in int_attributes.keys():
            if int_attribute_name.startswith(self.VCOLOR_CHANNEL_NAME_PREFIX):
                int_attributes.remove(int_attributes[int_attribute_name])

        if is_in_edit_mode:
            bmesh.update_edit_mesh(obj.data)
        else:
            bm.to_mesh(obj.data)
            bm.free()

    def execute(self, context):
        for obj in context.selected_objects:
            self.remove_color_attributes(obj)
        redraw_ui(context)
        return {"FINISHED"}

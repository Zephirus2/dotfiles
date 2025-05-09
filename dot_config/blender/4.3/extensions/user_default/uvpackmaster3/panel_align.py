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

from .multi_panel import MULTI_PANEL_ID_ALIGN
from .presets import UVPM3_PT_Presets
from .panel import UVPM3_PT_Generic, UVPM3_PT_Registerable, UVPM3_PT_IParamEditMixin
from .scripted_pipeline.operators.align_operator import UVPM3_OT_SelectSimilar, UVPM3_OT_AlignSimilar, UVPM3_OT_GroupBySimilarity


class UVPM3_PT_GenericAlign(UVPM3_PT_Generic):

    bl_category = 'UVPM3 - Aligning'

    MULTI_PANEL_ID = MULTI_PANEL_ID_ALIGN

    @classmethod
    def get_active_mode(cls, context):
        return None


class UVPM3_PT_MainAlign(UVPM3_PT_GenericAlign):

    bl_idname = 'UVPM3_PT_MainAlign'
    bl_label = 'Aligning'
    bl_context = ''

    HELP_URL_SUFFIX = '35-aligning-functionalities'
    PRESET_PANEL = UVPM3_PT_Presets

    def draw_header_preset(self, _context):
        UVPM3_PT_Presets.draw_panel_header(self.layout)

    def draw_impl(self, context):

        operators = [UVPM3_OT_SelectSimilar, UVPM3_OT_AlignSimilar, UVPM3_OT_GroupBySimilarity]

        layout = self.layout
        col = layout.column(align=True)

        for op in operators:
            row = col.row(align=True)
            row.operator(op.bl_idname)
        
    
class UVPM3_PT_SubPanelAlign(UVPM3_PT_GenericAlign, UVPM3_PT_Registerable):
    
    bl_parent_id = UVPM3_PT_MainAlign.bl_idname


class UVPM3_PT_IParamEditAlign(UVPM3_PT_IParamEditMixin, UVPM3_PT_SubPanelAlign):

    pass

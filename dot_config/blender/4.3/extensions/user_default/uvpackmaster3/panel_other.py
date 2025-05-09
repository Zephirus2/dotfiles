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


from .multi_panel import MULTI_PANEL_ID_OTHER
from .panel import UVPM3_PT_Generic, UVPM3_PT_Registerable



class UVPM3_PT_GenericOther(UVPM3_PT_Generic, UVPM3_PT_Registerable):

    bl_category = 'UVPM3 - Other'

    MULTI_PANEL_ID = MULTI_PANEL_ID_OTHER


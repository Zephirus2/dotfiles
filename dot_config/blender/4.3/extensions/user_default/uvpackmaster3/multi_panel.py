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


from .pgroup import standalone_property_group
from .app_iface import *


@standalone_property_group
class UVPM3_MultiPanelSettings:

    selected : BoolProperty(name='selected', default=True)

    def __init__(self, selected=True):
        self.selected = selected

    def copy_from(self, other):
        self.selected = bool(other.selected)


class UVPM3_SavedMultiPanelSettings(PropertyGroup):

    panel_id : StringProperty(name="", default="")
    settings : PointerProperty(type=UVPM3_MultiPanelSettings)


class MultiPanel:

    def __init__(self, id, name, icon=None, selected=False):
        self.id = id
        self.name = name
        self.icon = icon
        self.panels = []
        self.default_settings = UVPM3_MultiPanelSettings.SA(selected=selected)

        self.settings = UVPM3_MultiPanelSettings.SA()
        self.saved_settings_dict = None
        self.saved_settings = None

    def update_settings(self, saved_settings_dict):
        self.saved_settings_dict = saved_settings_dict
        self.saved_settings = self.saved_settings_dict.get(self.id)

        if self.saved_settings:
            self.settings.copy_from(self.saved_settings)
        else:
            self.settings.copy_from(self.default_settings)

    def save_settings(self):
        assert self.saved_settings_dict is not None

        if not self.saved_settings:
            self.saved_settings = self.saved_settings_dict[self.id]

        self.saved_settings.copy_from(self.settings)

    @property
    def selected(self):
        return self.settings.selected

    @selected.setter
    def selected(self, value):
        self.settings.selected = value
        self.save_settings()


MULTI_PANEL_ID_UTIL = 'util'
MULTI_PANEL_ID_PACK = 'pack'
MULTI_PANEL_ID_ALIGN = 'align'
MULTI_PANEL_ID_GROUPING_EDITOR = 'grouping_editor'
MULTI_PANEL_ID_OTHER = 'other'
MULTI_PANEL_ID_STATISTICS = 'statistics'
MULTI_PANEL_ID_ADDON_PREFERENCES = 'addon_preferences'


MULTI_PANELS = [
    MultiPanel(id=MULTI_PANEL_ID_UTIL, name='UTILITIES', selected=True, icon='TOOL_SETTINGS'),
    MultiPanel(id=MULTI_PANEL_ID_PACK, name='PACKING', selected=True, icon='EVENT_P'),
    MultiPanel(id=MULTI_PANEL_ID_ALIGN, name='ALIGNING', icon='EVENT_A'),
    MultiPanel(id=MULTI_PANEL_ID_GROUPING_EDITOR, name='GROUPING EDITOR', icon='EVENT_G'),
    MultiPanel(id=MULTI_PANEL_ID_OTHER, name='OTHER TOOLS', icon='EVENT_O'),
    MultiPanel(id=MULTI_PANEL_ID_STATISTICS, name='STATISTICS', icon='PROPERTIES'),
    MultiPanel(id=MULTI_PANEL_ID_ADDON_PREFERENCES, name='ADD-ON PREFERENCES', icon='SETTINGS')
]

       
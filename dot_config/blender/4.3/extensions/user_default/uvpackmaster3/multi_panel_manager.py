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


from .panel import UVPM3_PT_MainPack, UVPM3_PT_AdvancedPackOptions, UVPM3_PT_SPACE_TYPE, UVPM3_PT_REGION_TYPE, UVPM3_PT_CONTEXT
from .panel_align import UVPM3_PT_MainAlign
from .utils import CollectionPropertyDictWrapper
from .multi_panel import MULTI_PANELS
from .app_iface import *

from .scripted_pipeline.panels.pack_panels import *
from .scripted_pipeline.panels.align_panels import *
from .scripted_pipeline.panels.other_panels import *
from .scripted_pipeline.panels.grouping_editor_panels import *
from .help import UVPM3_OT_WarningPopup
from .pgroup import standalone_property_group

    
PANELS = [
    UVPM3_PT_Utilities,

    UVPM3_PT_MainPack,
    UVPM3_PT_PackOptions,
    UVPM3_PT_AdvancedPackOptions,
    UVPM3_PT_GroupingPack,

    UVPM3_PT_MainAlign,

    UVPM3_PT_GroupingEditor,

    UVPM3_PT_OrientTo3dSpace,
    UVPM3_PT_OtherUtilities,

    UVPM3_PT_Statistics,

    UVPM3_PT_AddonPreferences
]

CHILD_PANELS = [
    UVPM3_PT_TileSetup,
    UVPM3_PT_NormalizeScale,
    UVPM3_PT_PixelMargin,

    UVPM3_PT_Heuristic,
    UVPM3_PT_LockOverlapping,
    UVPM3_PT_LockGroups,
    UVPM3_PT_StackGroupsPack,
    UVPM3_PT_TrackGroups,
    UVPM3_PT_NonSquarePacking,
    UVPM3_PT_TargetBox,
    UVPM3_PT_IslandRotStep,
    UVPM3_PT_ScriptingPack,
    # UVPM3_PT_Help,

    UVPM3_PT_SchemeGroupsPack,
    UVPM3_PT_GroupTargetBoxesPack,

    UVPM3_PT_SimilarityOptions,
    UVPM3_PT_AlignPriority,
    UVPM3_PT_StackGroupsAlign,
    UVPM3_PT_SplitOverlapping,

    UVPM3_PT_SchemeGroupsGroupingEditor,
    UVPM3_PT_GroupTargetBoxesGroupingEditor
]


@standalone_property_group
class UVPM3_PanelSettings:

    expanded : BoolProperty(name='expanded', default=True)

    def __init__(self, panel_t=None):
        self.expanded = True
        if panel_t is not None and hasattr(panel_t, 'bl_options'):
            self.expanded = 'DEFAULT_CLOSED' not in panel_t.bl_options

    def copy_from(self, other):
        self.expanded = bool(other.expanded)


class UVPM3_SavedPanelSettings(PropertyGroup):

    panel_id : StringProperty(name="", default="")
    settings : PointerProperty(type=UVPM3_PanelSettings)


class PanelData:

    def __init__(self, panel_t):
        self.id = panel_t.bl_idname
        self.panel_t = panel_t
        self.ch_panels = []
        self.default_settings = UVPM3_PanelSettings.SA(panel_t)

        self.settings = UVPM3_PanelSettings.SA()
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
    def expanded(self):
        return self.settings.expanded

    @expanded.setter
    def expanded(self, value):
        self.settings.expanded = value
        self.save_settings()


class MultiPanelManager:

    def __init__(self):

        self.multi_panels = MULTI_PANELS
        self.m_panel_dict = { m_panel.id: m_panel for m_panel in self.multi_panels }
        self.panel_dict = {}

        for panel_t in PANELS:
            m_panel = self.m_panel_dict[panel_t.MULTI_PANEL_ID]
            panel_data = PanelData(panel_t)
            m_panel.panels.append(panel_data)
            self.panel_dict[panel_data.id] = panel_data

        for ch_panel_t in CHILD_PANELS:
            panel_data = self.panel_dict[ch_panel_t.bl_parent_id]
            ch_panel_data = PanelData(ch_panel_t)
            panel_data.ch_panels.append(ch_panel_data)
            self.panel_dict[ch_panel_data.id] = ch_panel_data

    def update_settings(self, scene_props):
        m_panel_settings_dict = CollectionPropertyDictWrapper(scene_props.saved_m_panel_settings, 'panel_id', 'settings')
        panel_settings_dict = CollectionPropertyDictWrapper(scene_props.saved_panel_settings, 'panel_id', 'settings')

        for m_panel in self.multi_panels:
            m_panel.update_settings(m_panel_settings_dict)

        for panel_data in self.panel_dict.values():
            panel_data.update_settings(panel_settings_dict)

    def get_multi_panel(self, m_panel_id):
        return self.m_panel_dict[m_panel_id]

    def get_panel_data(self, panel_id):
        return self.panel_dict[panel_id]


class PanelIdAttributeMixin:

    panel_id : StringProperty(name='', default='')


class UVPM3_OT_SelectMultiPanel(Operator, PanelIdAttributeMixin):

    bl_idname = 'uvpackmaster3.select_multi_panel'
    bl_label = 'Select Multi Panel'

    shift : BoolProperty(name='', default=False)
    force_select : BoolProperty(name='', default=False)

    @classmethod
    def description(cls, context, properties):

        mp_manager = get_prefs().get_multi_panel_manager(context)
        m_panel = mp_manager.get_multi_panel(properties.panel_id)

        return '{} (press with Shift to select multiple)'.format(m_panel.name)

    def invoke(self, context, event):

        self.shift = event.shift
        return self.execute(context)

    def execute(self, context):

        disable_box_rendering(None, context)

        selected_count = 0
        target_panel = None

        mp_manager = get_prefs().get_multi_panel_manager(context)

        for m_panel in mp_manager.multi_panels:

            if m_panel.selected:
                selected_count += 1

            if m_panel.id == self.panel_id:
                target_panel = m_panel

            if not self.shift:
                m_panel.selected = False

        if not target_panel:
            return {'CANCELLED'}
        
        if self.shift:
            if target_panel.selected and selected_count == 1:
                return {'CANCELLED'}
            
            select = True if self.force_select else not target_panel.selected
            target_panel.selected = select
        
        else:
            target_panel.selected = True

        return {'FINISHED'}


class UVPM3_OT_ExpandPanel(Operator, PanelIdAttributeMixin):

    bl_idname = 'uvpackmaster3.exapnd_panel'
    bl_label = 'Exapnd Panel'
    bl_description = 'Expand/hide the panel'

    expand : BoolProperty(name='', default=False)

    def execute(self, context):

        mp_manager = get_prefs().get_multi_panel_manager(context)
        panel_data = mp_manager.get_panel_data(self.panel_id)
        panel_data.expanded = self.expand

        return {'FINISHED'}


class UVPM3_PT_MultiPanels(Panel, PanelUtilsMixin):

    bl_space_type = UVPM3_PT_SPACE_TYPE
    bl_region_type = UVPM3_PT_REGION_TYPE
    bl_context = UVPM3_PT_CONTEXT
    bl_order = 1

    bl_category = 'UVPackmaster3'
    bl_idname = 'UVPM3_PT_MultiPanels'
    bl_label = 'UVPackmaster3'


    def draw_panel_header(self, context, panel_data, panel, layout):

        header_row_outer = layout.row(align=True)
        header_row_outer.scale_y = 0.8
        header_row = header_row_outer.row(align=True)

        panel_t = panel_data.panel_t
        expanded = panel_data.expanded
        not_supported_msg = panel.not_supported_msg(context)
        warning_msg = panel.warning_msg(context)
        supported = not_supported_msg is None
        expanded &= supported

        header_row.enabled = supported

        if hasattr(panel_t, 'draw_header'):
            # row = header_row.row(align=True)
            # row.alignment = 'LEFT'
            panel.layout = header_row
            panel.draw_header(context)

        expand_row = header_row.row()
        expand_row.alignment = 'LEFT'
        expand_op = expand_row.operator(UVPM3_OT_ExpandPanel.bl_idname, 
                                        text=panel_t.bl_label,
                                        icon='TRIA_DOWN' if expanded else 'TRIA_RIGHT',
                                        emboss=False)
        
        expand_op.panel_id = panel_data.id
        expand_op.expand = not expanded

        filler_row = header_row.row()

        if hasattr(panel_t, 'PRESET_PANEL'):
            preset_row = header_row.row()
            preset_row.alignment = 'RIGHT'

            preset_row.emboss = 'NONE'
            preset_row.popover(panel=panel_t.PRESET_PANEL.__name__, icon='PRESET', text="")

        if hasattr(panel_t, 'HELP_URL_SUFFIX'):
            help_row = header_row.row()
            help_row.alignment = 'RIGHT'
            self._draw_help_operator(help_row, panel_t.HELP_URL_SUFFIX)


        warning_text = not_supported_msg if not supported else warning_msg

        if warning_text is not None:
            warning_row = header_row_outer.row()
            warning_row.alignment = 'RIGHT'
            UVPM3_OT_WarningPopup.draw_operator(warning_row, text=warning_text)

        return expanded


    def draw(self, context):
        prefs = get_prefs()
        layout = self.layout

        hori_multi_panel_toggles = prefs.hori_multi_panel_toggles

        main_cont = layout.column(align=False) if hori_multi_panel_toggles else layout.row(align=False)
        toggle_cont = main_cont.row() if hori_multi_panel_toggles else main_cont.column()

        if hori_multi_panel_toggles:
            toggle_cont.alignment = 'LEFT'
            main_cont.separator()

        panel_col = main_cont.column(align=False)
        mp_manager = prefs.get_multi_panel_manager(context)

        for m_panel in mp_manager.multi_panels:

            toggle_row = toggle_cont.row()
            toggle_row.alignment = 'CENTER'
            toggle_op = toggle_row.operator(
                        UVPM3_OT_SelectMultiPanel.bl_idname,
                        icon=m_panel.icon if m_panel.icon else 'NONE',
                        depress=m_panel.selected,
                        emboss=True,
                        text="")
            
            toggle_op.panel_id = m_panel.id

            if not m_panel.selected:
                continue

            for panel_data in m_panel.panels:
                try:
                    panel_t = panel_data.panel_t

                    if hasattr(panel_t, 'poll') and not panel_t.poll(context):
                        continue

                    panel_box = panel_col.box()

                    panel = panel_t()
                    panel.multi_panel = True

                    expanded = self.draw_panel_header(context, panel_data, panel, panel_box)

                    if expanded:

                        panel.layout = panel_box
                        self.draw_engine_status(prefs, panel.layout)
                        panel.draw(context)

                        for ch_panel_data in panel_data.ch_panels:
                            try:

                                ch_panel_t = ch_panel_data.panel_t

                                if hasattr(ch_panel_t, 'poll') and not ch_panel_t.poll(context):
                                    continue

                                # panel_box.separator_spacer(factor=0.1)

                                ch_panel = ch_panel_t()
                                panel_col.separator(factor=0.5)
                                intend_factor = 0.001

                                if intend_factor > 0.0:
                                    ch_panel_split = panel_col.split(factor=intend_factor)
                                    margin_row = ch_panel_split.row()
                                    ch_panel_box = ch_panel_split.box()
                                else:
                                    ch_panel_box = panel_col.box()

                                
                                expanded = self.draw_panel_header(context, ch_panel_data, ch_panel, ch_panel_box)
                                
                                if not expanded:
                                    continue

                                intend_factor = 0.0

                                if intend_factor > 0.0:
                                    ch_panel_split = ch_panel_box.split(factor=intend_factor)
                                    margin_row = ch_panel_split.row()
                                    ch_panel_col = ch_panel_split.column(align=True)
                                else:
                                    ch_panel_col = ch_panel_box.column(align=True)
                                
                                ch_panel.layout = ch_panel_col
                                ch_panel.multi_panel = True
                                ch_panel.draw(context)

                            except Exception as ex:
                                if in_debug_mode():
                                    print_backtrace(ex)

                except Exception as ex:
                    if in_debug_mode():
                        print_backtrace(ex)

                panel_col.separator(factor=1.0)

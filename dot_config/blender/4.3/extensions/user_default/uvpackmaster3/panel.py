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


from .multi_panel import MULTI_PANEL_ID_PACK, MULTI_PANEL_ID_ADDON_PREFERENCES, MULTI_PANEL_ID_STATISTICS, MULTI_PANEL_ID_UTIL
from .app_iface import get_prefs
from .operator import *
from .utils import *
from .presets import *
from .mode import ModeType, UVPM3_MT_BrowseModes
from .scripted_pipeline.operators.util_operator import *


UVPM3_PT_SPACE_TYPE = 'IMAGE_EDITOR'
UVPM3_PT_REGION_TYPE = 'UI'
UVPM3_PT_CONTEXT = ''


class UVPM3_PT_Generic(PanelUtilsMixin):

    @classmethod
    def poll(cls, context):
        if not hasattr(cls, 'poll_impl'):
            return True
        
        try:
            cls.active_mode = cls.get_active_mode(context)
            return cls.poll_impl(context)
        except Exception as ex:
            if in_debug_mode():
                print_backtrace(ex)

        return False
        
    @classmethod
    def draw_expanded_enum(self, obj, prop_id, layout, item_enabled_checker=None):
        enum_values = AppInterface.object_property_data(obj)[prop_id].enum_items_static.keys()
        for enum_value in enum_values:
            row = layout.row(align=True)
            row.prop_enum(obj, prop_id, enum_value)
            if item_enabled_checker is not None:
                row.enabled = item_enabled_checker(enum_value)

    @classmethod
    def exclude_enum_item_checker(self, exclude_obj, prop_id):
        prop_value = getattr(exclude_obj, prop_id)
        return lambda enum_value: False if enum_value == prop_value else True

    @classmethod
    def handle_prop(self, obj, prop_id, layout, not_supported_msg=None, warning_msg=None):

        supported = not_supported_msg is None
        row = layout.row(align=True)

        prop_row = row.row(align=True)
        prop_row.prop(obj, prop_id)
        prop_row.enabled = supported

        warning_text =  not_supported_msg if not supported else warning_msg

        if warning_text is not None:
            from .help import UVPM3_OT_WarningPopup
            UVPM3_OT_WarningPopup.draw_operator(row, text=warning_text)
    
    def not_supported_msg(self, context):
        return None
    
    def warning_msg(self, context):
        return None

    def get_main_property(self):
        return None

    def draw_header(self, context):

        self.context = context

        main_property = self.get_main_property()
        if main_property is None:
            return

        layout = self.layout

        # col = layout.column()
        row = layout.row()
        main_property.draw(row, text='')
        # row.row()

    def draw(self, context):
        self.init_draw(context)

        main_property = self.get_main_property()

        if main_property is not None:
            self.layout.enabled = main_property.get()
        
        self.draw_impl(context)

    @classmethod
    def prop_with_help(cls, obj, prop_id, layout, help_url_suffix=None):

        row = layout.row(align=True)
        row.prop(obj, prop_id)

        if help_url_suffix:
            cls._draw_help_operator(row, help_url_suffix)

    @classmethod
    def operator_with_help(cls, op_idname, layout, text=None, help_url_suffix=None):
        row = layout.row(align=True)
        kwargs = {}
        if text:
            kwargs['text'] = text

        op = row.operator(op_idname, **kwargs)

        if help_url_suffix:
            cls._draw_help_operator(row, help_url_suffix)

        return op

    @classmethod
    def operator_attach_mode(cls, op_idname, mode_id, layout, text=None, help_url_suffix=None):
        op = cls.operator_with_help(op_idname, layout, text=text, help_url_suffix=help_url_suffix)
        if (hasattr(op, 'mode_id')):
            op.mode_id = mode_id

        return op

    def handle_prop_enum(self, obj, prop_name, prop_label, supported, not_supported_msg, layout):

        prop_label_colon = prop_label + ':'

        if supported:
            layout.label(text=prop_label_colon)
        else:
            split = layout.split(factor=0.4)
            col_s = split.column()
            col_s.label(text=prop_label_colon)
            col_s = split.column()
            col_s.label(text=not_supported_msg)

        layout.prop(obj, prop_name, text='')
        layout.enabled = supported

    def messages_in_boxes(self, ui_elem, messages):

        for msg in messages:
            box = ui_elem.box()

            msg_split = split_by_chars(msg, 60)
            if len(msg_split) > 0:
                # box.separator()
                for msg_part in msg_split:
                    box.label(text=msg_part)
                # box.separator()


class UVPM3_PT_GenericPack(UVPM3_PT_Generic):

    bl_category = 'UVPM3 - Packing'
    MULTI_PANEL_ID = MULTI_PANEL_ID_PACK

    @classmethod
    def get_active_mode(cls, context):
        return get_prefs().get_active_main_mode(context)


class UVPM3_PT_AddonPreferences(UVPM3_PT_Generic):

    bl_idname = 'UVPM3_PT_AddonPreferences'
    bl_context = ''
    bl_order = 0
    bl_label = 'Add-on Preferences'

    MULTI_PANEL_ID = MULTI_PANEL_ID_ADDON_PREFERENCES


    def draw_impl(self, context):

        layout = self.layout
        col = layout.column(align=True)
        
        self.prefs.draw_addon_preferences(col)

        if in_debug_mode():
            col.separator()

            dopt_layout = col
            dopt_layout.label(text="Debug options:")

            box = dopt_layout.box() 
            row = box.row(align=True)
            row.prop(self.prefs, "script_allow_execution")

            box = dopt_layout.box() 
            row = box.row(align=True)
            row.prop(self.prefs, "pixel_margin_warn_dismissed")

            box = dopt_layout.box()
            row = box.row(align=True)
            row.prop(self.prefs, "write_to_file")

            box = dopt_layout.box() 
            row = box.row(align=True)
            row.prop(self.prefs, "wait_for_debugger")

            row = dopt_layout.row(align=True)
            row.prop(self.prefs, "seed")
            row = dopt_layout.row(align=True)
            row.prop(self.prefs, "test_param")

            from .debug import UVPM3_OT_Debug
            dopt_layout.operator(UVPM3_OT_Debug.bl_idname)
            

class UVPM3_PT_Utilities(UVPM3_PT_Generic):

    bl_idname = 'UVPM3_PT_Utilities'
    bl_label = 'Utilities'
    bl_context = ''

    MULTI_PANEL_ID = MULTI_PANEL_ID_UTIL

    def draw_impl(self, context):

        layout = self.layout
        col = layout.column(align=True)

        # util_modes = self.prefs.get_modes(ModeType.UTIL)

        # if len(util_modes) > 0:
        #     for mode_id, mode_cls in util_modes:
        #         row = col.row(align=True)
        #         row.operator(mode_cls.OPERATOR_IDNAME)

        row = col.row(align=True)
        row.operator(UVPM3_OT_OverlapCheck.bl_idname)

        row = col.row(align=True)
        split = row.split(factor=0.7, align=True)

        row = split.row(align=True)
        op = row.operator(UVPM3_OT_MeasureArea.bl_idname)
        op.merged = False

        row = split.row(align=True)
        op = row.operator(UVPM3_OT_MeasureArea.bl_idname, text='(Merged)')
        op.merged = True

        row = col.row(align=True)
        row.operator(UVPM3_OT_AdjustTdToUnselected.bl_idname)


class UVPM3_PT_MainPack(UVPM3_PT_GenericPack):

    bl_idname = 'UVPM3_PT_MainPack'
    bl_label = 'Packing'
    bl_context = ''

    PRESET_PANEL = UVPM3_PT_Presets

    def draw_header_preset(self, _context):
        UVPM3_PT_Presets.draw_panel_header(self.layout)

    def draw_impl(self, context):

        layout = self.layout
        col = layout.column(align=True)
        row = col.row(align=True)

        active_mode = self.prefs.get_active_main_mode(context)
        row.menu(UVPM3_MT_BrowseModes.bl_idname, text=type(active_mode).enum_name(), icon='COLLAPSEMENU')

        if active_mode.MODE_HELP_URL_SUFFIX:
            from .help import UVPM3_OT_MainModeHelp
            help_op = row.operator(UVPM3_OT_MainModeHelp.bl_idname, icon=UVPM3_OT_MainModeHelp.ICON, text='')
            help_op.url_suffix = active_mode.MODE_HELP_URL_SUFFIX

        col.separator()

        mode = self.prefs.get_active_main_mode(context)
        mode_layout = col
        mode.draw(mode_layout)


class UVPM3_PT_AdvancedPackOptions(UVPM3_PT_GenericPack):

    bl_idname = 'UVPM3_PT_AdvancedPackOptions'
    bl_label = 'Advanced Packing Options'
    bl_context = ''

    bl_options = {'DEFAULT_CLOSED'}

    def draw_impl(self, context):
        col = self.layout.column(align=True)
        self.scene_props.pack_strategy_props.draw(col)


class UVPM3_PT_Statistics(UVPM3_PT_Generic):

    bl_idname = 'UVPM3_PT_Statistics'
    bl_label = 'Statistics'

    MULTI_PANEL_ID = MULTI_PANEL_ID_STATISTICS

    def draw_impl(self, context):
        layout = self.layout
        col = layout.column(align=True)
        box = col.box()
        box.label(text='Last operation statistics:')

        for idx, dev in enumerate(self.prefs.device_array()):
            col.separator()
            col.label(text=dev.name)
            box = col.box()
            box.label(text='Iteration count: ' + str(dev.bench_entry.iter_count))

            box = col.box()
            box.label(text='Total packing time: ' + str(dev.bench_entry.total_time) + ' ms')

            box = col.box()
            box.label(text='Average iteration time: ' + str(dev.bench_entry.avg_time) + ' ms')


class UVPM3_PT_Registerable:

    bl_order = 10
    PANEL_PRIORITY = sys.maxsize


class UVPM3_PT_SubPanelPack(UVPM3_PT_GenericPack, UVPM3_PT_Registerable):
    
    bl_parent_id = UVPM3_PT_MainPack.bl_idname

    @classmethod
    def poll_impl(cls, context):
        return cls.bl_idname in cls.active_mode.subpanels_base()
        

class UVPM3_PT_IParamEditMixin:

    def get_main_property(self):
        from .operator_islands import UVPM3_OT_StdIParamGeneric
        return UVPM3_OT_StdIParamGeneric.get_iparam_info_impl(self.IPARAM_INFO_TYPE).get_enabled_property(self.context)

    def draw_impl(self, context):
        from .operator_islands import IParamEditUI
        IParamEditUI(context, self.scene_props, self.IPARAM_INFO_TYPE, self.HELP_URL_SUFFIX if self.props_with_help else None).draw(self.layout)

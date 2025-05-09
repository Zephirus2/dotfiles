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


import os
import json
import traceback
import sys
from collections import defaultdict
import textwrap

from .connection import *
# from .prefs import *
from .enums import *
from .os_iface import *
from .app_iface import *


def get_engine_path():
    return get_prefs().engine_path


def get_engine_execpath():
    engine_basename = 'uvpm'
    return os.path.join(get_engine_path(), os_exec_dirname(), engine_basename + os_exec_extension())


def process_file_path(file_path):
    return os.path.realpath(file_path)


def in_debug_mode(debug_lvl = 1):
    return AppInterface.debug_value() >= debug_lvl or AppInterface.debug()


def split_by_chars(str, cnt):
    str_split = str.split()

    array = []
    curr_str = ''
    curr_cnt = 0

    for word in str_split:
        curr_str += ' ' + word
        curr_cnt += len(word)

        if curr_cnt > cnt:
            array.append((curr_str))
            curr_str = ''
            curr_cnt = 0

    if curr_str != '':
        array.append((curr_str))

    return array
        

def print_backtrace(ex):
    print('[UVPACKMASTER ERROR BEGIN]:')
    _, _, trback = sys.exc_info()
    traceback.print_tb(trback)
    trbackDump = traceback.extract_tb(trback)
    filename, line, func, msg = trbackDump[-1]

    print('Line: {} Message: {}'.format(line, msg))
    print(str(ex))
    print('[UVPACKMASTER ERROR END]')


def print_debug(debug_str):
    print('[UVPACKMASTER_DEBUG]: ' + debug_str)


def print_log(log_str):
    print('[UVPACKMASTER_LOG]: ' + log_str)


def print_error(error_str):
    print('[UVPACKMASTER_ERROR]: ' + error_str)


def print_warning(warning_str):
    print('[UVPACKMASTER_WARNING]: ' + warning_str)


def log_separator():
    return '-'*80


def rgb_to_rgba(rgb_color):

    return (rgb_color[0], rgb_color[1], rgb_color[2], 1.0)


def redraw_ui(context):

    for area in context.screen.areas:
        if area is not None:
            area.tag_redraw()


def get_active_image_size(context):

    img = None
    for area in context.screen.areas:
        if area.type == 'IMAGE_EDITOR':
            img = area.spaces.active.image

    if img is None:
        raise RuntimeError("Non-Square Packing: active texture required for the operation")

    if img.size[0] == 0 or img.size[1] == 0:
        raise RuntimeError("Non-Square Packing: active texture has invalid dimensions")

    return (img.size[0], img.size[1])


def get_active_image_ratio(context):

    img_size = get_active_image_size(context)

    return float(img_size[0]) / float(img_size[1])


def parse_json_file(json_file_path):
    with open(json_file_path) as f:
        try:
            data = json.load(f)
        except Exception as e:
            if in_debug_mode():
                print_backtrace(e)
            data = None
    return data


def unique_min_num(num_list, num_from=0):
    if not num_list:
        return num_from
    counter = num_from
    while True:
        counter += 1
        if counter in num_list:
            continue
        return counter


def unique_name(value, collection, instance=None):
    if collection.find(value) > -1:
        name_parts = value.rsplit(".", 1)
        base_name = name_parts[0]
        name_num_list = []
        found = 0
        same_found = 0
        for element in collection:
            if element == instance:
                continue

            if element.name.startswith(base_name):
                if element.name == value:
                    same_found += 1
                element_name_parts = element.name.rsplit(".", 1)
                if element_name_parts[0] != base_name:
                    continue
                found += 1
                if len(element_name_parts) < 2 or not element_name_parts[1].isnumeric():
                    continue
                name_num_list.append(int(element_name_parts[1]))

        if found > 0 and same_found > 0:
            return "{}.{:03d}".format(base_name, unique_min_num(name_num_list or [0]))
    return value


def snake_to_camel_case(snake_case_str):
    words = snake_case_str.split('_')
    camel_case_str = ''.join(word.capitalize() for word in words)
    return camel_case_str


def swap_attr(obj1, obj2, attr_name):
    tmp = getattr(obj1, attr_name)
    setattr(obj1, attr_name, getattr(obj2, attr_name))
    setattr(obj2, attr_name, tmp)


def is_builtin_class_instance(obj):
    return obj.__class__.__module__ == '__builtin__'


def clamp(x, _min, _max):
    return max(_min, min(x, _max))


class ShadowedCollectionProperty:

    def __init__(self, elem_type, factory=None, remove_callback=None):

        self.elem_type = elem_type
        self.collection = []
        self.key_id = 'name'
        self.factory = factory if factory else lambda: self.elem_type()
        self.remove_callback = remove_callback

    def copy_from(self, other):
        self.clear()
        for other_elem in other:
            new_elem = self.add()
            new_elem.copy_from(other_elem)

    def add(self):
        self.collection.append(self.factory())
        return self.collection[-1]
    
    def append(self, elem):
        self.collection.append(elem)

    def clear(self):

        if self.remove_callback:
            while len(self) > 0:
                self.remove(0)
            return
        
        self.collection.clear()

    def remove(self, idx):

        elem_to_del = self.collection[idx]
        del self.collection[idx]

        if self.remove_callback:
            self.remove_callback(elem_to_del)

    def find(self, key):
        try:
            first_idx = next(idx for idx, elem in enumerate(self) if getattr(elem, self.key_id) == key)
            return first_idx
        except StopIteration:
            pass

        return -1

    def __len__(self):

        return len(self.collection)

    def __getitem__(self, idx):

            return self.collection[idx]

    def __iter__(self):

        return iter(self.collection)
        

class PropertyWrapper:

    def __init__(self, obj, prop_id):
        self.obj = obj
        self.prop_id = prop_id

    def get(self):
        return getattr(self.obj, self.prop_id)
    
    def set(self, value):
        setattr(self.obj, self.prop_id, value)
    
    def draw(self, layout, text=None):
        kwargs = {}
        if text is not None:
            kwargs['text'] = text

        layout.prop(self.obj, self.prop_id, **kwargs)

    def get_name(self):
        return self.property_data().name if hasattr(self.obj, self.prop_id) else ''
    
    def property_data(self):
        return AppInterface.object_property_data(self.obj)[self.prop_id]

    def to_script_param(self):
        from .prefs_scripted_utils import ScriptParams
        return ScriptParams.to_param(self.get())

        
class CollectionPropertyDictWrapper:

    def __init__(self, collection, key_name, value_name):
        self.collection = collection
        self.key_name = key_name
        self.value_name = value_name
        self.dict = { getattr(elem, self.key_name): getattr(elem, self.value_name) for elem in self.collection }

    def get(self, key):

        return self.dict.get(key)

    def __getitem__(self, key):

        value = self.get(key)
        if value is not None:
            return value
            
        new_elem = self.collection.add()
        setattr(new_elem, self.key_name, key)
        new_value = getattr(new_elem, self.value_name)
        self.dict[key] = new_value
        return new_value
    

class UVPM3_OT_DismissWarning(Operator):

    bl_label = 'Dismiss'
    bl_idname = 'uvpackmaster3.dismiss_warning'

    dismissed_prop_id : StringProperty(name='', default='')

    def execute(self, context):
        prefs = get_prefs()

        dismissed_prop = PropertyWrapper(prefs, self.dismissed_prop_id)
        dismissed_prop.set(True)
        
        save_prefs_op = AppInterface.save_preferences_operator()
        if save_prefs_op:
            AppInterface.exec_operator(save_prefs_op.bl_idname)

        return {'FINISHED'}
    

class PanelUtilsMixin:

    @staticmethod
    def draw_prop_saved_state(obj, prop_id, layout):
        col = layout.column(align=True)

        prop = PropertyWrapper(obj, prop_id)
        prop_saved = PropertyWrapper(obj, prop_id + '_saved')

        prop.draw(col)

        if prop.get() != prop_saved.get():
            col.label(text='Press the Save Preferences button below and', icon='ERROR')
            col.label(text='restart the application for the change to take effect')



    @staticmethod
    def create_split_columns(layout, factors):
        cols = []
        space_left = 1.0
        prev_split = layout

        for factor in factors:
            new_split = prev_split.split(factor=factor / space_left, align=True)
            space_left -= factor

            cols.append(new_split.column(align=True))
            prev_split = new_split

        cols.append(prev_split.column(align=True))
        return cols

    @classmethod
    def _draw_help_operator(cls, layout, help_url_suffix):
        from .help import UVPM3_OT_Help
        help_op = layout.operator(UVPM3_OT_Help.bl_idname, icon=UVPM3_OT_Help.ICON, text='')
        help_op.url_suffix = help_url_suffix

    @classmethod
    def _draw_help_popover(cls, layout, help_panel_t):
        help_row = layout.row()
        help_row.emboss = 'NONE'
        help_row.popover(panel=help_panel_t.__name__, icon=help_panel_t.ICON, text="")

    @classmethod
    def _draw_multiline_label(cls, layout, text, width):
        chars = int(width / 6)
        wrapper = textwrap.TextWrapper(width=chars)
        text_lines = wrapper.wrap(text=text)
        for text_line in text_lines:
            layout.label(text=text_line)

    @staticmethod
    def draw_engine_status(prefs, layout):
        if not prefs.engine_initialized:
            box = layout.box()
            box.alert = True
            prefs.draw_engine_status(box)

    @staticmethod
    def draw_prop_name_up(obj, prop_id, layout):
        col = layout.column(align=True)
        col.label(text=PropertyWrapper(obj, prop_id).get_name() + ':')
        col.prop(obj, prop_id, text='')

    @staticmethod
    def draw_prop_with_set_menu(obj, prop_id, layout, menu_class, not_supported_msg=None):
        row = layout.row(align=True)
        split = row.split(factor=0.8, align=True)

        col_s = split.row(align=True)
        col_s.prop(obj, prop_id)
        col_s = split.row(align=True)
        col_s.menu(menu_class.bl_idname, text='Set')

        if not_supported_msg is not None:
            split.enabled = False
            from .help import UVPM3_OT_WarningPopup
            UVPM3_OT_WarningPopup.draw_operator(row, text=not_supported_msg)

    @classmethod
    def draw_enum_in_box(
            cls,
            obj,
            prop_id,
            layout,
            help_url_suffix=None,
            expand=False,
            not_supported_msg=None,
            warning_msg=None,
            prop_name=None):

        supported = not_supported_msg is None
        prop_kwargs = { 'expand' : expand }
        if not expand:
            prop_kwargs['text'] = ''

        box = layout.box()
        col = box.column(align=True)

        if prop_name is None:
            prop_name = PropertyWrapper(obj, prop_id).get_name()

        if prop_name:
            label_row = col.row(align=True)
            label_row.label(text=prop_name + ':')
            label_row.enabled = supported
            
        row = col.row(align=True)
        prop_row = row.row(align=True)
        prop_row.prop(obj, prop_id, **prop_kwargs)
        prop_row.enabled=supported

        if help_url_suffix:
            cls._draw_help_operator(row, help_url_suffix)

        warning_text = not_supported_msg if not supported else warning_msg

        if warning_text is not None:
            from .help import UVPM3_OT_WarningPopup
            UVPM3_OT_WarningPopup.draw_operator(row, text=warning_text)

        return col

    @classmethod
    def get_active_mode(cls, context):
        return None
    
    def draw_dismissable_warning(self, dismissed_prop_id, warning_msgs, layout):
        dismissed_prop = PropertyWrapper(self.prefs, dismissed_prop_id)

        if not dismissed_prop.get():
            box = layout.box()
            col = box.column(align=True)
            col.label(text='WARNING:', icon='ERROR')

            for msg in warning_msgs:
                col.label(text=msg)

            col.separator()
            op = col.operator(UVPM3_OT_DismissWarning.bl_idname)
            op.dismissed_prop_id = dismissed_prop_id

            layout.separator()

    def init_draw(self, context):

        self.prefs = get_prefs()
        self.scene_props = get_scene_props(context)
        self.scripted_props = self.scene_props.scripted_props
        self.context = context

        if not hasattr(self, 'multi_panel'):
            self.multi_panel = False

        self.props_with_help = not self.multi_panel
        self.active_mode = self.get_active_mode(context)

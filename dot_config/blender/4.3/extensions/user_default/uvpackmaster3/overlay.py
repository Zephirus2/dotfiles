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

from html.parser import HTMLParser

from .enums import OperationStatus, UvpmLogType
from .utils import in_debug_mode, print_backtrace, get_prefs
from .app_iface import *


if AppInterface.APP_VERSION >= (4, 0, 0):
    def blf_size(fontid, size, dpi):
        blf.size(fontid, size)
else:
    def blf_size(fontid, size, dpi):
        blf.size(fontid, size, dpi)


class TextOverlay:

    def __init__(self, text, color, font_size=None):
        self.coords = None
        self.text = text
        self.color = color
        self.font_size = font_size

    def set_coords(self, coords):
        self.coords = coords


class ParsedText:
    
    def __init__(self, text, chunks):
        self.text = text
        self.chunks = chunks

    def __str__(self):
        return self.text

    def __add__(self, other):
        if isinstance(other, str):
            return ParsedText(self.text + other, self.chunks + [TextOverlay(other, None)])
        if isinstance(other, ParsedText):
            return ParsedText(self.text + other.text, self.chunks + other.chunks)
        return self

    def __radd__(self, other):
        if isinstance(other, str):
            return ParsedText(other + self.text, [TextOverlay(other, None)] + self.chunks)
        if isinstance(other, ParsedText):
            return ParsedText(other.text + self.text, other.chunks + self.chunks)
        return self

    def __len__(self):
        return len(self.text)
    
    def startswith(self, str):
        if len(self) == 0:
            return str == ''
        
        return self.chunks[0].text.startswith(str)


class TextOverlayParser(HTMLParser):
    """
    Markup syntax: [TEXT]<tag attr=value ...>[INNER_TEXT]</tag>[TEXT]...
    Example: This is default color, <t color="1, 0, 0, 1">this is red text, <t color="#0000ff"> is nested blue color text</t> and again red text</t>

    Tag: any string at this moment
    Attributes:
        color - tuple of 3 or 4, comma seperated floats or css-like hex, or defined in COLORS_DICT dict
    """
    # A dict to store predefined colors, eg: "red", "blue" or the purpose eg: "error", "warning"
    COLORS_DICT = {
        "red" : (1, 0, 0, 1),
        "green" : (0, 1, 0, 1),
        "blue" : (0, 0, 1, 1),

        "warning" : (1, 0.4, 0, 1),
        "error" : (1, 0, 0, 1)
    }

    def __init__(self):
        super().__init__()
        self.chunks = [self._create_new_chunk()]
        self.chunks_level_map = {0: [self.chunks[0]]}
        self.current_chunk_index = 0
        self.current_level = 0

    @staticmethod
    def _create_new_chunk():
        new_chunk = TextOverlay("", None)
        return new_chunk

    def _get_current_chunk(self):
        if self.current_chunk_index < len(self.chunks):
            return self.chunks[self.current_chunk_index]

        new_chunk = self._create_new_chunk()
        if self.current_level in self.chunks_level_map:
            level_chunks = self.chunks_level_map[self.current_level]
            # copy attributes from last chunk in a level to ensure consistency when nested
            prev_level_chunk = level_chunks[-1]
            new_chunk.color = prev_level_chunk.color
        else:
            level_chunks = []
            self.chunks_level_map[self.current_level] = level_chunks
        level_chunks.append(new_chunk)
        self.chunks.append(new_chunk)
        return new_chunk

    def _start_level(self):
        self.current_chunk_index += 1
        self.current_level += 1

    def _end_level(self):
        self.current_chunk_index += 1
        self.current_level -= 1

    def _parse_attr(self, name, value):
        chunk = self._get_current_chunk()
        if name == "color":
            chunk.color = self._parse_color(value)

    @classmethod
    def _parse_color(cls, color_string):
        color = None
        if color_string in cls.COLORS_DICT:
            color = cls.COLORS_DICT[color_string]

        if color_string.startswith("#"):
            color_string = color_string.lstrip('#')
            color_string_len = len(color_string)
            if color_string_len == 0:
                return color
            if color_string_len in [3, 4]:
                color_string_last = color_string[-1]
                color_string = color_string[0]*2 + color_string[1]*2 + color_string[2]*2
                if color_string_len == 4:
                    color_string += color_string_last*2
                else:
                    color_string += "ff"
                    color_string_len = 4
            if color_string_len == 6:
                color_string += "ff"
                color_string_len = 8
            if color_string_len != 8:
                color_string = (color_string + 8 * color_string[-1])[:8]
            try:
                color = tuple(int(color_string[i:i + 8 // 4], 16)/255 for i in range(0, 8, 8 // 4))
            except ValueError:
                pass
        else:
            char_to_remove = ["(", ")"]
            for char in char_to_remove:
                color_string = color_string.replace(char, "")
            color_split = color_string.split(",")
            try:
                color_split = tuple(float(c.strip()) for c in color_split)
                if len(color_split) == 3:
                    color_split += (1,)
                if len(color_split) == 4:
                    color = color_split
            except ValueError:
                pass
        return color

    def handle_starttag(self, tag, attrs):
        self._start_level()
        for name, value in attrs:
            self._parse_attr(name, value)

    def handle_data(self, data):
        chunk = self._get_current_chunk()
        chunk.text = data

    def handle_endtag(self, tag):
        self._end_level()

    @staticmethod
    def parse_text(text):
        if text is None:
            text = ""
        parser = TextOverlayParser()
        parser.feed(text)

        inner_text = ""
        chunks = []
        for chunk in parser.chunks:
            if chunk.text != "":
                chunks.append(chunk)
                inner_text += chunk.text

        return ParsedText(inner_text, chunks)


class OverlayManager:

    LINE_X_COORD = 10
    LINE_Y_COORD = 35
    LINE_TEXT_COLOR = (1, 1, 1, 1)

    def __init__(self, context, callback):

        prefs = get_prefs()
        self.font_size = prefs.font_size_text_output
        self.line_distance = int(float(25) / 15 * self.font_size)

        self.font_id = 0
        self.curr_font_size = None
        self.context = context

        handler_args = (self, context)
        self.__draw_handler = SpaceImageEditor.draw_handler_add(callback, handler_args, 'WINDOW', 'POST_PIXEL')

    def finish(self):

        if self.__draw_handler is not None:
            SpaceImageEditor.draw_handler_remove(self.__draw_handler, 'WINDOW')

    def set_font_size(self, font_size, force=False):
        if not force and font_size == self.curr_font_size:
            return
        
        blf_size(self.font_id, font_size, 72)
        self.curr_font_size = font_size

    def print_text_overlay(self, text, coords=None, color=None, z_coord=0.0, offset=None):
        text_coords = text.coords if text.coords is not None else coords
        if text_coords is None:
            return

        offset, calc_ret_offset = (0.0, False) if offset is None else (offset, True)

        text_font_size = text.font_size if text.font_size is not None else self.font_size
        self.set_font_size(text_font_size)

        text_color = text.color if text.color is not None else color
        blf.color(self.font_id, *text_color)
        blf.position(self.font_id, text_coords[0] + offset, text_coords[1], z_coord)
        blf.draw(self.font_id, text.text)
        return blf.dimensions(self.font_id, text.text)[0] if calc_ret_offset else None

    def print_text(self, coords, text, color, z_coord=0.0):

        self.set_font_size(self.font_size, force=True)

        if isinstance(text, str):
            blf.color(self.font_id, *color)
            blf.position(self.font_id, coords[0], coords[1], z_coord)
            blf.draw(self.font_id, text)
        elif isinstance(text, TextOverlay):
            self.print_text_overlay(text, coords, color, z_coord=z_coord, offset=offset)
        elif isinstance(text, ParsedText):
            offset = 0.0
            for text_chunk in text.chunks:
                offset += self.print_text_overlay(text_chunk, coords, color, z_coord=z_coord, offset=offset)
        else:
            assert False

        blf.color(self.font_id, *(0, 0, 0, 1))

    def __print_text_inline(self, line_num, text, color):

        x_coord = self.LINE_X_COORD
        y_coord = self.LINE_Y_COORD + line_num * self.line_distance
        self.print_text((x_coord, y_coord), text, color)

    def print_text_inline(self, text, color=LINE_TEXT_COLOR):
        self.__print_text_inline(self.next_line_num, text, color)
        self.next_line_num += 1

    def callback_begin(self):

        self.next_line_num = 0



class EngineOverlayManager(OverlayManager):

    WARNING_COLOR = (1, 0.4, 0, 1)
    ERROR_COLOR = (1, 0, 0, 1)
    DISABLED_DEVICE_COLOR_MULTIPLIER = 0.7

    INTEND_STR = '  '

    OPSTATUS_TO_COLOR = {
        OperationStatus.ERROR : TextOverlayParser.COLORS_DICT['error'],
        OperationStatus.WARNING : TextOverlayParser.COLORS_DICT['warning'],
        OperationStatus.CORRECT : OverlayManager.LINE_TEXT_COLOR
    }

    def __init__(self, op, dev_array):
        super().__init__(op.p_context.context, engine_overlay_manager_draw_callback)
        
        self.op = op
        self.dev_array = dev_array
        self.print_dev_progress = True
        self.p_context = op.p_context
        self.log_manager = op.log_manager

        self.font_id = 0

    def set_dirty(self):
        pass

    def print_dev_array(self):
        if self.dev_array is None:
            return

        for dev in reversed(self.dev_array):
            dev_color = self.LINE_TEXT_COLOR

            if self.print_dev_progress:
                progress_str = "{}% ".format(dev.bench_entry.progress)
            else:
                progress_str = ''

            if dev.settings.enabled:
                dev_status = "{}(iterations: {})".format(progress_str, dev.bench_entry.iter_count)
            else:
                dev_status = 'disabled'
                dev_color = tuple(self.DISABLED_DEVICE_COLOR_MULTIPLIER * c for c in dev_color)

            self.print_text_inline(self.INTEND_STR + dev.name + ": " + dev_status, color=dev_color)

        self.print_text_inline("[PACKING DEVICES]:")

    def print_list(self, header, list, color):
        for elem in reversed(list):
            self.print_text_inline(self.INTEND_STR + "* " + elem, color=color)

        self.print_text_inline("["+header+"]:", color=color)


def engine_overlay_manager_draw_callback(self, context):

    try:
        self.callback_begin()

        status_str = self.log_manager.last_log(UvpmLogType.STATUS)
        if status_str is None:
            status_str = ''

        status_color = self.OPSTATUS_TO_COLOR[self.log_manager.operation_status()]
        hint_str = self.log_manager.last_log(UvpmLogType.HINT)

        if hint_str.startswith('('):
            hint_prefix = ' '
            hint_suffix = ''
        else:
            hint_prefix = ' ('
            hint_suffix = ')'

        if hint_str:
            status_str = status_str + hint_prefix + hint_str + hint_suffix

        self.print_text_inline('[STATUS]: ' + status_str, color=status_color)
        self.print_dev_array()

        log_print_metadata = (\
            (UvpmLogType.INFO,   'INFO'),
            (UvpmLogType.WARNING,'WARNINGS'),
            (UvpmLogType.ERROR,  'ERRORS')
        )

        for log_type, header in log_print_metadata:
            op_status = self.log_manager.LOGTYPE_TO_OPSTATUS[log_type]
            color = self.OPSTATUS_TO_COLOR[op_status]
            
            log_list = self.log_manager.log_list(log_type)
            if len(log_list) > 0:
                self.print_list(header, log_list, color)

        if self.p_context.p_islands is not None:
            for p_island in self.p_context.p_islands:
                overlay = p_island.overlay()

                if overlay is not None:
                    self.print_text_overlay(overlay)

    except Exception as ex:
        if in_debug_mode():
            print_backtrace(ex)


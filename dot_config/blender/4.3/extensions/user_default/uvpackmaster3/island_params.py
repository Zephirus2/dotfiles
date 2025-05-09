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


from .connection import encode_string, decode_string, force_read_int
from .enums import *
from .utils import rgb_to_rgba, PropertyWrapper
from .pack_context import PackContext
from .app_iface import get_scene_props

import struct


class IParamInfo:

    PARAM_TYPE = int
    PARAM_TYPE_MARK = 'i'
    TEXT_TYPE = PARAM_TYPE
    VALUE_PROP_ID = None
    
    DEFAULT_VALUE_TEXT = None
    TEXT_SUFFIX = None

    VCOLOR_CHANNEL_NAME_PREFIX_BASE = '__uvpm3'
    VCOLOR_CHANNEL_NAME_PREFIX_VERSION = '_v3_'
    VCOLOR_CHANNEL_NAME_PREFIX = VCOLOR_CHANNEL_NAME_PREFIX_BASE + VCOLOR_CHANNEL_NAME_PREFIX_VERSION

    VCOLOR_CHANNEL_COUNT = 3
    VCOLOR_CHANNEL_VALUE_COUNT = 256
    VCOLOR_CHANNEL_MAX_VALUE = VCOLOR_CHANNEL_VALUE_COUNT-1

    INT_TO_VCOLOR_CH = (lambda self, input: float(input) / (IParamInfo.VCOLOR_CHANNEL_MAX_VALUE))
    VCOLOR_CH_TO_INT = (lambda self, input: int(input * (IParamInfo.VCOLOR_CHANNEL_MAX_VALUE)))

    INDEX = -1

    def __init__(self, script_name, label, min_value, max_value, default_value=None):
        self.label = label
        self.script_name = script_name
        self.min_value = self.PARAM_TYPE(min_value)
        self.max_value = self.PARAM_TYPE(max_value)
        self.default_value = self.min_value if default_value is None else self.PARAM_TYPE(default_value)
        self.value_prop_obj = None
    
    def get_vcolor_chname(self):
        return self.VCOLOR_CHANNEL_NAME_PREFIX + self.script_name

    def vcolor_to_param(self, vcolor):
        return vcolor

    def param_to_vcolor(self, iparam_value):
        return iparam_value

    def index(self):

        if self.INDEX < 0:
            raise ValueError()

        return self.INDEX
    
    def get_default_vcolor(self):
        return self.param_to_vcolor(self.default_value)

    def param_to_text(self, value):
        if self.DEFAULT_VALUE_TEXT is not None and (value == self.default_value):
            return self.DEFAULT_VALUE_TEXT

        return str(self.TEXT_TYPE(value)) + (self.TEXT_SUFFIX if self.TEXT_SUFFIX is not None else '')

    def param_to_color(self, value):
        return (1,1,1,1)


class StaticIParamInfo(IParamInfo):

    def __init__(self):
        default_value = self.DEFAULT_VALUE if hasattr(self, 'DEFAULT_VALUE') else None

        super().__init__(
            script_name=self.SCRIPT_NAME,
            label=self.LABEL,
            min_value=self.MIN_VALUE,
            max_value=self.MAX_VALUE,
            default_value=default_value
        )

    @classmethod
    def get_enabled_property(cls, context):
        return PropertyWrapper(get_scene_props(context), cls.ENABLED_PROP_ID)
    
    @classmethod
    def get_value_property(cls, context):
        return PropertyWrapper(get_scene_props(context), cls.VALUE_PROP_ID)
    

class GroupIParamInfoGeneric(StaticIParamInfo):

    TEXT_TYPE = int
    GROUP_COLORS = [
		(0.0,   0.0,    1.0),
        (1.0,   1.0,    0.0),
        (0.0,   1.0,    1.0),
        (0.0,   1.0,    0.0),
        (1.0,   0.25,   0.0),
        (1.0,   0.0,    0.25),
        (0.25,  0.0,    1.0),
        (0.0,   0.25,   1.0),
        (1.0,   0.0,    0.0),
        (0.5,   0.0,    0.5),
        (1.0,   0.0,    0.5),
        (1.0,   0.0,    1.0),
        (0.5,   1.0,    0.0),
    ]

    def param_to_color(self, value):
        return rgb_to_rgba(self.GROUP_COLORS[int(value) % len(self.GROUP_COLORS)])


class RotStepIParamInfo(StaticIParamInfo):

    TEXT_TYPE = int
    LABEL = 'Rotation Step'
    SCRIPT_NAME = 'rotation_step'

    USE_GLOBAL_VALUE = -1

    MIN_VALUE = USE_GLOBAL_VALUE
    MAX_VALUE = 180

    DEFAULT_VALUE_TEXT = 'G'
    TEXT_SUFFIX = 'd'
    VALUE_PROP_ID = 'island_rot_step'
    ENABLED_PROP_ID = 'island_rot_step_enable'


class NormalizeMultiplierIParamInfo(StaticIParamInfo):

    TEXT_TYPE = int
    LABEL = 'Scale Multiplier'
    SCRIPT_NAME = 'normalize_multiplier'

    MIN_VALUE = 10
    MAX_VALUE = 1000
    DEFAULT_VALUE = 100

    TEXT_SUFFIX = '%'
    VALUE_PROP_ID = 'island_normalize_multiplier'
    
    
class NumberedGroupIParamInfo(GroupIParamInfoGeneric):

    TEXT_TYPE = int
    LABEL = None
    SCRIPT_NAME = None

    MIN_VALUE = 0
    MAX_VALUE = 1000
    DEFAULT_VALUE = MIN_VALUE
    DEFAULT_VALUE_TEXT = 'N'

    VALUE_PROP_ID = 'group_num'


class AlignPriorityIParamInfo(GroupIParamInfoGeneric):

    TEXT_TYPE = int
    LABEL = 'Align Priority'
    SCRIPT_NAME = 'align_priority'

    MIN_VALUE = 0
    MAX_VALUE = 100
    DEFAULT_VALUE = MIN_VALUE
    
    VALUE_PROP_ID = 'align_priority'
    ENABLED_PROP_ID = 'align_priority_enable'



class SplitOffsetIParamInfo(StaticIParamInfo):

    TEXT_TYPE = int
    LABEL = 'Split Offset'

    MAX_VALUE = 10000
    MIN_VALUE = -MAX_VALUE
    DEFAULT_VALUE = MIN_VALUE


class SplitOffsetXIParamInfo(SplitOffsetIParamInfo):

    SCRIPT_NAME = 'split_offset_x'


class SplitOffsetYIParamInfo(SplitOffsetIParamInfo):

    SCRIPT_NAME = 'split_offset_y'


class IParamError(RuntimeError):

    def __init__(self, str):
        super().__init__(str)



class IParamSerializer:

    def __init__(self, iparam_info):

        self.iparam_info = iparam_info
        self.iparam_values = []
        self.flags = 0

        if get_prefs().allow_inconsistent_islands:
            self.flags |= UvpmIParamFlags.CONSISTENCY_CHECK_DISABLE

    def init_context(self, p_context):
        pass

    def serialize_iparam_info(self):
        output = encode_string(self.iparam_info.script_name)
        output += encode_string(self.iparam_info.label)
        output += struct.pack(self.iparam_info.PARAM_TYPE_MARK, self.iparam_info.PARAM_TYPE(self.iparam_info.min_value))
        output += struct.pack(self.iparam_info.PARAM_TYPE_MARK, self.iparam_info.PARAM_TYPE(self.iparam_info.max_value))
        output += struct.pack(self.iparam_info.PARAM_TYPE_MARK, self.iparam_info.PARAM_TYPE(self.iparam_info.default_value))
        output += struct.pack('i', int(self.iparam_info.INDEX))
        output += struct.pack('i', int(self.flags))

        return output
    
    def serialize_iparam(self, p_obj_idx, p_obj, face):
        self.iparam_values.append(self.get_iparam_value(p_obj_idx, p_obj, face))

    def get_faces_for_iparam_value(self, p_obj_idx, p_obj, face_indices, iparam_value):
        return [face_idx for face_idx in face_indices if self.get_iparam_value(p_obj_idx, p_obj, p_obj.mw.faces[face_idx]) == iparam_value]
        

class VColorIParamSerializer(IParamSerializer):

    def init_context(self, p_context):
        super().init_context(p_context)
        self.vcolor_layers = []

        for p_obj in p_context.p_objects:
            self.vcolor_layers.append(p_obj.get_or_create_vcolor_layer(self.iparam_info))
    
    def get_iparam_value(self, p_obj_idx, p_obj, face):
        return PackContext.load_iparam(self.iparam_info, self.vcolor_layers[p_obj_idx], face)

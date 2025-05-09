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


from .labels import Labels
from .app_iface import *

# TODO: rename this file to types.py


class OpFinishedException(Exception):
    pass

class OpAbortedException(Exception):
    pass


class EnumValue:

    @classmethod
    def to_blend_items(cls, enum_values):

        prefs = get_prefs()
        items = []

        for enum_val in enum_values:
            supported = (enum_val.req_feature == '') or getattr(prefs, 'FEATURE_' + enum_val.req_feature)

            items.append(enum_val.to_blend_item(supported))

        return items

    def __init__(self, code, name, desc='', req_feature=''):
        self.code = code
        self.name = name
        self.desc = desc
        self.req_feature = req_feature

    def to_blend_item(self, supported=True, name_mod=None):
        name = self.name

        if name_mod:
            name = name_mod(name)

        if supported:
            icon = 'NONE'
        else:
            name = name + ' ' + Labels.FEATURE_NOT_SUPPORTED_MSG
            icon = Labels.FEATURE_NOT_SUPPORTED_ICON

        return (self.code, name, self.desc, icon, int(self.code))

    def __str__(self):
        return str(self.code)

    def __eq__(self, other):
        return str(self) == str(other)


class EnumBase:

    @classmethod
    def to_blend_items(cls):
        return (item.to_blend_item() for item in cls.ITEMS)
    
    @classmethod
    def item_by_code(cls, code):
        return cls.ITEM_BY_CODE[code]


def enum_decorator(new_cls):
    item_by_code = {item.code: item for item in new_cls.ITEMS}
    cls = type(new_cls.__name__, (EnumBase,) + new_cls.__bases__, dict(new_cls.__dict__, ITEM_BY_CODE=item_by_code))
    return cls



class UvpmOpcode:
    REPORT_VERSION = 0
    EXECUTE_SCENARIO = 1


class UvpmMessageCode:
    PHASE = 0
    VERSION = 1
    BENCHMARK = 2
    ISLANDS = 3
    OUT_ISLANDS = 4
    LOG = 5

class UvpmOutIslandsSerializationFlags:
    CONTAINS_TRANSFORM = 1
    CONTAINS_IPARAMS = 2
    CONTAINS_FLAGS = 4
    CONTAINS_VERTICES = 8

class UvpmIslandFlags:
    OVERLAPS = 1
    OUTSIDE_TARGET_BOX = 2
    ALIGNED = 4
    SELECTED = 8

class UvpmFeatureCode:
    DEMO = 0
    ISLAND_ROTATION = 1
    OVERLAP_CHECK = 2
    PACKING_DEPTH = 3
    HEURISTIC_SEARCH = 4
    PACK_RATIO = 5
    PACK_TO_OTHERS = 6
    GROUPING = 7
    LOCK_OVERLAPPING = 8
    ADVANCED_HEURISTIC = 9
    SELF_INTERSECT_PROCESSING = 10
    VALIDATION = 11
    MULTI_DEVICE_PACK = 12
    TARGET_BOX = 13
    ISLAND_ROTATION_STEP = 14
    PACK_TO_TILES = 15

class UvpmLogType:
    STATUS = 0
    INFO = 1
    WARNING = 2
    ERROR = 3
    HINT = 4

class UvpmRetCode:
    ABORTED = -2
    NOT_SET = -1
    SUCCESS = 0
    FATAL_ERROR = 1
    NO_SPACE = 2
    CANCELLED = 3
    INVALID_ISLANDS = 4
    NO_SIUTABLE_DEVICE = 5
    NO_UVS = 6
    INVALID_INPUT = 7
    WARNING = 8

class UvpmPhaseCode:
    RUNNING = 0
    STOPPED = 1
    DONE = 2


class UvpmScaleMode:
    MAX_SCALE = EnumValue('0', 'Max Scale', Labels.SCALE_MODE_MAX_SCALE_DESC)
    FIXED_SCALE = EnumValue('1', 'Fixed Scale', Labels.SCALE_MODE_FIXED_SCALE_DESC)
    FIXED_SCALE_MAX_MARGIN = EnumValue('2', 'Fixed Scale (Max Margin)', Labels.SCALE_MODE_FIXED_SCALE_MAX_MARGIN_DESC)

    @classmethod
    def to_blend_items(cls):
        return (cls.MAX_SCALE.to_blend_item(), cls.FIXED_SCALE.to_blend_item(), cls.FIXED_SCALE_MAX_MARGIN.to_blend_item())

    @classmethod
    def fixed_scale_enabled(cls, mode):
        return (cls.FIXED_SCALE == mode) or (cls.FIXED_SCALE_MAX_MARGIN == mode)
    

class UvpmPackStrategy:
    AUTOMATIC = EnumValue('0', 'Automatic')
    SIDE_TO_SIDE_VERT = EnumValue('1', 'Side To Side (Vertical)')
    SIDE_TO_SIDE_HORI = EnumValue('2', 'Side To Side (Horizontal)')
    SQUARE = EnumValue('3', 'Square')

    @classmethod
    def to_blend_items(cls):
        return (cls.AUTOMATIC.to_blend_item(), cls.SIDE_TO_SIDE_VERT.to_blend_item(), cls.SIDE_TO_SIDE_HORI.to_blend_item(), cls.SQUARE.to_blend_item())


class UvpmBoxCorner:   
    BOTTOM_LEFT = EnumValue('0', '↙')
    BOTTOM_RIGHT = EnumValue('1', '↘')
    TOP_RIGHT = EnumValue('2', '↗')
    TOP_LEFT = EnumValue('3', '↖')

    @classmethod
    def to_blend_items(cls):
        return (cls.BOTTOM_LEFT.to_blend_item(), cls.BOTTOM_RIGHT.to_blend_item(), cls.TOP_RIGHT.to_blend_item(), cls.TOP_LEFT.to_blend_item())
    

class UvpmTileFillingMethod:
    SIMULTANEOUSLY = EnumValue('0', Labels.TILE_FILLING_METHOD_SIMULTANEOUSLY_NAME)
    ONE_BY_ONE = EnumValue('1', Labels.TILE_FILLING_METHOD_ONE_BY_ONE_NAME)

    @classmethod
    def to_blend_items(cls):
        return (cls.SIMULTANEOUSLY.to_blend_item(), cls.ONE_BY_ONE.to_blend_item())
    

class UvpmOverlapDetectionMode:
    DISABLED = EnumValue('0', 'Disabled', 'Not used')
    ANY_PART = EnumValue('1', 'Any Part', Labels.OVERLAP_DETECTION_MODE_ANY_PART_DESC)
    EXACT = EnumValue('2', 'Exact', Labels.OVERLAP_DETECTION_MODE_EXACT_DESC)

    @classmethod
    def to_blend_items(cls):
        return (cls.ANY_PART.to_blend_item(), cls.EXACT.to_blend_item())

class UvpmSimilarityMode:
    BORDER_SHAPE = EnumValue('0', Labels.SIMI_MODE_BORDER_SHAPE_NAME, Labels.SIMI_MODE_BORDER_SHAPE_DESC)
    VERTEX_POSITION = EnumValue('1', Labels.SIMI_MODE_VERTEX_POSITION_NAME, Labels.SIMI_MODE_VERTEX_POSITION_DESC)
    TOPOLOGY = EnumValue('2', Labels.SIMI_MODE_TOPOLOGY_NAME, Labels.SIMI_MODE_TOPOLOGY_DESC)

    @classmethod
    def to_blend_items(cls):
        return (cls.BORDER_SHAPE.to_blend_item(), cls.VERTEX_POSITION.to_blend_item(), cls.TOPOLOGY.to_blend_item())

    @classmethod
    def is_vertex_based(cls, mode):
        return (cls.VERTEX_POSITION == mode) or (cls.TOPOLOGY == mode)


class UvpmAxis:
    NONE = EnumValue(str(0), 'None', '')
    X = EnumValue(str(1 << 0), '+X', '')
    Y = EnumValue(str(1 << 1), '+Y', '')
    Z = EnumValue(str(1 << 2), '+Z', '')
    X_NEG = EnumValue(str(1 << 3), '-X', '')
    Y_NEG = EnumValue(str(1 << 4), '-Y', '')
    Z_NEG = EnumValue(str(1 << 5), '-Z', '')

    AXES_3D = [X, Y, Z, X_NEG, Y_NEG, Z_NEG]
    AXES_2D = [X, Y, X_NEG, Y_NEG]

    @classmethod
    def __axis_log2(cls, axis):
        return int(axis.code).bit_length() - 1

    @classmethod
    def is_positive(cls, axis):
        if axis == cls.NONE:
            return False

        return cls.__axis_log2(axis) <= cls.__axis_log2(cls.Z)
    
    @classmethod
    def to_blend_items(cls, include_none=False, only_2d=False, only_positive=False):
        axes = cls.AXES_2D if only_2d else cls.AXES_3D
        items = []

        name_mod = None
        if only_positive:
            name_mod = lambda name: name[1]

        if include_none:
            items.append(cls.NONE.to_blend_item())

        for a in axes:

            if only_positive:
                if not cls.is_positive(a):
                    continue

            item = a.to_blend_item(name_mod=name_mod)
            items.append(item)

        return items


class UvpmCoordSpace:
    LOCAL = EnumValue('0', 'Local', '')
    GLOBAL = EnumValue('1', 'Global', '')

    @classmethod
    def to_blend_items(cls):
        return (cls.LOCAL.to_blend_item(), cls.GLOBAL.to_blend_item())


class UvpmMapSerializationFlags:
    CONTAINS_FLAGS = 1
    CONTAINS_VERTS_3D = 2
    CONTAINS_VERTS_3D_GLOBAL = 4

class UvpmFaceInputFlags:
    SELECTED = 1
    UV_SET_IDX_OFFSET = (1 << 16)

class UvpmDeviceFlags:
    SUPPORTED = 1
    SUPPORTS_GROUPS_TOGETHER = 2

class UvpmIParamFlags:
    CONSISTENCY_CHECK_DISABLE = 1

class UvpmLogFlags:
    PARSE = 1

class UvpmIslandIntParams:
    MAX_COUNT = 16


class OperationStatus:
    ERROR = 0
    WARNING = 1
    CORRECT = 2


class RetCodeMetadata:

    def __init__(self, op_status):
        self.op_status = op_status


RETCODE_METADATA = {
    UvpmRetCode.NOT_SET : RetCodeMetadata(
        op_status=None
    ),
    UvpmRetCode.SUCCESS : RetCodeMetadata(
        op_status=OperationStatus.CORRECT
    ),
    UvpmRetCode.FATAL_ERROR : RetCodeMetadata(
        op_status=OperationStatus.ERROR
    ),
    UvpmRetCode.NO_SPACE : RetCodeMetadata(
        op_status=OperationStatus.WARNING
    ),
    UvpmRetCode.CANCELLED : RetCodeMetadata(
        op_status=OperationStatus.CORRECT
    ),
    UvpmRetCode.INVALID_ISLANDS : RetCodeMetadata(
        op_status=OperationStatus.ERROR
    ),
    UvpmRetCode.NO_SIUTABLE_DEVICE : RetCodeMetadata(
        op_status=OperationStatus.ERROR
    ),
    UvpmRetCode.NO_UVS : RetCodeMetadata(
        op_status=OperationStatus.WARNING
    ),
    UvpmRetCode.INVALID_INPUT : RetCodeMetadata(
        op_status=OperationStatus.ERROR
    ),
    UvpmRetCode.WARNING : RetCodeMetadata(
        op_status=OperationStatus.WARNING
    )
}


class UvpmPixelPerfectVertAlignMode:
    NONE = EnumValue('0', 'None', Labels.PIXEL_PERFECT_VERT_ALIGN_MODE_NONE_DESC)
    BOUNDING_BOX_CORNERS = EnumValue('1', 'Bounding Box Corners', Labels.PIXEL_PERFECT_VERT_ALIGN_MODE_BOUNDING_BOX_CORNERS_DESC)
    BOUNDING_BOX = EnumValue('2', 'Bounding Box', Labels.PIXEL_PERFECT_VERT_ALIGN_MODE_BOUNDING_BOX_DESC)
    BORDER_EDGES = EnumValue('3', 'Border Edges', Labels.PIXEL_PERFECT_VERT_ALIGN_MODE_BORDER_EDGES_DESC)
    ALL = EnumValue('4', 'All', Labels.PIXEL_PERFECT_VERT_ALIGN_MODE_ALL_DESC)

    @classmethod
    def to_blend_items(cls):
        return (cls.NONE.to_blend_item(),
                cls.BOUNDING_BOX_CORNERS.to_blend_item(),
                cls.BOUNDING_BOX.to_blend_item(),
                cls.BORDER_EDGES.to_blend_item(),
                cls.ALL.to_blend_item())
    

@enum_decorator
class PackOpType:

    PACK = EnumValue('0', 'Pack', Labels.PACK_OP_TYPE_PACK_DESC)
    PACK_TO_OTHERS = EnumValue('1', 'Pack To Others', Labels.PACK_OP_TYPE_PACK_TO_OTHERS_DESC)
    REPACK_WITH_OTHERS = EnumValue('2', 'Repack With Others', Labels.PACK_OP_TYPE_REPACK_WITH_OTHERS_DESC)

    ITEMS = (PACK, PACK_TO_OTHERS, REPACK_WITH_OTHERS)

    @classmethod
    def send_unselected_islands(cls, op_type):
        return (op_type == cls.PACK_TO_OTHERS.code) or (op_type == cls.REPACK_WITH_OTHERS.code)

    # @classmethod
    # def to_blend_items(cls):
    #     return (cls.PACK.to_blend_item(), cls.PACK_TO_OTHERS.to_blend_item(), cls.REPACK_WITH_OTHERS.to_blend_item())
    

class GroupingMethod:
    MATERIAL = EnumValue('0', 'Material', Labels.GROUP_METHOD_MATERIAL_DESC)
    # SIMILARITY = EnumValue('1', 'Similarity', Labels.GROUP_METHOD_SIMILARITY_DESC)
    MESH = EnumValue('2', 'Mesh Part', Labels.GROUP_METHOD_MESH_DESC)
    OBJECT = EnumValue('3', 'Object', Labels.GROUP_METHOD_OBJECT_DESC)
    MANUAL = EnumValue('4', 'Grouping Scheme (Manual)', Labels.GROUP_METHOD_MANUAL_DESC)
    TILE = EnumValue('5', 'Tile', Labels.GROUP_METHOD_TILE_DESC)

    @classmethod
    def to_blend_items(cls):
        return (cls.MATERIAL.to_blend_item(),
                # cls.SIMILARITY.to_blend_item(),
                cls.MESH.to_blend_item(),
                cls.OBJECT.to_blend_item(),
                cls.TILE.to_blend_item(),
                cls.MANUAL.to_blend_item())

    @classmethod
    def auto_grouping_enabled(cls, g_method):
        return g_method != cls.MANUAL.code


class TexelDensityGroupPolicy:
    INDEPENDENT = EnumValue(
        '0',
        Labels.TEXEL_DENSITY_GROUP_POLICY_INDEPENDENT_NAME,
        Labels.TEXEL_DENSITY_GROUP_POLICY_INDEPENDENT_DESC)

    UNIFORM = EnumValue(
        '1',
        Labels.TEXEL_DENSITY_GROUP_POLICY_UNIFORM_NAME,
        Labels.TEXEL_DENSITY_GROUP_POLICY_UNIFORM_DESC)

    CUSTOM = EnumValue(
        '2',
        Labels.TEXEL_DENSITY_GROUP_POLICY_CUSTOM_NAME,
        Labels.TEXEL_DENSITY_GROUP_POLICY_CUSTOM_DESC)

    AUTOMATIC = EnumValue(
        '3',
        Labels.TEXEL_DENSITY_GROUP_POLICY_AUTOMATIC_NAME,
        Labels.TEXEL_DENSITY_GROUP_POLICY_AUTOMATIC_DESC)

    @classmethod
    def to_blend_items(cls):
        return (cls.INDEPENDENT.to_blend_item(), cls.UNIFORM.to_blend_item(), cls.AUTOMATIC.to_blend_item(), cls.CUSTOM.to_blend_item())

    @classmethod
    def to_blend_items_auto(cls):
        return (cls.INDEPENDENT.to_blend_item(), cls.UNIFORM.to_blend_item())

class GroupLayoutMode:
    AUTOMATIC = EnumValue('0', 'Automatic', Labels.GROUP_LAYOUT_MODE_AUTOMATIC_DESC)
    MANUAL = EnumValue('1', 'Manual', Labels.GROUP_LAYOUT_MODE_MANUAL_DESC)
    AUTOMATIC_HORI = EnumValue('2', 'Automatic (Horizontal)', Labels.GROUP_LAYOUT_MODE_AUTOMATIC_HORI_DESC)
    AUTOMATIC_VERT = EnumValue('3', 'Automatic (Vertical)', Labels.GROUP_LAYOUT_MODE_AUTOMATIC_VERT_DESC)
    TILE_GRID = EnumValue('4', 'Tile Grid', Labels.GROUP_LAYOUT_MODE_TILE_GRID_DESC)

    @classmethod
    def to_blend_items(cls):
        return\
            (cls.AUTOMATIC.to_blend_item(),
             cls.AUTOMATIC_HORI.to_blend_item(),
             cls.AUTOMATIC_VERT.to_blend_item(),
             cls.TILE_GRID.to_blend_item(),
             cls.MANUAL.to_blend_item())

    @classmethod
    def to_blend_items_auto(cls):
        return tuple(mode.to_blend_item() for mode in cls.automatic_modes())

    @classmethod
    def automatic_modes(cls):
        return\
            (cls.AUTOMATIC,
             cls.AUTOMATIC_HORI,
             cls.AUTOMATIC_VERT,
             cls.TILE_GRID)

    @classmethod
    def is_automatic(cls, mode_code):
        return mode_code in (mode.code for mode in cls.automatic_modes())

    @classmethod
    def supports_tiles_in_row(cls, mode_code):
        return\
            mode_code == cls.AUTOMATIC.code

    @classmethod
    def supports_tile_count(cls, mode_code):
        return cls.is_automatic(mode_code) and (not cls.supports_tile_count_xy(mode_code))
    
    @classmethod
    def supports_tile_count_xy(cls, mode_code):
        return mode_code == cls.TILE_GRID.code


class RunScenario:
    _SCENARIOS = {}

    @classmethod
    def add_scenario(cls, scenario):
        cls._SCENARIOS[scenario['id']] = scenario

    @classmethod
    def get_scenario(cls, scenario_id, default=None):
        return cls._SCENARIOS.get(scenario_id, default)

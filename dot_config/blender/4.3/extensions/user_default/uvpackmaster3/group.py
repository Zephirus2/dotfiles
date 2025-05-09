from .box import UVPM3_Box, mark_boxes_dirty
from .utils import ShadowedCollectionProperty
from .island_params import GroupIParamInfoGeneric
from .labels import Labels
from .contansts import PropConstants
from .props import UVPM3_PackStrategyProps
from .contansts import *
from .pgroup import standalone_property_group
from .app_iface import *


def _update_group_info_name(self, context):
    if self.name.strip() == '':
        name = UVPM3_GroupInfo.get_default_group_name(self.num)
        self['name'] = name
    mark_boxes_dirty(self, context)


_OVERRIDE_PROPERTY_DEFAULT = False


def _def_prop_override(orig_prop_name):
    return BoolProperty(
        name='Override {}'.format(orig_prop_name),
        description=Labels.OVERRIDE_GLOBAL_OPTION_DESC,
        default=_OVERRIDE_PROPERTY_DEFAULT)


@standalone_property_group
class UVPM3_GroupOverrides:

    override_global_options : BoolProperty(
        name=Labels.OVERRIDE_GLOBAL_OPTIONS_NAME,
        description=Labels.OVERRIDE_GLOBAL_OPTIONS_DESC,
        default=_OVERRIDE_PROPERTY_DEFAULT)

    override_rotation_enable : _def_prop_override(Labels.ROTATION_ENABLE_NAME)
    rotation_enable : BoolProperty(
        name=Labels.ROTATION_ENABLE_NAME,
        description=Labels.ROTATION_ENABLE_DESC,
        default=PropConstants.ROTATION_ENABLE_DEFAULT)

    override_pre_rotation_disable : _def_prop_override(Labels.PRE_ROTATION_DISABLE_NAME)
    pre_rotation_disable : BoolProperty(
        name=Labels.PRE_ROTATION_DISABLE_NAME,
        description=Labels.PRE_ROTATION_DISABLE_DESC,
        default=PropConstants.PRE_ROTATION_DISABLE_DEFAULT)

    override_rotation_step : _def_prop_override(Labels.ROTATION_STEP_NAME)
    rotation_step : IntProperty(
        name=Labels.ROTATION_STEP_NAME,
        description=Labels.ROTATION_STEP_DESC,
        default=PropConstants.ROTATION_STEP_DEFAULT,
        min=PropConstants.ROTATION_STEP_MIN,
        max=PropConstants.ROTATION_STEP_MAX)
    
    override_scale_mode : _def_prop_override(Labels.SCALE_MODE_NAME)
    scale_mode : def_prop__scale_mode()

    override_pixel_margin : _def_prop_override(Labels.PIXEL_MARGIN_NAME)
    pixel_margin : def_prop__pixel_margin()

    override_pixel_border_margin : _def_prop_override(Labels.PIXEL_BORDER_MARGIN_NAME)
    pixel_border_margin : def_prop__pixel_border_margin()

    override_extra_pixel_margin_to_others : _def_prop_override(Labels.EXTRA_PIXEL_MARGIN_TO_OTHERS_NAME)
    extra_pixel_margin_to_others : def_prop__extra_pixel_margin_to_others()

    override_pixel_margin_tex_size : _def_prop_override(Labels.PIXEL_MARGIN_TEX_SIZE_NAME)
    pixel_margin_tex_size : def_prop__pixel_margin_tex_size()
    
    override_groups_together : _def_prop_override(Labels.GROUPS_TOGETHER_NAME)
    groups_together : def_prop__groups_together()
    
    override_group_compactness : _def_prop_override(Labels.GROUP_COMPACTNESS_NAME)
    group_compactness : def_prop__group_compactness()
    
    override_pack_to_single_box : _def_prop_override(Labels.PACK_TO_SINGLE_BOX_NAME)
    pack_to_single_box : BoolProperty(
        name=Labels.PACK_TO_SINGLE_BOX_NAME,
        description=Labels.PACK_TO_SINGLE_BOX_DESC,
        default=PropConstants.PACK_TO_SINGLE_BOX_DEFAULT)
    
    override_pack_strategy : _def_prop_override(Labels.PACK_STRATEGY_NAME)
    pack_strategy : PointerProperty(type=UVPM3_PackStrategyProps)


@standalone_property_group
class UVPM3_GroupInfo:

    MIN_GROUP_NUM = 0
    MAX_GROUP_NUM = 1000
    DEFAULT_GROUP_NUM = MIN_GROUP_NUM
    DEFAULT_GROUP_NAME = 'G'
    TDENSITY_CLUSTER_DEFAULT = 0
    TILE_COUNT_DEFAULT = 1

    name : StringProperty(name="Name", default="", update=_update_group_info_name)
    num : IntProperty(name="Group Number", default=0)
    color : FloatVectorProperty(name="", default=(1.0, 1.0, 0.0), min=0.0, max=1.0, subtype="COLOR", update=mark_boxes_dirty)
    target_boxes : CollectionProperty(type=UVPM3_Box)
    active_target_box_idx : IntProperty(name="", default=0, update=mark_boxes_dirty)

    
    tdensity_cluster : IntProperty(
        name=Labels.TEXEL_DENSITY_CLUSTER_NAME,
        description=Labels.TEXEL_DENSITY_CLUSTER_DESC ,
        default=TDENSITY_CLUSTER_DEFAULT,
        min=0,
        max=100 * 1000)

    tile_count : IntProperty(
        name=Labels.TILE_COUNT_NAME,
        description=Labels.TILE_COUNT_DESC,
        default=TILE_COUNT_DEFAULT,
        min=1,
        max=100)

    overrides : PointerProperty(type=UVPM3_GroupOverrides)

    def __init__(self, name=None, num=None):

        self.name = name
        self.num = num
        self.color = GroupIParamInfoGeneric.GROUP_COLORS[self.num % len(GroupIParamInfoGeneric.GROUP_COLORS)] if self.num is not None else None
        self.active_target_box_idx = 0

        self.tdensity_cluster = self.TDENSITY_CLUSTER_DEFAULT
        self.tile_count = self.TILE_COUNT_DEFAULT

        self.target_boxes = ShadowedCollectionProperty(elem_type=UVPM3_Box.SA)
        self.overrides = UVPM3_GroupOverrides.SA()

    def copy_from(self, other):

        self.name = str(other.name)
        self.num = int(other.num)
        self.color = other.color[:]

        self.active_target_box_idx = int(other.active_target_box_idx)
        self.tdensity_cluster = int(other.tdensity_cluster)
        self.tile_count = int(other.tile_count)

        self.target_boxes.clear()
        for other_box in other.target_boxes:
            new_box = self.target_boxes.add()
            new_box.copy_from(other_box)

        self.overrides.copy_from(other.overrides)

    @classmethod
    def get_default_group_name(cls, g_num):
        return "{}{}".format(cls.DEFAULT_GROUP_NAME, g_num)

    def is_default(self):
        return self.num == self.DEFAULT_GROUP_NUM

    def add_target_box(self, new_box):

        added_box = self.target_boxes.add()
        added_box.copy_from(new_box)
        self.active_target_box_idx = len(self.target_boxes)-1

    def remove_target_box(self, box_idx):

        if len(self.target_boxes) <= 1:
            raise RuntimeError('Group has to have at least one target box')

        self.target_boxes.remove(box_idx)
        self.active_target_box_idx = min(self.active_target_box_idx, len(self.target_boxes)-1)

    def get_active_target_box(self):

        try:
            return self.target_boxes[self.active_target_box_idx]

        except IndexError:
            return None
        
    def to_script_param(self, group_sparam_handler=None):

        out_target_boxes = []
        for box in self.target_boxes:
            out_target_boxes.append(box.to_script_param())

        out_group =\
            {
                'name': self.name,
                'num': self.num,
            }

        out_group['target_boxes'] = out_target_boxes

        if group_sparam_handler is not None:
            group_sparam_handler(self, out_group)

        return out_group

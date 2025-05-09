
from .enums import GroupLayoutMode, TexelDensityGroupPolicy, GroupingMethod
from .labels import Labels
from .contansts import PropConstants
from .box import mark_boxes_dirty
from .box_utils import disable_box_rendering
from .grouping_scheme_access import GroupingSchemeAccess
from .contansts import def_prop__group_compactness, def_prop__groups_together
from .pgroup import standalone_property_group
from .utils import PropertyWrapper
from .app_iface import *


@standalone_property_group
class UVPM3_GroupingOptionsBase:

    tiles_in_row : IntProperty(
        name=Labels.TILES_IN_ROW_NAME,
        description=Labels.TILES_IN_ROW_DESC,
        default=PropConstants.TILES_IN_ROW_DEFAULT,
        min=PropConstants.TILE_COUNT_XY_MIN,
        max=PropConstants.TILE_COUNT_XY_MAX)

    tile_count_per_group : IntProperty(
        name=Labels.TILE_COUNT_PER_GROUP_NAME,
        description=Labels.TILE_COUNT_PER_GROUP_DESC,
        default=PropConstants.TILE_COUNT_PER_GROUP_DEFAULT,
        min=PropConstants.TILE_COUNT_XY_MIN,
        max=PropConstants.TILE_COUNT_XY_MAX)
    
    tile_count_x : IntProperty(
        name=Labels.TILE_COUNT_X_NAME,
        description=Labels.TILE_COUNT_X_DESC,
        default=PropConstants.TILE_COUNT_XY_DEFAULT,
        min=PropConstants.TILE_COUNT_XY_MIN,
        max=PropConstants.TILE_COUNT_XY_MAX)

    tile_count_y : IntProperty(
        name=Labels.TILE_COUNT_Y_NAME,
        description=Labels.TILE_COUNT_Y_DESC,
        default=PropConstants.TILE_COUNT_XY_DEFAULT,
        min=PropConstants.TILE_COUNT_XY_MIN,
        max=PropConstants.TILE_COUNT_XY_MAX)

    last_group_complementary : BoolProperty(
        name=Labels.LAST_GROUP_COMPLEMENTARY_NAME,
        description=Labels.LAST_GROUP_COMPLEMENTARY_DESC,
        default=PropConstants.LAST_GROUP_COMPLEMENTARY_DEFAULT,
        update=mark_boxes_dirty)

    groups_together : def_prop__groups_together()
    group_compactness : def_prop__group_compactness()
    
    pack_to_single_box : BoolProperty(
        name=Labels.PACK_TO_SINGLE_BOX_NAME,
        description=Labels.PACK_TO_SINGLE_BOX_DESC,
        default=PropConstants.PACK_TO_SINGLE_BOX_DEFAULT)


    def __init__(self):

        self.tiles_in_row = PropConstants.TILES_IN_ROW_DEFAULT
        self.tile_count_per_group = PropConstants.TILE_COUNT_PER_GROUP_DEFAULT
        self.tile_count_x = PropConstants.TILE_COUNT_XY_DEFAULT
        self.tile_count_y = PropConstants.TILE_COUNT_XY_DEFAULT
        self.last_group_complementary = PropConstants.LAST_GROUP_COMPLEMENTARY_DEFAULT
        self.groups_together = PropConstants.GROUPS_TOGETHER_DEFAULT
        self.group_compactness = PropConstants.GROUP_COMPACTNESS_DEFAULT
        self.pack_to_single_box = PropConstants.PACK_TO_SINGLE_BOX_DEFAULT

    def copy_from(self, other):

        self.tiles_in_row = int(other.tiles_in_row)
        self.tile_count_per_group = int(other.tile_count_per_group)
        self.tile_count_x = int(other.tile_count_x)
        self.tile_count_y = int(other.tile_count_y)
        self.last_group_complementary = bool(other.last_group_complementary)
        self.groups_together = bool(other.groups_together)
        self.group_compactness = float(other.group_compactness)
        self.pack_to_single_box = bool(other.pack_to_single_box)


@standalone_property_group
class UVPM3_GroupingOptions:

    automatic : BoolProperty(name='', default=False)
    base : PointerProperty(type=UVPM3_GroupingOptionsBase)

    tdensity_policy : EnumProperty(
        items=TexelDensityGroupPolicy.to_blend_items(),
        name=Labels.TEXEL_DENSITY_GROUP_POLICY_NAME,
        description=Labels.TEXEL_DENSITY_GROUP_POLICY_DESC,
        update=mark_boxes_dirty)

    group_layout_mode : EnumProperty(
        items=GroupLayoutMode.to_blend_items(),
        name=Labels.GROUP_LAYOUT_MODE_NAME,
        description=Labels.GROUP_LAYOUT_MODE_DESC,
        update=disable_box_rendering)
    

    def __init__(self):

        self.base = UVPM3_GroupingOptionsBase.SA()
        self.tdensity_policy = TexelDensityGroupPolicy.INDEPENDENT.code
        self.group_layout_mode = GroupLayoutMode.AUTOMATIC.code

    def copy_from(self, other):

        self.base.copy_from(other.base)
        self.tdensity_policy = str(other.tdensity_policy)
        self.group_layout_mode = str(other.group_layout_mode)

        self.group_initializer = other.group_initializer

    def group_initializer(self, group):
        pass


class UVPM3_AutoGroupingOptions(PropertyGroup):

    automatic : BoolProperty(name='', default=True)
    base : PointerProperty(type=UVPM3_GroupingOptionsBase)

    tdensity_policy : EnumProperty(
        items=TexelDensityGroupPolicy.to_blend_items_auto(),
        name=Labels.TEXEL_DENSITY_GROUP_POLICY_NAME,
        description=Labels.TEXEL_DENSITY_GROUP_POLICY_DESC)

    group_layout_mode : EnumProperty(
        items=GroupLayoutMode.to_blend_items_auto(),
        name=Labels.GROUP_LAYOUT_MODE_NAME,
        description=Labels.GROUP_LAYOUT_MODE_DESC)

    def group_initializer(self, group):
        group.tile_count = self.base.tile_count_per_group


class GroupingConfig:

    def __init__(self, context):
        self.context = context
        self.grouping_enabled = False
        self.g_scheme_access_desc_id = 'default'
        self.target_box_editing = False
        self.group_method_prop = PropertyWrapper(get_scene_props(context), 'group_method')

        from .presets_grouping_scheme import UVPM3_PT_PresetsGroupingSchemeDefault
        self.g_scheme_preset_panel_t = UVPM3_PT_PresetsGroupingSchemeDefault

    def auto_grouping_enabled(self):
        return GroupingMethod.auto_grouping_enabled(self.group_method_prop.get())
    
    def draw_group_method(self, layout):
        from .utils import PropertyWrapper
        layout.label(text=self.group_method_prop.get_name() + ':')
        row = layout.row(align=True)
        self.group_method_prop.draw(row, text='')

    def get_scheme_access(self, ui_drawing=False):
        g_scheme_access = GroupingSchemeAccess()
        g_scheme_access.init_access(self.context, desc_id=self.g_scheme_access_desc_id, ui_drawing=ui_drawing)
        return g_scheme_access

    def get_active_g_scheme(self, auto_grouping_check=True, ui_drawing=False):
        if auto_grouping_check and self.auto_grouping_enabled():
            return None

        return self.get_scheme_access(ui_drawing=ui_drawing).active_g_scheme
    
    def active_g_scheme_target_box_editing(self):
        active_g_scheme = self.get_active_g_scheme(auto_grouping_check=True, ui_drawing=True)

        if not active_g_scheme:
            return False
        
        return active_g_scheme.target_box_editing()
    
import uuid

from .box import DEFAULT_TARGET_BOX, UVPM3_Box, mark_boxes_dirty
from .box_utils import disable_box_rendering
from .utils import ShadowedCollectionProperty, unique_name
from .enums import GroupLayoutMode, TexelDensityGroupPolicy, GroupingMethod
from .group_map import *
from .island_params import IParamSerializer, VColorIParamSerializer, IParamInfo
from .grouping import UVPM3_GroupingOptions
from .group import UVPM3_GroupInfo
from .grouping_scheme_access import GroupingSchemeAccess, AccessDescIdAttrMixin
from .labels import Labels
from .pgroup import standalone_property_group
from .app_iface import *


class GroupMapSerializer(IParamSerializer):
    def __init__(self, g_scheme):
        super().__init__(g_scheme.get_iparam_info())
        assert (g_scheme.group_map is not None)
        self.group_map = g_scheme.group_map

    def get_iparam_value(self, p_obj_idx, p_obj, face):
        return self.group_map.get_map(p_obj, face.index)


class GroupingSchemeSerializer(VColorIParamSerializer):

    def __init__(self, g_scheme):
        super().__init__(g_scheme.get_iparam_info())
        assert (g_scheme.group_map is None)
        self.g_scheme = g_scheme
    
    def get_iparam_value(self, p_obj_idx, p_obj, face):
        return self.g_scheme.get_iparam_value(self.vcolor_layers[p_obj_idx], face)
    

def _update_g_scheme_name(self, context):
    g_scheme_access = GroupingSchemeAccess()
    g_scheme_access.init_access(context, desc_id='default')
    g_schemes = g_scheme_access.get_g_schemes()

    if self.name.strip() == '':
        name = UVPM3_GroupingScheme.DEFAULT_GROUPING_SCHEME_NAME
    else:
        name = self.name
    self['name'] = unique_name(name, g_schemes, self)


class UVPM3_GroupingSchemeAccessDescriptor(PropertyGroup):

    active_g_scheme_uuid : StringProperty(default='', update=disable_box_rendering)


class UVPM3_GroupingSchemeAccessDescriptorContainer(PropertyGroup):

    default : PointerProperty(type=UVPM3_GroupingSchemeAccessDescriptor)
    editor : PointerProperty(type=UVPM3_GroupingSchemeAccessDescriptor)
    lock_group : PointerProperty(type=UVPM3_GroupingSchemeAccessDescriptor)
    stack_group : PointerProperty(type=UVPM3_GroupingSchemeAccessDescriptor)
    track_group : PointerProperty(type=UVPM3_GroupingSchemeAccessDescriptor)


@standalone_property_group
class UVPM3_GroupingScheme:

    DEFAULT_GROUPING_SCHEME_NAME = 'Scheme'

    name : StringProperty(name="name", default="", update=_update_g_scheme_name)
    uuid : StringProperty(name="uuid", default="")
    groups : CollectionProperty(type=UVPM3_GroupInfo)
    active_group_idx : IntProperty(name="", default=0, update=mark_boxes_dirty)
    options : PointerProperty(type=UVPM3_GroupingOptions)
        
    def __init__(self, _name='', _uuid=''):

        self.name = _name
        self.uuid = _uuid
        self.groups = ShadowedCollectionProperty(elem_type=UVPM3_GroupInfo.SA)
        self.active_group_idx = 0
        self.options = UVPM3_GroupingOptions.SA()

        self.init_defaults()

    def copy_from(self, other):

        self.name = str(other.name)
        self.uuid = str(other.uuid)

        self.clear_groups()
        for other_group in other.groups:
            self.add_group_internal(other_group)

        self.active_group_idx = int(other.active_group_idx)
        self.options.copy_from(other.options)
        self.init_defaults()

    @staticmethod
    def uuid_is_valid(uuid_to_test):
        try:
            uuid_obj = uuid.UUID(uuid_to_test, version=4)
        except ValueError:
            return False
        return uuid_obj.hex == uuid_to_test

    @staticmethod
    def uuid_generate():
        return uuid.uuid4().hex

    def init_defaults(self):

        if self.name == '':
            self.name = self.DEFAULT_GROUPING_SCHEME_NAME

        if self.uuid == '':
            self.uuid = self.uuid_generate()

        self.group_by_num = dict()
        self.group_map = None
        self.iparam_info = None
        self.next_group_num = UVPM3_GroupInfo.DEFAULT_GROUP_NUM

        for group in self.groups:
            self.__add_group_to_dictionaries(group)

    def regenerate_uuid(self):
        self.uuid = self.uuid_generate()

    def copy(self):

        out = UVPM3_GroupingScheme.SA()
        out.copy_from(self)
        return out

    def clear_groups(self):

        self.groups.clear()
        self.group_by_num = dict()
        self.group_map = None
        self.next_group_num = UVPM3_GroupInfo.DEFAULT_GROUP_NUM

    def group_count(self):

        return len(self.groups)

    def complementary_group_supported(self):

        return (self.options.tdensity_policy in (TexelDensityGroupPolicy.UNIFORM.code, TexelDensityGroupPolicy.AUTOMATIC.code)) and len(self.groups) > 1
    
    def complementary_group_not_supported_msg(self):

        return None if self.complementary_group_supported() else Labels.LAST_GROUP_COMPLEMENTARY_SUPPORTED_MSG

    def complementary_group_enabled(self):

        return self.complementary_group_supported() and self.options.base.last_group_complementary

    def complementary_group(self):

        assert(self.complementary_group_enabled())
        assert(len(self.groups) > 0)
        return self.groups[len(self.groups)-1]

    def is_complementary_group(self, group):

        return self.complementary_group_enabled() and group.num == self.complementary_group().num

    def complementary_group_is_active(self):

        active_group = self.get_active_group()
        if active_group is None:
            return False
        return self.is_complementary_group(active_group)

    def apply_tdensity_policy(self):

        if self.options.tdensity_policy == TexelDensityGroupPolicy.CUSTOM.code:
            return

        def _group_and_intersect_groups(lookup_group, lookup_groups_to_process):
            if lookup_group in lookup_groups_to_process:
                yield lookup_group
                lookup_groups_to_process.remove(lookup_group)
                intersect_groups = []
                for group_to_process in lookup_groups_to_process:
                    if any(b.intersects(p_b) for b in group_to_process.target_boxes for p_b in lookup_group.target_boxes):
                        intersect_groups.extend(_group_and_intersect_groups(group_to_process, lookup_groups_to_process[:]))
                for intersect_group in intersect_groups:
                    yield intersect_group
                    if intersect_group in lookup_groups_to_process:
                        lookup_groups_to_process.remove(intersect_group)

        groups_to_process = self.groups[:]
        for g_num, group in self.group_by_num.items():
            if self.options.tdensity_policy == TexelDensityGroupPolicy.INDEPENDENT.code:
                group.tdensity_cluster = g_num

            elif self.options.tdensity_policy == TexelDensityGroupPolicy.UNIFORM.code:
                group.tdensity_cluster = 0

            elif self.options.tdensity_policy == TexelDensityGroupPolicy.AUTOMATIC.code:
                for g in _group_and_intersect_groups(group, groups_to_process):
                    g.tdensity_cluster = g_num
            else:
                assert(False)

    def target_box_editing(self):
        return self.options.group_layout_mode == GroupLayoutMode.MANUAL.code
    
    def apply_group_layout_tile_grid(self):
        tile_grid_boxes = UVPM3_Box.tile_grid_boxes(DEFAULT_TARGET_BOX, self.options.base.tile_count_x, self.options.base.tile_count_y)

        for group_idx, group in enumerate(self.groups):
            group.target_boxes.clear()

            for box in tile_grid_boxes:
                new_box = group.target_boxes.add()
                new_box.copy_from(box)

    def apply_group_layout_tile_count(self):
        if self.options.group_layout_mode == GroupLayoutMode.AUTOMATIC.code:
            def box_func(group_idx, tile_idx, global_tile_idx):
                return DEFAULT_TARGET_BOX.tile_from_num(global_tile_idx, self.options.base.tiles_in_row)
        elif self.options.group_layout_mode == GroupLayoutMode.AUTOMATIC_HORI.code:
            def box_func(group_idx, tile_idx, global_tile_idx):
                return DEFAULT_TARGET_BOX.tile(tile_idx, group_idx)
        elif self.options.group_layout_mode == GroupLayoutMode.AUTOMATIC_VERT.code:
            def box_func(group_idx, tile_idx, global_tile_idx):
                return DEFAULT_TARGET_BOX.tile(group_idx, tile_idx)
        else:
            assert False           

        global_tile_idx = 0
        for group_idx, group in enumerate(self.groups):
            group.target_boxes.clear()

            for tile_idx in range(group.tile_count):
                new_box = group.target_boxes.add()
                new_box.copy_from(box_func(group_idx, tile_idx, global_tile_idx))
                global_tile_idx += 1

    def apply_group_layout(self):

        if self.target_box_editing():
            pass
        
        else:           
            if self.options.group_layout_mode == GroupLayoutMode.TILE_GRID.code:
                self.apply_group_layout_tile_grid()
            elif GroupLayoutMode.supports_tile_count(self.options.group_layout_mode):
                self.apply_group_layout_tile_count()
            else:
                assert False

        if self.complementary_group_enabled():
            last_group = self.groups[-1]
            last_group.target_boxes.clear()

            for i in range(len(self.groups) - 1):
                group = self.groups[i]

                for box in group.target_boxes:
                    new_box = last_group.target_boxes.add()
                    new_box.copy_from(box)

    def get_group_by_num(self, g_num):

        group = self.group_by_num.get(g_num)
        return group
    
    def get_iparam_value(self, vcolor_layer, face):

        group_num = PackContext.load_iparam(self.get_iparam_info(), vcolor_layer, face)
        group = self.get_group_by_num(group_num)
        if group is None:
            group_num = UVPM3_GroupInfo.DEFAULT_GROUP_NUM

        return group_num

    def get_default_group(self):

        default_group = self.get_group_by_num(UVPM3_GroupInfo.DEFAULT_GROUP_NUM)

        if default_group is None:
            default_group = self.add_group_with_target_box(g_num=UVPM3_GroupInfo.DEFAULT_GROUP_NUM)

        return default_group

    def __add_group_to_dictionaries(self, group):

        if self.next_group_num <= group.num:
            self.next_group_num = group.num + 1

        self.group_by_num[group.num] = group

    def add_group(self, g_name=UVPM3_GroupInfo.DEFAULT_GROUP_NAME, g_num=None):

        if g_num is None:
            g_num = self.next_group_num

        if g_name == UVPM3_GroupInfo.DEFAULT_GROUP_NAME:
            g_name = UVPM3_GroupInfo.get_default_group_name(g_num)

        new_group = UVPM3_GroupInfo.SA(g_name, g_num)
        return self.add_group_internal(new_group)

    def add_group_with_target_box(self, g_name=UVPM3_GroupInfo.DEFAULT_GROUP_NAME, g_num=None):

        new_group = self.add_group(g_name, g_num)
        self.add_target_box(new_group)

        return new_group

    def add_group_internal(self, new_group):

        assert new_group.num >= UVPM3_GroupInfo.MIN_GROUP_NUM
        if new_group.num > UVPM3_GroupInfo.MAX_GROUP_NUM:
            raise RuntimeError('Max group limit reached')

        added_group = self.groups.add()
        added_group.copy_from(new_group)
        self.options.group_initializer(added_group)
        
        self.__add_group_to_dictionaries(added_group)
        self.active_group_idx = len(self.groups)-1
        return added_group

    def group_to_text(self, g_num):

        group = self.get_group_by_num(g_num)

        if group is None:
            raise RuntimeError('Group not found')

        return group.name

    def group_to_color(self, g_num):

        group = self.get_group_by_num(g_num)

        if group is None:
            raise RuntimeError('Group not found')

        return group.color

    def remove_group(self, group_idx):

        group_to_remove = self.groups[group_idx]

        if group_to_remove.is_default():
            raise RuntimeError("Cannot remove the default group")

        del self.group_by_num[group_to_remove.num]

        self.groups.remove(group_idx)
        self.active_group_idx = min(self.active_group_idx, len(self.groups)-1)

    def box_intersects_group_boxes(self, box_to_check):

        for group in self.groups:
            if self.is_complementary_group(group):
                continue
            
            for box in group.target_boxes:
                if box.intersects(box_to_check):
                    return True

        return False

    def add_target_box(self, target_group):

        tile_num_x = 0
        tile_num_y = 0

        if len(target_group.target_boxes) > 0:
            min_corner = target_group.target_boxes[-1].min_corner
            tile_num_x = int(min_corner[0]) + 1
            tile_num_y = int(min_corner[1])

        while True:
            intersects = False
            new_box = DEFAULT_TARGET_BOX.tile(tile_num_x, tile_num_y)

            if not self.box_intersects_group_boxes(new_box):
                target_group.add_target_box(new_box)
                break

            tile_num_x += 1


    def init_group_map(self, p_context, g_method, skip_default_group=False):

        g_method_to_map_type = {
            GroupingMethod.MATERIAL.code : GroupMapMaterial,
            GroupingMethod.MESH.code : GroupMapMeshPart,
            GroupingMethod.OBJECT.code : GroupMapObject,
            GroupingMethod.TILE.code : GroupMapTile
        }

        map_type = g_method_to_map_type.get(g_method)
        if map_type is None:
            raise RuntimeError('Unexpected grouping method encountered')
        
        if skip_default_group:
            def_group = self.add_group_with_target_box()
            assert def_group.num == UVPM3_GroupInfo.DEFAULT_GROUP_NUM

        self.group_map = map_type(self, p_context)
        return self.group_map

    def get_iparam_info(self):

        if self.iparam_info is not None:
            return self.iparam_info
        
        self.iparam_info = IParamInfo(
            script_name='g_scheme_{}'.format(self.uuid),
            label=self.group_map.iparam_label() if self.group_map is not None else self.name,
            min_value=UVPM3_GroupInfo.MIN_GROUP_NUM,
            max_value=UVPM3_GroupInfo.MAX_GROUP_NUM
        )

        return self.iparam_info
    
    def get_iparam_serializer(self):
        if self.group_map is not None:
            return GroupMapSerializer(self)
        
        return GroupingSchemeSerializer(self)

    def get_active_group(self):

        try:
            return self.groups[self.active_group_idx]
        except IndexError:
            return None
        
    def to_script_param(self, group_sparam_handler=None):
        out_groups = []
        for group in self.groups:
            out_groups.append(group.to_script_param(group_sparam_handler))

        out_g_scheme =\
        {
            'iparam_name': self.get_iparam_info().script_name,
            'groups': out_groups,
            'options': {
                'groups_together': self.options.base.groups_together,
                'group_compactness': self.options.base.group_compactness,
                'pack_to_single_box': self.options.base.pack_to_single_box,
            }
        }

        return out_g_scheme

    def is_valid(self):
        
        if self.name.strip() == '':
            return False

        if not self.uuid_is_valid(self.uuid):
            return False

        if len(self.groups) == 0:
            return False

        if self.active_group_idx not in range(len(self.groups)):
            return False

        def_group_found = False
        g_number_set = set()

        for group in self.groups:
            if group.name.strip() == '':
                return False

            if group.is_default():
                if def_group_found:
                    return False
                def_group_found = True

            if len(group.target_boxes) == 0:
                return False

            if group.active_target_box_idx not in range(len(group.target_boxes)):
                return False

            g_number_set.add(group.num)

        if not def_group_found:
            return False

        if len(g_number_set) != len(self.groups):
            return False

        return True


class TargetGroupingSchemeMixin(GroupingSchemeAccess):

    target_scheme_action : EnumProperty(name="Action", items=[("NEW", "Create A New Scheme", "Create A New Scheme", 0),
                                                      ("EXTEND", "Apply To An Existing Scheme", "Apply To An Existing Scheme", 1)])
    target_scheme_name : StringProperty(name="Name", default=UVPM3_GroupingScheme.DEFAULT_GROUPING_SCHEME_NAME)
    target_scheme_uuid : EnumProperty(name="Grouping Schemes", items=GroupingSchemeAccess.get_g_schemes_enum_items_callback)

    def create_new_g_scheme(self):
        return self.target_scheme_action == "NEW"

    def get_target_g_scheme(self):
        create_new_g_scheme = self.create_new_g_scheme()

        if not create_new_g_scheme and len(self.get_g_schemes()) == 0:
            raise RuntimeError('No grouping scheme in the blend file found')

        if create_new_g_scheme:
            self.create_g_scheme()
            self.active_g_scheme.name = self.target_scheme_name
        else:
            self.set_active_g_scheme_uuid(self.target_scheme_uuid)

        return self.active_g_scheme
    
    def invoke(self, context, event):
        self.target_scheme_name = self.target_scheme_name_impl(context)
        return super().invoke(context, event)
    
    def props_dialog_width(self):
        return 400

    def draw(self, context):
        self.init_access(context, ui_drawing=True, desc_id=self.get_desc_id_from_obj(self))
        create_new_g_scheme = self.create_new_g_scheme()

        layout = self.layout
        col = layout.column(align=True)
        col.prop(self, "target_scheme_action", text="")

        box = col.box()
        row = box.row(align=True)

        if create_new_g_scheme:
            split = row.split(factor=0.4, align=True)
            split.label(text="New Scheme Name:")
            row = split.row(align=True)
            row.prop(self, "target_scheme_name", text="")
        else:
            if len(self.get_g_schemes()) == 0:
                row.label(text='WARNING: no grouping scheme in the blend file found.')
            else:
                split = row.split(factor=0.4, align=True)
                split.label(text="Apply To Scheme:")
                row = split.row(align=True)
                row.prop(self, "target_scheme_uuid", text="")

        self.draw_impl(context, col)

    def draw_impl(self, context):
        pass


class UVPM3_OT_GroupingSchemeOperatorGeneric(Operator, GroupingSchemeAccess):

    bl_options = {'INTERNAL', 'UNDO'}

    def execute(self, context):

        try:
            # access_desc_id = None

            # if hasattr(self, 'access_desc_id'):
            #     access_desc_id = str(getattr(self, 'access_desc_id'))

            self.init_access(context, **self.get_access_desc_kwargs(context))
            return self.execute_impl(context)

        except Exception as ex:
            self.report({'ERROR'}, str(ex))

        return {'CANCELLED'}


class UVPM3_OT_NewGroupingScheme(UVPM3_OT_GroupingSchemeOperatorGeneric, AccessDescIdAttrMixin):

    bl_idname = "uvpackmaster3.new_grouping_scheme"
    bl_label = "New Grouping Scheme"
    bl_description = "Add a new grouping scheme"

    def execute_impl(self, context):
        self.create_g_scheme()
        return {'FINISHED'}


class UVPM3_OT_RemoveGroupingScheme(UVPM3_OT_GroupingSchemeOperatorGeneric, AccessDescIdAttrMixin):

    bl_idname = "uvpackmaster3.remove_grouping_scheme"
    bl_label = "Remove"
    bl_description = "Remove the active grouping scheme"

    def execute_impl(self, context):
        g_schemes = self.get_g_schemes()
        active_idx = self.get_active_g_scheme_idx()

        if active_idx < 0:
            return {'CANCELLED'}

        g_schemes.remove(active_idx)
        new_idx = min(active_idx, len(g_schemes)-1)
        self.set_active_g_scheme_uuid(g_schemes[new_idx].uuid if new_idx >=0 else '')

        return {'FINISHED'}


class UVPM3_OT_NewGroupInfo(UVPM3_OT_GroupingSchemeOperatorGeneric, AccessDescIdAttrMixin):

    bl_idname = "uvpackmaster3.new_group_info"
    bl_label = "New Item"
    bl_description = 'Add a group to the active grouping scheme'

    def execute_impl(self, context):
        
        if self.active_g_scheme is None:
            return {'CANCELLED'}

        new_group = self.active_g_scheme.add_group_with_target_box()
        mark_boxes_dirty(self, context)
        return {'FINISHED'}


class UVPM3_OT_RemoveGroupInfo(UVPM3_OT_GroupingSchemeOperatorGeneric, AccessDescIdAttrMixin):

    bl_idname = "uvpackmaster3.remove_group_info"
    bl_label = "Remove"
    bl_description = 'Remove the active group from the scheme'

    def execute_impl(self, context):

        if self.active_g_scheme is None:
            return {'CANCELLED'}

        self.active_g_scheme.remove_group(self.active_g_scheme.active_group_idx)
        mark_boxes_dirty(self, context)
        return {'FINISHED'}


class UVPM3_OT_MoveGroupInfo(UVPM3_OT_GroupingSchemeOperatorGeneric, AccessDescIdAttrMixin):
    bl_idname = "uvpackmaster3.move_group_info"
    bl_label = "Move"
    bl_description = "Move the active group up/down in the list"

    direction : EnumProperty(items=[("UP", "Up", "", 0), ("DOWN", "Down", "", 1)])

    def execute_impl(self, context):
        if self.active_g_scheme is None:
            return {'CANCELLED'}

        old_idx = self.active_g_scheme.active_group_idx
        new_idx = old_idx
        if self.direction == "UP":
            if old_idx > 0:
                new_idx = old_idx - 1
        else:
            if old_idx < len(self.active_g_scheme.groups) - 1:
                new_idx = old_idx + 1
        self.active_g_scheme.groups.move(old_idx, new_idx)
        self.active_g_scheme.active_group_idx = new_idx
        return {'FINISHED'}

class UVPM3_OT_NewTargetBox(UVPM3_OT_GroupingSchemeOperatorGeneric, AccessDescIdAttrMixin):

    bl_idname = "uvpackmaster3.new_target_box"
    bl_label = "New Item"
    bl_description = 'Add a new target box to the active group'

    def execute_impl(self, context):

        if self.active_g_scheme is None:
            return {'CANCELLED'}
        if self.active_group is None:
            return {'CANCELLED'}

        self.active_g_scheme.add_target_box(self.active_group)

        mark_boxes_dirty(self, context)
        return {'FINISHED'}


class UVPM3_OT_RemoveTargetBox(UVPM3_OT_GroupingSchemeOperatorGeneric, AccessDescIdAttrMixin):

    bl_idname = "uvpackmaster3.remove_target_box"
    bl_label = "Remove"
    bl_description = 'Remove the active target box'

    def execute_impl(self, context):

        if self.active_group is None:
            return {'CANCELLED'}

        self.active_group.remove_target_box(self.active_group.active_target_box_idx)

        mark_boxes_dirty(self, context)
        return {'FINISHED'}

class UVPM3_OT_MoveTargetBox(UVPM3_OT_GroupingSchemeOperatorGeneric, AccessDescIdAttrMixin):
    bl_idname = "uvpackmaster3.move_target_box"
    bl_label = "Move"
    bl_description = "Move the active box up/down in the list"

    direction : EnumProperty(items=[("UP", "Up", "", 0), ("DOWN", "Down", "", 1)])

    def execute_impl(self, context):
        if self.active_group is None:
            return {'CANCELLED'}

        old_idx = self.active_group.active_target_box_idx
        new_idx = old_idx
        if self.direction == "UP":
            if old_idx > 0:
                new_idx = old_idx - 1
        else:
            if old_idx < len(self.active_group.target_boxes) - 1:
                new_idx = old_idx + 1
        self.active_group.target_boxes.move(old_idx, new_idx)
        self.active_group.active_target_box_idx = new_idx
        return {'FINISHED'}

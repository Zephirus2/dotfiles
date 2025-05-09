
from .app_iface import *


class GroupingSchemeDescriptorMetadata:

    def __init__(self, panel_name='Island Grouping'):
        self.panel_name = panel_name


class GroupingSchemeAccess:

    DESC_METADATA = {
                        'default' : GroupingSchemeDescriptorMetadata(panel_name='Island Grouping'),
                        'editor' : GroupingSchemeDescriptorMetadata(panel_name='Island Grouping'),
                        'lock_group' : GroupingSchemeDescriptorMetadata(panel_name='Lock Groups'),
                        'stack_group' : GroupingSchemeDescriptorMetadata(panel_name='Stack Groups'),
                        'track_group' : GroupingSchemeDescriptorMetadata(panel_name='Track Groups')
                    }

    def init_access(self, context, desc_id=None, desc=None, ui_drawing=False):
        self.context = context
        self.ui_drawing = ui_drawing
        self.g_schemes = get_scene_props(self.context).grouping_schemes

        if desc:
            self.desc_id = None
            self.desc = desc
        else:
            if not desc_id:
                desc_id = self.get_desc_id_from_obj(self)

                if not desc_id:
                    raise RuntimeError('GroupingSchemeAccess: desc id not set')

            self.desc_id = desc_id
            self.desc = getattr(get_scene_props(context).grouping_scheme_access_descriptors, desc_id)

        self.init_active_members()

    def init_active_members(self):
        self.active_g_scheme = self.init_active_g_scheme()

        if not self.ui_drawing and self.active_g_scheme is not None:
            self.active_g_scheme.init_defaults()

        self.active_group = self.init_active_group()
        self.active_target_box = self.init_active_target_box()

    def get_g_schemes_enum_items(self):
        items = []
        enumerated_g_schemes = list(enumerate(self.g_schemes))
        enumerated_g_schemes.sort(key=lambda i: i[1].name)

        for idx, g_scheme in enumerated_g_schemes:
            items.append((str(g_scheme.uuid), g_scheme.name, "", idx))
        return items

    @staticmethod
    def get_g_schemes_enum_items_callback(property_self, context):
        g_scheme_access = GroupingSchemeAccess()
        g_scheme_access.init_access(context, ui_drawing=True, desc_id='default')
        return g_scheme_access.get_g_schemes_enum_items()

    def create_g_scheme(self, set_active=True):
        new_g_scheme = self.g_schemes.add()
        new_g_scheme.init_defaults()
        new_g_scheme.add_group_with_target_box()
        if set_active:
            self.set_active_g_scheme_uuid(new_g_scheme.uuid)

        return new_g_scheme
    
    def get_active_g_scheme_uuid(self):
        return  self.desc.active_g_scheme_uuid

    def get_active_g_scheme_idx(self):
        active_g_scheme_uuid = self.get_active_g_scheme_uuid()

        for idx, g_scheme in enumerate(self.g_schemes):
            if active_g_scheme_uuid == g_scheme.uuid:
                return idx

        return -1

    def init_active_g_scheme(self):
        active_g_scheme_idx = self.get_active_g_scheme_idx()
        active_g_scheme = None

        if active_g_scheme_idx >= 0:
            active_g_scheme = self.g_schemes[active_g_scheme_idx]

        return active_g_scheme
    
    def get_g_schemes(self):
        return self.g_schemes
    
    def get_active_g_scheme_safe(self):
        if self.active_g_scheme is None:
            desc_metadata = self.DESC_METADATA[self.desc_id]
            raise RuntimeError('Grouping scheme requested but it was not found - select a scheme in the {} panel'.format(desc_metadata.panel_name))
        
        return self.active_g_scheme

    def init_active_group(self):
        if self.active_g_scheme is None:
            return None

        return self.active_g_scheme.get_active_group()

    def init_active_target_box(self):
        if self.active_group is None:
            return None

        return self.active_group.get_active_target_box()

    def set_active_g_scheme_uuid(self, uuid):
        self.desc.active_g_scheme_uuid = uuid
        self.init_active_members()

    def impl_active_box(self):
        return self.active_target_box
    
    @staticmethod
    def get_desc_id_from_obj(obj):
        if hasattr(obj, 'ACCESS_DESC_ID') and obj.ACCESS_DESC_ID:
            return str(obj.ACCESS_DESC_ID)
        
        if hasattr(obj, 'access_desc_id') and obj.access_desc_id:
            return str(obj.access_desc_id)
        
        if hasattr(obj, 'grouping_config') and obj.grouping_config:
            return obj.grouping_config.g_scheme_access_desc_id
        
        if hasattr(obj, 'get_mode'):
            mode = obj.get_mode()
            if mode:
                return mode.grouping_config.g_scheme_access_desc_id

        return None
    
    def execute_internal(self, context):
        
        self.init_access(context, desc_id=self.get_desc_id_from_obj(self))
        return super().execute_internal(context)
    

class GroupByNameAccess:
    def __init__(self, g_scheme):
        self.g_scheme = g_scheme
        self.group_by_name = dict()

        for group in self.g_scheme.groups:
            if group.name in self.group_by_name:
                self.group_by_name[group.name].append(group)
            else:
                self.group_by_name[group.name] = [group]

    def get(self, name):
        return self.get_all(name)[-1]

    def get_all(self, name):
        groups = self.group_by_name.get(name)
        if groups is None:
            groups = [self.g_scheme.add_group_with_target_box(name)]
            self.group_by_name[name] = groups
        return groups


class AccessDescIdAttrMixin:

    access_desc_id : StringProperty(name='', description='', default='')

    def get_access_desc_kwargs(self, context):

        kwargs = {}
        if self.access_desc_id:
            kwargs['desc_id'] = self.access_desc_id
            kwargs['desc'] = None
        else:
            kwargs['desc_id'] = None
            kwargs['desc'] = context.uvpm3_access_desc

        return kwargs

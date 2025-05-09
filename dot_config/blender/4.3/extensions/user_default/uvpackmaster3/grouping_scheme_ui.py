
from .grouping_scheme_access import GroupingSchemeAccess, AccessDescIdAttrMixin
from .app_iface import *


class UVPM3_OT_BrowseGroupingSchemes(Operator, AccessDescIdAttrMixin):

    bl_options = {'INTERNAL'}
    bl_idname = 'uvpackmaster3.browse_grouping_schemes'
    bl_label = 'Browse Grouping Schemes'
    bl_description = "Browse Grouping Schemes"

    active_g_scheme_uuid : StringProperty(name='', description='', default='')

    def execute(self, context):

        g_scheme_access = GroupingSchemeAccess()
        g_scheme_access.init_access(context, **self.get_access_desc_kwargs(context))
        g_scheme_access.set_active_g_scheme_uuid(self.active_g_scheme_uuid)
        return {'FINISHED'}


class UVPM3_MT_BrowseGroupingSchemesBase(Menu):

    bl_label = "Grouping Schemes"

    ACCESS_DESC_ID = None
    ACCESS_DESC = None

    def draw(self, context):
        g_scheme_access = GroupingSchemeAccess()
        g_scheme_access.init_access(context, ui_drawing=True, desc_id=self.ACCESS_DESC_ID, desc=self.ACCESS_DESC)
        g_schemes = g_scheme_access.get_g_schemes()

        enumerated_g_schemes = list(enumerate(g_schemes))
        enumerated_g_schemes.sort(key=lambda i: i[1].name)

        layout = self.layout

        if self.ACCESS_DESC:
            layout.context_pointer_set('uvpm3_access_desc', self.ACCESS_DESC)

        for idx, g_scheme in enumerated_g_schemes:
            operator = layout.operator(UVPM3_OT_BrowseGroupingSchemes.bl_idname, text=g_scheme.name)
            operator.active_g_scheme_uuid = g_scheme.uuid
            if self.ACCESS_DESC_ID:
                operator.access_desc_id = self.ACCESS_DESC_ID


class UVPM3_MT_BrowseGroupingSchemesDefault(UVPM3_MT_BrowseGroupingSchemesBase):
    bl_idname = "UVPM3_MT_BrowseGroupingSchemesDefault"
    ACCESS_DESC_ID = "default"


class UVPM3_MT_BrowseGroupingSchemesEditor(UVPM3_MT_BrowseGroupingSchemesBase):
    bl_idname = "UVPM3_MT_BrowseGroupingSchemesEditor"
    ACCESS_DESC_ID = "editor"


class UVPM3_MT_BrowseGroupingSchemesLockGroup(UVPM3_MT_BrowseGroupingSchemesBase):
    bl_idname = "UVPM3_MT_BrowseGroupingSchemesLockGroup"
    ACCESS_DESC_ID = "lock_group"


class UVPM3_MT_BrowseGroupingSchemesStackGroup(UVPM3_MT_BrowseGroupingSchemesBase):
    bl_idname = "UVPM3_MT_BrowseGroupingSchemesStackGroup"
    ACCESS_DESC_ID = "stack_group"


class UVPM3_MT_BrowseGroupingSchemesTrackGroup(UVPM3_MT_BrowseGroupingSchemesBase):
    bl_idname = "UVPM3_MT_BrowseGroupingSchemesTrackGroup"
    ACCESS_DESC_ID = "track_group"


class UVPM3_MT_BrowseGroupingSchemesContext(UVPM3_MT_BrowseGroupingSchemesBase):

    bl_idname = "UVPM3_MT_BrowseGroupingSchemesContext"

    def draw(self, context):
        self.ACCESS_DESC = (context.uvpm3_access_desc)
        super().draw(context)


class UVPM3_UL_GroupInfo(UIList):
    bl_idname = 'UVPM3_UL_GroupInfo'

    def draw_item(self, _context, layout, _data, item, icon, _active_data, _active_propname, _index):
        group_info = item

        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            split = layout.split(factor=0.2)
            split.prop(group_info, "color", text="", emboss=True)
            row = split.row().split(factor=0.8)
            row.prop(group_info, "name", text="", emboss=False)
            row.label(text="[D]" if group_info.is_default() else "   ")

        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)


class UVPM3_UL_TargetBoxes(UIList):
    bl_idname = 'UVPM3_UL_TargetBoxes'
    
    def draw_item(self, _context, layout, _data, item, icon, _active_data, _active_propname, _index):
        target_box = item

        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.label(text="Box {}: {}".format(_index, target_box.label()))

        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)

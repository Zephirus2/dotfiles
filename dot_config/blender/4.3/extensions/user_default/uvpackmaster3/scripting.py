
from .enums import EnumValue
from .utils import PropertyWrapper, redraw_ui
from .grouping_scheme import UVPM3_GroupingSchemeAccessDescriptor
from .grouping_scheme_access import GroupingSchemeAccess
from .pack_context import PackContext
from .operator_misc import UVPM3_OT_ConfirmBase
from .app_iface import *


class ScriptEvent:
    BEFORE_OP = EnumValue('before_op', 'Before Operation', '')
    AFTER_OP = EnumValue('after_op', 'After Operation', '')

    CODE_TO_EVENT = {
        BEFORE_OP.code : BEFORE_OP,
        AFTER_OP.code : AFTER_OP
    }

    @classmethod
    def items(cls):
        return (cls.BEFORE_OP, cls.AFTER_OP)
    


def _get_script_data():
    return app_texts()


class UVPM3_OT_ScriptSet(Operator):

    bl_idname = 'uvpackmaster3.script_set'
    bl_label = 'Set String'
    bl_description = ''

    script : StringProperty(name='', default='')

    def execute(self, context):
        context.uvpm3_script_entry.script = str(self.script)
        return {'FINISHED'}
    

class UVPM3_MT_ScriptSet(Menu):

    bl_label = "Set"
    bl_idname = "UVPM3_MT_ScriptSet"

    def draw(self, context):

        layout = self.layout
        layout.context_pointer_set('uvpm3_script_entry', context.uvpm3_script_entry)

        if len(_get_script_data()) == 0:
            layout.label(text='No script found in the blend file. Add a script in the Text Editor', icon='ERROR')
            return

        for text in _get_script_data().keys():
            op = layout.operator(UVPM3_OT_ScriptSet.bl_idname, text=text)
            op.script = text


class UVPM3_ScriptEntry(PropertyGroup):

    enabled : BoolProperty(name='Enabled', default=True, description='Determines whether the script will be executed')
    script : StringProperty(
        default='',
        name='Script',
        description='Name of the script in the Text Editor to be executed')
    
    use_g_scheme : BoolProperty(
        name='Use Grouping Scheme',
        description='Execute the script per every group defined in a grouping scheme',
        default=False
    )

    func_name : StringProperty(
        name='Function Name',
        default='UVPM3_script',
        description='Python function name in the script to be executed'
    )

    func_args : StringProperty(
        name='Function Arguments',
        default='',
        description='Comma-separated list of additional arguments which will passed to the script function after two base arguments (context, group_name)'
    )

    g_scheme_access_desc : PointerProperty(type=UVPM3_GroupingSchemeAccessDescriptor)


class UVPM3_ScriptCollection(PropertyGroup):

    scripts : CollectionProperty(type=UVPM3_ScriptEntry)
    active_script_entry_idx : IntProperty(name='', default=0)
    enabled : BoolProperty(
        name='Enabled',
        default=False,
        description='Determines whether the given script collection will be executed')


class UVPM3_ScriptContainer(PropertyGroup):

    enabled : BoolProperty(name='Scripting Enabled', default=False)

    before_op : PointerProperty(type=UVPM3_ScriptCollection)
    after_op : PointerProperty(type=UVPM3_ScriptCollection)


class UVPM3_UL_ScriptCollection(UIList):

    bl_idname = 'UVPM3_UL_ScriptCollection'

    def draw_item(self, _context, layout, _data, item, icon, _active_data, _active_propname, _index):
        s_entry = item

        main_row = layout.row(align=True)
        idx_row = main_row.row(align=True)
        idx_row.alignment = 'LEFT'
        idx_row.label(text=str(_index)+':')
        main_row.prop(s_entry, 'enabled', text='')
        row = main_row.row(align=True)
        # row.enabled = s_entry.enabled
        script_row = row.row(align=True)
        script_row.prop(s_entry, 'script', text='')
        script_row.enabled = False

        if not s_entry.script:
            from .help import UVPM3_OT_WarningPopup
            UVPM3_OT_WarningPopup.draw_operator(row, text='Script name not set')
        elif s_entry.script not in _get_script_data().keys():
            from .help import UVPM3_OT_WarningPopup
            UVPM3_OT_WarningPopup.draw_operator(row, text='Script not found in the blend file')

        set_row = row.row(align=True)
        set_row.alignment = 'RIGHT'
        set_row.context_pointer_set('uvpm3_script_entry', s_entry)
        set_row.menu(UVPM3_MT_ScriptSet.bl_idname)


class UVPM3_ScriptCollectionWrapper:

    def __init__(self, container, s_event, collection):
        self.container = container
        self.s_event = s_event
        self.c = collection

    def __op_init(self, op):
        op.script_container_id = self.container.id
        op.script_event_code = self.s_event.code

    def active_script_entry_valid(self):
        return (self.c.active_script_entry_idx >=0) and (self.c.active_script_entry_idx < len(self.c.scripts))

    def draw(self, layout):
        from .panel import PanelUtilsMixin

        main_col = layout.box().column(align=True)
        row = main_col.row(align=True)
        row.prop(self.c, 'enabled', text='')
        row.label(text="'{}' scripts".format(self.s_event.name))

        if not self.c.enabled:
            return
        main_col.separator()

        row = main_col.row()
        row.template_list(UVPM3_UL_ScriptCollection.bl_idname, "", self.c, 'scripts',
                            self.c,
                            "active_script_entry_idx", rows=3)

        col = row.column(align=True)
        op_row = col.row(align=True)
        op = op_row.operator(UVPM3_OT_ScriptAddEntry.bl_idname, icon='ADD', text="")
        self.__op_init(op)
        op_row = col.row(align=True)
        op = op_row.operator(UVPM3_OT_ScriptRemoveEntry.bl_idname, icon='REMOVE', text="")
        self.__op_init(op)
        op.script_entry_idx = self.c.active_script_entry_idx
        op_row.enabled = len(self.c.scripts) > 0

        col.separator()
        op_row = col.row(align=True)
        op = op_row.operator(UVPM3_OT_ScriptMoveActiveEntry.bl_idname, icon='TRIA_UP', text="")
        self.__op_init(op)
        op.direction = 'UP'

        op_row = col.row(align=True)
        op = op_row.operator(UVPM3_OT_ScriptMoveActiveEntry.bl_idname, icon='TRIA_DOWN', text="")
        self.__op_init(op)
        op.direction = 'DOWN'

        main_col.separator()
        main_col.label(text='Script options:')
        if self.active_script_entry_valid():
            s_entry_idx = self.c.active_script_entry_idx
            s_entry = self.c.scripts[s_entry_idx]

            entry_layout = main_col
            func_prop_box = entry_layout.box()
            func_prop_col = func_prop_box.column(align=True)
            func_prop_col.label(text='Function')
            func_prop_split = func_prop_col.split(factor=0.01)
            func_prop_split.column()
            func_prop_split = func_prop_split.split(factor=0.3)
            name_col = func_prop_split.column(align=True)
            prop_col = func_prop_split.column(align=True)

            # name_col.alignment = 'RIGHT'
            name_col.label(text='Name:')
            name_col.label(text='Args:')
            prop_col.prop(s_entry, 'func_name', text='')
            prop_col.prop(s_entry, 'func_args', text='')

            box = entry_layout.box()
            box.prop(s_entry, 'use_g_scheme')

            if s_entry.use_g_scheme:
                box = entry_layout.box()

                from .panel_grouping_editor import  GroupingSchemeDrawer
                g_scheme_drawer = GroupingSchemeDrawer(
                    self.container.context,
                    None,
                    access_desc=s_entry.g_scheme_access_desc,
                    draw_edit_g_scheme_button=True)
                g_scheme_drawer.draw_g_schemes(box)

        # layout.separator()

    def add(self):
        self.c.scripts.add()
        self.c.active_script_entry_idx = len(self.c.scripts)-1

    def remove(self, s_entry_idx):
        self.c.scripts.remove(s_entry_idx)
        self.c.active_script_entry_idx = min(self.c.active_script_entry_idx, len(self.c.scripts)-1)

    def move_active_script_entry(self, up):
        old_idx = self.c.active_script_entry_idx
        new_idx = old_idx
        if up:
            if old_idx > 0:
                new_idx = old_idx - 1
        else:
            if old_idx < len(self.c.scripts) - 1:
                new_idx = old_idx + 1

        self.c.scripts.move(old_idx, new_idx)
        self.c.active_script_entry_idx = new_idx

    def raise_script_error(self, err_msg, s_entry_idx=None):
        err_header = 'Scripting error'
        if s_entry_idx is not None:
            err_header += ' ({}, script {})'.format(self.s_event.name, s_entry_idx)

        raise RuntimeError('{}: {}'.format(err_header, err_msg))
    
    def exec_script_entry(self, s_entry_idx):
        s_entry = self.c.scripts[s_entry_idx]

        if not s_entry.enabled:
            return
            
        script_name = str(s_entry.script)

        if not script_name:
            self.raise_script_error("script name not set", s_entry_idx=s_entry_idx)

        try:
            script_str = _get_script_data()[script_name].as_string()
        except:
            self.raise_script_error("could not find script '{}'".format(script_name), s_entry_idx=s_entry_idx)

        try:
            exec(script_str)
        except Exception as e:
            self.raise_script_error('exception: ' + str(e), s_entry_idx=s_entry_idx)

        attrs = locals()

        func_name = s_entry.func_name

        if not func_name:
            self.raise_script_error("Function name not set", s_entry_idx=s_entry_idx)

        if func_name not in attrs:
            self.raise_script_error("'{}' function not found in the script".format(func_name), s_entry_idx=s_entry_idx)

        script_func = attrs[func_name]

        if not callable(script_func):
            self.raise_script_error("'{}' attribute is not callable".format(func_name), s_entry_idx=s_entry_idx)

        from inspect import signature
        sig = signature(script_func)
        if len(sig.parameters) < 2:
            self.raise_script_error("'{}' function must take at least two arguments: (context, group_name)".format(func_name), s_entry_idx=s_entry_idx)

        func_args = str(s_entry.func_args)
        func_args_array = func_args.split(',') if func_args else []

        def run_script_func(group_name):
            try:
                script_func(self.container.context, group_name, *func_args_array)
            except Exception as e:
                self.raise_script_error('exception: ' + str(e), s_entry_idx=s_entry_idx)
        
        if s_entry.use_g_scheme:
            g_scheme_access = GroupingSchemeAccess()
            g_scheme_access.init_access(self.container.context, None, desc=s_entry.g_scheme_access_desc)

            g_scheme = g_scheme_access.active_g_scheme
            if not g_scheme:
                self.raise_script_error("grouping scheme not set", s_entry_idx=s_entry_idx)

            serializer = g_scheme.get_iparam_serializer()
            ref_p_context = PackContext(self.container.context)

            for group in g_scheme.groups:
                p_context = PackContext(self.container.context)
                serializer.init_context(p_context)
                for p_obj_idx, p_obj in enumerate(p_context.p_objects):
                    p_obj.select_faces(p_obj.visible_faces_stored_indices, False)
                    p_obj.select_faces(serializer.get_faces_for_iparam_value(p_obj_idx, p_obj, p_obj.visible_faces_stored_indices, group.num), True)

                p_context.update_meshes()
                run_script_func(group.name)

            p_context = PackContext(self.container.context)
            for p_obj_idx, p_obj in enumerate(p_context.p_objects):
                p_obj.select_faces(p_obj.visible_faces_stored_indices, False)
                p_obj.select_faces(ref_p_context.p_objects[p_obj_idx].selected_faces_stored_indices, True)

            p_context.update_meshes()

        else:
            run_script_func(None)
        
        del attrs[func_name]

    def exec_scripts(self):

        if not self.c.enabled:
            return

        for s_entry_idx in range(len(self.c.scripts)):
            self.exec_script_entry(s_entry_idx)
            

class UVPM3_ScriptContainerWrapper:

    def __init__(self, context, id, container):
        self.context = context
        self.id = id
        self.c = container
        self.prefs = get_prefs()

    def get_collection(self, s_event_code):
        return UVPM3_ScriptCollectionWrapper(self, ScriptEvent.CODE_TO_EVENT[s_event_code], getattr(self.c, s_event_code))
    
    def get_enabled_property(self):
        return PropertyWrapper(self.c, 'enabled')
    
    def enabled(self):
        return bool(self.c.enabled) and self.prefs.script_allow_execution

    def exec_scripts(self, s_event):
        if not self.enabled():
            return
        
        collection = self.get_collection(s_event.code)
        collection.exec_scripts()

    def draw(self, layout):

        if not self.prefs.script_allow_execution:
            layout.operator(UVPM3_OT_ScriptAllowExecution.bl_idname)
            return
        
        first = True

        for s_event in ScriptEvent.items():
            if not first:
                layout.separator()
                layout.separator()
            first = False

            coll_layout = layout.column(align=True)
            collection = self.get_collection(s_event.code)
            collection.draw(coll_layout)
            


class UVPM3_Scripting(PropertyGroup):

    packing : PointerProperty(type=UVPM3_ScriptContainer)

    @staticmethod
    def get_container(context, container_id):
        return UVPM3_ScriptContainerWrapper(context, container_id, getattr(get_scene_props(context).scripting, container_id))
    
    @staticmethod
    def exec_scripts(context, s_event, container_id):
        container = UVPM3_Scripting.get_container(context, container_id)
        container.exec_scripts(s_event)



class UVPM3_PT_ScriptingBase():

    def get_main_property(self):
        return UVPM3_Scripting.get_container(self.context, self.SCRIPT_CONTAINER_ID).get_enabled_property()

    def draw_impl(self, context):
        s_container = UVPM3_Scripting.get_container(context, self.SCRIPT_CONTAINER_ID)
        s_container.draw(self.layout)


class ScriptAttrMixin:

    script_container_id : StringProperty(name='', default='')
    script_event_code : StringProperty(name='', default='')
    script_entry_idx : IntProperty(name='', default=-1)


class UVPM3_OT_ScriptBase(Operator):
    
    def execute(self, context):
        self.s_container = UVPM3_Scripting.get_container(context, self.script_container_id)
        self.s_collection = self.s_container.get_collection(self.script_event_code)
        return self.execute_impl(context)


class UVPM3_OT_ScriptAddEntry(UVPM3_OT_ScriptBase, ScriptAttrMixin):

    bl_idname = 'uvpackmaster3.script_add_entry'
    bl_label = 'Add Script'
    bl_description = 'Add a new script'

    def execute_impl(self, context):
        self.s_collection.add()
        return {'FINISHED'}
    

class UVPM3_OT_ScriptRemoveEntry(UVPM3_OT_ScriptBase, ScriptAttrMixin):

    bl_idname = 'uvpackmaster3.script_remove_entry'
    bl_label = 'Add Script'
    bl_description = 'Remove the active script'

    def execute_impl(self, context):
        self.s_collection.remove(self.script_entry_idx)
        return {'FINISHED'}


class UVPM3_OT_ScriptMoveActiveEntry(UVPM3_OT_ScriptBase, ScriptAttrMixin):

    bl_idname = "uvpackmaster3.script_move_active_entry"
    bl_label = "Move"
    bl_description = "Move the active script up/down in the list"

    direction : EnumProperty(items=[("UP", "Up", "", 0), ("DOWN", "Down", "", 1)])

    def execute_impl(self, context):
        self.s_collection.move_active_script_entry(self.direction == "UP")
        return {'FINISHED'}


class UVPM3_OT_ScriptAllowExecution(UVPM3_OT_ConfirmBase):

    bl_idname = 'uvpackmaster3.script_allow_execution'
    bl_label = 'Allow Script Execution'

    TEXT_LINES = [
        'WARNING: keep in mind that every third-party script may potentially be dangerous to your system - always execute scripts from a trusted source only. Press OK to allow script execution.'
    ]

    def execute_impl(self, context):
        get_prefs().script_allow_execution = True
        self.report({'INFO'}, 'Script execution allowed. Save Blender Preferences to remember that setting.')
        redraw_ui(context)
        return {'FINISHED'}

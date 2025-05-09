
INSIDE_BLENDER = True

try:
    import bpy
except:
    INSIDE_BLENDER = False


if INSIDE_BLENDER:
    import bpy
    import _bpy as bpy_internal
    import bmesh
    import blf
    import bpy_types
    from bpy_extras.io_utils import ImportHelper, ExportHelper
    from bl_ui.utils import PresetPanel

    from bpy.app.handlers import persistent as persistent_handler

    from bpy.props import (
        IntProperty,
        FloatProperty,
        BoolProperty,
        StringProperty,
        EnumProperty,
        CollectionProperty,
        PointerProperty,
        FloatVectorProperty
    )

    from bpy.types import (
        PropertyGroup,
        Operator,
        Menu,
        SpaceImageEditor,
        UIList,
        Panel,
        AddonPreferences,
        Window
    )


    class MeshWrapper:

        UV_COORD_PRECISION = 5 # None
        UV_CONNECT_LIMIT = None # '0.0001'

        @staticmethod
        def obj_is_mesh(obj):
            return obj.type == 'MESH'
        
        @staticmethod
        def objs_equal(obj1, obj2):
            return obj1.data == obj2.data

        @staticmethod
        def get_vcolor(vcolor_layer, face):
            return face[vcolor_layer]

        @staticmethod
        def set_vcolor(vcolor_layer, face, value):
            face[vcolor_layer] = value

        @staticmethod
        def update_meshes(p_context):
            for p_obj in p_context.p_objects:
                p_obj.mw.update_mesh()

        def __init__(self, p_obj):
            self.p_obj = p_obj
            self.bm = bmesh.from_edit_mesh(p_obj.obj.data)
            self.bm.verts.ensure_lookup_table()
            self.bm.faces.ensure_lookup_table()

        def get_uv_layer(self):
            return self.bm.loops.layers.uv.verify()
        
        def update_mesh(self):
            bmesh.update_edit_mesh(self.p_obj.obj.data)

        def loop_vertex_index(self, loop):
            return loop.vert.index

        def pre_uv_self_modification(self):
            pass

        def loop_uv_is_self_modified(self, loop):
            return False
        
        def get_or_create_vcolor_layer(self, iparam_info):
            # MUSTDO: implement layer caching
            vcolor_chname = iparam_info.get_vcolor_chname()
            default_value = iparam_info.get_default_vcolor()

            layer_container = self.bm.faces.layers.int
            if vcolor_chname not in layer_container:
                vcolor_layer = layer_container.new(vcolor_chname)

                for face in self.bm.faces:
                    self.set_vcolor(vcolor_layer, face, default_value)

                self.p_obj.invalidate_faces_stored()

            else:
                vcolor_layer = layer_container[vcolor_chname]

            return vcolor_layer
        
        def uv_select_sync(self):
            return self.p_obj.p_context.context.tool_settings.use_uv_select_sync
        
        def view_to_region(self, coords):
            return self.p_obj.p_context.context.region.view2d.view_to_region(coords[0], coords[1])
        
        @property
        def faces(self):
            return self.bm.faces
        
        @property
        def verts(self):
            return self.bm.verts


    class UVPM3_OT_SaveBlenderPreferences(Operator):

        bl_label = 'Save Blender Preferences'
        bl_idname = 'uvpackmaster3.save_blender_preferences'
        bl_description = 'Save Blender preferences. Note it will save all Blender preferences, not only UVPackmaster-related'


        def execute(self, context):
            bpy.ops.wm.save_userpref()
            self.report({'INFO'}, 'Preferences saved')
            return {'FINISHED'}


    class AppInterface:

        APP_ID = 'blender'
        APP_NAME = 'Blender'
        APP_VERSION = bpy.app.version

        additional_classes = [UVPM3_OT_SaveBlenderPreferences]
        registered_classes = []

        @classmethod
        def register(cls, classes, scripted_operators_classes):
            cls.registered_classes = list(scripted_operators_classes)
            cls.registered_classes += classes
            cls.registered_classes += cls.additional_classes

            for c in cls.registered_classes:
                bpy.utils.register_class(c)

            from .prefs import UVPM3_SceneProps
            bpy.types.Scene.uvpm3_props = PointerProperty(type=UVPM3_SceneProps)

        @classmethod
        def unregister(cls):
            for c in reversed(cls.registered_classes):
                bpy.utils.unregister_class(c)

            cls.registered_classes = []

            del bpy.types.Scene.uvpm3_props

        @staticmethod
        def object_property_data(obj):
            if hasattr(obj, 'bl_rna'):
                return obj.bl_rna.properties
            
            return obj._pg_cls.bl_rna.properties
        
        @staticmethod
        def save_preferences_operator():
            return UVPM3_OT_SaveBlenderPreferences

        @staticmethod
        def debug():
            return bpy.app.debug
        
        @staticmethod
        def debug_value():
            return bpy.app.debug_value
        
        @staticmethod
        def exec_operator(bl_idtype, **attrs):
            id_split = bl_idtype.split('.')

            op_callable = bpy.ops
            for s in id_split:
                op_callable = getattr(op_callable, s)

            op_callable(**attrs)


    def addon_preferences(cls):
        return type(cls.__name__, (AddonPreferences,) + cls.__bases__, dict(cls.__dict__))

    def get_prefs():
        return bpy.context.preferences.addons[__package__].preferences

    def get_scene_props(context):
        return context.scene.uvpm3_props
    
    def append_load_post_handler(handler):
        bpy.app.handlers.load_post.append(handler)

    def app_texts():
        return bpy.data.texts

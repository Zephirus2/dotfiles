
from .app_iface import *


class UVPM3_OT_Debug(Operator):

    bl_label = 'Debug'
    bl_idname = 'uvpackmaster3.debug'

    def execute(self, context):
        return {'FINISHED'}

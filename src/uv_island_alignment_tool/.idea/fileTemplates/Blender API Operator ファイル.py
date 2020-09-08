import bpy
from bpy.types import Operator

class $class_name(bpy.types.Operator):
    bl_idname = ""
    bl_label = "ラベル(メニュー名)"
    bl_description = "説明"
    bl_options = {'REGISTER', 'UNDO'}

    def __init__(self):
        pass

    @classmethod
    def poll(cls, context):
        """ここに、スクリプトを実行しても良いかチェックをする内容を書く。
        obj = context.active_object
        if obj and obj.type == 'MESH' and (obj.mode == 'EDIT'):
            # Check if select_mode is 'VERTEX'
            if context.scene.tool_settings.mesh_select_mode[0]:
                return True
        """
        return False

    def invoke(self, context, event):
        return self.execute(context)

    def execute(self, context):
        return {'FINISHED'}
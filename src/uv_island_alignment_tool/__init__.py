# Copyright (c) 2020 Samia
# リロード対応
import os
import codecs
import csv

if "bpy" in locals():
    import importlib
    importlib.reload(operator)
    importlib.reload(preferences)
    importlib.reload(updater)
else:
    from . import operator
    from . import preferences
    from . import updater
import bpy

bl_info = {
    "name": "UV Island Alignment Tool",
    "author": "Samia",
    "version": (1, 1),
    "blender": (2, 80, 0),
    "location": "",
    "description": "",
    "warning": "",
    "support": "TESTING",
    "wiki_url": "",
    "tracker_url": "https://github.com/samia-done/UV-Island-Alignment-Tool",
    "category": "UV"
}

classes = (
    preferences.UVIA_AddonPreferences,
    updater.UVIA_OT_CheckAddonUpdate,
    updater.UVIA_OT_UpdateAddon,
    operator.UVIA_ToolSettings,
    operator.UV_OT_uv_island_alignment,
    operator.UV_OT_uv_island_distribute_spacing,
    operator.UV_OT_uv_island_distribute_scaling,
    operator.UV_OT_reset_2d_cursor,
    operator.IMAGE_PT_uv_island_aligment,
)


# 翻訳辞書の取得
def get_translation_dict():
    _translation_dict = {}
    path = os.path.join(os.path.dirname(__file__), "translation_dictionary.csv")
    with codecs.open(path, 'r', 'utf-8') as f:
        reader = csv.reader(f)
        _translation_dict['ja_JP'] = {}
        for row in reader:
            for context in bpy.app.translations.contexts:
                _translation_dict['ja_JP'][(context, row[1])] = row[0]
    return _translation_dict


# def menu_func(self, context):
#     self.layout.separator()


# def register_menu():


# def unregister_menu():


def register():
    updater.register_updater(bl_info)

    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.UVIA_tool_settings = bpy.props.PointerProperty(type=operator.UVIA_ToolSettings)
    print(__package__)
    # user_prefs = bl_context_wrappers.get_user_preferences(bpy.context)

    _translation_dict = get_translation_dict()
    bpy.app.translations.register(__name__, _translation_dict)
    # register_menu()


def unregister():
    # unregister_menu()
    bpy.app.translations.unregister(__name__)

    del bpy.types.Scene.UVIA_tool_settings
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()

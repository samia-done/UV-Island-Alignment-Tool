# Copyright (c) ${YEAR} Samia

import bpy
from bpy.types import AddonPreferences
from bpy.props import (
    StringProperty,
    IntProperty,
    FloatProperty,
    FloatVectorProperty,
    BoolProperty,
    EnumProperty,
)


# Blenderのバージョンを確認する関数。
# 引数に指定したバージョンとBlenderのバージョンを比較して、次に示す値を返す。
# 1 : 引数に指定したバージョン > Blenderのバージョン
# 0 : 引数に指定したバージョン == Blenderのバージョン
# -1: 引数に指定したバージョン < Blenderのバージョン
# 引数
# major: メジャーバージョン
# minor: マイナーバージョン
def check_version(major, minor):
    if bpy.app.version[0] == major and bpy.app.version[1] == minor:
        return 0
    if bpy.app.version[0] > major:
        return 1
    if bpy.app.version[1] > minor:
        return 1
    return -1


def make_annotations(cls):
    if check_version(2, 80, 0) < 0:
        return cls

    props = {k: v for k, v in cls.__dict__.items() if isinstance(v, tuple)}
    if props:
        if '__annotations__' not in cls.__dict__:
            setattr(cls, '__annotations__', {})
        annotations = cls.__dict__['__annotations__']
        for k, v in props.items():
            annotations[k] = v
            delattr(cls, k)
    return cls


@make_annotations
class $class_name(AddonPreferences):
    bl_idname = __package__

    string_prop = bpy.props.StringProperty(
        name="",
        description="",
        default=""
    )

    int_prop = IntProperty(
        name="",
        description="",
        default=3,
        min=0,
        max=6
    )

    bool_prop = bpy.props.BoolProperty(
        name="",
        description="",
        default=False
    )

    enum_prop = bpy.props.EnumProperty(
        name="",
        description="",
        items = []
    )

    def __init__(self):
        super(AddonPreferences, self).__init__()

    def draw(self, context):
        layout = self.layout
        layout.label(text="$addon_name")
        # 登録したプロパティのnameを指定する
        # layout.prop(self, "bone_name")
        # layout.prop(self, "bone_name_junction")
        # layout.prop(self, "bone_name_suffix")
        # layout.prop(self, "zero_padding")
        # layout.prop(self, "is_reverse")
        # layout.prop(self, "is_parent")
        # layout.prop(self, "use_connect")

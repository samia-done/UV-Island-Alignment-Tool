# Copyright (c) 2020 Samia
import bpy


def get_user_preferences(context):
    if hasattr(context, "user_preferences"):
        return context.user_preferences
    return context.preferences


def get_engine(context):
    if hasattr(context, "scene"):
        return context.scene.render.engine
    return context.engine


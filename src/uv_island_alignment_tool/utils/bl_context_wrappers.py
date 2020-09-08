# Copyright (c) 2020 Samia
import bpy


def get_engine(context):
    if hasattr(context, "scene"):
        return context.scene.render.engine
    return context.engine


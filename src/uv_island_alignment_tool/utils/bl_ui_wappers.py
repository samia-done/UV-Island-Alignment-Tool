# Copyright (c) 2020 Samia
import bpy
from .bl_version_helpers import get_bl_major_version, get_bl_minor_version, has_bl_major_version


# Image UI
def get_show_normalized_coords(context):
    if has_bl_major_version(2) and get_bl_minor_version() >= 80:
        return not context.space_data.uv_editor.show_pixel_coords
    else:
        return context.space_data.uv_editor.show_normalized_coords


def set_show_normalized_coords(context, value):
    if has_bl_major_version(2) and get_bl_minor_version() >= 80:
        context.space_data.uv_editor.show_pixel_coords = not value
    else:
        context.space_data.uv_editor.show_normalized_coords = value


def get_split_percentage(layout, value):
    if has_bl_major_version(2) and get_bl_minor_version() >= 80:
        return layout.split(factor=value)
    else:
        return layout.split(percentage=value)

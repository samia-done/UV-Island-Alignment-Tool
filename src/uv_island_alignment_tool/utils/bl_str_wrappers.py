# Copyright (c) 2020 Samia
import bpy
from typing import Dict
from .bl_version_helpers import get_bl_major_version, get_bl_minor_version, has_bl_major_version


icon_map_2_80 = {
        'IMAGE': 'IMAGE_COL',
        'ZOOMIN': 'ADD',
        'ZOOMOUT': 'REMOVE',
}  # type: Dict[str, str]

menu_map_2_80 = {
        'MESH_MT_vertex_group_specials': 'MESH_MT_vertex_group_context_menu',
}  # type: Dict[str, str]


def get_icon(name):
    if has_bl_major_version(2) and get_bl_minor_version() >= 80:
        try:
            name = icon_map_2_80[name]
        except KeyError as e:
            pass
    return name


def get_menu(name):
    if has_bl_major_version(2) and get_bl_minor_version() >= 80:
        try:
            name = menu_map_2_80[name]
        except KeyError as e:
            pass
    return name

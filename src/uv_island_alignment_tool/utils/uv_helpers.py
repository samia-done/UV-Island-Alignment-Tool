from builtins import print
from typing import List, Any, Tuple
from collections import namedtuple
import bpy
import bmesh
from bmesh.types import BMFace
from .bl_version_helpers import get_bl_minor_version, has_bl_major_version


def get_uv_island_bound_box(uv_island: List[bmesh.types.BMFace], uv_layer: bmesh.types.BMLayerItem):
    BoundBox = namedtuple('BoundBox', [
        'x',
        'y',
        'x_min',
        'x_max',
        'y_min',
        'y_max',
        'width',
        'height',
    ])
    x_min = 99999999.0
    x_max = -99999999.0
    y_min = 99999999.0
    y_max = -99999999.0

    for face in uv_island:  # type: bmesh.types.BMFace
        for loop in face.loops:
            x_min = min(x_min, loop[uv_layer].uv.x)
            x_max = max(x_max, loop[uv_layer].uv.x)
            y_min = min(y_min, loop[uv_layer].uv.y)
            y_max = max(y_max, loop[uv_layer].uv.y)
    bound_box = BoundBox(
        (x_min + x_max)/2,
        (y_min + y_max)/2,
        x_min,
        x_max,
        y_min,
        y_max,
        x_max - x_min,
        y_max - y_min
    )
    return bound_box


def get_uv_islands_bound_box(selected_uv_islands, uv_layer):
    print("get_uv_islands_bound_box")
    selected_uv_islands_bounds = []
    for uv_island in selected_uv_islands:  # type: List[bmesh.types.BMFace]
        selected_uv_islands_bounds.append(get_uv_island_bound_box(uv_island=uv_island, uv_layer=uv_layer))
    return selected_uv_islands_bounds


def get_selected_faces(bm: bmesh.types.BMesh, uv_layer: bmesh.types.BMLayerItem):
    print("get_selected_faces")
    selected_faces = []  # type: List[bmesh.types.BMFace]
    for face in bm.faces:  # type: bmesh.types.BMFace
        if face.select:
            if face.loops[0][uv_layer].select:
                selected_faces.append(face)

    return selected_faces


def get_selected_uv_islands(bm=None, uv_layer=None):
    print("get_selected_uv_islands")
    # if not bm:
    #     bm = bmesh.from_edit_mesh(bpy.context.active_object.data)
    #     uv_layer = bm.loops.layers.uv.verify()
    #
    # # if hasattr(bm.verts, "ensure_lookup_table"):
    # if bpy.app.version[0] >= 2 and bpy.app.version[1] >= 73:
    #     bm.verts.ensure_lookup_table()
    #     bm.edges.ensure_lookup_table()
    #     bm.faces.ensure_lookup_table()
    #

    # 選択が頂点だけでも、アイランドとして処理するために選択している。
    if not bpy.context.scene.tool_settings.use_uv_select_sync:
        if has_bl_major_version(2) and get_bl_minor_version() >= 80:
            bpy.ops.uv.select_linked()
        else:
            bpy.ops.uv.select_linked(extend=False)

    selected_uvislands = []  # type: List[bmesh.types.BMFace]
    selected_faces = get_selected_faces(bm, uv_layer)  # type: List[bmesh.types.BMFace]
    remove_faces = selected_faces.copy()  # type: List[bmesh.types.BMFace]

    for face in selected_faces:
        if face in remove_faces:
            bpy.ops.uv.select_all(action='DESELECT')
            face.loops[0][uv_layer].select = True

            # Extend selection / リンク選択
            if has_bl_major_version(2) and get_bl_minor_version() >= 80:
                bpy.ops.uv.select_linked()
            else:
                bpy.ops.uv.select_linked(extend=False)

            selected_uvislands.append(get_selected_faces(bm=bm, uv_layer=uv_layer))
            for remove_item in selected_uvislands[-1]:  # type: bmesh.types.BMFace
                remove_faces.remove(remove_item)

    # 選択を元に戻す
    for face in selected_faces:
        for loop in face.loops:
            loop[uv_layer].select = True

    return selected_uvislands

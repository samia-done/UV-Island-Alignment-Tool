from typing import Tuple, Iterator
import bpy
import bmesh
import copy
import time
import mathutils
from bmesh.types import BMFace
from bpy.types import OperatorProperties

from .utils.bl_ui_wappers import get_split_percentage, get_show_normalized_coords, set_show_normalized_coords
from .utils.bl_version_helpers import has_bl_major_version, get_bl_minor_version
from .utils import uv_helpers
from .utils.bl_anotations import make_annotations


@make_annotations
class UVIA_ToolSettings(bpy.types.PropertyGroup):
    pivot_xy = [
        {"x": -0.5, "y": 0.5}, {"x": 0.0, "y": 0.5}, {"x": 0.5, "y": 0.5},
        {"x": -0.5, "y": 0.0}, {"x": 0.0, "y": 0.0}, {"x": 0.5, "y": 0.0},
        {"x": -0.5, "y": -0.5}, {"x": 0.0, "y": -0.5}, {"x": 0.5, "y": -0.5}
    ]

    pivot_point_items = [
        ("0", "Upper Left", "", "", 0),
        ("1", "Up", "", "", 1),
        ("2", "Upper Right", "", "", 2),
        ("3", "Left", "", "", 3),
        ("4", "Center", "", "", 4),
        ("5", "Right", "", "", 5),
        ("6", "Lower Left", "", "", 6),
        ("7", "Bottom", "", "", 7),
        ("8", "Lower Right", "", "", 8)
    ]
    # ピボットポイント
    pivot_point = bpy.props.EnumProperty(
        name="Pivot Point",
        description="Pivot Point",
        items=pivot_point_items,
        options={'HIDDEN'}
    )

    align_to_items = [
        ("0", "Island", "", "", 0),
        ("1", "2D Cursor", "", "", 1),
        ("2", "Texture", "", "", 2),
    ]
    # 整列先
    align_to = bpy.props.EnumProperty(
        name="Align To",
        description="Align To",
        items=align_to_items,
        options={'HIDDEN'}
    )
    # 画像のマージン
    margin = bpy.props.IntProperty(
        name="Margin",
        description="Margin",
        default=0,
        min=0,
        options={'HIDDEN'}
    )
    # 分布の間隔
    spacing = bpy.props.IntProperty(
        name="Spacing",
        description="Spacing",
        default=0,
        options={'HIDDEN'}
    )


@make_annotations
class UV_OT_uv_island_Base:
    # 方向
    direction = bpy.props.IntProperty(
        description="Direction",
        default=4,
        min=0,
        max=8,
        options={'HIDDEN'}
    )

    # タイプ
    movement_type = bpy.props.IntProperty(
        description="Type",
        default=4,
        min=0,
        max=8,
        options={'HIDDEN'}
    )

    # 2Dカーソルの位置
    cursor_location = (0, 0)
    current_cursor_location = (0, 0)
    current_pivot_point = (0, 0)
    current_show_normalized_coords = False

    tool_settings = None
    pivot_xy = (0, 0)

    # bmesh
    bm = None
    active_uv_layer = None
    selected_uv_islands = None
    selected_uv_islands_bound_box = None

    # target
    target_x_min = None
    target_x_max = None
    target_x_avg = None
    target_y_min = None
    target_y_max = None
    target_y_avg = None

    def __init__(self):
        print("UV_OT_uv_island_Base Init")

        # 2Dカーソルの位置
        self.cursor_location = (0, 0)
        self.current_cursor_location = (0, 0)
        self.current_pivot_point = (0, 0)
        self.current_show_normalized_coords = False

        self.tool_settings = None
        self.pivot_xy = (0, 0)

        # bmesh
        self.bm = None
        self.active_uv_layer = None
        self.selected_uv_islands = None
        self.selected_uv_islands_bound_box = None

        # target
        self.target_x_min = None
        self.target_x_max = None
        self.target_x_avg = None
        self.target_y_min = None
        self.target_y_max = None
        self.target_y_avg = None

    def execute(self, context):
        # ピボットポイントをバウンディングボックスの中心
        self.current_pivot_point = copy.copy(context.space_data.pivot_point)
        context.space_data.pivot_point = 'CENTER'

        # UV座標を正規化
        self.current_show_normalized_coords = copy.copy(get_show_normalized_coords(context))
        # context.space_data.uv_editor.show_normalized_coords = True
        set_show_normalized_coords(context, True)

        self.tool_settings = context.scene.UVIA_tool_settings  # type: UVIA_ToolSettings
        self.pivot_xy = self.tool_settings.pivot_xy[int(self.direction)]

        _active_obj = context.active_object
        _me = _active_obj.data  # type: bpy.types.Mesh

        # 状態の更新
        bpy.context.edit_object.update_from_editmode()
        # メッシュからBMeshを作成
        self.bm = bmesh.from_edit_mesh(_me)

        if bpy.app.version[0] >= 2 and bpy.app.version[1] >= 73:
            self.bm.verts.ensure_lookup_table()
            self.bm.edges.ensure_lookup_table()
            self.bm.faces.ensure_lookup_table()

        # self.bm.loops.layers.uv.verify();
        self.active_uv_layer = self.bm.loops.layers.uv.active  # type: bmesh.types.BMLayerItem
        self.selected_uv_islands = uv_helpers.get_selected_uv_islands(bm=self.bm, uv_layer=self.active_uv_layer)

        if len(self.selected_uv_islands) > 0:
            print("a")
            self.selected_uv_islands_bound_box = uv_helpers.get_uv_islands_bound_box(self.selected_uv_islands, uv_layer=self.active_uv_layer)
            # print(len(self.selected_uv_islands))
            # print(len(self.selected_uv_islands_bound_box))

            _horizontal_margin = 0
            _vertical_margin = 0
            if self.tool_settings.align_to == '0':
                # 島
                self.target_x_min = min(self.selected_uv_islands_bound_box, key=lambda bound_box: bound_box.x_min).x_min
                self.target_x_max = max(self.selected_uv_islands_bound_box, key=lambda bound_box: bound_box.x_max).x_max
                self.target_x_avg = (self.target_x_min + self.target_x_max) / 2
                self.target_y_min = min(self.selected_uv_islands_bound_box, key=lambda bound_box: bound_box.y_min).y_min
                self.target_y_max = max(self.selected_uv_islands_bound_box, key=lambda bound_box: bound_box.y_max).y_max
                self.target_y_avg = (self.target_y_min + self.target_y_max) / 2
            elif self.tool_settings.align_to == '1':
                # 2Dカーソル
                self.target_x_min = context.space_data.cursor_location[0]
                self.target_x_max = context.space_data.cursor_location[0]
                self.target_x_avg = context.space_data.cursor_location[0]
                self.target_y_min = context.space_data.cursor_location[1]
                self.target_y_max = context.space_data.cursor_location[1]
                self.target_y_avg = context.space_data.cursor_location[1]
            else:
                if context.space_data.image:
                    _horizontal_margin = (1.0 / context.space_data.image.size[0]) * self.tool_settings.margin
                    _vertical_margin = (1.0 / context.space_data.image.size[1]) * self.tool_settings.margin
                else:
                    _horizontal_margin = 0.0009765625 * self.tool_settings.margin
                    _vertical_margin = 0.0009765625 * self.tool_settings.margin

                # 画像
                self.target_x_min = 0.0 + _horizontal_margin
                self.target_x_max = 1.0 - _horizontal_margin
                self.target_x_avg = 0.5
                self.target_y_min = 0.0 + _vertical_margin
                self.target_y_max = 1.0 - _vertical_margin
                self.target_y_avg = 0.5


class UV_OT_uv_island_alignment(UV_OT_uv_island_Base, bpy.types.Operator):
    bl_idname = "uv.uv_island_alignment"
    bl_label = "UV Island Alignment"
    bl_description = "Align selected UV islands"
    bl_options = {'REGISTER', 'UNDO'}

    def __init__(self):
        super(UV_OT_uv_island_alignment, self).__init__()

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        if obj and obj.type == 'MESH' and (obj.mode == 'EDIT'):
            return True
        return False

    def invoke(self, context, event):
        # テクスチャが設定されていないのに、テクスチャが選択された状態のときは島に戻す
        if not context.space_data.image and context.scene.UVIA_tool_settings.align_to == '2':
            context.scene.UVIA_tool_settings.align_to = '0'
        return self.execute(context)

    def execute(self, context):
        super(UV_OT_uv_island_alignment, self).execute(context)
        if len(self.selected_uv_islands) == 0:
            # 設定を元に戻す
            context.space_data.pivot_point = self.current_pivot_point
            set_show_normalized_coords(context, self.current_show_normalized_coords)
            return {'FINISHED'}

        # カーソル位置
        # 親のクラスだと取得できない?
        self.current_cursor_location = context.space_data.cursor_location[0], context.space_data.cursor_location[1]

        _target_x = 0
        _target_y = 0
        _items = zip(self.selected_uv_islands, self.selected_uv_islands_bound_box)
        for uv_island, bound_box in _items:
            bpy.ops.uv.select_all(action='DESELECT')

            for face in uv_island:  # type: bmesh.types.BMFace
                for loop in face.loops:
                    loop[self.active_uv_layer].select = True

            if self.movement_type == 0:
                return
            elif self.movement_type == 1:
                _target_x = self.target_x_min
                _target_y = bound_box.y
            elif self.movement_type == 2:
                _target_x = self.target_x_avg
                _target_y = bound_box.y
            elif self.movement_type == 3:
                _target_x = self.target_x_max
                _target_y = bound_box.y
            elif self.movement_type == 4:
                _target_x = bound_box.x
                _target_y = self.target_y_max
            elif self.movement_type == 5:
                _target_x = bound_box.x
                _target_y = self.target_y_avg
            elif self.movement_type == 6:
                _target_x = bound_box.x
                _target_y = self.target_y_min

            _cursor_location = _target_x - (bound_box.width * self.pivot_xy["x"]), _target_y - (
                        bound_box.height * self.pivot_xy["y"])

            bpy.ops.uv.cursor_set(location=_cursor_location)
            bpy.ops.uv.snap_selected(target='CURSOR_OFFSET')

        # 選択したものを元に戻す
        for uv_island in self.selected_uv_islands:
            for face in uv_island:  # type: bmesh.types.BMFace
                for loop in face.loops:
                    loop[self.active_uv_layer].select = True

        # 設定を元に戻す
        context.space_data.cursor_location = self.current_cursor_location
        context.space_data.pivot_point = self.current_pivot_point
        # context.space_data.uv_editor.show_normalized_coords = self.current_show_normalized_coords
        set_show_normalized_coords(context, self.current_show_normalized_coords)

        return {'FINISHED'}


class UV_OT_uv_island_distribute_spacing(UV_OT_uv_island_Base, bpy.types.Operator):
    bl_idname = "uv.uv_island_distribute_spacing"
    bl_label = "UV Island Distribute Spacing"
    bl_description = "Distribute selected UV islands evenly spaced"
    bl_options = {'REGISTER', 'UNDO'}

    def __init__(self):
        super(UV_OT_uv_island_distribute_spacing, self).__init__()

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        if obj and obj.type == 'MESH' and (obj.mode == 'EDIT'):
            return True
        return False

    def invoke(self, context, event):
        if not context.space_data.image and context.scene.UVIA_tool_settings.align_to == '2':
            context.scene.UVIA_tool_settings.align_to = '0'
        return self.execute(context)

    def execute(self, context):
        super(UV_OT_uv_island_distribute_spacing, self).execute(context)

        if len(self.selected_uv_islands) == 0:
            # 設定を元に戻す
            context.space_data.pivot_point = self.current_pivot_point
            set_show_normalized_coords(context, self.current_show_normalized_coords)
            return {'FINISHED'}

        # 親のクラスだと取得できない?
        self.current_cursor_location = context.space_data.cursor_location[0], context.space_data.cursor_location[1]

        _target_x = 0
        _target_y = 0
        _previous_width = 0
        _previous_height = 0
        _spacing = 0

        if context.space_data.image:
            _spacing = (1.0 / context.space_data.image.size[1]) * self.tool_settings.spacing
        else:
            _spacing = 0.0009765625 * self.tool_settings.spacing

        if self.movement_type == 0:
            return
        elif 0 < self.movement_type < 4:
            _use_reverse = True if self.movement_type == 3 else False
            _target_x = self.target_x_max if self.movement_type == 3 else self.target_x_min
            _items = sorted(zip(self.selected_uv_islands, self.selected_uv_islands_bound_box), key=lambda t: t[1].x,
                            reverse=_use_reverse)
        elif 3 < self.movement_type < 7:
            _use_reverse = True if self.movement_type == 4 else False
            _target_y = self.target_y_max if self.movement_type == 4 else self.target_y_min
            _items = sorted(zip(self.selected_uv_islands, self.selected_uv_islands_bound_box), key=lambda t: t[1].y,
                            reverse=_use_reverse)

        for i, (uv_island, bound_box) in enumerate(_items):

            bpy.ops.uv.select_all(action='DESELECT')

            for face in uv_island:  # type: bmesh.types.BMFace
                for loop in face.loops:
                    loop[self.active_uv_layer].select = True

            if self.movement_type == 0:
                return
            elif self.movement_type == 1:
                _target_x = _target_x + _previous_width
                _target_x = _target_x if i == 0 else _target_x + _spacing
                _target_y = bound_box.y
            elif self.movement_type == 3:
                _target_x = _target_x - _previous_width
                _target_x = _target_x if i == 0 else _target_x - _spacing
                _target_y = bound_box.y
            elif self.movement_type == 4:
                _target_x = bound_box.x
                _target_y = _target_y - _previous_height
                _target_y = _target_y if i == 0 else _target_y - _spacing
            elif self.movement_type == 6:
                _target_x = bound_box.x
                _target_y = _target_y + _previous_height
                _target_y = _target_y if i == 0 else _target_y + _spacing

            _cursor_location = _target_x - (bound_box.width * self.pivot_xy["x"]), _target_y - (
                        bound_box.height * self.pivot_xy["y"])
            bpy.ops.uv.cursor_set(location=_cursor_location)
            bpy.ops.uv.snap_selected(target='CURSOR_OFFSET')

            _previous_width = copy.copy(bound_box.width)
            _previous_height = copy.copy(bound_box.height)

        # 選択したものを元に戻す
        for uv_island in self.selected_uv_islands:
            for face in uv_island:  # type: bmesh.types.BMFace
                for loop in face.loops:
                    loop[self.active_uv_layer].select = True

        # 設定を元に戻す
        context.space_data.cursor_location = self.current_cursor_location
        context.space_data.pivot_point = self.current_pivot_point
        # context.space_data.uv_editor.show_normalized_coords = self.current_show_normalized_coords
        set_show_normalized_coords(context, self.current_show_normalized_coords)
        return {'FINISHED'}


class UV_OT_uv_island_distribute_scaling(UV_OT_uv_island_Base, bpy.types.Operator):
    bl_idname = "uv.uv_island_distribute_scaling"
    bl_label = "UV Island Distribute Within Range"
    bl_description = "Distribute selected UV islands within a range"
    bl_options = {'REGISTER', 'UNDO'}

    def __init__(self):
        super(UV_OT_uv_island_distribute_scaling, self).__init__()

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        if obj and obj.type == 'MESH' and (obj.mode == 'EDIT'):
            return True
        return False

    def invoke(self, context, event):
        if not context.space_data.image and context.scene.UVIA_tool_settings.align_to == '2':
            context.scene.UVIA_tool_settings.align_to = '0'
        return self.execute(context)

    def execute(self, context):
        super(UV_OT_uv_island_distribute_scaling, self).execute(context)

        if len(self.selected_uv_islands) == 0:
            # 設定を元に戻す
            context.space_data.pivot_point = self.current_pivot_point
            set_show_normalized_coords(context, self.current_show_normalized_coords)
            return {'FINISHED'}

        # 親のクラスだと取得できない?
        self.current_cursor_location = context.space_data.cursor_location[0], context.space_data.cursor_location[1]

        _target_x = 0
        _target_y = 0
        _previous_width = 0
        _previous_height = 0
        _spacing = 0
        _scale = 1.0

        if context.space_data.image:
            _spacing = (1.0 / context.space_data.image.size[1]) * self.tool_settings.spacing
        else:
            _spacing = 0.0009765625 * self.tool_settings.spacing

        _max_width = (self.target_x_max - self.target_x_min) - ((len(self.selected_uv_islands) - 1) * _spacing)
        _max_height = (self.target_y_max - self.target_y_min) - ((len(self.selected_uv_islands) - 1) * _spacing)

        if self.movement_type == 0:
            return
        elif 0 < self.movement_type < 4:
            _target_x = self.target_x_min
            _items = sorted(zip(self.selected_uv_islands, self.selected_uv_islands_bound_box), key=lambda t: t[1].x)
            _object_width = sum(map(lambda b: b.width, self.selected_uv_islands_bound_box))
            _scale = _max_width / _object_width
            # print("max_width", _max_width)
            # print("object_width", _object_width)
            # print("_scale", _scale)
        elif 3 < self.movement_type < 7:
            _use_reverse = True if self.movement_type == 4 else False
            _target_y = self.target_y_max if self.movement_type == 4 else self.target_y_min
            _items = sorted(zip(self.selected_uv_islands, self.selected_uv_islands_bound_box), key=lambda t: t[1].y,
                            reverse=_use_reverse)
            _object_height = sum(map(lambda b: b.height, self.selected_uv_islands_bound_box))
            _scale = _max_height / _object_height
            # print("object_height", _object_height)
            # print("max_height", _max_height)
            # print("_scale", _scale)

        bpy.context.space_data.pivot_point = 'CURSOR'

        for i, (uv_island, bound_box) in enumerate(_items):

            bpy.ops.uv.select_all(action='DESELECT')

            for face in uv_island:  # type: bmesh.types.BMFace
                for loop in face.loops:
                    loop[self.active_uv_layer].select = True

            if 0 < self.movement_type < 4:
                _cursor_location = bound_box.x_min, bound_box.y_max
            else:
                _cursor_location = bound_box.x_max, bound_box.y_min

            context.space_data.pivot_point = 'CURSOR'
            bpy.ops.uv.cursor_set(location=_cursor_location)
            # bpy.ops.transform.resize(value=(_scale, _scale, _scale), constraint_axis=(False, False, False),
            #                          constraint_orientation='GLOBAL', mirror=False, proportional='DISABLED',
            #                          proportional_edit_falloff='SMOOTH', proportional_size=1)
            bpy.ops.transform.resize(value=(_scale, _scale, _scale), constraint_axis=(False, False, False),
                                     mirror=False,
                                     proportional_edit_falloff='SMOOTH', proportional_size=1)
            context.space_data.pivot_point = 'CENTER'

            new_bound_box = uv_helpers.get_uv_island_bound_box(uv_island, self.active_uv_layer)

            if self.movement_type == 0:
                return
            elif 0 < self.movement_type < 4:
                _target_x = _target_x if i == 0 else _target_x + _previous_width + _spacing
                _target_y = new_bound_box.y
            elif 3 < self.movement_type < 7:
                _target_x = new_bound_box.x
                _target_y = _target_y if i == 0 else _target_y + _previous_height + _spacing

            _cursor_location = _target_x - (new_bound_box.width * self.pivot_xy["x"]), _target_y - (
                        new_bound_box.height * self.pivot_xy["y"])
            bpy.ops.uv.cursor_set(location=_cursor_location)
            bpy.ops.uv.snap_selected(target='CURSOR_OFFSET')

            _previous_width = copy.copy(new_bound_box.width)
            _previous_height = copy.copy(new_bound_box.height)

        # 選択したものを元に戻す
        for uv_island in self.selected_uv_islands:
            for face in uv_island:  # type: bmesh.types.BMFace
                for loop in face.loops:
                    loop[self.active_uv_layer].select = True

        # 設定を元に戻す
        context.space_data.cursor_location = self.current_cursor_location
        context.space_data.pivot_point = self.current_pivot_point
        # context.space_data.uv_editor.show_normalized_coords = self.current_show_normalized_coords
        set_show_normalized_coords(context, self.current_show_normalized_coords)
        return {'FINISHED'}


@make_annotations
class UV_OT_reset_2d_cursor(bpy.types.Operator):
    bl_idname = "uv.reset_2d_cursor"
    bl_label = "Reset Cursor Position"
    bl_description = "Move 2D cursor in lower left"
    bl_options = {'REGISTER', 'UNDO'}

    current_show_normalized_coords = False

    items = [
        ("0", "Upper Left", "", "", 0),
        ("1", "Up", "", "", 1),
        ("2", "Upper Right", "", "", 2),
        ("3", "Left", "", "", 3),
        ("4", "Center", "", "", 4),
        ("5", "Right", "", "", 5),
        ("6", "Lower Left", "", "", 6),
        ("7", "Bottom", "", "", 7),
        ("8", "Lower Right", "", "", 8)
    ]
    mode = bpy.props.EnumProperty(
        items=items,
        name="Location",
        default="6"
    )

    def execute(self, context):
        # UV座標を正規化
        self.current_show_normalized_coords = copy.copy(get_show_normalized_coords(context))
        # context.space_data.uv_editor.show_normalized_coords = True
        set_show_normalized_coords(context, True)

        x = 1.0
        y = 1.0

        if self.mode == "0":
            bpy.context.space_data.cursor_location = [0, y]
        elif self.mode == "1":
            bpy.context.space_data.cursor_location = [x / 2, y]
        elif self.mode == "2":
            bpy.context.space_data.cursor_location = [x, y]
        elif self.mode == "3":
            bpy.context.space_data.cursor_location = [0, y / 2]
        elif self.mode == "4":
            bpy.context.space_data.cursor_location = [x / 2, y / 2]
        elif self.mode == "5":
            bpy.context.space_data.cursor_location = [x, y / 2]
        elif self.mode == "6":
            bpy.context.space_data.cursor_location = [0, 0]
        elif self.mode == "7":
            bpy.context.space_data.cursor_location = [x / 2, 0]
        elif self.mode == "8":
            bpy.context.space_data.cursor_location = [x, 0]

        set_show_normalized_coords(context, self.current_show_normalized_coords)
        return {'FINISHED'}


class IMAGE_PT_uv_island_aligment(bpy.types.Panel):
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "UV Island Alignment Tool"
    # bl_options = {'DEFAULT_CLOSED'}
    bl_label = "UV Island Alignment Tool"

    # 以下、2.8ではUIが表示されなくなる?
    # bl_context = "mesh_edit"

    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context: bpy.types.Context):
        layout = self.layout

        row = layout.row()
        row.label(text="Align To")

        row = layout.row()
        box = row.box()
        box_column = box.column(align=True)
        box_row = box_column.row(align=True)
        box_row.prop_enum(context.scene.UVIA_tool_settings, "align_to", '1')
        box_row.prop_enum(context.scene.UVIA_tool_settings, "align_to", '0')

        box_row = box_column.row(align=True)
        # テクスチャが設定されていない場合は選択できない。
        box_row.enabled = True if context.space_data.image else False
        box_row.prop_enum(context.scene.UVIA_tool_settings, "align_to", '2')

        box_row = box_row.row(align=True)
        box_row.active = True if context.scene.UVIA_tool_settings.align_to == '2' else False
        box_row.prop(context.scene.UVIA_tool_settings, "margin", text="Margin")

        row = layout.row()
        row.label(text="Align")

        row = layout.row()
        box_column = row.box()

        # box_column = box_column.split(percentage=0.5)
        box_column = get_split_percentage(box_column, 0.5)

        # 垂直方向に整列
        box_row = box_column.row(align=True)
        box_row.operator_context = 'INVOKE_DEFAULT'
        op = box_row.operator(UV_OT_uv_island_alignment.bl_idname, text="Left")  # type: UV_OT_uv_island_alignment
        op.direction = 3
        op.movement_type = 1
        op = box_row.operator(UV_OT_uv_island_alignment.bl_idname, text="Center")  # type: UV_OT_uv_island_alignment
        op.direction = 4
        op.movement_type = 2
        op = box_row.operator(UV_OT_uv_island_alignment.bl_idname, text="Right")  # type: UV_OT_uv_island_alignment
        op.direction = 5
        op.movement_type = 3

        # 水平方向に整列
        box_row = box_column.row(align=True)
        # box_row.enabled = False if context.scene.UVIA_tool_settings.align_to == '1' else True
        op = box_row.operator(UV_OT_uv_island_alignment.bl_idname, text="Top")  # type: UV_OT_uv_island_alignment
        op.direction = 1
        op.movement_type = 4
        op = box_row.operator(UV_OT_uv_island_alignment.bl_idname, text="Center")  # type: UV_OT_uv_island_alignment
        op.direction = 4
        op.movement_type = 5
        # box_row.enabled = False if context.scene.UVIA_tool_settings.align_to == '1' else True
        op = box_row.operator(UV_OT_uv_island_alignment.bl_idname, text="Bottom")  # type: UV_OT_uv_island_alignment
        op.direction = 7
        op.movement_type = 6

        row = layout.row()
        row.label(text="Distribute Spacing")

        row = layout.row()
        box_column = row.box()

        box_row = box_column.row()
        box_row.prop(context.scene.UVIA_tool_settings, "spacing", text="Spacing")

        # box_column = box_column.split(percentage=0.5)
        box_column = get_split_percentage(box_column, 0.5)

        # 水平方向に等間隔に分布
        box_row = box_column.row(align=True)
        op = box_row.operator(UV_OT_uv_island_distribute_spacing.bl_idname,
                              text="Left")  # type: UV_OT_uv_island_distribute_spacing
        op.direction = 3
        op.movement_type = 1

        op = box_row.operator(UV_OT_uv_island_distribute_spacing.bl_idname,
                              text="Right")  # type: UV_OT_uv_island_distribute_spacing
        op.direction = 5
        op.movement_type = 3

        # 垂直方向に等間隔に分布
        box_row = box_column.row(align=True)
        op = box_row.operator(UV_OT_uv_island_distribute_spacing.bl_idname,
                              text="Top")  # type: UV_OT_uv_island_distribute_spacing
        op.direction = 1
        op.movement_type = 4

        op = box_row.operator(UV_OT_uv_island_distribute_spacing.bl_idname,
                              text="Bottom")  # type: UV_OT_uv_island_distribute_spacing
        op.direction = 7
        op.movement_type = 6

        row = layout.row()
        row.label(text="Distribute Within Range")

        row = layout.row()
        box_column = row.box()

        box_row = box_column.row()
        box_row.prop(context.scene.UVIA_tool_settings, "spacing", text="Spacing")

        box_row = box_column.row(align=True)
        box_row.enabled = False if context.scene.UVIA_tool_settings.align_to == '1' else True
        op = box_row.operator(UV_OT_uv_island_distribute_scaling.bl_idname, text="Horizontal Direction")
        op.direction = 3
        op.movement_type = 1

        op = box_row.operator(UV_OT_uv_island_distribute_scaling.bl_idname, text="Vertical Direction")
        op.direction = 7
        op.movement_type = 6

        box_column = layout.column()
        box_column.prop(context.space_data, "cursor_location", text="Cursor Location")

        row = layout.row()
        row.label(text="Move 2D Cursor")

        column = layout.column(align=True)
        row = column.row(align=True)
        op = row.operator(UV_OT_reset_2d_cursor.bl_idname, text="Upper Left")
        op.mode = "0"
        op = row.operator(UV_OT_reset_2d_cursor.bl_idname, text="Top")
        op.mode = "1"
        op = row.operator(UV_OT_reset_2d_cursor.bl_idname, text="Upper Right")
        op.mode = "2"
        row = column.row(align=True)
        op = row.operator(UV_OT_reset_2d_cursor.bl_idname, text="Left")
        op.mode = "3"
        op = row.operator(UV_OT_reset_2d_cursor.bl_idname, text="Center")
        op.mode = "4"
        op = row.operator(UV_OT_reset_2d_cursor.bl_idname, text="Right")
        op.mode = "5"
        row = column.row(align=True)
        op = row.operator(UV_OT_reset_2d_cursor.bl_idname, text="Lower Left")
        op.mode = "6"
        op = row.operator(UV_OT_reset_2d_cursor.bl_idname, text="Bottom")
        op.mode = "7"
        op = row.operator(UV_OT_reset_2d_cursor.bl_idname, text="Lower Right")
        op.mode = "8"

        row = column.row(align=True)

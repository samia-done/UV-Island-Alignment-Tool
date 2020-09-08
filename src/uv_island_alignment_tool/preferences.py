# Copyright (c) 2020 Samia

import bpy
from bpy.types import AddonPreferences
from .utils.addon_updater import AddonUpdaterManager
from . import updater
from .utils.bl_anotations import make_annotations


def get_update_candidate_branches(_, __):
    manager = AddonUpdaterManager.get_instance()
    if not manager.candidate_checked():
        return []

    return [(name, name, "") for name in manager.get_candidate_branch_names()]


@make_annotations
class UVIA_AddonPreferences(AddonPreferences):
    bl_idname = __package__

    # for add-on updater
    updater_branch_to_update = bpy.props.EnumProperty(
        name="branch",
        description="Target branch to update add-on",
        items=get_update_candidate_branches
    )

    def __init__(self):
        super(AddonPreferences, self).__init__()

    def draw(self, context):
        layout = self.layout
        layout.label(text="UVIA Settings")
        updater.draw_updater_ui(self)

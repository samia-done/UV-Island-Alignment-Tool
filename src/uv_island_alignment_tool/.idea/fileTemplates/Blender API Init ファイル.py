# Copyright (c) ${YEAR} Samia
import bpy

bl_info = {
    "name": "",
    "author": "Samia",
    "version": (1, 1),
    "blender": (2, 80, 0),
    "location": "",
    "description": "",
    "warning": "",
    "support": "TESTING",
    "wiki_url": "",
    "tracker_url": "",
    "category": ""
}

classes = (

)


# def menu_func(self, context):
#     self.layout.separator()


# def register_menu():


# def unregister_menu():


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    # register_menu()


def unregister():
    # unregister_menu()

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()

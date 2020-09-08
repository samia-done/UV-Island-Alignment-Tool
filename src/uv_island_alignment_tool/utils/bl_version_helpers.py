# Copyright (c) 2020 Samia
import bpy


def get_bl_version():
    return bpy.app.version[0], bpy.app.version[1]


def get_bl_major_version():
    return bpy.app.version[0]


def get_bl_minor_version():
    return bpy.app.version[1]


def has_bl_version(major, minor):
    if bpy.app.version[0] == major and bpy.app.version[1] == minor:
        return True
    return False


def has_bl_major_version(major):
    if bpy.app.version[0] == major:
        return True
    return False


def has_bl_minor_version(minor):
    if bpy.app.version[0] == minor:
        return True
    return False

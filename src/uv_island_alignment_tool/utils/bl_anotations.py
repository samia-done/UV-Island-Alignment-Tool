# Copyright (c) 2020 Samia

from .bl_version_helpers import has_bl_major_version, get_bl_minor_version


def make_annotations(cls):
    if has_bl_major_version(2) and get_bl_minor_version() < 80:
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

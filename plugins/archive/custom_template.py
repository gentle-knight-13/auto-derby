from doctest import UnexpectedException
import auto_derby
import os
from typing import Dict, Text
import pathlib
from PIL.Image import Image
from PIL.Image import open as open_image
from auto_derby import app, clients
from auto_derby import template
from auto_derby.services.log import Level

_LOADED_TEMPLATES: Dict[Text, Image] = {}

custom_template_path = os.getenv(
    "AUTO_DERBY_CUSTOM_TEMPLATE_PATH", "data/custom_template/"
)
custom_template_group = os.getenv(
    "AUTO_DERBY_CUSTOM_TEMPLATE_GROUP", ""
)
load_paths = []


def _append_exists(path: pathlib.Path) -> None:
    if path.is_dir():
        load_paths.append(path)


def _create_paths() -> None:
    client = app.device
    resolution = "{:.0f}x{:.0f}".format(client.width(), client.height())
    client_name = None
    if custom_template_group:
        _append_exists(pathlib.Path(custom_template_path) / custom_template_group)
    if type(client._c).__str__ is not object.__str__:
        client_name = str(client)
    elif isinstance(client._c, clients.DMMClient):
        client_name = "dmm"
    elif isinstance(client._c, clients.ADBClient):
        client_name = "adb"
    if client_name:
        _append_exists(
            pathlib.Path(custom_template_path) / "{}_{}".format(client_name, resolution)
        )
        _append_exists(pathlib.Path(custom_template_path) / client_name)
    _append_exists(pathlib.Path(custom_template_path) / resolution)
    _append_exists(pathlib.Path(custom_template_path) / "global")
    _append_exists(pathlib.Path(template.__file__).parent / "templates")


def custom_load(name: Text) -> Image:
    if not load_paths:
        _create_paths()
    if name not in _LOADED_TEMPLATES:
        for i, path in enumerate(load_paths):
            try:
                img = open_image(path / name)
                app.log.text(
                    "custom load: %s (%s)" % (name, path.stem), level=Level.DEBUG
                )
                break
            except Exception as e:
                if i < len(load_paths) - 1:
                    continue
                else:
                    raise e
        _LOADED_TEMPLATES[name] = img
    return _LOADED_TEMPLATES[name]


class Plugin(auto_derby.Plugin):
    """Replace templates under different 16:9 resolution"""

    def install(self) -> None:
        template.load = custom_load
        pass


auto_derby.plugin.register(__name__, Plugin())

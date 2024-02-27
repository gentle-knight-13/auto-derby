import configparser
import auto_derby
import os
from typing import Dict, Iterator, List, Text, Tuple, Union
import pathlib
from PIL.Image import Image
from PIL.Image import open as open_image
from auto_derby import app, template
from auto_derby.services.log import Level

_LOADED_TEMPLATES: Dict[Text, Image] = {}
_LOADED_EXTRA_NAMES: Dict[Text, List[template.Specification]] = {}

custom_config_path = os.getenv(
    "AUTO_DERBY_PLUGIN_CONFIG_PATH", "data/plugin_config.ini"
)
custom_template_path = os.getenv(
    "AUTO_DERBY_CUSTOM_TEMPLATE_PATH", "data/custom_template/"
)
custom_template_names = os.getenv("AUTO_DERBY_CUSTOM_TEMPLATE_NAMES", "")
load_paths: List[pathlib.Path] = []


def _append_exists(path: pathlib.Path) -> None:
    if path.is_dir():
        load_paths.append(path)
        app.log.text("custom load path: %s" % (path.stem), level=Level.DEBUG)
    else:
        app.log.text("custom load path not exist: %s" % (path.stem), level=Level.WARN)


def _create_paths() -> None:
    config = configparser.ConfigParser()
    config.read(custom_config_path)
    if custom_template_path:
        config["custom_templates"]["path"] = custom_template_path
    if custom_template_names:
        config["custom_templates"]["names"] = custom_template_names
    path = pathlib.Path(config["custom_templates"]["path"])
    names = config["custom_templates"]["names"].split(",")
    for name in names:
        _append_exists(path / name.strip())
    _append_exists(pathlib.Path(template.__file__).parent / "templates")
    with open(custom_config_path, "w") as config_file:
        config.write(config_file)


def custom_load(tmpl: Union[Text, template.Specification]) -> Image:
    if isinstance(tmpl, str):
        name = tmpl
    else:
        name = tmpl.name
    if name not in _LOADED_TEMPLATES:
        for i, path in enumerate(load_paths):
            try:
                img = open_image(path / name)
                app.log.text(
                    "custom load: %s (%s)" % (name, path.stem) #, level=Level.DEBUG
                )
                break
            except Exception as e:
                if i < len(load_paths) - 1:
                    continue
                else:
                    raise e
        _LOADED_TEMPLATES[name] = img
    return _LOADED_TEMPLATES[name]

_FileNotFoundError = getattr(__builtins__,'FileNotFoundError', IOError)
def _load_extra(tmpl: Union[Text, template.Specification]):
    threshold = None
    if isinstance(tmpl, str):
        name = tmpl
    else:
        name, threshold = tmpl.name, tmpl.threshold
    if threshold: 
        _spec = lambda name: template.Specification(name, threshold=threshold)
    else:
        _spec = lambda name: template.Specification(name)
    if name not in _LOADED_EXTRA_NAMES:
        _LOADED_EXTRA_NAMES[name] = [template.Specification.from_input(tmpl)]
        for i, path in enumerate(load_paths):
            extra_file_path = path / (name + ".extra")
            if extra_file_path.exists():
                try:
                    file = open(extra_file_path, "r")
                    _LOADED_EXTRA_NAMES[name].extend(
                        [_spec(i.strip()) for i in file.readlines()]
                    )
                    app.log.text(
                        "extra load: %s (%s)" % (name, _LOADED_EXTRA_NAMES[name]), 
                        level=Level.DEBUG
                    )
                    break
                except _FileNotFoundError as e:
                    if i < len(load_paths) - 1:
                        continue
                    else:
                        raise e
    return _LOADED_EXTRA_NAMES[name]


def extra_match(
    img: Image, *tmpl: Union[Text, template.Specification]
) -> Iterator[Tuple[template.Specification, Tuple[int, int]]]:
    match_count = 0
    for k in tmpl:
        tmpl_spec = template.Specification.from_input(k)
        for i in _load_extra(k):
            for j in template._match_one(img, i):
                match_count += 1
                yield (tmpl_spec,) + j[1:]
    if match_count == 0:
        app.log.text(f"no match: tmpl={tmpl}")


# original_spec = template.Specification


# class Specification(original_spec):
#     def __init__(self, *args, threshold: float = 0.8, **kwargs):
#         super().__init__(*args, threshold, **kwargs)
#         self.custom_name = None

    # def __str__(self):
    #     return (
    #         f"tmpl<{self.custom_name}:{self.name}+{self.pos}>"
    #         if self.custom_name and self.pos
    #         else f"tmpl<{self.custom_name}:{self.name}>"
    #         if self.custom_name and not self.pos
    #         else f"tmpl<{self.name}+{self.pos}>"
    #         if self.pos
    #         else f"tmpl<{self.name}>"
    #     )


class Plugin(auto_derby.Plugin):
    """Replace templates under different 16:9 resolution"""

    def install(self) -> None:
        template.load = custom_load
        template.match = extra_match
        # template.Specification = Specification
        _create_paths()


auto_derby.plugin.register(__name__, Plugin())

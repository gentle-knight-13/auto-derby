import auto_derby
import configparser
import re
import os
from adb_shell.adb_device import AdbDeviceTcp
from auto_derby import app
from auto_derby.clients import ADBClient
from typing import Text, Tuple

from auto_derby.services.log import Level

custom_config_path = os.getenv(
    "AUTO_DERBY_PLUGIN_CONFIG_PATH", "data/plugin_config.ini"
)


def _read_address(address: Text) -> Tuple:
    config = configparser.ConfigParser()
    config.read_dict(
        {
            "bluestacks": {
                "hostname": "127.0.0.1",
                "instance": "Nougat64",
                "conf_path": "C:\\ProgramData\\BlueStacks_nxt\\bluestacks.conf",
                "prefix": "",
            },
        }
    )
    config.read(custom_config_path)

    # Overide config with environment value
    if address and address.count(":") >= 3 and address.count(":") <= 4:
        if address.count(":") == 4:
            _, prefix, hostname, instance, conf_path = address.split(":", 4)
            if len(prefix) > 0:
                config["bluestacks"]["prefix"] = prefix + ":"
        else:
            _, hostname, instance, conf_path = address.split(":", 3)
        if len(hostname) != 0:
            config["bluestacks"]["hostname"] = hostname
        if len(instance) != 0:
            config["bluestacks"]["instance"] = instance
        if len(conf_path) != 0:
            config["bluestacks"]["conf_path"] = conf_path
    else:
        app.log.text(
            "Environment variable is not used: %s" % address, level=Level.DEBUG
        )

    # Search port in the config of the BlueStacks plugin
    port = 5555
    with open(config["bluestacks"]["conf_path"], encoding="utf-8") as conf:
        for line in conf:
            re_match = re.match(
                'bst\.instance\.%s\.status\.adb_port="(?P<port>\d{2,5})"'
                % config["bluestacks"]["instance"],
                line,
            )
            if re_match != None:
                port = re_match.group("port")
                break

    # Save in config
    with open(custom_config_path, "w") as config_file:
        config.write(config_file)

    assert port, "Invalid port: Invalid BlueStacks config path: %s" % conf_path

    app.log.text(
        "BlueStacks: %s%s:%s"
        % (config["bluestacks"]["prefix"],config["bluestacks"]["hostname"], port)
    )
    return "%s%s:%s" % (
        config["bluestacks"]["prefix"],
        config["bluestacks"]["hostname"],
        port,
    )


class Plugin(auto_derby.Plugin):
    """Connect to BlueStacks by search its port in the config file.\nActivated with bs:{hostname}:{instance name}:{config file path} in ADB address\nMinimal value of address field for activation would be \"bs:::\"\nIt accepts parameters with priority as below:\n1. AUTO_DERBY_ADB_ADDRESS with format\n2. Config file data/plugin_config.ini (Auto created with previously used value)\n3. Default values with common BlusStacks setup\nDefault value would be \"bs:127.0.0.1:Nougat64:C:\\ProgramData\\BlueStacks_nxt\\bluestacks.conf\"\nThere also can be a prefix after \"bs:\", like \"bs:<prefix>:<hostname>:<instance>:<config file>\""""

    def install(self) -> None:
        if auto_derby.config.ADB_ADDRESS.lower().startswith("bs:"):
            auto_derby.config.ADB_ADDRESS = _read_address(auto_derby.config.ADB_ADDRESS)


auto_derby.plugin.register(__name__, Plugin())

from __future__ import annotations

import auto_derby

class Plugin(auto_derby.Plugin):
    """Disable web log."""

    def install(self) -> None:
        auto_derby.config.web_log_disabled = True

auto_derby.plugin.register(__name__, Plugin())

from __future__ import annotations

from mnemosyne.ui_css.base import BASE_CSS
from mnemosyne.ui_css.density_and_buttons import DENSITY_AND_BUTTONS_CSS
from mnemosyne.ui_css.interaction_repairs import INTERACTION_REPAIRS_CSS
from mnemosyne.ui_css.stitch_foundation import STITCH_FOUNDATION_CSS
from mnemosyne.ui_css.workspace_modules import WORKSPACE_MODULES_CSS

APP_CSS = "".join([
    BASE_CSS,
    STITCH_FOUNDATION_CSS,
    WORKSPACE_MODULES_CSS,
    DENSITY_AND_BUTTONS_CSS,
    INTERACTION_REPAIRS_CSS,
])

__all__ = ["APP_CSS"]

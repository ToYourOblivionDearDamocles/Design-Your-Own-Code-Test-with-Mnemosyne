"""HTML section modules for the single-page UI."""

from mnemosyne.ui_html.practice_frame import TOPBAR_AND_PRACTICE_FRAME
from mnemosyne.ui_html.problem_catalog import CATALOG_VIEW
from mnemosyne.ui_html.create_view import CREATE_AGENT_VIEW
from mnemosyne.ui_html.practice_code import PRACTICE_CODE_VIEW
from mnemosyne.ui_html.manage_view import MANAGE_VIEW
from mnemosyne.ui_html.secondary_views import SECONDARY_VIEWS_AND_BODY_CLOSE

APP_BODY = "".join([
    TOPBAR_AND_PRACTICE_FRAME,
    CATALOG_VIEW,
    CREATE_AGENT_VIEW,
    PRACTICE_CODE_VIEW,
    MANAGE_VIEW,
    SECONDARY_VIEWS_AND_BODY_CLOSE,
])

__all__ = [
    "APP_BODY",
    "TOPBAR_AND_PRACTICE_FRAME",
    "CATALOG_VIEW",
    "CREATE_AGENT_VIEW",
    "PRACTICE_CODE_VIEW",
    "MANAGE_VIEW",
    "SECONDARY_VIEWS_AND_BODY_CLOSE",
]

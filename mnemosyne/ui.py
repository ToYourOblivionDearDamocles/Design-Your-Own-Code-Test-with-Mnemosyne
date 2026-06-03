from __future__ import annotations

from mnemosyne.ui_scripts import APP_SCRIPT
from mnemosyne.ui_html import APP_BODY
from mnemosyne.ui_css import APP_CSS as APP_STYLES

"""Assemble the Mnemosyne single-page app.

FastAPI and tests import APP_HTML from this module, so this stays as the stable public UI entry point.
Edit visual styling in mnemosyne/ui_css/, page markup in mnemosyne/ui_html/, browser behavior in mnemosyne/ui_js/, and copy in mnemosyne/ui_copy/ui_text.json. The top-level ui_*.py files are assembly wrappers.
"""

APP_HEAD_PREFIX = r"""
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Mnemosyne</title>
  <script>
    window.MathJax = {
      tex: {
        inlineMath: [['\\(', '\\)']],
        displayMath: [['\\[', '\\]']],
        processEscapes: true
      },
      options: {
        skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code']
      },
      startup: {
        typeset: false
      }
    };
  </script>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/codemirror@5/lib/codemirror.css" />
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/codemirror@5/theme/material-darker.css" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&family=Literata:opsz,wght@7..72,500;7..72,600;7..72,700&display=swap" rel="stylesheet" />
  <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet" />
  <script defer src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script>
  <script defer src="https://cdn.jsdelivr.net/npm/codemirror@5/lib/codemirror.js"></script>
  <script defer src="https://cdn.jsdelivr.net/npm/codemirror@5/mode/python/python.js"></script>
  <script defer src="https://cdn.jsdelivr.net/npm/codemirror@5/addon/edit/matchbrackets.js"></script>
  <script defer src="https://cdn.jsdelivr.net/npm/codemirror@5/addon/edit/closebrackets.js"></script>
  <style>
"""

APP_HEAD_SUFFIX = r"""  </style>
</head>
"""

APP_HTML = (
    APP_HEAD_PREFIX
    + APP_STYLES
    + APP_HEAD_SUFFIX
    + APP_BODY
    + "\n  <script>\n"
    + APP_SCRIPT
    + "\n  </script>\n</body>\n</html>"
)

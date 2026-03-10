"""
Path setup helper — must be imported before any multiagent_classroom imports.

Adds the project root to sys.path so that scripts inside manual_coder/
can import from multiagent_classroom regardless of the working directory.
"""

import sys
import pathlib

_PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

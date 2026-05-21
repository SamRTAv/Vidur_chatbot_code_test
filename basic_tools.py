"""
basic_tools.py — backward-compatibility shim.

The implementation has been split into the `wellbeing/` package for clarity.
This file simply re-exports the same public surface so anything that imports
from `basic_tools` (or runs `python basic_tools.py`) still works unchanged.

Run:
    python basic_tools.py                         # uses data3.json by default
    python basic_tools.py --data path/to/file.json
    python basic_tools.py --quiet                 # hide tool call logs

For new code, prefer importing directly from `wellbeing`:
    from wellbeing import TOOLS, dispatch_tool, run_agentic_turn, SYSTEM_PROMPT
"""

from wellbeing import *  # re-export the full public API
from wellbeing.agent import main


if __name__ == "__main__":
    main()

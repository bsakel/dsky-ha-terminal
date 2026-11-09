# Generator scripts

These scripts produced the boards. You only need them to regenerate the boards from scratch; normal edits can be made in KiCad directly. They need Python 3 with numpy and matplotlib.

```
python3 status_board.py out       # place + autoroute the status board  -> out/status_board.pkl
python3 keyboard_board.py out     # place + autoroute the keyboard board -> out/keyboard_board.pkl
python3 build_all.py <repo_root>  # KiCad projects, schematics, panel, JLCPCB BOM/CPL (run from this folder, reads out/*.pkl)
python3 diy.py <repo_root>        # hand-wired schematic + diagram
```

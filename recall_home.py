from recall_next_mine import *

import os
main_script = os.path.basename(__file__)


def recall_home():
    return recall(runebook, 0, runes[0])


if Misc.ScriptStatus(main_script) or Misc.ScriptStatus('recall_home.py'):
    for _ in range(50):
        Misc.Pause(100)
        if Misc.ReadSharedValue('ready_to_recall'):
            break
    recall_home()

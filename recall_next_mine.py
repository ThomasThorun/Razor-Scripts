from runebook import *

import os
main_script = os.path.basename(__file__)


def recall_next_mine():
    global mine_num
    runes_idx = [idx for idx, rune in enumerate(runes) if "mining" in rune.lower()]
    rune_pos = runes_idx[mine_num]
    print("rune pos", rune_pos)
    for i in range(5):
        if runebook:
            recall_result = recall(runebook, rune_pos, runes[rune_pos])
            if recall_result:
                mine_num = (mine_num + 1) % len(runes_idx)
                Misc.SetSharedValue('mine_num', mine_num)
                return True
    return False


mine_num = int(Misc.ReadSharedValue('mine_num'))
runebook, runes = get_runebook("Mining")

if Misc.ScriptStatus(main_script) or Misc.ScriptStatus('recall_next_mine.py'):
    for _ in range(50):
        Misc.Pause(100)
        if Misc.ReadSharedValue('ready_to_recall'):
            break
    recall_next_mine()

from AutoComplete import *
import time

tgt = Target.PromptGroundTarget("selecione o ground", 38)

stcs = Statics.GetStaticsTileInfo(tgt.X,tgt.Y,Player.Map)

for s in stcs:
    print(s)
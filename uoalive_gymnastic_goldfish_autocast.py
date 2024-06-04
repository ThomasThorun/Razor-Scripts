cast_divine_stam = 88  # change this to higher value if you want to cast Divine Fury more often
from AutoComplete import *

defs = {'recovery_time': 1600 - 250 * Player.FasterCastRecovery,
        'cw_timeout': max([750, 1000 - 250 * Player.FasterCasting]),
        'df_timeout': max([750, 1500 - 250 * Player.FasterCasting])}


def cast_chivalry(spell, timeout):
    if not Player.BuffsExist(spell):
        Journal.Clear()
        Spells.CastChivalry(spell, Player.Serial, 1000)
        for _ in range(int(timeout/10)):
            Misc.Pause(10)
            if Journal.Search(Player.Name + ": The spell fizzles.") or Player.BuffsExist(spell):
                break
            if Journal.SearchByType("You have not yet recovered from casting a spell.", "System"):
                Misc.Pause(200)
                break
        Misc.Pause(defs['recovery_time'])


def auto_cast_chivalry():
    while True:
        if Player.IsGhost:
            while Player.IsGhost or Player.AR <= 10:
                Misc.Pause(1000)
        cast_chivalry("Consecrate Weapon", defs['cw_timeout'])
        if Player.Stam <= cast_divine_stam and Player.BuffsExist("Consecrate Weapon"):
            cast_chivalry("Divine Fury", defs['df_timeout'])

auto_cast_chivalry()

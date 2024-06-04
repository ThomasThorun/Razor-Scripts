from AutoComplete import *


def in_cap(skill):
    if Player.GetSkillValue(skill) >= Player.GetSkillCap(skill):
        Misc.SendMessage(skill + " is in it's cap. Finishing.", 68)
        return True
    return False


def meditate(start_mana=40):
    if Player.Mana < start_mana:
        while Player.Mana != Player.ManaMax:
            Player.UseSkill("Meditation")
            Misc.Pause(1000)
            while Player.BuffsExist('Meditation') and Player.Mana != Player.ManaMax:
                Misc.Pause(1000)


def wait_spell_journal(spell, timeout):
    for _ in range(int(timeout / 10)):
        Misc.Pause(10)
        if Journal.Search(Player.Name + ": The spell fizzles.") or Player.BuffsExist(spell):
            break
        if Journal.SearchByType("You have not yet recovered from casting a spell.", "System"):
            Misc.Pause(200)
            break


def hp_recovery():
    if Player.GetSkillValue('Magery') >= 24:
        while not Player.IsGhost and Player.Hits <= 80:
            Spells.Cast('Greater Heal', Player.Serial)
            Misc.Pause(4000)
    if Player.GetSkillValue('Mysticism') >= 60:
        while not Player.IsGhost and Player.Hits <= 80:
            Spells.CastMysticism('Cleansing Winds', Player.Serial)
            Misc.Pause(4000)


def mysticism():
    spell = ''
    while not Player.IsGhost and not in_cap('Mysticism'):
        meditate()
        hp_recovery()
        if 0 <= Player.GetSkillValue('Mysticism') < 40:
            spell = 'Sleep'
        if 40 <= Player.GetSkillValue('Mysticism') < 60:
            spell = 'Stone Form'
        if 60 <= Player.GetSkillValue('Mysticism') < 80:
            spell = 'Cleansing Winds'
        if 80 <= Player.GetSkillValue('Mysticism') < 95:
            spell = 'Hail Storm'
        if 95 <= Player.GetSkillValue('Mysticism') <= 120:
            spell = 'Nether Cyclone'
        Spells.CastMysticism(spell, Player.Serial)
        wait_spell_journal(spell, 4500)
        Misc.Pause(500)


mysticism()
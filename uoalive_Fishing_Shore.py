from System.Collections.Generic import List
from System import Int32
from datetime import datetime, timedelta
import sys
from AutoComplete import *


utils = {'fishing_pole': 0x0DC0, 'fish_steak': 0x097A, 'white_pearl': 0x3196, 'fish_mess': 0x0DD6,
         'delicate scales': 0x573A,
         'cut_weapon': [0x2D20, 0x2D2F, 0x0EC3, 0x0EC4, 0x0F45, 0x0F47, 0x0F49, 0x0F52, 0x0F4B, 0x0F4D, 0x0F5E, 0x13B6,
                        0x13B9, 0x13F6, 0x1401, 0x143E, 0x1443, 0x26BA, 0x26BB, 0x26BD, 0x26C0, 0x26C1]}

trash = {'boots': 0x170B, 'thigh boots': 0x1711, 'sandals': 0x170D, 'shoes': 0x170F}

fishs = {"fish": [0x09CC, 0x09CD, 0x09CE, 0x09CF], "yellowtail barracuda": [0x44C3, 0x44C4],
         "blue marlin": [0x4304, 0x4305], "sunfish": [0x4306, 0x4307], "green catfish": [0x44C5, 0x44C6],
         "yellow perch": [0x4302, 0x4303]}

fish_id_list = [f for fish in fishs.values() for f in fish]

journal_messages = {'success': "You pull out ",
                    'pearl': "You have found ",
                    'big_fish': "Your fishing pole bends as you pull a big fish from the depths!",
                    'enemy': "Uh oh! That doesn't look like a fish!",
                    'fail': "You fish a while, but fail to catch anything.",
                    'wait': "You must wait to perform another action.",
                    'already': "You are already fishing.",
                    'empty': "The fish don't seem to be biting here.",
                    'far_away': "You need to be closer to the water to fish!",
                    'target': "Target cannot be seen."}

trash_bag: Item
cut_weapon: Item


def dist(pos1, pos2):
    if len(pos1) > 2 and len(pos2) > 2 and pos1[2] != pos2[2]:
        return 10000
    return max(abs(pos1[0] - pos2[0]), abs(pos1[1] - pos2[1]))


def refresh_ignore(respawn_time=2400):
    _new_list = []
    for _ignored in ignored_tile_list:
        if timedelta.total_seconds(datetime.now() - _ignored['time']) < respawn_time:
            _new_list.append(_ignored)
    return _new_list


def tile_ignored(tile, radius=0):
    for _ignored in ignored_tile_list:
        if dist((_ignored['tile']['X'], _ignored['tile']['Y'], _ignored['tile']['World']), tile) <= radius:
            return True
    return False


def uoalive_check_save():
    if Journal.Search("The world is saving, please wait."):
        Misc.Pause(3000)
        Journal.Clear()


def error(_msg, finish=False):
    Misc.SendMessage(_msg, 28)
    if finish:
        sys.exit()


def get_shared(name):
    return Items.FindBySerial(Misc.ReadSharedValue(name))


def set_shared(name, _msg):
    Misc.SendMessage(_msg, 68)
    item = Items.FindBySerial(Target.PromptTarget(""))
    if item:
        Misc.SetSharedValue(name, item.Serial)
    return item


def get_bag():
    bag = get_shared('trash_bag')
    while not bag or not bag.IsContainer or bag == Player.Backpack:
        bag = set_shared('trash_bag', "Target a bag for trash")
        if bag and bag.IsContainer:
            break
        error("Is that a bag?")
    return bag


def get_cut_weapon():
    for weapon_id in utils['cut_weapon']:
        weapon = Items.FindByID(weapon_id, -1, Player.Backpack.Serial)
        if weapon:
            Misc.SetSharedValue('cut_weapon', weapon.Serial)
            return weapon
    weapon = get_shared('cut_weapon')
    if weapon:
        return weapon
    return set_shared('cut_weapon', "Choose a weapon to cut fish into steaks:")


def get_fish_qtd():
    fish_qtd = 0
    for fish_id in fish_id_list:
        fish_qtd += Items.BackpackCount(fish_id, -1)
    return fish_qtd


def check_cut(max_fish=10):
    if get_fish_qtd() >= max_fish or Player.Weight >= Player.MaxWeight - 100:
        cut()
        handle_trash()
        Misc.Pause(1000)
        Misc.SendMessage("Restarting to fish", 68)


def check_hp():
    if Player.Hits < Player.HitsMax - 10:
        error("An enemy appeared. Finishing, as you prepare for battle.", True)


def wait_journal(timeout):
    for _ in range(int(timeout / 100)):
        Misc.Pause(100)
        for message in journal_messages:
            if Journal.Search(journal_messages[message]):
                return message
    Target.Cancel()
    return ''


def answer(message):
    if message in ['wait', 'already']:
        Misc.Pause(2000)
        return 'continue'
    if not message or message in ['empty', 'far_away', 'target']:
        return 'change'
    if message == 'enemy':
        error("An enemy appeared. Finishing, as you prepare for battle.", True)
    return 'continue'


def cut():
    no_steak = 0
    Misc.SendMessage("Cutting fish into steaks", 53)
    for fish_id in fish_id_list:
        while not Player.IsGhost:
            fish = Items.FindByID(fish_id, -1, Player.Backpack.Serial)
            if not fish:
                break
            Misc.Pause(300)
            Items.UseItem(cut_weapon)
            Target.WaitForTarget(2500, False)
            Target.TargetExecute(fish)
            Misc.Pause(300)
            uoalive_check_save()
            if not Items.FindByID(utils['fish_steak'], -1, Player.Backpack.Serial):
                no_steak += 1
            if no_steak > 2:
                error("Failed to cut fish with this weapon")
                set_shared('cut_weapon', "Choose a weapon to cut fish into steaks:")


def handle_trash():
    if trash_bag:
        Misc.SendMessage("Moving trash.", 53)
        Journal.Clear()
        for item_id in List[Int32](trash.values()):
            while not Player.IsGhost:
                item = Items.FindByID(item_id, -1, Player.Backpack.Serial)
                if not item or Journal.SearchByType('cannot hold', 'System'):
                    break
                Items.Move(item, trash_bag, 0)
                Misc.Pause(600)

    while not Player.IsGhost:
        mess = Items.FindByID(utils['fish_mess'], -1, Player.Backpack.Serial)
        if not mess:
            break
        Items.UseItem(mess)
        Misc.Pause(300)


def use_id(item_id):
    Target.Cancel()
    item = Player.GetItemOnLayer('RightHand')
    if not item or item.ItemID != int(item_id):
        item = Items.FindByID(int(item_id), -1, Player.Backpack.Serial)
        if not item or not item.ItemID == int(item_id):
            error("Error using item. Item not found.")
            return
        Player.EquipItem(item)
        Misc.Pause(2000)
    Items.UseItem(item)


def get_fishing_spots():
    global ignored_tile_list
    fish_spots = []
    ignored_tile_list = refresh_ignore()
    for spot in [(x, y) for x in range(-12, 13, 6) for y in range(-12, 13, 6) if (x, y) != (0, 0)]:
        if len(Statics.GetStaticsTileInfo(Player.Position.X + spot[0], Player.Position.Y + spot[1], Player.Map)) <= 0:
            water = Statics.GetStaticsLandInfo(Player.Position.X + spot[0], Player.Position.Y + spot[1], Player.Map)
            if (water.StaticZ < 0
                    and not tile_ignored((Player.Position.X + spot[0], Player.Position.Y + spot[1], Player.Map), 3)):
                fish_spots.append((Player.Position.X + spot[0], Player.Position.Y + spot[1], water.StaticZ))
    return fish_spots


def shore_fishing(max_attempts=20):
    while not Player.IsGhost:
        char_pos = (Player.Position.X, Player.Position.Y)
        for fish_spot in get_fishing_spots():
            if (Player.Position.X, Player.Position.Y) != char_pos:
                break
            for _ in range(max_attempts):
                check_hp()
                check_cut()
                use_id(utils['fishing_pole'])
                Target.WaitForTarget(2500, False)
                Journal.Clear()
                Target.TargetExecute(fish_spot[0], fish_spot[1], fish_spot[2], 0)
                if answer(wait_journal(10000)) == 'change':
                    ignored_tile_list.append({'tile': {'X': fish_spot[0], 'Y': fish_spot[1], 'World': Player.Map},
                                              'time': datetime.now()})
                    break
                if (Player.Position.X, Player.Position.Y) != char_pos:
                    break
        check_cut(1)
        while (Player.Position.X, Player.Position.Y) == char_pos:
            Misc.SendMessage("No more fish here. Move to another position.", 68)
            Misc.Pause(5000)


ignored_tile_list = []
cut_weapon = get_cut_weapon()
trash_bag = get_bag()
shore_fishing()



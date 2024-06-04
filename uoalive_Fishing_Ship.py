from System.Collections.Generic import List
from System import Int32
import sys
from AutoComplete import *


fish_info = {0x3E65: ('E', [(x, y) for x in range(0, 13, 6) for y in range(-12, 13, 6) if (x, y) != (0, 0)]),
             0x3EB9: ('S', [(x, y) for x in range(-12, 13, 6) for y in range(0, 13, 6) if (x, y) != (0, 0)]),
             0x3E93: ('W', [(x, y) for x in range(0, -13, -6) for y in range(-12, 13, 6) if (x, y) != (0, 0)]),
             0x3EAE: ('N', [(x, y) for x in range(-12, 13, 6) for y in range(0, -13, -6) if (x, y) != (0, 0)])}

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


def dist(pos1, pos2):
    return max(abs(pos1[0] - pos2[0]), abs(pos1[1] - pos2[1]))


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


def get_hatch():
    hatch_filter = Items.Filter()
    hatch_filter.OnGround = 1
    hatch_filter.RangeMax = 7
    hatch_filter.Graphics = List[Int32](fish_info.keys())
    hatch_list = Items.ApplyFilter(hatch_filter)
    if not hatch_list:
        error("Error. hatch not found. Finishing.", True)
    if len(hatch_list) > 1:
        error("Error. Try to run the macro far from other ships. Finishing.", True)
    return hatch_list[0]


def get_bag():
    bag = get_shared('trash_bag')
    while not bag or not bag.IsContainer:
        bag = set_shared('trash_bag', "Target a bag for trash inside the hatch")
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
        deposit()


def check_hp():
    if Player.Hits < Player.HitsMax - 10:
        error("An enemy appeared. Finishing, as you prepare for battle.", True)


def check_position():
    while not (Player.Position.X, Player.Position.Y) == (hatch.Position.X, hatch.Position.Y):
        Player.PathFindTo(hatch.Position)
        Misc.Pause(1000)


def turn_ship(old_dir):
    Player.ChatSay("turn right")
    Misc.Pause(1000)
    new_dir = fish_info[hatch.ItemID][0]
    if new_dir != old_dir:
        return
    error("something is wrong. Failed to change ship direction.")
    Misc.Pause(500)
    move_ship()


def move_ship():
    old_pos = (hatch.Position.X, hatch.Position.Y)
    Player.ChatSay("forward")
    for _ in range(200):
        Misc.Pause(100)
        if dist(old_pos, (hatch.Position.X, hatch.Position.Y)) >= 32:
            break
    Player.ChatSay("stop")


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


def deposit():
    while not Player.IsGhost:
        mess = Items.FindByID(utils['fish_mess'], -1, Player.Backpack.Serial)
        if not mess:
            break
        Items.UseItem(mess)
        Misc.Pause(300)

    Misc.SendMessage("Depositing fish into hatch", 53)
    Journal.Clear()
    transfer_list = [(hatch, [utils['fish_steak'], utils['white_pearl'], utils['delicate scales']]),
                     (trash_bag, List[Int32](trash.values()))]
    for container, item_id_list in transfer_list:
        for item_id in item_id_list:
            while not Player.IsGhost:
                item = Items.FindByID(item_id, -1, Player.Backpack.Serial)
                if not item or Journal.SearchByType('cannot hold', 'System'):
                    break
                Items.Move(item, container, 0)
                Misc.Pause(600)
    Misc.Pause(1000)
    Misc.SendMessage("Restarting to fish", 68)


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


def get_fishing_spots(position_list):
    fish_spots = []
    for spot in position_list:
        if len(Statics.GetStaticsTileInfo(Player.Position.X + spot[0], Player.Position.Y + spot[1], Player.Map)) <= 0:
            water = Statics.GetStaticsLandInfo(Player.Position.X + spot[0], Player.Position.Y + spot[1], Player.Map)
            if water.StaticZ < 0:
                fish_spots.append((Player.Position.X + spot[0], Player.Position.Y + spot[1], water.StaticZ))
    return fish_spots


def fish(max_attempts=20):
    while not Player.IsGhost:
        for i in range(4):
            direction, position_list = fish_info[hatch.ItemID]
            for fish_spot in get_fishing_spots(position_list):
                for _ in range(max_attempts):
                    check_hp()
                    check_cut()
                    check_position()
                    use_id(utils['fishing_pole'])
                    Target.WaitForTarget(2500, False)
                    Journal.Clear()
                    Target.TargetExecute(fish_spot[0], fish_spot[1], fish_spot[2], 0)
                    if answer(wait_journal(10000)) == 'change':
                        break
            if not i == 3:
                turn_ship(direction)
        move_ship()


hatch = get_hatch()
cut_weapon = get_cut_weapon()
check_position()
Items.UseItem(hatch)
Misc.Pause(500)
trash_bag = get_bag()
fish()

import re
import sys
from datetime import datetime, timedelta
from System.Collections.Generic import List
from System import Int32
from AutoComplete import *

unload_chest = 0x40242237

beetle_id = [0x0317]

tree_tiles = [782, 783, 3274, 3275, 3277, 3278, 3280, 3283, 3284, 3286, 3287, 3288, 3289, 3290, 3291, 3292, 3293, 3294,
              3295, 3296, 3297, 3299, 3300, 3302, 3303, 3304, 3320, 3322, 3323, 3324, 3325, 3326, 3328, 3329, 3330,
              3331, 3393, 3394, 3395, 3396, 3415, 3416, 3417, 3418, 3419, 3438, 3439, 3440, 3441, 3442, 3460, 3461,
              3462, 3476, 3478, 3479, 3480, 3482, 3484, 3488, 3489, 3490, 3492, 3494, 3496, 3498, 3499, 9099, 10171,
              10172, 10217, 10218, 10834, 10836, 10837, 10838, 11030, 11282, 11297, 13317, 13318, 13319, 13320, 13517,
              14392, 14394, 14396, 14397, 14398, 14399, 14403, 16298, 16299, 16300, 16301, 16302, 16303, 16304, 16305,
              16306, 16307]

utils = {'axe': [0x0F43, 0x0EC3, 0x0EC4, 0x0F45, 0x0F47, 0x0F49, 0x0F52, 0x0F4B, 0x0F4D, 0x0F5E, 0x13B6, 0x13B9, 0x13FB,
                 0x13F6, 0x1401, 0x143E, 0x1443, 0x26BA, 0x26BB, 0x26BD, 0x26C0, 0x26C1],
         'Kindling': 0x0DE1, 'Log': 0x1BDD}

to_transfer = {'Boards': 0x1BD7, 'Bark Fragment': 0x318F, 'Brilliant Amber': 0x3199, 'Luminescent Funghi': 0x3191,
               'Parasitic Plant': 0x3190, 'Switch': 0x2F5F}

journal_messages = {
    'Lumberjacking': {'success': " into your backpack.",
                      'fail': "You hack at the tree for a while, but ",
                      'wait': "You must wait to perform another action.",
                      'empty': " not enough wood here to harvest.",
                      'target': "Target cannot be seen.",
                      'target2': " can't see the target",
                      'far_away': "That is too far away.",
                      'worthless': "You can't use an axe on that."}}


def error(text, skill='', item_name='', finish=True):
    msg = ""
    if skill:
        msg = msg + skill
    if item_name:
        msg = msg + " | item: " + item_name
    msg = msg + "\r\n" + text + "\r\n"
    if finish:
        msg = msg + "FINISHING." + "\r\n\r\n"
    Misc.SendMessage(msg, 38)
    if finish:
        sys.exit()


def get_first(item_list):
    if item_list:
        return item_list[0]
    return None


def get_from_ground(id_list, type_="both", radius=2, name=None, only_containers=False):
    if type_ in ["mobile", "mob", "both"]:
        mobile_filter = Mobiles.Filter()
        mobile_filter.RangeMax = radius
        mobile_filter.Bodies = List[Int32](id_list)
        if name:
            mobile_filter.Name = name
        if only_containers:
            mobile_filter.IsContainer = 1
        mobiles = Mobiles.ApplyFilter(mobile_filter)
        if mobiles:
            return mobiles
    if type_ in ["item", "both"]:
        item_filter = Items.Filter()
        item_filter.OnGround = 1
        item_filter.RangeMax = radius
        item_filter.Graphics = List[Int32](id_list)
        if name:
            item_filter.Name = name
        if only_containers:
            item_filter.IsContainer = 1
        items = Items.ApplyFilter(item_filter)
        if items:
            return items
    return []


def dot_container(item):
    if type(item) is int:
        item = Items.FindBySerial(item)
    else:
        item = Items.FindBySerial(item.Serial)
    if item:
        return item.Container
    return 0


def dist(pos1, pos2=Player):
    pos = [pos1, pos2]
    for i, _ in enumerate(pos):
        if type(pos[i]) is not dict:
            try:
                _ = pos[i].Serial
            except Exception:
                pos[i] = Items.FindBySerial(pos[i])
        try:
            if pos[i].Serial == Player.Backpack.Serial:
                pos[i] = Player
            if dot_container(pos[i]) > 0:
                pos[i] = Items.FindBySerial(dot_container(pos[i]))
                return dist(pos[0], pos[1])
        except Exception:
            pass
        if pos[i] and type(pos[i]) is not dict:
            try:
                pos[i] = {'X': pos[i].Position.X, 'Y': pos[i].Position.Y, 'Map': pos[i].Map}
            except Exception:
                pos[i] = {'X': pos[i].Position.X, 'Y': pos[i].Position.Y, 'Map': Player.Map}
    try:
        if pos[0]['Map'] != pos[1]['Map']:
            return 10000
    except Exception:
        return 10000
    return max(abs(pos[0]['X'] - pos[1]['X']), abs(pos[0]['Y'] - pos[1]['Y']))


def refresh_ignore(respawn_time=2400):
    _new_list = []
    for _ignored in ignored_tile_list:
        if timedelta.total_seconds(datetime.now() - _ignored['time']) < respawn_time:
            _new_list.append(_ignored)
    return _new_list


def tile_ignored(tile, radius=0):
    for _ignored in ignored_tile_list:
        if dist(tile, _ignored['tile']) <= radius:
            return True
    for _ignored in temp_ignored_tile_list:
        if dist(tile, _ignored['tile']) <= radius:
            return True
    return False


def still(char_pos):
    return char_pos == (Player.Position.X, Player.Position.Y, Player.Map)


def wait_journal(timeout, skill):
    def uoalive_check_save():
        if Journal.Search("The world is saving, please wait."):
            Misc.Pause(3000)
            Journal.Clear("The world is saving, please wait.")

    for _ in range(int(timeout / 100)):
        Misc.Pause(100)
        uoalive_check_save()
        for message in journal_messages[skill]:
            if Journal.Search(journal_messages[skill][message]):
                return message
    Target.Cancel()
    return ''


def mount(animal):
    if animal and not Player.Mount:
        for _ in range(10):
            Mobiles.UseMobile(animal)
            for _ in range(10):
                Misc.Pause(100)
                if Player.Mount:
                    return True
    return False


def unmount():
    mounted = Player.Mount
    for _ in range(10):
        if Player.Mount:
            Mobiles.UseMobile(Player.Serial)
        for _ in range(10):
            Misc.Pause(100)
            if not Player.Mount:
                return mounted
    return None


def unload(unload_containers, to_container, ids_list=None, color_list=None, name_list=None, amount=0):
    for container in unload_containers:
        for item_id in ids_list:
            while True:
                item = Items.FindByID(item_id, -1, container.Serial, -1, True)
                if not item:
                    break
                if (color_list and item.Hue not in color_list) or (name_list and item.Name not in name_list):
                    Misc.IgnoreObject(item.Serial)
                    continue
                Items.Move(item, to_container, amount)
                Misc.Pause(1000)
    Misc.ClearIgnore()


def check_unload():
    if dist(unload_chest) <= 2:
        Misc.SendMessage("Transfering items to your selected chest...", 90)
        Misc.Pause(1000)
        if dist(unload_chest) > 2:
            return
        beetle = find_beetle()
        if beetle:
            Items.UseItem(beetle.Backpack)
        Misc.Pause(500)
        unload([Player.Backpack] + ([beetle.Backpack] if beetle else []), unload_chest, list(to_transfer.values()))
        mount(beetle)
        Misc.SendMessage("Transfer finished", 90)
        while dist(unload_chest) <= 2:
            Misc.Pause(1000)


def find_beetle():
    global no_beetle
    if no_beetle:
        return None
    beetles = get_from_ground(beetle_id, "mob")
    for beetle in beetles:
        if Mobiles.ContextExist(beetle.Serial, "Command: Guard", False) > 0:
            return beetle
    if Player.Mount:
        animal = unmount()
        beetle = find_beetle()
        if beetle:
            return beetle
        mount(animal)
        Player.HeadMessage(38, 'No Beetle Found')
        no_beetle = True
        Misc.Pause(1000)
    return None


def beetle_store():
    beetle = find_beetle()
    if beetle:
        Player.HeadMessage(2127, 'Moving boards to beetle...')
        unload([Player.Backpack], beetle.Backpack, list(to_transfer.values()))
        try:
            b_weight = int(re.findall(r'\d+', Mobiles.GetPropStringByIndex(beetle.Serial, 1))[0])
            b_items_count = re.findall(r'\d+', Mobiles.GetPropStringByIndex(beetle.Serial, 4))
            if b_weight > 1300 or int(b_items_count[0])/int(b_items_count[1]) > 0.8:
                Player.HeadMessage(38, "Beetle is heavy.")
        except Exception:
            pass
        mount(beetle)
        return True
    return False


def make_boards(_axe):
    while not Player.IsGhost:
        log = Items.FindByID(utils['Log'], -1, Player.Backpack.Serial, -1, True)
        if not log:
            break
        Items.UseItem(_axe)
        Target.WaitForTarget(3000)
        Target.TargetExecute(log.Serial)
        Misc.Pause(500)
        Target.Cancel()


def check_heavy():
    if Player.Weight > Player.MaxWeight - 50:
        make_boards()
    if Player.Weight > Player.MaxWeight - 50:
        Player.HeadMessage(28, "You are heavy.")
        beetle_store()


def answer(message):
    Journal.Clear()
    if message in ['wait', 'already']:
        Misc.Pause(2000)
        return 'continue'
    if not message or message in ['worthless', 'empty']:
        Target.Cancel()
        return 'change and ignore'
    if message in ['far_away', 'target', 'target2']:
        Target.Cancel()
        return 'change'
    if message == 'enemy':
        error("An enemy appeared. Finishing, as you prepare for battle.", '', '', True)
    return 'continue'


def get_trees(radius, skip_ignored=False):
    def height_reachable(_tile):
        return abs(_tile.StaticZ - Player.Position.Z) <= 3

    _selected = []
    for spot in [{'X': Player.Position.X + x, 'Y': Player.Position.Y + y, 'Map': Player.Map}
                 for x in range(-radius, radius + 1) for y in range(-radius, radius + 1) if (x, y) != (0, 0)]:
        if not tile_ignored(spot) or skip_ignored:
            for tile in Statics.GetStaticsTileInfo(spot['X'], spot['Y'], spot['Map']):
                if height_reachable(tile) and tile.StaticID in tree_tiles:
                    _selected.append({'Tile': tile.StaticID, 'X': spot['X'], 'Y': spot['Y'], 'Z': tile.StaticZ,
                                      'Map': spot['Map']})
                    break
    return _selected


def sort_trees(trees):
    _char_pos = {'X': Player.Position.X, 'Y': Player.Position.Y, 'Map': Player.Map}

    # Group trees by rounded distance
    trees_by_distance = {}
    for _tree in trees:
        trees_by_distance.setdefault(dist(_tree, _char_pos), []).append(_tree)

    # Sort trees within groups
    ordered_trees_list = []
    for _, group in sorted(trees_by_distance.items()):
        ordered_trees_list.extend(group)

    return ordered_trees_list


def equip_hand_from_id_list(item_id_list, first_run=False):
    if first_run:
        items = Items.FindAllByID(item_id_list, -1, Player.Backpack.Serial, 0, True)
        for item in items:
            if "|lumberjacking +" in "|".join([str(p).lower() for p in item.Properties]):
                Player.EquipItem(item)
                Misc.Pause(500)
                return item
    for i in ['RightHand', 'LeftHand']:
        hand_item = Player.GetItemOnLayer(i)
        if hand_item and hand_item.ItemID in item_id_list:
            return hand_item
    items = Items.FindAllByID(item_id_list, -1, Player.Backpack.Serial, 0, True)
    if items:
        Player.EquipItem(get_first(items))
        Misc.Pause(500)
        return get_first(items)
    error("Error equipping item. Item not found.")
    return None


def chop(char_pos, attempts):
    global axe, temp_ignored_tile_list
    temp_ignored_tile_list = []
    trees = sort_trees(get_trees(2))
    for tree in trees:
        for _ in range(attempts):
            if not still(char_pos):
                return trees
            check_heavy()
            axe = equip_hand_from_id_list(utils['axe'])
            Items.UseItem(axe)
            Target.WaitForTarget(4000)
            Target.TargetExecute(tree['X'], tree['Y'], tree['Z'], tree['Tile'])
            response = answer(wait_journal(3000, 'Lumberjacking'))
            if 'change' in response:
                if 'ignore' in response:
                    ignored_tile_list.append({'tile': tree, 'time': datetime.now()})
                else:
                    temp_ignored_tile_list.append({'tile': tree, 'time': datetime.now()})
                break
        while not Player.IsGhost:
            kindling = Items.FindByID(utils['Kindling'], -1, Player.Backpack.Serial, -1, True)
            if not kindling:
                break
            Items.UseItem(kindling)
            Misc.Pause(200)
    return trees


def lumberjacking():
    global ignored_tile_list
    while not Player.IsGhost:
        check_unload()
        char_pos = (Player.Position.X, Player.Position.Y, Player.Map)
        chop(char_pos, 15)
        make_boards(axe)

        trees = get_trees(2, True)
        ignored_tile_list = refresh_ignore()
        while still(char_pos):
            if trees:
                Misc.SendMessage("Empty trees. Move to Next Location.", 68)
            for _ in range(500):
                Misc.Pause(10)
                if not still(char_pos):
                    break


no_beetle = False
Journal.Clear()
ignored_tile_list = []
temp_ignored_tile_list = []
Misc.ClearIgnore()
axe = equip_hand_from_id_list(utils['axe'], True)
lumberjacking()

import sys
from datetime import datetime, timedelta
from AutoComplete import *
#from make_bod import *


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
        if type(pos[i]) is not dict:
            try:
                pos[i] = {'X': pos[i].Position.X, 'Y': pos[i].Position.Y, 'Map': pos[i].Map}
            except Exception:
                pos[i] = {'X': pos[i].Position.X, 'Y': pos[i].Position.Y, 'Map': Player.Map}
    try:
        if pos[0]['Map'] != pos[1]['Map']:
            return 10000
    except Exception:
        pass
    return max(abs(pos[0]['X'] - pos[1]['X']), abs(pos[0]['Y'] - pos[1]['Y']))


def craft(skill, item_name, resources_id_list, amount=1):
    for _ in range(amount):
        for _ in range(5):
            resource = get_resource(resources_id_list, amount)
            tool = get_tool(skill)
            if resource and tool:
                break
        make_item(item_name, skill, 1)


def cooking():
    global auxiliary_chest, trash_barrel
    auxiliary_chest = get_and_set_shared_container("auxiliary chest", "auxiliary_chest")
    trash_barrel = get_and_set_shared_container("trash barrel", "trash_barrel")

    foods = {'fish steak': {'done': 0x097B, 'raw': 0x097A}, 'cooked bird': {'done': 0x09B7, 'raw': 0x09B9},
             'cut of ribs': {'done': 0x09F2, 'raw': 0x09F1}, 'chicken leg': {'done': 0x1608, 'raw': 0x1607},
             'leg of lamb': {'done': 0x160A, 'raw': 0x1609}, 'miso soup': {'done': 0x284D, 'raw': 0x097A}}
    skill = "Cooking"

    while not Player.IsGhost and not in_cap(skill):
        if Player.GetSkillValue(skill) < 60:
            for _ in range(20):
                for food in foods:
                    if Player.GetSkillValue(skill) >= 60 or Player.Weight >= Player.MaxWeight - 20:
                        break
                    craft(skill, food, [foods[food]['raw']])
            if auxiliary_chest != Player.Backpack.Serial:
                throw_items([foods[food]['done'] for food in foods], auxiliary_chest)
        if 60 <= Player.GetSkillValue(skill) < 120 and not in_cap(skill):
            endless_decanter = Items.FindByID(int(0x0FF6), int(0x0399), Player.Backpack.Serial, -1, True)
            full_pitcher = Items.FindByID(int(0x1F9D), -1, Player.Backpack.Serial, -1, True)
            if endless_decanter or full_pitcher:
                craft(skill, 'miso soup', [foods['miso soup']['raw']], 10)
            else:
                empty_pitcher = Items.FindByID(int(0x0FF6), int(0x0000), Player.Backpack.Serial, -1, True)
                water_trough = get_first(get_items_by_filter([0x0B41, 0x0B42, 0x0B43, 0x0B44]))
                if empty_pitcher and water_trough:
                    Items.UseItem(empty_pitcher)
                    if Target.WaitForTarget(4000, False) > 0:
                        Target.TargetExecute(water_trough)
                        Misc.Pause(600)
            trash([foods['miso soup']['done']])


def cartography():
    global auxiliary_chest, trash_barrel
    auxiliary_chest = get_and_set_shared_container("auxiliary chest", "auxiliary_chest")
    trash_barrel = get_and_set_shared_container("trash barrel", "trash_barrel")
    skill = "Cartography"
    blank_scroll_id = 0x0EF3
    map_id = 0x14EC

    while not Player.IsGhost and not in_cap(skill):
        if 0 <= Player.GetSkillValue(skill) < 50:
            craft(skill, "Local Map", [blank_scroll_id], 10)
        if 50 <= Player.GetSkillValue(skill) < 70:
            craft(skill, "City Map", [blank_scroll_id], 10)
        if 70 <= Player.GetSkillValue(skill) < 99.5:
            craft(skill, "World Map", [blank_scroll_id], 10)
        trash([map_id])


################# LUMBERJACKING

tree_tiles = [782, 783, 3274, 3275, 3277, 3278, 3280, 3283, 3284, 3286, 3287, 3288, 3289, 3290, 3291, 3292, 3293, 3294,
              3295, 3296, 3297, 3299, 3300, 3302, 3303, 3304, 3320, 3322, 3323, 3324, 3325, 3326, 3328, 3329, 3330,
              3331, 3393, 3394, 3395, 3396, 3415, 3416, 3417, 3418, 3419, 3438, 3439, 3440, 3441, 3442, 3460, 3461,
              3462, 3476, 3478, 3479, 3480, 3482, 3484, 3488, 3489, 3490, 3492, 3494, 3496, 3498, 3499, 9099, 10171,
              10172, 10217, 10218, 10834, 10836, 10837, 10838, 11030, 11282, 11297, 13317, 13318, 13319, 13320, 13517,
              14392, 14394, 14396, 14397, 14398, 14399, 14403, 16298, 16299, 16300, 16301, 16302, 16303, 16304, 16305,
              16306, 16307]

cave_tiles = [1339, 1340, 1341, 1342, 1343, 1344, 1345, 1346, 1347, 1348, 1349, 1350, 1351, 1352,
              1353, 1354, 1355, 1356, 1357, 1358, 1359, 1361, 1362, 1363, 1386]

utils = {'axe': [0x0EC3, 0x0EC4, 0x0F45, 0x0F47, 0x0F49, 0x0F52, 0x0F4B, 0x0F4D, 0x0F5E, 0x13B6, 0x13B9, 0x13FB,
                 0x13F6, 0x1401, 0x143E, 0x1443, 0x26BA, 0x26BB, 0x26BD, 0x26C0, 0x26C1],
         'Kindling': 0x0DE1, 'Log': 0x1BDD}

journal_messages = {
    'Lumberjacking': {'success': " into your backpack.",
                      'fail': "You hack at the tree for a while, but ",
                      'wait': "You must wait to perform another action.",
                      'empty': " not enough wood here to harvest.",
                      'target': "Target cannot be seen.",
                      'target2': " can't see the target",
                      'far_away': "That is too far away.",
                      'worthless': "You can't use an axe on that."},
    'Fishing': {'success': "You pull out ",
                'pearl': "You have found ",
                'big_fish': "Your fishing pole bends as you pull a big fish from the depths!",
                'enemy': "Uh oh! That doesn't look like a fish!",
                'fail': "You fish a while, but fail to catch anything.",
                'wait': "You must wait to perform another action.",
                'already': "You are already fishing.",
                'empty': "The fish don't seem to be biting here.",
                'far_away': "You need to be closer to the water to fish!",
                'target': "Target cannot be seen."}}


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


def wait_journal(timeout, skill):
    for _ in range(int(timeout / 100)):
        Misc.Pause(100)
        for message in journal_messages[skill]:
            if Journal.Search(journal_messages[skill][message]):
                return message
    Target.Cancel()
    return ''


def answer(message):
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


def get_trees(radius):
    def height_reachable(_tile):
        return abs(_tile.StaticZ - Player.Position.Z) <= 3

    _selected = []
    for spot in [{'X': Player.Position.X + x, 'Y': Player.Position.Y + y, 'Map': Player.Map}
                 for x in range(-radius, radius + 1) for y in range(-radius, radius + 1) if (x, y) != (0, 0)]:
        if not tile_ignored(spot):
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


def make_boards():
    while not Player.IsGhost:
        log = Items.FindByID(utils['Log'], -1, Player.Backpack.Serial, -1, True)
        if not log:
            break
        use_from_id_list(utils['axe'])
        Target.WaitForTarget(3000)
        Target.TargetExecute(log.Serial)
        Misc.Pause(500)
        Target.Cancel()


def check_heavy():
    if Player.Weight > Player.MaxWeight - 50:
        make_boards()
    if Player.Weight > Player.MaxWeight - 50:
        Player.HeadMessage(28, "You are heavy.")


def still(_char_pos):
    return _char_pos == (Player.Position.X, Player.Position.Y, Player.Map)


def equip_hand_from_id_list(item_id_list):
    item_r = Player.GetItemOnLayer('RightHand')
    item_l = Player.GetItemOnLayer('LeftHand')
    if (not item_r or item_r.ItemID not in item_id_list) and (not item_l or item_l.ItemID not in item_id_list):
        item = None
        for item_id in item_id_list:
            item = Items.FindByID(int(item_id), -1, Player.Backpack.Serial)
            if item:
                break
        if not item:
            error("Error equipping item. Item not found.")
            return False
        Player.EquipItem(item)
        Misc.Pause(1000)
    return True


def use_from_id_list(item_id_list):
    Target.Cancel()
    item_r = Player.GetItemOnLayer('RightHand')
    if item_r and item_r.ItemID in item_id_list:
        Items.UseItem(item_r)
        return True
    item_l = Player.GetItemOnLayer('LeftHand')
    if item_l and item_l.ItemID in item_id_list:
        Items.UseItem(item_l)
        return True
    item = None
    for item_id in item_id_list:
        item = Items.FindByID(int(item_id), -1, Player.Backpack.Serial)
        if item:
            break
    if not item:
        error("Error using item. Item not found.")
        return False
    Items.UseItem(item)
    return True


def chop(_char_pos, attempts):
    global temp_ignored_tile_list
    temp_ignored_tile_list = []
    for tree in sort_trees(get_trees(3)):
        for i in range(attempts):
            if not still(_char_pos):
                return False
            check_heavy()
            equip_hand_from_id_list(utils['axe'])
            Journal.Clear()
            use_from_id_list(utils['axe'])
            Target.WaitForTarget(4000)
            Target.TargetExecute(tree['X'], tree['Y'], tree['Z'], tree['Tile'])
            response = answer(wait_journal(5000, 'Lumberjacking'))
            if 'change' in response:
                if 'ignore' in response:
                    ignored_tile_list.append({'tile': tree, 'time': datetime.now()})
                else:
                    temp_ignored_tile_list.append({'tile': tree, 'time': datetime.now()})
                break
        while True:
            kindling = Items.FindByID(utils['Kindling'], -1, Player.Backpack.Serial, -1, True)
            if not kindling:
                break
            Items.UseItem(kindling)
            Misc.Pause(200)
    return True


def lumberjacking():
    global ignored_tile_list
    while not Player.IsGhost:
        char_pos = (Player.Position.X, Player.Position.Y, Player.Map)
        chop(char_pos, 15)
        make_boards()

        while still(char_pos):
            Misc.SendMessage("Empty trees. Move to Next Location.", 68)
            Misc.Pause(1000)

        ignored_tile_list = refresh_ignore()


# globals
#crafting_gump_id = get_shared("crafting_gump_id")
#auxiliary_chest = get_shared_item("auxiliary_chest")
#trash_barrel = get_shared_item("trash_barrel")
ignored_tile_list = []
temp_ignored_tile_list = []
#Misc.ClearIgnore()

#mysticism()
# function calls
# cartography()
lumberjacking()
import os
import re
import sys
import shutil
import threading
from recall_home import *
from datetime import datetime, timedelta
from System.Collections.Generic import List
from System import Int32
from AutoComplete import *

# Original author/repo: https://github.com/fspy/uo-scripts
# REQUIREMENTS:
# - A few (~20) iron ingots, or some shovels;
# - A fire beetle;
# - A blue (giant) beetle;

tool_kits_to_keep = 2
shovels_to_keep = 2

# this is the chest serial you'll store your items in the house
unload_chest = 0x40242237

files = {'recall_home': 'recall_home.py', 'recall_next_mine': "recall_next_mine.py"}

enemy_msg = ["You have been ambushed!"]

mining_tools_ids = [0x0F39, 0x0E86]
tinker_tools_ids = [0x1EB8, 0x1EBC]
ingot_id = [0x1BF2]
ingot_colors = {'Iron': 0x0000, 'Dull Copper': 0x0973, 'Shadow Iron': 0x0966, 'Copper': 0x096D, 'Bronze': 0x0972,
                'Gold': 0x08A5, 'Agapite': 0x0979, 'Verite': 0x089F, 'Valorite': 0x08AB}
ores_ids = [0x19B7, 0x19B8, 0x19B9, 0x19BA]
gems_ids = [0x3192, 0x3193, 0x3194, 0x3195, 0x3196, 0x3197, 0x3198, 0x0F28]
sand_id = [0x423A]
fire_beetle_id = [0x00A9]
beetle_id = [0x0317]

use_teleport = True

land_coords = [(0, 0), (1, 0), (-1, 0), (0, -1), (0, 1), (1, -1), (-1, -1), (1, 1), (-1, 1)]

spell_recovery = 3000 - 250 * Player.FasterCastRecovery - 250 * Player.FasterCasting


class File:
    def __init__(self, name):
        self.name = name
        if name.find('/') > 0:
            os.makedirs(name.rsplit('/', 1)[0], exist_ok=True)  # create directory if it doesn't exist
        open(self.name, 'a').close()  # create file if it doesn't exist

    def read(self):
        with open(self.name) as _r_file:
            _lines = _r_file.readlines()
            _r_file.close()
            return [[item.strip() for item in line.replace('\n', '').split(',')] for line in _lines]

    def write(self, matrix):
        _file = open(self.name, 'a+')
        for _list in matrix:
            _file.write(", ".join(_list) + '\n')
        _file.close()

    def erase(self):
        open(self.name, 'w').close()

    def refresh(self, matrix):
        self.erase()
        self.write(matrix)

    def backup(self, backup_name):
        if backup_name.find('/') > 0:
            os.makedirs(backup_name.rsplit('/', 1)[0], exist_ok=True)  # create directory if it doesn't exist
        shutil.copy(self.name, backup_name)  # backups the original file before starting working on it


def get_first(item_list):
    return item_list[0] if item_list else None


def dot_container(item):
    item = Items.FindBySerial(item) if type(item) is int else Items.FindBySerial(item.Serial)
    return item.Container if item else 0


def uoalive_check_save():
    if Journal.Search("The world is saving, please wait."):
        Misc.Pause(3000)
        Journal.Clear("The world is saving, please wait.")


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


def ore_filter(hue=-1, container=Player.Backpack.Serial):
    return Items.FindAllByID(ores_ids, hue, container, True, True)


def dismount():
    if Player.Mount:
        mounted = Player.Mount
        for _ in range(10):
            if Player.Mount:
                Mobiles.UseMobile(Player.Serial)
            for _ in range(10):
                Misc.Pause(100)
                if not Player.Mount:
                    return mounted
    return None


def config_beetles():
    if not find_beetle('fire'):
        Player.HeadMessage(38, 'No Fire Beetle Found. The macro needs it to run. FINISHING.')
        sys.exit()
    if not find_beetle('blue'):
        Player.HeadMessage(28, 'No Blue Beetle Found. Continuing without beetle.')
        return False
    return True


def still(char_pos):
    return char_pos == {'X': Player.Position.X, 'Y': Player.Position.Y, 'Map': Player.Map}


def heavy(weight_limit=.8 * Player.MaxWeight):
    return Player.Weight >= weight_limit


def player_inside(char_pos):
    return get_land_resources(char_pos, ["rock", "sand"], 0)


def find_forge():
    return get_first(get_from_ground(fire_beetle_id))


def check_beetles_close():
    if find_beetle('fire') and ((not with_blue) or find_beetle('blue')):
        return
    for _ in range(3):
        Player.ChatSay(90, "all come")
        for _ in range(50):
            Misc.Pause(100)
            if find_beetle('fire') and ((not with_blue) or find_beetle('blue')):
                return
    Misc.SendMessage("Error: Beetle is lost. Check this manually. FINISHING.", 38)
    sys.exit()


def wait_recovery():
    if Timer.Check("recovery"):
        Misc.Pause(Timer.Remaining("recovery"))


def wait_mana():
    while Player.Mana < 9:
        Misc.Pause(1000)


def wait_needs():
    if needs_running:
        Misc.SendMessage("Waiting smelt/create tools to finish.", 90)
        while needs_running:
            Misc.Pause(100)


def wait_path():
    if path_running:
        Misc.SendMessage("Waiting path calculation.", 90)
        while path_running:
            Misc.Pause(100)


def recalling_home():
    global mine_path
    if Misc.ScriptStatus(files['recall_home']):
        Misc.SetSharedValue('ready_to_recall', True)
        mine_path = []
        return True
    return False


def recalling():
    global mine_path
    if Misc.ScriptStatus(files['recall_home']) or Misc.ScriptStatus(files['recall_next_mine']):
        Misc.SetSharedValue('ready_to_recall', True)
        mine_path = []
        return True
    return False


def manual_unload():
    deposit()
    while True:
        Misc.Pause(10)
        if Misc.ScriptStatus(files['recall_next_mine']):
            while True:
                Misc.Pause(1000)
                if not Misc.ScriptStatus(files['recall_next_mine']):
                    return


def chunk_in_list(tile, tile_list, size=8):
    for item in tile_list:
        if (int(tile['X'] / size), int(tile['Y'] / size)) == (int(item['X'] / size), int(item['Y'] / size)):
            return True
    return False


def tile_ignored(tile, radius=0):
    for _ignored in ignored_tile_list:
        if dist(tile, {'X': _ignored[0], 'Y': _ignored[1], 'Map': _ignored[2]}) <= radius:
            return True
    return False


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


def set_shared(name, item):
    if item:
        Misc.SetSharedValue(name, item.Serial)
    return item


def get_shared(name):
    return int(Misc.ReadSharedValue(name))


def set_shared_item(name, _msg):
    Misc.SendMessage(_msg, 68)
    item = Items.FindBySerial(Target.PromptTarget(""))
    if item:
        Misc.SetSharedValue(name, item.Serial)
    return item


def set_shared_gump(name, gump_num):
    if gump_num != get_shared(name):
        Misc.SetSharedValue(name, gump_num)
    return gump_num


def get_gump_num(text_list, timeout=10000):
    for _ in range(int(timeout / 100)):
        for text in text_list:
            if Gumps.LastGumpTextExist(text):
                return Gumps.CurrentGump()
        Misc.Pause(100)
        if Journal.Search("You must wait to perform another action."):
            Misc.Pause(2000)
            Journal.Clear()
            return 0
    return 0


def unload(unload_containers, to_container, ids_list=None, color_list=None, name_list=None, amount=0):
    try:
        to_container = Items.FindBySerial(to_container)
    except Exception:
        pass

    def wait_transfer(timeout):
        for _ in range(int(timeout / 100)):
            Misc.Pause(100)
            it = Items.FindBySerial(item.Serial)
            to_container_contents = to_container.Contains
            if (not it) or it.Serial in [i.Serial for i in to_container_contents] or it.Amount < i_amount:
                return True
        return False

    for container in unload_containers:
        for item_id in ids_list:
            items = Items.FindAllByID([item_id], -1, container.Serial, -1, True)
            for item in items:
                if (color_list and item.Hue not in color_list) or (name_list and item.Name not in name_list):
                    Misc.IgnoreObject(item.Serial)
                    continue
                i_amount = item.Amount
                for _ in range(3):
                    Items.Move(item, to_container, amount)
                    if wait_transfer(2000):
                        break

    Misc.ClearIgnore()


def open_craft_gump():
    global crafting_gump_id
    if crafting_gump_id > 0 and Gumps.WaitForGump(crafting_gump_id, 100) > 0:
        return True
    Journal.Clear()
    tinker_tool = get_first(get_tools(tinker_tools_ids))
    if tinker_tool:
        while True:
            Items.UseItem(tinker_tool)
            crafting_gump_new_id = get_gump_num(["TINKERING MENU"])
            if crafting_gump_new_id > 0:
                crafting_gump_id = set_shared_gump("crafting_gump_id", crafting_gump_new_id)
                return True
    else:
        Player.HeadMessage(38, 'Error: No Tool Kit Found. Finishing')
        sys.exit()


def answer_craft_gump(menu_button, item_button=None):
    if crafting_gump_id > 0 and Gumps.WaitForGump(crafting_gump_id, 100) > 0:
        Gumps.SendAction(crafting_gump_id, menu_button)
        if item_button:
            Gumps.WaitForGump(crafting_gump_id, 4000)
            Gumps.SendAction(crafting_gump_id, item_button)
        return True
    return False


def make_tool():
    button = {"tools": 41, "tool_kit": 62, "shovel": 202}
    for id_list, quantity, item in [(tinker_tools_ids, tool_kits_to_keep, "tool_kit"),
                                    (mining_tools_ids, shovels_to_keep, "shovel")]:
        if len(get_tools(id_list)) < quantity:
            open_craft_gump()
            answer_craft_gump(button["tools"], button[item])
            Misc.Pause(200)
    Gumps.WaitForGump(crafting_gump_id, 4000)
    Gumps.CloseGump(crafting_gump_id)


def get_tools(tool_id_list):
    tools = []
    for tool_id in tool_id_list:
        tools += Items.FindAllByID(tool_id, 0, Player.Backpack.Serial, True)
    return tools


def find_beetle(b_type):
    b_types = {'fire': fire_beetle_id, 'shrunken_fire': 0x281C,
               'blue': beetle_id, 'shrunken_blue': 0x260F}
    beetles = get_from_ground(b_types[b_type], "mob")
    for beetle in beetles:
        if Mobiles.ContextExist(beetle.Serial, "Command: Guard", False) > 0:
            return beetle
    if Player.Mount:
        dismount()
        return find_beetle(b_type)
    shrunken_beetle = Items.FindByID(b_types['shrunken_' + b_type], -1, Player.Backpack.Serial)
    if shrunken_beetle:
        Items.UseItem(shrunken_beetle)
        Misc.Pause(1000)
        return find_beetle(b_type)
    return None


def beetle_store():
    beetle = find_beetle('blue')
    if beetle:
        Player.HeadMessage(2127, 'Moving ingots to beetle...')
        unload([Player.Backpack], beetle.Backpack, ingot_id, [ingot_colors[i] for i in ingot_colors if i != 'Iron'])
        unload([Player.Backpack], beetle.Backpack, gems_ids + sand_id)
        iron = get_first(Items.FindAllByID(ingot_id, 0x0000, Player.Backpack.Serial, True, True))
        if iron and iron.Amount > 50:
            unload([Player.Backpack], beetle.Backpack, ingot_id, [0x0000], None, iron.Amount - 50)
        try:
            b_weight = int(re.findall(r'\d+', Mobiles.GetPropStringByIndex(beetle.Serial, 1))[0])
            b_items_count = re.findall(r'\d+', Mobiles.GetPropStringByIndex(beetle.Serial, 4))
            if b_weight > 1300 or int(b_items_count[0]) / int(b_items_count[1]) > 0.8:
                Player.HeadMessage(38, "Beetle is heavy.")
                return "heavy"
        except Exception:
            return "heavy"
        return "success"
    return "heavy"


def deposit():
    Timer.Create("chest", 5000)
    while dist(unload_chest) > 2:
        if not Timer.Check("chest"):
            Misc.SendMessage("Waiting char to come closer to the unload chest to continue.", 65)
            Timer.Create("chest", 5000)
        if Misc.ScriptStatus(files['recall_next_mine']):
            return
        Misc.Pause(100)
    Player.HeadMessage(90, "Transfering items to your selected chest...")
    Misc.Pause(500)
    for _ in range(10):
        if dist(unload_chest) <= 2:
            Misc.Pause(10)
            if Misc.ScriptStatus(files['recall_next_mine']):
                return
            unload([Player.Backpack], unload_chest, ingot_id, [ingot_colors[i] for i in ingot_colors if i != 'Iron'])
            unload([Player.Backpack], unload_chest, gems_ids + sand_id)
            iron = get_first(Items.FindAllByID(ingot_id, 0x0000, Player.Backpack.Serial, True, True))
            if iron and iron.Amount > 50:
                unload([Player.Backpack], unload_chest, ingot_id, [0x0000], None, iron.Amount - 50)
            beetle = find_beetle('blue')
            if beetle:
                Items.UseItem(beetle.Backpack)
                Misc.Pause(500)
            if beetle:
                unload([beetle.Backpack], unload_chest, ingot_id + gems_ids + sand_id)


def group_ores():
    to_group = [ore for ore in ore_filter() if (ore.ItemID == 0x19B7 and ore.Amount == 1)]
    for ore in to_group:
        to_target = [o for o in ore_filter(ore.Hue) if o.Serial != ore.Serial]
        target_ore = get_first(to_target)
        if target_ore:
            Items.UseItem(ore)
            Target.WaitForTarget(1000)
            Target.TargetExecute(target_ore)
            Misc.Pause(200)
    return True


def smelt():
    if get_first(get_land_resources({'X': Player.Position.X, 'Y': Player.Position.Y, 'Map': Player.Map}, ["rock", "sand"])):
        ores = [ore for ore in ore_filter() if not (ore.ItemID == 0x19B7 and ore.Amount == 1)]
        if ores:
            for _ in range(2):
                forge = find_forge()
                if forge:
                    for ore in ores:
                        if ore.Container <= 0:
                            Misc.IgnoreObject(ore)
                        Items.UseItem(ore)
                        Target.WaitForTarget(1000)
                        Target.TargetExecute(forge)
                        Misc.Pause(200)
                    Target.Cancel()
                    return True
                if not Timer.Check("teleport"):
                    Player.ChatSay(90, "all come")
                Misc.Pause(3000)
            if not Timer.Check("teleport"):
                Player.HeadMessage(38, 'Error: No Forge Found')
            Misc.Pause(3000)
    return False


def get_spots(ini_pos, inside, mine_spots=None):
    def height_available():
        tile_statics = Statics.GetStaticsTileInfo(pos['X'], pos['Y'], pos['Map'])
        for tile in tile_statics:
            if abs(tile.StaticZ - Player.Position.Z) <= 5:
                return True
        return False

    if not mine_spots:
        mine_spots = []
    if inside:
        for x, y in land_coords:
            Target.Cancel()
            pos = {'X': int((ini_pos['X'] + 8 * x) / 8) * 8, 'Y': int((ini_pos['Y'] + 8 * y) / 8) * 8,
                   'Map': ini_pos['Map']}
            if chunk_in_list(pos, mine_spots, 8):
                continue
            for _x, _y in [(_x, _y) for _x in range(8) for _y in range(8)]:
                if len(Statics.GetStaticsTileInfo(pos['X'], pos['Y'], pos['Map'])) <= 1:
                    break
                if dist(ini_pos, {'X': pos['X'] + _x, 'Y': pos['Y'] + _y, 'Map': pos['Map']}) > 10:
                    continue
                pos = {'X': pos['X'] + _x, 'Y': pos['Y'] + _y, 'Map': pos['Map']}
            if ((not pos) or (not height_available()) or
                    (not get_land_resources(pos, ["rock", "sand"], 0)) or tile_ignored(pos)):
                continue
            mine_spots.append(pos)
            print("chunk: " + str((int((ini_pos['X'] + 8 * x) / 8) * 8,int((ini_pos['Y'] + 8 * y) / 8) * 8)), dist(pos))
            get_spots(pos, inside, mine_spots)
    else:
        for dim in range(2, 14, 3):
            for x in range(-dim, dim + 1):
                for y in range(-dim, dim + 1):
                    if max(x, y) != dim:
                        continue  # checking just determined distance
                    pos = {'X': ini_pos['X'] + x, 'Y': ini_pos['Y'] + y, 'Map': ini_pos['Map']}
                    if (int(pos['X'] / 8), int(pos['Y'] / 8)) == (int((ini_pos['X']) / 8), int((ini_pos['Y']) / 8)):
                        continue
                    if (chunk_in_list(pos, mine_spots, 8) or player_inside(pos) or
                            len(get_land_resources(pos, ["rock"], 2)) < 2):
                        continue  # position to move is inside the rock (invalid)
                    mine_spots.append(pos)
                    get_spots(pos, inside, mine_spots)
    return mine_spots


def calculate_route(points, tsp_algorithm):
    def calculate_distance(point1, point2):
        return max(abs(point1[0] - point2[0]), abs(point1[1] - point2[1]))

    def calculate_all_distances():
        """Precompute distances between all pairs of points."""
        num_points = len(points)
        dist_matrix = [[0] * num_points for _ in range(num_points)]
        for i in range(num_points):
            for j in range(i + 1, num_points):
                dist = calculate_distance(points[i], points[j])
                dist_matrix[i][j] = dist_matrix[j][i] = dist
        return dist_matrix

    dist_matrix = calculate_all_distances()
    return tsp_algorithm(points, dist_matrix)


def greedy_tsp(points, dist_matrix):
    start_index = 0
    path = [start_index]
    total_length = 0
    visited = {start_index}

    while len(visited) < len(points):
        nearest_index, nearest_distance = min(
            ((i, dist_matrix[path[-1]][i]) for i in range(len(points)) if i not in visited),
            key=lambda x: x[1]
        )

        visited.add(nearest_index)
        path.append(nearest_index)
        total_length += nearest_distance

    # Do not return to start; just calculate the path traversed
    return [points[i] for i in path]


def complement_route(m_path, inside=True):
    def distance(p1, p2):
        return max(abs(p1[0] - p2[0]), abs(p1[1] - p2[1]))

    if (not use_teleport) or (not inside):
        return m_path

    for _ in range(100):
        if m_path:
            for i in range(len(m_path)):
                if i >= len(m_path) - 1:
                    return m_path
                point1, point2 = m_path[i], m_path[i + 1]
                if distance(point1, point2) > 10:
                    selected = point1
                    for point in m_path:
                        if distance(point1, point) <= 10 and distance(point, point2) < distance(selected, point2):
                            selected = point
                    if selected != point1:
                        m_path.insert(i + 1, selected)
                        break
    return m_path


def try_move(char_pos, pos, inside=True, teleport_moves=True):
    def cast_teleport():
        check_beetles_close()
        wait_needs()
        wait_recovery()
        wait_mana()
        Spells.CastMagery("Teleport")
        Target.WaitForTarget(4000, False)
        tile_info = Statics.GetStaticsTileInfo(pos['X'], pos['Y'], pos['Map'])
        s_id = tile_info[0].StaticID if tile_info else 0
        Target.TargetExecute(pos['X'], pos['Y'], Player.Position.Z, s_id)
        Timer.Create("teleport", 5000)
        Timer.Create("recovery", spell_recovery)

    def walk():
        path = PathFinding.GetPath(pos['X'], pos['Y'], True)
        if not path:
            ignored_tile_list.append([pos['X'], pos['Y'], pos['Map']])
            return False
        if len(path) > 20:
            return False
        for i in range(0, len(path), 3):
            if not inside and player_inside({'X': Player.Position.X, 'Y': Player.Position.Y, 'Map': Player.Map}):
                return False
            if not PathFinding.RunPath(path[i:i + 3], 5000, False, True):
                return False
            if not (find_beetle('fire') and ((not with_blue) or find_beetle('blue'))):
                Misc.Pause(1000)
                check_beetles_close()
        return True

    if inside and teleport_moves:
        cast_teleport()
        for _ in range(15):
            Misc.Pause(100)
            uoalive_check_save()
            if Journal.Search("That location is blocked."):
                ignored_tile_list.append([pos['X'], pos['Y'], pos['Map']])
                ignored_file.write([[str(pos['X']), str(pos['Y']), str(pos['Map'])]])
                Journal.Clear()
                return False
            for msg in ["Target cannot be seen.", "That is too far away."]:
                if Journal.Search(msg):
                    Journal.Clear()
                    return False
            if Journal.Search("You have not yet recovered from casting a spell."):
                Journal.Clear()
                Misc.Pause(500)
                cast_teleport()
                Misc.Pause(1000)
            if not still(char_pos):
                return True
        ignored_tile_list.append([pos['X'], pos['Y'], pos['Map']])
    else:
        return walk()
    return False


def move():
    global mine_path, path_idx
    char_pos = {'X': Player.Position.X, 'Y': Player.Position.Y, 'Map': Player.Map}
    wait_path()
    Journal.Clear()
    while path_idx < len(mine_path):
        Target.Cancel()
        pos = {'X': mine_path[path_idx][0], 'Y': mine_path[path_idx][1], 'Map': char_pos['Map']}
        path_idx += 1
        inside = True if player_inside(char_pos) else False
        if dist(pos) <= 10 if inside else 20:
            if try_move(char_pos, pos, inside, use_teleport):
                return True
    return False


def get_land_resources(pos, resources, radius=2):
    land_resources = []
    for x in range(-radius, radius + 1):
        for y in range(-radius, radius + 1):
            land_id = Statics.GetLandID(pos['X'] + x, pos['Y'] + y, pos['Map'])
            land_name = Statics.GetLandName(land_id)
            if land_name in resources:
                land_resources.append(land_name)
    return land_resources


def journal_find(msg_list, display_color=90, display_msg="msg"):
    for msg in msg_list:
        if Journal.Search(msg):
            m = Journal.GetLineText(msg)
            if display_msg:
                display_msg = m if display_msg == "msg" else display_msg
                Player.HeadMessage(display_color, display_msg)
            Journal.Clear(m)
            return m
    return ''


def mine():
    global mine_path

    while not Player.IsGhost:

        if recalling_home():
            manual_unload()

        if not needs_running:
            t_init(lambda: check_needs())
        Misc.Pause(200)

        if recalling():
            continue

        Misc.SetSharedValue('ready_to_recall', False)

        char_pos = {'X': Player.Position.X, 'Y': Player.Position.Y, 'Map': Player.Map}
        resource = get_first(get_land_resources(char_pos, ["rock", "sand"]))
        if not resource or journal_find(["There is no metal here to mine.", "There is no sand here to mine.",
                                         "You can't mine there."], 1254, "Nothing to mine here!"):
            if recalling():
                continue
            check_beetles_close()
            if not move():
                Player.HeadMessage(45, "Mine was completed.")
                wait_recovery()
                wait_mana()
                wait_needs()
                check_beetles_close()
                mine_path = []
                if not recall_next_mine():
                    Misc.SendMessage("Failed to recall 5 times. Waiting manual move.", 38)
                    while still(char_pos):
                        Misc.Pause(50)
            continue

        journal_find(["You have found a"], 1266)

        if heavy():
            wait_needs()
            if recalling():
                continue
            if heavy() and ((not with_blue) or beetle_store() == "heavy"):
                check_beetles_close()
                wait_recovery()
                wait_mana()
                wait_needs()
                mine_path = []
                recall_home()
                deposit()
                check_beetles_close()
                recall_next_mine()

        if recalling():
            continue

        if not path_running:
            t_init(lambda: check_path())

        dismount()
        mining_tool = get_first(get_tools(mining_tools_ids))
        if mining_tool:
            Target.TargetResource(mining_tool.Serial, resource)


def check_needs():
    global needs_running
    if recalling():
        return
    needs_running = True
    if not Player.IsGhost:
        smelt()
        group_ores()
        if len(get_tools(mining_tools_ids)) <= 1:
            Player.HeadMessage(2125, 'making more tools!!')
            make_tool()
        Gumps.CloseGump(crafting_gump_id)
    needs_running = False


def check_path():
    global mine_path, path_idx, path_running
    if mine_path or recalling():
        return
    path_running = True
    char_pos = {'X': Player.Position.X, 'Y': Player.Position.Y, 'Map': Player.Map}
    mine_path = complement_route(calculate_route([(tile['X'], tile['Y'])
                                                  for tile in get_spots(char_pos, player_inside(char_pos))],
                                                 greedy_tsp),
                                 True if player_inside(char_pos) else False)
    path_idx = 0
    path_running = False


def t_init(func):
    threading.Thread(target=func, daemon=True).start()


ignored_file = File("Data/mining_ignored_tiles.txt")
ignored_file_txt = ignored_file.read()
ignored_tile_list = [[int(ele) for ele in tile_str] for tile_str in ignored_file_txt]
mine_path = []
path_idx = 0
needs_running = False
path_running = False
with_blue = config_beetles()
crafting_gump_id = get_shared("crafting_gump_id")
Journal.Clear()
mine()

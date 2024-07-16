import re
import sys
import threading
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

ore_filter = Items.Filter()
ore_filter.Graphics.AddRange(ores_ids)


def get_first(item_list):
    if item_list:
        return item_list[0]
    return None


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


def find_forge():
    return get_first(get_from_ground(fire_beetle_id))


def check_beetles_close():
    if find_beetle('fire') and ((not with_blue) or find_beetle('blue')):
        return
    for _ in range(3):
        Player.ChatSay(90, "all come")
        Misc.Pause(5000)
        if find_beetle('fire') and ((not with_blue) or find_beetle('blue')):
            return
    Misc.SendMessage("Error: Beetle is lost. Check this manually. FINISHING.", 38)
    sys.exit()


def wait_needs():
    if needs_running:
        Misc.SendMessage("Waiting smelt/create tools to finish.", 90)
        while needs_running:
            Misc.Pause(100)


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

    def wait_transfer(timeout):
        for _ in range(int(timeout/100)):
            Misc.Pause(100)
            it = Items.FindBySerial(item.Serial)
            to_container_contents = Items.FindBySerial(to_container).Contains
            if not it or it.Serial in [i.Serial for i in to_container_contents] or it.Amount < i_amount:
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
                    if dist(to_container) > 2:
                        break
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


def group_ores():
    to_group = [ore for ore in Items.ApplyFilter(ore_filter) if (ore.ItemID == 0x19B7 and ore.Amount == 1)]
    for ore in to_group:
        to_target = [o for o
                     in Items.FindAllByID(ores_ids, ore.Hue, Player.Backpack.Serial, True, True)
                     if o.Serial != ore.Serial]
        target_ore = get_first(to_target)
        if target_ore:
            Items.UseItem(ore)
            Target.WaitForTarget(1000)
            Target.TargetExecute(target_ore)
            Misc.Pause(200)
    return True


def smelt():
    if get_first(get_land_resources({'X': Player.Position.X, 'Y': Player.Position.Y, 'Map': Player.Map})):
        ores = [ore for ore in Items.ApplyFilter(ore_filter) if not (ore.ItemID == 0x19B7 and ore.Amount == 1)]
        if ores:
            for _ in range(2):
                forge = find_forge()
                if forge:
                    for ore in ores:
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


def get_land_resources(pos, radius=2):
    land_resources = []
    for x in range(-radius, radius + 1):
        for y in range(-radius, radius + 1):
            land_id = Statics.GetLandID(pos['X'] + x, pos['Y'] + y, pos['Map'])
            land_name = Statics.GetLandName(land_id)
            if land_name in ["rock", "sand"]:
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
    global ignored_tile_list

    while not Player.IsGhost:

        if not needs_running:
            t_init(lambda: check_needs())
        Misc.Pause(200)

        char_pos = {'X': Player.Position.X, 'Y': Player.Position.Y, 'Map': Player.Map}
        resource = get_first(get_land_resources(char_pos))
        if not resource or journal_find(["There is no metal here to mine.", "There is no sand here to mine.",
                                         "You can't mine there."], 90, "Nothing to mine here!"):
            if resource:
                ignored_tile_list = refresh_ignore()
                ignored_tile_list.append({'tile': {'X': Player.Position.X, 'Y': Player.Position.Y, 'Map': Player.Map},
                                          'time': datetime.now()})
            while still(char_pos):
                Misc.Pause(50)
            continue

        journal_find(["You have found a"], 1266)

        if heavy():
            wait_needs()
            if heavy() and (not with_blue):
                beetle_store()

        dismount()
        mining_tool = get_first(get_tools(mining_tools_ids))
        if mining_tool:
            Target.TargetResource(mining_tool.Serial, resource)


def check_needs():
    global needs_running
    needs_running = True
    if not Player.IsGhost:
        smelt()
        group_ores()
        if len(get_tools(mining_tools_ids)) <= 1:
            Player.HeadMessage(2125, 'making more tools!!')
            make_tool()
        Gumps.CloseGump(crafting_gump_id)
    needs_running = False


def t_init(func):
    threading.Thread(target=func, daemon=True).start()


needs_running = False
with_blue = config_beetles()
ignored_tile_list = []
temp_ignored_tile_list = []
crafting_gump_id = get_shared("crafting_gump_id")
Journal.Clear()
mine()

import re
from AutoComplete import *

minimum_gold_to_send = 10000
garbage_names = ["Bightsight Lenses"]


def get_first(item_list):
    if item_list:
        return item_list[0]
    return None


def both_messages(msg, color):
    Misc.SendMessage(msg, color)
    Player.HeadMessage(color, msg)


def heavy(weight_limit=.8 * Player.MaxWeight):
    return Player.Weight >= weight_limit and not Player.IsGhost


def find_prop_value(item, prop):
    item_props = "|".join([str(p).lower() for p in item.Properties])
    if prop.lower() in item_props:
        value_list = item_props.split(prop.lower())
        if len(value_list) > 1:
            value = "/".join(re.findall(r'\d+', value_list[1].split("|")[0]))
            return value if value else prop
        return prop
    return ''


def wait_move(item, old_container):
    Timer.Create("move", 2000)  # move timeout
    while Timer.Check("move"):
        if item.Serial not in [i.Serial for i in old_container.Contains]:
            break
        Misc.Pause(50)


def find_items_list(item_id_list, container, color=-1, recursive=True):
    def compare_names(item_name1, item_name2):
        if type(item_name1) is str and type(item_name2) is str:
            return item_name1.lower() == item_name2.lower()
        return False

    found_items = []
    try:
        _ = container.Serial
    except Exception:
        container = Items.FindBySerial(container)
    for item_id in item_id_list:
        for item in container.Contains:
            if item_id == item.ItemID or compare_names(item.Name, item_id):
                if color >= 0:
                    if int(color) == int(item.Hue):
                        found_items.append(item)
                else:
                    found_items.append(item)
            if item.IsContainer and recursive:
                found_items.extend(find_items_list(item_id_list, item, color, True))
    return found_items


def send_gold():
    gold_piles = find_items_list([0x0EED], Player.Backpack)
    bags = [bag for bag in find_items_list(['A Bag Of Sending'], Player.Backpack) if bag not in ignored_bags]
    for gold in gold_piles:
        if gold.Amount < minimum_gold_to_send:
            continue
        for bag in bags:
            if bag.Serial in ignored_bags:
                continue
            bag_charges = int(find_prop_value(bag, "charges"))
            if bag_charges <= 0:
                powder = Items.FindByID(0x26B8, -1, Player.Backpack.Serial, True, True)
                if powder:
                    powder_old_amount = powder.Amount
                    Items.UseItem(powder)
                    Target.WaitForTarget(3000, False)
                    Target.TargetExecute(bag)
                    for _ in range(20):
                        Misc.Pause(100)
                        powder = Items.FindBySerial(powder.Serial)
                        if not powder or powder.Amount < powder_old_amount:
                            both_messages("Bag of Sending Recharged", 90)
                            break
                        if Journal.Search("This item has been oversaturated "):
                            both_messages(Journal.GetLineText("This item has been oversaturated "), 90)
                            break
            if bag_charges > 0 or int(find_prop_value(bag, "charges")) > 0:
                Items.UseItem(bag)
                Target.WaitForTarget(3000, False)
                Target.TargetExecute(gold)
                wait_move(gold, Player.Backpack)
                both_messages("Gold was sent to your Bank.", 48)
                return True
            ignored_bags.append(bag.Serial)
            Misc.Pause(1000)


def find_available_tile():
    for x in [0, -1, 1]:
        for y in [0, -1, 1]:
            if (x, y) == (0, 0):
                continue
            tile = (Player.Position.X + x, Player.Position.Y + y, Player.Map)
            z = Statics.GetLandZ(tile[0], tile[1], tile[2])
            if PathFinding.GetPath(tile[0], tile[1], True) and abs(z - Player.Position.Z) <= 1:
                return tile
    return Player.Position.X, Player.Position.Y - 1, Player.Map


def throw_garbage_away():
    garbage_list = find_items_list(garbage_names, Player.Backpack)
    if garbage_list:
        both_messages("Throwing garbage away.", 58)
        for garbage in garbage_list:
            tile = find_available_tile()
            Items.MoveOnGround(garbage, 0, tile[0], tile[1], tile[2])
            wait_move(garbage, Player.Backpack)


def weight_handler():
    while True:
        throw_garbage_away()
        if heavy():
            send_gold()
        Misc.Pause(1000)


ignored_bags = []
weight_handler()

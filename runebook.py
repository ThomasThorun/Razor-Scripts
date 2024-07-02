from AutoComplete import *


def get_shared(name):
    return int(Misc.ReadSharedValue(name))


def set_shared_gump(name, gump_num):
    if gump_num != get_shared(name):
        Misc.SetSharedValue(name, gump_num)
    return gump_num


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


def uoalive_check_save():
    if Journal.Search("The world is saving, please wait."):
        Misc.Pause(3000)
        Journal.Clear()


def set_rune_pos(book, rune_pos):
    pos = (rune_pos + 1) % (16 if book.ItemID == 0x22C5 else 48)
    return pos if pos != 0 else 1


def page_has(extra_arg=''):
    gump_txt_data = str("".join([text for text in Gumps.LastGumpRawText() if text]))
    if 'Max Charges' in gump_txt_data or 'Replace' in gump_txt_data:
        if not extra_arg or (extra_arg and extra_arg in gump_txt_data):
            return True
    return False


def get_runebook(r_type=''):
    global book_gump_id

    def get_runes():
        rune_list = []
        for _ in range(2):
            if prev_btn in Gumps.GetGumpRawData(book_gump_id):
                Gumps.SendAction(book_gump_id, 1151)
                Gumps.WaitForGump(book_gump_id, 5000)
        for _ in range(2):
            gump_text = [item for item in Gumps.GetGumpRawText(book_gump_id) if item and "<center>" not in item]
            rune_list.extend(gump_text[1 if book.ItemID in [0x9C16, 0x9C17] else 4:
                                       gump_text.index("Empty") if "Empty" in gump_text else gump_text.index("Replace")])
            if "Empty" in gump_text:
                break
            if next_btn in Gumps.GetGumpRawData(book_gump_id):
                Gumps.SendAction(book_gump_id, 1150)
                Gumps.WaitForGump(book_gump_id, 5000)
        Gumps.CloseGump(book_gump_id)
        return rune_list

    Misc.SendMessage("Doing Runic Atlas/Runebook configs.", 90)
    books = Items.FindAllByID([0x9C16, 0x9C17, 0x22C5], -1, Player.Backpack.Serial, -1, True)
    next_btn = "{ button 374 3 2206 2206 1 0 1150 }"
    prev_btn = "{ button 23 5 2205 2205 1 0 1151 }"
    for book in books:
        print(book)
        book_gump_id = set_shared_gump("book_gump_id", open_book_gump(book))
        for _ in range(2):
            if page_has(r_type) > 0:
                Misc.SendMessage("Atlas/Runebook config done!", 90)
                return book, get_runes()
            if next_btn in Gumps.GetGumpRawData(book_gump_id):
                Gumps.SendAction(book_gump_id, 1150)  # next page
                Gumps.WaitForGump(book_gump_id, 4000)
        Gumps.CloseGump(book_gump_id)
        Misc.Pause(500)
    Misc.SendMessage("Error: " + r_type + " runebook not found. Working with no recalls.", 38)
    return None, []


def open_book_gump(book):
    old_gump = Gumps.CurrentGump()
    for _ in range(3):
        Items.UseItem(book)
        for _ in range(200):
            Misc.Pause(10)
            if Gumps.CurrentGump() != old_gump:
                break
        if Gumps.CurrentGump() != old_gump:
            break
    return Gumps.CurrentGump()


def recall(book, rune_pos, rune_name='', gate=False):
    global book_gump_id

    def get_recall_button():
        def use_recall():
            return Player.GetSkillValue('Magery') >= Player.GetSkillValue('Chivalry')

        #  runebook buttons: recall = 50 to 65, sacred journey = 75 to 90, gate travel = 100 to 115
        # runic rune buttons = 100 to 147
        runic_buttons = {'rename_book': 1, 'set_default': 2, 'drop_rune': 3, 'replace_rune': 8, 'recall': 4,
                         'gate_travel': 6, 'sacred_journey': 7, 'next_page': 1150, 'previous_page': 1151}
        if book.ItemID == 0x22C5:  # runebook
            return (rune_pos + 100 if gate else (rune_pos + 50 if use_recall() else rune_pos + 75)), None
        if book.ItemID in [0x9C16, 0x9C17]:  # runic atlas
            return rune_pos + 100, (6 if gate else
                                    (runic_buttons['recall'] if use_recall() else runic_buttons['sacred_journey']))
        Misc.SendMessage("Error: book not found", 38)
        return None, None

    def recall_success():
        Journal.Clear()
        hp = Player.Hits
        old_pos = {'X': Player.Position.X, 'Y': Player.Position.Y, 'Map': Player.Map}
        for _ in range(500):
            Misc.Pause(10)
            uoalive_check_save()
            if (Journal.Search("Something is blocking the location.") or
                    Journal.Search(Player.Name + ": The spell fizzles.") or (hp > Player.Hits > 0)):
                Misc.SendMessage("Recall failed to: " + rune_name, 38)
                return False
            if Journal.Search("Insufficient mana. You must have at least "):
                Misc.SendMessage("Recall failed to: " + rune_name, 38)
                Player.UseSkill('Meditation')
                Misc.Pause(10000)
                return recall(book, rune_pos, rune_name, gate)
            if dist(old_pos) > 20:
                return True
        return True

    if not book:
        return False
    if Gumps.WaitForGump(book_gump_id, 100) <= 0:
        book_gump_id = open_book_gump(book)
    first_button, second_button = get_recall_button()
    if first_button:
        Gumps.WaitForGump(book_gump_id, 4000)
        Gumps.SendAction(book_gump_id, first_button)
    if second_button:
        Gumps.WaitForGump(book_gump_id, 4000)
        Gumps.SendAction(book_gump_id, second_button)
        Player.HeadMessage(65, "Recalling to: " + rune_name)
    return recall_success()


book_gump_id = get_shared("book_gump_id")

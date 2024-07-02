from AutoComplete import *

"""
def get_resource_name():
    for x in range(-2, 3):
        for y in range(-2, 3):
            tile_pos = (Player.Position.X + x, Player.Position.Y + y, Player.Map)
            land_id = Statics.GetLandID(tile_pos[0], tile_pos[1], tile_pos[2])
            statics_tiles = Statics.GetStaticsTileInfo(tile_pos[0], tile_pos[1], tile_pos[2])
            land_name = Statics.GetLandName(land_id)
            print(land_name, "" if x!=0 or y!=0 else "i'm here")
            if statics_tiles:
                print(statics_tiles)
    return
    
get_resource_name()
    
for i in range(100):
    Misc.SendMessage("color" + str(i), i)
    Misc.Pause(100)
"""

#for gump in Gumps.AllGumpIDs():
 #   print("|".join(Gumps.GetLineList(gump)))
    #print(Gumps.GetGumpRawData(gump))


def get_gump_num(text_list, timeout=4000):
    for _ in range(int(timeout / 100)):
        for text in text_list:
            if Gumps.LastGumpTextExist(text):
                return Gumps.CurrentGump()
        Misc.Pause(100)
    return 0


book_gump_id = int(Misc.ReadSharedValue("book_gump_id"))
print(book_gump_id)
Gumps.SendAction(book_gump_id, 110)

'''
for gump in Gumps.AllGumpIDs():
    Misc.SendMessage("Testing 'get gump funcs' Gump: " + str(gump) + ":", 48)
    print('Gumps.GetGumpRawText:', Gumps.GetGumpRawText(gump))
    print('Gumps.GetLineList: ', Gumps.GetLineList(gump))
    # print(Gumps.GetGumpData(gump))  # also show nothing, don't have similar in Last Gump funcs to compare
    # print('Gumps.GetGumpRawData:', Gumps.GetGumpRawData(gump))  # working - same result on both


Misc.SendMessage("Testing 'last gump funcs' Gump: " + str(Gumps.CurrentGump()) + ":", 90)
print('Gumps.LastGumpRawText:', Gumps.LastGumpRawText())
print('Gumps.LastGumpGetLineList:', Gumps.LastGumpGetLineList())
# print('Gumps.LastGumpGetLineList:', Gumps.LastGumpRawData())   # working - same result on both
'''
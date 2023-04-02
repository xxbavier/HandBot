def make_players_string(list_of_players):
    string = ""

    for player in list_of_players:
        string += "{} ({})\n".format(player.mention, player.name)
    
    return string


def get_members_from_string(string, htl):
    members = []

    string = string.split(" ")

    for word in string:
        if word.startswith("<@") and word.endswith(">"):
            id = ""

            for i in word:
                if i.isdigit():
                    id += str(i)

            id = int(id)
            
            if htl.get_member(id):
                members.append(htl.get_member(id))
    
    return members

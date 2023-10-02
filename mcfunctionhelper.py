import json

player_dat_file = "data/players.json"


def getPlayerById(player_id):
    with open(player_dat_file, "r") as file:
        data = json.load(file)
        result = data.get(str(player_id))
        if result:
            return result["name"]
        else:
            return f"No player found with ID: {player_id}"


def getPlayerIdByName(player_name):
    with open(player_dat_file, "r") as file:
        data = json.load(file)
        for player_id, player_data in data.items():
            if player_data["name"].lower() == player_name.lower():
                return int(player_id)
        return None

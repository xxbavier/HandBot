import os, json, requests

try:
    rover_key = os.environ["rover_api_key"]
except KeyError:
    with open("config.json", "r") as file:
        data = json.load(file)
        rover_key = data["rover_api_key"]

base_url = "https://registry.rover.link/api"

def get_Roblox(guild_id: int, discord_id: int):
    data = requests.get("{}/guilds/{}/discord-to-roblox/{}".format(base_url, guild_id, discord_id), headers={
        "Authorization": "Bearer {}".format(rover_key)
    })

    data = data.content.decode("utf-8")
    data = json.decoder.JSONDecoder().decode(data)
    
    return data
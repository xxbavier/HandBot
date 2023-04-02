import pymongo
from pymongo.errors import ConnectionFailure
from pymongo import InsertOne, DeleteOne, ReplaceOne
import os
import json

try:
    mongoLogIn = os.environ["MONGO_ACCESS"]
except KeyError:
    with open("config.json", "r") as file:
        data = json.load(file)
        mongoLogIn = data["db_connection"]

mongoClient = pymongo.MongoClient(mongoLogIn)

try:
    mongoClient.admin.command("ping")
except ConnectionFailure:
    print("MongoDB server is not available.")

databases = {
    "Player Data": mongoClient["Player_Data"],
    "Contracts": mongoClient["Contracts"],
    "Demands": mongoClient["Demands"],
    "Season Info": mongoClient["SeasonInfo"]
}
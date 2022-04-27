import asyncio
import traceback
from pavlov import PavlovRCON
import threading
from time import sleep
serverIP = "0.0.0.0"
serverPORT = "1234"
RCONPassword = "password"

ignoreBalancePlayers = []

# Created by Zackyy | 27.04.2022
# Github: https://github.com/Zackyy1
# Discord: Zackyy#8898
# ------------------------------------------------\
#         ______           _                       |
#        |___  /          | |                      |
#           / /  __ _  ___| | ___   _ _   _        |
#          / /  / _` |/ __| |/ / | | | | | |       |
#        ./ /__| (_| | (__|   <| |_| | |_| |       |
#        \_____/\__,_|\___|_|\_\\__, |\__, |       |
#                                __/ | __/ |       |
#                               |___/ |___/        |
# ------------------------------------------------/

# ------------------ CONFIG ------------------
# Adjust these values to your needs
setCashForSwitchedPlayers = True
cashAmountForSwitchedPlayers = 4200 # Switched players start with 900, so you can change their Cash manually

# ------------------ CONFIG ------------------

def startServer():
    try:
        asyncio.get_event_loop().run_until_complete(Server(PavlovRCON(serverIP, int(serverPORT), RCONPassword)))
    except Exception as err:
        print(f'Server crashed: {err}')
        traceback.print_exc() # If any errors come up, it will tell where exactly

        startServer()

async def balanceTeams(pavlov, PLAYERS, SERVER_INFO):
    global ignoreBalancePlayers
    playersInT0 = []
    playersInT1 = []
    team0Score = int(SERVER_INFO['ServerInfo']['Team0Score'])
    team1Score = int(SERVER_INFO['ServerInfo']['Team1Score'])
    
    try:
        for player in PLAYERS:
            playerData = await pavlov.send(f"InspectPlayer {player['UniqueId']}")
            playerTeam = int(playerData["PlayerInfo"]['TeamId'])

            if playerData["PlayerInfo"]['UniqueId'] not in ignoreBalancePlayers:
                if playerTeam == 0:
                    playersInT0.append(playerData)
                elif playerTeam == 1:
                    playersInT1.append(playerData)

        if team0Score != 10 and team1Score != 10:
            try:
                if (len(playersInT0) - len(playersInT1) >= 2):
                    playerToSwitchID = sorted(playersInT0, key=lambda k: k["PlayerInfo"]['Score'])[0]["PlayerInfo"]['UniqueId']
                    ignoreBalancePlayers.append(playerToSwitchID)
                    await pavlov.send(f'SwitchTeam {playerToSwitchID} 1')
                    if setCashForSwitchedPlayers:
                        await pavlov.send(f'SetCash {playerToSwitchID} {str(cashAmountForSwitchedPlayers)}')
            except:
                pass

            try:
                if (len(playersInT1) - len(playersInT0) >= 2):
                    playerToSwitchID = sorted(playersInT1, key=lambda k: k["PlayerInfo"]['Score'])[0]["PlayerInfo"]['UniqueId']
                    ignoreBalancePlayers.append(playerToSwitchID)
                    await pavlov.send(f'SwitchTeam {playerToSwitchID} 0')
                    if setCashForSwitchedPlayers:
                        await pavlov.send(f'SetCash {playerToSwitchID} {str(cashAmountForSwitchedPlayers)}')

            except:
                pass

    except Exception as err:
        print(f'Error during team balancing: {err}')


async def Server(pavlov):
    print(f"RCON Autobalancer started")

    roundEndDebouncer = False

    while True:
        SERVER_INFO = await pavlov.send("ServerInfo")
        try:    
            if SERVER_INFO and SERVER_INFO['ServerInfo']:
                round = 0
                ROUND_STATE = SERVER_INFO["ServerInfo"]["RoundState"]
                PLAYER_INFO = await pavlov.send("RefreshList")
                PLAYERS = PLAYER_INFO["PlayerList"]

                try:
                    team0 = int(
                        SERVER_INFO["ServerInfo"]["Team0Score"])
                    team1 = int(
                        SERVER_INFO["ServerInfo"]["Team1Score"])
                    round = team0 + team1 + 1
                except:
                    team0 = 10
                    team1 = 10
                    round = 0

                if ROUND_STATE == "Ended" and roundEndDebouncer == False:
                    roundEndDebouncer = True
                    if team0 == 10 or team1 == 10 or round < 3:
                        global ignoreBalancePlayers
                        ignoreBalancePlayers = []
                    elif (round > 3):
                        await balanceTeams(pavlov, PLAYERS, SERVER_INFO)
                        pass
                elif ROUND_STATE == "Started" or ROUND_STATE == "StandBy":
                    roundEndDebouncer = False

        except:
            traceback.print_exc()

        sleep(2)


startServer()



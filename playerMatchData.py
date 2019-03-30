import requests
import sqlite3
## see API call limit comment ~ line 59
# from time import sleep

db = sqlite3.connect('matchId.db')
c = db.cursor()

c.execute('DROP TABLE IF EXISTS matches;')
c.execute('DROP TABLE IF EXISTS champ_info;')
c.execute('DROP TABLE IF EXISTS match_info;')

# Create table with match ID, champion
c.execute('''CREATE TABLE matches(match_ID int, champion_ID text)''')

# create table with champion names and their ids
c.execute('''CREATE TABLE champ_info(champion_name text, champion_ID text)''')

# create table with match ID, win/loss, teammate champions, enemy champions
c.execute('''CREATE TABLE match_info(match_ID int, win_loss text, champion_id text, teammates text, enemies text)''')

# get the summoner object 

base = 'https://na1.api.riotgames.com'
summoner_name = 'danthebrohan'
summoner_name_call = '/lol/summoner/v4/summoners/by-name/' + summoner_name
api_key = '?api_key=RGAPI-9fe881f0-ec0a-42d2-be08-748a0cb597db'
summoner_object = requests.get(base+summoner_name_call+api_key).json()
all_champions_call = 'http://ddragon.leagueoflegends.com/cdn/6.24.1/data/en_US/champion.json'
match_call = '/lol/match/v4/matches/' # +matchID

# use summoner object information to get list of matches
summoner_accountId = summoner_object['accountId']
summoner_match_call = '/lol/match/v4/matchlists/by-account/'+summoner_accountId
matches_object = requests.get(base+summoner_match_call+api_key).json()
matches_array = matches_object['matches']
match_id_list = []
matches = []

# put matches into sqlite
for match in matches_array:
	row_data = (match['gameId'], match['champion'])
	c.execute('''INSERT INTO matches(match_ID,champion_ID) VALUES (?,?)''', (row_data))
	match_id_list.append(str(match['gameId']))

# get champion information and put into sqlite
all_Champions_object = ((requests.get(all_champions_call)).json())['data']
for key in all_Champions_object:
	row_data = (key, all_Champions_object[key]["key"])
	c.execute('''INSERT INTO champ_info(champion_name, champion_ID) VALUES (?,?)''', (row_data))

# get win/loss, and teammates, and enemies per match 
# for match_ID in match_id_list:
match_info = []
champion_win_loss_combinations = []

## function for handling champion_win_loss_combinations

def champ_win_loss_combo(champ_id, win_loss, teammates):
	win_loss_Obj = {}
	teammate_list = teammates.split(",")
	records_Obj = {}
	if len(champion_win_loss_combinations) == 0:
		if win_loss == 'win':
			for teammate in teammate_list:
				records_Obj[teammate] = [1, 0]
			win_loss_Obj = { champ_id : records_Obj}
		if win_loss == 'loss':
			for teammate in teammate_list:
				records_Obj[teammate] = [0, 1]
			win_loss_Obj = { champ_id : records_Obj}



	champion_win_loss_combinations.append(win_loss_Obj)

	print(win_loss_Obj)


# check if champ_id exists
# if it does not, create an object like so 
#{ "76" : {"12" : [1, 0], "14" : [0, 2], "11" : [1, 1] } }



for each_match in match_id_list[:50]:
	match_info = requests.get(base+match_call+each_match+api_key).json()
	matches.append(match_info)

#### API CALL LIMIT ISSUE FROM THE FOR LOOP ABOVE ####
## api call limit will break the code, can use sleep function temporarily 
## otherwise just setting matches to limit 50 
	# sleep(2)


# grab all the participant IDs and player names 
	participant_identities = match_info['participantIdentities']
	participants = match_info['participants']
	teams = match_info['teams']
# create list for participant ID and name 
	name_and_ID = []	

# access info in participantIdentities and put each player into { summonerName, partId}
	for participant_ident in participant_identities:
		name_ID_Obj = { 'summonerName': participant_ident['player']['summonerName'], 'partID': participant_ident['participantId'] } 
		name_and_ID.append(name_ID_Obj)

# use part_id to get win/loss
	summoner_part_id = ''
	win_loss = ''
	summoner_team_id = ''
	teammates = ''
	enemies = ''
	champion_id = ''
# use ID of summoner to determine win / loss and teammates vs enemies
	for player in name_and_ID:
		if player['summonerName'] == summoner_name:
			summoner_part_id = player['partID']

# access info in participants object 
	# identify summoner team ID
	for participant in participants:
		if participant['participantId'] == summoner_part_id:
			summoner_team_id = participant['teamId']
	# use it to identify teammates vs enemies
	for participant in participants:
		if summoner_part_id == participant['participantId']:
			champion_id = participant['championId']

		if summoner_part_id != participant['participantId']:
			if summoner_team_id == participant['teamId']:
				if teammates:
					teammates = teammates + ',' +  str(participant['championId'])
				else:
					teammates = str(participant['championId'])
			else: 
				if enemies:
					enemies = enemies + ',' + str(participant['championId'])
				else:
					enemies = str(participant['championId'])

# access info in team object
	for team in teams:
		if team['teamId'] == summoner_team_id:
			if team['win'] == 'Win':
				win_loss = 'win'
			if team['win'] == 'Fail':
				win_loss = 'loss'
		
	#row_data needs matchID, win/loss, teammates, enemies
	row_data = (each_match, win_loss, champion_id, teammates, enemies)
	champ_win_loss_combo(champion_id, win_loss, teammates)
	c.execute('''INSERT INTO match_info(match_ID, win_loss, champion_id, teammates, enemies) VALUES (?,?,?,?,?)''', (row_data))

## create a list of objects 
## each object has champion id, ally champion ids, and numbers of wins and losses
##[ { "76" : {"12" : [1, 0], "14" : [0, 2], "11" : [1, 1] } },
##  { "11" : {"17" : [2, 1], "23" : [4, 0], "12" : [2, 2] } } ]

## write a function or class to handle champion_win_loss_combo



db.commit()




#SQL query to see joined table of match id, champ id, and champion name
#select matches.match_ID, matches.champion_ID, champ_info.champion_name
#from matches
#left join champ_info on matches.champion_ID = champ_info.champion_ID


from Tkinter import *
from ttk import Separator
from tkMessageBox import *
from tkFileDialog import askopenfilename
from tkFont import Font
from glob import glob
from datetime import datetime
import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
import numpy as np
import pylab as pyl
import matplotlib.colors as colors
import os as os
import json, re
import sys
import shutil, time, math


#Important notes
#1) In order to create a full log file, players must first log out at the end of the round, then exit the server
#2) server ends when second to last player logs out?
#3) info.ini file must be in the same dir as this script

class FileNotFound(Exception):

	def __init__(self, value):
		self.value = value

	def __str__(self):
		return repr(self.value)


global_vars = {
	'ini_file_name':'info.ini',
	'ini_file':'',
	'log_file_name':'Launch.log',
	'records_file_name':'Records.xml',
	'sessions_file_name':'Sessions.xml',
	'poll_pkey':'CPIPOLLOUTPUT',
	'login_skey':'CPIPLAYERLOGIN',
	'logout_skey':'CPIPLAYERLOGOUT',
	'config_vars_pkey':'CPICONFIGVARS',
	'log_directory':"",
	'data_directory':"",
	'install_directory':'',
	'records_directory':"",
	'sessions_directory':"",
	'log_file':"",
	'sessions_file':"",
	'records_file':"",
	'MAX_CONFIG_VARIABLES':-1,
	'MAX_ROUNDS':-1,
	'MAX_SESSIONS':-1,
	'match_split_string':'LoadMap',
	'temp_directory':"",
	'MAX_PLAYERS':'32'
}


#global data/utility object
class SessionsObject:

	def __init__(self):
		self.settings_win = None
		self.extra_info_widget = None
		self.settings_vars = {}
		self.sessionsIDs = get_sessionIDs_from_sessions_file()
		self.sessions_widget = None
		self.config_vars_widget = None
		self.active_sessionID = None
		self.selected_sessionIDs = []
		self.selected_config_vars = set()
		#keep this list alphabetized
		#doesn't include RoundStartEvent
		self.all_events = ["HostageRescueEvent","KillEvent","KilledEvent","MarketTransactionEvent","ObjectiveEvent","PickupEvent"]
		self.event_types = {
			"HostageRescueEvent":"Hostage Rescue Events",
			"KillEvent":"Kill Events",
			"KilledEvent":"Killed Events",
			"MarketTransactionEvent":"Market Transaction Events",
			"ObjectiveEvent":"Objective Events",
			"PickupEvent":"Pickup Events",
			#"RoundStartEvent":"Round Start Events"
		}
		#self.available_colors = ['b','g','r','c','m','y']
		self.event_colors = {
			"HostageRescueEvent":'#4a4aff',
			"KillEvent":'#4aff4a',
			'KilledEvent':'#ff4a4a',
			"MarketTransactionEvent":'#4affff',
			"ObjectiveEvent":'#ff4aff',
			"PickupEvent":'#ffff4a',
			#"RoundStartEvent":"white"
		}
		self.default_player_event_filters = {
			# "RoundStartEvent" : {
				# "RoundNumber" : False,
				# "PlayerRoundStartAmounts" : {
					# "Wallet" : False,
					# "Player" : {
						# "PlayerID" : False,
						# "TeamIndex" : False
					# }
				# }
			# },
			"KilledEvent" : {
				"DropAmount" : True
			},
			"KillEvent" : {
				"KillerInventory" : {
					"Wallet" : True,
					"Weapon" : True,
					"PlayerInventory" : { #list
						"InventoryItem" : True,
						"AmmoCount" : True
					}
				},
				"KilledInventory" : {
					"Wallet" : True,
					"Weapon" : True,
					"PlayerInventory" : { #list
						"InventoryItem" : True,
						"AmmoCount" : True
					}
				},
				"Killed" : {
					"PlayerID" : True,
					"TeamIndex" : True
				}
			},
			"ObjectiveEvent" : True,
			"HostageRescueEvent" : {
				"RescuerID" : False
			},
			"PickupEvent" : {
				"InventoryBelt" : { #list
					"InventoryItem" : True,
						"AmmoCount" : True
				}, 
				"bIsCashReward" : True
			},
			"MarketTransactionEvent" : { #list
				"InventoryItem" : True, 
				"Quantity" : True
			}
		}

def set_globalvars():
	global global_vars
	try:
		curdir = os.path.dirname(os.path.realpath(__file__))
		if global_vars['ini_file_name'] not in os.listdir(curdir):
			raise FileNotFound(global_vars['ini_file_name'])
		else:
			file_name = curdir + '\\' + global_vars['ini_file_name']
			global_vars['ini_file'] = file_name
			try:
				ini_file = open(file_name, 'r')
			except IOError as e:
				print "I/O error({0}): {1}. Could not open file {2}".format(e.errno, e.strerror, file_name)
			else:
				try:
					global_vars['install_directory'] = curdir + '\\'
					global_vars['data_directory'] = global_vars['install_directory'] + 'Data' + '\\'
					global_vars['backup_directory'] = global_vars['data_directory'] + 'Log Backups' + '\\'
					for line in ini_file.readlines():
						ini_pair = line.split('=')
						if ini_pair[0] == 'log_directory':
							global_vars['log_directory'] = ini_pair[1][:-1]
						elif ini_pair[0] == 'data_directory':
							global_vars['data_directory'] = ini_pair[1][:-1]
						elif ini_pair[0] == 'MAX_CONFIG_VARIABLES':
							global_vars['MAX_CONFIG_VARIABLES'] = int(ini_pair[1])
						elif ini_pair[0] == 'MAX_ROUNDS':
							global_vars['MAX_ROUNDS'] = int(ini_pair[1])
						elif ini_pair[0] == 'MAX_SESSIONS':
							global_vars['MAX_SESSIONS'] = int(ini_pair[1])
						elif ini_pair[0] == 'MAX_PLAYERS':
							global_vars['MAX_PLAYERS'] = int(ini_pair[1])
						elif ini_pair[0] == 'log_file_name':
							global_vars['log_file_name'] = ini_pair[1][:-1]
						elif ini_pair[0] == 'records_file_name':
							global_vars['records_file_name'] = ini_pair[1][:-1]
						elif ini_pair[0] == 'sessions_file_name':
							global_vars['sessions_file_name'] = ini_pair[1][:-1]
						elif ini_pair[0] == 'poll_pkey':
							global_vars['poll_pkey'] = ini_pair[1][:-1]
						elif ini_pair[0] == 'login_skey':
							global_vars['login_skey'] = ini_pair[1][:-1]
						elif ini_pair[0] == 'logout_skey':
							global_vars['logout_skey'] = ini_pair[1][:-1]
						elif ini_pair[0] == 'config_vars_pkey':
							global_vars['config_vars_pkey'] = ini_pair[1][:-1]
					global_vars['sessions_directory'] = global_vars['data_directory'] + 'Sessions' + '\\'
					global_vars['records_directory'] = global_vars['data_directory'] + 'Records' + '\\'
					global_vars['tmp_directory'] = global_vars['data_directory'] + 'tmp' + '\\'
					global_vars['log_file'] = global_vars['log_directory'] + global_vars['log_file_name']
					global_vars['sessions_file'] = global_vars['sessions_directory'] + global_vars['sessions_file_name']
					global_vars['records_file'] = global_vars['records_directory'] + global_vars['records_file_name']
				except IOError as e:
					print "I/O error({0}): {1}. Could not set global variables".format(e.errno, e.strerror)
				except LookupError:
					print "Index or Key error. Could not set global variables"
			finally:
				if ini_file:
					ini_file.close()
				else:
					sys.exit()
	except OSError as e:
		print "I/O error({0}): {1}".format(e.errno, e.strerror)
		sys.exit()
	except FileNotFound as e:
		print "Error File not found: {0}".format(e.value)
		sys.exit()
	
#Workflow involves creating consecutive sessions:
#workflow is session based
#Clear log file
#Make config changes
#Play game
#make sure server log file is created properly (press ctrl+c twice to properly exit server terminal session)
#run bat file 'create_session_from_log.bat'
#create_session_from_log optionally takes a file argument
#if a file argument is not given, create_session_from_log creates a new session then deletes the log file
#session will automatically know which config vars were changed
#sessions correspond to zero or one or more config changes.
#records correspond to rounds
#
#To analyze results of config changes
#run bat file 'GameAnalyzer.bat'
#browse and select two sessions to compare
#changes to config vars will be displayed (independent variable)
#generate desired graph(s) (dependent variables)
#
#
#playerID's are unique per session
#

#Future Features
#record time player spends waiting, spectating, in the buy menu, etc.
#track individual players (eg real human players) over multiple sessions
#optionally remove players from data set
		
#@param	keystr	The tag in the log file
#@return	False if failed to get Json
def get_json_from_log(key_string, start_index=0, as_strings=False, return_first=False, log_file=global_vars['log_file']):
	global global_vars
	try:
		file = open(log_file, 'r')
		file_string = file.read()
		file.close()
	except IOError as e:
		print "I/O error({0}): {1}. Could not open or read file {2}".format(e.errno, e.strerror, log_file)
		return
	file_string = file_string[start_index:]
	if return_first:
		if not file_string.split(key_string):
			return False
		json_string = file_string.split(key_string)[1].split(key_string)[0]
		json_string = "{" + json_string.split("{",1)[1].rsplit("}",1)[0] + "}"
		if as_strings:
			return json_string
		else:
			return json.loads(json_string)
	else:
		json_string = file_string.split(key_string)
		if not json_string:
			return False
		json_string = json_string[1:]
		return_values = []
		loop_num = 0
		for return_value in json_string:
			if loop_num % 2 == 0:
				str_value = return_value.split(key_string)[0]
				str_value = "{" + str_value.split("{",1)[1].rsplit("}",1)[0] + "}"
				if as_strings:
					return_values.append(str_value)
				else:
					return_values.append(json.loads(str_value))
			loop_num = loop_num + 1
		return return_values;


def get_records_from_log_file(as_strings, log_file=global_vars['log_file']):
	global global_vars
	return get_json_from_log(global_vars['poll_pkey'], as_strings=as_strings, log_file=log_file)


#get all ID's from sessions in session file
def get_sessionIDs_from_sessions_file():
	global global_vars
	tree = ET.ElementTree()
	#TODO add exception handling for this xml parsing
	tree_parsed = tree.parse(global_vars['sessions_file'])
	sessionIDs = []
	for session in tree_parsed.findall('SESSION'):
		if session.attrib['sessionID'] not in sessionIDs:
			sessionIDs.append(session.attrib['sessionID'])
	return sessionIDs


def get_config_vars_from_log(log_file=global_vars['log_file']):
	global global_vars
	config_vars = get_json_from_log(global_vars['config_vars_pkey'], start_index=0, as_strings=False, return_first=True, log_file=log_file)
	return config_vars


#Data Structure (Players):
# [
#	 {
#		 'Player ID' : '1',
#		 'Name' : 'default-name',
#        'Team' : '1',
#		 'Login Time' : '34',
#		 'Logout Time' : '674',
#	 },
#	 ...
# ]
def get_players_from_log(log_file=global_vars['log_file']):
	global global_vars
	try:
		file = open(log_file, 'r')
		file_string = file.read()
		file.close()
	except IOError as e:
		print "I/O error({0}): {1}. Could not open or read file {2}".format(e.errno, e.strerror, log_file)
		return
	json_string = file_string.split(global_vars['login_skey'])
	json_string = json_string[1:]
	players = []
	#[0558.34] ScriptLog: Player changed name to Player1
	r5 = re.compile(r'^\[\d*\.\d*\]\s*ScriptLog\:\s*(.*)\s*changed name to\s*(.*)$', re.IGNORECASE | re.MULTILINE)
	name_changes = r5.findall(file_string)
	for match_string in json_string:
		player_info = {}
		r2 = re.compile(r'Player ID\:\s*(\d*)', re.IGNORECASE)
		playerID = r2.findall(match_string)[0]
		r3 = re.compile(r'Time\:\s*(\d*)', re.IGNORECASE)
		r4 = re.compile(r'Name\:\s*\'(.*)\'', re.IGNORECASE)
		player_info['Player ID'] = playerID
		player_info['Login Time'] = r3.findall(match_string)[0]
		player_info['Logout Time'] = "0" #default to null logout time
		#TODO find team number using poll output
		player_info['Team'] = "0"
		#{"PlayerID":1,"TeamIndex":1}
		r6 = re.compile(r'\{\"PlayerID\"\:'+str(playerID)+r'\,\"TeamIndex\"\:(\d*)\}', re.IGNORECASE)
		ids = r6.findall(file_string)
		if ids:
			if ids[len(ids)-1] == "0":
				player_info['Team'] = "Mrc"
			elif ids[len(ids)-1] == "1":
				player_info['Team'] = "Swt"
		if r4.findall(match_string):
			player_info['Name'] = r4.findall(match_string)[0]
			if name_changes:
				if player_info['Name'] == name_changes[0][0]:
					player_info['Name'] == name_changes[0][1]
					del name_changes[0]
		else:
			player_info['Name'] = "UNKNOWN"
		players.append(player_info)
	json_string = file_string.split(global_vars['logout_skey'])
	if len(json_string) >= 1:
		json_string = json_string[1:]
		players_out = []
		for match_string in json_string:
			player_info = {}
			player_info['Player ID'] = r2.findall(match_string)[0]
			logout_time = r3.findall(match_string)[0]
			r4 = re.compile(r'Team\:\s*(\d*)', re.IGNORECASE)
			team_number = r4.findall(match_string)
			if team_number:
				if team_number[0] == "0":
					player_info['Team'] = "Mrc"
				elif team_number[0] == "1":
					player_info['Team'] = "Swt"
			else:
				player_info['Team'] = "-1"
			# team_string = ""
			# n = -1
			# for team_number in team_numbers:
				# if team_number == "0":
					# team_number = "M"
				# elif team_number == "1":
					# team_number = "T"
				# n = n + 1
				# if n == 0:
					# team_string = team_string + str(team_number)
				# else:
					# team_string = team_string + str(team_number) + ", "
			# player_info['Team'] = team_string
			r1 = re.compile(r'Name\:\s*\'(.*)\'', re.IGNORECASE)
			if r1.findall(match_string):
				player_info['Name'] = r1.findall(match_string)[0]
			else:
				player_info['Name'] = "UNKNOWN"
			if logout_time:
				player_info['Logout Time'] = logout_time
			players_out.append(player_info)
		for player in players:
			for player_out in players_out:
				if player['Player ID'] == player_out['Player ID']:
					player['Name'] = player_out['Name']
					player['Team'] = str(player_out['Team'])
					if player_out.has_key('Logout Time'):
						player['Logout Time'] = player_out['Logout Time']
	#remove duplicate keys
	playerIDs_sofar = set()
	unique_players = []
	for player in players:
		if player['Player ID'] not in playerIDs_sofar:
			unique_players.append(player)
			playerIDs_sofar.add(player['Player ID'])
	return unique_players


def get_players_from_session(sessionID, getTeamNumbers=False):
	global global_vars
	if not sessionID:
		print "No sessionID selected"
		return None
	tree = ET.ElementTree()
	tree_parsed = tree.parse(global_vars['sessions_file'])
	player_infos = {}
	for session in tree_parsed.iter('SESSION'):
		if session.attrib['sessionID'] == sessionID:
			session_players = session.find('PLAYERS')
			for player in session_players.iter('PLAYER'):
				if getTeamNumbers:
					player_infos[str(player.attrib['playerID'])] = player.attrib['team']
				else:
					player_infos[str(player.attrib['playerID'])] = player.attrib['name']
	return player_infos


#Data Structure (Records):
# {
#	 'record_id' : { <record> },
#	 ...
# }
#
# Data Structure (Record)
# {
#	 'Round Number':"4",
#	 'Round Time':"4543",
#	 'Player Events': [ <PlayerEvent>,... ]
# }
def get_records_from_records_file(as_strings=False, recordIDs=[], return_first=False):
	global global_vars
	#tree = ET.ElementTree()
	tree_parsed = ET.parse(global_vars['records_file'])
	records = {}
	for record in tree_parsed.findall('RECORD'):
		if len(recordIDs) > 0 and not record.attrib['recordID'] in recordIDs:
			continue
		if as_strings:
			records[record.attrib['recordID']] = record.find('JSONSTR').text
		else:
			records[record.attrib['recordID']] = json.loads(record.find('JSONSTR').text)
		if return_first:
			break
	return records


#create a single record in recordFile from recordstr and returns ID
def create_record(record_string):
	global global_vars
	#tree = ET.ElementTree()
	tree_parsed = ET.parse(global_vars['records_file'])
	record_number = tree_parsed.find('RECORDCOUNT').attrib['count']
	record_number = int(record_number) + 1
	new_record = ET.SubElement(tree_parsed.getroot(), 'RECORD', {'recordID':str(record_number)})
	json_element = ET.SubElement(new_record, 'JSONSTR')
	json_element.text = record_string
	tree_parsed.find('RECORDCOUNT').set('count', str(record_number))
	tree_parsed.write(global_vars['records_file'])
	return record_number

	
def create_session(tags=[], desc="", log_file=global_vars['log_file'], refresh_sessions_widget=False):
	global global_vars
	#tree = ET.ElementTree()
	tree_parsed = ET.parse(global_vars['sessions_file'])
	session_number = tree_parsed.find('SESSIONCOUNT').attrib['count']
	session_number = int(session_number) + 1
	new_session = ET.SubElement(tree_parsed.getroot(), 'SESSION', {'sessionID':str(session_number), 'date':datetime.now().strftime('%c'), 'winner':'', 'merc_wins':'', 'swat_wins':''})
	tag_string = ""
	for tag in tags:
		tag_string = tag_string + tag + ";"
	new_session.set('tags', tag_string)
	new_session.set('desc', str(desc))
	#create players entry
	new_players = ET.SubElement(new_session, 'PLAYERS')
	players = get_players_from_log(log_file=log_file)
	for player in players:
		new_player = ET.SubElement(new_players, 'PLAYER', {'name':player['Name'], 'playerID':player['Player ID'], 'team':str(player['Team'])})
		ET.SubElement(new_player, 'LOGIN', {'time':player['Login Time']})
		if player.has_key('Logout Time'):
			ET.SubElement(new_player, 'LOGOUT', {'time':player['Logout Time']})
	#create config_vars entry
	new_config_vars = ET.SubElement(new_session, 'CONFIGVARS')
	config_vars = get_config_vars_from_log(log_file=log_file)
	if config_vars:
		for config_var in config_vars.items():
			new_config_var = ET.SubElement(new_config_vars, 'VAR', {'varName':str(config_var[0])})
			new_config_var.text = str(config_var[1])
	new_records = ET.SubElement(new_session, 'RECORDS')
	records = get_records_from_log_file(as_strings=True, log_file=log_file)
	win_stats = {}
	win_stats['merc wins'] = "0"
	win_stats['swat wins'] = "0"
	win_stats['winner'] = "UNKOWN"
	#create records entry
	for record in records:
		json_record = json.loads(record)
		if json_record.has_key('WinningTeamIndex'):
			win_team_index = str(json_record['WinningTeamIndex'])
			if win_team_index == "0":
				wins = int(win_stats['merc wins'])
				win_stats['merc wins'] = str(wins + 1)
			elif win_team_index == "1":
				wins = int(win_stats['swat wins'])
				win_stats['swat wins'] = str(wins + 1)
		record_number = create_record(record)
		ET.SubElement(new_records, 'RECORD', {'recordID':str(record_number)})
	if int(win_stats['merc wins']) > int(win_stats['swat wins']):
		win_stats['winner'] = "0"
	elif int(win_stats['merc wins']) < int(win_stats['swat wins']):
		win_stats['winner'] = "1"
	else:
		win_stats['winner'] = "Tie"
	new_session.set('merc_wins', str(win_stats['merc wins']))
	new_session.set('swat_wins', str(win_stats['swat wins']))
	new_session.set('winner', str(win_stats['winner']))
	tree_parsed.find('SESSIONCOUNT').set('count', str(session_number))
	tree_parsed.write(global_vars['sessions_file'])
	if refresh_sessions_widget:
		SessionsData.sessions_widget.scrollList.refreshList()
	return True


#TODO function has needless overhead
#Data Structure (Session)
#[
#    {
#        "Player IDs": ["1", ...], 
#        "Desc": "", 
#        "Tags": ["tag1", ...], 
#        "Date": "05/26/14 13:26:19", 
#        "Session ID": "1", 
#        "Record IDs": ["1","2",...], 
#        "Config Vars": [
#            { "DropAmountTier1Min": "3000"}, 
#            { "bDropMoneyOnSuicide": "True"}, 
#            ...
#        ]
#    },
#    ...
#]
# if one sessionID is passed, the index the result by 0, ie session = get_sessions(sessionID)[0]
def get_sessions(sessionIDs=[]):
	global global_vars
	if type(sessionIDs) == 'list' and len(sessionIDs) == 0:
		print "No sessions selected"
		return None
	tree = ET.ElementTree()
	tree_parsed = tree.parse(global_vars['sessions_file'])
	sessions = []
	for session in tree_parsed.iter('SESSION'):
		lsession = {}
		lsession['Session ID'] = session.attrib['sessionID']
		lsession['Date'] = session.attrib['date']
		lsession['Desc'] = session.attrib['desc']
		lsession['Tags'] = session.attrib['tags']
		lsession['Winner'] = session.attrib['winner']
		lsession['Merc Wins'] = session.attrib['merc_wins']
		lsession['Swat Wins'] = session.attrib['swat_wins']
		lsession['Config Vars'] = []
		session_config_vars = session.find('CONFIGVARS')
		for session_config_var in session_config_vars.iter('VAR'):
			for sessk in session_config_var.items():
				config_var = {}
				config_var[sessk[1]] = session_config_var.text
				lsession['Config Vars'].append(config_var)
		lsession['Record IDs'] = []
		session_records = session.find('RECORDS')
		for session_record in session_records.iter('RECORD'):
			lsession['Record IDs'].append(session_record.attrib['recordID'])
		lsession['Player IDs'] = []
		session_players = session.find('PLAYERS')
		for player in session_players.iter('PLAYER'):
			lsession['Player IDs'].append(player.attrib['playerID'])
		lsession['Player IDs'].sort()
		sessions.append(lsession)
	if sessionIDs:
		return [session for session in sessions if session['Session ID'] in sessionIDs]
	else:
		return sessions

		
def get_player_infos_from_session(sessionID=[]):
	global SessionsData
	player_infos = {}
	sessionID = SessionsData.active_sessionID
	session =  get_sessions(sessionID)[0]
	player_team_numbers = get_players_from_session(sessionID, getTeamNumbers=True)
	player_team_names = get_players_from_session(sessionID, getTeamNumbers=False)
	for playerID in session['Player IDs']:
		player_kill_events = get_player_events(sessionIDs=sessionID, playerIDs=[playerID], event_types=["KillEvent"])
		if not player_infos.has_key(playerID):
			player_infos[playerID] = {}
		if not player_infos[playerID].has_key('Kills'):
			player_infos[playerID]['Kills'] = 0
		if not player_infos[playerID].has_key('Team'):
			player_infos[playerID]['Team'] = player_team_numbers[playerID]
		if not player_infos[playerID].has_key('Name'):
			player_infos[playerID]['Name'] = player_team_names[playerID]
		if not player_infos[playerID].has_key('Deaths'):
			player_infos[playerID]['Deaths'] = 0
		for records in player_kill_events[sessionID].items():
			if records[1]['Player Events']:
				if records[1]['Player Events']:
					for x in range(0, len(records[1]['Player Events'])):
						if records[1]['Player Events'][x].has_key("KillEvent"):
							if not records[1]['Player Events'][x]['KillEvent']['Killed']['PlayerID'] == -1:
								kills = int(player_infos[playerID]['Kills'])
								player_infos[playerID]['Kills'] =  kills + 1
								killedID = str(records[1]['Player Events'][x]['KillEvent']['Killed']['PlayerID'])
								if not player_infos.has_key(killedID):
									player_infos[killedID] = {}
								if not player_infos[killedID].has_key('Deaths'):
									player_infos[killedID]['Deaths'] = 0
								deaths = int(player_infos[killedID]['Deaths'])
								player_infos[killedID]['Deaths'] = deaths + 1
	return player_infos


def get_recordIDs_from_session(sessionID):
	session = get_sessions(sessionID)
	return session[0]['Record IDs']


# Data Structure (Player Events):
# {
#	 'session ID': [
#        "record ID": [
#            "round time":"345",
#            "round number":"4",
#            "winner": "merc",				#TODO add this
#            "player events": [
#                {
#                    { <event> },
#                    ...
#                }
#            ]
#        ],
#        ...
#    ],
#    ...
# }
#
# use Filter to retrieve sub-event information for each event type. for example:
# defaults to SessionsData.default_player_event_filters
def get_player_events(playerIDs=[], sessionIDs=[], event_types=["all"], filters=[], label_player_name=False, return_first=False):
	global global_vars, SessionsData
	sessions = get_sessions(sessionIDs)
	if sessions == None:
		return
	if not filters:
		filters = SessionsData.default_player_event_filters
	player_events = {}
	if event_types == ["all"]:
		event_types = SessionsData.all_events
	for session in sessions:
		records = {}
		for recordID in session['Record IDs']:
			main_record = get_records_from_records_file(as_strings=False, return_first=False, recordIDs=[recordID])
			main_record = main_record[recordID]
			record_entry = {}
			record_entry['Round Number'] = main_record['RoundNumber']
			record_entry['Round Time'] = main_record['RoundTime']
			record_entry['Player Events'] = []
			for player_event in main_record['PlayerEvents']:
				event_type = [ event_key for event_key in player_event.keys() if event_key in event_types ]
				if not event_type:
					continue
				else:
					event_type = event_type[0]
				a_player_event = {}
				a_player_event['Amount'] = player_event['Amount']
				a_player_event['Time'] = player_event['Time']
				if not player_event.has_key('PlayerIDInfo'):
					print "Data Error. Discarded 1 event data"
					continue
				if len(playerIDs) > 0:
					if player_event.has_key('PlayerIDInfo') and str(player_event['PlayerIDInfo']['PlayerID']) not in playerIDs:
						continue
				else:
					if label_player_name:
						a_player_event['Player Name'] = player_event['PlayerIDInfo']['Name']
					else:
						a_player_event['Player ID'] = player_event['PlayerIDInfo']['PlayerID']
				a_player_event[event_type] = apply_filters(player_event[event_type], filters[event_type])
				record_entry['Player Events'].append(a_player_event)
			records[recordID] = record_entry
		player_events[session['Session ID']] = records
		if return_first:
			break
	return player_events


def apply_filters(input_array, filter):
	if hasattr(input_array, 'items'):
		filtered_array = {}
		for item in input_array.items():
			if hasattr(item[1], '__iter__'):
				filtered_array[item[0]] = apply_filters(input_array[item[0]], filter[item[0]])
			else:
				if filter[item[0]]:
					filtered_array[item[0]] = input_array[item[0]]
	elif hasattr(input_array, '__iter__'):
		filtered_array = []
		for item in input_array:
			filtered_array.append(apply_filters(item, filter))
	elif filter:
		filtered_array = filter
	return filtered_array


def delete_sessions(sessionIDs=[]):
	global global_vars
	N = len(sessionIDs)
	if N == 0:
		return
	tree_sessions = ET.ElementTree()
	tree_records = ET.ElementTree()
	tree_sessions_parsed = tree_sessions.parse(global_vars['sessions_file'])
	tree_records_parsed = tree_records.parse(global_vars['records_file'])
	try:
		for session in tree_sessions_parsed.findall('SESSION'):
			if session.attrib['sessionID'] in sessionIDs:
				recordIDs = get_recordIDs_from_session(session.attrib['sessionID'])
				for record in tree_records_parsed.findall('RECORD'):
					if record.attrib['recordID'] in recordIDs:
						tree_records_parsed.remove(record)
						record_number = tree_records_parsed.find('RECORDCOUNT').attrib['count']
						record_number = int(record_number) - 1
						tree_records_parsed.find('RECORDCOUNT').set('count', str(record_number))
				tree_sessions_parsed.remove(session)
				session_number = tree_sessions_parsed.find('SESSIONCOUNT').attrib['count']
				session_number = int(session_number) - 1
				tree_sessions_parsed.find('SESSIONCOUNT').set('count', str(session_number))
				N = N - 1
		tree_sessions.write(global_vars['sessions_file'])
		tree_records.write(global_vars['records_file'])
	except StandardError:
		print "Could not delete sessions"
	if N == 0:
		showinfo('Delete Sessions', 'Sessions deleted')
	else:
		showinfo('Delete Sessions', 'Could not delete sessions. Check session file.')


#TODO make a sorting function
def bar_data(sessionIDs=[], dependent_variable="Amount", event_types=["all"], playerIDs=[], statistic="net", include_zero_values=True, aggregate={"1":"events","2":"players"}):
	player_events = get_player_events(playerIDs=playerIDs, sessionIDs=sessionIDs, event_types=event_types)
	if event_types == ["all"]:
		event_types = SessionsData.all_events
	else:
		event_types.sort()
	main_frame = {}
	for sessionID in player_events.keys():
		data_frame = {}
		num_rounds = len(player_events[sessionID].keys())
		for recordID in player_events[sessionID].keys():
			for player_event in player_events[sessionID][recordID]['Player Events']:
				event_type = [event for event in player_event.keys() if event in event_types][0]
				if aggregate["1"] == "players" and aggregate["2"] == "events":
					first_key = str(player_event['Player ID'])
					second_key = event_type
				elif aggregate["1"] == "events" and aggregate["2"] == "players":
					first_key = event_type
					second_key = str(player_event['Player ID'])
				if not data_frame.has_key(first_key):
					data_frame[first_key] = {}
				if not data_frame[first_key].has_key(second_key):
					data_frame[first_key][second_key] = []
				data_frame[first_key][second_key].append(player_event[dependent_variable])
		complement_keys = []
		if aggregate["1"] == "players" and aggregate["2"] == "events":
			complement_keys = event_types
		elif aggregate["1"] == "events" and aggregate["2"] == "players":
			complement_keys = get_sessions(sessionID)[0]['Player IDs']
		for first_key in data_frame.keys():
			for second_key in data_frame[first_key].keys():
				xsum = 0
				for x in data_frame[first_key][second_key]:
					xsum = xsum + x
				if statistic == "average":
					#must divide by num rounds
					#xsum = float(xsum) / len(data_frame[first_key][second_key])
					xsum = float(xsum) / num_rounds
				data_frame[first_key][second_key] = xsum
			if include_zero_values:
				for complement_key in [str(key) for key in complement_keys if key not in data_frame[first_key].keys()]:
					data_frame[first_key][complement_key] = 0
		main_frame[sessionID] = data_frame
	return main_frame


#{
#	'playerID':[start_round_amount]
#}
def get_starting_round_amounts(sessionID=[]):
	global SessionsData, global_vars
	if not sessionID:
		sessionID = SessionsData.active_sessionID
	recordIDs = get_recordIDs_from_session(sessionID)
	records = get_records_from_records_file(recordIDs=recordIDs)
	playerIDs = set(get_players_from_session(sessionID).keys())
	starting_round_amounts = {}
	for recordID in recordIDs:
		playerIDs_this_round = set()
		json_record = records[str(recordID)]
		if json_record.has_key('PlayerEvents'):
			for event in json_record['PlayerEvents']:
				if event.has_key('RoundStartEvent'):
					round_start_events = event['RoundStartEvent']['PlayerRoundStartAmounts']
					for round_start_event in round_start_events:
						#{"Wallet":1000,"Player":{"PlayerID":2,"TeamIndex":0}
						playerID = str(round_start_event['Player']['PlayerID'])
						playerIDs_this_round.add(playerID)
						if not starting_round_amounts.has_key(playerID):
							starting_round_amounts[playerID] = []
						starting_round_amounts[playerID].append(round_start_event['Wallet'])
				else:
					break
		for no_playerID in playerIDs.difference(playerIDs_this_round):
			if not starting_round_amounts.has_key(no_playerID):
				starting_round_amounts[no_playerID] = []
			starting_round_amounts[no_playerID].append("NA")
	if starting_round_amounts.has_key("0"):
		del starting_round_amounts["0"]
	return starting_round_amounts
	
	
class SessionsScrollList(Frame):

	def __init__(self, parent=None):
		global global_vars
		Frame.__init__(self, parent)
		self.pack(expand=YES, fill=X)
		self.row_frames = []
		canv = Canvas(self, bd=0, highlightthickness=0)
		canv.config(scrollregion=(0, 0, 0, global_vars['MAX_SESSIONS'] * 26))
		#canv.config(scrollregion=(0, 0, 0, 1067))
		self.w = Frame(self)
		self.initList(self.w)
		self.w.pack(expand=YES, fill=BOTH)
		canv.create_window(0, 0, anchor=NW, window=self.w)
		sbar = Scrollbar(self)
		sbar.config(command=canv.yview)
		canv.config(yscrollcommand=sbar.set)
		sbar.pack(side=RIGHT, fill=Y)
		canv.pack(side=LEFT, expand=YES, fill=BOTH)

	def createSessionRow(self, parent, sessionID="", datestr="", tags="", desc=""):
		textFont = Font(family='Helvetica', size=12, weight='normal')
		row_frame = Frame(parent)
		row_frame.pack(expand=YES)
		row_frame.labels = []
		label1 = Checkbutton(row_frame, relief=RIDGE, bd=2, pady=1, padx=1, width=4, bg='white')
		label2 = Label(row_frame, text=sessionID, relief=RIDGE, bd=1, pady=3, width=13, font=textFont, bg='white')
		label3 = Label(row_frame, text=datestr, relief=RIDGE, bd=1, pady=3, width=16, font=textFont, bg='white')
		label4 = Label(row_frame, text=tags, relief=RIDGE, bd=1, pady=3, width=16, font=textFont, bg='white')
		label5 = Label(row_frame, text=desc, relief=RIDGE, bd=1, width=40, pady=3, font=textFont, bg='white')
		label1.pack(side=LEFT)
		row_frame.labels.append(label1)
		label2.pack(side=LEFT)
		row_frame.labels.append(label2)
		label3.pack(side=LEFT)
		row_frame.labels.append(label3)
		label4.pack(side=LEFT)
		row_frame.labels.append(label4)
		label5.pack(side=LEFT)
		row_frame.labels.append(label5)
		label1.sessionID = sessionID
		row_frame.labels.append(label1)
		label2.sessionID = sessionID
		label2.name = "sessionID"
		row_frame.labels.append(label2)
		label3.sessionID = sessionID
		label3.name = "datestr"
		row_frame.labels.append(label3)
		label4.sessionID = sessionID
		label4.name = "tags"
		row_frame.labels.append(label4)
		label5.sessionID = sessionID
		label5.name = "desc"
		row_frame.labels.append(label5)
		label1.bind('<Button-1>', self.onMouseLeftClick)
		label2.bind('<Button-1>', self.onMouseLeftClick)
		label3.bind('<Button-1>', self.onMouseLeftClick)
		label4.bind('<Button-1>', self.onMouseLeftClick)
		label5.bind('<Button-1>', self.onMouseLeftClick)
		row_frame.sessionID = sessionID
		return row_frame

	def onMouseLeftClick(self, event):
		global SessionsData, global_vars
		if event.widget.sessionID:
			SessionsData.active_sessionID = event.widget.sessionID
		else:
			if event.widget.__class__.__name__ == 'Checkbutton':
				event.widget.toggle()
			return
		if not event.widget.__class__.__name__ == 'Checkbutton':
			SessionsData.config_vars_widget.ConfigVarsScrollListRef.refresh()
			SessionsData.extra_info_widget.refresh()
		if event.widget.__class__.__name__ == 'Checkbutton':
			if len(SessionsData.selected_sessionIDs) < global_vars['MAX_SESSIONS']:
				if not event.widget.sessionID in SessionsData.selected_sessionIDs:
					SessionsData.selected_sessionIDs.append(SessionsData.active_sessionID)
				else:
					del SessionsData.selected_sessionIDs[SessionsData.selected_sessionIDs.index(event.widget.sessionID)]
			else:
				if not event.widget.sessionID in SessionsData.selected_sessionIDs:
					event.widget.toggle()
				else:
					del SessionsData.selected_sessionIDs[SessionsData.selected_sessionIDs.index(event.widget.sessionID)]
			return
		for row_frame in self.row_frames:
			if row_frame.sessionID == SessionsData.active_sessionID:
				for label in row_frame.labels:
					label.config(bg='blue')
					if not label.__class__.__name__ == 'Checkbutton':
						label.config(fg='white')
			else:
				for label in row_frame.labels:  #TODO just unblue the previous active_sessionID
					label.config(bg='white', fg='black')

	def initList(self, parent):
		global SessionsData, global_vars
		if not parent:
			parent = self.w
		SessionsData.sessionsIDs = get_sessionIDs_from_sessions_file()
		N = len(SessionsData.sessionsIDs)
		for sessionID in SessionsData.sessionsIDs:
				session = get_sessions(sessionID)
				self.row_frames.append(self.createSessionRow(parent, sessionID, session[0]['Date']))
		if N < global_vars['MAX_SESSIONS']:
			for m in range(N + 1, global_vars['MAX_SESSIONS'] + 1):
				self.row_frames.append(self.createSessionRow(parent, "", ""))

	def refreshList(self):
		global SessionsData
		SessionsData.sessionsIDs = get_sessionIDs_from_sessions_file()
		if len(self.row_frames) == 0:
			return
		n = -1
		SessionsData.sessionsIDs.sort()
		sessions_num = len(SessionsData.sessionsIDs)
		for row_frame in self.row_frames:
			n = n + 1
			if n < sessions_num:
				session = get_sessions(SessionsData.sessionsIDs[n])[0]
				row_frame.sessionID = session['Session ID']
				for label in row_frame.labels:
					label.sessionID = session['Session ID']
					if hasattr(label, 'name'):
						if label.name == "sessionID":
							label.config(text=session['Session ID'])
						elif label.name == "datestr":
							label.config(text=session['Date'])
						elif label.name == "tags":
							label.config(text=session['Tags'])
						elif label.name == "desc":
							label.config(text=session['Desc'])
			else:
				row_frame.sessionID = ""
				for label in row_frame.labels:
					if not label.__class__.__name__ == 'Checkbutton':
						label.config(text="")
					label.config(bg='white', fg='black')
		self.unchecklist()

	def unchecklist(self):
		global SessionsData
		SessionsData.active_sessionID = None
		SessionsData.selected_sessionIDs = []
		for row_frame in self.row_frames:
			for label in row_frame.labels:
				if label.__class__.__name__ == 'Checkbutton':
					label.deselect()


class ConfigVarsScrollList(Frame):

	def __init__(self, parent=None):
		global global_vars
		Frame.__init__(self, parent)
		self.pack(expand=YES, fill=BOTH)
		self.pFrame = Frame(self)
		self.pFrame.pack(side=LEFT, fill=BOTH, expand=YES)
		canv = Canvas(self.pFrame, bd=2, highlightthickness=0, width=422, relief=GROOVE)
		canv.config(scrollregion=(0, 0, 0, global_vars['MAX_CONFIG_VARIABLES'] * 26))
		#canv.config(scrollregion=(0, 0, 0, 1040))
		self.mainFrame = Frame(self.pFrame)
		self.labels = []
		for x in range(0, global_vars['MAX_CONFIG_VARIABLES']):
			self.labels.append(self.createConfigVarRow(self.mainFrame, "", ""))
		self.mainFrame.pack(expand=YES, fill=BOTH)
		canv.create_window(0, 0, anchor=NW, window=self.mainFrame)
		sbar = Scrollbar(self.pFrame)
		sbar.config(command=canv.yview)
		canv.config(yscrollcommand=sbar.set)
		sbar.pack(side=RIGHT, fill=Y)
		canv.pack(side=LEFT, fill=BOTH)
		
	def createConfigVarRow(self, parent, varName="", varValue=""):
		row_frame = Frame(parent)
		row_frame.pack(side=TOP, fill=X)
		textFont = Font(family='Helvetica', size=12, weight='normal')
		label1 = Label(row_frame, text="  " + varName, relief=RIDGE, bd=1, pady=3, width=32, font=textFont, anchor=W, bg='white')
		label2 = Label(row_frame, text="  " + varValue, relief=RIDGE, bd=1, pady=3, width=14, font=textFont, bg='white')
		label1.pack(side=LEFT)
		label2.pack(side=LEFT)
		row_frame.var_name_label = label1
		row_frame.var_value_label = label2
		return row_frame
		
	def refresh(self):
		global SessionsData, global_vars
		session = get_sessions(SessionsData.active_sessionID)
		N = -1
		if len(session) >= 1:
			session = session[0]
			for config_var in session['Config Vars']:
				for x,y in config_var.items():
					N = N + 1
					self.labels[N].var_name_label.config(text=x)
					self.labels[N].var_value_label.config(text=y)
					if N >= global_vars['MAX_CONFIG_VARIABLES']:
						break
		for i in range(N + 1, global_vars['MAX_CONFIG_VARIABLES']):
			self.labels[i].var_name_label.config(text="")
			self.labels[i].var_value_label.config(text="")


class SessionsWidget(Frame):

	def __init__(self, parent=None):
		Frame.__init__(self, parent)
		self.pack(expand=YES, fill=X)
		textFont = Font(family='Helvetica', size=12, weight='normal')
        #first divide into two frames and create headers
		leftFrame = Frame(self, padx=0, bd=0)
		leftFrame.pack(side=LEFT, expand=YES, fill=Y)
		leftFrameHeader = Frame(leftFrame)
		leftFrameHeader.pack(side=TOP, expand=YES, fill=X)
		label1 = Label(leftFrameHeader, text="", relief=RIDGE, bd=1, pady=3, padx=5, width=5, font=textFont)
		label2 = Label(leftFrameHeader, text="Match ID", relief=RIDGE, bd=1, pady=3, width=13, font=textFont)
		label3 = Label(leftFrameHeader, text="Date", relief=RIDGE, bd=1, pady=3, width=16, font=textFont)
		label4 = Label(leftFrameHeader, text="Tags", relief=RIDGE, bd=1, pady=3, width=16, font=textFont)
		label5 = Label(leftFrameHeader, text="Desc", relief=RIDGE, bd=1, width=40, pady=3, font=textFont)
		label1.pack(side=LEFT)
		label2.pack(side=LEFT)
		label3.pack(side=LEFT)
		label4.pack(side=LEFT)
		label5.pack(side=LEFT)
		self.scrollList = SessionsScrollList(leftFrame)
		self.scrollList.pack(side=LEFT, fill=BOTH, expand=YES)


# click on either the tag or desc label to pop up this menu to edit the values
class EditSessionWidget(Frame):

	def __init__(self, parent=None, SessionsWidgetRef=None):
		Frame.__init__(self, parent=None)
		self.pack(expand=YES, fill=X, side=BOTTOM)
		rowFrame = Frame(parent, pady=8, borderwidth=2, relief=GROOVE)
		rowFrame.pack(expand=YES, fill=X)
		textFont = Font(family='Helvetica', size=12, weight='normal')
		lab1 = Label(rowFrame, text="tags", relief=FLAT, bd=1, pady=3, width=8, font=textFont)
		ent1 = Entry(rowFrame, width=40)
		lab1.pack(side=LEFT)
		ent1.pack(side=LEFT)
		secondFrame = Frame(rowFrame, padx=10)
		secondFrame.pack()
		lab2 = Label(secondFrame, text="desc", relief=FLAT, bd=1, pady=3, width=8, font=textFont)
		ent2 = Entry(secondFrame, width=60)
		lab2.pack(side=LEFT)
		ent2.pack(side=LEFT)


class ConfigVarsWidget(Frame):

	def __init__(self, parent=None):
		Frame.__init__(self, parent, bg='red')
		self.pack(expand=YES, fill=BOTH)
		textFont = Font(family='Helvetica', size=12, weight='normal')
		mLabel = Label(self, text="ConfigVars", relief=FLAT, bd=1, pady=5, padx=8, font=textFont)
		mLabel.pack(side=TOP, fill=X)
		configVarFrame = Frame(self)
		configVarFrame.pack(expand=YES, fill=BOTH)
		self.ConfigVarsScrollListRef = ConfigVarsScrollList(configVarFrame)


class BarGraphWidget(Frame):

	def __init__(self, parent=None):
		global SessionsData
		optionList1 = ('Money')
		textFont = Font(family='Helvetica', size=12, weight='normal')
		labelFrameHolder = Frame(parent, pady=8, padx=4)
		labelFrameHolder.pack(side=TOP, fill=X)
		labFrame2 = LabelFrame(labelFrameHolder, text="Include Event Types", font=textFont, pady=4, padx=4)
		labFrame2.pack(expand=YES, fill=BOTH)
		self.eventTypeCheckbutton = {}
		for event_type in SessionsData.event_types:
			self.eventTypeCheckbutton[event_type] = IntVar()
			self.eventTypeCheckbutton[event_type].set(0)
			row = Frame(labFrame2)
			row.pack(side=TOP, fill=X, expand=YES)
			check = Checkbutton(row, text=SessionsData.event_types[event_type], font=textFont, variable=self.eventTypeCheckbutton[event_type])
			check.pack(side=LEFT, fill=X)
			check.select()
		labFrame4 = Frame(parent, pady=10)
		labFrame4.pack(side=TOP)
		labFrame3 = Frame(parent, pady=10)
		labFrame3.pack(side=TOP)
		self.mode = StringVar()
		self.mode.set('Total')
		optionList2 = ('Total', 'Average')
		om1 = OptionMenu(labFrame4, self.mode, *optionList2)
		mode_label = Label(labFrame4, text="Mode", font=textFont, width=8)
		mode_label.pack(side=LEFT)
		om1.pack(side=LEFT)
		lab2 = Button(labFrame3, text="generate bar graph", command=self.callGraph, font=textFont)
		lab2.pack(side=BOTTOM)

	#TODO create generic keys
	def callGraph(self):
		global SessionsData
		event_types = []
		for check in self.eventTypeCheckbutton.items():
			if check[1].get() == 1:
				event_types.append(check[0])
		event_types.sort()
		value = self.mode.get()
		if value == "Total":
			value = "net"
		else:
			value = "average"
		bar_data_frames = bar_data(sessionIDs=SessionsData.selected_sessionIDs, dependent_variable="Amount", event_types=event_types, statistic=value)
		for sessionID in SessionsData.selected_sessionIDs:
			num_rounds = len(get_sessions(sessionID)[0]['Record IDs'])
			bar_plot_labels = []
			bar_plots = []
			events_sofar = []
			bar_data_frame = bar_data_frames[sessionID]
			player_infos = get_players_from_session(sessionID)
			player_count = len(player_infos.keys())
			N = np.arange(player_count)
			fig_width = 9*math.log(player_count, 2) - 5*(player_count)/2 + 6
			bar_width = math.log(player_count, 2)/player_count
			fig = plt.figure(figsize=(fig_width,11), dpi=80, frameon=False)
			plot21 = fig.add_subplot(2,1,1, ymargin=0.09)
			player_labels = []
			player_IDs = []
			n = -1
			str_val = json.dumps(bar_data_frames, indent=4)
			file = open(global_vars['install_directory'] + 'tmp.txt', 'w')
			file.write(str_val)
			file.close()
			for event_layer in bar_data_frame.items():
				n = n + 1
				if not player_labels:
					for player_num in event_layer[1].keys():
						player_IDs.append(str(player_num))
						player_labels.append(player_infos[str(player_num)])
				event_name = event_layer[0]
				events_sofar.append(event_name)
				horizontal_layer = []
				for x in event_layer[1].items():
					horizontal_layer.append(x[1])
				if n == 0:
					bar_plot = plot21.bar(N, horizontal_layer, bar_width, color=SessionsData.event_colors[event_name], align='center')
					bar_plot_labels.append(bar_plot[1])
					bar_plots.append(bar_plot)
				else:
					bottom_bar = []
					other_event_types = [x for x in event_types if not x == event_name and x in bar_data_frame.keys() and x in events_sofar]
					for x in event_layer[1].items():
						player_ID = str(x[0])
						positive_bvalue = 0
						negative_bvalue = 0
						for other_event in other_event_types:
							bvalue = bar_data_frame[other_event][player_ID]
							if bvalue >= 0:
								positive_bvalue = positive_bvalue + bvalue
							else:
								negative_bvalue = negative_bvalue + bvalue
						if x[1] >= 0:
							bottom_bar.append(positive_bvalue)
						else:
							bottom_bar.append(negative_bvalue)
					bar_plot = plot21.bar(N, horizontal_layer, bar_width, bottom=bottom_bar, color=SessionsData.event_colors[event_name], align='center')
					bar_plot_labels.append(bar_plot[1])
					bar_plots.append(bar_plot)
			plot21.set_xlim(-1, player_count, auto=True)
			plot21.set_xticks(np.arange(player_count))
			plot21.set_xticklabels(player_labels, rotation=45)
			plot21.axhline(y=0, linewidth=1, color='black', ls='--')
			plot21.set_ylabel(r'Amount  \$\$')
			plot21.set_title("Match ID {0}:  {2} rounds ({1}) \n {3} \n".format(sessionID, value, num_rounds, get_sessions(sessionID)[0]['Desc']))
			ylim_value = plot21.get_ylim()
			ylim_value =  ylim_value[1] - ylim_value[0]
			index = -1
			for playerID in player_IDs:
				index = index + 1
				max_value = 0
				min_value = 0
				for event_type in event_types:
					if bar_data_frame.has_key(event_type):
						if bar_data_frame[event_type][str(playerID)] >= 0:
							max_value = max_value + bar_data_frame[event_type][str(playerID)]
						elif bar_data_frame[event_type][str(playerID)] < 0:
							min_value = min_value + bar_data_frame[event_type][str(playerID)]
				if max_value > 0:
					plot21.text(player_IDs.index(str(playerID)), (0.005*ylim_value) + max_value, "+"+str(max_value).split('.')[0], ha='center', va="bottom")
				if min_value < 0:
					plot21.text(player_IDs.index(str(playerID)), -1*(0.015*ylim_value) + min_value, str(min_value).split('.')[0], ha='center', va="top")
			plt22 = fig.add_subplot(2,1,2, axisbg='#bfbfbf', frameon=False)
			plt22.set_xticks([]), plt22.set_yticks([])
			plt22.legend(bar_plot_labels, events_sofar, loc=10)
			fig.show()


class PieChartWidget(Frame):

	def __init__(self, parent=None):
		lab1 = Label(parent, text="hello PieChart")
		lab1.pack()


class LineGraphWidget(Frame):

	def __init__(self, parent=None):
		lab1 = Label(parent, text="hello LineGraph")
		lab1.pack()


class ScatterPlotWidget(Frame):

	def __init__(self, parent=None):
		lab1 = Label(parent, text="hello ScatterPlot")
		lab1.pack()

		
class VizualizationWidget(Frame):

	def __init__(self, parent=None):
		Frame.__init__(self, parent)
		self.pack(expand=YES, fill=BOTH)
		textFont = Font(family='Helvetica', size=12, weight='normal')
		topRow1 = Frame(self, pady=8)
		topRow1.pack(side=TOP)
		labFrame = LabelFrame(topRow1, text="Cash Flow Visualization", font=textFont, pady=4, padx=14)
		textFont = Font(family='Helvetica', size=12, weight='normal')
		topRow2 = Frame(labFrame, pady=4)
		topRow2.pack(side=TOP)
		mLabel = Label(topRow2, text="Visualization Type", font=textFont, width=20)
		mLabel.pack(side=LEFT)
		optionList = ('Bar Graph', 'Pie Chart', 'Line Graph', 'Scatter Plot')
		self.v = StringVar()
		self.v.set(optionList[0])
		self.om = OptionMenu(topRow2, self.v, *optionList)
		self.om.pack(side=LEFT)
		labFrame.pack(fill=X, expand=YES)
		self.OptionsFrame = Frame(labFrame, pady=4, padx=4)
		self.OptionsFrame.pack(expand=YES, fill=BOTH)
		self.OptionsFrame.BarGraph = BarGraphWidget(self.OptionsFrame)
		
	def onClick(self):
		self.refresh(self.v.get())


class SessionInfoWidget(Frame):
	
	def __init__(self, parent=None):
		global SessionsData
		Frame.__init__(self, parent)
		self.pack(expand=YES, fill=BOTH)
		textFont = Font(family='Helvetica', size=12, weight='normal')
		row1 = Frame(self, pady=4)
		row1.pack(side=TOP, fill=X)
		row2 = Frame(self, pady=4)
		row2.pack(side=TOP, fill=X)
		row3 = Frame(self, pady=4)
		row3.pack(side=TOP, fill=X)
		row4 = Frame(self, pady=4)
		row4.pack(side=TOP, fill=X)
		row5 = Frame(self, pady=4)
		row5.pack(side=TOP, fill=X)
		
		lab1 = Label(row1, text="Match ID", font=textFont, width=10, anchor=E, padx=10)
		msg1 = Label(row1, text="", width=10, bg="white", font=textFont)
		lab1.pack(side=LEFT)
		msg1.pack(fill=X)
		
		lab2 = Label(row2, text="Rounds", font=textFont, width=10, anchor=E, padx=10)
		msg2 = Label(row2, text="", bd=1, bg="white", font=textFont)
		lab2.pack(side=LEFT)
		msg2.pack(fill=X)
		
		lab3 = Label(row3, text="Winner", font=textFont, width=10, anchor=E, padx=10)
		msg3 = Label(row3, text="", bd=1, bg="white", font=textFont)
		lab3.pack(side=LEFT)
		msg3.pack(fill=X)
		
		lab4 = Label(row4, text="Merc Wins", font=textFont, width=10, anchor=E, padx=10, fg="red")
		msg4 = Label(row4, text="", bd=1, bg="white", font=textFont)
		lab4.pack(side=LEFT)
		msg4.pack(fill=X)
		
		lab5 = Label(row5, text="SWAT Wins", font=textFont, width=10, anchor=E, padx=10, fg="blue")
		msg5 = Label(row5, text="", bd=1, bg="white", font=textFont)
		lab5.pack(side=LEFT)
		msg5.pack(fill=X)
		
		self.sessionID_msg = msg1
		self.rounds_msg = msg2
		self.winner_msg = msg3
		self.merc_wins_msg = msg4
		self.terrorist_wins_msg = msg5
		
	def refresh(self):
		global SessionsData
		if SessionsData.active_sessionID:
			session = get_sessions(SessionsData.active_sessionID)[0]
			self.sessionID_msg.config(text=session['Session ID'])
			self.rounds_msg.config(text=len(session['Record IDs']))
			if session['Winner'] == "0":
				winner = "Mercenaries"
				fg_color = "red"
			elif session['Winner'] == "1":
				winner = "SWAT"
				fg_color = "blue"
			self.winner_msg.config(text=winner, fg=fg_color)
			self.merc_wins_msg.config(text=session['Merc Wins'])
			self.terrorist_wins_msg.config(text=session['Swat Wins'])
		else:
			self.sessionID_msg.config(text="")
			self.rounds_msg.config(text="")
			self.winner_msg.config(text="", fg="black")
			self.merc_wins_msg.config(text="")
			self.terrorist_wins_msg.config(text="")
		
		
class PlayerInfoWidget(Frame):

	def __init__(self, parent=None):
		global SessionsData
		Frame.__init__(self, parent)
		self.pack(expand=YES, fill=BOTH)
		canv = Canvas(self, bd=1, highlightthickness=0)
		canv.config(scrollregion=(0, 0, 0, global_vars['MAX_PLAYERS'] * 26))
		self.player_list_frame = Frame(self)
		self.player_list_frame.pack(expand=YES, fill=BOTH)
		canv.create_window(0, 0, anchor=NW, window=self.player_list_frame)
		sbar = Scrollbar(self)
		sbar.config(command=canv.yview)
		canv.config(yscrollcommand=sbar.set)
		sbar.pack(side=RIGHT, fill=Y)
		canv.pack(side=LEFT, expand=YES, fill=BOTH)
		self.refresh()
	
	def refresh(self):
		global SessionsData, global_vars
		if self.player_list_frame.pack_slaves():
			for child in self.player_list_frame.pack_slaves():
				child.destroy()
		self.create_header()
		if not SessionsData.active_sessionID:
			for x in range(0, global_vars['MAX_PLAYERS']):
				self.create_row("", "", "", "")
			return
		player_infos = get_player_infos_from_session()
		for player_info in player_infos.items():
			self.create_row(player_info[1]['Name'], player_info[1]['Team'], player_info[1]['Kills'], player_info[1]['Deaths'])
		
	def create_header(self):
		textFont = Font(family='Helvetica', size=12, weight='normal')
		row = Frame(self.player_list_frame, pady=4)
		row.pack(fill=X, expand=YES)
		lab1 = Label(row, text="Name", font=textFont, width=16, relief=GROOVE)
		lab1.pack(side=LEFT)
		lab2 = Label(row, text="Team", font=textFont, width=8, relief=GROOVE)
		lab2.pack(side=LEFT)
		lab3 = Label(row, text="Kills", font=textFont, width=6, relief=GROOVE)
		lab3.pack(side=LEFT)
		lab4 = Label(row, text="Deaths", font=textFont, width=8, relief=GROOVE)
		lab4.pack(side=LEFT)
	
	def create_row(self, playerName, team, kills, deaths):
		fg_color = 'white'
		if team == "Mrc":
			fg_color = "red"
		elif team == "Swt":
			fg_color = "blue"
		textFont = Font(family='Helvetica', size=12, weight='normal')
		row = Frame(self.player_list_frame, pady=4)
		row.pack(fill=X, expand=YES)
		lab1 = Label(row, text=playerName, font=textFont, bg='white', width=16)
		lab1.pack(side=LEFT)
		lab2 = Label(row, text=team, font=textFont, bg='white', fg=fg_color, width=8)
		lab2.pack(side=LEFT)
		lab3 = Label(row, text=kills, font=textFont, bg='white', width=6)
		lab3.pack(side=LEFT)
		lab4 = Label(row, text=deaths, font=textFont, bg='white', width=8)
		lab4.pack(side=LEFT)


class MarketInfoWidget(Frame):

	def __init__(self, parent=None):
		global SessionsData
		win = Toplevel()
		win.title("Match ID "+str(SessionsData.active_sessionID))
		textFont = Font(family='Helvetica', size=12, weight='normal')
		top_frame = Frame(win, pady=12, padx=12)
		top_frame.pack(expand=YES, fill=BOTH)
		labFrame1 = LabelFrame(top_frame, text="Aggregate Purchases", font=textFont, pady=4, padx=14)
		labFrame1.pack(fill=Y, expand=YES, side=LEFT)
		labFrame2 = LabelFrame(top_frame, text="Starting Round Wallet", font=textFont, pady=4, padx=14)
		labFrame2.pack(fill=Y, expand=YES, side=RIGHT)
		starting_round_amounts = get_starting_round_amounts(SessionsData.active_sessionID)
		top_row = Frame(labFrame2, pady=4, padx=14)
		top_row.pack(side=TOP, fill=X, expand=YES)
		top_row_label = Label(top_row, text="Rounds", font=textFont)
		top_row_label.pack()
		second_top_row = Frame(labFrame2, pady=4, padx=14)
		second_top_row.pack(side=TOP, fill=X, expand=YES)
		upper_left_label = Label(second_top_row, text="", width=14, pady=4, padx=14)
		upper_left_label.pack(side=LEFT)
		players = starting_round_amounts.keys()
		if players > 0:
			round_count = len(get_recordIDs_from_session(SessionsData.active_sessionID))
		for x in range(0, round_count):
			lab1 = Label(second_top_row, text="{0}".format(x+1), font=textFont, pady=2, padx=2, width=7)
			lab1.pack(side=LEFT)
		round_avg_lab = Label(second_top_row, text="Mean", font=textFont, pady=2, padx=2, width=7)
		round_avg_lab.pack(side=LEFT)
		std_avg_lab = Label(second_top_row, text="Std", font=textFont, pady=2, padx=2, width=7)
		std_avg_lab.pack(side=LEFT)
		player_names = get_players_from_session(SessionsData.active_sessionID)
		for player in players:
			next_row = Frame(labFrame2, pady=4, padx=14)
			next_row.pack(fill=X)
			lab1 = Label(next_row, text="{0}".format(player_names[str(player)]), font=textFont, pady=2, padx=2, width=14)
			lab1.pack(side=LEFT)
			n = 0
			mean = 0
			std = 0
			non_na_rounds = 0
			values = []
			for value in starting_round_amounts[player]:
				n = n + 1
				if not str(value) == "NA":
					non_na_rounds = non_na_rounds + 1
					mean = mean + int(value)
					values.append(value)
				if n % 2 == 0:
					bg_color = "#f4f4f4"
				else:
					bg_color = "white"
				lab2 = Label(next_row, text=str(value), font=textFont, pady=2, padx=2, width=7, bg=bg_color)
				lab2.pack(side=LEFT)
			if n < round_count:
				for x in range(n, round_count):
					if not x % 2 == 0:
						bg_color = "#f4f4f4"
					else:
						bg_color = "white"
					lab2 = Label(next_row, text="", font=textFont, pady=2, padx=2, width=7, bg=bg_color)
					lab2.pack(side=LEFT)
			mean = int(float(mean) / non_na_rounds)
			round_avg_lab2 = Label(next_row, text=str(mean), font=textFont, pady=2, padx=2, width=7, bg='white')
			round_avg_lab2.pack(side=LEFT)
			std = 0
			for value in values:
				std = std + math.pow(value - mean, 2)
			std = math.sqrt(float(std)/non_na_rounds)
			std_avg_lab2 = Label(next_row, text=str(std).split('.')[0], font=textFont, pady=2, padx=2, width=7, bg='white')
			std_avg_lab2.pack(side=LEFT)
		bottom_row = Frame(labFrame2, pady=4, padx=14)
		bottom_row.pack(fill=X)
		bottom_row2 = Frame(labFrame2, pady=4, padx=14)
		bottom_row2.pack(fill=X)
		round_avg_lab2 = Label(bottom_row, text="Mean", font=textFont, pady=2, padx=2, width=14)
		round_avg_lab2.pack(side=LEFT)
		std_avg_lab2 = Label(bottom_row2, text="Std", font=textFont, pady=2, padx=2, width=14)
		std_avg_lab2.pack(side=LEFT)
		values = []
		for x in range(0, round_count):
			if not x % 2 == 0:
				bg_color = "#f4f4f4"
			else:
				bg_color = "white"
			mean = 0
			px = 0
			non_na_players = 0
			for playerID in players:
				if x < len(starting_round_amounts[playerID]):
					px = px + 1
					if not str(starting_round_amounts[playerID][x]) == "NA":
						non_na_players = non_na_players + 1
						mean = mean + starting_round_amounts[playerID][x]
						values.append(starting_round_amounts[playerID][x])
			mean = int(float(mean) / non_na_players)
			round_avg_lab3 = Label(bottom_row, text=str(mean), font=textFont, pady=2, padx=2, width=7, bg=bg_color)
			round_avg_lab3.pack(side=LEFT)
			std = 0
			for value in values:
				std = std + math.pow(value - mean, 2)
			std = math.sqrt(float(std)/non_na_players)
			round_avg_lab4 = Label(bottom_row2, text=str(std).split('.')[0], font=textFont, pady=2, padx=2, width=7, bg=bg_color)
			round_avg_lab4.pack(side=LEFT)
		
class ExtraInfoWidget(Frame):
	
	def __init__(self, parent=None):
		global SessionsData
		Frame.__init__(self, parent)
		self.pack(expand=YES, fill=BOTH)
		textFont = Font(family='Helvetica', size=12, weight='normal')
		session_info_frame = Frame(self, pady=8, padx=4)
		session_info_frame.pack(side=TOP, fill=BOTH, expand=YES)
		player_info_frame = Frame(self, pady=8, padx=4)
		player_info_frame.pack(side=TOP, fill=X, expand=YES)
		labFrame1 = LabelFrame(session_info_frame, text="Match Summary", font=textFont, pady=4, padx=14)
		labFrame1.pack(fill=BOTH, expand=YES)
		self.session_info_widget = SessionInfoWidget(labFrame1)
		labFrame2 = LabelFrame(labFrame1, text="Players", font=textFont, pady=4, padx=4)
		labFrame2.pack(fill=BOTH, expand=YES)
		self.player_info_widget = PlayerInfoWidget(labFrame2)
		btn_row = Frame(labFrame1, pady=10)
		btn_row.pack(fill=X, expand=YES)
		killInfo_btn_padding_frame = Frame(btn_row, padx=4)
		killInfo_btn_padding_frame.pack(side=LEFT)
		maketInfo_btn_padding_frame = Frame(btn_row, padx=4)
		maketInfo_btn_padding_frame.pack(side=RIGHT)
		round_summary_btn_padding_frame = Frame(btn_row, padx=4)
		round_summary_btn_padding_frame.pack()
		killInfo_btn = Button(killInfo_btn_padding_frame, text="Kill Summary", command=self.callGraphKillInfo, font=textFont)
		marketInfo_btn = Button(maketInfo_btn_padding_frame, text="Starting Round Money", command=self.callGraphMarketInfo, font=textFont)
		round_summary_btn = Button(round_summary_btn_padding_frame, text="Round Summaries", command=self.callGraphMarketInfo, font=textFont)
		killInfo_btn.pack()
		marketInfo_btn.pack()
		round_summary_btn.pack()
		
	def refresh(self):
		self.session_info_widget.refresh()
		self.player_info_widget.refresh()
		
	def callGraphKillInfo(self):
		pass

	def callGraphMarketInfo(self):
		MarketInfoWidget()
	
def edit_settings_menu():
	global SessionsData, global_vars
	textFont = Font(family='Helvetica', size=11, weight='normal')
	settings_list = {
		"log_directory":"Log Directory",
		"MAX_CONFIG_VARIABLES":"Max Config Variables",
		"MAX_ROUNDS":"Max Rounds",
		"log_file_name":"Log File Name",
		"records_file_name":"Records File Name",
		"sessions_file_name":"Sessions File Name",
		"poll_pkey":"Poll Key",
		"login_skey":"Login Key",
		"logout_skey":"Logout Key",
		"config_vars_pkey":"Config Vars Key",
		"MAX_SESSIONS":"Max Sessions"
	}
	SessionsData.settings_win = Toplevel()
	inner_frame = Frame(SessionsData.settings_win, padx=10, pady=10)
	inner_frame.pack(expand=YES, fill=BOTH)
	labels = []
	label_max_len = -1
	entry_max_len = -1
	for setting in settings_list.items():
		if len(setting[1]) > label_max_len:
			label_max_len = len(setting[1])
		if len(str(global_vars[setting[0]])) > entry_max_len:
			entry_max_len = len(str(global_vars[setting[0]]))
	label_width = label_max_len - 1
	entry_width = entry_max_len + 3
	for setting in settings_list.items():
		SessionsData.settings_vars[setting[0]] = StringVar()
		SessionsData.settings_vars[setting[0]].set(global_vars[setting[0]])
		row_frame = Frame(inner_frame, pady=8)
		row_frame.pack(side=TOP, fill=X, expand=YES)
		lab = Label(row_frame, width=label_width, text=settings_list[setting[0]], font=textFont, anchor=W)
		ent = Entry(row_frame, textvariable=SessionsData.settings_vars[setting[0]], font=textFont, width=entry_width)
		lab.pack(side=LEFT)
		ent.pack(side=RIGHT, expand=YES, fill=X)
	final_row = row_frame = Frame(inner_frame, pady=20)
	final_row.pack(side=TOP, fill=X, expand=YES)
	separator = Separator(final_row)
	separator.pack(side=TOP, fill=X, expand=YES)
	butn1 = Button(inner_frame, text="Save and Continue", command=save_settings)
	butn1.pack(side=LEFT)
	butn2 = Button(inner_frame, text="Cancel", command=SessionsData.settings_win.destroy)
	butn2.pack(side=RIGHT)
	SessionsData.settings_win.focus_set()
	SessionsData.settings_win.grab_set()
	SessionsData.settings_win.wait_window()
	
def save_settings():
	global SessionsData
	str_value = ""
	for settings_var in SessionsData.settings_vars.items():
		str_value = str_value + "{0}={1}".format(settings_var[0],settings_var[1].get()) + "\n"
	file = open(global_vars['ini_file'], 'w')
	file.write(str_value)
	file.close()
	SessionsData.settings_win.destroy()
	showinfo("Edit Settings", "You must restart this program for new settings to take effect.")

def backup_log_file():
	try:
		shutil.copyfile(global_vars['log_file'], global_vars['backup_directory'] + "log-" + str(time.time()))
		os.remove(global_vars['log_file'])
	except IOError as e:
		print "I/O error({0}) - could not create backup log: {1}".format(e.errno, e.strerror)

#split one log file by matches, and write each match to a tmp file, the create session for each tmp file
def digest_session(log_file=global_vars['log_file']):
	global global_vars, SessionData
	try:
		file = open(log_file, 'r')
		file_string = file.read()
		file.close()
	except IOError as e:
		print "I/O error({0}): {1}. Could not open or read file {2}".format(e.errno, e.strerror, log_file)
		return
	matches = file_string.split(global_vars['match_split_string'])
	del matches[0]
	new_session_files = []
	n = -1
	for match_string in matches:
		n = n + 1
		file_string = global_vars['tmp_directory'] + str(n) + '.txt'
		new_session_files.append(file_string)
		file = open(file_string, 'w')
		file.write(match_string)
		file.close()
	return new_session_files
		
class MainWindowFrame(Frame):

	def __init__(self, parent=None):
		global SessionsData, global_vars
		Frame.__init__(self, parent)
		self.pack(expand=YES, fill=BOTH)
		self.makeMenu(parent)
		
		LeftWindow = Frame(self)
		RightWindow = Frame(self)
		LeftWindow.pack(side=LEFT, expand=YES, fill=Y)
		RightWindow.pack(side=RIGHT, expand=YES, fill=Y)
		
		LeftWindowUpper = Frame(LeftWindow)
		LeftWindowUpper.pack(side=TOP, expand=YES, fill=X)
		LeftWindowMiddle = Frame(LeftWindow)
		LeftWindowMiddle.pack(side=TOP, expand=YES, fill=X)
		LeftWindowBottom = Frame(LeftWindow)
		LeftWindowBottom.pack(side=TOP, expand=YES, fill=X)
		
		LeftWindowBottomLeft = Frame(LeftWindowBottom)
		LeftWindowBottomLeft.pack(side=LEFT, expand=YES, fill=Y)
		LeftWindowBottomRight = Frame(LeftWindowBottom)
		LeftWindowBottomRight.pack(side=RIGHT, expand=YES, fill=Y)
		
		ConfigVarsWidgetRef = ConfigVarsWidget(RightWindow)
		
		ExtraInfoWidgetRef = ExtraInfoWidget(LeftWindowBottomLeft)
		VizualizationWidgetRef = VizualizationWidget(LeftWindowBottomRight)
		
		#VizualizationOptionsWidgetRef = VizualizationOptionsWidget(RightBottomLeftWindow)
		#VizualizationTypeWidgetRef = VizualizationTypeWidget(LeftBottomLeftWindow, VizualizationOptionsWidgetRef)
		#SessionsWidgetRef = SessionsWidget(LeftWindowUpper, ConfigVarsWidgetRef, VizualizationTypeWidgetRef)
		
		SessionsWidgetRef = SessionsWidget(LeftWindowUpper)
		SessionsData.config_vars_widget = ConfigVarsWidgetRef
		SessionsData.sessions_widget = SessionsWidgetRef
		SessionsData.extra_info_widget = ExtraInfoWidgetRef
		EditSessionWidget(LeftWindowMiddle)

	def makeMenu(self, win):
		top = Menu(win)
		win.config(menu=top)
		textFont = Font(family='Helvetica', size=11, weight='normal')
		file = Menu(top, tearoff=0, font=textFont)
		file.add_command(label='New Session',  command=self.new_session,  underline=0)
		file.add_command(label='New Session (choose log file)',  command=self.new_session_choose,  underline=0)
		top.add_cascade(label='File',     menu=file,        underline=0)
		
		edit = Menu(top, tearoff=0, font=textFont)
		edit.add_command(label='Delete Selected Sessions',  command=self.delete_sessions,  underline=0)
		edit.add_command(label='Main Settings',  command=self.main_settings,  underline=0)
		top.add_cascade(label='Edit',     menu=edit,        underline=0)

	def new_session_choose(self):
		global global_vars
		try:
			fileName = askopenfilename(initialdir=global_vars['log_directory'])
			if fileName:
				kk = fileName.replace("/", r'\\')
				log_file = kk
				splits = digest_session(log_file)
				for split in splits:
					create_session([], "", log_file=split, refresh_sessions_widget=True)
			else:
				return
		except IOError:
			print "IOError. Could not open file."

	def new_session(self):
		if not os.path.isfile(global_vars['log_file']):
			showinfo("New Session", "No log file found at {0}".format(global_vars['log_directory']))
		else:
			splits = digest_session(log_file)
			for split in splits:
				create_session([], log_file=split, refresh_sessions_widget=True)
			if askyesno('New Session', 'Log file digested! Relocate log file to back up folder (recommended)?'):
				backup_log_file()

	def delete_sessions(self):
		if askyesno('Delete Sessions?', 'Delete selected sessions?'):
			delete_sessions(SessionsData.selected_sessionIDs)			
			SessionsData.sessions_widget.scrollList.refreshList()
			SessionsData.config_vars_widget.ConfigVarsScrollListRef.refresh()
			SessionsData.extra_info_widget.refresh()
		
	def main_settings(self):
		edit_settings_menu()


def mainguiloop(guiRoot):
	guiRoot.mainloop()


if __name__ == '__main__':
	set_globalvars()
	SessionsData = SessionsObject()
	#str_value = json.dumps(bar_data(include_zero_values=True), indent=4)
	#file = open(global_vars['install_directory'] + 'tmp.txt', 'w')
	#file.write(str_value)
	#file.close()
	root = Tk()
	#root.geometry('1400x800+100+70') #"wxh+x+y" (width, height, xoffset, yoffset)
	root.title('CPI Game Analyzer')
	MainWindowFrame(root)
	mainguiloop(root)
	
	
	
#TODO
#add title for the amount axis


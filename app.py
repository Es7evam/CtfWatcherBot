import logging
import sys
import os
import urllib.request
import json
import datetime
import threading
import time
import traceback
import pickle

from collections import defaultdict

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ParseMode
from telegram.utils.helpers import escape_markdown

import eventScrapper

class App:
	def __init__(self):
		try:
			self.load()
		except FileNotFoundError:
			print("JSON file with token not found")
			exit(0)

		logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

		self.updater = Updater(token=self.key, use_context=False)
		self.dispatcher = self.updater.dispatcher

		self.dispatcher.add_handler(CommandHandler('start', self.start))
		self.dispatcher.add_handler(CommandHandler('help', self.help))
		self.dispatcher.add_handler(CommandHandler('subscribe', self.subscribe, pass_args=True))
		self.dispatcher.add_handler(CommandHandler('unsubscribe', self.unsubscribe, pass_args=True))
		self.dispatcher.add_handler(CommandHandler('listSubscribed', self.listSubscribed))
		self.dispatcher.add_handler(CommandHandler('upcoming', self.upcoming))
		self.dispatcher.add_handler(CommandHandler('getTimezone', self.getTimezone))
		self.dispatcher.add_handler(CommandHandler('setTimezone', self.setTimezone, pass_args=True))
		self.dispatcher.add_handler(CommandHandler('now', self.now))
		# self.dispatcher.add_handler(CommandHandler('list_events', self.list_events, pass_args=True))

		self.jobs = self.updater.job_queue
		self.tick_job = self.jobs.run_repeating(self.tick, interval=self.interval, first=0)

		self.subscribersLock = threading.Lock()

	def load(self):
		with open('config.json', 'r') as f:
			o = json.load(f)
			self.subscribers = set(o['subscribers']) if 'subscribers' in o else set()
			if 'teamSubscribers' in o:
				self.teamSubscribers = eventScrapper.listToDict(defaultdict(list, o['teamSubscribers']))
				#eventScrapper.listToDict(o['teamSubscribers']) 
				#self.teamSubscribers = eventScrapper.listToDict(o['teamSubscribers']) 
			else: 
				self.teamSubscribers = defaultdict(list)
			self.interval = o['interval'] if 'interval' in o else 300
			self.key = o['key']
		with open('db.json', 'r') as dbFile:
			db = json.load(dbFile)
			self.dayWarned = set(db['dayWarned']) if 'dayWarned' in db else set()
			self.hourWarned = set(db['hourWarned']) if 'hourWarned' in db else set()
			self.timezones = dict()
			if 'timezones' in db:
				for chat, tz in db['timezones'].items():
					self.timezones[int(chat)] = tz


	def save(self):
		with open('config.json', 'w') as f:
			json.dump({
				'subscribers': list(self.subscribers),
				'teamSubscribers' : defaultdict(list, self.teamSubscribers.items() ),
				'interval': self.interval,
				'key': self.key,
			}, f, indent=4)

		with open('db.json', 'w') as dbFile:
			json.dump({
                'dayWarned': list(self.dayWarned),
				'hourWarned': list(self.hourWarned),
				'timezones': dict(self.timezones),
			}, dbFile, indent=4)


	def run(self):
		self.updater.start_polling()

	def start(self, bot, update):
		msg = "Welcome to CtfWatcherBot \\o/\n"
		msg += "Type /help for a list of functionalities."
		bot.send_message(chat_id=update.message.chat_id, text=msg)

	def help(self, bot, update):
		msg = "Hey, I'm CtfWatcher Bot :D. I list Capture The Flag competitions."
		msg += "\n\nI currently have this commands:\n\n"
		msg += "/start - Starts the bot.\n"
		msg += "/upcoming - Shows the next month's CTFs, maximum of 5.\n"
		msg += "/now - Shows the CTFs happening right now.\n"
		msg += "/subscribe [all]- Subscribes for all CTF notifications (1 day and also 1 hour before).\n"
		msg += "/subscribe TeamName - Subscribes for the specified CTF notifications.\n"
		msg += "/unsubscribe - Unsubscribes for all CTF notifications.\n"
		msg += "/unsubscribe TeamName - Unsubscribes a team from the notifications.\n"
		msg += "/listSubscribed - Lists all the teams subscribed in this chat.\n"
		msg += "/getTimezone - Shows the timezone in this chat.\n"
		msg += "/setTimezone [TZ] - Sets the timezone to UTC + TZ (can be negative) in this chat.\n"
		msg += "/help - Shows this help message.\n"
		msg += "\nBe sure to check our [Github repo](https://github.com/Es7evam/CtfWatcherBot)."
		bot.send_message(chat_id=update.message.chat_id, text=msg, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True )

	def listSubscribed(self, bot, update):
		try:
			chat_id = update.message.chat_id
		except AttributeError:
			# Message was edited instead of sent
			chat_id = (update['edited_message']['chat'])['id']

		msg = ""
		if chat_id in self.subscribers:
			msg += "This chat is subscribed to all CTFs!\n\n"
		else:
			msg += "This chat is not subscribed to all CTFs!\n\n"

		if len(self.teamSubscribers[chat_id]) > 0:
			msg += "The following teams are subscribed in this chat (case insensitive):\n"
			for team in self.teamSubscribers[chat_id]:
				msg += ' - {}\n'.format(team) 
		else:
			msg += "There are no teams subscribed in this chat!"
		
		bot.send_message(chat_id=chat_id, text=msg)

	def setTimezone(self, bot, update, args):
		try:
			chat_id = update.message.chat_id
		except AttributeError:
			# Message was edited instead of sent
			chat_id = (update['edited_message']['chat'])['id']

		msg = ""
		if len(args) ==0:
			msg = "Please specify timezone in the message!\n E.g.: /setTimezone -3"
			bot.send_message(chat_id=chat_id, text=msg)
			return

		try:
			self.timezones[chat_id] = int(args[0])
			msg = "Timezone of this chat set to UTC"
			strTz = self.tzToString(int(args[0]))
			msg += strTz

			bot.send_message(chat_id=chat_id, text=msg)
		except Exception as e:
			msg = "Error setting timezone, please contact an admin if you think this is a bug."
			bot.send_message(chat_id=chat_id, text=msg)
			print("Error setTimezone", str(e))

		self.save()

	def getTimezone(self, bot, update):
		try:
			chat_id = update.message.chat_id
		except AttributeError:
			# Message was edited instead of sent
			chat_id = (update['edited_message']['chat'])['id']

		tz = self.timezones.get(chat_id)

		# Makes the pretty message
		if tz == None:
			msg = "The timezone of this chat is UTC+00:00"
		else:
			msg = "The timezone of this chat is UTC"
			strTz = self.tzToString(tz)
			msg += strTz

		bot.send_message(chat_id=chat_id, text=msg)
		

	# Receives an integer and return the UTC+XX:00 message
	def tzToString(self, intTimezone):
		if intTimezone >= 0:
			strTz = str(intTimezone).zfill(2)
			strTz = "+" + strTz 
		else:
			strTz = str(intTimezone).zfill(3)

		strTz += ":00"
		return strTz


	def subscribe(self, bot, update, args):
		chat_id = update.message.chat_id
		print("User @{} is subscribing!".format(update.message.from_user['username']))
		commands = ' '.join(args)	

		if len(commands) == 0 or commands == "all":
			with self.subscribersLock:
				if(chat_id in self.subscribers):
					bot.send_message(chat_id=chat_id, text="Already subscribed!")
					return
				self.subscribers.add(chat_id)
				bot.send_message(chat_id=chat_id, text="Subscribed for all CTFs successfully!")
		else:
			with self.subscribersLock:
				if commands.lower() in self.teamSubscribers[chat_id]:
					msg = "This team is already subscribed in this chat!"
				else:
					self.teamSubscribers[chat_id].append(commands.lower())
					msg = "Team {} subscribed in this chat successfully.".format(commands)

				bot.send_message(chat_id=chat_id, text=msg)

		self.save()
				

	def unsubscribe(self, bot, update, args):
		chat_id = update.message.chat_id
		teamName = (' '.join(args)).lower()
		print("User @{} is unsubscribing in chat {}!".format(update.message.from_user['username'], chat_id))

		with self.subscribersLock:
			if len(teamName) == 0 or teamName == 'all':
				if(chat_id in self.subscribers):
					self.subscribers.remove(chat_id)
					bot.send_message(chat_id=chat_id, text="Unsubscribed successfully :(")
				else:
					if len(self.teamSubscribers[chat_id]) > 0:
						self.teamSubscribers[chat_id].clear()
						bot.send_message(chat_id=chat_id, text="Unsubscribed all teams in this chat.")
					else:
						bot.send_message(chat_id=chat_id, text="Chat not subscribed!")
			else:
				if teamName in self.teamSubscribers[chat_id]:
					self.teamSubscribers[chat_id].remove(teamName.lower())
					msg = 'Unsubscribed team {} in this chat'.format(teamName)
					bot.send_message(chat_id=chat_id, text=msg)
				else:
					msg = 'Team {} not subscribed in this chat!'.format(teamName)
					bot.send_message(chat_id=chat_id, text=msg)

		self.save()

				

	def sendWarning(self, bot, job, msg, ctfid):
		print("Sending warning, ctf_id: {}. ".format(ctfid))
		teamList = eventScrapper.getEventParticipants(ctfid)
		with self.subscribersLock:
			for subscriber in self.subscribers:
				try:
					bot.send_message(chat_id=subscriber, text=msg, parse_mode=ParseMode.MARKDOWN)
				except:
					print("Message to user %s failed" % (subscriber))

			for chat in self.teamSubscribers:
				hasTeam = False
				for team in self.teamSubscribers[chat]:
					if team in teamList:
						print("\tTeam {} in list of chat {}!".format(team, chat))
						hasTeam = True

				if hasTeam == True:	
					bot.send_message(chat_id=int(chat), text=msg, parse_mode=ParseMode.MARKDOWN)



	def tick(self, bot, job):
		now = datetime.datetime.utcnow()
		fmtstr = '%Y-%m-%dT%H:%M:%S'

		reqHeader = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
    	'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    	'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
    	'Accept-Encoding': 'none',
    	'Accept-Language': 'en-US,en;q=0.8',
		'Connection': 'keep-alive'}

		# Getting CTFs from API
		callurl = 'https://ctftime.org/api/v1/events/?limit=5&start={}'.format(now.timestamp())
		print("\n\nCall URL: ", callurl, "\n")
		try:
			req = urllib.request.Request(callurl, headers=reqHeader)
			fDay = urllib.request.urlopen(req)
			ctfList = json.load(fDay)
			for ctf in ctfList:
				ctf['start'] = datetime.datetime.strptime(ctf['start'][:-6], fmtstr)
		except Exception as e:
			print("\nError requesting CTFTime API: " + str(e))
		
		print("Checking. Date: ", now)
		# Check if in dayWarned and hourWarned
		# If not, create a warning and put in it
		try:
			for ctf in ctfList:
				ctf['title'] = escape_markdown(ctf['title'])
				# Time until the start of the ctf
				timedelta = ctf['start'] - now

				if (str(ctf['id']) not in self.dayWarned) and timedelta.days <= 1:
					print("Adding ctf {} to the dayWarned set".format(ctf['id']))
					(self.dayWarned).add(str(ctf['id']))

					seconds = (timedelta.days * 86400) + timedelta.seconds - 86400

					if seconds < 0:
						seconds = 0

					msg = "[" + ctf['title'] + "](" + ctf['url'] + ") ([" + str(ctf['id']) + "](https://ctftime.org/event/" + str(ctf['id']) + ")) will start in 1 day."
					timer = threading.Timer(seconds, self.sendWarning, [bot, job, msg, ctf['id']])
					timer.start()

				if (str(ctf['id']) not in self.hourWarned) and timedelta.days == 0 and timedelta.seconds/3600 < 5:
					print("Adding ctf {} to the hourWarned set".format(ctf['id']))
					(self.hourWarned).add(str(ctf['id']))

					seconds = timedelta.seconds - 3600 # minus 1 hour

					if seconds < 0:
						seconds = 0

					msg = "[" + ctf['title'] + "](" + ctf['url'] + ") ([" + str(ctf['id']) + "](https://ctftime.org/event/" + str(ctf['id']) + ")) will start in 1 hour."
					timer = threading.Timer(seconds, self.sendWarning, [bot, job, msg, ctf['id']])
					timer.start()

				if timedelta.days < 0:
					msg = "[" + ctf['title'] + "](" + ctf['url'] + ") started already."
					self.sendWarning(bot, job, msg, ctf['id'])
		except UnboundLocalError as e:
			print("CTFTime is offline" + str(e))

		print(self.dayWarned)

		
		# Check scoreboard of CTFs that may have ended
		# Optimize this in the future by looking a week after finish
		toRemove = []
		for ctf_id in self.hourWarned:
			scores, ctfTitle = eventScrapper.getScoreboard(ctf_id)
			ctfTitle = escape_markdown(ctfTitle)
			if len(scores) > 0:
				for chat in self.teamSubscribers:
					msg = "*" + ctfTitle + "* has ended and the ratings are out.\n\n"
					hasTeam = False
					for team in self.teamSubscribers[chat]:
						for teamScore in scores:
							if team == teamScore[0].lower():
								hasTeam = True
								msg += "*" + teamScore[0] + "*: +" + teamScore[2] + "points\n"
								
					if hasTeam == True:	
						bot.send_message(chat_id=int(chat), text=msg, parse_mode=ParseMode.MARKDOWN)

				# CTF is over, remove from lists
				toRemove.append(ctf_id)

		for ctf_id in toRemove:
			self.dayWarned.remove(ctf_id)
			self.hourWarned.remove(ctf_id)

		self.save()


	def list_events(self, timezone):
		fmtstr = '%Y-%m-%dT%H:%M:%S'
		now = int(time.time())
		nextweek = now + 604800 * 4 # printing time in weeks

		reqHeader = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
    	'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    	'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
    	'Accept-Encoding': 'none',
    	'Accept-Language': 'en-US,en;q=0.8',
		'Connection': 'keep-alive'}

		reqUrl = 'https://ctftime.org/api/v1/events/?limit=5&start={}&finish={}'.format(now, nextweek)
		req = urllib.request.Request(reqUrl, headers=reqHeader)
		f = urllib.request.urlopen(req)
		l = json.load(f)
		newL = []
		genstr = '%a, %B %d, %Y %H:%M UTC'	#

		timeDelta = datetime.timedelta(hours=timezone)

		for o in l:
			o['start'] = datetime.datetime.strptime(o['start'][:-6], fmtstr) + timeDelta
			o['start'] = o['start'].strftime(genstr)
			newL.append(o)

		return newL


	def upcoming(self, bot, update):
		chat_id = update.message.chat_id
		timezone = self.timezones.get(chat_id)
		if timezone == None:
			timezone = 0

		l = self.list_events(timezone)
		msg = "*Upcoming Events:*"
		for o in l:
			o['title'] = escape_markdown(o['title'])
			msg += '\n' + '[' + o['title'] + ']' + '(' + o['url'] + ') (' + '[' + str(o['id']) + ']' + '(https://ctftime.org/event/' + str(o['id']) + ')' + ')' + '\n'
			msg += o['format'] + '\n'
			msg += str(o['start']) + self.tzToString(timezone) + '\n'
			msg += 'Weight: ' + str(int(o['weight'])) + ' points \n'
			if(o['duration']['days'] > 1):
				msg += 'Duration: ' + str(o['duration']['days']) + ' days'
				if(o['duration']['hours']):
					msg += ' and ' + str(o['duration']['hours']) + ' hours\n'
				else:
					msg += '\n'
			elif(o['duration']['days'] == 1):
				msg += 'Duration: ' + str(o['duration']['days']) + ' day'
				if(o['duration']['hours']):
					msg += ' and ' + str(o['duration']['hours']) + ' hours\n'
				else:
					msg += '\n'
			else: #0 days
				if(o['duration']['hours']):
					msg += 'Duration: ' + str(o['duration']['hours']) + ' hours\n'


		if update.message.chat.type == 'private':
			print("User %s requested upcoming CTFs at %d" % (update.message.chat.username, int(time.time())))
		bot.send_message(chat_id=update.message.chat_id, text=msg, parse_mode=ParseMode.MARKDOWN)


	def list_happening(self):
		fmtstr = '%Y-%m-%dT%H:%M:%S'
		now = int(time.time())
		daysAgo = now - 300000

		reqHeader = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
    	'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    	'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
    	'Accept-Encoding': 'none',
    	'Accept-Language': 'en-US,en;q=0.8',
		'Connection': 'keep-alive'}

		req = urllib.request.Request('https://ctftime.org/api/v1/events/?limit=5&start={}'.format(daysAgo), headers=reqHeader)
		f = urllib.request.urlopen(req)
		l = json.load(f)
		newL = []
		genstr = '%a, %B %d, %Y %H:%M UTC '	#

		for o in l:			
			o['start'] = datetime.datetime.strptime(o['start'][:-6], fmtstr)	
			o['finish'] = datetime.datetime.strptime(o['finish'][:-6], fmtstr)	
			o['title'] = escape_markdown(o['title'])
			if(int(o['start'].timestamp()) > daysAgo):
				if(int(o['finish'].timestamp()) > now) and (int(o['start'].timestamp() < now)):
					o['start'] = o['start'].strftime(genstr)
					newL.append(o)

		return newL

	def now(self, bot, update):
		l = self.list_happening()
		msg = "*Events Happening Now:*"
		for o in l:
			msg += '\n' + '[' + o['title'] + ']' + '(' + o['url'] + ') ' + '\n'
			msg += o['format'] + '\n'
			msg += 'Started: ' + str(o['start']) + '\n'
			if(o['duration']['days'] > 1):
				msg += 'Duration: ' + str(o['duration']['days']) + ' days'
				if(o['duration']['hours']):
					msg += ' and ' + str(o['duration']['hours']) + ' hours\n'
				else:
					msg += '\n'
			elif(o['duration']['days'] == 1):
				msg += 'Duration: ' + str(o['duration']['days']) + ' day'
				if(o['duration']['hours']):
					msg += ' and ' + str(o['duration']['hours']) + ' hours\n'
				else:
					msg += '\n'
			else: #0 days
				if(o['duration']['hours']):
					msg += 'Duration: ' + str(o['duration']['hours']) + ' hours\n'

		bot.send_message(chat_id=update.message.chat_id, text=msg, parse_mode=ParseMode.MARKDOWN)


if __name__ == '__main__':
	App().run()

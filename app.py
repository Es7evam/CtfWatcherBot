import logging
import sys
import os
import urllib.request
import json
import datetime
import threading
import time
import traceback


from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ParseMode


class App:
	def __init__(self):
		try:
			self.load()
		except FileNotFoundError:
			print("JSON file with token not found")
			exit(0)

		logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

		self.updater = Updater(token=self.key)
		self.dispatcher = self.updater.dispatcher

		self.dispatcher.add_handler(CommandHandler('start', self.start))
		self.dispatcher.add_handler(CommandHandler('help', self.help))
		self.dispatcher.add_handler(CommandHandler('subscribe', self.subscribe))
		self.dispatcher.add_handler(CommandHandler('unsubscribe', self.unsubscribe))
		self.dispatcher.add_handler(CommandHandler('upcoming', self.upcoming))
		self.dispatcher.add_handler(CommandHandler('now', self.now))
		# self.dispatcher.add_handler(CommandHandler('list_events', self.list_events, pass_args=True))

		self.jobs = self.updater.job_queue
		self.tick_job = self.jobs.run_repeating(self.tick, interval=self.interval, first=0)

		self.subscribersLock = threading.Lock()

	def load(self):
		with open('config.json', 'r') as f:
			o = json.load(f)
			self.subscribers = set(o['subscribers']) if 'subscribers' in o else set()
			self.interval = o['interval'] if 'interval' in o else 300
			self.key = o['key']

	def save(self):
		with open('config.json', 'w') as f:
			json.dump({
				'subscribers': list(self.subscribers),
				'interval': self.interval,
				'key': self.key,
			}, f, indent=4)

	def run(self):
		self.updater.start_polling()

	def start(self, bot, update):
		msg = "Welcome to CtfWatcherBot \o/\n"
		msg += "Type /help for a list of functionalities."
		bot.send_message(chat_id=update.message.chat_id, text=msg)

	def help(self, bot, update):
		msg = "Hey, I'm CtfWatcher Bot :D. I list Capture The Flag competitions."
		msg += "\n\nI currently have this commands:\n\n"
		msg += "/start - start the bot.\n"
		msg += "/upcoming - show the next month's CTFs, maximum of 5.\n"
		msg += "/now - show the CTFs happening right now.\n"
		msg += "/subscribe - subscribes for CTF notifications (1 day and also 1 hour before).\n"
		msg += "/unsubscribe - unsubscribe for CTF notifications.\n"
		msg += "/help - shows this help message.\n"
		msg += "\nBe sure to check our [Github repo](https://github.com/Es7evam/CtfWatcherBot)."
		bot.send_message(chat_id=update.message.chat_id, text=msg, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True )


	def subscribe(self, bot, update):
		chat_id = update.message.chat_id

		with self.subscribersLock:
			if(chat_id in self.subscribers):
				bot.send_message(chat_id=chat_id, text="Already subscribed!")
				return
			self.subscribers.add(chat_id)
			self.save()
			bot.send_message(chat_id=chat_id, text="Subscribed successfully!")

	def unsubscribe(self, bot, update):
		chat_id = update.message.chat_id

		with self.subscribersLock:
			if(chat_id in self.subscribers):
				self.subscribers.remove(chat_id)
				self.save()
				bot.send_message(chat_id=chat_id, text="Unsubscribed successfully :(")
				return

			bot.send_message(chat_id=chat_id, text="User not subscribed!")

	def tick(self, bot, job):
		oneDay = int(time.time()) + 86400 #1 day
		oneHour = int(time.time()) + 3600 #1 hour

		fmtstr = '%Y-%m-%dT%H:%M:%S'

		reqHeader = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
    	'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    	'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
    	'Accept-Encoding': 'none',
    	'Accept-Language': 'en-US,en;q=0.8',
		'Connection': 'keep-alive'}

		try:
			callurl = 'https://ctftime.org/api/v1/events/?limit=1&start={}'.format(oneDay-300)
			req = urllib.request.Request(callurl, headers=reqHeader)
			fDay = urllib.request.urlopen(req)
			lDay = json.load(fDay)
			for oDay in lDay:
				oDay['start'] = datetime.datetime.strptime(oDay['start'][:-6], fmtstr)
		except Exception as e:
			print("Error requesting CTFTime API: " + str(e))


		
		try:
			callurl = 'https://ctftime.org/api/v1/events/?limit=1&start={}'.format(oneHour-300)
			req = urllib.request.Request(callurl, headers=reqHeader)
			fHour = urllib.request.urlopen(req)
			lHour = json.load(fHour)
			for oHour in lHour:
				oHour['start'] = datetime.datetime.strptime(oHour['start'][:-6], fmtstr)
		except Exception as e:
			print("Error requesting CTFTime API" + str(e))

		#print(int(o['start'].timestamp())) # starting event time
		with self.subscribersLock:
			for subscriber in self.subscribers:
				if(int(oDay['start'].timestamp()) < oneDay):
					msg = "[" + oDay['title'] + "](" + oDay['url'] + ") will start in 1 day."
					bot.send_message(chat_id=subscriber, text=msg, parse_mode=ParseMode.MARKDOWN)
				if(int(oHour['start'].timestamp()) < oneHour):
					msg = '[' + oHour['title'] + '](' + oHour['url'] + ") will start in 1 hour."
					bot.send_message(chat_id=subscriber, text=msg, parse_mode=ParseMode.MARKDOWN)

	def list_events(self):
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
		genstr = '%a, %B %d, %Y %H:%M UTC '	#

		for o in l:
			o['start'] = datetime.datetime.strptime(o['start'][:-6], fmtstr)
			o['start'] = o['start'].strftime(genstr)
			newL.append(o)

		return newL


	def upcoming(self, bot, update):
		l = self.list_events()
		msg = "*Upcoming Events:*"
		for o in l:
			msg += '\n' + '[' + o['title'] + ']' + '(' + o['url'] + ') ' + '\n'
			msg += o['format'] + '\n'
			msg += str(o['start']) + '\n'
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

		f = urllib.request.urlopen('https://ctftime.org/api/v1/events/?limit=5&start={}'.format(daysAgo))
		l = json.load(f)
		newL = []
		genstr = '%a, %B %d, %Y %H:%M UTC '	#

		for o in l:			
			o['start'] = datetime.datetime.strptime(o['start'][:-6], fmtstr)	
			o['finish'] = datetime.datetime.strptime(o['finish'][:-6], fmtstr)	
			if(int(o['start'].timestamp()) > daysAgo):
				if(int(o['finish'].timestamp()) > now):
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

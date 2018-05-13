import logging
import sys
import os
import urllib.request
import json
import datetime
import threading
import time

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
        msg += "Type /help for a list of functionalities"
        bot.send_message(chat_id=update.message.chat_id, text=msg)

    def help(self, bot, update):
        msg = "Hey, I'm CtfWatcher Bot :D. I list Capture The Flag competitions."
        msg += "\n\nI currently have this commands:\n\n"
        msg += "/start - start the bot.\n"
        msg += "/upcoming - show the next month's CTFs, maximum of 5.\n"
        msg += "/subscribe - subscribes for CTF notifications (1 day before).\n"
        msg += "/unsubscribe - unsubscribe for CTF notifications.\n"
        msg += "/help - shows this help message."
        bot.send_message(chat_id=update.message.chat_id, text=msg)


    def subscribe(self, bot, update):
        chat_id = update.message.chat_id

        with self.subscribersLock:
            self.subscribers.add(chat_id)
            self.save()
            bot.send_message(chat_id=chat_id, text="Subscribed successfully!")

    def unsubscribe(self, bot, update):
        chat_id = update.message.chat_id

        with self.subscribersLock:
            self.subscribers.remove(chat_id)
            self.save()

    def tick(self, bot, job):
        startTime = int(time.time()) + 86400 #1 day
        fmtstr = '%Y-%m-%dT%H:%M:%S'

        f = urllib.request.urlopen('https://ctftime.org/api/v1/events/?limit=1&start={}'.format(startTime-300))
        l = json.load(f)
        for o in l:
            o['start'] = datetime.datetime.strptime(o['start'][:-6], fmtstr)

        #print(int(o['start'].timestamp())) # starting event time
        with self.subscribersLock:
            for subscriber in self.subscribers:
                if(int(o['start'].timestamp()) < startTime):
                    msg = "[" + o['title'] + "](" + o['url'] + ") will start in 1 day."
                    bot.send_message(chat_id=subscriber, text=msg, parse_mode=ParseMode.MARKDOWN)

    def list_events(self):
        fmtstr = '%Y-%m-%dT%H:%M:%S'
        now = int(time.time())
        nextweek = now + 604800 * 4 # printing time in weeks

        f = urllib.request.urlopen('https://ctftime.org/api/v1/events/?limit=5&start={}&finish={}'.format(now, nextweek))
        l = json.load(f)
        newL = []
        genstr = '%a, %B %d, %Y %H:%M UTC '    #

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

        bot.send_message(chat_id=update.message.chat_id, text=msg, parse_mode=ParseMode.MARKDOWN)

if __name__ == '__main__':
    App().run()

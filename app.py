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
        self.load()

        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

        self.updater = Updater(token=self.key)
        self.dispatcher = self.updater.dispatcher

        self.dispatcher.add_handler(CommandHandler('start', self.start))
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
            self.interval = o['interval'] if 'interval' in o else 60
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
        pass

    def subscribe(self, bot, update):
        chat_id = update.message.chat_id

        with self.subscribersLock:
            self.subscribers.add(chat_id)
            self.save()

    def unsubscribe(self, bot, update):
        chat_id = update.message.chat_id

        with self.subscribersLock:
            self.subscribers.remove(chat_id)
            self.save()

    def tick(self, bot, job):
        with self.subscribersLock:
            for subscriber in self.subscribers:
                bot.send_message(chat_id=subscriber, text="yo!")

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

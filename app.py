import logging
import sys
import os
import urllib.request
import json
import datetime
import threading

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters


class App:
    def __init__(self):
        self.load()

        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

        self.updater = Updater(token=self.key)
        self.dispatcher = self.updater.dispatcher

        self.dispatcher.add_handler(CommandHandler('start', self.start))
        self.dispatcher.add_handler(CommandHandler('subscribe', self.subscribe))
        self.dispatcher.add_handler(CommandHandler('unsubscribe', self.unsubscribe))
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

    # def list_events(self, bot, update, args):
    #     fmtstr = '%Y-%m-%dT%H:%M:%S'
    #     start, finish = args

    #     f = urllib.request.urlopen('https://ctftime.org/api/v1/events/?limit=20&start={}&finish={}'.format(start, finish))
    #     l = json.load(f)
    #     newL = []

    #     for o in l:
    #         if not o['onsite']:
    #             o['start'] = datetime.datetime.strptime(o['start'][:-6], fmtstr)
    #             o['finish'] = datetime.datetime.strptime(o['finish'][:-6], fmtstr)
    #             newL.append(o)

    #     return newL


if __name__ == '__main__':
    App().run()

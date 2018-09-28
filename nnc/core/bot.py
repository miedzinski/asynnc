import asyncio
import collections
import functools

import peewee_async

from nnc.core import plugin, protocol
from nnc.core.db import BaseModel

_IRC_HANDLERS = collections.defaultdict(list)


def irc(callback=None, numeric=None, cmd=None):
    if callback is None:
        return functools.partial(irc, numeric=numeric, cmd=cmd)
    if (numeric and cmd) or not (numeric or cmd):
        raise ValueError('numeric or cmd')
    if numeric and not str.isnumeric(numeric):
        numeric = protocol.NUMERICS[numeric]

    _IRC_HANDLERS[numeric or cmd].append(callback)
    return callback


class Bot:
    def __init__(self, config, loop=None):
        self.config = config
        self.loop = loop

        self.protocol = protocol.IrcProtocol(self, config.encoding)

        self.nick = config.nick

        self.modules = {}

        self.database = db = peewee_async.PostgresqlDatabase(
            database=config.db.name,
            user=config.db.user,
            host=config.db.host,
            port=config.db.port,
        )
        db.set_allow_sync(False)
        BaseModel._meta.database = db
        self.objects = peewee_async.Manager(db)

        self.channels = collections.defaultdict(set)

    def send_raw(self, msg):
        self.protocol.write(msg)

    def send(self, cmd, *params):
        params = list(params)
        if ' ' in params[-1]:
            params[-1] = ':' + params[-1]
        self.protocol.write('%s %s' % (cmd, ' '.join(map(str, params))))

    def handle(self, msg):
        for cb in _IRC_HANDLERS[msg.command]:
            self.schedule(cb, msg)

    def schedule(self, func, *args, **kwargs):
        if not asyncio.iscoroutinefunction(func):
            func = asyncio.coroutine(func)
        self.loop.create_task(func(self, *args, **kwargs))

    def connect(self):
        return self.loop.create_connection(
            protocol_factory=lambda: self.protocol,
            host=self.config.host,
            port=self.config.port,
            ssl=self.config.ssl,
        )

    def connected(self):
        self.send('USER', self.config.nick, 0, '*', self.config.nick)
        self.set_nick(self.config.nick)

    def disconnected(self):
        interval = self.config.reconnection_interval
        self.loop.call_later(interval, self.connect)

    def load(self, mod):
        self.modules[mod.__name__] = mod

    def unload(self, name):
        self.modules.pop(name)

    def say(self, target, text):
        self.send('PRIVMSG', target, text)

    def reply(self, msg, text):
        if msg.channel:
            self.say(msg.channel, text)
        else:
            self.say(msg.nick, text)

    def set_nick(self, nick):
        self.send('NICK', nick)
        self.nick = nick


@irc(cmd='PRIVMSG')
async def dispatch_privmsg(bot, msg):
    text = msg.params[-1]

    if text.startswith(bot.config.cmd_trigger):
        cmd = text[1:].split(' ', 1)[0]
        for cmd_handlers in plugin.CMD_HANDLERS.values():
            if cmd in cmd_handlers:
                bot.schedule(cmd_handlers[cmd], msg)

    for re_handlers in plugin.RE_HANDLERS.values():
        for pat, cbs in re_handlers.items():
            if pat.search(text):
                for cb in cbs:
                    bot.schedule(cb, msg)


@irc(cmd='PING')
def pong(bot, msg):
    bot.send('PONG', msg.params[-1])


@irc(numeric='RPL_ENDOFMOTD')
def join_channels(bot, msg):
    for channel in bot.config.channels:
        bot.send('JOIN', channel)


@irc(numeric='ERR_NICKNAMEINUSE')
def nickname_in_use(bot, msg):
    bot.set_nick(bot.nick + '_')


@irc(numeric='RPL_NAMREPLY')
def on_namreply(bot, msg):
    users = msg.params[-1].split()
    channel = msg.params[2]
    bot.channels[channel] = set(users)


@irc(cmd='JOIN')
def on_join(bot, msg):
    bot.channels[msg.channel].add(msg.nick)


@irc(cmd='KICK')
def on_kick(bot, msg):
    kicked_user = msg.params[-1]
    bot.channels[msg.channel].discard(kicked_user)
    if msg.nick == bot.nick:
        del bot.channels[msg.channel]


@irc(cmd='QUIT')
@irc(cmd='PART')
def on_part(bot, msg):
    bot.channels[msg.channel].discard(msg.nick)
    if msg.nick == bot.nick:
        del bot.channels[msg.channel]


@irc(cmd='NICK')
def on_nickname_change(bot, msg):
    old_nick = msg.nick
    new_nick = msg.params[-1]

    if old_nick == bot.nick:
        bot.nick = new_nick
    for channel in bot.channels:
        if old_nick in bot.channels[channel]:
            bot.channels[channel].discard(old_nick)
            bot.channels[channel].add(new_nick)

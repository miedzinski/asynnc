from nnc.core.plugin import cmd


@cmd('ping')
async def pong(bot, msg):
    bot.reply(msg, '%s: pong' % msg.nick)

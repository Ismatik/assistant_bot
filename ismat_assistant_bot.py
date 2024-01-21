

import telebot

#Done! Congratulations on your new bot. You will find it at t.me/ismat_assistant_bot. You can now add a description, about section and profile picture for your bot, see /help for a list of commands. By the way, when you've finished creating your cool bot, ping our Bot Support if you want a better username for it. Just make sure the bot is fully operational before you do this.

# Use this token to access the HTTP API:
# 6839478389:AAHv_ctSCfGKw1mj86orekFLDBcroRX6KH4

bot = telebot.TeleBot("6839478389:AAHv_ctSCfGKw1mj86orekFLDBcroRX6KH4")

@bot.message_handler(commands=["start","hello","hi"])
def start(message):

    bot.reply_to(message , "Yo, it is Ismat's bot")

@bot.message_handler(commands=["greeting"])
def greeting(message):
    bot.reply_to(message, "Welcome to Ismat's assistant bot")

@bot.message_handler(commands = ["stop" , "bye"])
def stop(message):
    bot.reply_to(message , "See ya later")

@bot.message_handler(content_types=["text"])
def answer(message):
    text = message.text
    bot.reply_to(message , f"Wanna find this music {text}?")

# bot.message_handler()(start) #We are adding start to our bot

bot.polling(non_stop=True, interval=0) 
#This function creates a new Thread that calls an internal __retrieve_updates function. 
#This allows the bot to retrieve Updates automatically and notify listeners and message handlers accordingly.


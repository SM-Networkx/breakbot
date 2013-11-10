#!/usr/bin/python
# Copyright 2012 Bruno Gonzalez
#
# Changes to original fork of breakbot by Michael Sauer
#
# This software is released under the GNU AFFERO GENERAL PUBLIC LICENSE (see agpl-3.0.txt or www.gnu.org/licenses/agpl-3.0.html)

import threading
import time
from irc_bot import IRCInterface
from wa_bot import WAInterface
from log import info, error
from catch_them_all import catch_them_all
import traceback
import re

logging = 1
verbose = 0

def store_msg(message, file_path=None):
    if file_path is None:
        raise Exception("No file specified!")
    try:
	if logging == 1:
	    text = message.serialize() + "\n"
	    with open(file_path, "a") as log:
		log.write(text.encode("utf-8"))
    except:
        error("Couldn't write message to log")

def channels_from_contacts(contacts):
    channels = []
    for k,v in contacts.items():
        if v.startswith("#"):
            channels.append(v)
    return channels
    
class Bot(threading.Thread):
    def __init__(self, cfg, contacts):
        threading.Thread.__init__(self)
        self.must_run = True
        self.irc_server = cfg["irc_server_name"]
        self.irc_port = cfg["irc_server_port"]
        self.owner_nick = cfg["bot_owner_nick"]
        self.wa_phone = cfg["wa_phone"]
        self.log_file = cfg["log_file"]
        self.irc_nick = cfg["irc_nick"]
        self.wa_password = cfg["wa_password"]
        self.contacts = contacts
        self.spamcheck = cfg["spamcheck"]
        self.logging = cfg["logging"]
        self.spamcheck_nick = cfg["spamcheck_nick"]
	self.verbose = cfg["verbose"]
	fwd_filters = cfg["filter"]
	if fwd_filters != "":
	    info(2, "Filter messages: "+fwd_filters)
	    filters = fwd_filters.split(",")
	    self.filters = filters
	    info(2, "Found %s Filters" %len(filters))
	else:
	    self.filters = []

	if len(self.filters) == 0:
	    info(2, "Filtering disabled")
        self.irc_i = IRCInterface(self.irc_server, self.irc_port, self.irc_nick, self.owner_nick, channels_from_contacts(self.contacts), self.irc_msg_received, self.stop)
        self.irc_i.spamcheck_enabled = self.spamcheck
        self.wa_i = WAInterface(self.wa_phone, self.wa_password, self.wa_msg_received, self.stop)
    @catch_them_all
    def run(self):
        try:
            self.must_run = True
	    info(1, "Starting IRC")
            self.irc_i.start()
            info(1, "Waiting for IRC")
            self.irc_i.wait_connected()
            info(1, "Starting WA")
            self.wa_i.start()
            info(1, "Waiting for WA")
            self.wa_i.wait_connected()
	    info(1, "Program ready")
            info(3, "Main loop running")
        except:
            info(3, "Main loop closing")
            self.stop()
    def stop(self):
        info(2, "Stop instructed, about to stop main loop")
        self.must_run = False
        self.irc_i.stop()
        self.wa_i.stop()

    def get_group_from_chan(self, contacts, irc_channel):
        for k,v in contacts.items():
            if v.lower() == irc_channel.lower():
                return k
        raise Exception("Channel not found in contact list")

    @catch_them_all
    def irc_msg_received(self, message):
	store_msg(message, self.log_file)
        info(3, " <<< IRC %s" %message)
	if message.get_nick() == self.owner_nick and message.msg == "!die":
	    info(1, "Got die from Owner")
	    self.irc_i.cli.send("QUIT :Die from owner")
	    self.stop()
	elif message.msg == "!die":
	    info(1, "%s in %s tried to die me. Slap around him." %(message.get_nick(), message.chan))
	    self.irc_i.send_queue.put("PRIVMSG %s :\001ACTION slaps %s around with a large trout\001" %(message.chan, message.get_nick()))
        if self.spamcheck == 1:
            #if message.target is None:
                #raise Exception("Private message sent to no one?")
	    if message.get_nick() != self.spamcheck_nick and message.target != None:
		try:
		    wa_target = self.contacts[message.target] #try by phone
		except KeyError:
		    wa_target = self.get_group_from_chan(self.contacts, message.target) #try by nick
		wa_target += "@s.whatsapp.net"
		msg = "<%s> %s" %(message.get_nick(), message.msg.split(":", 1)[1])
		self.wa_i.send(wa_target, msg)
	    elif message.get_nick() == self.spamcheck_nick:
		if self.irc_i.server_spamcheck == False:
		    self.irc_i.server_spamcheck = True
		    info(3, "SpamScanner scan is done. Now joining channels.")
		    self.irc_i.join_channels()
	    else:
		msg = "<%s> %s" %(message.get_nick(), message.msg)
		if len(self.filters) > 0:
		    matches = 0
		    for f in self.filters:
			if re.search(f, message.msg, re.I):
			    matches = matches + 1
		    if matches > 0:
			info(2, "IRC Message matching filters. Forwarding Message.")
			try:
			    group = self.get_group_from_chan(self.contacts, message.chan)
			    self.wa_i.send(group, msg)
			except Exception, e:
			    error(traceback.print_exc())
			    error("Cannot send message to channel %s: %s" %(message.chan, e))
		else:
		    info(3, "IRC Message filtering disabled. Forwarding Message.")
		    try:
			group = self.get_group_from_chan(self.contacts, message.chan)
			self.wa_i.send(group, msg)
		    except Exception, e:
			error(traceback.print_exc())
			error("Cannot send message to channel %s: %s" %(message.chan, e))
	elif message.chan == self.irc_nick and self.spamcheck == 0:
            #if message.target is None:
                #raise Exception("Private message sent to no one?")
	    if message.target != None:
		try:
		    wa_target = self.contacts[message.target] #try by phone
		except KeyError:
		    wa_target = self.get_group_from_chan(self.contacts, message.target) #try by nick
		wa_target += "@s.whatsapp.net"
		msg = "<%s> %s" %(message.get_nick(), message.msg.split(":", 1)[1])
		self.wa_i.send(wa_target, msg)
    	    else:
        	msg = "<%s> %s" %(message.get_nick(), message.msg)
        	if len(self.filters) > 0:
		    matches = 0
		    for f in self.filters:
			if re.search(f, message.msg, re.I):
			    matches = matches + 1
		    if matches > 0:
			info(2, "IRC Message matching filters. Forwarding Message.")
			try:
			    group = self.get_group_from_chan(self.contacts, message.chan)
			    self.wa_i.send(group, msg)
			except Exception, e:
			    error(traceback.print_exc())
			    error("Cannot send message to channel %s: %s" %(message.chan, e))
		else:
		    info(3, "IRC Message filtering disabled. Forwarding Message.")
		    try:
			group = self.get_group_from_chan(self.contacts, message.chan)
			self.wa_i.send(group, msg)
		    except Exception, e:
			error(traceback.print_exc())
			error("Cannot send message to channel %s: %s" %(message.chan, e))

    @catch_them_all
    def wa_msg_received(self, message):
	store_msg(message, self.log_file)
        lines = message.msg.strip().split("\n") #split multiline messages
        info(3, " <<< WA %s" %message)
        if message.chan == self.wa_phone:
            #private message
            if message.target is None:
                # directed to bot itself
		try:
            	    nick = self.contacts[message.get_nick()]
		    irc_target = self.contacts[message.nick_full.split("@")[0]]
            	    for line in lines:
                	irc_msg = "<%s> %s" %(nick, line)
                	self.irc_i.send(self.owner_nick, irc_msg)
		except:
		    info(2, "Contact not recognized (%s)" %message.get_nick())
            else:
                # directed to someone
                try:
                    phone = message.get_nick()
                    nick = self.contacts[phone]
                    target = self.get_group_from_chan(self.contacts, message.target)
                    for line in lines:
                        msg = "<%s> %s" %(target, line)
                        self.irc_i.send(target, msg)
                except:
                    error("Couldn't relay directed WA msg to IRC")
        else:
            #group message
            for line in lines:
                try:
                    msg = "<%s> %s" %(self.contacts[message.get_nick()], line)
                except:
                    info(2, "Contact not recognized (%s)" %message.get_nick())
                    msg = "<%s> %s" %(message.get_nick(), line)
                try:
                    self.irc_i.send(self.contacts[message.chan], msg)
                except:
                    info(2, "Channel %s not recognized" %(message.chan))

import json
with open("config.json", "r") as f:
    config = json.loads(f.read())
contacts = config["contacts"]
cfg = config["config"]

info(4,"Contact list: %s" %contacts)
with open("config.json.bak", "w") as f:
    json.dump(config, f, indent=4)

info(1,"Program started")
logging = cfg["logging"]
if logging == 1:
    info(2,"Logging enabled")
verbose = cfg["verbose"]
info (2, "Verbosity Level %d" %verbose)

#b = Bot(cfg["wa_phone"], cfg["wa_password"], contacts, cfg["irc_server_name"], int(cfg["irc_server_port"]), cfg["bot_owner_nick"], cfg["log_file"], cfg["logging"], cfg["spamcheck"], cfg["spamcheck_nick"], cfg["verbose"])
b = Bot(cfg, contacts)
try:
    b.start()
    while b.must_run:
        time.sleep(0.5)
except KeyboardInterrupt:
    info(4,"User wants to stop")
finally:
    b.stop()
info(1,"Program finished")

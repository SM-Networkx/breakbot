Breakbot
========

Description
-----------

This project is a fork of the breakbot from stenyak

Breakbot is a software that serves as gateway between several communication protocols.

It currently supports:

 * WhatsApp group chats <-> IRC rooms gatewaying.
 * WhatsApp phone numbers <-> IRC nick conversion.
 * WhastApp image and video attachments.
 * Private messaging

Added by this fork:

 * euIRC Spam checker workaround
 * euIRC compliant mode settings and whois information
 * Filter specific IRC messages to forward by keywords
 * !die command for the owner


### Contributing

Contact info is at the bottom of this document.

### Disclaimer

Breakbot is in early stages, lacks documentation everywhere, needs refactoring, may set fire to your computer, take your jobs... the usual drill. Just don't blame me for any problem it causes.


### Configuration

Same configuration steps like the original fork [stenyak/breakbot](https://github.com/stenyak/breakbot)
just a modified configuration file with more options

## config.json

```json
{
    "contacts": {
        "4917699999999-111111111111@g.us": "#raspberry-pi",   <--- The Whatsapp Group chat that is binded to a IRC Channel
        "4917699999999": "botnick" <--- The Bot itself had to appear in the contact list too, you can add a lot more receipients
    },
    "config": {
        "wa_phone": "4917699999999",            <--- your whatsapp fone number with country code
        "wa_password": "TJfdghjdshglhfdhgjls=", <--- you precrypted whatsapp password string
        "irc_nick": "botnick",                  <--- the nick the bot has on IRC
        "irc_server_name": "irc.de.euirc.net",  <--- irc server it connects to
        "irc_server_port": "6667",              <--- irc server port it should use
        "bot_owner_nick": "owner",              <--- the owner nick of the bot
        "log_file": "log.txt",                  <--- logfile name
        "logging": 1,                           <--- logging to disk enable [0=no 1=yes]
        "verbose": 2,                           <--- verbosity level [0-4 higher so more messages (to find out the whatsapp group chat id you can use level 4)
        "spamcheck": 1,				<--- got the irc network a spamcheck [0=no 1=yes]
        "spamcheck_nick": "SpamScanner",        <--- the spamcheck nickname that checks [for none leave it as it is]
	"filter": "keyword1,keyword2,keword3"	<--- filter out the messages that get forwarded? then put in the keywords delimited by comma, else leave it blank
    }
}
```

Contact
------

You can notify me about problems and feature requests at the [issue tracker](https://github.com/ninharp/breakbot/issues)

Fork copyright by Michael Sauer [sauer.uetersen@gmail.com](mailto:sauer.uetersen@gmail.com)
The author of original Breakbot Bruno Gonzalez can be reached at [stenyak@stenyak.com](mailto:stenyak@stenyak.com) and `/dev/null` respectively.


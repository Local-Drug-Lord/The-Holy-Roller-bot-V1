# The Holy Roller

## What Is The Holy Roller?

The Holy Roller is a (to be) general purpose discord bot made and managed by me (Local_Drug_Lord). The bot had its first real release on the 17th of january 2024 with added support for more than one server at a time 6 months later with the help of a Postgresql database. This addition of the database is what I've come to call V1 of the bot as I had to more or less redo the whole thing from scratch.

As of recently I've come to the decision to make the code open source, do I recommend using my code? No, not at all. Why? Well where do I start?

1. It's really shitty code.
2. I'm not a professional programmer and shall not be trusted as one.
3. There is bugs, lots of bugs. (I'm working on some of them, if you find anything please make an [issue in the issues tab](https://github.com/Local-Drug-Lord/The-Holy-Roller-bot-V1/issues) and i shall take a look at it. Don't forget to use the template :) )
4. Coding is fun, make your own bot from scratch.
5. I don't trust myself when it comes to good code.

## Why Is The Holy Roller?

I had been thinking about making a discord bot for some time. I'm strongly against how some bot makers are putting major (and non major) features behind a paywalls so I decided to make my own. "How hard can it be!" I said back then, if you ask me now I'll just pull out a gun and shoot myself. I really hate programming if I'm honest, but I do find something quite fun in it. I also love seeing the results and looking at the bot thinking about all the hours I've put into it. There's a special feeling about it all.

## How Do I Use The Bot Myself? (Myself being you the user/server owner)

Well there's two ways of doing it:

- Add the bot to your server using this [link](https://discord.com/oauth2/authorize?client_id=1197233793640177726).
- Or copy paste my code. (Which is a pain in the ass and takes time to set up)

### Dependencies

- [Python 3.13 or older](https://www.python.org/downloads/)
- [Pip](https://pip.pypa.io/en/stable/installation/) (to install the rest)
- Postgres database set up properly (see Database.md)
- [A discord bot account](https://discord.com/developers)
- A apikeys.py file that is set up to specs (see apikeys-template.py)

Pip packs:

- [Discord.py](https://discordpy.readthedocs.io/en/stable/intro.html)
- [Asyncpg](https://pypi.org/project/asyncpg/) (Used to connect and send/remove/view SLQ/database data in Postgre)

### Starting the bot

Confirm that everything is set up and working as it should, then just run Main.py on an old laptop running ubuntu that you shove into a closet and then forget about (or just run it on a real server).
Do not forget to read through the whole README.md, TOS-and-EUA.md and Database.md. Negligence could lead to problems like:

- Errors (Critical and non critical)
- Forgotten settings/dependencies
- A bloody awful time

## Help

If you need any help or find a bug you're free to join the [discord server](https://discord.gg/bXxFh72JNb) and ask for help or [make a bug report](https://github.com/Local-Drug-Lord/The-Holy-Roller-bot-V1/issues) the github repository.

## Authors

### Contributors

- Me
- Me again
- My alt accounts
- A random dude on the train who told me i could do it
- Redbull

## Versioning standard

Ever wondered what V4.5.15 actually means?
Well you're not alone, most companies use a system called "Semantic versioning" (SemVer).
Here's a helpful table:

| Major | Minor | Patch |
|:-----:|:-----:|:-----:|
|4      |5      |15     |

In this example this program would be in it's 4th major release, 5th minor release and 15th path release.
Major releases would be something like a big new feature set.
Minor releases would be something like small changes/updates, often as a response to criticism.
Path release would be fixes to bugs, vulnerability or just something that needs a small touch of paint to be better.

## TOS and EUA

Read TOS-and-EUA.md

## Acknowledgments

Inspiration, code snippets, documentation, etc:

- [Discord.py documentation](https://discordpy.readthedocs.io/en/stable/index.html)
- [Discord.py discord server](https://discord.com/invite/r3sSKJJ)
- [README.md template](https://gist.github.com/DomPizzie/7a5ff55ffa9081f2de27c315f5018afc)
- [Asyncpg documentation](https://magicstack.github.io/asyncpg/current/)
- [My spotify playlist](https://open.spotify.com/playlist/4ucmV3XcBeyBmecSm0WXCT?si=ec23a89b06944007)

## End notes

Please share this bot and github repository with your friends.
Thank you for using my bot/application : )

# Building the project
To build the project, just make from the root project directory.

Note that every time you change a Python file, you
must make for all of the project's imports to update properly.

Within the showdownai.spec file, you may need to update the path for the "pathex" 
argument to the Analysis constructor (currently set to /Users/siddharth/School/CS/159/pokemon_ai) 
so that it points to your root project directory, and the path for
selenium_tree (currently set to point to the location where
Selenium is installed on my computer).

# Running the bot
Run "python server/showdownbot.py" from the root project directory
(note that the bot doesn't work when run from other folders)

A GUI will pop up; populate the fields with the username and
password for our bot, and click play to launch the bot.

See https://www.reddit.com/r/stunfisk/comments/3i4hww/pokemon_showdown_ai/
for more info.

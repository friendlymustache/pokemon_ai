# Building/setting up the project

From the root project directory, untar the SL policy 
(one of the models used in running the bot) via the command:

tar -xzvf models/sl/sl.bst.tgz


# Running the bot

## Using a GUI
Run "python server/showdownbot.py" from the root project directory
(note that the bot doesn't work when run from other folders)

A GUI will pop up; populate the fields with the username and
password for our bot, and click play to launch the bot.

See https://www.reddit.com/r/stunfisk/comments/3i4hww/pokemon_showdown_ai/
for more info.

## Using the command-line

From the root project directory, run:

python showdownai/showdown.py --username your_username --password your_password --browser chrome teams/chris_volt.txt

where your_username and your_password are the username and password of a
valid Pokemon Showdown account.

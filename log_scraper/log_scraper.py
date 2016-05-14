'''
Scrapes replay logs of games and saves them to a database.
'''

from bs4 import BeautifulSoup
import requests
from argparse import ArgumentParser
from database import ReplayDatabase
from path import Path

import sys
sys.path.append('../showdownai')
from browser import Selenium
import time
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.alert import Alert
import re

LADDER_URL = "http://pokemonshowdown.com/ladder/ou"
USERNAME_URL = "http://replay.pokemonshowdown.com/search/?output=html&user={user}&format=&page={page}&output=html"
REPLAY_URL= "http://replay.pokemonshowdown.com/{replay_id}"
MAX_GAME_LENGTH = 500


class SeleniumScraper(Selenium):
    def get_replay_text(self, replay_id, background=True):
        # Navigate to the page of the desired replay
        self.driver.get(REPLAY_URL.format(replay_id=replay_id))

        # Start the desired replay
        start_replay_btn = self.driver.find_element_by_css_selector("[data-action='startMuted']")
        start_replay_btn.click()

        # Extract replay text. Run in background, i.e. without triggering any
        # alerts, if background=True. Otherwise, runs in the foreground,
        # triggering alerts (this is the faster method)
        return self.get_replay_helper(replay_id, background)


    def get_replay_helper(self, replay_id, background):
        if background:
            fast_forward_btn = self.driver.find_element_by_css_selector("[data-action='ff']")                
            # Iterate through up to MAX_GAME_LENGTH turns
            for i in range(MAX_GAME_LENGTH):
                fast_forward_btn.click()
                # Once we've skipped through at least 100 turns, check if the
                # battle has ended every 20 turns
                if i > 100 & i % 20 == 0:
                    log = self.driver.find_element_by_css_selector(".battle-log")
                    if "won the battle" in log.text:
                        return log.text 
            # If the game hasn't ended after MAX_GAME_LENGTH turns, throw an exception
            raise Exception("Failed to reach end of log file")                
        else:
            # Open the turn picking dialogue
            pick_turn_btn = self.driver.find_element_by_css_selector("[data-action='ffto']")
            pick_turn_btn.click()

            # Pick the last turn
            alert = Alert(self.driver)
            alert.send_keys(str(-1))
            alert.accept()      

            log = self.driver.find_element_by_css_selector(".battle-log")
            return log.text




def parse_args():
    argparser = ArgumentParser()
    argparser.add_argument('--db_path', default='../data/db')
    argparser.add_argument('--start_index', default=0, type=int)
    argparser.add_argument('--end_index', default=499, type=int)
    argparser.add_argument('--max_page', default=100, type=int)
    argparser.add_argument('--max_logs_to_scrape', default=15000, type=int)
    argparser.add_argument('--no-background', dest='background', action='store_false')    

    return argparser.parse_args()

def get_usernames():
    text = requests.get(LADDER_URL).text
    soup = BeautifulSoup(text)
    return [t.text.encode('utf-8') for t in soup.find_all('a', {'class': 'subtle'})]

def page_done(database, replay_ids):
    first, last = replay_ids[0], replay_ids[-1]
    return database.check_replay_exists(first) and database.check_replay_exists(last)


def get_replay_ids(username, page, tier='ou'):
    final_links = []
    url = USERNAME_URL.format(
        user=username,
        page=page
    )
    html = requests.get(url).text
    soup = BeautifulSoup(html)
    links = soup.find_all('a')
    for link in links:
        if tier in link.get("href"):
            final_links.append(link.get("href").encode("utf-8")[1:])
    return final_links

def get_logs(replay_id):
    html = requests.get(REPLAY_URL.format(
        replay_id=replay_id)
    ).text
    soup = BeautifulSoup(html)
    script = soup.find_all('script', {'class': 'log'})[0]
    log = script.text
    return log

if __name__ == "__main__":
    args = parse_args()
    # Get a hard-coded list of users whose replays we want to scrape
    usernames = get_usernames()
    print "Running log scraper."
    print "NOTE: Argument --no-background can be used to speed up scraper."

    # Connect to the database
    r = ReplayDatabase(args.db_path)
    run_in_background = args.background
    print "Scraper running in background: %s"%run_in_background
    print "Adding to dataset of %s scraped logs"%(r.get_replay_count())

    # Scrape the replays
    scraper = SeleniumScraper(lib_dir=Path("../lib"), browser="chrome")
    nreplays = 0
    for user in usernames[args.start_index:args.end_index]:
        if nreplays > args.max_logs_to_scrape:
            break
        print "User: %s" % user
        for i in range(1, args.max_page + 1):
            print "Page: %d" % i
            replay_ids = get_replay_ids(user, i)
            if not replay_ids:
                break
            if page_done(r, replay_ids):
                continue
            for replay_id in replay_ids:
                if not r.check_replay_exists(replay_id):                
                    # print "New replay ID: %s" % replay_id
                    try:
                        replay_text = scraper.get_replay_text(replay_id, run_in_background)
                        r.add_replay(replay_id, replay_text, user)
                        nreplays += 1
                        print "Scraped %s replays"%nreplays
                        r.commit()
                    except Exception as e:
                        print "Exception: %s"%e.message
                        continue
                else:
                    print "Already scraped replay %s"%replay_id

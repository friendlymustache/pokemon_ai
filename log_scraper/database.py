import sqlite3
from argparse import ArgumentParser
from operator import itemgetter



def parse_args():
    argparser = ArgumentParser()
    argparser.add_argument('db_path')

    return argparser.parse_args()

class ReplayDatabase(object):

    def __init__(self, db_path="../data/db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        print "Connected to database at %s"%db_path
        try:
            c = self.conn.cursor()
            c.execute("CREATE TABLE replay (_id INTEGER PRIMARY KEY AUTOINCREMENT, " + 
                "replay_id TEXT NOT NULL UNIQUE, battle_log TEXT NOT NULL," + 
                "username VARCHAR(100))")
            print "Created database for replays"
        except:
            pass

    def get_replay_count(self):
        c = self.conn.cursor()
        counts = c.execute("SELECT COUNT(*) FROM replay").fetchone()
        return counts

    def get_replay_ids(self):
        '''
        Returns a list of all replay ids in the database
        '''
        c = self.conn.cursor()
        return map(itemgetter(0), c.execute("SELECT _id FROM replay").fetchall())        

    def get_replay_battle_log(self, replay_id):
        '''
        Return a string representing an HTML block describing an entire pokemon
        battle
        '''
        c = self.conn.cursor()
        replay = c.execute("SELECT battle_log FROM replay WHERE replay_id=?", [replay_id]).fetchone()
        return replay[0]


    def get_replay_attributes(self, *columns):
        '''
        Get a list of the values of the passed-in columns for each replay in
        the database
        '''
        columns = map(str, list(columns))
        c = self.conn.cursor()

        # Build up a query string that selects the desired columns
        query_string = "SELECT %s FROM replay"%(",".join(columns))
        # Execute the query and return the results
        return c.execute(query_string).fetchall()

    def check_replay_exists(self, replay_id):
        c = self.conn.cursor()
        replay = c.execute("SELECT EXISTS(SELECT 1 FROM replay WHERE replay_id=? LIMIT 1)", [replay_id]).fetchone()
        return bool(replay[0])


    def add_replay(self, replay_id, battle_log, username):
        c = self.conn.cursor()
        c.execute("INSERT INTO replay (replay_id, battle_log, username) VALUES (?, ?, ?)", [replay_id, battle_log, username])

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()

if __name__ == "__main__":

    args = parse_args()
    r = ReplayDatabase(args.db_path)
    print r.get_replay_attributes("replay_id", "username")[:10]

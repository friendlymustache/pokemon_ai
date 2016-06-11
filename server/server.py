from flask import Flask, jsonify, send_from_directory, render_template
from webargs import fields
from webargs.flaskparser import use_args
from showdownai import Showdown
from showdownai import PessimisticMinimaxAgent
from showdownai import MonteCarloAgent
from showdownai import load_data
from argparse import ArgumentParser
from path import Path
from threading import Thread, Timer
import webbrowser

class Server():

    def __init__(self, teamdir, datadir):
        self.teamdir = Path(teamdir)
        self.datadir = datadir
        self.pokedata = load_data(datadir)
        self.ids = {}
        self.counter = 0
        self.app = app = Flask(__name__, static_url_path='',
                               static_folder='static',
                               template_folder='templates')

        @app.route("/")
        def index():
            files = self.get_team_files()
            return render_template('index.html', teamfiles=files)

        @app.route("/bots")
        def bots():
            return render_template('bots.html')

        @app.route("/api/showdown/<int:id>", methods=['get'])
        def get_showdown(id):
            showdownobj = self.ids[id]
            url = showdownobj.battle_url
            showdownargs = {
                'id': id,
                'url': url
            }
            return jsonify(**showdownargs)

        @app.route("/api/play_game", methods=['get', 'post'])
        @use_args({
            'iterations': fields.Int(default=1),
            'username': fields.Str(required=True),
            'password': fields.Str(required=True),
            'teamfile': fields.Str(required=True),
            'teamtext': fields.Str(required=True),
            'challenge': fields.Str(missing=None),
            'browser': fields.Str(default="phantomjs"),
        })
        def play_game(args):
            username = args.get('username', None)
            password = args.get('password', None)
            browser = args.get('browser', None)            

            print "Playing game as user %s"%username
            print "Password: %s"%password
            print "Browser: %s"%browser

            if args['teamtext'] != "":
                team_text = args['teamtext']
            else:
                team_text = (self.teamdir / args['teamfile']).text()

            # constructor_param = PessimisticMinimaxAgent(4, self.pokedata)
            constructor_param = MonteCarloAgent(10, self.pokedata)

            print "about to initialize showdown object"
            showdown = Showdown(
                team_text,
                constructor_param,
                username,
                self.pokedata,
                browser=browser,
                password=password,
            )
            id = self.run_showdown(showdown, args)
            response = {'id': id}
            return jsonify(**response)

    def start_server(self):
        port = 5000
        url = "http://127.0.0.1:{0}".format(port)
        host = '0.0.0.0'
        Timer(1.25, lambda: webbrowser.open(url)).start()
        self.app.run(debug=True, host=host, port=port, use_reloader=False)

    def add_id(self, showdown):
        self.counter += 1
        self.ids[self.counter] = showdown
        return self.counter

    def run_showdown(self, showdown, args):
        print args
        Thread(target=showdown.run, args=(args['iterations'],),
                kwargs={
                    'challenge': args['challenge']
                }).start()
        return self.add_id(showdown)

    def get_team_files(self):
    	if not self.teamdir.exists():
	    self.teamdir.mkdir()
        files = self.teamdir.files()
        files = [file.name for file in files]
        return files

def main():
    argparse = ArgumentParser()
    argparse.add_argument("--teamdir", default='teams')
    argparse.add_argument("--datadir", default='data')
    arguments = argparse.parse_args()
    teamdir = arguments.teamdir
    datadir = arguments.datadir
    server = Server(
        teamdir,
        datadir,
    )
    server.start_server()

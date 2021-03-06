from __future__ import print_function
import os
import re
import sys
import ujson
import flask
import random
import shutil
import flask_classful
import flaskext.markdown as flask_markdown
from Game import GameRunner
from Game import GameLanguage
from Database import GameDB


def static_file(filename):
    resource_path = os.path.join(os.path.split(__file__)[0], "static", filename)
    return resource_path


def get_public_ip():
    # This is taken from: http://stackoverflow.com/a/1267524
    import socket
    return [l for l in ([ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")][:1], [[(s.connect(('8.8.8.8', 53)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]]) if l][0][0]


def find_name_from_code(code):
    import re
    name = re.findall(r"#\s*name:\s*(.*)\s*", code, re.IGNORECASE)
    if len(name):
        return name[0]
    else:
        return ""


class GameServer(flask_classful.FlaskView):
    game = None
    host = None
    port = None
    compression = None
    language = None
    avg_game_count = None
    charset = None
    gamedb = None
    route_base = '/'

    @classmethod
    def __load_language(cls):
        if cls.language == GameLanguage.LITTLEPY:
            from littlepython import Compiler
            cls.compiler = Compiler()
        else:
            raise Exception("Invalid language. Could not load hookers.")

    @classmethod
    def __verify_game(cls):
        # TODO: add asserts for every attr used later.
        assert hasattr(cls.game, "GAME_TITLE")
        score_op = getattr(cls.game, "get_score", None)
        assert callable(score_op)

    @classmethod
    def __copy_in_charset(cls, charset):
        if not os.path.exists(static_file("fonts")):
            os.mkdir(static_file("fonts"))
        file_ending = os.path.split(charset)[-1]
        prepostfix = "_col"
        if "_ro." in file_ending:
            prepostfix = "_ro"
        elif "_tc." in file_ending:
            prepostfix = "_tc"
        postfix = file_ending.split(".")[-1]
        def new_token():
            return "".join([random.choice("0123456789ABCDEF") for _ in range(10)]) + prepostfix + "." + postfix
        token = new_token()
        while os.path.exists(static_file(os.path.join("fonts", token))):
            token = new_token()
        new_charset_path = static_file(os.path.join("fonts", token))
        shutil.copyfile(charset, new_charset_path)
        return os.path.split(new_charset_path)[-1]

    @flask_classful.route('/scoreboard', methods=["POST"])
    def scoreboard(self):
        token = flask.request.get_json(silent=True).get('token', '')
        if not self.gamedb.is_user_token(token):
            return flask.jsonify(error="Invalid Token")
        school_tk = self.gamedb.get_school_for_token(token)
        obj = {"school": self.gamedb.get_name(school_tk), "scores": []}
        for user_tk in self.gamedb.get_tokens_for_school(school_tk):
            score = self.gamedb.get_avg_score(user_tk)
            if score is not None:
                obj["scores"] += [{"name": self.gamedb.get_name(user_tk), "score": self.gamedb.get_avg_score(user_tk)}]
        return ujson.dumps(obj)

    @flask_classful.route('/comp_scoreboards', methods=["POST"])
    def comp_scoreboards(self):
        token = flask.request.get_json(silent=True).get('token', '')
        if not self.gamedb.is_user_token(token):
            return flask.jsonify(error="Invalid Token")
        comps = self.gamedb.get_comps_for_token(token)
        obj = {"comps": []}
        for comp in comps:
            comp_obj = {"scores": []}
            for school in self.gamedb.get_schools_in_comp(comp):
                score = self.gamedb.get_comp_avg_score(comp, school)
                if score is not None:
                    comp_obj["scores"] += [{"name": self.gamedb.get_name(school), "score": score}]
            obj["comps"] += [comp_obj]
        return ujson.dumps(obj)

    @flask_classful.route('/sim_avg', methods=['POST'])
    def sim_avg(self):
        # TODO: create this to run the game 100 times returning the average score to the user.
        code = flask.request.get_json(silent=True).get('code', '')
        token = flask.request.get_json(silent=True).get('token', '')
        if not self.gamedb.is_user_token(token):
            return flask.jsonify(error="Invalid Token")
        try:
            prog = self.compiler.compile(code.split("\n"))
        except:
            return flask.jsonify(error="Code did not compile")
        runner = GameRunner(self.game, prog)
        try:
            score = runner.run_for_avg_score(times=self.avg_game_count)
            self.gamedb.save_avg_score(token, score)
            self.gamedb.save_code(token, code)
            name = find_name_from_code(code)
            if name:
                self.gamedb.save_name(token, name)
            return flask.jsonify(score=score)
        except Exception as e:
            print(e)
            return flask.jsonify(error="Your bot ran into an error at runtime.\n"
                                       "If you think that your bot is correct, please file a bug report!\n"
                                       "Make sure to include your code.")
        # return result

    @flask_classful.route('/sim', methods=['POST'])
    def sim(self):
        code = flask.request.get_json(silent=True).get('code', '')
        seed_str = flask.request.get_json(silent=True).get('seed', '')
        seed = random.randint(0, sys.maxint)
        if seed_str:
            try:
                seed = int(seed_str, 36)
            except:
                return flask.jsonify(error="Invalid Seed")
        try:
            prog = self.compiler.compile(code.split("\n"))
        except:
            return flask.jsonify(error="Code did not compile")
        runner = GameRunner(self.game, prog)
        try:
            result = ujson.dumps(runner.run_for_playback(seed=seed))
        except Exception as e:
            print(e)
            return flask.jsonify(error="Your bot ran into an error at runtime.\n"
                                       "If you think that your bot is correct, please file a bug report!\n"
                                       "Make sure to include your code.")
        return result

    @flask_classful.route('/check_token', methods=['POST'])
    def check_token(self):
        token = flask.request.get_json(silent=True).get('token', '')
        if not self.gamedb.is_user_token(token):
            return flask.jsonify(error="Invalid Token")
        else:
            return flask.jsonify(result=True)

    @flask_classful.route('/load_code', methods=['POST'])
    def load_code(self):
        token = flask.request.get_json(silent=True).get('token', '')
        if not self.gamedb.is_user_token(token):
            return flask.jsonify(error="Invalid Token")
        else:
            return flask.jsonify(code=self.gamedb.get_code(token))

    def index(self):
        intro = self.game.get_intro() + GameLanguage.get_language_description(self.language)
        return flask.render_template('index.html', game_title=self.game.GAME_TITLE,
                                example_bot=self.game.default_prog_for_bot(self.language), char_width=self.game.CHAR_WIDTH,
                                char_height=self.game.CHAR_HEIGHT, screen_width=self.game.SCREEN_WIDTH,
                                screen_height=self.game.SCREEN_HEIGHT, char_set=self.charset,
                                intro_text=intro)

    @classmethod
    def serve(cls, game, host=None, port=None, compression=False, language=GameLanguage.LITTLEPY,
              avg_game_count=10, game_data_path="temp_game"):
        cls.game = game
        cls.host = host
        cls.port = port
        cls.compression = compression
        cls.language = language
        cls.avg_game_count = avg_game_count
        cls.gamedb = GameDB(game_data_path)
        cls.charset = cls.__copy_in_charset(game.CHAR_SET)

        cls.app = flask.Flask(__name__.split('.')[0])

        @cls.app.template_filter('markdown')
        def markdown_filter(data):
            from flask import Markup
            from markdown import markdown

            return Markup(markdown(data))

        if cls.compression:
            import flask_compress
            flask_compress.Compress(cls.app)
        cls.register(cls.app)
        cls.__load_language()
        if cls.host and cls.port:
            cls.app.run(cls.host, cls.port)
        elif cls.port:
            cls.app.run(port=cls.port)
        elif cls.host:
            cls.app.run(cls.host)
        else:
            cls.app.run()
        print("Dying...")
        if os.path.exists(static_file(os.path.join("fonts", cls.charset))):
            print("Removing charset...")
            os.remove(static_file(os.path.join("fonts", cls.charset)))
        print("All good :)")


# This is for backwards compatibility
serve = GameServer.serve

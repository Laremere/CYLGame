import tcod
import tdl
import tempfile
import os.path
import random
import string
import sys

TCOT_ROOT_CONSOLE = None
TDL_ROOT_CONSOLE = None


# From: http://stackoverflow.com/a/2267446/4441526
digs = string.digits + string.letters
def int2base(x, base):
    if x < 0:
        sign = -1
    elif x == 0:
        return digs[0]
    else:
        sign = 1

    x *= sign
    digits = []

    while x:
        digits.append(digs[x % base])
        x /= base

    if sign < 0:
        digits.append('-')

    digits.reverse()

    return ''.join(digits)


def data_file(filename):
    resource_path = os.path.join(os.path.split(__file__)[0], os.path.pardir, "data", filename)
    return resource_path


class GameLanguage(object):
    LITTLEPY = 0

    @staticmethod
    def get_language_description(language):
        if language == GameLanguage.LITTLEPY:
            return open(data_file("little_python_intro.md")).read()


class Game(object):
    SCREEN_WIDTH = 80
    SCREEN_HEIGHT = 25
    CHAR_WIDTH = 8
    CHAR_HEIGHT = 8
    GAME_TITLE = ""
    CHAR_SET = data_file("fonts/terminal8x8_gs_ro.png")

    def is_running(self):
        """This is how the game runner knows if the game is over.

        Returns:
            bool: True if the game should still be play. False otherwise
        """
        raise Exception("Not implemented!")

    def handle_key(self, key):
        """This is where your game should react to user input.
        We have decided on some standards for input. The following are the standard chars and their meaning:
            Q:  Quit, you should do whatever you need to before the game ends. Probably set a flag so the draw_screen
                function can draw an end of game screen.
            w:  North or Up
            a:  West or Left
            d:  East or Right
            s:  South or Down
            q:  Northwest
            e:  Northeast
            z:  Southwest
            c:  Southeast

        Args:
            key (str): key is a string of length one repenting a key press.
        """
        raise Exception("Not implemented!")

    def draw_screen(self, libtcod, console):
        raise Exception("Not implemented!")

    def get_vars_for_bot(self):
        raise Exception("Not implemented!")

    def get_score(self):
        """This is the game runner gets the ending or mid-game score

        Returns:
            int: The current score.
        """
        raise Exception("Not implemented!")

    @staticmethod
    def default_prog_for_bot(language):
        raise Exception("Not implemented!")

    @staticmethod
    def get_intro():
        raise Exception("Not implemented!")

    @staticmethod
    def get_move_consts():
        return {"north": ord("w"), "south": ord("s"), "west": ord("a"), "east": ord("d"),
                "northeast": ord("e"), "southeast": ord("c"), "northwest": ord("q"), "southwest": ord("z")}

    @staticmethod
    def get_move_names():
        return {ord("w"): "North", ord("s"): "South", ord("a"): "West", ord("d"): "East",
                ord("e"): "Northeast", ord("c"): "Southeast", ord("q"): "Northwest",
                ord("z"): "Southwest"}


class GameRunner(object):
    def __init__(self, game_class, bot=None):
        self.game_class = game_class  # type: type
        self.bot = bot  # type: LPProg

        self.BOT_CONSTS = self.game_class.get_move_consts()
        self.CONST_NAMES = self.game_class.get_move_names()

    def __run_for(self, score=False, playback=False, seed=None):
        global TDL_ROOT_CONSOLE
        assert self.bot is not None  # Make sure that we have a bot to run
        assert score != playback

        if not TDL_ROOT_CONSOLE:
            TDL_ROOT_CONSOLE = tdl.init(0, 0)
        if not seed:
            seed = random.randint(0, sys.maxint)
        game = self.game_class(random.Random(seed))


        console = tdl.Console(game.SCREEN_WIDTH, game.SCREEN_HEIGHT)
        if playback:
            screen_cap = []
            debug_vars = []
        vars = {}
        while game.is_running():
            result = self.__run_bot_turn(console, game, vars, capture_screen=playback)
            if result:
                vars, screen = result
                if playback:
                    screen_cap += [screen]
                    human_vars = {}
                    for v in vars:
                        if vars[v] in self.CONST_NAMES:
                            human_vars[v] = self.CONST_NAMES[vars[v]] + " ("+str(vars[v])+")"
                        else:
                            human_vars[v] = vars[v]
                    debug_vars += [human_vars]
            else:
                break

        if playback:
            return {"screen": screen_cap, "seed": int2base(seed, 36), "debug": debug_vars}
        else:  # if score
            return game.get_score()

    def run_for_avg_score(self, times=1):
        """Runs the given game keeping only the scores.

        Args:
            times (int): The number of times to run to get the average score.

        Return:
            The return value the average score for the times runs.
        """
        scores = []
        # TODO: make this able to run in a pool of threads (So it can be run on multiple CPUs)
        for t in range(times):
            scores += [self.__run_for(score=True)]
        return float(sum(scores*100) / times)/100

    def run_for_playback(self, seed=None):
        """Runs the given game saving the screen captures.

        Return:
            The return value is a 3-dimensional list the first dimension is time followed by y and x.
        """
        return self.__run_for(playback=True, seed=seed)

    def run(self, seed=None):
        """Will run the game for a user.

        Returns:
        """
        global TDL_ROOT_CONSOLE
        if not TDL_ROOT_CONSOLE:
            tdl.setFont(self.game_class.CHAR_SET)
            TDL_ROOT_CONSOLE = tdl.init(self.game_class.SCREEN_WIDTH, self.game_class.SCREEN_HEIGHT,
                                        self.game_class.GAME_TITLE)
        else:
            raise Exception("You are trying the run two games at the time! I cann't do that :(")

        game = self.game_class(random.Random(seed))
        console = tdl.Console(game.SCREEN_WIDTH, game.SCREEN_HEIGHT)
        while game.is_running():
            self.__run_user_turn(console, game)

    @staticmethod
    def get_screen_array(console):
        tf = tempfile.NamedTemporaryFile(mode="rb")
        tcod.console_save_asc(console.tcod_console, tf.name)
        lines = tf.readlines()
        y, x = map(int, lines[1].split())
        chars = lines[2][1::9]
        arr = []
        for i in range(y):
            arr += [map(ord, chars[i::x])]
        return arr

    @staticmethod
    def __run_user_turn(console, game):
        game.draw_screen(tcod, console.tcod_console)
        TDL_ROOT_CONSOLE.blit(console, 0, 0, game.SCREEN_WIDTH, game.SCREEN_HEIGHT, 0, 0)
        tdl.flush()

        key = tdl.event.key_wait()
        if key.char:
            game.handle_key(key.char)

    def __run_bot_turn(self, console, game, prev_vars={}, capture_screen=True):
        """run_bot will do a single bot turn"""
        game.draw_screen(tcod, console.tcod_console)
        if capture_screen:
            screen_cap = self.get_screen_array(console)
        else:
            screen_cap = None

        vars = dict(prev_vars)
        vars.update(self.BOT_CONSTS)
        vars.update(game.get_vars_for_bot())
        nxt_vars = self.bot.run(vars)

        # remove consts
        for key in self.BOT_CONSTS:
            nxt_vars.pop(key)

        if "move" in nxt_vars:
            game.handle_key(chr(nxt_vars["move"]))
        else:
            return False
        return nxt_vars, screen_cap


def run(game_class):
    def serve(args):
        print("I am going to serve")
        from .Server import serve
        serve(game_class, host=args.host, port=args.port, game_data_path=args.dbfile)

    def play(args):
        print("Playing...")
        GameRunner(game_class).run(int(args.seed, 36))

    import argparse

    parser = argparse.ArgumentParser(prog=game_class.GAME_TITLE, description='Play ' + game_class.GAME_TITLE + '.')
    subparsers = parser.add_subparsers(help='What do you what to do?')
    parser_play = subparsers.add_parser('play', help='Play ' + game_class.GAME_TITLE + ' with a GUI')
    parser_play.add_argument('-s', '--seed', nargs="?", type=str, help='Manually set the random seed.',
                             default=int2base(random.randint(0, sys.maxint), 36))
    parser_play.set_defaults(func=play)
    parser_serve = subparsers.add_parser('serve', help='Serve ' + game_class.GAME_TITLE + ' to the web.')
    parser_serve.add_argument('-p', '--port', nargs="?", type=int, help='Port to serve on', default=5000)
    parser_serve.add_argument('-db', '--dbfile', nargs="?", type=str, help='The root path of the game database', default="temp_game")
    parser_serve.add_argument('--host', nargs="?", type=str, help='The mask to host to', default='127.0.0.1')
    parser_serve.set_defaults(func=serve)

    args = parser.parse_args()
    args.func(args)

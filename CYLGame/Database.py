import io
import os
import ujson
import random


# TODO(derpferd): Use the move function to prevent RACE on files
class GameDB(object):
    TOKEN_LEN = 8

    def __init__(self, game_dir):
        self.game_dir = game_dir
        self.data_dir = os.path.join(self.game_dir, "data")
        self.schools_dir = os.path.join(self.game_dir, "schools")
        self.competitions_dir = os.path.join(self.game_dir, "competitions")
        self.__load()

    def __load(self):
        # is_new = False
        if not os.path.exists(self.game_dir):
            # is_new = True
            os.mkdir(self.game_dir)
        if not os.path.exists(self.data_dir):
            # is_new = True
            os.mkdir(self.data_dir)
        if not os.path.exists(self.schools_dir):
            # is_new = True
            os.mkdir(self.schools_dir)
        if not os.path.exists(self.competitions_dir):
            os.mkdir(self.competitions_dir)

        # if is_new:
        #
        #     # self.schools = {}
        #     # self.tokens = {}
        #     # self.__save()
        # else:
        #     obj = ujson.load(open(self.meta_fn, "r"))
        #     assert "schools" in obj
        #     assert "tokens" in obj
        #     self.schools = obj["schools"]
        #     self.tokens = obj["tokens"]

    # def __save(self):
    #     ujson.dump({"schools": self.schools, "tokens": self.tokens}, open(self.meta_fn, "w"))

    def __get_user_tokens(self):
        return os.listdir(self.data_dir)

    def __get_school_tokens(self):
        return os.listdir(self.schools_dir)

    def __get_comp_tokens(self):
        return os.listdir(self.competitions_dir)

    def __get_school_user_tokens(self, school_tk):
        if self.is_school_token(school_tk):
            return os.listdir(self.__get_dir_for_token(school_tk, "tokens"))
        return []

    def __get_new_token(self, tokens=None, prefix=""):

        def new_token():
            return prefix + "".join([random.choice("0123456789ABCDEF") for _ in range(self.TOKEN_LEN)])
        if not tokens:
            tokens = self.__get_user_tokens()
        token = new_token()
        while token in tokens:
            token = new_token()
        return token

    def __get_dir_for_token(self, token, fns=[]):
        """Get the file path for a given token and optionally an additional path after the token dir.

        Args:
            token (str): The user's token.
            fns (str or list): The file or files to add after the token directory.
        """
        if isinstance(fns, str):
            fns = [fns]
        else:
            assert isinstance(fns, list)
        if self.is_user_token(token):
            return os.path.join(self.data_dir, token, *fns)
        elif self.is_school_token(token):
            return os.path.join(self.schools_dir, token, *fns)
        elif self.is_comp_token(token):
            return os.path.join(self.competitions_dir, token, *fns)
        return None

    def __get_cur_code_for_token(self, token):
        pass

    def __get_next_code_for_token(self, token):
        pass

    def is_comp_token(self, token):
        if len(token) > 0 and token[0] == "P":
            # It is a competition token
            return token in self.__get_comp_tokens()
        return False

    def is_school_token(self, token):
        if len(token) > 0 and token[0] == "S":
            # It is a school token
            return token in self.__get_school_tokens()
        return False

    def is_user_token(self, token):
        return token in self.__get_user_tokens()

    def get_new_token(self, school_tk):
        # Is name needed?
        assert self.is_school_token(school_tk)
        token = self.__get_new_token()

        # Touch the file
        with open(self.__get_dir_for_token(school_tk, ["tokens", token]), "w") as fp:
            pass

        # Create token dir
        os.mkdir(os.path.join(self.data_dir, token))
        return token

    def add_new_school(self, name=""):
        token = self.__get_new_token(self.__get_school_tokens(), prefix="S")

        os.mkdir(os.path.join(self.schools_dir, token))
        os.mkdir(os.path.join(self.schools_dir, token, "tokens"))

        with io.open(os.path.join(self.schools_dir, token, "name"), "w", encoding="utf8") as fp:
            fp.write(unicode(name))

        return token

    def add_new_competition(self, name=""):
        token = self.__get_new_token(self.__get_comp_tokens(), prefix="P")

        os.mkdir(os.path.join(self.competitions_dir, token))
        os.mkdir(os.path.join(self.competitions_dir, token, "schools"))

        with io.open(os.path.join(self.competitions_dir, token, "name"), "w", encoding="utf8") as fp:
            fp.write(unicode(name))

        return token

    def add_school_to_comp(self, ctoken, stoken):
        assert self.is_comp_token(ctoken)
        assert self.is_school_token(stoken)

        school_dir = self.__get_dir_for_token(ctoken, ["schools", stoken])
        if not os.path.exists(school_dir):
            os.mkdir(school_dir)

    # TODO(derpferd): add function to remove a school

    def set_comp_school_code(self, ctoken, stoken, code):
        assert self.is_comp_token(ctoken)
        assert self.is_school_token(stoken)

        school_dir = self.__get_dir_for_token(ctoken, ["schools", stoken])
        if not os.path.exists(school_dir):
            os.mkdir(school_dir)

        with io.open(os.path.join(school_dir, "code.lp"), "w", encoding="utf8") as fp:
            fp.write(unicode(code))

    # def set_token_for_comp(self, ctoken, utoken, stoken):
    #     assert self.is_comp_token(ctoken)
    #     assert self.is_user_token(utoken)
    #     assert self.is_school_token(stoken)
    #
    #     school_dir = self.__get_dir_for_token(ctoken, ["schools", stoken])
    #     if not os.path.exists(school_dir):
    #         os.mkdir(school_dir)
    #     with io.open(os.path.join(school_dir, "code.lp"), "w", encoding="utf8") as fp:
    #         code = self.get_code(utoken)
    #         assert code is not None
    #         fp.write(code)
    #     # with open(os.path.join(school_dir, "name"), "w") as fp:
    #     #     name = self.get_name(stoken)
    #     #     assert name is not None
    #     #     fp.write(name)

    def get_comp_code(self, ctoken, stoken):
        school_dir = self.__get_dir_for_token(ctoken, ["schools", stoken])
        if os.path.exists(os.path.join(school_dir, "code.lp")):
            with io.open(os.path.join(school_dir, "code.lp"), "r", encoding="utf8") as fp:
                return fp.read()
        else:
            return None

    def get_comp_tokens(self):
        return self.__get_comp_tokens()

    def get_comps_for_token(self, utoken):
        comps = []
        stoken = self.get_school_for_token(utoken)
        for comp in self.__get_comp_tokens():
            if stoken in self.get_schools_in_comp(comp):
                comps += [comp]
        return comps

    def get_schools_in_comp(self, ctoken):
        return os.listdir(self.__get_dir_for_token(ctoken, "schools"))

    def set_comp_avg_score(self, ctoken, stoken, score):
        school_dir = self.__get_dir_for_token(ctoken, ["schools", stoken])
        assert school_dir is not None
        with io.open(os.path.join(school_dir, "avg_score"), "w", encoding="utf8") as fp:
            fp.write(unicode(score))

    def get_comp_avg_score(self, ctoken, stoken):
        school_dir = self.__get_dir_for_token(ctoken, ["schools", stoken])
        if os.path.exists(os.path.join(school_dir, "avg_score")):
            with io.open(os.path.join(school_dir, "avg_score"), "r", encoding="utf8") as fp:
                return float(fp.read())
        else:
            return None

    def save_code(self, token, code):
        """Save a user's code under their token.

        Args:
            token (str): The user's token.
            code (str): The user's code.
        """
        assert os.path.exists(self.__get_dir_for_token(token))
        with io.open(self.__get_dir_for_token(token, "code.lp"), "w", encoding="utf8") as fp:
            fp.write(unicode(code))

    def save_name(self, token, name):
        """Save a user's name under their token.

        Args:
            token (str): The user's token.
            name (str): The user's name.
        """
        assert os.path.exists(self.__get_dir_for_token(token))
        with io.open(self.__get_dir_for_token(token, "name"), "w", encoding="utf8") as fp:
            fp.write(unicode(name))

    def save_avg_score(self, token, score):
        """Save a user's average score.

        Args:
            token (str): The user's token.
            score (int): The user's average score.
        """
        assert os.path.exists(self.__get_dir_for_token(token))
        with io.open(self.__get_dir_for_token(token, "avg_score"), "w", encoding="utf8") as fp:
            fp.write(unicode(score))

    def get_code(self, token):
        if os.path.exists(self.__get_dir_for_token(token, "code.lp")):
            with io.open(self.__get_dir_for_token(token, "code.lp"), "r", encoding="utf8") as fp:
                return fp.read()
        else:
            return None

    def get_name(self, token):
        if self.is_user_token(token) or self.is_school_token(token) or self.is_comp_token(token):
            if os.path.exists(self.__get_dir_for_token(token, "name")):
                with io.open(self.__get_dir_for_token(token, "name"), "r", encoding="utf8") as fp:
                    return fp.read()
        return None

    def get_avg_score(self, token):
        if os.path.exists(self.__get_dir_for_token(token, "avg_score")):
            with io.open(self.__get_dir_for_token(token, "avg_score"), "r", encoding="utf8") as fp:
                try:
                    # Try to convert to float
                    return float(fp.read())
                except ValueError as e:
                    # If failed return none
                    return None
        else:
            return None

    # def get_name(self, token):
    #     if self.is_user_token(token):
    #         return self.
    #         return self.tokens[token]["name"]
    #     elif self.is_school_token(token):
    #         return self.schools[token]["name"]

    def get_school_for_token(self, token):
        for school in self.__get_school_tokens():
            if token in self.__get_school_user_tokens(school):
                return school
        return None

    # Get tokens that belong to a school
    def get_tokens_for_school(self, school_tk):
        return self.__get_school_user_tokens(school_tk)

    def get_school_tokens(self):
        return self.__get_school_tokens()

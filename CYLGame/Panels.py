from collections import defaultdict, namedtuple, Mapping
from functools import reduce
from copy import copy

DEFAULT_CHAR = ' '


class ColoredChar(object):
    def __init__(self, char=None, foreground=None, background=None):
        if isinstance(char, ColoredChar):
            self.char = char.char
            self.foreground = char.foreground
            self.background = char.background
        else:
            self.char = char
            self.foreground = foreground
            self.background = background

    def __str__(self):
        return self.char

    def __iter__(self):
        return [self.char, self.foreground, self.background].__iter__()

    def __repr__(self):
        return "<ColoredChar '" + str(self.char) + "', " + str(self.foreground) + ", " + str(self.background) + ">"

    # NOTE: == will only test both chars not the colors.
    def __eq__(self, other):
        if isinstance(other, str):
            return self.char == other
        else:
            assert isinstance(other, ColoredChar)
            return self.char == other.char


# WARNING: this does not do bounds checking
# TODO: Should the map do bounds checking?
class Map(object):
    """
    char_to_ps: This is a dictionary which has a character for the keys and the value for the key is a set of all the
                positions where that char is located.
    p_to_char:  The is a dictionary which has a position(tuple with two elements: x and y) as a key and the current
                ColoredChar as the value.
    """
    def __init__(self, default_char=DEFAULT_CHAR, default_foreground=(255, 255, 255), default_background=(0, 0, 0), default_colored_char=None):
        if default_colored_char:
            self.default_char = default_colored_char.char
            self.default_foreground = default_colored_char.foreground
            self.default_background = default_colored_char.background
        else:
            self.default_char = default_char
            self.default_foreground = default_foreground
            self.default_background = default_background
        self.char_to_ps = defaultdict(set)
        self.p_to_char = defaultdict(lambda: ColoredChar(self.default_char, self.default_foreground, self.default_background))
        self.changes = {}

    def __setitem__(self, key, value):
        self.add(value, key)

    def __getitem__(self, item):
        return self.get_char_at(item)

    # changes in the format of a dictionary
    # key: (x, y)
    # value: new_char
    def get_diff(self):
        changes = self.changes
        self.changes = {}
        return changes

    # pos must be tuple
    def add(self, char, pos):
        if type(char) == str:
            colored_char = ColoredChar(char)
        else:
            colored_char = char
            char = colored_char.char
            assert type(colored_char) == ColoredChar
        assert type(pos) == tuple

        if pos in self.p_to_char.keys():
            self.rm_char(pos)
        self.char_to_ps[char].add(pos)
        self.p_to_char[pos] = colored_char
        self.changes[pos] = colored_char

    # pos must be tuple
    def rm_char(self, pos):
        assert type(pos) == tuple
        colored_char = self.p_to_char[pos]
        del self.p_to_char[pos]
        char = colored_char.char
        if char in self.char_to_ps and pos in self.char_to_ps[char]:
            self.char_to_ps[char].remove(pos)
            self.changes[pos] = self.default_char

    # returns a set of pos
    def get_all_pos(self, char):
        if isinstance(char, ColoredChar):
            char = char.char
        assert isinstance(char, str)
        assert len(char) == 1
        return copy(self.char_to_ps[char])

    # will return default_char if the position is not set
    # Will return a ColoredChar
    def get_char_at(self, pos):
        return copy(self.p_to_char[pos])


class PanelPadding(object):
    TOP = 1
    RIGHT = 2
    LEFT = 4
    BOTTOM = 8
    DEFAULT_SIZE = 0

    def __init__(self, sides=0, size=0):
        self.sides = sides
        self.style = {self.sides: size}

    @staticmethod
    def create(top=False, bottom=False, right=False, left=False):
        paddings = [PanelPadding()]
        if type(top) == bool and top:
            paddings += [PanelPadding(PanelPadding.TOP)]
        elif type(top) == int:
            paddings += [PanelPadding(PanelPadding.TOP, top)]
        if type(bottom) == bool and bottom:
            paddings += [PanelPadding(PanelPadding.BOTTOM)]
        elif type(bottom) == int:
            paddings += [PanelPadding(PanelPadding.BOTTOM, bottom)]
        if type(right) == bool and right:
            paddings += [PanelPadding(PanelPadding.RIGHT)]
        elif type(right) == int:
            paddings += [PanelPadding(PanelPadding.RIGHT, right)]
        if type(left) == bool and left:
            paddings += [PanelPadding(PanelPadding.LEFT)]
        elif type(left) == int:
            paddings += [PanelPadding(PanelPadding.LEFT, left)]

        return reduce(lambda x, y: x | y, paddings)

    def __or__(self, other):
        assert isinstance(other, PanelPadding)
        new_padding = PanelPadding()
        new_padding.sides = other.sides | self.sides
        new_padding.style = self.style
        new_padding.style.update(other.style)
        return new_padding

    def __getitem__(self, item):
        if item in self.style:
            if self.style[item]:
                return self.style[item]
        return self.DEFAULT_SIZE

    def __contains__(self, item):
        return self.has_side(item)

    def has_side(self, side):
        return True
        # return side in self.style


class PanelBorder(object):
    TOP = 1
    RIGHT = 2
    LEFT = 4
    BOTTOM = 8
    DEFAULT_CHARS = {TOP: chr(196), BOTTOM: chr(196), RIGHT: chr(179), LEFT: chr(179),
                     TOP | RIGHT: chr(191), TOP | LEFT: chr(218), BOTTOM | RIGHT: chr(217), BOTTOM | LEFT: chr(192)}

    def __init__(self, sides=0, char=None):
        self.sides = sides
        self.style = {self.sides: char}

    @staticmethod
    def create(top=False, bottom=False, right=False, left=False, top_right=False, top_left=False, bottom_right=False,
               bottom_left=False):
        """
        Use this method for an easy way to create nice borders. Set any side to true to create a border with the default
        characters. You can also set any side to a character which will create a border with that character instead.
        In order for the corners (top_right, top_left, ...) to be rendered both of their respective sides must be set
        to True or a char.

        Ex.
        >>> PanelBorder.create(top=True)  # This will create a top border with the default char

        >>> PanelBorder.create(top='$')  # This will create a top border of '$'s.

        >>> PanelBorder.create(top='=', left='!', top_left='?')  # This will create a border looking like some thing below.
            ?====
            !
            !
        """
        borders = []
        if type(top) == bool and top:
            borders += [PanelBorder(PanelBorder.TOP)]
        elif type(top) == str:
            borders += [PanelBorder(PanelBorder.TOP, char=top)]
        if type(bottom) == bool and bottom:
            borders += [PanelBorder(PanelBorder.BOTTOM)]
        elif type(bottom) == str:
            borders += [PanelBorder(PanelBorder.BOTTOM, char=bottom)]
        if type(right) == bool and right:
            borders += [PanelBorder(PanelBorder.RIGHT)]
        elif type(right) == str:
            borders += [PanelBorder(PanelBorder.RIGHT, char=right)]
        if type(left) == bool and left:
            borders += [PanelBorder(PanelBorder.LEFT)]
        elif type(left) == str:
            borders += [PanelBorder(PanelBorder.LEFT, char=left)]
        if type(top_right) == bool and top_right:
            borders += [PanelBorder(PanelBorder.TOP | PanelBorder.RIGHT)]
        elif type(top_right) == str:
            borders += [PanelBorder(PanelBorder.TOP | PanelBorder.RIGHT, char=top_right)]
        if type(top_left) == bool and top_left:
            borders += [PanelBorder(PanelBorder.TOP | PanelBorder.LEFT)]
        elif type(top_left) == str:
            borders += [PanelBorder(PanelBorder.TOP | PanelBorder.LEFT, char=top_left)]
        if type(bottom_right) == bool and bottom_right:
            borders += [PanelBorder(PanelBorder.BOTTOM | PanelBorder.RIGHT)]
        elif type(bottom_right) == str:
            borders += [PanelBorder(PanelBorder.BOTTOM | PanelBorder.RIGHT, char=bottom_right)]
        if type(bottom_left) == bool and bottom_left:
            borders += [PanelBorder(PanelBorder.BOTTOM | PanelBorder.LEFT)]
        elif type(bottom_left) == str:
            borders += [PanelBorder(PanelBorder.BOTTOM | PanelBorder.LEFT, char=bottom_left)]

        return reduce(lambda x, y: x | y, borders)

    def __or__(self, other):
        assert isinstance(other, PanelBorder)
        new_border = PanelBorder()
        new_border.sides = other.sides | self.sides
        new_border.style = self.style
        new_border.style.update(other.style)
        return new_border

    def __getitem__(self, item):
        if item in self.style:
            if self.style[item]:
                return self.style[item]
        return self.DEFAULT_CHARS[item]

    def __contains__(self, item):
        return self.has_side(item)

    def has_side(self, side):
        return side in self.style


class Panel(Map):
    def __init__(self, x, y, w, h, background_char=DEFAULT_CHAR, border=PanelBorder(), padding=PanelPadding(), default_colored_char=None):
        super(Panel, self).__init__(background_char, default_colored_char=default_colored_char)
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.border = border
        self.padding = padding
        self.real_y = y
        self.real_x = x
        self.real_w = w
        self.real_h = h
        if PanelBorder.TOP in self.border:
            self.y += 1
            self.h -= 1
        if PanelBorder.LEFT in self.border:
            self.x += 1
            self.w -= 1
        if PanelBorder.BOTTOM in self.border:
            self.h -= 1
        if PanelBorder.RIGHT in self.border:
            self.w -= 1
        if PanelPadding.TOP in self.padding:
            self.y += self.padding[PanelPadding.TOP]
            self.h -= self.padding[PanelPadding.TOP]
        if PanelPadding.LEFT in self.padding:
            self.x += self.padding[PanelPadding.LEFT]
            self.w -= self.padding[PanelPadding.LEFT]
        if PanelPadding.BOTTOM in self.padding:
            self.h -= self.padding[PanelPadding.BOTTOM]
        if PanelPadding.RIGHT in self.padding:
            self.w -= self.padding[PanelPadding.RIGHT]

    def draw_colored_char(self, colored_char, pos, libtcod, console):
        # TODO: add asserts for these
        char, foreground, background = colored_char
        x, y = pos
        if char is not None:
            libtcod.console_set_char(console, x, y, char)
        if foreground is not None:
            libtcod.console_set_char_foreground(console, x, y, foreground)
        else:
            libtcod.console_set_char_foreground(console, x, y, self.default_foreground)
        if background is not None:
            libtcod.console_set_char_background(console, x, y, background)
        else:
            libtcod.console_set_char_background(console, x, y, self.default_background)

    def redraw(self, libtcod, console):
        if PanelBorder.TOP in self.border:
            for i in range(self.real_w):
                libtcod.console_put_char(console, self.real_x + i, self.real_y, self.border[PanelBorder.TOP],
                                         libtcod.BKGND_NONE)
        if PanelBorder.LEFT in self.border:
            for i in range(self.real_h):
                libtcod.console_put_char(console, self.real_x, self.real_y + i, self.border[PanelBorder.LEFT],
                                         libtcod.BKGND_NONE)
        if PanelBorder.BOTTOM in self.border:
            for i in range(self.real_w):
                libtcod.console_put_char(console, self.real_x + i, self.real_y + self.real_h - 1, self.border[PanelBorder.BOTTOM],
                                         libtcod.BKGND_NONE)
        if PanelBorder.RIGHT in self.border:
            for i in range(self.real_h):
                libtcod.console_put_char(console, self.real_x + self.real_w - 1, self.real_y + i, self.border[PanelBorder.RIGHT],
                                         libtcod.BKGND_NONE)
        if PanelBorder.TOP in self.border and PanelBorder.LEFT in self.border:
            libtcod.console_put_char(console, self.real_x, self.real_y, self.border[PanelBorder.TOP | PanelBorder.LEFT],
                                     libtcod.BKGND_NONE)
        if PanelBorder.BOTTOM in self.border and PanelBorder.LEFT in self.border:
            libtcod.console_put_char(console, self.real_x, self.real_y + self.real_h - 1, self.border[PanelBorder.BOTTOM | PanelBorder.LEFT],
                                     libtcod.BKGND_NONE)
        if PanelBorder.TOP in self.border and PanelBorder.RIGHT in self.border:
            libtcod.console_put_char(console, self.real_x + self.real_w - 1, self.real_y, self.border[PanelBorder.TOP | PanelBorder.RIGHT],
                                     libtcod.BKGND_NONE)
        if PanelBorder.BOTTOM in self.border and PanelBorder.RIGHT in self.border:
            libtcod.console_put_char(console, self.real_x + self.real_w - 1, self.real_y + self.real_h - 1, self.border[PanelBorder.BOTTOM | PanelBorder.RIGHT],
                                     libtcod.BKGND_NONE)


class MapPanel(Panel):
    def __init__(self, x, y, w, h, default_char=DEFAULT_CHAR, border=PanelBorder(), padding=PanelPadding(), default_colored_char=None):
        super(MapPanel, self).__init__(x, y, w, h, default_char, border, padding, default_colored_char=default_colored_char)
        # self.first_draw()
        self.is_first = True

    def first_draw(self, libtcod, console):
        # pass
        for x in range(self.w):
            for y in range(self.h):
                self.draw_colored_char(self[(x, y)], (self.x + x, self.y + y), libtcod, console)

    def redraw(self, libtcod, console):
        super(MapPanel, self).redraw(libtcod, console)
        if self.is_first:
            self.first_draw(libtcod, console)
            self.is_first = False
        diff = self.get_diff()
        for pos in diff:
            colored_char = diff[pos]
            # if not colored_char.foreground:
            #     colored_char = ColoredChar(colored_char.char, self.default_foreground, colored_char.background)
            # if not colored_char.background:
            #     colored_char = ColoredChar(colored_char.char, colored_char.foreground, self.default_background)

            # Check that the position is in bounds
            if 0 <= pos[0] < self.w and 0 <= pos[1] < self.h:
                self.draw_colored_char(colored_char, (self.x + pos[0], self.y + pos[1]), libtcod, console)
                # libtcod.console_put_char(console, self.x + pos[0], self.y + pos[1], char, libtcod.BKGND_NONE)
            else:
                raise Warning("Char out of bounds: Decided to skip drawing it!")


class MessagePanel(Panel):
    def __init__(self, x, y, w, h, default_char=DEFAULT_CHAR, border=PanelBorder(), padding=PanelPadding.create(*[1]*4)):
        super(MessagePanel, self).__init__(x, y, w, h, default_char, border, padding)
        self.msgs = []
        self.rows = self.h
        self.max_len = self.w

    def __add__(self, other):
        self.add(other)
        return self

    def __getitem__(self, item):
        assert isinstance(item, int)
        return self.msgs[item]

    # TODO: Decide if this should be allowed
    # Message should act like a stack without popping only adding
    def __setitem__(self, key, value):
        assert isinstance(key, int)
        assert isinstance(value, str)
        assert "\n" not in value
        if 0 <= key < len(self.msgs):
            self.msgs[key] = value

    def __iter__(self):
        return self.msgs.__iter__()

    def __contains__(self, item):
        return item in self.msgs

    def add(self, messages):
        assert isinstance(messages, str) or hasattr(messages, '__iter__')
        if isinstance(messages, str):
            messages = [messages]
        for message in messages:
            self.msgs += message.split("\n")

    def clear(self):
        self.msgs = []

    def get_current_messages(self):
        return self.msgs[-self.rows:]

    def redraw(self, libtcod, console):
        super(MessagePanel, self).redraw(libtcod, console)
        msgs_to_display = self.get_current_messages()
        for j in range(len(msgs_to_display)):
            msg = msgs_to_display[j]
            # TODO: optimize this
            # Clear msg board
            for i in range(self.max_len):
                libtcod.console_put_char(console, self.x + i, self.y + j, self.default_char)
            # Print msg
            for i in range(min(len(msg), self.max_len)):
                libtcod.console_put_char(console, self.x + i, self.y + j, msg[i])


class StatusPanel(MessagePanel):
    def __init__(self, x, y, w, h, default_char=DEFAULT_CHAR, border=PanelBorder(), padding=PanelPadding().create(*[1]*4)):
        super(StatusPanel, self).__init__(x, y, w, h, default_char, border, padding)
        self.info = {}

    def __getitem__(self, item):
        return self.info[item]

    def __setitem__(self, key, value):
        self.info[str(key)] = str(value)

    def __contains__(self, item):
        return item in self.info

    def get_current_messages(self):
        self.msgs = []
        for key in self.info:
            self.msgs += [key + ": " + self.info[key]]
        return super(StatusPanel, self).get_current_messages()

# ---------------------------------------
#    Import Libraries
# ---------------------------------------
import codecs
import json
import os
import re
import sys
import clr
clr.AddReference("IronPython.SQLite.dll")
clr.AddReference("IronPython.Modules.dll")


# ---------------------------------------
#    [Required]    Script Information
# ---------------------------------------
ScriptName = "DiceRoller"
Website = "https://www.twitch.tv/vestofholding"
Description = "Roll multi-sided dice in chat."
Creator = "VestOfHolding"
Version = "1.0"

# ---------------------------------------
# Set Variables
# ---------------------------------------

# This should match against strings like "2d6 + 4d20 + 7"
m_validChars = re.compile('[0-9+d ]+', re.IGNORECASE)
# This should match against the individual dice argument, such as "2d20", but note the dice number and dice side limit.
# The limits are a little higher than the actual limits so that users can change those limits in the future better,
# and to increase the liklihood of accurate error messages being produced.
m_rollFormat = re.compile('^([1-9]\d{0,7})?(d)([1-9]\d{0,7})$', re.IGNORECASE)

m_max_die_sides = 1000
m_max_die_num = 10

m_settings_file = os.path.join(os.path.dirname(__file__), "DiceRollerConfig.json")


# ---------------------------------------
# [Required]    Classes With These Specific Signatures
# ---------------------------------------
# noinspection PyPep8Naming
class Settings(object):
    """ Load in saved settings file if available else set default values. """
    def __init__(self, settings_file=None):
        try:
            with codecs.open(settings_file, encoding="utf-8-sig", mode="r") as f:
                self.__dict__ = json.load(f, encoding="utf-8-sig")
        except StandardError:
                self.command = "!roll"
                self.permission = "Everyone"
                self.cooldown = 2
                self.user_cooldown = 3
        return

    def reload(self, data):
        """ Reload settings from Chatbot user interface by given data. """
        self.__dict__ = json.loads(data, encoding="utf-8-sig")
        return

    def save(self, settings_file):
        """ Save settings contained within to .json and .js settings files. """
        try:
            with codecs.open(settings_file, encoding="utf-8-sig", mode="w+") as f:
                json.dump(self.__dict__, f, encoding="utf-8-sig")
            with codecs.open(settings_file.replace("json", "js"), encoding="utf-8-sig", mode="w+") as f:
                f.write("var settings = {0};".format(json.dumps(self.__dict__, encoding='utf-8-sig')))
        except StandardError:
            Parent.Log(ScriptName, "Failed to save settings to file.")
        return


# ---------------------------------------------------------
# [Required]    Functions With These Specific Signatures
# ---------------------------------------------------------
# noinspection PyPep8Naming
def Init():
    """[Required] Initialize Data (Only called on Load)"""
    global m_settings

    m_settings = Settings(m_settings_file)
    return


# noinspection PyPep8Naming
def ReloadSettings(json_data):
    """Reload Settings on Save"""
    m_settings.reload(json_data)
    return


# noinspection PyPep8Naming
def Tick():
    """[Required] Tick Function"""
    return


# noinspection PyPep8Naming,PyUnusedLocal
def ScriptToggled(state):
    return


# noinspection PyPep8Naming
def OpenReadMe():
    location = os.path.join(os.path.dirname(__file__), "README.txt")
    os.startfile(location)
    return


# noinspection PyPep8Naming
def Execute(data):
    """[Required] Execute Data / Process Messages"""
    global m_settings, ScriptName

    if not data.IsChatMessage() or data.GetParam(0).lower() != m_settings.command:
        post_execute(data)
        return

    if not Parent.HasPermission(data.User, m_settings.permission, "") or \
            Parent.IsOnCooldown(ScriptName, m_settings.command) or \
            Parent.IsOnUserCooldown(ScriptName, m_settings.command, data.User):
        post_execute(data)
        return

    # If no specific dice are listed, perform default roll
    if data.GetParamCount() == 1:
        post_execute(data, "Rolling 1d20... " + str(Parent.GetRandom(1, 21)))
        return

    try:
        # Pre-process the parameters to get them in to a more usable format
        dice_data = pre_process_data(data)

        # Roll all the dice we can find
        dice_rolls = roll_all_dice(dice_data)

        # If we somehow got through the previous code and have no resulting dice
        # raise dat error
        if len(dice_rolls) < 1:
            raise NoDiceFoundError()

        dice_sum = sum(dice_rolls)

        # A similar pre-caution as above.
        if dice_sum < 1:
            raise NoDiceFoundError()

    except DiceError as de:
        # It's here at the top level that we look at the error and let the user know about the error.
        post_execute(data, de.message)
        return

    response = "Rolling "

    response += " + ".join(str(d) for d in dice_data)
    response += "...   "

    if len(dice_rolls) > 1:
        response += " + ".join(str(d) for d in dice_rolls)
        response += " = " + str(dice_sum)
    else:
        response += str(dice_sum)

    post_execute(data, response)
    return


# ---------------------------------------------------------
# Other Functions
# ---------------------------------------------------------
def pre_process_data(data):
    """Given the data object that comes from Twitch via Streamlabs Chatbot,
        pull out the parameters we want and map them to a much simpler list.

    :param data: The original object from Twitch.
    :return: A list containing only dice roll parameters.
    """
    # Retrieve the message as a String while ignoring the initial command
    raw_message = "".join(data.Message.split(" ")[1:])

    # Yes, this needs to happen in addition to the valid characters check that happens right after this.
    # Because god knows what unicode shenanigans is happening that I don't feel like investigating
    # for this script.
    if non_ascii_check(raw_message):
        raise NonASCIIDiceError()

    if not re.match(m_validChars, raw_message):
        raise InvalidDiceCharacterError()

    # Now turn that raw String in to a more workable list of the dice parameters
    raw_message = raw_message.replace(" ", "")
    return raw_message.split("+")


def non_ascii_check(raw_message):
    """Checks for the presence of non-ASCII characters in the input.

    :param raw_message: The string input
    :return: True if a non-ASCII letter was found in the input. False otherwise.
    """
    try:
        raw_message.decode('ascii')
    except ValueError:
        return True
    else:
        return False


def roll_all_dice(dice_data_set):
    """Given a set of dice to roll, roll them all and return
    the list of results.

    :param dice_data_set: A list of dice to roll, such as "4d6".
    :return: A list of the roll results, or an empty list if any errors are found.
    """
    dice_results = []

    if len(dice_data_set) < 1:
        raise NoDiceFoundError()

    for dice in dice_data_set:
        dice_roll = dice.strip()

        try:
            dice_result = handle_die_roll(dice_roll)

            # If somehow we got no valid results but no errors were raised, that's a problem.
            if len(dice_result) < 1:
                raise NoDiceFoundError()

        except DiceError:
            # Raise the error up to the calling method that will handle everything more properly.
            raise

        dice_results.extend(dice_result)

        if len(dice_results) > m_max_die_num:
            raise InvalidDiceCountError()

    return dice_results


def handle_die_roll(dice):
    """Given a single type of dice roll to do, such as "2d20", roll however many
    type of dice of that type we were told to, and return the list of results.

    This may be a simple integer as a flat positive modifier instead.

    Will return no results if the maximum number of dice to roll or dice sides is exceeded.

    :param dice: The single type of dice roll to do, or a positive integer.
    :return: The list of integer results, or an empty list if any errors are found.
    """
    # This script also supports flat integer additions to the roll
    if dice.isdigit():
        if int(dice) > 1000:
            raise InvalidDiceModifierError()
        return [int(dice)]

    regex_result = re.match(m_rollFormat, dice)

    if not regex_result:
        raise DiceError(dice)

    groups = regex_result.groups()

    # There should only be two possibilities:
    # 1. We have a format like "d20", where we assume the number of dice is 1.
    # 2. We have a format like "2d20" where the number of dice is given.
    if len(groups) != 3 or str(groups[1]).lower() != "d":
        raise DiceError(dice)

    if groups[0] is None:
        num_dice = 1
    else:
        num_dice = int(groups[0])

    num_dice_sides = int(groups[2])

    # ALL OF THE INPUT CHECKING
    if num_dice > m_max_die_num:
        raise InvalidDiceCountError()

    if num_dice_sides > m_max_die_sides:
        raise InvalidDiceSideError()

    if num_dice < 1 or num_dice_sides < 2:
        raise DiceError(dice)

    # Now get to the actual die rolling.
    die_roll_results = []

    for x in xrange(0, num_dice):
        die_result = Parent.GetRandom(1, num_dice_sides)

        # If for some reason we went past all of the above checking and something still happened
        # the likely result will be that we get a 0. Therefore check for that and report the error.
        if die_result < 1:
            raise DiceError(dice)

        die_roll_results.append(die_result)

    return die_roll_results


def post_execute(data, message=None):
    """Should always be called right before the script ends processing a command."""
    if message is not None:
        Parent.SendTwitchMessage(message)

    Parent.AddUserCooldown(ScriptName, m_settings.command, data.User, m_settings.user_cooldown)
    Parent.AddCooldown(ScriptName, m_settings.command, m_settings.cooldown)

    return


# ---------------------------------------------------------
# Exceptions
# ---------------------------------------------------------
class DiceError(Exception):
    """Basic exception for errors raised by trying to roll dice"""
    def __init__(self, dice, msg=None):
        if msg is None:
            if dice is None:
                msg = "Invalid parameter found. Unable to roll dice."
            else:
                msg = "Invalid parameter found. Unable to roll " + str(dice)

        super(DiceError, self).__init__(msg)
        self.dice = dice


class InvalidDiceCountError(DiceError):
    """Tried to roll an invalid number of dice"""
    def __init__(self):
        super(InvalidDiceCountError, self).__init__(
            None, msg="Please don't ask to roll more than " + str(m_max_die_num) + " dice at a time.")


class InvalidDiceSideError(DiceError):
    """Tried to roll a dice with an invalid number of sides."""
    def __init__(self):
        super(InvalidDiceSideError, self).__init__(
            None, msg="Please don't ask to roll dice with more than " + str(m_max_die_sides) + " sides.")


class InvalidDiceModifierError(DiceError):
    """Tried to roll a dice with an invalid number of sides."""
    def __init__(self):
        super(InvalidDiceModifierError, self).__init__(
            None, msg="Please don't use a modifier higher than " + str(m_max_die_sides))


class NoDiceFoundError(DiceError):
    """No valid dice were found that could be rolled."""
    def __init__(self):
        super(NoDiceFoundError, self).__init__(None, msg="No valid dice found to roll.")


class InvalidDiceCharacterError(DiceError):
    """Unsupported characters were found in the dice input."""
    def __init__(self, msg=None):
        if msg is None:
            msg = "Unsupported characters found. No dice were rolled."

        super(InvalidDiceCharacterError, self).__init__(None, msg)


class NonASCIIDiceError(InvalidDiceCharacterError):
    """Non-ASCII characters were found in the user input."""
    def __init__(self):
        super(NonASCIIDiceError, self).__init__(msg="I will shit on your desk.")

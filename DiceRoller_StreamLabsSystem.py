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
m_rollFormat = re.compile('^([1-9]\d?)d([1-9]\d{0,3})$', re.IGNORECASE)

m_max_die_sides = 1000
m_max_die_num = 10

# Error Messages
m_default_error = "Invalid parameter found. Unable to roll "
m_dice_num_max_exceeded = "Please don't ask to roll more than " + str(m_max_die_num) + " dice at a time."
m_no_valid_rolls = "No valid dice found to roll."

m_settings_file = os.path.join(os.path.dirname(__file__), "DiceRollerConfig.json")


# ---------------------------------------
# Classes
# ---------------------------------------
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


def Init():
    """[Required] Initialize Data (Only called on Load)"""
    global m_settings

    m_settings = Settings(m_settings_file)
    return


def ReloadSettings(json_data):
    """Reload Settings on Save"""
    m_settings.reload(json_data)
    return


def Tick():
    """[Required] Tick Function"""
    return


def ScriptToggled(state):
    return


def OpenReadMe():
    location = os.path.join(os.path.dirname(__file__), "README.txt")
    os.startfile(location)
    return


def Execute(data):
    """[Required] Execute Data / Process Messages"""
    global m_settings, ScriptName

    if not data.IsChatMessage()\
            or data.GetParam(0).lower() != m_settings.command:
        return

    if Parent.IsOnCooldown(ScriptName, m_settings.command)\
            or not Parent.HasPermission(data.User, m_settings.permission, ""):
        return

    # If no specific dice are listed, perform default roll
    if data.GetParamCount() == 1:
        Parent.SendTwitchMessage("Rolling 1d20... " + str(Parent.GetRandom(1, 21)))
        return

    # Pre-process the parameters to get them in to a more usable format
    # Roll all the dice we can find
    dice_data = pre_process_data(data)

    dice_rolls = roll_all_dice(dice_data)

    if len(dice_rolls) < 1:
        return

    dice_sum = sum(dice_rolls)

    if dice_sum < 1:
        return

    response = "Rolling "

    response += " + ".join(str(d) for d in dice_data)
    response += "...   "

    if len(dice_rolls) > 1:
        response += " + ".join(str(d) for d in dice_rolls)
        response += " = " + str(dice_sum)
    else:
        response += str(dice_sum)

    Parent.SendTwitchMessage(response)

    return


def pre_process_data(data):
    """Given the data object that comes from Twitch via Streamlabs Chatbot,
        pull out the parameters we want and map them to a much simpler list.

    :param data: The original object from Twitch.
    :return: A list containing only dice roll parameters.
    """
    # Retrieve the message as a String while ignoring the initial command
    raw_message = "".join(data.Message.split(" ")[1:])

    if special_check(raw_message):
        Parent.SendTwitchMessage("Don't test me, human.")
        return []

    if not re.match(m_validChars, raw_message):
        Parent.SendTwitchMessage("Unsupported characters found. No dice were rolled.")
        return []

    # Now turn that raw String in to a more workable list of the dice parameters
    raw_message = raw_message.replace(" ", "")
    return raw_message.split("+")


def special_check(raw_message):
    """Makes a special check for non-ASCII characters.

    :param raw_message:
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
        return dice_results

    # There doesn't seem to be a way to just get the list of parameters, so we'll do it this way.
    # The first parameter is the command itself, so skip that one.
    for dice in dice_data_set:
        dice_roll = dice.strip()

        # Not sure we have to make sure it's an int, but I'm still used to type safety.
        dice_result = handle_die_roll(dice_roll)

        # If anything went wrong that meant we got no results, it was an error and we're done.
        if len(dice_result) < 1:
            return []

        dice_results.extend(dice_result)

        if len(dice_results) > m_max_die_num:
            Parent.SendTwitchMessage(m_dice_num_max_exceeded)
            return []

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
            Parent.SendTwitchMessage("Please don't use a modifier higher than " + str(m_max_die_sides))
            return []
        return [int(dice)]

    regex_result = re.match(m_rollFormat, dice)

    if not regex_result:
        Parent.SendTwitchMessage(m_default_error + dice)
        return []

    groups = regex_result.groups()

    # We better have only two things:
    # 1. How many dice to roll
    # 2. How many sides these dice have
    if len(groups) != 2:
        Parent.SendTwitchMessage(m_default_error + dice)
        return []

    # ALL OF THE INPUT CHECKING
    num_dice = int(groups[0])

    if num_dice > m_max_die_num:
        Parent.SendTwitchMessage(m_dice_num_max_exceeded)
        return []

    num_dice_sides = int(groups[1])

    if num_dice_sides > m_max_die_sides:
        Parent.SendTwitchMessage("Please don't ask to roll dice with more than " + str(m_max_die_sides) + " sides.")
        return []

    if num_dice < 1 or num_dice_sides < 2:
        Parent.SendTwitchMessage(m_default_error + dice)
        return []

    # Now get to the actual die rolling.
    die_roll_results = []

    for x in xrange(0, num_dice):
        die_result = Parent.GetRandom(1, num_dice_sides)

        # If for some reason we went past all of the above checking and something still happened
        # the likely result will be that we get a 0. Therefore check for that and report the error.
        if die_result < 1:
            Parent.SendTwitchMessage(m_default_error + dice)
            return []

        die_roll_results.append(die_result)

    return die_roll_results

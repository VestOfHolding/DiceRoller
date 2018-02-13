# DiceRoller for StreamLabs Chatbot


Created by: VestOfHolding - www.twitch.tv/vestofholding

Version: 1.0

This is a dice-rolling script designed to handle rolling multiple dice of number of sides at once as a custom script for use with [StreamLabs Chatbot](https://streamlabs.com/chatbot).

Due to StreamLabs Chatbot being written in .NET, [IronPython](http://ironpython.net/) is required as the interpreter in order for this project to work, which is also the same reason this project is written in Python 2.7.

All other questions about how to use this script within the Chatbot can be found in their documentation.

### Features

* Command: !roll
* If no further dice information is provided, the default is to roll one d20.
* Roll up to 10 dice of any number of sides up to 1000.
  * Example: !roll 3d10 + 5d20 + 1d1000
* Watch as the script outputs the result of each die roll as well as the total.
  * The 10 dice limit is to limit how much this impacts the chat.
* Add positive modifiers to your roll up to 1000.
  * Example: !roll 2d20 + 10
  * Modifiers count towards the 10 roll limit.
* Configurable cooldown with a default of 2 seconds.

Examples of invalid uses of this command include:

* !roll 0d6
* !roll 2d-8
* !roll 100d10
  * This exceeds the 10 dice limit.
* !roll 4d6 + 8d50
  * This exceeds the 10 dice limit.
* !roll 2d1200
  * This exceeds the 1000 side limit.
* !roll 4d6 - 8
  * No negative modifiers can be used currently.
* !roll 1dπ
  * You know who you are.

## Version History

### 1.0
- Initial Release
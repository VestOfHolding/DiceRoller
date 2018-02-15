# DiceRoller for StreamLabs Chatbot


Created by: VestOfHolding - www.twitch.tv/vestofholding

Version: 1.0

This is a dice-rolling script designed to handle rolling multiple dice of number of sides at once as a custom script for use with [StreamLabs Chatbot](https://streamlabs.com/chatbot).

Due to StreamLabs Chatbot being written in .NET, [IronPython](http://ironpython.net/) is required as the interpreter in order for this project to work, which is also the same reason this project is written in Python 2.7.

All other questions about how to use this script within the Chatbot can be found in their documentation.

## Features and Usage

This script uses [dice notation](https://en.wikipedia.org/wiki/Dice_notation) to specify what dice and how many you want to roll. The current version supports only the [standard notation](https://en.wikipedia.org/wiki/Dice_notation#Standard_notation). It will then output each individual die result, as well as the total of all dice rolled.

* `!roll`
  * With no other parameters specified, this script will roll 1d20.
  * Example output: `Rolling 1d20... 14`
* `!roll 1d20`
  * The normal standard notation is accepted.
  * Example output: `Rolling 1d20... 2`
* `!roll 2d20 + 2d6`
  * Multiple standard notation dice of different sides can be rolled together.
  * Example output: `Rolling 2d20 + 2d6... 14 + 20 + 2 + 3 = 39`
* `!roll 2d6 + 5`
  * Integer modifiers can be added to a dice roll.
  * Example output: `Rolling 2d6 + 5... 2 + 3 + 5= 10`

### Restrictions

* This script currently cannot handle any arithmetic operators besides "+".
  * `!roll 1d20 - 5` will throw an error.
* No more than ten dice/modifiers can be used in one command. This is to minimize the impact that displaying all of the individual dice rolls has on chat.
  * `!roll 11d6`, `!roll 8d6 + 4d8`, and `!roll 10d6 + 5` are all examples of rolls that will hit this limit.
* The number of sides a dice has cannot exceed 1000.
  * `!roll 1d1200` will throw an error.
* Any integer modifier added to the roll cannot exceed 1000.
  * `!roll 1d20 + 2000` will throw an error.


## Configurable Values

| Value  | Default |
| ------------- | ------------- |
| Command  | !roll |
| Permission | Everyone |
| Cooldown (seconds)  | 2 |


## Version History

### 1.0
- Initial Release
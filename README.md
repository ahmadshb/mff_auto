# mff_auto
Game bot for [Marvel Future Fight](https://play.google.com/store/apps/details?id=com.netmarble.mherosgb&hl=ru) game.

## FAQ
Q: What this bot can do?

A: **mff_auto** can play several game modes: World Bosses, Alliance Battle, Co-op missions, Dimension missions, Timeline battles, Legendary battles, World Boss Invasions, Epic Quests.

Q: Which Android emulators are supported?

A: Currently only [NoxPlayer](https://bignox.com).

## Video example

Video footage of all game modes running by **mff_auto**: https://youtu.be/QcgZcAwBL-I

## Installation and usage

For now installation isn't ready but you can run it manually from source code with Python3 or check out existing releases:

#### Install and setup game emulator

- Install [NoxPlayer](https://bignox.com) and then install and run [Marvel Future Fight](https://play.google.com/store/apps/details?id=com.netmarble.mherosgb&hl=ru).
- Set [NoxPlayer](https://bignox.com) graphics rendering mode to `Speed (DirectX)`: [Tutorial](https://www.bignox.com/blog/change-graphics-rendering-mode-noxplayer/)

#### From releases

Check available releases of compiled Python/Tesseract binaries for **mff_auto**: [Link to releases](https://github.com/tmarenko/mff_auto/releases)

- Edit `app.py` file to change algorithm of **mff_auto**.
- Run `start.bat` and enjoy.

#### From source code

- Install [Tesseract ORC](https://github.com/tesseract-ocr/tesseract) and add path to Tesseract to your ```PATH``` environment.
- Download source code and install all requirements: ```pip install -r requirements.txt```
- Add ```lib``` folder to your ```PYTHONPATH``` or mark it as lib source.
- Create Python file and use game modes libraries. Example:
    ```python
    from lib.players.nox_player import NoxWindow
    from lib.game.game import Game
    
    from lib.game.missions.coop import CoopPlay
    
    
    nox = NoxWindow("NoxPlayer")
    game = Game(nox)
    CoopPlay(game).do_missions()
    ```
- Run Python script and enjoy.

#### Examples

Check `example.py` for examples of running any modes.

Check `autoplay.py` for activating `Autoplay` in any battles (Shadowland, Danger Room, etc.).

## Development

At current state Marvel Future Fight bot is at alpha stage.

- Farming bios in Epic Quest requires setting up `GAME_TASK`, `GAME_TASK_DRAG_FROM`, `GAME_TASK_DRAG_TO` and `GAME_APP`
in `settings\ui\main_menu.json`. This values should be calculated for your emulator's launcher.
- Legendary Battle contains only one free battle. Can be changed in JSON's settings.
- Co-op missions do not check if you have characters for all 5 stages.
- Timeline battle do not check if your team is available for battle.
- Alliance and World Boss battles do not check if your characters can do these modes.

If you want to run any kind of mission regardless of libraries realisation:
- Open mission screen in emulator (the screen with `START` button at right bottom corner)
- Run example:
    ```python
    from lib.players.nox_player import NoxWindow
    from lib.game.game import Game
    from lib.game.missions.missions import Missions
    
    nox = NoxWindow("NoxPlayer")
    game = Game(nox)
    Missions(game, None).repeat_mission(times=20)
    ```

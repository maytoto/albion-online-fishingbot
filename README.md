# albion-online-fishingbot
A python bot for fishing in albion online

This bot is by far from being perfect or performant, but hey, it's free and open source!

I combined some sources and tutorials and came to this version.

Feel free to use it, edit it, share it, but do note that you take full responsibility for your own actions.

# How to use it

Open cmd and cd into the repo directory, then use pip install -r requirements.txt

You need to install [VB-AUDIO](https://vb-audio.com/Cable/) and set it as default device for playback and recording devices in order for the bot to be able to detect when it cought a fish.

Then I recommend to set the game resolution to 1600 x 900 windowed.

Get close to a waterpool and run main.py

# Notes

You'll mainly look into main.py do_minigame() inside fishing_bot.py to make adjustments to your liking/use-case. 

The images which have _2 are made in 1600x900, the others are in 1024x728. Opencv matches the fishing bob better with the in-game images if they're of the same resolution.

I have a screen with 1920x1080 resolution, if you've installed the VB-Cable and set everything right for sound detection but the bot doesn't complete the minigame, add this like in main():

`threading.Thread(target=debug).start()`

in order to see what the bot sees, if you are doing the minigame and the minigame bar is not fit inside the debug window, then the touple `screenshot = wincap.get_screenshot(region=(690, 440, 210, 55))` does not have the right values for your game resolution/screen

`region` is used inside windowcapture.py at get_screenshot if it helps out looking at what the bot does with those values (x, y, width, height of the minigame bar).

Adjust those values in order for the minigame bar to fit inside the debug window, then change inside main `bot = FishermanBot('./bobber_2.png', './empty_bar_2.png', (690, 440, 210, 55))` with your proper values.

If that doesn't work either or works poorly, then it might be because opencv doesn't recognizes MY image samples on your screen and game resolution, then you must take screenshots and crop and edit them like my samples and use them instead. 

# And another word

Don't expect updates on this code, but you can expect sooner or later some other bots using opencv and maybe even machine learning for gathering.

But if you find improvements to the code, you can make a pull request

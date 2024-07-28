## A Python script for auto check in *_Genshin Impact Daily Check-in_*
### **Features**:
A simple Python script to auto check in `Genshin Impact Daily Check-in` every time you run the game. It'll check if you have already checked in today or not. If not, it'll check in for you.
### How it works:
- The file `dailyCheckin.py` is the main program, it'll check in for you by sending a POST request to the server via the API, so you need to provide some information to the program (more details [here](#how-to-use)).
- The file `daycheck.py` is a module that contains the function to check if you have already checked in today or not.
- The file `genshin.bat` is a batch file that runs the program `daycheck.py` to check if you have already checked in today or not, then run the program `dailyCheckin.py` to check in for you and finally run the game `Genshin Impact`. You can add a shortcut of this file to your Desktop to run the game and check in at the same time.
### Requirements:
Up to now, I have only developed the program for my own use. Therefore, this program is known to work stably in:
- Windows 11
- Python 3.10
- Genshin server Asia account (other servers will probably need a different login API so won't work, if you know the api for your server, replace it in the `.env` file). I make no promises but will support other servers later if possible.
### How to use:
1. Clone this repository use `git clone` or download the zip file.
2. Install the required packages (***at the first time only***) use:
```bash
  python -m venv venv
  .\venv\Scripts\activate
  pip install -r requirements.txt
```
3. Modify value of `APP_PATH`, `ACT_ID` and `COOKIE` in `.env` file (More instructions [here](#get-your-act_id-and-cookie)).
4. Add shortcut of `genshin.bat` to Desktop (optional).
5. Run `genshin.bat` to play Genshin Impact and auto check in
6. You can check the log file `log.txt` to see the history of check-in.

### Another way to use:
- ***Steps 1 to 3 in the instructions above are required***
- You can also simplify the program (skip `genshin.bat`, skip the cmd window with a Vietnamese interface that you may not understand,...) by running the dailyCheckin.py program directly (_don't spam the program, it may be detected as a bot and banned_)
- With this method, you can also check in automatically with the [Task Scheduler](https://en.wikipedia.org/wiki/Windows_Task_Scheduler) through a `.bat` file running the python command `python dailyCheckin.py` (it is recommended to set a random delay time).

### Get your `ACT_ID` and `COOKIE`:
1. `ACT_ID`: 
    - _Use your browser_.
    - Go to [Hoyolab](https://www.hoyolab.com/genshin/).
    - Login with your Genshin account.
    - Go to check-in page (you may know that page).
    - Check the URL, it should look like this: \
      `https://act.hoyolab.com/ys/event/signin-sea-v3/index.html?act_id=xxxxxxxxxxxxxxxx&.........`.
    - Where `xxxxxxxxxxxxxxxx` is your `ACT_ID`.
2. `COOKIE`:
   - At the same page, press `F12` to open the Developer Tools.
   - Go to `Network` tab.
   - Refresh the page.
   - Click on the first request (should be `signin`).
   - Go to `Headers` tab.
   - Find the `cookie` field.
   - Copy the value of `cookie` field.
   - Paste it to the `.env` file.
   - **Note: Don't share your `COOKIE` with anyone.**
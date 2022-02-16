from pynput.keyboard import Key, Listener, Controller
from pynput import keyboard
import clipboard
import time
from PIL import ImageFont
import os, sys


# The key combination to check
CTRLQ = {keyboard.Key.ctrl, keyboard.KeyCode.from_char('\x11')} # q
CTRLA = {keyboard.Key.ctrl, keyboard.KeyCode.from_char('\x01')} # a
CTRL1 = {keyboard.Key.ctrl, keyboard.KeyCode.from_char('1')} # 1
CTRL2 = {keyboard.Key.ctrl, keyboard.KeyCode.from_char('2')} # 2
CTRL3 = {keyboard.Key.ctrl, keyboard.KeyCode.from_char('3')} # 2
CTRL4 = {keyboard.Key.ctrl, keyboard.KeyCode.from_char('4')} # 2
CTRLRETURN = {keyboard.Key.ctrl, keyboard.Key.enter} # return
hotkeys = CTRLQ.union(CTRLA).union(CTRLRETURN).union(CTRL1).union(CTRL2).union(CTRL3).union(CTRL4)

# The currently active modifiers
current = set()
control = Controller()
application_path = os.path.dirname(sys.argv[0])
os.chdir(application_path)
print(application_path)

with open("Settings.txt", "r") as f:
    lines = f.readlines()
    max_len = int(lines[0].split(":")[-1].strip())
    debug = str(lines[1].split(":")[-1].strip())
    if debug.lower() == "true":
        debug = True
    delay = float(lines[2].split(":")[-1].strip())
MAX_LEN = max_len
DEBUG = debug
DELAY = delay

def split_words(text, font=False, ignore_max_len=False):
    lines = text.split("\n")
    text = " ".join([l.strip() for l in lines if l])
    words = [word for word in text.split(" ") if word]
    best_split = 0
    min_diff = 42069
    if not font:
        font = ImageFont.truetype("Arial.ttf", 36)

    for x in range(len(words)):
        start = " ".join(words[:x])
        end = " ".join(words[x:])
        len_start = font.getsize(start)[0]
        len_end = font.getsize(end)[0]
        if not ignore_max_len:
            if len_start > MAX_LEN or len_end > MAX_LEN:
                continue
        diff = len_start - len_end
        if abs(diff) < min_diff:
            if diff < 100:
                min_diff = abs(diff)
                best_split = x
    if best_split == 0:
        return split_words(text, font, True)
    text = " ".join(words[:best_split]) + "\n" + " ".join(words[best_split:])
    return text

def clean_text(text):
    if (text.endswith(".") or text.endswith(",")) and not text.endswith("..."):
        text = text[:-1]

    font = ImageFont.truetype("Arial.ttf", 36)
    if any([i.islower() for i in text]):

        if font.getsize(text)[0] > MAX_LEN or '\n' in text:
            text = split_words(text)

    elif "\n" in text:

        text = split_words(text)

    return text

def press(key):
    control.press(key)
    wait()

def release(key):
    control.release(key)
    wait()

def wait(t=DELAY):
    time.sleep(t)

def start_check(last1="1", last2="2", last3="3"):
    text = get_text()
    if not isinstance(text, str):
        print("Process interrupted and ended prematurely")
        return
    elif len(text) > 1000:
        print("Process interrupted and ended prematurely")
        print(len(text))
        return
    if text == last1 and text == last2 and text == last3:
        print("Process ended naturally")
        return

    new_text = clean_text(text)
    if new_text != text:
        return_text(new_text)
    else:
        next_text()

    next_text()
    wait()
    return start_check(new_text, last1, last2)

def get_text():
    press(Key.cmd)
    press("a")
    release("a")
    press("c")
    release("c")
    release(Key.cmd)
    text = clipboard.paste()
    return text

def return_text(text):
    clipboard.copy(text)
    wait()
    press(Key.cmd)
    press("a")
    release("a")
    press("v")
    release(Key.cmd)
    release("v")

def next_text():
    press(Key.down)
    wait()
    release(Key.down)


def on_press(key):
    if DEBUG:
        print("Pressed " + str(key))
    try:
        if key in hotkeys:
            current.add(key)

            if all(k in current for k in CTRLQ):
                text = get_text()
                new_text = clean_text(text)
                return_text(new_text)

            elif all(k in current for k in CTRLA):
                start_check()

            elif all(k in current for k in CTRL1):
                text = get_text()
                text = " ".join([words.strip() for words in text.split("\n") if words])
                return_text(text)

            elif all(k in current for k in CTRL2):
                text = get_text()
                text = split_words(text.replace("\n", " "))
                return_text(text)

            elif all(k in current for k in CTRL3):
                text = get_text()
                return_text(text.lower())

            elif all(k in current for k in CTRL4):
                text = get_text()
                return_text(text.upper())

            elif all(k in current for k in CTRLRETURN):
                listener.stop()
                exit()

    except Exception as e:
        print(e)

def on_release(key):
    try:
        current.remove(key)
    except KeyError:
        pass





if __name__ == "__main__":
    print("---".join(["-" for _ in range(20)]))
    print("Welcome to Lesan Helper version 1.4"
          "\n\n<Controls>"
          "\nCtrl + Q: Clean current textbox selected"
          "\nCtrl + A: Clean all textboxes (box 1 must be selected first)"
          "\n          To end process click anywhere outside the textbox"
          "\nCtrl + 1: Merges current text into 1 line"
          "\nCtrl + 2: Splits current text into 2 even lines"
          "\nCtrl + 3: Turns current text into lower case"
          "\nCtrl + 4: Turns current text into UPPER case"
          "\nCtrl + Return: Quit application"
          "\n\n*note - Controls not responsive if many inputs are given in a row"
          "\n\n<Settings>"
          "\nMAX_LEN: Maximum horizontal length of line before splitting into 2"
          "\n         For reference - 1080x1080 SQ video is ~600 units"
          "\nDEBUG: Set to 'True' to see detailed log"
          "\nDELAY: Delay (in seconds) between each action"
          "\n       Set below 0.05 at your own risk")
    print("---".join(["-" for _ in range(20)]))

    print("Current settings:\nDEBUG-{}\nMAX_LEN-{}\nDELAY-{}".format(DEBUG, MAX_LEN, DELAY))


    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()

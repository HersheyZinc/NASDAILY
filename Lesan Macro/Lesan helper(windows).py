
from pynput import keyboard
import clipboard
import time
from PIL import ImageFont
import os, sys


# The key combination to check
'''CTRLQ = {keyboard.Key.alt_l, keyboard.Key.ctrl_l, keyboard.KeyCode.from_char('q')} # q
CTRLA = {keyboard.Key.alt_l, keyboard.Key.ctrl_l, keyboard.KeyCode.from_char('a')} # a
CTRL1 = {keyboard.Key.alt_l, keyboard.Key.ctrl_l, keyboard.KeyCode.from_char('1')} # 1
CTRL2 = {keyboard.Key.alt_l, keyboard.Key.ctrl_l, keyboard.KeyCode.from_char('2')} # 2
CTRL3 = {keyboard.Key.alt_l, keyboard.Key.ctrl_l, keyboard.KeyCode.from_char('3')} # 2
CTRL4 = {keyboard.Key.alt_l, keyboard.Key.ctrl_l, keyboard.KeyCode.from_char('4')} # 2
CTRLRETURN = {keyboard.Key.alt_l, keyboard.Key.ctrl_l, keyboard.Key.enter} # return
hotkeys = CTRLQ.union(CTRLA).union(CTRLRETURN).union(CTRL1).union(CTRL2).union(CTRL3).union(CTRL4)'''

# The currently active modifiers
current = set()
control = keyboard.Controller()
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
        font = ImageFont.truetype("arial.ttf", 36)

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
        if ignore_max_len:
            return text
        return split_words(text, font, True)
    text = " ".join(words[:best_split]) + "\n" + " ".join(words[best_split:])
    return text

def clean_text(text):
    if (text.endswith(".") or text.endswith(",")) and not text.endswith("..."):
        text = text[:-1]

    font = ImageFont.truetype("arial.ttf", 36)
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
        control.release("a")
        return
    elif len(text) > 1000:
        print("Process interrupted and ended prematurely")
        print(len(text))
        control.release("a")
        return
    if text == last1 and text == last2 and text == last3:
        print("Process ended naturally")
        control.release("a")
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
    if DEBUG:
        print("Getting text")
    with control.pressed(keyboard.Key.ctrl_l):
        control.release(keyboard.Key.shift)
        control.release(keyboard.Key.alt)
        press("a")
        release("a")
        press("c")
        release("c")
    text = clipboard.paste()
    return text

def return_text(text):
    if DEBUG:
        print("Pasting text")
    clipboard.copy(text)
    wait()
    with control.pressed(keyboard.Key.ctrl_l):
        control.release(keyboard.Key.shift)
        press("a")
        release("a")
    control.type(text)

def next_text():
    press(keyboard.Key.down)
    wait()
    release(keyboard.Key.down)

def check_current():
    text = get_text()
    new_text = clean_text(text)
    return_text(new_text)
    control.release('q')

def one_line():
    text = get_text()
    text = " ".join([words.strip() for words in text.split("\n") if words])
    return_text(text)
    control.release("1")

def two_line():
    text = get_text()
    text = split_words(text.replace("\n", " "))
    return_text(text)
    control.release("2")

def upper_text():
    text = get_text()
    return_text(text.upper())
    control.release("4")


def lower_text():
    text = get_text()
    return_text(text.lower())
    control.release("3")



if __name__ == "__main__":
    print("---".join(["-" for _ in range(20)]))
    print("Welcome to Lesan Helper version 1.4"
          "\n\n<Controls>"
          "\nCtrl Alt + Q: Clean current textbox selected"
          "\nCtrl Alt + A: Clean all textboxes (box 1 must be selected first)"
          "\n          To end process click anywhere outside the textbox"
          "\nCtrl Alt + 1: Merges current text into 1 line"
          "\nCtrl Alt + 2: Splits current text into 2 even lines"
          "\nCtrl Alt + 3: Turns current text into lower case"
          "\nCtrl Alt + 3: Turns current text into UPPER case"
          "\n\n*note - Need to release and press Ctrl Alt after every hotkey"
          "\n\n<Settings>"
          "\nMAX_LEN: Maximum horizontal length of line before splitting into 2"
          "\n         For reference - 1080x1080 SQ video is ~600 units"
          "\nDEBUG: Set to 'True' to see detailed log"
          "\nDELAY: Delay (in seconds) between each action"
          "\n       Set below 0.05 at your own risk")
    print("---".join(["-" for _ in range(20)]))

    print("Current settings:\nDEBUG-{}\nMAX_LEN-{}\nDELAY-{}".format(DEBUG, MAX_LEN, DELAY))

    with keyboard.GlobalHotKeys({
        '<ctrl>+<alt>+a': start_check,
        '<ctrl>+<alt>+q': check_current,
        '<ctrl>+<alt>+1': one_line,
        '<ctrl>+<alt>+2': two_line,
        '<ctrl>+<alt>+3': lower_text,
        '<ctrl>+<alt>+4': upper_text}) as h:
        h.join()


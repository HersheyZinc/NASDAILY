from datetime import datetime
from tkinter import messagebox
import random
import cv2 as cv
import os
from playsound import playsound

def generic_process(misc, main):
    os.chdir(misc)
    hours = datetime.now().strftime("%H")
    if int(hours) < 10 or int(hours) > 18:
        if int(hours) < 10:
            img = cv.imread("T2stop2.jpeg")
            msg = "It's only {} AM, go back to sleep!".format(str(int(hours)))
        else:
            img = cv.imread("T2stop.jpeg")
            msg = "It's already {} PM, go home".format(str(int(hours)))
        cv.imshow(msg, img)
        cv.waitKey()
        cv.destroyAllWindows()
        return False

    rng = random.randint(0,100)
    cursor_list = ["star", "man", "mouse", "spider", "heart"]
    quotes = ["There are more planes in the sea than submarines in the sky!",
              "People die when they are killed",
              "Nas means people in arabic",
              "100% of people who drink water die",
              "Fugu poison is 1200 times more toxic than the regular poison"
              ]

    if rng == 1 or rng == 2:
        i = random.randint(0, len(cursor_list)-1)
        main.config(cursor=cursor_list[i])

    elif rng == 3 or rng == 4:
        i = random.randint(0, len(quotes)-1)
        messagebox.showinfo(message=quotes[i])

    elif rng == 69:
        i = random.randint(0,6)
        img = cv.imread(str(i).join(["M", ".jpeg"]))
        msg = "A wild meme appeared!"
        cv.imshow(msg, img)
        cv.waitKey()
        cv.destroyAllWindows()

    elif rng == 42:
        return True

    return False

def music(MISC):
    print('Never gonna give you up'
    '\nNever gonna let you down'
    '\nNever gonna run around and desert you'
    '\nNever gonna make you cry'
    '\nNever gonna say goodbye'
    '\nNever gonna tell a lie and hurt you')
    playsound(MISC + "/RR.mp3")









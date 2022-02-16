from tkinter import *
from PIL import ImageFont, Image, ImageDraw
import os
import sys
from arabic_reshaper import ArabicReshaper
from bidi.algorithm import get_display
from tkinter import messagebox

def start_up():
    application_path = os.path.dirname(sys.argv[0])
    global INPUT
    global OUTPUT
    global TN
    global FONTS
    INPUT = application_path + "/Input"
    OUTPUT = application_path + "/Output"
    TN = application_path + "/Clean Thumbnail"
    FONTS = application_path + "/py_fonts/"


    if not os.path.exists(INPUT):
        os.mkdir(INPUT)
        print("New directory created: {}".format(INPUT))
    if not os.path.exists(OUTPUT):
        os.mkdir(OUTPUT)
        print("New directory created: {}".format(OUTPUT))

def find_files(name):
    for root, dirs, files in os.walk(TN):
        for file in files:
            if file.endswith(".jpg") or file.endswith(".jpeg"):
                if name.lower()+"_" in file.lower():
                    print("Found {} in directory {}".format(file, root))
                    return os.path.join(root, file)
        for file in files:
            if file.endswith(".jpg") or file.endswith(".jpeg"):
                if name.lower() in file.lower():
                    print("Found {} in directory {}".format(file, root))
                    return os.path.join(root, file)
    return False

def create_tn(name, text, lan, config, x_change=0, y_change=0, spacing_change=0, padx=30, pady=30, opac=70):
    try: x_change = int(x_change)
    except: x_change = 0
    try: y_change = int(y_change)
    except: y_change = 0
    try: spacing_change = int(spacing_change)
    except: spacing_change = 0
    try: padx = int(padx)
    except: padx = 30
    try: pady = int(pady)
    except: pady = 30
    try: opac = int(opac)
    except: opac = 70

    if not lan:
        lan = "en"
    else:
        lan = lan.strip().lower()

    if not name:
        messagebox.showerror("Error", "No video name given")
        return
    else:
        name = name.strip()

    if not text:
        messagebox.showerror("Error", "No title given")
        return
    dir = find_files(name)
    if not dir:
        messagebox.showerror("Error", "JPG of {} not found".format(name))
        return

    font_type, index = "Avenir Next.ttc", 0
    no_ascents = False
    if lan == 'ur':

        # font_type, index = "Jameel Noori Nastaleeq Regular.ttf", 0
        font_type, index = 'jameel-unicode-regular-1.ttf', 0
        urdu_reshape = ArabicReshaper(configuration={'language': "Urdu", "delete_harakat": False, "support_ligatures": True, "use_unshaped_instead_of_isolated":True})
        # urdu_reshape = ArabicReshaper(configuration={"language":"Urdu"})
        text = urdu_reshape.reshape(text)
        text = get_display(text)


    elif lan == "ar":
        font_type, index = "GeezaPro.ttc", 1
        arabic_reshape = ArabicReshaper(configuration={'language': "Arabic", "delete_harakat": False})
        text = arabic_reshape.reshape(text)
        text = get_display(text)

    elif lan == "th":
        # font_type, index = "Ayuthaya.ttf", 0
        font_type, index = "Tahoma Bold.ttf", 0
        # font_type = "Arial Unicode MS Bold.ttf"
        no_ascents = True

    elif lan == "he":
        # font_type, index = "ArialHB.ttc", 1
        # font_type, index = "Tahoma Bold.ttf", 0
        font_type, index = "LucidaGrande.ttc", 1
        text = get_display(text)
        no_ascents = True

    elif lan == "tw":
        font_type, index = "PingFang.ttc", 5
        # no_ascents = True
    elif lan == "cn":
        font_type, index = "PingFang.ttc", 4
        # no_ascents = True

    else:
        text = text.upper()

    img = Image.open(dir)
    width, height = img.size
    true_width = width - padx*2
    min_diff = 42069
    final_size = 200
    draw = ImageDraw.Draw(img, "RGBA")
    print(font_type)
    for font_size in range(10, 350, 1):
        font = ImageFont.truetype(FONTS + font_type, font_size, index=index)
        l, h = draw.textsize(text, font, stroke_width=4)
        if l > width:
            break
        elif h > height/3.5:
            break
        if abs(l-true_width) < min_diff:
            min_diff = abs(l-true_width)
            final_size = font_size

    font = ImageFont.truetype(FONTS + font_type, final_size, index=index)
    (length, baseline), (offset_x, offset_y) = font.font.getsize(text)
    ascent, descent = font.getmetrics()
    l, h = draw.textsize(text, font, stroke_width=4)

    del draw

    spacing = descent + offset_y + spacing_change
    if all(ord(c) < 128 for c in text) or no_ascents:
        spacing = 0
    h += spacing*text.count("\n")
    rect_height = pady*2 + h
    if height > width:
        min_height = height/7
    else:
        min_height = height/5
    rect_height = max(min_height, rect_height)

    x = (width - l) / 2 + x_change
    y = (rect_height - h) / 2 - offset_y / 2 - y_change
    if config == "Top":
        x1, y1 = 0, 0
        x2, y2 = width, rect_height
    else:
        y += (height-rect_height)
        x1, y1 = 0, height
        x2, y2 = width, height - rect_height

    opacity = int(opac/100 * 255)


    draw = ImageDraw.Draw(img, "RGBA")
    draw.rectangle([x1, y1, x2, y2], fill=(0, 0, 0, opacity))
    del draw
    '''draw = ImageDraw.Draw(img)
    draw.line((0, y, width, y), fill=0, width=5)
    draw.line((0, y+offset_y, width, y+offset_y), fill=0, width=5)
    draw.line((0, y+h, width, y+h), fill=0, width=5)
    del draw'''

    draw = ImageDraw.Draw(img)
    draw.text((x, y), text, (255,255,255), font=font, stroke_width=4, stroke_fill=(0,0,0), align="center", spacing=spacing)

    os.chdir(OUTPUT)
    save_name = name+"-"+lan.upper()+"_TN.jpg"
    img.save(save_name)
    img.show(title="title")

def clear_val(name, title, lan, x, y, spacing, padx, pady, opac):
    name.set("")
    title.delete("1.0", END)
    lan.set("")
    x.set("0")
    y.set("0")
    spacing.set("0")
    padx.set("30")
    pady.set("30")
    opac.set("69")
    print("Hippity Hoppity")
    print("Your text is now my property")

def compress_text(textbox):
    text = textbox.get("1.0", 'end-1c')
    text = text.replace("\n", " ").replace("  ", " ").strip()
    textbox.delete(1.0, "end")
    textbox.insert(1.0, text)

def expand_text(textbox):
    text = textbox.get("1.0", 'end-1c')
    lines = text.split("\n")
    text = " ".join([l.strip() for l in lines if l])
    words = [word for word in text.split(" ") if word]
    best_split = 0
    min_diff = 42069
    font = ImageFont.truetype(FONTS + "Arial.ttf", 36)

    for x in range(len(words)):
        start = " ".join(words[:x])
        end = " ".join(words[x:])
        len_start = font.getsize(start)[0]
        len_end = font.getsize(end)[0]
        diff = len_start - len_end
        if abs(diff) < min_diff:
            if diff < 100:
                min_diff = abs(diff)
                best_split = x
    text = " ".join(words[:best_split]) + "\n" + " ".join(words[best_split:])
    textbox.delete(1.0, "end")
    textbox.insert(1.0, text)

if __name__ == "__main__":
    start_up()
    main = Tk()
    main.title("MAIN MENU")
    main.geometry("750x300")
    test = [["المحامي الذي يعيش في حفرة", 'ar'], ['El abogado que vive en\n un agujero en el suelo', 'es'], ['עורך הדין שגר בבור', 'he'],
            ['VỊ LUẬT SƯ SỐNG TRONG HANG', 'vn'], ['La ciudad más \nvisitada del mundo', 'es'], ["全世界最多旅客的城市", 'cn'],
            ['ชายชาวอาหรับกับรถยนต์ 3,000 คันของเขา', 'th'],['ชายชาวอาหรับกับรถยนต์', 'th'], ["Filin jirgin sama da\n ya kamata ka sani",'ha']]
    test = test + [[u"کیوں میں سنگاپور سے نفرت کرتا ہوں !", 'ur'], ['ایسٹونیا میں خواتین کی طرف سے بنا ایک جزیرہ', 'ur'], ['وہ 1 ملین سگریٹ کا مالک ہے', 'ur']]
    for i in test:
        if False:
            create_tn("shorts 11", i[0], i[1], "Top")
    frame = Frame(main)
    frame.pack()
    Label(frame, text="Video Name", width=25).grid(row=0, column=0)
    Label(frame, text="Language Code", width=15).grid(row=0, column=1)
    Label(frame, text="Configuration", width=10).grid(row=0, column=2)
    Label(frame, text="Title").grid(row=3, column=0, columnspan=3)
    name = StringVar()
    lan = StringVar()
    config = StringVar(value="Top")
    options = ["Top", "Bottom"]
    Entry(frame, textvariable=name).grid(row=1, column=0, sticky="ew")
    Entry(frame, textvariable=lan).grid(row=1, column=1, sticky="ew")
    OptionMenu(frame, config, *options).grid(row=1, column=2, sticky="ew")
    title = Text(frame, height=2)
    title.grid(row=4, column=0, columnspan=3)
    sub_frame = Frame(frame)
    sub_frame.grid(row=5, column=0, columnspan=3)
    Button(sub_frame, text="1 line", command=lambda: compress_text(title)).pack(side=LEFT)
    Button(sub_frame, text="2 line", command=lambda: expand_text(title)).pack(side=RIGHT)

    frame = Frame(main)
    frame.pack()
    Label(frame, text='x').grid(row=0, column=0)
    Label(frame, text='y').grid(row=0, column=1)
    Label(frame, text='spacing').grid(row=0, column=2)
    x, y, spacing = StringVar(value="0"), StringVar(value="0"), StringVar(value="0")

    Entry(frame, textvariable=x).grid(row=1,column=0)
    Entry(frame, textvariable=y).grid(row=1, column=1)
    Entry(frame, textvariable=spacing).grid(row=1, column=2)

    Label(frame, text='pad-x').grid(row=2, column=0)
    Label(frame, text='pad-y').grid(row=2, column=1)
    Label(frame, text='bg opacity').grid(row=2, column=2)
    padx, pady, opac = StringVar(value="30"), StringVar(value="30"), StringVar(value="70")
    Entry(frame, textvariable=padx).grid(row=3, column=0)
    Entry(frame, textvariable=pady).grid(row=3, column=1)
    Entry(frame, textvariable=opac).grid(row=3, column=2)

    configurations = [x, y, spacing, padx, pady, opac]


    frame = Frame(main)
    frame.pack()
    Button(frame, text="Magic Trick", command=lambda: clear_val(name, title, lan, x, y, spacing, padx, pady, opac)).pack(side=LEFT)
    Button(frame, text="Create Thumbnail", command=lambda: create_tn(name.get(), title.get("1.0", 'end-1c'), lan.get(),
                                                                     config.get(), x.get(), y.get().strip(),
                                                                     spacing.get(), padx.get(), pady.get(),
                                                                     opac.get())).pack(side=RIGHT)
    main.mainloop()
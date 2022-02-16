from tkinter import *
from tkinter import filedialog
import glob
import os
import sys
import SRT_handler as SRT
import FCP_handler as FCP
import MP4_handler as MP4
import EXE_handler as EXE

def get_input(message=""):

    msg = Toplevel()
    msg.title("Configure settings")
    msg.geometry(center_coords(msg, 200, 300))

    text = StringVar(value=message)
    Entry(msg, textvariable=text).pack()
    Button(msg, text="Confirm", command=msg.destroy).pack(pady=10)
    msg.bind('<Return>', lambda e: msg.destroy())

    msg.wait_window()
    return text.get()


def center_coords(window, h, w):
    ws = window.winfo_screenwidth()  # width of the screen
    hs = window.winfo_screenheight()  # height of the screen

    x = (ws / 2) - (w / 2)
    y = (hs / 2) - (h / 2)
    output = '%dx%d+%d+%d' % (w, h, x, y)
    return output


def show_report(logs):
    result = ("\n" + "--".join(["-" for _ in range(20)]) + "\n").join(["\n".join(log) for log in logs])
    report = Toplevel()
    report.title("Report")
    report.geometry(center_coords(report, 500, 440))
    box = Frame(report, height=34)
    box.pack()
    scrollbar = Scrollbar(box)
    scrollbar.pack(side=RIGHT, fill=Y)
    text = Text(box, height=33, yscrollcommand=scrollbar.set)
    text.pack()
    text.insert(END, result)
    scrollbar.config(command=text.yview)
    Button(report, text="OK", command=report.destroy).pack(pady=10)


def clean_subs_select():

    config = Toplevel()
    config.title("Configure settings")
    config.geometry(center_coords(config, 225, 450))
    punctuation = BooleanVar()
    merge = BooleanVar()
    split_lines_bool = BooleanVar()
    close_gap_bool = BooleanVar()
    max_diff_bool = BooleanVar()

    lf = LabelFrame(config)
    lf.pack(fill="x", padx=5, pady=(5, 2))
    Checkbutton(lf, text='Remove any <.> or <,> at the end of each subtitle', variable=punctuation).pack(side=LEFT)

    lf = LabelFrame(config,)
    lf.pack(fill="x", padx=5, pady=2)
    Checkbutton(lf, text='Merge subtitles that are longer than 1 line', var=merge).pack(side=LEFT)

    lf = LabelFrame(config)
    lf.pack(fill="x", padx=5, pady=2)
    Checkbutton(lf, text='Splits line into 2 if more than ', var=split_lines_bool).pack(side=LEFT)
    split_lines = Spinbox(lf, from_=610, to=1080, width=5)
    split_lines.pack(side=LEFT)
    Label(lf, text=" unit lengths long").pack(side=LEFT)

    lf = LabelFrame(config)
    lf.pack(fill="x", padx=5, pady=2)
    Checkbutton(lf, text='Snaps timecodes to shot changes less than', variable=max_diff_bool).pack(side=LEFT)
    max_diff = Spinbox(lf, from_=1, to=5, width=5)
    max_diff.pack(side=LEFT)
    Label(lf, text=" seconds").pack(side=LEFT)

    lf = LabelFrame(config)
    lf.pack(fill="x", padx=5, pady=2)
    Checkbutton(lf, text='Closes any gaps less than', var=close_gap_bool).pack(side=LEFT)
    close_gap = Spinbox(lf, from_=1, to=5, width=5)
    close_gap.pack(side=LEFT)
    Label(lf, text=" seconds between subtitles").pack(side=LEFT)

    Button(config, text="Start", command=lambda: clean_subs(punctuation.get(), merge.get(), close_gap_bool.get(),
                                                            split_lines_bool.get(), int(close_gap.get()),
                                                            int(split_lines.get()), max_diff_bool.get(),
                                                            max_diff.get(), config)).pack(pady=10)


def clean_subs(punctuation, merge, close_gap_bool, split_lines_bool,
               close_gap, split_lines,max_diff_bool, max_diff, config):
    config.destroy()
    title = "Select SRTs to clean"
    filetypes = [("SRTs", ".srt")]
    files = filedialog.askopenfilenames(title=title, filetypes=filetypes, initialdir=INPUT)
    if not files:
        return
    logs = []
    if not close_gap_bool:
        close_gap = 0
    else:
        close_gap *= 1000
    if not split_lines_bool:
        split_lines = 0
    if not max_diff_bool:
        max_diff = 0
        scenes = None
    else:
        title = "Select MP4"
        filetypes = [("MP4", ".mp4")]
        mp4 = filedialog.askopenfilename(title=title, filetypes=filetypes, initialdir=INPUT)
        if not mp4:
            return

        fps, width, height = MP4.check_attributes(mp4)
        print(str(fps) + "fps")
        splits = MP4.find_scenes(mp4)
        scenes = [scene[1].get_frames() for scene in splits]
        scenes = [round(frame / fps, 2) for frame in scenes]

    for file in files:

        log = SRT.clean_subs(file, OUTPUT, punctuation, merge, close_gap, split_lines, float(max_diff), scenes)
        logs.append(log)

    show_report(logs)


def compare_srt_select():
    title = "Select SRT for the base"
    filetypes = [("SRTs", ".srt")]
    base = filedialog.askopenfilename(title=title, filetypes=filetypes, initialdir=INPUT)
    if not base:
        return
    title = "Select SRT(s) to check/conform"
    filetypes = [("SRTs", ".srt")]
    files = filedialog.askopenfilenames(title=title, filetypes=filetypes, initialdir=INPUT)
    if not files:
        return
    config = Toplevel()
    config.title("Configure settings")
    config.geometry(center_coords(config, 150, 175))
    var1 = IntVar(value=0)
    conform = BooleanVar()

    lf = LabelFrame(config)
    lf.pack(fill="x", padx=5, pady=2)
    Radiobutton(lf, text="Check timecode", variable=var1, value=0).pack(side=LEFT)
    lf = LabelFrame(config)
    lf.pack(fill="x", padx=5, pady=2)
    Radiobutton(lf, text="Check text", variable=var1, value=1).pack(side=LEFT)
    lf = LabelFrame(config)
    lf.pack(fill="x", padx=5, pady=2)
    Checkbutton(lf, text="Conform SRT", variable=conform).pack(side=LEFT)

    Button(config, text="Start", command=lambda: compare_srt(config, files, base, var1.get(),
                                                             conform.get())).pack(pady=10)


def compare_srt(config, files, base, var1, conform):
    config.destroy()
    logs = []
    if var1 == 0:
        c_time, c_text = True, False
    else:
        c_time, c_text = False, True

    for file in files:
        log = SRT.compare_srt(file, base, c_time, c_text, conform, OUTPUT)
        logs.append(log)

    show_report(logs)


def extract_captions_select():
    title = "Select SRT(s) to extract subtitles"
    filetypes = [("SRTs", ".srt")]
    files = filedialog.askopenfilenames(title=title, filetypes=filetypes, initialdir=INPUT)
    if not files:
        return

    config = Toplevel()
    config.title("Configure settings")
    config.geometry(center_coords(config, 125, 300))
    separate = BooleanVar()
    merge = BooleanVar()

    lf = LabelFrame(config)
    lf.pack(fill="x", padx=5, pady=(5, 2))
    Checkbutton(lf, text='Separate subtitles into individual lines', variable=separate).pack(side=LEFT)

    lf = LabelFrame(config)
    lf.pack(fill="x", padx=5, pady=2)
    Checkbutton(lf, text='Merge subtitles that have more than 1 line', var=merge).pack(side=LEFT)

    Button(config, text="Start",
           command=lambda: extract_captions(files, separate.get(), merge.get(), config)).pack(pady=10)


def extract_captions(files, separate, merge_lines, config):
    config.destroy()
    logs = []
    for file in files:
        log = SRT.extract_subs(file, OUTPUT, separate, merge_lines)
        logs.append(log)

    show_report(logs)


def extract_SRT():
    title = "Select FCPXML(s) to extract subtitles"
    filetypes = [("FCPXML", ".fcpxml")]
    files = filedialog.askopenfilenames(title=title, filetypes=filetypes, initialdir=INPUT)
    if not files:
        return
    logs = []
    for file in files:
        log = FCP.extract_srt(file, OUTPUT)
        logs.append(log)

    show_report(logs)


def simplify_chinese():
    title = "Select traditional chinese SRT(s) to simplify"
    filetypes = [("SRTs", ".srt")]
    files = filedialog.askopenfilenames(title=title, filetypes=filetypes, initialdir=INPUT)
    if not files:
        return
    logs = []
    for file in files:
        log = SRT.simplify_chinese(file, OUTPUT)
        logs.append(log)

    show_report(logs)


def check_video_select():

    config = Toplevel()
    config.title("Configure settings")
    config.geometry(center_coords(config, 375, 275))
    view_title1 = BooleanVar(value=True)
    view_title2 = BooleanVar()
    check_subs1 = BooleanVar(value=True)
    check_subs2 = BooleanVar(value=True)
    check_subs3 = BooleanVar(value=True)
    check_blinks = BooleanVar()
    check_border = BooleanVar()
    guidelines = BooleanVar()
    bulk_check = BooleanVar()
    scale_var = StringVar(value='50')


    lf = LabelFrame(config)
    lf.pack(fill="x", padx=5, pady=(5, 2))
    Checkbutton(lf, text='View titles - first frame', variable=view_title1).pack(side=LEFT)

    lf = LabelFrame(config)
    lf.pack(fill="x", padx=5, pady=2)
    Checkbutton(lf, text='View titles - last frame', var=view_title2).pack(side=LEFT)

    lf = LabelFrame(config)
    lf.pack(fill="x", padx=5, pady=2)
    Checkbutton(lf, text='Checks if subtitles are within frame', var=check_subs1).pack(side=LEFT)

    lf = LabelFrame(config)
    lf.pack(fill="x", padx=5, pady=2)
    Checkbutton(lf, text='Checks if subtitles match SRT timing', var=check_subs2).pack(side=LEFT)

    lf = LabelFrame(config)
    lf.pack(fill="x", padx=5, pady=2)
    Checkbutton(lf, text='View subtitles - first frame', var=check_subs3).pack(side=LEFT)

    lf = LabelFrame(config)
    lf.pack(fill="x", padx=5, pady=2)
    Checkbutton(lf, text='Checks for blinks(ignores SRT)', var=check_blinks).pack(side=LEFT)

    lf = LabelFrame(config)
    lf.pack(fill="x", padx=5, pady=2)
    Checkbutton(lf, text='Checks for black borders at the sides', var=check_border).pack(side=LEFT)

    lf = LabelFrame(config)
    lf.pack(fill="x", padx=5, pady=2)
    Checkbutton(lf, text='View frame with center markings', var=guidelines).pack(side=LEFT)

    lf = LabelFrame(config)
    lf.pack(fill="x", padx=5, pady=2)
    Checkbutton(lf, text='Check videos in bulk', var=bulk_check).pack(side=LEFT)

    lf = LabelFrame(config)
    lf.pack(fill="x", padx=5, pady=2)
    Label(lf, text="Preview scale %:").pack(side=LEFT)
    scale = Spinbox(lf, from_=25, to=125, increment=25)
    scale.pack(side=LEFT)

    Button(config, text="Start",
           command=lambda: check_video(config, view_title1.get(), view_title2.get(), check_subs1.get(),
                                       check_subs2.get(), check_subs3.get(),
                                       check_blinks.get(), check_border.get(),
                                       guidelines.get(), bulk_check.get(), int(scale.get()))).pack(pady=10)


def check_video(config, title1, title2, subs1, subs2, subs3, blink, border, guidelines, bulk_check, scale):
    config.destroy()
    to_check = {}
    logs = []
    if bulk_check:
        os.chdir(INPUT)
        extension = "*.srt"
        srt_list = [".".join(name.split(".")[:-1]) for name in glob.glob(extension)]
        print("{} SRTs found: {}\n".format(len(srt_list), srt_list))
        for name in srt_list:
            extension = "*.mp4"
            video_list = [os.path.join(INPUT, mp4) for mp4 in glob.glob(extension) if mp4.startswith(name)]
            if video_list:
                to_check[os.path.join(INPUT, name+".srt")] = video_list
    else:
        title = "Select MP4(s) to check"
        filetypes = [("MP4", ".mp4")]
        video_list = filedialog.askopenfilenames(title=title, filetypes=filetypes, initialdir=INPUT)
        if not video_list:
            return

        filetypes = [("SRTs", ".srt")]
        title = "Select SRT for videos selected"
        srt = filedialog.askopenfilename(title=title, filetypes=filetypes, initialdir=INPUT)
        if not srt:
            return
        to_check[srt] = video_list

    configs = {"title1": title1, "title2": title2, "subs1": subs1, "subs2": subs2,
               "subs3": subs3, "blink": blink, "borders": border, "guidelines": guidelines}

    report_list = []
    for srt in to_check:
        _, srt_name = os.path.split(srt)
        print("\n\nChecking videos for {}\n".format(srt_name))
        videos = to_check[srt]
        video_names = [os.path.split(vid)[1] for vid in videos]

        fps, width, height = MP4.check_attributes(videos[0])
        log, titles, subtitles = SRT.find_titles(srt, fps)

        if not titles and not subtitles:
            logs.append(log)
            show_report(logs)
            return

        if blink:
            splits = MP4.find_scenes(videos[0])
            scenes = [scene[1].get_frames() - 1 for scene in splits]
        else:
            scenes = []

        log = list()
        log.append("In {}, found {} videos:".format(srt_name, str(len(video_names))))
        log.append("  |  ".join(video_names) + "\n")
        for video in videos:
            _, name = os.path.split(video)
            print("Checking {}...".format(name))
            try:
                vid = MP4.Video(video, scenes, titles, subtitles, configs, fps, OUTPUT, scale)
                report_list.append(vid)
                print("Check completed!")

            except Exception as e:
                print("ERROR - could not check {}:".format(name))
                print(e)

        logs.append(log)
    print("\nVideo frames are ready to be checked!")
    log = []
    for vid in report_list:

        try:
            vid.check_video()
            log.append("Checked {} - Success".format(vid.file))
            del vid
        except Exception as e:
            print("ERROR- could not be checked\n{}".format(e))
            log.append("Checked {} - FAIL".format(vid.file))
    logs.append(log)
    show_report(logs)

def create_xml():
    filetypes = [("SRTs", ".srt")]
    title = "Select SRTs"
    files = filedialog.askopenfilenames(title=title, filetypes=filetypes, initialdir=INPUT)
    if not files:
        return

    log = []
    for file in files:
        name = file.split('/')[-1]
        try:
            FCP.create_xml(file, INPUT, OUTPUT, MISC+"/TEMPLATE.fcpxml")
            log.append("{} was successfully converted to FCPXML".format(name))
        except Exception as e:
            print("ERROR- could not be converted:\n{}".format(e))
            log.append("Checked {} - FAIL".format(name))

    show_report([log])



def start_up():
    application_path = os.path.dirname(sys.argv[0])
    global INPUT
    global OUTPUT
    global MISC
    INPUT = application_path + "/Input"
    OUTPUT = application_path + "/Output"
    MISC = application_path + "/Misc"

    if not os.path.exists(INPUT):
        os.mkdir(INPUT)
        print("New directory created: {}".format(INPUT))
    if not os.path.exists(OUTPUT):
        os.mkdir(OUTPUT)
        print("New directory created: {}".format(OUTPUT))


if __name__ == "__main__":
    print("Welcome to Coriander 2.1!")
    print("Created by Zhe Xun")
    print("Lark me for customer support!")
    start_up()
    main = Tk()
    main.title("MAIN MENU")

    button = Button(main, text="Clean subtitles", width=30, height=10, command=clean_subs_select)
    button.grid(row=0, column=0, padx=(3, 0))

    button = Button(main, text="Compare SRT", width=30, height=10, command=compare_srt_select)
    button.grid(row=0, column=1, padx=(0, 3))

    button = Button(main, text="Extract captions", width=30, height=10,  command=extract_captions_select)
    button.grid(row=1, column=0, padx=(3, 0))

    button = Button(main, text="Extract SRT", width=30, height=10,  command=extract_SRT)
    button.grid(row=1, column=1, padx=(0, 3))

    button = Button(main, text="Check Video", width=30, height=10, command=check_video_select)
    button.grid(row=2, column=0, padx=(3, 0))

    button = Button(main, text="Simplify Chinese", width=30, height=10,  command=simplify_chinese)
    button.grid(row=2, column=1, padx=(0, 3))

    button = Button(main, text="Create FCPXML", width=30, height=10, command=create_xml)
    button.grid(row=3, column=0, padx=(3, 0))

    button = Button(main, text="Musical button", width=30, height=10, command=lambda: EXE.music(MISC))
    button.grid(row=3, column=1, padx=(0, 3))

    s = EXE.generic_process(MISC, main)

    main.mainloop()


import xml.etree.ElementTree as ET
import os
from pathlib import Path
import glob
import pysrt

class Sub:
    def __init__(self, title, base_start=0, offset=0):
        self.text = "".join([s.text for s in title.find("text").findall("text-style")])
        if self.text.endswith(".") or self.text.endswith(","):
            if not self.text.endswith("..."):
                self.text = self.text[:-1]
        if "role" in title.attrib:
            if title.attrib["role"].startswith("BIG"):
                self.text = self.text.upper()
        self.start = Time(title.attrib["offset"]) + offset
        self.end = self.start + Time(title.attrib["duration"])
        # print(self.text, round(self.start,3), round(self.end,3))


def find_files(type="srt"):
    print(os.getcwd())
    extension = "*." + type
    os.chdir("Input")
    file_list = [file for file in glob.glob(extension)]
    print("{} files found with extension <{}>: {}\n".format(len(file_list), type, file_list))
    os.chdir("..")
    return file_list

def Time(timeString):
    vals = [float(n) for n in timeString.replace('s', '').split('/')]
    if len(vals) == 1:
        val = vals[0]
    else:
        val = vals[0]/vals[1]

    return val

def timestring(t, base=0.04):

    milliseconds = (t % 1) * 1000
    milliseconds = base * round(milliseconds/base)
    t = t // 1
    hours = t // 3600
    minutes = (t % 3600) // 60
    seconds = (t % 3600) % 60 // 1
    return {'hours': int(hours), "minutes": int(minutes), "seconds": int(seconds), "milliseconds": int(milliseconds)}


def extract_srt(file_dir, output):
    log = []

    try:
        os.chdir(Path(file_dir).parent.absolute())
        file = Path(file_dir).name
        log.append("Extracting SRT from {}".format(file))
        name = file.split(".")[0]
        tree = ET.parse(file)
        root = tree.getroot()
        subtitles = []
        spine = root.find("library").find("event").find("project").find("sequence").find("spine")
        asset_clips = spine.findall("asset-clip") + spine.findall("gap") + spine.findall("ref-clip")
        for asset_clip in asset_clips:
            total_length = Time(asset_clip.attrib["duration"])
            base_offset = asset_clip.attrib["offset"]
            main_subs = asset_clip.findall("title")
            trans_subs = asset_clip.findall("spine")
            base_start = 0
            if main_subs:
                base_start = Time(main_subs[0].attrib["start"])

            for title in main_subs:
                if not title.find("text") or "enabled" in title.attrib:
                    continue
                elif "role" in title.attrib:
                    if title.attrib["role"].lower().startswith("video"):
                        continue

                sub = Sub(title, base_start)
                subtitles.append(sub)

            for spine in trans_subs:
                offset = 0
                if "offset" in spine.attrib:
                    offset = Time(spine.attrib["offset"])
                for title in spine.findall("title"):
                    if not title.find("text") or "enabled" in title.attrib:
                        continue
                    elif "role" in title.attrib:
                        if title.attrib["role"].lower().startswith("video"):
                            continue
                    sub = Sub(title, base_start, offset)
                    subtitles.append(sub)

            format = root.find("resources").find("format")
            frame_duration = format.attrib["frameDuration"]

            frame_duration = round(Time(frame_duration), 3)
            print(frame_duration)

            for media in root.find("resources").findall("media"):
                if not media.find("sequence"):
                    continue
                for ref_clip in media.find("sequence").iter("ref-clip"):
                    titles = ref_clip.findall("title")
                    if titles:
                        log.append("Could not extract titles inside media clips:")
                        for title in titles:
                            log.append(" ".join([str(title.attrib["name"]), str(Time(title.attrib["offset"])), str(Time(title.attrib["start"]))]))

        srt = pysrt.SubRipFile([pysrt.SubRipItem(i + 1, start=timestring(sub.start, frame_duration), end=timestring(sub.end, frame_duration),
                                    text=sub.text) for i, sub in enumerate(subtitles)])

        if srt[0].start.hours != 0:
            offset = srt[0].start.hours
            for sub in srt:
                sub.start.hours -= offset
                sub.end.hours -= offset
        os.chdir(output)
        srt.save(name+".srt")
        log.append("SRT extracted successfully")

    except Exception as e:
        log.append("ERROR: could not process {} successfully\n{}".format(Path(file_dir).name, str(e)))

    return log



STYLES = {"big_title": {'font':"Gotham",'fontSize':"50", 'fontColor':"1 1 1 1", 'fontFace':"Medium", 'alignment':"center", "strokeColor":"0 0 0 1", "strokeWidth":"4", 'lineSpacing':"3"},
          "subtitle": {"font":"Seravek", "fontSize":"77", "fontFace":"Regular", "fontColor":"1 1 1 1", "shadowColor":"0 0 0 1", "shadowOffset":"5 315", "alignment":"center"}
}



class Title:
    def __init__(self, sub, subtitles, smart=True, role="BIG"):
        self.start = "3600s"
        self.text = sub.text.strip()
        self.offset, self.duration, self.end = self.fcp_time(sub)
        if len(sub.text) > 20:
            self.name = sub.text[:17] + "..."
        else:
            self.name = self.text

        self.style = "big_title"
        self.role = role + "." + role + "-1"
        self.position = "0 -140"

        self.start_time, self.end_time = self.to_seconds(sub.start), self.to_seconds(sub.end)
        self.lane = 1
        if subtitles:
            if self.start_time < subtitles[-1].end_time:
                self.lane = subtitles[-1].lane + 1
            if self.lane > 3:
                self.lane = 1


        self.attribs = {"offset":self.offset, "start":self.start, "duration":self.duration,
                        "name":self.name, "ref":"r4", "lane":str(self.lane), "role":self.role}

    def to_seconds(self, time):

        seconds = (time.hours * 60 + time.minutes) * 60 + time.seconds + time.milliseconds/1000

        return round(seconds, 2)

    def fcp_time(self, sub, fps=25):
        offset = self.to_seconds(sub.start)
        end = self.to_seconds(sub.end)
        duration = round(end - offset, 2)
        frame = fps*100
        s = str(frame).join(["/", "s"])

        offset = str(round(offset * frame)) + s
        end = str(round(end * frame)) + s
        duration = str(round(duration * frame)) + s

        # print(offset, duration, end)
        return offset, duration, end


def add_sub(tree, sub, style=STYLES, first=False):
    new_sub = ET.SubElement(tree, "title")
    param = ET.SubElement(new_sub, "param")
    param.set("name", "Position")
    param.set("key", "9999/999166631/999166633/1/100/101")
    param.set("value", sub.position)
    for attribute in sub.attribs:
        new_sub.set(attribute, sub.attribs[attribute])
    text = ET.SubElement(new_sub, "text")
    text_style = ET.SubElement(text, "text-style")
    text_style.set("ref", sub.style)
    text_style.text = sub.text

    if first:
        for style in STYLES:
            text_style_def = ET.SubElement(new_sub, "text-style-def")
            text_style_def.set("id", style)
            text_style = ET.SubElement(text_style_def, "text-style")
            for i in STYLES[style]:
                text_style.set(i, STYLES[style][i])

def create_xml(file, INPUT, OUTPUT, template):
    os.chdir(INPUT)
    name = Path(file).name.split(".")[0]
    role = name.split("-")[-1]
    subs = pysrt.open(file)
    titles = []
    for i, line in enumerate(subs):

        sub = Title(line, titles, role=role)
        titles.append(sub)
    tree = ET.parse(template)
    root = tree.getroot()
    project = root.find("library").find("event").find("project")
    project.set("name", name)
    project.find("sequence").set("duration", titles[-1].end)
    main = project.find("sequence").find("spine").find("title")
    main.set("duration", titles[-1].end)
    main.find('video').set("duration", titles[0].end)

    add_sub(main, titles[0], first=True)
    for sub in titles[1:]:
        add_sub(main, sub)


    os.chdir(OUTPUT)
    tree.write(name+".fcpxml")
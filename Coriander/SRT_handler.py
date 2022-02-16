import pysrt
import os
import glob
from pathlib import Path
import string
from math import ceil
from PIL import ImageFont
# import chinese_converter as converter
import hanzidentifier
from hanziconv import HanziConv

DEBUG = True


def find_files(type="srt"):
    extension = "*." + type
    os.chdir("Input")
    file_list = [file for file in glob.glob(extension)]
    print("{} files found with extension <{}>: {}\n".format(len(file_list), type, file_list))
    os.chdir("..")
    return file_list


def clean_subs(file_dir, output, punctuations=False, merge_lines=False, close_gap=0, split_lines=0, max_diff=0, scenes=None):
    log = []
    os.chdir(Path(file_dir).parent.absolute())
    file = Path(file_dir).name
    log.append("Cleaning {}...".format(file))
    try:
        subs = pysrt.open(file)
        if scenes:
            for i, line in enumerate(subs[:-1]):
                start = (line.start.hours * 60 + line.start.minutes) * 60 + line.start.seconds + line.start.milliseconds / 1000
                end = (line.end.hours * 60 + line.end.minutes) * 60 + line.end.seconds + line.end.milliseconds / 1000
                diff = end - start

                new_start, scenes = find_time(start, scenes, max_diff, min(diff, max_diff))
                # new_start, scenes = find_time(start, scenes, max_diff=max_diff)
                line.start.hours, line.start.minutes, line.start.seconds, line.start.milliseconds = srt_time(new_start)
                scenes.remove(new_start)

                new_end, scenes = find_time(end, scenes, min(diff, max_diff), max_diff)
                # new_end, scenes = find_time(end, scenes, max_diff=max_diff)
                line.end.hours, line.end.minutes, line.end.seconds, line.end.milliseconds = srt_time(new_end)

        for i, line in enumerate(subs[:-1]):
            line.text = line.text.strip()
            
            if not line.text:
                log.append("In line {}: Empty line".format(i + 1))
                continue

            if punctuations:
                if (line.text.endswith(".") or line.text.endswith(",")) and not line.text.endswith("..."):
                    line.text = line.text[:-1]
                    log.append("In line {}: punctuation was removed".format(i + 1))

            if merge_lines:
                if "\n" in line.text:
                    log.append("In line {}: Double lines found and merged".format(i + 1))
                lines = line.text.split("\n")
                line.text = " ".join([l.strip() for l in lines])

            if split_lines:
                font = ImageFont.truetype("arial.ttf", 36)
                if font.getsize(line.text)[0] > split_lines or '\n' in line.text:
                    log.append(str(split_lines))
                    log.append("In line {}: text was split into two lines".format(i + 1))
                    log.append("{}  -  length: {} units\n".format(line.text, font.getsize(line.text)[0]))
                    lines = line.text.split("\n")
                    line.text = " ".join([l.strip() for l in lines if l])
                    words = line.text.split(" ")
                    best_split, best_split2 = 0, 0
                    min_diff = 42069

                    for x in range(len(words)):
                        start = " ".join(words[:x])
                        end = " ".join(words[x:])
                        len_start = font.getsize(start)[0]
                        len_end = font.getsize(end)[0]

                        diff = len_start - len_end
                        if abs(diff) < min_diff:
                            if diff < 100:
                                min_diff = abs(diff)
                                if len_start > split_lines or len_end > split_lines:
                                    best_split2 = x
                                else:
                                    best_split = x
                    if best_split == 0:
                        best_split = best_split2
                    line.text = " ".join(words[:best_split]) + "\n" + " ".join(words[best_split:])


                '''if len(line.text) > split_lines:
                    words = line.text.split(" ")
                    best_split = int()
                    min_diff = 100
                    for x in range(len(words)):
                        start = "".join(words[:x])
                        end = "".join(words[x:])
                        if len(start) > len(end):
                            continue
                        if abs(len(start) - len(end)) < min_diff:
                            min_diff = abs(len(end) - len(start))
                            best_split = x
                    line.text = " ".join(words[:best_split]) + "\n" + " ".join(words[best_split:])'''


            if close_gap:
                nline = subs[i + 1]
                t1 = (line.end.minutes * 60 + line.end.seconds) * 1000 + line.end.milliseconds
                t2 = (nline.start.minutes * 60 + nline.start.seconds) * 1000 + nline.start.milliseconds
                if 0 < t2 - t1 < close_gap:
                    line.end = nline.start
                    log.append("In line {}: Closed gap of {} milliseconds to line {}".format(i + 1, t2 - t1, i + 2))
                if scenes and t1 - t2 > 0:
                    line.end = nline.start
                    log.append("In line {}: Removed overlap of {} milliseconds to line {}".format(i + 1, t2 - t1, i + 2))

        os.chdir(output)
        subs.save(file)
        log.append("{} cleaned successfully".format(file))

    except Exception as e:
        log.append("ERROR: could not process {} successfully\n{}".format(Path(file_dir).name, str(e)))

    return log


def find_titles(file_dir, frame_rate=25):
    log = []
    titles = []
    subtitles = []
    try:
        name = Path(file_dir).name
        log.append("Finding titles in {}...".format(name))
        os.chdir(Path(file_dir).parent.absolute())
        subs = pysrt.open(name)

        for num, sub in enumerate(subs):
            time = sub.start

            seconds = (time.hours * 60 + time.minutes) * 60 + time.seconds + time.milliseconds / 1000
            start_frame = ceil(round(seconds * frame_rate, 3))
            time = sub.end
            seconds = (time.hours * 60 + time.minutes) * 60 + time.seconds + time.milliseconds / 1000
            end_frame = ceil(round(seconds * frame_rate, 3)) - 1
            mid_frame = int((start_frame + end_frame) // 2)
            is_sub = False
            for i in sub.text.strip():
                if i.islower():
                    is_sub = True
            if is_sub:
                subtitles.append([start_frame, end_frame, mid_frame])
            else:
                titles.append([start_frame, end_frame, mid_frame])
                log.append("In line {}: Found title <{}>".format(num + 1, sub.text))

        return log, titles, subtitles

    except Exception as e:
        log.append("ERROR: could not process {} successfully\n{}".format(Path(file_dir).name, str(e)))
        return log, False, False


def extract_subs(file_dir, output, separate, merge_lines):
    log = []
    try:
        os.chdir(Path(file_dir).parent.absolute())
        file = Path(file_dir).name
        name = file.split(".")[0]
        log.append("Extracting captions from {}".format(file))
        subtitles = [sub.text for sub in pysrt.open(file)]
        if merge_lines:
            subtitles = [sub.replace("\n", " ") for sub in subtitles]
        if separate:
            subtitles = [sub + "\n" for sub in subtitles]
        else:
            subtitles = [sub + " " for sub in subtitles if sub[-1] not in string.punctuation]
        os.chdir(output)
        with open(name + "_subtitles.txt", "w") as f:
            f.writelines(subtitles)
        log.append("Captions extracted successfully")

    except Exception as e:
        log.append("ERROR: could not process {} successfully\n{}".format(Path(file_dir).name, str(e)))

    return log


def simplify_chinese(file_dir, output):
    log = []
    try:
        os.chdir(Path(file_dir).parent.absolute())
        file = Path(file_dir).name
        name = ".".join(file.split(".")[:-1])
        subs = pysrt.open(file)
        log.append('Simplifying {}...\n'.format(file))
        for i, sub in enumerate(subs):
            # text1 = converter.to_simplified(sub.text)
            text2 = HanziConv.toSimplified(sub.text)
            sub.text = text2

            if not hanzidentifier.is_simplified(text2):
                l = [word for word in text2 if not hanzidentifier.is_simplified(word)]

                log.append("In line {}: {}\n Could not simplify {}\n".format(i + 1, text2, l))

        os.chdir(output)
        subs.save(name + "_SIMPLIFIED.srt")
        log.append("Simplified")

    except Exception as e:
        log.append("ERROR: could not process {} successfully\n{}".format(Path(file_dir).name, str(e)))

    return log

def srt_time(s):
    hours = s // 3600
    s = s % 3600
    minutes = s // 60
    s = s % 60
    seconds = s // 1
    milliseconds = (round(s % 1, 3)) * 1000
    return hours, minutes, seconds, milliseconds

def find_time(time, timecodes, max_before, max_after):
    min_time, max_time = time - max_before, time + max_after
    valid_times = [timecode for timecode in timecodes if min_time < timecode < max_time]
    if not valid_times:
        print("New timecode created: {}".format(time))
        timecodes.append(time)
        return time, timecodes
    closest = valid_times[min(range(len(valid_times)), key=lambda i: abs(valid_times[i]-time))]
    return closest, timecodes

'''def find_time(time, timecodes, index=0, max_diff=1, min_diff=7200, min_time=0):

    index = int(index)
    time_diff = abs(time - timecodes[index])
    # print(time, timecodes[index], time_diff, min_diff, index)
    if time_diff <= min_diff:
        min_diff = time_diff
        min_time = timecodes[index]

    elif time_diff > min_diff:
        if min_diff > max_diff:
            time = round(time, 2)
            timecodes.insert(index-1, time)
            print("New timecode created: {}".format(time))
            return time, timecodes
        else:
            print("Time conformed to {}".format(min_time))
            return min_time, timecodes

    return find_time(time, timecodes, index+1, max_diff, min_diff, min_time)'''



def compare_srt(file_dir1, file_dir2, c_time, c_text, conform, output):
    log = []

    try:
        os.chdir(Path(file_dir1).parent.absolute())
        file = Path(file_dir1).name
        name1 = ".".join(file.split(".")[:-1])
        subs1 = pysrt.open(file)

        os.chdir(Path(file_dir2).parent.absolute())
        file = Path(file_dir2).name
        name2 = ".".join(file.split(".")[:-1])
        subs2 = pysrt.open(file)

        log.append("Comparing {} to {}".format(name1, name2))
        limit = min(len(subs1), len(subs2))
        if len(subs1) > len(subs2):
            log.append("WARNING: {} is longer than {}".format(name1, name2))
            log.append("Lines {} and onwards will not be changed\n".format(limit+1))
        elif len(subs1) < len(subs2):
            log.append("WARNING: {} is shorter than {}".format(name1, name2))
            log.append("Lines {} and onwards will not be changed\n".format(limit+1))

    except Exception as e:
        log.append("ERROR: could not read files: {}, {}\n{}".format(Path(file_dir1).name, Path(file_dir2).name, str(e)))
        return log

    if c_time:
        try:
            for i in range(limit):
                if subs1[i].start == subs2[i].start and subs1[i].end == subs2[i].end:
                    continue

                log.append("In line {}:\n{}-->{} changed to\n{}-->{}\n".format(i + 1, subs1[i].start, subs1[i].end,
                                                                                subs2[i].start, subs2[i].end))
                subs1[i].start = subs2[i].start
                subs1[i].end = subs2[i].end

        except Exception as e:
            log.append("ERROR: could not conform {} timing to {}\n{}".format(name1, name2, str(e)))
            return log

    if c_text:
        try:
            for i in range(limit):
                if subs1[i].text == subs2[i].text:
                    continue

                log.append("In line {}:\n{}\nV TO V\n{}\n".format(i+1, subs1[i].text, subs2[i].text))
                subs1[i].text = subs2[i].text

        except Exception as e:
            log.append("ERROR: could not conform {} text to {}\n{}".format(name1, name2, str(e)))
            return log
    if conform:
        print(output)
        os.chdir(output)
        subs1.save(name1+"_CONFORMED.srt")
    log.append("Process was successful")
    return log


def conform_time(file_dir, base, output):
    log = []
    try:
        os.chdir(Path(base).parent.absolute())
        base_name = Path(base).name
        c_subs = pysrt.open(base)

        os.chdir(Path(file_dir).parent.absolute())
        file = Path(file_dir).name
        subs = pysrt.open(file)

        log.append("conforming {} to match {}".format(file, base_name))

        if len(subs) > len(c_subs):
            log.append("Conforming SRT is longer than base SRT!")
            log.append("Lines {} and onwards will not be changed".format(1 + min(len(subs), len(c_subs))))
        elif len(subs) < len(c_subs):
            log.append("Conforming SRT is shorter than base SRT!")
            log.append("Lines {} and onwards will not be changed".format(1 + min(len(subs), len(c_subs))))

        for i, sub in enumerate(subs):
            if i >= len(c_subs):
                break
            if sub.start == c_subs[i].start and sub.end == c_subs[i].end:
                continue
            log.append("In line {}:\n{}-->{} changed to:\n{}-->{}\n".format(i + 1, sub.start, sub.end, c_subs[i].start,
                                                                            c_subs[i].end))
            sub.start = c_subs[i].start
            sub.end = c_subs[i].end

        os.chdir(output)
        subs.save(file)
        log.append("{} conformed successfully".format(file))

    except Exception as e:
        log.append("ERROR: could not process {} successfully\n{}".format(Path(file_dir).name, str(e)))

    return log

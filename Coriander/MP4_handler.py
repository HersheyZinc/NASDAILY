import cv2 as cv
import os
import numpy as np
from pathlib import Path
from scenedetect import VideoManager
from scenedetect import SceneManager
from skimage.metrics import structural_similarity
from scenedetect.detectors import ContentDetector
from GUI_handler import get_input


def find_scenes(file_dir, threshold=30.0):
    os.chdir(Path(file_dir).parent.absolute())
    name = Path(file_dir).name
    # Create our video & scene managers, then add the detector.
    video_manager = VideoManager([name])
    scene_manager = SceneManager()
    scene_manager.add_detector(
        ContentDetector(threshold=threshold))

    # Improve processing speed by downscaling before processing.
    video_manager.set_downscale_factor()

    # Start the video manager and perform the scene detection.
    video_manager.start()
    scene_manager.detect_scenes(frame_source=video_manager)

    # Each returned scene is a tuple of the (start, end) timecode.
    return scene_manager.get_scene_list()


def timestamp(frame, fps=25):
    if frame == 0:
        return "0,0,00"
    minutes = int((frame/fps)//60)
    seconds = round(frame/fps - (minutes*60),3)
    ts = ",".join([str(minutes), str(seconds)])
    return ts

def check_attributes(file_dir):
    os.chdir(Path(file_dir).parent.absolute())
    vidcap = cv.VideoCapture(Path(file_dir).name)
    fps = vidcap.get(cv.CAP_PROP_FPS)
    width = vidcap.get(cv.CAP_PROP_FRAME_WIDTH)
    height = vidcap.get(cv.CAP_PROP_FRAME_HEIGHT)
    return fps, width, height

class Video:
    def __init__(self, file_dir, scenes, titles, subtitles, configs, fps, output, scale):
        self.configs = configs
        self.log = []
        self.fps = fps
        self.output = output
        os.chdir(Path(file_dir).parent.absolute())
        self.file = Path(file_dir).name
        self.vidcap = cv.VideoCapture(self.file)
        self.scale = scale


        all_frames = list(set([frame for sublist in titles+subtitles for frame in sublist[:2]] + scenes))
        frames_needed = []
        for frame in all_frames:
            for i in range(max(0, frame - 3), frame + 4):
                if i not in frames_needed:
                    frames_needed.append(i)
        frames_needed += [frame[2] for frame in subtitles]
        # reads all frames
        self.frames = []
        self.key_frames = []
        self.frame_data = {}

        frame = 0
        last_image = None
        last_border = False
        success = True
        while success:
            success, image = self.vidcap.read()
            if not success:
                self.key_frames.append(frame)
                self.frame_data[frame] = ["Last frame", last_image]
                break
            needed = False
            if frame in frames_needed:
                needed = True
            if self.configs["borders"]:
                border, msg = self.check_borders(image)
                if border:
                    needed = True
                    if not last_border:
                        self.key_frames.append(frame)
                    self.frame_data[frame] = [msg, image]
                elif last_border:
                    self.key_frames.append(frame)
                    self.frame_data[frame] = [msg, image]
                last_border = border


            if needed:
                self.frames.append(image)
            else:
                self.frames.append(None)
            frame += 1
            last_image = image



        if self.configs["subs1"] or self.configs["subs2"] or self.configs["subs3"]:
            self.check_subtitles(subtitles)

        if self.configs["title1"] or self.configs["title2"]:
            self.check_titles(titles)

        if scenes:
            self.check_blinks(scenes)

        self.key_frames = list(set(self.key_frames))
        self.key_frames.sort()
        if not self.key_frames:
            self.key_frames.append(0)
            self.frame_data[0] = ["No key frames", self.frames[0]]
        self.frames = sorted([frame for frame in self.frame_data])

        if self.configs["guidelines"]:
            res = 1080

            half = res//2
            for i in self.frame_data:
                for y in range(half-1, half+2):
                    for x in range(80):
                        self.frame_data[i][1][x, y] = [0, 255, 0]
                        self.frame_data[i][1][y, x] = [0, 255, 0]
                    for x in range(res-80, res):
                        self.frame_data[i][1][x, y] = [0, 255, 0]
                        self.frame_data[i][1][y, x] = [0, 255, 0]

    def check_video(self):
        # print(self.key_frames)
        # print(self.frames)
        self.show_frame(self.key_frames[0])

    def show_frame(self, frame=0, i=0):
        if frame not in self.frame_data:
            print("frame {} not found".format(frame))
            i = min(len(self.key_frames) - 1, i + 1)
            new_frame = self.key_frames[i]
            return self.show_frame(new_frame, i)

        os.chdir(self.output)
        msg = self.frame_data[frame][0]
        if msg.startswith("ERROR"):
            padded_img = cv.copyMakeBorder(self.frame_data[frame][1], 10, 10, 10, 10, cv.BORDER_CONSTANT,
                                           value=[0, 0, 225])
        else:
            padded_img = cv.copyMakeBorder(self.frame_data[frame][1], 10, 10, 10, 10, cv.BORDER_CONSTANT,
                                           value=[255, 255, 255])
        width = int(padded_img.shape[1] * self.scale / 100)
        height = int(padded_img.shape[0] * self.scale / 100)
        dim = (width, height)
        padded_img = cv.resize(padded_img, dim)
        name = "{} | {} - {}".format(self.file, timestamp(frame, self.fps), msg)
        cv.namedWindow(name)
        cv.moveWindow(name, 30, 40)
        cv.imshow(name, padded_img)
        k = cv.waitKey()
        cv.destroyAllWindows()
        if k == 13:
            # "enter" Quit
            return
        if k == 100:
            # "d" next frame
            frame_i = min(self.frames.index(frame)+1, len(self.frames)-1)
            return self.show_frame(self.frames[frame_i], i)
        if k == 97:
            # "a" previous frame
            frame_i = max(self.frames.index(frame) - 1, 0)
            return self.show_frame(self.frames[frame_i], i)
        if k == 119:
            # "w" previous key frame
            i = max(0, i-1)
            new_frame = self.key_frames[i]
            return self.show_frame(new_frame, i)
        if k == 115:
            # "s" next key frame
            i = min(len(self.key_frames)-1, i+1)
            new_frame = self.key_frames[i]
            return self.show_frame(new_frame, i)
        if k == 113:
            # "q" to save image
            message = get_input(self.frame_data[frame][0])

            cv.imwrite("{} - {} - {}.jpg".format(self.file.split(".")[0], timestamp(frame,self.fps), message), self.frame_data[frame][1])

            return self.show_frame(frame, i)
        return self.show_frame(frame, i)

    def check_titles(self, titles):
        for title in titles:
            if self.configs["title1"]:
                if title[0] not in self.key_frames:
                    self.key_frames.append(title[0])
                    if title[0] not in self.frame_data:
                        self.frame_data[title[0]] = ["title first frame", self.frames[title[0]]]

            if self.configs["title2"]:
                if title[1] not in self.key_frames:
                    self.key_frames.append(title[1])
                    self.frame_data[title[1]] = ["title last frame", self.frames[title[1]]]

    def check_subtitles(self, subtitles):

        for sub in subtitles:

            if sub[0] >= len(self.frames):
                continue
            mid = sub[2]
            frame_test = self.frames[mid]
            height, width, channels = frame_test.shape

            # check dimensions and change settings
            if width > height:
                # set to youtube config
                top, bottom = 940, 1000
            elif height > width:
                #set to half vertical config
                top, bottom = int(height*0.92), int(height*0.97)

            else:
                # set to SQ config
                top, bottom = 980, 1030


            '''cv.imshow(str(top) + "-" + str(bottom), frame_test[top:bottom])
            cv.waitKey()
            cv.destroyAllWindows()'''
            frame_test = self.frames[mid][top:bottom]

            '''size = frame_test.size
            frame_test = cv.cvtColor(frame_test, cv.COLOR_BGR2GRAY)
            _, frame_test = cv.threshold(frame_test, 60, 100, cv.THRESH_BINARY)
            percent_w = round(np.count_nonzero(frame_test) / size * 100, 2)
            if percent_w < 10:
                top = 880
                if percent_w < 0.2:
                    self.key_frames.append(mid)
                    self.frame_data[mid] = ["LINES - Top line is empty", self.frames[mid]]
            frame_test = self.frames[mid][946:1060]
            size = frame_test.size
            frame_test = cv.cvtColor(frame_test, cv.COLOR_BGR2GRAY)
            _, frame_test = cv.threshold(frame_test, 100, 255, cv.THRESH_BINARY)
            percent_w = round(np.count_nonzero(frame_test) / size * 100, 2)
            if percent_w < 0.2:
                self.key_frames.append(mid)
                self.frame_data[mid] = ["LINES - Bottom line is empty", self.frames[mid]]'''

            frame_start1 = self.frames[sub[0]][top:bottom]
            frame_start2 = self.frames[sub[0]+3][top:bottom]
            frame_end1 = self.frames[sub[1]][top:bottom]
            frame_end2 = self.frames[sub[1]-3][top:bottom]
            frame_mid = self.frames[mid][top:bottom]

            # subtitle first frame
            if self.configs["subs3"]:
                if sub[0] not in self.frame_data:

                    self.frame_data[sub[0]] = ["subtitle start", self.frames[sub[0]]]
                # self.frame_data[sub[1]] = ["subtitle end", self.frames[sub[1]]]

            # Check if subtitle within frame
            if self.configs["subs1"]:
                left = frame_mid[:, :10]
                right = frame_mid[:, -10:]
                exceed = False
                H, W = left.shape[:2]
                for h in range(H):
                    for w in range(W):
                        if left.item(h, w, 0) == 255 and left.item(h, w, 1) == 255 and left.item(h, w, 2) == 255:
                            exceed = True
                            break
                        if right.item(h, w, 0) == 255 and right.item(h, w, 1) == 255 and right.item(h, w, 2) == 255:
                            exceed = True
                            break

                if exceed:
                    self.key_frames.append(mid)
                    self.frame_data[mid] = ["ERROR MARGIN - subtitles exceed frame", self.frames[mid]]
                    for h in range(top, bottom):
                        for w in range(0, 10):
                            if self.frames[mid].item(h, w, 0) > 200 and self.frames[mid].item(h, w, 1) > 200 and self.frames[mid].item(h, w, 2) > 200:
                                continue
                            self.frames[mid][h, w] = [0, 0, 150]
                        for w in range(1070, 1080):
                            if self.frames[mid].item(h, w, 0) > 200 and self.frames[mid].item(h, w, 1) > 200 and self.frames[mid].item(h, w, 2) > 200:
                                continue
                            self.frames[mid][h, w] = [0, 0, 150]

            # check subtitle timing
            if self.configs["subs2"]:

                if sub[1] + 1 < len(self.frames):
                    n_frame = sub[1]+1
                    frame_next = self.frames[n_frame][top:bottom]
                    if self.compare_images(frame_end1, frame_next):
                        for i in range(n_frame-4, n_frame+3):
                            self.frame_data[i] = ["", self.frames[i]]
                        self.key_frames.append(n_frame)
                        self.frame_data[n_frame] = ["ERROR BLINK - subtitles overshot", self.frames[n_frame]]

                if not self.compare_images(frame_start1, frame_end1):

                    if not self.compare_images(frame_start1, frame_start2):
                        for i in range(sub[0] - 3, sub[0] + 4):
                            self.frame_data[i] = ["", self.frames[i]]
                        self.key_frames.append(sub[0])
                        self.frame_data[sub[0]] = ["ERROR BLINK - subtitles start late", self.frames[sub[0]]]

                    if not self.compare_images(frame_end1, frame_end2):
                        for i in range(sub[1] - 3, sub[1] + 4):
                            self.frame_data[i] = ["", self.frames[i]]
                        self.key_frames.append(sub[1])
                        self.frame_data[sub[1]] = ["ERROR BLINK - subtitles end early", self.frames[sub[1]]]

    def check_borders(self, img, margin=5):
        gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
        top = gray[:margin]
        bottom = gray[-margin:]
        left = gray[:, :margin]
        right = gray[:, -margin:]
        t_check = not bool(cv.countNonZero(top))
        b_check = not bool(cv.countNonZero(bottom))
        r_check = not bool(cv.countNonZero(right))
        l_check = not bool(cv.countNonZero(left))
        checks = [t_check, b_check, r_check, l_check]
        sides = ["top", "bottom", "right", "left"]
        if any(checks) and not all(checks):
            text = "ERROR BORDERS - " + " and ".join([sides[i] for i, x in enumerate(checks) if x]) + " border(s)"
            return True, text
        else:
            return False, "-"


    def check_blinks(self, scenes):
        top, bottom = 946, 1060
        for scene_frame in scenes:
            if scene_frame < 6:
                continue
            if abs(scene_frame - len(self.frames)) < 6:
                continue
            frame_0 = self.frames[scene_frame-2][top:bottom]
            frame_2 = self.frames[scene_frame][top:bottom]

            frame_3 = self.frames[scene_frame + 1][top:bottom]
            frame_5 = self.frames[scene_frame + 3][top:bottom]

            if self.compare_images(frame_2, frame_3) and not self.compare_images(frame_0, frame_5):
                for i in range(scene_frame - 3, scene_frame + 4):
                    self.frame_data[i] = ["", self.frames[i]]
                self.key_frames.append(scene_frame)
                self.frame_data[scene_frame] = ["BLINK - TYPE I", self.frames[scene_frame]]

            elif not self.compare_images(frame_0, frame_2) or not self.compare_images(frame_3, frame_5):
                for i in range(scene_frame - 3, scene_frame + 4):
                    self.frame_data[i] = ["", self.frames[i]]
                self.key_frames.append(scene_frame)
                self.frame_data[scene_frame] = ["BLINK - TYPE II", self.frames[scene_frame]]




    def compare_images(self, img1, img2):
        img1_gray = cv.cvtColor(img1, cv.COLOR_BGR2GRAY)
        img2_gray = cv.cvtColor(img2, cv.COLOR_BGR2GRAY)
        _, img1_gray = cv.threshold(img1_gray, 127, 255, cv.THRESH_BINARY_INV)
        _, img2_gray = cv.threshold(img2_gray, 127, 255, cv.THRESH_BINARY_INV)
        score, diff = structural_similarity(img1_gray, img2_gray, full=True)

        # True -> similar
        if score > 0.975:
            output = True
        else:
            output = False
            '''vis = np.concatenate([img1, img2], axis=1)
            cv.imshow(str(output), vis)
            k = cv.waitKey()'''
            cv.destroyAllWindows()


        return output





import sys
from PyQt5 import uic, QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

import os
os.environ["OPENCV_VIDEOIO_MSMF_ENABLE_HW_TRANSFORMS"] = "0"
import cv2
import concurrent.futures

class RecordThread(QtCore.QThread):
    frame_ready = QtCore.pyqtSignal(int, QtGui.QPixmap)

    def __init__(self, camera_ids, path_save, calibration, record_time=None):
        super().__init__()
        self.camera_ids = camera_ids
        self.path_save = path_save
        self.calibration = calibration
        self.recording = False
        self.record_time = record_time
        self.mutex = QtCore.QMutex()

    def run(self):
        self.recording = True
        captures, writers, labels = [], [], []
        for i, camera_id in enumerate(self.camera_ids):
            cap = cv2.VideoCapture(camera_id)
            
            width = 1280
            height = 720
            fps = int(cap.get(cv2.CAP_PROP_FPS))
           
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            
            if self.calibration:
                filename = os.path.join(self.path_save, f'{i}.mp4')
            else:
                self.path_save = self.path_save.replace("\\","/")
                filename = os.path.join(self.path_save, f'{self.path_save.split("/")[-1]}_{i}.mp4')

            filename = filename.replace("\\","/")
            writer_fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            writer_params = (writer_fourcc, fps, (width, height))
            writer = cv2.VideoWriter(filename, *writer_params)
            captures.append(cap)
            writers.append(writer)

        labels = [f'Camera {i+1}' for i in range(len(captures))]

        max_frames = float('inf')
        if self.record_time:
            max_frames = int(self.record_time * min([cap.get(cv2.CAP_PROP_FPS) for cap in captures]))

        with concurrent.futures.ThreadPoolExecutor(max_workers=len(captures)) as executor:
            futures = []

            for i, cap in enumerate(captures):
                future = executor.submit(self.record_video, cap, writers[i], i, max_frames)
                futures.append(future)

            for future in concurrent.futures.as_completed(futures):
                result = future.result()

        for cap in captures:
            cap.release()
        for writer in writers:
            writer.release()

    def stop_recording(self):
        self.recording = False

    def convert_cv_qt(self, frame):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        qt_img = QtGui.QImage(rgb_frame.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
        return QtGui.QPixmap.fromImage(qt_img)

    def record_video(self, cap, writer, i, max_frames):
        frame_count = 0
        while self.recording and frame_count < max_frames:
            ret, frame = cap.read()
            if not ret:
                break

            writer.write(frame)

            max_width = 161
            max_height = 146
            resized_frame = cv2.resize(frame, (max_width, max_height))
            qt_img = self.convert_cv_qt(resized_frame)

            # Add a lock to avoid conflicts when emitting signals
            with QtCore.QMutexLocker(self.mutex):
                self.frame_ready.emit(i, qt_img)

            frame_count += 1
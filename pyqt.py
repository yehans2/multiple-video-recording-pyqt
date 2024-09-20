import sys
from PyQt5 import uic, QtWidgets, QtCore
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

from PyQt5 import *
from PyQt5.QtWidgets import*
from PyQt5.QtCore import *

from RecordThread import RecordThread
import os
os.environ["OPENCV_VIDEOIO_MSMF_ENABLE_HW_TRANSFORMS"] = "0"
import glob
import cv2
import threading

menu_widget = uic.loadUiType("menu_widget.ui")[0]
setting_widget = uic.loadUiType("setting_widget.ui")[0]
calibrate_widget = uic.loadUiType("calibrate_widget.ui")[0]
record_widget = uic.loadUiType("record_widget.ui")[0]


class MenuWidget(QMainWindow, menu_widget):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.Setting_button.clicked.connect(self.settingbuttonfunc)

    def settingbuttonfunc(self):
        widget.setCurrentIndex(widget.currentIndex()+1)


class SettingWidget(QMainWindow, setting_widget):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.dateEdit.setDateTime(QDateTime.currentDateTime())
        self.dataset_next_button.setDisabled(True)
        self.dataset_next_button.clicked.connect(self.datasetnextbuttonfunc)
        self.LoadButton.clicked.connect(self.loadpathfunc)

        self.pain_checkbox.toggled.connect(self.changeTitle)
        self.health_checkbox.toggled.connect(self.changeTitle)
        self.sng_checkbox.toggled.connect(self.changeTitle)
        self.test_checkbox.toggled.connect(self.changeTitle)
        self.calibration_checkbox.toggled.connect(self.changeTitle)

        self.setting_check_button.clicked.connect(self.settingcheckbuttonfunc)
        self.setting_next_button.clicked.connect(self.settingnextbuttonfunc)

        self.actionhome.triggered.connect(self.toolbar_clicked1)
        self.actionsetting.triggered.connect(self.toolbar_clicked2)
        self.actioncalibration.triggered.connect(self.toolbar_clicked3)
        self.actionrecord.triggered.connect(self.toolbar_clicked4)

        self.setting_next_button.setDisabled(True)

        self.path_save = ''
        self.calibration = ''
        self.calibration_save = ''
        self.recording_time = int()
        self.textBrowser_2.append("Please enter mouse information and savpath")

    def clear_hidden_layer_editor(self, event):
        self.hidden_layer_editor.clear()

    def clear_learning_rate_editor(self, event):
        self.learning_rate_editor.clear()

    def toolbar_clicked1(self):
        widget.setCurrentIndex(0)

    def toolbar_clicked2(self):
        widget.setCurrentIndex(1)

    def toolbar_clicked3(self):
        widget.setCurrentIndex(2)

    def toolbar_clicked4(self):
        widget.setCurrentIndex(3)

    def datasetnextbuttonfunc(self):
        self.tabWidget.setCurrentIndex(1)
        self.tabWidget.setTabEnabled(1, True)

    def changeTitle(self):
        checkbox_mapping = {
            self.pain_checkbox: ("pain", "./image/coronavirus.png"),
            self.health_checkbox: ("health", "./image/heart-beat.png"),
            self.sng_checkbox: ("sng", "./image/pain.png"),
            self.test_checkbox: ("test", "./image/question.png")
        }
    
        for checkbox, (dataset_name, pixmap_path) in checkbox_mapping.items():
            if checkbox.isChecked():
                self.dataset = dataset_name
                self.choosed_data.setText(dataset_name.capitalize())
                pixmap = QPixmap(pixmap_path)
                self.select_dataset.setPixmap(QPixmap(pixmap))
    
        self.dataset_next_button.setDisabled(False)
    
        if self.calibration_checkbox.isChecked():
            QMessageBox.information(self, 'ok', 'Finished calibration')

    def settingcheckbuttonfunc(self):
        try:
            typeofdrug = self.typeofdrug.currentText()
            mousename = self.mousename_editor.text()
            date = self.dateEdit.dateTime().toPyDateTime().date().strftime("%Y_%m_%d")
            date_calibration = self.dateEdit.dateTime().toPyDateTime().date().strftime("%Y_%m_%d_%H")
            self.recording_time = int(self.recordingtime.currentText().replace('min','')) * 60
        
            # calibration path
            self.calibration = os.path.join(self.selected_directory, 'calibration')
        
            # calibration save path
            self.calibration_save = os.path.join(self.selected_directory, 'calibration', date_calibration)
        
            # pain or helath or sng or calbrtion folder path
            self.path = os.path.join(self.selected_directory, self.dataset)
        
            # save path
            self.path_save = os.path.join(self.selected_directory, self.dataset, f"{typeofdrug}_{mousename}_{date}")
        
            self.textBrowser_2.setText(self.path_save)
        
            self.setting_next_button.setDisabled(False)
        except:
            QMessageBox.information(self, 'ok', f"Please enter mouse information and savpath")
    
    def settingnextbuttonfunc(self):
        if os.path.isdir(self.path):
            QMessageBox.information(self, 'ok', f"The folder {self.path} exists.\nWill create folder at{self.path_save}")
        else:
            QMessageBox.information(self, 'ok', f'Will make the folder at {self.path_save}')
            os.makedirs(self.path)
    
        try:
            os.makedirs(self.path_save)
        except:
            pass
    
        if self.calibration_checkbox.isChecked():
            widget.setCurrentIndex(widget.currentIndex()+2)
        else:
            widget.setCurrentIndex(widget.currentIndex()+1)
    
        os.makedirs(self.calibration, exist_ok=True)
        os.makedirs(self.calibration_save, exist_ok=True)

    def loadpathfunc(self):
        dialog = QFileDialog()
        dialog.setFileMode(QFileDialog.Directory)
        if dialog.exec_() == QFileDialog.Accepted:
            self.selected_directory = dialog.selectedFiles()[0]
            self.savepath_editor.setText(self.selected_directory)


class CalibrationWidget(QMainWindow, calibrate_widget):
    def __init__(self) -> None:
        super().__init__()
        self.setupUi(self)

        self.record_thread = None

        self.camera = [self.camera1_label, self.camera2_label, self.camera3_label, self.camera4_label, self.camera5_label]

        self.connect_signals()

    def start_recording(self, calibration_save: str) -> None:
        if settingwindow.path_save is not None:
            self.record_thread = RecordThread([0, 1, 2, 3, 4], calibration_save, True)
            self.record_thread.frame_ready.connect(self.update_label)
            self.record_thread.start()
    

    def stop_recording(self) -> None:
        if self.record_thread is not None:
            self.record_thread.stop_recording()
            self.record_thread.wait()
            self.record_thread = None

        for i, _ in enumerate(self.camera):
            self.camera[i].clear() 
        QMessageBox.information(self, 'ok', 'stop calibration')

    def next_recording(self) -> None:
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setWindowTitle("Calibration Done")
        msg_box.setText("The calibration process has been completed.")
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec_()
        widget.setCurrentIndex(widget.currentIndex() + 1)

    def update_label(self, i: int, pixmap: QPixmap) -> None:
        self.camera[i].setPixmap(pixmap)

    def toolbar_clicked1(self) -> None:
        widget.setCurrentIndex(0)

    def toolbar_clicked2(self) -> None:
        widget.setCurrentIndex(1)

    def toolbar_clicked3(self) -> None:
        widget.setCurrentIndex(2)

    def toolbar_clicked4(self) -> None:
        widget.setCurrentIndex(3)

    def connect_signals(self) -> None:
        self.calibration_start.clicked.connect(lambda: self.start_recording(settingwindow.calibration_save))
        self.calibration_stop_but.clicked.connect(self.stop_recording)
        self.calibration_next_but.clicked.connect(self.next_recording)
        self.actionhome.triggered.connect(self.toolbar_clicked1)
        self.actionsetting.triggered.connect(self.toolbar_clicked2)
        self.actioncalibration.triggered.connect(self.toolbar_clicked3)
        self.actionrecord.triggered.connect(self.toolbar_clicked4)

class RecordWidget(QMainWindow, record_widget):
    def __init__(self) -> None:
        super().__init__()
        self.setupUi(self)

        self.record_thread = None
        self.camera = [self.record1, self.record2, self.record3, self.record4, self.record5]

        self.connect_signals()

    def start_recording(self) -> None:
        if settingwindow.path_save is not None:
            self.record_thread = RecordThread([0, 1, 2, 3, 4], settingwindow.path_save, False, record_time = settingwindow.recording_time)
            self.record_thread.frame_ready.connect(self.update_label)
            self.record_thread.start()
           
    def stop_recording(self) -> None:
        if self.record_thread is not None:
            self.record_thread.stop_recording()
            self.record_thread.wait()
            self.record_thread = None
        for i, _ in enumerate(self.camera):
            self.camera[i].clear()
        QMessageBox.information(self, 'ok', 'stop recording')

    def record_donefunc(self) -> None:
        settingwindow.textBrowser_2.setText("Please enter mouse information and savpath")
        settingwindow.savepath_editor.setText('')
        settingwindow.typeofdrug.setCurrentText('base')
        settingwindow.mousename_editor.setText('')

        widget.setCurrentIndex(0)

    def update_label(self, i: int, pixmap: QPixmap) -> None:
        self.camera[i].setPixmap(pixmap)

    def toolbar_clicked1(self) -> None:
        widget.setCurrentIndex(0)

    def toolbar_clicked2(self) -> None:
        widget.setCurrentIndex(1)

    def toolbar_clicked3(self) -> None:
        widget.setCurrentIndex(2)

    def toolbar_clicked4(self) -> None:
        widget.setCurrentIndex(3)

    def connect_signals(self) -> None:
        self.record_start.clicked.connect(self.start_recording)
        self.record_stop.clicked.connect(self.stop_recording)
        self.record_done.clicked.connect(self.record_donefunc)
        self.actionhome.triggered.connect(self.toolbar_clicked1)
        self.actionsetting.triggered.connect(self.toolbar_clicked2)
        self.actioncalibration.triggered.connect(self.toolbar_clicked3)
        self.actionrecord.triggered.connect(self.toolbar_clicked4)    


if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = QtWidgets.QStackedWidget()

    menuwindow = MenuWidget()
    settingwindow = SettingWidget()
    calibrationwindow = CalibrationWidget()
    Recordwindow = RecordWidget()

    widget.addWidget(menuwindow)
    widget.addWidget(settingwindow)
    widget.addWidget(calibrationwindow)
    widget.addWidget(Recordwindow)
    widget.setFixedSize(730, 430)
    widget.show()

    app.exec_()






import asyncio
import sys
from typing import Iterator, Tuple

import serial
from fbs_runtime.application_context.PyQt5 import ApplicationContext
from PyQt5.QtCore import QSettings
from PyQt5.QtGui import QCloseEvent
from PyQt5.QtWidgets import (QApplication, QCheckBox, QComboBox, QGridLayout,
                             QLabel, QLineEdit, QMessageBox, QPlainTextEdit,
                             QPushButton, QWidget)
from quamash import QEventLoop
from serial.tools.list_ports import comports

from ATCommands import Sensor
import ATCommands as Motherboard

#import ATCommands as Motherboard
import qdarkstyle
#from ATCommands import Sensor
from CustomDebug import CustomDebug

# Object for access to the serial port
_bytesize = serial.EIGHTBITS
_stopbits = serial.STOPBITS_ONE
_parity = serial.PARITY_NONE
_baudrate = 115200
_flowcontrol = False
ser = serial.Serial(baudrate=_baudrate, xonxoff=_flowcontrol,
                    timeout=5, bytesize=_bytesize, stopbits=_stopbits, parity=_parity, write_timeout=None)

# Setting constants
SETTING_PORT_NAME = 'port_name'
SETTING_MESSAGE = "message"

VERSION = "version 1.0 by Gilles Callebaut"


def gen_serial_ports() -> Iterator[Tuple[str, str]]:
    """Return all available serial ports."""
    ports = comports()
    return ((p.description, p.device) for p in ports)


def send_serial_async(msg: str) -> None:
    """Send a message to serial port (async)."""
    ser.write(msg.encode())


# noinspection PyArgumentList
class RemoteWidget(QWidget):
    """Main Widget."""

    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)

        self._connected_sensors = {}

        # debug messages
        self.debug_label = QLabel(self.tr('Debug'))
        self.debug_textedit = QPlainTextEdit()
        self.debug_textedit.setReadOnly(True)
        self.debug_label.setBuddy(self.debug_textedit)

        self._debug = CustomDebug(self.debug_textedit)

        # Refresh COM Ports
        self.refresh_com_ports_btn = QPushButton(self.tr('Refresh'))
        self.refresh_com_ports_btn.pressed.connect(self.update_com_ports)

        # Refresh COM Ports
        self.connect_btn = QPushButton(self.tr('Connect'))
        self.connect_btn.pressed.connect(self.on_connect_btn_pressed)

        # Port Combobox
        self.port_label = QLabel(self.tr('COM Port:'))
        self.port_combobox = QComboBox()
        self.port_label.setBuddy(self.port_combobox)
        self.port_combobox.currentIndexChanged.connect(
            self.on_port_combobox_change)
        self.update_com_ports()

        # Connect and Disconnect Buttons
        self.connect_btn = QPushButton(self.tr('Connect'))
        self.disconnect_btn = QPushButton(self.tr('Disconnect'))
        self.disconnect_btn.setVisible(False)
        self.connect_btn.pressed.connect(self.on_connect_btn_pressed)
        self.disconnect_btn.pressed.connect(self.on_disconnect_btn_pressed)

        # poll messages
        # Enabled?
        #self.poll_checkbox = QCheckBox("Poll?", self)
        # self.poll_checkbox.stateChanged.connect(self.click_poll_sensor)
        # Seconds
        self.poll_label = QLabel(self.tr('Poll interval (minutes):'))
        self.poll_lineedit = QLineEdit()
        self.poll_label.setBuddy(self.poll_lineedit)
        self.poll_lineedit.setEnabled(True)
        # self.poll_lineedit.returnPressed.connect(self.)

        # threshold
        # per metric
        # Enabled?
        self.threshold_label_1 = QLabel(self.tr('Metric 1:'))

        self.threshold_label_2 = QLabel(self.tr('Metric 2:'))
        self.threshold_label_2.setVisible(False)

        self.threshold_label_3 = QLabel(self.tr('Metric 3:'))
        self.threshold_label_3.setVisible(True)

        self.threshold_label_4 = QLabel(self.tr('Metric 4:'))
        self.threshold_label_4.setVisible(True)

        self.threshold_checkbox_1 = QCheckBox("Threshold ?", self)
        self.threshold_checkbox_1.stateChanged.connect(
            self.click_threshold_checkbox_1)
        self.threshold_checkbox_1.setVisible(False)

        self.threshold_checkbox_2 = QCheckBox("Threshold ?", self)
        self.threshold_checkbox_2.stateChanged.connect(
            self.click_threshold_checkbox_2)
        self.threshold_checkbox_2.setVisible(False)

        self.threshold_checkbox_3 = QCheckBox("Threshold ?", self)
        self.threshold_checkbox_3.stateChanged.connect(
            self.click_threshold_checkbox_3)
        self.threshold_checkbox_3.setVisible(False)

        self.threshold_checkbox_4 = QCheckBox("Threshold ?", self)
        self.threshold_checkbox_4.stateChanged.connect(
            self.click_threshold_checkbox_4)
        self.threshold_checkbox_4.setVisible(False)

        # threshold high
        self.threshold_high_label_1 = QLabel(self.tr('High:'))
        self.threshold_high_lineedit_1 = QLineEdit()
        self.threshold_high_label_1.setBuddy(self.threshold_high_lineedit_1)
        self.threshold_high_lineedit_1.setEnabled(True)

        self.threshold_high_label_2 = QLabel(self.tr('High:'))
        self.threshold_high_lineedit_2 = QLineEdit()
        self.threshold_high_label_2.setBuddy(self.threshold_high_lineedit_2)
        self.threshold_high_lineedit_2.setEnabled(True)

        self.threshold_high_label_3 = QLabel(self.tr('High:'))
        self.threshold_high_lineedit_3 = QLineEdit()
        self.threshold_high_label_3.setBuddy(self.threshold_high_lineedit_3)
        self.threshold_high_lineedit_3.setEnabled(True)

        self.threshold_high_label_4 = QLabel(self.tr('High:'))
        self.threshold_high_lineedit_4 = QLineEdit()
        self.threshold_high_label_4.setBuddy(self.threshold_high_lineedit_4)
        self.threshold_high_lineedit_4.setEnabled(True)

        # threshold Low
        self.threshold_low_label_1 = QLabel(self.tr('Low:'))
        self.threshold_low_lineedit_1 = QLineEdit()
        self.threshold_low_label_1.setBuddy(self.threshold_low_lineedit_1)
        self.threshold_low_lineedit_1.setEnabled(True)

        self.threshold_low_label_2 = QLabel(self.tr('Low:'))
        self.threshold_low_lineedit_2 = QLineEdit()
        self.threshold_low_label_2.setBuddy(self.threshold_low_lineedit_2)
        self.threshold_low_lineedit_2.setEnabled(True)

        self.threshold_low_label_3 = QLabel(self.tr('Low:'))
        self.threshold_low_lineedit_3 = QLineEdit()
        self.threshold_low_label_3.setBuddy(self.threshold_low_lineedit_3)
        self.threshold_low_lineedit_3.setEnabled(True)

        self.threshold_low_label_4 = QLabel(self.tr('Low:'))
        self.threshold_low_lineedit_4 = QLineEdit()
        self.threshold_low_label_4.setBuddy(self.threshold_low_lineedit_4)
        self.threshold_low_lineedit_4.setEnabled(True)

        # Sensor Combobox
        self.sensor_label = QLabel(self.tr('Sensor:'))
        self.sensor_combobox = QComboBox()
        self.sensor_label.setBuddy(self.sensor_combobox)
        self.sensor_combobox.currentIndexChanged.connect(
            self.on_sensor_combobox_change)
        self.update_com_ports()
        self.sensor_btn = QPushButton(self.tr('Load'))
        self.sensor_btn.setVisible(False)
        self.sensor_btn.pressed.connect(self.on_sensor_btn_pressed)

        # Save and Disconnect Buttons
        self.save_btn = QPushButton(self.tr('Save'))
        # disable visivibility and only show when there is a connection
        self.save_btn.setVisible(False)
        self.disconnect_btn = QPushButton(self.tr('Disconnect'))
        self.disconnect_btn.setVisible(False)
        self.save_btn.pressed.connect(self.on_save_btn_pressed)
        self.disconnect_btn.pressed.connect(self.on_disconnect_btn_pressed)

        # Arrange Layout
        layout = QGridLayout()

        # COM Port line
        layout.addWidget(self.port_label, 0, 0)
        layout.addWidget(self.port_combobox, 0, 1, 1, 2)
        layout.addWidget(self.connect_btn, 0, 3)
        layout.addWidget(self.refresh_com_ports_btn, 0, 4)
        #layout.addWidget(self.port_motherboard, 0, 1, 2)

        # Sensors line
        layout.addWidget(self.sensor_label, 1, 0)
        layout.addWidget(self.sensor_combobox, 1, 1, 1, 2)
        layout.addWidget(self.sensor_btn, 1, 3)
        layout.addWidget(self.save_btn, 1, 4)

        # Polling line

        #layout.addWidget(self.poll_checkbox, 2, 0)
        layout.addWidget(self.poll_label, 2, 1)
        layout.addWidget(self.poll_lineedit, 2, 2)

        # threshold line

        layout.addWidget(self.threshold_label_1, 3, 0)
        layout.addWidget(self.threshold_checkbox_1, 3, 1)
        layout.addWidget(self.threshold_high_label_1, 3, 2)
        layout.addWidget(self.threshold_high_lineedit_1, 3, 3)
        layout.addWidget(self.threshold_low_label_1, 3, 4)
        layout.addWidget(self.threshold_low_lineedit_1, 3, 5)

        layout.addWidget(self.threshold_label_2, 4, 0)
        layout.addWidget(self.threshold_checkbox_2, 4, 1)
        layout.addWidget(self.threshold_high_label_2, 4, 2)
        layout.addWidget(self.threshold_high_lineedit_2, 4, 3)
        layout.addWidget(self.threshold_low_label_2, 4, 4)
        layout.addWidget(self.threshold_low_lineedit_2, 4, 5)

        layout.addWidget(self.threshold_label_3, 5, 0)
        layout.addWidget(self.threshold_checkbox_3, 5, 1)
        layout.addWidget(self.threshold_high_label_3, 5, 2)
        layout.addWidget(self.threshold_high_lineedit_3, 5, 3)
        layout.addWidget(self.threshold_low_label_3, 5, 4)
        layout.addWidget(self.threshold_low_lineedit_3, 5, 5)

        layout.addWidget(self.threshold_label_4, 6, 0)
        layout.addWidget(self.threshold_checkbox_4, 6, 1)
        layout.addWidget(self.threshold_high_label_4, 6, 2)
        layout.addWidget(self.threshold_high_lineedit_4, 6, 3)
        layout.addWidget(self.threshold_low_label_4, 6, 4)
        layout.addWidget(self.threshold_low_lineedit_4, 6, 5)

        # Debug
        layout.addWidget(self.debug_label, 7, 0)
        layout.addWidget(self.debug_textedit, 8, 0, 1, 5)

        # Save and disconnect layout

        layout.addWidget(self.disconnect_btn, 9, 4)

        self.remove_metric_rows_from_gui()

        self.setLayout(layout)

        # self._load_settings()

        self._debug.write("GUI", "Application started successfully")
        self._debug.write("GUI", VERSION)
        self.update_com_ports()

    # def _load_settings(self) -> None:
    #     """Load settings on startup."""
    #     settings = QSettings()

    #     # port name
    #     port_name = settings.value(SETTING_PORT_NAME)
    #     if port_name is not None:
    #         index = self.port_combobox.findData(port_name)
    #         if index > -1:
    #             self.port_combobox.setCurrentIndex(index)

    #     # last message
    #     msg = settings.value(SETTING_MESSAGE)
    #     if msg is not None:
    #         self.msg_lineedit.setText(msg)

    # def _save_settings(self) -> None:
    #     """Save settings on shutdown."""
    #     settings = QSettings()
    #     settings.setValue(SETTING_PORT_NAME, self.port)
    #     settings.setValue(SETTING_MESSAGE, self.msg_lineedit.text())

    def show_error_message(self, msg: str) -> None:
        """Show a Message Box with the error message."""
        QMessageBox.critical(self, QApplication.applicationName(), str(msg))

    def update_com_ports(self) -> None:
        """Update COM Port list in GUI."""
        self._debug.write("COM", "Searching for COM ports")
        self.port_combobox.clear()
        for name, device in gen_serial_ports():
            self.port_combobox.addItem(name, device)
            self._debug.write("COM", F"Found name: {name}, device: {device}")

    def on_sensor_combobox_change(self, i):
        # TODO
        pass

    def on_port_combobox_change(self, i):
        self._debug.write(
            "GUI", F"Selected {self.port_combobox.currentText()} COM ports")

    def remove_metric_rows_from_gui(self):
        self.threshold_label_1.setVisible(False)
        self.threshold_label_2.setVisible(False)
        self.threshold_label_3.setVisible(False)
        self.threshold_label_4.setVisible(False)

        self.threshold_checkbox_1.setVisible(False)
        self.threshold_checkbox_2.setVisible(False)
        self.threshold_checkbox_3.setVisible(False)
        self.threshold_checkbox_4.setVisible(False)

        self.threshold_high_label_1.setVisible(False)
        self.threshold_high_label_2.setVisible(False)
        self.threshold_high_label_3.setVisible(False)
        self.threshold_high_label_4.setVisible(False)

        self.threshold_low_label_1.setVisible(False)
        self.threshold_low_label_2.setVisible(False)
        self.threshold_low_label_3.setVisible(False)
        self.threshold_low_label_4.setVisible(False)

        self.threshold_high_lineedit_1.setVisible(False)
        self.threshold_high_lineedit_2.setVisible(False)
        self.threshold_high_lineedit_3.setVisible(False)
        self.threshold_high_lineedit_4.setVisible(False)

        self.threshold_low_lineedit_1.setVisible(False)
        self.threshold_low_lineedit_2.setVisible(False)
        self.threshold_low_lineedit_3.setVisible(False)
        self.threshold_low_lineedit_4.setVisible(False)

    def on_sensor_btn_pressed(self):
        self.save_btn.setVisible(True)

        self.remove_metric_rows_from_gui()
        sensor_str = self.sensor_combobox.currentText()
        selected_sensor = self._connected_sensors[sensor_str]
        self._debug.write("APP", F"Loading sensor data from {selected_sensor}")
        print(self._connected_sensors)
        Motherboard.load_data(selected_sensor, self._debug, ser)

        # self.poll_checkbox.setCheckState(selected_sensor._polling_enabled)
        self.poll_lineedit.setText(
            str(selected_sensor._polling_interval_sec//60))
        for idx, (th_e, th_h, th_l, label) in enumerate(zip(selected_sensor._thresholds_enabled, selected_sensor.get_thresholds(which_th=Motherboard.TH_HIGH, to_machine=False), selected_sensor.get_thresholds(which_th=Motherboard.TH_LOW, to_machine=False), selected_sensor._metric_labels)):
            th_h = str(th_h)
            th_l = str(th_l)
            
            if idx == 0:
                self.threshold_label_1.setText(label)
                self.threshold_label_1.setVisible(True)
                self.threshold_checkbox_1.setCheckState(th_e)
                self.threshold_checkbox_1.setVisible(True)
                self.threshold_high_lineedit_1.setText(th_h)
                self.threshold_high_lineedit_1.setVisible(True)
                self.threshold_low_lineedit_1.setText(th_l)
                self.threshold_low_lineedit_1.setVisible(True)
                self.threshold_low_label_1.setVisible(True)
                self.threshold_high_label_1.setVisible(True)
            if idx == 1:
                self.threshold_label_2.setText(label)
                self.threshold_label_2.setVisible(True)
                self.threshold_checkbox_2.setCheckState(th_e)
                self.threshold_checkbox_2.setVisible(True)
                self.threshold_high_lineedit_2.setText(th_h)
                self.threshold_high_lineedit_2.setVisible(True)
                self.threshold_low_lineedit_2.setText(th_l)
                self.threshold_low_lineedit_2.setVisible(True)
                self.threshold_low_label_2.setVisible(True)
                self.threshold_high_label_2.setVisible(True)
            if idx == 2:
                self.threshold_label_3.setText(label)
                self.threshold_label_3.setVisible(True)
                self.threshold_checkbox_3.setCheckState(th_e)
                self.threshold_checkbox_3.setVisible(True)
                self.threshold_high_lineedit_3.setText(th_h)
                self.threshold_high_lineedit_3.setVisible(True)
                self.threshold_low_lineedit_3.setText(th_l)
                self.threshold_low_lineedit_3.setVisible(True)
                self.threshold_low_label_3.setVisible(True)
                self.threshold_high_label_3.setVisible(True)
            if idx == 3:
                self.threshold_label_4.setText(label)
                self.threshold_label_4.setVisible(True)
                self.threshold_checkbox_4.setCheckState(th_e)
                self.threshold_checkbox_4.setVisible(True)
                self.threshold_high_lineedit_4.setText(th_h)
                self.threshold_high_lineedit_4.setVisible(True)
                self.threshold_low_lineedit_4.setText(th_l)
                self.threshold_low_lineedit_4.setVisible(True)
                self.threshold_low_label_4.setVisible(True)
                self.threshold_high_label_4.setVisible(True)

    @property
    def port(self) -> str:
        """Return the current serial port."""
        return self.port_combobox.currentData()

    def closeEvent(self, event: QCloseEvent) -> None:
        """Handle Close event of the Widget."""
        if ser.is_open:
            ser.close()

        # self._save_settings()

        event.accept()

    def click_poll_sensor(self):
        # TODO
        pass

    def click_threshold_checkbox_1(self):
        pass
        # TODO

    def click_threshold_checkbox_2(self):
        pass
        # TODO

    def click_threshold_checkbox_3(self):
        pass
        # TODO

    def click_threshold_checkbox_4(self):
        pass
        # TODO

    def on_save_btn_pressed(self):
        sensor_str = self.sensor_combobox.currentText()
        selected_sensor = self._connected_sensors[sensor_str]
        self._debug.write("APP", F"Saving data from {sensor_str}")
        # check which metrics are visible
        # update data from input to selected_sensor object
        # update motherboard

        #selected_sensor._polling_enabled = self.poll_checkbox.isChecked()
        selected_sensor._polling_interval_sec = int(
            self.poll_lineedit.text())*60

        if self.threshold_label_1.isVisible():
            # read data from threshold 1

            selected_sensor._thresholds_enabled[0] = self.threshold_checkbox_1.isChecked(
            )

            selected_sensor.set_threshold(float(self.threshold_high_lineedit_1.text(
            )), metric_idx=0, to_machine=True, which_th=Motherboard.TH_HIGH)
            selected_sensor.set_threshold(float(self.threshold_low_lineedit_1.text(
            )), metric_idx=0, to_machine=True, which_th=Motherboard.TH_LOW)

            self._debug.write("APP", F"Saving metric 1 from {sensor_str}")

            # metric 2 is only visible when 1 is also visible
            if self.threshold_label_2.isVisible():
                selected_sensor._thresholds_enabled[1] = self.threshold_checkbox_2.isChecked(
                )
                selected_sensor.set_threshold(float(self.threshold_high_lineedit_2.text(
                )), metric_idx=1, to_machine=True, which_th=Motherboard.TH_HIGH)
                selected_sensor.set_threshold(float(self.threshold_low_lineedit_2.text(
                )), metric_idx=1, to_machine=True, which_th=Motherboard.TH_LOW)

                self._debug.write(
                    "APP", F"Saving metric 2 from {sensor_str}")
                if self.threshold_label_3.isVisible():
                    selected_sensor._thresholds_enabled[2] = self.threshold_checkbox_3.isChecked(
                    )
                    selected_sensor.set_threshold(float(self.threshold_high_lineedit_3.text(
                    )), metric_idx=2, to_machine=True, which_th=Motherboard.TH_HIGH)
                    selected_sensor.set_threshold(float(self.threshold_low_lineedit_3.text(
                    )), metric_idx=2, to_machine=True, which_th=Motherboard.TH_LOW)

                    self._debug.write(
                        "APP", F"Saving metric 3 from {sensor_str}")
                    if self.threshold_label_4.isVisible():
                        selected_sensor._thresholds_enabled[3] = self.threshold_checkbox_4.isChecked(
                        )
                        selected_sensor.set_threshold(float(self.threshold_high_lineedit_4.text(
                        )), metric_idx=3, to_machine=True, which_th=Motherboard.TH_HIGH)
                        selected_sensor.set_threshold(float(self.threshold_low_lineedit_4.text(
                        )), metric_idx=3, to_machine=True, which_th=Motherboard.TH_LOW)

                        self._debug.write(
                            "APP", F"Saving metric 4 from {sensor_str}")
        Motherboard.upload_sensor(selected_sensor, ser, self._debug)

    def on_connect_btn_pressed(self) -> None:
        """Open serial connection to the specified port."""
        self._debug.write(
            "APP", F"Trying to access motherbaord on port {self.port}")
        if ser.is_open:
            ser.close()
        ser.port = self.port

        try:
            ser.open()
        except Exception as e:
            self.show_error_message(str(e))

        if ser.is_open:
            self._debug.write(
                "COM", F"Serial port {self.port} is open.")
            (err, motherboard_id) = Motherboard.handle_ping(ser, self._debug)

            if(not err):
                self._debug.write("COM", F"Connected to {motherboard_id}")
                self.connect_btn.setEnabled(False)
                self.disconnect_btn.setVisible(True)
                self.port_combobox.setDisabled(True)
                self.save_btn.setEnabled(True)
                self.load_sensors()

        else:
            self._debug.write(
                "ERR", F"Serial port {self.port} is not open :(.")

            # loop.create_task(self.receive_serial_async())

    def load_sensors(self):
        self._connected_sensors = {}
        """request the connected sensors on the motherboard"""

        _sensors = []
        (_err, _sensors) = Motherboard.request_sensors(ser, self._debug)

        if (not _err):
            if len(_sensors) > 0:
                self.sensor_btn.setVisible(True)

            for s in _sensors:
                _name = s.get_name()
                _id = s.get_addr()

                _sensor_str = F"{_name} [{_id}]"
                self._debug.write("GUI", F"Adding Sensor: {_sensor_str}")

                self.sensor_combobox.addItem(_sensor_str)

                self._connected_sensors.update({
                    _sensor_str: s
                })

    # def load_sensor_data(self):
    #     for sensor_str, sensor in self._connected_sensors.items():
    #         Motherboard.load_data(sensor, self._debug)

    def on_disconnect_btn_pressed(self) -> None:
        """Close current serial connection."""

        Motherboard.close(ser, self._debug)

        if ser.is_open:
            ser.close()

    def on_send_btn_pressed(self) -> None:
        """Send message to serial port."""
        msg = self.msg_lineedit.text() + '\r\n'
        loop.call_soon(send_serial_async, msg)

    async def receive_serial_async(self) -> None:
        """Wait for incoming data, convert it to text and add to Textedit."""
        while True:
            msg = ser.readline()
            if msg != b'':
                text = msg.decode().strip()
                self.received_textedit.appendPlainText(text)
            await asyncio.sleep(0)


if __name__ == '__main__':
    appctxt = ApplicationContext()       # 1. Instantiate ApplicationContext
    app = QApplication([])
    loop = QEventLoop()
    asyncio.set_event_loop(loop)

    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt5'))

    app.setOrganizationName('Dramco')
    app.setApplicationName('IWAST Configurator')
    w = RemoteWidget()
    w.show()

    exit_code = appctxt.app.exec_()      # 2. Invoke appctxt.app.exec_()
    sys.exit(exit_code)

    with loop:
        loop.run_forever()

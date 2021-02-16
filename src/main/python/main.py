import asyncio
import sys
from typing import Iterator, Tuple

import serial
from fbs_runtime.application_context.PyQt5 import ApplicationContext

from PyQt5.QtGui import QCloseEvent
from PyQt5.QtWidgets import (QApplication, QCheckBox, QComboBox, QGridLayout,
                             QLabel, QLineEdit, QMessageBox, QPlainTextEdit,
                             QPushButton, QWidget)
from quamash import QEventLoop
from serial.tools.list_ports import comports

import ATCommands as Motherboard
import qdarkstyle
from CustomDebug import CustomDebug
import PowerReport

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

VERSION = "version 2.1 by Pierre Verhulst (from V1.0 by Gilles Callebaut) "


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
        self.resize(700, 500)

        # Varibles for PowerReport
        self.window_power_r = None
        self.power_config_name = []
        self.power_config_id = []
        self.power_th = []
        self.power_pol = []
        self.power_data_acc = False

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

        # New Configuration Button
        self.new_config_btn = QPushButton(self.tr('New'))
        self.new_config_btn.setVisible(False)
        self.new_config_btn.pressed.connect(self.on_new_config_pressed)

        # poll messages
        # Enabled?
        # self.poll_checkbox = QCheckBox("Poll?", self)
        # self.poll_checkbox.stateChanged.connect(self.click_poll_sensor)
        # Seconds
        self.poll_label = QLabel(self.tr('Poll interval (minutes):'))
        self.poll_lineedit = QLineEdit()
        self.poll_label.setBuddy(self.poll_lineedit)
        self.poll_label.setVisible(False)
        self.poll_lineedit.setEnabled(True)
        self.poll_lineedit.setVisible(False)
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

        # Power Report Button
        self.power_report_btn = QPushButton(self.tr('Power Report'))
        self.power_report_btn.setVisible(False)
        self.power_report_btn.pressed.connect(self.on_power_report_btn_pressed)

        # Data Accumulation Enabling/Disabling
        self.accumulation_checkbox = QCheckBox("Data Accumulation ?", self)
        self.accumulation_checkbox.stateChanged.connect(self.click_accumulation_checkbox)
        self.accumulation_checkbox.setVisible(False)

        # Arrange Layout
        layout = QGridLayout()

        # COM Port line
        layout.addWidget(self.port_label, 0, 0)
        layout.addWidget(self.port_combobox, 0, 1, 1, 3)
        layout.addWidget(self.connect_btn, 0, 4)
        layout.addWidget(self.refresh_com_ports_btn, 0, 5)
        # layout.addWidget(self.port_motherboard, 0, 1, 2)

        # Sensors line
        layout.addWidget(self.sensor_label, 1, 0)
        layout.addWidget(self.sensor_combobox, 1, 1, 1, 3)
        layout.addWidget(self.sensor_btn, 1, 4)
        layout.addWidget(self.save_btn, 1, 5)

        # Polling line

        # layout.addWidget(self.poll_checkbox, 2, 0)
        layout.addWidget(self.poll_label, 3, 1)
        layout.addWidget(self.poll_lineedit, 3, 2)

        # threshold line

        layout.addWidget(self.threshold_label_1, 4, 0)
        layout.addWidget(self.threshold_checkbox_1, 4, 1)
        layout.addWidget(self.threshold_high_label_1, 4, 2)
        layout.addWidget(self.threshold_high_lineedit_1, 4, 3)
        layout.addWidget(self.threshold_low_label_1, 4, 4)
        layout.addWidget(self.threshold_low_lineedit_1, 4, 5)

        layout.addWidget(self.threshold_label_2, 5, 0)
        layout.addWidget(self.threshold_checkbox_2, 5, 1)
        layout.addWidget(self.threshold_high_label_2, 5, 2)
        layout.addWidget(self.threshold_high_lineedit_2, 5, 3)
        layout.addWidget(self.threshold_low_label_2, 5, 4)
        layout.addWidget(self.threshold_low_lineedit_2, 5, 5)

        layout.addWidget(self.threshold_label_3, 6, 0)
        layout.addWidget(self.threshold_checkbox_3, 6, 1)
        layout.addWidget(self.threshold_high_label_3, 6, 2)
        layout.addWidget(self.threshold_high_lineedit_3, 6, 3)
        layout.addWidget(self.threshold_low_label_3, 6, 4)
        layout.addWidget(self.threshold_low_lineedit_3, 6, 5)

        layout.addWidget(self.threshold_label_4, 7, 0)
        layout.addWidget(self.threshold_checkbox_4, 7, 1)
        layout.addWidget(self.threshold_high_label_4, 7, 2)
        layout.addWidget(self.threshold_high_lineedit_4, 7, 3)
        layout.addWidget(self.threshold_low_label_4, 7, 4)
        layout.addWidget(self.threshold_low_lineedit_4, 7, 5)

        # Debug
        layout.addWidget(self.debug_label, 8, 0)
        layout.addWidget(self.debug_textedit, 9, 0, 1, 6)

        # Save and disconnect layout
        layout.addWidget(self.disconnect_btn, 10, 5)

        # Power Report Button
        layout.addWidget(self.power_report_btn, 10, 0)

        # Accumulation Checkbox
        layout.addWidget(self.accumulation_checkbox, 2, 1)

        # New Configuration Button
        layout.addWidget(self.new_config_btn, 10, 4)

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
        self.poll_lineedit.setVisible(False)
        self.poll_label.setVisible(False)

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
        Motherboard.load_data(selected_sensor, self._debug, ser)
        # self.poll_checkbox.setCheckState(selected_sensor._polling_enabled)
        if selected_sensor.get_name() == 'Button Sensor':
            self.poll_label.setVisible(False)
            self.poll_lineedit.setVisible(False)
            self.poll_lineedit.setEnabled(False)
        else:
            self.poll_label.setVisible(True)
            self.poll_lineedit.setVisible(True)
            self.poll_lineedit.setEnabled(True)
            self.poll_lineedit.setText(str(selected_sensor._polling_interval_sec // 60))

        for idx, (th_e, th_h, th_l, label) in enumerate(zip(selected_sensor._thresholds_enabled,
                                                            selected_sensor.get_thresholds(which_th=Motherboard.TH_HIGH,
                                                                                           to_machine=False),
                                                            selected_sensor.get_thresholds(which_th=Motherboard.TH_LOW,
                                                                                           to_machine=False),
                                                            selected_sensor._metric_labels)):
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

    def on_power_report_btn_pressed(self):
        """Display Power Measurement for the selected configuration """
        # TODO
        if self.window_power_r is None:
            self.power_report_btn.setVisible(False)
            nb_bd = len(self.power_config_id)

            if nb_bd == 0:
                self.window_power_r = PowerReport.PowerReport(data_acc=self.power_data_acc)
            elif nb_bd == 1:
                self.window_power_r = PowerReport.PowerReport(data_acc=self.power_data_acc,
                                                              id_config_1=self.power_config_id[0],
                                                              poll_interval_1=self.power_pol[0],
                                                              thresholds_1=self.power_th[0])
            elif nb_bd == 2:
                self.window_power_r = PowerReport.PowerReport(data_acc=self.power_data_acc,
                                                              id_config_1=self.power_config_id[0],
                                                              poll_interval_1=self.power_pol[0],
                                                              thresholds_1=self.power_th[0],
                                                              id_config_2=self.power_config_id[1],
                                                              poll_interval_2=self.power_pol[1],
                                                              thresholds_2=self.power_th[1])
            elif nb_bd == 3:
                self.window_power_r = PowerReport.PowerReport(data_acc=self.power_data_acc,
                                                              id_config_1=self.power_config_id[0],
                                                              poll_interval_1=self.power_pol[0],
                                                              thresholds_1=self.power_th[0],
                                                              id_config_2=self.power_config_id[1],
                                                              poll_interval_2=self.power_pol[1],
                                                              thresholds_2=self.power_th[1],
                                                              id_config_3=self.power_config_id[2],
                                                              poll_interval_3=self.power_pol[2],
                                                              thresholds_3=self.power_th[2])
            elif nb_bd == 4:
                self.window_power_r = PowerReport.PowerReport(data_acc=self.power_data_acc,
                                                              id_config_1=self.power_config_id[0],
                                                              poll_interval_1=self.power_pol[0],
                                                              thresholds_1=self.power_th[0],
                                                              id_config_2=self.power_config_id[1],
                                                              poll_interval_2=self.power_pol[1],
                                                              thresholds_2=self.power_th[1],
                                                              id_config_3=self.power_config_id[2],
                                                              poll_interval_3=self.power_pol[2],
                                                              thresholds_3=self.power_th[2],
                                                              id_config_4=self.power_config_id[3],
                                                              poll_interval_4=self.power_pol[3],
                                                              thresholds_4=self.power_th[3])
            elif nb_bd == 5:
                self.window_power_r = PowerReport.PowerReport(data_acc=self.power_data_acc,
                                                              id_config_1=self.power_config_id[0],
                                                              poll_interval_1=self.power_pol[0],
                                                              thresholds_1=self.power_th[0],
                                                              id_config_2=self.power_config_id[1],
                                                              poll_interval_2=self.power_pol[1],
                                                              thresholds_2=self.power_th[1],
                                                              id_config_3=self.power_config_id[2],
                                                              poll_interval_3=self.power_pol[2],
                                                              thresholds_3=self.power_th[2],
                                                              id_config_4=self.power_config_id[3],
                                                              poll_interval_4=self.power_pol[3],
                                                              thresholds_4=self.power_th[3],
                                                              id_config_5=self.power_config_id[4],
                                                              poll_interval_5=self.power_pol[4],
                                                              thresholds_5=self.power_th[4])
            elif nb_bd == 6:
                self.window_power_r = PowerReport.PowerReport(data_acc=self.power_data_acc,
                                                              id_config_1=self.power_config_id[0],
                                                              poll_interval_1=self.power_pol[0],
                                                              thresholds_1=self.power_th[0],
                                                              id_config_2=self.power_config_id[1],
                                                              poll_interval_2=self.power_pol[1],
                                                              thresholds_2=self.power_th[1],
                                                              id_config_3=self.power_config_id[2],
                                                              poll_interval_3=self.power_pol[2],
                                                              thresholds_3=self.power_th[2],
                                                              id_config_4=self.power_config_id[3],
                                                              poll_interval_4=self.power_pol[3],
                                                              thresholds_4=self.power_th[3],
                                                              id_config_5=self.power_config_id[4],
                                                              poll_interval_5=self.power_pol[4],
                                                              thresholds_5=self.power_th[4],
                                                              id_config_6=self.power_config_id[5],
                                                              poll_interval_6=self.power_pol[5],
                                                              thresholds_6=self.power_th[5])
            self.window_power_r.show()

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

    def click_accumulation_checkbox(self):
        (err, acc_confirm) = Motherboard.set_accumulation(
            ser, self._debug, enable=self.accumulation_checkbox.isChecked())
        if (not err):
            self._debug.write("APP", F"Accumulation {acc_confirm}")
        self.power_data_acc = self.accumulation_checkbox.isChecked()

    def on_save_btn_pressed(self):
        sensor_str = self.sensor_combobox.currentText()
        selected_sensor = self._connected_sensors[sensor_str]
        self._debug.write("APP", F"Saving data from {sensor_str}")
        # check which metrics are visible
        # update data from input to selected_sensor object
        # update motherboard

        # selected_sensor._polling_enabled = self.poll_checkbox.isChecked()
        if selected_sensor.get_name() != 'Button Sensor':
            selected_sensor._polling_interval_sec = int(self.poll_lineedit.text()) * 60

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

        # For the power report -----------------------------------------------------------------------------------------
        idc = self.power_config_name.index(selected_sensor.get_name())
        if selected_sensor.get_polling_interval_sec() != 65535:
            if selected_sensor.get_polling_interval_sec() != 0:
                self.power_pol[idc] = int(selected_sensor.get_polling_interval_sec()/60)
        flag = False
        for metrics in range(selected_sensor.get_num_metrics()):
            if selected_sensor.get_thresholds_enabled(metrics) is True:
                flag = True
                break
        if flag is True:
            self.power_th[idc] = True
            if selected_sensor.get_name() == 'Power Sensor':
                self.power_config_id[idc] = 3
            elif selected_sensor.get_name() == 'Sound Sensor':
                self.power_config_id[idc] = 5
            elif selected_sensor.get_name() == 'Environmental Sensor':
                self.power_config_id[idc] = 7
        else:
            self.power_th[idc] = False
            if selected_sensor.get_name() == 'Power Sensor':
                self.power_config_id[idc] = 2
            elif selected_sensor.get_name() == 'Sound Sensor':
                self.power_config_id[idc] = 4
            elif selected_sensor.get_name() == 'Environmental Sensor':
                self.power_config_id[idc] = 6

        if self.window_power_r is not None:
            self.window_power_r = None
            self.power_report_btn.setVisible(True)
        # --------------------------------------------------------------------------------------------------------------

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

            if (not err):
                self._debug.write("COM", F"Connected to {motherboard_id}")
                self.connect_btn.setEnabled(False)
                self.disconnect_btn.setVisible(True)
                self.disconnect_btn.pressed.connect(self.on_disconnect_btn_pressed)
                self.sensor_btn.pressed.connect(self.on_sensor_btn_pressed)
                self.save_btn.pressed.connect(self.on_save_btn_pressed)
                self.port_combobox.setDisabled(True)
                self.save_btn.setEnabled(True)
                self.load_sensors()

            (err2, acc_state) = Motherboard.request_acc(ser, self._debug)

            if (not err2):
                self.accumulation_checkbox.setVisible(True)
                self.accumulation_checkbox.setCheckState(acc_state)

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

                # For the power report ---------------------------------------------------------------------------------
                self.power_config_name.append(_name)
                if _name == 'Button Sensor':
                    self.power_config_id.append(1)
                elif _name == 'Power Sensor':
                    self.power_config_id.append(2)
                elif _name == 'Sound Sensor':
                    self.power_config_id.append(4)
                elif _name == 'Environmental Sensor':
                    self.power_config_id.append(6)
                self.power_pol.append(False)
                self.power_th.append(False)
                self.power_report_btn.setVisible(True)
                # ------------------------------------------------------------------------------------------------------

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
        self.disconnect_btn.pressed.disconnect()
        self.new_config_btn.setVisible(True)
        self.save_btn.pressed.disconnect()
        self.sensor_btn.pressed.disconnect()
        Motherboard.close(ser, self._debug)

        if ser.is_open:
            ser.close()
        self.update_com_ports()

    def on_send_btn_pressed(self) -> None:
        """Send message to serial port."""
        msg = self.msg_lineedit.text() + '\r\n'
        loop.call_soon(send_serial_async, msg)

    def on_new_config_pressed(self):
        """Reset all variables to restart a new configuration"""
        self._connected_sensors = {}
        self.window_power_r = None
        self.power_config_name = []
        self.power_config_id = []
        self.power_th = []
        self.power_pol = []
        self.power_data_acc = False

        self._debug = CustomDebug(self.debug_textedit)
        self.update_com_ports()

        self.remove_metric_rows_from_gui()
        self._debug.write("GUI", "Application started successfully")
        self._debug.write("GUI", VERSION)
        self.update_com_ports()

        self.sensor_combobox.clear()
        self.sensor_btn.setVisible(False)
        self.save_btn.setVisible(False)
        self.accumulation_checkbox.setVisible(False)
        self.new_config_btn.setVisible(False)
        self.disconnect_btn.setVisible(False)
        self.connect_btn.setEnabled(True)
        self.port_combobox.setEnabled(True)

    async def receive_serial_async(self) -> None:
        """Wait for incoming data, convert it to text and add to Textedit."""
        while True:
            msg = ser.readline()
            if msg != b'':
                text = msg.decode().strip()
                self.received_textedit.appendPlainText(text)
            await asyncio.sleep(0)


if __name__ == '__main__':
    appctxt = ApplicationContext()  # 1. Instantiate ApplicationContext
    app = QApplication([])
    loop = QEventLoop()
    asyncio.set_event_loop(loop)

    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt5'))

    app.setOrganizationName('Dramco')
    app.setApplicationName('IWAST Configurator')
    w = RemoteWidget()
    w.show()

    exit_code = appctxt.app.exec_()  # 2. Invoke appctxt.app.exec_()
    sys.exit(exit_code)

    with loop:
        loop.run_forever()

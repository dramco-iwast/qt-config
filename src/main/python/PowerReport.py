from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QGridLayout, QLabel, QPushButton, QWidget, QSlider,
                             QScrollArea, QSpinBox, QTabWidget, QErrorMessage, QFileDialog)
import math
import requests
from bs4 import BeautifulSoup
import pandas as pd
import io
import ReportPDF

# ---- Constant ----
URL_GITHUB = 'https://raw.githubusercontent.com/dramco-iwast/docs/master/Power_Data.csv'
DEBUG = False
BATTERY = 500  # in mAh
ERROR_AVER_CUR_SLEEP = 1.26
ERROR_AVER_CUR_TX = 8000
ERROR_DATA_TX_TIME = [24.12, 35.05, 45.5, 126.15, 249.12, 495.61]
ERROR_DATA_TX_TIME_ACC = [30.06, 55.71, 107, 127.29, 332.24, 661.31]


class PowerReport(QWidget):
    """Second window to manage the power report"""

    def __init__(self, data_acc,
                 id_config_1=False, poll_interval_1=False, thresholds_1=False,
                 id_config_2=False, poll_interval_2=False, thresholds_2=False,
                 id_config_3=False, poll_interval_3=False, thresholds_3=False,
                 id_config_4=False, poll_interval_4=False, thresholds_4=False,
                 id_config_5=False, poll_interval_5=False, thresholds_5=False,
                 id_config_6=False, poll_interval_6=False, thresholds_6=False,):
        super().__init__()

        self.resize(1000, 600)
        self.move(300, 150)

        # --------------------------------------------------------------------------------------------------------------
        #       DECLARE ATTRIBUTES
        # --------------------------------------------------------------------------------------------------------------

        self.__data_acc = data_acc          # Data accumulation ?       (if 'False' -> No Data acc)
        self.__id = []                      # ID(s) of the board(s) used
        self.__poll_interval = []           # Polling(s) Interval(s)    (if 'False' -> No Polling)
        self.__thresholds = []              # Threshold(s) ?            (if 'False' -> No Thresholds)
        self.__id_name = []                 # ID(s) name(s) of the board(s) used
        self.__number_metrics = []          # Number(s) of metrics of each boards
        self.__lora_spread_factor = 11      # LoRa spreading factor     (default -> 11)

        self.__id.append(id_config_1)                   # ID of the configuration 1
        self.__poll_interval.append(poll_interval_1)    # Polling interval in min ? (if 'False' -> No Polling)
        self.__thresholds.append(thresholds_1)          # Thresholds ?              (if 'False' -> No Thresholds)

        self.__id.append(id_config_2)                   # ID of the configuration 2
        self.__poll_interval.append(poll_interval_2)    # Polling interval in min ? (if 'False' -> No Polling)
        self.__thresholds.append(thresholds_2)          # Thresholds ?              (if 'False' -> No Thresholds)

        self.__id.append(id_config_3)                   # ID of the configuration 3
        self.__poll_interval.append(poll_interval_3)    # Polling interval in min ? (if 'False' -> No Polling)
        self.__thresholds.append(thresholds_3)          # Thresholds ?              (if 'False' -> No Thresholds)

        self.__id.append(id_config_4)                   # ID of the configuration 4
        self.__poll_interval.append(poll_interval_4)    # Polling interval in min ? (if 'False' -> No Polling)
        self.__thresholds.append(thresholds_4)          # Thresholds ?              (if 'False' -> No Thresholds)

        self.__id.append(id_config_5)                   # ID of the configuration 5
        self.__poll_interval.append(poll_interval_5)    # Polling interval in min ? (if 'False' -> No Polling)
        self.__thresholds.append(thresholds_5)          # Thresholds ?              (if 'False' -> No Thresholds)

        self.__id.append(id_config_6)                   # ID of the configuration 6
        self.__poll_interval.append(poll_interval_6)    # Polling interval in min ? (if 'False' -> No Polling)
        self.__thresholds.append(thresholds_6)          # Thresholds ?              (if 'False' -> No Thresholds)

        # Thresholds parameters (depends on the board -> we use an array for each parameters)
        self.__number_possible_thresh = []              # Nbr possible thresholds when there is a threshold interval
        self.__number_thresh_exceeded = []              # Nbr of excedeed thresholds (must be choose by the user !)
        self.__number_thresh_not_exceeded = []          # Nbr of non-exceeded thresholds
        self.__energy_thresh_exceeded = []              # Energy of an exceeded threshold event     [uWh]
        self.__energy_thresh_not_exceeded = []          # Energy of a non-exceeded threshold event  [uWh]
        self.__time_thresh_exceeded = []                # Time of an exceeded threshold event       [ms]
        self.__time_thresh_not_exceeded = []            # Time of a non-exceeded threshold event    [ms]
        self.__threshold_interval = []                  # Time for the thresholds intervall (if it exists)   [ms]

        # Polling parameters (depends on the board -> we use an array for each parameters)
        self.__number_polling_occurs = []               # Total number of pollings interrupts
        self.__time_polling_occurs = []                 # Time for a polling event      [ms]
        self.__energy_polling_occurs = []               # Energy for a polling event    [uWh]

        # LoRa message parameters (depends on the board -> we use an array for each parameters)
        self.__time_wut_data = []                       # Time for the "Wake-Up Transceiver" part   [ms]
        self.__energy_wut_data = []                     # Energy for the "Wake-Up Transceiver" part [uWh]
        self.__aver_cur_data_transmission = []          # Aver. Current for the transmission part   [uA]
        self.__time_data_transmission = []              # Time for the transmission part            [ms]
        self.__energy_data_transmission = []            # Energy for the transmission part          [uWh]
        self.__time_data_reception = []                 # Time for the receiving part               [ms]
        self.__energy_data_reception = []               # Energy for the receiving part             [uWh]
        self.__sending_castle_time = []                 # Total time for a LoRa castle (=WUT+TX+RX)     [ms]
        self.__sending_castle_energy = []               # Total energy for a LoRa castle (=WUT+TX+RX)   [uWh]
        self.__sending_castle_energy_max = []           # Total energy for a LoRa castle (+Error on TX) [uWh]

        # Max Peak Value
        self.__max_peak_value = 0           # Maximum peak current depending on all data [mA]

        # Static Energy (depends on the board -> we use an array for parameters who depend on the board)
        self.__time_static_energy = []      # Time for the static energy of a specific board        [ms]
        self.__power_static_energy = []     # Aver. Power for the static energy of a specific board [uW]
        self.__static_energy = 0            # Total static energy for the complete system           [uWh]
        self.__static_energy_max = 0        # Total static energy for the complete system (with error max) [uWh]
        self.__static_energy_min = 0        # Total static energy for the complete system (with error min) [uWh]
        self.__static_time = 0              # Total static time for the complete system    [ms]
        self.__percent_static_time = 100    # Percent of the static time                   [%]

        # Dynamic Energy (depends on the board -> we use an array for parameters who depend on the board)
        self.__time_dyn_data_energy = []    # Time for the "dynamic-data" energy of a specific board        [ms]
        self.__dyn_data_energy = 0          # Energy for the "dynamic-data" energy of the complete system   [uWh]
        self.__dyn_send_time = 0            # Time for the "dynamic-send" energy of the motherboard         [ms]
        self.__dyn_send_energy = 0          # Energy for the "dynamic-send" energy of the motherboard       [uWh]
        self.__dyn_send_energy_max = 0      # Energy for the "dynamic-send" energy of the motherboard (+Error TX)  [uWh]

        # Total Aver. Consumption
        self.__total_aver_cons = 0          # Total aver. consumption for the complete system                   [uWh]
        self.__total_aver_cons_max = 0      # Total aver. consumption for the complete system (with error max)  [uWh]
        self.__total_aver_cons_min = 0      # Total aver. consumption for the complete system (with error min)  [uWh]

        # Status LoRa message parameters
        self.__wut_st_time = 0              # Time for the "Wake-Up Transceiver" part   [ms]
        self.__wut_st_energy = 0            # Energy for the "Wake-Up Transceiver" part [uWh]
        self.__data_tx_st_aver_cur = 0      # Aver. Current for the transmission part   [uA]
        self.__data_rx_st_time = 0          # Time for the transmission part            [ms]
        self.__data_rx_st_energy = 0        # Energy for the transmission part          [uWh]
        self.__time_st = 0                  # Total time for the Status LoRa castle (=WUT+TX+RX)     [ms]
        self.__energy_st = 0                # Total energy for the Status LoRa castle (=WUT+TX+RX)   [uWh]
        self.__energy_st_max = 0            # Total energy for the Status LoRa castle (+Error on TX) [uWh]

        # Wake-Up motherboard event
        self.__time_wum = 0                 # Time for a "Wake-Up Motherboard" event        [ms]
        self.__number_wum = 5760            # This event occurs each with the new firmware
        self.__energy_wum = 0               # Energy for a "Wake-Up Motherboard" event      [uWh]

        # Accumulation data parameters (depends on the board -> we use an array for parameters who depend on the board)
        self.__acc_data_send_nb = 0         # Number of accumulated message that are sent by the motherboard
        self.__lora_acc_thresholds = 30     # Limit of bytes for an accumulated message
        self.__time_store_data = []         # Time to store one metric in the motherboard for a specific board    [ms]
        self.__energy_store_data = []       # Energy to store one metric in the motherboard for a specific board  [uWh]
        self.__number_storing_msg = []      # Number of storing event for a specific board

        # Battery
        self.__life_estimation = 0          # Estimation of the lifetime for the complete system             [ms]
        self.__life_estimation_min = 0      # Estimation of the lifetime for the complete system (min. life) [ms]

        # PDF report
        colonnes = 6
        lignes = 64
        self.data_pdf = [['/'] * colonnes for _ in range(lignes)]
        self.section_pdf = [0, 7, 14, 21, 28, 35, 42, 49, 56]
        self.pdf_data_date = ""

        # --------------------------------------------------------------------------------------------------------------
        #       DESCRIPTION
        # --------------------------------------------------------------------------------------------------------------

        self.description_config_title = QLabel()
        self.description_config_title.setText("Configuration:")

        self.description_config = QLabel()

        # --------------------------------------------------------------------------------------------------------------
        #       POWER MEASUREMENT DATA
        # --------------------------------------------------------------------------------------------------------------
        self.tabs = QTabWidget()
        self.scrollDataWidget = self.config_data_widget()
        self.tabs.addTab(self.scrollDataWidget, "Measurement Data")

        # Collect number of pollings
        for id_c in range(len(self.__id)):
            if self.get_id(id_c) is not False:
                if self.get_poll_interval(id_c) is not False or self.get_poll_interval(id_c) != 0:
                    self.append_number_polling_occurs(int(1440 / self.get_poll_interval(id_c)))
                else:
                    self.append_number_polling_occurs(0)
            else:
                self.append_number_polling_occurs(0)

        # Collect number of thresholds not exceeded
        self.determine_number_thresh_not_exceeded()

        # Collect number of storing event (if data accumulation is enable)
        if self.get_data_acc() is True:
            self.determine_number_storing_msg()

        # --------------------------------------------------------------------------------------------------------------
        #       EVENT WIDGET
        # --------------------------------------------------------------------------------------------------------------

        self.event_config_title = QLabel()
        self.event_config_title.setText("Events for a day:")

        self.event_config = self.config_event_widget()
        self.event_config.setMaximumWidth(400)

        # Determine the number of message sending (if data accumulation is enabled)
        if self.get_data_acc() is True:
            self.determine_number_acc_send()

        # Determine an estimation of the total consumption of the system
        self.determine_total_average_cons()

        # --------------------------------------------------------------------------------------------------------------
        #       GRAPHICS WIDGET
        # --------------------------------------------------------------------------------------------------------------

        self.graphics = self.config_graphic_widget()
        self.tabs.addTab(self.graphics, "LoRa Castles")

        # --------------------------------------------------------------------------------------------------------------
        #       CONSUMPTION SUMMARY
        # --------------------------------------------------------------------------------------------------------------

        self.summary_consumption_title = QLabel()
        self.summary_consumption_title.setText("Consumption Summary:")

        self.summary_consumption = QWidget()
        self.summary_consumption_layout = QGridLayout()

        # Determine Max Peak Value
        self.max_peak_value_label = QLabel(self.tr('Maximum peak current: '))
        max_peak_value_tr = self.get_max_peak_value()
        if max_peak_value_tr // 1000 >= 1.0:
            max_peak_value_tr /= 1000
            self.max_peak_value_n = QLabel(self.tr(str(max_peak_value_tr) + ' mA'))
        else:
            self.max_peak_value_n = QLabel(self.tr(str(max_peak_value_tr) + ' uA'))

        # Determine total time in static mode
        self.set_percent_static_time(round(self.get_static_time() / 864000, 3))
        self.sleep_time_label = QLabel(self.tr('Total sleep time: '))
        self.sleep_time_value_label = QLabel(
            self.tr(self.better_sleep_time(int(self.get_static_time() / 1000)) + ' (' + str(
                self.get_percent_static_time()) + ' %)'))

        # Determine total average consumption
        self.average_total_consumption_label = QLabel(self.tr('Average total consumption: '))
        self.average_total_consumption_max_label = QLabel(self.tr('Maximum: '))
        self.average_total_consumption_max_label.setAlignment(Qt.AlignRight)
        self.average_total_consumption_min_label = QLabel(self.tr('Minimum: '))
        self.average_total_consumption_min_label.setAlignment(Qt.AlignRight)
        self.average_total_consumption = QLabel(self.tr(str(round(self.get_total_aver_cons(), 2)) + ' uWh'))
        self.average_total_consumption.setStyleSheet("border-width: 1px; border-style: solid; border-radius: 0px;")
        self.average_total_consumption_max = QLabel(self.tr(str(round(self.get_total_aver_cons_max(), 2)) + ' uWh'))
        self.average_total_consumption_min = QLabel(self.tr(str(round(self.get_total_aver_cons_min(), 2)) + ' uWh'))

        # Determine lifetime battery estimation
        self.determine_lifetime()
        self.lifetime_label = QLabel(self.tr('Estimated life time: '))
        self.lifetime_value_label = QLabel(self.tr(
            str(self.get_life_estimation())+' (min: '+str(self.get_life_estimation_min())+')'))

        self.summary_consumption_layout.addWidget(self.max_peak_value_label, 3, 0)
        self.summary_consumption_layout.addWidget(self.max_peak_value_n, 3, 1)
        self.summary_consumption_layout.addWidget(self.sleep_time_label, 4, 0)
        self.summary_consumption_layout.addWidget(self.sleep_time_value_label, 4, 1)
        self.summary_consumption_layout.addWidget(self.average_total_consumption_label, 0, 0)
        self.summary_consumption_layout.addWidget(self.average_total_consumption_max_label, 1, 0)
        self.summary_consumption_layout.addWidget(self.average_total_consumption_min_label, 2, 0)
        self.summary_consumption_layout.addWidget(self.average_total_consumption, 0, 1)
        self.summary_consumption_layout.addWidget(self.average_total_consumption_max, 1, 1)
        self.summary_consumption_layout.addWidget(self.average_total_consumption_min, 2, 1)
        self.summary_consumption_layout.addWidget(self.lifetime_label, 5, 0)
        self.summary_consumption_layout.addWidget(self.lifetime_value_label, 5, 1)

        self.summary_consumption.setLayout(self.summary_consumption_layout)

        # --------------------------------------------------------------------------------------------------------------
        #       OTHERS
        # --------------------------------------------------------------------------------------------------------------

        link_template = '<a href={0}>{1}</a>'
        self.measurement_table_link = QLabel()
        self.measurement_table_link.setOpenExternalLinks(True)
        self.measurement_table_link.setText(link_template.format(URL_GITHUB, 'Access the table'))

        self.exit_button = QPushButton(self.tr('Exit'))
        self.exit_button.pressed.connect(self.on_exit_button)

        self.print_button = QPushButton(self.tr('Print PDF'))
        self.print_button.pressed.connect(self.on_print_button)

        self.debug()

        # --------------------------------------------------------------------------------------------------------------

        layout = QGridLayout()
        layout.addWidget(self.description_config_title, 0, 0)
        layout.addWidget(self.description_config, 1, 0)
        layout.addWidget(self.event_config_title, 4, 0)
        layout.addWidget(self.event_config, 5, 0, 9, 1)
        layout.addWidget(self.summary_consumption_title, 0, 1, 1, 4)
        layout.addWidget(self.summary_consumption, 1, 1, 3, 2)
        layout.addWidget(self.measurement_table_link, 15, 0)
        layout.addWidget(self.exit_button, 15, 4)
        layout.addWidget(self.print_button, 15, 3)
        layout.addWidget(self.tabs, 4, 1, 10, 4)
        self.setLayout(layout)

    def config_data_widget(self):
        """Create the data  widget table"""

        id_config = [0]                         # motherboard ID
        for idc in range(len(self.__id)):
            id_config.append(self.get_id(idc))  # sensor boards ID

        for idc in range(len(id_config)):
            if id_config[idc] is False:
                id_config[idc] = 1000           # if no sensor boards -> ID = 1000

        data_csv = self.collect_csv()

        # Collect date of the measurement of the motherboard
        date = data_csv.iat[0, 2]
        self.pdf_data_date = date

        # Collect Number of metrics per board
        for id_c in range(len(id_config)):
            if id_c != 0:
                if id_config[id_c] != 1000:
                    self.append_number_metrics(int(data_csv.iat[id_config[id_c], 51]))
                else:
                    self.append_number_metrics(0)

        # Collect LoRa Castles Characteristics
        if self.get_data_acc() is False:
            for id_c in range(len(id_config)):
                if id_c != 0:
                    if id_config[id_c] != 1000:
                        if data_csv.iat[id_config[id_c], 40] != 'No data':
                            self.append_energy_wut_data(float(data_csv.iat[id_config[id_c], 40]))
                            self.append_time_wut_data(float(data_csv.iat[id_config[id_c], 41]))
                            self.append_aver_cur_data_transmission(float(data_csv.iat[id_config[id_c], 42]))
                            self.append_energy_data_reception(float(data_csv.iat[id_config[id_c], 43]))
                            self.append_time_data_reception(float(data_csv.iat[id_config[id_c], 44]))
                            self.append_sending_castle_time(0)
                            self.append_sending_castle_energy(0)
                            self.append_sending_castle_energy_max(0)
                            self.determine_sending_message(id_c - 1)
                        else:
                            self.append_energy_wut_data(0)
                            self.append_time_wut_data(0)
                            self.append_aver_cur_data_transmission(0)
                            self.append_energy_data_reception(0)
                            self.append_time_data_reception(0)
                            self.append_sending_castle_time(0)
                            self.append_sending_castle_energy(0)
                            self.append_sending_castle_energy_max(0)
                    else:
                        self.append_energy_wut_data(0)
                        self.append_time_wut_data(0)
                        self.append_aver_cur_data_transmission(0)
                        self.append_energy_data_reception(0)
                        self.append_time_data_reception(0)
                        self.append_sending_castle_time(0)
                        self.append_sending_castle_energy(0)
                        self.append_sending_castle_energy_max(0)
        else:  # Data Acc is true
            self.append_energy_wut_data(float(data_csv.iat[5, 45]))
            self.append_time_wut_data(float(data_csv.iat[5, 46]))
            self.append_aver_cur_data_transmission(float(data_csv.iat[5, 47]))
            self.append_energy_data_reception(float(data_csv.iat[5, 48]))
            self.append_time_data_reception(float(data_csv.iat[5, 49]))
            self.append_sending_castle_time(0)
            self.append_sending_castle_energy(0)
            self.append_sending_castle_energy_max(0)
            self.determine_sending_message(0)

        # Collect Data storage informations
        if self.get_data_acc() is True:
            for id_c in range(len(id_config)):
                if id_c != 0:
                    self.append_number_storing_msg(0)
                    if id_config[id_c] != 1000:
                        self.append_time_store_data(float(data_csv.iat[id_config[id_c], 34]))
                        self.append_energy_store_data(float(data_csv.iat[id_config[id_c], 33]))
                    else:
                        self.append_time_store_data(0)
                        self.append_energy_store_data(0)

        # Collect Static Power for all the system
        self.append_time_static_energy(0)
        self.append_time_dyn_data_energy(0)
        for id_c in range(len(id_config)):
            if id_config[id_c] != 1000:
                self.append_power_static_energy((float(data_csv.iat[id_config[id_c], 7]))*3.3) # in uW
            else:
                self.append_power_static_energy(0)

            self.append_time_static_energy(0)
            self.append_time_dyn_data_energy(0)

        # Determine Characteristics of the WUM event
        self.set_energy_wum(float(data_csv.iat[id_config[0], 13]))
        self.set_time_wum(float(data_csv.iat[id_config[0], 14]))

        # Collect boards name for the description
        Texte1 = str()
        for id_c in range(len(id_config)):
            if id_c != 0 and id_config[id_c] != 1000:
                self.append_id_name(str(data_csv.iat[id_config[id_c], 4]))
                Texte1 += 'Board ' + str(id_c) + ' -> ' + str(self.get_id_name(id_c - 1)) + '\n'
        self.description_config.setText(Texte1)

        # Determine the status LoRa castle
        self.set_wut_st_time(float(data_csv.iat[id_config[0], 36]))
        self.set_wut_st_energy(float(data_csv.iat[id_config[0], 35]))
        self.set_data_tx_st_aver_cur(float(data_csv.iat[id_config[0], 37]))
        self.set_data_rx_st_time(float(data_csv.iat[id_config[0], 39]))
        self.set_data_rx_st_energy(float(data_csv.iat[id_config[0], 38]))

        self.determine_status_message()

        # Récupérer la période des thresholds en ms
        id_c = 1
        while id_c < len(id_config):
            if id_config[id_c] != 1000 and id_config[id_c] != 0 and self.get_thresholds(id_c - 1) is not False:
                self.append_threshold_interval(int(data_csv.iat[id_config[id_c], 50]))
            elif id_config[id_c] != 0:
                self.append_threshold_interval(0)
            id_c += 1

        # Collect all data and build the table
        data_label = []
        data_label_total = []
        data_header = [[], [], [], [], [], []]
        data_value = [[], [], [], [], [], []]
        data_value_nb = [[], [], [], [], [], []]
        data_total = [[], [], [], [], [], []]
        value_tempo = 0
        data_label_title = ['    -    Motherboard Wakes Up',
                            '    -    Threshold Not Exceeded',
                            '    -    Threshold Exceeded',
                            '    -    Polling Interrupt',
                            '    -    Saving data']

        data = QGridLayout()
        data.setSpacing(0)
        data.setVerticalSpacing(1)
        dataWidget = QWidget()
        dataWidget.setContentsMargins(0, 0, 0, 0)
        scrollDataWidget = QScrollArea()
        scrollDataWidget.setStyleSheet("border-width: 0px; border-radius: 0px;")

        dataWidget.setLayout(data)
        scrollDataWidget.setWidgetResizable(True)
        scrollDataWidget.setWidget(dataWidget)

        column_dep = 5        # We begin at the column n°6
        section = 1           # 6 sections (without the data castle section)
        number_rows = 0       # 6 rows by sections

        while section <= 6:
            if section == 1:
                data_label.append(QLabel(self.tr('1. ')))  # Item data_label (number_rows)
                data_label.append(QLabel(self.tr('Static Power/Sleep Mode')))  # Item data_label (number_rows+1)
            else:
                data_label.append(QLabel(self.tr(str(section) + '. ')))     # Item data_label (number_rows)
                data_label.append(
                    QLabel(self.tr('Dynamic Power ' + str(section - 2) + data_label_title[section-2])))   # Item data_label (number_rows+1)

            data_label.append(QLabel(self.tr('Average Current Value')))     # Item data_label (number_rows+2)
            data_label.append(QLabel(self.tr('Peak Current Value')))        # Item data_label (number_rows+3)
            data_label.append(QLabel(self.tr('Energy Value')))              # Item data_label (number_rows+4)
            data_label.append(QLabel(self.tr('Interval Time Value')))       # Item data_label (number_rows+5)

            data_label_total.append(QLabel(self.tr('Total')))
            data_total[section - 1].append(0)
            data_total[section - 1].append(0)
            data_total[section - 1].append(0)

            ligne_pdf = 0

            for id_c in range(len(id_config)):
                if id_config[id_c] == 1000:
                    data_header[section - 1].append(QLabel(self.tr('Nothing')))
                elif id_config[id_c] == 0:
                    data_header[section - 1].append(
                        QLabel(self.tr('Motherboard\nAlone')))  # Item data_header (id_c+section)
                else:
                    data_header[section - 1].append(QLabel(  # Item data_header (id_c+section)
                        self.tr(str(data_csv.iat[id_config[id_c], 4]) + '\nBoard')))

                if id_config[id_c] != 1000:
                    # Aver. Current Value
                    value_tempo = data_csv.iat[id_config[id_c], column_dep + 2 + ((section - 1) * 5)]
                    if value_tempo == 'No data':
                        data_value[section - 1].append(
                            QLabel(self.tr(value_tempo)))  # Item data_value[section-1][id_c*4]
                        data_value_nb[section - 1].append(0)  # Item data_value_nb[section-1][id_c*4]
                    else:
                        value_tempo = float(value_tempo)
                        data_total[section - 1][0] += value_tempo
                        data_value_nb[section - 1].append(value_tempo)
                        self.data_pdf[self.section_pdf[section-1]+ligne_pdf][1] = str(round(value_tempo, 2))
                        if value_tempo // 1000 >= 1.0:
                            value_tempo /= 1000
                            data_value[section - 1].append(QLabel(self.tr(str(round(value_tempo, 2)) + ' mA')))
                        else:
                            data_value[section - 1].append(QLabel(self.tr(str(round(value_tempo, 2)) + ' uA')))

                    # Max. Current Value
                    value_tempo = data_csv.iat[id_config[id_c], column_dep + ((section - 1) * 5)]
                    if value_tempo == 'No data':
                        data_value[section - 1].append(
                            QLabel(self.tr(value_tempo)))  # Item data_value[section-1][(id_c*4)+1]
                        data_value_nb[section - 1].append(0)  # Item data_value_nb[section-1][(id_c*4)+1]
                    else:
                        value_tempo = float(value_tempo)
                        data_total[section - 1][1] += value_tempo
                        data_value_nb[section - 1].append(value_tempo)
                        if value_tempo > self.get_max_peak_value():
                            self.set_max_peak_value(value_tempo)
                        if value_tempo // 1000 >= 1.0:
                            value_tempo /= 1000
                            data_value[section - 1].append(QLabel(self.tr(str(round(value_tempo, 2)) + ' mA')))
                        else:
                            data_value[section - 1].append(QLabel(self.tr(str(round(value_tempo, 2)) + ' uA')))

                    # Energy
                    value_tempo = data_csv.iat[id_config[id_c], column_dep + 3 + ((section - 1) * 5)]
                    if value_tempo == 'No data':
                        data_value[section - 1].append(
                            QLabel(self.tr(value_tempo)))  # Item data_value[section-1][(id_c*4)+2]
                        data_value_nb[section - 1].append(0)  # Item data_value_nb[section-1][(id_c*4)+2]
                    else:
                        data_total[section - 1][2] += float(value_tempo)
                        data_value[section - 1].append(QLabel(self.tr((str(round(float(value_tempo), 2))) + ' uWh')))
                        data_value_nb[section - 1].append(float(value_tempo))
                        self.data_pdf[self.section_pdf[section-1]+ligne_pdf][4] = str(round(float(value_tempo), 2))

                    # Interval time
                    value_tempo = data_csv.iat[id_config[id_c], column_dep + 4 + ((section - 1) * 5)]
                    if value_tempo == 'No data':
                        data_value[section - 1].append(
                            QLabel(self.tr(value_tempo)))  # Item data_value[section-1][(id_c*4)+3]
                        data_value_nb[section - 1].append(0)  # Item data_value_nb[section-1][(id_c*4)+3]
                    else:
                        value_tempo = float(value_tempo)
                        data_value_nb[section - 1].append(float(value_tempo))
                        self.data_pdf[self.section_pdf[section-1]+ligne_pdf][2] = str(round(value_tempo, 2))
                        if value_tempo // 1000 >= 1.0:
                            value_tempo /= 1000
                            data_value[section - 1].append(QLabel(self.tr(str(round(value_tempo, 2)) + ' s')))
                        else:
                            data_value[section - 1].append(QLabel(self.tr(str(round(value_tempo, 2)) + ' ms')))

                    data.addWidget(data_value[section - 1][id_c * 4], number_rows + 2, id_c + 2)
                    data.addWidget(data_value[section - 1][(id_c * 4) + 1], number_rows + 3, id_c + 2)
                    data.addWidget(data_value[section - 1][(id_c * 4) + 2], number_rows + 4, id_c + 2)
                    data.addWidget(data_value[section - 1][(id_c * 4) + 3], number_rows + 5, id_c + 2)

                if id_config[id_c] != 1000:
                    ligne_pdf += 1
                data.addWidget(data_header[section - 1][id_c], number_rows + 1, id_c + 2)

            data.addWidget(data_label_total[section - 1], number_rows + 1, id_c + 3)
            if data_total[section - 1][0] // 1000 >= 1.0:
                data_total[section - 1][0] /= 1000
                data.addWidget(QLabel(self.tr(str(round(data_total[section - 1][0], 1)) + ' mA')), number_rows + 2,
                               id_c + 3)
            else:
                data.addWidget(QLabel(self.tr(str(round(data_total[section - 1][0], 1)) + ' uA')), number_rows + 2,
                               id_c + 3)

            if data_total[section - 1][1] // 1000 >= 1.0:
                data_total[section - 1][1] /= 1000
                data.addWidget(QLabel(self.tr(str(round(data_total[section - 1][1], 1)) + ' mA')), number_rows + 3,
                               id_c + 3)
            else:
                data.addWidget(QLabel(self.tr(str(round(data_total[section - 1][1], 1)) + ' uA')), number_rows + 3,
                               id_c + 3)

            data.addWidget(QLabel(self.tr(str(round(data_total[section - 1][2], 1)) + ' uWh')), number_rows + 4,
                           id_c + 3)

            data.addWidget(data_label[number_rows], number_rows, 0)
            data.addWidget(data_label[number_rows + 1], number_rows, 1, 1, 9)
            data_label[number_rows + 1].setStyleSheet(
                "border-bottom-width: 1px; border-bottom-style: solid; border-radius: 0px;"
                "border-top-width: 1px; border-top-style: solid; border-radius: 0px;")
            data.addWidget(data_label[number_rows + 2], number_rows + 2, 1)
            data.addWidget(data_label[number_rows + 3], number_rows + 3, 1)
            data.addWidget(data_label[number_rows + 4], number_rows + 4, 1)
            data.addWidget(data_label[number_rows + 5], number_rows + 5, 1)

            section += 1
            number_rows += 6

        for id_c in range(len(self.__id)):
            if self.get_poll_interval(id_c) is not False:
                self.append_energy_polling_occurs(nb=data_value_nb[4][((id_c + 1) * 4) + 2])
                self.append_time_polling_occurs(nb=data_value_nb[4][((id_c + 1) * 4) + 3])
            else:
                self.append_energy_polling_occurs(nb=0)
                self.append_time_polling_occurs(nb=0)

            if self.get_thresholds(id_c) is not False:
                self.append_energy_thresh_not_exceeded(nb=data_value_nb[2][((id_c + 1) * 4) + 2])
                self.append_time_thresh_not_exceeded(nb=data_value_nb[2][((id_c + 1) * 4) + 3])
                self.append_energy_thresh_exceeded(nb=data_value_nb[3][((id_c + 1) * 4) + 2])
                self.append_time_thresh_exceeded(nb=data_value_nb[3][((id_c + 1) * 4) + 3])
            elif self.get_id(id_c) == 1:  # Exception for the buttons board...
                self.append_energy_thresh_not_exceeded(nb=0)
                self.append_time_thresh_not_exceeded(nb=0)
                self.append_energy_thresh_exceeded(nb=data_value_nb[3][((id_c + 1) * 4) + 2])
                self.append_time_thresh_exceeded(nb=data_value_nb[3][((id_c + 1) * 4) + 3])
            else:
                self.append_energy_thresh_not_exceeded(nb=0)
                self.append_time_thresh_not_exceeded(nb=0)
                self.append_energy_thresh_exceeded(nb=0)
                self.append_time_thresh_exceeded(nb=0)

        return scrollDataWidget

        # --------------------------------------------------------------------------------------------------------------

    def collect_csv(self):
        """Upload the csv file stored in GitHub"""

        try:
            req = requests.get(URL_GITHUB)
        except requests.exceptions.ConnectionError:
            print("Error - No connection !")
            error_window = QErrorMessage()
            error_window.setWindowTitle("Error")
            error_window.showMessage("Hum... There is a problem with your Internet connection")

        page = req.content
        soup = BeautifulSoup(page, 'html.parser')
        soup_str = soup.get_text()
        soup_str_io = io.StringIO(soup_str)
        data = pd.read_csv(soup_str_io, sep=";", skiprows=7)
        return data

    def config_graphic_widget(self):
        """Build the LoRa castle widget"""

        graphics = QGridLayout()
        graphics.setSpacing(0)
        graphics.setVerticalSpacing(1)
        graphicsWidget = QWidget()
        graphicsWidget.setContentsMargins(0, 0, 0, 0)
        scrollGraphicsWidget = QScrollArea()
        scrollGraphicsWidget.setStyleSheet("border-width: 0px; border-radius: 0px;")

        graphicsWidget.setLayout(graphics)
        # Scroll Area Properties
        scrollGraphicsWidget.setWidgetResizable(True)
        scrollGraphicsWidget.setWidget(graphicsWidget)

        # Status Message
        data_tx_time = self.determine_airtime_lora(payload_size=(7 + len(self.__id_name)), st=True)  # in ms
        data_tx_energy = (((self.get_data_tx_st_aver_cur() / 1000000) * 3.3 * (
                data_tx_time / 1000)) / 3600) * 1000000  # in uWh

        title_status_message = QLabel(self.tr('Status Message'))
        title_status_message.setStyleSheet(
            "border-bottom-width: 1px; border-bottom-style: solid; border-radius: 0px;"
            "border-top-width: 1px; border-top-style: solid; border-radius: 0px;")
        title_energy_1 = QLabel(self.tr('Energy [uWh]'))
        title_time_1 = QLabel(self.tr('Time [ms]'))
        title_area_1 = QLabel(self.tr('Wake Up TX'))
        title_area_2 = QLabel(self.tr('Airtime TX'))
        title_area_3 = QLabel(self.tr('RX Area'))
        title_total_1 = QLabel(self.tr('Total'))
        value_energy_area_1 = QLabel(self.tr(str(round(self.get_wut_st_energy(),2))))
        self.value_energy_area_2 = QLabel(self.tr(str(round(data_tx_energy,2))))
        value_energy_area_3 = QLabel(self.tr(str(round(self.get_data_rx_st_energy(),2))))
        value_time_area_1 = QLabel(self.tr(str(round(self.get_wut_st_time(),2))))
        self.value_time_area_2 = QLabel(self.tr(str(round(data_tx_time,2))))
        value_time_area_3 = QLabel(self.tr(str(round(self.get_data_rx_st_time(),2))))
        self.value_total_energy_1 = QLabel(
            self.tr(str(round((self.get_wut_st_energy()+data_tx_energy+self.get_data_rx_st_energy()),2))))
        self.value_total_time_1 = QLabel(
            self.tr(str(round((self.get_wut_st_time() + data_tx_time + self.get_data_rx_st_time()),2))))

        graphics.addWidget(title_status_message, 0, 0, 1, 6)
        graphics.addWidget(title_energy_1, 1, 4)
        graphics.addWidget(title_time_1, 1, 5)
        graphics.addWidget(title_area_1, 2, 3)
        graphics.addWidget(title_area_2, 3, 3)
        graphics.addWidget(title_area_3, 4, 3)
        graphics.addWidget(title_total_1, 5, 3)
        graphics.addWidget(value_energy_area_1, 2, 4)
        graphics.addWidget(self.value_energy_area_2, 3, 4)
        graphics.addWidget(value_energy_area_3, 4, 4)
        graphics.addWidget(value_time_area_1, 2, 5)
        graphics.addWidget(self.value_time_area_2, 3, 5)
        graphics.addWidget(value_time_area_3, 4, 5)
        graphics.addWidget(self.value_total_energy_1, 5, 4)
        graphics.addWidget(self.value_total_time_1, 5, 5)

        if self.get_data_acc() is True:    # Accumulated Message
            time_data_tx = self.determine_airtime_lora(payload_size=self.get_lora_acc_thresholds())
            energy_data_tx = (((time_data_tx / 1000) * 3.3 * (
                    self.get_aver_cur_data_transmission(0) / 1000000)) / 3600) * 1000000

            title_acc_message = QLabel(self.tr('Accumulated Message'))
            title_acc_message.setStyleSheet(
                "border-bottom-width: 1px; border-bottom-style: solid; border-radius: 0px;"
                "border-top-width: 1px; border-top-style: solid; border-radius: 0px;")
            title_energy_2 = QLabel(self.tr('Energy [uWh]'))
            title_time_2 = QLabel(self.tr('Time [ms]'))
            title_area_21 = QLabel(self.tr('Wake Up TX'))
            title_area_22 = QLabel(self.tr('Airtime TX'))
            title_area_23 = QLabel(self.tr('RX Area'))
            title_total_2 = QLabel(self.tr('Total'))
            value_energy_area_21 = QLabel(self.tr(str(round(self.get_energy_wut_data(0),2))))
            self.value_energy_area_22 = QLabel(self.tr(str(round(energy_data_tx,2))))
            value_energy_area_23 = QLabel(self.tr(str(round(self.get_energy_data_reception(0),2))))
            value_time_area_21 = QLabel(self.tr(str(round(self.get_time_wut_data(0),2))))
            self.value_time_area_22 = QLabel(self.tr(str(round(time_data_tx,2))))
            value_time_area_23 = QLabel(self.tr(str(round(self.get_time_data_reception(0),2))))
            self.value_total_energy_2 = QLabel(
                self.tr(str(round((self.get_energy_wut_data(0) + energy_data_tx + self.get_energy_data_reception(0)),2))))
            self.value_total_time_2 = QLabel(
                self.tr(str(round((self.get_time_wut_data(0) + time_data_tx + self.get_time_data_reception(0)),2))))
            value_number_msg_title = QLabel(self.tr('Number of messages: '))
            self.value_number_msg = QLabel(self.tr(str(self.get_acc_data_send_nb())))

            graphics.addWidget(title_acc_message, 6, 0, 1, 6)
            graphics.addWidget(title_energy_2, 7, 4)
            graphics.addWidget(title_time_2, 7, 5)
            graphics.addWidget(title_area_21, 8, 3)
            graphics.addWidget(title_area_22, 9, 3)
            graphics.addWidget(title_area_23, 10, 3)
            graphics.addWidget(title_total_2, 11, 3)
            graphics.addWidget(value_energy_area_21, 8, 4)
            graphics.addWidget(self.value_energy_area_22, 9, 4)
            graphics.addWidget(value_energy_area_23, 10, 4)
            graphics.addWidget(value_time_area_21, 8, 5)
            graphics.addWidget(self.value_time_area_22, 9, 5)
            graphics.addWidget(value_time_area_23, 10, 5)
            graphics.addWidget(self.value_total_energy_2, 11, 4)
            graphics.addWidget(self.value_total_time_2, 11, 5)
            graphics.addWidget(value_number_msg_title, 12, 0)
            graphics.addWidget(self.value_number_msg, 12, 1)

        else:   # Normal Message
            title_normal_message = []
            title_energy = []
            title_time = []
            title_area_21 = []
            title_area_22 = []
            title_area_23 = []
            title_total = []
            value_energy_area_21 = []
            self.value_energy_area_22 = []
            value_energy_area_23 = []
            value_time_area_21 = []
            self.value_time_area_22 = []
            value_time_area_23 = []
            self.value_total_energy = []
            self.value_total_time = []
            value_number_msg_title = []
            self.value_number_msg = []
            nb_rows = 6
            for board in range(len(self.__id_name)):
                time_data_tx = self.determine_airtime_lora(payload_size=(2 + (2 * (self.get_number_metrics(board)))))
                energy_data_tx = (((time_data_tx / 1000) * 3.3 * (
                        self.get_aver_cur_data_transmission(board) / 1000000)) / 3600) * 1000000
                title_normal_message.append(QLabel(self.tr('Normal Message  -  '+self.get_id_name(board))))
                title_normal_message[board].setStyleSheet(
                    "border-bottom-width: 1px; border-bottom-style: solid; border-radius: 0px;"
                    "border-top-width: 1px; border-top-style: solid; border-radius: 0px;")
                title_energy.append(QLabel(self.tr('Energy [uWh]')))
                title_time.append(QLabel(self.tr('Time [ms]')))
                title_area_21.append(QLabel(self.tr('Wake Up TX')))
                title_area_22.append(QLabel(self.tr('Airtime TX')))
                title_area_23.append(QLabel(self.tr('RX Area')))
                title_total.append(QLabel(self.tr('Total')))
                value_energy_area_21.append(QLabel(self.tr(str(round(self.get_energy_wut_data(board), 2)))))
                self.value_energy_area_22.append(QLabel(self.tr(str(round(energy_data_tx, 2)))))
                value_energy_area_23.append(QLabel(self.tr(str(round(self.get_energy_data_reception(board), 2)))))
                value_time_area_21.append(QLabel(self.tr(str(round(self.get_time_wut_data(board), 2)))))
                self.value_time_area_22.append(QLabel(self.tr(str(round(time_data_tx, 2)))))
                value_time_area_23.append(QLabel(self.tr(str(round(self.get_time_data_reception(board), 2)))))
                self.value_total_energy.append(QLabel(
                    self.tr(str(
                        round((self.get_energy_wut_data(board) + energy_data_tx + self.get_energy_data_reception(board)), 2)))))
                self.value_total_time.append(QLabel(
                    self.tr(
                        str(round((self.get_time_wut_data(board) + time_data_tx + self.get_time_data_reception(board)), 2)))))
                value_number_msg_title.append(QLabel(self.tr('Number of messages: ')))
                self.value_number_msg.append(QLabel(self.tr(str(self.get_number_thresh_exceeded(board)+self.get_number_polling_occurs(board)))))

                graphics.addWidget(title_normal_message[board], 6+nb_rows, 0, 1, 6)
                graphics.addWidget(title_energy[board], 7+nb_rows, 4)
                graphics.addWidget(title_time[board], 7+nb_rows, 5)
                graphics.addWidget(title_area_21[board], 8+nb_rows, 3)
                graphics.addWidget(title_area_22[board], 9+nb_rows, 3)
                graphics.addWidget(title_area_23[board], 10+nb_rows, 3)
                graphics.addWidget(title_total[board], 11+nb_rows, 3)
                graphics.addWidget(value_energy_area_21[board], 8+nb_rows, 4)
                graphics.addWidget(self.value_energy_area_22[board], 9+nb_rows, 4)
                graphics.addWidget(value_energy_area_23[board], 10+nb_rows, 4)
                graphics.addWidget(value_time_area_21[board], 8+nb_rows, 5)
                graphics.addWidget(self.value_time_area_22[board], 9+nb_rows, 5)
                graphics.addWidget(value_time_area_23[board], 10+nb_rows, 5)
                graphics.addWidget(self.value_total_energy[board], 11+nb_rows, 4)
                graphics.addWidget(self.value_total_time[board], 11+nb_rows, 5)
                graphics.addWidget(value_number_msg_title[board], 12+nb_rows, 0)
                graphics.addWidget(self.value_number_msg[board], 12+nb_rows, 1)

                nb_rows += 7

        return scrollGraphicsWidget

    def config_event_widget(self):
        """Build the event area to choose the parameters"""

        event_box = QGridLayout()
        event_widget = QWidget()
        scroll_event_widget = QScrollArea()

        for id_c in range(len(self.__id_name)):
            # For the buttons board
            if self.get_id_name(id_c) == 'Buttons':
                button_title = QLabel(self.tr('Events for the button board'))
                button_title.setStyleSheet("border-bottom-width: 1px; border-bottom-style: solid; border-radius: 0px;")
                button_label = QLabel(self.tr('Number of times buttons are pressed: '))
                self.button_choice = QSpinBox()
                self.button_choice.setMaximum(100000)
                self.button_choice.valueChanged.connect(self.update_values)

                event_box.addWidget(button_title, 0, 0)
                event_box.addWidget(button_label, 1, 0)
                event_box.addWidget(self.button_choice, 1, 1)
            # For the power board
            elif self.get_id_name(id_c) == 'Power' or self.get_id_name(id_c) == 'Power (no thresh)':
                power_title = QLabel(self.tr('Events for the power board'))
                power_title.setStyleSheet("border-bottom-width: 1px; border-bottom-style: solid; border-radius: 0px;")
                event_box.addWidget(power_title, 2, 0)
                if self.get_number_polling_occurs(id_c) != 0:
                    power_label_pol = QLabel(self.tr('Number of polling interrupts: '))
                    power_label_pol_nb = QLabel(self.tr(str(self.get_number_polling_occurs(id_c))))
                    event_box.addWidget(power_label_pol, 3, 0)
                    event_box.addWidget(power_label_pol_nb, 3, 1)
                if self.get_thresholds(id_c) is not False:
                    power_label_th_ne = QLabel(self.tr('Number of non-exceeded thresholds: '))
                    self.power_label_th_ne_nb = QLabel(self.tr(str(self.get_number_thresh_not_exceeded(id_c))))
                    power_label_th_e = QLabel(self.tr('Number of exceeded thresholds:'))
                    self.power_choice = QSpinBox()
                    self.power_choice.setMaximum(self.get_number_thresh_not_exceeded(id_c))
                    self.power_choice.valueChanged.connect(self.update_values)
                    event_box.addWidget(power_label_th_ne, 4, 0)
                    event_box.addWidget(self.power_label_th_ne_nb, 4, 1)
                    event_box.addWidget(power_label_th_e, 5, 0)
                    event_box.addWidget(self.power_choice, 5, 1)
            # For the sound board
            elif self.get_id_name(id_c) == 'Sound' or self.get_id_name(id_c) == 'Sound (no thresh)':
                sound_title = QLabel(self.tr('Events for the sound board'))
                sound_title.setStyleSheet("border-bottom-width: 1px; border-bottom-style: solid; border-radius: 0px;")
                event_box.addWidget(sound_title, 6, 0)
                if self.get_number_polling_occurs(id_c) != 0:
                    sound_label_pol = QLabel(self.tr('Number of polling interrupts: '))
                    sound_label_pol_nb = QLabel(self.tr(str(self.get_number_polling_occurs(id_c))))
                    event_box.addWidget(sound_label_pol, 7, 0)
                    event_box.addWidget(sound_label_pol_nb, 7, 1)
                if self.get_thresholds(id_c) is not False:
                    sound_label_th_ne = QLabel(self.tr('Number of non-exceeded thresholds: '))
                    self.sound_choice_th_ne = QSpinBox()
                    self.sound_choice_th_ne.setMaximum(100000)
                    self.sound_choice_th_ne.valueChanged.connect(self.update_values)
                    sound_label_th_e = QLabel(self.tr('Number of exceeded thresholds:'))
                    self.sound_choice_th_e = QSpinBox()
                    self.sound_choice_th_e.setMaximum(100000)
                    self.sound_choice_th_e.valueChanged.connect(self.update_values)
                    event_box.addWidget(sound_label_th_ne, 8, 0)
                    event_box.addWidget(self.sound_choice_th_ne, 8, 1)
                    event_box.addWidget(sound_label_th_e, 9, 0)
                    event_box.addWidget(self.sound_choice_th_e, 9, 1)
            # For the environmental board
            elif self.get_id_name(id_c) == 'Environmental' or self.get_id_name(id_c) == 'Environmental (no thresh)':
                environmental_title = QLabel(self.tr('Events for the environmental board'))
                environmental_title.setStyleSheet("border-bottom-width: 1px; border-bottom-style: solid; border-radius: 0px;")
                event_box.addWidget(environmental_title, 6, 0)
                if self.get_number_polling_occurs(id_c) != 0:
                    environmental_label_pol = QLabel(self.tr('Number of polling interrupts: '))
                    environmental_label_pol_nb = QLabel(self.tr(str(self.get_number_polling_occurs(id_c))))
                    event_box.addWidget(environmental_label_pol, 7, 0)
                    event_box.addWidget(environmental_label_pol_nb, 7, 1)
                if self.get_thresholds(id_c) is not False:
                    environmental_label_th_ne = QLabel(self.tr('Number of non-exceeded thresholds: '))
                    self.environmental_choice_th_ne = QSpinBox()
                    self.environmental_choice_th_ne.setMaximum(100000)
                    self.environmental_choice_th_ne.valueChanged.connect(self.update_values)
                    environmental_label_th_e = QLabel(self.tr('Number of exceeded thresholds:'))
                    self.environmental_choice_th_e = QSpinBox()
                    self.environmental_choice_th_e.setMaximum(100000)
                    self.environmental_choice_th_e.valueChanged.connect(self.update_values)
                    event_box.addWidget(environmental_label_th_ne, 8, 0)
                    event_box.addWidget(self.environmental_choice_th_ne, 8, 1)
                    event_box.addWidget(environmental_label_th_e, 9, 0)
                    event_box.addWidget(self.environmental_choice_th_e, 9, 1)
            # If you want to add a new board ...

        lora_label = QLabel(self.tr('LoRa settings'))
        lora_label.setStyleSheet("border-bottom-width: 1px; border-bottom-style: solid; border-radius: 0px;")
        event_box.addWidget(lora_label, 10, 0)

        lora_spread_fact_label = QLabel(self.tr('Spreading factor: '))
        self.lora_spread_fact_nb_label = QLabel(self.tr(str(self.get_lora_spread_factor())))
        self.lora_spread_fact = QSlider(Qt.Horizontal, self)
        self.lora_spread_fact.setRange(7, 12)
        self.lora_spread_fact.setValue(11)
        self.lora_spread_fact.setFocusPolicy(Qt.NoFocus)
        self.lora_spread_fact.setPageStep(1)
        self.lora_spread_fact.valueChanged.connect(self.update_values)

        event_box.addWidget(lora_spread_fact_label, 11, 0)
        event_box.addWidget(self.lora_spread_fact, 12, 0)
        event_box.addWidget(self.lora_spread_fact_nb_label, 12, 1)

        event_widget.setLayout(event_box)
        scroll_event_widget.setWidgetResizable(True)
        scroll_event_widget.setWidget(event_widget)
        scroll_event_widget.setMinimumWidth(425)

        return scroll_event_widget

    def determine_airtime_lora(self, payload_size, st=False):
        """Determine Air Time for the LoRa castle (TX time)"""
        # Inspired by code from GillesC
        # https://github.com/GillesC/LoRaEnergySim/blob/master/Framework/LoRaPacket.py
        n_pream = 8  # https://www.google.com/patents/EP2763321A1?cl=en
        t_sym = (2.0 ** self.get_lora_spread_factor()) / 125
        t_pream = (n_pream + 4.25) * t_sym
        if self.get_lora_spread_factor() >= 11:
            LDR_opt = 1  # Low Data Rate optimisation
        else:
            LDR_opt = 0

        payload_symb_n_b = 8 + max(
            math.ceil(
                (8.0 * payload_size - 4.0 * self.get_lora_spread_factor() + 28 + 16) / (4.0 * (
                        self.get_lora_spread_factor() - 2 * LDR_opt))) * (1 + 4), 0)
        t_payload = payload_symb_n_b * t_sym

        if self.get_data_acc() is False:
            t_error = ERROR_DATA_TX_TIME[self.get_lora_spread_factor()-7]
        elif st is True:
            t_error = ERROR_DATA_TX_TIME[self.get_lora_spread_factor() - 7]
        else:
            t_error = ERROR_DATA_TX_TIME_ACC[self.get_lora_spread_factor()-7]

        return t_pream + t_payload + t_error

    def determine_status_message(self):
        """Determine total energy and time for the status message"""

        data_tx_time = self.determine_airtime_lora(payload_size=(7 + len(self.__id_name)), st=True)  # in ms
        data_tx_energy = (((self.get_data_tx_st_aver_cur() / 1000000) * 3.3 * (
                    data_tx_time / 1000)) / 3600) * 1000000  # in uWh
        data_tx_energy_max = ((((self.get_data_tx_st_aver_cur()+ERROR_AVER_CUR_TX) / 1000000) * 3.3 * (
                data_tx_time / 1000)) / 3600) * 1000000  # in uWh

        total_time = self.get_wut_st_time() + data_tx_time + self.get_data_rx_st_time()
        total_energy = self.get_wut_st_energy() + data_tx_energy + self.get_data_rx_st_energy()
        total_energy_max = self.get_wut_st_energy() + data_tx_energy_max + self.get_data_rx_st_energy()

        self.set_time_st(total_time)
        self.set_energy_st(total_energy)
        self.set_energy_st_max(total_energy_max)

    def determine_sending_message(self, id):
        """Determine normal LoRa message for a specific ID (or for the accumulated msg)"""

        if self.get_data_acc() is False:
            time_data_tx = self.determine_airtime_lora(payload_size=(2 + (2 * (self.get_number_metrics(id)))))
        else:
            time_data_tx = self.determine_airtime_lora(payload_size=self.get_lora_acc_thresholds())

        energy_data_tx = (((time_data_tx / 1000) * 3.3 * (
                self.get_aver_cur_data_transmission(id) / 1000000)) / 3600) * 1000000

        energy_data_tx_max = (((time_data_tx / 1000) * 3.3 * (
                (self.get_aver_cur_data_transmission(id)+ERROR_AVER_CUR_TX) / 1000000)) / 3600) * 1000000

        self.set_sending_castle_time(id,
                                     self.get_time_wut_data(id) + self.get_time_data_reception(id) + time_data_tx)
        self.set_sending_castle_energy(id,
                                       self.get_energy_wut_data(id) + self.get_energy_data_reception(id) + energy_data_tx)
        self.set_sending_castle_energy_max(id,
                                       self.get_energy_wut_data(id) + self.get_energy_data_reception(
                                           id) + energy_data_tx_max)

    def determine_static_energy(self):
        """Determine the static energy for the entire system"""

        # ---- Determine Static Time ---- [ms]
        static_time = 86400000
        self.set_time_static_energy(0, 86400000-self.get_time_dyn_data_energy(0)-self.get_dyn_send_time())
        self.data_pdf[0][3] = round(86400000-self.get_time_dyn_data_energy(0)-self.get_dyn_send_time(), 2)
        static_time = static_time - self.get_time_dyn_data_energy(0) - self.get_dyn_send_time()
        for idc in range(len(self.__id)):
            self.set_time_static_energy(idc+1, 86400000-self.get_time_dyn_data_energy(idc+1))
            if self.__id[idc] is not False:
                self.data_pdf[idc+1][3] = round(86400000-self.get_time_dyn_data_energy(idc+1), 2)
            static_time -= self.get_time_dyn_data_energy(idc+1)

        # ---- Determine Static Energy ---- [uWh]
        static_energy = 0
        static_energy_max = 0
        static_energy_min = 0
        static_energy += self.get_power_static_energy(0)*self.get_time_static_energy(0)
        self.data_pdf[0][5] = round((self.get_power_static_energy(0)*self.get_time_static_energy(0)/3600000), 2)
        static_energy_max += (((self.get_power_static_energy(
            0)/3.3)+ERROR_AVER_CUR_SLEEP)*3.3)*self.get_time_static_energy(0)
        static_energy_min += (((self.get_power_static_energy(
            0)/3.3)-ERROR_AVER_CUR_SLEEP)*3.3)*self.get_time_static_energy(0)

        for idc in range(len(self.__id)):
            static_energy += self.get_power_static_energy(idc+1)*self.get_time_static_energy(idc+1)
            static_energy_max += (((self.get_power_static_energy(
                idc+1) / 3.3) + ERROR_AVER_CUR_SLEEP) * 3.3) * self.get_time_static_energy(idc+1)
            static_energy_min += (((self.get_power_static_energy(
                idc+1) / 3.3) - ERROR_AVER_CUR_SLEEP) * 3.3) * self.get_time_static_energy(idc+1)

            if self.get_id(idc) is not False:
                if self.get_id_name(idc) == 'Sound':              # Disabling the microphone after an exceeded threshold
                    static_energy -= ((21.6*3.3)*64000)*self.get_number_thresh_exceeded(idc)
                    static_energy_max -= ((21.6*3.3)*64000)*self.get_number_thresh_exceeded(idc)
                    static_energy_min -= ((21.6*3.3)*64000) * self.get_number_thresh_exceeded(idc)
            if self.get_id(idc) is not False:
                self.data_pdf[idc+1][5] = round((self.get_power_static_energy(idc+1) * self.get_time_static_energy(idc+1) / 3600000),
                                          2)

        self.set_static_energy(static_energy/3600000)
        self.set_static_energy_max(static_energy_max/3600000)
        self.set_static_energy_min(static_energy_min/3600000)
        self.set_static_time(static_time)

    def determine_dynamic_data_energy(self):
        """Determine the data dynamic energy for the entire system"""

        # ---- Determine Dynamic Data Time ---- [ms]
        # For Motherboard
        dynamic_time = 0
        dynamic_time += self.get_number_wum()*self.get_time_wum()
        if self.get_data_acc() is True:
            for idc in range(len(self.__id)):
                if self.get_id(idc) is not False:
                    dynamic_time += self.get_number_storing_msg(idc)*self.get_time_store_data(idc)

        self.set_time_dyn_data_energy(0, dynamic_time)

        # For other boards
        for idc in range(len(self.__id)):
            dynamic_time = 0
            dynamic_time += self.get_number_polling_occurs(idc)*self.get_time_polling_occurs(idc)
            dynamic_time += self.get_number_thresh_not_exceeded(idc)*self.get_time_thresh_not_exceeded(idc)
            dynamic_time += self.get_number_thresh_exceeded(idc)*self.get_time_thresh_exceeded(idc)
            self.set_time_dyn_data_energy(idc+1, dynamic_time)

        # ---- Determine Dynamic Data Energy ---- [uWh]
        dynamic_energy = 0
        # For Motherboard
        dynamic_energy += self.get_number_wum()*self.get_energy_wum()
        if self.get_data_acc() is True:
            for idc in range(len(self.__id)):
                if self.get_id(idc) is not False:
                    dynamic_energy += self.get_number_storing_msg(idc)*self.get_energy_store_data(idc)

        # For other boards
        for idc in range(len(self.__id)):
            dynamic_energy += self.get_number_polling_occurs(idc)*self.get_energy_polling_occurs(idc)
            dynamic_energy += self.get_number_thresh_not_exceeded(idc)*self.get_energy_thresh_not_exceeded(idc)
            dynamic_energy += self.get_number_thresh_exceeded(idc)*self.get_energy_thresh_exceeded(idc)

        self.set_dyn_data_energy(dynamic_energy)

    def determine_dynamic_send_energy(self):
        """Determine the sending dynamic energy for the entire system"""

        # ---- Determine Dynamic Send Time ---- [ms]
        # For Motherboard
        dynamic_time = 0
        dynamic_time += self.get_time_st()
        if self.get_data_acc() is True:
            dynamic_time += self.get_acc_data_send_nb()*self.get_sending_castle_time(0)
        else:
            for idc in range(len(self.__id)):
                dynamic_time += self.get_number_thresh_exceeded(idc)*self.get_sending_castle_time(idc)
                dynamic_time += self.get_number_polling_occurs(idc)*self.get_sending_castle_time(idc)

        self.set_dyn_send_time(dynamic_time)

        # ---- Determine Dynamic Send Energy ---- [uWh]
        # For Motherboard
        dynamic_energy = 0
        dynamic_energy_max = 0
        dynamic_energy += self.get_energy_st()
        dynamic_energy_max += self.get_energy_st_max()

        if self.get_data_acc() is True:
            dynamic_energy += self.get_acc_data_send_nb()*self.get_sending_castle_energy(0)
            dynamic_energy_max += self.get_acc_data_send_nb() * self.get_sending_castle_energy_max(0)
        else:
            for idc in range(len(self.__id)):
                dynamic_energy += self.get_number_thresh_exceeded(idc)*self.get_sending_castle_energy(idc)
                dynamic_energy_max += self.get_number_thresh_exceeded(idc) * self.get_sending_castle_energy_max(idc)
                dynamic_energy += self.get_number_polling_occurs(idc)*self.get_sending_castle_energy(idc)
                dynamic_energy_max += self.get_number_polling_occurs(idc) * self.get_sending_castle_energy_max(idc)

        self.set_dyn_send_energy(dynamic_energy)
        self.set_dyn_send_energy_max(dynamic_energy_max)

    def determine_total_average_cons(self):
        """Estimate the total average consumption"""

        self.determine_dynamic_data_energy()
        self.determine_dynamic_send_energy()
        self.determine_static_energy()

        self.set_total_aver_cons(self.get_static_energy()+self.get_dyn_data_energy()+self.get_dyn_send_energy())
        self.set_total_aver_cons_max(
            self.get_static_energy_max()+self.get_dyn_data_energy()+self.get_dyn_send_energy_max())
        self.set_total_aver_cons_min(
            self.get_static_energy_min() + self.get_dyn_data_energy() + self.get_dyn_send_energy())

    def on_exit_button(self):
        """Close the window"""
        self.close()

    def on_print_button(self):
        """Print a PDF report"""
        filepath, _ = QFileDialog.getSaveFileName(self, "Save PDF", "", "PDF(*.pdf) ")
        if filepath == "":
            return
        self.pdf = ReportPDF.Report(filepath, "IWAST Power Report", )
        self.pdf.set_data_acc(self.get_data_acc())
        self.pdf.data_value = self.data_pdf
        self.pdf.data_date = self.pdf_data_date
        self.update_pdf()
        err = "ok"
        try:
            err = self.pdf.run()
        except:
            print("Error !")
            error_window = QErrorMessage()
            error_window.setWindowTitle("Error")
            error_window.showMessage(err)

    def update_values(self):
        """Set the new values depending on the event choices"""
        # Update LoRa settings
        self.set_lora_spread_factor(self.lora_spread_fact.value())
        self.lora_spread_fact_nb_label.setText(self.tr(str(self.get_lora_spread_factor())))
        if self.get_data_acc() is False:
            for id_c in range(len(self.__id_name)):
                self.determine_sending_message(id_c)
        else:
            self.determine_sending_message(0)
        self.determine_status_message()

        # Update Thresholds numbers
        for id_c in range(len(self.__id_name)):
            if self.get_id_name(id_c) == 'Buttons':
                self.set_number_thresh_exceeded(idx=id_c, nb=self.button_choice.value())
            elif self.get_id_name(id_c) == 'Power':
                if self.get_thresholds(id_c) is not False:
                    self.set_number_thresh_exceeded(idx=id_c, nb=self.power_choice.value())
                    self.set_number_thresh_not_exceeded(idx=id_c, nb=(
                            self.get_number_possible_thresh(id_c) - self.get_number_thresh_exceeded(id_c)))
                    if self.get_number_thresh_not_exceeded(idx=id_c) < 0:
                        self.set_number_thresh_not_exceeded(idx=id_c, nb=0)
                    self.power_label_th_ne_nb.setText(str(self.get_number_thresh_not_exceeded(idx=id_c)))
            elif self.get_id_name(id_c) == 'Sound':
                if self.get_thresholds(id_c) is not False:
                    self.set_number_thresh_exceeded(idx=id_c, nb=self.sound_choice_th_e.value())
                    self.set_number_thresh_not_exceeded(idx=id_c, nb=self.sound_choice_th_ne.value())
            elif self.get_id_name(id_c) == 'Environmental':
                if self.get_thresholds(id_c) is not False:
                    self.set_number_thresh_exceeded(idx=id_c, nb=self.environmental_choice_th_e.value())
                    self.set_number_thresh_not_exceeded(idx=id_c, nb=self.environmental_choice_th_ne.value())

        if self.get_data_acc() is not False:
            self.determine_number_acc_send()
            self.determine_number_storing_msg()

        # Update total average consumption
        self.determine_total_average_cons()
        self.average_total_consumption.setText(self.tr(str(round(self.get_total_aver_cons(), 2)) + ' uWh'))
        self.average_total_consumption_max.setText(self.tr(str(round(self.get_total_aver_cons_max(), 2)) + ' uWh'))
        self.average_total_consumption_min.setText(self.tr(str(round(self.get_total_aver_cons_min(), 2)) + ' uWh'))

        # Update sleep time value
        self.set_percent_static_time(round(self.get_static_time() / 864000, 3))
        self.sleep_time_value_label.setText(
            self.tr(self.better_sleep_time(int(self.get_static_time() / 1000)) + ' (' + str(
                self.get_percent_static_time()) + ' %)'))

        # Update lifetime
        self.determine_lifetime()
        self.lifetime_value_label.setText(self.tr(
            str(self.get_life_estimation()) + ' (min: ' + str(self.get_life_estimation_min()) + ')'))

        # Update LoRa castles
        self.update_castles()

        self.debug()

    def update_castles(self):
        """Update the LoRa castles characteristics"""
        # Status Message
        data_tx_time = self.determine_airtime_lora(payload_size=(7 + len(self.__id_name)), st=True)  # in ms
        data_tx_energy = (((self.get_data_tx_st_aver_cur() / 1000000) * 3.3 * (
                data_tx_time / 1000)) / 3600) * 1000000  # in uWh

        self.value_energy_area_2.setText(self.tr(str(round(data_tx_energy, 2))))
        self.value_time_area_2.setText(self.tr(str(round(data_tx_time, 2))))
        self.value_total_energy_1.setText(
            self.tr(str(round((self.get_wut_st_energy() + data_tx_energy + self.get_data_rx_st_energy()), 2))))
        self.value_total_time_1.setText(
            self.tr(str(round((self.get_wut_st_time() + data_tx_time + self.get_data_rx_st_time()), 2))))

        if self.get_data_acc() is True:

            # Accumulated Message
            time_data_tx = self.determine_airtime_lora(payload_size=self.get_lora_acc_thresholds())
            energy_data_tx = (((time_data_tx / 1000) * 3.3 * (
                    self.get_aver_cur_data_transmission(0) / 1000000)) / 3600) * 1000000

            self.value_energy_area_22.setText(self.tr(str(round(energy_data_tx, 2))))
            self.value_time_area_22.setText(self.tr(str(round(time_data_tx, 2))))
            self.value_total_energy_2.setText(
                self.tr(
                    str(round((self.get_energy_wut_data(0) + energy_data_tx + self.get_energy_data_reception(0)), 2))))
            self.value_total_time_2.setText(
                self.tr(str(round((self.get_time_wut_data(0) + time_data_tx + self.get_time_data_reception(0)), 2))))
            self.value_number_msg.setText(self.tr(str(self.get_acc_data_send_nb())))

        else:
            nb_rows = 6
            for board in range(len(self.__id_name)):
                time_data_tx = self.determine_airtime_lora(payload_size=(2 + (2 * (self.get_number_metrics(board)))))
                energy_data_tx = (((time_data_tx / 1000) * 3.3 * (
                        self.get_aver_cur_data_transmission(board) / 1000000)) / 3600) * 1000000

                self.value_energy_area_22[board].setText(self.tr(str(round(energy_data_tx, 2))))
                self.value_time_area_22[board].setText(self.tr(str(round(time_data_tx, 2))))
                self.value_total_energy[board].setText(
                    self.tr(str(
                        round(
                            (self.get_energy_wut_data(board) + energy_data_tx + self.get_energy_data_reception(board)),
                            2))))
                self.value_total_time[board].setText(
                    self.tr(
                        str(round((self.get_time_wut_data(board) + time_data_tx + self.get_time_data_reception(board)),
                                  2))))
                self.value_number_msg[board].setText(
                    self.tr(str(self.get_number_thresh_exceeded(board) + self.get_number_polling_occurs(board))))
                nb_rows += 7

    def update_pdf(self):
        """Update the PDF information"""
        for idc in range(len(self.__id_name)):
            self.pdf.add_board_name(idc+1, self.get_id_name(idc))

        self.pdf.add_spreading_factor(self.get_lora_spread_factor())
        self.pdf.add_data_value(self.section_pdf[1], 0, self.get_number_wum())
        self.pdf.add_data_value(self.section_pdf[1], 3, self.get_number_wum() * self.get_time_wum())
        self.pdf.add_data_value(self.section_pdf[1], 5, self.get_number_wum() * self.get_energy_wum())
        self.pdf.add_estimation_value(0, self.get_total_aver_cons())
        self.pdf.add_estimation_value(1, self.get_total_aver_cons_max())
        self.pdf.add_estimation_value(2, self.get_life_estimation())
        self.pdf.add_estimation_value(3, self.get_life_estimation_min())
        i = 0
        while i < 6:
            for idc in range(len(self.__id)):
                if self.get_id(idc) is not False:
                    if i == 0:
                        self.pdf.add_data_value(self.section_pdf[i + 2] + idc + 1, 0,
                                                self.get_number_thresh_not_exceeded(idc))
                        self.pdf.add_data_value(self.section_pdf[i + 2] + idc + 1, 3,
                                                round(self.get_number_thresh_not_exceeded(idc) *
                                                      self.get_time_thresh_not_exceeded(idc), 2))
                        self.pdf.add_data_value(self.section_pdf[i + 2] + idc + 1, 5,
                                                round(self.get_number_thresh_not_exceeded(idc) *
                                                      self.get_energy_thresh_not_exceeded(idc), 2))
                    elif i == 1:
                        self.pdf.add_data_value(self.section_pdf[i + 2] + idc + 1, 0,
                                                self.get_number_thresh_exceeded(idc))
                        self.pdf.add_data_value(self.section_pdf[i + 2] + idc + 1, 3,
                                                round(self.get_number_thresh_exceeded(idc) *
                                                      self.get_time_thresh_exceeded(idc), 2))
                        self.pdf.add_data_value(self.section_pdf[i + 2] + idc + 1, 5,
                                                round(self.get_number_thresh_exceeded(idc) *
                                                      self.get_energy_thresh_exceeded(idc), 2))
                    elif i == 2:
                        self.pdf.add_data_value(self.section_pdf[i + 2] + idc + 1, 0,
                                                self.get_number_polling_occurs(idc))
                        self.pdf.add_data_value(self.section_pdf[i + 2] + idc + 1, 3,
                                                round(self.get_number_polling_occurs(idc) *
                                                      self.get_time_polling_occurs(idc), 2))
                        self.pdf.add_data_value(self.section_pdf[i + 2] + idc + 1, 5,
                                                round(self.get_number_polling_occurs(idc) *
                                                      self.get_energy_polling_occurs(idc), 2))
                    elif i == 3:
                        if self.get_data_acc() is True:
                            self.pdf.add_data_value(self.section_pdf[i + 2] + idc + 1, 0,
                                                    self.get_number_storing_msg(idc))
                            self.pdf.add_data_value(self.section_pdf[i + 2] + idc + 1, 3,
                                                    round(self.get_number_storing_msg(idc) *
                                                          self.get_time_store_data(idc), 2))
                            self.pdf.add_data_value(self.section_pdf[i + 2] + idc + 1, 5,
                                                    round(self.get_number_storing_msg(idc) *
                                                          self.get_energy_store_data(idc), 2))
                    elif i == 4:
                        self.pdf.add_data_value(self.section_pdf[i + 2], 0, 1)
                        self.pdf.add_data_value(self.section_pdf[i + 2], 1, '/')
                        self.pdf.add_data_value(self.section_pdf[i + 2], 2, '/')
                        self.pdf.add_data_value(self.section_pdf[i + 2], 3, round(self.get_time_st(), 2))
                        self.pdf.add_data_value(self.section_pdf[i + 2], 4, '/')
                        self.pdf.add_data_value(self.section_pdf[i + 2], 5, round(self.get_energy_st(), 2))
                    elif i == 5:
                        if self.get_data_acc() is True:
                            self.pdf.add_data_value(self.section_pdf[i + 2], 0, round(self.get_acc_data_send_nb(),2))
                            self.pdf.add_data_value(self.section_pdf[i + 2], 1, '/')
                            self.pdf.add_data_value(self.section_pdf[i + 2], 2, round(self.get_sending_castle_time(0),2))
                            self.pdf.add_data_value(self.section_pdf[i + 2], 3, round(self.get_acc_data_send_nb()*self.get_sending_castle_time(0),2))
                            self.pdf.add_data_value(self.section_pdf[i + 2], 4, round(self.get_sending_castle_energy(0),2))
                            self.pdf.add_data_value(self.section_pdf[i + 2], 5, round(self.get_acc_data_send_nb()*self.get_sending_castle_energy(0),2))
                        else:
                            self.pdf.add_data_value(self.section_pdf[i + 2] + idc + 1, 0,
                                                    round(self.get_number_thresh_exceeded(idc) + self.get_number_polling_occurs(idc), 2))
                            self.pdf.add_data_value(self.section_pdf[i + 2] + idc + 1, 1, '/')
                            self.pdf.add_data_value(self.section_pdf[i + 2] + idc + 1, 2,
                                                    round(self.get_sending_castle_time(idc), 2))
                            self.pdf.add_data_value(self.section_pdf[i + 2] + idc + 1, 3,
                                                    round(self.get_sending_castle_time(idc)*(self.get_number_thresh_exceeded(idc) + self.get_number_polling_occurs(idc)),
                                                          2))
                            self.pdf.add_data_value(self.section_pdf[i + 2] + idc + 1, 4,
                                                    round(self.get_sending_castle_energy(idc), 2))
                            self.pdf.add_data_value(self.section_pdf[i + 2] + idc + 1, 5, round(self.get_sending_castle_energy(idc)*(self.get_number_thresh_exceeded(idc) + self.get_number_polling_occurs(idc)), 2))

            i += 1

    def better_sleep_time(self, value_st):
        """Convert sleep time in [s] into [hh:mm:ss]"""
        number_hours = str(value_st // 3600)
        number_min = str((value_st % 3600) // 60)
        number_sec = str((value_st % 3600) % 60)

        better_value = str('' + number_hours + 'h ' + number_min + 'm ' + number_sec + 's')
        return better_value

    def determine_number_thresh_not_exceeded(self):
        """Determine the number of not-exceeded threshold for each board"""
        for id_c in range(len(self.__id)):
            if self.get_id(id_c) is not False:
                if self.get_thresholds(id_c) is True and self.get_id_name(id_c) != 'Sound':
                    self.append_number_possible_thresh(int((86400000 / self.get_threshold_interval(id_c)
                                                            - self.get_number_polling_occurs(id_c))))

                    if self.get_number_possible_thresh(id_c) >= 0:
                        self.append_number_thresh_not_exceeded(self.get_number_possible_thresh(id_c))
                        self.append_number_thresh_exceeded(0)
                    else:
                        self.append_number_thresh_not_exceeded(0)
                        self.append_number_thresh_exceeded(0)
                else:
                    self.append_number_possible_thresh(0)
                    self.append_number_thresh_not_exceeded(0)
                    self.append_number_thresh_exceeded(0)
            else:
                self.append_number_possible_thresh(0)
                self.append_number_thresh_not_exceeded(0)
                self.append_number_thresh_exceeded(0)

    def determine_number_acc_send(self):
        """Determine the number of accumulated message"""
        total_nb_metrics = 0
        for id_c in range(len(self.__id)):
            if self.get_id(id_c) is not False:
                total_nb_metrics += self.get_number_thresh_exceeded(id_c) * ((self.get_number_metrics(id_c)*2)+4)
                total_nb_metrics += self.get_number_polling_occurs(id_c) * ((self.get_number_metrics(id_c)*2)+4)

        self.set_acc_data_send_nb(int(total_nb_metrics / self.get_lora_acc_thresholds()))

    def determine_number_storing_msg(self):
        """Determine the number of storing event for each boards"""
        for idc in range(len(self.__id)):
            if self.get_id(idc) is not False:
                total_number = 0
                total_number += self.get_number_thresh_exceeded(idc)*self.get_number_metrics(idc)
                if self.get_id_name(idc) == 'Sound' or self.get_id_name(idc) == 'Sound (no thresh)':     # Sound board particularity
                    total_number += 2*(self.get_number_polling_occurs(idc)*self.get_number_metrics(idc))
                else:
                    total_number += self.get_number_polling_occurs(idc) * self.get_number_metrics(idc)
                self.set_number_storing_msg(idc, total_number)

    def determine_lifetime(self):
        """Determine the lifetime of the entire system"""
        duration = (24/self.get_total_aver_cons())*((BATTERY*3.3)*1000)     # in hours
        nb_jour = int(duration // 24)
        nb_heure = int(duration % 24)
        nb_minutes = int(((duration % 24) - int(duration % 24))*60)
        nb_seconds = int(
            ((((duration % 24) - int(duration % 24))*60) - int(((duration % 24) - int(duration % 24))*60))*60)
        self.set_life_estimation(str(nb_jour)+'d '+str(nb_heure)+'h '+str(nb_minutes)+'m '+str(nb_seconds)+'s')

        duration = (24 / self.get_total_aver_cons_max()) * ((BATTERY * 3.3) * 1000)  # in hours
        nb_jour = int(duration // 24)
        nb_heure = int(duration % 24)
        nb_minutes = int(((duration % 24) - int(duration % 24)) * 60)
        nb_seconds = int(
            ((((duration % 24) - int(duration % 24)) * 60) - int(((duration % 24) - int(duration % 24)) * 60)) * 60)
        self.set_life_estimation_min(str(nb_jour)+'d '+str(nb_heure)+'h '+str(nb_minutes)+'m '+str(nb_seconds)+'s')

    def debug(self):
        if DEBUG is True:
            print('\n--------------------GENERAL--------------------')
            print('                       ID Config: ' + str(self.__id))
            print('                         ID Name: ' + str(self.__id_name))
            print('                    Thresholds ?: ' + str(self.__thresholds))
            print('               Number of metrics: ' + str(self.__number_metrics))
            print('\n--------------------POLLING--------------------')
            print('               Polling Intervals: ' + str(self.__poll_interval))
            print('                 Polling Numbers: ' + str(self.__number_polling_occurs))
            print('                   Polling Times: ' + str(self.__time_polling_occurs))
            print('                  Polling Energy: ' + str(self.__energy_polling_occurs))
            print('\n------------------THRESHOLDS-------------------')
            print('     Possible Thresholds Numbers: ' + str(self.__number_possible_thresh))
            print('  Possible NE Thresholds Numbers: ' + str(self.__number_thresh_not_exceeded))
            print('   Possible E Thresholds Numbers: ' + str(self.__number_thresh_exceeded))
            print('             NE Thresholds Times: ' + str(self.__time_thresh_not_exceeded))
            print('              E Thresholds Times: ' + str(self.__time_thresh_exceeded))
            print('            NE Thresholds Energy: ' + str(self.__energy_thresh_not_exceeded))
            print('             E Thresholds Energy: ' + str(self.__energy_thresh_exceeded))
            print('\n--------------WAKE UP MOTHERBOARD--------------')
            print('                     WUM Numbers: ' + str(self.__number_wum))
            print('                       WUM Times: ' + str(self.__time_wum))
            print('                      WUM Energy: ' + str(self.__energy_wum))
            print('\n--------------DATA SENDING CASTLE--------------')
            print('                 WUT DATA Energy: ' + str(self.__energy_wut_data))
            print('                   WUT DATA Time: ' + str(self.__time_wut_data))
            print('           DATA TX Aver. Current: ' + str(self.__aver_cur_data_transmission))
            print('                  DATA RX Energy: ' + str(self.__energy_data_reception))
            print('                    DATA RX Time: ' + str(self.__time_data_reception))
            print('        DATA Sending Castle Time: ' + str(self.__sending_castle_time))
            print('      DATA Sending Castle Energy: ' + str(self.__sending_castle_energy))
            print('DATA Sending Castle Energy (ERR): ' + str(self.__sending_castle_energy_max))
            print('\n----------DATA SENDING CASTLE (STATUS)---------')
            print('    Sending Castle Time (status): ' + str(self.get_time_st()))
            print('  Sending Castle Energy (status): ' + str(self.get_energy_st()))
            print('Sending Castle Energy (status) E: ' + str(self.get_energy_st_max()))
            print('\n-------------DATA ACCUMULATION-----------------')
            print('    (ACC)    DATA Storage Energy: ' + str(self.__energy_store_data))
            print('    (ACC)      DATA Storage Time: ' + str(self.__time_store_data))
            print('    (ACC)    Number Data sending: ' + str(self.__acc_data_send_nb))
            print('    (ACC)    Number Data Storing: ' + str(self.__number_storing_msg))
            print('\n----------------STATIC ENERGY------------------')
            print('                    Static Power: ' + str(self.__power_static_energy))
            print('                    Static Times: ' + str(self.__time_static_energy))
            print('                   Static Energy: ' + str(self.__static_energy))
            print('\n----------- DYNAMIC ENERGY (DATA)--------------')
            print('                   Dynamic Times: ' + str(self.__time_dyn_data_energy))
            print('                  Dynamic Energy: ' + str(self.__dyn_data_energy))
            print('\n----------- DYNAMIC ENERGY (SEND)--------------')
            print('                    Dynamic Time: ' + str(self.__dyn_send_time))
            print('                  Dynamic Energy: ' + str(self.__dyn_send_energy))

    # ------------------------------------------------------------------------------------------------------------------
    #      ACCESSORS AND MUTATORS
    # ------------------------------------------------------------------------------------------------------------------

    def get_id(self, idx):
        return self.__id[idx]

    def get_poll_interval(self, idx):
        return self.__poll_interval[idx]

    def get_data_acc(self):
        return self.__data_acc

    def get_thresholds(self, idx):
        return self.__thresholds[idx]

    def get_energy_data_reception(self, idx):
        return self.__energy_data_reception[idx]

    def get_time_data_reception(self, idx):
        return self.__time_data_reception[idx]

    def get_energy_data_transmission(self, idx):
        return self.__energy_data_transmission[idx]

    def get_time_data_transmission(self, idx):
        return self.__time_data_transmission[idx]

    def get_aver_cur_data_transmission(self, idx):
        return self.__aver_cur_data_transmission[idx]

    def get_energy_wut_data(self, idx):
        return self.__energy_wut_data[idx]

    def get_time_wut_data(self, idx):
        return self.__time_wut_data[idx]

    def get_number_possible_thresh(self, idx):
        return self.__number_possible_thresh[idx]

    def get_number_thresh_exceeded(self, idx):
        return self.__number_thresh_exceeded[idx]

    def get_number_thresh_not_exceeded(self, idx):
        return self.__number_thresh_not_exceeded[idx]

    def get_energy_thresh_exceeded(self, idx):
        return self.__energy_thresh_exceeded[idx]

    def get_energy_thresh_not_exceeded(self, idx):
        return self.__energy_thresh_not_exceeded[idx]

    def get_time_thresh_exceeded(self, idx):
        return self.__time_thresh_exceeded[idx]

    def get_time_thresh_not_exceeded(self, idx):
        return self.__time_thresh_not_exceeded[idx]

    def get_threshold_interval(self, idx):
        return self.__threshold_interval[idx]

    def get_number_polling_occurs(self, idx):
        return self.__number_polling_occurs[idx]

    def get_time_polling_occurs(self, idx):
        return self.__time_polling_occurs[idx]

    def get_energy_polling_occurs(self, idx):
        return self.__energy_polling_occurs[idx]

    def get_id_name(self, idx):
        return self.__id_name[idx]

    def get_time_st(self):
        return self.__time_st

    def get_energy_st(self):
        return self.__energy_st

    def get_time_wum(self):
        return self.__time_wum

    def get_number_wum(self):
        return self.__number_wum

    def get_energy_wum(self):
        return self.__energy_wum

    def get_number_metrics(self, idx):
        return self.__number_metrics[idx]

    def get_sending_castle_time(self, idx):
        return self.__sending_castle_time[idx]

    def get_sending_castle_energy(self, idx):
        return self.__sending_castle_energy[idx]

    def get_percent_static_time(self):
        return self.__percent_static_time

    def get_total_aver_cons(self):
        return self.__total_aver_cons

    def get_lora_spread_factor(self):
        return self.__lora_spread_factor

    def get_wut_st_time(self):
        return self.__wut_st_time

    def get_wut_st_energy(self):
        return self.__wut_st_energy

    def get_data_tx_st_aver_cur(self):
        return self.__data_tx_st_aver_cur

    def get_data_rx_st_time(self):
        return self.__data_rx_st_time

    def get_data_rx_st_energy(self):
        return self.__data_rx_st_energy

    def get_acc_data_send_nb(self):
        return self.__acc_data_send_nb

    def get_lora_acc_thresholds(self):
        return self.__lora_acc_thresholds

    def get_time_store_data(self, idx):
        return self.__time_store_data[idx]

    def get_energy_store_data(self, idx):
        return self.__energy_store_data[idx]

    def get_total_aver_cons_max(self):
        return self.__total_aver_cons_max

    def get_total_aver_cons_min(self):
        return self.__total_aver_cons_min

    def get_life_estimation(self):
        return self.__life_estimation

    def get_life_estimation_min(self):
        return self.__life_estimation_min

    def get_time_static_energy(self, idx):
        return self.__time_static_energy[idx]

    def get_power_static_energy(self, idx):
        return self.__power_static_energy[idx]

    def get_static_energy(self):
        return self.__static_energy

    def get_static_energy_max(self):
        return self.__static_energy_max

    def get_static_energy_min(self):
        return self.__static_energy_min

    def get_static_time(self):
        return self.__static_time

    def get_time_dyn_data_energy(self, idx):
        return self.__time_dyn_data_energy[idx]

    def get_dyn_data_energy(self):
        return self.__dyn_data_energy

    def get_dyn_send_energy(self):
        return self.__dyn_send_energy

    def get_dyn_send_time(self):
        return self.__dyn_send_time

    def get_number_storing_msg(self, idx):
        return self.__number_storing_msg[idx]

    def get_energy_st_max(self):
        return self.__energy_st_max

    def get_sending_castle_energy_max(self, idx):
        return self.__sending_castle_energy_max[idx]

    def get_dyn_send_energy_max(self):
        return self.__dyn_send_energy_max

    # ------------------------------------------------------------------------------------------------------------------

    def set_energy_data_reception(self, idx, nb):
        self.__energy_data_reception[idx] = nb

    def set_time_data_reception(self, idx, nb):
        self.__time_data_reception[idx] = nb

    def set_energy_data_transmission(self, idx, nb):
        self.__energy_data_transmission[idx] = nb

    def set_time_data_transmission(self, idx, nb):
        self.__time_data_transmission[idx] = nb

    def set_aver_cur_data_transmission(self, idx, nb):
        self.__aver_cur_data_transmission[idx] = nb

    def set_energy_wut_data(self, idx, nb):
        self.__energy_wut_data[idx] = nb

    def set_time_wut_data(self, idx, nb):
        self.__time_wut_data[idx] = nb

    def set_number_possible_thresh(self, idx, nb):
        self.__number_possible_thresh[idx] = nb

    def set_number_thresh_exceeded(self, idx, nb):
        self.__number_thresh_exceeded[idx] = nb

    def set_number_thresh_not_exceeded(self, idx, nb):
        self.__number_thresh_not_exceeded[idx] = nb

    def set_energy_thresh_exceeded(self, idx, nb):
        self.__energy_thresh_exceeded[idx] = nb

    def set_energy_thresh_not_exceeded(self, idx, nb):
        self.__energy_thresh_not_exceeded[idx] = nb

    def set_time_thresh_exceeded(self, idx, nb):
        self.__time_thresh_exceeded[idx] = nb

    def set_time_thresh_not_exceeeded(self, idx, nb):
        self.__time_thresh_not_exceeeded[idx] = nb

    def set_threshold_interval(self, idx, nb):
        self.__threshold_interval[idx] = nb

    def set_number_polling_occurs(self, idx, nb):
        self.__number_polling_occurs[idx] = nb

    def set_time_polling_occurs(self, idx, nb):
        self.__time_polling_occurs[idx] = nb

    def set_energy_polling_occurs(self, idx, nb):
        self.__energy_polling_occurs[idx] = nb

    def set_id_name(self, idx, nb):
        self.__id_name[idx] = nb

    def set_time_st(self, nb):
        self.__time_st = nb

    def set_energy_st(self, nb):
        self.__energy_st = nb

    def set_time_wum(self, nb):
        self.__time_wum = nb

    def set_number_wum(self, nb):
        self.__number_wum = nb

    def set_energy_wum(self, nb):
        self.__energy_wum = nb

    def set_number_metrics(self, idx, nb):
        self.__number_metrics[idx] = nb

    def set_sending_castle_time(self, idx, nb):
        self.__sending_castle_time[idx] = nb

    def set_sending_castle_energy(self, idx, nb):
        self.__sending_castle_energy[idx] = nb

    def set_percent_static_time(self, nb):
        self.__percent_static_time = nb

    def set_total_aver_cons(self, nb):
        self.__total_aver_cons = nb

    def set_lora_spread_factor(self, nb):
        self.__lora_spread_factor = nb

    def set_wut_st_time(self, nb):
        self.__wut_st_time = nb

    def set_wut_st_energy(self, nb):
        self.__wut_st_energy = nb

    def set_data_tx_st_aver_cur(self, nb):
        self.__data_tx_st_aver_cur = nb

    def set_data_rx_st_time(self, nb):
        self.__data_rx_st_time = nb

    def set_data_rx_st_energy(self, nb):
        self.__data_rx_st_energy = nb

    def set_acc_data_send_nb(self, nb):
        self.__acc_data_send_nb = nb

    def set_lora_acc_thresholds(self, nb):
        self.__lora_acc_thresholds = nb

    def set_time_store_data(self, idx, nb):
        self.__time_store_data[idx] = nb

    def set_energy_store_data(self, idx, nb):
        self.__energy_store_data[idx] = nb

    def set_total_aver_cons_max(self, nb):
        self.__total_aver_cons_max = nb

    def set_total_aver_cons_min(self, nb):
        self.__total_aver_cons_min = nb

    def set_life_estimation(self, nb):
        self.__life_estimation = nb

    def set_life_estimation_min(self, nb):
        self.__life_estimation_min = nb

    def set_time_static_energy(self, idx, nb):
        self.__time_static_energy[idx] = nb

    def set_power_static_energy(self, idx, nb):
        self.__power_static_energy[idx] = nb

    def set_static_energy(self, nb):
        self.__static_energy = nb

    def set_static_time(self, nb):
        self.__static_time = nb

    def set_static_energy_max(self, nb):
        self.__static_energy_max = nb

    def set_static_energy_min(self, nb):
        self.__static_energy_min = nb

    def set_time_dyn_data_energy(self, idx, nb):
        self.__time_dyn_data_energy[idx] = nb

    def set_dyn_data_energy(self, nb):
        self.__dyn_data_energy = nb

    def set_dyn_send_energy(self, nb):
        self.__dyn_send_energy = nb

    def set_dyn_send_time(self, nb):
        self.__dyn_send_time = nb

    def set_number_storing_msg(self, idx, nb):
        self.__number_storing_msg[idx] = nb

    def set_energy_st_max(self, nb):
        self.__energy_st_max = nb

    def set_sending_castle_energy_max(self, idx, nb):
        self.__sending_castle_energy_max[idx] = nb

    def set_dyn_send_energy_max(self, nb):
        self.__dyn_send_energy_max = nb

    # ------------------------------------------------------------------------------------------------------------------

    def append_energy_data_reception(self, nb):
        self.__energy_data_reception.append(nb)

    def append_time_data_reception(self, nb):
        self.__time_data_reception.append(nb)

    def append_energy_data_transmission(self, nb):
        self.__energy_data_transmission.append(nb)

    def append_time_data_transmission(self, nb):
        self.__time_data_transmission.append(nb)

    def append_aver_cur_data_transmission(self, nb):
        self.__aver_cur_data_transmission.append(nb)

    def append_energy_wut_data(self, nb):
        self.__energy_wut_data.append(nb)

    def append_time_wut_data(self, nb):
        self.__time_wut_data.append(nb)

    def append_number_possible_thresh(self, nb):
        self.__number_possible_thresh.append(nb)

    def append_number_thresh_exceeded(self, nb):
        self.__number_thresh_exceeded.append(nb)

    def append_number_thresh_not_exceeded(self, nb):
        self.__number_thresh_not_exceeded.append(nb)

    def append_energy_thresh_exceeded(self, nb):
        self.__energy_thresh_exceeded.append(nb)

    def append_energy_thresh_not_exceeded(self, nb):
        self.__energy_thresh_not_exceeded.append(nb)

    def append_time_thresh_exceeded(self, nb):
        self.__time_thresh_exceeded.append(nb)

    def append_time_thresh_not_exceeded(self, nb):
        self.__time_thresh_not_exceeded.append(nb)

    def append_threshold_interval(self, nb):
        self.__threshold_interval.append(nb)

    def append_number_polling_occurs(self, nb):
        self.__number_polling_occurs.append(nb)

    def append_time_polling_occurs(self, nb):
        self.__time_polling_occurs.append(nb)

    def append_energy_polling_occurs(self, nb):
        self.__energy_polling_occurs.append(nb)

    def append_id_name(self, nb):
        self.__id_name.append(nb)

    def append_number_metrics(self, nb):
        self.__number_metrics.append(nb)

    def append_sending_castle_time(self, nb):
        self.__sending_castle_time.append(nb)

    def append_sending_castle_energy(self, nb):
        self.__sending_castle_energy.append(nb)

    def append_time_store_data(self, nb):
        self.__time_store_data.append(nb)

    def append_energy_store_data(self, nb):
        self.__energy_store_data.append(nb)

    def append_time_static_energy(self, nb):
        self.__time_static_energy.append(nb)

    def append_power_static_energy(self, nb):
        self.__power_static_energy.append(nb)

    def append_time_dyn_data_energy(self, nb):
        self.__time_dyn_data_energy.append(nb)

    def append_power_dyn_data_energy(self, nb):
        self.__power_dyn_data_energy.append(nb)

    def append_number_storing_msg(self, nb):
        self.__number_storing_msg.append(nb)

    def append_sending_castle_energy_max(self, nb):
        self.__sending_castle_energy_max.append(nb)
    # ------------------------------------------------------------------------------------------------------------------

    def get_max_peak_value(self):
        return self.__max_peak_value

    def get_time_evt(self, ind):
        return self.__time_evt[ind]

    def get_number_evt(self, ind):
        return self.__number_evt[ind]

    def get_energy_evt(self, ind):
        return self.__energy_evt[ind]

    def set_max_peak_value(self, nb):
        self.__max_peak_value = nb

    def set_number_evt(self, ind, nb):
        self.__number_evt[ind] = nb

    def set_time_evt(self, ind, nb):
        self.__time_evt[ind] = nb

    def set_energy_evt(self, ind, nb):
        self.__energy_evt[ind] = nb

    def append_time_evt(self, nb):
        self.__time_evt.append(nb)

    def append_number_evt(self, nb):
        self.__number_evt.append(nb)

    def append_energy_evt(self, nb):
        self.__energy_evt.append(nb)

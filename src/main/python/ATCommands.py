AT_PING_REQ = "AT+PNG?"
AT_PING_RES = "+PNG:"  # +PNG: <motherboard-id>


AT_LIST_REQ = "AT+LS?"
AT_LIST_RES = "+LS:"  # +LS: {<sensor1> <sensor2> ...}


AT_POLL_REQ = "AT+POL?"  # <sensor-address> <metric>
AT_POLL_RES = "+POL:"  # <poll-interval>
AT_POLL_CMD = "AT+POL="  # <sensor-address> <metric> <poll-interval>


AT_TH_REQ = "AT+TH?"  # sensor-address> <metric>
AT_TH_RES = "+TH:"  # +TH: <thresholds-enabled> <threshold-level-low> <threshold-level-high>

AT_TH_E_CMD = "AT+TE="  # <sensor-address> <metric> <thresholds-enabled>
AT_TH_L_CMD = "AT+TLL="  # <sensor-address> <metric> <threshold-level-low>
AT_TH_H_CMD = "AT+TLH="  # <sensor-address> <metric> <threshold-level-high>

AT_ACC_REQ = "AT+ACC?"  # OK | ERROR <code>
AT_ACC_CMD = "AT+ACC="
AT_ACC_RES = "+ACC:"    # +ACC: <0|1>

AT_CLOSE = "AT+CLS"


def remove_cmd_str(_str, _cmd) -> str:
    return _str.replace(_cmd, "")


def clean_response(_str) -> str:
    return _str.strip()


def readline(_ser):
    _res = None
    _msg = _ser.readline()

    if _msg != b'':
        _res = _msg.decode().strip()

    return _res


def close(_ser, _debug):
    _err = True

    _cmd = (AT_CLOSE + "\r\n").encode('utf-8')
    _debug.write("COM", F"TX: {_cmd}")
    _ser.write(_cmd)
    response = readline(_ser)
    _debug.write("COM", F"RX: {response}")


def upload_sensor(sensor, _ser, _debug):
    _err = True

    _cmd = (AT_POLL_CMD + sensor.get_addr() + " 01 " +
            str(sensor.get_polling_interval_sec())+"\r\n").encode('utf-8')
    _debug.write("COM", F"TX: {_cmd}")
    _ser.write(_cmd)
    response = readline(_ser)
    _debug.write("COM", F"RX: {response}")

    # TODO de rest ook nog eh!

    for metric_idx in range(sensor._num_metrics):

        AT_TH_E_CMD = "AT+TE="  # <sensor-address> <metric> <thresholds-enabled>
        AT_TH_L_CMD = "AT+TLL="  # <sensor-address> <metric> <threshold-level-low>
        AT_TH_H_CMD = "AT+TLH="  # <sensor-address> <metric> <threshold-level-high>

        enabled = "1" if sensor._thresholds_enabled[metric_idx] else "0"

        _cmd = (AT_TH_E_CMD + sensor.get_addr() + " " +
                metric_str_arr[metric_idx] + " "+enabled+"\r\n").encode('utf-8')

        _ser.write(_cmd)
        _debug.write("COM", F"TX: {_cmd}")
        response = readline(_ser)
        _debug.write("COM", F"RX: {response}")

        _cmd = (AT_TH_L_CMD + sensor.get_addr() + " " +
                metric_str_arr[metric_idx] + " "+str(sensor._thresholds_low[metric_idx])+"\r\n").encode('utf-8')

        _ser.write(_cmd)
        _debug.write("COM", F"TX: {_cmd}")
        response = readline(_ser)
        _debug.write("COM", F"RX: {response}")

        _cmd = (AT_TH_H_CMD + sensor.get_addr() + " " +
                metric_str_arr[metric_idx] + " "+str(sensor._thresholds_high[metric_idx])+"\r\n").encode('utf-8')

        _ser.write(_cmd)
        _debug.write("COM", F"TX: {_cmd}")
        response = readline(_ser)
        _debug.write("COM", F"RX: {response}")


def handle_ping(_ser, _debug) -> (bool, str):
    _motherboard_id = None
    _err = True

    _cmd = (AT_PING_REQ + "\r\n").encode('utf-8')
    _debug.write("COM", F"TX: {_cmd}")
    _ser.write(_cmd)
    response = readline(_ser)
    _debug.write("COM", F"RX: {response}")
    if AT_PING_RES in response:
        _motherboard_id = clean_response(remove_cmd_str(response, AT_PING_RES))
        _err = False

    return (_err, _motherboard_id)

def set_accumulation(_ser, _debug, enable=False):
    if enable is True:
        _cmd = (AT_ACC_CMD + "1" + "\r\n").encode('utf-8')
    else:
        _cmd = (AT_ACC_CMD + "0" + "\r\n").encode('utf-8')
    _err = True
    _acc = 0

    _ser.write(_cmd)
    _debug.write("COM", F"TX: {_cmd}")
    response = readline(_ser)
    _debug.write("COM", F"RX: {response}")
    if AT_ACC_RES in response:
        _err = False
        _acc = clean_response(remove_cmd_str(response, AT_ACC_RES))

    return (_err, _acc)

def request_sensors(_ser, _debug):
    _sensors = []
    _err = True
    _cmd = (AT_LIST_REQ + "\r\n").encode('utf-8')
    _ser.write(_cmd)
    _debug.write("COM", F"TX: {_cmd}")
    response = readline(_ser)
    _debug.write("COM", F"RX: {response}")
    if AT_LIST_RES in response:
        _clean_res = clean_response(remove_cmd_str(response, AT_LIST_RES))
        _raw_sensor_arr = _clean_res.split(" ")
        _sensors = [Sensor(s) for s in _raw_sensor_arr]
        _err = False
    return (_err, _sensors)


metric_str_arr = ["01", "02", "03", "04"]


def load_data(sensor, _debug, _ser):
    _err = True
    _cmd = (AT_POLL_REQ + " " + sensor.get_addr() + " 01\r\n").encode('utf-8')
    _ser.write(_cmd)
    _debug.write("COM", F"TX: {_cmd}")
    response = readline(_ser)
    _debug.write("COM", F"RX: {response}")
    if AT_POLL_RES in response:
        _clean_res = clean_response(remove_cmd_str(response, AT_POLL_RES))
        sensor._polling_enabled = int(_clean_res) > 0
        sensor._polling_interval_sec = int(_clean_res)
        _err = False

    for metric_idx in range(sensor._num_metrics):
        _cmd = (AT_TH_REQ + " " + sensor.get_addr() + " " +
                metric_str_arr[metric_idx] + "\r\n").encode('utf-8')
        _ser.write(_cmd)
        _debug.write("COM", F"TX: {_cmd}")
        response = readline(_ser)
        _debug.write("COM", F"RX: {response}")
        if AT_TH_RES in response:
            _clean_res = clean_response(remove_cmd_str(response, AT_TH_RES))
            _raw_th_arr = _clean_res.split(" ")
            sensor._thresholds_enabled[metric_idx] = _raw_th_arr[0] == "1"
            sensor._thresholds_low[metric_idx] = _raw_th_arr[1]
            sensor._thresholds_high[metric_idx] = _raw_th_arr[2]
            _err = False

    return _err

TH_HIGH = 0
TH_LOW = 1

class Sensor:

    def __init__(self, _id):
        assert len(_id) == 4, "Wrong sensor id length"

        self._sensor_mapping = {
            "01": "Sound Sensor",
            "02": "Button Sensor",
            "03": "Environmental Sensor",
            "04": "Power Sensor"
        }

        self._num_metrics_mapping = {
            "01": 1,
            "02": 0,
            "03": 4,
            "04": 2
        }

        self._metric_labels_mapping = {
            "01": ["Sound Level [dBa]"],
            "02": [],
            "03": ["Temperature °C", "Pressure [hPa]", "Air Quality Indication [-]", "Humidity (%)"],
            "04": ["Battery Level [V]", "Light Intensity [lux]"]
        }

        self._addr = _id[:2]
        self._type = _id[2:]
        self._num_metrics = self._num_metrics_mapping[self._type]
        self._sensor_name = self._sensor_mapping[self._type]
        self._metric_labels = self._metric_labels_mapping[self._type]

        self._thresholds_high = [None]*self._num_metrics
        self._thresholds_low = [None]*self._num_metrics
        self._thresholds_enabled = [False for i in range(self._num_metrics)]

        self._polling_interval_sec = 65535

    def get_name(self):
        return self._sensor_name

    def get_addr(self):
        return self._addr

    def get_polling_interval_sec(self):
        return self._polling_interval_sec

    def get_num_metrics(self):
        return self._num_metrics

    def convert_metric_value(self, value, metric_idx=0, to_machine=True):
        value = float(value)
        metric_str = self._metric_labels[metric_idx]
        new_value = None
        if metric_str == "Temperature °C":
            if to_machine:
                new_value = (value + 50) * 100
            else:
                new_value = (value / 100.0) - 50
        elif metric_str == "Sound Level [dBa]":
            if to_machine:
                new_value = value * 600
            else:
                new_value = value / 600
        elif metric_str == "Humidity (%)":
            if to_machine:
                new_value = value * 100
            else:
                new_value = value / 100
        elif metric_str == "Battery Level [V]":
            if to_machine:
                new_value = value*10000
            else:
                new_value = value/10000
        else:
            # value is the same
            new_value = value
        return new_value

    def get_thresholds(self, which_th=TH_HIGH, to_machine=False):
        if which_th == TH_HIGH:
            return_what =  self._thresholds_high
        else:
            return_what = self._thresholds_low
            
        return [self.convert_metric_value(value=v,metric_idx=idx, to_machine=to_machine) for idx, v in enumerate(return_what)]

    def get_thresholds_enabled(self, id):
        return self._thresholds_enabled[id]

    def set_threshold(self, value, metric_idx=0, to_machine=True, which_th=TH_HIGH):
        new_value = self.convert_metric_value(value= value, metric_idx=metric_idx, to_machine=to_machine)

        if which_th == TH_HIGH:
            self._thresholds_high[metric_idx] = int(new_value)
        else:
            self._thresholds_low[metric_idx] = int(new_value)

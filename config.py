# config.py
import yaml
from utils import error

class Config:
    def __init__(self, filename, radio_id):
        self.raw_config = self._load_radio_config(filename, radio_id)
        self.channel_defaults = self.raw_config['channel_defaults']
        self.field_names = list(self.channel_defaults.keys())
        self.channel_csv_field_name = {i: n for i, n in enumerate(self.field_names)}
        self.channel_csv_default_value = {i: self.channel_defaults[n] for i, n in enumerate(self.field_names)}
        self.field_index = {n: i for i, n in enumerate(self.field_names)}
        self._set_constants()
        self._set_field_indices()

    def _load_radio_config(self, filename, radio_id):
        with open(filename, 'r') as f:
            data = yaml.safe_load(f)
        if radio_id not in data['radio']:
            error(f"Radio ID {radio_id} not found in {filename}")
        return data['radio'][radio_id]['configuration']

    def _set_constants(self):
        c = self.raw_config
        self.SCANLIST_LIMIT = c['max_channels_per_scanlist']
        self.ZONE_CHANNEL_LIMIT = c['max_channel_per_zone']
        self.LENGTH_CHAN_NAME = c['max_channel_name_characters']
        self.LENGTH_ZONE_NAME = c['max_zone_name_characters']
        self.LENGTH_SCANLIST_NAME = c['max_scanlist_name_characters']
        self.MIN_FREQUENCY = c['min_frequency']
        self.MAX_FREQUENCY = c['max_frequency']
        self.COLOR_CODE_MIN = c['color_code_min']
        self.COLOR_CODE_MAX = c['color_code_max']
        self.CTCSS_MIN = c['ctcss_min']
        self.CTCSS_MAX = c['ctcss_max']
        v = c['values']
        self.VAL_ANALOG = v['channel_type']['analog']
        self.VAL_DIGITAL = v['channel_type']['digital']
        self.VAL_NO_TIME_SLOT = v['time_slot_none']
        self.VAL_TX_PERMIT_FREE = v['tx_permit']['channel_free']
        self.VAL_TX_PERMIT_SAME = v['tx_permit']['same_color_code']
        self.VAL_TX_PERMIT_DIFFERENT = v['tx_permit']['different_color_code']
        self.VAL_TX_PERMIT_ALWAYS = v['tx_permit']['always']
        self.VAL_CALL_TYPE_GROUP = v['call_type']['group_call']
        self.VAL_CALL_TYPE_PRIVATE = v['call_type']['private_call']
        self.VAL_CTCSS_DCS = v['squelch_mode_ctcss_dcs']
        self.VAL_DMR_MODE_SIMPLEX = v['dmr_mode']['simplex']
        self.VAL_DMR_MODE_REPEATER = v['dmr_mode']['repeater']
        self.POWER_LEVELS = set(v['power_levels'])
        self.BANDWIDTHS = set(v['bandwidths'])
        self.TIMESLOTS = set(v['timeslots'])
        self.ON_OFF = set(v['on_off'])
        self.LIST_SEPARATOR = c['list_separator']

    def _set_field_indices(self):
        fi = self.field_index
        self.CHAN_NUM = fi["No."]
        self.CHAN_NAME = fi["Channel Name"]
        self.CHAN_RX_FREQ = fi["Receive Frequency"]
        self.CHAN_TX_FREQ = fi["Transmit Frequency"]
        self.CHAN_MODE = fi["Channel Type"]
        self.CHAN_POWER = fi["Transmit Power"]
        self.CHAN_BANDWIDTH = fi["Band Width"]
        self.CHAN_CTCSS_DEC = fi["CTCSS/DCS Decode"]
        self.CHAN_CTCSS_ENC = fi["CTCSS/DCS Encode"]
        self.CHAN_CONTACT = fi["Contact"]
        self.CHAN_CALL_TYPE_OLD = fi["Contact Call Type"]
        self.CHAN_TG_ID = fi["Contact TG/DMR ID"]
        self.CHAN_TX_PERMIT = fi["Busy Lock/TX Permit"]
        self.CHAN_SQUELCH_MODE = fi["Squelch Mode"]
        self.CHAN_TIME_SLOT = fi["Slot"]
        self.CHAN_SCANLIST_NAME = fi["Scan List"]
        self.CHAN_PTT_PROHIBIT = fi.get("PTT Prohibit", None)
        self.CHAN_DMR_MODE = fi.get("DMR MODE", None)
        if "RX Color Code" in fi:
            self.CHAN_RX_COLOR_CODE = fi["RX Color Code"]
            self.CHAN_TX_COLOR_CODE = fi.get("TxCC", None)
            self.IS_OLD_FW = False
        elif "Color Code" in fi:
            self.CHAN_RX_COLOR_CODE = fi["Color Code"]
            self.CHAN_TX_COLOR_CODE = None
            self.IS_OLD_FW = True
        else:
            error("No color field found in radio configuration")
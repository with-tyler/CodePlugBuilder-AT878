# validators.py
import re
from utils import error

def validate_bandwidth(config, value, location_str=''):
    return _validate_membership(config, value, config.BANDWIDTHS, "Bandwidth", location_str)

def validate_call_type(config, value, location_str=''):
    valid = {config.VAL_CALL_TYPE_GROUP, config.VAL_CALL_TYPE_PRIVATE}
    return _validate_membership(config, value, valid, "Call Type", location_str)

def validate_channel_name(config, value, location_str=''):
    return _validate_string_length("Channel Name", value, config.LENGTH_CHAN_NAME, location_str)

def validate_color_code(config, value, location_str=''):
    return _validate_num_in_range(config, "Color Code", value, config.COLOR_CODE_MIN, config.COLOR_CODE_MAX, location_str)

def validate_contact(config, value, location_str=''):
    return _validate_string_length("Contact (aka Talk Group)", value, config.LENGTH_CHAN_NAME, location_str)

def validate_ctcss(config, value, location_str=''):
    if value == 'Off':
        return value
    if re.match(r'^D[0-9A-Za-z]+', value) and len(value) < 10:
        return value
    return _validate_num_in_range(config, 'CTCSS/DCS', value, config.CTCSS_MIN, config.CTCSS_MAX, location_str)

def validate_freq(config, value, location_str=''):
    return _validate_num_in_range(config, 'Frequency', value, config.MIN_FREQUENCY, config.MAX_FREQUENCY, location_str)

def validate_name(config, value, location_str=''):
    return _validate_string_length('Channel Name', value, config.LENGTH_CHAN_NAME, location_str)

def validate_power(config, value, location_str=''):
    return _validate_membership(config, value, config.POWER_LEVELS, "Power Level", location_str)

def validate_timeslot(config, value, location_str=''):
    return _validate_membership(config, value, config.TIMESLOTS, "Time Slot", location_str)

def validate_tx_prohibit(config, value, location_str=''):
    return _validate_membership(config, value, config.ON_OFF, "TX Prohibit", location_str)

def validate_tx_permit(config, value, location_str=''):
    valid = {config.VAL_TX_PERMIT_FREE, config.VAL_TX_PERMIT_SAME, config.VAL_TX_PERMIT_DIFFERENT, config.VAL_TX_PERMIT_ALWAYS}
    return _validate_membership(config, value, valid, "TX Permit", location_str)

def validate_zone(config, value, location_str=''):
    return _validate_string_length('Zone', value, config.LENGTH_ZONE_NAME, location_str)

def validate_sort_mode(value):
    valid = {"alpha", "repeaters-first", "analog-first", "analog_and_others_first"}
    if value not in valid:
        error(f"Invalid Sort Order: '{value}' is not one of: {', '.join(valid)}")
    return value

def validate_hotspot_mode(value):
    valid = {"always", "same-color-code"}
    if value not in valid:
        error(f"Invalid Hotspot TX Permit: '{value}' is not one of: {', '.join(valid)}")
    return value

def validate_nickname_mode(value):
    valid = {"off", "prefix", "suffix", "prefix-forced", "suffix-forced"}
    if value not in valid:
        error(f"Invalid Nickname Mode: '{value}' is not one of: {', '.join(valid)}")
    return value

def validate_talkgroup_sort(value):
    valid = {"input", "id", "name"}
    if value not in valid:
        error(f"Invalid Talkgroup Sort: '{value}' is not one of: {', '.join(valid)}")
    return value

def _validate_membership(config, value, valid_set, error_type, location_str=''):
    if value not in valid_set:
        error(f"Invalid {error_type}: '{value}' is not one of: {', '.join(sorted(valid_set))} {location_str}")
    return value

def _validate_num_in_range(config, type_name, value, min_val, max_val, location_str=''):
    try:
        num = float(value)
        if num < min_val or num > max_val:
            error(f"Invalid {type_name}: '{value}' must be between {min_val} and {max_val} (inclusive) {location_str}")
    except ValueError:
        error(f"Invalid {type_name}: '{value}' must be a number between {min_val} and {max_val} (inclusive) {location_str}")
    return value

def _validate_string_length(type_name, value, length, location_str=''):
    if len(value) > length:
        error(f"Invalid {type_name}: '{value}' is more than {length} characters {location_str}")
    return value
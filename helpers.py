# helpers.py
import re
from utils import warning

def handle_repeater_value(value):
    subvalues = value.split(';')
    timeslot = subvalues[0] if subvalues else ''
    call_type = 'Group Call'  # Default, but will be validated later
    for v in subvalues[1:]:
        if v == 'P':
            call_type = 'Private Call'
    return timeslot, call_type

def handle_nickname_values(value):
    subvalues = value.split(';')
    full = subvalues[0] if subvalues else ''
    nick = subvalues[1] if len(subvalues) > 1 else ''
    return full, nick

def make_channel_name(config, nickname_mode, zone_nick, chan_full, chan_nick=''):
    if nickname_mode == 'off' or not zone_nick:
        return chan_full
    if not chan_nick:
        chan_nick = chan_full
    if nickname_mode in ('prefix-forced', 'suffix-forced'):
        chan_full = chan_nick
    if len(zone_nick) + len(chan_full) + 1 <= config.LENGTH_CHAN_NAME:
        chan_name, sep = chan_full, ' '
    elif len(zone_nick) + len(chan_nick) + 1 <= config.LENGTH_CHAN_NAME:
        chan_name, sep = chan_nick, ' '
    elif len(zone_nick) + len(chan_nick) <= config.LENGTH_CHAN_NAME:
        chan_name, sep = chan_nick, ''
    else:
        raise ValueError(f"Can't make a channel name fit into {config.LENGTH_CHAN_NAME} characters for '{zone_nick}' and '{chan_nick}'")
    if not re.match(r'^[A-Za-z0-9]', zone_nick):
        sep = ''
    if nickname_mode in ('prefix', 'prefix-forced'):
        return f"{zone_nick}{sep}{chan_name}"
    return f"{chan_name}{sep}{zone_nick}"

def tx_permit(config, hotspot_tx_permit, chan_config):
    result = config.VAL_TX_PERMIT_SAME
    if hotspot_tx_permit == "always" and chan_config[config.CHAN_RX_FREQ] == chan_config[config.CHAN_TX_FREQ]:
        result = config.VAL_TX_PERMIT_ALWAYS
    elif config.CHAN_TX_COLOR_CODE is not None and chan_config.get(config.CHAN_RX_COLOR_CODE) != chan_config.get(config.CHAN_TX_COLOR_CODE):
        result = config.VAL_TX_PERMIT_DIFFERENT
    return result

def dmr_mode(config, chan_config):
    result = config.VAL_DMR_MODE_SIMPLEX
    if chan_config[config.CHAN_RX_FREQ] != chan_config[config.CHAN_TX_FREQ]:
        result = config.VAL_DMR_MODE_REPEATER
    return result

def channel_order_name(config, data, chan_config, sort_mode):
    index1 = 9999
    index2 = 0
    chan_name = chan_config[config.CHAN_NAME]
    if sort_mode != 'alpha':
        if chan_config[config.CHAN_MODE] == config.VAL_DIGITAL:
            contact = chan_config.get(config.CHAN_CONTACT)
            if contact in data.talkgroup_order:
                index1 = data.talkgroup_order[contact]
        elif chan_config[config.CHAN_MODE] == config.VAL_ANALOG:
            index2 = data.analog_channel_index
    return f"{index1:04d}{index2:04d}{chan_name}"

def get_overflow_scanlist_name(config, scanlist_channel_counts, base_name, scanlist_limit):
    num = 1
    while True:
        if num == 1:
            name = base_name
        else:
            name = f"{base_name}_OF{num}"
        if scanlist_channel_counts[name] < scanlist_limit:
            return name
        num += 1
        if num > 1000:
            raise ValueError(f"Infinite loop detected in scanlist overflow for '{base_name}'")

def zone_sort_key(sort_mode, zone_type):
    def key_func(a):
        a_i = zone_type.get(a, 9999)
        if sort_mode == 'alpha':
            return a.lower()
        elif sort_mode == 'repeaters-first':
            return (0 if zone_type.get(a, 'analog') == 'digital_repeaters' else 1, a.lower())
        elif sort_mode == 'analog-first':
            return (0 if zone_type.get(a, 'digital') == 'analog' else 1, a.lower())
        elif sort_mode == 'analog_and_others_first':
            return (0 if zone_type.get(a, 'digital_repeaters') in ['analog', 'digital_others'] else 1, a.lower())
        return f"{a_i:04d}{a.lower()}"
    return key_func

def generic_row_builder(row_number, name, row_record, details_func, row_limit, warning_name, list_separator):
    values = [row_number, name]
    channels = []
    rx_freqs = []
    tx_freqs = []
    i = 0
    for row_details in sorted(row_record, key=lambda x: x.lower()):
        order, chan_name, rx_freq, tx_freq = row_details.split('\t')
        chan_name = chan_name.rstrip()
        if row_limit > 0 and i >= row_limit:
            warning(f"{warning_name} '{name}' has more than {row_limit} channels. Truncated to first {row_limit}.")
            break
        channels.append(chan_name)
        rx_freqs.append(rx_freq)
        tx_freqs.append(tx_freq)
        i += 1
    values.append(list_separator.join(channels))
    values.append(list_separator.join(rx_freqs))
    values.append(list_separator.join(tx_freqs))
    first_chan = channels[0] if channels else ''
    first_rx = rx_freqs[0] if rx_freqs else ''
    first_tx = tx_freqs[0] if tx_freqs else ''
    details_func(values, first_chan, first_rx, first_tx)
    return values

def _zone_row_details(values, channel0, rx0, tx0):
    values.extend([channel0, rx0, tx0, channel0, rx0, tx0])

def _scanlist_row_details(values, channel0, rx0, tx0):
    values.extend(["Off", "Off", "", "", "", "", "", "Selected", "0.5", "0.5", "0.1", "0.1"])
#!/usr/bin/env python3

import csv
import os
import argparse
from collections import defaultdict
import re
import sys

# Constants for channel CSV fields
CHAN_NUM = 0
CHAN_NAME = 1
CHAN_RX_FREQ = 2
CHAN_TX_FREQ = 3
CHAN_MODE = 4
CHAN_POWER = 5
CHAN_BANDWIDTH = 6
CHAN_CTCSS_DEC = 7
CHAN_CTCSS_ENC = 8
CHAN_CONTACT = 9
CHAN_CALL_TYPE_OLD = 10
CHAN_TG_ID = 11
CHAN_TX_PERMIT = 13
CHAN_SQUELCH_MODE = 14
CHAN_RX_COLOR_CODE = 20
CHAN_TIME_SLOT = 21
CHAN_SCANLIST_NAME = 22
CHAN_TX_PROHIBIT = 24
CHAN_DMR_MODE = 45
CHAN_PTT_PROHIBIT = 24
ACB_ZONE_NICKNAME = 1000
CHAN_TX_COLOR_CODE = 1001  # New field for TX Color Code

# Constants for values
VAL_DIGITAL = 'D-Digital'
VAL_ANALOG = 'A-Analog'
VAL_NO_TIME_SLOT = '-'
VAL_TX_PERMIT_FREE = 'ChannelFree'
VAL_TX_PERMIT_SAME = 'Same Color Code'
VAL_TX_PERMIT_DIFFERENT = 'Different Color Code'
VAL_TX_PERMIT_ALWAYS = 'Always'
VAL_CALL_TYPE_GROUP = 'Group Call'
VAL_CALL_TYPE_PRIVATE = 'Private Call'
VAL_CTCSS_DCS = 'CTCSS/DCS'
VAL_DMR_MODE_SIMPLEX = 0
VAL_DMR_MODE_REPEATER = 1
LENGTH_CHAN_NAME = 16
SCANLIST_LIMIT = 50  # Maximum channels per scanlist

# Global variables
global_sort_mode = 'alpha'
global_hotspot_tx_permit = 'same-color-code'
global_nickname_mode = 'off'
global_talkgroup_sort = 'input'
global_line_number = 0
global_file_name = 'none'
global_channel_number = 1
channel_csv_field_name = {}
channel_csv_default_value = {}
talkgroup_mapping = {}
zone_config = defaultdict(list)
zone_order = {}
zone_type = {}  # Dictionary to track zone types
scanlist_config = defaultdict(list)
talkgroup_config = {}
talkgroup_order = {}
scanlist_channel_counts = defaultdict(int)  # Dictionary to track channel counts per scanlist
all_talkgroups = []  # List to store all talkgroups from input file
analog_channel_index = 0

def main():
    args = handle_command_line_args()

    if args.generate_templates:
        templates_dir = './Templates'
        generate_templates(templates_dir)
        print(f"Templates generated in: {os.path.abspath(templates_dir)}")
        return

    output_dir = args.output_directory or './Output'
    os.makedirs(output_dir, exist_ok=True)

    analog_filename = args.analog_csv
    digital_others_filename = args.digital_others_csv
    digital_repeaters_filename = args.digital_repeaters_csv
    talkgroups_filename = args.talkgroups_csv
    config_directory = args.config

    read_talkgroups(talkgroups_filename)
    read_channel_csv_default(os.path.join(config_directory, 'channel-defaults.csv'))

    with open(os.path.join(output_dir, 'channels.csv'), 'w', newline='', encoding='utf-8') as fh:
        csv_out = csv.writer(fh, quoting=csv.QUOTE_ALL, lineterminator='\r\n')
        print_channel_header(csv_out)
        process_dmr_others_file(csv_out, digital_others_filename)
        process_dmr_repeater_file(csv_out, digital_repeaters_filename)
        process_analog_file(csv_out, analog_filename)

    write_zone_file(os.path.join(output_dir, 'zones.csv'))
    write_scanlist_file(os.path.join(output_dir, 'scanlists.csv'))
    write_talkgroup_file(os.path.join(output_dir, 'talkgroups.csv'))

    if args.dmr_id:
        write_radio_id_list(args.dmr_id, output_dir)

    print(f"Output files generated in: {os.path.abspath(output_dir)}")

# CSV Output Routines
def write_zone_file(filename):
    headers = ["No.", "Zone Name", "Zone Channel Member", "Zone Channel Member RX Frequency", "Zone Channel Member TX Frequency",
               "A Channel", "A Channel RX Frequency", "A Channel TX Frequency",
               "B Channel", "B Channel RX Frequency", "B Channel TX Frequency"]
    generate_csv_file(filename, headers, zone_config, zone_row_builder, zone_sort_key)

def write_scanlist_file(filename):
    headers = ["No.", "Scan List Name", "Scan Channel Member", "Scan Channel Member RX Frequency", "Scan Channel Member TX Frequency",
               "Scan Mode", "Priority Channel Select", "Priority Channel 1", "Priority Channel 1 RX Frequency",
               "Priority Channel 1 TX Frequency", "Priority Channel 2", "Priority Channel 2 RX Frequency",
               "Priority Channel 2 TX Frequency", "Revert Channel", "Look Back Time A[s]", "Look Back Time B[s]",
               "Dropout Delay Time[s]", "Dwell Time[s]"]
    generate_csv_file(filename, headers, scanlist_config, scanlist_row_builder, str.lower, log_scanlists=True)

def write_talkgroup_file(filename):
    headers = ["No.", "Radio ID", "Name", "Country", "Remarks", "Call Type", "Call Alert"]
    with open(filename, 'w', newline='', encoding='utf-8') as fh:
        csv_out = csv.writer(fh, quoting=csv.QUOTE_ALL, lineterminator='\r\n')
        csv_out.writerow(headers)
        talkgroups = []
        for row in all_talkgroups[1:]:  # Skip header row
            radio_id = row[0].strip()
            name = row[1].strip()
            call_type = row[2].strip() if len(row) > 2 and row[2].strip() else "Group Call"
            call_alert = row[3].strip() if len(row) > 3 and row[3].strip() else "None"
            talkgroups.append((radio_id, name, call_type, call_alert))
        if global_talkgroup_sort == 'id':
            talkgroups.sort(key=lambda x: int(x[0]))
        elif global_talkgroup_sort == 'name':
            talkgroups.sort(key=lambda x: x[1].lower())
        # else: 'input', keep original order
        row_num = 1
        for tg in talkgroups:
            csv_out.writerow([row_num, tg[0], tg[1], "", "", tg[2], tg[3]])
            row_num += 1

def write_radio_id_list(dmr_id, output_dir):
    headers = ["No.", "Radio ID", "Name"]
    with open(os.path.join(output_dir, 'radio_id_list.csv'), 'w', newline='', encoding='utf-8') as fh:
        csv_out = csv.writer(fh, quoting=csv.QUOTE_ALL, lineterminator='\r\n')
        csv_out.writerow(headers)
        # Validate DMR ID
        try:
            dmr_id_num = int(dmr_id)
            if dmr_id_num <= 0:
                raise ValueError("DMR ID must be a positive integer")
        except ValueError:
            error(f"Invalid DMR ID: '{dmr_id}' must be a positive integer")
        # Validate name length (same as channel name validation)
        dmr_name = 'DMR ID'  # Use DMR ID as name for consistency
        if len(dmr_name) > LENGTH_CHAN_NAME:
            error(f"Invalid DMR ID name: '{dmr_name}' is more than {LENGTH_CHAN_NAME} characters")
        csv_out.writerow([1, dmr_id, dmr_name])

def zone_row_builder(zone_number, zone_name, zone_record):
    return generic_row_builder(zone_number, zone_name, zone_record, _zone_row_details, 250, "Zone")

def scanlist_row_builder(scan_number, scan_name, scan_record):
    return generic_row_builder(scan_number, scan_name, scan_record, _scanlist_row_details, SCANLIST_LIMIT, "Scanlist")

def generic_row_builder(row_number, name, row_record, details_func, row_limit, warning_name):
    values = [row_number, name]
    channels = []
    rx_freqs = []
    tx_freqs = []
    i = 0
    for row_details in sorted(row_record, key=lambda x: x.lower()):
        order, chan_name, rx_freq, tx_freq = row_details.split('\t')
        chan_name = chan_name.rstrip()
        if row_limit > 0 and i >= row_limit:
            warning(f"{warning_name} '{name}' has more than {row_limit} channels. "
                    f"It has been truncated to the first {row_limit} channels to keep the CPS software happy.")
            break
        channels.append(chan_name)
        rx_freqs.append(rx_freq)
        tx_freqs.append(tx_freq)
        i += 1
    values.append('|'.join(channels))
    values.append('|'.join(rx_freqs))
    values.append('|'.join(tx_freqs))
    details_func(values, channels[0] if channels else '', rx_freqs[0] if rx_freqs else '', tx_freqs[0] if tx_freqs else '')
    return values

def _zone_row_details(values, channel0, rx0, tx0):
    values.extend([channel0, rx0, tx0, channel0, rx0, tx0])

def _scanlist_row_details(values, channel0, rx0, tx0):
    values.extend(["Off", "Off", "", "", "", "", "", "Selected", "0.5", "0.5", "0.1", "0.1"])

def generate_csv_file(filename, headers, data, row_func, sort_key_func, log_scanlists=False):
    with open(filename, 'w', newline='', encoding='utf-8') as fh:
        csv_out = csv.writer(fh, quoting=csv.QUOTE_ALL, lineterminator='\r\n')
        csv_out.writerow(headers)
        row_num = 1
        for key in sorted(data.keys(), key=sort_key_func):
            row = row_func(row_num, key, data[key])
            csv_out.writerow(row)
            if log_scanlists:
                channel_count = len(data[key])
                print(f"Scanlist '{key}' contains {channel_count} channels")
            row_num += 1

def print_channel_header(csv_out):
    output = [channel_csv_field_name[index] for index in sorted(channel_csv_field_name.keys())]
    csv_out.writerow(output)

# Sort Functions
def zone_sort_key(a):
    a_i = zone_order.get(a, 9999)
    if global_sort_mode == 'alpha':
        return a.lower()
    elif global_sort_mode == 'repeaters-first':
        return (0 if zone_type.get(a, 'analog') == 'digital_repeaters' else 1, a.lower())
    elif global_sort_mode == 'analog-first':
        return (0 if zone_type.get(a, 'digital') == 'analog' else 1, a.lower())
    elif global_sort_mode == 'analog_and_others_first':
        group_key = 0 if zone_type.get(a, 'digital_repeaters') in ['analog', 'digital_others'] else 1
        return (group_key, a.lower())
    return f"{a_i:04d}{a.lower()}"

# CSV Input Routines
def process_analog_file(csv_out, filename):
    headers = ["Zone", "Channel Name", "Bandwidth", "Power", "RX Freq", "TX Freq", "CTCSS Decode", "CTCSS Encode", "TX Prohibit"]
    process_csv_file_with_header(csv_out, filename, "Analog", headers, analog_csv_field_extractor)

def analog_csv_field_extractor(row):
    chan_config = {
        CHAN_SCANLIST_NAME: validate_zone(row[0]),
        CHAN_NAME: validate_name(row[1]),
        CHAN_BANDWIDTH: validate_bandwidth(row[2]),
        CHAN_POWER: validate_power(row[3]),
        CHAN_RX_FREQ: validate_freq(row[4]),
        CHAN_TX_FREQ: validate_freq(row[5]),
        CHAN_CTCSS_DEC: validate_ctcss(row[6]),
        CHAN_CTCSS_ENC: validate_ctcss(row[7]),
        CHAN_TX_PROHIBIT: validate_tx_prohibit(row[8]),
        CHAN_PTT_PROHIBIT: validate_tx_prohibit(row[8]),
        CHAN_MODE: VAL_ANALOG
    }
    if chan_config[CHAN_CTCSS_DEC] != "Off":
        chan_config[CHAN_SQUELCH_MODE] = VAL_CTCSS_DCS
    return chan_config

def process_dmr_others_file(csv_out, filename):
    headers = ["Zone", "Channel Name", "Power", "RX Freq", "TX Freq", "RX Color Code", "TX Color Code", "Talk Group", "TimeSlot", "Call Type", "TX Permit"]
    process_csv_file_with_header(csv_out, filename, "Digital-Others", headers, dmr_others_csv_field_extractor)

def dmr_others_csv_field_extractor(row):
    talkgroup = row[7]
    if talkgroup not in talkgroup_mapping:
        error(f"Talkgroup '{talkgroup}' is referenced in Digital-Others.csv but not defined in TalkGroups.csv {_file_and_line()}")
    rx_color_code = validate_color_code(row[5])
    tx_color_code = validate_color_code(row[6] if len(row) > 6 and row[6].strip() else row[5])  # Use RX Color Code if TX Color Code is empty
    chan_config = {
        CHAN_SCANLIST_NAME: validate_zone(row[0]),
        CHAN_NAME: validate_name(row[1]),
        CHAN_POWER: validate_power(row[2]),
        CHAN_RX_FREQ: validate_freq(row[3]),
        CHAN_TX_FREQ: validate_freq(row[4]),
        CHAN_RX_COLOR_CODE: rx_color_code,
        CHAN_TX_COLOR_CODE: tx_color_code,
        55: tx_color_code,  # Set TxCC directly at index 55
        CHAN_CONTACT: validate_contact(talkgroup),
        CHAN_TG_ID: talkgroup_mapping[talkgroup],
        CHAN_TIME_SLOT: validate_timeslot(row[8]),
        CHAN_CALL_TYPE_OLD: validate_call_type(row[9]),
        CHAN_TX_PERMIT: validate_tx_permit(row[10]),
        CHAN_MODE: VAL_DIGITAL
    }
    chan_config[CHAN_DMR_MODE] = dmr_mode(chan_config)
    return chan_config

def process_dmr_repeater_file(csv_out, filename):
    headers = ["Zone Name", "Comment", "Power", "RX Freq", "TX Freq", "Color Code"]
    process_csv_file_with_header(csv_out, filename, "Digital-Repeater", headers, dmr_repeater_csv_field_extractor, dmr_repeater_csv_matrix_extractor)

def dmr_repeater_csv_field_extractor(row):
    zone_full, zone_nick = handle_nickname_values(row[0])
    rx_color_code = validate_color_code(row[5])
    tx_color_code = validate_color_code(row[5])  # Use RX Color Code as TX Color Code
    chan_config = {
        CHAN_SCANLIST_NAME: validate_zone(zone_full),
        ACB_ZONE_NICKNAME: validate_zone(zone_nick),
        CHAN_POWER: validate_power(row[2]),
        CHAN_RX_FREQ: validate_freq(row[3]),
        CHAN_TX_FREQ: validate_freq(row[4]),
        CHAN_RX_COLOR_CODE: rx_color_code,
        CHAN_TX_COLOR_CODE: tx_color_code,
        55: tx_color_code,  # Set TxCC directly at index 55
        CHAN_MODE: VAL_DIGITAL
    }
    chan_config[CHAN_DMR_MODE] = dmr_mode(chan_config)
    return chan_config

def dmr_repeater_csv_matrix_extractor(chan_config, contact, value, headers, row, col):
    do_multiply = False
    timeslot, call_type = handle_repeater_value(value)
    timeslot = validate_timeslot(timeslot)
    if timeslot != VAL_NO_TIME_SLOT:
        contact, chan_nick = handle_nickname_values(contact)
        chan_name = make_channel_name(chan_config[ACB_ZONE_NICKNAME], contact, chan_nick)
        chan_config[CHAN_CONTACT] = validate_contact(contact)
        chan_config[CHAN_TG_ID] = talkgroup_mapping[contact]
        chan_config[CHAN_TIME_SLOT] = timeslot
        chan_config[CHAN_NAME] = validate_channel_name(chan_name)
        chan_config[CHAN_CALL_TYPE_OLD] = validate_call_type(call_type)
        do_multiply = True
    return do_multiply, chan_config

def read_channel_csv_default(filename):
    with open(filename, 'r', newline='', encoding='utf-8-sig') as fh:
        csv_reader = csv.reader(fh)
        for row in csv_reader:
            channel_csv_field_name[int(row[0])] = row[1]
            channel_csv_default_value[int(row[0])] = row[2]

def read_talkgroups(filename):
    global talkgroup_mapping, talkgroup_order, all_talkgroups
    index = 1
    with open(filename, 'r', newline='', encoding='utf-8-sig') as fh:
        csv_reader = csv.reader(fh)
        for row in csv_reader:
            all_talkgroups.append(row)  # Store every row, including header
            if index == 1:
                index += 1
                continue  # Skip header row for mapping
            if len(row) < 2:
                error(f"Invalid TalkGroups.csv format: each row must have at least two columns (Radio ID, Name) {_file_and_line()}")
            talkgroup_name = row[1].strip()
            talkgroup_id = row[0].strip()
            if not talkgroup_name or not talkgroup_id:
                error(f"Invalid TalkGroups.csv entry: Name or Radio ID is empty in row {index} {_file_and_line()}")
            talkgroup_mapping[talkgroup_name] = talkgroup_id
            talkgroup_order[talkgroup_name] = index
            index += 1

def process_csv_file_with_header(csv_out, filename, file_nickname, header_ref, field_extractor, matrix_field_extractor=None):
    global global_file_name, global_line_number
    global_file_name = file_nickname
    headers = []
    zone_order_index = 1
    with open(filename, 'r', newline='', encoding='utf-8-sig') as fh:
        csv_reader = csv.reader(fh)
        for line_no, row in enumerate(csv_reader, start=0):
            global_line_number = line_no
            if line_no == 0:
                for col, expected in enumerate(header_ref):
                    if col < len(row) and row[col] != expected:
                        error(f"CSV header does not match for {file_nickname} file (found '{row[col]}' expected '{expected}')")
                headers = row
            else:
                chan_config = field_extractor(row)
                zone_name = chan_config[CHAN_SCANLIST_NAME]
                # Tag zone type based on file source
                if file_nickname == "Analog":
                    zone_type[zone_name] = 'analog'
                elif file_nickname == "Digital-Others":
                    zone_type[zone_name] = 'digital_others'
                elif file_nickname == "Digital-Repeater":
                    zone_type[zone_name] = 'digital_repeaters'
                if len(row) == len(header_ref):
                    chan_config[CHAN_TX_PERMIT] = tx_permit(chan_config)
                    base_scanlist_name = chan_config[CHAN_SCANLIST_NAME]
                    actual_scanlist_name = get_overflow_scanlist_name(base_scanlist_name)
                    chan_config[CHAN_SCANLIST_NAME] = actual_scanlist_name
                    scanlist_channel_counts[actual_scanlist_name] += 1
                    add_channel(csv_out, chan_config, zone_name, actual_scanlist_name, zone_order_index)
                for col in range(len(header_ref), len(row)):
                    if not matrix_field_extractor:
                        error(f"There are too many columns in '{file_nickname}' file, line {line_no}.")
                    do_matrix, chan_config = matrix_field_extractor(chan_config, headers[col], row[col], headers, row, col)
                    if do_matrix:
                        base_scanlist_name = chan_config[CHAN_CONTACT]
                        actual_scanlist_name = get_overflow_scanlist_name(base_scanlist_name)
                        chan_config[CHAN_SCANLIST_NAME] = actual_scanlist_name
                        chan_config[CHAN_TX_PERMIT] = tx_permit(chan_config)
                        scanlist_channel_counts[actual_scanlist_name] += 1
                        add_channel(csv_out, chan_config, zone_name, actual_scanlist_name, zone_order_index)
                zone_order_index += 1

def get_overflow_scanlist_name(base_name):
    """Determine the appropriate scanlist name, creating overflow if necessary."""
    num = 1
    while True:
        if num == 1:
            name = base_name
        else:
            name = f"{base_name}_OF{num}"
        current_count = scanlist_channel_counts[name]
        if current_count < SCANLIST_LIMIT:
            return name
        num += 1
        if num > 1000:  # Safety limit to prevent infinite loop
            error(f"Infinite loop detected in scanlist overflow for '{base_name}'")

def add_channel(csv_out, chan_config, zone_name, scanlist_name, zone_order_index):
    global global_channel_number, analog_channel_index
    num_fields = max(channel_csv_default_value.keys()) + 1
    output = [''] * num_fields
    for index in range(num_fields):
        value = channel_csv_default_value.get(index, '')
        if index in chan_config:
            value = chan_config[index]
        if index == CHAN_NUM:
            value = global_channel_number
            global_channel_number += 1
        if value == "REQUIRED" and not chan_config.get(index):
            error(f"Missing required value for '{channel_csv_field_name.get(index, f'Field_{index}')}' in channel '{chan_config.get(CHAN_NAME, 'unknown')}'")
        output[index] = value
    csv_out.writerow(output)
    build_zone_config(chan_config, zone_name, zone_order_index)
    build_scanlist_config(chan_config, scanlist_name)
    if chan_config[CHAN_MODE] == VAL_DIGITAL:
        build_talkgroup_config(chan_config, zone_name)

def build_zone_config(chan_config, zone_name, zone_order_index):
    chan_name = chan_config[CHAN_NAME]
    rx_freq = chan_config[CHAN_RX_FREQ]
    tx_freq = chan_config[CHAN_TX_FREQ]
    zone_order[zone_name] = zone_order_index
    order = channel_order_name(chan_config)
    zone_config[zone_name].append(f"{order}\t{chan_name}\t{rx_freq}\t{tx_freq}")

def build_scanlist_config(chan_config, scanlist_name):
    chan_name = chan_config[CHAN_NAME]
    rx_freq = chan_config[CHAN_RX_FREQ]
    tx_freq = chan_config[CHAN_TX_FREQ]
    order = channel_order_name(chan_config)
    scanlist_config[scanlist_name].append(f"{order}\t{chan_name}\t{rx_freq}\t{tx_freq}")

def build_talkgroup_config(chan_config, zone_name):
    talkgroup = chan_config[CHAN_CONTACT]
    call_type = chan_config[CHAN_CALL_TYPE_OLD]
    if talkgroup not in talkgroup_mapping:
        error(f"Talkgroup '{talkgroup}' is referenced but not defined in the talkgroup input CSV file")
    if talkgroup in talkgroup_config and talkgroup_config[talkgroup] != call_type:
        other_call_type = talkgroup_config[talkgroup]
        chan_name = chan_config[CHAN_NAME]
        rx_freq = chan_config[CHAN_RX_FREQ]
        tx_freq = chan_config[CHAN_TX_FREQ]
        error(f"Talkgroup '{talkgroup}' was previously identified as a '{other_call_type}', but is now trying to be "
              f"used as a '{call_type}' on channel '{chan_name}' (Zone: '{zone_name}', RX: {rx_freq}, TX: {tx_freq}). "
              f"The Anytone CPS won't allow this to be imported. To fix this, create a second entry in your "
              f"talkgroups CSV input file for this talkgroup with a different name.")
    talkgroup_config[talkgroup] = call_type

def channel_order_name(chan_config):
    global analog_channel_index
    index1 = 9999
    index2 = 0
    chan_name = chan_config[CHAN_NAME]
    if global_sort_mode != 'alpha':
        if chan_config[CHAN_MODE] == VAL_DIGITAL:
            if chan_config[CHAN_CONTACT] in talkgroup_order:
                index1 = talkgroup_order[chan_config[CHAN_CONTACT]]
        elif chan_config[CHAN_MODE] == VAL_ANALOG:
            index2 = analog_channel_index
            analog_channel_index += 1
    return f"{index1:04d}{index2:04d}{chan_name}"

def tx_permit(chan_config):
    result = VAL_TX_PERMIT_SAME
    if global_hotspot_tx_permit == "always" and chan_config[CHAN_RX_FREQ] == chan_config[CHAN_TX_FREQ]:
        result = VAL_TX_PERMIT_ALWAYS
    elif CHAN_RX_COLOR_CODE in chan_config and CHAN_TX_COLOR_CODE in chan_config:
        if chan_config[CHAN_RX_COLOR_CODE] != chan_config[CHAN_TX_COLOR_CODE]:
            result = VAL_TX_PERMIT_DIFFERENT
    return result

def dmr_mode(chan_config):
    result = VAL_DMR_MODE_SIMPLEX
    if chan_config[CHAN_RX_FREQ] != chan_config[CHAN_TX_FREQ]:
        result = VAL_DMR_MODE_REPEATER
    return result

def handle_repeater_value(value):
    subvalues = value.split(';')
    timeslot = subvalues[0] if subvalues else ''
    call_type = VAL_CALL_TYPE_GROUP
    for v in subvalues[1:]:
        if v == 'P':
            call_type = VAL_CALL_TYPE_PRIVATE
    return timeslot, call_type

def handle_nickname_values(value):
    subvalues = value.split(';')
    full = subvalues[0] if subvalues else ''
    nick = subvalues[1] if len(subvalues) > 1 else ''
    return full, nick

def make_channel_name(zone_nick, chan_full, chan_nick):
    if global_nickname_mode == 'off' or not zone_nick:
        return chan_full
    if not chan_nick:
        chan_nick = chan_full
    if global_nickname_mode in ('prefix-forced', 'suffix-forced'):
        chan_full = chan_nick
    if len(zone_nick) + len(chan_full) + 1 <= LENGTH_CHAN_NAME:
        chan_name, sep = chan_full, ' '
    elif len(zone_nick) + len(chan_nick) + 1 <= LENGTH_CHAN_NAME:
        chan_name, sep = chan_nick, ' '
    elif len(zone_nick) + len(chan_nick) <= LENGTH_CHAN_NAME:
        chan_name, sep = chan_nick, ''
    else:
        error(f"Can't make a channel name fit into 16 characters for '{zone_nick}' and '{chan_nick}'")
    if not re.match(r'^[A-Za-z0-9]', zone_nick):
        sep = ''
    if global_nickname_mode in ('prefix', 'prefix-forced'):
        return f"{zone_nick}{sep}{chan_name}"
    return f"{chan_name}{sep}{zone_nick}"

# Data Validation Routines
def validate_bandwidth(mode):
    valid_modes = {"25K", "12.5K"}
    return _validate_membership(mode, valid_modes, "Analog Mode")

def validate_call_type(call_type):
    valid_call_types = {"Private Call", "Group Call"}
    return _validate_membership(call_type, valid_call_types, "Call Type")

def validate_channel_name(contact):
    return _validate_string_length("Channel Name", contact, LENGTH_CHAN_NAME)

def validate_color_code(color_code):
    return _validate_num_in_range("Color Code", color_code, 0, 15)

def validate_contact(contact):
    return _validate_string_length("Contact (aka Talk Group)", contact, LENGTH_CHAN_NAME)

def validate_ctcss(ctcss):
    if ctcss == 'Off':
        return ctcss
    if re.match(r'D[0-9A-Za-z]+', ctcss) and len(ctcss) < 10:
        return ctcss
    return _validate_num_in_range('CTCSS/DCS', ctcss, 0, 300)

def validate_freq(freq):
    return _validate_num_in_range('Frequency', freq, 0, 1000)

def validate_name(name):
    return _validate_string_length('Channel Name', name, LENGTH_CHAN_NAME)

def validate_power(power):
    valid_power_levels = {"Low", "Mid", "High", "Turbo"}
    return _validate_membership(power, valid_power_levels, "Power Level")

def validate_timeslot(timeslot):
    valid_timeslots = {"1", "2", "-"}
    return _validate_membership(timeslot, valid_timeslots, "Time Slot")

def validate_tx_prohibit(tx_prohibit):
    return _validate_on_off(tx_prohibit, "TX Prohibit")

def validate_zone(zone):
    return _validate_string_length('Zone', zone, 16)

def validate_sort_mode(sort_order):
    valid_sort_orders = {"alpha", "repeaters-first", "analog-first", "analog_and_others_first"}
    return _validate_membership(sort_order, valid_sort_orders, "Sort Order")

def validate_hotspot_mode(hotspot_mode):
    valid_modes = {"always", "same-color-code"}
    return _validate_membership(hotspot_mode, valid_modes, "Hotspot TX Permit")

def validate_nickname_mode(nickname_mode):
    valid_modes = {"off", "prefix", "suffix", "prefix-forced", "suffix-forced"}
    return _validate_membership(nickname_mode, valid_modes, "Nickname Mode")

def validate_talkgroup_sort(sort_mode):
    valid_modes = {"input", "id", "name"}
    return _validate_membership(sort_mode, valid_modes, "Talkgroup Sort")

# Validation Helpers
def _validate_membership(value, valid_set, error_type):
    if value not in valid_set:
        error_msg = f"Invalid {error_type}: '{value}' is not one of: {', '.join(valid_set)} {_file_and_line()}"
        error(error_msg)
    return value

def _validate_num_in_range(type_name, value, min_val, max_val):
    try:
        num = float(value)
        if num < min_val or num > max_val:
            error(f"Invalid {type_name}: '{value}' must be a number between {min_val} and {max_val} (inclusive) {_file_and_line()} ")
    except ValueError:
        error(f"Invalid {type_name}: '{value}' must be a number between {min_val} and {max_val} (inclusive) {_file_and_line()}")
    return value

def _validate_on_off(value, error_type):
    valid_on_off = {"On", "Off"}
    return _validate_membership(value, valid_on_off, error_type)

def _validate_string_length(type_name, string, length):
    if len(string) > length:
        error(f"Invalid {type_name}: '{string}' is more than {length} characters {_file_and_line()}")
    return string

def _file_and_line():
    return f"[On line {global_line_number} of {global_file_name} file.]"

def validate_tx_permit(tx_permit):
    valid_tx_permits = {"Always", "ChannelFree", "Same Color Code", "Different Color Code"}
    return _validate_membership(tx_permit, valid_tx_permits, "TX Permit")

def error(message):
    print(f"ERROR: {message}")
    sys.exit(1)

def warning(message):
    print(f"WARNING: {message}")

def handle_command_line_args():
    parser = argparse.ArgumentParser(
        description="Anytone Config Builder\n\n"
                    "This script generates CSV files for Anytone CPS from input CSV files.\n"
                    "Use --generate-templates to create example CSV files with headers.",
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument(
        '--analog-csv',
        required=False,
        help='Path to Analog.csv (analog channels). Required unless --generate-templates is used.'
    )
    parser.add_argument(
        '--digital-others-csv',
        required=False,
        help='Path to Digital-Others.csv (DMR simplex, hotspots). Required unless --generate-templates is used.'
    )
    parser.add_argument(
        '--digital-repeaters-csv',
        required=False,
        help='Path to Digital-Repeaters.csv (DMR repeaters). Required unless --generate-templates is used.'
    )
    parser.add_argument(
        '--talkgroups-csv',
        required=False,
        help='Path to TalkGroups.csv (talkgroup names and IDs). Required unless --generate-templates is used.'
    )
    parser.add_argument(
        '--output-directory',
        required=False,
        default='./Output',
        help='Directory for output CSV files. Defaults to ./Output if not provided.\n'
             'Example: --output-directory ./my_output'
    )
    parser.add_argument(
        '--config',
        default='config',
        help='Directory containing channel-defaults.csv. Defaults to "config".'
    )
    parser.add_argument(
        '--sorting',
        default='alpha',
        choices=['alpha', 'repeaters-first', 'analog-first', 'analog_and_others_first'],
        help='Zone sorting mode:\n'
             '  alpha: Sort all zones alphabetically.\n'
             '  repeaters-first: Place digital repeater zones first, then others, each sorted alphabetically.\n'
             '  analog-first: Place analog zones first, then others, each sorted alphabetically.\n'
             '  analog_and_others_first: Place analog and digital-others zones first, sorted alphabetically,\n'
             '                           followed by digital-repeater zones, sorted alphabetically.\n'
             'Default: alpha'
    )
    parser.add_argument(
        '--hotspot-tx-permit',
        default='same-color-code',
        choices=['always', 'same-color-code'],
        help='TX Permit for hotspots. Default: same-color-code'
    )
    parser.add_argument(
        '--nicknames',
        default='off',
        choices=['off', 'prefix', 'suffix', 'prefix-forced', 'suffix-forced'],
        help='Nickname mode for channel names. Default: off'
    )
    parser.add_argument(
        '--talkgroup-sort',
        default='input',
        choices=['input', 'id', 'name'],
        help='Talkgroup sorting mode:\n'
             '  input: Keep the order from the input file.\n'
             '  id: Sort by TGID (Radio ID) numerically.\n'
             '  name: Sort by Talkgroup Name alphabetically (case-insensitive).\n'
             'Default: input'
    )
    parser.add_argument(
        '--generate-templates',
        action='store_true',
        help='Generate empty CSV templates with headers in ./Templates and exit.\n'
             'Use this to get started with the correct file formats.'
    )
    parser.add_argument(
        '--dmr-id',
        required=False,
        help='Adding your DMR ID will also add the radio_id_list csv file.\n'
             'This will utilize the standard naming convention to match the\n'
             'channels for your DMR ID.'
    )

    args = parser.parse_args()

    if not args.generate_templates:
        if not all([args.analog_csv, args.digital_others_csv, args.digital_repeaters_csv, args.talkgroups_csv]):
            parser.error("All input CSV files (--analog-csv, --digital-others-csv, --digital-repeaters-csv, --talkgroups-csv) "
                         "are required unless --generate-templates is used.")

    global global_sort_mode, global_hotspot_tx_permit, global_nickname_mode, global_talkgroup_sort
    global_sort_mode = validate_sort_mode(args.sorting)
    global_hotspot_tx_permit = validate_hotspot_mode(args.hotspot_tx_permit)
    global_nickname_mode = validate_nickname_mode(args.nicknames)
    global_talkgroup_sort = validate_talkgroup_sort(args.talkgroup_sort)
    return args

def generate_templates(templates_dir):
    os.makedirs(templates_dir, exist_ok=True)

    # Analog template
    with open(os.path.join(templates_dir, 'Analog_template.csv'), 'w', newline='', encoding='utf-8') as fh:
        csv_out = csv.writer(fh)
        csv_out.writerow(["Zone", "Channel Name", "Bandwidth", "Power", "RX Freq", "TX Freq", "CTCSS Decode", "CTCSS Encode", "TX Prohibit"])
        csv_out.writerow(["NOAA","NOAA1","25K","High","162.4","440","Off","Off","On"])
        csv_out.writerow(["NOAA","NOAA2","25K","High","162.425","440","Off","Off","On"])
        csv_out.writerow(["NOAA","NOAA3","25K","High","162.45","440","Off","Off","On"])
        csv_out.writerow(["NOAA","NOAA4","25K","High","162.475","440","Off","Off","On"])
        csv_out.writerow(["NOAA","NOAA5","25K","High","162.5","440","Off","Off","On"])
        csv_out.writerow(["NOAA","NOAA6","25K","High","162.525","440","Off","Off","On"])
        csv_out.writerow(["NOAA","NOAA7","25K","High","162.55","440","Off","Off","On"])
        csv_out.writerow(["Calling","Calling 2m","25K","High","144.2","144.2","Off","Off","Off"])
        csv_out.writerow(["Calling","Simplex 2m Call","25K","Low","146.52","146.52","Off","Off","Off"])
        csv_out.writerow(["Calling","70CM Calling","25K","High","432.1","432.1","Off","Off","Off"])
        csv_out.writerow(["Calling","70CM Calling1","25K","High","446","446","Off","Off","Off"])

    # Digital-Others template
    with open(os.path.join(templates_dir, 'Digital-Others_template.csv'), 'w', newline='', encoding='utf-8') as fh:
        csv_out = csv.writer(fh)
        csv_out.writerow(["Zone", "Channel Name", "Power", "RX Freq", "TX Freq", "RX Color Code", "TX Color Code", "Talk Group", "TimeSlot", "Call Type", "TX Permit"])
        csv_out.writerow(["PiStar","PiBM/Bridge 2","Low","440.35","445.35","1","1","Bridge 2","1","Group Call","Same Color Code"])
        csv_out.writerow(["PiStar","PiBM/DMRAnarchy","Low","440.35","445.35","1","1","DMR Anarchy","2","Group Call","Same Color Code"])
        csv_out.writerow(["PiStar","PiBM/Parrot","Low","440.35","445.35","1","1","Parrot","1","Private Call","Same Color Code"])

    # Digital-Repeaters template
    with open(os.path.join(templates_dir, 'Digital-Repeaters_template.csv'), 'w', newline='', encoding='utf-8') as fh:
        csv_out = csv.writer(fh)
        headers = ["Zone Name", "Comment", "Power", "RX Freq", "TX Freq", "Color Code"]
        headers += ["DMR Anarchy", "Bridge 2", "N America"]
        csv_out.writerow(headers)
        csv_out.writerow(["Salem/MT;SMT", "", "High", "435.875", "440.875", "3", "1", "1", "2"])
        csv_out.writerow(["Oakland/Cherry;OAC", "", "High", "434.500", "439.500", "7", "2", "-", "-"])
        csv_out.writerow(["Oakland/Valley;OAV", "", "High", "436.500", "441.500", "1", "2", "2", "2"])

    # TalkGroups template
    with open(os.path.join(templates_dir, 'TalkGroups_template.csv'), 'w', newline='', encoding='utf-8') as fh:
        csv_out = csv.writer(fh)
        csv_out.writerow(["Radio ID", "Name", "Call Type", "Call Alert"])
        csv_out.writerow(["9990", "Parrot", "Private Call", "None"])
        csv_out.writerow(["3100", "Bridge 2", "Group Call", "None"])
        csv_out.writerow(["93", "N America", "Group Call", "None"])
        csv_out.writerow(["31666", "DMR Anarchy", "Group Call", "None"])

if __name__ == '__main__':
    main()
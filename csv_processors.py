# csv_processors.py
import csv
from validators import *
from helpers import *
from utils import error

def read_talkgroups(filename, data, ctx):
    index = 1
    with open(filename, 'r', newline='', encoding='utf-8-sig') as fh:
        csv_reader = csv.reader(fh)
        for line_no, row in enumerate(csv_reader, start=1):
            ctx.set_file_line('TalkGroups', line_no)
            data.all_talkgroups.append(row)
            if index == 1:
                index += 1
                continue
            if len(row) < 2:
                error(f"Invalid TalkGroups.csv format: each row must have at least two columns (Radio ID, Name) {ctx.location_str()}")
            talkgroup_id = row[0].strip()
            talkgroup_name = row[1].strip()
            if not talkgroup_name or not talkgroup_id:
                error(f"Invalid TalkGroups.csv entry: Name or Radio ID is empty {ctx.location_str()}")
            data.talkgroup_mapping[talkgroup_name] = talkgroup_id
            data.talkgroup_order[talkgroup_name] = index
            index += 1

def process_csv_file_with_header(csv_out, filename, file_nickname, header_ref, field_extractor, config, data, ctx, sort_mode, hotspot_tx_permit, nickname_mode, matrix_field_extractor=None):
    headers = []
    zone_order_index = 1
    with open(filename, 'r', newline='', encoding='utf-8-sig') as fh:
        csv_reader = csv.reader(fh)
        for line_no, row in enumerate(csv_reader, start=1):
            ctx.set_file_line(file_nickname, line_no)
            if line_no == 1:
                for col in range(len(header_ref)):
                    if col < len(row) and row[col] != header_ref[col]:
                        error(f"CSV header does not match expected for {file_nickname} file (found '{row[col]}' expected '{header_ref[col]}') {ctx.location_str()}")
                headers = row
                continue
            chan_config = field_extractor(config, row, data, ctx, file_nickname)
            zone_name = chan_config[config.CHAN_SCANLIST_NAME]
            data.zone_type[zone_name] = file_nickname.lower().replace('-', '_')
            if len(row) == len(header_ref):
                chan_config[config.CHAN_TX_PERMIT] = tx_permit(config, hotspot_tx_permit, chan_config)
                base_scanlist_name = chan_config[config.CHAN_SCANLIST_NAME]
                actual_scanlist_name = get_overflow_scanlist_name(config, data.scanlist_channel_counts, base_scanlist_name, config.SCANLIST_LIMIT)
                chan_config[config.CHAN_SCANLIST_NAME] = actual_scanlist_name
                data.scanlist_channel_counts[actual_scanlist_name] += 1
                add_channel(csv_out, config, data, ctx, chan_config, zone_name, actual_scanlist_name, zone_order_index, sort_mode)
            for col in range(len(header_ref), len(row)):
                if not matrix_field_extractor:
                    error(f"There are too many columns in '{file_nickname}' file {ctx.location_str()}.")
                do_multiply, chan_config = matrix_field_extractor(config, chan_config, headers[col], row[col], headers, row, col, data, ctx, nickname_mode)
                if do_multiply:
                    actual_scanlist_name = get_overflow_scanlist_name(config, data.scanlist_channel_counts, chan_config[config.CHAN_CONTACT], config.SCANLIST_LIMIT)
                    chan_config[config.CHAN_SCANLIST_NAME] = actual_scanlist_name
                    chan_config[config.CHAN_TX_PERMIT] = tx_permit(config, hotspot_tx_permit, chan_config)
                    data.scanlist_channel_counts[actual_scanlist_name] += 1
                    add_channel(csv_out, config, data, ctx, chan_config, zone_name, actual_scanlist_name, zone_order_index, sort_mode)
            zone_order_index += 1

def analog_csv_field_extractor(config, row, data, ctx, file_nickname):
    location_str = ctx.location_str()
    chan_config = {
        config.CHAN_SCANLIST_NAME: validate_zone(config, row[0], location_str),
        config.CHAN_NAME: validate_name(config, row[1], location_str),
        config.CHAN_BANDWIDTH: validate_bandwidth(config, row[2], location_str),
        config.CHAN_POWER: validate_power(config, row[3], location_str),
        config.CHAN_RX_FREQ: validate_freq(config, row[4], location_str),
        config.CHAN_TX_FREQ: validate_freq(config, row[5], location_str),
        config.CHAN_CTCSS_DEC: validate_ctcss(config, row[6], location_str),
        config.CHAN_CTCSS_ENC: validate_ctcss(config, row[7], location_str),
        config.CHAN_PTT_PROHIBIT: validate_tx_prohibit(config, row[8] if len(row) > 8 else 'Off', location_str),
        config.CHAN_MODE: config.VAL_ANALOG
    }
    if chan_config[config.CHAN_CTCSS_DEC] != "Off":
        chan_config[config.CHAN_SQUELCH_MODE] = config.VAL_CTCSS_DCS
    return chan_config

def dmr_others_csv_field_extractor(config, row, data, ctx, file_nickname):
    location_str = ctx.location_str()
    talkgroup = row[7]
    if talkgroup not in data.talkgroup_mapping:
        error(f"Talkgroup '{talkgroup}' is referenced in Digital-Others.csv but not defined in TalkGroups.csv {location_str}")
    rx_color_code = validate_color_code(config, row[5], location_str)
    tx_color_code = validate_color_code(config, row[6] if len(row) > 6 and row[6].strip() else row[5], location_str)
    if config.IS_OLD_FW and rx_color_code != tx_color_code:
        error(f"Different RX and TX color codes not supported in older firmware versions {location_str}")
    chan_config = {
        config.CHAN_SCANLIST_NAME: validate_zone(config, row[0], location_str),
        config.CHAN_NAME: validate_name(config, row[1], location_str),
        config.CHAN_POWER: validate_power(config, row[2], location_str),
        config.CHAN_RX_FREQ: validate_freq(config, row[3], location_str),
        config.CHAN_TX_FREQ: validate_freq(config, row[4], location_str),
        config.CHAN_RX_COLOR_CODE: rx_color_code,
        config.CHAN_CONTACT: validate_contact(config, talkgroup, location_str),
        config.CHAN_TG_ID: data.talkgroup_mapping[talkgroup],
        config.CHAN_TIME_SLOT: validate_timeslot(config, row[8] if len(row) > 8 else config.VAL_NO_TIME_SLOT, location_str),
        config.CHAN_CALL_TYPE_OLD: validate_call_type(config, row[9] if len(row) > 9 else config.VAL_CALL_TYPE_GROUP, location_str),
        config.CHAN_TX_PERMIT: validate_tx_permit(config, row[10] if len(row) > 10 else config.VAL_TX_PERMIT_SAME, location_str),
        config.CHAN_MODE: config.VAL_DIGITAL
    }
    if config.CHAN_TX_COLOR_CODE is not None:
        chan_config[config.CHAN_TX_COLOR_CODE] = tx_color_code
    if config.CHAN_DMR_MODE is not None:
        chan_config[config.CHAN_DMR_MODE] = dmr_mode(config, chan_config)
    return chan_config

def dmr_repeater_csv_field_extractor(config, row, data, ctx, file_nickname):
    location_str = ctx.location_str()
    zone_full, zone_nick = handle_nickname_values(row[0])
    rx_color_code = validate_color_code(config, row[5], location_str)
    tx_color_code = rx_color_code
    chan_config = {
        config.CHAN_SCANLIST_NAME: validate_zone(config, zone_full, location_str),
        'ACB_ZONE_NICKNAME': validate_zone(config, zone_nick, location_str),
        config.CHAN_POWER: validate_power(config, row[2], location_str),
        config.CHAN_RX_FREQ: validate_freq(config, row[3], location_str),
        config.CHAN_TX_FREQ: validate_freq(config, row[4], location_str),
        config.CHAN_RX_COLOR_CODE: rx_color_code,
        config.CHAN_MODE: config.VAL_DIGITAL
    }
    if config.CHAN_TX_COLOR_CODE is not None:
        chan_config[config.CHAN_TX_COLOR_CODE] = tx_color_code
    if config.CHAN_DMR_MODE is not None:
        chan_config[config.CHAN_DMR_MODE] = dmr_mode(config, chan_config)
    return chan_config

def dmr_repeater_csv_matrix_extractor(config, chan_config, contact, value, headers, row, col, data, ctx, nickname_mode):
    do_multiply = False
    timeslot, call_type = handle_repeater_value(value)
    timeslot = validate_timeslot(config, timeslot, ctx.location_str())
    if timeslot != config.VAL_NO_TIME_SLOT:
        contact_full, chan_nick = handle_nickname_values(contact)
        chan_name = make_channel_name(config, nickname_mode, chan_config['ACB_ZONE_NICKNAME'], contact_full, chan_nick)
        chan_config[config.CHAN_CONTACT] = validate_contact(config, contact_full, ctx.location_str())
        if contact_full not in data.talkgroup_mapping:
            error(f"Talkgroup '{contact_full}' is referenced but not defined in TalkGroups.csv {ctx.location_str()}")
        chan_config[config.CHAN_TG_ID] = data.talkgroup_mapping[contact_full]
        chan_config[config.CHAN_TIME_SLOT] = timeslot
        chan_config[config.CHAN_NAME] = validate_channel_name(config, chan_name, ctx.location_str())
        chan_config[config.CHAN_CALL_TYPE_OLD] = validate_call_type(config, call_type, ctx.location_str())
        do_multiply = True
    return do_multiply, chan_config

def add_channel(csv_out, config, data, ctx, chan_config, zone_name, scanlist_name, zone_order_index, sort_mode):
    num_fields = max(config.channel_csv_field_name.keys()) + 1
    output = [''] * num_fields
    for index in range(num_fields):
        value = config.channel_csv_default_value.get(index, '')
        if index in chan_config:
            value = chan_config[index]
        if index == config.CHAN_NUM:
            value = data.channel_number
            data.channel_number += 1
        if value == "REQUIRED" and index not in chan_config:
            error(f"Missing required value for '{config.channel_csv_field_name.get(index, f'Field_{index}')}' in channel '{chan_config.get(config.CHAN_NAME, 'unknown')}' {ctx.location_str()}")
        output[index] = value
    csv_out.writerow(output)
    build_zone_config(config, data, chan_config, zone_name, zone_order_index, sort_mode)
    build_scanlist_config(config, data, chan_config, scanlist_name)
    if chan_config[config.CHAN_MODE] == config.VAL_DIGITAL:
        build_talkgroup_config(config, data, chan_config, zone_name, ctx)
    if chan_config[config.CHAN_MODE] == config.VAL_ANALOG:
        data.analog_channel_index += 1

def build_zone_config(config, data, chan_config, zone_name, zone_order_index, sort_mode):
    chan_name = chan_config[config.CHAN_NAME]
    rx_freq = chan_config[config.CHAN_RX_FREQ]
    tx_freq = chan_config[config.CHAN_TX_FREQ]
    data.zone_order[zone_name] = min(data.zone_order.get(zone_name, 9999), zone_order_index)
    order = channel_order_name(config, data, chan_config, sort_mode)
    data.zone_config[zone_name].append(f"{order}\t{chan_name}\t{rx_freq}\t{tx_freq}")

def build_scanlist_config(config, data, chan_config, scanlist_name):
    chan_name = chan_config[config.CHAN_NAME]
    rx_freq = chan_config[config.CHAN_RX_FREQ]
    tx_freq = chan_config[config.CHAN_TX_FREQ]
    order = chan_name.lower()  # For scanlists, sort alpha
    data.scanlist_config[scanlist_name].append(f"{order}\t{chan_name}\t{rx_freq}\t{tx_freq}")

def build_talkgroup_config(config, data, chan_config, zone_name, ctx):
    talkgroup = chan_config[config.CHAN_CONTACT]
    call_type = chan_config[config.CHAN_CALL_TYPE_OLD]
    if talkgroup not in data.talkgroup_mapping:
        error(f"Talkgroup '{talkgroup}' is referenced but not defined in the talkgroup input CSV file {ctx.location_str()}")
    if talkgroup in data.talkgroup_config and data.talkgroup_config[talkgroup] != call_type:
        other_call_type = data.talkgroup_config[talkgroup]
        chan_name = chan_config[config.CHAN_NAME]
        rx_freq = chan_config[config.CHAN_RX_FREQ]
        tx_freq = chan_config[config.CHAN_TX_FREQ]
        error(f"Talkgroup '{talkgroup}' was previously identified as a '{other_call_type}', but is now trying to be used as a '{call_type}' on channel '{chan_name}' (Zone: '{zone_name}', RX: {rx_freq}, TX: {tx_freq}). The Anytone CPS won't allow this to be imported. To fix this, create a second entry in your talkgroups CSV input file for this talkgroup with a different name.")
    data.talkgroup_config[talkgroup] = call_type
# csv_writers.py
import csv
import os
from helpers import generic_row_builder, _zone_row_details, _scanlist_row_details, zone_sort_key
from utils import error

def print_channel_header(csv_out, config):
    output = [config.channel_csv_field_name[index] for index in sorted(config.channel_csv_field_name.keys())]
    csv_out.writerow(output)

def write_zone_file(filename, config, data, sort_mode):
    headers = ["No.", "Zone Name", "Zone Channel Member", "Zone Channel Member RX Frequency", "Zone Channel Member TX Frequency",
               "A Channel", "A Channel RX Frequency", "A Channel TX Frequency",
               "B Channel", "B Channel RX Frequency", "B Channel TX Frequency"]
    generate_csv_file(filename, headers, data.zone_config, lambda rn, n, rr: generic_row_builder(rn, n, rr, _zone_row_details, config.ZONE_CHANNEL_LIMIT, "Zone", config.LIST_SEPARATOR), zone_sort_key(sort_mode, data.zone_type))

def write_scanlist_file(filename, config, data):
    headers = ["No.", "Scan List Name", "Scan Channel Member", "Scan Channel Member RX Frequency", "Scan Channel Member TX Frequency",
               "Scan Mode", "Priority Channel Select", "Priority Channel 1", "Priority Channel 1 RX Frequency",
               "Priority Channel 1 TX Frequency", "Priority Channel 2", "Priority Channel 2 RX Frequency",
               "Priority Channel 2 TX Frequency", "Revert Channel", "Look Back Time A[s]", "Look Back Time B[s]",
               "Dropout Delay Time[s]", "Dwell Time[s]"]
    generate_csv_file(filename, headers, data.scanlist_config, lambda rn, n, rr: generic_row_builder(rn, n, rr, _scanlist_row_details, config.SCANLIST_LIMIT, "Scanlist", config.LIST_SEPARATOR), str.lower)

def write_talkgroup_file(filename, data, talkgroup_sort):
    headers = ["No.", "Radio ID", "Name", "Country", "Remarks", "Call Type", "Call Alert"]
    with open(filename, 'w', newline='', encoding='utf-8') as fh:
        csv_out = csv.writer(fh, quoting=csv.QUOTE_ALL, lineterminator='\r\n')
        csv_out.writerow(headers)
        talkgroups = []
        for row in data.all_talkgroups[1:]:
            radio_id = row[0].strip()
            name = row[1].strip()
            call_type = row[2].strip() if len(row) > 2 and row[2].strip() else "Group Call"
            call_alert = row[3].strip() if len(row) > 3 and row[3].strip() else "None"
            talkgroups.append((radio_id, name, call_type, call_alert))
        if talkgroup_sort == 'id':
            talkgroups.sort(key=lambda x: int(x[0]))
        elif talkgroup_sort == 'name':
            talkgroups.sort(key=lambda x: x[1].lower())
        row_num = 1
        for tg in talkgroups:
            csv_out.writerow([row_num, tg[0], tg[1], "", "", tg[2], tg[3]])
            row_num += 1

def write_radio_id_list(dmr_id, output_dir, config):
    if not dmr_id:
        return
    headers = ["No.", "Radio ID", "Name"]
    filename = os.path.join(output_dir, 'radio_id_list.csv')
    with open(filename, 'w', newline='', encoding='utf-8') as fh:
        csv_out = csv.writer(fh, quoting=csv.QUOTE_ALL, lineterminator='\r\n')
        csv_out.writerow(headers)
        try:
            dmr_id_num = int(dmr_id)
            if dmr_id_num <= 0:
                raise ValueError
        except ValueError:
            error(f"Invalid DMR ID: '{dmr_id}' must be a positive integer")
        dmr_name = 'DMR ID'
        if len(dmr_name) > config.LENGTH_CHAN_NAME:
            error(f"Invalid DMR ID name: '{dmr_name}' is more than {config.LENGTH_CHAN_NAME} characters")
        csv_out.writerow([1, dmr_id, dmr_name])

def generate_csv_file(filename, headers, data_dict, row_func, sort_key_func):
    with open(filename, 'w', newline='', encoding='utf-8') as fh:
        csv_out = csv.writer(fh, quoting=csv.QUOTE_ALL, lineterminator='\r\n')
        csv_out.writerow(headers)
        row_num = 1
        for key in sorted(data_dict.keys(), key=sort_key_func):
            row = row_func(row_num, key, data_dict[key])
            csv_out.writerow(row)
            row_num += 1
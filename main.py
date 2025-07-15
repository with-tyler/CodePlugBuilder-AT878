# main.py
#!/usr/bin/env python3

import argparse
import os
import csv
from config import Config
from data_structures import Data
from processing_context import ProcessingContext
from validators import *
from csv_processors import *
from csv_writers import *
from template_generator import generate_templates
from utils import error

ACB_ZONE_NICKNAME = 1000  # Custom index

def main():
    args = handle_command_line_args()
    if args.generate_templates:
        templates_dir = './Templates'
        generate_templates(templates_dir)
        print(f"Templates generated in: {os.path.abspath(templates_dir)}")
        return

    radio_config_filename = args.radio_config or os.path.join(args.config, 'radio.yml')
    config = Config(radio_config_filename, args.radio_id)

    if args.verify_defaults:
        print(f"Radio configuration file: {os.path.abspath(radio_config_filename)}")
        print("Channel defaults:")
        for key, value in config.channel_defaults.items():
            print(f"  {key}: {value}")
        print(f"Radio configuration file '{radio_config_filename}' is valid.")
        return

    output_dir = args.output_directory or './Output'
    os.makedirs(output_dir, exist_ok=True)

    sort_mode = validate_sort_mode(args.sorting)
    hotspot_tx_permit = validate_hotspot_mode(args.hotspot_tx_permit)
    nickname_mode = validate_nickname_mode(args.nicknames)
    talkgroup_sort = validate_talkgroup_sort(args.talkgroup_sort)

    data = Data()
    ctx = ProcessingContext()

    analog_filename = args.analog_csv
    digital_others_filename = args.digital_others_csv
    digital_repeaters_filename = args.digital_repeaters_csv
    talkgroups_filename = args.talkgroups_csv

    read_talkgroups(talkgroups_filename, data, ctx)

    with open(os.path.join(output_dir, 'channels.csv'), 'w', newline='', encoding='utf-8') as fh:
        csv_out = csv.writer(fh, quoting=csv.QUOTE_ALL, lineterminator='\r\n')
        print_channel_header(csv_out, config)

        process_csv_file_with_header(csv_out, digital_others_filename, "Digital-Others", 
                                     ["Zone", "Channel Name", "Power", "RX Freq", "TX Freq", "RX Color Code", "TX Color Code", "Talk Group", "TimeSlot", "Call Type", "TX Permit"],
                                     dmr_others_csv_field_extractor, config, data, ctx, sort_mode, hotspot_tx_permit, nickname_mode)

        process_csv_file_with_header(csv_out, digital_repeaters_filename, "Digital-Repeaters", 
                                     ["Zone Name", "Comment", "Power", "RX Freq", "TX Freq", "Color Code"],
                                     dmr_repeater_csv_field_extractor, config, data, ctx, sort_mode, hotspot_tx_permit, nickname_mode,
                                     dmr_repeater_csv_matrix_extractor)

        process_csv_file_with_header(csv_out, analog_filename, "Analog", 
                                     ["Zone", "Channel Name", "Bandwidth", "Power", "RX Freq", "TX Freq", "CTCSS Decode", "CTCSS Encode", "TX Prohibit"],
                                     analog_csv_field_extractor, config, data, ctx, sort_mode, hotspot_tx_permit, nickname_mode)

    write_zone_file(os.path.join(output_dir, 'zones.csv'), config, data, sort_mode)
    write_scanlist_file(os.path.join(output_dir, 'scanlists.csv'), config, data)
    write_talkgroup_file(os.path.join(output_dir, 'talkgroups.csv'), data, talkgroup_sort)
    write_radio_id_list(args.dmr_id, output_dir, config)

    print(f"Output files generated in: {os.path.abspath(output_dir)}")
    print("Summary:")
    print(f"Generated {data.channel_number - 1} channels")
    print(f"{len(data.zone_config)} zones")
    print(f"{len(data.scanlist_config)} scanlists")
    print(f"{len(data.all_talkgroups) - 1} talkgroups")

def handle_command_line_args():
    parser = argparse.ArgumentParser(
        description="Anytone Config Builder\n\n"
                    "This script generates CSV files for Anytone CPS from input CSV files.\n"
                    "Use --generate-templates to create example CSV files with headers.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument('--analog-csv', required=False, help='Path to Analog.csv (analog channels). Required unless --generate-templates is used.')
    parser.add_argument('--digital-others-csv', required=False, help='Path to Digital-Others.csv (DMR simplex, hotspots). Required unless --generate-templates is used.')
    parser.add_argument('--digital-repeaters-csv', required=False, help='Path to Digital-Repeaters.csv (DMR repeaters). Required unless --generate-templates is used.')
    parser.add_argument('--talkgroups-csv', required=False, help='Path to TalkGroups.csv (talkgroup names and IDs). Required unless --generate-templates is used.')
    parser.add_argument('--output-directory', required=False, default='./Output', help='Directory for output CSV files. Defaults to ./Output.')
    parser.add_argument('--config', default='config', help='Directory containing radio.yml. Defaults to "config".')
    parser.add_argument('--radio-config', required=False, help='Path to radio configuration YAML file. Defaults to config/radio.yml.')
    parser.add_argument('--radio-id', type=int, default=1, help='Radio ID to select configuration for. Default: 1')
    parser.add_argument('--verify-defaults', action='store_true', help='Verify the radio configuration file and exit.')
    parser.add_argument('--sorting', default='alpha', choices=['alpha', 'repeaters-first', 'analog-first', 'analog_and_others_first'], help='Zone sorting mode. Default: alpha')
    parser.add_argument('--hotspot-tx-permit', default='same-color-code', choices=['always', 'same-color-code'], help='TX Permit for hotspots. Default: same-color-code')
    parser.add_argument('--nicknames', default='off', choices=['off', 'prefix', 'suffix', 'prefix-forced', 'suffix-forced'], help='Nickname mode for channel names. Default: off')
    parser.add_argument('--talkgroup-sort', default='input', choices=['input', 'id', 'name'], help='Talkgroup sorting mode. Default: input')
    parser.add_argument('--generate-templates', action='store_true', help='Generate empty CSV templates with headers in ./Templates and exit.')
    parser.add_argument('--dmr-id', required=False, help='Your DMR ID to generate radio_id_list.csv.')
    args = parser.parse_args()
    if not args.generate_templates and not args.verify_defaults:
        if not all([args.analog_csv, args.digital_others_csv, args.digital_repeaters_csv, args.talkgroups_csv]):
            parser.error("All input CSV files are required unless --generate-templates or --verify-defaults is used.")
    return args

if __name__ == '__main__':
    main()
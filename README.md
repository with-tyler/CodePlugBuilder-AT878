# Anytone Config Builder

This is a simple Python program designed to help ham radio enthusiasts create configuration files (in CSV format) for Anytone radios. These files can be imported into the Anytone CPS (CodePlug Software) to set up channels, zones, talkgroups, and other settings on your radio.

The program takes your custom settings from easy-to-edit CSV template files (like spreadsheets) and turns them into the exact CSV files needed by the Anytone CPS. It's especially useful for setting up analog channels (like traditional FM radio frequencies) and digital channels (DMR mode for things like repeaters and hotspots).

If you're not very technical, don't worry! You can edit the template files using a spreadsheet program like Microsoft Excel, Google Sheets, or LibreOffice Calc. Just fill in the columns as described below, save them as CSV files, and run the program.

## Prerequisites

- **Python 3**: You need Python 3 installed on your computer. Download it from [python.org](https://www.python.org/downloads/) if you don't have it. (The program uses Python 3.13, but any Python 3 version should work.)
- **The only additional packge**: The program uses built-in Python features and the packages found in `requirements.txt`.
- **A text editor or spreadsheet app**: For editing the CSV templates.
- **CPS Version**: Currently based on CPS Version 3.06 (default, `radio-id: 1`), see `config/radio.yml`, and above channel creation.
  - Some tweaks to the channel output may be necessary for import into older CPS versions.
  - Better yet, create a new radio in `radio.yml` or edit the current ones.

## How to Run the Program

1. Download or copy all the Python files (`main.py`, `utils.py`, `config.py`, `validators.py`, `data_structures.py`, `processing_context.py`, `helpers.py`, `csv_processors.py`, `csv_writers.py`, `template_generator.py`) and the `config` folder (which contains `radio.yml`) to a folder on your computer.
2. Open a command prompt or terminal:
   - **On Windows**: Search for "cmd" and open Command Prompt. Navigate to your folder using `cd path\to\your\folder`.
   - **On macOS/Linux**: Open Terminal and use `cd` to go to the folder.
   - **Install Requirements**: `pip install -r requirements.txt`
     - This is only required the first time running the program.
3. Run the program with Python: Type `python main.py` (or `python3 main.py` on some systems) followed by options (explained below).

The program will process your input files and create output CSVs in a folder (default: `./Output`).

## Generating Template Files

Before creating your config, generate blank template files with example data. These are starter CSV files you can edit.

Run this command:

```bash
python main.py --generate-templates
````

or

```bash
python3 main.py --generate-templates
```

This creates a `./Templates` folder with four files:

- `Analog_template.csv`: For analog (non-digital) channels like weather radios or simplex calling frequencies.
- `Digital-Others_template.csv`: For digital DMR simplex channels or hotspots (like Pi-Star setups).
- `Digital-Repeaters_template.csv`: For digital DMR repeaters (stations that boost your signal over a wider area).
- `TalkGroups_template.csv`: A list of talkgroups (like group chat IDs in DMR digital mode).

These templates include headers (column names) and a few example rows. Open them in a spreadsheet app, edit the rows, add new ones as needed, and save (make sure to save as CSV format).

>[!TIP]
>Don't change the header row (first line). Add or edit rows below it. If a cell is empty, the program might use a default value or give an error if it's required.

## Using the Template Files

Each template is a CSV file that looks like a table. Here's what each one is for, what columns mean, and limitations. All frequencies are in MHz (e.g., 146.52). Strings (like names) can't have special characters that break CSV format—stick to letters, numbers, and spaces.

### 1. Analog\_template.csv (Analog Channels)

Analog channels are for traditional FM radio modes, like listening to weather broadcasts or talking directly radio-to-radio.

**Columns:**

- **Zone**: Group name for channels (e.g., "NOAA" or "Calling"). Max `max_zone_name_characters`.
- **Channel Name**: Name of the channel (e.g., "NOAA1"). Max `max_channel_name_characters`.
- **Bandwidth**: "25K" (wide) or "12.5K" (narrow). Use "25K" for most ham uses.
- **Power**: Transmit power: "Low", "Mid", "High", or "Turbo".
- **RX Freq**: Receive frequency (e.g., 162.4). Between 136 and 480 MHz.
- **TX Freq**: Transmit frequency (e.g., 440). Same as RX for simplex; different for repeaters. Between 136 and 480 MHz.
- **CTCSS Decode**: Tone for receiving (e.g., "Off" or a number like 67.0). "Off" or valid CTCSS/DCS code (0–300 or Dxxx format).
- **CTCSS Encode**: Tone for transmitting. Same as above.
- **TX Prohibit**: "On" (can't transmit) or "Off" (can transmit).

**Limitations:**

- Channel names must be unique and ≤ `max_channel_name_characters` chars.
- Frequencies must be valid numbers; no letters.
- Example: For weather listening, set TX Prohibit to "On" so you don't accidentally transmit.

### 2. Digital-Others\_template.csv (DMR Simplex/Hotspots)

For digital DMR channels that aren't repeaters, like hotspots (small devices that connect your radio to the internet).

**Columns:**

- **Zone**: Group name (e.g., "PiStar"). Max `max_zone_name_characters`.
- **Channel Name**: Name (e.g., "PiBM/Bridge 2"). Max `max_channel_name_characters`.
- **Power**: "Low", "Mid", "High", or "Turbo".
- **RX Freq**: Receive freq (e.g., 440.35).
- **TX Freq**: Transmit freq (e.g., 445.35).
- **RX Color Code**: Number Range `color_code_min` - `color_code_max` (like a "channel code" for DMR).
- **TX Color Code**: Same as RX, or Range `color_code_min` - `color_code_max`. If blank, uses RX value.
- **Talk Group**: Name of the talkgroup (must match one in TalkGroups\_template.csv, e.g., "Bridge 2").
- **TimeSlot**: "1" or "2" (DMR time slots).
- **Call Type**: "Group Call" or "Private Call".
- **TX Permit**: "Always", "ChannelFree", "Same Color Code", or "Different Color Code".

**Limitations:**

- Talk Group must exist in TalkGroups.csv.
- Color codes: Range `color_code_min` - `color_code_max`.
- For hotspots, use "Low" power to avoid interference.

### 3. Digital-Repeaters\_template.csv (DMR Repeaters)

For digital repeaters. This file is special — it uses a matrix format where columns after the basics are talkgroups.

**Columns (first few are fixed; then one column per talkgroup):**

- **Zone Name**: Repeater name, optionally with nickname (e.g., "Salem/MT;SMT"). Full name;nickname. Max `max_zone_name_characters`. Nickname delineated by characters following ";".
- **Comment**: Optional notes (ignored by program currently).
- **Power**: "Low", "Mid", "High", or "Turbo".
- **RX Freq**: Receive freq from repeater.
- **TX Freq**: Transmit freq to repeater (usually offset from RX).
- **Color Code**: Range `color_code_min` - `color_code_max`.
- Then, columns for each talkgroup (e.g., "DMR Anarchy", "Bridge 2"): Enter "1" or "2" for time slot, or "-" for none. Add ";P" for private call (e.g., "1;P").

**Limitations:**

- Add new talkgroup columns by adding headers and values.
- Zone Name nickname (after ";") is used for short channel names if enabled.
- TimeSlot: "1", "2", or "-".
- The program creates one channel per talkgroup per repeater.

>[!IMPORTANT]
> Every row for repeaters must have an entry for every Talkgroup Header. Use "-" for the Talkgroups that are not present on that repeater.

### 4. TalkGroups\_template.csv (Talkgroups List)

A list of DMR talkgroups used in digital channels.

**Columns:**

- **Radio ID**: Numeric ID (e.g., 9990). Positive integer.
- **Name**: Talkgroup name (e.g., "Parrot"). Max 16 chars (but keep short).
- **Call Type**: "Group Call" or "Private Call" (Optional; default "Group Call")
- **Call Alert**: "None" or other (usually "None").

**Limitations:**

- IDs must be unique and match what's used in digital files.
- Names must be unique; no duplicates.
- This file is required for digital channels.

> [!TIP]
> Each talkgroup name in this file must match exactly the ones utilized in the `--digital-others-csv` and the `--digital-repeaters-csv`.
> Additional Talkgroups contained in this file that are not referenced will still be included in the output.

## **General Limitations Across All Templates**

- Limitations are set in the `radio.yml` file. Ensure you update each radio ID as required.

## Command-Line Options

Run `python main.py --help` for a list. Required unless generating templates: Provide paths to the four input CSV files.

```shell
usage: main.py [-h] [--analog-csv ANALOG_CSV] [--digital-others-csv DIGITAL_OTHERS_CSV] [--digital-repeaters-csv DIGITAL_REPEATERS_CSV] [--talkgroups-csv TALKGROUPS_CSV] [--output-directory OUTPUT_DIRECTORY]
               [--config CONFIG] [--radio-config RADIO_CONFIG] [--radio-id RADIO_ID] [--verify-defaults] [--sorting {alpha,repeaters-first,analog-first,analog_and_others_first}]
               [--hotspot-tx-permit {always,same-color-code}] [--nicknames {off,prefix,suffix,prefix-forced,suffix-forced}] [--talkgroup-sort {input,id,name}] [--generate-templates] [--dmr-id DMR_ID]

Anytone Config Builder

This script generates CSV files for Anytone CPS from input CSV files.
Use --generate-templates to create example CSV files with headers.

options:
  -h, --help            show this help message and exit
  --analog-csv ANALOG_CSV
                        Path to Analog.csv (analog channels). Required unless --generate-templates is used.
  --digital-others-csv DIGITAL_OTHERS_CSV
                        Path to Digital-Others.csv (DMR simplex, hotspots). Required unless --generate-templates is used.
  --digital-repeaters-csv DIGITAL_REPEATERS_CSV
                        Path to Digital-Repeaters.csv (DMR repeaters). Required unless --generate-templates is used.
  --talkgroups-csv TALKGROUPS_CSV
                        Path to TalkGroups.csv (talkgroup names and IDs). Required unless --generate-templates is used.
  --output-directory OUTPUT_DIRECTORY
                        Directory for output CSV files. Defaults to ./Output.
  --config CONFIG       Directory containing radio.yml. Defaults to "config".
  --radio-config RADIO_CONFIG
                        Path to radio configuration YAML file. Defaults to config/radio.yml.
  --radio-id RADIO_ID   Radio ID to select configuration for. Default: 1
  --verify-defaults     Verify the radio configuration file and exit.
  --sorting {alpha,repeaters-first,analog-first,analog_and_others_first}
                        Zone sorting mode. Default: alpha
  --hotspot-tx-permit {always,same-color-code}
                        TX Permit for hotspots. Default: same-color-code
  --nicknames {off,prefix,suffix,prefix-forced,suffix-forced}
                        Nickname mode for channel names. Default: off
  --talkgroup-sort {input,id,name}
                        Talkgroup sorting mode. Default: input
  --generate-templates  Generate empty CSV templates with headers in ./Templates and exit.
  --dmr-id DMR_ID       Your DMR ID to generate radio_id_list.csv.
```

## Output Files

In the output folder:

- `channels.csv`: All channels combined.
- `zones.csv`: Zone groups.
- `scanlists.csv`: Scan lists (for auto-scanning channels).
- `talkgroups.csv`: Talkgroup list.
- `radio_id_list.csv` (if `--dmr-id` used): Your radio ID.

## Troubleshooting

- **Errors:**
  - Usually mean invalid data (e.g., bad frequency). Check the message for line/file.
- **Warnings:**
  - Like truncated zones — non-fatal, but check your radio limits.

## First Time Using

1. Ensure you have Python installed.

2. Ensure you have `PyYAML` installed.

3. Run `python main.py --generate-templates`

4. Then run:

   ```bash
   python main.py --analog-csv "./Templates/Analog_template.csv" \
     --digital-others-csv "./Templates/Digital-Others_template.csv" \
     --digital-repeaters-csv "./Templates/Digital-Repeaters_template.csv" \
     --talkgroups-csv "./Templates/TalkGroups_template.csv" \
     --nicknames prefix \
     --sorting analog_and_others_first \
     --talkgroup-sort name \
     --dmr-id <dmr-id>
   ```

5. Review the output files to see how things are generated.

## Shout Out and Thank You

I have to give a huge shoutout to [K7ABD](https://github.com/K7ABD) and his work on the [anytone-config-builder](https://github.com/K7ABD/anytone-config-builder). I have used his tool countless times and finally got around to working one out in Python as I am no expert in Perl. Really not an expert in either but I enjoy the challenge. I based a lot of my effort here on what he did with some personal tweaks.

Enjoy building your codeplug! 🚀

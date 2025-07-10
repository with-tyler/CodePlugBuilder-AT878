# Anytone Config Builder

This is a simple Python program designed to help ham radio enthusiasts create configuration files (in CSV format) for Anytone radios. These files can be imported into the Anytone CPS (CodePlug Software) to set up channels, zones, talkgroups, and other settings on your radio.

The program takes your custom settings from easy-to-edit CSV template files (like spreadsheets) and turns them into the exact CSV files needed by the Anytone CPS. It's especially useful for setting up analog channels (like traditional FM radio frequencies) and digital channels (DMR mode for things like repeaters and hotspots).

If you're not very technical, don't worry! You can edit the template files using a spreadsheet program like Microsoft Excel, Google Sheets, or LibreOffice Calc. Just fill in the columns as described below, save them as CSV files, and run the program.

## Prerequisites

- **Python 3**: You need Python 3 installed on your computer. Download it from [python.org](https://www.python.org/downloads/) if you don't have it. (The program uses Python 3.13, but any Python 3 version should work.)
- **No extra installations needed**: The program uses built-in Python features, so no additional libraries are required.
- **A text editor or spreadsheet app**: For editing the CSV templates.

## How to Run the Program

1. Download or copy the `builder.py` file and the `config` folder (which contains `channel-defaults.csv`) to a folder on your computer.
2. Open a command prompt or terminal:
   - On Windows: Search for "cmd" and open Command Prompt. Navigate to your folder using `cd path\to\your\folder`.
   - On macOS/Linux: Open Terminal and use `cd` to go to the folder.
3. Run the program with Python: Type `python builder.py` (or `python3 builder.py` on some systems) followed by options (explained below).

The program will process your input files and create output CSVs in a folder (default: `./Output`).

## Generating Template Files

Before creating your config, generate blank template files with example data. These are starter CSV files you can edit.

Run this command:

`python3 builder.py --generate-templates` or `python builder.py --generate-templates`

- This creates a `./Templates` folder with four files:
  - `Analog_template.csv`: For analog (non-digital) channels like weather radios or simplex calling frequencies.
  - `Digital-Others_template.csv`: For digital DMR simplex channels or hotspots (like Pi-Star setups).
  - `Digital-Repeaters_template.csv`: For digital DMR repeaters (stations that boost your signal over a wider area).
  - `TalkGroups_template.csv`: A list of talkgroups (like group chat IDs in DMR digital mode).

These templates include headers (column names) and a few example rows. Open them in a spreadsheet app, edit the rows, add new ones as needed, and save (make sure to save as CSV format).

**Tip**: Don't change the header row (first line). Add or edit rows below it. If a cell is empty, the program might use a default value or give an error if it's required.

## Using the Template Files

Each template is a CSV file that looks like a table. Here's what each one is for, what columns mean, and limitations. All frequencies are in MHz (e.g., 146.52). Strings (like names) can't have special characters that break CSV format—stick to letters, numbers, and spaces.

### 1. Analog_template.csv (Analog Channels)

Analog channels are for traditional FM radio modes, like listening to weather broadcasts or talking directly radio-to-radio.

Columns:

- **Zone**: Group name for channels (e.g., "NOAA" or "Calling"). Max 16 characters. This organizes channels in your radio.
- **Channel Name**: Name of the channel (e.g., "NOAA1"). Max 16 characters.
- **Bandwidth**: "25K" (wide) or "12.5K" (narrow). Use "25K" for most ham uses.
- **Power**: Transmit power: "Low", "Mid", "High", or "Turbo".
- **RX Freq**: Receive frequency (e.g., 162.4). Between 0 and 500 MHz.
- **TX Freq**: Transmit frequency (e.g., 440). Same as RX for simplex; different for repeaters. Between 0 and 500 MHz.
- **CTCSS Decode**: Tone for receiving (e.g., "Off" or a number like 67.0). "Off" or valid CTCSS/DCS code (0-300 or Dxxx format).
- **CTCSS Encode**: Tone for transmitting. Same as above.
- **TX Prohibit**: "On" (can't transmit) or "Off" (can transmit).

Limitations:

- Channel names must be unique and <=16 chars.
- Frequencies must be valid numbers; no letters.
- Example: For weather listening, set TX Prohibit to "On" so you don't accidentally transmit.

### 2. Digital-Others_template.csv (DMR Simplex/Hotspots)

For digital DMR channels that aren't repeaters, like hotspots (small devices that connect your radio to the internet).

Columns:

- **Zone**: Group name (e.g., "PiStar"). Max 16 chars.
- **Channel Name**: Name (e.g., "PiBM/Bridge 2"). Max 16 chars.
- **Power**: "Low", "Mid", "High", or "Turbo".
- **RX Freq**: Receive freq (e.g., 440.35).
- **TX Freq**: Transmit freq (e.g., 445.35). For simplex/hotspots, often different from RX.
- **RX Color Code**: Number 0-16 (like a "channel code" for DMR). Usually 1.
- **TX Color Code**: Same as RX, or different (0-16). If blank, uses RX value.
- **Talk Group**: Name of the talkgroup (must match one in TalkGroups_template.csv, e.g., "Bridge 2").
- **TimeSlot**: "1" or "2" (DMR time slots).
- **Call Type**: "Group Call" or "Private Call".
- **TX Permit**: "Always", "ChannelFree", "Same Color Code", or "Different Color Code".

Limitations:

- Talk Group must exist in TalkGroups.csv.
- Color codes: 0-16 only.
- For hotspots, use "Low" power to avoid interference.

### 3. Digital-Repeaters_template.csv (DMR Repeaters)

For digital repeaters. This file is special—it uses a matrix format where columns after the basics are talkgroups.

Columns (first few are fixed; then one column per talkgroup):

- **Zone Name**: Repeater name, optionally with nickname (e.g., "Salem/MT;SMT"). Full name;nickname. Max 16 chars each.
- **Comment**: Optional notes (ignored by program).
- **Power**: "Low", "Mid", "High", or "Turbo".
- **RX Freq**: Receive freq from repeater.
- **TX Freq**: Transmit freq to repeater (usually offset from RX).
- **Color Code**: 0-16.
- Then, columns for each talkgroup (e.g., "DMR Anarchy", "Bridge 2"): Enter "1" or "2" for time slot, or "-" for none. Add ";P" for private call (e.g., "1;P").

Limitations:

- Add new talkgroup columns by adding headers and values.
- Zone Name nickname (after ";") is used for short channel names if enabled.
- TimeSlot: "1", "2", or "-".
- The program creates one channel per talkgroup per repeater.

>[!IMPORTANT] Must Have an Entry
>Every row for repeaters must have an entry for every Talkgroup Header. Use "-" for the Talkgroups that are not present on that repeater.

### 4. TalkGroups_template.csv (Talkgroups List)

A list of DMR talkgroups used in digital channels.

Columns:

- **Radio ID**: Numeric ID (e.g., 9990). Positive integer.
- **Name**: Talkgroup name (e.g., "Parrot"). Max 16 chars? (but keep short).
- **Call Type**: "Group Call" or "Private Call" (Optional; default "Group Call")
- **Call Alert**: "None" or other (usually "None").

Limitations:

- IDs must be unique and match what's used in digital files.
- Names must be unique; no duplicates.
- This file is required for digital channels.

>[!TIP] Talkgroup Names Must Match
>Each talkgroup name in this file must match exactly the ones utilized in the `--digital-others-csv` and the `--digital-repeaters-csv`.
>
> Additional Talkgroups contained in this file that are not references will still be included in the output.

**General Limitations Across All Templates**:

- No more than 250 channels per zone zone.
- Scanlists (automatic channel scanning groups) limited to 50 channels; if more, the program splits them (e.g., "Zone_OF1").
- Names can't exceed 16 characters (radio display limit).
- Frequencies: 0-500 MHz, with valid decimals.
- Always use quotes around values with spaces if editing in text.
- Required fields: If something's missing, the program will error—check error messages.

## Command-Line Options

Run `python builder.py --help` for a list. Required unless generating templates: Provide paths to the four input CSV files.

- `--analog-csv <path>`: Path to your edited Analog.csv (e.g., `--analog-csv ./Templates/Analog_template.csv`).
- `--digital-others-csv <path>`: Path to Digital-Others.csv.
- `--digital-repeaters-csv <path>`: Path to Digital-Repeaters.csv.
- `--talkgroups-csv <path>`: Path to TalkGroups.csv.
- `--output-directory <path>` (optional, default ./Output): Where to save output files.
- `--config <path>` (default 'config'): Folder with channel-defaults.csv (don't change unless advanced).
- `--sorting <mode>` (default 'alpha'): How to sort zones in output:
  - 'alpha': Alphabetical (A-Z.
  - 'repeaters-first': Digital repeaters first, then others (each group alpha sorted).
  - 'analog-first': Analog first, then others.
  - 'analog_and_others_first': Analog and digital simplex/hotspots first, then repeaters.
- `--hotspot_tx_permit <mode>` (default 'same-color-code'): For hotspots (where RX=TX freq):
  - 'always': Always allow transmit.
  - 'same-color-code': Only if color codes match (safer default).
- `--nicknames <mode>` (default 'off'): Use nicknames (short abbreviations) in channel names:
  - 'off': No nicknames.
  - 'prefix': Add zone nickname as prefix if it fits (e.g., "SMT-Parrot").
  - 'suffix': Add as suffix.
  - 'prefix-forced': Force prefix, use short talkgroup name if needed.
  - 'suffix-forced': Force suffix.
  - This helps with long names (limited to 16 chars).
- `--generate-templates`: Create blank templates and exit (no other inputs needed).
- `--dmr-id <your_ID>`: Your personal DMR ID (number). Adds a `radio_id_list.csv` file for private calls to your ID.

## Output Files

In the output folder:

- `channels.csv`: All channels combined.
- `zones.csv`: Zone groups.
- `scanlists.csv`: Scan lists (for auto-scanning channels).
- `talkgroups.csv`: Talkgroup list.
- `radio_id_list.csv` (if --dmr-id used): Your radio ID.

Import these into Anytone CPS. If errors, check console for warnings (e.g., name too long).

## Troubleshooting

- Errors: Usually mean invalid data (e.g., bad frequency). Check the message for line/file.
- Warnings: Like truncated zones—non-fatal, but check your radio limits.

## First Time Using

1. Ensure you have Python installed.
2. Run `python builder.py --generate-templates`

    - That will generate a template directory (`./Templates`) with the template files.

3. Then we can use those templates files to run the builder:

    ```shell
    python3.13 builder.py --analog-csv "./Templates/Analog_template.csv" /
    --digital-others-csv "./Templates/Digital-Others_template.csv" /
    --digital-repeaters-csv "./Templates/Digital-Repeaters_template.csv" /
    --talkgroups-csv "./Templates/TalkGroups_template.csv" /
    --nicknames prefix /
    --sorting analog_and_others_first /
    --dmr-id <dmr-id>
    ```

4. Review those files to see how things are generated and what is needed in the template files to generate your codeplug.

## Shout Out and Thank You

I have to give a huge shoutout to [K7ABD](https://github.com/K7ABD) and his work on the [anytone-config-builder](https://github.com/K7ABD/anytone-config-builder). I have used his tool countless times and finally got around to working one out in Python as I am no expert in Perl. Really not an expert in either but I enjoy the challenge. I based a lot of my effort here on what he did with some personal tweaks.

Enjoy building your codeplug! 🚀

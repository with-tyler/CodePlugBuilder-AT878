# template_generator.py
import csv
import os

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
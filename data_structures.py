# data_structures.py
from collections import defaultdict

class Data:
    def __init__(self):
        self.talkgroup_mapping = {}
        self.talkgroup_order = {}
        self.all_talkgroups = []  # List to store all talkgroups from input file
        self.zone_config = defaultdict(list)
        self.zone_order = {}
        self.zone_type = {}  # Dictionary to track zone types
        self.scanlist_config = defaultdict(list)
        self.talkgroup_config = {}
        self.scanlist_channel_counts = defaultdict(int)  # Dictionary to track channel counts per scanlist
        self.channel_number = 1
        self.analog_channel_index = 0
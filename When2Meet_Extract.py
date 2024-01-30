from bs4 import BeautifulSoup
import requests
import re
import datetime
import pandas as pd


when2meet_page = requests.get('Link here')

class GetData:
    def __init__(self, soup):
        self.soup = soup
        self.normal_time = self.get_time()
        self.nameid_names = self.get_nameid_names()

    def get_time(self):
        # When2Meet has its time in UNIX format in the following structure: TimeOfSlot[##]=UNIX Time;.
        table_data = self.soup.find(text=re.compile('TimeOfSlot*'))
        unix_time = re.compile(r"TimeOfSlot\[\d+\]=(\d+);").findall(table_data)
        normal_time = []
        
        for unix in unix_time:
            time_stamp = datetime.datetime.fromtimestamp(int(unix))
            # adjust 6 hours ahead for the poll's settings
            time_stamp += datetime.timedelta(hours=6)
            # Add day of the week %A and 12 hour setting %I
            time = time_stamp.strftime('%A%I:%M')

            normal_time.append(time)
        return normal_time

    def get_nameid_names(self):
        # In <div id=AvailabilityGrids><script type="text/javascript">, When2Meet lists the unique IDs and the corresponding names.
        availability_grids = self.soup.find('div', {'id': 'AvailabilityGrids'})
        script_tags = availability_grids.find_all('script', {'type': 'text/javascript'})
        ids = re.findall(r'PeopleIDs\[\d+\] = (\d+);', script_tags[0].contents[0])
        names = re.findall(r"PeopleNames\[\d+\] = '([ a-zA-Z]{2,})';", script_tags[0].contents[0])
        nameid_names = dict(zip(ids,names))
        return nameid_names

    def get_slot_name(self):
        # When2Meet uses the following structure to label who is available at a time slot: AvailableAtSlot[Index].push(Unique ID);
        table_data = self.soup.find(text=re.compile('TimeOfSlot*'))
        dataset = re.compile(r"AvailableAtSlot\[(\d+)\]\.push\((\d+)\)").findall(table_data)
        slot_names = [(slot, self.nameid_names[nameid]) for slot, nameid in dataset] #Convert ID to Names

        return slot_names

#Get sets of names at different time slots
def get_sets(index_name, availability):
    time_sets = {}
   
    for slot, name in availability:
        # Convert the slot to a human-readable time format
        time_str = index_name[int(slot)]

        # Check if the time set exists, if not, create it
        if time_str not in time_sets:
            time_sets[time_str] = set()

        # Add the name to the corresponding time set
        time_sets[time_str].add(name)

    return time_sets



soup = GetData(BeautifulSoup(when2meet_page.content, "html.parser"))
slot_names = soup.get_slot_name()
sets = get_sets(soup.normal_time, slot_names)
for time_str, names_set in sets.items():
    print(f"At {time_str}: {names_set}")


#print(export_dataset)
#export_dataset.to_csv('times.csv', encoding='utf-8', index=True)


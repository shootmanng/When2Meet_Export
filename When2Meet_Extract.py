from bs4 import BeautifulSoup
import requests
import re
import datetime


when2meet_page = requests.get('https://www.when2meet.com/POLL Link')

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

# Get sets of names at different time slots
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

# Remove test entries I made named 'Scott', if you have a test entry to remove, change the string below to the test name, or, if not, remove/comment out the following block:
for times in sets:
    if 'Scott' in sets[times]:
        sets[times].remove('Scott')
        
# set size counter
k=0

# remove times that conflict with personal/work calendar
sets.pop('Wednesday03:15')
sets.pop('Thursday12:00')
sets.pop('Tuesday12:00')
# end removed time blocks

# create reference set to remove already tested values to avoid duplicate comparisons
sets1=sets.copy()

# compare different time blocks by unioning their members and counting the size of the set, storing the relevant values with the largest size (the result may not be unique, i.e. there can be several time blocks with the max number of students)
while len(sets1)!=0:
    for times1 in sets:
        sets1.pop(times1)
        for times2 in sets1:
            if len(sets[times1] | sets[times2])>k:
                k=len(sets[times1] | sets[times2])
                b1=sets[times1]
                b2=sets[times2]
                t1=times1
                t2=times2
                
# print the results
print('The maximal number of students covered by the blocks ',t1,' and ',t2,' is ',k,' and the students are ',b1 | b2)
print('--------------------')
# pick two hour blocks based on this info and see the total number of students covered
print('The total students covered by hour blocks chosen is', sets['Monday03:00'] | sets['Monday03:15'] | sets['Monday03:30'] | sets['Monday03:45'] | sets['Thursday12:30'] | sets['Thursday12:45'] | sets['Thursday01:00']| sets['Thursday01:15'],'which is ',len(sets['Monday03:00'] | sets['Monday03:15'] | sets['Monday03:30'] | sets['Monday03:45'] | sets['Thursday12:30'] | sets['Thursday12:45'] | sets['Thursday01:00']| sets['Thursday01:15']),'students')

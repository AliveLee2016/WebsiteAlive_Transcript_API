#This is a sample script that can be used with the WebsiteAlive API to
#pull larger than normally allowed date ranges from the WSA system.
#This script will pull on a day by day basis to help prevent timeouts
#due to slow connection speeds or larger than average amounts of data.
#You will need to enter either Admin credentials or operator credentials
#for an operator that has administrative rights to run the chat transcript
#report.
from __future__ import unicode_literals
import json
import requests
from datetime import datetime
from pytz import UTC
import pytest
from datetime import timedelta
from datetime import date
import csv

#This method generates a token for the user attempting to pull chat transcripts.
def get_token(username, password):
    tokens_rsp = requests.post(
    'https://api.websitealive.com/auth/token',
    data=json.dumps({'username': username, 'password': password}),
    headers={'content-type': 'application/json'})
    if tokens_rsp.status_code != requests.codes.ok:
        raise Exception('Get auth token failed. Code: {}. Reason: {}. Details: {}'.format(
            tokens_rsp.status_code, tokens_rsp.reason, tokens_rsp.content))

    access_token = tokens_rsp.json()['accessToken']
    return access_token

#This pulls the individual days. If an error occurs, then the day is re-tried
#a total of 10 times. If the system fails on each attempt, then a notice of the
#day is displayed and the script will continue onward.
def pullTrans(syear, smonth, sday, eyear, emonth, eday, access_token):
    cs_results = []
    transcripts_remain = True
    page = 1
    page_size = 10
    while transcripts_remain:
        tries = 0
        repeat = 1
        while repeat == 1:
            
            rs = requests.post(
                'https://api.websitealive.com/chat_search',
                data=json.dumps({
                    'dateStart': datetime(syear, smonth, sday, 0, 0, 0, 0, UTC).isoformat(),
                    'dateEnd': datetime(eyear, emonth, eday, 0, 0, 0, 0, UTC).isoformat(),
                    'properties': {'all': True},
                    'responseFormat': 'application/json',
                    'page': {
                        'size': page_size,
                        'number': page
                    }
                }),
                headers={
                    'content-type': 'application/json',
                    'authorization': 'token {}'.format(access_token)
                }
            )
            if rs.status_code != requests.codes.ok:#raise Exception('Chat search failed. Code: {}. Reason: {}. Details: {}'.format(rs.status_code, rs.reason, rs.content))
                repeat = 1
            else:
                repeat = 0
            if tries == 10:
                print str(smonth) + " " + str(sday) + " " + str(syear)
                print str(emonth) + " " + str(eday) + " " + str(eyear)
                return []
            else:
                tries +=1
    
        transcripts = rs.json()['transcripts']
        if rs.json()['transcripts']:
            cs_results.extend(transcripts)
            page += 1
        else:
            transcripts_remain = False
    #assert len(cs_results) > 0
    return cs_results


print "Login Credentials:"
uName = raw_input("Username: ")
pWord = raw_input("Password: ")

print "Starting date"
start_day = raw_input("Day: ")
start_month = raw_input("Month: ")
start_year = raw_input("Year: ")
print "End date"
end_day = raw_input("Day: ")
end_month = raw_input("Month: ")
end_year = raw_input("Year: ")
start = date(int(start_year), int(start_month), int(start_day))
end = date(int(end_year), int(end_month), int(end_day)+1)
one_day = timedelta(days = 1)

Run = 0
Runs = 0
access_token = get_token(uName, pWord)
chats = []
while Run == 0:
    Runs +=1
    if Runs == 10:
        access_token = get_token(uName, pWord)
    endb = end - one_day
    results = pullTrans(endb.year, endb.month, endb.day, end.year, end.month, end.day, access_token)
    #print str(endb) + " " + str(len(results))
    print len(results)
    if len(results) != 0:
        for i in results:
            chats.append(i)
    print len(chats)
    if end == start:
        print "Complete"
        Run = 1
    end = endb


#This segment creates the dictionary for the csv file, then converts the Json
#object into a Json string, to remove the Unicode indicators, then converts
#back into a Json object. This prevents any issues with non Ascii objects.
mDict = []
for i in chats:
    if len(i) > len(mDict):
        mDict = i
Keys = []
for key, item in mDict.iteritems():
    Keys.append(key)

jSonk = json.dumps(Keys)
jSonk = json.loads(jSonk)
csvName = "Transcripts " + str(start_month) + "-" + str(start_day) + "-" + str(start_year) + " to " + str(end_month) + "-" + str(end_day) + "-" + str(end_year) + ".csv"
with open(csvName, 'w') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames = jSonk)
    writer.writeheader()
    for i in chats:
        jSon1 = json.dumps(i)
        jSon1 = json.loads(jSon1)
        try:
            writer.writerow(jSon1)
        except:
            pass
    csvfile.close()
print "Done"

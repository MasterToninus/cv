#!/usr/bin/env python3
#
# Generates yaml of my activities from website
# Credits : https://commandercoriander.net/blog/2013/06/22/a-quick-path-from-csv-to-yaml/


import csv
import urllib.request
import codecs
import warnings
import datetime


def readmywebsite():
    # Stream the csv from my website to a Dict
    url = 'http://dmf.unicatt.it/miti/data/activities.csv'
    ftpstream = urllib.request.urlopen(url)
    csvfile = csv.DictReader(codecs.iterdecode(ftpstream, 'utf-8'),delimiter=";")

    # Parse Csv file to group different kind of entries
    # Meglio una funziona parse to yaml.
    schools = []
    conferences = []
    talks = []
    unused = set()

    # Limit date
    todaydate = datetime.datetime.now()
    limitdate = todaydate + datetime.timedelta(days=63)

    for line in csvfile:
        event = line.get('Type')
        date = datetime.datetime.strptime(line.get('Start_Date'), '%d-%b-%y')
        # Escaping % for use in latex
        url   = line.get('Url').replace('%','\%').replace('#','\#')
        line.update({'Url':url})
        if (date > todaydate):
            scheduled = line.get('Approx_Date')+" (scheduled)"
            line.update({'Approx_Date':scheduled})

        #Do not add events in the distant future
        if (date < limitdate):
            if event in ('Workshop','Conference'):
                conferences.append(line)
            elif event in ('Training Course','Ph.D. Course','School','Summer school','Master Course','Reading Course','Industry Course'):
               schools.append(line)
            elif event in ('Invited Talk','Contributed Talk','Poster'):
              talks.append(line)    
            else:
                unused.add(event)
            
    #
    msg = "Unused keys:"+ str(unused)
    warnings.warn(msg)

    # Reverse in anticrhonological order
    schools.reverse()
    conferences.reverse()
    talks.reverse()




    # Arrange the contents in a single dictionary
    yamlcontents = {
        "schools":schools,
        "conferences":conferences,
        "talks":talks
    }
    return (yamlcontents)


#!/usr/bin/env python3
#
# Generates yaml of my activities from website
# Credits : https://commandercoriander.net/blog/2013/06/22/a-quick-path-from-csv-to-yaml/


import csv
import urllib.request
import codecs
import warnings

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

    for line in csvfile:
        event = line.get('Type')
        # Escaping % for use in latex
        url   = line.get('Url').replace('%','\%').replace('#','\#')
        line.update({'Url':url})

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


"""
CV Data Processor
Author: Antonio Miti
Description:
    Processes online CSV data and BibTeX publications to prepare structured data for LaTeX CV.
Last Updated: 2024-12-23
"""

import csv
import urllib.request
import codecs
import warnings
import datetime
import yaml
from pybtex.database import parse_file
from pybliometrics.scopus import AuthorRetrieval

# Global variables
CSV_URL = 'http://antoniomiti.it/data/activities.csv'
BIBTEX_FILEPATH = 'data/publications.bib'
SCOPUS_AUTHOR_ID = '57218509273'
YAML_FILEPATH = 'data/cv.yaml'
PHD_DEFENSE_DATE = datetime.datetime(2021, 4, 1)

def readmywebsite():
    """
    Reads activities from a CSV file hosted on a website and categorizes them.

    Returns:
        dict: A dictionary containing categorized activities and their counts.
    """
    # Stream the CSV file from the provided URL and parse it into a dictionary format
    ftpstream = urllib.request.urlopen(CSV_URL)
    csvfile = csv.DictReader(codecs.iterdecode(ftpstream, 'utf-8'), delimiter=";")

    # Initialize lists for categorized events and a set for uncategorized events
    schools = []
    conferences = []
    talks = []
    unused = set()

    # List to count occurrences of each event type
    talksnum = [
        {'type': 'Invited Talks', 'value': 0},
        {'type': 'Contributed Talks and Posters', 'value': 0},
        {'type': 'Attended Conferences', 'value': 0}
    ]

    # Define date limits to filter future events
    todaydate = datetime.datetime.now()
    limitdate = todaydate + datetime.timedelta(days=63)

    for line in csvfile:
        event = line.get('Type')
        date = datetime.datetime.strptime(line.get('Start_Date'), '%d-%b-%y')
        
        # Escape LaTeX special characters in URLs
        url = line.get('Url').replace('%', '\%').replace('#', '\#')
        line.update({'Url': url})

        # Mark future events as "scheduled"
        line.update({'Scheduled': ""})
        if date > todaydate:
            line.update({'Scheduled': "(scheduled)"})

        # Convert Approx_Date from "Month Year" to "mm/yy"
        approx_date = datetime.datetime.strptime(line.get('Approx_Date'), '%B %Y').strftime('%m/%Y')
        line.update({'Approx_Date': approx_date})

        # Update the event type count
        if event in ('Invited Talk'):
            talksnum[0]['value'] += 1
        elif event in ('Contributed Talk', 'Poster'):
            talksnum[1]['value'] += 1
        elif event in ('Workshop', 'Conference', 'School'):
            talksnum[2]['value'] += 1
        else:
            unused.add(event)

        # Categorize events based on type and date limits
        if date < limitdate:
            if event in ('Workshop', 'Conference'):
                conferences.append(line)
            elif event in ('Training Course', 'Ph.D. Course', 'School', 'Summer school', 'Master Course', 'Reading Course', 'Industry Course'):
                schools.append(line)
            elif event in ('Invited Talk', 'Contributed Talk', 'Poster'):
                talks.append(line)
            else:
                unused.add(event)

    # Warn about any uncategorized event types
    msg = "Unused keys: " + str(unused)
    warnings.warn(msg)  # This warning highlights uncategorized event types but does not affect program output

    # Reverse lists to ensure events are in anti-chronological order
    schools.reverse()
    conferences.reverse()
    talks.reverse()

    # Combine categorized events and counts into a single output dictionary
    yamlcontents = {
        "schools": schools,
        "conferences": conferences,
        "talks": talks,
        "talksnum": talksnum  # Includes counts of each event type
    }
    # Final structured output ready for further processing or export
    return yamlcontents

def readmybibfile():
    """
    Reads publications from a BibTeX file and counts the number of each type.
    Also stores publication citation keys and their type.

    Returns:
        dict: A dictionary containing counts of different types of publications and their details.
    """
    # Parse the BibTeX file
    bib_data = parse_file(BIBTEX_FILEPATH)

    # Initialize counts and details
    pubsnum = [
        {'type': 'Published Papers', 'value': 0},
        {'type': 'Preprints', 'value': 0},
        {'type': 'Drafts in Preparation', 'value': 0}
    ]
    pub_details = []

    # Categorize entries based on type
    for entry_key, entry in bib_data.entries.items():
        entry_type = entry.type.lower()
        pub_detail = {'key': entry_key, 'type': entry_type}

        if entry_type in ('article', 'book', 'inproceedings', 'proceedings'):
            pubsnum[0]['value'] += 1
            pub_detail['type'] = 'published'
        elif entry_type in ('unpublished', 'preprint'):
            pubsnum[1]['value'] += 1
            pub_detail['type'] = 'preprints'
        elif entry_type == 'draft':
            pubsnum[2]['value'] += 1
            pub_detail['type'] = 'drafts'
        elif entry_type == 'phdthesis' or entry_type == 'mastersthesis':
            pub_detail['type'] = 'thesis'

        pub_details.append(pub_detail)

    # Calculate postdoctoral experience in years
    today_date = datetime.datetime.now()
    postdoc_years = (today_date - PHD_DEFENSE_DATE).days // 365

    # Add postdoctoral experience to pubsnum
    pubsnum.append({'type': 'Postdoctoral experience (years)', 'value': postdoc_years})

    return {'pubsnum': pubsnum, 'pub_details': pub_details}

def readmyscopus():
    """
    Reads author information from Scopus using the pybliometrics API.

    Returns:
        dict: A dictionary containing author information and metrics.
    """
    author = AuthorRetrieval(SCOPUS_AUTHOR_ID)

    scopus_data = {
        'name': author.given_name + ' ' + author.surname,
        'affiliation': author.affiliation_current[0]['name'],
        'documents': author.document_count,
        'citations': author.citation_count,
        'h_index': author.h_index,
        'subjects': [subject['name'] for subject in author.subject_areas]
    }

    return scopus_data

def readmyconfigurations():
    """
    Reads the YAML file and counts the number of conferences organized, courses taught, and total frontal teaching load.

    Returns:
        list: A list of dictionaries containing the counts of conferences organized, courses taught, and total frontal teaching load.
    """
    with open(YAML_FILEPATH, 'r', encoding='utf-8') as f:
        yaml_contents = yaml.safe_load(f)

    conferences_organized = 0
    courses_taught = 0
    total_frontal_teaching_load = 0

    # Count conferences organized
    if 'org' in yaml_contents:
        conferences_organized = len(yaml_contents['org'])

    # Count courses taught and sum the total frontal teaching load
    if 'teach' in yaml_contents:
        courses_taught = len(yaml_contents['teach'])
        total_frontal_teaching_load = sum(course.get('load', 0) for course in yaml_contents['teach'])

    teachnum = [
        {'type': 'Conferences Organized', 'value': conferences_organized},
        {'type': 'Courses Taught', 'value': courses_taught},
        {'type': 'Frontal Teaching (hours)', 'value': total_frontal_teaching_load}
    ]

    return teachnum

# Example usage:
# bibtex_counts = parse_bibtex_and_count()
# print(bibtex_counts)
# teachnum = readmyconfigurations()
# print(teachnum)

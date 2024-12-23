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
from pybtex.database import parse_file
from pybliometrics.scopus import AuthorRetrieval

# Global variables
CSV_URL = 'http://antoniomiti.it/data/activities.csv'
BIBTEX_FILEPATH = 'data/publications.bib'
SCOPUS_AUTHOR_ID = '57218509273'

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

    # Dictionary to count occurrences of each event type
    entry_counts = {}  # Tracks the count of each event type encountered in the CSV file

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
        if event in entry_counts:
            entry_counts[event] += 1
        else:
            entry_counts[event] = 1

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
        "entry_counts": entry_counts  # Includes counts of each event type
    }
    # Final structured output ready for further processing or export
    return yamlcontents

def readmybibfile():
    """
    Reads publications from a BibTeX file and counts the number of each type.

    Returns:
        list: A list of dictionaries containing counts of different types of publications.
    """
    # Parse the BibTeX file
    bib_data = parse_file(BIBTEX_FILEPATH)

    # Initialize counts
    pubsnum = [
        {'type': 'Published Papers', 'value': 0},
        {'type': 'Preprints', 'value': 0},
        {'type': 'Drafts', 'value': 0}
    ]

    # Categorize entries based on type
    for entry in bib_data.entries.values():
        entry_type = entry.type.lower()

        if entry_type in ('article', 'book', 'inproceedings', 'proceedings'):
            pubsnum[0]['value'] += 1
        elif entry_type in ('unpublished', 'preprint'):
            pubsnum[1]['value'] += 1
        elif entry_type == 'draft':
            pubsnum[2]['value'] += 1

    return pubsnum

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

# Example usage:
# bibtex_counts = parse_bibtex_and_count()
# print(bibtex_counts)

"""
Generate CV Script
Author: Antonio Miti
Description:
    Combines YAML, website activities, and publications data to produce a professional LaTeX CV.
Last Updated: 2024-12-23
"""

#!/usr/bin/env python3

import yaml
import os
from datetime import date
from jinja2 import Environment, FileSystemLoader
from getactivities import readmywebsite, readmybibfile, readmyscopus, readmyconfigurations
from pybliometrics.scopus import init

# Initialize pybliometrics configuration
init()

# Initialize the Jinja2 environment with custom delimiters for LaTeX compatibility
env = Environment(
    loader=FileSystemLoader("tmpl"),
    block_start_string='~{',
    block_end_string='}~',
    variable_start_string='~{{',
    variable_end_string='}}~',
    comment_start_string="~{#",
    comment_end_string="#}~"
)

# Load CV data from YAML file
with open("data/cv.yaml", 'r', encoding='utf-8') as f:
    yaml_contents = yaml.safe_load(f)

# Merge activities from the website into the YAML data
activities = readmywebsite()
yaml_contents.update(activities)

# Read and update publication counts from the BibTeX file
pubsnum = readmybibfile()
yaml_contents.update({'pubsnum': pubsnum})

# Read and update teaching counts from the YAML file
teachnum = readmyconfigurations()
yaml_contents.update({'teachnum': teachnum})

# Move "Conferences Organized" from teachnum to talksnum
for item in teachnum:
    if item['type'] == 'Conferences Organized':
        yaml_contents['talksnum'].append(item)
        teachnum.remove(item)
        break

# Optionally read and update Scopus data
# scopus_data = readmyscopus()
# yaml_contents.update(scopus_data)

# Ensure the output directory exists
if not os.path.exists("gen"):
    os.makedirs("gen")

def generate(ext):
    """
    Generates the CV in the specified format.

    Args:
        ext (str): The file extension for the output format (e.g., 'tex').

    Returns:
        None
    """
    body1, body2, body3 = "", "", ""  # Initialize content for the three columns

    # Process each section defined in the YAML order
    for section in yaml_contents['order']:
        name = section[0]          # Section title
        contents = yaml_contents[section[1]]  # Section content
        kind = section[2]          # Section type (e.g., list, table)
        column = section[3]        # Target column for this section

        # Render the section using the appropriate template
        parsed = env.get_template("section_tmpl." + ext).render(
            name=name,
            contents=contents,
            kind=kind
        )

        # Assign the rendered section to the appropriate column
        if column == 1:
            body1 += parsed
        elif column == 2:
            body2 += parsed
        else:
            body3 += parsed

    # Generate the cover statement
    coverstatement = yaml_contents['coverstatement'] + "\\vspace{0.25em}\n\n\\textbf{Keywords: }\\it "
    for line in yaml_contents['keywords']:
        coverstatement += line + ", "
    coverstatement = coverstatement[:-2] + "."

    # Write the CV to the output file
    with open(f"gen/cv.{ext}", 'w+', encoding='utf-8') as f_cv:
        f_cv.write(env.get_template("home_tmpl." + ext).render(
            name=yaml_contents['name'],
            phone=yaml_contents['phone'],
            email=yaml_contents['email'],
            site=yaml_contents['site'],
            github=yaml_contents['github'],
            currentposition=yaml_contents['currentposition'],
            coverstatement=coverstatement,
            body1=body1,
            body2=body2,
            body3=body3,
            pubsnum=pubsnum,
            talksnum=activities['talksnum'],
            teachnum=teachnum,
            today=date.today().strftime("%d/%m/%y")
        ))

# Generate the CV in LaTeX format
generate("tex")



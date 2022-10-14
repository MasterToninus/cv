#!/usr/bin/env python3
#
# Generates LaTeX version of my CV.
#
# Credits: Vittorio Erba https://github.com/vittorioerba
# 2019.12.06

import yaml
import sys

from datetime import date
from jinja2 import Environment, FileSystemLoader
from getactivities import readmywebsite

env = Environment(
        loader=FileSystemLoader("tmpl"),
        block_start_string      ='~{',
        block_end_string        ='}~',
        variable_start_string   ='~{{', 
        variable_end_string     ='}}~',
        comment_start_string    ="~{#", 
        comment_end_string      ="#}~"
        )

f = open("data/cv.yaml", 'r')
yaml_contents = yaml.safe_load(f)
yaml_contents.update(readmywebsite())
f.close()


# Create output directory
import os
if not os.path.exists("gen"):
    os.makedirs("gen")



def generate(ext):
    body1 = ""
    body2 = ""
    body3 = ""
    for section in yaml_contents['order']:
        name      = section[0]
        contents  = yaml_contents[section[1]]
        kind      = section[2] 
        column    = section[3]

        parsed = env.get_template("section_tmpl." + ext).render(
            name = name,
            contents = contents,
            kind = kind
            )


        if column == 1:
            body1 += parsed
        elif column == 2:
            body2 += parsed
        else:
            body3 += parsed

    #Generate cover paper on research interest
    coverstatement = yaml_contents['coverstatement'] + "\\vspace{0.25em}\n\n\\textbf{Keywords: }\\it "
    for line in yaml_contents['keywords']:
        coverstatement = coverstatement + line +", "
    coverstatement = coverstatement[:-2]+"."


    f_cv = open("gen/cv." + ext, 'w+')
    f_cv.write(env.get_template("home_tmpl." + ext).render(
        name = yaml_contents['name'],
        phone = yaml_contents['phone'],
        email = yaml_contents['email'],
        site = yaml_contents['site'],
        github = yaml_contents['github'],
        currentposition = yaml_contents['currentposition'],
        coverstatement = coverstatement,
        body1 = body1,
        body2 = body2,
        body3 = body3,
        today = date.today().strftime("%d/%m/%y"))
      )
    f_cv.close()

generate("tex")

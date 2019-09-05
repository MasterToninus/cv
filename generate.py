#!/usr/bin/env python3
#
# Generates LaTeX, markdown, and plaintext copies of my CV.
#
# Vittorio Erba <site>
# 2019.09.03

import yaml
import sys

from datetime import date
from jinja2 import Environment, FileSystemLoader

env = Environment(
        loader=FileSystemLoader("tmpl"),
        block_start_string      ='~{',
        block_end_string        ='}~',
        variable_start_string   ='~{{', 
        variable_end_string     ='}}~',
        comment_start_string    ="~{#", 
        comment_end_string      ="#}~"
        )

f = open("cv.yaml", 'r')
yaml_contents = yaml.load(f)
f.close()

def generate(ext):
    body1 = ""
    body2 = ""
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
        else:
            body2 += parsed

    f_cv = open("gen/cv." + ext, 'w')
    f_cv.write(env.get_template("home_tmpl." + ext).render(
        name = yaml_contents['name'],
        phone = yaml_contents['phone'],
        email = yaml_contents['email'],
        site = yaml_contents['site'],
        body1 = body1,
        body2 = body2,
        today = date.today().strftime("%B %d, %Y"))
      )
    f_cv.close()

generate("tex")

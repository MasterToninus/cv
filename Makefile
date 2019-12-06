all: gen/cv.pdf

gen/cv.tex: data/cv.yaml generate.py \
	tmpl/home_tmpl.tex tmpl/section_tmpl.tex
	./generate.py

gen/cv.pdf: gen/cv.tex
	cd gen && \
	latexmk --pdf  && \
	latexmk -c

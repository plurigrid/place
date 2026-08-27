# labfinder

Ranks labs (PI × institution) for a free-text project description and **emits a
forester tree**. A ranking is forest content, not a web widget — the output is
`.tree` source you commit, so the site stays static XML + XSLT.

One file. No dune, no libraries, no build step:

    ocaml labfinder.ml "prion proteomics sudden unexplained death" \
      --facet "prion protein misfolding" \
      --facet "proteomics mass spectrometry brain" \
      --facet "sudden unexplained death" \
      --facet "neuropathology postmortem" \
      --since 2018 --n 10 > ../../../trees/lf-0001.tree

It also compiles if you want a binary: `ocamlc labfinder.ml -o labfinder` (or
`ocamlopt`). Nothing else is required — the JSON reader is in the file.

Rationale and scoring live in `trees/bcf-0074.tree`; this file does not restate
them. Sample output: `trees/lf-0001.tree`.

OpenAlex is HTTPS-only, so the raw GET is delegated to `curl`; JSON parsing,
scoring, forester-escaping and emission are all in `labfinder.ml`.

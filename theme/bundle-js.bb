#!/usr/bin/env bb
;; Bundle forester.js via esbuild

(require '[babashka.process :refer [shell]])

(shell "npm" "install")
(shell "./node_modules/.bin/esbuild" "--minify" "--bundle"
  "javascript-source/forester.js" "--outfile=forester.js")

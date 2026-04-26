#!/usr/bin/env bb
;; Serve the forester output on localhost:8080

(require '[babashka.process :refer [shell]])

(println "Open http://localhost:8080/index.xml ...")
(println)
(shell "python3" "-m" "http.server" "-d" "output" "8080")

#!/usr/bin/env bb
;; Build the bci.horse forester site
;; Rooted at horse-0001 (BCI Factory)

(require '[babashka.process :refer [shell]]
         '[babashka.fs :as fs])

(def script-dir (str (fs/parent (fs/absolutize *file*))))
(fs/set-cwd script-dir)

(System/setProperty "user.dir" script-dir)

(let [config "bci-forest.toml"
      tree-count (fn [dir pattern]
                   (count (fs/glob dir pattern {:hidden false})))]
  (println "Building bci.horse forest...")
  (println (format "  Root: horse-0001 (BCI Factory)"))
  (println (format "  Trees: %d total"
    (+ (tree-count "trees" "*.tree")
       (tree-count "localcharts/forest/trees" "*.tree")
       (tree-count "bci/stages" "*.tree"))))
  (println (format "  BCI trees: %d" (tree-count "trees" "bci-*.tree")))
  (println (format "  Horse trees: %d" (tree-count "localcharts/forest/trees" "horse-*.tree")))

  (shell {:dir script-dir :extra-env {"FORESTER_CONFIG" config}}
    "./forester" "build" "--config" config)

  (println "Output in output/")
  (println "Deploy: rsync -avz output/ bci.horse:/var/www/bci.horse/"))

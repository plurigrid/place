#!/usr/bin/env bb
;; Watch trees/ for changes and rebuild

(require '[babashka.process :refer [shell]]
         '[babashka.fs :as fs])

(def watch-dir "trees")
(def build-cmd ["./forester" "build"])

(defn build! []
  (try
    (apply shell build-cmd)
    (catch Exception e
      (println "Build error:" (.getMessage e)))))

;; Initial build
(build!)

(cond
  (fs/which "fswatch")
  (do
    (println "Using fswatch to monitor changes...")
    (let [p (shell {:out :inherit :err :inherit}
              "fswatch" "-o" "-e" ".*" "-i" "\\.tree$"
              "--event" "Created" "--event" "Updated"
              "--event" "Removed" "--event" "MovedFrom"
              "--event" "MovedTo" watch-dir)]
      ;; fswatch -o outputs a count per batch; rebuild on each
      (build!)))

  (fs/which "inotifywait")
  (do
    (println "Using inotifywait to monitor changes...")
    (loop []
      (shell "inotifywait" "-e" "modify,create,delete,move" "-r" watch-dir)
      (build!)
      (recur)))

  :else
  (do
    (println "No fswatch or inotifywait. Polling every 2s...")
    (let [snapshot (atom (into {} (map (fn [f] [(str f) (fs/last-modified-time f)])
                                       (fs/glob watch-dir "**/*.tree"))))]
      (loop []
        (Thread/sleep 2000)
        (let [current (into {} (map (fn [f] [(str f) (fs/last-modified-time f)])
                                     (fs/glob watch-dir "**/*.tree")))]
          (when (not= current @snapshot)
            (reset! snapshot current)
            (build!)))
        (recur)))))

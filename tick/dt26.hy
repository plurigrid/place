;; DT-26 — 26-letter color distinguishability 2AFC trial loop
;; A-Z → SplitMix64 hash → hex color → CIEDE2000 ΔE metric
;; Emits trit per trial to ZMQ :7069 for basilisp arena merge.

(import time json zmq
        [colormath.color_objects [sRGBColor LabColor]]
        [colormath.color_conversions [convert_color]]
        [colormath.color_diff [delta_e_cie2000]])

(setv MASK64 0xFFFFFFFFFFFFFFFF)

(defn splitmix64 [seed]
  (setv z (& (+ seed 0x9E3779B97F4A7C15) MASK64))
  (setv z (& (* (^ z (>> z 30)) 0xBF58476D1CE4E5B9) MASK64))
  (setv z (& (* (^ z (>> z 27)) 0x94D049BB133111EB) MASK64))
  (^ z (>> z 31)))

(defn theory-color [letter]
  "A-Z → #rrggbb"
  (setv h (splitmix64 (ord letter)))
  (setv r (& h 0xFF))
  (setv g (& (>> h 8) 0xFF))
  (setv b (& (>> h 16) 0xFF))
  #(r g b))

(defn ciede2000 [c1 c2]
  (setv l1 (convert_color (sRGBColor #* c1 :is_upscaled True) LabColor))
  (setv l2 (convert_color (sRGBColor #* c2 :is_upscaled True) LabColor))
  (delta_e_cie2000 l1 l2))

(defn trial [ctx left-letter right-letter target-letter]
  "Show two swatches, user picks which matches target. Return trit + latency."
  (setv t0 (time.monotonic))
  ;; render hook — Textual brick tile fills with theory-color
  (setv lc (theory-color left-letter))
  (setv rc (theory-color right-letter))
  (setv tc (theory-color target-letter))
  (setv de-left (ciede2000 lc tc))
  (setv de-right (ciede2000 rc tc))
  ;; placeholder: real impl reads keypress via Textual on_key
  (setv correct (if (< de-left de-right) "left" "right"))
  (setv response (input (.format "L[{}] R[{}] T[{}]> " left-letter right-letter target-letter)))
  (setv latency-ms (* 1000 (- (time.monotonic) t0)))
  (setv ok (= response correct))
  (setv trit (cond [(and ok (< (min de-left de-right) 2.3)) 1]   ; hit at JND
                   [ok 0]                                          ; hit easy
                   [True -1]))                                     ; miss
  {"t" (time.time) "trit" trit "latency_ms" latency-ms
   "L" left-letter "R" right-letter "target" target-letter
   "de_L" de-left "de_R" de-right "correct" ok})

(defn run [[n-trials 200]]
  (setv ctx (zmq.Context))
  (setv sock (.socket ctx zmq.PUB))
  (.bind sock "tcp://127.0.0.1:7069")
  (import random)
  (setv letters "ABCDEFGHIJKLMNOPQRSTUVWXYZ")
  (for [i (range n-trials)]
    (setv [L R T] (random.sample letters 3))
    (setv ev (trial ctx L R T))
    (.send_string sock (json.dumps ev))
    (print (.format "{}/{}  trit={}  ΔE_L={:.2f} ΔE_R={:.2f}  {}ms"
                    (+ i 1) n-trials (get ev "trit")
                    (get ev "de_L") (get ev "de_R")
                    (int (get ev "latency_ms"))))))

(when (= __name__ "__main__")
  (run))

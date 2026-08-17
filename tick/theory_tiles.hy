;; Render 26 catcolab theories × 3 objects as a brick diagram grid.
;; 26 parallel bricks (one per theory), each a seq of 3 object tiles.
;; Flow = all 78 tiles labeled; interrupt gate fires only when full.

(import [vibesnipe.widgets.brick [Brick BrickSeq BrickPar BrickId is-flowing]])

(setv THEORIES
  {"A" #("Arena"        #("play" "coplay" "merge")     "crdt-converge")
   "B" #("Blume-Capel"  #("spin-1" "spin0" "spin+1")   "gf3-sum")
   "C" #("Cohomology"   #("site" "sheaf" "descent")    "cech-closed")
   "D" #("DOTS"         #("double" "open" "tracing")   "para-lens-6")
   "E" #("Eff"          #("handler" "op" "cont")       "neg-neg-top")
   "F" #("Fisher-Rao"   #("metric" "geodesic" "kl")    "info-monotone")
   "G" #("Glimpse"      #("epoch" "sync" "emit")       "temporal-align")
   "H" #("Hedges-Herold" #("seq" "par" "id")           "brick-flow")
   "I" #("IES"          #("olog" "000" "session")      "type-safe")
   "J" #("Julia-Gay"    #("hash" "color" "mac")        "splitmix-det")
   "K" #("Kuramoto"     #("phase" "coupling" "sync")   "order-param")
   "L" #("Lens"         #("get" "put" "law")           "put-get")
   "M" #("Majj"         #("cell" "merge" "ord")        "lattice-join")
   "N" #("Nashator"     #("player" "payoff" "eq")      "best-response")
   "O" #("Open-Games"   #("play" "coplay" "best")      "subgame-perfect")
   "P" #("Propagator"   #("cell" "merge" "contra")     "monotone")
   "Q" #("Qualia-Market" #("bid" "ask" "clear")        "budget-balance")
   "R" #("Rewriting"    #("lhs" "rhs" "strategy")      "confluence")
   "S" #("Sheaf"        #("cover" "section" "glue")    "parrot-fixed")
   "T" #("Topos"        #("obj" "arrow" "subobj")      "heyting")
   "U" #("USS"          #("entropy" "mc" "quantize")   "second-law")
   "V" #("Vertex"       #("model" "pipeline" "rag")    "kfp-dag")
   "W" #("Wiring"       #("box" "wire" "nerve")        "nerve-commute")
   "X" #("X-acsets"     #("schema" "instance" "hom")   "mural")
   "Y" #("Y-combinator" #("fix" "aseity" "loop")       "y-squared")
   "Z" #("Z2-graded"    #("even" "odd" "susy")         "aperiodic")})

(defn theory-row [letter]
  "One theory → BrickSeq of 3 object tiles."
  (setv [name objs inv] (get THEORIES letter))
  (BrickSeq #* (lfor o objs (Brick (.format "{}:{}" letter o)))))

(defn catcolab-grid []
  "All 26 theories → BrickPar. Flows iff all 78 tiles labeled."
  (BrickPar #* (lfor l "ABCDEFGHIJKLMNOPQRSTUVWXYZ" (theory-row l))))

(defn interrupt-gate? []
  "Per the flowing rule: interrupts allowed only when full grid flows."
  (is-flowing (catcolab-grid)))

(when (= __name__ "__main__")
  (setv grid (catcolab-grid))
  (print (.format "78 tiles, flowing={}" (is-flowing grid)))
  (print (.format "interrupt allowed: {}" (interrupt-gate?))))

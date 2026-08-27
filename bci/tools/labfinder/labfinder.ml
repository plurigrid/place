(* labfinder — rank labs (PI x institution) for a project description and emit
   the result as a forester tree.

   Plain OCaml. No dune, no libraries, no build step:

     ocaml labfinder.ml "<project>" --facet "..." --since 2018 --n 10 > out.tree

   The output is .tree source. A ranking is forest content, not a web widget,
   so the site stays static XML + XSLT with nothing to execute.

   OpenAlex is HTTPS-only; the raw GET is delegated to curl. Everything else —
   JSON parsing, scoring, forester escaping, emission — is in this file. *)

let api = "https://api.openalex.org"
let mailto = "yuzu@plurigrid.com"

(* ---------- a small JSON reader (stdlib only) ---------------------------- *)
type json =
  | Null
  | Bool of bool
  | Num of float
  | Str of string
  | Arr of json list
  | Obj of (string * json) list

exception Bad of string

let parse (s : string) : json =
  let n = String.length s in
  let i = ref 0 in
  let peek () = if !i < n then s.[!i] else '\000' in
  let adv () = incr i in
  let rec ws () =
    if !i < n then
      match s.[!i] with ' ' | '\t' | '\n' | '\r' -> adv (); ws () | _ -> ()
  in
  let lit w v = 
    if !i + String.length w <= n && String.sub s !i (String.length w) = w
    then (i := !i + String.length w; v)
    else raise (Bad "literal")
  in
  let hex c =
    match c with
    | '0' .. '9' -> Char.code c - 48
    | 'a' .. 'f' -> Char.code c - 87
    | 'A' .. 'F' -> Char.code c - 55
    | _ -> raise (Bad "hex")
  in
  (* encode a code point as UTF-8 so titles keep their accents and dashes *)
  let utf8 b cp =
    if cp < 0x80 then Buffer.add_char b (Char.chr cp)
    else if cp < 0x800 then begin
      Buffer.add_char b (Char.chr (0xC0 lor (cp lsr 6)));
      Buffer.add_char b (Char.chr (0x80 lor (cp land 0x3F)))
    end else if cp < 0x10000 then begin
      Buffer.add_char b (Char.chr (0xE0 lor (cp lsr 12)));
      Buffer.add_char b (Char.chr (0x80 lor ((cp lsr 6) land 0x3F)));
      Buffer.add_char b (Char.chr (0x80 lor (cp land 0x3F)))
    end else begin
      Buffer.add_char b (Char.chr (0xF0 lor (cp lsr 18)));
      Buffer.add_char b (Char.chr (0x80 lor ((cp lsr 12) land 0x3F)));
      Buffer.add_char b (Char.chr (0x80 lor ((cp lsr 6) land 0x3F)));
      Buffer.add_char b (Char.chr (0x80 lor (cp land 0x3F)))
    end
  in
  let string_ () =
    adv ();                                   (* opening quote *)
    let b = Buffer.create 32 in
    let rec go () =
      if !i >= n then raise (Bad "eof in string");
      match s.[!i] with
      | '"' -> adv (); Buffer.contents b
      | '\\' ->
          adv ();
          (match peek () with
           | 'n' -> Buffer.add_char b '\n'; adv ()
           | 't' -> Buffer.add_char b '\t'; adv ()
           | 'r' -> Buffer.add_char b '\r'; adv ()
           | 'b' -> Buffer.add_char b '\b'; adv ()
           | 'f' -> Buffer.add_char b '\012'; adv ()
           | 'u' ->
               adv ();
               let cp = ref 0 in
               for _ = 1 to 4 do cp := (!cp * 16) + hex (peek ()); adv () done;
               (* surrogate pair *)
               if !cp >= 0xD800 && !cp <= 0xDBFF && !i + 1 < n
                  && s.[!i] = '\\' && s.[!i + 1] = 'u' then begin
                 i := !i + 2;
                 let lo = ref 0 in
                 for _ = 1 to 4 do lo := (!lo * 16) + hex (peek ()); adv () done;
                 utf8 b (0x10000 + ((!cp - 0xD800) * 0x400) + (!lo - 0xDC00))
               end else utf8 b !cp
           | c -> Buffer.add_char b c; adv ());
          go ()
      | c -> Buffer.add_char b c; adv (); go ()
    in
    go ()
  in
  let rec value () =
    ws ();
    match peek () with
    | '"' -> Str (string_ ())
    | '{' ->
        adv (); ws ();
        if peek () = '}' then (adv (); Obj [])
        else
          let acc = ref [] in
          let rec members () =
            ws ();
            let k = string_ () in
            ws ();
            if peek () <> ':' then raise (Bad "expected :");
            adv ();
            let v = value () in
            acc := (k, v) :: !acc;
            ws ();
            match peek () with
            | ',' -> adv (); members ()
            | '}' -> adv ()
            | _ -> raise (Bad "expected , or }")
          in
          members (); Obj (List.rev !acc)
    | '[' ->
        adv (); ws ();
        if peek () = ']' then (adv (); Arr [])
        else
          let acc = ref [] in
          let rec elems () =
            let v = value () in
            acc := v :: !acc;
            ws ();
            match peek () with
            | ',' -> adv (); elems ()
            | ']' -> adv ()
            | _ -> raise (Bad "expected , or ]")
          in
          elems (); Arr (List.rev !acc)
    | 't' -> lit "true" (Bool true)
    | 'f' -> lit "false" (Bool false)
    | 'n' -> lit "null" Null
    | _ ->
        let st = !i in
        let ok c =
          match c with '0' .. '9' | '-' | '+' | '.' | 'e' | 'E' -> true | _ -> false
        in
        while !i < n && ok s.[!i] do adv () done;
        if !i = st then raise (Bad "number");
        Num (float_of_string (String.sub s st (!i - st)))
  in
  let v = value () in
  v

let mem k = function Obj l -> (try List.assoc k l with Not_found -> Null) | _ -> Null
let str = function Str s -> s | _ -> ""
let num = function Num f -> f | _ -> 0.0
let int_ = function Num f -> int_of_float f | _ -> 0
let list_ = function Arr l -> l | _ -> []

(* ---------- shell out for the HTTPS GET --------------------------------- *)
let read_file p =
  let ic = open_in_bin p in
  let len = in_channel_length ic in
  let s = really_input_string ic len in
  close_in ic; s

let shell_capture cmd =
  let tmp = Filename.temp_file "labfinder" ".out" in
  let rc = Sys.command (cmd ^ " > " ^ Filename.quote tmp ^ " 2>/dev/null") in
  let out = if Sys.file_exists tmp then read_file tmp else "" in
  (try Sys.remove tmp with _ -> ());
  (rc, out)

let urlencode s =
  let b = Buffer.create (String.length s * 3) in
  String.iter
    (fun c ->
      match c with
      | 'A' .. 'Z' | 'a' .. 'z' | '0' .. '9' | '-' | '_' | '.' | '~' -> Buffer.add_char b c
      | ' ' -> Buffer.add_char b '+'
      | c -> Buffer.add_string b (Printf.sprintf "%%%02X" (Char.code c)))
    s;
  Buffer.contents b

let get_json path params =
  let q =
    ("mailto", mailto) :: params
    |> List.map (fun (k, v) -> k ^ "=" ^ urlencode v)
    |> String.concat "&"
  in
  let url = Printf.sprintf "%s/%s?%s" api path q in
  let cmd =
    "curl -sS --max-time 60 --retry 3 --retry-delay 2 " ^ Filename.quote url
  in
  let _, body = shell_capture cmd in
  try parse body with _ -> Obj []

let this_year =
  let _, out = shell_capture "date +%Y" in
  try int_of_string (String.trim out) with _ -> 2026

(* ---------- scoring: senior/corresponding author is the PI --------------- *)
let w_last = 1.0 and w_corr = 1.0 and w_first = 0.35 and w_mid = 0.12
let both_bonus = 1.15
let half_life = 3.0

let recency y = if y = 0 then 0.3 else Float.pow 0.5 (float_of_int (this_year - y) /. half_life)

let pos_weight a =
  let p = str (mem "author_position" a) in
  let corr = match mem "is_corresponding" a with Bool b -> b | _ -> false in
  if p = "last" && corr then both_bonus
  else if p = "last" then w_last
  else if corr then w_corr
  else if p = "first" then w_first
  else w_mid

(* ---------- forester escaping (each of these is a fatal parse error) ------ *)
let escape s =
  let b = Buffer.create (String.length s + 8) in
  let depth = ref 0 in
  String.iter
    (fun c ->
      match c with
      | '%' -> Buffer.add_string b "\\%"    (* comments out the rest of the line *)
      | '\\' -> Buffer.add_char b '/'       (* a stray \word parses as a command *)
      | '{' | '}' -> Buffer.add_char b ' '  (* unbalanced braces are fatal *)
      | '#' -> Buffer.add_char b ' '        (* #{ opens math mode *)
      | '(' -> incr depth; Buffer.add_char b '('
      | ')' -> if !depth > 0 then (decr depth; Buffer.add_char b ')') else Buffer.add_char b ' '
      | c -> Buffer.add_char b c)
    s;
  Buffer.contents b ^ String.make !depth ')'

type lab = {
  mutable name : string;
  mutable orcid : string;
  mutable score : float;
  mutable n : int;
  mutable senior : int;
  mutable years : int list;
  mutable insts : (string * int) list;
  mutable facets : string list;
  mutable papers : (int * string) list;
}

let () =
  let argv = Array.to_list Sys.argv |> List.tl in
  let facets = ref [] and since = ref (this_year - 8) and topn = ref 10 and q = ref [] in
  let rec go = function
    | "--facet" :: v :: r -> facets := v :: !facets; go r
    | "--since" :: v :: r -> since := int_of_string v; go r
    | "--n" :: v :: r -> topn := int_of_string v; go r
    | x :: r -> q := x :: !q; go r
    | [] -> ()
  in
  go argv;
  let query = String.concat " " (List.rev !q) in
  let facets = if !facets = [] then [ query ] else List.rev !facets in

  let tbl : (string, lab) Hashtbl.t = Hashtbl.create 512 in
  let seen : (string, unit) Hashtbl.t = Hashtbl.create 4096 in
  let report = ref [] in

  List.iter
    (fun f ->
      let d =
        get_json "works"
          [ ("search", f);
            ("filter", Printf.sprintf "from_publication_date:%d-01-01,type:article" !since);
            ("per-page", "200");
            ("select", "id,display_name,publication_year,cited_by_count,relevance_score,authorships") ]
      in
      let works = list_ (mem "results" d) in
      report := (f, List.length works, int_ (mem "count" (mem "meta" d))) :: !report;
      let maxrel = List.fold_left (fun m w -> Float.max m (num (mem "relevance_score" w))) 1e-9 works in
      List.iter
        (fun w ->
          Hashtbl.replace seen (str (mem "id" w)) ();
          let rel = 0.3 +. (0.7 *. (num (mem "relevance_score" w) /. maxrel)) in
          let year = int_ (mem "publication_year" w) in
          let rc = recency year in
          List.iter
            (fun a ->
              let au = mem "author" a in
              let aid = str (mem "id" au) in
              if aid <> "" then begin
                let l =
                  match Hashtbl.find_opt tbl aid with
                  | Some l -> l
                  | None ->
                      let l = { name = str (mem "display_name" au); orcid = str (mem "orcid" au);
                                score = 0.; n = 0; senior = 0; years = []; insts = [];
                                facets = []; papers = [] } in
                      Hashtbl.replace tbl aid l; l
                in
                let pw = pos_weight a in
                l.score <- l.score +. (pw *. rc *. rel);
                l.n <- l.n + 1;
                if not (List.mem f l.facets) then l.facets <- f :: l.facets;
                if pw >= w_last then begin
                  l.senior <- l.senior + 1;
                  if List.length l.papers < 3 then
                    l.papers <- (year, str (mem "display_name" w)) :: l.papers
                end;
                if year > 0 then l.years <- year :: l.years;
                (* OpenAlex lists consortia and funders next to the real
                   employer, so count affiliations and take the mode *)
                List.iter
                  (fun i ->
                    let dn = str (mem "display_name" i) in
                    if dn <> "" then
                      l.insts <-
                        (match List.assoc_opt dn l.insts with
                         | Some c -> (dn, c + 1) :: List.remove_assoc dn l.insts
                         | None -> (dn, 1) :: l.insts))
                  (list_ (mem "institutions" a))
              end)
            (list_ (mem "authorships" w)))
        works;
      ignore (Sys.command "sleep 0.2"))
    facets;

  let rows =
    Hashtbl.fold (fun _ l acc -> l :: acc) tbl []
    |> List.filter (fun l -> l.senior >= 2 && l.n >= 3)
    |> List.map (fun l ->
           (* the point: the best lab is at the INTERSECTION of the facets *)
           l.score <- l.score *. Float.pow (float_of_int (List.length l.facets)) 1.5; l)
    |> List.sort (fun a b -> compare b.score a.score)
    |> List.filteri (fun i _ -> i < !topn)
  in

  let p = Printf.printf in
  p "\\title{labfinder: %s}\n" (escape query);
  p "\\taxon{lab ranking}\n\\author{monaduck1069}\n";
  p "\\meta{generated-by}{bci/tools/labfinder/labfinder.ml}\n";
  p "\\meta{source}{OpenAlex}\n\\meta{since}{%d}\n" !since;
  p "\\meta{corpus}{%d unique works}\n\n" (Hashtbl.length seen);
  p "\\p{Labs ranked by principal investigator for the project \\em{%s}. " (escape query);
  p "Score sums authorship weight times recency times relevance, then multiplies \
     by facets matched to the power 1.5 — the best lab sits at the intersection \
     of the project's facets, not at the most-cited lab touching one of them.}\n\n";
  p "\\p{Facets searched:}\n\\ul{\n";
  List.iter (fun (f, g, t) -> p "  \\li{%s — %d of %d works}\n" (escape f) g t) (List.rev !report);
  p "}\n\n\\ol{\n";
  List.iter
    (fun l ->
      let inst =
        match List.sort (fun (_, a) (_, b) -> compare b a) l.insts with
        | (i, _) :: _ -> i | [] -> "?"
      in
      let yrs =
        match l.years with
        | [] -> "?"
        | ys -> Printf.sprintf "%d–%d" (List.fold_left min 9999 ys) (List.fold_left max 0 ys)
      in
      p "  \\li{\\strong{%s} — %s. Score %.2f across %d facet(s); %d on-topic works, \
         %d as senior author; active %s."
        (escape l.name) (escape inst) l.score (List.length l.facets) l.n l.senior yrs;
      List.iter (fun (y, t) -> p " \\p{%d — %s}" y (escape t)) (List.rev l.papers);
      if l.orcid <> "" then p " \\p{ORCID: %s}" (escape l.orcid);
      p "}\n")
    rows;
  p "}\n"

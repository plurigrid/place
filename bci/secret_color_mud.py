#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import random
import re
import textwrap
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from statistics import mean


MASK64 = 0xFFFFFFFFFFFFFFFF
DISPLAY_WIDTH = 94
LINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
WORD_RE = re.compile(r"[a-z0-9]+")
STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "in",
    "into",
    "is",
    "it",
    "its",
    "of",
    "on",
    "or",
    "that",
    "the",
    "their",
    "this",
    "to",
    "via",
    "with",
}
BRAIN_EFFECTS = {
    "focus": ("Precision", "Reliable traversal and steady drills."),
    "flow": ("Splash", "Navigation previews an extra thematic branch."),
    "alert": ("Adrenaline", "Correct drills are worth a bonus point."),
    "rest": ("Zen", "Wrong drills do not cost score."),
    "fatigue": ("Wild", "Travel can drift into a nearby linked room."),
}
QUEST_ROOMS = {
    "bcf-0019": "bci.blue",
    "bcf-0020": "bci.red",
    "bcf-0021": "bci.place",
}


@dataclass(frozen=True)
class SecretColor:
    hex_color: str
    brain_state: str
    valence: float


@dataclass(frozen=True)
class CytonEpoch:
    index: int
    brain_state: str
    valence: float
    energy: float
    valid_fraction: float
    samples: int


@dataclass
class Room:
    id: str
    title: str
    summary: str
    details: list[str]
    links: list[str]
    exits: list[str] = field(default_factory=list)
    tokens: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class DrillCard:
    key: str
    prompt: str
    answer_id: str
    answer_title: str
    keywords: set[str]


def splitmix64(value: int) -> int:
    value = (value + 0x9E3779B97F4A7C15) & MASK64
    value = ((value ^ (value >> 30)) * 0xBF58476D1CE4E5B9) & MASK64
    value = ((value ^ (value >> 27)) * 0x94D049BB133111EB) & MASK64
    return value ^ (value >> 31)


def stable_seed(text: str) -> int:
    acc = 0xCBF29CE484222325
    for byte in text.encode("utf-8"):
        acc ^= byte
        acc = (acc * 0x100000001B3) & MASK64
    return splitmix64(acc)


def quantile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    pos = (len(ordered) - 1) * q
    low = int(math.floor(pos))
    high = int(math.ceil(pos))
    if low == high:
        return ordered[low]
    weight = pos - low
    return ordered[low] * (1.0 - weight) + ordered[high] * weight


def tokenise(text: str) -> set[str]:
    return {
        word
        for word in WORD_RE.findall(text.lower())
        if len(word) > 1 and word not in STOP_WORDS
    }


def extract_braced_payloads(text: str, command: str) -> list[str]:
    token = "\\" + command + "{"
    payloads: list[str] = []
    start = 0
    while True:
        idx = text.find(token, start)
        if idx == -1:
            return payloads
        cursor = idx + len(token)
        depth = 1
        chunk: list[str] = []
        while cursor < len(text) and depth > 0:
            char = text[cursor]
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    cursor += 1
                    break
            if depth > 0:
                chunk.append(char)
            cursor += 1
        payloads.append("".join(chunk))
        start = cursor


def clean_markup(text: str) -> str:
    text = re.sub(r"(?m)^%.*$", "", text)
    text = LINK_RE.sub(r"\1", text)
    previous = None
    while previous != text:
        previous = text
        text = re.sub(r"(?:##|#)\{([^{}]*)\}", r"\1", text)
        text = re.sub(r"\\[a-zA-Z@]+(?:\[[^\]]*\])?\{([^{}]*)\}", r"\1", text)
    text = re.sub(r"\\[a-zA-Z@]+", "", text)
    text = text.replace("~", " ")
    text = text.replace("—", " — ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def wrap(text: str) -> str:
    return textwrap.fill(text, width=DISPLAY_WIDTH)


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    value = hex_color.lstrip("#")
    r, g, b = (int(value[index : index + 2], 16) for index in (0, 2, 4))
    return (r, g, b)


def swatch(hex_color: str, width: int = 6) -> str:
    r, g, b = hex_to_rgb(hex_color)
    return f"\033[48;2;{r};{g};{b}m{' ' * width}\033[0m"


def color_distance(a: SecretColor, b: SecretColor) -> float:
    ra, ga, ba = hex_to_rgb(a.hex_color)
    rb, gb, bb = hex_to_rgb(b.hex_color)
    rgb_delta = math.sqrt((ra - rb) ** 2 + (ga - gb) ** 2 + (ba - bb) ** 2)
    rgb_score = rgb_delta / math.sqrt(3 * (255**2))
    valence_score = abs(a.valence - b.valence) / 2.0
    return min(1.0, rgb_score * 0.75 + valence_score * 0.25)


def coherence(a: SecretColor, b: SecretColor) -> float:
    return 1.0 - color_distance(a, b)


def load_secret_colors(path: Path) -> tuple[list[SecretColor], dict[str, list[SecretColor]]]:
    records = json.loads(path.read_text())
    colors = [
        SecretColor(
            hex_color=record["hex_color"],
            brain_state=record["brain_state"],
            valence=float(record["valence"]),
        )
        for record in records
    ]
    by_state: dict[str, list[SecretColor]] = {}
    for color in colors:
        by_state.setdefault(color.brain_state, []).append(color)
    return colors, by_state


def load_cyton_epochs(path: Path, epoch_size: int = 250) -> list[CytonEpoch]:
    samples: list[list[float]] = []
    for line in path.read_text().splitlines():
        parts = line.split()
        if len(parts) < 9:
            continue
        row: list[float] = []
        for value in parts[1:9]:
            try:
                number = float(value)
            except ValueError:
                continue
            if abs(number) > 100000:
                continue
            row.append(number)
        samples.append(row)
    epochs_raw: list[tuple[int, float, float, float, int]] = []
    energies: list[float] = []
    biases: list[float] = []
    for offset in range(0, len(samples), epoch_size):
        chunk = samples[offset : offset + epoch_size]
        if len(chunk) < max(25, epoch_size // 5):
            continue
        values = [value for row in chunk for value in row]
        energy = mean(abs(value) for value in values) if values else 0.0
        bias = mean(values) if values else 0.0
        valid_fraction = sum(len(row) for row in chunk) / (len(chunk) * 8)
        epochs_raw.append((offset // epoch_size, energy, bias, valid_fraction, len(chunk)))
        energies.append(energy)
        biases.append(bias)
    if not epochs_raw:
        return [CytonEpoch(index=0, brain_state="focus", valence=0.0, energy=0.0, valid_fraction=1.0, samples=0)]
    q1 = quantile(energies, 0.25)
    q2 = quantile(energies, 0.50)
    q3 = quantile(energies, 0.75)
    min_bias = min(biases)
    max_bias = max(biases)
    epochs: list[CytonEpoch] = []
    for index, energy, bias, valid_fraction, sample_count in epochs_raw:
        if energy <= q1:
            state = "rest"
        elif energy <= q2:
            state = "focus"
        elif energy <= q3:
            state = "alert"
        else:
            state = "fatigue"
        valence = 0.0 if min_bias == max_bias else ((bias - min_bias) / (max_bias - min_bias)) * 2.0 - 1.0
        if valid_fraction < 0.35:
            state = "fatigue"
            valence = max(-1.0, valence - 0.25)
        epochs.append(
            CytonEpoch(
                index=index,
                brain_state=state,
                valence=round(valence, 2),
                energy=energy,
                valid_fraction=valid_fraction,
                samples=sample_count,
            )
        )
    return epochs


def load_rooms(tree_dir: Path) -> dict[str, Room]:
    rooms: dict[str, Room] = {}
    for path in sorted(tree_dir.glob("*.tree")):
        raw = path.read_text()
        titles = extract_braced_payloads(raw, "title")
        paragraphs = [clean_markup(paragraph) for paragraph in extract_braced_payloads(raw, "p")]
        details = [paragraph for paragraph in paragraphs if paragraph]
        title = clean_markup(titles[0]) if titles else path.stem
        summary = details[0] if details else title
        links = [match.group(1).strip() for match in LINK_RE.finditer(raw)]
        room = Room(
            id=path.stem,
            title=title,
            summary=summary,
            details=details[:3],
            links=links,
            tokens=tokenise(f"{title} {summary} {' '.join(details[:3])}"),
        )
        rooms[room.id] = room
    for room in rooms.values():
        seen: set[str] = set()
        exits: list[str] = []
        for link in room.links:
            if link in rooms and link != room.id and link not in seen:
                exits.append(link)
                seen.add(link)
        if not exits:
            exits = fallback_exits(room, rooms)
        room.exits = exits
    return rooms


def fallback_exits(room: Room, rooms: dict[str, Room]) -> list[str]:
    prefix = room.id.split("-")[0]
    scored: list[tuple[int, str]] = []
    for other in rooms.values():
        if other.id == room.id:
            continue
        score = len(room.tokens & other.tokens)
        if other.id.split("-")[0] == prefix:
            score += 2
        if score > 0:
            scored.append((score, other.id))
    scored.sort(key=lambda item: (-item[0], item[1]))
    return [room_id for _, room_id in scored[:6]]


def load_nblm_cards(path: Path) -> tuple[dict[str, str], list[DrillCard]]:
    data = json.loads(path.read_text())
    node_titles = {node["id"]: node["title"] for node in data.get("nodes", [])}
    cards: list[DrillCard] = []
    for index, edge in enumerate(data.get("edges", [])):
        source_title = node_titles.get(edge.get("from"))
        target_title = node_titles.get(edge.get("to"))
        if not source_title or not target_title:
            continue
        label = edge.get("via") or edge.get("theme") or "relationship"
        prompt = f"Which distillation cluster follows '{source_title}' via '{label}'?"
        cards.append(
            DrillCard(
                key=f"card-{index}",
                prompt=prompt,
                answer_id=edge["to"],
                answer_title=target_title,
                keywords=tokenise(f"{source_title} {target_title} {label}"),
            )
        )
    return node_titles, cards


class SecretColorMud:
    def __init__(self, name: str, start_room: str, workspace_root: Path, repo_root: Path) -> None:
        self.name = name
        self.workspace_root = workspace_root
        self.repo_root = repo_root
        self.colors, self.colors_by_state = load_secret_colors(workspace_root / "secret_colors.json")
        self.cyton_epochs = load_cyton_epochs(workspace_root / "cyton_recording.csv")
        self.rooms = load_rooms(repo_root / "trees")
        self.node_titles, self.cards = load_nblm_cards(workspace_root / "nblm_mindmap_distillation.json")
        if start_room not in self.rooms:
            start_room = "horse-0001" if "horse-0001" in self.rooms else sorted(self.rooms)[0]
        self.current_room_id = start_room
        self.player_color = self.colors[stable_seed(name.lower()) % len(self.colors)]
        self.turn_index = 0
        self.score = 0
        self.visits = [self.current_room_id]
        self.witnessed: set[str] = set()
        self.cleared_cards: set[str] = set()
        self.random = random.Random(stable_seed(f"{name}:{start_room}"))
        self.aura_cache: dict[tuple[str, int], tuple[SecretColor, CytonEpoch]] = {}
        self.journal: deque[str] = deque(maxlen=12)
        self.triad_complete = False
        self.message = ""
        self.set_message("Ride the forester graph. Close the gap between name-color and brain-color.")

    def room(self, room_id: str | None = None) -> Room:
        return self.rooms[room_id or self.current_room_id]

    def current_epoch(self) -> CytonEpoch:
        return self.cyton_epochs[self.turn_index % len(self.cyton_epochs)]

    def room_aura(self, room_id: str | None = None) -> tuple[SecretColor, CytonEpoch]:
        room_key = room_id or self.current_room_id
        epoch = self.current_epoch()
        cache_key = (room_key, epoch.index)
        if cache_key in self.aura_cache:
            return self.aura_cache[cache_key]
        palette = self.colors_by_state.get(epoch.brain_state) or self.colors
        ranked = sorted(
            palette,
            key=lambda color: (
                abs(color.valence - epoch.valence),
                stable_seed(f"{room_key}:{color.hex_color}") % 997,
            ),
        )
        bucket = ranked[: max(1, min(64, len(ranked)))]
        color = bucket[stable_seed(f"{room_key}:{epoch.index}") % len(bucket)]
        self.aura_cache[cache_key] = (color, epoch)
        return color, epoch

    def current_exits(self) -> list[str]:
        exits = list(self.room().exits)
        aura, _ = self.room_aura()
        if aura.brain_state == "flow":
            preview: list[str] = []
            for exit_id in exits[:2]:
                preview.extend(self.rooms[exit_id].exits[:2])
            for extra in preview:
                if extra != self.current_room_id and extra not in exits:
                    exits.append(extra)
        return exits[:10]

    def rider_coherence(self) -> float:
        color, _ = self.room_aura()
        return coherence(self.player_color, color)

    def witness_threshold(self) -> float:
        aura, _ = self.room_aura()
        adjustment = {
            "flow": -0.03,
            "focus": 0.0,
            "alert": 0.02,
            "rest": -0.01,
            "fatigue": 0.05,
        }.get(aura.brain_state, 0.0)
        return max(0.45, min(0.85, 0.58 + adjustment))

    def award_witness(self, bonus: int = 2) -> bool:
        if self.current_room_id in self.witnessed:
            return False
        if self.rider_coherence() < self.witness_threshold():
            return False
        self.witnessed.add(self.current_room_id)
        self.score += bonus
        return True

    def shortest_path(self, start: str, goal: str) -> list[str]:
        if start == goal:
            return [start]
        frontier: deque[list[str]] = deque([[start]])
        seen = {start}
        while frontier:
            path = frontier.popleft()
            current = path[-1]
            for next_room in self.rooms[current].exits:
                if next_room in seen:
                    continue
                next_path = path + [next_room]
                if next_room == goal:
                    return next_path
                seen.add(next_room)
                frontier.append(next_path)
        return []

    def search_rooms(self, query: str, limit: int = 8) -> list[Room]:
        query = query.strip().lower()
        if not query:
            return []
        query_tokens = tokenise(query)
        ranked: list[tuple[int, Room]] = []
        for room in self.rooms.values():
            score = 0
            if query in room.id.lower():
                score += 8
            if query in room.title.lower():
                score += 6
            if query in room.summary.lower():
                score += 3
            if query_tokens:
                score += 2 * len(query_tokens & room.tokens)
            if score > 0:
                ranked.append((score, room))
        ranked.sort(key=lambda item: (-item[0], item[1].id))
        return [room for _, room in ranked[:limit]]

    def set_message(self, message: str) -> None:
        self.message = message
        self.journal.appendleft(message)

    def quest_completion_count(self) -> int:
        return sum(1 for room_id in QUEST_ROOMS if room_id in self.witnessed)

    def quest_status(self) -> list[tuple[str, str, bool, int | str]]:
        status: list[tuple[str, str, bool, int | str]] = []
        for room_id, label in QUEST_ROOMS.items():
            path = self.shortest_path(self.current_room_id, room_id)
            hops: int | str = max(0, len(path) - 1) if path else "?"
            status.append((room_id, label, room_id in self.witnessed, hops))
        return status

    def close_triads_if_ready(self) -> str:
        if self.triad_complete:
            return ""
        if self.quest_completion_count() != len(QUEST_ROOMS):
            return ""
        self.triad_complete = True
        self.score += 5
        return " Triadic circuit closed: +5."

    def best_targets(self, limit: int = 5) -> list[tuple[float, int, str, float]]:
        ranked: list[tuple[float, int, str, float]] = []
        for room_id, room in self.rooms.items():
            path = self.shortest_path(self.current_room_id, room_id)
            if not path:
                continue
            hops = max(0, len(path) - 1)
            aura, _ = self.room_aura(room_id)
            coherence_value = coherence(self.player_color, aura)
            score = coherence_value - (0.03 * hops)
            if room_id in QUEST_ROOMS:
                score += 0.15
            if room_id in self.witnessed:
                score -= 0.25
            if room_id == self.current_room_id and room_id in self.witnessed:
                score -= 0.25
            if "rider" in room.tokens or "game" in room.tokens:
                score += 0.04
            ranked.append((score, hops, room_id, coherence_value))
        ranked.sort(key=lambda item: (-item[0], item[1], item[2]))
        return ranked[:limit]

    def clear(self) -> None:
        print("\033[2J\033[H", end="")

    def pause(self) -> None:
        input("\nPress Enter to continue...")

    def render(self) -> None:
        self.clear()
        room = self.room()
        aura, epoch = self.room_aura()
        effect_name, effect_desc = BRAIN_EFFECTS.get(aura.brain_state, ("Unknown", "No effect"))
        print("HORSE x NBLM SECRET COLOR MUD")
        print("=" * DISPLAY_WIDTH)
        print(
            f"Rider: {self.name}   Score: {self.score:+d}   Witnessed: {len(self.witnessed)}   "
            f"Steps: {len(self.visits) - 1}"
        )
        quest_line = f"Triad quest: {self.quest_completion_count()}/{len(QUEST_ROOMS)}"
        if self.triad_complete:
            quest_line += " complete"
        print(quest_line)
        print(
            f"Ambient Cyton epoch: {epoch.index + 1}/{len(self.cyton_epochs)}   "
            f"State: {epoch.brain_state}   Valence: {epoch.valence:+.2f}   "
            f"Valid: {epoch.valid_fraction:>5.1%}"
        )
        print(
            f"Name-color  {swatch(self.player_color.hex_color)} {self.player_color.hex_color} "
            f"{self.player_color.brain_state}/{self.player_color.valence:+.2f}"
        )
        print(
            f"Brain-color {swatch(aura.hex_color)} {aura.hex_color} "
            f"{aura.brain_state}/{aura.valence:+.2f}   Coherence: {self.rider_coherence():.1%}"
        )
        print(f"Effect: {effect_name} — {effect_desc}")
        print(f"Witness window: {self.rider_coherence():.1%} / {self.witness_threshold():.1%}")
        print()
        print(f"{room.id} — {room.title}")
        print(wrap(room.summary))
        if room.id in self.witnessed:
            print("Witness status: stabilized.")
        print()
        print("Exits")
        print("-" * DISPLAY_WIDTH)
        exits = self.current_exits()
        if not exits:
            print("No exits resolved. Use `map` to inspect nearby trees.")
        for index, exit_id in enumerate(exits, start=1):
            exit_room = self.rooms[exit_id]
            exit_aura, _ = self.room_aura(exit_id)
            marker = "*" if exit_id in self.witnessed else " "
            print(
                f"{index:>2}.{marker} {exit_room.id:<11} {swatch(exit_aura.hex_color, 3)} "
                f"{exit_room.title[:52]}"
            )
        print()
        print(wrap(self.message))
        print(
            "Commands: [number|room-id] move, d drill, w witness, r resonate, "
            "s <query> search, route <room>, go <room>, p status, l look, m map, t trace, h help, q quit"
        )

    def help_panel(self) -> None:
        self.clear()
        lines = [
            "The world graph comes from horse forester trees.",
            "Room aura comes from secret_colors.json, steered by Cyton-derived ambient epochs.",
            "Drills come from nblm_mindmap_distillation.json.",
            "",
            "focus: steady traversal",
            "alert: correct drill = +2 score",
            "rest: wrong drill does not reduce score",
            "fatigue: 15% chance to drift to another linked room on travel",
            "flow: reveals an extra thematic branch when present",
            "",
            "witness: stabilize the current room when coherence clears the witness window",
            "resonate: advance to the next Cyton epoch without moving",
            "search <query>: find matching rooms by id, title, and summary",
            "route <room-id>: shortest linked path from the current room",
            "go <room-id>: follow the shortest linked path automatically",
            "status: show triad quest progress, recommendations, and recent events",
        ]
        print("HELP")
        print("=" * DISPLAY_WIDTH)
        for line in lines:
            print(wrap(line) if line else "")
        self.pause()

    def look_panel(self) -> None:
        self.clear()
        room = self.room()
        print(f"{room.id} — {room.title}")
        print("=" * DISPLAY_WIDTH)
        for paragraph in room.details:
            print(wrap(paragraph))
            print()
        linked = ", ".join(room.exits[:12]) or "none"
        print(f"Coherence: {self.rider_coherence():.1%}")
        print(f"Witness threshold: {self.witness_threshold():.1%}")
        print(f"Linked rooms: {linked}")
        self.pause()

    def map_panel(self) -> None:
        self.clear()
        room = self.room()
        print("LOCAL MAP")
        print("=" * DISPLAY_WIDTH)
        print(f"Current room: {room.id} — {room.title}")
        print()
        for exit_id in self.current_exits():
            exit_room = self.rooms[exit_id]
            second_hop = ", ".join(self.rooms[target].id for target in exit_room.exits[:3]) or "none"
            marker = "*" if exit_id in self.witnessed else "-"
            print(f"{marker} {exit_room.id} — {exit_room.title}")
            print(f"    next: {second_hop}")
        self.pause()

    def trace_panel(self) -> None:
        self.clear()
        print("CYTON TRACE")
        print("=" * DISPLAY_WIDTH)
        current_index = self.turn_index % len(self.cyton_epochs)
        for offset in range(max(0, current_index - 3), min(len(self.cyton_epochs), current_index + 4)):
            epoch = self.cyton_epochs[offset]
            marker = ">" if offset == current_index else " "
            print(
                f"{marker} epoch {epoch.index + 1:>2}/{len(self.cyton_epochs)}  "
                f"{epoch.brain_state:<7}  valence {epoch.valence:+.2f}  "
                f"energy {epoch.energy:>9.2f}  valid {epoch.valid_fraction:>5.1%}"
            )
        self.pause()

    def status_panel(self) -> None:
        self.clear()
        print("RIDER STATUS")
        print("=" * DISPLAY_WIDTH)
        print(f"Current room: {self.current_room_id} — {self.room().title}")
        print(f"Coherence: {self.rider_coherence():.1%}   Witness threshold: {self.witness_threshold():.1%}")
        print(f"Triad quest: {self.quest_completion_count()}/{len(QUEST_ROOMS)}")
        print()
        print("Triad rooms")
        print("-" * DISPLAY_WIDTH)
        for room_id, label, witnessed, hops in self.quest_status():
            state = "witnessed" if witnessed else "open"
            room = self.rooms[room_id]
            print(f"- {label:<9} {room_id:<9} {state:<9} hops:{hops!s:<3} {room.title}")
        print()
        print("Recommended targets")
        print("-" * DISPLAY_WIDTH)
        for score, hops, room_id, coherence_value in self.best_targets():
            room = self.rooms[room_id]
            marker = "quest" if room_id in QUEST_ROOMS else "world"
            wit_mark = "*" if room_id in self.witnessed else "-"
            print(
                f"{wit_mark} {room_id:<12} {marker:<5} coh:{coherence_value:.1%} "
                f"hops:{hops:<2} rank:{score:.2f} {room.title}"
            )
        print()
        print("Recent journal")
        print("-" * DISPLAY_WIDTH)
        for entry in list(self.journal)[:6]:
            print(textwrap.indent(wrap(entry), prefix="- "))
        self.pause()

    def search_panel(self, query: str) -> None:
        results = self.search_rooms(query)
        self.clear()
        print(f"SEARCH — {query}")
        print("=" * DISPLAY_WIDTH)
        if not results:
            print("No matching rooms.")
            self.pause()
            return
        for room in results:
            path = self.shortest_path(self.current_room_id, room.id)
            hops = max(0, len(path) - 1) if path else "?"
            marker = "@" if room.id == self.current_room_id else ("*" if room.id in self.witnessed else "-")
            print(f"{marker} {room.id:<12} hops:{hops!s:<3} {room.title}")
            print(f"    {wrap(room.summary)}")
        self.pause()

    def route_panel(self, destination: str) -> None:
        self.clear()
        print(f"ROUTE — {destination}")
        print("=" * DISPLAY_WIDTH)
        if destination not in self.rooms:
            print(f"Unknown room id: {destination}")
            matches = self.search_rooms(destination, limit=5)
            if matches:
                print()
                print("Closest matches:")
                for room in matches:
                    print(f"- {room.id}: {room.title}")
            self.pause()
            return
        path = self.shortest_path(self.current_room_id, destination)
        if not path:
            print("No linked path found.")
            self.pause()
            return
        print(f"{len(path) - 1} hop(s)")
        print()
        for index, room_id in enumerate(path):
            room = self.rooms[room_id]
            prefix = "->" if index else "  "
            print(f"{prefix} {room.id}: {room.title}")
        self.pause()

    def best_card(self) -> DrillCard | None:
        if not self.cards:
            return None
        room_tokens = self.room().tokens
        candidates = sorted(
            self.cards,
            key=lambda card: (
                card.key in self.cleared_cards,
                -len(room_tokens & card.keywords),
                card.key,
            ),
        )
        return candidates[0]

    def drill(self) -> None:
        card = self.best_card()
        if card is None:
            self.message = "No distillation drill cards are available."
            return
        option_ids = [node_id for node_id in self.node_titles if node_id != card.answer_id]
        self.random.shuffle(option_ids)
        options = option_ids[:3] + [card.answer_id]
        self.random.shuffle(options)
        self.clear()
        print("DISTILLATION DRILL")
        print("=" * DISPLAY_WIDTH)
        print(wrap(card.prompt))
        print()
        for index, node_id in enumerate(options, start=1):
            print(f"{index}. {self.node_titles[node_id]}")
        print()
        answer = input("Pick 1-4 (blank to cancel): ").strip()
        if not answer:
            self.set_message("Drill canceled.")
            return
        if answer not in {"1", "2", "3", "4"}:
            self.set_message(f"Invalid drill choice: {answer}")
            return
        selected = options[int(answer) - 1]
        aura, _ = self.room_aura()
        if selected == card.answer_id:
            bonus = 2 if aura.brain_state == "alert" else 1
            self.score += bonus
            witnessed = self.award_witness(bonus=2)
            message = f"Correct. {card.answer_title} stabilized the room. +{bonus}."
            if witnessed:
                message += " Witness locked: +2."
                message += self.close_triads_if_ready()
            self.set_message(message)
        else:
            if aura.brain_state != "rest":
                self.score -= 1
            self.set_message(f"Wrong. Correct answer: {card.answer_title}.")
        self.cleared_cards.add(card.key)

    def witness(self) -> None:
        room = self.room()
        coherence_value = self.rider_coherence()
        threshold = self.witness_threshold()
        if room.id in self.witnessed:
            self.set_message(f"{room.id} is already witnessed.")
            return
        if self.award_witness(bonus=3):
            self.set_message(
                f"Witness sealed for {room.id}. Coherence {coherence_value:.1%}. +3."
                + self.close_triads_if_ready()
            )
            return
        self.set_message(
            f"Coherence {coherence_value:.1%} is below the witness window {threshold:.1%}. "
            "Try `r` to resonate or move to a different room."
        )

    def resonate(self) -> None:
        previous = self.current_epoch()
        previous_coherence = self.rider_coherence()
        self.turn_index += 1
        epoch = self.current_epoch()
        coherence_value = self.rider_coherence()
        delta = coherence_value - previous_coherence
        message = (
            f"Resonated from epoch {previous.index + 1} to {epoch.index + 1}: "
            f"{epoch.brain_state} {epoch.valence:+.2f}."
        )
        if delta > 0.05:
            self.score += 1
            message += " Gap narrowed: +1."
        elif delta < -0.08 and epoch.brain_state != "rest":
            self.score -= 1
            message += " Gap widened: -1."
        self.set_message(message)

    def go_to(self, destination: str) -> None:
        destination = destination.strip()
        if not destination:
            self.set_message("Usage: go <room-id>")
            return
        if destination not in self.rooms:
            matches = self.search_rooms(destination, limit=3)
            if matches:
                hint = ", ".join(room.id for room in matches)
                self.set_message(f"Unknown room '{destination}'. Try: {hint}")
            else:
                self.set_message(f"Unknown room '{destination}'.")
            return
        if destination == self.current_room_id:
            self.set_message(f"Already in {destination}.")
            return
        hops_taken = 0
        drifted = False
        while self.current_room_id != destination:
            path = self.shortest_path(self.current_room_id, destination)
            if len(path) < 2:
                self.set_message(f"No linked path from {self.current_room_id} to {destination}.")
                return
            next_step = path[1]
            before = self.current_room_id
            self.move(next_step)
            hops_taken += 1
            if self.current_room_id == before:
                break
            if self.current_room_id != next_step:
                drifted = True
                break
            if hops_taken > 50:
                break
        suffix = (
            f" Autotravel arrived after {hops_taken} hop(s)."
            if self.current_room_id == destination
            else f" Autotravel drifted off route after {hops_taken} hop(s)."
            if drifted
            else f" Autotravel stopped after {hops_taken} hop(s)."
        )
        self.set_message(self.message + suffix)

    def move(self, destination: str) -> None:
        exits = self.current_exits()
        previous_coherence = self.rider_coherence()
        if destination.isdigit():
            index = int(destination) - 1
            if index < 0 or index >= len(exits):
                self.set_message(f"Exit {destination} is out of range.")
                return
            destination = exits[index]
        if destination not in exits:
            self.set_message(f"{destination} is not a linked exit from {self.current_room_id}.")
            return
        self.current_room_id = destination
        self.turn_index += 1
        self.visits.append(destination)
        aura, _ = self.room_aura()
        if aura.brain_state == "fatigue" and len(self.room().exits) > 1 and self.random.random() < 0.15:
            drift_options = [room_id for room_id in self.room().exits if room_id != self.current_room_id]
            if drift_options:
                drift_target = self.random.choice(drift_options)
                self.current_room_id = drift_target
                self.visits.append(drift_target)
                message = f"Wild drift pulled you through fatigue space into {drift_target}."
            else:
                message = f"Moved to {destination}."
        else:
            message = f"Moved to {self.current_room_id}."
        current_coherence = self.rider_coherence()
        if current_coherence > previous_coherence + 0.05:
            self.score += 1
            message += " Gap narrowed: +1."
        self.set_message(message)

    def run(self) -> int:
        while True:
            self.render()
            try:
                command = input("> ").strip()
            except EOFError:
                print()
                return 0
            if command in {"q", "quit", "exit"}:
                return 0
            if command in {"", "l", "look"}:
                self.look_panel()
                continue
            if command in {"w", "witness"}:
                self.witness()
                continue
            if command in {"r", "resonate"}:
                self.resonate()
                continue
            if command in {"d", "drill"}:
                self.drill()
                continue
            if command in {"m", "map"}:
                self.map_panel()
                continue
            if command in {"t", "trace"}:
                self.trace_panel()
                continue
            if command in {"h", "help", "?"}:
                self.help_panel()
                continue
            if command in {"p", "status"}:
                self.status_panel()
                continue
            if command.startswith("s "):
                self.search_panel(command[2:])
                continue
            if command.startswith("search "):
                self.search_panel(command[7:])
                continue
            if command.startswith("route "):
                self.route_panel(command[6:].strip())
                continue
            if command.startswith("go "):
                self.go_to(command[3:].strip())
                continue
            self.move(command)


def smoke_test(name: str, start_room: str, workspace_root: Path, repo_root: Path) -> int:
    game = SecretColorMud(name=name, start_room=start_room, workspace_root=workspace_root, repo_root=repo_root)
    room = game.room()
    aura, epoch = game.room_aura()
    card = game.best_card()
    print(f"rooms={len(game.rooms)}")
    print(f"drills={len(game.cards)}")
    print(f"start={room.id}:{room.title}")
    print(f"name_color={game.player_color.hex_color}:{game.player_color.brain_state}:{game.player_color.valence:+.2f}")
    print(f"brain_color={aura.hex_color}:{aura.brain_state}:{aura.valence:+.2f}")
    print(f"ambient_epoch={epoch.index + 1}/{len(game.cyton_epochs)}")
    print(f"exit_count={len(game.current_exits())}")
    print(f"coherence={game.rider_coherence():.3f}")
    print(f"witness_threshold={game.witness_threshold():.3f}")
    print(f"triad_progress={game.quest_completion_count()}/{len(QUEST_ROOMS)}")
    if card:
        print(f"sample_drill={card.answer_title}")
    return 0


def main() -> int:
    script_path = Path(__file__).resolve()
    repo_root = script_path.parents[1]
    workspace_root = script_path.parents[2]
    parser = argparse.ArgumentParser(description="Horse x NBLM secret-color terminal MUD")
    parser.add_argument("--name", default="Rider", help="Player name used for the deterministic name-color")
    parser.add_argument("--start", default="horse-0001", help="Starting room id")
    parser.add_argument("--smoke-test", action="store_true", help="Load data, build the world, and print a summary")
    args = parser.parse_args()
    if args.smoke_test:
        return smoke_test(args.name, args.start, workspace_root, repo_root)
    game = SecretColorMud(name=args.name, start_room=args.start, workspace_root=workspace_root, repo_root=repo_root)
    return game.run()


if __name__ == "__main__":
    raise SystemExit(main())

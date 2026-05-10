import tkinter as tk
from tkinter import messagebox
import json
import os
import random

# ============================================================
# RWB Science Crossword v2.7 Mobile
# Created by: Robert William Blennerhed - RWB Tech Lab
# Developed in collaboration with ChatGPT by OpenAI.
# Smart crossword engine + autosave + statistics bugfix.
# ============================================================

GRID_SIZE = 12
CELL_SIZE = 70
MAX_WORDS = 24

DATA_FILE = "rwb_science_questions_1000.json"
USERDATA_FILE = "rwb_crossword_userdata.json"
STATISTICS_FILE = "rwb_crossword_statistics.json"

grid = [["" for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
entries = {}
placed_words = []
start_numbers = {}
cell_to_words = {}
active_word = {"data": None}
saved_values = {}


def load_questions():
    if not os.path.exists(DATA_FILE):
        messagebox.showerror("Missing JSON", f"Missing file:\n{DATA_FILE}")
        return []

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    valid = []
    used = set()

    for item in data:
        clue = item.get("clue", "").strip()
        answer = item.get("answer", "").strip().upper()
        category = str(item.get("category", "science")).strip()

        if clue and 2 <= len(answer) <= 12 and answer.isalpha() and answer not in used:
            valid.append({"answer": answer, "clue": clue, "category": category})
            used.add(answer)

    return valid


def load_statistics():
    if not os.path.exists(STATISTICS_FILE):
        return {"crosswords_solved": 0, "solved_words": [], "solved_crosswords": []}

    try:
        with open(STATISTICS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        data.setdefault("crosswords_solved", 0)
        data.setdefault("solved_words", [])
        data.setdefault("solved_crosswords", [])
        return data

    except Exception:
        return {"crosswords_solved": 0, "solved_words": [], "solved_crosswords": []}


def save_statistics(data):
    try:
        with open(STATISTICS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception:
        pass


def can_place(word, row, col, direction):
    if direction == "A":
        if row < 0 or row >= GRID_SIZE or col < 0 or col + len(word) > GRID_SIZE:
            return False
        if col > 0 and grid[row][col - 1] != "":
            return False
        if col + len(word) < GRID_SIZE and grid[row][col + len(word)] != "":
            return False

        crossings = 0
        for i, ch in enumerate(word):
            r = row
            c = col + i
            current = grid[r][c]
            if current != "" and current != ch:
                return False
            if current == ch:
                crossings += 1
            else:
                if r > 0 and grid[r - 1][c] != "":
                    return False
                if r < GRID_SIZE - 1 and grid[r + 1][c] != "":
                    return False
        return crossings > 0

    if col < 0 or col >= GRID_SIZE or row < 0 or row + len(word) > GRID_SIZE:
        return False
    if row > 0 and grid[row - 1][col] != "":
        return False
    if row + len(word) < GRID_SIZE and grid[row + len(word)][col] != "":
        return False

    crossings = 0
    for i, ch in enumerate(word):
        r = row + i
        c = col
        current = grid[r][c]
        if current != "" and current != ch:
            return False
        if current == ch:
            crossings += 1
        else:
            if c > 0 and grid[r][c - 1] != "":
                return False
            if c < GRID_SIZE - 1 and grid[r][c + 1] != "":
                return False
    return crossings > 0


def count_crossings(word, row, col, direction):
    crossings = 0
    for i, ch in enumerate(word):
        r = row + (i if direction == "D" else 0)
        c = col + (i if direction == "A" else 0)
        if grid[r][c] == ch:
            crossings += 1
    return crossings


def get_bounds_after(word, row, col, direction):
    used_cells = []
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            if grid[r][c]:
                used_cells.append((r, c))

    for i in range(len(word)):
        r = row + (i if direction == "D" else 0)
        c = col + (i if direction == "A" else 0)
        used_cells.append((r, c))

    min_r = min(r for r, c in used_cells)
    max_r = max(r for r, c in used_cells)
    min_c = min(c for r, c in used_cells)
    max_c = max(c for r, c in used_cells)
    return (max_r - min_r + 1) * (max_c - min_c + 1)


def place_word(number, item, row, col, direction):
    word = item["answer"]

    for i, ch in enumerate(word):
        r = row + (i if direction == "D" else 0)
        c = col + (i if direction == "A" else 0)
        grid[r][c] = ch

    placed_words.append({
        "number": number,
        "answer": word,
        "clue": item["clue"],
        "category": item["category"],
        "row": row,
        "col": col,
        "direction": direction
    })

    if (row, col) not in start_numbers:
        start_numbers[(row, col)] = str(number)


def build_crossword(question_bank):
    random.shuffle(question_bank)
    words = sorted(question_bank, key=lambda x: len(x["answer"]), reverse=True)
    if not words:
        return

    first = words[0]
    start_row = GRID_SIZE // 2
    start_col = max(0, (GRID_SIZE - len(first["answer"])) // 2)
    place_word(1, first, start_row, start_col, "A")

    number = 2
    for item in words[1:]:
        if number > MAX_WORDS:
            break

        word = item["answer"]
        candidates = []

        for existing in placed_words:
            existing_word = existing["answer"]
            for i, ch1 in enumerate(word):
                for j, ch2 in enumerate(existing_word):
                    if ch1 != ch2:
                        continue

                    new_dir = "D" if existing["direction"] == "A" else "A"

                    if new_dir == "A":
                        row = existing["row"] + (j if existing["direction"] == "D" else 0)
                        col = existing["col"] + (j if existing["direction"] == "A" else 0) - i
                    else:
                        row = existing["row"] + (j if existing["direction"] == "D" else 0) - i
                        col = existing["col"] + (j if existing["direction"] == "A" else 0)

                    if can_place(word, row, col, new_dir):
                        crossings = count_crossings(word, row, col, new_dir)
                        compactness = get_bounds_after(word, row, col, new_dir)
                        score = (crossings * 1000) - compactness
                        candidates.append((score, row, col, new_dir))

        if candidates:
            candidates.sort(reverse=True)
            _, row, col, direction = candidates[0]
            place_word(number, item, row, col, direction)
            number += 1


def build_cell_to_words():
    cell_to_words.clear()
    for word_data in placed_words:
        for i in range(len(word_data["answer"])):
            r = word_data["row"] + (i if word_data["direction"] == "D" else 0)
            c = word_data["col"] + (i if word_data["direction"] == "A" else 0)
            cell_to_words.setdefault((r, c), []).append(word_data)


def set_active_word(r, c):
    words_here = cell_to_words.get((r, c), [])
    if not words_here:
        active_word["data"] = None
        return

    for w in words_here:
        if w["direction"] == "A":
            active_word["data"] = w
            return
    active_word["data"] = words_here[0]


def move_to_next_in_word(r, c):
    w = active_word["data"]
    if not isinstance(w, dict) or "answer" not in w:
        return

    for i in range(len(w["answer"])):
        rr = w["row"] + (i if w["direction"] == "D" else 0)
        cc = w["col"] + (i if w["direction"] == "A" else 0)

        if rr == r and cc == c:
            next_i = i + 1
            if next_i < len(w["answer"]):
                nr = w["row"] + (next_i if w["direction"] == "D" else 0)
                nc = w["col"] + (next_i if w["direction"] == "A" else 0)
                if (nr, nc) in entries:
                    entries[(nr, nc)].focus_set()
            return


def save_user_data():
    data = {
        "grid_size": GRID_SIZE,
        "data_file": DATA_FILE,
        "placed_words": placed_words,
        "values": {}
    }
    for (r, c), e in entries.items():
        data["values"][f"{r},{c}"] = e.get().upper()

    try:
        with open(USERDATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception:
        pass


def load_user_data():
    global placed_words, saved_values

    if not os.path.exists(USERDATA_FILE):
        return False

    try:
        with open(USERDATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        if data.get("grid_size") != GRID_SIZE:
            return False
        if data.get("data_file") != DATA_FILE:
            return False

        placed_words = data.get("placed_words", [])
        saved_values = data.get("values", {})

        for word_data in placed_words:
            word = word_data["answer"]
            row = word_data["row"]
            col = word_data["col"]
            direction = word_data["direction"]

            if (row, col) not in start_numbers:
                start_numbers[(row, col)] = str(word_data["number"])

            for i, ch in enumerate(word):
                r = row + (i if direction == "D" else 0)
                c = col + (i if direction == "A" else 0)
                grid[r][c] = ch
        return True

    except Exception:
        return False


def apply_saved_values():
    for key, value in saved_values.items():
        try:
            r, c = map(int, key.split(","))
            if (r, c) in entries and value:
                entries[(r, c)].delete(0, tk.END)
                entries[(r, c)].insert(0, value)
        except Exception:
            pass


def limit_one_char(event, r, c):
    value = entries[(r, c)].get().upper()
    if len(value) > 1:
        value = value[-1]

    entries[(r, c)].delete(0, tk.END)
    entries[(r, c)].insert(0, value)
    entries[(r, c)].config(bg="white")
    save_user_data()

    if value:
        move_to_next_in_word(r, c)


def read_answer(word_data):
    answer = ""
    for i in range(len(word_data["answer"])):
        r = word_data["row"] + (i if word_data["direction"] == "D" else 0)
        c = word_data["col"] + (i if word_data["direction"] == "A" else 0)
        answer += entries[(r, c)].get().upper()
    return answer


def check_all_complete_and_correct():
    for w in placed_words:
        if read_answer(w) != w["answer"]:
            return False
    return True


def get_crossword_id():
    words = sorted(w["answer"] for w in placed_words)
    return "|".join(words)


def update_statistics_when_solved():
    stats = load_statistics()
    crossword_id = get_crossword_id()

    if crossword_id in stats.get("solved_crosswords", []):
        return False

    stats["crosswords_solved"] += 1
    stats["solved_crosswords"].append(crossword_id)

    solved_set = set(stats.get("solved_words", []))
    for w in placed_words:
        solved_set.add(w["answer"])
    stats["solved_words"] = sorted(list(solved_set))

    save_statistics(stats)
    return True


def correct_letters():
    total_filled = 0
    correct_count = 0

    for (r, c), e in entries.items():
        value = e.get().upper()
        correct_value = grid[r][c]

        if value == "":
            e.config(bg="white")
            continue

        total_filled += 1
        if value == correct_value:
            correct_count += 1
            e.config(bg="#c8f7c5")
        else:
            e.config(bg="#ffd0d0")

    return correct_count, total_filled


def check_answers():
    correct_count, total_filled = correct_letters()
    save_user_data()

    if check_all_complete_and_correct():
        was_new = update_statistics_when_solved()
        if was_new:
            messagebox.showinfo(
                "Well done!",
                "Well done!\nYou did it.\nCongratulations!"
            )
        else:
            messagebox.showinfo(
                "Already solved",
                "This crossword has already been counted in your statistics."
            )
    else:
        messagebox.showinfo(
            "Result",
            f"Correct letters: {correct_count} / {total_filled}"
        )


def new_game():
    confirm = messagebox.askyesno(
        "New Game",
        "Start a new crossword?\n\nYour statistics will be kept."
    )
    if not confirm:
        return

    if os.path.exists(USERDATA_FILE):
        try:
            os.remove(USERDATA_FILE)
        except Exception:
            pass

    root.destroy()


def show_statistics():
    stats = load_statistics()
    solved_words = stats.get("solved_words", [])
    total_words = 1000

    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                total_words = len(json.load(f))
        except Exception:
            total_words = 1000

    solved_count = len(solved_words)
    percent = (solved_count / total_words) * 100 if total_words > 0 else 0

    messagebox.showinfo(
        "Statistics",
        f"Crosswords solved: {stats.get('crosswords_solved', 0)}\n"
        f"Words solved in database: {solved_count} / {total_words}\n"
        f"Database progress: {percent:.2f}%"
    )


# ============================
# START PROGRAM
# ============================

root = tk.Tk()
root.title("RWB Science Crossword v2.7")
root.geometry("720x1200")
root.configure(bg="#d9d9d9")

loaded_saved_game = load_user_data()

if not loaded_saved_game:
    question_bank = load_questions()
    if question_bank:
        build_crossword(question_bank)

build_cell_to_words()

title = tk.Label(
    root,
    text="RWB Science Crossword v2.7",
    font=("Arial", 12, "bold"),
    bg="#d9d9d9"
)
title.pack(pady=2)

info_text = f"Smart crossword engine - {len(placed_words)} words placed"
if loaded_saved_game:
    info_text += "\nsaved game loaded"

info = tk.Label(root, text=info_text, font=("Arial", 9), bg="#d9d9d9")
info.pack(pady=1)

grid_frame = tk.Frame(root, bg="#d9d9d9")
grid_frame.pack(pady=2)

for r in range(GRID_SIZE):
    for c in range(GRID_SIZE):
        if grid[r][c]:
            cell = tk.Frame(
                grid_frame,
                width=CELL_SIZE,
                height=CELL_SIZE,
                bg="white",
                highlightbackground="gray",
                highlightthickness=1
            )
            cell.grid(row=r, column=c, padx=1, pady=1)
            cell.grid_propagate(False)

            e = tk.Entry(cell, justify="center", font=("Arial", 14), bd=0)
            e.place(x=3, y=3, width=CELL_SIZE - 6, height=CELL_SIZE - 6)
            e.bind("<FocusIn>", lambda event, rr=r, cc=c: set_active_word(rr, cc))
            e.bind("<KeyRelease>", lambda event, rr=r, cc=c: limit_one_char(event, rr, cc))
            entries[(r, c)] = e

        else:
            block = tk.Frame(
                grid_frame,
                width=CELL_SIZE,
                height=CELL_SIZE,
                bg="black",
                highlightbackground="gray",
                highlightthickness=1
            )
            block.grid(row=r, column=c, padx=1, pady=1)
            block.grid_propagate(False)

apply_saved_values()

button_frame = tk.Frame(root, bg="#d9d9d9")
button_frame.pack(pady=5)

btn_font = ("Arial", 11)

tk.Button(button_frame, text="Correct", width=7, font=btn_font, bg="#4CAF50",fg="white" , command=check_answers).grid(row=0, column=0, padx=3)
tk.Button(button_frame, text="New Game", width=7, font=btn_font, bg="#2196F3", fg="white", command=new_game).grid(row=0, column=1, padx=3)
tk.Button(button_frame, text="Statistics", width=7, font=btn_font, bg="#673ab7",  fg="white"  ,command=show_statistics).grid(row=0, column=2, padx=3)

clue_frame = tk.Frame(root, bg="#d9d9d9")
clue_frame.pack(pady=3, fill="both", expand=True)

scrollbar = tk.Scrollbar(clue_frame)
scrollbar.pack(side="right", fill="y")

clue_box = tk.Text(
    clue_frame,
    height=6,
    width=38,
    font=("Arial", 10),
    wrap="word",
    yscrollcommand=scrollbar.set
)
clue_box.pack(side="left", fill="both", expand=True)
scrollbar.config(command=clue_box.yview)

clue_box.insert(tk.END, "ACROSS\n")
for word_data in placed_words:
    if word_data["direction"] == "A":
        clue_box.insert(
            tk.END,
            f"{word_data['number']}. {word_data['clue']} ({len(word_data['answer'])})\n"
        )

clue_box.insert(tk.END, "\nDOWN\n")
for word_data in placed_words:
    if word_data["direction"] == "D":
        clue_box.insert(
            tk.END,
            f"{word_data['number']}. {word_data['clue']} ({len(word_data['answer'])})\n"
        )

clue_box.config(state="disabled")

# Allow scrolling but block selection and key input
clue_box.bind("<Button-1>", lambda e: "break")
clue_box.bind("<B1-Motion>", lambda e: "break")
clue_box.bind("<Double-1>", lambda e: "break")
clue_box.bind("<Triple-1>", lambda e: "break")
clue_box.bind("<Key>", lambda e: "break")

root.mainloop()

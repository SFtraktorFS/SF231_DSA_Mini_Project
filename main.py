import tkinter as tk
from tkinter import messagebox
import random
import copy
import time

# =======================
# GLOBAL
# =======================
SIZE = 9
BOX = 3

operation_normal = 0
operation_fast = 0

solution_board = None
original_puzzle = None

# =======================
# MODE
# =======================
def set_mode(mode):
    global SIZE, BOX
    if mode == "Easy":
        SIZE, BOX = 4, 2
    else:
        SIZE, BOX = 9, 3
    reset_board()

# =======================
# BASIC SOLVER
# =======================
def find_empty(board):
    for i in range(SIZE):
        for j in range(SIZE):
            if board[i][j] == 0:
                return i, j
    return None

def is_valid(board, num, pos):
    r, c = pos

    if num in board[r]:
        return False

    for i in range(SIZE):
        if board[i][c] == num:
            return False

    box_x = c // BOX
    box_y = r // BOX

    for i in range(box_y*BOX, box_y*BOX + BOX):
        for j in range(box_x*BOX, box_x*BOX + BOX):
            if board[i][j] == num:
                return False

    return True

def solve_normal(board):
    global operation_normal

    find = find_empty(board)
    if not find:
        return True

    r, c = find

    for num in range(1, SIZE+1):
        operation_normal += 1
        if is_valid(board, num, (r, c)):
            board[r][c] = num
            if solve_normal(board):
                return True
            board[r][c] = 0

    return False

# =======================
# FAST SOLVER (MRV + BITMASK)
# =======================
def init_masks(board):
    row = [0]*SIZE
    col = [0]*SIZE
    box = [0]*SIZE

    for i in range(SIZE):
        for j in range(SIZE):
            num = board[i][j]
            if num != 0:
                bit = 1 << num
                row[i] |= bit
                col[j] |= bit
                box[(i//BOX)*BOX + j//BOX] |= bit

    return row, col, box

def find_best_cell(board, row, col, box):
    min_options = SIZE + 1
    best = None

    for i in range(SIZE):
        for j in range(SIZE):
            if board[i][j] == 0:
                used = row[i] | col[j] | box[(i//BOX)*BOX + j//BOX]

                options = []
                for num in range(1, SIZE+1):
                    if not (used & (1 << num)):
                        options.append(num)

                if len(options) < min_options:
                    min_options = len(options)
                    best = (i, j, options)

                if min_options == 1:
                    return best

    return best

def solve_fast(board, row, col, box):
    global operation_fast

    cell = find_best_cell(board, row, col, box)
    if not cell:
        return True

    i, j, options = cell
    b = (i//BOX)*BOX + j//BOX

    for num in options:
        operation_fast += 1
        bit = 1 << num

        board[i][j] = num
        row[i] |= bit
        col[j] |= bit
        box[b] |= bit

        if solve_fast(board, row, col, box):
            return True

        board[i][j] = 0
        row[i] ^= bit
        col[j] ^= bit
        box[b] ^= bit

    return False

# =======================
# GENERATE
# =======================
def generate_full():
    board = [[0]*SIZE for _ in range(SIZE)]

    def fill():
        find = find_empty(board)
        if not find:
            return True

        r, c = find
        nums = list(range(1, SIZE+1))
        random.shuffle(nums)

        for num in nums:
            if is_valid(board, num, (r, c)):
                board[r][c] = num
                if fill():
                    return True
                board[r][c] = 0
        return False

    reset_board()
    fill()
    return board

def create_puzzle(full, clues):
    puzzle = copy.deepcopy(full)
    remove = SIZE*SIZE - clues

    while remove > 0:
        r = random.randint(0, SIZE-1)
        c = random.randint(0, SIZE-1)
        if puzzle[r][c] != 0:
            puzzle[r][c] = 0
            remove -= 1

    return puzzle

# =======================
# GUI
# =======================
root = tk.Tk()
root.title("Sudoku AI Solver")
root.configure(bg="#f5f5f5")

entries = []

bg1 = "#ffffff"    # Grid color 1
bg2 = "#f0f0f0"    # Grid color 2
fg_given = "#000000" # Black for problem
fg_user = "#007acc"  # Blue for answer
red_light = "#ffcccc" # Light red for warning

frame = tk.Frame(root, bg="#dcdcdc", bd=2) # Darker border for the grid
frame.pack(pady=10)

# =======================
# GRID
# =======================
def build_grid():
    global entries
    for w in frame.winfo_children():
        w.destroy()

    entries = []

    for i in range(SIZE):
        row = []
        for j in range(SIZE):
            color = bg1 if (i//BOX + j//BOX) % 2 == 0 else bg2

            e = tk.Entry(frame, width=2, font=("Consolas", 18),
                         justify="center", bg=color, fg=fg_user,
                         insertbackground="black")

            e.grid(row=i, column=j,
                   padx=(4 if j % BOX == 0 else 1),
                   pady=(4 if i % BOX == 0 else 1))

            row.append(e)
        entries.append(row)

def load_board(board):
    for i in range(SIZE):
        for j in range(SIZE):
            e = entries[i][j]
            e.config(state="normal")
            e.delete(0, tk.END)
            if board[i][j] != 0:
                e.insert(0, str(board[i][j]))
                e.config(state="readonly", fg=fg_given, font=("Consolas", 18, "bold"))
            else:
                e.config(state="normal", fg=fg_user, font=("Consolas", 18))

def load_row(board, row_idx):
    for j in range(SIZE):
        e = entries[row_idx][j]
        # Skip updating if it's already a given number (optional, but cleaner)
        if original_puzzle and original_puzzle[row_idx][j] != 0:
            continue
            
        e.config(state="normal")
        e.delete(0, tk.END)
        e.insert(0, str(board[row_idx][j]))
        e.config(fg=fg_user) # Solved numbers count as user/AI numbers

def animate_solution(board, row=0):
    if row >= SIZE:
        return

    load_row(board, row)
    root.after(500, lambda: animate_solution(board, row+1))

def read_board():
    board = []
    for i in range(SIZE):
        row = []
        for j in range(SIZE):
            val = entries[i][j].get()
            row.append(int(val) if val.isdigit() else 0)
        board.append(row)
    return board

# =======================
# GENERATE / SOLVE
# =======================
def generate():
    global solution_board, original_puzzle

    clues = int(clue_entry.get())

    full = generate_full()
    puzzle = create_puzzle(full, clues)

    solution_board = full
    original_puzzle = copy.deepcopy(puzzle)

    load_board(puzzle)

def solve_gui():
    global operation_normal, operation_fast, solution_board

    board = read_board()
    algo = algo_var.get()

    if algo == "Normal":
        operation_normal = 0
        start = time.time()
        success = solve_normal(board)
        elapsed = time.time() - start

        if success:
            solution_board = copy.deepcopy(board)
            animate_solution(board)
            result.config(text=f"Normal: {operation_normal} ops | {elapsed:.4f}s")
        else:
            messagebox.showinfo("Sudoku", "No solution exists for this board!")

    else:
        operation_fast = 0
        row_mask, col_mask, box_mask = init_masks(board)

        start = time.time()
        success = solve_fast(board, row_mask, col_mask, box_mask)
        elapsed = time.time() - start

        if success:
            solution_board = copy.deepcopy(board)
            animate_solution(board)
            result.config(text=f"Fast: {operation_fast} ops | {elapsed:.4f}s")
        else:
            messagebox.showinfo("Sudoku", "No solution exists for this board!")

# =======================
# CHECK
# =======================
def flash(e, orig_bg, c=0):
    if c < 6:
        e.config(bg=red_light if c % 2 == 0 else orig_bg)
        root.after(100, lambda: flash(e, orig_bg, c+1))
    else:
        e.config(bg=red_light)

def check():
    if solution_board is None:
        return

    ok = True
    for i in range(SIZE):
        for j in range(SIZE):
            if original_puzzle[i][j] != 0:
                continue

            e = entries[i][j]
            val = e.get()
            orig_bg = bg1 if (i//BOX + j//BOX) % 2 == 0 else bg2

            if val.isdigit():
                if int(val) == solution_board[i][j]:
                    e.config(bg=orig_bg) # ถูกไม่แสดง (Keep original bg)
                else:
                    flash(e, orig_bg)
                    ok = False
            else:
                e.config(bg=orig_bg)
                ok = False

# =======================
# BIG-O
# =======================


# =======================
# CONTROL
# =======================
control = tk.Frame(root, bg="#f5f5f5")
control.pack(pady=10)
def reset_board():
    build_grid()
    result.config(text="")

# แล้วค่อยมีปุ่ม
tk.Button(control, text="Reset", command=reset_board)

mode = tk.StringVar(value="Normal")
tk.OptionMenu(control, mode, "Normal", "Easy",
              command=set_mode).grid(row=0, column=0)

clue_entry = tk.Entry(control, width=5)
clue_entry.insert(0, "30")
clue_entry.grid(row=0, column=1)

algo_var = tk.StringVar(value="Fast")
tk.OptionMenu(control, algo_var, "Normal", "Fast")\
    .grid(row=0, column=2)

tk.Button(control, text="Generate", command=generate).grid(row=0, column=3)
tk.Button(control, text="Solve", command=solve_gui).grid(row=0, column=4)
tk.Button(control, text="Check", command=check).grid(row=0, column=5)
tk.Button(control, text="Reset", command=reset_board).grid(row=0, column=6)

bigo_label = tk.Label(root, text="", fg="black", bg="#f5f5f5")
bigo_label.pack()

result = tk.Label(root, text="", fg="#007acc", bg="#f5f5f5")
result.pack()


build_grid()
root.mainloop()
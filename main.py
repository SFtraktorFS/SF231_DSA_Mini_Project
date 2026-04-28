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
# UI STYLING & COLORS
# =======================
BG_MAIN    = "#F0F2F5"    # Soft Gray-Blue Background
BG_CARD    = "#FFFFFF"    # Card background
ACCENT     = "#4361EE"    # Primary Action Blue
SUCCESS    = "#2EC4B6"    # Success Green
ERROR      = "#E71D36"    # Error Red
TEXT_DARK  = "#2B2D42"    # Main Text
TEXT_LIGHT = "#8D99AE"    # Subtext

# Grid Colors
BG_GRID_1  = "#FFFFFF"    # White block
BG_GRID_2  = "#E0F2FE"    # Light Sea Blue (สีน้ำเงินอ่อนทะเล)
FG_GIVEN   = "#1A1A1A"    # Bold black for clues
FG_USER    = "#4361EE"    # Blue for answers
FG_SOLVED  = "#7209B7"    # Purple for AI solved numbers
HIGHLIGHT  = "#E0E7FF"    # Highlight for active cell

FONT_MAIN  = ("Segoe UI", 10)
FONT_BOLD  = ("Segoe UI", 10, "bold")
FONT_TITLE = ("Segoe UI", 18, "bold")
FONT_GRID  = ("Consolas", 20, "bold")

# =======================
# UI INITIALIZATION
# =======================
root = tk.Tk()
root.title("Sudoku AI Solver Pro")
root.geometry("800x700")
root.configure(bg=BG_MAIN)

# Main Container
main_container = tk.Frame(root, bg=BG_MAIN)
main_container.pack(expand=True, fill="both", padx=40, pady=20)

# Header
header = tk.Frame(main_container, bg=BG_MAIN)
header.pack(fill="x", pady=(0, 20))

tk.Label(header, text="Sudoku AI Solver", font=FONT_TITLE,
         bg=BG_MAIN, fg=TEXT_DARK).pack(side="left")

# Grid Frame with distinct borders
grid_container = tk.Frame(main_container, bg="#343A40", bd=2) # Dark background for lines
grid_container.pack(side="left", padx=(0, 20))

entries = []

def build_grid():
    global entries
    for w in grid_container.winfo_children():
        w.destroy()

    entries = []
    
    # Determine square size in pixels
    cell_size = 55 if SIZE == 9 else 100
    font_size = 22 if SIZE == 9 else 36
    
    for i in range(SIZE):
        row = []
        for j in range(SIZE):
            if (i // BOX + j // BOX) % 2 == 0:
                color = BG_GRID_1
            else:
                color = BG_GRID_2

            # Thicker borders for the major boxes
            left_pad = 3 if j % BOX == 0 and j != 0 else 1
            top_pad = 3 if i % BOX == 0 and i != 0 else 1
            
            # FIXED SIZE Cell wrapper to ensure perfect square
            cell_frame = tk.Frame(grid_container, bg="#343A40", width=cell_size, height=cell_size)
            cell_frame.grid_propagate(False) # Force the frame to stay at fixed width/height
            cell_frame.grid(row=i, column=j, padx=(left_pad, 0), pady=(top_pad, 0), sticky="nsew")

            e = tk.Entry(cell_frame, width=2, font=("Consolas", font_size, "bold"),
                         justify="center", bg=color, fg=FG_USER,
                         bd=0, relief="flat", insertbackground=ACCENT)
            
            # Pack the entry to fill the square frame completely
            e.pack(expand=True, fill="both")
            
            # Events for better UX
            e.bind("<FocusIn>", lambda event, entry=e, bg=color: entry.config(bg=HIGHLIGHT))
            e.bind("<FocusOut>", lambda event, entry=e, bg=color: entry.config(bg=bg))

            row.append(e)
        entries.append(row)

def reset_board():
    build_grid()
    if 'result' in globals() and result:
        result.config(text="Ready (พร้อมใช้งาน)", fg=ACCENT)

def load_board(board):
    for i in range(SIZE):
        for j in range(SIZE):
            e = entries[i][j]
            e.config(state="normal")
            e.delete(0, tk.END)
            if board[i][j] != 0:
                e.insert(0, str(board[i][j]))
                e.config(state="readonly", fg=FG_GIVEN, readonlybackground=entries[i][j].cget("bg"))
            else:
                e.config(state="normal", fg=FG_USER)

def load_row(board, row_idx):
    for j in range(SIZE):
        e = entries[row_idx][j]
        if original_puzzle and original_puzzle[row_idx][j] != 0:
            continue
            
        e.config(state="normal")
        e.delete(0, tk.END)
        e.insert(0, str(board[row_idx][j]))
        e.config(fg=FG_SOLVED)

def animate_solution(board, row=0):
    if row >= SIZE:
        result.config(text=f"Solution found! {result.cget('text')}", fg=SUCCESS)
        return

    load_row(board, row)
    root.after(100, lambda: animate_solution(board, row+1))

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

    if original_puzzle is None:
        messagebox.showwarning("Warning", "กรุณาสร้างโจทย์ก่อน! (Please generate a puzzle first!)")
        return

    # ล้างเลขที่เติมไว้ก่อนหน้า โดยโหลดโจทย์ตั้งต้นกลับมา (Clear previous solution/user input)
    load_board(original_puzzle)
    
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
            messagebox.showinfo("Sudoku", "ไม่พบคำตอบสำหรับโจทย์นี้! (No solution exists for this board!)")

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
            messagebox.showinfo("Sudoku", "ไม่พบคำตอบสำหรับโจทย์นี้! (No solution exists for this board!)")

# =======================
# CHECK LOGIC
# =======================
def flash(e, orig_bg, c=0):
    if c < 6:
        e.config(bg=ERROR if c % 2 == 0 else orig_bg)
        root.after(100, lambda: flash(e, orig_bg, c+1))
    else:
        e.config(bg="#FEE2E2") # Light red background for errors

def check():
    if solution_board is None:
        messagebox.showwarning("Warning", "กรุณาสร้างโจทย์ก่อน! (Please generate a puzzle first!)")
        return

    ok = True
    for i in range(SIZE):
        for j in range(SIZE):
            if original_puzzle[i][j] != 0:
                continue

            e = entries[i][j]
            val = e.get()
            orig_bg = BG_GRID_1 if (i//BOX + j//BOX) % 2 == 0 else BG_GRID_2

            if val.isdigit():
                if int(val) == solution_board[i][j]:
                    e.config(bg=orig_bg)
                else:
                    flash(e, orig_bg)
                    ok = False
            else:
                if val != "":
                    flash(e, orig_bg)
                ok = False
    
    if ok:
        messagebox.showinfo("Sudoku", "ถูกต้อง! ยินดีด้วย (Correct! Well done!)")

# =======================
# CONTROL PANEL (SIDEBAR)
# =======================
side_panel = tk.Frame(main_container, bg=BG_CARD, padx=20, pady=20, bd=0)
side_panel.pack(side="right", fill="both", expand=True)

def create_styled_button(parent, text, command, color=ACCENT):
    btn = tk.Button(parent, text=text, command=command, font=FONT_BOLD,
                    bg=color, fg="white", activebackground=color,
                    activeforeground="white", bd=0, cursor="hand2",
                    padx=15, pady=8)
    return btn

# Settings Section
tk.Label(side_panel, text="SETTINGS (ตั้งค่า)", font=FONT_BOLD, bg=BG_CARD, fg=TEXT_LIGHT).pack(anchor="w", pady=(0, 10))

# Mode Selection
mode_frame = tk.Frame(side_panel, bg=BG_CARD)
mode_frame.pack(fill="x", pady=5)
tk.Label(mode_frame, text="Board Type (ขนาด):", font=FONT_MAIN, bg=BG_CARD, fg=TEXT_DARK).pack(side="left")
mode_var = tk.StringVar(value="Normal")
mode_menu = tk.OptionMenu(mode_frame, mode_var, "Normal", "Easy", command=set_mode)
mode_menu.config(bg=BG_CARD, font=FONT_MAIN, relief="flat", bd=1)
mode_menu.pack(side="right")

# Clues Selection
clue_frame = tk.Frame(side_panel, bg=BG_CARD)
clue_frame.pack(fill="x", pady=5)
tk.Label(clue_frame, text="Clues (ตัวเลขเริ่มต้น):", font=FONT_MAIN, bg=BG_CARD, fg=TEXT_DARK).pack(side="left")
clue_entry = tk.Entry(clue_frame, width=5, font=FONT_MAIN, justify="center")
clue_entry.insert(0, "30")
clue_entry.pack(side="right")

# Algorithm Selection
algo_frame = tk.Frame(side_panel, bg=BG_CARD)
algo_frame.pack(fill="x", pady=5)
tk.Label(algo_frame, text="Algorithm (อัลกอริทึม):", font=FONT_MAIN, bg=BG_CARD, fg=TEXT_DARK).pack(side="left")
algo_var = tk.StringVar(value="Fast")
algo_menu = tk.OptionMenu(algo_frame, algo_var, "Normal", "Fast")
algo_menu.config(bg=BG_CARD, font=FONT_MAIN, relief="flat", bd=1)
algo_menu.pack(side="right")

tk.Frame(side_panel, height=2, bg=BG_MAIN).pack(fill="x", pady=20)

# Actions Section
tk.Label(side_panel, text="ACTIONS (จัดการ)", font=FONT_BOLD, bg=BG_CARD, fg=TEXT_LIGHT).pack(anchor="w", pady=(0, 10))

btn_generate = create_styled_button(side_panel, "GENERATE (สร้างโจทย์)", generate)
btn_generate.pack(fill="x", pady=5)

btn_solve = create_styled_button(side_panel, "SOLVE (แก้โจทย์ AI)", solve_gui)
btn_solve.pack(fill="x", pady=5)

btn_check = create_styled_button(side_panel, "CHECK (ตรวจสอบ)", check, color=SUCCESS)
btn_check.pack(fill="x", pady=5)

btn_reset = create_styled_button(side_panel, "RESET (ล้างกระดาน)", reset_board, color=TEXT_LIGHT)
btn_reset.pack(fill="x", pady=5)

# Status Section
tk.Frame(side_panel, height=2, bg=BG_MAIN).pack(fill="x", pady=20)
tk.Label(side_panel, text="STATISTICS (สถิติ)", font=FONT_BOLD, bg=BG_CARD, fg=TEXT_LIGHT).pack(anchor="w", pady=(0, 10))

result = tk.Label(side_panel, text="Ready (พร้อมใช้งาน)", font=FONT_MAIN, bg=BG_CARD, fg=ACCENT, wraplength=150, justify="left")
result.pack(anchor="w")

build_grid()
root.mainloop()
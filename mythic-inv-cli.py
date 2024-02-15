import os
import curses
import curses.textpad
import shutil
import logging
from logging.handlers import RotatingFileHandler
import yaml

log_filename = 'locator.log'
# Limit log file to 2 GB (2 * 1024 * 1024 * 1024 bytes)
log_filesize = 1 * 1024 * 1024 * 1024

# Setting up RotatingFileHandler
file_handler = RotatingFileHandler(log_filename, maxBytes=log_filesize, backupCount=3)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

logging.basicConfig(level=logging.DEBUG, handlers=[file_handler])

# let us read world_folder from config.yml

with open('config.yml', 'r') as file:
    config = yaml.safe_load(file)

if not config:
    config = {}

world_folder = config.get('world_folder', './world/data')

# if the world_folder doens't exist, create it
def ensure_dir_exists(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

ensure_dir_exists(world_folder)

os.environ.setdefault('ESCDELAY', '1')
# Initialize curses
stdscr = curses.initscr()
curses.noecho()
curses.cbreak()
stdscr.keypad(True)
curses.start_color()
curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)  # text in black, bg in white
if os.name == 'posix':
    curses.set_escdelay(1)
os.environ.setdefault('ESCDELAY', '1')

def display_content(win, path, selected_idx, offset):
    if path != world_folder:
        files_and_dirs =  ['..']
    else:
        files_and_dirs = []
    files_and_dirs += os.listdir(path)  # Add '..' at the top
    max_y, max_x = win.getmaxyx()  # Get the dimensions of the window
    for idx, item in enumerate(files_and_dirs[offset:]):
        if idx >= max_y - 2:  # Reserve one line for the footer
            break  # Stop if we reach the maximum y dimension
        display_str = item if len(item) <= max_x else item[:max_x - 3] + "..."
        try:
            if idx + offset == selected_idx:
                win.addstr(idx + 1, 1, display_str, curses.color_pair(1))
            else:
                win.addstr(idx + 1, 1, display_str)
        except curses.error:
            pass  # Ignore any errors related to screen size


# Perform a search in all subdirectories and files
def search_files(start_path, query):
    matches = []
    for root, dirs, files in os.walk(start_path):
        for name in dirs + files:
            if query.lower() in name.lower():
                matches.append(os.path.join(root, name))
    return matches

def confirmation_prompt(win):
    win.addstr(0, 0, "Are you sure you want to delete? [Y/N]")
    win.addstr(1, 0, "> Yes")
    win.addstr(2, 0, "  No")
    selected_option = 0  # 0 for Yes, 1 for No
    while True:
        c = win.getch()
        if c == curses.KEY_DOWN:
            selected_option = 1
        elif c == curses.KEY_UP:
            selected_option = 0
        elif c == ord('\n'):  # Enter key
            return selected_option == 0
        elif c == 27:  # Escape key
            return False

        win.addstr(1, 0, "> Yes" if selected_option == 0 else "  Yes")
        win.addstr(2, 0, "> No"  if selected_option == 1 else "  No ")



def main(stdscr):
    global item_to_move
    item_to_move = None
    default_footer = "Press 'h' for help"
    footer = default_footer
    current_path = world_folder
    selected_idx = 0
    offset = 0  # Added an offset for scrolling
    # top_idx = 0  # Add this line
    search_mode = False  # True when the user is in "search mode"
    search_results = []
    search_query = ""
    curses.curs_set(0)

    move_mode = False

    while True:
        stdscr.clear()
        # Get terminal dimensions
        max_y, max_x = stdscr.getmaxyx()
        logging.debug(f"max_y: {max_y}, max_x: {max_x}")
        try:
            relative_path = current_path.replace(world_folder, "", 1) if current_path.startswith(world_folder) else current_path
            header = f"@{relative_path[:max_x - 14]}"
            stdscr.addstr(0, 0, header)  # Truncate if necessary
            stdscr.addstr(max_y - 1, 0, footer)
        except curses.error:
            logging.debug("Error: Screen size too small")
            pass  # Ignore any errors related to screen size
        # stdscr.addstr(0, 0, f"Current path: {current_path}")

        if not search_mode:
            display_content(stdscr, current_path, selected_idx, offset)
        else:
            try:
                stdscr.addstr(1, 0, f"Search: {search_query[:max_x - 8]}")  # Truncate if necessary
            except curses.error:
                pass  # Ignore any errors related to screen size

            for idx, path in enumerate(search_results):
                if idx >= max_y - 2:  # Leave space for instructions and search query
                    break  # Stop if we reach the maximum y dimension
                display_str = path if len(path) <= max_x else path[:max_x - 3] + "..."
                try:
                    if idx == selected_idx:
                        stdscr.addstr(idx + 2, 1, display_str, curses.color_pair(1))
                    else:
                        stdscr.addstr(idx + 2, 1, display_str)
                except curses.error:
                    pass  # Ignore any errors related to screen size

        max_y, max_x = stdscr.getmaxyx()

        c = stdscr.getch()

        if current_path != world_folder:
            files_and_dirs =  ['..']  # Add '..' at the top
        else:
            files_and_dirs = []
        files_and_dirs += os.listdir(current_path)

        # Quit the program
        if c == ord("q"):
            break

        elif c == ord("s") and (not search_mode):
            search_mode = not search_mode  # Toggle search mode
            search_query = ""
            selected_idx = 0

            if search_mode:
                curses.echo()

        elif search_mode:
            if c == 27:  # Escape key
                search_mode = False  # Toggle off search mode
                curses.noecho()
                search_query = ""
                selected_idx = 0
            elif c == ord("\n"):
                if 0 <= selected_idx < len(search_results):
                    selected_item = search_results[selected_idx]
                    if os.path.isdir(selected_item):
                        current_path = selected_item
                    elif os.path.isfile(selected_item):
                        current_path = os.path.dirname(selected_item)
                    selected_idx = 0
                    offset = 0
                    search_mode = False
                    curses.noecho()
            elif c == 8 or c == curses.KEY_BACKSPACE or c == 127:  # Backspace/Delete key
                search_query = search_query[:-1]
                stdscr.addstr(1, len("Search: ") + len(search_query), " ")
            elif c == curses.KEY_DOWN:
                selected_idx = min(selected_idx + 1, len(search_results) - 1)
            elif c == curses.KEY_UP:
                selected_idx = max(selected_idx - 1, 0)
            elif c >= 32 and c <= 126:  # Only add printable characters to the query
                search_query += chr(c)
            search_results = search_files(world_folder, search_query)
            # selected_idx = 0  # Reset index after each search query update; you can comment this line if you don't want it to reset

        elif c == ord("x") and move_mode:
            # let us consider the item_to_move item as suspense and move it to the ./Suspense folder inside world_folder
            destination_folder_path = os.path.join(world_folder, 'Suspense')
            ensure_dir_exists(destination_folder_path)
            logging.debug(f"Destination folder: {destination_folder_path}")
            if os.path.isdir(destination_folder_path):
                full_dest_path = os.path.join(destination_folder_path, os.path.basename(item_to_move)) 
                logging.debug(f"Moving {item_to_move} to {full_dest_path}")
                shutil.move(item_to_move, full_dest_path)
            else:
                logging.debug(f"Destination folder {destination_folder_path} does not exist.")
            # make sure get out of move mode
            move_mode = False
            item_to_move = None
            log_str = f"Moved item. Move mode deactivated."
            logging.debug(log_str)
            footer = log_str

        elif c == ord('m'):  # The user pressed 'm'
            if not move_mode:
                # Activate move mode and store the selected item's full path
                move_mode = True
                next_folder = ['..'] + os.listdir(current_path)
                item_to_move = os.path.join(current_path, next_folder[selected_idx]) if selected_idx < len(next_folder) else None
                log_str = f"Move mode activated. Selected: {item_to_move}"
                logging.debug(log_str)
                footer = log_str
            else:
                # Deactivate move mode and move the file
                move_mode = False
                if item_to_move:
                    destination_folder_path = current_path
                    logging.debug(f"Destination folder: {destination_folder_path}")
                    if os.path.isdir(destination_folder_path):
                        full_dest_path = os.path.join(destination_folder_path, os.path.basename(item_to_move)) 
                        logging.debug(f"Moving {item_to_move} to {full_dest_path}")
                        shutil.move(item_to_move, full_dest_path)

                    item_to_move = None
                    log_str = f"Moved item. Move mode deactivated."
                    logging.debug(log_str)
                    footer = log_str
        elif c == ord('c'):  # The user pressed 'c'
            if len(os.listdir(current_path)) + 3 < max_y:  # Adding +3 to keep a gap for the footer
                stdscr.addstr(len(os.listdir(current_path)) + 2 - offset, 1, "New item name: ")
            else:
                stdscr.addstr(max_y - 2, 1, "New item name: ")  # Display it one row above the footer
            curses.echo()
            new_item_name = stdscr.getstr().decode('utf-8')
            curses.noecho()

            new_item = new_item_name.strip()
            if new_item and not os.path.exists(os.path.join(current_path, new_item)):
                with open(os.path.join(current_path, new_item), "w") as f:
                    f.write(" ")
            else:
                stdscr.addstr(max_y - 1, 1, "Invalid name or item exists.")  # Error message on the footer line

        elif c == ord('d'):
            next_folder = files_and_dirs  # Add '..' at the top
            if next_folder[selected_idx] == '..':
                stdscr.addstr(max_y - 3, 0, "Cannot delete parent directory!")
                continue

            selected_item = next_folder[selected_idx]
            selected_item_path = os.path.join(current_path, selected_item)

            # Create a new window for confirmation
            confirm_win = curses.newwin(3, 40, max_y//2, max_x//2 - 20)
            confirm_win.keypad(True)
            if confirmation_prompt(confirm_win):
                if os.path.isdir(selected_item_path):
                    shutil.rmtree(selected_item_path)  # Delete directory and all its contents
                elif os.path.isfile(selected_item_path):
                    os.remove(selected_item_path)
                selected_idx = max(selected_idx - 1, 0)
        elif c == ord('r'):  # The user pressed 'r' for renaming
            next_folder = ['..'] + os.listdir(current_path)  # Add '..' at the top
            if selected_idx == 0:
                footer = "Cannot rename parent directory!"
                continue

            selected_item = next_folder[selected_idx]
            selected_item_path = os.path.join(current_path, selected_item)
            
            footer = "Rename to: "
            stdscr.addstr(max_y - 1, 0, footer)
            stdscr.refresh()
            # Create a sub-window and a textbox at the footer location
            textbox_win = curses.newwin(1, 60, max_y - 1, len(footer))
            textbox_win.addstr(0, 0, selected_item)  # Pre-fill with the current name
            textbox = curses.textpad.Textbox(textbox_win, insert_mode=True)
            curses.curs_set(1)  # Show cursor
            new_name = textbox.edit().strip()  # Capture the edited text
            curses.curs_set(0)  # Hide cursor

            new_item_path = os.path.join(current_path, new_name)
            if new_name and not os.path.exists(new_item_path):
                os.rename(selected_item_path, new_item_path)
                footer = f"Renamed to {new_name}"
            else:
                footer = "Invalid name or item already exists."


        elif c == ord("h"):
            stdscr.clear()
            stdscr.addstr(0, 0, "'c': create item | 'n' : new location/container")
            stdscr.addstr(1, 0, "'s': search      | 'd' : delete")
            stdscr.addstr(2, 0, "'q': quit        | 'esc' : escape to normal mode")
            stdscr.addstr(3, 0, "'m': move mode   | 'r' : rename")
            stdscr.addstr(5, 0, "move mode:")
            stdscr.addstr(6, 0, "m: drop item     | x: move to suspense")
            stdscr.getch()
        elif c == ord("n"):
            curses.echo()
            stdscr.addstr(len(os.listdir(current_path)) + 2, 1, "New location/container name: ")
            new_item = stdscr.getstr().decode("utf-8")

            # Create a new directory
            new_item_path = os.path.join(current_path, new_item)
            os.makedirs(new_item_path, exist_ok=True)
            curses.noecho()

        elif c == curses.KEY_DOWN:
            if not search_mode:
                selected_idx = min(selected_idx + 1, len(os.listdir(current_path)))
                if selected_idx - offset >= max_y - 2:
                    offset += 1
            else:
                selected_idx = min(selected_idx + 1, len(os.listdir(current_path)))
                if selected_idx > top_idx + max_y - 2:
                    top_idx = selected_idx - (max_y - 2)

        elif c == curses.KEY_UP:
            if not search_mode:
                selected_idx = max(selected_idx - 1, 0)
                if selected_idx < offset:
                    offset = max(0, offset - 1)
            else:
                selected_idx = max(selected_idx - 1, 0)
                if selected_idx < top_idx:
                    top_idx = selected_idx

        # Navigate deeper with 'Enter'
        elif c == ord("\n"):
            try:
                
                next_folder = files_and_dirs
                selected_item = next_folder[selected_idx]

                # Formulate the absolute path for the selected item
                selected_item_path = os.path.join(current_path, selected_item)

                if os.path.isdir(selected_item_path):  # Check if the selected item is a directory
                    if selected_item == '..':
                        # Navigate back to parent folder
                        current_path = os.path.dirname(current_path)
                    else:
                        # Navigate into the selected folder
                        current_path = selected_item_path

                    selected_idx = 0  # Reset selected index
                elif os.path.isfile(selected_item_path):  # Check if the selected item is a file
                    stdscr.clear()
                    stdscr.addstr(0, 0, f"Contents of {selected_item}:")
                    
                    with open(selected_item_path, 'r') as f:
                        content = f.read()
                    
                    stdscr.addstr(1, 0, content)
                    stdscr.addstr(2, 0, "Press any key to continue...")
                    stdscr.getch()  # Wait for any key
                    
            except IndexError:
                pass
        stdscr.refresh()

curses.wrapper(main)

curses.endwin()

import os
import re
import json
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from collections import OrderedDict
from datetime import datetime
import subprocess
from copy import deepcopy

#
# -----------------------------------------------------------------------
# Script Name: Ultimate FortiClient Log Filter Tool
# Description: Review logs quicker for the exact things you want to see.
#              FortiClient logs a lot of information and sometimes you 
#              only need part of it.
#              Quickly filter FortiClient logs based on specific criteria 
#              like source name (srcname), destination IP(dstip), url, 
#              and other criteria via checkboxes.
# Author: cr0m
# Created Date: April 22, 2024
# Updated Date: May 28rd, 2024
# Version: 0.4
# Usage: Start the tool, load a log file, configure filters, and save the output.
# -----------------------------------------------------------------------
#
# Features include:
# 1. Load a log file to parse key-value pairs from each log entry.
# 2. Display checkboxes for each unique key found in the log file, to select which keys to include in the output.
# 3. Filter Text - Filter by or filter out text. Only entries containing or not containing this text.
# 4. Lines Before/After - Specify a number of contextual lines to include around each matching entry in the output.
# 5. Save filtered results to a new file with a timestamp in the filename.
# 6. Automatically opens the saved file in Notepad++ for quick viewing and further editing. 
# 7. Memory feature - Saves filter checkboxes to config.txt
# 8. Dropdown to select from the last three checkbox states
#
# Usage:
# - Start the tool and use the "Load Log File" button to load the desired log file.
# - Select or deselect keys to include in the output by checking the corresponding boxes.
# - If needed, enter a filter text and specify whether to include or exclude entries with this text.
# - Specify the number of lines before and after matching entries to include for additional context.
# - Click "Save Selected" to save the filtered entries to a new file and automatically open this file in Notepad++.
# - This will also save the current checkboxes selected/not selected to config.txt for favorite keys

# Initialize a variable to keep track of the last saved state
last_saved_state = None

# Function to compare current checkbox state with the last saved state
def has_state_changed(current_state, last_state):
    if last_state is None:
        return True
    return current_state != last_state

# Load the last three checkbox states from a file
def load_checkbox_states():
    try:
        with open('checkbox_states.txt', 'r') as f:
            return json.load(f)  # Load the JSON array from file
    except FileNotFoundError:
        return []
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return []

# Function to parse the log file and extract key-value pairs
def parse_log_file(filepath):
    """ Parse the log file and extract key-value pairs from each line, preserving the prefix. """
    data = []  # List to store parsed data
    keys_order = OrderedDict()  # Ordered dictionary to maintain the order of keys
    with open(filepath, 'r') as file:
        lines = file.readlines()  # Read all lines from the log file

    for index, line in enumerate(lines):
        if 'date=' in line:
            prefix_part, kv_part = line.split('date=', 1)  # Split into prefix and key-value pairs
            prefix_part = prefix_part.strip()  # Strip any extra whitespace
            kv_part = 'date=' + kv_part.strip()  # Reconstruct the key-value string
        else:
            prefix_part = line.strip()  # If 'date=' is not found, treat the whole line as prefix
            kv_part = ""

        pattern = re.compile(r'\b(\w+)=(\"[^\"]*\"|\S+)')  # Regular expression pattern for key-value pairs
        if kv_part:
            entry = {match.group(1): match.group(2) for match in pattern.finditer(kv_part)}  # Parse key-value pairs
        else:
            entry = {}

        data.append((prefix_part, entry, index))  # Append parsed data along with the index for context
        for key in entry.keys():
            keys_order[key] = None  # Keep track of all unique keys in their first encountered order

    return data, keys_order

def save_results(selected_keys, all_data, original_file, filter_text, exclude_filter, context_lines):
    """ Save the selected key-value pairs to a new file with timestamp, then open it in Notepad++. """
    timestamp = datetime.now().strftime("%H%M%S")  # Generate a timestamp for the new filename

    # Get the directory of the original file
    original_file_dir = os.path.dirname(original_file)

    # Construct the new filename
    new_filename = f"{os.path.splitext(os.path.basename(original_file))[0]}_results_{timestamp}.txt"

    # Construct the full path for the new file
    new_file_path = os.path.join(original_file_dir, new_filename)

    with open(new_file_path, 'w') as file:
        for prefix, line, idx in all_data:
            # Check if the line matches the filter criteria
            contains_filter = filter_text.lower() in prefix.lower() or any(filter_text.lower() in v.lower() for v in line.values())
            if (contains_filter and not exclude_filter) or (not contains_filter and exclude_filter):
                # Include context lines around the matched line
                start_idx = max(0, idx - context_lines)
                end_idx = min(len(all_data), idx + context_lines + 1)
                for context_idx in range(start_idx, end_idx):
                    prefix, line, _ = all_data[context_idx]
                    # Construct a string containing the prefix and selected key-value pairs
                    selected_data = prefix + ' ' + ' '.join(f"{k}={v}" for k, v in line.items() if k in selected_keys)
                    file.write(selected_data + '\n')  # Write the formatted data to the file

    # Open the file in Notepad++
    try:
        notepad_plus_path = "C:\\Program Files\\Notepad++\\notepad++.exe"
        subprocess.run([notepad_plus_path, new_file_path])  # Use subprocess to open Notepad++
    except Exception as e:
        messagebox.showerror("Error", f"Failed to open Notepad++: {e}")  # Show an error if Notepad++ cannot be opened

# Save the current checkbox state and keep only the last three states
def save_checkbox_states():
    global last_saved_state
    state = {key: var.get() for key, var in checkboxes.items()}
    if not has_state_changed(state, last_saved_state):
        print("No changes detected. Skipping save.")
        return
    states = load_checkbox_states()
    states.append(state)
    states = states[-3:]  # Keep only the last three states
    with open('checkbox_states.txt', 'w') as f:
        json.dump(states, f, indent=4)  # Save states as a JSON array
    last_saved_state = deepcopy(state)

# Function to update checkboxes based on the selected state
def update_checkboxes(event):
    """ Update checkboxes based on the selected state. """
    selection = combobox.current()
    states = load_checkbox_states()
    if states and selection < len(states):
        state = states[selection]
        if isinstance(state, dict):
            for key, var in checkboxes.items():
                var.set(state.get(key, False))

def bind_combobox():
    combobox.bind("<<ComboboxSelected>>", update_checkboxes)

# Load the last three checkbox states from a file
def load_checkbox_states():
    try:
        with open('checkbox_states.txt', 'r') as f:
            return json.load(f)  # Load the JSON array from file
    except FileNotFoundError:
        return []
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return []

# Update the dropdown with the last three checkbox states
def update_combobox():
    states = load_checkbox_states()
    names = ["Last " + str(i+1) for i in range(len(states))]
    names.reverse()  # Reverse the list so the most recent is first
    combobox['values'] = names
    if states:
        combobox.set("Last 1")  # Set the default value to "Last 1"

# Load file and update checkboxes based on keys found in the log file
def load_file():
    """ Load a log file and update the GUI with available keys. """
    global all_data, filepath, last_saved_state
    filepath = filedialog.askopenfilename()  # Open a file dialog to select a log file
    if not filepath:
        return  # Return if no file was selected
    all_data, keys_order = parse_log_file(filepath)  # Parse the selected file
    saved_states = load_checkbox_states()  # Load previously saved checkbox states
    if saved_states:
        last_saved_state = deepcopy(saved_states[-1])
    else:
        last_saved_state = None
    filename_label.config(text="FileName: " + os.path.basename(filepath))  # Update the filename label

    for widget in scrollable_frame.winfo_children():
        widget.destroy()  # Clear all previous checkbox widgets
    checkboxes.clear()
    column = 0
    row = 0
    for key in keys_order.keys():
        checked = False
        if saved_states:
            state = saved_states[-1]
            if isinstance(state, dict):
                checked = state.get(key, False)

        var = tk.BooleanVar(value=checked)
        cb = tk.Checkbutton(scrollable_frame, text=key, variable=var)
        cb.grid(row=row, column=column, sticky='w')  # Arrange checkboxes in a grid layout
        checkboxes[key] = var  # Add checkbox variable to the dictionary

        # Update row and column for next checkbox
        column += 1
        if column > 3:  # Change this number to set how many checkboxes per row
            column = 0
            row += 1


# Save filtered results and checkbox states
def save_filtered_results():
    """ Save the filtered results and the current checkbox states to a file. """
    selected_keys = [k for k, v in checkboxes.items() if v.get()]  # Collect selected keys
    filter_text = filter_entry.get()  # Get the filter text
    exclude_filter = filter_out_var.get()  # Check if the 'exclude filter' option is selected
    context_lines = int(lines_context_entry.get() or 0)  # Default to 0 if empty
    save_results(selected_keys, all_data, filepath, filter_text, exclude_filter, context_lines)  # Save results
    save_checkbox_states()  # Save checkbox states
    update_combobox()  # Update combobox after saving states

# GUI Setup
root = tk.Tk()
root.title("Ultimate FortiClient EMS Log Filter v.4")
root.geometry("450x650")

# Frame to contain the Load button and combobox
top_frame = tk.Frame(root)
top_frame.pack(pady=3)

# Button to load the log file
load_button = tk.Button(top_frame, text="Load Log File", command=load_file)
load_button.grid(row=0, column=0, padx=5)

# Label to display the loaded filename
filename_label = tk.Label(root, text="No file loaded")
filename_label.pack(pady=0)

# Frame for labels and combobox
label_frame = tk.Frame(root)
label_frame.pack(anchor='w')

# Label for "Memory"
memory_label = tk.Label(label_frame, text="Prev. Filters:")
memory_label.pack(side='left', padx=5)

# Create a dropdown for the last three checkbox states
combobox = ttk.Combobox(label_frame, width=10, state='readonly')
combobox.pack(side='left')

# Horizontal line
line = tk.Frame(root, height=1, bg='black')
line.pack(fill='x', padx=5, pady=5)

# Frame to contain the scrollable canvas and scrollbars
frame = tk.Frame(root)
frame.pack(fill='both', expand=True)

# Canvas for the scrollable content
canvas = tk.Canvas(frame)
scrollbar_x = tk.Scrollbar(frame, orient='horizontal', command=canvas.xview)
scrollbar_y = tk.Scrollbar(frame, orient='vertical', command=canvas.yview)
scrollable_frame = tk.Frame(canvas)

scrollbar_x.pack(side='bottom', fill='x')
scrollbar_y.pack(side='right', fill='y')
canvas.pack(side='left', fill='both', expand=True)
canvas.configure(xscrollcommand=scrollbar_x.set, yscrollcommand=scrollbar_y.set)
canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

# Frame to contain the filter options
filter_frame = tk.Frame(root)
filter_frame.pack(side=tk.LEFT, padx=50, pady=0, fill='both', anchor='n')

# Label and entry for filter text
filter_label = tk.Label(filter_frame, text="Filter Text:")
filter_label.pack(side=tk.TOP, fill='x', pady=(0, 0))
filter_entry = tk.Entry(filter_frame)
filter_entry.pack(side=tk.TOP, fill='x')

# Checkbox to toggle 'filter out' mode
filter_out_var = tk.BooleanVar()
filter_out_checkbox = tk.Checkbutton(filter_frame, text="Filter out", variable=filter_out_var)
filter_out_checkbox.pack(side=tk.TOP, fill='x')

# Label and entry for the number of context lines
lines_context_label = tk.Label(root, text="# Lines Before/After:")
lines_context_label.pack(pady=0)
lines_context_entry = tk.Entry(root)
lines_context_entry.pack(pady=0)

# Button to save the selected results
save_button = tk.Button(root, text="Save & View", command=save_filtered_results)
save_button.pack(pady=3)

# Bind the function to the combobox
bind_combobox()

# Update the dropdown when the GUI starts
update_combobox()

# Dictionary to store the checkbox variables
checkboxes = {}

# Start the GUI event loop
root.mainloop()

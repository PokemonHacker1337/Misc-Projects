import os
import stat
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import xml.etree.ElementTree as ET

def find_wizard101_folder(start_folder):
    for root, dirs, files in os.walk(start_folder):
        if "config.xml" in files and "WizardGraphicalClient.exe" in files:
            return root
    return None

def get_config_path():
    default_path = "C:\\ProgramData\\Kingsisle Entertainment\\Wizard101\\Bin"
    if os.path.exists(os.path.join(default_path, "config.xml")) and os.path.exists(os.path.join(default_path, "WizardGraphicalClient.exe")):
        return default_path

    saved_path = load_saved_path()
    if saved_path:
        return saved_path

    response = messagebox.askyesno("Directory Search", "Would you like to manually select the Wizard101 folder?")
    if response:
        selected_path = filedialog.askdirectory(title="Select Wizard101 folder")
        if os.path.exists(os.path.join(selected_path, "config.xml")) and os.path.exists(os.path.join(selected_path, "WizardGraphicalClient.exe")):
            save_path(selected_path)
            return selected_path
    else:
        root_directory = "C:\\"
        print("Searching. Please wait...")
        found_path = find_wizard101_folder(root_directory)
        input("Path found. Press any key to continue.")
        if found_path:
            save_path(found_path)
            return found_path

    messagebox.showerror("File Not Found", "Wizard101 config.xml not found.")
    return None

def save_path(path):
    with open("wizard101_path.txt", "w") as file:
        file.write(path)

def load_saved_path():
    if os.path.exists("wizard101_path.txt"):
        with open("wizard101_path.txt", "r") as file:
            return file.read().strip()
    return None

def parse_xml_and_get_records(config_path):
    xml_path = os.path.join(config_path, "config.xml")
    tree = ET.parse(xml_path)
    root = tree.getroot()

    records = []
    for record in root.findall(".//InputMappings/RECORD"):
        if any(record.find(tag) is not None for tag in ['Ctrl', 'Alt', 'Shift']) and (record.find('InputType') is None or record.find('InputType').text != 'Mouse'):
            records.append(record)
    return records, root

def setup_checkbox(parent, tag, record):
    element = record.find(tag)
    is_checked = element is not None and element.text == '1'
    var = tk.IntVar(value=1 if is_checked else 0)
    chk = tk.Checkbutton(parent, text=tag, variable=var)
    chk.pack(side='left', padx=(0, 10))
    return var  # Return the variable for potential future use

def create_gui(records, config_path, xml_root):
    root = tk.Tk()
    root.title("Wizard101 Config Editor")
    root.geometry("500x375")

    # Main frame for the scrollable area
    main_frame = ttk.Frame(root)
    main_frame.pack(side="top", fill="both", expand=True)

    # Canvas and scrollbar for the scrollable area
    canvas = tk.Canvas(main_frame)
    scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)

    scrollable_frame = ttk.Frame(canvas)
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Dictionary to hold variables for checkboxes and key entries
    checkbox_vars = {}

    for record in records:
        event_name = record.find('Event').text if record.find('Event') is not None else "Unknown Event"
        key_value = record.find('Key').text if record.find('Key') is not None else ""
        
        frame = ttk.Frame(scrollable_frame)
        frame.pack(padx=10, pady=5, fill='x')

        ttk.Label(frame, text=event_name).pack(side='left', padx=(0, 10))

        key_entry = ttk.Entry(frame)
        key_entry.insert(0, key_value)
        key_entry.pack(side='left')
        
        checkbox_vars[event_name] = {
            'Ctrl': setup_checkbox(frame, 'Ctrl', record),
            'Alt': setup_checkbox(frame, 'Alt', record),
            'Shift': setup_checkbox(frame, 'Shift', record),
            'KeyEntry': key_entry
        }
    def set_read_only_flag(file_path, set_flag=True):
        file_attr = os.stat(file_path).st_mode
        if set_flag:
            os.chmod(file_path, file_attr | stat.S_IREAD)
        else:
            os.chmod(file_path, file_attr & ~stat.S_IREAD)
    def save_changes():
        config_file_path = os.path.join(config_path, "config.xml")
        try:
            set_read_only_flag(config_file_path, False)
            for event_name, controls in checkbox_vars.items():
                record = next((rec for rec in records if rec.find('Event').text == event_name), None)
                if record:
                    key_element = record.find('Key')
                    if key_element is not None:
                        key_element.text = controls['KeyEntry'].get()

                    for key in ['Ctrl', 'Alt', 'Shift']:
                        checkbox_var = controls[key]
                        element = record.find(key)
                        if element is not None:
                            element.text = '1' if checkbox_var.get() == 1 else '0'

                tree = ET.ElementTree(xml_root)
                tree.write(os.path.join(config_path, "config.xml"), encoding="utf-8")
            messagebox.showinfo("Success", "Changes saved successfully.")
            set_read_only_flag(config_file_path, True)
        except Exception as e:
            messagebox.showerror("Error", f"Error saving changes: {e}")
            set_read_only_flag(config_file_path, True)

    # Save button at the bottom
    save_button = ttk.Button(root, text="Save Changes", command=save_changes)
    save_button.pack(side="bottom", pady=10)

    root.mainloop()


def main_app():
    config_path = get_config_path()
    if config_path:
        records, xml_root = parse_xml_and_get_records(config_path)
        if records:
            create_gui(records, config_path, xml_root)
        else:
            print("No valid records found in XML.")
    else:
        print("Config path not found.")

if __name__ == "__main__":
    main_app()

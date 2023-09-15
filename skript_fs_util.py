import os


def entries_in_directory(directory):
    entries = []
    for root, dirs, files in os.walk(directory):
        for entry in dirs + files:
            entry_path = os.path.join(root, entry)
            entries.append(entry_path)
    return entries


def file_exists_in_directory(directory, path_item):
    matching_entries = [entry for entry in entries_in_directory(directory) if path_item in entry]

    matching_files = [entry for entry in matching_entries if
                      os.path.isfile(entry) and entry.endswith(os.path.sep + path_item)]
    matching_folders = [
        entry for entry in matching_entries if os.path.isdir(entry) and entry.endswith(os.path.sep + path_item)
    ]

    if not matching_entries:
        return None
    elif len(matching_folders) == 1 and len(matching_files) == 0:
        return matching_folders[0]
    elif len(matching_files) == 1 and len(matching_folders) == 0:
        return matching_files[0]
    elif len(matching_files) == 0 and len(matching_folders) == 0:
        return None
    else:
        raise RuntimeError(f"Multiple matches found for '{path_item}':\n{matching_entries}")


def create_dirs_if_needed_for(arbitrary_path):

    # Split the path into individual components
    path_components = [component for component in arbitrary_path.split('/') if component]

    # Initialize a base directory
    base_directory = ''
    if arbitrary_path.startswith(os.sep):
        base_directory = os.sep

    # Iterate over the components and create directories as needed
    for component in path_components:
        # Build the full path
        current_path = os.path.join(base_directory, component)

        # Check if the directory exists
        if not os.path.exists(current_path):
            # If it doesn't exist, create it
            print(f"Creating dir {component} in {os.path.dirname(current_path)}")
            os.makedirs(current_path)

        # Update the base directory for the next iteration
        base_directory = current_path

import os
import hashlib

ALLOWED_EXTENSIONS = (".py", ".html", ".css", ".js")

RESTRICTED_FOLDERS = {
    ".git",
    "venv",
    "__pycache__",
    "node_modules",
    ".vscode",
    ".idea",
    "migrations",
    "Include",
    "Lib",
    "Scripts"
}

OUTPUT_FILE = "output.txt"


def get_file_hash(content):
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def parse_existing_output(output_path):
    if not os.path.exists(output_path):
        return {}

    entries = {}
    current_block = []
    current_path = None
    current_hash = None

    with open(output_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("--------------------------------------------------------"):
                if current_path:
                    entries[current_path] = (current_hash, "".join(current_block))
                current_block = [line]
                current_path = None
                current_hash = None
            else:
                current_block.append(line)

                if not current_path and "\\" in line:
                    current_path = line.strip()

                if line.startswith("HASH:"):
                    current_hash = line.strip().replace("HASH:", "")

        if current_path:
            entries[current_path] = (current_hash, "".join(current_block))

    return entries


def generate_block(windows_path, file_hash, content):
    return (
        "--------------------------------------------------------\n"
        f"{windows_path}\n"
        #f"HASH:{file_hash}\n"
        "<<code:\n"
        f"{content}\n"
        ">>\n\n"
    )


def collect_and_update():
    current_folder = os.getcwd()
    output_path = os.path.join(current_folder, OUTPUT_FILE)
    current_script_name = os.path.basename(__file__)

    existing_entries = parse_existing_output(output_path)
    updated_entries = {}

    for root, dirs, files in os.walk(current_folder):

        # Skip restricted folders
        dirs[:] = [d for d in dirs if d not in RESTRICTED_FOLDERS]

        for file_name in files:

            if file_name == OUTPUT_FILE:
                continue

            if file_name == current_script_name:
                continue

            if not file_name.lower().endswith(ALLOWED_EXTENSIONS):
                continue

            full_path = os.path.join(root, file_name)
            windows_path = os.path.abspath(full_path).replace("/", "\\")

            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    content = f.read()

                file_hash = get_file_hash(content)

                if windows_path in existing_entries:
                    old_hash, old_block = existing_entries[windows_path]
                    if old_hash == file_hash:
                        updated_entries[windows_path] = old_block
                        continue

                updated_entries[windows_path] = generate_block(
                    windows_path, file_hash, content
                )

            except Exception:
                pass

    # Rewrite clean synchronized output
    with open(output_path, "w", encoding="utf-8") as out:
        for path in sorted(updated_entries):
            out.write(updated_entries[path])
    print("Done")


if __name__ == "__main__":
    collect_and_update()

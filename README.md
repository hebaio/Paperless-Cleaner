# Paperless Cleaner

A web-based tool to merge duplicate Correspondents and Document Types in Paperless-ngx.

## Features
- Connects to your Paperless-ngx instance via API.
- Lists all Correspondents and Document Types.
- Allows selecting multiple items to merge into a single target.
- Updates all affected documents to the new target.
- Deletes the old (merged) items.

## Requirements
- Python 3.14 (or compatible 3.x)
- `flask`
- `requests`

## Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Run the application:
   ```bash
   python app.py
   ```

2. Open your browser and navigate to `http://localhost:5000`.

3. Go to **Settings** and enter your Paperless-ngx API URL (e.g., `http://192.168.178.42:30070`) and your API Token.

4. Go to **Correspondents** or **Document Types** to start merging.

## How to Merge

1. Select the items you want to **remove** (merge source) using the checkboxes on the left.
2. Select the item you want to **keep** (target) using the radio button.
3. Click **Merge Selected into Target**.

**Warning:** This action cannot be undone. The source items will be deleted after their documents are moved to the target.

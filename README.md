# Paperless Cleaner

A web-based tool to merge duplicate Correspondents and Document Types in Paperless-ngx.
This is designed to be a very simple cleaning tools to remove duplicated entries created by automated tools like Paperless-AI. 

## Features
- Connects to your Paperless-ngx instance via API.
- Lists all Correspondents and Document Types.
- Finds and groups similar items automatically.
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

1. It is highly recommended to create a backup of your paperless-ngx instance (https://docs.paperless-ngx.com/administration/#backup) or using the document exporter (https://docs.paperless-ngx.com/administration/#exporter) before using paperless-cleaner. 

1. Run the application:
   ```bash
   python src/app.py
   ```

2. Open your browser and navigate to `http://localhost:5000`.

3. Go to **Settings** and enter your Paperless-ngx API URL and your API Token. Create an API token by clicking on 'My Profile' in the Web UI of your paperless-ngx instance. 

4. Go to **Correspondents** or **Document Types** to start merging.


## How to Merge

1. Select the items you want to **remove** (merge source) using the checkboxes on the left.
2. Select the item you want to **keep** (target) using the radio button.
3. Click **Merge Selected into Target**.

**Warning:** This action cannot be undone. The source items will be deleted after their documents are moved to the target.

## Find Similar Items

1. Click on **Similar** in the navigation bar.
2. Choose **Correspondents** or **Document Types**.
3. The tool will group items with similar names (e.g., "Amazon" and "Amazon DE").
4. Review the groups and merge them directly from this view.

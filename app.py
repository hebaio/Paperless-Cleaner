from flask import Flask, render_template, request, redirect, url_for, flash
from config import load_settings, save_settings
from paperless_client import PaperlessClient

app = Flask(__name__)
app.secret_key = 'supersecretkey' # Change this for production

def get_client():
    settings = load_settings()
    if not settings['api_url'] or not settings['api_token']:
        return None
    return PaperlessClient(settings['api_url'], settings['api_token'])

@app.route('/')
def index():
    client = get_client()
    if not client:
        return redirect(url_for('settings'))
    if not client.check_connection():
        flash('Could not connect to Paperless API. Please check settings.', 'danger')
        return redirect(url_for('settings'))
    return render_template('index.html')

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'POST':
        api_url = request.form.get('api_url')
        api_token = request.form.get('api_token')
        save_settings(api_url, api_token)
        flash('Settings saved.', 'success')
        return redirect(url_for('index'))
    
    current_settings = load_settings()
    return render_template('settings.html', settings=current_settings)

@app.route('/correspondents')
def correspondents():
    client = get_client()
    if not client: return redirect(url_for('settings'))
    
    try:
        items = client.get_correspondents()
        # Sort by name
        items.sort(key=lambda x: x['name'].lower())
        return render_template('merge.html', items=items, type='correspondent', title='Correspondents')
    except Exception as e:
        flash(f'Error fetching correspondents: {e}', 'danger')
        return redirect(url_for('index'))

@app.route('/document_types')
def document_types():
    client = get_client()
    if not client: return redirect(url_for('settings'))
    
    try:
        items = client.get_document_types()
        items.sort(key=lambda x: x['name'].lower())
        return render_template('merge.html', items=items, type='document_type', title='Document Types')
    except Exception as e:
        flash(f'Error fetching document types: {e}', 'danger')
        return redirect(url_for('index'))

@app.route('/merge', methods=['POST'])
def merge():
    client = get_client()
    if not client: return redirect(url_for('settings'))

    item_type = request.form.get('type')
    target_id = request.form.get('target_id')
    merge_ids = request.form.getlist('merge_ids')

    if not target_id or not merge_ids:
        flash('Please select a target and at least one item to merge.', 'warning')
        return redirect(url_for('correspondents' if item_type == 'correspondent' else 'document_types'))

    target_id = int(target_id)
    merge_ids = [int(mid) for mid in merge_ids if int(mid) != target_id]

    if not merge_ids:
        flash('No items to merge (target was excluded).', 'warning')
        return redirect(url_for('correspondents' if item_type == 'correspondent' else 'document_types'))

    try:
        count = 0
        for mid in merge_ids:
            # 1. Find documents
            if item_type == 'correspondent':
                docs = client.get_documents_by_correspondent(mid)
                doc_ids = [d['id'] for d in docs]
                # 2. Update documents
                if doc_ids:
                    client.bulk_edit_correspondent(doc_ids, target_id)
                # 3. Delete old item
                client.delete_correspondent(mid)
            elif item_type == 'document_type':
                docs = client.get_documents_by_document_type(mid)
                doc_ids = [d['id'] for d in docs]
                if doc_ids:
                    client.bulk_edit_document_type(doc_ids, target_id)
                client.delete_document_type(mid)
            count += 1
        
        flash(f'Successfully merged {count} items.', 'success')
    except Exception as e:
        flash(f'Error during merge: {e}', 'danger')

    return redirect(url_for('correspondents' if item_type == 'correspondent' else 'document_types'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

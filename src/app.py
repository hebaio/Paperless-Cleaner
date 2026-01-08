from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, Response
from config import load_settings, save_settings
from paperless_client import PaperlessClient
from similarity import find_similar_groups
from similarity_llm import find_similar_groups_llm

app = Flask(__name__)
app.secret_key = 'supersecretkey' # Change this for production


"""Web UI for cleaning and merging Paperless-ng metadata.

This module provides a small Flask application that allows the user to:
- configure Paperless API credentials
- list correspondents and document types
- preview, merge, and delete metadata items

The app delegates API operations to `PaperlessClient` (in
`paperless_client.py`) and keeps only lightweight request/response logic
and presentation glue.
"""


def get_client() -> PaperlessClient | None:
    """Create and return a configured PaperlessClient or None.

    Loads API settings from the configuration store and returns a
    `PaperlessClient` instance when both the API URL and token are
    available. Returns `None` when settings are missing so callers can
    redirect the user to the settings page.

    Returns:
        PaperlessClient | None: Configured client or None
    """
    settings = load_settings()
    if not settings['api_url'] or not settings['api_token']:
        return None
    return PaperlessClient(settings['api_url'], settings['api_token'])

@app.route('/')
def index():
    """Render the application index.

    If API settings are missing or the app cannot connect to the
    Paperless API, the user is redirected to the settings page with a
    flash message describing the problem.
    """
    client = get_client()

    if not client:
        return redirect(url_for('settings'))
    if not client.check_connection():
        flash('Could not connect to Paperless API. Please check settings.', 'danger')
        return redirect(url_for('settings'))

    return render_template('index.html')

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    """Display and update saved Paperless API settings.

    GET: show current settings
    POST: persist provided `api_url` and `api_token`, then redirect to
    the index.
    """

    if request.method == 'POST':
        api_url = request.form.get('api_url')
        api_token = request.form.get('api_token')
        
        # LLM Settings
        llm_enabled = 'true' if request.form.get('llm_enabled') == 'true' else 'false'
        llm_api_base = request.form.get('llm_api_base', '')
        llm_api_key = request.form.get('llm_api_key', '')
        llm_model = request.form.get('llm_model', '')

        save_settings(api_url, api_token, llm_enabled, llm_api_base, llm_api_key, llm_model)
        flash('Settings saved.', 'success')
        return redirect(url_for('index'))

    current_settings = load_settings()
    return render_template('settings.html', settings=current_settings)

@app.route('/correspondents')
def correspondents():
    """List correspondents for merging and deletion.

    Fetches correspondents from Paperless, sorts them by name and
    renders the merge UI. Any API errors are surfaced to the user via
    flash messages.

    Returns:
        Response: Redirect back to the relevant listing page
    """
    client = get_client()
    # If not configured, redirect to settings.
    if not client: return redirect(url_for('settings'))

    try:
        items = client.get_correspondents()
        # Sort by name for a predictable UI ordering
        items.sort(key=lambda x: x['name'].lower())
        return render_template('merge.html', items=items, type='correspondent', title='Correspondents')
    except Exception as e:
        flash(f'Error fetching correspondents: {e}', 'danger')
        return redirect(url_for('index'))

@app.route('/document_types')
def document_types() -> Response:
    """List document types for merging and deletion.
    Works similarly to `correspondents()` but for document types.

    Returns:
        Response: Redirect back to the relevant listing page
    """
    client = get_client()

    # If not configured, redirect to settings.
    if not client: return redirect(url_for('settings'))

    try:
        items = client.get_document_types()
        items.sort(key=lambda x: x['name'].lower())
        return render_template('merge.html', items=items, type='document_type', title='Document Types')
    except Exception as e:
        flash(f'Error fetching document types: {e}', 'danger')
        return redirect(url_for('index'))

@app.route('/similar/<item_type>')
def similar(item_type: str) -> Response:
    """List groups of similar items for probable merging.

    Args:
        item_type (str): Either 'correspondent' or 'document_type'

    Returns:
        Response: Rendered template with groups of similar items
    """
    client = get_client()
    if not client: return redirect(url_for('settings'))
    
    try:
        if item_type == 'correspondent':
            items = client.get_correspondents()
            title = 'Correspondents'
        elif item_type == 'document_type':
            items = client.get_document_types()
            title = 'Document Types'
        else:
            flash('Invalid item type', 'danger')
            return redirect(url_for('index'))
            
        settings = load_settings()
        method = request.args.get('method', 'algo')
        
        if method == 'llm' and settings.get('llm_enabled') == 'true':
            groups = find_similar_groups_llm(items, settings)
            title = f'{title} (LLM)'
        else:
            groups = find_similar_groups(items)
            title = f'{title} (Basic)'

        # Sort groups by size (descending) then by name of first item
        groups.sort(key=lambda g: (-len(g), g[0]['name'].lower()))
        
        return render_template('similar.html', groups=groups, type=item_type, title=f'Similar {title}', all_items=items, method=method, llm_enabled=settings.get('llm_enabled'))
    except Exception as e:
        flash(f'Error finding similar items: {e}', 'danger')
        return redirect(url_for(f'{item_type}s'))

@app.route('/merge', methods=['POST'])
def merge() -> Response:
    """Merges the selected elements (correspondents or document types).
    The route expects POST requests with form data indicating the
    target item and the list of items to merge into it. On success or failure
    the user is redirected back to the relevant listing page with a
    flash message.

    Returns:
        Response: Redirect back to the relevant listing page
    """

    # Fetch the client. If not configured, redirect to settings.
    client = get_client()
    if not client: return redirect(url_for('settings'))

    # Extract form data
    item_type = request.form.get('type')
    target_id = request.form.get('target_id')
    merge_ids = request.form.getlist('merge_ids')
    
    # Determine redirect destination
    next_url = request.form.get('next')
    default_url = url_for('correspondents' if item_type == 'correspondent' else 'document_types')
    redirect_dest = next_url if next_url else default_url

    # Basic validation, ensure we have a target and at least one source
    if not target_id or not merge_ids:
        flash('Please select a target and at least one item to merge.', 'warning')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
             return jsonify({'success': False, 'message': 'Please select a target and at least one item to merge.'}), 400
        return redirect(redirect_dest)

    target_id = int(target_id)
    # Exclude the chosen target from the list of IDs to merge
    merge_ids = [int(mid) for mid in merge_ids if int(mid) != target_id]

    if not merge_ids:
        flash('No items to merge (target was excluded).', 'warning')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
             return jsonify({'success': False, 'message': 'No items to merge (target was excluded).'}), 400
        return redirect(redirect_dest)

    try:
        count = 0
        for mid in merge_ids:
            # Step 1: find all documents referencing the source item
            if item_type == 'correspondent':
                docs = client.get_documents_by_correspondent(mid)
                doc_ids = [d['id'] for d in docs]
                # Step 2: update those documents to reference the target
                if doc_ids:
                    client.bulk_edit_correspondent(doc_ids, target_id)
                # Step 3: delete the now-unused correspondent
                client.delete_correspondent(mid)
            elif item_type == 'document_type':
                docs = client.get_documents_by_document_type(mid)
                doc_ids = [d['id'] for d in docs]
                if doc_ids:
                    client.bulk_edit_document_type(doc_ids, target_id)
                client.delete_document_type(mid)
            count += 1

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'message': f'Successfully merged {count} items.'})

        flash(f'Successfully merged {count} items.', 'success')
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': str(e)}), 500
        
        # Surface API or client errors to the user
        flash(f'Error during merge: {e}', 'danger')

    # Redirect back to the relevant listing page
    return redirect(redirect_dest)

@app.route('/delete/<item_type>/<int:item_id>', methods=['POST'])
def delete_item(item_type: str, item_id: int) -> Response:
    """Delete a metadata item (correspondent or document type).

    The route expects POST requests and will call the appropriate client
    deletion method. On success or failure the user is redirected back
    to the relevant listing and shown a flash message.

    Args:
        item_type (str): Either correspondent or document_type
        item_id (int): ID of the item to delete

    Returns:
        Response: Redirect back to the calling page
    """

    
    client = get_client()
    if not client: return redirect(url_for('settings'))

    try:
        if item_type == 'correspondent':
            client.delete_correspondent(item_id)
            flash('Correspondent deleted.', 'success')
        elif item_type == 'document_type':
            client.delete_document_type(item_id)
            flash('Document Type deleted.', 'success')
        else:
            flash('Invalid item type.', 'danger')
    except Exception as e:
        flash(f'Error deleting item: {e}', 'danger')

    return redirect(url_for('correspondents' if item_type == 'correspondent' else 'document_types'))

@app.route('/api/preview/<item_type>/<int:item_id>')
def preview_documents(item_type: str, item_id: int) -> Response:
    """Get the documents for the preview function. Will get all documents for the correspondent/document type.
    Truncates the title to max of 50 characters. 
    Also attaches the base_url of the paperless instance to build a link to the document in the templates Javascript.

    Args:
        item_type (str): Either correspondent or document_type
        item_id (int): ID of the item to get the documents for

    Returns:
        Response: JSON encoded response with documents and the base_url.
    """
    client = get_client()
    if not client: return jsonify({'error': 'Not connected'}), 401

    try:
        docs = client.get_document_titles(item_type, item_id)
        # Truncate long titles for display in small preview widgets
        processed_docs = []
        for doc in docs:
            title = doc['title']
            if len(title) > 50:
                title = title[:47] + '...'
            processed_docs.append({'id': doc['id'], 'title': title})

        return jsonify({
            'documents': processed_docs,
            'base_url': client.api_url
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)

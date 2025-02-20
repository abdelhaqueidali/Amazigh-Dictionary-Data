import gradio as gr
import sqlite3
from pathlib import Path
import unicodedata
import re

def remove_diacritics(text):
    """Removes diacritics from text."""
    if text is None:
        return None
    return ''.join(c for c in unicodedata.normalize('NFD', text)
                   if unicodedata.category(c) != 'Mn')

def get_db_connection(db_name):
    """Establish database connection with custom functions."""
    conn = sqlite3.connect(db_name)
    conn.row_factory = sqlite3.Row
    conn.create_function("REMOVE_DIACRITICS", 1, remove_diacritics)
    conn.create_function("NORMALIZE_AMAZIGH", 1, normalize_amazigh_text)
    conn.create_function("NORMALIZE_FRENCH", 1, normalize_french_text)
    return conn

def normalize_french_text(text):
    """Normalize French text."""
    if not text:
        return text
    normalized_text = ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')
    return normalized_text.lower()

def normalize_arabic_text(text):
    """Normalize Arabic text."""
    if not text:
        return text
    text = text.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
    return text.lower()

def normalize_general_text(text):
    """General text normalization."""
    if not text:
        return text
    text = normalize_arabic_text(text)
    return remove_diacritics(text)

def normalize_amazigh_text(text):
    """Normalize Amazigh text."""
    if not text:
        return text
    text = text.replace("ⵕ", "ⵔ")
    text = text.replace("ⵯ", "")
    return text.lower()

def get_search_pattern(query, search_type):
    """Generate search pattern based on search type."""
    if not query:
        return "", ""
    
    normalized_query = re.escape(normalize_general_text(query))
    
    if search_type == 'exact':
        pattern = f"\\b{normalized_query}\\b"
        contains_pattern = pattern
        starts_pattern = pattern
    elif search_type == 'starts':
        pattern = f"{normalized_query}%"
        contains_pattern = f"%{normalized_query}%"
        starts_pattern = pattern
    else:  # contains
        pattern = f"%{normalized_query}%"
        contains_pattern = pattern
        starts_pattern = f"{normalized_query}%"
        
    return starts_pattern, contains_pattern

def search_dictionary(query, language='general', search_type='contains'):
    """Main search function with language and search type options."""
    if not query or len(query.strip()) < 1:
        return "Please enter a search term"

    starts_pattern, contains_pattern = get_search_pattern(query, search_type)
    results = []
    
    if language == 'english':
        results = search_eng(starts_pattern, contains_pattern, starts_pattern, contains_pattern, 50)
    elif language == 'french':
        results.extend(search_dglai14_french(starts_pattern, contains_pattern))
        if len(results) < 50:
            results.extend(search_tawalt_fr(starts_pattern, contains_pattern, starts_pattern, contains_pattern, 50 - len(results)))
        if len(results) < 50:
            results.extend(search_msmun_fr(starts_pattern, contains_pattern, 50 - len(results)))
    elif language == 'arabic':
        results.extend(search_dglai14_arabic(starts_pattern, contains_pattern))
        if len(results) < 50:
            results.extend(search_tawalt_arabic(starts_pattern, contains_pattern, 50 - len(results)))
        if len(results) < 50:
            results.extend(search_msmun_ar(starts_pattern, contains_pattern, 50 - len(results)))
    elif language == 'amazigh':
        results.extend(search_amazigh_only(starts_pattern, contains_pattern))
    else:  # general
        results = search_all_databases(starts_pattern, contains_pattern)

    # Format results based on their source
    html_output = format_results(results)
    return html_output if html_output else "No results found"

def search_eng(starts_pattern, contains_pattern, starts_amazigh, contains_amazigh, limit):
    conn = get_db_connection('eng.db')
    cursor = conn.cursor()
    
    # Start search
    cursor.execute("""
        SELECT da.*, dea.sens_eng
        FROM Dictionary_Amazigh_full AS da
        LEFT JOIN Dictionary_English_Amazih_links AS dea ON da.id_lexie = dea.id_lexie
        WHERE LOWER(dea.sens_eng) LIKE ? OR NORMALIZE_AMAZIGH(da.lexie) LIKE ?
        LIMIT ?
    """, (starts_pattern, starts_amazigh, limit))
    start_results = cursor.fetchall()
    
    # Contains search
    cursor.execute("""
        SELECT da.*, dea.sens_eng
        FROM Dictionary_Amazigh_full AS da
        LEFT JOIN Dictionary_English_Amazih_links AS dea ON da.id_lexie = dea.id_lexie
        WHERE (LOWER(dea.sens_eng) LIKE ? OR NORMALIZE_AMAZIGH(da.lexie) LIKE ?)
        AND NOT (LOWER(dea.sens_eng) LIKE ? OR NORMALIZE_AMAZIGH(da.lexie) LIKE ?)
        LIMIT ?
    """, (contains_pattern, contains_amazigh, starts_pattern, starts_amazigh, limit))
    contain_results = cursor.fetchall()
    
    conn.close()
    return list(start_results) + list(contain_results)

def search_dglai14_french(starts_pattern, contains_pattern):
    conn = get_db_connection('dglai14.db')
    cursor = conn.cursor()
    
    # Search focusing on French translations
    cursor.execute("""
        SELECT lexie.*, sens.sens_fr, sens.sens_ar,
               expression.exp_amz, expression.exp_fr, expression.exp_ar
        FROM lexie
        LEFT JOIN sens ON lexie.id_lexie = sens.id_lexie
        LEFT JOIN expression ON lexie.id_lexie = expression.id_lexie
        WHERE NORMALIZE_FRENCH(sens.sens_fr) LIKE ?
        OR NORMALIZE_FRENCH(expression.exp_fr) LIKE ?
        LIMIT 50
    """, (starts_pattern, starts_pattern))
    results = cursor.fetchall()
    
    conn.close()
    return results

def search_dglai14_arabic(starts_pattern, contains_pattern):
    conn = get_db_connection('dglai14.db')
    cursor = conn.cursor()
    
    # Search focusing on Arabic translations
    cursor.execute("""
        SELECT lexie.*, sens.sens_fr, sens.sens_ar,
               expression.exp_amz, expression.exp_fr, expression.exp_ar
        FROM lexie
        LEFT JOIN sens ON lexie.id_lexie = sens.id_lexie
        LEFT JOIN expression ON lexie.id_lexie = expression.id_lexie
        WHERE REMOVE_DIACRITICS(LOWER(sens.sens_ar)) LIKE ?
        OR REMOVE_DIACRITICS(LOWER(expression.exp_ar)) LIKE ?
        LIMIT 50
    """, (starts_pattern, starts_pattern))
    results = cursor.fetchall()
    
    conn.close()
    return results

def search_amazigh_only(starts_pattern, contains_pattern):
    results = []
    
    # Search in dglai14
    conn = get_db_connection('dglai14.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT lexie.*, sens.sens_fr, sens.sens_ar,
               expression.exp_amz, expression.exp_fr, expression.exp_ar
        FROM lexie
        LEFT JOIN sens ON lexie.id_lexie = sens.id_lexie
        LEFT JOIN expression ON lexie.id_lexie = expression.id_lexie
        WHERE NORMALIZE_AMAZIGH(lexie) LIKE ?
        OR NORMALIZE_AMAZIGH(variante) LIKE ?
        OR NORMALIZE_AMAZIGH(eadata) LIKE ?
        OR NORMALIZE_AMAZIGH(pldata) LIKE ?
        OR NORMALIZE_AMAZIGH(expression.exp_amz) LIKE ?
        LIMIT 50
    """, (starts_pattern, starts_pattern, starts_pattern, starts_pattern, starts_pattern))
    results.extend(cursor.fetchall())
    conn.close()
    
    # Add searches for other databases with Amazigh content
    if len(results) < 50:
        conn = get_db_connection('tawalt.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT *
            FROM words
            WHERE NORMALIZE_AMAZIGH(tifinagh) LIKE ?
            LIMIT ?
        """, (starts_pattern, 50 - len(results)))
        results.extend(cursor.fetchall())
        conn.close()
    
    return results

def format_results(results):
    """Format search results as HTML."""
    if not results:
        return ""
        
    html_output = "<div class='search-results'>"
    
    for result in results:
        # Determine result type and format accordingly
        if 'sens_eng' in result.keys():
            html_output += format_eng_result(result)
        elif 'sens_fr' in result.keys():
            html_output += format_dglai14_result(result)
        elif 'french' in result.keys():
            html_output += format_tawalt_fr_result(result)
        else:
            html_output += format_generic_result(result)
            
    html_output += "</div>"
    return html_output

def format_eng_result(result):
    """Format English dictionary result."""
    return f"""
    <div class="result-card" style="background: #d3f8d3; padding: 20px; margin: 10px 0; border-radius: 8px;">
        <h3>{result['lexie'] or ''}</h3>
        <p><strong>English:</strong> {result['sens_eng'] or ''}</p>
        {f"<p><strong>Notes:</strong> {result['remarque']}</p>" if result['remarque'] else ''}
    </div>
    """

def format_dglai14_result(result):
    """Format dglai14 dictionary result."""
    return f"""
    <div class="result-card" style="background: #f0f8ff; padding: 20px; margin: 10px 0; border-radius: 8px;">
        <h3>{result['lexie'] or ''}</h3>
        {f"<p><strong>French:</strong> {result['sens_fr']}</p>" if result['sens_fr'] else ''}
        {f"<p><strong>Arabic:</strong> {result['sens_ar']}</p>" if result['sens_ar'] else ''}
        {f"<p><strong>Notes:</strong> {result['remarque']}</p>" if result['remarque'] else ''}
    </div>
    """

def format_tawalt_fr_result(result):
    """Format tawalt_fr dictionary result."""
    return f"""
    <div class="result-card" style="background: #ffe0b2; padding: 20px; margin: 10px 0; border-radius: 8px;">
        <h3>{result['tifinagh'] or ''}</h3>
        <p><strong>French:</strong> {result['french'] or ''}</p>
    </div>
    """

def format_generic_result(result):
    """Format generic dictionary result."""
    return f"""
    <div class="result-card" style="background: #e8eaf6; padding: 20px; margin: 10px 0; border-radius: 8px;">
        <h3>{next((result[k] for k in ['word', 'tifinagh', 'lexie'] if k in result.keys()), '')}</h3>
        <p>{', '.join(f"{k}: {v}" for k, v in dict(result).items() if v and k not in ['_id', 'id_lexie'])}</p>
    </div>
    """

# Create Gradio interface
with gr.Blocks(css="footer {display: none !important}") as iface:
    gr.HTML("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <h1 style="color: #2c3e50; margin-bottom: 1rem;">Amazigh Dictionary</h1>
    </div>
    """)

    with gr.Row():
        input_text = gr.Textbox(
            label="Search",
            placeholder="Enter a word to search...",
            lines=1
        )
        language_select = gr.Dropdown(
            choices=['general', 'amazigh', 'arabic', 'english', 'french'],
            value='general',
            label="Language"
        )
        search_type = gr.Radio(
            choices=['contains', 'exact', 'starts'],
            value='contains',
            label="Search Type"
        )

    output_html = gr.HTML()

    def search_wrapper(query, language, search_type):
        return search_dictionary(query, language, search_type)

    input_text.change(
        fn=search_wrapper,
        inputs=[input_text, language_select, search_type],
        outputs=output_html,
        api_name="search"
    )

if __name__ == "__main__":
    iface.launch()
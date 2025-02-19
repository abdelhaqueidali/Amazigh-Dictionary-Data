import gradio as gr
import sqlite3
from pathlib import Path
import unicodedata

def remove_diacritics(text):
    """Removes diacritics from Arabic text (and any other text)."""
    if text is None:  # Handle potential NULL values
        return None
    return ''.join(c for c in unicodedata.normalize('NFD', text)
                   if unicodedata.category(c) != 'Mn')

def get_db_connection():
    conn = sqlite3.connect('dglai14.db')
    conn.row_factory = sqlite3.Row
    # Create the custom SQLite function
    conn.create_function("REMOVE_DIACRITICS", 1, remove_diacritics)
    return conn

def normalize_french_text(text):
    """Normalize French text by removing diacritics and converting to lower case."""
    if not text:
        return text
    normalized_text = ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')
    return normalized_text.lower()

def normalize_arabic_text(text):
    """Normalize Arabic text by unifying similar characters (Alif)."""
    if not text:
        return text
    text = text.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا") # unify alif forms
    return text.lower() # Keep lowercasing for consistency

def normalize_general_text(text): #Add general normalization
    if not text:
        return text
    text = normalize_arabic_text(text)
    return remove_diacritics(text)

def search_dictionary(query):
    if not query or len(query.strip()) < 1:
        return "Please enter a search term"

    conn = get_db_connection()
    cursor = conn.cursor()

    normalized_query_french = normalize_french_text(query)
    #normalized_query_arabic = normalize_arabic_text(query) # No longer needed
    normalized_query_general = normalize_general_text(query) # Use general normalization

    start_search_term_french = f"{normalized_query_french}%"
    contain_search_term_french = f"%{normalized_query_french}%"
    #start_search_term_arabic = f"{normalized_query_arabic}%" # No longer needed
    #contain_search_term_arabic = f"%{normalized_query_arabic}%" # No longer needed
    start_search_term_general = f"{normalized_query_general}%"
    contain_search_term_general = f"%{normalized_query_general}%"


    # Query for results starting with the search term (in any field)
    cursor.execute("""
        SELECT lexie.*, sens.sens_fr, sens.sens_ar,
               expression.exp_amz, expression.exp_fr, expression.exp_ar
        FROM lexie
        LEFT JOIN sens ON lexie.id_lexie = sens.id_lexie
        LEFT JOIN expression ON lexie.id_lexie = expression.id_lexie
        WHERE
        (REMOVE_DIACRITICS(LOWER(lexie)) LIKE ?)
        OR (REMOVE_DIACRITICS(LOWER(api)) LIKE ?)
        OR (REMOVE_DIACRITICS(LOWER(remarque)) LIKE ?)
        OR (REMOVE_DIACRITICS(LOWER(variante)) LIKE ?)
        OR (REMOVE_DIACRITICS(LOWER(cg)) LIKE ?)
        OR (REMOVE_DIACRITICS(LOWER(eadata)) LIKE ?)
        OR (REMOVE_DIACRITICS(LOWER(pldata)) LIKE ?)
        OR (REMOVE_DIACRITICS(LOWER(acc)) LIKE ?)
        OR (REMOVE_DIACRITICS(LOWER(acc_neg)) LIKE ?)
        OR (REMOVE_DIACRITICS(LOWER(inacc)) LIKE ?)
        OR (REMOVE_DIACRITICS(LOWER(fel)) LIKE ?)
        OR (REMOVE_DIACRITICS(LOWER(fea)) LIKE ?)
        OR (REMOVE_DIACRITICS(LOWER(fpel)) LIKE ?)
        OR (REMOVE_DIACRITICS(LOWER(fpea)) LIKE ?)
        OR (LOWER(sens_fr) LIKE ?)
        OR (REMOVE_DIACRITICS(LOWER(sens_ar)) LIKE ?)
        OR (REMOVE_DIACRITICS(LOWER(expression.exp_amz)) LIKE ?)
        OR (LOWER(expression.exp_fr) LIKE ?)
        OR (REMOVE_DIACRITICS(LOWER(expression.exp_ar)) LIKE ?)

        ORDER BY lexie.id_lexie
        LIMIT 50
    """, (start_search_term_general, start_search_term_general, start_search_term_general, start_search_term_general, start_search_term_general,
          start_search_term_general, start_search_term_general, start_search_term_general, start_search_term_general, start_search_term_general,
          start_search_term_general, start_search_term_general, start_search_term_general, start_search_term_general,
          start_search_term_french, start_search_term_general,  # Use general normalization for all Arabic fields
          start_search_term_general, start_search_term_french, start_search_term_general)) # Use general normalization for all Arabic fields
    start_results = cursor.fetchall()

    # Query for results containing the search term (in any field), but NOT starting with in lexie field
    cursor.execute("""
        SELECT lexie.*, sens.sens_fr, sens.sens_ar,
               expression.exp_amz, expression.exp_fr, expression.exp_ar
        FROM lexie
        LEFT JOIN sens ON lexie.id_lexie = sens.id_lexie
        LEFT JOIN expression ON lexie.id_lexie = expression.id_lexie
        WHERE (
        (REMOVE_DIACRITICS(LOWER(lexie)) LIKE ?)
        OR (REMOVE_DIACRITICS(LOWER(api)) LIKE ?)
        OR (REMOVE_DIACRITICS(LOWER(remarque)) LIKE ?)
        OR (REMOVE_DIACRITICS(LOWER(variante)) LIKE ?)
        OR (REMOVE_DIACRITICS(LOWER(cg)) LIKE ?)
        OR (REMOVE_DIACRITICS(LOWER(eadata)) LIKE ?)
        OR (REMOVE_DIACRITICS(LOWER(pldata)) LIKE ?)
        OR (REMOVE_DIACRITICS(LOWER(acc)) LIKE ?)
        OR (REMOVE_DIACRITICS(LOWER(acc_neg)) LIKE ?)
        OR (REMOVE_DIACRITICS(LOWER(inacc)) LIKE ?)
        OR (REMOVE_DIACRITICS(LOWER(fel)) LIKE ?)
        OR (REMOVE_DIACRITICS(LOWER(fea)) LIKE ?)
        OR (REMOVE_DIACRITICS(LOWER(fpel)) LIKE ?)
        OR (REMOVE_DIACRITICS(LOWER(fpea)) LIKE ?)
        OR (LOWER(sens_fr) LIKE ?)
        OR (REMOVE_DIACRITICS(LOWER(sens_ar)) LIKE ?)
        OR (REMOVE_DIACRITICS(LOWER(expression.exp_amz)) LIKE ?)
        OR (LOWER(expression.exp_fr) LIKE ?)
        OR (REMOVE_DIACRITICS(LOWER(expression.exp_ar)) LIKE ?)
        )
        AND NOT (REMOVE_DIACRITICS(LOWER(lexie)) LIKE ?)
        ORDER BY lexie.id_lexie
        LIMIT 50
    """, (contain_search_term_general, contain_search_term_general, contain_search_term_general, contain_search_term_general, contain_search_term_general,
          contain_search_term_general, contain_search_term_general, contain_search_term_general, contain_search_term_general, contain_search_term_general,
          contain_search_term_general, contain_search_term_general, contain_search_term_general, contain_search_term_general,
          contain_search_term_french, contain_search_term_general,  # Use general normalization for all Arabic fields
          contain_search_term_general, contain_search_term_french, contain_search_term_general,
          start_search_term_general)) # Use general normalization for NOT LIKE
    contain_results = cursor.fetchall()

    conn.close()

    results = list(start_results) + list(contain_results)

    if not results:
        return "No results found"

    # Aggregate results by lexie.id_lexie, now handling duplicate expressions based on exp_amz
    aggregated_results = {}
    for row in results:
        lexie_id = row['id_lexie']
        if lexie_id not in aggregated_results:
            aggregated_results[lexie_id] = {
                'lexie': row['lexie'],
                'api': row['api'],
                'remarque': row['remarque'],
                'variante': row['variante'],
                'cg': row['cg'],
                'eadata': row['eadata'],
                'pldata': row['pldata'],
                'acc': row['acc'],
                'acc_neg': row['acc_neg'],
                'inacc': row['inacc'],
                'fel': row['fel'],
                'fea': row['fea'],
                'fpel': row['fpel'],
                'fpea': row['fpea'],
                'sens_frs': set(),
                'sens_ars': set(),
                'expressions': {} # Change to dictionary to store unique exp_amz
            }
        aggregated_results[lexie_id]['sens_frs'].add(row['sens_fr'])
        aggregated_results[lexie_id]['sens_ars'].add(row['sens_ar'])
        if row['exp_amz']:
            exp_amz = row['exp_amz']
            if exp_amz not in aggregated_results[lexie_id]['expressions']:
                aggregated_results[lexie_id]['expressions'][exp_amz] = {
                    'french_translations': set(),
                    'arabic_translations': set()
                }
            if row['exp_fr']:
                aggregated_results[lexie_id]['expressions'][exp_amz]['french_translations'].add(row['exp_fr'])
            if row['exp_ar']:
                aggregated_results[lexie_id]['expressions'][exp_amz]['arabic_translations'].add(row['exp_ar'])


    # Format aggregated results as HTML
    html_output = ""
    for lexie_id, data in list(aggregated_results.items())[:50]:
        html_output += f"""
        <div style="background: white; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #3498db; padding-bottom: 10px; margin-bottom: 10px;">
                <h3 style="color: #2c3e50; margin: 0;">{data['lexie'] or ''}</h3>
                <span style="background: #3498db; color: white; padding: 4px 8px; border-radius: 4px;">{data['cg'] or ''}</span>
            </div>
        """

        fields = {
            'Transcription': 'api',
            'Notes': 'remarque',
            'Construct State': 'eadata',
            'Plural': 'pldata',
            'Accomplished': 'acc',
            'Negative Accomplished': 'acc_neg',
            'Unaccomplished': 'inacc',
            'Variants': 'variante',
            'Feminine': 'fel',
            'Feminine Construct': 'fea',
            'Feminine Plural': 'fpel',
            'Feminine Plural Construct': 'fpea',
        }

        for label, field in fields.items():
            if data[field]:
                html_output += f"""
                <div style="margin-bottom: 8px;">
                    <strong style="color: #34495e;">{label}:</strong>
                    <span style="color: black;">{data[field]}</span>
                </div>
                """

        french_translations = ", ".join(filter(None, data['sens_frs']))
        arabic_translations = ", ".join(filter(None, data['sens_ars']))

        if french_translations:
            html_output += f"""
            <div style="margin-bottom: 8px;">
                <strong style="color: #34495e;">French Translation:</strong>
                <span style="color: black;">{french_translations}</span>
            </div>
            """
        if arabic_translations:
            html_output += f"""
            <div style="margin-bottom: 8px;">
                <strong style="color: #34495e;">Arabic Translation:</strong>
                <span style="color: black;">{arabic_translations}</span>
            </div>
            """

        if data['expressions']:
            html_output += f"""
            <div style="margin-top: 10px; border-top: 1px solid #ddd; padding-top: 10px;">
                <strong style="color: #34495e;">Expressions:</strong>
            """
            for exp_amz, translations in data['expressions'].items(): # Iterate through expression dictionary
                french_exp_translations = ", ".join(filter(None, translations['french_translations']))
                arabic_exp_translations = ", ".join(filter(None, translations['arabic_translations']))

                html_output += f"""
                <div style="margin-top: 6px; padding-left: 15px; border-bottom: 1px solid #eee; padding-bottom: 8px; margin-bottom: 8px;">
                    <div style="margin-bottom: 4px;">
                        <strong style="color: #546e7a;">Amazigh:</strong>
                        <span style="color: black;">{exp_amz or ''}</span>
                    </div>
                    """
                if french_exp_translations:
                    html_output += f"""
                    <div style="margin-bottom: 4px;">
                        <strong style="color: #546e7a;">French:</strong>
                        <span style="color: black;">{french_exp_translations or ''}</span>
                    </div>
                    """
                if arabic_exp_translations:
                    html_output += f"""
                    <div>
                        <strong style="color: #546e7a;">Arabic:</strong>
                        <span style="color: black;">{arabic_exp_translations or ''}</span>
                    </div>
                    """
                html_output += "</div>"
            html_output += "</div>"

        html_output += "</div></div>"

    return html_output

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

    output_html = gr.HTML()

    input_text.change(
        fn=search_dictionary,
        inputs=input_text,
        outputs=output_html,
        api_name="search"
    )

if __name__ == "__main__":
    iface.launch()
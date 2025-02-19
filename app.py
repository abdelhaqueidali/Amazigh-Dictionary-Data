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

def get_db_connection(db_name):  # Function now takes db_name as argument
    conn = sqlite3.connect(db_name)
    conn.row_factory = sqlite3.Row
    conn.create_function("REMOVE_DIACRITICS", 1, remove_diacritics)
    return conn

def normalize_french_text(text):
    if not text:
        return text
    normalized_text = ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')
    return normalized_text.lower()

def normalize_arabic_text(text):
    if not text:
        return text
    text = text.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا") # unify alif forms
    return text.lower()

def normalize_general_text(text):
    if not text:
        return text
    text = normalize_arabic_text(text)
    return remove_diacritics(text)

def normalize_amazigh_text(text):
    """
    Normalizes Amazigh text for consistent searching.
    This function:
    1. Treats ⵔ and ⵕ as the same character.
    2. Removes ⵯ (Tawalt) from the text (similar to diacritic removal).
    """
    if not text:
        return text

    # Treat ⵔ and ⵕ as the same character
    text = text.replace("ⵕ", "ⵔ")  # Replace all instances of ⵕ with ⵔ

    # Remove ⵯ (Tawalt)
    text = text.replace("ⵯ", "")

    return text.lower() # Return lowercase for consistence

def search_dictionary(query):
    if not query or len(query.strip()) < 1:
        return "Please enter a search term"

    normalized_query_general = normalize_general_text(query)
    start_search_term_general = f"{normalized_query_general}%"
    contain_search_term_general = f"%{normalized_query_general}%"

    normalized_query_amazigh = normalize_amazigh_text(query)
    start_search_term_amazigh = f"{normalized_query_amazigh}%"
    contain_search_term_amazigh = f"%{normalized_query_amazigh}%"

    # --- Search dglai14.db (Prioritized) ---
    dglai14_results = search_dglai14(start_search_term_general, contain_search_term_general,start_search_term_amazigh, contain_search_term_amazigh)

    # --- Search tawalt.db (Secondary) ---
    # Only search tawalt if dglai14 returns fewer than 50 results
    if len(dglai14_results) < 50:
        remaining_count = 50 - len(dglai14_results)
        tawalt_results = search_tawalt(start_search_term_general, contain_search_term_general,start_search_term_amazigh, contain_search_term_amazigh, remaining_count)
    else:
        tawalt_results = []  # No need to search tawalt

    # --- Combine and Format Results ---
    html_output = format_dglai14_results(dglai14_results)  # Format dglai14 results
    html_output += format_tawalt_results(tawalt_results) # Format tawalt results (if any)

    if not html_output:
        return "No results found"

    return html_output


def search_dglai14(start_search_term_general, contain_search_term_general,start_search_term_amazigh, contain_search_term_amazigh):
    conn = get_db_connection('dglai14.db')
    cursor = conn.cursor()

    # Add the custom SQLite function for Amazigh normalization *inside* the function that uses it
    conn.create_function("NORMALIZE_AMAZIGH", 1, normalize_amazigh_text) # To be removed if the database is selectable

    # Start Search (dglai14)
    cursor.execute("""
        SELECT lexie.*, sens.sens_fr, sens.sens_ar,
               expression.exp_amz, expression.exp_fr, expression.exp_ar
        FROM lexie
        LEFT JOIN sens ON lexie.id_lexie = sens.id_lexie
        LEFT JOIN expression ON lexie.id_lexie = expression.id_lexie
        WHERE
        (NORMALIZE_AMAZIGH(lexie) LIKE ?) -- Use NORMALIZE_AMAZIGH for lexie (Amazigh word)
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
        OR (REMOVE_DIACRITICS(LOWER(sens_ar)) LIKE ?)
        OR (NORMALIZE_AMAZIGH(expression.exp_amz) LIKE ?) -- Use NORMALIZE_AMAZIGH for exp_amz
        OR (REMOVE_DIACRITICS(LOWER(expression.exp_ar)) LIKE ?)

        ORDER BY lexie.id_lexie
        LIMIT 50
    """, (start_search_term_amazigh, start_search_term_general, start_search_term_general, start_search_term_general, start_search_term_general,
          start_search_term_general, start_search_term_general, start_search_term_general, start_search_term_general, start_search_term_general,
          start_search_term_general, start_search_term_general, start_search_term_general, start_search_term_general,
          start_search_term_general, start_search_term_amazigh, start_search_term_general))
    start_results = cursor.fetchall()

    # Contain Search (dglai14)
    cursor.execute("""
        SELECT lexie.*, sens.sens_fr, sens.sens_ar,
               expression.exp_amz, expression.exp_fr, expression.exp_ar
        FROM lexie
        LEFT JOIN sens ON lexie.id_lexie = sens.id_lexie
        LEFT JOIN expression ON lexie.id_lexie = expression.id_lexie
        WHERE (
        (NORMALIZE_AMAZIGH(lexie) LIKE ?) -- Use NORMALIZE_AMAZIGH for lexie (Amazigh word)
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
        OR (REMOVE_DIACRITICS(LOWER(sens_ar)) LIKE ?)
        OR (NORMALIZE_AMAZIGH(expression.exp_amz) LIKE ?) -- Use NORMALIZE_AMAZIGH for exp_amz
        OR (REMOVE_DIACRITICS(LOWER(expression.exp_ar)) LIKE ?)
        )
        AND NOT (NORMALIZE_AMAZIGH(lexie) LIKE ?) -- Use NORMALIZE_AMAZIGH here too
        ORDER BY lexie.id_lexie
        LIMIT 50
    """, (contain_search_term_amazigh, contain_search_term_general, contain_search_term_general, contain_search_term_general, contain_search_term_general,
          contain_search_term_general, contain_search_term_general, contain_search_term_general, contain_search_term_general, contain_search_term_general,
          contain_search_term_general, contain_search_term_general, contain_search_term_general, contain_search_term_general,
          contain_search_term_general, contain_search_term_amazigh, contain_search_term_general,
          start_search_term_amazigh))  # Use start_search_term_amazigh for the NOT LIKE part
    contain_results = cursor.fetchall()
    conn.close()
    return list(start_results) + list(contain_results)

def search_tawalt(start_search_term_general, contain_search_term_general,start_search_term_amazigh, contain_search_term_amazigh, limit):
    conn = get_db_connection('tawalt.db')
    cursor = conn.cursor()

    # Add the custom SQLite function for Amazigh normalization
    conn.create_function("NORMALIZE_AMAZIGH", 1, normalize_amazigh_text)  #To be removed if the database is selectable

    # Start Search (tawalt)
    cursor.execute("""
        SELECT *
        FROM words
        WHERE
        (NORMALIZE_AMAZIGH(tifinagh) LIKE ?) -- Use NORMALIZE_AMAZIGH for tifinagh
        OR (REMOVE_DIACRITICS(LOWER(arabic)) LIKE ?)
        OR (REMOVE_DIACRITICS(LOWER(arabic_meaning)) LIKE ?)
        OR (NORMALIZE_AMAZIGH(tifinagh_in_arabic) LIKE ?) -- Use NORMALIZE_AMAZIGH
        OR (REMOVE_DIACRITICS(LOWER(_arabic)) LIKE ?)
        OR (REMOVE_DIACRITICS(LOWER(_arabic_meaning)) LIKE ?)
        OR (REMOVE_DIACRITICS(LOWER(_tifinagh_in_arabic)) LIKE ?)
        ORDER BY _id
        LIMIT ?
    """, (start_search_term_amazigh, start_search_term_general, start_search_term_general, start_search_term_amazigh,
          start_search_term_general, start_search_term_general, start_search_term_general, limit))
    start_results = cursor.fetchall()

    # Contain Search (tawalt)
    cursor.execute("""
        SELECT *
        FROM words
        WHERE (
        (NORMALIZE_AMAZIGH(tifinagh) LIKE ?) -- Use NORMALIZE_AMAZIGH for tifinagh
        OR (REMOVE_DIACRITICS(LOWER(arabic)) LIKE ?)
        OR (REMOVE_DIACRITICS(LOWER(arabic_meaning)) LIKE ?)
        OR (NORMALIZE_AMAZIGH(tifinagh_in_arabic) LIKE ?) -- Use NORMALIZE_AMAZIGH
        OR (REMOVE_DIACRITICS(LOWER(_arabic)) LIKE ?)
        OR (REMOVE_DIACRITICS(LOWER(_arabic_meaning)) LIKE ?)
        OR (REMOVE_DIACRITICS(LOWER(_tifinagh_in_arabic)) LIKE ?)
        )
        AND NOT (NORMALIZE_AMAZIGH(tifinagh) LIKE ?) -- Use NORMALIZE_AMAZIGH
        ORDER BY _id
        LIMIT ?
    """, (contain_search_term_amazigh, contain_search_term_general, contain_search_term_general, contain_search_term_amazigh,
          contain_search_term_general, contain_search_term_general, contain_search_term_general,
          start_search_term_amazigh, limit)) # Use start_search_term_amazigh for NOT LIKE
    contain_results = cursor.fetchall()
    conn.close()
    return list(start_results) + list(contain_results)

def format_dglai14_results(results):
    """Formats results from dglai14.db."""
    if not results:
        return ""

    aggregated_results = {}
    for row in results:
        lexie_id = row['id_lexie']
        if lexie_id not in aggregated_results:
            aggregated_results[lexie_id] = {
                'lexie': row['lexie'],
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
                'expressions': {}
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

    html_output = ""
    for lexie_id, data in aggregated_results.items():
        html_output += f"""
        <div style="background: #f0f8ff; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #3498db; padding-bottom: 10px; margin-bottom: 10px;">
                <h3 style="color: #2c3e50; margin: 0;">{data['lexie'] or ''}</h3>
                <span style="background: #3498db; color: white; padding: 4px 8px; border-radius: 4px;">{data['cg'] or ''}</span>
            </div>
        """

        fields = {
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
            for exp_amz, translations in data['expressions'].items():
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

        html_output += "</div>"
    return html_output

def format_tawalt_results(results):
    """Formats results from tawalt.db."""
    if not results:
        return ""

    html_output = ""
    for row in results:
        html_output += f"""
        <div style="background: white; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #3498db; padding-bottom: 10px; margin-bottom: 10px;">
                <h3 style="color: #2c3e50; margin: 0;">{row['tifinagh'] or ''}</h3>
            </div>
        """
        if row['arabic']:
            html_output += f"""
            <div style="margin-bottom: 8px;">
                <strong style="color: #34495e;">Arabic:</strong>
                <span style="color: black;">{row['arabic']}</span>
            </div>
            """
        if row['arabic_meaning']:
            html_output += f"""
            <div style="margin-bottom: 8px;">
                <strong style="color: #34495e;">Arabic Meaning:</strong>
                <span style="color: black;">{row['arabic_meaning']}</span>
            </div>
            """
        html_output += "</div>"

    return html_output
# Create Gradio interface (Remains the same)
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
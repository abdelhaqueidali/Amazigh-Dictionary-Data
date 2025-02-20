import gradio as gr
import sqlite3
from pathlib import Path
import unicodedata
import re

def remove_diacritics(text):
    """Removes diacritics from Arabic text (and any other text)."""
    if text is None:  # Handle potential NULL values
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
    text = text.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا") # unify alif forms
    return text.lower()

def normalize_general_text(text):
    """General text normalization."""
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
    text = text.replace("ⵕ", "ⵔ")  # Replace all instances of ⵕ with ⵔ
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

    if language == 'english':
        results = search_eng(starts_pattern, contains_pattern, starts_pattern, contains_pattern, 50)
    elif language == 'french':
        results = []
        results.extend(search_dglai14_french(starts_pattern, contains_pattern))
        if len(results) < 50:
            results.extend(search_tawalt_fr(starts_pattern, contains_pattern, starts_pattern, contains_pattern, 50 - len(results)))
        if len(results) < 50:
            results.extend(search_msmun_fr_m(starts_pattern, contains_pattern, starts_pattern, contains_pattern, 50 - len(results)))
            results.extend(search_msmun_fr_r(starts_pattern, contains_pattern, starts_pattern, contains_pattern, 50 - len(results)))
    elif language == 'arabic':
        results = []
        results.extend(search_dglai14_arabic(starts_pattern, contains_pattern))
        if len(results) < 50:
            results.extend(search_tawalt(starts_pattern, contains_pattern, starts_pattern, contains_pattern, 50 - len(results)))
        if len(results) < 50:
            results.extend(search_msmun_ar_m_r(starts_pattern, contains_pattern, starts_pattern, contains_pattern, 50 - len(results)))
            results.extend(search_msmun_ar_r_m(starts_pattern, contains_pattern, starts_pattern, contains_pattern, 50 - len(results)))
    elif language == 'amazigh':
        results = search_amazigh_only(starts_pattern, contains_pattern)
    else:  # general
        # --- Search dglai14.db (Prioritized) ---
        results = search_dglai14(starts_pattern, contains_pattern, starts_pattern, contains_pattern)

        # --- Search tawalt_fr.db (Secondary) ---
        remaining_results = 50 - len(results)
        if remaining_results > 0:
            tawalt_fr_results = search_tawalt_fr(starts_pattern, contains_pattern, starts_pattern, contains_pattern, remaining_results)
            remaining_results -= len(tawalt_fr_results)
            results.extend(tawalt_fr_results)

        # --- Search tawalt.db (Tertiary) ---
        if remaining_results > 0:
            tawalt_results = search_tawalt(starts_pattern, contains_pattern, starts_pattern, contains_pattern, remaining_results)
            remaining_results -= len(tawalt_results)
            results.extend(tawalt_results)

        # --- Search eng.db (Quaternary) ---
        if remaining_results > 0:
            eng_results = search_eng(starts_pattern, contains_pattern, starts_pattern, contains_pattern, remaining_results)
            remaining_results -= len(eng_results)
            results.extend(eng_results)

        # --- Search msmun_fr.db (Quinary) ---
        if remaining_results > 0:
            msmun_fr_m_results = search_msmun_fr_m(starts_pattern, contains_pattern, starts_pattern, contains_pattern, remaining_results)
            remaining_results -= len(msmun_fr_m_results)
            results.extend(msmun_fr_m_results)

        if remaining_results > 0:
            msmun_fr_r_results = search_msmun_fr_r(starts_pattern, contains_pattern, starts_pattern, contains_pattern, remaining_results)
            remaining_results -= len(msmun_fr_r_results)
            results.extend(msmun_fr_r_results)

        # --- Search msmun_ar.db (Senary) ---
        if remaining_results > 0:
            msmun_ar_m_r_results = search_msmun_ar_m_r(starts_pattern, contains_pattern, starts_pattern, contains_pattern, remaining_results)
            remaining_results -= len(msmun_ar_m_r_results)
            results.extend(msmun_ar_m_r_results)

        if remaining_results > 0:
            msmun_ar_r_m_results = search_msmun_ar_r_m(starts_pattern, contains_pattern, starts_pattern, contains_pattern, remaining_results)
            results.extend(msmun_ar_r_m_results)

    # Format results based on their source
    html_output = format_results(results)
    return html_output if html_output else "No results found"

def search_dglai14(starts_pattern, contains_pattern, starts_amazigh, contains_amazigh):
    conn = get_db_connection('dglai14.db')
    cursor = conn.cursor()

    # Start Search (dglai14)
    cursor.execute("""
        SELECT lexie.*, sens.sens_fr, sens.sens_ar,
               expression.exp_amz, expression.exp_fr, expression.exp_ar
        FROM lexie
        LEFT JOIN sens ON lexie.id_lexie = sens.id_lexie
        LEFT JOIN expression ON lexie.id_lexie = expression.id_lexie
        WHERE
        (NORMALIZE_AMAZIGH(lexie) LIKE ?)
        OR (NORMALIZE_AMAZIGH(remarque) LIKE ?)
        OR (NORMALIZE_AMAZIGH(variante) LIKE ?)
        OR (REMOVE_DIACRITICS(LOWER(cg)) LIKE ?)
        OR (NORMALIZE_AMAZIGH(eadata) LIKE ?)
        OR (NORMALIZE_AMAZIGH(pldata) LIKE ?)
        OR (REMOVE_DIACRITICS(LOWER(acc)) LIKE ?)
        OR (REMOVE_DIACRITICS(LOWER(acc_neg)) LIKE ?)
        OR (REMOVE_DIACRITICS(LOWER(inacc)) LIKE ?)
        OR (REMOVE_DIACRITICS(LOWER(fel)) LIKE ?)
        OR (REMOVE_DIACRITICS(LOWER(fea)) LIKE ?)
        OR (REMOVE_diacritics(LOWER(fpel)) LIKE ?)
        OR (REMOVE_DIACRITICS(LOWER(fpea)) LIKE ?)
        OR (REMOVE_DIACRITICS(LOWER(sens_ar)) LIKE ?)
        OR (NORMALIZE_AMAZIGH(expression.exp_amz) LIKE ?)
        OR (REMOVE_DIACRITICS(LOWER(expression.exp_ar)) LIKE ?)
        ORDER BY lexie.id_lexie
        LIMIT 50
    """, (starts_amazigh, starts_amazigh, starts_amazigh, starts_pattern,
          starts_amazigh, starts_amazigh, starts_pattern, starts_pattern, starts_pattern,
          starts_pattern, starts_pattern, starts_pattern, starts_pattern,
          starts_pattern, starts_amazigh, starts_pattern))
    start_results = cursor.fetchall()

    # Contain Search (dglai14)
    cursor.execute("""
        SELECT lexie.*, sens.sens_fr, sens.sens_ar,
               expression.exp_amz, expression.exp_fr, expression.exp_ar
        FROM lexie
        LEFT JOIN sens ON lexie.id_lexie = sens.id_lexie
        LEFT JOIN expression ON lexie.id_lexie = expression.id_lexie
        WHERE (
        (NORMALIZE_AMAZIGH(lexie) LIKE ?)
        OR (NORMALIZE_AMAZIGH(remarque) LIKE ?)
        OR (NORMALIZE_AMAZIGH(variante) LIKE ?)
        OR (REMOVE_DIACRITICS(LOWER(cg)) LIKE ?)
        OR (NORMALIZE_AMAZIGH(eadata) LIKE ?)
        OR (NORMALIZE_AMAZIGH(pldata) LIKE ?)
        OR (REMOVE_DIACRITICS(LOWER(acc)) LIKE ?)
        OR (REMOVE_DIACRITICS(LOWER(acc_neg)) LIKE ?)
        OR (REMOVE_DIACRITICS(LOWER(inacc)) LIKE ?)
        OR (REMOVE_DIACRITICS(LOWER(fel)) LIKE ?)
        OR (REMOVE_DIACRITICS(LOWER(fea)) LIKE ?)
        OR (REMOVE_DIACRITICS(LOWER(fpel)) LIKE ?)
        OR (REMOVE_DIACRITICS(LOWER(fpea)) LIKE ?)
        OR (REMOVE_DIACRITICS(LOWER(sens_ar)) LIKE ?)
        OR (NORMALIZE_AMAZIGH(expression.exp_amz) LIKE ?)
        OR (REMOVE_DIACRITICS(LOWER(expression.exp_ar)) LIKE ?)
        )
        AND NOT (NORMALIZE_AMAZIGH(lexie) LIKE ?)
        ORDER BY lexie.id_lexie
        LIMIT 50
    """, (contains_amazigh, contains_amazigh, contains_amazigh, contains_pattern,
          contains_amazigh, contains_amazigh, contains_pattern, contains_pattern, contains_pattern,
          contains_pattern, contains_pattern, contains_pattern, contains_pattern,
          contains_pattern, contains_amazigh, contains_pattern,
          starts_amazigh))
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

def search_tawalt_fr(starts_pattern, contains_pattern, starts_amazigh, contains_amazigh, limit):
    conn = get_db_connection('tawalt_fr.db')
    cursor = conn.cursor()

    # Start Search (tawalt_fr)
    cursor.execute("""
        SELECT *
        FROM words
        WHERE
        (NORMALIZE_AMAZIGH(tifinagh) LIKE ?)
        OR (NORMALIZE_FRENCH(french) LIKE ?)
        ORDER BY _id
        LIMIT ?
    """, (starts_amazigh, starts_pattern, limit))
    start_results = cursor.fetchall()

    # Contain Search (tawalt_fr)
    cursor.execute("""
        SELECT *
        FROM words
        WHERE (
        (NORMALIZE_AMAZIGH(tifinagh) LIKE ?)
        OR (NORMALIZE_FRENCH(french) LIKE ?)
        )
        AND NOT (NORMALIZE_AMAZIGH(tifinagh) LIKE ?)
        ORDER BY _id
        LIMIT ?
    """, (contains_amazigh, contains_pattern, starts_amazigh, limit))
    contain_results = cursor.fetchall()
    conn.close()
    return list(start_results) + list(contain_results)


def search_tawalt(starts_pattern, contains_pattern, starts_amazigh, contains_amazigh, limit):
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
        OR (REMOVE_DIACRITICS(LOWER(_arabic)) LIKE ?)  -- Corrected: REMOVE_DIACRITICS for arabic columns
        OR (REMOVE_DIACRITICS(LOWER(_arabic_meaning)) LIKE ?) -- Corrected: REMOVE_DIACRITICS for arabic columns
        OR (NORMALIZE_AMAZIGH(_tifinagh_in_arabic) LIKE ?)
        ORDER BY _id
        LIMIT ?
    """, (starts_amazigh, starts_pattern, starts_pattern, starts_amazigh,
          starts_pattern, starts_pattern, starts_amazigh, limit))
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
        OR (REMOVE_DIACRITICS(LOWER(_arabic)) LIKE ?)  -- Corrected: REMOVE_DIACRITICS for arabic columns
        OR (REMOVE_DIACRITICS(LOWER(_arabic_meaning)) LIKE ?) -- Corrected: REMOVE_DIACRITICS for arabic columns
        OR (NORMALIZE_AMAZIGH(_tifinagh_in_arabic) LIKE ?)
        )
        AND NOT (NORMALIZE_AMAZIGH(tifinagh) LIKE ?) -- Use NORMALIZE_AMAZIGH
        ORDER BY _id
        LIMIT ?
    """, (contains_amazigh, contains_pattern, contains_pattern, contains_amazigh,
          contains_pattern, contains_pattern, contains_amazigh,
          starts_amazigh, limit)) # Use start_search_term_amazigh for NOT LIKE
    contain_results = cursor.fetchall()
    conn.close()
    return list(start_results) + list(contain_results)

def search_eng(starts_pattern, contains_pattern, starts_amazigh, contains_amazigh, limit):
    conn = get_db_connection('eng.db')
    cursor = conn.cursor()
    conn.create_function("NORMALIZE_AMAZIGH", 1, normalize_amazigh_text)

    cursor.execute("""
        SELECT da.*, dea.sens_eng
        FROM Dictionary_Amazigh_full AS da
        LEFT JOIN Dictionary_English_Amazih_links AS dea ON da.id_lexie = dea.id_lexie
        WHERE (
            NORMALIZE_AMAZIGH(da.lexie) LIKE ?
            OR NORMALIZE_AMAZIGH(da.remarque) LIKE ?
            OR NORMALIZE_AMAZIGH(da.variante) LIKE ?
            OR LOWER(da.cg) LIKE ?
            OR NORMALIZE_AMAZIGH(da.eadata) LIKE ?
            OR NORMALIZE_AMAZIGH(da.pldata) LIKE ?
            OR LOWER(da.acc) LIKE ?
            OR LOWER(da.acc_neg) LIKE ?
            OR LOWER(da.inacc) LIKE ?
            OR LOWER(dea.sens_eng) LIKE ?
        )
        ORDER BY da.id_lexie
        LIMIT ?
    """, (starts_amazigh, starts_amazigh, starts_amazigh, starts_pattern,
          starts_amazigh, starts_amazigh, starts_pattern, starts_pattern,
          starts_pattern, starts_pattern, limit))

    start_results = cursor.fetchall()

    cursor.execute("""
      SELECT da.*, dea.sens_eng
        FROM Dictionary_Amazigh_full AS da
        LEFT JOIN Dictionary_English_Amazih_links AS dea ON da.id_lexie = dea.id_lexie
        WHERE (
            NORMALIZE_AMAZIGH(da.lexie) LIKE ?
            OR NORMALIZE_AMAZIGH(da.remarque) LIKE ?
            OR NORMALIZE_AMAZIGH(da.variante) LIKE ?
            OR LOWER(da.cg) LIKE ?
            OR NORMALIZE_AMAZIGH(da.eadata) LIKE ?
            OR NORMALIZE_AMAZIGH(da.pldata) LIKE ?
            OR LOWER(da.acc) LIKE ?
            OR LOWER(da.acc_neg) LIKE ?
            OR LOWER(da.inacc) LIKE ?
            OR LOWER(dea.sens_eng) LIKE ?
        )
        AND NOT NORMALIZE_AMAZIGH(da.lexie) LIKE ?
        ORDER BY da.id_lexie
        LIMIT ?
    """, (contains_amazigh, contains_amazigh, contains_amazigh, contains_pattern,
          contains_amazigh, contains_amazigh, contains_pattern, contains_pattern,
          contains_pattern, contains_pattern, starts_amazigh, limit))
    contain_results = cursor.fetchall()
    conn.close()

    return list(start_results) + list(contain_results)

def search_msmun_fr_m(starts_pattern, contains_pattern, starts_amazigh, contains_amazigh, limit):
    conn = get_db_connection('msmun_fr.db')
    cursor = conn.cursor()
    conn.create_function("NORMALIZE_AMAZIGH", 1, normalize_amazigh_text)
    conn.create_function("NORMALIZE_FRENCH", 1, normalize_french_text)

    cursor.execute("""
        SELECT *
        FROM table_m
        WHERE (
            NORMALIZE_AMAZIGH(word) LIKE ?
            OR NORMALIZE_FRENCH(result) LIKE ?
        )
        ORDER BY _id
        LIMIT ?
    """, (starts_amazigh, starts_pattern, limit))
    start_results = cursor.fetchall()

    cursor.execute("""
        SELECT *
        FROM table_m
        WHERE (
            NORMALIZE_AMAZIGH(word) LIKE ?
            OR NORMALIZE_FRENCH(result) LIKE ?
        )
        AND NOT NORMALIZE_AMAZIGH(word) LIKE ?
        ORDER BY _id
        LIMIT ?
    """, (contains_amazigh, contains_pattern, starts_amazigh, limit))
    contain_results = cursor.fetchall()
    conn.close()
    return list(start_results) + list(contain_results)

def search_msmun_fr_r(starts_pattern, contains_pattern, starts_amazigh, contains_amazigh, limit):
    conn = get_db_connection('msmun_fr.db')
    cursor = conn.cursor()
    conn.create_function("NORMALIZE_AMAZIGH", 1, normalize_amazigh_text)
    conn.create_function("NORMALIZE_FRENCH", 1, normalize_french_text)

    cursor.execute("""
        SELECT *
        FROM table_r
        WHERE (
            NORMALIZE_FRENCH(word) LIKE ?
            OR NORMALIZE_AMAZIGH(result) LIKE ?
        )
        ORDER BY _id
        LIMIT ?
    """, (starts_pattern, starts_amazigh, limit))
    start_results = cursor.fetchall()

    cursor.execute("""
        SELECT *
        FROM table_r
        WHERE (
            NORMALIZE_FRENCH(word) LIKE ?
            OR NORMALIZE_AMAZIGH(result) LIKE ?
        )
        AND NOT NORMALIZE_FRENCH(word) LIKE ?
        ORDER BY _id
        LIMIT ?
    """, (contains_pattern, contains_amazigh, starts_pattern, limit))
    contain_results = cursor.fetchall()
    conn.close()
    return list(start_results) + list(contain_results)


def search_msmun_ar_m_r(starts_pattern, contains_pattern, starts_amazigh, contains_amazigh, limit):
    conn = get_db_connection('msmun_ar.db')
    cursor = conn.cursor()
    conn.create_function("NORMALIZE_AMAZIGH", 1, normalize_amazigh_text)

    cursor.execute("""
        SELECT *
        FROM table_m_r
        WHERE (
            NORMALIZE_AMAZIGH(word) LIKE ?
            OR REMOVE_DIACRITICS(LOWER(result)) LIKE ?
        )
        ORDER BY _id
        LIMIT ?
    """, (starts_amazigh, starts_pattern, limit))
    start_results = cursor.fetchall()

    cursor.execute("""
        SELECT *
        FROM table_m_r
        WHERE (
            NORMALIZE_AMAZIGH(word) LIKE ?
            OR REMOVE_DIACRITICS(LOWER(result)) LIKE ?
        )
        AND NOT NORMALIZE_AMAZIGH(word) LIKE ?
        ORDER BY _id
        LIMIT ?
    """, (contains_amazigh, contains_pattern, starts_amazigh, limit))
    contain_results = cursor.fetchall()
    conn.close()
    return list(start_results) + list(contain_results)

def search_msmun_ar_r_m(starts_pattern, contains_pattern, starts_amazigh, contains_amazigh, limit):
    conn = get_db_connection('msmun_ar.db')
    cursor = conn.cursor()
    conn.create_function("NORMALIZE_AMAZIGH", 1, normalize_amazigh_text)

    cursor.execute("""
        SELECT *
        FROM table_r_m
        WHERE (
            REMOVE_DIACRITICS(LOWER(word)) LIKE ?
            OR NORMALIZE_AMAZIGH(result) LIKE ?
        )
        ORDER BY _id
        LIMIT ?
    """, (starts_pattern, starts_amazigh, limit))
    start_results = cursor.fetchall()

    cursor.execute("""
        SELECT *
        FROM table_r_m
        WHERE (
            REMOVE_DIACRITICS(LOWER(word)) LIKE ?
            OR NORMALIZE_AMAZIGH(result) LIKE ?
        )
        AND NOT REMOVE_DIACRITICS(LOWER(word)) LIKE ?
        ORDER BY _id
        LIMIT ?
    """, (contains_pattern, contains_amazigh, starts_pattern, limit))
    contain_results = cursor.fetchall()
    conn.close()
    return list(start_results) + list(contain_results)


def format_results(results):
    """Formats results from different databases."""
    dglai14_results = []
    tawalt_fr_results = []
    tawalt_results = []
    eng_results = []
    msmun_fr_m_results = []
    msmun_fr_r_results = []
    msmun_ar_m_r_results = []
    msmun_ar_r_m_results = []

    for row in results:
        if 'sens_fr' in row.keys(): # Check for dglai14.db keys
            dglai14_results.append(row)
        elif 'french' in row.keys(): # Check for tawalt_fr.db keys
            tawalt_fr_results.append(row)
        elif 'arabic' in row.keys() and 'arabic_meaning' in row.keys(): # Check for tawalt.db keys
            tawalt_results.append(row)
        elif 'sens_eng' in row.keys(): # Check for eng.db keys
            eng_results.append(row)
        elif 'table_name' in row.keys() and row['table_name'] == 'table_m' and 'msmun_fr' in row['db_name']: # Check for msmun_fr table_m
            msmun_fr_m_results.append(row)
        elif 'table_name' in row.keys() and row['table_name'] == 'table_r' and 'msmun_fr' in row['db_name']: # Check for msmun_fr table_r
            msmun_fr_r_results.append(row)
        elif 'table_name' in row.keys() and row['table_name'] == 'table_m_r' and 'msmun_ar' in row['db_name']: # Check for msmun_ar table_m_r
            msmun_ar_m_r_results.append(row)
        elif 'table_name' in row.keys() and row['table_name'] == 'table_r_m' and 'msmun_ar' in row['db_name']: # Check for msmun_ar table_r_m
            msmun_ar_r_m_results.append(row)

    html_output = ""
    html_output += format_dglai14_results(dglai14_results)
    html_output += format_tawalt_fr_results(tawalt_fr_results)
    html_output += format_tawalt_results(tawalt_results)
    html_output += format_eng_results(eng_results)
    html_output += format_msmun_fr_m_results(msmun_fr_m_results)
    html_output += format_msmun_fr_r_results(msmun_fr_r_results)
    html_output += format_msmun_ar_m_r_results(msmun_ar_m_r_results)
    html_output += format_msmun_ar_r_m_results(msmun_ar_r_m_results)
    return html_output


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

def format_tawalt_fr_results(results):
    """Formats results from tawalt_fr.db."""
    if not results:
        return ""

    html_output = ""
    for row in results:
        html_output += f"""
        <div style="background: #ffe0b2; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #ff9800; padding-bottom: 10px; margin-bottom: 10px;">
                <h3 style="color: #2c3e50; margin: 0;">{row['tifinagh'] or ''}</h3>
            </div>
        """
        if row['french']:
            html_output += f"""
            <div style="margin-bottom: 8px;">
                <strong style="color: #34495e;">French:</strong>
                <span style="color: black;">{row['french']}</span>
            </div>
            """
        html_output += "</div>"

    return html_output


def format_tawalt_results(results):
    """Formats results from tawalt.db."""
    if not results:
        return ""

    html_output = ""
    for row in results:
        html_output += f"""
        <div style="background: #fffacd; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
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

def format_eng_results(results):
    """Formats results from eng.db."""
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
                'sens_eng': set()
            }
        if row['sens_eng']:  # Handle potential NULL values
            aggregated_results[lexie_id]['sens_eng'].add(row['sens_eng'])

    html_output = ""
    for lexie_id, data in aggregated_results.items():
        html_output += f"""
        <div style="background: #d3f8d3; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #2ecc71; padding-bottom: 10px; margin-bottom: 10px;">
                <h3 style="color: #2c3e50; margin: 0;">{data['lexie'] or ''}</h3>
                <span style="background: #2ecc71; color: white; padding: 4px 8px; border-radius: 4px;">{data['cg'] or ''}</span>
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
        }

        for label, field in fields.items():
            if data[field]:
                html_output += f"""
                <div style="margin-bottom: 8px;">
                    <strong style="color: #34495e;">{label}:</strong>
                    <span style="color: black;">{data[field]}</span>
                </div>
                """
        english_translations = ", ".join(filter(None, data['sens_eng'])) # Handle null values

        if english_translations:
             html_output += f"""
             <div style="margin-bottom: 8px;">
                <strong style="color: #34495e;">English Translation:</strong>
                <span style="color: black;">{english_translations}</span>
             </div>
             """
        html_output += "</div>"

    return html_output

def format_msmun_fr_m_results(results):
    """Formats results from msmun_fr.db table_m."""
    if not results:
        return ""

    html_output = ""
    for row in results:
        html_output += f"""
        <div style="background: #fce4ec; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #f06292; padding-bottom: 10px; margin-bottom: 10px;">
                <h3 style="color: #2c3e50; margin: 0;">{row['word'] or ''}</h3>
            </div>
        """
        if row['result']:
            html_output += f"""
            <div style="margin-bottom: 8px;">
                <strong style="color: #34495e;">French Translation:</strong>
                <span style="color: black;">{row['result']}</span>
            </div>
            """
        if row['edited'] and row['edited'].lower() == 'true':
            html_output += f"""
            <div style="margin-bottom: 8px;">
                <strong style="color: #34495e;">Edited:</strong>
                <span style="color: black;">Yes</span>
            </div>
            """
        if row['favorites'] and row['favorites'].lower() == 'true':
            html_output += f"""
            <div style="margin-bottom: 8px;">
                <strong style="color: #34495e;">Favorites:</strong>
                <span style="color: black;">Yes</span>
            </div>
            """
        html_output += "</div>"
    return html_output

def format_msmun_fr_r_results(results):
    """Formats results from msmun_fr.db table_r."""
    if not results:
        return ""

    html_output = ""
    for row in results:
        html_output += f"""
        <div style="background: #f3e5f5; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #ab47bc; padding-bottom: 10px; margin-bottom: 10px;">
                <h3 style="color: #2c3e50; margin: 0;">{row['result'] or ''}</h3>
            </div>
        """
        if row['result']:
            html_output += f"""
            <div style="margin-bottom: 8px;">
                <strong style="color: #34495e;">Arabic Translation:</strong>
                <span style="color: black;">{row['word']}</span>
            </div>
            """
        if row['edited'] and row['edited'].lower() == 'true':
            html_output += f"""
            <div style="margin-bottom: 8px;">
                <strong style="color: #34495e;">Edited:</strong>
                <span style="color: black;">Yes</span>
            </div>
            """
        if row['favorites'] and row['favorites'].lower() == 'true':
            html_output += f"""
            <div style="margin-bottom: 8px;">
                <strong style="color: #34495e;">Favorites:</strong>
                <span style="color: black;">Yes</span>
            </div>
            """
        html_output += "</div>"
    return html_output


def format_msmun_ar_m_r_results(results):
    """Formats results from msmun_ar.db table_m_r."""
    if not results:
        return ""

    html_output = ""
    for row in results:
        html_output += f"""
        <div style="background: #e0f7fa; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #00bcd4; padding-bottom: 10px; margin-bottom: 10px;">
                <h3 style="color: #2c3e50; margin: 0;">{row['word'] or ''}</h3>
            </div>
        """
        if row['result']:
            html_output += f"""
            <div style="margin-bottom: 8px;">
                <strong style="color: #34495e;">Arabic Translation:</strong>
                <span style="color: black;">{row['result']}</span>
            </div>
            """
        if row['edited'] and row['edited'].lower() == 'true':
            html_output += f"""
            <div style="margin-bottom: 8px;">
                <strong style="color: #34495e;">Edited:</strong>
                <span style="color: black;">Yes</span>
            </div>
            """
        if row['favorites'] and row['favorites'].lower() == 'true':
            html_output += f"""
            <div style="margin-bottom: 8px;">
                <strong style="color: #34495e;">Favorites:</strong>
                <span style="color: black;">Yes</span>
            </div>
            """
        html_output += "</div>"
    return html_output

def format_msmun_ar_r_m_results(results):
    """Formats results from msmun_ar.db table_r_m."""
    if not results:
        return ""

    html_output = ""
    for row in results:
        html_output += f"""
        <div style="background: #e8f5e9; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #4caf50; padding-bottom: 10px; margin-bottom: 10px;">
                <h3 style="color: #2c3e50; margin: 0;">{row['result'] or ''}</h3>
            </div>
        """
        if row['result']:
            html_output += f"""
            <div style="margin-bottom: 8px;">
                <strong style="color: #34495e;">Arabic Translation:</strong>
                <span style="color: black;">{row['word']}</span>
            </div>
            """
        if row['edited'] and row['edited'].lower() == 'true':
            html_output += f"""
            <div style="margin-bottom: 8px;">
                <strong style="color: #34495e;">Edited:</strong>
                <span style="color: black;">Yes</span>
            </div>
            """
        if row['favorites'] and row['favorites'].lower() == 'true':
            html_output += f"""
            <div style="margin-bottom: 8px;">
                <strong style="color: #34495e;">Favorites:</strong>
                <span style="color: black;">Yes</span>
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
        language_select = gr.Dropdown(
            ["general", "amazigh", "arabic", "french", "english"],
            value="general", label="Language"
        )
        search_type_select = gr.Dropdown(
            ["contains", "starts", "exact"],
            value="contains", label="Search Type"
        )

    output_html = gr.HTML()

    inputs_list = [input_text, language_select, search_type_select]

    iface.load(fn=search_dictionary, inputs=inputs_list, outputs=output_html) # Load example results on start

    input_text.change(
        fn=search_dictionary,
        inputs=inputs_list,
        outputs=output_html,
        api_name="search"
    )

if __name__ == "__main__":
    iface.launch()
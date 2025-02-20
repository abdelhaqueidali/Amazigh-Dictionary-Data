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

def search_dictionary(query, language_option, exact_search):
    if not query or len(query.strip()) < 1:
        return "Please enter a search term"

    normalized_query_general = normalize_general_text(query)
    if exact_search:
        start_search_term_general = f"\\b{normalized_query_general}\\b"
        contain_search_term_general = f"\\b{normalized_query_general}\\b" # For exact search, start and contain are the same
    else:
        start_search_term_general = f"{normalized_query_general}%"
        contain_search_term_general = f"%{normalized_query_general}%"


    normalized_query_amazigh = normalize_amazigh_text(query)
    if exact_search:
        start_search_term_amazigh = f"\\b{normalized_query_amazigh}\\b"
        contain_search_term_amazigh = f"\\b{normalized_query_amazigh}\\b" # For exact search, start and contain are the same
    else:
        start_search_term_amazigh = f"{normalized_query_amazigh}%"
        contain_search_term_amazigh = f"%{normalized_query_amazigh}%"

    # --- Search dglai14.db (Prioritized) ---
    dglai14_results = search_dglai14(start_search_term_general, contain_search_term_general,start_search_term_amazigh, contain_search_term_amazigh, exact_search)

    # --- Search tawalt_fr.db (Secondary) ---
    remaining_results = 50 - len(dglai14_results)
    if remaining_results > 0:
        tawalt_fr_results = search_tawalt_fr(start_search_term_general, contain_search_term_general, start_search_term_amazigh, contain_search_term_amazigh, remaining_results, exact_search)
        remaining_results -= len(tawalt_fr_results)
    else:
        tawalt_fr_results = []

    # --- Search tawalt.db (Tertiary) ---
    if remaining_results > 0:
        tawalt_results = search_tawalt(start_search_term_general, contain_search_term_general,start_search_term_amazigh, contain_search_term_amazigh, remaining_results, exact_search)
        remaining_results -= len(tawalt_results)
    else:
        tawalt_results = []  # No need to search tawalt

    # --- Search eng.db (Quaternary) ---
    if remaining_results > 0:
      eng_results = search_eng(start_search_term_general, contain_search_term_general, start_search_term_amazigh, contain_search_term_amazigh, remaining_results, exact_search)
      remaining_results -= len(eng_results)
    else:
      eng_results = []

    # --- Search msmun_fr.db (Quinary) ---
    if remaining_results > 0:
        msmun_fr_m_results = search_msmun_fr_m(start_search_term_general, contain_search_term_general, start_search_term_amazigh, contain_search_term_amazigh, remaining_results, exact_search)
        remaining_results -= len(msmun_fr_m_results)
    else:
        msmun_fr_m_results = []

    if remaining_results > 0:
        msmun_fr_r_results = search_msmun_fr_r(start_search_term_general, contain_search_term_general, start_search_term_amazigh, contain_search_term_amazigh, remaining_results, exact_search)
        remaining_results -= len(msmun_fr_r_results)
    else:
        msmun_fr_r_results = []

    # --- Search msmun_ar.db (Senary) ---
    if remaining_results > 0:
        msmun_ar_m_r_results = search_msmun_ar_m_r(start_search_term_general, contain_search_term_general, start_search_term_amazigh, contain_search_term_amazigh, remaining_results, exact_search)
        remaining_results -= len(msmun_ar_m_r_results)
    else:
        msmun_ar_m_r_results = []

    if remaining_results > 0:
        msmun_ar_r_m_results = search_msmun_ar_r_m(start_search_term_general, contain_search_term_general, start_search_term_amazigh, contain_search_term_amazigh, remaining_results, exact_search)
        remaining_results -= len(msmun_ar_r_m_results)
    else:
        msmun_ar_r_m_results = []


    # --- Combine and Format Results ---
    html_output = format_dglai14_results(dglai14_results, language_option)  # Format dglai14 results
    html_output += format_tawalt_fr_results(tawalt_fr_results, language_option) # Format tawalt_fr results
    html_output += format_tawalt_results(tawalt_results, language_option) # Format tawalt results (if any)
    html_output += format_eng_results(eng_results, language_option)
    html_output += format_msmun_fr_m_results(msmun_fr_m_results, language_option) # Format msmun_fr table_m results
    html_output += format_msmun_fr_r_results(msmun_fr_r_results, language_option) # Format msmun_fr table_r results
    html_output += format_msmun_ar_m_r_results(msmun_ar_m_r_results, language_option)
    html_output += format_msmun_ar_r_m_results(msmun_ar_r_m_results, language_option)


    if not html_output:
        return "No results found"

    return html_output


def search_dglai14(start_search_term_general, contain_search_term_general,start_search_term_amazigh, contain_search_term_amazigh, exact_search):
    conn = get_db_connection('dglai14.db')
    cursor = conn.cursor()

    # Add the custom SQLite function for Amazigh normalization *inside* the function that uses it
    conn.create_function("NORMALIZE_AMAZIGH", 1, normalize_amazigh_text) # To be removed if the database is selectable

    like_op = "GLOB" if exact_search else "LIKE"

    # Start Search (dglai14)
    cursor.execute(f"""
        SELECT lexie.*, sens.sens_fr, sens.sens_ar,
               expression.exp_amz, expression.exp_fr, expression.exp_ar
        FROM lexie
        LEFT JOIN sens ON lexie.id_lexie = sens.id_lexie
        LEFT JOIN expression ON lexie.id_lexie = expression.id_lexie
        WHERE
        (NORMALIZE_AMAZIGH(lexie) {like_op} ?)
        OR (NORMALIZE_AMAZIGH(remarque) {like_op} ?)
        OR (NORMALIZE_AMAZIGH(variante) {like_op} ?)
        OR (REMOVE_DIACRITICS(LOWER(cg)) {like_op} ?)
        OR (NORMALIZE_AMAZIGH(eadata) {like_op} ?)
        OR (NORMALIZE_AMAZIGH(pldata) {like_op} ?)
        OR (REMOVE_DIACRITICS(LOWER(acc)) {like_op} ?)
        OR (REMOVE_DIACRITICS(LOWER(acc_neg)) {like_op} ?)
        OR (REMOVE_DIACRITICS(LOWER(inacc)) {like_op} ?)
        OR (REMOVE_DIACRITICS(LOWER(fel)) {like_op} ?)
        OR (REMOVE_DIACRITICS(LOWER(fea)) {like_op} ?)
        OR (REMOVE_diacritics(LOWER(fpel)) {like_op} ?)
        OR (REMOVE_DIACRITICS(LOWER(fpea)) {like_op} ?)
        OR (REMOVE_DIACRITICS(LOWER(sens_ar)) {like_op} ?)
        OR (NORMALIZE_AMAZIGH(expression.exp_amz) {like_op} ?)
        OR (REMOVE_DIACRITICS(LOWER(expression.exp_ar)) {like_op} ?)

        ORDER BY lexie.id_lexie
        LIMIT 50
    """, (start_search_term_amazigh, start_search_term_amazigh, start_search_term_amazigh, start_search_term_general,
          start_search_term_amazigh, start_search_term_amazigh, start_search_term_general, start_search_term_general, start_search_term_general,
          start_search_term_general, start_search_term_general, start_search_term_general, start_search_term_general,
          start_search_term_general, start_search_term_amazigh, start_search_term_general))
    start_results = cursor.fetchall()

    # Contain Search (dglai14)
    cursor.execute(f"""
        SELECT lexie.*, sens.sens_fr, sens.sens_ar,
               expression.exp_amz, expression.exp_fr, expression.exp_ar
        FROM lexie
        LEFT JOIN sens ON lexie.id_lexie = sens.id_lexie
        LEFT JOIN expression ON lexie.id_lexie = expression.id_lexie
        WHERE (
        (NORMALIZE_AMAZIGH(lexie) {like_op} ?)
        OR (NORMALIZE_AMAZIGH(remarque) {like_op} ?)
        OR (NORMALIZE_AMAZIGH(variante) {like_op} ?)
        OR (REMOVE_DIACRITICS(LOWER(cg)) {like_op} ?)
        OR (NORMALIZE_AMAZIGH(eadata) {like_op} ?)
        OR (NORMALIZE_AMAZIGH(pldata) {like_op} ?)
        OR (REMOVE_DIACRITICS(LOWER(acc)) {like_op} ?)
        OR (REMOVE_DIACRITICS(LOWER(acc_neg)) {like_op} ?)
        OR (REMOVE_DIACRITICS(LOWER(inacc)) {like_op} ?)
        OR (REMOVE_DIACRITICS(LOWER(fel)) {like_op} ?)
        OR (REMOVE_DIACRITICS(LOWER(fea)) {like_op} ?)
        OR (REMOVE_DIACRITICS(LOWER(fpel)) {like_op} ?)
        OR (REMOVE_DIACRITICS(LOWER(fpea)) {like_op} ?)
        OR (REMOVE_DIACRITICS(LOWER(sens_ar)) {like_op} ?)
        OR (NORMALIZE_AMAZIGH(expression.exp_amz) {like_op} ?)
        OR (REMOVE_DIACRITICS(LOWER(expression.exp_ar)) {like_op} ?)
        )
        AND NOT (NORMALIZE_AMAZIGH(lexie) {like_op} ?)
        ORDER BY lexie.id_lexie
        LIMIT 50
    """, (contain_search_term_amazigh, contain_search_term_amazigh, contain_search_term_amazigh, contain_search_term_general,
          contain_search_term_amazigh, contain_search_term_amazigh, contain_search_term_general, contain_search_term_general, contain_search_term_general,
          contain_search_term_general, contain_search_term_general, contain_search_term_general, contain_search_term_general,
          contain_search_term_general, contain_search_term_amazigh, contain_search_term_general,
          start_search_term_amazigh))  # Use start_search_term_amazigh for the NOT LIKE part
    contain_results = cursor.fetchall()
    conn.close()
    return list(start_results) + list(contain_results)

def search_tawalt_fr(start_search_term_general, contain_search_term_general, start_search_term_amazigh, contain_search_term_amazigh, limit, exact_search):
    conn = get_db_connection('tawalt_fr.db')
    cursor = conn.cursor()

    # Add the custom SQLite function for Amazigh normalization
    conn.create_function("NORMALIZE_AMAZIGH", 1, normalize_amazigh_text)
    conn.create_function("NORMALIZE_FRENCH", 1, normalize_french_text)

    like_op = "GLOB" if exact_search else "LIKE"

    # Start Search (tawalt_fr)
    cursor.execute(f"""
        SELECT *
        FROM words
        WHERE
        (NORMALIZE_AMAZIGH(tifinagh) {like_op} ?)
        OR (NORMALIZE_FRENCH(french) {like_op} ?)
        ORDER BY _id
        LIMIT ?
    """, (start_search_term_amazigh, start_search_term_general, limit))
    start_results = cursor.fetchall()

    # Contain Search (tawalt_fr)
    cursor.execute(f"""
        SELECT *
        FROM words
        WHERE (
        (NORMALIZE_AMAZIGH(tifinagh) {like_op} ?)
        OR (NORMALIZE_FRENCH(french) {like_op} ?)
        )
        AND NOT (NORMALIZE_AMAZIGH(tifinagh) {like_op} ?)
        ORDER BY _id
        LIMIT ?
    """, (contain_search_term_amazigh, contain_search_term_general, start_search_term_amazigh, limit))
    contain_results = cursor.fetchall()
    conn.close()
    return list(start_results) + list(contain_results)


def search_tawalt(start_search_term_general, contain_search_term_general,start_search_term_amazigh, contain_search_term_amazigh, limit, exact_search):
    conn = get_db_connection('tawalt.db')
    cursor = conn.cursor()

    # Add the custom SQLite function for Amazigh normalization
    conn.create_function("NORMALIZE_AMAZIGH", 1, normalize_amazigh_text)  #To be removed if the database is selectable
    like_op = "GLOB" if exact_search else "LIKE"

    # Start Search (tawalt)
    cursor.execute(f"""
        SELECT *
        FROM words
        WHERE
        (NORMALIZE_AMAZIGH(tifinagh) {like_op} ?)
        OR (REMOVE_DIACRITICS(LOWER(arabic)) {like_op} ?)
        OR (REMOVE_DIACRITICS(LOWER(arabic_meaning)) {like_op} ?)
        OR (NORMALIZE_AMAZIGH(tifinagh_in_arabic) {like_op} ?)
        OR (REMOVE_DIACRITICS(LOWER(_arabic)) {like_op} ?)
        OR (REMOVE_DIACRITICS(LOWER(_arabic_meaning)) {like_op} ?)
        OR (NORMALIZE_AMAZIGH(_tifinagh_in_arabic) {like_op} ?)
        ORDER BY _id
        LIMIT ?
    """, (start_search_term_amazigh, start_search_term_general, start_search_term_general, start_search_term_amazigh,
          start_search_term_general, start_search_term_general, start_search_term_amazigh, limit))
    start_results = cursor.fetchall()

    # Contain Search (tawalt)
    cursor.execute(f"""
        SELECT *
        FROM words
        WHERE (
        (NORMALIZE_AMAZIGH(tifinagh) {like_op} ?)
        OR (REMOVE_DIACRITICS(LOWER(arabic)) {like_op} ?)
        OR (REMOVE_DIACRITICS(LOWER(arabic_meaning)) {like_op} ?)
        OR (NORMALIZE_AMAZIGH(tifinagh_in_arabic) {like_op} ?)
        OR (REMOVE_DIACRITICS(LOWER(_arabic)) {like_op} ?)
        OR (REMOVE_DIACRITICS(LOWER(_arabic_meaning)) {like_op} ?)
        OR (NORMALIZE_AMAZIGH(_tifinagh_in_arabic) {like_op} ?)
        )
        AND NOT (NORMALIZE_AMAZIGH(tifinagh) {like_op} ?)
        ORDER BY _id
        LIMIT ?
    """, (contain_search_term_amazigh, contain_search_term_general, contain_search_term_general, contain_search_term_amazigh,
          contain_search_term_general, contain_search_term_general, contain_search_term_amazigh,
          start_search_term_amazigh, limit)) # Use start_search_term_amazigh for NOT LIKE
    contain_results = cursor.fetchall()
    conn.close()
    return list(start_results) + list(contain_results)

def search_eng(start_search_term_general, contain_search_term_general, start_search_term_amazigh, contain_search_term_amazigh, limit, exact_search):
    conn = get_db_connection('eng.db')
    cursor = conn.cursor()
    conn.create_function("NORMALIZE_AMAZIGH", 1, normalize_amazigh_text)
    like_op = "GLOB" if exact_search else "LIKE"

    cursor.execute(f"""
        SELECT da.*, dea.sens_eng
        FROM Dictionary_Amazigh_full AS da
        LEFT JOIN Dictionary_English_Amazih_links AS dea ON da.id_lexie = dea.id_lexie
        WHERE (
            NORMALIZE_AMAZIGH(da.lexie) {like_op} ?
            OR NORMALIZE_AMAZIGH(da.remarque) {like_op} ?
            OR NORMALIZE_AMAZIGH(da.variante) {like_op} ?
            OR LOWER(da.cg) {like_op} ?
            OR NORMALIZE_AMAZIGH(da.eadata) {like_op} ?
            OR NORMALIZE_AMAZIGH(da.pldata) {like_op} ?
            OR LOWER(da.acc) {like_op} ?
            OR LOWER(da.acc_neg) {like_op} ?
            OR LOWER(da.inacc) {like_op} ?
            OR LOWER(dea.sens_eng) {like_op} ?
        )
        ORDER BY da.id_lexie
        LIMIT ?
    """, (start_search_term_amazigh, start_search_term_amazigh, start_search_term_amazigh, start_search_term_general,
          start_search_term_amazigh, start_search_term_amazigh, start_search_term_general, start_search_term_general,
          start_search_term_general, start_search_term_general, limit))

    start_results = cursor.fetchall()

    cursor.execute(f"""
      SELECT da.*, dea.sens_eng
        FROM Dictionary_Amazigh_full AS da
        LEFT JOIN Dictionary_English_Amazih_links AS dea ON da.id_lexie = dea.id_lexie
        WHERE (
            NORMALIZE_AMAZIGH(da.lexie) {like_op} ?
            OR NORMALIZE_AMAZIGH(da.remarque) {like_op} ?
            OR NORMALIZE_AMAZIGH(da.variante) {like_op} ?
            OR LOWER(da.cg) {like_op} ?
            OR NORMALIZE_AMAZIGH(da.eadata) {like_op} ?
            OR NORMALIZE_AMAZIGH(da.pldata) {like_op} ?
            OR LOWER(da.acc) {like_op} ?
            OR LOWER(da.acc_neg) {like_op} ?
            OR LOWER(da.inacc) {like_op} ?
            OR LOWER(dea.sens_eng) {like_op} ?
        )
        AND NOT NORMALIZE_AMAZIGH(da.lexie) {like_op} ?
        ORDER BY da.id_lexie
        LIMIT ?
    """, (contain_search_term_amazigh, contain_search_term_amazigh, contain_search_term_amazigh, contain_search_term_general,
          contain_search_term_amazigh, contain_search_term_amazigh, contain_search_term_general, contain_search_term_general,
          contain_search_term_general, contain_search_term_general, start_search_term_amazigh, limit))
    contain_results = cursor.fetchall()
    conn.close()

    return list(start_results) + list(contain_results)

def search_msmun_fr_m(start_search_term_general, contain_search_term_general, start_search_term_amazigh, contain_search_term_amazigh, limit, exact_search):
    conn = get_db_connection('msmun_fr.db')
    cursor = conn.cursor()
    conn.create_function("NORMALIZE_AMAZIGH", 1, normalize_amazigh_text)
    conn.create_function("NORMALIZE_FRENCH", 1, normalize_french_text)
    like_op = "GLOB" if exact_search else "LIKE"

    cursor.execute(f"""
        SELECT *
        FROM table_m
        WHERE (
            NORMALIZE_AMAZIGH(word) {like_op} ?
            OR NORMALIZE_FRENCH(result) {like_op} ?
        )
        ORDER BY _id
        LIMIT ?
    """, (start_search_term_amazigh, start_search_term_general, limit))
    start_results = cursor.fetchall()

    cursor.execute(f"""
        SELECT *
        FROM table_m
        WHERE (
            NORMALIZE_AMAZIGH(word) {like_op} ?
            OR NORMALIZE_FRENCH(result) {like_op} ?
        )
        AND NOT NORMALIZE_AMAZIGH(word) {like_op} ?
        ORDER BY _id
        LIMIT ?
    """, (contain_search_term_amazigh, contain_search_term_general, start_search_term_amazigh, limit))
    contain_results = cursor.fetchall()
    conn.close()
    return list(start_results) + list(contain_results)

def search_msmun_fr_r(start_search_term_general, contain_search_term_general, start_search_term_amazigh, contain_search_term_amazigh, limit, exact_search):
    conn = get_db_connection('msmun_fr.db')
    cursor = conn.cursor()
    conn.create_function("NORMALIZE_AMAZIGH", 1, normalize_amazigh_text)
    conn.create_function("NORMALIZE_FRENCH", 1, normalize_french_text)
    like_op = "GLOB" if exact_search else "LIKE"

    cursor.execute(f"""
        SELECT *
        FROM table_r
        WHERE (
            NORMALIZE_FRENCH(word) {like_op} ?
            OR NORMALIZE_AMAZIGH(result) {like_op} ?
        )
        ORDER BY _id
        LIMIT ?
    """, (start_search_term_general, start_search_term_amazigh, limit))
    start_results = cursor.fetchall()

    cursor.execute(f"""
        SELECT *
        FROM table_r
        WHERE (
            NORMALIZE_FRENCH(word) {like_op} ?
            OR NORMALIZE_AMAZIGH(result) {like_op} ?
        )
        AND NOT NORMALIZE_FRENCH(word) {like_op} ?
        ORDER BY _id
        LIMIT ?
    """, (contain_search_term_general, contain_search_term_amazigh, start_search_term_general, limit))
    contain_results = cursor.fetchall()
    conn.close()
    return list(start_results) + list(contain_results)


def search_msmun_ar_m_r(start_search_term_general, contain_search_term_general, start_search_term_amazigh, contain_search_term_amazigh, limit, exact_search):
    conn = get_db_connection('msmun_ar.db')
    cursor = conn.cursor()
    conn.create_function("NORMALIZE_AMAZIGH", 1, normalize_amazigh_text)
    like_op = "GLOB" if exact_search else "LIKE"

    cursor.execute(f"""
        SELECT *
        FROM table_m_r
        WHERE (
            NORMALIZE_AMAZIGH(word) {like_op} ?
            OR REMOVE_DIACRITICS(LOWER(result)) {like_op} ?
        )
        ORDER BY _id
        LIMIT ?
    """, (start_search_term_amazigh, start_search_term_general, limit))
    start_results = cursor.fetchall()

    cursor.execute(f"""
        SELECT *
        FROM table_m_r
        WHERE (
            NORMALIZE_AMAZIGH(word) {like_op} ?
            OR REMOVE_DIACRITICS(LOWER(result)) {like_op} ?
        )
        AND NOT NORMALIZE_AMAZIGH(word) {like_op} ?
        ORDER BY _id
        LIMIT ?
    """, (contain_search_term_amazigh, contain_search_term_general, start_search_term_amazigh, limit))
    contain_results = cursor.fetchall()
    conn.close()
    return list(start_results) + list(contain_results)

def search_msmun_ar_r_m(start_search_term_general, contain_search_term_general, start_search_term_amazigh, contain_search_term_amazigh, limit, exact_search):
    conn = get_db_connection('msmun_ar.db')
    cursor = conn.cursor()
    conn.create_function("NORMALIZE_AMAZIGH", 1, normalize_amazigh_text)
    like_op = "GLOB" if exact_search else "LIKE"

    cursor.execute(f"""
        SELECT *
        FROM table_r_m
        WHERE (
            REMOVE_DIACRITICS(LOWER(word)) {like_op} ?
            OR NORMALIZE_AMAZIGH(result) {like_op} ?
        )
        ORDER BY _id
        LIMIT ?
    """, (start_search_term_general, start_search_term_amazigh, limit))
    start_results = cursor.fetchall()

    cursor.execute(f"""
        SELECT *
        FROM table_r_m
        WHERE (
            REMOVE_DIACRITICS(LOWER(word)) {like_op} ?
            OR NORMALIZE_AMAZIGH(result) {like_op} ?
        )
        AND NOT REMOVE_DIACRITICS(LOWER(word)) {like_op} ?
        ORDER BY _id
        LIMIT ?
    """, (contain_search_term_general, contain_search_term_amazigh, start_search_term_general, limit))
    contain_results = cursor.fetchall()
    conn.close()
    return list(start_results) + list(contain_results)


def format_dglai14_results(results, language_option):
    """Formats results from dglai14.db based on language option."""
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
        display_result = False
        if language_option == 'General':
            display_result = True
        elif language_option == 'Amazigh' and data['lexie']:
            display_result = True
        elif language_option == 'English' and any(data['sens_frs']) or any(data['sens_ars']): # Check for any translation for now
            display_result = True
        elif language_option == 'Arabic' and any(data['sens_ars']):
            display_result = True
        elif language_option == 'French' and any(data['sens_frs']):
            display_result = True

        if display_result:
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

            if language_option in ['General', 'French'] and french_translations:
                html_output += f"""
                <div style="margin-bottom: 8px;">
                    <strong style="color: #34495e;">French Translation:</strong>
                    <span style="color: black;">{french_translations}</span>
                </div>
                """
            if language_option in ['General', 'Arabic'] and arabic_translations:
                html_output += f"""
                <div style="margin-bottom: 8px;">
                    <strong style="color: #34495e;">Arabic Translation:</strong>
                    <span style="color: black;">{arabic_translations}</span>
                </div>
                """

            if language_option in ['General', 'Amazigh'] and data['expressions']:
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
                    if language_option in ['General', 'French'] and french_exp_translations:
                        html_output += f"""
                        <div style="margin-bottom: 4px;">
                            <strong style="color: #546e7a;">French:</strong>
                            <span style="color: black;">{french_exp_translations or ''}</span>
                        </div>
                        """
                    if language_option in ['General', 'Arabic'] and arabic_exp_translations:
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

def format_tawalt_fr_results(results, language_option):
    """Formats results from tawalt_fr.db based on language option."""
    if not results:
        return ""

    html_output = ""
    for row in results:
        display_result = False
        if language_option == 'General':
            display_result = True
        elif language_option == 'Amazigh' and row['tifinagh']:
            display_result = True
        elif language_option == 'French' and row['french']:
            display_result = True
        elif language_option == 'English' and row['french']: # Assuming french is english for now
            display_result = True

        if display_result:
            html_output += f"""
            <div style="background: #ffe0b2; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #ff9800; padding-bottom: 10px; margin-bottom: 10px;">
                    <h3 style="color: #2c3e50; margin: 0;">{row['tifinagh'] or ''}</h3>
                </div>
            """
            if language_option in ['General', 'French', 'English'] and row['french']:
                html_output += f"""
                <div style="margin-bottom: 8px;">
                    <strong style="color: #34495e;">French:</strong>
                    <span style="color: black;">{row['french']}</span>
                </div>
                """
            html_output += "</div>"

    return html_output


def format_tawalt_results(results, language_option):
    """Formats results from tawalt.db based on language option."""
    if not results:
        return ""

    html_output = ""
    for row in results:
        display_result = False
        if language_option == 'General':
            display_result = True
        elif language_option == 'Amazigh' and row['tifinagh']:
            display_result = True
        elif language_option == 'Arabic' and (row['arabic'] or row['arabic_meaning']):
            display_result = True
        elif language_option == 'English' and (row['arabic'] or row['arabic_meaning']): # Assuming arabic somewhat relates to english for now

            display_result = True

        if display_result:
            html_output += f"""
            <div style="background: #fffacd; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #3498db; padding-bottom: 10px; margin-bottom: 10px;">
                    <h3 style="color: #2c3e50; margin: 0;">{row['tifinagh'] or ''}</h3>
                </div>
            """
            if language_option in ['General', 'Arabic', 'English'] and row['arabic']:
                html_output += f"""
                <div style="margin-bottom: 8px;">
                    <strong style="color: #34495e;">Arabic:</strong>
                    <span style="color: black;">{row['arabic']}</span>
                </div>
                """
            if language_option in ['General', 'Arabic', 'English'] and row['arabic_meaning']:
                html_output += f"""
                <div style="margin-bottom: 8px;">
                    <strong style="color: #34495e;">Arabic Meaning:</strong>
                    <span style="color: black;">{row['arabic_meaning']}</span>
                </div>
                """
            html_output += "</div>"

    return html_output

def format_eng_results(results, language_option):
    """Formats results from eng.db based on language option."""
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
        display_result = False
        if language_option == 'General':
            display_result = True
        elif language_option == 'Amazigh' and data['lexie']:
            display_result = True
        elif language_option == 'English' and any(data['sens_eng']):
            display_result = True

        if display_result:
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

            if language_option in ['General', 'English'] and english_translations:
                 html_output += f"""
                 <div style="margin-bottom: 8px;">
                    <strong style="color: #34495e;">English Translation:</strong>
                    <span style="color: black;">{english_translations}</span>
                 </div>
                 """
            html_output += "</div>"

    return html_output

def format_msmun_fr_m_results(results, language_option):
    """Formats results from msmun_fr.db table_m based on language option."""
    if not results:
        return ""

    html_output = ""
    for row in results:
        display_result = False
        if language_option == 'General':
            display_result = True
        elif language_option == 'Amazigh' and row['word']:
            display_result = True
        elif language_option == 'French' and row['result']:
            display_result = True
        elif language_option == 'English' and row['result']: # Assuming french is english for now
            display_result = True

        if display_result:
            html_output += f"""
            <div style="background: #fce4ec; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #f06292; padding-bottom: 10px; margin-bottom: 10px;">
                    <h3 style="color: #2c3e50; margin: 0;">{row['word'] or ''}</h3>
                </div>
            """
            if language_option in ['General', 'French', 'English'] and row['result']:
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

def format_msmun_fr_r_results(results, language_option):
    """Formats results from msmun_fr.db table_r based on language option."""
    if not results:
        return ""

    html_output = ""
    for row in results:
        display_result = False
        if language_option == 'General':
            display_result = True
        elif language_option == 'Amazigh' and row['result']:
            display_result = True
        elif language_option == 'Arabic' and row['word']:
            display_result = True
        elif language_option == 'English' and row['word']: # Assuming arabic is english for now
            display_result = True

        if display_result:
            html_output += f"""
            <div style="background: #f3e5f5; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #ab47bc; padding-bottom: 10px; margin-bottom: 10px;">
                    <h3 style="color: #2c3e50; margin: 0;">{row['result'] or ''}</h3>
                </div>
            """
            if language_option in ['General', 'Arabic', 'English'] and row['word']:
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


def format_msmun_ar_m_r_results(results, language_option):
    """Formats results from msmun_ar.db table_m_r based on language option."""
    if not results:
        return ""

    html_output = ""
    for row in results:
        display_result = False
        if language_option == 'General':
            display_result = True
        elif language_option == 'Amazigh' and row['word']:
            display_result = True
        elif language_option == 'Arabic' and row['result']:
            display_result = True
        elif language_option == 'English' and row['result']: # Assuming arabic is english for now
            display_result = True

        if display_result:
            html_output += f"""
            <div style="background: #e0f7fa; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #00bcd4; padding-bottom: 10px; margin-bottom: 10px;">
                    <h3 style="color: #2c3e50; margin: 0;">{row['word'] or ''}</h3>
                </div>
            """
            if language_option in ['General', 'Arabic', 'English'] and row['result']:
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

def format_msmun_ar_r_m_results(results, language_option):
    """Formats results from msmun_ar.db table_r_m based on language option."""
    if not results:
        return ""

    html_output = ""
    for row in results:
        display_result = False
        if language_option == 'General':
            display_result = True
        elif language_option == 'Amazigh' and row['result']:
            display_result = True
        elif language_option == 'Arabic' and row['word']:
            display_result = True
        elif language_option == 'English' and row['word']: # Assuming arabic is english for now
            display_result = True

        if display_result:
            html_output += f"""
            <div style="background: #e8f5e9; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #4caf50; padding-bottom: 10px; margin-bottom: 10px;">
                    <h3 style="color: #2c3e50; margin: 0;">{row['result'] or ''}</h3>
                </div>
            """
            if language_option in ['General', 'Arabic', 'English'] and row['word']:
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
        language_option = gr.Radio(
            ["General", "Amazigh", "English", "Arabic", "French"],
            label="Language Option",
            value="General" # Default to General
        )
        exact_search = gr.Checkbox(label="Exact Search")

    output_html = gr.HTML()

    input_text.change(
        fn=search_dictionary,
        inputs=[input_text, language_option, exact_search],
        outputs=output_html,
        api_name="search"
    )
    language_option.change(
        fn=search_dictionary,
        inputs=[input_text, language_option, exact_search],
        outputs=output_html,
        api_name="search_language_change"
    )
    exact_search.change(
        fn=search_dictionary,
        inputs=[input_text, language_option, exact_search],
        outputs=output_html,
        api_name="search_exact_change"
    )


if __name__ == "__main__":
    iface.launch()
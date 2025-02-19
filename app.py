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

    # --- Search tawalt_fr.db (Secondary) ---
    remaining_results = 50 - len(dglai14_results)
    if remaining_results > 0:
        tawalt_fr_results = search_tawalt_fr(start_search_term_general, contain_search_term_general, start_search_term_amazigh, contain_search_term_amazigh, remaining_results)
        remaining_results -= len(tawalt_fr_results)
    else:
        tawalt_fr_results = []

    # --- Search tawalt.db (Tertiary) ---
    if remaining_results > 0:
        tawalt_results = search_tawalt(start_search_term_general, contain_search_term_general,start_search_term_amazigh, contain_search_term_amazigh, remaining_results)
        remaining_results -= len(tawalt_results)
    else:
        tawalt_results = []  # No need to search tawalt

    # --- Search eng.db (Quaternary) ---
    if remaining_results > 0:
      eng_results = search_eng(start_search_term_general, contain_search_term_general, start_search_term_amazigh, contain_search_term_amazigh, remaining_results)
      remaining_results -= len(eng_results)
    else:
      eng_results = []

    # --- Search msmun_ar.db (Quinary) ---
    if remaining_results > 0:
        msmun_ar_m_r_results = search_msmun_ar_m_r(start_search_term_general, contain_search_term_general, start_search_term_amazigh, contain_search_term_amazigh, remaining_results)
        remaining_results -= len(msmun_ar_m_r_results)
    else:
        msmun_ar_m_r_results = []

    if remaining_results > 0:
        msmun_ar_r_m_results = search_msmun_ar_r_m(start_search_term_general, contain_search_term_general, start_search_term_amazigh, contain_search_term_amazigh, remaining_results)
        remaining_results -= len(msmun_ar_r_m_results)
    else:
        msmun_ar_r_m_results = []

    # --- Search msmun_بق.db (Senary) ---
    if remaining_results > 0:
        msmun_بق_m_results = search_msmun_بق_m(start_search_term_general, contain_search_term_general, start_search_term_amazigh, contain_search_term_amazigh, remaining_results)
        remaining_results -= len(msmun_بق_m_results)
    else:
        msmun_بق_m_results = []

    if remaining_results > 0:
        msmun_بق_r_results = search_msmun_بق_r(start_search_term_general, contain_search_term_general, start_search_term_amazigh, contain_search_term_amazigh, remaining_results)
        remaining_results -= len(msmun_بق_r_results)
    else:
        msmun_بق_r_results = []


    # --- Combine and Format Results ---
    html_output = format_dglai14_results(dglai14_results)  # Format dglai14 results
    html_output += format_tawalt_fr_results(tawalt_fr_results) # Format tawalt_fr results
    html_output += format_tawalt_results(tawalt_results) # Format tawalt results (if any)
    html_output += format_eng_results(eng_results)
    html_output += format_msmun_ar_m_r_results(msmun_ar_m_r_results)
    html_output += format_msmun_ar_r_m_results(msmun_ar_r_m_results)
    html_output += format_msmun_بق_m_results(msmun_بق_m_results) # Format msmun_بق table_m results
    html_output += format_msmun_بق_r_results(msmun_بق_r_results) # Format msmun_بق table_r results


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
        OR (NORMALIZE_AMAZIGH(expression.exp_amz) LIKE ?) -- Use NORMALIZE_AMAZIGH for exp_amz
        OR (REMOVE_DIACRITICS(LOWER(expression.exp_ar)) LIKE ?)

        ORDER BY lexie.id_lexie
        LIMIT 50
    """, (start_search_term_amazigh, start_search_term_amazigh, start_search_term_amazigh, start_search_term_general,
          start_search_term_amazigh, start_search_term_amazigh, start_search_term_general, start_search_term_general, start_search_term_general,
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
        OR (NORMALIZE_AMAZIGH(expression.exp_amz) LIKE ?) -- Use NORMALIZE_AMAZIGH for exp_amz
        OR (REMOVE_DIACRITICS(LOWER(expression.exp_ar)) LIKE ?)
        )
        AND NOT (NORMALIZE_AMAZIGH(lexie) LIKE ?) -- Use NORMALIZE_AMAZIGH here too
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

def search_tawalt_fr(start_search_term_general, contain_search_term_general, start_search_term_amazigh, contain_search_term_amazigh, limit):
    conn = get_db_connection('tawalt_fr.db')
    cursor = conn.cursor()

    # Add the custom SQLite function for Amazigh normalization
    conn.create_function("NORMALIZE_AMAZIGH", 1, normalize_amazigh_text)
    conn.create_function("NORMALIZE_FRENCH", 1, normalize_french_text)

    # Start Search (tawalt_fr)
    cursor.execute("""
        SELECT *
        FROM words
        WHERE
        (NORMALIZE_AMAZIGH(tifinagh) LIKE ?)
        OR (NORMALIZE_FRENCH(french) LIKE ?)
        ORDER BY _id
        LIMIT ?
    """, (start_search_term_amazigh, start_search_term_general, limit))
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
    """, (contain_search_term_amazigh, contain_search_term_general, start_search_term_amazigh, limit))
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
        OR (NORMALIZE_AMAZIGH(_arabic) LIKE ?)
        OR (NORMALIZE_AMAZIGH(_arabic_meaning) LIKE ?)
        OR (NORMALIZE_AMAZIGH(_tifinagh_in_arabic) LIKE ?)
        ORDER BY _id
        LIMIT ?
    """, (start_search_term_amazigh, start_search_term_general, start_search_term_general, start_search_term_amazigh,
          start_search_term_amazigh, start_search_term_amazigh, start_search_term_amazigh, limit))
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
        OR (NORMALIZE_AMAZIGH(_arabic) LIKE ?)
        OR (NORMALIZE_AMAZIGH(_arabic_meaning) LIKE ?)
        OR (NORMALIZE_AMAZIGH(_tifinagh_in_arabic) LIKE ?)
        )
        AND NOT (NORMALIZE_AMAZIGH(tifinagh) LIKE ?) -- Use NORMALIZE_AMAZIGH
        ORDER BY _id
        LIMIT ?
    """, (contain_search_term_amazigh, contain_search_term_general, contain_search_term_general, contain_search_term_amazigh,
          contain_search_term_amazigh, contain_search_term_amazigh, contain_search_term_amazigh,
          start_search_term_amazigh, limit)) # Use start_search_term_amazigh for NOT LIKE
    contain_results = cursor.fetchall()
    conn.close()
    return list(start_results) + list(contain_results)

def search_eng(start_search_term_general, contain_search_term_general, start_search_term_amazigh, contain_search_term_amazigh, limit):
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
    """, (start_search_term_amazigh, start_search_term_amazigh, start_search_term_amazigh, start_search_term_general,
          start_search_term_amazigh, start_search_term_amazigh, start_search_term_general, start_search_term_general,
          start_search_term_general, start_search_term_general, limit))

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
    """, (contain_search_term_amazigh, contain_search_term_amazigh, contain_search_term_amazigh, contain_search_term_general,
          contain_search_term_amazigh, contain_search_term_amazigh, contain_search_term_general, contain_search_term_general,
          contain_search_term_general, contain_search_term_general, start_search_term_amazigh, limit))
    contain_results = cursor.fetchall()
    conn.close()

    return list(start_results) + list(contain_results)

def search_msmun_ar_m_r(start_search_term_general, contain_search_term_general, start_search_term_amazigh, contain_search_term_amazigh, limit):
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
    """, (start_search_term_amazigh, start_search_term_general, limit))
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
    """, (contain_search_term_amazigh, contain_search_term_general, start_search_term_amazigh, limit))
    contain_results = cursor.fetchall()
    conn.close()
    return list(start_results) + list(contain_results)

def search_msmun_ar_r_m(start_search_term_general, contain_search_term_general, start_search_term_amazigh, contain_search_term_amazigh, limit):
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
    """, (start_search_term_general, start_search_term_amazigh, limit))
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
    """, (contain_search_term_general, contain_search_term_amazigh, start_search_term_general, limit))
    contain_results = cursor.fetchall()
    conn.close()
    return list(start_results) + list(contain_results)

def search_msmun_بق_m(start_search_term_general, contain_search_term_general, start_search_term_amazigh, contain_search_term_amazigh, limit):
    conn = get_db_connection('msmun_بق.db')
    cursor = conn.cursor()
    conn.create_function("NORMALIZE_AMAZIGH", 1, normalize_amazigh_text)
    conn.create_function("NORMALIZE_FRENCH", 1, normalize_french_text)

    cursor.execute("""
        SELECT *
        FROM table_m
        WHERE (
            NORMALIZE_AMAZIGH(word) LIKE ?
            OR NORMALIZE_FRENCH(result) LIKE ?
            OR NORMALIZE_AMAZIGH(tfiar) LIKE ?
        )
        ORDER BY _id
        LIMIT ?
    """, (start_search_term_amazigh, start_search_term_general, start_search_term_amazigh, limit))
    start_results = cursor.fetchall()

    cursor.execute("""
        SELECT *
        FROM table_m
        WHERE (
            NORMALIZE_AMAZIGH(word) LIKE ?
            OR NORMALIZE_FRENCH(result) LIKE ?
            OR NORMALIZE_AMAZIGH(tfiar) LIKE ?
        )
        AND NOT NORMALIZE_AMAZIGH(word) LIKE ?
        ORDER BY _id
        LIMIT ?
    """, (contain_search_term_amazigh, contain_search_term_general, contain_search_term_amazigh, start_search_term_amazigh, limit))
    contain_results = cursor.fetchall()
    conn.close()
    return list(start_results) + list(contain_results)

def search_msmun_بق_r(start_search_term_general, contain_search_term_general, start_search_term_amazigh, contain_search_term_amazigh, limit):
    conn = get_db_connection('msmun_بق.db')
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
    """, (start_search_term_general, start_search_term_amazigh, limit))
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
    """, (contain_search_term_general, contain_search_term_amazigh, start_search_term_general, limit))
    contain_results = cursor.fetchall()
    conn.close()
    return list(start_results) + list(contain_results)


def format_dglai14_results(results):
    """Formats results from dglai14.db."""
    return _format_dglai14_results(results) # No change needed here, refactoring in helper function


def format_tawalt_fr_results(results):
    """Formats results from tawalt_fr.db."""
    return _format_tawalt_fr_results(results) # No change needed here, refactoring in helper function


def format_tawalt_results(results):
    """Formats results from tawalt.db."""
    return _format_tawalt_results(results) # No change needed here, refactoring in helper function


def format_eng_results(results):
    """Formats results from eng.db."""
    return _format_eng_results(results) # No change needed here, refactoring in helper function


def format_msmun_ar_m_r_results(results):
    """Formats results from msmun_ar.db table_m_r."""
    return _format_msmun_ar_m_r_results(results) # No change needed here, refactoring in helper function


def format_msmun_ar_r_m_results(results):
    """Formats results from msmun_ar.db table_r_m."""
    return _format_msmun_ar_r_m_results(results) # No change needed here, refactoring in helper function

def format_msmun_بق_m_results(results):
    """Formats results from msmun_بق.db table_m."""
    if not results:
        return ""

    html_output = ""
    for row in results:
        html_output += f"""
        <div style="background: #f0f0f0; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #9e9e9e; padding-bottom: 10px; margin-bottom: 10px;">
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
        if row['tfiar']:
            html_output += f"""
            <div style="margin-bottom: 8px;">
                <strong style="color: #34495e;">Tfiar:</strong>
                <span style="color: black;">{row['tfiar']}</span>
            </div>
            """
        html_output += "</div>"
    return html_output

def format_msmun_بق_r_results(results):
    """Formats results from msmun_بق.db table_r."""
    if not results:
        return ""

    html_output = ""
    for row in results:
        html_output += f"""
        <div style="background: #e0e0e0; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #757575; padding-bottom: 10px; margin-bottom: 10px;">
                <h3 style="color: #2c3e50; margin: 0;">{row['word'] or ''}</h3>
            </div>
        """
        if row['result']:
            html_output += f"""
            <div style="margin-bottom: 8px;">
                <strong style="color: #34495e;">Amazigh Translation:</strong>
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
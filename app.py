import gradio as gr
import sqlite3
from pathlib import Path
import unicodedata
import re  # Import the regular expression module

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

def search_dictionary(query, search_type):
    if not query or len(query.strip()) < 1:
        return "Please enter a search term"

    normalized_query_general = normalize_general_text(query)
    normalized_query_amazigh = normalize_amazigh_text(query)

    # Determine search terms based on search_type
    if search_type == "contains":
        start_search_term_general = f"%{normalized_query_general}%"
        start_search_term_amazigh = f"%{normalized_query_amazigh}%"
        contain_search_term_general = f"%{normalized_query_general}%"
        contain_search_term_amazigh = f"%{normalized_query_amazigh}%"
        exact_search_term_general = None  # Not used for "contains"
        exact_search_term_amazigh = None   # Not used for "contains"

    elif search_type == "starts_with":
        start_search_term_general = f"{normalized_query_general}%"
        start_search_term_amazigh = f"{normalized_query_amazigh}%"
        contain_search_term_general = f"{normalized_query_general}%"
        contain_search_term_amazigh = f"{normalized_query_amazigh}%"
        exact_search_term_general = None
        exact_search_term_amazigh = None

    elif search_type == "exact_word":
        # Use word boundaries (\b) for exact word matching
        exact_search_term_general = r'\b' + re.escape(normalized_query_general) + r'\b'
        exact_search_term_amazigh = r'\b' + re.escape(normalized_query_amazigh) + r'\b'
        start_search_term_general = None
        start_search_term_amazigh = None
        contain_search_term_general = None
        contain_search_term_amazigh = None

    else:  # Default to contains if invalid search_type
        start_search_term_general = f"%{normalized_query_general}%"
        start_search_term_amazigh = f"%{normalized_query_amazigh}%"
        contain_search_term_general = f"%{normalized_query_general}%"
        contain_search_term_amazigh = f"%{normalized_query_amazigh}%"
        exact_search_term_general = None
        exact_search_term_amazigh = None
        print("Invalid search type.  Defaulting to 'contains'.")



    # --- Search dglai14.db (Prioritized) ---
    dglai14_results = search_dglai14(start_search_term_general, contain_search_term_general, start_search_term_amazigh, contain_search_term_amazigh, exact_search_term_general, exact_search_term_amazigh)

    # --- Search tawalt_fr.db (Secondary) ---
    remaining_results = 50 - len(dglai14_results)
    if remaining_results > 0:
        tawalt_fr_results = search_tawalt_fr(start_search_term_general, contain_search_term_general, start_search_term_amazigh, contain_search_term_amazigh, exact_search_term_general, exact_search_term_amazigh, remaining_results)
        remaining_results -= len(tawalt_fr_results)
    else:
        tawalt_fr_results = []

    # --- Search tawalt.db (Tertiary) ---
    if remaining_results > 0:
        tawalt_results = search_tawalt(start_search_term_general, contain_search_term_general,start_search_term_amazigh, contain_search_term_amazigh, exact_search_term_general, exact_search_term_amazigh, remaining_results)
        remaining_results -= len(tawalt_results)
    else:
        tawalt_results = []  # No need to search tawalt

    # --- Search eng.db (Quaternary) ---
    if remaining_results > 0:
      eng_results = search_eng(start_search_term_general, contain_search_term_general, start_search_term_amazigh, contain_search_term_amazigh, exact_search_term_general, exact_search_term_amazigh, remaining_results)
      remaining_results -= len(eng_results)
    else:
      eng_results = []

    # --- Search msmun_fr.db (Quinary) ---
    if remaining_results > 0:
        msmun_fr_m_results = search_msmun_fr_m(start_search_term_general, contain_search_term_general, start_search_term_amazigh, contain_search_term_amazigh, exact_search_term_general, exact_search_term_amazigh, remaining_results)
        remaining_results -= len(msmun_fr_m_results)
    else:
        msmun_fr_m_results = []

    if remaining_results > 0:
        msmun_fr_r_results = search_msmun_fr_r(start_search_term_general, contain_search_term_general, start_search_term_amazigh, contain_search_term_amazigh, exact_search_term_general, exact_search_term_amazigh, remaining_results)
        remaining_results -= len(msmun_fr_r_results)
    else:
        msmun_fr_r_results = []

    # --- Search msmun_ar.db (Senary) ---
    if remaining_results > 0:
        msmun_ar_m_r_results = search_msmun_ar_m_r(start_search_term_general, contain_search_term_general, start_search_term_amazigh, contain_search_term_amazigh, exact_search_term_general, exact_search_term_amazigh, remaining_results)
        remaining_results -= len(msmun_ar_m_r_results)
    else:
        msmun_ar_m_r_results = []

    if remaining_results > 0:
        msmun_ar_r_m_results = search_msmun_ar_r_m(start_search_term_general, contain_search_term_general, start_search_term_amazigh, contain_search_term_amazigh, exact_search_term_general, exact_search_term_amazigh, remaining_results)
        remaining_results -= len(msmun_ar_r_m_results)
    else:
        msmun_ar_r_m_results = []


    # --- Combine and Format Results ---
    html_output = format_dglai14_results(dglai14_results)  # Format dglai14 results
    html_output += format_tawalt_fr_results(tawalt_fr_results) # Format tawalt_fr results
    html_output += format_tawalt_results(tawalt_results) # Format tawalt results (if any)
    html_output += format_eng_results(eng_results)
    html_output += format_msmun_fr_m_results(msmun_fr_m_results) # Format msmun_fr table_m results
    html_output += format_msmun_fr_r_results(msmun_fr_r_results) # Format msmun_fr table_r results
    html_output += format_msmun_ar_m_r_results(msmun_ar_m_r_results)
    html_output += format_msmun_ar_r_m_results(msmun_ar_r_m_results)


    if not html_output:
        return "No results found"

    return html_output


def search_dglai14(start_search_term_general, contain_search_term_general,start_search_term_amazigh, contain_search_term_amazigh, exact_search_term_general, exact_search_term_amazigh):
    conn = get_db_connection('dglai14.db')
    cursor = conn.cursor()

    # Add the custom SQLite function for Amazigh normalization *inside* the function that uses it
    conn.create_function("NORMALIZE_AMAZIGH", 1, normalize_amazigh_text) # To be removed if the database is selectable

    # Base query
    base_query = """
        SELECT lexie.*, sens.sens_fr, sens.sens_ar,
               expression.exp_amz, expression.exp_fr, expression.exp_ar
        FROM lexie
        LEFT JOIN sens ON lexie.id_lexie = sens.id_lexie
        LEFT JOIN expression ON lexie.id_lexie = expression.id_lexie
        WHERE 1=1
    """
    conditions = []
    params = []

    # --- Handle different search types ---
    if exact_search_term_general:
      conditions.append(" (REMOVE_DIACRITICS(LOWER(cg)) REGEXP ?)")
      conditions.append(" OR (REMOVE_DIACRITICS(LOWER(acc)) REGEXP ?)")
      conditions.append(" OR (REMOVE_DIACRITICS(LOWER(acc_neg)) REGEXP ?)")
      conditions.append(" OR (REMOVE_DIACRITICS(LOWER(inacc)) REGEXP ?)")
      conditions.append(" OR (REMOVE_DIACRITICS(LOWER(fel)) REGEXP ?)")
      conditions.append(" OR (REMOVE_DIACRITICS(LOWER(fea)) REGEXP ?)")
      conditions.append(" OR (REMOVE_diacritics(LOWER(fpel)) REGEXP ?)")
      conditions.append(" OR (REMOVE_DIACRITICS(LOWER(fpea)) REGEXP ?)")
      conditions.append(" OR (REMOVE_DIACRITICS(LOWER(sens_ar)) REGEXP ?)")
      conditions.append(" OR (REMOVE_DIACRITICS(LOWER(expression.exp_ar)) REGEXP ?)")
      params.extend([exact_search_term_general] * 10)

    if exact_search_term_amazigh:
      conditions.append(" (NORMALIZE_AMAZIGH(lexie) REGEXP ?)")  # Use REGEXP for exact word match
      conditions.append(" OR (NORMALIZE_AMAZIGH(remarque) REGEXP ?)")
      conditions.append(" OR (NORMALIZE_AMAZIGH(variante) REGEXP ?)")
      conditions.append(" OR (NORMALIZE_AMAZIGH(eadata) REGEXP ?)")
      conditions.append(" OR (NORMALIZE_AMAZIGH(pldata) REGEXP ?)")
      conditions.append(" OR (NORMALIZE_AMAZIGH(expression.exp_amz) REGEXP ?)")
      params.extend([exact_search_term_amazigh] * 6)

    if start_search_term_general:
        conditions.append(" (REMOVE_DIACRITICS(LOWER(cg)) LIKE ?)")
        conditions.append(" OR (REMOVE_DIACRITICS(LOWER(acc)) LIKE ?)")
        conditions.append(" OR (REMOVE_DIACRITICS(LOWER(acc_neg)) LIKE ?)")
        conditions.append(" OR (REMOVE_DIACRITICS(LOWER(inacc)) LIKE ?)")
        conditions.append(" OR (REMOVE_DIACRITICS(LOWER(fel)) LIKE ?)")
        conditions.append(" OR (REMOVE_DIACRITICS(LOWER(fea)) LIKE ?)")
        conditions.append(" OR (REMOVE_DIACRITICS(LOWER(fpel)) LIKE ?)")
        conditions.append(" OR (REMOVE_DIACRITICS(LOWER(fpea)) LIKE ?)")
        conditions.append(" OR (REMOVE_DIACRITICS(LOWER(sens_ar)) LIKE ?)")
        conditions.append(" OR (REMOVE_DIACRITICS(LOWER(expression.exp_ar)) LIKE ?)")
        params.extend([start_search_term_general] * 10)

    if start_search_term_amazigh:
        conditions.append(" (NORMALIZE_AMAZIGH(lexie) LIKE ?)")
        conditions.append(" OR (NORMALIZE_AMAZIGH(remarque) LIKE ?)")
        conditions.append(" OR (NORMALIZE_AMAZIGH(variante) LIKE ?)")
        conditions.append(" OR (NORMALIZE_AMAZIGH(eadata) LIKE ?)")
        conditions.append(" OR (NORMALIZE_AMAZIGH(pldata) LIKE ?)")
        conditions.append(" OR (NORMALIZE_AMAZIGH(expression.exp_amz) LIKE ?)")  # Use NORMALIZE_AMAZIGH for exp_amz
        params.extend([start_search_term_amazigh] * 6)

    if contain_search_term_general:
        conditions.append(" (REMOVE_DIACRITICS(LOWER(cg)) LIKE ?)")
        conditions.append(" OR (REMOVE_DIACRITICS(LOWER(acc)) LIKE ?)")
        conditions.append(" OR (REMOVE_DIACRITICS(LOWER(acc_neg)) LIKE ?)")
        conditions.append(" OR (REMOVE_DIACRITICS(LOWER(inacc)) LIKE ?)")
        conditions.append(" OR (REMOVE_DIACRITICS(LOWER(fel)) LIKE ?)")
        conditions.append(" OR (REMOVE_DIACRITICS(LOWER(fea)) LIKE ?)")
        conditions.append(" OR (REMOVE_DIACRITICS(LOWER(fpel)) LIKE ?)")
        conditions.append(" OR (REMOVE_DIACRITICS(LOWER(fpea)) LIKE ?)")
        conditions.append(" OR (REMOVE_DIACRITICS(LOWER(sens_ar)) LIKE ?)")
        conditions.append(" OR (REMOVE_DIACRITICS(LOWER(expression.exp_ar)) LIKE ?)")
        params.extend([contain_search_term_general] * 10)

    if contain_search_term_amazigh:
        conditions.append(" (NORMALIZE_AMAZIGH(lexie) LIKE ?)")
        conditions.append(" OR (NORMALIZE_AMAZIGH(remarque) LIKE ?)")
        conditions.append(" OR (NORMALIZE_AMAZIGH(variante) LIKE ?)")
        conditions.append(" OR (NORMALIZE_AMAZIGH(eadata) LIKE ?)")
        conditions.append(" OR (NORMALIZE_AMAZIGH(pldata) LIKE ?)")
        conditions.append(" OR (NORMALIZE_AMAZIGH(expression.exp_amz) LIKE ?)")  # Use NORMALIZE_AMAZIGH for exp_amz
        params.extend([contain_search_term_amazigh] * 6)

    if conditions:
      where_clause = " AND (" + " OR ".join(conditions) + ")"
      final_query = base_query + where_clause + " ORDER BY lexie.id_lexie LIMIT 50"
      cursor.execute(final_query, params)
      results = cursor.fetchall()
    else:
      results = []

    conn.close()
    return results



def search_tawalt_fr(start_search_term_general, contain_search_term_general, start_search_term_amazigh, contain_search_term_amazigh, exact_search_term_general, exact_search_term_amazigh, limit):
    conn = get_db_connection('tawalt_fr.db')
    cursor = conn.cursor()

    # Add the custom SQLite function for Amazigh normalization
    conn.create_function("NORMALIZE_AMAZIGH", 1, normalize_amazigh_text)
    conn.create_function("NORMALIZE_FRENCH", 1, normalize_french_text)

    # Base query
    base_query = """
        SELECT *
        FROM words
        WHERE 1=1
    """
    conditions = []
    params = []

    if exact_search_term_general:
        conditions.append(" (NORMALIZE_FRENCH(french) REGEXP ?)")
        params.append(exact_search_term_general)

    if exact_search_term_amazigh:
        conditions.append(" (NORMALIZE_AMAZIGH(tifinagh) REGEXP ?)")
        params.append(exact_search_term_amazigh)

    if start_search_term_general:
        conditions.append(" (NORMALIZE_FRENCH(french) LIKE ?)")
        params.append(start_search_term_general)

    if start_search_term_amazigh:
        conditions.append(" (NORMALIZE_AMAZIGH(tifinagh) LIKE ?)")
        params.append(start_search_term_amazigh)

    if contain_search_term_general:
        conditions.append(" (NORMALIZE_FRENCH(french) LIKE ?)")
        params.append(contain_search_term_general)

    if contain_search_term_amazigh:
        conditions.append(" (NORMALIZE_AMAZIGH(tifinagh) LIKE ?)")
        params.append(contain_search_term_amazigh)


    if conditions:
        where_clause = " AND (" + " OR ".join(conditions) + ")"
        final_query = base_query + where_clause + " ORDER BY _id LIMIT ?"
        params.append(limit)  # Add the limit parameter
        cursor.execute(final_query, params)
        results = cursor.fetchall()
    else:
        results = []

    conn.close()
    return results



def search_tawalt(start_search_term_general, contain_search_term_general,start_search_term_amazigh, contain_search_term_amazigh, exact_search_term_general, exact_search_term_amazigh, limit):
    conn = get_db_connection('tawalt.db')
    cursor = conn.cursor()

    # Add the custom SQLite function for Amazigh normalization
    conn.create_function("NORMALIZE_AMAZIGH", 1, normalize_amazigh_text)  #To be removed if the database is selectable

    # Base query
    base_query = """
        SELECT *
        FROM words
        WHERE 1=1
    """

    conditions = []
    params = []

    if exact_search_term_general:
        conditions.append(" (REMOVE_DIACRITICS(LOWER(arabic)) REGEXP ?)")
        conditions.append(" OR (REMOVE_DIACRITICS(LOWER(arabic_meaning)) REGEXP ?)")
        conditions.append(" OR (REMOVE_DIACRITICS(LOWER(_arabic)) REGEXP ?)")
        conditions.append(" OR (REMOVE_DIACRITICS(LOWER(_arabic_meaning)) REGEXP ?)")
        params.extend([exact_search_term_general] * 4)

    if exact_search_term_amazigh:
        conditions.append(" (NORMALIZE_AMAZIGH(tifinagh) REGEXP ?)")
        conditions.append(" OR (NORMALIZE_AMAZIGH(tifinagh_in_arabic) REGEXP ?)")
        conditions.append(" OR (NORMALIZE_AMAZIGH(_tifinagh_in_arabic) REGEXP ?)")
        params.extend([exact_search_term_amazigh] * 3)

    if start_search_term_general:
        conditions.append(" (REMOVE_DIACRITICS(LOWER(arabic)) LIKE ?)")
        conditions.append(" OR (REMOVE_DIACRITICS(LOWER(arabic_meaning)) LIKE ?)")
        conditions.append(" OR (REMOVE_DIACRITICS(LOWER(_arabic)) LIKE ?)")  # Corrected: REMOVE_DIACRITICS for arabic columns
        conditions.append(" OR (REMOVE_DIACRITICS(LOWER(_arabic_meaning)) LIKE ?)")
        params.extend([start_search_term_general] * 4)


    if start_search_term_amazigh:
        conditions.append(" (NORMALIZE_AMAZIGH(tifinagh) LIKE ?)")
        conditions.append(" OR (NORMALIZE_AMAZIGH(tifinagh_in_arabic) LIKE ?)")
        conditions.append(" OR (NORMALIZE_AMAZIGH(_tifinagh_in_arabic) LIKE ?)")
        params.extend([start_search_term_amazigh] * 3)


    if contain_search_term_general:
        conditions.append(" (REMOVE_DIACRITICS(LOWER(arabic)) LIKE ?)")
        conditions.append(" OR (REMOVE_DIACRITICS(LOWER(arabic_meaning)) LIKE ?)")
        conditions.append(" OR (REMOVE_DIACRITICS(LOWER(_arabic)) LIKE ?)")  # Corrected: REMOVE_DIACRITICS for arabic columns
        conditions.append(" OR (REMOVE_DIACRITICS(LOWER(_arabic_meaning)) LIKE ?)")
        params.extend([contain_search_term_general] * 4)


    if contain_search_term_amazigh:
        conditions.append(" (NORMALIZE_AMAZIGH(tifinagh) LIKE ?)")
        conditions.append(" OR (NORMALIZE_AMAZIGH(tifinagh_in_arabic) LIKE ?)")
        conditions.append(" OR (NORMALIZE_AMAZIGH(_tifinagh_in_arabic) LIKE ?)")
        params.extend([contain_search_term_amazigh] * 3)


    if conditions:
        where_clause = " AND (" + " OR ".join(conditions) + ")"
        final_query = base_query + where_clause + " ORDER BY _id LIMIT ?"
        params.append(limit)
        cursor.execute(final_query, params)
        results = cursor.fetchall()
    else:
        results = []

    conn.close()
    return results


def search_eng(start_search_term_general, contain_search_term_general, start_search_term_amazigh, contain_search_term_amazigh, exact_search_term_general, exact_search_term_amazigh, limit):
    conn = get_db_connection('eng.db')
    cursor = conn.cursor()
    conn.create_function("NORMALIZE_AMAZIGH", 1, normalize_amazigh_text)

    base_query = """
        SELECT da.*, dea.sens_eng
        FROM Dictionary_Amazigh_full AS da
        LEFT JOIN Dictionary_English_Amazih_links AS dea ON da.id_lexie = dea.id_lexie
        WHERE 1=1
    """
    conditions = []
    params = []

    if exact_search_term_general:
        conditions.append(" (LOWER(da.cg) REGEXP ?)")
        conditions.append(" OR (LOWER(da.acc) REGEXP ?)")
        conditions.append(" OR (LOWER(da.acc_neg) REGEXP ?)")
        conditions.append(" OR (LOWER(da.inacc) REGEXP ?)")
        conditions.append(" OR (LOWER(dea.sens_eng) REGEXP ?)")
        params.extend([exact_search_term_general] * 5)


    if exact_search_term_amazigh:
        conditions.append(" (NORMALIZE_AMAZIGH(da.lexie) REGEXP ?)")
        conditions.append(" OR (NORMALIZE_AMAZIGH(da.remarque) REGEXP ?)")
        conditions.append(" OR (NORMALIZE_AMAZIGH(da.variante) REGEXP ?)")
        conditions.append(" OR (NORMALIZE_AMAZIGH(da.eadata) REGEXP ?)")
        conditions.append(" OR (NORMALIZE_AMAZIGH(da.pldata) REGEXP ?)")
        params.extend([exact_search_term_amazigh] * 5)


    if start_search_term_general:
        conditions.append(" (LOWER(da.cg) LIKE ?)")
        conditions.append(" OR (LOWER(da.acc) LIKE ?)")
        conditions.append(" OR (LOWER(da.acc_neg) LIKE ?)")
        conditions.append(" OR (LOWER(da.inacc) LIKE ?)")
        conditions.append(" OR (LOWER(dea.sens_eng) LIKE ?)")
        params.extend([start_search_term_general] * 5)

    if start_search_term_amazigh:
        conditions.append(" (NORMALIZE_AMAZIGH(da.lexie) LIKE ?)")
        conditions.append(" OR (NORMALIZE_AMAZIGH(da.remarque) LIKE ?)")
        conditions.append(" OR (NORMALIZE_AMAZIGH(da.variante) LIKE ?)")
        conditions.append(" OR (NORMALIZE_AMAZIGH(da.eadata) LIKE ?)")
        conditions.append(" OR (NORMALIZE_AMAZIGH(da.pldata) LIKE ?)")
        params.extend([start_search_term_amazigh] * 5)

    if contain_search_term_general:
        conditions.append(" (LOWER(da.cg) LIKE ?)")
        conditions.append(" OR (LOWER(da.acc) LIKE ?)")
        conditions.append(" OR (LOWER(da.acc_neg) LIKE ?)")
        conditions.append(" OR (LOWER(da.inacc) LIKE ?)")
        conditions.append(" OR (LOWER(dea.sens_eng) LIKE ?)")
        params.extend([contain_search_term_general] * 5)

    if contain_search_term_amazigh:
        conditions.append(" (NORMALIZE_AMAZIGH(da.lexie) LIKE ?)")
        conditions.append(" OR (NORMALIZE_AMAZIGH(da.remarque) LIKE ?)")
        conditions.append(" OR (NORMALIZE_AMAZIGH(da.variante) LIKE ?)")
        conditions.append(" OR (NORMALIZE_AMAZIGH(da.eadata) LIKE ?)")
        conditions.append(" OR (NORMALIZE_AMAZIGH(da.pldata) LIKE ?)")
        params.extend([contain_search_term_amazigh] * 5)

    if conditions:
        where_clause = " AND (" + " OR ".join(conditions) + ")"
        final_query = base_query + where_clause + " ORDER BY da.id_lexie LIMIT ?"
        params.append(limit)
        cursor.execute(final_query, params)
        results = cursor.fetchall()

    else:
        results = []
    conn.close()
    return results

def search_msmun_fr_m(start_search_term_general, contain_search_term_general, start_search_term_amazigh, contain_search_term_amazigh, exact_search_term_general, exact_search_term_amazigh, limit):
    conn = get_db_connection('msmun_fr.db')
    cursor = conn.cursor()
    conn.create_function("NORMALIZE_AMAZIGH", 1, normalize_amazigh_text)
    conn.create_function("NORMALIZE_FRENCH", 1, normalize_french_text)

    base_query = """
        SELECT *
        FROM table_m
        WHERE 1=1
    """

    conditions = []
    params = []

    if exact_search_term_general:
        conditions.append(" (NORMALIZE_FRENCH(result) REGEXP ?)")
        params.append(exact_search_term_general)

    if exact_search_term_amazigh:
        conditions.append(" (NORMALIZE_AMAZIGH(word) REGEXP ?)")
        params.append(exact_search_term_amazigh)

    if start_search_term_general:
       conditions.append(" (NORMALIZE_FRENCH(result) LIKE ?)")
       params.append(start_search_term_general)

    if start_search_term_amazigh:
        conditions.append(" (NORMALIZE_AMAZIGH(word) LIKE ?)")
        params.append(start_search_term_amazigh)

    if contain_search_term_general:
        conditions.append(" (NORMALIZE_FRENCH(result) LIKE ?)")
        params.append(contain_search_term_general)

    if contain_search_term_amazigh:
        conditions.append(" (NORMALIZE_AMAZIGH(word) LIKE ?)")
        params.append(contain_search_term_amazigh)

    if conditions:
        where_clause = " AND (" + " OR ".join(conditions) + ")"
        final_query = base_query + where_clause + " ORDER BY _id LIMIT ?"
        params.append(limit)
        cursor.execute(final_query, params)
        results = cursor.fetchall()
    else:
        results = []

    conn.close()
    return results

def search_msmun_fr_r(start_search_term_general, contain_search_term_general, start_search_term_amazigh, contain_search_term_amazigh, exact_search_term_general, exact_search_term_amazigh, limit):
    conn = get_db_connection('msmun_fr.db')
    cursor = conn.cursor()
    conn.create_function("NORMALIZE_AMAZIGH", 1, normalize_amazigh_text)
    conn.create_function("NORMALIZE_FRENCH", 1, normalize_french_text)

    base_query = """
      SELECT *
      FROM table_r
      WHERE 1=1
    """
    conditions = []
    params = []

    if exact_search_term_general:
        conditions.append(" (NORMALIZE_FRENCH(word) REGEXP ?)")
        params.append(exact_search_term_general)

    if exact_search_term_amazigh:
        conditions.append(" (NORMALIZE_AMAZIGH(result) REGEXP ?)")
        params.append(exact_search_term_amazigh)

    if start_search_term_general:
        conditions.append(" (NORMALIZE_FRENCH(word) LIKE ?)")
        params.append(start_search_term_general)

    if start_search_term_amazigh:
        conditions.append(" (NORMALIZE_AMAZIGH(result) LIKE ?)")
        params.append(start_search_term_amazigh)


    if contain_search_term_general:
        conditions.append(" (NORMALIZE_FRENCH(word) LIKE ?)")
        params.append(contain_search_term_general)

    if contain_search_term_amazigh:
        conditions.append(" (NORMALIZE_AMAZIGH(result) LIKE ?)")
        params.append(contain_search_term_amazigh)

    if conditions:
      where_clause = " AND (" + " OR ".join(conditions) + ")"
      final_query = base_query + where_clause + " ORDER BY _id LIMIT ?"
      params.append(limit)
      cursor.execute(final_query, params)
      results = cursor.fetchall()
    else:
      results = []

    conn.close()
    return results


def search_msmun_ar_m_r(start_search_term_general, contain_search_term_general, start_search_term_amazigh, contain_search_term_amazigh, exact_search_term_general, exact_search_term_amazigh, limit):
    conn = get_db_connection('msmun_ar.db')
    cursor = conn.cursor()
    conn.create_function("NORMALIZE_AMAZIGH", 1, normalize_amazigh_text)

    base_query = """
        SELECT *
        FROM table_m_r
        WHERE 1=1
    """
    conditions = []
    params = []

    if exact_search_term_general:
        conditions.append(" (REMOVE_DIACRITICS(LOWER(result)) REGEXP ?)")
        params.append(exact_search_term_general)

    if exact_search_term_amazigh:
        conditions.append(" (NORMALIZE_AMAZIGH(word) REGEXP ?)")
        params.append(exact_search_term_amazigh)

    if start_search_term_general:
        conditions.append(" (REMOVE_DIACRITICS(LOWER(result)) LIKE ?)")
        params.append(start_search_term_general)

    if start_search_term_amazigh:
        conditions.append(" (NORMALIZE_AMAZIGH(word) LIKE ?)")
        params.append(start_search_term_amazigh)

    if contain_search_term_general:
        conditions.append(" (REMOVE_DIACRITICS(LOWER(result)) LIKE ?)")
        params.append(contain_search_term_general)

    if contain_search_term_amazigh:
        conditions.append(" (NORMALIZE_AMAZIGH(word) LIKE ?)")
        params.append(contain_search_term_amazigh)

    if conditions:
        where_clause = " AND (" + " OR ".join(conditions) + ")"
        final_query = base_query + where_clause + " ORDER BY _id LIMIT ?"
        params.append(limit)
        cursor.execute(final_query, params)
        results = cursor.fetchall()
    else:
        results = []

    conn.close()
    return results

def search_msmun_ar_r_m(start_search_term_general, contain_search_term_general, start_search_term_amazigh, contain_search_term_amazigh, exact_search_term_general, exact_search_term_amazigh, limit):
    conn = get_db_connection('msmun_ar.db')
    cursor = conn.cursor()
    conn.create_function("NORMALIZE_AMAZIGH", 1, normalize_amazigh_text)

    base_query = """
        SELECT *
        FROM table_r_m
        WHERE 1=1
    """
    conditions = []
    params = []

    if exact_search_term_general:
        conditions.append(" (REMOVE_DIACRITICS(LOWER(word)) REGEXP ?)")
        params.append(exact_search_term_general)

    if exact_search_term_amazigh:
        conditions.append(" (NORMALIZE_AMAZIGH(result) REGEXP ?)")
        params.append(exact_search_term_amazigh)

    if start_search_term_general:
        conditions.append(" (REMOVE_DIACRITICS(LOWER(word)) LIKE ?)")
        params.append(start_search_term_general)

    if start_search_term_amazigh:
        conditions.append(" (NORMALIZE_AMAZIGH(result) LIKE ?)")
        params.append(start_search_term_amazigh)

    if contain_search_term_general:
        conditions.append(" (REMOVE_DIACRITICS(LOWER(word)) LIKE ?)")
        params.append(contain_search_term_general)

    if contain_search_term_amazigh:
        conditions.append(" (NORMALIZE_AMAZIGH(result) LIKE ?)")
        params.append(contain_search_term_amazigh)


    if conditions:
        where_clause = " AND (" + " OR ".join(conditions) + ")"
        final_query = base_query + where_clause + " ORDER BY _id LIMIT ?"
        params.append(limit)
        cursor.execute(final_query, params)
        results = cursor.fetchall()
    else:
        results = []

    conn.close()
    return results
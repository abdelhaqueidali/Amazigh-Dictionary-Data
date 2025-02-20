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

def search_dictionary(query, language, search_type):
    if not query or len(query.strip()) < 1:
        return "Please enter a search term"

    if language == "general":
        normalized_query_general = normalize_general_text(query)
        normalized_query_amazigh = normalize_amazigh_text(query)
    elif language == "english":
        normalized_query_general = normalize_general_text(query) # still use general for english search in relevant fields.
        normalized_query_amazigh = normalize_amazigh_text(query) # still use amazigh for amazigh fields.
    elif language == "french":
        normalized_query_general = normalize_general_text(query) # Use general normalization for french relevant fields.
        normalized_query_amazigh = normalize_amazigh_text(query) # Use amazigh normalization for amazigh fields.
    elif language == "arabic":
        normalized_query_general = normalize_general_text(query) # Use general normalization for arabic relevant fields.
        normalized_query_amazigh = normalize_amazigh_text(query) # Use amazigh normalization for amazigh fields.
    elif language == "amazigh":
        normalized_query_general = normalize_general_text(query) # Use general normalization for general fields.
        normalized_query_amazigh = normalize_amazigh_text(query)

    if search_type == "start_with":
        start_search_term_general = f"{normalized_query_general}%"
        contain_search_term_general = f"%{normalized_query_general}%" # Not used in start_with, but kept for function signature.
        start_search_term_amazigh = f"{normalized_query_amazigh}%"
        contain_search_term_amazigh = f"%{normalized_query_amazigh}%" # Not used in start_with, but kept for function signature.
        exact_search_term_general = normalized_query_general # Not used in start_with, but kept for function signature.
        exact_search_term_amazigh = normalized_query_amazigh # Not used in start_with, but kept for function signature.

    elif search_type == "contain":
        start_search_term_general = f"{normalized_query_general}%" # Not used in contain, but kept for function signature.
        contain_search_term_general = f"%{normalized_query_general}%"
        start_search_term_amazigh = f"{normalized_query_amazigh}%" # Not used in contain, but kept for function signature.
        contain_search_term_amazigh = f"%{normalized_query_amazigh}%"
        exact_search_term_general = normalized_query_general # Not used in contain, but kept for function signature.
        exact_search_term_amazigh = normalized_query_amazigh # Not used in contain, but kept for function signature.

    elif search_type == "exact_word":
        start_search_term_general = f"{normalized_query_general}%" # Not used in exact_word, but kept for function signature.
        contain_search_term_general = f"%{normalized_query_general}%" # Not used in exact_word, but kept for function signature.
        start_search_term_amazigh = f"{normalized_query_amazigh}%" # Not used in exact_word, but kept for function signature.
        contain_search_term_amazigh = f"%{normalized_query_amazigh}%" # Not used in exact_word, but kept for function signature.
        exact_search_term_general = normalized_query_general
        exact_search_term_amazigh = normalized_query_amazigh
    else: # Default to contain if search_type is not recognized.
        start_search_term_general = f"{normalized_query_general}%" # Not used in contain, but kept for function signature.
        contain_search_term_general = f"%{normalized_query_general}%"
        start_search_term_amazigh = f"{normalized_query_amazigh}%" # Not used in contain, but kept for function signature.
        contain_search_term_amazigh = f"%{normalized_query_amazigh}%"
        exact_search_term_general = normalized_query_general # Not used in contain, but kept for function signature.
        exact_search_term_amazigh = normalized_query_amazigh # Not used in contain, but kept for function signature.


    dglai14_results = []
    tawalt_fr_results = []
    tawalt_results = []
    eng_results = []
    msmun_fr_m_results = []
    msmun_fr_r_results = []
    msmun_ar_m_r_results = []
    msmun_ar_r_m_results = []

    remaining_results = 50

    if language == "general" or language == "amazigh":
        # --- Search dglai14.db (Prioritized) ---
        dglai14_results = search_dglai14(start_search_term_general, contain_search_term_general,start_search_term_amazigh, contain_search_term_amazigh, exact_search_term_general, exact_search_term_amazigh, search_type)
        remaining_results -= len(dglai14_results)
        if remaining_results < 0: remaining_results = 0

        # --- Search tawalt_fr.db (Secondary) ---
        if remaining_results > 0:
            tawalt_fr_results = search_tawalt_fr(start_search_term_general, contain_search_term_general, start_search_term_amazigh, contain_search_term_amazigh, exact_search_term_general, exact_search_term_amazigh, remaining_results, search_type)
            remaining_results -= len(tawalt_fr_results)
            if remaining_results < 0: remaining_results = 0

        # --- Search tawalt.db (Tertiary) ---
        if remaining_results > 0:
            tawalt_results = search_tawalt(start_search_term_general, contain_search_term_general,start_search_term_amazigh, contain_search_term_amazigh, exact_search_term_general, exact_search_term_amazigh, remaining_results, search_type)
            remaining_results -= len(tawalt_results)
            if remaining_results < 0: remaining_results = 0

        if language == "general" or language == "english":
            # --- Search eng.db (Quaternary) ---
            if remaining_results > 0:
              eng_results = search_eng(start_search_term_general, contain_search_term_general, start_search_term_amazigh, contain_search_term_amazigh, exact_search_term_general, exact_search_term_amazigh, remaining_results, search_type)
              remaining_results -= len(eng_results)
              if remaining_results < 0: remaining_results = 0

        if language == "general" or language == "french":
            # --- Search msmun_fr.db (Quinary) ---
            if remaining_results > 0:
                msmun_fr_m_results = search_msmun_fr_m(start_search_term_general, contain_search_term_general, start_search_term_amazigh, contain_search_term_amazigh, exact_search_term_general, exact_search_term_amazigh, remaining_results, search_type)
                remaining_results -= len(msmun_fr_m_results)
                if remaining_results < 0: remaining_results = 0

            if remaining_results > 0:
                msmun_fr_r_results = search_msmun_fr_r(start_search_term_general, contain_search_term_general, start_search_term_amazigh, contain_search_term_amazigh, exact_search_term_general, exact_search_term_amazigh, remaining_results, search_type)
                remaining_results -= len(msmun_fr_r_results)
                if remaining_results < 0: remaining_results = 0

        if language == "general" or language == "arabic":
            # --- Search msmun_ar.db (Senary) ---
            if remaining_results > 0:
                msmun_ar_m_r_results = search_msmun_ar_m_r(start_search_term_general, contain_search_term_general, start_search_term_amazigh, contain_search_term_amazigh, exact_search_term_general, exact_search_term_amazigh, remaining_results, search_type)
                remaining_results -= len(msmun_ar_m_r_results)
                if remaining_results < 0: remaining_results = 0

            if remaining_results > 0:
                msmun_ar_r_m_results = search_msmun_ar_r_m(start_search_term_general, contain_search_term_general, start_search_term_amazigh, contain_search_term_amazigh, exact_search_term_general, exact_search_term_amazigh, remaining_results, search_type)
                remaining_results -= len(msmun_ar_r_m_results)
                if remaining_results < 0: remaining_results = 0


    # --- Combine and Format Results ---
    html_output = format_dglai14_results(dglai14_results)  # Format dglai14 results
    html_output += format_tawalt_fr_results(tawalt_fr_results) # Format tawalt_fr results
    html_output += format_tawalt_results(tawalt_results) # Format tawalt results (if any)
    if language == "general" or language == "english":
        html_output += format_eng_results(eng_results)
    if language == "general" or language == "french":
        html_output += format_msmun_fr_m_results(msmun_fr_m_results) # Format msmun_fr table_m results
        html_output += format_msmun_fr_r_results(msmun_fr_r_results) # Format msmun_fr table_r results
    if language == "general" or language == "arabic":
        html_output += format_msmun_ar_m_r_results(msmun_ar_m_r_results)
        html_output += format_msmun_ar_r_m_results(msmun_ar_r_m_results)


    if not html_output:
        return "No results found"

    return html_output


def search_dglai14(start_search_term_general, contain_search_term_general,start_search_term_amazigh, contain_search_term_amazigh, exact_search_term_general, exact_search_term_amazigh, search_type):
    conn = get_db_connection('dglai14.db')
    cursor = conn.cursor()

    # Add the custom SQLite function for Amazigh normalization *inside* the function that uses it
    conn.create_function("NORMALIZE_AMAZIGH", 1, normalize_amazigh_text) # To be removed if the database is selectable

    if search_type == "exact_word":
        where_clause = """
        WHERE (
            (NORMALIZE_AMAZIGH(lexie) = ?)
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
            OR (NORMALIZE_AMAZIGH(expression.exp_amz) = ?)
            OR (REMOVE_DIACRITICS(LOWER(expression.exp_ar)) LIKE ?)
        )
        """
        params_start = (exact_search_term_amazigh, f"%{exact_search_term_amazigh}%", f"%{exact_search_term_amazigh}%", f"%{exact_search_term_general}%",
                      f"%{exact_search_term_amazigh}%", f"%{exact_search_term_amazigh}%", f"%{exact_search_term_general}%", f"%{exact_search_term_general}%", f"%{exact_search_term_general}%",
                      f"%{exact_search_term_general}%", f"%{exact_search_term_general}%", f"%{exact_search_term_general}%", f"%{exact_search_term_general}%",
                      f"%{exact_search_term_general}%", exact_search_term_amazigh, f"%{exact_search_term_general}%")
        params_contain = params_start # Exact and contain are same for exact word search in this context.

    elif search_type == "start_with":
        where_clause = """
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
        """
        params_start = (start_search_term_amazigh, start_search_term_amazigh, start_search_term_amazigh, start_search_term_general,
                      start_search_term_amazigh, start_search_term_amazigh, start_search_term_general, start_search_term_general, start_search_term_general,
                      start_search_term_general, start_search_term_general, start_search_term_general, start_search_term_general,
                      start_search_term_general, start_search_term_amazigh, start_search_term_general)
        params_contain = params_start # Not used in start_with, but kept for function signature.

    elif search_type == "contain":
        where_clause = """
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
        """
        params_start = (start_search_term_amazigh, start_search_term_amazigh, start_search_term_amazigh, start_search_term_general,
                      start_search_term_amazigh, start_search_term_amazigh, start_search_term_general, start_search_term_general, start_search_term_general,
                      start_search_term_general, start_search_term_general, start_search_term_general, start_search_term_general,
                      start_search_term_general, start_search_term_amazigh, start_search_term_general) # Not used in contain, but kept for function signature.
        params_contain = (contain_search_term_amazigh, contain_search_term_amazigh, contain_search_term_amazigh, contain_search_term_general,
                          contain_search_term_amazigh, contain_search_term_amazigh, contain_search_term_general, contain_search_term_general, contain_search_term_general,
                          contain_search_term_general, contain_search_term_general, contain_search_term_general, contain_search_term_general,
                          contain_search_term_general, contain_search_term_amazigh, contain_search_term_general,
                          start_search_term_amazigh)  # Use start_search_term_amazigh for the NOT LIKE part

    else: # Default to contain
        where_clause = """
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
        """
        params_start = (start_search_term_amazigh, start_search_term_amazigh, start_search_term_amazigh, start_search_term_general,
                      start_search_term_amazigh, start_search_term_amazigh, start_search_term_general, start_search_term_general, start_search_term_general,
                      start_search_term_general, start_search_term_general, start_search_term_general, start_search_term_general,
                      start_search_term_general, start_search_term_amazigh, start_search_term_general) # Not used in contain, but kept for function signature.
        params_contain = (contain_search_term_amazigh, contain_search_term_amazigh, contain_search_term_amazigh, contain_search_term_general,
                          contain_search_term_amazigh, contain_search_term_amazigh, contain_search_term_general, contain_search_term_general, contain_search_term_general,
                          contain_search_term_general, contain_search_term_general, contain_search_term_general, contain_search_term_general,
                          contain_search_term_general, contain_search_term_amazigh, contain_search_term_general,
                          start_search_term_amazigh)  # Use start_search_term_amazigh for the NOT LIKE part


    # Start Search (dglai14)
    query_start = f"""
        SELECT lexie.*, sens.sens_fr, sens.sens_ar,
               expression.exp_amz, expression.exp_fr, expression.exp_ar
        FROM lexie
        LEFT JOIN sens ON lexie.id_lexie = sens.id_lexie
        LEFT JOIN expression ON lexie.id_lexie = expression.id_lexie
        {where_clause}
        ORDER BY lexie.id_lexie
        LIMIT 50
    """
    cursor.execute(query_start, params_start)
    start_results = cursor.fetchall()

    if search_type == "contain" or search_type == "exact_word" or search_type not in ["start_with", "contain", "exact_word"]: # Avoid contain search for start_with
        # Contain Search (dglai14)
        query_contain = f"""
            SELECT lexie.*, sens.sens_fr, sens.sens_ar,
                   expression.exp_amz, expression.exp_fr, expression.exp_ar
            FROM lexie
            LEFT JOIN sens ON lexie.id_lexie = sens.id_lexie
            LEFT JOIN expression ON lexie.id_lexie = expression.id_lexie
            {where_clause}
            ORDER BY lexie.id_lexie
            LIMIT 50
        """
        cursor.execute(query_contain, params_contain)
        contain_results = cursor.fetchall()
    else:
        contain_results = []

    conn.close()
    return list(start_results) + list(contain_results)

def search_tawalt_fr(start_search_term_general, contain_search_term_general, start_search_term_amazigh, contain_search_term_amazigh, exact_search_term_general, exact_search_term_amazigh, limit, search_type):
    conn = get_db_connection('tawalt_fr.db')
    cursor = conn.cursor()

    # Add the custom SQLite function for Amazigh normalization
    conn.create_function("NORMALIZE_AMAZIGH", 1, normalize_amazigh_text)
    conn.create_function("NORMALIZE_FRENCH", 1, normalize_french_text)

    if search_type == "exact_word":
        where_clause = """
        WHERE (
            (NORMALIZE_AMAZIGH(tifinagh) = ?)
            OR (NORMALIZE_FRENCH(french) LIKE ?)
        )
        """
        params_start = (exact_search_term_amazigh, f"%{exact_search_term_general}%")
        params_contain = params_start # Exact and contain are same for exact word search in this context.

    elif search_type == "start_with":
        where_clause = """
        WHERE
        (NORMALIZE_AMAZIGH(tifinagh) LIKE ?)
        OR (NORMALIZE_FRENCH(french) LIKE ?)
        """
        params_start = (start_search_term_amazigh, start_search_term_general)
        params_contain = params_start # Not used in start_with, but kept for function signature.

    elif search_type == "contain":
        where_clause = """
        WHERE (
        (NORMALIZE_AMAZIGH(tifinagh) LIKE ?)
        OR (NORMALIZE_FRENCH(french) LIKE ?)
        )
        AND NOT (NORMALIZE_AMAZIGH(tifinagh) LIKE ?)
        """
        params_start = (start_search_term_amazigh, start_search_term_general) # Not used in contain, but kept for function signature.
        params_contain = (contain_search_term_amazigh, contain_search_term_general, start_search_term_amazigh)

    else: # Default to contain
        where_clause = """
        WHERE (
        (NORMALIZE_AMAZIGH(tifinagh) LIKE ?)
        OR (NORMALIZE_FRENCH(french) LIKE ?)
        )
        AND NOT (NORMALIZE_AMAZIGH(tifinagh) LIKE ?)
        """
        params_start = (start_search_term_amazigh, start_search_term_general) # Not used in contain, but kept for function signature.
        params_contain = (contain_search_term_amazigh, contain_search_term_general, start_search_term_amazigh)


    # Start Search (tawalt_fr)
    query_start = f"""
        SELECT *
        FROM words
        {where_clause}
        ORDER BY _id
        LIMIT ?
    """
    cursor.execute(query_start, params_start + (limit,))
    start_results = cursor.fetchall()

    if search_type == "contain" or search_type == "exact_word" or search_type not in ["start_with", "contain", "exact_word"]: # Avoid contain search for start_with
        # Contain Search (tawalt_fr)
        query_contain = f"""
            SELECT *
            FROM words
            {where_clause}
            ORDER BY _id
            LIMIT ?
        """
        cursor.execute(query_contain, params_contain + (limit,))
        contain_results = cursor.fetchall()
    else:
        contain_results = []

    conn.close()
    return list(start_results) + list(contain_results)


def search_tawalt(start_search_term_general, contain_search_term_general,start_search_term_amazigh, contain_search_term_amazigh, exact_search_term_general, exact_search_term_amazigh, limit, search_type):
    conn = get_db_connection('tawalt.db')
    cursor = conn.cursor()

    # Add the custom SQLite function for Amazigh normalization
    conn.create_function("NORMALIZE_AMAZIGH", 1, normalize_amazigh_text)  #To be removed if the database is selectable

    if search_type == "exact_word":
        where_clause = """
        WHERE (
            (NORMALIZE_AMAZIGH(tifinagh) = ?) -- Use NORMALIZE_AMAZIGH for tifinagh
            OR (REMOVE_DIACRITICS(LOWER(arabic)) LIKE ?)
            OR (REMOVE_DIACRITICS(LOWER(arabic_meaning)) LIKE ?)
            OR (NORMALIZE_AMAZIGH(tifinagh_in_arabic) = ?) -- Use NORMALIZE_AMAZIGH
            OR (REMOVE_DIACRITICS(LOWER(_arabic)) LIKE ?)  -- Corrected: REMOVE_DIACRITICS for arabic columns
            OR (REMOVE_DIACRITICS(LOWER(_arabic_meaning)) LIKE ?) -- Corrected: REMOVE_DIACRITICS for arabic columns
            OR (NORMALIZE_AMAZIGH(_tifinagh_in_arabic) = ?)
        )
        """
        params_start = (exact_search_term_amazigh, f"%{exact_search_term_general}%", f"%{exact_search_term_general}%", exact_search_term_amazigh,
                      f"%{exact_search_term_general}%", f"%{exact_search_term_general}%", exact_search_term_amazigh)
        params_contain = params_start # Exact and contain are same for exact word search in this context.

    elif search_type == "start_with":
        where_clause = """
        WHERE
        (NORMALIZE_AMAZIGH(tifinagh) LIKE ?) -- Use NORMALIZE_AMAZIGH for tifinagh
        OR (REMOVE_DIACRITICS(LOWER(arabic)) LIKE ?)
        OR (REMOVE_DIACRITICS(LOWER(arabic_meaning)) LIKE ?)
        OR (NORMALIZE_AMAZIGH(tifinagh_in_arabic) LIKE ?) -- Use NORMALIZE_AMAZIGH
        OR (REMOVE_DIACRITICS(LOWER(_arabic)) LIKE ?)  -- Corrected: REMOVE_DIACRITICS for arabic columns
        OR (REMOVE_DIACRITICS(LOWER(_arabic_meaning)) LIKE ?) -- Corrected: REMOVE_DIACRITICS for arabic columns
        OR (NORMALIZE_AMAZIGH(_tifinagh_in_arabic) LIKE ?)
        """
        params_start = (start_search_term_amazigh, start_search_term_general, start_search_term_general, start_search_term_amazigh,
                      start_search_term_general, start_search_term_general, start_search_term_amazigh)
        params_contain = params_start # Not used in start_with, but kept for function signature.

    elif search_type == "contain":
        where_clause = """
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
        """
        params_start = (start_search_term_amazigh, start_search_term_general, start_search_term_general, start_search_term_amazigh,
                      start_search_term_general, start_search_term_general, start_search_term_amazigh) # Not used in contain, but kept for function signature.
        params_contain = (contain_search_term_amazigh, contain_search_term_general, contain_search_term_general, contain_search_term_amazigh,
                          contain_search_term_general, contain_search_term_general, contain_search_term_amazigh,
                          start_search_term_amazigh) # Use start_search_term_amazigh for NOT LIKE

    else: # Default to contain
        where_clause = """
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
        """
        params_start = (start_search_term_amazigh, start_search_term_general, start_search_term_general, start_search_term_amazigh,
                      start_search_term_general, start_search_term_general, start_search_term_amazigh) # Not used in contain, but kept for function signature.
        params_contain = (contain_search_term_amazigh, contain_search_term_general, contain_search_term_general, contain_search_term_amazigh,
                          contain_search_term_general, contain_search_term_general, contain_search_term_amazigh,
                          start_search_term_amazigh) # Use start_search_term_amazigh for NOT LIKE


    # Start Search (tawalt)
    query_start = f"""
        SELECT *
        FROM words
        {where_clause}
        ORDER BY _id
        LIMIT ?
    """
    cursor.execute(query_start, params_start + (limit,))
    start_results = cursor.fetchall()

    if search_type == "contain" or search_type == "exact_word" or search_type not in ["start_with", "contain", "exact_word"]: # Avoid contain search for start_with
        # Contain Search (tawalt)
        query_contain = f"""
            SELECT *
            FROM words
            {where_clause}
            ORDER BY _id
            LIMIT ?
        """
        cursor.execute(query_contain, params_contain + (limit,))
        contain_results = cursor.fetchall()
    else:
        contain_results = []

    conn.close()
    return list(start_results) + list(contain_results)

def search_eng(start_search_term_general, contain_search_term_general, start_search_term_amazigh, contain_search_term_amazigh, exact_search_term_general, exact_search_term_amazigh, limit, search_type):
    conn = get_db_connection('eng.db')
    cursor = conn.cursor()
    conn.create_function("NORMALIZE_AMAZIGH", 1, normalize_amazigh_text)

    if search_type == "exact_word":
        where_clause = """
        WHERE (
            NORMALIZE_AMAZIGH(da.lexie) = ?
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
        """
        params_start = (exact_search_term_amazigh, f"%{exact_search_term_amazigh}%", f"%{exact_search_term_amazigh}%", f"%{exact_search_term_general}%",
                      f"%{exact_search_term_amazigh}%", f"%{exact_search_term_amazigh}%", f"%{exact_search_term_general}%", f"%{exact_search_term_general}%",
                      f"%{exact_search_term_general}%", f"%{exact_search_term_general}%")
        params_contain = params_start # Exact and contain are same for exact word search in this context.

    elif search_type == "start_with":
        where_clause = """
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
        """
        params_start = (start_search_term_amazigh, start_search_term_amazigh, start_search_term_amazigh, start_search_term_general,
                      start_search_term_amazigh, start_search_term_amazigh, start_search_term_general, start_search_term_general,
                      start_search_term_general, start_search_term_general)
        params_contain = params_start # Not used in start_with, but kept for function signature.

    elif search_type == "contain":
        where_clause = """
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
        """
        params_start = (start_search_term_amazigh, start_search_term_amazigh, start_search_term_amazigh, start_search_term_general,
                      start_search_term_amazigh, start_search_term_amazigh, start_search_term_general, start_search_term_general,
                      start_search_term_general, start_search_term_general) # Not used in contain, but kept for function signature.
        params_contain = (contain_search_term_amazigh, contain_search_term_amazigh, contain_search_term_amazigh, contain_search_term_general,
                          contain_search_term_amazigh, contain_search_term_amazigh, contain_search_term_general, contain_search_term_general,
                          contain_search_term_general, contain_search_term_general, start_search_term_amazigh)

    else: # Default to contain
        where_clause = """
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
        """
        params_start = (start_search_term_amazigh, start_search_term_amazigh, start_search_term_amazigh, start_search_term_general,
                      start_search_term_amazigh, start_search_term_amazigh, start_search_term_general, start_search_term_general,
                      start_search_term_general, start_search_term_general) # Not used in contain, but kept for function signature.
        params_contain = (contain_search_term_amazigh, contain_search_term_amazigh, contain_search_term_amazigh, contain_search_term_general,
                          contain_search_term_amazigh, contain_search_term_amazigh, contain_search_term_general, contain_search_term_general,
                          contain_search_term_general, contain_search_term_general, start_search_term_amazigh)


    query_start = f"""
        SELECT da.*, dea.sens_eng
        FROM Dictionary_Amazigh_full AS da
        LEFT JOIN Dictionary_English_Amazih_links AS dea ON da.id_lexie = dea.id_lexie
        {where_clause}
        ORDER BY da.id_lexie
        LIMIT ?
    """

    cursor.execute(query_start, params_start + (limit,))
    start_results = cursor.fetchall()

    if search_type == "contain" or search_type == "exact_word" or search_type not in ["start_with", "contain", "exact_word"]: # Avoid contain search for start_with
        query_contain = f"""
          SELECT da.*, dea.sens_eng
            FROM Dictionary_Amazigh_full AS da
            LEFT JOIN Dictionary_English_Amazih_links AS dea ON da.id_lexie = dea.id_lexie
            {where_clause}
            AND NOT NORMALIZE_AMAZIGH(da.lexie) LIKE ?
            ORDER BY da.id_lexie
            LIMIT ?
        """
        cursor.execute(query_contain, params_contain + (limit,))
        contain_results = cursor.fetchall()
    else:
        contain_results = []
    conn.close()

    return list(start_results) + list(contain_results)

def search_msmun_fr_m(start_search_term_general, contain_search_term_general, start_search_term_amazigh, contain_search_term_amazigh, exact_search_term_general, exact_search_term_amazigh, limit, search_type):
    conn = get_db_connection('msmun_fr.db')
    cursor = conn.cursor()
    conn.create_function("NORMALIZE_AMAZIGH", 1, normalize_amazigh_text)
    conn.create_function("NORMALIZE_FRENCH", 1, normalize_french_text)

    if search_type == "exact_word":
        where_clause = """
        WHERE (
            NORMALIZE_AMAZIGH(word) = ?
            OR NORMALIZE_FRENCH(result) LIKE ?
        )
        """
        params_start = (exact_search_term_amazigh, f"%{exact_search_term_general}%")
        params_contain = params_start # Exact and contain are same for exact word search in this context.

    elif search_type == "start_with":
        where_clause = """
        WHERE (
            NORMALIZE_AMAZIGH(word) LIKE ?
            OR NORMALIZE_FRENCH(result) LIKE ?
        )
        """
        params_start = (start_search_term_amazigh, start_search_term_general)
        params_contain = params_start # Not used in start_with, but kept for function signature.

    elif search_type == "contain":
        where_clause = """
        WHERE (
            NORMALIZE_AMAZIGH(word) LIKE ?
            OR NORMALIZE_FRENCH(result) LIKE ?
        )
        AND NOT NORMALIZE_AMAZIGH(word) LIKE ?
        """
        params_start = (start_search_term_amazigh, start_search_term_general) # Not used in contain, but kept for function signature.
        params_contain = (contain_search_term_amazigh, contain_search_term_general, start_search_term_amazigh)

    else: # Default to contain
        where_clause = """
        WHERE (
            NORMALIZE_AMAZIGH(word) LIKE ?
            OR NORMALIZE_FRENCH(result) LIKE ?
        )
        AND NOT NORMALIZE_AMAZIGH(word) LIKE ?
        """
        params_start = (start_search_term_amazigh, start_search_term_general) # Not used in contain, but kept for function signature.
        params_contain = (contain_search_term_amazigh, contain_search_term_general, start_search_term_amazigh)


    query_start = f"""
        SELECT *
        FROM table_m
        {where_clause}
        ORDER BY _id
        LIMIT ?
    """
    cursor.execute(query_start, params_start + (limit,))
    start_results = cursor.fetchall()

    if search_type == "contain" or search_type == "exact_word" or search_type not in ["start_with", "contain", "exact_word"]: # Avoid contain search for start_with
        query_contain = f"""
            SELECT *
            FROM table_m
            {where_clause}
            AND NOT NORMALIZE_AMAZIGH(word) LIKE ?
            ORDER BY _id
            LIMIT ?
        """
        cursor.execute(query_contain, params_contain + (limit,))
        contain_results = cursor.fetchall()
    else:
        contain_results = []
    conn.close()
    return list(start_results) + list(contain_results)

def search_msmun_fr_r(start_search_term_general, contain_search_term_general, start_search_term_amazigh, contain_search_term_amazigh, exact_search_term_general, exact_search_term_amazigh, limit, search_type):
    conn = get_db_connection('msmun_fr.db')
    cursor = conn.cursor()
    conn.create_function("NORMALIZE_AMAZIGH", 1, normalize_amazigh_text)
    conn.create_function("NORMALIZE_FRENCH", 1, normalize_french_text)

    if search_type == "exact_word":
        where_clause = """
        WHERE (
            NORMALIZE_FRENCH(word) LIKE ?
            OR NORMALIZE_AMAZIGH(result) = ?
        )
        """
        params_start = (f"%{exact_search_term_general}%", exact_search_term_amazigh)
        params_contain = params_start # Exact and contain are same for exact word search in this context.

    elif search_type == "start_with":
        where_clause = """
        WHERE (
            NORMALIZE_FRENCH(word) LIKE ?
            OR NORMALIZE_AMAZIGH(result) LIKE ?
        )
        """
        params_start = (start_search_term_general, start_search_term_amazigh)
        params_contain = params_start # Not used in start_with, but kept for function signature.

    elif search_type == "contain":
        where_clause = """
        WHERE (
            NORMALIZE_FRENCH(word) LIKE ?
            OR NORMALIZE_AMAZIGH(result) LIKE ?
        )
        AND NOT NORMALIZE_FRENCH(word) LIKE ?
        """
        params_start = (start_search_term_general, start_search_term_amazigh) # Not used in contain, but kept for function signature.
        params_contain = (contain_search_term_general, contain_search_term_amazigh, start_search_term_general)

    else: # Default to contain
        where_clause = """
        WHERE (
            NORMALIZE_FRENCH(word) LIKE ?
            OR NORMALIZE_AMAZIGH(result) LIKE ?
        )
        AND NOT NORMALIZE_FRENCH(word) LIKE ?
        """
        params_start = (start_search_term_general, start_search_term_amazigh) # Not used in contain, but kept for function signature.
        params_contain = (contain_search_term_general, contain_search_term_amazigh, start_search_term_general)


    query_start = f"""
        SELECT *
        FROM table_r
        {where_clause}
        ORDER BY _id
        LIMIT ?
    """
    cursor.execute(query_start, params_start + (limit,))
    start_results = cursor.fetchall()

    if search_type == "contain" or search_type == "exact_word" or search_type not in ["start_with", "contain", "exact_word"]: # Avoid contain search for start_with
        query_contain = f"""
            SELECT *
            FROM table_r
            {where_clause}
            AND NOT NORMALIZE_FRENCH(word) LIKE ?
            ORDER BY _id
            LIMIT ?
        """
        cursor.execute(query_contain, params_contain + (limit,))
        contain_results = cursor.fetchall()
    else:
        contain_results = []
    conn.close()
    return list(start_results) + list(contain_results)


def search_msmun_ar_m_r(start_search_term_general, contain_search_term_general, start_search_term_amazigh, contain_search_term_amazigh, exact_search_term_general, exact_search_term_amazigh, limit, search_type):
    conn = get_db_connection('msmun_ar.db')
    cursor = conn.cursor()
    conn.create_function("NORMALIZE_AMAZIGH", 1, normalize_amazigh_text)

    if search_type == "exact_word":
        where_clause = """
        WHERE (
            NORMALIZE_AMAZIGH(word) = ?
            OR REMOVE_DIACRITICS(LOWER(result)) LIKE ?
        )
        """
        params_start = (exact_search_term_amazigh, f"%{exact_search_term_general}%")
        params_contain = params_start # Exact and contain are same for exact word search in this context.

    elif search_type == "start_with":
        where_clause = """
        WHERE (
            NORMALIZE_AMAZIGH(word) LIKE ?
            OR REMOVE_DIACRITICS(LOWER(result)) LIKE ?
        )
        """
        params_start = (start_search_term_amazigh, start_search_term_general)
        params_contain = params_start # Not used in start_with, but kept for function signature.

    elif search_type == "contain":
        where_clause = """
        WHERE (
            NORMALIZE_AMAZIGH(word) LIKE ?
            OR REMOVE_DIACRITICS(LOWER(result)) LIKE ?
        )
        AND NOT NORMALIZE_AMAZIGH(word) LIKE ?
        """
        params_start = (start_search_term_amazigh, start_search_term_general) # Not used in contain, but kept for function signature.
        params_contain = (contain_search_term_amazigh, contain_search_term_general, start_search_term_amazigh)

    else: # Default to contain
        where_clause = """
        WHERE (
            NORMALIZE_AMAZIGH(word) LIKE ?
            OR REMOVE_DIACRITICS(LOWER(result)) LIKE ?
        )
        AND NOT NORMALIZE_AMAZIGH(word) LIKE ?
        """
        params_start = (start_search_term_amazigh, start_search_term_general) # Not used in contain, but kept for function signature.
        params_contain = (contain_search_term_amazigh, contain_search_term_general, start_search_term_amazigh)


    query_start = f"""
        SELECT *
        FROM table_m_r
        {where_clause}
        ORDER BY _id
        LIMIT ?
    """
    cursor.execute(query_start, params_start + (limit,))
    start_results = cursor.fetchall()

    if search_type == "contain" or search_type == "exact_word" or search_type not in ["start_with", "contain", "exact_word"]: # Avoid contain search for start_with
        query_contain = f"""
            SELECT *
            FROM table_m_r
            {where_clause}
            AND NOT NORMALIZE_AMAZIGH(word) LIKE ?
            ORDER BY _id
            LIMIT ?
        """
        cursor.execute(query_contain, params_contain + (limit,))
        contain_results = cursor.fetchall()
    else:
        contain_results = []
    conn.close()
    return list(start_results) + list(contain_results)

def search_msmun_ar_r_m(start_search_term_general, contain_search_term_general, start_search_term_amazigh, contain_search_term_amazigh, exact_search_term_general, exact_search_term_amazigh, limit, search_type):
    conn = get_db_connection('msmun_ar.db')
    cursor = conn.cursor()
    conn.create_function("NORMALIZE_AMAZIGH", 1, normalize_amazigh_text)

    if search_type == "exact_word":
        where_clause = """
        WHERE (
            REMOVE_DIACRITICS(LOWER(word)) LIKE ?
            OR NORMALIZE_AMAZIGH(result) = ?
        )
        """
        params_start = (f"%{exact_search_term_general}%", exact_search_term_amazigh)
        params_contain = params_start # Exact and contain are same for exact word search in this context.

    elif search_type == "start_with":
        where_clause = """
        WHERE (
            REMOVE_DIACRITICS(LOWER(word)) LIKE ?
            OR NORMALIZE_AMAZIGH(result) LIKE ?
        )
        """
        params_start = (start_search_term_general, start_search_term_amazigh)
        params_contain = params_start # Not used in start_with, but kept for function signature.

    elif search_type == "contain":
        where_clause = """
        WHERE (
            REMOVE_DIACRITICS(LOWER(word)) LIKE ?
            OR NORMALIZE_AMAZIGH(result) LIKE ?
        )
        AND NOT REMOVE_DIACRITICS(LOWER(word)) LIKE ?
        """
        params_start = (start_search_term_general, start_search_term_amazigh) # Not used in contain, but kept for function signature.
        params_contain = (contain_search_term_general, start_search_term_amazigh, start_search_term_general)

    else: # Default to contain
        where_clause = """
        WHERE (
            REMOVE_DIACRITICS(LOWER(word)) LIKE ?
            OR NORMALIZE_AMAZIGH(result) LIKE ?
        )
        AND NOT REMOVE_DIACRITICS(LOWER(word)) LIKE ?
        """
        params_start = (start_search_term_general, start_search_term_amazigh) # Not used in contain, but kept for function signature.
        params_contain = (contain_search_term_general, start_search_term_amazigh, start_search_term_general)


    query_start = f"""
        SELECT *
        FROM table_r_m
        {where_clause}
        ORDER BY _id
        LIMIT ?
    """
    cursor.execute(query_start, params_start + (limit,))
    start_results = cursor.fetchall()

    if search_type == "contain" or search_type == "exact_word" or search_type not in ["start_with", "contain", "exact_word"]: # Avoid contain search for start_with
        query_contain = f"""
            SELECT *
            FROM table_r_m
            {where_clause}
            AND NOT REMOVE_DIACRITICS(LOWER(word)) LIKE ?
            ORDER BY _id
            LIMIT ?
        """
        cursor.execute(query_contain, params_contain + (limit,))
        contain_results = cursor.fetchall()
    else:
        contain_results = []
    conn.close()
    return list(start_results) + list(contain_results)


def format_dglai14_results(results):
    return _format_results(results, "dglai14", '#f0f8ff', '#3498db')

def format_tawalt_fr_results(results):
    return _format_results(results, "tawalt_fr", '#ffe0b2', '#ff9800', word_key='tifinagh', translation_key='french', translation_label='French')

def format_tawalt_results(results):
    return _format_results(results, "tawalt", '#fffacd', '#3498db', word_key='tifinagh', translation_key='arabic', translation_label='Arabic', meaning_key='arabic_meaning', meaning_label='Arabic Meaning')

def format_eng_results(results):
    return _format_results(results, "eng", '#d3f8d3', '#2ecc71', word_key='lexie', translation_key='sens_eng', translation_label='English', cg_key='cg')

def format_msmun_fr_m_results(results):
    return _format_results(results, "msmun_fr_m", '#fce4ec', '#f06292', word_key='word', translation_key='result', translation_label='French', edited=True, favorites=True)

def format_msmun_fr_r_results(results):
    return _format_results(results, "msmun_fr_r", '#f3e5f5', '#ab47bc', word_key='result', translation_key='word', translation_label='Arabic', edited=True, favorites=True)

def format_msmun_ar_m_r_results(results):
    return _format_results(results, "msmun_ar_m_r", '#e0f7fa', '#00bcd4', word_key='word', translation_key='result', translation_label='Arabic', edited=True, favorites=True)

def format_msmun_ar_r_m_results(results):
    return _format_results(results, "msmun_ar_r_m", '#e8f5e9', '#4caf50', word_key='result', translation_key='word', translation_label='Arabic', edited=True, favorites=True)


def _format_results(results, db_name, bg_color, border_color, word_key='lexie', translation_key='sens_frs', translation_label='French Translation', meaning_key=None, meaning_label=None, cg_key='cg', edited=False, favorites=False):
    """Formats results from various databases."""
    if not results:
        return ""

    html_output = ""
    if db_name == "dglai14" or db_name == "eng":
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
                    'sens_eng': set(),
                    'expressions': {}
                }
            if db_name == "dglai14":
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
            elif db_name == "eng":
                 if row['sens_eng']:
                    aggregated_results[lexie_id]['sens_eng'].add(row['sens_eng'])


        for lexie_id, data in aggregated_results.items():
            html_output += f"""
            <div style="background: {bg_color}; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid {border_color}; padding-bottom: 10px; margin-bottom: 10px;">
                    <h3 style="color: #2c3e50; margin: 0;">{data[word_key] or ''}</h3>
                    <span style="background: {border_color}; color: white; padding: 4px 8px; border-radius: 4px;">{data[cg_key] or ''}</span>
                </div>
            """

            if db_name == "dglai14":
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
            elif db_name == "eng":
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

            if db_name == "dglai14":
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

            elif db_name == "eng":
                english_translations = ", ".join(filter(None, data['sens_eng']))
                if english_translations:
                     html_output += f"""
                     <div style="margin-bottom: 8px;">
                        <strong style="color: #34495e;">English Translation:</strong>
                        <span style="color: black;">{english_translations}</span>
                     </div>
                     """

            html_output += "</div>"

    else: # For tawalt_fr, tawalt, msmun_fr_m, msmun_fr_r, msmun_ar_m_r, msmun_ar_r_m
        for row in results:
            html_output += f"""
            <div style="background: {bg_color}; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid {border_color}; padding-bottom: 10px; margin-bottom: 10px;">
                    <h3 style="color: #2c3e50; margin: 0;">{row[word_key] or ''}</h3>
                </div>
            """
            if row[translation_key]:
                html_output += f"""
                <div style="margin-bottom: 8px;">
                    <strong style="color: #34495e;">{translation_label}:</strong>
                    <span style="color: black;">{row[translation_key]}</span>
                </div>
                """
            if meaning_key and row[meaning_key]:
                html_output += f"""
                <div style="margin-bottom: 8px;">
                    <strong style="color: #34495e;">{meaning_label}:</strong>
                    <span style="color: black;">{row[meaning_key]}</span>
                </div>
                """
            if edited and row['edited'] and row['edited'].lower() == 'true':
                html_output += f"""
                <div style="margin-bottom: 8px;">
                    <strong style="color: #34495e;">Edited:</strong>
                    <span style="color: black;">Yes</span>
                </div>
                """
            if favorites and row['favorites'] and row['favorites'].lower() == 'true':
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
            label="Search Term",
            placeholder="Enter a word to search...",
            lines=1
        )
        language_select = gr.Radio(
            ["general", "english", "french", "arabic", "amazigh"],
            label="Language",
            value="general"
        )
        search_type_select = gr.Radio(
            ["contain", "start_with", "exact_word"],
            label="Search Type",
            value="contain"
        )

    output_html = gr.HTML()

    input_text.change(
        fn=search_dictionary,
        inputs=[input_text, language_select, search_type_select],
        outputs=output_html,
        api_name="search"
    )
    language_select.change(
        fn=search_dictionary,
        inputs=[input_text, language_select, search_type_select],
        outputs=output_html,
    )
    search_type_select.change(
        fn=search_dictionary,
        inputs=[input_text, language_select, search_type_select],
        outputs=output_html,
    )


if __name__ == "__main__":
    iface.launch()
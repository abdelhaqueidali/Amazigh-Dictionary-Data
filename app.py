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

def search_dictionary(query, language, exact_match):
    print(f"Searching for: '{query}', Language: '{language}', Exact Match: {exact_match}") # Debug print
    if not query or len(query.strip()) < 1:
        return "Please enter a search term"

    if language == "General":
        normalized_query = normalize_general_text(query)

    elif language == "Amazigh":
        normalized_query = normalize_amazigh_text(query)

    elif language == "French":
        normalized_query = normalize_french_text(query)

    elif language == "Arabic":
        normalized_query = normalize_arabic_text(query)

    else: # Default to General if language is not selected or something goes wrong
        normalized_query = normalize_general_text(query)

    search_term_exact = normalized_query if exact_match else f"{normalized_query}" # For exact match in all cases
    search_term_contain = normalized_query if exact_match else f"%{normalized_query}%" # For contain match in all cases


    if language == "General":
        dglai14_results = search_dglai14(search_term_exact, search_term_contain, exact_match)
        remaining_results = 50 - len(dglai14_results)

        tawalt_fr_results = search_tawalt_fr(search_term_exact, search_term_contain, remaining_results, exact_match)
        remaining_results -= len(tawalt_fr_results)

        tawalt_results = search_tawalt(search_term_exact, search_term_contain, remaining_results, exact_match)
        remaining_results -= len(tawalt_results)

        eng_results = search_eng(search_term_exact, search_term_contain, remaining_results, exact_match)
        remaining_results -= len(eng_results)

        msmun_fr_m_results = search_msmun_fr_m(search_term_exact, search_term_contain, remaining_results, exact_match)
        remaining_results -= len(msmun_fr_m_results)

        msmun_fr_r_results = search_msmun_fr_r(search_term_exact, search_term_contain, remaining_results, exact_match)
        remaining_results -= len(msmun_fr_r_results)

        msmun_ar_m_r_results = search_msmun_ar_m_r(search_term_exact, search_term_contain, remaining_results, exact_match)
        remaining_results -= len(msmun_ar_m_r_results)

        msmun_ar_r_m_results = search_msmun_ar_r_m(search_term_exact, search_term_contain, remaining_results, exact_match)
        remaining_results -= len(msmun_ar_r_m_results)


    elif language == "Amazigh":
        dglai14_results = search_dglai14(search_term_exact, search_term_contain, exact_match, amazigh_only=True)
        remaining_results = 50 - len(dglai14_results)
        tawalt_fr_results = search_tawalt_fr(search_term_exact, search_term_contain, remaining_results, exact_match, amazigh_only=True)
        remaining_results -= len(tawalt_fr_results)
        tawalt_results = search_tawalt(search_term_exact, search_term_contain, remaining_results, exact_match, amazigh_only=True)
        remaining_results -= len(tawalt_results)
        eng_results = search_eng(search_term_exact, search_term_contain, remaining_results, exact_match, amazigh_only=True)
        remaining_results -= len(eng_results)
        msmun_fr_m_results = search_msmun_fr_m(search_term_exact, search_term_contain, remaining_results, exact_match, amazigh_only=True)
        remaining_results -= len(msmun_fr_m_results)
        msmun_fr_r_results = search_msmun_fr_r(search_term_exact, search_term_contain, remaining_results, exact_match, amazigh_only=True)
        remaining_results -= len(msmun_fr_r_results)
        msmun_ar_m_r_results = search_msmun_ar_m_r(search_term_exact, search_term_contain, remaining_results, exact_match, amazigh_only=True)
        remaining_results -= len(msmun_ar_m_r_results)
        msmun_ar_r_m_results = search_msmun_ar_r_m(search_term_exact, search_term_contain, remaining_results, exact_match, amazigh_only=True)
        remaining_results -= len(msmun_ar_r_m_results)


    elif language == "French":
        tawalt_fr_results = search_tawalt_fr(search_term_exact, search_term_contain, 50, exact_match, french_only=True) # French only search
        remaining_results = 50 - len(tawalt_fr_results)
        dglai14_results = search_dglai14(search_term_exact, search_term_contain, exact_match, french_only=True)
        tawalt_results = search_tawalt(search_term_exact, search_term_contain, remaining_results, exact_match, french_only=True)
        eng_results = search_eng(search_term_exact, search_term_contain, remaining_results, exact_match, french_only=True)
        msmun_fr_m_results = search_msmun_fr_m(search_term_exact, search_term_contain, remaining_results, exact_match, french_only=True)
        remaining_results -= len(msmun_fr_m_results)
        msmun_fr_r_results = search_msmun_fr_r(search_term_exact, search_term_contain, remaining_results, exact_match, french_only=True)
        remaining_results -= len(msmun_fr_r_results)
        msmun_ar_m_r_results = search_msmun_ar_m_r(search_term_exact, search_term_contain, remaining_results, exact_match, french_only=True)
        remaining_results -= len(msmun_ar_m_r_results)
        msmun_ar_r_m_results = search_msmun_ar_r_m(search_term_exact, search_term_contain, remaining_results, exact_match, french_only=True)
        remaining_results -= len(msmun_ar_r_m_results)


    elif language == "Arabic":
        tawalt_results = search_tawalt(search_term_exact, search_term_contain, 50, exact_match, arabic_only=True) # Arabic only search in tawalt
        remaining_results = 50 - len(tawalt_results)
        dglai14_results = search_dglai14(search_term_exact, search_term_contain, exact_match, arabic_only=True)
        tawalt_fr_results = search_tawalt_fr(search_term_exact, search_term_contain, remaining_results, exact_match, arabic_only=True)
        eng_results = search_eng(search_term_exact, search_term_contain, remaining_results, exact_match, arabic_only=True)
        msmun_ar_m_r_results = search_msmun_ar_m_r(search_term_exact, search_term_contain, remaining_results, exact_match, arabic_only=True)
        remaining_results -= len(msmun_ar_m_r_results)
        msmun_ar_r_m_results = search_msmun_ar_r_m(search_term_exact, search_term_contain, remaining_results, exact_match, arabic_only=True)
        remaining_results -= len(msmun_ar_r_m_results)
        msmun_fr_m_results = search_msmun_fr_m(search_term_exact, search_term_contain, remaining_results, exact_match, arabic_only=True)
        remaining_results -= len(msmun_fr_m_results)
        msmun_fr_r_results = search_msmun_fr_r(search_term_exact, search_term_contain, remaining_results, exact_match, arabic_only=True)
        remaining_results -= len(msmun_fr_r_results)


    else: # Default to General if language is not selected or something goes wrong
        dglai14_results = search_dglai14(search_term_exact, search_term_contain, exact_match)
        remaining_results = 50 - len(dglai14_results)

        tawalt_fr_results = search_tawalt_fr(search_term_exact, search_term_contain, remaining_results, exact_match)
        remaining_results -= len(tawalt_fr_results)

        tawalt_results = search_tawalt(search_term_exact, search_term_contain, remaining_results, exact_match)
        remaining_results -= len(tawalt_results)

        eng_results = search_eng(search_term_exact, search_term_contain, remaining_results, exact_match)
        remaining_results -= len(eng_results)

        msmun_fr_m_results = search_msmun_fr_m(search_term_exact, search_term_contain, remaining_results, exact_match)
        remaining_results -= len(msmun_fr_m_results)

        msmun_fr_r_results = search_msmun_fr_r(search_term_exact, search_term_contain, remaining_results, exact_match)
        remaining_results -= len(msmun_fr_r_results)

        msmun_ar_m_r_results = search_msmun_ar_m_r(search_term_exact, search_term_contain, remaining_results, exact_match)
        remaining_results -= len(msmun_ar_m_r_results)

        msmun_ar_r_m_results = search_msmun_ar_r_m(search_term_exact, search_term_contain, remaining_results, exact_match)
        remaining_results -= len(msmun_ar_r_m_results)


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


def search_dglai14(search_term_exact, search_term_contain, exact_match, amazigh_only=False, french_only=False, arabic_only=False):
    conn = get_db_connection('dglai14.db')
    cursor = conn.cursor()

    # Add the custom SQLite function for Amazigh normalization *inside* the function that uses it
    conn.create_function("NORMALIZE_AMAZIGH", 1, normalize_amazigh_text) # To be removed if the database is selectable
    conn.create_function("NORMALIZE_FRENCH", 1, normalize_french_text)

    like_op_exact = "=" if exact_match else "LIKE"
    like_op_contain = "=" if exact_match else "LIKE"

    print(f"  dglai14 - Exact Search Term: '{search_term_exact}', Contain: '{search_term_contain}', Exact: {exact_match}, Amazigh Only: {amazigh_only}, French Only: {french_only}, Arabic Only: {arabic_only}") # Debug print

    query_clauses = []
    params_exact = []
    params_contain = []

    if not french_only and not arabic_only: # Default or Amazigh/General search
        query_clauses.extend([
            f"(NORMALIZE_AMAZIGH(lexie) {like_op_exact} ?)",
            f"(NORMALIZE_AMAZIGH(remarque) {like_op_exact} ?)",
            f"(NORMALIZE_AMAZIGH(variante) {like_op_exact} ?)",
            f"(NORMALIZE_AMAZIGH(eadata) {like_op_exact} ?)",
            f"(NORMALIZE_AMAZIGH(pldata) {like_op_exact} ?)",
            f"(NORMALIZE_AMAZIGH(expression.exp_amz) {like_op_exact} ?)",

            f"(NORMALIZE_AMAZIGH(lexie) {like_op_contain} ?)",
            f"(NORMALIZE_AMAZIGH(remarque) {like_op_contain} ?)",
            f"(NORMALIZE_AMAZIGH(variante) {like_op_contain} ?)",
            f"(NORMALIZE_AMAZIGH(eadata) {like_op_contain} ?)",
            f"(NORMALIZE_AMAZIGH(pldata) {like_op_contain} ?)",
            f"(NORMALIZE_AMAZIGH(expression.exp_amz) {like_op_contain} ?)",
        ])
        params_exact.extend([search_term_exact] * 6)
        params_contain.extend([search_term_contain] * 6)


    if not amazigh_only: # Default or General/French/Arabic search
        query_clauses.extend([
            f"(REMOVE_DIACRITICS(LOWER(cg)) {like_op_exact} ?)",
            f"(REMOVE_DIACRITICS(LOWER(acc)) {like_op_exact} ?)",
            f"(REMOVE_DIACRITICS(LOWER(acc_neg)) {like_op_exact} ?)",
            f"(REMOVE_DIACRITICS(LOWER(inacc)) {like_op_exact} ?)",
            f"(REMOVE_DIACRITICS(LOWER(fel)) {like_op_exact} ?)",
            f"(REMOVE_DIACRITICS(LOWER(fea)) {like_op_exact} ?)",
            f"(REMOVE_DIACRITICS(LOWER(fpel)) {like_op_exact} ?)",
            f"(REMOVE_DIACRITICS(LOWER(fpea)) {like_op_exact} ?)",
            f"(REMOVE_DIACRITICS(LOWER(sens_ar)) {like_op_exact} ?)",
            f"(REMOVE_DIACRITICS(LOWER(expression.exp_ar)) {like_op_exact} ?)",

            f"(REMOVE_DIACRITICS(LOWER(cg)) {like_op_contain} ?)",
            f"(REMOVE_DIACRITICS(LOWER(acc)) {like_op_contain} ?)",
            f"(REMOVE_DIACRITICS(LOWER(acc_neg)) {like_op_contain} ?)",
            f"(REMOVE_DIACRITICS(LOWER(inacc)) {like_op_contain} ?)",
            f"(REMOVE_DIACRITICS(LOWER(fel)) {like_op_contain} ?)",
            f"(REMOVE_DIACRITICS(LOWER(fea)) {like_op_contain} ?)",
            f"(REMOVE_DIACRITICS(LOWER(fpel)) {like_op_contain} ?)",
            f"(REMOVE_DIACRITICS(LOWER(fpea)) {like_op_contain} ?)",
            f"(REMOVE_DIACRITICS(LOWER(sens_ar)) {like_op_contain} ?)",
            f"(REMOVE_DIACRITICS(LOWER(expression.exp_ar)) {like_op_contain} ?)",
        ])
        params_exact.extend([search_term_exact] * 10)
        params_contain.extend([search_term_contain] * 10)


    exact_query_where = " OR ".join(query_clauses[::2]) # Even indices for exact
    contain_query_where = " OR ".join(query_clauses[1::2]) # Odd indices for contain


    # Start Search (dglai14)
    cursor.execute(f"""
        SELECT lexie.*, sens.sens_fr, sens.sens_ar,
               expression.exp_amz, expression.exp_fr, expression.exp_ar
        FROM lexie
        LEFT JOIN sens ON lexie.id_lexie = sens.id_lexie
        LEFT JOIN expression ON lexie.id_lexie = expression.id_lexie
        WHERE
        ({exact_query_where})

        ORDER BY lexie.id_lexie
        LIMIT 50
    """, tuple(params_exact))
    start_results = cursor.fetchall()
    print(f"  dglai14 - Start Results Count: {len(start_results)}") # Debug print

    # Contain Search (dglai14)
    cursor.execute(f"""
        SELECT lexie.*, sens.sens_fr, sens.sens_ar,
               expression.exp_amz, expression.exp_fr, expression.exp_ar
        FROM lexie
        LEFT JOIN sens ON lexie.id_lexie = sens.id_lexie
        LEFT JOIN expression ON lexie.id_lexie = expression.id_lexie
        WHERE (
        ({contain_query_where})
        )
        AND NOT (NORMALIZE_AMAZIGH(lexie) {like_op_exact} ?)  -- To exclude start results
        ORDER BY lexie.id_lexie
        LIMIT 50
    """, tuple(params_contain + [search_term_exact]))  # Use start_search_term for the NOT LIKE part
    contain_results = cursor.fetchall()
    print(f"  dglai14 - Contain Results Count: {len(contain_results)}") # Debug print
    conn.close()
    return list(start_results) + list(contain_results)

def search_tawalt_fr(search_term_exact, search_term_contain, limit, exact_match, french_only=False, amazigh_only=False, arabic_only=False):
    conn = get_db_connection('tawalt_fr.db')
    cursor = conn.cursor()

    # Add the custom SQLite function for Amazigh and French normalization
    conn.create_function("NORMALIZE_AMAZIGH", 1, normalize_amazigh_text)
    conn.create_function("NORMALIZE_FRENCH", 1, normalize_french_text)

    like_op_exact = "=" if exact_match else "LIKE"
    like_op_contain = "=" if exact_match else "LIKE"

    query_parts = []
    params_exact = []
    params_contain = []

    if not french_only and not arabic_only: # Default or Amazigh/General search
        query_parts.extend([
            f"(NORMALIZE_AMAZIGH(tifinagh) {like_op_exact} ?)",
            f"(NORMALIZE_AMAZIGH(tifinagh) {like_op_contain} ?)",
        ])
        params_exact.append(search_term_exact)
        params_contain.append(search_term_contain)

    if not amazigh_only and not arabic_only: # Default or General/French search
        query_parts.extend([
            f"(NORMALIZE_FRENCH(french) {like_op_exact} ?)",
            f"(NORMALIZE_FRENCH(french) {like_op_contain} ?)",
        ])
        params_exact.append(search_term_exact)
        params_contain.append(search_term_contain)


    start_query_where = " OR ".join(query_parts[::2]) # Take even indices for start
    contain_query_where = " OR ".join(query_parts[1::2]) # Take odd indices for contain

    print(f"  tawalt_fr - Exact Search Term: '{search_term_exact}', Contain: '{search_term_contain}', Exact: {exact_match}, French Only: {french_only}, Amazigh Only: {amazigh_only}, Arabic Only: {arabic_only}") # Debug print

    # Start Search (tawalt_fr)
    cursor.execute(f"""
        SELECT *
        FROM words
        WHERE
        ({start_query_where})
        ORDER BY _id
        LIMIT ?
    """, tuple(params_exact + [limit]))
    start_results = cursor.fetchall()
    print(f"  tawalt_fr - Start Results Count: {len(start_results)}") # Debug print

    # Contain Search (tawalt_fr)
    cursor.execute(f"""
        SELECT *
        FROM words
        WHERE (
        ({contain_query_where})
        )
        AND NOT (NORMALIZE_AMAZIGH(tifinagh) {like_op_exact} ?) -- Exclude start results based on tifinagh
        ORDER BY _id
        LIMIT ?
    """, tuple(params_contain + [search_term_exact, limit])) # Use search_term_exact for NOT LIKE
    contain_results = cursor.fetchall()
    print(f"  tawalt_fr - Contain Results Count: {len(contain_results)}") # Debug print
    conn.close()
    return list(start_results) + list(contain_results)


def search_tawalt(search_term_exact, search_term_contain, limit, exact_match, arabic_only=False, amazigh_only=False, french_only=False):
    conn = get_db_connection('tawalt.db')
    cursor = conn.cursor()

    # Add the custom SQLite function for Amazigh normalization
    conn.create_function("NORMALIZE_AMAZIGH", 1, normalize_amazigh_text)  #To be removed if the database is selectable

    like_op_exact = "=" if exact_match else "LIKE"
    like_op_contain = "=" if exact_match else "LIKE"

    query_parts = []
    params_exact = []
    params_contain = []

    if not arabic_only and not french_only: # Default or Amazigh/General search
        query_parts.extend([
            f"(NORMALIZE_AMAZIGH(tifinagh) {like_op_exact} ?)",
            f"(NORMALIZE_AMAZIGH(tifinagh_in_arabic) {like_op_exact} ?)",
            f"(NORMALIZE_AMAZIGH(_tifinagh_in_arabic) {like_op_exact} ?)",

            f"(NORMALIZE_AMAZIGH(tifinagh) {like_op_contain} ?)",
            f"(NORMALIZE_AMAZIGH(tifinagh_in_arabic) {like_op_contain} ?)",
            f"(NORMALIZE_AMAZIGH(_tifinagh_in_arabic) {like_op_contain} ?)",
        ])
        params_exact.extend([search_term_exact] * 3)
        params_contain.extend([search_term_contain] * 3)


    if not amazigh_only and not french_only: # Default or General/Arabic search
        query_parts.extend([
            f"(REMOVE_DIACRITICS(LOWER(arabic)) {like_op_exact} ?)",
            f"(REMOVE_DIACRITICS(LOWER(arabic_meaning)) {like_op_exact} ?)",
            f"(REMOVE_DIACRITICS(LOWER(_arabic)) {like_op_exact} ?)",
            f"(REMOVE_DIACRITICS(LOWER(_arabic_meaning)) {like_op_exact} ?)",

            f"(REMOVE_DIACRITICS(LOWER(arabic)) {like_op_contain} ?)",
            f"(REMOVE_DIACRITICS(LOWER(arabic_meaning)) {like_op_contain} ?)",
            f"(REMOVE_DIACRITICS(LOWER(_arabic)) {like_op_contain} ?)",
            f"(REMOVE_DIACRITICS(LOWER(_arabic_meaning)) {like_op_contain} ?)",
        ])
        params_exact.extend([search_term_exact] * 4)
        params_contain.extend([search_term_contain] * 4)


    start_query_where = " OR ".join(query_parts[::2]) # Take even indices for start
    contain_query_where = " OR ".join(query_parts[1::2]) # Take odd indices for contain

    print(f"  tawalt - Exact Search Term: '{search_term_exact}', Contain: '{search_term_contain}', Exact: {exact_match}, Arabic Only: {arabic_only}, Amazigh Only: {amazigh_only}, French Only: {french_only}") # Debug print

    # Start Search (tawalt)
    cursor.execute(f"""
        SELECT *
        FROM words
        WHERE
        ({start_query_where})
        ORDER BY _id
        LIMIT ?
    """, tuple(params_exact + [limit]))
    start_results = cursor.fetchall()
    print(f"  tawalt - Start Results Count: {len(start_results)}") # Debug print

    # Contain Search (tawalt)
    cursor.execute(f"""
        SELECT *
        FROM words
        WHERE (
        ({contain_query_where})
        )
        AND NOT (NORMALIZE_AMAZIGH(tifinagh) {like_op_exact} ?) -- Exclude start results based on tifinagh
        ORDER BY _id
        LIMIT ?
    """, tuple(params_contain + [search_term_exact, limit])) # Use search_term_exact for NOT LIKE
    contain_results = cursor.fetchall()
    print(f"  tawalt - Contain Results Count: {len(contain_results)}") # Debug print
    conn.close()
    return list(start_results) + list(contain_results)

def search_eng(search_term_exact, search_term_contain, limit, exact_match, amazigh_only=False, french_only=False, arabic_only=False):
    conn = get_db_connection('eng.db')
    cursor = conn.cursor()
    conn.create_function("NORMALIZE_AMAZIGH", 1, normalize_amazigh_text)

    like_op_exact = "=" if exact_match else "LIKE"
    like_op_contain = "=" if exact_match else "LIKE"

    print(f"  eng - Exact Search Term: '{search_term_exact}', Contain: '{search_term_contain}', Exact: {exact_match}, Amazigh Only: {amazigh_only}, French Only: {french_only}, Arabic Only: {arabic_only}") # Debug print

    query_clauses = []
    params_exact = []
    params_contain = []

    if not french_only and not arabic_only: # Default or Amazigh/General search
        query_clauses.extend([
            f"(NORMALIZE_AMAZIGH(da.lexie) {like_op_exact} ?)",
            f"(NORMALIZE_AMAZIGH(da.remarque) {like_op_exact} ?)",
            f"(NORMALIZE_AMAZIGH(da.variante) {like_op_exact} ?)",
            f"(NORMALIZE_AMAZIGH(da.eadata) {like_op_exact} ?)",
            f"(NORMALIZE_AMAZIGH(da.pldata) {like_op_exact} ?)",

            f"(NORMALIZE_AMAZIGH(da.lexie) {like_op_contain} ?)",
            f"(NORMALIZE_AMAZIGH(da.remarque) {like_op_contain} ?)",
            f"(NORMALIZE_AMAZIGH(da.variante) {like_op_contain} ?)",
            f"(NORMALIZE_AMAZIGH(da.eadata) {like_op_contain} ?)",
            f"(NORMALIZE_AMAZIGH(da.pldata) {like_op_contain} ?)",
        ])
        params_exact.extend([search_term_exact] * 5)
        params_contain.extend([search_term_contain] * 5)


    if not amazigh_only and not french_only and not arabic_only: # Default or General search
        query_clauses.extend([
            f"(LOWER(da.cg) {like_op_exact} ?)",
            f"(LOWER(da.acc) {like_op_exact} ?)",
            f"(LOWER(da.acc_neg) {like_op_exact} ?)",
            f"(LOWER(da.inacc) {like_op_exact} ?)",
            f"(LOWER(dea.sens_eng) {like_op_exact} ?)",

            f"(LOWER(da.cg) {like_op_contain} ?)",
            f"(LOWER(da.acc) {like_op_contain} ?)",
            f"(LOWER(da.acc_neg) {like_op_contain} ?)",
            f"(LOWER(da.inacc) {like_op_contain} ?)",
            f"(LOWER(dea.sens_eng) {like_op_contain} ?)",
        ])
        params_exact.extend([search_term_exact] * 5)
        params_contain.extend([search_term_contain] * 5)


    exact_query_where = " OR ".join(query_clauses[::2]) # Even indices for exact
    contain_query_where = " OR ".join(query_clauses[1::2]) # Odd indices for contain


    cursor.execute(f"""
        SELECT da.*, dea.sens_eng
        FROM Dictionary_Amazigh_full AS da
        LEFT JOIN Dictionary_English_Amazih_links AS dea ON da.id_lexie = dea.id_lexie
        WHERE (
            {exact_query_where}
        )
        ORDER BY da.id_lexie
        LIMIT ?
    """, tuple(params_exact + [limit]))

    start_results = cursor.fetchall()
    print(f"  eng - Start Results Count: {len(start_results)}") # Debug print

    cursor.execute(f"""
      SELECT da.*, dea.sens_eng
        FROM Dictionary_Amazigh_full AS da
        LEFT JOIN Dictionary_English_Amazih_links AS dea ON da.id_lexie = dea.id_lexie
        WHERE (
            {contain_query_where}
        )
        AND NOT NORMALIZE_AMAZIGH(da.lexie) {like_op_exact} ? -- Exclude start results based on lexie
        ORDER BY da.id_lexie
        LIMIT ?
    """, tuple(params_contain + [search_term_exact, limit]))
    contain_results = cursor.fetchall()
    print(f"  eng - Contain Results Count: {len(contain_results)}") # Debug print
    conn.close()

    return list(start_results) + list(contain_results)

def search_msmun_fr_m(search_term_exact, search_term_contain, limit, exact_match, french_only=False, amazigh_only=False, arabic_only=False):
    conn = get_db_connection('msmun_fr.db')
    cursor = conn.cursor()
    conn.create_function("NORMALIZE_AMAZIGH", 1, normalize_amazigh_text)
    conn.create_function("NORMALIZE_FRENCH", 1, normalize_french_text)

    like_op_exact = "=" if exact_match else "LIKE"
    like_op_contain = "=" if exact_match else "LIKE"

    query_parts = []
    params_exact = []
    params_contain = []

    if not french_only and not arabic_only: # Default or Amazigh/General search
        query_parts.extend([
            f"(NORMALIZE_AMAZIGH(word) {like_op_exact} ?)",
            f"(NORMALIZE_AMAZIGH(word) {like_op_contain} ?)",
        ])
        params_exact.append(search_term_exact)
        params_contain.append(search_term_contain)


    if not amazigh_only and not arabic_only: # Default or General/French search
        query_parts.extend([
            f"(NORMALIZE_FRENCH(result) {like_op_exact} ?)",
            f"(NORMALIZE_FRENCH(result) {like_op_contain} ?)",
        ])
        params_exact.append(search_term_exact)
        params_contain.append(search_term_contain)


    start_query_where = " OR ".join(query_parts[::2]) # Take even indices for start
    contain_query_where = " OR ".join(query_parts[1::2]) # Take odd indices for contain

    print(f"  msmun_fr_m - Exact Search Term: '{search_term_exact}', Contain: '{search_term_contain}', Exact: {exact_match}, French Only: {french_only}, Amazigh Only: {amazigh_only}, Arabic Only: {arabic_only}") # Debug print

    cursor.execute(f"""
        SELECT *
        FROM table_m
        WHERE (
            {start_query_where}
        )
        ORDER BY _id
        LIMIT ?
    """, tuple(params_exact + [limit]))
    start_results = cursor.fetchall()
    print(f"  msmun_fr_m - Start Results Count: {len(start_results)}") # Debug print

    cursor.execute(f"""
        SELECT *
        FROM table_m
        WHERE (
            {contain_query_where}
        )
        AND NOT NORMALIZE_AMAZIGH(word) {like_op_exact} ? -- Exclude start results based on word
        ORDER BY _id
        LIMIT ?
    """, tuple(params_contain + [search_term_exact, limit]))
    contain_results = cursor.fetchall()
    print(f"  msmun_fr_m - Contain Results Count: {len(contain_results)}") # Debug print
    conn.close()
    return list(start_results) + list(contain_results)

def search_msmun_fr_r(search_term_exact, search_term_contain, limit, exact_match, french_only=False, amazigh_only=False, arabic_only=False):
    conn = get_db_connection('msmun_fr.db')
    cursor = conn.cursor()
    conn.create_function("NORMALIZE_AMAZIGH", 1, normalize_amazigh_text)
    conn.create_function("NORMALIZE_FRENCH", 1, normalize_french_text)

    like_op_exact = "=" if exact_match else "LIKE"
    like_op_contain = "=" if exact_match else "LIKE"

    query_parts = []
    params_exact = []
    params_contain = []

    if not french_only and not arabic_only: # Default or Amazigh/General search
        query_parts.extend([
            f"(NORMALIZE_AMAZIGH(result) {like_op_exact} ?)",
            f"(NORMALIZE_AMAZIGH(result) {like_op_contain} ?)",
        ])
        params_exact.append(search_term_exact)
        params_contain.append(search_term_contain)

    if not amazigh_only and not arabic_only: # Default or General/French search
        query_parts.extend([
            f"(NORMALIZE_FRENCH(word) {like_op_exact} ?)",
            f"(NORMALIZE_FRENCH(word) {like_op_contain} ?)",
        ])
        params_exact.append(search_term_exact)
        params_contain.append(search_term_contain)


    start_query_where = " OR ".join(query_parts[::2]) # Take even indices for start
    contain_query_where = " OR ".join(query_parts[1::2]) # Take odd indices for contain

    print(f"  msmun_fr_r - Exact Search Term: '{search_term_exact}', Contain: '{search_term_contain}', Exact: {exact_match}, French Only: {french_only}, Amazigh Only: {amazigh_only}, Arabic Only: {arabic_only}") # Debug print

    cursor.execute(f"""
        SELECT *
        FROM table_r
        WHERE (
            {start_query_where}
        )
        ORDER BY _id
        LIMIT ?
    """, tuple(params_exact + [limit]))
    start_results = cursor.fetchall()
    print(f"  msmun_fr_r - Start Results Count: {len(start_results)}") # Debug print

    cursor.execute(f"""
        SELECT *
        FROM table_r
        WHERE (
            {contain_query_where}
        )
        AND NOT NORMALIZE_FRENCH(word) {like_op_exact} ? -- Exclude start results based on word
        ORDER BY _id
        LIMIT ?
    """, tuple(params_contain + [search_term_exact, limit]))
    contain_results = cursor.fetchall()
    print(f"  msmun_fr_r - Contain Results Count: {len(contain_results)}") # Debug print
    conn.close()
    return list(start_results) + list(contain_results)


def search_msmun_ar_m_r(search_term_exact, search_term_contain, limit, exact_match, arabic_only=False, amazigh_only=False, french_only=False):
    conn = get_db_connection('msmun_ar.db')
    cursor = conn.cursor()
    conn.create_function("NORMALIZE_AMAZIGH", 1, normalize_amazigh_text)

    like_op_exact = "=" if exact_match else "LIKE"
    like_op_contain = "=" if exact_match else "LIKE"

    query_parts = []
    params_exact = []
    params_contain = []

    if not arabic_only and not french_only: # Default or Amazigh/General search
        query_parts.extend([
            f"(NORMALIZE_AMAZIGH(word) {like_op_exact} ?)",
            f"(NORMALIZE_AMAZIGH(word) {like_op_contain} ?)",
        ])
        params_exact.append(search_term_exact)
        params_contain.append(search_term_contain)


    if not amazigh_only: # Default or General/Arabic/French search
        query_parts.extend([
            f"(REMOVE_DIACRITICS(LOWER(result)) {like_op_exact} ?)",
            f"(REMOVE_DIACRITICS(LOWER(result)) {like_op_contain} ?)",
        ])
        params_exact.append(search_term_exact)
        params_contain.append(search_term_contain)


    start_query_where = " OR ".join(query_parts[::2]) # Take even indices for start
    contain_query_where = " OR ".join(query_parts[1::2]) # Take odd indices for contain

    print(f"  msmun_ar_m_r - Exact Search Term: '{search_term_exact}', Contain: '{search_term_contain}', Exact: {exact_match}, Arabic Only: {arabic_only}, Amazigh Only: {amazigh_only}, French Only: {french_only}") # Debug print

    cursor.execute(f"""
        SELECT *
        FROM table_m_r
        WHERE (
            {start_query_where}
        )
        ORDER BY _id
        LIMIT ?
    """, tuple(params_exact + [limit]))
    start_results = cursor.fetchall()
    print(f"  msmun_ar_m_r - Start Results Count: {len(start_results)}") # Debug print

    cursor.execute(f"""
        SELECT *
        FROM table_m_r
        WHERE (
            {contain_query_where}
        )
        AND NOT NORMALIZE_AMAZIGH(word) {like_op_exact} ? -- Exclude start results based on word
        ORDER BY _id
        LIMIT ?
    """, tuple(params_contain + [search_term_exact, limit]))
    contain_results = cursor.fetchall()
    print(f"  msmun_ar_m_r - Contain Results Count: {len(contain_results)}") # Debug print
    conn.close()
    return list(start_results) + list(contain_results)

def search_msmun_ar_r_m(search_term_exact, search_term_contain, limit, exact_match, arabic_only=False, amazigh_only=False, french_only=False):
    conn = get_db_connection('msmun_ar.db')
    cursor = conn.cursor()
    conn.create_function("NORMALIZE_AMAZIGH", 1, normalize_amazigh_text)

    like_op_exact = "=" if exact_match else "LIKE"
    like_op_contain = "=" if exact_match else "LIKE"

    query_parts = []
    params_exact = []
    params_contain = []

    if not arabic_only and not french_only: # Default or Amazigh/General search
        query_parts.extend([
            f"(NORMALIZE_AMAZIGH(result) {like_op_exact} ?)",
            f"(NORMALIZE_AMAZIGH(result) {like_op_contain} ?)",
        ])
        params_exact.append(search_term_exact)
        params_contain.append(search_term_contain)

    if not amazigh_only: # Default or General/Arabic/French search
        query_parts.extend([
            f"(REMOVE_DIACRITICS(LOWER(word)) {like_op_exact} ?)",
            f"(REMOVE_DIACRITICS(LOWER(word)) {like_op_contain} ?)",
        ])
        params_exact.append(search_term_exact)
        params_contain.append(search_term_contain)


    start_query_where = " OR ".join(query_parts[::2]) # Take even indices for start
    contain_query_where = " OR ".join(query_parts[1::2]) # Take odd indices for contain

    print(f"  msmun_ar_r_m - Exact Search Term: '{search_term_exact}', Contain: '{search_term_contain}', Exact: {exact_match}, Arabic Only: {arabic_only}, Amazigh Only: {amazigh_only}, French Only: {french_only}") # Debug print

    cursor.execute(f"""
        SELECT *
        FROM table_r_m
        WHERE (
            {start_query_where}
        )
        ORDER BY _id
        LIMIT ?
    """, tuple(params_exact + [limit]))
    start_results = cursor.fetchall()
    print(f"  msmun_ar_r_m - Start Results Count: {len(start_results)}") # Debug print

    cursor.execute(f"""
        SELECT *
        FROM table_r_m
        WHERE (
            {contain_query_where}
        )
        AND NOT REMOVE_DIACRITICS(LOWER(word)) {like_op_exact} ? -- Exclude start results based on word
        ORDER BY _id
        LIMIT ?
    """, tuple(params_contain + [search_term_exact, limit]))
    contain_results = cursor.fetchall()
    print(f"  msmun_ar_r_m - Contain Results Count: {len(contain_results)}") # Debug print
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


# Create Gradio interface
with gr.Blocks(css="""
footer {display: none !important}
.gr-radio .item.selected {
    background-color: rgba(var(--primary-500-rgb), 0.2); /* Light color from primary theme, adjust as needed */
    border-radius: 5px;
    padding: 5px;
}
.search-row {
    display: flex;
    align-items: stretch; /* Align items vertically */
}
.search-input {
    flex-grow: 1; /* Input takes up available space */
    margin-right: 5px; /* Space between input and button */
}
""") as iface:
    gr.HTML("""
    <div style="text-align: center; margin-bottom: 2rem;">
    <h1 style="color: #2c3e50; margin-bottom: 1rem;">Amazigh Dictionary</h1>
    </div>
    """)

    with gr.Row():
        language_radio = gr.Radio(
            ["General", "Amazigh", "French", "Arabic"],
            label="Language",
            value="General",
            interactive=True,
        )

    with gr.Row(elem_classes="search-row"): # Added class to the row
        input_text = gr.Textbox(
            label="Search",
            placeholder="Enter a word to search...",
            lines=1,
            elem_classes="search-input" # Added class to the input
        )
        search_button = gr.Button("Search") # Add search button

    with gr.Row():
        exact_checkbox = gr.Checkbox(label="Exact search", value=False)

    output_html = gr.HTML()

    search_button.click( # Use button.click instead of text.change
        fn=search_dictionary,
        inputs=[input_text, language_radio, exact_checkbox],
        outputs=output_html,
        api_name="search"
    )

if __name__ == "__main__":
    iface.launch()
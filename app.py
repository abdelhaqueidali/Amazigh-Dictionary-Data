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

def search_dictionary(query, exact_search, language):
    if not query or len(query.strip()) < 1:
        return "Please enter a search term"

    normalized_query_general = normalize_general_text(query)
    normalized_query_amazigh = normalize_amazigh_text(query)

    if exact_search:
        search_results = search_exact_mode(normalized_query_general, normalized_query_amazigh, language)
    else:
        search_results = search_fuzzy_mode(normalized_query_general, normalized_query_amazigh, language)

    # --- Combine and Format Results ---
    html_output = format_results(search_results)

    if not html_output:
        return "No results found"

    return html_output

def search_exact_mode(normalized_query_general, normalized_query_amazigh, language):
    results = []
    remaining_results = 50

    db_order = get_db_order(language)

    for db_name in db_order:
        if remaining_results <= 0:
            break

        if db_name == 'dglai14.db':
            db_results = search_dglai14_exact(normalized_query_general, normalized_query_amazigh, remaining_results)
        elif db_name == 'tawalt_fr.db':
            db_results = search_tawalt_fr_exact(normalized_query_general, normalized_query_amazigh, remaining_results)
        elif db_name == 'tawalt.db':
            db_results = search_tawalt_exact(normalized_query_general, normalized_query_amazigh, remaining_results)
        elif db_name == 'eng.db':
            db_results = search_eng_exact(normalized_query_general, normalized_query_amazigh, remaining_results)
        elif db_name == 'msmun_fr.db':
            db_results_m = search_msmun_fr_m_exact(normalized_query_general, normalized_query_amazigh, remaining_results)
            db_results_r = search_msmun_fr_r_exact(normalized_query_general, normalized_query_amazigh, remaining_results)
            db_results = db_results_m + db_results_r
        elif db_name == 'msmun_ar.db':
            db_results_mr = search_msmun_ar_m_r_exact(normalized_query_general, normalized_query_amazigh, remaining_results)
            db_results_rm = search_msmun_ar_r_m_exact(normalized_query_general, normalized_query_amazigh, remaining_results)
            db_results = db_results_mr + db_results_rm
        else:
            continue

        results.extend(db_results[:remaining_results])
        remaining_results -= len(db_results[:remaining_results])
    return results


def search_fuzzy_mode(normalized_query_general, normalized_query_amazigh, language):
    start_search_term_general = f"{normalized_query_general}%"
    contain_search_term_general = f"%{normalized_query_general}%"
    start_search_term_amazigh = f"{normalized_query_amazigh}%"
    contain_search_term_amazigh = f"%{normalized_query_amazigh}%"

    results = []
    remaining_results = 50

    db_order = get_db_order(language)

    for db_name in db_order:
        if remaining_results <= 0:
            break

        if db_name == 'dglai14.db':
            db_results = search_dglai14(start_search_term_general, contain_search_term_general,start_search_term_amazigh, contain_search_term_amazigh)
        elif db_name == 'tawalt_fr.db':
            db_results = search_tawalt_fr(start_search_term_general, contain_search_term_general, start_search_term_amazigh, contain_search_term_amazigh, remaining_results)
        elif db_name == 'tawalt.db':
            db_results = search_tawalt(start_search_term_general, contain_search_term_general,start_search_term_amazigh, contain_search_term_amazigh, remaining_results)
        elif db_name == 'eng.db':
            db_results = search_eng(start_search_term_general, contain_search_term_general, start_search_term_amazigh, contain_search_term_amazigh, remaining_results)
        elif db_name == 'msmun_fr.db':
            db_results_m = search_msmun_fr_m(start_search_term_general, contain_search_term_general, start_search_term_amazigh, contain_search_term_amazigh, remaining_results)
            db_results_r = search_msmun_fr_r(start_search_term_general, contain_search_term_general, start_search_term_amazigh, contain_search_term_amazigh, remaining_results)
            db_results = db_results_m + db_results_r
        elif db_name == 'msmun_ar.db':
            db_results_mr = search_msmun_ar_m_r(start_search_term_general, contain_search_term_general, start_search_term_amazigh, contain_search_term_amazigh, remaining_results)
            db_results_rm = search_msmun_ar_r_m(start_search_term_general, contain_search_term_general, start_search_term_amazigh, contain_search_term_amazigh, remaining_results)
            db_results = db_results_mr + db_results_rm
        else:
            continue

        results.extend(db_results[:remaining_results])
        remaining_results -= len(db_results[:remaining_results])
    return results

def get_db_order(language):
    if language == "Amazigh":
        return ['dglai14.db', 'tawalt.db', 'tawalt_fr.db', 'eng.db', 'msmun_fr.db', 'msmun_ar.db'] #Amazigh prioritized
    elif language == "French":
        return ['tawalt_fr.db', 'msmun_fr.db', 'dglai14.db', 'tawalt.db', 'eng.db', 'msmun_ar.db'] #French prioritized
    elif language == "Arabic":
        return ['tawalt.db', 'msmun_ar.db', 'dglai14.db', 'tawalt_fr.db', 'eng.db', 'msmun_fr.db'] #Arabic prioritized
    elif language == "English":
        return ['eng.db', 'dglai14.db', 'tawalt_fr.db', 'tawalt.db', 'msmun_fr.db', 'msmun_ar.db'] #English prioritized
    else: # General or "All"
        return ['dglai14.db', 'tawalt_fr.db', 'tawalt.db', 'eng.db', 'msmun_fr.db', 'msmun_ar.db'] #Original order

def search_dglai14_exact(exact_search_term_general, exact_search_term_amazigh, limit):
    conn = get_db_connection('dglai14.db')
    cursor = conn.cursor()
    conn.create_function("NORMALIZE_AMAZIGH", 1, normalize_amazigh_text)

    cursor.execute("""
        SELECT lexie.*, sens.sens_fr, sens.sens_ar,
               expression.exp_amz, expression.exp_fr, expression.exp_ar
        FROM lexie
        LEFT JOIN sens ON lexie.id_lexie = sens.id_lexie
        LEFT JOIN expression ON lexie.id_lexie = expression.id_lexie
        WHERE
        (NORMALIZE_AMAZIGH(lexie) = ?)
        OR (NORMALIZE_AMAZIGH(remarque) = ?)
        OR (NORMALIZE_AMAZIGH(variante) = ?)
        OR (REMOVE_DIACRITICS(LOWER(cg)) = ?)
        OR (NORMALIZE_AMAZIGH(eadata) = ?)
        OR (NORMALIZE_AMAZIGH(pldata) = ?)
        OR (REMOVE_DIACRITICS(LOWER(acc)) = ?)
        OR (REMOVE_DIACRITICS(LOWER(acc_neg)) = ?)
        OR (REMOVE_DIACRITICS(LOWER(inacc)) = ?)
        OR (REMOVE_DIACRITICS(LOWER(fel)) = ?)
        OR (REMOVE_DIACRITICS(LOWER(fea)) = ?)
        OR (REMOVE_diacritics(LOWER(fpel)) = ?)
        OR (REMOVE_DIACRITICS(LOWER(fpea)) = ?)
        OR (REMOVE_DIACRITICS(LOWER(sens_ar)) = ?)
        OR (NORMALIZE_AMAZIGH(expression.exp_amz) = ?)
        OR (REMOVE_DIACRITICS(LOWER(expression.exp_ar)) = ?)
        ORDER BY lexie.id_lexie
        LIMIT ?
    """, (exact_search_term_amazigh, exact_search_term_amazigh, exact_search_term_amazigh, exact_search_term_general,
          exact_search_term_amazigh, exact_search_term_amazigh, exact_search_term_general, exact_search_term_general, exact_search_term_general,
          exact_search_term_general, exact_search_term_general, exact_search_term_general, exact_search_term_general,
          exact_search_term_general, exact_search_term_amazigh, exact_search_term_general, limit))
    exact_results = cursor.fetchall()
    conn.close()
    return exact_results

def search_tawalt_fr_exact(exact_search_term_general, exact_search_term_amazigh, limit):
    conn = get_db_connection('tawalt_fr.db')
    cursor = conn.cursor()
    conn.create_function("NORMALIZE_AMAZIGH", 1, normalize_amazigh_text)
    conn.create_function("NORMALIZE_FRENCH", 1, normalize_french_text)

    cursor.execute("""
        SELECT *
        FROM words
        WHERE
        (NORMALIZE_AMAZIGH(tifinagh) = ?)
        OR (NORMALIZE_FRENCH(french) = ?)
        ORDER BY _id
        LIMIT ?
    """, (exact_search_term_amazigh, exact_search_term_general, limit))
    exact_results = cursor.fetchall()
    conn.close()
    return exact_results

def search_tawalt_exact(exact_search_term_general, exact_search_term_amazigh, limit):
    conn = get_db_connection('tawalt.db')
    cursor = conn.cursor()
    conn.create_function("NORMALIZE_AMAZIGH", 1, normalize_amazigh_text)

    cursor.execute("""
        SELECT *
        FROM words
        WHERE
        (NORMALIZE_AMAZIGH(tifinagh) = ?)
        OR (REMOVE_DIACRITICS(LOWER(arabic)) = ?)
        OR (REMOVE_DIACRITICS(LOWER(arabic_meaning)) = ?)
        OR (NORMALIZE_AMAZIGH(tifinagh_in_arabic) = ?)
        OR (NORMALIZE_AMAZIGH(_arabic) = ?)
        OR (NORMALIZE_AMAZIGH(_arabic_meaning) = ?)
        OR (NORMALIZE_AMAZIGH(_tifinagh_in_arabic) = ?)
        ORDER BY _id
        LIMIT ?
    """, (exact_search_term_amazigh, exact_search_term_general, exact_search_term_general, exact_search_term_amazigh,
          exact_search_term_amazigh, exact_search_term_amazigh, exact_search_term_amazigh, limit))
    exact_results = cursor.fetchall()
    conn.close()
    return exact_results

def search_eng_exact(exact_search_term_general, exact_search_term_amazigh, limit):
    conn = get_db_connection('eng.db')
    cursor = conn.cursor()
    conn.create_function("NORMALIZE_AMAZIGH", 1, normalize_amazigh_text)

    cursor.execute("""
        SELECT da.*, dea.sens_eng
        FROM Dictionary_Amazigh_full AS da
        LEFT JOIN Dictionary_English_Amazih_links AS dea ON da.id_lexie = dea.id_lexie
        WHERE (
            NORMALIZE_AMAZIGH(da.lexie) = ?
            OR NORMALIZE_AMAZIGH(da.remarque) = ?
            OR NORMALIZE_AMAZIGH(da.variante) = ?
            OR LOWER(da.cg) = ?
            OR NORMALIZE_AMAZIGH(da.eadata) = ?
            OR NORMALIZE_AMAZIGH(da.pldata) = ?
            OR LOWER(da.acc) = ?
            OR LOWER(da.acc_neg) = ?
            OR LOWER(da.inacc) = ?
            OR LOWER(dea.sens_eng) = ?
        )
        ORDER BY da.id_lexie
        LIMIT ?
    """, (exact_search_term_amazigh, exact_search_term_amazigh, exact_search_term_amazigh, exact_search_term_general,
          exact_search_term_amazigh, exact_search_term_amazigh, exact_search_term_general, exact_search_term_general,
          exact_search_term_general, exact_search_term_general, limit))
    exact_results = cursor.fetchall()
    conn.close()
    return exact_results

def search_msmun_fr_m_exact(exact_search_term_general, exact_search_term_amazigh, limit):
    conn = get_db_connection('msmun_fr.db')
    cursor = conn.cursor()
    conn.create_function("NORMALIZE_AMAZIGH", 1, normalize_amazigh_text)
    conn.create_function("NORMALIZE_FRENCH", 1, normalize_french_text)

    cursor.execute("""
        SELECT *
        FROM table_m
        WHERE (
            NORMALIZE_AMAZIGH(word) = ?
            OR NORMALIZE_FRENCH(result) = ?
        )
        ORDER BY _id
        LIMIT ?
    """, (exact_search_term_amazigh, exact_search_term_general, limit))
    exact_results = cursor.fetchall()
    conn.close()
    return exact_results

def search_msmun_fr_r_exact(exact_search_term_general, exact_search_term_amazigh, limit):
    conn = get_db_connection('msmun_fr.db')
    cursor = conn.cursor()
    conn.create_function("NORMALIZE_AMAZIGH", 1, normalize_amazigh_text)
    conn.create_function("NORMALIZE_FRENCH", 1, normalize_french_text)

    cursor.execute("""
        SELECT *
        FROM table_r
        WHERE (
            NORMALIZE_FRENCH(word) = ?
            OR NORMALIZE_AMAZIGH(result) = ?
        )
        ORDER BY _id
        LIMIT ?
    """, (exact_search_term_general, exact_search_term_amazigh, limit))
    exact_results = cursor.fetchall()
    conn.close()
    return exact_results

def search_msmun_ar_m_r_exact(exact_search_term_general, exact_search_term_amazigh, limit):
    conn = get_db_connection('msmun_ar.db')
    cursor = conn.cursor()
    conn.create_function("NORMALIZE_AMAZIGH", 1, normalize_amazigh_text)

    cursor.execute("""
        SELECT *
        FROM table_m_r
        WHERE (
            NORMALIZE_AMAZIGH(word) = ?
            OR REMOVE_DIACRITICS(LOWER(result)) = ?
        )
        ORDER BY _id
        LIMIT ?
    """, (exact_search_term_amazigh, exact_search_term_general, limit))
    exact_results = cursor.fetchall()
    conn.close()
    return exact_results

def search_msmun_ar_r_m_exact(exact_search_term_general, exact_search_term_amazigh, limit):
    conn = get_db_connection('msmun_ar.db')
    cursor = conn.cursor()
    conn.create_function("NORMALIZE_AMAZIGH", 1, normalize_amazigh_text)

    cursor.execute("""
        SELECT *
        FROM table_r_m
        WHERE (
            REMOVE_DIACRITICS(LOWER(word)) = ?
            OR NORMALIZE_AMAZIGH(result) = ?
        )
        ORDER BY _id
        LIMIT ?
    """, (exact_search_term_general, exact_search_term_amazigh, limit))
    exact_results = cursor.fetchall()
    conn.close()
    return exact_results


def format_results(results):
    dglai14_results = []
    tawalt_fr_results = []
    tawalt_results = []
    eng_results = []
    msmun_fr_m_results = []
    msmun_fr_r_results = []
    msmun_ar_m_r_results = []
    msmun_ar_r_m_results = []

    for row in results:
        if 'cg' in row.keys() and 'sens_fr' in row.keys(): # Check for dglai14 keys
            dglai14_results.append(dict(row))
        elif 'french' in row.keys() and 'tifinagh' in row.keys() and 'words' == row.table_name: #Check for tawalt_fr keys
            tawalt_fr_results.append(dict(row))
        elif 'arabic' in row.keys() and 'tifinagh' in row.keys() and 'words' == row.table_name: # Check for tawalt keys
            tawalt_results.append(dict(row))
        elif 'sens_eng' in row.keys() and 'Dictionary_Amazigh_full' == row.table_name: # Check for eng keys
            eng_results.append(dict(row))
        elif 'table_name' == 'table_m' and 'result' in row.keys(): # Check for msmun_fr table_m keys
            msmun_fr_m_results.append(dict(row))
        elif 'table_name' == 'table_r' and 'result' in row.keys(): # Check for msmun_fr table_r keys
            msmun_fr_r_results.append(dict(row))
        elif 'table_name' == 'table_m_r' and 'result' in row.keys(): # Check for msmun_ar table_m_r keys
            msmun_ar_m_r_results.append(dict(row))
        elif 'table_name' == 'table_r_m' and 'result' in row.keys(): # Check for msmun_ar table_r_m keys
            msmun_ar_r_m_results.append(dict(row))

    html_output = format_dglai14_results(dglai14_results)  # Format dglai14 results
    html_output += format_tawalt_fr_results(tawalt_fr_results) # Format tawalt_fr results
    html_output += format_tawalt_results(tawalt_results) # Format tawalt results (if any)
    html_output += format_eng_results(eng_results)
    html_output += format_msmun_fr_m_results(msmun_fr_m_results) # Format msmun_fr table_m results
    html_output += format_msmun_fr_r_results(msmun_fr_r_results) # Format msmun_fr table_r results
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

    with gr.Row():
        exact_search_checkbox = gr.Checkbox(label="Exact Search", value=False)
        language_select = gr.Dropdown(
            ["General", "Amazigh", "French", "Arabic", "English"],
            value="General",
            label="Language"
        )
        search_button = gr.Button("Search")

    output_html = gr.HTML()

    search_button.click(
        fn=search_dictionary,
        inputs=[input_text, exact_search_checkbox, language_select],
        outputs=output_html,
        api_name="search"
    )

if __name__ == "__main__":
    iface.launch()
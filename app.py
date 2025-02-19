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
    conn = sqlite3.connect('tawalt.db')  # Connect to tawalt.db
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

    normalized_query_french = normalize_french_text(query)  # Keep French for potential future use with this DB
    normalized_query_general = normalize_general_text(query)

    start_search_term_french = f"{normalized_query_french}%" # Keep French for potential future use with this DB
    contain_search_term_french = f"%{normalized_query_french}%" # Keep French for potential future use with this DB
    start_search_term_general = f"{normalized_query_general}%"
    contain_search_term_general = f"%{normalized_query_general}%"


    # Query for results starting with the search term (in any field)
    cursor.execute("""
        SELECT *
        FROM words
        WHERE
        (REMOVE_DIACRITICS(LOWER(tifinagh)) LIKE ?)
        OR (REMOVE_DIACRITICS(LOWER(arabic)) LIKE ?)
        OR (REMOVE_DIACRITICS(LOWER(arabic_meaning)) LIKE ?)
        OR (REMOVE_DIACRITICS(LOWER(tifinagh_in_arabic)) LIKE ?)
        OR (REMOVE_DIACRITICS(LOWER(_arabic)) LIKE ?)
        OR (REMOVE_DIACRITICS(LOWER(_arabic_meaning)) LIKE ?)
        OR (REMOVE_DIACRITICS(LOWER(_tifinagh_in_arabic)) LIKE ?)
        ORDER BY _id
        LIMIT 50
    """, (start_search_term_general, start_search_term_general, start_search_term_general, start_search_term_general,
          start_search_term_general, start_search_term_general, start_search_term_general))  # Use general normalization

    start_results = cursor.fetchall()

    # Query for results containing the search term, but NOT starting with the tifinagh
    cursor.execute("""
        SELECT *
        FROM words
        WHERE (
        (REMOVE_DIACRITICS(LOWER(tifinagh)) LIKE ?)
        OR (REMOVE_DIACRITICS(LOWER(arabic)) LIKE ?)
        OR (REMOVE_DIACRITICS(LOWER(arabic_meaning)) LIKE ?)
        OR (REMOVE_DIACRITICS(LOWER(tifinagh_in_arabic)) LIKE ?)
        OR (REMOVE_DIACRITICS(LOWER(_arabic)) LIKE ?)
        OR (REMOVE_DIACRITICS(LOWER(_arabic_meaning)) LIKE ?)
        OR (REMOVE_DIACRITICS(LOWER(_tifinagh_in_arabic)) LIKE ?)
        )
        AND NOT (REMOVE_DIACRITICS(LOWER(tifinagh)) LIKE ?)
        ORDER BY _id
        LIMIT 50
    """, (contain_search_term_general, contain_search_term_general, contain_search_term_general, contain_search_term_general,
          contain_search_term_general, contain_search_term_general, contain_search_term_general,
          start_search_term_general)) # and not the start term in tifinagh
    contain_results = cursor.fetchall()

    conn.close()

    results = list(start_results) + list(contain_results)

    if not results:
        return "No results found"

    # No need for aggregation since there are no joins.  Directly format.
    html_output = ""
    for row in results[:50]:  # Limit to 50 results directly
        html_output += f"""
        <div style="background: white; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #3498db; padding-bottom: 10px; margin-bottom: 10px;">
                <h3 style="color: #2c3e50; margin: 0;">{row['tifinagh'] or ''}</h3>
            </div>
        """
        # Display relevant fields, handling potential NULL values
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
        # Add other fields similarly, if you need to display them
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

    output_html = gr.HTML()

    input_text.change(
        fn=search_dictionary,
        inputs=input_text,
        outputs=output_html,
        api_name="search"
    )

if __name__ == "__main__":
    iface.launch()
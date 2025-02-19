import gradio as gr
import sqlite3
import unicodedata

def get_db_connection():
    conn = sqlite3.connect('dglai14.db')
    conn.row_factory = sqlite3.Row
    return conn

def normalize_text(text):
    """Normalize text by removing diacritics and unifying characters."""
    if not text:
        return ""
    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    text = text.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")  # Normalize Arabic
    return text.lower()

def search_dictionary(query):
    if not query or len(query.strip()) < 1:
        return "Please enter a search term"
    
    normalized_query = normalize_text(query)
    search_term = f"%{normalized_query}%"
    
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT lexie.*, sens.sens_fr, sens.sens_ar, expression.exp_amz, expression.exp_fr, expression.exp_ar
        FROM lexie
        LEFT JOIN sens ON lexie.id_lexie = sens.id_lexie
        LEFT JOIN expression ON lexie.id_lexie = expression.id_lexie
        WHERE lower(lexie) LIKE ? OR lower(api) LIKE ? OR lower(sens_fr) LIKE ? OR lower(sens_ar) LIKE ?
        OR lower(expression.exp_amz) LIKE ? OR lower(expression.exp_fr) LIKE ? OR lower(expression.exp_ar) LIKE ?
        ORDER BY lexie.id_lexie
        LIMIT 50
    """, (search_term, search_term, search_term, search_term, search_term, search_term, search_term))
    results = cursor.fetchall()
    conn.close()

    if not results:
        return "No results found"

    # Formatting results
    html_output = """
    <div style='text-align: center; font-size: 18px; font-weight: bold;'>Search Results</div>
    """
    for row in results:
        html_output += f"""
        <div style='background: white; padding: 10px; border-radius: 5px; margin-top: 10px; box-shadow: 2px 2px 5px rgba(0,0,0,0.1);'>
            <h3 style='color: #2c3e50;'>{row['lexie']}</h3>
            <p><strong>API:</strong> {row['api'] or ''}</p>
            <p><strong>French:</strong> {row['sens_fr'] or ''}</p>
            <p><strong>Arabic:</strong> {row['sens_ar'] or ''}</p>
        </div>
        """
    return html_output

# Gradio UI
with gr.Blocks() as iface:
    gr.Markdown("# Amazigh Dictionary")
    query_input = gr.Textbox(label="Search")
    output_html = gr.HTML()
    query_input.change(search_dictionary, inputs=query_input, outputs=output_html)

if __name__ == "__main__":
    iface.launch()

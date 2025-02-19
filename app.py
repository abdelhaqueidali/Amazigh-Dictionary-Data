import gradio as gr
import sqlite3
from pathlib import Path

def get_db_connection():
    conn = sqlite3.connect('dglai14.db')
    conn.row_factory = sqlite3.Row
    return conn

def search_dictionary(query):
    if not query or len(query.strip()) < 1:
        return "Please enter a search term"

    conn = get_db_connection()
    cursor = conn.cursor()

    start_search_term = f"{query}%"
    contain_search_term = f"%{query}%"

    # Query for results starting with the search term (in any field)
    cursor.execute("""
        SELECT lexie.*, sens.sens_fr, sens.sens_ar
        FROM lexie
        LEFT JOIN sens ON lexie.id_lexie = sens.id_lexie
        WHERE lexie LIKE ?
        OR api LIKE ?
        OR remarque LIKE ?
        OR variante LIKE ?
        OR cg LIKE ?
        OR eadata LIKE ?
        OR pldata LIKE ?
        OR acc LIKE ?
        OR acc_neg LIKE ?
        OR inacc LIKE ?
        OR fel LIKE ?
        OR fea LIKE ?
        OR fpel LIKE ?
        OR fpea LIKE ?
        GROUP BY lexie.id_lexie  -- Group by lexie.id_lexie to remove duplicates
        LIMIT 50
    """, (start_search_term, start_search_term, start_search_term, start_search_term, start_search_term,
          start_search_term, start_search_term, start_search_term, start_search_term, start_search_term,
          start_search_term, start_search_term, start_search_term, start_search_term))
    start_results = cursor.fetchall()

    # Query for results containing the search term (in any field), but NOT starting with in lexie field
    cursor.execute("""
        SELECT lexie.*, sens.sens_fr, sens.sens_ar
        FROM lexie
        LEFT JOIN sens ON lexie.id_lexie = sens.id_lexie
        WHERE (lexie LIKE ?
        OR api LIKE ?
        OR remarque LIKE ?
        OR variante LIKE ?
        OR cg LIKE ?
        OR eadata LIKE ?
        OR pldata LIKE ?
        OR acc LIKE ?
        OR acc_neg LIKE ?
        OR inacc LIKE ?
        OR fel LIKE ?
        OR fea LIKE ?
        OR fpel LIKE ?
        OR fpea LIKE ?)
        AND NOT lexie LIKE ?  -- Exclude only if lexie starts with the search term
        GROUP BY lexie.id_lexie  -- Group by lexie.id_lexie to remove duplicates
        LIMIT 50
    """, (contain_search_term, contain_search_term, contain_search_term, contain_search_term, contain_search_term,
          contain_search_term, contain_search_term, contain_search_term, contain_search_term, contain_search_term,
          contain_search_term, contain_search_term, contain_search_term, contain_search_term,
          start_search_term)) # Using start_search_term for the NOT lexie LIKE condition
    contain_results = cursor.fetchall()

    conn.close()

    results = list(start_results) + list(contain_results)
    unique_results = []
    seen_lexie_ids = set()
    for row in results:
        if row['id_lexie'] not in seen_lexie_ids:
            unique_results.append(row)
            seen_lexie_ids.add(row['id_lexie'])


    if not unique_results:
        return "No results found"

    # Format results as HTML
    html_output = ""
    for row in unique_results[:50]: # Limit to 50 after combining and deduplication
        html_output += f"""
        <div style="background: white; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #3498db; padding-bottom: 10px; margin-bottom: 10px;">
                <h3 style="color: #2c3e50; margin: 0;">{row['lexie'] or ''}</h3>
                <span style="background: #3498db; color: white; padding: 4px 8px; border-radius: 4px;">{row['cg'] or ''}</span>
            </div>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 10px;">
        """

        # Add fields if they exist
        fields = {
            'Transcription': 'api',
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
            'French Translation': 'sens_fr',
            'Arabic Translation': 'sens_ar'
        }

        for label, field in fields.items():
            if row[field]:
                html_output += f"""
                <div style="margin-bottom: 8px;">
                    <strong style="color: #34495e;">{label}:</strong>
                    <span style="color: black;">{row[field]}</span>
                </div>
                """

        html_output += "</div></div>"

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
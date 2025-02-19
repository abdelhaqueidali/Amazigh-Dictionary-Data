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
    
    search_term = f"%{query}%"
    cursor.execute("""
        SELECT * FROM lexie 
        WHERE lexie LIKE ? 
        OR api LIKE ? 
        OR remarque LIKE ? 
        OR variante LIKE ?
        OR cg LIKE ?
        LIMIT 50
    """, (search_term, search_term, search_term, search_term, search_term))
    
    results = cursor.fetchall()
    conn.close()
    
    if not results:
        return "No results found"
    
    # Format results as HTML
    html_output = ""
    for row in results:
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
            'Feminine Plural Construct': 'fpea'
        }
        
        for label, field in fields.items():
            if row[field]:  # Check if the field has a value
                html_output += f"""
                <div style="margin-bottom: 8px;">
                    <strong style="color: #34495e;">{label}:</strong>
                    <span>{row[field]}</span> 
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
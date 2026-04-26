# src/visualizer/sankey_flow.py
import plotly.graph_objects as go
from dash import html, dcc

def create_sankey_flow(df):
    """
    Create a Sankey diagram representing the flow of intelligence:
    Source -> Category -> High-Degree Entity -> Sentiment
    """
    if df.empty:
        return html.Div("No data available for flow analysis.", style={'color': '#94a3b8', 'textAlign': 'center', 'padding': '20px'})

    # Use full filtered dataset for accurate flow representation (cap at 200 for readability)
    sample_df = df.head(200).copy()
    
    from collections import Counter
    
    # For entities, pick top ones
    all_ents = []
    for ents in sample_df['entities']:
        if isinstance(ents, str):
            all_ents.extend([e.strip() for e in ents.split(',') if e.strip()])
        elif hasattr(ents, '__iter__'):
            all_ents.extend([ent_obj.name for ent_obj in ents])
    
    top_entities = [e for e, c in Counter(all_ents).most_common(15)]
    if not top_entities:
        top_entities = ['No Entities']
        
    top_entities.append('Other Entities')

    # Nodes: Sources, Categories, Entities, Sentiments
    sources = sample_df['source'].unique().tolist()
    categories = sample_df['category'].unique().tolist()
    sentiments = sample_df['sentiment'].unique().tolist()

    # Map labels to indices
    labels = sources + categories + top_entities + sentiments
    label_map = {l: i for i, l in enumerate(labels)}
    
    link_counts = {}

    def add_link(src_label, tgt_label):
        if src_label not in label_map or tgt_label not in label_map:
            return
        pair = (label_map[src_label], label_map[tgt_label])
        link_counts[pair] = link_counts.get(pair, 0) + 1

    # Build continuous paths per article
    for _, row in sample_df.iterrows():
        src = row['source']
        cat = row['category']
        sent = row['sentiment']
        
        row_ents = []
        if isinstance(row['entities'], str):
            row_ents = [e.strip() for e in row['entities'].split(',') if e.strip()]
        elif hasattr(row['entities'], '__iter__'):
            row_ents = [ent_obj.name for ent_obj in row['entities']]
            
        valid_ents = [e for e in row_ents if e in top_entities]
        if not valid_ents:
            valid_ents = ['Other Entities']
            
        for ent in valid_ents:
            add_link(src, cat)
            add_link(cat, ent)
            add_link(ent, sent)

    source_indices = [pair[0] for pair in link_counts.keys()]
    target_indices = [pair[1] for pair in link_counts.keys()]
    values = list(link_counts.values())

    fig = go.Figure(data=[go.Sankey(
        node = dict(
          pad = 15,
          thickness = 20,
          line = dict(color = "#1e293b", width = 0.5),
          label = labels,
          color = "#00f2ff"
        ),
        link = dict(
          source = source_indices,
          target = target_indices,
          value = values,
          color = "rgba(0, 242, 255, 0.2)"
      ))])

    fig.update_layout(
        title_text="Intelligence Supply Chain: Source → Category → Entity → Risk",
        font_size=10,
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(t=40, b=20, l=10, r=10)
    )
    
    return dcc.Graph(figure=fig, config={'displayModeBar': False}, style={'height': '500px'})

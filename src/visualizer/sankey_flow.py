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
    
    # Nodes: Sources, Categories, Entities, Sentiments
    sources = sample_df['source'].unique().tolist()
    categories = sample_df['category'].unique().tolist()
    sentiments = sample_df['sentiment'].unique().tolist()
    
    # For entities, pick top ones
    all_ents = []
    for ents in sample_df['entities']:
        if isinstance(ents, str):
            all_ents.extend([e.strip() for e in ents.split(',') if e.strip()])
        elif hasattr(ents, '__iter__'):
            all_ents.extend([ent_obj.name for ent_obj in ents])
    
    top_entities = sorted(list(set(all_ents)))[:15] # Limit for readability

    # Map labels to indices
    labels = sources + categories + top_entities + sentiments
    label_map = {l: i for i, l in enumerate(labels)}
    
    source_indices = []
    target_indices = []
    values = []
    
    # 1. Source -> Category
    for s in sources:
        for c in categories:
            count = len(sample_df[(sample_df['source'] == s) & (sample_df['category'] == c)])
            if count > 0:
                source_indices.append(label_map[s])
                target_indices.append(label_map[c])
                values.append(count)
                
    # 2. Category -> Entity
    for c in categories:
        for ent in top_entities:
            # Count articles in category c that have entity ent
            count = 0
            for _, row in sample_df[sample_df['category'] == c].iterrows():
                row_ents = []
                if isinstance(row['entities'], str):
                    row_ents = [e.strip() for e in row['entities'].split(',')]
                elif hasattr(row['entities'], '__iter__'):
                    row_ents = [ent_obj.name for ent_obj in row['entities']]
                if ent in row_ents:
                    count += 1
            if count > 0:
                source_indices.append(label_map[c])
                target_indices.append(label_map[ent])
                values.append(count)

    # 3. Entity -> Sentiment
    for ent in top_entities:
        for sent in sentiments:
            count = 0
            for _, row in sample_df[sample_df['sentiment'] == sent].iterrows():
                row_ents = []
                if isinstance(row['entities'], str):
                    row_ents = [e.strip() for e in row['entities'].split(',')]
                elif hasattr(row['entities'], '__iter__'):
                    row_ents = [ent_obj.name for ent_obj in row['entities']]
                if ent in row_ents:
                    count += 1
            if count > 0:
                source_indices.append(label_map[ent])
                target_indices.append(label_map[sent])
                values.append(count)

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

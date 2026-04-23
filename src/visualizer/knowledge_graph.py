# src/visualizer/knowledge_graph.py
import dash_cytoscape as cyto
from dash import html

def create_knowledge_graph(df):
    """
    Create a Strategic Risk-Aware Knowledge Graph for deep intelligence analysis.
    """
    if df.empty or 'entities' not in df.columns:
        return html.Div("No entity data available for graph.", style={'color': '#94a3b8', 'textAlign': 'center', 'padding': '20px'})

    # Use full filtered dataset (cap at 200 for browser performance)
    sample_df = df.head(200).copy()
    
    # Pre-process entities to find "Hubs" (Connectivity Degree)
    entity_to_articles = {}
    for idx, row in sample_df.iterrows():
        if row['entities'] and isinstance(row['entities'], str):
            ents = [e.strip() for e in row['entities'].split(',') if e.strip()]
            for e in ents:
                if e not in entity_to_articles:
                    entity_to_articles[e] = set()
                entity_to_articles[e].add(f"art_{idx}")
        elif hasattr(row['entities'], '__iter__'): # If it's a list of objects
            for ent_obj in row['entities']:
                e = ent_obj.name
                if e not in entity_to_articles:
                    entity_to_articles[e] = set()
                entity_to_articles[e].add(f"art_{idx}")

    elements = []
    seen_nodes = set()

    for idx, row in sample_df.iterrows():
        article_id = f"art_{idx}"
        article_title = (row['title'][:32] + "..") if len(row['title']) > 32 else row['title']
        sentiment = row.get('sentiment', 'Neutral')
        
        # Article Node (Color-coded by Sentiment/Risk)
        if article_id not in seen_nodes:
            elements.append({
                'data': {
                    'id': article_id, 
                    'label': article_title,
                    'sentiment': sentiment
                },
                'classes': sentiment.lower() # 'negative', 'neutral', 'positive'
            })
            seen_nodes.add(article_id)

        # Process Entities
        raw_ents = []
        if isinstance(row['entities'], str):
            raw_ents = [e.strip() for e in row['entities'].split(',') if e.strip()]
        elif hasattr(row['entities'], '__iter__'):
            raw_ents = [ent_obj.name for ent_obj in row['entities']]
            
        for entity in raw_ents:
            entity_id = f"ent_{entity}"
            is_cve = entity.upper().startswith("CVE-")
            degree = len(entity_to_articles.get(entity, []))
            
            # STRATEGIC FILTER: Show CVEs or entities connecting multiple articles
            if not (is_cve or degree > 1):
                continue

            # Entity Node (Sized by Degree)
            if entity_id not in seen_nodes:
                elements.append({
                    'data': {
                        'id': entity_id, 
                        'label': entity,
                        'degree': degree,
                        'size': 30 + (degree * 10) # Dynamic scaling
                    },
                    'classes': 'cve' if is_cve else 'entity'
                })
                seen_nodes.add(entity_id)

            # Relationship Edge
            elements.append({
                'data': {'source': entity_id, 'target': article_id}
            })

    return cyto.Cytoscape(
        id='knowledge-graph',
        layout={
            'name': 'cose',
            'idealEdgeLength': 120,
            'nodeOverlap': 40,
            'refresh': 20,
            'fit': True,
            'padding': 40,
            'randomize': False,
            'componentSpacing': 120,
            'nodeRepulsion': 600000,
            'edgeElasticity': 100,
            'nestingFactor': 5,
            'gravity': 70,
            'numIter': 1000,
            'initialTemp': 250,
            'coolingFactor': 0.95,
            'minTemp': 1.0
        },
        style={'width': '100%', 'height': '600px', 'backgroundColor': '#0a0c10'},
        elements=elements,
        stylesheet=[
            {
                'selector': 'node',
                'style': {
                    'label': 'data(label)',
                    'color': '#e0e6ed',
                    'font-size': '11px',
                    'text-valign': 'top',
                    'text-halign': 'center',
                    'text-margin-y': '-10px',
                    'font-family': 'Inter, sans-serif'
                }
            },
            {
                'selector': '.negative', # High Risk
                'style': {
                    'background-color': '#11141d',
                    'line-color': '#ff3e3e',
                    'border-width': 3,
                    'border-color': '#ff3e3e',
                    'shape': 'round-rectangle',
                    'width': '130px', 'height': '45px',
                    'text-valign': 'center', 'text-wrap': 'wrap', 'text-max-width': '120px'
                }
            },
            {
                'selector': '.neutral',
                'style': {
                    'background-color': '#11141d',
                    'line-color': '#94a3b8',
                    'border-width': 2,
                    'border-color': '#94a3b8',
                    'shape': 'round-rectangle',
                    'width': '130px', 'height': '45px',
                    'text-valign': 'center', 'text-wrap': 'wrap', 'text-max-width': '120px'
                }
            },
            {
                'selector': '.positive', # Low Risk
                'style': {
                    'background-color': '#11141d',
                    'line-color': '#00ff9d',
                    'border-width': 2,
                    'border-color': '#00ff9d',
                    'shape': 'round-rectangle',
                    'width': '130px', 'height': '45px',
                    'text-valign': 'center', 'text-wrap': 'wrap', 'text-max-width': '120px'
                }
            },
            {
                'selector': '.entity',
                'style': {
                    'background-color': '#00f2ff',
                    'opacity': 0.8,
                    'shape': 'ellipse',
                    'width': 'data(size)',
                    'height': 'data(size)'
                }
            },
            {
                'selector': '.cve',
                'style': {
                    'background-color': '#ffa500',
                    'shape': 'diamond',
                    'width': '50px',
                    'height': '50px',
                    'border-width': 2,
                    'border-color': '#ff3e3e'
                }
            },
            {
                'selector': 'edge',
                'style': {
                    'line-color': '#1e293b',
                    'width': 1.5,
                    'curve-style': 'bezier',
                    'target-arrow-shape': 'triangle',
                    'target-arrow-color': '#1e293b',
                    'opacity': 0.4
                }
            }
        ]
    )

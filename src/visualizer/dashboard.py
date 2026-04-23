# src/visualizer/dashboard.py
import pandas as pd
from dash import Dash, dcc, html, Input, Output, State, dash_table, callback_context, no_update
import plotly.express as px
import plotly.graph_objects as go
from src.database import SessionLocal, News, AlertHistory
from sqlalchemy.orm import joinedload
from src.scraper.scrape_news import scrape_news
from src.visualizer.knowledge_graph import create_knowledge_graph
from src.visualizer.sankey_flow import create_sankey_flow
from src.processor.evaluate import run_evaluation
import datetime
import time

# ---------------------------------------
# Load news data from DB
# ---------------------------------------
def load_news_data():
    db = SessionLocal()
    news_list = db.query(News).options(joinedload(News.entities)).all()
    data = {
        "title": [n.title for n in news_list],
        "summary": [n.content[:200] + "..." for n in news_list],
        "content": [n.content for n in news_list],
        "category": [n.category for n in news_list],
        "date": [n.date for n in news_list],
        "source": [n.source for n in news_list],
        "full_article": [f"[View Full]({n.url})" for n in news_list],
        "sentiment": [n.sentiment for n in news_list],
        "entities": [", ".join([e.name for e in n.entities]) for n in news_list],
        "ai_summary": [n.ai_summary if n.ai_summary else (n.content[:200] + "...") for n in news_list],
        "latitude": [float(n.latitude) if n.latitude and n.latitude != 'None' else None for n in news_list],
        "longitude": [float(n.longitude) if n.longitude and n.longitude != 'None' else None for n in news_list],
        "location_name": [n.location_name for n in news_list]
    }
    df = pd.DataFrame(data)
    db.close()
    return df

# ---------------------------------------
# Figures
# ---------------------------------------
def create_category_pie(df):
    if df.empty:
        return px.pie(title="No data available")
    counts = df['category'].value_counts()
    fig = px.pie(
        counts,
        values=counts.values,
        names=counts.index,
        hole=0.4,
        template="plotly_dark"
    )
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(t=10, b=10, l=10, r=10),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
    )
    return fig

def create_top5_category_bar(df):
    if df.empty:
        return px.bar(title="No data available")
    counts = df['category'].value_counts().head(5)
    fig = px.bar(
        counts,
        x=counts.index,
        y=counts.values,
        template="plotly_dark",
        color=counts.index,
        color_discrete_sequence=['#00f2ff', '#00ff9d', '#ff3e3e', '#94a3b8', '#1e293b']
    )
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(t=10, b=10, l=10, r=10),
        xaxis_title="",
        yaxis_title="",
        showlegend=False
    )
    fig.update_yaxes(showgrid=True, gridcolor='#1e293b')
    return fig

def create_articles_trend(df):
    if df.empty:
        return px.line(title="No data available")
    df_grouped = df.groupby('date').size().reset_index(name='count')
    fig = px.line(
        df_grouped,
        x='date',
        y='count',
        template="plotly_dark"
    )
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(t=10, b=10, l=10, r=10),
        xaxis_title="",
        yaxis_title=""
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor='#1e293b')
    fig.update_traces(line_color='#00f2ff', line_width=2)
    return fig

def create_category_radar(df):
    if df.empty:
        fig = go.Figure()
        fig.update_layout(title="No data available", template="plotly_dark")
        return fig
    counts = df['category'].value_counts()
    categories = counts.index.tolist()
    values = counts.values.tolist()
    categories += categories[:1]
    values = list(values) + values[:1]

    fig = go.Figure(
        data=[go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name='Category Distribution',
            line_color='#00CC96'
        )]
    )
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, color='white')),
        title="Radar Chart of Cybersecurity Categories",
        title_font_size=22,
        template="plotly_dark"
    )
    return fig

# -----------------------------
# Sentiment Figures
# -----------------------------
def create_sentiment_pie(df):
    if df.empty or 'sentiment' not in df.columns:
        return px.pie(title="No data available")
    
    # Convert value_counts to DataFrame
    counts = df['sentiment'].value_counts().reset_index()
    counts.columns = ['sentiment', 'count']
    
    fig = px.pie(
        counts,
        values='count',
        names='sentiment',
        hole=0.4,
        color='sentiment',
        color_discrete_map={
            "Positive": "#00ff9d",
            "Neutral": "#94a3b8",
            "Negative": "#ff3e3e"
        },
        template="plotly_dark"
    )
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(t=10, b=10, l=10, r=10),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
    )
    return fig

    fig.update_layout(
        title="News Sentiment Over Time (Stacked Area, 7-day MA)",
        template="plotly_dark",
        title_font_size=22,
        xaxis_title="Date",
        yaxis_title="Number of Articles",
        legend_title="Sentiment"
    )
    return fig

def create_sentiment_trend(df):
    if df.empty or 'sentiment' not in df.columns:
        return px.line(title="No data available")
    df_grouped = df.groupby(['date','sentiment']).size().reset_index(name='count')
    df_pivot = df_grouped.pivot(index='date', columns='sentiment', values='count').fillna(0)
    # Ensure all sentiments are present for consistent coloring
    for s in ["Positive", "Neutral", "Negative"]:
        if s not in df_pivot.columns:
            df_pivot[s] = 0
            
    df_pivot = df_pivot.sort_index()
    df_ma = df_pivot.rolling(7, min_periods=1).mean()

    fig = go.Figure()
    for sentiment, color in {"Positive":"#00CC96", "Neutral":"#FFA500", "Negative":"#EF553B"}.items():
        if sentiment in df_ma.columns:
            fig.add_trace(go.Scatter(
                x=df_ma.index,
                y=df_ma[sentiment],
                mode='lines+markers',
                name=sentiment,
                line=dict(color=color),
                stackgroup='one'
            ))

    fig.update_layout(
        title="News Sentiment Over Time (Stacked Area, 7-day MA)",
        template="plotly_dark",
        title_font_size=22,
        xaxis_title="Date",
        yaxis_title="Number of Articles",
        legend_title="Sentiment"
    )
    return fig

def create_threat_map(df, selected_region='global'):
    # Region view settings (lat, lon, zoom)
    region_map = {
        'global': {'center': {'lat': 20, 'lon': 0}, 'zoom': 1},
        'na': {'center': {'lat': 45, 'lon': -100}, 'zoom': 3},
        'eu': {'center': {'lat': 50, 'lon': 15}, 'zoom': 3.5},
        'asia': {'center': {'lat': 35, 'lon': 110}, 'zoom': 2.5},
        'mea': {'center': {'lat': 15, 'lon': 30}, 'zoom': 2.5},
        'latam': {'center': {'lat': -15, 'lon': -60}, 'zoom': 2.5}
    }
    
    view = region_map.get(selected_region, region_map['global'])

    if df.empty or 'latitude' not in df.columns:
        fig = px.scatter_map(lat=[0], lon=[0], zoom=view['zoom'], center=view['center'])
        fig.update_layout(
            map_style="carto-darkmatter",
            template="plotly_dark",
            title="No location data available"
        )
        return fig
    
    # Filter only rows with valid lat/lon
    map_df = df.dropna(subset=['latitude', 'longitude'])
    
    if map_df.empty:
        fig = px.scatter_map(lat=[0], lon=[0], zoom=view['zoom'], center=view['center'])
        fig.update_layout(
            map_style="carto-darkmatter",
            template="plotly_dark",
            title="No location data available"
        )
        return fig

    fig = px.scatter_map(
        map_df,
        lat="latitude",
        lon="longitude",
        hover_name="title",
        color="sentiment",
        color_discrete_map={
            "Negative": "#ff3e3e",
            "Neutral": "#94a3b8",
            "Positive": "#00ff9d"
        },
        hover_data={
            "latitude": False,
            "longitude": False,
            "location_name": True,
            "category": True,
            "source": True,
            "date": True
        },
        zoom=view['zoom'],
        center=view['center'],
        map_style="carto-darkmatter",
        template="plotly_dark"
    )
    
    # Enable point clustering for better SOC aesthetic
    fig.update_traces(cluster=dict(enabled=True))
    
    fig.update_layout(
        margin=dict(t=0, b=0, l=0, r=0),
        title_font_size=22,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    return fig

# ---------------------------------------
# Dashboard
# ---------------------------------------
def run_dashboard():
    df = load_news_data()
    if df.empty:
        df = pd.DataFrame(columns=["title","summary","content","category","date","source","full_article","sentiment"])
    df['date'] = pd.to_datetime(df['date'])

    app = Dash(__name__, suppress_callback_exceptions=True)
    categories = sorted(df['category'].unique())

    card_style = {
        'backgroundColor': '#1f2c56',
        'padding': '20px',
        'borderRadius': '10px',
        'marginBottom': '20px',
        'boxShadow': '2px 2px 10px rgba(0,0,0,0.5)',
        'color': 'white'
    }

    # -----------------------------
    # Initial data for range
    # -----------------------------
    df = load_news_data()
    if df.empty:
        start_date = datetime.date.today()
        end_date = datetime.date.today()
    else:
        start_date = df['date'].min()
        end_date = df['date'].max()

    # -----------------------------
    # Premium SOC CSS & Layout
    # -----------------------------
    app.index_string = '''
    <!DOCTYPE html>
    <html>
        <head>
            {%metas%}
            <title>SHIELD // Cyber Intelligence Hub</title>
            {%favicon%}
            {%css%}
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
            <style>
                :root {
                    --bg-dark: #0a0c10;
                    --card-bg: #11141d;
                    --accent-cyan: #00f2ff;
                    --accent-green: #00ff9d;
                    --accent-red: #ff3e3e;
                    --text-main: #e0e6ed;
                    --text-muted: #94a3b8;
                    --border: #1e293b;
                }
                body {
                    margin: 0;
                    background-color: var(--bg-dark);
                    font-family: 'Inter', sans-serif;
                    color: var(--text-main);
                    overflow-x: hidden;
                }
                .dashboard-container {
                    padding: 20px;
                    display: grid;
                    grid-template-columns: repeat(12, 1fr);
                    grid-gap: 20px;
                }
                .header {
                    grid-column: span 12;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    border-bottom: 1px solid var(--border);
                    padding-bottom: 15px;
                    margin-bottom: 10px;
                }
                .header h1 {
                    margin: 0;
                    font-size: 1.5rem;
                    text-transform: uppercase;
                    letter-spacing: 2px;
                    background: linear-gradient(90deg, var(--accent-cyan), var(--accent-green));
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                }
                .soc-card {
                    background-color: var(--card-bg);
                    border: 1px solid var(--border);
                    border-radius: 4px;
                    padding: 15px;
                    position: relative;
                    overflow: hidden;
                }
                .soc-card::before {
                    content: "";
                    position: absolute;
                    top: 0; left: 0;
                    width: 2px; height: 100%;
                    background: var(--accent-cyan);
                    opacity: 0.5;
                }
                .kpi-card {
                    grid-column: span 3;
                    text-align: left;
                    display: flex;
                    flex-direction: column;
                }
                .kpi-card .label {
                    font-size: 0.75rem;
                    text-transform: uppercase;
                    color: var(--text-muted);
                    font-weight: 600;
                    margin-bottom: 5px;
                }
                .kpi-card .value {
                    font-family: 'JetBrains Mono', monospace;
                    font-size: 1.8rem;
                    color: var(--text-main);
                }
                .filter-bar {
                    grid-column: span 12;
                    display: flex;
                    gap: 15px;
                    align-items: center;
                    background: #161b22;
                    padding: 10px 20px;
                    border-radius: 4px;
                    border: 1px solid var(--border);
                }
                .chart-container {
                    grid-column: span 6;
                }
                .full-width {
                    grid-column: span 12;
                }
                .three-col {
                    grid-column: span 4;
                }
                .live-feed {
                    font-family: 'JetBrains Mono', monospace;
                    font-size: 0.85rem;
                }
                /* Scrollbar */
                ::-webkit-scrollbar { width: 6px; }
                ::-webkit-scrollbar-track { background: var(--bg-dark); }
                ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 10px; }
                
                /* Custom Dropdown Overrides */
                .Select-control, .Select-menu-outer {
                    background-color: #1a2336 !important;
                    color: white !important;
                    border: 1px solid var(--border) !important;
                }
                .Select-value-label { color: white !important; }
                
                /* DatePicker Styling */
                .DateInput_input {
                    background-color: #1a2336 !important;
                    color: white !important;
                    border: 1px solid var(--border) !important;
                    font-family: 'JetBrains Mono', monospace !important;
                    font-size: 13px !important;
                }
                .briefing-panel {
                    background-color: #0d1117;
                    border: 1px solid #30363d;
                    padding: 20px;
                    border-radius: 5px;
                    min-height: 200px;
                    color: #e6edf3;
                    margin-top: 10px;
                }
                .briefing-label {
                    color: var(--accent-cyan);
                    font-size: 0.7rem;
                    font-weight: bold;
                    margin-bottom: 5px;
                    text-transform: uppercase;
                }
                .briefing-title {
                    font-size: 1.2rem;
                    margin-bottom: 15px;
                    color: white;
                }
            </style>
        </head>
        <body>
            {%app_entry%}
            <footer>
                {%config%}
                {%scripts%}
                {%renderer%}
            </footer>
        </body>
    </html>
    '''

    app.layout = html.Div(className='dashboard-container', children=[
        # Header
        html.Div(className='header', children=[
            html.Div([
                html.H1("CYBER INTELLIGENCE HUB"),
                html.Small("CIH //V3.0", style={'color': 'var(--text-muted)'})
            ]),
            html.Div(id='last-updated', className='live-feed', style={'color': 'var(--accent-green)'})
        ]),

        # KPIs
        html.Div(className='soc-card kpi-card', children=[
            html.Div("Total Intelligence", className='label'),
            html.Div(id='total-articles', className='value')
        ]),
        html.Div(className='soc-card kpi-card', children=[
            html.Div("Active Categories", className='label'),
            html.Div(id='total-categories', className='value')
        ]),
        html.Div(className='soc-card kpi-card', children=[
            html.Div("Primary Threat", className='label'),
            html.Div(id='top-category', className='value', style={'fontSize':'1.2rem', 'paddingTop':'10px'})
        ]),
        html.Div(className='soc-card kpi-card', children=[
            html.Div("Monitor Status", className='label'),
            html.Div("SYSTEM ONLINE", className='value', style={'color': 'var(--accent-green)', 'fontSize':'1.2rem', 'paddingTop':'10px'})
        ]),

        # Filters Bar
        html.Div(className='filter-bar', children=[
            html.Div([
                html.Span("🔍 SEARCH", style={'fontSize':'0.7rem', 'fontWeight':'bold', 'marginRight':'10px'}),
                dcc.Input(id='search-input', type='text', placeholder='Enter term...', 
                          style={'backgroundColor':'#0d1117', 'border':'1px solid #30363d', 'color':'white', 'padding':'5px 10px', 'borderRadius':'3px', 'width':'250px'})
            ]),
            html.Div([
                html.Span("📂 CATEGORY", style={'fontSize':'0.7rem', 'fontWeight':'bold', 'marginRight':'10px'}),
                dcc.Dropdown(id='category-dropdown', options=[{'label': c, 'value': c} for c in categories], 
                             placeholder="ALL", style={'width':'150px', 'display':'inline-block'})
            ]),
            html.Div([
                html.Span("🌍 REGION", style={'fontSize':'0.7rem', 'fontWeight':'bold', 'marginRight':'10px'}),
                dcc.Dropdown(id='region-dropdown', options=[
                    {'label': 'GLOBAL', 'value': 'global'},
                    {'label': 'NORTH AMERICA', 'value': 'na'},
                    {'label': 'EUROPE', 'value': 'eu'},
                    {'label': 'ASIA', 'value': 'asia'},
                    {'label': 'MEA', 'value': 'mea'},
                    {'label': 'LATAM', 'value': 'latam'}
                ], value='global', style={'width':'160px', 'display':'inline-block'})
            ]),
            html.Div([
                html.Span("📅 RANGE", style={'fontSize':'0.7rem', 'fontWeight':'bold', 'marginRight':'10px'}),
                dcc.DatePickerRange(id='date-picker', start_date=start_date, end_date=end_date, 
                                     display_format='YYYY-MM-DD', style={'display':'inline-block'})
            ]),
            html.Button("RUN SCRAPE", id='scrape-button', n_clicks=0, 
                        style={'marginLeft':'auto', 'backgroundColor':'var(--accent-cyan)', 'color':'black', 'border':'none', 'padding':'7px 15px', 'fontWeight':'bold', 'borderRadius':'3px', 'cursor':'pointer'}),
            html.Div(id='scrape-output', style={'fontSize':'0.7rem', 'color':'var(--text-muted)'})
        ]),

        # Main Visualization Grid
        html.Div(className='soc-card chart-container', children=[
            html.H3("THREAT DISTRIBUTION", style={'fontSize':'0.9rem', 'marginBottom':'15px', 'borderBottom':'1px solid #1e293b'}),
            dcc.Graph(id='pie-chart', config={'displayModeBar': False})
        ]),
        html.Div(className='soc-card chart-container', children=[
            html.H3("INCIDENT TREND LINE", style={'fontSize':'0.9rem', 'marginBottom':'15px', 'borderBottom':'1px solid #1e293b'}),
            dcc.Graph(id='trend-chart', config={'displayModeBar': False})
        ]),

        html.Div(className='soc-card three-col', children=[
            html.H3("SENTIMENT ANALYSIS", style={'fontSize':'0.9rem', 'marginBottom':'15px', 'borderBottom':'1px solid #1e293b'}),
            dcc.Graph(id='sentiment-pie-chart', config={'displayModeBar': False})
        ]),
        html.Div(className='soc-card three-col', children=[
            html.H3("INTELLIGENCE HUB STATUS", style={'fontSize':'0.9rem', 'marginBottom':'15px', 'borderBottom':'1px solid #1e293b'}),
            html.Div([
                html.Div("CORE ENGINE: ACTIVE", style={'color':'var(--accent-green)', 'fontSize':'0.8rem', 'marginBottom':'10px'}),
                html.Div("NER MODEL: LOADED", style={'color':'var(--accent-cyan)', 'fontSize':'0.8rem', 'marginBottom':'10px'}),
                html.Div("SITUATION AWARENESS: CALIBRATED", style={'color':'var(--text-main)', 'fontSize':'0.8rem'})
            ], style={'padding':'20px', 'textAlign':'center'})
        ]),
        html.Div(className='soc-card three-col', children=[
            html.H3("VECTOR ANALYSIS (RADAR)", style={'fontSize':'0.9rem', 'marginBottom':'15px', 'borderBottom':'1px solid #1e293b'}),
            dcc.Graph(id='radar-chart', config={'displayModeBar': False})
        ]),

        # Evaluation & Alerts Row
        html.Div(id='evaluation-report', className='soc-card chart-container'),
        html.Div(className='soc-card chart-container', children=[
            html.H3("LIVE ALERT STREAM", style={'fontSize':'0.9rem', 'marginBottom':'15px', 'borderBottom':'1px solid #1e293b', 'color':'var(--accent-red)'}),
            html.Div(id='alerts-feed-container', className='live-feed', style={'maxHeight':'300px', 'overflowY':'auto'})
        ]),

        # Geospatial Map (Primary Awareness)
        html.Div(className='soc-card full-width', children=[
            html.H3("GLOBAL GEOSPATIAL THREATS // INCIDENT MAPPING", style={'fontSize':'0.9rem', 'marginBottom':'15px', 'borderBottom':'1px solid #1e293b'}),
            dcc.Graph(id='threat-map', config={'displayModeBar': False}, style={'height':'600px'})
        ]),

        # Advanced Intelligence Analysis
        html.Div(className='soc-card full-width', children=[
            html.H3("DATA ANALYSIS", style={'fontSize':'0.9rem', 'marginBottom':'15px', 'borderBottom':'1px solid #1e293b'}),
            dcc.Tabs(id='intel-tabs', value='graph', children=[
                dcc.Tab(label='KNOWLEDGE GRAPH', value='graph', style={'backgroundColor':'#0d1117', 'color':'#94a3b8', 'border':'none'}, selected_style={'backgroundColor':'#161b22', 'color':'var(--accent-cyan)', 'borderTop':'2px solid var(--accent-cyan)'}),
                dcc.Tab(label='SANKEY FLOW', value='sankey', style={'backgroundColor':'#0d1117', 'color':'#94a3b8', 'border':'none'}, selected_style={'backgroundColor':'#161b22', 'color':'var(--accent-cyan)', 'borderTop':'2px solid var(--accent-cyan)'}),
            ]),
            html.Div(id='intel-container', style={'height':'600px', 'marginTop':'20px'})
        ]),

        # Intelligence Briefing Panel (Details-on-Demand)
        html.Div(className='soc-card full-width', children=[
            html.H3("BRIEFING SAMPLE", style={'fontSize':'0.9rem', 'marginBottom':'15px', 'borderBottom':'1px solid #1e293b', 'color':'var(--accent-cyan)'}),
            html.Div(id='briefing-panel-content', className='briefing-panel', children=[
                html.Div("Select a node or incident on the graphs above to view detailed intelligence briefing.", 
                         style={'color': 'var(--text-muted)', 'textAlign': 'center', 'paddingTop': '80px'})
            ])
        ]),

        # Data Table
        html.Div(className='soc-card full-width', children=[
            html.H3("RAW INTELLIGENCE LOGS", style={'fontSize':'0.9rem', 'marginBottom':'15px', 'borderBottom':'1px solid #1e293b'}),
            dash_table.DataTable(
                id='articles-table',
                columns=[
                    {"name":"DATE","id":"date"},
                    {"name":"CAT","id":"category"},
                    {"name":"TITLE","id":"title"},
                    {"name":"ENTITIES","id":"entities"},
                    {"name":"AI SUMMARY","id":"ai_summary"}
                ],
                style_header={'backgroundColor': '#161b22', 'color': 'var(--accent-cyan)', 'fontWeight': 'bold', 'border': '1px solid #30363d'},
                style_cell={'backgroundColor': '#0d1117', 'color': 'var(--text-main)', 'textAlign': 'left', 'fontFamily': 'JetBrains Mono', 'fontSize': '12px', 'border': '1px solid #30363d'},
                page_size=10,
                style_table={'overflowX':'auto'},
                markdown_options={"link_target":"_blank"}
            )
        ]),

        dcc.Interval(id='interval-component', interval=5*60*1000, n_intervals=0),
        dcc.Store(id='graph-node-store', data=None)
    ])

    # ---------------------------------------
    # Callback
    # ---------------------------------------
    @app.callback(
        [
            Output('pie-chart','figure'),
            Output('trend-chart','figure'),
            Output('radar-chart','figure'),
            Output('sentiment-pie-chart','figure'),
            Output('threat-map', 'figure'),
            Output('articles-table','data'),
            Output('last-updated','children'),
            Output('total-articles','children'),
            Output('total-categories','children'),
            Output('top-category','children'),
            Output('scrape-output', 'children'),
            Output('intel-container', 'children'),
            Output('alerts-feed-container', 'children'),
            Output('evaluation-report', 'children')
        ],
        [
            Input('category-dropdown','value'),
            Input('region-dropdown','value'),
            Input('date-picker','start_date'),
            Input('date-picker','end_date'),
            Input('search-input', 'value'),
            Input('interval-component','n_intervals'),
            Input('scrape-button', 'n_clicks'),
            Input('intel-tabs', 'value')
        ]
    )
    def update_dashboard(selected_category, selected_region, start_date, end_date, search_query, n_intervals, n_clicks, current_tab):
        # Handle scraping if button clicked
        ctx = callback_context
        triggered_ids = [t['prop_id'].split('.')[0] for t in ctx.triggered]
        scrape_msg = ""
        
        if 'scrape-button' in triggered_ids and n_clicks > 0:
            try:
                scrape_news()
                scrape_msg = f"✅ Scraping complete at {datetime.datetime.now().strftime('%H:%M:%S')}"
            except Exception as e:
                scrape_msg = f"❌ Scraping failed: {str(e)}"

        # Load News
        df = load_news_data()
        
        # KPIs (Initialize for safety)
        last_updated = f"Last Updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        total_articles = "Total Articles: 0"
        total_categories = "Total Categories: 0"
        top_category = "Top Category: -"

        if df.empty:
            empty_fig = px.pie(title="No data available")
            return empty_fig, empty_fig, empty_fig, empty_fig, create_threat_map(pd.DataFrame(), selected_region), [], last_updated, "0", "0", "-", scrape_msg, None, [], []

        df['date'] = pd.to_datetime(df['date'])

        # Filtering
        start = pd.to_datetime(start_date) if start_date else df['date'].min()
        end = pd.to_datetime(end_date) if end_date else df['date'].max()
        
        mask = (df['date'] >= start) & (df['date'] <= end)
        if selected_category:
            mask = mask & (df['category'] == selected_category)
        
        if search_query and len(search_query) > 2:
            sq = search_query.lower()
            mask = mask & (df['title'].str.lower().str.contains(sq) | 
                          df['content'].str.lower().str.contains(sq) |
                          df['ai_summary'].str.lower().str.contains(sq))
            
        filtered_df = df[mask]

        # Load Alerts (Task 7)
        db = SessionLocal()
        alerts_list = db.query(AlertHistory).options(joinedload(AlertHistory.article)).order_by(AlertHistory.id.desc()).limit(8).all()
        alert_elements = []
        for a in alerts_list:
            alert_elements.append(html.Div(style={
                'padding':'10px','borderBottom':'1px solid #1e293b','backgroundColor':'#11141d','borderRadius':'4px','marginBottom':'8px', 'borderLeft':'2px solid var(--accent-red)'
            }, children=[
                html.Div([
                    html.B(f"LIVE // {a.rule.name}", style={'color':'var(--accent-red)', 'fontSize':'0.7rem', 'letterSpacing':'1px'}),
                    html.Span(f" // {a.timestamp}", style={'color':'var(--text-muted)', 'fontSize':'0.7rem', 'float':'right'})
                ]),
                html.Div(f"{a.article.title}", style={'fontSize':'0.85rem', 'marginTop':'5px', 'color':'var(--text-main)'})
            ]))
        if not alert_elements:
            alert_elements = [html.Div("No active alerts triggered yet.", style={'padding':'10px','color':'#AAAAAA'})]

        report = run_evaluation(filtered_df)
        eval_ui = []
        if report and "metrics" in report:
            m = report["metrics"]
            eval_ui = [
                html.H3("INTELLIGENCE METRICS", style={'fontSize':'0.9rem', 'marginBottom':'15px', 'borderBottom':'1px solid #1e293b'}),
                html.Div(style={'display':'flex', 'justifyContent':'space-around', 'padding':'10px'}, children=[
                    html.Div([html.Small("DENSITY", style={'color':'var(--text-muted)', 'fontSize':'0.7rem'}), html.H4(m['avg_entity_density'], style={'color':'var(--accent-cyan)', 'margin':'0'})]),
                    html.Div([html.Small("COVERAGE", style={'color':'var(--text-muted)', 'fontSize':'0.7rem'}), html.H4(m['ner_coverage'], style={'color':'var(--accent-cyan)', 'margin':'0'})]),
                    html.Div([html.Small("COMPRESSION", style={'color':'var(--text-muted)', 'fontSize':'0.7rem'}), html.H4(m['compression_efficiency'], style={'color':'var(--accent-cyan)', 'margin':'0'})]),
                    html.Div([html.Small("NODES", style={'color':'var(--text-muted)', 'fontSize':'0.7rem'}), html.H4(m['total_intelligence_nodes'], style={'color':'var(--accent-cyan)', 'margin':'0'})])
                ])
            ]
        # KPIs
        last_updated = f"Last Updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        total_articles = f"Total Articles: {len(filtered_df)}"
        total_categories = f"Total Categories: {filtered_df['category'].nunique()}"
        top_cat_val = filtered_df['category'].value_counts().idxmax() if not filtered_df.empty else "-"
        top_category = f"Top Category: {top_cat_val}"

        # Intelligence View Implementation (Task 16)
        if current_tab == 'sankey':
            intel_view = create_sankey_flow(filtered_df)
        else:
            intel_view = create_knowledge_graph(filtered_df)

        db.close()

        return (
            create_category_pie(filtered_df),
            create_articles_trend(filtered_df),
            create_category_radar(filtered_df),
            create_sentiment_pie(filtered_df),
            create_threat_map(filtered_df, selected_region),
            filtered_df.to_dict('records'),
            last_updated,
            total_articles,
            total_categories,
            top_category,
            scrape_msg,
            intel_view,
            alert_elements,
            eval_ui
        )

    # Intelligence Briefing Callback (Task 16)
    # Uses only static layout IDs to avoid ReferenceError
    @app.callback(
        Output('briefing-panel-content', 'children'),
        [
            Input('threat-map', 'clickData'),
            Input('articles-table', 'active_cell')
        ],
        [
            State('articles-table', 'data')
        ]
    )
    def display_briefing(map_click, table_cell, table_data):
        ctx = callback_context
        if not ctx.triggered:
            return html.Div("Click a point on the Threat Map or a row in the Intelligence Logs to load a full briefing.",
                             style={'color': 'var(--text-muted)', 'textAlign': 'center', 'paddingTop': '40px'})

        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

        # 1. From Threat Map
        if trigger_id == 'threat-map' and map_click:
            point_title = map_click['points'][0].get('hovertext', '')
            df = load_news_data()
            matches = df[df['title'] == point_title]
            if not matches.empty:
                article = matches.iloc[0]
                return html.Div([
                    html.Div("GEOSPATIAL INTELLIGENCE BRIEF", className='briefing-label'),
                    html.Div(article['title'], className='briefing-title'),
                    html.Hr(style={'borderColor':'#1e293b'}),
                    html.Div(style={'display':'flex', 'gap':'30px', 'marginBottom':'15px'}, children=[
                        html.Div([html.Div("CATEGORY", className='briefing-label'), html.Div(article['category'], style={'color':'var(--accent-cyan)'})]),
                        html.Div([html.Div("SENTIMENT", className='briefing-label'), html.Div(article['sentiment'], style={'color': '#ff3e3e' if article['sentiment']=='Negative' else '#00ff9d'})]),
                        html.Div([html.Div("SOURCE", className='briefing-label'), html.Div(article['source'], style={'color':'var(--text-muted)'})]),
                    ]),
                    html.Div("AI GENERATED SUMMARY", className='briefing-label'),
                    html.P(article['ai_summary'], style={'lineHeight':'1.8', 'fontSize':'0.95rem'}),
                    html.Div("DETECTED ENTITIES", className='briefing-label'),
                    html.P(article['entities'], style={'fontSize':'0.8rem', 'color':'var(--text-muted)'}),
                ])

        # 2. From Table
        if trigger_id == 'articles-table' and table_cell and table_data:
            row_idx = table_cell['row']
            article = table_data[row_idx]
            return html.Div([
                html.Div("LOG ENTRY INTELLIGENCE BRIEFING", className='briefing-label'),
                html.Div(article['title'], className='briefing-title'),
                html.Hr(style={'borderColor':'#1e293b'}),
                html.Div(style={'display':'flex', 'gap':'30px', 'marginBottom':'15px'}, children=[
                    html.Div([html.Div("CATEGORY", className='briefing-label'), html.Div(article.get('category',''), style={'color':'var(--accent-cyan)'})]),
                    html.Div([html.Div("SENTIMENT", className='briefing-label'), html.Div(article.get('sentiment',''), style={'color': '#ff3e3e' if article.get('sentiment')=='Negative' else '#00ff9d'})]),
                    html.Div([html.Div("DATE", className='briefing-label'), html.Div(article.get('date',''), style={'color':'var(--text-muted)'})]),
                ]),
                html.Div("AI GENERATED SUMMARY", className='briefing-label'),
                html.P(article.get('ai_summary', 'No summary available.'), style={'lineHeight':'1.8', 'fontSize':'0.95rem'}),
                html.Div("DETECTED ENTITIES", className='briefing-label'),
                html.P(article.get('entities', 'None'), style={'fontSize':'0.8rem', 'color':'var(--text-muted)'}),
            ])

        return no_update


    app.run(debug=True, port=8050)

if __name__ == "__main__":
    from src.database import init_db
    init_db()
    run_dashboard()

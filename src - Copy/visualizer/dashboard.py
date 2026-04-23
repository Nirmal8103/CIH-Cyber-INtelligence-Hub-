# src/visualizer/dashboard.py
import pandas as pd
from dash import Dash, dcc, html, Input, Output, dash_table
import plotly.express as px
import plotly.graph_objects as go
from src.database import SessionLocal, News
import datetime

# ---------------------------------------
# Default date range: current month
# ---------------------------------------
today = datetime.date.today()
first_day = today.replace(day=1)
last_day = (today.replace(day=28) + datetime.timedelta(days=4)).replace(day=1) - datetime.timedelta(days=1)

# ---------------------------------------
# Load news data from DB
# ---------------------------------------
def load_news_data():
    db = SessionLocal()
    news_list = db.query(News).all()
    db.close()
    data = {
        "title": [n.title for n in news_list],
        "summary": [n.content[:200] + "..." for n in news_list],
        "content": [n.content for n in news_list],
        "category": [n.category for n in news_list],
        "date": [n.date for n in news_list],
        "source": [n.source for n in news_list],
        "full_article": [f"[View Full]({n.url})" for n in news_list],
        "sentiment": [n.sentiment for n in news_list]
    }
    df = pd.DataFrame(data)
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
        title="Cybersecurity News by Category",
        color_discrete_sequence=px.colors.qualitative.Vivid,
        template="plotly_dark"
    )
    fig.update_layout(title_font_size=22)
    return fig

def create_top5_category_bar(df):
    if df.empty:
        return px.bar(title="No data available")
    counts = df['category'].value_counts().head(5)
    fig = px.bar(
        counts,
        x=counts.index,
        y=counts.values,
        title="Top 5 Categories",
        text=counts.values,
        template="plotly_dark",
        color=counts.index,
        color_discrete_sequence=px.colors.qualitative.Vivid
    )
    fig.update_traces(textposition='auto')
    fig.update_layout(title_font_size=22, showlegend=False)
    return fig

def create_articles_trend(df):
    if df.empty:
        return px.line(title="No data available")
    df_grouped = df.groupby('date').size().reset_index(name='count')
    fig = px.line(
        df_grouped,
        x='date',
        y='count',
        title="Number of Articles Over Time",
        markers=True,
        template="plotly_dark"
    )
    fig.update_layout(title_font_size=22)
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
        title="News Sentiment Distribution",
        color='sentiment',
        color_discrete_map={
            "Positive": "#00CC96",  # green
            "Neutral": "#FFA500",   # orange
            "Negative": "#EF553B"   # red
        },
        template="plotly_dark"
    )
    fig.update_layout(title_font_size=22)
    return fig

def create_sentiment_trend(df):
    if df.empty or 'sentiment' not in df.columns:
        return px.line(title="No data available")
    df_grouped = df.groupby(['date','sentiment']).size().reset_index(name='count')
    df_pivot = df_grouped.pivot(index='date', columns='sentiment', values='count').fillna(0)
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

# ---------------------------------------
# Dashboard
# ---------------------------------------
def run_dashboard():
    df = load_news_data()
    if df.empty:
        df = pd.DataFrame(columns=["title","summary","content","category","date","source","full_article","sentiment"])
    df['date'] = pd.to_datetime(df['date'])

    app = Dash(__name__)
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
    # Layout
    # -----------------------------
    app.layout = html.Div(
        style={'fontFamily': 'Arial, sans-serif', 'backgroundColor': '#121212', 'color': 'white', 'padding': '20px'},
        children=[

            html.H1("Cybersecurity News Dashboard",
                    style={'textAlign': 'center', 'marginBottom': '40px', 'color': '#00CC96'}),

            html.Div(id='last-updated', style={'textAlign': 'center', 'marginBottom': '30px', 'color': '#AAAAAA'}),

            # Filters
            html.Div(style={'display': 'flex', 'justifyContent': 'space-between', 'flexWrap': 'wrap', 'marginBottom': '30px'}, children=[
                html.Div(style=card_style, children=[
                    html.Label("Select Category:", style={'fontWeight': 'bold'}),
                    dcc.Dropdown(
                        id='category-dropdown',
                        options=[{'label': c, 'value': c} for c in categories],
                        value=categories,
                        multi=True,
                        style={'color':'black'}
                    )
                ]),
                html.Div(style=card_style, children=[
                    html.Label("Select Date Range:", style={'fontWeight': 'bold'}),
                    dcc.DatePickerRange(
                        id='date-picker',
                        start_date=first_day,
                        end_date=last_day,
                        min_date_allowed=df['date'].min() if not df.empty else first_day,
                        max_date_allowed=df['date'].max() if not df.empty else last_day,
                        display_format='YYYY-MM-DD',
                        style={'color':'black'}
                    )
                ]),
                html.Div(style=card_style, children=[
                    html.Label("Search Keyword:", style={'fontWeight': 'bold'}),
                    dcc.Input(
                        id='keyword-input',
                        type='text',
                        placeholder='Enter keyword',
                        style={'width':'100%','padding':'5px'}
                    )
                ])
            ]),

            # Summary Cards (single row with colors)
            html.Div(
                style={'display':'flex','justifyContent':'space-between','gap':'20px','marginBottom':'30px'},
                children=[
                    html.Div(id='total-articles', style={**card_style,'backgroundColor':'#00A3E0','flex':'1','textAlign':'center','fontSize':'18px'}, children=["Total Articles: 0"]),
                    html.Div(id='total-categories', style={**card_style,'backgroundColor':'#9B59B6','flex':'1','textAlign':'center','fontSize':'18px'}, children=["Total Categories: 0"]),
                    html.Div(id='top-category', style={**card_style,'backgroundColor':'#E74C3C','flex':'1','textAlign':'center','fontSize':'18px'}, children=["Top Category: -"]),
                    html.Div(id='least-category', style={**card_style,'backgroundColor':'#FFA500','flex':'1','textAlign':'center','fontSize':'18px'}, children=["Least Category: -"])
                ]
            ),

            # Charts (3x2 grid)
            html.Div(
                style={'display':'grid','gridTemplateColumns':'repeat(3, 1fr)','gap':'20px','marginBottom':'30px'},
                children=[
                    html.Div(style={**card_style}, children=[dcc.Graph(id='pie-chart')]),
                    html.Div(style={**card_style}, children=[dcc.Graph(id='top5-bar-chart')]),
                    html.Div(style={**card_style}, children=[dcc.Graph(id='trend-chart')]),
                    html.Div(style={**card_style}, children=[dcc.Graph(id='radar-chart')]),
                    html.Div(style={**card_style}, children=[dcc.Graph(id='sentiment-pie-chart')]),
                    html.Div(style={**card_style}, children=[dcc.Graph(id='sentiment-trend-chart')])
                ]
            ),

            # Articles Table
            html.Div(style={**card_style,'width':'100%'}, children=[
                html.H2("Filtered Articles", style={'textAlign':'center','color':'#00CC96'}),
                dash_table.DataTable(
                    id='articles-table',
                    columns=[
                        {"name":"Date","id":"date"},
                        {"name":"Category","id":"category"},
                        {"name":"Source","id":"source"},
                        {"name":"Title","id":"title"},
                        {"name":"Sentiment","id":"sentiment"},
                        {"name":"Full Article","id":"full_article","presentation":"markdown"},
                        {"name":"Summary","id":"summary"}
                    ],
                    style_cell={'textAlign':'left','padding':'8px','color':'white','backgroundColor':'#1f2c56'},
                    style_header={'fontWeight':'bold','backgroundColor':'#1a2336'},
                    style_table={'overflowX':'auto'},
                    page_size=10,
                    markdown_options={"link_target":"_blank"}
                )
            ]),

            dcc.Interval(
                id='interval-component',
                interval=5*60*1000,
                n_intervals=0
            )
        ]
    )

    # ---------------------------------------
    # Callback
    # ---------------------------------------
    @app.callback(
        [
            Output('pie-chart','figure'),
            Output('top5-bar-chart','figure'),
            Output('trend-chart','figure'),
            Output('radar-chart','figure'),
            Output('sentiment-pie-chart','figure'),
            Output('sentiment-trend-chart','figure'),
            Output('articles-table','data'),
            Output('last-updated','children'),
            Output('total-articles','children'),
            Output('total-categories','children'),
            Output('top-category','children'),
            Output('least-category','children')
        ],
        [
            Input('category-dropdown','value'),
            Input('date-picker','start_date'),
            Input('date-picker','end_date'),
            Input('keyword-input','value'),
            Input('interval-component','n_intervals')
        ]
    )
    def update_dashboard(selected_categories, start_date, end_date, keyword, n_intervals):
        df = load_news_data()
        df['date'] = pd.to_datetime(df['date'])

        start = pd.to_datetime(start_date) if start_date else df['date'].min()
        end = pd.to_datetime(end_date) if end_date else df['date'].max()

        filtered_df = df[
            df['category'].isin(selected_categories) &
            (df['date'] >= start) &
            (df['date'] <= end)
        ]

        if keyword and keyword.strip():
            kw = keyword.lower()
            filtered_df = filtered_df[
                filtered_df['title'].str.lower().str.contains(kw) |
                filtered_df['content'].str.lower().str.contains(kw)
            ]

        last_updated = f"Last Updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        total_articles = f"Total Articles: {len(filtered_df)}"
        total_categories = f"Total Categories: {filtered_df['category'].nunique()}"
        top_category = f"Top Category: {filtered_df['category'].value_counts().idxmax() if not filtered_df.empty else '-'}"
        least_category = f"Least Category: {filtered_df['category'].value_counts().idxmin() if not filtered_df.empty else '-'}"

        return (
            create_category_pie(filtered_df),
            create_top5_category_bar(filtered_df),
            create_articles_trend(filtered_df),
            create_category_radar(filtered_df),
            create_sentiment_pie(filtered_df),
            create_sentiment_trend(filtered_df),
            filtered_df.to_dict('records'),
            last_updated,
            total_articles,
            total_categories,
            top_category,
            least_category
        )

    app.run(debug=True, port=8050)


if __name__ == "__main__":
    run_dashboard()

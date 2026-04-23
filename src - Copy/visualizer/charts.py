# src/visualizer/charts.py
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.database import SessionLocal, News

# ---------------------------------------
# Load news data from the database
# ---------------------------------------
def load_news_data(limit=None):
    db = SessionLocal()
    query = db.query(News)
    if limit:
        query = query.limit(limit)
    news_list = query.all()
    db.close()

    # Convert to DataFrame
    data = {
        "title": [n.title for n in news_list],
        "category": [n.category for n in news_list],
        "date": [n.date for n in news_list],
    }
    df = pd.DataFrame(data)
    return df

# ---------------------------------------
# Pie chart of category distribution
# ---------------------------------------
def plot_category_distribution(df):
    counts = df['category'].value_counts()
    fig = px.pie(
        counts,
        values=counts.values,
        names=counts.index,
        title="Cybersecurity News by Category",
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    # Save HTML and open in browser
    fig.write_html("category_distribution.html", auto_open=True)

# ---------------------------------------
# Trend chart: articles over time
# ---------------------------------------
def plot_articles_over_time(df):
    df_grouped = df.groupby('date').size().reset_index(name='count')
    fig = px.line(
        df_grouped,
        x='date',
        y='count',
        title="Number of Articles Over Time",
        markers=True
    )
    # Save HTML and open in browser
    fig.write_html("articles_over_time.html", auto_open=True)

# ---------------------------------------
# Radar chart: category proportion
# ---------------------------------------
def plot_category_radar(df):
    counts = df['category'].value_counts()
    categories = counts.index.tolist()
    values = counts.values.tolist()

    # Close the radar
    categories += categories[:1]
    values = list(values) + values[:1]

    fig = go.Figure(
        data=[go.Scatterpolar(r=values, theta=categories, fill='toself', name='Category Distribution')]
    )
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True)),
        title="Radar Chart of Cybersecurity Categories"
    )
    # Save HTML and open in browser
    fig.write_html("category_radar.html", auto_open=True)

# ---------------------------------------
# Example usage
# ---------------------------------------
if __name__ == "__main__":
    df = load_news_data()
    if df.empty:
        print("No news data available.")
    else:
        plot_category_distribution(df)
        plot_articles_over_time(df)
        plot_category_radar(df)

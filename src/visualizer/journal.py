import os
import random
from fpdf import FPDF
import pandas as pd
from datetime import datetime
from dash import html, dcc, Input, Output, State
from src.database import SessionLocal, News

os.makedirs("generated_journals", exist_ok=True)

# -----------------------------
# PDF Generation Function
# -----------------------------
def generate_journal_pdf(articles, name, header, footer):
    pdf = FPDF()
    # Cover page
    pdf.add_page()
    pdf.set_font("Arial", "B", 24)
    pdf.cell(0, 20, "Cybersecurity News Journal", 0, 1, 'C')
    pdf.ln(10)
    pdf.set_font("Arial", "", 16)
    pdf.cell(0, 10, f"Prepared by: {name}", 0, 1, 'C')
    pdf.cell(0, 10, f"Submitted to: [Recipient]", 0, 1, 'C')
    pdf.cell(0, 10, f"Date: {datetime.today().strftime('%Y-%m-%d')}", 0, 1, 'C')

    # Journal entries
    for idx, article in enumerate(articles, start=1):
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.multi_cell(0, 10, f"{name} - {header}", 0, 1)
        pdf.ln(5)
        pdf.set_font("Arial", "", 12)
        pdf.multi_cell(0, 8, f"Article {idx}: {article['title']}")
        pdf.ln(3)
        pdf.multi_cell(0, 8, f"Summary:\n{article['summary']}")
        pdf.ln(3)
        pdf.multi_cell(0, 8, f"Reflection:\nThis article highlights key points in the cybersecurity field ({article['category']}).")
        if footer:
            pdf.set_y(-30)
            pdf.set_font("Arial", "I", 10)
            pdf.cell(0, 10, footer, 0, 0, 'C')

    file_path = f"generated_journals/Cyber_Journal_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
    pdf.output(file_path)
    return file_path

# -----------------------------
# Layout for Dash Page
# -----------------------------
def journal_layout(df):
    categories = sorted(df['category'].unique())
    return html.Div([
        html.H1("Generate Cybersecurity Journal", style={'textAlign':'center', 'color':'#00CC96'}),
        html.Div([
            html.Label("Header Text:"),
            dcc.Input(id='journal-header', type='text', value="Daily Cybersecurity Summary", style={'width':'100%'}),
            html.Label("Footer Text:"),
            dcc.Input(id='journal-footer', type='text', style={'width':'100%'}),
            html.Label("Your Name:"),
            dcc.Input(id='journal-name', type='text', style={'width':'100%'}),
            html.Label("Number of Articles:"),
            dcc.Input(id='num-articles', type='number', value=5, min=1, style={'width':'100%'}),
            html.Label("Select Categories:"),
            dcc.Dropdown(
                id='journal-categories',
                options=[{'label': c, 'value': c} for c in categories],
                multi=True,
                value=categories
            ),
            html.Label("Select Sentiments:"),
            dcc.Checklist(
                id='journal-sentiments',
                options=[{'label': s, 'value': s} for s in ['Positive','Neutral','Negative']],
                value=['Positive','Neutral','Negative'],
                inline=True
            ),
            html.Label("Select Date Range:"),
            dcc.DatePickerRange(
                id='journal-date-range',
                min_date_allowed=df['date'].min(),
                max_date_allowed=df['date'].max(),
                start_date=df['date'].min(),
                end_date=df['date'].max()
            ),
            html.Br(), html.Br(),
            html.Button("Generate Journal PDF", id='generate-journal-btn', n_clicks=0),
            html.Br(), html.Br(),
            html.Div(id='journal-download-links')
        ], style={'width':'50%', 'margin':'auto'})
    ])

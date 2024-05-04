import dash_draggable
import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Output, callback, Input

df = pd.read_csv('https://raw.githubusercontent.com/plotly/datasets/master/gapminder_unfiltered.csv')

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = Dash(__name__, external_stylesheets=external_stylesheets)

style_dashboard = {
    "height": '100%',
    "width": '100%',
    "display": "flex",
    "flex-direction": "column",
    "flex-grow": "0"
}


def extract_from_to(arg):
    year_from = None
    year_to = None
    if arg:
        if 'xaxis.range[0]' in arg:
            year_from = arg['xaxis.range[0]']
        if 'xaxis.range[1]' in arg:
            year_to = arg['xaxis.range[1]']

    return year_from, year_to


# 1. График по странам

default_countries = ["Russia", "United Kingdom", "Canada"]

country_chart = html.Div([
    html.H1(children='Линейный график', style={'textAlign': 'center'}),
    html.Table([
        html.Tr([
            html.Td([
                html.Div("Country")
            ], style={"white-space": "nowrap"}),
            html.Td([
                dcc.Dropdown(df.country.unique(), default_countries, multi=True, id='dropdown-countries'),
            ], style={"width": "100%"}),
        ]),
        html.Tr([
            html.Td([
                html.Div("Measure")
            ]),
            html.Td([
                dcc.Dropdown(["pop", "lifeExp", "gdpPercap"], "pop", id='dropdown-measure', clearable=False)
            ]),
        ])
    ]),
    dcc.Graph(id='country_graph', style=style_dashboard)
], id='country_chart', style=style_dashboard)


@callback(
    Output('country_graph', 'figure'),
    Input('dropdown-countries', 'value'),
    Input('dropdown-measure', 'value'),
)
def update_graph(country, measure='pop'):
    df_ = df[df.country.isin(country)]
    return px.line(df_, x='year', y=measure, color='country', title="Показатели по годам")


# 2. Пузырьковая диаграмма


def build_bubble_fig(x="pop", y="lifeExp", size="pop", year_from=None, year_to=None):
    filtered_data = df
    if year_from and year_to:
        filtered_data = df[df.year.between(year_from, year_to)]

    latest_data = filtered_data.sort_values(["continent", "year"], ascending=False).drop_duplicates("country")

    if size == "lifeExp":
        size = latest_data.lifeExp
        size = size / size.max()
        size = size ** 6

    return px.scatter(latest_data, x=x, y=y, size=size, color="continent", hover_name="country", size_max=60,
                      hover_data=["year"])


bubble_chart = html.Div([
    html.H1(children='Пузырьковая диаграмма', style={'textAlign': 'center'}),
    html.Table([
        html.Tr([
            html.Td([
                html.Div("Ось Х")
            ], style={"white-space": "nowrap"}),
            html.Td([
                dcc.Dropdown(["pop", "lifeExp", "gdpPercap"], "lifeExp", id='dropdown-bubble-ax-x', clearable=False),
            ], style={"width": "100%"}),
        ]),
        html.Tr([
            html.Td([
                html.Div("Ось Y")
            ]),
            html.Td([
                dcc.Dropdown(["pop", "lifeExp", "gdpPercap"], "pop", id='dropdown-bubble-ax-y', clearable=False)
            ]),
        ]),
        html.Tr([
            html.Td([
                html.Div("Размер")
            ]),
            html.Td([
                dcc.Dropdown(["pop", "lifeExp", "gdpPercap"], "gdpPercap", id='dropdown-bubble-size', clearable=False),
            ])
        ]),
    ]),
    dcc.Graph(id='bubble', figure=build_bubble_fig(), style=style_dashboard, responsive=True)
], id='bubble_chart', style=style_dashboard)


@callback(
    Output('bubble', 'figure'),
    Input('dropdown-bubble-ax-x', 'value'),
    Input('dropdown-bubble-ax-y', 'value'),
    Input('dropdown-bubble-size', 'value'),
    Input('country_graph', 'relayoutData'),
)
def update_bubble_dash(x, y, size, meas_vs_year_zoom):
    return build_bubble_fig(x, y, size, *extract_from_to(meas_vs_year_zoom))


# 3. Топ-15 по популяции


def build_top_pop_hist(year_from=None, year_to=None):
    filtered_data = df

    if year_from and year_to:
        filtered_data = df[df.year.between(year_from, year_to)]

    latest_data = filtered_data.sort_values("year", ascending=False).drop_duplicates("country")
    top = latest_data.sort_values("pop", ascending=False)[:15][::-1]
    return px.bar(top, x="pop", y="country", hover_data=["year"])


hist = html.Div([
    html.H1(children='Топ 15 по популяции', style={'textAlign': 'center'}),
    dcc.Graph(id='hist', figure=build_top_pop_hist(), style=style_dashboard, responsive=True)
], id='hist_chart')


@callback(
    Output('hist', 'figure'),
    Input('country_graph', 'relayoutData'),
)
def update_top_pop_hist(meas_vs_year_zoom):
    return build_top_pop_hist(*extract_from_to(meas_vs_year_zoom))


# 4. Круговая

def build_pie_fig(year_from=None, year_to=None):
    filtered_data = df

    if year_from and year_to:
        filtered_data = df[df.year.between(year_from, year_to)]

    latest_data = filtered_data.sort_values("year", ascending=False).drop_duplicates("country")

    return px.pie(latest_data, values="pop", names="continent", hole=.3)


pie_chart = html.Div([
    html.H1(children="Население континентов", style={'textAlign': 'center'}),
    dcc.Graph(id='pie', figure=build_pie_fig(), style=style_dashboard, responsive=True)
], style=style_dashboard, id="pie_chart")


@callback(
    Output('pie', 'figure'),
    Input('country_graph', 'relayoutData'),
)
def update_pie_fig(meas_vs_year_zoom):
    return build_pie_fig(*extract_from_to(meas_vs_year_zoom))


app.layout = html.Div([
    html.H1(children='Dashboard', style={'textAlign': 'center'}),
    dash_draggable.ResponsiveGridLayout([country_chart, bubble_chart, hist, pie_chart], clearSavedLayout=True, layouts={
        "lg": [
            {
                "i": "country_chart",
                "x": 0, "y": 0, "w": 6, "h": 15
            },
            {
                "i": "bubble_chart",
                "x": 0, "y": 15, "w": 6, "h": 15
            },
            {
                "i": "hist_chart",
                "x": 6, "y": 0, "w": 6, "h": 15
            },
            {
                "i": "pie_chart",
                "x": 6, "y": 15, "w": 6, "h": 15
            }
        ]
    })
])

if __name__ == '__main__':
    app.run(debug=True)

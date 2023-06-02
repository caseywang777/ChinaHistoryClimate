import dash
from dash import dcc
import plotly.graph_objs as go
from dash import html
import pandas as pd
from dash.dependencies import Input, Output
import json
import plotly.express as px
from dash import dash_table
# from dash_extensions.enrich import Output, DashProxy, Input, MultiplexerTransform

app = dash.Dash()
server = app.server
# app = DashProxy(prevent_initial_callbacks=True, transforms=[MultiplexerTransform()])

### data loading
#load china map
with open("china_province.geojson") as f:
    provinces_map = json.load(f)

#hardcode event code - name mapping
mainCode = [{'code':'10', 'str': 'Precipitation'},
            {'code':'11', 'str': 'Temperature'},
            {'code':'12', 'str': 'Visibility'},
            {'code':'13', 'str': 'Thunder, lightning'},
            {'code':'14', 'str': 'Optical'},
            {'code':'15', 'str': 'Wind'},
            {'code':'16', 'str': 'Cloud'},
            {'code':'17', 'str': 'Gas, Air'},
            {'code':'30', 'str': 'Drought'},
            {'code':'31', 'str': 'Flood'},
            {'code':'32', 'str': 'Pest/Vermin'},
            {'code':'33', 'str': 'Crops'},
            {'code':'34', 'str': 'Disease'},
            {'code':'35', 'str': 'Famine'} ]
code2Name = {d['code']: d['str'] for d in mainCode}

#load climate data
# climateDf = pd.read_excel('REACHES1368_1911.xlsx', sheet_name='data')
climateDf = pd.read_csv('REACHES1368_1911.csv')
climateDf['mainCode'] = climateDf['event_code'].str[:2]
cond = [False] * len(climateDf)
for i in mainCode:
    cond = cond | (climateDf['mainCode'] == i['code'])
climateDf = climateDf[cond]
print(climateDf)
dfDownload = climateDf

###initialization
#init choropleth map
climateCountDf = climateDf['place_provin'].value_counts().to_frame().reset_index()
climateCountDf.columns = ['province', 'count']
provinceDict = climateCountDf.set_index('province')['count'].apply(lambda x: 1).to_dict()
fig = px.choropleth_mapbox(
    data_frame=climateCountDf,
    geojson=provinces_map,
    color='count',
    locations="province",
    featureidkey="properties.NL_NAME_1",
    mapbox_style="carto-darkmatter",
    color_continuous_scale='viridis',
    center={"lat": 37.110573, "lon": 106.493924},
    zoom=2.5,
    opacity=1.0
)
climateCountDfBk = climateCountDf.copy(deep=True)
climateCountDfBk['count'] = 0
fig.add_trace(
        px.choropleth_mapbox(
    data_frame=climateCountDfBk,
    geojson=provinces_map,
    color='count',
    locations="province",
    featureidkey="properties.NL_NAME_1",
    mapbox_style="carto-darkmatter",
    color_continuous_scale='viridis',
    center={"lat": 37.110573, "lon": 106.493924},
    zoom=2.5,
    opacity=0.2
).data[0]
)

fig.update_layout(height=500)

#init line chart

climateLineDf = climateDf[climateDf['mainCode'] == '10']
df_count = climateLineDf.groupby(['place_provin', 'year_lunar_st']).size().reset_index(name='Count')
lineFig = px.line(df_count, x='year_lunar_st', y='Count', color='place_provin')
lineFig.update_layout(
    title={
        'text': 'Record Count of Variables by Years',
        'x': 0.5,  # Set x-coordinate to 0.5 for center alignment
        'xanchor': 'center'  # Anchor the title in the center
    },
    xaxis_title='Year',
    yaxis_title='Record Count',
    legend_title_text='Province'
)
lineFig.update_traces(opacity=1.0)  # Set the opacity level for all lines

#init bar chart
climateBarDf = climateDf[climateDf['mainCode'] == '10']
climateBarDf = climateBarDf[climateBarDf['year_lunar_st'] == 1911]
df_count = climateBarDf.groupby(['place_provin', 'mainCode']).size().reset_index(name='Count')
barChartFig = px.bar(df_count, x='place_provin', y='Count', color='mainCode')
barChartFig.update_layout(
    title={
        'text': 'Record Count of Provinces',
        'x': 0.5,  # Set x-coordinate to 0.5 for center alignment
        'xanchor': 'center'  # Anchor the title in the center
    },
    xaxis_title='Province',
    yaxis_title='Record Count',
    legend_title_text='Variable'
)
barChartFig.for_each_trace(lambda t: t.update(name = code2Name[t['name']]))

### init heatmap
count_items = climateDf.groupby(['place_provin', 'year_lunar_st']).size().reset_index(name='Count')
new_df = count_items.pivot(index='place_provin', columns='year_lunar_st', values='Count')
new_df = new_df.fillna(0)
heatmapFig = px.imshow(new_df)
heatmapFig.update_layout(
    title={
        'text': 'Record Count Distribution (Province vs Year)',
        'x': 0.5,  # Set x-coordinate to 0.5 for center alignment
        'xanchor': 'center'  # Anchor the title in the center
    },
    xaxis_title='Year',
    yaxis_title='Province',
    legend_title_text='Record Count',
)

app.layout = html.Div([
    html.Div([
    html.Div([
            html.Label('Select Climate Categories:'),
            dcc.Dropdown(
                id = 'categorySelector',
                options = [ 
                            {'label': i['str'], 'value': i['code']} for i in mainCode 
                           ],
                value = mainCode[0]['code'],
                multi = False
            )
        ] ,  style={'width': '25%', 'display': 'inline-block'}
    ),

    html.Br(),
    html.Br(),

    html.Div([        
        dcc.Graph(
            id = 'map',
            figure = fig,
            style={'height': '500px'}
        )
        ],  style={'width': '30%', 'display': 'inline-block'}
    ),

    html.Div([
        dcc.Graph(
            id = 'lineChart',
            figure = lineFig,
            style={'height': '500px' }
        )
        ],  style={'width': '30%', 'display': 'inline-block'}
    ),

    html.Div([
        dcc.Graph(
            id = 'barChart',
            figure = barChartFig,
            style={'height': '500px' }
        )
        ],  style={'width': '30%', 'display': 'inline-block' }
    ),
    ], style={'backgroundColor': '#E4E4E4', 'padding': '10px'}  ),


    html.Br(),

    html.Div([
    html.Div([html.Button("Download csv with selected conditions", id="btn"), dcc.Download(id="download")]),
    html.Div([
            html.Label('Year Range Selection:'),
            dcc.RangeSlider(
                id = 'yearSelector',
                min = climateDf['year_lunar_st'].min(),
                max = climateDf['year_lunar_st'].max(),
                step = 1,
                 tooltip={"placement": "bottom", "always_visible": True},
                #  marks = {1000:'1000', 1500:'1500', 2000:'2000'}
                 marks = {i: str(i) for i in range(climateDf['year_lunar_st'].min(), climateDf['year_lunar_st'].max(), 100)}
            )
        ],  style={'width': '40%', 'display': 'inline-block'}
    ),
    html.Br(),
    html.Div([
            html.Label('Select province (or select on the map):'),
            dcc.Dropdown(
                id = 'provinceSelector',
                options = [ 
                            {'label': k[0], 'value': k[0]} for k in provinceDict.items()
                           ],
                value = [k[0] for k in provinceDict.items() if k[1] == 1],
                multi = True
            )
        ] ,  style={'width': '45%', 'display': 'inline-block','margin-right': '10px'}
    ),

    html.Div([
            html.Label('Select Climate Categories:'),
            dcc.Dropdown(
                id = 'multiCategorySelector',
                options = [ 
                            {'label': i['str'], 'value': i['code']} for i in mainCode 
                           ],
                value = [mainCode[0]['code']],
                multi = True
            )
        ] ,  style={'width': '40%', 'display': 'inline-block'}
    ),


    html.Br(),
    

    html.Div([
        dcc.Graph(
            id = 'heatMap',
            figure = heatmapFig,
            style={'height': '500px' }
        )
        ],  style={'width': '40%', 'display': 'inline-block', 'margin-right': '10px' }
    ),

    html.Div([
            html.H2('Preview Data Table (Click Heat Map)'), 
            dash_table.DataTable(
            id='table',
            columns=[{'name': col, 'id': col} for col in climateDf.head(200).columns],
            data=climateDf.head(200).to_dict('records'),
            page_current=0,
            page_size=10,
            page_action='custom',
            style_table={'overflowY': 'auto', 'height': '430px'}
        ),
    ], style={'width': '55%', 'display': 'inline-block' }),

    

    # html.A('Download CSV', id='download-link', download="data.csv", href="", target="_blank"),

    html.Div(id = 'hidden-div' )
    # , style={'display':'none'}
    ], style={'backgroundColor': '#E4E4E4', 'padding': '10px'} )
], style={'backgroundColor': '#F4F4F4', 'padding': '10px'})

@app.callback([Output('table', 'data'), Output('table', 'columns')],
              [Input('heatMap','clickData')])
def updateDataTable(hover_data):
    year = hover_data['points'][0]['x']
    prov = hover_data['points'][0]['y']
    cond = (climateDf['year_lunar_st'] == year)
    cond2 = (climateDf['place_provin'] == prov)
    cond = cond & cond2
    df_filtered = climateDf[cond]
    columns = [{'name': col, 'id': col} for col in df_filtered.columns]
    return df_filtered.to_dict('records'), columns

    
mapClickString = "aa"

# @app.callback(
#     Output('hidden-div', 'children'),
#     Input('lineChart', 'clickData')
# )
# def display_hover_data(hover_data):
#     # print(hover_data)
#     # if hover_data is not None:
#     #     x_value = hover_data['points'][0]['x']
#     #     return f'Hover x-axis location: {x_value}'
#     # else:
#     #     return 'No hover data'
#     return "aaa"

@app.callback(
    Output('barChart', 'figure'),
    [Input('lineChart', 'hoverData'), Input('categorySelector','value')]
)
def updateBarChart(hover_data, varSelect):
    
    selectedAttribute = ""
    for element in mainCode:
        if element['code'] == varSelect:
            selectedAttribute = element['str']

    climateBarDf = climateDf[climateDf['mainCode'] == varSelect]
    hoverYear  = hover_data['points'][0]['x']
    if hover_data is not None:
        yearFilterDf = climateBarDf[climateBarDf['year_lunar_st'] == hoverYear ]
    else:
        yearFilterDf = climateBarDf[climateBarDf['year_lunar_st'] == 1911]
    df_count = yearFilterDf.groupby(['place_provin', 'mainCode']).size().reset_index(name='Count')
    barChartFig = px.bar(df_count, x='place_provin', y='Count', color='mainCode')
    barChartFig.update_layout(
        title={
            'text': 'Record Count of Sub-categories of "' + selectedAttribute + '" in ' + str(hoverYear) + ' by Provinces',
            'x': 0.5,  # Set x-coordinate to 0.5 for center alignment
            'xanchor': 'center'  # Anchor the title in the center
        },
        xaxis_title='Province',
        yaxis_title='Record Count',
        legend_title_text='Variable'
    )
    barChartFig.for_each_trace(lambda t: t.update(name = code2Name[t['name']]))
    return barChartFig

@app.callback(Output('lineChart', 'figure'),
    [Input('map', 'hoverData'), Input('categorySelector','value')])
def hoverMapProvince(hoverData, varSelect):
    #init line chart
    global climateDf
    global lineFig

    selectedAttribute = ""
    for element in mainCode:
        if element['code'] == varSelect:
            selectedAttribute = element['str']

    climateLineDf = climateDf[climateDf['mainCode'] == varSelect]
    df_count = climateLineDf.groupby(['place_provin', 'year_lunar_st']).size().reset_index(name='Count')
    lineFig = px.line(df_count, x='year_lunar_st', y='Count', color='place_provin')
    lineFig.update_layout(
        title={
            'text': 'Record Count of "' + selectedAttribute + '" by Years',
            'x': 0.5,  # Set x-coordinate to 0.5 for center alignment
            'xanchor': 'center'  # Anchor the title in the center
        },
        xaxis_title='Year',
        yaxis_title='Record Count',
        legend_title_text='Province'
    )
    lineFig.update_traces(opacity=1.0)  # Set the opacity level for all lines

    if not hoverData:
        lineFig.update_traces(opacity=1.0)  # Set the opacity level for all lines
    else :
        lineFig.update_traces(opacity=0.1)  # Set the opacity level for all lines

        lineFig.update_traces(opacity=1, selector=dict(name=hoverData['points'][0]['location'])) 
    
    return lineFig

@app.callback(Output('map', 'figure'),
    [Input('map', 'clickData'), Input('categorySelector','value')])
def selectProvince(clickData, varSelect): 
    global mapClickString
    global climateDf
    if clickData is not None:
        print(clickData)
        print(clickData['points'][0]['location'])
        clickProvince = clickData['points'][0]['location']
        if( provinceDict[clickProvince] == 1):
            provinceDict[clickProvince] = 0
        else:
            provinceDict[clickProvince] = 1
        print(provinceDict)
        mapClickString = mapClickString + " " + clickData['points'][0]['location']

    climateFilterDf = climateDf[climateDf['mainCode'] == varSelect]
    climateCountDf = climateFilterDf['place_provin'].value_counts().to_frame().reset_index()
    climateCountDf.columns = ['province', 'count']

    print(provinceDict)
    climateCountDfBk = climateCountDf.copy(deep=True)
    for key, value in provinceDict.items():
        if value == 0 :
            climateCountDfBk = climateCountDfBk[climateCountDfBk['province'] != key]
    print(climateCountDfBk)
    fig = px.choropleth_mapbox(
        data_frame=climateCountDfBk,
        geojson=provinces_map,
        color='count',
        locations="province",
        featureidkey="properties.NL_NAME_1",
        mapbox_style="carto-darkmatter",
        color_continuous_scale='viridis',
        center={"lat": 37.110573, "lon": 106.493924},
        zoom=2.5,
        opacity=1.0
    )
    climateCountDfBk = climateCountDf.copy(deep=True)
    climateCountDfBk['count'] = 0

    fig.add_trace(
            px.choropleth_mapbox(
        data_frame=climateCountDf,
        geojson=provinces_map,
        color='count',
        locations="province",
        featureidkey="properties.NL_NAME_1",
        mapbox_style="carto-darkmatter",
        color_continuous_scale='viridis',
        center={"lat": 37.110573, "lon": 106.493924},
        zoom=2.5,
        opacity=0.3
    ).data[0]
    )

    selectedAttribute = ""
    for element in mainCode:
        if element['code'] == varSelect:
            selectedAttribute = element['str']

    fig.update_layout(
        title={
            'text': '"' + selectedAttribute + '" Map (Record Count)',
            'x': 0.5,  # Set x-coordinate to 0.5 for center alignment
            'xanchor': 'center'  # Anchor the title in the center
        }
    )

    return fig
    # return "click"

@app.callback(Output('heatMap', 'figure'),
              [Input('multiCategorySelector','value'), Input('yearSelector','value'), Input('map', 'clickData')])
def updateHeatmap(categories, yearCond, mapClick):
    print(categories)
    print(yearCond)
    cond = (climateDf['year_lunar_st'] > yearCond[0]) & (climateDf['year_lunar_st'] < yearCond[1])
    cond2 = [False] * len(cond)
    for i in categories:
        cond2 = cond2 | (climateDf['mainCode'] == i)
    cond3 = [False] * len(cond)
    mapSelection = [key for key, value in provinceDict.items() if value == 1]
    print(mapSelection)
    for i in mapSelection:
        cond3 = cond3 | (climateDf['place_provin'] == i)
    cond = cond & cond2 &cond3
    df_filtered = climateDf[cond]
    count_items = df_filtered.groupby(['place_provin', 'year_lunar_st']).size().reset_index(name='Count')
    new_df = count_items.pivot(index='place_provin', columns='year_lunar_st', values='Count')
    new_df = new_df.fillna(0)
    figure = px.imshow(new_df)
    figure.update_layout(
        title={
            'text': 'Record Count Heatmap',
            'x': 0.5,  # Set x-coordinate to 0.5 for center alignment
            'xanchor': 'center'  # Anchor the title in the center
        },
        xaxis_title='Year',
        yaxis_title='Province',
        legend_title_text='Record Count',
    )
    global dfDownload
    dfDownload = df_filtered

    return figure

@app.callback(Output("download", "data"), [Input("btn", "n_clicks")])
def generate_csv(n_nlicks):
    global dfDownload
    return dcc.send_data_frame(dfDownload.to_csv, filename="some_name.csv")


if __name__ == '__main__':
    app.run_server()


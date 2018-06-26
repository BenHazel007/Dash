# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_html_components as html
import sqlite3
import pandas as pd
import plotly.graph_objs as go
from datetime import datetime
#from dash.dependencies import Input, Output

def df_with_index(df_temp):
    index = []
    for fwd in df_temp['underlying']:
        index.append(fwd[0:-3])
    df_temp['index'] = index
    return df_temp

def df_with_dates_price(df_temp):
    dates = []
    for fwd in df_temp['underlying']:
            dates.append(get_date(str(fwd)[-3: len(str(fwd))]))
    df_temp['forward_date'] = dates
    return df_temp

def df_with_dates(df_temp):
    dates = []
    for fwd in df_temp['UnderlyingFwd']:
            dates.append(get_date(str(fwd)[-3: len(str(fwd))]))
    df_temp['forward_date'] = dates
    return df_temp

def get_date(index):
    date = ""
    if index[0] == 'A':
        date = date + "Jan"
    elif index[0] == 'B':
        date = date + "Feb"
    elif index[0] == 'C':
        date = date + "Mar"
    elif index[0] == 'D':
        date = date + "Apr"
    elif index[0] == 'E':
        date = date + "May"
    elif index[0] == 'F':
        date = date + "Jun"
    elif index[0] == 'G':
        date = date + "Jul"
    elif index[0] == 'H':
        date = date + "Aug"
    elif index[0] == 'I':
        date = date + "Sep"
    elif index[0] == 'J':
        date = date + "Oct"
    elif index[0] == 'K':
        date = date + "Nov"
    elif index[0] == 'L':
        date = date + "Dec"

    date = date + " 20" + index[1:3]
    
    return date

#data frames containing 
df = pd.read_csv("VaR530.csv")
dfd = df_with_dates(df)

dfprice = pd.read_csv("HistoricalPrices.csv", header = None, names=['underlying', 'date', 'price'] )
dfi = df_with_index(dfprice)
dfi = df_with_dates_price(dfi)


price_indexes = dfi['index'].unique()
dates = dfi['date'].unique()

#initializes lists of available choices and includes the option for All
desks = ['All']
indexes = []
products = ['All']

#populates each list with the possible choices
desks.extend(dfd['Desk'].unique())
indexes.extend(dfd['Index'].unique())
products.extend(dfd['Product1'].unique())

app = dash.Dash()

app.layout = html.Div(children=[
    
    html.Div([
        'Products:',
        dcc.Dropdown(
            id = 'prod_drop',
            options=[{'label':i, 'value':i} for i in products],
            #inital value set to 'All'
            value = products[0]
        )
    ]),
    html.Div([
        'Index:',
        dcc.Dropdown(
            id = 'ind_drop',
            options=[{'label':i, 'value':i} for i in indexes],
            multi = True,
            value = indexes[0]
        )
    ]),
    html.Button(
        'All Indexes',
            id = 'all_button'
        ),
    html.Div([
        #the poisitions graph
        'Positions',
        dcc.Graph(
            id='main_graph'
            #set to empty at first because the 'update_graph' callback will initialize it for us
        )
    ]),
    html.Div([
        html.Div([
            dcc.Dropdown(
                id = 'index_drop',
                options=[{'label':i, 'value':i} for i in price_indexes],
                value = price_indexes[0]
            )
        ], style={'width': '49%', 'display': 'inline-block'}),
        html.Div([
            dcc.Dropdown(
                id = 'index2_drop',
                options=[{'label':i, 'value':i} for i in price_indexes],
                value = price_indexes[0]
            )
        ],style={'width': '49%', 'display': 'inline-block'})
    ]),
    html.Div([
        dcc.Checklist(
            id= 'comp_check',
            options = [{'label': 'Compare Two Products', 'value': 'comp'}],
            values = []
        )
    ]),
    html.Div([
        dcc.Graph(
            id = 'price_graph'
        )
    ]),
    html.Div([
        dcc.Dropdown(
            id = 'date_drop',
            options = [{'label':i, 'value':i} for i in dates],
            value = dates[-1]
        )
    ]),
    html.Div([
        dcc.Graph(
            id = 'single_forward'
        )
    ])
])


@app.callback(
    dash.dependencies.Output('main_graph', 'figure'),
    [dash.dependencies.Input('ind_drop', 'value'),
    dash.dependencies.Input('prod_drop', 'value')]
)
def update_graph(ind, prod):
    dfd1 = dfd[ (dfd['Product1'] == prod) ]
    dfd1 = dfd1[ (dfd['QtyBBL'] != 0) ]
    traces = []
    for i in ind:
        dfd2 = dfd1[ (dfd1['Index'] == i) ]
        real_dates = []
        for d in dfd2['forward_date']:
            dt = datetime.strptime(d, '%b %Y')
            real_dates.append(dt)
        dfd_real = dfd2[['QtyBBL']].copy()
        dfd_real['real_dates'] = real_dates

        final_qty = []
        for d in dfd_real['real_dates'].unique():
            qty = 0
            dfd3 = dfd_real[ (dfd_real['real_dates'] == d) ]

            for q in dfd3['QtyBBL']:
                qty = qty + q
            final_qty.append(qty)
        dfd_final = pd.DataFrame()
        dfd_final['real_dates'] = dfd_real['real_dates'].unique()
        dfd_final['qty'] = final_qty
        dfd_final.sort_values(by=['real_dates'], inplace=True)


        cur_trace = go.Bar(
                x = dfd_final.real_dates,
                y = dfd_final.qty.values,
                name = i
            )
        traces.append(cur_trace)

    return {
        'data': traces,
        'layout': go.Layout(
            barmode = 'relative'
        )
    }

    

@app.callback(
    dash.dependencies.Output('ind_drop', 'value'),
    [dash.dependencies.Input('all_button', 'n_clicks'),
    dash.dependencies.Input('prod_drop', 'value')]
)
def choose_all(n_clicks, prod):
    if prod == 'All':
        return ""
    else:
        df_temp = dfd[ (dfd['Product1'] == prod) ]
        return df_temp['Index'].unique()




#makes sure you can only choose indexes that are included in the currently chosen desk
#desk is the currently chosen product
@app.callback(
    dash.dependencies.Output('ind_drop', 'options'),
    [dash.dependencies.Input('prod_drop', 'value')]
)
def update_forward_options(prod):
    #Initializes the list of forwards with 'All' at the beginning
    indexes2 = []
    dfd_temp = dfd[ (dfd['QtyBBL'] != 0) ]
    if prod == 'All':    
        #if desk is 'All' all forwards are available to choose
        indexes2.extend(dfd_temp['Index'].unique())
    else:
        #if desk is specified then only get forwards associated with said desk
        dfd_temp1 = dfd_temp[ (dfd_temp['Product1'] == prod) ]
        indexes2.extend(dfd_temp1['Index'].unique())

    return [{'label':i, 'value':i} for i in indexes2]



@app.callback(
    dash.dependencies.Output('price_graph', 'figure'),
    [dash.dependencies.Input('index_drop', 'value'),
    dash.dependencies.Input('index2_drop', 'value'),
    dash.dependencies.Input('date_drop', 'value'),
    dash.dependencies.Input('comp_check', 'values')]
)
def update_price(index, index2, date, comp):
    if 'comp' not in comp:
        dfi1 = dfi[ (dfi['index'] == index) ]
        dfi1 = dfi1[ (dfi1['date'] == date) ]
        dfi1 = dfi1[ (dfi1['price'] > 0) ]
        real_dates = []
        for fdate in dfi1['forward_date']:
            dt = datetime.strptime(fdate, '%b %Y')
            real_dates.append(dt)
        df_real = dfi1[['price']].copy()
        df_real['real_dates'] = real_dates
        df_real['underlying'] = dfi['underlying']
        df_real.sort_values(by=['real_dates'], inplace=True)
        return {
            'data': [
                go.Scatter(
                    x = df_real.real_dates,
                    y = df_real.price.values,
                    text =  df_real['underlying']
                )
            ],
            'layout': go.Layout(
                xaxis = {
                    'tickangle': -45
                }
            )
        }   
    else:
        dfi1 = dfi[ (dfi['index'] == index) ]
        dfi1 = dfi1[ (dfi1['date'] == date) ]
        dfi1 = dfi1[ (dfi1['price'] > 0) ]
        real_dates1 = []
        for fdate in dfi1['forward_date']:
            dt = datetime.strptime(fdate, '%b %Y')
            real_dates1.append(dt)
        df_real1 = dfi1[['price']].copy()
        df_real1['real_dates'] = real_dates1
        df_real1['underlying'] = dfi['underlying']
        df_real1.sort_values(by=['real_dates'], inplace=True)

        dfi2 = dfi[ (dfi['index'] == index2) ]
        dfi2 = dfi2[ (dfi2['date'] == date) ]
        dfi2 = dfi2[ (dfi2['price'] > 0) ]
        real_dates2 = []
        for fdate in dfi2['forward_date']:
            dt = datetime.strptime(fdate, '%b %Y')
            real_dates2.append(dt)
        df_real2 = dfi2[['price']].copy()
        df_real2['real_dates'] = real_dates2
        df_real2['underlying'] = dfi['underlying']
        df_real2.sort_values(by = ['real_dates'], inplace=True)


        return {
            'data': [
                go.Scatter(
                    x = df_real1.real_dates,
                    y = df_real1.price.values,
                    text =  df_real1['underlying']
                ),
                go.Scatter(
                    x = df_real2.real_dates,
                    y = df_real2.price.values,
                    text =  df_real2['underlying']
                )
            ],
            'layout': go.Layout(
                xaxis = {
                    'tickangle': -45
                }
            )
        }   

@app.callback(
    dash.dependencies.Output('single_forward', 'figure'),
    [dash.dependencies.Input('price_graph', 'hoverData'),
    dash.dependencies.Input('comp_check', 'values')]
)
def single_forward(hover, comp):
    if 'comp' not in comp:
        hover_text1 = hover['points'][0]['text']
        df1 = dfprice[ (dfprice['underlying'] == hover_text1) ]
        df1 = df1[ (df1['price'] > 0) ]
        title = '<b>{}'.format(hover_text1) + " historical prices"
        
        return {
            'data': [
                go.Scatter(
                    x = df1.date.values,
                    y = df1.price.values
                )
            ],
            'layout': {
                'annotations': [{'x': 0, 'y': 1, 'xanchor': 'left', 'yanchor': 'bottom',
                    'xref': 'paper', 'yref': 'paper', 'showarrow': False,
                    'align': 'left', 'bgcolor': 'rgba(255, 255, 255, 0.5)',
                    'text': title
                }]
            }
        }
    else: 
        hover_text1 = hover['points'][0]['text']
        hover_text2 = hover['points'][1]['text']
        df1 = dfprice[ (dfprice['underlying'] == hover_text1) ]
        df1 = df1[ (df1['price'] > 0) ]
        real_dates1 = []
        for d in df1['date']:
            dt = datetime.strptime(d, '%m/%d/%Y')
            real_dates1.append(dt)
        df_real1 = df1[['price']].copy()
        df_real1['real_dates'] = real_dates1
        df_real1.sort_values(by=['real_dates'], inplace=True)

        df2 = dfprice[ (dfprice['underlying'] == hover_text2) ]
        df2 = df2[ (df2['price'] > 0) ]
        real_dates2 = []
        for d in df2['date']:
            dt = datetime.strptime(d, '%m/%d/%Y')
            real_dates2.append(dt)
        df_real2 = df2[['price']].copy()
        df_real2['real_dates'] = real_dates2
        df_real2.sort_values(by=['real_dates'], inplace=True)

        title = '<b>{}'.format(hover_text1) + " and " + hover_text2 + " historical prices"
        
        return {
            'data': [
                go.Scatter(
                    x = df_real1.real_dates,
                    y = df_real1.price.values
                ),
                go.Scatter(
                    x = df_real2.real_dates,
                    y = df_real2.price.values
                )
            ],
            'layout': {
                'annotations': [{'x': 0, 'y': 1, 'xanchor': 'left', 'yanchor': 'bottom',
                    'xref': 'paper', 'yref': 'paper', 'showarrow': False,
                    'align': 'left', 'bgcolor': 'rgba(255, 255, 255, 0.5)',
                    'text': title
                }]
            }
        }




#Runs the app
if __name__ == '__main__':
    app.run_server()

# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_html_components as html
import sqlite3
import pandas as pd
import plotly.graph_objs as go
from datetime import datetime
#from dash.dependencies import Input, Output

#adds an index column to a historic prices dataframe
def df_with_index(df_temp):
    index = []
    for fwd in df_temp['underlying']:
        index.append(fwd[0:-3])
    df_temp['index'] = index
    return df_temp

#gets the dates f the forwards and adds them in a new column to a historic prices dataframe
def df_with_dates_price(df_temp):
    dates = []
    for fwd in df_temp['underlying']:
        #looks at the last 3 characters in a forward and uses that to find the month and year it describes
        dates.append(get_date(str(fwd)[-3:]))
    df_temp['forward_date'] = dates
    return df_temp

#gets the dates f the forwards and adds them in a new column to a VaRData dataframe
def df_with_dates(df_temp):
    dates = []
    for fwd in df_temp['UnderlyingFwd']:
        #looks at the last 3 characters in a forward and uses that to find the month and year it describes
        dates.append(get_date(str(fwd)[-3:]))
    df_temp['forward_date'] = dates
    return df_temp

#uses the last 3 characters from a forward to determine what date it describes
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

    #adds the year (will have to be changed in ~82 years to stay correct for forwards in the year 2100)
    date = date + " 20" + index[1:3]
    
    return date

#df uses the first sheet of the VarData files
df = pd.read_csv("VaR530.csv")
#adds the date column (dfd = df-date)
dfd = df_with_dates(df)

#dfprice uses the historic price files
dfprice = pd.read_csv("HistoricalPrices.csv", header = None, names=['underlying', 'date', 'price'] )
#adds the index column (dfi = df-index)
dfi = df_with_index(dfprice)
#adds the date column to dfi 
dfi = df_with_dates_price(dfi)

#initializes the list of available choices for indexes to look at future curves for
price_indexes = dfi['index'].unique()
#initilializes the list of dates on which the futures where made
dates = dfi['date'].unique()

#initializes lists of available choices and includes the option for All
desks = ['All'] #currently not in use
products = ['All']
#indexes is left empty because comapring all indexes against eachother would take a long time to load
indexes = []

#populates each list with the possible choices
desks.extend(dfd['Desk'].unique()) #currently not in use
indexes.extend(dfd['Index'].unique())
products.extend(dfd['Product1'].unique())

#initializes the app itself
app = dash.Dash()

#the layout of the app
app.layout = html.Div(children=[
    
    #drop down box of available products
    html.Div([
        'Products:',
        dcc.Dropdown(
            id = 'prod_drop',
            options=[{'label':i, 'value':i} for i in products],
            #inital value set to 'All'
            value = products[0]
        )
    ]),
    #drop down box of avaialable indexes 
    html.Div([
        'Index:',
        dcc.Dropdown(
            id = 'ind_drop',
            options=[{'label':i, 'value':i} for i in indexes],
            multi = True,
            value = indexes[0]
        )
    ]),
    #Button that adds all indexes fot the given product back into the ind_drop box
    html.Button(
        'All Indexes',
        id = 'all_button'
    ),
    #
    html.Div([
        #the poisitions graph
        'Positions',
        dcc.Graph(
            id='main_graph'
            #set to empty at first because the 'update_graph' callback will initialize it for us
        )
    ]),
    # to look at future curves of individual indexes
    html.Div([
        html.Div([
            #select the first index
            dcc.Dropdown(
                id = 'index_drop',
                options=[{'label':i, 'value':i} for i in price_indexes],
                value = price_indexes[0]
            )
        ], style={'width': '49%', 'display': 'inline-block'}),
        #select the second index, but it will only show if the compare checkbox is checked
        html.Div([
            dcc.Dropdown(
                id = 'index2_drop',
                options=[{'label':i, 'value':i} for i in price_indexes],
                value = price_indexes[0]
            )
        ],style={'width': '49%', 'display': 'inline-block'})
    ]),
    #when checked the second selected index is displayed against the first 
    html.Div([
        dcc.Checklist(
            id= 'comp_check',
            options = [{'label': 'Compare Two Products', 'value': 'comp'}],
            #initially set to not compare 
            values = []
        )
    ]),
    #the graph that displays the future curves
    html.Div([
        dcc.Graph(
            id = 'price_graph'
        )
    ]),
    #chooses the date on which the forwards were purchased
    html.Div([
        dcc.Dropdown(
            id = 'date_drop',
            options = [{'label':i, 'value':i} for i in dates],
            #initially set to display the most recent date available
            value = dates[-1]
        )
    ]),
    #displays the historic prices of the given forwards
    html.Div([
        dcc.Graph(
            id = 'historic_prices'
        )
    ])
])

#uses the index drop down and the product drop down to determine what information to display on the main_graph
@app.callback(
    dash.dependencies.Output('main_graph', 'figure'),
    [dash.dependencies.Input('ind_drop', 'value'),
    dash.dependencies.Input('prod_drop', 'value')]
)
def update_graph(ind, prod):
    #dfd1 takes dfd and filters out only the chosen product to look at
    dfd1 = dfd[ (dfd['Product1'] == prod) ]
    #it also gets rid of Zero positions
    dfd1 = dfd1[ (dfd['QtyBBL'] != 0) ]
    #traces is going to be a list of data that allows multiple different indexes to be displayed 
    traces = []
    #for each index that is chosen in the ind_drop
    for i in ind:
        #dfd2 uses the filters that dfd1 applied and filters out each index from dfd1
        #dfd2 is a temporary dataframe that is reset for each chosen index
        dfd2 = dfd1[ (dfd1['Index'] == i) ]
        #dfd has already created a column with dates in the format of "Month Year" as a string
        #but now those need to be converted into datetime objects so they are displayed properly on the graph
        real_dates = []
        #for each of the dates convert it into a datetime object and then put it into real_dates[]
        #the datetime objects are the "real" dates because they actually represent a date and aren't just strings
        for d in dfd2['forward_date']:
            dt = datetime.strptime(d, '%b %Y')
            real_dates.append(dt)
        #dfd_real is a separate dataframe that holds the datetime objects of each forward and the positions assocaited with them
        #dfd_real is a temporary dataframe that is used when 
        dfd_real = dfd2[['QtyBBL']].copy()
        dfd_real['real_dates'] = real_dates
        #final_qty is a list of the sums of all positions associated with the given index
        final_qty = []
        #sums up all of the positions of an index on a given date d
        for d in dfd_real['real_dates'].unique():
            qty = 0
            #dfd3 is a temporary dataframe that represents data for a single month and a single index
            dfd3 = dfd_real[ (dfd_real['real_dates'] == d) ]
            #add up each position for a given index of a given month
            for q in dfd3['QtyBBL']:
                qty = qty + q
            #put the sum into the final_qty list
            final_qty.append(qty)
        #dfd_final is initialized as an empty dataframe
        #dfd_final is a dataframe that holds all the dates and the sum of all positions for each month
        dfd_final = pd.DataFrame()
        #it only holds the data for one index so it only needs one copy of each date
        dfd_final['real_dates'] = dfd_real['real_dates'].unique()
        dfd_final['qty'] = final_qty
        dfd_final.sort_values(by=['real_dates'], inplace=True)

        #the current trace 
        cur_trace = go.Bar(
                x = dfd_final.real_dates,
                y = dfd_final.qty.values,
                name = i
            )
        #the trace is added to the list of traces
        traces.append(cur_trace)

    return {
        'data': traces,
        'layout': go.Layout(
            #relative makes the bars stacked while still showing their actual values
            barmode = 'relative',
            xaxis = {
                'tickangle': -45,
                'dtick': 'M1'
            }
        )
    }

    
#when a product is chosen or when the "All Indexes" button is pressed all indexes are added to ind_drop
@app.callback(
    dash.dependencies.Output('ind_drop', 'value'),
    [dash.dependencies.Input('all_button', 'n_clicks'),
    dash.dependencies.Input('prod_drop', 'value')]
)
def choose_all(n_clicks, prod):
    #when all products are selected it doesn't display any indexes
    if prod == 'All':
        return ""
    else:
        df_temp = dfd[ (dfd['Product1'] == prod) ]
        df_temp = df_temp[ (df_temp['QtyBBL'] != 0) ]
        df_temp = df_temp[ (df_temp['Product1'] == prod) ]
        #all these indexes have underlying forwards that don't end in month and year characters
        #this makes them impossible to place in the graph so they are omitted
        df_temp = df_temp[ (df_temp['Index'] != 'COLONIAL A PIPE') ]
        df_temp = df_temp[ (df_temp['Index'] != 'COLONIAL D PIPE') ]
        df_temp = df_temp[ (df_temp['Index'] != 'COLONIAL F PIPE') ]
        df_temp = df_temp[ (df_temp['Index'] != 'COLONIAL H PIPE') ]
        df_temp = df_temp[ (df_temp['Index'] != 'COLONIAL M PIPE') ]
        df_temp = df_temp[ (df_temp['Index'] != 'NYMEX RBOB GCV') ]
        return df_temp['Index'].unique()


#makes sure you can only choose indexes that are part of the currently chosen product
@app.callback(
    dash.dependencies.Output('ind_drop', 'options'),
    [dash.dependencies.Input('prod_drop', 'value')]
)
def update_forward_options(prod):
    #Initializes the list of indexes
    indexes2 = []
    dfd_temp = dfd[ (dfd['QtyBBL'] != 0) ]
    if prod == 'All':    
        #if prod is 'All' all indexes are available to choose
        indexes2.extend(dfd_temp['Index'].unique())
    else:
        #if prod is specified then only get indexes associated with said product
        dfd_temp = dfd_temp[ (dfd_temp['Product1'] == prod) ]
        #all these indexes have underlying forwards that don't end in month and year characters
        #this makes them impossible to place in the graph so they are omitted
        dfd_temp = dfd_temp[ (dfd_temp['Index'] != 'COLONIAL A PIPE') ]
        dfd_temp = dfd_temp[ (dfd_temp['Index'] != 'COLONIAL D PIPE') ]
        dfd_temp = dfd_temp[ (dfd_temp['Index'] != 'COLONIAL F PIPE') ]
        dfd_temp = dfd_temp[ (dfd_temp['Index'] != 'COLONIAL H PIPE') ]
        dfd_temp = dfd_temp[ (dfd_temp['Index'] != 'COLONIAL M PIPE') ]
        dfd_temp = dfd_temp[ (dfd_temp['Index'] != 'NYMEX RBOB GCV') ]
        #dfd_temp = dfd_temp[ (dfd_temp['Index'] != 'NY BARGE F') ]
        indexes2.extend(dfd_temp['Index'].unique())

    return [{'label':i, 'value':i} for i in indexes2]


#changes the future curve graph based on the index(es) chosen in index_drop (and index2_drop if comp_check is checked)
@app.callback(
    dash.dependencies.Output('price_graph', 'figure'),
    [dash.dependencies.Input('index_drop', 'value'),
    dash.dependencies.Input('index2_drop', 'value'),
    dash.dependencies.Input('date_drop', 'value'),
    dash.dependencies.Input('comp_check', 'values')]
)
def update_price(index, index2, date, comp):
    traces = []
    #dfi1 filters out only data for the given index and the given purchase date and any prices that are at or below 0
    dfi1 = dfi[ (dfi['index'] == index) ]
    dfi1 = dfi1[ (dfi1['date'] == date) ]
    dfi1 = dfi1[ (dfi1['price'] > 0) ]
    real_dates = []
    #gets the dates associated with each forward
    for fdate in dfi1['forward_date']:
        dt = datetime.strptime(fdate, '%b %Y')
        real_dates.append(dt)
    #due to the way that dataframes work you can't add a new column to a dataframe that has been filtered like dfi1 has
    #because of this and since I want to add the 'real_dates' column a new data fram (df_real) is made
    df_real = dfi1[['price']].copy()
    df_real['real_dates'] = real_dates
    df_real['underlying'] = dfi['underlying']
    df_real.sort_values(by=['real_dates'], inplace=True)
    trace1 = go.Scatter(
        x = df_real.real_dates,
        y = df_real.price.values,
        text =  df_real['underlying']
    )
    traces.append(trace1)
    if 'comp' in comp:
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
        trace2 = go.Scatter(
                    x = df_real2.real_dates,
                    y = df_real2.price.values,
                    text =  df_real2['underlying']
                )
        traces.append(trace2)


    return {
        'data': traces,
        'layout': go.Layout(
            xaxis = {
                'tickangle': -45,
                'dtick': 'M1'
            }
        )
    }   

@app.callback(
    dash.dependencies.Output('historic_prices', 'figure'),
    [dash.dependencies.Input('price_graph', 'hoverData'),
    dash.dependencies.Input('comp_check', 'values')]
)
def historic_prices(hover, comp):
    traces = []
    hover_text1 = hover['points'][0]['text']
    df1 = dfprice[ (dfprice['underlying'] == hover_text1) ]
    df1 = df1[ (df1['price'] > 0) ]
    real_dates1 = []
    for d in df1['date']:
        dt = datetime.strptime(d, '%m/%d/%Y')
        real_dates1.append(dt)
    df_real1 = df1[['price']].copy()
    df_real1['real_dates'] = real_dates1
    df_real1.sort_values(by=['real_dates'], inplace=True)
    trace1 = go.Scatter(
        x = df_real1.real_dates,
        y = df_real1.price.values
    )
    traces.append(trace1)

    if 'comp' in comp:
        hover_text2 = hover['points'][1]['text']
        df2 = dfprice[ (dfprice['underlying'] == hover_text2) ]
        df2 = df2[ (df2['price'] > 0) ]
        real_dates2 = []
        for d in df2['date']:
            dt = datetime.strptime(d, '%m/%d/%Y')
            real_dates2.append(dt)
        df_real2 = df2[['price']].copy()
        df_real2['real_dates'] = real_dates2
        df_real2.sort_values(by=['real_dates'], inplace=True)
        trace2 = go.Scatter(
            x = df_real2.real_dates,
            y = df_real2.price.values
        )
        traces.append(trace2)

        title = '<b>{}'.format(hover_text1) + " and " + hover_text2 + " historical prices"

    else: 
        title = '<b>{}'.format(hover_text1) + " historical prices"
        
    return {
        'data': traces,
        'layout': go.Layout(
            annotations = [{'x': 0, 'y': 1, 'xanchor': 'left', 'yanchor': 'bottom',
                'xref': 'paper', 'yref': 'paper', 'showarrow': False,
                'align': 'left', 'bgcolor': 'rgba(255, 255, 255, 0.5)',
                'text': title
            }],
            xaxis = {
                'tickangle': -45
            }
        )
            
    }




#Runs the app
if __name__ == '__main__':
    app.run_server()

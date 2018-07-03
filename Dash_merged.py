import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.graph_objs as go
from datetime import datetime
import numpy as np
import base64
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

def adjust_fwd(df):
    df.loc[ (df['UnderlyingFwd'] == 'XNHON18c'), 'UnderlyingFwd'] = 'FNYHOG18'
    df.loc[ (df['UnderlyingFwd'] == 'XNHOQ18c'), 'UnderlyingFwd'] = 'FNYHOH18'
    
    df.loc[ (df['UnderlyingFwd'] == 'RBGCA'), 'UnderlyingFwd'] += "G18"
    df.loc[ (df['UnderlyingFwd'] == 'RBGCD'), 'UnderlyingFwd'] += "G18"
    df.loc[ (df['UnderlyingFwd'] == 'RBGCF'), 'UnderlyingFwd'] += "G18"
    df.loc[ (df['UnderlyingFwd'] == 'RBGCH'), 'UnderlyingFwd'] += "G18"    
    df.loc[ (df['UnderlyingFwd'] == 'RBGCM'), 'UnderlyingFwd'] += "G18"
    df.loc[ (df['UnderlyingFwd'] == 'RBGCV'), 'UnderlyingFwd'] += "G18"
    
    df.loc[ (df['Desk'] == 'Natgas'), 'QtyBBL'] = df.loc[ (df['Desk'] == 'Natgas'), 'QtyMT']

    df = df_with_dates(df)

    df = df[df.UnderlyingFwd != 'XNRBK18c']
    df = df[df.UnderlyingFwd != 'XNRBZ17c']

    
    df['QtyBBL'] = round(df['QtyBBL'])
    
    df = df.loc[df['QtyBBL'] != 0, :]
    return df

#path = "S:\TradingSystemExtracts\Risk\DailyData\DailyPosition_{}0{}0{}.csv".format(datetime.now().year, datetime.now().month, datetime.now().day)
#dfd = pd.read_csv(path)
    

#path = "S:\TradingSystemExtracts\Risk\DailyData\\"
#
#temp = []
#for file in os.listdir("S:\TradingSystemExtracts\Risk\DailyData"):
#    if 'DailyPosition_' in file:
#        if '0613' in file:
#            pass
#        else:
#            try:
#                print(file)
#                temp.append(pd.read_csv(path + file))
#            except:
#                pass
#dfd = pd.concat(temp)


dfd = pd.read_csv('dashdata.csv')
dfd = adjust_fwd(dfd)

#dfi uses the historic price files
dfi = pd.read_csv("S:\TradingSystemExtracts\Risk\DailyData\HistoricalPrices.csv", header = None, names=['underlying', 'date', 'price', 'name'],
                  skiprows = 1)
#adds the index column (dfi = df-index)
dfi = df_with_index(dfi)
#adds the date column to dfi 
dfi = df_with_dates_price(dfi)
dfi.drop(0)

#initializes the list of available choices for indexes to look at future curves for
price_indexes = dfi['name'].unique()
#initilializes the list of dates on which the futures where made
dates = dfi['date'].unique()
dates.sort()
dfi = dfi.loc[~dfi.underlying.str.contains('SPNY'), :]
dfi = dfi.loc[~dfi.underlying.str.contains('SPNX'), :]
dfi = dfi.loc[~dfi.underlying.str.contains('SPIP'), :]
#initializes lists of available choices and includes the option for All
desks = []
products = []
pos_type = []
#indexes is left empty because comapring all indexes against eachother would take a long time to load
indexes = []
val_date = []
#populates each list with the possible choices
desks.extend(dfd['Desk'].unique())
desks.sort()
indexes.extend(dfd['Index'].unique())
products.extend(dfd['Product1'].unique())
pos_type.extend(dfd['PositionType'].unique())
val_date.extend(dfd['ValueDate'].unique())
val_date.sort()
val_date = [d[0:10] for d in val_date]

#initializes the app itself

image_filename = 'gunvor.png' # replace with your own image
encoded_image = base64.b64encode(open(image_filename, 'rb').read())

app = dash.Dash()

#the layout of the app
app.layout = html.Div(children=[
    html.Div([
            html.Img(src='data:image/png;base64,{}'.format(encoded_image.decode()))
    ], style = {'text-align': 'center'}),
    html.Div([
        'Date',
        dcc.Dropdown(
            id = 'pos_date_drop',
            options=[{'label':i, 'value':i} for i in val_date],
            multi = False,
            value = val_date[-1]
        )
    ]),

    html.Div([
        'Desk',
        dcc.Dropdown(
            id = 'desk_drop',
            options=[{'label':i, 'value':i} for i in desks],
            multi = True,
            value = ''
        )
    ]),
    #drop down box of available products
    html.Div([
        'Products:',
        dcc.Dropdown(
            id = 'prod_drop',
            options=[{'label':i, 'value':i} for i in products],
            multi = True,
            value = ''
        )
    ]),
    html.Div([
        'Position Type:',
        dcc.Dropdown(
            id = 'pos_drop',
            options=[{'label':i, 'value':i} for i in pos_type],
            multi = True,
            value = ''
        )
    ]),
    #drop down box of avaialable indexes 
    html.Div([
        'Index:',
        dcc.Dropdown(
            id = 'ind_drop',
            options=[{'label':i, 'value':i} for i in indexes],
            multi = True,
            value = ''
        )
    ]),
    #Button that adds all indexes fot the given product back into the ind_drop box
    html.Button(
        'All Products',
        id = 'all_button_prod'
    ),
    html.Button(
        'All PositionTypes',
        id = 'all_button_postype'
    ),
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
        html.Div([
            dcc.Checklist(
            id= 'comp_check',
            options = [{'label': 'Compare Two Products', 'value': 'comp'}],
            #initially set to not compare 
            values = []
            )
        ],style={'width': '10%', 'display': 'inline-block'}),
        html.Div([
            dcc.Checklist(
                id = 'custom_check',
                options = [{'label': 'Create Custom Cruve', 'value': 'custom'}],
                values = []
            )
        ],style={'width': '10%', 'display': 'inline-block'})
    ]),
    html.Div([
        html.Div([],style={'width': '10%', 'display': 'inline-block'}),
        html.Div([
            dcc.Input(
                id = 'const1',
                type = 'number',
                value = 1
            )
        ],style={'width': '30%', 'display': 'inline-block'}),
        html.Div([
            dcc.Dropdown(
                id = 'op_drop',
                options = [
                    {'label':'-', 'value':'-'},
                    {'label':'+', 'value':'+'}
                ],
                value = '-'
            )
        ],style={'width': '5%', 'display': 'inline-block'}),
        html.Div([],style={'width': '15%', 'display': 'inline-block'}),
        html.Div([
            dcc.Input(
                id = 'const2',
                type = 'number',
                value = 1
            )
        ],style={'width': '30%', 'display': 'inline-block'})
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
        )],style={'width': '25%', 'display': 'inline-block'}
    ),
    #displays the historic prices of the given forwards
    html.Div([
        dcc.Graph(
            id = 'historic_prices'
        )
    ]),
     # Checklist for technical indicators
    html.Div([
        dcc.Checklist(
            id = 'technicals',
            options = [{'label': 'EWMA', 'value' : 'ewma'},
                       {'label': 'Bollinger Bands', 'value' : 'bb'},
                       {'label': 'Rolling Vol', 'value': 'vol'}],
            values = []
        )
    ]),
    # Returns distribution
    html.Div([
        dcc.Graph(
            id = 'return_dist'
        )
    ])
])

#uses the index drop down and the product drop down to determine what information to display on the main_graph
@app.callback(
    dash.dependencies.Output('main_graph', 'figure'),
    [dash.dependencies.Input('ind_drop', 'value'),
    dash.dependencies.Input('pos_drop', 'value'),
    dash.dependencies.Input('prod_drop', 'value'),
    dash.dependencies.Input('desk_drop', 'value'),
    dash.dependencies.Input('pos_date_drop', 'value')]
)
def update_graph(ind, pos, prod, desk, val_date):

    #traces is going to be a list of data that allows multiple different indexes to be displayed 
    traces = []
    if type(desk) != list:
        desk = list(desk)
    if type(prod) != list:
        prod = list(prod)
    if type(pos) != list:
        pos = list(pos)

    dfd_temp = dfd.copy()
    dfd_temp = dfd_temp[ (dfd_temp['ValueDate'].str.contains(val_date)) ]
    dfd_temp = dfd_temp[ (dfd_temp['Desk'].isin(desk)) ]
    dfd_temp = dfd_temp[ (dfd_temp['Product1'].isin(prod)) ]
    dfd1 = dfd_temp[ (dfd_temp['PositionType'].isin(pos)) ]
#    for de in desk:
#        dfd_temp = dfd[ (dfd['Desk'] == de) ]
#
#        for p in prod:
#            dfd1 = dfd_temp[ (dfd_temp['Product1'] == p) ]
#            #for each index that is chosen in the ind_drop
    for i in dfd1.Index.unique():
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

        final_qty = [round(x) for x in final_qty]
        #dfd_final is initialized as an empty dataframe
        #dfd_final is a dataframe that holds all the dates and the sum of all positions for each month
        dfd_final = pd.DataFrame()
        #it only holds the data for one index so it only needs one copy of each date
        dfd_final['real_dates'] = dfd_real['real_dates'].unique()
        dfd_final['qty'] = final_qty
        #dfd_final.sort_values(by=['real_dates'], inplace=True)
        dfd_final = dfd_final[ (dfd_final['qty'] != 0) ]

        name = i #+ " in " + p + " in " + de
        #the current trace 
        cur_trace = go.Bar(
                x = dfd_final.real_dates,
                y = dfd_final.qty.values,
                name = name
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
            },
        height = 700
        )
    }

    
#when a product is chosen or when the "All Indexes" button is pressed all indexes are added to ind_drop

#
#@app.callback(
#        dash.dependencies.Output('date_drop', 'value'),
#        [dash.dependencies.Input('date_drop', 'options')]
#)
#def update_date(date):
#    return date[0]['value']


@app.callback(
    dash.dependencies.Output('prod_drop', 'value'),
    [dash.dependencies.Input('all_button_prod', 'n_clicks'),
    dash.dependencies.Input('desk_drop', 'value')]
)
def choose_all_prod(n_clicks, desk):
    prods = []
    df_temp = dfd[ (dfd['Desk'].isin(desk)) ]
    prods.extend(df_temp['Product1'].unique())
    return prods


@app.callback(
    dash.dependencies.Output('pos_drop', 'value'),
    [dash.dependencies.Input('all_button_postype', 'n_clicks'),
    dash.dependencies.Input('desk_drop', 'value'),
    dash.dependencies.Input('prod_drop', 'value')]
)
def choose_all_pos(n_clicks, desk, prod):
    pos = []
    
    df_temp = dfd[ (dfd['Desk'].isin(desk)) ]
    df_temp2 = df_temp[ (df_temp['Product1'].isin(prod)) ]
    pos.extend(df_temp2['PositionType'].unique())
    return pos




@app.callback(
    dash.dependencies.Output('ind_drop', 'value'),
    [dash.dependencies.Input('all_button', 'n_clicks'),
    dash.dependencies.Input('prod_drop', 'value'),
    dash.dependencies.Input('desk_drop', 'value'),
    dash.dependencies.Input('pos_drop', 'value')]
)
def choose_all(n_clicks, prod, desk, pos):
    idx = []
    
    df_temp = dfd[ (dfd['Desk'].isin(desk)) ]
    df_temp2 = df_temp[ (df_temp['Product1'].isin(prod)) ]
    df_temp3 = df_temp2[ (df_temp2['PositionType'].isin(pos)) ]
    idx.extend(df_temp3['Index'].unique())

    return idx   

#makes sure you can only choose indexes that are part of the currently chosen product
@app.callback(
    dash.dependencies.Output('ind_drop', 'options'),
    [dash.dependencies.Input('prod_drop', 'value')]
)
def update_forward_options(prod):
    #Initializes the list of indexes
    indexes2 = []
    for p in prod:
        dfd_temp = dfd[ (dfd['Product1'] == p) ]
        indexes2.extend(dfd_temp['Index'].unique())

    return [{'label':i, 'value':i} for i in indexes2]

#sets the options for products to be only ones inside the available desk
@app.callback(
    dash.dependencies.Output('prod_drop', 'options'),
    [dash.dependencies.Input('desk_drop', 'value')]
)
def update_product_options(desk):
    prods = []
    for de in desk:
        dfd_temp = dfd[ (dfd['Desk'] == de) ]
        for p in prods:
            dfd_temp = dfd_temp[ (dfd_temp['Product1'] != p) ]
        prods.extend(dfd_temp['Product1'].unique())
    
    return [{'label':i, 'value':i} for i in prods]


#changes the future curve graph based on the index(es) chosen in index_drop (and index2_drop if comp_check is checked)
@app.callback(
    dash.dependencies.Output('price_graph', 'figure'),
    [dash.dependencies.Input('index_drop', 'value'),
    dash.dependencies.Input('index2_drop', 'value'),
    dash.dependencies.Input('date_drop', 'value'),
    dash.dependencies.Input('comp_check', 'values'),
    dash.dependencies.Input('custom_check', 'values'),
    dash.dependencies.Input('const1', 'value'),
    dash.dependencies.Input('op_drop', 'value'),
    dash.dependencies.Input('const2', 'value')]
)
def update_price(index1, index2, date, comp, cust, const1, op, const2):
    traces = []
    if 'custom' not in cust:
        #dfi1 filters out only data for the given index and the given purchase date and any prices that are at or below 0
        dfi1 = dfi[ (dfi['name'] == index1) ]
        dfi1 = dfi1[ (dfi1['date'] == date) ]
        dfi1 = dfi1[ (dfi1['price'] > 0) ]
        real_dates1 = []
        #gets the dates associated with each forward
        for fdate in dfi1['forward_date']:
            dt = datetime.strptime(fdate, '%b %Y')
            real_dates1.append(dt)
        #due to the way that dataframes work you can't add a new column to a dataframe that has been filtered like dfi1 has
        #because of this and since I want to add the 'real_dates' column a new data fram (df_real) is made
        df_real1 = dfi1[['price']].copy()
        df_real1['real_dates'] = real_dates1
        df_real1['underlying'] = dfi['underlying']
        df_real1.sort_values(by=['real_dates'], inplace=True)
        trace1 = go.Scatter(
            x = df_real1.real_dates,
            y = df_real1.price.values,
            text =  df_real1['underlying'],
            name = index1,
            line = {'color' : ('rgb(255, 0, 0)')}
        )
        traces.append(trace1)
        if 'comp' in comp:
            dfi2 = dfi[ (dfi['name'] == index2) ]
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
                        text =  df_real2['underlying'],
                        name = index2,
                        yaxis = 'y2',
                        line = {'color' : ('rgb(0, 0, 255)')}
                    )
            traces.append(trace2)
    else:
        dfi1 = dfi[ (dfi['name'] == index1) ]
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


        dfi2 = dfi[ (dfi['name'] == index2) ]
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

        df_temp1 = df_real1[ (df_real1['real_dates'].isin(df_real2['real_dates'])) ]
        df_temp2 = df_real2[ (df_real2['real_dates'].isin(df_real1['real_dates'])) ]
        df_real3 = pd.DataFrame()
        df_real3['price'] = df_temp1['price'].values + df_temp2['price'].values
        df_real3['real_dates'] = df_temp1['real_dates'].values
        print(df_temp1)
        print(df_temp2)
        print(df_real3)
        trace3 = go.Scatter(
            x = df_real3.real_dates,
            y = df_real3.price.values,
            text =  df_real1['underlying'],
            name = index1,
            line = {'color' : ('rgb(0, 215, 0)')}
        )
        traces.append(trace3)



    return {
        'data': traces,
        'layout': go.Layout(
            xaxis = {
                'tickangle': -45,
                'dtick': 'M1'
            },
            legend={'x' : 0,
                    'y': 1.25,
                    'font' : {'size': 10},
                    'orientation' : 'h'
            },
            yaxis2 = {
                    'overlaying': 'y',
                    'side' : 'right'},
            height = 500
        )
    }   

#shows the historical price of the forwards that are being hovered over in the price_graph
@app.callback(
    dash.dependencies.Output('historic_prices', 'figure'),
    [dash.dependencies.Input('price_graph', 'hoverData'),
    dash.dependencies.Input('comp_check', 'values'),
    dash.dependencies.Input('technicals', 'values')]
)
def historic_prices(hover, comp, tech):
    traces = []
    hover_text1 = hover['points'][0]['text']
    df1 = dfi[ (dfi['underlying'] == hover_text1) ]
    df1 = df1[ (df1['price'].astype(float) > 0) ]
    real_dates1 = []
    for d in df1['date']:
        dt = datetime.strptime(d, '%Y-%m-%d')
        real_dates1.append(dt)
    df_real1 = df1[['price']].copy()
    df_real1['real_dates'] = real_dates1
    df_real1.sort_values(by=['real_dates'], inplace=True)
    returns1 = df_real1.price.astype(float).values - df_real1.price.astype(float).shift(1)
    returns1.index = df_real1['real_dates']
    returns1 = returns1[~np.isnan(returns1)]
    trace1 = go.Scatter(
        x = df_real1.real_dates,
        y = df_real1.price.values,
        name = hover_text1,
        line = {'color' : ('rgb(255, 0, 0)')}
    )
    traces.append(trace1)
    
    if 'ewma' in tech:
        ewm = go.Scatter(
                x = df_real1.real_dates,
                y = df_real1.price.ewm(span = 20).mean().values,
                name = hover_text1 + " EWMA",
                line = {'dash':'dash'}
        )       
        traces.append(ewm)
        
    if 'bb' in tech:
        uband = go.Scatter(
                x = df_real1.real_dates,
                y = df_real1.price.ewm(span = 20).mean().values + df_real1.price.ewm(span = 20).std().values,
                name = hover_text1 + " UBand",
                line = {'dash':'dash'}
        )       
        traces.append(uband)
        lband = go.Scatter(
                x = df_real1.real_dates,
                y = df_real1.price.ewm(span = 20).mean().values - df_real1.price.ewm(span = 20).std().values,
                name = hover_text1 + " LBand",
                line = {'dash':'dash'}
        )
        traces.append(lband)
    if 'vol' in tech:
        vol = go.Scatter(
                x = df_real1.real_dates,
                y = returns1.rolling(20).std(),
                name = hover_text1 + " Volatility",
                line = {'dash':'dash',
                        'color' : 'orange'},
                yaxis = 'y2',
        )
        traces.append(vol)

    if 'comp' in comp:
        hover_text2 = hover['points'][1]['text']
        df2 = dfi[ (dfi['underlying'] == hover_text2) ]
        df2 = df2[ (df2['price'].astype(float) > 0) ]
        real_dates2 = []
        for d in df2['date']:
            dt = datetime.strptime(d, '%Y-%m-%d')
            real_dates2.append(dt)
        df_real2 = df2[['price']].copy()
        df_real2['real_dates'] = real_dates2
        df_real2.sort_values(by=['real_dates'], inplace=True)
        returns2 = df_real2.price.astype(float) - df_real2.price.astype(float).shift(1)
        returns2.index = df_real2['real_dates']
        returns2 = returns2[~np.isnan(returns2)]    
        trace2 = go.Scatter(
            x = df_real2.real_dates,
            y = df_real2.price.values,
            name = hover_text2,
            yaxis = 'y3',
            line = {'color' : ('rgb(0, 0, 255)')}
        )
        traces.append(trace2)
        
        if 'ewma' in tech:
            trace4 = go.Scatter(
                    x = df_real2.real_dates,
                    y = df_real2.price.ewm(span = 20).mean().values,
                    name = hover_text2 + " EWMA",
                    line = {'dash':'dash'},
                    yaxis = 'y3',
            )       
            traces.append(trace4)
        
        if 'bb' in tech:
            uband = go.Scatter(
                    x = df_real2.real_dates,
                    y = df_real2.price.ewm(span = 20).mean().values + df_real2.price.ewm(span = 20).std().values,
                    name = hover_text2 + " UBand",
                    line = {'dash':'dash'},
                    yaxis = 'y3',
            )       
            traces.append(uband)
            lband = go.Scatter(
                    x = df_real2.real_dates,
                    y = df_real2.price.ewm(span = 20).mean().values - df_real2.price.ewm(span = 20).std().values,
                    name = hover_text2 + " LBand",
                    line = {'dash':'dash'},
                    yaxis = 'y3',
            )
            traces.append(lband)
            
        if 'vol' in tech:
            vol2 = go.Scatter(
                    x = df_real2.real_dates,
                    y = returns2.rolling(20).std(),
                    name = hover_text2 + " Volatility",
                    line = {'dash':'dash',
                            'color' : 'green'},
                    yaxis = 'y4',
            )
            traces.append(vol2)
        
      
        title = '<b>{}'.format(hover_text1) + " and " + hover_text2 + " Historical Price"

    else: 
        title = '<b>{}'.format(hover_text1) + " Historical Prices"
        
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
            },
            legend={'x' : 0,
                    'y': 1.25,
                    'font' : {'size': 10},
                    'orientation' : 'h'
                    },
            yaxis2 = {
                    'overlaying': 'y',
                    'side' : 'left',
                    'anchor': 'free',
                    'showline' : False,
                    'showgrid' : False,
                    'showticklabels': False},
            yaxis3 = {
                    'overlaying': 'y',
                    'side' : 'right',
                    'anchor': 'x'},
            yaxis4 = {
                    'overlaying': 'y',
                    'side' : 'right',
                    'anchor': 'free',
                    'showline' : False,
                    'showgrid' : False,
                    'showticklabels': False},
            height = 500
        )
            
    }

@app.callback(
    dash.dependencies.Output('return_dist', 'figure'),
    [dash.dependencies.Input('price_graph', 'hoverData'),
     dash.dependencies.Input('comp_check', 'values')]
)
def return_distributions(hover, comp):
    ret = []
    hover_text1 = hover['points'][0]['text']
    df1 = dfi[ (dfi['underlying'] == hover_text1) ]
    df1 = df1[ (df1['price'].astype(float) > 0) ]
    real_dates1 = []
    for d in df1['date']:
        dt = datetime.strptime(d, '%Y-%m-%d')
        real_dates1.append(dt)
    df_real1 = df1[['price']].copy()
    df_real1['real_dates'] = real_dates1
    df_real1.sort_values(by=['real_dates'], inplace=True)
    returns1 = df_real1.price.astype(float).values - df_real1.price.astype(float).shift(1)
    returns1.index = df_real1['real_dates']
    returns1 = returns1[~np.isnan(returns1)]
    ret1 = go.Histogram(
        x = returns1,
        name = hover_text1,
        opacity = .75
        
    )
    corr = 1
    ret.append(ret1)
    if 'comp' in comp:
        hover_text2 = hover['points'][1]['text']
        df2 = dfi[ (dfi['underlying'] == hover_text2) ]
        df2 = df2[ (df2['price'].astype(float) > 0) ]
        real_dates2 = []
        for d in df2['date']:
            dt = datetime.strptime(d, '%Y-%m-%d')
            real_dates2.append(dt)
        df_real2 = df2[['price']].copy()
        df_real2['real_dates'] = real_dates2
        df_real2.sort_values(by=['real_dates'], inplace=True)
        returns2 = df_real2.price.astype(float) - df_real2.price.astype(float).shift(1)
        returns2.index = df_real2['real_dates']
        returns2 = returns2[~np.isnan(returns2)]
        ret2 = go.Histogram(
            x = returns2,
            name = hover_text2,
            opacity = .5
        )
        ret.append(ret2)
        
        if returns1.shape[0] > returns2.shape[0]:
            mask = [idx in returns2.index for idx in returns1.index]
            returns1 = returns1[mask]
            mask = [idx in returns1.index for idx in returns2.index]
            returns2 = returns2[mask]
        else: 
            mask = [idx in returns1.index for idx in returns2.index]
            returns2 = returns2[mask]
            mask = [idx in returns2.index for idx in returns1.index]
            returns1 = returns1[mask]
        
        corr = np.corrcoef(returns1, returns2)[0][1]
            
        
    return {
        'data': ret,
        'layout' : go.Layout(
                barmode='stack',
                
                annotations = [{'x': 0, 'y': 1, 'xanchor': 'left', 'yanchor': 'bottom',
                    'xref': 'paper', 'yref': 'paper', 'showarrow': False,
                    'align': 'left', 'bgcolor': 'rgba(255, 255, 255, 0.5)',
                    'text': "<b>{}".format("Return Distribution")
            }, {'x': .25, 'y': 1, 'xanchor': 'left', 'yanchor': 'bottom',
                    'xref': 'paper', 'yref': 'paper', 'showarrow': False,
                    'align': 'center', 'bgcolor': 'rgba(255, 255, 255, 0.5)',
                    'text': "Correlation = {:+.4f}".format(corr)}]
        )
    }

#Runs the app
if __name__ == '__main__':
    app.run_server()
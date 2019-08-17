industry_list = np.array(
        ['建材', '食品饮料', '医药', '家电', '机械', '电子元器件', '交通运输', '电力及公用事业', '餐饮旅游', '石油石化', '有色金属',  '计算机', '商贸零售',
         '基础化工','汽车', '电力设备', '轻工制造', '综合', '钢铁', '农林牧渔', '煤炭', '纺织服装', '传媒', '国防军工', '通信'])
industry_classification = c_data.get_CITIC_classification('2019-06-10')
sample_start_date = '2010-01-01'
sample_end_date ='2019-06-13'
date_list = c_date.gen_date_list(sample_start_date, sample_end_date, request_type=2)

#load四张表
price_all = c_data.get_N_day_stock_EOD(sample_start_date, sample_end_date, columns=['date_int', 'stock_code_wind', 'close_adj'])
column_list = ['s_fa_cashtoliqdebt','s_fa_grossprofitmargin', 's_fa_fcff']
indicator_all = c_data.get_Ashare_financial_indicator2('all', column_list, start_date=sample_start_date, end_date=sample_end_date)
column_list = ['acct_rcv','inventories','oth_rcv', 'fix_assets', 'const_in_prog', 'proj_matl', 'monetary_cap']
balance_sheet_all = c_data.get_Ashare_balance_sheet2('all', column_list, start_date=sample_start_date, end_date=sample_end_date)
column_list = ['oper_rev']
profit_sheet_all = c_data.get_Ashare_income2('all', column_list,start_date=sample_start_date, end_date=sample_end_date)

#本地储存四张表
indicator_all.to_csv('indicator_all.csv')
balance_sheet_all.to_csv('balance_sheet_all.csv')
profit_sheet_all.to_csv('profit_sheet_all.csv')

#create dataframe of avg growth among industries
industries_avg_growth = pd.DataFrame(columns=industry_list, index=date_list)
for ind in industry_list:
    codes = industry_classification[industry_classification['industry_L1'] == ind]['stock_code_wind']
    codes.index = codes
    price_df = pd.DataFrame(index = date_list, columns = codes)
    for code in codes:
        temp_price = price_all[price_all['stock_code_wind'] == code]
        temp_price.index = temp_price.date_int
        if (len(temp_price != 0)):
            price_df[code] = temp_price.loc[date_list]['close_adj']
    price_df = price_df.pct_change()
    price_df.to_csv('industries_prices/' + str(ind) + 'price.csv')
    industries_avg_growth[ind] = price_df.mean(axis=1)

#本地储存industry growth
industries_avg_growth.to_csv('industries_prices/industries_avg_growth.csv')
#本地读取Industry growth
industries_avg_growth = pd.read_csv('industries_prices/industries_avg_growth.csv', index_col=0, header=0, engine='python')


def closest_trade_day(date): #date format int
    while c_date.is_trade_day(date) == False:
        date = c_date.get_next_x_day(date, x=1, trade_day=True, request_type=2)
    return date


#create dataframe of trading start dates of stocks (date format: int)
all_codes = price_all.stock_code_wind.unique()
trading_start_date = pd.DataFrame(columns = all_codes, index = ['date'])
for code in all_codes:
    trading_start_date.loc['date', code] = price_all[price_all.stock_code_wind == code].date_int.min()
trading_start_date.to_csv('trading_start_date.csv')

#本地读取四张表
price_all = pd.read_csv('price_all.csv', index_col=0, header=0, engine='python')
indicator_all = pd.read_csv('indicator_all.csv', index_col=0, header=0, engine='python')
balance_sheet_all = pd.read_csv('balance_sheet_all.csv', index_col=0, header=0, engine='python')
profit_sheet_all = pd.read_csv('profit_sheet_all.csv', index_col=0, header=0, engine='python')

#data cleaning
indicator_all = pd.read_csv('indicator_all.csv', index_col=0, header=0, engine='python')
indicator_all['ann_date'] = indicator_all['ann_date'].apply(lambda x: closest_trade_day(x))   #将财报发布日期调整至最近交易日
indicator_all.period = pd.to_datetime(indicator_all['period'].astype(str), format= '%Y%m%d')

balance_sheet_all = pd.read_csv('balance_sheet_all.csv', index_col=0, header=0, engine='python')
balance_sheet_all = balance_sheet_all[balance_sheet_all['report_type'] == 408001000]    #选用合并报表
balance_sheet_all['ann_date'] = balance_sheet_all['ann_date'].apply(lambda x: closest_trade_day(x))  #将财报发布日期调整至最近交易日
balance_sheet_all.period = pd.to_datetime(balance_sheet_all['period'].astype(str), format= '%Y%m%d')

#将固定资产，在建工程，工程物资及货币资金缺失数据处理为0
balance_sheet_all[['const_in_prog','proj_matl','monetary_cap','fix_assets']] = balance_sheet_all[['const_in_prog','proj_matl','monetary_cap','fix_assets']].fillna(0)

profit_sheet_all = pd.read_csv('profit_sheet_all.csv', index_col=0, header=0, engine='python')
profit_sheet_all= profit_sheet_all[profit_sheet_all['report_type'] == 408001000] #选用合并报表
profit_sheet_all['ann_date'] = profit_sheet_all['ann_date'].apply(lambda x: closest_trade_day(x))  #将财报发布日期调整至最近交易日
profit_sheet_all.period = pd.to_datetime(profit_sheet_all['period'].astype(str), format= '%Y%m%d')

#create dictionary of adjusted close prices in each industry
price_dict = {}
for ind in industry_list:
    price_dict[ind] = pd.read_csv('industries_prices/' + str(ind) + 'price.csv', index_col=0, header=0, engine='python')




import os
import datetime
import numpy as np
import pandas as pd

def closest_trade_day(date): #date format int
    while c_date.is_trade_day(date) == False:
        date = c_date.get_next_x_day(date, x=1, trade_day=True, request_type=2)
    return int(date)

#本地读取Industry growth
industries_avg_growth = pd.read_csv('industries_prices/industries_avg_growth.csv', index_col=0, header=0, engine='python')

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

industry_list = np.array(
        ['建材', '食品饮料', '医药', '家电', '机械', '电子元器件', '交通运输', '电力及公用事业', '餐饮旅游', '石油石化', '有色金属',  '计算机', '商贸零售',
         '基础化工','汽车', '电力设备', '轻工制造', '综合', '钢铁', '农林牧渔', '煤炭', '纺织服装', '传媒', '国防军工', '通信'])
industry_classification = c_data.get_CITIC_classification('2019-06-10')
sample_start_date = '2010-01-01'
sample_end_date ='2019-06-13'
date_list = c_date.gen_date_list(sample_start_date, sample_end_date, request_type=2)


#create dictionary of adjusted close prices in each industry
price_dict = {}
for ind in industry_list:
    price_dict[ind] = pd.read_csv('industries_prices/' + str(ind) + 'price.csv', index_col=0, header=0, engine='python')


def cash_to_liqdebt_quantile(ind, quantile = 0.999):
    index = 's_fa_cashtoliqdebt'
    price_df = price_dict[ind]
    fin_df = pd.DataFrame(columns=price_df.columns, index=date_list)
    for code in price_df.columns:
        temp = indicator_all[indicator_all['stock_code_wind'] == code]
        temp = temp.drop_duplicates(subset='ann_date', keep='last')
        temp.index = temp.ann_date

        fin_df[code] = temp[index]
        fin_df = fin_df.fillna(method='ffill')
        fin_df = fin_df.fillna(method='bfill')

    fin_df = fin_df[~price_df.isnull()]   #处理非上市日期的数据
    compare = fin_df.quantile(quantile, axis=1)  #进行同业位序排列
    compare = compare.fillna(np.inf)
    fin_df[price_df.isnull()] = -np.inf   #处理非上市日期的数据，使非上市期间的票不会被选中

    selection = fin_df.gt(compare, axis=0)
    return selection


def ar_to_or_quantile(ind, quantile = 0.999):
    index1, index2 = 'acct_rcv', 'oper_rev'
    price_df = price_dict[ind]
    fin_df1 = pd.DataFrame(columns=price_df.columns, index=date_list)
    fin_df2 = pd.DataFrame(columns=price_df.columns, index=date_list)
    for code in price_df.columns:
        temp = balance_sheet_all[balance_sheet_all['stock_code_wind'] == code]
        temp = temp.drop_duplicates(subset='ann_date', keep='last')
        temp.index = temp.ann_date
        # financial indicator: account receivable
        fin_df1[code] = temp[index1]
        fin_df1 = fin_df1.fillna(method='ffill')
        fin_df1 = fin_df1.fillna(method='bfill')

        # financial indicator: operating revenue
        temp2 = profit_sheet_all[profit_sheet_all['stock_code_wind'] == code]
        temp2 = temp2.drop_duplicates(subset='ann_date', keep='last')
        temp2.index = temp2.ann_date
        fin_df2[code] = temp2[index2]
        fin_df2 = fin_df2.fillna(method='ffill')
        fin_df2 = fin_df2.fillna(method='bfill')
    ratio = fin_df1.div(fin_df2)
    ratio = ratio[~price_df.isnull()]          #处理非上市日期的数据
    compare = ratio.quantile(quantile, axis=1)
    ratio[price_df.isnull()] = -np.inf  # 处理非上市日期的数据，使非上市期间的票不会被选中
    selection = ratio.gt(compare, axis=0)
    return selection




def invt_to_ta_quantile(ind, quantile = 0.999):
    index1, index2 = 'inventories', 'total_asset'
    price_df = price_dict[ind]
    fin_df1 = pd.DataFrame(columns=price_df.columns, index=date_list)
    fin_df2 = pd.DataFrame(columns=price_df.columns, index=date_list)
    for code in price_df.columns:
        temp = balance_sheet_all[balance_sheet_all['stock_code_wind'] == code]
        temp = temp.drop_duplicates(subset='ann_date', keep='last')
        temp.index = temp.ann_date
        # inventories
        fin_df1[code] = temp[index1]
        fin_df1 = fin_df1.fillna(method='ffill')
        fin_df1 = fin_df1.fillna(method='bfill')

        # total assets
        fin_df2[code] = temp[index2]
        fin_df2 = fin_df2.fillna(method='ffill')
        fin_df2 = fin_df2.fillna(method='bfill')

    ratio = fin_df1.div(fin_df2)
    ratio = ratio[~price_df.isnull()]          #清除非上市日期的数据
    compare = ratio.quantile(quantile, axis=1)
    ratio[price_df.isnull()] = -np.inf  # 处理非上市日期的数据，使非上市期间的票不会被选中
    selection = ratio.gt(compare, axis=0)
    return selection



def oth_rcv_to_ta_quantile(ind, quantile = 0.999 ):
    index1, index2 = 'oth_rcv', 'total_asset'
    price_df = price_dict[ind]
    fin_df1 = pd.DataFrame(columns=price_df.columns, index=date_list)
    fin_df2 = pd.DataFrame(columns=price_df.columns, index=date_list)
    for code in price_df.columns:
        temp = balance_sheet_all[balance_sheet_all['stock_code_wind'] == code]
        temp = temp.drop_duplicates(subset='ann_date', keep='last')
        temp.index = temp.ann_date
        # inventories
        fin_df1[code] = temp[index1]
        fin_df1 = fin_df1.fillna(method='ffill')
        fin_df1 = fin_df1.fillna(method='bfill')

        # total assets
        fin_df2[code] = temp[index2]
        fin_df2 = fin_df2.fillna(method='ffill')
        fin_df2 = fin_df2.fillna(method='bfill')

    ratio = fin_df1.div(fin_df2)
    ratio = ratio[~price_df.isnull()]          #清除非上市日期的数据
    compare = ratio.quantile(quantile, axis=1)
    ratio[price_df.isnull()] = -np.inf # 处理非上市日期的数据，使非上市期间的票不会被选中
    selection = ratio.gt(compare, axis=0)
    return selection



def sa_to_ta_quantile(ind, quantile = 0.999):
    index1, index2, index3, index4, index5 = 'total_asset', 'fix_assets', 'const_in_prog', 'proj_matl', 'monetary_cap'
    price_df = price_dict[ind]
    fin_df1 = pd.DataFrame(columns=price_df.columns, index=date_list)
    fin_df2 = pd.DataFrame(columns=price_df.columns, index=date_list)
    fin_df3 = pd.DataFrame(columns=price_df.columns, index=date_list)
    fin_df4 = pd.DataFrame(columns=price_df.columns, index=date_list)
    fin_df5 = pd.DataFrame(columns=price_df.columns, index=date_list)

    for code in price_df.columns:
        temp = balance_sheet_all[balance_sheet_all['stock_code_wind'] == code]
        temp = temp.drop_duplicates(subset='ann_date', keep='last')
        temp.index = temp.ann_date
        # total assets
        fin_df1[code] = temp[index1]
        fin_df1 = fin_df1.fillna(method='ffill')
        fin_df1 = fin_df1.fillna(method='bfill')
        # fix_assets
        fin_df2[code] = temp[index2]
        fin_df2 = fin_df2.fillna(method='ffill')
        fin_df2 = fin_df2.fillna(method='bfill')
        #const_in_prog
        fin_df3[code] = temp[index3]
        fin_df3 = fin_df3.fillna(method='ffill')
        fin_df3 = fin_df3.fillna(method='bfill')
        #proj_matl
        fin_df4[code] = temp[index4]
        fin_df4 = fin_df4.fillna(method='ffill')
        fin_df4 = fin_df4.fillna(method='bfill')
        #monetary_cap
        fin_df5[code] = temp[index5]
        fin_df5 = fin_df5.fillna(method='ffill')
        fin_df5 = fin_df5.fillna(method='bfill')

    sa = fin_df1 - fin_df2 - fin_df3 - fin_df4 - fin_df5
    ratio = sa.div(fin_df2)
    ratio = ratio[~price_df.isnull()]          #清除非上市日期的数据
    compare = ratio.quantile(quantile, axis=1)
    ratio[price_df.isnull()] = -np.inf # 处理非上市日期的数据，使非上市期间的票不会被选中
    selection = ratio.gt(compare, axis=0)
    return selection


def fcff_to_ta_quantile(ind, quantile=0.999):
    index1, index2 = 'total_asset', 's_fa_fcff'
    price_df = price_dict[ind]
    fin_df1 = pd.DataFrame(columns=price_df.columns, index=date_list)
    fin_df2 = pd.DataFrame(columns=price_df.columns, index=date_list)
    for code in price_df.columns:
        temp = balance_sheet_all[balance_sheet_all['stock_code_wind'] == code]
        temp = temp.drop_duplicates(subset='ann_date', keep='last')
        temp.index = temp.ann_date
        # total assets
        fin_df1[code] = temp[index1]
        fin_df1 = fin_df1.fillna(method='ffill')
        fin_df1 = fin_df1.fillna(method='bfill')

        temp2 = indicator_all[indicator_all['stock_code_wind'] == code]
        temp2 = temp2.drop_duplicates(subset='ann_date', keep='last')
        temp2.index = temp2.ann_date
        # free cash flow
        fin_df2[code] = temp2[index2]
        fin_df2 = fin_df2.fillna(method='ffill')
        fin_df2 = fin_df2.fillna(method='bfill')

    ratio = fin_df2.div(fin_df1)
    ratio = ratio[~price_df.isnull()]          #清除非上市日期的数据
    compare = ratio.quantile(quantile, axis=1)
    ratio[price_df.isnull()] = -np.inf # 处理非上市日期的数据，使非上市期间的票不会被选中
    selection = ratio.gt(compare, axis=0)
    return selection




#selection = oth_rcv_to_ta(ind, 0.95)
# selection = ar_to_or(ind, 0.99)
# selection4 = cash_to_liqdebt(ind, 0.99)
# selection_merge = pd.DataFrame(selection.values * selection2.values * selection3.values * selection4.values, columns = selection.columns, index = selection.index)
# selection = fcff_to_ta(ind)

selection = invt_to_ta(ind, 0.95)

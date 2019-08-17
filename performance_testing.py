price_all =pd.DataFrame(index = date_list)
selection_all = pd.DataFrame(index = date_list)
ind_performance_all = pd.DataFrame(index = date_list)
output = pd.DataFrame(columns = industry_list, index = date_list)
for year in np.arange(2010, 2019):
    output = output.append(pd.Series(name =str(year) + '_stock' ))
    output = output.append(pd.Series(name=str(year) + '_win rate'))
    output = output.append(pd.Series(name=str(year) + '_P/L'))

for ind in industry_list:
    selection_gpm = gpm_growth_rate_std(ind, 6) *1
    selection_invt_ta = invt_to_ta_std(ind,  2) *1
    selection_cash_liqdebt = cash_to_liqdebt_std(ind, 4) *1
    selection_ar_or = ar_to_or_std(ind, 2) *1
    selection_oar_ta = oth_rcv_to_ta_std(ind, 3) *1
    selection_sa_ta = sa_to_ta_std(ind, 3) *1
    selection_fcff = fcff_to_ta_std(ind, 1.5) *1

    all_factor = selection_gpm + selection_invt_ta + selection_cash_liqdebt + selection_ar_or +  selection_oar_ta + selection_sa_ta + selection_fcff
    selection = all_factor > 2


    if (selection.sum().sum() != 0):
        price_df = price_dict[ind]
        portfolio = price_df[selection]
        ind_price_df = pd.concat([industries_avg_growth[ind]] * len(price_df.columns), axis=1)

        price_all = pd.concat([price_all, price_df], axis = 1)
        selection_all = pd.concat([selection_all, selection], axis = 1)
        ind_performance_all = pd.concat([ind_performance_all, ind_price_df], axis = 1)
        output[ind] = selection.sum(axis=1)

        for year in np.arange(2010, 2019):
            #number of stocks selected
            selected_stocks = selection.loc[int(str(year) +'0104') : int(str(year) +'1231')]
            output.loc[str(year) + '_stock',ind] = len(selected_stocks.sum()[selected_stocks.sum() >0].index)
            #胜率
            ind_price_df.columns = selection.columns
            temp = ind_price_df[selection]
            product1 = (portfolio + 1).product()
            product2 = (temp + 1).product()
            diff = product1 - product2
            win = (diff > 0)
            lose = (diff < 0)
            fair = (diff == 0)
            win_rate = (win.sum() + 0.5 * fair.sum()) / (~diff.isnull()).sum()
            output.loc[str(year) + '_win rate',ind] = win_rate
            #盈亏比
            if (-diff[lose].sum() == 0):
                PL = 0
            else:
                PL = diff[win].sum() / -diff[lose].sum()
            output.loc[str(year) + '_P/L',ind] = PL

output['all'] = output.sum(axis=1)
for year in np.arange(2010, 2019):
    output.loc[str(year) + '_win rate', 'all' ] = np.mean(output.loc[str(year) + '_win rate'][:-1])
    output.loc[str(year) + '_P/L', 'all'] = np.mean(output.loc[str(year) + '_P/L'][:-1])

date_series = pd.Series(date_list)
sell_dates = date_series[1:]
buy_selection = selection_all
sell_selection = selection_all.copy()
sell_selection = sell_selection.iloc[:-1, :]
sell_selection.index = sell_dates

price_all = price_all+1
sell_port = price_all[sell_selection].sum(axis=1) / (~price_all[sell_selection].isnull()).sum(axis=1)
buy_port = price_all[buy_selection].sum(axis=1) / (~price_all[buy_selection].isnull()).sum(axis=1)
buy_port_yest = buy_port.copy()
buy_port_yest = buy_port_yest[:-1]
buy_port_yest.index = sell_dates
pml = buy_port_yest - sell_port + buy_port
output['pml'] = buy_port_yest - sell_port + buy_port


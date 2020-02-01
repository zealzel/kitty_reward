
#  custom_funcs = {}


common_funcs = {

    # date  as datetime
    'format_date': lambda date: '%s年%s月%s日' % (date.year - 1911, date.month, date.day),
    'y_m_d': lambda date: [date.year, date.month, date.day],
    'date_year': lambda date : date.year, 
    'date_month': lambda date: date.month, 
    'date_day': lambda date: date.day, 
    
    # year as integer
    'year_minguo_to_bc': lambda year: year + 1911,
    'year_bc_to_minguo': lambda year: year - 1911
}

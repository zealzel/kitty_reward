from explay.source import xlManager, ExPlay


def xls_process(file_to_process, award_type):
    print('xls_process !!!!!!')
    if award_type == '2_points':
        print('2_points!!!!!')
        exp = ExPlay(proj_name='project_2p')
    elif award_type == '4_points':
        print('4_points!!!!!')
        exp = ExPlay(proj_name='project_4p')
    exp._merg_params[0]['location'] = [file_to_process]
    exp.run_proj()
    df_txt, df_excel = exp.results['txt'], exp.results['excel']
    df_txt.warning.to_csv('output/final_result.txt', index=False)

# -*- coding: utf8 -*-
import datetime
import json
from collections import Counter
import pandas as pd

# define customed functions here. mainly for extension operation



def exp_check_category(category):

    # remove duplicate
    category_remove_dup = list(set(category))

    # remove first two characters
    category_reduced = [e[2:] for e in category_remove_dup]
    print(category_reduced)

    # conditional logic
    all_by_order = ['補繳車費處理單', '裁處書', '菸害防制法檢查紀錄表']

    if len(category_reduced) == 1:
        output_string = '開立{}'.format(category_reduced[0])

    elif len(category_reduced) ==2 :
        output_string = '開立{}'.format('或'.join(filter(lambda x: x in category_reduced, all_by_order)))
    else:
        output_string = '開立{}、{}或{}'.format(*all_by_order)

    return output_string


def exp_to_datetime(date, time):
    date_time = datetime.datetime.combine(date, time)
    return date_time


def exp_date_minguo_2p(date):
    return [date.year - 1911, date.month, date.day]


def exp_cal_score(role_list):
    return len(role_list)


def exp_award_each(role_list, content, category):
    if len(role_list) >= 2:
        words = '發現且成功取締旅客{}，並{}'.format(content, category)
    elif len(role_list) == 1:
        role = role_list[0]
        if role == '開立者':
            words = '成功取締旅客{}，並{}'.format(content, category)
        elif role == '發現者':
            words = '發現旅客{}'.format(content)
    else:
        import pdb; pdb.set_trace()
    return words


def exp_award_each2(award_item, date_list, role_list_sum):
    date_list_json = [json.dumps(e) for e in date_list]
    cc = Counter()
    for d in date_list_json:
        cc[d] += 1

    words = []
    for i, (date_json, count) in enumerate(cc.items()):
        date = json.loads(date_json)

        each = '{}月{}日'.format(date[1], date[2])
        if i==0:
            each = '{}年{}'.format(date[0], each)

        if award_item.startswith('發現且成功'):
            if role_list_sum > 2:
                each = '{}(同日{}次)'.format(each, int(role_list_sum/2))
        else:
            if role_list_sum > 1:
                each = '{}(同日{}次)'.format(each, int(role_list_sum))

        words.append(each)

    concat_words = words[0]

    return concat_words


def exp_award_each3(award_item, words):

    def concat_year(words):
        if len(words) == 1:
            concat_words = words[0]
        elif len(words) == 2:
            word_first, word_second = words
            word_second_remove_year = word_second[4:]
            concat_words = '{}及{}'.format(word_first, word_second_remove_year)
        else:
            word_first = words[0]
            word_else = words[1:]
            word_else_remove_year = [w[4:] for w in word_else]
            words = [word_first] + word_else_remove_year
            concat_words = '{}及{}'.format('、'.join(words[:-1]), words[-1])
        return concat_words

    print(words)
    if len(words) == 1:
        concat_words = words[0]
    elif len(words) == 2:
        word_first, word_second = words
        if_cross_year = word_first[:3]!=word_second[:3]
        if if_cross_year:
            concat_words = '{}及{}'.format(*words)
        else:
            concat_words = concat_year(words)
    else:
        each_year_extracted = [w[:3] for w in words]
        year_cross = sorted(list(set(each_year_extracted)))
        if_cross_year = len(year_cross)>1
        if if_cross_year:
            ix_second = each_year_extracted.index(year_cross[-1])
            group_first = words[:ix_second]
            group_second = words[ix_second:]
            concat1 = concat_year(group_first)
            concat2 = concat_year(group_second)
            concat_words = '{}和{}'.format(concat1, concat2)
        else:
            concat_words = concat_year(words)
    return concat_words


def exp_concat_words(name, job_title, award_item3):
    concat_each = '；'.join(award_item3)
    words = '{}{}於{}'.format(job_title, name, concat_each)
    return words
    

def exp_datestr_to_ymd(date): # date string to datetime
    date = datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
    y_m_d = [date.year, date.month, date.day]
    return y_m_d




# 4-points

def exp_gen_year(date_list, score_list, sort=True):
    from collections import Counter
    import json
    import pandas as pd
    if sort:
        date_list = sorted(date_list)
    count = Counter([e[0] for e in date_list])

    def is_this_year_first(each, array):
        more_than_once_this_year = Counter([e[0] for e in array])[each[0]] > 1
        this_year = each[0]
        before_this_year = [e[0] for e in array[:array.index(each)]]
        is_this_year_first = this_year not in before_this_year
        return is_this_year_first

    def format1(y_m_d, score, taiwan=False):
        y_m_d[0] = y_m_d[0] - 1911 if taiwan else y_m_d[0]
        additional = '(共%s件)' % score if score>1 else ''
        return '%d年%d月%d日%s' % tuple(y_m_d + [additional])

    def format2(y_m_d, score):
        additional = '(共%s件)' % score if score>1 else ''
        return '%d月%d日%s' % tuple(y_m_d[1:] + [additional])

    def get_date_score_list(date_list, score_list): # each day
        date_list_ = [json.dumps(l) for l in date_list]
        date_score = list(zip(date_list_, score_list))
        dd = pd.DataFrame(date_score)
        stat = dd.groupby(0, sort=False).agg({1:sum}).reset_index()
        stat.iloc[:,0] = stat.iloc[:,0].map(lambda x: json.loads(x))
        stat = stat.values.tolist()
        return stat

    date_score_list = get_date_score_list(date_list, score_list)
    date_list_stat = [y_m_d for y_m_d, score in date_score_list]
    this_year_first = [is_this_year_first(e, date_list_stat) for e in date_list_stat]
    split_index = [e[0] for e in filter(lambda x: x[1], enumerate(this_year_first))][-1]

    if split_index != 0:
        first_half = date_score_list[:split_index]
        second_half = date_score_list[split_index:]
        str1 = '、'.join([format1(e, score, True) if is_this_year_first(e, date_list) else format2(e, score) for e, score in first_half])
        str2 = '、'.join([format1(e, score, True) if is_this_year_first(e, date_list) else format2(e, score) for e, score in second_half])
        str_final = '%s及%s' % (str1, str2)
    else:
        str_final = '、'.join([format1(e, score, True) if is_this_year_first(e, date_list) else format2(e, score) for e, score in date_score_list])
    return str_final


def exp_each_award(date_minguo, content):
    verb = '發現' if content.startswith('小型動物') else '查核旅客' 
    words = f'{date_minguo}{verb}{content}'
    return words

import pandas as pd
import numpy as np
from pulp import *

def do_recomendation():
    data = pd.read_excel('predict.xlsx')

    # Группировка данных по 'Наименование структурного подразделения' и 'Тип закрепления'
    all_combinations_2 = pd.MultiIndex.from_product([data['Наименование структурного подразделения'].unique(), data['Номерной знак ТС'].unique(), data['Тип закрепления'].unique()], names=['Наименование структурного подразделения', 'Номерной знак ТС', 'Тип закрепления'])

    grouped_2 = data.groupby(['Наименование структурного подразделения', 'Номерной знак ТС', 'Тип закрепления']).size().reset_index(name='Количество')
    pivot_table = grouped_2.pivot_table(index=['Наименование структурного подразделения', 'Номерной знак ТС'], columns='Тип закрепления', values='Количество', fill_value=0).reset_index()

    for index, row in pivot_table.iterrows():
        if pd.isnull(row['Прочие']):
            pivot_table.at[index, 'Прочие'] = 0
    #print(pivot_table, 'pivot')
    pivot_table['Общее'] = pivot_table['Прочие'] + pivot_table['В целевой структуре парка']
    pivot_table['Общее_по_только_машине'] = pivot_table['Прочие'] + pivot_table['В целевой структуре парка']

    total_sum = pivot_table.groupby('Наименование структурного подразделения')['Общее'].transform('sum')
    total_min = pivot_table.groupby('Наименование структурного подразделения')['Общее'].transform('min')
    total_mean = pivot_table.groupby('Наименование структурного подразделения')['Общее'].transform('mean')

    pivot_table['Общее'] = total_sum
    pivot_table['Среднее по подразделению'] = total_mean
    pivot_table['Минимальное по подразделению'] = total_min
    pivot_table['Индекс'] = pivot_table['Общее_по_только_машине'] - (pivot_table['Среднее по подразделению'] + pivot_table['Минимальное по подразделению']) / 2

    pivot_table = pivot_table.replace([np.inf, -np.inf], 0)

    # Проверка наличия столбца 'Индекс'
    if 'Индекс' not in pivot_table.columns:
        raise KeyError("Столбец 'Индекс' не найден в DataFrame")

    # Линейное программирование
    df = pivot_table

    prob = LpProblem("Maximize_Index", LpMaximize)

    # Переменные и их ограничения
    transfer_vars = LpVariable.dicts("Transfer", df.index, cat='Binary')
    for i in df.index:
        condition = df.at[i, 'Индекс'] < 0
        prob += transfer_vars[i] == int(condition)  # Преобразуем булевое значение в целое

    # Целевая функция
    prob += lpSum([df.at[i, 'Индекс'] * transfer_vars[i] for i in df.index])

    # Решение задачи
    prob.solve()

    # Формирование итоговых данных
    recommendations = []
    for i in df.index:
        if value(transfer_vars[i]):
            if df.at[i, 'В целевой структуре парка'] > 0:
                recommendation = 'В целевой структуре парка'
            else:
                recommendation = 'Прочие'
            recommendations.append([
                df.at[i, 'Номерной знак ТС'],
                recommendation,
                df.at[i, 'Наименование структурного подразделения']
            ])
    recommendations = [['НомерМашины', 'Рекомендация на переход куда', 'Наименование структурного подразделения']] +recommendations
    return(recommendations)


f = do_recomendation()
print(f)
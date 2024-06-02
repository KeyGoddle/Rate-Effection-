from itertools import combinations
import sys
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pulp import *
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QTabWidget
import pandas as pd
o1 = []
o4 = []
f = []

S = 5  # ______

# inp='по условию'#_____
inp = 'по следствию'  # _____
import pandas as pd
import lightgbm as lgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import numpy as np
from sklearn.preprocessing import LabelEncoder
from transliterate import translit


def inverse_transform_all_columns(encoders, encoded_data):
    decoded_data = encoded_data.copy()
    for col, encoder in encoders.items():
        decoded_data[col] = encoder.inverse_transform(encoded_data[col])
    return decoded_data


def prepare_data():
    # Загрузка данных
    df = pd.read_csv('Обработанные.csv')
    df = df.drop(columns=['Дата сигнала телематики', 'Unnamed: 0'])
    df = df.drop(columns=['Данные путевых листов, пробег', 'Данные телематики, пробег', 'Штрафы', 'манера вождения'])
    df['дата путевого листа'] = pd.to_datetime(df['дата путевого листа'])
    df['дата путевого листа'] = df['дата путевого листа'] + pd.DateOffset(months=1)
    max_value = df['дата путевого листа'].max()
    # print(df)
    df[['Наименование полигона', 'Краткое наименование', 'Полигон', 'Номерной знак ТС',
        'Наименование структурного подразделения', 'Тип закрепления', 'дата путевого листа']] = df[
        ['Наименование полигона', 'Краткое наименование', 'Полигон', 'Номерной знак ТС',
         'Наименование структурного подразделения', 'Тип закрепления', 'дата путевого листа']].fillna('Nan')
    # Кодирование категориальных признаков в int
    # print(df)
    categorical_columns = ['Наименование полигона', 'Краткое наименование', 'Полигон', 'Номерной знак ТС',
                           'Наименование структурного подразделения', 'Тип закрепления', 'дата путевого листа']
    label_encoders = {}
    for col in categorical_columns:
        label_encoders[col] = LabelEncoder()
        df[col] = label_encoders[col].fit_transform(df[col].astype(str))

    # Определение признаков (features) и меток (labels) для каждой целевой переменной
    features = df

    # Определение целевых переменных
    label_columns = ['Данные путевых листов, пробег', 'Данные телематики, пробег', 'Штрафы', 'манера вождения']
    return features, label_encoders


def do_first(features, label_encoders):
    # Создание словарей для моделей и прогнозов
    models = {}
    predictions = {}
    label_columns = ['Данные путевых листов, пробег', 'Данные телематики, пробег', 'Штрафы', 'манера вождения']
    # Загрузка и использование предварительно обученной модели для каждой целевой переменной
    for col in label_columns:
        # Загрузка модели из файла
        name_file_model = col.replace(' ', '_')
        name_file_model = name_file_model.replace(',', '_')
        name_file_model = name_file_model.replace('__', '_')
        name_file_model = translit(name_file_model, 'ru', reversed=True)
        model = lgb.Booster(model_file=f'model_first_{name_file_model}.txt')

        # Прогнозирование с помощью загруженной модели
        preds = model.predict(features)
        predictions[col] = np.abs(preds)

        # Вывод результатов
        # print(f"Прогноз для переменной '{col}':")
        # print(predictions[col])

    final_predictions_df = pd.DataFrame(predictions)
    # df_fact=pd.DataFrame(fact)
    columns_to_round_one_znak = ['манера вождения']
    columns_to_round = ['Штрафы', 'Данные путевых листов, пробег', 'Данные телематики, пробег']
    # print(final_predictions_df, 'округление')
    final_predictions_df[columns_to_round] = final_predictions_df[columns_to_round].round().astype(int)
    final_predictions_df[columns_to_round_one_znak] = final_predictions_df[columns_to_round_one_znak].round(decimals=1)
    # final_predictions_df = final_predictions_df.round().astype(int)
    decoded_df = inverse_transform_all_columns(label_encoders, features)
    decoded_df = decoded_df.reset_index(drop=True)

    # print (final_predictions_df,decoded_df)
    merged_df = decoded_df.merge(final_predictions_df, left_index=True, right_index=True)
    # print (merged_df)
    # merged_df.to_excel('output.xlsx')
    return merged_df


def do_secod_null(features):
    # Создание словарей для моделей и прогнозов
    models = {}
    predictions = {}
    label_columns = ['Данные путевых листов, пробег', 'Данные телематики, пробег', 'Штрафы', 'манера вождения']
    # Загрузка и использование предварительно обученной модели для каждой целевой переменной
    for col in label_columns:
        # Загрузка модели из файла

        name_file_model = col.replace(' ', '_')
        name_file_model = name_file_model.replace(',', '_')
        name_file_model = name_file_model.replace('__', '_')
        name_file_model = translit(name_file_model, 'ru', reversed=True)
        model = lgb.Booster(model_file=f'model_second_{name_file_model}.txt')

        # Прогнозирование с помощью загруженной модели
        preds = model.predict(features)
        predictions[col] = np.abs(preds)

        # Вывод результатов
        # print(f"Прогноз для переменной '{col}':")
        # print(predictions[col])

    final_predictions_df = pd.DataFrame(predictions)
    final_predictions_df = final_predictions_df.round().astype(int)

    # Замена нулевых значений на NaN
    final_predictions_df = final_predictions_df.replace(0, np.nan)
    # final_predictions_df.to_excel('fucking_null.xlsx')
    # print(final_predictions_df)
    return final_predictions_df


def do_all_predictions():
    features, label_encoders = prepare_data()
    data_df = do_first(features, label_encoders)
    null_df = do_secod_null(features)
    columns_to_filter = ['Данные путевых листов, пробег', 'Данные телематики, пробег', 'Штрафы', 'манера вождения']
    not_filter = ['Наименование полигона', 'Краткое наименование', 'Полигон', 'Номерной знак ТС',
                  'Наименование структурного подразделения', 'Тип закрепления', 'дата путевого листа']
    # Применяем операцию where только к выбранным столбцам
    result = data_df.copy()
    result.loc[:, columns_to_filter] = data_df[columns_to_filter].where(null_df[columns_to_filter] == 1,
                                                                        other=data_df[not_filter])
    # print(result)
    result.replace('Nan', np.nan, inplace=True)
    result.to_excel('predict.xlsx',index= False)

def file(y):
    df = pd.DataFrame(pd.read_excel(f'{y}'))
    array = list(df.values)
    array1 = []
    array1.append(['', 'Наименование полигона', 'Краткое наименование', 'Полигон', 'Номерной знак ТС',
                   'Наименование структурного подразделения', 'Тип закрепления', 'дата путевого листа',
                   'Данные путевых листов', 'Дата сигнала телематики', 'Данные телематики, пробег', 'Штрафы',
                   'манера вождения', 'Rating', 'P_coef', 'C_coef', 'S_coef', 'MV_coef'])
    for item in array:
        array1.append(list(item))
    f = array1

    # f = []
    # v = open(f'{y}', 'r', encoding='ANSI')  # ______
    #
    # for line in v:
    #     f.append(line.strip("\n").split('|')[1])
    del f[0]
    # print(f)
    return f


def file1(y):
    df = pd.DataFrame(pd.read_excel(f'{y}'))
    array = list(df.values)
    array1 = []
    array1.append(["",	"Наименование полигона", "Краткое наименование",	"Полигон",	"Номерной знак ТС",	"Наименование структурного подразделения",	"Тип закрепления",	"дата путевого листа",	"Данные путевых листов, пробег",	"Дата сигнала телематики",	"Данные телематики, пробег",	"Штрафы",	"манера вождения"])
    for item in array:
        array1.append(list(item))
    f1 = array1
    # f1 = []
    # v = open(f'{y}', 'r', encoding='ANSI')  # ______
    # for line in v:
    #     f1.append(line.strip("\n").split('|'))
    print(f1[0])
    return f1

def file2(y):
    df = pd.DataFrame(pd.read_excel(f'{y}'))
    array = list(df.values)
    array1 = []
    array1.append(["Наименование полигона",	"Краткое наименование",	"Полигон",	"Номерной знак ТС", "Наименование структурного подразделения",	"Тип закрепления",	"дата путевого листа",	"Данные путевых листов, пробег", "Данные телематики, пробег",	"Штрафы",	"манера вождения"])
    for item in array:
        print(f'1111111111 {item}')
        array1.append(list(item))
    f1 = array1
    # f1 = []
    # v = open(f'{y}', 'r', encoding='ANSI')  # ______
    # for line in v:
    #     f1.append(line.strip("\n").split('|'))
    print(f1[0])
    return f1

def plot_example_1():
        # Загрузка данных из файла Excel
        data = pd.read_excel('predict.xlsx')

        # Группировка данных по 'Наименование структурного подразделения' и 'Тип закрепления'
        all_combinations = pd.MultiIndex.from_product(
            [data['Наименование структурного подразделения'].unique(), data['Тип закрепления'].unique()],
            names=['Наименование структурного подразделения', 'Тип закрепления']
        )
        all_combinations_df = pd.DataFrame(index=all_combinations).reset_index()

        # Группируем исходные данные
        grouped = data.groupby(['Наименование структурного подразделения', 'Тип закрепления']).size().reset_index(
            name='Количество')

        # Объединяем группированные данные с полным набором комбинаций
        merged_data = pd.merge(all_combinations_df, grouped,
                               on=['Наименование структурного подразделения', 'Тип закрепления'], how='left')

        # Заполняем отсутствующие значения нулями
        merged_data['Количество'] = merged_data['Количество'].fillna(0).astype(int)

        # Создание столбчатой диаграммы с Plotly
        fig = px.bar(merged_data, x="Наименование структурного подразделения", y="Количество", color="Тип закрепления",
                     title="Количество транспорта в целевой структуре / прочие")

        # Настройка осей и поворот меток
        fig.update_layout(xaxis_title="Наименование структурного подразделения",
                          yaxis_title="Количество",
                          xaxis_tickangle=-45,
                          font=dict(size=12))

        # Добавление кастомного CSS для изменения цвета текста при наведении на красный
        custom_css = """
        <style>
        .plotly .hoverlayer .bg {
            fill-opacity: 0.7 !important;
        }
        .plotly .hoverlayer .hovertext {
            fill: white !important;
        }
        </style>
        """

        # Конвертация графика в HTML и добавление кастомного CSS
        html = fig.to_html(include_plotlyjs='cdn')
        html = html.replace('<body>', f'<body>{custom_css}')

        # Загрузка HTML в QWebEngineView
        return(html)
def plot_example_2():
        data = pd.read_excel('predict.xlsx')

        # Группировка данных по 'Наименование структурного подразделения' и 'Тип закрепления'
        all_combinations = pd.MultiIndex.from_product(
            [data['Наименование структурного подразделения'].unique(), data['Тип закрепления'].unique()],
            names=['Наименование структурного подразделения', 'Тип закрепления']
        )
        all_combinations_df = pd.DataFrame(index=all_combinations).reset_index()

        # Группируем исходные данные
        grouped = data.groupby(['Наименование структурного подразделения', 'Тип закрепления']).size().reset_index(
            name='Количество')

        # Объединяем группированные данные с полным набором комбинаций
        merged_data = pd.merge(all_combinations_df, grouped,
                               on=['Наименование структурного подразделения', 'Тип закрепления'], how='left')

        # Заполняем отсутствующие значения нулями
        merged_data['Количество'] = merged_data['Количество'].fillna(0).astype(int)
        grouped_mean = data.groupby('Наименование структурного подразделения').mean().reset_index()
        grouped_mean['Путевые_листы'] = abs(
            grouped_mean['Данные путевых листов, пробег'] / grouped_mean['Данные телематики, пробег'] - 1)
        grouped_mean['Путевые_листы'] = abs(
            grouped_mean['Данные путевых листов, пробег'] / grouped_mean['Данные телематики, пробег'] - 1)

        # Применяем условные операторы с помощью метода apply
        def apply_conditions(x):
            if x > 0.2:
                return 0.6
            elif x > 0.1:
                return 0.7
            elif x > 0.05:
                return 0.8
            else:
                return 1

        def apply_conditions_driving(x):
            if x == 0:
                return 1
            elif x < 0.1:
                return 0.9
            elif x < 0.15:
                return 0.8
            elif x < 0.20:
                return 0.7
            elif x == 1:
                return 0
            else:
                return 0.7

        def apply_conditions_shtraf(x):
            if x > 1:
                return 0.7
            else:
                return 0.9

        grouped_mean['Путевые_листы_coef'] = grouped_mean['Путевые_листы'].apply(apply_conditions)

        grouped_mean['манера вождения'] = abs(grouped_mean['манера вождения'] / 6 - 1)
        grouped_mean['манера вождения_coef'] = grouped_mean['манера вождения'].apply(apply_conditions_driving)
        grouped_mean['Штрафы_coef'] = (abs(grouped_mean['Штрафы'] / grouped_mean['Штрафы'].mean())).apply(
            apply_conditions_shtraf)

        total_counts = merged_data.groupby('Наименование структурного подразделения')['Количество'].sum().reset_index()
        vrem = merged_data[merged_data['Тип закрепления'] == 'В целевой структуре парка']
        vrem = vrem.sort_values(by='Наименование структурного подразделения', ascending=False)
        vrem = vrem.reset_index(drop=True)
        total_counts = total_counts.sort_values(by='Наименование структурного подразделения', ascending=False)
        total_counts = total_counts.reset_index(drop=True)
        total_counts['соответствие целевой структуре'] = abs(total_counts['Количество'] / vrem['Количество'] - 1)
        total_counts['соответствие целевой структуре_coef'] = total_counts['соответствие целевой структуре'].apply(
            apply_conditions)

        result_rating = pd.merge(total_counts, grouped_mean, on="Наименование структурного подразделения", how='inner')
        result_rating = result_rating.drop(
            columns=['Количество', 'соответствие целевой структуре', 'Данные путевых листов, пробег',
                     'Данные телематики, пробег', 'Штрафы', 'манера вождения', 'Путевые_листы'])
        result_rating['Общий рейтинг'] = result_rating['Путевые_листы_coef'] * 0.4 + result_rating[
            'соответствие целевой структуре_coef'] * 0.3 + result_rating['манера вождения_coef'] * 0.15 + result_rating[
                                             'манера вождения_coef'] * 0.15

        # Сортировка данных по общему рейтингу
        result_rating_sorted = result_rating.sort_values(by='Общий рейтинг', ascending=True)

        # Построение столбчатой диаграммы с градиентной шкалой цветов
        fig = px.bar(result_rating_sorted, x='Общий рейтинг', y='Наименование структурного подразделения',
                     orientation='h', title='Общий рейтинг структурных подразделений',
                     color='Общий рейтинг', color_continuous_scale='RdYlGn')

        fig.update_layout(xaxis_title='Общий рейтинг',
                          yaxis_title='Наименование структурного подразделения',
                          yaxis_tickfont=dict(size=15))
        # Устанавливаем размер шрифта для текста по оси Y
        fig.update_yaxes(title_font=dict(size=17))
        fig.update_xaxes(title_font=dict(size=17))

        # Конвертация графика в HTML
        html = fig.to_html(include_plotlyjs='cdn')

        # Загрузка HTML в QWebEngineView
        return html

def plot_example_3():
    data = pd.read_excel('predict.xlsx')
    grouped_mean = data.groupby('Наименование структурного подразделения').mean().reset_index()
    # Создание фигуры
    fig = go.Figure()

    # Добавление следов на график

    fig.add_trace(go.Bar(
        y=grouped_mean['Наименование структурного подразделения'],
        x=grouped_mean['Штрафы'],
        name='Штрафы',
        orientation='h',  # задаем горизонтальную ориентацию
        marker_color='lightseagreen'
    ))

    fig.add_trace(go.Bar(
        y=grouped_mean['Наименование структурного подразделения'],
        x=grouped_mean['манера вождения'],
        name='Манера вождения',
        orientation='h',  # задаем горизонтальную ориентацию
        marker_color='lightskyblue'
    ))

    # Настройка макета
    fig.update_layout(
        title='Сравнение данных по структурным подразделениям',
        # поворачиваем метки на оси y
        yaxis=dict(
            title='Наименование структурного подразделения',
            tickfont=dict(size=10)
        ),
        xaxis=dict(
            title='Значения'
        ),
        barmode='group'
    )

    # Конвертация графика в HTML
    html = fig.to_html(include_plotlyjs='cdn')
    return html
def plot_example_4():
        data = pd.read_excel('predict.xlsx')
        grouped_mean = data.groupby('Наименование структурного подразделения').mean().reset_index()
        # Создание фигуры
        fig = go.Figure()

        # Добавление следов на график


        fig.add_trace(go.Bar(
            y=grouped_mean['Наименование структурного подразделения'],
            x=grouped_mean['Данные телематики, пробег'],
            name='Данные телематики, пробег',
            orientation='h',  # задаем горизонтальную ориентацию
            marker_color='peachpuff'
        ))

        fig.add_trace(go.Bar(
            y=grouped_mean['Наименование структурного подразделения'],
            x=grouped_mean['Данные путевых листов, пробег'],
            name='Данные путевых листов, пробег',
            orientation='h',  # задаем горизонтальную ориентацию
            marker_color='lightcoral'
        ))

        # Настройка макета
        fig.update_layout(
            title='Сравнение данных по структурным подразделениям',
             # поворачиваем метки на оси y
            yaxis=dict(
                title='Наименование структурного подразделения',
                tickfont=dict(size=10)
            ),
            xaxis=dict(
                title='Значения'
            ),
            barmode='group'
        )



        # Конвертация графика в HTML
        html = fig.to_html(include_plotlyjs='cdn')

        # Загрузка HTML в QWebEngineView
        return(html)


def do_recomendation():
    data = pd.read_excel('predict.xlsx')

    # Группировка данных по 'Наименование структурного подразделения' и 'Тип закрепления'
    all_combinations_2 = pd.MultiIndex.from_product(
        [data['Наименование структурного подразделения'].unique(), data['Номерной знак ТС'].unique(),
         data['Тип закрепления'].unique()],
        names=['Наименование структурного подразделения', 'Номерной знак ТС', 'Тип закрепления'])

    grouped_2 = data.groupby(
        ['Наименование структурного подразделения', 'Номерной знак ТС', 'Тип закрепления']).size().reset_index(
        name='Количество')
    pivot_table = grouped_2.pivot_table(index=['Наименование структурного подразделения', 'Номерной знак ТС'],
                                        columns='Тип закрепления', values='Количество', fill_value=0).reset_index()

    for index, row in pivot_table.iterrows():
        if pd.isnull(row['Прочие']):
            pivot_table.at[index, 'Прочие'] = 0
    # print(pivot_table, 'pivot')
    pivot_table['Общее'] = pivot_table['Прочие'] + pivot_table['В целевой структуре парка']
    pivot_table['Общее_по_только_машине'] = pivot_table['Прочие'] + pivot_table['В целевой структуре парка']

    total_sum = pivot_table.groupby('Наименование структурного подразделения')['Общее'].transform('sum')
    total_min = pivot_table.groupby('Наименование структурного подразделения')['Общее'].transform('min')
    total_mean = pivot_table.groupby('Наименование структурного подразделения')['Общее'].transform('mean')

    pivot_table['Общее'] = total_sum
    pivot_table['Среднее по подразделению'] = total_mean
    pivot_table['Минимальное по подразделению'] = total_min
    pivot_table['Индекс'] = pivot_table['Общее_по_только_машине'] - (
                pivot_table['Среднее по подразделению'] + pivot_table['Минимальное по подразделению']) / 2

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
    recommendations = [['НомерМашины', 'Рекомендация на переход',
                        'Наименование структурного подразделения']] + recommendations
    return (recommendations)


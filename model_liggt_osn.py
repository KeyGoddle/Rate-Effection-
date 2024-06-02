import pandas as pd
import lightgbm as lgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import numpy as np
from sklearn.preprocessing import LabelEncoder
from transliterate import translit
import pandas as pd
import numpy as np
class Prepare_data:
    def load_data():
        def find_lines_before_blank_rows(df):
                lines_before_blanks = []
                for i in range(len(df) - 1):
                    current_row = df.iloc[i]
                    next_row = df.iloc[i + 1]
                    if (next_row.isnull().all() or (next_row.astype(str).str.strip() == '').all()) and not (current_row.isnull().all() or (current_row.astype(str).str.strip() == '').all()):
                        lines_before_blanks.append(i)
                return lines_before_blanks

        file_ = 'dataset.xlsx'
        data = pd.read_excel(file_, sheet_name=None)
        df_vehicles = data['22.05.2024']
        
        # Удаление ненужных колонок
        df_vehicles.drop(['Выполняемые функции','Должность за кем закреплен ТС'], axis=1, inplace=True)

        errase_df=df_vehicles.drop(columns=['Данные путевых листов, пробег', 'Данные телематики, пробег', 'Штрафы', 'манера вождения','дата путевого листа', 'Дата сигнала телематики'])
        print (errase_df)
        lines_before_blank_rows = find_lines_before_blank_rows(errase_df)
        print (lines_before_blank_rows)
        # Заполнение пустых значений только в строках, где все значения пустые
        #df_vehicles.loc[~non_empty_rows, ['Наименование полигона', 'Краткое наименование', 'Полигон', 'Номерной знак ТС', 'Наименование структурного подразделения', 'Тип закрепления']] = df_vehicles.loc[~non_empty_rows, ['Наименование полигона', 'Краткое наименование', 'Полигон', 'Номерной знак ТС', 'Наименование структурного подразделения', 'Тип закрепления']].fillna(method='bfill')
        df_vehicles['Наименование полигона']=df_vehicles['Наименование полигона'].fillna(method='ffill')
        df_vehicles['Краткое наименование']=df_vehicles['Краткое наименование'].fillna(method='ffill')
        df_vehicles['Полигон']=df_vehicles['Полигон'].fillna(method='ffill')
        df_vehicles['Номерной знак ТС']=df_vehicles['Номерной знак ТС'].fillna(method='ffill')
        df_vehicles['Наименование структурного подразделения']=df_vehicles['Наименование структурного подразделения'].fillna(method='ffill')
        # Заполняем пропущенные значения методом ffill
        df_vehicles['манера вождения']=df_vehicles['манера вождения'].fillna(method='ffill')
        df_vehicles['Тип закрепления'] = df_vehicles['Тип закрепления'].fillna(method='ffill')
        # Удаляем строки, которые изначально содержали пропуски
        column_to_filter=['Номерной знак ТС']
        print (len(df_vehicles),df_vehicles[df_vehicles[column_to_filter] == 'Б/Н'].index)
        df_vehicles.drop(df_vehicles.loc[df_vehicles['Номерной знак ТС']== 'Б/Н'].index, inplace=True)
        # Создание индексации для заполнения номеров
        print (df_vehicles['Тип закрепления'])
        return df_vehicles



def prepare():

    df_vehicles=Prepare_data.load_data()
    
    # Применение функции для каждого ряда
    #df_vehicles[['Rating', 'P_coef', 'C_coef', 'S_coef', 'MV_coef']] = df_vehicles.apply(Calculate_params.calc_vehicle_rating, axis=1, result_type='expand')
    df_vehicles['манера вождения'] = df_vehicles.groupby('Номерной знак ТС')['манера вождения'].transform(
        lambda x: x.fillna(x.median())
    )

    # Если все значения в группе NaN, можно заменить их на общую медиану
    overall_median = df_vehicles['манера вождения'].median()
    df_vehicles['манера вождения'] = df_vehicles['манера вождения'].fillna(overall_median)

    # Проверка результата
    print(df_vehicles[['Номерной знак ТС', 'манера вождения']].head())
    print (df_vehicles)
    df_vehicles.to_csv('Обработанные.csv')
    df_vehicles.to_excel('Обработанные.xlsx')
    return df_vehicles


def inverse_transform_all_columns(encoders, encoded_data):
    """
    Выполняет обратное преобразование для всех столбцов, закодированных с использованием LabelEncoder.

    Параметры:
    encoders : dict
        Словарь, где ключами являются названия столбцов, а значениями - соответствующие экземпляры LabelEncoder.
    encoded_data : pandas.DataFrame
        DataFrame с закодированными значениями.

    Возвращает:
    pandas.DataFrame
        DataFrame с исходными значениями до кодирования.
    """
    decoded_data = encoded_data.copy()
    for col, encoder in encoders.items():
        decoded_data[col] = encoder.inverse_transform(encoded_data[col])
    return decoded_data

params = {
    'objective': 'regression',  # тип задачи: регрессия
    'metric': 'mse',            # метрика качества: среднеквадратичная ошибка
    'verbosity': -1             # уровень логирования
}
def do_first(df):
    # Загрузка данных
    #df = pd.read_csv('Обработанные.csv')
    df = df.drop(columns=['Дата сигнала телематики'])

    group_columns = [
        'Наименование полигона', 'Краткое наименование', 'Полигон', 
        'Номерной знак ТС', 'Наименование структурного подразделения', 'Тип закрепления'
    ]
    mean_values_list_rpob = df.groupby(group_columns)['Данные путевых листов, пробег'].transform('mean')

    # Заполняем пустые значения средними значениями
    df['Данные путевых листов, пробег'] = df['Данные путевых листов, пробег'].fillna(mean_values_list_rpob)

    mean_values_shtrafy = df.groupby(group_columns)['Штрафы'].transform('mean')
    df['Штрафы'] = df['Штрафы'].fillna(mean_values_shtrafy)

    mean_values_manera= df.groupby(group_columns)['манера вождения'].transform('mean')
    df['манера вождения'] = df['манера вождения'].fillna(mean_values_manera)

    mean_values_tele = df.groupby(group_columns)['Данные телематики, пробег'].transform('mean')

    df['Данные телематики, пробег'] = df['Данные телематики, пробег'].fillna(mean_values_tele)

    df[['Наименование полигона', 'Краткое наименование', 'Полигон', 'Номерной знак ТС', 
                        'Наименование структурного подразделения', 'Тип закрепления', 'дата путевого листа']]=df[['Наименование полигона', 'Краткое наименование', 'Полигон', 'Номерной знак ТС', 
                        'Наименование структурного подразделения', 'Тип закрепления', 'дата путевого листа']].fillna('Nan')
    # Кодирование категориальных признаков в int
    categorical_columns = ['Наименование полигона', 'Краткое наименование', 'Полигон', 'Номерной знак ТС', 
                        'Наименование структурного подразделения', 'Тип закрепления', 'дата путевого листа']
    label_encoders = {}
    for col in categorical_columns:
        label_encoders[col] = LabelEncoder()
        df[col] = label_encoders[col].fit_transform(df[col].astype(str))

    # Определение признаков (features) и меток (labels) для каждой целевой переменной
    features = df.drop(columns=['Данные путевых листов, пробег', 'Данные телематики, пробег', 'Штрафы', 'манера вождения'])

    label_columns = ['Данные путевых листов, пробег', 'Данные телематики, пробег', 'Штрафы', 'манера вождения']

    # Обучение модели LightGBM для каждой целевой переменной и прогнозирование
    for col in label_columns:
        if col=='Данные телематики, пробег' or col=='Данные путевых листов, пробег':
            df[col]=df[col].fillna(df[col].mean())
        else:
            df[col]=df[col].fillna(0)

        train_data = lgb.Dataset(features, label=df[col])      
        print ('длинна',len(df[col]),len(features) )

        model = lgb.train(params, train_data)           #, valid_sets=[train_data, test_data])
        name_file_model = col.replace(' ', '_')
        name_file_model = name_file_model.replace(',', '_')
        name_file_model = name_file_model.replace('__', '_')
        name_file_model = translit(name_file_model, 'ru', reversed=True)
        model.save_model(f'model_first_{name_file_model}.txt') 
     
    return 0

def do_second_null(df_2):
    params = {
        'objective': 'regression',  # тип задачи: регрессия
        'metric': 'mse',            # метрика качества: среднеквадратичная ошибка
        'verbosity': -1             # уровень логирования
    }

    # Загрузка данных
    #df_2 = pd.read_csv('Обработанные.csv')
    df_2 = df_2.drop(columns=['Дата сигнала телематики'])#,'Rating', 'P_coef', 'C_coef', 'S_coef', 'MV_coef' ])

    # Кодирование категориальных признаков в int
    categorical_columns = ['Наименование полигона', 'Краткое наименование', 'Полигон', 'Номерной знак ТС', 
                        'Наименование структурного подразделения', 'Тип закрепления', 'дата путевого листа']
    label_encoders = {}
    for col in categorical_columns:
        label_encoders[col] = LabelEncoder()
        df_2[col] = label_encoders[col].fit_transform(df_2[col].astype(str))

    # Определение признаков (features) и меток (labels) для каждой целевой переменной
    features = df_2.drop(columns=['Данные путевых листов, пробег', 'Данные телематики, пробег', 'Штрафы', 'манера вождения'])
    features=features.fillna('-1')
    label_columns = ['Данные путевых листов, пробег', 'Данные телематики, пробег', 'Штрафы', 'манера вождения']

    # Обучение модели LightGBM для каждой целевой переменной и прогнозирование
    for col in label_columns:
        df_2[col]=df_2[col].notnull().astype('int')
        df_2[col]=df_2[col].fillna(0)

        train_data = lgb.Dataset(features, label=df_2[col])       #y_train
        model = lgb.train(params, train_data)     
        name_file_model = col.replace(' ', '_')
        name_file_model = name_file_model.replace(',', '_')
        name_file_model = name_file_model.replace('__', '_')
        name_file_model = translit(name_file_model, 'ru', reversed=True)
        model.save_model(f'model_second_{name_file_model}.txt') 

    return 0



if __name__ == "__main__":
    df=prepare()
    do_first(df)
    do_second_null(df)



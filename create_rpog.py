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
    df =df.drop(columns=['Данные путевых листов, пробег', 'Данные телематики, пробег', 'Штрафы', 'манера вождения']) 
    df['дата путевого листа'] = pd.to_datetime(df['дата путевого листа'])
    df['дата путевого листа'] = df['дата путевого листа'] + pd.DateOffset(months=1)
    max_value = df['дата путевого листа'].max()
    print (df)
    df[['Наименование полигона', 'Краткое наименование', 'Полигон', 'Номерной знак ТС', 
                        'Наименование структурного подразделения', 'Тип закрепления', 'дата путевого листа']]=df[['Наименование полигона', 'Краткое наименование', 'Полигон', 'Номерной знак ТС', 
                        'Наименование структурного подразделения', 'Тип закрепления', 'дата путевого листа']].fillna('Nan')
    # Кодирование категориальных признаков в int
    print (df)
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
    return features,label_encoders
def do_first(features,label_encoders):
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
        print(f"Прогноз для переменной '{col}':")
        print(predictions[col])
        
    final_predictions_df = pd.DataFrame(predictions)
    #df_fact=pd.DataFrame(fact)
    columns_to_round_one_znak=['манера вождения']
    columns_to_round=['Штрафы', 'Данные путевых листов, пробег' , 'Данные телематики, пробег']
    print(final_predictions_df,'округление')
    final_predictions_df[columns_to_round] = final_predictions_df[columns_to_round].round().astype(int)
    final_predictions_df[columns_to_round_one_znak] = final_predictions_df[columns_to_round_one_znak].round(decimals=1)
    #final_predictions_df = final_predictions_df.round().astype(int)
    decoded_df = inverse_transform_all_columns(label_encoders, features)
    decoded_df = decoded_df.reset_index(drop=True)

    #print (final_predictions_df,decoded_df)
    merged_df = decoded_df.merge( final_predictions_df, left_index=True, right_index=True)
    #print (merged_df)
    #merged_df.to_excel('output.xlsx')
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
        print(f"Прогноз для переменной '{col}':")
        print(predictions[col])
        
    final_predictions_df = pd.DataFrame(predictions)
    final_predictions_df = final_predictions_df.round().astype(int)

    # Замена нулевых значений на NaN
    final_predictions_df = final_predictions_df.replace(0, np.nan)
    #final_predictions_df.to_excel('fucking_null.xlsx')
    #print(final_predictions_df)
    return final_predictions_df

def do_all_predictions():
    features,label_encoders=prepare_data()
    data_df=do_first(features,label_encoders)
    null_df=do_secod_null(features)
    columns_to_filter = ['Данные путевых листов, пробег' , 'Данные телематики, пробег', 'Штрафы' , 'манера вождения']
    not_filter=['Наименование полигона', 'Краткое наименование', 'Полигон' ,'Номерной знак ТС', 'Наименование структурного подразделения' ,'Тип закрепления' ,'дата путевого листа']
    # Применяем операцию where только к выбранным столбцам
    result = data_df.copy()
    result.loc[:, columns_to_filter] = data_df[columns_to_filter].where(null_df[columns_to_filter] == 1, other=data_df[not_filter])
    #print(result)
    result.replace('Nan', np.nan, inplace=True)
    result.to_excel('fucking_result_prediction.xlsx')

if __name__ == "__main__":
    do_all_predictions()
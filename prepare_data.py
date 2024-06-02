# -*- coding: utf-8 -*-

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
        print (df_vehicles[df_vehicles['Номерной знак ТС']=='0044НО50'],'stroka')
        # Удаление ненужных колонок
        df_vehicles.drop(['Выполняемые функции','Должность за кем закреплен ТС'], axis=1, inplace=True)
        
        # Поиск строк, где все нужные значения не пустые

        errase_df=df_vehicles.drop(columns=['Данные путевых листов, пробег', 'Данные телематики, пробег', 'Штрафы', 'манера вождения','дата путевого листа', 'Дата сигнала телематики'])
        #print (errase_df)
        lines_before_blank_rows = find_lines_before_blank_rows(errase_df)
        #print (lines_before_blank_rows)
        
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
        df_vehicles = df_vehicles.drop (index=lines_before_blank_rows)
        #print (len(df_vehicles),df_vehicles[df_vehicles[column_to_filter] == 'Б/Н'].index)
        
        df_vehicles.drop(df_vehicles.loc[df_vehicles['Номерной знак ТС']== 'Б/Н'].index, inplace=True)
        # Создание индексации для заполнения номеров
        #print (df_vehicles,'Проверка')
        return df_vehicles


class Calculate_param:
    def calc_probeg_coef(self,probeg_p, probeg_t):
        if probeg_t == 0:
            return 0  # или другое значение, если телематика не работает
        deviation = abs(probeg_p / probeg_t - 1)
        if deviation > 0.20:
            return 0.4
        elif deviation > 0.10:
            return 0.3
        elif deviation > 0.05:
            return 0.2
        else:
            return 1

    def calc_structure_coef(self,structure_ratio):
        deviation = abs(structure_ratio - 1)
        if deviation > 0.20:
            return 0.4
        elif deviation > 0.10:
            return 0.3
        elif deviation > 0.05:
            return 0.2
        else:
            return 1

    def calc_penalties_coef(self,penalties):
        if penalties > 0.25:
            return 0.3
        elif penalties > 0.15:
            return 0.2
        elif penalties > 0.05:
            return 0.1
        else:
            return 1

    def calc_driving_style_coef(self,driving_score):
        deviation = abs(driving_score - 6)  / 6
        if deviation < 0.20:
            return 0.3
        elif deviation < 0.15:
            return 0.2
        elif deviation < 0.10:
            return 0.1
        else:
            return 1

    # Вычисление рейтинга для каждого ТС
    def calc_vehicle_rating(self,row):
        P_coef = self.calc_probeg_coef(row['Данные путевых листов, пробег'], row['Данные телематики, пробег'])
        C_coef = self.calc_structure_coef(1)  # Здесь нужен реальный показатель структуры, сейчас 1 как пример
        S_coef = self.calc_penalties_coef(row['Штрафы'])
        MV_coef = self.calc_driving_style_coef(row['манера вождения'])

        rating = P_coef * 0.4 + C_coef * 0.3 + S_coef * 0.15 + MV_coef * 0.15
        if len([rating, P_coef, C_coef, S_coef, MV_coef])!=5:
            print(rating, P_coef, C_coef, S_coef, MV_coef)
        return rating,P_coef,C_coef,S_coef,MV_coef





def prepare():
    preparation=Prepare_data()
    Calculate_params=Calculate_param()
    df_vehicles=Prepare_data.load_data()
    
    # Применение функции для каждого ряда
    #df_vehicles[['Rating', 'P_coef', 'C_coef', 'S_coef', 'MV_coef']] = df_vehicles.apply(Calculate_params.calc_vehicle_rating, axis=1, result_type='expand')
    
    df_vehicles['манера вождения'] = df_vehicles.groupby('Номерной знак ТС')['манера вождения'].transform(
        lambda x: x.fillna(x.median())
    )
    
    # Если все значения в группе NaN, можно заменить их на общую медиану
    overall_median = df_vehicles['манера вождения'].median()
    df_vehicles['манера вождения'] = df_vehicles['манера вождения'].fillna(overall_median)
    print (df_vehicles,'Проверка 2')
    # Проверка результата
    print(df_vehicles[['Номерной знак ТС', 'манера вождения']].head())
    print (df_vehicles)
    df_vehicles.to_csv('Обработанные.csv')
    df_vehicles.to_excel('Обработанные.xlsx')

prepare()
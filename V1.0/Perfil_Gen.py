# -*- coding: utf-8 -*-
"""
Created on Thu Oct 26 19:30:05 2023

@author: faull
"""

import pandas as pd
import datetime

df_gen=pd.read_excel("./Insumos/Entrada_Modelo.xlsx",header=[0])
df_gen.columns=["Fecha","Hora","Pmax","Pmin","CV"]
df_gen["Date"]=None

##Dateformat entry for the simulator:
##YYYYMMDDHH

for index,row in df_gen.iterrows():
    actual = row["Fecha"]
    hora = row["Hora"]
    df_gen.iloc[index,5] = actual.strftime("%Y%m%d")+"{0:0=2d}".format(hora)
        
    #df_gen.iloc[index,5] = actual+datetime.timedelta(hours=hora-1)

    
    
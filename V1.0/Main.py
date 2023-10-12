#%%Imports and aux functions
# -*- coding: utf-8 -*-
"""
Created on Sun May  8 23:16:47 2022

@author: franc
"""

import pandas as pd
import numpy as np
import os
import sys
import linecache
import warnings
import time

warnings.filterwarnings('ignore')

def check_files(path):
    #Returns a dictionary with all the files/filepath in the directory.
    files={}
    for (dirpath, dirnames, filenames) in os.walk(path):
        for file in filenames:
            files.update({file:os.path.join(dirpath,file)})
            #print(dirpath,file)
            #print(os.path.join(dirpath,file))
            ##Returns
            # ./DB/DB_PO PO230912.xlsx
            # ./DB/DB_PO\PO230912.xlsx
    return files

def aux_updatedict(dicc,key,val,index):
    if key in dicc.keys():
        data=dicc[key]
        dicc.update({key:[val[0],data[index]+val[1]]})
        return dicc
    else:
        dicc.update({key:val})
        return dicc

def aux_updatedict_gen(dicc,key,val):
    new_dict=dicc
    if key in new_dict.keys():
        data=new_dict[key]
        new_dict.update({key:data+val})
        return new_dict
    else:
        dicc.update({key:val})
        return new_dict
    
    
central_estudio="150 MW parejo."

#%%Inputs del programa
#Central de estudio
central_estudio=None
df_centrales=pd.DataFrame(columns=["Grupo Reporte Nombre","Central"])

#%%Revisamos BD para poder asociar Unidades a Centrales en Generación Real.
##Probablemente sea necesario hacer esto con múltiples archivos para poder
##tener una base de datos más precisa
df=pd.read_excel("./DB/DB_CmgFpen/FPen_2307_def/BD_DS_2307.xlsm",sheet_name="Hoja1",header=1)
df=df[["OPREAL","Llave OPREAL"]].drop_duplicates().sort_values(by="OPREAL")
df.to_excel("./Insumos/Llaves_OPREAL.xlsx",header=True,index=False)

#%%Revisamos BD de Costos de Combustible adicional.
##Probablemente sea necesario hacer esto con múltiples archivos para poder
##tener una base de datos más precisa
path="./DB/DB_SSCC/Respaldos_CO_SC_CCA/03 Costos de Combustible Adicional/Detalle diario"
CCAs=check_files(path)
asoc=pd.DataFrame(columns=["Unidad","Central"])
for cca in CCAs.keys():
    df=pd.read_excel(CCAs[cca],sheet_name="GenN",header=7)
    sel1=df[["UNIDADES", "Gen Neta [MWh]"]]
    sel2=df[["UNIDADES.1", "Gen Neta [MWh].1"]]
    sel3=df[["UNIDADES.2", "Gen Neta [MWh].2"]]
    cols=["Unidad","Central"]
    sel1.columns=cols
    sel2.columns=cols
    sel3.columns=cols
    
    asoc=asoc.append(sel1)
    asoc=asoc.append(sel2)
    asoc=asoc.append(sel3)
    
    #break
    
asoc=asoc.drop_duplicates().sort_values(by="Central")
asoc.to_excel("./Insumos/Llaves_CCA.xlsx",header=True,index=False)

#%%Revisamos BD de Costos de Costos de Oportunidad
##Probablemente sea necesario hacer esto con múltiples archivos para poder
##tener una base de datos más precisa
path="./DB/DB_SSCC/Respaldos_CO_SC_CCA/02 Costos de Oportunidad/Detalle diario"
CCOs=check_files(path)
asoc=pd.DataFrame(columns=["Unidad","Central"])
for cco in CCOs.keys():
    df=pd.read_excel(CCOs[cco],sheet_name="GenN",header=7)
    sel1=df[["UNIDADES", "Gen Neta [MWh]",1,2,3,4,5,6,7,8]]
    raise
    break
    sel2=df[["UNIDADES.1", "Gen Neta [MWh].1"]]
    sel3=df[["UNIDADES.2", "Gen Neta [MWh].2"]]
    cols=["Unidad","Central"]
    sel1.columns=cols
    sel2.columns=cols
    sel3.columns=cols
    
    asoc=asoc.append(sel1)
    asoc=asoc.append(sel2)
    asoc=asoc.append(sel3)
    
    #break
    
#asoc=asoc.drop_duplicates().sort_values(by="Central")
#asoc.to_excel("./Insumos/Llaves_CCA.xlsx",header=True,index=False)



#%% Procesamiento de datos de la generación real
##Probablemente sea necesario hacer esto con múltiples archivos para poder
##tener una base de datos más precisa

#Generación Real por central.
##Leemos el Dataframe, ordenamos, seleccionamos grupo_reporte_nombre y exportamos sin duplicados.
df=pd.read_csv('./DB/DB_GenReal/2023-7_unit.tsv', sep='\t')
df=df.sort_values(by="grupo_reporte_nombre",ascending=True)
#df_centrales=df[["nombre","grupo_reporte_nombre","nemotecnico"]]
#df_centrales=df_centrales.drop_duplicates().sort_values(by="nombre",ascending=True)
#df_centrales.to_excel("./Insumos/Centrales_genreal.xlsx",
#                      header=True,
#                      index=False)

#df_c=pd.read_csv('./DB/DB_GenReal/2023-7_cen.tsv', sep='\t')
#lista_centrales=df.grupo_reporte_nombre.unique().tolist()

#%% Procesamiento de datos de las políticas de operación
##Probablemente sea necesario hacer esto con múltiples archivos para poder
##tener una base de datos más precisa
POs_path="./DB/DB_PO"
POs_paths=check_files(POs_path)
POs=[POs_paths[file] for file in POs_paths.keys() if "PO" in file]

#Single PO processing

df=pd.read_excel(POs[0],sheet_name="TCO",header=6)
array=pd.unique(df[["CENTRALES","CENTRALES.1","CENTRALES.2"]].values.ravel('K'))
df_centralesPO=pd.DataFrame(array,columns=["Central"]).sort_values(by="Central",ascending=True)
df_centralesPO.to_excel("./Insumos/Centrales_POs.xlsx",header=True,index=False)

#%%Revisamos registros RIO para determinar Mínimos Técnicos por central.

#%% Registro centrales marginales por barra
##Esta sección retorna un diccionario que contiene todos los bloques horarios
##con un resumen de las centrales marginales y minutos marginados.

Regs_path="./DB/DB_CmgFpen"
Regs_paths=check_files(Regs_path)
Regs=[Regs_paths[file] for file in Regs_paths.keys() if ("Registro" in file and ".xlsx" in file)]

#Single df extraction
df=pd.read_excel(Regs[0],header=[0])
df["Bloque_horario"]=(df["Mes"].astype(str)
                      +df["Día"].apply(lambda x:"%02d" % (x,)).astype(str)
                      +df["Hora"].apply(lambda x:"%02d" % (x,)).astype(str))
dicc_marginal={}

for bloque in df.groupby("Bloque_horario"):
    bloquehorario=bloque[0]
    resumen_marginales = bloque[1].pivot_table(index = [bloque[1].columns[4]],
                                               aggfunc ='size').to_dict()
    dicc_marginal.update({bloquehorario:resumen_marginales})

Cmgs_horarios=[Regs_paths[file] for file in Regs_paths.keys() if ("cmg" in str(file).lower() and ".xlsx" in file)]

df_cmgs=pd.read_excel(Cmgs_horarios[0],header=[0])
df_cmgs=df_cmgs.loc[df_cmgs["Barra"]=="QUILLOTA______220"]
df_cmgs["Fecha"]=(df_cmgs["Mes"].astype(str)
                  +df_cmgs["Día"].apply(lambda x:"%02d" % (x,)).astype(str)
                  +df_cmgs["Hora"].apply(lambda x:"%02d" % (x,)).astype(str))
cmg_reales={}
for index,row in df_cmgs.iterrows():
    cmg_reales.update({row["Fecha"]:row["CMg [mills/kWh]"]})
#%%Del block
del bloque,bloquehorario,df,Regs,Regs_path,Regs_paths,resumen_marginales

#%%Algoritmo de la nueva central marginal según bloque horario, usando POs.

POs_path=".\DB\DB_PO"
POs_paths=check_files(POs_path)
POs=[POs_paths[file] for file in POs_paths.keys() if "PO" in file]

path="./DB/DB_SSCC/Respaldos_CO_SC_CCA/02 Costos de Oportunidad/Detalle diario"
CCOs=check_files(path)

df_mintecnicos=pd.read_excel("./Insumos/Minimos_Tecnicos.xlsx",header=[6],usecols = ['Central',"Potencia bruta máxima",'Potencia neta máxima',"Potencia bruta mínima (A.T.)"])

#Cuánta generación tendrá la central de estudio
gen_cx_estudio=150
#Cuál es el costo marginal de la central de estudio
cmg_central_estudio=0
#Cuál es el mínimo técnico de la central de estudio
mintec_cx_estudio=0
#Cuál es el algoritmo utilizado para remover generación.
#1 -> Remover máx generación
#2 -> Algoritmo establecido en Campiche.
alg_type=2

#Qué se hace cuando hay bloque a costo cero.
#1-> Envía la central a generación plena.
#2-> Envía la central a mínimo técnico.
costo_cero_alg=2


output={}
gen_output={}
for fecha in dicc_marginal.keys():
    # if not fecha in (["20230701"+"%02d" % (x,) for x in range(1,25)]):
    # +["20230702"+"%02d" % (x,) for x in range(1,25)]):
    if not fecha =="2023070101":
        continue
    #Para cada fecha
    cx=dicc_marginal[fecha]
    #Para cada central marginal distinta dentro del bloque intra-horario
    new_cmgs={}
    costo_marginal=0
    old_cmgs={}
    
    
    for central in cx.keys():
        #Periodo de marginación, hora del bloque
        periodo_marginacion=cx[central]
        hora=fecha[-2:]
        
        #Consideramos también la existencia de los mínimos técnicos.
        gen_req=gen_cx_estudio*periodo_marginacion/60
        gen_max=gen_req
        gen_mintecnico=mintec_cx_estudio*periodo_marginacion/60
        
        #Caso base: Costo cero -> Hay que seguir removiendo generación a las centrales:
        #Por lo tanto, se debe incorporar como primer elemento dentro del a PO.
        # if central=="COSTO_CERO":
        #     #output.update({fecha:[0,0]})
        #     if "COSTO_CERO" in new_cmgs.keys():
        #         data=new_cmgs["COSTO_CERO"]
        #         new_cmgs.update({"COSTO_CERO":[0,periodo_marginacion+data[1]]})
        #     else:
                # new_cmgs.update({"COSTO_CERO":[0,periodo_marginacion]})
        #     old_cmgs.update({"COSTO_CERO":[0,periodo_marginacion]})
        #     #Qué hacer cuando hay costo cero? -> Mín técnico, full despacho?
        #     if costo_cero_alg==1:
        #         # print("\nBloque Costo Cero")
        #         # print(gen_output)
        #         aux_updatedict_gen(gen_output,fecha,gen_cx_estudio*periodo_marginacion/60)
        #         # print(gen_output)s
        #     elif costo_cero_alg==2:
        #         aux_updatedict_gen(gen_output,fecha,gen_mintecnico)
        #     continue
        
        
        PO_asociada=[POs_paths[x] for x in POs_paths.keys() if fecha[2:-2] in x][0]
        df=pd.read_excel(PO_asociada,sheet_name="TCO",header=6)
        pos_bloque=[df[df.columns[1+i*4:4+i*4]] for i in range(3)]

        for subdf in pos_bloque:
            subdf.columns=["N","Central","Cmg"]
        
        #del df
        
        for gen_fecha in CCOs.keys():
            if fecha[:-2] in str(gen_fecha):
                path=CCOs[gen_fecha]
                df_generacion=pd.read_excel(path,sheet_name="GenN",header=7)
                if int(hora) in list(range(9)):
                    df_generacion=df_generacion[["UNIDADES","CV en Quillota", "Gen Neta [MWh]",int(hora)]]
                    df_generacion.columns=["Central","CV en Quillota", "Gen Neta [MWh]"]+[x for x in df_generacion.columns[3:]]
                    
                    #print("Using PO1")
                elif int(hora) in list(range(9,19)):
                    df_generacion=df_generacion[["UNIDADES.1","CV en Quillota.1", "Gen Neta [MWh].1",int(hora)]]
                    df_generacion.columns=["Central","CV en Quillota", "Gen Neta [MWh]"]+[x for x in df_generacion.columns[3:]]
                    #print("Using PO2")
                elif int(hora) in list(range(19,25)):
                    df_generacion=df_generacion[["UNIDADES.2","CV en Quillota.2", "Gen Neta [MWh].2",int(hora)]]
                    df_generacion.columns=["Central","CV en Quillota", "Gen Neta [MWh]"]+[x for x in df_generacion.columns[3:]]


        
        #Inicio del algoritmo:
        #Paso 1: En función de la fecha/hora seleccionamos el bloque
        po_bloque=None
        print("\n")
        #Seleccionamos bloque según hora
        if int(hora) in list(range(9)):
            po_bloque=pos_bloque[0]
            print("Using PO1")
        elif int(hora) in list(range(9,19)):
            po_bloque=pos_bloque[1]
            print("Using PO2")
        elif int(hora) in list(range(19,25)):
            po_bloque=pos_bloque[2]
            print("Using PO3")
            
        #Agregamos Central Costo Cero
        po_bloque.loc[-1]=[0,"COSTO_CERO",0]
        po_bloque.index = po_bloque.index + 1  # shifting index
        po_bloque = po_bloque.sort_index(ascending=True)  # sorting by index

        # raise
        #Paso 2: Encontrar central marginal según registro anterior. -> variable "central"
        #Indice de la central
        pos_centralmarginal=po_bloque.loc[po_bloque["Central"]==central].index[0]
        
        
        #Ordenamos el registro de centrales
        po_bloque=po_bloque.iloc[0:pos_centralmarginal+1].sort_index(ascending=False)
        # raise
        
        
        
        #Asociamos la generación a la PO.
        #Asociamos la generación desde df_generacion a po_bloque.
        po_bloque = pd.merge(po_bloque, df_generacion, on='Central',how="left")
        po_bloque = pd.merge(po_bloque,df_mintecnicos,on="Central",how="left")
        
        #Agregamos generación infinita a la central Costo Cero.
        po_bloque.loc[po_bloque.Central == "COSTO_CERO", po_bloque.columns[5]] = 999
        #raise
        

        
        #Cols K, M and R
        po_bloque["Potencia bruta máxima"] = po_bloque["Potencia bruta máxima"].fillna(0)
        po_bloque["Potencia neta máxima"] = po_bloque["Potencia neta máxima"].fillna(0)
        po_bloque["Potencia bruta mínima (A.T.)"] = po_bloque["Potencia bruta mínima (A.T.)"].fillna(0)
        
        
        #Min Tecnico = M/K*R
        po_bloque["Min_Tecnico"] = po_bloque["Potencia bruta máxima"]/po_bloque["Potencia neta máxima"]*po_bloque["Potencia bruta mínima (A.T.)"]
        po_bloque["Min_Tecnico"] = po_bloque["Min_Tecnico"].fillna(0)
        po_bloque["Gen_Restante"] =None
        #Si el cmg es distinto, el programa avisa.
        
       
        new_pos_centralmarginal=po_bloque.loc[po_bloque["Central"]==central].index[0]
        marginal_real=po_bloque.loc[po_bloque["Central"]==central]['Cmg'][new_pos_centralmarginal]
        ##Revisar 
        costo_marginal+=marginal_real*periodo_marginacion/60
        old_cmgs.update({po_bloque.iloc[new_pos_centralmarginal]["Central"]:[marginal_real,periodo_marginacion]})
        
        #Obtenemos minimos técnicos
        ###Funcion que asigna minimos técnicos.
    
        #Iniciamos algoritmo para descubrir que central es la nueva marginal.
        na_map=po_bloque.isna() 
        
        gen_required=True
        #print(fecha,hora)
        print(fecha,hora,periodo_marginacion,gen_req,gen_mintecnico)
        
        if alg_type==1:
            while gen_req>0:
                for index,row in po_bloque.iterrows():
                    
                    #Si no hay generación asociada, avanzamos.
                    if na_map.iloc[index,5]==True:
                        continue
                    print(row["Central"],
                          row["Cmg"],
                          gen_req,
                          row[po_bloque.columns[5]],
                          row[po_bloque.columns[5]]*periodo_marginacion/60)
                    
                    #Obtenemos la generación y se pondera por el periodo de marginación.
                    gen=(row[po_bloque.columns[5]]-row["Min_Tecnico"])*periodo_marginacion/60
                    
                    #Si la generación requerida es mayor que la disponible en la central.
                    if gen_req>gen:
                        #Update the new generation
                        po_bloque.iloc[index,10]=0
                        gen_req=gen_req-gen
                    
                    #Si la generación de la central es suficiente para cubrir el 
                    #delta de generación requerido.
                    else:
                        aux_updatedict(new_cmgs,row["Central"],[row["Cmg"],periodo_marginacion],1)
                        gen_req=0
                        #Update the new generation
                        po_bloque.iloc[index,10]=gen-gen_req
                        break


        if alg_type==2:
            while gen_required==True:
                for index,row in po_bloque.iterrows():
                    
                    #Si no está vacío el CV en Quillota, lo tomo. En otro caso,
                    #Tomamos el de la PO.
                    if not na_map.iloc[index,3]:
                        cmg_actual=row['CV en Quillota']
                    else:
                        cmg_actual=row["Cmg"]
                    #Si no hay generación asociada, avanzamos.
                    #Comparamos el costo marginal del bloque con el de la central de estudio.
                    #Si el costo marginal de la central de estudio es mayor, no revisamos generación (???)
                    # if cmg_central_estudio>cmg_actual:
                    #     print("Caso 0")
                    #     aux_updatedict(new_cmgs,row["Central"],[row["Cmg"],periodo_marginacion],1)
                    #     gen_req=gen_max-gen_mintecnico
                    #     gen_required=False
                    #     break
                    
                    if na_map.iloc[index,5]==True:
                        continue
                    
                   
                    
                    
                    
                    #Obtenemos la generación y se pondera por el periodo de marginación.
                    gen=(row[po_bloque.columns[5]]-row["Min_Tecnico"])*periodo_marginacion/60
                    
                    print("Central, Cmg, Gen_req, Gen_Central_Actual,Gen_Central_Actual_Prorrateada,Gen_Central_Actual_Prorrateada_ConMT")
                    print(row["Central"],
                          row["Cmg"],
                          gen_req,
                          row[po_bloque.columns[5]],
                          row[po_bloque.columns[5]]*periodo_marginacion/60,
                          gen)
                    
                    # if row["Central"]=="MEJILLONES-CTM3_TG1+TV1_GNL_E":
                        # raise
                    
                    #Caso 1
                    #Si la generación requerida es más que la que tiene la central
                    #Y el Costo marginal es mayor que el de la central de estudio
                    #Removemos toda la generación y vamos a la próxima central.
                    if cmg_actual>=cmg_central_estudio and gen_req>=gen:
                        print("Caso1")
                        po_bloque.iloc[index,10]=0
                        gen_req=gen_req-gen
                        
                    #Caso 2
                    #Si la generación requerida es más que la que tiene la central
                    #Y el Costo marginal es menor que el de la central de estudio
                    #No removemos y detenemos el algoritmo.
                    elif cmg_actual<cmg_central_estudio and gen_req>=gen:
                        print("Caso2")
                        #Si la central aún no genera a mínimo técnico, entonces
                        #removemos la energía necesaria y evaluamos.
                        #Si lo que generé es menor que el mínimo técnico
                        if (gen_max-gen_req)<gen_mintecnico:
                            # print("Generando a min tecnico")
                            #Si la energía de la central es mayor que la que
                            #necesito para alcanzar el min técnico.
                            #Le quito lo necesario
                            if gen>gen_mintecnico-(gen_max-gen_req):
                                #print(gen>gen_mintecnico-(gen_max-gen_req),gen,gen_mintecnico-(gen_max-gen_req))
                                #Genero a mínimo Técnico
                                delta=gen_max-gen_req+gen_mintecnico
                                gen_req=gen_max-gen_mintecnico
                                #Remuevo la diferencia de la central anterior
                                #Gen restante = gen-delta+gen anterior?
                                #po_bloque = (gen-mintec)*periodomarginal-gen_req
                                po_bloque.iloc[index,10]=(gen-delta)
                                #Detengo el algoritmo.
                                gen_required=False
                                #La central a la que se le quitó generación margina.
                                aux_updatedict(new_cmgs,row["Central"],[row["Cmg"],periodo_marginacion],1)
                                break
                            #Si la energía es menor que la que requiero
                            else:
                                #Quito toda la energía
                                po_bloque.iloc[index,10]=0
                                #Y la restamos al a generación requerida.
                                gen_req=gen_req-gen
                                #El algoritmo sigue con la próxima central.
                                continue
                            
                        else:
                            #Si ya he generado más del mínimo técnico, entonces
                            #el algoritmo se detiene.
                            #Falta exportar la generación final de la central
                            aux_updatedict(new_cmgs,row["Central"],[row["Cmg"],periodo_marginacion],1)
                                
                            gen_required=False
                            break
                    
                    #Caso 3
                    #Si la generación requerida es menor que la que tiene la central
                    #Y el costo marginal es mayor que el de la central de estudio
                    #Removemos lo necesario y detenemos el algoritmo.
                    elif gen_req<gen and cmg_actual>=cmg_central_estudio:
                        print("Caso3")
                        aux_updatedict(new_cmgs,row["Central"],[row["Cmg"],periodo_marginacion],1)
                        gen_req=0
                        po_bloque.iloc[index,10]=gen-gen_req
                        gen_required=False
                        break
                    
                    #Caso 4
                    #Si la generación requerida es menor que la que tiene la central
                    #Y el Costo marginal es menor que el de la central de estudio
                    #No removemos y detenemos el algoritmo.
                    elif gen_req<gen and cmg_actual<cmg_central_estudio:
                        print("Caso4")
                        #Si la central aún no genera a mínimo técnico, entonces
                        #removemos la energía necesaria y evaluamos.
                        #Si lo que generé es menor que el mínimo técnico
                        if (gen_max-gen_req)<gen_mintecnico:
                            print("Generando a min tecnico")
                            #Si la energía de la central es mayor que la que
                            #necesito para alcanzar el min técnico.
                            #Le quito lo necesario
                            if gen>gen_mintecnico-(gen_max-gen_req):
                                #print(gen>gen_mintecnico-(gen_max-gen_req),gen,gen_mintecnico-(gen_max-gen_req))
                                #Lo que falta para generar a minimo tecnico
                                print(gen_max,gen_req,gen_mintecnico)
                                delta=gen_max-gen_req+gen_mintecnico
                                print(delta)
                                gen_req=gen_max-gen_mintecnico
                                #Remuevo la diferencia de la central anterior
                                #Gen restante = gen-delta+gen anterior?
                                #po_bloque = (gen-mintec)*periodomarginal-gen_req
                                po_bloque.iloc[index,10]=(gen-delta)
                                #Detengo el algoritmo.
                                gen_required=False
                                #La central a la que se le quitó generación margina.
                                aux_updatedict(new_cmgs,row["Central"],[row["Cmg"],periodo_marginacion],1)
                                break
                            #Si la energía es menor que la que requiero
                            else:
                                print("Si la energia es menor")
                                #Quito toda la energía
                                po_bloque.iloc[index,10]=0
                                #Y la restamos al a generación requerida.
                                gen_req=gen_req-gen
                                #El algoritmo sigue con la próxima central.
                                continue
                        else:
                            #Si ya he generado más del mínimo técnico, entonces
                            #el algoritmo se detiene.
                            #Falta exportar la generación final de la central
                            aux_updatedict(new_cmgs,row["Central"],[row["Cmg"],periodo_marginacion],1)
    
                            gen_required=False
                            break
            val=(gen_max-gen_req)
            # print(gen_output)
            # print(val)
            aux_updatedict_gen(gen_output,fecha,val)
            # print(gen_output)
        
            
                    
                
    #Actualizamos diccionario de salida con el nuevo CMG y el antiguo                
    output.update({fecha:[sum([new_cmgs[key][0]*new_cmgs[key][1]/60 for key in new_cmgs.keys()]),costo_marginal]})
        



#%%Del block
del cx,CCOs,central,df_generacion,fecha,gen_fecha,hora,path,periodo_marginacion,PO_asociada,POs,pos_centralmarginal,POs_path,POs_paths,costo_marginal,gen,gen_cx_estudio,gen_req,index,na_map,new_cmgs,row
#%% Visualization block
import plotly.io as pio
pio.renderers.default='browser'
import plotly.express as px
import plotly.graph_objects as go
df=pd.DataFrame(columns=["Día","Hora","Nuevo CMg", "CMg Original"])

for key in output.keys():
    fecha=key
    dia=fecha[:-2]
    hora=fecha[-2::]
    df.loc[len(df)+1]=[dia,hora,output[key][0],output[key][1]]

#fig = px.line(df, x="Hora", y="Nuevo CMg", color="Día",markers=True)
fig = go.Figure()
color_counter=0
for sdf in df.groupby("Día"):
    fig.add_trace(go.Scatter(x=sdf[1]["Hora"], y=sdf[1]["CMg Original"],
                    mode='lines+markers',
                    marker_color=fig.layout['template']['layout']['colorway'][color_counter],
                    name='Marginal real',legendgroup=sdf[0],  # this can be any string, not just "group"
    legendgrouptitle_text=sdf[0]))
    
    fig.add_trace(go.Scatter(x=sdf[1]["Hora"], y=sdf[1]["Nuevo CMg"],
                    mode='lines+markers',
                    marker_color=fig.layout['template']['layout']['colorway'][color_counter],
                    name='Nuevo Marginal',legendgroup=sdf[0],
                    line=dict(dash="dash"),
    legendgrouptitle_text=sdf[0]))
    color_counter+=1
    if color_counter==10:
        color_counter=0



df_cmgs["Fecha_Index"]=(df_cmgs["Mes"].astype(str)
                  +df_cmgs["Día"].apply(lambda x:"%02d" % (x,)).astype(str))
df_cmgs["Hora"]=df_cmgs["Hora"].apply(lambda x:"%02d" % (int(x),)).astype(str)

color_counter=1
for sdf in df_cmgs.groupby("Fecha_Index"):
    fig.add_trace(go.Scatter(x=sdf[1]["Hora"], y=sdf[1]["CMg [mills/kWh]"],
                    mode='lines+markers',
                    marker_color=fig.layout['template']['layout']['colorway'][color_counter],
                    name='Marginal real reportado',legendgroup=sdf[0],
                    line=dict(dash="dot"),
    legendgrouptitle_text=sdf[0]))
    color_counter+=1
    if color_counter==10:
        color_counter=0
    

    
    
    
    color_counter+=1
    if color_counter==10:
        color_counter=0

fig.update_layout(
    title="Nuevo Costo Marginal calculado vs Marginal real en el periodo de estudio para la central "+str(central_estudio),
    xaxis_title="Hora del día",
    yaxis_title="Costo Marginal [$US/MWh]",
    legend_title="Periodo de estudio",
)


fig.show()
fig.write_html("Nuevos_CMgs.html")
df.to_excel("Nuevos_CMgs.xlsx",header=True,index=False)



df=pd.DataFrame(columns=["Día","Hora","Gen",])
for key in gen_output.keys():
    fecha=key
    dia=fecha[:-2]
    hora=fecha[-2::]
    df.loc[len(df)+1]=[dia,hora,gen_output[key]]

#fig = px.line(df, x="Hora", y="Nuevo CMg", color="Día",markers=True)
fig = go.Figure()
color_counter=0
for sdf in df.groupby("Día"):
    fig.add_trace(go.Scatter(x=sdf[1]["Hora"], y=sdf[1]["Gen"].apply(lambda x: round(x,3)),
                    mode='lines+markers',
                    marker_color=fig.layout['template']['layout']['colorway'][color_counter],
                    name='Generación por bloque',legendgroup=sdf[0],  # this can be any string, not just "group"
    legendgrouptitle_text=sdf[0]))
    
    color_counter+=1
    if color_counter==10:
        color_counter=0

fig.update_layout(
    title="Generación para la central "+str(central_estudio),
    xaxis_title="Hora del día",
    yaxis_title="Generación [MW]",
    legend_title="Periodo de estudio",
)


fig.show()
fig.write_html("Generacion.html")
df.to_excel("Generacion.xlsx",header=True,index=False)

#%%
for data in df.groupby("grupo_reporte_nombre"):
    table=data[1]
    #table.drop_duplicates(subset=['central_nombre'],inplace=True)
    #print(data[0],table.iloc[0,11])
    df_centrales.loc[len(df_centrales)+1]=[table.iloc[0,11],data[0]]
    break
    
#Costos marginal por barra
#Centrales marginales por barra por minuto.

#%%

#Fechas en formato AAAAMMDD
fechainicio='20220103'
fechatermino='20220113'
fechas_simulacion=[d.strftime('%Y%m%d') for d in pd.date_range(fechainicio,fechatermino)]
#Hora inicial del dia = 0, Hora final del dia = 23.
horainicio=0
horatermino=23
horas_simulacion=range(horainicio,horatermino+1)
###Documentar de donde viene el nombre. Ahora la contraparte es colbún.
df=pd.read_csv("./Insumos/CentralesEstudio.csv",header=[0])
Centrales_estudio=df['Centrales_Estudio'].tolist()

#Cargamos centrales térmicas de estudio
df_termicas=pd.read_csv("./Insumos/CentralesTermicas.csv",header=[0])
Centrales_Termicas=df_termicas['Centrales_Termicas'].tolist()

#Cargamos el archivo de codificaciones
Codificacion=pd.read_excel("./Insumos/DiccionarioCentrales.xlsx",sheet_name='Sheet1',header=[0])

#Cargamos el archivo con los pares de centrales
Pares=pd.read_excel("./Insumos/Pares.xlsx",header=[0],)  

#Cargamos la planilla de generacion del mes
df_generacion=pd.read_excel('./Insumos/Generación Real/2022-1.xlsx',header=[3])
df_generacion['Key']=df_generacion['Central']+" "+df_generacion['Llave']
# df_generacion['Fecha']=df_generacion['Fecha'].replace(regex=["-"],value="")
#CMg por barra
Cmg_barra=pd.read_excel('./Insumos/Centrales Marginales por barra/Centrales_marginales_por_barra_2201__def_RESUMEN.xlsx',header=[9],sheet_name='Centrales por barra')

#Embarques
embarques=pd.read_excel("./Insumos/Embarques horarios.xlsx",sheet_name="Embarque01",header=[0]).replace(to_replace=1,value=0)
embarques['Fecha']=embarques['Fecha'].replace(regex=["-"],value="")
embarques=embarques.replace(0,"GN")
dicc_centrales_estudio={'GN':'NEHUENCO-2_TG1+TV1_GN_A',"GNL":"NEHUENCO-2_TG1+TV1_GNL_C",'diesel':"NEHUENCO-2_TG1+TV1_DIESEL"}
generacion_declarada=pd.read_excel("./Insumos/Comparacion_Costos_Enero.xlsx",header=[0])
generacion_declarada=generacion_declarada.replace(0,221).replace(1,300)
generacion_declarada['Fecha']=generacion_declarada['Fecha'].replace(regex=["-"],value="")

#Declaracion del gas
df_gas=pd.read_excel("./Insumos/Declaración de Gas Diario Disponible.xlsx",header=[0])
df_gas.replace(np.nan,0,inplace=True)

if not os.path.exists("./Resultados"):
    os.mkdir("Resultados")

def gen_real_conmintec(central):
    try:
        Codigo=Codificacion.loc[Codificacion['Nombre']==central]['Nombre Central'].iloc[0]
        Codigo=Pares.loc[Pares['Central']==Codigo]['Central _Original'].iloc[0]
        Gen_Real=df_fecha.loc[df_fecha['Key']==Codigo]['Hora '+str(hora+1)].values[0]
        # Min_Tecnico=Codificacion.loc[Codificacion['Nombre']==str(central)]['Mínimo Técnico MW'].iloc[0]
        return Gen_Real
    except:
        return 0

def gen_real(central):
    try:
        Codigo=Codificacion.loc[Codificacion['Nombre']==central]['Nombre Central'].iloc[0]
        Codigo=Pares.loc[Pares['Central']==Codigo]['Central _Original'].iloc[0]
        Gen_Real=df_fecha.loc[df_fecha['Key']==Codigo]['Hora '+str(hora+1)].values[0]
        Min_Tecnico=Codificacion.loc[Codificacion['Nombre']==str(central)]['Mínimo Técnico MW'].iloc[0]
        if Gen_Real-Min_Tecnico<=0:
            return 0
        else:      
            return Gen_Real-Min_Tecnico
    except:
        return 0
def gen_real_dia(central):
    Codigo=Codificacion.loc[Codificacion['Nombre']==central]['Nombre Central'].iloc[0]
    Codigo=Pares.loc[Pares['Central']==Codigo]['Central _Original'].iloc[0]
    Gen_Real=df_fecha.loc[df_fecha['Key']==Codigo]['Total'].values[0]
    Min_Tecnico=Codificacion.loc[Codificacion['Nombre']==str(central)]['Mínimo Técnico MW'].iloc[0]
    if Gen_Real-Min_Tecnico<=0:
        return 0
    else:      
        return Gen_Real-Min_Tecnico

def hr_central(central):
    return df_termicas.loc[df_termicas['Centrales_Termicas']==central]['Heat_rate'].values[0]
del fechainicio,fechatermino,horainicio,horatermino
def mintecnico_central(central):
    return Codificacion.loc[Codificacion['Nombre']==central]['Mínimo Técnico MW'].iloc[0]
#%%
t0 = time.time()

for fecha,df_fecha in df_generacion.groupby('Fecha'):
    df_salida=pd.DataFrame(columns=['Fecha','Hora','Central','CV Central','CMg Original Bloque','CMg Final Bloque','Generacion Central Estudio','ERROR'])
    df_salida_2=pd.DataFrame(columns=['Fecha','Hora','Central Desplazada','CV','CMg_Bloque','Generacion Original','Generacion Desplazable','Generacion Desplazada','Minimo tecnico','Generacion final de la central','Tiempo'])
    df_salida_3=pd.DataFrame(columns=['Fecha','Hora','Central','CV Central','CMg Final Bloque','Generacion Central Estudio'])
    anno=fecha[0:4]
    mes=fecha[5:7]
    dia=fecha[8:10]
    fecha=fecha.replace("-","")
    if fecha in fechas_simulacion:
        path_po="./Insumos/Programas de Operación - Modificados/"+'PO'+anno[2:]+mes+dia+".xlsx"
        df_po=pd.read_excel(path_po,sheet_name="TCO",header=[6])
        df_po.columns=['Unnamed: 0', 'Prioridad_1', 'CENTRALES_1', 'CMg_1', 'Unnamed: 4', 'Prioridad_2','CENTRALES_2', 'CMg_2', 'Unnamed: 8', 'Prioridad_3', 'CENTRALES_3','CMg_3']
        df_po.dropna(thresh=3,inplace=True)
        
        
        
        for hora in horas_simulacion:
            embarque=embarques.loc[embarques['Fecha']==fecha]['Hora '+str(hora+1)].iloc[0]
            central_estudio=dicc_centrales_estudio[embarque]
            print(fecha,hora+1,embarque)
            
            if hora in list(range(8)):
                politica=df_po[['Prioridad_1','CENTRALES_1','CMg_1']]
                politica.columns=['Prioridad','Central','CV']
            if hora in list(range(8,18)):
                politica=df_po[['Prioridad_2','CENTRALES_2','CMg_2']]
                politica.columns=['Prioridad','Central','CV']
            if hora in list(range(18,24)):
                politica=df_po[['Prioridad_3','CENTRALES_3','CMg_3']]
                politica.columns=['Prioridad','Central','CV']
                
                
            Gas_Declarado_Dia=df_gas.loc[df_gas['Dia']==pd.date_range(fecha,fecha)[0]]
            if embarque!='GNL':
                Gas_Declarado_Dia=Gas_Declarado_Dia[Gas_Declarado_Dia.columns[1]].iloc[0]+Gas_Declarado_Dia[Gas_Declarado_Dia.columns[2]].iloc[0]
            else:
                Gas_Declarado_Dia=Gas_Declarado_Dia[Gas_Declarado_Dia.columns[3]].iloc[0]+Gas_Declarado_Dia[Gas_Declarado_Dia.columns[4]].iloc[0]
            
            heat_rate_central_estudio=df_termicas.loc[df_termicas['Centrales_Termicas']==central_estudio]['Heat_rate'].values[0]
            Min_Tecnico_Central_Estudio=221
            #Min_Tecnico_N1=244.7
            CV_central_estudio=politica.loc[politica['Central']==central_estudio]['CV'].values[0]
            prioridad_central_estudio=politica.loc[politica['Central']==central_estudio]['Prioridad'].values[0]
            termicas_estudiables=df_termicas.loc[(df_termicas['Heat_rate']>=heat_rate_central_estudio)&(df_termicas['Centrales_Termicas']!=central_estudio)]    

            termicas_estudiables['CV_Hora']=None
            termicas_estudiables['Gen_Hora']=None
            termicas_estudiables['Gas_Hora']=None
            termicas_estudiables['Gas_Dia']=None
            termicas_estudiables['Gas_Original_Hora']=None
            termicas_estudiables['Gas_Movilizado']=None
            
            for index,row in termicas_estudiables.iterrows():
                termica=row[0]
                termicas_estudiables['CV_Hora'][index]=politica.loc[politica['Central']==termica]['CV'].values[0]
                termicas_estudiables['Gen_Hora'][index]=gen_real(termica)
                termicas_estudiables['Gas_Hora'][index]=gen_real(termica)*row[1]/1000
                termicas_estudiables['Gas_Original_Hora'][index]=gen_real(termica)*row[1]/1000
                termicas_estudiables['Gas_Dia'][index]=gen_real_dia(termica)*row[1]/1000
            termicas_estudiables.sort_values(by=[termicas_estudiables.columns[2]],ascending=False,inplace=True)
            
            
            Gen_Centrales_Termicas_Dia=sum([gen_real_dia(central) for central in termicas_estudiables.Centrales_Termicas.tolist()])
            Gas_Centrales_Termicas_Dia=sum([gen_real_dia(central)*hr_central(central) for central in termicas_estudiables.Centrales_Termicas.tolist()])/1000
            Gen_Centrales_Termicas_Hora=sum([gen_real(central) for central in termicas_estudiables.Centrales_Termicas.tolist()])
            Gas_Centrales_Termicas_Hora=sum([(mintecnico_central(central)+gen_real(central))*hr_central(central) for central in termicas_estudiables.Centrales_Termicas.tolist()])/1000
            
            #Vemos cuanto gas más se usó. Si hay más declarado que utilizado, se lo damos a N2. Si hay más utilizado que declarado, entonces nos quedamos con ese y el diferencial es cero.
            Z_Gas_Declarado_Dia=max(Gas_Declarado_Dia,Gas_Centrales_Termicas_Dia)
            #La diferencia es 0 o un valor mayor que cero.
            Dif_Gas_Diario=Z_Gas_Declarado_Dia-Gas_Centrales_Termicas_Dia
            
            #Vemos ahora cuanto gas usan las centrales sin N1 y lo comparamos.
            termicas_estudiables_SinN1=termicas_estudiables.copy()
            termicas_estudiables_SinN1=termicas_estudiables_SinN1[~termicas_estudiables_SinN1.Centrales_Termicas.str.contains("NEHUENCO-1")]
            # Gen_Centrales_Termicas_Dia_SinN1=sum([gen_real_dia(central) for central in termicas_estudiables_SinN1.Centrales_Termicas.tolist()])
            # Gas_Centrales_Termicas_Dia_SinN1=sum([gen_real_dia(central)*hr_central(central) for central in termicas_estudiables_SinN1.Centrales_Termicas.tolist()])/1000
            # Gen_Centrales_Termicas_Hora_SinN1=sum([gen_real(central) for central in termicas_estudiables_SinN1.Centrales_Termicas.tolist()])
            Gas_Centrales_Termicas_Hora_SinN1=sum([(gen_real(central))*hr_central(central) for central in termicas_estudiables_SinN1.Centrales_Termicas.tolist()])/1000
            #Calculamos las diferencias de generacion. Será 0 o un valor positivo ya que el conjunto genera lo mismo o menos si sacamos N1.
            # Dif_Gas_N1=Gas_Centrales_Termicas_Hora-Gas_Centrales_Termicas_Hora_SinN1
            
            
            Marginales=Cmg_barra.loc[(Cmg_barra['Día']==int(dia))&(Cmg_barra['Hora']==hora+1)]
            Marginales.columns=['Mes', 'Día', 'Hora', 'Minuto', 'Central', 'Central2']
            Marginales=Marginales.groupby(['Central'])['Minuto'].count()
            CMg_bloque=0
            for central,tiempo in Marginales.items():
                if central!='COSTO_CERO':
                    CMg_bloque+=politica.loc[politica['Central']==central]['CV'].values[0]*tiempo/60
                    
            # Gen_central_estudio=generacion_declarada.loc[generacion_declarada['Fecha']==fecha]['Hora '+str(hora+1)].values[0]/heat_rate_central_estudio*1000
            Gen_central_estudio=generacion_declarada.loc[generacion_declarada['Fecha']==fecha]['Hora '+str(hora+1)].values[0]
            if CMg_bloque<CV_central_estudio:
                Gen_central_estudio=Min_Tecnico_Central_Estudio
            # print(Gen_central_estudio,CV_central_estudio,CMg_bloque)
            Gas_Movilizado_A_Central_Estudio_Bloque=0
           
            
            #Agregamos inmediatamente el gas sobrante de la declaracion que sera la diferencia que sobro (que puede ser 0 o más, o el valor máximo de generacion si es que hay gas disponible ):
            # Gas_Movilizado_A_Central_Estudio_Bloque=min(Dif_Gas_Diario,Gen_central_estudio*heat_rate_central_estudio/1000)
            # print(min(Dif_Gas_Diario,Gen_central_estudio*heat_rate_central_estudio/1000))
            #Lo restamos de la generacion necesaria en el bloque:
            # Gen_central_estudio-=Gas_Movilizado_A_Central_Estudio_Bloque/heat_rate_central_estudio*1000
            # print(Gen_central_estudio)
            #Revisamos la condicion de N1 y su generacion.
            #GAS generado por todas las centrales = Gas_Centrales_Termicas_Hora
            #GAS generado por las centrales sin N1= Gas_Centrales_Termicas_Hora_SinN1
            #GAS generado por la central N1= Dif_Gas_N1
            #Gas Requerido por la central en estudio= Gen_central_estudio*heat_rate_central_estudio/1000
            #Si el gas generado por las centrales SIN N1 cubre N2: avanzamos.
            #Si no, reviso N1.
            if Gas_Centrales_Termicas_Hora_SinN1<Gen_central_estudio*heat_rate_central_estudio/1000:
                #reviso N1:
                    # print(Gas_Centrales_Termicas_Hora,Gas_Centrales_Termicas_Hora_SinN1,Gen_central_estudio*heat_rate_central_estudio/1000)
                    # print('hey')
                    N1=central_estudio.replace("2","1")
                    hr_n1=hr_central(N1)
                    Gas_MIN_TECNICO_N1=mintecnico_central(N1)*hr_n1/1000
                    Gas_N1=(gen_real(N1)+mintecnico_central(N1))*hr_n1/1000
                    indice_N1=termicas_estudiables.loc[termicas_estudiables['Centrales_Termicas']==N1].index[0]
                    #Si N1 cubre N2 y no rompe min tecnico. Avanzo normalmente
                    if Gas_N1-Gen_central_estudio*heat_rate_central_estudio/1000>=Gas_MIN_TECNICO_N1 and Gas_N1>=Gen_central_estudio*heat_rate_central_estudio/1000:
                        # print('a',(Gas_N1-Gen_central_estudio*heat_rate_central_estudio/1000)/heat_rate_central_estudio*1000,Gas_N1,Gen_central_estudio*heat_rate_central_estudio/1000)
                        pass
                    #Si N1 cubre N2 y rompe min tecnico, entonces saco N1 completamente y avanzo.
                    elif Gas_N1-Gen_central_estudio*heat_rate_central_estudio/1000<Gas_MIN_TECNICO_N1 and Gas_N1>=Gen_central_estudio*heat_rate_central_estudio/1000:
                        # print('b')
                        #Generacion_necesaria=0
                        # Gen_central_estudio=Gen_central_estudio
                        Gas_Movilizado_A_Central_Estudio_Bloque+=Gen_central_estudio*heat_rate_central_estudio/1000
                        termicas_estudiables['Gas_Hora'][indice_N1]=0
                        termicas_estudiables['Gen_Hora'][indice_N1]=0
                        
                        # raise
                    #Si N1 no cubre N2 y rompe min tecnico, saco N1 completa y avanzo.
                    elif Gas_N1-Gen_central_estudio*heat_rate_central_estudio/1000<Gas_MIN_TECNICO_N1 and Gas_N1<=Gen_central_estudio*heat_rate_central_estudio/1000:
                        # print('c')
                        # Gen_central_estudio-=Dif_Gas_N1/heat_rate_central_estudio*1000
                        Gas_Movilizado_A_Central_Estudio_Bloque+=Gas_N1
                        termicas_estudiables['Gas_Hora'][indice_N1]=0
                        termicas_estudiables['Gen_Hora'][indice_N1]=0
                        # raise
                    #Si N1 no cubre N2 y no rompe min tecnico.
                    #Sigo la rutina normalmente y respeto el min tecnico.
            
                    
                        
            
            Gen_central_estudio=Gen_central_estudio-Gas_Movilizado_A_Central_Estudio_Bloque/heat_rate_central_estudio*1000
            
            CMg_Final_Bloque=0
            # print('Generacion Objetivo:',Gen_central_estudio)
            for central,tiempo in Marginales.items():
                
                Gen_central_estudio_subbloque=Gen_central_estudio*tiempo/60
                Gas_central_estudio_subbloque=hr_central(central_estudio)*Gen_central_estudio_subbloque/1000
                Gas_Movilizado_A_Central_Estudio=0
                gen_original_marginal=gen_real(central)
                if central!='COSTO_CERO':
                    CV_original_marginal=politica.loc[politica['Central']==central]['CV'].values[0]*tiempo/60
                else:
                    CV_original_marginal=0
                    Gas_Movilizado_A_Central_Estudio+=Gas_central_estudio_subbloque
                    Gas_central_estudio_subbloque=0
                for index,row in termicas_estudiables.iterrows():
                    termica=row[0]
                    heat_rate=row[1]
                    gen_original=row[3]
                    gas_termica=(gen_original*tiempo/60*heat_rate/1000)
                    diferencial_gas=Gas_central_estudio_subbloque-gas_termica
                    #Si lo que necesito es mayor a lo que hay
                    if diferencial_gas>0:
                        termicas_estudiables['Gas_Hora'][index]=0
                        Gas_Movilizado_A_Central_Estudio+=gas_termica
                        Gas_central_estudio_subbloque=Gas_central_estudio_subbloque-gas_termica
                        # print(termica,gen_original,gas_termica,Gas_central_estudio_subbloque)
                    elif diferencial_gas==0:
                        # columnas=df_salida_3.columns
                        # columnas=columnas+[central,]
                        break
                    elif diferencial_gas<0 and Gen_central_estudio_subbloque==0:
                        break
                    #Si lo que hay es mayor a lo que necesito
                    else:
                        termicas_estudiables['Gas_Hora'][index]=gas_termica-abs(diferencial_gas)
                        Gas_Movilizado_A_Central_Estudio+=Gas_central_estudio_subbloque
                        Gas_central_estudio_subbloque=0
                        break
                Gas_Movilizado_A_Central_Estudio_Bloque+=Gas_Movilizado_A_Central_Estudio
                termicas_estudiables['Gas_Movilizado']=termicas_estudiables['Gas_Original_Hora']-termicas_estudiables['Gas_Hora']
                termicas_estudiables['Gen_Final_Hora']=termicas_estudiables['Gas_Hora']/termicas_estudiables['Heat_rate']*1000
                termicas_estudiables['Gen_Desplazada']=termicas_estudiables['Gen_Hora']-termicas_estudiables['Gen_Final_Hora']
                Gen_Marginal_Desplazar=Gas_Movilizado_A_Central_Estudio/heat_rate_central_estudio*1000-termicas_estudiables['Gen_Desplazada'].sum()
                Gen_Marginal_Desplazar_orig=Gen_Marginal_Desplazar
                
                #Armamos una PO.
                po2=politica.copy()
                po2=po2.sort_values(by='Prioridad',ascending=False)
                po2=po2.loc[(po2['Central']==central)|(po2['CV']<=CV_original_marginal)]
                # po2=po2.sort_values(by='Prioridad',ascending=False)
                CMg_final=CMg_bloque
                CMg_Final_Bloque=CMg_bloque
                
                if Gen_Marginal_Desplazar_orig>0:
                    CMg_Final_Bloque=0
                    for index,row in po2.iterrows():
                        try:
                            Min_Tecnico=Codificacion.loc[Codificacion['Nombre']==str(row[1])]['Mínimo Técnico MW'].iloc[0]
                        except:
                            Min_Tecnico=0
                        
                        if central=='COSTO_CERO':
                            gen_original=Gen_Marginal_Desplazar
                            Min_Tecnico=0
                            gen_desplazable=Gen_Marginal_Desplazar
                            gen_desplazada=Gen_Marginal_Desplazar
                            Gen_final_marginal=0
                            CMg_final=0
                            df_salida_2.loc[len(df_salida_2)+1]=[fecha,hora+1,'COSTO_CERO',0,CMg_Final_Bloque,gen_original+Min_Tecnico,gen_desplazable,gen_desplazada,Min_Tecnico,Gen_final_marginal+Min_Tecnico,tiempo]
                            # print('a-   ',row[1],gen_desplazable,gen_desplazada,Gen_Marginal_Desplazar)
                            break
                        
                        gen_original=gen_real(str(row[1]))*tiempo/60
                        gen_desplazable=gen_original
                        if gen_desplazable>=Gen_Marginal_Desplazar:
                            gen_desplazada=Gen_Marginal_Desplazar
                            Gen_Marginal_Desplazar-=gen_desplazada
                            CMg_Final_Bloque+=politica.loc[politica['Central']==central]['CV'].values[0]*tiempo/60
                            Gen_final_marginal=gen_original-gen_desplazada
                            # print(row[1],gen_desplazable,gen_desplazada,Gen_Marginal_Desplazar_orig,gen_desplazada,Gen_Marginal_Desplazar,Min_Tecnico)
                            df_salida_2.loc[len(df_salida_2)+1]=[fecha,hora+1,row[1],politica.loc[politica['Central']==central]['CV'].values[0]*tiempo/60,CMg_Final_Bloque,gen_original+Min_Tecnico,gen_desplazable,gen_desplazada,Min_Tecnico,Gen_final_marginal+Min_Tecnico,tiempo]
                            # print('b-   ',row[1],gen_desplazable,gen_desplazada,Gen_Marginal_Desplazar)
                            break
                            
                        else:
                            gen_desplazada=gen_desplazable
                            Gen_Marginal_Desplazar-=gen_desplazada
                            Gen_final_marginal=gen_original-gen_desplazada
                            df_salida_2.loc[len(df_salida_2)+1]=[fecha,hora+1,row[1],politica.loc[politica['Central']==central]['CV'].values[0]*tiempo/60,CMg_Final_Bloque,gen_original+Min_Tecnico,gen_desplazable,gen_desplazada,Min_Tecnico,Gen_final_marginal+Min_Tecnico,tiempo]
                            # print('c-   ',row[1],gen_desplazable,gen_desplazada,Gen_Marginal_Desplazar)
                            
                            
                        
                        
                    # print(central,gen_original_marginal,Gen_final_marginal,Gen_final_marginal,Min_Tecnico)
                    
            #Filtramos los resultados buscados
            #Merge para las centrales termicas:
            df_termicas_copy=df_termicas.copy()
            df_termicas_completo=pd.merge(df_termicas_copy, termicas_estudiables,how='outer')
            for index,row in df_termicas_completo.iterrows():
                termica=row[0]
                if 'Gen_i_'+str(termica) not in df_salida.columns:
                    df_salida['Gen_i_'+str(termica)]=None
                if 'Gen_f_'+str(termica) not in df_salida.columns:
                    df_salida['Gen_f_'+str(termica)]=None
                if 'CV_'+str(termica) not in df_salida.columns:
                    df_salida['CV_'+str(termica)]=None
                
            
            if Gas_Movilizado_A_Central_Estudio_Bloque/heat_rate_central_estudio*1000<Min_Tecnico_Central_Estudio:
                # print(termicas_estudiables.Gen_Final_Hora.to_list())
                valores_termicas=[]
                for index,row in df_termicas_completo.iterrows():
                    if row[3]>0:
                        valores_termicas.append(gen_real_conmintec(str(row[0])))
                        valores_termicas.append(row[8]+mintecnico_central(row[0]))
                    else:
                        valores_termicas.append(gen_real_conmintec(str(row[0])))
                        valores_termicas.append(row[8])
                    valores_termicas.append(row[2])
                    
                df_salida.loc[len(df_salida)+1]=[fecha,hora+1,central_estudio,CV_central_estudio,CMg_bloque,CMg_Final_Bloque,Gas_Movilizado_A_Central_Estudio_Bloque/heat_rate_central_estudio*1000,'Si']+valores_termicas
            else:
                valores_termicas=[]
                for index,row in df_termicas_completo.iterrows():
                    if row[3]>0:
                        valores_termicas.append(gen_real_conmintec(str(row[0])))
                        valores_termicas.append(row[8]+mintecnico_central(row[0]))
                    else:
                        valores_termicas.append(gen_real_conmintec(str(row[0])))
                        valores_termicas.append(row[8])
                    valores_termicas.append(row[2])
                df_salida.loc[len(df_salida)+1]=[fecha,hora+1,central_estudio,CV_central_estudio,CMg_bloque,CMg_Final_Bloque,Gas_Movilizado_A_Central_Estudio_Bloque/heat_rate_central_estudio*1000,'No']+valores_termicas
        # df_salida=df_salida[['Fecha', 'Hora', 'Central', 'CV Central','CMg Final Bloque', 'Generacion Central Estudio', 'ERROR']]
        df_salida=df_salida.drop('ERROR',axis=1)
        df_salida.to_excel('./Resultados/Resultados_Horarios_Central_'+str(fecha)+'.xlsx',header=True,index=False)
        df_salida_2.to_excel('./Resultados/Desplazamientos_'+str(fecha)+'.xlsx',header=True,index=False)
        # break
            # print(max(Gas_Declarado_Dia,Gas_Centrales_Termicas))
            # print(Gas_Movilizado_A_Central_Estudio/heat_rate_central_estudio*1000,termicas_estudiables['Gen_Desplazada'].sum(),Gen_Marginal_Desplazar)
                
            
        
t1 = time.time()
print("\nTiempo de ejecución ",t1-t0)
# del t0,t1,anno,mes,dia,path_po,CMg_bloque,Gen_central_estudio,tiempo,embarque,central,central_estudio,CMg_final,CMg_Final_Bloque
# del CV_central_estudio,CV_original_marginal,diferencial_gas,fecha,Gas_central_estudio_subbloque,Gas_Centrales_Termicas_Dia
# del Gas_Movilizado_A_Central_Estudio,Gas_Movilizado_A_Central_Estudio_Bloque,gas_termica,Gas_Declarado_Dia,Gen_central_estudio_subbloque,Gen_Centrales_Termicas_Dia,gen_desplazable,gen_desplazada,Gen_final_marginal,Gen_Marginal_Desplazar
# del Gen_Marginal_Desplazar_orig,gen_original,gen_original_marginal,heat_rate,heat_rate_central_estudio,hora,index,Min_Tecnico,Min_Tecnico_Central_Estudio,row,termica,prioridad_central_estudio
    # 
# -*- coding: utf-8 -*-
"""
Created on Sat Oct 14 09:10:01 2023

@author: faull
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

#% Registro centrales marginales por barra
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
#%Del block
del bloque,bloquehorario,df,Regs,Regs_path,Regs_paths,resumen_marginales

#%Algoritmo de la nueva central marginal según bloque horario, usando POs.

POs_path=".\DB\DB_PO"
POs_paths=check_files(POs_path)
POs=[POs_paths[file] for file in POs_paths.keys() if "PO" in file]

path="./DB/DB_SSCC/Respaldos_CO_SC_CCA/02 Costos de Oportunidad/Detalle diario"
CCOs=check_files(path)

df_mintecnicos=pd.read_excel("./Insumos/Minimos_Tecnicos.xlsx",header=[6],usecols = ['Central',"Potencia bruta máxima",'Potencia neta máxima',"Potencia bruta mínima (A.T.)"])


try:
    #Cuánta generación tendrá la central de estudio
    gen_cx_estudio=int(sys.argv[1])
    #Cuál es el costo marginal de la central de estudio
    cmg_central_estudio=int(sys.argv[2])
    #Cuál es el mínimo técnico de la central de estudio
    mintec_cx_estudio=int(sys.argv[3])
except:
    #Cuánta generación tendrá la central de estudio
    gen_cx_estudio=150
    #Cuál es el costo marginal de la central de estudio
    cmg_central_estudio=300
    #Cuál es el mínimo técnico de la central de estudio
    mintec_cx_estudio=0

print(sys.argv)
print(cmg_central_estudio,mintec_cx_estudio)


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
    # if not fecha =="2023070101":
        # continue
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
        #         # #print("\nBloque Costo Cero")
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
                    
                    ##print("Using PO1")
                elif int(hora) in list(range(9,19)):
                    df_generacion=df_generacion[["UNIDADES.1","CV en Quillota.1", "Gen Neta [MWh].1",int(hora)]]
                    df_generacion.columns=["Central","CV en Quillota", "Gen Neta [MWh]"]+[x for x in df_generacion.columns[3:]]
                    ##print("Using PO2")
                elif int(hora) in list(range(19,25)):
                    df_generacion=df_generacion[["UNIDADES.2","CV en Quillota.2", "Gen Neta [MWh].2",int(hora)]]
                    df_generacion.columns=["Central","CV en Quillota", "Gen Neta [MWh]"]+[x for x in df_generacion.columns[3:]]


        
        #Inicio del algoritmo:
        #Paso 1: En función de la fecha/hora seleccionamos el bloque
        po_bloque=None
        #print("\n")
        #Seleccionamos bloque según hora
        if int(hora) in list(range(9)):
            po_bloque=pos_bloque[0]
            #print("Using PO1")
        elif int(hora) in list(range(9,19)):
            po_bloque=pos_bloque[1]
            #print("Using PO2")
        elif int(hora) in list(range(19,25)):
            po_bloque=pos_bloque[2]
            #print("Using PO3")
            
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
        ##print(fecha,hora)
        #print(fecha,hora,periodo_marginacion,gen_req,gen_mintecnico)
        
        if alg_type==1:
            while gen_req>0:
                for index,row in po_bloque.iterrows():
                    
                    #Si no hay generación asociada, avanzamos.
                    if na_map.iloc[index,5]==True:
                        continue
                    #print(row["Central"],
                          #row["Cmg"],
                         # gen_req,
                          #row[po_bloque.columns[5]],
                          #row[po_bloque.columns[5]]*periodo_marginacion/60)
                    
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
                    #     #print("Caso 0")
                    #     aux_updatedict(new_cmgs,row["Central"],[row["Cmg"],periodo_marginacion],1)
                    #     gen_req=gen_max-gen_mintecnico
                    #     gen_required=False
                    #     break
                    
                    if na_map.iloc[index,5]==True:
                        continue
                    
                   
                    
                    
                    
                    #Obtenemos la generación y se pondera por el periodo de marginación.
                    gen=(row[po_bloque.columns[5]]-row["Min_Tecnico"])*periodo_marginacion/60
                    
                    #print("Central, Cmg, Gen_req, Gen_Central_Actual,Gen_Central_Actual_Prorrateada,Gen_Central_Actual_Prorrateada_ConMT")
                    #print(row["Central"],
                          #row["Cmg"],
                          #gen_req,
                          #row[po_bloque.columns[5]],
                          #row[po_bloque.columns[5]]*periodo_marginacion/60,
                          #gen)
                    
                    #   if row["Central"]=="MEJILLONES-CTM3_TG1+TV1_GNL_E":
                        # raise
                    
                    #Caso 1
                    #Si la generación requerida es más que la que tiene la central
                    #Y el Costo marginal es mayor que el de la central de estudio
                    #Removemos toda la generación y vamos a la próxima central.
                    if cmg_actual>=cmg_central_estudio and gen_req>=gen:
                        #print("Caso1")
                        po_bloque.iloc[index,10]=0
                        gen_req=gen_req-gen
                        
                    #Caso 2
                    #Si la generación requerida es más que la que tiene la central
                    #Y el Costo marginal es menor que el de la central de estudio
                    #No removemos y detenemos el algoritmo.
                    elif cmg_actual<cmg_central_estudio and gen_req>=gen:
                        #print("Caso2")
                        #Si la central aún no genera a mínimo técnico, entonces
                        #removemos la energía necesaria y evaluamos.
                        #Si lo que generé es menor que el mínimo técnico
                        if (gen_max-gen_req)<gen_mintecnico:
                            # #print("Generando a min tecnico")
                            #Si la energía de la central es mayor que la que
                            #necesito para alcanzar el min técnico.
                            #Le quito lo necesario
                            if gen>gen_mintecnico-(gen_max-gen_req):
                                ##print(gen>gen_mintecnico-(gen_max-gen_req),gen,gen_mintecnico-(gen_max-gen_req))
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
                        #print("Caso3")
                        aux_updatedict(new_cmgs,row["Central"],[row["Cmg"],periodo_marginacion],1)
                        gen_req=0
                        po_bloque.iloc[index,10]=gen-gen_req
                        gen_required=False
                        break
                    
                    #Caso 4
                    #Si la generación requerida es menor que la que tiene la central
                    #Y el Costo marginal es menor que el de la central de estudio
                    elif gen_req<gen and cmg_actual<cmg_central_estudio:
                        #print("Caso4")
                        #Si la central aún no genera a mínimo técnico, entonces
                        #removemos la energía necesaria y evaluamos.
                        #Si lo que generé es menor que el mínimo técnico
                        if (gen_max-gen_req)<=gen_mintecnico:
                            #print("Generando a min tecnico")
                            #Si la energía de la central es mayor que la que
                            #necesito para alcanzar el min técnico.
                            #Le quito lo necesario
                            if gen>gen_mintecnico-(gen_max-gen_req):
                                ##print(gen>gen_mintecnico-(gen_max-gen_req),gen,gen_mintecnico-(gen_max-gen_req))
                                #Lo que falta para generar a minimo tecnico
                                #print(gen_max,gen_req,gen_mintecnico)
                                delta=gen_max-gen_req+gen_mintecnico
                                #print(delta)
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
                                #print("Si la energia es menor")
                                #Quito toda la energía
                                po_bloque.iloc[index,10]=0
                                #Y la restamos al a generación requerida.
                                gen_req=gen_req-gen
                                #El algoritmo sigue con la próxima central.
                                continue
                        else:
                            #Si ya he generado más del mínimo técnico, entonces
                            #el algoritmo se detiene.
                            #Central de estudio margina.
                            #aux_updatedict(new_cmgs,row["Central"],[row["Cmg"],periodo_marginacion],1)
                            aux_updatedict(new_cmgs,"Central Estudio",[cmg_central_estudio,periodo_marginacion],1)
                            gen_required=False
                            break
            val=(gen_max-gen_req)
            # #print(gen_output)
            # print(val)
            aux_updatedict_gen(gen_output,fecha,val)
            # print(gen_output)
        
            
                    
                
    #Actualizamos diccionario de salida con el nuevo CMG y el antiguo                
    output.update({fecha:[sum([new_cmgs[key][0]*new_cmgs[key][1]/60 for key in new_cmgs.keys()]),costo_marginal]})
        

#% Visualization block
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
fig.write_html("Generacion"+str(cmg_central_estudio)+"_"+str(mintec_cx_estudio)+".html")
df.to_excel("Generacion"+str(cmg_central_estudio)+"_"+str(mintec_cx_estudio)+".xlsx",header=True,index=False)
sys.exit(0)

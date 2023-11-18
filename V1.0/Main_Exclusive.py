# -*- coding: utf-8 -*-
"""
Created on Mon Oct 16 20:55:51 2023

@author: faull
"""

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


debug = True
init_time=time.time()

init_periodo_estudio = str(input("Fecha inicial del periodo de estudio"))
end_periodo_estudio = str(input("Fecha final del periodo de estudio"))

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
    
def marginal_sorted(dicc):
    ordered_dict = dict(sorted(dicc.items(), key=lambda x:x[1][1]))
    reversed_dict = {}
    while ordered_dict:
        key, value = ordered_dict.popitem()
        reversed_dict[key] = value
    return reversed_dict
    
def resta_genpo(po,central,valor):
    #Encuentra la central en la PO
    idx=po_bloque.loc[po_bloque["Central"]==central].index[0]
    #Asigna el valor de generación nuevo en la columna de generación restante.
    po_bloque[po_bloque.columns[-1]][idx]=po_bloque[po_bloque.columns[-1]][idx]-valor
    
    
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


##Perfil de generación
df_gen_entrada=pd.read_excel("./Insumos/Entrada_Modelo.xlsx",header=[0])
df_gen_entrada.columns=["Fecha","Hora","Pmax","Pmin","CV"]
df_gen_entrada["Date"]=None

##Dateformat entry for the simulator:
##YYYYMMDDHH

for index,row in df_gen_entrada.iterrows():
    actual = row["Fecha"]
    hora = row["Hora"]
    df_gen_entrada.iloc[index,5] = actual.strftime("%Y%m%d")+"{0:0=2d}".format(hora)
        
    #df_gen.iloc[index,5] = actual+datetime.timedelta(hours=hora-1)


##Min tecnicos

##P_Reserva paths

df_mintecnicos=pd.read_excel("./Insumos/Minimos_Tecnicos.xlsx",header=[6],usecols = ['Central',"Potencia bruta máxima",'Potencia neta máxima',"Potencia bruta mínima (A.T.)"])
#init_time=time.time()
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
    mintec_cx_estudio=75    

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

#%%
output={}
gen_output={}
for fecha in dicc_marginal.keys():
    # if not fecha in (["20230701"+"%02d" % (x,) for x in range(1,25)]):
    # +["20230702"+"%02d" % (x,) for x in range(1,25)]):
    # if not fecha =="2023070118":
        # continue
    #Para cada fecha
    cx=dicc_marginal[fecha].copy()
    #Para cada central marginal distinta dentro del bloque intra-horario
    new_cmgs={}
    costo_marginal=0
    old_cmgs={}
    periodo_marginacion_acumulado=0
    
    #Entrada horaria:
    valores_horarios = df_gen_entrada.loc[df_gen_entrada["Date"] == fecha]
    ##cmg_central_estudio tiene que ser definido acá.
    cmg_central_estudio = valores_horarios["CV"].values[0]
    ##mintec_cx_estudio tiene que ser definido acá también.
    mintec_cx_estudio = valores_horarios["Pmin"].values[0]
    #gen_cx_estudio tiene que ser definido acá.
    gen_cx_estudio = valores_horarios["Pmax"].values[0]
    
    hora=fecha[-2:]
    PO_asociada=[POs_paths[x] for x in POs_paths.keys() if fecha[2:-2] in x][0]
    df=pd.read_excel(PO_asociada,sheet_name="TCO",header=6)
    pos_bloque=[df[df.columns[1+i*4:4+i*4]] for i in range(3)]
    
    #P_reserva segun mes
    df_preserva = pd.read_excel("./Insumos/Potencia_Reserva_"+str(fecha[:-4])+".xlsx",header=[3],usecols = ['Fecha','Hora','Hora Mensual','Central',"CPF (-).1","CSF (-).1","CTF (-).1"])
    df_preserva["P_reserva"] = df_preserva[df_preserva.columns[4]] + df_preserva[df_preserva.columns[5]] +df_preserva[df_preserva.columns[6]]
    df_preserva["Fecha_formato"] = df_preserva["Fecha"].apply(lambda x: str(x.year)+"{0:0=2d}".format(x.month)+"{0:0=2d}".format(x.day))
    df_preserva["Fecha_formato"] = df_preserva["Fecha_formato"] + df_preserva["Hora"].apply(lambda x: "{0:0=2d}".format(x))

    for subdf in pos_bloque:
        subdf.columns=["N","Central","Cmg"]
    
    for gen_fecha in CCOs.keys():
        if fecha[:-2] in str(gen_fecha):
            path=CCOs[gen_fecha]
            df_generacion=pd.read_excel(path,sheet_name="GenN",header=7)
            if int(hora) in list(range(9)):
                df_generacion=df_generacion[["UNIDADES","CV en Quillota", "Gen Neta [MWh]",int(hora)]]
                df_generacion.columns=["Central","CV en Quillota", "Gen Neta [MWh]"]+[x for x in df_generacion.columns[3:]]
                break
            elif int(hora) in list(range(9,19)):
                df_generacion=df_generacion[["UNIDADES.1","CV en Quillota.1", "Gen Neta [MWh].1",int(hora)]]
                df_generacion.columns=["Central","CV en Quillota", "Gen Neta [MWh]"]+[x for x in df_generacion.columns[3:]]
                break
            elif int(hora) in list(range(19,25)):
                df_generacion=df_generacion[["UNIDADES.2","CV en Quillota.2", "Gen Neta [MWh].2",int(hora)]]
                df_generacion.columns=["Central","CV en Quillota", "Gen Neta [MWh]"]+[x for x in df_generacion.columns[3:]]
                break

    #Paso 1: En función de la fecha/hora seleccionamos el bloque
    po_bloque=None

    #Seleccionamos bloque según hora
    if int(hora) in list(range(9)):
        po_bloque=pos_bloque[0]
        print("Usando PO bloque 1")
    elif int(hora) in list(range(9,19)):
        po_bloque=pos_bloque[1]
        print("Usando PO bloque 2")
    elif int(hora) in list(range(19,25)):
        po_bloque=pos_bloque[2]
        print("Usando PO bloque 3")
        
    #Agregamos Central Costo Cero
    po_bloque.loc[-1]=[0,"COSTO_CERO",0]
    po_bloque.index = po_bloque.index + 1  # shifting index
    po_bloque = po_bloque.sort_index(ascending=True)  # sorting by index

    #Potencia de reserva
    p_reserva_horaria = df_preserva.loc[df_preserva["Fecha_formato"] == fecha]
    
    #Asociamos la generación a la PO.
    #Asociamos la generación desde df_generacion a po_bloque.
    po_bloque = pd.merge(po_bloque, df_generacion, on='Central',how="left")
    po_bloque = pd.merge(po_bloque,df_mintecnicos,on="Central",how="left")
    po_bloque = pd.merge(po_bloque,p_reserva_horaria,on="Central",how="left")
    
    #Agregamos generación infinita a la central Costo Cero.
    po_bloque.loc[po_bloque.Central == "COSTO_CERO", po_bloque.columns[5]] = 999
    
    #Obtenemos minimos técnicos
    ###Funcion que asigna minimos técnicos.
    #Cols K, M and R
    po_bloque["Potencia bruta máxima"] = po_bloque["Potencia bruta máxima"].fillna(0)
    po_bloque["Potencia neta máxima"] = po_bloque["Potencia neta máxima"].fillna(0)
    po_bloque["Potencia neta máxima"] = pd.to_numeric(po_bloque["Potencia neta máxima"], errors='coerce').fillna(0)
    po_bloque["Potencia bruta mínima (A.T.)"] = po_bloque["Potencia bruta mínima (A.T.)"].fillna(0)
    po_bloque["P_reserva"] = po_bloque["P_reserva"].fillna(0)
    
    #Min Tecnico = M/K*R
    po_bloque["Min_Tecnico"] = po_bloque["Potencia bruta máxima"]/po_bloque["Potencia neta máxima"]*po_bloque["Potencia bruta mínima (A.T.)"] + po_bloque["P_reserva"] #+Potencia de reserva.
    po_bloque["Min_Tecnico"] = po_bloque["Min_Tecnico"].fillna(0)
    
    #Asignamos generación restante igual a generación inicial.
    po_bloque["Gen_Restante"] = po_bloque[po_bloque.columns[5]]-po_bloque["Min_Tecnico"]
    
    #Asignamos Cmg a centrales marginales 
    for central in cx.keys():
        periodo_marginacion=cx[central]
        try:
            value=po_bloque.loc[po_bloque["Central"]==central]["Cmg"].values[0]
            cx.update({central:(periodo_marginacion,value)})
        except:
            #print(central)
            cx.update({central:(periodo_marginacion,0)})
    
    #Reordenamos centrales marginales según Cmg. Caras primero.
    #print(cx)
    cx=marginal_sorted(cx)
    #print(cx)
    
    

    #Algoritmo para ordenar las centrales según costo marginal.
    for central in cx.keys():
        if debug:
            print("\n\n")
            print(fecha)
            print(cmg_central_estudio,mintec_cx_estudio,gen_cx_estudio)
        #Periodo de marginación, hora del bloque
        periodo_marginacion=cx[central][0]
        periodo_marginacion_acumulado+=periodo_marginacion
        print(periodo_marginacion)
        #Consideramos también la existencia de los mínimos técnicos.
        gen_req=gen_cx_estudio*periodo_marginacion/60
        gen_max=gen_req
        gen_mintecnico=mintec_cx_estudio*periodo_marginacion/60
        
        #Paso 2: Encontrar central marginal según registro anterior. -> variable "central"
        #Indice de la central
        pos_centralmarginal=po_bloque.loc[po_bloque["Central"]==central].index[0]
        
        #Ordenamos el registro de centrales
        intra_horario=po_bloque.iloc[0:pos_centralmarginal+1].sort_index(ascending=False).copy()
        
        new_pos_centralmarginal=intra_horario.loc[intra_horario["Central"]==central].index[0]
        marginal_real=intra_horario.loc[intra_horario["Central"]==central]['Cmg'][new_pos_centralmarginal]
        
        ##Revisar 
        costo_marginal+=marginal_real*periodo_marginacion/60
        old_cmgs.update({intra_horario.iloc[new_pos_centralmarginal]["Central"]:[marginal_real,periodo_marginacion]})
    
        #Iniciamos algoritmo para descubrir que central es la nueva marginal.
        na_map=intra_horario.isna() 
        gen_required=True
        #print(fecha,hora,periodo_marginacion,gen_req,gen_mintecnico)
        # raise
        # if central=="ELTORO_vlaja1":
        #raise
        if alg_type==1:
            while gen_req>0:
                for index,row in intra_horario.iterrows():
                    
                    #Si no hay generación asociada, avanzamos.
                    if na_map.iloc[index,11]==True:
                        continue
                    
                    #Obtenemos la generación y se pondera por el periodo de marginación.
                    gen=(row[intra_horario.columns[5]]-row["Min_Tecnico"])*periodo_marginacion/60
                    
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
                        intra_horario.iloc[index,10]=gen-gen_req
                        break


        if alg_type==2:
            while gen_required==True:
                for index,row in intra_horario.iterrows():
                    #print(row["Central"],index,na_map.iloc[index,10])
                    
                    
                    #Si no está vacío el CV en Quillota, lo tomo. En otro caso,
                    #Tomamos el de la PO.
                    if not na_map.iloc[index,3]:
                        cmg_actual=row['CV en Quillota']
                    else:
                        cmg_actual=row["Cmg"]

                    if na_map["Gen_Restante"][index]==True:
                        
                        continue
                    
                    
                    #Obtenemos la generación (restante) y se pondera por el periodo de marginación.
                    # gen=row["Gen_Restante"]*periodo_marginacion/60
                    gen=(po_bloque.iloc[index,5]-row["Min_Tecnico"])*periodo_marginacion/periodo_marginacion_acumulado
                    # if periodo_marginacion==16:
                        # raise
                    print("Central, Cmg, Gen_req, Min Tecnico, Gen_Central_Actual_Prorrateada_ConMT, Unidad")
                    if debug:
                        print(row["Central"],
                              row["Cmg"],
                              gen_req,
                              row["Min_Tecnico"],
                              #row[po_bloque.columns[5]],
                              #row[po_bloque.columns[5]]*periodo_marginacion/60,
                              gen,
                              row["Gen Neta [MWh]"])
                    
                    # if row["Central"]=="CANDELARIA-1_GNL_C":
                        # raise
                    
                    #Caso 1
                    #Si la generación requerida es más que la que tiene la central
                    #Y el Costo marginal es mayor que el de la central de estudio
                    #Removemos toda la generación y vamos a la próxima central.
                    if cmg_actual>=cmg_central_estudio and gen_req>=gen:
                        if debug:
                            print("Caso1")
                        resta_genpo(po_bloque, row["Central"], gen)
                        #intra_horario.iloc[index,10]=0
                        gen_req=gen_req-gen
                        
                        
                    #Caso 2
                    #Si la generación requerida es más que la que tiene la central
                    #Y el Costo marginal es menor que el de la central de estudio
                    #No removemos y detenemos el algoritmo.
                    elif cmg_actual<cmg_central_estudio and gen_req>=gen:
                        if debug:
                            print("Caso2")
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
                                resta_genpo(po_bloque, row["Central"], delta)
                                #intra_horario.iloc[index,10]=(gen-delta)
                                #Detengo el algoritmo.
                                gen_required=False
                                #La central a la que se le quitó generación margina.
                                aux_updatedict(new_cmgs,row["Central"],[row["Cmg"],periodo_marginacion],1)
                                break
                            #Si la energía es menor que la que requiero
                            else:
                                #Quito toda la energía
                                resta_genpo(po_bloque, row["Central"], gen)
                                #intra_horario.iloc[index,10]=0
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
                        if debug:
                            print("Caso3")
                        aux_updatedict(new_cmgs,row["Central"],[row["Cmg"],periodo_marginacion],1)
                        gen_req=0
                        resta_genpo(po_bloque, row["Central"], gen_req)
                        #intra_horario.iloc[index,10]=gen-gen_req
                        gen_required=False
                        break
                    
                    #Caso 4
                    #Si la generación requerida es menor que la que tiene la central
                    #Y el Costo marginal es menor que el de la central de estudio
                    elif gen_req<gen and cmg_actual<cmg_central_estudio:
                        if debug:
                            print("Caso4")
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
                                resta_genpo(po_bloque, row["Central"], delta)
                                #intra_horario.iloc[index,10]=(gen-delta)
                                #Detengo el algoritmo.
                                gen_required=False
                                #La central a la que se le quitó generación margina.
                                aux_updatedict(new_cmgs,row["Central"],[row["Cmg"],periodo_marginacion],1)
                                break
                            #Si la energía es menor que la que requiero
                            else:
                                #print("Si la energia es menor")
                                #Quito toda la energía
                                intra_horario.iloc[index,10]=0
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
    
    #raise

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
    title="Nuevo Costo Marginal calculado vs Marginal real en el periodo de estudio para la central "+str(central_estudio)+" Caso "+str(cmg_central_estudio)+"_"+str(mintec_cx_estudio),
    xaxis_title="Hora del día",
    yaxis_title="Costo Marginal [$US/MWh]",
    legend_title="Periodo de estudio",
)


fig.show()
#fig.write_html("Nuevos_CMgs.html")
#df.to_excel("Nuevos_CMgs.xlsx",header=True,index=False)
df.to_excel("Nuevos_CMgs"+str(cmg_central_estudio)+"_"+str(mintec_cx_estudio)+".xlsx",header=True,index=False)
fig.write_html("Nuevos_CMgs"+str(cmg_central_estudio)+"_"+str(mintec_cx_estudio)+".html")


df=pd.DataFrame(columns=["Día","Hora","Gen",])
for key in gen_output.keys():
    fecha=key
    dia=fecha[:-2]
    hora=fecha[-2::]
    df.loc[len(df)+1]=[dia,hora,gen_output[key]]

    

#fig = px.line(df, x="Hora", y="Nuevo CMg", color="Día",markers=True)

fig = go.Figure()
color_counter = 1


for sdf in df_gen_entrada.groupby(by="Fecha"):
    #Quiero obtener el día, para agregarlo como trace.
    dia=str(sdf[0].year)+"{0:0=2d}".format(sdf[0].month)+"{0:0=2d}".format(sdf[0].day)
    fig.add_trace(go.Scatter(x=sdf[1]["Hora"], y=sdf[1]["Pmin"],
                    mode='markers',
                    marker_color=fig.layout['template']['layout']['colorway'][color_counter],
                    name='Generación - Archivo Entrada',legendgroup=dia,
                    legendgrouptitle_text=dia))
    
    color_counter+=1
    if color_counter==10:
        color_counter=0

color_counter = 0 

for sdf in df.groupby("Día"):
    fig.add_trace(go.Scatter(x=sdf[1]["Hora"], y=sdf[1]["Gen"].apply(lambda x: round(x,3)),
                    mode='lines',
                    marker_color=fig.layout['template']['layout']['colorway'][color_counter],
                    name='Generación Simulada',legendgroup=sdf[0],  # this can be any string, not just "group"
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

print(time.time()-init_time)
sys.exit(0)

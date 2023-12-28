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
from datetime import date, timedelta
import logging

logging.basicConfig(filename="simulacion.log", 
					format='%(asctime)s %(message)s', 
					filemode='w') 

logger=logging.getLogger() 
logger.setLevel(logging.DEBUG) 

debug = True
init_time=time.time()
init_periodo_estudio = str(input("Fecha inicial del periodo de estudio (AAAAMMDDHH) : "))
end_periodo_estudio = str(input("Fecha final del periodo de estudio (AAAAMMDDHH) :"))

warnings.filterwarnings('ignore')

#check_input_files("Mensual",fecha,Regs)
def check_input_files(fecha):
    #fecha en formato AAAAMMDDHH
    mensual = fecha[:-4]
    diario = fecha[:-2]
    #Variables
    Regs_files,POs_files,CCOs_files,PRs_files = 0,0,0,0
    ##Regs -> Mensual
    ##POs -> Diario
    ##CCOs -> Diario
    ##PRs -> Mensual
    check_ok = 1
    #Regs check
    for file in Regs:
        if mensual in file:
            Regs_files = 1
    #POs check
    for file in POs:
        if diario in file:
            POs_files = 1
            
    #CCOs check
    for file in list(CCOs.keys()):
        if diario in file:
            CCOs_files = 1
            
    #PRs check
    for file in PRs:
        if mensual in file:
            PRs_files = 1
            
    if Regs_files == 0:
        check_ok = 0
        logger.debug("No se encuentran archivos de registro asociados a la fecha "+fecha)
    if POs_files == 0:
        check_ok = 0
        logger.debug("No se encuentran archivos de políticas de operación asociados a la fecha "+fecha)
    if CCOs_files == 0:
        check_ok = 0
        logger.debug("No se encuentran archivos de Costo de Oportunidad asociados a la fecha "+fecha)
    if PRs_files == 0:
        check_ok = 0
        logger.debug("No se encuentran archivos de Potencia de Reserva asociados a la fecha "+fecha)
    return check_ok


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
    
    
#Creacion de directorios
general_dirs = ["DB", "Insumos","./DB/DB_PO","./DB/DB_CmgFpen","./DB/DB_SSCC"]
for directorio in general_dirs:
    if not os.path.exists(directorio):
        os.mkdir(directorio)
        logger.info("La carpeta "+directorio+" ha sido creada")
        


central_estudio="150 MW parejo."

#% Registro centrales marginales por barra
##Esta sección retorna un diccionario que contiene todos los bloques horarios
##con un resumen de las centrales marginales y minutos marginados.

Regs_path="./DB/DB_CmgFpen"
Regs_paths=check_files(Regs_path)
Regs=[Regs_paths[file] for file in Regs_paths.keys() if ("Registro" in file and ".xlsx" in file)]

if Regs == []:
    logger.info("Directorio de registros vacío")
    input("Directorio de registros vacío, presione para continuar")

#Multiple df extraction
dicc_marginal={}

for file in Regs:
    df=pd.read_excel(file,header=[0])
    df["Bloque_horario"]=(df["Mes"].astype(str)
                        +df["Día"].apply(lambda x:"%02d" % (x,)).astype(str)
                        +df["Hora"].apply(lambda x:"%02d" % (x,)).astype(str))

    for bloque in df.groupby("Bloque_horario"):
        bloquehorario=bloque[0]
        resumen_marginales = bloque[1].pivot_table(index = [bloque[1].columns[4]],
                                                aggfunc ='size').to_dict()
        dicc_marginal.update({bloquehorario:resumen_marginales})


#%Algoritmo de la nueva central marginal según bloque horario, usando POs.

POs_path=".\DB\DB_PO"
POs_paths=check_files(POs_path)
POs=[POs_paths[file] for file in POs_paths.keys() if "PO" in file]

if POs == []:
    logger.info("Directorio de PO vacío")
    input("Directorio de PO vacío, presione para continuar")
    

path="./DB/DB_SSCC/CCO Diarios"
CCOs=check_files(path)

if CCOs == []:
    logger.info("Directorio de CCOs vacío")
    input("Directorio de CCOs vacío, presione para continuar")
    

    
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

##Yet to process and aggregate per month.
#P_reserva segun mes
PR_paths="./Insumos"
PRs_paths=check_files(PR_paths)
PRs=[PRs_paths[file] for file in PRs_paths.keys() if "Potencia_Reserva" in file]

potencias_reserva = pd.DataFrame()

for file in PRs:
    df_preserva = pd.read_excel(file,header=[3],usecols = ['Fecha','Hora','Hora Mensual','Central',"CPF (-).1","CSF (-).1","CTF (-).1"])
    df_preserva["P_reserva"] = df_preserva[df_preserva.columns[4]] + df_preserva[df_preserva.columns[5]] +df_preserva[df_preserva.columns[6]]
    df_preserva["Fecha_formato"] = df_preserva["Fecha"].apply(lambda x: str(x.year)+"{0:0=2d}".format(x.month)+"{0:0=2d}".format(x.day))
    df_preserva["Fecha_formato"] = df_preserva["Fecha_formato"] + df_preserva["Hora"].apply(lambda x: "{0:0=2d}".format(x))
    potencias_reserva = potencias_reserva._append(df_preserva)
    
potencias_reserva = potencias_reserva.drop_duplicates()

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

fechas_estudio = []
start_dt = date(int(init_periodo_estudio[:4]), int(init_periodo_estudio[4:6]), int(init_periodo_estudio[6:8]))
end_dt = date(int(end_periodo_estudio[:4]), int(end_periodo_estudio[4:6]), int(end_periodo_estudio[6:8]))
deltafechas = timedelta(days=1)
while start_dt <= end_dt:
    fechas_estudio.append(start_dt.isoformat())
    start_dt+=deltafechas

fechas_estudio = [x.replace("-","")+"{0:0=2d}".format(k) for x in fechas_estudio for k in range(1,25)]


removable_dates=[]
for fecha in fechas_estudio:
    if end_periodo_estudio[:-2] in fecha:
        if int(fecha[-2:])>int(end_periodo_estudio[-2:]):
            removable_dates.append(fecha)

for date in removable_dates:
    fechas_estudio.remove(date)

##Checking layer for input files.
for fecha in fechas_estudio:
    if not check_input_files(fecha):
        print("Error con datos de entrada para la fecha ",fecha)
        input("Presione Enter para continuar")


#%%
output={}
gen_output={}
#fechas_estudio = ["2023070108"]
for fecha in dicc_marginal.keys():
    if fecha not in fechas_estudio:
        continue
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
        logger.debug("Usando PO bloque 1")
    elif int(hora) in list(range(9,19)):
        po_bloque=pos_bloque[1]
        logger.debug("Usando PO bloque 2")
    elif int(hora) in list(range(19,25)):
        po_bloque=pos_bloque[2]
        logger.debug("Usando PO bloque 3")
        
    #Agregamos Central Costo Cero
    po_bloque.loc[-1]=[0,"COSTO_CERO",0]
    po_bloque.index = po_bloque.index + 1  # shifting index
    po_bloque = po_bloque.sort_index(ascending=True)  # sorting by index

    #Potencia de reserva
    p_reserva_horaria = potencias_reserva.loc[potencias_reserva["Fecha_formato"] == fecha]
    
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
            #print("\n\n")
            logger.debug(fecha)
            logger.debug("Costo marginal, minimo tecnico y generación requerida de la central de estudio en esta hora")
            print(fecha)
            logger.debug(",".join([str(x) for x in [cmg_central_estudio,mintec_cx_estudio,gen_cx_estudio]]))
            print(cmg_central_estudio,mintec_cx_estudio,gen_cx_estudio)
        #Periodo de marginación, hora del bloque
        periodo_marginacion=cx[central][0]
        periodo_marginacion_acumulado+=periodo_marginacion
        print(periodo_marginacion)
        logger.debug("Duracion subperiodo: " + str(periodo_marginacion))
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
                    if gen <0:
                        gen = 0
                    # if periodo_marginacion==16:
                        # raise
                    print("Central, Cmg, Generacion requerida para el subperiodo, Min Tecnico de la central, Gen Central en el supberiodo, Unidad")
                    logger.debug("Central, Cmg, Generacion requerida para el subperiodo, Min Tecnico de la central, Gen Central en el supberiodo, Unidad")
                    if debug:
                        print(row["Central"],
                              row["Cmg"],
                              gen_req,
                              row["Min_Tecnico"],
                              #row[po_bloque.columns[5]],
                              #row[po_bloque.columns[5]]*periodo_marginacion/60,
                              gen,
                              row["Gen Neta [MWh]"])
                        logger.debug(",".join([str(x) for x in [row["Central"],row["Cmg"],gen_req,row["Min_Tecnico"],gen,row["Gen Neta [MWh]"]]]))
                    # if row["Central"]=="CANDELARIA-1_GNL_C":
                        # raise
                    
                    #Caso 1
                    #Si la generación requerida es más que la que tiene la central
                    #Y el Costo marginal es mayor que el de la central de estudio
                    #Removemos toda la generación y vamos a la próxima central.
                    if cmg_actual>=cmg_central_estudio and gen_req>=gen:
                        if debug:
                            print("Caso1")
                            logger.debug("Caso1")
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
                            logger.debug("Caso2")
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
                            logger.debug("Caso3")
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
                            logger.debug("Caso4")
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


df=pd.DataFrame(columns=["Día","Hora","Nuevo CMg", "CMg Original"])

for key in output.keys():
    fecha=key
    dia=fecha[:-2]
    hora=fecha[-2::]
    df.loc[len(df)+1]=[dia,hora,output[key][0],output[key][1]]

df.to_excel("Nuevos_CMgs.xlsx",header=True,index=False)



df=pd.DataFrame(columns=["Día","Hora","Gen",])
for key in gen_output.keys():
    fecha=key
    dia=fecha[:-2]
    hora=fecha[-2::]
    df.loc[len(df)+1]=[dia,hora,gen_output[key]]

    
df.to_excel("Generacion.xlsx",header=True,index=False)

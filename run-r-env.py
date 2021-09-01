from database import SQLiteConnection
import os


# Cambia al directorio rdc/ donde se encuentran los scripts de R
os.chdir("../rdc")

sqlite = SQLiteConnection("database.db")
conn = sqlite.db_connection()

sqlite.create_flag_table(conn)
restored_renv = sqlite.select_flag(conn, "R_ENVIRONMENT")[2]
if not restored_renv:
    os.system("rscript  -e \"renv::restore()\"")
    # Se tiene que confirmar el restore
    #os.system("y")
    os.system("rscript solo_modelo_metadatos.r")
    sqlite.update_flag(conn, [1, "R_ENVIRONMENT"])
conn.close()

for i in range(1000):
    print("#########################")
    print(f"# INTENTO {str(i).zfill(4)} de 1000 #")
    print("#########################")
    os.system("rscript generar_datos.r 1")
    os.system(f"rscript modelo_servido.r muestra.csv resultados{i}.csv")
    os.chdir("../analisis-de-resultados")
    os.system(f"python decision-maker.py {i}")
    os.chdir("../rdc")
    os.system("move muestra.csv D:/anaconda3/envs/ML-Adapting/rdc/del")
    os.system(f"move resultados{i}.csv D:/anaconda3/envs/ML-Adapting/rdc/del")
print("#############################")
print("# SE TERMINARON LAS PRUEBAS #")
print("#############################")
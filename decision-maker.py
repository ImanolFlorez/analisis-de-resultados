from database import SQLiteConnection
import pandas as pd
import numpy as np


def get_unique_elements(elements: list)-> set:
    """
    Recibe una lista con las posibles categorías arrojadas por los modulos
    de clasificación y retorna un conjuto de las categorias sin repetidos.\n
    Parametros:\n
    elements: lista que contiene las posibles categorías.\n
    Retorna:\n
    Un conjunto que contiene las categorías sin repetir
    """
    # Se instancia un conjunto vacio
    uniques = set()
    # Se recorren los elementos de la lista
    for element in elements:
        # Se agregan las llaves de los elementos de la lista al conjunto
        uniques.update(element.keys())
    return uniques


def add_area_to_db(areas: list):
    """
    Recibe una lista con las posibles áreas y verifica cuales no se encuentran en la base
    de datos SQLite y las agrega.\n
    Parametros:\n
    areas: lista con las posibles áreas predichas por los modulos de clasificación.
    """
    sqlite = SQLiteConnection("database.db")
    conn = sqlite.db_connection()
    # Vuelve los registros devueltos por la base de datos en un arreglo de Numpy
    # y solo toma la segunda columna que posee el nombre de las áreas.
    areas_in_db = np.array(sqlite.select_all_area(conn))
    if not areas_in_db.size:
        # Si la tabla está vacia agrega todas las categorias
        for element in areas:
            sqlite.insert_area(conn, element)
            print(f"{element} fue insertado en la tabla de Áreas.")
    else:
        # Si la tabla no está vacia verifica si hay algún elemento nuevo y lo agrega
        for element in areas:
            if element not in areas_in_db[:,1]:
                sqlite.insert_area(conn, element)
                print(f"{element} fue insertado en la tabla de Áreas.")
            else:
                print(f"El área {element} ya se encuentra en la base de datos.")
    conn.close()


def first_filter(inputs: pd.DataFrame) -> dict:
    """
    Verifica si un porcentaje de las posibles áreas es mayor o igual a un porcentaje de
    confiabilidad alojado en la base de datos.
    Parametros:\n
    inputs: DataFrame con las salidas de los módulos de clasificación.
    Retorna:\n
    Un valor booleano indicando si se debe aplicar el segundo filtro.
    Un diccionario indicando el área de clasificación que decidió y
    el porcentaje de confiabilidad.
    """
    sqlite = SQLiteConnection("database.db")
    conn = sqlite.db_connection()
    # Obtiene el porcentaje de confiabilidad de la base de datos SQLite.
    percentage = sqlite.select_parameter(conn, "porc_conf")[2]
    conn.close()
    # Obtiene las posiciones de los valores mayores o iguales al porcentaje de confianza
    indexes = np.where(inputs >= percentage)
    # Crea una lista con las posiciones
    indexes = list(zip(indexes[0], indexes[1]))
    if len(indexes) == 0:
        # Si no hay ningun valor mayor o igual al procentaje de confianza (lista vacia)
        return True, inputs
    elif len(indexes) == 1:
        # Si solo existe un valor mayor o igual al procentaje de confianza (un elemento en la lista)
        return False, {"decision":{"area": str(inputs.iloc[inputs.values >= percentage].index[0]),
                "porc_conf": inputs.iloc[indexes[0]]}, "others": []}
    else:
        # Si hay más de un valor mayor o igual al procentaje de confianza (más de un elemento en la lista)
        return True, inputs.iloc[inputs.values >= percentage]


def second_filter(inputs: pd.DataFrame)-> dict:
    """
    Obtiene el promedio de los porcentajes de aquellas áreas que superen el primer
    filtro. Con el promedio mayor se definirá un rango de la siguiente forma:\n
    rango = [promedio mayor - marg_error, promedio mayor]\n
    Devolverá aquel valor que se encuentre dentro del rango, en caso de ser más de uno,
    devolverá todos los valor dentro del rango y el usuario debe escoger el área que mejor
    considere.\n
    Parametros:\n
    inputs: DataFrame con las áreas que pasaron el primer filtro.
    Retorna:\n
    Área(s) que se encuentre(n) dentro rango definido.
    """
    # Crea un DataFrame con una única columna que contiene el promedio de la áreas
    avg_inputs = pd.DataFrame(inputs.mean(axis=1), index=inputs.index, columns=["avg"])
    sqlite = SQLiteConnection("database.db")
    conn = sqlite.db_connection()
    err_marg = sqlite.select_parameter(conn, "marg_err")[2]
    conn.close()
    # Calcula el rango
    allowed_range = [float(avg_inputs.max() - err_marg), float(avg_inputs.max())]
    # Aquellos valores del DataFrame que estén dentro del rango
    in_range_df = avg_inputs.query(f"{allowed_range[0]} <= avg <= {allowed_range[1]}")
    # Ordena los porcentajes de manera descendiente
    in_range_df = in_range_df.sort_values(by="avg", ascending=False)
    if (in_range_df.shape[0] == 1):
        # Si solo un valor existe dentro del rango
        return {"decision":{"area": in_range_df.index[0], "porc_conf": in_range_df.iloc[0, 0]},
                "others": []}
    else:
        # Si hay más de un valor dentro del rango
        output_list = []
        d = {"decision": {"area": in_range_df.index[0], "porc_conf": in_range_df.iloc[0, 0]},
             "others": output_list}
        for i, avg in enumerate(in_range_df["avg"][1:], start=1):
            inner_dict = {"area": in_range_df.index[i], "porc_conf": avg}
            output_list.append(inner_dict)
        d["others"] = output_list
        return d


def decision(inputs: pd.DataFrame)-> dict:
    """
    Recibe un DataFrame que contiene las salidas de los respectivos
    modulos de clasificación: texto, metadatos e imágenes; y determina
    a que categoría pertenece.\n
    Parametros:\n
    inputs: DataFrame con las salidas de los modulos de clasificación.\n
    Retorna:\n
    Un diccionario indicando el área de clasificación que decidió y
    el porcentaje de confiabilidad.
    """
    # Inserta aquellas áreas que no se encuentren en la base de datos.
    add_area_to_db(list(inputs.index))
    apply_second_filter, results = first_filter(inputs)

    if apply_second_filter:
        results = second_filter(results)

    # Actualiza la columna 'timesChosen' del área seleccionada
    sqlite = SQLiteConnection("database.db")
    conn = sqlite.db_connection()
    timesChosen = sqlite.select_area(conn, results["decision"]["area"])[2] + 1
    sqlite.update_area(conn, [timesChosen, results["decision"]["area"]])
    conn.close()

    return results


if __name__ == "__main__":    # Crea la base de datos SQL si no existe.
    sqlite = SQLiteConnection("database.db")
    conn = sqlite.db_connection()
    cur = conn.cursor()
    # Se pregunta si las tablas 'Areas' y 'Parameters' existen.
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('Areas', 'Parameters')")
    tables = np.array(cur.fetchall()).flatten().tolist()
    if 'Areas' not in tables and 'Parameters' not in tables:
        # Si 'Areas' y 'Parameters' no están en los resultados del query anterior quiere decir
        # que no han sido creadas, por lo tanto, se pcede a crearlas.
        sqlite.create_area_table(conn)
        sqlite.create_parameters_table(conn)
        # Inserta los parametros en la tabla de de parametros
        sqlite.insert_parameter(conn, ["porc_conf", 0.88])
        sqlite.insert_parameter(conn, ["marg_err", 0.05])
    conn.close()

    input_df = pd.read_csv("../rdc/resultados.csv").transpose()
    input_df = input_df.drop(["path", "tipo", ".pred_class"])
    # Convierte el diccionario de entrada en un DataFrame de Pandas reemplazando
    # los Na/NaN por ceros.
    input_df = pd.DataFrame(input_df).fillna(0)
    print(decision(input_df))

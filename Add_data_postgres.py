import psycopg2
import numpy as np

class Add_data_postgres:
     def __init__(self, database, user, password, host, port):
        self.con = psycopg2.connect(database=database, user=user,\
                password=password, host=host, port=port)
        self.cur = self.con.cursor()

     def insert_data_param(self, dict_param, play_time,status):
          """
          esta funcion agrega los datos a la base de datos
          dict_param: diccionario con los datos a agregar
          id: id del dato a agregar, string
          length_word:  largo del dato a agregar, entero
          vawels: cantidad de vocales del dato a agregar, entero
          consonants: cantidad de consonantes del dato a agregar, entero
          las anteriores son las claves del diccionario
          """
          self.cur.execute("INSERT INTO juegos(id,amount_vawels,\
          amount_consonants,play_time,status) VALUES(%s, %s, %s, %s, %s)", \
          (dict_param['id'], dict_param['vowels'],\
          dict_param['consonants'], play_time,status))
          self.con.commit()
          # self.cur.close()
          print("Add data success")
     
     def insert_data_result(self, primary_key, dict_param,dict_result, attempts_time):
          """
          Esta funcion se encarga de agregar los datos del diccionario a la base de datos
          primary_key: es la clave primaria de la tabla juegos
          dic_data es el diccionario con los siguientes datos a agregar:
          id: id del juego que se esta jugando, string
          word_sent: palabra que se envio en el intento
          score: puntaje del intento, enteto
          datatime: fecha y hora del intento, string
          pisition_array: posiciones de las letras en la palabra, lista booleana
          amount_of_true: cantidad de letras correctas, entero no viene el el diccionario
          amount_of_false: cantidad de letras incorrectas, entero no viene en el diccionario
          array_letters_in_wrong_position: letras en la posicion incorrecta, lista string
          amount_letters_in_wrong_position: cantidad de letras en la posicion incorrecta, entero
          no viene en el diccionario
          current_attemps: numero de intentos
          attempst_time: tiempo que tarda por inteto, entero
          """
          # se mira la cantidad de letras incorretes en la palabra
          amount_letters_in_wrong_position = len(dict_result['right_letters_in_wrong_positions'])
         
          # se agrega los datos a la base de datos
          self.cur.execute("INSERT INTO intentos(id_game,id,word_sent,score,\
               datetime,position_array,amount_letters_in_wrong_positions,\
               current_attemps,attempt_time)\
               VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)", \
                (primary_key, dict_param['id'], dict_result['word_sent'], dict_result['score'],\
                dict_result['try_datetime'], dict_result['position_array'],\
                amount_letters_in_wrong_position, dict_result['current_attemps'],\
                attempts_time))
          # se guarda los cambios en la base de datos
          self.con.commit()
          
          print("Add data success")
     
     def close_connection(self):
          """
          esta funcion cierra la conexion con la base de datos
          """
          self.con.close()
          print("Connection closed")

     def select_table(self,name_table):
          """
          esta funcion selecciona todos los datos de la tabla
          """
          self.con = self.con
          cursor = self.con.cursor()
          cursor.execute("SELECT * FROM %s" % name_table)
          rows = cursor.fetchall()
          cursor.close()
          return rows

     def select_colomn_table(self,name_table,name_colomn):
          """
          esta funcion selecciona todos los datos de la tabla
          """
          self.con = self.con
          cursor = self.con.cursor()
          cursor.execute("SELECT %s FROM %s" % (name_colomn,name_table))
          rows = cursor.fetchall()
          return rows




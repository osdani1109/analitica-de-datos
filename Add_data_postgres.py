import psycopg2
import numpy as np

class Add_data_postgres:
     def __init__(self, database, user, password, host, port):
        self.con = psycopg2.connect(database=database, user=user,\
                password=password, host=host, port=port)
        self.cur = self.con.cursor()

     def insert_data_param(self, dict_param, play_time):
          """
          esta funcion agrega los datos a la base de datos
          dict_param: diccionario con los datos a agregar
          id: id del dato a agregar, string
          length_word:  largo del dato a agregar, entero
          vawels: cantidad de vocales del dato a agregar, entero
          consonants: cantidad de consonantes del dato a agregar, entero
          las anteriores son las claves del diccionario
          """
          self.cur.execute("INSERT INTO parametros_del_juego(id,length_word,amount_vawels,amount_consonants,play_time)\
          VALUES(%s, %s, %s, %s, %s)", (dict_param['id'], dict_param['length_word'], dict_param['vowels'],\
          dict_param['consonants'], play_time,))
          self.con.commit()
          # self.cur.close()
          print("Add data success")
     
     def insert_data_result(self, dict_param,dict_result, attempts_time):
          """
          Esta funcion se encarga de agregar los datos del diccionario a la base de datos
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
          array_position = np.array(dict_result['position_array'])
          # se mira la cantidad de letras correctas
          amount_of_true = np.where(array_position == True)
          amount_of_true = len(amount_of_true[0])
          # se mira la cantidad de letras incorrectas
          amount_of_false = np.where(array_position == False)
          amount_of_false = len(amount_of_false[0])
          # se agrega los datos a la base de datos
          self.cur.execute("INSERT INTO resultados(id,word_sent,score,\
               datetime,position_array,amount_of_true,amount_of_false,\
               array_letters_in_wrong_positions,amount_letters_in_wrong_positions,\
               current_attemps,attempt_time)\
               VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", \
                (dict_param['id'], dict_result['word_sent'], dict_result['score'],\
                dict_result['try_datetime'], dict_result['position_array'], amount_of_true,\
                amount_of_false, dict_result['right_letters_in_wrong_positions'],\
                amount_letters_in_wrong_position, dict_result['current_attemps'],\
                attempts_time,))
          # se guarda los cambios en la base de datos
          self.con.commit()
          self.cur.close()
          print("Add data success")
       

     def select_table(self,name_table):
          """
          esta funcion selecciona todos los datos de la tabla
          """
          self.con = self.con
          cursor = self.con.cursor()
          cursor.execute("SELECT * FROM %s" % name_table)
          rows = cursor.fetchall()
          print(rows)
          cursor.close()
          return rows

dic_data = {'id': '62bdb48c8d949c9a49ffa7fc', 'length_word': 12, 'vowels': 5, 'consonants': 7}
dic_data2 = {'word_sent': 'describiendo', 'score': 0.08333333333333333, 
'try_datetime': '2022-06-30T14:34:53.700117', 
'position_array': [False, False, False, False, False, False, False, False, False, True, False, False], 
'right_letters_in_wrong_positions': ['s', 'r', 'i', 'o'], 'current_attemps': 1}
save_data = Add_data_postgres("wordle_hqiu",
                               "osdani1109", 
                               "xlZC8coyZEuyIrxbCYSs79BxmsyLRLGW",
                               "ohio-postgres.render.com",
                               "5432")

save_data.insert_data_param(dic_data,0.2)
save_data.insert_data_result(dic_data,dic_data2,0.2)
save_data.select_table("resultados")


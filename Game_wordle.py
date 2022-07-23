import numpy as np
import pandas as pd
import re
import random
import requests
import json
import time
import Add_data_postgres as adp

class Game_wordle:
    def __init__(self, endpoint_get, endpoint_post, database, user, password):
        self.endpoint_post = endpoint_post
        self.endpoint_get = endpoint_get
        # se crea diccionario para la respusta del servidor
        # response_get: guarda los parametros de la palabra
        self.response_get = {}
        # response_post: guarda el resultado de la palabra
        self.response_post = {}
        # database: es la base de datos de palabras
        self.database = database
        # dataframe: es un dataframe con la base de datos vacia
        # con el fin trabajar con facilidad los datos
        self.dataframe = pd.DataFrame()
        # se crea un diccionario para almacenar la palabra para 
        # enviarla al servidor
        self.request_post_word = {}
        # credenciales 
        self.user = user
        self.password = password
        # lista para guardar los intentos del juego
        self.list_attempts = []
        # varialbes para calcular tiempos 
        self.times = []
        self.start_time_get = 0
        self.end_time_get = 0
        self.start_time_post = 0
        self.end_time_post = 0

    def star_game(self):
        """
        para comenzar el juego se pide la palabra al servidor
        el serividor devuelve en un archivo json con lo siguiente:
        ● id: Un identificador único del juego generado
        ● length_word: Longitud de la palabra asignada
        ● vowels: Número de vocales en la palabra
        ● consonants: Número de consonantes en la palabra
        """
        # se hace la solicitud al servidor para iniciar el juego
        self.response_get = requests.get(self.endpoint_get, auth = (self.user,self.password))
        print("respuesta del servidor",self.response_get)
        # se guarda el tiempo de inicio de la solicitud
        self.start_time_get = time.time()
        # se  trasnforma en un json response_get
        self.response_get = self.response_get.json()

    def quantity_vawols_consonats(self, database):
        """
        Esta funcion cuenta la cantidad de vocales y consontates
        por palabra, la cantidad de vocales y consonantes son almacenadas
        en su correspodiente lista, la cual es retornada al final
        database: es una lista de palabras
        """
        quantity_vawols = []
        quantity_consonats = []
        cont_vawels = 0
        cont_consonants = 0
        for word in database:
            # se crea un regex para encontrar solo las letras
            cont_vawels = len(re.findall("[aeiou]", word))
            cont_consonants = len(re.findall("[b-df-hj-np-tv-xz]", word))
            quantity_vawols.append(cont_vawels)
            quantity_consonats.append(cont_consonants)

        return quantity_vawols, quantity_consonats

    def create_dataframe(self):
        """
        Esta funcion se encarga de crear un dataframe con las palabras que tiene la siguiente estructura:
        ● Word: Palabra
        ● Word length: Longitud de la palabra
        ● Vawols: Número de vocales en la palabra
        ● Consonts: Número de consonantes en la palabra
        database: es la base de datos de palabras
        """
        self.dataframe["Words"] = self.database.split(" ")
        self.dataframe["Word length"] = [len(w) for w in self.dataframe["Words"]]
        quantity_vawols, quantity_consonats = self.quantity_vawols_consonats(self.dataframe["Words"])
        self.dataframe["Vawols"] = quantity_vawols
        self.dataframe["Consonts"] = quantity_consonats

    def filter_words(self):
        """
        Esta funcion se encargar de filtra en la base de datos la cantidad de palabras
        con las caracteristicas dadas por el juego al hacer una solicitud a la API
        ● id: Un identificador único del juego generado
        ● length_word: Longitud de la palabra asignada
        ● vowels: Número de vocales en la palabra
        ● consonants: Número de consonantes en la palabra
        """
        data_filter = self.dataframe
        data_filter = data_filter[((data_filter["Word length"] == self.response_get["length_word"]) &
                                    (self.dataframe["Vawols"] == self.response_get["vowels"]) &
                                    (self.dataframe["Consonts"] == self.response_get["consonants"]))]
        return data_filter

    def random_word_filters(self, filter_words):
        """
        Esta funcion se encarga de escoger una palabra al azar de las filtradas
        para ser enviada al post
        filter_words: es una lista de palabras filtradas de la cual se escoge una palabra al azar
        """
        word = random.choice(filter_words)
        return word

    def request_post(self, response):
        """
        Esta funcion se encarga de enviar la palabra al servidor
        response: es a un diccionario con la palabra 
        {
         "result_word": "string"
        }
        respuesta del servidor en formato json
        {
            "word_sent": "string",
            "score": float,
            "try_datetime": datetime,
            "position_array": [false,true,false,false,false],
            "right_letters_in_wrong_positions": ["string","string"]
        }
        """
        self.response_post = requests.post(self.endpoint_post, json = response, auth = (self.user,self.password))
        # se guarda el tiempo de inicio de la solicitud
        self.start_time_post = time.time()
        # respuesta del servidor en formato json
        self.response_post = self.response_post.json()
        # se almacena la respuesta en una lista
        self.list_attempts.append(self.response_post)

    def wrong_letters(self,word):
        """
        Esta funcion recibe como parametro la palabra que se envio 
        se encarga de buscar las letras que no estan en la palabara y a su vez 
        marcar las letras que se encuentra en la palabra pero en la posición incorrecta
        ''.join(remove_words_with_letters): entrega un string con las letras que no estan en la palabra
        result_true[0]: entrega las posiciones de las letras que estan en la palabra
        letters_position_wrong: entrega las letras que estan en la palabra pero en la posicion incorrecta
        """
        # corresponde la areglo de posiciones correctas de letras de la palabra 
        array_position = np.array(self.response_post['position_array'])
        # corresponde la areglo de posiciones correctas de letras de la palabra
        result_true = np.where(array_position == True)

        # corresponde la areglo de posiciones incorrectas de letras de la palabra
        result_false = np.where(array_position == False)

        # se transforma la palabra para que pueda ser iterada 
        word = ''.join(word)

        remove_words_with_letters = []
        letters_position_wrong = []
        # se busca la posicion de las letras que no estan en la palbra 
        # se busca la posicion de las letras que estan en la palabra pero en la posicion incorrecta
        for i in result_false[0]:
            if len(result_true[0]) == 0:
                if word[i] not in ''.join(self.response_post['right_letters_in_wrong_positions']):
                    remove_words_with_letters.append(word[i])

            elif len(result_true[0]) == 1:
                if word[i] not in ''.join(self.response_post['right_letters_in_wrong_positions']) and\
                   ( word[i] != word[result_true[0][0]]):
                    remove_words_with_letters.append(word[i])

            elif len(result_true[0]) == 2:
                if word[i] not in ''.join(self.response_post['right_letters_in_wrong_positions']) and\
                    (word[i] != word[result_true[0][0]])and\
                    (word[i] != word[result_true[0][1]]):
                    remove_words_with_letters.append(word[i])

            elif len(result_true[0]) == 3:
                if word[i] not in ''.join(self.response_post['right_letters_in_wrong_positions']) and\
                    (word[i] != word[result_true[0][0]]) and\
                    (word[i] != word[result_true[0][1]]) and\
                    (word[i] != word[result_true[0][2]]):
                    remove_words_with_letters.append(word[i])
            
            elif len(result_true[0]) == 4:
                if word[i] not in ''.join(self.response_post['right_letters_in_wrong_positions']) and\
                    (word[i] != word[result_true[0][0]]) and\
                    (word[i] != word[result_true[0][1]]) and\
                    (word[i] != word[result_true[0][2]]) and\
                    (word[i] != word[result_true[0][3]]):
                    remove_words_with_letters.append(word[i])

            elif len(result_true[0]) == 5:
                if word[i] not in ''.join(self.response_post['right_letters_in_wrong_positions']) and\
                    (word[i] != word[result_true[0][0]]) and\
                    (word[i] != word[result_true[0][1]]) and\
                    (word[i] != word[result_true[0][2]]) and\
                    (word[i] != word[result_true[0][3]]) and\
                    (word[i] != word[result_true[0][4]]):
                    remove_words_with_letters.append(word[i])

            elif len(result_true[0]) == 6:
                if word[i] not in ''.join(self.response_post['right_letters_in_wrong_positions']) and\
                    (word[i] != word[result_true[0][0]]) and\
                    (word[i] != word[result_true[0][1]]) and\
                    (word[i] != word[result_true[0][2]]) and\
                    (word[i] != word[result_true[0][3]]) and\
                    (word[i] != word[result_true[0][4]]) and\
                    (word[i] != word[result_true[0][5]]):
                    remove_words_with_letters.append(word[i])

            elif len(result_true[0]) == 7:
                if word[i] not in ''.join(self.response_post['right_letters_in_wrong_positions']) and\
                    (word[i] != word[result_true[0][0]]) and (word[i] != word[result_true[0][1]]) and\
                    (word[i] != word[result_true[0][2]]) and (word[i] != word[result_true[0][3]]) and\
                    (word[i] != word[result_true[0][4]]) and (word[i] != word[result_true[0][5]]) and\
                    (word[i] != word[result_true[0][6]]):
                    remove_words_with_letters.append(word[i])
            
            elif len(result_true[0]) == 8:
                if word[i] not in ''.join(self.response_post['right_letters_in_wrong_positions']) and\
                    (word[i] != word[result_true[0][0]]) and (word[i] != word[result_true[0][1]]) and\
                    (word[i] != word[result_true[0][2]]) and (word[i] != word[result_true[0][3]]) and\
                    (word[i] != word[result_true[0][4]]) and (word[i] != word[result_true[0][5]]) and\
                    (word[i] != word[result_true[0][6]]) and (word[i] != word[result_true[0][7]]):
                    remove_words_with_letters.append(word[i])

            elif len(result_true[0]) == 9:
                if word[i] not in ''.join(self.response_post['right_letters_in_wrong_positions']) and\
                    (word[i] != word[result_true[0][0]]) and (word[i] != word[result_true[0][1]]) and\
                    (word[i] != word[result_true[0][2]]) and (word[i] != word[result_true[0][3]]) and\
                    (word[i] != word[result_true[0][4]]) and (word[i] != word[result_true[0][5]]) and\
                    (word[i] != word[result_true[0][6]]) and (word[i] != word[result_true[0][7]]) and\
                    (word[i] != word[result_true[0][8]]):

                    remove_words_with_letters.append(word[i])   
            
            elif len(result_true[0]) == 10:
                if word[i] not in ''.join(self.response_post['right_letters_in_wrong_positions']) and\
                    (word[i] != word[result_true[0][0]]) and (word[i] != word[result_true[0][1]]) and\
                    (word[i] != word[result_true[0][2]]) and (word[i] != word[result_true[0][3]]) and\
                    (word[i] != word[result_true[0][4]]) and (word[i] != word[result_true[0][5]]) and\
                    (word[i] != word[result_true[0][6]]) and (word[i] != word[result_true[0][7]]) and\
                    (word[i] != word[result_true[0][8]]) and (word[i] != word[result_true[0][9]]):

                    remove_words_with_letters.append(word[i])
            
            elif len(result_true[0]) == 11:
                if word[i] not in ''.join(self.response_post['right_letters_in_wrong_positions']) and\
                    (word[i] != word[result_true[0][0]]) and (word[i] != word[result_true[0][1]]) and\
                    (word[i] != word[result_true[0][2]]) and (word[i] != word[result_true[0][3]]) and\
                    (word[i] != word[result_true[0][4]]) and (word[i] != word[result_true[0][5]]) and\
                    (word[i] != word[result_true[0][6]]) and (word[i] != word[result_true[0][7]]) and\
                    (word[i] != word[result_true[0][8]]) and (word[i] != word[result_true[0][9]]) and\
                    (word[i] != word[result_true[0][10]]):

                    remove_words_with_letters.append(word[i])
            
            elif len(result_true[0]) == 12:
                if word[i] not in ''.join(self.response_post['right_letters_in_wrong_positions']) and\
                    (word[i] != word[result_true[0][0]]) and (word[i] != word[result_true[0][1]]) and\
                    (word[i] != word[result_true[0][2]]) and (word[i] != word[result_true[0][3]]) and\
                    (word[i] != word[result_true[0][4]]) and (word[i] != word[result_true[0][5]]) and\
                    (word[i] != word[result_true[0][6]]) and (word[i] != word[result_true[0][7]]) and\
                    (word[i] != word[result_true[0][8]]) and (word[i] != word[result_true[0][9]]) and\
                    (word[i] != word[result_true[0][10]]) and (word[i] != word[result_true[0][11]]):

                    remove_words_with_letters.append(word[i])

            elif len(result_true[0]) == 13:
                if word[i] not in ''.join(self.response_post['right_letters_in_wrong_positions']) and\
                    (word[i] != word[result_true[0][0]]) and (word[i] != word[result_true[0][1]]) and\
                    (word[i] != word[result_true[0][2]]) and (word[i] != word[result_true[0][3]]) and\
                    (word[i] != word[result_true[0][4]]) and (word[i] != word[result_true[0][5]]) and\
                    (word[i] != word[result_true[0][6]]) and (word[i] != word[result_true[0][7]]) and\
                    (word[i] != word[result_true[0][8]]) and (word[i] != word[result_true[0][9]]) and\
                    (word[i] != word[result_true[0][10]]) and (word[i] != word[result_true[0][11]]) and\
                    (word[i] != word[result_true[0][12]]):

                    remove_words_with_letters.append(word[i])

            elif len(result_true[0]) == 14:
                if word[i] not in ''.join(self.response_post['right_letters_in_wrong_positions']) and\
                    (word[i] != word[result_true[0][0]]) and (word[i] != word[result_true[0][1]]) and\
                    (word[i] != word[result_true[0][2]]) and (word[i] != word[result_true[0][3]]) and\
                    (word[i] != word[result_true[0][4]]) and (word[i] != word[result_true[0][5]]) and\
                    (word[i] != word[result_true[0][6]]) and (word[i] != word[result_true[0][7]]) and\
                    (word[i] != word[result_true[0][8]]) and (word[i] != word[result_true[0][9]]) and\
                    (word[i] != word[result_true[0][10]]) and (word[i] != word[result_true[0][11]]) and\
                    (word[i] != word[result_true[0][12]]) and (word[i] != word[result_true[0][13]]):

                    remove_words_with_letters.append(word[i])

            elif len(result_true[0]) == 15:
                if word[i] not in ''.join(self.response_post['right_letters_in_wrong_positions']) and\
                    (word[i] != word[result_true[0][0]]) and (word[i] != word[result_true[0][1]]) and\
                    (word[i] != word[result_true[0][2]]) and (word[i] != word[result_true[0][3]]) and\
                    (word[i] != word[result_true[0][4]]) and (word[i] != word[result_true[0][5]]) and\
                    (word[i] != word[result_true[0][6]]) and (word[i] != word[result_true[0][7]]) and\
                    (word[i] != word[result_true[0][8]]) and (word[i] != word[result_true[0][9]]) and\
                    (word[i] != word[result_true[0][10]]) and (word[i] != word[result_true[0][11]]) and\
                    (word[i] != word[result_true[0][12]]) and (word[i] != word[result_true[0][13]]) and\
                    (word[i] != word[result_true[0][14]]):

                    remove_words_with_letters.append(word[i])

            elif len(result_true[0]) == 16:
                if word[i] not in ''.join(self.response_post['right_letters_in_wrong_positions']) and\
                    (word[i] != word[result_true[0][0]]) and (word[i] != word[result_true[0][1]]) and\
                    (word[i] != word[result_true[0][2]]) and (word[i] != word[result_true[0][3]]) and\
                    (word[i] != word[result_true[0][4]]) and (word[i] != word[result_true[0][5]]) and\
                    (word[i] != word[result_true[0][6]]) and (word[i] != word[result_true[0][7]]) and\
                    (word[i] != word[result_true[0][8]]) and (word[i] != word[result_true[0][9]]) and\
                    (word[i] != word[result_true[0][10]]) and (word[i] != word[result_true[0][11]]) and\
                    (word[i] != word[result_true[0][12]]) and (word[i] != word[result_true[0][13]]) and\
                    (word[i] != word[result_true[0][14]]) and (word[i] != word[result_true[0][15]]):

                    remove_words_with_letters.append(word[i])

            elif len(result_true[0]) == 17:
                if word[i] not in ''.join(self.response_post['right_letters_in_wrong_positions']) and\
                    (word[i] != word[result_true[0][0]]) and (word[i] != word[result_true[0][1]]) and\
                    (word[i] != word[result_true[0][2]]) and (word[i] != word[result_true[0][3]]) and\
                    (word[i] != word[result_true[0][4]]) and (word[i] != word[result_true[0][5]]) and\
                    (word[i] != word[result_true[0][6]]) and (word[i] != word[result_true[0][7]]) and\
                    (word[i] != word[result_true[0][8]]) and (word[i] != word[result_true[0][9]]) and\
                    (word[i] != word[result_true[0][10]]) and (word[i] != word[result_true[0][11]]) and\
                    (word[i] != word[result_true[0][12]]) and (word[i] != word[result_true[0][13]]) and\
                    (word[i] != word[result_true[0][14]]) and (word[i] != word[result_true[0][15]]) and\
                    (word[i] != word[result_true[0][16]]):

                    remove_words_with_letters.append(word[i])

            elif len(result_true[0]) == 18:
                if word[i] not in ''.join(self.response_post['right_letters_in_wrong_positions']) and\
                    (word[i] != word[result_true[0][0]]) and (word[i] != word[result_true[0][1]]) and\
                    (word[i] != word[result_true[0][2]]) and (word[i] != word[result_true[0][3]]) and\
                    (word[i] != word[result_true[0][4]]) and (word[i] != word[result_true[0][5]]) and\
                    (word[i] != word[result_true[0][6]]) and (word[i] != word[result_true[0][7]]) and\
                    (word[i] != word[result_true[0][8]]) and (word[i] != word[result_true[0][9]]) and\
                    (word[i] != word[result_true[0][10]]) and (word[i] != word[result_true[0][11]]) and\
                    (word[i] != word[result_true[0][12]]) and (word[i] != word[result_true[0][13]]) and\
                    (word[i] != word[result_true[0][14]]) and (word[i] != word[result_true[0][15]]) and\
                    (word[i] != word[result_true[0][16]]) and (word[i] != word[result_true[0][17]]):

                    remove_words_with_letters.append(word[i])

            elif len(result_true[0]) == 19:
                if word[i] not in ''.join(self.response_post['right_letters_in_wrong_positions']) and\
                    (word[i] != word[result_true[0][0]]) and (word[i] != word[result_true[0][1]]) and\
                    (word[i] != word[result_true[0][2]]) and (word[i] != word[result_true[0][3]]) and\
                    (word[i] != word[result_true[0][4]]) and (word[i] != word[result_true[0][5]]) and\
                    (word[i] != word[result_true[0][6]]) and (word[i] != word[result_true[0][7]]) and\
                    (word[i] != word[result_true[0][8]]) and (word[i] != word[result_true[0][9]]) and\
                    (word[i] != word[result_true[0][10]]) and (word[i] != word[result_true[0][11]]) and\
                    (word[i] != word[result_true[0][12]]) and (word[i] != word[result_true[0][13]]) and\
                    (word[i] != word[result_true[0][14]]) and (word[i] != word[result_true[0][15]]) and\
                    (word[i] != word[result_true[0][16]]) and (word[i] != word[result_true[0][17]]) and\
                    (word[i] != word[result_true[0][18]]):

                    remove_words_with_letters.append(word[i])

            elif len(result_true[0]) == 20:
                if word[i] not in ''.join(self.response_post['right_letters_in_wrong_positions']) and\
                    (word[i] != word[result_true[0][0]]) and (word[i] != word[result_true[0][1]]) and\
                    (word[i] != word[result_true[0][2]]) and (word[i] != word[result_true[0][3]]) and\
                    (word[i] != word[result_true[0][4]]) and (word[i] != word[result_true[0][5]]) and\
                    (word[i] != word[result_true[0][6]]) and (word[i] != word[result_true[0][7]]) and\
                    (word[i] != word[result_true[0][8]]) and (word[i] != word[result_true[0][9]]) and\
                    (word[i] != word[result_true[0][10]]) and (word[i] != word[result_true[0][11]]) and\
                    (word[i] != word[result_true[0][12]]) and (word[i] != word[result_true[0][13]]) and\
                    (word[i] != word[result_true[0][14]]) and (word[i] != word[result_true[0][15]]) and\
                    (word[i] != word[result_true[0][16]]) and (word[i] != word[result_true[0][17]]) and\
                    (word[i] != word[result_true[0][18]]) and (word[i] != word[result_true[0][19]]):

                    remove_words_with_letters.append(word[i])   

            elif len(result_true[0]) == 21:
                if word[i] not in ''.join(self.response_post['right_letters_in_wrong_positions']) and\
                    (word[i] != word[result_true[0][0]]) and (word[i] != word[result_true[0][1]]) and\
                    (word[i] != word[result_true[0][2]]) and (word[i] != word[result_true[0][3]]) and\
                    (word[i] != word[result_true[0][4]]) and (word[i] != word[result_true[0][5]]) and\
                    (word[i] != word[result_true[0][6]]) and (word[i] != word[result_true[0][7]]) and\
                    (word[i] != word[result_true[0][8]]) and (word[i] != word[result_true[0][9]]) and\
                    (word[i] != word[result_true[0][10]]) and (word[i] != word[result_true[0][11]]) and\
                    (word[i] != word[result_true[0][12]]) and (word[i] != word[result_true[0][13]]) and\
                    (word[i] != word[result_true[0][14]]) and (word[i] != word[result_true[0][15]]) and\
                    (word[i] != word[result_true[0][16]]) and (word[i] != word[result_true[0][17]]) and\
                    (word[i] != word[result_true[0][18]]) and (word[i] != word[result_true[0][19]]) and\
                    (word[i] != word[result_true[0][20]]):

                    remove_words_with_letters.append(word[i])
            
            elif len(result_true[0]) == 22:
                if word[i] not in ''.join(self.response_post['right_letters_in_wrong_positions']) and\
                    (word[i] != word[result_true[0][0]]) and (word[i] != word[result_true[0][1]]) and\
                    (word[i] != word[result_true[0][2]]) and (word[i] != word[result_true[0][3]]) and\
                    (word[i] != word[result_true[0][4]]) and (word[i] != word[result_true[0][5]]) and\
                    (word[i] != word[result_true[0][6]]) and (word[i] != word[result_true[0][7]]) and\
                    (word[i] != word[result_true[0][8]]) and (word[i] != word[result_true[0][9]]) and\
                    (word[i] != word[result_true[0][10]]) and (word[i] != word[result_true[0][11]]) and\
                    (word[i] != word[result_true[0][12]]) and (word[i] != word[result_true[0][13]]) and\
                    (word[i] != word[result_true[0][14]]) and (word[i] != word[result_true[0][15]]) and\
                    (word[i] != word[result_true[0][16]]) and (word[i] != word[result_true[0][17]]) and\
                    (word[i] != word[result_true[0][18]]) and (word[i] != word[result_true[0][19]]) and\
                    (word[i] != word[result_true[0][20]]) and (word[i] != word[result_true[0][21]]):

                    remove_words_with_letters.append(word[i])

            elif len(result_true[0]) == 23:
                if word[i] not in ''.join(self.response_post['right_letters_in_wrong_positions']) and\
                    (word[i] != word[result_true[0][0]]) and (word[i] != word[result_true[0][1]]) and\
                    (word[i] != word[result_true[0][2]]) and (word[i] != word[result_true[0][3]]) and\
                    (word[i] != word[result_true[0][4]]) and (word[i] != word[result_true[0][5]]) and\
                    (word[i] != word[result_true[0][6]]) and (word[i] != word[result_true[0][7]]) and\
                    (word[i] != word[result_true[0][8]]) and (word[i] != word[result_true[0][9]]) and\
                    (word[i] != word[result_true[0][10]]) and (word[i] != word[result_true[0][11]]) and\
                    (word[i] != word[result_true[0][12]]) and (word[i] != word[result_true[0][13]]) and\
                    (word[i] != word[result_true[0][14]]) and (word[i] != word[result_true[0][15]]) and\
                    (word[i] != word[result_true[0][16]]) and (word[i] != word[result_true[0][17]]) and\
                    (word[i] != word[result_true[0][18]]) and (word[i] != word[result_true[0][19]]) and\
                    (word[i] != word[result_true[0][20]]) and (word[i] != word[result_true[0][21]]) and\
                    (word[i] != word[result_true[0][22]]):

                    remove_words_with_letters.append(word[i])

            elif len(result_true[0]) == 24:
                if word[i] not in ''.join(self.response_post['right_letters_in_wrong_positions']) and\
                    (word[i] != word[result_true[0][0]]) and (word[i] != word[result_true[0][1]]) and\
                    (word[i] != word[result_true[0][2]]) and (word[i] != word[result_true[0][3]]) and\
                    (word[i] != word[result_true[0][4]]) and (word[i] != word[result_true[0][5]]) and\
                    (word[i] != word[result_true[0][6]]) and (word[i] != word[result_true[0][7]]) and\
                    (word[i] != word[result_true[0][8]]) and (word[i] != word[result_true[0][9]]) and\
                    (word[i] != word[result_true[0][10]]) and (word[i] != word[result_true[0][11]]) and\
                    (word[i] != word[result_true[0][12]]) and (word[i] != word[result_true[0][13]]) and\
                    (word[i] != word[result_true[0][14]]) and (word[i] != word[result_true[0][15]]) and\
                    (word[i] != word[result_true[0][16]]) and (word[i] != word[result_true[0][17]]) and\
                    (word[i] != word[result_true[0][18]]) and (word[i] != word[result_true[0][19]]) and\
                    (word[i] != word[result_true[0][20]]) and (word[i] != word[result_true[0][21]]) and\
                    (word[i] != word[result_true[0][22]]) and (word[i] != word[result_true[0][23]]):

                    remove_words_with_letters.append(word[i])
            
            elif len(result_true[0]) == 25:
                if word[i] not in ''.join(self.response_post['right_letters_in_wrong_positions']) and\
                    (word[i] != word[result_true[0][0]]) and (word[i] != word[result_true[0][1]]) and\
                    (word[i] != word[result_true[0][2]]) and (word[i] != word[result_true[0][3]]) and\
                    (word[i] != word[result_true[0][4]]) and (word[i] != word[result_true[0][5]]) and\
                    (word[i] != word[result_true[0][6]]) and (word[i] != word[result_true[0][7]]) and\
                    (word[i] != word[result_true[0][8]]) and (word[i] != word[result_true[0][9]]) and\
                    (word[i] != word[result_true[0][10]]) and (word[i] != word[result_true[0][11]]) and\
                    (word[i] != word[result_true[0][12]]) and (word[i] != word[result_true[0][13]]) and\
                    (word[i] != word[result_true[0][14]]) and (word[i] != word[result_true[0][15]]) and\
                    (word[i] != word[result_true[0][16]]) and (word[i] != word[result_true[0][17]]) and\
                    (word[i] != word[result_true[0][18]]) and (word[i] != word[result_true[0][19]]) and\
                    (word[i] != word[result_true[0][20]]) and (word[i] != word[result_true[0][21]]) and\
                    (word[i] != word[result_true[0][22]]) and (word[i] != word[result_true[0][23]]) and\
                    (word[i] != word[result_true[0][24]]):

                    remove_words_with_letters.append(word[i])
                

            if (word[i] in ''.join(self.response_post['right_letters_in_wrong_positions'])):
                letters_position_wrong.append(i)
    
        return ''.join(remove_words_with_letters), result_true[0], letters_position_wrong

    def filter_words_by_letters(self,database, letters):
        """
        Esta funcion se encarga de filtrar las palabras que tiene letras que no corresponden a
        la palabra que se esta buscando 
        database corresponde a las palabras 
        letters es un string que corresponde a las letras que se deben filtrar en las palabras 
        """
        filter_words = []
        regex = '['+letters+']+'
        if len(letters) > 0:
            for word in database:
                if re.findall(regex,word):
                    continue
                filter_words.append(word)
            return filter_words
        else:
            return database

    def filter_words_by_letter_positions(self,database,positions,word_sent):
        """
        Esta funcion se encarga de filtrar las palabras que tiene letras que no corresponden a
        la palabra que se esta buscando 
        database: corresponde a las palabras 
        positions: es vector que corresponde a las posiciones de las letras que no se deben filtrar en 
        las palabras o buscar conincidencias en las palabras con la letra que se busca
        """
        filter_words = []
        if(len(positions)!=0)and(len(positions)<len(word_sent)):
            for word in database:
                if len(positions) == 1:
                    if (word[positions[0]] == word_sent[positions[0]]) and\
                        (word != word_sent):
                        filter_words.append(word)

                elif len(positions) == 2:
                    if (word[positions[0]] == word_sent[positions[0]]) and\
                         (word[positions[1]] == word_sent[positions[1]]) and\
                         (word != word_sent):
                        filter_words.append(word)

                elif len(positions) == 3:
                    if (word[positions[0]] == word_sent[positions[0]]) and\
                         (word[positions[1]] == word_sent[positions[1]]) and\
                         (word[positions[2]] == word_sent[positions[2]]) and\
                         (word != word_sent):
                        filter_words.append(word)
                
                elif len(positions) == 4:
                    if (word[positions[0]] == word_sent[positions[0]]) and\
                         (word[positions[1]] == word_sent[positions[1]]) and\
                         (word[positions[2]] == word_sent[positions[2]]) and\
                         (word[positions[3]] == word_sent[positions[3]]) and\
                         (word != word_sent):
                        filter_words.append(word)
                
                elif len(positions) == 5:
                    if (word[positions[0]] == word_sent[positions[0]]) and\
                         (word[positions[1]] == word_sent[positions[1]]) and\
                         (word[positions[2]] == word_sent[positions[2]]) and\
                         (word[positions[3]] == word_sent[positions[3]]) and\
                         (word[positions[4]] == word_sent[positions[4]]) and\
                         (word != word_sent):
                        filter_words.append(word)
                
                elif len(positions) == 6:
                    if (word[positions[0]] == word_sent[positions[0]]) and\
                         (word[positions[1]] == word_sent[positions[1]]) and\
                         (word[positions[2]] == word_sent[positions[2]]) and\
                         (word[positions[3]] == word_sent[positions[3]]) and\
                         (word[positions[4]] == word_sent[positions[4]]) and\
                         (word[positions[5]] == word_sent[positions[5]]) and\
                         (word != word_sent):
                        filter_words.append(word)
                
                elif len(positions) == 7:
                    if (word[positions[0]] == word_sent[positions[0]]) and\
                         (word[positions[1]] == word_sent[positions[1]]) and\
                         (word[positions[2]] == word_sent[positions[2]]) and\
                         (word[positions[3]] == word_sent[positions[3]]) and\
                         (word[positions[4]] == word_sent[positions[4]]) and\
                         (word[positions[5]] == word_sent[positions[5]]) and\
                         (word[positions[6]] == word_sent[positions[6]]) and\
                         (word != word_sent):
                        filter_words.append(word)
                
                elif len(positions) == 8:
                    if (word[positions[0]] == word_sent[positions[0]]) and\
                         (word[positions[1]] == word_sent[positions[1]]) and\
                         (word[positions[2]] == word_sent[positions[2]]) and\
                         (word[positions[3]] == word_sent[positions[3]]) and\
                         (word[positions[4]] == word_sent[positions[4]]) and\
                         (word[positions[5]] == word_sent[positions[5]]) and\
                         (word[positions[6]] == word_sent[positions[6]]) and\
                         (word[positions[7]] == word_sent[positions[7]]) and\
                         (word != word_sent):
                        filter_words.append(word)
                
                elif len(positions) == 9:
                    if (word[positions[0]] == word_sent[positions[0]]) and\
                         (word[positions[1]] == word_sent[positions[1]]) and\
                         (word[positions[2]] == word_sent[positions[2]]) and\
                         (word[positions[3]] == word_sent[positions[3]]) and\
                         (word[positions[4]] == word_sent[positions[4]]) and\
                         (word[positions[5]] == word_sent[positions[5]]) and\
                         (word[positions[6]] == word_sent[positions[6]]) and\
                         (word[positions[7]] == word_sent[positions[7]]) and\
                         (word[positions[8]] == word_sent[positions[8]]) and\
                         (word != word_sent):
                        filter_words.append(word)
                
                elif len(positions) == 10:
                    if (word[positions[0]] == word_sent[positions[0]]) and\
                         (word[positions[1]] == word_sent[positions[1]]) and\
                         (word[positions[2]] == word_sent[positions[2]]) and\
                         (word[positions[3]] == word_sent[positions[3]]) and\
                         (word[positions[4]] == word_sent[positions[4]]) and\
                         (word[positions[5]] == word_sent[positions[5]]) and\
                         (word[positions[6]] == word_sent[positions[6]]) and\
                         (word[positions[7]] == word_sent[positions[7]]) and\
                         (word[positions[8]] == word_sent[positions[8]]) and\
                         (word[positions[9]] == word_sent[positions[9]]) and\
                         (word != word_sent):
                        filter_words.append(word)
                    
                elif len(positions) == 11:
                    if (word[positions[0]] == word_sent[positions[0]]) and\
                         (word[positions[1]] == word_sent[positions[1]]) and\
                         (word[positions[2]] == word_sent[positions[2]]) and\
                         (word[positions[3]] == word_sent[positions[3]]) and\
                         (word[positions[4]] == word_sent[positions[4]]) and\
                         (word[positions[5]] == word_sent[positions[5]]) and\
                         (word[positions[6]] == word_sent[positions[6]]) and\
                         (word[positions[7]] == word_sent[positions[7]]) and\
                         (word[positions[8]] == word_sent[positions[8]]) and\
                         (word[positions[9]] == word_sent[positions[9]]) and\
                         (word[positions[10]] == word_sent[positions[10]]) and\
                         (word != word_sent):
                        filter_words.append(word)

                elif len(positions) == 12:
                    if (word[positions[0]] == word_sent[positions[0]]) and\
                         (word[positions[1]] == word_sent[positions[1]]) and\
                         (word[positions[2]] == word_sent[positions[2]]) and\
                         (word[positions[3]] == word_sent[positions[3]]) and\
                         (word[positions[4]] == word_sent[positions[4]]) and\
                         (word[positions[5]] == word_sent[positions[5]]) and\
                         (word[positions[6]] == word_sent[positions[6]]) and\
                         (word[positions[7]] == word_sent[positions[7]]) and\
                         (word[positions[8]] == word_sent[positions[8]]) and\
                         (word[positions[9]] == word_sent[positions[9]]) and\
                         (word[positions[10]] == word_sent[positions[10]]) and\
                         (word[positions[11]] == word_sent[positions[11]]) and\
                         (word != word_sent):
                        filter_words.append(word)

                elif len(positions) == 13:
                    if (word[positions[0]] == word_sent[positions[0]]) and\
                         (word[positions[1]] == word_sent[positions[1]]) and\
                         (word[positions[2]] == word_sent[positions[2]]) and\
                         (word[positions[3]] == word_sent[positions[3]]) and\
                         (word[positions[4]] == word_sent[positions[4]]) and\
                         (word[positions[5]] == word_sent[positions[5]]) and\
                         (word[positions[6]] == word_sent[positions[6]]) and\
                         (word[positions[7]] == word_sent[positions[7]]) and\
                         (word[positions[8]] == word_sent[positions[8]]) and\
                         (word[positions[9]] == word_sent[positions[9]]) and\
                         (word[positions[10]] == word_sent[positions[10]]) and\
                         (word[positions[11]] == word_sent[positions[11]]) and\
                         (word[positions[12]] == word_sent[positions[12]]) and\
                         (word != word_sent):
                        filter_words.append(word)

                elif len(positions) == 14:
                    if (word[positions[0]] == word_sent[positions[0]]) and\
                         (word[positions[1]] == word_sent[positions[1]]) and\
                         (word[positions[2]] == word_sent[positions[2]]) and\
                         (word[positions[3]] == word_sent[positions[3]]) and\
                         (word[positions[4]] == word_sent[positions[4]]) and\
                         (word[positions[5]] == word_sent[positions[5]]) and\
                         (word[positions[6]] == word_sent[positions[6]]) and\
                         (word[positions[7]] == word_sent[positions[7]]) and\
                         (word[positions[8]] == word_sent[positions[8]]) and\
                         (word[positions[9]] == word_sent[positions[9]]) and\
                         (word[positions[10]] == word_sent[positions[10]]) and\
                         (word[positions[11]] == word_sent[positions[11]]) and\
                         (word[positions[12]] == word_sent[positions[12]]) and\
                         (word[positions[13]] == word_sent[positions[13]]) and\
                         (word != word_sent):
                        filter_words.append(word)
                
                elif len(positions) == 15:
                    if (word[positions[0]] == word_sent[positions[0]]) and\
                         (word[positions[1]] == word_sent[positions[1]]) and\
                         (word[positions[2]] == word_sent[positions[2]]) and\
                         (word[positions[3]] == word_sent[positions[3]]) and\
                         (word[positions[4]] == word_sent[positions[4]]) and\
                         (word[positions[5]] == word_sent[positions[5]]) and\
                         (word[positions[6]] == word_sent[positions[6]]) and\
                         (word[positions[7]] == word_sent[positions[7]]) and\
                         (word[positions[8]] == word_sent[positions[8]]) and\
                         (word[positions[9]] == word_sent[positions[9]]) and\
                         (word[positions[10]] == word_sent[positions[10]]) and\
                         (word[positions[11]] == word_sent[positions[11]]) and\
                         (word[positions[12]] == word_sent[positions[12]]) and\
                         (word[positions[13]] == word_sent[positions[13]]) and\
                         (word[positions[14]] == word_sent[positions[14]]) and\
                         (word != word_sent):
                        filter_words.append(word)
                
                elif len(positions) == 16:
                    if (word[positions[0]] == word_sent[positions[0]]) and\
                         (word[positions[1]] == word_sent[positions[1]]) and\
                         (word[positions[2]] == word_sent[positions[2]]) and\
                         (word[positions[3]] == word_sent[positions[3]]) and\
                         (word[positions[4]] == word_sent[positions[4]]) and\
                         (word[positions[5]] == word_sent[positions[5]]) and\
                         (word[positions[6]] == word_sent[positions[6]]) and\
                         (word[positions[7]] == word_sent[positions[7]]) and\
                         (word[positions[8]] == word_sent[positions[8]]) and\
                         (word[positions[9]] == word_sent[positions[9]]) and\
                         (word[positions[10]] == word_sent[positions[10]]) and\
                         (word[positions[11]] == word_sent[positions[11]]) and\
                         (word[positions[12]] == word_sent[positions[12]]) and\
                         (word[positions[13]] == word_sent[positions[13]]) and\
                         (word[positions[14]] == word_sent[positions[14]]) and\
                         (word[positions[15]] == word_sent[positions[15]]) and\
                         (word != word_sent):
                        filter_words.append(word)

                elif len(positions) == 17:
                    if (word[positions[0]] == word_sent[positions[0]]) and\
                         (word[positions[1]] == word_sent[positions[1]]) and\
                         (word[positions[2]] == word_sent[positions[2]]) and\
                         (word[positions[3]] == word_sent[positions[3]]) and\
                         (word[positions[4]] == word_sent[positions[4]]) and\
                         (word[positions[5]] == word_sent[positions[5]]) and\
                         (word[positions[6]] == word_sent[positions[6]]) and\
                         (word[positions[7]] == word_sent[positions[7]]) and\
                         (word[positions[8]] == word_sent[positions[8]]) and\
                         (word[positions[9]] == word_sent[positions[9]]) and\
                         (word[positions[10]] == word_sent[positions[10]]) and\
                         (word[positions[11]] == word_sent[positions[11]]) and\
                         (word[positions[12]] == word_sent[positions[12]]) and\
                         (word[positions[13]] == word_sent[positions[13]]) and\
                         (word[positions[14]] == word_sent[positions[14]]) and\
                         (word[positions[15]] == word_sent[positions[15]]) and\
                         (word[positions[16]] == word_sent[positions[16]]) and\
                         (word != word_sent):
                        filter_words.append(word)

                elif len(positions) == 18:
                    if (word[positions[0]] == word_sent[positions[0]]) and\
                         (word[positions[1]] == word_sent[positions[1]]) and\
                         (word[positions[2]] == word_sent[positions[2]]) and\
                         (word[positions[3]] == word_sent[positions[3]]) and\
                         (word[positions[4]] == word_sent[positions[4]]) and\
                         (word[positions[5]] == word_sent[positions[5]]) and\
                         (word[positions[6]] == word_sent[positions[6]]) and\
                         (word[positions[7]] == word_sent[positions[7]]) and\
                         (word[positions[8]] == word_sent[positions[8]]) and\
                         (word[positions[9]] == word_sent[positions[9]]) and\
                         (word[positions[10]] == word_sent[positions[10]]) and\
                         (word[positions[11]] == word_sent[positions[11]]) and\
                         (word[positions[12]] == word_sent[positions[12]]) and\
                         (word[positions[13]] == word_sent[positions[13]]) and\
                         (word[positions[14]] == word_sent[positions[14]]) and\
                         (word[positions[15]] == word_sent[positions[15]]) and\
                         (word[positions[16]] == word_sent[positions[16]]) and\
                         (word[positions[17]] == word_sent[positions[17]]) and\
                         (word != word_sent):
                        filter_words.append(word) 

                elif len(positions) == 19:
                    if (word[positions[0]] == word_sent[positions[0]]) and\
                         (word[positions[1]] == word_sent[positions[1]]) and\
                         (word[positions[2]] == word_sent[positions[2]]) and\
                         (word[positions[3]] == word_sent[positions[3]]) and\
                         (word[positions[4]] == word_sent[positions[4]]) and\
                         (word[positions[5]] == word_sent[positions[5]]) and\
                         (word[positions[6]] == word_sent[positions[6]]) and\
                         (word[positions[7]] == word_sent[positions[7]]) and\
                         (word[positions[8]] == word_sent[positions[8]]) and\
                         (word[positions[9]] == word_sent[positions[9]]) and\
                         (word[positions[10]] == word_sent[positions[10]]) and\
                         (word[positions[11]] == word_sent[positions[11]]) and\
                         (word[positions[12]] == word_sent[positions[12]]) and\
                         (word[positions[13]] == word_sent[positions[13]]) and\
                         (word[positions[14]] == word_sent[positions[14]]) and\
                         (word[positions[15]] == word_sent[positions[15]]) and\
                         (word[positions[16]] == word_sent[positions[16]]) and\
                         (word[positions[17]] == word_sent[positions[17]]) and\
                         (word[positions[18]] == word_sent[positions[18]]) and\
                         (word != word_sent):
                        filter_words.append(word)

                elif len(positions) == 20:
                    if (word[positions[0]] == word_sent[positions[0]]) and\
                         (word[positions[1]] == word_sent[positions[1]]) and\
                         (word[positions[2]] == word_sent[positions[2]]) and\
                         (word[positions[3]] == word_sent[positions[3]]) and\
                         (word[positions[4]] == word_sent[positions[4]]) and\
                         (word[positions[5]] == word_sent[positions[5]]) and\
                         (word[positions[6]] == word_sent[positions[6]]) and\
                         (word[positions[7]] == word_sent[positions[7]]) and\
                         (word[positions[8]] == word_sent[positions[8]]) and\
                         (word[positions[9]] == word_sent[positions[9]]) and\
                         (word[positions[10]] == word_sent[positions[10]]) and\
                         (word[positions[11]] == word_sent[positions[11]]) and\
                         (word[positions[12]] == word_sent[positions[12]]) and\
                         (word[positions[13]] == word_sent[positions[13]]) and\
                         (word[positions[14]] == word_sent[positions[14]]) and\
                         (word[positions[15]] == word_sent[positions[15]]) and\
                         (word[positions[16]] == word_sent[positions[16]]) and\
                         (word[positions[17]] == word_sent[positions[17]]) and\
                         (word[positions[18]] == word_sent[positions[18]]) and\
                         (word[positions[19]] == word_sent[positions[19]]) and\
                         (word != word_sent):
                        filter_words.append(word)
                
                elif len(positions) == 21:
                    if (word[positions[0]] == word_sent[positions[0]]) and\
                         (word[positions[1]] == word_sent[positions[1]]) and\
                         (word[positions[2]] == word_sent[positions[2]]) and\
                         (word[positions[3]] == word_sent[positions[3]]) and\
                         (word[positions[4]] == word_sent[positions[4]]) and\
                         (word[positions[5]] == word_sent[positions[5]]) and\
                         (word[positions[6]] == word_sent[positions[6]]) and\
                         (word[positions[7]] == word_sent[positions[7]]) and\
                         (word[positions[8]] == word_sent[positions[8]]) and\
                         (word[positions[9]] == word_sent[positions[9]]) and\
                         (word[positions[10]] == word_sent[positions[10]]) and\
                         (word[positions[11]] == word_sent[positions[11]]) and\
                         (word[positions[12]] == word_sent[positions[12]]) and\
                         (word[positions[13]] == word_sent[positions[13]]) and\
                         (word[positions[14]] == word_sent[positions[14]]) and\
                         (word[positions[15]] == word_sent[positions[15]]) and\
                         (word[positions[16]] == word_sent[positions[16]]) and\
                         (word[positions[17]] == word_sent[positions[17]]) and\
                         (word[positions[18]] == word_sent[positions[18]]) and\
                         (word[positions[19]] == word_sent[positions[19]]) and\
                         (word[positions[20]] == word_sent[positions[20]]) and\
                         (word != word_sent):
                        filter_words.append(word)
                
                elif len(positions) == 22:
                    if (word[positions[0]] == word_sent[positions[0]]) and\
                         (word[positions[1]] == word_sent[positions[1]]) and\
                         (word[positions[2]] == word_sent[positions[2]]) and\
                         (word[positions[3]] == word_sent[positions[3]]) and\
                         (word[positions[4]] == word_sent[positions[4]]) and\
                         (word[positions[5]] == word_sent[positions[5]]) and\
                         (word[positions[6]] == word_sent[positions[6]]) and\
                         (word[positions[7]] == word_sent[positions[7]]) and\
                         (word[positions[8]] == word_sent[positions[8]]) and\
                         (word[positions[9]] == word_sent[positions[9]]) and\
                         (word[positions[10]] == word_sent[positions[10]]) and\
                         (word[positions[11]] == word_sent[positions[11]]) and\
                         (word[positions[12]] == word_sent[positions[12]]) and\
                         (word[positions[13]] == word_sent[positions[13]]) and\
                         (word[positions[14]] == word_sent[positions[14]]) and\
                         (word[positions[15]] == word_sent[positions[15]]) and\
                         (word[positions[16]] == word_sent[positions[16]]) and\
                         (word[positions[17]] == word_sent[positions[17]]) and\
                         (word[positions[18]] == word_sent[positions[18]]) and\
                         (word[positions[19]] == word_sent[positions[19]]) and\
                         (word[positions[20]] == word_sent[positions[20]]) and\
                         (word[positions[21]] == word_sent[positions[21]]) and\
                         (word != word_sent):
                        filter_words.append(word)
                
                elif len(positions) == 23:
                    if (word[positions[0]] == word_sent[positions[0]]) and\
                         (word[positions[1]] == word_sent[positions[1]]) and\
                         (word[positions[2]] == word_sent[positions[2]]) and\
                         (word[positions[3]] == word_sent[positions[3]]) and\
                         (word[positions[4]] == word_sent[positions[4]]) and\
                         (word[positions[5]] == word_sent[positions[5]]) and\
                         (word[positions[6]] == word_sent[positions[6]]) and\
                         (word[positions[7]] == word_sent[positions[7]]) and\
                         (word[positions[8]] == word_sent[positions[8]]) and\
                         (word[positions[9]] == word_sent[positions[9]]) and\
                         (word[positions[10]] == word_sent[positions[10]]) and\
                         (word[positions[11]] == word_sent[positions[11]]) and\
                         (word[positions[12]] == word_sent[positions[12]]) and\
                         (word[positions[13]] == word_sent[positions[13]]) and\
                         (word[positions[14]] == word_sent[positions[14]]) and\
                         (word[positions[15]] == word_sent[positions[15]]) and\
                         (word[positions[16]] == word_sent[positions[16]]) and\
                         (word[positions[17]] == word_sent[positions[17]]) and\
                         (word[positions[18]] == word_sent[positions[18]]) and\
                         (word[positions[19]] == word_sent[positions[19]]) and\
                         (word[positions[20]] == word_sent[positions[20]]) and\
                         (word[positions[21]] == word_sent[positions[21]]) and\
                         (word[positions[22]] == word_sent[positions[22]]) and\
                         (word != word_sent):
                        filter_words.append(word)
                
                elif len(positions) == 24:
                    if (word[positions[0]] == word_sent[positions[0]]) and\
                         (word[positions[1]] == word_sent[positions[1]]) and\
                         (word[positions[2]] == word_sent[positions[2]]) and\
                         (word[positions[3]] == word_sent[positions[3]]) and\
                         (word[positions[4]] == word_sent[positions[4]]) and\
                         (word[positions[5]] == word_sent[positions[5]]) and\
                         (word[positions[6]] == word_sent[positions[6]]) and\
                         (word[positions[7]] == word_sent[positions[7]]) and\
                         (word[positions[8]] == word_sent[positions[8]]) and\
                         (word[positions[9]] == word_sent[positions[9]]) and\
                         (word[positions[10]] == word_sent[positions[10]]) and\
                         (word[positions[11]] == word_sent[positions[11]]) and\
                         (word[positions[12]] == word_sent[positions[12]]) and\
                         (word[positions[13]] == word_sent[positions[13]]) and\
                         (word[positions[14]] == word_sent[positions[14]]) and\
                         (word[positions[15]] == word_sent[positions[15]]) and\
                         (word[positions[16]] == word_sent[positions[16]]) and\
                         (word[positions[17]] == word_sent[positions[17]]) and\
                         (word[positions[18]] == word_sent[positions[18]]) and\
                         (word[positions[19]] == word_sent[positions[19]]) and\
                         (word[positions[20]] == word_sent[positions[20]]) and\
                         (word[positions[21]] == word_sent[positions[21]]) and\
                         (word[positions[22]] == word_sent[positions[22]]) and\
                         (word[positions[23]] == word_sent[positions[23]]) and\
                         (word != word_sent):
                        filter_words.append(word)
                
                elif len(positions) == 25:
                    if (word[positions[0]] == word_sent[positions[0]]) and\
                         (word[positions[1]] == word_sent[positions[1]]) and\
                         (word[positions[2]] == word_sent[positions[2]]) and\
                         (word[positions[3]] == word_sent[positions[3]]) and\
                         (word[positions[4]] == word_sent[positions[4]]) and\
                         (word[positions[5]] == word_sent[positions[5]]) and\
                         (word[positions[6]] == word_sent[positions[6]]) and\
                         (word[positions[7]] == word_sent[positions[7]]) and\
                         (word[positions[8]] == word_sent[positions[8]]) and\
                         (word[positions[9]] == word_sent[positions[9]]) and\
                         (word[positions[10]] == word_sent[positions[10]]) and\
                         (word[positions[11]] == word_sent[positions[11]]) and\
                         (word[positions[12]] == word_sent[positions[12]]) and\
                         (word[positions[13]] == word_sent[positions[13]]) and\
                         (word[positions[14]] == word_sent[positions[14]]) and\
                         (word[positions[15]] == word_sent[positions[15]]) and\
                         (word[positions[16]] == word_sent[positions[16]]) and\
                         (word[positions[17]] == word_sent[positions[17]]) and\
                         (word[positions[18]] == word_sent[positions[18]]) and\
                         (word[positions[19]] == word_sent[positions[19]]) and\
                         (word[positions[20]] == word_sent[positions[20]]) and\
                         (word[positions[21]] == word_sent[positions[21]]) and\
                         (word[positions[22]] == word_sent[positions[22]]) and\
                         (word[positions[23]] == word_sent[positions[23]]) and\
                         (word[positions[24]] == word_sent[positions[24]]) and\
                         (word != word_sent):
                        filter_words.append(word)

            return filter_words
        else:
            return database
    
    def filter_words_by_letter_positions_wrong(self, database, letters_position_wrong, word_sent):
        """
        Esta funcion elimina de la base de datos todas las palabras que tiene letras en las posiciones
        incorrectas 
        database: corresponde a las palabras que se van a filtrar
        letters_position_wrong: corresponde a la posicion de las letras que estan en la palabra pero no en
        la posicion correcta 
        word_send: corresponde a la palabra que se envio a la API 
        """
        filter_words = []
        if len(letters_position_wrong) > 0:
            for word in database:
                if len(letters_position_wrong) == 1:
                    if (word[letters_position_wrong[0]] != word_sent[letters_position_wrong[0]]) and\
                         (word != word_sent):
                        filter_words.append(word)

                elif len(letters_position_wrong) == 2:
                    if (word[letters_position_wrong[0]] != word_sent[letters_position_wrong[0]]) and\
                         (word[letters_position_wrong[1]] != word_sent[letters_position_wrong[1]]) and\
                         (word != word_sent):
                        filter_words.append(word)

                elif len(letters_position_wrong) == 3:
                    if (word[letters_position_wrong[0]] != word_sent[letters_position_wrong[0]]) and\
                         (word[letters_position_wrong[1]] != word_sent[letters_position_wrong[1]]) and\
                         (word[letters_position_wrong[2]] != word_sent[letters_position_wrong[2]]) and\
                         (word != word_sent):
                        filter_words.append(word)

                elif len(letters_position_wrong) == 4:
                    if (word[letters_position_wrong[0]] != word_sent[letters_position_wrong[0]]) and\
                         (word[letters_position_wrong[1]] != word_sent[letters_position_wrong[1]]) and\
                         (word[letters_position_wrong[2]] != word_sent[letters_position_wrong[2]]) and\
                         (word[letters_position_wrong[3]] != word_sent[letters_position_wrong[3]]) and\
                         (word != word_sent):
                        filter_words.append(word)

                elif len(letters_position_wrong) == 5:
                    if (word[letters_position_wrong[0]] != word_sent[letters_position_wrong[0]]) and\
                         (word[letters_position_wrong[1]] != word_sent[letters_position_wrong[1]]) and\
                         (word[letters_position_wrong[2]] != word_sent[letters_position_wrong[2]]) and\
                         (word[letters_position_wrong[3]] != word_sent[letters_position_wrong[3]]) and\
                         (word[letters_position_wrong[4]] != word_sent[letters_position_wrong[4]]) and\
                         (word != word_sent):
                        filter_words.append(word)

                elif len(letters_position_wrong) == 6:
                    if (word[letters_position_wrong[0]] != word_sent[letters_position_wrong[0]]) and\
                         (word[letters_position_wrong[1]] != word_sent[letters_position_wrong[1]]) and\
                         (word[letters_position_wrong[2]] != word_sent[letters_position_wrong[2]]) and\
                         (word[letters_position_wrong[3]] != word_sent[letters_position_wrong[3]]) and\
                         (word[letters_position_wrong[4]] != word_sent[letters_position_wrong[4]]) and\
                         (word[letters_position_wrong[5]] != word_sent[letters_position_wrong[5]]) and\
                         (word != word_sent):
                        filter_words.append(word)

                elif len(letters_position_wrong) == 7:
                    if (word[letters_position_wrong[0]] != word_sent[letters_position_wrong[0]]) and\
                         (word[letters_position_wrong[1]] != word_sent[letters_position_wrong[1]]) and\
                         (word[letters_position_wrong[2]] != word_sent[letters_position_wrong[2]]) and\
                         (word[letters_position_wrong[3]] != word_sent[letters_position_wrong[3]]) and\
                         (word[letters_position_wrong[4]] != word_sent[letters_position_wrong[4]]) and\
                         (word[letters_position_wrong[5]] != word_sent[letters_position_wrong[5]]) and\
                         (word[letters_position_wrong[6]] != word_sent[letters_position_wrong[6]]) and\
                         (word != word_sent):
                        filter_words.append(word)

                elif len(letters_position_wrong) == 8:
                    if (word[letters_position_wrong[0]] != word_sent[letters_position_wrong[0]]) and\
                         (word[letters_position_wrong[1]] != word_sent[letters_position_wrong[1]]) and\
                         (word[letters_position_wrong[2]] != word_sent[letters_position_wrong[2]]) and\
                         (word[letters_position_wrong[3]] != word_sent[letters_position_wrong[3]]) and\
                         (word[letters_position_wrong[4]] != word_sent[letters_position_wrong[4]]) and\
                         (word[letters_position_wrong[5]] != word_sent[letters_position_wrong[5]]) and\
                         (word[letters_position_wrong[6]] != word_sent[letters_position_wrong[6]]) and\
                         (word[letters_position_wrong[7]] != word_sent[letters_position_wrong[7]]) and\
                         (word != word_sent):
                        filter_words.append(word)

                elif len(letters_position_wrong) == 9:
                    if (word[letters_position_wrong[0]] != word_sent[letters_position_wrong[0]]) and\
                         (word[letters_position_wrong[1]] != word_sent[letters_position_wrong[1]]) and\
                         (word[letters_position_wrong[2]] != word_sent[letters_position_wrong[2]]) and\
                         (word[letters_position_wrong[3]] != word_sent[letters_position_wrong[3]]) and\
                         (word[letters_position_wrong[4]] != word_sent[letters_position_wrong[4]]) and\
                         (word[letters_position_wrong[5]] != word_sent[letters_position_wrong[5]]) and\
                         (word[letters_position_wrong[6]] != word_sent[letters_position_wrong[6]]) and\
                         (word[letters_position_wrong[7]] != word_sent[letters_position_wrong[7]]) and\
                         (word[letters_position_wrong[8]] != word_sent[letters_position_wrong[8]]) and\
                         (word != word_sent):
                        filter_words.append(word)

                elif len(letters_position_wrong) == 10:
                    if (word[letters_position_wrong[0]] != word_sent[letters_position_wrong[0]]) and\
                         (word[letters_position_wrong[1]] != word_sent[letters_position_wrong[1]]) and\
                         (word[letters_position_wrong[2]] != word_sent[letters_position_wrong[2]]) and\
                         (word[letters_position_wrong[3]] != word_sent[letters_position_wrong[3]]) and\
                         (word[letters_position_wrong[4]] != word_sent[letters_position_wrong[4]]) and\
                         (word[letters_position_wrong[5]] != word_sent[letters_position_wrong[5]]) and\
                         (word[letters_position_wrong[6]] != word_sent[letters_position_wrong[6]]) and\
                         (word[letters_position_wrong[7]] != word_sent[letters_position_wrong[7]]) and\
                         (word[letters_position_wrong[8]] != word_sent[letters_position_wrong[8]]) and\
                         (word[letters_position_wrong[9]] != word_sent[letters_position_wrong[9]]) and\
                         (word != word_sent):
                        filter_words.append(word)

                elif len(letters_position_wrong) == 11:
                    if (word[letters_position_wrong[0]] != word_sent[letters_position_wrong[0]]) and\
                         (word[letters_position_wrong[1]] != word_sent[letters_position_wrong[1]]) and\
                         (word[letters_position_wrong[2]] != word_sent[letters_position_wrong[2]]) and\
                         (word[letters_position_wrong[3]] != word_sent[letters_position_wrong[3]]) and\
                         (word[letters_position_wrong[4]] != word_sent[letters_position_wrong[4]]) and\
                         (word[letters_position_wrong[5]] != word_sent[letters_position_wrong[5]]) and\
                         (word[letters_position_wrong[6]] != word_sent[letters_position_wrong[6]]) and\
                         (word[letters_position_wrong[7]] != word_sent[letters_position_wrong[7]]) and\
                         (word[letters_position_wrong[8]] != word_sent[letters_position_wrong[8]]) and\
                         (word[letters_position_wrong[9]] != word_sent[letters_position_wrong[9]]) and\
                         (word[letters_position_wrong[10]] != word_sent[letters_position_wrong[10]]) and\
                         (word != word_sent):
                        filter_words.append(word)
                
                elif len(letters_position_wrong) == 12:
                    if (word[letters_position_wrong[0]] != word_sent[letters_position_wrong[0]]) and\
                         (word[letters_position_wrong[1]] != word_sent[letters_position_wrong[1]]) and\
                         (word[letters_position_wrong[2]] != word_sent[letters_position_wrong[2]]) and\
                         (word[letters_position_wrong[3]] != word_sent[letters_position_wrong[3]]) and\
                         (word[letters_position_wrong[4]] != word_sent[letters_position_wrong[4]]) and\
                         (word[letters_position_wrong[5]] != word_sent[letters_position_wrong[5]]) and\
                         (word[letters_position_wrong[6]] != word_sent[letters_position_wrong[6]]) and\
                         (word[letters_position_wrong[7]] != word_sent[letters_position_wrong[7]]) and\
                         (word[letters_position_wrong[8]] != word_sent[letters_position_wrong[8]]) and\
                         (word[letters_position_wrong[9]] != word_sent[letters_position_wrong[9]]) and\
                         (word[letters_position_wrong[10]] != word_sent[letters_position_wrong[10]]) and\
                         (word[letters_position_wrong[11]] != word_sent[letters_position_wrong[11]]) and\
                         (word != word_sent):
                        filter_words.append(word)

                elif len(letters_position_wrong) == 13:
                    if (word[letters_position_wrong[0]] != word_sent[letters_position_wrong[0]]) and\
                         (word[letters_position_wrong[1]] != word_sent[letters_position_wrong[1]]) and\
                         (word[letters_position_wrong[2]] != word_sent[letters_position_wrong[2]]) and\
                         (word[letters_position_wrong[3]] != word_sent[letters_position_wrong[3]]) and\
                         (word[letters_position_wrong[4]] != word_sent[letters_position_wrong[4]]) and\
                         (word[letters_position_wrong[5]] != word_sent[letters_position_wrong[5]]) and\
                         (word[letters_position_wrong[6]] != word_sent[letters_position_wrong[6]]) and\
                         (word[letters_position_wrong[7]] != word_sent[letters_position_wrong[7]]) and\
                         (word[letters_position_wrong[8]] != word_sent[letters_position_wrong[8]]) and\
                         (word[letters_position_wrong[9]] != word_sent[letters_position_wrong[9]]) and\
                         (word[letters_position_wrong[10]] != word_sent[letters_position_wrong[10]]) and\
                         (word[letters_position_wrong[11]] != word_sent[letters_position_wrong[11]]) and\
                         (word[letters_position_wrong[12]] != word_sent[letters_position_wrong[12]]) and\
                         (word != word_sent):
                        filter_words.append(word)

                elif len(letters_position_wrong) == 14:
                    if (word[letters_position_wrong[0]] != word_sent[letters_position_wrong[0]]) and\
                         (word[letters_position_wrong[1]] != word_sent[letters_position_wrong[1]]) and\
                         (word[letters_position_wrong[2]] != word_sent[letters_position_wrong[2]]) and\
                         (word[letters_position_wrong[3]] != word_sent[letters_position_wrong[3]]) and\
                         (word[letters_position_wrong[4]] != word_sent[letters_position_wrong[4]]) and\
                         (word[letters_position_wrong[5]] != word_sent[letters_position_wrong[5]]) and\
                         (word[letters_position_wrong[6]] != word_sent[letters_position_wrong[6]]) and\
                         (word[letters_position_wrong[7]] != word_sent[letters_position_wrong[7]]) and\
                         (word[letters_position_wrong[8]] != word_sent[letters_position_wrong[8]]) and\
                         (word[letters_position_wrong[9]] != word_sent[letters_position_wrong[9]]) and\
                         (word[letters_position_wrong[10]] != word_sent[letters_position_wrong[10]]) and\
                         (word[letters_position_wrong[11]] != word_sent[letters_position_wrong[11]]) and\
                         (word[letters_position_wrong[12]] != word_sent[letters_position_wrong[12]]) and\
                         (word[letters_position_wrong[13]] != word_sent[letters_position_wrong[13]]) and\
                         (word != word_sent):
                        filter_words.append(word)

                elif len(letters_position_wrong) == 15:
                    if (word[letters_position_wrong[0]] != word_sent[letters_position_wrong[0]]) and\
                         (word[letters_position_wrong[1]] != word_sent[letters_position_wrong[1]]) and\
                         (word[letters_position_wrong[2]] != word_sent[letters_position_wrong[2]]) and\
                         (word[letters_position_wrong[3]] != word_sent[letters_position_wrong[3]]) and\
                         (word[letters_position_wrong[4]] != word_sent[letters_position_wrong[4]]) and\
                         (word[letters_position_wrong[5]] != word_sent[letters_position_wrong[5]]) and\
                         (word[letters_position_wrong[6]] != word_sent[letters_position_wrong[6]]) and\
                         (word[letters_position_wrong[7]] != word_sent[letters_position_wrong[7]]) and\
                         (word[letters_position_wrong[8]] != word_sent[letters_position_wrong[8]]) and\
                         (word[letters_position_wrong[9]] != word_sent[letters_position_wrong[9]]) and\
                         (word[letters_position_wrong[10]] != word_sent[letters_position_wrong[10]]) and\
                         (word[letters_position_wrong[11]] != word_sent[letters_position_wrong[11]]) and\
                         (word[letters_position_wrong[12]] != word_sent[letters_position_wrong[12]]) and\
                         (word[letters_position_wrong[13]] != word_sent[letters_position_wrong[13]]) and\
                         (word[letters_position_wrong[14]] != word_sent[letters_position_wrong[14]]) and\
                         (word != word_sent):
                        filter_words.append(word)

                elif len(letters_position_wrong) == 16:
                    if (word[letters_position_wrong[0]] != word_sent[letters_position_wrong[0]]) and\
                         (word[letters_position_wrong[1]] != word_sent[letters_position_wrong[1]]) and\
                         (word[letters_position_wrong[2]] != word_sent[letters_position_wrong[2]]) and\
                         (word[letters_position_wrong[3]] != word_sent[letters_position_wrong[3]]) and\
                         (word[letters_position_wrong[4]] != word_sent[letters_position_wrong[4]]) and\
                         (word[letters_position_wrong[5]] != word_sent[letters_position_wrong[5]]) and\
                         (word[letters_position_wrong[6]] != word_sent[letters_position_wrong[6]]) and\
                         (word[letters_position_wrong[7]] != word_sent[letters_position_wrong[7]]) and\
                         (word[letters_position_wrong[8]] != word_sent[letters_position_wrong[8]]) and\
                         (word[letters_position_wrong[9]] != word_sent[letters_position_wrong[9]]) and\
                         (word[letters_position_wrong[10]] != word_sent[letters_position_wrong[10]]) and\
                         (word[letters_position_wrong[11]] != word_sent[letters_position_wrong[11]]) and\
                         (word[letters_position_wrong[12]] != word_sent[letters_position_wrong[12]]) and\
                         (word[letters_position_wrong[13]] != word_sent[letters_position_wrong[13]]) and\
                         (word[letters_position_wrong[14]] != word_sent[letters_position_wrong[14]]) and\
                         (word[letters_position_wrong[15]] != word_sent[letters_position_wrong[15]]) and\
                         (word != word_sent):
                        filter_words.append(word)

                elif len(letters_position_wrong) == 17:
                    if (word[letters_position_wrong[0]] != word_sent[letters_position_wrong[0]]) and\
                         (word[letters_position_wrong[1]] != word_sent[letters_position_wrong[1]]) and\
                         (word[letters_position_wrong[2]] != word_sent[letters_position_wrong[2]]) and\
                         (word[letters_position_wrong[3]] != word_sent[letters_position_wrong[3]]) and\
                         (word[letters_position_wrong[4]] != word_sent[letters_position_wrong[4]]) and\
                         (word[letters_position_wrong[5]] != word_sent[letters_position_wrong[5]]) and\
                         (word[letters_position_wrong[6]] != word_sent[letters_position_wrong[6]]) and\
                         (word[letters_position_wrong[7]] != word_sent[letters_position_wrong[7]]) and\
                         (word[letters_position_wrong[8]] != word_sent[letters_position_wrong[8]]) and\
                         (word[letters_position_wrong[9]] != word_sent[letters_position_wrong[9]]) and\
                         (word[letters_position_wrong[10]] != word_sent[letters_position_wrong[10]]) and\
                         (word[letters_position_wrong[11]] != word_sent[letters_position_wrong[11]]) and\
                         (word[letters_position_wrong[12]] != word_sent[letters_position_wrong[12]]) and\
                         (word[letters_position_wrong[13]] != word_sent[letters_position_wrong[13]]) and\
                         (word[letters_position_wrong[14]] != word_sent[letters_position_wrong[14]]) and\
                         (word[letters_position_wrong[15]] != word_sent[letters_position_wrong[15]]) and\
                         (word[letters_position_wrong[16]] != word_sent[letters_position_wrong[16]]) and\
                         (word != word_sent):
                        filter_words.append(word)
                
                elif len(letters_position_wrong) == 18:
                    if (word[letters_position_wrong[0]] != word_sent[letters_position_wrong[0]]) and\
                         (word[letters_position_wrong[1]] != word_sent[letters_position_wrong[1]]) and\
                         (word[letters_position_wrong[2]] != word_sent[letters_position_wrong[2]]) and\
                         (word[letters_position_wrong[3]] != word_sent[letters_position_wrong[3]]) and\
                         (word[letters_position_wrong[4]] != word_sent[letters_position_wrong[4]]) and\
                         (word[letters_position_wrong[5]] != word_sent[letters_position_wrong[5]]) and\
                         (word[letters_position_wrong[6]] != word_sent[letters_position_wrong[6]]) and\
                         (word[letters_position_wrong[7]] != word_sent[letters_position_wrong[7]]) and\
                         (word[letters_position_wrong[8]] != word_sent[letters_position_wrong[8]]) and\
                         (word[letters_position_wrong[9]] != word_sent[letters_position_wrong[9]]) and\
                         (word[letters_position_wrong[10]] != word_sent[letters_position_wrong[10]]) and\
                         (word[letters_position_wrong[11]] != word_sent[letters_position_wrong[11]]) and\
                         (word[letters_position_wrong[12]] != word_sent[letters_position_wrong[12]]) and\
                         (word[letters_position_wrong[13]] != word_sent[letters_position_wrong[13]]) and\
                         (word[letters_position_wrong[14]] != word_sent[letters_position_wrong[14]]) and\
                         (word[letters_position_wrong[15]] != word_sent[letters_position_wrong[15]]) and\
                         (word[letters_position_wrong[16]] != word_sent[letters_position_wrong[16]]) and\
                         (word[letters_position_wrong[17]] != word_sent[letters_position_wrong[17]]) and\
                         (word != word_sent):
                        filter_words.append(word)
                
                elif len(letters_position_wrong) == 19:
                    if (word[letters_position_wrong[0]] != word_sent[letters_position_wrong[0]]) and\
                         (word[letters_position_wrong[1]] != word_sent[letters_position_wrong[1]]) and\
                         (word[letters_position_wrong[2]] != word_sent[letters_position_wrong[2]]) and\
                         (word[letters_position_wrong[3]] != word_sent[letters_position_wrong[3]]) and\
                         (word[letters_position_wrong[4]] != word_sent[letters_position_wrong[4]]) and\
                         (word[letters_position_wrong[5]] != word_sent[letters_position_wrong[5]]) and\
                         (word[letters_position_wrong[6]] != word_sent[letters_position_wrong[6]]) and\
                         (word[letters_position_wrong[7]] != word_sent[letters_position_wrong[7]]) and\
                         (word[letters_position_wrong[8]] != word_sent[letters_position_wrong[8]]) and\
                         (word[letters_position_wrong[9]] != word_sent[letters_position_wrong[9]]) and\
                         (word[letters_position_wrong[10]] != word_sent[letters_position_wrong[10]]) and\
                         (word[letters_position_wrong[11]] != word_sent[letters_position_wrong[11]]) and\
                         (word[letters_position_wrong[12]] != word_sent[letters_position_wrong[12]]) and\
                         (word[letters_position_wrong[13]] != word_sent[letters_position_wrong[13]]) and\
                         (word[letters_position_wrong[14]] != word_sent[letters_position_wrong[14]]) and\
                         (word[letters_position_wrong[15]] != word_sent[letters_position_wrong[15]]) and\
                         (word[letters_position_wrong[16]] != word_sent[letters_position_wrong[16]]) and\
                         (word[letters_position_wrong[17]] != word_sent[letters_position_wrong[17]]) and\
                         (word[letters_position_wrong[18]] != word_sent[letters_position_wrong[18]]) and\
                         (word != word_sent):
                        filter_words.append(word)
                
                elif len(letters_position_wrong) == 20:
                    if (word[letters_position_wrong[0]] != word_sent[letters_position_wrong[0]]) and\
                         (word[letters_position_wrong[1]] != word_sent[letters_position_wrong[1]]) and\
                         (word[letters_position_wrong[2]] != word_sent[letters_position_wrong[2]]) and\
                         (word[letters_position_wrong[3]] != word_sent[letters_position_wrong[3]]) and\
                         (word[letters_position_wrong[4]] != word_sent[letters_position_wrong[4]]) and\
                         (word[letters_position_wrong[5]] != word_sent[letters_position_wrong[5]]) and\
                         (word[letters_position_wrong[6]] != word_sent[letters_position_wrong[6]]) and\
                         (word[letters_position_wrong[7]] != word_sent[letters_position_wrong[7]]) and\
                         (word[letters_position_wrong[8]] != word_sent[letters_position_wrong[8]]) and\
                         (word[letters_position_wrong[9]] != word_sent[letters_position_wrong[9]]) and\
                         (word[letters_position_wrong[10]] != word_sent[letters_position_wrong[10]]) and\
                         (word[letters_position_wrong[11]] != word_sent[letters_position_wrong[11]]) and\
                         (word[letters_position_wrong[12]] != word_sent[letters_position_wrong[12]]) and\
                         (word[letters_position_wrong[13]] != word_sent[letters_position_wrong[13]]) and\
                         (word[letters_position_wrong[14]] != word_sent[letters_position_wrong[14]]) and\
                         (word[letters_position_wrong[15]] != word_sent[letters_position_wrong[15]]) and\
                         (word[letters_position_wrong[16]] != word_sent[letters_position_wrong[16]]) and\
                         (word[letters_position_wrong[17]] != word_sent[letters_position_wrong[17]]) and\
                         (word[letters_position_wrong[18]] != word_sent[letters_position_wrong[18]]) and\
                         (word[letters_position_wrong[19]] != word_sent[letters_position_wrong[19]]) and\
                         (word != word_sent):
                        filter_words.append(word)
                
                elif len(letters_position_wrong) == 21:
                    if (word[letters_position_wrong[0]] != word_sent[letters_position_wrong[0]]) and\
                         (word[letters_position_wrong[1]] != word_sent[letters_position_wrong[1]]) and\
                         (word[letters_position_wrong[2]] != word_sent[letters_position_wrong[2]]) and\
                         (word[letters_position_wrong[3]] != word_sent[letters_position_wrong[3]]) and\
                         (word[letters_position_wrong[4]] != word_sent[letters_position_wrong[4]]) and\
                         (word[letters_position_wrong[5]] != word_sent[letters_position_wrong[5]]) and\
                         (word[letters_position_wrong[6]] != word_sent[letters_position_wrong[6]]) and\
                         (word[letters_position_wrong[7]] != word_sent[letters_position_wrong[7]]) and\
                         (word[letters_position_wrong[8]] != word_sent[letters_position_wrong[8]]) and\
                         (word[letters_position_wrong[9]] != word_sent[letters_position_wrong[9]]) and\
                         (word[letters_position_wrong[10]] != word_sent[letters_position_wrong[10]]) and\
                         (word[letters_position_wrong[11]] != word_sent[letters_position_wrong[11]]) and\
                         (word[letters_position_wrong[12]] != word_sent[letters_position_wrong[12]]) and\
                         (word[letters_position_wrong[13]] != word_sent[letters_position_wrong[13]]) and\
                         (word[letters_position_wrong[14]] != word_sent[letters_position_wrong[14]]) and\
                         (word[letters_position_wrong[15]] != word_sent[letters_position_wrong[15]]) and\
                         (word[letters_position_wrong[16]] != word_sent[letters_position_wrong[16]]) and\
                         (word[letters_position_wrong[17]] != word_sent[letters_position_wrong[17]]) and\
                         (word[letters_position_wrong[18]] != word_sent[letters_position_wrong[18]]) and\
                         (word[letters_position_wrong[19]] != word_sent[letters_position_wrong[19]]) and\
                         (word[letters_position_wrong[20]] != word_sent[letters_position_wrong[20]]) and\
                         (word != word_sent):
                        filter_words.append(word)
            
                elif len(letters_position_wrong) == 22:
                    if (word[letters_position_wrong[0]] != word_sent[letters_position_wrong[0]]) and\
                         (word[letters_position_wrong[1]] != word_sent[letters_position_wrong[1]]) and\
                         (word[letters_position_wrong[2]] != word_sent[letters_position_wrong[2]]) and\
                         (word[letters_position_wrong[3]] != word_sent[letters_position_wrong[3]]) and\
                         (word[letters_position_wrong[4]] != word_sent[letters_position_wrong[4]]) and\
                         (word[letters_position_wrong[5]] != word_sent[letters_position_wrong[5]]) and\
                         (word[letters_position_wrong[6]] != word_sent[letters_position_wrong[6]]) and\
                         (word[letters_position_wrong[7]] != word_sent[letters_position_wrong[7]]) and\
                         (word[letters_position_wrong[8]] != word_sent[letters_position_wrong[8]]) and\
                         (word[letters_position_wrong[9]] != word_sent[letters_position_wrong[9]]) and\
                         (word[letters_position_wrong[10]] != word_sent[letters_position_wrong[10]]) and\
                         (word[letters_position_wrong[11]] != word_sent[letters_position_wrong[11]]) and\
                         (word[letters_position_wrong[12]] != word_sent[letters_position_wrong[12]]) and\
                         (word[letters_position_wrong[13]] != word_sent[letters_position_wrong[13]]) and\
                         (word[letters_position_wrong[14]] != word_sent[letters_position_wrong[14]]) and\
                         (word[letters_position_wrong[15]] != word_sent[letters_position_wrong[15]]) and\
                         (word[letters_position_wrong[16]] != word_sent[letters_position_wrong[16]]) and\
                         (word[letters_position_wrong[17]] != word_sent[letters_position_wrong[17]]) and\
                         (word[letters_position_wrong[18]] != word_sent[letters_position_wrong[18]]) and\
                         (word[letters_position_wrong[19]] != word_sent[letters_position_wrong[19]]) and\
                         (word[letters_position_wrong[20]] != word_sent[letters_position_wrong[20]]) and\
                         (word[letters_position_wrong[21]] != word_sent[letters_position_wrong[21]]) and\
                         (word != word_sent):
                        filter_words.append(word)
                    
                elif len(letters_position_wrong) == 23:
                    if (word[letters_position_wrong[0]] != word_sent[letters_position_wrong[0]]) and\
                         (word[letters_position_wrong[1]] != word_sent[letters_position_wrong[1]]) and\
                         (word[letters_position_wrong[2]] != word_sent[letters_position_wrong[2]]) and\
                         (word[letters_position_wrong[3]] != word_sent[letters_position_wrong[3]]) and\
                         (word[letters_position_wrong[4]] != word_sent[letters_position_wrong[4]]) and\
                         (word[letters_position_wrong[5]] != word_sent[letters_position_wrong[5]]) and\
                         (word[letters_position_wrong[6]] != word_sent[letters_position_wrong[6]]) and\
                         (word[letters_position_wrong[7]] != word_sent[letters_position_wrong[7]]) and\
                         (word[letters_position_wrong[8]] != word_sent[letters_position_wrong[8]]) and\
                         (word[letters_position_wrong[9]] != word_sent[letters_position_wrong[9]]) and\
                         (word[letters_position_wrong[10]] != word_sent[letters_position_wrong[10]]) and\
                         (word[letters_position_wrong[11]] != word_sent[letters_position_wrong[11]]) and\
                         (word[letters_position_wrong[12]] != word_sent[letters_position_wrong[12]]) and\
                         (word[letters_position_wrong[13]] != word_sent[letters_position_wrong[13]]) and\
                         (word[letters_position_wrong[14]] != word_sent[letters_position_wrong[14]]) and\
                         (word[letters_position_wrong[15]] != word_sent[letters_position_wrong[15]]) and\
                         (word[letters_position_wrong[16]] != word_sent[letters_position_wrong[16]]) and\
                         (word[letters_position_wrong[17]] != word_sent[letters_position_wrong[17]]) and\
                         (word[letters_position_wrong[18]] != word_sent[letters_position_wrong[18]]) and\
                         (word[letters_position_wrong[19]] != word_sent[letters_position_wrong[19]]) and\
                         (word[letters_position_wrong[20]] != word_sent[letters_position_wrong[20]]) and\
                         (word[letters_position_wrong[21]] != word_sent[letters_position_wrong[21]]) and\
                         (word[letters_position_wrong[22]] != word_sent[letters_position_wrong[22]]) and\
                         (word != word_sent):
                        filter_words.append(word)
                
                elif len(letters_position_wrong) == 24:
                    if (word[letters_position_wrong[0]] != word_sent[letters_position_wrong[0]]) and\
                         (word[letters_position_wrong[1]] != word_sent[letters_position_wrong[1]]) and\
                         (word[letters_position_wrong[2]] != word_sent[letters_position_wrong[2]]) and\
                         (word[letters_position_wrong[3]] != word_sent[letters_position_wrong[3]]) and\
                         (word[letters_position_wrong[4]] != word_sent[letters_position_wrong[4]]) and\
                         (word[letters_position_wrong[5]] != word_sent[letters_position_wrong[5]]) and\
                         (word[letters_position_wrong[6]] != word_sent[letters_position_wrong[6]]) and\
                         (word[letters_position_wrong[7]] != word_sent[letters_position_wrong[7]]) and\
                         (word[letters_position_wrong[8]] != word_sent[letters_position_wrong[8]]) and\
                         (word[letters_position_wrong[9]] != word_sent[letters_position_wrong[9]]) and\
                         (word[letters_position_wrong[10]] != word_sent[letters_position_wrong[10]]) and\
                         (word[letters_position_wrong[11]] != word_sent[letters_position_wrong[11]]) and\
                         (word[letters_position_wrong[12]] != word_sent[letters_position_wrong[12]]) and\
                         (word[letters_position_wrong[13]] != word_sent[letters_position_wrong[13]]) and\
                         (word[letters_position_wrong[14]] != word_sent[letters_position_wrong[14]]) and\
                         (word[letters_position_wrong[15]] != word_sent[letters_position_wrong[15]]) and\
                         (word[letters_position_wrong[16]] != word_sent[letters_position_wrong[16]]) and\
                         (word[letters_position_wrong[17]] != word_sent[letters_position_wrong[17]]) and\
                         (word[letters_position_wrong[18]] != word_sent[letters_position_wrong[18]]) and\
                         (word[letters_position_wrong[19]] != word_sent[letters_position_wrong[19]]) and\
                         (word[letters_position_wrong[20]] != word_sent[letters_position_wrong[20]]) and\
                         (word[letters_position_wrong[21]] != word_sent[letters_position_wrong[21]]) and\
                         (word[letters_position_wrong[22]] != word_sent[letters_position_wrong[22]]) and\
                         (word[letters_position_wrong[23]] != word_sent[letters_position_wrong[23]]) and\
                         (word != word_sent):
                        filter_words.append(word)
                
                elif len(letters_position_wrong) == 25:
                    if (word[letters_position_wrong[0]] != word_sent[letters_position_wrong[0]]) and\
                         (word[letters_position_wrong[1]] != word_sent[letters_position_wrong[1]]) and\
                         (word[letters_position_wrong[2]] != word_sent[letters_position_wrong[2]]) and\
                         (word[letters_position_wrong[3]] != word_sent[letters_position_wrong[3]]) and\
                         (word[letters_position_wrong[4]] != word_sent[letters_position_wrong[4]]) and\
                         (word[letters_position_wrong[5]] != word_sent[letters_position_wrong[5]]) and\
                         (word[letters_position_wrong[6]] != word_sent[letters_position_wrong[6]]) and\
                         (word[letters_position_wrong[7]] != word_sent[letters_position_wrong[7]]) and\
                         (word[letters_position_wrong[8]] != word_sent[letters_position_wrong[8]]) and\
                         (word[letters_position_wrong[9]] != word_sent[letters_position_wrong[9]]) and\
                         (word[letters_position_wrong[10]] != word_sent[letters_position_wrong[10]]) and\
                         (word[letters_position_wrong[11]] != word_sent[letters_position_wrong[11]]) and\
                         (word[letters_position_wrong[12]] != word_sent[letters_position_wrong[12]]) and\
                         (word[letters_position_wrong[13]] != word_sent[letters_position_wrong[13]]) and\
                         (word[letters_position_wrong[14]] != word_sent[letters_position_wrong[14]]) and\
                         (word[letters_position_wrong[15]] != word_sent[letters_position_wrong[15]]) and\
                         (word[letters_position_wrong[16]] != word_sent[letters_position_wrong[16]]) and\
                         (word[letters_position_wrong[17]] != word_sent[letters_position_wrong[17]]) and\
                         (word[letters_position_wrong[18]] != word_sent[letters_position_wrong[18]]) and\
                         (word[letters_position_wrong[19]] != word_sent[letters_position_wrong[19]]) and\
                         (word[letters_position_wrong[20]] != word_sent[letters_position_wrong[20]]) and\
                         (word[letters_position_wrong[21]] != word_sent[letters_position_wrong[21]]) and\
                         (word[letters_position_wrong[22]] != word_sent[letters_position_wrong[22]]) and\
                         (word[letters_position_wrong[23]] != word_sent[letters_position_wrong[23]]) and\
                         (word[letters_position_wrong[24]] != word_sent[letters_position_wrong[24]]) and\
                         (word != word_sent):
                        filter_words.append(word)

            return filter_words
        else:
            return database

    def save_games(self,status):
        """
        Se guardan los intentos ue se hicieron en el juego en 
        un archivo  txt con el nombre  response_game.txt
        """
        dictionary_times = {}
        
        self.end_time_get = time.time()
        # se almacena el tiempo de respuesta en una lista data por el get_response
        
        self.times.append(self.end_time_get- self.start_time_get)
        print(self.times)

        # se alamcena las respuesta en la base de datos postgresql
        # se crea un objeto de la clase Postgresql
        save_data = adp.Add_data_postgres("wordle_hqiu",
                                    "osdani1109", 
                                    "xlZC8coyZEuyIrxbCYSs79BxmsyLRLGW",
                                    "dpg-cb3nsk441lsfos6mr3ug-a.ohio-postgres.render.com",
                                    "5432")
        save_data.insert_data_param(self.response_get, self.times.pop(),status)
        # se hace la consulta de la primaria key de la base de datos
        pk = save_data.select_colomn_table("juegos", "id_game")
        pk = pk.pop()
        pk = list(pk).pop()
        print(pk)
       
        for i,dict_ in reversed(list(enumerate(self.list_attempts))):
            save_data.insert_data_result(pk,self.response_get, dict_, self.times[i])
        # se almacena la respuesta en una lista data por el get_response
        self.list_attempts.append(self.response_get)
        # se almacena los tiempos en un dcitionario
        dictionary_times['time'] = self.times
        self.list_attempts.append(dictionary_times)

        with open('response_game.txt', 'a') as filetxt:
            filetxt.write(str(self.list_attempts)+'\n')
    
    def search_word_game(self,filter_data,word_post):
        # se envia la palabra al post
        for i in range(5):
            #{
             #   "result_word": "string"
            #}
            self.request_post_word["result_word"] = word_post
            self.request_post(self.request_post_word)
            
            # se buscan las letras que no estan en la palabra
            wrong_letters, letters_true, letters_position_wrong = self.wrong_letters(word_post)
            
            if(len(word_post) == len(letters_true)):
                print("Se encontro la palabra: "+ word_post +" en el intento: ",i+1)
                # se almacena el tiempo de respuesta en una lista data por el post_response
                self.end_time_post = time.time()
                data = abs(self.end_time_post - self.start_time_post)

                self.times.append(data)
                # se guarda los juegos en un archivo json y un txt
                self.save_games("ganado")
                break
            # se filtra la las palabras que no estan en la posicion correcta
            filter_data = self.filter_words_by_letter_positions_wrong(filter_data, letters_position_wrong, word_post)
            # palabras filtradas que no estan en la posicion correcta
            
            # se filtra las palabras que no tienen las letras que se buscan
            filter_data = self.filter_words_by_letters(filter_data, wrong_letters)
            
            # filtrar palabras por posciones
            filter_data = self.filter_words_by_letter_positions(filter_data,letters_true,word_post)
            
            # se escogen una palabra al azar de las filtradas
            word_post = self.random_word_filters(filter_data)
            self.end_time_post = time.time()
            # se almacena el tiempo de respuesta en una lista data por el post_response
            self.times.append(abs(self.end_time_post - self.start_time_post))
        
        if(len(word_post) != len(letters_true)):
            self.save_games("perdido")


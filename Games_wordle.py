import Game_wordle as gw
import pandas as pd
import numpy as np
import re
import time
import requests
import Add_data_postgres as adp


class Games_wordle:
    def __init__(self, endpoint_get, endpoint_post, database, user, password):
        self.endpoint_post = endpoint_post
        self.endpoint_get = endpoint_get
        # credenciales 
        self.user = user
        self.password = password
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
        # lista para guardar los intentos del juego
        self.list_attempts = []
        # varialbes para calcular tiempos 
        self.times = []
        self.start_time_get = 0
        self.end_time_get = 0
        self.start_time_post = 0
        self.end_time_post = 0

    def start_game(self):
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
        return self.dataframe

    def calculate_highest_scoring_word(self, dataframe,dic_letter_score,name_column):
        """
        Esta funcion calcula el puntaje de cada una de las palabras de un dataframe
        word_list: lista de palabras
        dic_letter_score: diccionario con los puntajes de las letras
        name_column: nombre de la columna que se va a calcular
        return: lista con los puntajes de cada palabra
        """
        dataframe['score'] = dataframe[name_column].apply(lambda word: sum(dic_letter_score[letter]\
                                                                             for letter in word))
        return dataframe

    def calculate_dict_letter_score(self, Words):
        """
        Esta funcion calcula el puntaje de cada una de las letras de un diccionario
        para ello cuenta la cantidad de veces que aparece cada letra en la palabra
        Words: lista de palabras
        return: diccionario con los puntajes de las letras
        """
        dic_letter_score = {}
        for word in Words:
            for letter in word:
                if letter in dic_letter_score:
                    dic_letter_score[letter] += 1
                else:
                    dic_letter_score[letter] = 1
        return dic_letter_score

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

    def choose_word_with_highest_score(self,dataframe):
        """
        Esta funcion se encarga de elegir la palabra con mayor score
        dataframe: es un dataframe con las palabras
        """
        # se ordena el dataframe por el score
        dataframe = dataframe.sort_values(by = "score", ascending = False)
        # se toma la primera palabra del dataframe
        return dataframe.iloc[0]["Words"]
    
    def request_post(self, word):
        """
        Esta funcion se encarga de enviar la palabra al servidor
        self.request_post_word: es a un diccionario con la palabra 
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
        # se crea un diccionario para enviar la palabra al servidor
        self.request_post_word["result_word"] = word
        self.response_post = requests.post(self.endpoint_post, json = self.request_post_word,
                                             auth = (self.user,self.password))
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
        # se busca la posicion de las letras que no estan en la palabra
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
        return: una lista de palabras que no contienen letras que no corresponden a la palabra que se esta buscando
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

            return filter_words
        else:
            return database
    
    def filter_words_by_letter_positions_wrong(self, database, letters_position_wrong, word_sent):
        """
        Esta funcion elimina de la base de datos todas las palabras que tiene letras en las posiciones
        incorrectas 
        database: corresponde a las palabras que se van a filtrar debe ser un arreglo de palabras
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
                         (word != word_sent):
                        filter_words.append(word)
            return filter_words
        else:
            return database
    
    def create_dataframe_with_words_filter(self, filter_words):
        """
        crea un data frame con los datos de los filtrados 
        filter_words: lista de palabras filtradas
        return: dataframe_with_words_filter
        """
        dataframe_with_words_filter = pd.DataFrame(filter_words, columns=["Words"])
        return dataframe_with_words_filter

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
        pk = save_data.select_colomn_table("parametros_del_juego", "id_game")
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

    def search_word_game(self,filter_data,word_post):
        # se calcula el escore de cada letra y se guarda en un diccionario
        dictionary_score = self.calculate_dict_letter_score(self.database.split(' '))
        # se envia la palabra al post
        for i in range(5):
            #{
             #   "result_word": "string"
            #}
            self.request_post(word_post)
            
            # se buscan las letras que no estan en la palabra
            wrong_letters, letters_true, letters_position_wrong = self.wrong_letters(word_post)
            
            if(len(word_post) == len(letters_true)):
                print("Se encontro la palabra: "+ word_post +" en el intento: ",i+1)
                # se almacena el tiempo de respuesta en una lista data por el post_response
                self.end_time_post = time.time()
                data = self.end_time_post - self.start_time_post
                if data < 0:
                    data = 0.0
                else:
                    data = data
                self.times.append(data)
                # se guarda los juegos en un archivo json y un txt
                #self.save_games("ganado")
                break
            # se filtra la las palabras que no estan en la posicion correcta
            filter_data = self.filter_words_by_letter_positions_wrong(filter_data, letters_position_wrong, word_post)
            # palabras filtradas que no estan en la posicion correcta
            
            # se filtra las palabras que no tienen las letras que se buscan
            filter_data = self.filter_words_by_letters(filter_data, wrong_letters)
            
            # filtrar palabras por posciones
            filter_data = self.filter_words_by_letter_positions(filter_data,letters_true,word_post)
            
            # se crea un dataframe con las palabras filtradas
            dataframe = self.create_dataframe_with_words_filter(filter_data)
            # se calcula el escore de cada palabra 
            dataframe = self.calculate_highest_scoring_word(dataframe,dictionary_score,"Words")

            # se escogen una palabra al azar de las filtradas
            word_post = self.choose_word_with_highest_score(dataframe)
            self.end_time_post = time.time()
            # se almacena el tiempo de respuesta en una lista data por el post_response
            self.times.append(self.end_time_post - self.start_time_post)
        
        if(len(word_post) != len(letters_true)):
            #self.save_games("perdido")
            print("No se encontro la palabra: "+ word_post)

if __name__ == "__main__":
    # direccion del servidor
    endpoint_get = "https://7b8uflffq0.execute-api.us-east-1.amazonaws.com/game/get_params"
    endpoint_post = "https://7b8uflffq0.execute-api.us-east-1.amazonaws.com/game/check_results"
    # credenciales de acceso
    user = "daniel.rodriguez"
    password = "24ccc748da3a42edb624f0721875ef6c"
    # se carga la base de datos
    with open("final_data_cleaned.txt", "r", encoding='utf8') as file:
        database = file.read()
    
    # se crea el nuevo juego
    game = Games_wordle(endpoint_get, endpoint_post, database, user, password)
    # se hace la solicitudd a la API
    game.start_game()
    # se crea un dtaframe con los parametros del juego
    dataframe = game.create_dataframe()
    # se calcula el score de cada letra 
    dictionary_score = game.calculate_dict_letter_score(dataframe["Words"].tolist())
    # se calcula el score de cada palabra
    dataframe = game.calculate_highest_scoring_word(dataframe, dictionary_score, "Words")
    # se filtra la palabras segun las caracteristicas de la palabra dada por el servidor
    dataframe = game.filter_words()
    # se escoge la plabra con mayor score
    word_post = game.choose_word_with_highest_score(dataframe)
    # se comienza hacer los intetos
    game.search_word_game(dataframe["Words"].tolist(),word_post)
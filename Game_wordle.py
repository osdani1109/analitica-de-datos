import numpy as np
import pandas as pd
import re
import random
import requests

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

    def star_game(self):
        """
        para comenzar el juego se pide la palabra al servidor
        el serividor devuelve en un archivo json con lo siguiente:
        ● id: Un identificador único del juego generado
        ● length_word: Longitud de la palabra asignada
        ● vowels: Número de vocales en la palabra
        ● consonants: Número de consonantes en la palabra
        """
        # se hace la solicitud al servidor
        self.response_get = requests.get(self.endpoint_get, auth = (self.user,self.password))
        # respuesta del servidor en formato json
        print("respuesta del servidor: ",self.response_get)
        print("json:\n ",self.response_get.json())
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
        self.dataframe["Word length"] = [
            len(w) for w in self.dataframe["Words"]]
        quantity_vawols, quantity_consonats = self.quantity_vawols_consonats(
            self.dataframe["Words"])
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
        """
        self.response_post = requests.post(self.endpoint_post, json = response, auth = (self.user,self.password))
        print("respuesta del servidor: ",self.response_post)
        print("json:\n ",self.response_post.json())

        self.response_post = self.response_post.json()

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
        print("respuesta del servidor: ",self.response_post['position_array']) 
        array_position = np.array(self.response_post['position_array'])
        # corresponde la areglo de posiciones correctas de letras de la palabra
        result_true = np.where(array_position == True)
        print("aciertos:",result_true[0])
        # corresponde la areglo de posiciones incorrectas de letras de la palabra
        result_false = np.where(array_position == False)
        print("fallos:",result_false[0])
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
                    (word[i] != word[result_true[0][0]]) and\
                    (word[i] != word[result_true[0][1]]) and\
                    (word[i] != word[result_true[0][2]]) and\
                    (word[i] != word[result_true[0][3]]) and\
                    (word[i] != word[result_true[0][4]]) and\
                    (word[i] != word[result_true[0][5]]) and\
                    (word[i] != word[result_true[0][6]]):
                    remove_words_with_letters.append(word[i])
            
            elif len(result_true[0]) == 8:
                if word[i] not in ''.join(self.response_post['right_letters_in_wrong_positions']) and\
                    (word[i] != word[result_true[0][0]]) and\
                    (word[i] != word[result_true[0][1]]) and\
                    (word[i] != word[result_true[0][2]]) and\
                    (word[i] != word[result_true[0][3]]) and\
                    (word[i] != word[result_true[0][4]]) and\
                    (word[i] != word[result_true[0][5]]) and\
                    (word[i] != word[result_true[0][6]]) and\
                    (word[i] != word[result_true[0][7]]):
                    remove_words_with_letters.append(word[i])

            elif len(result_true[0]) == 9:
                if word[i] not in ''.join(self.response_post['right_letters_in_wrong_positions']) and\
                    (word[i] != word[result_true[0][0]]) and\
                    (word[i] != word[result_true[0][1]]) and\
                    (word[i] != word[result_true[0][2]]) and\
                    (word[i] != word[result_true[0][3]]) and\
                    (word[i] != word[result_true[0][4]]) and\
                    (word[i] != word[result_true[0][5]]) and\
                    (word[i] != word[result_true[0][6]]) and\
                    (word[i] != word[result_true[0][7]]) and\
                    (word[i] != word[result_true[0][8]]):
                    remove_words_with_letters.append(word[i])   
            
            if (word[i] in ''.join(self.response_post['right_letters_in_wrong_positions'])) :
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
        print("--------------------------------------",len(letters))
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
        database corresponde a las palabras 
        positions es vecgtor que corresponde a las posiciones de las letras que no se deben filtrar en 
        las palabras o buscar conincidencias en las palabras con la letra que se busca
        """
        filter_words = []
        if(len(positions)!=0)and(len(positions)<len(word_sent)):
            print("posiciones: ",positions)
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

            return filter_words
        else:
            return database

    def search_word_game(self,filter_data,word_post):
        # se envia la palabra al post
        for i in range(5):
            self.request_post_word["result_word"] = word_post
            self.request_post(self.request_post_word)
            
            # se buscan las letras que no estan en la palabra
            wrong_letters, letters_true, letters_position_wrong = self.wrong_letters(word_post)
            print("--------------------------------------------------------------------------------")
            print("letras que no estan en la palabra: ",wrong_letters)
            print("letras que no estan en la posicion correcta: ",letters_position_wrong)
            print("--------------------------------------------------------------------------------")
            if(len(word_post) == len(letters_true)):
                print("Se encontro la palabra: "+ word_post +" en el intento: ",i+1)
                break
            # se filtra la las palabras que no estan en la posicion correcta
            filter_data = self.filter_words_by_letter_positions_wrong(filter_data, letters_position_wrong, word_post)
            # palabras filtradas que no estan en la posicion correcta
            print("palabras por posiciones incorrectas:\n ",len(filter_data))
            # se filtra las palabras que no tienen las letras que se buscan
            filter_data = self.filter_words_by_letters(filter_data, wrong_letters)
            print("palabras filtradas\n: ",len(filter_data))
            # filtrar palabras por posciones
            filter_data = self.filter_words_by_letter_positions(filter_data,letters_true,word_post)
            print("palabras filtradas por posiciones\n: ",len(filter_data))
            # se escogen una palabra al azar de las filtradas
            word_post = self.random_word_filters(filter_data)
            print("palabra al azar: ",word_post,"---------------------------------") # muestra la palabra escogida  
            

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
    game = Game_wordle(endpoint_get, endpoint_post, database, user, password)
    # se hace la solicitud a la API para comezar el juego y obtener los parametros de la palabra
    game.star_game()
    # se crea una tabla con los parametros obtenidos
    game.create_dataframe()
    # se filtra la palabras segun las caracteristicas de la palabra dada por el servidor
    filter_data = game.filter_words()
    print(filter_data) # muestra las palabras filtradas
    
    filter_data = filter_data["Words"].tolist()
    print("Cantidad de palabras",len(filter_data),"-------------------------")
    # se escogen una palabra al azar de las filtradas
    word_post = game.random_word_filters(filter_data)
    print("palabra al azar: ",word_post) # muestra la palabra escogida
    # se busca la palabra en el juego
    game.search_word_game(filter_data, word_post)
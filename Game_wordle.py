import numpy as np
import pandas as pd
import re
import random

class Game_wordle:
    def __init__(self, endpoint_get, endpoint_post, database):
        self.endpoint_post = endpoint_post
        self.endpoint_get = endpoint_get
        self.response_get = {}
        self.response_post = {}
        self.database = database
        self.dataframe = pd.DataFrame()

    def star_game(self):
        """
        para comenzar el juego se pide la palabra al servidor
        el serividor devuelve en un archov json lo siguiente:
        ● id: Un identificador único del juego generado
        ● length_word: Longitud de la palabra asignada
        ● vowels: Número de vocales en la palabra
        ● consonants: Número de consonantes en la palabra
        """
        cont_vawels = 0
        cont_consonants = 0
        request_game = input("Ingrese la palabra: ")
        for l in request_game:
            if (l in "aeiou"):
                cont_vawels += 1
            else:
                cont_consonants += 1

        self.response_get["id"] = "12abf"
        self.response_get["lenght_word"] = len(request_game)
        self.response_get["vawels"] = cont_vawels
        self.response_get["consonants"] = cont_consonants
        return self.response_get

    def quantity_vawols_consonats(self, database):
        """
        Esta funcion cuenta la cantidad de vocales y consontates
        por palabra, la cantidad de vocales y consonantes son almacenadas
        en su correspodiente lista, la cual es retornada al final
        la funcion resibe un string como para metro
        database
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
        Esta funcion se encarga de crear un data frame con las palabras
        Words: palabras
        Word length: tamaño de la palabras
        vawols: canditad de vocales
        consonats:cantidad de consosnates
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
        """
        data_filter = self.dataframe
        data_filter = data_filter[((data_filter["Word length"] == self.response_get["lenght_word"]) &
                                    (self.dataframe["Vawols"] == self.response_get["vawels"]) &
                                    (self.dataframe["Consonts"] == self.response_get["consonants"]))]
        return data_filter

    def random_word_filters(self, filter_words):
        """
        Esta funcion se encarga de escoger una palabra al azar de las filtradas
        para ser enviada al post
        """
        word = random.choice(filter_words)
        return word

    def request_post(self, response):
        print(response)
        array_position = input("ingrese las conincidencias T O F: ").split(" ")
        array_letters = input("ingrese las letras que no estan en la poscion correcta: ").split(" ")
        print("posiciones: ",array_position)
        print("letras: ",array_letters)
        self.response_post["position_array"] = array_position
        self.response_post["right_letters_in_wrong_positions"] = array_letters
        # right_letters_in_wrong_positions

    def wrong_letters(self,word):
        """
        Esta funcion recibe como parametro la palabra que se envio 
        se encarga de buscar las letras que no estan en la palabara y a su vez 
        marcar las letras que se encuentra en la palabra pero en la posición incorrecta
        """
        # corresponde la areglo de posiciones correctas de letras de la palabra 
        array_position = np.array(self.response_post["position_array"]) 
        result_true = np.where(array_position == "true")
        print("tamaño:",len(result_true[0]))
        result_false = np.where(array_position == "false")
        # se transforma la palabra para que pueda ser iterada 
        word = ''.join(word)

        remove_words_with_letters = []
        for i in result_false[0]:
            if word[i] not in ''.join(self.response_post["right_letters_in_wrong_positions"]):
                remove_words_with_letters.append(word[i])
    
        return ''.join(remove_words_with_letters), result_true[0]

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
            return filter_words
        else:
            return database
    
    def search_word_game(self,filter_data,word_post):
        # se envia la palabra al post
        for i in range(6):
            print("--------------------------------------------------------------------------------")
            print("intento: ",i)
            print("--------------------------------------------------------------------------------")
            self.request_post(word_post)
            # se buscan las letras que no estan en la palabra
            wrong_letters, letters_true = self.wrong_letters(word_post)
            print("letras que no estan en la palabra: ",wrong_letters)
            # se filtra las palabras que no tienen las letras que se buscan
            filter_data = self.filter_words_by_letters(filter_data, wrong_letters)
            print("palabras filtradas\n: ",filter_data)
            print(len(filter_data))
            # filtrar palabras por posciones
            filter_data = self.filter_words_by_letter_positions(filter_data,letters_true,word_post)
            print("palabras filtradas por posiciones\n: ",filter_data)
            print(len(filter_data))
            # se escogen una palabra al azar de las filtradas
            word_post = self.random_word_filters(filter_data)
            print("palabra al azar: ",word_post) # muestra la palabra escogida  
            if(len(word_post) == len(letters_true)):
                print("Se encontro la palabra, en el intento: ",i+1)
                break

if __name__ == "__main__":

    endpoint_get = "direccion"
    endpoint_post = "direccion"
    # se carga la base de datos
    with open("final_data_cleaned.txt", "r", encoding='utf8') as file:
        database = file.read()
    # se crea el nuevo juego
    game = Game_wordle(endpoint_get, endpoint_post, database)
    # se hace la solicitud para comenzar un nuevo juego
    request_game = game.star_game()
    game.create_dataframe()
    # se filtra la palabras segun las caracteristicas de la palabra a adivinar 
    filter_data = game.filter_words()
    print(filter_data) # muestra las palabras filtradas
    # se escogen una palabra al azar de las filtradas
    filter_data = filter_data["Words"].tolist()
    print("Cantidad de palabras",len(filter_data),"-------------------------")
    word_post = game.random_word_filters(filter_data)
    print("palabra al azar: ",word_post) # muestra la palabra escogida
    # se busca la palabra en el juego
    game.search_word_game(filter_data, word_post)
    
        
    
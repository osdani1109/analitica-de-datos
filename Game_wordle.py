import numpy as np
import pandas as pd
import re
class Game_wordle:
    def __init__(self,endpoint_get,endpoint_post,database):
        self.endpoint_post = endpoint_post
        self.endpoint_get = endpoint_get
        self.response_get = { }
        self.response_post = { }
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
        self.response_get["consonants"]  = cont_consonants
        return self.response_get

    def quantity_vawols_consonats(self,database):
        """
        Esta funcion cuenta la cantidad de vocales y consontates 
        por palabra, la cantidad de vocales y consonantes son almacenadas 
        en su correspodiente lista, la cual es retornada al final
        la funcion resibe un string como para metro 
        database 
        """
        quantity_vawols = []
        quantity_consonats = []
        cont_vawels =0
        cont_consonants =0
        for word in database:
            # se crea un regex para encontrar solo las letras 
            cont_vawels = len(re.findall("[aeiou]", word))
            cont_consonants = len(re.findall("[b-df-hj-np-tv-xz]", word))
            quantity_vawols.append(cont_vawels)
            quantity_consonats.append(cont_consonants)

        return quantity_vawols,quantity_consonats

    def create_dataframe(self):
        """
        Esta funcion se encarga de crear un data frame con las palabras 
        Words: palabras
        Word length: tamaño de la palabras
        vawols: canditad de vocales
        consonats:cantidad de consosnates 
        """
        self.dataframe["Words"] = self.database.split(" ")
        self.dataframe["Word length"] = [len(w) for w in self.dataframe["Words"]]
        quantity_vawols,quantity_consonats  = self.quantity_vawols_consonats(self.dataframe["Words"])
        self.dataframe["Vawols"] = quantity_vawols
        self.dataframe["Consonts"] = quantity_consonats

if __name__ == "__main__":
    endpoint_get = "direccion"
    endpoint_post = "direccion"
    #se carga la base de datos 
    with open("final_data_cleaned.txt", "r",encoding='utf8') as file:
        database = file.read()

    game = Game_wordle(endpoint_get, endpoint_post,database)
    request_game = game.star_game()
    game.create_dataframe()
    print(game.dataframe)
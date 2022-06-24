import os
import re
from collections import OrderedDict
import nltk
from nltk.corpus import stopwords
# files = []
# dir_files = os.listdir(direction)

# for name_file in dir_files:
#     with open(direction + '/' + name_file, 'r', encoding='utf8') as file:
#         files_save = file.read()
#         files.append(files_save)

# with open("Total_data_file.txt", "w", encoding='utf8') as new_file:
#     new_file.write(' '.join(files))

# with open("Total_data_file.txt", "r", encoding='utf8') as Total_file:
#     data = Total_file.read()

class Database_cleanup:
    def __init__(self):
        self.files = []
        self.database = ''

    def join_database(self,direction):
        # se carga las directiones en las que se encuentras las bases de datos
        dir_files = os.listdir(direction)
        for name_file in dir_files:
            with open(direction + '/' + name_file, 'r', encoding='utf8') as file:
                files_save = file.read()
                self.files.append(files_save)
        # se guarda las bases de datos en un nuveov txt
        with open("Total_data_file.txt", "w", encoding='utf8') as new_file:
            new_file.write(' '.join(self.files))
        # lectura de de la base de datos unidad 
        with open("Total_data_file.txt", "r", encoding='utf8') as Total_file:
            self.database = Total_file.read()
        return self.database

    def remove_uppercase(self,database):
        # se elimina la palabras con mas de 2 letras mayusculas
        data_base = re.sub(r"\w*[A-Z]\w*[A-Z]\w*"," ",database)
        # se pasa a minusculas todo el texto
        data_base  = data_base.lower()
        return data_base 

    def remove_letters_accents(self,database):
        # se elimina las tildes 
        a,b = 'áéíóúÁÉÍÓÚ','aeiouAEIOU'
        trans = str.maketrans(a,b)
        data_base  = database.translate(trans)
        return data_base

    def remove_invalid_characters(self,database):
        #se eliminana las palabars que nos son de alfabeto español
        data_base = re.sub(r'[^a-zñ]+',' ',database)
        return data_base
    # funcion que remueve palabras menores a 4 letras
    def remove_words(self,database):
        list_data = []
        for word in database:
            if len(word)>3:
                list_data.append(word)
        return ' '.join(list_data)

    def remove_repeated_words(self,database):
        ulist = []
        # se agregan las palabras si estas no estan en la lista
        # [ulist.append(word) for word in database if word not in ulist]
        ulist = list(OrderedDict.fromkeys(database)) 
        return ' '.join(ulist)

    def remove_stopwords(self, database):
        # esta funcion se usa para eliminar los stop words de la base de datos 
        nltk.download('stopwords')
        stop_words = stopwords.words('spanish')
        ulist = []
        for word in database.split(' '):
            if word not in stop_words:
                ulist.append(word)
        return ' '.join(ulist)
    def save_database(self,database):
        # se guarda la base de datos en un txt
        with open("final_data_cleaned.txt", "w",encoding='utf8') as file_clear:
            file_clear.write(database)

if __name__ == "__main__":
    direction = "C:/Users/ASUSVivoBook/Documents/Github/analitica-de-datos/data understanding/raw_texts"
    database = Database_cleanup()
    # se alamacena las bases de datos en una sola base de datos 
    new_database = database.join_database(direction)
    # se remueve las palabaras que tiene mas de una mayuscualas y se debaja todo el texto en minuscula
    new_database = database.remove_uppercase(new_database)
    # se remueve las vocales con acentos
    new_database = database.remove_letters_accents(new_database)
    # se remueve los caractesres no validos 
    new_database = database.remove_invalid_characters(new_database)
    # se remueve las palabras con menos de 3 letras
    new_database = database.remove_words(re.split(" ",new_database))
    # se remueve las palabras repetidas 
    new_database = database.remove_repeated_words(re.split(" ",new_database)) 
    # se remueve las stopwords
    new_database = database.remove_stopwords(new_database)
    # se guarda la base de datos limpiada en un archivo txt 
    database.save_database(new_database)
    #print(sorted(set(new_database)))
    print(len(re.split(" ",new_database)))

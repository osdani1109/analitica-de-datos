import Game_wordle as gw

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
    game = gw.Game_wordle(endpoint_get, endpoint_post, database, user, password)
    # se crea una tabla con los parametros obtenidos
    game.create_dataframe()
    # se hace la solicitud a la API para comezar el juego y obtener los parametros de la palabra
    game.star_game()
    # se filtra la palabras segun las caracteristicas de la palabra dada por el servidor
    filter_data = game.filter_words()
    
    filter_data = filter_data["Words"].tolist()
   
    # se escogen una palabra al azar de las filtradas
    word_post = game.random_word_filters(filter_data)

    # se busca la palabra en el juego
    game.search_word_game(filter_data, word_post)
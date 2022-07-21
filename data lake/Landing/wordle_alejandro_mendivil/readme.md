##Sobre los tiempos medidos:
Mido los tiempos antes y después de interactuar tanto con la API GET como la API POST.
Así mismo, mido el tiempo final de cada juego, y el tiempo inicial y final de cada intento.
A continuación, un esquema breve del código que ilustra dónde se mide cada tiempo:

-> mido word_req_start_time
[pido pistas de palabra a servidor]
-> mido game_start_time

[hago unos procesos]

[inicio ciclo de intentos]
-> mido attempt_start_time
[escojo la palabra]

-> mido test_req_time
[pido prueba de palabra al servidor]
-> mido test_res_time
-> guardo server_test_time (la hora que devuelve el servidor al hacer la prueba de la palabra)

[acabo el juego, o continúo haciendo filtros con lo que obtuve]
-> mido attempt_end_time
[fin de ciclo de intentos]

-> mido game_end_time

##Sobre game_resol_method:
Hice intentos con 2 métodos de selección de palabras distintos (1 y 2). El titular es el método 2.

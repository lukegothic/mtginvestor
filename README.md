# mtginvestor
__mycache__                     --> ¡¡¡¡obsoletar!!! mover a cada dir de cada endpoint
__pycache__
.vscode
backup                          --> ¡¡¡¡obsoletar!!!  (mover a cada endpoint)
bin                             --> ¡¡¡¡obsoletar!!! archivos ejecutables que son los que realizan acciones (MOVER A RAIZ)
data                            --> ¡¡¡¡obsoletar!!! mover a cada dir de cada endpoint
data_preparation                --> ¡¡¡¡obsoletar!!! cache y salida de data_preparation
docs                            --> informacion variada del y sobre el proyecto
old                             --> codigo legacy no usado, probablemente no funcionará
output                          --> directorio de salida de los procesos
tampermonkey_scripts            --> scripts de tampermonkey asociados con el proyecto
templates                       --> html de plantilla para mostrar info
endpoints/*                     --> una carpeta por cada endpoint que se consume (ck, cubecobra, deckbox)
endpoints/[endpointid]/backup   --> copias de seguridad antes de realizar operaciones destructivas
endpoints/[endpointid]/cache    --> cache de datos descargados
endpoints/[endpointid]/data     --> datos estaticos del endpoint
utils/*                         --> utilidades generales/codigo comun etc
utils/cardview.py               --> convierte una lista de cartas a html + visor
utils/dateutils.py              --> funciones de fecha
utils/decklist.py               --> carga las cartas de una baraja desde fichero o texto
utils/ftp.py                    --> utilidades ftp
utils/image.py                  --> utilidades imagen
utils/ospath.py                 --> utilidades os y path
utils/phppgadmin.py             --> utilidades pgadmin
utils/sqlite3.py                --> utilidades sqlite3
utils/traductor.py              --> traduce codigos entre endpoints
utils/web.py                    --> utilidades web
# directorio raiz
archivos principales del proyecto, agregadores de los endpoint dando como resultado salidas diversas

_mkm_data_preparation.py --> realiza operaciones de consumo y empaquetado de datos de uno o varios endpoint
setup.py            --> crea el instalador del proyecto

#TODO
base.py
main.py
main2.py
endpoints/*




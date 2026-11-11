# Plan de arquitectura de traductor-epub-opencode

## Contexto y mision

Este documento describe la arquitectura actual del proyecto. El proyecto nacio como un bot de Telegram con proveedores de inteligencia artificial externos basados en claves de API, y evoluciono hacia una herramienta local de linea de comandos que traduce libros electronicos usando opencode como motor de inferencia. La mision actual es ofrecer un traductor de libros que no requiera claves de API externas, que se ejecute desde la terminal y que tambien pueda invocarse como skill desde opencode. La interfaz de Telegram queda registrada como propuesta de mejora futura y no forma parte del alcance actual.

El analisis previo de repositorios de referencia sigue siendo la base conceptual del sistema. De quantrancse se toma el recorrido del OPF para determinar el orden de archivos y la preservacion de la jerarquia de carpetas al reempaquetar. De slyh se toma la idea de limpiar el HTML antes de enviarlo al modelo. De oomol-lab se toman la cache de traducciones, la concurrencia controlada con semaforo y los modos de salida. De jb41 se toma la reanudacion a nivel de capitulo. De Mubumbutu se toma el sistema de placeholders numerados para el marcado inline. De hydropix se toma la arquitectura de proveedores intercambiables. De KazKozDev se toma la segunda pasada de revision como modo de calidad opcional. De Calibre se toma la conversion de formatos, la escritura de metadatos y la deteccion de DRM. Todo se implementa desde cero en Python sin copiar codigo de ninguna fuente.

---

## Vision general de la arquitectura

El sistema se organiza en cinco capas desacopladas bajo el paquete traductor_epub_opencode, de manera que cada capa puede reemplazarse de forma independiente. La capa core procesa el EPUB y contiene el lector, el limpiador, el restaurador, el empaquetador y el orquestador. La capa providers abstrae el motor de traduccion tras una interfaz comun, con opencode como implementacion actual. La capa state gestiona la cache de traducciones y el estado de reanudacion del trabajo. La capa security contiene todas las validaciones de entrada, la deteccion de prompt injection y la verificacion de ejecutables. La capa calibre envuelve los ejecutables ebook-convert y ebook-meta mediante subprocess.

    src/traductor_epub_opencode/
    ├── core/
    │   ├── reader.py      (abre el ZIP, valida integridad y DRM, lee el OPF y los capitulos)
    │   ├── cleaner.py     (convierte HTML a texto con placeholders numerados)
    │   ├── restorer.py    (restaura placeholders, valida traduccion y sanitiza el HTML final)
    │   ├── packager.py    (reempaqueta el EPUB preservando la jerarquia)
    │   └── translator.py  (orquestador que coordina todo el pipeline)
    ├── providers/
    │   ├── base.py        (clase abstracta TranslationProvider)
    │   └── opencode.py    (adaptador que invoca opencode como proceso hijo)
    ├── state/
    │   ├── cache.py       (cache en disco indexada por hash SHA256 e idioma)
    │   └── job.py         (estado por capitulo para reanudacion)
    ├── security/
    │   └── validation.py  (limites de tamano, rutas ZIP, DRM, injection, ejecutables)
    ├── calibre/
    │   ├── converter.py   (wrapper de ebook-convert)
    │   └── metadata.py    (wrapper de ebook-meta)
    └── cli.py             (punto de entrada de la linea de comandos)

Complementan el paquete el directorio skill con la skill invocable desde opencode, el directorio tests con las pruebas automatizadas y el workflow de GitHub Actions en .github/workflows/ci.yml.

---

## Flujo del pipeline

La traduccion de un libro sigue este camino dentro del orquestador translator.py. Cada paso aplica una validacion de seguridad antes de continuar, de modo que ninguna entrada maliciosa alcanza al motor de traduccion ni al sistema de archivos.

    entrada
      │
      ├── check_file_size          limita el tamano del archivo de entrada
      ├── open_epub                abre el ZIP, valida integridad, rutas y DRM
      ├── read_chapter             decodifica cada capitulo con fallback latin-1
      ├── clean_html               extrae texto con placeholders [T01] y [P01]
      ├── detect_prompt_injection  bloquea el proceso si el texto contiene patrones hostiles
      ├── TranslationCache.get     consulta la cache por hash e idioma
      ├── provider.translate       invoca opencode si no hay cache hit
      ├── restore_html             reintegra los placeholders como HTML original
      ├── sanitize_translated_html elimina scripts, estilos y atributos peligrosos
      ├── validacion lxml          rechaza el resultado si el HTML restaurado no parsea
      ├── modo de salida           replace, bilingual_inline o bilingual_block
      ├── TranslationJob           marca el capitulo como completado para reanudacion
      └── repack_epub + write_metadata  escribe el EPUB final y actualiza metadatos

El orquestador limita la concurrencia con un semaphore de tres tareas y aplica un timeout global configurable sobre toda la operacion. El modo de solo lectura evita escribir el EPUB de salida y los metadatos, util para validaciones sin efectos en disco. Al terminar se registra una linea de auditoria con archivo de entrada, archivo de salida e idioma.

---

## Nucleo de procesamiento

### reader.py

El lector abre el archivo como ZIP y ejecuta tres verificaciones de seguridad antes de parsear. La primera comprueba que el tamano comprimido no supere el limite configurado. La segunda valida la integridad del ZIP con la cantidad de entradas y el tamano total descomprimido. La tercera detecta DRM verificando la presencia de META-INF/container.xml y la ausencia de META-INF/encryption.xml. Las rutas internas de las entradas se normalizan con posixpath para evitar escapes de directorio mediante secuencias de puntos. Despues de las verificaciones, el lector lee META-INF/container.xml, resuelve la ruta del OPF, parsea el manifest y recorre el spine en orden de lectura. Los hrefs con navegacion relativa se normalizan para soportar OPFs en cualquier subcarpeta.

### cleaner.py y restorer.py

El limpiador recorre cada elemento de bloque del capitulo y clasifica el contenido. Los tags inline como em, strong, span y a se reemplazan por pares de tokens [T01]/[/T01] guardando la serializacion exacta del tag original con todos sus atributos. Los elementos no traducibles como img, code, pre y script se reemplazan por tokens de posicion [P01]. El resultado es un texto limpio que el modelo puede traducir sin riesgo de alterar el marcado.

El restaurador realiza el proceso inverso con tres garantias. Detecta los tokens omitidos por el modelo y los registra como advertencias mediante count_token_mismatches. Restaura cada token a su HTML original usando el mapa guardado. Y aplica sanitize_translated_html sobre el resultado final, eliminando scripts, estilos, iframes y atributos de eventos, de modo que la salida no pueda inyectar codigo ejecutable en el lector del usuario. La funcion validate_translation comprueba ademas la proporcion de longitud entre original y traduccion para detectar omisiones o duplicaciones del modelo.

### packager.py y translator.py

El empaquetador reescribe las entradas traducidas dentro del ZIP preservando la jerarquia de carpetas, el mimetype y todos los archivos no traducibles. El orquestador translator.py coordina el pipeline completo, expone la configuracion mediante la clase TranslationConfig con idioma, modo de salida, modo de calidad, directorio de cache, tamano maximo y modo de solo lectura, y compone el system prompt que exige preservar los tokens entre corchetes sin modificarlos.

---

## Capa de proveedores

La clase base abstracta TranslationProvider define dos metodos, translate que recibe texto y system prompt y devuelve la traduccion, y estimate_tokens que aproxima un token por cada cuatro caracteres en escritura latina. Esta abstraccion permite agregar adaptadores futuros sin tocar el nucleo.

OpencodeProvider invoca opencode como proceso hijo en modo no interactivo. El comando se resuelve con la variable de entorno OPENCODE_COMMAND y por defecto es opencode run. El texto y el system prompt se envian por stdin separados por un delimitador, la respuesta se lee de stdout, y un timeout configurable mata el proceso si no responde. Antes de crear el proceso, el adaptador verifica la existencia del ejecutable en el PATH mediante check_executable, y un codigo de salida distinto de cero produce un RuntimeError con el stderr incluido. No se requiere ninguna clave de API porque opencode gestiona sus propios modelos.

---

## Estado y reanudacion

### cache.py

La cache guarda cada traduccion en disco indexada por el hash SHA256 del texto original mas el codigo de idioma de destino, de manera que el mismo fragmento puede estar traducido a varios idiomas sin conflicto y el mismo texto repetido en el libro se traduce una sola vez. Si un archivo de cache esta corrupto, se elimina y se vuelve a traducir el fragmento sin interrumpir el proceso.

### job.py

El trabajo guarda un archivo JSON con el estado de cada capitulo, con tres valores posibles, pending, in_progress y completed. Al retomar un archivo ya procesado, el orquestador carga el estado, salta los capitulos completados y continua desde el punto de interrupcion. Al completar todos los capitulos, el trabajo elimina su directorio temporal.

---

## Seguridad

La capa security centraliza las validaciones de todo el sistema. Los limites de tamano son configurables mediante variables de entorno, con MAX_FILE_SIZE_BYTES para el archivo de entrada, MAX_UNCOMPRESSED_BYTES para el contenido descomprimido y MAX_ZIP_ENTRIES para la cantidad de entradas del ZIP. La deteccion de prompt injection aplica cinco patrones sobre el texto limpio de cada fragmento y bloquea el proceso con un error explicito en lugar de solo registrar la coincidencia, de modo que instrucciones hostiles embebidas en el contenido del libro nunca alcanzan al motor. La sanitizacion del HTML traducido elimina scripts, estilos, iframes y controladores de eventos. La verificacion de ejecutables evita errores cripticos de subprocess cuando Calibre u opencode no estan instalados. El registro de auditoria deja trazabilidad de cada traduccion completada.

---

## Integracion con Calibre

Los formatos MOBI, AZW3, FB2, RTF y DOCX se convierten a EPUB mediante ebook-convert antes de procesarse, y el resultado final siempre se entrega como EPUB. La conversion corre en un subprocess asincrono con timeout y verifica el formato de entrada antes de invocar el ejecutable. Tras la traduccion, ebook-meta actualiza los metadatos con el codigo de idioma de destino y silencia cualquier fallo de esta escritura para no perder el trabajo ya hecho. La deteccion de DRM se basa en la estructura del ZIP y produce un mensaje claro sobre proteccion digital en lugar de una excepcion interna.

---

## Interfaz de linea de comandos y skill

La CLI traductor-epub acepta el archivo de entrada, el idioma de destino con -l, el modo de salida con -m, el nivel de calidad con -q, la ruta de salida con -o y el directorio de cache con --cache-dir. Si no se indica salida, el resultado se escribe junto al original con sufijo _translated. La skill en skill/SKILL.md permite que opencode invoque la herramienta como parte de una conversacion, y las variables de entorno OPENCODE_COMMAND, TRANSLATIONS_CACHE_DIR y DOWNLOADS_DIR configuran el comportamiento sin tocar codigo.

---

## Calidad, pruebas e integracion continua

Las pruebas automatizadas cubren el lector con EPUBs reales minimos, el limpiador y el restaurador con casos borde, el empaquetador, la cache, el estado de reanudacion, la seguridad, el orquestador con proveedor simulado, los modos bilingues, Calibre con subprocess simulado y la CLI. El workflow de GitHub Actions ejecuta ruff check, ruff format --check y pytest con un umbral de cobertura del ochenta por ciento en cada push y pull request sobre main. El entorno se gestiona con pyproject.toml y el paquete se instala en modo editable con pip install -e .

---

## Roadmap

Las siguientes mejoras estan previstas sobre esta arquitectura. La inyeccion de glosario en el system prompt permitira al usuario pasar un archivo de terminos con --glossary para que el modelo respete traducciones fijas de forma contextualmente coherente. La agrupacion de fragmentos por tokens estimados reducira el numero de llamadas a opencode acumulando parrafos hasta un umbral configurable. El flag de solo lectura y el log de auditoria a archivo se expondran desde la CLI para trazabilidad completa. El manejo de errores de la CLI mejorara con mensajes accionables y codigos de salida diferenciados. La guia de contribucion documentara el estilo del codigo y el proceso de pull request. A largo plazo quedan abiertas la interfaz de Telegram como frontend del nucleo actual y los adaptadores de API keys como proveedores alternativos opcionales.

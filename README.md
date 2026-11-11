# traductor-epub-opencode

Traductor de libros electronicos que usa opencode como motor de inferencia. No requiere claves de API externas. Acepta EPUB, MOBI, AZW3, FB2, RTF y DOCX. El libro traducido conserva la tabla de contenidos, las imagenes, las hojas de estilo, los hiperenlaces internos y el orden de capitulos del original.

## Mision

El proyecto nacio como un bot de Telegram con proveedores de inteligencia artificial externos. La mision actual es ofrecer una herramienta local que traduzca libros electronicos usando los modelos disponibles en opencode. La herramienta se ejecuta desde la linea de comandos y tambien como skill invocable desde opencode. Telegram queda como propuesta de mejora futura.

## Que hace este proyecto

El sistema recibe un archivo de libro electronico, lo procesa internamente respetando la estructura original del EPUB, lo traduce al idioma que el usuario seleccione usando opencode como motor, y devuelve el resultado como un archivo listo para abrir en cualquier lector de ebooks. El libro traducido conserva la tabla de contenidos, las imagenes, las hojas de estilo, los hiperenlaces internos y el orden de capitulos del original, sin alterar nada de la estructura que no sea el texto visible.

## Formatos de entrada aceptados

EPUB, MOBI, AZW3, FB2, RTF y DOCX. Los formatos que no son EPUB se convierten automaticamente a ese formato antes de procesarse, usando Calibre como conversor de sistema, y el resultado final se entrega igualmente como EPUB con los metadatos del libro actualizados para reflejar el idioma de destino.

## Motor de traduccion

El motor de traduccion es opencode. No se requieren claves de API externas. La herramienta invoca opencode como proceso hijo para cada fragmento de texto, capturando la salida y restaurandola en el EPUB. La interfaz de proveedores queda preparada para agregar adaptadores de API keys en el futuro sin modificar el nucleo.

## Modos de salida

El usuario puede elegir entre tres modos antes de confirmar la traduccion. El modo reemplazar elimina el texto original y deja solo la traduccion en el lugar de cada parrafo. El modo bilingue inline agrega la traduccion inmediatamente despues del parrafo original en el mismo elemento HTML, separada por un espacio. El modo bilingue bloque inserta la traduccion como un parrafo nuevo a continuacion del original, con una clase CSS diferente para que los lectores que soporten estilos puedan distinguirlos visualmente.

## Nivel de calidad

El modo normal traduce cada grupo de fragmentos en una sola pasada al modelo. El modo de alta calidad aplica una segunda llamada al mismo modelo por cada grupo, enviando tanto el texto original como la traduccion generada y pidiendole que evalúe si hay nombres propios incorrectamente traducidos, terminos del glosario que no se respetaron, o frases que suenen poco naturales en el idioma de destino. Si no detecta ningun problema, la segunda pasada devuelve la traduccion sin cambios y el costo adicional se reduce al minimo. Si detecta algun problema, devuelve la version corregida.

## Requisitos del sistema

Python 3.11 o superior. Calibre instalado como aplicacion del sistema, accesible desde la terminal mediante los comandos ebook-convert y ebook-meta. Opencode instalado y disponible en el PATH del sistema.

## Instalacion

Clonar el repositorio e instalar las dependencias:

    git clone https://github.com/TU_USUARIO/traductor-epub-opencode.git
    cd traductor-epub-opencode
    pip install -e .

Copiar la plantilla de variables de entorno si se desea configurar opciones adicionales:

    cp .env.example .env

Iniciar la traduccion desde la linea de comandos:

    traductor-epub libro.epub -l es -m replace -q normal

O invocar la skill desde opencode.

## Estructura del proyecto

    src/traductor_epub_opencode/   nucleo del traductor
    tests/                        pruebas automatizadas
    skill/                        skill para opencode
    documents/                    documentacion tecnica

## Variables de entorno

    OPENCODE_COMMAND    comando para invocar opencode, por defecto opencode run
    TRANSLATIONS_CACHE_DIR   directorio para la cache de traducciones en disco
    DOWNLOADS_DIR            directorio temporal para los archivos del usuario

## Testing

El proyecto incluye pruebas automatizadas con pytest. Para ejecutarlas:

    pytest tests/ -v

## Propuesta de mejora futura

Telegram como interfaz de usuario. En una version futura se podria agregar un bot de Telegram que use esta misma herramienta como backend, permitiendo traducir libros desde el chat. Esta funcionalidad no esta implementada en la version actual.

## Licencia

MIT
# Guia de contribucion

## Requisitos del entorno

Python 3.11 o superior. Calibre instalado como aplicacion del sistema con los ejecutables ebook-convert y ebook-meta disponibles en el PATH. Opencode instalado y disponible en el PATH. Git para control de versiones.

## Instalacion para desarrollo

Clonar el repositorio e instalar el paquete en modo editable junto con las dependencias de desarrollo.

    git clone https://github.com/Nemryz/traductor-epub-opencode.git
    cd traductor-epub-opencode
    python -m venv venv
    venv\Scripts\pip install -e .
    venv\Scripts\pip install pytest pytest-cov ruff

## Ejecucion de pruebas

El proyecto incluye pruebas automatizadas con pytest. Para ejecutarlas todas.

    venv\Scripts\pytest tests/ -v

Para verificar la cobertura de codigo con un umbral minimo del ochenta por ciento.

    venv\Scripts\pytest tests/ --cov=src/traductor_epub_opencode --cov-report=term-missing --cov-fail-under=80

## Estilo de codigo

El proyecto usa ruff para linting y formateo. Antes de enviar un cambio, ejecutar ambas verificaciones.

    venv\Scripts\ruff check src tests
    venv\Scripts\ruff format src tests

Las reglas de estilo para los archivos del proyecto son las siguientes. El texto en espanol. Las oraciones en prosa no terminan con punto y coma ni con dos puntos. Las citas usan comillas simples en lugar de comillas dobles. No se usan negritas ni cursivas en la prosa. La estructura es continua. Los comentarios de una sola linea con almohadilla describen lo que hace el codigo, sin docstrings. No se usan palabras reservadas como identificadores.

## Proceso de pull request

Crear una rama descriptiva para cada cambio.

    git checkout -b feat-descripcion-corta

Desarrollar en esa rama, ejecutar pruebas y linting, y hacer commit con un prefijo apropiado. Los prefijos validos son feat, fix, docs, test, chore y refactor. El mensaje describe lo que se hizo, sin mencionar fases ni etapas.

    git commit -m "feat: descripcion del cambio"

Subir la rama y crear el pull request.

    git push -u origin feat-descripcion-corta
    gh pr create

El workflow de GitHub Actions ejecuta linting, formateo y pruebas en cada push y pull request. Un pull request solo se acepta cuando todas las verificaciones pasan.

## Estructura del proyecto

El nucleo del traductor vive en src/traductor_epub_opencode. Las pruebas en tests. La skill para opencode en skill. La documentacion tecnica en documents. Los cambios deben mantener la separacion de responsabilidades entre las capas core, providers, state, security y calibre.

## Agregar un nuevo proveedor

Los proveedores heredan de TranslationProvider en providers/base.py e implementan los metodos name y translate, ademas de estimate_tokens si se necesita una estimacion distinta a la por defecto. Agregar la nueva clase en providers y registrarla donde corresponda. No modificar el nucleo para soportar un proveedor nuevo.

## Reporte de problemas

Abrir un issue en el repositorio describiendo el problema, los pasos para reproducirlo y el entorno en el que ocurre.

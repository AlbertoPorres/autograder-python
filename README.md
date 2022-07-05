Plataforma de Corrección Automática de Ejercicios en Python
=

[![made-with-python](https://img.shields.io/badge/Coded%20with-Python-21496b.svg?style=flat-square)](https://www.python.org/)
[![made-with-latex](https://img.shields.io/badge/Documented%20with-LaTeX-4c9843.svg?style=flat-square)](https://www.latex-project.org/) ![GitHub](https://img.shields.io/github/license/AlbertoPorres/autograder-python?style=flat-square) 

Trabajo de Fin de Grado, del Grado Universitario en **Ingeniería Informática** en la **Universidad de Burgos** realizado por **Alberto Porres Fernández**

Tutores: **Bruno Baruque Zanón** y **Roberto Carlos Casado Vara**.

---
### Contenido del repositorio
Este repositorio alberga todo el contenido relativo al Trabajo de Fin de Grado de Alberto Porres Fernández:

* **Curso-Python**: Directorio de contenido del curso introductorio a Python desarrollado en este proyecto.
* **doc**: Directorio de documentación del proyecto perteneciente a la herramienta LaTeX. En este directorio podrá encontrar la **memoria y los anexos** relativos a la realización del proyecto.
* **env**: Directorio del entorno virtual utilizado en el proceso de desarrollo de la plataforma en el que se encuentran todas las dependencias software de la misma.
* **migrations**: Directorio de migraciones de la base de datos de la plataforma durante su desarrollo.
* **src**: Directorio de código fuente de la plataforma.
* **Dockerfile**: Archivo de creación de la imagen del contenedor Docker desde el que es ejecutada la plataforma.
* **LICENCE.txt**: Archivo de licencia.
* **README.md**: Archivo actual.
* **app.py**: Archivo Python de ejecución / lanzamiento de la plataforma Flask.
* **jupyter_notebook_config.py**: Archivo de configuración de Jupyter Notebook necesario para el correcto funcionamiento de Jupyter ejecutado en el contenedor Docker desde el que es ejecutada la plataforma.
* **requirements.txt** Archivo de dependencias software de la plataforma instaladas en el montaje del contenedor Docker.

### Acceso a la plataforma
**Se recomienda la lectura de la memoria y los manuales del profesor y el alumno encontrados en los anexos como paso previo al manejo de la plataforma.**

La plataforma desarrollada en este TFG se encuentra accesible a través de la URL: http://3.89.140.10/ .
En esta han sido definidas de forma incial 5 cuentas de profesores cuyas credenciales de acceso son las siguientes:

| Profesor          | Nombre de Usuario    | Contraseña  |
|-------------------|----------------------|-------------|
| Web Teacher 1     | wt001                | teacher     |
| Web Teacher 2     | wt002                | teacher     |
| Web Teacher 3     | wt003                | teacher     |
| Web Teacher 4     | wt004                | teacher     |
| Web Teacher 5     | wt005                | teacher     |

La plataforma en el **estado inicial en el que se encuentra en este repósitorio** preparada para su despliegue únicamente contiene estas 5 cuentas en Base de Datos sin ningún otro contenido.

La contraseña de la **instancia de ejecución de Jupyter Notebook accesible desde la plataforma** es también la palabra **teacher**.

De forma adicional, tras el despliegue de la plataforma ha sido añadido el pequeño **Curso Introductorio a Python** desarrollado tambíen en este proyecto cuyos contenidos se pueden encontrar dentro de la carpeta **Curso-Python**. Este curso ha sido introducido por el **Web Teacher 1** junto con una serie de **alumnos ficticios** creados por el mismo y registrados en este curso. Estos alumnos son:

| Alumno            | Nombre de Usuario    | Contraseña  |
|-------------------|----------------------|-------------|
| Pablo Gómez     | pg103                | 0000     |
| Sofía Tomé     | st124              | 0000     |
| Laura Merino     | lm231                | 0000     |
| Paula Gil     | pg891                | 0000     |
| Ramón López    | rl201                | 0000     |
| Alberto Sierra     | as129                | 0000     |
| Pedro Castro     | pc235                | 0000     |

Para la representación de la plataforma en un estado funcional **han sido realizadas algunas entregas de tareas** por parte de estos alumnos, visualizables desde los apartados de Calificaciones de estos o del Web Teacher1.

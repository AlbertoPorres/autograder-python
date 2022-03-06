# Búsqueda de Herramientas para el Proyecto

El primer paso con el que comenzar el proyecto es la selección de las herramientas que se utilizarán en el desarrollo de este las cuales serán, por un lado, el curso de Python
del que se extraerán los contenidos y, por otro lado, el autograder para Python con el que se crearán las actividades autocorregibles que el alumnó deberá resolver.

## Búsqueda de Autograder
### Herramientas encontradas:
---
**CodeGrade:** Esta es una aplicación de aprendizaje diseñara específicamente para la enseñanza de lenguajes de programación,
haciendo que la calificación y entrega de ejercicios sea más efectiva para los estudiantes y más eficaz para los profesores,
proporcionando un entorno en línea diseñado específicamente para cubrir las necesidades de la educación de la programación moderna.

A diferencia con la mayoría de cursos y herramientas para el aprendizaje de lenguajes de programación, en las que los ejercicios 
son revisados de forma clásica y poco intuitiva, CodeGrade crea un entorno intuitivo para la revisión de ejercicios de programación.
Las características más interesantes que CodeGrade nos ofrece son las siguientes:
- Rúbricas fáciles de usar para ayudar a calificar los trabajos de forma rápida y coherente.
- Sistema de entrega de archivos el cual permite a estudiantes y profesores acceder y corregir los envíos de forma local sin sobrecarga.
- Feedback linea a linea.
- Fácil e intuitiva creación de tareas de programación para los alumnos.

CodeGrade combina todos estos elementos dentro de un ambiente onine cuidadosamente diseñado para adarparse a las necesidades de la
enseñanza con otras funcionalidades útiles. 

*Documentación:* https://docs.codegra.de/

---
**CodingRooms:** Este es una plataforma de creación de cursos online, similar a CodeGrade, orientada a la enseñanza de lenguajes de programación.
Ofrece un ambiente en tiempo real en el que los instructores pueden ver todo el código de sus estudiantes a través de tableros interactivos combinandolo 
con la posibilidad de crear sesiones en directo o previamente grabadas por parte de los profesores para impartir los contenidos.

La principal y más atractiva característica de CodingRooms es la capacidad de creación de tareas autocalificables para los alumnos dentro de 
un curso. Con respecto al resto de características y funcionalidades, estas son muy similares a las ya listadas para CodeGrade.

*Documentación:* https://www.codingrooms.com/

---
**Otter-Grader:** Este es un autocalificador ligero y modular de código abierto diseñado para calificar tareas de Python y R para clases a cualquier escala, abstrayendo el funcionamiento interno del autograder, haciendolo así compatible con la distribución de tareas de cualquier instructor.

Otter soporta calificación local a través de contenedores Docker paralelos, calificando mediante el uso de plataformas de autocalificación de terceros (LMSs), la maquina del instructor y un paquete cliente que permite a los alumnos e instructores comprobar y calificar las tareas. Este está diseñado para calificar ejecutables Python y R, Jypyter Notebooks y documentos RMarkdown, y es compatible con diferentes LMSs como Canvas y Gradescope.

*Documentación:* https://otter-grader.readthedocs.io/en/latest/

---
### Elección de Autograder:
En la sección anterior se han descrito diferentes herramientas actualmente utilizadas para la creación de actividades autocorregibles, orientadas a la enseñanza de lenguajes de programación. CodeGrade y CodingRooms son dos herramientas muy similares centradas en la creación de cursos dentro de un ambiente web, esto hace que no sea posible la creación de las actividades de forma externa a su plataforma; es esta dependencia la que ha llevado a la decisión de utilizar el paquete de Python, **Otter-Grader** para el desarrollo de las actividades autocorregibles durante la realización de este proyecto.

## Selección del Curso de Python:
Los contenidos del curso que se desarrollará en este proyecto serán extraidos de un curso de Python ya existente, el curso elegido para este fin es la guía audivisual de Python  publicada por el canal de YouTube de **pildorasinformaticas** (https://www.youtube.com/c/pildorasinformaticas), esta consta de al rededor de 70 lecciones individuales dedicadas a la enseñanza de las principales y más importantes características del lenguaje de programación Python.

*Documentación:* https://www.youtube.com/playlist?list=PLU8oAlHdN5BlvPxziopYZRd55pdqFwkeS


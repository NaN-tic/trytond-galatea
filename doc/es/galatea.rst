=======
Galatea
=======

Galatea es el nombre que se le ha dado a la plataforma web de su ERP. 

A continuación se listara las funcionalidades de la plataforma web que dispone así
como la documentación para sus usuarios.

.. inheritref:: galatea/galatea:section:usuarios

--------
Usuarios
--------

A |menu_galatea_user| dispondrá de los usuarios dados de alta a la plataforma.

Cada usuario dispone de un correo electrónico y una contraseña, que son los dos campos
que se usan para la identificación (el login).

Cada usuario va relacionado con un tercero o un tercero dispone de varios usuarios.

La opción "Gestor" en un usuario le dará acceso a la gestión o visualización de ciertos
contenidos vía web.

Para la identificación de un usuario al sistema deberá rellenar sus datos (correo
y contraseña) en el formulario de identificación: http://www.sudominio.com/es/login

Para finalizar la identificación es recomendable cerrar la sesión. Para cerrar la
sesión accede a http://www.sudominio.com/es/logout

.. important:: Si a la configuración global está desactivado el login, no dispondrá
              de esta sección.

.. inheritref:: galatea/galatea:section:alta_usuario

Alta de un usuario
------------------

Si damos de alta un usuario un usuario en el sistema, este usuario es dado de alta
y ya se puede identificar (login).

Si un usuario es dado de alta con la plataforma web, el usuario deberá seguir los pasos:

* Rellenar el formulario de alta. Accede a http://www.sudominio.com/es/registration
  para acceder al formulario de registro y completa los campos (nombre, correo, password).
  Si a la configuración global se requiere el CIF/NIF, se le pedirá también este campo para
  la alta. Antes de dar de alta se verifica que el correo electronico y password sean correctos,
  como el CIF/NIF en el caso que sea obligatorio.
  Si ya existe un tercero que en sus medios de contacto disponga de este correo electrónico,
  el usuario irá relacionado con este tercero. En caso contrario, se creará un nuevo tercero.
* Se enviará un correo al usuario en el correo electrónico que ha introducido. Todavía no está
  activa su cuenta ya que deberá hacer clic en el link que encontrará en el correo. Este link
  le activará la cuenta. En caso contrario, su cuenta no estará activa.

En el caso que el usuario no ha activado su cuenta y desee activarla, simplemente le podéis
cambiar la contraseña y su cuenta estará activada (recuerden de informar al usuario de su nueva
contraseña).

.. important:: Si a la configuración global está desactivado el registro o alta
              de usuarios, no dispondrá de esta sección.

.. inheritref:: galatea/galatea:section:eliminar_usuario

Eliminar un usuario
-------------------

Puede eliminar un usuario del mismo modo que eliminar cualquier registro, con el botón
de eliminar. Ahora bien, antes de eliminar usuarios, os recomendamos que los desactiven.
De este modo siempre que desean dar de alta otra vez simplemente lo pueden volver activar.

Eliminar un usuario no eliminará el Tercero, pues este, ya puede que esté relacionado con
otras secciones, como ventas, albaranes, facturas, proyectos, etc...

.. inheritref:: galatea/galatea:section:recordar_contrasena

Recordar la contraseña
----------------------

La contraseña del usuario no la podemos saber ya que se encuentra encriptada. El único
modo de saber una contraseña es modificar la contraseña del usuario por una de nueva.

Para el usuario poder cambiar la contraseña puede acceder a http://www.sudominio.com/es/reset-password
para introducir su correo. Se enviará un correo electrónico con una nueva dirección
para que reiniciar su cuenta con su nueva contraseña.

.. inheritref:: galatea/galatea:section:cambiar_contrasena

Cambiar la contraseña
---------------------

Una vez un usuario ha iniciado sesión (login), podrá cambiar la contraseña si lo desea a
http://www.sudominio.com/es/new-password

.. |menu_galatea_user| tryref:: galatea.menu_galatea_user/complete_name

.. inheritref:: galatea/galatea:section:ficheros_estaticos

------------------
Ficheros estáticos
------------------

Si necesita publicar ficheros en su site (imagenes, pdf,...) con el sistema de ficheros
estáticos podrá activar que estos ficheros esten disponibles.

A |menu_galatea_static| dispone de la gestión de ficheros:

* Directorios: Organize la publicación de ficheros en directorios (físicos)
* Ficheros. Si son ficheros locales, van relacionados con un directorio.

Para acceder a los ficheros la direcció es http://www.midominio.com/file/nombre-del-fichero.pdf

También puede usar esta url para disponer de los ficheros que haya adjuntado con los registros.
(a la configuración global se configura que modelos se permite la descarga de ficheros).

.. important:: Es importante que los nombres de los fichero usar los carácteres az09- y evitar
              el uso de espacios y accentos y mejor siempre usar todo en minúscula.

.. |menu_galatea_static| tryref:: galatea.menu_galatea_static/complete_name

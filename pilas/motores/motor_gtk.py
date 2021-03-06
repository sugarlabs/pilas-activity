# -*- encoding: utf-8 -*-
# pilas engine - a video game framework.
#
# copyright 2015 - Cristian García
# license: lgplv3 (see http://www.gnu.org/licenses/lgpl.html)
#
# website - http://www.pilas-engine.com.ar

import os
import sys
import copy

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GdkPixbuf

import motor
from pilas import imagenes
from pilas import actores
from pilas import eventos
from pilas import utils
from pilas import depurador

from pilas import fps
from pilas import simbolos
from pilas import colores


class BaseActor(object):

    def __init__(self):
        self._rotacion = 0
        self._transparencia = 0
        self.centro_x = 0
        self.centro_y = 0
        self._escala_x = 1
        self._escala_y = 1
        self._espejado = False
        self.fijo = 0

    def definir_centro(self, x, y):
        self.centro_x = x
        self.centro_y = y

    def obtener_posicion(self):
        return self.x, self.y

    def definir_posicion(self, x, y):
        self.x, self.y = x, y

    def obtener_escala(self):
        return self._escala_x

    def definir_escala(self, s):
        self._escala_x = s
        self._escala_y = s

    def definir_escala_x(self, s):
        self._escala_x = s

    def definir_escala_y(self, s):
        self._escala_y = s

    def definir_transparencia(self, nuevo_valor):
        self._transparencia = nuevo_valor

    def obtener_transparencia(self):
        return self._transparencia

    def obtener_rotacion(self):
        return self._rotacion

    def definir_rotacion(self, r):
        self._rotacion = r

    def set_espejado(self, espejado):
        self._espejado = espejado


class GtkImagen(object):

    def __init__(self, ruta):
        self.ruta_original = ruta
        self._imagen = GdkPixbuf.Pixbuf.new_from_file(ruta)

    def ancho(self):
        return self._imagen.get_width()

    def alto(self):
        return self._imagen.get_height()

    def centro(self):
        "Retorna una tupla con la coordenada del punto medio del la imagen."
        return (self.ancho() / 2, self.alto() / 2)

    def avanzar(self):
        pass

    def dibujar(self, motor, x, y, dx=0, dy=0, escala_x=1, escala_y=1, rotacion=0, transparencia=0):
        """Dibuja la imagen sobre la ventana que muestra el motor.

           x, y: indican la posicion dentro del mundo.
           dx, dy: es el punto centro de la imagen (importante para rotaciones).
           escala_x, escala_yindican cambio de tamano (1 significa normal).
           rotacion: angulo de inclinacion en sentido de las agujas del reloj.
        """

        motor.context.save()
        centro_x, centro_y = motor.centro_fisico()

        motor.context.translate(x + centro_x, centro_y - y)
        motor.context.rotate(rotacion)
        motor.context.scale(escala_x, escala_y)

        #if transparencia:
        #    motor.context.setOpacity(1 - transparencia/100.0)

        self._dibujar_pixmap(motor.context, -dx, -dy)
        motor.context.restore()

    def _dibujar_pixmap(self, context, x, y):
        Gdk.cairo_set_source_pixbuf(context, self._imagen, self._image.width(), self._image.height())

    def __str__(self):
        nombre_imagen = os.path.basename(self.ruta_original)
        return "<Imagen del archivo '%s'>" %(nombre_imagen)


class GtkGrilla(GtkImagen):

    """Representa una grilla regular, que se utiliza en animaciones.

       La grilla regular se tiene que crear indicando la cantidad
       de filas y columnas. Una vez definida se puede usar como
       una imagen normal, solo que tiene dos metodos adicionales
       para ``definir_cuadro`` y ``avanzar`` el cuadro actual.
    """

    def __init__(self, ruta, columnas=1, filas=1):
        GtkImagen.__init__(self, ruta)

        self.cantidad_de_cuadros = columnas * filas
        self.columnas = columnas
        self.filas = filas
        self.cuadro_ancho = GtkImagen.ancho(self) / columnas
        self.cuadro_alto = GtkImagen.alto(self) / filas
        self.definir_cuadro(0)

    def ancho(self):
        return self.cuadro_ancho

    def alto(self):
        return self.cuadro_alto

    def _dibujar_pixmap(self, motor, x, y):
        Gdk.cairo_set_source_pixbuf(context, self._imagen, self._image.width(), self._image.height())
        #motor.context.drawPixmap(x, y, self._imagen, self.dx, self.dy,
        #        self.cuadro_ancho, self.cuadro_alto)

    def definir_cuadro(self, cuadro):
        self._cuadro = cuadro

        frame_col = cuadro % self.columnas
        frame_row = cuadro / self.columnas

        self.dx = frame_col * self.cuadro_ancho
        self.dy = frame_row * self.cuadro_alto

    def avanzar(self):
        ha_reiniciado = False
        cuadro_actual = self._cuadro + 1

        if cuadro_actual >= self.cantidad_de_cuadros:
            cuadro_actual = 0
            ha_reiniciado = True

        self.definir_cuadro(cuadro_actual)
        return ha_reiniciado

    def obtener_cuadro(self):
        return self._cuadro

    def dibujarse_sobre_una_pizarra(self, pizarra, x, y):
        pizarra.pintar_parte_de_imagen(self, self.dx, self.dy, self.cuadro_ancho, self.cuadro_alto, x, y)


class GtkTexto(GtkImagen):

    def __init__(self, texto, magnitud, motor):
        self._ancho, self._alto = motor.obtener_area_de_texto(texto, magnitud)

    def _dibujar_pixmap(self, motor, dx, dy):
        nombre_de_fuente = motor.context.get_font_face()
        tamano = 12
        r, g, b, a = self.color.obtener_componentes()

        motor.context.set_font_face(nombre_de_fuente)
        motor.context.set_font_size(tamano)
        motor.context.set_source_rgb(r, g, b)

        lines = self.texto.split('\n')

        for line in lines:
            extents = motor.context.text_extents(line)
            motor.context.show_text(dx, dy + self._alto, line)
            dy += extents.height()

    def ancho(self):
        return self._ancho

    def alto(self):
        return self._alto


class GtkLienzo(GtkImagen):

    def __init__(self):
        pass

    def texto(self, motor, cadena, x=0, y=0, magnitud=10, fuente=None, color=colores.negro):
        "Imprime un texto respespetando el desplazamiento de la camara."
        self.texto_absoluto(motor, cadena, x, y, magnitud, fuente, color)

    def texto_absoluto(self, motor, cadena, x=0, y=0, magnitud=10, fuente=None, color=colores.negro):
        "Imprime un texto sin respetar al camara."
        x, y = utils.hacer_coordenada_pantalla_absoluta(x, y)

        r, g, b, a = color.obtener_componentes()
        motor.context.set_source_rgb(r, g, b)

        if not fuente:
            fuente = motor.context.get_font_face()

        motor.context.set_font_face(fuente)
        motor.context.set_font_size(magnitud)
        motor.context.show_text(x, y, cadena)

    def pintar(self, motor, color):
        r, g, b, a = color.obtener_componentes()
        ancho, alto = motor.obtener_area()
        context.set_source_rgb(r, g, b)
        motor.context.rectangle(0, 0, ancho, alto)

    def linea(self, motor, x0, y0, x1, y1, color=colores.negro, grosor=1):
        x0, y0 = utils.hacer_coordenada_pantalla_absoluta(x0, y0)
        x1, y1 = utils.hacer_coordenada_pantalla_absoluta(x1, y1)

        r, g, b, a = color.obtener_componentes()

        motor.context.set_source_rgb(r, g, b)
        motor.context.set_line_width(grosor)
        motor.context.move_to(x0, y0)
        motor.context.line_to(x1, y1)
        motor.context.stroke()

    def poligono(self, motor, puntos, color=colores.negro, grosor=1, cerrado=False):
        x, y = puntos[0]
        if cerrado:
            puntos.append((x, y))

        for p in puntos[1:]:
            nuevo_x, nuevo_y = p
            self.linea(motor, x, y, nuevo_x, nuevo_y, color, grosor)
            x, y = nuevo_x, nuevo_y

    def cruz(self, motor, x, y, color=colores.negro, grosor=1):
        t = 3
        self.linea(motor, x - t, y - t, x + t, y + t, color, grosor)
        self.linea(motor, x + t, y - t, x - t, y + t, color, grosor)

    def circulo(self, motor, x, y, radio, color=colores.negro, grosor=1):
        x, y = utils.hacer_coordenada_pantalla_absoluta(x, y)
        r, g, b, a = color.obtener_componentes()

        motor.context.set_source_rgb(r, g, b)
        motor.context.set_line_width(grosor)

        motor.context.arc(x -radio, y - radio, radio * 2, radio * 2)
        motor.stroke()

    def rectangulo(self, motor, x, y, ancho, alto, color=colores.negro, grosor=1):
        x, y = utils.hacer_coordenada_pantalla_absoluta(x, y)
        r, g, b, a = color.obtener_componentes()

        motor.context.set_source_rgb(r, g, b)
        motor.context.set_line_width(grosor)
        motor.context.rectangle(x, y, ancho, alto)
        motor.context.stroke()


class GtkSuperficie(GtkImagen):

    def __init__(self, ancho, alto):
        self.ancho = ancho
        self.alto = alto

    def pintar(self, color):
        r, g, b, a = color.obtener_componentes()
        self._imagen.fill(QtGui.QColor(r, g, b, a))

    def pintar_parte_de_imagen(self, imagen, origen_x, origen_y, ancho, alto, x, y):
        #self.canvas.begin(self._imagen)
        #self.canvas.drawPixmap(x, y, imagen._imagen, origen_x, origen_y, ancho, alto)
        #self.canvas.end()
        pass

    def pintar_imagen(self, imagen, x=0, y=0):
        self.pintar_parte_de_imagen(imagen, 0, 0, imagen.ancho(), imagen.alto(), x, y)

    def texto(self, cadena, x=0, y=0, magnitud=10, fuente=None, color=colores.negro):
        self.canvas.begin(self._imagen)
        r, g, b, a = color.obtener_componentes()
        self.canvas.setPen(QtGui.QColor(r, g, b))
        dx = x
        dy = y

        if not fuente:
            fuente = self.canvas.font().family()

        font = QtGui.QFont(fuente, magnitud)
        self.canvas.setFont(font)
        metrica = QtGui.QFontMetrics(font)

        for line in cadena.split('\n'):
            self.canvas.drawText(dx, dy, line)
            dy += metrica.height()

        self.canvas.end()

    def circulo(self, x, y, radio, color=colores.negro, relleno=False, grosor=1):
        self.canvas.begin(self._imagen)

        r, g, b, a = color.obtener_componentes()
        color = QtGui.QColor(r, g, b)
        pen = QtGui.QPen(color, grosor)
        self.canvas.setPen(pen)

        if relleno:
            self.canvas.setBrush(color)

        self.canvas.drawEllipse(x -radio, y-radio, radio*2, radio*2)
        self.canvas.end()

    def rectangulo(self, x, y, ancho, alto, color=colores.negro, relleno=False, grosor=1):
        self.canvas.begin(self._imagen)

        r, g, b, a = color.obtener_componentes()
        color = QtGui.QColor(r, g, b)
        pen = QtGui.QPen(color, grosor)
        self.canvas.setPen(pen)

        if relleno:
            self.canvas.setBrush(color)

        self.canvas.drawRect(x, y, ancho, alto)
        self.canvas.end()

    def linea(self, x, y, x2, y2, color=colores.negro, grosor=1):
        self.canvas.begin(self._imagen)

        r, g, b, a = color.obtener_componentes()
        color = QtGui.QColor(r, g, b)
        pen = QtGui.QPen(color, grosor)
        self.canvas.setPen(pen)

        self.canvas.drawLine(x, y, x2, y2)
        self.canvas.end()

    def poligono(self, puntos, color, grosor, cerrado=False):
        x, y = puntos[0]

        if cerrado:
            puntos.append((x, y))

        for p in puntos[1:]:
            nuevo_x, nuevo_y = p
            self.linea(x, y, nuevo_x, nuevo_y, color, grosor)
            x, y = nuevo_x, nuevo_y

    def dibujar_punto(self, x, y, color=colores.negro):
        self.circulo(x, y, 3, color=color, relleno=True)

    def limpiar(self):
        self._imagen.fill(QtGui.QColor(0, 0, 0, 0))


class GtkActor(BaseActor):

    def __init__(self, imagen="sin_imagen.png", x=0, y=0):

        if isinstance(imagen, str):
            self.imagen = imagenes.cargar(imagen)
        else:
            self.imagen = imagen

        self.x = x
        self.y = y
        BaseActor.__init__(self)

    def definir_imagen(self, imagen):
        # permite que varios actores usen la misma grilla.
        if isinstance(imagen, GtkGrilla):
            self.imagen = copy.copy(imagen)
        else:
            self.imagen = imagen

    def obtener_imagen(self):
        return self.imagen

    def dibujar(self, motor):
        escala_x, escala_y = self._escala_x, self._escala_y

        if self._espejado:
            escala_x *= -1

        if not self.fijo:
            x = self.x - motor.camara_x
            y = self.y - motor.camara_y
        else:
            x = self.x
            y = self.y

        self.imagen.dibujar(motor, x, y,
                self.centro_x, self.centro_y,
                escala_x, escala_y, self._rotacion, self._transparencia)


class GtkSonido:

    def __init__(self, ruta):
        try:
            import pygame
            pygame.mixer.init()
            self.sonido = pygame.mixer.Sound(ruta)

        except (ImportError, pygame.error):
            self.sonido = None

    def reproducir(self):
        if self.sonido != None:
            self.sonido.play()


class GtkBase(motor.Motor):

    def __init__(self):
        motor.Motor.__init__(self)

        self.box = Gtk.VBox()
        self.add(self.box)

        self.canvas = Gtk.DrawingArea()
        self.canvas.add_events(Gdk.EventMask.POINTER_MOTION_MASK)
        self.canvas.connect("draw", self.paintEvent)
        self.box.pack_start(self.canvas, True, True, 0)

        self.fps = fps.FPS(60, True)
        self.pausa_habilitada = False

        self.depurador = depurador.Depurador(self.obtener_lienzo(), self.fps)
        self.mouse_x = 0
        self.mouse_y = 0
        self.camara_x = 0
        self.camara_y = 0

        self.__fullscreen = False

    def iniciar_ventana(self, ancho, alto, titulo, pantalla_completa):
        self.ancho = ancho
        self.alto = alto
        self.ancho_original = ancho
        self.alto_original = alto
        self.titulo = titulo
        self.__fullscreen = pantalla_completa
        self.centrar_ventana()

        if pantalla_completa:
            self.fullscreen()

        else:
            self.show()

        # Activa la invocacion al evento timerEvent.
        #self.startTimer(1000 / 60.0)

    def pantalla_completa(self):
        self.__fullscreen = True
        self.fullscreen()

    def pantalla_modo_ventana(self):
        self.__fullscreen = False
        self.unfullscreen()

    def esta_en_pantalla_completa(self):
        return self.__fullscreen

    def alternar_pantalla_completa(self):
        """Permite cambiar el modo de video.

        Si está en modo ventana, pasa a pantalla completa y viceversa.
        """
        if self.esta_en_pantalla_completa():
            self.pantalla_modo_ventana()

        else:
            self.pantalla_completa()

    def centro_fisico(self):
        "Centro de la ventana para situar el punto (0, 0)"
        return self.ancho_original / 2, self.alto_original / 2

    def obtener_area(self):
        return (self.ancho_original, self.alto_original)

    def centrar_ventana(self):
        ancho_escritorio = Gdk.Screen.width()
        alto_escritorio = Gdk.Screen.height()
        #self.setGeometry((escritorio.width() - self.ancho) / 2, (escritorio.height() - self.alto) / 2, self.ancho, self.alto)

    def obtener_actor(self, imagen, x, y):
        return GtkActor(imagen, x, y)

    def obtener_texto(self, texto, magnitud):
        return GtkTexto(texto, magnitud, self)

    def obtener_grilla(self, ruta, columnas, filas):
        return GtkGrilla(ruta, columnas, filas)

    def actualizar_pantalla(self):
        self.ventana.update()

    def definir_centro_de_la_camara(self, x, y):
        self.camara_x = x
        self.camara_y = y

    def obtener_centro_de_la_camara(self):
        return (self.camara_x, self.camara_y)

    def cargar_sonido(self, ruta):
        return GtkSonido(ruta)

    def cargar_imagen(self, ruta):
        return GtkImagen(ruta)

    def obtener_lienzo(self):
        return GtkLienzo()

    def obtener_superficie(self, ancho, alto):
        return GtkSuperficie(ancho, alto)

    def ejecutar_bucle_principal(self, mundo, ignorar_errores):
        #sys.exit(self.app.exec_())
        pass

    def paintEvent(self, area, context):
        print("DRAW")
        self.context = context

        self.context.set_source_rgb(1, 1, 1)
        self.context.rectangle(0, 0, self.alto * self.ancho_original / self.alto_original, self.alto)
        self.context.fill()

        alto = self.alto / float(self.alto_original)
        self.context.scale(alto, alto)

        self.depurador.comienza_dibujado(self)

        for actor in actores.todos:
            try:
                actor.dibujar(self)

            except Exception as e:
                actor.eliminar()

            self.depurador.dibuja_al_actor(self, actor)

        self.depurador.termina_dibujado(self)

        return False

    def timerEvent(self, event):

        if not self.pausa_habilitada:
            try:
                self.realizar_actualizacion_logica()
            except Exception as e:
                print e

        # Invoca el dibujado de la pantalla.
        self.update()


    def realizar_actualizacion_logica(self):
        for x in range(self.fps.actualizar()):
            if not self.pausa_habilitada:
                eventos.actualizar.send("Qt::timerEvent")

                for actor in actores.todos:
                    actor.pre_actualizar()
                    actor.actualizar()

    def resizeEvent(self, event):
        self.ancho = event.size().width()
        self.alto = event.size().height()

    def mousePressEvent(self, e):
        escala = self.escala()
        x, y = utils.convertir_de_posicion_fisica_relativa(e.pos().x()/escala, e.pos().y()/escala)
        eventos.click_de_mouse.send("Qt::mousePressEvent", x=x, y=y, dx=0, dy=0)

    def mouseReleaseEvent(self, e):
        escala = self.escala()
        x, y = utils.convertir_de_posicion_fisica_relativa(e.pos().x()/escala, e.pos().y()/escala)
        eventos.termina_click.send("Qt::mouseReleaseEvent", x=x, y=y, dx=0, dy=0)

    def wheelEvent(self, e):
        eventos.mueve_rueda.send("ejecutar", delta=e.delta() / 120)

    def mouseMoveEvent(self, e):
        escala = self.escala()
        x, y = utils.convertir_de_posicion_fisica_relativa(e.pos().x()/escala, e.pos().y()/escala)
        dx, dy = x - self.mouse_x, y - self.mouse_y
        eventos.mueve_mouse.send("Qt::mouseMoveEvent", x=x, y=y, dx=dx, dy=dy)
        self.mouse_x = x
        self.mouse_y = y

    def keyPressEvent(self, event):
        codigo_de_tecla = self.obtener_codigo_de_tecla_normalizado(event.key())

        if event.key() == QtCore.Qt.Key_Escape:
            eventos.pulsa_tecla_escape.send("Qt::keyPressEvent")
        if event.key() == QtCore.Qt.Key_P:
            self.alternar_pausa()
        if event.key() == QtCore.Qt.Key_F:
            self.alternar_pantalla_completa()

        eventos.pulsa_tecla.send("Qt::keyPressEvent", codigo=codigo_de_tecla, texto=event.text())

    def keyReleaseEvent(self, event):
        codigo_de_tecla = self.obtener_codigo_de_tecla_normalizado(event.key())
        eventos.suelta_tecla.send("Qt::keyReleaseEvent", codigo=codigo_de_tecla, texto=event.text())

    def obtener_codigo_de_tecla_normalizado(self, tecla_qt):
        teclas = {
            QtCore.Qt.Key_Left: simbolos.IZQUIERDA,
            QtCore.Qt.Key_Right: simbolos.DERECHA,
            QtCore.Qt.Key_Up: simbolos.ARRIBA,
            QtCore.Qt.Key_Down: simbolos.ABAJO,
            QtCore.Qt.Key_Space: simbolos.SELECCION,
            QtCore.Qt.Key_Return: simbolos.SELECCION,
            QtCore.Qt.Key_F1: simbolos.F1,
            QtCore.Qt.Key_F2: simbolos.F2,
            QtCore.Qt.Key_F3: simbolos.F3,
            QtCore.Qt.Key_F4: simbolos.F4,
            QtCore.Qt.Key_F5: simbolos.F5,
            QtCore.Qt.Key_F6: simbolos.F6,
            QtCore.Qt.Key_F7: simbolos.F7,
            QtCore.Qt.Key_F8: simbolos.F8,
            QtCore.Qt.Key_F9: simbolos.F9,
            QtCore.Qt.Key_F10: simbolos.F10,
            QtCore.Qt.Key_F11: simbolos.F11,
            QtCore.Qt.Key_F12: simbolos.F12,
        }

        if teclas.has_key(tecla_qt):
            return teclas[tecla_qt]
        else:
            return tecla_qt

    def escala(self):
        "Obtiene la proporcion de cambio de escala de la pantalla"
        return self.alto / float(self.alto_original)

    def obtener_area_de_texto(self, texto, magnitud=10):
        ancho = 0
        alto = 0

        fuente = QtGui.QFont()
        fuente.setPointSize(magnitud)
        metrica = QtGui.QFontMetrics(fuente)

        lineas = texto.split('\n')

        for linea in lineas:
            ancho = max(ancho, metrica.width(linea))
            alto += metrica.height()

        return ancho, alto

    def alternar_pausa(self):
        if self.pausa_habilitada:
            self.pausa_habilitada = False
            self.actor_pausa.eliminar()
        else:
            self.pausa_habilitada = True
            self.actor_pausa = actores.Pausa()

    def ocultar_puntero_del_mouse(self):
        bitmap = QtGui.QBitmap(1, 1)
        nuevo_cursor = QtGui.QCursor(bitmap, bitmap)
        self.setCursor(QtGui.QCursor(nuevo_cursor))


class GtkMotor(GtkBase, Gtk.Window):

    def __init__(self):
        GtkBase.__init__(self)
        Gtk.Window.__init__(self)


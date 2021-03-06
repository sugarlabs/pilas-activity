# Copyright 2009 Simon Schampijer
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

"""Pilas Activity.  Live interpreter to learn programming with games."""

import os
import sys
import copy
import logging
import subprocess

from gettext import gettext as _

from gi.repository import Gtk
from gi.repository import Gdk

import pilas
from pilas.motores.motor_activity import ActivityBase
from pilas.console import console_widget


class PilasActivity(ActivityBase):
    """Pilas class as specified in activity.info"""

    def __init__(self, handle):
        """Set up the Pilas activity."""
        ActivityBase.__init__(self, handle)

        # we do not have collaboration features,
        # make the share option insensitive
        self.max_participants = 1

        # Pilas
        pilas.iniciar(motor=self)

        #Crear actor
        self.mono = pilas.actores.Mono()
        self.mono.x = self.ancho / 2 - self.mono.imagen.ancho() / 4
        self.mono.y = 0 + self.mono.imagen.alto() / 2
        pilas.eventos.click_de_mouse.conectar(self.sonreir)

        # Agrega la Consola
        locals = {'pilas': pilas, 'mono': self.mono, 'self': self}
        self.consoleWidget = console_widget.ConsoleWidget(locals)
        self.consoleWidget.set_size_request(1, 200)
        self.layout.pack_end(self.consoleWidget, False, False, 0)

        self.show_all()

    def sonreir(self, evento):
        self.mono.sonreir()


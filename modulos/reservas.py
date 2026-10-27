# -*- coding: utf-8 -*-
"""
Modulo: Reservas - CRUD Completo
Crear, Leer, Actualizar y Eliminar reservas.
Incluye dialogo personalizado para alta/edicion y confirmaciones para borrado.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFormLayout, QLineEdit, QComboBox, QPushButton,
    QCheckBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QFrame, QDateEdit, QTimeEdit,
    QAbstractItemView, QDialog, QDialogButtonBox,
    QGroupBox, QScrollArea, QProgressBar
)
from PySide6.QtCore import Qt, QDate, QTime, Signal
from PySide6.QtGui import QFont, QColor, QIntValidator

from modulos.buscador_cliente import BuscadorCliente, BuscadorMesa
from modulos import almacen_datos
from modulos.almacen_configuracion import almacen_config
from modulos.hilos import HiloLimpiarReservas

PRIMARIO = "#1B3A5C"
SECUNDARIO = "#2C5F8A"
DORADO = "#D4A843"
VERDE = "#4CAF50"
ROJO = "#BC1515"
NARANJA = "#FF9800"
GRIS = "#9E9E9E"
NEUTRO_CLARO = "#F5F5F5"


# ============================================================
# Dialogo para crear o editar una reserva
# ============================================================
class DialogoReserva(QDialog):
    """
    Dialogo modal para crear o editar una reserva.
    Retorna un diccionario con los datos si el usuario acepta, None si cancela.
    """
    def __init__(self, parent=None, datos=None):
        """
        parent: widget padre
        datos: diccionario con datos existentes (para editar) o None (para crear)
        """
        super().__init__(parent)
        self.datos = datos
        self.setWindowTitle("Editar Reserva" if datos else "Nueva Reserva")
        self.setMinimumWidth(420)
        self.setMinimumHeight(480)

        # Bloquear redimensionamiento vertical excesivo
        self.setMaximumHeight(550)

        self._construir_formulario()

    def _construir_formulario(self):
        # Parametros de configuracion (max personas y duracion estandar)
        # Se leen desde configuracion_general para que el formulario respete
        # lo configurado en el modulo de Configuracion.
        parametros = almacen_config.obtener_parametros()
        try:
            self.max_personas = int(parametros.get("max_personas") or 20)
        except (TypeError, ValueError):
            self.max_personas = 20
        try:
            self.duracion_min = int(parametros.get("duracion") or 90)
        except (TypeError, ValueError):
            self.duracion_min = 90
        try:
            self.tolerancia_min = int(parametros.get("tolerancia") or 0)
        except (TypeError, ValueError):
            self.tolerancia_min = 0
        if self.max_personas < 1:
            self.max_personas = 1

        # Limites de anticipacion por zona, horarios de atencion y festivos
        # (tomados de configuracion_general y horarios_atencion en la BD)
        self.dias_estandar = almacen_config.obtener_dias_estandar()
        self.limites_zonas = almacen_config.obtener_limites_anticipacion()
        self.horarios = {h["dia"]: h for h in almacen_config.obtener_horarios()}
        self.festivos = almacen_config.obtener_festivos()
        self._nota_deposito = ""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        # Titulo del dialogo
        titulo = "Editar Reserva" if self.datos else "Nueva Reserva"
        lbl_titulo = QLabel(titulo)
        lbl_titulo.setStyleSheet(f"""
            font-size: 18px;
            font-weight: 700;
            color: {PRIMARIO};
            padding-bottom: 4px;
        """)
        layout.addWidget(lbl_titulo)

        separador = QFrame()
        separador.setFrameShape(QFrame.Shape.HLine)
        separador.setStyleSheet(f"background-color: {DORADO}; max-height: 2px;")
        layout.addWidget(separador)

        # Scroll por si el formulario es largo
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        formulario = QWidget()
        form = QFormLayout(formulario)
        form.setSpacing(10)
        form.setContentsMargins(0, 8, 0, 8)

        # --- Selector de cliente (busqueda con autocomplete) ---
        self.buscador_cliente = BuscadorCliente()
        # Cargar clientes desde la fuente unica (almacen central), no duplicados.
        # En produccion esta operacion equivale a: SELECT id, nombre, telefono FROM clientes
        self.buscador_cliente.cargar_clientes([
            (c.get("id"), c.get("nombre"), c.get("telefono"))
            for c in almacen_datos.lista_clientes
        ])
        form.addRow("Cliente:", self.buscador_cliente)

        # --- Fecha ---
        self.date_reserva = QDateEdit()
        self.date_reserva.setDate(QDate.currentDate())
        self.date_reserva.setCalendarPopup(True)
        self.date_reserva.setMinimumDate(QDate.currentDate())
        self.date_reserva.setMinimumHeight(34)
        form.addRow("Fecha:", self.date_reserva)

        # --- Hora inicio ---
        self.time_inicio = QTimeEdit()
        self.time_inicio.setTime(QTime(19, 0))
        self.time_inicio.setDisplayFormat("HH:mm")
        self.time_inicio.setMinimumHeight(34)
        form.addRow("Hora Inicio:", self.time_inicio)

        # --- Hora fin (sugerida = inicio + duracion estandar configurada) ---
        self.time_fin = QTimeEdit()
        self.time_fin.setTime(QTime(19, 0).addSecs(self.duracion_min * 60))
        self.time_fin.setDisplayFormat("HH:mm")
        self.time_fin.setMinimumHeight(34)
        form.addRow("Hora Fin:", self.time_fin)

        # --- Numero de personas ---
        self.txt_personas = QLineEdit()
        self.txt_personas.setPlaceholderText("Ej: 4")
        self.txt_personas.setMaximumWidth(120)
        self.txt_personas.setValidator(QIntValidator(1, self.max_personas))
        self.txt_personas.setMaxLength(len(str(self.max_personas)))
        form.addRow("Personas:", self.txt_personas)

        # --- Mesa ---
        # Buscador con autocomplete (misma UX que el cliente): se escribe y solo
        # se muestran las mesas coincidentes, evitando saturar con la lista completa.
        # Se construye desde el catalogo central MESAS (fuente unica) para que
        # las mesas y sus zonas/capacidades sean siempre correctas.
        self.cmb_mesa = BuscadorMesa([
            f"{m['numero']} - {m['capacidad']}p - {m['zona']}"
            for m in almacen_datos.MESAS
        ])
        form.addRow("Mesa:", self.cmb_mesa)

        # Al cambiar la fecha o la mesa se ajustan los limites del calendario
        # y el rango de horas permitido segun la zona y el dia seleccionados.
        self.date_reserva.dateChanged.connect(self._actualizar_limites_reserva)
        self.cmb_mesa.currentIndexChanged.connect(self._actualizar_limites_reserva)
        self._actualizar_limites_reserva()

        # --- Estado ---
        # Al crear solo P/Confirmada. Al editar, se ofrecen los destinos validos
        # del flujo (Pendiente->Confirmada/Cancelada, Confirmada->Completada/
        # Cancelada); Cancelada y Completada son terminales.
        self.cmb_estado = QComboBox()
        if self.datos:
            estado_actual = self.datos.get("estado", almacen_datos.ESTADO_PENDIENTE)
            destinos = [estado_actual]
            destinos += [
                e for e in almacen_datos.TRANSICIONES_ESTADO.get(estado_actual, [])
                if e != estado_actual
            ]
            self.cmb_estado.addItems(destinos)
        else:
            self.cmb_estado.addItems([
                almacen_datos.ESTADO_PENDIENTE,
                almacen_datos.ESTADO_CONFIRMADA,
            ])
        form.addRow("Estado:", self.cmb_estado)

        # --- Observaciones ---
        self.txt_observaciones = QLineEdit()
        self.txt_observaciones.setPlaceholderText("Opcional...")
        self.txt_observaciones.setMaxLength(255)
        form.addRow("Observaciones:", self.txt_observaciones)

        scroll.setWidget(formulario)
        layout.addWidget(scroll)

        # --- Botones Guardar / Cancelar ( QPushButton normales para mejor estilizado ) ---
        separador2 = QFrame()
        separador2.setFrameShape(QFrame.Shape.HLine)
        separador2.setStyleSheet("background-color: #E0E0E0; max-height: 1px; margin: 8px 0;")
        layout.addWidget(separador2)

        layout_botones_dialogo = QHBoxLayout()
        layout_botones_dialogo.setContentsMargins(0, 8, 0, 0)
        layout_botones_dialogo.addStretch()

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setObjectName("secundario")
        btn_cancelar.setMinimumHeight(40)
        btn_cancelar.setMinimumWidth(130)
        btn_cancelar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancelar.clicked.connect(self.reject)
        layout_botones_dialogo.addWidget(btn_cancelar)

        texto_btn = "Guardar Reserva" if not self.datos else "Actualizar Reserva"
        btn_aceptar = QPushButton(texto_btn)
        btn_aceptar.setObjectName("exito")
        btn_aceptar.setMinimumHeight(40)
        btn_aceptar.setMinimumWidth(160)
        btn_aceptar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_aceptar.clicked.connect(self._validar_y_aceptar)
        layout_botones_dialogo.addWidget(btn_aceptar)

        layout.addLayout(layout_botones_dialogo)

        # Si estamos editando, cargar los datos existentes
        if self.datos:
            self._cargar_datos()

    def _cargar_datos(self):
        """Rellena el formulario con los datos de una reserva existente."""
        d = self.datos

        # Buscar y seleccionar el cliente en el buscador
        nombre_cliente = d.get("cliente", "")
        for c in self.buscador_cliente.clientes:
            if c["nombre"] == nombre_cliente:
                self.buscador_cliente._id_seleccionado = c["id"]
                self.buscador_cliente._nombre_seleccionado = c["nombre"]
                self.buscador_cliente._telefono_seleccionado = c["telefono"]
                self.buscador_cliente.txt_busqueda.setVisible(False)
                texto_sel = f"{c['nombre']}  |  Tel: {c['telefono']}"
                self.buscador_cliente.lbl_seleccionado.setText(texto_sel)
                self.buscador_cliente.lbl_seleccionado.setVisible(True)
                self.buscador_cliente.widget_seleccion.setVisible(True)
                break

        # Fecha
        fecha = d.get("fecha", "")
        if fecha:
            partes = fecha.split("/")
            if len(partes) == 3:
                self.date_reserva.setDate(QDate(int(partes[2]), int(partes[1]), int(partes[0])))

        # Horas
        hora_ini = d.get("hora_inicio", "19:00")
        h, m = map(int, hora_ini.split(":"))
        self.time_inicio.setTime(QTime(h, m))

        hora_fin = d.get("hora_fin", "")
        if hora_fin:
            h, m = map(int, hora_fin.split(":"))
            self.time_fin.setTime(QTime(h, m))
        else:
            self.time_fin.setTime(
                self.time_inicio.time().addSecs(self.duracion_min * 60)
            )

        # Personas
        self.txt_personas.setText(str(d.get("personas", "")))

        # Mesa
        mesa = d.get("mesa", "")
        for i in range(self.cmb_mesa.count()):
            if mesa in self.cmb_mesa.itemText(i):
                self.cmb_mesa.setCurrentIndex(i)
                break

        # Estado
        estado = d.get("estado", "Pendiente")
        idx_estado = self.cmb_estado.findText(estado)
        if idx_estado >= 0:
            self.cmb_estado.setCurrentIndex(idx_estado)

        # Observaciones
        self.txt_observaciones.setText(d.get("observaciones", ""))

    @staticmethod
    def _nombre_dia_semana(day_of_week):
        """1=Lunes ... 7=Domingo -> nombre en espanol (igual a horarios_atencion)."""
        return [
            "Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado", "Domingo"
        ][day_of_week - 1]

    def _zona_de_mesa(self, numero):
        for m in almacen_datos.MESAS:
            if m["numero"] == numero:
                return m["zona"]
        return ""

    def _horario_para_fecha(self, fecha):
        """Horario {apertura, cierre, cerrado} del dia de la fecha, o None."""
        return self.horarios.get(self._nombre_dia_semana(fecha.dayOfWeek()))

    def _max_dias_zona_actual(self):
        """Tope de anticipacion (dias) de la zona de la mesa seleccionada."""
        mesa = self.cmb_mesa.currentText().split(" - ")[0]
        lim = self.limites_zonas.get(self._zona_de_mesa(mesa))
        if lim:
            try:
                return int(lim.get("max_dias") or self.dias_estandar)
            except (TypeError, ValueError):
                pass
        return self.dias_estandar

    def _actualizar_limites_reserva(self):
        """Ajusta la fecha maxima del calendario y el rango de horas
        segun la zona y el dia/festivo seleccionados."""
        try:
            self.date_reserva.blockSignals(True)
            self.date_reserva.setMaximumDate(
                QDate.currentDate().addDays(self._max_dias_zona_actual())
            )
        finally:
            self.date_reserva.blockSignals(False)

        hor = self._horario_para_fecha(self.date_reserva.date())
        if hor and not hor.get("cerrado"):
            min_t = QTime.fromString(str(hor["apertura"]), "HH:mm")
            max_t = QTime.fromString(str(hor["cierre"]), "HH:mm")
            if min_t.isValid() and max_t.isValid() and max_t > min_t:
                self.time_inicio.setMinimumTime(min_t)
                self.time_inicio.setMaximumTime(max_t)
                self.time_fin.setMinimumTime(min_t)
                self.time_fin.setMaximumTime(max_t)
                return
        # Dia cerrado, horario no configurado o incoherente: rango abierto
        # (la validacion de guardado mostrara el mensaje correspondiente).
        self.time_inicio.setMinimumTime(QTime(0, 0))
        self.time_inicio.setMaximumTime(QTime(23, 59))
        self.time_fin.setMinimumTime(QTime(0, 0))
        self.time_fin.setMaximumTime(QTime(23, 59))

    def _validar_y_aceptar(self):
        """Valida los campos obligatorios antes de aceptar."""
        # Verificar que se selecciono un cliente
        if not self.buscador_cliente.tiene_seleccion():
            QMessageBox.warning(
                self,
                "Cliente requerido",
                "Debe buscar y seleccionar un cliente de la lista."
            )
            self.buscador_cliente.txt_busqueda.setFocus()
            return

        personas = self.txt_personas.text().strip()

        if not personas:
            QMessageBox.warning(self, "Campo requerido", "Debe ingresar el numero de personas.")
            self.txt_personas.setFocus()
            return

        try:
            num = int(personas)
            if num <= 0 or num > self.max_personas:
                raise ValueError
        except ValueError:
            QMessageBox.warning(
                self,
                "Valor invalido",
                f"El numero de personas debe ser un entero entre 1 y {self.max_personas}."
            )
            self.txt_personas.setFocus()
            return

        # Verificar que se selecciono una mesa del buscador
        if not self.cmb_mesa.tiene_seleccion():
            QMessageBox.warning(
                self,
                "Mesa requerida",
                "Debe buscar y seleccionar una mesa de la lista."
            )
            self.cmb_mesa.txt_busqueda.setFocus()
            return

        if self.time_fin.time() <= self.time_inicio.time():
            QMessageBox.warning(
                self,
                "Horario invalido",
                "La hora de fin debe ser posterior a la hora de inicio."
            )
            return

        # No permitir reservas en fechas pasadas
        from datetime import date
        if self.date_reserva.date().toPython() < date.today():
            QMessageBox.warning(
                self,
                "Fecha invalida",
                "No se puede registrar una reserva con una fecha pasada.\n"
                "Seleccione la fecha de hoy o una fecha futura."
            )
            return

        # Datos de fecha/hora/mesa (formato UI)
        hora_ini = self.time_inicio.time().toString("HH:mm")
        hora_fin = self.time_fin.time().toString("HH:mm")
        mesa = self.cmb_mesa.currentText().split(" - ")[0]
        fecha = self.date_reserva.date().toString("dd/MM/yyyy")

        # No registrar reservas de hoy en un horario ya transcurrido
        from datetime import datetime as _dt, timedelta as _td
        if fecha == _dt.today().strftime("%d/%m/%Y"):
            es_nueva = self.datos is None
            hora_cambiada = hora_ini != (self.datos or {}).get("hora_inicio", "")
            if es_nueva or hora_cambiada:
                umbral = (_dt.now() + _td(minutes=self.tolerancia_min)).strftime("%H:%M")
                if hora_ini < umbral:
                    QMessageBox.warning(
                        self,
                        "Horario ya pasado",
                        f"No se puede registrar la reserva para hoy a las {hora_ini}, "
                        "esa hora ya transcurrio.\n\n"
                        f"Hora minima permitida: {umbral}."
                    )
                    return
        zona = self._zona_de_mesa(mesa)
        fecha_q = self.date_reserva.date()

        # Dia festivo (tanto "Cerrado" como "Horario Especial" no son reservables)
        for festivo in self.festivos:
            if festivo["fecha"] == fecha:
                detalle = ""
                if festivo.get("descripcion"):
                    detalle = f" ({festivo['descripcion']})"
                QMessageBox.warning(
                    self,
                    "Dia festivo",
                    f"El {fecha} es un dia festivo{detalle}.\n"
                    "No se pueden registrar reservas ese dia."
                )
                return

        # Dia cerrado segun horarios de atencion
        hor = self._horario_para_fecha(fecha_q)
        if hor and hor.get("cerrado"):
            QMessageBox.warning(
                self,
                "Restaurante cerrado",
                f"El restaurante esta cerrado los {self._nombre_dia_semana(fecha_q.dayOfWeek())}.\n"
                "Seleccione otro dia de la semana."
            )
            return

        # Horario dentro del horario de atencion del local
        if hor:
            if hora_ini < hor["apertura"] or hora_fin > hor["cierre"]:
                QMessageBox.warning(
                    self,
                    "Fuera del horario de atencion",
                    f"El restaurante atiende los "
                    f"{self._nombre_dia_semana(fecha_q.dayOfWeek())} "
                    f"de {hor['apertura']} a {hor['cierre']}.\n"
                    f"Seleccione un horario dentro de ese rango "
                    f"(inicio {hora_ini} / fin {hora_fin})."
                )
                return

        # Limite de anticipacion segun la zona de la mesa seleccionada
        lim_zona = self.limites_zonas.get(zona) or {}
        try:
            max_dias_zona = int(lim_zona.get("max_dias") or self.dias_estandar)
        except (TypeError, ValueError):
            max_dias_zona = self.dias_estandar
        try:
            dias_anticipacion = (fecha_q.toPython() - date.today()).days
        except TypeError:
            dias_anticipacion = self.dias_estandar + 1
        if dias_anticipacion > max_dias_zona:
            QMessageBox.warning(
                self,
                "Demasiada anticipacion",
                f"La zona {zona} solo admite reservas hasta "
                f"{max_dias_zona} dias de anticipacion.\n"
                f"La fecha seleccionada esta a {dias_anticipacion} dias."
            )
            return

        # Reservas que superan el limite estandar requieren deposito (si la zona lo exige)
        if dias_anticipacion > self.dias_estandar:
            requiere_deposito = bool(lim_zona.get("requiere_deposito"))
            try:
                pct = int(lim_zona.get("porcentaje_deposito") or 0)
            except (TypeError, ValueError):
                pct = 0
            if not requiere_deposito:
                QMessageBox.warning(
                    self,
                    "Supera el limite estandar",
                    f"Las reservas se aceptan con hasta "
                    f"{self.dias_estandar} dias de anticipacion.\n"
                    f"La zona {zona} no admite anticipaciones mayores."
                )
                return
            respuesta = QMessageBox.question(
                self,
                "Deposito requerido",
                f"La reserva excede el limite estandar de "
                f"{self.dias_estandar} dias de anticipacion.\n\n"
                f"La zona {zona} exige un deposito del {pct}% "
                "(no reembolsable) para asegurar la fecha.\n\n"
                "Desea continuar y registrar la reserva?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if respuesta != QMessageBox.StandardButton.Yes:
                return
            self._nota_deposito = f"Requiere deposito del {pct}% (no reembolsable)."
        else:
            self._nota_deposito = ""

        # Validaciones de disponibilidad de mesas
        from modulos.almacen_datos import hay_traslape, mesas_disponibles, local_lleno, MESAS
        id_excluir = self.datos.get("id") if self.datos else None

        # Capacidad de la mesa seleccionada
        capacidad_mesa = next(
            (m["capacidad"] for m in MESAS if m["numero"] == mesa), 0
        )
        if num > capacidad_mesa:
            QMessageBox.warning(
                self,
                "Capacidad insuficiente",
                f"La mesa {mesa} tiene capacidad para {capacidad_mesa} personas, "
                f"pero la reserva es para {num}.\n\n"
                "Seleccione una mesa con mayor capacidad."
            )
            return

        # Si el local no tiene mesas libres para esa fecha/horario y personas -> lleno
        if local_lleno(fecha, hora_ini, hora_fin, num, id_excluir):
            QMessageBox.warning(
                self,
                "Local lleno",
                "No hay mesas disponibles para ese dia y horario: "
                "el restaurante se encuentra lleno.\n\n"
                "No es posible registrar la reserva. Intente con otra fecha u horario."
            )
            return

        # Verificar traslape de la mesa seleccionada
        conflicto = hay_traslape(mesa, fecha, hora_ini, hora_fin, id_excluir)
        if conflicto is not None:
            # Sugerir mesas alternativas libres
            alternativas = mesas_disponibles(fecha, hora_ini, hora_fin, num, id_excluir)
            texto_alt = ", ".join(f"{a['numero']} ({a['capacidad']}p)" for a in alternativas[:5])
            msg = (
                f"La mesa {mesa} ya tiene una reserva activa que se traslapa "
                f"({conflicto.get('cliente', '')} de {conflicto.get('hora_inicio', '')} "
                f"a {conflicto.get('hora_fin', '')})."
            )
            if texto_alt:
                msg += f"\n\nMesas disponibles en ese horario: {texto_alt}."
            else:
                msg += "\n\nNo quedan mesas libres en ese horario."
            QMessageBox.warning(self, "Mesa ocupada", msg)
            return

        self.accept()

    def obtener_datos(self):
        """Retorna un diccionario con los datos del formulario."""
        return {
            "cliente": self.buscador_cliente.obtener_nombre(),
            "id_cliente": self.buscador_cliente.obtener_id(),
            "telefono": self.buscador_cliente.obtener_telefono(),
            "fecha": self.date_reserva.date().toString("dd/MM/yyyy"),
            "hora_inicio": self.time_inicio.time().toString("HH:mm"),
            "hora_fin": self.time_fin.time().toString("HH:mm"),
            "personas": self.txt_personas.text().strip(),
            "mesa": self.cmb_mesa.currentText().split(" - ")[0],
            "estado": self.cmb_estado.currentText(),
            "observaciones": self._observaciones_con_deposito(),
        }

    def _observaciones_con_deposito(self):
        """Observaciones escritas + nota de deposito cuando corresponde."""
        obs = self.txt_observaciones.text().strip()
        nota = self._nota_deposito or ""
        if nota and nota not in obs:
            obs = (nota + " " + obs).strip() if obs else nota
        return obs


# ============================================================
# Dialogo para eliminar reservas en lote
# ============================================================
class DialogoLimpiarReservas(QDialog):
    """Dialogo para eliminar en lote reservas segun estado y antiguedad."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Limpiar Reservas en Lote")
        self.setMinimumWidth(420)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        lbl_titulo = QLabel("Eliminacion en lote de reservas")
        lbl_titulo.setStyleSheet(
            f"font-size: 16px; font-weight: 700; color: {PRIMARIO};"
        )
        layout.addWidget(lbl_titulo)

        lbl_ayuda = QLabel(
            "Depura el historial sin tener que borrar reserva por reserva."
        )
        lbl_ayuda.setWordWrap(True)
        lbl_ayuda.setStyleSheet("color: #777777; font-size: 11px;")
        layout.addWidget(lbl_ayuda)

        form = QFormLayout()
        self.cmb_estado = QComboBox()
        self.cmb_estado.addItems([
            "Cualquier estado", "Pendiente", "Confirmada",
            "Cancelada", "Completada",
        ])
        form.addRow("Filtrar por estado:", self.cmb_estado)

        self.chk_pasadas = QCheckBox(
            "Solo reservas de fechas ya pasadas (historial)"
        )
        self.chk_pasadas.setChecked(True)
        form.addRow("", self.chk_pasadas)
        layout.addLayout(form)

        self.lbl_preview = QLabel("")
        self.lbl_preview.setStyleSheet(
            "font-size: 13px; font-weight: 600; color: #BC1515;"
        )
        layout.addWidget(self.lbl_preview)

        # Sesion 25: barra de progreso de la tarea en segundo plano.
        self.barra_progreso = QProgressBar()
        self.barra_progreso.setRange(0, 100)
        self.barra_progreso.setValue(0)
        self.barra_progreso.setVisible(False)
        layout.addWidget(self.barra_progreso)

        fila_botones = QHBoxLayout()
        fila_botones.addStretch()

        # Sesion 26: boton de detencion cooperativa (Stop Flag).
        self.btn_detener = QPushButton("Detener Proceso")
        self.btn_detener.setObjectName("secundario")
        self.btn_detener.setMinimumHeight(38)
        self.btn_detener.setVisible(False)
        self.btn_detener.clicked.connect(self._detener_hilo)
        fila_botones.addWidget(self.btn_detener)

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setObjectName("secundario")
        btn_cancelar.setMinimumHeight(38)
        btn_cancelar.clicked.connect(self.reject)
        fila_botones.addWidget(btn_cancelar)

        self.btn_eliminar = QPushButton("Eliminar Seleccionadas")
        self.btn_eliminar.setObjectName("peligro")
        self.btn_eliminar.setMinimumHeight(38)
        self.btn_eliminar.clicked.connect(self._ejecutar)
        fila_botones.addWidget(self.btn_eliminar)
        layout.addLayout(fila_botones)

        self.cmb_estado.currentTextChanged.connect(self._actualizar_preview)
        self.chk_pasadas.toggled.connect(self._actualizar_preview)
        self._actualizar_preview()

        # Hilo de tarea pesada (Sesion 23): None mientras no haya limpieza.
        self.hilo = None

    def reject(self):
        """Sesion 24: no permite cerrar el dialogo mientras el hilo corre."""
        if self.hilo is not None and self.hilo.isRunning():
            return
        super().reject()

    def _estados_seleccion(self):
        texto = self.cmb_estado.currentText()
        return None if texto == "Cualquier estado" else [texto]

    def _ids_seleccion(self):
        return almacen_datos._reservas_lote_seleccion(
            self._estados_seleccion(), self.chk_pasadas.isChecked()
        )

    def _actualizar_preview(self):
        ids = self._ids_seleccion()
        self.btn_eliminar.setEnabled(bool(ids))
        criterio = self.cmb_estado.currentText().lower()
        ambito = "fechas pasadas" if self.chk_pasadas.isChecked() else "todas las fechas"
        self.lbl_preview.setText(
            f"Se eliminaran {len(ids)} reserva(s)\n({criterio}, {ambito})."
        )

    def _al_iniciar_hilo(self):
        """Sesion 24: señal started (el boton ya se deshabilita en _ejecutar)."""
        self.lbl_preview.setText("Purgando reservas en segundo plano...")

    def _al_progreso(self, porcentaje, texto):
        """Sesion 25: slot receptor thread-safe (solo actualiza la UI)."""
        self.barra_progreso.setValue(porcentaje)
        self.lbl_preview.setText(texto)

    def _detener_hilo(self):
        """Sesion 26: peticion cooperativa; el hilo para en el siguiente lote."""
        self.btn_detener.setEnabled(False)
        self.lbl_preview.setText("Deteniendo... se confirmara en el siguiente lote.")
        if self.hilo is not None:
            self.hilo.detener()

    def _al_finalizar_hilo(self):
        """Sesion 24: señal finished (reactiva el dialogo)."""
        if self.hilo is not None and not self.hilo.isRunning():
            self.btn_eliminar.setEnabled(bool(self._ids_seleccion()))

    def _al_tarea_finalizada(self, resultado):
        """Procesa el resultado del hilo en el Main Thread (thread-safe)."""
        self.btn_detener.setVisible(False)
        self.barra_progreso.setVisible(False)
        self.btn_detener.setEnabled(True)

        error = resultado.get("error")
        if error:
            QMessageBox.critical(
                self, "Error", f"No se pudo purgar el historial.\n{error}"
            )
            self.btn_eliminar.setEnabled(True)
            self._actualizar_preview()
            return

        # La cache en memoria solo se muta aqui (hilo principal).
        nuevas = resultado.get("nuevas_reservas")
        if nuevas is not None:
            almacen_datos.lista_reservas[:] = nuevas
        for numero in resultado.get("mesas_afectadas", []):
            almacen_datos._sincronizar_estado_mesa_bd(numero)

        eliminadas = resultado.get("eliminadas", 0)
        cancelado = resultado.get("cancelado", False)
        if cancelado:
            QMessageBox.warning(
                self, "Proceso detenido",
                f"Se detuvo la limpieza. Se eliminaron {eliminadas} reserva(s).",
            )
            self.accept()
        elif eliminadas:
            QMessageBox.information(
                self, "Limpieza completada",
                f"Se eliminaron {eliminadas} reserva(s).",
            )
            self.accept()
        else:
            QMessageBox.warning(
                self, "Sin cambios",
                "No se pudo eliminar ninguna reserva.",
            )
            self.reject()

    def _ejecutar(self):
        ids = self._ids_seleccion()
        if not ids:
            return
        # Sesion 24: guarda para evitar ejecuciones duplicadas.
        if self.hilo is not None and self.hilo.isRunning():
            return
        respuesta = QMessageBox.question(
            self,
            "Confirmar eliminacion en lote",
            f"Desea eliminar {len(ids)} reserva(s)?\n\n"
            "Esta accion no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if respuesta != QMessageBox.StandardButton.Yes:
            return

        self.btn_eliminar.setEnabled(False)
        self.barra_progreso.setVisible(True)
        self.barra_progreso.setValue(0)
        self.btn_detener.setVisible(True)
        self.btn_detener.setEnabled(True)

        # Sesion 23: arrancar el Worker Thread con start() (nunca run()).
        self.hilo = HiloLimpiarReservas(ids)
        self.hilo.started.connect(self._al_iniciar_hilo)
        self.hilo.progreso.connect(self._al_progreso)
        self.hilo.tarea_finalizada.connect(self._al_tarea_finalizada)
        self.hilo.finished.connect(self._al_finalizar_hilo)
        self.hilo.start()


# ============================================================
# Panel principal de reservas con CRUD
# ============================================================
class PanelReservas(QWidget):
    """
    Panel de gestion de reservas.
    CRUD: Create, Read, Update, Delete - todo sobre la tabla en memoria.
    Cuando se conecte la BD, cada operacion ejecutara el SQL correspondiente.
    """
    # Senal que se emite cuando cambian las reservas (para actualizar dashboard, etc.)
    reservas_cambiadas = Signal()

    def __init__(self, usuario_gestion="Admin General"):
        super().__init__()
        # Nombre del usuario que gestiona las reservas (para el campo 'gestiono').
        # En produccion se conserva como FK del usuario en BD.
        self.usuario_gestion = usuario_gestion
        # Almacenamiento en memoria de las reservas
        # Cada reserva es un diccionario con sus campos
        self.lista_reservas = []
        self._cargar_datos_prueba()
        self._construir_interfaz()

    def _cargar_datos_prueba(self):
        """
        Vincula la lista de reservas del panel con el almacen central.
        En produccion, esta linea se reemplaza por: lista_reservas = consulta_SQL()
        Compartir la MISMA lista garantiza que mesas y reportes siempre vean
        los cambios de reservas (una unica fuente de verdad).
        """
        self.lista_reservas = almacen_datos.lista_reservas

    def _construir_interfaz(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        # ============================================================
        # ENCABEZADO + BOTONES DE ACCION PRINCIPALES
        # ============================================================
        layout_encabezado = QHBoxLayout()

        izquierda = QVBoxLayout()
        lbl_titulo = QLabel("Gestion de Reservas")
        lbl_titulo.setObjectName("titulo")
        izquierda.addWidget(lbl_titulo)

        lbl_sub = QLabel("Crear, editar y administrar reservas del restaurante")
        lbl_sub.setObjectName("subtitulo")
        izquierda.addWidget(lbl_sub)

        layout_encabezado.addLayout(izquierda)
        layout_encabezado.addStretch()

        # Botones principales de accion
        btn_nueva = QPushButton("+ Nueva Reserva")
        btn_nueva.setObjectName("acento")
        btn_nueva.setMinimumHeight(42)
        btn_nueva.setMinimumWidth(160)
        btn_nueva.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_nueva.clicked.connect(self._crear_reserva)
        layout_encabezado.addWidget(btn_nueva)

        layout.addLayout(layout_encabezado)

        # ============================================================
        # BARRA DE FILTROS
        # ============================================================
        layout_filtros = QHBoxLayout()
        layout_filtros.setSpacing(12)

        lbl_filtro = QLabel("Filtrar por estado:")
        lbl_filtro.setStyleSheet("font-weight: 600; color: #555;")
        layout_filtros.addWidget(lbl_filtro)

        self.cmb_filtro_estado = QComboBox()
        self.cmb_filtro_estado.addItems(["Todas", "Pendiente", "Confirmada", "Cancelada", "Completada"])
        self.cmb_filtro_estado.setMinimumWidth(160)
        self.cmb_filtro_estado.currentTextChanged.connect(self._aplicar_filtro)
        layout_filtros.addWidget(self.cmb_filtro_estado)

        lbl_buscar = QLabel("Buscar:")
        lbl_buscar.setStyleSheet("font-weight: 600; color: #555;")
        layout_filtros.addWidget(lbl_buscar)

        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("Nombre del cliente o mesa...")
        self.txt_buscar.setMinimumWidth(220)
        self.txt_buscar.textChanged.connect(self._aplicar_filtro)
        layout_filtros.addWidget(self.txt_buscar)

        layout_filtros.addStretch()

        # Contador de reservas
        self.lbl_contador = QLabel()
        self.lbl_contador.setStyleSheet("color: #888; font-size: 12px;")
        layout_filtros.addWidget(self.lbl_contador)

        layout.addLayout(layout_filtros)

        # ============================================================
        # TABLA DE RESERVAS
        # ============================================================
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(8)
        self.tabla.setHorizontalHeaderLabels([
            "ID", "Cliente", "Mesa", "Fecha", "Inicio", "Fin", "Estado", "Personas"
        ])

        # Configurar encabezados
        header = self.tabla.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)

        # Configurar comportamiento de seleccion
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setMinimumHeight(300)

        # Doble clic para editar
        self.tabla.doubleClicked.connect(self._editar_reserva)

        layout.addWidget(self.tabla)

        # ============================================================
        # BOTONES DE ACCION INFERIORES
        # ============================================================
        layout_acciones = QHBoxLayout()
        layout_acciones.setSpacing(12)

        btn_ver = QPushButton("Ver Detalle")
        btn_ver.setObjectName("secundario")
        btn_ver.setMinimumHeight(40)
        btn_ver.setMinimumWidth(140)
        btn_ver.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ver.clicked.connect(self._ver_detalle)
        layout_acciones.addWidget(btn_ver)

        btn_editar = QPushButton("Editar")
        btn_editar.setMinimumHeight(40)
        btn_editar.setMinimumWidth(120)
        btn_editar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_editar.clicked.connect(self._editar_reserva)
        layout_acciones.addWidget(btn_editar)

        btn_confirmar = QPushButton("Confirmar")
        btn_confirmar.setObjectName("exito")
        btn_confirmar.setMinimumHeight(40)
        btn_confirmar.setMinimumWidth(120)
        btn_confirmar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_confirmar.clicked.connect(self._confirmar_reserva)
        layout_acciones.addWidget(btn_confirmar)

        btn_completar = QPushButton("Completar")
        btn_completar.setObjectName("exito")
        btn_completar.setMinimumHeight(40)
        btn_completar.setMinimumWidth(120)
        btn_completar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_completar.clicked.connect(self._completar_reserva)
        layout_acciones.addWidget(btn_completar)

        btn_cancelar = QPushButton("Cancelar Reserva")
        btn_cancelar.setObjectName("peligro")
        btn_cancelar.setMinimumHeight(40)
        btn_cancelar.setMinimumWidth(160)
        btn_cancelar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancelar.clicked.connect(self._cancelar_reserva)
        layout_acciones.addWidget(btn_cancelar)

        btn_eliminar = QPushButton("Eliminar")
        btn_eliminar.setObjectName("peligro")
        btn_eliminar.setMinimumHeight(40)
        btn_eliminar.setMinimumWidth(120)
        btn_eliminar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_eliminar.clicked.connect(self._eliminar_reserva)
        layout_acciones.addWidget(btn_eliminar)

        btn_limpiar = QPushButton("Limpiar en Lote")
        btn_limpiar.setObjectName("peligro")
        btn_limpiar.setMinimumHeight(40)
        btn_limpiar.setMinimumWidth(140)
        btn_limpiar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_limpiar.clicked.connect(self._limpiar_en_lote)
        layout_acciones.addWidget(btn_limpiar)

        layout_acciones.addStretch()

        layout.addLayout(layout_acciones)

        # Cargar datos en la tabla
        self._refrescar_tabla()

    # ============================================================
    # OPERACIONES CRUD
    # ============================================================

    def _refrescar_tabla(self, reservas=None):
        """
        Reconstruye la tabla completa con la lista de reservas.
        Si se pasa una lista filtrada, muestra solo esas.
        """
        datos = reservas if reservas is not None else self.lista_reservas

        self.tabla.setRowCount(len(datos))

        colores_estado = {
            "Pendiente": NARANJA,
            "Confirmada": VERDE,
            "Cancelada": ROJO,
            "Completada": SECUNDARIO,
        }

        for fila, r in enumerate(datos):
            campos = [
                str(r["id"]),
                r["cliente"],
                r["mesa"],
                r["fecha"],
                r["hora_inicio"],
                r["hora_fin"],
                r["estado"],
                r["personas"],
            ]

            for col, valor in enumerate(campos):
                item = QTableWidgetItem(valor)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                # Guardar el ID como data oculta para facilitar busquedas
                if col == 0:
                    item.setData(Qt.ItemDataRole.UserRole, r["id"])

                # Colorear la columna de estado
                if col == 6:
                    color = colores_estado.get(valor, GRIS)
                    item.setBackground(QColor(color))
                    item.setForeground(QColor("white") if valor != "Pendiente" else QColor("#333"))
                    item.setFont(QFont("Raleway", 11, QFont.Weight.Bold))

                self.tabla.setItem(fila, col, item)

        # Actualizar contador
        total = len(self.lista_reservas)
        mostrados = len(datos)
        if mostrados == total:
            self.lbl_contador.setText(f"Total: {total} reservas")
        else:
            self.lbl_contador.setText(f"Mostrando {mostrados} de {total} reservas")

    def _aplicar_filtro(self):
        """Filtra la tabla segun el estado y texto de busqueda."""
        texto_estado = self.cmb_filtro_estado.currentText()
        texto_busqueda = self.txt_buscar.text().strip().lower()

        resultado = self.lista_reservas

        # Filtro por estado
        if texto_estado != "Todas":
            resultado = [r for r in resultado if r["estado"] == texto_estado]

        # Filtro por texto (cliente o mesa)
        if texto_busqueda:
            resultado = [
                r for r in resultado
                if texto_busqueda in r["cliente"].lower()
                or texto_busqueda in r["mesa"].lower()
            ]

        self._refrescar_tabla(resultado)

    def _obtener_reserva_seleccionada(self):
        """
        Retorna la reserva completa que esta seleccionada en la tabla, o None.
        Utiliza el ID guardado en el UserRole del item de la columna 0.
        """
        fila = self.tabla.currentRow()
        if fila == -1:
            return None

        item_id = self.tabla.item(fila, 0)
        if item_id is None:
            return None

        reserva_id = item_id.data(Qt.ItemDataRole.UserRole)

        for r in self.lista_reservas:
            if r["id"] == reserva_id:
                return r
        return None

    def _obtener_siguiente_id(self):
        """Genera el siguiente ID disponible (autoincremento en memoria)."""
        if not self.lista_reservas:
            return 1
        return max(r["id"] for r in self.lista_reservas) + 1

    # ============================================================
    # CREATE - Crear nueva reserva
    # ============================================================
    def _crear_reserva(self):
        """Abre el dialogo para crear una nueva reserva."""
        dialogo = DialogoReserva(parent=self)

        if dialogo.exec() == QDialog.DialogCode.Accepted:
            datos = dialogo.obtener_datos()
            datos["gestiono"] = self.usuario_gestion

            ok, nid, error = almacen_datos.crear_reserva(datos)
            if not ok:
                QMessageBox.critical(self, "Error al guardar", error or "No se pudo crear la reserva.")
                return

            self._refrescar_tabla()
            self.reservas_cambiadas.emit()

            QMessageBox.information(
                self,
                "Reserva Creada",
                f"Reserva #{nid} creada exitosamente para {datos['cliente']}."
            )

    # ============================================================
    # READ - Ver detalle de reserva
    # ============================================================
    def _ver_detalle(self):
        """Muestra los datos completos de la reserva seleccionada."""
        reserva = self._obtener_reserva_seleccionada()
        if reserva is None:
            QMessageBox.information(self, "Sin seleccion", "Seleccione una reserva para ver su detalle.")
            return

        detalle = f"""
        RESERVA #{reserva['id']}
        ─────────────────────────────
        Cliente:      {reserva['cliente']}
        Mesa:         {reserva['mesa']}
        Fecha:        {reserva['fecha']}
        Hora:         {reserva['hora_inicio']} - {reserva['hora_fin']}
        Personas:     {reserva['personas']}
        Estado:       {reserva['estado']}
        Observaciones: {reserva['observaciones'] if reserva['observaciones'] else 'Ninguna'}
        Gestiono:     {reserva['gestiono']}
        """

        QMessageBox.information(self, "Detalle de Reserva", detalle)

    # ============================================================
    # UPDATE - Editar reserva existente
    # ============================================================
    def _editar_reserva(self):
        """Abre el dialogo con los datos de la reserva para editarla."""
        reserva = self._obtener_reserva_seleccionada()
        if reserva is None:
            QMessageBox.information(self, "Sin seleccion", "Seleccione una reserva para editar.")
            return

        dialogo = DialogoReserva(parent=self, datos=reserva)

        if dialogo.exec() == QDialog.DialogCode.Accepted:
            nuevos_datos = dialogo.obtener_datos()
            nuevos_datos["gestiono"] = reserva["gestiono"]

            ok, error = almacen_datos.actualizar_reserva(reserva["id"], nuevos_datos)
            if not ok:
                QMessageBox.critical(self, "Error al actualizar", error or "No se pudo actualizar la reserva.")
                return

            self._refrescar_tabla()
            self.reservas_cambiadas.emit()

            QMessageBox.information(
                self,
                "Reserva Actualizada",
                f"Reserva #{reserva['id']} actualizada correctamente."
            )

    # ============================================================
    # UPDATE - Confirmar reserva (cambiar estado a Confirmada)
    # ============================================================
    def _confirmar_reserva(self):
        """Cambia el estado de la reserva seleccionada a 'Confirmada'."""
        reserva = self._obtener_reserva_seleccionada()
        if reserva is None:
            QMessageBox.information(self, "Sin seleccion", "Seleccione una reserva para confirmar.")
            return

        if reserva["estado"] == "Confirmada":
            QMessageBox.information(self, "Ya confirmada", "Esta reserva ya esta confirmada.")
            return

        if reserva["estado"] == "Cancelada":
            QMessageBox.warning(
                self,
                "Reserva cancelada",
                "No se puede confirmar una reserva que fue cancelada."
            )
            return

        if reserva["estado"] == "Completada":
            QMessageBox.warning(
                self,
                "Reserva completada",
                "No se puede confirmar una reserva que ya fue completada."
            )
            return

        respuesta = QMessageBox.question(
            self,
            "Confirmar Reserva",
            f"Confirmar la reserva #{reserva['id']} de {reserva['cliente']}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if respuesta == QMessageBox.StandardButton.Yes:
            ok, error = almacen_datos.cambiar_estado_reserva(
                reserva["id"], "Confirmada"
            )
            if ok:
                self._refrescar_tabla()
                self.reservas_cambiadas.emit()
                QMessageBox.information(
                    self,
                    "Confirmada",
                    f"Reserva #{reserva['id']} confirmada exitosamente."
                )
            else:
                QMessageBox.critical(
                    self, "Error", error or "No se pudo confirmar la reserva."
                )

    # ============================================================
    # UPDATE - Completar reserva (cambiar estado a Completada)
    # ============================================================
    def _completar_reserva(self):
        """Cambia el estado de la reserva seleccionada a 'Completada'."""
        reserva = self._obtener_reserva_seleccionada()
        if reserva is None:
            QMessageBox.information(self, "Sin seleccion", "Seleccione una reserva para completar.")
            return

        if reserva["estado"] == "Completada":
            QMessageBox.information(self, "Ya completada", "Esta reserva ya esta completada.")
            return

        if reserva["estado"] == "Cancelada":
            QMessageBox.warning(
                self,
                "Reserva cancelada",
                "No se puede completar una reserva que fue cancelada."
            )
            return

        if reserva["estado"] != "Confirmada":
            QMessageBox.warning(
                self,
                "Reserva no confirmada",
                "Solo se puede completar una reserva previamente confirmada."
            )
            return

        respuesta = QMessageBox.question(
            self,
            "Completar Reserva",
            f"Marcar como completada la reserva #{reserva['id']} de {reserva['cliente']}?\n\n"
            f"Mesa: {reserva['mesa']} | {reserva['hora_inicio']} - {reserva['hora_fin']}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if respuesta == QMessageBox.StandardButton.Yes:
            ok, error = almacen_datos.cambiar_estado_reserva(
                reserva["id"], "Completada"
            )
            if ok:
                self._refrescar_tabla()
                self.reservas_cambiadas.emit()
                QMessageBox.information(
                    self,
                    "Completada",
                    f"Reserva #{reserva['id']} marcada como completada."
                )
            else:
                QMessageBox.critical(
                    self, "Error", error or "No se pudo completar la reserva."
                )

    # ============================================================
    # UPDATE - Cancelar reserva (cambiar estado a Cancelada)
    # ============================================================
    def _cancelar_reserva(self):
        """Cambia el estado de la reserva seleccionada a 'Cancelada'."""
        reserva = self._obtener_reserva_seleccionada()
        if reserva is None:
            QMessageBox.information(self, "Sin seleccion", "Seleccione una reserva para cancelar.")
            return

        if reserva["estado"] == "Cancelada":
            QMessageBox.information(self, "Ya cancelada", "Esta reserva ya esta cancelada.")
            return

        if reserva["estado"] == "Completada":
            QMessageBox.warning(
                self,
                "Reserva completada",
                "No se puede cancelar una reserva que ya fue completada."
            )
            return

        respuesta = QMessageBox.question(
            self,
            "Cancelar Reserva",
            f"Desea cancelar la reserva #{reserva['id']} de {reserva['cliente']}?\n\n"
            f"Mesa: {reserva['mesa']} | {reserva['hora_inicio']} - {reserva['hora_fin']}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if respuesta == QMessageBox.StandardButton.Yes:
            ok, error = almacen_datos.cambiar_estado_reserva(
                reserva["id"], "Cancelada"
            )
            if ok:
                self._refrescar_tabla()
                self.reservas_cambiadas.emit()
                QMessageBox.information(
                    self,
                    "Cancelada",
                    f"Reserva #{reserva['id']} cancelada."
                )
            else:
                QMessageBox.critical(
                    self, "Error", error or "No se pudo cancelar la reserva."
                )

    # ============================================================
    # DELETE - Eliminar reserva permanentemente
    # ============================================================
    def _eliminar_reserva(self):
        """Elimina permanentemente la reserva seleccionada de la lista."""
        reserva = self._obtener_reserva_seleccionada()
        if reserva is None:
            QMessageBox.information(self, "Sin seleccion", "Seleccione una reserva para eliminar.")
            return

        respuesta = QMessageBox.warning(
            self,
            "Eliminar Reserva",
            f"ELIMINAR permanentemente la reserva #{reserva['id']}?\n\n"
            f"Cliente: {reserva['cliente']}\n"
            f"Mesa: {reserva['mesa']} | {reserva['fecha']} {reserva['hora_inicio']}\n\n"
            f"Esta accion no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if respuesta == QMessageBox.StandardButton.Yes:
            if almacen_datos.eliminar_reserva(reserva["id"]):
                self._refrescar_tabla()
            else:
                QMessageBox.critical(self, "Error", "No se pudo eliminar la reserva.")
            self.reservas_cambiadas.emit()

            QMessageBox.information(
                self,
                "Eliminada",
                f"Reserva #{reserva['id']} eliminada permanentemente."
            )

    def _limpiar_en_lote(self):
        """Abre el dialogo de eliminacion en lote y refresca la tabla."""
        dialogo = DialogoLimpiarReservas(parent=self)
        if dialogo.exec() == QDialog.DialogCode.Accepted:
            self._refrescar_tabla()
            self.reservas_cambiadas.emit()

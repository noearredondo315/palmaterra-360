from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import QApplication, QStyleFactory, QAbstractItemView, QHeaderView, QMenu, QMessageBox, QProgressDialog
from PyQt6.QtGui import QAction, QPalette, QFont, QCursor, QStandardItemModel, QStandardItem, QIcon
from PyQt6.QtCore import pyqtSlot, QTime, QDateTime, QFileInfo, Qt, QSize, QRunnable, QThreadPool, pyqtSignal, QObject, QMutex, QMutexLocker, QSortFilterProxyModel, QDate
from PyQt6.QtWidgets import QInputDialog, QDialog, QFileDialog, QStyleOptionButton, QStyledItemDelegate, QVBoxLayout, QCheckBox, QPushButton, QHBoxLayout, QScrollArea, QWidget
import pandas as pd
from bs4 import BeautifulSoup
from requests.exceptions import ConnectionError, Timeout, RequestException
import icons62, os, requests, webbrowser, re
from PyQt6.QtCore import Qt, QDate
import sys
import pikepdf
import hashlib
import xml.etree.ElementTree as ET
import openpyxl
from openpyxl.styles import numbers
from collections import Counter
from style6 import Ui_Form  # Asegúrate de que Ui_Form sea la clase de la interfaz en style6.py
from PIL import Image
import imghdr
import io

if getattr(sys, 'frozen', False):
    import pyi_splash

class DialogoErrores(QDialog):
    def __init__(self, errores, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Errores encontrados")
        self.setMinimumSize(600, 400)  # Tamaño mínimo del diálogo

        # Layout principal
        layout = QVBoxLayout(self)

        # Widget de texto con scroll
        self.text_edit = QtWidgets.QTextEdit(self)
        self.text_edit.setReadOnly(True)  # Solo lectura
        layout.addWidget(self.text_edit)

        # Botón de cerrar
        self.cerrar_button = QPushButton("Cerrar", self)
        self.cerrar_button.clicked.connect(self.accept)
        layout.addWidget(self.cerrar_button)

        # Llenar el texto con los errores
        self.mostrar_errores(errores)

    def mostrar_errores(self, errores):
        """
        Mostrar los errores en el QTextEdit.
        """
        mensaje = "Se encontraron los siguientes errores:\n\n"
        for error in errores:
            mensaje += f"Obra: {error['OBRA']}\n"
            mensaje += f"Proveedor: {error['PROVEEDOR']}\n"
            mensaje += f"Número: {error['NÚMERO']}\n"
            mensaje += f"Error: {error['ERROR']}\n"
            mensaje += "-" * 40 + "\n"

        self.text_edit.setText(mensaje)

# Modelo personalizado para mostrar valores formateados con separador de miles
class FormattedStandardItemModel(QStandardItemModel):
    # Definir las columnas que requieren el símbolo de pesos
    currency_columns = ["P. UNITARIO", "IMPORTE", "TOTAL IMPORTE", "IVA (16%)", "DESCUENTO", "IMPORTE CON DESCUENTO", "RET. IVA", "RET. ISR", "ISH"]

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        # Obtener el valor original del modelo base en EditRole
        value = super().data(index, Qt.ItemDataRole.EditRole)

        # Verificar si el rol es DisplayRole y si el valor es numérico
        if role == Qt.ItemDataRole.DisplayRole and isinstance(value, (int, float)):
            # Obtener el nombre de la columna actual
            column_name = self.headerData(index.column(), Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole)

            # Formatear el valor con separador de miles
            formatted_value = "{:,.2f}".format(value) if isinstance(value, float) else "{:,}".format(value)

            # Si la columna es una de las que requiere símbolo de pesos, añadirlo
            if column_name in self.currency_columns:
                return f"${formatted_value}"

            return formatted_value

        # Para otros roles, devolvemos el valor sin formato
        return super().data(index, role)

class MultiSelectDialog(QDialog):
    def __init__(self, items, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Seleccionar Opciones")
        self.resize(400, 300)

        self.selected_items = []

        # Layout principal del diálogo
        layout = QVBoxLayout(self)

        # Área de scroll para los checkboxes
        scroll = QScrollArea(self)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        self.checkboxes = []
        for item in items:
            checkbox = QCheckBox(item)
            scroll_layout.addWidget(checkbox)
            self.checkboxes.append(checkbox)

        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)

        # Añadir scroll al layout principal
        layout.addWidget(scroll)

        # Botón para seleccionar/deseleccionar todos
        self.select_all_button = QPushButton("Seleccionar Todos", self)
        self.select_all_button.clicked.connect(self.toggle_select_all)
        layout.addWidget(self.select_all_button)

        # Botones de Aceptar y Cancelar
        button_layout = QHBoxLayout()
        accept_button = QPushButton("Aceptar", self)
        cancel_button = QPushButton("Cancelar", self)
        accept_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(accept_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

    def toggle_select_all(self):
        """Selecciona o deselecciona todos los checkboxes."""
        new_state = Qt.CheckState.Checked if self.select_all_button.text() == "Seleccionar Todos" else Qt.CheckState.Unchecked
        for checkbox in self.checkboxes:
            checkbox.setCheckState(new_state)

        # Cambiar el texto del botón
        self.select_all_button.setText("Deseleccionar Todos" if new_state == Qt.CheckState.Checked else "Seleccionar Todos")

    def get_selected_items(self):
        """Devuelve la lista de elementos seleccionados."""
        self.selected_items = [checkbox.text() for checkbox in self.checkboxes if checkbox.isChecked()]
        return self.selected_items

class CustomFilterProxyModel(QSortFilterProxyModel):
    def __init__(self):
        super().__init__()
        self.filter_obra_text_list = []
        self.filter_proveedor_text_list = []
        self.filter_residente_text_list = []
        self.filter_numero_text_list = []
        self.filter_descripcion_text_list = []
        self.filter_fecha_inicio = None
        self.filter_fecha_fin = None
        self.filter_estatus_list = []
        self.column_indices = {}
        self.numeric_columns = []
        self.date_columns = []
        self.date_cache = {}  # Caché para almacenar conversiones de fecha

    def set_filter_estatus(self, estatus_list):
        """Actualizar la lista de estatus a filtrar."""
        self.filter_estatus_list = estatus_list
        self.invalidateFilter()

    def invalidateCache(self):
        """Método para limpiar el caché de fechas."""
        self.date_cache.clear()

    def set_fecha_column_index(self, index):
        """Método para definir el índice de la columna de fecha a filtrar."""
        self.fecha_column_index = index
        self.invalidateFilter()

    def set_filter_obra(self, text):
        # Dividir el texto en base a comas y eliminar espacios innecesarios
        self.filter_obra_text_list = [t.strip().lower() for t in text.split(",") if t.strip()]
        self.invalidateFilter()

    def set_filter_proveedor(self, text):
        # Dividir el texto en base a comas y eliminar espacios innecesarios
        self.filter_proveedor_text_list = [t.strip().lower() for t in text.split(",") if t.strip()]
        self.invalidateFilter()

    def set_filter_residente(self, text):
        # Dividir el texto en base a comas y eliminar espacios innecesarios
        self.filter_residente_text_list = [t.strip().lower() for t in text.split(",") if t.strip()]
        self.invalidateFilter()

    def set_filter_numero(self, text):
        # Dividir el texto en base a comas y eliminar espacios innecesarios
        self.filter_numero_text_list = [t.strip().lower() for t in text.split(",") if t.strip()]
        self.invalidateFilter()

    def set_filter_descripcion(self, text):
        # Dividir el texto en base a comas y eliminar espacios innecesarios
        self.filter_descripcion_text_list = [t.strip().lower() for t in text.split(",") if t.strip()]
        self.invalidateFilter()

    def set_filter_fecha(self, start_date, end_date):
        # Validar si start_date y end_date son válidos, de lo contrario poner None
        if start_date:
            self.filter_fecha_inicio = QDateTime(start_date, QTime(0, 0, 0))  # Hora 00:00 para el inicio del rango
        else:
            self.filter_fecha_inicio = None

        if end_date:
            self.filter_fecha_fin = QDateTime(end_date, QTime(23, 59, 59))  # Hora 23:59 para el final del rango
        else:
            self.filter_fecha_fin = None

        self.invalidateFilter()

    def clear_filters(self):
        self.filter_fecha_inicio = None
        self.filter_fecha_fin = None
        self.invalidateFilter()

    def set_column_indices(self, column_mapping):
        """Configura el mapeo de nombres de columnas a índices."""
        self.column_indices = column_mapping

    def set_numeric_columns(self, columns):
        """Método para definir las columnas que deben ordenarse numéricamente."""
        self.numeric_columns = columns
        self.invalidateFilter()  # Refresca el filtro y la ordenación

    def set_date_columns(self, columns):
        """Método para definir las columnas que deben ordenarse numéricamente."""
        self.date_columns = columns
        self.invalidateFilter()  # Refresca el filtro y la ordenación

    def lessThan(self, left_index, right_index):
        model = self.sourceModel()

        # Identificar si la columna es "OrdenOriginal" usando su nombre
        if self.column_indices.get('OrdenOriginal') == left_index.column():
            left_data = model.data(left_index, Qt.ItemDataRole.UserRole) or float('-inf')
            right_data = model.data(right_index, Qt.ItemDataRole.UserRole) or float('-inf')
            return left_data < right_data

        # Ordenar las columnas definidas como numéricas
        if left_index.column() in self.numeric_columns:
            left_data = model.data(left_index, Qt.ItemDataRole.UserRole) or float('-inf')
            right_data = model.data(right_index, Qt.ItemDataRole.UserRole) or float('-inf')
            return left_data < right_data

        # Ordenar columnas de fecha y hora
        if left_index.column() in self.date_columns:
            left_data = model.data(left_index, Qt.ItemDataRole.DisplayRole) or ""
            right_data = model.data(right_index, Qt.ItemDataRole.DisplayRole) or ""

            # Función para convertir y almacenar fechas en caché
            def get_cached_date(data):
                if data not in self.date_cache:
                    date = QtCore.QDateTime.fromString(data, "dd/MM/yyyy HH:mm")
                    self.date_cache[data] = date if date.isValid() else QtCore.QDateTime()  # Fecha predeterminada
                return self.date_cache[data]

            left_date = get_cached_date(left_data)
            right_date = get_cached_date(right_data)

            return left_date < right_date

        # Ordenar el resto de las columnas como cadenas
        left_data = model.data(left_index, Qt.ItemDataRole.DisplayRole) or ""
        right_data = model.data(right_index, Qt.ItemDataRole.DisplayRole) or ""
        return str(left_data) < str(right_data)


    def filterAcceptsRow(self, source_row, source_parent):
        model = self.sourceModel()

        # Filtrar por 'Obra'
        if self.filter_obra_text_list:
            obra_index = model.index(source_row, self.column_indices.get('Obra'), source_parent)
            obra_data = model.data(obra_index).lower() if model.data(obra_index) else ""
            if not any(filter_text in obra_data for filter_text in self.filter_obra_text_list):
                return False

        # Filtrar por 'Proveedor'
        if self.filter_proveedor_text_list:
            proveedor_index = model.index(source_row, self.column_indices.get('Proveedor'), source_parent)
            proveedor_data = model.data(proveedor_index).lower() if model.data(proveedor_index) else ""
            if not any(filter_text in proveedor_data for filter_text in self.filter_proveedor_text_list):
                return False

        # Filtrar por 'Residente'
        if self.filter_residente_text_list:
            residente_index = model.index(source_row, self.column_indices.get('Residente'), source_parent)
            residente_data = model.data(residente_index).lower() if model.data(residente_index) else ""
            if not any(filter_text in residente_data for filter_text in self.filter_residente_text_list):
                return False

        # Filtrar por 'Numero'
        if self.filter_numero_text_list:
            numero_index = model.index(source_row, self.column_indices.get('Número'), source_parent)
            numero_data = model.data(numero_index).lower() if model.data(numero_index) else ""
            if not any(filter_text in numero_data for filter_text in self.filter_numero_text_list):
                return False

        # Filtrar por 'Descripcion'
        if self.filter_descripcion_text_list:
            descripcion_index = model.index(source_row, self.column_indices.get('Descripción'), source_parent)
            descripcion_data = model.data(descripcion_index).lower() if model.data(descripcion_index) else ""
            if not any(filter_text in descripcion_data for filter_text in self.filter_descripcion_text_list):
                return False

        # Filtrar por rango de 'Fecha'
        fecha_index = model.index(source_row, self.column_indices.get('Fecha'), source_parent)
        fecha_data = model.data(fecha_index)

        if fecha_data and self.filter_fecha_inicio is not None and self.filter_fecha_fin is not None:
            fecha_data_qdatetime = QDateTime.fromString(fecha_data, "dd/MM/yyyy HH:mm")
            if not fecha_data_qdatetime.isValid():
                return False
            if not (self.filter_fecha_inicio <= fecha_data_qdatetime <= self.filter_fecha_fin):
                return False

        # Filtrar por 'Estatus'
        estatus_index = model.index(source_row, self.column_indices.get('Estatus'), source_parent)
        estatus_data = model.data(estatus_index)
        if self.filter_estatus_list and estatus_data not in self.filter_estatus_list:
            return False

        return True

class WorkerSignals(QObject):
    progress = pyqtSignal(int)
    error = pyqtSignal(str)
    finished = pyqtSignal()

class DownloadWorker(QRunnable):
    def __init__(self, fila, df_original, ruta_descarga, nombre_archivo, columna):
        super().__init__()
        self.fila = fila
        self.df_original = df_original
        self.ruta_descarga = ruta_descarga
        self.nombre_archivo = nombre_archivo
        self.columna = columna  # Columna específica del enlace
        self.signals = WorkerSignals()

    def run(self):
        """
        Ejecuta el proceso de descarga y conversión en el hilo.
        """
        try:
            # Obtener el enlace según la columna especificada
            enlace = self.df_original.iloc[self.fila][self.columna]

            if pd.notna(enlace) and isinstance(enlace, str):
                # Descargar el archivo
                response = requests.get(enlace, stream=True, timeout=10)
                response.raise_for_status()  # Verifica errores HTTP

                # Intentar detectar si es una imagen
                content_type = response.headers.get('Content-Type', '')
                is_image = 'image' in content_type or imghdr.what(None, h=response.content) is not None

                # Ruta completa del archivo
                ruta_archivo = os.path.join(self.ruta_descarga, self.nombre_archivo)

                if is_image:
                    # Convertir la imagen a PDF
                    image = Image.open(io.BytesIO(response.content))
                    ruta_pdf = ruta_archivo.replace(".pdf", ".pdf")
                    image.convert("RGB").save(ruta_pdf, "PDF")
                    ruta_archivo_final = ruta_pdf
                else:
                    # Guardar el archivo directamente si no es una imagen
                    with open(ruta_archivo, "wb") as file:
                        file.write(response.content)
                    ruta_archivo_final = ruta_archivo

                # Emitir señal de progreso por cada archivo descargado
                self.signals.progress.emit(1)

                # Opcional: Emitir señal con la ruta del archivo final si se necesita
                # self.signals.result.emit(ruta_archivo_final)
            else:
                # Emitir progreso si no hay enlace válido
                self.signals.progress.emit(1)

        except requests.ConnectionError:
            self.signals.error.emit(f"Error de conexión al descargar el archivo para la fila {self.fila}: Verifique su conexión a internet.")
        except requests.Timeout:
            self.signals.error.emit(f"Tiempo de espera agotado al intentar descargar el archivo para la fila {self.fila}: La conexión a internet es muy lenta.")
        except requests.RequestException as e:
            self.signals.error.emit(f"Error al descargar el archivo para la fila {self.fila}: {e}")
        except Exception as e:
            self.signals.error.emit(f"Error inesperado en la fila {self.fila}: {e}")

        # Emitir señal de finalización
        self.signals.finished.emit()

class Ui_MainWindow(QtWidgets.QMainWindow):
    cerrar_ventanas = pyqtSignal()  # Señal personalizada

    def __init__(self):
        super().__init__()

        self.thread_pool = QThreadPool()
        self.errores = []
        self.new_window = None  # Para almacenar la referencia de la nueva ventana
        self.cerrar_ventanas.connect(self.cerrar_ventana_secundaria)

        self.tareas_completadas = 0
        self.descargas_completadas = 0  # Contador para descargas completadas
        self.dataframes_descargados = []  # Lista para almacenar los DataFrames procesados
        self.soup_from_consulta = None
        self.formatted_name_from_consulta = None

        self.mutex = QMutex()  # Mutex para evitar problemas de concurrencia

        self.path_file = None
        self.df_original = None
        self.df_vista = None
        # Definir los nombres de columnas de fechas para cada vista
        self.columnas_fecha_concentrado = {
            1: 'Fecha Recepción',
            2: 'Fecha Factura',
            3: 'Fecha Autorización',
            4: 'Fecha Pagada'
        }

        self.columnas_fecha_desglosado = {
            1: 'FECHA RECEPCIÓN',
            2: 'FECHA FACTURA',
            3: 'FECHA AUTORIZACIÓN',
            4: 'FECHA PAGADO'
        }
        # Crear instancia del modelo proxy para filtrar el DataFrame
        self.proxy_model = CustomFilterProxyModel()
        self.proxy_model.setDynamicSortFilter(True)
        self.proxy_model_desglose = CustomFilterProxyModel()
        self.proxy_model_desglose.setDynamicSortFilter(True)
        self.todos_seleccionados = False  # Inicialmente, ningún checkbox está seleccionado
        self.todos_seleccionados_PDF = False  # Inicialmente, ningún checkbox está seleccionado

    def setupUi(self, MainWindow):
        self.MainWindow = MainWindow  # Guardar la referencia de MainWindow para utilizarla como parent

        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1000, 750)
        MainWindow.setMinimumSize(QtCore.QSize(700, 750))
        MainWindow.setWindowIcon(QIcon("C:\\Users\\noear\\Downloads\\Facturas_Octubre\\Octubre 2024\\favicon.ico"))  # Reemplaza con la ruta de tu ícono

        font = QtGui.QFont()
        font.setStrikeOut(False)
        MainWindow.setFont(font)
        MainWindow.setTabShape(QtWidgets.QTabWidget.TabShape.Rounded)
        self.centralwidget = QtWidgets.QWidget(parent=MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout(self.centralwidget)
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setContentsMargins(0, -1, -1, -1)
        self.horizontalLayout_3.setSpacing(0)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.icon_Only = QtWidgets.QWidget(parent=self.centralwidget)
        self.icon_Only.setMinimumSize(QtCore.QSize(50, 0))
        self.icon_Only.setMaximumSize(QtCore.QSize(50, 16777215))
        self.icon_Only.setStyleSheet("QWidget{\n"
"        background-color: #1C1C1C; /* Fondo oscuro */\n"
"        border-radius: 12px; /* Bordes redondeados para un toque moderno */\n"
"        padding: 10px; /* Relleno interno */\n"
"    }\n"
"\n"
"    /* Sombra sutil para darle profundidad */\n"
"    QWidget:hover {\n"
"        background-color: #1F1F1F; /* Cambia ligeramente el color al pasar el cursor */\n"
"    }\n"
"\n"
"    /* Efecto de sombra usando QFrame si es necesario */\n"
"    QFrame {\n"
"        background-color: #1C1C1C;\n"
"        border-radius: 12px;\n"
"    }")
        self.icon_Only.setObjectName("icon_Only")
        self.verticalLayout_7 = QtWidgets.QVBoxLayout(self.icon_Only)
        self.verticalLayout_7.setContentsMargins(0, 6, 0, 0)
        self.verticalLayout_7.setSpacing(0)
        self.verticalLayout_7.setObjectName("verticalLayout_7")
        spacerItem = QtWidgets.QSpacerItem(20, 15, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Fixed)
        self.verticalLayout_7.addItem(spacerItem)
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setContentsMargins(0, -1, 0, -1)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.home_tab = QtWidgets.QPushButton(parent=self.icon_Only)
        self.home_tab.setMinimumSize(QtCore.QSize(40, 60))
        self.home_tab.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.home_tab.setStyleSheet("QPushButton {\n"
"        background-color: 3A3A3A; /* Color de fondo oscuro */\n"
"        border: none;\n"
"        color: #FFFFFF; /* Color del ícono en blanco */\n"
"        padding: 15px;\n"
"        border-radius: 3px; /* Bordes redondeados */\n"
"    }\n"
"\n"
"    QPushButton:hover {\n"
"        background-color: #454545; /* Color al pasar el cursor */\n"
"    }\n"
"\n"
"    QPushButton:pressed {\n"
"        background-color: #424242; /* Color al hacer clic */\n"
"    }\n"
"\n"
"    QPushButton:checked {\n"
"        background-color: #FFFFFF; /* Color cuando está seleccionado (si se aplica) */\n"
"    }")
        self.home_tab.setText("")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/icons/Mesa de trabajo 1 copia.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        icon.addPixmap(QtGui.QPixmap(":/icons/homepngblack.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.On)
        self.home_tab.setIcon(icon)
        self.home_tab.setIconSize(QtCore.QSize(40, 40))
        self.home_tab.setCheckable(True)
        self.home_tab.setObjectName("home_tab")
        self.verticalLayout.addWidget(self.home_tab)
        self.filter_tab = QtWidgets.QPushButton(parent=self.icon_Only)
        self.filter_tab.setMinimumSize(QtCore.QSize(40, 60))
        self.filter_tab.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.filter_tab.setStyleSheet("QPushButton {\n"
"        background-color: 3A3A3A; /* Color de fondo oscuro */\n"
"        border: none;\n"
"        color: #FFFFFF; /* Color del ícono en blanco */\n"
"        padding: 15px;\n"
"        border-radius: 3px; /* Bordes redondeados */\n"
"    }\n"
"\n"
"    QPushButton:hover {\n"
"        background-color: #454545; /* Color al pasar el cursor */\n"
"    }\n"
"\n"
"    QPushButton:pressed {\n"
"        background-color: #424242; /* Color al hacer clic */\n"
"    }\n"
"\n"
"    QPushButton:checked {\n"
"        background-color: #FFFFFF; /* Color cuando está seleccionado (si se aplica) */\n"
"    }")
        self.filter_tab.setText("")
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/icons/Mesa de trabajo 1 copia 2.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        icon1.addPixmap(QtGui.QPixmap(":/icons/filterpngblack.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.On)
        self.filter_tab.setIcon(icon1)
        self.filter_tab.setIconSize(QtCore.QSize(30, 30))
        self.filter_tab.setCheckable(True)
        self.filter_tab.setObjectName("filter_tab")
        self.verticalLayout.addWidget(self.filter_tab)
        self.pushButton_2 = QtWidgets.QPushButton(parent=self.icon_Only)
        self.pushButton_2.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.pushButton_2.setStyleSheet("QPushButton {\n"
"        background-color: 3A3A3A; /* Color de fondo oscuro */\n"
"        border: none;\n"
"        color: #FFFFFF; /* Color del ícono en blanco */\n"
"        padding: 15px;\n"
"        border-radius: 3px; /* Bordes redondeados */\n"
"    }\n"
"\n"
"    QPushButton:hover {\n"
"        background-color: #454545; /* Color al pasar el cursor */\n"
"    }\n"
"\n"
"    QPushButton:pressed {\n"
"        background-color: #424242; /* Color al hacer clic */\n"
"    }\n"
"\n"
"    QPushButton:checked {\n"
"        background-color: #FFFFFF; /* Color cuando está seleccionado (si se aplica) */\n"
"    }")
        self.pushButton_2.setText("")
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(":/icons/Mesa de trabajo 1.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        icon2.addPixmap(QtGui.QPixmap(":/icons/exportpngblack.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.On)
        self.pushButton_2.setIcon(icon2)
        self.pushButton_2.setIconSize(QtCore.QSize(30, 30))
        self.pushButton_2.setCheckable(True)
        self.pushButton_2.setObjectName("pushButton_2")
        self.verticalLayout.addWidget(self.pushButton_2)
        self.verticalLayout_7.addLayout(self.verticalLayout)
        spacerItem1 = QtWidgets.QSpacerItem(20, 598, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        self.verticalLayout_7.addItem(spacerItem1)
        self.horizontalLayout_3.addWidget(self.icon_Only)
        self.stackedWidget = QtWidgets.QStackedWidget(parent=self.centralwidget)
        self.stackedWidget.setMinimumSize(QtCore.QSize(0, 0))
        self.stackedWidget.setMaximumSize(QtCore.QSize(350, 16777215))
        self.stackedWidget.setStyleSheet("QStackedWidget{\n"
"    background-color: rgb(255, 255, 255);\n"
"}\n"
"")
        self.stackedWidget.setObjectName("stackedWidget")
        self.HOME_stckW = QtWidgets.QWidget()
        self.HOME_stckW.setStyleSheet("QFrame {\n"
"    background-color: #F5F5F5;\n"
"    border-radius: 8px;\n"
"    padding: 5px;\n"
"}")
        self.HOME_stckW.setObjectName("HOME_stckW")
        self.verticalLayout_23 = QtWidgets.QVBoxLayout(self.HOME_stckW)
        self.verticalLayout_23.setObjectName("verticalLayout_23")
        self.frame_5 = QtWidgets.QFrame(parent=self.HOME_stckW)
        self.frame_5.setStyleSheet("QFrame {\n"
"    background-color: #F9F9F9;\n"
"    border-radius: 10px;\n"
"    padding: 15px;\n"
"}")
        self.frame_5.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.frame_5.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.frame_5.setObjectName("frame_5")
        self.verticalLayout_59 = QtWidgets.QVBoxLayout(self.frame_5)
        self.verticalLayout_59.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_59.setObjectName("verticalLayout_59")
        self.verticalLayout_58 = QtWidgets.QVBoxLayout()
        self.verticalLayout_58.setObjectName("verticalLayout_58")
        self.horizontalLayout_10 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_10.setContentsMargins(-1, 0, -1, -1)
        self.horizontalLayout_10.setObjectName("horizontalLayout_10")
        self.pushButton_selectHTML = QtWidgets.QPushButton(parent=self.frame_5)
        self.pushButton_selectHTML.setMinimumSize(QtCore.QSize(50, 55))
        self.pushButton_selectHTML.setMaximumSize(QtCore.QSize(16777215, 16777215))
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.pushButton_selectHTML.setFont(font)
        self.pushButton_selectHTML.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.pushButton_selectHTML.setWhatsThis("")
        self.pushButton_selectHTML.setStyleSheet("QPushButton {\n"
"    background-color: #333333; /* Fondo negro */\n"
"    color: #FFFFFF;\n"
"    font-size: 13px;\n"
"    font-weight: bold;\n"
"    border-radius: 8px;\n"
"    padding: 10px 20px;\n"
"    border: none;\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: #4D4D4D; /* Fondo gris oscuro al pasar el cursor */\n"
"}\n"
"\n"
"QPushButton:pressed {\n"
"    background-color: #222222; /* Fondo gris muy oscuro al presionar */\n"
"}\n"
"\n"
"QPushButton::before {\n"
"    margin-right: 8px;\n"
"}")
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap(":/icons/carpeta.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.pushButton_selectHTML.setIcon(icon3)
        self.pushButton_selectHTML.setIconSize(QtCore.QSize(25, 25))
        self.pushButton_selectHTML.setCheckable(True)
        self.pushButton_selectHTML.setObjectName("pushButton_selectHTML")
        self.horizontalLayout_10.addWidget(self.pushButton_selectHTML)
        self.pushButton_4 = QtWidgets.QPushButton(parent=self.frame_5)
        self.pushButton_4.setMinimumSize(QtCore.QSize(0, 55))
        self.pushButton_4.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.pushButton_4.setStyleSheet("QPushButton {\n"
                                        "    background-color: #333333; /* Fondo negro */\n"
                                        "    color: #FFFFFF;\n"
                                        "    font-size: 13px;\n"
                                        "    font-weight: bold;\n"
                                        "    border-radius: 8px;\n"
                                        "    padding: 10px 20px;\n"
                                        "    border: none;\n"
                                        "}\n"
                                        "\n"
                                        "QPushButton:hover {\n"
                                        "    background-color: #4D4D4D; /* Fondo gris oscuro al pasar el cursor */\n"
                                        "}\n"
                                        "\n"
                                        "QPushButton:pressed {\n"
                                        "    background-color: #222222; /* Fondo gris muy oscuro al presionar */\n"
                                        "}\n"
                                        "\n"
                                        "QPushButton::before {\n"
                                        "    margin-right: 8px;\n"
                                        "}")
        self.pushButton_4.setObjectName("pushButton_4")
        self.horizontalLayout_10.addWidget(self.pushButton_4)
        self.verticalLayout_58.addLayout(self.horizontalLayout_10)
        #cambios
        self.namefile_loadedHTML = QtWidgets.QTextEdit(parent=self.frame_5)
        self.namefile_loadedHTML.setMinimumSize(QtCore.QSize(0, 70))
        self.namefile_loadedHTML.setMaximumSize(QtCore.QSize(16777215, 70))
        self.namefile_loadedHTML.setStyleSheet("""
                                    QTextEdit {
                                        border: 1px solid #C0C0C0;
                                        border-radius: 5px;
                                        padding: 4px 8px; /* Ajustar el padding para alinearlo con el estilo anterior */
                                        background-color: #FCFCFC;
                                        font-size: 12px;
                                        color: #333333;
                                        height: 25px; /* Aunque el QTextEdit se adapta automáticamente, puedes usar height mínima */
                                    }

                                    QTextEdit:disabled {
                                        background-color: #F0F0F0; /* Fondo gris claro para los campos deshabilitados */
                                        color: #666666;
                                        border: 1px solid #D3D3D3;
                                    }
                                    """)
        self.namefile_loadedHTML.setReadOnly(True)
        self.namefile_loadedHTML.setObjectName("namefile_loadedHTML")
        self.namefile_loadedHTML.setPlaceholderText("Cargar archivo *.html ...")
        self.verticalLayout_58.addWidget(self.namefile_loadedHTML)
        self.verticalLayout_59.addLayout(self.verticalLayout_58)
        spacerItem2 = QtWidgets.QSpacerItem(20, 5, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Fixed)
        self.verticalLayout_59.addItem(spacerItem2)
        self.verticalLayout_57 = QtWidgets.QVBoxLayout()
        self.verticalLayout_57.setObjectName("verticalLayout_57")
        self.pushButton_Analizar = QtWidgets.QPushButton(parent=self.frame_5)
        self.pushButton_Analizar.setMinimumSize(QtCore.QSize(150, 45))
        self.pushButton_Analizar.setMaximumSize(QtCore.QSize(16777215, 16777215))
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.pushButton_Analizar.setFont(font)
        self.pushButton_Analizar.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.pushButton_Analizar.setStyleSheet("QPushButton {\n"
"    background-color: #333333; /* Fondo negro */\n"
"    color: #FFFFFF;\n"
"    font-size: 13px;\n"
"    font-weight: bold;\n"
"    border-radius: 8px;\n"
"    padding: 10px 20px;\n"
"    border: none;\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: #4D4D4D; /* Fondo gris oscuro al pasar el cursor */\n"
"}\n"
"\n"
"QPushButton:pressed {\n"
"    background-color: #222222; /* Fondo gris muy oscuro al presionar */\n"
"}")
        icon4 = QtGui.QIcon()
        icon4.addPixmap(QtGui.QPixmap(":/icons/archivo.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.pushButton_Analizar.setIcon(icon4)
        self.pushButton_Analizar.setObjectName("pushButton_Analizar")
        self.verticalLayout_57.addWidget(self.pushButton_Analizar)
        self.progressBar = QtWidgets.QProgressBar(parent=self.frame_5)
        self.progressBar.setMinimumSize(QtCore.QSize(0, 30))
        self.progressBar.setStyleSheet("QProgressBar {\n"
"    border: 1px solid #D0D0D0;\n"
"    border-radius: 8px; /* Bordes redondeados */\n"
"    background-color: #F0F0F0; /* Fondo más suave */\n"
"    height: 20px; /* Aumenta un poco la altura para mejor visibilidad */\n"
"    text-align: center; /* Muestra el texto centrado en la barra */\n"
"    color: #333333; /* Color del texto de progreso */\n"
"    font-weight: bold;\n"
"}\n"
"\n"
"/* Estilo para la parte de progreso (chunk) */\n"
"QProgressBar::chunk {\n"
"    border-radius: 8px; /* Bordes redondeados para un efecto moderno */\n"
"    background: qlineargradient(\n"
"        x1: 0, y1: 0, x2: 1, y2: 0,\n"
"        stop: 0 #4CAF50, /* Verde oscuro al inicio */\n"
"        stop: 1 #81C784 /* Verde claro al final */\n"
"    );\n"
"    margin: 1px; /* Añade un pequeño margen para un efecto de \"barra flotante\" */\n"
"}")
        self.progressBar.setProperty("value", 0)
        self.progressBar.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.progressBar.setInvertedAppearance(False)
        self.progressBar.setObjectName("progressBar")
        self.verticalLayout_57.addWidget(self.progressBar)
        self.verticalLayout_59.addLayout(self.verticalLayout_57)
        spacerItem3 = QtWidgets.QSpacerItem(20, 5, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Fixed)
        self.verticalLayout_59.addItem(spacerItem3)
        self.groupBox_InfofileHTML = QtWidgets.QGroupBox(parent=self.frame_5)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.groupBox_InfofileHTML.sizePolicy().hasHeightForWidth())
        self.groupBox_InfofileHTML.setSizePolicy(sizePolicy)
        self.groupBox_InfofileHTML.setMinimumSize(QtCore.QSize(0, 200))
        self.groupBox_InfofileHTML.setMaximumSize(QtCore.QSize(16777215, 16777215))
        font = QtGui.QFont()
        font.setFamily("Lato Black")
        font.setBold(True)
        font.setWeight(75)
        self.groupBox_InfofileHTML.setFont(font)
        self.groupBox_InfofileHTML.setStyleSheet("QGroupBox {\n"
"    font-size: 14px;\n"
"    font-weight: bold;\n"
"    color: #5A5A5A;\n"
"    border: 1px solid #D3D3D3;\n"
"    border-radius: 8px;\n"
"    margin-top: 10px;\n"
"    padding-top: 15px;\n"
"    background-color: #FFFFFF;\n"
"}\n"
"\n"
"QGroupBox::title {\n"
"    subcontrol-origin: margin;\n"
"    subcontrol-position: top left;\n"
"    padding: 0 5px;\n"
"    color: #333333;\n"
"    font-size: 13px;\n"
"}")
        self.groupBox_InfofileHTML.setObjectName("groupBox_InfofileHTML")
        self.verticalLayout_51 = QtWidgets.QVBoxLayout(self.groupBox_InfofileHTML)
        self.verticalLayout_51.setContentsMargins(-1, 0, -1, 0)
        self.verticalLayout_51.setSpacing(0)
        self.verticalLayout_51.setObjectName("verticalLayout_51")
        self.verticalLayout_21 = QtWidgets.QVBoxLayout()
        self.verticalLayout_21.setSpacing(0)
        self.verticalLayout_21.setObjectName("verticalLayout_21")
        self.label_amountFacturas = QtWidgets.QLabel(parent=self.groupBox_InfofileHTML)
        self.label_amountFacturas.setStyleSheet("QLabel {\n"
"    font-size: 12px;\n"
"    color: #555555;\n"
"    background-color: white;\n"
"    padding: 4px;\n"
"    margin: 4px;\n"
"}\n"
"")
        self.label_amountFacturas.setObjectName("label_amountFacturas")
        self.verticalLayout_21.addWidget(self.label_amountFacturas)
        self.lineEdit_amountFacturas = QtWidgets.QLineEdit(parent=self.groupBox_InfofileHTML)
        self.lineEdit_amountFacturas.setMinimumSize(QtCore.QSize(0, 30))
        self.lineEdit_amountFacturas.setStyleSheet("QLineEdit {\n"
"    border: 1px solid #C0C0C0;\n"
"    border-radius: 5px;\n"
"    padding-left: 8px;\n"
"    height: 25px;\n"
"    background-color: #FCFCFC;\n"
"    font-size: 12px;\n"
"    color: #333333;\n"
"}\n"
"\n"
"QLineEdit:disabled {\n"
"    background-color: #F0F0F0; /* Fondo gris claro para los campos deshabilitados */\n"
"    color: #666666;\n"
"    border: 1px solid #D3D3D3;\n"
"}\n"
"")
        self.lineEdit_amountFacturas.setText("")
        self.lineEdit_amountFacturas.setReadOnly(True)
        self.lineEdit_amountFacturas.setObjectName("lineEdit_amountFacturas")
        self.verticalLayout_21.addWidget(self.lineEdit_amountFacturas)
        self.label_amountMonto = QtWidgets.QLabel(parent=self.groupBox_InfofileHTML)
        self.label_amountMonto.setStyleSheet("QLabel {\n"
"    font-size: 12px;\n"
"    color: #555555;\n"
"    background-color: white;\n"
"    padding: 4px;\n"
"    margin: 4px;\n"
"}\n"
"")
        self.label_amountMonto.setObjectName("label_amountMonto")
        self.verticalLayout_21.addWidget(self.label_amountMonto)
        self.lineEdit_amountMonto = QtWidgets.QLineEdit(parent=self.groupBox_InfofileHTML)
        self.lineEdit_amountMonto.setMinimumSize(QtCore.QSize(0, 30))
        self.lineEdit_amountMonto.setStyleSheet("QLineEdit {\n"
"    border: 1px solid #C0C0C0;\n"
"    border-radius: 5px;\n"
"    padding-left: 8px;\n"
"    height: 25px;\n"
"    background-color: #FCFCFC;\n"
"    font-size: 12px;\n"
"    color: #333333;\n"
"}\n"
"\n"
"QLineEdit:disabled {\n"
"    background-color: #F0F0F0; /* Fondo gris claro para los campos deshabilitados */\n"
"    color: #666666;\n"
"    border: 1px solid #D3D3D3;\n"
"}")
        self.lineEdit_amountMonto.setText("")
        self.lineEdit_amountMonto.setReadOnly(True)
        self.lineEdit_amountMonto.setObjectName("lineEdit_amountMonto")
        self.verticalLayout_21.addWidget(self.lineEdit_amountMonto)
        self.label_amountConceptos = QtWidgets.QLabel(parent=self.groupBox_InfofileHTML)
        self.label_amountConceptos.setStyleSheet("QLabel {\n"
"    font-size: 12px;\n"
"    color: #555555;\n"
"    background-color: white;\n"
"    padding: 4px;\n"
"    margin: 4px;\n"
"}\n"
"")
        self.label_amountConceptos.setObjectName("label_amountConceptos")
        self.verticalLayout_21.addWidget(self.label_amountConceptos)
        self.lineEdit_amountConcepto = QtWidgets.QLineEdit(parent=self.groupBox_InfofileHTML)
        self.lineEdit_amountConcepto.setMinimumSize(QtCore.QSize(0, 30))
        self.lineEdit_amountConcepto.setStyleSheet("QLineEdit {\n"
"    border: 1px solid #C0C0C0;\n"
"    border-radius: 5px;\n"
"    padding-left: 8px;\n"
"    height: 25px;\n"
"    background-color: #FCFCFC;\n"
"    font-size: 12px;\n"
"    color: #333333;\n"
"}\n"
"\n"
"QLineEdit:disabled {\n"
"    background-color: #F0F0F0; /* Fondo gris claro para los campos deshabilitados */\n"
"    color: #666666;\n"
"    border: 1px solid #D3D3D3;\n"
"}")
        self.lineEdit_amountConcepto.setText("")
        self.lineEdit_amountConcepto.setReadOnly(True)
        self.lineEdit_amountConcepto.setObjectName("lineEdit_amountConcepto")
        self.verticalLayout_21.addWidget(self.lineEdit_amountConcepto)
        self.verticalLayout_51.addLayout(self.verticalLayout_21)
        spacerItem4 = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.MinimumExpanding)
        self.verticalLayout_51.addItem(spacerItem4)
        self.EXCEL_groupBox_Descarga_2 = QtWidgets.QGroupBox(parent=self.groupBox_InfofileHTML)
        self.EXCEL_groupBox_Descarga_2.setMaximumSize(QtCore.QSize(16777215, 200))
        font = QtGui.QFont()
        font.setFamily("Lato Black")
        font.setBold(True)
        font.setWeight(75)
        self.EXCEL_groupBox_Descarga_2.setFont(font)
        self.EXCEL_groupBox_Descarga_2.setStyleSheet("QGroupBox#EXCEL_groupBox_Descarga {\n"
"    background-color: #F7F9FC;  /* Fondo gris muy claro */\n"
"    border: 1px solid #D0D7DF;  /* Borde suave para un contorno definido */\n"
"    border-radius: 8px;  /* Esquinas ligeramente redondeadas */\n"
"    padding: 15px;\n"
"    margin-top: 10px;\n"
"}\n"
"\n"
"QGroupBox::title {\n"
"    subcontrol-origin: margin;\n"
"    subcontrol-position: top left;\n"
"    padding: 0 10px;\n"
"    color: #006400;  /* Verde para el título */\n"
"    font-size: 13px;\n"
"    font-weight: 600;\n"
"    border-radius: 5px;\n"
"}")
        self.EXCEL_groupBox_Descarga_2.setObjectName("EXCEL_groupBox_Descarga_2")
        self.verticalLayout_55 = QtWidgets.QVBoxLayout(self.EXCEL_groupBox_Descarga_2)
        self.verticalLayout_55.setContentsMargins(11, 0, 11, 10)
        self.verticalLayout_55.setSpacing(0)
        self.verticalLayout_55.setObjectName("verticalLayout_55")
        self.EXCEL_checkBox_RESUMEN_2 = QtWidgets.QCheckBox(parent=self.EXCEL_groupBox_Descarga_2)
        self.EXCEL_checkBox_RESUMEN_2.setStyleSheet("/* Estilo general para QCheckBox */\n"
"QCheckBox {\n"
"    font-size: 13px;\n"
"    background-color: white;\n"
"    color: #333333;\n"
"    padding: 10px;\n"
"}\n"
"\n"
"")
        self.EXCEL_checkBox_RESUMEN_2.setObjectName("EXCEL_checkBox_RESUMEN_2")
        self.verticalLayout_55.addWidget(self.EXCEL_checkBox_RESUMEN_2)
        self.EXCEL_checkBox_DESGLOSADO_2 = QtWidgets.QCheckBox(parent=self.EXCEL_groupBox_Descarga_2)
        self.EXCEL_checkBox_DESGLOSADO_2.setToolTip("")
        self.EXCEL_checkBox_DESGLOSADO_2.setToolTipDuration(-1)
        self.EXCEL_checkBox_DESGLOSADO_2.setStyleSheet("/* Estilo general para QCheckBox */\n"
"QCheckBox {\n"
"    font-size: 13px;\n"
"    background-color: white;\n"
"    color: #333333;\n"
"    padding: 10px;\n"
"}\n"
"\n"
"")
        self.EXCEL_checkBox_DESGLOSADO_2.setObjectName("EXCEL_checkBox_DESGLOSADO_2")
        self.verticalLayout_55.addWidget(self.EXCEL_checkBox_DESGLOSADO_2)
        self.EXCEL_btn_Descargar_2 = QtWidgets.QPushButton(parent=self.EXCEL_groupBox_Descarga_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.EXCEL_btn_Descargar_2.sizePolicy().hasHeightForWidth())
        self.EXCEL_btn_Descargar_2.setSizePolicy(sizePolicy)
        self.EXCEL_btn_Descargar_2.setMinimumSize(QtCore.QSize(0, 0))
        self.EXCEL_btn_Descargar_2.setMaximumSize(QtCore.QSize(16777215, 40))
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.EXCEL_btn_Descargar_2.setFont(font)
        self.EXCEL_btn_Descargar_2.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.EXCEL_btn_Descargar_2.setStyleSheet("QPushButton#EXCEL_btn_Descargar_2 {\n"
"    background-color: #4CAF50;  /* Color verde moderno */\n"
"    color: white;\n"
"    border-radius: 5px;\n"
"    padding: 8px;\n"
"    font-weight: bold;\n"
"}\n"
"\n"
"QPushButton#EXCEL_btn_Descargar_2:hover {\n"
"    background-color: #45A049;  /* Color ligeramente más oscuro al pasar el cursor */\n"
"}")
        icon5 = QtGui.QIcon()
        icon5.addPixmap(QtGui.QPixmap(":/icons/roundimgexcel.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.EXCEL_btn_Descargar_2.setIcon(icon5)
        self.EXCEL_btn_Descargar_2.setIconSize(QtCore.QSize(15, 15))
        self.EXCEL_btn_Descargar_2.setObjectName("EXCEL_btn_Descargar_2")
        self.verticalLayout_55.addWidget(self.EXCEL_btn_Descargar_2)
        self.verticalLayout_51.addWidget(self.EXCEL_groupBox_Descarga_2)
        self.label_versionSoftware = QtWidgets.QLabel(parent=self.groupBox_InfofileHTML)
        self.label_versionSoftware.setStyleSheet("QLabel {\n"
"    font-size: 11px;\n"
"    color: #555555;\n"
"    background-color: white;\n"
"    padding: 5px;\n"
"    margin: 5px;\n"
"}\n"
"")
        self.label_versionSoftware.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_versionSoftware.setObjectName("label_versionSoftware")
        self.verticalLayout_51.addWidget(self.label_versionSoftware)
        self.verticalLayout_59.addWidget(self.groupBox_InfofileHTML)
        self.verticalLayout_23.addWidget(self.frame_5)
        self.stackedWidget.addWidget(self.HOME_stckW)
        self.FILTRO_stckW = QtWidgets.QWidget()
        self.FILTRO_stckW.setStyleSheet("QWidget{\n"
"    background-color: rgb(255, 255, 255);\n"
"}\n"
"")
        self.FILTRO_stckW.setObjectName("FILTRO_stckW")
        self.verticalLayout_25 = QtWidgets.QVBoxLayout(self.FILTRO_stckW)
        self.verticalLayout_25.setObjectName("verticalLayout_25")
        self.frame_6 = QtWidgets.QFrame(parent=self.FILTRO_stckW)
        self.frame_6.setStyleSheet("QFrame {\n"
"    background-color: #F9F9F9;\n"
"    border-radius: 10px;\n"
"    padding: 10px;\n"
"}")
        self.frame_6.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.frame_6.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.frame_6.setObjectName("frame_6")
        self.verticalLayout_5 = QtWidgets.QVBoxLayout(self.frame_6)
        self.verticalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_5.setSpacing(7)
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.label_tituloPDF_2 = QtWidgets.QLabel(parent=self.frame_6)
        self.label_tituloPDF_2.setMaximumSize(QtCore.QSize(16777215, 65))
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.label_tituloPDF_2.setFont(font)
        self.label_tituloPDF_2.setStyleSheet("QLabel {\n"
"    font-size: 20px;\n"
"    font-weight: bold;\n"
"    color: #FFFFFF;  /* Texto en blanco para contraste */\n"
"    background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #191970, stop:1 #3A5FCD);  /* Degradado de rojo oscuro */\n"
"    padding: 10px 15px;\n"
"    border-radius: 8px;\n"
"    letter-spacing: 1px;\n"
"    text-align: center;\n"
"    margin-bottom: 5px;\n"
"}\n"
"\n"
"QLabel::after {\n"
"    content: \"\";\n"
"    display: block;\n"
"    margin: 8px auto;\n"
"    width: 50px;  /* Ancho de la línea */\n"
"    height: 3px;  /* Grosor de la línea */\n"
"    background-color: #B22222;  /* Mismo color que el degradado para cohesión */\n"
"    border-radius: 1px;\n"
"    opacity: 0.8;  /* Ligeramente translúcido */\n"
"}")
        self.label_tituloPDF_2.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_tituloPDF_2.setObjectName("label_tituloPDF_2")
        self.verticalLayout_5.addWidget(self.label_tituloPDF_2)
        self.frame_2 = QtWidgets.QFrame(parent=self.frame_6)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.frame_2.sizePolicy().hasHeightForWidth())
        self.frame_2.setSizePolicy(sizePolicy)
        self.frame_2.setMinimumSize(QtCore.QSize(0, 295))
        self.frame_2.setStyleSheet("background-color: rgb(255, 255, 255);")
        self.frame_2.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.frame_2.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.frame_2.setObjectName("frame_2")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout(self.frame_2)
        self.verticalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_4.setSpacing(0)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.label__filterObra = QtWidgets.QLabel(parent=self.frame_2)
        self.label__filterObra.setStyleSheet("QLabel {\n"
"    font-size: 12px;\n"
"    color: #555555;\n"
"    padding: 4px;\n"
"    margin: 4px;\n"
"}\n"
"")
        self.label__filterObra.setObjectName("label__filterObra")
        self.verticalLayout_4.addWidget(self.label__filterObra)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setContentsMargins(0, -1, -1, -1)
        self.horizontalLayout.setSpacing(10)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.pushButton__filterObra = QtWidgets.QPushButton(parent=self.frame_2)
        self.pushButton__filterObra.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.pushButton__filterObra.setStyleSheet("QPushButton {\n"
"    image: url(:/icons/checkbox-icon-512x512-kv3qo5ui.png);\n"
"    width: 20px;\n"
"    height: 20px;\n"
"    border: 1px solid #CCCCCC;\n"
"    border-radius: 5px;\n"
"    padding: 5px;\n"
"    background-color: #F9F9F9; /* Fondo claro */\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: #E6E6E6; /* Color al pasar el mouse */\n"
"    border: 1px solid #BBBBBB;\n"
"}\n"
"\n"
"QPushButton:pressed {\n"
"    background-color: #D4D4D4; /* Color cuando está presionado */\n"
"    border: 1px solid #AAAAAA;\n"
"}")
        self.pushButton__filterObra.setText("")
        self.pushButton__filterObra.setObjectName("pushButton__filterObra")
        self.horizontalLayout.addWidget(self.pushButton__filterObra)
        self.lineEdit_filterObra = QtWidgets.QLineEdit(parent=self.frame_2)
        self.lineEdit_filterObra.setMinimumSize(QtCore.QSize(0, 30))
        font = QtGui.QFont()
        self.lineEdit_filterObra.setFont(font)
        self.lineEdit_filterObra.setStyleSheet("QLineEdit {\n"
"    border: 1px solid #DADADA;\n"
"    border-radius: 5px;\n"
"    padding: 5px;\n"
"    background-color: #F7F7F7;\n"
"    color: #333;\n"
"}\n"
"\n"
"QLineEdit:focus {\n"
"    border: 1px solid #4A90E2;  /* Azul al enfocar */\n"
"    background-color: #FFFFFF;\n"
"}")
        self.lineEdit_filterObra.setText("")
        self.lineEdit_filterObra.setReadOnly(False)
        self.lineEdit_filterObra.setClearButtonEnabled(True)
        self.lineEdit_filterObra.setObjectName("lineEdit_filterObra")
        self.horizontalLayout.addWidget(self.lineEdit_filterObra)
        self.verticalLayout_4.addLayout(self.horizontalLayout)
        self.label__filterProveedor = QtWidgets.QLabel(parent=self.frame_2)
        self.label__filterProveedor.setStyleSheet("QLabel {\n"
"    font-size: 12px;\n"
"    color: #555555;\n"
"    padding: 4px;\n"
"    margin: 4px;\n"
"}\n"
"")
        self.label__filterProveedor.setObjectName("label__filterProveedor")
        self.verticalLayout_4.addWidget(self.label__filterProveedor)
        self.horizontalLayout_11 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_11.setContentsMargins(0, -1, -1, -1)
        self.horizontalLayout_11.setSpacing(10)
        self.horizontalLayout_11.setObjectName("horizontalLayout_11")
        self.pushButton_filterProveedor = QtWidgets.QPushButton(parent=self.frame_2)
        self.pushButton_filterProveedor.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.pushButton_filterProveedor.setStyleSheet("QPushButton {\n"
"    image: url(:/icons/checkbox-icon-512x512-kv3qo5ui.png);\n"
"    width: 20px;\n"
"    height: 20px;\n"
"    border: 1px solid #CCCCCC;\n"
"    border-radius: 5px;\n"
"    padding: 5px;\n"
"    background-color: #F9F9F9; /* Fondo claro */\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: #E6E6E6; /* Color al pasar el mouse */\n"
"    border: 1px solid #BBBBBB;\n"
"}\n"
"\n"
"QPushButton:pressed {\n"
"    background-color: #D4D4D4; /* Color cuando está presionado */\n"
"    border: 1px solid #AAAAAA;\n"
"}")
        self.pushButton_filterProveedor.setText("")
        self.pushButton_filterProveedor.setObjectName("pushButton_filterProveedor")
        self.horizontalLayout_11.addWidget(self.pushButton_filterProveedor)
        self.lineEdit__filterProveedor = QtWidgets.QLineEdit(parent=self.frame_2)
        self.lineEdit__filterProveedor.setMinimumSize(QtCore.QSize(0, 30))
        font = QtGui.QFont()
        self.lineEdit__filterProveedor.setFont(font)
        self.lineEdit__filterProveedor.setStyleSheet("QLineEdit {\n"
"    border: 1px solid #DADADA;\n"
"    border-radius: 5px;\n"
"    padding: 5px;\n"
"    background-color: #F7F7F7;\n"
"    color: #333;\n"
"}\n"
"\n"
"QLineEdit:focus {\n"
"    border: 1px solid #4A90E2;  /* Azul al enfocar */\n"
"    background-color: #FFFFFF;\n"
"}\n"
"")
        self.lineEdit__filterProveedor.setText("")
        self.lineEdit__filterProveedor.setReadOnly(False)
        self.lineEdit__filterProveedor.setClearButtonEnabled(True)
        self.lineEdit__filterProveedor.setObjectName("lineEdit__filterProveedor")
        self.horizontalLayout_11.addWidget(self.lineEdit__filterProveedor)
        self.verticalLayout_4.addLayout(self.horizontalLayout_11)
        self.label_filterResidente = QtWidgets.QLabel(parent=self.frame_2)
        self.label_filterResidente.setStyleSheet("QLabel {\n"
"    font-size: 12px;\n"
"    color: #555555;\n"
"    padding: 4px;\n"
"    margin: 4px;\n"
"}\n"
"")
        self.label_filterResidente.setObjectName("label_filterResidente")
        self.verticalLayout_4.addWidget(self.label_filterResidente)
        self.horizontalLayout_12 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_12.setContentsMargins(0, -1, -1, -1)
        self.horizontalLayout_12.setSpacing(10)
        self.horizontalLayout_12.setObjectName("horizontalLayout_12")
        self.pushButton_filterResidente = QtWidgets.QPushButton(parent=self.frame_2)
        self.pushButton_filterResidente.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.pushButton_filterResidente.setStyleSheet("QPushButton {\n"
"    image: url(:/icons/checkbox-icon-512x512-kv3qo5ui.png);\n"
"    width: 20px;\n"
"    height: 20px;\n"
"    border: 1px solid #CCCCCC;\n"
"    border-radius: 5px;\n"
"    padding: 5px;\n"
"    background-color: #F9F9F9; /* Fondo claro */\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: #E6E6E6; /* Color al pasar el mouse */\n"
"    border: 1px solid #BBBBBB;\n"
"}\n"
"\n"
"QPushButton:pressed {\n"
"    background-color: #D4D4D4; /* Color cuando está presionado */\n"
"    border: 1px solid #AAAAAA;\n"
"}")
        self.pushButton_filterResidente.setText("")
        self.pushButton_filterResidente.setObjectName("pushButton_filterResidente")
        self.horizontalLayout_12.addWidget(self.pushButton_filterResidente)
        self.lineEdit__filterResidente = QtWidgets.QLineEdit(parent=self.frame_2)
        self.lineEdit__filterResidente.setMinimumSize(QtCore.QSize(0, 30))
        font = QtGui.QFont()
        self.lineEdit__filterResidente.setFont(font)
        self.lineEdit__filterResidente.setStyleSheet("QLineEdit {\n"
"    border: 1px solid #DADADA;\n"
"    border-radius: 5px;\n"
"    padding: 5px;\n"
"    background-color: #F7F7F7;\n"
"    color: #333;\n"
"}\n"
"\n"
"QLineEdit:focus {\n"
"    border: 1px solid #4A90E2;  /* Azul al enfocar */\n"
"    background-color: #FFFFFF;\n"
"}\n"
"\n"
"")
        self.lineEdit__filterResidente.setText("")
        self.lineEdit__filterResidente.setReadOnly(False)
        self.lineEdit__filterResidente.setClearButtonEnabled(True)
        self.lineEdit__filterResidente.setObjectName("lineEdit__filterResidente")
        self.horizontalLayout_12.addWidget(self.lineEdit__filterResidente)
        self.verticalLayout_4.addLayout(self.horizontalLayout_12)

        self.label_filterNumero = QtWidgets.QLabel(parent=self.frame_2)
        self.label_filterNumero.setStyleSheet("QLabel {\n"
"    font-size: 12px;\n"
"    color: #555555;\n"
"    padding: 4px;\n"
"    margin: 4px;\n"
"}\n"
"")
        self.label_filterNumero.setObjectName("label_filterNumero")
        self.verticalLayout_4.addWidget(self.label_filterNumero)
        self.horizontalLayout_16 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_16.setContentsMargins(0, -1, -1, -1)
        self.horizontalLayout_16.setSpacing(10)
        self.horizontalLayout_16.setObjectName("horizontalLayout_16")
        self.lineEdit__filterNumero = QtWidgets.QLineEdit(parent=self.frame_2)
        self.lineEdit__filterNumero.setMinimumSize(QtCore.QSize(0, 30))
        font = QtGui.QFont()
        self.lineEdit__filterNumero.setFont(font)
        self.lineEdit__filterNumero.setStyleSheet("QLineEdit {\n"
                                                  "    border: 1px solid #DADADA;\n"
                                                  "    border-radius: 5px;\n"
                                                  "    padding: 5px;\n"
                                                  "    background-color: #F7F7F7;\n"
                                                  "    color: #333;\n"
                                                  "}\n"
                                                  "\n"
                                                  "QLineEdit:focus {\n"
                                                  "    border: 1px solid #4A90E2;  /* Azul al enfocar */\n"
                                                  "    background-color: #FFFFFF;\n"
                                                  "}\n"
                                                  "")
        self.lineEdit__filterNumero.setText("")
        self.lineEdit__filterNumero.setReadOnly(False)
        self.lineEdit__filterNumero.setClearButtonEnabled(True)
        self.lineEdit__filterNumero.setObjectName("lineEdit__filterNumero")
        self.horizontalLayout_16.addWidget(self.lineEdit__filterNumero)
        self.verticalLayout_4.addLayout(self.horizontalLayout_16)

        self.label_filterDescrip = QtWidgets.QLabel(parent=self.frame_2)
        self.label_filterDescrip.setStyleSheet("QLabel {\n"
                                              "    font-size: 12px;\n"
                                              "    color: #555555;\n"
                                              "    padding: 4px;\n"
                                              "    margin: 4px;\n"
                                              "}\n"
                                              "")
        self.label_filterDescrip.setObjectName("label_filterDescrip")
        self.verticalLayout_4.addWidget(self.label_filterDescrip)
        self.horizontalLayout_17 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_17.setContentsMargins(0, -1, -1, -1)
        self.horizontalLayout_17.setSpacing(10)
        self.horizontalLayout_17.setObjectName("horizontalLayout_17")
        self.lineEdit__filterDescrip = QtWidgets.QLineEdit(parent=self.frame_2)
        self.lineEdit__filterDescrip.setMinimumSize(QtCore.QSize(0, 30))
        font = QtGui.QFont()
        self.lineEdit__filterDescrip.setFont(font)
        self.lineEdit__filterDescrip.setStyleSheet("QLineEdit {\n"
                                                  "    border: 1px solid #DADADA;\n"
                                                  "    border-radius: 5px;\n"
                                                  "    padding: 5px;\n"
                                                  "    background-color: #F7F7F7;\n"
                                                  "    color: #333;\n"
                                                  "}\n"
                                                  "\n"
                                                  "QLineEdit:focus {\n"
                                                  "    border: 1px solid #4A90E2;  /* Azul al enfocar */\n"
                                                  "    background-color: #FFFFFF;\n"
                                                  "}\n"
                                                  "")
        self.lineEdit__filterDescrip.setText("")
        self.lineEdit__filterDescrip.setReadOnly(False)
        self.lineEdit__filterDescrip.setClearButtonEnabled(True)
        self.lineEdit__filterDescrip.setObjectName("lineEdit__filterDescrip")
        self.horizontalLayout_17.addWidget(self.lineEdit__filterDescrip)
        self.verticalLayout_4.addLayout(self.horizontalLayout_17)


        self.verticalLayout_5.addWidget(self.frame_2)
        self.ESTATUS = QtWidgets.QGroupBox(parent=self.frame_6)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.MinimumExpanding, QtWidgets.QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.ESTATUS.sizePolicy().hasHeightForWidth())
        self.ESTATUS.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Lato Black")
        font.setBold(True)
        font.setWeight(75)
        self.ESTATUS.setFont(font)
        self.ESTATUS.setStyleSheet("QGroupBox {\n"
"    background-color: #FAFAFA;  /* Fondo gris muy claro */\n"
"    border: 1px solid #D3D3D3;\n"
"    border-radius: 6px;\n"
"    padding: 10px;\n"
"    margin-top: 10px;\n"
"}\n"
"\n"
"QGroupBox::title {\n"
"    subcontrol-origin: margin;\n"
"    subcontrol-position: top left;\n"
"    padding: 0 5px;\n"
"    color: #4A90E2;  /* Azul suave */\n"
"    font-size: 13px;\n"
"    font-weight: bold;\n"
"}")
        self.ESTATUS.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.ESTATUS.setCheckable(False)
        self.ESTATUS.setChecked(False)
        self.ESTATUS.setObjectName("ESTATUS")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.ESTATUS)
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_3.setSpacing(6)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.listView = QtWidgets.QListView(parent=self.ESTATUS)
        self.listView.setStyleSheet("QListView {\n"
"    background-color: #FFFFFF;\n"
"    border: 1px solid #D3D3D3;\n"
"    border-radius: 5px;\n"
"    padding: 5px;\n"
"    color: #333;\n"
"}")
        self.listView.setObjectName("listView")
        self.verticalLayout_3.addWidget(self.listView)
        self.pushButton_3 = QtWidgets.QPushButton(parent=self.ESTATUS)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pushButton_3.sizePolicy().hasHeightForWidth())
        self.pushButton_3.setSizePolicy(sizePolicy)
        self.pushButton_3.setMinimumSize(QtCore.QSize(0, 25))
        self.pushButton_3.setMaximumSize(QtCore.QSize(16777215, 30))
        font = QtGui.QFont()
        font.setFamily("Lato Black")
        font.setBold(True)
        font.setWeight(75)
        self.pushButton_3.setFont(font)
        self.pushButton_3.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.pushButton_3.setStyleSheet("QPushButton {\n"
"    background-color: #333333; /* Fondo negro */\n"
"    color: #FFFFFF;\n"
"    font-size: 13px;\n"
"    font-weight: bold;\n"
"    border-radius: 8px;\n"
"    border: none;\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: #4D4D4D; /* Fondo gris oscuro al pasar el cursor */\n"
"}\n"
"\n"
"QPushButton:pressed {\n"
"    background-color: #222222; /* Fondo gris muy oscuro al presionar */\n"
"}")
        self.pushButton_3.setObjectName("pushButton_3")
        self.verticalLayout_3.addWidget(self.pushButton_3)
        self.verticalLayout_5.addWidget(self.ESTATUS)
        self.FECHA = QtWidgets.QGroupBox(parent=self.frame_6)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.FECHA.sizePolicy().hasHeightForWidth())
        self.FECHA.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Lato Black")
        font.setBold(True)
        font.setWeight(75)
        self.FECHA.setFont(font)
        self.FECHA.setStyleSheet("""
            QGroupBox {
                background-color: #FAFAFA;  /* Fondo gris muy claro */
                border: 1px solid #D3D3D3;
                border-radius: 6px;
                padding: 10px;
                margin-top: 10px;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
                color: #4A90E2;  /* Azul suave */
                font-size: 13px;
                font-weight: bold;
            }
        """)
        self.FECHA.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.FECHA.setCheckable(False)
        self.FECHA.setChecked(False)
        self.FECHA.setObjectName("FECHA")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.FECHA)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setSpacing(5)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.horizontalLayout_13 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_13.setObjectName("horizontalLayout_13")
        self.label_amountFacturas_4 = QtWidgets.QLabel(parent=self.FECHA)
        font = QtGui.QFont()
        font.setFamily("Lato Black")
        font.setBold(True)
        font.setWeight(75)
        self.label_amountFacturas_4.setFont(font)
        self.label_amountFacturas_4.setStyleSheet("QLabel {\n"
"    font-weight: bold;\n"
"    color: #333333;\n"
"    padding: 2px 5px;\n"
"    background-color: transparent;\n"
"}\n"
"")
        self.label_amountFacturas_4.setObjectName("label_amountFacturas_4")
        self.horizontalLayout_13.addWidget(self.label_amountFacturas_4)
        self.dateEdit = QtWidgets.QDateEdit(parent=self.FECHA)
        self.dateEdit.setMinimumSize(QtCore.QSize(150, 0))
        self.dateEdit.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.dateEdit.setStyle(QStyleFactory.create("WindowsVista"))
        self.dateEdit.setStyleSheet("""
            QDateEdit {
                border: 1px solid #CCCCCC;
                border-radius: 5px;
                padding: 5px;
                background-color: #FFFFFF;
                color: #000000;  /* Cambiado a negro para mejor contraste */
            }

            QDateEdit::drop-down {
                padding: 5px;
                image: url(:/icons/arrow-drop-down-big.png);
                width: 20px;
                height: 20px;
            }

            QDateEdit QAbstractItemView {
                background-color: #FFFFFF;  /* Fondo blanco para la vista desplegable */
                color: #000000;  /* Texto negro para mejor visibilidad */
                selection-background-color: #90CAF9;  /* Fondo azul claro para selección */
                selection-color: #FFFFFF;  /* Texto blanco para elementos seleccionados */
            }

            QDateEdit::hover {
                background-color: #E6E6E6;
            }

            QDateEdit::pressed {
                background-color: #D4D4D4;
            }
            
               /* Navigation Buttons (Previous and Next Month) */
            QCalendarWidget QToolButton {
                background-color: #F0F0F0;
                color: #333333;
                font-weight: bold;
                padding: 5px;
                width: 30px;
                border: 1px solid #CCCCCC;
                border-radius: 12px;  /* Botones más redondeados */
            }

            QCalendarWidget QToolButton:hover {
                background-color: #D3D3D3;
            }
    
            QCalendarWidget QToolButton:pressed {
                background-color: #3E8EDE;
                color: #FFFFFF;
            }
        
        
            QCalendarWidget QAbstractItemView:disabled {
                color: #bfbfbf;
            }
        
            /* Month and Year Display */
            QCalendarWidget QWidget {
                background-color: #FFFFFF;
                alternate-background-color: #E0E0E0;
                color: #000000;
                font-weight: bold;
                min-width: 60px;
            }          
            
        """)
        self.dateEdit.setCurrentSection(QtWidgets.QDateTimeEdit.Section.DaySection)
        self.dateEdit.setCalendarPopup(True)
        self.dateEdit.setCurrentSectionIndex(0)
        self.dateEdit.setObjectName("dateEdit")
        self.horizontalLayout_13.addWidget(self.dateEdit)
        self.verticalLayout_2.addLayout(self.horizontalLayout_13)
        self.horizontalLayout_14 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_14.setObjectName("horizontalLayout_14")
        self.label_amountFacturas_5 = QtWidgets.QLabel(parent=self.FECHA)
        font = QtGui.QFont()
        font.setFamily("Lato Black")
        font.setBold(True)
        font.setWeight(75)
        self.label_amountFacturas_5.setFont(font)
        self.label_amountFacturas_5.setStyleSheet("QLabel {\n"
"    font-weight: bold;\n"
"    color: #333333;\n"
"    padding: 2px 5px;\n"
"    background-color: transparent;\n"
"}\n"
"")
        self.label_amountFacturas_5.setObjectName("label_amountFacturas_5")
        self.horizontalLayout_14.addWidget(self.label_amountFacturas_5)
        self.dateEdit_2 = QtWidgets.QDateEdit(parent=self.FECHA)
        self.dateEdit_2.setMinimumSize(QtCore.QSize(150, 0))
        self.dateEdit_2.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.dateEdit_2.setStyleSheet("""
            QDateEdit {
                border: 1px solid #CCCCCC;
                border-radius: 5px;
                padding: 5px;
                background-color: #FFFFFF;
                color: #000000;  /* Cambiado a negro para mejor contraste */
            }

            QDateEdit::drop-down {
                padding: 5px;
                image: url(:/icons/arrow-drop-down-big.png);
                width: 20px;
                height: 20px;
            }

            QDateEdit QAbstractItemView {
                background-color: #FFFFFF;  /* Fondo blanco para la vista desplegable */
                color: #000000;  /* Texto negro para mejor visibilidad */
                selection-background-color: #90CAF9;  /* Fondo azul claro para selección */
                selection-color: #FFFFFF;  /* Texto blanco para elementos seleccionados */
            }

            QDateEdit::hover {
                background-color: #E6E6E6;
            }

            QDateEdit::pressed {
                background-color: #D4D4D4;
            }

               /* Navigation Buttons (Previous and Next Month) */
            QCalendarWidget QToolButton {
                background-color: #F0F0F0;
                color: #333333;
                font-weight: bold;
                padding: 5px;
                width: 30px;
                border: 1px solid #CCCCCC;
                border-radius: 12px;  /* Botones más redondeados */
            }

            QCalendarWidget QToolButton:hover {
                background-color: #D3D3D3;
            }

            QCalendarWidget QToolButton:pressed {
                background-color: #3E8EDE;
                color: #FFFFFF;
            }


            QCalendarWidget QAbstractItemView:disabled {
                color: #bfbfbf;
            }

            /* Month and Year Display */
            QCalendarWidget QWidget {
                background-color: #FFFFFF;
                alternate-background-color: #E0E0E0;
                color: #000000;
                font-weight: bold;
                min-width: 70px;
            }          

        """)
        self.dateEdit_2.setButtonSymbols(QtWidgets.QAbstractSpinBox.ButtonSymbols.PlusMinus)
        self.dateEdit_2.setAccelerated(True)
        self.dateEdit_2.setCalendarPopup(True)
        self.dateEdit_2.setTimeSpec(QtCore.Qt.TimeSpec.LocalTime)
        self.dateEdit_2.setObjectName("dateEdit_2")
        self.horizontalLayout_14.addWidget(self.dateEdit_2)
        self.verticalLayout_2.addLayout(self.horizontalLayout_14)
        self.comboBox_FECHA = QtWidgets.QComboBox(parent=self.FECHA)
        self.comboBox_FECHA.setMinimumSize(QtCore.QSize(100, 25))
        self.comboBox_FECHA.setMaximumSize(QtCore.QSize(16777215, 30))
        self.comboBox_FECHA.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.comboBox_FECHA.setStyle(QStyleFactory.create("WindowsVista"))

        self.comboBox_FECHA.setStyleSheet("QComboBox {\n"
"    background-color: #FFFFFF;\n"
"    border: 1px solid #C4C4C4;\n"
"    border-radius: 5px;\n"
"    padding: 5px;\n"
"    font-size: 14px;\n"
"    color: #333333;\n"
"}\n"
"\n"
"QComboBox::drop-down {\n"
"    subcontrol-origin: padding;\n"
"    subcontrol-position: top right;\n"
"    width: 30px;\n"
"    border-left: 1px solid #C4C4C4;\n"
"    background: transparent;\n"
"}\n"
"\n"
"QComboBox::down-arrow {\n"
"    image: url(:/icons/arrow-drop-down-big.png);\n"
"    width: 20px;\n"
"    height: 20px;\n"
"}\n"
"\n"
"QComboBox QAbstractItemView {\n"
"    border: 1px solid #C4C4C4;\n"
"    selection-background-color: #F0F0F0;\n"
"    background: #FFFFFF;\n"
"    font-size: 14px;\n"
"    color: #333333;\n"
"    border-radius: 8px;  /* Ajuste para evitar bordes negros */\n"
"    padding: 4px;\n"
"    outline: 0;\n"
"}\n"
"\n"
"QComboBox:disabled {\n"
"    background-color: #F9F9F9;\n"
"    color: #A0A0A0;\n"
"    border: 1px solid #E0E0E0;\n"
"}\n"
"\n"
"/* Ajuste de la estética de la interfaz */\n"
"QComboBox {\n"
"    background: #FFFFFF;\n"
"    border: 1px solid #BDBDBD;\n"
"    border-radius: 8px;\n"
"    padding: 4px 8px;\n"
"    font: 13px \'Segoe UI\';\n"
"    outline: none;\n"
"}\n"
"\n"
"QComboBox::drop-down {\n"
"    border: none;\n"
"    padding-right: 6px;\n"
"}\n"
"\n"
"QComboBox::down-arrow {\n"
"    image: url(:/icons/arrow-drop-down-big.png);\n"
"    width: 16px;\n"
"    height: 16px;\n"
"}\n"
"\n"
"QComboBox:hover {\n"
"    border: 1px solid #1F618D;\n"
"    background-color: #F0F8FF;\n"
"}\n"
"\n"
"QComboBox QAbstractItemView {\n"
"    selection-background-color: #D6EAF8;\n"
"    selection-color: #1F618D;\n"
"    background: #FFFFFF;\n"
"    border: 1px solid #BDBDBD;\n"
"    border-radius: 8px;\n"
"    padding: 4px;\n"
"    outline: 0;\n"
"}\n"
"")
        self.comboBox_FECHA.setFrame(True)
        self.comboBox_FECHA.setObjectName("comboBox_FECHA")
        self.comboBox_FECHA.addItem("")
        self.comboBox_FECHA.addItem("")
        self.comboBox_FECHA.addItem("")
        self.comboBox_FECHA.addItem("")
        self.comboBox_FECHA.addItem("")
        self.verticalLayout_2.addWidget(self.comboBox_FECHA)
        self.horizontalLayout_15 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_15.setSpacing(10)
        self.horizontalLayout_15.setObjectName("horizontalLayout_15")
        self.pushButton_filterFECHA = QtWidgets.QPushButton(parent=self.FECHA)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pushButton_filterFECHA.sizePolicy().hasHeightForWidth())
        self.pushButton_filterFECHA.setSizePolicy(sizePolicy)
        self.pushButton_filterFECHA.setMinimumSize(QtCore.QSize(0, 25))
        self.pushButton_filterFECHA.setMaximumSize(QtCore.QSize(16777215, 35))
        font = QtGui.QFont()
        font.setFamily("Lato Black")
        font.setBold(True)
        font.setWeight(75)
        self.pushButton_filterFECHA.setFont(font)
        self.pushButton_filterFECHA.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.pushButton_filterFECHA.setStyleSheet("QPushButton {\n"
"    background-color: #333333; /* Fondo negro */\n"
"    color: #FFFFFF;\n"
"    font-size: 13px;\n"
"    font-weight: bold;\n"
"    border-radius: 8px;\n"
"    border: none;\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: #4D4D4D; /* Fondo gris oscuro al pasar el cursor */\n"
"}\n"
"\n"
"QPushButton:pressed {\n"
"    background-color: #222222; /* Fondo gris muy oscuro al presionar */\n"
"}")
        icon6 = QtGui.QIcon()
        icon6.addPixmap(QtGui.QPixmap(":/icons/Mesa de trabajo 1 copia 2.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.pushButton_filterFECHA.setIcon(icon6)
        self.pushButton_filterFECHA.setObjectName("pushButton_filterFECHA")
        self.horizontalLayout_15.addWidget(self.pushButton_filterFECHA)
        self.pushButton_cleanFECHA = QtWidgets.QPushButton(parent=self.FECHA)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pushButton_cleanFECHA.sizePolicy().hasHeightForWidth())
        self.pushButton_cleanFECHA.setSizePolicy(sizePolicy)
        self.pushButton_cleanFECHA.setMinimumSize(QtCore.QSize(0, 25))
        self.pushButton_cleanFECHA.setMaximumSize(QtCore.QSize(16777215, 35))
        font = QtGui.QFont()
        font.setFamily("Lato Black")
        font.setBold(True)
        font.setWeight(75)
        self.pushButton_cleanFECHA.setFont(font)
        self.pushButton_cleanFECHA.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.pushButton_cleanFECHA.setStyleSheet("QPushButton {\n"
"    background-color: #333333; /* Fondo negro */\n"
"    color: #FFFFFF;\n"
"    font-size: 13px;\n"
"    font-weight: bold;\n"
"    border-radius: 8px;\n"
"    border: none;\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: #4D4D4D; /* Fondo gris oscuro al pasar el cursor */\n"
"}\n"
"\n"
"QPushButton:pressed {\n"
"    background-color: #222222; /* Fondo gris muy oscuro al presionar */\n"
"}")
        icon7 = QtGui.QIcon()
        icon7.addPixmap(QtGui.QPixmap(":/icons/trashwhite.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.pushButton_cleanFECHA.setIcon(icon7)
        self.pushButton_cleanFECHA.setObjectName("pushButton_cleanFECHA")
        self.horizontalLayout_15.addWidget(self.pushButton_cleanFECHA)
        self.verticalLayout_2.addLayout(self.horizontalLayout_15)
        self.verticalLayout_5.addWidget(self.FECHA)
        self.verticalLayout_25.addWidget(self.frame_6)
        self.stackedWidget.addWidget(self.FILTRO_stckW)
        self.EXPORTAR_stckW = QtWidgets.QWidget()
        self.EXPORTAR_stckW.setStyleSheet("QWidget{\n"
"    background-color: rgb(255, 255, 255);\n"
"}\n"
"")
        self.EXPORTAR_stckW.setObjectName("EXPORTAR_stckW")
        self.verticalLayout_17 = QtWidgets.QVBoxLayout(self.EXPORTAR_stckW)
        self.verticalLayout_17.setObjectName("verticalLayout_17")
        self.frame = QtWidgets.QFrame(parent=self.EXPORTAR_stckW)
        self.frame.setStyleSheet("QFrame {\n"
"    background-color: #F8F8F8;\n"
"    border-radius: 8px;\n"
"    padding: 10px;\n"
"}")
        self.frame.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.frame.setObjectName("frame")
        self.verticalLayout_13 = QtWidgets.QVBoxLayout(self.frame)
        self.verticalLayout_13.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_13.setSpacing(7)
        self.verticalLayout_13.setObjectName("verticalLayout_13")
        self.label_tituloPDF = QtWidgets.QLabel(parent=self.frame)
        self.label_tituloPDF.setMaximumSize(QtCore.QSize(16777215, 65))
        self.label_tituloPDF.setStyleSheet("QLabel {\n"
"    font-size: 20px;\n"
"    font-weight: bold;\n"
"    color: #FFFFFF;  /* Texto en blanco para contraste */\n"
"    background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #8B0000, stop:1 #B22222);  /* Degradado de rojo oscuro */\n"
"    padding: 10px 15px;\n"
"    border-radius: 8px;\n"
"    letter-spacing: 1px;\n"
"    text-align: center;\n"
"    margin-bottom: 5px;\n"
"}\n"
"\n"
"QLabel::after {\n"
"    content: \"\";\n"
"    display: block;\n"
"    margin: 8px auto;\n"
"    width: 50px;  /* Ancho de la línea */\n"
"    height: 3px;  /* Grosor de la línea */\n"
"    background-color: #B22222;  /* Mismo color que el degradado para cohesión */\n"
"    border-radius: 1px;\n"
"    opacity: 0.8;  /* Ligeramente translúcido */\n"
"}")
        self.label_tituloPDF.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_tituloPDF.setObjectName("label_tituloPDF")
        self.verticalLayout_13.addWidget(self.label_tituloPDF)
        self.PDF_groupBox_ARCHIVOSPDF = QtWidgets.QGroupBox(parent=self.frame)
        self.PDF_groupBox_ARCHIVOSPDF.setMinimumSize(QtCore.QSize(0, 0))
        self.PDF_groupBox_ARCHIVOSPDF.setMaximumSize(QtCore.QSize(16777215, 16777215))
        font = QtGui.QFont()
        font.setFamily("Lato Black")
        font.setBold(True)
        font.setWeight(75)
        self.PDF_groupBox_ARCHIVOSPDF.setFont(font)
        self.PDF_groupBox_ARCHIVOSPDF.setToolTipDuration(-1)
        self.PDF_groupBox_ARCHIVOSPDF.setStyleSheet("QGroupBox {\n"
"    font-size: 14px;\n"
"    font-weight: bold;\n"
"    color: #8B0000; /* Color rojo oscuro */\n"
"    border: 1px solid #D3D3D3;\n"
"    border-radius: 6px;\n"
"    margin-top: 10px;\n"
"    padding-top: 10px;\n"
"}\n"
"\n"
"QGroupBox::title {\n"
"    subcontrol-origin: margin;\n"
"    subcontrol-position: top left;\n"
"    padding: 0 5px;\n"
"    color: #8B0000;\n"
"    font-size: 13px;\n"
"}")
        self.PDF_groupBox_ARCHIVOSPDF.setObjectName("PDF_groupBox_ARCHIVOSPDF")
        self.verticalLayout_10 = QtWidgets.QVBoxLayout(self.PDF_groupBox_ARCHIVOSPDF)
        self.verticalLayout_10.setContentsMargins(-1, 0, 11, 13)
        self.verticalLayout_10.setSpacing(1)
        self.verticalLayout_10.setObjectName("verticalLayout_10")
        self.PDF_checkBox_FAC = QtWidgets.QCheckBox(parent=self.PDF_groupBox_ARCHIVOSPDF)
        self.PDF_checkBox_FAC.setMinimumSize(QtCore.QSize(0, 30))
        self.PDF_checkBox_FAC.setStyleSheet("/* Estilo general para QCheckBox */\n"
"QCheckBox {\n"
"    font-size: 13px;\n"
"    color: #333333;\n"
"    padding: 5px;\n"
"}\n"
"\n"
"")
        self.PDF_checkBox_FAC.setObjectName("PDF_checkBox_FAC")
        self.verticalLayout_10.addWidget(self.PDF_checkBox_FAC)
        self.PDF_checkBox_CR = QtWidgets.QCheckBox(parent=self.PDF_groupBox_ARCHIVOSPDF)
        self.PDF_checkBox_CR.setMinimumSize(QtCore.QSize(0, 30))
        self.PDF_checkBox_CR.setStyleSheet("/* Estilo general para QCheckBox */\n"
"QCheckBox {\n"
"    font-size: 13px;\n"
"    color: #333333;\n"
"    padding: 5px;\n"
"}\n"
"\n"
"")
        self.PDF_checkBox_CR.setObjectName("PDF_checkBox_CR")
        self.verticalLayout_10.addWidget(self.PDF_checkBox_CR)
        self.PDF_checkBox_REM = QtWidgets.QCheckBox(parent=self.PDF_groupBox_ARCHIVOSPDF)
        self.PDF_checkBox_REM.setMinimumSize(QtCore.QSize(0, 30))
        self.PDF_checkBox_REM.setStyleSheet("/* Estilo general para QCheckBox */\n"
"QCheckBox {\n"
"    font-size: 13px;\n"
"    color: #333333;\n"
"    padding: 5px;\n"
"}\n"
"")
        self.PDF_checkBox_REM.setObjectName("PDF_checkBox_REM")
        self.verticalLayout_10.addWidget(self.PDF_checkBox_REM)
        self.PDF_checkBox_OC = QtWidgets.QCheckBox(parent=self.PDF_groupBox_ARCHIVOSPDF)
        self.PDF_checkBox_OC.setMinimumSize(QtCore.QSize(0, 30))
        self.PDF_checkBox_OC.setStyleSheet("/* Estilo general para QCheckBox */\n"
"QCheckBox {\n"
"    font-size: 13px;\n"
"    color: #333333;\n"
"    padding: 5px;\n"
"}\n"
"")
        self.PDF_checkBox_OC.setObjectName("PDF_checkBox_OC")
        self.verticalLayout_10.addWidget(self.PDF_checkBox_OC)
        self.PDF_btn_SelectAll = QtWidgets.QPushButton(parent=self.PDF_groupBox_ARCHIVOSPDF)
        self.PDF_btn_SelectAll.setMinimumSize(QtCore.QSize(0, 30))
        self.PDF_btn_SelectAll.setMaximumSize(QtCore.QSize(150, 16777215))
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.PDF_btn_SelectAll.setFont(font)
        self.PDF_btn_SelectAll.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.PDF_btn_SelectAll.setMouseTracking(True)
        self.PDF_btn_SelectAll.setLayoutDirection(QtCore.Qt.LayoutDirection.RightToLeft)
        self.PDF_btn_SelectAll.setStyleSheet("QPushButton {\n"
"    background-color: #8B0000; /* Rojo oscuro */\n"
"    color: #FFFFFF;\n"
"    font-size: 12px;\n"
"    font-weight: bold;\n"
"    border: none;\n"
"    border-radius: 5px;\n"
"    padding: 7px 6px;\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: #A52A2A; /* Rojo intermedio al pasar el cursor */\n"
"}\n"
"\n"
"QPushButton:pressed {\n"
"    background-color: #5F0A0A; /* Rojo más oscuro al presionar */\n"
"}\n"
"")
        self.PDF_btn_SelectAll.setCheckable(True)
        self.PDF_btn_SelectAll.setObjectName("PDF_btn_SelectAll")
        self.verticalLayout_10.addWidget(self.PDF_btn_SelectAll)
        self.verticalLayout_13.addWidget(self.PDF_groupBox_ARCHIVOSPDF)
        self.groupbox_Descarga = QtWidgets.QGroupBox(parent=self.frame)
        self.groupbox_Descarga.setMinimumSize(QtCore.QSize(0, 0))
        self.groupbox_Descarga.setMaximumSize(QtCore.QSize(16777215, 120))
        font = QtGui.QFont()
        font.setFamily("Lato Black")
        font.setBold(True)
        font.setWeight(75)
        self.groupbox_Descarga.setFont(font)
        self.groupbox_Descarga.setStyleSheet("QGroupBox {\n"
"    font-size: 14px;\n"
"    font-weight: bold;\n"
"    color: #8B0000; /* Color rojo oscuro */\n"
"    border: 1px solid #D3D3D3;\n"
"    border-radius: 6px;\n"
"    margin-top: 10px;\n"
"    padding-top: 5px;\n"
"}\n"
"\n"
"QGroupBox::title {\n"
"    subcontrol-origin: margin;\n"
"    subcontrol-position: top left;\n"
"    padding: 0 5px;\n"
"    color: #8B0000;\n"
"    font-size: 13px;\n"
"}")
        self.groupbox_Descarga.setObjectName("groupbox_Descarga")
        self.verticalLayout_12 = QtWidgets.QVBoxLayout(self.groupbox_Descarga)
        self.verticalLayout_12.setSpacing(0)
        self.verticalLayout_12.setObjectName("verticalLayout_12")
        self.radioButton_joinPDF = QtWidgets.QRadioButton(parent=self.groupbox_Descarga)
        self.radioButton_joinPDF.setStyleSheet("QRadioButton {\n"
"    font-size: 13px;\n"
"    color: #333333;\n"
"    padding: 5px;\n"
"}\n"
"")
        self.radioButton_joinPDF.setObjectName("radioButton_joinPDF")
        self.verticalLayout_12.addWidget(self.radioButton_joinPDF)
        self.radioButton_splitPDF = QtWidgets.QRadioButton(parent=self.groupbox_Descarga)
        self.radioButton_splitPDF.setToolTip("")
        self.radioButton_splitPDF.setToolTipDuration(-1)
        self.radioButton_splitPDF.setStyleSheet("QRadioButton {\n"
"    font-size: 13px;\n"
"    color: #333333;\n"
"    padding: 5px;\n"
"}\n"
"")
        self.radioButton_splitPDF.setObjectName("radioButton_splitPDF")
        self.verticalLayout_12.addWidget(self.radioButton_splitPDF)
        self.verticalLayout_13.addWidget(self.groupbox_Descarga)
        self.PDF_groupBox_Carpetas = QtWidgets.QGroupBox(parent=self.frame)
        self.PDF_groupBox_Carpetas.setMinimumSize(QtCore.QSize(0, 0))
        self.PDF_groupBox_Carpetas.setMaximumSize(QtCore.QSize(16777215, 120))
        font = QtGui.QFont()
        font.setFamily("Lato Black")
        font.setBold(True)
        font.setWeight(75)
        self.PDF_groupBox_Carpetas.setFont(font)
        self.PDF_groupBox_Carpetas.setStyleSheet("QGroupBox {\n"
"    font-size: 14px;\n"
"    font-weight: bold;\n"
"    color: #8B0000; /* Color rojo oscuro */\n"
"    border: 1px solid #D3D3D3;\n"
"    border-radius: 6px;\n"
"    margin-top: 10px;\n"
"    padding-top: 10px;\n"
"}\n"
"\n"
"QGroupBox::title {\n"
"    subcontrol-origin: margin;\n"
"    subcontrol-position: top left;\n"
"    padding: 0 5px;\n"
"    color: #8B0000;\n"
"    font-size: 13px;\n"
"}")
        self.PDF_groupBox_Carpetas.setCheckable(False)
        self.PDF_groupBox_Carpetas.setChecked(False)
        self.PDF_groupBox_Carpetas.setObjectName("PDF_groupBox_Carpetas")
        self.verticalLayout_11 = QtWidgets.QVBoxLayout(self.PDF_groupBox_Carpetas)
        self.verticalLayout_11.setContentsMargins(-1, -1, -1, 11)
        self.verticalLayout_11.setSpacing(0)
        self.verticalLayout_11.setObjectName("verticalLayout_11")
        self.PDF_checkBox_PROVEEDOR = QtWidgets.QCheckBox(parent=self.PDF_groupBox_Carpetas)
        self.PDF_checkBox_PROVEEDOR.setStyleSheet("/* Estilo general para QCheckBox */\n"
"QCheckBox {\n"
"    font-size: 13px;\n"
"    color: #333333;\n"
"    padding: 5px;\n"
"}\n"
"")
        self.PDF_checkBox_PROVEEDOR.setObjectName("PDF_checkBox_PROVEEDOR")
        self.verticalLayout_11.addWidget(self.PDF_checkBox_PROVEEDOR)
        self.verticalLayout_13.addWidget(self.PDF_groupBox_Carpetas)
        self.PDF_btn_descargar = QtWidgets.QPushButton(parent=self.frame)
        self.PDF_btn_descargar.setMinimumSize(QtCore.QSize(0, 40))
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.PDF_btn_descargar.setFont(font)
        self.PDF_btn_descargar.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.PDF_btn_descargar.setStyleSheet("QPushButton {\n"
"    background-color: #8B0000; /* Rojo oscuro */\n"
"    color: #FFFFFF;\n"
"    font-size: 14px;\n"
"    font-weight: bold;\n"
"    border: none;\n"
"    border-radius: 5px;\n"
"    padding: 7px 6px;\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: #A52A2A; /* Rojo intermedio al pasar el cursor */\n"
"}\n"
"\n"
"QPushButton:pressed {\n"
"    background-color: #5F0A0A; /* Rojo más oscuro al presionar */\n"
"}\n"
"")
        icon8 = QtGui.QIcon()
        icon8.addPixmap(QtGui.QPixmap(":/icons/pdf-file.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.PDF_btn_descargar.setIcon(icon8)
        self.PDF_btn_descargar.setIconSize(QtCore.QSize(15, 15))
        self.PDF_btn_descargar.setCheckable(True)
        self.PDF_btn_descargar.setObjectName("PDF_btn_descargar")
        self.verticalLayout_13.addWidget(self.PDF_btn_descargar)
        self.verticalLayout_17.addWidget(self.frame)
        self.frame_7 = QtWidgets.QFrame(parent=self.EXPORTAR_stckW)
        self.frame_7.setMinimumSize(QtCore.QSize(0, 200))
        self.frame_7.setMaximumSize(QtCore.QSize(16777215, 200))
        self.frame_7.setStyleSheet("QFrame {\n"
"    background-color: #F8F8F8;\n"
"    border-radius: 8px;\n"
"    padding: 3px;\n"
"}")
        self.frame_7.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.frame_7.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.frame_7.setObjectName("frame_7")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.frame_7)
        self.gridLayout_2.setContentsMargins(11, 0, 11, 0)
        self.gridLayout_2.setSpacing(0)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.stackedWidget_2 = QtWidgets.QStackedWidget(parent=self.frame_7)
        self.stackedWidget_2.setMinimumSize(QtCore.QSize(0, 0))
        self.stackedWidget_2.setMaximumSize(QtCore.QSize(16777215, 170))
        self.stackedWidget_2.setStyleSheet("")
        self.stackedWidget_2.setObjectName("stackedWidget_2")
        self.tipo0_info = QtWidgets.QWidget()
        self.tipo0_info.setStyleSheet("QWidget {\n"
"    background-color: #F8F8F8;\n"
"}")
        self.tipo0_info.setObjectName("tipo0_info")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.tipo0_info)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.pushButton = QtWidgets.QPushButton(parent=self.tipo0_info)
        self.pushButton.setMinimumSize(QtCore.QSize(100, 100))
        self.pushButton.setMaximumSize(QtCore.QSize(80, 16777215))
        font = QtGui.QFont()
        font.setFamily("MS Shell Dlg 2")
        self.pushButton.setFont(font)
        self.pushButton.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.pushButton.setStyleSheet("QPushButton {\n"
"        border: none;\n"
"        border-radius: 40px; /* Asegura que el botón sea redondo */\n"
"        background-color: #E0E0E0; /* Color de fondo inicial */\n"
"        image: url(:/icons/information-button.png); /* Icono del botón */\n"
"        padding: 15px; /* Espacio alrededor de la imagen para centrarla */\n"
"    }\n"
"\n"
"    QPushButton:hover {\n"
"        background-color: #BDBDBD; /* Fondo más oscuro al pasar el cursor */\n"
"    }\n"
"\n"
"    QPushButton:pressed {\n"
"        background-color: #9E9E9E; /* Fondo aún más oscuro al presionar */\n"
"    }")
        self.pushButton.setText("")
        self.pushButton.setObjectName("pushButton")
        self.horizontalLayout_2.addWidget(self.pushButton)
        self.stackedWidget_2.addWidget(self.tipo0_info)
        self.tipo1 = QtWidgets.QWidget()
        self.tipo1.setObjectName("tipo1")
        self.verticalLayout_27 = QtWidgets.QVBoxLayout(self.tipo1)
        self.verticalLayout_27.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_27.setSpacing(0)
        self.verticalLayout_27.setObjectName("verticalLayout_27")
        self.label_2 = QtWidgets.QLabel(parent=self.tipo1)
        self.label_2.setStyleSheet("border-image: url(:/icons/stck1.png);")
        self.label_2.setText("")
        self.label_2.setObjectName("label_2")
        self.verticalLayout_27.addWidget(self.label_2)
        self.stackedWidget_2.addWidget(self.tipo1)
        self.tipo2 = QtWidgets.QWidget()
        self.tipo2.setObjectName("tipo2")
        self.verticalLayout_28 = QtWidgets.QVBoxLayout(self.tipo2)
        self.verticalLayout_28.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_28.setSpacing(0)
        self.verticalLayout_28.setObjectName("verticalLayout_28")
        self.label_3 = QtWidgets.QLabel(parent=self.tipo2)
        self.label_3.setStyleSheet("border-image: url(:/icons/stck2.png);")
        self.label_3.setText("")
        self.label_3.setObjectName("label_3")
        self.verticalLayout_28.addWidget(self.label_3)
        self.stackedWidget_2.addWidget(self.tipo2)
        self.tipo3 = QtWidgets.QWidget()
        self.tipo3.setObjectName("tipo3")
        self.verticalLayout_29 = QtWidgets.QVBoxLayout(self.tipo3)
        self.verticalLayout_29.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_29.setSpacing(0)
        self.verticalLayout_29.setObjectName("verticalLayout_29")
        self.label_4 = QtWidgets.QLabel(parent=self.tipo3)
        self.label_4.setStyleSheet("border-image: url(:/icons/stck3.png);")
        self.label_4.setText("")
        self.label_4.setObjectName("label_4")
        self.verticalLayout_29.addWidget(self.label_4)
        self.stackedWidget_2.addWidget(self.tipo3)
        self.tipo4 = QtWidgets.QWidget()
        self.tipo4.setObjectName("tipo4")
        self.verticalLayout_30 = QtWidgets.QVBoxLayout(self.tipo4)
        self.verticalLayout_30.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_30.setSpacing(0)
        self.verticalLayout_30.setObjectName("verticalLayout_30")
        self.label_5 = QtWidgets.QLabel(parent=self.tipo4)
        self.label_5.setStyleSheet("border-image: url(:/icons/stck4.png);")
        self.label_5.setText("")
        self.label_5.setObjectName("label_5")
        self.verticalLayout_30.addWidget(self.label_5)
        self.stackedWidget_2.addWidget(self.tipo4)
        self.tipo5 = QtWidgets.QWidget()
        self.tipo5.setObjectName("tipo5")
        self.verticalLayout_31 = QtWidgets.QVBoxLayout(self.tipo5)
        self.verticalLayout_31.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_31.setSpacing(0)
        self.verticalLayout_31.setObjectName("verticalLayout_31")
        self.label_6 = QtWidgets.QLabel(parent=self.tipo5)
        self.label_6.setStyleSheet("border-image: url(:/icons/stck5.png);")
        self.label_6.setText("")
        self.label_6.setObjectName("label_6")
        self.verticalLayout_31.addWidget(self.label_6)
        self.stackedWidget_2.addWidget(self.tipo5)
        self.tipo6 = QtWidgets.QWidget()
        self.tipo6.setObjectName("tipo6")
        self.verticalLayout_32 = QtWidgets.QVBoxLayout(self.tipo6)
        self.verticalLayout_32.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_32.setSpacing(0)
        self.verticalLayout_32.setObjectName("verticalLayout_32")
        self.label_7 = QtWidgets.QLabel(parent=self.tipo6)
        self.label_7.setStyleSheet("border-image: url(:/icons/stck6.png);")
        self.label_7.setText("")
        self.label_7.setObjectName("label_7")
        self.verticalLayout_32.addWidget(self.label_7)
        self.stackedWidget_2.addWidget(self.tipo6)
        self.tipo7 = QtWidgets.QWidget()
        self.tipo7.setObjectName("tipo7")
        self.verticalLayout_33 = QtWidgets.QVBoxLayout(self.tipo7)
        self.verticalLayout_33.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_33.setSpacing(0)
        self.verticalLayout_33.setObjectName("verticalLayout_33")
        self.label_8 = QtWidgets.QLabel(parent=self.tipo7)
        self.label_8.setStyleSheet("border-image: url(:/icons/stck7.png);")
        self.label_8.setText("")
        self.label_8.setObjectName("label_8")
        self.verticalLayout_33.addWidget(self.label_8)
        self.stackedWidget_2.addWidget(self.tipo7)
        self.tipo8 = QtWidgets.QWidget()
        self.tipo8.setObjectName("tipo8")
        self.verticalLayout_34 = QtWidgets.QVBoxLayout(self.tipo8)
        self.verticalLayout_34.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_34.setSpacing(0)
        self.verticalLayout_34.setObjectName("verticalLayout_34")
        self.label_9 = QtWidgets.QLabel(parent=self.tipo8)
        self.label_9.setStyleSheet("border-image: url(:/icons/stck8.png);")
        self.label_9.setText("")
        self.label_9.setObjectName("label_9")
        self.verticalLayout_34.addWidget(self.label_9)
        self.stackedWidget_2.addWidget(self.tipo8)
        self.gridLayout_2.addWidget(self.stackedWidget_2, 1, 0, 1, 1)
        self.verticalLayout_17.addWidget(self.frame_7)
        self.stackedWidget.addWidget(self.EXPORTAR_stckW)
        self.horizontalLayout_3.addWidget(self.stackedWidget)
        self.verticalLayout_8 = QtWidgets.QVBoxLayout()
        self.verticalLayout_8.setSpacing(0)
        self.verticalLayout_8.setObjectName("verticalLayout_8")
        self.header_wg = QtWidgets.QWidget(parent=self.centralwidget)
        self.header_wg.setMaximumSize(QtCore.QSize(16777215, 200))
        self.header_wg.setStyleSheet("background-color: rgb(255, 255, 255);")
        self.header_wg.setObjectName("header_wg")
        self.horizontalLayout_5 = QtWidgets.QHBoxLayout(self.header_wg)
        self.horizontalLayout_5.setContentsMargins(0, 19, 0, 11)
        self.horizontalLayout_5.setSpacing(0)
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.palmaterra_logo = QtWidgets.QLabel(parent=self.header_wg)
        self.palmaterra_logo.setMinimumSize(QtCore.QSize(300, 70))
        self.palmaterra_logo.setMaximumSize(QtCore.QSize(300, 70))
        self.palmaterra_logo.setStyleSheet("border-image: url(:/icons/Palmaterra-Cartel.png);")
        self.palmaterra_logo.setText("")
        self.palmaterra_logo.setObjectName("palmaterra_logo")
        self.horizontalLayout_5.addWidget(self.palmaterra_logo)
        self.verticalLayout_8.addWidget(self.header_wg)
        self.mainscreen_wg = QtWidgets.QWidget(parent=self.centralwidget)
        self.mainscreen_wg.setMinimumSize(QtCore.QSize(50, 0))
        self.mainscreen_wg.setStyleSheet("background-color: rgb(255, 255, 255);")
        self.mainscreen_wg.setObjectName("mainscreen_wg")
        self.verticalLayout_9 = QtWidgets.QVBoxLayout(self.mainscreen_wg)
        self.verticalLayout_9.setContentsMargins(-1, 10, -1, 11)
        self.verticalLayout_9.setObjectName("verticalLayout_9")
        self.tablasWidget = QtWidgets.QTabWidget(parent=self.mainscreen_wg)
        font = QtGui.QFont()
        font.setFamily("Lato Black")
        self.tablasWidget.setFont(font)
        self.tablasWidget.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.ArrowCursor))
        self.tablasWidget.setStyleSheet("QTabWidget::pane {\n"
"    border: 1px solid #AFAFAF;\n"
"    border-radius: 2px; /* Borde menos redondeado */\n"
"    background-color: #FFFFFF;\n"
"}\n"
"\n"
"QTabBar::tab {\n"
"    background: #E0E0E0;\n"
"    color: #333333;\n"
"    padding: 8px 20px;\n"
"    border-top-left-radius: 3px; /* Menos redondeado en las pestañas */\n"
"    border-top-right-radius: 3px;\n"
"    margin-right: 2px;\n"
"    font-size: 13px;\n"
"}\n"
"\n"
"QTabBar::tab:selected {\n"
"    background: #4A90E2; /* Color de fondo para la pestaña seleccionada */\n"
"    color: #FFFFFF; /* Color de texto blanco en la pestaña activa */\n"
"    font-weight: bold; /* Texto en negrita para destacar la pestaña activa */\n"
"}\n"
"\n"
"QTabBar::tab:hover {\n"
"    background: #B0C4DE; /* Fondo ligeramente más claro al pasar el cursor */\n"
"    color: #333333;\n"
"}\n"
"\n"
"QTabBar::tab:!selected {\n"
"    margin-top: 2px; /* Pequeño desplazamiento para pestañas no seleccionadas */\n"
"}\n"
"\n"
"\n"
"\n"
"QWidget {\n"
"    background-color: #FAFAFA; /* Fondo del área de contenido de cada pestaña */\n"
"    padding: 0px;\n"
"    border-bottom-left-radius: 3px; /* Bordes menos redondeados */\n"
"    border-bottom-right-radius: 3px;\n"
"}\n"
"\n"
"")
        self.tablasWidget.setIconSize(QtCore.QSize(20, 20))
        self.tablasWidget.setObjectName("tablasWidget")
        self.ConcentradoTab = QtWidgets.QWidget()
        self.ConcentradoTab.setObjectName("ConcentradoTab")
        self.horizontalLayout_6 = QtWidgets.QHBoxLayout(self.ConcentradoTab)
        self.horizontalLayout_6.setSizeConstraint(QtWidgets.QLayout.SizeConstraint.SetDefaultConstraint)
        self.horizontalLayout_6.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_6.setSpacing(0)
        self.horizontalLayout_6.setObjectName("horizontalLayout_6")
        self.tableView_concentrado = QtWidgets.QTableView(parent=self.ConcentradoTab)
        self.tableView_concentrado.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.tableView_concentrado.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.tableView_concentrado.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.SizeAdjustPolicy.AdjustIgnored)
        self.tableView_concentrado.setSortingEnabled(True)
        self.tableView_concentrado.setStyleSheet("""
                            QTableView {
                                background-color: #FAFAFA;
                                alternate-background-color: #E0E0E0;
                                gridline-color: #AFAFAF;
                                color: #333333;
                                selection-background-color: #4A90E2;
                                selection-color: #FFFFFF;
                            }
                            QHeaderView::section {
                                background-color: black;
                                color: #FFFFFF;
                                font-weight: bold;
                                padding: 4px;
                                border: none;
                            }
                            QTableCornerButton::section {
                                background-color: black;
                            }
                            QScrollBar:horizontal, QScrollBar:vertical {
                                background-color: #F0F0F0; /* Fondo suave */
                                border: none;
                                width: 12px; /* Ancho de la barra de desplazamiento */
                                height: 12px; /* Altura de la barra de desplazamiento horizontal */
                                margin: 0px; /* Sin margen */
                            }
                            QScrollBar::handle:horizontal, QScrollBar::handle:vertical {
                                background-color: #B7B7B7; /* Color del handle */
                                border-radius: 1px; /* Bordes redondeados para darle un toque moderno */
                                min-height: 20px; /* Altura mínima para el handle */
                                min-width: 20px; /* Ancho mínimo para el handle */
                            }
                            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
                            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                                border: none;
                                background: none; /* Eliminar los botones de línea */
                            }
                            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal,
                            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                                background: none;
                            }

                            QMenu {
                                background-color: #FFFFFF; /* Fondo blanco */
                                color: #333333; /* Texto oscuro */
                                border: 1px solid #AFAFAF; /* Borde de menú */
                            }
                            QMenu::item:selected {
                                background-color: #4A90E2; /* Fondo azul para elementos seleccionados */
                                color: #FFFFFF; /* Texto blanco cuando el elemento es seleccionado */
                            }   
                        """)

        self.tableView_concentrado.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.tableView_concentrado.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)

        self.tableView_concentrado.setObjectName("tableView_concentrado")
        self.horizontalLayout_6.addWidget(self.tableView_concentrado)
        self.tablasWidget.addTab(self.ConcentradoTab, "")
        self.DesglosadoTab = QtWidgets.QWidget()
        self.DesglosadoTab.setObjectName("DesglosadoTab")
        self.horizontalLayout_7 = QtWidgets.QHBoxLayout(self.DesglosadoTab)
        self.horizontalLayout_7.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_7.setSpacing(0)
        self.horizontalLayout_7.setObjectName("horizontalLayout_7")
        self.tableView_desglosado = QtWidgets.QTableView(parent=self.DesglosadoTab)
        self.tableView_desglosado.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.tableView_desglosado.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.tableView_desglosado.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.SizeAdjustPolicy.AdjustIgnored)
        self.tableView_desglosado.setSortingEnabled(True)
        self.tableView_desglosado.setStyleSheet("""
                            QTableView {
                                background-color: #FAFAFA;
                                alternate-background-color: #E0E0E0;
                                gridline-color: #AFAFAF;
                                color: #333333;
                                selection-background-color: #4A90E2;
                                selection-color: #FFFFFF;
                            }
                            QHeaderView::section {
                                background-color: black;
                                color: #FFFFFF;
                                font-weight: bold;
                                padding: 4px;
                                border: none;
                            }
                            QTableCornerButton::section {
                                background-color: black;
                            }
                            QScrollBar:horizontal, QScrollBar:vertical {
                                background-color: #F0F0F0; /* Fondo suave */
                                border: none;
                                width: 12px; /* Ancho de la barra de desplazamiento */
                                height: 12px; /* Altura de la barra de desplazamiento horizontal */
                                margin: 0px; /* Sin margen */
                            }
                            QScrollBar::handle:horizontal, QScrollBar::handle:vertical {
                                background-color: #B7B7B7; /* Color del handle */
                                border-radius: 1px; /* Bordes redondeados para darle un toque moderno */
                                min-height: 20px; /* Altura mínima para el handle */
                                min-width: 20px; /* Ancho mínimo para el handle */
                            }
                            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
                            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                                border: none;
                                background: none; /* Eliminar los botones de línea */
                            }
                            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal,
                            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                                background: none;
                            }

                            QMenu {
                                background-color: #FFFFFF; /* Fondo blanco */
                                color: #333333; /* Texto oscuro */
                                border: 1px solid #AFAFAF; /* Borde de menú */
                            }
                            QMenu::item:selected {
                                background-color: #4A90E2; /* Fondo azul para elementos seleccionados */
                                color: #FFFFFF; /* Texto blanco cuando el elemento es seleccionado */
                            }   
                        """)

        self.tableView_desglosado.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.tableView_desglosado.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.tableView_desglosado.setObjectName("tableView_desglosado")
        self.horizontalLayout_7.addWidget(self.tableView_desglosado)
        self.tablasWidget.addTab(self.DesglosadoTab, "")
        self.verticalLayout_9.addWidget(self.tablasWidget)
        self.verticalLayout_8.addWidget(self.mainscreen_wg)
        self.horizontalLayout_3.addLayout(self.verticalLayout_8)
        self.horizontalLayout_4.addLayout(self.horizontalLayout_3)
        MainWindow.setCentralWidget(self.centralwidget)
        self.statusBar = QtWidgets.QStatusBar(parent=MainWindow)
        self.statusBar.setObjectName("statusBar")
        MainWindow.setStatusBar(self.statusBar)
        self.actionCONCENTRADO = QtGui.QAction(parent=MainWindow)
        self.actionCONCENTRADO.setObjectName("actionCONCENTRADO")
        self.actionDESGLOSADO = QtGui.QAction(parent=MainWindow)
        self.actionDESGLOSADO.setObjectName("actionDESGLOSADO")

        self.retranslateUi(MainWindow)
        self.stackedWidget.setHidden(True)
        self.stackedWidget_2.setCurrentIndex(0)
        self.tablasWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)
        QApplication.setStyle(QStyleFactory.create("Fusion"))

        self.home_tab.clicked.connect(self.toggle_page_home)
        self.filter_tab.clicked.connect(self.toggle_page_filter)
        self.pushButton_2.clicked.connect(self.toggle_page_export)
        self.pushButton_selectHTML.clicked.connect(self.seleccionar_archivos)
        self.pushButton_Analizar.clicked.connect(self.analizar)
        self.tableView_concentrado.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tableView_concentrado.customContextMenuRequested.connect(self.mostrar_menu_contextual)
        self.tableView_concentrado.setModel(self.proxy_model)
        self.dateEdit.setDate(QDate.currentDate())
        self.dateEdit_2.setDate(QDate.currentDate())
        self.pushButton_4.clicked.connect(self.abrir_nueva_ventana)

        self.comboBox_FECHA.currentIndexChanged.connect(self.on_combobox_fecha_changed)

        # Conectar los botones para abrir el diálogo de selección múltiple
        self.pushButton__filterObra.clicked.connect(self.seleccionar_obras)
        self.pushButton_filterProveedor.clicked.connect(self.seleccionar_proveedores)
        self.pushButton_filterResidente.clicked.connect(self.seleccionar_residentes)

        #Conectar las filas con los filtros
        self.lineEdit_filterObra.textChanged.connect(lambda text: self.proxy_model.set_filter_obra(text))
        self.lineEdit__filterProveedor.textChanged.connect(lambda text: self.proxy_model.set_filter_proveedor(text))
        self.lineEdit__filterResidente.textChanged.connect(lambda text: self.proxy_model.set_filter_residente(text))
        self.lineEdit__filterNumero.textChanged.connect(lambda text: self.proxy_model.set_filter_numero(text))
        self.pushButton_filterFECHA.clicked.connect(lambda: self.proxy_model.set_filter_fecha(
            self.dateEdit.date(), self.dateEdit_2.date()
        ))

        #Conectar las filas con los filtros
        self.lineEdit_filterObra.textChanged.connect(lambda text: self.proxy_model_desglose.set_filter_obra(text))
        self.lineEdit__filterProveedor.textChanged.connect(lambda text: self.proxy_model_desglose.set_filter_proveedor(text))
        self.lineEdit__filterResidente.textChanged.connect(lambda text: self.proxy_model_desglose.set_filter_residente(text))
        self.lineEdit__filterNumero.textChanged.connect(lambda text: self.proxy_model_desglose.set_filter_numero(text))
        self.lineEdit__filterDescrip.textChanged.connect(lambda text: self.proxy_model_desglose.set_filter_descripcion(text))
        self.pushButton_filterFECHA.clicked.connect(lambda: self.proxy_model_desglose.set_filter_fecha(
            self.dateEdit.date(), self.dateEdit_2.date()
        ))

        self.pushButton_cleanFECHA.clicked.connect(self.clear_all_filters)
        # Inicializar el ListView de estatus
        self.listView_model = QStandardItemModel()
        self.listView.setModel(self.listView_model)
        self.pushButton_3.clicked.connect(self.seleccionar_todos_estatus)

        self.PDF_checkBox_FAC.stateChanged.connect(self.actualizar_pagina_stackedWidget)
        self.radioButton_splitPDF.toggled.connect(self.actualizar_pagina_stackedWidget)
        self.radioButton_joinPDF.toggled.connect(self.actualizar_pagina_stackedWidget)
        self.PDF_checkBox_PROVEEDOR.stateChanged.connect(self.actualizar_pagina_stackedWidget)
        self.PDF_checkBox_CR.stateChanged.connect(self.actualizar_pagina_stackedWidget)
        self.PDF_checkBox_OC.stateChanged.connect(self.actualizar_pagina_stackedWidget)
        self.PDF_checkBox_REM.stateChanged.connect(self.actualizar_pagina_stackedWidget)
        self.pushButton.clicked.connect(self.mostrar_alerta_combinacion)

        self.PDF_btn_descargar.clicked.connect(self.iniciar_descarga)

        self.radioButton_splitPDF.setChecked(True)
        self.PDF_btn_SelectAll.clicked.connect(self.select_all_pdf)
        self.EXCEL_btn_Descargar_2.clicked.connect(self.exportar_datos_excel)
       # Elementos de la barra de estado
        self.status_promedio = QtWidgets.QLabel("Promedio: 0.00")
        self.status_recuento = QtWidgets.QLabel("Recuento: 0")
        self.status_suma = QtWidgets.QLabel("Suma: 0.00")

        # Añadir etiquetas a la barra de estado
        self.statusBar.addPermanentWidget(self.status_promedio)
        self.statusBar.addPermanentWidget(self.status_recuento)
        self.statusBar.addPermanentWidget(self.status_suma)

        # Asignar un modelo vacío a los tableViews para permitir la selección
        modelo_vacio = QStandardItemModel(0, 0)
        self.tableView_concentrado.setModel(modelo_vacio)
        self.tableView_desglosado.setModel(modelo_vacio)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "PALMA TERRA 360 | MÓDULO FACTURAS"))
        self.pushButton_selectHTML.setText(_translate("MainWindow", "  SELECCIONAR\n"
                                                                    "  ARCHIVO"))
        self.pushButton_4.setText(_translate("MainWindow", "DESCARGAR"))
        # self.namefile_loadedHTML.setPlaceholderText(_translate("MainWindow", "Cargar archivo *.html ..."))
        self.pushButton_Analizar.setText(_translate("MainWindow", "  ANALIZAR"))
        self.groupBox_InfofileHTML.setTitle(_translate("MainWindow", "INFORMACIÓN"))
        self.label_amountFacturas.setText(_translate("MainWindow", "Facturas:"))
        self.lineEdit_amountFacturas.setPlaceholderText(_translate("MainWindow", "0 Facturas..."))
        self.label_amountMonto.setText(_translate("MainWindow", "Monto (IVA Inlcuido):"))
        self.lineEdit_amountMonto.setPlaceholderText(_translate("MainWindow", "$0 Acumulado"))
        self.label_amountConceptos.setText(_translate("MainWindow", "Conceptos:"))
        self.lineEdit_amountConcepto.setPlaceholderText(_translate("MainWindow", "0 Conceptos analizados"))
        self.EXCEL_groupBox_Descarga_2.setTitle(_translate("MainWindow", "EXPORTAR A EXCEL"))
        self.EXCEL_checkBox_RESUMEN_2.setText(_translate("MainWindow", "CONCENTRADO"))
        self.EXCEL_checkBox_DESGLOSADO_2.setText(_translate("MainWindow", "DESGLOSADO"))
        self.EXCEL_btn_Descargar_2.setText(_translate("MainWindow", "DESCARGAR"))
        self.label_versionSoftware.setText(_translate("MainWindow", "© Palma Terra | Facturas Noé | Versión 1.00 "))
        self.label_tituloPDF_2.setText(_translate("MainWindow", "FILTRO"))
        self.label__filterObra.setText(_translate("MainWindow", "Obra:"))
        self.lineEdit_filterObra.setPlaceholderText(_translate("MainWindow", "Ingrese obra..."))
        self.label__filterProveedor.setText(_translate("MainWindow", "Proveedor:"))
        self.lineEdit__filterProveedor.setPlaceholderText(_translate("MainWindow", "Ingrese proveedor..."))
        self.label_filterResidente.setText(_translate("MainWindow", "Residente:"))
        self.lineEdit__filterResidente.setPlaceholderText(_translate("MainWindow", "Ingrese residente..."))
        self.label_filterNumero.setText(_translate("MainWindow", "Número:"))
        self.lineEdit__filterNumero.setPlaceholderText(_translate("MainWindow", "Ingrese número..."))
        self.label_filterDescrip.setText(_translate("MainWindow", "Descripción:"))
        self.lineEdit__filterDescrip.setPlaceholderText(_translate("MainWindow", "Ingrese descripción..."))
        self.ESTATUS.setTitle(_translate("MainWindow", "ESTATUS"))
        self.pushButton_3.setText(_translate("MainWindow", "SELECCIONAR TODOS"))
        self.FECHA.setTitle(_translate("MainWindow", "FECHA"))
        self.label_amountFacturas_4.setText(_translate("MainWindow", "DESDE:"))
        self.label_amountFacturas_5.setText(_translate("MainWindow", "HASTA:"))
        self.comboBox_FECHA.setItemText(0, _translate("MainWindow", "-"))
        self.comboBox_FECHA.setItemText(1, _translate("MainWindow", "FECHA RECEPCIÓN"))
        self.comboBox_FECHA.setItemText(2, _translate("MainWindow", "FECHA FACTURA"))
        self.comboBox_FECHA.setItemText(3, _translate("MainWindow", "FECHA AUTORIZACIÓN"))
        self.comboBox_FECHA.setItemText(4, _translate("MainWindow", "FECHA PAGADO"))
        self.pushButton_filterFECHA.setText(_translate("MainWindow", "FILTRAR"))
        self.pushButton_cleanFECHA.setText(_translate("MainWindow", "LIMPIAR"))
        self.label_tituloPDF.setText(_translate("MainWindow", "EXPORTAR A PDF"))
        self.PDF_groupBox_ARCHIVOSPDF.setTitle(_translate("MainWindow", "ARCHIVOS PDF"))
        self.PDF_checkBox_FAC.setText(_translate("MainWindow", "FACTURA"))
        self.PDF_checkBox_CR.setText(_translate("MainWindow", "C. RECIBO (SI ESTÁ DISPONIBLE)"))
        self.PDF_checkBox_REM.setText(_translate("MainWindow", "REMISIÓN (SI ESTÁ DISPONIBLE)"))
        self.PDF_checkBox_OC.setText(_translate("MainWindow", "O. COMP. (SI ESTÁ DISPONIBLE)"))
        self.PDF_btn_SelectAll.setText(_translate("MainWindow", "SELECCIONAR TODOS"))
        self.groupbox_Descarga.setTitle(_translate("MainWindow", "DESCARGA"))
        self.radioButton_joinPDF.setText(_translate("MainWindow", "UNIR PDF\'s"))
        self.radioButton_splitPDF.setText(_translate("MainWindow", "ARCHIVOS PDF SEPARADOS"))
        self.PDF_groupBox_Carpetas.setTitle(_translate("MainWindow", "ORGANIZAR EN CARPETAS"))
        self.PDF_checkBox_PROVEEDOR.setText(_translate("MainWindow", "PROVEEDOR"))
        self.PDF_btn_descargar.setText(_translate("MainWindow", "DESCARGAR"))
        self.tablasWidget.setTabText(self.tablasWidget.indexOf(self.ConcentradoTab), _translate("MainWindow", "CONCENTRADO"))
        self.tablasWidget.setTabText(self.tablasWidget.indexOf(self.DesglosadoTab), _translate("MainWindow", "DESGLOSADO"))
        self.actionCONCENTRADO.setText(_translate("MainWindow", "CONCENTRADO"))
        self.actionDESGLOSADO.setText(_translate("MainWindow", "DESGLOSADO"))

    def cerrar_ventana_secundaria(self):
        """
        Método para cerrar la ventana secundaria si está abierta.
        """
        if self.new_window and self.new_window.isVisible():
            self.new_window.close()
            self.new_window = None  # Libera la referencia

    def abrir_nueva_ventana(self):
        # Deshabilitar el botón para evitar aperturas múltiples
        self.pushButton_4.setEnabled(False)

        # Crear una instancia de la nueva ventana
        self.new_window = QWidget()
        self.ui_form = Ui_Form()  # Instanciar la clase de la nueva interfaz
        self.ui_form.setupUi(self.new_window)  # Configurar la nueva ventana

        # Conectar la señal `consulta_exitosa` del formulario a la función para recibir los datos
        self.ui_form.consulta_exitosa.connect(self.recibir_datos_consulta)

        # Sobrescribir el evento de cierre de la ventana para habilitar el botón
        self.new_window.closeEvent = self.habilitar_pushButton_4

        # Mostrar la nueva ventana
        self.new_window.show()

    def closeEvent(self, event):
        """
        Cierra todas las ventanas abiertas al cerrar la principal.
        """
        self.cerrar_ventanas.emit()  # Emite la señal para cerrar la secundaria
        super().closeEvent(event)

    def recibir_datos_consulta(self, formatted_name, df):
        # Guardar los datos recibidos de la consulta
        self.formatted_name_from_consulta = formatted_name
        self.df_from_consulta = df
        # Actualizar el nombre formateado en el QLineEdit
        self.namefile_loadedHTML.setPlainText(formatted_name)

    def habilitar_pushButton_4(self, event):
        # Habilitar el botón nuevamente cuando se cierra la ventana
        self.pushButton_4.setEnabled(True)
        # Asegurarse de que el evento de cierre se propague
        event.accept()

    def on_combobox_fecha_changed(self):
        # Obtener el índice seleccionado y llamar a la función actualizada
        index = self.comboBox_FECHA.currentIndex()
        self.actualizar_filtros_fecha(index)

    def actualizar_filtros_fecha(self, index):
        # Si el índice es 0, significa que el usuario no ha seleccionado ninguna fecha
        if index == 0:
            return

        # Obtener el nombre de la columna de fecha para cada vista
        columna_concentrado = self.columnas_fecha_concentrado.get(index, None)
        columna_desglosado = self.columnas_fecha_desglosado.get(index, None)

        # Configurar el filtro para tableView_concentrado
        if columna_concentrado and self.df_vista is not None:
            try:
                columna_concentrado_idx = self.df_vista.columns.get_loc(columna_concentrado)
                # Actualizar el índice de la columna de fecha en el diccionario column_indices
                self.proxy_model.column_indices['Fecha'] = columna_concentrado_idx
            except KeyError:
                print(f"No se encontró la columna {columna_concentrado} en el DataFrame 'df_vista'")

        # Configurar el filtro para tableView_desglosado
        if columna_desglosado and self.df_unificado is not None:
            try:
                columna_desglosado_idx = self.df_unificado.columns.get_loc(columna_desglosado)
                # Actualizar el índice de la columna de fecha en el diccionario column_indices
                self.proxy_model_desglose.column_indices['Fecha'] = columna_desglosado_idx
            except KeyError:
                print(f"No se encontró la columna {columna_desglosado} en el DataFrame 'df_original'")

        # Invalidate the filters to refresh the views with the new filter criteria
        self.proxy_model.invalidateFilter()
        self.proxy_model_desglose.invalidateFilter()

    def configurar_proxy_model_desglose(self, df_unificado):
        column_mapping = {
            'Obra': df_unificado.columns.get_loc('OBRA'),
            'Proveedor': df_unificado.columns.get_loc('PROVEEDOR'),
            'Residente': df_unificado.columns.get_loc('RESIDENTE'),
            'Fecha': df_unificado.columns.get_loc('FECHA FACTURA'),
            'Estatus': df_unificado.columns.get_loc('ESTATUS'),
            'Número': df_unificado.columns.get_loc('NÚMERO'),
            'Descripción': df_unificado.columns.get_loc('DESCRIPCIÓN'),
            'OrdenOriginal': df_unificado.columns.get_loc('OrdenOriginal'),  # Suponiendo que esta columna existe
        }

        self.proxy_model_desglose.set_column_indices(column_mapping)
        numeric_columns = [
            df_unificado.columns.get_loc('CANTIDAD'),
            df_unificado.columns.get_loc('P. UNITARIO'),
            df_unificado.columns.get_loc('IMPORTE'),
            df_unificado.columns.get_loc('IMPORTE CON DESCUENTO'),
            df_unificado.columns.get_loc('DESCUENTO'),
            df_unificado.columns.get_loc('TOTAL IMPORTE'),
            df_unificado.columns.get_loc('IVA (16%)'),
            df_unificado.columns.get_loc('RET. IVA'),
            df_unificado.columns.get_loc('RET. ISR'),
            df_unificado.columns.get_loc('ISH')
        ]

        date_columns = [
            df_unificado.columns.get_loc('FECHA FACTURA'),
            df_unificado.columns.get_loc('FECHA RECEPCIÓN'),
            df_unificado.columns.get_loc('FECHA PAGADO'),
            df_unificado.columns.get_loc('FECHA AUTORIZACIÓN')
        ]

        self.proxy_model_desglose.invalidateCache()
        self.proxy_model_desglose.set_numeric_columns(numeric_columns)
        self.proxy_model_desglose.set_date_columns(date_columns)
        self.proxy_model_desglose.invalidateFilter()

    def configurar_proxy_model(self, df_vista):
        column_mapping = {
            'Obra': df_vista.columns.get_loc('Obra'),
            'Proveedor': df_vista.columns.get_loc('Proveedor'),
            'Residente': df_vista.columns.get_loc('Residente'),
            'Fecha': df_vista.columns.get_loc('Fecha Factura'),
            'Estatus': df_vista.columns.get_loc('Estatus'),
            'Monto': df_vista.columns.get_loc('Monto'),
            'Número': df_vista.columns.get_loc('Número'),
            'OrdenOriginal': df_vista.columns.get_loc('OrdenOriginal'),  # Suponiendo que esta columna existe

        }

        date_columns = [
            df_vista.columns.get_loc('Fecha Factura'),
            df_vista.columns.get_loc('Fecha Recepción'),
            df_vista.columns.get_loc('Fecha Contrarecibo'),
            df_vista.columns.get_loc('Fecha Autorización'),
            df_vista.columns.get_loc('Fecha Pagada'),
            df_vista.columns.get_loc('Fecha Alta')
        ]

        self.proxy_model.set_column_indices(column_mapping)

        numeric_columns = [column_mapping['Monto']]  # Ajusta según las columnas numéricas de df_vista
        self.proxy_model.invalidateCache()
        self.proxy_model.set_numeric_columns(numeric_columns)
        self.proxy_model.set_date_columns(date_columns)

        self.proxy_model.invalidateFilter()

    def actualizar_status_bar(self, table_view, df):
        # Definir las columnas numéricas específicas para cada tabla
        if table_view == self.tableView_concentrado:
            numeric_columns = [df.columns.get_loc('Monto')]

        elif table_view == self.tableView_desglosado:
            numeric_columns = [
                df.columns.get_loc('CANTIDAD'),
                df.columns.get_loc('P. UNITARIO'),
                df.columns.get_loc('IMPORTE'),
                df.columns.get_loc('IMPORTE CON DESCUENTO'),
                df.columns.get_loc('DESCUENTO'),
                df.columns.get_loc('TOTAL IMPORTE'),
                df.columns.get_loc('IVA (16%)'),
                df.columns.get_loc('RET. IVA'),
                df.columns.get_loc('RET. ISR'),
                df.columns.get_loc('ISH')
            ]
        else:
            # Si se llama desde una tabla no conocida, no hacer nada
            return

        # Verificar si hay una selección activa
        selection_model = table_view.selectionModel()
        selected_indexes = selection_model.selectedIndexes()

        if not selected_indexes:
            # No hay ninguna celda seleccionada
            self.status_promedio.setText("Promedio: 0.00")
            self.status_recuento.setText("Recuento: 0")
            self.status_suma.setText("Suma: 0.00")
            return

        # Variables para almacenar el cálculo
        total_suma = 0.0
        total_recuento = len(selected_indexes)  # Contar todas las celdas seleccionadas, incluyendo no numéricas
        total_numerico = 0

        # Recorrer todos los índices seleccionados para hacer cálculos
        for index in selected_indexes:
            # Verificar si la columna del índice seleccionado está en las columnas numéricas permitidas
            if index.column() in numeric_columns:
                # Intentar convertir el valor a float (si es un valor numérico)
                try:
                    value = float(index.data().replace(',', '').replace('$',
                                                                        ''))  # Quitar separadores de miles y el símbolo de moneda si existe
                    total_suma += value
                    total_numerico += 1  # Solo contar las celdas que tengan un valor numérico
                except (ValueError, AttributeError):
                    pass  # Ignorar si no es un valor numérico

        # Calcular el promedio si hay celdas válidas seleccionadas
        promedio = total_suma / total_numerico if total_numerico > 0 else 0.0

        # Actualizar la barra de estado con los resultados
        self.status_promedio.setText(f"Promedio: {promedio:,.2f}")
        self.status_recuento.setText(f"Recuento: {total_recuento}")
        self.status_suma.setText(f"Suma: {total_suma:,.2f}")

    def exportar_datos_excel(self):
        if self.path_file:
            # Verificar si el checkbox de resumen está marcado y exportar tableView_concentrado
            if self.EXCEL_checkBox_RESUMEN_2.isChecked():
                self.exportar_datos_visibles(self.tableView_concentrado, f"{self.path_file.split('.')[0]}_Resumen")

            # Verificar si el checkbox de desglosado está marcado y exportar tableView_desglosado
            if self.EXCEL_checkBox_DESGLOSADO_2.isChecked():
                self.exportar_datos_visibles(self.tableView_desglosado, f"{self.path_file.split('.')[0]}_Desglosado")
        elif self.df_from_consulta is not None:
            # Verificar si el checkbox de resumen está marcado y exportar tableView_concentrado
            if self.EXCEL_checkBox_RESUMEN_2.isChecked():
                self.exportar_datos_visibles(self.tableView_concentrado, "Consulta_Resumen")

            # Verificar si el checkbox de desglosado está marcado y exportar tableView_desglosado
            if self.EXCEL_checkBox_DESGLOSADO_2.isChecked():
                self.exportar_datos_visibles(self.tableView_desglosado, "Consulta_Desglosado")
        else:
            QtWidgets.QMessageBox.warning(None, "Advertencia", "No se ha analizado ningún archivo.")

    def exportar_datos_visibles(self, table_view, sugerencia_nombre_archivo):
        # Obtener la ruta del Escritorio o Descargas según el sistema operativo
        downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")  # Descargas

        # Definir la ruta por defecto. Aquí se usa la carpeta Descargas
        ruta_por_defecto = os.path.join(downloads_path, f"{sugerencia_nombre_archivo}.xlsx")

        # Abrir QFileDialog para que el usuario seleccione la ruta y el nombre del archivo
        file_dialog = QtWidgets.QFileDialog()
        file_path, _ = file_dialog.getSaveFileName(
            None,
            "Guardar archivo",
            ruta_por_defecto,
            "Archivos Excel (*.xlsx)"
        )

        # Verificar si se seleccionó un archivo o si se canceló el diálogo
        if not file_path:
            QtWidgets.QMessageBox.warning(None, "Advertencia", "No se ha seleccionado ruta de descarga.")
            return

        # Obtener el modelo asociado a la tableView
        model = table_view.model()
        if not model:
            QtWidgets.QMessageBox.warning(None, "Advertencia", "No se ha analizado ningún archivo.")
            return

        # Crear una lista para almacenar los datos visibles
        visible_data = []

        # Verificar si el modelo es un QSortFilterProxyModel (o un proxy model similar)
        if hasattr(model, 'sourceModel'):
            # Extraer el modelo original de datos desde el proxy
            source_model = model.sourceModel()
        else:
            # Asumir que el modelo es directamente un QStandardItemModel
            source_model = model

        # Recorrer todas las filas visibles y obtener los datos originales
        for row in range(model.rowCount()):
            # Si el modelo es un proxy, mapear la fila al índice del modelo fuente
            source_row = model.mapToSource(model.index(row, 0)).row() if hasattr(model, 'mapToSource') else row
            row_data = []

            for col in range(source_model.columnCount()):
                # Obtener el índice en el modelo original y luego el valor de la celda
                index = source_model.index(source_row, col)
                row_data.append(index.data())

            visible_data.append(row_data)

        # Crear un DataFrame de pandas para almacenar los datos visibles
        columns = [source_model.headerData(i, QtCore.Qt.Orientation.Horizontal) for i in
                   range(source_model.columnCount())]
        df_visible = pd.DataFrame(visible_data, columns=columns)

        # Limpiar y convertir columnas específicas a tipo numérico
        columnas_numericas = ['CANTIDAD', 'P. UNITARIO', 'IMPORTE', 'DESCUENTO', 'IMPORTE CON DESCUENTO',
                              'IVA (16%)', 'RET. IVA', 'RET. ISR', 'ISH', 'TOTAL IMPORTE', 'Monto']
        for col in columnas_numericas:
            if col in df_visible.columns:
                # Eliminar caracteres que no sean números, signos negativos, o punto decimal
                df_visible[col] = df_visible[col].replace({r'[^\d.-]': ''}, regex=True)
                # Convertir la columna a tipo numérico
                df_visible[col] = pd.to_numeric(df_visible[col], errors='coerce')

        # Exportar a Excel usando pandas
        if not df_visible.empty:
            try:
                # Primero exportar el DataFrame a Excel
                df_visible.to_excel(file_path, index=False)

                # Abrir el archivo con openpyxl para aplicar el formato de moneda
                workbook = openpyxl.load_workbook(file_path)
                worksheet = workbook.active

                # Aplicar formato de moneda a las columnas de tipo moneda
                columnas_monedas = ['P. UNITARIO', 'IMPORTE', 'DESCUENTO', 'IMPORTE CON DESCUENTO',
                                    'IVA (16%)', 'RET. IVA', 'RET. ISR', 'ISH', 'TOTAL IMPORTE', 'Monto']
                for col_name in columnas_monedas:
                    if col_name in df_visible.columns:
                        # Obtener el índice de la columna (base 1 para openpyxl)
                        col_idx = df_visible.columns.get_loc(col_name) + 1
                        for row in range(2, len(df_visible) + 2):  # Empezar en la fila 2 para omitir encabezados
                            cell = worksheet.cell(row=row, column=col_idx)
                            cell.number_format = numbers.FORMAT_CURRENCY_USD_SIMPLE

                # Guardar los cambios en el archivo Excel
                workbook.save(file_path)

                QtWidgets.QMessageBox.information(None, "Éxito",
                                                  f"Los datos visibles se han exportado exitosamente a {file_path}.")
            except Exception as e:
                QtWidgets.QMessageBox.critical(None, "Error", f"Ocurrió un error al guardar el archivo: {str(e)}")
        else:
            QtWidgets.QMessageBox.warning(None, "Advertencia", "No hay datos visibles para exportar.")

    def descargar_todos_los_xml(self):
        if self.df_original is None:
            QMessageBox.warning(None, "Advertencia", "No se ha cargado ningún archivo para analizar.")
            return

        output_folder = "descargas_temp"
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        # Inicializar la barra de progreso
        total_pasos = len(self.df_original) * 2  # Cada archivo tiene dos pasos: descarga y procesamiento
        self.progressBar.setMaximum(total_pasos)
        self.progressBar.setValue(0)
        self.descargas_completadas = 0

        for idx in range(len(self.df_original)):
            url = self.df_original.iloc[idx].get("XML")

            if pd.notna(url) and isinstance(url, str):
                filename_hash = hashlib.md5(url.encode()).hexdigest() + ".xml"
                worker = DownloadWorker(
                    fila=idx,
                    df_original=self.df_original,
                    ruta_descarga=output_folder,
                    nombre_archivo=filename_hash,
                    columna="XML"
                )
                worker.signals.finished.connect(self.descarga_completada)
                worker.signals.error.connect(self.mostrar_error)
                worker.signals.progress.connect(self.actualizar_progreso_descarga)
                self.thread_pool.start(worker)

    def actualizar_progreso_descarga(self, progreso):
        # Aquí se puede recibir progreso individual del worker
        # Si se desea hacer una actualización más detallada, se puede actualizar aquí
        pass

    def descarga_completada(self):
        self.descargas_completadas += 1
        # Actualizar la barra de progreso al finalizar la descarga
        self.progressBar.setValue(self.descargas_completadas)

        if self.descargas_completadas == len(self.df_original):
            # Todas las descargas han sido completadas
            self.dataframes_descargados = []
            self.procesar_todos_los_xml_descargados()

    def mostrar_error(self, mensaje):
        QMessageBox.critical(None, "Error de descarga", mensaje)

    def mostrar_errores(self):
        if self.errores:
            dialogo = DialogoErrores(self.errores, self)
            dialogo.exec()

    def procesar_todos_los_xml_descargados(self):
        output_folder = "descargas_temp"

        # Contar cuántas veces se requiere cada URL
        url_counts = Counter(self.df_original["XML"].dropna())

        for idx in range(len(self.df_original)):
            url = self.df_original.iloc[idx].get("XML")

            if pd.notna(url) and isinstance(url, str):
                filename_hash = hashlib.md5(url.encode()).hexdigest() + ".xml"
                xml_path = os.path.join(output_folder, filename_hash)

                if os.path.exists(xml_path):
                    # Llamar a la lógica de extracción, pasando la fila correspondiente de df_original
                    row_data = self.df_original.iloc[idx]
                    df_concepto = self.procesar_xml(xml_path, row_data)
                    self.dataframes_descargados.append(df_concepto)

                    # Actualizar la barra de progreso después de procesar cada XML
                    self.progressBar.setValue(len(self.df_original) + idx + 1)

                    # Restar 1 al contador de la URL actual
                    url_counts[url] -= 1

                    # Solo eliminar el archivo XML si es la última vez que se necesita
                    if url_counts[url] == 0:
                        try:
                            os.remove(xml_path)
                        except Exception as e:
                            print(f"Error al eliminar el archivo {xml_path}: {e}")

        self.mostrar_errores()
        # Concatenar todos los DataFrames en uno solo
        df_unificado = pd.concat(self.dataframes_descargados, ignore_index=True)

        # Actualizar los campos de texto en la interfaz
        conceptos_amount = len(df_unificado) * len(df_unificado.columns)
        self.lineEdit_amountConcepto.setText(f"{conceptos_amount:,.0f} | Elementos analizados")

        # Mostrar el desglose en el tableWidget
        self.mostrar_desglose_en_tablewidget(df_unificado)

        # Asegurarse de completar la barra de progreso
        self.progressBar.setValue(self.progressBar.maximum())

        # Eliminar la carpeta de descargas temporales si ya no contiene archivos
        if not os.listdir(output_folder):
            os.rmdir(output_folder)

    from PyQt6.QtWidgets import QMessageBox
    import pandas as pd
    import xml.etree.ElementTree as ET

    def procesar_xml(self, xml_file, row_data):
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            version = root.attrib.get('Version', '4.0')

            # Definir namespaces según la versión
            if version.startswith("4."):
                namespace = {'cfdi': 'http://www.sat.gob.mx/cfd/4'}
            elif version.startswith("3.3"):
                namespace = {'cfdi': 'http://www.sat.gob.mx/cfd/3'}
            else:
                raise ValueError(f"Versión de CFDI no soportada en el archivo {xml_file}.")

            # Verificar si hay conceptos en el XML
            conceptos_nodes = root.findall('.//cfdi:Concepto', namespace)
            if not conceptos_nodes:
                raise ValueError(f"El archivo XML {xml_file} no contiene conceptos válidos.")

            # Procesar los conceptos (lógica existente)
            conceptos = []
            for concepto in conceptos_nodes:
                cantidad = float(concepto.attrib.get('Cantidad', 0))
                clave_prod_serv = concepto.attrib.get('ClaveProdServ', '')
                clave_unidad = concepto.attrib.get('ClaveUnidad', '')
                descripcion = concepto.attrib.get('Descripcion', '')
                valor_unitario = float(concepto.attrib.get('ValorUnitario', 0))
                importe = float(concepto.attrib.get('Importe', 0))
                unidad = concepto.attrib.get('Unidad', '')
                descuento = float(concepto.attrib.get('Descuento', 0))
                importe_con_descuento = importe - descuento

                concepto_data = {
                    'OBRA': row_data.get('Obra', ''),
                    'PROVEEDOR': row_data.get('Proveedor', ''),
                    'RESIDENTE': row_data.get('Residente', ''),
                    'NÚMERO': row_data.get('Número', ''),
                    'ESTATUS': row_data.get('Estatus', ''),
                    'FECHA FACTURA': row_data.get('Fecha Factura', ''),
                    'FECHA RECEPCIÓN': row_data.get('Fecha Recepción', ''),
                    'FECHA PAGADO': row_data.get('Fecha Pagada', ''),
                    'FECHA AUTORIZACIÓN': row_data.get('Fecha Autorización', ''),
                    'CLAVE PROD.': clave_prod_serv,
                    'CLAVE UNID': clave_unidad,
                    'CANTIDAD': cantidad,
                    'DESCRIPCIÓN': descripcion,
                    'UNIDAD': unidad,
                    'P. UNITARIO': valor_unitario,
                    'IMPORTE': importe,
                    'DESCUENTO': descuento,
                    'IMPORTE CON DESCUENTO': importe_con_descuento,
                    'MONEDA': root.attrib.get('Moneda', ''),
                    'IVA (16%)': 0.0,
                    'RET. IVA': 0.0,
                    'RET. ISR': 0.0,
                    'ISH': 0.0,
                    'TOTAL IMPORTE': importe_con_descuento
                }
                conceptos.append(concepto_data)

            df_conceptos = pd.DataFrame(conceptos)
            return df_conceptos

        except ValueError as e:
            # Registrar el error en la lista de errores
            self.errores.append({
                'OBRA': row_data.get('Obra', 'desconocido'),
                'PROVEEDOR': row_data.get('Proveedor', 'desconocido'),
                'NÚMERO': row_data.get('Número', 'desconocido'),
                'ERROR': str(e)
            })
            # Retornar un DataFrame vacío con las columnas esperadas
            columnas = [
                'OBRA', 'PROVEEDOR', 'RESIDENTE', 'NÚMERO', 'ESTATUS',
                'FECHA FACTURA', 'FECHA RECEPCIÓN', 'FECHA PAGADO', 'FECHA AUTORIZACIÓN',
                'CLAVE PROD.', 'CLAVE UNID', 'CANTIDAD', 'DESCRIPCIÓN', 'UNIDAD',
                'P. UNITARIO', 'IMPORTE', 'DESCUENTO', 'IMPORTE CON DESCUENTO', 'MONEDA',
                'IVA (16%)', 'RET. IVA', 'RET. ISR', 'ISH', 'TOTAL IMPORTE'
            ]
            return pd.DataFrame(columns=columnas)

        except Exception as e:
            # Registrar error inesperado en la lista de errores
            self.errores.append({
                'OBRA': row_data.get('Obra', 'desconocido'),
                'PROVEEDOR': row_data.get('Proveedor', 'desconocido'),
                'NÚMERO': row_data.get('Número', 'desconocido'),
                'ERROR': f"Error inesperado: {e}"
            })
            # Retornar un DataFrame vacío con las columnas esperadas
            columnas = [
                'OBRA', 'PROVEEDOR', 'RESIDENTE', 'NÚMERO', 'ESTATUS',
                'FECHA FACTURA', 'FECHA RECEPCIÓN', 'FECHA PAGADO', 'FECHA AUTORIZACIÓN',
                'CLAVE PROD.', 'CLAVE UNID', 'CANTIDAD', 'DESCRIPCIÓN', 'UNIDAD',
                'P. UNITARIO', 'IMPORTE', 'DESCUENTO', 'IMPORTE CON DESCUENTO', 'MONEDA',
                'IVA (16%)', 'RET. IVA', 'RET. ISR', 'ISH', 'TOTAL IMPORTE'
            ]
            return pd.DataFrame(columns=columnas)

    def mostrar_desglose_en_tablewidget(self, df_unificado):
        # Agregar una columna temporal para el índice original
        df_unificado = df_unificado.reset_index().rename(columns={"index": "OrdenOriginal"})
        self.df_unificado = df_unificado

        # Usar el modelo personalizado para el formateo de los valores
        model = FormattedStandardItemModel()
        model.setColumnCount(len(df_unificado.columns))
        model.setHorizontalHeaderLabels(df_unificado.columns)

        # Iterar por cada fila del DataFrame unificado
        for row_idx, row in df_unificado.iterrows():
            items = []

            for col_idx, value in enumerate(row):
                item = QStandardItem()

                # Almacenar el valor numérico en UserRole para ordenación y el valor formateado en DisplayRole
                if isinstance(value, (int, float)):
                    item.setData(value, Qt.ItemDataRole.UserRole)  # Valor sin formato para ordenación y filtrado

                    # Obtener el nombre de la columna para verificar si requiere formato de moneda
                    column_name = df_unificado.columns[col_idx]

                    # Formatear el valor con separador de miles y símbolo de pesos si corresponde
                    formatted_value = "{:,.2f}".format(value)
                    if column_name in model.currency_columns:
                        item.setData(f"${formatted_value}", Qt.ItemDataRole.DisplayRole)
                    else:
                        item.setData(formatted_value, Qt.ItemDataRole.DisplayRole)
                elif pd.notna(value) and isinstance(value, pd.Timestamp):
                    value_str = value.strftime("%d/%m/%Y %H:%M")
                    item.setData(value_str, Qt.ItemDataRole.DisplayRole)
                else:
                    item.setData(str(value), Qt.ItemDataRole.DisplayRole)  # Mostrar el valor como cadena

                items.append(item)

            # Añadir la fila al modelo
            model.appendRow(items)

        self.proxy_model_desglose.setSourceModel(model)
        self.configurar_proxy_model_desglose(df_unificado)

        # Asignar el proxy model al QTableView para mostrarlo
        self.tableView_desglosado.setModel(self.proxy_model_desglose)
        self.tableView_desglosado.setColumnHidden(0, True)  # Asumiendo que "OrdenOriginal" es la primera columna

        # Ajustar las columnas al contenido
        self.tableView_desglosado.resizeColumnsToContents()

        colum_dc = df_unificado.columns.get_loc('DESCRIPCIÓN')
        # Ajustar el ancho de las dos últimas columnas
        self.tableView_desglosado.horizontalHeader().setSectionResizeMode(colum_dc,
                                                                           QHeaderView.ResizeMode.Interactive)
        self.tableView_desglosado.setColumnWidth(colum_dc,
                                                  250)  # Ajustar ancho de penúltima columna
        self.tableView_desglosado.selectionModel().selectionChanged.connect(lambda: self.actualizar_status_bar(self.tableView_desglosado, df_unificado))

    def select_all_pdf(self):
        """Seleccionar o deseleccionar todos los checkboxes en el ListView."""
        # Verificar el estado actual
        nuevo_estado = Qt.CheckState.Checked if not self.todos_seleccionados_PDF else Qt.CheckState.Unchecked

        self.PDF_checkBox_FAC.setCheckState(nuevo_estado)
        self.PDF_checkBox_CR.setCheckState(nuevo_estado)
        self.PDF_checkBox_REM.setCheckState(nuevo_estado)
        self.PDF_checkBox_OC.setCheckState(nuevo_estado)

        # Cambiar el estado de "todos_seleccionados" para la próxima vez
        self.todos_seleccionados_PDF = not self.todos_seleccionados_PDF

    def actualizar_pagina_stackedWidget(self):
        if self.PDF_checkBox_FAC.isChecked() and (self.PDF_checkBox_CR.isChecked() or self.PDF_checkBox_OC.isChecked() or self.PDF_checkBox_REM.isChecked()) and self.radioButton_splitPDF.isChecked() and self.PDF_checkBox_PROVEEDOR.isChecked():
            self.stackedWidget_2.setCurrentIndex(6)
        elif self.PDF_checkBox_FAC.isChecked() and (self.PDF_checkBox_CR.isChecked() or self.PDF_checkBox_OC.isChecked() or self.PDF_checkBox_REM.isChecked()) and self.radioButton_joinPDF.isChecked() and self.PDF_checkBox_PROVEEDOR.isChecked():
            self.stackedWidget_2.setCurrentIndex(7)
        elif self.PDF_checkBox_FAC.isChecked() and (self.PDF_checkBox_CR.isChecked() or self.PDF_checkBox_OC.isChecked() or self.PDF_checkBox_REM.isChecked()) and self.radioButton_joinPDF.isChecked():
            self.stackedWidget_2.setCurrentIndex(8)
        elif self.PDF_checkBox_FAC.isChecked() and (self.PDF_checkBox_CR.isChecked() or self.PDF_checkBox_OC.isChecked() or self.PDF_checkBox_REM.isChecked()) and self.radioButton_splitPDF.isChecked():
            self.stackedWidget_2.setCurrentIndex(5)
        elif self.PDF_checkBox_FAC.isChecked() and self.radioButton_splitPDF.isChecked() and self.PDF_checkBox_PROVEEDOR.isChecked():
            self.stackedWidget_2.setCurrentIndex(4)
        elif self.PDF_checkBox_FAC.isChecked() and self.radioButton_joinPDF.isChecked() and self.PDF_checkBox_PROVEEDOR.isChecked():
            self.stackedWidget_2.setCurrentIndex(3)
        elif self.PDF_checkBox_FAC.isChecked() and self.radioButton_joinPDF.isChecked() and not self.PDF_checkBox_PROVEEDOR.isChecked():
            self.stackedWidget_2.setCurrentIndex(2)
        elif self.PDF_checkBox_FAC.isChecked() and self.radioButton_splitPDF.isChecked() and not self.PDF_checkBox_PROVEEDOR.isChecked():
            self.stackedWidget_2.setCurrentIndex(1)
        else:
            # Opcional: establecer una página por defecto cuando no se cumplen las condiciones
            self.stackedWidget_2.setCurrentIndex(0)

        # Función para manejar la selección de la carpeta y la configuración del progreso

    def descargar_y_preparar_archivo(self, enlace, ruta_archivo):
        """
        Descarga el archivo desde un enlace y lo prepara para su uso (conversión a PDF si es necesario).

        Parámetros:
            enlace (str): URL del archivo a descargar.
            ruta_archivo (str): Ruta completa donde se guardará el archivo.

        Retorna:
            str: Ruta del archivo final, asegurando que es un PDF.
        """
        try:
            # Descargar el archivo desde el enlace
            response = requests.get(enlace, stream=True)
            response.raise_for_status()  # Lanza una excepción si hay un error en la descarga

            # Intentar detectar si es una imagen
            content_type = response.headers.get('Content-Type', '')
            is_image = 'image' in content_type or imghdr.what(None, h=response.content) is not None

            if is_image:
                # Convertir la imagen a PDF
                image = Image.open(io.BytesIO(response.content))
                pdf_path = ruta_archivo.replace(".pdf", "_converted.pdf")
                image.convert("RGB").save(pdf_path, "PDF")
                return pdf_path
            else:
                # Guardar directamente si no es una imagen
                with open(ruta_archivo, "wb") as f:
                    f.write(response.content)
                return ruta_archivo
        except Exception as e:
            print(f"Error al descargar o preparar el archivo: {e}")
            return None

    def iniciar_descarga(self):
        # Paso 1: Determinar las columnas a descargar según los checkboxes
        self.columnas_descarga = []
        if self.PDF_checkBox_FAC.isChecked():
            self.columnas_descarga.append("PDF")
        if self.PDF_checkBox_CR.isChecked():
            self.columnas_descarga.append("C.REC")
        if self.PDF_checkBox_REM.isChecked():
            self.columnas_descarga.append("REM")
        if self.PDF_checkBox_OC.isChecked():
            self.columnas_descarga.append("OC")

        if not self.columnas_descarga:
            QMessageBox.information(self.MainWindow, "Información",
                                    "Por favor, selecciona al menos un tipo de archivo para descargar.")
            return



        # Paso 2: Obtener índices de las filas visibles en `df_vista` usando "OrdenOriginal"
        modelo_filtrado = self.tableView_concentrado.model()
        indices_visibles = [
            int(modelo_filtrado.index(row, 0).data())  # Convertimos OrdenOriginal a entero
            for row in range(modelo_filtrado.rowCount())
        ]

        # Utilizar `df_vista` para encontrar las posiciones en `df_original`
        self.indices_original = self.df_vista[self.df_vista['OrdenOriginal'].isin(indices_visibles)].index.tolist()

        if not self.indices_original:
            QMessageBox.information(self.MainWindow, "Información",
                                    "No hay filas visibles con documentos para descargar.")
            return

        # Paso 3: Configurar unir archivos o descargarlos separados
        unir_pdf = self.radioButton_joinPDF.isChecked()

        # Paso 4: Verificar si se organizará por proveedor
        self.organizar_por_proveedor = self.PDF_checkBox_PROVEEDOR.isChecked()

        # Paso 5: Obtener la ruta de descarga
        ruta_descarga = QFileDialog.getExistingDirectory(self.MainWindow, "Seleccionar carpeta de descarga")
        if not ruta_descarga:
            QMessageBox.warning(self.MainWindow, "Advertencia",
                                "No se seleccionó ninguna carpeta de descarga. Operación cancelada.")
            return
        self.ruta_descarga = ruta_descarga
        # Configurar la barra de progreso
        self.progress_dialog = QProgressDialog("Descargando archivos...", "Cancelar", 0,
                                               len(self.indices_original) * len(self.columnas_descarga),
                                               self.MainWindow)
        self.progress_dialog.setWindowTitle("Progreso de la descarga")
        self.progress_dialog.setValue(0)
        self.progress_dialog.setAutoClose(True)
        self.progress_dialog.setAutoReset(True)
        self.progress_dialog.show()

        # Contador de progreso
        self.descargas_completadas = 0
        self.rutas_archivos_descargados = {}  # Para almacenar las rutas de archivos descargados

        # Función para actualizar la barra de progreso
        def actualizar_progreso22():
            self.descargas_completadas += 1
            self.progress_dialog.setValue(self.descargas_completadas)
            if self.descargas_completadas >= len(self.indices_original) * len(self.columnas_descarga):
                self.unir_pdfs_si_necesario()  # Unir PDF al finalizar todas las descargas
                QMessageBox.information(self.MainWindow, "Descarga Completa", "Todas las descargas han finalizado.")

        # Función para manejar errores
        def manejar_error(mensaje):
            QMessageBox.warning(self.MainWindow, "Error de descarga", mensaje)

        # Crear y ejecutar DownloadWorkers para cada tarea
        indice_archivo = 1
        for idx in self.indices_original:
            fila = self.df_original.loc[idx]
            proveedor = fila["Proveedor"]
            for columna in self.columnas_descarga:
                enlace = fila[columna]
                if pd.notna(enlace) and isinstance(enlace, str):  # Verificar que hay un enlace válido
                    nombre_archivo = f"{indice_archivo}_{fila['Obra']}_{fila['Proveedor']}_{fila['Número']}_{columna}.pdf"
                    ruta_proveedor = os.path.normpath(
                        os.path.join(self.ruta_descarga,
                                     proveedor)) if self.organizar_por_proveedor else self.ruta_descarga

                    # Crear el directorio si no existe
                    os.makedirs(ruta_proveedor, exist_ok=True)

                    # Guardar tarea de descarga
                    tarea = {
                        "fila": idx,
                        "ruta_descarga": ruta_proveedor,
                        "nombre_archivo": nombre_archivo,
                        "columna": columna,
                    }

                    # Guardar ruta para unión de PDF
                    self.guardar_ruta_archivo(tarea)

                    # Crear y configurar DownloadWorker
                    worker = DownloadWorker(
                        fila=idx,
                        df_original=self.df_original,
                        ruta_descarga=tarea["ruta_descarga"],
                        nombre_archivo=tarea["nombre_archivo"],
                        columna=tarea["columna"]
                    )

                    # Conectar señales para manejar progreso y errores
                    worker.signals.progress.connect(actualizar_progreso22)
                    worker.signals.error.connect(manejar_error)

                    # Ejecutar el worker en el thread pool
                    self.thread_pool.start(worker)

                    # Incrementar índice para el siguiente archivo
                    indice_archivo += 1

                else:
                    actualizar_progreso22()

    def guardar_ruta_archivo(self, tarea):
        """Guardar la ruta del archivo descargado para unir después si es necesario."""
        proveedor = tarea["ruta_descarga"].split(os.sep)[-1] if self.organizar_por_proveedor else "General"
        if proveedor not in self.rutas_archivos_descargados:
            self.rutas_archivos_descargados[proveedor] = []
        ruta_archivo = os.path.join(tarea["ruta_descarga"], tarea["nombre_archivo"])
        self.rutas_archivos_descargados[proveedor].append(ruta_archivo)

    def unir_pdfs_si_necesario(self):
        """Unir archivos PDF descargados según los escenarios A y B."""
        if not self.radioButton_joinPDF.isChecked():
            return

        # Escenario A: Solo una columna seleccionada
        if len(self.columnas_descarga) == 1:
            # Caso especial: unir en la carpeta seleccionada por el usuario sin separar por proveedor
            if not self.organizar_por_proveedor:

                self.unir_archivos_en_carpeta_general()  # Función específica para este caso
            else:
                # Caso cuando se organiza por proveedor
                for proveedor, archivos in self.rutas_archivos_descargados.items():
                    if archivos:
                        nombre_unico = f"{proveedor}_{self.columnas_descarga[0]}.pdf"
                        self.unir_y_guardar_archivos(archivos, os.path.join(self.ruta_descarga, proveedor, nombre_unico))

        # Escenario B: Varias columnas seleccionadas
        else:
            for idx in self.indices_original:
                fila = self.df_original.loc[idx]
                columnas_dwn = ['PDF', 'C.REC', 'OC', 'REM']

                if fila[columnas_dwn].isna().all():
                    continue  # Saltar al siguiente índice si todas las columnas son nulas

                proveedor = fila["Proveedor"]
                # Obtener archivos correspondientes a la fila actual, considerando si "organizar por proveedor" está activado
                if self.organizar_por_proveedor:
                    archivos_por_fila = [
                        archivo for archivo in self.rutas_archivos_descargados.get(proveedor, [])
                        if f"_{fila['Número']}_" in archivo
                    ]
                else:
                    # Buscar en "General" si no se organiza por proveedor
                    archivos_por_fila = [
                        archivo for archivo in self.rutas_archivos_descargados.get("General", [])
                        if f"_{fila['Número']}_" in archivo
                    ]

                if archivos_por_fila:
                    # Generar el nombre del archivo combinado para la fila actual
                    columnas_str = "_".join(columna.replace(".", "") for columna in self.columnas_descarga)
                    nombre_por_fila = f"{idx + 1}_{fila['Obra']}_{fila['Proveedor']}_{columnas_str}.pdf"
                    ruta_destino = os.path.join(self.ruta_descarga, proveedor, nombre_por_fila) if self.organizar_por_proveedor else os.path.join(self.ruta_descarga, nombre_por_fila)
                    self.unir_y_guardar_archivos(archivos_por_fila, ruta_destino)

    def unir_archivos_en_carpeta_general(self):
        """Unir archivos PDF en la carpeta general sin separar por proveedor (caso especial)."""
        # Obtener todos los archivos bajo la clave "General"
        archivos = self.rutas_archivos_descargados.get("General", [])
        if archivos:
            # Generar el nombre del archivo combinado con la ruta de descarga elegida
            nombre_unico = f"{QFileInfo(self.path_file).fileName()}_{self.columnas_descarga[0]}.pdf"

            ruta_final = os.path.join(self.ruta_descarga, nombre_unico)
            self.unir_y_guardar_archivos(archivos, ruta_final)

    def unir_y_guardar_archivos(self, archivos, ruta_destino):
        """Unir archivos PDF y guardar en una ruta específica, eliminando los archivos individuales."""
        if not archivos:
            return

        # Crear y guardar el PDF unido en la ruta de destino especificada
        with pikepdf.Pdf.new() as pdf_unido:
            for archivo in archivos:
                archivo = os.path.normpath(archivo)
                if os.path.exists(archivo):
                    with pikepdf.open(archivo) as pdf:
                        pdf_unido.pages.extend(pdf.pages)
                    os.remove(archivo)  # Eliminar el archivo individual después de unirlo
            pdf_unido.save(ruta_destino)

    def mostrar_alerta_combinacion(self):
        mensaje = (
            "Por favor, realice una combinación de opciones para visualizar los ejemplos "
            "de cómo se descargarán los archivos. Asegúrese de seleccionar al menos una "
            "opción en 'ARCHIVOS PDF' y un método de descarga en 'DESCARGA'."
        )

        alerta = QMessageBox()
        alerta.setIcon(QMessageBox.Icon.Warning)
        alerta.setWindowTitle("Selección de Opciones Necesaria")
        alerta.setText(mensaje)
        alerta.setStandardButtons(QMessageBox.StandardButton.Ok)
        alerta.exec()

    def seleccionar_obras(self):
        """Abrir diálogo para seleccionar varias obras."""
        if self.df_vista is not None and 'Obra' in self.df_vista.columns:
            items = self.df_vista['Obra'].dropna().unique().tolist()
            dialog = MultiSelectDialog(items, parent=self.MainWindow)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                seleccionados = dialog.get_selected_items()
                self.lineEdit_filterObra.setText(", ".join(seleccionados))
                # Actualiza el filtro del proxy model según sea necesario
        else:
            # Mostrar alerta al usuario
            QMessageBox.warning(self.MainWindow, "Análisis requerido", "Primero debe realizar el análisis del archivo HTML para poder seleccionar obras.")

    def seleccionar_proveedores(self):
        """Abrir diálogo para seleccionar varios proveedores."""
        if self.df_vista is not None and 'Proveedor' in self.df_vista.columns:
            items = self.df_vista['Proveedor'].dropna().unique().tolist()
            dialog = MultiSelectDialog(items, parent=self.MainWindow)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                seleccionados = dialog.get_selected_items()
                self.lineEdit__filterProveedor.setText(", ".join(seleccionados))
                # Actualiza el filtro del proxy model según sea necesario
        else:
            # Mostrar alerta al usuario
            QMessageBox.warning(self.MainWindow, "Análisis requerido", "Primero debe realizar el análisis del archivo HTML para poder seleccionar proveedores.")

    def seleccionar_residentes(self):
        """Abrir diálogo para seleccionar varios residentes."""
        if self.df_vista is not None and 'Residente' in self.df_vista.columns:
            items = self.df_vista['Residente'].dropna().unique().tolist()
            dialog = MultiSelectDialog(items, parent=self.MainWindow)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                seleccionados = dialog.get_selected_items()
                self.lineEdit__filterResidente.setText(", ".join(seleccionados))
                # Actualiza el filtro del proxy model según sea necesario
        else:
            # Mostrar alerta al usuario
            QMessageBox.warning(self.MainWindow, "Análisis requerido", "Primero debe realizar el análisis del archivo HTML para poder seleccionar residentes.")

    def seleccionar_todos_estatus(self):
        """Seleccionar o deseleccionar todos los checkboxes en el ListView."""
        # Verificar el estado actual
        nuevo_estado = Qt.CheckState.Checked if not self.todos_seleccionados else Qt.CheckState.Unchecked

        # Actualizar todos los elementos del modelo
        for i in range(self.listView_model.rowCount()):
            item = self.listView_model.item(i)
            item.setCheckState(nuevo_estado)

        # Cambiar el estado de "todos_seleccionados" para la próxima vez
        self.todos_seleccionados = not self.todos_seleccionados

    def cargar_estatus_en_listview(self):
        """Cargar los valores únicos de 'Estatus' en la lista de checkboxes."""
        try:
            # Verificar si df_vista está inicializado
            if self.df_vista is None:
                raise ValueError("El DataFrame 'df_vista' no está cargado. Por favor, carga los datos primero.")

            # Verificar si la columna 'Estatus' existe en df_vista
            if 'Estatus' not in self.df_vista.columns:
                raise ValueError("La columna 'Estatus' no existe en el DataFrame 'df_vista'. Verifica los datos.")

            # Limpiar el modelo existente en el QListView
            self.listView_model.clear()

            # Obtener los valores únicos de 'Estatus' del DataFrame
            estatus_unicos = self.df_vista['Estatus'].dropna().unique()
            if estatus_unicos is None or len(estatus_unicos) == 0:
                raise ValueError("No se encontraron valores únicos en la columna 'Estatus'.")

            # Crear un item para cada valor de estatus y hacerlo checkable
            for estatus in estatus_unicos:
                item = QStandardItem(estatus)
                item.setCheckable(True)
                item.setEditable(False)  # Evitar que el usuario edite el texto

                # Aumentar el tamaño de la fuente de cada elemento
                font = QFont()
                font.setPointSize(11)  # Aumentar el tamaño de la fuente, puedes ajustar este valor
                item.setFont(font)

                self.listView_model.appendRow(item)

            # Conectar el cambio de checkboxes al filtrado
            self.listView_model.itemChanged.connect(self.actualizar_filtro_estatus)

        except Exception as e:
            # Mostrar el error usando QMessageBox para que sea visible para el usuario
            error_msg = QMessageBox()
            error_msg.setIcon(QMessageBox.Icon.Critical)
            error_msg.setWindowTitle("Error")
            error_msg.setText(f"Ocurrió un error al procesar el archivo: {str(e)}")
            error_msg.exec()

    def actualizar_filtro_estatus(self):
        """Actualizar el filtro del DataFrame con base en los estatus seleccionados."""
        estatus_seleccionados = []

        # Iterar sobre todos los elementos del modelo y verificar cuáles están seleccionados
        for i in range(self.listView_model.rowCount()):
            item = self.listView_model.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                estatus_seleccionados.append(item.text())

        # Pasar la lista de estatus seleccionados al proxy model para filtrar
        self.proxy_model.set_filter_estatus(estatus_seleccionados)
        self.proxy_model_desglose.set_filter_estatus(estatus_seleccionados)

    def actualizar_fecha_combo_box(self, table_view, df):
        combo_index = self.comboBox_FECHA.currentIndex()

        # Definir las columnas numéricas específicas para cada tabla
        if table_view is self.tableView_concentrado:
            # Mapeo del índice del comboBox a las columnas del DataFrame
            if combo_index == 1:
                fecha_column_index = df.columns.get_loc('Fecha Recepción')  # FECHA RECEPCIÓN
            elif combo_index == 2:
                fecha_column_index = df.columns.get_loc('Fecha Factura')  # FECHA FACTURA
            elif combo_index == 3:
                fecha_column_index = df.columns.get_loc('Fecha Autorización')  # FECHA AUTORIZACIÓN
            elif combo_index == 4:
                fecha_column_index = df.columns.get_loc('Fecha Pagada')  # FECHA PAGADO
            else:
                fecha_column_index = df.columns.get_loc('Fecha Factura')  # Valor por defecto

            # Establecer el índice de la columna de fecha en el modelo proxy
            self.proxy_model.set_fecha_column_index(fecha_column_index)

        elif table_view is self.tableView_desglosado:
            # Mapeo del índice del comboBox a las columnas del DataFrame
            if combo_index == 1:
                fecha_column_index = df.columns.get_loc('FECHA RECEPCIÓN')  # FECHA RECEPCIÓN
            elif combo_index == 2:
                fecha_column_index = df.columns.get_loc('FECHA FACTURA')  # FECHA FACTURA
            elif combo_index == 3:
                fecha_column_index = df.columns.get_loc('FECHA AUTORIZACIÓN')  # FECHA AUTORIZACIÓN
            elif combo_index == 4:
                fecha_column_index = df.columns.get_loc('FECHA PAGADO')  # FECHA PAGADO
            else:
                fecha_column_index = df.columns.get_loc('FECHA FACTURA')  # Valor por defecto

            # Establecer el índice de la columna de fecha en el modelo proxy
            self.proxy_model_desglose.set_fecha_column_index(fecha_column_index)

    def mostrar_menu_contextual(self, posicion):
            # Crear el menú contextual
            menu = QMenu(self.tableView_concentrado)

            # Crear acción de descargar archivo y conectarla con la función correspondiente
            descargar_archivo_accion = QAction("Descargar factura PDF", self.tableView_concentrado)
            descargar_rem_action = QAction("Descargar remisión PDF", self.tableView_concentrado)
            descargar_OC_action = QAction("Descargar orden de compra PDF", self.tableView_concentrado)
            descargar_todos_juntos = QAction("Todos los archivos disponibles", self.tableView_concentrado)

            descargar_archivo_accion.triggered.connect(lambda: self.descargar_archivo_menu(["PDF"]))
            descargar_rem_action.triggered.connect(lambda: self.descargar_archivo_menu(["REM"]))
            descargar_OC_action.triggered.connect(lambda: self.descargar_archivo_menu(["OC"]))
            descargar_todos_juntos.triggered.connect(lambda: self.descargar_archivo_menu(["PDF","REM","OC"]))

            # Agregar la acción al menú
            menu.addAction(descargar_archivo_accion)
            menu.addAction(descargar_rem_action)
            menu.addAction(descargar_OC_action)
            menu.addAction(descargar_todos_juntos)

            # Mostrar el menú contextual en la posición del cursor
            menu.exec(self.tableView_concentrado.viewport().mapToGlobal(posicion))

    def descargar_archivo_menu(self, tipos_archivo):
        indices = self.tableView_concentrado.selectionModel().selectedIndexes()

        if not indices:
            QMessageBox.warning(None, "Advertencia", "No se seleccionó ninguna celda o fila.")
            return

        filas_seleccionadas = sorted(set(index.row() for index in indices))
        filas_originales = [self.proxy_model.mapToSource(self.proxy_model.index(fila, 0)).row() for fila in
                            filas_seleccionadas]

        ruta_descarga = QFileDialog.getExistingDirectory(None, "Seleccionar Carpeta de Descarga",
                                                         os.path.expanduser("~"))
        if not ruta_descarga:
            QMessageBox.information(None, "Información", "No se seleccionó ninguna ruta de descarga.")
            return

        errores, contador_tareas, total_tareas = [], 0, 0
        progreso = QProgressDialog("Descargando archivos...", "Cancelar", 0, len(filas_originales))
        progreso.setWindowTitle("Progreso")
        progreso.setWindowModality(Qt.WindowModality.WindowModal)
        progreso.setValue(0)

        # Función para actualizar progreso y manejar errores
        def actualizar_progreso(valor):
            progreso.setValue(progreso.value() + valor)

        def registrar_error(mensaje):
            errores.append(mensaje)

        # Función para combinar y eliminar archivos
        def combinar_y_eliminar(obra, proveedor, numero, pdf_paths):
            if len(pdf_paths) > 1:
                nombre_combinado = f"{obra}_{proveedor}_{numero}_combinado.pdf"
                ruta_combinada = os.path.join(ruta_descarga, nombre_combinado)

                try:
                    with pikepdf.Pdf.new() as pdf_combined:
                        for pdf_path in pdf_paths:
                            with pikepdf.open(pdf_path) as pdf:
                                pdf_combined.pages.extend(pdf.pages)
                        pdf_combined.save(ruta_combinada)

                    for pdf_path in pdf_paths:
                        os.remove(pdf_path)

                except Exception as e:
                    errores.append(f"Error combinando archivos para {nombre_combinado}: {e}")

        archivos_descargados = {fila: 0 for fila in filas_originales}

        def finalizar_descarga(fila, obra, proveedor, numero, pdf_paths):
            nonlocal contador_tareas
            contador_tareas += 1
            archivos_descargados[fila] += 1

            if archivos_descargados[fila] == len(pdf_paths) and len(pdf_paths) > 1:
                combinar_y_eliminar(obra, proveedor, numero, pdf_paths)

            if contador_tareas == total_tareas:
                if progreso.wasCanceled():
                    QMessageBox.information(None, "Cancelado", "La descarga ha sido cancelada.")
                elif errores:
                    QMessageBox.critical(None, "Errores en la descarga", "\n".join(errores))
                else:
                    QMessageBox.information(None, "Éxito", "Todos los archivos se descargaron correctamente.")

        # Generar tareas y lanzar workers
        contador = 1
        for fila in filas_originales:
            obra, proveedor, numero = self.df_original.iloc[fila]['Obra'], self.df_original.iloc[fila][
                'Proveedor'], str(self.df_original.iloc[fila]['Número'])
            pdf_paths = []

            for tipo in tipos_archivo:
                enlace_pdf = self.df_original.iloc[fila][tipo]
                if pd.notna(enlace_pdf) and enlace_pdf != "NA" and isinstance(enlace_pdf, str):
                    total_tareas += 1

                    nombre_archivo = f"{contador}_{obra}_{proveedor}_{numero}_{tipo}.pdf"
                    nombre_archivo = re.sub(r'[\\/*?:"<>|&]', '_', nombre_archivo)
                    pdf_path = os.path.join(ruta_descarga, nombre_archivo)
                    pdf_paths.append(pdf_path)

                    worker = DownloadWorker(fila, self.df_original, ruta_descarga, nombre_archivo, tipo)
                    worker.signals.progress.connect(actualizar_progreso)
                    worker.signals.error.connect(registrar_error)
                    worker.signals.finished.connect(
                        lambda f=fila, o=obra, p=proveedor, n=numero, pp=pdf_paths: finalizar_descarga(f, o, p, n, pp))

                    self.thread_pool.start(worker)
                contador += 1

        progreso.canceled.connect(lambda: self.thread_pool.clear())

        if total_tareas == 0:
            QMessageBox.warning(None, "Advertencia", "No se encontraron archivos válidos para descargar.")

    def analizar(self):  # No recibe parámetros
        try:
            # Verificar si hay un DataFrame desde la consulta
            if hasattr(self, 'df_from_consulta') and self.df_from_consulta is not None:
                # Si existe un DataFrame de la consulta, usarlo directamente
                df = self.df_from_consulta
                # Procesar las columnas específicas (aplica a ambos casos)
                self.df_original, df_vista = self.procesar_columnas(df, 2)

                # Limpiar columnas irrelevantes y mostrar en la interfaz
                self.mostrar_datos(df_vista, self.df_original, 2)
            else:
                # Si no hay DataFrame de la consulta, verificar si hay un archivo cargado
                if not hasattr(self, 'path_file') or not self.path_file:
                    QMessageBox.warning(None, "Advertencia",
                                        "No se ha seleccionado ningún archivo para analizar ni se realizó una consulta.")
                    return

                # Leer y procesar el contenido del archivo HTML
                contenido_html = self.leer_archivo_html(self.path_file)
                soup = BeautifulSoup(contenido_html, 'html.parser')

                # Extraer la tabla y convertirla en un DataFrame
                tabla = soup.find('table', id='tbaFacturasNC')
                if not tabla:
                    QMessageBox.critical(None, "Error",
                                         "No se encontró la tabla 'Facturas Portal' en el archivo seleccionado.")
                    return

                # Procesar la tabla HTML para obtener el DataFrame
                df = self.extraer_datos_tabla(tabla)

                # Procesar las columnas específicas (aplica a ambos casos)
                df_original, df_vista = self.procesar_columnas(df,1)

                # Limpiar columnas irrelevantes y mostrar en la interfaz
                self.mostrar_datos(df_vista, df_original, 1)

        except Exception as e:
            # Manejo de cualquier otro error inesperado
            QMessageBox.critical(None, "Error", f"Ocurrió un error al procesar el archivo o los datos: {e}")

    def leer_archivo_html(self, ruta_archivo):
            """Lee y retorna el contenido del archivo HTML."""
            with open(ruta_archivo, 'r', encoding='utf-8') as archivo:
                    return archivo.read()

    def extraer_datos_tabla(self, tabla):
        """Convierte una tabla HTML en un DataFrame de Pandas, recopilando atributos 'onclick' y 'class'."""
        # Extraer encabezados
        encabezados = [th.get_text(strip=True) for th in
                       tabla.find('thead', class_='text-warning').find_all('th')]

        # Extraer filas
        filas = []
        for tr in tabla.find('tbody', id='theListNC').find_all('tr'):
            fila = []
            for i, td in enumerate(tr.find_all('td')):
                # Procesar columnas específicas con enlaces
                if i in [7, 8, 9, 10, 11, 12, 13]:
                    enlace = td.find('a')
                    if enlace:
                        onclick = enlace.get('onclick', None)
                        clase = enlace.get('class', None)
                        # Guardar los valores en una tupla
                        fila.append((onclick, ' '.join(clase) if clase else None))
                    else:
                        fila.append((None, None))  # Enlace no presente
                else:
                    # Otras columnas simplemente toman su texto
                    fila.append(td.get_text(strip=True))
            filas.append(fila)

        # Ajustar encabezados para las columnas con enlaces
        for i in [7, 8]:
            encabezados[i] = f"{encabezados[i]}_data"  # Cambia el nombre para reflejar que es un dato compuesto

        return pd.DataFrame(filas, columns=encabezados)

    def extraer_fechas(self, historial_data):
        """
        Extrae y retorna las fechas de un atributo 'onclick' del historial.
        Si 'onclick' no tiene un formato válido, retorna una lista de valores nulos.

        Parámetros:
            historial_data (tuple): Una tupla con el 'onclick' y el atributo 'class' (onclick, class).

        Retorna:
            list: Fechas extraídas (fFactura, fRecepcion, fContra, fAutoriza, fPaga, fAlta) o [None] * 6 si no son válidas.
        """
        if not historial_data or not isinstance(historial_data, tuple) or not historial_data[0]:
            return [None] * 6  # Retornar valores nulos si no hay 'onclick'

        onclick = historial_data[0]  # Primer elemento de la tupla (el atributo 'onclick')
        try:
            # Extraer datos si el 'onclick' contiene el formato esperado
            if "OpenmodalFechas" in onclick:
                fechas = onclick.replace("OpenmodalFechas(", "").replace("); return false", "").replace("'", "").split(
                    ',')
                return [fecha.strip() if fecha.strip() != '-' else None for fecha in fechas]
        except Exception as e:
            print(f"Error al procesar historial: {e}")  # Depuración

        return [None] * 6  # Retornar valores nulos si ocurre un error

    def extraer_comentarios(self, comentarios_data):
        """
        Extrae los comentarios y observaciones del atributo 'onclick' utilizando expresiones regulares.

        Parámetros:
            comentarios_data (tuple): Una tupla con el 'onclick' y el atributo 'class' (onclick, class).

        Retorna:
            tuple: (comentarios_web, observaciones_hilo), o (None, None) si no son válidos.
        """
        if not comentarios_data or not isinstance(comentarios_data, tuple) or not comentarios_data[0]:
            return None, None  # Retornar valores nulos si no hay 'onclick'

        onclick = comentarios_data[0]  # Primer elemento de la tupla (el atributo 'onclick')
        try:
            # Verificar si el 'onclick' contiene el patrón esperado
            if "show_modalPopUpFacturaObs" in onclick:
                # Usar expresiones regulares para extraer las dos partes de la cadena
                pattern = r"show_modalPopUpFacturaObs\('([^']*)','([^']*)'\);"
                match = re.search(pattern, onclick)
                if match:
                    comentarios_web = match.group(1).replace("_lnfd_", "\n").strip()
                    observaciones_hilo = match.group(2).replace("_lnfd_", "\n").strip()
                    return comentarios_web, observaciones_hilo
        except Exception as e:
            print(f"Error al procesar comentarios: {e}")  # Depuración

        return None, None  # Retornar valores nulos si ocurre un error

    def generar_link(self, onclick, columna, clase):
        """Genera el enlace de descarga según el 'onclick', la columna y verifica la clase."""
        # Verificar si la clase indica que el enlace es válido
        if not clase or not any(
                valid_class in clase.lower() for valid_class in ["btn btn-primary btn-sm", "btn btn-info btn-sm"]):
            return None  # Retornar nulo si la clase no es válida

        # Procesar el atributo "onclick"
        if onclick:
            valores = onclick.replace("openXML(", "").replace("openContrareciboRdte(", "").replace(
                "); return false", "").replace("'", "").split(',')
            if len(valores) >= 2:
                id_val, file_val = valores[0].strip(), valores[1].strip()
                contrarecibo_val = '1' if columna == 'C.REC' else '0'
                # Generar el enlace si "file_val" tiene un valor válido
                return f"https://palmaterraproveedores.centralinformatica.com/Download.ashx?id={file_val}&rfc={id_val}&contrarecibo={contrarecibo_val}" if file_val else None

        return None  # Retornar nulo si no se puede procesar

    def procesar_columnas(self, df, type):
        if type == 1:
            """Procesa las columnas de fechas, comentarios y enlaces, y retorna dos versiones del DataFrame."""
            # Extraer fechas y comentarios
            df[['Fecha Factura', 'Fecha Recepción', 'Fecha Contrarecibo', 'Fecha Autorización', 'Fecha Pagada',
                'Fecha Alta']] = (
                df['Historial_data']
                .apply(self.extraer_fechas)  # Aplica la función para extraer las fechas
                .apply(pd.Series)  # Divide la lista resultante en columnas separadas
            )

            df[['Comentarios proveedor', 'Observaciones facturación']] = df['Comentarios_data'].apply(
                self.extraer_comentarios
            ).apply(pd.Series)

            for col in ['XML', 'PDF', 'C.REC', 'OC', 'REM']:
                df[col] = df[col].apply(
                    lambda data: self.generar_link(data[0], col, data[1]) if data else None
                )

            # Crear una vista simplificada para la interfaz
            df_vista = df.copy()
            for col in ['XML', 'PDF', 'C.REC', 'OC', 'REM']:
                    df_vista[col] = df_vista[col].apply(lambda x: "✅" if x is not None else "❌")

            return df, df_vista
        elif type==2:
            # Crear una vista simplificada para la interfaz
            df_vista = df.copy()
            for col in ['XML', 'PDF', 'C.REC', 'OC', 'REM']:
                    df_vista[col] = df_vista[col].apply(lambda x: "✅" if x is not None else "❌")

            return df, df_vista

    def mostrar_datos(self, df_vista, df_original, type):
        if type == 1:
            """Muestra los datos en la interfaz y calcula el monto total."""

            # Eliminar columnas innecesarias para la vista
            df_vista = df_vista.drop(columns=["NC", "F.Factura", "Historial_data", "Comentarios_data"], errors='ignore')
            df_original = df_original.drop(columns=["NC", "F.Factura", "Historial_data", "Comentarios_data"], errors='ignore')

            # Convertir columnas de fechas a formato datetime en df_vista y df_original
            for idx in range(11, 17):
                if idx < len(df_vista.columns):
                    column_name = df_vista.columns[idx]
                    df_vista[column_name] = pd.to_datetime(df_vista[column_name], format="%d/%m/%y %H:%M", errors='coerce')

                if idx < len(df_original.columns):
                    column_name = df_original.columns[idx]
                    df_original[column_name] = pd.to_datetime(df_original[column_name], format="%d/%m/%y %H:%M",
                                                          errors='coerce')
        elif type == 2:
            # Convertir columnas de fechas a formato datetime en df_vista y df_original
            for idx in range(12, 18):
                if idx < len(df_vista.columns):
                    column_name = df_vista.columns[idx]
                    df_vista[column_name] = pd.to_datetime(df_vista[column_name], format="%d/%m/%y %H:%M",
                                                           errors='coerce')

                if idx < len(df_original.columns):
                    column_name = df_original.columns[idx]
                    df_original[column_name] = pd.to_datetime(df_original[column_name], format="%d/%m/%y %H:%M",
                                                              errors='coerce')

        self.df_vista = df_vista
        self.df_original = df_original


        # Calcular y mostrar el monto total
        df_vista["Monto"] = df_vista["Monto"].replace(r'[\$,]', '', regex=True).astype(float)
        monto_total = df_vista["Monto"].sum()

        # Mostrar el DataFrame en el QTableWidget (asume que mostrar_dataframe_en_tablewidget está adaptado a PyQt6)
        self.mostrar_dataframe_en_tablewidget(df_vista)
        self.cargar_estatus_en_listview()

        # Actualizar los campos de texto en la interfaz
        self.lineEdit_amountMonto.setText(f"${monto_total:,.2f} | IVA Incluido")
        self.lineEdit_amountFacturas.setText(f"{len(df_vista)} Facturas")

        self.mostrar_desglose()

    # Nueva función para mostrar el desglose
    def mostrar_desglose(self):
        """Descarga y muestra el desglose detallado de todas las facturas en tableView_desglosado."""

        if self.df_original is None:
            QMessageBox.warning(None, "Advertencia", "No hay datos disponibles para mostrar el desglose.")
            return

        # Obtener la lista de URLs de los XML
        lista_urls = self.df_original['XML'].dropna().tolist()

        if not lista_urls:
            QMessageBox.warning(None, "Advertencia", "No hay enlaces XML disponibles para descargar.")
            return

        # Iniciar la descarga y procesamiento de los XML
        self.descargar_todos_los_xml()

    def mostrar_dataframe_en_tablewidget(self, df_vista):
        # Agregar una columna temporal para el índice original
        df_vista = df_vista.reset_index().rename(columns={"index": "OrdenOriginal"})
        self.df_vista = df_vista

        # Crear el modelo estándar para cargar los datos
        model = QStandardItemModel()
        model.setColumnCount(len(df_vista.columns))
        model.setHorizontalHeaderLabels(df_vista.columns)

        # Iterar por cada fila del DataFrame
        for row_idx, row in df_vista.iterrows():
            items = []

            for col_idx, value in enumerate(row):
                item = QStandardItem()

                if col_idx == df_vista.columns.get_loc('OrdenOriginal'):  # Columna "OrdenOriginal"
                    item.setData(int(value), Qt.ItemDataRole.UserRole)  # Almacenar como número para ordenación
                    item.setData(str(value), Qt.ItemDataRole.DisplayRole)  # Mostrar como texto
                elif pd.notna(value) and isinstance(value, pd.Timestamp):
                    value_str = value.strftime("%d/%m/%Y %H:%M")
                    item.setData(value_str, Qt.ItemDataRole.DisplayRole)
                elif col_idx == df_vista.columns.get_loc('Monto'):  # Ajuste de índice para la columna "Monto"
                    item.setData(value,
                                 Qt.ItemDataRole.UserRole)  # Guarda el valor numérico en UserRole para ordenación
                    item.setData(f"${value:,.2f}", Qt.ItemDataRole.DisplayRole)  # Formato de moneda
                else:
                    item.setData(str(value), Qt.ItemDataRole.DisplayRole)  # Mostrar el valor como cadena

                items.append(item)

            model.appendRow(items)

        # Asignar el modelo al proxy y luego al QTableView
        self.proxy_model.setSourceModel(model)
        self.configurar_proxy_model(df_vista)

        self.tableView_concentrado.setModel(self.proxy_model)
        self.tableView_concentrado.setColumnHidden(0, True)  # Asumiendo que "OrdenOriginal" es la primera columna

        # Ajustar las columnas al contenido
        self.tableView_concentrado.resizeColumnsToContents()
        self.tableView_concentrado.selectionModel().selectionChanged.connect(lambda: self.actualizar_status_bar(self.tableView_concentrado, df_vista))


        # Obtener el número total de columnas en el modelo de datos
        total_columns = self.tableView_concentrado.model().columnCount()

        # Ajustar el tamaño de las últimas dos columnas si hay al menos dos columnas
        if total_columns >= 2:
            # Índice de la penúltima columna
            penultimate_column_index = total_columns - 2
            # Índice de la última columna
            last_column_index = total_columns - 1

            # Ajustar el ancho de las dos últimas columnas
            self.tableView_concentrado.horizontalHeader().setSectionResizeMode(penultimate_column_index,
                                                                               QHeaderView.ResizeMode.Interactive)
            self.tableView_concentrado.horizontalHeader().setSectionResizeMode(last_column_index,
                                                                               QHeaderView.ResizeMode.Interactive)
            self.tableView_concentrado.setColumnWidth(penultimate_column_index,
                                                      200)  # Ajustar ancho de penúltima columna
            self.tableView_concentrado.setColumnWidth(last_column_index, 200)

    def clear_all_filters(self):
            # Limpiar los campos de entrada
            self.tableView_desglosado.sortByColumn(0, Qt.SortOrder.AscendingOrder)
            self.tableView_concentrado.sortByColumn(0, Qt.SortOrder.AscendingOrder)

            self.dateEdit.setDate(QDate.currentDate())
            self.dateEdit_2.setDate(QDate.currentDate())
            self.comboBox_FECHA.setCurrentIndex(0)
            # Limpiar los filtros en el modelo proxy
            self.proxy_model.clear_filters()
            self.proxy_model_desglose.clear_filters()

    def seleccionar_archivos(self):
            self.df_from_consulta = None
            # Cambiamos a getOpenFileName para permitir solo un archivo
            file, _ = QFileDialog.getOpenFileName(None, "Seleccionar Archivo HTML", "",
                                                  "HTML Files (*.html);;All Files (*)")
            # Verificar si se ha seleccionado un archivo válido (es decir, no está vacío)
            if file and file.strip():
                    # Si el archivo es válido, guardamos la ruta y actualizamos el LineEdit con el nombre del archivo
                    self.path_file = file  # ruta de archivo

                    # Obtenemos solo el nombre del archivo sin la ruta completa
                    file_name = QFileInfo(file).fileName()  # NOMBRE de archivo

                    # Mostramos el nombre del archivo en el QLineEdit
                    self.namefile_loadedHTML.setPlainText(file_name)
            else:
                    self.limpiar_interfaz()

    def limpiar_interfaz(self):
        # Limpiar la tabla QTableView
        self.tableView_concentrado.setModel(None)
        self.tableView_desglosado.setModel(None)
        self.namefile_loadedHTML.clear()

        self.lineEdit_amountFacturas.clear()
        self.lineEdit_amountMonto.clear()
        self.lineEdit_amountConcepto.clear()
        self.progressBar.setValue(0)

        QMessageBox.critical(None, "Alerta", "No se seleccionó ningún archivo")

    def update_button_states(self, index):
                # Resetea todos los botones a "Normal Off"
                self.filter_tab.setChecked(False)
                self.home_tab.setChecked(False)
                self.pushButton_2.setChecked(False)

                # Cambia el botón correspondiente a "Normal On"
                if index == 1:
                        self.filter_tab.setChecked(True)
                elif index == 0:
                        self.home_tab.setChecked(True)
                elif index == 2:
                        self.pushButton_2.setChecked(True)

    def show_stacked_widget_page(self, index):
            # Cambia al índice deseado y asegura que el stackedWidget esté visible
            self.stackedWidget.setCurrentIndex(index)
            self.stackedWidget.setVisible(True)
            # Actualiza el estado de los botones
            self.update_button_states(index)

    def toggle_page_filter(self):
            if self.stackedWidget.currentIndex() == 1 and self.stackedWidget.isVisible():
                    self.stackedWidget.setVisible(False)
            else:
                    self.show_stacked_widget_page(1)

    def toggle_page_export(self):
            if self.stackedWidget.currentIndex() == 2 and self.stackedWidget.isVisible():
                    self.stackedWidget.setVisible(False)
            else:
                    self.show_stacked_widget_page(2)

    def toggle_page_home(self):
                if self.stackedWidget.currentIndex() == 0 and self.stackedWidget.isVisible():
                        self.stackedWidget.setVisible(False)
                else:
                        self.show_stacked_widget_page(0)


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)

    # Instancia directamente Ui_MainWindow
    main_window = Ui_MainWindow()
    main_window.setupUi(main_window)
    main_window.show()

    if getattr(sys, 'frozen', False):
        pyi_splash.close()

    sys.exit(app.exec())

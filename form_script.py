from PyQt6.QtCore import QThread, pyqtSignal, QObject, Qt, QSortFilterProxyModel, QRunnable, QThreadPool
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtGui import QStandardItem, QStandardItemModel, QIcon

from PyQt6.QtWidgets import QMessageBox, QStyleFactory,  QProgressDialog
import iconsLogin
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import requests
import re
import pandas as pd
import json, html


def obtener_obras_y_residentes_con_beautifulsoup(username, password, thread):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    service = ChromeService(executable_path=ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    obras = []
    residentes = []
    cookies = {}

    try:
        # Paso 1: Ingresar a la web
        driver.get("https://palmaterraproveedores.centralinformatica.com/")
        thread.progress_signal.emit(1, "Ingresando a la web...")

        # Paso 2: Ingresando usuario y contraseña
        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Usuario..']")))
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Contraseña..']")))
        username_input = driver.find_element(By.XPATH, "//input[@placeholder='Usuario..']")
        password_input = driver.find_element(By.XPATH, "//input[@placeholder='Contraseña..']")
        username_input.send_keys(username)
        password_input.send_keys(password)

        login_button = driver.find_element(By.ID, "Button1")
        login_button.click()
        thread.progress_signal.emit(2, "Verificando credenciales...")

        # Verificar si el inicio de sesión fue exitoso
        try:
            WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "liConsulta")))
        except Exception:
            # Si no aparece el elemento esperado, asumir que las credenciales son incorrectas
            thread.error_signal.emit("Usuario o contraseña incorrectos. Verifique sus credenciales.")
            driver.quit()
            return obras, residentes, cookies

        # Paso 3: Entrando a la sección de consulta
        consulta_button = driver.find_element(By.ID, "liConsulta")
        consulta_button.click()
        thread.progress_signal.emit(3, "Entrando a la sección de consulta...")

        # Paso 4: Obteniendo residentes y obras
        WebDriverWait(driver, 5).until(lambda d: len(d.find_elements(By.CSS_SELECTOR, "#txtObras option")) > 1)
        WebDriverWait(driver, 5).until(lambda d: len(d.find_elements(By.CSS_SELECTOR, "#txtResidente option")) > 1)
        page_html = driver.page_source
        soup = BeautifulSoup(page_html, "html.parser")

        obras_select = soup.find("select", {"id": "txtObras"})
        if obras_select:
            obras = [{"value": option.get("value", "").strip(), "name": option.text.strip()} for option in
                     obras_select.find_all("option") if option.get("value", "").strip()]

        residentes_select = soup.find("select", {"id": "txtResidente"})
        if residentes_select:
            residentes = [{"value": option.get("value", "").strip(), "name": option.text.strip()} for option in
                          residentes_select.find_all("option") if option.get("value", "").strip()]

        # Emitir progreso al completar
        thread.progress_signal.emit(4, "Obteniendo residentes y obras...")

        cookies = {cookie['name']: cookie['value'] for cookie in driver.get_cookies()}

    except Exception as e:
        thread.error_signal.emit(f"Ocurrió un error: {str(e)}")
    finally:
        driver.quit()

    return obras, residentes, cookies

class CargarObrasYResidentesThread(QThread):
    # Señales para enviar el progreso, el resultado y los errores
    progress_signal = pyqtSignal(int, str)
    result_signal = pyqtSignal(list, list, dict)
    error_signal = pyqtSignal(str)

    def __init__(self, username, password, parent=None):
        super().__init__(parent)
        self.username = username
        self.password = password

    def run(self):
        try:
            # Paso 1: Ingresando a la web
            self.progress_signal.emit(1, "Ingresando a la web")
            obras, residentes, cookies = obtener_obras_y_residentes_con_beautifulsoup(self.username, self.password, self)

            # Emitir el resultado final al terminar
            self.result_signal.emit(obras, residentes, cookies)
        except Exception as e:
            self.error_signal.emit(str(e))


class ProgresoInfinito(QProgressDialog):
    def __init__(self, mensaje="Realizando la consulta, por favor espere...", parent=None):
        super().__init__(parent)

        self.setWindowTitle("Cargando...")
        self.setLabelText(mensaje)
        self.setCancelButton(None)  # Opcional: deshabilita el botón de cancelar
        self.setMinimumDuration(0)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setRange(0, 0)  # Rango "infinito"
        self.cancelado = False  # Variable para verificar si fue cancelado

    def on_cancel(self):
        """
        Manejar la cancelación del proceso.
        """
        self.cancelado = True
        QMessageBox.warning(self, "Advertencia", "El proceso fue cancelado por el usuario.")
        self.close()

    def closeEvent(self, event):
        """
        Manejar el cierre del diálogo. No lo interpretamos como una cancelación.
        """
        if not self.cancelado:
            event.accept()  # Permitir el cierre sin mostrar advertencias

class WorkerSignals(QObject):
    finished = pyqtSignal(str, object)  # Emite un string y un objeto (en este caso, el DataFrame)
    error = pyqtSignal(str)  # Emite errores como string


class WorkerConsulta(QRunnable):
    def __init__(self, funcion_consulta, *args, **kwargs):
        super().__init__()
        self.funcion_consulta = funcion_consulta
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    def run(self):
        """
        Ejecuta la función de consulta en un hilo separado.
        """
        try:
            formatted_name, df = self.funcion_consulta(*self.args, **self.kwargs)  # Ejecutar la función
            self.signals.finished.emit(formatted_name, df)  # Emitir ambos valores al hilo principal
        except Exception as e:
            self.signals.error.emit(str(e))  # Emitir señal de error


class Ui_Form(QObject):  # Heredar de QObject
    # Definimos la señal para emitir `formatted_name` y `soup`
    consulta_exitosa = pyqtSignal(str, object)

    def __init__(self):
        super().__init__()  # Llamar al constructor de QObject
        self.thread_pool = QThreadPool()  # Crear un pool de hilos


    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(500, 550)
        Form.setWindowIcon(QIcon("C:\\Users\\noear\\Downloads\\Facturas_Octubre\\Octubre 2024\\favicon.ico"))  # Reemplaza con la ruta de tu ícono

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Form.sizePolicy().hasHeightForWidth())
        Form.setSizePolicy(sizePolicy)
        Form.setMinimumSize(QtCore.QSize(500, 550))
        Form.setMaximumSize(QtCore.QSize(500, 550))
        Form.setStyleSheet("background-color: rgb(82, 88, 96);")
        self.centralwidget = QtWidgets.QWidget(parent=Form)
        self.centralwidget.setObjectName("centralwidget")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout(self.centralwidget)
        self.horizontalLayout_3.setSpacing(7)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.frame_2 = QtWidgets.QFrame(parent=self.centralwidget)
        self.frame_2.setStyleSheet("/* Estilo para el frame que contiene los botones a la izquierda (frame_2) */\n"
"QFrame {\n"
"    background-color: #727b86; /* Color de fondo oscuro */\n"
"    border-radius: 10px; /* Bordes redondeados */\n"
"    padding: 2px; /* Espaciado interno */\n"
"}\n"
"\n"
"/* Estilo para los botones dentro de frame_2 */\n"
"QPushButton {\n"
"    background-color: #3C3F45; /* Fondo oscuro */\n"
"    color: #FFFFFF; /* Color del texto */\n"
"    border: none; /* Sin borde para simplicidad */\n"
"    border-radius: 8px; /* Bordes redondeados */\n"
"    padding: 10px; /* Espaciado interno */\n"
"    margin-bottom: 5px; /* Espacio entre botones */\n"
"    font-size: 14px; /* Tamaño de la fuente */\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: #5C5F65; /* Color de fondo al pasar el ratón */\n"
"}\n"
"\n"
"QPushButton:pressed {\n"
"    background-color: #2F3238; /* Fondo más oscuro al presionar */\n"
"}\n"
"\n"
"QPushButton:checked {\n"
"    background-color: #FFFFFF; /* Fondo blanco cuando está seleccionado */\n"
"    color: #333333; /* Texto oscuro para visibilidad sobre fondo blanco */\n"
"}\n"
"\n"
"/* Estilo para el botón deshabilitado */\n"
"QPushButton:disabled {\n"
"    background-color: #A0A4A8; /* Fondo gris claro para botón deshabilitado */\n"
"    color: #D1D3D4; /* Texto en gris claro para apariencia desactivada */\n"
"    border: none; /* Sin borde */\n"
"    border-radius: 8px; /* Mantiene los bordes redondeados */\n"
"}\n"
"")
        self.frame_2.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.frame_2.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.frame_2.setObjectName("frame_2")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.frame_2)
        self.verticalLayout_3.setContentsMargins(6, 6, 6, -1)
        self.verticalLayout_3.setSpacing(7)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.pushButton_2 = QtWidgets.QPushButton(parent=self.frame_2)
        self.pushButton_2.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.pushButton_2.setStyleSheet("")
        self.pushButton_2.setText("")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/images/whiteLogin.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        icon.addPixmap(QtGui.QPixmap(":/images/blackLogin.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.On)
        self.pushButton_2.setIcon(icon)
        self.pushButton_2.setIconSize(QtCore.QSize(40, 40))
        self.pushButton_2.setCheckable(True)
        self.pushButton_2.setObjectName("pushButton_2")
        self.verticalLayout_2.addWidget(self.pushButton_2)
        self.pushButton_3 = QtWidgets.QPushButton(parent=self.frame_2)
        self.pushButton_3.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.pushButton_3.setStyleSheet("")
        self.pushButton_3.setText("")
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/images/wwhitefind_11916806.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        icon1.addPixmap(QtGui.QPixmap(":/images/blacktefind_11916806.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.On)
        self.pushButton_3.setIcon(icon1)
        self.pushButton_3.setIconSize(QtCore.QSize(40, 40))
        self.pushButton_3.setCheckable(True)
        self.pushButton_3.setObjectName("pushButton_3")
        self.verticalLayout_2.addWidget(self.pushButton_3)
        self.verticalLayout_3.addLayout(self.verticalLayout_2)
        spacerItem = QtWidgets.QSpacerItem(20, 483, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        self.verticalLayout_3.addItem(spacerItem)
        self.horizontalLayout_3.addWidget(self.frame_2)
        self.stackedWidget = QtWidgets.QStackedWidget(parent=self.centralwidget)
        self.stackedWidget.setStyleSheet("QWidget {\n"
"    border-radius: 12px; /* Bordes redondeados suaves */\n"
"}\n"
"")
        self.stackedWidget.setObjectName("stackedWidget")
        self.page = QtWidgets.QWidget()
        self.page.setStyleSheet("background-color: rgb(82, 88, 96);")
        self.page.setObjectName("page")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout(self.page)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.frame = QtWidgets.QFrame(parent=self.page)
        self.frame.setStyleSheet("/* Estilo para QLineEdit */\n"
"QLineEdit {\n"
"    background-color: #3C3F45; /* Fondo del campo de texto */\n"
"    border: 1px solid #7A7D82; /* Borde del campo de texto */\n"
"    border-radius: 5px; /* Bordes redondeados */\n"
"    padding: 5px; /* Espaciado interno */\n"
"    color: #FFFFFF; /* Color del texto */\n"
"}\n"
"\n"
"QLineEdit:focus {\n"
"    border: 1px solid #FFFFFF; /* Borde al enfocar */\n"
"}\n"
"\n"
"QLineEdit:disabled {\n"
"    background-color: #FFFFFF; /* Fondo cuando está deshabilitado */\n"
"    color: #B0B0B0; /* Color del texto cuando está deshabilitado */\n"
"    border: 1px solid #7A7D82; /* Borde cuando está deshabilitado */\n"
"}")
        self.frame.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.frame.setObjectName("frame")
        self.verticalLayout_5 = QtWidgets.QVBoxLayout(self.frame)
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)
        self.imgPT = QtWidgets.QLabel(parent=self.frame)
        self.imgPT.setMinimumSize(QtCore.QSize(350, 100))
        self.imgPT.setMaximumSize(QtCore.QSize(16777215, 100))
        self.imgPT.setStyleSheet("border-image: url(:/images/logo-white.png);")
        self.imgPT.setText("")
        self.imgPT.setObjectName("imgPT")
        self.horizontalLayout.addWidget(self.imgPT)
        spacerItem2 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.horizontalLayout.addItem(spacerItem2)
        self.verticalLayout_5.addLayout(self.horizontalLayout)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        spacerItem3 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem3)
        self.label_portal = QtWidgets.QLabel(parent=self.frame)
        font = QtGui.QFont()
        font.setFamily("Lato Black")
        font.setPointSize(18)
        font.setBold(True)
        font.setWeight(75)
        self.label_portal.setFont(font)
        self.label_portal.setStyleSheet("QLabel {\n"
"    color: #FFFFFF; /* Color del texto */\n"
"}\n"
"")
        self.label_portal.setObjectName("label_portal")
        self.horizontalLayout_2.addWidget(self.label_portal)
        spacerItem4 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem4)
        self.verticalLayout_5.addLayout(self.horizontalLayout_2)
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.label_user = QtWidgets.QLabel(parent=self.frame)
        self.label_user.setStyleSheet("QLabel {\n"
"    color: #FFFFFF; /* Color del texto */\n"
"    font-size: 16px; /* Tamaño de fuente */\n"
"    font-weight: bold; /* Negrita */\n"
"}\n"
"")
        self.label_user.setObjectName("label_user")
        self.verticalLayout.addWidget(self.label_user)
        self.lineEdit = QtWidgets.QLineEdit(parent=self.frame)
        self.lineEdit.setObjectName("lineEdit")
        self.verticalLayout.addWidget(self.lineEdit)
        self.label_passw = QtWidgets.QLabel(parent=self.frame)
        self.label_passw.setStyleSheet("QLabel {\n"
"    color: #FFFFFF; /* Color del texto */\n"
"    font-size: 16px; /* Tamaño de fuente */\n"
"    font-weight: bold; /* Negrita */\n"
"}\n"
"")
        self.label_passw.setObjectName("label_passw")
        self.verticalLayout.addWidget(self.label_passw)
        self.lineEdit_2 = QtWidgets.QLineEdit(parent=self.frame)
        self.lineEdit_2.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        self.lineEdit_2.setObjectName("lineEdit_2")
        self.verticalLayout.addWidget(self.lineEdit_2)
        self.verticalLayout_5.addLayout(self.verticalLayout)
        spacerItem5 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Fixed)
        self.verticalLayout_5.addItem(spacerItem5)
        self.pushButton = QtWidgets.QPushButton(parent=self.frame)
        self.pushButton.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.pushButton.setStyleSheet("/* Estilo para el QPushButton \"ENTRAR\" con fondo claro y efecto moderno */\n"
"QPushButton {\n"
"    background-color: #FFFFFF; /* Fondo claro */\n"
"    color: #333333; /* Texto oscuro */\n"
"    font-size: 16px; /* Tamaño de fuente */\n"
"    font-weight: bold; /* Negrita para el texto */\n"
"    border: 2px solid #CCCCCC; /* Borde sutil */\n"
"    border-radius: 10px; /* Bordes redondeados */\n"
"    padding: 10px 20px; /* Espaciado interno */\n"
"}\n"
"\n"
"/* Efecto hover */\n"
"QPushButton:hover {\n"
"    background-color: #F0F0F0; /* Fondo ligeramente más oscuro al pasar el ratón */\n"
"}\n"
"\n"
"/* Efecto al presionar */\n"
"QPushButton:pressed {\n"
"    background-color: #E0E0E0; /* Fondo más oscuro al hacer clic */\n"
"}\n"
"")
        self.pushButton.setCheckable(True)
        self.pushButton.setObjectName("pushButton")
        self.verticalLayout_5.addWidget(self.pushButton)
        self.verticalLayout_4.addWidget(self.frame)
        self.stackedWidget.addWidget(self.page)
        self.page_2 = QtWidgets.QWidget()
        self.page_2.setStyleSheet("background-color: rgb(243, 243, 243);")
        self.page_2.setObjectName("page_2")
        self.verticalLayout_6 = QtWidgets.QVBoxLayout(self.page_2)
        self.verticalLayout_6.setObjectName("verticalLayout_6")
        self.frame_3 = QtWidgets.QFrame(parent=self.page_2)
        self.frame_3.setStyleSheet("/* Estilo para el frame_3 */\n"
"QFrame {\n"
"    background-color: #F7F7F8; /* Fondo ligeramente claro */\n"
"    border-radius: 12px; /* Bordes redondeados suaves */\n"
"    padding: 20px; /* Espaciado interno */\n"
"    border: 1px solid #E0E0E0; /* Borde suave */\n"
"}\n"
"\n"
"/* Estilo para QLabel dentro de frame_3 */\n"
"QLabel {\n"
"    color: #444444; /* Color de texto gris oscuro para elegancia */\n"
"    font-size: 14px; /* Tamaño de fuente */\n"
"    font-weight: 500; /* Peso medio para una apariencia más moderna */\n"
"    margin-bottom: 5px; /* Espacio inferior */\n"
"}\n"
"\n"
"/* Estilo para QLineEdit dentro de frame_3 */\n"
"QLineEdit {\n"
"    background-color: #FFFFFF; /* Fondo blanco */\n"
"    color: #333333; /* Color del texto */\n"
"    border: 1px solid #CCCCCC; /* Borde gris claro */\n"
"    border-radius: 8px; /* Bordes redondeados */\n"
"    padding: 8px; /* Espaciado interno */\n"
"    margin-bottom: 15px; /* Espacio inferior entre campos */\n"
"}\n"
"\n"
"QLineEdit:focus {\n"
"    border: 1px solid #7B9ACC; /* Borde azul sutil al enfocar */\n"
"}\n"
"\n"
"/* Estilo para QComboBox dentro de frame_3 */\n"
"QComboBox {\n"
"    background-color: #FFFFFF; /* Fondo blanco */\n"
"    color: #333333; /* Color del texto */\n"
"    border: 1px solid #CCCCCC; /* Borde gris claro */\n"
"    border-radius: 8px; /* Bordes redondeados */\n"
"    padding: 8px; /* Espaciado interno */\n"
"    font-size: 14px; /* Tamaño de fuente */\n"
"    margin-bottom: 15px; /* Espacio inferior entre campos */\n"
"}\n"
"\n"
"QComboBox:focus {\n"
"    border: 1px solid #7B9ACC; /* Borde azul sutil al enfocar */\n"
"}\n"
"\n"
"QComboBox::drop-down {\n"
"    border-left: 1px solid #CCCCCC; /* Borde del lado izquierdo */\n"
"    width: 30px; /* Ancho del botón desplegable */\n"
"    background-color: #E8E8E8; /* Fondo gris claro del botón desplegable */\n"
"    border-top-right-radius: 8px; /* Bordes redondeados */\n"
"    border-bottom-right-radius: 8px;\n"
"}\n"
"\n"
"QComboBox::down-arrow {\n"
"    image: url(down_arrow_icon.png); /* Cambia esto a la ruta de tu icono para la flecha */\n"
"    width: 10px;\n"
"    height: 10px;\n"
"}\n"
"\n"
"/* Estilo para el botón de \"BUSCAR\" */\n"
"QPushButton {\n"
"    background-color: #4A6FA5; /* Azul oscuro elegante */\n"
"    color: #FFFFFF; /* Texto en blanco */\n"
"    font-size: 15px; /* Tamaño de la fuente */\n"
"    font-weight: bold; /* Negrita */\n"
"    border: none; /* Sin borde */\n"
"    border-radius: 10px; /* Bordes redondeados */\n"
"    padding: 10px 20px; /* Espaciado interno */\n"
"    margin-top: 20px; /* Espacio superior */\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: #3B5A85; /* Fondo más oscuro al pasar el ratón */\n"
"}\n"
"\n"
"QPushButton:pressed {\n"
"    background-color: #2D4565; /* Fondo aún más oscuro al presionar */\n"
"}\n"
"")
        self.frame_3.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.frame_3.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.frame_3.setObjectName("frame_3")
        self.verticalLayout_7 = QtWidgets.QVBoxLayout(self.frame_3)
        self.verticalLayout_7.setObjectName("verticalLayout_7")
        self.label_residente = QtWidgets.QLabel(parent=self.frame_3)
        self.label_residente.setObjectName("label_residente")
        self.verticalLayout_7.addWidget(self.label_residente)
        self.comboBox_obras = QtWidgets.QComboBox(parent=self.frame_3)
        self.comboBox_obras.setObjectName("comboBox_obras")
        self.comboBox_obras.setEditable(True)
        self.comboBox_obras.setStyle(QStyleFactory.create("WindowsVista"))

        self.comboBox_obras.setStyleSheet("QComboBox {\n"
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
        # self.comboBox_obras.lineEdit().textChanged.connect(self.filtrar_obras)
        self.verticalLayout_7.addWidget(self.comboBox_obras)

        # Crear un modelo base para las obras
        self.model_obras = QStandardItemModel(self.comboBox_obras)

        # Crear el proxy para filtrar dinámicamente
        self.proxy_model_obras = QSortFilterProxyModel(self.comboBox_obras)
        self.proxy_model_obras.setSourceModel(self.model_obras)
        self.proxy_model_obras.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)

        # Configurar el comboBox para usar el proxy
        self.comboBox_obras.setModel(self.proxy_model_obras)

        # Conectar la edición del comboBox con el proxy para filtrar
        self.comboBox_obras.lineEdit().textChanged.connect(self.filtrar_obras)
        self.block_text_signal = False  # Indicador para bloquear señales

        self.label_2 = QtWidgets.QLabel(parent=self.frame_3)
        self.label_2.setObjectName("label_2")
        self.verticalLayout_7.addWidget(self.label_2)
        self.comboBox_residentes = QtWidgets.QComboBox(parent=self.frame_3)
        self.comboBox_residentes.setObjectName("comboBox_residentes")
        self.comboBox_residentes.setEditable(True)
        self.comboBox_residentes.setStyle(QStyleFactory.create("WindowsVista"))

        self.comboBox_residentes.setStyleSheet("QComboBox {\n"
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

        self.model_rdte = QStandardItemModel(self.comboBox_residentes)
        # Crear el proxy para filtrar dinámicamente
        self.proxy_model_rdte = QSortFilterProxyModel(self.comboBox_residentes)
        self.proxy_model_rdte.setSourceModel(self.model_rdte)
        self.proxy_model_rdte.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        # Configurar el comboBox para usar el proxy
        self.comboBox_residentes.setModel(self.proxy_model_rdte)
        # Conectar la edición del comboBox con el proxy para filtrar
        self.comboBox_residentes.lineEdit().textChanged.connect(self.filtrar_Rdte)
        self.block_text_signal2 = False  # Indicador para bloquear señales

        self.verticalLayout_7.addWidget(self.comboBox_residentes)
        self.label = QtWidgets.QLabel(parent=self.frame_3)
        self.label.setObjectName("label")
        self.verticalLayout_7.addWidget(self.label)
        self.lineEdit_3 = QtWidgets.QLineEdit(parent=self.frame_3)
        self.lineEdit_3.setObjectName("lineEdit_3")
        self.verticalLayout_7.addWidget(self.lineEdit_3)
        self.pushButton_4 = QtWidgets.QPushButton(parent=self.frame_3)
        self.pushButton_4.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.pushButton_4.setObjectName("pushButton_4")
        self.verticalLayout_7.addWidget(self.pushButton_4)
        self.verticalLayout_6.addWidget(self.frame_3)
        self.stackedWidget.addWidget(self.page_2)
        self.horizontalLayout_3.addWidget(self.stackedWidget)
        Form.setLayout(self.horizontalLayout_3)

        # Conectar los botones para cambiar de página en el stackedWidget
        self.pushButton_2.clicked.connect(self.mostrar_pagina_0)
        self.pushButton_3.clicked.connect(self.mostrar_pagina_1)
        self.pushButton_2.setChecked(True)
        self.pushButton_3.setDisabled(True)
        self.pushButton.clicked.connect(self.cargar_obras_y_residentes_en_comboBox)
        self.pushButton_4.clicked.connect(self.iniciar_consulta_facturas)  # Conectar el botón

        self.retranslateUi(Form)
        self.stackedWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Acceso portal"))
        self.label_portal.setText(_translate("Form", "Portal de proveedores"))
        self.label_user.setText(_translate("Form", "Usuario:"))
        self.lineEdit.setPlaceholderText(_translate("Form", "Ingrese usuario..."))
        self.label_passw.setText(_translate("Form", "Contraseña:"))
        self.lineEdit_2.setPlaceholderText(_translate("Form", "Ingrese contraseña..."))
        self.pushButton.setText(_translate("Form", "ENTRAR"))
        self.label_residente.setText(_translate("Form", "Obras:"))
        self.label_2.setText(_translate("Form", "Residente:"))
        self.label.setText(_translate("Form", "Proveedor:"))
        self.lineEdit_3.setPlaceholderText(_translate("Form", "Ingrese proveedor (mínimo 3 letras)..."))
        self.pushButton_4.setText(_translate("Form", "BUSCAR"))

    # Función de Selenium para obtener las obras y residentes usando BeautifulSoup para el análisis del HTM

    def iniciar_consulta_facturas(self):
        """
        Inicia el proceso de consulta de facturas con un QProgressDialog infinito.
        """
        # Mostrar el QProgressDialog
        self.progreso_dialogo = ProgresoInfinito("Realizando la consulta, por favor espere...", None)
        self.progreso_dialogo.show()

        # Crear y ejecutar el trabajador
        trabajador = WorkerConsulta(self._realizar_consulta_facturas)
        trabajador.signals.finished.connect(self.manejar_resultado)  # Manejar el resultado al finalizar
        trabajador.signals.error.connect(self.mostrar_error)  # Manejar errores

        self.thread_pool.start(trabajador)  # Agregar el trabajador al ThreadPool

    def manejar_resultado(self, formatted_name, df):
        """
        Maneja el resultado del hilo secundario y lo usa en la GUI principal.
        """
        self.progreso_dialogo.close()  # Cerrar el diálogo de progreso
        self.consulta_exitosa.emit(formatted_name, df)
        # Aquí puedes procesar `formatted_name` y `df` en tu interfaz principal
        QMessageBox.information(None, "Consulta Exitosa", "La consulta se realizó correctamente.")

    def mostrar_error(self, mensaje):
        """
        Muestra un mensaje de error en el hilo principal.
        """
        self.progreso_dialogo.close()  # Cerrar el diálogo de progreso si está abierto
        QMessageBox.critical(None, "Error", f"Ocurrió un error durante la consulta:\n{mensaje}")

    def _realizar_consulta_facturas(self):
        try:
            # Obtener los valores seleccionados en los ComboBox
            proveedor_seleccionado = self.lineEdit_3.text()
            obra_seleccionada = self.comboBox_obras.currentText()
            residente_seleccionado = self.comboBox_residentes.currentText()

            # Validar selección de obra
            if not obra_seleccionada:
                raise ValueError("Debe seleccionar una obra para realizar la consulta.")

            # Obtener el valor correspondiente a la obra seleccionada
            obra_value = next((obra["value"] for obra in self.obras_data if obra["name"] == obra_seleccionada), "")
            if obra_seleccionada == "TODAS":
                obra_value = ""  # Si se selecciona "TODAS", el valor es una cadena vacía

            # Obtener el valor correspondiente al residente seleccionado
            residente_value = next(
                (residente["value"] for residente in self.residentes_data if
                 residente["name"] == residente_seleccionado),
                "")
            if residente_seleccionado == "TODOS":
                residente_value = ""  # Si se selecciona "TODOS", el valor es una cadena vacía

            # Construir los datos de la solicitud
            data = {
                "Estatus": "",
                "Residente": residente_value,
                "Obra": obra_value,
                "Proveedor": f"{proveedor_seleccionado}",
                "Fecha": "",
                "FechaDesde": "",
                "FechaHasta": "",
                "Numero": ""
            }

            headers = {
                "Content-Type": "application/json; charset=utf-8"
            }

            # Realizar la solicitud POST
            response = requests.post(
                "https://palmaterraproveedores.centralinformatica.com/WSUnico.asmx/GetAllFacturasBusqueda",
                json=data,
                headers=headers,
                cookies=self.cookies
            )
            clean_html = ""

            if response.status_code == 200:
                response_data = json.loads(response.content.decode("utf-8"))
                nested_json = response_data.get("d", "")

                if not nested_json:
                    raise ValueError("No se encontraron datos en la respuesta.")

                nested_data = json.loads(nested_json)

                if "tbodyFacturas" not in nested_data:
                    raise ValueError("No se encontraron facturas en la respuesta.")

                extracted_html = nested_data.get("tbodyFacturas", "")

                if not extracted_html:
                    raise ValueError("No hay contenido de facturas para procesar.")

                clean_html = html.unescape(extracted_html)

                if clean_html:
                    def limpiar_texto(texto):
                        texto = re.sub(r'\s{2,}', ' ', texto)
                        texto = texto.replace('_lnfd_', '\n').strip()
                        return texto if texto else '-'

                    def procesar_enlace(onclick, clase):
                        clase_valida = clase.strip() in ["btn btn-primary btn-sm", "btn btn-info btn-sm"]
                        if not clase_valida:
                            return None

                        onclick = onclick.replace('\\&quot;', '"').replace('\\"', '"').strip()

                        if "openXML" in onclick:
                            match = re.search(r"openXML\('([^']+)','([^']*)'\)", onclick)
                            if match:
                                rfc = match.group(1)
                                fname = match.group(2)
                                if fname:
                                    return f"https://palmaterraproveedores.centralinformatica.com/Download.ashx?id={fname}&rfc={rfc}&contrarecibo=0"

                        elif "openContrareciboRdte" in onclick:
                            match = re.search(r"openContrareciboRdte\('([^']+)','([^']*)'\)", onclick)
                            if match:
                                rfc = match.group(1)
                                fname = match.group(2)
                                if fname:
                                    return f"https://palmaterraproveedores.centralinformatica.com/Download.ashx?id={fname}&rfc={rfc}&contrarecibo=1"

                        return None

                    def procesar_fecha(onclick):
                        match = re.search(
                            r"OpenmodalFechas\('([^']+)','([^']+)','([^']+)','([^']+)','([^']+)','([^']+)'\)", onclick)
                        if match:
                            fechas = {
                                "Fecha Factura": limpiar_texto(match.group(1)),
                                "Fecha Recepción": limpiar_texto(match.group(2)),
                                "Fecha Contrarecibo": limpiar_texto(match.group(3)),
                                "Fecha Autorización": limpiar_texto(match.group(4)),
                                "Fecha Pagada": limpiar_texto(match.group(5)),
                                "Fecha Alta": limpiar_texto(match.group(6)),
                            }
                            return fechas
                        return {}

                    def procesar_comentarios(onclick):
                        match = re.search(r"show_modalPopUpFacturaObs\('([^']*)','([^']*)'\)", onclick)
                        if match:
                            comentarios = limpiar_texto(match.group(1))
                            observaciones = limpiar_texto(match.group(2))
                            return {"Comentarios de proveedor": comentarios,
                                    "Observaciones de Facturación": observaciones}
                        return {"Comentarios de proveedor": "-", "Observaciones de Facturación": "-"}

                    def procesar_html_content(html_content):
                        soup = BeautifulSoup(html_content, 'html.parser')
                        data = []

                        rows = soup.find_all("tr")
                        for row in rows:
                            cells = row.find_all("td")
                            if len(cells) > 0:
                                obra = limpiar_texto(cells[0].get_text(strip=True)) if len(cells) > 0 else "-"
                                proveedor = limpiar_texto(cells[1].get_text(strip=True)) if len(cells) > 1 else "-"
                                encargado = limpiar_texto(cells[2].get_text(strip=True)) if len(cells) > 2 else "-"
                                numero = limpiar_texto(cells[3].get_text(strip=True)) if len(cells) > 3 else "-"
                                estatus = limpiar_texto(cells[4].get_text(strip=True)) if len(cells) > 4 else "-"
                                monto = limpiar_texto(cells[5].get_text(strip=True)) if len(cells) > 5 else "-"
                                fecha = limpiar_texto(cells[6].get_text(strip=True)) if len(cells) > 6 else "-"

                                xml_link = pdf_link = cr_link = oc_link = rem_link = None
                                fechas = comentarios = {}

                                for enlace in row.find_all("a"):
                                    onclick = enlace.get("onclick", "")
                                    clase = " ".join(enlace.get("class", []))

                                    if "OpenmodalFechas" in onclick:
                                        fechas = procesar_fecha(onclick)
                                    elif "show_modalPopUpFacturaObs" in onclick:
                                        comentarios = procesar_comentarios(onclick)
                                    elif "XML" in enlace.text.strip().upper() and not xml_link:
                                        xml_link = procesar_enlace(onclick, clase)
                                    elif "PDF" in enlace.text.strip().upper() and not pdf_link:
                                        pdf_link = procesar_enlace(onclick, clase)
                                    elif "CR" in enlace.text.strip().upper() and not cr_link:
                                        cr_link = procesar_enlace(onclick, clase)
                                    elif "OC" in enlace.text.strip().upper() and not oc_link:
                                        oc_link = procesar_enlace(onclick, clase)
                                    elif "REM" in enlace.text.strip().upper() and not rem_link:
                                        rem_link = procesar_enlace(onclick, clase)

                                data.append({
                                    "Obra": obra,
                                    "Proveedor": proveedor,
                                    "Residente": encargado,
                                    "Número": numero,
                                    "Estatus": estatus,
                                    "Monto": monto,
                                    "Fecha": fecha,
                                    "XML": xml_link,
                                    "PDF": pdf_link,
                                    "C.REC": cr_link,
                                    "OC": oc_link,
                                    "REM": rem_link,
                                    **fechas,
                                    **comentarios,
                                })


                        return pd.DataFrame(data)

                    df = procesar_html_content(clean_html)
                    formatted_name = f"Proveedor: '{proveedor_seleccionado}'\nObras: {obra_seleccionada}\nResidente: {residente_seleccionado}"

                    # self.consulta_exitosa.emit(formatted_name, df)

                else:
                    raise ValueError("No se encontraron facturas o ocurrió un error.")
            else:
                raise ValueError(f"Error en la consulta: {response.status_code}")

            return formatted_name, df
        except Exception as e:
            raise RuntimeError(f"Ocurrió un error al realizar la consulta: {e}")

    def mostrar_error(self, mensaje):
        """
        Muestra un mensaje de error en la GUI.
        """
        QMessageBox.critical(None, "Error", f"Ocurrió un error durante la consulta:\n{mensaje}")

    def filtrar_obras(self, texto):
        """
        Permite entrada libre en el comboBox y filtra las obras dinámicamente.
        """
        if self.block_text_signal:
            return  # No hacer nada si las señales están bloqueadas

        try:
            # Bloquear señales mientras se actualiza el filtro
            self.block_text_signal = True

            # Aplica el filtro al modelo
            self.proxy_model_obras.setFilterFixedString(texto)

            # Mantiene el texto ingresado intacto en el lineEdit
            self.comboBox_obras.lineEdit().setText(texto)
            self.comboBox_obras.lineEdit().setCursorPosition(len(texto))  # Mantener el cursor al final

        except Exception as e:
            QMessageBox.critical(None, "Error", f"Ocurrió un error al filtrar: {str(e)}")
        finally:
            # Liberar el bloqueo de señales
            self.block_text_signal = False

    def filtrar_Rdte(self, texto):
        """
        Permite entrada libre en el comboBox y filtra las obras dinámicamente.
        """
        if self.block_text_signal2:
            return  # No hacer nada si las señales están bloqueadas

        try:
            # Bloquear señales mientras se actualiza el filtro
            self.block_text_signal2 = True

            # Aplica el filtro al modelo
            self.proxy_model_rdte.setFilterFixedString(texto)

            # Mantiene el texto ingresado intacto en el lineEdit
            self.comboBox_residentes.lineEdit().setText(texto)
            self.comboBox_residentes.lineEdit().setCursorPosition(len(texto))  # Mantener el cursor al final

        except Exception as e:
            QMessageBox.critical(None, "Error", f"Ocurrió un error al filtrar: {str(e)}")
        finally:
            # Liberar el bloqueo de señales
            self.block_text_signal2 = False

    def consultar_facturas(self):
        # Obtener los valores seleccionados en los ComboBox
        proveedor_seleccionado = self.lineEdit_3.text()
        obra_seleccionada = self.comboBox_obras.currentText()
        residente_seleccionado = self.comboBox_residentes.currentText()


        # Validar selección de obra
        if not obra_seleccionada:
            QMessageBox.warning(None, "Advertencia", "Debe seleccionar una obra para realizar la consulta.")
            return

        # Obtener el valor correspondiente a la obra seleccionada
        obra_value = next((obra["value"] for obra in self.obras_data if obra["name"] == obra_seleccionada), "")
        if obra_seleccionada == "TODAS":
            obra_value = ""  # Si se selecciona "TODAS", el valor es una cadena vacía

        # Obtener el valor correspondiente al residente seleccionado
        residente_value = next(
            (residente["value"] for residente in self.residentes_data if residente["name"] == residente_seleccionado),
            "")
        if residente_seleccionado == "TODOS":
            residente_value = ""  # Si se selecciona "TODOS", el valor es una cadena vacía

        # Construir los datos de la solicitud
        data = {
            "Estatus": "",  # Ajustar según sea necesario
            "Residente": residente_value,
            "Obra": obra_value,
            "Proveedor": f"{proveedor_seleccionado}",  # Ajustar según sea necesario
            "Fecha": "",  # Ajustar según sea necesario
            "FechaDesde": "",  # Ajustar según sea necesario
            "FechaHasta": "",  # Ajustar según sea necesario
            "Numero": ""  # Ajustar según sea necesario
        }

        headers = {
            "Content-Type": "application/json; charset=utf-8"
        }

        # Realizar la solicitud POST
        try:
            response = requests.post(
                "https://palmaterraproveedores.centralinformatica.com/WSUnico.asmx/GetAllFacturasBusqueda",
                json=data,
                headers=headers,
                cookies=self.cookies
            )
            clean_html = ""  # Inicializa clean_html al inicio

            if response.status_code == 200:
                # Inspeccionar el contenido de la respuesta
                response_data = json.loads(response.content.decode("utf-8"))
                nested_json = response_data.get("d", "")

                # Verifica que nested_json no esté vacío
                if not nested_json:
                    QMessageBox.warning(None, "Advertencia", "No se encontraron datos en la respuesta.")
                    return

                nested_data = json.loads(nested_json)  # Deserializar la cadena JSON anidada

                # Verifica que nested_data contenga "tbodyFacturas"
                if "tbodyFacturas" not in nested_data:
                    QMessageBox.warning(None, "Advertencia", "No se encontraron facturas en la respuesta.")
                    return

                # Extraer el HTML dentro de "tbodyFacturas"
                extracted_html = nested_data.get("tbodyFacturas", "")

                # Verifica que extracted_html no esté vacío
                if not extracted_html:
                    QMessageBox.warning(None, "Advertencia", "No hay contenido de facturas para procesar.")
                    return

                # Desescapar caracteres especiales
                clean_html = html.unescape(extracted_html)


                if clean_html:
                    # Funciones previamente definidas
                    def limpiar_texto(texto):
                        texto = re.sub(r'\s{2,}', ' ', texto)
                        texto = texto.replace('_lnfd_', '\n').strip()
                        return texto if texto else '-'

                    def procesar_enlace(onclick, clase):
                        """
                        Procesa el atributo onclick y clase para extraer un enlace válido.
                        Solo retorna un enlace si la clase es válida y los parámetros en onclick son correctos.

                        Parámetros:
                            onclick (str): El atributo onclick del elemento <a>.
                            clase (str): El atributo class del elemento <a>.

                        Retorna:
                            str: La URL construida si es válida, de lo contrario, None.
                        """
                        # Validar si la clase es válida
                        clase_valida = clase.strip() in ["btn btn-primary btn-sm", "btn btn-info btn-sm"]
                        if not clase_valida:
                            return None  # Retorna None si la clase no es válida

                        # Limpiar y procesar el atributo onclick
                        onclick = onclick.replace('\\&quot;', '"').replace('\\"', '"').strip()

                        if "openXML" in onclick:
                            # Buscar los parámetros en el onclick
                            match = re.search(r"openXML\('([^']+)','([^']*)'\)", onclick)
                            if match:
                                rfc = match.group(1)
                                fname = match.group(2)
                                if fname:  # Verificar que fname no esté vacío
                                    return f"https://palmaterraproveedores.centralinformatica.com/Download.ashx?id={fname}&rfc={rfc}&contrarecibo=0"

                        elif "openContrareciboRdte" in onclick:
                            # Buscar los parámetros en el onclick
                            match = re.search(r"openContrareciboRdte\('([^']+)','([^']*)'\)", onclick)
                            if match:
                                rfc = match.group(1)
                                fname = match.group(2)
                                if fname:  # Verificar que fname no esté vacío
                                    return f"https://palmaterraproveedores.centralinformatica.com/Download.ashx?id={fname}&rfc={rfc}&contrarecibo=1"

                        return None  # Retorna None si no cumple con las condiciones

                    def procesar_fecha(onclick):
                        match = re.search(
                            r"OpenmodalFechas\('([^']+)','([^']+)','([^']+)','([^']+)','([^']+)','([^']+)'\)", onclick)
                        if match:
                            fechas = {
                                "Fecha Factura": limpiar_texto(match.group(1)),
                                "Fecha Recepción": limpiar_texto(match.group(2)),
                                "Fecha Contrarecibo": limpiar_texto(match.group(3)),
                                "Fecha Autorización": limpiar_texto(match.group(4)),
                                "Fecha Pagada": limpiar_texto(match.group(5)),
                                "Fecha Alta": limpiar_texto(match.group(6)),
                            }
                            return fechas
                        return {}

                    def procesar_comentarios(onclick):
                        match = re.search(r"show_modalPopUpFacturaObs\('([^']*)','([^']*)'\)", onclick)
                        if match:
                            comentarios = limpiar_texto(match.group(1))
                            observaciones = limpiar_texto(match.group(2))
                            return {"Comentarios de proveedor": comentarios, "Observaciones de Facturación": observaciones}
                        return {"Comentarios de proveedor": "-", "Observaciones de Facturación": "-"}

                    def procesar_html_content(html_content):
                        soup = BeautifulSoup(html_content, 'html.parser')
                        data = []

                        rows = soup.find_all("tr")
                        for row in rows:
                            cells = row.find_all("td")
                            if len(cells) > 0:
                                obra = limpiar_texto(cells[0].get_text(strip=True)) if len(cells) > 0 else "-"
                                proveedor = limpiar_texto(cells[1].get_text(strip=True)) if len(cells) > 1 else "-"
                                encargado = limpiar_texto(cells[2].get_text(strip=True)) if len(cells) > 2 else "-"
                                numero = limpiar_texto(cells[3].get_text(strip=True)) if len(cells) > 3 else "-"
                                estatus = limpiar_texto(cells[4].get_text(strip=True)) if len(cells) > 4 else "-"
                                monto = limpiar_texto(cells[5].get_text(strip=True)) if len(cells) > 5 else "-"
                                fecha = limpiar_texto(cells[6].get_text(strip=True)) if len(cells) > 6 else "-"

                                xml_link = None
                                pdf_link = None
                                cr_link = None
                                oc_link = None
                                rem_link = None
                                fechas = {}
                                comentarios = {}

                                for enlace in row.find_all("a"):
                                    onclick = enlace.get("onclick", "")
                                    clase = " ".join(
                                        enlace.get("class", []))  # Obtener el atributo "class" como una cadena

                                    if "OpenmodalFechas" in onclick:
                                        fechas = procesar_fecha(onclick)
                                    elif "show_modalPopUpFacturaObs" in onclick:
                                        comentarios = procesar_comentarios(onclick)
                                    elif "XML" in enlace.text.strip().upper() and not xml_link:
                                        xml_link = procesar_enlace(onclick, clase)  # Pasar "onclick" y "class" a la nueva función
                                    elif "PDF" in enlace.text.strip().upper() and not pdf_link:
                                        pdf_link = procesar_enlace(onclick, clase)
                                    elif "CR" in enlace.text.strip().upper() and not cr_link:
                                        cr_link = procesar_enlace(onclick, clase)
                                    elif "OC" in enlace.text.strip().upper() and not oc_link:
                                        oc_link = procesar_enlace(onclick, clase)
                                    elif "REM" in enlace.text.strip().upper() and not rem_link:
                                        rem_link = procesar_enlace(onclick, clase)

                                data.append({
                                    "Obra": obra,
                                    "Proveedor": proveedor,
                                    "Residente": encargado,
                                    "Número": numero,
                                    "Estatus": estatus,
                                    "Monto": monto,
                                    "Fecha": fecha,
                                    "XML": xml_link,
                                    "PDF": pdf_link,
                                    "C.REC": cr_link,
                                    "OC": oc_link,
                                    "REM": rem_link,
                                    **fechas,
                                    **comentarios,
                                })

                        df = pd.DataFrame(data)
                        return df

                    df = procesar_html_content(clean_html)
                    formatted_name = f"Proveedor: '{self.lineEdit_3.text()}'\nObras: {self.comboBox_obras.currentText()}\nResidente: {self.comboBox_residentes.currentText()}"

                    # Emitimos la señal con `formatted_name` y `soup`
                    self.consulta_exitosa.emit(formatted_name, df)

                    QMessageBox.information(None, "Consulta Exitosa", "La consulta se realizó correctamente.")
                else:
                    QMessageBox.warning(None, "Advertencia", "No se encontraron facturas o ocurrió un error.")
            else:
                QMessageBox.warning(None, "Error en la Consulta",
                                    f"Error al realizar la consulta: {response.status_code}")
        except Exception as e:
            QMessageBox.critical(None, "Error", f"Ocurrió un error al realizar la consulta: {str(e)}, clean {clean_html}")

    def cargar_obras_y_residentes_en_comboBox(self):
        # Obtiene las credenciales directamente de los campos de entrada
        username = self.lineEdit.text()
        password = self.lineEdit_2.text()

        # Verificar si el usuario y contraseña fueron ingresados
        if not username:
            QMessageBox.warning(None, "Advertencia", "Debe ingresar un nombre de usuario.")
            return
        if not password:
            QMessageBox.warning(None, "Advertencia", "Debe ingresar una contraseña.")
            return

        # Configuración del QProgressDialog como barra indeterminada
        self.progress_dialog = QtWidgets.QProgressDialog("Cargando, por favor espere...", None, 0, 0, None)
        self.progress_dialog.setMinimumWidth(250)  # Cambia el valor según lo necesario
        self.progress_dialog.setWindowTitle("Progreso de la consulta")
        self.progress_dialog.setWindowModality(QtCore.Qt.WindowModality.ApplicationModal)
        self.progress_dialog.setMinimumDuration(0)  # Para que aparezca inmediatamente
        self.progress_dialog.setAutoClose(True)
        self.progress_dialog.show()

        # Crear e iniciar el hilo
        self.thread = CargarObrasYResidentesThread(username, password)

        # Conectar la señal de progreso para actualizar la leyenda del diálogo de progreso
        self.thread.progress_signal.connect(lambda _, text: self.progress_dialog.setLabelText(text))
        # Conectar la señal de resultado para manejar el fin del hilo
        self.thread.result_signal.connect(
            lambda obras, residentes, cookies: self.on_load_complete(obras, residentes, cookies))
        # Conectar la señal de error para mostrar errores
        self.thread.error_signal.connect(lambda error: QMessageBox.critical(None, "Error", error))

        # Iniciar el hilo
        self.thread.start()

    def on_load_complete(self, obras, residentes, cookies):
        try:
            # Cerrar el cuadro de progreso
            self.progress_dialog.close()

            # Limpiar modelos y comboBox
            self.model_obras.clear()
            self.comboBox_obras.lineEdit().clear()

            # Limpiar modelos y comboBox
            self.model_rdte.clear()
            self.comboBox_residentes.lineEdit().clear()

            if obras:
                self.obras_data = obras  # Guardar datos originales
                self.model_obras.appendRow(QStandardItem("TODAS"))  # Agregar opción "TODAS"

                # Añadir obras al modelo base
                for obra in obras:
                    item = QStandardItem(obra["name"])
                    item.setData(obra)  # Asociar datos adicionales si es necesario
                    self.model_obras.appendRow(item)
                    self.comboBox_obras.setCurrentText("")

            if residentes:
                self.residentes_data = residentes
                self.model_rdte.appendRow(QStandardItem("TODOS"))  # Agregar opción "TODAS"

                # Añadir obras al modelo base
                for residente in residentes:
                    item = QStandardItem(residente["name"])
                    item.setData(residente)  # Asociar datos adicionales si es necesario
                    self.model_rdte.appendRow(item)
                    self.comboBox_residentes.setCurrentText("")

            # Guarda las cookies para futuras consultas
            self.cookies = cookies
            # Habilitar interacción después de cargar los datos
            self.comboBox_obras.lineEdit().setEnabled(True)
            self.comboBox_residentes.lineEdit().setEnabled(True)
            QMessageBox.information(None, "Éxito", "Datos cargados correctamente.")
            self.pushButton_3.setDisabled(False)
            self.mostrar_pagina_1()

        except Exception as e:
            QMessageBox.critical(None, "Error", f"Ocurrió un error: {str(e)}")

    def mostrar_pagina_0(self):
        # Cambiar a la página 0 del stackedWidget
        self.stackedWidget.setCurrentIndex(0)
        # Configurar el estado de los botones
        self.pushButton_2.setChecked(True)
        self.pushButton_3.setChecked(False)

    def mostrar_pagina_1(self):
        # Cambiar a la página 1 del stackedWidget
        self.stackedWidget.setCurrentIndex(1)
        # Configurar el estado de los botones
        self.pushButton_2.setChecked(False)
        self.pushButton_3.setChecked(True)

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Form = QtWidgets.QMainWindow()
    ui = Ui_Form()
    ui.setupUi(Form)
    Form.show()
    sys.exit(app.exec())

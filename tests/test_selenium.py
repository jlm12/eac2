import time
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.contrib.auth.models import User
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

class AdminStaffTest(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        """
        Configuración inicial del test:
        - Inicia Firefox.
        - Crea un superusuario (isard/pirineus) para acceder al admin.
        """
        super().setUpClass()
        opts = FirefoxOptions()
        # Si quieres ejecutar en modo headless, descomenta la siguiente línea:
        # opts.add_argument("--headless")
        cls.selenium = webdriver.Firefox(options=opts)
        cls.selenium.implicitly_wait(10)

        # Crear superusuario
        User.objects.create_superuser(username="isard", email="admin@example.com", password="pirineus")

    @classmethod
    def tearDownClass(cls):
        """Cierra el navegador al finalizar los tests."""
        cls.selenium.quit()
        super().tearDownClass()

    def admin_login(self, username, password):
        """Inicia sesión en el panel de administración."""
        print(f"Intentando iniciar sesión como {username}...")
        self.selenium.get(f"{self.live_server_url}/admin/login/")
        wait = WebDriverWait(self.selenium, 15)
        try:
            username_input = wait.until(EC.presence_of_element_located((By.NAME, "username")))
            password_input = self.selenium.find_element(By.NAME, "password")
            username_input.send_keys(username)
            password_input.send_keys(password)
            login_button = self.selenium.find_element(By.XPATH, "//input[@value='Log in']")
            login_button.click()
            print(f"Inicio de sesión exitoso como {username}.")
        except TimeoutException:
            print(f"Fallo al iniciar sesión como {username}. No se encontró el campo de nombre de usuario.")
            print(self.selenium.page_source)  # Imprimir el HTML de la página actual para depuración
            raise

    def admin_logout(self):
        """Cierra sesión en el panel de administración mediante el botón 'Log out'."""
        print("Cerrando sesión mediante el botón 'Log out'...")
        wait = WebDriverWait(self.selenium, 15)
        try:
            # Ubicar el botón dentro del formulario logout y hacer clic en él
            logout_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "form#logout-form button[type='submit']")))
            logout_button.click()
            print("Sesión cerrada exitosamente.")
        except TimeoutException:
            print("No se pudo encontrar el botón de 'Log out'.")
            print(self.selenium.page_source)  # Para depuración
            raise

    def test_create_staff_and_change_password(self):
        """
        Flujo del test:
        1. Iniciar sesión como superusuario.
        2. Crear un usuario staff (staff/password1_st) con permisos mínimos de staff.
        3. Cerrar sesión del superusuario mediante el botón "Log out".
        4. Iniciar sesión como staff.
        5. Verificar acceso a /admin y cambiar la contraseña.
        """
        # 1. Iniciar sesión como superusuario
        self.admin_login("isard", "pirineus")

        # 2. Crear usuario staff
        print("Creando usuario 'staff' con permisos mínimos...")
        self.selenium.get(f"{self.live_server_url}/admin/auth/user/add/")
        wait = WebDriverWait(self.selenium, 15)

        # Completar el formulario para crear el usuario
        username_input = wait.until(EC.presence_of_element_located((By.ID, "id_username")))
        username_input.send_keys("staff")
        password1_input = self.selenium.find_element(By.ID, "id_password1")
        password2_input = self.selenium.find_element(By.ID, "id_password2")
        password1_input.send_keys("password1_st")
        password2_input.send_keys("password1_st")
        save_button = self.selenium.find_element(By.NAME, "_save")
        save_button.click()

        # Asignar únicamente el permiso de staff
        print("Asignando permisos mínimos de staff...")
        is_staff_checkbox = wait.until(EC.presence_of_element_located((By.ID, "id_is_staff")))
        if not is_staff_checkbox.is_selected():
            is_staff_checkbox.click()
        # Guardar los cambios
        self.selenium.find_element(By.NAME, "_save").click()

        # 3. Cerrar sesión como admin mediante "Log out"
        self.admin_logout()

        # 4. Iniciar sesión como staff
        self.admin_login("staff", "password1_st")

        # Verificar que el usuario staff puede acceder al panel de administración
        print("Verificando que el usuario 'staff' puede acceder a /admin...")
        WebDriverWait(self.selenium, 15).until(
            EC.presence_of_element_located((By.XPATH, "//a[text()='View site']"))
        )

        # 5. Cambiar contraseña de staff
        print("Cambiando contraseña del usuario 'staff'...")
        self.selenium.get(f"{self.live_server_url}/admin/password_change/")
        old_password_input = wait.until(EC.presence_of_element_located((By.NAME, "old_password")))
        new_password1_input = self.selenium.find_element(By.NAME, "new_password1")
        new_password2_input = self.selenium.find_element(By.NAME, "new_password2")
        old_password_input.send_keys("password1_st")
        new_password1_input.send_keys("NuevaContraseña456!")
        new_password2_input.send_keys("NuevaContraseña456!")
        save_button = self.selenium.find_element(By.XPATH, "//input[@type='submit' and @value='Change my password']")
        save_button.click()

        # Verificar cambio exitoso
        print("Verificando que la contraseña fue cambiada exitosamente...")
        success_message = wait.until(
            EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Your password was changed.')]"))
        )
        assert success_message is not None, "El mensaje de éxito no apareció después de cambiar la contraseña."
        print("El cambio de contraseña fue exitoso.")

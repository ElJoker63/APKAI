import flet as ft
import re
from groq import Groq
import requests
import json
import os
import socks
import socket
import logging

# Configura el sistema de logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class ChatApp:
    def __init__(self):
        self.client = None
        self.chat_history = [
            {
                "role": "system",
                "content": "You are a helpful assistant. You reply with very short answers.",
            }
        ]
        self.proxy_enabled = False  # Estado del proxy
        self.proxy_host = ""
        self.proxy_port = 0
        self.proxy_user = ""
        self.proxy_pass = ""
        self.available_models = ChatApp.get_models()
        self.current_model = "llama3-8b-8192"  

    def get_models():
        key = "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"
        req = Groq(api_key=key).models.list()
        models = {}
        for model in req.data:
            model_id = model.id
            model_name = model.owned_by
            models[model_id] = model_name
        return models   

    def apply_proxy(self):
        """Aplica la configuración del proxy si está habilitado."""
        if self.proxy_enabled and self.proxy_host and self.proxy_port:
            socks.set_default_proxy(
                socks.SOCKS5,
                self.proxy_host,
                self.proxy_port,
                username=self.proxy_user or None,
                password=self.proxy_pass or None,
            )
            socket.socket = socks.socksocket  # Reemplaza el socket global
            os.environ["HTTPS_PROXY"] = f"socks5://{self.proxy_host}:{self.proxy_port}"
            os.environ["HTTP_PROXY"] = f"socks5://{self.proxy_host}:{self.proxy_port}"
        else:
            # Elimina la configuración de proxy si está desactivado
            os.environ.pop("HTTPS_PROXY", None)
            os.environ.pop("HTTP_PROXY", None)

    def save_proxy_settings(self, page):
        """Guarda la configuración del proxy en client_storage y aplica los cambios."""
        self.proxy_enabled = self.proxy_switch.value
        self.proxy_host = self.proxy_host_field.value
        self.proxy_port = int(self.proxy_port_field.value)
        self.proxy_user = self.proxy_user_field.value
        self.proxy_pass = self.proxy_pass_field.value

        logging.info(f"Proxy settings saved: {self.proxy_enabled}, {self.proxy_host}, {self.proxy_port}")

        self.apply_proxy()  # Aplica la configuración
        self.proxy_dialog.open = False
        page.client_storage.set("proxy_enabled", self.proxy_enabled)
        page.client_storage.set("proxy_host", self.proxy_host)
        page.client_storage.set("proxy_port", self.proxy_port)
        page.client_storage.set("proxy_user", self.proxy_user)
        page.client_storage.set("proxy_pass", self.proxy_pass)
        page.update()   

    def process_message_with_code(self, message):
        # Split message into parts based on code blocks
        parts = re.split(r"(```[\s\S]*?```)", message)
        controls = []

        for part in parts:
            if part.startswith("```") and part.endswith("```"):
                # Extract code content and language
                code_content = part[3:-3].strip()
                # Check if language is specified
                if "\n" in code_content:
                    lang, *code_lines = code_content.split("\n")
                    code_content = "\n".join(code_lines)
                else:
                    lang = ""

                # Create code block container
                code_container = ft.Container(
                    content=ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Text(
                                        f"Code ({lang})" if lang else "Code",
                                        size=12,
                                        color=ft.Colors.GREY_400,
                                        font_family="mons",
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.COPY,
                                        icon_size=16,
                                        tooltip="Copiar código",
                                        on_click=lambda e, code=code_content: self.copy_to_clipboard(code, e),
                                    ),
                                ]
                            ,wrap=True),
                            ft.Container(
                                content=ft.Text(
                                    code_content,
                                    font_family="monospace",
                                    selectable=True,
                                ),
                                bgcolor=ft.Colors.BLACK,
                                padding=10,
                                border_radius=8,
                            ),
                        ]
                    ),
                    bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
                    border_radius=8,
                    padding=10,
                    margin=ft.margin.symmetric(vertical=5),
                )
                controls.append(code_container)
            else:
                if part.strip():
                    controls.append(
                        ft.Text(part.strip(), selectable=True, font_family="mons")
                    )

        return controls
    
    def copy_to_clipboard(self, text: str, e):
        # Usar el clipboard nativo de Flet
        e.page.set_clipboard(text)
        # Opcional: Mostrar un snackbar de confirmación
        e.page.show_snack_bar(
            ft.SnackBar(
                content=ft.Text("Texto copiado al portapapeles"),
                action="OK",
                duration=2000,
            )
        )
        e.page.update()

    def create_message_bubble(self, message, is_user=True):
        content_controls = (
            [
                ft.Text(
                    message,
                    selectable=True,
                    font_family="mons",
                )
            ]
            if is_user
            else self.process_message_with_code(message)
        )
        
        copy_button = ft.IconButton(
            icon=ft.Icons.COPY,
            icon_size=16,
            tooltip="Copiar mensaje",
            visible=not is_user,
            on_click=lambda e, msg=message: self.copy_to_clipboard(msg, e)
        )

        message_row = ft.Row(
            [
                ft.Container(
                    content=ft.Column(controls=content_controls, spacing=0, tight=True),
                    bgcolor=ft.Colors.PRIMARY if is_user else ft.Colors.GREY_700,
                    border_radius=8,
                    padding=10,
                ),
                ft.IconButton(
                    icon=ft.Icons.COPY,
                    icon_size=16,
                    tooltip="Copiar mensaje",
                    visible=not is_user,
                    on_click=lambda e, msg=message: self.copy_to_clipboard(msg, e)
                ),
            ],
            alignment=(
                ft.MainAxisAlignment.END if is_user else ft.MainAxisAlignment.START
            ), wrap=True
        )

        return message_row

    def main(self, page: ft.Page):
        #page.client_storage.set("api_key", ""),
        #page.client_storage.set("selected_model", self.current_model),
        page.title = "Chat AI"
        page.fonts = {
            "mon": "/fonts/MontserratAlternates-Light.ttf",
            "mons": "/fonts/MontserratAlternates-SemiBold.ttf",
            "monospace": "",
        }
        page.theme_mode = ft.ThemeMode.DARK
        page.theme = ft.Theme(
            color_scheme=ft.ColorScheme(
                primary="#F55036",
                secondary="#153333",
                background=ft.Colors.SECONDARY,
            ),
            scrollbar_theme=ft.ScrollbarTheme(
                thumb_color=ft.Colors.TRANSPARENT
            ),
            font_family="mons",
        )
        page.padding = 20
        # page.window.width = 400
        # page.window.height = 600
        page.update()

        # Cargar configuración previa
        self.proxy_enabled = page.client_storage.get("proxy_enabled") or False
        self.proxy_host = page.client_storage.get("proxy_host") or ""
        self.proxy_port = int(page.client_storage.get("proxy_port")) if page.client_storage.get("proxy_port") else 0
        self.proxy_user = page.client_storage.get("proxy_user") or ""
        self.proxy_pass = page.client_storage.get("proxy_pass") or ""


        # Aplicar proxy si estaba activado
        self.apply_proxy()

        # Crear interfaz de ajustes de proxy
        self.proxy_switch = ft.Switch(label="Habilitar Proxy", value=self.proxy_enabled)
        self.proxy_host_field = ft.TextField(label="Host", value=self.proxy_host, border_radius=35,
                border_color=ft.Colors.PRIMARY,
                color=ft.Colors.PRIMARY,)
        self.proxy_port_field = ft.TextField(label="Puerto", value=str(self.proxy_port), border_radius=35,
                border_color=ft.Colors.PRIMARY,
                color=ft.Colors.PRIMARY,)
        self.proxy_user_field = ft.TextField(label="Usuario", value=self.proxy_user, border_radius=35,
                border_color=ft.Colors.PRIMARY,
                color=ft.Colors.PRIMARY,)
        self.proxy_pass_field = ft.TextField(label="Contraseña", value=self.proxy_pass, password=True, border_radius=35,
                border_color=ft.Colors.PRIMARY,
                color=ft.Colors.PRIMARY,)

        # Agregar el diálogo de configuración al overlay
        #page.overlay.append(self.proxy_dialog)

        def check_api_key():
            stored_key = page.client_storage.get("api_key")
            stored_model = page.client_storage.get("selected_model")
            if stored_model:
                self.current_model = stored_model
            if stored_key:
                self.client = Groq(api_key=stored_key, )
                show_chat()
            else:
                show_welcome()

        def save(e,b=None):
            api_key = e
            self.current_model = b
            page.client_storage.set("selected_model", self.current_model)
            if api_key:
                page.client_storage.set("api_key", api_key)
                self.client = Groq(api_key=api_key)
                show_chat()
            if settings_dialog.open:
                settings_dialog.open = False
            page.update()

        def close(e):
            info_dialog.open = False
            page.update()

        def close_proxy(e):
            self.proxy_dialog.open = False
            page.update()

        def close_info(e):
            info_dialog.open = False
            page.update()
            
        def show_settings(e):
            settings_dialog.open = True
            page.update()

        def show_proxy(e):
            self.proxy_dialog.open = True
            page.update()
            
        def show_info(e):
            if settings_dialog.open:
                settings_dialog.open = False
            info_dialog.open = True
            page.update()

        def show_welcome():
            page.clean()
            page.add(
                ft.Column(
                    controls=[
                        ft.Container(
                            content=ft.Column(
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                controls=[
                                    ft.Divider(height=70, color="transparent"),
                                    ft.Image(
                                        "/images/groqcloud_light_v2.svg",
                                        border_radius=0,
                                        height=50,
                                    ),
                                    ft.Divider(height=70, color="transparent"),
                                    ft.Row(
                                        [
                                            ft.Text(
                                                "chat",
                                                size=32,
                                                weight=ft.FontWeight.BOLD,
                                                color=ft.Colors.WHITE,
                                                font_family="mons",
                                            ),
                                            ft.Text(
                                                "ai",
                                                size=32,
                                                weight=ft.FontWeight.BOLD,
                                                color=ft.Colors.PRIMARY,
                                                font_family="mon",
                                            ),
                                        ],
                                        alignment=ft.MainAxisAlignment.CENTER,
                                    ),
                                ],
                            ),
                            margin=ft.margin.only(bottom=40),
                        ),
                        ft.Divider(height=70, color="transparent"),
                        api_key_field,
                        ft.TextButton('Obtener API KEY', url='https://console.groq.com/keys'),
                        ft.Divider(height=50, color="transparent"),
                        ft.ElevatedButton(
                            text="COMENZAR",
                            width=200,
                            bgcolor=ft.Colors.PRIMARY,
                            color=ft.Colors.SECONDARY,
                            style=(
                                ft.ButtonStyle(overlay_color="white", color="white")
                            ),
                            on_click=lambda _: save(api_key_field.value, self.current_model),
                        ),
                        ft.Divider(height=100, color="transparent"),
                        ft.Text(
                            "Powered by groqcloud",
                            size=12,
                            color=ft.Colors.GREY_800,
                            font_family="mons",
                        ),
                        ft.Text(
                            "Dev @ElJoker63",
                            size=12,
                            color=ft.Colors.GREY_800,
                            font_family="mons",
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=0,
                )
            )

        def show_chat():
            page.clean()
            self.chat_display = ft.ListView(
                expand=True, spacing=0, auto_scroll=True, height=400
            )

            self.input_field = ft.TextField(
                hint_text="Escribe tu mensaje...",
                border_radius=8,
                border_color=ft.Colors.PRIMARY,
                expand=True,
                on_submit=self.send_message,
            )

            settings_button = ft.IconButton(icon=ft.Icons.SETTINGS, on_click=show_settings)
            
            send_button = ft.IconButton(icon=ft.Icons.SEND, on_click=self.send_message)

            page.add(
                ft.Divider(height=10, color="transparent"),
                ft.Row(
                    [
                        ft.Image(
                            "/images/groqcloud_light_v2.svg",
                            border_radius=0,
                            width=150,
                        ),
                        settings_button,
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Text(f'📦Modelo: {self.current_model}\n🐧Owner: {next((text for key, text in ChatApp.get_models().items() if key == self.current_model), None)}', color=ft.Colors.PRIMARY),
                ft.Container(
                    content=self.chat_display,
                    border=ft.border.all(1, ft.Colors.PRIMARY),
                    border_radius=8,
                    padding=10,
                    expand=True,
                ),
                ft.Row(
                    controls=[self.input_field, send_button],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
            )

        if page.client_storage.get("api_key"):
            api_key_field = ft.TextField(
                value=page.client_storage.get("api_key"),
                label="API_KEY GROQCLOUD",
                password=False,
                width=300,
                border_radius=35,
                border_color=ft.Colors.PRIMARY,
            )
        else:
            api_key_field = ft.TextField(
                label="API_KEY GROQCLOUD",
                password=False,
                width=300,
                border_radius=35,
                border_color=ft.Colors.PRIMARY,
                color=ft.Colors.PRIMARY,
            )

        # Botón de configuración de proxy
        proxy_button =  ft.TextButton('SET PROXY', on_click=show_proxy, style=ft.ButtonStyle(color=ft.Colors.PRIMARY),)
        #ft.IconButton(icon=ft.icons.SETTINGS, on_click=show_proxy)

        model_dropdown = ft.Dropdown(
            width=300,
            border_color=ft.Colors.PRIMARY,
            color=ft.Colors.PRIMARY,
            border_radius=35,
            label="Selecciona el modelo",
            options=[
                ft.dropdown.Option(key, key.upper().replace('-', ' '))
                for key, text in self.available_models.items()
            ],
            value=page.client_storage.get("selected_model"),
        )

        settings_dialog = ft.AlertDialog(
            # bgcolor=ft.Colors.SECONDARY,
            modal=True,
            title=ft.Row([ft.Text("Configuración", font_family="mon", color=ft.Colors.PRIMARY),ft.IconButton(icon=ft.Icons.INFO, on_click=show_info,)]),
            content=ft.Column(
                controls=[
                    proxy_button,
                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                    model_dropdown,
                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                    api_key_field,
                ],
                tight=True,
                spacing=5,
            ),
            actions=[
                ft.TextButton(
                    "GUARDAR", on_click=lambda _: save(api_key_field.value, model_dropdown.value)
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.proxy_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Proxy SOCKS5", font_family='mon', color=ft.Colors.PRIMARY),
            content=ft.Column([
                self.proxy_switch,
                self.proxy_host_field,
                self.proxy_port_field,
                self.proxy_user_field,
                self.proxy_pass_field,
            ], 
                tight=True,
                spacing=5,),
            actions=[
                ft.TextButton("Guardar", on_click=lambda _: self.save_proxy_settings(page)),
                ft.TextButton("Cerrar", on_click=close_proxy),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        page.overlay.append(self.proxy_dialog)
        page.overlay.append(settings_dialog)
        check_api_key()
        
        info_dialog = ft.AlertDialog(
            scrollable=True,
            modal=True,
            title=ft.Row([ft.Text("Información", font_family="mon", color=ft.Colors.PRIMARY)]),
            content=ft.Column(
                controls=[
                    ft.Row([ft.Image("/images/groqcloud_light_v2.svg",width=150)], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Text('gropcloud es una aplicación que ha sido creada con el objetivo de tener a la mano una potente herramienta que nos permite acceder y utilizar facilmente diferentes modelos de lenguaje.', text_align='center'),
                    ft.Divider(height=40, color='transparent'),
                    #ft.Row([ft.IconButton(ft.Icons.GET_APP)], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Row([ft.Text('Copyright (c) 2025 AEWareDevs', color=ft.Colors.PRIMARY)], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Row([ft.TextButton('ElJoker63', url='https://t.me/ElJoker63')], alignment=ft.MainAxisAlignment.CENTER),
                ],
                tight=True,
                spacing=0,
            ),
            actions=[
                ft.TextButton(
                    "CERRAR", on_click=lambda _: close(None)
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.overlay.append(info_dialog)

    def send_message(self, e):
        user_message = self.input_field.value
        if not user_message:
            return

        self.chat_display.controls.append(
            self.create_message_bubble(user_message, True)
        )

        self.chat_history.append({"role": "user", "content": user_message})

        try:
            response = self.client.chat.completions.create(
                model=self.current_model,
                messages=self.chat_history,
                temperature=1.2,
                max_tokens=2000,
                top_p=1,
            )

            ai_message = response.choices[0].message.content

            self.chat_display.controls.append(
                self.create_message_bubble(ai_message, False)
            )

            self.chat_history.append({"role": "assistant", "content": ai_message})
        except Exception as e:
            self.chat_display.controls.append(
                self.create_message_bubble(f"Error: {str(e)}", False)
            )

        self.input_field.value = ""
        self.chat_display.update()
        self.input_field.update()


if __name__ == "__main__":
    logging.info("Starting Flet application")
    ft.app(target=ChatApp().main, assets_dir='assets')

# APKAI

## Descripción

Esta aplicación es un chat de IA construido con Flet y Groq, que permite interactuar con modelos de lenguaje de Groq de manera fácil y accesible. Proporciona una interfaz gráfica para chatear con IA, gestionar configuraciones y personalizar la experiencia.

## Características

- **Interfaz de chat intuitiva**: Burbujas de mensajes con diseño moderno y tema oscuro.
- **Soporte para múltiples modelos**: Selecciona entre diferentes modelos de IA disponibles en Groq.
- **Configuración de proxy SOCKS5**: Permite configurar un proxy para conexiones seguras y anónimas.
- **Gestión de claves API**: Almacena y gestiona tu clave API de Groq de forma segura.
- **Resaltado de bloques de código**: Las respuestas de la IA con código se muestran en bloques destacados con opción de copiar.
- **Función de copiar al portapapeles**: Copia fácilmente mensajes o bloques de código.
- **Almacenamiento local**: Guarda configuraciones como API key, modelo seleccionado y ajustes de proxy.

## Instalación

1. Clona el repositorio:
   ```
   git clone https://github.com/ElJoker63/APKAI.git
   cd APKAI
   ```

2. Instala las dependencias:
   ```
   pip install -r requirements.txt
   ```

3. Ejecuta la aplicación:
   ```
   python main.py
   ```

## Uso

1. **Primera ejecución**: Ingresa tu clave API de Groq (puedes obtenerla en https://console.groq.com/keys).
2. **Selecciona modelo**: Elige el modelo de IA que deseas usar.
3. **Configura proxy** (opcional): Si necesitas usar un proxy SOCKS5, ve a Configuración > SET PROXY.
4. **Comienza a chatear**: Escribe tus mensajes en el campo de entrada y presiona Enter o el botón de enviar.
5. **Ajustes adicionales**: Usa el botón de configuración para cambiar modelo o API key.

## Requisitos

- Python 3.x
- Dependencias:
  - flet
  - groq
  - requests
  - pysocks
  - httpx[socks]
  - cryptography

## Créditos

- Desarrollado por @ElJoker63
- Powered by [GroqCloud](https://groq.com/)
- Copyright (c) 2025 AEWareDevs
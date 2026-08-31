import os
import sys
import threading
import time
import socket
import webview
from streamlit.web import cli as stcli

def get_free_port():
    """Boş bir yerel port bulur."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('127.0.0.1', 0))
    port = sock.getsockname()[1]
    sock.close()
    return port

def start_streamlit(port, app_path):
    """Streamlit uygulamasını arka planda sessizce başlatır."""
    sys.argv = [
        "streamlit",
        "run",
        app_path,
        f"--server.port={port}",
        "--server.headless=true",
        "--server.enableCORS=false",
        "--server.enableXsrfProtection=false",
        "--browser.gatherUsageStats=false",
        "--global.developmentMode=false",
    ]
    stcli.main()

def is_server_ready(port, timeout=15):
    """Sunucunun hazır olup olmadığını kontrol eder."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.create_connection(('127.0.0.1', port), timeout=1):
                return True
        except (socket.timeout, ConnectionRefusedError, OSError):
            time.sleep(0.3)
    return False

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    app_path = os.path.join(base_dir, "app.py")
    
    if not os.path.exists(app_path):
        print(f"Hata: {app_path} bulunamadı!")
        return

    port = get_free_port()

    # Streamlit motorunu arka planda başlat
    server_thread = threading.Thread(target=start_streamlit, args=(port, app_path), daemon=True)
    server_thread.start()

    # Hazır olmasını bekle
    if not is_server_ready(port):
        print("Uygulama sunucusu başlatılamadı.")
        return

    # Yerel masaüstü penceresini aç
    window = webview.create_window(
        title="AFSÜ İktisadi İşletme - Mesai Takip Sistemi",
        url=f"http://127.0.0.1:{port}",
        width=1280,
        height=850,
        resizable=True,
        min_size=(900, 600),
        confirm_close=True,
        text_select=True
    )
    
    # Masaüstü döngüsünü başlat
    webview.start(private_mode=False)

if __name__ == "__main__":
    main()

import cv2
import socket
import threading
import struct
import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

# Server Configuration
HOST = '0.0.0.0'  # Listen on all available network interfaces
PORT = 9999

# 16-byte Secret Key and Initialization Vector (IV) for AES-128 Encryption
# Note: In production, exchange keys securely using RSA or Diffie-Hellman
KEY = b'1234567890123456' 
IV = b'1234567890123456'

clients = []

def encrypt_frame(data):
    """Encrypts raw byte data using AES-CBC mode with PKCS7 padding."""
    pad_len = 16 - (len(data) % 16)
    data += bytes([pad_len]) * pad_len  # PKCS7 padding
    
    cipher = Cipher(algorithms.AES(KEY), modes.CBC(IV), backend=default_backend())
    encryptor = cipher.encryptor()
    return encryptor.update(data) + encryptor.finalize()

def handle_client(client_socket, addr):
    """Handles individual client streaming connection in a dedicated thread."""
    print(f"[+] Client connected from {addr}")
    clients.append(client_socket)
    try:
        while True:
            # Keep thread alive to monitor connection status
            pass
    except ConnectionResetError:
        print(f"[-] Client {addr} disconnected.")
    finally:
        if client_socket in clients:
            clients.remove(client_socket)
        client_socket.close()

def video_stream_loop():
    """Captures camera frames, encrypts them, and broadcasts to all active clients."""
    cap = cv2.VideoCapture(0)  # Use 0 for default webcam, or 'video.mp4' for a video file
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
            
        # Resize frame to reduce bandwidth and transmission latency
        frame = cv2.resize(frame, (640, 480))
        
        # Compress frame as JPEG image
        _, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 50])
        raw_bytes = buffer.tobytes()
        
        # Encrypt the compressed frame
        encrypted_data = encrypt_frame(raw_bytes)
        
        # Pack length of encrypted data (unsigned long long - 8 bytes)
        message_size = struct.pack("Q", len(encrypted_data))
        packet = message_size + encrypted_data
        
        # Broadcast frame packet to all connected clients
        for client in list(clients):
            try:
                client.sendall(packet)
            except Exception:
                clients.remove(client)
                
    cap.release()

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    print(f"[*] Server listening on {HOST}:{PORT}...")

    # Start video capture & encryption broadcast loop in a separate thread
    threading.Thread(target=video_stream_loop, daemon=True).start()

    while True:
        client_socket, addr = server_socket.accept()
        client_thread = threading.Thread(target=handle_client, args=(client_socket, addr))
        client_thread.start()

if __name__ == "__main__":
    start_server()
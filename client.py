import cv2
import socket
import struct
import numpy as np
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

# Server Connection Configuration
SERVER_IP = '127.0.0.1'  # Change to Server's IP address if running across network
PORT = 9999

KEY = b'1234567890123456'
IV = b'1234567890123456'

def decrypt_frame(encrypted_data):
    """Decrypts AES-CBC encrypted frame payload and removes PKCS7 padding."""
    cipher = Cipher(algorithms.AES(KEY), modes.CBC(IV), backend=default_backend())
    decryptor = cipher.decryptor()
    decrypted_data = decryptor.update(encrypted_data) + decryptor.finalize()
    
    pad_len = decrypted_data[-1]
    return decrypted_data[:-pad_len]

def start_client():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((SERVER_IP, PORT))
    print(f"[+] Connected to Encrypted Video Server at {SERVER_IP}:{PORT}")

    data = b""
    payload_size = struct.calcsize("Q")

    try:
        while True:
            # Retrieve packet header (length of payload)
            while len(data) < payload_size:
                packet = client_socket.recv(4096)
                if not packet:
                    break
                data += packet
                
            if not data:
                break

            packed_msg_size = data[:payload_size]
            data = data[payload_size:]
            msg_size = struct.unpack("Q", packed_msg_size)[0]

            # Retrieve full encrypted frame payload
            while len(data) < msg_size:
                data += client_socket.recv(4096)

            encrypted_frame = data[:msg_size]
            data = data[msg_size:]

            # Decrypt payload and decode JPEG frame
            decrypted_bytes = decrypt_frame(encrypted_frame)
            np_data = np.frombuffer(decrypted_bytes, dtype=np.uint8)
            frame = cv2.imdecode(np_data, cv2.IMREAD_COLOR)

            if frame is not None:
                cv2.imshow("Encrypted Video Stream (Client)", frame)

            # Press 'q' to disconnect and exit video window
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except Exception as e:
        print(f"[-] Streaming error: {e}")
    finally:
        client_socket.close()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    start_client()
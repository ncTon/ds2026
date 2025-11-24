import socket
import os
import struct
import argparse
import sys

HEADER_FORMAT = '>IQ'
# Note: We actually send the filename length (I), then filename, then size (Q).

def send_file(sock, filename):
    # protocol: [Filename Length (4B)][Filename (NB)][File Size (8B)][File Content...]
    if not os.path.exists(filename):
        print(f"Error: File '{filename}' not found.")
        return

    filesize = os.path.getsize(filename)
    filename_base = os.path.basename(filename)
    filename_encoded = filename_base.encode('utf-8')
    
    print(f"Preparing to send '{filename_base}' ({filesize} bytes)...")

    # Packet format: 
    #   - 4 bytes: Length of filename string
    #   - N bytes: Filename string
    #   - 8 bytes: File size
    
    try:
        sock.sendall(struct.pack('>I', len(filename_encoded)))
        sock.sendall(filename_encoded)
        sock.sendall(struct.pack('>Q', filesize))
        sent_total = 0
        with open(filename, 'rb') as f:
            while True:
                chunk = f.read(4096) # buffer
                if not chunk:
                    break
                sock.sendall(chunk)
                sent_total += len(chunk)
                
                # progress indicator
                sys.stdout.write(f"\rSending: {int(sent_total/filesize*100)}%")
                sys.stdout.flush()
                
        print("\nFile transfer completed successfully.")
        
    except Exception as e:
        print(f"\nError during transfer: {e}")

def recv_file(sock):
    try:
        raw_len = sock.recv(4)
        if not raw_len: return
        filename_len = struct.unpack('>I', raw_len)[0]

        filename = sock.recv(filename_len).decode('utf-8')
        raw_size = sock.recv(8)
        filesize = struct.unpack('>Q', raw_size)[0]
        print(f"Incoming file: '{filename}' ({filesize} bytes)")
        output_filename = f"received_{filename}"
        received = 0
        with open(output_filename, 'wb') as f:
            while received < filesize:
                bytes_to_read = min(4096, filesize - received)
                chunk = sock.recv(bytes_to_read)
                if not chunk: 
                    raise ConnectionError("Connection closed unexpectedly")
                f.write(chunk)
                received += len(chunk)
                
                # progress indicator
                sys.stdout.write(f"\rReceiving: {int(received/filesize*100)}%")
                sys.stdout.flush()
                
        print(f"\nSaved as '{output_filename}'. Transfer complete.")
        
    except Exception as e:
        print(f"\nError receiving file: {e}")

def run_server(port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # avoid "Address already in use" errors
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server_socket.bind(('0.0.0.0', port))
        server_socket.listen(1)
        print(f"Server listening on 0.0.0.0:{port}...")
        print("Press Ctrl+C to stop.")

        while True:
            conn, addr = server_socket.accept()
            print(f"\nConnection from {addr}")
            recv_file(conn)
            conn.close()
            print("Waiting for next connection...")
            
    except KeyboardInterrupt:
        print("\nServer stopped by user.")
    except Exception as e:
        print(f"Server error: {e}")
    finally:
        server_socket.close()

def run_client(host, port, filepath):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        print(f"Connecting to {host}:{port}...")
        client_socket.connect((host, port))
        send_file(client_socket, filepath)
    except ConnectionRefusedError:
        print("Error: Could not connect to server. Is it running?")
    except Exception as e:
        print(f"Client error: {e}")
    finally:
        client_socket.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simple TCP File Transfer Tool")
    subparsers = parser.add_subparsers(dest='mode', required=True, help='Mode: server or client')

    # Server arguments
    server_parser = subparsers.add_parser('server', help='Start in receiver mode')
    server_parser.add_argument('-p', '--port', type=int, default=5000, help='Port to listen on (default: 5000)')

    # Client arguments
    client_parser = subparsers.add_parser('client', help='Start in sender mode')
    client_parser.add_argument('host', help='Server IP address')
    client_parser.add_argument('filepath', help='Path to the file to send')
    client_parser.add_argument('-p', '--port', type=int, default=5000, help='Port to connect to (default: 5000)')

    args = parser.parse_args()

    if args.mode == 'server':
        run_server(args.port)
    elif args.mode == 'client':
        run_client(args.host, args.port, args.filepath)
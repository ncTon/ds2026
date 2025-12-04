from mpi4py import MPI # type: ignore
import os
import sys
import numpy as np # pyright: ignore[reportMissingImports]

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

CHUNK = 4096  # Same as TCP version


def send_file(filepath, dest=1):
    if not os.path.exists(filepath):
        print(f"[Sender] File '{filepath}' does not exist.")
        return

    filename = os.path.basename(filepath)
    filesize = os.path.getsize(filepath)

    print(f"[Sender] Preparing to send '{filename}' ({filesize} bytes)")

    # 1) Send filename
    comm.send(filename, dest=dest, tag=0)

    # 2) Send filesize
    comm.send(filesize, dest=dest, tag=1)

    sent = 0

    # 3) Send file in chunks
    with open(filepath, "rb") as f:
        while sent < filesize:
            data = f.read(CHUNK)
            arr = np.frombuffer(data, dtype=np.uint8)
            comm.Send(arr, dest=dest, tag=2)

            sent += len(data)
            sys.stdout.write(f"\r[Sender] Progress: {int(sent/filesize*100)}%")
            sys.stdout.flush()

    print("\n[Sender] File transfer complete.")


def recv_file(src=0):
    # 1) Receive filename
    filename = comm.recv(source=src, tag=0)

    # 2) Receive filesize
    filesize = comm.recv(source=src, tag=1)

    print(f"[Receiver] Incoming file '{filename}' ({filesize} bytes)")

    received = 0
    output_name = "received_" + filename

    with open(output_name, "wb") as f:
        while received < filesize:
            # Prepare buffer for chunk
            buffer = np.empty(min(CHUNK, filesize - received), dtype=np.uint8)
            comm.Recv(buffer, source=src, tag=2)

            f.write(buffer.tobytes())
            received += len(buffer)

            sys.stdout.write(f"\r[Receiver] Progress: {int(received/filesize*100)}%")
            sys.stdout.flush()

    print(f"\n[Receiver] Saved as '{output_name}'. Transfer complete.")


def main():
    if size < 2:
        print("Error: You must run with at least 2 MPI processes.")
        return

    if rank == 0:
        # Process 0 = sender
        filepath = input("Enter file path to send: ")
        send_file(filepath, dest=1)
    elif rank == 1:
        # Process 1 = receiver
        recv_file(src=0)
    else:
        print(f"Process {rank} not used.")


if __name__ == "__main__":
    main()

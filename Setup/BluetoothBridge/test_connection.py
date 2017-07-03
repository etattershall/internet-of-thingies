"""A script to test connection to hosts and print the results to console.
This is used instead of ping to show connection status to multiple different
hosts."""

import socket
import argparse
import time


def test(address, port):
    """Returns whether or not connection could be established to address over
    port."""
    try:
        s = socket.create_connection((address, port), 0.25)
    except (ConnectionRefusedError, socket.timeout) as ex:
        return False
    except OSError as e:
        print(address, port)
        raise

    else:
        s.close()
        return True


def wrapText(text, colour=None):
    """Returns text wrapped by green or red escape sequenses for console
    printing."""
    if colour == "green":
        return('\x1b[6;30;42m' + text + '\x1b[0m')
    elif colour == "red":
        return('\x1b[2;30;41m' + text + '\x1b[0m')
    else:
        return text


def print_results(addresses, port):
    """Runs tests and prints results on addresses over port."""
    result = (wrapText(text=addr + " Y", colour="green")
              if test(addr, args.port)
              else wrapText(text=addr + " N", colour="red")
              for addr in addresses)
    print(*result)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Test connection using '
                                                 'sockets.')
    parser.add_argument('-port', metavar='p', type=int, default=22,
                        help='The port to test.')
    parser.add_argument('-address', metavar='a', nargs="*", type=str,
                        default=["vm216.nubes.stfc.ac.uk",
                                 "130.246.77.144", "130.246.77.145"],
                        help='The address to connect to (ip or example.com).')

    args = parser.parse_args()
    try:
        while True:
            print_results(args.address, args.port)
            time.sleep(1)
    except KeyboardInterrupt:
        print("Quit.")

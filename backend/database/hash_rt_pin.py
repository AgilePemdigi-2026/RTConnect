"""Generate a bcrypt hash for RT_SIGNING_PIN_HASH without echoing the PIN."""

import getpass

import bcrypt


def main():
    pin = getpass.getpass('RT signing PIN (6 to 72 bytes): ')
    confirmation = getpass.getpass('Confirm PIN: ')
    if not 6 <= len(pin.encode('utf-8')) <= 72:
        raise SystemExit('PIN must be 6 to 72 bytes long.')
    if pin != confirmation:
        raise SystemExit('PINs do not match.')
    print(bcrypt.hashpw(pin.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'))


if __name__ == '__main__':
    main()

# PGPass
A password encryption and management command line application.

PGPass is a *portmanteau* of [PGP](https://www.openpgp.org/) and [Pass](https://www.passwordstore.org/). It utilizes GnuPG to encrypt and decrypt stored passwords on the device. 

Requires access to the device terminal and a GnuPG encryption keypair.

## Installation

1. Download and install [GnuPG](https://gnupg.org/) for your device
2. Create at least one keypair for encryption and decryption
3. `pip install -i https://test.pypi.org/simple/ PGPass`
4. Enter `pgpass` in a terminal and follow the setup

## Inspiration:
* [Pass](https://www.passwordstore.org/)
* [GnuPG](https://gnupg.org/)

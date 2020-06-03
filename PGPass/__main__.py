from click_shell import shell
from .passgen import generatePassword
import gnupg
import pyperclip
import yaml
import click
import os
import shutil
import time
# import logging

@shell(prompt='>> ', intro='************** PGPass v0.1.0 ***************',)
def cli():
	settings = read_settings()
	root = os.path.dirname(os.path.abspath(__file__))

	if not os.path.isdir(settings['storeDirectory']):
		datum = click.prompt(style('Enter the path for a password directory, ENTER for default', 'setup'), default='{}'.format(os.path.join(root, '.password-store')), show_default=False)
		try:
			os.mkdir(datum)
		except FileExistsError:
			# LOG
			pass
		while not os.path.isdir(datum):
			datum = click.prompt(style('Bad path, try again', 'error'), default='{}'.format(os.path.join(root, '.password-store')), show_default=False)
			try:
				os.mkdir(datum)
			except FileExistsError:
				# LOG 
				pass
		with open('{}'.format(os.path.join(root, 'settings.yaml')), 'w') as f:
			settings['storeDirectory'] = datum
			yaml.safe_dump(settings, f, default_flow_style=False)
		click.echo(style('Password store ready!', 'setup'))
		click.echo('---------------------------')

	if settings['gnupgDirectory'] != 'default' and not os.path.isdir(settings['gnupgDirectory']):
		datum = click.prompt(style('Enter the path for the GnuPG home directory, ENTER for default', 'setup'), default='default', show_default=False)
		while datum != 'default' and not os.path.exists('{}\\pubring.kbx'.format(datum)):
			datum = click.prompt(style('GnuPG not detected at this path, try again', 'error'), default='default', show_default=False)
		with open('{}'.format(os.path.join(root, 'settings.yaml')), 'w') as f:
			settings['gnupgDirectory'] = datum
			yaml.safe_dump(settings, f, default_flow_style=False)
			click.echo(style('GnuPG ready!', 'setup'))
			click.echo('---------------------------')

	if settings['encryptKey'] == '':
		datum = click.prompt(style('Enter fingerprint or partial userid of key to encrypt with', 'setup'), default='', show_default=False)
		found = False
		settings = read_settings()
		gpg = load_GPG()
		keys = gpg.list_keys()
		while not found:
			for key in keys:
				if key['fingerprint'].lower() == datum.lower():
					found = True
					settings['encryptKey'] = key['fingerprint']
				elif len(key['uids']) > 0:
					for ID in key['uids']:
						if datum in ID:
							found = True
							settings['encryptKey'] = key['fingerprint']
			if found:
				pass
			else:
				datum = click.prompt(style('Key not found, try again:', 'error'), default='', show_default=False)
		with open('{}'.format(os.path.join(root, 'settings.yaml')), 'w') as f:
			yaml.safe_dump(settings, f, default_flow_style=False)
		click.echo(style('Encryption key ready!', 'setup'))
		click.echo('---------------------------')

@cli.command()
@click.argument('name', type=click.STRING)
@click.argument('length', type=click.INT)
@click.option('-b', '--ban', type=click.STRING, help='Symbols to ban from password generation')
def new(name, length, ban):
	"""Creates a new password entry"""
	settings = read_settings()
	gpgs = [f for f in os.listdir(settings['storeDirectory']) if '.gpg' in f]
	if '{}.gpg'.format(name) in gpgs:
		click.echo(style('Password name already in use', 'error'))
	elif length < 1 or length > 100:
		if length > 100:
			length = click.echo(style('Length too large, must be < 101', 'error'))
		elif length < 1:
			length = click.echo(style('Length too small, must be > 0', 'error'))
	else:
		notes = click.prompt('Add any notes', default='', show_default=False)
		if ban == None:
			password = generatePassword(length)
		else:
			password = generatePassword(length, ban)
		settings = read_settings()
		gpg = load_GPG()
		data = '{}\n{}\n'.format(password, notes)
		encrypted_data = gpg.encrypt(data, settings['encryptKey'])
		with open('{}\\{}.gpg'.format(settings['storeDirectory'], name), 'w') as f:
			f.write(str(encrypted_data))
		click.echo(style('Password \'{}\' created successfully'.format(name), 'success'))

@cli.command()
@click.argument('name', type=click.STRING)
@click.option('-n', '--name', 'new_name', type=click.STRING, help='New name for password')
@click.option('-p', '--password', type=click.STRING, help='New password string')
@click.option('-no', '--notes', type=click.STRING, help='New notes for password')
def edit(name, new_name, password, notes):
	"""Edit a password or its name or its notes"""
	if new_name != None or password != None or notes != None:
		extract = decrypt(name)
		found = extract()
		print(found)
		if found:
			if password != None:
				found[0] = password
			if notes != None:
				found[1] = notes
			gpg = load_GPG()
			settings = read_settings()
			data = '\n'.join(found)
			encrypted_data = gpg.encrypt(data, settings['encryptKey'])
			if new_name != None:
				with open('{}\\{}.gpg'.format(settings['storeDirectory'], new_name), 'w') as f:
					f.write(str(encrypted_data))
				try:
					os.remove(os.path.join(settings['storeDirectory'], name + '.gpg'))
				except:
					# LOG that old file wasn't deleted
					pass
			else:
				with open('{}\\{}.gpg'.format(settings['storeDirectory'], name), 'w') as f:
					f.write(str(encrypted_data))
			click.echo(style('Password \'{}\' edited successfully'.format(name), 'success'))
		else:
			click.echo(style('Password {} does not exist'.format(name), 'error'))
	else:
		click.echo(style('Enter at least one option to change', 'error'))

@cli.command()
@click.argument('name', type=click.STRING)
def delete(name):
	"""Delete a stored password"""
	delete = click.confirm('Delete \'{}\'?'.format(name))
	if delete:
		settings = read_settings()
		gpgs = [f for f in os.listdir(settings['storeDirectory']) if '.gpg' in f]
		names = [f[:-4] for f in gpgs]
		if name in names:
			password = os.path.join(settings['storeDirectory'], gpgs[names.index(name)])
			try:
				os.remove(password)
				click.echo(style('\'{}\' deleted'.format(name), 'success'))
			except FileNotFoundError:
				click.echo(style('File not found!', 'error'))
		else:
			click.echo(style('File not found!', 'error'))

@cli.command()
def list():
	"""Lists all passwords in the store directory"""
	settings = read_settings()
	gpgs = [f for f in os.listdir(settings['storeDirectory']) if '.gpg' in f]
	if len(gpgs) < 1:
		click.echo(style('No passwords stored!', 'error'))
	else:
		names = [f[:-4] for f in gpgs]
		pass_list = '\n'.join(names)
		click.echo(click.style('Passwords\n----------', fg='bright_yellow'))
		click.echo(click.style(pass_list, bold=True))

@cli.command()
@click.option('-m', '--move', 'path', type=click.STRING, help='New path for password store')
def store(path):
	"""Returns the path of the password store"""
	settings = read_settings()
	if path == None:
		click.echo(style('Password store is:\n{}'.format(settings['storeDirectory']), 'info'))
	else:
		sure = click.confirm('Move all passwords to \'{}\'?'.format(path))
		if sure:
			try:
				os.mkdir(path)
			except:
				# LOG that directory exists
				pass
			gpgs = os.listdir(settings['storeDirectory'])
			for file in gpgs:
				if file.endswith('.gpg'):
					shutil.move(os.path.join(settings['storeDirectory'], file), path)
			try:
				os.rmdir(settings['storeDirectory'])
			except:
				# LOG that old store has non .gpg files inside
				pass
			settings['storeDirectory'] = path
			root = os.path.dirname(os.path.abspath(__file__))
			with open('{}'.format(os.path.join(root, 'settings.yaml')), 'w') as f:
				yaml.safe_dump(settings, f, default_flow_style=False)
			click.echo(style('Password store is now located at:\n{}'.format(settings['storeDirectory']), 'success'))
		else:
			click.echo(style('Password store is located at:\n{}'.format(settings['storeDirectory']), 'info'))

@cli.command()
@click.option('-t', '--time', 'duration', type=click.INT, help='New duration for password to be copied in the clipboard')
def timer(duration):
	"""Change the duration in seconds that a password is copied in the clipboard"""
	settings = read_settings()
	if duration == None:
		click.echo(style('Passwords are copied for {} seconds'.format(settings['copyTime']), 'info'))
	else:
		settings['copyTime'] = duration
		root = os.path.dirname(os.path.abspath(__file__))
		with open('{}'.format(os.path.join(root, 'settings.yaml')), 'w') as f:
			yaml.safe_dump(settings, f, default_flow_style=False)
		click.echo(style('Passwords will now be copied for {} seconds'.format(duration), 'success'))

@cli.command()
@click.argument('name')
@click.option('-n', '--notes', is_flag=True)
def get(name, notes):
	"""Get a stored password"""
	extract = decrypt(name)
	found = extract()
	if found:
		if notes:
			del found[0]
			notes_data = '\n'.join(found)
			click.echo(style('Notes for password \'{}\' are:\n'.format(name), 'info'))
			click.echo(notes_data)
		else:
			settings = read_settings()
			pyperclip.copy(found[0])
			click.echo(style('Password {} copied to clipboard'.format(name), 'info'))	
			with click.progressbar(length=settings['copyTime'], show_percent=False) as bar:
				while bar.pos != bar.length:
					time.sleep(1)
					bar.update(1)
			pyperclip.copy('')
	if not found:
		click.echo(style('Password {} does not exist'.format(name), 'error'))

@cli.command()
@click.option('-i', '--id', 'identifier', type=click.STRING, help='Fingerprint or partial ID of key to encrypt with')
def key(identifier):
	"""Check encryption key fingerprint or change key to the one identified"""
	found = False
	root = os.path.dirname(os.path.abspath(__file__))
	settings = read_settings()
	if identifier == None:
		click.echo(style('{} in use'.format(settings['encryptKey']), 'info'))
	else:
		gpg = load_GPG()
		keys = gpg.list_keys()
		for key in keys:
			if key['fingerprint'].lower() == identifier.lower():
				found = True
				settings['encryptKey'] = key['fingerprint']
			elif len(key['uids']) > 0:
				for ID in key['uids']:
					if identifier in ID:
						found = True
						settings['encryptKey'] = key['fingerprint']
		if found:	
			with open('{}'.format(os.path.join(root, 'settings.yaml')), 'w') as f:
				yaml.safe_dump(settings, f, default_flow_style=False)
			click.echo(style('{} now in use'.format(settings['encryptKey']), 'success'))
		else:
			click.echo(style('Key not found', 'error'))

# UTILITY METHODS
def style(message, mode=None):
	style = None
	if mode == 'error':
		style = click.style('[ERROR] ' + message, fg='bright_red')
	elif mode == 'success':
		style = click.style('[SUCCESS] ' + message, fg='bright_green')
	elif mode == 'info':
		style = click.style('[INFO] ' + message, fg='bright_yellow')
	elif mode == 'setup':
		style = click.style('[SETUP] ' + message, fg='bright_magenta')
	else:
		style = message
	return style

def load_GPG():
	settings = read_settings()
	gpg = None
	if settings['gnupgDirectory'] == 'default':
		gpg = gnupg.GPG()
	else:
		gpg = gnupg.GPG(gnupghome=settings['gnupgDirectory'])
	gpg.encoding = 'utf-8'
	return gpg

def read_settings():
	settings = None
	root = os.path.dirname(os.path.abspath(__file__))
	with open('{}'.format(os.path.join(root, 'settings.yaml')), 'r') as f:
		settings = yaml.safe_load(f)
	return settings

def decrypt(name):
	settings = read_settings()
	gpgs = [f for f in os.listdir(settings['storeDirectory']) if '.gpg' in f]
	names = [f[:-4] for f in gpgs]
	if name in names:
		path = os.path.join(settings['storeDirectory'], gpgs[names.index(name)])
		gpg = load_GPG()
		def closure():
			decrypted_data = None
			with open(path, 'rb') as f:
				decrypted_data = gpg.decrypt_file(f)
				data = str(decrypted_data).split('\n')
			return data
		return closure
	else:
		return False

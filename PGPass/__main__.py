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

IO_READ = 'r'
IO_WRITE = 'w'
IO_RB = 'rb'
# IO_WB = 'wb'
MODE_SETUP = 'setup'
MODE_INFO = 'info'
MODE_ERROR = 'error'
MODE_SUCCESS = 'success'

@shell(prompt='>> ', intro='************** PGPass v0.1.0 ***************',)
def cli():
	setup()
	
@cli.command()
@click.argument('name', type=click.STRING)
@click.argument('length', type=click.INT)
@click.option('-b', '--ban', type=click.STRING, help='Symbols to ban from password generation')
def new(name, length, ban):
	"""Creates a new password entry"""
	settings = read_settings()
	gpgs = [f for f in os.listdir(settings['storeDirectory']) if '.gpg' in f]
	if '{}.gpg'.format(name) in gpgs:
		click.echo(style('Password name already in use', mode=MODE_ERROR))
	elif length < 1 or length > 100:
		if length > 100:
			length = click.echo(style('Length too large, must be < 101', mode=MODE_ERROR))
		elif length < 1:
			length = click.echo(style('Length too small, must be > 0', mode=MODE_ERROR))
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
		f = IO_operation(os.path.join(settings['storeDirectory'], name+'.gpg'), mode=IO_WRITE)
		if f:
			with f:
				f.write(str(encrypted_data))
			click.echo(style('Password \'{}\' created successfully'.format(name), mode=MODE_SUCCESS))
		else:
			pass

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
				f = IO_operation(os.path.join(settings['storeDirectory'], new_name+'.gpg'), mode=IO_WRITE)
				if f:
					with f:
						f.write(str(encrypted_data))
					try:
						os.remove(os.path.join(settings['storeDirectory'], name + '.gpg'))
					except Exception as e:
						# LOG that old file wasn't deleted
						click.echo(click.style(str(e), fg='bright_red'))
				else:
					pass
			else:
				f = IO_operation(os.path.join(settings['storeDirectory'], name+'.gpg'), mode=IO_WRITE)
				if f:
					with f:
						f.write(str(encrypted_data))
					click.echo(style('Password \'{}\' edited successfully'.format(name), mode=MODE_SUCCESS))
				else:
					pass
		else:
			click.echo(style('Password {} does not exist'.format(name), mode=MODE_ERROR))
	else:
		click.echo(style('Enter at least one option to change', mode=MODE_ERROR))

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
				click.echo(style('\'{}\' deleted'.format(name), mode=MODE_SUCCESS))
			except Exception as e:
				click.echo(click.style(str(e), fg='bright_red'))
		else:
			click.echo(style('File not found!', mode=MODE_ERROR))

@cli.command()
def list():
	"""Lists all passwords in the store directory"""
	settings = read_settings()
	gpgs = [f for f in os.listdir(settings['storeDirectory']) if '.gpg' in f]
	if len(gpgs) < 1:
		click.echo(style('No passwords stored!', mode=MODE_ERROR))
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
		click.echo(style('Password store is:\n{}'.format(settings['storeDirectory']), mode=MODE_INFO))
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
			f = IO_operation(os.path.join(root, 'settings.yaml'), mode=IO_WRITE)
			if f:
				with f:
					yaml.safe_dump(settings, f, default_flow_style=False)
				click.echo(style('Password store is now located at:\n{}'.format(settings['storeDirectory']), mode=MODE_SUCCESS))
			else:
				pass
		else:
			click.echo(style('Password store is located at:\n{}'.format(settings['storeDirectory']), mode=MODE_INFO))

@cli.command()
@click.option('-t', '--time', 'duration', type=click.INT, help='New duration for password to be copied in the clipboard')
def timer(duration):
	"""Change the duration in seconds that a password is copied in the clipboard"""
	settings = read_settings()
	if duration == None:
		click.echo(style('Passwords are copied for {} seconds'.format(settings['copyTime']), mode=MODE_INFO))
	else:
		settings['copyTime'] = duration
		root = os.path.dirname(os.path.abspath(__file__))
		f = IO_operation(os.path.join(root, 'settings.yaml'), mode=IO_WRITE)
		if f:	
			with f:
				yaml.safe_dump(settings, f, default_flow_style=False)
			click.echo(style('Passwords will now be copied for {} seconds'.format(duration), mode=MODE_SUCCESS))
		else:
			pass

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
			click.echo(style('Notes for password \'{}\' are:\n'.format(name), mode=MODE_INFO))
			click.echo(notes_data)
		else:
			settings = read_settings()
			pyperclip.copy(found[0])
			click.echo(style('Password {} copied to clipboard'.format(name), mode=MODE_INFO))	
			with click.progressbar(length=settings['copyTime'], show_percent=False) as bar:
				while bar.pos != bar.length:
					time.sleep(1)
					bar.update(1)
			pyperclip.copy('')
	if not found:
		click.echo(style('Password {} does not exist'.format(name), mode=MODE_ERROR))

@cli.command()
@click.option('-i', '--id', 'identifier', type=click.STRING, help='Fingerprint or partial ID of key to encrypt with')
def key(identifier):
	"""Check encryption key fingerprint or change key to the one identified"""
	found = False
	root = os.path.dirname(os.path.abspath(__file__))
	settings = read_settings()
	if identifier == None:
		click.echo(style('{} in use'.format(settings['encryptKey']), mode=MODE_INFO))
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
			f = IO_operation(os.path.join(root, 'settings.yaml'), mode=IO_WRITE)
			if f:	
				with f:
					yaml.safe_dump(settings, f, default_flow_style=False)
				click.echo(style('{} now in use'.format(settings['encryptKey']), mode=MODE_SUCCESS))
			else:
				pass
		else:
			click.echo(style('Key not found', mode=MODE_ERROR))

# UTILITY METHODS
def style(message, mode=None):
	style = None
	if mode == MODE_ERROR:
		style = click.style('[ERROR] ' + message, fg='bright_red')
	elif mode == MODE_SUCCESS:
		style = click.style('[SUCCESS] ' + message, fg='bright_green')
	elif mode == MODE_INFO:
		style = click.style('[INFO] ' + message, fg='bright_yellow')
	elif mode == MODE_SETUP:
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
	f = IO_operation(os.path.join(root, 'settings.yaml'), mode=IO_READ)
	if f:
		with f:
			settings = yaml.safe_load(f)
	else:
		pass
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
			f = IO_operation(path, mode=IO_RB)
			if f:
				with f:
					decrypted_data = gpg.decrypt_file(f)
					data = str(decrypted_data).split('\n')
			else:
				pass
			return data
		return closure
	else:
		return False

def IO_operation(path, mode=IO_READ):
	file = None
	try:
		file = open(path, mode)
	except Exception as e:
		# LOG
		click.echo(click.style(str(e), fg='bright_red'))
	return file

def setup():
	root = os.path.dirname(os.path.abspath(__file__))

	# Settings check
	f = IO_operation(os.path.join(root, 'settings.yaml'), mode=IO_READ)
	if f:
		with f:
			settings = yaml.safe_load(f)
		# LOG THIS
		# print('Using prexisting settings file')
	else:
		# LOG THIS
		# print('Settings file not found, creating...')
		f = IO_operation(os.path.join(root, 'settings.yaml'), mode=IO_WRITE)
		if f:
			with f:
				yaml.safe_dump({'storeDirectory': '', 'gnupgDirectory': '', 'encryptKey': '', 'copyTime': 15}, f, default_flow_style=False)
				# LOG
				print('New settings file created')
		else:
			pass

	settings = read_settings()

	# Password store check
	if not os.path.isdir(settings['storeDirectory']):
		datum = click.prompt(style('Enter the path for a password directory, ENTER for default', mode=MODE_SETUP), default=os.path.join(root, '.password-store'), show_default=False)
		while not os.path.isdir(datum):
			try:
				os.mkdir(datum)
			except Exception as e:
				# LOG 
				click.echo(click.style(str(e), fg='bright_red'))
			datum = click.prompt(style('Bad path, try again', mode=MODE_ERROR), default=os.path.join(root, '.password-store'), show_default=False)
		f = IO_operation(os.path.join(root, 'settings.yaml'), IO_WRITE)
		if f:
			with f:
				settings['storeDirectory'] = datum
				yaml.safe_dump(settings, f, default_flow_style=False)
			click.echo(style('Password store ready!', mode=MODE_SETUP))
			click.echo('---------------------------')
		else:
			pass

	# GnuPG check
	if settings['gnupgDirectory'] != 'default' and not os.path.isdir(settings['gnupgDirectory']):
		datum = click.prompt(style('Enter the path for the GnuPG home directory, ENTER for default', mode=MODE_SETUP), default='default', show_default=False)
		while datum != 'default' and not os.path.exists('{}\\pubring.kbx'.format(datum)):
			datum = click.prompt(style('GnuPG not detected at this path, try again', mode=MODE_ERROR), default='default', show_default=False)
		f = IO_operation(os.path.join(root, 'settings.yaml'), IO_WRITE)
		if f:
			with f:
				settings['gnupgDirectory'] = datum
				yaml.safe_dump(settings, f, default_flow_style=False)
			click.echo(style('GnuPG ready!', mode=MODE_SETUP))
			click.echo('---------------------------')
		else:
			pass

	# Encryption key check
	if settings['encryptKey'] == '':
		datum = click.prompt(style('Enter fingerprint or partial userid of key to encrypt with', mode=MODE_SETUP), default='', show_default=False)
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
				datum = click.prompt(style('Key not found, try again:', mode=MODE_ERROR), default='', show_default=False)
		f = IO_operation(os.path.join(root, 'settings.yaml'), IO_WRITE)
		if f:
			with f:
				yaml.safe_dump(settings, f, default_flow_style=False)
			click.echo(style('Encryption key ready!', mode=MODE_SETUP))
		else:
			pass

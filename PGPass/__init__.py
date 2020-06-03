import yaml
import os

try:
	with open('{}'.format(os.path.dirname(os.path.abspath(__file__)) + '\\settings.yaml'), 'r') as f:
		settings = yaml.safe_load(f)
		# LOG THIS
		# print('Using prexisting settings file')
except IOError:
	# LOG THIS
	# print('Settings file not found, creating...')
	with open('{}'.format(os.path.dirname(os.path.abspath(__file__)) + '\\settings.yaml'), 'w') as f:
		yaml.safe_dump({'storeDirectory': '', 'gnupgDirectory': '', 'encryptKey': '', 'copyTime': 15}, f, default_flow_style=False)
		print('New settings file created')

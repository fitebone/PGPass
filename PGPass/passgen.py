from random import SystemRandom

def generatePassword(length=20, ban=''):
	systemRandom = SystemRandom()
	password = ''
	components = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 !@#$%^&*)(}{][\\/~;:\'\"`-+=.,_|<>'

	for char in ban:
		components = components.replace(char, '')
	selection = split(components)
	for i in range(length):
		num = systemRandom.randint(0, len(selection)-1)
		password += selection[num]
	return password

def split(word):
	return [char for char in word]

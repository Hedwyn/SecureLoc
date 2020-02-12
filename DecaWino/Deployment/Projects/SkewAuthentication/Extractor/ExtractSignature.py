COM_PORT = 'COM17'
#DIRECTORY = 'References/'
DIRECTORY = 'Challenges/'
LOG_PATH = '../skew_' + COM_PORT + '.txt'
SIGNATURE_FILE = DIRECTORY + 'signature_' + COM_PORT + '.txt'

with open(LOG_PATH, 'r') as f:
    signature = ''
    for line in f:
        data = line.split()
        if len(data) == 2:
            signature += data[0] + '|'
    print(signature)

with open(SIGNATURE_FILE, 'a+') as f:
    f.write('\n')
    f.write(signature[:-1])

import math
IN_FILE = "skew_COM21.txt"

def get_average(in_file, id):
    with open(in_file, 'r') as f:
        sum  = 0
        idx = 0
        for line in f:
            data = line.split()
            if len(data) == 3:
                try:
                    sum += float(data[id])
                    idx += 1
                except:
                    print("unproper_value: " + line)
    return(sum/idx)


def get_std(in_file, id):
    average = get_average(in_file, id)
    with open(in_file, 'r') as f:
        sum = 0
        idx = 0
        for line in f:
            data = line.split()
            if len(data) ==  3:
                try:
                    sum += pow(float(data[id]) - average, 2)
                    idx += 1
                except:
                    print("unproper_value: " + line)
    return(math.sqrt(sum/idx))


if __name__ == "__main__":
    print(get_average(IN_FILE, 1))
    print(get_std(IN_FILE, 1))

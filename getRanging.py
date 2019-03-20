import sys

LOGSFILE = "rangings/logs"
OUTDIR = "single_rangings"
OUTNAME = "logs"
ANCHORS = ['A','B','C','D']


def getSingleRangings(anchor_name,logsfile,outfile):

    logs = open(logsfile)
    out = open(outfile,'w+')
    for line in logs:
        values = line.split()

        if ( len(values) == 4):
            # set of rangings
            out.write(values[ ANCHORS.index(anchor_name) ] + "\n" )
        else:
            # copying the line
            out.write(line)
    logs.close()
    out.close()
    

def getAllRangings(logindex):
    logsfile = LOGSFILE +  str(logindex) +  ".txt"
    

    for anchor_name in ANCHORS:
        outfile = OUTDIR + "/" + anchor_name + "/" + OUTNAME + logindex + ".txt"
        getSingleRangings(anchor_name,logsfile,outfile)
    
    


if __name__ == "__main__":


    if (len(sys.argv) == 1):
        print("Index of logsfile should be given in args. Quitting...")
              
    elif (len(sys.argv) == 2):
        # only one file to extract
        getAllRangings(sys.argv[1])
        
    else:
        idx = int(sys.argv[1])
        while (idx <= int(sys.argv[2]) ):
            getAllRangings(str(idx) )
            idx += 1
            

              
        
        
        
    

    
    

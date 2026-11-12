import zmq

def main():
    ctx = zmq.Context()
    xsub = ctx.socket(zmq.XSUB)
    xsub.bind("tcp://*:5557")
    xpub = ctx.socket(zmq.XPUB)
    xpub.bind("tcp://*:5558")
    zmq.proxy(xsub, xpub)

if __name__ == "__main__":
    main()
# XR-1000 Keypad Controller
# rev 1 - march 2022 - shabaz
import board
import audiomp3
import audiobusio
from digitalio import DigitalInOut, Direction
import adafruit_matrixkeypad
import busio
import time

# file names
fname = [
    "0.mp3",
    "1.mp3",
    "2.mp3",
    "3.mp3",
    "4.mp3",
    "5.mp3",
    "6.mp3",
    "7.mp3",
    "8.mp3",
    "9.mp3",
    "forward.mp3",
    "back.mp3",
    "tleft.mp3",
    "tright.mp3",
    "function.mp3",
    "enter.mp3",
]

# commands
cname = [
    "fwd",  # 10
    "back",  # 11
    "left",  # 12
    "right",  # 13
    "",  # 14
    "",  # 15
    "",  # 16
    "",  # 100
    "",  # 101
    "",  # 102
    "pu",  # 103
    "",  # 104
    "",  # 105
    "pd",  # 106
    "",  # 107
    "",  # 108
    "",  # 109
]

# keypad
cols = [DigitalInOut(x) for x in (board.GP2, board.GP3, board.GP6, board.GP7)]
rows = [DigitalInOut(x) for x in (board.GP8, board.GP9, board.GP10, board.GP11)]
keys = ((1, 2, 3, 10), (4, 5, 6, 11), (7, 8, 9, 12), (14, 0, 15, 13))
keypad = adafruit_matrixkeypad.Matrix_Keypad(rows, cols, keys)

# uart
uart = busio.UART(
    tx=board.GP0, rx=board.GP1, baudrate=115200, timeout=0.25, receiver_buffer_size=16
)

# command list
command = []

# other variables
forever = 1


def get_fname(n):
    if n >= 0 and n < 16:
        return fname[n]
    else:
        return ""


def build_command(a, p):
    comstr = ""
    if a > 9 and a < 14:
        comstr = cname[a - 10] + " " + p
    elif a == 103:  # FUNC3
        comstr = cname[a - 93]
    elif a == 106:  # FUNC6
        comstr = cname[a - 93]
    else:
        pass
    return comstr


def command_append(a, p):
    global command
    comstr = build_command(a, p)
    command.append(comstr)
    print(f"command added: {comstr}, total is {len(command)}")


def uart_flush():
    n = uart.in_waiting
    if n >= 0:
        uart.read(n)


def uart_waitfor(s, maxtime):
    i = 0
    r = bytearray()
    idx = -1
    print(f"waiting for '{s}'\n\r")
    while True:
        n = uart.in_waiting
        if n >= 0:
            r.extend(uart.read(n))
            if len(r) > 2:
                print(f"r is '{r}'")
                idx = r.find(s)
                if idx >= 0:
                    break
        i = i + 1
        time.sleep(0.1)
        if i >= maxtime:
            break
    if idx >= 0:  # success, received the expected content
        print("success\n\r")
        return 0
    else:
        print("timed out\n\r")
        return -1


def command_send_uart(a, p, s=""):
    if a < 0:
        comstr = s
    else:
        comstr = build_command(a, p)
    print(f"todo, send uart '{comstr}'")
    uart_flush()
    uart.write(bytearray(comstr + "\r"))  # \n\r
    res = uart_waitfor("PR", 10)  # wait up to 10 * 0.1 seconds for a PR response
    if res >= 0:  # only wait for OK if we first saw PR
        uart_flush()
        res = uart_waitfor("OK", 200)  # wait up to 200 * 0.1 seconds for an OK response
        if res < 0:  # timed out
            print("timed out.. was this an extremely long motor operation?")


def program_send():
    for i, c in enumerate(command):
        print(f"line {i}: '{c}'")
        if "rpt" in c:
            tok = c.split()  # [0]=rpt, [1]=secpos, [2]=timesparam
            for lp in range(0, int(tok[2])):
                for j in range(int(tok[1]), i):
                    command_send_uart(-1, "", command[j])
        else:
            command_send_uart(-1, "", c)


# main program
def main():
    global command
    print("Hello")
    # setup connections
    # create I2S output, pins order: (BCLK, FS, DATA)
    i2s = audiobusio.I2SOut(board.GP14, board.GP15, board.GP13)
    # board LED
    boardled = DigitalInOut(board.GP25)
    boardled.direction = Direction.OUTPUT

    # create MP3 decoder with any file
    dummy = open(fname[0], "rb")
    asource = audiomp3.MP3Decoder(dummy)

    param = ""  # this is the command parameter
    action = 0  # this is the actual command instruction

    f = ""  # filename
    fsel = 0  # function button not pressed
    section = 0  # a section (for repeats) is not being defined
    secpos = 0  # the index to the section start
    penstate = -1  # pen state is unknown
    tested = 0  # set to 1 if a test instruction was just executed
    while forever:
        keys = keypad.pressed_keys
        if keys:
            knum = keys[0]
            f = get_fname(knum)
            if f != "":
                print(f"key {knum}, action {action}, param '{param}'")
                asource.file = open(f, "rb")
                i2s.play(asource)  # play the audio source
                if fsel == 0:  # we are in normal mode
                    if knum < 10:  # digit was pressed
                        asource.file = open(f, "rb")
                        i2s.play(asource)  # play the audio source
                        if tested > 0:  # we have just run a test instruction earlier
                            param = ""  # clear out the previous parameter
                            tested = 0
                        param = param + str(knum)
                    elif knum < 14:  # action button A-D was pressed
                        asource.file = open(f, "rb")
                        i2s.play(asource)  # play the audio source
                        action = knum
                    elif knum == 14:  # function was pressed
                        if fsel == 1:  # we are already in function mode
                            fsel = 0
                            asource.file = open("nofunc.mp3", "rb")
                            i2s.play(asource)  # play the audio source
                        else:
                            fsel = 1
                            asource.file = open(f, "rb")
                            i2s.play(asource)  # play the audio source
                    elif knum == 15:  # enter was pressed
                        if section == 2:
                            command.append("rpt " + str(secpos) + " " + param)
                            section = 0
                            secpos = 0
                            param = ""
                            action = 0
                        elif param == "" or action == 0:
                            asource.file = open("needinp.mp3", "rb")
                            i2s.play(asource)  # play the audio source
                        else:
                            asource.file = open(f, "rb")
                            i2s.play(asource)  # play the audio source
                            command_append(action, param)
                            param = ""
                            action = 0
                    else:
                        asource.file = open("error.mp3", "rb")
                        i2s.play(asource)  # play the audio source
                    #  while i2s.playing:
                    #    pass
                else:  # fsel == 1, we are in function selection mode
                    if knum == 1:  # FUNC1 = Cancel
                        if param == "" and action == 0 and len(command) > 0:
                            asource.file = open("undolastcmd.mp3", "rb")
                            i2s.play(asource)  # play the audio source
                            command.pop()
                        else:
                            asource.file = open("cancel.mp3", "rb")
                            i2s.play(asource)  # play the audio source
                            param = ""
                            action = 0
                    elif knum == 2:  # FUNC2 = Repeat a section
                        if section == 0:
                            asource.file = open("repsec.mp3", "rb")
                            i2s.play(asource)  # play the audio source
                            section = 1
                            secpos = len(command)
                        elif section == 1:  # we are now at the end of a section
                            secend = len(command)
                            if secend <= secpos:  # no commands in the section!
                                asource.file = open("abort.mp3", "rb")
                                i2s.play(asource)  # play the audio source
                                section = 0
                                secpos = 0
                            else:
                                asource.file = open("reptimes.mp3", "rb")
                                i2s.play(asource)  # play the audio source
                                section = 2
                        else:  # we should not be here!
                            asource.file = open("abort.mp3", "rb")
                            i2s.play(asource)  # play the audio source
                            section = 0
                            secpos = 0
                    elif knum == 3:  # FUNC3 = Pen Up
                        if penstate == 1:  # pen is already up
                            pass
                        else:
                            asource.file = open("up.mp3", "rb")
                            i2s.play(asource)  # play the audio source
                            action = knum + 100
                            param = "-"
                            penstate = 1
                    elif knum == 4:  # FUNC4 = Mem STO
                        if len(command) < 1:
                            asource.file = open("needinp.mp3", "rb")
                            i2s.play(asource)  # play the audio source
                        else:
                            asource.file = open("memsto.mp3", "rb")
                            i2s.play(asource)  # play the audio source
                            #  todo: implement STO feature
                    elif knum == 5:  # FUNC5 = Mem RCL
                        asource.file = open("memrcl.mp3", "rb")
                        i2s.play(asource)  # play the audio source
                        #  todo: implement RCL feature
                    elif knum == 6:  # FUNC6 = Pen Down
                        if penstate == 0:  # pen is already down
                            pass
                        else:
                            asource.file = open("down.mp3", "rb")
                            i2s.play(asource)  # play the audio source
                            action = knum + 100
                            param = "-"
                            penstate = 0
                    elif knum == 9:  # FUNC9 = test the instruction
                        if param == "" or action == 0:
                            asource.file = open("needinp.mp3", "rb")
                            i2s.play(asource)  # play the audio source
                        else:
                            asource.file = open("test321.mp3", "rb")
                            i2s.play(asource)  # play the audio source
                            while i2s.playing:
                                pass
                            command_send_uart(action, param)  # issue the test instruc.
                            asource.file = open("ready.mp3", "rb")
                            i2s.play(asource)  # play the audio source
                            tested = 1
                    elif knum == 15:  # FUNC-ENTER = run the current program
                        asource.file = open("go.mp3", "rb")
                        i2s.play(asource)  # play the audio source
                        while i2s.playing:
                            pass
                        program_send()
                        asource.file = open("ready.mp3", "rb")
                        i2s.play(asource)  # play the audio source
                    elif knum == 0:  # FUNC0 = print debug silently
                        asource.file = open("nofunc.mp3", "rb")
                        i2s.play(asource)  # play the audio source
                        for i, c in enumerate(command):
                            print(f"{i}: {c}")
                        print("End")
                    else:
                        asource.file = open("nofunc.mp3", "rb")
                        i2s.play(asource)  # play the audio source
                    fsel = 0

            f = ""
            time.sleep(0.2)
        time.sleep(0.01)


main()  # run main program

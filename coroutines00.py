"""协程的小练习，利用协程实现同时进行一个抽象的复杂任务（这里用time.sleep()代替）和一个不断旋转的指示器"""

import time
import sys


def draw():
    while True:
        for icon in ['/  ', '|  ', '\\  ', '——  ']:
            sys.stdout.write('\r')
            sys.stdout.write(icon)
            sys.stdout.flush()
            x = yield


def time_waste():
    current_time = 0
    while True:
        time.sleep(0.2)
        current_time += 0.2
        x = yield current_time


def main():
    total_time = 10
    draw_machine = draw()
    time_waste_machine = time_waste()
    next(draw_machine)
    next(time_waste_machine)
    is_finished = False
    while not is_finished:
        draw_machine.send(1)
        current_time = time_waste_machine.send(1)
        if current_time >= total_time:
            is_finished = True


if __name__ == '__main__':
    main()
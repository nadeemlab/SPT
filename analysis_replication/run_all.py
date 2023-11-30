
from typing import Callable
from time import sleep

from accessors import StillPendingException

from melanoma_il2 import test as test1
from melanoma_ici import test as test2
from breast_imc import test as test3
from luad_imc import test as test4

def do_test(test: Callable):
    while True:
        try:
            test()
            break
        except StillPendingException:
            seconds = 10
            print(f'Waiting {seconds} seconds to poll.')
            sleep(seconds)


if __name__=='__main__':
    for test in [test1, test2, test3, test4]:
        do_test(test)

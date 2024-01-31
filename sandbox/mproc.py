# multiprocessing exception handling
import multiprocessing as mp
import ctypes
import time


class ZoinksException(Exception):
    def __init__(
        self,
        message="\n\n\033[0;31mLiek Zoinks sckooby\033[0m\n",
    ):
        self.message = message
        super().__init__(self.message)

def child_process(name= "NIL"):
    import time
    print(f"Hello {name}, Welcome to the company.")
    time.sleep(3)
    print(f"{name} is done")
    try:
        int("hello")
    except ValueError:
        print("Value Error")
    finally:
        raise ZoinksException


def excall(e: Exception):
    """Handles the immediate exception, should exit immediately or blocks
    the thread handling the result

    :param e: _description_
    :type e: Exception
    """
    print(str(e))
    # SystemExit(0)
    return

def main():
    # setup process pool.
    try:
        manager = mp.Manager()
        pool = mp.Pool(3)
        name = "Robocop"
        ar1 = pool.apply_async(child_process, (name,), error_callback=excall)
        name = "kony"
        ar2 = pool.apply_async(child_process, (name,), error_callback=excall)
        print("is ar1 ready?",ar1.ready())
        print("Waiting on pool to close, processes to exit\n")
        pool.close()
        pool.join() # Wait on child processes to close
        print("is ar1 ready?",ar1.ready())
    except ValueError:
        print("Caught Value Error")
    except Exception as E:
        raise E


if __name__ == "__main__":
    main()

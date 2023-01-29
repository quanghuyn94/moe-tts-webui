import threading
import time

def loading_animation(flag):
        for loop in range(1_000_000):
            dots = ['|', '/', '-', '\\']
            print(" Generating...", end='\r')
            for i in range(3):
                if flag[0]:
                    print("Sucess full!    ")
                    return
                print(dots[i % len(dots)] + " Generating...", end='\r')
                time.sleep(0.2)
        raise "Time out!"

complete = [False] #Animation flag.

animation_theard = threading.Thread(target=loading_animation, args=(complete,))
animation_theard.start()

time.sleep(10)

complete[0] = True

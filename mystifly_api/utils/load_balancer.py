import psutil


def is_max_cpu_load(n=0.2):
    is_max_load = False

    # Calling psutil.cpu_precent() for n seconds
    cpu_load = psutil.cpu_percent(n)
    print("CPU Load - ", cpu_load)

    if cpu_load > 85:
        is_max_load = True

    return cpu_load, is_max_load


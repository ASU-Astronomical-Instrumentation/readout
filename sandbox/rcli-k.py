import redis
import redis.exceptions
import json
import numpy as np

class Command:
    def __init__(self, command, args):
        self.command = "none"
        self.args = args

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)

class SystemStatus:
    def __init__(self, name):
        self.name = name
        self.status = "OK"
        self.message = "System is Unknown"
        self.bitstream = "unloaded"
        self.ip_cli = "0.0.0.0"
        self.ip_host = "0.0.0.0"
        self.mac_host = "00:11:22:33:44:55"
        self.mac_cli = "00:11:22:33:44:55"
        self.last_cmd = "none"
        self.last_cmd_status = "none"
    
    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)

def redis_command(redisfunc : redis.Redis, *args):
    try:
        return redisfunc(*args)
    except redis.exceptions.ConnectionError:
        print("Error: Redis server is not running")
        exit(1)
    except redis.exceptions.TimeoutError:
        print("Error: Redis server is not responding and timed out")
        exit(1)
    except redis.exceptions.RedisError:
        print("Error: Encoutnered an issue with Redis server")
        exit(1)

def main():
    # mystats = SystemStatus("dev")
    # serv = redis.Redis(host='localhost', port=6379, db=0)
    
    # redis_command(serv.set, "systemstatus", mystats.to_json())

    x = np.array([1, 2, 3])
    cmd = Command("test", ["This is a string arg", 2, x.tolist()])
    print(cmd.to_json())

    
if __name__ == '__main__':
    main()
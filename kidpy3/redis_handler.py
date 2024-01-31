"""
Description
-----------

Handles the command and control messaging as well as the connection to the redis server.


Command Packet Format
---------------------
{
    cmd : 'ulwaveform'
    args : [
        arg1,
        arg2,
        arg3
    ]
}

Reply Packet Format
-------------------
{
    'reply' : 'success'/'fail'
    'error' : none/Exception

}

DO I want to class this bitch??
"""
import json, sys, os, time, redis

def dispatch_command():
    pass

def await_reply():
    pass
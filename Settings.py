# CREDIT: https://gist.github.com/nadya-p/b25519cf3a74d1bed86ed9b1d8c71692
# AUTHOR: https://github.com/nadya-p
# Heavily modified by me (github.com/kotae4)
import json
import os
from tkinter import StringVar, IntVar, DoubleVar, BooleanVar, Variable


class SettingsEncoder(json.JSONEncoder):
    def default(self, obj):
        try:
            if (isinstance(obj, Variable) is True):
                return { 
                    "type": type(obj).__name__, 
                    "name": str(obj), 
                    "value": obj.get()
                };
            else:
                return obj.__dict__;
        except:
            return json.JSONEncoder.default(self, obj);

def SettingsDecoderHook(dct):
    if ("type" in dct):
        typeStr = dct['type'];
        if (typeStr == "StringVar"):
            return StringVar(value=dct['value'], name=dct['name']);
        elif (typeStr == "IntVar"):
            return IntVar(value=dct['value'], name=dct['name']);
        elif (typeStr == "DoubleVar"):
            return DoubleVar(value=dct['value'], name=dct['name']);
        elif (typeStr == "BooleanVar"):
            return BooleanVar(value=dct['value'], name=dct['name']);
    return dct;

class Settings:
    _config_location = "config.json";

    def __init__(self):
        if os.path.exists(self._config_location):
            with open(self._config_location, 'r') as f:
                fileStr = f.read();
                pyObj = json.loads(fileStr, object_hook=SettingsDecoderHook);
                self.__dict__ = pyObj;
        else:
            # default values for first run
            self.__dict__ = {
                'videoGameWindowTitle': StringVar(value="Counter", name='videoGameWindowTitle'),
                'screenShotWidth': IntVar(value=320, name='screenShotWidth'),
                'screenShotHeight': IntVar(value=320, name='screenShotHeight'),
                'aaDetectionBox': IntVar(value=320, name='aaDetectionBox'),
                'aaRightShift': IntVar(value=0, name='aaRightShift'),
                'aaMovementAmp': DoubleVar(value=1.1, name='aaMovementAmp'),
                'confidence': DoubleVar(value=0.5, name='confidence'),
                'aaQuitKey': StringVar(value="Q", name='aaQuitKey'),
                'headshotMode': BooleanVar(value=True, name='headshotMode'),
                'visuals': BooleanVar(value=False, name='visuals'),
            };

    def Save(self):
        try:
            jsonStr = json.dumps(self, cls=SettingsEncoder);
            with open(self._config_location, 'w') as f:
                f.write(jsonStr);
            return;
        except Exception as e:
            print("Exception occurred during JSON serialization: {}".format(e));
            return;

    def Load():
        return Settings();
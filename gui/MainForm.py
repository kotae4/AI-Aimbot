from tkinter import *
from tkinter import ttk
import tkinter.font as tkFont
from turtle import width
from Settings import *
from gui.WindowPickerForm import WindowPickerForm
import dxcam
from PIL import Image, ImageTk
from main import GetWindowByTitle
import time;
import gc;

class MainForm(Tk):
    def __init__(self, maxWidth, maxHeight):
        super().__init__();
        self.maxWidth = maxWidth;
        self.maxHeight = maxHeight;
        self.title("AI Aimbot [https://github.com/RootKit-Org/AI-Aimbot]");
        self.isDestroyed = False;
        self.protocol("WM_DELETE_WINDOW", lambda: self.OnClose());

        self.Settings = Settings();

        self.BuildSettingsFrame();
        ttk.Separator(self, orient=HORIZONTAL).grid(row=1, column=0, sticky='nsew');
        self.BuildVideoFrame();

        self.columnconfigure(0, weight=1);
        self.rowconfigure(0, weight=1);

    def BuildSettingsFrame(self):
        self.SettingsFrame = ttk.Frame(self, padding=5);
        self.SettingsFrame.grid(row=0, column=0, sticky='nsew');

        ttk.Label(self.SettingsFrame, text="Target Window:").grid(row=0, column=0, sticky='w');
        ttk.Button(self.SettingsFrame, textvariable=self.Settings.videoGameWindowTitle, command=lambda: self.OnClick_SetTargetWindow()).grid(row=0, column=1, sticky='e');

        ttk.Label(self.SettingsFrame, text="ScreenshotWidth:").grid(row=1, column=0, sticky='w');
        # TO-DO:
        # grab screen dimensions from directx
        ttk.Scale(self.SettingsFrame, orient=HORIZONTAL, from_=50.0, to=self.maxWidth, 
        variable=self.Settings.screenShotWidth, command=lambda: self.OnValueChanged_ScreenshotWidth()).grid(row=1, column=1, sticky='e');

        ttk.Label(self.SettingsFrame, text="ScreenshotHeight:").grid(row=2, column=0, sticky='w');
        # TO-DO:
        # grab screen dimensions from directx
        ttk.Scale(self.SettingsFrame, orient=HORIZONTAL, from_=50.0, to=self.maxHeight, 
        variable=self.Settings.screenShotHeight, command=lambda: self.OnValueChanged_ScreenshotWidth()).grid(row=2, column=1, sticky='e');

        ttk.Label(self.SettingsFrame, text="aaDetectionBox:").grid(row=3, column=0, sticky='w');
        # TO-DO:
        # grab screen dimensions from directx
        ttk.Scale(self.SettingsFrame, orient=HORIZONTAL, from_=50.0, to=self.maxHeight, 
        variable=self.Settings.aaDetectionBox, command=lambda: self.OnValueChanged_AADetectionBox()).grid(row=3, column=1, sticky='e');

        ttk.Label(self.SettingsFrame, text="aaRightShift:").grid(row=4, column=0, sticky='w');
        ttk.Scale(self.SettingsFrame, orient=HORIZONTAL, from_=0.0, to=500.0, 
        variable=self.Settings.aaRightShift, command=lambda: self.OnValueChanged_AARightShift()).grid(row=4, column=1, sticky='e');

        ttk.Label(self.SettingsFrame, text="aaMovementAmp:").grid(row=5, column=0, sticky='w');
        ttk.Scale(self.SettingsFrame, orient=HORIZONTAL, from_=0.0, to=5.0, 
        variable=self.Settings.aaMovementAmp, command=lambda: self.OnValueChanged_AAMovementAmp()).grid(row=5, column=1, sticky='e');

        ttk.Label(self.SettingsFrame, text="Confidence:").grid(row=6, column=0, sticky='w');
        ttk.Scale(self.SettingsFrame, orient=HORIZONTAL, from_=0.0, to=1.0, 
        variable=self.Settings.confidence, command=lambda: self.OnValueChanged_Confidence()).grid(row=6, column=1, sticky='e');

        # TO-DO:
        # make list of valid keys
        ttk.Label(self.SettingsFrame, text="aaQuitKey:").grid(row=7, column=0, sticky='w');
        cbox = ttk.Combobox(self.SettingsFrame, state='readonly', textvariable=self.Settings.aaQuitKey, values=('Q',));
        cbox.grid(row=7, column=1, sticky='e');
        cbox.bind('<<ComboboxSelected>>', self.OnComboboxSelected_AAQuitKey);

        ttk.Label(self.SettingsFrame, text="Headshot Mode:").grid(row=8, column=0, sticky='w');
        ttk.Checkbutton(self.SettingsFrame, variable=self.Settings.headshotMode, command=lambda: self.OnToggle_HeadshotMode()).grid(row=8, column=1, sticky='e');

        ttk.Label(self.SettingsFrame, text="Visuals:").grid(row=9, column=0, sticky='w');
        ttk.Checkbutton(self.SettingsFrame, variable=self.Settings.visuals, command=lambda: self.OnToggle_Visuals()).grid(row=9, column=1, sticky='e');

    def BuildVideoFrame(self):
        self.VideoFrame = ttk.Frame(self, width=self.Settings.screenShotWidth.get(), height=self.Settings.screenShotHeight.get());
        self.VideoFrame.grid(row=1, column=0);

        self.FPSLabel = ttk.Label(self.VideoFrame, text="0 fps");
        self.FPSLabel.grid(row=0, column=0);

        self.VideoFrontBuffer = Image.new("RGB", (self.maxWidth, self.maxHeight), "white");
        self.VideoBackBuffer = Image.new("RGB", (self.maxWidth, self.maxHeight), "white");
        self._CompatImage = ImageTk.PhotoImage(image=self.VideoFrontBuffer);
        self.VideoFrameImage = Label(self.VideoFrame, image=self._CompatImage, width=320, height=320);
        self.VideoFrameImage.grid(row=1, column=0);
        self.VideoNeedsBufferSwap = False;
        self.VideoNeedsBufferResize = False;

    def RenderCapturedImage(self, cv2Img):
        # populates the existing image, but doesn't work because frombytes can't handle numpy arrays
        #self.VideoBackBuffer.frombytes(cv2Img);
        img = Image.fromarray(cv2Img);
        tkImg = ImageTk.PhotoImage(image=img);
        self.VideoFrameImage.configure(image=tkImg);
        self.VideoFrameImage._cache_img = tkImg;
        """
        oldWidth, oldHeight = self.VideoBackBuffer.width, self.VideoBackBuffer.height;
        self.VideoBackBuffer = Image.fromarray(cv2Img);
        if ((self.VideoBackBuffer.width != oldWidth) or (self.VideoBackBuffer.height != oldHeight)):
            # resize front buffer too
            self.VideoNeedsBufferResize = True;

        self.VideoNeedsBufferSwap = True;
        """

    def SpawnWindowPickerDialogue(self):
        # spawn modal dialogue form that lists all top-level windows and allows user to select one
        windowPickerDialogue = WindowPickerForm(self);
        windowPickerDialogue.top.protocol('WM_DELETE_WINDOW', lambda: self.OnDialogueClosed(windowPickerDialogue));
        windowPickerDialogue.top.transient(self);
        windowPickerDialogue.top.wait_visibility();
        windowPickerDialogue.top.grab_set();
        windowPickerDialogue.top.wait_window();
        # if the user exits gracefully then this will execute
        # if the user exits harshly then OnDialogueClosed will execute first
        if (windowPickerDialogue.ReturnValue is not None):
            print("Got window: {}".format(str(windowPickerDialogue.ReturnValue)));
            self.Settings.videoGameWindowTitle.set(windowPickerDialogue.ReturnValue.title);
        del windowPickerDialogue;

    def OnDialogueClosed(self, dialogue : WindowPickerForm):
        # this is only called when the user presses the red X of the dialogue window
        print("Window picker dialogue was cancelled before selecting a window");
        dialogue.top.grab_release();
        dialogue.top.destroy();
        del dialogue;

    def OnClick_SetTargetWindow(self):
        self.SpawnWindowPickerDialogue();
        pass;

    def OnValueChanged_ScreenshotWidth(self):
        pass;

    def OnValueChanged_ScreenshotHeight(self):
        pass;

    def OnValueChanged_AADetectionBox(self):
        pass;

    def OnValueChanged_AARightShift(self):
        pass;

    def OnValueChanged_Confidence(self):
        pass;

    def OnComboboxSelected_AAQuitKey(self, event):
        pass;

    def OnToggle_HeadshotMode(self):
        pass;

    def OnToggle_Visuals(self):
        pass;

    def OnClose(self):
        self.isDestroyed = True;
        self.Settings.Save();
        self.destroy();
        pass;


def Run(cb):
    cam = dxcam.create(output_color="RGB");
    app = MainForm(cam.width, cam.height);
    loopCounter = 0;
    startFrameTime = time.perf_counter_ns();
    endFrameTime = time.perf_counter_ns();
    oneSecondTimer = 0;
    while app.isDestroyed is False:
        startFrameTime = time.perf_counter_ns();
        # magic number is conversion between nanoseconds and milliseconds
        cb(app, cam);
        app.update_idletasks();
        app.update();
        loopCounter = loopCounter + 1;
        endFrameTime = time.perf_counter_ns();
        oneSecondTimer = oneSecondTimer + (endFrameTime - startFrameTime);
        if (oneSecondTimer > 1e+9):
            # one second has elapsed
            oneSecondTimer = 0;
            app.FPSLabel.configure(text="FPS: {}".format(loopCounter));
            loopCounter = 0;
    
    cam.stop();
    cam.release();
    del cam;
    print("Exiting gracefully!");
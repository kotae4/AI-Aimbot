import gui.MainForm as GUI
from Settings import *
import pyautogui
import dxcam;
import numpy as np;
# from pywin32
import win32api, win32con;
# for getting current directory to pass to torch.hub.set_dir
import os;

import torch;
import cv2;
# needed by torch internally
import pandas;
pandas.options.mode.chained_assignment = None;  

import openvino.utils as utils
utils.add_openvino_libs_to_path()

def GetWindowByTitle(title : str) -> pyautogui.Window:
    matchingWindows = pyautogui.getWindowsWithTitle(title);
    if ((matchingWindows) and (len(matchingWindows) > 0)):
        return matchingWindows[0];
    return None;

def BotLogic(app : GUI, cam : dxcam.DXCamera):
    # everything in this function is ran every single frame
    
    # attempt to grab the game window (it may have been destroyed since last frame)
    # this allows us to update our capture region with the latest window position too
    # so if the user moves the game window it won't break everything
    gameWindow = GetWindowByTitle(app.Settings.videoGameWindowTitle.get());
    if (gameWindow is None):
        return;

    # cache our settings values so we don't have to keep calling .get() on them
    aaRightShift = app.Settings.aaRightShift.get();
    screenShotWidth = app.Settings.screenShotWidth.get();
    screenShotHeight = app.Settings.screenShotHeight.get();
    confidence = app.Settings.confidence.get();
    aaDetectionBox = app.Settings.aaDetectionBox.get();
    headshotMode = app.Settings.headshotMode.get();
    aaMovementAmp = app.Settings.aaMovementAmp.get();
    visuals = app.Settings.visuals.get();

    #gameWindow.activate();
    # NOTE: '//' operator divides, rounds down, and returns a whole number (saved you a google search)
    # Calculating the center of the game window
    centerX_desktopspace = gameWindow.left + ((gameWindow.right - gameWindow.left) // 2);
    centerY_desktopspace = gameWindow.top + ((gameWindow.bottom - gameWindow.top) // 2);
    left = (centerX_desktopspace - screenShotWidth) + aaRightShift;
    top = (centerY_desktopspace - screenShotHeight);
    right = (centerX_desktopspace + screenShotWidth);
    bottom = (centerY_desktopspace + screenShotHeight);
    # dxcam expects tuple of (left, top, right, bottom) in that order
    captureRegion = (left, top, right, bottom);
    if (cam.is_capturing is not True):
        cam.start(captureRegion, video_mode=True);

    npImg = cam.get_latest_frame();
    if (npImg is None):
        print("Warning: could not grab frame from dxcam (skipping this frame)");
        return;

    normalizedImg = torch.from_numpy(npImg).to('cpu')
    normalizedImg = torch.movedim(normalizedImg, 2, 0)
    normalizedImg = normalizedImg.half()
    normalizedImg /= 255
    if len(normalizedImg.shape) == 3:
        normalizedImg = normalizedImg[None]

    centerX_windowspace = (right - left) // 2;
    centerY_windowspace = (bottom - top) // 2;

    # Detecting all the objects
    detected = MODEL(npImg, size=screenShotHeight);
    detectedPandas = detected.pandas();
    results = detectedPandas.xyxy[0];

    # Filtering out everything that isn't a person
    targets = results[(results['class'] == 0) & (results['confidence'] > confidence)]

    # If there are people in the center bounding box
    if len(targets) > 0:
        targets['current_mid_x'] = (targets['xmax'] + targets['xmin']) // 2
        targets['current_mid_y'] = (targets['ymax'] + targets['ymin']) // 2
        # TO-DO:
        # sort by distance from center of screen

        # Take the first person that shows up in the dataframe
        targetCenterX = round((targets.iloc[0].xmax + targets.iloc[0].xmin) / 2) + aaRightShift;
        targetCenterY = round((targets.iloc[0].ymax + targets.iloc[0].ymin) / 2);

        box_height = targets.iloc[0].ymax - targets.iloc[0].ymin
        if headshotMode:
            headshot_offset = box_height * 0.38
        else:
            headshot_offset = box_height * 0.2
        mouseMove = [targetCenterX - centerX_windowspace, (targetCenterY - headshot_offset) - centerY_windowspace]
        cv2.circle(npImg, (int(mouseMove[0] + targetCenterX), int(mouseMove[1] + targetCenterY - headshot_offset)), 3, (0, 0, 255))

        # Moving the mouse
        if win32api.GetKeyState(0x14):
            win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, int(mouseMove[0] * aaMovementAmp), int(mouseMove[1] * aaMovementAmp), 0, 0)

    # See what the bot sees
    if visuals:
        # Loops over every item identified and draws a bounding box
        for i in range(0, len(results)):
            (startX, startY, endX, endY) = int(results["xmin"][i]), int(results["ymin"][i]), int(results["xmax"][i]), int(results["ymax"][i])

            resConfidence = results["confidence"][i]

            idx = int(results["class"][i])

            # draw the bounding box and label on the frame
            label = "{}: {:.2f}%".format(results["name"][i], resConfidence * 100)
            cv2.rectangle(npImg, (startX, startY), (endX, endY),
                COLORS[idx], 2)
            y = startY - 15 if startY - 15 > 15 else startY + 15
            cv2.putText(npImg, label, (startX, y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLORS[idx], 2)
        # update the GUI with the processed image
        app.RenderCapturedImage(npImg);

if __name__ == "__main__":
    torch.hub.set_dir(os.getcwd() + "\\models");
    print(torch.hub.get_dir());
    # Loading Yolo5 Small AI Model
    MODEL = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True, force_reload=False);
    """
    for loading local models:
    modelPath = os.getcwd() + '\\yolov6n.pt';
    print(modelPath);
    MODEL = torch.hub.load(os.getcwd(), 'custom', path=modelPath, source='local');
    """
    MODEL.classes = [0];
    MODEL.multi_label = False;
    MODEL.max_det = 10;
    MODEL.conf = 0.5;
    MODEL.amp = False;
    MODEL.agnostic = False;
    # Used for colors drawn on bounding boxes
    COLORS = np.random.uniform(0, 255, size=(1500, 3))
    GUI.Run(BotLogic);
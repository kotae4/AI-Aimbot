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

from utils.general import (LOGGER, check_file, check_img_size, check_imshow, check_requirements, colorstr, cv2,
                           increment_path, non_max_suppression, print_args, scale_coords, strip_optimizer, xywh2xyxy, xyxy2xywh);

import platform
#from onnx import numpy_helper
import onnx
import onnxruntime as ort;

if platform.system() == "Windows":
    from openvino import utils;
    utils.add_openvino_libs_to_path();

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
    centerX_windowspace = (right - left) // 2;
    centerY_windowspace = (bottom - top) // 2;
    # dxcam expects tuple of (left, top, right, bottom) in that order
    captureRegion = (left, top, right, bottom);
    if (cam.is_capturing is not True):
        cam.start(captureRegion, video_mode=True);

    cap = cam.get_latest_frame();
    if (cap is None):
        print("Warning: could not grab frame from dxcam (skipping this frame)");
        return;

    npImg = np.array([cap]) / 255;
    npImg = npImg.astype(np.half);
    npImg = np.moveaxis(npImg, 3, 1);

    # Detecting all the objects
    outputs = ORT_SESSION.run(None, {'images': npImg});
    im = torch.from_numpy(outputs[0]).to('cpu');
    pred = non_max_suppression(im, 0.25, 0.25, 0, False, max_det=1000);
    #print(pred);
    targets = [];
    for i, det in enumerate(pred):
        gn = torch.tensor(npImg.shape)[[0, 0, 0, 0]];
        if len(det):
            for *xyxy, conf, cls in reversed(det):
                targets.append(xywh2xyxy(xyxy2xywh(torch.tensor(xyxy).view(1, 4)) / gn).view(-1).tolist());

    # If there are people in the center bounding box
    if len(targets) > 0:
        # TO-DO:
        # sort by distance from center of screen

        # Take the first person that shows up in the dataframe
        targetCenterX = round((targets[0][2] + targets[0][0]) / 2) + aaRightShift;
        targetCenterY = round((targets[0][3] + targets[0][1]) / 2);

        box_height = targets[0][3] - targets[0][1]
        if headshotMode:
            headshot_offset = box_height * 0.38
        else:
            headshot_offset = box_height * 0.2
        mouseMove = [targetCenterX - centerX_windowspace, (targetCenterY - headshot_offset) - centerY_windowspace]
        cv2.circle(cap, (int(mouseMove[0] + targetCenterX), int(mouseMove[1] + targetCenterY - headshot_offset)), 3, (0, 0, 255))

        # Moving the mouse
        if win32api.GetKeyState(0x14):
            win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, int(mouseMove[0] * aaMovementAmp), int(mouseMove[1] * aaMovementAmp), 0, 0)

    # See what the bot sees
    if visuals:
        # Loops over every item identified and draws a bounding box
        for i in range(0, len(targets)):
            # xywh format
            #(startX, startY, endX, endY) = int(targets[i][0]), int(targets[i][1]), int(targets[i][0] + targets[i][2]), int(targets[i][1] + targets[i][3]);
            # xyxy format
            (startX, startY, endX, endY) = int(targets[i][0]), int(targets[i][1]), int(targets[i][2]), int(targets[i][3]);
            # draw the bounding box and label on the frame
            cv2.rectangle(cap, (startX, startY), (endX, endY),
                COLORS[i], 2)
        # update the GUI with the processed image
        app.RenderCapturedImage(cap);

if __name__ == "__main__":
    so = ort.SessionOptions();
    so.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL;
    ORT_SESSION = ort.InferenceSession('yolov5s16.onnx', sess_options=so, providers=['CUDAExecutionProvider', 'OpenVINOExecutionProvider', 'CPUExecutionProvider']);

    # Used for colors drawn on bounding boxes
    COLORS = np.random.uniform(0, 255, size=(1500, 3))
    GUI.Run(BotLogic);
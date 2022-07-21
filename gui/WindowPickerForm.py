from tkinter import *
from tkinter import ttk
import tkinter.font as tkFont
from Settings import *
import pyautogui;

class WindowPickerForm:

    def __init__(self, parent):

        self.top = Toplevel(parent);
        self.top.title("Window Picker");
        self.top.protocol('WM_DELETE_WINDOW', lambda: self.OnCancel());
        self.ReturnValue = None;

        windowsTitles = pyautogui.getAllTitles();

        self.WindowsTitlesList = Listbox(self.top, width=50, height=10);
        for title in windowsTitles:
            self.WindowsTitlesList.insert(END, title);
        self.WindowsTitlesList.grid(row=0, column=0, sticky='nsew');
        self.WindowsTitlesList.bind('<Double-1>', lambda event: self.OnDblClick_WindowsTitles(event));

        self.Scrollbar = ttk.Scrollbar(self.top, orient=VERTICAL, command=self.WindowsTitlesList.yview);
        self.WindowsTitlesList.configure(yscrollcommand=self.Scrollbar.set);
        self.Scrollbar.grid(row=0, column=1, sticky='ns');

        ttk.Button(self.top, text="Select", command=lambda: self.OnDblClick_WindowsTitles(None)).grid(row=1, column=0, sticky='sw');
        ttk.Button(self.top, text="Cancel", command=lambda: self.OnCancel()).grid(row=1, column=1, sticky='se');

    def OnDblClick_WindowsTitles(self, event):
        selectedIndex = self.WindowsTitlesList.curselection();
        if (len(selectedIndex) == 1):
            selectedTitle = self.WindowsTitlesList.get(selectedIndex);
            matchingWindows = pyautogui.getWindowsWithTitle(selectedTitle);
            if ((matchingWindows) and (len(matchingWindows) > 0)):
                self.ReturnValue = matchingWindows[0];
        self.top.grab_release();
        self.top.destroy();

    def OnCancel(self):
        self.ReturnValue = None;
        self.top.grab_release();
        self.top.destroy();
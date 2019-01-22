import tkinter as tk
from tkinter import font  as tkfont
import tkinter.messagebox as tm
from urllib.request import urlopen
from tkinter import filedialog

class LoginGUI(tk.Tk):

    def __init__(self,*args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        self.title_font = tkfont.Font(family='Helvetica', size=18, weight="bold", slant="italic")
        self.subtitle_font = tkfont.Font(family='Helvetica', size=12, weight="bold", slant="italic")

        # the container is where we'll stack a bunch of frames
        # on top of each other, then the one we want visible
        # will be raised above the others

        container = tk.Frame(self)
        container.grid(row = 10)

        label = tk.Label(self, text="Easy Apply Bot", font=self.title_font)
        label.grid(row=0,columnspan = 2, pady=10)

        self.frames = {}
        for F in (StartPage, PageOne, PageTwo, PageThree, PageFour, PageFive, PageSix):
            page_name = F.__name__
            frame = F(parent=container, controller=self)
            self.frames[page_name] = frame

            # put all of the pages in the same location;
            # the one on the top of the stacking order
            # will be the one that is visible.
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("StartPage")

    def show_frame(self, page_name):
        '''Show a frame for the given page name'''
        frame = self.frames[page_name]
        frame.tkraise()


class StartPage(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller

        #title
        label = tk.Label(self, text="Insert your LinkedIn credentials", font=controller.subtitle_font)
        label.grid(row=2,columnspan = 2, pady=10)


        #Username and password
        label_username = tk.Label(self, text="Username")
        label_password = tk.Label(self, text="Password")
        label_username.grid(row=4, column=0)
        label_password.grid(row=5, column=0)

        self.entry_username = tk.Entry(self)
        self.entry_password = tk.Entry(self, show="*")
        self.entry_username.grid(row=4, column=1)
        self.entry_password.grid(row=5, column=1)

        #button = tk.Button(self, text="Next", command=lambda: controller.show_frame("PageOne"))
        button = tk.Button(self, text="Next", command= self.auth)
        button.grid(row=7, columnspan=2, pady=30)

    def auth (self):

        self.username = self.entry_username.get()
        self.password = self.entry_password.get()

        self.controller.show_frame("PageOne")
            


class PageOne(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller

        #title
        label = tk.Label(self, text="Choose your LinkedIn language", font=controller.subtitle_font)
        label.grid(row=2,columnspan = 2, pady=10)

        #language
        self.var = tk.StringVar()
        R1 = tk.Radiobutton(self, text="English", variable=self.var, value="en")#,command=self.sel)
        R1.grid(row=4, column=0, sticky = "W")

        R2 = tk.Radiobutton(self, text="Spanish", variable=self.var, value="es")#,command=self.sel)
        R2.grid(row=5,column=0, sticky = "W")

        R3 = tk.Radiobutton(self, text="Portuguese", variable=self.var, value="pt")#,command=self.sel)
        R3.grid(row=6,column=0, sticky = "W")

        self.var.set("en")

        #button
        button = tk.Button(self, text="Next",command=self.sel)
        button.grid(row=7, columnspan=2, pady=30)

    def sel(self):
        self.language = self.var.get()
        self.controller.show_frame("PageTwo")

class PageTwo(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller

        #title
        label = tk.Label(self, text="Type your desired job title \n (e.g. Consulting innovation)", font=controller.subtitle_font)
        label.grid(row=2,columnspan = 2, pady=10)

        #job tite
        label_position = tk.Label(self, text="job title")
        label_position.grid(row=3, column=0)
        self.entry_position = tk.Entry(self)
        self.entry_position.grid(row=3, column=1)

        #button
        button = tk.Button(self, text="Next",command= self.sel_position)
        button.grid(row=7, columnspan=2, pady=30)

    def sel_position (self):
        self.position = self.entry_position.get()
        self.controller.show_frame("PageThree")


class PageThree(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller

        #title
        label = tk.Label(self, text="Where are you looking for a job?", font=controller.subtitle_font)
        label.grid(row=2,columnspan = 2, pady=10)

        #Location
        self.var = tk.IntVar()
        R1 = tk.Radiobutton(self, text="Worldwide", variable=self.var, value=1)#,command=self.sel_location_code)
        R1.grid(row=3, column=0, sticky = "W")

        R2 = tk.Radiobutton(self, text="In a specific Country", variable=self.var, value=2)#,command=self.sel_location_code)
        R2.grid(row=4,column=0, sticky = "W")

        R3 = tk.Radiobutton(self, text="In a specific State", variable=self.var, value=3)#,command=self.sel_location_code)
        R3.grid(row=5,column=0, sticky = "W")

        R4 = tk.Radiobutton(self, text="In a specific City", variable=self.var, value=4)#,command=self.sel_location_code)
        R4.grid(row=6,column=0, sticky = "W")

        self.var.set(1)

        #button
        #button = tk.Button(self, text="Next",command=lambda: controller.show_frame("PageFour"))
        button = tk.Button(self, text="Next",command= self.sel_location_code)
        button.grid(row=7, columnspan=2, pady=30)

    def sel_location_code(self):
        self.location_code = self.var.get()

        if self.location_code == 1:
            self.location = "Worldwide"
            self.controller.show_frame("PageFive")
        else:
            self.controller.show_frame("PageFour")


class PageFour(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller

        #title
        label = tk.Label(self, text="loc2", font=controller.subtitle_font)
        label.grid(row=2,columnspan = 2, pady=10)

        #type position
        label_location = tk.Label(self, text="Enter the name:")
        label_location.grid(row=2, column=0)
        self.entry_location = tk.Entry(self)
        self.entry_location.grid(row=2, column=1)

        #button
        #button = tk.Button(self, text="Next",command=lambda: controller.show_frame("StartPage"))
        button = tk.Button(self, text="Next",command= self.sel_location)
        button.grid(row=7, columnspan=2, pady=30)


    def sel_location(self):
        self.location = self.entry_location.get()
        self.controller.show_frame("PageFive")


class PageFive(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.summary()

    def summary (self):
        label = tk.Label(self, text="Upload your CV", font=self.controller.subtitle_font)
        label.grid(row=2,columnspan = 2, pady=10)

        #button1 = tk.Button(self, text="Next", command=lambda: controller.show_frame("PageOne"))
        self.resumeloctn = ''
        button1 = tk.Button(self, text="Upload",command=self.CV)
        button1.grid(row=7, column = 1, pady=30)
        button2 = tk.Button(self, text="Next",command= lambda: self.controller.show_frame("PageSix"))
        button2.grid(row=7, column = 2, pady=30)

    def CV (self):
        #root = tk.Tk()
        self.resumeloctn = filedialog.askopenfilename(parent=self, initialdir="/", title='Please select your curriculum')
        #root.destroy()
        #print(self.resumeloctn)
        return


class PageSix(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.summary()

    def summary (self):
        label = tk.Label(self, text="Ready to start applying?", font=self.controller.subtitle_font)
        label.grid(row=2,columnspan = 2, pady=10)

        #button1 = tk.Button(self, text="Next", command=lambda: controller.show_frame("PageOne"))
        button = tk.Button(self, text="START!",command=self.finish)
        button.grid(row=7, columnspan=2, pady=30)

    def finish(self):
        self.controller.destroy()

# if __name__ == "__main__":
#     print("\nEasy Apply Bot\n")

#     app = LoginGUI()
#     app.mainloop()

#     #get user info
#     username=app.frames["StartPage"].username
#     password=app.frames["StartPage"].password
#     language=app.frames["PageOne"].language
#     position=app.frames["PageTwo"].position
#     location_code=app.frames["PageThree"].location_code
#     if location_code == 1:
#         location=app.frames["PageThree"].location
#     else:
#         location = app.frames["PageFour"].location
#     resumeloctn=app.frames["PageFive"].resumeloctn

#     print(username,password, language, position, location_code, location, resumeloctn)
